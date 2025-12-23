# Project Architecture - Dynamic Bandwidth Allocator

## 🎯 Goal of This Document
Understand how all components of this project work together and why each file exists.

---

## 📁 Project Directory Structure

```
dynamic-bandwidth-allocator/
│
├── controller/                    # SDN Controller (Brain)
│   ├── group_bandwidth.py        # Main Ryu controller app
│   └── exam_scheduler.py         # NEW: Exam mode scheduler
│
├── mininet/                       # Network Emulator
│   ├── campus_topo.py            # Network topology definition
│   ├── run_simulation.sh         # Script to start everything
│   └── qos_setup.sh              # NEW: QoS queue configuration
│
├── dashboard/                     # Web Dashboard
│   ├── app.py                    # Flask web server
│   ├── templates/
│   │   └── index.html            # Dashboard UI
│   └── static/                   # NEW: CSS, JS files
│       ├── css/
│       │   └── dashboard.css
│       └── js/
│           └── dashboard.js
│
├── traffic/                       # Traffic Generation & Testing
│   ├── generate_traffic.py      # Generate test traffic
│   └── test_bandwidth.sh         # NEW: Automated bandwidth tests
│
├── docs/                          # Documentation
│   ├── SETUP_GUIDE.md            # Installation guide
│   ├── SDN_BASICS.md             # SDN concepts
│   ├── ARCHITECTURE.md           # This file
│   ├── TESTING_GUIDE.md          # How to test
│   ├── TROUBLESHOOTING.md        # Common errors
│   ├── DEMO_GUIDE.md             # Final demo preparation
│   └── VIVA_QUESTIONS.md         # Viva preparation
│
├── logs/                          # NEW: Log files
│   ├── controller.log
│   ├── bandwidth.log
│   └── exam_mode.log
│
├── config/                        # NEW: Configuration files
│   ├── priorities.json           # Group priorities
│   ├── bandwidth_limits.json     # Bandwidth allocations
│   └── exam_schedule.json        # Exam timing
│
├── requirements.txt               # Python dependencies
└── README.md                      # Quick start guide
```

---

## 🏗️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN DASHBOARD                          │
│                    (Flask Web Interface)                         │
│  • Real-time graphs                                              │
│  • Bandwidth monitoring                                          │
│  • Exam mode scheduler                                           │
│  • Faculty IP management                                         │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP API
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      RYU SDN CONTROLLER                          │
│                  (controller/group_bandwidth.py)                 │
│                                                                   │
│  • Traffic classification (Faculty/Lab/Student)                  │
│  • Bandwidth calculation (every 5 seconds)                       │
│  • QoS rule installation                                         │
│  • Statistics collection                                         │
│  • Exam mode logic                                               │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ OpenFlow Protocol
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                   OPEN vSWITCH (OVS)                             │
│                    (Mininet Virtual Switch)                      │
│                                                                   │
│  • Packet forwarding                                             │
│  • Flow table management                                         │
│  • QoS queues (TC)                                               │
│  • Statistics reporting                                          │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ Virtual Links
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                      NETWORK HOSTS                               │
│                   (Mininet Virtual Hosts)                        │
│                                                                   │
│  ┌─────────┐  ┌─────────┐  ┌──────────┐                        │
│  │ Faculty │  │   Lab   │  │ Student  │                         │
│  │ (2 PCs) │  │ (5 PCs) │  │ (10 PCs) │                         │
│  └─────────┘  └─────────┘  └──────────┘                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow - Step by Step

### Scenario: Student Starts Downloading a File

#### Step 1: Network Initialization

```
1. Admin runs: bash run_simulation.sh
   └─> Starts Ryu controller
   └─> Creates Mininet topology
   └─> Configures OVS queues

2. Ryu controller connects to switch
   └─> Switch sends features (capabilities)
   └─> Controller installs default rules

3. Dashboard starts
   └─> Flask server on port 5000
   └─> Waits for stats from controller
```

#### Step 2: Student Generates Traffic

```
Student (10.0.2.5) → Internet (172.217.x.x)

1. Student's host sends packet
   ↓
2. Packet arrives at OVS switch (s1)
   └─> Switch checks flow table
   └─> No matching rule found!
   ↓
3. Switch sends PACKET_IN to controller
   └─> "Hey controller, what should I do?"
```

#### Step 3: Controller Makes Decision

```python
# In controller/group_bandwidth.py

@set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
def packet_in_handler(self, ev):
    # Extract packet info
    src_ip = packet.src  # "10.0.2.5"
    
    # Step 3.1: Classify group
    group = classify_group(src_ip)  # Returns "student"
    
    # Step 3.2: Check current usage
    current_usage = self.group_stats['student']  # e.g., 45 Mbps
    
    # Step 3.3: Calculate allowed bandwidth
    if current_usage < GROUP_MIN_BW['student']:
        bandwidth = GROUP_MIN_BW['student']  # 5 Mbps
    else:
        bandwidth = calculate_fair_share()
    
    # Step 3.4: Install flow rule
    install_flow_with_qos(src_ip, bandwidth, priority=1)
```

#### Step 4: Controller Installs Rule

```
Controller → Switch (FLOW_MOD message)

Match: ipv4_src=10.0.2.5
Actions:
  - Set queue: queue_id=3 (student queue)
  - Forward: output=port_to_internet
Priority: 1 (lower than faculty)
Timeout: 60 seconds
```

#### Step 5: Switch Enforces Rule

```
OVS Switch receives FLOW_MOD
  ↓
Installs rule in flow table
  ↓
Applies QoS queue (rate limiting)
  ↓
Forwards packet at controlled rate (5 Mbps max)
```

#### Step 6: Statistics Collection

```
Every 5 seconds:

Controller → Switch: "Send me stats" (STATS_REQUEST)
  ↓
Switch → Controller: "Here are stats" (STATS_REPLY)
  - Faculty: 35 Mbps (3,500,000 bytes in 5 sec)
  - Lab: 28 Mbps
  - Student: 47 Mbps
  ↓
Controller updates group_stats dictionary
  ↓
Controller writes to /tmp/group_stats.json
```

#### Step 7: Dashboard Updates

```
Every 2 seconds:

Browser → Dashboard: GET /api/group_stats
  ↓
Dashboard reads /tmp/group_stats.json
  ↓
Dashboard → Browser: JSON response
  {
    "faculty": 35.2,
    "lab": 28.7,
    "student": 47.1
  }
  ↓
JavaScript updates chart in real-time
```

#### Step 8: Dynamic Reallocation

```python
# In controller monitoring thread

def _monitor(self):
    while True:
        # Collect stats
        stats = collect_all_stats()
        
        # Check if faculty under-utilizing
        if stats['faculty'] < GROUP_MIN_BW['faculty'] * 0.5:
            # Faculty using less than 20 Mbps (50% of 40)
            unused = GROUP_MIN_BW['faculty'] - stats['faculty']
            
            # Redistribute to others
            redistribute_bandwidth(unused, ['student', 'lab'])
        
        hub.sleep(5)  # Wait 5 seconds
```

---

## 🧩 Component Details

### 1. Controller (controller/group_bandwidth.py)

**Purpose**: The brain that makes bandwidth decisions

**Key Functions**:

```python
class DynamicBWAllocator(app_manager.RyuApp):
    
    def __init__(self):
        # Initialize data structures
        self.datapaths = {}           # Connected switches
        self.flow_stats = {}          # Traffic statistics
        self.group_bandwidth = {}     # Current allocations
        self.exam_mode = False        # Exam mode flag
        self.monitor_thread = hub.spawn(self._monitor)
    
    def classify_group(self, ip):
        """Determine if IP is faculty, lab, or student"""
        # Returns: 'faculty' | 'lab' | 'student'
        
    def calculate_bandwidth(self, group, current_usage):
        """Calculate bandwidth for group based on policy"""
        # Considers: priority, current usage, available bandwidth
        
    def install_qos_rule(self, ip, bandwidth, priority):
        """Install OpenFlow rule with QoS queue"""
        # Creates: match + actions + queue_id
        
    def redistribute_bandwidth(self):
        """Give unused bandwidth to others"""
        # Logic: Faculty unused → Give to students
        
    def _monitor(self):
        """Background thread: collect stats every 5 seconds"""
        while True:
            self.request_stats()
            hub.sleep(5)
```

**Why this design?**
- **Event-driven**: Ryu calls functions automatically when events occur
- **Threaded monitoring**: Separate thread for periodic tasks
- **Stateful**: Remembers connections and statistics

---

### 2. Network Topology (mininet/campus_topo.py)

**Purpose**: Define the virtual campus network structure

```python
class CampusTopo(Topo):
    def build(self):
        # Create central switch
        s1 = self.addSwitch('s1', protocols='OpenFlow13')
        
        # Add faculty hosts (10.0.1.x)
        faculty1 = self.addHost('faculty1', ip='10.0.1.10', mac='00:00:00:00:01:10')
        faculty2 = self.addHost('faculty2', ip='10.0.1.11', mac='00:00:00:00:01:11')
        
        # Add lab hosts (10.0.0.x)
        for i in range(1, 6):
            lab = self.addHost(f'lab{i}', ip=f'10.0.0.{i}', mac=f'00:00:00:00:00:0{i}')
            
        # Add student hosts (10.0.2.x)
        for i in range(1, 11):
            student = self.addHost(f'student{i}', ip=f'10.0.2.{i}', mac=f'00:00:00:00:02:0{i}')
        
        # Create links (all to s1)
        # All with default bandwidth (no limit on link itself)
```

**Why this structure?**
- **Star topology**: Simple, all hosts connect to one switch
- **IP addressing**: Easy to classify by IP range
- **Scalable**: Easy to add more hosts

---

### 3. QoS Configuration (mininet/qos_setup.sh)

**Purpose**: Create traffic control queues on OVS

```bash
#!/bin/bash

# Get interface name
IFACE=$(sudo ovs-vsctl list-ports s1 | head -1)

# Create HTB (Hierarchical Token Bucket) qdisc
sudo tc qdisc add dev $IFACE root handle 1: htb default 30

# Create classes for each group
# Faculty: 40 Mbps guaranteed, 100 Mbps max
sudo tc class add dev $IFACE parent 1: classid 1:1 htb rate 40mbit ceil 100mbit

# Lab: 30 Mbps guaranteed, 80 Mbps max
sudo tc class add dev $IFACE parent 1: classid 1:2 htb rate 30mbit ceil 80mbit

# Student: 5 Mbps guaranteed, 50 Mbps max
sudo tc class add dev $IFACE parent 1: classid 1:3 htb rate 5mbit ceil 50mbit

# Map queues to OVS
sudo ovs-vsctl set port $IFACE qos=@newqos -- \
    --id=@newqos create qos type=linux-htb other-config:max-rate=1000000000 \
    queues:1=@q1 queues:2=@q2 queues:3=@q3 -- \
    --id=@q1 create queue other-config:min-rate=40000000 other-config:max-rate=100000000 -- \
    --id=@q2 create queue other-config:min-rate=30000000 other-config:max-rate=80000000 -- \
    --id=@q3 create queue other-config:min-rate=5000000 other-config:max-rate=50000000
```

**Why TC (Traffic Control)?**
- **Rate limiting**: Enforce bandwidth caps
- **Guaranteed bandwidth**: Minimum assured rates
- **Priority**: Different classes for different groups

---

### 4. Dashboard (dashboard/app.py)

**Purpose**: Web interface for monitoring and control

```python
from flask import Flask, render_template, jsonify, request

app = Flask(__name__)

@app.route('/')
def index():
    """Serve main dashboard page"""
    return render_template('index.html')

@app.route('/api/group_stats')
def group_stats():
    """API: Get current bandwidth usage"""
    stats = read_stats_file()
    return jsonify(stats)

@app.route('/api/update_faculty', methods=['POST'])
def update_faculty():
    """API: Update faculty IP/MAC"""
    data = request.json
    # Update controller configuration
    return jsonify({'status': 'success'})

@app.route('/api/exam_mode', methods=['POST'])
def set_exam_mode():
    """API: Schedule exam mode"""
    start_time = request.json['start_time']
    end_time = request.json['end_time']
    # Configure exam mode in controller
    return jsonify({'status': 'scheduled'})

@app.route('/api/current_allocations')
def current_allocations():
    """API: Get current bandwidth allocations"""
    # Read from controller state
    return jsonify(allocations)
```

**Why Flask?**
- **Lightweight**: Easy to set up and run
- **RESTful APIs**: Easy to fetch data with JavaScript
- **Template engine**: Render HTML with Python data

---

### 5. Exam Mode Scheduler (controller/exam_scheduler.py)

**Purpose**: Automatically change priorities during exams

```python
import schedule
import time
from datetime import datetime

class ExamScheduler:
    def __init__(self, controller):
        self.controller = controller
        self.exam_active = False
        
    def schedule_exam(self, start_time, end_time):
        """Schedule exam mode for specific time"""
        # start_time: "2024-03-15 09:00"
        # end_time: "2024-03-15 12:00"
        
        schedule.every().day.at(start_time).do(self.start_exam)
        schedule.every().day.at(end_time).do(self.end_exam)
        
    def start_exam(self):
        """Enter exam mode: Lab priority increases"""
        self.exam_active = True
        
        # Change priorities
        priorities = {
            'lab': 3,      # Highest
            'faculty': 2,
            'student': 1   # Lowest
        }
        
        # Update bandwidth allocations
        bandwidth = {
            'lab': 60,     # Mbps
            'faculty': 20,
            'student': 5
        }
        
        self.controller.update_priorities(priorities)
        self.controller.update_bandwidth(bandwidth)
        
    def end_exam(self):
        """Exit exam mode: Restore normal priorities"""
        self.exam_active = False
        
        # Restore normal priorities
        priorities = {
            'faculty': 3,  # Highest
            'lab': 2,
            'student': 1
        }
        
        bandwidth = {
            'faculty': 40,
            'lab': 30,
            'student': 5
        }
        
        self.controller.update_priorities(priorities)
        self.controller.update_bandwidth(bandwidth)
```

---

## 🔐 Security Considerations

### Input Validation
```python
def update_faculty_ip(new_ip):
    # Validate IP format
    if not is_valid_ip(new_ip):
        raise ValueError("Invalid IP address")
    
    # Update configuration
    FACULTY_IPS.append(new_ip)
```

### Authentication (Future Enhancement)
```python
@app.route('/api/admin_action', methods=['POST'])
@require_admin_auth
def admin_action():
    # Only admin can change settings
    pass
```

---

## 📊 Performance Considerations

### Why Update Every 5 Seconds?
- **Too frequent** (1 sec): High CPU usage, unnecessary
- **Too slow** (30 sec): Delayed response to changes
- **5 seconds**: Good balance for demo

### Why Use Shared File for Stats?
```python
# /tmp/group_stats.json
{
    "faculty": 35.2,
    "lab": 28.7,
    "student": 47.1
}
```

**Pros**:
- Simple (no database needed)
- Fast (local file system)
- Easy to debug (can read with `cat`)

**Cons** (acceptable for demo):
- Not persistent (lost on reboot)
- Not scalable (multiple controllers)

---

## 🎯 Design Decisions Explained

### 1. Why Python?
- **Ryu** is Python-based
- **Flask** is Python-based
- Easy for students to understand
- Quick prototyping

### 2. Why Star Topology?
- **Simple**: All hosts connect to one switch
- **Realistic**: Similar to actual campus (central router)
- **Easy to manage**: One point of control

### 3. Why OpenFlow 1.3?
- **Mature**: Well-tested, stable
- **QoS support**: Has queue actions
- **Ryu support**: Well-supported by Ryu

### 4. Why Group-based (not per-host)?
- **Scalability**: 100s of hosts in real campus
- **Policy-based**: Easier to manage policies
- **Fair**: Within group, all get equal share

---

## 🔮 Future Enhancements

### Possible Additions:
1. **Machine Learning**: Predict usage patterns
2. **Multiple Switches**: Multi-campus support
3. **Application-aware**: Different rates for Zoom vs Netflix
4. **User Authentication**: Login-based policies
5. **Database**: Persistent storage
6. **Mobile App**: Android/iOS dashboard

---

## 📚 Next Steps

Now that you understand the architecture:

1. ✅ **Setup** → Follow `SETUP_GUIDE.md`
2. ✅ **Run** → Follow `README.md`
3. → **Test** → Follow `TESTING_GUIDE.md`
4. → **Debug** → Check `TROUBLESHOOTING.md`
5. → **Demo** → Prepare with `DEMO_GUIDE.md`

---

## ❓ Understanding Check

Before proceeding, make sure you can answer:

1. What are the three main components of the system?
   - Answer: Controller (Ryu), Switch (OVS), Dashboard (Flask)

2. How does the controller learn about new traffic?
   - Answer: Switch sends PACKET_IN message

3. How is bandwidth enforced?
   - Answer: TC queues on OVS + OpenFlow rules

4. How does the dashboard get data?
   - Answer: Reads /tmp/group_stats.json written by controller

5. What happens during exam mode?
   - Answer: Lab priority increases, faculty/student decreases

If you can answer these, you understand the architecture! 🎉

---

**Ready?** Let's install and run the system! → Go to `SETUP_GUIDE.md` 🚀
