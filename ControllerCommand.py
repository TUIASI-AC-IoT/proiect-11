import Message as ms, CommunicationController as ComC


class ControllerCommand:

    def __init__(self):
        self._message = None

    def getDetails(self):
        return self._message


class CreateFolder(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.POST)
        self._message.addOption(ms.Options.LOCATION_PATH, path)


class UploadFile(ControllerCommand):
    def __init__(self, path, file):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.POST)
        self._message.addOption(ms.Options.LOCATION_PATH, path)
        # self._message.addOption(ms.Options.CONTENT_FORMAT, path)


class RenameFile(ControllerCommand):
    def __init__(self, path, newName):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.PUT)
        self._message.addOption(ms.Options.LOCATION_PATH, path)
        self._message.addPayload(bytearray(newName, 'ascii'))


class MoveFile(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.PUT)
        self._message.addOption(ms.Options.LOCATION_PATH, path)
        # Maybe Uri change with Location


class DeleteFile(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.DELETE)
        self._message.addOption(ms.Options.LOCATION_PATH, path)


class ListFolder(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.GET)
        self._message.addOption(ms.Options.LOCATION_PATH, path)


class DownloadFile(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.GET)
        self._message.addOption(ms.Options.LOCATION_PATH, path)


class GetMetadata(ControllerCommand):
    def __init__(self, path):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.HEAD)
        self._message.addOption(ms.Options.LOCATION_PATH, path)
