from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel

def test_traffic():
    net = Mininet(controller=RemoteController)
    net.start()
    # Faculty runs iperf server
    faculty = net.get('faculty1')
    faculty.cmd('iperf -s -p 5001 &')
    # Lab runs iperf server
    lab = net.get('lab1')
    lab.cmd('iperf -s -p 5002 &')
    # Students run iperf client (simulate traffic)
    for i in range(1, 6):
        student = net.get(f'student{i}')
        student.cmd(f'iperf -c 10.0.1.10 -p 5001 -t 30 &')
        student.cmd(f'iperf -c 10.0.0.1 -p 5002 -t 30 &')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    test_traffic()
