import Tkinter
import tkMessageBox
import ttk
import threading
from functools import partial
from sessions.client.main import *
from Queue import Empty
import time


def main():
    root = RootWindow()
    root.mainloop()
    try:
        root.close_file()
    except (AttributeError, Tkinter.TclError):
        pass


class RootWindow(Tkinter.Tk, object):

    def __init__(self):
        super(RootWindow, self).__init__()

        self.username = None

        # Frames
        self.login_frame = LoginFrame(self)
        self.main_frame = MainFrame(self)
        self.text_frame = TextFrame(self)

        self.login_frame.pack(fill=Tkinter.BOTH)

    def login(self, login_input):
        self.username = login_input.get()
        self.login_frame.pack_forget()
        self.main_frame.pack(fill=Tkinter.BOTH)

        self.wm_title('Colted - {0}'.format(self.username))

    def get_files(self):
        error, owned_files, other_files = get_files(self.username)

        if error != "":
            tkMessageBox.showerror('Error', error)

        return owned_files, other_files

    def create_file(self, fname):
        error = create_file(self.username, fname)

        if error != '':
            tkMessageBox.showerror('Error', error)
            return False

        return True

    def get_editors(self, fname):

        error, editors = get_editors(self.username, fname)

        if error != '':
            tkMessageBox.showerror('Error', error)
            return []

        return editors

    def open_file(self, fname):

        error, content, queue = open_file(self.username, fname)

        if error != '':
            tkMessageBox.showerror('Error', error)
            return ''

        self.text_frame.textarea.delete('1.0', Tkinter.END)
        self.text_frame.textarea.insert(Tkinter.END, content)
        self.main_frame.pack_forget()
        self.text_frame.pack(fill=Tkinter.BOTH)

        self.edits_listener = EditsListener(queue, self.text_frame)
        self.text_frame._is_running = True  # Periodic updates are ready to run
        self.text_frame.open(self.username, fname)
        self.wm_title('Colted - {0}'.format(fname))  # Set file name as a title

    def close_file(self):
        self.edits_listener._is_running = False
        self.text_frame._is_running = False
        stop_listening()

        self.wm_title('Colted - {0}'.format(self.username))

        self.text_frame.pack_forget()
        self.main_frame.pack(fill=Tkinter.BOTH)

    def add_editor(self, fname, editor):

        error = add_editor(self.username, fname, editor)

        if error != '':
            tkMessageBox.showerror('Error', error)
            return False

        return True

    def remove_editor(self, fname, editor):

        error = remove_editor(self.username, fname, editor)

        if error != '':
            tkMessageBox.showerror('Error', error)
            return False

        return True


class LoginFrame(Tkinter.Frame, object):

    def __init__(self, parent):
        super(LoginFrame, self).__init__(parent)

        self.parent = parent

        Tkinter.Label(self, text='Username:').pack(side=Tkinter.LEFT)
        login_input = Tkinter.Entry(self)
        login_input.pack(side=Tkinter.LEFT, padx=10, fill=Tkinter.BOTH)
        login_button = Tkinter.Button(self, text="Login", width=10, command=partial(self.login, login_input))
        login_button.pack(side=Tkinter.LEFT)

    def login(self, login_input):
        self.parent.login(login_input)


class MainFrame(Tkinter.Frame, object):

    def __init__(self, parent):
        super(MainFrame, self).__init__(parent)

        self.parent = parent

        new_file_input = Tkinter.Entry(self)
        new_file_input.grid(row=0, column=1)
        Tkinter.Button(self, text="Make new file", command=partial(self.create_file, new_file_input)).grid(row=0, column=2)

        ttk.Separator(self, orient=Tkinter.HORIZONTAL).grid(row=1, column=0, columnspan=10, sticky='ew')

        Tkinter.Label(self, text='Owned files:').grid(row=2, column=0)
        self.owned_files_listbox = Tkinter.Listbox(self, selectmode=Tkinter.SINGLE)
        self.owned_files_listbox.grid(row=3, column=0, rowspan=10)
        self.owned_files_listbox.bind('<<ListboxSelect>>', self.owned_files_listbox_onselect)

        Tkinter.Label(self, text='Other files:').grid(row=13, column=0)
        self.other_files_listbox = Tkinter.Listbox(self, selectmode=Tkinter.SINGLE)
        self.other_files_listbox.grid(row=14, column=0, rowspan=10)
        self.other_files_listbox.bind('<<ListboxSelect>>', self.other_files_listbox_onselect)


        Tkinter.Button(self, text="Open selected file", command=self.open_file).grid(row=25, column=0)

        Tkinter.Label(self, text='Editors of selected owned file:').grid(row=2, column=1)
        self.editors_listbox = Tkinter.Listbox(self, selectmode=Tkinter.SINGLE)
        self.editors_listbox.grid(row=3, column=1, rowspan=10)

        new_editor_input = Tkinter.Entry(self)
        new_editor_input.grid(row=3, column=2)
        Tkinter.Button(self, text="Add editor", command=partial(self.add_editor, new_editor_input)).grid(row=4, column=2)
        Tkinter.Button(self, text="Remove selected editor", command=self.remove_editor).grid(row=12, column=2)

    def pack(self, *args, **kwargs):
        super(MainFrame, self).pack(*args, **kwargs)

        self.refresh_files()

    def owned_files_listbox_onselect(self, event):
        w = event.widget
        try:
            index = int(w.curselection()[0])
            fname = w.get(index)
            self.seleted_fname = fname

            self.editors_listbox.delete(0, Tkinter.END)
            for editor in self.parent.get_editors(fname):
                self.editors_listbox.insert(Tkinter.END, editor)

        except (KeyError, IndexError):
            pass

    def other_files_listbox_onselect(self, event):
        w = event.widget
        index = int(w.curselection()[0])
        self.refresh_files()
        self.other_files_listbox.select_set(index) #Select item selected before refreshing

    def refresh_files(self):

        owned_files, other_files = self.parent.get_files()

        self.owned_files_listbox.delete(0, Tkinter.END)
        for fname in owned_files:
            self.owned_files_listbox.insert(Tkinter.END, fname)

        self.other_files_listbox.delete(0, Tkinter.END)
        for fname in other_files:
            self.other_files_listbox.insert(Tkinter.END, fname)

    def create_file(self, new_file_input):
        fname = new_file_input.get()
        new_file_input.delete(0, Tkinter.END)

        if self.parent.create_file(fname):
            self.refresh_files()
            # open the created file
            self.open_file(fname)

    def open_file(self, fname=None):

        if fname is None:

            for widget in (self.owned_files_listbox, self.other_files_listbox):
                selection = widget.curselection()

                if selection:
                    fname = widget.get(int(selection[0]))
                    break
            else:
                return None

        self.parent.open_file(fname)

    def add_editor(self, new_editor_input):
        editor = new_editor_input.get()
        new_editor_input.delete(0, Tkinter.END)

        for widget in (self.owned_files_listbox, self.other_files_listbox):
            selection = widget.curselection()

            if selection:
                fname = widget.get(int(selection[0]))
                if self.parent.add_editor(fname, editor):
                    self.editors_listbox.insert(Tkinter.END, editor)

    def remove_editor(self):
        editor_selection = self.editors_listbox.curselection()

        if editor_selection:
            fname = self.seleted_fname
            editor = self.editors_listbox.get(int(editor_selection[0]))
            self.parent.remove_editor(fname, editor)

            self.editors_listbox.delete(int(editor_selection[0]))


class TextFrame(Tkinter.Frame, object):

    def __init__(self, parent):
        super(TextFrame, self).__init__(parent)

        self.parent = parent

        Tkinter.Button(self, text="<< Back", command=self.parent.close_file).grid(row=0, column=0)
        self.textarea = Tkinter.Text(self)
        self.textarea.grid(row=1, column=0, columnspan=10)

        self.fname = None
        self.user = None
        self.lock = None

        self.change_made = False
        self._is_running = True

    def open(self, user, fname):
        self.user = user
        self.fname = fname

        self.textarea.bind('<Control-x>', lambda e: 'break')  # disable cut
        self.textarea.bind('<Control-c>', lambda e: 'break')  # disable copy
        self.textarea.bind('<Control-v>', lambda e: 'break')  # disable paste
        self.textarea.bind('<Button-3>', lambda e: 'break')  # disable right-click

        self.textarea.bind('<Key>', self.on_key_press)
        self.textarea.bind('<ButtonRelease-1>', self.on_click)
        self.textarea.bind('<Up>', self.move_up)
        self.textarea.bind('<Down>', self.move_down)
        self.textarea.bind('<KeyRelease-Left>', self.move_lr)
        self.textarea.bind('<KeyRelease-Right>', self.move_lr)
        self.textarea.bind('<BackSpace>', self.on_backspace_press)
        self.textarea.bind('<Return>', self.on_return_press)
        self.textarea.bind('<Delete>', self.on_delete_press)

        self.periodic_updates(0.5)

    def on_click(self, event):
        self.lock_line(self.line_no)

    def on_key_press(self, event):

        if self.textarea.tag_ranges(Tkinter.SEL):
            return 'break'

        if event.keysym in ('Shift_L', 'Control_L', 'Alt_L', 'End', 'Home', 'Left', 'Up', 'Right', 'Down'):
            return None

        if event.keysym in ('otilde', 'udiaeresis', 'adiaeresis', 'odiaeresis'):
            return 'break'

        if self.lock != self.line_no:
            return 'break'

        self.change_made = True

    def on_backspace_press(self, event):

        if self.textarea.tag_ranges(Tkinter.SEL):
            return 'break'

        # in case line is locked by other user do not erase
        if self.lock != self.line_no:
            return 'break'

        prev_line_no = self.line_no

        if prev_line_no == 1:
            self.change_made = True
            return None

        if self.col_no == 0:
            if self.lock_line(prev_line_no - 1):
                delete_line(self.user, self.fname, prev_line_no)
            else:
                return 'break'

        self.change_made = True

    def on_delete_press(self, event):

        if self.textarea.tag_ranges(Tkinter.SEL):
            return 'break'

        # If at the end of the line
        if self.col_no == int(self.textarea.index('{0}.end'.format(self.line_no)).split('.')[1]):
            return 'break'

        self.change_made = True

    def on_return_press(self, event):

        if self.textarea.tag_ranges(Tkinter.SEL):
            return 'break'

        line_no = self.line_no
        if line_no == self.lock:
            index = self.textarea.index(Tkinter.INSERT)
            part_1 = self.textarea.get(str(float(line_no)), str(index))
            part_2 = self.textarea.get(str(index), str(line_no) + '.end')
            send_new_edit(self.user, self.fname, line_no, part_1, False)
            send_new_edit(self.user, self.fname, line_no + 1, part_2, True)
            time.sleep(0.1) # A hack
            self.lock_line(line_no+1)
        else:
            return 'break'

    def move_lr(self, event):
        self.lock_line(self.line_no)

    def move_up(self, event):
        if self.line_no == self.lock:
            self.send_new_edit()

        if self.line_no == 1:
            self.lock_line(1)
        else:
            self.lock_line(self.line_no - 1)

    def move_down(self, event):
        if self.line_no == self.lock:
            self.send_new_edit()

        self.lock_line(self.line_no + 1)

    def lock_line(self, line_no):

        err, lock = lock_line(self.user, self.fname, line_no)

        if lock:
            self.lock = line_no
            return True
        else:
            self.lock = None
            return False

    def send_new_edit(self, is_new_line=False, *args):

        line_no = self.line_no

        if line_no == self.lock:
            send_new_edit(self.user, self.fname, line_no, self.line_content(line_no), is_new_line)

    def periodic_updates(self, t=5):

        if self.change_made:
            self.change_made = False
            self.send_new_edit()

        if not self._is_running:
            return None

        threading.Timer(2, partial(self.periodic_updates, t)).start()

    def line_content(self, line_no):
        return self.textarea.get(str(float(line_no)), str(line_no) + '.end')

    @property
    def line_no(self):
        return int(self.textarea.index(Tkinter.INSERT).split('.')[0])

    @property
    def col_no(self):
        return int(self.textarea.index(Tkinter.INSERT).split('.')[1])


class EditsListener(threading.Thread):
    def __init__(self, q, text_frame):
        """
       Tries to get edits from Queue (blocking) and puts them into file in GUI
       @param q: queue
       @type q: Queue.Queue
       """

        super(EditsListener, self).__init__()
        self.q = q
        self.text_frame = text_frame
        self._is_running = True

        self.start()

    def run(self):
        # Loop until program is closed from server
        while self._is_running:
            try:
                line_no, line_content, is_new_line = self.q.get(timeout=1)

                if line_content is None:
                    self.text_frame.textarea.delete(str(float(line_no)), str(float(line_no+1)))
                    if self.text_frame.lock is not None and self.text_frame.lock >= line_no:
                        self.text_frame.lock -= 1
                    continue

                line_content = line_content.strip()
                if is_new_line:
                    self.text_frame.textarea.insert(str(float(line_no)), line_content + '\n')

                    if self.text_frame.lock is not None and self.text_frame.lock >= line_no:
                        self.text_frame.lock += 1
                else:
                    self.text_frame.textarea.delete(str(float(line_no)), str(line_no) + '.end')
                    self.text_frame.textarea.insert(str(float(line_no)), line_content)

            except Empty:
                pass
