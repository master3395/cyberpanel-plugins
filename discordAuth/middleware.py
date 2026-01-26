# -*- coding: utf-8 -*-
"""
Discord Authentication Middleware
Automatically injects Discord login button script into login page
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from .utils.config import is_enabled
import re


class DiscordAuthMiddleware(MiddlewareMixin):
    """
    Middleware to inject Discord login button into login page
    """
    
    def process_response(self, request, response):
        # Only process HTML responses
        if not isinstance(response, HttpResponse):
            return response
        
        content_type = response.get('Content-Type', '')
        if 'text/html' not in content_type:
            return response
        
        # Only process login page
        if request.path != '/' and 'login' not in request.path.lower():
            return response
        
        # Check if Discord auth is enabled
        if not is_enabled():
            return response
        
        # Get response content
        try:
            content = response.content.decode('utf-8')
        except (UnicodeDecodeError, AttributeError):
            return response
        
        # Check if script is already injected
        if 'discord-login-inject.js' in content or 'discord-login-btn' in content:
            return response
        
        # Find where to inject (before closing body tag or after login form)
        injection_point = None
        
        # Try to find login form submit button
        submit_button_pattern = r'(<button[^>]*type=["\']submit["\'][^>]*>.*?</button>)'
        match = re.search(submit_button_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if match:
            # Inject after submit button
            injection_point = match.end()
        else:
            # Fallback: inject before closing body tag
            body_close = content.rfind('</body>')
            if body_close > 0:
                injection_point = body_close
        
        if injection_point:
            # Create injection HTML
            injection_html = '''
<!-- Discord Authentication Plugin -->
<link rel="stylesheet" href="/static/discordAuth/css/discord-auth.css">
<script>
(function() {
    'use strict';
    
    // Check if Discord auth is enabled
    fetch('/plugins/discordAuth/check/', {
        method: 'GET',
        credentials: 'same-origin'
    })
    .then(response => response.json())
    .then(data => {
        if (!data.enabled) {
            return; // Discord auth not enabled
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
            
            # Inject the HTML
            new_content = content[:injection_point] + injection_html + content[injection_point:]
            response.content = new_content.encode('utf-8')
            response['Content-Length'] = str(len(response.content))
        
        return response
