import os
import pickle
import threading
from socket import *
from threading import Semaphore



class PeerListener(threading.Thread):
    def __init__(self, addr, port, max_connection, id):
        host_name = gethostname()
        host_ip = gethostbyname(host_name)

        threading.Thread.__init__(self)
        self.id = id
        self.host = -1
        self.semaphore = Semaphore(max_connection)  # For Handling threads synchronization
        self.port = -1  # this port it will listen to
        self.sock = socket(AF_INET, SOCK_STREAM)
        self.sock.bind(('', 0))  # bind socket to address
        self.host, self.port = self.sock.getsockname()
        self.host = host_ip
        self.update_info(addr, port)
        self.sock.listen(max_connection)

    def run(self):
        while True:
            conn, addr = self.sock.accept()
            request = pickle.loads(conn.recv(1024))
            if request[0] == "DOWNLOAD":  # Organizing the path of file that will be shared

                cwd = os.getcwd()

                file_path = os.path.join(cwd, 'Shared')

                file_name = request[1]

                Full_path = os.path.join(file_path, file_name)
                self.semaphore.acquire()

                with open(Full_path, "rb") as myfile:       # Start Transfer File to Other Peer
                    while True:
                        l = myfile.read(4096)
                        while (l):
                            conn.send(l)
                            l = myfile.read(4096)
                        if not l:
                            myfile.close()
                            conn.close()
                            break
                self.semaphore.release()
            elif request[0] == "TERMINATE":
                conn.close()
                return
            else:
                continue

    def update_info(self, addr, port):
        s = socket(AF_INET, SOCK_STREAM)
        s.connect((addr, port))
        request = ["From_Listner", self.id, [self.host, self.port]]
        data = pickle.dumps(request)
        s.send(data)
        s.close()


def Start_PeerListener(addr, port, id):
    peer = PeerListener(addr, port, 5, id)  # Start Thread listen to peer_id to share the files with others Peers
    peer.start()
