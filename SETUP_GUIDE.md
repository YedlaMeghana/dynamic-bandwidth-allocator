# Setup Guide - Dynamic Bandwidth Allocation Using SDN

## 🎯 Goal of This Guide
By the end of this guide, you will have a fully working SDN environment with Mininet, Ryu Controller, and all dependencies installed and verified.

---

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS (Recommended)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: 10GB free space
- **Processor**: 2+ cores

### Why Ubuntu?
- Mininet works best on Linux
- Most SDN tools are tested on Ubuntu
- Easy package management with apt
- Large community support for troubleshooting

---

## 🔧 Step 0: Verify Your System

Run these commands to check your system:

```bash
# Check OS version
lsb_release -a

# Check available memory
free -h

# Check disk space
df -h
```

**Expected Output**:
- Ubuntu 20.04 or 22.04
- At least 2GB free RAM
- At least 10GB free disk space

**🛑 If you see errors**: Make sure you're using Ubuntu Linux

---

## 📦 Step 1: Update System Packages

### Goal
Update your system to have the latest package information.

### Why?
- Ensures you get the latest stable versions
- Prevents package conflicts
- Fixes known bugs in older packages

### Commands

```bash
sudo apt update
sudo apt upgrade -y
```

### Expected Output
```
Reading package lists... Done
Building dependency tree... Done
All packages are up to date.
```

**⏱️ Time**: 2-5 minutes depending on internet speed

**🛑 Common Errors**:
- "Could not get lock": Another apt process is running. Wait or reboot.
- "Unable to fetch": Check your internet connection.

---

## 🌐 Step 2: Install Python3 and pip

### Goal
Install Python 3.8+ which is required for Ryu controller and dashboard.

### Why Python?
- Ryu controller is written in Python
- Flask dashboard uses Python
- Easy to write network automation scripts

### Commands

```bash
# Install Python3
sudo apt install -y python3 python3-pip python3-dev

# Verify installation
python3 --version
pip3 --version
```

### Expected Output
```
Python 3.8.10 (or higher)
pip 20.0.2 (or higher)
```

**🛑 If python3 --version shows 2.x**: Your system has old Python. Use python3 explicitly.

---

## 🔌 Step 3: Install Mininet

### Goal
Install Mininet - the network emulator that creates virtual switches and hosts.

### What is Mininet?
Mininet creates a realistic virtual network on your laptop:
- Virtual switches (like your Wi-Fi router)
- Virtual hosts (like laptops, phones)
- Virtual links (like ethernet cables)

All running in software, so you can test network ideas safely!

### Commands

```bash
# Install Mininet
sudo apt install -y mininet

# Verify installation
sudo mn --version
```

### Expected Output
```
mininet 2.3.0 (or higher)
```

### Test Mininet

```bash
# Run a simple test
sudo mn --test pingall
```

### Expected Output
```
*** Creating network
*** Adding controller
*** Adding hosts:
h1 h2
*** Adding switches:
s1
*** Ping: testing ping reachability
h1 -> h2
h2 -> h1
*** Results: 0% dropped (2/2 received)
```

**✅ Success Indicator**: You should see "0% dropped"

**🛑 Common Errors**:
- "command not found": Mininet didn't install. Try: `sudo apt install mininet -y`
- "Permission denied": Use `sudo` before commands
- "Cannot connect to X server": You're on a server without GUI. This is OK, GUI not needed.

---

## 🌊 Step 4: Install Open vSwitch (OVS)

### Goal
Install Open vSwitch - the software switch that handles packet forwarding.

### What is Open vSwitch?
- Software version of a physical network switch
- Supports OpenFlow protocol
- Can create queues for QoS (bandwidth control)
- Used by Mininet to create virtual switches

### Commands

```bash
# Install OVS
sudo apt install -y openvswitch-switch openvswitch-common

# Verify installation
sudo ovs-vsctl --version
```

### Expected Output
```
ovs-vsctl (Open vSwitch) 2.15.0 (or higher)
```

### Check OVS Service

```bash
# Check if OVS is running
sudo systemctl status openvswitch-switch
```

### Expected Output
```
● openvswitch-switch.service - Open vSwitch
   Loaded: loaded
   Active: active (exited)
```

**✅ Success Indicator**: Status should be "active"

**🛑 If inactive**:
```bash
sudo systemctl start openvswitch-switch
sudo systemctl enable openvswitch-switch
```

---

## 🎮 Step 5: Install Ryu Controller

### Goal
Install Ryu - the SDN controller that makes intelligent decisions about network traffic.

### What is Ryu?
Ryu is the "brain" of your SDN network:
- Receives packet information from switches
- Decides how to handle traffic (forward, drop, rate-limit)
- Installs rules in switches via OpenFlow
- Written in Python, easy to customize

### Commands

```bash
# Install Ryu
sudo pip3 install ryu

# Verify installation
ryu-manager --version
```

### Expected Output
```
ryu-manager 4.34 (or higher)
```

### Test Ryu

```bash
# Run a simple Ryu app
ryu-manager --version
```

**✅ Success**: Should show version without errors

**🛑 Common Errors**:
- "command not found": Path issue. Try: `python3 -m ryu.cmd.manager --version`
- "No module named ryu": Installation failed. Retry: `sudo pip3 install --upgrade ryu`

---

## 🌐 Step 6: Install Flask (For Dashboard)

### Goal
Install Flask web framework for the monitoring dashboard.

### What is Flask?
- Python web framework
- Creates web pages and REST APIs
- Used to visualize bandwidth usage
- Provides web interface for admin controls

### Commands

```bash
# Install Flask
sudo pip3 install flask

# Verify installation
python3 -c "import flask; print(flask.__version__)"
```

### Expected Output
```
2.0.1 (or higher)
```

---

## 🔧 Step 7: Install Additional Tools

### Goal
Install helper tools for traffic testing and monitoring.

### Commands

```bash
# Install iperf (traffic generator)
sudo apt install -y iperf iperf3

# Install network tools
sudo apt install -y net-tools tcpdump iproute2

# Verify iperf
iperf --version
```

### Expected Output
```
iperf version 2.x.x (or higher)
```

### Why These Tools?
- **iperf**: Generate test traffic to measure bandwidth
- **tcpdump**: Capture and analyze network packets
- **net-tools**: Network configuration (ifconfig, route)
- **iproute2**: Advanced networking (ip, tc commands for QoS)

---

## 🎨 Step 8: Install Project Dependencies

### Goal
Install all Python packages required by this project.

### Commands

```bash
# Navigate to project directory
cd /path/to/dynamic-bandwidth-allocator

# Install project requirements
pip3 install -r requirements.txt
```

### Expected Output
```
Successfully installed ryu-4.34 flask-2.0.1 mininet-2.3.0
```

**🛑 If requirements.txt not found**: You're in wrong directory. Use `ls` to verify.

---

## ✅ Step 9: Verify Complete Setup

### Goal
Run all verification commands to ensure everything is installed correctly.

### Verification Script

Create and run this verification script:

```bash
#!/bin/bash
echo "=== SDN Environment Verification ==="
echo ""

echo "1. Python3 version:"
python3 --version

echo ""
echo "2. pip3 version:"
pip3 --version

echo ""
echo "3. Mininet version:"
sudo mn --version

echo ""
echo "4. Open vSwitch version:"
sudo ovs-vsctl --version

echo ""
echo "5. Ryu version:"
ryu-manager --version

echo ""
echo "6. Flask installed:"
python3 -c "import flask; print('Flask', flask.__version__)"

echo ""
echo "7. iperf installed:"
iperf --version | head -1

echo ""
echo "=== Verification Complete ==="
echo "If all commands succeeded, you're ready to proceed!"
```

Save as `verify_setup.sh` and run:

```bash
chmod +x verify_setup.sh
./verify_setup.sh
```

---

## 🎯 Next Steps

**✅ Setup Complete!** You now have:
- Ubuntu system updated
- Python 3 installed
- Mininet installed and tested
- Open vSwitch installed and running
- Ryu controller installed
- Flask framework ready
- Testing tools available

**👉 What's Next?**
1. Read `SDN_BASICS.md` to understand SDN concepts
2. Read `ARCHITECTURE.md` to understand project structure
3. Follow `README.md` to run the project

---

## 🆘 Troubleshooting

### Problem: "Permission denied" errors
**Solution**: Use `sudo` for system commands

### Problem: "Package not found"
**Solution**: Run `sudo apt update` first

### Problem: Mininet test fails
**Solution**:
```bash
sudo mn -c  # Clean up old instances
sudo systemctl restart openvswitch-switch
sudo mn --test pingall
```

### Problem: Can't install Ryu
**Solution**:
```bash
sudo apt install -y python3-pip python3-dev
sudo pip3 install --upgrade pip
sudo pip3 install ryu
```

### Problem: Out of disk space
**Solution**:
```bash
# Clean apt cache
sudo apt clean
sudo apt autoremove -y
```

---

## 📚 Additional Resources

- **Mininet Documentation**: http://mininet.org/walkthrough/
- **Ryu Documentation**: https://ryu.readthedocs.io/
- **OpenFlow Tutorial**: https://github.com/mininet/openflow-tutorial/wiki
- **Ubuntu Help**: https://help.ubuntu.com/

---

## ✉️ Need Help?

If you're stuck:
1. Check the error message carefully
2. Look in `TROUBLESHOOTING.md`
3. Search the error on Google with "mininet" or "ryu"
4. Ask your project mentor

**Remember**: Every expert was once a beginner. Take it step by step! 🚀
