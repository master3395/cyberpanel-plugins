#!/usr/bin/env python3
"""
Test Contabo API connection. Run from CyberCP directory:
  cd /usr/local/CyberCP && python3 contaboAutoSnapshot/test_contabo_api.py

Set env: CONTABO_CLIENT_SECRET, CONTABO_API_USER (email), CONTABO_API_PASSWORD
Or copy credentials from archive-snapshots config.
"""
import os
import sys
sys.path.insert(0, '/usr/local/CyberCP')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CyberCP.settings')
import django
django.setup()

from contaboAutoSnapshot.utils import get_contabo_api

def main():
    try:
        api = get_contabo_api()
        result = api.test_connection()
        if result.get('success'):
            print("OK:", result.get('message'))
            print("Plan max snapshots:", result.get('plan_max_snapshots'))
        else:
            print("FAIL:", result.get('message'))
            sys.exit(1)
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == '__main__':
    main()
