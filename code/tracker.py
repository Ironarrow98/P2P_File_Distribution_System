import pickle
import threading
import datetime
import socket
import os
import random


class Tracker(threading.Thread):

    def __init__(self, max_connect):
        threading.Thread.__init__(self)
        # Open port file
        port_txt = open("port.txt", "w+")

        # Initialize TCP socket and bind to a randomly assigned avalible port
        self.TCP_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.TCP_socket.bind(('', 0))
        tracker_addr, tracker_port = self.TCP_socket.getsockname()
        
        
        # Write to file
        port_txt.write("%d\n" % tracker_port)
        port_txt.close()

        self.host = tracker_addr
        self.port = tracker_port
        self.semaphore = threading.Semaphore(max_connect)
        self.peer_ID = 0
        self.peer_ID_lock = threading.Lock()
        

        self.TCP_socket.listen(max_connect)

        self.files = {}
        self.pinfos = {}
        

    def run(self):
        while True:
            peer_TCP_socket, peer_TCP_addr = self.TCP_socket.accept()

            request = pickle.loads(peer_TCP_socket.recv(1024))
            


            # broadcast info to peer: ["list_all_files"]
            if request[0] == "list_all_files":
                
                self.semaphore.acquire()
                ret_data = pickle.dumps(self.all_data())
                peer_TCP_socket.send(ret_data)
                self.semaphore.release()

                peer_TCP_socket.close()
                
            elif request[0] == "require_info":
                pID = request[1]
                data = pickle.dumps(self.pinfos[pID])
                peer_TCP_socket.send(data)

            # peer first time connect
            elif request[0] == "need_ID":
                # send peer ID
                self.peer_ID_lock.acquire()
                self.peer_ID += 1
                peer_TCP_socket.send(str(self.peer_ID).encode())
                self.peer_ID_lock.release()
                
                
                request[0] = self.peer_ID

                self.semaphore.acquire()
                self.register(request)
                self.semaphore.release()

                print("PEER {0} CONNECT: OFFERS {1}".format(self.peer_ID, len(self.files[self.peer_ID])))
                for i in self.files[self.peer_ID]:
                    print("{0}    {1} {2}".format(self.peer_ID, i[0], i[2]))
                peer_TCP_socket.close()

            elif request[0] == "need_files":
                files_needed = request[1:]

                self.semaphore.acquire()
                ret_data = pickle.dumps(self.Search_data(files_needed))
                peer_TCP_socket.send(ret_data)
                self.semaphore.release()

                peer_TCP_socket.close()
                
            elif request[0] == "chunk":
                N = request[1]
                X = request[2]
                n_chunk = request[3]
                filename = request[4]
                print("PEER {0} ACQUIRED: CHUNK {1}/{2} {3}".format(N, X, n_chunk, filename))
                
                peer_TCP_socket.close()
                
            elif request[0] == "From_Listner":
                pID = request[1]
                info = request[2]
                self.semaphore.acquire()
                self.update_info(pID, info)
                self.semaphore.release()
                
                peer_TCP_socket.close()
                
            elif request[0] == "search_again":
                file = request[1]
                
                self.semaphore.acquire()
                ret_data = pickle.dumps(self.search_again(file))
                peer_TCP_socket.send(ret_data)
                self.semaphore.release()
                
                peer_TCP_socket.close()
                
            else:
                if request[1] == "update_status":
                
                    
                    pID = int(request[0])
                    update_files = request[2:]
                    
                    
                    self.semaphore.acquire()
                    self.update(pID, update_files)
                    peer_TCP_socket.send(ret_data)
                    self.semaphore.release()

                    peer_TCP_socket.close()
                    
                else:
                    pID = request[0]
                    
                    print("PEER {0} SHUTDOWN: HAS {1}".format(pID, len(self.files[pID])))
                    for i in self.files[pID]:
                        print("{0}    {1}".format(pID, i[0]))
                    
                    self.semaphore.acquire()
                    del self.files[pID]
                    del self.pinfos[pID]
                    self.semaphore.release()
                    
                    
                    peer_TCP_socket.close()


    def register(self, request):
        pID = int(request[0])
        info = request[1]
        file = request[2:]
        self.files[pID] = file
        self.pinfos[pID] = info
        
        
    def is_port_avaliable(self, host):
        result = -1
        v = self.pinfos.values()
        for i in v:
            if self.peer_port in i:
                return False
        if self.peer_port == self.port:
            return False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, self.peer_port))
        if result == 0:
            result = True
        else:
            result = False
        sock.close()
        return result
        
        
    def union(self, list):
        u = []
        for l in list:
            for ll in l:
                if ll not in u:
                    u.append(ll)
        return u


    def all_data(self):
        files = self.union(self.files.values())
        return files


    def Search_data(self, files):
        ret_data = []
        for f in files:
            info = []
            for k in self.files:
                if f in self.files[k] and (not (self.pinfos[k] == ["Waiting"])):
                    pID = [k]
                    pinfo = self.pinfos[k]
                    info.append(pID + pinfo)
            if info == []:
                info = ["Waiting"]
            ret_data.append([f, info])
        return ret_data
        
    def search_again(self, file):
        ret_data = []
        for k in self.files:
            if file in self.files[k] and (not (self.pinfos[k] == ["Waiting"])):
                pID = [k]
                pinfo = self.pinfos[k]
                ret_data.append(pID + pinfo)
        if ret_data == []:
            ret_data = ["False"]
        return ret_data
        
    def update(self, pID, update_files):
        self.files[pID].extend(update_files)
    
    
    def update_info(self, pID, info):
        self.pinfos[pID] = info







def Start_Tracker():
    stracker = Tracker(5)  # Start the Central Server
    stracker.start()




if __name__ == '__main__':
    Start_Tracker()
