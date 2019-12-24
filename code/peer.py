import pickle
import threading
import datetime
import socket
import os
import random
import PeerListener
import time
import sys

class Peer_Server:

    def __init__(self, addr, port, min_alive):


        self.first = True
        self.require_info = True
        self.list_all = False
        self.need_search = False
        self.need_download = False
        self.success_and_update = False

        self.files = []
        self.require_file = []
        self.desire_file = []

        self.peer_id = "need_ID"
        self.peer_port = -1
        self.host_ip = -1

        self.start_time = self.getTime()

        while True:
            if (self.getTime() - self.start_time) >= min_alive:
                self.request = [self.peer_id, "dc"]
                self.disconnect(addr, port)
                self.stop_listen(self.host_ip, self.peer_port)
                print("PEER {0} SHUTDOWN: HAS {1}".format(self.peer_id, len(self.files)))
                for i in self.files:
                    print("{0}    {1}".format(self.peer_id, i[0]))
                os._exit(0)
                return


            if self.first:
                self.first = False
                self.list_all = True
                self.peer_id = "need_ID"

                cwd = os.getcwd()
                shared = cwd + '/Shared'
                onlyfiles = [f for f in os.listdir(shared) if os.path.isfile(os.path.join(shared, f))]


                for f in onlyfiles:
                    file_size = os.stat(shared + '/' + f).st_size
                    n_chunk = file_size // 512
                    offset = file_size % 512
                    if offset > 0:
                        n_chunk += 1
                    self.files.append([f, n_chunk, file_size])

                self.request = [self.peer_id] + [["Waiting"]] + self.files
                self.registerInServer(addr, port)

                self.start_time = self.getTime()

                PeerListener.Start_PeerListener(addr, port, self.peer_id)

            if self.require_info:
                ret_data = self.require(addr, port)
                if ret_data == ["Waiting"]:
                    self.require_info = True
                else:
                    self.host_ip = ret_data[0]
                    self.peer_port = ret_data[1]
                    self.require_info = False

            elif self.list_all:
                ret_data = self.List_all(addr, port)
                for f in ret_data:
                    if f not in self.files:
                        self.require_file.append(f)
                if len(self.require_file) > 0:
                    self.list_all = False
                    self.need_search = True


            elif self.need_search:
                self.desire_file = self.SearchInServer(addr, port)  # Connect with server and send command to search for file name
                self.need_search = False
                self.need_download = True

                self.start_time = self.getTime()

            elif self.need_download:
                l = len(self.desire_file)
                i = 0
                while i < l:
                    file = self.desire_file[i]
                    if file[1] == ["Waiting"]:
                        flag = self.SearchAgain(file[0], addr, port)
                        if flag == ["False"]:
                            i += 1
                        else:
                            f = file[0][0]
                            n_chunk = file[0][1]
                            result = False
                            j = 0
                            while result == False:
                                if j >= len(flag):
                                    self.require_file.remove(file[0])
                                    break
                                info = flag[j]
                                ip = info[1]
                                n_port = info[2]
                                result = self.Download(ip, n_port, f, n_chunk, addr, port)
                                j += 1
                            self.desire_file.pop(i)
                            l -= 1
                    else:
                        f = file[0][0]
                        n_chunk = file[0][1]
                        infos = file[1]
                        result = False
                        j = 0
                        while result == False:
                            if j >= len(infos):
                                self.require_file.remove(file[0])
                                break
                            info = infos[j]
                            ip = info[1]
                            n_port = info[2]
                            result = self.Download(ip, n_port, f, n_chunk, addr, port)
                            j += 1
                        self.desire_file.pop(i)
                        l -= 1

                if self.desire_file == []:
                    self.need_download = False
                    self.success_and_update = True
                else:
                    self.need_download = True
                self.start_time = self.getTime()

            elif self.success_and_update:
                self.update(addr, port)
                for file in self.require_file:
                    self.files.append(file)
                self.require_file = []
                self.desire_file = []
                self.success_and_update = False
                self.list_all = True

                self.start_time = self.getTime()


    def getTime(self):
        return int(round(time.time()))


    def registerInServer(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        data = pickle.dumps(self.request)
        s.send(data)
        pID = s.recv(1024)
        self.peer_id = int(pID)
        state = s.recv(1024)
        s.close()


    def List_all(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        self.request = ["list_all_files", self.peer_id]
        data = pickle.dumps(self.request)
        s.send(data)
        ret_data = pickle.loads(s.recv(1024))
        s.close()
        return ret_data

    def require(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        self.request = ["require_info", self.peer_id]
        data = pickle.dumps(self.request)
        s.send(data)
        ret_data = pickle.loads(s.recv(1024))
        s.close()
        return ret_data


    def SearchInServer(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        self.request = ["need_files"] + self.require_file
        data = pickle.dumps(self.request)
        s.send(data)
        ret_data = pickle.loads(s.recv(1024)) # Return List of Files contain that name
        s.close()
        return ret_data

    def SearchAgain(self, file, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        self.request = ["search_again"] + [file]
        data = pickle.dumps(self.request)
        s.send(data)
        ret_data = pickle.loads(s.recv(1024)) # Return List of Files contain that name
        s.close()
        return ret_data

    def Download(self, pip, pport, file_name, n_chunk, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((pip, pport))
        except socket.error, exc:
            return False
        data = pickle.dumps(["DOWNLOAD", str(file_name), str(self.peer_id)])
        s.send(data)

        cwd = os.getcwd()

        file_path = os.path.join(cwd, 'Shared')  # Organizing the path of file that will be Download

        X = 0
        with open(os.path.join(file_path, file_name), 'wb') as myfile:
            while True:
                data = s.recv(4096)
                if not data:
                    myfile.close()
                    break
                myfile.write(data)
                self.update_chunk(addr, port, X, file_name, n_chunk)
                X += 1
        s.close()
        return True

    def update_chunk(self, addr, port, X, filename, n_chunk):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        request = ["chunk", self.peer_id, X, n_chunk, filename]
        data = pickle.dumps(request)
        s.send(data)
        s.close()
        return


    def update(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        self.request = [self.peer_id] + ["update_status"] + self.require_file
        data = pickle.dumps(self.request)
        s.send(data)
        s.close()

    def disconnect(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        data = pickle.dumps(self.request)
        s.send(data)
        s.close()

    def stop_listen(self, addr, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((addr, port))
        request = ["TERMINATE"]
        data = pickle.dumps(request)
        s.send(data)
        s.close()


def Start_Peer(args):

    tracker_addr = args[1]
    n_port = int(args[2])
    min_alive = int(args[3])
    peer = Peer_Server(tracker_addr, n_port, min_alive)  # Start New Peer


if __name__ == '__main__':
    Start_Peer(sys.argv)
