'''
Input Topology:
    <size_of_network>
    <node_id> <timeout1> <timeout2> <timeout3>
    // NEIGHBORS
    <node_id> <delay> 
    <node_id> <delay>
'''

import threading
import socket
import time
import json

class Message:
    def __init__(self, nid, type, value):
        self.nid = nid
        self.type = type
        self.value = value

class Node:
    class Message:
        def __init__(self, _nid, _type, _value):
            self.nid = _nid
            self.type = _type
            self.value = _value

    def __init__(self, _n, _id, _ip_bind, _port_bind, _outnbrs_id,_out_nbrs_ip, _out_nbrs_port, _delay, _timer):
        self.n = _n
        self.id = _id
        self.ip_bind = _ip_bind
        self.port_bind = _port_bind
        self.out_nbrs_id = _outnbrs_id
        self.out_nbrs_ip = _out_nbrs_ip
        self.out_nbrs_port = _out_nbrs_port
        self.delay = _delay
        self.timer = _timer
        self.send_thread = []

        self.status = "TryToBeLeader"
        # TryToBeLeader , SentLeaderRequest , SentProposedValue , FinalDecision , SentLeaderAck , SentProposalValueAck
        #POTENTIAL_LEADER, V_PROPOSE, V_DECIDE, POTENTIAL_LEADER_ACK, V_PROPOSE_ACK

        self.current_leader = 0
        self.accepted_value = []
        self.max_ballot = 0
        self.leader_ack_num = 0
        self.proposal_ack_num = 0
        self.leader_ack_values = []
        self.proposed_value = 0
        self.final_value = 0

        main_thread = threading.Thread(target=self.main, args=())
        main_thread.daemon = True
        main_thread.start()

    def main(self):
        server_thread = threading.Thread(target=self.server, args=())
        server_thread.daemon = True
        server_thread.start()
        time.sleep(0.1)
        connect_thread = threading.Thread(target=self.connect, args=())
        connect_thread.daemon = True
        connect_thread.start()

        # Timer for potential leader
        timer0 = threading.Timer(self.timer[0], self.potential_leader)
        timer0.start()

    def potential_leader(self):
        if self.status != "FinalDecision":
            timer0 = threading.Timer(self.timer[0], self.potential_leader)
            timer0.start()
            m = Message(str(self.id), "POTENTIAL_LEADER", str(self.max_ballot + 1) )
            self.max_ballot = self.max_ballot + 1
            byte_array = json.dumps(m.__dict__).encode("utf-8")
            for ii in range(len(self.send_thread)):
                delayed_send_thread = threading.Thread(target=self.delayed_send, args=(ii, byte_array))
                delayed_send_thread.daemon = True
                delayed_send_thread.start()
            self.status = "SentLeaderRequest"
            timer11 = threading.Timer(self.timer[1], self.potential_leader_fail)
            timer11.start()

    def potential_leader_fail(self):
        self.status = "TryToBeLeader"
        self.leader_ack_values = []
        self.leader_ack_num = 0
        self.proposed_value = 0

    def successful_leader_fail(self):
        self.status = "TryToBeLeader"
        self.leader_ack_values = []
        self.leader_ack_num = 0
        self.proposal_ack_num = 0

    def listen(self, conn):
        while True:
            data = conn.recv(1024)
            if not data:
                break
            else:
                msg_rec = Message(**json.loads(data, encoding="utf-8"))
                print("node " + str(self.id) + ":")
                print(msg_rec.nid + ",  " + msg_rec.type+ ",  " + msg_rec.value)

                msg_rec = Message(int(msg_rec.nid), msg_rec.type, [int(item) for item in msg_rec.value.split() ] )

                # answer to potential leader request
                if int(msg_rec.value[0]) > self.max_ballot and msg_rec.type == "POTENTIAL_LEADER" :
                    if len(self.accepted_value) == 0:
                        tmp = str(-1)
                    else:
                        self.accepted_value = [str(item) for item in self.accepted_value]
                        tmp = self.accepted_value[1] + " " + self.accepted_value[0]
                    m = Message(str(self.id), "POTENTIAL_LEADER_ACK", tmp)
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    idx = self.out_nbrs_id.index(msg_rec.nid)
                    delayed_send_thread = threading.Thread(target=self.delayed_send, args=(idx, byte_array))
                    delayed_send_thread.daemon = True
                    delayed_send_thread.start()
                    self.status = "SentLeaderAck"
                    self.current_leader = msg_rec.nid
                    self.max_ballot = msg_rec.value[0]

                # receive potential leader ack
                if msg_rec.type == "POTENTIAL_LEADER_ACK" and self.status == "SentLeaderRequest":
                    self.leader_ack_num = self.leader_ack_num + 1
                    if len(msg_rec.value) == 2:
                        self.leader_ack_values.append([int(item) for item in msg_rec.value])
                    # successful leader
                    if float(self.leader_ack_num) >= float((self.n - 1) / 2):
                        if self.leader_ack_values == []:
                            self.proposed_value = self.id * self.n
                        else:
                            maximum = 0
                            for ii, item in enumerate(self.leader_ack_values):
                                if item[1] > maximum:
                                    maximum = item[1]
                                    idx = ii
                            self.proposed_value = self.leader_ack_values[idx][0]
                        tmp0 = str(self.max_ballot)
                        tmp1 = str(self.proposed_value)
                        self.accepted_value = [tmp0, tmp1]
                        tmp = tmp0 + " " + tmp1
                        m = Message(str(self.id), "V_PROPOSE", tmp)
                        byte_array = json.dumps(m.__dict__).encode("utf-8")
                        for ii in range(len(self.send_thread)):
                            delayed_send_thread = threading.Thread(target=self.delayed_send, args=(ii, byte_array))
                            delayed_send_thread.daemon = True
                            delayed_send_thread.start()
                        self.status = "SentProposedValue"
                        timer22 = threading.Timer(self.timer[2], self.successful_leader_fail)
                        timer22.start()

                # answer to proposed value
                if msg_rec.type == "V_PROPOSE" and self.status == "SentLeaderAck":
                    self.accepted_value = [str(item) for item in msg_rec.value]
                    m = Message(str(self.id), "V_PROPOSE_ACK", str(-1))
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    idx = self.out_nbrs_id.index(msg_rec.nid)
                    delayed_send_thread = threading.Thread(target=self.delayed_send, args=(idx, byte_array))
                    delayed_send_thread.daemon = True
                    delayed_send_thread.start()
                    self.status = "SentProposalValueAck"

                # receive proposed value ack
                if msg_rec.type == "V_PROPOSE_ACK" and self.status == "SentProposedValue":
                    self.proposal_ack_num = self.proposal_ack_num + 1
                    # successful proposed value
                    if float(self.proposal_ack_num) >= float((self.n-1)/2):
                        m = Message(str(self.id), "V_DECIDE", str(self.proposed_value))
                    self.final_value = self.proposed_value
                    byte_array = json.dumps(m.__dict__).encode("utf-8")
                    for ii in range(len(self.send_thread)):
                        delayed_send_thread = threading.Thread(target=self.delayed_send, args=(ii, byte_array))
                        delayed_send_thread.daemon = True
                        delayed_send_thread.start()
                    self.status = "FinalDecision"


                # receive final value
                if msg_rec.type == "FinalDecision" and self.status == "SentProposalValueAck":
                    self.final_value = msg_rec.value
                    self.status = "FinalDecision"


    def server(self):
        server_socket = socket.socket()
        server_socket.bind((self.ip_bind, self.port_bind))
        while True:
            server_socket.listen(2)
            conn, address = server_socket.accept()
            listen_thread = threading.Thread(target=self.listen, args=([conn]))
            listen_thread.daemon = True
            listen_thread.start()

    def connect(self):
        for ii in range(len(self.out_nbrs_port)):
            client_socket = socket.socket()
            client_socket.connect((self.out_nbrs_ip[ii], self.out_nbrs_port[ii]))
            self.send_thread.append(client_socket)


    def delayed_send(self, idx, msg):
        time.sleep(self.delay[idx])
        self.send_thread[idx].send(msg)


# main
n = int(input())
out_nbr = []
timer = []
for i in range(n):
    neighbor = []
    for j in range(n):
        if j == 0:
            [ignore, timer1, timer2, timer3] = input().split()
        else:
            [nbr, delay] = input().split()
            neighbor.append([int(nbr), float(delay)])
    out_nbr.append(neighbor)
    timer.append([int(timer1), int(timer2), int(timer3)])

# ip, port generator
suffix = 1
InitIp = "127.0.0."
InitPort = 5000
ip_list = []
port_list = []
for i in range(n):
    ip_list.append(InitIp + str(i + 1))
    port_list.append(InitPort + i + 1)

# nodes
for i in range(n):
    out_nbr_id = []
    out_nbr_delay = []
    for j in range(n-1):
        out_nbr_id.append(out_nbr[i][j][0])
        out_nbr_delay.append(out_nbr[i][j][1])
    out_nbr_ip = [ip_list[i-1] for i in out_nbr_id]
    out_nbr_port = [port_list[i-1] for i in out_nbr_id]
    Node(n, i+1, ip_list[i], port_list[i], out_nbr_id, out_nbr_ip, out_nbr_port, out_nbr_delay, timer[i])

time.sleep(60)

