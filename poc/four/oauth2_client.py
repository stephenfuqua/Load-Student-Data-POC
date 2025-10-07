"""
OAuth2 client for Ed-Fi API authentication using client credentials flow.
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional


class OAuth2Client:
    """Client for OAuth2 authentication with Ed-Fi API."""
    
    def __init__(self, token_url: str, client_id: str, client_secret: str):
        """
        Initialize OAuth2 client.
        
        Args:
            token_url: OAuth2 token endpoint URL
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
        """
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.logger = logging.getLogger(__name__)
    
    def get_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            Valid access token
            
        Raises:
            requests.RequestException: If authentication fails
        """
        if self._is_token_valid():
            return self.access_token
        
        return self._refresh_token()
    
    def _is_token_valid(self) -> bool:
        """
        Check if the current token is valid and not expired.
        
        Returns:
            True if token is valid, False otherwise
        """
        if not self.access_token or not self.token_expires_at:
            return False
        
        # Check if token expires within the next 60 seconds
        buffer_time = timedelta(seconds=60)
        return datetime.now() < (self.token_expires_at - buffer_time)
    
    def _refresh_token(self) -> str:
        """
        Request a new access token using client credentials flow.
        
        Returns:
            New access token
            
        Raises:
            requests.RequestException: If the token request fails
        """
        try:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            self.logger.info(f"Requesting new access token from {self.token_url}")
            response = requests.post(self.token_url, data=data, headers=headers)
            response.raise_for_status()
            
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            self.logger.info(f"Successfully obtained access token, expires at {self.token_expires_at}")
            return self.access_token
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get access token: {e}")
            raise
        except KeyError as e:
            self.logger.error(f"Invalid token response format: {e}")
            raise requests.RequestException(f"Invalid token response: missing {e}")
    
    def get_auth_headers(self) -> dict:
        """
        Get HTTP headers with valid authentication.
        
        Returns:
            Dictionary with Authorization header
        """
        token = self.get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }