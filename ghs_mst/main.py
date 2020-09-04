'''
GHS MST
Read input from input.txt
Format: <head_node> <tail_node> <weight> <delay>
'''

import threading
import socket
import time
import json

class Message:
    def __init__(self, id, type, value):
        self.id = id
        self.type = type
        self.value = value

class Node:
    def __init__(self, _n, _id, _ip_bind, _port_bind, _out_nbr_id , _out_nbr_ip, _out_nbr_port, _edge_delay, _edge_weight):
        # self inf.
        self.n = _n
        self.id = _id
        self.ip_bind = _ip_bind
        self.port_bind = _port_bind
        # nbr inf.
        self.out_nbr_id = _out_nbr_id
        self.out_nbr_ip = _out_nbr_ip
        self.out_nbr_port = _out_nbr_port
        self.edge_delay = _edge_delay
        self.edge_weight = _edge_weight
        self.send_thread = []
        # protocol inf.
        self.out_nbr_basic = self.out_nbr_id
        self.out_nbr_rejected = []
        self.out_nbr_branch = []
        self.leaderId = self.id
        self.level = 0
        self.mode = 'sleep'
        self.mwoe = 0
        self.parent = 0
        self.mwoe_localCandidate = []
        self.mwoe_descCandidate = []
        self.connectSent = []
        self.connectRec = []
        self.flag_phase0 = 0
        self.notCompleted = False

        thread_main = threading.Thread(target=self.main, args=())
        thread_main.daemon = True
        thread_main.start()

    def main(self):

        thread_server = threading.Thread(target=self.server, args=())
        thread_server.daemon = True
        thread_server.start()

        time.sleep(0.1)

        thread_connect = threading.Thread(target=self.connect, args=())
        thread_connect.daemon = True
        thread_connect.start()

    def server(self):

        server_socket = socket.socket()
        server_socket.bind((self.ip_bind, self.port_bind))
        while True:
            server_socket.listen(2)
            conn, address = server_socket.accept()
            thread_listen = threading.Thread(target=self.listen, args=([conn]))
            thread_listen.daemon = True
            thread_listen.start()

    def connect(self):
        for ii in range(len(self.out_nbr_port)):
            m = Message(str(self.id), "hello", "null")
            byte_array = json.dumps(m.__dict__).encode("utf-8")
            client_socket = socket.socket()
            client_socket.settimeout(n * n * n)
            client_socket.connect((self.out_nbr_ip[ii], self.out_nbr_port[ii]))
            client_socket.send(byte_array)
            self.send_thread.append(client_socket)

    def start_protocol(self):
        self.mwoe = self.out_nbr_id[self.edge_weight.index(min(self.edge_weight))]
        thread_start = threading.Thread(target=self.start, args=())
        thread_start.daemon = True
        thread_start.start()

    def start(self):

        # phase 0
        time.sleep(0.2)
        m = Message(str(self.id), "connect", str(self.leaderId) + " , " + str(self.level))
        byte_array = json.dumps(m.__dict__).encode("utf-8")
        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(self.mwoe, byte_array))
        thread_delayed_send.daemon = True
        thread_delayed_send.start()
        self.mode = "search"

        while True:

            if self.flag_phase0 == 0:
                time.sleep(3)
            else:
                time.sleep(3 * n + 5)  # periodically

            if self.mode == "end":
                break
            self.flag_phase0 = self.flag_phase0 + 1

            # reset
            self.parent = 0
            self.mwoe_localCandidate = []
            self.mwoe_descCandidate = []
            self.connectSent = []
            self.connectRec = []
            self.notCompleted = False

            if self.id == self.leaderId: # if leader

                if len(self.out_nbr_branch) > 0: # has some tree nbr --- send initiate ..................................

                    m = Message(str(self.id), "initiate", str(self.leaderId) + " , " + str(self.level) )
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    for item2 in self.out_nbr_branch: # tell branch nbrs to initiate
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item2, byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                    if len(self.out_nbr_basic) > 0: #  some basic nbr --- send test
                        m = Message(str(self.id), "test", str(self.leaderId) + " , " + str(self.level))
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        for item6 in self.out_nbr_basic:
                            thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item6, byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()

                    thread_mwoe_wait = threading.Thread(target=self.mwoe_wait, args=())  # wait for mwoe answer
                    thread_mwoe_wait.daemon = True
                    thread_mwoe_wait.start()

                else: # left behind .....................................................................................
                    m = Message(str(self.id), "test", str(self.leaderId) + " , " + str(self.level))
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    for item in  self.out_nbr_basic:
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item, byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                    thread_single_component = threading.Thread(target=self.single_component, args=())
                    thread_single_component.daemon = True
                    thread_single_component.start()

    def listen(self, conn):
        in_id = 0
        while True:
            data = conn.recv(1024)
            if not data:
                break
            else:
                msg_rec = Message(**json.loads(data, encoding="utf-8"))

                if msg_rec.type == "hello": # setup negotiation -----------------------------------------------------------------------------------------------
                    in_id = int(msg_rec.id)

                if msg_rec.type == "connect": # -------------------------------------------------------------------------------------------------------------
                    tmp8 = msg_rec.value.split(",")
                    tmp8 = int(tmp8[1])

                    if self.level == 0 and tmp8 == 0: # phase 0
                        if int(msg_rec.id) == self.mwoe: # Merge :)
                            self.out_nbr_basic.remove(int(msg_rec.id))
                            self.out_nbr_branch.append(int(msg_rec.id))
                            self.level = self.level + 1
                            if int(msg_rec.id) > int(self.id):
                                self.leaderId = int(msg_rec.id)

                    elif self.flag_phase0 > 0:
                        tmp8 = msg_rec.value.split(",")
                        if int(tmp8[1]) < self.level: # add branch to single component
                            self.out_nbr_branch.append(int(msg_rec.id))
                            self.out_nbr_basic.remove(int(msg_rec.id))
                        else:
                            self.connectRec = [int(msg_rec.id)]

                if msg_rec.type == "initiate": # -------------------------------------------------------------------------------------------------------------

                    tmp = msg_rec.value.split(",")

                    self.parent = in_id
                    self.level = int(tmp[1])
                    self.leaderId = int(tmp[0])

                    for item3 in self.out_nbr_branch: #rebroadcast
                        if item3 != self.parent:

                            m = Message(self.id, "initiate", tmp[0] + " , " + tmp[1])
                            byte_array = json.dumps(m.__dict__).encode("utf-8")
                            thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item3, byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()

                    for item4 in self.out_nbr_basic: # test
                        m = Message(str(self.id), "test", str(self.leaderId) + " , " + str(self.level))
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item4, byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                    thread_mwoe_wait = threading.Thread(target=self.mwoe_wait, args=()) # wait for mwoe answer
                    thread_mwoe_wait.daemon = True
                    thread_mwoe_wait.start()

                if msg_rec.type == "test": # -------------------------------------------------------------------------------------------------------------
                    tmp = msg_rec.value.split(",")

                    time.sleep(0.2)

                    if int(tmp[1]) == self.level:
                        if int(tmp[0]) == self.leaderId: # same component
                            if self.out_nbr_basic.count(int(msg_rec.id)) > 0:
                                self.out_nbr_basic.remove(int(msg_rec.id))
                            self.out_nbr_rejected.append(int(msg_rec.id))
                            m = Message(str(self.id), "reject", "None")
                            byte_array = json.dumps(m.__dict__).encode("utf-8")
                            thread_delayed_send = threading.Thread(target=self.delayed_send, args=(int(msg_rec.id), byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()

                        else: #merge
                            m = Message(str(self.id), "accept", str(self.leaderId) + " , " + str(self.level))
                            byte_array = json.dumps(m.__dict__).encode("utf-8")
                            thread_delayed_send = threading.Thread(target=self.delayed_send,args=(int(msg_rec.id), byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()

                    elif int(tmp[1]) < self.level: #to be absorbed
                        m = Message(str(self.id), "accept", str(self.leaderId) + " , " + str(self.level))
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send,
                                                               args=(int(msg_rec.id), byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                    else: # left behind
                        pass

                if msg_rec.type == "reject": # -------------------------------------------------------------------------------------------------------------
                    tmp = int(msg_rec.id)
                    if self.out_nbr_basic.count(tmp) > 0:
                        self.out_nbr_basic.remove(tmp)
                    if self.out_nbr_rejected.count(tmp) > 0:
                        self.out_nbr_rejected.append(tmp)

                if msg_rec.type == "accept": # -------------------------------------------------------------------------------------------------------------
                    tmp = msg_rec.value.split(',')
                    self.mwoe_localCandidate.append(
                        [int(msg_rec.id), self.edge_weight[self.out_nbr_id.index(int(msg_rec.id))], int(tmp[1])])

                if msg_rec.type == "report": # -------------------------------------------------------------------------------------------------------------

                    tmp3 = msg_rec.value.split(",")
                    if len(tmp3) > 1:
                        self.mwoe_descCandidate.append([tmp3[0], int(tmp3[1]), int(tmp3[2])])
                    elif int(tmp3[0]) == self.n * self.n:
                        self.notCompleted = True

                if msg_rec.type == "end": # -------------------------------------------------------------------------------------------------------------
                    self.parent = int(msg_rec.id)
                    self.mode = "end"
                    m = Message(str(self.id), "end", "None")
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    for item9 in self.out_nbr_branch:
                        if item9 != self.parent:
                            thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item9, byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()
                    return

                if msg_rec.type == "change_root": # -------------------------------------------------------------------------------------------------------------
                    tmp4 = msg_rec.value.split()

                    if len(tmp4) == 1: # border vertex

                        nxt_hop = tmp4[0]

                        m = Message(str(self.id), "connect", str(self.leaderId) + " , " + str(self.level))
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(int(nxt_hop), byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                        self.connectSent = [int(nxt_hop)]

                        # wait to check for merge
                        thread_connect_check = threading.Thread(target=self.connect_check, args=())
                        thread_connect_check.daemon = True
                        thread_connect_check.start()

                    else:
                        item9 = ""
                        for item9 in tmp4[0]:
                            pass
                        nxt_hop = item9
                        tmp4[0].remove(nxt_hop)
                        tmp5 = ""
                        for item8 in tmp4[0]:  # regenerate path
                            tmp5 = tmp5 + " " + item8
                        m = Message(str(self.id), "change_root", tmp4)
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(nxt_hop, byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                if msg_rec.type == "far_absorb":
                    tmp4 = msg_rec.value.split()

                    if len(tmp4) == 1:  # border vertex
                        nxt_hop = tmp4[0]
                        m = Message(str(self.id), "connect", str(self.leaderId) + " , " + str(self.level))
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(int(nxt_hop), byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

                        self.out_nbr_basic.remove(int(nxt_hop))
                        self.out_nbr_branch.append(int(nxt_hop))

                    else:
                        item9 = ""
                        for item9 in tmp4[0]:
                            pass
                        nxt_hop = item9
                        tmp4[0].remove(nxt_hop)
                        tmp5 = ""
                        for item8 in tmp4[0]:  # regenerate path
                            tmp5 = tmp5 + "far_absorb" + item8
                        m = Message(str(self.id), "", tmp4)
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(nxt_hop, byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()

    def connect_check(self):

        time.sleep( 8.1 )

        if len(self.connectRec) == 1 and len(self.connectSent) == 1 and self.connectRec[0] == self.connectSent[0]:
            self.level = self.level + 1
            if self.out_nbr_branch.count(int(self.connectSent[0])) == 0:
                self.out_nbr_branch.append(int(self.connectSent[0]))
            if self.out_nbr_basic.count(int(self.connectSent[0])) > 0:
                self.out_nbr_basic.remove(int(self.connectSent[0]))

            if self.connectSent[0] < self.id:
                self.leaderId = self.id
            else:
                self.leaderId = 0

    def mwoe_wait(self):

        if self.id != self.leaderId: # not leader --------------------------------------------------------------------------------------------------------
            if len(self.out_nbr_branch) == 1: #leaf ................................

                time.sleep( 3.1 )

                if len(self.mwoe_localCandidate) == 0:  # no mwoe
                    if len(self.out_nbr_basic) == 0:
                        m = Message(str(self.id), "report", str(2 * self.n * self.n))
                    else:
                        m = Message(str(self.id), "report", str(self.n * self.n))

                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    thread_delayed_send = threading.Thread(target=self.delayed_send, args=(self.out_nbr_branch[0], byte_array))
                    thread_delayed_send.daemon = True
                    thread_delayed_send.start()

                else: # has mwoe
                    mwoe = self.n * self.n
                    tmp2 = []
                    for item5 in self.mwoe_localCandidate: # select mwoe
                        if item5[1] < mwoe:
                            tmp2 = item5
                            mwoe = int(item5[1])
                    m = Message(str(self.id), "report", str(tmp2[0]) + " " + str(self.id) + "," + str(tmp2[1]) + "," + str(tmp2[2]))
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    thread_delayed_send = threading.Thread(target=self.delayed_send, args=(self.out_nbr_branch[0], byte_array))
                    thread_delayed_send.daemon = True
                    thread_delayed_send.start()

            else: # wait for descendant ............................................
                time.sleep(n) # if received from descendant

                if len(self.mwoe_descCandidate) == 0 and len(self.mwoe_localCandidate) == 0:  # no mwoe

                    if self.notCompleted or len(self.out_nbr_basic) > 0:
                        m = Message(str(self.id), "report", str(self.n * self.n))
                    else:
                        m = Message(str(self.id), "report", str(2 * self.n * self.n))

                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    thread_delayed_send = threading.Thread(target=self.delayed_send, args=(self.parent, byte_array))
                    thread_delayed_send.daemon = True
                    thread_delayed_send.start()

                else: # has mwoe
                    mwoe = self.n * self.n
                    tmp2 = []
                    for item5 in self.mwoe_localCandidate:  # select mwoe
                        if int(item5[1]) < mwoe:
                            tmp2 = item5
                            mwoe = int(item5[1])

                    flag = False
                    for item6 in self.mwoe_descCandidate:
                        if item6[1] < mwoe:
                            flag = True
                            tmp2 = item6
                            mwoe = int(item6[1])

                    if flag: # adjust the path if needed
                        (str(self.id) + " mwoe: " + str(tmp2[0][0]))
                        tmp2[0] = tmp2[0] + str(self.id)
                        m = Message(str(self.id), "report", str(tmp2[0])  + "," + str(tmp2[1]) + "," + str(tmp2[2]))
                    else:
                        m = Message(str(self.id), "report", str(tmp2[0]) + " " + str(self.id) + "," + str(tmp2[1]) + "," + str(tmp2[2]))

                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    thread_delayed_send = threading.Thread(target=self.delayed_send, args=(self.parent, byte_array))
                    thread_delayed_send.daemon = True
                    thread_delayed_send.start()

        else: #  leader --------------------------------------------------------------------------------------------------------
            if len(self.out_nbr_branch) > 0:  # has some tree nbr --- wait for all
                time.sleep( (self.level + 1) * n  )

                mwoe = self.n * self.n
                tmp2 = []
                for item5 in self.mwoe_localCandidate:  # select mwoe
                    if item5[1] < mwoe:
                        tmp2 = item5
                        mwoe = int(item5[1])

                flag = False
                for item6 in self.mwoe_descCandidate:
                    if item6[1] < mwoe:
                        flag = True
                        tmp2 = item6
                        mwoe = int(item6[1])

                if mwoe == self.n * self.n : # no mwoe ++++++++++++++++++++
                    if len(self.out_nbr_basic) == 0 and not self.notCompleted:
                        self.mode = "end"
                        m = Message(str(self.id), "end", "None")
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        for item9 in self.out_nbr_branch:
                            thread_delayed_send = threading.Thread(target=self.delayed_send, args=(item9, byte_array))
                            thread_delayed_send.daemon = True
                            thread_delayed_send.start()
                        return

                    else:
                        return

                elif flag: # far mwoe ++++++++++++++++++++
                    if int(tmp2[2]) > self.level:
                        tmp2[0] = tmp2[0].split()
                        item7 = ""
                        for item7 in tmp2[0]:
                            pass
                        nxt_hop = item7
                        tmp2[0].remove(nxt_hop)
                        tmp4 = ""
                        for item8 in tmp2[0]:  # regenerate path
                            tmp4 = tmp4 + " " + item8

                        m = Message(str(self.id), "far_absorb", tmp4)
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(int(nxt_hop), byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()
                        self.leaderId = 0

                    else:
                        tmp2[0] = tmp2[0].split()
                        item7 = ""
                        for item7 in tmp2[0]:
                            pass
                        nxt_hop = item7
                        tmp2[0].remove(nxt_hop)
                        tmp4 = ""
                        for item8 in tmp2[0]: # regenerate path
                            tmp4 = tmp4 + " " + item8

                        m = Message(str(self.id), "change_root", tmp4)
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(int(nxt_hop), byte_array))
                        thread_delayed_send.daemon = True
                        thread_delayed_send.start()
                        self.leaderId = 0

                else: # near mwoe ++++++++++++++++++++
                    m = Message(str(self.id), "connect", str(self.leaderId) + " , " + str(self.level))
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    thread_delayed_send = threading.Thread(target=self.delayed_send, args=(tmp2[0], byte_array))
                    thread_delayed_send.daemon = True
                    thread_delayed_send.start()

                    self.connectSent = [tmp2[0]]
                    thread_connect_check = threading.Thread(target=self.connect_check, args=())
                    thread_connect_check.daemon = True
                    thread_connect_check.start()

                    # wait to check for merge
                    thread_connect_check = threading.Thread(target=self.connect_check, args=())
                    thread_connect_check.daemon = True
                    thread_connect_check.start()

    def delayed_send(self, idd, msg):
        self.out_nbr_id = [int(item) for item in self.out_nbr_id]
        idx = self.out_nbr_id.index(idd)
        time.sleep(self.edge_delay[idx])
        mmm = Message(**json.loads(msg, encoding="utf-8"))
        print([mmm.id, mmm.type, mmm.value, idd])
        self.send_thread[idx].send(msg)

    def single_component(self):

        time.sleep( 5 )
        # find mwoe
        mwoe = self.n * self.n
        tmp2 = []
        for item5 in self.mwoe_localCandidate:  # select mwoe
            if item5[1] < mwoe:
                tmp2 = item5
                mwoe = int(item5[1])

        # connect / branch
        if self.out_nbr_branch.count(tmp2[0]) == 0:
            self.out_nbr_branch.append(tmp2[0])
        self.out_nbr_basic.remove(tmp2[0])
        self.leaderId = 0

        m = Message(str(self.id), "connect", str(self.leaderId) + " , " + str(self.level))
        byte_array = json.dumps(m.__dict__).encode("utf-8")
        thread_delayed_send = threading.Thread(target=self.delayed_send, args=(tmp2[0], byte_array))
        thread_delayed_send.daemon = True
        thread_delayed_send.start()

# topology learning
f = open("input.txt", "r")

f1 = f.readlines()
nodes = set()
for x in f1:
    x = x.split()
    nodes.add(int(x[0]))
    nodes.add(int(x[1]))
nodes = [[x] for x in list(nodes)]
f = open("input.txt", "r")
f2 = f.readlines()
for x in f2:
    x = [int(x) for x in x.split()]
    nodes[x[0] - 1].append([x[1], x[2], x[3]])
    nodes[x[1] - 1].append([x[0], x[2], x[3]])

# ip, port generator
n = len(nodes)
suffix = 1
InitIp = "127.0.0."
InitPort = 5000
ip_list = []
port_list = []
for i in range(n):
    ip_list.append(InitIp + str(i + 1))
    port_list.append(InitPort + i + 1)

# nodes
nodes_object = []
for i in range(n):
    out_nbr_id = []
    edge_delay = []
    edge_weight = []
    for j in range(len(nodes[i]) - 1):
        out_nbr_id.append(nodes[i][j+1][0])
        edge_weight.append(nodes[i][j+1][1])
        edge_delay.append(nodes[i][j+1][2])
    out_nbr_ip = [ip_list[i-1] for i in out_nbr_id]
    out_nbr_port = [port_list[i-1] for i in out_nbr_id]
    nodes_object.append(Node(n, i+1, ip_list[i], port_list[i], out_nbr_id, out_nbr_ip, out_nbr_port, edge_delay, edge_weight))

for item in nodes_object:
    item.start_protocol()

time.sleep(120)

for item in nodes_object:
    print([item.id, item.out_nbr_basic, item.out_nbr_branch])
