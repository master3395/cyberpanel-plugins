# CSP Plugin Opt-Out Guide

## Overview

The CSP Manager plugin makes Content Security Policy **optional for plugins**. Plugins can opt-out of CSP restrictions if needed.

## How Plugins Can Opt-Out

### Method 1: Set Response Header (Recommended)

In your plugin view, set the `X-CSP-Opt-Out` header:

```python
from django.http import HttpResponse

def my_plugin_view(request):
    response = HttpResponse("Plugin content")
    response['X-CSP-Opt-Out'] = 'true'  # Opt-out of CSP
    return response
```

### Method 2: Automatic Opt-Out for Plugin Routes

All routes under `/plugins/` automatically get **more permissive CSP** that allows:
- All HTTPS/HTTP scripts, styles, images, fonts
- WebSocket connections
- Data URIs and blob URIs
- More flexibility for plugin-specific resources

### Method 3: Use CyberPanel's httpProc

If using `httpProc`, you can set headers:

```python
from plogical.httpProc import httpProc

def my_plugin_view(request):
    proc = httpProc(request, 'myPlugin/template.html', context, 'admin')
    response = proc.render()
    response['X-CSP-Opt-Out'] = 'true'
    return response
```

## CSP Behavior

### Core CyberPanel Pages
- **Standard CSP**: Restrictive CSP with specific allowed domains
- **Applies to**: Login, dashboard, settings, etc.

### Plugin Routes (`/plugins/*`)
- **Permissive CSP**: Allows more resources by default
- **Opt-Out Available**: Plugins can completely opt-out
- **Applies to**: All plugin pages

## Example: Plugin Opting Out

```python
# -*- coding: utf-8 -*-
from django.http import HttpResponse
from plogical.httpProc import httpProc
from plogical.mailUtilities import mailUtilities

def my_plugin_view(request):
    try:
        mailUtilities.checkHome()
        
        # Your plugin logic here
        context = {'data': 'example'}
        
        proc = httpProc(request, 'myPlugin/template.html', context, 'admin')
        response = proc.render()
        
        # Opt-out of CSP for this plugin
        response['X-CSP-Opt-Out'] = 'true'
        
        return response
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")
```

## Benefits

1. **Flexibility**: Plugins can use any resources they need
2. **Security**: Core CyberPanel pages still have strict CSP
3. **Compatibility**: Older plugins that don't work with CSP can opt-out
4. **Gradual Migration**: Plugins can opt-out now, add CSP support later

## Notes

- Opting out removes CSP entirely for that response
- Plugin routes automatically get more permissive CSP
- Core pages always use standard CSP
- The CSP Manager middleware runs after core secMiddleware
