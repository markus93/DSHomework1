
from tkinter import *

import ScrolledText
import tkFileDialog
import os

import tkMessageBox
textPad = None
user = None
currentfile = None
window = None

class app:

    def newappwindow(self,username):
        global textPad
        global user
        global window
        user = username

        self.file = ['chem_data.txt','chem_data2.txt','show.txt','file2.txt','file3.txt']
        self.list = {'name': 'Zed', 'age': 39, 'height': 6 * 12 + 2}
        window = Toplevel()

        window.geometry('700x300')
        textPad = ScrolledText.ScrolledText(window, width=400, height=100)
        textPad.configure(state = DISABLED)
        if currentfile == None:
            window.title('Welcome back '+str(user))
        else:
            window.title ('You are currently on '+currentfile)

        menu = Menu(window)
        window.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.new_file)
        #filemenu.add_command(label="Open...", command=self.open_command)
        filemenu.add_command(label="Member Files...", command=self.member)
        filemenu.add_command(label="Master Files..", command=self.master)
        filemenu.add_command(label="Save", command=self.save_command)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit_command)
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.about_command)
        # end of menu creation

        textPad.pack()
        window.mainloop()

    def open_command(self,filename):
        global currentfile
        print str(filename)

        window.title('You are currently editing ' +filename)

        textPad.delete('1.0',END)
        count = 1.0
        with open(filename) as f:
            textPad.configure(state=NORMAL)
            for line in f:
                textPad.insert(str(count), line)
                count = count + 1.0
            textPad.configure(state=DISABLED)
        f.close()
        textPad.configure(state=NORMAL)
        textPad.bind('<Return>', self.new_line)

    def new_line(self,event):

        pos = textPad.index("end-1c linestart")
        print pos
        textPad.tag_config(pos, foreground="blue", underline=1)
        print textPad.get(pos, 'end-1c')




    def new_file(self):
        newfile = createFile()
        newfile.newfileview(user)

    def save_command(self):
        textPad
        file = open(currentfile,'w')
        if file != None:
            # slice off the last character from get, as an extra return is added
            data = textPad.get('1.0', END + '-1c')
            file.write(data)
            file.close()


    def exit_command(self):

        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            window.destroy()

    def about_command(self):
        label = tkMessageBox.showinfo("About", "Just Another TextPad \n Copyright \n No rights left to reserve")

    def member(self):

        #self.window.withdraw()
        callview = view()
        callview.views(self.file,user,'member')
    def master(self):
        callview = view()
        callview.views(self.file,user,'master')


class view:

    def views(self,files,username,type):
        self.username = username
        self.root = Tk()
        self.files = files
        self.type = type
        self.list_box_1 = Listbox(self.root, width=100, height=20, selectmode=EXTENDED)
        self.list_box_1.grid(row=0, column=0)
        self.list_box_1.pack()
        if self.type == "master":
            self.delete_button = Button(self.root, text="Delete", command=self.DeleteSelection)
            self.delete_button.pack(side="right")
            self.editor_button = Button(self.root, text="[Editor Review]", command=self.EditorSelection)
            self.editor_button.pack(side="right")
        self.back_button = Button(self.root, text="<Back", command=self.Close)
        self.back_button.pack(side="left")
        self.open_button = Button(self.root, text="[Open File]", command=self.Selected)
        # self.open_button.grid(row=1, col=0)
        self.open_button.pack(side='left')
        for item in self.files:
            self.list_box_1.insert(END, item)
        self.root.mainloop()


    def Selected(self):
        try:
            index = self.list_box_1.curselection()[0]
            seltext = self.list_box_1.get(index)
            if tkMessageBox.askokcancel("Open file", "Do you really want to open file %s?" %seltext):
                self.root.destroy()
                openfile = app()
                openfile.open_command(seltext)

        except:
            print 'Index of out range'

    def DeleteSelection(self):
        items = self.list_box_1.curselection()
        pos = 0
        for i in items:
            idx = int(i) - pos
            self.list_box_1.delete(idx, idx)
            pos = pos + 1
            #send file update to server
    def EditorSelection(self):
        try:
            index = self.list_box_1.curselection()[0]
            selected_file = self.list_box_1.get(index)
            self.root.destroy()
            callEditor = Editor()
            callEditor.Editor_view(self.username,self.files,selected_file,self.type)
        except:
            print "nothing selected"

    def Close(self):

        self.root.destroy()

lbt = view()

class createFile():

    def newfileview(self,username):
        fileview = Tk()
        Label(fileview, text = "Create New FIle").grid(row=0)
        self.filename = Entry(fileview)
        self.filename.grid(row=0, column=1)
        Button(fileview, text='Create File', command=self.create).grid(row=3, column=1, sticky=W, pady=4)

    def create(self):
        #send file to server and create file
        #if successfull, go to view
       file = (self.filename.get().split(".")[0])
       file = file.replace(" ", "")
       if file == "\n":

            print 'new line added'
       if file != "":
           print "successfull input %s.txt"%file
       else:
            Label = tkMessageBox.showinfo("Error", "Invalid Text Input")

       print file

class Editor():

    def Editor_view(self,username,files,selected_file,type):
        self.username = username
        self.files = files
        self.selected_file = selected_file
        self.type = type
        self.root = Tk()
        self.list_box_1 = Listbox(self.root, width=50, height=20, selectmode=EXTENDED)
        self.list_box_1.grid(row=0, column=0)
        self.root.title('Control Editor for  ' + self.selected_file)
        self.list_box_1.pack()
        self.input1 = ["one", "two", "three", "four"]
        #get editors for this files
        self.input2 = ["five","six","seven"]
        self.add_button = Button(self.root, text="Add Editor >", command=self.Selected)
        self.add_button.pack(side = 'left')
        self.remove_button = Button(self.root, text="Remove Editor ", command=self.DeleteSelection)
        self.remove_button.pack(side = 'right')
        self.editor_name = Entry(self.root)
        self.editor_name.pack()
        self.populate(self.list_box_1)
        self.root.mainloop()
    def populate(self,name):
        for item in self.input2:
           name.insert(END,item)

    def Selected(self):
            editor_name = self.editor_name.get()
            if editor_name != '':
                if tkMessageBox.askokcancel("Message", "Do you want to give this user Editor right %s?" % editor_name):
                    self.input2.insert(0, editor_name)
                    self.list_box_1.insert(END, editor_name)

    def DeleteSelection(self):

        items = self.list_box_1.curselection()
        pos = 0
        try:
            index = self.list_box_1.curselection()[0]
            seltext = self.list_box_1.get(index)
            if tkMessageBox.askokcancel("Message", "Are you sure you want to remove user %s?" % seltext):
                for i in items:
                    idx = int(i) - pos
                    self.list_box_1.delete(idx, idx)
                    pos = pos + 1
        except:
            print 'nothing selected'


    def back(self):
        self.root.destroy()
        callview = view()
        callview.views(self.files, self.username, self.type)


loadEditor = Editor()


