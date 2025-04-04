'''
GVS AI nxOmronPLC_V1_4
Reads Tags From Omron NX PLC
Author: Kevin Lay
Version Log:
V1_0 Init
V1_1 Changed To OOP to hold a connection
V1_2 Added Close Function Updated Program For aphyt v 0.1.7
V1_3 ...
V1_4 Thread Dispatcher
V1_5 Added Comments
'''

# Import the required library for communication with Omron NX PLC
from aphyt import omron

# Define a class to hold an Omron connection
class omronConnection:
    def __init__(self, ip):
        """
        Initialize the Omron connection
        :param ip: IP address of the Omron PLC to connect to
        """
        # Create an instance of the Omron NSeriesThreadDispatcher
        self.eip_instance = omron.n_series.NSeriesThreadDispatcher()
        # Connect to the Omron PLC with the given IP address
        self.eip_instance.connect_explicit(ip)
        # Register a session with the Omron PLC
        self.eip_instance.register_session()
        # Update the variable dictionary of the Omron PLC
        self.eip_instance.update_variable_dictionary()
        # Print a message to indicate a successful connection to the Omron PLC
        print("Successfully Connect To Omron PLC")

    def _approvebasetag(self, tag):
        """
        Check if the tag value is a basic data type
        :param tag: value of the tag to check
        :return: True if tag is of a basic data type, False otherwise
        """
        # Check if the tag is of type bool, int, bytes, str or float
        if type(tag) == bool or type(tag) == int or type(tag) == bytes or type(tag) == str or type(tag) == float:
            # Return True if the tag is of approved data type
            return True
        else:
            # Return False if the tag is not of approved data type
            return False

    def plcreadsingle(self, tagname):
        """
        Read the value of a single tag from the Omron PLC
        :param tagname: name of the tag to read
        :return: a dictionary with the tagname and its value, or a nested dictionary if the tag value is a structured
        data type
        """
        # Create a dictionary to hold the tagname and its value
        my_dict = None
        # Read the tag value from the Omron PLC
        tags = self.eip_instance.read_variable(tagname)
        # Check if the tag value is of approved data type
        if self._approvebasetag(tags) == True:
            # If the tag value is of approved data type, create a dictionary with the tagname and its value
            my_dict = {tagname: tags}
        else:
            # If the tag value is not of approved data type, create a nested dictionary with the tagname and its members
            inner_dict = tags.members
            my_dict = {tags.variable_name: inner_dict}
        # Return the dictionary holding the tagname and its value
        return my_dict

    def close(self):
        """
        Close the Omron connection
        """
        self.eip_instance.close_explicit()

if __name__ == "__main__":
    # Create an instance of the omronConnection class with the IP address of the Omron PLC
    con = omronConnection("10.203.26.10")
    # Define the tag to read from the Omron PLC
    tagReq = "RemoteInputs_gvsAI.DI_10000_Spare"
    # Read the tag value from the Omron PLC
    tags = con.plcreadsingle(tagReq)
    # Print the dictionary holding the tagname and its value
    print(tags)
