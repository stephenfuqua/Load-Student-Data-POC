#!/usr/bin/env python3
"""
Demo script showing how the Ed-Fi Student Data Loader would work
This creates a mock API client that simulates successful responses
"""

import sys
import os
import json
from unittest.mock import Mock, patch
sys.path.append('.')

from load_student_data import StudentDataLoader, EdFiApiClient

def demo_student_loading():
    """Demonstrate the student loading functionality with a mock API"""
    print("=== Ed-Fi Student Data Loader Demo ===\n")
    
    # Create a mock API client that simulates successful responses
    api_client = EdFiApiClient("https://demo.api.ed-fi.org/v5.3/api")
    
    # Mock the API methods to simulate successful responses
    api_client.authenticate = Mock(return_value=True)
    api_client.create_student = Mock(return_value=True)
    api_client.create_enrollment = Mock(return_value=True)
    
    # Create the loader
    loader = StudentDataLoader("./students.csv", api_client)
    
    print("1. Loading CSV data...")
    df = loader.load_csv_data()
    print(f"   ✓ Loaded {len(df)} student records\n")
    
    print("2. Demonstrating data transformation...")
    for index, row in df.head(2).iterrows():
        student_data = loader.transform_student_data(row)
        enrollment_data = loader.transform_enrollment_data(row)
        
        print(f"\n   --- Student Record {index + 1} ---")
        print(f"   Student JSON:")
        print(f"   {json.dumps(student_data, indent=6)}")
        
        print(f"\n   Enrollment JSON:")
        print(f"   {json.dumps(enrollment_data, indent=6)}")
    
    print("\n\n3. Simulating API calls...")
    success = loader.load_data()
    
    print(f"\n4. Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"   API authenticate() called: {api_client.authenticate.called}")
    print(f"   API create_student() called {api_client.create_student.call_count} times")
    print(f"   API create_enrollment() called {api_client.create_enrollment.call_count} times")
    
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    demo_student_loading()