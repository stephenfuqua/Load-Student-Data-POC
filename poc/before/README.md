# Load Student Data POC - Before

This directory contains the POC 1 implementation for loading student data into an Ed-Fi ODS/API.

## Setup

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Create environment configuration:
   ```bash
   cp .env.template .env
   ```
   
4. Edit `.env` file with your Ed-Fi API credentials:
   ```
   EDFI_API_BASE_URL=https://your-edfi-api.com/v7.2/api
   EDFI_API_CLIENT_ID=your_client_id
   EDFI_API_CLIENT_SECRET=your_client_secret
   ```

## Usage

Run the script to load student data:

```bash
poetry run python load_students.py
```

## Data Mapping

### CSV to Students Endpoint

| CSV Column         | API Property         |
| ------------------ | -------------------- |
| uniqueId           | studentUniqueId      |
| birthDate          | birthDate            |
| firstName          | firstName            |
| lastName           | lastSurname          |
| middleName         | middleName           |
| title              | personalTitlePrefix  |
| preferredFirstName | preferredFirstName   |
| preferredLastName  | preferredLastSurname |

### CSV to StudentSchoolAssociations Endpoint

| CSV Column           | API Property              |
| -------------------- | ------------------------- |
| uniqueId             | studentReference.studentUniqueId |
| schoolId             | schoolReference.schoolId  |
| enrollmentDate       | entryDate                 |
| enrollmentGradeLevel | entryGradeLevelDescriptor |
| fullTime             | fullTimeEquivalency       |

The `entryGradeLevelDescriptor` is formatted as: `uri://ed-fi.org/GradeLevelDescriptor#{enrollmentGradeLevel}`

## Features

- Authenticates with Ed-Fi ODS/API using OAuth 2.0 client credentials flow
- Uses the Discovery API to automatically find the correct data management API endpoints (with fallback to default paths)
- Reads student data from `students.csv` file
- Creates student records first, then student-school associations
- Handles optional fields (empty values are excluded from API calls)
- Comprehensive logging for debugging and monitoring
- Error handling with detailed error messages