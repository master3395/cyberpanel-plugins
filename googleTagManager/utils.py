# -*- coding: utf-8 -*-
"""
Google Tag Manager Plugin Utility Functions
"""

from .models import GTMSettings
from plogical.acl import ACLManager
from websiteFunctions.models import Websites, ChildDomains


def get_user_domains(userID, currentACL):
    """
    Get all domains accessible by the current user
    
    Returns:
        list: List of domain dictionaries with domain name and type
    """
    domains = []
    
    try:
        # Get all domains using ACLManager
        domain_list = ACLManager.findAllDomains(currentACL, userID)
        
        for domain_name in domain_list:
            # Try to find if it's a main website or child domain
            website = None
            child_domain = None
            
            try:
                website = Websites.objects.get(domain=domain_name)
            except Websites.DoesNotExist:
                try:
                    child_domain = ChildDomains.objects.get(domain=domain_name)
                    website = child_domain.master
                except ChildDomains.DoesNotExist:
                    pass
            
            domains.append({
                'domain': domain_name,
                'type': 'main' if website and not child_domain else 'child',
                'website': website
            })
        
        # Sort domains alphabetically
        domains.sort(key=lambda x: x['domain'])
        
    except Exception as e:
        # Log error but return empty list
        from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging
        logging.writeToFile(f"Error getting user domains: {str(e)}")
    
    return domains


def get_gtm_code_head(container_id):
    """
    Generate GTM code for <head> section
    
    Args:
        container_id: GTM container ID (e.g., GTM-XXXXXXX)
    
    Returns:
        str: HTML code for <head> section
    """
    # Ensure container_id has GTM- prefix
    if not container_id.startswith('GTM-'):
        container_id = f'GTM-{container_id}'
    
    return f'''<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':
new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
}})(window,document,'script','dataLayer','{container_id}');</script>
<!-- End Google Tag Manager -->'''


def get_gtm_code_body(container_id):
    """
    Generate GTM code for <body> section (noscript fallback)
    
    Args:
        container_id: GTM container ID (e.g., GTM-XXXXXXX)
    
    Returns:
        str: HTML code for <body> section
    """
    # Ensure container_id has GTM- prefix
    if not container_id.startswith('GTM-'):
        container_id = f'GTM-{container_id}'
    
    return f'''<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id={container_id}"
height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>
<!-- End Google Tag Manager (noscript) -->'''


def get_gtm_code_full(container_id):
    """
    Get complete GTM code (head + body)
    
    Args:
        container_id: GTM container ID (e.g., GTM-XXXXXXX)
    
    Returns:
        dict: Dictionary with 'head' and 'body' code snippets
    """
    return {
        'head': get_gtm_code_head(container_id),
        'body': get_gtm_code_body(container_id),
        'container_id': container_id
    }


def get_gtm_for_domain(domain):
    """
    Get GTM settings for a specific domain
    
    Args:
        domain: Domain name
    
    Returns:
        GTMSettings object or None
    """
    try:
        return GTMSettings.objects.get(domain=domain, enabled=True)
    except GTMSettings.DoesNotExist:
        return None
    except GTMSettings.MultipleObjectsReturned:
        # Should not happen, but handle it
        return GTMSettings.objects.filter(domain=domain, enabled=True).first()
