# -*- coding: utf-8 -*-
"""
Enhanced Security Implementation Example
This shows how to implement multiple security layers for paid plugins
"""

import hashlib
import socket
import platform
import subprocess
import time
import json
import os
import hmac
import urllib.request
import urllib.error
from functools import wraps

# Configuration
REMOTE_VERIFICATION_URL = 'https://api.newstargeted.com/api/verify-paypal-payment'
PLUGIN_NAME = 'paypalPremiumPlugin'
PLUGIN_VERSION = '1.0.0'
CACHE_FILE = '/tmp/.plugin_license_cache'
CACHE_DURATION = 3600  # 1 hour

# File integrity hashes (generate these when creating plugin)
PLUGIN_FILE_HASHES = {
    'views.py': 'YOUR_SHA256_HASH_HERE',  # Replace with actual hash
    'urls.py': 'YOUR_SHA256_HASH_HERE',
}

def get_server_fingerprint():
    """
    Generate unique server fingerprint
    Ties license to specific server hardware/configuration
    """
    fingerprint_data = []
    
    try:
        # Server hostname
        fingerprint_data.append(socket.gethostname())
        
        # Primary IP
        fingerprint_data.append(socket.gethostbyname(socket.gethostname()))
        
        # System information
        fingerprint_data.append(platform.node())
        fingerprint_data.append(platform.machine())
        fingerprint_data.append(platform.processor())
        
        # MAC address
        import uuid
        fingerprint_data.append(str(uuid.getnode()))
        
        # Disk information (if available)
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True, timeout=2)
            fingerprint_data.append(result.stdout[:100])
        except:
            pass
        
        # Create hash
        fingerprint_string = '|'.join(str(x) for x in fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    except Exception as e:
        # Fallback fingerprint
        return hashlib.sha256(f"{socket.gethostname()}|{platform.node()}".encode()).hexdigest()

def verify_code_integrity():
    """
    Verify plugin files haven't been tampered with
    Returns: (is_valid, error_message)
    """
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    
    for filename, expected_hash in PLUGIN_FILE_HASHES.items():
        if not expected_hash or expected_hash == 'YOUR_SHA256_HASH_HERE':
            continue  # Skip if hash not set
            
        filepath = os.path.join(plugin_dir, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'rb') as f:
                    file_content = f.read()
                    file_hash = hashlib.sha256(file_content).hexdigest()
                    
                    if file_hash != expected_hash:
                        return False, f"File {filename} has been modified (integrity check failed)"
            except Exception as e:
                return False, f"Error checking {filename}: {str(e)}"
    
    return True, None

def get_cached_verification():
    """Get cached verification result"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                cache_time = cache_data.get('timestamp', 0)
                server_fp = cache_data.get('server_fingerprint')
                
                # Verify server fingerprint matches
                current_fp = get_server_fingerprint()
                if server_fp != current_fp:
                    return None  # Server changed, invalidate cache
                
                # Check if cache is still valid
                if time.time() - cache_time < CACHE_DURATION:
                    return cache_data.get('has_access', False)
        except:
            pass
    return None

def cache_verification_result(has_access, server_fp):
    """Cache verification result"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump({
                'has_access': has_access,
                'server_fingerprint': server_fp,
                'timestamp': time.time()
            }, f)
        os.chmod(CACHE_FILE, 0o600)  # Secure permissions (owner read/write only)
    except Exception as e:
        pass  # Silently fail caching

def generate_request_signature(data, secret_key):
    """Generate HMAC signature for secure API communication"""
    message = json.dumps(data, sort_keys=True).encode()
    signature = hmac.new(
        secret_key.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature

def check_remote_payment_secure(user_email, user_ip, domain, request_timestamp=None):
    """
    Enhanced remote payment verification with multiple security layers
    """
    # Layer 1: Code integrity check
    is_valid, integrity_error = verify_code_integrity()
    if not is_valid:
        return {
            'has_access': False,
            'message': 'Plugin integrity check failed',
            'error': integrity_error,
            'security_violation': True
        }
    
    # Layer 2: Check cache
    cached_result = get_cached_verification()
    if cached_result is not None:
        return {'has_access': cached_result}
    
    # Layer 3: Server fingerprinting
    server_fp = get_server_fingerprint()
    
    # Layer 4: Prepare secure request
    request_data = {
        'user_email': user_email,
        'plugin_name': PLUGIN_NAME,
        'plugin_version': PLUGIN_VERSION,
        'server_fingerprint': server_fp,
        'domain': domain,
        'user_ip': user_ip,
        'timestamp': request_timestamp or int(time.time())
    }
    
    # Layer 5: Generate signature (if you have shared secret)
    # Note: Secret should be stored on verification server, not in plugin
    # For now, we'll use a simple approach, but you can enhance this
    
    try:
        # Make request to remote verification server
        req = urllib.request.Request(
            REMOTE_VERIFICATION_URL,
            data=json.dumps(request_data).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'User-Agent': f'CyberPanel-Plugin/{PLUGIN_VERSION}',
                'X-Plugin-Name': PLUGIN_NAME,
                'X-Timestamp': str(request_data['timestamp']),
                # Add signature header if using HMAC
                # 'X-Signature': generate_request_signature(request_data, SECRET_KEY)
            }
        )
        
        # Send request with timeout
        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            
            if response_data.get('success', False):
                has_access = response_data.get('has_access', False)
                
                # Cache result
                cache_verification_result(has_access, server_fp)
                
                return {
                    'has_access': has_access,
                    'paypal_me_url': response_data.get('paypal_me_url', ''),
                    'paypal_payment_link': response_data.get('paypal_payment_link', ''),
                    'message': response_data.get('message', 'Access granted' if has_access else 'Payment required'),
                    'expires_at': response_data.get('expires_at'),
                    'license_type': response_data.get('license_type')
                }
            else:
                return {
                    'has_access': False,
                    'paypal_me_url': response_data.get('paypal_me_url', ''),
                    'paypal_payment_link': response_data.get('paypal_payment_link', ''),
                    'message': response_data.get('message', 'Payment required'),
                    'error': response_data.get('error')
                }
                
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'Unknown error'
        return {
            'has_access': False,
            'message': 'Unable to verify payment. Please try again later.',
            'error': f'HTTP {e.code}: {error_body}'
        }
    except urllib.error.URLError as e:
        return {
            'has_access': False,
            'message': 'Unable to connect to verification server.',
            'error': str(e.reason) if hasattr(e, 'reason') else str(e)
        }
    except Exception as e:
        return {
            'has_access': False,
            'message': 'Verification error occurred.',
            'error': str(e)
        }

def secure_verification_required(view_func):
    """
    Enhanced decorator with multiple security checks
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check 1: Login required
        try:
            userID = request.session['userID']
        except KeyError:
            from loginSystem.views import loadLoginPage
            return redirect(loadLoginPage)
        
        # Check 2: Code integrity
        is_valid, integrity_error = verify_code_integrity()
        if not is_valid:
            # Log security violation
            from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
            logging.writeToFile(f"SECURITY VIOLATION: {integrity_error} - User: {request.session.get('userID')}")
            
            # Show error (don't reveal details)
            from plogical.httpProc import httpProc
            context = {
                'error': 'Plugin integrity check failed. Please reinstall the plugin.',
                'security_violation': True
            }
            proc = httpProc(request, 'paypalPremiumPlugin/subscription_required.html', context, 'admin')
            return proc.render()
        
        # Check 3: Remote verification
        user_email = getattr(request.user, 'email', None) if hasattr(request, 'user') and request.user else None
        if not user_email:
            user_email = request.session.get('email', '') or getattr(request.user, 'username', '')
        
        domain = request.get_host()
        user_ip = request.META.get('REMOTE_ADDR', '')
        
        verification_result = check_remote_payment_secure(
            user_email,
            user_ip,
            domain
        )
        
        if not verification_result.get('has_access', False):
            # Show payment required page
            from plogical.httpProc import httpProc
            context = {
                'plugin_name': 'PayPal Premium Plugin Example',
                'is_paid': True,
                'paypal_me_url': verification_result.get('paypal_me_url', ''),
                'paypal_payment_link': verification_result.get('paypal_payment_link', ''),
                'message': verification_result.get('message', 'PayPal payment required'),
                'error': verification_result.get('error')
            }
            proc = httpProc(request, 'paypalPremiumPlugin/subscription_required.html', context, 'admin')
            return proc.render()
        
        # All checks passed - proceed
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# Usage example:
# @cyberpanel_login_required
# @secure_verification_required
# def settings_view(request):
#     # Your settings code here
#     pass

def generate_file_hash(filepath):
    """Helper function to generate SHA256 hash of a file"""
    with open(filepath, 'rb') as f:
        file_content = f.read()
        return hashlib.sha256(file_content).hexdigest()

# To generate hashes for your files:
# print(f"views.py: {generate_file_hash('/path/to/views.py')}")
# print(f"urls.py: {generate_file_hash('/path/to/urls.py')}")
