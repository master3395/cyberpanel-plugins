# -*- coding: utf-8 -*-
"""
Memcache Manager - utility functions for Memcached/LSMCD status, control, stats, and config.
Supports both standard Memcached and LiteSpeed LSMCD with automatic detection.
"""
import subprocess
import shlex
import os
import socket
import re

# Service configuration
MEMCACHED_MARKER = '/home/cyberpanel/memcached'
LSMCD_MARKER = '/home/cyberpanel/lsmcd'

# Service binaries
MEMCACHED_BIN = '/usr/bin/memcached'
LSMCD_BIN = '/usr/local/lsmcd/bin/lsmcd'

# Service names
MEMCACHED_SERVICE = 'memcached'
LSMCD_SERVICE = 'lsmcd'

# Default connection settings
MEMCACHE_HOST = '127.0.0.1'
MEMCACHE_PORT = 11211

# Config file locations
MEMCACHED_CONFIG = '/etc/sysconfig/memcached'
MEMCACHED_CONFIG_ALT = '/etc/memcached.conf'
LSMCD_CONFIG = '/usr/local/lsmcd/conf/node.conf'


def detect_service_type():
    """
    Detect which memcache service is installed.
    Returns: 'memcached', 'lsmcd', or None
    """
    # Check for LSMCD first (more specific)
    if os.path.exists(LSMCD_MARKER) or os.path.exists(LSMCD_BIN):
        return 'lsmcd'
    # Check for standard memcached
    if os.path.exists(MEMCACHED_MARKER) or os.path.exists(MEMCACHED_BIN):
        return 'memcached'
    # Check if either service is active
    for service in [LSMCD_SERVICE, MEMCACHED_SERVICE]:
        ok, out = run_cmd('systemctl is-active %s' % service, timeout=5)
        if ok and out.strip().lower() == 'active':
            return service
    return None


def is_installed():
    """Return True if any memcache service is installed."""
    return detect_service_type() is not None


def get_service_name():
    """Get the active service name."""
    service_type = detect_service_type()
    if service_type == 'lsmcd':
        return LSMCD_SERVICE
    elif service_type == 'memcached':
        return MEMCACHED_SERVICE
    return None


def run_cmd(command, timeout=10):
    """Run shell command, return (success, output)."""
    try:
        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        out = (result.stdout or '').strip()
        err = (result.stderr or '').strip()
        if err and not out:
            out = err
        elif err:
            out = out + '\n' + err
        return result.returncode == 0, out
    except subprocess.TimeoutExpired:
        return False, 'Command timed out'
    except FileNotFoundError:
        return False, 'Command not found'
    except Exception as e:
        return False, str(e)


def get_service_status():
    """
    Return status of memcache service: running, stopped, or not-installed.
    Returns: (status_key, status_msg)
    """
    service_type = detect_service_type()
    if not service_type:
        return 'not-installed', 'Memcache is not installed. Install Memcached or LSMCD from Manage Services.'
    
    service_name = LSMCD_SERVICE if service_type == 'lsmcd' else MEMCACHED_SERVICE
    ok, out = run_cmd('systemctl is-active %s' % service_name)
    
    if not out:
        return 'unknown', 'Could not determine status'
    
    status = out.strip().lower()
    service_display = 'LSMCD' if service_type == 'lsmcd' else 'Memcached'
    
    if status == 'active':
        return 'running', '%s Running' % service_display
    if status in ('inactive', 'failed', 'dead'):
        return 'stopped', '%s Stopped' % service_display
    return 'unknown', '%s: %s' % (service_display, status)


def service_control(action):
    """
    Start, stop, or restart memcache service.
    action: start, stop, restart, enable, disable
    Returns: (success, message)
    """
    if action not in ('start', 'stop', 'restart', 'enable', 'disable'):
        return False, 'Invalid action'
    
    service_type = detect_service_type()
    if not service_type:
        return False, 'Memcache is not installed.'
    
    service_name = LSMCD_SERVICE if service_type == 'lsmcd' else MEMCACHED_SERVICE
    ok, out = run_cmd('systemctl %s %s' % (action, service_name), timeout=30)
    
    if ok:
        return True, '%s %sed successfully.' % (service_name.upper(), action)
    return False, out or '%s failed' % action.capitalize()


def test_connection(host=None, port=None):
    """
    Test TCP connection to memcache server.
    Returns: (success, message)
    """
    host = host or MEMCACHE_HOST
    port = port or MEMCACHE_PORT
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        
        if result == 0:
            return True, 'Connection successful to %s:%s' % (host, port)
        return False, 'Cannot connect to %s:%s (error code: %d)' % (host, port, result)
    except socket.timeout:
        return False, 'Connection timed out'
    except Exception as e:
        return False, 'Connection error: %s' % str(e)


def send_memcache_command(command, host=None, port=None, timeout=5):
    """
    Send command to memcache server and return response.
    Returns: (success, response)
    """
    host = host or MEMCACHE_HOST
    port = port or MEMCACHE_PORT
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, int(port)))
        
        # Send command
        sock.sendall((command + '\r\n').encode('utf-8'))
        
        # Receive response
        response = b''
        while True:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                # Check for END or ERROR markers
                if b'END\r\n' in response or b'ERROR' in response or b'OK\r\n' in response:
                    break
            except socket.timeout:
                break
        
        sock.close()
        return True, response.decode('utf-8', errors='replace')
    except socket.timeout:
        return False, 'Connection timed out'
    except ConnectionRefusedError:
        return False, 'Connection refused - memcache may not be running'
    except Exception as e:
        return False, 'Error: %s' % str(e)


def get_memcache_stats():
    """
    Get memcache statistics.
    Returns: (stats_dict, error_message)
    """
    if not is_installed():
        return None, 'Memcache is not installed.'
    
    ok, response = send_memcache_command('stats')
    if not ok:
        return None, response
    
    # Parse stats response
    stats = {}
    for line in response.split('\n'):
        line = line.strip()
        if line.startswith('STAT '):
            parts = line.split(' ', 2)
            if len(parts) >= 3:
                key = parts[1]
                value = parts[2]
                # Try to convert numeric values
                try:
                    if '.' in value:
                        stats[key] = float(value)
                    else:
                        stats[key] = int(value)
                except ValueError:
                    stats[key] = value
    
    if not stats:
        return None, 'Could not parse stats response'
    
    # Calculate additional metrics
    if 'get_hits' in stats and 'get_misses' in stats:
        total_gets = stats['get_hits'] + stats['get_misses']
        if total_gets > 0:
            stats['hit_rate'] = round((stats['get_hits'] / total_gets) * 100, 2)
            stats['miss_rate'] = round((stats['get_misses'] / total_gets) * 100, 2)
        else:
            stats['hit_rate'] = 0
            stats['miss_rate'] = 0
    
    if 'bytes' in stats and 'limit_maxbytes' in stats:
        if stats['limit_maxbytes'] > 0:
            stats['memory_usage_percent'] = round(
                (stats['bytes'] / stats['limit_maxbytes']) * 100, 2
            )
        else:
            stats['memory_usage_percent'] = 0
    
    # Format uptime
    if 'uptime' in stats:
        uptime_secs = stats['uptime']
        days = uptime_secs // 86400
        hours = (uptime_secs % 86400) // 3600
        minutes = (uptime_secs % 3600) // 60
        stats['uptime_formatted'] = '%dd %dh %dm' % (days, hours, minutes)
    
    return stats, None


def get_memcache_stats_raw():
    """
    Get raw memcache stats output.
    Returns: (raw_text, error_message)
    """
    if not is_installed():
        return None, 'Memcache is not installed.'
    
    ok, response = send_memcache_command('stats')
    if not ok:
        return None, response
    
    return response, None


def memcache_flush_all():
    """
    Flush all memcache data.
    Returns: (success, message)
    """
    if not is_installed():
        return False, 'Memcache is not installed.'
    
    ok, response = send_memcache_command('flush_all')
    if ok and 'OK' in response:
        return True, 'Cache flushed successfully.'
    return False, response or 'Flush failed.'


def get_memcache_config():
    """
    Read memcache configuration.
    Returns: (config_dict, error_message)
    """
    service_type = detect_service_type()
    if not service_type:
        return None, 'Memcache is not installed.'
    
    config = {
        'service_type': service_type,
        'service_name': LSMCD_SERVICE if service_type == 'lsmcd' else MEMCACHED_SERVICE,
        'host': MEMCACHE_HOST,
        'port': MEMCACHE_PORT,
        'config_file': None,
        'settings': {}
    }
    
    if service_type == 'lsmcd':
        config['config_file'] = LSMCD_CONFIG
        config = _parse_lsmcd_config(config)
    else:
        # Try both config file locations
        if os.path.exists(MEMCACHED_CONFIG):
            config['config_file'] = MEMCACHED_CONFIG
        elif os.path.exists(MEMCACHED_CONFIG_ALT):
            config['config_file'] = MEMCACHED_CONFIG_ALT
        config = _parse_memcached_config(config)
    
    return config, None


def _parse_memcached_config(config):
    """Parse memcached configuration file."""
    config_file = config.get('config_file')
    if not config_file or not os.path.exists(config_file):
        return config
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        # Parse sysconfig style (KEY="value")
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"\'')
                
                if key == 'PORT':
                    config['port'] = int(value)
                    config['settings']['port'] = value
                elif key == 'USER':
                    config['settings']['user'] = value
                elif key == 'MAXCONN':
                    config['settings']['max_connections'] = value
                elif key == 'CACHESIZE':
                    config['settings']['cache_size_mb'] = value
                elif key == 'OPTIONS':
                    config['settings']['options'] = value
        
        # Parse debian style (-m 64 -p 11211)
        if 'OPTIONS' in config['settings']:
            opts = config['settings']['options']
            if '-m' in opts:
                match = re.search(r'-m\s+(\d+)', opts)
                if match:
                    config['settings']['cache_size_mb'] = match.group(1)
            if '-c' in opts:
                match = re.search(r'-c\s+(\d+)', opts)
                if match:
                    config['settings']['max_connections'] = match.group(1)
            if '-t' in opts:
                match = re.search(r'-t\s+(\d+)', opts)
                if match:
                    config['settings']['threads'] = match.group(1)
    
    except Exception:
        pass
    
    return config


def _parse_lsmcd_config(config):
    """Parse LSMCD configuration file."""
    config_file = config.get('config_file')
    if not config_file or not os.path.exists(config_file):
        return config
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                
                if key == 'cached.slicecnt':
                    config['settings']['slice_count'] = value
                elif key == 'cached.maxconn':
                    config['settings']['max_connections'] = value
                elif key == 'cached.maxmem':
                    config['settings']['max_memory'] = value
                elif key == 'cached.sock':
                    config['settings']['socket'] = value
                elif key == 'cached.addr':
                    parts = value.split(':')
                    if len(parts) >= 2:
                        config['port'] = int(parts[1])
                        config['settings']['listen_address'] = value
    
    except Exception:
        pass
    
    return config


def format_bytes(bytes_val):
    """Format bytes to human readable string."""
    try:
        bytes_val = int(bytes_val)
        if bytes_val < 1024:
            return '%d B' % bytes_val
        elif bytes_val < 1024 * 1024:
            return '%.2f KB' % (bytes_val / 1024)
        elif bytes_val < 1024 * 1024 * 1024:
            return '%.2f MB' % (bytes_val / (1024 * 1024))
        else:
            return '%.2f GB' % (bytes_val / (1024 * 1024 * 1024))
    except (ValueError, TypeError):
        return str(bytes_val)
