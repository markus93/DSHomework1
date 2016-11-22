from Tkinter import *
import ScrolledText
from sessions.client.main import *
import tkMessageBox
import threading
textPad = None
user = None
currentfile = None
window = None
threadWaitForEdit = None


class app:
    def newappwindow(self, username):
        global textPad
        global user
        global window

        # initialize username
        user = username
        # call get_files function and retrieve files from server
        self.error, self.userfiles, self.memberfiles = get_files(username)

        window = Toplevel()
        window.geometry('700x300')
        window.title('Welcome back ' + str(user))

        # create menu option for client
        menu = Menu(window)
        window.config(menu=menu)
        filemenu = Menu(menu)
        menu.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="New", command=self.new_file)

        filemenu.add_command(label="Member Files...", command=self.member)
        filemenu.add_command(label="Master Files..", command=self.master)
        # filemenu.add_command(label="Save", command=self.save_command) No need for saving ATM
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit_command)
        helpmenu = Menu(menu)
        menu.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="About...", command=self.about_command)

        textPad = ReadonlyText(window)
        sb = Scrollbar(window, orient="vertical", command=textPad.yview)
        textPad.configure(yscrollcommand=sb.set)
        sb.pack(side="left", fill="y")
        textPad.pack(side="right", fill="both", expand=True)
        textPad.tag_configure("locked", foreground="grey")
        window.protocol("WM_DELETE_WINDOW", self.on_closing)
        window.mainloop()

    def on_closing(self):
        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            if threadWaitForEdit != None:
                threadWaitForEdit._is_running = False
                stop_listening()
            window.destroy()

    def open(self, filename):
        global currentfile
        global threadWaitForEdit
        # global window
        # textPad
        window.title('You are currently editting ' + str(filename))
        textPad.delete('1.0', END)
        error, contents, queue = open_file(user, filename)
        print error + " " + contents
        if error == "":
            textPad.insert('2.0', contents)
            threadWaitForEdit = wait_for_edits(queue)
            threadWaitForEdit.start()
            # in order to stop the thread (ie if closed the program), insert following line:
            # threadWaitForEdit._is_running = False

        currentfile = filename

        textPad.bind('<Key>', self.new_line)
        textPad.bind('<Return>', self.send)

    def new_line(self, event):
        index = textPad.index(INSERT)
        pos = int(float(index))
        let = str(float(pos))
        last_pos = textPad.index('end')
        err, reply = lock_line(user, currentfile, pos)

        if err == "":
            if reply == False:
                textPad.tag_add('locked', let, str(float(pos) + 1.0))
                if (float(pos) == 1.0):
                    textPad.insert('1.0', ' ', 'locked')

                if (float(last_pos) - 1) == float(let):
                    textPad.insert('end', '\n', 'locked')
                print 'line locked'
            else:
                textPad.tag_remove('locked', let, str(float(pos) + 1.0))
                print 'line not locked'
        else:
            print err

    def send(self, event):
        index = textPad.index(INSERT)
        pos = int(float(index))
        let = str(float(pos))
        endline = textPad.index(str(pos)+".0 lineend")
        last_pos = textPad.index('end')
        err, reply = lock_line(user, currentfile, pos)
        word = textPad.get(str(float(pos)), str(pos) + '.end')
        if err == "":
            if reply == False:
                textPad.tag_add('locked', let, str(pos) + '.end')
                if (float(pos) == 1.0):
                    textPad.insert('1.0', ' ', 'locked')
                if (float(last_pos) - 1) == float(let):
                    textPad.insert('end', '\n', 'locked')

                print 'line locked'
            else:
                if word != '':
                    try:
                        if index != endline:
                            part_1 = textPad.get(str(float(pos)),str(index))
                            part_2 = textPad.get(str(index), str(pos) + '.end')
                            send_new_edit(user, currentfile, pos,part_1,False)
                            #lock_line(user, currentfile,pos+1)
                            send_new_edit(user,currentfile,pos+1,part_2,True)
                            print 'this is part_1 %s'%part_1
                            print 'this is part 2 %s'%part_2
                            print pos+1
                        else:

                            send_new_edit(user,currentfile,pos,word,True)
                    except:
                        print 'Error occured'
                    # textPad.tag_delete('locked', let, str(pos) + '.end')
                    print word
        else:
            print err


            # open new view to input file name

    def new_file(self):
        newfile = createFile()
        newfile.newfileview(user, self.userfiles)

    # close connection
    def exit_command(self):

        if tkMessageBox.askokcancel("Quit", "Do you really want to quit?"):
            stop_listening()

    def about_command(self):
        label = tkMessageBox.showinfo("About", "Home work for Distributed Systems (2016)")

    # open files that user can edit
    def member(self):
        self.error, self.userfiles, self.memberfiles = get_files(user)
        if len(self.memberfiles) == 0:
            label = tkMessageBox.showinfo("Error message", "No file to open")
        else:
            callview = view()
            callview.views(self.memberfiles, user, 'member')

            # list files that user can invite and delete client

    def master(self):
        self.error, self.userfiles, self.memberfiles = get_files(user)
        if len(self.userfiles) == 0:
            label = tkMessageBox.showinfo("Error message", "You do not own any file at this moment")
        else:
            callview = view()
            callview.views(self.userfiles, user, 'master')


class view:
    def views(self, files, username, type):

        self.username = username
        self.root = Tk()
        self.type = type
        self.files = files
        self.list_box_1 = Listbox(self.root, width=100, height=20, selectmode=EXTENDED)
        self.list_box_1.grid(row=0, column=0)
        self.list_box_1.pack()
        # if usertype is master, then user can delete files

        if self.type == "master":
            self.delete_button = Button(self.root, text="Delete", command=self.DeleteSelection)
            self.delete_button.pack(side="right")
            self.editor_button = Button(self.root, text="[Editor Review]", command=self.EditorSelection)
            self.editor_button.pack(side="right")

        # universal menu for both master and member
        self.back_button = Button(self.root, text="<Back", command=self.Close)
        self.back_button.pack(side="left")

        self.open_button = Button(self.root, text="[Open File]", command=self.Selected)
        # self.open_button.grid(row=1, col=0)
        self.open_button.pack(side='left')
        # list files in list
        for item in self.files:
            self.list_box_1.insert(END, item)
        self.root.mainloop()

    def Selected(self):
        index = self.list_box_1.curselection()[0]
        selected_file = self.list_box_1.get(index)
        if tkMessageBox.askokcancel("Open file", "Do you really want to open file %s?" % selected_file):
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
            # send file update to server

    def EditorSelection(self):
        try:
            index = self.list_box_1.curselection()[0]
            selected_file = self.list_box_1.get(index)
            self.root.destroy()
            callEditor = Editor()
            callEditor.Editor_view(self.username, self.files, selected_file, self.type)
        except:
            print "nothing selected"

    def Close(self):

        self.root.destroy()


lbt = view()


class createFile():
    def newfileview(self, username, userfiles):
        self.fileview = Tk()
        self.userfiles = userfiles
        Label(self.fileview, text="Create New File, you will be the master of this file").grid(row=0)
        self.filename = Entry(self.fileview)
        self.filename.grid(row=0, column=1)
        Button(self.fileview, text='Create File', command=self.create).grid(row=3, column=1, sticky=W, pady=4)

    def create(self):
        file = (self.filename.get().split(".")[0])
        file = file.replace(" ", "")

        if file != "":
            error_message = create_file(user, file + ".txt")  # changed it to user from self.username
            if error_message == "":
                self.fileview.destroy()
                self.userfiles.append(file + ".txt")
                openfile = app()
                openfile.open(file + ".txt")
            else:
                Label = tkMessageBox.showinfo("Error", error_message)
        else:
            Label = tkMessageBox.showinfo("Error", "Invalid Text Input")

        print file


class Editor():
    def Editor_view(self, username, files, selected_file, type):
        self.username = username
        self.files = files
        self.selected_file = selected_file
        self.type = type
        self.root = Tk()
        self.list_box_1 = Listbox(self.root, width=50, height=20, selectmode=EXTENDED)
        self.list_box_1.grid(row=0, column=0)
        self.root.title('Control Editor for  ' + self.selected_file)
        self.list_box_1.pack()
        errors, self.editors = get_editors(self.username, self.selected_file)
        if len(self.editors) == 0:
            self.editors = []
        self.add_button = Button(self.root, text="Add Editor >", command=self.Selected)
        self.add_button.pack(side='left')
        self.remove_button = Button(self.root, text=" Remove Editor ", command=self.DeleteSelection)
        self.remove_button.pack(side='right')
        self.editor_name = Entry(self.root)
        self.editor_name.pack()
        self.populate(self.editors, self.list_box_1)
        self.root.mainloop()

    def populate(self, input, name):
        for item in input:
            name.insert(END, item)

    def Selected(self):
        editor_name = self.editor_name.get()
        if editor_name != '':
            if tkMessageBox.askokcancel("Message", "Do you want to give this user Editor right %s?" % editor_name):
                message = add_editor(self.username, self.selected_file, editor_name)
                if message == "":
                    self.editors.insert(0, editor_name)
                    self.list_box_1.insert(0, editor_name)
                else:
                    Label = tkMessageBox.showinfo("Error", message)

    def DeleteSelection(self):
        items = self.list_box_1.curselection()
        pos = 0
        try:
            index = self.list_box_1.curselection()[0]
            seltext = self.list_box_1.get(index)
            if tkMessageBox.askokcancel("Message", "Are you sure you want to remove user %s?" % seltext):
                message = remove_editor(self.username, self.selected_file, seltext)
                if message == "":
                    for i in items:
                        idx = int(i) - pos
                        self.list_box_1.delete(idx, idx)
                        pos = pos + 1
                else:
                    Label = tkMessageBox.showinfo("Error", message)
        except:
            print 'nothing selected'

    def back(self):
        self.root.destroy()
        callview = view()
        callview.views(self.files, self.username, self.type)


loadEditor = Editor()


class wait_for_edits(threading.Thread):
    def __init__(self, q):
        """
       Tries to get edits from Queue (blocking) and puts them into file in GUI
       @param q: queue
       @type q: Queue.Queue
       """

        super(wait_for_edits, self).__init__()
        self.q = q
        self._is_running = True

    def run(self):
        # Loop until program is closed from server
        while self._is_running:
            line_no, line_content = self.q.get()
            next_pos = line_no + 1
            print "Line: " + str(line_no) + ": " + line_content
            textPad.tag_remove('locked', str(float(line_no)),str(float(next_pos)))
            textPad.delete(str(float(line_no)), str(line_no) + '.end')
            textPad.insert(str(float(line_no)), line_content, 'locked')
            # TODO add this line to GUI!!!


class ReadonlyText(Text):
    '''A text widget that doesn't permit inserts and deletes in regions tagged with "locked"'''

    def __init__(self, *args, **kwargs):
        Text.__init__(self, *args, **kwargs)

        # this code creates a proxy that will intercept
        # each actual insert and delete.
        self.tk.eval(WIDGET_PROXY)

        # this code replaces the low level tk widget
        # with the proxy
        widget = str(self)
        self.tk.eval('''
            rename {widget} _{widget}
            interp alias {{}} ::{widget} {{}} widget_proxy _{widget}
        '''.format(widget=widget))


WIDGET_PROXY = '''
if {[llength [info commands widget_proxy]] == 0} {
    # Tcl code to implement a text widget proxy that disallows
    # insertions and deletions in regions marked with "locked"
    proc widget_proxy {actual_widget args} {
        set command [lindex $args 0]
        set args [lrange $args 1 end]
        if {$command == "insert"} {
            set index [lindex $args 0]
            if [_is_locked $actual_widget $index "$index+1c"] {
                bell
                return ""
            }
        }
        if {$command == "delete"} {
            foreach {index1 index2} $args {
                if {[_is_locked $actual_widget $index1 $index2]} {
                    bell
                    return ""
                }
            }
        }
        # if we passed the previous checks, allow the command to
        # run normally
        $actual_widget $command {*}$args
    }
    proc _is_locked {widget index1 index2} {
        # return true if any text in the range between
        # index1 and index2 has the tag "locked"
        set result false
        if {$index2 eq ""} {set index2 "$index1+1c"}
        # see if "locked" is applied to any character in the
        # range. There's probably a more efficient way to do this, but
        # this is Good Enough
        for {set index $index1} \
            {[$widget compare $index < $index2]} \
            {set index [$widget index "$index+1c"]} {
                if {"locked" in [$widget tag names $index]} {
                    set result true
                    break
                }
            }
        return $result
    }
}
'''
