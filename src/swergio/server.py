import socket
import threading
import json
from uuid import uuid4

from .messageType import MESSAGE_TYPE

reserved_rooms = ['_command','_logging']

class Server:
    def __init__(self, ip: str, port: int, format: str, header_length: int, enable_logging=True) -> None:
        """
        Initializes the server instance with given ip, port, format and header length

        :param ip: IP address of the server
        :type ip: str
        :param port: Port number of the server
        :type port: int
        :param format: Format of the message data
        :type format: str
        :param header_length: Length of the message header
        :type header_length: int
        :param enable_logging: Flag to enable logging of the messages
        :type enable_logging: bool
        """
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
        """
        Handles the incoming client connection and processes the messages

        :param client: Client connection instance
        :type client: socket.socket
        :param addr: IP address of the client
        :type addr: tuple
        """
        print(f"[NEW CONNECTION] {addr} connected.")
        try:
            connected = True
            name = ""
            while connected:
                message_header = client.recv(self.header_length)
                if not message_header:
                    break
                message_length = int(message_header.decode(self.format)) 

                full_message_received = False
                message = b''
                message_length_left = message_length
                while not full_message_received:
                    message += client.recv(message_length_left)
                    message_length_left = message_length - len(message)
                    if message_length_left <= 0:
                        full_message_received = True
            
                message = message.decode(self.format)

                try:
                    msg_content = json.loads(message)
                except:
                    print(message_length)
                    print(message)

                msg_type = MESSAGE_TYPE.by_id(msg_content["TYPE"])
                
                if msg_type == MESSAGE_TYPE.COMMAND.DISCONNECT:
                    connected = self.disconnect_client(client)
                    break

                if msg_type == MESSAGE_TYPE.COMMAND.REGISTER:
                    name = self.register_client(client, msg_content)
                    

                if msg_type == MESSAGE_TYPE.COMMAND.JOINROOM:
                    self.join_room(client, msg_content)
                    
                if msg_type == MESSAGE_TYPE.COMMAND.LEAVEROOM:
                    self.leave_room(client, msg_content)
                    
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
        """
        Registers the client with the given name
        :param client: Client connection instance
        :type client: socket.socket
        :param msg_content: Message content containing the name of the client
        :type msg_content: dict
        :return: Name of the registered client
        :rtype: str
        """
        print(f"[REGISTER] {msg_content['NAME']} is registering...")
        name = msg_content["NAME"]
        with self.clients_lock:
            self.names[client] = name
        return name

    def disconnect_client(self, client):
        """
        Disconnects the given client from the server
        :param client: Client connection instance
        :type client: socket.socket
        :return: False to indicate disconnection
        :rtype: bool
        """
        return False

    def join_room(self, client, msg_content):
        """
        Adds the given client to the specified room
        :param client: Client connection instance
        :type client: socket.socket
        :param msg_content: Message content containing the name of the room
        :type msg_content: dict
        """
        room = msg_content["ROOM"]
        with self.clients_lock:
            if room not in self.rooms:
                self.rooms[room] = set()
                print(f"[ROOM CREATED] {room}")
            if client not in self.rooms[room]:
                self.rooms[room].add(client)
                print(f"[CLIENT ADDED] {self.names[client]} to {room}")

    def leave_room(self, client, msg_content):
        """
        Removes the given client from the specified room
        :param client: Client connection instance
        :type client: socket.socket
        :param msg_content: Message content containing the name of the room
        :type msg_content: dict
        """
        room = msg_content["ROOM"]
        with self.clients_lock:
            if client in self.rooms[room]:
                self.rooms[room].remove(client)
                if len(self.rooms[room]) == 0:
                    del self.rooms[room]

    def broadcast_message(self, client,message_header,message, msg_content):
        """
        Broadcasts the given message to the intended recipients
        :param client: Client connection instance who sent the message
        :type client: socket.socket
        :param message_header: Header of the message
        :type message_header: bytes
        :param message: Message data
        :type message: str
        :param msg_content: Message content containing the recipient details
        :type msg_content: dict
        """
        print(f"[BROADCAST] {self.names[client]} sent a message.")
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
        """
        Sends the given message to the logging room
        :param msg_content: Message content to be logged
        :type msg_content: dict
        """
        print(f"[LOGGING] {msg_content['SENT_BY']} sent a message.")
        msg = {'ID': uuid4().hex, 'TO_ROOM': '_logging', 'TYPE': MESSAGE_TYPE.LOG.MESSAGE.id, 'MESSAGE': msg_content}
        msg = json.dumps(msg)
        message_encoded = msg.encode(self.format)
        message_header = f"{len(message_encoded):<{self.header_length}}".encode(self.format)
        for client in self.rooms['_logging']:
            client.sendall(message_header + message_encoded)

    def start(self):
        """
        Starts the server and listens for incoming client connections
        """
        print(f"[STARTING] Server is starting...")
        self.server.listen()
        while True:
            client, addr = self.server.accept()
            with self.clients_lock:
                self.clients.add(client)
            thread = threading.Thread(target=self.handle_client, args=(client,addr))
            thread.start()

