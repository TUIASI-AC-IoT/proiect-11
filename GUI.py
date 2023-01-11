import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from tkinter import filedialog
from functools import partial
import CommunicationController as com
import ControllerCommand as cmd
import ControllerEvent as ce
import queue as q
import threading


class Window(tk.Tk):
    def __init__(self, cmdQueue: q.Queue, eventQueue: q.Queue):
        super().__init__()
        self.geometry("500x200")
        self.grid()

        # communication queues
        self.__cmdQueue = cmdQueue
        self.__eventQueue = eventQueue

        # init event listener
        self.__eventListener = threading.Thread(target=self.__listenEventQ)
        self.__eventListener.setDaemon(True)
        self.__eventListener.start()

        # string list with path folders
        self.__pathString = []
        self.__pathString.append("")

        # upper menu frame
        self.__menu = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.__menu.grid()
        self.__menu.pack(anchor="n", fill="x")

        # connection type checkbutton
        self.__commTypeVar = tk.IntVar()
        self.__commType = tk.Checkbutton(self.__menu, text="Non-Confirmable", command=self.__setCommType, variable=self.__commTypeVar)
        self.__commType.grid(column=0, row=0)

        # ip label
        self.__ipVar = tk.StringVar()
        self.__ip = tk.Entry(self.__menu, textvariable=self.__ipVar)
        self.__ip.bind("<FocusOut>", self.__setServerIp)
        self.__ip.configure(width=16)
        self.__ip.grid(column=1, row=0)

        # port label
        self.__portVar = tk.IntVar()
        self.__port = tk.Entry(self.__menu)
        self.__port.bind("<FocusOut>", self.__setServerPort)
        self.__port.configure(width=6)
        self.__port.grid(column=2, row=0)

        # backward button
        self.__back = tk.Button(self.__menu, text="<-", command=self.__backwardCB)
        self.__back.grid(column=3, row=0)

        # refresh button
        self.__refresh = tk.Button(self.__menu, text="Refresh", command=self.__refreshCB)
        self.__refresh.grid(column=4, row=0)

        # current path label
        self.__path = tk.Label(self.__menu, text="")
        self.__path.grid(column=5, row=0)

        # files list
        self.__files = ttk.Treeview(self, columns=("type", "name"), show="headings", selectmode="browse")
        self.__files.heading("name", text="Name")
        self.__files["displaycolumns"] = ("name", )
        self.__scroll = ttk.Scrollbar(self.__files, orient="vertical", command=self.__files.yview)
        self.__files.configure(yscrollcommand=self.__scroll.set)
        self.__scroll.pack(side="right", fill="y")
        self.__files.pack(fill="both", expand=True)

        self.__files.bind("<ButtonRelease-3>", self.__filePopup)

        # bottom menu frame
        self.__actions = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.__actions.pack(fill="x", side="bottom")

        # upload  file button
        self.__uploadFile = tk.Button(self.__actions, text="Upload file", command=self.__uploadFileCB)
        self.__uploadFile.grid(column=0, row=0)

        # create folder button
        self.__createFolder = tk.Button(self.__actions, text="Create folder", command=self.__createFolderCB)
        self.__createFolder.grid(column=1, row=0)

        self.__cmdQueue.put(cmd.ListFolder(self.__pathString))

    def __setCommType(self):
        com.Com_Type = self.__commTypeVar.get()

    def __setServerIp(self, useless):
        com.serverIp = self.__ipVar.get()

    def __setServerPort(self, useless):
        com.serverPort = self.__portVar.get()

    def __refreshCB(self):
        self.__cmdQueue.put(cmd.ListFolder(self.__pathString))

    def __backwardCB(self):
        if len(self.__pathString) != 1:
            self.__cmdQueue.put(cmd.ListFolder(self.__pathString[0:len(self.__pathString) - 1]))

    def __filePopup(self, event):
        iid = self.__files.identify_row(event.y)
        name = self.__files.item(iid).get('values')[1]
        if iid:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Rename", command=partial(self.__fileRename, name))
            menu.add_command(label="Delete", command=partial(self.__fileDelete, name))
            menu.add_command(label="Move", command=partial(self.__fileMove, name))
            menu.add_command(label="Details", command=partial(self.__fileDetails, name))
            if self.__files.item(iid).get('values')[0] == 1:
                menu.add_command(label="Download", command=partial(self.__fileDownload, name))
            menu.tk_popup(event.x_root, event.y_root, 1)

    def __fileRename(self, name):
        new_name = simpledialog.askstring(title=name, prompt='Enter new name: ', initialvalue=name)
        if new_name is not None:
            uri = self.__pathString.copy()
            uri.append(name)
            self.__cmdQueue.put(cmd.RenameFile(uri, new_name))

    def __fileDelete(self, name):
        uri = self.__pathString.copy()
        uri.append(name)
        self.__cmdQueue.put(cmd.DeleteFile(uri))

    def __fileMove(self, name):
        new_path = simpledialog.askstring(title='Path', prompt='Enter new path with /: ')
        if new_path is not None:
            uri: list = new_path.split('/')
            uri.append(name)
            self.__cmdQueue.put(cmd.MoveFile(uri))

    def __fileDetails(self, name):
        uri = self.__pathString.copy()
        uri.append(name)
        self.__cmdQueue.put(cmd.GetMetadata(uri))

    def __fileDownload(self, name):
        uri = self.__pathString.copy()
        uri.append(name)
        self.__cmdQueue.put(cmd.DownloadFile(uri))

    def __listenEventQ(self):
        while True:
            event: ce.ControllerEvent = self.__eventQueue.get()

            if event.eventType == ce.EventType.FILE_LIST:
                for item in self.__files.get_children():
                    self.__files.delete(item)

                for i in event.data:
                    self.__files.insert('', tk.END, values=i)

            self.__eventQueue.task_done()

    def __uploadFileCB(self):
        file = filedialog.askopenfilename()
        if file != "":
            self.__cmdQueue.put(cmd.UploadFile(self.__pathString, file))

    def __createFolderCB(self):
        name = simpledialog.askstring(title="New folder", prompt='Enter name: ')
        if name is not None:
            uri = self.__pathString.copy()
            uri.append(name)
            self.__cmdQueue.put(cmd.CreateFolder(uri))
