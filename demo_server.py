import pickle
import socket
import struct
import threading

class Server:
    def __init__(self):
        self.host = '71.56.5.98'
        self.port1 = 6000
        self.port2 = 6001
        self.addr1 = (self.host, self.port1)
        self.addr2 = (self.host, self.port2)

        self.jetbot1_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.jetbot1_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.jetbot1_sock.bind(self.addr1)
        self.jetbot1_sock.listen(1)
        print(f"Server bound @ {self.addr1}")

        self.jetbot2_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.jetbot2_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.jetbot2_sock.bind(self.addr2)
        self.jetbot2_sock.listen(1)
        print(f"Server bound @ {self.addr2}")

        self.target = 'person'
        self.mission_complete = 0

        self.hint = None
        # self.bot1_complete = False
        # self.bot2_complete = False

    def receive_mission_data(self, sock):
        in_data = b""
        payload_size = struct.calcsize("Q")

        while len(in_data) < payload_size:
            segment = sock.recv(20 * 2024)
            if not segment:
                break
            in_data += segment

        packed_msg_size = in_data[:payload_size]
        in_data = in_data[payload_size:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(in_data) < msg_size:
            in_data += sock.recv(12 * 1024)

        incoming_data = in_data[:msg_size]
        packet = pickle.loads(incoming_data)
        return packet

    def bot1_getdata(self):
        jetbot1, jetbot1_addr = self.jetbot1_sock.accept()
        print(f"Jetbot connected @ {jetbot1_addr}")
        with jetbot1:
            start = {"msg": "start"}
            packet = pickle.dumps(start)
            jetbot1.sendall(packet)

            while True:
                current_data = self.receive_mission_data(jetbot1)
                print(current_data)
                if self.target in current_data['object']:
                    hint_direction = current_data['direction']
                    self.hint = hint_direction
                    self.mission_complete += 1
                    out_data = pickle.dumps({"msg": "mission_complete",
                                             "hint": self.hint})
                    jetbot1.sendall(out_data)
                    break
                else:
                    out_data = pickle.dumps({"msg": "in progress",
                                             "hint": self.hint})
                    jetbot1.sendall(out_data)

            # while self.mission_complete != 2:
            #     pass
            # out_data = pickle.dumps({"msg": "start routine"})
            # jetbot1.sendall(out_data)

    def bot2_getdata(self):
        self.jetbot2, jetbot2_addr = self.jetbot2_sock.accept()
        print(f"Jetbot connected @ {jetbot2_addr}")
        with self.jetbot2 as jetbot2:
            start = {"msg": "start"}
            packet = pickle.dumps(start)
            jetbot2.sendall(packet)

            while True:
                current_data = self.receive_mission_data(jetbot2)
                print(current_data)
                if self.target in current_data['object']:
                    hint_direction = current_data['direction']
                    self.hint = hint_direction
                    self.mission_complete += 1
                    out_data = pickle.dumps({"msg": "mission_complete",
                                             "hint": self.hint})
                    jetbot2.sendall(out_data)
                    break
                else:
                    out_data = pickle.dumps({"msg": "in progress",
                                             "hint": self.hint})
                    jetbot2.sendall(out_data)

            # while self.mission_complete != 2:
            #     pass
            # out_data = pickle.dumps({"msg": "start routine"})
            # jetbot2.sendall(out_data)

s = Server()
s.bot1_getdata()
s.bot2_getdata()

out_data = pickle.dumps({"msg": "start routine"})
s.jetbot1.sendall(out_data)
s.jetbot2.sendall(out_data)
