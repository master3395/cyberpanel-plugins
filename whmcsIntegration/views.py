# -*- coding: utf-8 -*-
"""
WHMCS Integration - Documentation plugin
Links to the official CyberPanel WHMCS module (runs in WHMCS, not CyberPanel).
Original: https://github.com/jetchirag/cyberpanel-whmcs
Maintained: https://github.com/jesussuarz/cyberpanel-whmcs
"""
from django.shortcuts import render
from loginSystem.views import loadLoginPage
from plogical.acl import ACLManager


def index(request):
    """Render WHMCS integration documentation page."""
    try:
        userID = request.session.get('userID', None)
        if userID is None:
            return loadLoginPage(request)

        current_acl = ACLManager.loadedACL(userID)
        if current_acl.get('adminStatus', 0) != 1:
            return ACLManager.loadError()

        return render(request, 'whmcsIntegration/index.html', {
            'plugin_name': 'WHMCS Integration',
            'plugin_version': '1.0.0',
        })
    except Exception as e:
        return render(request, 'whmcsIntegration/index.html', {
            'plugin_name': 'WHMCS Integration',
            'plugin_version': '1.0.0',
            'error': str(e),
        })
