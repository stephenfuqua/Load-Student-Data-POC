#!/usr/bin/env python3
"""
Ed-Fi API Student Data Loader

This script loads student and enrollment data from a CSV file into an Ed-Fi API
using the Data Standard 5 OpenAPI Specification.
"""

import csv
import os
import sys
from typing import Dict, Optional
import requests
from dotenv import load_dotenv


class EdFiAPIClient:
    """Client for interacting with Ed-Fi API"""

    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.access_token = None
        self.session = requests.Session()

    def authenticate(self) -> bool:
        """Authenticate with the Ed-Fi API and get access token"""
        auth_url = f"{self.base_url.replace('/data/v3', '')}/oauth/token"

        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
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
                print("Successfully authenticated with Ed-Fi API")
                return True
            else:
                print("Failed to get access token")
                return False

        except requests.exceptions.RequestException as e:
            print(f"Authentication failed: {e}")
            return False

    def create_student(self, student_data: Dict) -> Optional[str]:
        """Create a student record in Ed-Fi API"""
        url = f"{self.base_url}/ed-fi/students"

        try:
            response = self.session.post(url, json=student_data)

            if response.status_code == 201:
                # Student created successfully
                location = response.headers.get('Location', '')
                student_id = location.split('/')[-1] if location else None
                print(f"✓ Created student: {student_data['studentUniqueId']}")
                return student_id
            elif response.status_code == 409:
                # Student already exists
                print(f"⚠ Student already exists: {student_data['studentUniqueId']}")
                return "existing"
            else:
                student_id = student_data['studentUniqueId']
                status = response.status_code
                text = response.text
                print(f"✗ Failed to create student {student_id}: {status} - {text}")
                return None

        except requests.exceptions.RequestException as e:
            print(f"✗ Error creating student {student_data['studentUniqueId']}: {e}")
            return None

    def create_student_school_association(self, association_data: Dict) -> Optional[str]:
        """Create a student school association (enrollment) record in Ed-Fi API"""
        url = f"{self.base_url}/ed-fi/studentSchoolAssociations"

        try:
            response = self.session.post(url, json=association_data)

            if response.status_code == 201:
                # Association created successfully
                location = response.headers.get('Location', '')
                association_id = location.split('/')[-1] if location else None
                student_id = association_data['studentReference']['studentUniqueId']
                school_id = association_data['schoolReference']['schoolId']
                print(f"✓ Created enrollment for student {student_id} at school {school_id}")
                return association_id
            elif response.status_code == 409:
                # Association already exists
                student_id = association_data['studentReference']['studentUniqueId']
                school_id = association_data['schoolReference']['schoolId']
                print(f"⚠ Enrollment already exists for student {student_id} at school {school_id}")
                return "existing"
            else:
                student_id = association_data['studentReference']['studentUniqueId']
                status = response.status_code
                text = response.text
                print(f"✗ Failed to create enrollment for student {student_id}: {status} - {text}")
                return None

        except requests.exceptions.RequestException as e:
            student_id = association_data['studentReference']['studentUniqueId']
            print(f"✗ Error creating enrollment for student {student_id}: {e}")
            return None


class StudentDataMapper:
    """Maps CSV data to Ed-Fi API data structures"""

    @staticmethod
    def map_grade_level(csv_grade: str) -> str:
        """Map CSV grade level to Ed-Fi descriptor"""
        grade_mapping = {
            'Ninth grade': 'uri://ed-fi.org/GradeLevelDescriptor#Ninth grade',
            'Tenth grade': 'uri://ed-fi.org/GradeLevelDescriptor#Tenth grade',
            'Eleventh grade': 'uri://ed-fi.org/GradeLevelDescriptor#Eleventh grade',
            'Twelfth grade': 'uri://ed-fi.org/GradeLevelDescriptor#Twelfth grade',
            # Add more mappings as needed
        }
        return grade_mapping.get(csv_grade, f'uri://ed-fi.org/GradeLevelDescriptor#{csv_grade}')

    @staticmethod
    def create_student_payload(row: Dict[str, str]) -> Dict:
        """Create Ed-Fi student payload from CSV row"""
        payload = {
            'studentUniqueId': row['uniqueId'],
            'firstName': row['firstName'],
            'lastSurname': row['lastName'],
            'birthDate': row['birthDate']
        }

        # Add optional fields if present
        if row.get('middleName'):
            payload['middleName'] = row['middleName']

        if row.get('title'):
            payload['personalTitlePrefix'] = row['title']

        if row.get('preferredFirstName'):
            payload['preferredFirstName'] = row['preferredFirstName']

        if row.get('preferredLastName'):
            payload['preferredLastSurname'] = row['preferredLastName']

        return payload

    @staticmethod
    def create_student_school_association_payload(row: Dict[str, str]) -> Dict:
        """Create Ed-Fi student school association payload from CSV row"""
        payload = {
            'studentReference': {
                'studentUniqueId': row['uniqueId']
            },
            'schoolReference': {
                'schoolId': int(row['schoolId'])
            },
            'entryDate': row['enrollmentDate'],
            'entryGradeLevelDescriptor': StudentDataMapper.map_grade_level(
                row['enrollmentGradeLevel']
            )
        }

        # Add full-time equivalency if available
        if row.get('fullTime'):
            fte = 1.0 if row['fullTime'] == '1' else 0.5
            payload['fullTimeEquivalency'] = fte

        return payload


def load_students_from_csv(file_path: str, api_client: EdFiAPIClient) -> None:
    """Load students and enrollments from CSV file"""

    if not os.path.exists(file_path):
        print(f"Error: CSV file not found: {file_path}")
        return

    students_created = 0
    enrollments_created = 0
    errors = 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)

            print(f"Loading students from {file_path}...")
            print("=" * 50)

            for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                try:
                    # Create student record
                    student_payload = StudentDataMapper.create_student_payload(row)
                    student_result = api_client.create_student(student_payload)

                    if student_result:
                        if student_result != "existing":
                            students_created += 1

                        # Create student school association (enrollment)
                        mapper = StudentDataMapper
                        association_payload = mapper.create_student_school_association_payload(row)
                        result = api_client.create_student_school_association(association_payload)

                        if result and result != "existing":
                            enrollments_created += 1
                        elif not result:
                            errors += 1
                    else:
                        errors += 1

                except Exception as e:
                    print(f"✗ Error processing row {row_num}: {e}")
                    errors += 1

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print("=" * 50)
    print("Summary:")
    print(f"  Students created: {students_created}")
    print(f"  Enrollments created: {enrollments_created}")
    print(f"  Errors: {errors}")


def main():
    """Main function"""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    base_url = os.getenv('EDFI_API_BASE_URL')
    api_key = os.getenv('EDFI_API_KEY')
    api_secret = os.getenv('EDFI_API_SECRET')

    if not all([base_url, api_key, api_secret]):
        print("Error: Missing required environment variables:")
        print("  EDFI_API_BASE_URL")
        print("  EDFI_API_KEY")
        print("  EDFI_API_SECRET")
        print("\nPlease create a .env file based on .env.example")
        sys.exit(1)

    # CSV file path
    csv_file = os.path.join(os.path.dirname(__file__), 'students.csv')

    # Create API client
    api_client = EdFiAPIClient(base_url, api_key, api_secret)

    # Authenticate
    if not api_client.authenticate():
        print("Failed to authenticate with Ed-Fi API")
        sys.exit(1)

    # Load students
    load_students_from_csv(csv_file, api_client)


if __name__ == '__main__':
    main()
