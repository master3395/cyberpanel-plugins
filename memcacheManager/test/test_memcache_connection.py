#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memcache Manager - Connection and Integration Tests
Run with: python3 test_memcache_connection.py
"""
import socket
import sys
import time


class MemcacheConnectionTest:
    """Test memcache connection and basic operations."""
    
    def __init__(self, host='127.0.0.1', port=11211, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.passed = 0
        self.failed = 0
    
    def log_pass(self, test_name, details=''):
        self.passed += 1
        detail_str = f': {details}' if details else ''
        print(f'  [PASS] {test_name}{detail_str}')
    
    def log_fail(self, test_name, error):
        self.failed += 1
        print(f'  [FAIL] {test_name}: {error}')
    
    def send_command(self, command):
        """Send command to memcache and return response."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((self.host, self.port))
            
            sock.sendall((command + '\r\n').encode('utf-8'))
            
            response = b''
            while True:
                try:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk
                    if b'END\r\n' in response or b'ERROR' in response or b'OK\r\n' in response:
                        break
                    if b'STORED\r\n' in response or b'NOT_STORED\r\n' in response:
                        break
                    if b'DELETED\r\n' in response or b'NOT_FOUND\r\n' in response:
                        break
                except socket.timeout:
                    break
            
            sock.close()
            return True, response.decode('utf-8', errors='replace')
        except socket.timeout:
            return False, 'Connection timed out'
        except ConnectionRefusedError:
            return False, 'Connection refused'
        except Exception as e:
            return False, str(e)
    
    def test_connection(self):
        """Test basic TCP connection."""
        print('\n[Testing TCP Connection]')
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((self.host, self.port))
            sock.close()
            
            if result == 0:
                self.log_pass('TCP connection', f'{self.host}:{self.port}')
                return True
            else:
                self.log_fail('TCP connection', f'Error code {result}')
                return False
        except Exception as e:
            self.log_fail('TCP connection', str(e))
            return False
    
    def test_stats(self):
        """Test stats command."""
        print('\n[Testing Stats Command]')
        ok, response = self.send_command('stats')
        
        if not ok:
            self.log_fail('stats command', response)
            return False
        
        if 'STAT' in response:
            self.log_pass('stats command', 'Received valid response')
            
            stats = {}
            for line in response.split('\n'):
                if line.startswith('STAT '):
                    parts = line.split(' ', 2)
                    if len(parts) >= 3:
                        stats[parts[1]] = parts[2].strip()
            
            if 'version' in stats:
                self.log_pass('version', stats['version'])
            if 'uptime' in stats:
                uptime = int(stats['uptime'])
                days = uptime // 86400
                hours = (uptime % 86400) // 3600
                self.log_pass('uptime', f'{days}d {hours}h')
            if 'curr_items' in stats:
                self.log_pass('current items', stats['curr_items'])
            
            return True
        else:
            self.log_fail('stats command', 'Invalid response format')
            return False
    
    def test_set_get_delete(self):
        """Test set, get, and delete operations."""
        print('\n[Testing Set/Get/Delete Operations]')
        test_key = f'cyberpanel_test_{int(time.time())}'
        test_value = 'test_value_12345'
        
        # Test SET
        set_cmd = f'set {test_key} 0 60 {len(test_value)}\r\n{test_value}'
        ok, response = self.send_command(set_cmd)
        
        if ok and 'STORED' in response:
            self.log_pass('SET operation')
        else:
            self.log_fail('SET operation', response[:50])
            return False
        
        # Test GET
        ok, response = self.send_command(f'get {test_key}')
        
        if ok and test_value in response:
            self.log_pass('GET operation', 'Value retrieved correctly')
        else:
            self.log_fail('GET operation', response[:50])
            return False
        
        # Test DELETE
        ok, response = self.send_command(f'delete {test_key}')
        
        if ok and 'DELETED' in response:
            self.log_pass('DELETE operation')
        else:
            self.log_fail('DELETE operation', response[:50])
            return False
        
        return True
    
    def test_version(self):
        """Test version command."""
        print('\n[Testing Version Command]')
        ok, response = self.send_command('version')
        
        if ok and 'VERSION' in response:
            version = response.replace('VERSION', '').strip()
            self.log_pass('version command', version)
            return True
        else:
            self.log_fail('version command', response[:50])
            return False
    
    def run_all_tests(self):
        """Run all tests and return success status."""
        print('=' * 60)
        print('Memcache Connection Test Suite')
        print(f'Target: {self.host}:{self.port}')
        print('=' * 60)
        
        if not self.test_connection():
            print('\n[ABORT] Cannot connect to memcache server')
            print('        Ensure memcached or lsmcd is running')
            return False
        
        self.test_version()
        self.test_stats()
        self.test_set_get_delete()
        
        total = self.passed + self.failed
        print('\n' + '=' * 60)
        print(f'Test Results: {self.passed}/{total} passed')
        print('=' * 60)
        
        return self.failed == 0


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test memcache connection')
    parser.add_argument('--host', default='127.0.0.1', help='Memcache host')
    parser.add_argument('--port', type=int, default=11211, help='Memcache port')
    parser.add_argument('--timeout', type=int, default=5, help='Connection timeout')
    
    args = parser.parse_args()
    
    tester = MemcacheConnectionTest(
        host=args.host,
        port=args.port,
        timeout=args.timeout
    )
    
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
