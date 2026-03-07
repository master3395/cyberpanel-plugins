# -*- coding: utf-8 -*-
"""
PM2 Manager Utility Functions
"""
import subprocess
import json
import os
import shlex
import time
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

def _run_pm2_command(command, timeout=10):
    """
    Execute PM2 command and return result.
    Tries root first (sudo -u root with HOME=/root) so we always use root's PM2
    and never trigger EACCES under the panel user's HOME. Falls back to current
    user only if root attempt fails (e.g. sudo not allowed).
    """
    pm2_path = _get_pm2_path()
    if not pm2_path:
        return {
            'success': False,
            'error': 'PM2 is not installed or not in PATH'
        }
    # Try root first so panel user never touches /usr/local/lscp/cyberpanel/.pm2
    result_root = _run_pm2_command_impl(pm2_path, command, timeout, run_as_root=True)
    if result_root['success']:
        return result_root
    result = _run_pm2_command_impl(pm2_path, command, timeout, run_as_root=False)
    if result['success']:
        return result
    return result_root

def _is_pm2_user_error(text):
    """True if error suggests PM2 daemon is running under another user (e.g. root)."""
    if not text:
        return False
    t = text.lower()
    return (
        'eacces' in t or 'permission denied' in t or
        'enonet' in t or 'no such file' in t or
        ('connect' in t and 'refused' in t) or
        ('daemon' in t and 'not' in t)
    )

def _run_pm2_command_impl(pm2_path, command, timeout=10, run_as_root=False):
    """Run PM2 command; optionally as root (sudo -u root) to use root's PM2 daemon."""
    try:
        args = shlex.split(command)
        if run_as_root:
            cmd_list = ['sudo', '-n', '-u', 'root', pm2_path] + args
            env = os.environ.copy()
            env['HOME'] = '/root'
            env.setdefault('PATH', '/usr/bin:/bin')
        else:
            cmd_list = [pm2_path] + args
            env = None
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=timeout,
            check=False,
            env=env
        )
        if result.returncode == 0:
            # Merge stdout and stderr - PM2 logs often writes to stderr
            out = result.stdout or ''
            err = result.stderr or ''
            combined = (out + '\n' + err).strip() if err else out.strip()
            return {'success': True, 'output': combined, 'error': None}
        return {
            'success': False,
            'output': result.stdout,
            'error': result.stderr or 'PM2 command failed'
        }
    except subprocess.TimeoutExpired:
        logging.writeToFile(f"PM2 command timeout: {command}")
        return {'success': False, 'error': 'Command timeout'}
    except Exception as e:
        logging.writeToFile(f"PM2 command error: {str(e)}")
        return {'success': False, 'error': str(e)}

def _get_pm2_path():
    """Get PM2 executable path. Prefer direct path check so it works when panel runs as lscpd (minimal PATH)."""
    possible_paths = [
        '/usr/bin/pm2',
        '/usr/local/bin/pm2',
        '/opt/nodejs/bin/pm2',
    ]
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    try:
        result = subprocess.run(
            ['which', 'pm2'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=2
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    try:
        result = subprocess.run(
            ['pm2', '--version'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=2
        )
        if result.returncode == 0:
            return 'pm2'
    except Exception:
        pass
    return None

def get_pm2_status():
    """
    Check if PM2 is installed and the daemon is running.
    Returns: dict with 'installed', 'running', 'message' (optional error/info).
    """
    pm2_path = _get_pm2_path()
    if not pm2_path:
        return {
            'installed': False,
            'running': False,
            'message': 'PM2 is not installed or not in PATH. Install with: npm install -g pm2'
        }
    # Check if PM2 daemon is running: "pm2 ping" returns 0 when daemon is up (output often contains "pong")
    result = _run_pm2_command("ping")
    if result['success']:
        return {
            'installed': True,
            'running': True,
            'message': None
        }
    err = (result.get('error') or result.get('output') or 'Unknown error').strip()
    return {
        'installed': True,
        'running': False,
        'message': err or 'PM2 daemon not responding. Run "pm2 list" in a shell to start the daemon.'
    }

def get_pm2_list():
    """Get list of PM2 processes in JSON format"""
    result = _run_pm2_command("jlist")
    if not result['success']:
        return []
    
    try:
        processes = json.loads(result['output'])
        return processes
    except json.JSONDecodeError:
        logging.writeToFile(f"Failed to parse PM2 jlist output: {result['output']}")
        return []

def get_pm2_info(app_name):
    """Get detailed information about a specific PM2 app"""
    result = _run_pm2_command(f"show {shlex.quote(app_name)}")
    if not result['success']:
        return None
    
    # Also get JSON info
    json_result = _run_pm2_command(f"show {shlex.quote(app_name)} --json")
    if json_result['success']:
        try:
            return json.loads(json_result['output'])
        except:
            pass
    
    return {'raw_output': result['output']}

def _get_pm2_logs_fallback(app_name, lines=100):
    """Fallback: read log files with sudo tail when pm2 logs fails. Needs: sudoers pm2-logs (tail)."""
    out_log = f"/root/.pm2/logs/{app_name}-out.log"
    err_log = f"/root/.pm2/logs/{app_name}-error.log"
    try:
        n = max(1, min(int(lines), 5000))
        r = subprocess.run(
            ['sudo', '-n', '-u', 'root', '/usr/bin/tail', '-n', str(n), out_log, err_log],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=5,
            check=False,
            env=None
        )
        if r.returncode == 0 and (r.stdout or r.stderr):
            combined = (r.stdout or '') + (r.stderr or '')
            return [s for s in combined.strip().split('\n') if s], None
    except Exception:
        pass
    return [], None


def get_pm2_logs(app_name, lines=100):
    """
    Get logs for a PM2 app.
    Returns (list_of_lines, error_message).
    On success: (lines, None). On failure: ([], error_msg).
    """
    result = _run_pm2_command(f"logs {shlex.quote(app_name)} --lines {lines} --nostream")
    if result['success']:
        output = (result.get('output') or '').strip()
        log_lines = output.split('\n') if output else []
        return log_lines, None
    fallback_lines, _ = _get_pm2_logs_fallback(app_name, lines)
    if fallback_lines:
        return fallback_lines, None
    err = result.get('error') or result.get('output', '') or 'Unknown error'
    return [], str(err).strip()

def start_pm2_app(app_name):
    """Start a PM2 app"""
    return _run_pm2_command(f"start {shlex.quote(app_name)}")

def stop_pm2_app(app_name):
    """Stop a PM2 app"""
    return _run_pm2_command(f"stop {shlex.quote(app_name)}")

def restart_pm2_app(app_name):
    """Restart a PM2 app"""
    return _run_pm2_command(f"restart {shlex.quote(app_name)}")

def delete_pm2_app(app_name):
    """Delete a PM2 app"""
    return _run_pm2_command(f"delete {shlex.quote(app_name)}")

def add_pm2_app(name, script_path, args=None, instances=1, exec_mode='fork', env_vars=None, 
                max_memory_restart=None, autorestart=True, cwd=None, interpreter=None):
    """
    Add a new PM2 application
    
    Args:
        name: Application name
        script_path: Path to the script to run
        args: Command line arguments (string)
        instances: Number of instances (for cluster mode)
        exec_mode: 'fork' or 'cluster'
        env_vars: Dictionary of environment variables
        max_memory_restart: Memory limit before restart (e.g., "500M", "1G")
        autorestart: Enable auto restart on crash (default: True)
        cwd: Current working directory path
        interpreter: Interpreter to use (e.g., "node", "python", "ruby")
    """
    if not os.path.exists(script_path):
        return {
            'success': False,
            'error': f'Script not found: {script_path}'
        }
    
    # Build PM2 start command
    cmd_parts = [f"start {shlex.quote(script_path)}"]
    cmd_parts.append(f"--name {shlex.quote(name)}")
    
    if instances > 1:
        cmd_parts.append(f"-i {instances}")
        cmd_parts.append("--exec-mode cluster")
    else:
        cmd_parts.append(f"--exec-mode {exec_mode}")
    
    # Memory limit
    if max_memory_restart:
        cmd_parts.append(f"--max-memory-restart {shlex.quote(str(max_memory_restart))}")
    
    # Auto restart
    if not autorestart:
        cmd_parts.append("--no-autorestart")
    
    # Current working directory
    if cwd:
        if not os.path.isdir(cwd):
            return {
                'success': False,
                'error': f'Working directory not found: {cwd}'
            }
        cmd_parts.append(f"--cwd {shlex.quote(cwd)}")
    
    # Interpreter
    if interpreter:
        cmd_parts.append(f"--interpreter {shlex.quote(interpreter)}")
    
    if args:
        cmd_parts.append(f"-- {args}")
    
    if env_vars:
        for key, value in env_vars.items():
            cmd_parts.append(f"--update-env {shlex.quote(f'{key}={value}')}")
    
    command = " ".join(cmd_parts)
    return _run_pm2_command(command)

def _normalize_mode(mode):
    """Normalize PM2 exec_mode e.g. fork_mode -> fork, cluster_mode -> cluster."""
    if not mode:
        return 'fork'
    s = (mode or '').strip().lower()
    if s in ('fork_mode', 'fork'):
        return 'fork'
    if s in ('cluster_mode', 'cluster'):
        return 'cluster'
    return mode

def format_pm2_process(process):
    """Format PM2 process data for display. Normalizes uptime to seconds."""
    pm2_env = process.get('pm2_env', {})
    monit = process.get('monit', {})

    pm_uptime = pm2_env.get('pm_uptime', 0)
    # PM2 may send start-time timestamp (ms) or duration (ms or seconds)
    if pm_uptime > 1e11:
        # Start-time timestamp in ms: uptime = now - start
        uptime_seconds = max(0, (int(time.time() * 1000) - int(pm_uptime)) / 1000)
    elif pm_uptime > 86400 * 1000:
        # Duration in ms
        uptime_seconds = pm_uptime / 1000
    else:
        uptime_seconds = pm_uptime  # already seconds or small ms

    # User: PM2 can expose username in pm2_env
    user = pm2_env.get('username') or pm2_env.get('user') or ''
    if isinstance(user, dict):
        user = user.get('username', '') or ''

    # PM2 may expose internal id as 'pm_id' or 'id'
    pm_id = process.get('pm_id', process.get('id', 0))
    return {
        'name': process.get('name', 'N/A'),
        'pid': process.get('pid', 0),
        'pm_id': pm_id,
        'id': pm_id,
        'status': pm2_env.get('status', 'unknown'),
        'cpu': monit.get('cpu', 0),
        'memory': monit.get('memory', 0),
        'uptime': int(uptime_seconds),
        'restarts': pm2_env.get('restart_time', 0),
        'script_path': pm2_env.get('pm_exec_path', 'N/A'),
        'mode': _normalize_mode(pm2_env.get('exec_mode', 'fork')),
        'instances': pm2_env.get('instances', 1),
        'namespace': pm2_env.get('namespace', 'default'),
        'version': pm2_env.get('version', '') or process.get('version', ''),
        'user': user if isinstance(user, str) else '',
        'watching': pm2_env.get('watch', False) or False,
    }
