import random

import Server as sv, Message as ms


def App():
    server = sv.Server('localhost', 8080)

    message_id = int(random.random() * 65535)
    msg = ms.Message(ms.Type.Confirmable, ms.Class.Method, ms.Method.GET, message_id)
    msg.add_option(8, 'home/')
    server.send_request(msg.encode())


if __name__ == '__main__':
    App()
