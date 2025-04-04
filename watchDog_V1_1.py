'''
GVS AI watchDog_V1_1
This program watches for the trigger tags in the PLC and
grabs the data and inserts it into the table on a low to high transition

Version Log:
V1_0 Init
V1_1 Updated For New UI Threading Every Single Tag
Author: Kevin Lay
'''

from dataLogger_V1_2 import gvsDB
import abPLC_V1_0 as abPLC
import nxOmronPLC_V1_4 as nxOmronPLC
import time
import threading
from threading import Event
from datetime import datetime
import traceback

class watchDog():
    def __init__(self):
        # Create The Event To Terminate The Threads On Software Exit
        self.event = Event()

        # Create Current Connection To Database
        self.connection = gvsDB("gvsAI")

        # Read In Database Config To Get PLC Type
        self.user, self.username, self.plcType, self.ipAddress = self.connection.configurationRead()[0]

        # Create mySQL Read in a thread.
        self.thread1 = threading.Thread(target=self.databaseAlive, args=(self.event,))
        self.thread1.start()

        if self.plcType == 1: # 1 = Omron Connection
            # Create Omron Connection in a thread.
            self.thread2 = threading.Thread(target=self.omronConnection, args=(self.event,))
            self.thread2.start()

    def getImportedTags(self):
        return self.connection.tagImportReadAll()

    def databaseAlive(self, event):
        # Keep database working so we don't get the "MySQL server has gone away"
        while not event.is_set():
            for i in range(30):
                time.sleep(1)
                if event.is_set():
                    break
            try:
                self.connection.tableList()
                print("MySQL Heartbeat OK")
            except:
                # Create Current Connection To Database If it can't read successfully
                print("Recreating Database Connection")
                self.connection = gvsDB("gvsAI")
                self.connection.selectAllTable()

    def omronConnection(self, event):
        # Opening Database Connection
        print("Opening Omron Database Connection")
        if self.plcType == 1:
            self.omronConnection = nxOmronPLC.omronConnection(self.ipAddress)
            print("Database Connected")

        # Looping a read command inside the thread to keep the connection active always
        while not event.is_set():
            for i in range(30):
                time.sleep(1)
                if event.is_set():
                    break
            result = self.omronConnection.plcreadsingle("testBOOL")
            print("PLC Heartbeat OK")


    # Trying to figuree out how to generate a thread for every tag
    def checkTagStatus(self, tag):
        while not self.event.is_set():
            # Omron
            if self.plcType == 1:
                try:
                    print(f"{tag} Result: {self.omronConnection.plcreadsingle(tag)}")
                except Exception as e:
                    tb = traceback.format_exc()
                    print(tb)
            time.sleep(0.10)

    def threadingTagCheckFaultList(self, taglist):
        self.faultThreads = []
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag,))
            print(f"Thread Started For Fault Monitoring: {tag}")
            self.faultThreads.append(t)
            t.start()

    def threadingTagCheckBypassList(self, taglist):
        self.bypassThreads = []
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag,))
            print(f"Thread Started For Bypass Monitoring: {tag}")
            self.bypassThreads.append(t)
            t.start()

    def threadingTagCheckLogList(self, taglist):
        self.logThreads = []
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag,))
            print(f"Thread Started For Log Monitoring: {tag}")
            self.logThreads.append(t)
            t.start()

    def close(self):
        # Set Exit Event
        self.event.set()
        # Attempt To Clean Up Threads On Exit
        try:
            print("Cleaning Up Thread 1")
            self.thread1.join()
            print("Thread 1 Successfully Closed")
        except:
            print("Thread 1 Not Running")
        try:
            print("Cleaning Up Thread 2")
            self.thread2.join()
            print("Thread 2 Successfully Closed")
        except:
            print("Thread 2 Not Running")

        for item in self.faultThreads:
            item.join()
            print(f"{item} Thread Closed")

        for item in self.bypassThreads:
            item.join()
            print(f"{item} Thread Closed")

        for item in self.logThreads:
            item.join()
            print(f"{item} Thread Closed")



if __name__ == "__main__":
    watchDog = watchDog()
    time.sleep(20)
    # Create a list of tags for monitoring bypasses
    tagList = watchDog.getImportedTags()
    faultList = []
    bypassList = []
    logList = []
    # Iterate through tag list to create a list that contains only bypasses & faults
    for tag in tagList:
        plcTagName, tagDatatype, logValue, triggerTag, databaseKey, isFault, isBypass = tag
        if isFault == True:
            faultList.append(plcTagName)
        elif isBypass == True:
            bypassList.append(plcTagName)
        elif logValue == True:
            logList.append(plcTagName)

    print(f"isFault:{faultList}")
    print(f"isBypass:{bypassList}")
    print(f"logList:{logList}")

    watchDog.threadingTagCheckFaultList(faultList)
    watchDog.threadingTagCheckBypassList(bypassList)
    watchDog.threadingTagCheckLogList(logList)

    time.sleep(61)
    watchDog.close()




