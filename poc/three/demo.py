#!/usr/bin/env python3
"""
Example usage of the Ed-Fi API Student Data Loader

This script demonstrates how to use the loader with mock data
without actually making API calls.
"""

import os
import sys

# Add the current directory to Python path to import our module
sys.path.insert(0, os.path.dirname(__file__))

from load_students import StudentDataMapper


def demo_without_api():
    """Demonstrate the data mapping without API calls"""
    
    print("Ed-Fi API Student Data Loader - Demo Mode")
    print("=" * 50)
    print("This demo shows how CSV data is mapped to Ed-Fi API format")
    print("without making actual API calls.\n")
    
    # Sample CSV data (same as in the CSV file)
    sample_students = [
        {
            'uniqueId': '604835',
            'birthDate': '2016-09-29',
            'firstName': 'Diana',
            'lastName': 'Holt',
            'middleName': 'Emily',
            'title': 'Ms',
            'preferredFirstName': '',
            'preferredLastName': '',
            'enrollmentDate': '2021-08-23',
            'enrollmentGradeLevel': 'Ninth grade',
            'fullTime': '1',
            'schoolId': '255901001'
        },
        {
            'uniqueId': '604843',
            'birthDate': '2009-09-24',
            'firstName': 'Byron',
            'lastName': 'Wilkerson',
            'middleName': 'Keith',
            'title': 'Mr',
            'preferredFirstName': 'Page',
            'preferredLastName': 'Jackson',
            'enrollmentDate': '2021-08-23',
            'enrollmentGradeLevel': 'Ninth grade',
            'fullTime': '0',
            'schoolId': '255901001'
        }
    ]
    
    for i, student_data in enumerate(sample_students, 1):
        print(f"Student {i}: {student_data['firstName']} {student_data['lastName']}")
        print("-" * 40)
        
        # Map to Ed-Fi student format
        student_payload = StudentDataMapper.create_student_payload(student_data)
        print("Ed-Fi Student Payload:")
        for key, value in student_payload.items():
            print(f"  {key}: {value}")
        
        print()
        
        # Map to Ed-Fi student school association format
        association_payload = StudentDataMapper.create_student_school_association_payload(student_data)
        print("Ed-Fi Student School Association Payload:")
        for key, value in association_payload.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 50 + "\n")
    
    print("Demo completed! To run with actual Ed-Fi API:")
    print("1. Copy .env.example to .env")
    print("2. Configure your Ed-Fi API credentials")
    print("3. Run: poetry run python load_students.py")


if __name__ == '__main__':
    demo_without_api()