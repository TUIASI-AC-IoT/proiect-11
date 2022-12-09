import Server as sv, Message as ms


def App():
    server = sv.Server('0.0.0.0', 8080)

    msg = ms.Message(ms.Type.Confirmable, ms.Class.Method, ms.Method.GET)

    server.send_request(msg.encode())


if __name__ == '__main__':
    App()
