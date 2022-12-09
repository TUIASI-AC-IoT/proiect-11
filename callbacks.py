import tkinter as tk


def lol():
    print("lol")


def file_popup(event, self):
    iid = self.files.identify_row(event.y)
    if iid:
        # mouse pointer over item
        self.files.selection_set(iid)
        print(iid)
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Rename")
        menu.add_command(label="Delete")
        menu.add_command(label="Move", command=lol)
        menu.tk_popup(event.x_root, event.y_root, 0)
    else:
        pass


def test(event):
    print(event.x_root)
