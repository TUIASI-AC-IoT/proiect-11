from enum import IntEnum


class Type(IntEnum):
    Confirmable = b'00'
    NonConfirmable = b'01'
    Acknowledgement = b'10'
    Reset = b'11'


class Class(IntEnum):
    Method = 0
    Success = 2
    Client_Error = 4
    Server_Error = 5


class Code(IntEnum):
    pass


class Method(Code):
    EMPTY = 0
    GET = 1
    POST = 2
    PUT = 3
    DELETE = 4
    HEAD = 8


class Success(Code):
    Created = 1
    Deleted = 2
    Valid = 3
    Changed = 4
    Content = 5


class Client_Error(Code):
    Bad_Request = 0
    Bad_Option = 2
    Not_Found = 4
    Method_Not_Allowed = 5
    Not_Acceptable = 6


class Server_Error(Code):
    Internal_server_error = 0
    Not_implemented = 1
    Bad_gateway = 2
    Service_unavailable = 3
    Gateway_timeout = 4


# Class for managing a CoAP message
class Message:
    __version = 1

    def __init__(self, msgType, msgClass, msgCode):
        self.__msgType = msgType
        self.__msgClass = msgClass
        self.__msgCode = msgCode
        self.__token = b'666'

    def encode(self):
        message = bytearray()
        message.append(((self.__version << 6) + (self.__msgType << 4) + len(self.__token)))
        message.append((self.__msgClass << 5) + self.__msgCode)
        return message

