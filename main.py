import random
import GUI

import Server as sv, Message as ms


def App():
    server = sv.Server('localhost', 5683)

    message_id = int(random.random() * 65535)
    msg = ms.Message(ms.Type.Confirmable, ms.Class.Method, ms.Method.GET, message_id)
    msg.add_option(8, 'home/')
    server.send_request(msg.encode())


if __name__ == '__main__':
    App()
    # ui = GUI.Window()
    # ui.title("widuv")
    # ui.mainloop()
