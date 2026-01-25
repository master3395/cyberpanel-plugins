import subprocess
import json
import re
import os
from datetime import datetime, timedelta
from .models import SecurityEvent, BannedIP

class Fail2banManager:
    """Main class for managing fail2ban operations"""
    
    def __init__(self):
        self.fail2ban_cmd = 'fail2ban-client'
        self.firewall_cmd = 'firewall-cmd'
        self.config_file = '/etc/fail2ban/jail.local'
    
    def run_command(self, command, timeout=30):
        """Run a shell command and return the result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                'success': result.returncode == 0,
                'stdout': result.stdout.strip(),
                'stderr': result.stderr.strip(),
                'returncode': result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }
    
    def get_status(self):
        """Get fail2ban service status"""
        # Check if fail2ban is running
        status_cmd = 'systemctl is-active fail2ban'
        result = self.run_command(status_cmd)
        
        if not result['success']:
            return {
                'running': False,
                'error': 'Fail2ban service is not running'
            }
        
        # Get fail2ban status
        fail2ban_cmd = f'{self.fail2ban_cmd} status'
        result = self.run_command(fail2ban_cmd)
        
        if not result['success']:
            return {
                'running': False,
                'error': 'Failed to get fail2ban status'
            }
        
        # Parse the output
        lines = result['stdout'].split('\n')
        jails = []
        
        for line in lines:
            if 'Jail list:' in line:
                jail_list = line.split('Jail list:')[1].strip()
                jails = [jail.strip() for jail in jail_list.split(',') if jail.strip()]
                break
        
        return {
            'running': True,
            'jails': jails,
            'total_jails': len(jails)
        }
    
    def get_jails(self):
        """Get detailed information about all jails"""
        try:
            status_cmd = f'{self.fail2ban_cmd} status'
            result = self.run_command(status_cmd)
            
            if not result['success']:
                return []
            
            jails = []
            lines = result['stdout'].split('\n')
            current_jail = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Status for the jail:'):
                    jail_name = line.split('Status for the jail:')[1].strip()
                    current_jail = {
                        'name': jail_name,
                        'enabled': True,
                        'failed_attempts': 0,
                        'banned_ips': 0,
                        'banned_ip_list': []
                    }
                    jails.append(current_jail)
                elif current_jail and 'Currently failed:' in line:
                    current_jail['failed_attempts'] = int(line.split(':')[1].strip())
                elif current_jail and 'Currently banned:' in line:
                    current_jail['banned_ips'] = int(line.split(':')[1].strip())
                elif current_jail and 'Banned IP list:' in line:
                    banned_ips = line.split('Banned IP list:')[1].strip()
                    if banned_ips:
                        current_jail['banned_ip_list'] = [ip.strip() for ip in banned_ips.split() if ip.strip()]
            
            return jails
        except Exception as e:
            return []
    
    def get_banned_ips(self):
        """Get all currently banned IPs"""
        try:
            jails = self.get_jails()
            banned_ips = []
            
            for jail in jails:
                for ip in jail.get('banned_ip_list', []):
                    banned_ips.append({
                        'ip': ip,
                        'jail': jail['name'],
                        'banned_at': datetime.now().isoformat()
                    })
            
            return banned_ips
        except Exception as e:
            return []
    
    def get_whitelist(self):
        """Get whitelisted IPs from configuration"""
        try:
            if not os.path.exists(self.config_file):
                return []
            
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Find ignoreip line
            ignoreip_match = re.search(r'ignoreip\s*=\s*(.+)', content)
            if ignoreip_match:
                ignoreip_line = ignoreip_match.group(1).strip()
                ips = [ip.strip() for ip in ignoreip_line.split() if ip.strip()]
                return ips
            
            return []
        except Exception as e:
            return []
    
    def get_blacklist(self):
        """Get blacklisted IPs from firewall rules"""
        try:
            cmd = f'{self.firewall_cmd} --list-rich-rules | grep "drop"'
            result = self.run_command(cmd)
            
            if not result['success']:
                return []
            
            blacklisted_ips = []
            lines = result['stdout'].split('\n')
            
            for line in lines:
                if 'source address=' in line and 'drop' in line:
                    # Extract IP from rule
                    ip_match = re.search(r'source address="([^"]+)"', line)
                    if ip_match:
                        blacklisted_ips.append(ip_match.group(1))
            
            return blacklisted_ips
        except Exception as e:
            return []
    
    def add_to_whitelist(self, ip):
        """Add IP to whitelist"""
        try:
            # Validate IP format
            if not self.is_valid_ip(ip):
                return {'success': False, 'error': 'Invalid IP address format'}
            
            # Read current config
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    content = f.read()
            else:
                return {'success': False, 'error': 'Configuration file not found'}
            
            # Check if IP is already whitelisted
            if ip in content:
                return {'success': True, 'message': 'IP already whitelisted'}
            
            # Add IP to ignoreip line
            new_content = re.sub(
                r'(ignoreip\s*=\s*[^\n]+)',
                r'\1 ' + ip,
                content
            )
            
            # Write back to file
            with open(self.config_file, 'w') as f:
                f.write(new_content)
            
            # Restart fail2ban to apply changes
            self.restart_service()
            
            return {'success': True, 'message': f'IP {ip} added to whitelist'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_from_whitelist(self, ip):
        """Remove IP from whitelist"""
        try:
            if not os.path.exists(self.config_file):
                return {'success': False, 'error': 'Configuration file not found'}
            
            with open(self.config_file, 'r') as f:
                content = f.read()
            
            # Remove IP from ignoreip line
            new_content = re.sub(
                r'\s+' + re.escape(ip) + r'(?=\s|$)',
                '',
                content
            )
            
            # Write back to file
            with open(self.config_file, 'w') as f:
                f.write(new_content)
            
            # Restart fail2ban to apply changes
            self.restart_service()
            
            return {'success': True, 'message': f'IP {ip} removed from whitelist'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def add_to_blacklist(self, ip):
        """Add IP to blacklist (permanent ban)"""
        try:
            if not self.is_valid_ip(ip):
                return {'success': False, 'error': 'Invalid IP address format'}
            
            # Add firewall rule
            cmd = f'{self.firewall_cmd} --permanent --add-rich-rule="rule family=ipv4 source address={ip} drop"'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': 'Failed to add firewall rule'}
            
            # Reload firewall
            reload_cmd = f'{self.firewall_cmd} --reload'
            reload_result = self.run_command(reload_cmd)
            
            if not reload_result['success']:
                return {'success': False, 'error': 'Failed to reload firewall'}
            
            return {'success': True, 'message': f'IP {ip} added to blacklist'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def remove_from_blacklist(self, ip):
        """Remove IP from blacklist"""
        try:
            # Remove firewall rule
            cmd = f'{self.firewall_cmd} --permanent --remove-rich-rule="rule family=ipv4 source address={ip} drop"'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': 'Failed to remove firewall rule'}
            
            # Reload firewall
            reload_cmd = f'{self.firewall_cmd} --reload'
            reload_result = self.run_command(reload_cmd)
            
            if not reload_result['success']:
                return {'success': False, 'error': 'Failed to reload firewall'}
            
            return {'success': True, 'message': f'IP {ip} removed from blacklist'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def ban_ip(self, ip, jail='sshd'):
        """Ban an IP address"""
        try:
            if not self.is_valid_ip(ip):
                return {'success': False, 'error': 'Invalid IP address format'}
            
            # Ban IP using fail2ban
            cmd = f'{self.fail2ban_cmd} set {jail} banip {ip}'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': f'Failed to ban IP: {result["stderr"]}'}
            
            return {'success': True, 'message': f'IP {ip} banned from {jail}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def unban_ip(self, ip, jail='sshd'):
        """Unban an IP address"""
        try:
            if not self.is_valid_ip(ip):
                return {'success': False, 'error': 'Invalid IP address format'}
            
            # Unban IP using fail2ban
            cmd = f'{self.fail2ban_cmd} set {jail} unbanip {ip}'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': f'Failed to unban IP: {result["stderr"]}'}
            
            return {'success': True, 'message': f'IP {ip} unbanned from {jail}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restart_service(self):
        """Restart fail2ban service"""
        try:
            cmd = 'systemctl restart fail2ban'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': f'Failed to restart service: {result["stderr"]}'}
            
            return {'success': True, 'message': 'Fail2ban service restarted successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_logs(self, lines=100):
        """Get fail2ban logs"""
        try:
            cmd = f'journalctl -u fail2ban -n {lines} --no-pager'
            result = self.run_command(cmd)
            
            if not result['success']:
                return []
            
            logs = []
            for line in result['stdout'].split('\n'):
                if line.strip():
                    logs.append(line.strip())
            
            return logs
        except Exception as e:
            return []
    
    def is_valid_ip(self, ip):
        """Validate IP address format"""
        import ipaddress
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
    
    def start_service(self):
        """Start fail2ban service"""
        try:
            cmd = 'systemctl start fail2ban'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': f'Failed to start service: {result["stderr"]}'}
            
            return {'success': True, 'message': 'Fail2ban service started successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_service(self):
        """Stop fail2ban service"""
        try:
            cmd = 'systemctl stop fail2ban'
            result = self.run_command(cmd)
            
            if not result['success']:
                return {'success': False, 'error': f'Failed to stop service: {result["stderr"]}'}
            
            return {'success': True, 'message': 'Fail2ban service stopped successfully'}
        except Exception as e:
            return {'success': False, 'error': str(e)}