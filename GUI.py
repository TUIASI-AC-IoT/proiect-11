import functools
import tkinter as tk
from tkinter import ttk
import callbacks as cb


class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("500x200")
        self.grid()

        self.pathString = tk.StringVar()
        self.pathString = "Home/"

        self.menu = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.menu.grid()
        self.menu.pack(anchor="n", fill="x")

        # self.ip = tk.Text(self.menu, height=1, width=10)
        self.ip = tk.Entry(self.menu)
        self.ip.configure(width=16)
        self.ip.grid(column=0, row=0)

        # self.port = tk.Text(self.menu, height=1, width=5)
        self.port = tk.Entry(self.menu)
        self.port.configure(width=6)
        self.port.grid(column=1, row=0)

        self.back = tk.Button(self.menu, text="Backward", command=cb.lol)
        self.back.grid(column=2, row=0)

        self.forward = tk.Button(self.menu, text="Forward", command=cb.lol)
        self.forward.grid(column=3, row=0)

        self.path = tk.Label(self.menu, text=self.pathString)
        self.path.grid(column=4, row=0)

        # files list
        self.files = ttk.Treeview(self, columns=("name", "date", "size"), show="headings", selectmode="browse")
        self.files.heading("name", text="Name")
        self.files.column("date", width=100, stretch=False)
        self.files.heading("date", text="Date modified")
        self.files.column("size", width=120, stretch=False)
        self.files.heading("size", text="Size")
        self.scroll = ttk.Scrollbar(self.files, orient="vertical", command=self.files.yview)
        self.files.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.files.pack(fill="both", expand=True)
        self.files.insert('', tk.END, values=("file1", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file2", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file3", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file4", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file5", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file6", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file7", "20.10.2019", "16KB"))
        self.files.insert('', tk.END, values=("file8", "20.10.2019", "16KB"))

        self.files.bind("<Button-3>", cb.file_popup)

        # file actions
        self.actions = tk.Frame(self, highlightbackground="black", highlightthickness=1)
        self.actions.pack(fill="x", side="bottom")

        self.uploadFile = tk.Button(self.actions, text="Upload file", command=cb.lol())
        self.uploadFile.grid(column=0, row=0)

        self.createFolder = tk.Button(self.actions, text="Create folder", command=cb.lol())
        self.createFolder.grid(column=1, row=0)

    def popup(self, event):
        iid = self.files.identify_row(event.y)
        if iid:
            # mouse pointer over item
            self.files.selection_set(iid)
            print(iid)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Rename")
            menu.add_command(label="Delete")
            menu.add_command(label="Move", command=cb.lol)
            menu.tk_popup(event.x_root, event.y_root, 0)
        else:
            pass
