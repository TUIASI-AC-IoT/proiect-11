import Message as ms, CommunicationController as ComC


class ControllerCommand:
    extraData = None

    def __init__(self):
        self._message = None

    def getDetails(self):
        return self._message


class CreateFolder(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.POST)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)
        self._message.addOption(ms.Options.CONTENT_FORMAT, ms.Content_Format.PLAIN_TEXT.value)


class UploadFile(ControllerCommand):
    def __init__(self, path: list, file):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.POST)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)
        self._message.addOption(ms.Options.CONTENT_FORMAT, ms.Content_Format.OCTET_STREAM.value)

        # the syspath of the file
        extraData = file


class RenameFile(ControllerCommand):
    def __init__(self, path: list, newName):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.PUT)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)
        self._message.addPayload(bytearray(newName, 'ascii'))


class MoveFile(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.PUT)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)


class DeleteFile(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.DELETE)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)


class ListFolder(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.GET)
        # self._message.addOption(ms.Options.URI_PATH, path)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)


class DownloadFile(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.GET)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)


class GetMetadata(ControllerCommand):
    def __init__(self, path: list):
        super().__init__()
        self._message = ms.Message(ComC.Com_Type, ms.Class.Method, ms.Method.HEAD)
        for p in path:
            self._message.addOption(ms.Options.URI_PATH, p)
