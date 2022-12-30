from enum import IntEnum


class EventType(IntEnum):
    FILE_LIST = 0
    FILE_CONTENT = 1
    FILE_HEADER = 2
    USER_ERROR = 3
    SERVER_ADDRESS_ERROR = 4
    REQUEST_TIMEOUT = 5


class ControllerEvent:
    def __init__(self, eventType: EventType, data=None):
        self.eventType = eventType
        self.data = data
