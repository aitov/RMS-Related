from tkinter import filedialog
from tkinter import *


def select_folder(initial_folder):
    root = Tk()
    root.withdraw()
    path = filedialog.askdirectory(title="Choose directory for Processing",
                                   initialdir=initial_folder,
                                   mustexist=True)
    root.destroy()
    return path


def select_file(initial_folder, file_type):
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(title="Choose file for Processing",
                                      initialdir=initial_folder,
                                      filetypes=[('Type', file_type)])
    root.destroy()
    return path


def select_from_list(title, choices):
    root = Tk()
    window_height = 300
    window_width = 400

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x_cordinate = int((screen_width / 2) - (window_width / 2))
    y_cordinate = int((screen_height / 2) - (window_height / 2))

    root.geometry("{}x{}+{}+{}".format(window_width, window_height, x_cordinate, y_cordinate))

    root.resizable(False, False)
    root.title(title)
    choice = Choices(root, choices)
    root.mainloop()
    return choice.selected


class Choices:

    def __init__(self, parent_window, choice_list):
        self.window = parent_window
        Label(self.window, text="Select required file:").grid(row=0, column=0, sticky="W", padx=10)
        self.selected = ""
        var = Variable(value=choice_list)
        self.list_box = Listbox(self.window,
                                listvariable=var,
                                height=10,
                                width=40,
                                selectmode=SINGLE)
        self.list_box.grid(sticky="nesw", row=1, column=0, padx=10, pady=10)
        self.list_box.select_set(0)
        Button(self.window, text='Select', command=self.select_handler).grid(row=2, column=0)

    def select_handler(self):
        self.selected = self.list_box.get(self.list_box.curselection())

        self.window.destroy()
