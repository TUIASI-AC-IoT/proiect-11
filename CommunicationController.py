import socket


class CommunicationController:
    def __init__(self, ip, port):
        self.__address = (ip, port)
        self.__sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.__sk.bind(('0.0.0.0', 5683))

    def send_request(self, message):
        self.__sk.sendto(message, self.__address)
