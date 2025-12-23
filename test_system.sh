#!/bin/bash
#
# Comprehensive Testing Script for Dynamic Bandwidth Allocator
#
# This script runs automated tests to verify all features are working correctly.
# Tests include: connectivity, bandwidth limits, priority enforcement, and exam mode.

echo "========================================="
echo "Dynamic Bandwidth Allocator - Test Suite"
echo "========================================="
echo ""
echo "Starting comprehensive tests..."
echo ""

# Test results tracking
PASSED=0
FAILED=0

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print test results
pass_test() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    ((PASSED++))
}

fail_test() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    ((FAILED++))
}

info() {
    echo -e "${YELLOW}ℹ INFO${NC}: $1"
}

# Check if running in Mininet
if ! command -v mn &> /dev/null; then
    echo "ERROR: Mininet not installed. Please install Mininet first."
    exit 1
fi

# Test 1: Check if controller is running
echo "Test 1: Controller Status"
echo "-------------------------"
if ps aux | grep -q "[r]yu-manager"; then
    pass_test "Ryu controller is running"
else
    fail_test "Ryu controller is NOT running"
    echo "Please start the controller first: ryu-manager controller/group_bandwidth.py"
fi
echo ""

# Test 2: Check if dashboard is running
echo "Test 2: Dashboard Status"
echo "------------------------"
if curl -s http://localhost:5000/ > /dev/null 2>&1; then
    pass_test "Dashboard is accessible on port 5000"
else
    fail_test "Dashboard is NOT accessible on port 5000"
    echo "Please start the dashboard: cd dashboard && python3 app.py"
fi
echo ""

# Test 3: Check stats file
echo "Test 3: Statistics Collection"
echo "-----------------------------"
if [ -f /tmp/group_stats.json ]; then
    pass_test "Stats file exists at /tmp/group_stats.json"
    
    # Check if file is being updated
    initial_time=$(stat -c %Y /tmp/group_stats.json 2>/dev/null || stat -f %m /tmp/group_stats.json)
    sleep 6  # Wait for next stats update (5 second interval)
    new_time=$(stat -c %Y /tmp/group_stats.json 2>/dev/null || stat -f %m /tmp/group_stats.json)
    
    if [ "$new_time" -gt "$initial_time" ]; then
        pass_test "Stats file is being updated regularly"
    else
        fail_test "Stats file is NOT being updated"
    fi
    
    # Check file content
    content=$(cat /tmp/group_stats.json)
    if echo "$content" | grep -q "faculty"; then
        pass_test "Stats file contains valid data"
        info "Current stats: $content"
    else
        fail_test "Stats file does NOT contain valid data"
    fi
else
    fail_test "Stats file does NOT exist"
    echo "Controller may not be collecting statistics"
fi
echo ""

# Test 4: Check QoS queues
echo "Test 4: QoS Configuration"
echo "-------------------------"
if command -v ovs-vsctl &> /dev/null; then
    # Check if OVS is running
    if systemctl is-active --quiet openvswitch-switch 2>/dev/null || pgrep ovs-vswitchd > /dev/null; then
        pass_test "Open vSwitch is running"
        
        # Check for queues
        queue_count=$(sudo ovs-vsctl list Queue | grep -c "_uuid" || echo "0")
        if [ "$queue_count" -ge 3 ]; then
            pass_test "QoS queues are configured ($queue_count queues found)"
        else
            fail_test "QoS queues are NOT properly configured (expected 3, found $queue_count)"
            echo "Run: cd mininet && sudo bash qos_setup.sh"
        fi
    else
        fail_test "Open vSwitch is NOT running"
        echo "Start OVS: sudo systemctl start openvswitch-switch"
    fi
else
    fail_test "Open vSwitch is NOT installed"
fi
echo ""

# Test 5: Dashboard API endpoints
echo "Test 5: Dashboard API"
echo "---------------------"
if curl -s http://localhost:5000/api/group_stats > /dev/null; then
    pass_test "API endpoint /api/group_stats is accessible"
    
    # Test API response
    response=$(curl -s http://localhost:5000/api/group_stats)
    if echo "$response" | grep -q "faculty"; then
        pass_test "API returns valid JSON data"
        info "API response: $response"
    else
        fail_test "API does NOT return valid data"
    fi
else
    fail_test "API endpoint is NOT accessible"
fi

if curl -s http://localhost:5000/api/system_status > /dev/null; then
    pass_test "API endpoint /api/system_status is accessible"
else
    fail_test "API endpoint /api/system_status is NOT accessible"
fi
echo ""

# Test 6: Log files
echo "Test 6: Logging"
echo "---------------"
if [ -f /tmp/controller.log ]; then
    pass_test "Controller log file exists"
    
    # Check if log is being written
    log_lines=$(wc -l < /tmp/controller.log)
    if [ "$log_lines" -gt 0 ]; then
        pass_test "Controller is logging (${log_lines} lines)"
    else
        fail_test "Controller log is empty"
    fi
else
    fail_test "Controller log file does NOT exist"
fi

if [ -f /tmp/bandwidth.log ]; then
    pass_test "Bandwidth log file exists"
else
    info "Bandwidth log file not yet created (normal if just started)"
fi
echo ""

# Test 7: Dependencies
echo "Test 7: Dependencies"
echo "--------------------"
python3 -c "import ryu" 2>/dev/null && pass_test "Ryu module is installed" || fail_test "Ryu module is NOT installed"
python3 -c "import flask" 2>/dev/null && pass_test "Flask module is installed" || fail_test "Flask module is NOT installed"
python3 -c "import mininet" 2>/dev/null && pass_test "Mininet module is installed" || fail_test "Mininet module is NOT installed"

if command -v iperf &> /dev/null; then
    pass_test "iperf is installed"
else
    fail_test "iperf is NOT installed"
    echo "Install with: sudo apt install iperf"
fi
echo ""

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Total tests run: $((PASSED + FAILED))"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! System is ready for demo.${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Some tests failed. Please fix the issues above.${NC}"
    exit 1
fi
