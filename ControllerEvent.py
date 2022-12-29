from enum import IntEnum


class EventType(IntEnum):
    FILE_LIST = 0
    FILE_CONTENT = 1
    FILE_HEADER = 2
    USER_ERROR = 3
    SERVER_ADDRESS_ERROR = 4


class ControllerEvent:
    def __int__(self, eventType: EventType, data: bytearray):
        self.eventType = eventType
        self.data = data
