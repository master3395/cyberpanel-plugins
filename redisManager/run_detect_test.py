#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Redis Manager config path detection (implement, run, test).
Usage: cd /home/cyberpanel-plugins && python redisManager/run_detect_test.py
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def main():
    from redisManager import utils

    print('=== Redis Manager detect_redis_config_path ===')
    print('REDIS_CONF_PATHS:', utils.REDIS_CONF_PATHS)
    print()

    # 1) _config_path_from_cmdline
    print('1) _config_path_from_cmdline:')
    for sample in [
        '/usr/bin/redis-server\x00/etc/redis/redis.conf\x00--supervised\x00systemd',
        '/usr/bin/redis-server\x00/usr/local/etc/redis.conf',
    ]:
        path = utils._config_path_from_cmdline(sample)
        print('   sample -> %r' % path)
    print()

    # 2) Full detection
    print('2) detect_redis_config_path():')
    try:
        path = utils.detect_redis_config_path()
        if path:
            print('   SUCCESS: %s' % path)
            print('   File exists: %s' % os.path.isfile(path))
        else:
            print('   RESULT: None (no config found)')
    except Exception as e:
        print('   ERROR: %s' % e)
        import traceback
        traceback.print_exc()
        return 1
    print()

    # 3) get_redis_config_path
    print('3) get_redis_config_path(): %r' % utils.get_redis_config_path())
    print('=== Done ===')
    return 0

if __name__ == '__main__':
    sys.exit(main())
