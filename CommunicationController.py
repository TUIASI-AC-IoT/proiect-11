import socket, queue as q, Message as ms, ControllerEvent as ev
import threading, select, random, time

serverIp = '127.0.0.1'
serverPort = 5683

# Communication type by default CON
Com_Type = ms.Type.Confirmable


class CommunicationController:
    __ACK_TIMEOUT = 2  # s
    __MAX_RETRANSMIT = 4
    __ACK_RANDOM_FACTOR = 5

    __msgIdValue = random.randint(0, 0xFFFF)
    __tknValue = random.randint(0, 0XFFFF_FFFF_FFFF_FFFF)

    def __init__(self, cmdQueue: q.Queue, eventQueue: q.Queue):
        self.__sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__sk.bind(('0.0.0.0', 5683))

        # Communication with GUI queues
        self.__cmdQueue = cmdQueue
        self.__eventQueue = eventQueue

        # sender socket lock
        self.__sendLock = threading.Lock()

        #
        self.__reqList = list()
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
                        self.__cmdQueue.put(ev.ControllerEvent(ev.EventType.REQUEST_TIMEOUT, req[0]))
                        self.__reqList.remove(req)


    def listen_for_command(self):
        while True:
            command = self.__cmdQueue.get()
            msg: ms.Message = command.getDetails()
            msg.setMessageId(33)
            msg.setToken(666)
            self.send_request(msg.encode())
            self.__reqList.append((msg, time.time(), self.__ACK_TIMEOUT, 4))

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

            msg_req = None
            # Searching to associate a response with a request
            if msg_resp.tk_len == 0:
                for msg in self.__reqList:
                    if msg_resp.msgId == msg.msgId:
                        msg_req = msg
                        break
                if msg_req is not None:
                    if msg_resp.msgType == ms.Type.Acknowledgement:
                        self.__reqList.remove(msg_req)
                        self.__delayedReq.append(msg_req)
                return
            else:
                for msg in self.__reqList:
                    if msg_resp.token == msg.token:
                        msg_req = msg
                        break
                if msg_req is None: # Might be a response from a delayed request
                    for msg in self.__delayedReq:
                        if msg_resp.token == msg.token:
                            msg_req = msg
                            break
                if msg_req is None:
                    return  # No matching request for this response (might be a duplicate from a resolved request)

                # supposed req is always a method
                if msg_req.msgClass != ms.Class.Method:
                    return

                # Creating events based on request - response types

                if msg_resp.msgClass == ms.Class.Success:
                    if msg_req.msgCode == ms.Method.GET and msg_resp.msgCode == ms.Success.Content:
                        if int.from_bytes(msg_resp.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          "big") == ms.Content_Format.PLAIN_TEXT:
                            # Matching for a ListDirectory-event

                            return
                        if int.from_bytes(msg_resp.getOptionVal(ms.Options.CONTENT_FORMAT),
                                          "big") == ms.Content_Format.OCTET_STREAM:
                            #
                            return

                    if msg_req.msgCode == ms.Method.POST and msg_resp.msgCode == ms.Success.Created:
                            #
                        return
                    if msg_req.msgCode == ms.Method.PUT and msg_resp.msgCode == ms.Success.Changed:

                        pass
                    if msg_req.msgCode == ms.Method.DELETE and msg_resp.msgCode == ms.Success.Deleted:

                        pass
                    if msg_req.msgCode == ms.Method.HEAD and msg_resp.msgCode == ms.Success.Content:

                        pass

                if msg_resp.msgClass == ms.Class.Client_Error or msg_resp.msgClass == ms.Class.Server_Error:
                    if msg_req.msgCode == ms.Method.GET:
                        pass
                    if msg_req.msgCode == ms.Method.POST:
                        return
                    if msg_req.msgCode == ms.Method.PUT:
                        pass
                    if msg_req.msgCode == ms.Method.DELETE:
                        pass
                    if msg_req.msgCode == ms.Method.HEAD:
                        pass







