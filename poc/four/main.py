#!/usr/bin/env python3
"""
Ed-Fi Student Data Loader - POC Five

This script loads student and enrollment data from a CSV file into an Ed-Fi API
using OAuth2 authentication and Discovery API for endpoint discovery.

Usage:
    python main.py [--csv-file students.csv] [--dry-run]
"""
import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

from discovery_client import DiscoveryClient
from oauth2_client import OAuth2Client
from data_handler import StudentDataHandler
from edfi_client import EdFiApiClient


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('edfi_loader.log')
        ]
    )


def load_config() -> dict:
    """
    Load configuration from environment variables.
    
    Returns:
        Dictionary with configuration values
        
    Raises:
        ValueError: If required configuration is missing
    """
    # Load .env file if it exists
    env_file = Path('.env')
    if env_file.exists():
        load_dotenv(env_file)
    
    config = {
        'api_base_url': os.getenv('EDFI_API_BASE_URL'),
        'client_id': os.getenv('EDFI_CLIENT_ID'),
        'client_secret': os.getenv('EDFI_CLIENT_SECRET'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    # Validate required configuration
    required_keys = ['api_base_url', 'client_id', 'client_secret']
    missing_keys = [key for key in required_keys if not config[key]]
    
    if missing_keys:
        raise ValueError(f"Missing required configuration: {missing_keys}")
    
    return config


def process_student_data(csv_file: str, dry_run: bool = False) -> bool:
    """
    Process student data from CSV file and load into Ed-Fi API.
    
    Args:
        csv_file: Path to CSV file containing student data
        dry_run: If True, validate data but don't make API calls
        
    Returns:
        True if successful, False otherwise
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Load configuration
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Initialize Discovery client
        discovery = DiscoveryClient(config['api_base_url'])
        logger.info(f"Initialized Discovery client for {config['api_base_url']}")
        
        if dry_run:
            logger.info("Dry run mode - using mock endpoints")
            oauth_endpoints = {
                'token': config['api_base_url'] + '/oauth/token',
                'authorize': config['api_base_url'] + '/oauth/authorize'
            }
            data_api_base = config['api_base_url'] + '/data/v3/'
        else:
            # Get OAuth endpoints
            oauth_endpoints = discovery.get_oauth_endpoints()
            logger.info(f"Found OAuth endpoints: {oauth_endpoints}")
            
            # Get Data Management API base path
            data_api_base = discovery.get_data_management_api_base_path()
            logger.info(f"Data Management API base path: {data_api_base}")
            
            # Optionally get OpenAPI metadata
            openapi_metadata = discovery.get_openapi_metadata()
            if openapi_metadata:
                logger.info("OpenAPI metadata retrieved successfully")
            else:
                logger.warning("OpenAPI metadata not available")
        
        if dry_run:
            logger.info("Dry run mode - skipping OAuth and API operations")
            # For dry run, we can use a mock OAuth client
            oauth_client = None
            api_client = None
        else:
            # Initialize OAuth2 client
            oauth_client = OAuth2Client(
                oauth_endpoints['token'],
                config['client_id'],
                config['client_secret']
            )
            logger.info("OAuth2 client initialized")
            
            # Initialize Ed-Fi API client
            api_client = EdFiApiClient(data_api_base, oauth_client)
            logger.info("Ed-Fi API client initialized")
        
        # Load and validate CSV data
        data_handler = StudentDataHandler(csv_file)
        df = data_handler.load_data()
        
        if not data_handler.validate_data(df):
            logger.error("Data validation failed")
            return False
        
        # Group records by action
        records_by_action = data_handler.get_records_by_action(df)
        
        # Process each action type
        success_count = 0
        error_count = 0
        
        for action, records in records_by_action.items():
            if not records:
                continue
                
            logger.info(f"Processing {len(records)} {action} operations")
            
            for record in records:
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Would {action}: {record}")
                        success_count += 1
                        continue
                    
                    success = False
                    
                    if action == 'insert':
                        # Create student
                        if api_client.create_student(record['student']):
                            success = True
                            # Create enrollment if data exists
                            if record['enrollment']:
                                if not api_client.create_enrollment(record['enrollment']):
                                    logger.warning(f"Student created but enrollment failed for {record['student']['studentUniqueId']}")
                        
                    elif action == 'update':
                        # Update student
                        student_id = record['student']['studentUniqueId']
                        if api_client.update_student(student_id, record['student']):
                            success = True
                            # Update enrollment if data exists
                            if record['enrollment']:
                                school_id = record['enrollment']['schoolReference']['schoolId']
                                if not api_client.update_enrollment(student_id, school_id, record['enrollment']):
                                    logger.warning(f"Student updated but enrollment update failed for {student_id}")
                        
                    elif action == 'delete':
                        # Delete student (this should cascade to enrollments)
                        student_id = record['studentUniqueId']
                        success = api_client.delete_student(student_id)
                    
                    if success:
                        success_count += 1
                        logger.info(f"Successfully processed {action} for student {record.get('student', record).get('studentUniqueId', 'unknown')}")
                    else:
                        error_count += 1
                        logger.error(f"Failed to process {action} for student {record.get('student', record).get('studentUniqueId', 'unknown')}")
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"Error processing {action} operation: {e}")
        
        # Summary
        total_processed = success_count + error_count
        logger.info(f"Processing complete: {success_count} successful, {error_count} failed, {total_processed} total")
        
        return error_count == 0
        
    except Exception as e:
        logger.error(f"Fatal error in process_student_data: {e}")
        return False


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description='Load student data into Ed-Fi API')
    parser.add_argument(
        '--csv-file',
        default='students.csv',
        help='Path to CSV file containing student data (default: students.csv)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate data and endpoints but do not make API calls'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Set logging level (default: INFO)'
    )
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # Check if CSV file exists
    if not Path(args.csv_file).exists():
        logger.error(f"CSV file not found: {args.csv_file}")
        sys.exit(1)
    
    logger.info("Starting Ed-Fi Student Data Loader")
    logger.info(f"CSV file: {args.csv_file}")
    logger.info(f"Dry run: {args.dry_run}")
    
    try:
        success = process_student_data(args.csv_file, args.dry_run)
        
        if success:
            logger.info("Data loading completed successfully")
            sys.exit(0)
        else:
            logger.error("Data loading completed with errors")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()