from tkinter import filedialog, Tk


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
