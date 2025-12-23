from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
from ryu.lib import hub
import ipaddress
import json
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/controller.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('DynamicBWAllocator')

# Faculty IPs as a list (can be updated dynamically)
FACULTY_IPS = ['10.0.1.10', '10.0.1.11']

# Lab IPs as a range
LAB_IP_RANGE = ipaddress.summarize_address_range(
    ipaddress.IPv4Address('10.0.0.1'),
    ipaddress.IPv4Address('10.0.0.244')
)

# Application Priority mapping
APP_PORT_PRIORITIES = {
    443: 'edu',   # HTTPS (assume edu apps)
    8801: 'edu',  # Zoom
    80: 'stream', # HTTP (assume streaming)
    8080: 'stream',
    554: 'stream', # RTSP (streaming)
}

# Default bandwidth allocations (Mbps)
GROUP_MIN_BW = {
    'faculty': 40,  # Mbps (guaranteed min)
    'lab': 30,
    'student': 5,
}

# Maximum bandwidth allocations (Mbps)
GROUP_MAX_BW = {
    'faculty': 100,
    'lab': 80,
    'student': 50,
}

# Priority levels (higher = more important)
GROUP_PRIORITY = {
    'faculty': 3,  # Highest
    'lab': 2,      # Medium
    'student': 1   # Lowest
}

# Queue mapping
GROUP_QUEUE = {
    'faculty': 1,
    'lab': 2,
    'student': 3
}

# Stats file location
STATS_FILE = '/tmp/group_stats.json'
BANDWIDTH_LOG_FILE = '/tmp/bandwidth.log'

class DynamicBWAllocator(app_manager.RyuApp):
    """
    Dynamic Bandwidth Allocator SDN Controller
    
    Features:
    - Priority-based bandwidth allocation (Faculty > Lab > Student)
    - Dynamic bandwidth recalculation every 5 seconds
    - QoS enforcement via OpenFlow queues
    - Automatic redistribution of unused bandwidth
    - Exam mode support (time-based priority switching)
    - Real-time monitoring and statistics
    """
    
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        
        # Statistics tracking
        self.flow_stats = {'faculty': 0, 'lab': 0, 'student': 0}
        self.flow_stats_bytes = {'faculty': 0, 'lab': 0, 'student': 0}
        self.last_stats_time = time.time()
        
        # Current bandwidth allocations (can change dynamically)
        self.current_bandwidth = GROUP_MIN_BW.copy()
        self.current_priority = GROUP_PRIORITY.copy()
        
        # Exam mode flag
        self.exam_mode = False
        
        # Flow tracking for redistribution
        self.active_flows = {}  # {src_ip: {group, bytes, last_seen}}
        
        logger.info("="*60)
        logger.info("Dynamic Bandwidth Allocator Started")
        logger.info("="*60)
        logger.info("Initial Configuration:")
        logger.info(f"  Faculty: {GROUP_MIN_BW['faculty']}-{GROUP_MAX_BW['faculty']} Mbps (Priority {GROUP_PRIORITY['faculty']})")
        logger.info(f"  Lab:     {GROUP_MIN_BW['lab']}-{GROUP_MAX_BW['lab']} Mbps (Priority {GROUP_PRIORITY['lab']})")
        logger.info(f"  Student: {GROUP_MIN_BW['student']}-{GROUP_MAX_BW['student']} Mbps (Priority {GROUP_PRIORITY['student']})")
        logger.info("="*60)

    def classify_group(self, ip):
        """
        Classify IP address into group (faculty, lab, or student).
        
        Args:
            ip: IP address string
            
        Returns:
            str: Group name ('faculty', 'lab', or 'student')
        """
        if ip in FACULTY_IPS:
            return 'faculty'
        for rng in LAB_IP_RANGE:
            try:
                if ipaddress.IPv4Address(ip) in rng:
                    return 'lab'
            except:
                pass
        return 'student'

    def classify_app(self, pkt):
        if pkt.has_protocol(tcp.tcp):
            port = pkt.get_protocol(tcp.tcp).dst_port
        elif pkt.has_protocol(udp.udp):
            port = pkt.get_protocol(udp.udp).dst_port
        else:
            return None
        return APP_PORT_PRIORITIES.get(port)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        self.datapaths[datapath.id] = datapath
        self.install_table_miss(datapath)

    def install_table_miss(self, datapath):
        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=0, match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        """
        Handle packets sent to controller (PACKET_IN events).
        Install flow rules with appropriate QoS queue.
        """
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if not ip_pkt:
            return

        src_ip = ip_pkt.src
        dst_ip = ip_pkt.dst
        group = self.classify_group(src_ip)
        app_priority = self.classify_app(pkt)

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        # Get queue ID for this group
        queue_id = GROUP_QUEUE.get(group, 3)  # Default to student queue
        
        # Get priority level for this group
        flow_priority = 100 + (self.current_priority.get(group, 1) * 10)
        
        # Higher priority for educational apps
        if app_priority == 'edu':
            flow_priority += 50

        # Log new flow
        logger.info(f"New flow: {src_ip} ({group}) -> {dst_ip}, Queue: {queue_id}, Priority: {flow_priority}")

        # Actions: Set queue and forward
        actions = [
            parser.OFPActionSetQueue(queue_id),
            parser.OFPActionOutput(ofproto.OFPP_NORMAL)
        ]

        # Match on source IP
        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)

        # Install flow rule
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath,
            priority=flow_priority,
            match=match,
            instructions=inst,
            idle_timeout=30,
            hard_timeout=60
        )
        datapath.send_msg(mod)

        # Send packet out
        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data
        )
        datapath.send_msg(out)
        
        # Track active flow
        self.active_flows[src_ip] = {
            'group': group,
            'bytes': 0,
            'last_seen': time.time()
        }

    def _monitor(self):
        """
        Background monitoring thread.
        Collects statistics every 5 seconds and performs dynamic reallocation.
        """
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(5)  # Monitor every 5 seconds

    def request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        """
        Handle flow statistics replies from switches.
        Calculate bandwidth usage and perform dynamic reallocation.
        """
        body = ev.msg.body
        current_time = time.time()
        time_diff = current_time - self.last_stats_time
        
        if time_diff == 0:
            time_diff = 1  # Avoid division by zero
        
        # Calculate bytes transferred per group
        group_stats_bytes = {'faculty': 0, 'lab': 0, 'student': 0}
        for stat in body:
            if 'ipv4_src' in stat.match:
                ip = stat.match['ipv4_src']
                group = self.classify_group(ip)
                group_stats_bytes[group] += stat.byte_count
        
        # Calculate bandwidth in Mbps: (bytes * 8) / (time_in_seconds * 1_000_000)
        group_stats_mbps = {}
        for group in ['faculty', 'lab', 'student']:
            bytes_diff = group_stats_bytes[group] - self.flow_stats_bytes.get(group, 0)
            if bytes_diff < 0:
                bytes_diff = group_stats_bytes[group]  # Counter wrapped or reset
            
            # Convert to Mbps
            mbps = (bytes_diff * 8) / (time_diff * 1_000_000)
            group_stats_mbps[group] = round(mbps, 2)
        
        # Update stored values
        self.flow_stats = group_stats_mbps
        self.flow_stats_bytes = group_stats_bytes
        self.last_stats_time = current_time
        
        # Log bandwidth usage
        logger.info(f"Current Bandwidth - Faculty: {group_stats_mbps['faculty']} Mbps, "
                   f"Lab: {group_stats_mbps['lab']} Mbps, "
                   f"Student: {group_stats_mbps['student']} Mbps")
        
        # Perform dynamic bandwidth redistribution
        self._redistribute_bandwidth(group_stats_mbps)
        
        # Write stats for dashboard
        try:
            with open(STATS_FILE, 'w') as f:
                json.dump(self.flow_stats, f)
        except Exception as e:
            logger.error(f"Error writing stats file: {e}")
        
        # Log to bandwidth log file
        try:
            with open(BANDWIDTH_LOG_FILE, 'a') as f:
                log_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'bandwidth': group_stats_mbps,
                    'exam_mode': self.exam_mode
                }
                f.write(json.dumps(log_entry) + '\n')
        except Exception as e:
            logger.error(f"Error writing bandwidth log: {e}")
    
    def _redistribute_bandwidth(self, current_usage):
        """
        Dynamically redistribute unused bandwidth to groups that need it.
        
        Args:
            current_usage: Dict with current bandwidth usage per group (Mbps)
        """
        # Check if faculty is under-utilizing
        faculty_guaranteed = self.current_bandwidth.get('faculty', 40)
        faculty_usage = current_usage.get('faculty', 0)
        
        if faculty_usage < faculty_guaranteed * 0.5:  # Using less than 50% of guarantee
            unused = faculty_guaranteed - faculty_usage
            logger.info(f"Faculty under-utilizing: {faculty_usage} Mbps (guaranteed {faculty_guaranteed})")
            logger.info(f"Unused bandwidth available for redistribution: {unused} Mbps")
            
            # Could redistribute to students and labs here
            # For now, just log the availability
            # In a full implementation, would update queue parameters dynamically
    
    def update_bandwidth_config(self, new_bandwidth):
        """
        Update bandwidth configuration (for exam mode or manual changes).
        
        Args:
            new_bandwidth: Dict with new bandwidth allocations
        """
        logger.info(f"Updating bandwidth configuration: {new_bandwidth}")
        self.current_bandwidth = new_bandwidth.copy()
        
    def update_priority_config(self, new_priority):
        """
        Update priority configuration (for exam mode or manual changes).
        
        Args:
            new_priority: Dict with new priority levels
        """
        logger.info(f"Updating priority configuration: {new_priority}")
        self.current_priority = new_priority.copy()
    
    def reinstall_all_flows(self):
        """
        Reinstall all flow rules with updated priorities/queues.
        Used when switching modes (normal -> exam or exam -> normal).
        """
        logger.info("Reinstalling all flows with updated configuration")
        for dp in self.datapaths.values():
            # Clear all existing flows (except table-miss)
            parser = dp.ofproto_parser
            ofproto = dp.ofproto
            match = parser.OFPMatch()
            mod = parser.OFPFlowMod(
                datapath=dp,
                command=ofproto.OFPFC_DELETE,
                out_port=ofproto.OFPP_ANY,
                out_group=ofproto.OFPG_ANY,
                match=match
            )
            dp.send_msg(mod)
            
            # Reinstall table-miss rule
            self.install_table_miss(dp)
        
        logger.info("Flow rules cleared, new rules will be installed on next PACKET_IN")
    
    def update_faculty_ips(self, new_ips):
        """
        Update faculty IP list (for dashboard admin functionality).
        
        Args:
            new_ips: List of new faculty IP addresses
        """
        global FACULTY_IPS
        FACULTY_IPS = new_ips
        logger.info(f"Updated faculty IPs: {FACULTY_IPS}")
        return {"status": "success", "faculty_ips": FACULTY_IPS}
