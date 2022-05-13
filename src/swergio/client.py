import socket
import json
import numpy as np
import uuid
import copy
import sys
import inspect
from .messageType import MESSAGE_TYPE

"""
Class for client to connect to server, send and receive messages
"""

reserved_rooms = ['_command']#,'_logging']

class Client:

    def __init__(self,name, server, port, format='utf-8', header_length=10, **kwargs):
        self.name = name
        self.server = server
        self.port = port
        self.format = format
        self.header_length = header_length
        self.eventHandlers = set()
        self.rooms = set()
        self.kwargs = kwargs

        self.client = self.connect(self.server, self.port)
        self.register()

    def connect(self, server, port):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server, port))
        return client
    
    def register(self):
        self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.REGISTER.id, 'NAME': self.name,'TO_ROOM':'_command'})
        # join default rooms
        for room in reserved_rooms:
            self.join_room(room)
    
    def send(self, message):
        message_encoded = json.dumps(message).encode(self.format)
        self.client.send(f"{len(message_encoded):<{self.header_length}}".encode(self.format))
        self.client.send(message_encoded)
    
    def receive(self):
        try:
            message_header = self.client.recv(self.header_length)
            if not len(message_header):
                return False
            message_length = int(message_header.decode(self.format))
            full_message_received = False
            message = b''
            message_length_left = message_length
            while not full_message_received:
                message += self.client.recv(message_length_left) #.decode(self.format)
                message_length_left = message_length - len(message)
                if message_length_left <= 0:
                    full_message_received = True
           
            message = message.decode(self.format)
            #print(f"{message_length} <-> {len(message.encode(self.format))}")
            if message_length !=  len(message.encode(self.format)):
                print(message)


            return json.loads(message)
        #except socket.error as e: 
        #    print ("Error receiving data: %s" % e) 
            #sys.exit(1) 
        #    return False
        except:
            return False

    def close(self):
        self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.DISCONNECT.id, 'TO_ROOM':'_command'})
        self.client.close()

    def add_eventHandler(self,handleFunction, responseType,responseRooms = None, responseComponent = None, trigger = None):
        responseRooms = responseRooms if responseRooms is None or type(responseRooms) is list else [responseRooms]
        
        # join trigger and response rooms
        if trigger is not None:
            for room in trigger.rooms:
                self.join_room(room)
        if responseRooms is not None:
            for room in responseRooms:
                self.join_room(room)
        self.eventHandlers.add(EventHandler(handleFunction, responseType,responseRooms,responseComponent, trigger))

    def join_room(self, room):
        if room not in self.rooms:
            self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.JOINROOM.id, 'ROOM': room,'TO_ROOM':'_command'})
            self.rooms.add(room)

    def listen(self):
        while True:
            message = self.receive()
            if message is not False:
                for eventHandler in self.eventHandlers:
                    if eventHandler.is_triggered(message):
                        responses = eventHandler.handle(message,**self.filter_dict(self.kwargs,eventHandler.handleFunction))
                        if responses is not None:
                            for response in responses:
                                self.send(self.add_propagated_fields(message,response))
            else:
                self.close()
                break

    def add_propagated_fields(self, message, response):
        if 'ROOT_ID' in message.keys() and 'ROOT_ID' not in response.keys():
            response['ROOT_ID'] = message['ROOT_ID']
        if 'MODEL_STATUS' in message.keys() and 'MODEL_STATUS' not in response.keys():
            response['MODEL_STATUS'] = message['MODEL_STATUS']
        if 'SENT_BY' not in response.keys():
            response['SENT_BY'] = self.name
        return response
                        
    def filter_dict(self,dict_to_filter, thing_with_kwargs):
        sig = inspect.signature(thing_with_kwargs)
        filter_keys = [param.name for param in sig.parameters.values() if param.kind == param.POSITIONAL_OR_KEYWORD]
        filtered_dict = {filter_key:dict_to_filter[filter_key] for filter_key in filter_keys if filter_key in dict_to_filter}
        return filtered_dict

class EventHandler:

    def __init__(self,handleFunction, responseType,responseRooms = None,responseComponent = None, trigger = None):
        responseRooms = responseRooms if responseRooms is None or type(responseRooms) is list else [responseRooms]
        self.handleFunction = handleFunction
        self.responseType = responseType
        self.responseRooms = responseRooms
        self.responseComponent = responseComponent
        self.trigger = trigger

    def is_triggered(self, message):
        if self.trigger is not None:
            return self.trigger.is_triggered(message)
        return False

    def handle(self,*args,**kwargs):
        #response_id = uuid.uuid4().hex
        response = self.handleFunction(*args,**kwargs)
        if response is None:
            return None
        if 'ID' not in response:
            response['ID'] = uuid.uuid4().hex
    
        if self.responseType is not None:
            response['TYPE'] = self.responseType.id

        if self.responseComponent is not None:
            response['TO'] = self.responseComponent
    
        responses = []
        if self.responseRooms is not None:
            for room in self.responseRooms:
                resp = copy.deepcopy(response)
                resp['TO_ROOM'] = room
                responses.append(resp)

        return responses

class Trigger:
    def __init__(self, types, rooms = None, directmessage = True):
        self.types = types if type(types) is list else [types]
        self.rooms = rooms if rooms is None or type(rooms) is list else [rooms]
        self.directmessage = directmessage

    def is_triggered(self, message):
        if MESSAGE_TYPE.by_id(message['TYPE']) in self.types:
            if self.rooms is not None and message['TO_ROOM'] in self.rooms:
                return True
            if self.directmessage and 'TO_ROOM' not in message.keys():
                return True
        return False

