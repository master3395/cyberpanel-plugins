<?php
/**
 * Enhanced Security Implementation Example
 * 
 * This document shows how to implement multiple security layers for paid plugins.
 * Contains Python code examples that can be adapted for your plugins.
 * 
 * @author master3395
 * @version 1.0.0
 * @date 2026-01-25
 */

// Prevent direct access if needed
if (!defined('APP_INIT')) {
    define('APP_INIT', true);
}

// Set content type for HTML output
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Security Implementation Example - CyberPanel Plugins</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f7fa;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #2d3748;
            font-size: 2.5em;
            margin-bottom: 10px;
            border-bottom: 3px solid #4299e1;
            padding-bottom: 15px;
        }
        
        h2 {
            color: #2d3748;
            font-size: 1.8em;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-left: 15px;
            border-left: 4px solid #4299e1;
        }
        
        h3 {
            color: #4a5568;
            font-size: 1.4em;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        
        h4 {
            color: #718096;
            font-size: 1.2em;
            margin-top: 25px;
            margin-bottom: 12px;
        }
        
        p {
            margin-bottom: 15px;
            color: #4a5568;
        }
        
        ul, ol {
            margin-left: 30px;
            margin-bottom: 20px;
        }
        
        li {
            margin-bottom: 10px;
            color: #4a5568;
        }
        
        .code-block {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 25px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.6;
            border: 1px solid #3c3c3c;
            position: relative;
        }
        
        .code-block::before {
            content: 'Python';
            position: absolute;
            top: 10px;
            right: 15px;
            background: #4299e1;
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
        }
        
        .code-block code {
            color: #d4d4d4;
            display: block;
            white-space: pre;
        }
        
        /* Python syntax highlighting */
        .code-block .keyword { color: #569cd6; }
        .code-block .string { color: #ce9178; }
        .code-block .comment { color: #6a9955; }
        .code-block .function { color: #dcdcaa; }
        .code-block .number { color: #b5cea8; }
        .code-block .operator { color: #d4d4d4; }
        
        .function-block {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }
        
        .function-block h4 {
            color: #2d3748;
            margin-top: 0;
            font-family: 'Consolas', monospace;
        }
        
        .function-block .description {
            color: #4a5568;
            margin-bottom: 15px;
            font-style: italic;
        }
        
        .note {
            background: #ebf8ff;
            border-left: 4px solid #4299e1;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .warning {
            background: #fffaf0;
            border-left: 4px solid #ed8936;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .success {
            background: #f0fff4;
            border-left: 4px solid #48bb78;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        
        .info-box {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .info-box h4 {
            margin-top: 0;
            color: #2d3748;
        }
        
        .toc {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
        }
        
        .toc h3 {
            margin-top: 0;
        }
        
        .toc ul {
            list-style: none;
            margin-left: 0;
        }
        
        .toc a {
            color: #4299e1;
            text-decoration: none;
        }
        
        .toc a:hover {
            text-decoration: underline;
        }
        
        .config-section {
            background: #fffaf0;
            border: 1px solid #fbd38d;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }
        
        .config-section h4 {
            color: #7c2d12;
            margin-top: 0;
        }
        
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            text-align: center;
            color: #718096;
            font-size: 0.9em;
        }
        
        .copy-btn {
            background: #4299e1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85em;
            margin-top: 10px;
        }
        
        .copy-btn:hover {
            background: #3182ce;
        }
    </style>
    <script>
        function copyCode(elementId) {
            const codeBlock = document.getElementById(elementId);
            const text = codeBlock.textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('Code copied to clipboard!');
            });
        }
    </script>
</head>
<body>
    <div class="container">
        <h1>🔐 Security Implementation Example</h1>
        <p style="font-size: 1.1em; color: #718096; margin-bottom: 30px;">
            Python code examples showing how to implement multiple security layers for paid plugins.
        </p>
        
        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#overview">Overview</a></li>
                <li><a href="#configuration">Configuration</a></li>
                <li><a href="#server-fingerprint">Server Fingerprinting</a></li>
                <li><a href="#code-integrity">Code Integrity Verification</a></li>
                <li><a href="#caching">Caching & Re-Validation</a></li>
                <li><a href="#secure-api">Secure API Communication</a></li>
                <li><a href="#verification">Enhanced Verification</a></li>
                <li><a href="#decorator">Secure Decorator</a></li>
                <li><a href="#utilities">Utility Functions</a></li>
            </ul>
        </div>
        
        <h2 id="overview">Overview</h2>
        <p>
            This document contains Python code examples for implementing enhanced security in your paid plugins.
            Each function demonstrates a specific security layer that can be integrated into your plugin's verification system.
        </p>
        
        <div class="note">
            <strong>💡 Note:</strong> These are Python examples. Adapt the concepts to your plugin's language and framework.
            The security principles apply regardless of the implementation language.
        </div>
        
        <h2 id="configuration">Configuration</h2>
        
        <div class="config-section">
            <h4>Configuration Variables</h4>
            <p>These constants should be defined at the top of your plugin's views.py file:</p>
        </div>
        
        <div class="code-block" id="config-code">
<code># Configuration
REMOTE_VERIFICATION_URL = 'https://api.newstargeted.com/api/verify-paypal-payment'
PLUGIN_NAME = 'paypalPremiumPlugin'
PLUGIN_VERSION = '1.0.0'
CACHE_FILE = '/tmp/.plugin_license_cache'
CACHE_DURATION = 3600  # 1 hour

# File integrity hashes (generate these when creating plugin)
PLUGIN_FILE_HASHES = {
    'views.py': 'YOUR_SHA256_HASH_HERE',  # Replace with actual hash
    'urls.py': 'YOUR_SHA256_HASH_HERE',
}</code>
        </div>
        <button class="copy-btn" onclick="copyCode('config-code')">Copy Code</button>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> Replace <code>YOUR_SHA256_HASH_HERE</code> with actual SHA256 hashes of your plugin files.
            Generate these hashes when creating the plugin, not after distribution.
        </div>
        
        <h2 id="server-fingerprint">Server Fingerprinting</h2>
        
        <div class="function-block">
            <h4>get_server_fingerprint()</h4>
            <div class="description">
                Generate unique server fingerprint that ties license to specific server hardware/configuration.
            </div>
        </div>
        
        <div class="code-block" id="fingerprint-code">
<code>import hashlib
import socket
import platform
import subprocess
import uuid

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
            result = subprocess.run(['df', '-h', '/'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=2)
            fingerprint_data.append(result.stdout[:100])
        except:
            pass
        
        # Create hash
        fingerprint_string = '|'.join(str(x) for x in fingerprint_data)
        return hashlib.sha256(fingerprint_string.encode()).hexdigest()
    except Exception as e:
        # Fallback fingerprint
        return hashlib.sha256(
            f"{socket.gethostname()}|{platform.node()}".encode()
        ).hexdigest()</code>
        </div>
        <button class="copy-btn" onclick="copyCode('fingerprint-code')">Copy Code</button>
        
        <div class="info-box">
            <h4>How It Works</h4>
            <ul>
                <li>Collects unique server identifiers (hostname, IP, MAC, disk info)</li>
                <li>Combines them into a single string</li>
                <li>Creates SHA256 hash for consistent, unique fingerprint</li>
                <li>Includes fallback for systems where some info isn't available</li>
            </ul>
        </div>
        
        <h2 id="code-integrity">Code Integrity Verification</h2>
        
        <div class="function-block">
            <h4>verify_code_integrity()</h4>
            <div class="description">
                Verify plugin files haven't been tampered with by checking SHA256 hashes.
            </div>
        </div>
        
        <div class="code-block" id="integrity-code">
<code>import hashlib
import os

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
    
    return True, None</code>
        </div>
        <button class="copy-btn" onclick="copyCode('integrity-code')">Copy Code</button>
        
        <div class="warning">
            <strong>⚠️ Security Note:</strong> If integrity check fails, log the violation and block access.
            Don't reveal too much detail to potential attackers.
        </div>
        
        <h2 id="caching">Caching & Re-Validation</h2>
        
        <div class="function-block">
            <h4>get_cached_verification() & cache_verification_result()</h4>
            <div class="description">
                Cache verification results with server fingerprint validation for time-based re-validation.
            </div>
        </div>
        
        <div class="code-block" id="cache-code">
<code>import json
import time
import os

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
        pass  # Silently fail caching</code>
        </div>
        <button class="copy-btn" onclick="copyCode('cache-code')">Copy Code</button>
        
        <div class="info-box">
            <h4>Benefits</h4>
            <ul>
                <li>Reduces API calls (improves performance)</li>
                <li>Allows remote license revocation (cache expires)</li>
                <li>Validates server fingerprint (prevents cache reuse on different server)</li>
                <li>Secure file permissions (only owner can read/write)</li>
            </ul>
        </div>
        
        <h2 id="secure-api">Secure API Communication</h2>
        
        <div class="function-block">
            <h4>generate_request_signature()</h4>
            <div class="description">
                Generate HMAC signature for secure API communication to prevent request tampering.
            </div>
        </div>
        
        <div class="code-block" id="hmac-code">
<code>import hmac
import hashlib
import json

def generate_request_signature(data, secret_key):
    """Generate HMAC signature for secure API communication"""
    message = json.dumps(data, sort_keys=True).encode()
    signature = hmac.new(
        secret_key.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    return signature</code>
        </div>
        <button class="copy-btn" onclick="copyCode('hmac-code')">Copy Code</button>
        
        <div class="warning">
            <strong>⚠️ Important:</strong> The secret key should be stored on your verification server, not in the plugin.
            The plugin can request a temporary token or use a public/private key pair.
        </div>
        
        <h2 id="verification">Enhanced Verification Function</h2>
        
        <div class="function-block">
            <h4>check_remote_payment_secure()</h4>
            <div class="description">
                Complete verification function that combines all security layers: integrity checks, 
                server fingerprinting, caching, and secure API communication.
            </div>
        </div>
        
        <div class="code-block" id="verification-code">
<code>import urllib.request
import urllib.error
import json
import time

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
                    'message': response_data.get('message', 
                        'Access granted' if has_access else 'Payment required'),
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
        }</code>
        </div>
        <button class="copy-btn" onclick="copyCode('verification-code')">Copy Code</button>
        
        <h2 id="decorator">Secure Decorator</h2>
        
        <div class="function-block">
            <h4>secure_verification_required()</h4>
            <div class="description">
                Enhanced decorator that combines all security checks: login, code integrity, and remote verification.
            </div>
        </div>
        
        <div class="code-block" id="decorator-code">
<code>from functools import wraps
from django.shortcuts import redirect
from plogical.httpProc import httpProc
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

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
            logging.writeToFile(
                f"SECURITY VIOLATION: {integrity_error} - "
                f"User: {request.session.get('userID')}"
            )
            
            # Show error (don't reveal details)
            context = {
                'error': 'Plugin integrity check failed. Please reinstall the plugin.',
                'security_violation': True
            }
            proc = httpProc(request, 
                          'paypalPremiumPlugin/subscription_required.html', 
                          context, 
                          'admin')
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
            context = {
                'plugin_name': 'PayPal Premium Plugin Example',
                'is_paid': True,
                'paypal_me_url': verification_result.get('paypal_me_url', ''),
                'paypal_payment_link': verification_result.get('paypal_payment_link', ''),
                'message': verification_result.get('message', 'PayPal payment required'),
                'error': verification_result.get('error')
            }
            proc = httpProc(request, 
                          'paypalPremiumPlugin/subscription_required.html', 
                          context, 
                          'admin')
            return proc.render()
        
        # All checks passed - proceed
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view

# Usage example:
# @cyberpanel_login_required
# @secure_verification_required
# def settings_view(request):
#     # Your settings code here
#     pass</code>
        </div>
        <button class="copy-btn" onclick="copyCode('decorator-code')">Copy Code</button>
        
        <h2 id="utilities">Utility Functions</h2>
        
        <div class="function-block">
            <h4>generate_file_hash()</h4>
            <div class="description">
                Helper function to generate SHA256 hash of a file. Use this when creating your plugin to generate the hashes for PLUGIN_FILE_HASHES.
            </div>
        </div>
        
        <div class="code-block" id="utility-code">
<code>import hashlib

def generate_file_hash(filepath):
    """Helper function to generate SHA256 hash of a file"""
    with open(filepath, 'rb') as f:
        file_content = f.read()
        return hashlib.sha256(file_content).hexdigest()

# To generate hashes for your files:
# print(f"views.py: {generate_file_hash('/path/to/views.py')}")
# print(f"urls.py: {generate_file_hash('/path/to/urls.py')}")</code>
        </div>
        <button class="copy-btn" onclick="copyCode('utility-code')">Copy Code</button>
        
        <div class="success">
            <h4>✅ Implementation Steps</h4>
            <ol>
                <li><strong>Generate file hashes:</strong> Use <code>generate_file_hash()</code> to create hashes for your plugin files</li>
                <li><strong>Add configuration:</strong> Copy the configuration section to your plugin's views.py</li>
                <li><strong>Import functions:</strong> Add all security functions to your views.py</li>
                <li><strong>Update decorator:</strong> Replace <code>@remote_verification_required</code> with <code>@secure_verification_required</code></li>
                <li><strong>Test thoroughly:</strong> Verify all security layers work correctly</li>
            </ol>
        </div>
        
        <div class="note">
            <strong>📚 Related Documentation:</strong><br>
            - See <code>PAID-PLUGIN-SECURITY.php</code> for detailed security guide<br>
            - Contact master3395 for implementation help
        </div>
        
        <div class="footer">
            <p><strong>Security Implementation Example</strong></p>
            <p>Version 1.0.0 | Last Updated: <?php echo date('Y-m-d'); ?></p>
            <p>© <?php echo date('Y'); ?> master3395 - CyberPanel Plugins</p>
        </div>
    </div>
</body>
</html>
