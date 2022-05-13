import inspect

class ModelStatusSetting:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class MODEL_STATUS:
    TRAIN = ModelStatusSetting(1, 'TRAIN')
    VALIDATE = ModelStatusSetting(2, 'VALIDATE')

    @staticmethod
    def by_id(id):
        for k,v in MODEL_STATUS.__dict__.items():
            if isinstance(v,ModelStatusSetting) and v.id == id:
                return v
        return None


class MessageTypeSetting:
    def __init__(self,id,name,required_fields,optional_fields):
        self.id = id
        self.name = name
        self.required_fields = required_fields
        self.optional_fields = optional_fields

    def check_fields(self,msg_content):
        for field in self.required_fields:
            if field not in msg_content:
                return False
        #for field in self.optional_fields:
        #    if field not in msg_content:
        #        return False
        return True

class MessageMainType:
    @staticmethod
    def by_id(id,cls):
        for k,v in cls.__dict__.items():
            if isinstance(v,MessageTypeSetting) and v.id == id:
                return v
        return None

class DATA(MessageMainType):
    FORWARD = MessageTypeSetting('DATA/FORWARD','FORWARD',['DATA'],['ROOM'])
    GRADIENT = MessageTypeSetting('DATA/GRADIENT','GRADIENT',['DATA'],['ROOM'])
    REWARD = MessageTypeSetting('DATA/REWARD','REWARD',['DATA'],['ROOM'])
    TEXT = MessageTypeSetting('DATA/TEXT','TEXT',['DATA'],['ROOM'])
    CUSTOM = MessageTypeSetting('DATA/CUSTOM','CUSTOM',[],[])

class COMMAND(MessageMainType):
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
    MODELWEIGHTS = MessageTypeSetting('LOG/MODELWEIGHTS','MODELWEIGHTS',['WEIGHTS', 'COMPONENT'],['DM'])
    SETTINGS = MessageTypeSetting('LOG/SETTINGS','SETTINGS',['SETTINGS', 'COMPONENT'],['DM'])
    MESSAGE = MessageTypeSetting('LOG/MESSAGES','MESSAGES',['MESSAGE', 'SENDER', 'ROOM'],[])
    KPI = MessageTypeSetting('LOG/KPI','KPI',['KPI', 'COMPONENT','TIME','VALUE'],[])
    RUN = MessageTypeSetting('LOG/RUN','RUN',['RUN'],['TYPE','STARTTIME','ENDTIME'])
    CUSTOM = MessageTypeSetting('LOG/CUSTOM','CUSTOM',[],[])

class MESSAGE_TYPE:
    DATA = DATA 
    COMMAND = COMMAND
    LOG = LOG

    @staticmethod
    def by_id(id):
        for k,v in MESSAGE_TYPE.__dict__.items():
            #if inspect.isclass(v) and v.__name__ in ['DATA','COMMAND','LOG']:
            #print(v)
            #print(inspect.isclass(v))
            #if inspect.isclass(v):
            #    print(issubclass(v,MessageMainType))
            if inspect.isclass(v) and issubclass(v,MessageMainType):
                messagetype = v.by_id(id,v)
                #print(messagetype)
                if messagetype is not None:
                    return messagetype
        return None