from enum import IntEnum


class EventType(IntEnum):
    FILE_LIST = 0
    FILE_CONTENT = 1
    FILE_HEADER = 2
    FOLDER_CREATED = 3
    FILE_UPLOADED = 4
    FILE_RENAMED = 5
    FILE_DELETED = 6
    REQUEST_FAILED = 7
    REQUEST_TIMEOUT = 8


class ControllerEvent:
    def __init__(self, eventType: EventType, data=None):
        self.eventType = eventType
        self.data = data
