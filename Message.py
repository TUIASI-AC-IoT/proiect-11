import random
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


class Options(IntEnum):
    LOCATION_PATH = 8
    URI_PATH = 11
    CONTENT_FORMAT = 12
    BLOCK2 = 23
    BLOCK1 = 27
    # SIZE2 = 28
    # SIZE1 = 60


# Class for managing a CoAP message
class Message:
    __version = 1

    def __init__(self, msgType, msgClass, msgCode, msgId):
        self.__msgId = int(random.random()*65535)
        self.__msgType = msgType
        self.__msgClass = msgClass
        self.__msgCode = msgCode
        self.__token = 666
        self.__options = list()
        self.__payload = bytearray()

    def encode(self):
        message = bytearray()

        # calculate token length
        tk_len = 0
        if self.__token != 0:
            for i in range(1, 8):
                if self.__token < 2**(i*8):
                    tk_len = i
                    break

        message.append(((self.__version << 6) + (self.__msgType << 4) + tk_len))
        message.append((self.__msgClass << 5) + self.__msgCode)
        for b in self.__msgId.to_bytes(2, 'big'):
            message.append(b)
        for b in self.__token.to_bytes(tk_len, 'big'):
            message.append(b)

        # append options bytes
        prevOption = 0
        for (op, val) in self.__options:
            if type(val) is str:
                valLen = len(val)
            else:
                for i in range(1, 8):
                    if val < 2 ** (i * 8):
                        valLen = i
                        break

            if (op - prevOption) < 13:
                if valLen < 13:
                    message.append(((op - prevOption) << 4) + valLen)
                elif valLen < 269:
                    message.append(((op - prevOption) << 4) + 13)
                    message.append(valLen - 13)
                else:
                    message.append(((op - prevOption) << 4) + 14)
                    message.append(valLen - 269)

                prevOption = op
            else:
                if valLen < 13:
                    message.append((13 << 4) + valLen)
                    message.append(op - prevOption - 13)
                elif valLen < 269:
                    message.append((13 << 4) + 13)
                    message.append(op - prevOption - 13)
                    message.append(valLen - 13)
                else:
                    message.append((13 << 4) + 14)
                    message.append(op - prevOption - 13)
                    message.append(valLen - 269)

                prevOption = op

            # append option value
            if type(val) is str:
                for b in bytes(val, 'ascii'):
                    message.append(b)
            else:
                for b in val.to_bytes(valLen, 'big'):
                    message.append(b)

        # append payload if exist
        if len(self.__payload) != 0:
            message.append(255)
            for b in self.__payload:
                message.append(b)

        return message

    def addOption(self, option, value):
        self.__options.append((option, value))

    def addPayload(self, content):
        self.__payload = content
