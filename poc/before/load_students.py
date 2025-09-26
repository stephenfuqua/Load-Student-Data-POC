#!/usr/bin/env python3
"""
Load Student Data POC - Script to load student data into Ed-Fi ODS/API

This script reads student data from a CSV file and loads it into two Ed-Fi API endpoints:
1. students - for student demographic information
2. studentSchoolAssociations - for enrollment information
"""

import os
import sys
import csv
import requests
from dotenv import load_dotenv
from typing import Dict, List, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EdFiApiClient:
    """Client for interacting with Ed-Fi ODS/API"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.session = requests.Session()
    
    def authenticate(self) -> bool:
        """Authenticate with the Ed-Fi API and get access token"""
        auth_url = f"{self.base_url}/oauth/token"
        
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = self.session.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            if self.access_token:
                self.session.headers.update({
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                })
                logger.info("Successfully authenticated with Ed-Fi API")
                return True
            else:
                logger.error("No access token received from authentication")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def post_student(self, student_data: Dict[str, Any]) -> bool:
        """POST student data to the students endpoint"""
        endpoint = f"{self.base_url}/data/v3/ed-fi/students"
        
        try:
            response = self.session.post(endpoint, json=student_data)
            response.raise_for_status()
            logger.info(f"Successfully created student {student_data.get('studentUniqueId')}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create student {student_data.get('studentUniqueId')}: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return False
    
    def post_student_school_association(self, association_data: Dict[str, Any]) -> bool:
        """POST student school association data to the studentSchoolAssociations endpoint"""
        endpoint = f"{self.base_url}/data/v3/ed-fi/studentSchoolAssociations"
        
        try:
            response = self.session.post(endpoint, json=association_data)
            response.raise_for_status()
            logger.info(f"Successfully created student school association for student {association_data.get('studentReference', {}).get('studentUniqueId')}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Failed to create student school association: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            return False


def map_csv_to_student(row: Dict[str, str]) -> Dict[str, Any]:
    """Map CSV row to Ed-Fi student data structure"""
    student_data = {
        "studentUniqueId": row['uniqueId'],
        "birthDate": row['birthDate'],
        "firstName": row['firstName'],
        "lastSurname": row['lastName']
    }
    
    # Add optional fields if they exist and are not empty
    if row.get('middleName') and row['middleName'].strip():
        student_data['middleName'] = row['middleName']
    
    if row.get('title') and row['title'].strip():
        student_data['personalTitlePrefix'] = row['title']
    
    if row.get('preferredFirstName') and row['preferredFirstName'].strip():
        student_data['preferredFirstName'] = row['preferredFirstName']
    
    if row.get('preferredLastName') and row['preferredLastName'].strip():
        student_data['preferredLastSurname'] = row['preferredLastName']
    
    return student_data


def map_csv_to_student_school_association(row: Dict[str, str]) -> Dict[str, Any]:
    """Map CSV row to Ed-Fi student school association data structure"""
    grade_level_descriptor = f"uri://ed-fi.org/GradeLevelDescriptor#{row['enrollmentGradeLevel']}"
    
    association_data = {
        "studentReference": {
            "studentUniqueId": row['uniqueId']
        },
        "schoolReference": {
            "schoolId": int(row['schoolId'])
        },
        "entryDate": row['enrollmentDate'],
        "entryGradeLevelDescriptor": grade_level_descriptor
    }
    
    # Add fullTimeEquivalency if it's provided and is 1 (True)
    if row.get('fullTime') and row['fullTime'].strip() == '1':
        association_data['fullTimeEquivalency'] = 1.0
    elif row.get('fullTime') and row['fullTime'].strip() == '0':
        association_data['fullTimeEquivalency'] = 0.0
    
    return association_data


def load_student_data(csv_file_path: str, api_client: EdFiApiClient) -> None:
    """Load student data from CSV file into Ed-Fi API"""
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV file not found: {csv_file_path}")
        sys.exit(1)
    
    success_count = 0
    error_count = 0
    
    with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
            logger.info(f"Processing row {row_num}: Student {row.get('uniqueId')}")
            
            # Map and post student data
            student_data = map_csv_to_student(row)
            student_success = api_client.post_student(student_data)
            
            if student_success:
                # If student creation successful, create the school association
                association_data = map_csv_to_student_school_association(row)
                association_success = api_client.post_student_school_association(association_data)
                
                if association_success:
                    success_count += 1
                    logger.info(f"Successfully processed student {row.get('uniqueId')}")
                else:
                    error_count += 1
                    logger.error(f"Student created but school association failed for {row.get('uniqueId')}")
            else:
                error_count += 1
                logger.error(f"Failed to process student {row.get('uniqueId')}")
    
    logger.info(f"Processing complete. Success: {success_count}, Errors: {error_count}")


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    base_url = os.getenv('EDFI_API_BASE_URL')
    client_id = os.getenv('EDFI_API_CLIENT_ID')
    client_secret = os.getenv('EDFI_API_CLIENT_SECRET')
    
    if not all([base_url, client_id, client_secret]):
        logger.error("Missing required environment variables. Please check your .env file.")
        logger.error("Required variables: EDFI_API_BASE_URL, EDFI_API_CLIENT_ID, EDFI_API_CLIENT_SECRET")
        sys.exit(1)
    
    # Initialize API client
    api_client = EdFiApiClient(base_url, client_id, client_secret)
    
    # Authenticate
    if not api_client.authenticate():
        logger.error("Failed to authenticate with Ed-Fi API")
        sys.exit(1)
    
    # Load student data
    csv_file_path = os.path.join(os.path.dirname(__file__), 'students.csv')
    load_student_data(csv_file_path, api_client)


if __name__ == "__main__":
    main()