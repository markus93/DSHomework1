# Graphical User Interface main methods
from Tkinter import *
import appwindow

trial = 5


root = Tk()
root.geometry('250x150')
root.title('Enter your login Information')
def input(parent, label, width=None, **options):
    Label(parent, text=label).pack(side=TOP)
    entry = Entry(parent, **options)
    if width:
      entry.pack(side=TOP, padx=10, fill=BOTH)
      return entry
    
def displaywindow():
    root.withdraw()
    username = user.get()
     #TODO problems with that
    displayapp = appwindow.app()
    displayapp.newappwindow(username)

parent = Frame(root, padx=10, pady=10)
parent.pack(fill=BOTH, expand=True)

user = input(parent, "Username:", 16)
login_button = Button(parent, borderwidth=4, text="Login", width=10, pady=8, command=displaywindow)

login_button.pack(side=BOTTOM)

user.focus_set()
parent.mainloop()
