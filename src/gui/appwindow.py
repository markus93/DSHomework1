from Tkinter import *
import ScrolledText
from sessions.client.main import *
import tkMessageBox
textPad = None
user = None
currentfile = None


class app:
        def newappwindow(self,username):
                global textPad
                global user

                #initialize username
                user = username
                #call get_files function and retrieve files from server
                self.error, self.userfiles, self.memberfiles = get_files(username)

                self.window = Toplevel()
                self.window.geometry('700x300')
                textPad = ScrolledText.ScrolledText(self.window, width=400, height=100)
                self.window.title('Welcome back '+str(user))

                #create menu option for client
                menu = Menu(self.window)
                self.window.config(menu=menu)
                filemenu = Menu(menu)
                menu.add_cascade(label="File", menu=filemenu)
                filemenu.add_command(label="New", command=self.new_file)

                filemenu.add_command(label="Member Files...", command=self.member)
                filemenu.add_command(label="Master Files..", command=self.master)
                filemenu.add_command(label="Save", command=self.save_command)
                filemenu.add_separator()
                filemenu.add_command(label="Exit", command=self.exit_command)
                helpmenu = Menu(menu)
                menu.add_cascade(label="Help", menu=helpmenu)
                helpmenu.add_command(label="About...", command=self.about_command)

                textPad.pack()
                self.window.mainloop()

        def open(self,filename):
                global currentfile
                global window
                textPad
                textPad.delete('1.0',END)
                error, contents = open_file(user,filename)
                if error == "":
                    textPad.insert('1.0', contents)
                    currentfile = filename

                #initialize queue and start reading from server

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
                self.window.destroy()

        #open files that user can edit
        def member(self):
                if len(self.memberfiles):
                        label = tkMessageBox.showinfo("Error message", "No file to open")
                else :
                        callview = view()
                        callview.views(self.memberfiles,user,'member')

         #list files that user can invite and delete client
        def master(self):
                if len(self.userfiles):
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
        fileview = Tk()
        Label(fileview, text = "Create New FIle, you will be the master of this file").grid(row=0)
        self.filename = Entry(fileview)
        self.filename.grid(row=0, column=1)
        Button(fileview, text='Create File', command=self.create).grid(row=3, column=1, sticky=W, pady=4)

    def create(self):
        file = (self.filename.get().split(".")[0])
        file = file.replace(" ", "")

        if file != "":
            error_message = create_file(self.username,file+".txt")
            if error_message == "":
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
        self.list_box_1.pack(side = "left")
        self.list_box_2 = Listbox(self.root, width=50, height=20, selectmode=EXTENDED)
        self.list_box_2.grid(row=0, column=0)
        self.list_box_2.pack(side = "right")
        #get all users
        self.all_users = get_all_users()
        #get editors for this files
        error_message,self.editors = get_editors(self.selected_file)
        if error_message != "":
            self.editors= list()

        self.back_button = Button(self.root, text="back", command=self.back)
        self.back_button.place(relx=0.5, rely=0.9, anchor=CENTER)
        self.add_button = Button(self.root, text="Add Editor >", command=self.Selected)
        self.add_button.place(relx=0.5, rely=0.5, anchor=CENTER)
        self.remove_button = Button(self.root, text=" < Remove Editor ", command=self.DeleteSelection)
        self.remove_button.place(relx=0.5, rely=0.4, anchor=CENTER)
        self.populate(self.all_users,self.list_box_1)
        self.populate(self.editors, self.list_box_2)
        self.root.mainloop()
    def populate(self,input,name):
        for item in input:
           name.insert(END,item)


    def Selected(self):
        index = self.list_box_1.curselection()[0]
        seltext = self.list_box_1.get(index)
        if tkMessageBox.askokcancel("Message", "Do you want to give this user Editor right %s?" % seltext):
            message = add_editor(self.selected_file,seltext)
            if message == "":
                self.editors.insert(0,seltext)
                self.list_box_2.insert(END,seltext)
            else:
                Label = tkMessageBox.showinfo("Error", "Error occured")

    def DeleteSelection(self):
        items = self.list_box_2.curselection()
        pos = 0
        index = self.list_box_2.curselection()[0]
        seltext = self.list_box_2.get(index)
        if tkMessageBox.askokcancel("Message", "Are you sure you want to remove user %s?" % seltext):
            message = remove_editor(self.selected_file,seltext)
            if message == "":
                for i in items:
                    idx = int(i) - pos
                    self.list_box_2.delete(idx, idx)
                    pos = pos + 1
            else:
                Label = tkMessageBox.showinfo("Error", "Error occured")
    def back(self):
        self.root.destroy()
        callview = view()
        callview.views(self.files, self.username, self.type)


loadEditor = Editor()





