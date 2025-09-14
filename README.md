# Dynamic Bandwidth Allocator for College Wi-Fi (SDN + Mininet + Python)

## Overview

Simulate a campus Wi-Fi network in Mininet. Use an SDN controller (Ryu) to dynamically allocate bandwidth to students, faculty, and labs. Visualize group usage on a live Flask dashboard.

## How To Run

1. **Install Dependencies**:
    ```
    pip install -r requirements.txt
    ```

2. **Start the Dashboard**:
    ```
    cd dashboard
    python app.py
    ```

3. **Run SDN Controller and Mininet**:
    ```
    cd mininet
    bash run_simulation.sh
    ```

4. **Generate Traffic**:
    ```
    cd traffic
    sudo python generate_traffic.py
    ```

5. **See Dashboard**:  
   Open [http://localhost:5000](http://localhost:5000) in your browser.

## Customization

- Edit `controller/group_bandwidth.py` for group policies and bandwidth.
- Edit `mininet/campus_topo.py` to change host counts or IPs.
- Extend dashboard for more advanced stats.
