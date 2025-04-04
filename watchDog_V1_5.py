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
V1_5 Adding Fault Log and Bypass log --A.A
Author: Kevin Lay
'''

from dataLogger_V1_2 import gvsDB
from collections import deque
import abPLC_V1_0 as abPLC
import nxOmronPLC_V1_5 as nxOmronPLC
import time
import threading
from threading import Event
from datetime import datetime
import traceback

 

'''
    Tag_state_t : Object discovers Low to High Tag state transitions, and Push Transitions as events to database
    Methods     :
                check_transitions(), LogEvent
    Attributes  :
                current_state, previous_state, transition, event, queue, queue_item
'''
class tag_state_t:
    def __init__(self):
        self.current_state  = False          #Holds current state of tag
        self.previous_state = True           #Holds previous state of tag (Initialized to False to prevent false event triggering)
        

    '''
        @_check_transition function: Compare's previous ans current tag state, returns True when tarnsition occurs
        @Param : N/A
        @return : Bool
    '''
    def check_transition(self):
        #check for Low to High transition
        if not self.previous_state and self.current_state :
            self.previous_state = self.current_state
            return True
        #Update tag state every cycle
        self.previous_state = self.current_state
        return False


        
        

class watchDog():
    def __init__(self):
        # Create The Event To Terminate The Threads On Software Exit
        self.event = Event()

        # Create Thread Lists
        self.faultThreads = []
        self.bypassThreads = []
        self.logThreads = []

        #Transition variables initalization
        self.current_state  = False          #Holds current state of tag
        self.previous_state = True 

        # Create Current Connection To Database
        self.connection = gvsDB("gvsAI")

        # Read In Database Config To Get PLC Type
        self.user, self.username, self.plcType, self.ipAddress = self.connection.configurationRead()[0]

        # Create mySQL Read in a thread.
        self.thread1 = threading.Thread(target=self.databaseAlive, args=(self.event,))
        self.thread1.start()

        # Create Connection Monitoring Objects
        self.omronConnectionEstablished = False
        
        #Create variables to store keywords to identify tags
        self.Fault_id   =     "Fault"
        self.Bypass_id  =    "Bypass"

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
                #self.connection.deployUpdateDB()
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

    #Checks through tag values and return actual state of tag
    def checkFault_n_BypassValue(self, value, tag):
        #convert tag to string
        str_value = str(value)
        #search for tag i string
        is_found_fault = str_value.find(tag)
        

        #check for Boolean Value of tags
        if is_found_fault != -1 :
            is_found_fault = str_value.find("True")
            is_false = str_value.find("False")

            #return 1 when Tag value is true, Return 2 when value is false, Return 0 if neither True or False
            if is_found_fault > -1:
                return 1
            elif is_false > -1:
                return 2
            else:
                return 0

        return 0
    
    def _check_transition(self):
        #check for Low to High transition
        if not self.previous_state and self.current_state :
            self.previous_state = self.current_state
            return True
        #Update tag state every cycle
        self.previous_state = self.current_state
        return False

    # Trying to figuree out how to generate a thread for every tag
    def checkTagStatus(self, tag, type_id):
        tag_state = tag_state_t()
    
        while not self.event.is_set():
            # Omron
            if self.plcType == 1:
                try:
                    # Need to determine if the tag selected is a structure
                    # if so then read the structure in and get the individual result
                    if "." in tag:
                        # Strip the . and put it into a double dict
                        structureTag, baseTag = tag.split(".", 1)

                        # Read in the result for the tag structure
                        result = self.omronConnection.plcreadsingle(structureTag)
                        value = result[structureTag][baseTag]

                        
                        #If Need ever arises to monitior tags of structures, just uncomment the program below
                        '''if self.checkActualTagValue(value, tag) == 1:
                            self.current_state = True
                        
                        elif self.checkActualTagValue(value, tag) == 2:
                            self.state = False'''
                    else:
                        #Check Tag state and Return state as a boolean to the Tag_state object
                        if self.checkFault_n_BypassValue(self.omronConnection.plcreadsingle(tag), tag) == 1:
                            tag_state.current_state = True
                            
                        elif self.checkFault_n_BypassValue(self.omronConnection.plcreadsingle(tag), tag) == 2:
                            tag_state.current_state = False
                            
                    #Push tag state as a log to database when transition occurs
                    if tag_state.check_transition() :
                        
                        #check if tag is fault or by pass 
                        if type_id == self.Fault_id:
                            self.connection.faultLogInsert(datetime.now(), tag)
                        elif type_id == self.Bypass_id:
                            self.connection.bypassLogInsert(datetime.now(), tag)

                        print(f"{tag} transitioned")
                        

                except Exception as e:
                    tb = traceback.format_exc()
                    print(tb)

            time.sleep(0.1)

        

    def threadingTagCheckFaultList(self, taglist, type_id):
        self.faultTagList = taglist
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag, type_id))
            print(f"Thread Started For Fault Monitoring: {tag}")
            self.faultThreads.append(t)
            t.start()

    def threadingTagCheckBypassList(self, taglist, type_id):
        self.bypassTagList = tagList
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag, type_id))
            print(f"Thread Started For Bypass Monitoring: {tag}")
            self.bypassThreads.append(t)
            t.start()

    def threadingTagCheckLogList(self, taglist):
        for tag in taglist:
            t = threading.Thread(target=self.checkTagStatus, args=(tag, "Log"))
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

    if watchDog.plcType == 1:
        while watchDog.omronConnectionEstablished == False:
            time.sleep(0.1)
    time.sleep(5)
    watchDog.threadingTagCheckFaultList(faultList, "Fault")
    watchDog.threadingTagCheckBypassList(bypassList, "Bypass")
    watchDog.threadingTagCheckLogList(logList)

    time.sleep(61)
    watchDog.close()




