import sys
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import StringVar
from functools import partial
import Message as ms
import ControllerCommand as cmd
import queue as q
import threading
import ControllerEvent as ce


class Window(tk.Tk):
    __rootFolder = "Home/"

    def __init__(self, cmdQueue: q.Queue, eventQueue: q.Queue):
        super().__init__()
        # communication queues
        self.__cmdQueue = cmdQueue
        self.__eventQueue = eventQueue

        # init event listener
        self.__eventListener = threading.Thread(target=self.__listenEventQ)
        self.__eventListener.setDaemon(True)
        self.__eventListener.start()

        # send get command for listing root folder
        self.__cmdQueue.put(cmd.ListFolder(self.__rootFolder))

        self.geometry("500x200")
        self.grid()

        # string list with path folders
        self.__pathString = []
        self.__pathString.append(self.__rootFolder)

        # upper menu frame
        self.__menu = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.__menu.grid()
        self.__menu.pack(anchor="n", fill="x")

        # connection type checkbutton
        self.__commTypeState = tk.IntVar()
        self.__commType = tk.Checkbutton(self.__menu, text="Confirmable", variable=self.__commTypeState)
        self.__commType.grid(column=0, row=0)

        # ip label
        self.__ip = tk.Entry(self.__menu)
        self.__ip.configure(width=16)
        self.__ip.grid(column=1, row=0)

        # port label
        self.__port = tk.Entry(self.__menu)
        self.__port.configure(width=6)
        self.__port.grid(column=2, row=0)

        # backward button
        self.__back = tk.Button(self.__menu, text="<-", command=self.__testCb)
        self.__back.grid(column=3, row=0)

        # forward button
        self.__forward = tk.Button(self.__menu, text="->", command=self.__testCb)
        self.__forward.grid(column=4, row=0)

        # current path label
        self.__path = tk.Label(self.__menu, text="Home/")
        self.__path.grid(column=5, row=0)

        # files list
        self.__files = ttk.Treeview(self, columns=("type", "name"), show="headings", selectmode="browse")
        self.__files.heading("name", text="Name")
        self.__files["displaycolumns"] = ("name", )
        self.__scroll = ttk.Scrollbar(self.__files, orient="vertical", command=self.__files.yview)
        self.__files.configure(yscrollcommand=self.__scroll.set)
        self.__scroll.pack(side="right", fill="y")
        self.__files.pack(fill="both", expand=True)
        self.__files.insert('', tk.END, values=(0, "file1"))
        self.__files.insert('', tk.END, values=(0, "file2"))
        self.__files.insert('', tk.END, values=(1, "file3"))
        self.__files.insert('', tk.END, values=(0, "file4"))
        self.__files.insert('', tk.END, values=(0, "file5"))
        self.__files.insert('', tk.END, values=(0, "file6"))
        self.__files.insert('', tk.END, values=(0, "file7"))
        self.__files.insert('', tk.END, values=(1, "file8"))

        self.__files.bind("<ButtonRelease-3>", self.__filePopup)

        # bottom menu frame
        self.__actions = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.__actions.pack(fill="x", side="bottom")

        # upload  file button
        self.__uploadFile = tk.Button(self.__actions, text="Upload file", command=self.__testCb)
        self.__uploadFile.grid(column=0, row=0)

        # create folder button
        self.__createFolder = tk.Button(self.__actions, text="Create folder", command=self.__testCb)
        self.__createFolder.grid(column=1, row=0)

    def __filePopup(self, event):
        iid = self.__files.identify_row(event.y)
        name = self.__files.item(iid).get('values')[0]
        if iid:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Rename", command=partial(self.__fileRename, iid, name))
            menu.add_command(label="Delete", command=partial(self.__fileDelete, iid))
            menu.add_command(label="Move", command=partial(self.__fileMove, name))
            menu.tk_popup(event.x_root, event.y_root, 0)
        else:
            pass

    def __fileRename(self, file_id, name):
        new_name = simpledialog.askstring(title=name, prompt='Enter new name: ', initialvalue=name)
        columns = self.__files.item(file_id).get('values')
        columns[0] = new_name
        # TODO send the request, and if successful:
        if self.__commTypeState.get() == 0:
            t = ms.Type.Confirmable
        else:
            t = ms.Type.NonConfirmable

        msg = ms.Message(t, ms.Class.Method, ms.Method.PUT)
        msg.addOption(8, self.__path.cget("text") + name)
        self.__files.item(file_id, values=columns)

    def __fileDelete(self, file_id):
        # TODO send the request, and if successful:
        self.__pathString.append("lol/")
        tmp = ""
        for string in self.__pathString:
            tmp += string
        self.__path.configure(text=tmp)
        self.__files.delete(file_id)

    def __fileMove(self, name):
        new_path = simpledialog.askstring(title='Path', prompt='Enter new path: ', initialvalue=self.__pathString)
        # TODO send the request for update
        # TODO send the GET request for updated file parent folder
        self.__pathString.pop()
        tmp = ""
        for string in self.__pathString:
            tmp += string
        self.__path.configure(text=tmp)

    def __testCb(self):
        print(self.__pathString.get())

    def __listenEventQ(self):
        while self.__running:
            event: ce.ControllerEvent = self.__eventQueue.get()
