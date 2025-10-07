# POC 6: Load Student Data using Ed-Fi SDK MCP

This POC demonstrates loading student and enrollment data from a CSV file into an Ed-Fi API using Data Standard 5.2.

## Features

- Support for **insert**, **update**, and **delete** operations
- Student data management (personal information, names, birth date)
- Enrollment data management (school associations, grade levels, entry dates)
- Error handling and progress reporting
- Environment-based configuration

## Requirements

- Python 3.8+
- Poetry for dependency management
- Ed-Fi API access (client credentials)

## Installation

1. Navigate to the POC directory:
```bash
cd poc/six
```

2. Install dependencies using Poetry:
```bash
export PATH="/home/runner/.local/bin:$PATH"
poetry install
```

## Configuration

1. Copy the environment template:
```bash
cp .env.example .env
```

2. Edit `.env` with your Ed-Fi API credentials:
```bash
EDFI_API_BASE_URL=https://your-edfi-api-url.org/data/v3
EDFI_CLIENT_ID=your_client_id
EDFI_CLIENT_SECRET=your_client_secret
STUDENT_CSV_FILE=students.csv
```

## CSV Format

The CSV file should contain the following columns:

| Column | Required | Description |
|--------|----------|-------------|
| action | Yes | Operation type: `insert`, `update`, or `delete` |
| uniqueId | Yes | Student unique identifier |
| birthDate | Yes* | Student birth date (YYYY-MM-DD format) |
| firstName | Yes* | Student first name |
| lastName | Yes* | Student last name |
| middleName | No | Student middle name |
| title | No | Personal title prefix (Mr, Ms, Mrs, etc.) |
| preferredFirstName | No | Preferred first name |
| preferredLastName | No | Preferred last name |
| enrollmentDate | No** | School enrollment date |
| enrollmentGradeLevel | No** | Grade level (Ninth grade, Tenth grade, etc.) |
| fullTime | No | Full-time status (1 = full-time, 0 = part-time) |
| schoolId | No** | School identifier |

\* Required for insert/update operations  
\** Required for enrollment data

### Sample CSV Data

```csv
action,uniqueId,birthDate,firstName,lastName,middleName,title,preferredFirstName,preferredLastName,enrollmentDate,enrollmentGradeLevel,fullTime,schoolId
insert,604835,2016-09-29,Diana,Holt,Emily,Ms,,,2021-08-23,Ninth grade,1,255901001
update,604839,2011-04-26,Meredith,Lloyd,Felicia,Mrs,,,2021-08-23,Eleventh grade,1,255901001
delete,604834,,,,,,,,,,,,
```

## Usage

Run the student data loader:

```bash
export PATH="/home/runner/.local/bin:$PATH"
poetry run python student_loader.py
```

## Data Operations

### Insert
Creates new student and enrollment records. If a student with the same `uniqueId` already exists, the record will be updated (upsert behavior).

### Update
Updates existing student and enrollment records. Uses the same upsert behavior as insert.

### Delete
Removes student records from the Ed-Fi API. Enrollment records are typically removed automatically through cascade delete policies.

## Error Handling

The script provides detailed error reporting:
- ✅ Success indicators for completed operations
- ❌ Error messages with details
- ⚠️ Warnings for missing data or records not found
- 📊 Summary statistics at completion

## Dependencies

This POC uses the following Python packages:
- `requests` - HTTP client for Ed-Fi API calls
- `pandas` - CSV data processing
- `python-dotenv` - Environment variable management

## Ed-Fi Data Standard 5.2

This implementation uses Ed-Fi Data Standard 5.2 endpoints:
- `/ed-fi/students` - Student demographic data
- `/ed-fi/studentSchoolAssociations` - School enrollment data

## Architecture

The code is organized into three main classes:

1. **EdFiApiClient** - Handles authentication and API communication
2. **StudentDataProcessor** - Processes CSV data and orchestrates operations
3. **Main function** - Configuration and execution entry point

## License

Licensed under the Apache License, Version 2.0.