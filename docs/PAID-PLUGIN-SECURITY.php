<?php
/**
 * Paid Plugin Security Guide
 * 
 * This document outlines multiple security layers to protect your paid plugins
 * from unauthorized copying, tampering, and bypassing payment verification.
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
    <title>Paid Plugin Security Guide - CyberPanel Plugins</title>
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
        
        .security-layer {
            background: #f7fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }
        
        .security-layer h3 {
            color: #2d3748;
            margin-top: 0;
        }
        
        .priority {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
            margin-left: 10px;
        }
        
        .priority-high {
            background: #fed7d7;
            color: #c53030;
        }
        
        .priority-medium {
            background: #feebc8;
            color: #c05621;
        }
        
        .priority-low {
            background: #c6f6d5;
            color: #22543d;
        }
        
        .status-box {
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid;
        }
        
        .status-implemented {
            background: #f0fff4;
            border-color: #48bb78;
        }
        
        .status-vulnerable {
            background: #fffaf0;
            border-color: #ed8936;
        }
        
        .status-implemented h4 {
            color: #22543d;
            margin-top: 0;
        }
        
        .status-vulnerable h4 {
            color: #7c2d12;
            margin-top: 0;
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
        
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }
        
        th {
            background: #edf2f7;
            font-weight: 600;
            color: #2d3748;
        }
        
        tr:hover {
            background: #f7fafc;
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
        
        code {
            background: #f7fafc;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 0.9em;
            color: #e53e3e;
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
        <h1>🔒 Paid Plugin Security Guide</h1>
        <p style="font-size: 1.1em; color: #718096; margin-bottom: 30px;">
            Comprehensive security strategies to protect your paid plugins from unauthorized copying, tampering, and payment bypass.
        </p>
        
        <div class="toc">
            <h3>📑 Table of Contents</h3>
            <ul>
                <li><a href="#overview">Overview</a></li>
                <li><a href="#current-status">Current Security Status</a></li>
                <li><a href="#security-layers">Security Layers</a></li>
                <li><a href="#implementation">Implementation Priority</a></li>
                <li><a href="#best-practices">Best Practices</a></li>
                <li><a href="#testing">Testing Your Security</a></li>
            </ul>
        </div>
        
        <h2 id="overview">Overview</h2>
        <p>
            This guide outlines multiple security layers to protect your paid plugins from unauthorized copying, 
            tampering, and bypassing payment verification. Each layer adds additional protection, making it 
            progressively harder for attackers to bypass your security measures.
        </p>
        
        <div class="note">
            <strong>💡 Note:</strong> No security is perfect. The goal is to make it difficult enough that 
            most attackers will give up, while legitimate users can still use your plugins easily.
        </div>
        
        <h2 id="current-status">Current Security Status</h2>
        
        <div class="status-box status-implemented">
            <h4>✅ Already Implemented</h4>
            <ul>
                <li>Remote verification server (no secrets in plugin code)</li>
                <li>Server-side payment validation</li>
                <li>User email and IP tracking</li>
            </ul>
        </div>
        
        <div class="status-box status-vulnerable">
            <h4>⚠️ Current Vulnerabilities</h4>
            <ul>
                <li>Verification can be bypassed by editing <code>views.py</code></li>
                <li>No server fingerprinting (can copy to any server)</li>
                <li>No code integrity checks</li>
                <li>No time-based re-validation</li>
                <li>Verification URL can be changed</li>
            </ul>
        </div>
        
        <h2 id="security-layers">Security Layers</h2>
        
        <div class="security-layer">
            <h3>Layer 1: Server Fingerprinting <span class="priority priority-high">HIGH PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Tie the license to a specific server/domain</p>
            <p><strong>How it works:</strong> Generate a unique fingerprint based on server hardware, hostname, MAC address, and system information. This fingerprint is included in every verification request.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>License tied to specific server</li>
                    <li>Prevents copying plugin to another server</li>
                    <li>Can detect license sharing</li>
                </ul>
            </div>
            
            <div class="code-block" id="fingerprint-code">
<code>def get_server_fingerprint():
    fingerprint_data = []
    fingerprint_data.append(socket.gethostname())
    fingerprint_data.append(socket.gethostbyname(socket.gethostname()))
    fingerprint_data.append(platform.node())
    fingerprint_data.append(platform.machine())
    # Create hash
    fingerprint_string = '|'.join(str(x) for x in fingerprint_data)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()</code>
            </div>
            <button class="copy-btn" onclick="copyCode('fingerprint-code')">Copy Code</button>
        </div>
        
        <div class="security-layer">
            <h3>Layer 2: Code Integrity Verification <span class="priority priority-high">HIGH PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Detect if plugin files have been tampered with</p>
            <p><strong>How it works:</strong> Store SHA256 hashes of critical files when creating the plugin. At runtime, verify these hashes match. If any file has been modified, block access.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Detects file tampering</li>
                    <li>Prevents bypassing verification by editing code</li>
                    <li>Can trigger security alerts</li>
                </ul>
            </div>
            
            <div class="code-block" id="integrity-code">
<code>PLUGIN_FILE_HASHES = {
    'views.py': 'abc123...',  # SHA256 hash
    'urls.py': 'def456...',
}

def verify_code_integrity():
    for filename, expected_hash in PLUGIN_FILE_HASHES.items():
        file_hash = hashlib.sha256(file_content).hexdigest()
        if file_hash != expected_hash:
            return False, "File modified"
    return True, None</code>
            </div>
            <button class="copy-btn" onclick="copyCode('integrity-code')">Copy Code</button>
        </div>
        
        <div class="security-layer">
            <h3>Layer 3: Domain/Server Binding <span class="priority priority-high">HIGH PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Tie license to specific domain or server</p>
            <p><strong>How it works:</strong> Include the current domain in verification requests. Your server checks if the domain matches the licensed domain.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Prevents using license on unauthorized domains</li>
                    <li>Can support multiple domains per license (if configured)</li>
                    <li>Easy to detect domain changes</li>
                </ul>
            </div>
        </div>
        
        <div class="security-layer">
            <h3>Layer 4: Time-Based Re-Validation <span class="priority priority-medium">MEDIUM PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Require periodic re-verification</p>
            <p><strong>How it works:</strong> Cache verification results for a short period (e.g., 1 hour), then require re-verification. This allows you to revoke licenses remotely.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Periodic re-validation</li>
                    <li>Can revoke licenses remotely</li>
                    <li>Reduces API calls (caching)</li>
                </ul>
            </div>
        </div>
        
        <div class="security-layer">
            <h3>Layer 5: Multiple Verification Points <span class="priority priority-medium">MEDIUM PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Verify at multiple points, not just once</p>
            <p><strong>How it works:</strong> Check verification at plugin load, settings access, API calls, form submissions, and critical function execution.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Harder to bypass all checks</li>
                    <li>Multiple failure points</li>
                    <li>Can log all verification attempts</li>
                </ul>
            </div>
        </div>
        
        <div class="security-layer">
            <h3>Layer 6: Secure Remote API <span class="priority priority-medium">MEDIUM PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Make remote verification server secure</p>
            <p><strong>How it works:</strong> Use HMAC signatures for API requests, include timestamps to prevent replay attacks, implement rate limiting.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Prevents request tampering</li>
                    <li>Secure API communication</li>
                    <li>Can implement rate limiting</li>
                </ul>
            </div>
        </div>
        
        <div class="security-layer">
            <h3>Layer 7: License Database & Tracking <span class="priority priority-medium">MEDIUM PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Track all license usage</p>
            <p><strong>How it works:</strong> Store all verification attempts in a database. Track server fingerprints, domains, IP addresses, and verification results.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Track all license usage</li>
                    <li>Detect license sharing</li>
                    <li>Audit trail</li>
                    <li>Can revoke licenses</li>
                </ul>
            </div>
        </div>
        
        <div class="security-layer">
            <h3>Layer 8: Anomaly Detection <span class="priority priority-low">LOW PRIORITY</span></h3>
            <p><strong>Purpose:</strong> Detect suspicious behavior</p>
            <p><strong>How it works:</strong> Monitor for patterns like excessive verification attempts, multiple servers with same license, rapid domain changes, suspicious IP changes.</p>
            
            <div class="info-box">
                <h4>Benefits</h4>
                <ul>
                    <li>Automatic threat detection</li>
                    <li>Can block suspicious activity</li>
                    <li>Provides security insights</li>
                </ul>
            </div>
        </div>
        
        <h2 id="implementation">Implementation Priority</h2>
        
        <table>
            <thead>
                <tr>
                    <th>Priority</th>
                    <th>Layer</th>
                    <th>Impact</th>
                    <th>Effort</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><span class="priority priority-high">HIGH</span></td>
                    <td>Server Fingerprinting</td>
                    <td>Very High</td>
                    <td>Low</td>
                </tr>
                <tr>
                    <td><span class="priority priority-high">HIGH</span></td>
                    <td>Code Integrity Checks</td>
                    <td>Very High</td>
                    <td>Medium</td>
                </tr>
                <tr>
                    <td><span class="priority priority-high">HIGH</span></td>
                    <td>Domain Binding</td>
                    <td>High</td>
                    <td>Low</td>
                </tr>
                <tr>
                    <td><span class="priority priority-medium">MEDIUM</span></td>
                    <td>Time-Based Re-Validation</td>
                    <td>High</td>
                    <td>Medium</td>
                </tr>
                <tr>
                    <td><span class="priority priority-medium">MEDIUM</span></td>
                    <td>Multiple Verification Points</td>
                    <td>Medium</td>
                    <td>Medium</td>
                </tr>
                <tr>
                    <td><span class="priority priority-medium">MEDIUM</span></td>
                    <td>Secure API with HMAC</td>
                    <td>High</td>
                    <td>High</td>
                </tr>
                <tr>
                    <td><span class="priority priority-medium">MEDIUM</span></td>
                    <td>License Database</td>
                    <td>Medium</td>
                    <td>High</td>
                </tr>
                <tr>
                    <td><span class="priority priority-low">LOW</span></td>
                    <td>Anomaly Detection</td>
                    <td>Low</td>
                    <td>High</td>
                </tr>
            </tbody>
        </table>
        
        <h3>Recommended Implementation Order</h3>
        <ol>
            <li><strong>Immediate (Week 1):</strong> Server fingerprinting, Code integrity checks, Domain binding</li>
            <li><strong>Short-term (Month 1):</strong> Time-based re-validation, Multiple verification points, Secure API</li>
            <li><strong>Long-term (Quarter 1):</strong> License database, Anomaly detection</li>
        </ol>
        
        <h2 id="best-practices">Best Practices</h2>
        
        <div class="success">
            <h4>✅ Do's</h4>
            <ul>
                <li>Always verify on YOUR server (never trust client)</li>
                <li>Use HTTPS for all API calls</li>
                <li>Log all verification attempts</li>
                <li>Monitor for suspicious patterns</li>
                <li>Regularly update security measures</li>
                <li>Balance security with user experience</li>
                <li>Include license terms in plugin</li>
                <li>Use EULA (End User License Agreement)</li>
            </ul>
        </div>
        
        <div class="warning">
            <h4>⚠️ Don'ts</h4>
            <ul>
                <li>Don't store secrets in plugin code</li>
                <li>Don't trust client-side verification</li>
                <li>Don't make security too complex (hurts UX)</li>
                <li>Don't ignore security logs</li>
                <li>Don't assume one layer is enough</li>
            </ul>
        </div>
        
        <h2 id="testing">Testing Your Security</h2>
        
        <div class="info-box">
            <h4>Security Testing Checklist</h4>
            <ol>
                <li><strong>Try to bypass verification:</strong> Edit <code>views.py</code> to skip verification</li>
                <li><strong>Copy plugin to another server:</strong> See if server fingerprinting catches it</li>
                <li><strong>Modify code:</strong> Change verification logic and see if integrity checks catch it</li>
                <li><strong>Monitor logs:</strong> Check verification logs for suspicious patterns</li>
                <li><strong>Regular audits:</strong> Review security measures quarterly</li>
            </ol>
        </div>
        
        <div class="note">
            <strong>📚 Additional Resources:</strong><br>
            - See <code>security-implementation-example.php</code> for complete code examples<br>
            - Contact master3395 for security questions or implementation help
        </div>
        
        <div class="footer">
            <p><strong>Paid Plugin Security Guide</strong></p>
            <p>Version 1.0.0 | Last Updated: <?php echo date('Y-m-d'); ?></p>
            <p>© <?php echo date('Y'); ?> master3395 - CyberPanel Plugins</p>
        </div>
    </div>
</body>
</html>
