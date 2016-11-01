# Graphical User Interface main methods
from tkinter import *

trial = 5


root = Tk()
root.geometry('250 x 150')
root.title ('Enter your login Information')
def input(parent, label, width=None, **options)
    Label(parent, text=label).pack(side=TOP)
    entry = Entry(parent, **options)
    if width:
      entry.pack(side=TOP, padx=10, fill=BOTH)
      return entry

parent = Frame(root, padx=10, pady=10)
parent.pack(fill=BOTH, expand=True)

user = input(parent, "Username:", 16, show='*')
login_button = Button(parent, borderwidth=4, text="Login", width=10, pady=8, command=authorize_user)

login_button.pack(side=BOTTOM)

user.focus_set()
parent.mainloop()
