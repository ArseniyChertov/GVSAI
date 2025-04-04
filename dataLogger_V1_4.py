'''
GVS AI Datalogger

This program logs all the data into the database based on the UI settings

Version Log:
Author: Kevin Lay
V1_0 Init
V1_1 Small Bug Fix, Added Event Log, Added String Cap of 255 for event log
V1_2 Added Fault Log
V1_3 Corrected bugs with deploying database
'''
import mariadb
import sys
from datetime import datetime


class gvsDB:
    def __init__(self, db):
        self.conn = mariadb.connect(
            user="1",
            password="100",
            host="localhost",
            port=3306,
            database=db
        )
        self.cur = self.conn.cursor()
        print("Sucessfully Connect To Database")

    def _grabDBDatatype(self, datatype):
        if datatype.lower() == "bool":
            return "BOOLEAN"
        if datatype.lower() == "string":
            return "VARCHAR(255)"
        if datatype.lower() == "float":
            return "FLOAT"
        if datatype.lower() == "int":
            return "INT"
        if datatype.lower() == "bytes":
            return "VARCHAR(255)"

    def configurationSave(self, plcType, ipAddress):
        user = 1
        username = "gvs"
        sql = ("""UPDATE configuration SET user = %s, username = %s, plcType = %s, ipAddress = %s WHERE user = %s""")
        data = (user, username, plcType, ipAddress, user)
        self.cur.execute(sql, data)
        self.conn.commit()

    def configurationInsert(self, plcType, ipAddress):
        user = 1
        username = "gvs"
        sql = ("""INSERT INTO configuration (user,username,plcType,ipAddress) VALUES (%s,%s,%s,%s)""")
        data = (user, username, plcType, ipAddress)
        self.cur.execute(sql, data)
        self.conn.commit()

    def configurationRead(self):
        user = 1
        username = "gvs"
        sql = ("""SELECT * FROM configuration WHERE user = %s""")
        data = (user,)
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def tagImportInsert(self, plcTagName, tagDataType, logValue, triggerTag, databaseKey, isFault, isBypass):
        sql = ("""INSERT INTO importedTags (plcTagName,tagDataType,logValue,triggerTag,databaseKey,isFault,isBypass) VALUES (%s,%s,%s,%s,%s,%s,%s)""")
        data = (plcTagName, tagDataType, logValue, triggerTag, databaseKey, isFault, isBypass)
        self.cur.execute(sql, data)
        self.conn.commit()

    def tagImportReadAll(self):
        sql = ("""SELECT * FROM importedTags""")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def tagImportReadByTagName(self, tagName):
        sql = ("""SELECT * FROM importedTags WHERE plcTagName = %s""")
        data = (tagName,)
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def tagImportCheckIfLogged(self, tagName):
        sql = ("""SELECT * FROM importedTags WHERE plcTagName = %s""")
        data = (tagName,)
        self.cur.execute(sql, data)
        result = self.cur.fetchall()

        if result[0][2] == 1:
            return True
        else:
            return False

    def tagImportReadSelect(self, triggertag):
        sql = ("""SELECT * FROM importedTags WHERE triggerTag = %s""")
        data = (triggertag,)
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def tagImportCheckMatch(self, plcTagName):
        # Read All Tags and check for a PLC Tag Name
        matchName = False
        sql = ("""SELECT * FROM importedTags""")
        data = ()
        self.cur.execute(sql, data)
        results = self.cur.fetchall()
        for result in results:
            tagname = result[0]
            if tagname == plcTagName:
                matchName = True
        return matchName

    def searchForTagName(self, tagName):
        # Search the database based on the saved tag name and return the line of data
        sql = ("""SELECT * FROM importedTags WHERE plcTagName = %s""")
        data = (tagName,)
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def deleteFromTagImport(self, plcTagName):
        sql = ("""DELETE FROM importedTags WHERE plcTagName = %s""")
        data = (plcTagName,)
        self.cur.execute(sql, data)
        self.conn.commit()

    def updateTagSetup(self, plcTagName, logValue, triggerTag, databaseKey, isFault, isBypass):
        # Update Tag Setup Values In Database
        sql = ("""UPDATE importedTags SET logValue = %s, triggerTag = %s, databaseKey = %s, isFault = %s, isBypass = %s WHERE plcTagName = %s""")
        data = (logValue, triggerTag, databaseKey, isFault, isBypass, plcTagName)
        print(sql,data)
        self.cur.execute(sql, data)
        self.conn.commit()

    def insertIntoDataGroup(self, table, headers, values):  # In Progress
        delimiter = ','
        valueStr = ""
        index = 0

        for header in headers:
            if index == 0:
                valueStr = "%s"
            else:
                valueStr = valueStr + ", %s"
            index = index + 1

        # INSERT INTO `Barcode_data` (`time`, `Barcode`, `TestDintSensor`, `TestIntSensor2`, `TestRealSensor4`, `TestSintSensor3`) VALUES ('2022-01-21 08:18:24', 'BCR12345', '1', '2', '2.3', '4')

        sql = (f"INSERT INTO {table} ({delimiter.join(headers)}) VALUES ({valueStr})")
        data = (values)
        print(sql, data)
        self.cur.execute(sql, data)
        self.conn.commit()

    def insertIntoData(self, table, header, value):
        valueStr = "%s,%s"
        sql = (f"INSERT IGNORE INTO {table} ({header}, time) VALUES ({valueStr})")
        data = (value, datetime.now())
        print(sql, data)
        self.cur.execute(sql, data)
        self.conn.commit()

    def updateData(self, table, header, databasekey, databasekeyVal, value):
        valueStr = "%s"
        sql = (f"UPDATE {table} SET {header} = {valueStr} WHERE {databasekey} = {valueStr}")
        data = (value, databasekeyVal)
        print(sql, data)
        self.cur.execute(sql, data)
        self.conn.commit()

    def selectAll(self):
        sql = ("""SELECT * FROM importedTags""")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def selectAllTable(self, table):
        sql = (f"SELECT * FROM {table} ORDER BY time DESC")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def selectAllEventLog(self):
        sql = (f"SELECT * FROM eventLog ORDER BY time DESC")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def selectAllFaultLog(self):
        sql = (f"SELECT * FROM faultLog ORDER BY time DESC")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def selectAllBypassLog(self):
        sql = (f"SELECT * FROM bypassLog ORDER BY time DESC")
        data = ()
        self.cur.execute(sql, data)
        result = self.cur.fetchall()
        return result

    def deployUpdateDB(self):
        # Steps To Deploy/Update Database
        # 1. Cycle through the tags and pull a list of active database keys
        # 2. Check If Database Already Exists Else Create New Database called {DatabaseKey}_data
        # 3. For each database key pulled cycle through the database and build a list of required tags with Log Value = 1.
        #    Also do a double grab to make sure we always add database key
        # 4. Check For Existing Columns And Create columns in the database with the correct datatypes

        # Step 1
        sql = ("""SELECT * FROM importedTags""")
        data = ()
        self.cur.execute(sql, data)
        results = self.cur.fetchall()
        tempResults = []
        activeResults = []
        duplicate = False

        for result in results:
            if result[4] != '' and result[4] != None:
                tempResults.append(result[4])

        # Remove Duplicates From The List
        for i in tempResults:
            if i not in activeResults:
                activeResults.append(i)

        # Step 2
        for activeResult in activeResults:
            # Deploy New Table If it doesnt Exist
            sql = "CREATE TABLE IF NOT EXISTS " + activeResult + """_data (time datetime)"""
            data = ()
            self.cur.execute(sql, data)
            self.conn.commit()

        # Step 3
        # Grab
        for table in activeResults:
            sql = ("""SELECT * FROM importedTags WHERE databaseKey = %s AND logValue = 1""")
            data = (table,)
            self.cur.execute(sql, data)
            results = self.cur.fetchall()

            # Grab Database Key Result
            sql = ("""SELECT * FROM importedTags WHERE plcTagName = %s""")
            data = (table,)
            self.cur.execute(sql, data)
            plcTagNameResult = self.cur.fetchall()
            # Add Database Key Column To Database
            databaseKey = table
            databaseTable = (f"{table}_data")
            datatype = self._grabDBDatatype(plcTagNameResult[0][1])
            sql = ("ALTER TABLE " + databaseTable + " ADD COLUMN IF NOT EXISTS " + databaseKey + " " + datatype)
            data = ()
            # self.cur.execute(sql, data)
            # self.conn.commit()

            # Step 4
            # Add The New Columns

            for result in results:
                plcTagName = result[0]
                databaseTable = (f"{result[4]}_data")
                datatype = self._grabDBDatatype(result[1])
                sql = ("ALTER TABLE " + databaseTable + " ADD COLUMN IF NOT EXISTS " + plcTagName + " " + datatype)
                data = ()
                print(sql)
                self.cur.execute(sql, data)
                self.conn.commit()

            # SET The Database Key
            databaseTable = (f"{table}_data")
            databaseKey = table
            print(f"{databaseTable} {databaseKey}")
            sql = ("ALTER TABLE " + databaseTable + " ADD PRIMARY KEY IF NOT EXISTS(" + databaseKey + ")")
            data = ()
            self.cur.execute(sql, data)
            self.conn.commit()

    def tableList(self):
        sql = ("""SHOW TABLES;""")
        self.cur.execute(sql)
        results = self.cur.fetchall()
        dataTables = []
        for result in results:
            if "_data" in result[0]:
                dataTables.append(result[0])
        return dataTables

    def readColumnsForTable(self, tableName):
        sql = (f"SHOW columns from {tableName}")
        self.cur.execute(sql)
        return self.cur.fetchall()

    def eventLogInsert(self, time, level, event):
        sql = ("""INSERT INTO eventLog (time,level,event) VALUES (%s,%s,%s)""")
        event = event[:255]
        data = (time, level, event)
        self.cur.execute(sql, data)
        self.conn.commit()

    def faultLogInsert(self, time, event):
        sql = ("""INSERT INTO faultLog (time,event) VALUES (%s,%s)""")
        event = event[:255]
        data = (time, event)
        self.cur.execute(sql, data)
        self.conn.commit()
        print(f"Inserted {event} into fault log @ {time}")

    def bypassLogInsert(self, time, event):
        sql = ("""INSERT INTO bypassLog (time,event) VALUES (%s,%s)""")
        event = event[:255]
        data = (time, event)
        self.cur.execute(sql, data)
        self.conn.commit()
        print(f"Inserted {event} into bypass log @ {time}")

if __name__ == "__main__":
    connection = gvsDB("gvsDataLogger")

    # Retrieve Tables Test
    tablelist = connection.tableList()
    print(tablelist)

    # plcType = 0
    # ipAddress = "192.168.1.1"

    # Update Test
    # connection.configurationSave(plcType,ipAddress)

    # Insert Test
    # connection.configurationInsert(plcType,ipAddress)

    # Read Test
    # print(connection.configurationRead())
    # user = connection.configurationRead()[0][0]
    # username = connection.configurationRead()[0][1]
    # plcType = connection.configurationRead()[0][2]
    # ipAddress = connection.configurationRead()[0][3]
    # print(f"User = {user} Username = {username} plcType = {plcType} ipAddress = {ipAddress}")

    # tagImportInsert Test
    # connection.tagImportInsert("tagname","plctagname","INT",0,"triggertag")\

    # tagImportRead All Test
    # print(connection.tagImportReadAll())
    # print(connection.tagImportCheckMatch("TestIntegerr", "TedstInt"))

    # search for DB Saved Tag Name Test
    # print(connection.searchForDBSavedTagName('TestInteger'))

    # Deploy Testing
    # connection.deployUpdateDB()

    # INSERT INTO `Barcode_data` (`time`, `Barcode`, `TestDintSensor`, `TestIntSensor2`, `TestRealSensor4`, `TestSintSensor3`) VALUES ('2022-01-21 08:18:24', 'BCR12345', '1', '2', '2.3', '4')
    # table = "Barcode_data"
    # headers = ('time', 'Barcode', 'TestDintSensor', 'TestIntSensor2', 'TestRealSensor4')
    # data = ('2022-01-21 08:18:24', 'BCR12345', '1', '2', '2.3')
    # connection.insertIntoData(table, headers,data )
