"""
CSV data handler for student and enrollment data.
"""
import pandas as pd
import logging
from typing import List, Dict, Optional
from datetime import datetime


class StudentDataHandler:
    """Handler for processing student CSV data."""
    
    def __init__(self, csv_file_path: str):
        """
        Initialize the data handler.
        
        Args:
            csv_file_path: Path to the CSV file containing student data
        """
        self.csv_file_path = csv_file_path
        self.logger = logging.getLogger(__name__)
        
    def load_data(self) -> pd.DataFrame:
        """
        Load student data from CSV file.
        
        Returns:
            DataFrame containing student data
            
        Raises:
            FileNotFoundError: If CSV file is not found
            pd.errors.EmptyDataError: If CSV file is empty
        """
        try:
            df = pd.read_csv(self.csv_file_path)
            self.logger.info(f"Loaded {len(df)} records from {self.csv_file_path}")
            return df
        except FileNotFoundError:
            self.logger.error(f"CSV file not found: {self.csv_file_path}")
            raise
        except pd.errors.EmptyDataError:
            self.logger.error(f"CSV file is empty: {self.csv_file_path}")
            raise
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate the CSV data structure and content.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        required_columns = [
            'action', 'uniqueId', 'birthDate', 'firstName', 'lastName',
            'enrollmentDate', 'enrollmentGradeLevel', 'fullTime', 'schoolId'
        ]
        
        # Check for required columns
        missing_columns = set(required_columns) - set(df.columns)
        if missing_columns:
            self.logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        # Check for valid actions
        valid_actions = {'insert', 'update', 'delete'}
        invalid_actions = set(df['action'].dropna()) - valid_actions
        if invalid_actions:
            self.logger.error(f"Invalid actions found: {invalid_actions}")
            return False
        
        self.logger.info("Data validation passed")
        return True
    
    def transform_to_edfi_format(self, row: pd.Series) -> Dict:
        """
        Transform a CSV row to Ed-Fi API format.
        
        Args:
            row: Pandas Series representing a CSV row
            
        Returns:
            Dictionary in Ed-Fi API format
        """
        # Base student data
        student_data = {
            'studentUniqueId': str(row['uniqueId']),
            'birthDate': self._format_date(row.get('birthDate')),
            'firstName': row.get('firstName', ''),
            'lastSurname': row.get('lastName', ''),
        }
        
        # Optional fields
        if pd.notna(row.get('middleName')):
            student_data['middleName'] = row['middleName']
        
        if pd.notna(row.get('preferredFirstName')):
            student_data['preferredFirstName'] = row['preferredFirstName']
        
        if pd.notna(row.get('preferredLastName')):
            student_data['preferredLastName'] = row['preferredLastName']
        
        # Personal title
        if pd.notna(row.get('title')):
            student_data['personalTitlePrefix'] = row['title']
        
        return student_data
    
    def transform_to_enrollment_format(self, row: pd.Series) -> Dict:
        """
        Transform a CSV row to Ed-Fi enrollment format.
        
        Args:
            row: Pandas Series representing a CSV row
            
        Returns:
            Dictionary in Ed-Fi enrollment API format
        """
        enrollment_data = {
            'studentReference': {
                'studentUniqueId': str(row['uniqueId'])
            },
            'schoolReference': {
                'schoolId': int(row['schoolId'])
            },
            'entryDate': self._format_date(row.get('enrollmentDate')),
            'gradeLevel': self._map_grade_level(row.get('enrollmentGradeLevel')),
            'fullTimeEquivalency': float(row.get('fullTime', 0))
        }
        
        return enrollment_data
    
    def _format_date(self, date_value) -> Optional[str]:
        """
        Format date value to Ed-Fi API format (YYYY-MM-DD).
        
        Args:
            date_value: Date value to format
            
        Returns:
            Formatted date string or None
        """
        if pd.isna(date_value) or date_value == '':
            return None
        
        try:
            # Try to parse the date and format it
            if isinstance(date_value, str):
                parsed_date = pd.to_datetime(date_value)
                return parsed_date.strftime('%Y-%m-%d')
            return str(date_value)
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid date format: {date_value}")
            return None
    
    def _map_grade_level(self, grade_level) -> str:
        """
        Map grade level text to Ed-Fi descriptor.
        
        Args:
            grade_level: Grade level from CSV
            
        Returns:
            Ed-Fi grade level descriptor
        """
        grade_mapping = {
            'Ninth grade': 'Ninth grade',
            'Tenth grade': 'Tenth grade',
            'Eleventh grade': 'Eleventh grade',
            'Twelfth grade': 'Twelfth grade',
            '9th grade': 'Ninth grade',
            '10th grade': 'Tenth grade',
            '11th grade': 'Eleventh grade',
            '12th grade': 'Twelfth grade',
            '9': 'Ninth grade',
            '10': 'Tenth grade',
            '11': 'Eleventh grade',
            '12': 'Twelfth grade'
        }
        
        return grade_mapping.get(str(grade_level), str(grade_level))
    
    def get_records_by_action(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """
        Group records by action type.
        
        Args:
            df: DataFrame containing student data
            
        Returns:
            Dictionary with actions as keys and lists of records as values
        """
        records_by_action = {
            'insert': [],
            'update': [],
            'delete': []
        }
        
        for _, row in df.iterrows():
            action = row['action'].lower()
            if action in records_by_action:
                if action == 'delete':
                    # For delete operations, we only need the unique ID
                    record = {'studentUniqueId': str(row['uniqueId'])}
                else:
                    # For insert/update, transform the full record
                    record = {
                        'student': self.transform_to_edfi_format(row),
                        'enrollment': self.transform_to_enrollment_format(row) if pd.notna(row.get('schoolId')) else None
                    }
                records_by_action[action].append(record)
        
        return records_by_action