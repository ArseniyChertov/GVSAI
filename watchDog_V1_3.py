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
import nxOmronPLC_V1_3 as nxOmronPLC
import time
import threading
from threading import Event
from datetime import datetime
import traceback

class watchDog():
    def __init__(self):
        # Create The Event To Terminate The Threads On Software Exit
        self.event = Event()

        # Init Thread Lists
        self.faultThreads = []
        self.bypassThreads = []
        self.logThreads = []

        # Create Current Connection To Database
        self.connection = gvsDB("gvsAI")

        # Read In Database Config To Get PLC Type
        self.user, self.username, self.plcType, self.ipAddress = self.connection.configurationRead()[0]

        # Create mySQL Read in a thread.
        self.thread1 = threading.Thread(target=self.databaseAlive, args=(self.event,))
        self.thread1.start()

        if self.plcType == 1: # 1 = Omron Connection
            self.omronConnection = nxOmronPLC.omronConnection(self.ipAddress)
            self.omronConnection2 = nxOmronPLC.omronConnection(self.ipAddress)
            self.omronConnection3 = nxOmronPLC.omronConnection(self.ipAddress)


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

    # Trying to figuree out how to generate a thread for every tag
    def checkTagStatusList(self, taglist, connection):
        while not self.event.is_set():
            # Omron
            if self.plcType == 1:
                for tag in taglist:
                    try:
                        print(f"{tag} Result: {connection.plcreadsingle(tag)}")
                    except Exception as e:
                        tb = traceback.format_exc()
                        print(tb)
            time.sleep(0.001)

    def threadingTagCheckFaultList(self, taglist):
        t = threading.Thread(target=self.checkTagStatusList, args=(taglist, self.omronConnection))
        print(f"Thread Started For Fault Monitoring: {taglist}")
        self.faultThreads.append(t)
        t.start()

    def threadingTagCheckBypassList(self, taglist):
        t = threading.Thread(target=self.checkTagStatusList, args=(taglist, self.omronConnection))
        print(f"Thread Started For Bypass Monitoring: {taglist}")
        self.bypassThreads.append(t)
        t.start()

    def threadingTagCheckLogList(self, taglist):
        t = threading.Thread(target=self.checkTagStatusList, args=(taglist, self.omronConnection2))
        print(f"Thread Started For Log Monitoring: {taglist}")
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

    time.sleep(20)
    watchDog.close()




