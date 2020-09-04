'''
Sample Input:
5
1 2
3 1
2 1
5 3
4 1
----
5 nodes in the circular toplogy with arbitrary IDs
1st value in each line: node ID in clockwise order
1st value in each line: link delay detween that node and the next node
----
Every node prints each received message, 
at he end, the node with the greatest ID value is chosen as the leader
'''

import threading
import time
import queue
import socket


class Node(object):
    def __init__(self, nodeSize, uid, delay, IP_Bind, IP_Send, Port_Bind, Port_Send):
        self.q = queue.Queue(maxsize=nodeSize)
        self.nodeSize = nodeSize
        self.IP_Bind = IP_Bind
        self.IP_Send = IP_Send
        self.Port_Bind = Port_Bind
        self.Port_Send = Port_Send
        self.uid = uid
        self.delay = [int(delay)]
        self.flag = False
        self.status = 'unknown'
        # Start Clinet-Server with defined functionality on each node
        threadListen = threading.Thread(target=self.listen, args=())
        threadListen.daemon = True
        threadSend = threading.Thread(target=self.send, args=())
        threadSend.daemon = True
        threadListen.start()
        threadSend.start()

    def listen(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.IP_Bind, self.Port_Bind))
        server_socket.listen(10)
        conn, address = server_socket.accept()
        while True:
            data = conn.recv(self.nodeSize)
            if not data:
                break

            data = int(data)
            if int(data) >  0:
                print("Node " + str(self.uid) + " : received " + str(data))
                if int(data) > int(self.uid):
                    self.q.put(data)
                    threadDelay = threading.Thread(target=self.delayCount, args=(self.delay))
                    threadDelay.daemon = True
                    threadDelay.start()

                elif int(data) < int(self.uid):
                    pass

                elif int(data) == int(self.uid):
                    self.status = 'leader'
                    print("Node " + str(self.uid) + " : leader" + str(self.uid))
                    self.q.put(int(self.uid) * (-1))
                    threadDelay = threading.Thread(target=self.delayCount, args=(self.delay))
                    threadDelay.daemon = True
                    threadDelay.start()

            elif int(data) < 0:
                tmp2 = int(data) * (-1)
                if int(self.uid) != tmp2:
                    print("Node " + str(self.uid) + " : leader" + str(tmp2))
                    self.q.put(int(data))
                    threadDelay = threading.Thread(target=self.delayCount, args=(self.delay))
                    threadDelay.daemon = True
                    threadDelay.start()

                elif int(self.uid) == tmp2:
                    print("Node " + str(self.uid) + " : leader" + str(tmp2))
                    print("Election is over. Leader UID is " + str(tmp2))

    def send(self):
        time.sleep(2)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((self.IP_Send, self.Port_Send))

        self.q.put(int(self.uid))
        threadDelay = threading.Thread(target=self.delayCount, args=(self.delay))
        threadDelay.daemon = True
        threadDelay.start()
        while True:
            if self.flag == True:
                tmp = self.q.get()
                client_socket.send(str(tmp).encode())
                self.flag = False

    def delayCount(self, d):
        time.sleep(d)
        self.flag = True


# Main 
n = int(input())
suffix = 1
InitIp = "127.0.0"
InitPort = 5000

uid = []
delay = []
delay_sum = 0
for i in range(n):
    tmp1, tmp2 = input().split()
    uid.append(tmp1)
    delay.append(tmp2)
    delay_sum += int(delay[i])
for i in range(n):
    if i == n - 1:
        IP_Bind = InitIp + "." + str(suffix)
        Port_Bind = InitPort + 2 * i + 1
        IP_Send = InitIp + ".1"
        Port_Send = InitPort + 1
        Node(n, uid[i], delay[i], IP_Bind, IP_Send, Port_Bind, Port_Send)
        break
    IP_Bind = InitIp + "." + str(suffix)
    Port_Bind = InitPort + 2 * i + 1
    IP_Send = InitIp + "." + str(suffix + 1)
    Port_Send = InitPort + 2 * (i + 1) + 1
    suffix = suffix + 1
    Node(n, uid[i], delay[i], IP_Bind, IP_Send, Port_Bind, Port_Send)

time.sleep(n * n * delay_sum)
