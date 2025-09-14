#!/bin/bash
# Run Ryu controller in background
ryu-manager ../controller/group_bandwidth.py &
sleep 2
# Start Mininet with custom topology
sudo mn --custom campus_topo.py --topo campustopo --controller remote,ip=127.0.0.1 --switch ovs,protocols=OpenFlow13
