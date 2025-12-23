#!/bin/bash
#
# Simulation Startup Script
# Starts Ryu controller and Mininet with custom topology
#

echo "========================================="
echo "Starting Dynamic Bandwidth Allocator"
echo "========================================="
echo ""

# Step 1: Clean up any existing Mininet instances
echo "Step 1: Cleaning up old Mininet instances..."
sudo mn -c
echo "  ✓ Cleanup complete"
echo ""

# Step 2: Start Ryu controller in background
echo "Step 2: Starting Ryu controller..."
cd ..
ryu-manager controller/group_bandwidth.py > /tmp/ryu_output.log 2>&1 &
RYU_PID=$!
echo "  ✓ Controller started (PID: $RYU_PID)"
echo "  ✓ Logs: /tmp/ryu_output.log"
echo "  ✓ Controller logs: /tmp/controller.log"
echo ""

# Wait for controller to start
echo "Waiting for controller to initialize..."
sleep 3
echo ""

# Step 3: Start Mininet with custom topology
echo "Step 3: Starting Mininet network..."
cd mininet
sudo mn --custom campus_topo.py --topo campustopo \
        --controller remote,ip=127.0.0.1 \
        --switch ovs,protocols=OpenFlow13 &
MININET_PID=$!
echo "  ✓ Mininet started (PID: $MININET_PID)"
echo ""

# Wait for Mininet to create switches
echo "Waiting for network to initialize..."
sleep 5
echo ""

# Step 4: Configure QoS queues
echo "Step 4: Configuring QoS queues..."
sudo bash qos_setup.sh s1
echo ""

echo "========================================="
echo "System Started Successfully!"
echo "========================================="
echo ""
echo "Components running:"
echo "  • Ryu Controller (PID: $RYU_PID)"
echo "  • Mininet Network (PID: $MININET_PID)"
echo "  • QoS Queues: Configured"
echo ""
echo "Next steps:"
echo "  1. Start dashboard: cd dashboard && python3 app.py"
echo "  2. Open browser: http://localhost:5000"
echo "  3. Test with iperf (see TESTING_GUIDE.md)"
echo ""
echo "To stop: sudo mn -c && kill $RYU_PID"
echo "========================================="
