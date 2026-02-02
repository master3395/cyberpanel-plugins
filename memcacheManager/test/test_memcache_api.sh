#!/bin/bash
# Memcache Manager - API Endpoint Tests
# Run with: bash test_memcache_api.sh

set -e

echo "============================================================"
echo "Memcache Manager - API Test Suite"
echo "============================================================"

# Configuration
BASE_URL="${BASE_URL:-https://localhost:8090}"
PLUGIN_URL="${BASE_URL}/plugins/memcacheManager"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

pass() {
    echo -e "  ${GREEN}[PASS]${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "  ${RED}[FAIL]${NC} $1: $2"
    ((FAILED++))
}

warn() {
    echo -e "  ${YELLOW}[WARN]${NC} $1"
}

# Check if curl is available
if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

# Test 1: Check if plugin URL is accessible
echo -e "\n[Testing Plugin Accessibility]"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "${PLUGIN_URL}/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ]; then
    pass "Plugin URL accessible (HTTP $HTTP_CODE)"
else
    fail "Plugin URL" "HTTP $HTTP_CODE (expected 200 or 302)"
fi

# Test 2: Check API endpoints
echo -e "\n[Testing API Endpoints]"
warn "API endpoints require authentication - testing response format only"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "${PLUGIN_URL}/api/stats/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "Stats API endpoint exists (HTTP $HTTP_CODE)"
else
    fail "Stats API" "HTTP $HTTP_CODE"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k -X POST "${PLUGIN_URL}/api/control/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "Control API endpoint exists (HTTP $HTTP_CODE)"
else
    fail "Control API" "HTTP $HTTP_CODE"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k -X POST "${PLUGIN_URL}/api/flush/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "Flush API endpoint exists (HTTP $HTTP_CODE)"
else
    fail "Flush API" "HTTP $HTTP_CODE"
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -k "${PLUGIN_URL}/api/config/" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "302" ] || [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "403" ]; then
    pass "Config API endpoint exists (HTTP $HTTP_CODE)"
else
    fail "Config API" "HTTP $HTTP_CODE"
fi

# Test 3: Direct memcache connection
echo -e "\n[Testing Memcache Connection]"
if command -v nc &> /dev/null; then
    STATS=$(echo "stats" | nc -w 2 127.0.0.1 11211 2>/dev/null || echo "")
    if [ -n "$STATS" ] && echo "$STATS" | grep -q "STAT"; then
        pass "Memcache responding on port 11211"
        VERSION=$(echo "$STATS" | grep "^STAT version" | awk '{print $3}')
        if [ -n "$VERSION" ]; then
            pass "Memcache version: $VERSION"
        fi
    else
        warn "Memcache not responding - service may not be running"
    fi
else
    warn "nc (netcat) not installed - skipping direct connection test"
fi

# Test 4: Check service status
echo -e "\n[Testing Service Status]"
if systemctl is-active --quiet memcached 2>/dev/null; then
    pass "memcached service is active"
elif systemctl is-active --quiet lsmcd 2>/dev/null; then
    pass "lsmcd service is active"
else
    warn "No memcache service appears to be running"
fi

# Summary
echo -e "\n============================================================"
echo "Test Results: $PASSED passed, $FAILED failed"
echo "============================================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
exit 0
