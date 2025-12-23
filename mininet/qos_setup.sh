#!/bin/bash
#
# QoS Setup Script for Dynamic Bandwidth Allocator
# 
# This script configures Traffic Control (TC) queues on Open vSwitch
# to implement Quality of Service (bandwidth limiting and guarantees)
#
# Queue Configuration:
# - Queue 1 (Faculty): 40 Mbps guaranteed, 100 Mbps max
# - Queue 2 (Lab):     30 Mbps guaranteed, 80 Mbps max  
# - Queue 3 (Student):  5 Mbps guaranteed, 50 Mbps max

echo "========================================="
echo "QoS Setup for Dynamic Bandwidth Allocator"
echo "========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if OVS is running
if ! systemctl is-active --quiet openvswitch-switch; then
    echo "ERROR: Open vSwitch is not running"
    echo "Start it with: sudo systemctl start openvswitch-switch"
    exit 1
fi

# Get switch name (default: s1)
SWITCH=${1:-s1}

echo "Configuring QoS on switch: $SWITCH"
echo ""

# Check if switch exists
if ! ovs-vsctl br-exists $SWITCH 2>/dev/null; then
    echo "ERROR: Switch $SWITCH does not exist"
    echo "Available switches:"
    ovs-vsctl list-br
    exit 1
fi

# Get first port of the switch (usually connects to hosts)
PORT=$(ovs-vsctl list-ports $SWITCH | head -1)

if [ -z "$PORT" ]; then
    echo "WARNING: No ports found on switch $SWITCH"
    echo "QoS will be configured but may not be active until hosts connect"
    # Use eth0 as fallback for configuration
    PORT="${SWITCH}-eth1"
fi

echo "Configuring QoS on port: $PORT"
echo ""

# Step 1: Clean up any existing QoS configuration
echo "Step 1: Cleaning up old QoS configuration..."
ovs-vsctl clear Port $PORT qos 2>/dev/null
ovs-vsctl --all destroy QoS 2>/dev/null  
ovs-vsctl --all destroy Queue 2>/dev/null

# Also clean TC qdiscs on interfaces
for iface in $(ovs-vsctl list-ports $SWITCH 2>/dev/null); do
    tc qdisc del dev $iface root 2>/dev/null
done

echo "  ✓ Cleanup complete"
echo ""

# Step 2: Create Queues with bandwidth limits
echo "Step 2: Creating queues..."

# Queue 1: Faculty (40 Mbps min, 100 Mbps max)
QUEUE1=$(ovs-vsctl create Queue other-config:min-rate=40000000 other-config:max-rate=100000000)
echo "  ✓ Queue 1 (Faculty): 40 Mbps min, 100 Mbps max - ID: $QUEUE1"

# Queue 2: Lab (30 Mbps min, 80 Mbps max)
QUEUE2=$(ovs-vsctl create Queue other-config:min-rate=30000000 other-config:max-rate=80000000)
echo "  ✓ Queue 2 (Lab): 30 Mbps min, 80 Mbps max - ID: $QUEUE2"

# Queue 3: Student (5 Mbps min, 50 Mbps max)
QUEUE3=$(ovs-vsctl create Queue other-config:min-rate=5000000 other-config:max-rate=50000000)
echo "  ✓ Queue 3 (Student): 5 Mbps min, 50 Mbps max - ID: $QUEUE3"

echo ""

# Step 3: Create QoS and attach queues
echo "Step 3: Creating QoS policy..."

QOS=$(ovs-vsctl create QoS type=linux-htb \
    other-config:max-rate=1000000000 \
    queues:1=$QUEUE1 \
    queues:2=$QUEUE2 \
    queues:3=$QUEUE3)

echo "  ✓ QoS policy created - ID: $QOS"
echo "  ✓ Max rate: 1000 Mbps (1 Gbps)"
echo ""

# Step 4: Attach QoS to port
echo "Step 4: Attaching QoS to port..."
ovs-vsctl set Port $PORT qos=$QOS
echo "  ✓ QoS attached to port: $PORT"
echo ""

# Step 5: Verify configuration
echo "Step 5: Verifying configuration..."
echo ""

echo "QoS Configuration:"
ovs-vsctl list QoS

echo ""
echo "Queue Configuration:"
ovs-vsctl list Queue

echo ""
echo "========================================="
echo "QoS Setup Complete!"
echo "========================================="
echo ""
echo "Summary:"
echo "  • Switch: $SWITCH"
echo "  • Port: $PORT"
echo "  • Queue 1 (Faculty): 40-100 Mbps"
echo "  • Queue 2 (Lab):     30-80 Mbps"
echo "  • Queue 3 (Student):  5-50 Mbps"
echo ""
echo "Queue Usage in Controller:"
echo "  - Faculty traffic → set_queue(1)"
echo "  - Lab traffic     → set_queue(2)"
echo "  - Student traffic → set_queue(3)"
echo ""

# Step 6: Show how to verify queues are working
echo "To verify queues are working:"
echo "  sudo ovs-ofctl -O OpenFlow13 queue-stats $SWITCH"
echo ""
echo "To view QoS statistics:"
echo "  sudo ovs-ofctl -O OpenFlow13 dump-flows $SWITCH"
echo "  (Look for 'set_queue' actions in flow rules)"
echo ""

# Optional: Configure TC on physical interfaces for testing
echo "Additional TC Configuration (Optional):"
echo "Configuring TC qdiscs on switch interfaces..."
echo ""

for iface in $(ovs-vsctl list-ports $SWITCH 2>/dev/null); do
    # Check if interface exists
    if ip link show $iface >/dev/null 2>&1; then
        echo "Configuring TC on $iface..."
        
        # Add HTB qdisc
        tc qdisc add dev $iface root handle 1: htb default 30 2>/dev/null
        
        # Add classes for each group
        tc class add dev $iface parent 1: classid 1:1 htb rate 40mbit ceil 100mbit 2>/dev/null
        tc class add dev $iface parent 1: classid 1:2 htb rate 30mbit ceil 80mbit 2>/dev/null
        tc class add dev $iface parent 1: classid 1:3 htb rate 5mbit ceil 50mbit 2>/dev/null
        
        echo "  ✓ TC configured on $iface"
    fi
done

echo ""
echo "========================================="
echo "Setup complete! Ready for SDN controller."
echo "========================================="

exit 0
