#!/bin/bash
#
# Setup Verification Script
# Verifies that all components are correctly installed
#

echo "========================================="
echo "SDN Environment Verification"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASSED=0
FAILED=0

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
        ((PASSED++))
    else
        echo -e "${RED}✗${NC} $1"
        ((FAILED++))
    fi
}

info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# 1. Python3
echo "1. Python3 version:"
python3 --version 2>/dev/null
check "Python 3 installed"
echo ""

# 2. pip3
echo "2. pip3 version:"
pip3 --version 2>/dev/null
check "pip3 installed"
echo ""

# 3. Mininet
echo "3. Mininet version:"
sudo mn --version 2>/dev/null
check "Mininet installed"
echo ""

# 4. Open vSwitch
echo "4. Open vSwitch version:"
sudo ovs-vsctl --version 2>/dev/null
check "Open vSwitch installed"
echo ""

# 5. Ryu
echo "5. Ryu version:"
ryu-manager --version 2>/dev/null
check "Ryu controller installed"
echo ""

# 6. Flask
echo "6. Flask module:"
python3 -c "import flask; print(f'Flask {flask.__version__}')" 2>/dev/null
check "Flask installed"
echo ""

# 7. iperf
echo "7. iperf version:"
iperf --version 2>/dev/null | head -1
check "iperf installed"
echo ""

# 8. Python modules
echo "8. Python modules:"
python3 -c "import ryu" 2>/dev/null && echo "  - ryu: OK" || echo "  - ryu: MISSING"
python3 -c "import flask" 2>/dev/null && echo "  - flask: OK" || echo "  - flask: MISSING"
python3 -c "import mininet" 2>/dev/null && echo "  - mininet: OK" || echo "  - mininet: MISSING"
python3 -c "import schedule" 2>/dev/null && echo "  - schedule: OK" || echo "  - schedule: MISSING"

python3 -c "import ryu, flask, mininet, schedule" 2>/dev/null
check "All Python modules installed"
echo ""

# 9. OVS Service
echo "9. OVS Service:"
if systemctl is-active --quiet openvswitch-switch 2>/dev/null || pgrep ovs-vswitchd > /dev/null; then
    echo -e "${GREEN}✓${NC} Open vSwitch service is running"
    ((PASSED++))
else
    echo -e "${RED}✗${NC} Open vSwitch service is NOT running"
    echo "  Start with: sudo systemctl start openvswitch-switch"
    ((FAILED++))
fi
echo ""

# 10. Project files
echo "10. Project files:"
[ -f "controller/group_bandwidth.py" ] && echo "  - controller/group_bandwidth.py: OK" || echo "  - controller/group_bandwidth.py: MISSING"
[ -f "controller/exam_scheduler.py" ] && echo "  - controller/exam_scheduler.py: OK" || echo "  - controller/exam_scheduler.py: MISSING"
[ -f "mininet/campus_topo.py" ] && echo "  - mininet/campus_topo.py: OK" || echo "  - mininet/campus_topo.py: MISSING"
[ -f "mininet/qos_setup.sh" ] && echo "  - mininet/qos_setup.sh: OK" || echo "  - mininet/qos_setup.sh: MISSING"
[ -f "dashboard/app.py" ] && echo "  - dashboard/app.py: OK" || echo "  - dashboard/app.py: MISSING"
[ -f "requirements.txt" ] && echo "  - requirements.txt: OK" || echo "  - requirements.txt: MISSING"

if [ -f "controller/group_bandwidth.py" ] && [ -f "controller/exam_scheduler.py" ] && \
   [ -f "mininet/campus_topo.py" ] && [ -f "dashboard/app.py" ]; then
    check "All project files present"
else
    fail_test "Some project files are missing"
fi
echo ""

# Summary
echo "========================================="
echo "Verification Summary"
echo "========================================="
echo "Checks passed: $PASSED"
echo "Checks failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! You're ready to run the project.${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Read SDN_BASICS.md to understand concepts"
    echo "  2. Read ARCHITECTURE.md to understand structure"
    echo "  3. Run: cd mininet && sudo bash run_simulation.sh"
    echo "  4. In another terminal: cd dashboard && python3 app.py"
    echo "  5. Open browser: http://localhost:5000"
    exit 0
else
    echo -e "${RED}✗ Some checks failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  - Install missing packages: pip3 install -r requirements.txt"
    echo "  - Install Mininet: sudo apt install mininet"
    echo "  - Install OVS: sudo apt install openvswitch-switch"
    echo "  - Start OVS: sudo systemctl start openvswitch-switch"
    exit 1
fi
