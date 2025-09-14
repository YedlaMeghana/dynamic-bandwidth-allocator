from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, ipv4, tcp, udp
from ryu.lib import hub
import ipaddress
import json
import time

# Faculty IPs as a list
FACULTY_IPS = ['10.0.1.10', '10.0.1.11']
# Lab IPs as a range
LAB_IP_RANGE = ipaddress.summarize_address_range(ipaddress.IPv4Address('10.0.0.1'),
                                                 ipaddress.IPv4Address('10.0.0.244'))

# Application Priority mapping
APP_PORT_PRIORITIES = {
    443: 'edu',   # HTTPS (assume edu apps)
    8801: 'edu',  # Zoom
    80: 'stream', # HTTP (assume streaming)
    8080: 'stream',
    554: 'stream', # RTSP (streaming)
}

GROUP_MIN_BW = {
    'faculty': 40,  # Mbps (guaranteed min)
    'lab': 30,
    'student': 5,
}

STATS_FILE = '/tmp/group_stats.json'

class DynamicBWAllocator(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.flow_stats = {'faculty': 0, 'lab': 0, 'student': 0}

    def classify_group(self, ip):
        if ip in FACULTY_IPS:
            return 'faculty'
        for rng in LAB_IP_RANGE:
            if ipaddress.IPv4Address(ip) in rng:
                return 'lab'
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
        msg = ev.msg
        datapath = msg.datapath
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        ip_pkt = pkt.get_protocol(ipv4.ipv4)

        if not ip_pkt:
            return

        src_ip = ip_pkt.src
        group = self.classify_group(src_ip)
        app_priority = self.classify_app(pkt)

        parser = datapath.ofproto_parser
        ofproto = datapath.ofproto

        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=src_ip)
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]

        priority = 100
        if app_priority == 'edu':
            priority = 200  # Higher priority for education apps

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst, idle_timeout=30, hard_timeout=60)
        datapath.send_msg(mod)

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=ofproto.OFP_NO_BUFFER,
            in_port=in_port,
            actions=actions,
            data=msg.data)
        datapath.send_msg(out)

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self.request_stats(dp)
            hub.sleep(2)

    def request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        body = ev.msg.body
        group_stats = {'faculty': 0, 'lab': 0, 'student': 0}
        for stat in body:
            if 'ipv4_src' in stat.match:
                ip = stat.match['ipv4_src']
                group = self.classify_group(ip)
                group_stats[group] += stat.byte_count
        self.flow_stats = group_stats
        # Write stats for dashboard
        with open(STATS_FILE, 'w') as f:
            json.dump(self.flow_stats, f)
