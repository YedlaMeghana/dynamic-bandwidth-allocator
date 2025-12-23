# Troubleshooting Guide - Common Issues and Solutions

## 🎯 Goal of This Guide
Fix common problems you'll encounter while setting up and running the SDN bandwidth allocator.

---

## 🆘 General Debugging Strategy

When something doesn't work:

1. **Don't panic** - Most issues have simple solutions
2. **Read error messages carefully** - They usually tell you what's wrong
3. **Check one thing at a time** - Systematic debugging
4. **Search the error** - Google is your friend
5. **Ask for help** - After trying basic fixes

---

## 🔧 Installation Issues

### Issue 1: "pip: command not found"

**Error**:
```bash
$ pip install ryu
bash: pip: command not found
```

**Cause**: pip not installed or not in PATH

**Solution**:
```bash
# Install pip
sudo apt install python3-pip -y

# Try again with pip3
pip3 install ryu

# Or use python3 -m pip
python3 -m pip install ryu
```

**Verification**:
```bash
pip3 --version
# Should show: pip X.X.X from /usr/...
```

---

### Issue 2: "Mininet command not found"

**Error**:
```bash
$ sudo mn --test pingall
sudo: mn: command not found
```

**Cause**: Mininet not installed

**Solution**:
```bash
# Install Mininet
sudo apt update
sudo apt install mininet -y

# Verify
sudo mn --version
```

**If still not working**:
```bash
# Install from source
cd /tmp
git clone https://github.com/mininet/mininet
cd mininet
sudo ./util/install.sh -a
```

---

### Issue 3: "Permission denied" errors

**Error**:
```bash
$ mn --test pingall
Error: Permission denied
```

**Cause**: Mininet needs root privileges

**Solution**:
```bash
# Always use sudo with Mininet commands
sudo mn --test pingall

# For custom topologies
sudo mn --custom topo.py --topo mytopo
```

---

### Issue 4: "Ryu module not found"

**Error**:
```bash
$ ryu-manager controller.py
ModuleNotFoundError: No module named 'ryu'
```

**Cause**: Ryu installed for different Python version

**Solution**:
```bash
# Check Python version
python3 --version

# Install Ryu for correct version
sudo pip3 install ryu

# Or use specific Python version
sudo python3.8 -m pip install ryu

# Try running with python3 explicitly
python3 -m ryu.cmd.manager controller.py
```

---

## 🌐 Mininet Issues

### Issue 5: "Cannot connect to X server"

**Error**:
```bash
$ sudo mn
Error: Cannot connect to X server
xterm: Xt error: Can't open display
```

**Cause**: Running on headless server (no GUI)

**Solution**:
```bash
# This is actually OK! You don't need GUI
# Just ignore xterm warnings

# Or disable xterm
sudo mn --test pingall

# In scripts, use CLI instead of xterm
from mininet.cli import CLI
CLI(net)
```

---

### Issue 6: "Address already in use"

**Error**:
```bash
$ sudo mn --controller remote
Error: Address already in use
```

**Cause**: Previous Mininet instance still running

**Solution**:
```bash
# Clean up old instances
sudo mn -c

# Kill any remaining processes
sudo killall -9 controller
sudo killall -9 ovs-vswitchd
sudo killall -9 ovsdb-server

# Try again
sudo mn --controller remote
```

---

### Issue 7: "pingall fails with 100% packet loss"

**Error**:
```bash
mininet> pingall
*** Results: 100% dropped (0/X received)
```

**Cause**: Controller not running or not connected

**Solution**:

**Step 1: Check if controller is running**
```bash
# In another terminal
ps aux | grep ryu
# Should see ryu-manager process
```

**Step 2: Start controller if not running**
```bash
ryu-manager controller/group_bandwidth.py &
# Wait 2-3 seconds for it to start
```

**Step 3: Check switch-controller connection**
```bash
sudo ovs-vsctl show
# Look for "is_connected: true"
```

**Step 4: Check OpenFlow connection**
```bash
sudo ovs-ofctl -O OpenFlow13 show s1
# Should show connection to 127.0.0.1:6653
```

**If still failing**:
```bash
# Restart everything
sudo mn -c
ryu-manager controller/group_bandwidth.py &
sleep 3
sudo mn --custom campus_topo.py --topo campustopo --controller remote
```

---

### Issue 8: "Unknown topo type"

**Error**:
```bash
$ sudo mn --custom campus_topo.py --topo campustopo
Error: Unknown topo type: campustopo
```

**Cause**: Topology not exported correctly

**Solution**:

**Check your topology file has**:
```python
# At the END of campus_topo.py
topos = {'campustopo': (lambda: CampusTopo())}
```

**Verify file syntax**:
```bash
python3 campus_topo.py
# Should not show errors
```

**Try with absolute path**:
```bash
sudo mn --custom /full/path/to/campus_topo.py --topo campustopo
```

---

## 🎮 Ryu Controller Issues

### Issue 9: "Controller not receiving packets"

**Symptom**: Controller starts but no PACKET_IN events

**Debug**:

**Step 1: Check controller is listening**
```bash
# Should see controller running
ps aux | grep ryu

# Check it's listening on port 6653
sudo netstat -tlnp | grep 6653
```

**Step 2: Check switch connected**
```bash
sudo ovs-vsctl show
# Look for "is_connected: true"

# Check OpenFlow version
sudo ovs-vsctl get bridge s1 protocols
# Should include OpenFlow13
```

**Step 3: Check table-miss rule**
```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
# Should see a rule with priority=0
# Action should be CONTROLLER
```

**Solution**:

Add explicit table-miss flow:
```python
# In your controller
def install_table_miss(self, datapath):
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto
    match = parser.OFPMatch()
    actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                      ofproto.OFPCML_NO_BUFFER)]
    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
    mod = parser.OFPFlowMod(datapath=datapath, priority=0, 
                           match=match, instructions=inst)
    datapath.send_msg(mod)
```

---

### Issue 10: "OpenFlow version mismatch"

**Error**:
```bash
ryu-manager: OpenFlow version mismatch
```

**Cause**: Switch and controller using different OpenFlow versions

**Solution**:

**In controller (group_bandwidth.py)**:
```python
class DynamicBWAllocator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]  # Force OpenFlow 1.3
```

**When starting Mininet**:
```bash
sudo mn --custom campus_topo.py --topo campustopo \
        --controller remote \
        --switch ovs,protocols=OpenFlow13  # Force OpenFlow13
```

**Verify**:
```bash
sudo ovs-vsctl get bridge s1 protocols
# Should show: ["OpenFlow13"]
```

---

### Issue 11: "Stats not being collected"

**Symptom**: Dashboard shows 0 for all groups

**Debug**:

**Step 1: Check stats file**
```bash
cat /tmp/group_stats.json
# Should exist and contain numbers
```

**Step 2: Check if stats file is updating**
```bash
# Watch for changes
watch -n 1 cat /tmp/group_stats.json
# Should update every 2-5 seconds
```

**Step 3: Check controller logs**
```bash
# Look for stats_reply messages in controller output
# Should see FlowStatsReply events
```

**Solution**:

**Ensure monitor thread is running**:
```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.monitor_thread = hub.spawn(self._monitor)  # IMPORTANT!

def _monitor(self):
    while True:
        for dp in self.datapaths.values():
            self.request_stats(dp)
        hub.sleep(5)  # Every 5 seconds
```

**Ensure stats handler writes to file**:
```python
@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
def flow_stats_reply_handler(self, ev):
    # ... calculate stats ...
    
    # WRITE TO FILE
    with open('/tmp/group_stats.json', 'w') as f:
        json.dump(self.flow_stats, f)
```

---

## 🚦 QoS and Bandwidth Issues

### Issue 12: "Bandwidth not being limited"

**Symptom**: Student gets 50 Mbps instead of 5 Mbps

**Debug**:

**Step 1: Check if QoS queues exist**
```bash
sudo ovs-vsctl list qos
# Should show queue configurations

sudo ovs-vsctl list queue
# Should show queue 1, 2, 3 with rate limits
```

**Step 2: Check if flows use queues**
```bash
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
# Look for "set_queue:X" in actions
```

**Step 3: Check queue statistics**
```bash
sudo ovs-ofctl -O OpenFlow13 queue-stats s1
# Should show tx_packets and tx_bytes for each queue
```

**Solution**:

**If queues don't exist, create them**:
```bash
# Run QoS setup script
cd mininet
sudo bash qos_setup.sh
```

**Ensure flows have set_queue action**:
```python
def install_qos_rule(self, datapath, ip, queue_id):
    parser = datapath.ofproto_parser
    ofproto = datapath.ofproto
    
    match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip)
    actions = [
        parser.OFPActionSetQueue(queue_id),  # SET QUEUE!
        parser.OFPActionOutput(ofproto.OFPP_NORMAL)
    ]
    # ... rest of flow mod ...
```

---

### Issue 13: "Faculty not getting guaranteed bandwidth"

**Symptom**: Faculty only gets 10 Mbps when network is busy

**Debug**:

**Check queue configuration**:
```bash
sudo ovs-vsctl list queue
# Queue 1 (faculty) should have:
# min-rate: 40000000 (40 Mbps)
```

**Check if HTB qdisc is configured**:
```bash
# Get switch interface
IFACE=$(sudo ovs-vsctl list-ports s1 | head -1)
sudo tc -s qdisc show dev $IFACE
# Should show HTB with rate limits
```

**Solution**:

**Recreate TC queues with guarantees**:
```bash
#!/bin/bash
# qos_setup.sh

IFACE=$(sudo ovs-vsctl list-ports s1 | head -1)

# Remove old qdisc
sudo tc qdisc del dev $IFACE root 2>/dev/null

# Create HTB qdisc
sudo tc qdisc add dev $IFACE root handle 1: htb default 30

# Faculty: 40 Mbps guaranteed, 100 Mbps ceiling
sudo tc class add dev $IFACE parent 1: classid 1:1 htb \
    rate 40mbit ceil 100mbit

# Lab: 30 Mbps guaranteed, 80 Mbps ceiling
sudo tc class add dev $IFACE parent 1: classid 1:2 htb \
    rate 30mbit ceil 80mbit

# Student: 5 Mbps guaranteed, 50 Mbps ceiling
sudo tc class add dev $IFACE parent 1: classid 1:3 htb \
    rate 5mbit ceil 50mbit
```

---

## 🌐 Dashboard Issues

### Issue 14: "Dashboard not loading (localhost:5000)"

**Error**:
```bash
# In browser
Unable to connect to localhost:5000
```

**Debug**:

**Step 1: Check if Flask is running**
```bash
ps aux | grep "python.*app.py"
# Should see Flask process
```

**Step 2: Check if port 5000 is listening**
```bash
sudo netstat -tlnp | grep 5000
# Should show Python listening on 0.0.0.0:5000 or 127.0.0.1:5000
```

**Step 3: Check Flask logs**
```bash
# Look at terminal where you started Flask
# Should see:
# * Running on http://127.0.0.1:5000/
# * Running on http://0.0.0.0:5000/
```

**Solution**:

**Start Flask correctly**:
```bash
cd dashboard
python3 app.py

# Or with explicit host
python3 app.py --host=0.0.0.0 --port=5000
```

**If port in use**:
```bash
# Kill process using port 5000
sudo lsof -ti:5000 | xargs kill -9

# Or use different port
python3 app.py --port=5001
```

---

### Issue 15: "Dashboard shows all zeros"

**Symptom**: Chart displays but all values are 0

**Debug**:

**Step 1: Check stats file exists**
```bash
ls -l /tmp/group_stats.json
cat /tmp/group_stats.json
```

**Step 2: Check if controller is writing stats**
```bash
# Generate traffic in Mininet
mininet> h1 ping -c 10 h2

# Check if stats file updated
watch -n 1 cat /tmp/group_stats.json
```

**Step 3: Check dashboard can read file**
```bash
# Check permissions
ls -l /tmp/group_stats.json
# Should be readable: -rw-r--r--

# Test reading
python3 -c "import json; print(json.load(open('/tmp/group_stats.json')))"
```

**Solution**:

**Ensure controller writes stats**:
```python
@set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
def flow_stats_reply_handler(self, ev):
    # ... process stats ...
    
    # WRITE TO FILE
    import json
    STATS_FILE = '/tmp/group_stats.json'
    with open(STATS_FILE, 'w') as f:
        json.dump(self.flow_stats, f)
```

**Ensure dashboard reads correctly**:
```python
@app.route('/api/group_stats')
def group_stats():
    stats_file = '/tmp/group_stats.json'
    if os.path.exists(stats_file):
        with open(stats_file) as f:
            stats = json.load(f)
    else:
        stats = {'faculty': 0, 'lab': 0, 'student': 0}
    
    # Convert bytes to Mbps
    for k in stats:
        stats[k] = round(stats[k] * 8 / 1_000_000, 2)
    
    return jsonify(stats)
```

---

### Issue 16: "Chart not updating in real-time"

**Symptom**: Dashboard loads but chart doesn't refresh

**Debug**:

**Step 1: Check browser console**
```
Press F12 in browser → Console tab
Look for JavaScript errors
```

**Step 2: Check if API endpoint works**
```bash
# In browser or terminal
curl http://localhost:5000/api/group_stats
# Should return JSON like:
# {"faculty": 35.2, "lab": 28.5, "student": 10.3}
```

**Step 3: Check Chart.js loaded**
```
In browser console:
typeof Chart
# Should show "function", not "undefined"
```

**Solution**:

**Fix JavaScript in index.html**:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
<script>
    function updateChart() {
        fetch('/api/group_stats')
            .then(r => r.json())
            .then(data => {
                bwChart.data.datasets[0].data = [
                    data.faculty, data.lab, data.student
                ];
                bwChart.update();
            })
            .catch(err => console.error('Error:', err));
    }
    
    // Update every 2 seconds
    setInterval(updateChart, 2000);
    updateChart();  // Initial update
</script>
```

---

## 🐛 Traffic Generation Issues

### Issue 17: "iperf: connection refused"

**Error**:
```bash
mininet> h1 iperf -c 10.0.0.2
connect failed: Connection refused
```

**Cause**: iperf server not running on target host

**Solution**:

**Start iperf server first**:
```bash
# On server host
mininet> h2 iperf -s -p 5001 &

# Then run client
mininet> h1 iperf -c 10.0.0.2 -p 5001 -t 30
```

**Check if server is running**:
```bash
mininet> h2 ps aux | grep iperf
# Should see "iperf -s"
```

---

### Issue 18: "iperf shows very low bandwidth"

**Symptom**: iperf reports 0.5 Mbps when you expect 40 Mbps

**Debug**:

**Step 1: Check basic connectivity**
```bash
mininet> h1 ping -c 4 h2
# Should have 0% packet loss
```

**Step 2: Check CPU load**
```bash
top
# If CPU is 100%, system might be overloaded
```

**Step 3: Check if QoS is too restrictive**
```bash
# Check queue config
sudo ovs-vsctl list queue
```

**Solution**:

**Try UDP instead of TCP**:
```bash
# UDP test (doesn't need as much CPU)
mininet> h2 iperf -s -u -p 5001 &
mininet> h1 iperf -c 10.0.0.2 -u -p 5001 -b 50M -t 10
```

**Increase iperf buffer**:
```bash
mininet> h1 iperf -c 10.0.0.2 -w 256K
```

---

## 🔍 General Debugging Tips

### Enable Debug Logging

**Controller**:
```bash
# Run with verbose output
ryu-manager --verbose controller/group_bandwidth.py
```

**Mininet**:
```bash
# Run with debug output
sudo mn --custom campus_topo.py --topo campustopo --controller remote -v debug
```

**OpenFlow messages**:
```bash
# Capture OpenFlow packets
sudo tcpdump -i lo -n port 6653 -w of.pcap

# View in Wireshark
wireshark of.pcap
```

---

### Check System Resources

```bash
# Check memory
free -h

# Check disk space
df -h

# Check CPU
top

# Check network interfaces
ip addr show
```

---

### Clean Slate Restart

When everything is broken:

```bash
# 1. Stop everything
sudo mn -c
sudo killall ryu-manager
sudo killall python3
sudo pkill -f flask

# 2. Clean Open vSwitch
sudo /etc/init.d/openvswitch-switch restart
# or
sudo systemctl restart openvswitch-switch

# 3. Remove old data
rm -f /tmp/group_stats.json

# 4. Start fresh
cd /path/to/project
bash mininet/run_simulation.sh
cd dashboard && python3 app.py
```

---

## 📚 Where to Get Help

### Online Resources
1. **Mininet**: http://mininet.org/
2. **Ryu**: https://ryu.readthedocs.io/
3. **OpenFlow**: https://www.opennetworking.org/
4. **Stack Overflow**: Search "mininet [your error]"

### Useful Commands for Support Requests

When asking for help, provide:

```bash
# System info
uname -a
lsb_release -a

# Software versions
sudo mn --version
ryu-manager --version
python3 --version

# Current state
ps aux | grep -E "(ryu|mininet|ovs)"
sudo ovs-vsctl show
sudo ovs-ofctl dump-flows s1

# Logs
# Copy relevant error messages
```

---

## 🎯 Quick Reference - Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| "Command not found" | Install package with apt or pip |
| "Permission denied" | Use sudo |
| "Address in use" | sudo mn -c |
| "Connection refused" | Check if service is running |
| "Module not found" | pip3 install <module> |
| All flows disappear | Check idle_timeout and hard_timeout |
| No ping connectivity | Check controller running |
| Bandwidth not limited | Check QoS queues configured |
| Dashboard shows zeros | Check /tmp/group_stats.json |
| Chart not updating | Check browser console for errors |

---

## 💡 Prevention Tips

1. **Always cleanup**: Run `sudo mn -c` between tests
2. **Check before running**: Verify controller is up before starting Mininet
3. **Save your work**: Commit code changes to git
4. **Document changes**: Comment your code
5. **Test incrementally**: Don't change everything at once

**Remember**: Debugging is a skill. The more you practice, the faster you'll fix issues! 🔧
