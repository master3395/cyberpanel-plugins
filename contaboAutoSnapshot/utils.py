# -*- coding: utf-8 -*-
"""
Contabo API utility functions for snapshot management
"""
import requests
import json
from datetime import datetime
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging


class ContaboAPI:
    """Contabo API client for snapshot operations"""
    
    def __init__(self, client_id, client_secret, api_key, api_secret, base_url='https://api.contabo.com/v1'):
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.access_token = None
        self.token_expires_at = None
    
    def _get_access_token(self):
        """Get OAuth2 access token from Contabo API"""
        try:
            if self.access_token and self.token_expires_at:
                # Check if token is still valid (with 5 minute buffer)
                from django.utils import timezone
                from datetime import datetime
                if datetime.now(timezone.utc) < self.token_expires_at:
                    return self.access_token
            
            # Request new token
            token_url = f"{self.base_url}/auth/tokens"
            auth = (self.client_id, self.client_secret)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            data = {
                'grant_type': 'client_credentials',
            }
            
            response = requests.post(token_url, auth=auth, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 3600)  # Default to 1 hour
            
            # Calculate expiration time
            from django.utils import timezone
            from datetime import timedelta
            self.token_expires_at = timezone.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer
            
            logging.writeToFile(f"Contabo API: Successfully obtained access token")
            return self.access_token
            
        except requests.exceptions.RequestException as e:
            logging.writeToFile(f"Contabo API: Failed to get access token: {str(e)}")
            raise Exception(f"Failed to authenticate with Contabo API: {str(e)}")
        except Exception as e:
            logging.writeToFile(f"Contabo API: Error getting access token: {str(e)}")
            raise Exception(f"Error authenticating with Contabo API: {str(e)}")
    
    def _get_headers(self):
        """Get headers for API requests"""
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'x-request-id': f'cyberpanel-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        }
    
    def test_connection(self):
        """Test API connection by listing instances"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'message': 'Successfully connected to Contabo API',
                'data': response.json()
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e.response, 'text'):
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            return {
                'success': False,
                'message': f'Failed to connect to Contabo API: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error testing connection: {str(e)}'
            }
    
    def create_snapshot(self, instance_id, snapshot_name, description='', include_ram=False):
        """Create a snapshot for a VPS instance"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances/{instance_id}/snapshots"
            
            payload = {
                'name': snapshot_name,
                'description': description,
                'vmstate': include_ram,  # Contabo uses 'vmstate' for RAM inclusion
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            snapshot_data = response.json()
            
            logging.writeToFile(f"Contabo API: Successfully created snapshot '{snapshot_name}' for instance {instance_id}")
            
            return {
                'success': True,
                'message': f'Snapshot "{snapshot_name}" created successfully',
                'data': snapshot_data
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_data.get('error', error_msg))
                except:
                    error_msg = e.response.text or error_msg
            
            logging.writeToFile(f"Contabo API: Failed to create snapshot: {error_msg}")
            return {
                'success': False,
                'message': f'Failed to create snapshot: {error_msg}'
            }
        except Exception as e:
            logging.writeToFile(f"Contabo API: Error creating snapshot: {str(e)}")
            return {
                'success': False,
                'message': f'Error creating snapshot: {str(e)}'
            }
    
    def list_snapshots(self, instance_id):
        """List all snapshots for a VPS instance"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances/{instance_id}/snapshots"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            
            return {
                'success': False,
                'message': f'Failed to list snapshots: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error listing snapshots: {str(e)}'
            }
    
    def delete_snapshot(self, instance_id, snapshot_id):
        """Delete a snapshot"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances/{instance_id}/snapshots/{snapshot_id}"
            
            response = requests.delete(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            logging.writeToFile(f"Contabo API: Successfully deleted snapshot {snapshot_id} for instance {instance_id}")
            
            return {
                'success': True,
                'message': 'Snapshot deleted successfully'
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            
            return {
                'success': False,
                'message': f'Failed to delete snapshot: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error deleting snapshot: {str(e)}'
            }
    
    def list_instances(self):
        """List all VPS instances"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            return {
                'success': True,
                'data': response.json()
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    error_msg = error_data.get('message', error_msg)
                except:
                    error_msg = e.response.text or error_msg
            
            return {
                'success': False,
                'message': f'Failed to list instances: {error_msg}'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Error listing instances: {str(e)}'
            }


def get_contabo_api():
    """Get Contabo API client instance from config"""
    from .models import ContaboConfig
    
    config = ContaboConfig.get_config()
    
    if not config.api_client_id or not config.api_client_secret:
        raise Exception("Contabo API credentials not configured. Please configure API settings first.")
    
    return ContaboAPI(
        client_id=config.api_client_id,
        client_secret=config.api_client_secret,
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.api_base_url
    )
