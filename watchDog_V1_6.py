'''
GVS AI watchDog_V1_1
This program watches for the trigger tags in the PLC and
grabs the data and inserts it into the table on a low to high transition

Version Log:
V1_0 Init
V1_1 Updated For New UI Threading Every Single Tag
V1_2 Testing
V1_3 Testing
V1_4 NSeriesThreadDispatcher Added
Author: Kevin Lay
'''

from dataLogger_V1_4 import gvsDB
import nxOmronPLC_V1_5 as nxOmronPLC
import time
import threading
from threading import Event
from datetime import datetime
import traceback

class watchDog():
    def __init__(self):
        # Create The Event To Terminate The Threads On Software Exit
        self.event = Event()

        # Create Thread Lists
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

        # Create Connection Monitoring Objects
        self.omronConnectionEstablished = False

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
            self.omronConnectionEstablished = True

        # Looping a read command inside the thread to keep the connection active always
        while not event.is_set():
            for i in range(30):
                time.sleep(1)
                if event.is_set():
                    break
            result = self.omronConnection.plcreadsingle("testBOOL")
            print("PLC Heartbeat OK")

    # Trying to figuree out how to generate a thread for every tag
    def checkTagStatus(self, tag, tagType):
        prev_value = None
        while not self.event.is_set():
            # Omron
            if self.plcType == 1:
                try:
                    result, value = self.getTagValue(tag)

                    if tagType == "bypass" or tagType == "fault":
                        self.logCheckAndInsert(tag, tagType, value, prev_value)
                        # Update the previous value
                        prev_value = value

                except Exception as e:
                    tb = traceback.format_exc()
                    print(tb)

            time.sleep(0.1)

    def logTagControl(self, tag):
        prev_value = None
        # Need To Remember The Value To Update Data
        self.databaseKeyValue = None
        while not self.event.is_set():
            # Omron
            if self.plcType == 1:
                try:
                    result, value = self.getTagValue(tag)
                    # print(result, value)
                    if prev_value is not None and prev_value == False and value == True:
                        print(f"{tag} transitioned from False to True")


                        # Make a dict of tags that have the triggerTag that transitioned
                        tagsWithTriggerTag = self.connection.tagImportReadSelect(tag)
                        # The dict also needs to contain the database key
                        tagDict = {}
                        # Loop through and populate the dict with the tag name, database key, & current value
                        for tagForProcessing in tagsWithTriggerTag:
                            # print(tagForProcessing)
                            # Check That the tag is set to log
                            if tagForProcessing[2] == 1:
                                NOP, tagStatus = self.getTagValue(tagForProcessing[0])
                                tagDict[tagForProcessing[0]] = (tagForProcessing[4], tagStatus)

                        # update the main database using the key and the value
                        for tagItem, (databaseKey, state) in tagDict.items():
                            table = (f"{databaseKey}_data")
                            tagName = tagItem
                            tagValue = state

                            # Insert New Row Into Database If The Database Key Is In The List
                            if databaseKey == tagName:
                                self.databaseKeyValue = tagValue
                                self.connection.insertIntoData(table, tagName, tagValue)

                        # Do the same itteration again but this time to update the data now that the row exists
                        for tagItem, (databaseKey, state) in tagDict.items():
                            table = (f"{databaseKey}_data")
                            tagName = tagItem
                            tagValue = state
                            self.connection.updateData(table, tagName, databaseKey, self.databaseKeyValue, tagValue)

                    # Update the previous value
                    prev_value = value

                except Exception as e:
                    tb = traceback.format_exc()
                    print(tb)

            time.sleep(0.1)

    def getTagValue(self, tag):
        try:
            # Need to determine if the tag selected is a structure
            # if so then read the structure in and get the individual result
            if "." in tag:
                # Strip the . and put it into a double dict
                structureTag, baseTag = tag.split(".", 1)

                # Read in the result for the tag structure
                result = self.omronConnection.plcreadsingle(structureTag)
                tagvalue = result[structureTag][baseTag]
                return result, tagvalue

            else:
                result = self.omronConnection.plcreadsingle(tag)
                value = result.get(tag, False)
                return result, value


        except Exception as e:
            tb = traceback.format_exc()
            print(tb)
            return None, None


    def logCheckAndInsert(self, tag, tagType, value, prev_value):
        # Check if the new value is True and the previous value is False
        if prev_value is not None and prev_value == False and value == True:
            print(f"{tag} transitioned from False to True")
            if tagType == "bypass":
                self.connection.bypassLogInsert(datetime.now(), tag)
            elif tagType == 'fault':
                self.connection.faultLogInsert(datetime.now(), tag)

    def threadingTagCheckFaultList(self, taglist):
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag, "fault"))
            print(f"Thread Started For Fault Monitoring: {tag}")
            self.faultThreads.append(t)
            t.start()

    def threadingTagCheckBypassList(self, taglist):
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag, "bypass"))
            print(f"Thread Started For Bypass Monitoring: {tag}")
            self.bypassThreads.append(t)
            t.start()

    def threadingTagCheckTriggerList(self, taglist):
        for tag in taglist:
            t = threading.Thread(target=self.logTagControl, args=(tag,))
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
    # Create a list of tags for monitoring bypasses
    tagList = watchDog.getImportedTags()
    faultList = []
    bypassList = []
    triggerList = []
    # Iterate through tag list to create a list that contains only bypasses & faults
    for tag in tagList:
        plcTagName, tagDatatype, logValue, triggerTag, databaseKey, isFault, isBypass = tag
        if isFault == True:
            faultList.append(plcTagName)
        elif isBypass == True:
            bypassList.append(plcTagName)
        elif logValue == True and triggerTag:
            # Make sure Trigger Tag Is Not Empty So We Don't Try To Log To Nothing
            # The goal is to make a list of trigger tags, these are what we need to capture
            # Cycle through each tag with a log value and add the trigger tag to the list
            # if it doesnt exist in the list already
            if not triggerTag in triggerList:
                triggerList.append(triggerTag)

    print(f"isFault:{faultList}")
    print(f"isBypass:{bypassList}")
    print(f"logList:{triggerList}")

    if watchDog.plcType == 1:
        while watchDog.omronConnectionEstablished == False:
            time.sleep(0.1)

    watchDog.threadingTagCheckFaultList(faultList)
    watchDog.threadingTagCheckBypassList(bypassList)
    watchDog.threadingTagCheckTriggerList(triggerList)

    time.sleep(120)
    watchDog.close()




