#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memcache Manager - Unit Tests for utils.py
Run with: python3 test_memcache_utils.py
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now import utils
try:
    from memcacheManager import utils
except ImportError:
    # Fallback for standalone testing
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "utils",
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "utils.py")
    )
    utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils)


class TestResults:
    """Simple test results tracker."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def test_pass(self, name):
        self.passed += 1
        print(f"  [PASS] {name}")
    
    def test_fail(self, name, reason):
        self.failed += 1
        self.errors.append((name, reason))
        print(f"  [FAIL] {name}: {reason}")
    
    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"Test Results: {self.passed}/{total} passed")
        if self.errors:
            print("\nFailed tests:")
            for name, reason in self.errors:
                print(f"  - {name}: {reason}")
        return self.failed == 0


def test_service_detection(results):
    """Test service detection functions."""
    print("\n[Testing Service Detection]")
    
    # Test detect_service_type
    try:
        service_type = utils.detect_service_type()
        if service_type in (None, 'memcached', 'lsmcd'):
            results.test_pass("detect_service_type returns valid value")
        else:
            results.test_fail("detect_service_type", f"Invalid return: {service_type}")
    except Exception as e:
        results.test_fail("detect_service_type", str(e))
    
    # Test is_installed
    try:
        installed = utils.is_installed()
        if isinstance(installed, bool):
            results.test_pass(f"is_installed returns bool: {installed}")
        else:
            results.test_fail("is_installed", f"Not a bool: {type(installed)}")
    except Exception as e:
        results.test_fail("is_installed", str(e))
    
    # Test get_service_name
    try:
        service_name = utils.get_service_name()
        if service_name in (None, 'memcached', 'lsmcd'):
            results.test_pass(f"get_service_name: {service_name}")
        else:
            results.test_fail("get_service_name", f"Invalid: {service_name}")
    except Exception as e:
        results.test_fail("get_service_name", str(e))


def test_service_status(results):
    """Test service status functions."""
    print("\n[Testing Service Status]")
    
    # Test get_service_status
    try:
        status_key, status_msg = utils.get_service_status()
        valid_keys = ('running', 'stopped', 'not-installed', 'unknown')
        if status_key in valid_keys:
            results.test_pass(f"get_service_status: {status_key} - {status_msg}")
        else:
            results.test_fail("get_service_status", f"Invalid key: {status_key}")
    except Exception as e:
        results.test_fail("get_service_status", str(e))


def test_connection(results):
    """Test connection functions."""
    print("\n[Testing Connection]")
    
    # Test test_connection
    try:
        ok, msg = utils.test_connection()
        results.test_pass(f"test_connection: success={ok}, msg={msg[:50]}...")
    except Exception as e:
        results.test_fail("test_connection", str(e))


def test_memcache_commands(results):
    """Test memcache command functions."""
    print("\n[Testing Memcache Commands]")
    
    # Test send_memcache_command
    try:
        ok, response = utils.send_memcache_command('stats')
        if ok:
            results.test_pass(f"send_memcache_command stats: {len(response)} bytes")
        else:
            results.test_pass(f"send_memcache_command (not running): {response[:50]}")
    except Exception as e:
        results.test_fail("send_memcache_command", str(e))
    
    # Test get_memcache_stats
    try:
        stats, error = utils.get_memcache_stats()
        if stats:
            results.test_pass(f"get_memcache_stats: {len(stats)} keys")
        elif error:
            results.test_pass(f"get_memcache_stats (not running): {error[:50]}")
        else:
            results.test_fail("get_memcache_stats", "No stats or error")
    except Exception as e:
        results.test_fail("get_memcache_stats", str(e))


def test_configuration(results):
    """Test configuration functions."""
    print("\n[Testing Configuration]")
    
    # Test get_memcache_config
    try:
        config, error = utils.get_memcache_config()
        if config:
            results.test_pass(f"get_memcache_config: service_type={config.get('service_type')}")
        elif error:
            results.test_pass(f"get_memcache_config (not installed): {error[:50]}")
        else:
            results.test_fail("get_memcache_config", "No config or error")
    except Exception as e:
        results.test_fail("get_memcache_config", str(e))


def test_format_bytes(results):
    """Test format_bytes helper function."""
    print("\n[Testing Format Bytes]")
    
    test_cases = [
        (0, '0 B'),
        (100, '100 B'),
        (1024, '1.00 KB'),
        (1048576, '1.00 MB'),
        (1073741824, '1.00 GB'),
    ]
    
    for input_val, expected in test_cases:
        try:
            result = utils.format_bytes(input_val)
            if result == expected:
                results.test_pass(f"format_bytes({input_val}) = {result}")
            else:
                results.test_fail(f"format_bytes({input_val})", f"Got {result}, expected {expected}")
        except Exception as e:
            results.test_fail(f"format_bytes({input_val})", str(e))


def test_run_cmd(results):
    """Test run_cmd helper function."""
    print("\n[Testing Run Command]")
    
    # Test successful command
    try:
        ok, out = utils.run_cmd('echo "hello"')
        if ok and 'hello' in out:
            results.test_pass("run_cmd echo: success")
        else:
            results.test_fail("run_cmd echo", f"ok={ok}, out={out}")
    except Exception as e:
        results.test_fail("run_cmd echo", str(e))
    
    # Test failed command
    try:
        ok, out = utils.run_cmd('false')
        if not ok:
            results.test_pass("run_cmd false: correctly returns failure")
        else:
            results.test_fail("run_cmd false", "Should have failed")
    except Exception as e:
        results.test_fail("run_cmd false", str(e))


def main():
    """Run all tests."""
    print("=" * 60)
    print("Memcache Manager - Utils Test Suite")
    print("=" * 60)
    
    results = TestResults()
    
    # Run all test groups
    test_run_cmd(results)
    test_format_bytes(results)
    test_service_detection(results)
    test_service_status(results)
    test_connection(results)
    test_memcache_commands(results)
    test_configuration(results)
    
    # Print summary
    success = results.summary()
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
