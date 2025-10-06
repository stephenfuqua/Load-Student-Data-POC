"""
Ed-Fi API client for CRUD operations on student and enrollment data.
"""
import requests
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
from oauth2_client import OAuth2Client


class EdFiApiClient:
    """Client for interacting with Ed-Fi Data Management API."""
    
    def __init__(self, base_url: str, oauth_client: OAuth2Client):
        """
        Initialize the Ed-Fi API client.
        
        Args:
            base_url: Base URL for Ed-Fi Data Management API
            oauth_client: OAuth2 client for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.oauth_client = oauth_client
        self.logger = logging.getLogger(__name__)
    
    def create_student(self, student_data: Dict) -> bool:
        """
        Create a new student record.
        
        Args:
            student_data: Student data in Ed-Fi format
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = urljoin(self.base_url + '/', 'students')
        return self._make_request('POST', endpoint, student_data)
    
    def update_student(self, student_id: str, student_data: Dict) -> bool:
        """
        Update an existing student record.
        
        Args:
            student_id: Student unique ID
            student_data: Updated student data in Ed-Fi format
            
        Returns:
            True if successful, False otherwise
        """
        # First, get the student record to get the Ed-Fi ID
        student_edfi_id = self._get_student_edfi_id(student_id)
        if not student_edfi_id:
            self.logger.error(f"Student not found for update: {student_id}")
            return False
        
        endpoint = urljoin(self.base_url + '/', f'students/{student_edfi_id}')
        return self._make_request('PUT', endpoint, student_data)
    
    def delete_student(self, student_id: str) -> bool:
        """
        Delete a student record.
        
        Args:
            student_id: Student unique ID
            
        Returns:
            True if successful, False otherwise
        """
        # First, get the student record to get the Ed-Fi ID
        student_edfi_id = self._get_student_edfi_id(student_id)
        if not student_edfi_id:
            self.logger.error(f"Student not found for deletion: {student_id}")
            return False
        
        endpoint = urljoin(self.base_url + '/', f'students/{student_edfi_id}')
        return self._make_request('DELETE', endpoint)
    
    def create_enrollment(self, enrollment_data: Dict) -> bool:
        """
        Create a new student school enrollment.
        
        Args:
            enrollment_data: Enrollment data in Ed-Fi format
            
        Returns:
            True if successful, False otherwise
        """
        endpoint = urljoin(self.base_url + '/', 'studentSchoolAssociations')
        return self._make_request('POST', endpoint, enrollment_data)
    
    def update_enrollment(self, student_id: str, school_id: int, enrollment_data: Dict) -> bool:
        """
        Update an existing student school enrollment.
        
        Args:
            student_id: Student unique ID
            school_id: School ID
            enrollment_data: Updated enrollment data in Ed-Fi format
            
        Returns:
            True if successful, False otherwise
        """
        # Get the enrollment record to get the Ed-Fi ID
        enrollment_edfi_id = self._get_enrollment_edfi_id(student_id, school_id)
        if not enrollment_edfi_id:
            self.logger.error(f"Enrollment not found for update: student {student_id}, school {school_id}")
            return False
        
        endpoint = urljoin(self.base_url + '/', f'studentSchoolAssociations/{enrollment_edfi_id}')
        return self._make_request('PUT', endpoint, enrollment_data)
    
    def delete_enrollment(self, student_id: str, school_id: int) -> bool:
        """
        Delete a student school enrollment.
        
        Args:
            student_id: Student unique ID
            school_id: School ID
            
        Returns:
            True if successful, False otherwise
        """
        # Get the enrollment record to get the Ed-Fi ID
        enrollment_edfi_id = self._get_enrollment_edfi_id(student_id, school_id)
        if not enrollment_edfi_id:
            self.logger.error(f"Enrollment not found for deletion: student {student_id}, school {school_id}")
            return False
        
        endpoint = urljoin(self.base_url + '/', f'studentSchoolAssociations/{enrollment_edfi_id}')
        return self._make_request('DELETE', endpoint)
    
    def _get_student_edfi_id(self, student_unique_id: str) -> Optional[str]:
        """
        Get the Ed-Fi internal ID for a student by unique ID.
        
        Args:
            student_unique_id: Student unique ID
            
        Returns:
            Ed-Fi internal ID or None if not found
        """
        endpoint = urljoin(self.base_url + '/', 'students')
        params = {'studentUniqueId': student_unique_id}
        
        try:
            headers = self.oauth_client.get_auth_headers()
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code == 200:
                students = response.json()
                if students and len(students) > 0:
                    return students[0].get('id')
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
                
        except requests.RequestException as e:
            self.logger.error(f"Error getting student Ed-Fi ID: {e}")
        
        return None
    
    def _get_enrollment_edfi_id(self, student_unique_id: str, school_id: int) -> Optional[str]:
        """
        Get the Ed-Fi internal ID for a student enrollment.
        
        Args:
            student_unique_id: Student unique ID
            school_id: School ID
            
        Returns:
            Ed-Fi internal ID or None if not found
        """
        endpoint = urljoin(self.base_url + '/', 'studentSchoolAssociations')
        params = {
            'studentUniqueId': student_unique_id,
            'schoolId': school_id
        }
        
        try:
            headers = self.oauth_client.get_auth_headers()
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code == 200:
                enrollments = response.json()
                if enrollments and len(enrollments) > 0:
                    return enrollments[0].get('id')
            elif response.status_code == 404:
                return None
            else:
                response.raise_for_status()
                
        except requests.RequestException as e:
            self.logger.error(f"Error getting enrollment Ed-Fi ID: {e}")
        
        return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> bool:
        """
        Make an HTTP request to the Ed-Fi API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint URL
            data: Request data for POST/PUT requests
            
        Returns:
            True if successful, False otherwise
        """
        try:
            headers = self.oauth_client.get_auth_headers()
            
            if method.upper() == 'GET':
                response = requests.get(endpoint, headers=headers)
            elif method.upper() == 'POST':
                response = requests.post(endpoint, headers=headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(endpoint, headers=headers, json=data)
            elif method.upper() == 'DELETE':
                response = requests.delete(endpoint, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code in [200, 201, 204]:
                self.logger.info(f"Successful {method} request to {endpoint}")
                return True
            else:
                self.logger.error(f"API request failed: {method} {endpoint} - {response.status_code}: {response.text}")
                return False
                
        except requests.RequestException as e:
            self.logger.error(f"Request error: {method} {endpoint} - {e}")
            return False