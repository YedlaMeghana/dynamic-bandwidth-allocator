from mininet.topo import Topo

class CampusTopo(Topo):
    def build(self):
        s1 = self.addSwitch('s1')
        # Lab hosts
        for i in range(1, 6):
            h = self.addHost(f'lab{i}', ip=f'10.0.0.{i}')
            self.addLink(h, s1)
        # Faculty hosts
        faculty_ips = ['10.0.1.10', '10.0.1.11']
        for idx, ip in enumerate(faculty_ips):
            h = self.addHost(f'faculty{idx+1}', ip=ip)
            self.addLink(h, s1)
        # Student hosts
        for i in range(1, 11):
            h = self.addHost(f'student{i}', ip=f'10.0.2.{i}')
            self.addLink(h, s1)

topos = {'campustopo': (lambda: CampusTopo())}
