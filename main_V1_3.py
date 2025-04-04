'''
GVS AI Main
This program watches controls the main UI

Worker Threads are for collection / reading data without interrupting UI function

Version Log:
Author: Kevin Lay
V1_0 Init Made revision with "Tabs", going to change to customTkinter going forward
V1_1 Implementing CustomTkinter
V1_2 Implementing Functionality To Screens
V1_3 Finishing Tag import screen, Named frames instead of numbering to make future expansion easier, Added Omron Connection Close On Screen Change, Clean up all frames on screen change
'''

import tkinter
import time
import threading
import traceback
import queue
import customtkinter
from PIL import Image, ImageTk
from tkinter import ttk
import getSetIP_V1_0 as getsetIP
from dataLogger_V1_1 import gvsDB
import ipaddress
import traceback
import abPLC_V1_0 as abPLC
import nxOmronPLC_V1_2 as nxOmronPLC
from datetime import datetime
import aphyt

# Custom Tkinter Setup
customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class GuiPart(customtkinter.CTk):

    def __init__(self, master, queue_, endCommand):
        super().__init__()
        self.versionLong = "GVS AI V1_3"
        self.queue = queue_
        self.master = master
        self.master.title(self.versionLong)

        ico = Image.open("resources/gvsIcon.png")
        photo = ImageTk.PhotoImage(ico)
        self.master.wm_iconphoto(False, photo)

        # Configure Window Size
        self.windowx = 1915
        self.windowy = 1015
        self.master.geometry(f"{self.windowx}x{self.windowy}+0+0")
        self.master.resizable(width=False, height=False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Treeview", background="#212121", foreground="black", rowheight=25, fieldbackground="D3D3D3")
        self.style.configure("Treeview.Heading", background="#212121", foreground="white", font=(None, 8))
        self.style.map("Treeview.Heading", background=[('selected','#EB8613')], foreground=[('selected', 'black')])
        self.style.map('Treeview', background=[('selected', '#EB8613')], foreground=[('selected', 'black')])

        # Configure Left Side Bar Frame
        self.frame = customtkinter.CTkFrame(master=self.master, width=225, height=1080, corner_radius=0)
        self.frame.place(x=0, y=0)

        # Left Side Bar --> Title
        title = customtkinter.CTkLabel(master=self.frame, text=self.versionLong, font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=112, y=50, anchor='center')

        # Left Side Bar --> View
        title = customtkinter.CTkLabel(master=self.frame, text="View:", font=customtkinter.CTkFont(size=14))
        title.place(x=112, y=100, anchor='center')

        # Left Side Bar --> main
        self.button_mainMenu_main = customtkinter.CTkButton(master=self.frame, text="Main", command=self.open_main)
        self.button_mainMenu_main.place(x=112, y=150, anchor='center')

        # Left Side Bar --> Tag Overview
        self.button_mainMenu_tagOverview = customtkinter.CTkButton(master=self.frame, text="Tag Overview", command=self.open_tagOverview)
        self.button_mainMenu_tagOverview.place(x=112, y=200, anchor='center')

        # Left Side Bar --> Fault Log
        self.button_mainMenu_faultLog = customtkinter.CTkButton(master=self.frame, text="Fault Log", command=self.open_faultLog)
        self.button_mainMenu_faultLog.place(x=112, y=250, anchor='center')

        # Left Side Bar --> Setup
        title = customtkinter.CTkLabel(master=self.frame, text="Setup:", font=customtkinter.CTkFont(size=14))
        title.place(x=112, y=300, anchor='center')

        # Left Side Bar --> Tag Setup
        self.button_mainMenu_tagSetup = customtkinter.CTkButton(master=self.frame, text="Tag Setup", command=self.open_tagSetup)
        self.button_mainMenu_tagSetup.place(x=112, y=350, anchor='center')

        # Left Side Bar --> Tag Import
        self.button_mainMenu_tagImport = customtkinter.CTkButton(master=self.frame, text="Tag Import", command=self.open_tagImport)
        self.button_mainMenu_tagImport.place(x=112, y=400, anchor='center')

        # Left Side Bar --> Configuration
        self.button_mainMenu_configuration = customtkinter.CTkButton(master=self.frame, text="Configuration", command=self.open_configuration)
        self.button_mainMenu_configuration.place(x=112, y=450, anchor='center')

        # Left Side Bar --> Bypass Setup
        self.button_mainMenu_bypassSetup = customtkinter.CTkButton(master=self.frame, text="Bypass Setup", command=self.open_bypassSetup)
        self.button_mainMenu_bypassSetup.place(x=112, y=500, anchor='center')

        # Left Side Bar --> Fault Log Setup
        self.button_mainMenu_faultLogSetup = customtkinter.CTkButton(master=self.frame, text="Fault Log Setup", command=self.open_faultLogSetup)
        self.button_mainMenu_faultLogSetup.place(x=112, y=550, anchor='center')

        # Left Side Bar --> Event Log
        self.button_mainMenu_eventLog = customtkinter.CTkButton(master=self.frame, text="Event Log", command=self.open_eventLog)
        self.button_mainMenu_eventLog.place(x=112, y=850, anchor='center')

        # Left Side Bar --> Help
        self.button_mainMenu_help = customtkinter.CTkButton(master=self.frame, text="Help", command=self.open_help)
        self.button_mainMenu_help.place(x=112, y=900, anchor='center')

        # Left Side Bar --> Setup Exit Button
        console = customtkinter.CTkButton(master=self.frame, text='Exit', command=endCommand)
        console.place(x=112, y=950, anchor='center')

        # Create Current Connection To Database
        self.connection = gvsDB("gvsAI")

        # Create Imported Tag List
        self.updateImportTagList()

        # Create Main View Table List
        self.updateDatabaseList()

        # UI Button And Object Functions
        self.framePosX = 220
        self.framePosY = 0
        self.frameSizeW = 1695 # Width & Height Of All Main Windows
        self.frameSizeH = 1015

        # Open Main window to start
        self.activeWindow = 0
        self.open_main()
        self.activeWindow = 2

    def open_main(self):
        self.closeWindows()
        self.activeWindow = 2
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Main Screen Opened")

        # Update Main View Table List
        self.updateDatabaseList()

        # Configure Main Viewing Frame
        self.frame_main = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_main.place(x=self.framePosX, y=self.framePosY)

        # Main Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_main, text="Main", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2, y=20, anchor='center')

        # Main View --> PLC Tag Data Type
        self.comboBoxTableList = customtkinter.CTkComboBox(master=self.frame_main, values=self.tableList, width=400)
        self.comboBoxTableList.place(x=1198, y=10)

        # Read The Columns In For Current Database Selection
        columnData = self.connection.readColumnsForTable(self.comboBoxTableList.get())

        # Create Column List
        columnList = []
        for column in columnData:
            columnList.append(column[0])

        # Create Data For Table
        mainTableData = self.connection.selectAllTable(self.comboBoxTableList.get())

        # Setup Scrollable Frame Window
        self.tree_frame = customtkinter.CTkFrame(master=self.frame_main, border_color="#EB8613", border_width=2)
        self.tree_frame.place(x=self.frameSizeW/2, y=40, anchor='n', height=950, width=1500)

        tree_scrollY = customtkinter.CTkScrollbar(self.tree_frame, width=15)
        tree_scrollY.pack(side='right', fill='y', padx=2, pady=2)
        tree_scrollX = customtkinter.CTkScrollbar(self.tree_frame, orientation='horizontal')
        tree_scrollX.pack(side='bottom', fill='x', padx=2, pady=2)

        # Setup Tree View
        self.my_tree = ttk.Treeview(master=self.tree_frame, height=45, yscrollcommand=tree_scrollY.set, xscrollcommand=tree_scrollX.set)

        # Configure the scrollbar
        tree_scrollY.configure(command=self.my_tree.yview)
        tree_scrollX.configure(command=self.my_tree.xview)

        # Need to get the column list to populate columns correctly. This column list drives the table creation

        # Define Our Columns
        self.my_tree['columns'] = columnList

        # Format Our Columns / Create Headings
        self.my_tree.column("#0", width=0, minwidth=0, stretch='NO')
        self.my_tree.heading("#0", text="", anchor='w')
        for column in self.my_tree['columns']:
            self.my_tree.column(column, anchor='w', width=200, minwidth=25)
            self.my_tree.heading(column, text=column, anchor='w')

        # Pack The Tree Widget
        self.my_tree.pack(padx=(8,0), pady=(8,0))

        # Alternating Line Colour
        self.my_tree.tag_configure('oddrow', background="lightgray", foreground='#1F538D')
        self.my_tree.tag_configure('evenrow', background="#1F538D", foreground='white')

        # Treeview Data
        data = mainTableData

        # Insert Data Into Treeview with For Loop
        count = 0
        for record in data:
            if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                self.my_tree.insert(parent='', index='end', iid=count, text="", values=record, tags=('evenrow',))
            else:
                self.my_tree.insert(parent='', index='end', iid=count, text="", values=record, tags=('oddrow',))
            # values could also = (record[0],record[1],record[2])
            count += 1

        # Var 1 For Threading
        self.label1variable = tkinter.StringVar()
        self.label1variable.set('41')
        label1 = customtkinter.CTkLabel(master=self.frame_main, textvariable=self.label1variable)
        label1.place(x=0,y=40, anchor='nw')

        # Var 2 For Threading
        self.label2variable = tkinter.StringVar()
        self.label2variable.set('41')
        label2 = customtkinter.CTkLabel(master=self.frame_main, textvariable=self.label2variable)
        label2.place(x=0,y=60, anchor='nw')

        # Var 3 For Threading
        self.label3variable = tkinter.StringVar()
        self.label3variable.set('41')
        label3 = customtkinter.CTkLabel(master=self.frame_main, textvariable=self.label3variable)
        label3.place(x=0,y=80, anchor='nw')

    def open_tagOverview(self):
        self.closeWindows()
        self.activeWindow = 3
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Tag Overview Screen Opened")

        # Update Imported Tag List
        self.updateImportTagList()

        # Configure Tag Overview Viewing Frame
        self.frame_tagOverview = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_tagOverview.place(x=self.framePosX, y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_tagOverview, text="Tag Overview", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        # Need To Grab Table Name --> Column Names --> Data

        # Setup Scrollable Frame Window
        self.tree_frameTagOverview = customtkinter.CTkFrame(master=self.frame_tagOverview, border_color="#EB8613", border_width=2)
        self.tree_frameTagOverview.place(x=self.frameSizeW/2, y=40, anchor='n', height=950, width=1404)

        tree_scrollY = customtkinter.CTkScrollbar(self.tree_frameTagOverview, width=15)
        tree_scrollY.pack(side='right', fill='y', padx=4, pady=2)

        # Setup Tree View
        self.my_treeTagOverview = ttk.Treeview(master=self.tree_frameTagOverview, height=45, yscrollcommand=tree_scrollY.set)

        # Configure the scrollbar
        tree_scrollY.configure(command=self.my_treeTagOverview.yview)

        # Need to get the column list to populate columns correctly. This column list drives the table creation

        # Define Our Columns
        self.my_treeTagOverview['columns'] = ("PLCTagName", "DataType", "LogValue", "TriggerTag", "DatabaseKey", "isFault", "isBypass")

        # Format Our Columns / Create Headings
        self.my_treeTagOverview.column("#0", width=0, minwidth=0, stretch='NO')
        self.my_treeTagOverview.heading("#0", text="", anchor='w')
        for column in self.my_treeTagOverview['columns']:
            self.my_treeTagOverview.column(column, anchor='w', width=200, minwidth=25)
            self.my_treeTagOverview.heading(column, text=column, anchor='w')

        # Pack The Tree Widget
        self.my_treeTagOverview.pack(padx=(8,0), pady=(8,2))

        # Alternating Line Colour
        self.my_treeTagOverview.tag_configure('oddrow', background="lightgray", foreground='#1F538D')
        self.my_treeTagOverview.tag_configure('evenrow', background="#1F538D", foreground='white')

        # Treeview Data
        data = self.importedTagListFull

        # Insert Data Into Treeview with For Loop
        count = 0
        for record in data:
            if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                self.my_treeTagOverview.insert(parent='', index='end', iid=count, text="", values=record, tags=('evenrow',))
            else:
                self.my_treeTagOverview.insert(parent='', index='end', iid=count, text="", values=record, tags=('oddrow',))
            # values could also = (record[0],record[1],record[2])
            count += 1

    def open_faultLog(self):
        self.closeWindows()
        self.activeWindow = 4
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Fault Log Screen Opened")

        # Update Imported Tag List
        self.updateImportTagList()

        # Configure Tag Overview Viewing Frame
        self.frame_faultlog = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_faultlog.place(x=self.framePosX, y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_faultlog, text="Fault Log", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

    def open_tagSetup(self):
        self.closeWindows()
        self.activeWindow = 5
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Tag Setup Screen Opened")

        # Update Imported Tag List
        self.updateImportTagList()

        # Configure Tag Setup Viewing Frame
        self.frame_tagSetup = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_tagSetup.place(x=self.framePosX, y=self.framePosY)

        # Tag Setup Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Tag Setup", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        # Tag Setup Frame --> Add/Remove Tags
        label = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Setup The Logging Of Tags", font=customtkinter.CTkFont(size=18, weight="bold"))
        label.place(x=20,y=60)

        # Configure Tag Setup --> PLC Tag Name
        label2 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="PLC Tag Name", font=customtkinter.CTkFont(size=16,))
        label2.place(x=20,y=100)

        # Configure Tag Setup --> Entry Box for PLC
        self.entry_tagSetup_plcTagName = customtkinter.CTkEntry(master=self.frame_tagSetup, placeholder_text="Select PLC Tag From List", width=400)
        self.entry_tagSetup_plcTagName.configure(state='disabled')
        self.entry_tagSetup_plcTagName.place(x=20, y=140)

        # Tag Setup Frame --> Log Value
        label3 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Log Value", font=customtkinter.CTkFont(size=16,))
        label3.place(x=20,y=180)

        # Tag Setup Frame --> Log Value
        self.comboBox_tagSetup_logValue = customtkinter.CTkComboBox(master=self.frame_tagSetup, values=["YES", "NO"], width=400)
        self.comboBox_tagSetup_logValue.place(x=20, y=220)

        # Tag Setup Frame --> Trigger Tag
        label4 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Trigger Tag", font=customtkinter.CTkFont(size=16,))
        label4.place(x=20,y=260)

        # Tag Setup Frame --> Trigger Tag
        self.updateImportTagList()
        self.comboBox_tagSetup_triggerTag = customtkinter.CTkComboBox(master=self.frame_tagSetup, values=self.importedTagList, width=400)
        self.comboBox_tagSetup_triggerTag.place(x=20, y=300)

        # Tag Setup Frame --> Database Key
        label5 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Database Key", font=customtkinter.CTkFont(size=16,))
        label5.place(x=20, y=340)

        # Tag Setup Frame --> Database Key
        self.updateImportTagList()
        self.comboBox_tagSetup_databaseKey = customtkinter.CTkComboBox(master=self.frame_tagSetup, values=self.importedTagList, width=400)
        self.comboBox_tagSetup_databaseKey.place(x=20, y=380)

        # Tag Setup Frame --> isFault
        label6 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="is Fault?", font=customtkinter.CTkFont(size=16,))
        label6.place(x=20, y=420)

        # Tag Setup Frame --> isFault
        self.updateImportTagList()
        self.comboBox_tagSetup_isFault = customtkinter.CTkComboBox(master=self.frame_tagSetup, values=["YES", "NO"], width=400)
        self.comboBox_tagSetup_isFault.place(x=20, y=460)

        # Tag Setup Frame --> isBypass
        label7 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="is Bypass?", font=customtkinter.CTkFont(size=16,))
        label7.place(x=20, y=500)

        # Tag Setup Frame --> isBypass
        self.updateImportTagList()
        self.comboBox_tagSetup_isBypass = customtkinter.CTkComboBox(master=self.frame_tagSetup, values=["YES", "NO"], width=400)
        self.comboBox_tagSetup_isBypass.place(x=20, y=540)

        # Tag Setup Frame --> Button For Saving
        self.button_tagSetup_save = customtkinter.CTkButton(master=self.frame_tagSetup, text="Save", command=self.button_tagSetup_saveIt)
        self.button_tagSetup_save.place(x=20, y=600)

        # Setup Scrollable Frame Window
        self.tree_frameTagSetup = customtkinter.CTkFrame(master=self.frame_tagSetup, border_color="#EB8613", border_width=2)
        self.tree_frameTagSetup.place(x=1675, y=40, anchor="ne", width=400, height=950)

        # Tag Import Viewing Frame --> Read Value
        label8 = customtkinter.CTkLabel(master=self.tree_frameTagSetup, text="List of Imported Tags", font=customtkinter.CTkFont(size=16,))
        label8.pack(pady=6)

        tree_scrollYtagOverview = customtkinter.CTkScrollbar(self.tree_frameTagSetup, width=15)
        tree_scrollYtagOverview.pack(side='right', fill='y', padx=4, pady=2)

        # Setup Tree View selectmode="" prevents selecting item
        self.my_treeTagSetup = ttk.Treeview(master=self.tree_frameTagSetup, height=40, yscrollcommand=tree_scrollYtagOverview.set)

        # Configure the scrollbar
        tree_scrollYtagOverview.configure(command=self.my_treeTagSetup.yview)

        # Define Our Columns
        self.my_treeTagSetup['columns'] = ("TagName")
        # Format Our Columns
        self.my_treeTagSetup.column("#0", width=0, minwidth=0, stretch='NO')
        self.my_treeTagSetup.column("TagName", anchor='w', width=600, minwidth=25)
        # Create Headings
        self.my_treeTagSetup.heading("#0", text="", anchor='w')
        self.my_treeTagSetup.heading("TagName", text="Tag Name", anchor='w')
        self.my_treeTagSetup.pack(padx=(8,0), pady=(8,4))
        # Alternating Line Colour
        self.my_treeTagSetup.tag_configure('oddrow', background="lightgray", foreground='#1F538D')
        self.my_treeTagSetup.tag_configure('evenrow', background="#1F538D", foreground='white')

        # Treeview Data
        data = self.importedTagList

        # Insert Data Into Treeview with For Loop
        count = 0
        for record in data:
            if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                self.my_treeTagSetup.insert(parent='', index='end', iid=count, text="", values=record, tags=('evenrow',))
            else:
                self.my_treeTagSetup.insert(parent='', index='end', iid=count, text="", values=record, tags=('oddrow',))
            # values could also = (record[0],record[1],record[2])
            count += 1

        # Bind Treeview click
        self.my_treeTagSetup.bind("<ButtonRelease-1>", self.tagSetupFillData)
        # Make the selection of the first item
        self.my_treeTagSetup.selection_set(0)
        self.tagSetupFillData(None)

        # Tag Setup Frame --> Note At Bottom
        label6 = customtkinter.CTkLabel(master=self.frame_tagSetup, text="Note: Trigger Tag & Database Key Selection Are Irrelevant If Log Value = No", font=customtkinter.CTkFont(size=14,))
        label6.place(x=20,y=980)

    def open_tagImport(self):
        self.closeWindows()
        self.activeWindow = 6
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Tag Import Screen Opened")

        # Update Imported Tag List
        self.updateImportTagList()

        # Configure Tag Overview Viewing Frame
        self.frame_tagImport = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_tagImport.place(x=self.framePosX, y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_tagImport, text="Tag Import", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        # Tag Import Viewing Frame --> Add/Remove Tags
        label = customtkinter.CTkLabel(master=self.frame_tagImport, text="Add / Remove Tags", font=customtkinter.CTkFont(size=18, weight="bold"))
        label.place(x=20,y=60)

        # Tag Import Viewing Frame --> PLC Tag Name
        label2 = customtkinter.CTkLabel(master=self.frame_tagImport, text="PLC Tag Name", font=customtkinter.CTkFont(size=16,))
        label2.place(x=20,y=100)

        # Entry Box for PLC
        self.entry_tagImport_plcTagName = customtkinter.CTkEntry(master=self.frame_tagImport, placeholder_text="Enter PLC Tag Name", width=400)
        self.entry_tagImport_plcTagName.place(x=20, y=140)

        # Tag Import Viewing Frame --> Data Type
        label3 = customtkinter.CTkLabel(master=self.frame_tagImport, text="Data Type", font=customtkinter.CTkFont(size=16,))
        label3.place(x=20,y=180)

        # Tag Import Viewing Frame --> PLC Tag Data Type
        self.comboBox_tagImport_plcDataType = customtkinter.CTkComboBox(master=self.frame_tagImport, values=["BOOL", "STRING", "FLOAT", "INT", "BYTES", "STRUCTURE"], width=400)
        self.comboBox_tagImport_plcDataType.place(x=20, y=220)

        # Button For Testing Tag
        self.button_tagTest = customtkinter.CTkButton(master=self.frame_tagImport, text="Tag Test", command=self.button_tagTest_CMD)
        self.button_tagTest.place(x=20, y=280)

        # Tag Import Viewing Frame --> Tag Successful / Fail
        self.label_tagTest = customtkinter.CTkLabel(master=self.frame_tagImport, text="Click Tag Test Button", font=customtkinter.CTkFont(size=16,))
        self.label_tagTest.place(x=180, y=280)

        # Tag Import Viewing Frame --> Read Value
        label4 = customtkinter.CTkLabel(master=self.frame_tagImport, text="Read Value", font=customtkinter.CTkFont(size=16,))
        label4.place(x=20, y=320)

        # Text Box for Read Value (read only)
        self.tagImport_textBox = customtkinter.CTkTextbox(master=self.frame_tagImport, width=400, height=16)
        self.tagImport_textBox.place(x=20, y=360)
        self.tagImport_textBox.insert("0.0", "Click Tag Test Button")
        self.tagImport_textBox.configure(state='disabled')

        # Button For Adding Tag
        button = customtkinter.CTkButton(master=self.frame_tagImport, text="Add Tag", command=self.button_tagAdd_CMD)
        button.place(x=20, y=420)

        # Button For Removing Tag
        button1 = customtkinter.CTkButton(master=self.frame_tagImport, text="Remove Tag", command=self.button_tagRemove_CMD)
        button1.place(x=200, y=420)

        # Need To Grab Table Name --> Column Names --> Data

        # Setup Scrollable Frame Window
        self.tree_frameTagImport = customtkinter.CTkFrame(master=self.frame_tagImport, border_color="#EB8613", border_width=2)
        self.tree_frameTagImport.place(x=1675, y=40, anchor="ne", width=400, height=950)

        # Tag Import Viewing Frame --> Read Value
        label5 = customtkinter.CTkLabel(master=self.tree_frameTagImport, text="List of Imported Tags", font=customtkinter.CTkFont(size=16,))
        label5.pack(pady=6)

        tree_scrollYtagOverview = customtkinter.CTkScrollbar(self.tree_frameTagImport, width=15)
        tree_scrollYtagOverview.pack(side='right', fill='y', padx=4, pady=2)

        # Setup Tree View selectmode="" prevents selecting item
        self.my_treeTagImport = ttk.Treeview(master=self.tree_frameTagImport, height=40, yscrollcommand=tree_scrollYtagOverview.set)

        # Configure the scrollbar
        tree_scrollYtagOverview.configure(command=self.my_treeTagImport.yview)

        # Define Our Columns
        self.my_treeTagImport['columns'] = ("TagName")
        # Format Our Columns
        self.my_treeTagImport.column("#0", width=0, minwidth=0, stretch='NO')
        self.my_treeTagImport.column("TagName", anchor='w', width=600, minwidth=25)
        # Create Headings
        self.my_treeTagImport.heading("#0", text="", anchor='w')
        self.my_treeTagImport.heading("TagName", text="Tag Name", anchor='w')
        self.my_treeTagImport.pack(padx=(8,0), pady=(8,4))
        # Alternating Line Colour
        self.my_treeTagImport.tag_configure('oddrow', background="lightgray", foreground='#1F538D')
        self.my_treeTagImport.tag_configure('evenrow', background="#1F538D", foreground='white')

        # Treeview Data
        data = self.importedTagList

        # Insert Data Into Treeview with For Loop
        count = 0
        for record in data:
            if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                self.my_treeTagImport.insert(parent='', index='end', iid=count, text="", values=record, tags=('evenrow',))
            else:
                self.my_treeTagImport.insert(parent='', index='end', iid=count, text="", values=record, tags=('oddrow',))
            # values could also = (record[0],record[1],record[2])
            count += 1

        # Bind Treeview click
        self.my_treeTagImport.bind("<ButtonRelease-1>", self.tagImportFillData)
        # Make the selection of the first item
        self.my_treeTagImport.selection_set(0)
        self.tagImportFillData(None)


        # Tag Import Viewing Frame --> Connecting To PLC
        label99 = customtkinter.CTkLabel(master=self.frame_tagImport, text="Connecting To PLC", fg_color="red", font=customtkinter.CTkFont(size=24,))
        label99.place(x=500, y=500)
        # To Make sure we wait for label to display??
        label99.update()
        # Get PLC Type
        user, username, plcType, ipAddress = self.connection.configurationRead()[0]
        # Opening Database Connection
        if plcType == 1:
            self.omronConnection = nxOmronPLC.omronConnection(ipAddress)
            self.connection.eventLogInsert(datetime.now(), 3, "Connected To Omron PLC")

        label99.destroy()

    def open_configuration(self):
        self.closeWindows()
        self.activeWindow = 7
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Configuration Screen Opened")
        
        # Collect Required Data for screen init
        eth0, wlan0 = self.updateIPAddresses()
        user, username, plcType, ipAddress = self.connection.configurationRead()[0]
        plcTypeString = self.plcTypeIntToString(plcType)

        # Configure Tag Overview Viewing Frame
        self.frame_openConfiguration = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_openConfiguration.place(x=self.framePosX, y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="Tag Configuration", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        # Labels for Settings
        label1 = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="PLC Type:", font=customtkinter.CTkFont(size=16, weight="bold"))
        label2 = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="PLC IP Address:", font=customtkinter.CTkFont(size=16, weight="bold"))
        label3 = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="ETH0 IP:", font=customtkinter.CTkFont(size=16, weight="bold"))
        label4 = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="WLAN IP:", font=customtkinter.CTkFont(size=16, weight="bold"))
        label5 = customtkinter.CTkLabel(master=self.frame_openConfiguration, text="When Changing ETH0/WLAN\nReboot Indicates Successful Change", font=customtkinter.CTkFont(size=16,))
        label1.place(x=20, y=40)
        label2.place(x=20, y=80)
        label3.place(x=20, y=120)
        label4.place(x=20, y=160)
        label5.place(x=30, y=200)

        # Combo Box For PLC Type
        self.comboBoxPLCType = customtkinter.CTkComboBox(master=self.frame_openConfiguration, values=["Allen Bradley", "Omron NX", "Siemens TIA"],)
        self.comboBoxPLCType.set(plcTypeString)
        self.comboBoxPLCType.place(x=200, y=40)

        # Entry Box for PLC IP Address
        self.entryPLCipAddress = customtkinter.CTkEntry(master=self.frame_openConfiguration)
        self.entryPLCipAddress.insert(0, ipAddress)
        self.entryPLCipAddress.place(x=200, y=80)

        # Entry Box for ETH0 IP Address
        self.entryEth0IP = customtkinter.CTkEntry(master=self.frame_openConfiguration)
        self.entryEth0IP.insert(0, eth0)
        self.entryEth0IP.place(x=200, y=120)

        # Entry Box for WLAN IP Address
        self.entryWLAN0IP = customtkinter.CTkEntry(master=self.frame_openConfiguration)
        self.entryWLAN0IP.insert(0, wlan0)
        self.entryWLAN0IP.place(x=200, y=160)

        # Button For Setting Eth0 IP
        button1 = customtkinter.CTkButton(master=self.frame_openConfiguration, text="Set", command=self.button_setEth0_IP)
        button1.place(x=400, y=120)

        # Button For Setting WLAN IP
        button2 = customtkinter.CTkButton(master=self.frame_openConfiguration, text="Set", command=self.button_setWlan0_IP)
        button2.place(x=400, y=160)

        # Button For Saving Config
        button3 = customtkinter.CTkButton(master=self.frame_openConfiguration, text="Save\nConfiguration", command=self.button_saveConfig)
        button3.place(x=1525, y=950)

        # Configure Deploy Label & Button Frame
        self.frame_openConfiguration_2 = customtkinter.CTkFrame(master=self.frame_openConfiguration, width=475, height=200,corner_radius=0, border_color="#EB8613", border_width=2)
        self.frame_openConfiguration_2.place(x=20, y=800)

        label61 = customtkinter.CTkLabel(master=self.frame_openConfiguration_2, text=""" This button will Deploy/Update/Modify the database.\n A database will be automatically built for each unique\nDatabase Key used in the Tag's Database Key field.\nThe columns will reflect time, Database Key, and each tag\nselected with that corresponding Database Key.""", font=customtkinter.CTkFont(size=16,))
        label61.place(x=475/2,y=20, anchor='n')

        # Button For Updating Database
        button4 = customtkinter.CTkButton(master=self.frame_openConfiguration_2, text="Deploy / Update\nDatabase", command=self.button_deployDB)
        button4.place(x=475/2,y=140, anchor='n')

    def open_bypassSetup(self):
        self.closeWindows()
        self.activeWindow = 8
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Bypass Setup Screen Opened")

        # Configure Tag Overview Viewing Frame
        self.frame_bypassSetup = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_bypassSetup.place(x=self.framePosX,y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_bypassSetup, text="Bypass Setup",font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

    def open_faultLogSetup(self):
        self.closeWindows()
        self.activeWindow = 9
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Fault Log Setup Screen Opened")

        # Configure Tag Overview Viewing Frame
        self.frame_faultLogSetup = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_faultLogSetup.place(x=self.framePosX,y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_faultLogSetup, text="Fault Log Setup",font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

    def open_eventLog(self):
        self.closeWindows()
        self.activeWindow = 98
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Event Log Screen Opened")

        # Update Imported Tag List
        self.updateEventLog()

        # Configure Tag Overview Viewing Frame
        self.frame_eventLog = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_eventLog.place(x=self.framePosX, y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_eventLog, text="Event Log", font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        # Need To Grab Table Name --> Column Names --> Data

        # Setup Scrollable Frame Window
        self.tree_frameEventLog = customtkinter.CTkFrame(master=self.frame_eventLog, border_color="#EB8613", border_width=2)
        self.tree_frameEventLog.place(x=self.frameSizeW/2, y=40, anchor='n', height=950, width=1404)

        tree_scrollY = customtkinter.CTkScrollbar(self.tree_frameEventLog, width=15)
        tree_scrollY.pack(side='right', fill='y', padx=4, pady=2)

        # Setup Tree View
        self.my_treeEventLog = ttk.Treeview(master=self.tree_frameEventLog, height=45, yscrollcommand=tree_scrollY.set)

        # Configure the scrollbar
        tree_scrollY.configure(command=self.my_treeEventLog.yview)

        # Need to get the column list to populate columns correctly. This column list drives the table creation

        # Define Our Columns
        self.my_treeEventLog['columns'] = ("Time", "Level", "Event")

        # Format Our Columns / Create Headings
        self.my_treeEventLog.column("#0", width=0, minwidth=0, stretch='NO')
        self.my_treeEventLog.heading("#0", text="", anchor='w')
        for column in self.my_treeEventLog['columns']:
            if column == "Event":
                self.my_treeEventLog.column(column, anchor='w', width=1100, minwidth=25)
            elif column == "Level":
                self.my_treeEventLog.column(column, anchor='w', width=50, minwidth=25)
            else:
                self.my_treeEventLog.column(column, anchor='w', width=200, minwidth=25)
            self.my_treeEventLog.heading(column, text=column, anchor='w')

        # Pack The Tree Widget
        self.my_treeEventLog.pack(padx=(8,0), pady=(8,2))

        # Treeview Data
        data = self.eventLog

        # Configure Treeview Colour Scheme
        self.my_treeEventLog.tag_configure('oddrow', background="lightgray", foreground='#1F538D')
        self.my_treeEventLog.tag_configure('evenrow', background="#1F538D", foreground='white')
        self.my_treeEventLog.tag_configure('oddrowRed', background="lightgray", foreground='red')
        self.my_treeEventLog.tag_configure('evenrowRed', background="#1F538D", foreground='red')
        self.my_treeEventLog.tag_configure('oddrowOrange', background="lightgray", foreground='orange')
        self.my_treeEventLog.tag_configure('evenrowOrange', background="#1F538D", foreground='orange')

        # Insert Data Into Treeview with For Loop
        count = 0
        for record in data:
            # Alternating Line Colour Plus Text Based On Event Level Record[1] = Event #
            if record[1] == 1:
                if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('evenrowRed',))
                else:
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('oddrowRed',))
                count += 1
            elif record[1] == 2:
                if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('evenrowOrange',))
                else:
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('oddrowOrange',))
                count += 1
            else:
                if count % 2 == 0:  # If we divide count by 2 and the remainder is 0 (even Row)
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('evenrow',))
                else:
                    self.my_treeEventLog.insert(parent='', index='end', iid=count, text="", values=record,tags=('oddrow',))
                count += 1

    def open_help(self):
        self.closeWindows()
        self.activeWindow = 99
        self.setMainMenuColors()
        self.connection.eventLogInsert(datetime.now(), 3, "Help Screen Opened")

        # Configure Tag Overview Viewing Frame
        self.frame_help = customtkinter.CTkFrame(master=self.master, width=self.frameSizeW, height=self.frameSizeH, corner_radius=0, fg_color="transparent")
        self.frame_help.place(x=self.framePosX,y=self.framePosY)

        # Tag Import Viewing Frame --> Title
        title = customtkinter.CTkLabel(master=self.frame_help, text="Help",font=customtkinter.CTkFont(size=20, weight="bold"))
        title.place(x=self.frameSizeW/2,y=20, anchor='center')

        textbox = customtkinter.CTkTextbox(master=self.frame_help, corner_radius=5, width=self.frameSizeW-40, height=955, font=customtkinter.CTkFont(size=16))
        textbox.place(x=self.frameSizeW/2,y=40, anchor='n')
        textbox.insert("0.0",
    f'''
PLC Tag Name: Name of tag in the PLC
Log Value: Save Values For This Tag (Yes/No)
Trigger Tag: When want to snapshot this tag data
Database Key: This is the part number/Barcode

If the log value is "Yes" the machine will store the data from PLC Tag Name when Trigger Tag is activated under the part number/barcode of Database Key.

Multiple Items can be saved under 1 database key.

If database key is set to "Time" the machine will save the data based on time. This is for machines that don't have a barcode. When using "Time" as the key all tags will need to have the same "Trigger Tag" or they will save as seperate parts.

The Database Key "Trigger Tag" must be the first trigger tag.

The Barcode in the "Database Key" needs to have the barcode in it through the process of all "Trigger Tags"

"Log Value" must be set to "Yes" to make the tag selectable as a Database Key

Omron tags must be global and set to "Publish"

{self.versionLong}
Programming By: Kevin Lay''')
        textbox.configure(state="disabled")

    def closeWindows(self):
        # Try To Close Omron Connection If Its Open
        try:
            self.omronConnection.close()
            self.connection.eventLogInsert(datetime.now(), 3, "Omron PLC Connection Closed")
        except AttributeError:
            pass
        # Close All Frames Before Opening New Frame
        try:
            self.frame_main.destroy()
        except AttributeError:
            pass
        try:
            self.frame_tagOverview.destroy()
        except AttributeError:
            pass
        try:
            self.frame_faultlog.destroy()
        except AttributeError:
            pass
        try:
            self.frame_tagSetup.destroy()
        except AttributeError:
            pass
        try:
            self.frame_tagImport.destroy()
        except AttributeError:
            pass
        try:
            self.frame_openConfiguration.destroy()
        except AttributeError:
            pass
        try:
            self.frame_bypassSetup.destroy()
        except AttributeError:
            pass
        try:
            self.frame_faultLogSetup.destroy()
        except AttributeError:
            pass
        try:
            self.frame_eventLog.destroy()
        except AttributeError:
            pass
        try:
            self.frame_help.destroy()
        except AttributeError:
            pass

    def processIncoming(self):
        while self.queue.qsize():
            try:
                msg = self.queue.get()
                self.queue.task_done()
                self.label1variable.set(str(msg["thread1"]))
                self.label2variable.set(str(msg["thread2"]))
                self.label3variable.set(str(msg["thread3"]))
                if msg == 'stop':
                    print('stopping')
                    self.close()
            except :#Queue.Empty:
                pass

    # Button Definitions

    def button_saveConfig(self):
        # Get Current Settings From Selections On Config Tab
        plcTypeString = self.comboBoxPLCType.get()
        plcType = self.plcTypeStringToInt(plcTypeString)
        ipAddress = self.entryPLCipAddress.get()

        # Save Settings From Configuration tab
        self.connection.configurationSave(plcType, ipAddress)
        print("Configuration Saved Successfully")

    def button_tagTest_CMD(self):
        # Allow the modification of the text box
        self.tagImport_textBox.configure(state='normal')
        self.tagImport_textBox.delete("1.0", 'end')

        # Grab The Required Data From The Database
        user, userName, plcType, ipAddress = self.connection.configurationRead()[0]
        plcTag = str(self.entry_tagImport_plcTagName.get())

        if plcType == 0: #AB
            try:
                # Read Tag Information
                result = abPLC.plcreadsingle(ipAddress, plcTag)
                # Set Pass / Fail Indicator
                if result.error == None:
                    self.button_tagTest.configure(fg_color="green")
                    self.label_tagTest.configure(text="Sucessful Test", text_color="green")
                    # Set Read Result Value
                    self.tagImport_textBox.insert("0.0", result.type)
                    return True
                else:
                    self.button_tagTest.configure(fg_color="red")
                    self.label_tagTest.configure(text="Failed Test", text_color="red")
                    self.tagImport_textBox.insert("0.0", "ERROR")
                    return False
            except:
                self.button_tagTest.configure(fg_color="red")
                self.label_tagTest.configure(text="Failed Test", text_color="red")
                self.tagImport_textBox.insert("0.0", "ERROR")
                return False


        if plcType == 1: #Omron NX
            # Need to determine if the tag selected is a structure
            # if so then read the structure in and get the individual result
            if "." in plcTag:
                # Strip the . and put it into a double dict
                structureTag, baseTag = plcTag.split(".", 1)

                # Read in the result for the tag structure
                result = self.omronConnection.plcreadsingle(structureTag)
                value = result[structureTag][baseTag]

                # Set Data Type
                datatype = self.datatypeConvertForDisplay(value)
                self.comboBox_tagImport_plcDataType.set(datatype)

                # Set Pass / Fail Indicator And Read Value
                self.tagImport_textBox.insert("0.0", value)
                self.button_tagTest.configure(fg_color="green")
                self.label_tagTest.configure(text="Sucessful Test", text_color="green")


            else:
                try:
                    # Read The Tag Result
                    result = self.omronConnection.plcreadsingle(plcTag)
                    print(f"Need This Format: {result}")

                    # Set Read Result Value After Determining If It is a structure. If it is a structure it will be a
                    # dict inside a dict
                    if type(result[plcTag]) == dict:
                        # Structure Of Tags
                        self.tagImport_textBox.insert("0.0", "udtStructure Detected")
                        self.connection.eventLogInsert(datetime.now(), 3, f"Omron Test Tag Result Sucessful: {plcTag} Structure")
                        # Set the datatype combo box to the current datatype read
                        self.comboBox_tagImport_plcDataType.set("STRUCTURE")
                    else:
                        # Individual Tag
                        self.tagImport_textBox.insert("0.0", result.get(plcTag))
                        self.connection.eventLogInsert(datetime.now(), 3, f"Omron Test Tag Result Sucessful: {result}")
                        # Set the datatype combo box to the current datatype read
                        datatype = self.datatypeConvertForDisplay(result[plcTag])
                        self.comboBox_tagImport_plcDataType.set(datatype)
                    # Set Pass / Fail Indicator
                    self.button_tagTest.configure(fg_color="green")
                    self.label_tagTest.configure(text="Sucessful Test", text_color="green")

                except Exception as e:
                    tb = traceback.format_exc()
                    self.tagImport_textBox.insert("0.0", "Error")
                    self.button_tagTest.configure(fg_color="red")
                    self.label_tagTest.configure(text="Failed Test", text_color="red")
                    print(tb)
                    self.connection.eventLogInsert(datetime.now(), 2, f"Omron Test Tag Result Failed: {plcTag} Error: {e}")
                    return False
                return True, result

        # Lock the Text Box
        self.tagImport_textBox.configure(state='disabled')

    def button_tagAdd_CMD(self):
        plcTagName = self.entry_tagImport_plcTagName.get()
        datatype = self.comboBox_tagImport_plcDataType.get()

        if datatype != "STRUCTURE":
        # Take the Present PLC Tag information and save it into the database if properly filled out
        # and the test function passesTes
            if self.button_tagTest_CMD()[0] == True:
                # Run the test it function to make sure it is a good tag in the PLC
                # Add Here the check to make sure it doesn't exist already PLC Tag Name & Saved Name
                compareResult = self.connection.tagImportCheckMatch(plcTagName)
                if compareResult == False:
                    tagDatatype = self.comboBox_tagImport_plcDataType.get()
                    triggerTag = ""
                    databaseKey = ""
                    isFault = 0
                    isBypass = 0
                    self.connection.tagImportInsert(plcTagName, tagDatatype, 0, triggerTag, databaseKey, isFault, isBypass)
                    self.connection.eventLogInsert(datetime.now(), 3, f"Successfully Added {plcTagName, tagDatatype, 0, triggerTag, databaseKey, isFault, isBypass}")
                    self.open_tagImport()
                else:
                    self.connection.eventLogInsert(datetime.now(), 3, f"PLC Tag Already Exists In Database {plcTagName}")

        elif datatype == "STRUCTURE":
            tags = self.button_tagTest_CMD()[1]
            result = {}
            for key, value in tags[plcTagName].items():
                new_key = plcTagName + "." + key
                result[new_key] = value

            for key, value in result.items():
                plcTagName = key
                print(f"Key = {key}, Value = {value}")
                print(type(value))
                tagDatatype = self.datatypeConvertForDisplay(value)
                print(tagDatatype)
                triggerTag = ""
                databaseKey = ""
                isFault = 0
                isBypass = 0
                compareResult = self.connection.tagImportCheckMatch(plcTagName)

                if compareResult == False:
                    self.connection.tagImportInsert(plcTagName, tagDatatype, 0, triggerTag, databaseKey, isFault, isBypass)
                else:
                    self.connection.eventLogInsert(datetime.now(), 3, f"PLC Tag Already Exists In Database {plcTagName}")
            self.open_tagImport()


        else:
            self.connection.eventLogInsert(datetime.now(), 3, f"Unknown Error While Adding Tag {plcTagName}")

    def button_tagRemove_CMD(self):
        # Delete The DB Saved Tag Name From The database
        plcTagName = self.entry_tagImport_plcTagName.get()
        self.connection.deleteFromTagImport(plcTagName)
        self.open_tagImport()

    def button_deployDB(self):
        self.connection.deployUpdateDB()

    def button_tagSetup_saveIt(self):
        plcTagName = self.entry_tagSetup_plcTagName.get()
        logValue = self.comboBox_tagSetup_logValue.get()
        triggerTag = self.comboBox_tagSetup_triggerTag.get()
        databaseKey = self.comboBox_tagSetup_databaseKey.get()
        isFault = self.comboBox_tagSetup_isFault.get()
        isBypass = self.comboBox_tagSetup_isBypass.get()

        # Change Values From no/yes to 0/1
        logValue = self.YesNoToNum(logValue)
        isFault = self.YesNoToNum(isFault)
        isBypass = self.YesNoToNum(isBypass)

        self.connection.updateTagSetup(plcTagName, logValue, triggerTag, databaseKey, isFault, isBypass)

    def button_setEth0_IP(self):
        # Set Ip Address On Raspberry PI
        ip = self.entryEth0IP.get()
        try:
            ipaddress.ip_address(ip)
            print(f"Setting {ip}")
            getsetIP.setEth0(ip)
        except:
            print(f"Invalid IP Address: {ip}")

    def button_setWlan0_IP(self):
        # Set Ip Address On Raspberry PI
        ip = self.entryWLAN0IP.get()
        try:
            ipaddress.ip_address(ip)
            print(f"Setting {ip}")
            getsetIP.setWlan0(ip)
        except:
            print(f"Invalid IP Address: {ip}")

    # Other Functions

    def setMainMenuColors(self):
        if self.activeWindow == 2:
            self.button_mainMenu_main.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 3:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 4:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 5:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 6:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 7:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 8:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 9:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 98:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#EB8613', text_color='black', hover=False)
            self.button_mainMenu_help.configure(fg_color='#1F538D', text_color='white')
        if self.activeWindow == 99:
            self.button_mainMenu_main.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagOverview.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_tagImport.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_configuration.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_bypassSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_faultLogSetup.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_eventLog.configure(fg_color='#1F538D', text_color='white')
            self.button_mainMenu_help.configure(fg_color='#EB8613', text_color='black', hover=False)

    def updateIPAddresses(self):
        # Read Current Wlan & Ethernet IP
        eth0, wlan0 = getsetIP.getIPs()
        return eth0, wlan0

    def plcTypeIntToString(self, plctype):
        if plctype == 0:
            return "Allen Bradley"
        elif plctype == 1:
            return "Omron NX"
        elif plctype == 2:
            return "Siemens TIA"
        else:
            return "Unknown"

    def plcTypeStringToInt(self, plctype):
        if plctype == "Allen Bradley":
            return 0
        elif plctype == "Omron NX":
            return 1
        elif plctype == "Siemens TIA":
            return 2
        else:
            return 99

    def updateImportTagList(self):
        # Create Imported Tag List
        self.importedTagListFull = self.connection.tagImportReadAll()

        # Create Imported Tag List Names Only
        self.importedTagList = []
        for tag in self.importedTagListFull:
            self.importedTagList.append(tag[0])

    def updateEventLog(self):
        # Create Imported Tag List
        self.eventLog = self.connection.selectAllEventLog()

    def updateDatabaseList(self):
        self.tableList = []
        for table in self.connection.tableList():
            self.tableList.append(table)

    def tagSetupFillData(self, e):
        # Grab Record Number
        selected = int(self.my_treeTagSetup.selection()[0])
        # Grab Record Values
        tagName = self.my_treeTagSetup.item(selected, "values")[0]
        # Read Records From Database
        plcTagName, tagDatatype, logValue, triggerTag, databaseKey, isFault, isBypass = self.connection.tagImportReadByTagName(tagName)[0]

        # Change Log Value From 0/1 to No/Yes
        logValue = self.NumtoYesNo(logValue)
        isFault = self.NumtoYesNo(isFault)
        isBypass = self.NumtoYesNo(isBypass)

        # Clear Entry Box and Populate Data
        self.entry_tagSetup_plcTagName.configure(state='normal')
        self.entry_tagSetup_plcTagName.delete(0, 'end')
        self.entry_tagSetup_plcTagName.insert(0, plcTagName)
        self.comboBox_tagSetup_logValue.set(logValue)
        self.comboBox_tagSetup_triggerTag.set(triggerTag)
        self.comboBox_tagSetup_databaseKey.set(databaseKey)
        self.comboBox_tagSetup_isFault.set(isFault)
        self.comboBox_tagSetup_isBypass.set(isBypass)
        self.entry_tagSetup_plcTagName.configure(state='disabled')

    def tagImportFillData(self, e):
        # Grab Record Number
        selected = int(self.my_treeTagImport.selection()[0])
        # Grab Record Values
        tagName = self.my_treeTagImport.item(selected, "values")[0]
        # Read Records From Database
        plcTagName, tagDatatype, logValue, triggerTag, databaseKey, isFault, isBypass = self.connection.tagImportReadByTagName(tagName)[0]

        # Clear Entry Box and Populate Data
        self.entry_tagImport_plcTagName.delete(0, 'end')
        self.entry_tagImport_plcTagName.insert(0, plcTagName)
        self.comboBox_tagImport_plcDataType.set(tagDatatype)

    def NumtoYesNo(self,input):
        if input == 1:
            return 'YES'
        else:
            return 'NO'

    def YesNoToNum(self,input):
        if input == 'YES':
            return 1
        else:
            return 0

    def datatypeConvertForDisplay(self, input):
        if type(input) == bool:
            return "BOOL"
        if type(input) == str:
            return "STRING"
        if type(input) == float:
            return "FLOAT"
        if type(input) == int:
            return "INT"
        if type(input) == bytes:
            return "BYTES"
        if isinstance(input, aphyt.cip.cip_datatypes.CIPBoolean):
            return "BOOL"
        if isinstance(input, aphyt.cip.cip_datatypes.CIPByte) or isinstance(input, aphyt.cip.cip_datatypes.CIPWord) or isinstance(input, aphyt.cip.cip_datatypes.CIPDoubleWord) or isinstance(input, aphyt.cip.cip_datatypes.CIPLongWord):
            return "BYTES"
        if isinstance(input, aphyt.cip.cip_datatypes.CIPDoubleInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPUnsignedShortInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPUnsignedLongInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPUnsignedInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPUnsignedDoubleInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPLongInteger) or isinstance(input, aphyt.cip.cip_datatypes.CIPShortInteger):
            return "INT"
        if isinstance(input, aphyt.cip.cip_datatypes.CIPLongReal) or isinstance(input, aphyt.cip.cip_datatypes.CIPReal):
            return "FLOAT"
        if isinstance(input, aphyt.cip.cip_datatypes.CIPString):
            return "STRING"




    def close(self):
        self.closeWindows()
        self.master.quit()


class ThreadedClient:
    def __init__(self, master, qdic_):
        self.master = master
        self.qdic = qdic_
        self.threadlist = []

        self.queue = queue.Queue()

        self.gui = GuiPart(master, self.queue, self.endApplication)

        qdic_["running"] = 1

        self.thread1 = threading.Thread(target=self.workerThread1, args=(self.qdic, "thread1"))
        self.threadlist.append(self.thread1)
        self.thread1.start()

        self.thread2 = threading.Thread(target=self.workerThread2, args=(self.qdic, "thread2", 0.05))
        self.threadlist.append(self.thread2)
        self.thread2.start()

        self.thread3 = threading.Thread(target=self.workerThread2, args=(self.qdic, "thread3", 2.3))
        self.threadlist.append(self.thread3)
        self.thread3.start()

        self.periodicCall()

    def periodicCall(self):
        self.gui.processIncoming()
        if not self.qdic["running"]:
            for threads in self.threadlist:
                threads.join()
            self.gui.close()
        self.master.after(16, self.periodicCall)

    def workerThread1(self, qdic_, dicname):
        i = 0
        while qdic_["running"]:
            i += 2
            qdic_[dicname] = i
            self.queue.put(qdic_)
            time.sleep(0.1)  # you must always have a wait, or you will crush your processor

    def workerThread2(self, qdic_, dicname, wait):
        i = 0
        while qdic_["running"]:
            i += 1
            time.sleep(wait)
            qdic_[dicname] = i
            self.queue.put(qdic_)

    def endApplication(self):
        self.qdic["running"] = 0


if __name__ == '__main__':

    try:
        qdic = {"running": 1, "thread1": 0, "thread2": 0, "thread3": 0}
        # root = tkinter.Tk()
        root = customtkinter.CTk()
        client = ThreadedClient(root, qdic)
        root.mainloop()
    except:
        print(traceback.format_exc())
        exit()
    finally:
        root.quit()
        print('Printing this is the last line of code')
