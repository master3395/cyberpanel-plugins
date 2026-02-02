# -*- coding: utf-8 -*-
"""
Contabo API utility functions for snapshot management
"""
import uuid
import requests
import json
from datetime import datetime
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

# Contabo snapshot limits by productId (from Contabo docs: VPS 10=1, VPS 20=2, VPS 30+=3)
SNAPSHOT_LIMIT_BY_PRODUCT = {
    'V91': 1, 'V92': 1, 'V93': 1,  # VPS 10
    'V94': 2, 'V95': 2, 'V96': 2,  # VPS 20
    'V97': 3, 'V98': 3, 'V99': 3, 'V100': 3, 'V101': 3, 'V102': 3,
    'V103': 3, 'V104': 3, 'V105': 3, 'V106': 3, 'V107': 3,  # VPS 30-60
    'V8': 3, 'V9': 3, 'V10': 3, 'V11': 3, 'V16': 3,  # VDS
}


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
        """Get OAuth2 access token from Contabo API.
        Contabo uses auth.contabo.com with grant_type=password:
        - API User = email (api_key field)
        - API Password = api_secret field
        - Client ID + Client Secret from Customer Control Panel
        """
        try:
            if self.access_token and self.token_expires_at:
                from django.utils import timezone
                from datetime import datetime
                if datetime.now(timezone.utc) < self.token_expires_at:
                    return self.access_token
            
            # Contabo auth: https://auth.contabo.com with grant_type=password
            token_url = 'https://auth.contabo.com/auth/realms/contabo/protocol/openid-connect/token'
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            data = {
                'grant_type': 'password',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'username': self.api_key or '',   # API User = your Contabo login email
                'password': self.api_secret or '',  # API Password (set in Control Panel)
            }
            if not data['username'] or not data['password']:
                raise Exception("API User (email) and API Password are required. Get them from my.contabo.com/api")
            
            response = requests.post(token_url, headers=headers, data=data, timeout=30)
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
        """Get headers for API requests. Contabo requires valid UUID4 for x-request-id."""
        token = self._get_access_token()
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'x-request-id': str(uuid.uuid4()),
        }
    
    def get_snapshot_counts_per_instance(self):
        """Get current snapshot count for each instance. Returns {instance_id: count}."""
        result = {}
        try:
            inst_resp = self.list_instances()
            if not inst_resp.get('success') or not inst_resp.get('data'):
                return result
            data = inst_resp['data']
            instances = data.get('data', []) if isinstance(data, dict) else []
            for inst in instances:
                iid = inst.get('instanceId') or inst.get('instance_id')
                if iid is None:
                    continue
                try:
                    url = f"{self.base_url}/compute/instances/{iid}/snapshots"
                    headers = self._get_headers()
                    r = requests.get(url, headers=headers, timeout=15)
                    if r.ok:
                        snap_data = r.json()
                        total = snap_data.get('_pagination', {}).get('totalElements', 0)
                        result[str(iid)] = int(total)
                except Exception:
                    result[str(iid)] = 0
        except Exception:
            pass
        return result

    def test_connection(self):
        """Test API connection by listing instances"""
        try:
            headers = self._get_headers()
            url = f"{self.base_url}/compute/instances"
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            instances = data.get('data', []) if isinstance(data, dict) else []
            instance_count = len(instances) if isinstance(instances, list) else 0
            # Compute max snapshots from plan (min across all instances - conservative)
            plan_max = None
            for inst in instances:
                pid = (inst.get('productId') or inst.get('product_id') or '').strip().upper()
                limit = SNAPSHOT_LIMIT_BY_PRODUCT.get(pid, 3)  # default 3 for unknown products
                plan_max = min(plan_max, limit) if plan_max is not None else limit
            if plan_max is None:
                plan_max = 1  # no instances
            msg = f'Successfully connected to Contabo API. Found {instance_count} instance(s).'
            if instance_count > 0:
                msg += f' Your plan allows up to {plan_max} snapshot(s) per VPS.'
            snapshot_counts = {}
            if instance_count > 0 and instance_count <= 20:
                try:
                    for inst in instances[:10]:
                        iid = inst.get('instanceId') or inst.get('instance_id')
                        if iid is None:
                            continue
                        snap_url = f"{self.base_url}/compute/instances/{iid}/snapshots"
                        r = requests.get(snap_url, headers=headers, timeout=10)
                        if r.ok:
                            total = r.json().get('_pagination', {}).get('totalElements', 0)
                            snapshot_counts[str(iid)] = int(total)
                    if snapshot_counts:
                        parts = [f"Instance {k}: {v} snapshot(s)" for k, v in list(snapshot_counts.items())[:5]]
                        if len(snapshot_counts) > 5:
                            parts.append('...')
                        msg += ' Snapshot usage: ' + '; '.join(parts) + '. Set max per VPS in Auto Backup Settings.'
                except Exception:
                    pass
            
            return {
                'success': True,
                'message': msg,
                'data': data,
                'instance_count': instance_count,
                'snapshot_counts': snapshot_counts,
                'plan_max_snapshots': plan_max
            }
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    err = e.response.json()
                    error_msg = err.get('message') or err.get('error') or err.get('detail') or str(err)
                except Exception:
                    error_msg = (getattr(e.response, 'text', None) or str(e))[:500]
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
        raise Exception("API Client ID and Client Secret are required.")
    if not config.api_key or not config.api_secret:
        raise Exception("API User (email) and API Password are required. Set them in Contabo API Configuration.")
    
    return ContaboAPI(
        client_id=config.api_client_id,
        client_secret=config.api_client_secret,
        api_key=config.api_key,
        api_secret=config.api_secret,
        base_url=config.api_base_url
    )
