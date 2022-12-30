import random
import GUI
import CommunicationController as ComC
import queue as q

import CommunicationController as sv, Message as ms


def App():
    server = sv.Server('localhost', 5683)

    message_id = int(random.random() * 65535)
    msg = ms.Message(ms.Type.Confirmable, ms.Class.Method, ms.Method.GET)
    msg.addOption(8, 'home/')
    server.send_request(msg.encode())


if __name__ == '__main__':
    commandsQueue = q.Queue()
    eventsQueue = q.Queue()
    # Communication part
    cc = ComC.CommunicationController(commandsQueue, eventsQueue)
    cc.start()

    # Interface part
    ui = GUI.Window(commandsQueue, eventsQueue)
    ui.title("widuv")
    ui.mainloop()
