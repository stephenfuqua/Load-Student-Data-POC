#!/usr/bin/env python3
"""
Test script for Ed-Fi Student Data Loader

This script tests the basic functionality without making actual API calls.
"""
import os
import sys
import tempfile
from pathlib import Path

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from discovery_client import DiscoveryClient
from oauth2_client import OAuth2Client
from data_handler import StudentDataHandler
from edfi_client import EdFiApiClient


def test_discovery_client():
    """Test Discovery client functionality."""
    print("Testing Discovery Client...")
    
    # Test with a mock URL (this will fail but should handle gracefully)
    client = DiscoveryClient("https://api.ed-fi.org/v7.3/api")
    
    try:
        # This will fail but shouldn't crash
        oauth_endpoints = client.get_oauth_endpoints()
        print(f"OAuth endpoints: {oauth_endpoints}")
    except Exception as e:
        print(f"Expected failure for Discovery API (no real endpoint): {e}")
    
    print("Discovery Client test completed")


def test_data_handler():
    """Test Data Handler functionality."""
    print("\nTesting Data Handler...")
    
    # Create a temporary CSV file for testing
    csv_content = """action,uniqueId,birthDate,firstName,lastName,middleName,title,preferredFirstName,preferredLastName,enrollmentDate,enrollmentGradeLevel,fullTime,schoolId
insert,604835,2016-09-29,Diana,Holt,Emily,Ms,,,2021-08-23,Ninth grade,1,255901001
update,604839,2011-04-26,Meredith,Lloyd,Felicia,Mrs,,,2021-08-23,Eleventh grade,1,255901001
delete,604834,,,,,,,,,,,
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        f.write(csv_content)
        temp_csv_path = f.name
    
    try:
        # Test data loading and validation
        handler = StudentDataHandler(temp_csv_path)
        df = handler.load_data()
        print(f"Loaded {len(df)} records")
        
        is_valid = handler.validate_data(df)
        print(f"Data validation: {'PASSED' if is_valid else 'FAILED'}")
        
        # Test data transformation
        first_row = df.iloc[0]
        student_data = handler.transform_to_edfi_format(first_row)
        enrollment_data = handler.transform_to_enrollment_format(first_row)
        
        print(f"Student data: {student_data}")
        print(f"Enrollment data: {enrollment_data}")
        
        # Test grouping by action
        records_by_action = handler.get_records_by_action(df)
        for action, records in records_by_action.items():
            print(f"{action}: {len(records)} records")
        
    finally:
        # Clean up temporary file
        os.unlink(temp_csv_path)
    
    print("Data Handler test completed")


def test_oauth_client():
    """Test OAuth2 client functionality."""
    print("\nTesting OAuth2 Client...")
    
    # Test initialization (won't make actual requests)
    client = OAuth2Client(
        "https://api.ed-fi.org/oauth/token",
        "test_client_id",
        "test_client_secret"
    )
    
    print("OAuth2 client initialized successfully")
    
    # Test token validation logic
    is_valid = client._is_token_valid()
    print(f"Token valid (should be False): {is_valid}")
    
    print("OAuth2 Client test completed")


def test_integration():
    """Test integration with the main CSV file."""
    print("\nTesting Integration with students.csv...")
    
    csv_file = Path(__file__).parent / "students.csv"
    if not csv_file.exists():
        print("students.csv not found - skipping integration test")
        return
    
    handler = StudentDataHandler(str(csv_file))
    df = handler.load_data()
    
    print(f"Loaded {len(df)} records from students.csv")
    
    is_valid = handler.validate_data(df)
    print(f"Data validation: {'PASSED' if is_valid else 'FAILED'}")
    
    records_by_action = handler.get_records_by_action(df)
    for action, records in records_by_action.items():
        print(f"{action}: {len(records)} records")
    
    print("Integration test completed")


def main():
    """Run all tests."""
    print("Ed-Fi Student Data Loader - Test Suite")
    print("=" * 50)
    
    test_discovery_client()
    test_data_handler()
    test_oauth_client()
    test_integration()
    
    print("\n" + "=" * 50)
    print("All tests completed!")


if __name__ == "__main__":
    main()