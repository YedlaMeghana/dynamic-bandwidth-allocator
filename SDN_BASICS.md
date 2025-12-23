# SDN Basics - Explained in Simple Terms

## 🎯 Goal of This Document
Understand what SDN is, why we use it, and how it works - explained like you're learning for the first time.

---

## 🤔 What is SDN (Software-Defined Networking)?

### Traditional Networking (Without SDN)

Imagine your college has many Wi-Fi routers. Each router:
- Makes its own decisions ("Should I forward this packet?")
- Has its own configuration
- Cannot coordinate with other routers easily
- Needs manual configuration per device

**Problem**: 
- Hard to manage many devices
- Cannot make smart decisions across the network
- No central control
- Difficult to implement new features

### SDN Networking (The Better Way!)

With SDN:
- **One central brain (Controller)** makes all decisions
- **Switches** just forward packets as told by the controller
- **Programmable** - write code to control the network
- **Dynamic** - adjust behavior in real-time

**Analogy**: 
- **Traditional**: Each car (router) decides its own route
- **SDN**: GPS system (controller) guides all cars optimally

---

## 🏗️ SDN Architecture - The Three Layers

```
┌─────────────────────────────────────────┐
│     APPLICATION LAYER (Your Code)      │  ← You write Python code here
│  (Bandwidth Allocator, Firewall, etc.) │
└─────────────────────────────────────────┘
                  ↕️ 
         (Northbound API)
                  ↕️
┌─────────────────────────────────────────┐
│      CONTROL LAYER (SDN Controller)     │  ← Ryu Controller runs here
│           (Ryu, ONOS, ODL)              │
└─────────────────────────────────────────┘
                  ↕️
         (Southbound API - OpenFlow)
                  ↕️
┌─────────────────────────────────────────┐
│   DATA LAYER (Network Switches/Routers) │  ← Mininet creates virtual switches
│         (OVS, Physical switches)        │
└─────────────────────────────────────────┘
```

### 1. Application Layer (Your Python Code)
**What it does**: Business logic for network behavior

**Example in our project**:
- "Faculty should get more bandwidth than students"
- "During exam time, prioritize lab computers"
- "If someone uses too much bandwidth, limit them"

**Code Location**: `controller/group_bandwidth.py`

### 2. Control Layer (Ryu Controller)
**What it does**: Translates your application logic into network rules

**Example**:
- Receives: "Give faculty 40 Mbps"
- Does: Installs OpenFlow rules in switches to enforce this
- Monitors: Collects statistics from switches

**Technology**: Ryu (Python-based SDN controller)

### 3. Data Layer (OVS Switches)
**What it does**: Forwards packets based on controller instructions

**Example**:
- Receives packet from student's laptop
- Asks controller: "What should I do?"
- Controller says: "Forward to port 3 with rate limit"
- Switch obeys

**Technology**: Open vSwitch (OVS) in Mininet

---

## 🔄 How SDN Works - Step by Step

### Scenario: Student Opens YouTube

**Step 1: Packet Arrives**
```
Student's laptop (10.0.2.1) sends packet to YouTube (172.217.x.x)
```

**Step 2: Switch Doesn't Know What To Do**
```
OVS Switch: "I've never seen traffic from 10.0.2.1 before"
OVS Switch: "Let me ask the controller..."
```

**Step 3: Packet Sent to Controller**
```
Switch → Controller: "I have a packet from 10.0.2.1, what should I do?"
                     (This is called PACKET_IN message)
```

**Step 4: Controller Analyzes**
```python
# In your Python code (controller/group_bandwidth.py)
def packet_in_handler(packet):
    src_ip = packet.src  # "10.0.2.1"
    
    # Classify: Is this faculty, lab, or student?
    if src_ip in STUDENT_IPS:
        group = "student"
        bandwidth_limit = 5  # Mbps
    
    # Install rule in switch
    install_flow(src_ip, bandwidth_limit)
```

**Step 5: Controller Installs Rule**
```
Controller → Switch: "For packets from 10.0.2.1:"
                     "- Forward to internet port"
                     "- Limit bandwidth to 5 Mbps"
                     "- Keep this rule for 60 seconds"
                     (This is called FLOW_MOD message)
```

**Step 6: Switch Follows Orders**
```
Switch: "Got it! Rule installed."
Switch: "All future packets from 10.0.2.1 will follow this rule"
Switch: "No need to ask controller again (for 60 seconds)"
```

**Step 7: Statistics**
```
Switch → Controller: "In last 5 seconds:"
                     "- Faculty used 35 Mbps"
                     "- Lab used 28 Mbps"  
                     "- Students used 45 Mbps"
                     (This is called STATS_REPLY message)
```

**Step 8: Controller Adjusts**
```python
# Controller analyzes stats
if student_usage > 50:  # Mbps
    reduce_student_bandwidth()
    
if faculty_usage < 20:  # Under-utilized
    redistribute_to_students()
```

---

## 📡 What is OpenFlow?

### Simple Explanation
OpenFlow is the "language" that the controller and switches speak.

**Analogy**: 
- You speak English with your friend
- Controller speaks OpenFlow with switches

### Key OpenFlow Messages

#### 1. PACKET_IN (Switch → Controller)
```
Switch: "Hey controller, I got a new packet and don't know what to do!"
```

**When it happens**: First packet from a new source

**Example**: Student's first packet to YouTube

#### 2. FLOW_MOD (Controller → Switch)
```
Controller: "Here's a rule to follow for similar packets"
```

**Contains**:
- **Match**: "For packets from 10.0.2.1"
- **Action**: "Forward to port 3"
- **Priority**: "This rule is more important than default"
- **Timeout**: "Keep rule for 60 seconds"

#### 3. STATS_REQUEST (Controller → Switch)
```
Controller: "Send me statistics about traffic"
```

#### 4. STATS_REPLY (Switch → Controller)
```
Switch: "Here are the stats you requested"
```

**Contains**:
- Packets forwarded per rule
- Bytes transferred per rule
- Active time per rule

---

## 🏢 What is Mininet?

### Simple Explanation
Mininet creates a **virtual network** on your laptop:
- Virtual switches
- Virtual hosts (computers)
- Virtual links (cables)

All runs in software, so you can test network ideas **safely and quickly**!

### Why Mininet?

#### Without Mininet:
- Need real routers ($$$)
- Need real switches ($$$)
- Need physical space
- Risk breaking real network
- Slow to test changes

#### With Mininet:
- ✅ Free (software only)
- ✅ Fast (create 100-host network in seconds)
- ✅ Safe (cannot break real network)
- ✅ Reproducible (same setup every time)
- ✅ Easy to change topology

### Mininet Components

#### 1. Hosts
Virtual computers (like your laptop or phone)

```python
h1 = net.addHost('h1', ip='10.0.0.1')
```

**Can do**:
- Run commands (`h1.cmd('ping 10.0.0.2')`)
- Generate traffic (`h1.cmd('iperf -c 10.0.0.2')`)
- Act like real computers

#### 2. Switches
Virtual network switches (like your Wi-Fi router)

```python
s1 = net.addSwitch('s1')
```

**Can do**:
- Forward packets
- Connect to controller via OpenFlow
- Create queues for QoS

#### 3. Links
Virtual cables connecting hosts and switches

```python
net.addLink(h1, s1)  # Connect host h1 to switch s1
```

**Can configure**:
- Bandwidth limit
- Delay (latency)
- Packet loss

---

## 🎮 What is Ryu?

### Simple Explanation
Ryu is a **SDN controller framework** written in Python.

**Think of it as**: A library that makes it easy to write SDN applications.

### Why Ryu?

✅ **Python**: Easy to learn and write
✅ **Event-driven**: Automatic handling of switch events
✅ **Well-documented**: Good examples and community
✅ **OpenFlow support**: Supports all OpenFlow versions
✅ **Active development**: Regular updates

### Ryu Application Structure

```python
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls

class MyController(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize variables
    
    @set_ev_cls(ofp_event.EventOFPPacketIn)
    def packet_in_handler(self, ev):
        # Handle packets from switch
        pass
    
    @set_ev_cls(ofp_event.EventOFPStatsReply)
    def stats_reply_handler(self, ev):
        # Handle statistics from switch
        pass
```

**Key Concepts**:
- **Events**: Things that happen (packet arrives, switch connects)
- **Handlers**: Your code that responds to events
- **Decorators** (`@set_ev_cls`): Tells Ryu which function handles which event

---

## 🚦 What is QoS (Quality of Service)?

### Simple Explanation
QoS means **controlling who gets how much bandwidth**.

**Analogy**: 
- Highway with 3 lanes
- **Fast lane** (Faculty): Always clear, fast
- **Middle lane** (Lab): Moderate traffic
- **Slow lane** (Students): Can get congested

### Why QoS?

Without QoS:
- Students download movies → Network slows for everyone
- Faculty cannot access important resources
- No fairness

With QoS:
- Faculty always gets minimum guaranteed bandwidth
- Labs get priority during exams
- Students get remaining bandwidth (fair sharing)

### QoS Mechanisms

#### 1. Rate Limiting
**What**: Maximum bandwidth allowed

**Example**: 
- Student: Max 5 Mbps
- Faculty: Max 50 Mbps

#### 2. Guaranteed Bandwidth
**What**: Minimum bandwidth reserved

**Example**:
- Faculty: Guaranteed 40 Mbps (even if network is busy)
- Lab: Guaranteed 30 Mbps

#### 3. Priority Queuing
**What**: Some traffic goes first

**Example**:
- Video calls (high priority)
- File downloads (low priority)

---

## 🎯 How Our Project Uses These Concepts

### 1. Mininet Creates Virtual Campus Network
```
           [Switch s1]
           /    |    \
        [Lab] [Faculty] [Students]
```

### 2. Ryu Controller Monitors Traffic
```python
# Every 5 seconds, collect stats
faculty_usage = get_stats('faculty')
student_usage = get_stats('student')
lab_usage = get_stats('lab')
```

### 3. Dynamic Bandwidth Allocation
```python
# If faculty not using much, give to students
if faculty_usage < 20:  # Mbps
    available = 40 - faculty_usage
    redistribute_to_students(available)
```

### 4. Priority During Exams
```python
# Normal mode
priority = {'faculty': 3, 'lab': 2, 'student': 1}

# Exam mode (scheduled)
priority = {'lab': 3, 'faculty': 2, 'student': 1}
```

### 5. Dashboard Shows Real-time Data
```javascript
// Update every 2 seconds
fetch('/api/group_stats')
    .then(data => updateChart(data))
```

---

## 🎓 Key Takeaways

### Remember These:
1. **SDN** = Central brain controls network
2. **OpenFlow** = Language between controller and switches
3. **Mininet** = Create virtual networks for testing
4. **Ryu** = Write controller logic in Python
5. **QoS** = Control who gets what bandwidth
6. **OVS** = Virtual switch that supports OpenFlow

### The Flow:
```
Your Python Code (Ryu App)
    ↓ (decides bandwidth rules)
Controller (Ryu)
    ↓ (sends OpenFlow messages)
Switch (OVS in Mininet)
    ↓ (enforces rules on packets)
Network Traffic (between hosts)
```

---

## 📚 Want to Learn More?

### Recommended Order:
1. ✅ Read this document (you're here!)
2. → Read `ARCHITECTURE.md` (how our project is structured)
3. → Follow `SETUP_GUIDE.md` (install everything)
4. → Read `README.md` (run the project)
5. → Read `TESTING_GUIDE.md` (test with iperf)

### Video Tutorials:
- Mininet Walkthrough: http://mininet.org/walkthrough/
- OpenFlow Tutorial: https://github.com/mininet/openflow-tutorial
- Ryu Book: https://osrg.github.io/ryu-book/en/html/

---

## ❓ FAQ

**Q: Do I need to understand networking deeply?**
A: No! This project teaches you step-by-step.

**Q: Is programming experience required?**
A: Basic Python knowledge helps, but code is explained line by line.

**Q: Can I run this on Windows?**
A: No, Mininet needs Linux. Use Ubuntu in VirtualBox or dual-boot.

**Q: Will this work for my final year project?**
A: Yes! It covers SDN, QoS, monitoring, and has measurable results.

**Q: How long to complete?**
A: 2-3 weeks if you follow step-by-step (1-2 hours daily).

---

**Ready to proceed?** 
Next step: Read `ARCHITECTURE.md` to understand the project structure! 🚀
