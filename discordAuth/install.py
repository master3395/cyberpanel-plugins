# -*- coding: utf-8 -*-
"""
Discord Auth Plugin Installation Script
Automatically modifies login template to include Discord login button
"""

import os
import re
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging


def install_discord_auth_integration():
    """
    Install Discord auth integration into login template
    Adds script tag to inject Discord login button
    """
    login_template = '/usr/local/CyberCP/loginSystem/templates/loginSystem/login.html'
    
    if not os.path.exists(login_template):
        logging.writeToFile(f"Login template not found: {login_template}")
        return False
    
    try:
        # Read login template
        with open(login_template, 'r') as f:
            content = f.read()
        
        # Check if already installed
        if 'discord-login-inject.js' in content or 'discordAuth' in content:
            logging.writeToFile("Discord auth already integrated into login template")
            return True
        
        # Find insertion point (before closing body tag or after webauthn script)
        insertion_point = None
        
        # Try to find webauthn script section
        webauthn_pattern = r'(<!-- Optional: WebAuthn script.*?</script>\s*</script>)'
        match = re.search(webauthn_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if match:
            # Insert after webauthn script
            insertion_point = match.end()
        else:
            # Fallback: find closing body tag
            body_close = content.rfind('</body>')
            if body_close > 0:
                insertion_point = body_close
        
        if not insertion_point:
            logging.writeToFile("Could not find insertion point in login template")
            return False
        
        # Create injection code
        injection_code = '''
<!-- Discord Authentication Plugin -->
<script>
(function() {
    'use strict';
    
    // Check if Discord auth is enabled and inject button
    fetch('/plugins/discordAuth/check/', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.enabled) {
            return; // Discord auth not enabled
        }
        
        // Load CSS
        if (!document.getElementById('discord-auth-css')) {
            const link = document.createElement('link');
            link.id = 'discord-auth-css';
            link.rel = 'stylesheet';
            link.href = '/static/discordAuth/css/discord-auth.css';
            document.head.appendChild(link);
        }
        
        // Wait for login form to be ready
        const checkForm = setInterval(function() {
            const loginForm = document.getElementById('loginForm');
            const submitButton = document.querySelector('#loginForm button[type="submit"]');
            
            if (loginForm && submitButton) {
                clearInterval(checkForm);
                
                // Check if already injected
                if (document.querySelector('.discord-login-container')) {
                    return;
                }
                
                // Create Discord button container
                const discordContainer = document.createElement('div');
                discordContainer.className = 'discord-login-container';
                discordContainer.style.cssText = 'text-align: center; margin: 20px 0;';
                
                // Create divider
                const divider = document.createElement('div');
                divider.className = 'discord-login-divider';
                divider.textContent = 'OR';
                
                // Create Discord button
                const discordButton = document.createElement('a');
                discordButton.href = '/plugins/discordAuth/login/';
                discordButton.className = 'discord-login-btn';
                discordButton.innerHTML = '<i class="fab fa-discord"></i> Login with Discord';
                
                // Insert after submit button
                submitButton.parentNode.insertBefore(divider, submitButton.nextSibling);
                submitButton.parentNode.insertBefore(discordContainer, divider.nextSibling);
                discordContainer.appendChild(discordButton);
            }
        }, 100);
        
        // Timeout after 5 seconds
        setTimeout(function() {
            clearInterval(checkForm);
        }, 5000);
    })
    .catch(function() {
        // Silently fail if check endpoint is not available
    });
})();
</script>
<!-- End Discord Authentication Plugin -->
'''
        
        # Insert the code
        new_content = content[:insertion_point] + injection_code + content[insertion_point:]
        
        # Write back to file
        with open(login_template, 'w') as f:
            f.write(new_content)
        
        logging.writeToFile("Discord auth integration installed successfully in login template")
        return True
        
    except Exception as e:
        logging.writeToFile(f"Error installing Discord auth integration: {str(e)}")
        return False


def uninstall_discord_auth_integration():
    """
    Remove Discord auth integration from login template
    """
    login_template = '/usr/local/CyberCP/loginSystem/templates/loginSystem/login.html'
    
    if not os.path.exists(login_template):
        return True
    
    try:
        with open(login_template, 'r') as f:
            content = f.read()
        
        # Remove Discord auth injection code
        pattern = r'<!-- Discord Authentication Plugin -->.*?<!-- End Discord Authentication Plugin -->'
        new_content = re.sub(pattern, '', content, flags=re.DOTALL)
        
        if new_content != content:
            with open(login_template, 'w') as f:
                f.write(new_content)
            logging.writeToFile("Discord auth integration removed from login template")
        
        return True
        
    except Exception as e:
        logging.writeToFile(f"Error removing Discord auth integration: {str(e)}")
        return False
