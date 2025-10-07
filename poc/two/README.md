# POC 2: Ed-Fi Student Data Loader

This POC demonstrates loading student and enrollment data from a CSV file into an Ed-Fi API.

## Features

- Reads student data from CSV file
- Transforms data to Ed-Fi API format
- Creates Student records in Ed-Fi API
- Creates StudentSchoolEnrollment records in Ed-Fi API
- Handles authentication with Ed-Fi API
- Comprehensive error handling and logging
- Supports optional fields (middle name, preferred names, etc.)

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your Ed-Fi API credentials
   ```

3. Prepare your CSV file (see `students.csv` for example format)

## Usage

### Basic Usage
```bash
python load_student_data.py
```

### With Environment Variables
```bash
export EDFI_BASE_URL="https://your-edfi-api.org/api"
export EDFI_CLIENT_ID="your_client_id"
export EDFI_CLIENT_SECRET="your_client_secret"
export CSV_FILE_PATH="./students.csv"
python load_student_data.py
```

## CSV File Format

The CSV file should contain the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| uniqueId | Yes | Unique student identifier |
| birthDate | Yes | Student birth date (YYYY-MM-DD) |
| firstName | Yes | Student first name |
| lastName | Yes | Student last name |
| middleName | No | Student middle name |
| title | No | Student title (Mr, Ms, Mrs, etc.) |
| preferredFirstName | No | Student preferred first name |
| preferredLastName | No | Student preferred last name |
| enrollmentDate | Yes | School enrollment date (YYYY-MM-DD) |
| enrollmentGradeLevel | Yes | Grade level (e.g., "Ninth grade") |
| fullTime | Yes | Full-time status (1 = full-time, 0 = part-time) |
| schoolId | Yes | School identifier |

## Ed-Fi API Endpoints Used

- `POST /data/v3/ed-fi/students` - Create student records
- `POST /data/v3/ed-fi/studentSchoolEnrollments` - Create enrollment records
- `POST /oauth/token` - Authentication

## Error Handling

The script includes comprehensive error handling:
- Authentication failures
- Network connectivity issues
- Duplicate records (409 responses are handled gracefully)
- Invalid data formats
- Missing required fields

## Logging

All operations are logged with timestamps and appropriate log levels:
- INFO: Successful operations and progress updates
- WARNING: Non-critical issues (e.g., duplicate records)
- ERROR: Critical failures that prevent processing

## Example Output

```
2023-10-03 16:47:00 - INFO - Successfully authenticated with Ed-Fi API
2023-10-03 16:47:01 - INFO - Loaded 10 records from ./students.csv
2023-10-03 16:47:02 - INFO - Successfully created student 604835
2023-10-03 16:47:02 - INFO - Successfully created enrollment for student 604835
2023-10-03 16:47:03 - INFO - Successfully created student 604836
2023-10-03 16:47:03 - INFO - Successfully created enrollment for student 604836
...
2023-10-03 16:47:10 - INFO - Data loading completed: 10 successful, 0 errors
2023-10-03 16:47:10 - INFO - Student data loading completed successfully
```