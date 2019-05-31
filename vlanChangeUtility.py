#!/usr/bin/env python3

# Documentation...
# python -m pip install netmiko
# https://docs.python.org/2/library/socket.html
# https://docs.python.org/2/library/getpass.html

from __future__ import print_function, unicode_literals

##########################
# Import
##########################

# Netmiko is the same as ConnectHandler
from netmiko import Netmiko
from getpass import getpass

import string
import socket

##########################
# Functions Defintions Start
##########################

# Menu defintions
def ciscoMenu():
    print ("1. Show VLAN list")
    print ("2. Show interface status")
    print ("3. Modify interface")
    print ("4. Exit")

def showVlan():
    showVlan = net_connect.send_command('show vlan brief')
    print (showVlan)

def showInt():
    showInt = net_connect.send_command('show int '+switchInt+ ' status')
    print (showInt)

# def modifyInterface():

def exitProgram():
    print ("\nExiting Program")
    print ('\nThank you for using the VLAN Change Utility, Goodbye!')
    loop=False  # Exit menu to exit application
    net_connect.disconnect()

##########################
# Functions Defintions End
##########################

print ('Welcome to the VLAN change utility.')
userMAC = input("\nPlease enter the MAC address you would like to search. Must be HHHH.HHHH.HHHH format: ")
deviceName = input("Please enter the IP of the switch you would like to search: ")

username = input("\nUsername: ")
password = getpass()

# connect to user's choice
while True:
	try:
		myDevice = {
		'host': deviceName,
		'username': username,
		'password': password,
		'device_type': 'cisco_ios',
		}
		print ('\nLogging in now...')
		# connects to "myDevice"
		net_connect = Netmiko(**myDevice)
		net_connect.enable()
		break
	except:
		print ('\nLogin failed. Please try again.')
		continue

print ('\nSearching MAC address...\n')

# check to see if the MAC is on the distro and grab some variables
while True:
    # issue show mac add add userMAC
    showMAC = net_connect.send_command('show mac add add ' +userMAC)
    # checks to see if we get correct output
    if 'Unicast Entries' in showMAC:
        # splits output into strings
        MAClst = [];
        for char in showMAC:
            MAClst.append(char)
        MACvarsplit = (''.join(MAClst).split('\n'))

        MACint = MACvarsplit[3]

        # grabs VLAN
        switchVLAN = MACint.split()[0]

        # grabs current interface
        currentSwitchInt = MACint.split()[4]

        break
    else:
        # if no results, tell the user MAC not found, check MAC
        print ('\n*****ERROR: MAC NOT FOUND****\n')
        # offer for them to change MAC and try again or change MAC
        userMAC = input('\nMust be HHHH.HHHH.HHHH format: ')
        continue

# runs traceroute and if the MAC is on another switch, it will connect. If the MAC is on the switch itself, it'll go directly to change VLAN
while True:
    tracerouteMAC = net_connect.send_command('traceroute mac ' +userMAC+ ' ' + userMAC)

    # MAC is on another switch
    if 'Layer 2 trace completed' in tracerouteMAC:

        # makes output into seperate strings
        TRACElst = [];
        for char in tracerouteMAC:
            TRACElst.append(char)
        TRACEvarsplit = (''.join(TRACElst).split('\n'))

        # grabs only the part of the output that contains IP and interface of MAC
        TRACEint = TRACEvarsplit[1]

        # grabs switch name
        switchName = TRACEint.split()[1]

        # grabs switch interface
        switchInt = TRACEint.split()[-1]

        # grabs switch IP
        outputSwitchIP = TRACEint.split()[2]
        switchIP = outputSwitchIP.strip(string.punctuation) # removes () from output

	# tell the user MAC has been found and where it is
        print ('\nMAC ' +userMAC+ ' has been found! \n\nSwitch: ' +switchName+ ' (' +switchIP+ ')\nInterface: ' +switchInt+ '\nVLAN: ' +switchVLAN)

	# connect to switch so they can change the VLAN
        changeVLAN = input ('\nWould you like to change the VLAN? Y/N: ').upper() # corrects user input into Uppercase
        if changeVLAN=='Y':
        	# connects to switchIP
        	while True:
        		try:
        			myDevice = {
        			'host': switchIP,
        			'username': username,
        			'password': password,
        			'device_type': 'cisco_ios',
        			}
        			print ('\nLogging into ' +switchName+ ' now...')
        			# connects to "myDevice"
        			net_connect = Netmiko(**myDevice)
        			net_connect.enable()
        			break
        		except:
        			print ('Login failed. Please try again.')
        			continue

        elif changeVLAN=='N':
        	exitProgram()
        break

    # MAC is on current switch.
    elif 'Source and Destination on same port and no nbr!' in tracerouteMAC:

	# tell the user the MAC has been found and is on the current switch
        print ('\nMAC ' +userMAC+ ' is on this switch! \n\nInterface: ' +currentSwitchInt+ '\nVLAN: ' +switchVLAN)

        # ask user if they want to change the VLAN
        changeVLAN = input ('\nWould you like to change the VLAN? Y/N: ').upper() # corrects user input into Uppercase
        if changeVLAN=='Y':
        	break

        elif changeVLAN=='N':
        	exit()

    else:
        print ('\nAn error has occured.')
        exitProgram()

while True:     # While loop which will keep going until loop = False
    ciscoMenu() # Displays menu
    menuChoice = input("Enter your choice [1-4]: ")
    if menuChoice=='1':
        showVlan()
    elif menuChoice=='2':
        showInt()
    elif menuChoice=='3':
        print ('\nShowing Current Configuration')
        output = net_connect.send_command('show run int '+switchInt)
        if 'Invalid input detected' in output: # Checks for valid port selection
            print ('*****ERROR: INVALID PORT TYPE****')
            continue
        print (output)
        if "switchport mode trunk" in output: # Checks for trunk port
            print ('*****ERROR: RESTRICTED PORT******')
            continue

        changeDecision = input('\nType "Yes" to change the VLAN or press any key to return: ').upper()

# Starting VLAN configuration
        if changeDecision == 'YES' or changeDecision == 'Y':
            vlanNumber = input ('\nPlease assign VLAN number: ') # User enters VLAN number
            showVlan = net_connect.send_command('show vlan brief') # Store variable if user does not execute menu option1
            if vlanNumber in showVlan: # Checks for valid vlan
                print ('\nAssiging VLAN number...')
                config_commands = [                                  # config_commands list array.
                'Interface '+switchInt,
                'switchport access vlan '+vlanNumber
                            ]
                net_connect.send_config_set(config_commands)
                print ('\nVlan Updated...')
                print ('\nShowing Updated Configuration')
                output = net_connect.send_command('show run int '+switchInt) # Show Updated Config after changes
                print (output)
                print ('\nWriting Configuration...')
                net_connect.send_command_expect('write mem') # Write Mem
            else:
                print ('******ERROR: INVALID VLAN CHOICE******')
                continue
# Ending VLAN configuration
    elif menuChoice=='4':
        exitProgram()
        break
    else:
        # Any integer inputs other than values 1-4 print an error message
        print("\nInvalid option. Enter any key to try again..")
