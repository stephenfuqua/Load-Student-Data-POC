# POC Four: Ed-Fi Discovery API Integration

This POC demonstrates using the Ed-Fi Discovery API to dynamically discover API endpoints and load student enrollment data into an Ed-Fi API.

## Features

- **Discovery API Integration**: Uses the Ed-Fi Discovery API to:
  - Identify OAuth2 token endpoints
  - Identify Data Management API base path
  - Explore OpenAPI metadata for Resources API endpoints
- **Dynamic Endpoint Discovery**: No hardcoded API endpoints - all discovered at runtime
- **Student Data Loading**: Processes CSV data and loads students and enrollments
- **Poetry Dependency Management**: Uses Poetry for Python dependency management
- **Clean Implementation**: No downloaded JSON files kept (in-memory processing only)

## Requirements

- Python 3.8+
- Poetry for dependency management
- Valid Ed-Fi API credentials (for actual data loading)

## Setup

1. Install Poetry (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

## Usage

### Running the Discovery Demo

```bash
poetry run python load_student_data.py
```

This will demonstrate:
- Discovery API endpoint identification
- OpenAPI metadata exploration
- Data transformation examples
- Sample CSV data processing

### Loading Actual Data

To load actual data into an Ed-Fi API, you would use:

```python
from load_student_data import EdFiDiscoveryClient, StudentDataLoader

# Initialize and discover endpoints
discovery_client = EdFiDiscoveryClient("https://your-edfi-api.com/v7.3/api/")
discovery_client.discover_endpoints()
discovery_client.explore_resources_metadata()

# Load data with valid credentials
loader = StudentDataLoader(discovery_client)
success = loader.process_students_csv(
    "students.csv", 
    "your_client_id", 
    "your_client_secret"
)
```

## Data Format

The script processes CSV files with the following columns:

- `uniqueId`: Student unique identifier
- `birthDate`: Birth date (YYYY-MM-DD)
- `firstName`: Student first name
- `lastName`: Student last name
- `middleName`: Student middle name (optional)
- `title`: Title (Ms, Mr, Mrs, etc.)
- `preferredFirstName`: Preferred first name (optional)
- `preferredLastName`: Preferred last name (optional)
- `enrollmentDate`: Enrollment date (YYYY-MM-DD)
- `enrollmentGradeLevel`: Grade level (e.g., "Ninth grade")
- `fullTime`: Full-time indicator (1 for full-time, 0 for part-time)
- `schoolId`: School identifier

## API Endpoints Used

The script automatically discovers and uses:

- `/ed-fi/students` - For creating student records
- `/ed-fi/studentSchoolAssociations` - For creating enrollment records

## Discovery API Process

1. **Initial Discovery**: Fetches endpoint URLs from the Discovery API
2. **Metadata Exploration**: Downloads OpenAPI metadata to understand available endpoints
3. **Schema Analysis**: Analyzes schemas to understand required fields and data formats
4. **Dynamic Processing**: Uses discovered endpoints to post data

## Error Handling

The script includes comprehensive error handling for:
- API discovery failures
- Authentication errors
- Data validation issues
- Network connectivity problems
- Duplicate record scenarios

## Notes

- This is a demonstration POC showing Discovery API integration
- The sample `students.csv` contains fake data with realistic names
- No JSON files are downloaded or saved (in-memory processing only)
- The script gracefully handles existing records (409 conflicts)
- All API endpoints and schemas are discovered dynamically

## Example Output

```
Ed-Fi Discovery API POC - Student Data Loader
==================================================
Discovering Ed-Fi API endpoints from: https://api.ed-fi.org/v7.3/api/
✓ OAuth2 token endpoint: https://api.ed-fi.org/v7.3/api/oauth/token
✓ Data Management API base path: https://api.ed-fi.org/v7.3/api/data/v3/
✓ Exploring Resources API metadata: https://api.ed-fi.org/v7.3/api/metadata/data/v3/resources/swagger.json
✓ Found 180 student-related endpoints
✓ Found 15 student-school association endpoints

Key endpoints for our POC:
  - /ed-fi/students (for creating students)
  - /ed-fi/studentSchoolAssociations (for enrollment)
```