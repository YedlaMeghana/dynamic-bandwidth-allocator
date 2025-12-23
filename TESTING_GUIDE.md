# Testing Guide - Bandwidth Allocation Verification

## 🎯 Goal of This Guide
Learn how to test the bandwidth allocation system and verify it's working correctly using measurable results.

---

## 📋 Prerequisites

Before testing:
- ✅ System setup complete (SETUP_GUIDE.md)
- ✅ Understanding of SDN basics (SDN_BASICS.md)
- ✅ Understanding of architecture (ARCHITECTURE.md)
- ✅ Controller and Mininet running

---

## 🧪 Testing Tools

### 1. iperf (Bandwidth Testing)
**What it does**: Measures bandwidth between two hosts

**Two modes**:
- **Server**: Receives traffic (`iperf -s`)
- **Client**: Sends traffic (`iperf -c <server_ip>`)

**Example**:
```bash
# On host1 (server)
iperf -s -p 5001

# On host2 (client)
iperf -c 10.0.0.1 -p 5001 -t 30
# -t 30 means run for 30 seconds
```

### 2. ping (Connectivity Testing)
**What it does**: Verifies hosts can reach each other

```bash
# From student1 to faculty1
mininet> student1 ping -c 4 10.0.1.10
```

### 3. TC (Traffic Control - QoS Verification)
**What it does**: Shows queue statistics

```bash
# Show queues on switch
sudo tc -s qdisc show dev s1-eth1
sudo ovs-ofctl -O OpenFlow13 queue-stats s1
```

---

## 🔬 Test Scenarios

### Test 1: Basic Connectivity
**Goal**: Verify all hosts can communicate

**Steps**:
```bash
# Start Mininet
cd mininet
sudo bash run_simulation.sh

# In Mininet CLI
mininet> pingall
```

**Expected Output**:
```
*** Ping: testing ping reachability
faculty1 -> faculty2 lab1 lab2 ... student1 student2 ...
faculty2 -> faculty1 lab1 lab2 ... student1 student2 ...
...
*** Results: 0% dropped (X/X received)
```

**✅ Success**: 0% packet loss
**❌ Failure**: Any packet loss means connectivity issue

---

### Test 2: Faculty Bandwidth (Guaranteed 40 Mbps)
**Goal**: Verify faculty gets at least 40 Mbps

**Steps**:

1. **Start iperf server on external host**:
```bash
# In new terminal
sudo mn --version  # Just to have mininet context
# Or use a lab host as server
mininet> lab1 iperf -s -p 5001 &
```

2. **Faculty generates traffic**:
```bash
mininet> faculty1 iperf -c 10.0.0.1 -p 5001 -t 30 -i 5
# -i 5 means report every 5 seconds
```

3. **Observe output**:
```
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 5.0 sec   25.0 MBytes  42.0 Mbits/sec
[  3]  5.0-10.0 sec   24.8 MBytes  41.6 Mbits/sec
[  3] 10.0-15.0 sec   25.2 MBytes  42.3 Mbits/sec
```

**Expected**: Bandwidth ~40-50 Mbps (around guaranteed minimum)

**✅ Success**: Bandwidth ≥ 40 Mbps consistently
**❌ Failure**: Bandwidth < 40 Mbps (QoS not working)

---

### Test 3: Student Bandwidth (Limited to 5 Mbps)
**Goal**: Verify students are limited to 5 Mbps

**Steps**:

1. **Start iperf server**:
```bash
mininet> lab1 iperf -s -p 5002 &
```

2. **Student generates traffic**:
```bash
mininet> student1 iperf -c 10.0.0.1 -p 5002 -t 30 -i 5
```

3. **Observe output**:
```
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 5.0 sec   3.12 MBytes  5.23 Mbits/sec
[  3]  5.0-10.0 sec   2.98 MBytes  4.99 Mbits/sec
[  3] 10.0-15.0 sec   3.05 MBytes  5.11 Mbits/sec
```

**Expected**: Bandwidth ~5 Mbps (capped at limit)

**✅ Success**: Bandwidth ≤ 5 Mbps consistently
**❌ Failure**: Bandwidth > 5 Mbps (QoS not enforcing limit)

---

### Test 4: Priority During Congestion
**Goal**: Faculty gets priority when network is busy

**Setup**: Generate traffic from all groups simultaneously

**Steps**:

1. **Start multiple iperf servers**:
```bash
mininet> lab1 iperf -s -p 5001 &
mininet> lab2 iperf -s -p 5002 &
mininet> lab3 iperf -s -p 5003 &
```

2. **Faculty generates traffic**:
```bash
mininet> faculty1 iperf -c 10.0.0.1 -p 5001 -t 60 > /tmp/faculty_result.txt &
```

3. **Lab generates traffic** (same time):
```bash
mininet> lab4 iperf -c 10.0.0.2 -p 5002 -t 60 > /tmp/lab_result.txt &
```

4. **Students generate traffic** (same time):
```bash
mininet> student1 iperf -c 10.0.0.3 -p 5003 -t 60 > /tmp/student_result.txt &
mininet> student2 iperf -c 10.0.0.3 -p 5003 -t 60 &
mininet> student3 iperf -c 10.0.0.3 -p 5003 -t 60 &
```

5. **Wait 60 seconds, then check results**:
```bash
# After test finishes
mininet> sh cat /tmp/faculty_result.txt | tail -1
mininet> sh cat /tmp/lab_result.txt | tail -1
mininet> sh cat /tmp/student_result.txt | tail -1
```

**Expected Results**:
- Faculty: ~40-50 Mbps (maintains bandwidth)
- Lab: ~30-40 Mbps (maintains bandwidth)
- Students: ~5 Mbps each (limited, shares remaining)

**✅ Success**: Priority ordering maintained (Faculty > Lab > Student)
**❌ Failure**: All get similar bandwidth (no prioritization)

---

### Test 5: Dynamic Bandwidth Redistribution
**Goal**: Unused faculty bandwidth goes to students

**Scenario**: Faculty not using bandwidth, students need more

**Steps**:

1. **Faculty idle** (not generating traffic)
```bash
# Don't start faculty traffic
```

2. **Multiple students generate traffic**:
```bash
mininet> lab1 iperf -s -p 5001 &

# 5 students simultaneously
mininet> student1 iperf -c 10.0.0.1 -p 5001 -t 30 > /tmp/s1.txt &
mininet> student2 iperf -c 10.0.0.1 -p 5001 -t 30 > /tmp/s2.txt &
mininet> student3 iperf -c 10.0.0.1 -p 5001 -t 30 > /tmp/s3.txt &
```

3. **Check student bandwidth**:
```bash
# Each student should get more than 5 Mbps
# because faculty's 40 Mbps is unused
```

**Expected**: Students get ~15-20 Mbps each (more than normal 5 Mbps)

**Why?**
- Total available: ~100 Mbps
- Faculty unused: 40 Mbps
- Lab unused: 30 Mbps
- Available for students: 70 Mbps
- Split among 3-5 students: ~15-20 Mbps each

**✅ Success**: Students get > 5 Mbps when faculty idle
**❌ Failure**: Students still limited to 5 Mbps (no redistribution)

---

### Test 6: Exam Mode Bandwidth Shift
**Goal**: During exam, lab gets priority over faculty

**Steps**:

1. **Check normal mode** (before exam):
```bash
# Faculty bandwidth: 40 Mbps
# Lab bandwidth: 30 Mbps
```

2. **Activate exam mode** (via dashboard or config):
```bash
# In dashboard, schedule exam mode
# Or manually:
curl -X POST http://localhost:5000/api/exam_mode \
  -H "Content-Type: application/json" \
  -d '{"active": true}'
```

3. **Test lab bandwidth**:
```bash
mininet> faculty1 iperf -s -p 5001 &
mininet> lab1 iperf -c 10.0.1.10 -p 5001 -t 30 -i 5
```

**Expected in Exam Mode**:
- Lab: ~60 Mbps (increased from 30)
- Faculty: ~20 Mbps (decreased from 40)

**✅ Success**: Lab bandwidth increases in exam mode
**❌ Failure**: No change in bandwidth allocation

---

### Test 7: Dashboard Real-Time Updates
**Goal**: Dashboard shows live bandwidth usage

**Steps**:

1. **Open dashboard**:
```bash
# In browser
http://localhost:5000
```

2. **Generate traffic from different groups**:
```bash
# Faculty traffic
mininet> lab1 iperf -s -p 5001 &
mininet> faculty1 iperf -c 10.0.0.1 -p 5001 -t 60 &

# Wait 5 seconds, start student traffic
mininet> student1 iperf -c 10.0.0.1 -p 5001 -t 60 &
```

3. **Observe dashboard**:
- Chart should update every 2 seconds
- Faculty bar should rise first
- Student bar should rise after 5 seconds
- Real-time update (not static)

**Expected**: Chart dynamically updates with current bandwidth

**✅ Success**: Chart reflects traffic generation in real-time
**❌ Failure**: Chart doesn't update or shows 0

---

## 📊 Interpreting iperf Output

### Understanding the Numbers

```
[ ID] Interval       Transfer     Bandwidth
[  3]  0.0- 5.0 sec   25.0 MBytes  42.0 Mbits/sec
[  3]  5.0-10.0 sec   24.8 MBytes  41.6 Mbits/sec
[  3] 10.0-15.0 sec   25.2 MBytes  42.3 Mbits/sec
[  3]  0.0-30.0 sec   150 MBytes   41.9 Mbits/sec
```

**Columns**:
- **ID**: Connection identifier
- **Interval**: Time window (seconds)
- **Transfer**: Total data sent (MBytes)
- **Bandwidth**: Speed (Mbits/sec)

**What to look for**:
- **Consistent bandwidth**: Similar values each interval = stable QoS
- **Average bandwidth**: Last line shows overall average
- **Ceiling effect**: Bandwidth hitting limit = QoS working

---

## 🧮 Bandwidth Calculations

### Convert Between Units
```
1 Mbps (Megabit per second) = 125 KBps (Kilobyte per second)
1 Gbps = 1000 Mbps
8 Mbps = 1 MBps (Megabyte per second)
```

### Example Calculations

**If iperf shows "40.0 Mbits/sec"**:
- = 40 Mbps
- = 5 MBps (40 ÷ 8)
- = 5,000,000 bytes per second

**If you see "25.0 MBytes in 5.0 sec"**:
- Transfer = 25 MB
- Time = 5 seconds
- Bandwidth = (25 × 8) ÷ 5 = 40 Mbps

---

## 🎯 Complete Test Script

### Automated Test Suite

Create `test_all.sh`:

```bash
#!/bin/bash
# Automated test suite for bandwidth allocation

echo "=== Bandwidth Allocation Test Suite ==="
echo ""

# Test 1: Connectivity
echo "Test 1: Basic Connectivity"
sudo mn -c
echo "  Starting Mininet..."
# Run connectivity test

# Test 2: Faculty bandwidth
echo ""
echo "Test 2: Faculty Bandwidth (Expected: ~40 Mbps)"
# Run faculty iperf test

# Test 3: Student bandwidth
echo ""
echo "Test 3: Student Bandwidth (Expected: ~5 Mbps)"
# Run student iperf test

# Test 4: Priority under congestion
echo ""
echo "Test 4: Priority Test"
# Run concurrent traffic

# Test 5: Redistribution
echo ""
echo "Test 5: Bandwidth Redistribution"
# Test with faculty idle

# Summary
echo ""
echo "=== Test Complete ==="
echo "Check results above for PASS/FAIL"
```

---

## 📸 Collecting Evidence for Demo

### What to Capture

1. **Terminal screenshots**:
```bash
# Take screenshots showing:
- iperf output with bandwidth numbers
- Dashboard with real-time graphs
- Controller logs showing decisions
```

2. **Dashboard screenshots**:
- Normal mode bandwidth
- Exam mode bandwidth
- Real-time graph updates

3. **Logs for report**:
```bash
# Save controller output
ryu-manager controller/group_bandwidth.py > controller.log 2>&1
```

---

## 🎥 Creating Demo Video

### Recording Steps

1. **Show normal operation**:
```bash
# Start system
# Generate traffic
# Show dashboard updating
```

2. **Show priority enforcement**:
```bash
# Faculty gets 40 Mbps
# Student gets 5 Mbps
# Show side-by-side comparison
```

3. **Show exam mode**:
```bash
# Activate exam mode
# Lab bandwidth increases
# Show dashboard change
```

4. **Show redistribution**:
```bash
# Faculty idle
# Students get more bandwidth
# Show dynamic allocation
```

---

## 🔍 Debugging Tests

### Test Failing? Check These

#### No traffic reaching destination
```bash
# Check connectivity first
mininet> pingall

# Check if controller is running
ps aux | grep ryu

# Check switch connection
sudo ovs-ofctl -O OpenFlow13 show s1
```

#### Bandwidth not limited
```bash
# Check if QoS queues exist
sudo ovs-vsctl list qos
sudo ovs-vsctl list queue

# Check if flows have queue actions
sudo ovs-ofctl -O OpenFlow13 dump-flows s1
# Look for "set_queue" actions
```

#### Dashboard not updating
```bash
# Check if stats file exists
cat /tmp/group_stats.json

# Check if controller is writing stats
tail -f /tmp/group_stats.json
# Should update every 5 seconds

# Check dashboard logs
# In dashboard terminal, look for errors
```

#### iperf connection refused
```bash
# Make sure server is running
mininet> lab1 ps aux | grep iperf

# Check if port is correct
# Default iperf port: 5001

# Try different port
mininet> lab1 iperf -s -p 5002 &
mininet> student1 iperf -c 10.0.0.1 -p 5002
```

---

## 📋 Test Results Template

Use this template to record test results:

```
=== Bandwidth Allocation Test Results ===
Date: __________
Tested by: __________

Test 1: Connectivity
Status: [PASS / FAIL]
Notes: _____________________

Test 2: Faculty Bandwidth
Expected: 40 Mbps
Actual: _____ Mbps
Status: [PASS / FAIL]

Test 3: Student Bandwidth
Expected: 5 Mbps
Actual: _____ Mbps
Status: [PASS / FAIL]

Test 4: Priority Under Load
Faculty: _____ Mbps
Lab: _____ Mbps
Student: _____ Mbps
Priority maintained: [YES / NO]
Status: [PASS / FAIL]

Test 5: Bandwidth Redistribution
Student bandwidth when faculty idle: _____ Mbps
Increased from 5 Mbps: [YES / NO]
Status: [PASS / FAIL]

Test 6: Exam Mode
Lab bandwidth in exam mode: _____ Mbps
Increased from 30 Mbps: [YES / NO]
Status: [PASS / FAIL]

Test 7: Dashboard Updates
Real-time updates: [YES / NO]
Update frequency: _____ seconds
Status: [PASS / FAIL]

=== Overall: ___ / 7 Tests Passed ===
```

---

## 🎓 What Your Evaluator Will Check

During final demo, they will verify:

1. **Basic functionality**: Can generate and measure traffic
2. **QoS enforcement**: Limits and guarantees working
3. **Priority**: Faculty > Lab > Student
4. **Dynamic allocation**: Redistribution working
5. **Exam mode**: Schedule-based priority change
6. **Dashboard**: Real-time visualization
7. **Understanding**: Can you explain the results?

---

## 📚 Next Steps

After testing:
1. ✅ Record all test results
2. ✅ Take screenshots for report
3. → Read `DEMO_GUIDE.md` for presentation prep
4. → Read `VIVA_QUESTIONS.md` for Q&A prep
5. → Read `TROUBLESHOOTING.md` if issues found

---

## 💡 Tips for Successful Testing

1. **Clean environment**: Run `sudo mn -c` before each test
2. **Wait for stabilization**: Let traffic run 10-15 seconds
3. **Multiple runs**: Test 3 times, take average
4. **Document everything**: Screenshots, logs, results
5. **Understand output**: Don't just run commands blindly

**Remember**: Testing proves your project works! Good results = good grade 🎓
