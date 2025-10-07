#!/usr/bin/env python3
"""
Test script for Ed-Fi API Student Data Loader

This script tests the data mapping functionality without making actual API calls.
"""

import os
import sys
import csv
from datetime import datetime

# Add the current directory to Python path to import our module
sys.path.insert(0, os.path.dirname(__file__))

from load_students import StudentDataMapper


def test_student_mapping():
    """Test student data mapping"""
    print("Testing Student Data Mapping...")
    print("=" * 40)
    
    # Sample CSV row
    test_row = {
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
    }
    
    # Test student payload creation
    student_payload = StudentDataMapper.create_student_payload(test_row)
    print("Student Payload:")
    for key, value in student_payload.items():
        print(f"  {key}: {value}")
    
    print()
    
    # Test student school association payload creation
    association_payload = StudentDataMapper.create_student_school_association_payload(test_row)
    print("Student School Association Payload:")
    for key, value in association_payload.items():
        print(f"  {key}: {value}")
    
    print()


def test_csv_parsing():
    """Test CSV file parsing"""
    print("Testing CSV File Parsing...")
    print("=" * 40)
    
    csv_file = os.path.join(os.path.dirname(__file__), 'students.csv')
    
    if not os.path.exists(csv_file):
        print(f"Error: CSV file not found: {csv_file}")
        return
    
    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            print(f"CSV Headers: {reader.fieldnames}")
            print()
            
            row_count = 0
            for row in reader:
                row_count += 1
                if row_count <= 3:  # Show first 3 rows
                    print(f"Row {row_count}:")
                    for key, value in row.items():
                        print(f"  {key}: {value}")
                    print()
            
            print(f"Total rows: {row_count}")
    
    except Exception as e:
        print(f"Error reading CSV file: {e}")


def test_grade_level_mapping():
    """Test grade level mapping"""
    print("Testing Grade Level Mapping...")
    print("=" * 40)
    
    test_grades = [
        'Ninth grade',
        'Tenth grade', 
        'Eleventh grade',
        'Twelfth grade'
    ]
    
    for grade in test_grades:
        mapped = StudentDataMapper.map_grade_level(grade)
        print(f"  {grade} -> {mapped}")
    
    print()


def main():
    """Main test function"""
    print("Ed-Fi API Student Data Loader - Test Suite")
    print("=" * 50)
    print()
    
    test_csv_parsing()
    test_student_mapping()
    test_grade_level_mapping()
    
    print("All tests completed!")


if __name__ == '__main__':
    main()