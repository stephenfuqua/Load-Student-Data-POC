#!/usr/bin/env python3
"""
Ed-Fi Discovery API POC for Loading Student Data

This script demonstrates using the Ed-Fi Discovery API to:
1. Identify OAuth2 token endpoints
2. Identify Data Management API base path
3. Explore OpenAPI metadata for Resources API endpoints
4. Load student and enrollment data from CSV into the Ed-Fi API

The script processes student and enrollment data from students.csv and posts
the data to the appropriate Ed-Fi API endpoints.
"""

import csv
import json
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os


class EdFiDiscoveryClient:
    """Client for interacting with the Ed-Fi Discovery API"""
    
    def __init__(self, discovery_url: str = "https://api.ed-fi.org/v7.3/api/"):
        self.discovery_url = discovery_url
        self.discovery_data = None
        self.oauth_endpoint = None
        self.data_api_base = None
        self.resources_metadata = None
        
    def discover_endpoints(self):
        """Discover OAuth and API endpoints using the Discovery API"""
        print(f"Discovering Ed-Fi API endpoints from: {self.discovery_url}")
        
        try:
            response = requests.get(self.discovery_url)
            response.raise_for_status()
            self.discovery_data = response.json()
            
            # Extract key endpoints
            urls = self.discovery_data.get('urls', {})
            self.oauth_endpoint = urls.get('oauth')
            self.data_api_base = urls.get('dataManagementApi')
            
            print(f"✓ OAuth2 token endpoint: {self.oauth_endpoint}")
            print(f"✓ Data Management API base path: {self.data_api_base}")
            
            return True
            
        except Exception as e:
            print(f"✗ Error discovering endpoints: {e}")
            return False
    
    def explore_resources_metadata(self):
        """Explore the OpenAPI metadata for Resources API endpoints"""
        if not self.discovery_data:
            print("✗ Discovery data not available. Run discover_endpoints() first.")
            return False
            
        try:
            # Get metadata endpoints list
            metadata_url = self.discovery_data['urls']['openApiMetadata']
            response = requests.get(metadata_url)
            response.raise_for_status()
            metadata_list = response.json()
            
            # Find Resources API metadata
            resources_metadata_url = None
            for item in metadata_list:
                if item.get('name') == 'Resources':
                    resources_metadata_url = item['endpointUri']
                    break
            
            if not resources_metadata_url:
                print("✗ Resources API metadata not found")
                return False
            
            print(f"✓ Exploring Resources API metadata: {resources_metadata_url}")
            
            # Get Resources API metadata (not storing JSON files as per requirements)
            response = requests.get(resources_metadata_url)
            response.raise_for_status()
            self.resources_metadata = response.json()
            
            # Analyze the metadata
            paths = self.resources_metadata.get('paths', {})
            
            # Find student-related endpoints
            student_endpoints = [path for path in paths.keys() if 'student' in path.lower()]
            enrollment_endpoints = [path for path in paths.keys() if 'studentschool' in path.lower().replace('-', '')]
            
            print(f"✓ Found {len(student_endpoints)} student-related endpoints")
            print(f"✓ Found {len(enrollment_endpoints)} student-school association endpoints")
            
            # Show key endpoints we'll use
            print("\nKey endpoints for our POC:")
            if '/ed-fi/students' in paths:
                print("  - /ed-fi/students (for creating students)")
            if '/ed-fi/studentSchoolAssociations' in paths:
                print("  - /ed-fi/studentSchoolAssociations (for enrollment)")
            
            return True
            
        except Exception as e:
            print(f"✗ Error exploring metadata: {e}")
            return False
    
    def get_oauth_token(self, client_id: str, client_secret: str) -> Optional[str]:
        """Get OAuth token for API authentication"""
        if not self.oauth_endpoint:
            print("✗ OAuth endpoint not available")
            return None
        
        token_data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            response = requests.post(self.oauth_endpoint, data=token_data)
            response.raise_for_status()
            token_response = response.json()
            return token_response.get('access_token')
        except Exception as e:
            print(f"✗ Error getting OAuth token: {e}")
            return None


class StudentDataLoader:
    """Loads student data from CSV and posts to Ed-Fi API"""
    
    def __init__(self, discovery_client: EdFiDiscoveryClient):
        self.discovery_client = discovery_client
        self.access_token = None
    
    def authenticate(self, client_id: str, client_secret: str) -> bool:
        """Authenticate with the Ed-Fi API"""
        print("\nAuthenticating with Ed-Fi API...")
        self.access_token = self.discovery_client.get_oauth_token(client_id, client_secret)
        
        if self.access_token:
            print("✓ Successfully authenticated")
            return True
        else:
            print("✗ Authentication failed")
            return False
    
    def load_student_data(self, csv_file_path: str) -> List[Dict[str, Any]]:
        """Load student data from CSV file"""
        students = []
        
        try:
            with open(csv_file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    students.append(row)
            
            print(f"✓ Loaded {len(students)} student records from {csv_file_path}")
            return students
            
        except Exception as e:
            print(f"✗ Error loading CSV file: {e}")
            return []
    
    def transform_student_for_api(self, student_row: Dict[str, str]) -> Dict[str, Any]:
        """Transform CSV student data to Ed-Fi API format"""
        student_data = {
            "studentUniqueId": student_row['uniqueId'],
            "birthDate": student_row['birthDate'],
            "firstName": student_row['firstName'],
            "lastSurname": student_row['lastName']
        }
        
        # Add optional fields if present
        if student_row.get('middleName'):
            student_data["middleName"] = student_row['middleName']
        
        if student_row.get('preferredFirstName'):
            student_data["personalTitlePrefix"] = student_row.get('title', '')
        
        return student_data
    
    def transform_enrollment_for_api(self, student_row: Dict[str, str]) -> Dict[str, Any]:
        """Transform CSV enrollment data to Ed-Fi API format"""
        enrollment_data = {
            "studentReference": {
                "studentUniqueId": student_row['uniqueId']
            },
            "schoolReference": {
                "schoolId": int(student_row['schoolId'])
            },
            "entryDate": student_row['enrollmentDate'],
            "entryGradeLevelDescriptor": f"uri://ed-fi.org/GradeLevelDescriptor#{student_row['enrollmentGradeLevel'].replace(' ', '%20')}"
        }
        
        # Add full-time equivalency if available
        if student_row.get('fullTime'):
            enrollment_data["fullTimeEquivalency"] = float(student_row['fullTime'])
        
        return enrollment_data
    
    def post_student(self, student_data: Dict[str, Any]) -> bool:
        """Post a student record to the Ed-Fi API"""
        if not self.access_token or not self.discovery_client.data_api_base:
            print("✗ Missing authentication or API base URL")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.discovery_client.data_api_base}ed-fi/students"
        
        try:
            response = requests.post(url, json=student_data, headers=headers)
            
            if response.status_code in [200, 201]:
                print(f"✓ Created student: {student_data['studentUniqueId']}")
                return True
            elif response.status_code == 409:
                print(f"i Student already exists: {student_data['studentUniqueId']}")
                return True  # Consider existing student as success
            else:
                print(f"✗ Failed to create student {student_data['studentUniqueId']}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"✗ Error posting student {student_data['studentUniqueId']}: {e}")
            return False
    
    def post_enrollment(self, enrollment_data: Dict[str, Any]) -> bool:
        """Post an enrollment record to the Ed-Fi API"""
        if not self.access_token or not self.discovery_client.data_api_base:
            print("✗ Missing authentication or API base URL")
            return False
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.discovery_client.data_api_base}ed-fi/studentSchoolAssociations"
        
        try:
            response = requests.post(url, json=enrollment_data, headers=headers)
            
            if response.status_code in [200, 201]:
                student_id = enrollment_data['studentReference']['studentUniqueId']
                school_id = enrollment_data['schoolReference']['schoolId']
                print(f"✓ Created enrollment for student {student_id} at school {school_id}")
                return True
            elif response.status_code == 409:
                student_id = enrollment_data['studentReference']['studentUniqueId']
                print(f"i Enrollment already exists for student: {student_id}")
                return True  # Consider existing enrollment as success
            else:
                student_id = enrollment_data['studentReference']['studentUniqueId']
                print(f"✗ Failed to create enrollment for student {student_id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            student_id = enrollment_data['studentReference']['studentUniqueId']
            print(f"✗ Error posting enrollment for student {student_id}: {e}")
            return False
    
    def process_students_csv(self, csv_file_path: str, client_id: str, client_secret: str) -> bool:
        """Process the entire CSV file and load data into Ed-Fi API"""
        print(f"\n{'='*60}")
        print("STARTING Ed-Fi DATA LOAD PROCESS")
        print(f"{'='*60}")
        
        # Authenticate
        if not self.authenticate(client_id, client_secret):
            return False
        
        # Load CSV data
        students = self.load_student_data(csv_file_path)
        if not students:
            return False
        
        success_count = 0
        enrollment_success_count = 0
        
        print(f"\nProcessing {len(students)} student records...")
        
        # Process each student
        for i, student_row in enumerate(students, 1):
            print(f"\n--- Processing student {i}/{len(students)} ---")
            
            # Transform and post student
            student_data = self.transform_student_for_api(student_row)
            if self.post_student(student_data):
                success_count += 1
                
                # Transform and post enrollment
                enrollment_data = self.transform_enrollment_for_api(student_row)
                if self.post_enrollment(enrollment_data):
                    enrollment_success_count += 1
        
        print(f"\n{'='*60}")
        print("LOAD PROCESS COMPLETE")
        print(f"{'='*60}")
        print(f"Students processed: {success_count}/{len(students)}")
        print(f"Enrollments processed: {enrollment_success_count}/{len(students)}")
        
        return success_count == len(students) and enrollment_success_count == len(students)


def main():
    """Main function demonstrating the Discovery API POC"""
    
    print("Ed-Fi Discovery API POC - Student Data Loader")
    print("=" * 50)
    
    # Initialize Discovery Client
    discovery_client = EdFiDiscoveryClient()
    
    # Step 1: Discover endpoints
    if not discovery_client.discover_endpoints():
        print("Failed to discover endpoints. Exiting.")
        sys.exit(1)
    
    # Step 2: Explore metadata
    if not discovery_client.explore_resources_metadata():
        print("Failed to explore metadata. Exiting.")
        sys.exit(1)
    
    # Step 3: Load student data
    print("\nNOTE: This is a demonstration script.")
    print("To actually load data, you would need valid Ed-Fi API credentials.")
    print("The script shows how to use the Discovery API to find endpoints and schemas.")
    
    # For demonstration, show what would happen with dummy credentials
    print("\nDemonstration with dummy credentials:")
    loader = StudentDataLoader(discovery_client)
    
    # Check if students.csv exists
    csv_file = os.path.join(os.path.dirname(__file__), 'students.csv')
    if os.path.exists(csv_file):
        print(f"\n✓ Found students.csv file: {csv_file}")
        
        # Load and show the data structure
        students = loader.load_student_data(csv_file)
        if students:
            print(f"\nSample student data transformation:")
            sample_student = students[0]
            print("Original CSV row:")
            print(json.dumps(sample_student, indent=2))
            
            print("\nTransformed for Ed-Fi Student API:")
            student_api_data = loader.transform_student_for_api(sample_student)
            print(json.dumps(student_api_data, indent=2))
            
            print("\nTransformed for Ed-Fi Enrollment API:")
            enrollment_api_data = loader.transform_enrollment_for_api(sample_student)
            print(json.dumps(enrollment_api_data, indent=2))
    else:
        print(f"\n✗ students.csv not found at: {csv_file}")
    
    print("\nDiscovery API exploration complete!")
    print("Use loader.process_students_csv() with valid credentials to load actual data.")


if __name__ == "__main__":
    main()