import socket
import json
import uuid
import copy
import inspect
from .messageType import MESSAGE_TYPE

"""
Class for client to connect to server, send and receive messages
"""

reserved_rooms = ['_command']#,'_logging']

class Client:
    """
    This class defines a client, which can be used to connect to a server and send and
    receive messages.

    :param name: The name of the client.
    :param server: The IP address of the server.
    :param port: The port number of the server.
    :param format: The encoding format to use for messages.
    :param header_length: The length of the message header in bytes.
    :param kwargs: Additional keyword arguments that will be passed to event handler
                   functions when they are called.

    :ivar name: The name of the client.
    :ivar server: The IP address of the server.
    :ivar port: The port number of the server.
    :ivar format: The encoding format to use for messages.
    :ivar header_length: The length of the message header in bytes.
    :ivar eventHandlers: A set of `EventHandler` instances registered with this client.
    :ivar rooms: A set of rooms that the client has joined.
    :ivar kwargs: Additional keyword arguments that will be passed to event handler
                  functions when they are called.
    :ivar client: The socket used to connect to the server.
    """

    def __init__(self,name, server, port, format='utf-8', header_length=10, **kwargs):
        """
        Initialize a new `Client` instance with the given parameters.

        :param name: The name of the client.
        :param server: The IP address of the server.
        :param port: The port number of the server.
        :param format: The encoding format to use for messages.
        :param header_length: The length of the message header in bytes.
        :param kwargs: Additional keyword arguments that will be passed to event handler
                       functions when they are called.
        """
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
        """
        Connect to the server at the given IP address and port number.

        :param server: The IP address of the server.
        :param port: The port number of the server.
        :return: The socket used to connect to the server.
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((server, port))
        return client

    def register(self):
        """
        Register this client with the server. This will send a REGISTER command message
        to the server and join the reserved rooms.
        """
        self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.REGISTER.id, 'NAME': self.name,'TO_ROOM':'_command'})
        for room in reserved_rooms:
            self.join_room(room)

    def send(self, message):
        """
        Send the given message to the server.

        :param message: The message to send.
        """
        message_encoded = json.dumps(message).encode(self.format)
        self.client.send(f"{len(message_encoded):<{self.header_length}}".encode(self.format))
        self.client.send(message_encoded)

    def receive(self):
        """
        Receive a message from the server.

        :return: The received message, or False if an error occurred.
        """
        try:
            message_header = self.client.recv(self.header_length)
            if not len(message_header):
                return False
            message_length = int(message_header.decode(self.format))
            full_message_received = False
            message = b''
            message_length_left = message_length
            while not full_message_received:
                message += self.client.recv(message_length_left)
                message_length_left = message_length - len(message)
                if message_length_left <= 0:
                    full_message_received = True
           
            message = message.decode(self.format)
            if message_length !=  len(message.encode(self.format)):
                print(message)


            return json.loads(message)
        except:
            return False


    def close(self):
        """
        Close the connection to the server. This will send a DISCONNECT command message
        to the server and close the socket.
        """
        self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.DISCONNECT.id, 'TO_ROOM':'_command'})
        self.client.close()

    def add_eventHandler(self,handleFunction, responseType,responseRooms = None, responseComponent = None, trigger = None):
        """
        Add a new event handler to this client.

        :param handleFunction: The function to call when a message is handled by this event
                               handler. This function should take the same arguments as the
                               `handle` method of the `EventHandler` class and return a
                               response message, or None if no response is needed.
        :param responseType: The type of the response message.
        :param responseRooms: A list of room IDs where the response message should be sent.
                              If not specified, the response will be sent to the same room as
                              the original message.
        :param responseComponent: The component ID where the response message should be sent.
        :param trigger: A `Trigger` instance that specifies the criteria for triggering this
                        event handler. If not specified, the event handler will never be
                        triggered.
        """
        responseRooms = responseRooms if responseRooms is None or type(responseRooms) is list else [responseRooms]
        
        if trigger is not None:
            for room in trigger.rooms:
                self.join_room(room)
        if responseRooms is not None:
            for room in responseRooms:
                self.join_room(room)
        self.eventHandlers.add(EventHandler(handleFunction, responseType,responseRooms,responseComponent, trigger))

    def join_room(self, room):
        """
        Join the given room. This will send a JOINROOM command message to the server.

        :param room: The ID of the room to join.
        """
        if room not in self.rooms:
            self.send({'ID':uuid.uuid4().hex ,'TYPE': MESSAGE_TYPE.COMMAND.JOINROOM.id, 'ROOM': room,'TO_ROOM':'_command'})
            self.rooms.add(room)

    def listen(self):
        """
        Listen for incoming messages from the server and handle them using the registered
        event handlers. This method will block until the connection to the server is closed.
        """
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
        """
        Add the fields from the original message that should be propagated to the response
        message. This includes the root ID, the model status of the original message as 
        well as the name of the sender.

        :param message: The original message.
        :param response: The response message.
        :return: The updated response message.
        """
        if 'ROOT_ID' in message.keys() and 'ROOT_ID' not in response.keys():
            response['ROOT_ID'] = message['ROOT_ID']
        if 'MODEL_STATUS' in message.keys() and 'MODEL_STATUS' not in response.keys():
            response['MODEL_STATUS'] = message['MODEL_STATUS']
        if 'SENT_BY' not in response.keys():
            response['SENT_BY'] = self.name
        return response
                        
    # def filter_dict(self,dict_to_filter, thing_with_kwargs):
    #     """
    #     Filter the given dictionary and return a new dictionary containing only the keys
    #     that correspond to arguments of the given function.

    #     :param dictionary: The dictionary to filter.
    #     :param function: The function whose arguments should be used to filter the
    #                      dictionary.
    #     :return: The filtered dictionary.
    #     """
    #     sig = inspect.signature(thing_with_kwargs)
    #     filter_keys = [param.name for param in sig.parameters.values() if param.kind == param.POSITIONAL_OR_KEYWORD]
    #     filtered_dict = {filter_key:dict_to_filter[filter_key] for filter_key in filter_keys if filter_key in dict_to_filter}
    #     return filtered_dict
    
    def filter_dict(self,dictionary, function):
        """
        Filter the given dictionary and return a new dictionary containing only the keys
        that correspond to arguments of the given function.

        :param dictionary: The dictionary to filter.
        :param function: The function whose arguments should be used to filter the
                         dictionary.
        :return: The filtered dictionary.
        """
        return {k: v for k, v in dictionary.items() if k in inspect.getfullargspec(function).args}

class EventHandler:
    """
    This class defines an event handler, which can be used to handle messages that match
    certain criteria.

    :param handleFunction: The function to call when a message is handled by this event
                           handler. This function should take the same arguments as the
                           `handle` method of this class and return a response message, or
                           None if no response is needed.
    :param responseType: The type of the response message.
    :param responseRooms: A list of room IDs where the response message should be sent. If
                          not specified, the response will be sent to the same room as the
                          original message.
    :param responseComponent: The component ID where the response message should be sent.
    :param trigger: A `Trigger` instance that specifies the criteria for triggering this
                    event handler. If not specified, the event handler will never be
                    triggered.

    :ivar handleFunction: The function to call when a message is handled by this event
                          handler.
    :ivar responseType: The type of the response message.
    :ivar responseRooms: A list of room IDs where the response message should be sent.
    :ivar responseComponent: The component ID where the response message should be sent.
    :ivar trigger: A `Trigger` instance that specifies the criteria for triggering this
                   event handler.
    """
    def __init__(self,handleFunction, responseType,responseRooms = None,responseComponent = None, trigger = None):
        responseRooms = responseRooms if responseRooms is None or type(responseRooms) is list else [responseRooms]
        self.handleFunction = handleFunction
        self.responseType = responseType
        self.responseRooms = responseRooms
        self.responseComponent = responseComponent
        self.trigger = trigger

    def is_triggered(self, message):
        """
        Check if this event handler is triggered by the given message.

        :param message: The message to check.
        :return: True if the message matches the criteria specified for this event handler,
                 False otherwise.
        """
        if self.trigger is not None:
            return self.trigger.is_triggered(message)
        return False

    def handle(self,*args,**kwargs):
        """
        Handle the given message by calling the `handleFunction` specified in the
        constructor, and return a response message if needed.

        :param args: Positional arguments to pass to `handleFunction`.
        :param kwargs: Keyword arguments to pass to `handleFunction`.
        :return: A response message, or None if no response is needed.
        """
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
    """
    This class defines a trigger, which can be used to check if a given message matches
    certain criteria.

    :param types: A list of message types that should trigger this trigger.
    :param rooms: A list of room IDs that should trigger this trigger. If not specified,
                  the trigger will be triggered by messages in any room.
    :param directmessage: A boolean indicating whether direct messages (messages not
                          sent to a specific room) should trigger this trigger.

    :ivar types: A list of message types that should trigger this trigger.
    :ivar rooms: A list of room IDs that should trigger this trigger.
    :ivar directmessage: A boolean indicating whether direct messages should trigger this
                         trigger.
    """
    def __init__(self, types, rooms = None, directmessage = True):
        self.types = types if type(types) is list else [types]
        self.rooms = rooms if rooms is None or type(rooms) is list else [rooms]
        self.directmessage = directmessage

    def is_triggered(self, message):
        """
        Check if this trigger is triggered by the given message.

        :param message: The message to check.
        :return: True if the message matches the criteria specified for this trigger, False
                 otherwise.
        """
        if MESSAGE_TYPE.by_id(message['TYPE']) in self.types:
            if self.rooms is not None and message['TO_ROOM'] in self.rooms:
                return True
            if self.directmessage and 'TO_ROOM' not in message.keys():
                return True
        return False


