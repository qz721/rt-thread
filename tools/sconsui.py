#! /usr/bin/env python
#coding=utf-8

import sys

py2 = py30 = py31 = False
version = sys.hexversion
if version >= 0x020600F0 and version < 0x03000000 :
    py2 = True    # Python 2.6 or 2.7
    from Tkinter import *
    import ttk
elif version >= 0x03000000 and version < 0x03010000 :
    py30 = True
    from tkinter import *
    import ttk
elif version >= 0x03010000:
    py31 = True
    from tkinter import *
    import tkinter.ttk as ttk
else:
    print ("""
    You do not have a version of python supporting ttk widgets..
    You need a version >= 2.6 to execute PAGE modules.
    """)
    sys.exit()

import ScrolledText
import tkFileDialog
import tkMessageBox

import os
import threading
import platform

builder = None
executor = None
lock = None

class CmdExecutor(threading.Thread):
    def __init__(self, cmd, output):
        threading.Thread.__init__(self) 
        self.cmd = cmd
        self.child = None

    def run(self):
        global executor
        
        if platform.system() == 'Windows':
            from win32spawn import Win32Spawn
            
            subprocess = Win32Spawn(self.cmd)
            subprocess.start_pipe()
            
            builder.progressbar.start()
            while not subprocess.is_terminated or subprocess.qsize() > 0:
                try:
                    line = subprocess.get(timeout=1)
                    line = line.replace('\r', '')
                    if line:
                        lock.acquire()
                        builder.output.see(END)
                        builder.output.insert(END, line)
                        lock.release()
                except:
                    pass

            builder.progressbar.stop()

        executor = None

def ExecCmd(cmd):
    global executor
    if executor:
        print 'cmd not exit, return'
        return

    executor = CmdExecutor(cmd, builder)
    executor.start()

class DirSelectBox(ttk.Frame):
    def __init__(self, master=None, **kw):
        ttk.Frame.__init__(self, master, **kw)
        self.dir_var = StringVar()
        self.entry = ttk.Entry(self, textvariable = self.dir_var)
        self.entry.pack(fill=BOTH, expand=1,side=LEFT)
        self.entry.configure(width = 50)
        
        self.browser_button = ttk.Button(self, text="Browser", command=self.browser)
        self.browser_button.pack(side=RIGHT)

    def browser(self):
        dir = tkFileDialog.askdirectory(parent=self, title='Open directory', initialdir=self.dir_var.get())
        if dir != '':
            self.dir_var.set(dir)

    def set_path(self, path):
        path = path.replace('\\', '/')
        self.dir_var.set(path)
    
    def get_path(self):
        return self.dir_var.get()

COMPILER = [
        ("GNU GCC", "GCC"),
        ("Keil ARMCC", "ARMCC"),
        ("IAR Compiler", "IAR"),
    ]

IDE = [
    ('Keil MDK4', 'mdk4'),
    ('Keil MDK', 'mdk'),
    ('IAR Compiler', 'iar')
]

class SconsUI():
    def __init__(self, master=None):
        style = ttk.Style()
        theme = style.theme_use()
        default = style.lookup(theme, 'background')
        master.configure(background=default)
        
        notebook = ttk.Notebook(master)
        notebook.pack(fill=BOTH, padx=5, pady=5)
        
        # building page 
        page_building = ttk.Frame(notebook)
        notebook.add(page_building, padding=3)
        notebook.tab(0, text='Build', underline="-1")
        self.setup_building_ui(page_building)
        
        # make project page
        page_project = ttk.Frame(notebook)
        notebook.add(page_project, padding = 3)
        notebook.tab(1, text = 'Project', underline = '-1')
        self.setup_project_ui(page_project)
        
        # setting page 
        page_setting = ttk.Frame(notebook)
        notebook.add(page_setting, padding = 3)
        notebook.tab(2, text = 'Setting', underline = '-1')
        self.setup_setting_ui(page_setting)
        
        padding = ttk.Frame(master)
        padding.pack(fill=X)
        quit = ttk.Button(padding, text='Quit', command = self.quit)
        quit.pack(side=RIGHT)

        # read setting 
        self.read_setting()
        
    def read_setting(self):
        import platform
        import os
        
        home = ''
        if platform.system() == 'Windows':
            driver = os.environ['HOMEDRIVE']
            home = os.environ['HOMEPATH']
            home = os.path.join(driver, home)
        else:
            home = os.environ['HOME']
        
        setting_path = os.path.join(home, '.rtt_scons')
        if os.path.exists(setting_path):
            setting = file(os.path.join(home, '.rtt_scons'))
            for line in setting:
                line = line.replace('\n', '')
                line = line.replace('\r', '')
                if line.find('=') != -1:
                    items = line.split('=')
                    if items[0] == 'RTTRoot':
                        self.RTTRoot.set_path(items[1])
                    elif items[0] == 'BSPRoot':
                        self.BSPRoot.set_path(items[1])
                    elif items[0] == 'compiler':
                        compiler = items[1]
                    else:
                        self.CompilersPath[items[0]].set_path(items[1])
            setting.close()

        # set  RT-Thread Root Directory according environ
        if os.environ.has_key('RTT_ROOT'):
            self.RTTRoot.set_path(os.environ['RTT_ROOT'])
        
        # detect compiler path
        if platform.system() == 'Windows':
            # Keil MDK
            if not self.CompilersPath['ARMCC'].get_path():
                if os.path.exists('C:\\Keil'):
                    self.CompilersPath['ARMCC'].set_path('C:\\Keil')
                elif os.path.exists('D:\\Keil'):
                    self.CompilersPath['ARMCC'].set_path('D:\\Keil')
                elif os.path.exists('E:\\Keil'):
                    self.CompilersPath['ARMCC'].set_path('E:\\Keil')
                elif os.path.exists('F:\\Keil'):
                    self.CompilersPath['ARMCC'].set_path('F:\\Keil')
                elif os.path.exists('G:\\Keil'):
                    self.CompilersPath['ARMCC'].set_path('G:\\Keil')

            # GNU GCC
            if not self.CompilersPath['GCC'].get_path():
                paths = os.environ['PATH']
                paths = paths.split(';')
                
                for path in paths:
                    if path.find('CodeSourcery') != -1:
                        self.CompilersPath['GCC'].set_path(path)
                        break
                    elif path.find('GNU Tools ARM Embedded') != -1:
                        self.CompilersPath['GCC'].set_path(path)
                        break

    def save_setting(self):
        import platform
        import os

        home = ''
        if platform.system() == 'Windows':
            driver = os.environ['HOMEDRIVE']
            home = os.environ['HOMEPATH']
            home = os.path.join(driver, home)
        else:
            home = os.environ['HOME']

        setting = file(os.path.join(home, '.rtt_scons'), 'wb+')
        # current comiler 
        # line = '%s=%s\n' % ('compiler', self.compilers.get()))
        line = '%s=%s\n' % ('compiler', 'iar')
        setting.write(line)

        # RTT Root Folder
        if self.RTTRoot.get_path():
            line = '%s=%s\n' % ('RTTRoot', self.RTTRoot.get_path())
            setting.write(line)

        # BSP Root Folder
        if self.BSPRoot.get_path():
            line = '%s=%s\n' % ('BSPRoot', self.BSPRoot.get_path())
            setting.write(line)

        for (compiler, path) in self.CompilersPath.iteritems():
            if path.get_path():
                line = '%s=%s\n' % (compiler, path.get_path())
                setting.write(line)

        setting.close()
        tkMessageBox.showinfo("RT-Thread SCons UI",
                    "Save setting sucessfully")

    def setup_building_ui(self, frame):
        padding = ttk.Frame(frame)
        padding.pack(fill=X)
        
        button = ttk.Button(padding, text='Clean', command=self.do_clean)
        button.pack(side=RIGHT)
        button = ttk.Button(padding, text='Build', command=self.do_build)
        button.pack(side=RIGHT)
        label = ttk.Label(padding, relief = 'flat', text = 'Click Build or Clean to build or clean system -->')
        label.pack(side=RIGHT, ipady = 5)
        
        self.progressbar = ttk.Progressbar(frame)
        self.progressbar.pack(fill=X)
        
        separator = ttk.Separator(frame)
        separator.pack(fill=X)

        self.output = ScrolledText.ScrolledText(frame)
        self.output.pack(fill=X)

    def setup_project_ui(self, frame):
        label = ttk.Label(frame, relief = 'flat', text = 'Choose Integrated Development Environment:')
        label.pack(fill=X, pady = 5)
        
        separator = ttk.Separator(frame)
        separator.pack(fill=X)
    
        self.ide = StringVar()
        self.ide.set("mdk4") # initialize
        
        for text,mode in IDE:
            radiobutton = ttk.Radiobutton(frame, text=text, variable = self.ide, value = mode)
            radiobutton.pack(fill=X, padx=10)
    
        bottom = ttk.Frame(frame)
        bottom.pack(side=BOTTOM, fill=X)
        button = ttk.Button(bottom, text="Make Project", command = self.do_make_project)
        button.pack(side=RIGHT, padx = 10, pady = 10)

    def setup_setting_ui(self, frame):
        row = 0
        label = ttk.Label (frame, relief = 'flat', text='RT-Thread Root Folder:')
        label.grid(row=row, column=0,ipadx=5, ipady=5, padx = 5)
    
        self.RTTRoot = DirSelectBox(frame)
        self.RTTRoot.grid(row=row, column=1, sticky=E+W)
        row = row + 1
    
        label = ttk.Label (frame, relief = 'flat', text='Board Support Folder:')
        label.grid(row=row, column=0,ipadx=5, ipady=5, padx = 5)
    
        self.BSPRoot = DirSelectBox(frame)
        self.BSPRoot.grid(row=row, column=1, sticky=E+W)
        row = row + 1
    
        label = ttk.Label (frame, relief='flat', text='Toolchain:')
        label.grid(row=row, column=0,ipadx=5, ipady=5, sticky=E+W)
        row = row + 1
        
        separator = ttk.Separator(frame)
        separator.grid(row = row, column = 0, columnspan = 2, sticky = E+W)
        row = row + 1
        
        self.compilers = StringVar()
        self.compilers.set("GCC") # initialize

        self.CompilersPath = {}

        for text,compiler in COMPILER:
            radiobutton = ttk.Radiobutton(frame, text=text, variable = self.compilers, value = compiler)
            radiobutton.grid(row=row, column = 0, sticky = W, ipadx = 5, ipady = 5, padx = 20)

            self.CompilersPath[compiler] = DirSelectBox(frame)
            self.CompilersPath[compiler].grid(row=row, column=1, sticky=E+W)
            row = row + 1
    
        button = ttk.Button(frame, text='Save Setting', command = self.save_setting)
        button.grid(row = row, column = 1, sticky = E)
        row = row + 1

    def prepare_build(self):
        # get compiler 
        compiler = self.compilers.get()
        if compiler == 'GCC':
            compiler = 'gcc'
        elif compiler == 'ARMCC':
            compiler = 'keil'
        elif compiler == 'IAR':
            compiler = 'iar'

        # get RTT Root
        rtt_root = self.RTTRoot.get_path()
        # get Compiler path 
        exec_path = self.CompilersPath[self.compilers.get()].get_path()
        
        command = ''

        os.environ['RTT_ROOT'] = rtt_root
        os.environ['RTT_CC'] = compiler
        os.environ['RTT_EXEC_PATH'] = exec_path
        
        return command 
        
    def do_build(self):
        self.prepare_build()
        command = 'scons'

        bsp = self.BSPRoot.get_path()
        os.chdir(bsp)

        self.output.delete(1.0, END)
        self.output.insert(END, 'building project...\n')
        ExecCmd(command)        
    
    def do_clean(self):
        self.prepare_build()
        command = 'scons -c'

        bsp = self.BSPRoot.get_path()
        os.chdir(bsp)

        self.output.delete(1.0, END)
        self.output.insert(END, 'clean project...\n')
        ExecCmd(command)
    
    def do_make_project(self):
        ide = self.ide.get()
        self.prepare_build()
        command = 'scons --target=%s -s' % ide
        
        bsp = self.BSPRoot.get_path()
        os.chdir(bsp)

        self.output.delete(1.0, END)
        self.output.insert(END, 'make project ...\n')
        ExecCmd(command)

    def quit(self):
        exit(0)

def StartSConsUI(path=None):
    global val, root
    root = Tk()
    root.title('RT-Thread SCons UI')
    root.geometrygeometry('590x510+50+50')
    lock = threading.RLock()
    builder = SconsUI(root)
    if path:
        builder.BSPRoot.set_path(path)
    root.mainloop

if __name__ == '__main__':
    global val, root
    root = Tk()
    root.title('scons_builder')
    root.geometry('590x510+50+50')
    lock = threading.RLock()
    scons_ui = SconsUI(root)
    builder = scons_ui
    root.mainloop()