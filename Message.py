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
    ACCEPT = 17
    BLOCK2 = 23
    BLOCK1 = 27
    # SIZE2 = 28
    # SIZE1 = 60


class Content_Format(IntEnum):
    PLAIN_TEXT = 0  # text/plain; charset=utf-8
    OCTET_STREAM = 42  # application/octet-stream


# Class for managing a CoAP message
class Message:
    __version = 1

    def __init__(self, msgType=None, msgClass=None, msgCode=None):
        self.msgType = msgType
        self.msgClass = msgClass
        self.msgCode = msgCode
        self.options = list()
        self.__payload = bytearray()

        self.msgId = None
        self.token = None
        self.tk_len = 0

    def encode(self):
        message = bytearray()

        # calculate token length
        if self.token != 0:
            for i in range(1, 8):
                if self.token < (1 << (i * 8)):
                    self.tk_len = i
                    break

        message.append(((self.__version << 6) + (self.msgType << 4) + self.tk_len))
        message.append((self.msgClass << 5) + self.msgCode)
        for b in self.msgId.to_bytes(2, 'big'):
            message.append(b)
        for b in self.token.to_bytes(self.tk_len, 'big'):
            message.append(b)

        # append options bytes
        prevOption = 0
        for (op, val) in self.options:
            valLen = len(val)

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
        if value is int:
            value = bytes(value, 'big')
        if value is str:
            value = bytes(value, 'ascii')

        self.options.append((option, value))

    def getOptionVal(self, opt: Options):
        res = None
        for (op, val) in self.options:
            if op == opt:
                res = val
                break

        return res

    def addPayload(self, content: bytearray):
        self.__payload = content

    def getPayload(self):
        return self.__payload

    def setMessageId(self, msgId):
        self.msgId = msgId

    def setToken(self, tkn):
        self.token = tkn

    def decode(self, data: bytes):
        if ((data[0] & 0xC0) >> 6) != self.__version:
            print(data[0] & 0xC0 >> 6)
            raise Exception("Invalid Version")

        self.msgType = (data[0] & 0x30) >> 4
        self.tk_len = data[0] & 0x0F

        self.msgClass = (data[1] & 0xE0) >> 5
        self.msgCode = data[1] & 0x1F

        self.msgId = int.from_bytes(data[2:4], "big")

        # Parsing token

        if self.tk_len == 0:
            pass
        elif self.tk_len < 9:
            self.token = 0
            for byte in data[4:4 + self.tk_len]:
                self.token = (self.token << 8) | byte
        else:
            raise Exception("Use of reserved token length values!")

        # Parsing Options (Check RFC7252 page 18 for details)
        if len(data) > 4 + self.tk_len:
            index = 4 + self.tk_len
            opDeltaPrev = 0
            while index < len(data):
                opDelta = (data[index] & 0xF0) >> 4
                opLen = data[index] & 0x0F
                opVal = None
                if opDelta < 13:
                    opDeltaPrev += opDelta
                    if opLen < 13:
                        opVal = data[index + 1:index + 1 + opLen]
                        index += 1 + opLen
                    elif opLen == 13:
                        opLen = data[index + 1] + 13
                        opVal = data[index + 2:index + 2 + opLen]
                        index += 2 + opLen
                    elif opLen == 14:
                        opLen = int.from_bytes(data[index + 1:index + 3], "big") + 269
                        opVal = data[index + 3:index + 3 + opLen]
                        index += 3 + opLen
                    else:
                        raise Exception("Invalid option length value!")
                elif opDelta == 13:
                    opDeltaPrev += data[index + 1] + 13
                    if opLen < 13:
                        opVal = data[index + 2:index + 2 + opLen]
                        index += 2 + opLen
                    elif opLen == 13:
                        opLen = data[index + 2] + 13
                        opVal = data[index + 3:index + 3 + opLen]
                        index += 3 + opLen
                    elif opLen == 14:
                        opLen = int.from_bytes(data[index + 2:index + 4], "big") + 269
                        opVal = data[index + 4:index + 4 + opLen]
                        index += 4 + opLen
                    else:
                        raise Exception("Invalid option length value!")
                elif opDelta == 14:
                    opDeltaPrev += int.from_bytes(data[index + 1:index + 3], "big") + 269
                    if opLen < 13:
                        opVal = data[index + 3:index + 3 + opLen]
                        index += 3 + opLen
                    elif opLen == 13:
                        opLen = data[index + 3] + 13
                        opVal = data[index + 4:index + 4 + opLen]
                        index += 4 + opLen
                    elif opLen == 14:
                        opLen = int.from_bytes(data[index + 3:index + 5], "big") + 269
                        opVal = data[index + 5:index + 5 + opLen]
                        index += 5 + opLen
                    else:
                        raise Exception("Invalid option length value!")
                else:
                    if opLen == 15:
                        self.__payload = data[index + 1:len(data)]
                        break
                    else:
                        raise Exception("Invalid option length value!")

                self.addOption(opDeltaPrev, opVal)

            if index < len(data):
                self.__payload = data[index + 1:len(data)]
