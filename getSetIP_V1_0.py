'''
GVS AI getSetIP_V1_0
Set WLAN / ETH 0 Port On Raspberry PI
Version Log:
V1_0 Init
Author: Kevin Lay
'''

import ipaddress
from tkinter import N
import netifaces as ni
from os import system


def getIPs():
    # Grab Current IP Address
    eth0 = ni.ifaddresses('eth0')[2][0]['addr']
    wlan0 = ni.ifaddresses('wlan0')[2][0]['addr']
    return eth0, wlan0


def setEth0(ipAddress):
    if ipAddress != "":
        eth0_interface_1 = "auto eth0\n"
        eth0_interface_2 = "iface eth0 inet static\n"
        eth0_interface_3 = f"    address {ipAddress}"
        eth0_interface = [eth0_interface_1, eth0_interface_2, eth0_interface_3]
        try:
            with open("/etc/network/interfaces.d/eth0", 'w') as f:
                for line in eth0_interface:
                    f.write(line)
            system('sudo reboot')
        except Exception as e:
            return e


def setWlan0(ipAddress):
    if ipAddress != "":
        wlan0_interface_1 = "auto wlan0\n"
        wlan0_interface_2 = "iface wlan0 inet static\n"
        wlan0_interface_3 = f"    address {ipAddress}"
        wlan_interface = [wlan0_interface_1, wlan0_interface_2, wlan0_interface_3]
        try:
            with open("/etc/network/interfaces.d/wlan0", 'w') as f:
                for line in wlan_interface:
                    f.write(line)
            system('sudo reboot')
        except Exception as e:
            return e
