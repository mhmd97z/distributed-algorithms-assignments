'''
Bellman-Ford Shrtest Path
-----
Topology Input foramt: 
	src_node dest_node weight delay
Example:
	0 1 -1 2
	0 2 4 1
	1 2 3 3
	1 3 2 1
	1 4 2 2
	3 2 5 4
	3 1 1 1
	4 3 -3 2
'''

import math
import socket
import threading
import time

# ------------------------ Classes
class Edge:
    def __init__(self, _dest, _weight, _delay, _ip_send, _port_send):
        self.dest = _dest
        self.weight = _weight
        self.delay = [_delay]
        self.ip_send = _ip_send
        self.port_send = _port_send

class Node:
    def __init__(self, _uid, _nodenum, _ip, _port):
        self.uid = _uid
        self.node_num = _nodenum
        self.dist = math.inf
        self.ip = _ip
        self.port = _port
        self.out_edges = []
        self.send_thread = []
        self.send_flag = False
        self.receive_thread = []

        threadmainserver = threading.Thread(target=self.server, args=())
        threadmainserver.daemon = True
        threadmainserver.start()

    def connect(self):
        for item in self.out_edges:
            client_socket = socket.socket()
            client_socket.connect((item.ip_send, item.port_send))
            self.send_thread.append(client_socket)
        threadmainsend = threading.Thread(target=self.send, args=())
        threadmainsend.daemon = True
        threadmainsend.start()
        if self.dist == 0:
            self.send_flag = True

    def send(self):
        while True:
            if self.send_flag:
                for i in range(len(self.send_thread)):
                    threadDelayedSend = threading.Thread(target=self.DelayedSend, args=([i]))
                    threadDelayedSend.daemon = True
                    threadDelayedSend.start()
                self.send_flag = False

    def DelayedSend(self, idx):
        time.sleep(int(self.out_edges[idx].delay[0]))
        self.send_thread[idx].send(str(self.dist + self.out_edges[idx].weight).encode())

    def server(self):
        server_socket = socket.socket()
        server_socket.bind((self.ip, self.port))
        while True:
            server_socket.listen(2)
            conn, address = server_socket.accept()
            self.receive_thread.append(self.ServerThread(conn, address, self))

    class ServerThread:
        def __init__(self, _conn, _address, _outself):
            self.address = _address
            self.conn = _conn
            self.outself = _outself
            threadlisten = threading.Thread(target=self.listen, args=())
            threadlisten.daemon = True
            threadlisten.start()

        def listen(self):
            while True:
                data = self.conn.recv(1024)
                if not data:
                    break
                if int(data) < self.outself.dist:
                    self.outself.dist = int(data)
                    self.outself.send_flag = True

# ------------------------ main
data = []
totalDelay = 0
while True:
    n  = input()
    if n  == "":
        print("done")
        break
    else:
        tmp = n.split()
        tmp = [int(x) for x in tmp]
        totalDelay = totalDelay + tmp[3]
        data.append(tmp)

# info extraction from input
uid_list = []
for item in data:
    uid_list.append(item[0])
    uid_list.append(item[1])
uid_list = list(set(uid_list))
node_num = len(uid_list)

# ip, port generator
suffix = 1
InitIp = "127.0.0."
InitPort = 5000
ip_list = []
port_list = []
for i in range(node_num):
    ip_list.append(InitIp + str(suffix))
    port_list.append(InitPort + i)
    suffix = suffix + 1

# creating a list of nodes and start listening
node_list = []
for i in range(node_num):
    node_list.append(Node(uid_list[i], node_num, ip_list[i], port_list[i]))

# initializing the graph
first = True
for item in data:
    if first:
        node_list[uid_list.index(item[0])].dist = 0
        first = False
    node_list[uid_list.index(item[0])].out_edges.append(Edge(item[1], item[2], item[3], ip_list[uid_list.index(item[1])], port_list[uid_list.index(item[1])]))

print("Serevers up")

# start connections
for item in node_list:
    item.connect()

print("Connections Ready")

# Waiting
print("Please wait")
time.sleep(totalDelay)

# output
for item in node_list:
    print(str(item.uid) + ": " + str(item.dist))