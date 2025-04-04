'''
GVS AI watchDog_V1_0
This program watches for the trigger tags in the PLC and
grabs the data and inserts it into the table on a low to high transition

Version Log:
V1_0 Init
Author: Kevin Lay
'''

from dataLogger_V1_0 import gvsDB
import abPLC_V1_0 as abPLC
import nxOmronPLC_V1_0 as nxPLC
from time import sleep

# Create Database Connection
connection = gvsDB("gvsDataLogger")

# Read In Database Config To Get PLC Type
plcType = plcType = connection.configurationRead()[0][2]
ipAddress = connection.configurationRead()[0][3]

tagDebounce = []
while True:
    # Step 1 grab a list of trigger tags to look for in the PLC.
    importedTagList = connection.selectAll()

    taglist = []
    tagvalues = []
    tagnames = []
    databaseKeys = []
    databasekeyVals = []

    # Step 1 grab a list of trigger tags to look for in the PLC. 
    for tag in importedTagList:
        if tag[3]:  # Check For Empty
            if tag[3] not in taglist:
                taglist.append(tag[3])

    if plcType == 0:  # AB PLC
        # Step 2 For each trigger tag check the PLC tags to see if one is True 
        ipAddress = connection.configurationRead()[0][3]
        for tag in taglist:
            plcTag = (tag)
            result = abPLC.plcreadsingle(ipAddress, plcTag)
            if result.error == None:
                if result.value == True:
                    if result.tag not in tagDebounce:  # Check To Make sure the Tag Isn't In The Memory Of Written Tags Already
                        tagDebounce.append(result.tag)  # Add the tag to the memory of written tags
                        tagsToGrabData = connection.tagImportReadSelect(tag)
                        # Step 3 Create a list of tags that have that each trigger tag seperated by database key
                        for tagdata in tagsToGrabData:
                            if tagdata[2] == 1:  # Make sure log data is enabled
                                tagval = abPLC.plcreadsingle(ipAddress, tagdata[0])
                                tagnames.append(tagdata[0])
                                databaseKeys.append(tagdata[4])
                                tagvalues.append(
                                    tagval.value)  # Need to create a new list that contains the barcode that the data belongs with
                                tempBarcode = abPLC.plcreadsingle(ipAddress, tagdata[4])
                                databasekeyVals.append(tempBarcode.value)

                        for tagname, tagvalue, databasekey in zip(tagnames, tagvalues, databaseKeys):
                            # Run Through Once First And Check For databasekey == tagname. Then run an insert command To insert the line
                            # into the database with the database key data filled out
                            # Then run update commands on the remaining data. 
                            table = (f"{databasekey}_data")
                            if tagname == databasekey:
                                print(f"Inserting:{tagname, tagvalue, databasekey}")
                                connection.insertIntoData(table, tagname, tagvalue)

                        for tagname, tagvalue, databasekey, databasekeyVal in zip(tagnames, tagvalues, databaseKeys,
                                                                                  databasekeyVals):
                            # Run Through a second time updating the outstanding data
                            table = (f"{databasekey}_data")
                            if tagname != databasekey:
                                print(f"Updating:{tagname, tagvalue, databasekey, databasekeyVal}")
                                connection.updateData(table, tagname, databasekey, databasekeyVal, tagvalue)

                if result.value == False:  # If the tag is off we can remove it from the memory of written tags
                    if result.tag in tagDebounce:
                        tagDebounce.remove(result.tag)

            else:
                print(result.error)

    if plcType == 1:  # Omron NX PLC
        omronConnection = nxPLC.connect(ipAddress)
        for tag in taglist:
            plcTag = (tag)
            result = nxPLC.plcreadsingle(plcTag, omronConnection)

            if result == True:
                if tag not in tagDebounce:  # Check To Make sure the Tag Isn't In The Memory Of Written Tags Already
                    tagDebounce.append(plcTag)  # Add the tag to the memory of written tags
                    tagsToGrabData = connection.tagImportReadSelect(plcTag)
                    # Step 3 Create a list of tags that have that each trigger tag seperated by database key
                    for tagdata in tagsToGrabData:
                        if tagdata[2] == 1:  # Make sure log data is enabled
                            tagval = nxPLC.plcreadsingle(tagdata[0], omronConnection)
                            tagnames.append(tagdata[0])
                            databaseKeys.append(tagdata[4])
                            tagvalues.append(
                                tagval)  # Need to create a new list that contains the barcode that the data belongs with
                            tempBarcode = nxPLC.plcreadsingle(tagdata[4], omronConnection)
                            databasekeyVals.append(tempBarcode)

                    for tagname, tagvalue, databasekey in zip(tagnames, tagvalues, databaseKeys):
                        # Run Through Once First And Check For databasekey == tagname. Then run an insert command To insert the line
                        # into the database with the database key data filled out
                        # Then run update commands on the remaining data. 
                        table = (f"{databasekey}_data")
                        if tagname == databasekey:
                            print(f"Inserting:{tagname, tagvalue, databasekey}")
                            connection.insertIntoData(table, tagname, tagvalue)

                    for tagname, tagvalue, databasekey, databasekeyVal in zip(tagnames, tagvalues, databaseKeys,
                                                                              databasekeyVals):
                        # Run Through a second time updating the outstanding data
                        table = (f"{databasekey}_data")
                        if tagname != databasekey:
                            print(f"Updating:{tagname, tagvalue, databasekey, databasekeyVal}")
                            connection.updateData(table, tagname, databasekey, databasekeyVal, tagvalue)

            if result == False:  # If the tag is off we can remove it from the memory of written tags
                if plcTag in tagDebounce:
                    tagDebounce.remove(plcTag)
