# -*- coding: utf-8 -*-
"""
OpenLiteSpeed reverse-proxy setup for Panel Access (custom domain).
Creates a proxy-only vhost so the panel is reachable at the custom domain
without manual OLS configuration.
"""
import os
import re

# Path used by CyberPanel for panel port (same as ProcessUtilities.portPath); SSH login message uses this
BIND_CONF = '/usr/local/lscp/conf/bind.conf'


def get_panel_port():
    """Detect panel port from bind.conf (*:PORT). Fallback 8090 (default), then 2087 (common alternate)."""
    if os.environ.get('PANEL_BACKEND_URL'):
        # Let caller parse URL if they need port from env
        pass
    try:
        if os.path.isfile(BIND_CONF):
            with open(BIND_CONF, 'r') as f:
                line = f.read().strip()
            if '*' in line and ':' in line:
                port = line.split(':')[1].strip().split()[0]
                if port.isdigit():
                    return port
    except (OSError, IOError):
        pass
    return '8090'


def get_panel_backend_url():
    """Panel backend URL for proxy. Prefer PANEL_BACKEND_URL env; else detect port from bind.conf."""
    url = os.environ.get('PANEL_BACKEND_URL', '').strip()
    if url:
        return url
    port = get_panel_port()
    return 'https://127.0.0.1:{}'.format(port)


# Used when module loads (can be overridden by get_panel_backend_url() at runtime)
PANEL_BACKEND_URL = os.environ.get('PANEL_BACKEND_URL') or ('https://127.0.0.1:' + get_panel_port())
LSWS_ROOT = '/usr/local/lsws'
VHOSTS_DIR = os.path.join(LSWS_ROOT, 'conf', 'vhosts')
PANEL_PROXY_VHROOT = '/usr/local/lsws/panel_proxy'
HTTPD_CONFIG = '/usr/local/lsws/conf/httpd_config.conf'


def _domain_from_origin(origin):
    """Extract host from origin (e.g. https://panel.example.com -> panel.example.com)."""
    if not origin or not isinstance(origin, str):
        return None
    origin = origin.strip().lower()
    if origin.startswith('http://'):
        origin = origin[7:]
    elif origin.startswith('https://'):
        origin = origin[8:]
    if '/' in origin:
        origin = origin.split('/')[0]
    if ':' in origin:
        origin = origin.split(':')[0]
    # Basic hostname validation
    if origin and re.match(r'^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$', origin):
        return origin
    return None


def _vhost_conf_content(domain, backend_url):
    """Generate vhost.conf content: proxy entire site to panel backend."""
    # OLS: extprocessor (proxy) + context / (handler = proxy)
    return """# Panel Access: reverse proxy to CyberPanel backend (do not edit manually)
docRoot                   {vhroot}/
vhDomain                  {domain}
enableGzip                1

extprocessor panelbackend {{
  type                    proxy
  address                 {backend}
  maxConns                100
  initTimeout             60
  retryTimeout            0
  respBuffer              0
}}

context / {{
  type                    proxy
  handler                 panelbackend
  addDefaultCharset       off
}}

errorlog $VH_ROOT/logs/error.log {{
  logLevel                WARN
  rollingSize             10M
  useServer               0
}}

accessLog $VH_ROOT/logs/access.log {{
  rollingSize             10M
  keepDays                7
  useServer               0
}}
""".format(
        vhroot=PANEL_PROXY_VHROOT,
        domain=domain,
        backend=backend_url,
    )


def _virtual_host_block(domain):
    """VirtualHost block for httpd_config.conf (same shape as olsMasterMainConf but vhRoot fixed)."""
    return """virtualHost {domain} {{
  vhRoot                  {vhroot}
  configFile              $SERVER_ROOT/conf/vhosts/{domain}/vhost.conf
  allowSymbolLink         1
  enableScript            1
  restrained              1
}}
""".format(domain=domain, vhroot=PANEL_PROXY_VHROOT)


def _domain_already_mapped(domain, lines):
    """Return True if domain is already in a listener map."""
    for line in lines:
        if 'map' in line and domain in line.split():
            return True
    return False


def _vhost_block_exists(domain, lines):
    """Return True if virtualHost {domain} already exists."""
    marker = 'virtualHost {}'.format(domain)
    for line in lines:
        if marker in line and ('virtualHost' in line):
            return True
    return False


def setup_panel_proxy_vhost(domain_name):
    """
    Create OpenLiteSpeed proxy vhost for the given domain (panel accessible at domain -> backend).
    Returns (success: bool, message: str).
    """
    try:
        from plogical.processUtilities import ProcessUtilities
        from plogical import installUtilities
        from plogical import CyberCPLogFileWriter as logging
    except ImportError:
        return False, 'CyberPanel plumbing not available (run inside CyberPanel).'

    if ProcessUtilities.decideServer() != ProcessUtilities.OLS:
        return False, 'Only OpenLiteSpeed is supported for automatic proxy setup.'

    domain = _domain_from_origin(domain_name) if _domain_from_origin(domain_name) else domain_name
    if not domain or not re.match(r'^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$', domain):
        return False, 'Invalid domain: {}'.format(domain_name)

    vhost_dir = os.path.join(VHOSTS_DIR, domain)
    vhost_conf = os.path.join(vhost_dir, 'vhost.conf')

    # Create vhRoot and vhost dirs
    try:
        os.makedirs(PANEL_PROXY_VHROOT, mode=0o755, exist_ok=True)
        log_dir = os.path.join(PANEL_PROXY_VHROOT, 'logs')
        os.makedirs(log_dir, mode=0o755, exist_ok=True)
        os.makedirs(vhost_dir, mode=0o755, exist_ok=True)
    except OSError as e:
        logging.writeToFile('[panelAccess.ols_proxy] makedirs: {}'.format(e))
        return False, 'Could not create directories: {}'.format(e)

    # Write vhost.conf (use detected panel URL so port 2087/8090 is correct)
    backend_url = get_panel_backend_url()
    try:
        with open(vhost_conf, 'w') as f:
            f.write(_vhost_conf_content(domain, backend_url))
    except OSError as e:
        logging.writeToFile('[panelAccess.ols_proxy] write vhost.conf: {}'.format(e))
        return False, 'Could not write vhost config: {}'.format(e)

    # Add virtualHost + map to httpd_config.conf (idempotent)
    if not os.path.isfile(HTTPD_CONFIG):
        return False, 'OpenLiteSpeed config not found.'

    def modifier(current_lines):
        out = list(current_lines)
        if not _domain_already_mapped(domain, out):
            for i, line in enumerate(out):
                if 'listener' in line and 'Default' in line:
                    out.insert(i + 1, '  map                     {} {}\n'.format(domain, domain))
                    break
            else:
                raise ValueError('Default listener not found in httpd_config.conf')
        if not _vhost_block_exists(domain, out):
            out.append(_virtual_host_block(domain))
        return out

    success, error = installUtilities.installUtilities.safeModifyHttpdConfig(
        modifier,
        'Panel Access: add proxy vhost for {}'.format(domain),
    )
    if not success:
        return False, error or 'Failed to update httpd_config.conf.'

    # Reload OpenLiteSpeed
    try:
        cmd = '/usr/local/lsws/bin/lswsctrl reload'
        subprocess = __import__('subprocess')
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
        if r.returncode != 0:
            logging.writeToFile('[panelAccess.ols_proxy] lswsctrl reload: {}'.format(r.stderr or r.stdout))
    except Exception as e:
        logging.writeToFile('[panelAccess.ols_proxy] reload: {}'.format(e))

    return True, 'Proxy for {} added. Reload OpenLiteSpeed if needed.'.format(domain)


def domain_from_origin(origin):
    """Public helper: extract hostname from origin URL."""
    return _domain_from_origin(origin)
