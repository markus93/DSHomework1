from Tkinter import *
import ScrolledText
from sessions.client.main import *
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

                #initialize username
                user = username
                #call get_files function and retrieve files from server
                self.error, self.userfiles, self.memberfiles = get_files(username)

                window = Toplevel()
                window.geometry('700x300')
                textPad = ScrolledText.ScrolledText(self.window, width=400, height=100)
                window.title('Welcome back '+str(user))

                #create menu option for client
                menu = Menu(self.window)
                window.config(menu=menu)
                filemenu = Menu(menu)
                menu.add_cascade(label="File", menu=filemenu)
                filemenu.add_command(label="New", command=self.new_file)

                filemenu.add_command(label="Member Files...", command=self.member)
                filemenu.add_command(label="Master Files..", command=self.master)
                #filemenu.add_command(label="Save", command=self.save_command) No need for saving ATM
                filemenu.add_separator()
                filemenu.add_command(label="Exit", command=self.exit_command)
                helpmenu = Menu(menu)
                menu.add_cascade(label="Help", menu=helpmenu)
                helpmenu.add_command(label="About...", command=self.about_command)

                textPad.pack()
                window.mainloop()

        def open(self,filename):
                global currentfile
                #global window
                #textPad
                 window.title('You are currently editting'+str(filename))
                textPad.delete('1.0',END)
                error, contents, queue = open_file(user,filename)
                if error == "":
                    textPad.insert('1.0', contents)
                    currentfile = filename
                # TODO also lock line for user (so other users couldn't edit that)
                # TODO add somewhere method which recognises line switching (when user goes from one line to another)
                    # TODO then new line edit should be sent and next line locked.
                # TODO Make new thread which calls queue.get() and puts line into right place in GUI.

         #open new view to input file name
        def new_file(self):
                newfile = createFile()
                newfile.newfileview(user)
        #close connection
        def exit_command(self):

                if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
                    stop_listening()

        def about_command(self):
                label = tkMessageBox.showinfo("About", "Home work for Distributed Systems (2016)")

        #open files that user can edit
        def member(self):
                if len(self.memberfiles) == 0:
                        label = tkMessageBox.showinfo("Error message", "No file to open")
                else:
                        callview = view()
                        callview.views(self.memberfiles,user,'member')

         #list files that user can invite and delete client
        def master(self):
                if len(self.userfiles) == 0:
                        label = tkMessageBox.showinfo("Error message", "You do not own any file at this moment")
                else:
                        callview = view()
                        callview.views(self.userfiles,user,'master')
class view:

    def views(self,files,username,type):
        self.username = username
        self.root = Tk()
        self.type =type
        self.files = files
        self.list_box_1 = Listbox(self.root, width=100, height=20, selectmode=EXTENDED)
        self.list_box_1.grid(row=0, column=0)
        self.list_box_1.pack()
        #if usertype is master, then user can delete files

        if self.type == "master":
            self.delete_button = Button(self.root, text="Delete", command=self.DeleteSelection)
            self.delete_button.pack(side="right")
            self.editor_button = Button(self.root, text="[Editor Review]", command=self.EditorSelection)
            self.editor_button.pack(side="right")

        #universal menu for both master and member
        self.back_button = Button(self.root, text="<Back", command=self.Close)
        self.back_button.pack(side="left")

        self.open_button = Button(self.root, text="[Open File]", command=self.Selected)
        # self.open_button.grid(row=1, col=0)
        self.open_button.pack(side='left')
        #list files in list
        for item in self.files:
            self.list_box_1.insert(END, item)
        self.root.mainloop()


    def Selected(self):
        index = self.list_box_1.curselection()[0]
        selected_file = self.list_box_1.get(index)
        if tkMessageBox.askokcancel("Open file", "Do you really want to open file %s?" %selected_file):
            openfile = app()
            openfile.open(selected_file)
            self.root.destroy()

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
        self.fileview = Tk()
        Label(self.fileview, text = "Create New File, you will be the master of this file").grid(row=0)
        self.filename = Entry(self.fileview)
        self.filename.grid(row=0, column=1)
        Button(self.fileview, text='Create File', command=self.create).grid(row=3, column=1, sticky=W, pady=4)

    def create(self):
        file = (self.filename.get().split(".")[0])
        file = file.replace(" ", "")

        if file != "":
            error_message = create_file(user,file+".txt") #changed it to user from self.username
            if error_message == "":
                self.fileview.destroy()
                openfile = app()
                openfile.open(file+".txt")
            else:
                Label = tkMessageBox.showinfo("Error", "Error occurred while creating file")
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
        #get editors for this files
        error_message,self.editors = get_editors(self.selected_file)
        if error_message != "":
            self.editors= list()
        self.add_button = Button(self.root, text="Add Editor >", command=self.Selected)
        self.add_button.pack(side='left')
        self.remove_button = Button(self.root, text=" Remove Editor ", command=self.DeleteSelection)
        self.remove_button.pack(side='right')
        self.editor_name = Entry(self.root)
        self.editor_name.pack()
        self.populate(self.editors,self.list_box_1)
        self.root.mainloop()


    def populate(self,input,name):
        for item in input:
           name.insert(END,item)

    def Selected(self):
        editor_name = self.editor_name.get()
        if editor_name != '':
            if tkMessageBox.askokcancel("Message", "Do you want to give this user Editor right %s?" % editor_name):
                message = add_editor(self.selected_file,editor_name)
                if message =="":
                    self.editors.insert(END,editor_name)
                    self.list_box_1.insert(END, editor_name)
                else:
                    Label = tkMessageBox.showinfo("Error", "Error occured")

    def DeleteSelection(self):
        items = self.list_box_1.curselection()
        pos = 0
        try:

            index = self.list_box_1.curselection()[0]
            seltext = self.list_box_1.get(index)
            if tkMessageBox.askokcancel("Message", "Are you sure you want to remove user %s?" % seltext):
                message = remove_editor(self.selected_file,seltext)
                if message == "":
                    for i in items:
                        idx = int(i) - pos
                        self.list_box_1.delete(idx, idx)
                        pos = pos + 1
            else:
                Label = tkMessageBox.showinfo("Error", "Error occured")
        except:
            print 'nothing selected'

    def back(self):
        self.root.destroy()
        callview = view()
        callview.views(self.files, self.username, self.type)


loadEditor = Editor()











