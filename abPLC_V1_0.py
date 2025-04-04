'''
GVS AI abPLC_V1_0
Reads Tags From AB PLC
Version Log:
V1_0 Init
Author: Kevin Lay
'''

from pycomm3 import LogixDriver

def plcreadsingle(ip, tagname):
    with LogixDriver(ip) as plc:
        return plc.read(tagname)


if __name__ == "__main__":
    ipAddress = ("192.168.1.1")
    plcTag = ("TestBool")
    result = plcreadsingle(ipAddress, plcTag)
    if result.error == None:
        print(result.tag)
        print(result.value)
        print(result.type)
        print(result.error)
    else:
        print(result.error)
