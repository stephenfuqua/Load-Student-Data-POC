#!/usr/bin/env python3
"""
POC 6: Load Student Data using Ed-Fi SDK MCP

This script loads student and enrollment data from a CSV file into an Ed-Fi API
using Data Standard 5.2. Supports insert, update, and delete operations.
"""

import csv
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import requests
from dotenv import load_dotenv
import pandas as pd


class EdFiApiClient:
    """Client for interacting with Ed-Fi API"""
    
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url.rstrip('/')
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Authenticate with Ed-Fi API and get access token"""
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
            self.access_token = token_data['access_token']
            self.session.headers.update({
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            })
            return True
        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False
    
    def create_student(self, student_data: Dict) -> bool:
        """Create or update a student record"""
        url = f"{self.base_url}/data/v3/ed-fi/students"
        try:
            response = self.session.post(url, json=student_data)
            if response.status_code in [200, 201]:
                print(f"✅ Student {student_data['studentUniqueId']} created/updated successfully")
                return True
            else:
                print(f"❌ Failed to create/update student {student_data['studentUniqueId']}: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating/updating student {student_data['studentUniqueId']}: {e}")
            return False
    
    def delete_student(self, student_unique_id: str) -> bool:
        """Delete a student record"""
        # First, get the student to find the ID
        url = f"{self.base_url}/data/v3/ed-fi/students"
        params = {'studentUniqueId': student_unique_id}
        
        try:
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                students = response.json()
                if students:
                    student_id = students[0]['id']
                    delete_url = f"{self.base_url}/data/v3/ed-fi/students/{student_id}"
                    delete_response = self.session.delete(delete_url)
                    if delete_response.status_code == 204:
                        print(f"✅ Student {student_unique_id} deleted successfully")
                        return True
                    else:
                        print(f"❌ Failed to delete student {student_unique_id}: {delete_response.status_code}")
                        return False
                else:
                    print(f"⚠️ Student {student_unique_id} not found for deletion")
                    return True  # Consider it successful if already doesn't exist
            else:
                print(f"❌ Failed to find student {student_unique_id} for deletion: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting student {student_unique_id}: {e}")
            return False
    
    def create_enrollment(self, enrollment_data: Dict) -> bool:
        """Create or update a student school association (enrollment)"""
        url = f"{self.base_url}/data/v3/ed-fi/studentSchoolAssociations"
        try:
            response = self.session.post(url, json=enrollment_data)
            if response.status_code in [200, 201]:
                print(f"✅ Enrollment for student {enrollment_data['studentReference']['studentUniqueId']} created/updated successfully")
                return True
            else:
                print(f"❌ Failed to create/update enrollment: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating/updating enrollment: {e}")
            return False


class StudentDataProcessor:
    """Process student data from CSV file"""
    
    def __init__(self, api_client: EdFiApiClient):
        self.api_client = api_client
        
    def process_csv_file(self, csv_file_path: str) -> None:
        """Process student data from CSV file"""
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return
        
        try:
            # Read CSV with dtype=str to prevent type conversion issues
            df = pd.read_csv(csv_file_path, dtype=str, na_values=[''], keep_default_na=False)
            print(f"📊 Processing {len(df)} records from {csv_file_path}")
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                action = str(row['action']).lower().strip()
                
                if action == 'delete':
                    if self.process_delete_action(row):
                        success_count += 1
                    else:
                        error_count += 1
                elif action in ['insert', 'update']:
                    if self.process_insert_update_action(row):
                        success_count += 1
                    else:
                        error_count += 1
                else:
                    print(f"⚠️ Unknown action '{action}' for record {index + 1}")
                    error_count += 1
            
            print(f"\n📈 Processing complete: {success_count} successful, {error_count} errors")
            
        except Exception as e:
            print(f"❌ Error processing CSV file: {e}")
    
    def process_delete_action(self, row: pd.Series) -> bool:
        """Process delete action for a student"""
        unique_id = str(row['uniqueId']).strip()
        if not unique_id or unique_id == 'nan':
            print(f"❌ Missing uniqueId for delete action")
            return False
        
        return self.api_client.delete_student(unique_id)
    
    def process_insert_update_action(self, row: pd.Series) -> bool:
        """Process insert or update action for a student and enrollment"""
        try:
            # Build student data
            student_data = self.build_student_data(row)
            
            # Create/update student
            if not self.api_client.create_student(student_data):
                return False
            
            # Build and create enrollment if enrollment data is present
            if self.has_enrollment_data(row):
                enrollment_data = self.build_enrollment_data(row)
                if not self.api_client.create_enrollment(enrollment_data):
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing insert/update for student {row.get('uniqueId', 'unknown')}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def build_student_data(self, row: pd.Series) -> Dict:
        """Build student data object from CSV row"""
        student_data = {
            "studentUniqueId": str(row['uniqueId']).strip(),
            "firstName": str(row['firstName']).strip(),
            "lastSurname": str(row['lastName']).strip(),
            "birthDate": self.format_date(row['birthDate'])
        }
        
        # Add optional fields
        if str(row.get('middleName', '')).strip() not in ['', 'nan', 'None']:
            student_data["middleName"] = str(row['middleName']).strip()
        
        if str(row.get('title', '')).strip() not in ['', 'nan', 'None']:
            student_data["personalTitlePrefix"] = str(row['title']).strip()
        
        if str(row.get('preferredFirstName', '')).strip() not in ['', 'nan', 'None']:
            student_data["preferredFirstName"] = str(row['preferredFirstName']).strip()
        
        if str(row.get('preferredLastName', '')).strip() not in ['', 'nan', 'None']:
            student_data["preferredLastSurname"] = str(row['preferredLastName']).strip()
        
        return student_data
    
    def build_enrollment_data(self, row: pd.Series) -> Dict:
        """Build enrollment data object from CSV row"""
        enrollment_data = {
            "studentReference": {
                "studentUniqueId": str(row['uniqueId']).strip()
            },
            "schoolReference": {
                "schoolId": int(str(row['schoolId']).strip())
            },
            "entryDate": self.format_date(row['enrollmentDate']),
            "entryGradeLevelDescriptor": f"uri://ed-fi.org/GradeLevelDescriptor#{self.normalize_grade_level(row['enrollmentGradeLevel'])}"
        }
        
        # Add full-time equivalency
        full_time_str = str(row.get('fullTime', '')).strip()
        if full_time_str and full_time_str not in ['', 'nan', 'None']:
            full_time = int(full_time_str)
            enrollment_data["fullTimeEquivalency"] = 1.0 if full_time == 1 else 0.5
        
        return enrollment_data
    
    def has_enrollment_data(self, row: pd.Series) -> bool:
        """Check if row contains enrollment data"""
        required_fields = ['enrollmentDate', 'enrollmentGradeLevel', 'schoolId']
        return all(
            str(row.get(field, '')).strip() not in ['', 'nan', 'None'] 
            for field in required_fields
        )
    
    def format_date(self, date_value) -> str:
        """Format date value to YYYY-MM-DD format"""
        date_str = str(date_value).strip()
        if not date_str or date_str in ['nan', 'None', '']:
            return ""
        
        try:
            # Try parsing different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y']:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # If no format matches, return as-is and let API handle it
            return date_str
            
        except Exception:
            return date_str
    
    def normalize_grade_level(self, grade_level) -> str:
        """Normalize grade level to Ed-Fi descriptor format"""
        grade_str = str(grade_level).strip()
        if not grade_str or grade_str in ['nan', 'None', '']:
            return ""
        
        # Mapping for common grade level variations
        grade_mapping = {
            "ninth grade": "Ninth grade",
            "tenth grade": "Tenth grade", 
            "eleventh grade": "Eleventh grade",
            "twelfth grade": "Twelfth grade",
            "9th grade": "Ninth grade",
            "10th grade": "Tenth grade",
            "11th grade": "Eleventh grade", 
            "12th grade": "Twelfth grade",
            "9": "Ninth grade",
            "10": "Tenth grade",
            "11": "Eleventh grade",
            "12": "Twelfth grade"
        }
        
        return grade_mapping.get(grade_str.lower(), grade_str)


def main():
    """Main function to run the student data loader"""
    print("🚀 Starting POC 6: Load Student Data using Ed-Fi SDK MCP")
    
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment variables
    api_base_url = os.getenv('EDFI_API_BASE_URL', 'https://api.ed-fi.org/v7.3/api')
    client_id = os.getenv('EDFI_CLIENT_ID')
    client_secret = os.getenv('EDFI_CLIENT_SECRET')
    csv_file_path = os.getenv('STUDENT_CSV_FILE', 'students.csv')
    
    # Validate configuration
    if not all([client_id, client_secret]):
        print("❌ Missing required environment variables:")
        print("   - EDFI_CLIENT_ID")
        print("   - EDFI_CLIENT_SECRET")
        print("   Optional:")
        print("   - EDFI_API_BASE_URL (default: https://api.ed-fi.org/v7.3/api)")
        print("   - STUDENT_CSV_FILE (default: students.csv)")
        return
    
    # Initialize API client
    api_client = EdFiApiClient(api_base_url, client_id, client_secret)
    
    # Authenticate
    print("🔐 Authenticating with Ed-Fi API...")
    if not api_client.authenticate():
        print("❌ Authentication failed. Please check your credentials.")
        return
    
    print("✅ Authentication successful")
    
    # Initialize processor and process CSV file
    processor = StudentDataProcessor(api_client)
    processor.process_csv_file(csv_file_path)
    
    print("✅ POC 6 completed")


if __name__ == "__main__":
    main()