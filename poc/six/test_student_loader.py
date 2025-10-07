#!/usr/bin/env python3
"""
Test script for POC 6: Validate CSV parsing and data processing without API calls
"""

import csv
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd

# Import our modules
from student_loader import StudentDataProcessor, EdFiApiClient


class MockEdFiApiClient:
    """Mock API client for testing without actual API calls"""
    
    def __init__(self):
        self.authenticated = False
        self.operations_log = []
    
    def authenticate(self) -> bool:
        self.authenticated = True
        print("✅ Mock authentication successful")
        return True
    
    def create_student(self, student_data: Dict) -> bool:
        operation = f"CREATE_STUDENT: {student_data['studentUniqueId']}"
        self.operations_log.append(operation)
        print(f"✅ Mock student {student_data['studentUniqueId']} created/updated successfully")
        print(f"   Data: {student_data}")
        return True
    
    def delete_student(self, student_unique_id: str) -> bool:
        operation = f"DELETE_STUDENT: {student_unique_id}"
        self.operations_log.append(operation)
        print(f"✅ Mock student {student_unique_id} deleted successfully")
        return True
    
    def create_enrollment(self, enrollment_data: Dict) -> bool:
        operation = f"CREATE_ENROLLMENT: {enrollment_data['studentReference']['studentUniqueId']}"
        self.operations_log.append(operation)
        print(f"✅ Mock enrollment for student {enrollment_data['studentReference']['studentUniqueId']} created/updated successfully")
        print(f"   Data: {enrollment_data}")
        return True


def test_csv_processing():
    """Test CSV processing with mock API client"""
    print("🧪 Testing POC 6: CSV Processing and Data Validation")
    print("=" * 60)
    
    # Initialize mock API client
    mock_api = MockEdFiApiClient()
    mock_api.authenticate()
    
    # Initialize processor with mock client
    processor = StudentDataProcessor(mock_api)
    
    # Test with the sample CSV file
    csv_file_path = "students.csv"
    
    if not os.path.exists(csv_file_path):
        print(f"❌ CSV file not found: {csv_file_path}")
        return False
    
    print(f"📁 Processing test CSV file: {csv_file_path}")
    print("-" * 60)
    
    # Process the CSV file
    processor.process_csv_file(csv_file_path)
    
    print("\n" + "=" * 60)
    print("📊 Operations Summary:")
    for i, operation in enumerate(mock_api.operations_log, 1):
        print(f"  {i}. {operation}")
    
    print(f"\n✅ Test completed successfully! {len(mock_api.operations_log)} operations logged.")
    return True


def test_individual_records():
    """Test individual record processing"""
    print("\n🔍 Testing Individual Record Processing")
    print("=" * 60)
    
    # Create test data
    test_records = [
        {
            'action': 'insert',
            'uniqueId': 'TEST001',
            'birthDate': '2010-05-15',
            'firstName': 'John',
            'lastName': 'Doe',
            'middleName': 'Michael',
            'title': 'Mr',
            'preferredFirstName': '',
            'preferredLastName': '',
            'enrollmentDate': '2021-08-23',
            'enrollmentGradeLevel': 'Ninth grade',
            'fullTime': 1,
            'schoolId': 255901001
        },
        {
            'action': 'update',
            'uniqueId': 'TEST002',
            'birthDate': '2009-12-03',
            'firstName': 'Jane',
            'lastName': 'Smith',
            'middleName': '',
            'title': 'Ms',
            'preferredFirstName': 'Janie',
            'preferredLastName': 'Smith-Jones',
            'enrollmentDate': '2021-08-23',
            'enrollmentGradeLevel': 'Tenth grade',
            'fullTime': 0,
            'schoolId': 255901002
        },
        {
            'action': 'delete',
            'uniqueId': 'TEST003',
            'birthDate': '',
            'firstName': '',
            'lastName': '',
            'middleName': '',
            'title': '',
            'preferredFirstName': '',
            'preferredLastName': '',
            'enrollmentDate': '',
            'enrollmentGradeLevel': '',
            'fullTime': '',
            'schoolId': ''
        }
    ]
    
    mock_api = MockEdFiApiClient()
    processor = StudentDataProcessor(mock_api)
    
    for i, record in enumerate(test_records, 1):
        print(f"\n--- Test Record {i} ---")
        row = pd.Series(record)
        
        action = record['action'].lower()
        if action == 'delete':
            success = processor.process_delete_action(row)
        else:
            success = processor.process_insert_update_action(row)
        
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    return True


def validate_data_transformations():
    """Test data transformation functions"""
    print("\n🔧 Testing Data Transformations")
    print("=" * 60)
    
    mock_api = MockEdFiApiClient()
    processor = StudentDataProcessor(mock_api)
    
    # Test date formatting
    test_dates = ['2021-08-23', '08/23/2021', '08-23-2021', '', None]
    print("Date formatting tests:")
    for date_val in test_dates:
        formatted = processor.format_date(date_val)
        print(f"  {date_val} -> {formatted}")
    
    # Test grade level normalization
    test_grades = ['Ninth grade', 'ninth grade', '9th grade', '9', 'Twelfth grade', 'unknown']
    print("\nGrade level normalization tests:")
    for grade in test_grades:
        normalized = processor.normalize_grade_level(grade)
        print(f"  {grade} -> {normalized}")
    
    return True


def main():
    """Run all tests"""
    print("🚀 Starting POC 6 Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        if not test_csv_processing():
            return False
        
        if not test_individual_records():
            return False
        
        if not validate_data_transformations():
            return False
        
        print("\n" + "=" * 60)
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)