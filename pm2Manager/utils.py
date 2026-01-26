# -*- coding: utf-8 -*-
"""
PM2 Manager Utility Functions
"""
import subprocess
import json
import os
import shlex
from plogical.CyberCPLogFileWriter import CyberCPLogFileWriter as logging

def _run_pm2_command(command, timeout=10):
    """
    Execute PM2 command and return result
    
    Args:
        command: PM2 command string (e.g., "pm2 list")
        timeout: Command timeout in seconds
    
    Returns:
        dict: {'success': bool, 'output': str, 'error': str}
    """
    try:
        # Ensure PM2 is available
        pm2_path = _get_pm2_path()
        if not pm2_path:
            return {
                'success': False,
                'error': 'PM2 is not installed or not in PATH'
            }
        
        # Execute command
        full_command = f"{pm2_path} {command}"
        result = subprocess.run(
            shlex.split(full_command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': result.stderr or 'PM2 command failed'
            }
    
    except subprocess.TimeoutExpired:
        logging.writeToFile(f"PM2 command timeout: {command}")
        return {
            'success': False,
            'error': 'Command timeout'
        }
    except Exception as e:
        logging.writeToFile(f"PM2 command error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def _get_pm2_path():
    """Get PM2 executable path"""
    possible_paths = [
        '/usr/bin/pm2',
        '/usr/local/bin/pm2',
        '/opt/nodejs/bin/pm2',
        'pm2'  # Try PATH
    ]
    
    for path in possible_paths:
        try:
            result = subprocess.run(
                ['which', path] if path != 'pm2' else ['which', 'pm2'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            continue
    
    # Try direct execution
    try:
        result = subprocess.run(
            ['pm2', '--version'],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return 'pm2'
    except:
        pass
    
    return None

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

def get_pm2_logs(app_name, lines=100):
    """Get logs for a PM2 app"""
    result = _run_pm2_command(f"logs {shlex.quote(app_name)} --lines {lines} --nostream")
    if not result['success']:
        return []
    
    # Parse logs (PM2 logs format)
    log_lines = result['output'].strip().split('\n')
    return log_lines

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

def format_pm2_process(process):
    """Format PM2 process data for display"""
    return {
        'name': process.get('name', 'N/A'),
        'pid': process.get('pid', 0),
        'pm_id': process.get('pm_id', 0),
        'status': process.get('pm2_env', {}).get('status', 'unknown'),
        'cpu': process.get('monit', {}).get('cpu', 0),
        'memory': process.get('monit', {}).get('memory', 0),
        'uptime': process.get('pm2_env', {}).get('pm_uptime', 0),
        'restarts': process.get('pm2_env', {}).get('restart_time', 0),
        'script_path': process.get('pm2_env', {}).get('pm_exec_path', 'N/A'),
        'mode': process.get('pm2_env', {}).get('exec_mode', 'fork'),
        'instances': process.get('pm2_env', {}).get('instances', 1),
    }
