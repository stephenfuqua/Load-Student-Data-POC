"""
Discovery API client for Ed-Fi API endpoint discovery.
"""
import requests
import logging
from typing import Dict, Optional
from urllib.parse import urljoin


class DiscoveryClient:
    """Client for interacting with Ed-Fi Discovery API."""
    
    def __init__(self, base_url: str):
        """
        Initialize the Discovery client.
        
        Args:
            base_url: Base URL of the Ed-Fi API
        """
        self.base_url = base_url.rstrip('/')
        self.logger = logging.getLogger(__name__)
        
    def get_api_metadata(self) -> Dict:
        """
        Get API metadata from the Discovery API.
        
        Returns:
            Dictionary containing API metadata
            
        Raises:
            requests.RequestException: If the API request fails
        """
        discovery_url = urljoin(self.base_url + '/', 'api')
        
        try:
            response = requests.get(discovery_url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            self.logger.error(f"Failed to get API metadata: {e}")
            raise
    
    def get_oauth_endpoints(self) -> Dict[str, str]:
        """
        Get OAuth2 endpoint URLs from the Discovery API.
        
        Returns:
            Dictionary with 'token' and 'authorize' URLs
            
        Raises:
            requests.RequestException: If the API request fails
            KeyError: If required OAuth endpoints are not found
        """
        try:
            metadata = self.get_api_metadata()
            
            # Extract OAuth endpoints from metadata
            oauth_urls = {}
            
            # Look for OAuth URLs in the metadata structure
            if 'urls' in metadata:
                for url_info in metadata['urls']:
                    if 'oauth' in url_info.get('name', '').lower():
                        oauth_urls['token'] = urljoin(self.base_url + '/', 'oauth/token')
                        oauth_urls['authorize'] = urljoin(self.base_url + '/', 'oauth/authorize')
                        break
            
            # Fallback to standard OAuth endpoints if not found in metadata
            if not oauth_urls:
                oauth_urls = {
                    'token': urljoin(self.base_url + '/', 'oauth/token'),
                    'authorize': urljoin(self.base_url + '/', 'oauth/authorize')
                }
            
            self.logger.info(f"Found OAuth endpoints: {oauth_urls}")
            return oauth_urls
            
        except Exception as e:
            self.logger.error(f"Failed to get OAuth endpoints: {e}")
            raise
    
    def get_data_management_api_base_path(self) -> str:
        """
        Get the Data Management API base path.
        
        Returns:
            Base path for Data Management API
            
        Raises:
            requests.RequestException: If the API request fails
        """
        try:
            metadata = self.get_api_metadata()
            
            # Look for data management API URL in metadata
            if 'urls' in metadata:
                for url_info in metadata['urls']:
                    if 'data' in url_info.get('name', '').lower():
                        return url_info.get('url', urljoin(self.base_url + '/', 'data/v3/'))
            
            # Fallback to standard data management API path
            data_api_path = urljoin(self.base_url + '/', 'data/v3/')
            self.logger.info(f"Using Data Management API base path: {data_api_path}")
            return data_api_path
            
        except Exception as e:
            self.logger.error(f"Failed to get Data Management API base path: {e}")
            raise
    
    def get_openapi_metadata(self) -> Optional[Dict]:
        """
        Get OpenAPI metadata for the Resources API.
        
        Returns:
            OpenAPI specification dictionary or None if not available
        """
        try:
            # Try to get OpenAPI metadata from common endpoints
            openapi_urls = [
                urljoin(self.base_url + '/', 'metadata'),
                urljoin(self.base_url + '/', 'data/v3/metadata'),
                urljoin(self.base_url + '/', 'swagger.json'),
                urljoin(self.base_url + '/', 'api-docs')
            ]
            
            for url in openapi_urls:
                try:
                    response = requests.get(url)
                    if response.status_code == 200:
                        self.logger.info(f"Found OpenAPI metadata at: {url}")
                        return response.json()
                except requests.RequestException:
                    continue
            
            self.logger.warning("OpenAPI metadata not found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get OpenAPI metadata: {e}")
            return None