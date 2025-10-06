# POC 3: Ed-Fi API Student Data Loader

This project demonstrates loading student and enrollment data into an Ed-Fi API using the Data Standard 5 OpenAPI Specification.

## Features

- Loads student data from CSV file into Ed-Fi API
- Creates student records and student-school associations (enrollments)
- Uses Ed-Fi Data Standard v5 OpenAPI specification
- Supports authentication and proper error handling

## Usage

1. Configure environment variables in `.env` file:
   ```
   EDFI_API_BASE_URL=https://your-edfi-api.com/data/v3
   EDFI_API_KEY=your-api-key
   EDFI_API_SECRET=your-api-secret
   ```

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run the loader:
   ```bash
   poetry run python load_students.py
   ```

## Data Format

The CSV file should contain the following columns:
- uniqueId: Student unique identifier
- birthDate: Student birth date (YYYY-MM-DD)
- firstName: Student first name
- lastName: Student last name
- middleName: Student middle name (optional)
- title: Student title (optional)
- preferredFirstName: Preferred first name (optional)
- preferredLastName: Preferred last name (optional)
- enrollmentDate: School enrollment date (YYYY-MM-DD)
- enrollmentGradeLevel: Grade level for enrollment
- fullTime: Full-time status (1 for true, 0 for false)
- schoolId: School identifier for enrollment