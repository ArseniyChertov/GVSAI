'''
GVS AI nxOmronPLC_V1_2
Reads Tags From Omron NX PLC
Version Log:
V1_0 Init
V1_1 Changed To OOP to hold a connection
V1_2 Added Close Function Updated Program For aphyt v 0.1.7
Author: Kevin Lay
'''

from aphyt import omron

class omronConnection:
    def __init__(self, ip):
        self.eip_instance = omron.n_series.NSeries()
        self.eip_instance.connect_explicit(ip)
        self.eip_instance.register_session()
        self.eip_instance.update_variable_dictionary()
        print("Successfully Connect To Omron PLC")

    def _approvebasetag(self, tag):
        if type(tag) == bool or type(tag) == int or type(tag) == bytes or type(tag) == str or type(tag) == float:
            return True
        else:
            return False

    def plcreadsingle(self, tagname):
        # Create a dict for the tagname:value then add it to the local variables
        my_dict = None
        tags = self.eip_instance.read_variable(tagname)
        if self._approvebasetag(tags) == True:
            my_dict = {tagname: tags}
        else:
            inner_dict = tags.members
            my_dict = {tags.variable_name: inner_dict}
        print(my_dict)
        return my_dict

    def close(self):
        self.eip_instance.close_explicit()

if __name__ == "__main__":
    con = omronConnection("10.203.26.10")
    tagReq = "testBOOL"
    tags = con.plcreadsingle(tagReq)
    print(tags)
