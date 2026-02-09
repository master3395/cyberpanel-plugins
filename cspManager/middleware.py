# -*- coding: utf-8 -*-
"""
CSP Manager Middleware
Sets comprehensive Content Security Policy headers for CyberPanel
Supports Google Analytics, Tag Manager, Discord Auth, and all required resources
Makes CSP optional for plugin routes (plugins can opt-out)
Handles Cloudflare proxy by setting multiple CSP headers
Respects user settings from CSPConfig model
"""

from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponse


class CSPManagerMiddleware(MiddlewareMixin):
    """
    Middleware to set comprehensive CSP headers
    Overrides core CyberPanel CSP to support Google Analytics, Tag Manager, and Discord Auth
    Makes CSP optional for plugin routes - plugins can opt-out by setting X-CSP-Opt-Out header
    Handles Cloudflare by setting both Content-Security-Policy and X-Content-Security-Policy headers
    """
    
    def process_response(self, request, response):
        """Set CSP headers on all responses, but allow plugins to opt-out"""
        if isinstance(response, HttpResponse):
            # Get CSP configuration
            try:
                from .models import CSPConfig
                config = CSPConfig.get_config()
                
                # Check if CSP is globally enabled
                if not config.csp_enabled:
                    # CSP is disabled globally - remove any existing CSP headers
                    if 'Content-Security-Policy' in response:
                        del response['Content-Security-Policy']
                    if 'X-Content-Security-Policy' in response:
                        del response['X-Content-Security-Policy']
                    return response
            except Exception:
                # If config doesn't exist or error, use defaults
                config = None
            
            # Check if plugin wants to opt-out of CSP
            # Plugins can set X-CSP-Opt-Out: true in their response to bypass CSP
            opt_out = response.get('X-CSP-Opt-Out', '').lower() == 'true'
            
            # Also check if this is a plugin route and if plugin has opted out via request header
            is_plugin_route = request.path.startswith('/plugins/')
            
            # Check plugin-specific settings
            if config and is_plugin_route:
                # Extract plugin name from path (e.g., /plugins/cspManager/settings/ -> cspManager)
                plugin_name = request.path.split('/')[2] if len(request.path.split('/')) > 2 else None
                if plugin_name:
                    plugin_setting = config.get_plugin_setting(plugin_name, {})
                    if isinstance(plugin_setting, dict) and not plugin_setting.get('enabled', True):
                        # Plugin has CSP disabled - remove CSP headers
                        if 'Content-Security-Policy' in response:
                            del response['Content-Security-Policy']
                        if 'X-Content-Security-Policy' in response:
                            del response['X-Content-Security-Policy']
                        return response
            
            # Check if CSP should be applied to plugins or core
            if config:
                if is_plugin_route and not config.apply_to_plugins:
                    # Don't apply CSP to plugins
                    if 'Content-Security-Policy' in response:
                        del response['Content-Security-Policy']
                    if 'X-Content-Security-Policy' in response:
                        del response['X-Content-Security-Policy']
                    return response
                
                if not is_plugin_route and not config.apply_to_core:
                    # Don't apply CSP to core pages
                    if 'Content-Security-Policy' in response:
                        del response['Content-Security-Policy']
                    if 'X-Content-Security-Policy' in response:
                        del response['X-Content-Security-Policy']
                    return response
            
            # Check if request is coming through Cloudflare
            is_cloudflare = any([
                request.META.get('HTTP_CF_RAY'),
                request.META.get('HTTP_CF_CONNECTING_IP'),
                'cloudflare' in request.META.get('HTTP_VIA', '').lower(),
            ])
            
            # For plugin routes, use more permissive CSP or allow opt-out
            if is_plugin_route and opt_out:
                # Plugin has opted out - remove CSP entirely or use very permissive CSP
                # Remove CSP header to allow plugin full control
                if 'Content-Security-Policy' in response:
                    del response['Content-Security-Policy']
                if 'X-Content-Security-Policy' in response:
                    del response['X-Content-Security-Policy']
            else:
                # Build comprehensive CSP that supports all required resources
                # For plugin routes, use more permissive CSP
                if is_plugin_route:
                    # More permissive CSP for plugins (allows more flexibility)
                    if config and config.permissive_plugin_csp:
                        csp_parts = [
                            "default-src 'self'",
                            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https: http: data: blob:",
                            "style-src 'self' 'unsafe-inline' https: http: data:",
                            "img-src 'self' data: https: http: blob:",
                            "font-src 'self' 'unsafe-inline' https: http: data:",
                            "connect-src 'self' https: http: wss: ws: data: blob:",
                            "frame-src 'self' https: http: data:",
                            "frame-ancestors 'none'",
                            "base-uri 'self'",
                            "form-action 'self'"
                        ]
                    else:
                        # Use standard CSP for plugins (respects settings)
                        csp_parts = self._build_csp_parts(config, is_plugin_route)
                else:
                    # Standard CSP for core CyberPanel pages (login, dashboard, etc.)
                    csp_parts = self._build_csp_parts(config, is_plugin_route)
                
                csp_value = "; ".join(csp_parts)
                
                # Set CSP header - Cloudflare may override, but we set it here
                response['Content-Security-Policy'] = csp_value
                
                # Also set X-Content-Security-Policy for older browsers and Cloudflare compatibility
                response['X-Content-Security-Policy'] = csp_value
                
                # If Cloudflare is detected, also set a header that Cloudflare Transform Rules can read
                if is_cloudflare:
                    # Set a custom header that Cloudflare can use in Transform Rules
                    response['X-CSP-Source'] = csp_value
        
        return response
    
    def _build_csp_parts(self, config, is_plugin_route=False):
        """Build CSP parts based on configuration"""
        script_src = ["'self'", "'unsafe-inline'", "'unsafe-eval'"]
        style_src = ["'self'", "'unsafe-inline'"]
        img_src = ["'self'", "data:", "https:"]
        font_src = ["'self'", "'unsafe-inline'"]
        connect_src = ["'self'", "https:", "wss:", "ws:"]
        
        # Add resources based on configuration
        if not config or config.allow_cdn_resources:
            script_src.extend([
                "https://www.jsdelivr.com",
                "https://cdn.jsdelivr.net",
                "https://cdnjs.cloudflare.com",
                "https://maxcdn.bootstrapcdn.com"
            ])
            style_src.extend([
                "https://www.jsdelivr.com",
                "https://cdnjs.cloudflare.com",
                "https://maxcdn.bootstrapcdn.com",
                "https://cdn.jsdelivr.net"
            ])
            font_src.extend([
                "https://www.jsdelivr.com",
                "https://cdnjs.cloudflare.com"
            ])
        
        if not config or config.allow_jquery:
            script_src.append("https://code.jquery.com")
        
        if not config or config.allow_angularjs:
            script_src.append("https://code.angularjs.org")
        
        if not config or config.allow_google_analytics:
            script_src.append("https://www.google-analytics.com")
            connect_src.extend([
                "https://www.google-analytics.com",
                "https://stats.g.doubleclick.net"
            ])
        
        if not config or config.allow_google_tag_manager:
            script_src.append("https://www.googletagmanager.com")
            connect_src.append("https://www.googletagmanager.com")
        
        if not config or config.allow_discord_auth:
            img_src.append("https://cdn.discordapp.com")
            connect_src.extend([
                "https://discord.com",
                "https://discordapp.com",
                "https://cdn.discordapp.com"
            ])
        
        # Always allow Cloudflare insights
        script_src.append("https://static.cloudflareinsights.com")
        connect_src.append("https://static.cloudflareinsights.com")
        
        # Always allow Google Fonts
        style_src.append("https://fonts.googleapis.com")
        font_src.extend([
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com"
        ])
        
        return [
            "default-src 'self'",
            f"script-src {' '.join(script_src)}",
            f"style-src {' '.join(style_src)}",
            f"img-src {' '.join(img_src)}",
            f"font-src {' '.join(font_src)}",
            f"connect-src {' '.join(connect_src)}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]