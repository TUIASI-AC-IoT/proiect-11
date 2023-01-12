import socket, queue as q, Message as ms, ControllerEvent as ev
import threading, select, random, time

import ControllerCommand

serverIp = '127.0.0.1'
serverPort = 5683

clientPort = 25575

# Communication type by default CON
Com_Type = ms.Type.Confirmable

# default path were files would be stored
DownloadPath = "~/Downloads"


class CommunicationController:
    __ACK_TIMEOUT = 2  # s
    __MAX_RETRANSMIT = 4
    __ACK_RANDOM_FACTOR = 5

    # Because no negotiation this time
    __MAX_SZX = 6
    __MAX_BLOCK = 2 ^ (__MAX_SZX + 4)

    __msgIdValue = random.randint(0, 0xFFFF)
    __tknValue = random.randint(0, 0XFFFF_FFFF_FFFF)

    def __init__(self, cmdQueue: q.Queue, eventQueue: q.Queue):
        self.__sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__sk.bind(('0.0.0.0', clientPort))

        # Communication with GUI queues
        self.__cmdQueue = cmdQueue
        self.__eventQueue = eventQueue

        # sender socket lock
        self.__sendLock = threading.Lock()

        #
        self.__reqList = list()

        #
        self.__delayedReq = list()
        self.__blockWiseReq = list()
        self.__resQueue = q.Queue()

    def start(self):
        threading.Thread(target=self.listen_for_command, daemon=True).start()
        threading.Thread(target=self.receive_responses, daemon=True).start()
        threading.Thread(target=self.resolve_response, daemon=True).start()

    def send_request(self, message):
        with self.__sendLock:
            self.__sk.sendto(message, (serverIp, serverPort))

    def refresh_lifetime(self):
        while True:
            for req in self.__reqList:  # req is a tuple of request message, timestamp, timeout and retransmit count
                if (time.time() - req[1]) > req[2]:
                    if req[3] > 0:
                        req[3] -= 1
                        req[2] *= self.__ACK_RANDOM_FACTOR
                        req[1] = time.time()
                    else:
                        self.__cmdQueue.put(
                            ev.ControllerEvent(ev.EventType.REQUEST_TIMEOUT, ms.Method(req[0].msgCode).name))
                        self.__reqList.remove(req)

    def listen_for_command(self):
        while True:
            command = self.__cmdQueue.get()

            msg: ms.Message = command.getDetails()
            msg.setMessageId(self.__msgIdValue)
            self.__msgIdValue = self.__msgIdValue + 1
            msg.setToken(self.__tknValue)
            self.__tknValue = self.__tknValue + 1
            self.send_request(msg.encode())
            self.__reqList.append((msg, time.time(), self.__ACK_TIMEOUT, 4))

            self.__cmdQueue.task_done()

    def receive_responses(self):
        while True:
            r, _, _ = select.select([self.__sk], [], [], 1)
            if r:
                data, _ = self.__sk.recvfrom(1024)
                msg = ms.Message()
                msg.decode(data)
                self.__resQueue.put(msg)

    def resolve_response(self):
        while True:
            msg_resp: ms.Message = self.__resQueue.get()
            self.__resQueue.task_done()

            msg_req = None
            # Searching to associate a response with a request
            if msg_resp.tk_len == 0:
                for msg in self.__reqList:
                    if msg_resp.msgId == msg[0].msgId:
                        msg_req = msg[0]
                        break
                if msg_req is not None:
                    if msg_resp.msgType == ms.Type.Acknowledgement:
                        self.__reqList.remove(msg_req)
                        self.__delayedReq.append(msg_req)
                continue
            else:
                for msg in self.__reqList:
                    if msg_resp.token == msg[0].token:
                        msg_req = msg[0]
                        break
                if msg_req is None:  # Might be a response from a delayed request
                    for msg in self.__delayedReq:
                        if msg_resp.token == msg.token:
                            msg_req = msg
                            break
                if msg_req is None:
                    continue  # No matching request for this response (might be a duplicate from a resolved request)

                # supposed req is always a method
                if msg_req.msgClass != ms.Class.Method:
                    continue

                # Creating events based on request - response types

                if msg_resp.msgClass == ms.Class.Success:
                    if msg_req.msgCode == ms.Method.GET and msg_resp.msgCode == ms.Success.Content:
                        if int.from_bytes(msg_resp.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          "big") == ms.Content_Format.PLAIN_TEXT:
                            # Matching for a ListDirectory-event
                            file_list = list()
                            index = 0
                            data = msg_resp.getPayload()
                            while index < len(data):
                                val_len = (data[index] & 0xfe) >> 1
                                file_type = data[index] & 0x01
                                name = data[index + 1:index + 1 + val_len].decode("ascii")
                                file_list.append((file_type, name))
                                index += 1 + val_len
                            uri = list()
                            for ur in msg_req.getOptionValList(ms.Options.URI_PATH):
                                uri.append(ur.decode("ascii"))
                            self.__eventQueue.put(ev.ControllerEvent(ev.EventType.FILE_LIST, (file_list, uri)))
                            continue
                        if int.from_bytes(msg_resp.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          "big") == ms.Content_Format.OCTET_STREAM:
                            # Matching for a FileDownloaded-event

                            location = list()
                            for lc in msg_resp.getOptionValList(ms.Options.LOCATION_PATH):
                                location.append(lc.decode("ascii"))

                            self.__eventQueue.put(ev.ControllerEvent(ev.EventType.FILE_CONTENT, location[-1]))
                            continue

                    if msg_req.msgCode == ms.Method.POST and (msg_resp.msgCode == ms.Success.Created or msg_resp.msgCode == ms.Success.Changed):

                        location = list()
                        for lc in msg_resp.getOptionValList(ms.Options.LOCATION_PATH):
                            location.append(lc.decode("ascii"))

                        # Matching for a FolderCreated-event
                        if int.from_bytes(msg_req.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          'big') == ms.Content_Format.PLAIN_TEXT:
                            event = ev.ControllerEvent(ev.EventType.FOLDER_CREATED, location)
                            self.__eventQueue.put(event)
                        # Matching for a FileUploaded-event
                        else:
                            event = ev.ControllerEvent(ev.EventType.FILE_UPLOADED, location)
                            self.__eventQueue.put(event)
                        continue

                    if msg_req.msgCode == ms.Method.PUT and msg_resp.msgCode == ms.Success.Changed:
                        # Matching for a FileRenamed-event
                        location = list()
                        for lc in msg_resp.getOptionValList(ms.Options.LOCATION_PATH):
                            location.append(lc.decode("ascii"))
                        event = ev.ControllerEvent(ev.EventType.RESOURCE_CHANGED, location)
                        self.__eventQueue.put(event)
                    if msg_req.msgCode == ms.Method.DELETE and msg_resp.msgCode == ms.Success.Deleted:
                        # Matching for a FileDeleted-event
                        uri = list()
                        for ur in msg_resp.getOptionValList(ms.Options.URI_PATH):
                            uri.append(ur.decode("ascii"))
                        event = ev.ControllerEvent(ev.EventType.FILE_DELETED, uri)
                        self.__eventQueue.put(event)
                        pass
                    if msg_req.msgCode == ms.Method.HEAD and msg_resp.msgCode == ms.Success.Content:
                        # Matching for a FileHeader-event
                        uri = list()
                        for ur in msg_resp.getOptionValList(ms.Options.URI_PATH):
                            uri.append(ur.decode("ascii"))
                        event = ev.ControllerEvent(ev.EventType.FILE_HEADER, (uri, msg_resp.getPayload().decode("ascii")))
                        self.__eventQueue.put(event)

                if msg_resp.msgClass == ms.Class.Client_Error:
                    err_msg = ms.Client_Error(msg_resp.msgCode).name
                else:
                    err_msg = ms.Server_Error(msg_resp.msgCode).name

                prompt = ms.Method(msg_req.msgCode).name + "request error: " + err_msg
                self.__eventQueue.put(ev.ControllerEvent(ev.EventType.REQUEST_FAILED, prompt))
