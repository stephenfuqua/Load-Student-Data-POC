# Ed-Fi Student Data Loader POC

This POC demonstrates loading, updating, and deleting student and enrollment data via the Ed-Fi API using OAuth2 authentication and the Discovery API.

## Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your Ed-Fi API credentials
   ```

3. Run the loader:
   ```bash
   poetry run python main.py
   ```

## Features

- Discovery API integration for endpoint discovery
- OAuth2 client credentials authentication
- CSV-based data input with support for insert, update, and delete operations
- Student and enrollment data handling
- Error handling and logging

## CSV Format

The `students.csv` file should contain columns:
- action: insert, update, or delete
- uniqueId: Student unique identifier
- birthDate: Student birth date (YYYY-MM-DD)
- firstName, lastName, middleName: Student names
- title: Student title (Mr, Ms, Mrs, etc.)
- preferredFirstName, preferredLastName: Preferred names
- enrollmentDate: Enrollment date (YYYY-MM-DD)
- enrollmentGradeLevel: Grade level
- fullTime: 1 for full-time, 0 for part-time
- schoolId: School identifier