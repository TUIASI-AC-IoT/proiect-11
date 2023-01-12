import socket, queue as q, Message as ms, ControllerEvent as ev
import threading, select, random, time, os, copy

import ControllerCommand

serverIp = '127.0.0.1'
serverPort = 5683

clientPort = 25575

# Communication type by default CON
Com_Type = ms.Type.Confirmable

# default path were files would be stored
DownloadPath = "Downloads/"


class CommunicationController:
    __ACK_TIMEOUT = 2  # s
    __MAX_RETRANSMIT = 4
    __ACK_RANDOM_FACTOR = 5

    # Because no negotiation this time
    __MAX_SZX = 6
    __MAX_BLOCK = 1 << (__MAX_SZX + 4)

    __msgIdValue = random.randint(0, 0xFFFF)
    __tknValue = random.randint(0, 0XFFFF_FFFF)

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

        # (token, resourceName, (blocksID))
        self.__recvBlock = list()
        # (token , (blocksID))
        self.__sentBlock = list()

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
                        self.__sk.sendto(req[0], (serverIp, serverPort))
                    else:
                        self.__cmdQueue.put(
                            ev.ControllerEvent(ev.EventType.REQUEST_TIMEOUT, ms.Method(req[0].msgCode).name))
                        self.__reqList.remove(req)

    def listen_for_command(self):
        while True:
            command = self.__cmdQueue.get()

            msg: ms.Message = command.getDetails()

            if type(command) is ControllerCommand.UploadFile:
                file_path = command.extraData
                file_size = os.path.getsize(file_path)
                num = 0
                if file_size > self.__MAX_BLOCK:
                    # split
                    szx = self.__MAX_SZX
                    while file_size > self.__MAX_BLOCK:
                        msgd = copy.deepcopy(msg)
                        msgd.addOption(ms.Options.BLOCK1, (((num << 1) + 1) << 3) + szx)

                        with open(file_path, 'rb') as f:
                            f.seek(num << (szx + 4))
                            msgd.addPayload(f.read(self.__MAX_BLOCK))
                        msgd.setMessageId(self.__msgIdValue)
                        self.__msgIdValue = self.__msgIdValue + 1
                        msgd.setToken(self.__tknValue)

                        self.send_request(msgd.encode())
                        self.__reqList.append((msgd, time.time(), self.__ACK_TIMEOUT, 4))
                        num = num + 1
                        file_size = file_size - self.__MAX_BLOCK

                    msg.addOption(ms.Options.BLOCK1, (((num << 1) | 0) << 3) | szx)
                    with open(file_path, 'rb') as f:
                        f.seek(num << (szx + 4))
                        msg.addPayload(f.read(self.__MAX_BLOCK))

                    msg.setMessageId(self.__msgIdValue)
                    self.__msgIdValue = self.__msgIdValue + 1
                    msg.setToken(self.__tknValue)
                    self.__tknValue = self.__tknValue + 1

                    self.send_request(msg.encode())
                    self.__reqList.append((msg, time.time(), self.__ACK_TIMEOUT, 4))

                    self.__cmdQueue.task_done()
                    continue
                else:
                    with open(file_path, 'rb') as f:
                        msg.addPayload(f.read())

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
                data, _ = self.__sk.recvfrom(4096)
                msg = ms.Message()
                msg.decode(data)
                self.__resQueue.put(msg)

    def remove_req(self, req):
        for msg in self.__reqList:
            if req == msg[0]:
                self.__reqList.remove(msg)
                return

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
                        self.remove_req(msg_req)
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
                                name = data[index + 1:index + 1 + val_len].decode("utf-8")
                                file_list.append((file_type, name))
                                index += 1 + val_len
                            uri = list()
                            for ur in msg_req.getOptionValList(ms.Options.URI_PATH):
                                uri.append(ur.decode("utf-8"))
                            self.__eventQueue.put(ev.ControllerEvent(ev.EventType.FILE_LIST, (file_list, uri)))
                            self.remove_req(msg_req)
                            continue
                        if int.from_bytes(msg_resp.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          "big") == ms.Content_Format.OCTET_STREAM:
                            # Matching for a FileDownloaded-event

                            location = list()
                            for lc in msg_req.getOptionValList(ms.Options.URI_PATH):
                                location.append(lc.decode("utf-8"))

                            if msg_resp.getOptionVal(ms.Options.BLOCK2) is None:
                                with open(os.path.join(DownloadPath, location[-1]), 'wb') as f:
                                    f.write(msg_resp.getPayload())
                                    f.close()
                            else:
                                # receive blocks
                                block2 = int.from_bytes(msg_resp.getOptionVal(ms.Options.BLOCK2), 'big')
                                szx = block2 & 0x7
                                m = (block2 & 0x8) >> 3
                                num = block2 >> 4

                                file_path = os.path.join(DownloadPath, location[-1])
                                if num == 0:
                                    self.__recvBlock.append((msg_resp.token, file_path, list().append(0)))
                                else:
                                    for trz in self.__recvBlock:
                                        if trz[0] == msg_resp.token:
                                            file_path = trz[1]
                                            # trz[2].append(num)
                                            break

                                if not os.path.exists(file_path):
                                    with (open(file_path, 'w') as f):
                                        pass
                                with open(file_path, 'r+b') as f:
                                    f.seek(num << (szx + 4))
                                    f.write(msg_resp.getPayload())

                                if m == 1:
                                    num = num + 1
                                    nextBlock = ms.Message(Com_Type, ms.Class.Method, ms.Method.GET)
                                    nextBlock.token = msg_resp.token
                                    nextBlock.msgId = self.__msgIdValue
                                    self.__msgIdValue = self.__msgIdValue + 1
                                    nextBlock.addOption(ms.Options.BLOCK2, (num << 4) + szx)
                                    for op in msg_resp.getOptionValList(ms.Options.URI_PATH):
                                        nextBlock.addOption(ms.Options.URI_PATH, op)
                                    self.send_request(nextBlock.encode())
                                    self.__reqList.append((nextBlock, time.time(), self.__ACK_TIMEOUT, 4))
                                    self.remove_req(msg_req)
                                    continue

                            self.__eventQueue.put(ev.ControllerEvent(ev.EventType.FILE_CONTENT, location[-1]))
                            self.remove_req(msg_req)
                            continue

                    if msg_req.msgCode == ms.Method.POST and (
                            msg_resp.msgCode == ms.Success.Created or msg_resp.msgCode == ms.Success.Changed):
                        location = list()
                        for lc in msg_resp.getOptionValList(ms.Options.LOCATION_PATH):
                            location.append(lc.decode("utf-8"))

                        # Matching for a FolderCreated-event
                        if int.from_bytes(msg_req.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          'big') == ms.Content_Format.PLAIN_TEXT:
                            event = ev.ControllerEvent(ev.EventType.FOLDER_CREATED, location)
                            self.__eventQueue.put(event)
                            self.remove_req(msg_req)
                            continue
                        # Matching for a FileUploaded-event
                        if int.from_bytes(msg_req.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          'big') == ms.Content_Format.OCTET_STREAM:
                            # if msg_resp.getOptionVal(ms.Options.BLOCK1) is None:
                            #     for e in self.__sentBlock:
                            #         if
                            #     continue
                            #
                            # self.__sentBlock = list()

                            event = ev.ControllerEvent(ev.EventType.FILE_UPLOADED, location)
                            self.__eventQueue.put(event)
                            self.remove_req(msg_req)
                            continue

                    if msg_req.msgCode == ms.Method.PUT and msg_resp.msgCode == ms.Success.Changed:
                        # Matching for a FileRenamed-event
                        location = list()
                        for lc in msg_resp.getOptionValList(ms.Options.LOCATION_PATH):
                            location.append(lc.decode("utf-8"))
                        event = ev.ControllerEvent(ev.EventType.RESOURCE_CHANGED, location)
                        self.__eventQueue.put(event)
                        self.remove_req(msg_req)
                        continue
                    if msg_req.msgCode == ms.Method.DELETE and msg_resp.msgCode == ms.Success.Deleted:
                        # Matching for a FileDeleted-event
                        uri = list()
                        for ur in msg_req.getOptionValList(ms.Options.URI_PATH):
                            uri.append(ur.decode("utf-8"))
                        event = ev.ControllerEvent(ev.EventType.FILE_DELETED, uri)
                        self.__eventQueue.put(event)
                        self.remove_req(msg_req)
                        continue
                    if msg_req.msgCode == ms.Method.HEAD and msg_resp.msgCode == ms.Success.Content:
                        # Matching for a FileHeader-event
                        uri = list()
                        for ur in msg_resp.getOptionValList(ms.Options.URI_PATH):
                            uri.append(ur.decode("utf-8"))
                        event = ev.ControllerEvent(ev.EventType.FILE_HEADER,
                                                   (uri, msg_resp.getPayload().decode("utf-8")))
                        self.__eventQueue.put(event)
                        self.remove_req(msg_req)
                        continue

                if msg_resp.msgClass == ms.Class.Client_Error or msg_resp.msgClass == ms.Class.Server_Error:

                    prompt = ""
                    if (msg_resp.getOptionVal(ms.Options.BLOCK1) is None) and (
                            msg_resp.getOptionVal(ms.Options.BLOCK2) is None):
                        err_msg = ms.Class(msg_resp.msgClass).name + ", "
                        if msg_resp.msgClass == ms.Class.Server_Error:
                            err_msg += ms.Server_Error(msg_resp.msgCode).name
                        else:
                            err_msg += ms.Client_Error(msg_resp.msgCode).name
                        prompt = ms.Method(msg_req.msgCode).name + " request error: " + err_msg

                    if msg_resp.getOptionVal(ms.Options.BLOCK2) is not None:
                        transaction = None
                        for trz in self.__recvBlock:
                            if trz[0] == msg_resp.token:
                                transaction = trz
                                break
                        if transaction is not None:
                            prompt = "Error while downloading " + transaction[1]
                            self.__recvBlock.remove(transaction)
                    self.__eventQueue.put(ev.ControllerEvent(ev.EventType.REQUEST_FAILED, prompt))
                    self.remove_req(msg_req)

