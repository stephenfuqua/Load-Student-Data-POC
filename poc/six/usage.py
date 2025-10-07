#!/usr/bin/env python3
"""
Simple usage example for POC 6: Load Student Data

This script demonstrates basic usage without requiring actual API credentials.
For real usage, see the main student_loader.py script.
"""

import os
import sys

def show_usage():
    """Show usage information"""
    print("=" * 60)
    print("POC 6: Load Student Data using Ed-Fi SDK MCP")
    print("=" * 60)
    print()
    print("📋 SETUP INSTRUCTIONS:")
    print("1. Copy .env.example to .env")
    print("2. Configure your Ed-Fi API credentials in .env:")
    print("   - EDFI_API_BASE_URL")
    print("   - EDFI_CLIENT_ID")
    print("   - EDFI_CLIENT_SECRET")
    print("   - STUDENT_CSV_FILE (optional, defaults to students.csv)")
    print()
    print("🚀 USAGE:")
    print("poetry run python student_loader.py")
    print()
    print("🧪 TESTING:")
    print("poetry run python test_student_loader.py")
    print()
    print("📊 CSV FORMAT:")
    print("The CSV file should contain columns:")
    print("- action: insert, update, or delete")
    print("- uniqueId: Student unique identifier")
    print("- birthDate, firstName, lastName: Required for insert/update")
    print("- middleName, title, preferredFirstName, preferredLastName: Optional")
    print("- enrollmentDate, enrollmentGradeLevel, fullTime, schoolId: Enrollment data")
    print()
    print("✅ SUPPORTED OPERATIONS:")
    print("- Insert: Create new student and enrollment records")
    print("- Update: Update existing student and enrollment records")
    print("- Delete: Remove student records")
    print()
    print("📖 For detailed documentation, see README.md")


if __name__ == "__main__":
    show_usage()