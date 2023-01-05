import inspect

class ModelStatusSetting:
    """
    This class represents a setting for a model's status.

    :param id: The unique identifier for the model status setting.
    :param name: The name of the model status setting.
    """
    def __init__(self, id, name):
        self.id = id
        self.name = name

class MODEL_STATUS:
    """
    This class contains the possible settings for a model's status.
    """
    TRAIN = ModelStatusSetting(1, 'TRAIN')
    VALIDATE = ModelStatusSetting(2, 'VALIDATE')

    @staticmethod
    def by_id(id):
        """
        Returns the model status setting with the given id, or None if no such setting exists.

        :param id: The unique identifier of the model status setting to return.
        :return: The model status setting with the given id, or None if no such setting exists.
        :rtype: ModelStatusSetting or None
        """
        for k,v in MODEL_STATUS.__dict__.items():
            if isinstance(v,ModelStatusSetting) and v.id == id:
                return v
        return None

class MessageTypeSetting:
    """
    This class represents a setting for a message type.

    :param id: The unique identifier for the message type setting.
    :param name: The name of the message type setting.
    :param required_fields: A list of field names that are required for a message of this type.
    :param optional_fields: A list of field names that are optional for a message of this type.
    """
    def __init__(self, id, name, required_fields, optional_fields):
        self.id = id
        self.name = name
        self.required_fields = required_fields
        self.optional_fields = optional_fields

    def check_fields(self, msg_content):
        """
        Checks if the given message content contains all of the required fields for this message type.

        :param msg_content: A dictionary containing the fields and values for the message.
        :return: True if the message content contains all of the required fields, False otherwise.
        :rtype: bool
        """
        for field in self.required_fields:
            if field not in msg_content:
                return False
        return True

class MessageMainType:
    @staticmethod
    def by_id(id, cls):
        """
        Returns the message type setting with the given id from the given class, or None if no such setting exists.

        :param id: The unique identifier of the message type setting to return.
        :param cls: The class to search for the message type setting.
        :return: The message type setting with the given id, or None if no such setting exists.
        :rtype: MessageTypeSetting or None
        """
        for k,v in cls.__dict__.items():
            if isinstance(v,MessageTypeSetting) and v.id == id:
                return v
        return None


class DATA(MessageMainType):
    """
    This class contains the possible settings for a DATA message.
    """
    FORWARD = MessageTypeSetting('DATA/FORWARD','FORWARD',['DATA'],['ROOM'])
    GRADIENT = MessageTypeSetting('DATA/GRADIENT','GRADIENT',['DATA'],['ROOM'])
    REWARD = MessageTypeSetting('DATA/REWARD','REWARD',['DATA'],['ROOM'])
    TEXT = MessageTypeSetting('DATA/TEXT','TEXT',['DATA'],['ROOM'])
    CUSTOM = MessageTypeSetting('DATA/CUSTOM','CUSTOM',[],[])

class COMMAND(MessageMainType):
    """
    This class contains the possible settings for a COMMAND message.
    """
    REGISTER = MessageTypeSetting('COMMAND/REGISTER','REGISTER',['NAME'],[])
    DISCONNECT = MessageTypeSetting('COMMAND/DISCONNECT','DISCONNECT',[],[])
    JOINROOM = MessageTypeSetting('COMMAND/JOINROOM','JOINROOM',['ROOM'],[])
    LEAVEROOM = MessageTypeSetting('COMMAND/LEAVEROOM','LEAVEROOM',['ROOM'],[])
    ENABLELOGGING = MessageTypeSetting('COMMAND/ENABLELOGGING','ENABLELOGGING',[],['COMPONENT'])
    DISABLELOGGING = MessageTypeSetting('COMMAND/DISABLELOGGING','DISABLELOGGING',[],['COMPONENT'])
    SAVEMODELWEIGHTS = MessageTypeSetting('COMMAND/SAVEMODELWEIGHTS','SAVEMODELWEIGHTS',[],['WEIGHTS','COMPONENT'])
    LOADMODELWEIGHTS = MessageTypeSetting('COMMAND/LOADMODELWEIGHTS','LOADMODELWEIGHTS',[],['WEIGHTS','COMPONENT'])
    SAVESETTINGS = MessageTypeSetting('COMMAND/SAVESETTINGS','SAVESETTINGS',['SETTINGS'],['COMPONENT'])
    LOADSETTINGS = MessageTypeSetting('COMMAND/LOADSETTINGS','LOADSETTINGS',['SETTINGS'],['COMPONENT'])
    CUSTOM = MessageTypeSetting('COMMAND/CUSTOM','CUSTOM',[],[])

class LOG(MessageMainType):
    """
    This class contains the possible settings for a LOG message.
    """
    MODELWEIGHTS = MessageTypeSetting('LOG/MODELWEIGHTS','MODELWEIGHTS',['WEIGHTS', 'COMPONENT'],['DM'])
    SETTINGS = MessageTypeSetting('LOG/SETTINGS','SETTINGS',['SETTINGS', 'COMPONENT'],['DM'])
    MESSAGE = MessageTypeSetting('LOG/MESSAGES','MESSAGES',['MESSAGE', 'SENDER', 'ROOM'],[])
    KPI = MessageTypeSetting('LOG/KPI','KPI',['KPI', 'COMPONENT','TIME','VALUE'],[])
    RUN = MessageTypeSetting('LOG/RUN','RUN',['RUN'],['TYPE','STARTTIME','ENDTIME'])
    CUSTOM = MessageTypeSetting('LOG/CUSTOM','CUSTOM',[],[])
    
    
class MESSAGE_TYPE:
    """
    This class contains the possible settings for a message's main type.
    """
    DATA = DATA
    COMMAND = COMMAND
    LOG = LOG

    @staticmethod
    def by_id(id):
        """
        Returns the message type setting with the given id, or None if no such setting exists.

        :param id: The unique identifier of the message type setting to return.
        :return: The message type setting with the given id, or None if no such setting exists.
        :rtype: MessageTypeSetting or None
        """
        for k,v in MESSAGE_TYPE.__dict__.items():
            if inspect.isclass(v) and issubclass(v,MessageMainType):
                messagetype = v.by_id(id,v)
                if messagetype is not None:
                    return messagetype
        return None
