import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
from functools import partial
import Message as ms
import random


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.message_id = int(random.random() * 65535)

        self.geometry("500x200")
        self.grid()

        self.pathString = []
        self.pathString.append("Home/")

        self.menu = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.menu.grid()
        self.menu.pack(anchor="n", fill="x")

        # connection type checkbutton
        self.connTypeState = tk.IntVar()
        self.connType = tk.Checkbutton(self.menu, text="Confirmable", variable=self.connTypeState)
        self.connType.grid(column=0, row=0)

        # ip label
        self.ip = tk.Entry(self.menu)
        self.ip.configure(width=16)
        self.ip.grid(column=1, row=0)

        # port label
        self.port = tk.Entry(self.menu)
        self.port.configure(width=6)
        self.port.grid(column=2, row=0)

        self.back = tk.Button(self.menu, text="Backward", command=self.test_cb)
        self.back.grid(column=3, row=0)

        self.forward = tk.Button(self.menu, text="Forward", command=self.test_cb)
        self.forward.grid(column=4, row=0)

        self.path = tk.Label(self.menu, text="Home/")
        self.path.grid(column=5, row=0)

        # files list
        self.files = ttk.Treeview(self, columns="name", show="headings", selectmode="browse")
        self.files.heading("name", text="Name")
        self.scroll = ttk.Scrollbar(self.files, orient="vertical", command=self.files.yview)
        self.files.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.files.pack(fill="both", expand=True)
        self.files.insert('', tk.END, values=("file1",))
        self.files.insert('', tk.END, values=("file2",))
        self.files.insert('', tk.END, values=("file3",))
        self.files.insert('', tk.END, values=("file4",))
        self.files.insert('', tk.END, values=("file5",))
        self.files.insert('', tk.END, values=("file6",))
        self.files.insert('', tk.END, values=("file7",))
        self.files.insert('', tk.END, values=("file8",))

        self.files.bind("<ButtonRelease-3>", self.__file_popup)

        # file actions
        self.actions = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.actions.pack(fill="x", side="bottom")

        self.uploadFile = tk.Button(self.actions, text="Upload file", command=self.test_cb)
        self.uploadFile.grid(column=0, row=0)

        self.createFolder = tk.Button(self.actions, text="Create folder", command=self.test_cb)
        self.createFolder.grid(column=1, row=0)

    def __file_popup(self, event):
        iid = self.files.identify_row(event.y)
        name = self.files.item(iid).get('values')[0]
        if iid:
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Rename", command=partial(self.__file_rename, iid, name))
            menu.add_command(label="Delete", command=partial(self.__file_delete, iid))
            menu.add_command(label="Move", command=partial(self.__file_move, name))
            menu.tk_popup(event.x_root, event.y_root, 0)
        else:
            pass

    def __file_rename(self, file_id, name):
        new_name = simpledialog.askstring(title=name, prompt='Enter new name: ', initialvalue=name)
        columns = self.files.item(file_id).get('values')
        columns[0] = new_name
        # TODO send the request, and if successful:
        if self.connTypeState.get() == 0:
            t = ms.Type.Confirmable
        else:
            t = ms.Type.NonConfirmable

        msg = ms.Message(t, ms.Class.Method, ms.Method.PUT, self.message_id)
        msg.addOption(8, self.path.cget("text") + name)
        self.files.item(file_id, values=columns)

    def __file_delete(self, file_id):
        # TODO send the request, and if successful:
        self.pathString.append("lol/")
        tmp = ""
        for string in self.pathString:
            tmp += string
        self.path.configure(text=tmp)
        self.files.delete(file_id)

    def __file_move(self, name):
        new_path = simpledialog.askstring(title='Path', prompt='Enter new path: ', initialvalue=self.pathString)
        # TODO send the request for update
        # TODO send the GET request for updated file parent folder
        self.pathString.pop()
        tmp = ""
        for string in self.pathString:
            tmp += string
        self.path.configure(text=tmp)

    def test_cb(self):
        print("test")
