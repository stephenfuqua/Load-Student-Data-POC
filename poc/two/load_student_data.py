#!/usr/bin/env python3
"""
Ed-Fi Student Data Loader - POC 2

This script loads student and enrollment data from a CSV file into an Ed-Fi API.
It creates both Student records and StudentSchoolEnrollment records.
"""

import csv
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

import pandas as pd
import requests
from dateutil.parser import parse as parse_date


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EdFiApiClient:
    """Client for interacting with Ed-Fi API"""
    
    def __init__(self, base_url: str, access_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.access_token = access_token
        self.session = requests.Session()
        
        if access_token:
            self.session.headers.update({
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            })
    
    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Authenticate with the Ed-Fi API and obtain access token"""
        auth_url = f"{self.base_url}/oauth/token"
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
            
            logger.info("Successfully authenticated with Ed-Fi API")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    def create_student(self, student_data: Dict[str, Any]) -> bool:
        """Create a student record in the Ed-Fi API"""
        url = f"{self.base_url}/data/v3/ed-fi/students"
        
        try:
            response = self.session.post(url, json=student_data)
            
            if response.status_code == 201:
                logger.info(f"Successfully created student {student_data.get('studentUniqueId')}")
                return True
            elif response.status_code == 409:
                logger.warning(f"Student {student_data.get('studentUniqueId')} already exists")
                return True
            else:
                logger.error(f"Failed to create student {student_data.get('studentUniqueId')}: "
                           f"{response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error creating student {student_data.get('studentUniqueId')}: {e}")
            return False
    
    def create_enrollment(self, enrollment_data: Dict[str, Any]) -> bool:
        """Create a student school enrollment record in the Ed-Fi API"""
        url = f"{self.base_url}/data/v3/ed-fi/studentSchoolEnrollments"
        
        try:
            response = self.session.post(url, json=enrollment_data)
            
            if response.status_code == 201:
                logger.info(f"Successfully created enrollment for student "
                          f"{enrollment_data.get('studentReference', {}).get('studentUniqueId')}")
                return True
            elif response.status_code == 409:
                logger.warning(f"Enrollment for student "
                             f"{enrollment_data.get('studentReference', {}).get('studentUniqueId')} "
                             f"already exists")
                return True
            else:
                logger.error(f"Failed to create enrollment: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"Error creating enrollment: {e}")
            return False


class StudentDataLoader:
    """Handles loading student data from CSV and transforming it for Ed-Fi API"""
    
    def __init__(self, csv_file_path: str, api_client: EdFiApiClient):
        self.csv_file_path = csv_file_path
        self.api_client = api_client
    
    def load_csv_data(self) -> pd.DataFrame:
        """Load student data from CSV file"""
        try:
            df = pd.read_csv(self.csv_file_path)
            logger.info(f"Loaded {len(df)} records from {self.csv_file_path}")
            return df
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise
    
    def transform_student_data(self, row: pd.Series) -> Dict[str, Any]:
        """Transform CSV row data to Ed-Fi Student format"""
        student_data = {
            "studentUniqueId": str(row['uniqueId']),
            "birthDate": row['birthDate'],
            "firstName": row['firstName'],
            "lastSurname": row['lastName']
        }
        
        # Add optional fields if they exist and are not empty
        if pd.notna(row['middleName']) and row['middleName'].strip():
            student_data["middleName"] = row['middleName']
        
        if pd.notna(row['title']) and row['title'].strip():
            student_data["generationCodeSuffix"] = row['title']
        
        # Handle preferred names
        if pd.notna(row['preferredFirstName']) and row['preferredFirstName'].strip():
            student_data["preferredFirstName"] = row['preferredFirstName']
        
        if pd.notna(row['preferredLastName']) and row['preferredLastName'].strip():
            student_data["preferredLastSurname"] = row['preferredLastName']
        
        return student_data
    
    def transform_enrollment_data(self, row: pd.Series) -> Dict[str, Any]:
        """Transform CSV row data to Ed-Fi StudentSchoolEnrollment format"""
        
        # Map grade levels to Ed-Fi standard descriptors
        grade_level_map = {
            "Ninth grade": "Ninth grade",
            "Tenth grade": "Tenth grade", 
            "Eleventh grade": "Eleventh grade",
            "Twelfth grade": "Twelfth grade"
        }
        
        enrollment_data = {
            "studentReference": {
                "studentUniqueId": str(row['uniqueId'])
            },
            "schoolReference": {
                "schoolId": int(row['schoolId'])
            },
            "entryDate": row['enrollmentDate'],
            "entryGradeLevelDescriptor": f"uri://ed-fi.org/GradeLevelDescriptor#{grade_level_map.get(row['enrollmentGradeLevel'], row['enrollmentGradeLevel'])}",
            "fullTimeEquivalency": 1.0 if row['fullTime'] == 1 else 0.5
        }
        
        return enrollment_data
    
    def load_data(self) -> bool:
        """Load all student and enrollment data to Ed-Fi API"""
        try:
            df = self.load_csv_data()
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                # Create student record first
                student_data = self.transform_student_data(row)
                if self.api_client.create_student(student_data):
                    
                    # Create enrollment record
                    enrollment_data = self.transform_enrollment_data(row)
                    if self.api_client.create_enrollment(enrollment_data):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
            
            logger.info(f"Data loading completed: {success_count} successful, {error_count} errors")
            return error_count == 0
            
        except Exception as e:
            logger.error(f"Error during data loading: {e}")
            return False


def main():
    """Main function to run the student data loader"""
    
    # Configuration - these would typically come from environment variables or config file
    ED_FI_BASE_URL = os.getenv('EDFI_BASE_URL', 'https://api.ed-fi.org/v5.3/api')
    ED_FI_CLIENT_ID = os.getenv('EDFI_CLIENT_ID')
    ED_FI_CLIENT_SECRET = os.getenv('EDFI_CLIENT_SECRET')
    CSV_FILE_PATH = os.getenv('CSV_FILE_PATH', './students.csv')
    
    # Validate required configuration
    if not ED_FI_CLIENT_ID or not ED_FI_CLIENT_SECRET:
        logger.error("ED_FI_CLIENT_ID and ED_FI_CLIENT_SECRET environment variables are required")
        sys.exit(1)
    
    if not os.path.exists(CSV_FILE_PATH):
        logger.error(f"CSV file not found: {CSV_FILE_PATH}")
        sys.exit(1)
    
    # Initialize API client
    api_client = EdFiApiClient(ED_FI_BASE_URL)
    
    # Authenticate
    if not api_client.authenticate(ED_FI_CLIENT_ID, ED_FI_CLIENT_SECRET):
        logger.error("Failed to authenticate with Ed-Fi API")
        sys.exit(1)
    
    # Load data
    loader = StudentDataLoader(CSV_FILE_PATH, api_client)
    
    if loader.load_data():
        logger.info("Student data loading completed successfully")
        sys.exit(0)
    else:
        logger.error("Student data loading failed")
        sys.exit(1)


if __name__ == "__main__":
    main()