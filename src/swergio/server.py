import socket
import threading
import json
from uuid import uuid4

from .messageType import MESSAGE_TYPE

reserved_rooms = ['_command','_logging']

class Server:
    def __init__(self,ip,port, format, header_length, enable_logging = True):
        self.ip = ip
        self.port = port
        self.format = format
        self.header_length = header_length
        self.enable_logging = enable_logging

        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((self.ip, self.port))

        self.clients = set()
        self.rooms = dict()
        for room in reserved_rooms:
            self.rooms[room] = set()
        self.names = dict()
        self.clients_lock = threading.Lock()

    def handle_client(self, client, addr):
        print(f"[NEW CONNECTION] {addr} connected.")
        try:
            connected = True
            name = ""
            while connected:
                message_header = client.recv(self.header_length)
                if not message_header:
                    break
                message_length = int(message_header.decode(self.format))
                #message = client.recv(message_length).decode(self.format)

                full_message_received = False
                message = b''
                message_length_left = message_length
                while not full_message_received:
                    message += client.recv(message_length_left) #.decode(self.format)
                    message_length_left = message_length - len(message)
                    if message_length_left <= 0:
                        full_message_received = True
            
                message = message.decode(self.format)

                #print(message_length)
                #print(message)
                        
                # handle event messages
                try:
                    msg_content = json.loads(message)
                except:
                    print(message_length)
                    print(message)
                #print(msg_content["TYPE"])
                msg_type = MESSAGE_TYPE.by_id(msg_content["TYPE"])
                #print(msg_type)
                #print(f"[{addr}] {message_length}")
                #print(f"[{addr}] {msg_content}")


                if msg_type == MESSAGE_TYPE.COMMAND.DISCONNECT:
                    connected = self.disconnect_client(client)
                    break

                if msg_type == MESSAGE_TYPE.COMMAND.REGISTER:
                    name = self.register_client(client, msg_content)
                    

                if msg_type == MESSAGE_TYPE.COMMAND.JOINROOM:
                    self.join_room(client, msg_content)
                    
                    # remove from room
                if msg_type == MESSAGE_TYPE.COMMAND.LEAVEROOM:
                    self.leave_room(client, msg_content)
                    
                # forward message to all clients
                self.broadcast_message(client,message_header,message, msg_content)

        finally:
            client.close()
            with self.clients_lock:
                self.clients.remove(client)
                for room in self.rooms:
                    if client in self.rooms[room]:
                        self.rooms[room].remove(client)
                self.names.pop(client)
            print(f"[{addr}] Disconnected.")

    def register_client(self,client,msg_content):
        print(f"[REGISTER] {msg_content['NAME']} is registering...")
        name = msg_content["NAME"]
        with self.clients_lock:
            self.names[client] = name
        return name

    def disconnect_client(self, client):
        return False

    def join_room(self, client, msg_content):
        # add to room
        room = msg_content["ROOM"]
        with self.clients_lock:
            if room not in self.rooms:
                self.rooms[room] = set()
                print(f"[ROOM CREATED] {room}")
            if client not in self.rooms[room]:
                self.rooms[room].add(client)
                print(f"[CLIENT ADDED] {self.names[client]} to {room}")

    def leave_room(self, client, msg_content):
        room = msg_content["ROOM"]
        with self.clients_lock:
            if client in self.rooms[room]:
                self.rooms[room].remove(client)
                if len(self.rooms[room]) == 0:
                    del self.rooms[room]

    def broadcast_message(self, client,message_header,message, msg_content):
        print(f"[BROADCAST] {self.names[client]} sent a message.")
        #print(msg_content)
        if 'SENT_BY' not in msg_content:
            msg_content['SENT_BY'] = self.names[client]
            message = json.dumps(msg_content)
            message_encoded = message.encode(self.format)
            message_header = f"{len(message_encoded):<{self.header_length}}".encode(self.format)

        with self.clients_lock:
            if "TO_ROOM" in msg_content:
                room = msg_content["TO_ROOM"]
                for other in self.rooms[room]:
                    if other != client:
                        other.sendall(message_header)
                        other.sendall(message.encode(self.format))
            if "TO" in msg_content:
                name = msg_content["TO"]
                for other in self.clients:
                    if self.names[other] == name:
                        other.sendall(message_header)
                        other.sendall(message.encode(self.format))
            if self.enable_logging:
                if MESSAGE_TYPE.by_id(msg_content["TYPE"]) in [MESSAGE_TYPE.DATA.FORWARD, MESSAGE_TYPE.DATA.GRADIENT]:
                    self.send_message_log(msg_content)

    def send_message_log(self, msg_content):
        print(f"[LOGGING] {msg_content['SENT_BY']} sent a message.")
        msg = {'ID': uuid4().hex, 'TO_ROOM': '_logging', 'TYPE': MESSAGE_TYPE.LOG.MESSAGE.id, 'MESSAGE': msg_content}
        msg = json.dumps(msg)
        message_encoded = msg.encode(self.format)
        message_header = f"{len(message_encoded):<{self.header_length}}".encode(self.format)
        #print(message_header)
        #print(f"{msg_content['SENT_BY']}: {msg_content['TYPE']} {msg_content['ID']}")        
        for client in self.rooms['_logging']:
            client.sendall(message_header + message_encoded)
            #client.sendall(message_encoded)
            #client.sendall(msg.encode(self.format))

    def start(self):
        print(f"[STARTING] Server is starting...")
        self.server.listen()
        while True:
            client, addr = self.server.accept()
            with self.clients_lock:
                self.clients.add(client)
            thread = threading.Thread(target=self.handle_client, args=(client,addr))
            thread.start()

