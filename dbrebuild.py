#!/usr/bin/env python

from __future__ import print_function


import sys
import os
import time
import subprocess
import shutil
import ConfigParser
import re

RECOVERY_VERSION = 2016					    #application version that enabled recovery
MIN_PART_NUM = 0					    #Smallest partition number
MAX_PART_NUM = 7					    #Highest  partition number
whoami	     = os.popen('whoami').read().rstrip('\n')	    #Get username of of user calling the script, remove carriage return
scriptname   = os.path.basename(sys.argv[0])		    #name of script
uname	     = os.uname()				    #Tuple containing system information
vartmp	     = "/var/tmp/"				    #path of vartmp
scriptmp     = vartmp + scriptname + "/"		    #make tmp dir vartmp/scriptname/
dbpath	     = ""					    #path to database directory, will be defined later
epoch	     = str ( int( time.time() ) )		    #number seconds since epoch, used for temp directory
tmpdir	     = scriptmp + scriptname + "." + epoch	    #set program temp dir  to

autodesk = ""						    #This will be assigned /opt/Autodesk or /usr/discreet depending what version is installed
DataBaseDict = {}					    #Declare empty datbase dictionary
recoveryStatus = ""					    #This will store if Enabled=yes or Enabled=no from [Recovery] of sw_dbd.cfg

#Name	: disclaimer():
#Purpose: Function that prints disclaimer of the script
def disclaimer():
    print ("==========================================================================================")
    print ("	Copyright (c) 2008 Autodesk, Inc.")
    print ("	All rights reserved.")
    print (" ")
    print ("	AUTODESK CANADA CO./AUTODESK, INC., MAKES NO WARRANTY, EITHER EXPRESS OR")
    print ("	IMPLIED, INCLUDING BUT NOT LIMITED TO ANY IMPLIED WARRANTIES OF")
    print ("	MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE REGARDING THESE MATERIALS,")
    print ("	AND MAKES SUCH MATERIALS AVAILABLE SOLELY ON AN AS-IS BASIS.")
    print (" ")
    print ("	IN NO EVENT SHALL AUTODESK CANADA CO./AUTODESK, INC., BE LIABLE TO ANYONE")
    print ("	FOR SPECIAL, COLLATERAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES IN CONNECTION")
    print ("	WITH OR ARISING OUT OF PURCHASE OR USE OF THESE MATERIALS. THE SOLE AND")
    print ("	EXCLUSIVE LIABILITY TO AUTODESK CANADA CO./AUTODESK, INC., REGARDLESS OF")
    print ("	THE FORM OF ACTION, SHALL NOT EXCEED THE PURCHASE PRICE OF THE MATERIALS")
    print ("	DESCRIBED HEREIN.")
    print ("")
    print ("    This script is not distributed by Autodesk Flame Family / Smoke Development")
    print ("    If issues are encountered please contact Autodesk Flame Technical Support")
    print ("    Troubleshooting of this script is not covered by Technical Support.")
    print ("    Technical support can investigate the database rebuild (with a valid support contract)")
    print ("    To contact support : https://manage.autodesk.com")
    print ("==========================================================================================")

#Name	: usage()
#Purpose: Displays usage instructions for the script
def usage():
    print (" ")
    print ("%s initiates a database rebuild on given partition(s) from mirror recovery files\n" %scriptname)
    print ("The user will be prompted to enter partition number(s)\n")
    print ("After verifying to continue the following will be done:")
    print ("   -stone+wire version will be checked to see if it supports mirror recovery")
    print ("   -stone+wire will be stopped")
    print ("   -The entered database files will be moved out of their location to a temp directory %s" %scriptmp)
    print ("   -sw_dbd.cfg file will be copied to a temp directory")
    print ("   -stone+wire will be started to initiate the datbase rebuild\n")
    print ("==========================================================================================\n")

#Name	: getDBpath
#Purpuse: get the path of datbase files. May be /opt/Autodesk/sw/swdb or /usr/discreet/sw/swdb
#	  Depending on versions installed
#	  returns list : autodesk and datbase path
def getDBpath():
    #First check to see if /opt/Autodesk/sw/swdb exists.
    #If it does, return that
    #If not check to see if /usr/discreet/sw/swdb exists
    #If it does, return that
    #If none exist, exit the program

    if os.path.exists("/opt/Autodesk/sw/swdb"):
	return ("/opt/Autodesk","/opt/Autodesk/sw/swdb")

    elif os.path.exists("/usr/discreet/sw/swdb"):
	return ("/usr/discreet","/usr/discreet/sw/swdb")

    else:
	print ("None of the following directoriews exist:")
	print ("   /opt/Autodesk/sw/swdb")
	print ("   /usr/discreet/sw/swdb")
	sys.exit(1)

#Name	: mktmpdir
#Purpose: Creates temp directory which will be used to move database files
def mktmpdir():

    pths = [ scriptmp, tmpdir ]		    # put /var/tmp/<scriptname>	   /var/tmp/<scriptname>/<scriptname>.<epoch>/ directories in a list
    for d in pths:			    # foreech dir in pths list see if directory exists if not create it

	if not os.path.exists(d):	    # if the path does not exist try and create it
	    try:
		os.mkdir(d)		    # make the directory
	    except:
		print ("Could not create temp directory %s" %dir)
		sys.exit(1)
	    os.chmod(d,0777) #set to 777


#Name	: verifySWstop
#Purpose: verify stone and wire database process has stopped
def verifySWstop(dbApp):

    #NEED TO VERIFY THAT sw_dbd stopped
    #Shell command is "ps -ef | egrep dbApp | grep -v grep"   # dbApp taks /optAutodesk and /usr/discreet into account
    #p1, p2, p3 are variables that stpre parts of the command becuse a | is used
    p1 = subprocess.Popen(["ps", "-ef"], stdout=subprocess.PIPE)
    p2 = subprocess.Popen(["egrep", dbApp], stdin=p1.stdout, stdout=subprocess.PIPE)
    p3 = subprocess.Popen(["grep", "-v", "grep"], stdin=p2.stdout, stdout=subprocess.PIPE)
    output, err = p3.communicate()
    p2.stdout.close()
    p1.stdout.close()
    output = output.rstrip('\n')
    return output


#Name	: stopStoneWireDB
#Purpose: stop the stone and wire database process
def stopStoneWireDB(autodesk):

    dbApp = autodesk + "/sw/sw_dbd"	   #Path to the stone+wire sw_dbd program

    if uname[0] == "Linux":   #we are on Linux
	#See if datbase program exists
	if os.path.exists(dbApp):	       #if datbase program exists continue
	    dbstop = dbApp + " -s"	       #    Sets the database stop command
	    print ("Executing: %s\n" %dbstop)  #    print database stop
	    os.system(dbstop)		       #    execute datbase stop
	else:				       #else exit program because database program not installed
	    print ("Could not find command %s" %dbApp)
	    sys.exit(1)
	print ("")

    else:							   #we are on a MAC
	stopf = "/Library/LaunchDaemons/com.autodesk.sw_dbd.plist" #set to plist of sw_dbd file
	if os.path.exists(stopf):				   #if plist file exists
	    dbstop = "launchctl unload -w " + stopf		   #	Sets the database stop command
	    print ("Executing: %s\n" %dbstop)			   #	print database stop
	    os.system(dbstop)					   #	execute datbase stop
	else:							   #else exit program because database program not installed
	    print ("Could not find command %s" %stopf)
	    sys.exit(1)
	print ("")

    #NEED TO VERIFY THAT sw_dbd stopped
    #Shell command is "ps -ef | egrep dbApp | grep -v grep"   # dbApp taks /optAutodesk and /usr/discreet into account
    #p1, p2, p3 are variables that stpre parts of the command becuse a | is used
    #p1 = subprocess.Popen(["ps", "-ef"], stdout=subprocess.PIPE)
    #p2 = subprocess.Popen(["egrep", dbApp], stdin=p1.stdout, stdout=subprocess.PIPE)
    #p3 = subprocess.Popen(["grep", "-v", "grep"], stdin=p2.stdout, stdout=subprocess.PIPE)
    #output, err = p3.communicate()
    #p2.stdout.close()
    #p1.stdout.close()
    #output = output.rstrip('\n')
    output = verifySWstop(dbApp)

    if	output != "": #then datbase did not stop so exit program
	print ("Datbase process did not stop : %s" %output)
	print ("Try killing process manually and execute this script again\n")
	sys.exit(1)

#Name	: startStoneWireDB
#Purpose: Start the stone+wire database
def startStoneWireDB(autodesk):

    startDB(autodesk)  # call startDB function

    print ("\nTo verify recovery is runnig do a tail -F %s/sw/log/sw_dbd.log" %autodesk)
    print ("You will know the recovery is done when \"Recovered\" messages stop being added to the log file")
    print ("Once the recovery finishes; run a vic on each partition recovered\n")

    for key, value in DataBaseDict.iteritems():
	dbf = tmpdir + "/part" + str(key) + ".db"
	if os.path.isfile(dbf):			   #if db file was moved to the temp dir print out vic command to run
	    if key != 0:			   #need to adjust stonefs if it is 0 or not
		print ("\t%s/io/bin/vic -v stonefs%s" %(autodesk,key))
	    else:
		print ("\t%s/io/bin/vic -v stonefs" %autodesk)
    print ("")



#Name	: getPartitions
#Purpose: Get partition numbers from the user and store on a dictionary
def getPartitions():
    DataBaseDict = {}	  #declare empty datbase dictionary

    while True:

	partnum =  raw_input ("Enter a partition number (%s - %s) <Enter nothing to exit> : " %(MIN_PART_NUM,MAX_PART_NUM))  #get user input

	if partnum ==  "":

	    print ("\nDONE GETTING PRATITION NUMBERS")
	    if bool(DataBaseDict):					   #if there is something in DataBaseDict  return DataBaseDict
		return DataBaseDict
	    else:							   #else there is nothing in DataBaseDict exit program
		print ("No valid partition numbers given\n")
		sys.exit(1)

	elif partnum.isdigit():						  #elseif input is a digit
	    dbfileNum = int (partnum)					  #    convert to integer
	    if	dbfileNum >= MIN_PART_NUM and dbfileNum <= MAX_PART_NUM:  #    verify it meets MIN_PART_NUM - MAX_PART_NUM
									  #
		fnum = dbpath + "/part" + str(dbfileNum) + ".db"	  #	       set it to part#.db
		DataBaseDict[dbfileNum] = fnum				  #	       push onto database dictionary

	    else:							  #    else it is a number just not from MIN_PART_NUM - MAX_PART_NUM
		print ("\tINVALID ENTRY")
	else:								  #else invalid entry (possible real number or text)
	    print ("\tINVALID ENTRY")					  #else it is non-number

#Name	: confirmRecovery
#Purpose: Verify client wants to proceed with the recovery
def confirmRecovery():

    while (True):
	ans = raw_input ("Would you like to proceed with recovery (y/n): ")

	if ans.lower() == "y":	 #if they answer Y/y proceed with program
	    print ("")
	    break
	elif ans.lower() == "n": #if they answer N/n exit the program
	    print ("")
	    sys.exit(0)
	else:			 #anything else	 start at the beginning of the loop
	    continue

#Name	: moveDbFiles
#Purpose: Move datbase files part#.db to temp directory
def moveDbFiles(autodesk):

    missing = 0;								    #Counter for db files not in autodesk/sw/swdb/
    for key, value in DataBaseDict.iteritems():					    #For all items in the datbase dictionary
	#print value
	if os.path.isfile(value):						    #Check if the datbase file exists
	    print ("move %s -> %s" %(value,tmpdir))				    #if it does move it

	    try:
		shutil.move(value,tmpdir)					     #try the move if it does not work print a warning
	    except:
		print ("\nWarning : I was not able to move %s -> %s" %(value,tmpdir))
		print ("\tYou may have to do manual recovery of this datbase file (check permissions)")

	else:									    #otherwise say it is being ignored
	    print ("%s file does not exist, ignoring" %value)
	    missing += 1

    if len(DataBaseDict) == missing:						    #all partitons given do not exist in autodesk/sw/swdb
	print ("RECOVERY NOT RUNNING\n")
	startDB(autodesk)							    # call startDB function
	sys.exit(1)


#Name	: startDB
#Purpose: start stone+wire datbase process
def startDB(autodesk):

    dbApp = autodesk + "/sw/sw_dbd"    #    Path to the stone+wire sw_dbd program; no need to check if	it exists since it already exists

    if uname[0] == "Linux":		   #Linux system
	dbstart = dbApp + " -d"		   #	set start datbase command
    else:				   #Mac	  system
	dbstart = "launchctl load -w /Library/LaunchDaemons/com.autodesk.sw_dbd.plist"

    print ("\nExecuting : %s\n" %dbstart)
    status  = int (os.system(dbstart)) #execute the start command


    if uname[0] == "Linux":				 #We are on Linux  and need to verify that sw_dbd started
	if status != 0:					 #datbase did not start print message to start it manually
	    print ("\t datbase process %s did not start, try starting manually" %s)
	    print ("")
	    sys.exit(1)

    else:						 #We are on MAC	   and need to verify that sw_dbd started
	output = verifySWstop(dbApp)

	if  output == "":				 # then datbase is not running
	    print ("\t datbase process %s did not start, try starting manually" %s)
	    sys.exit(1)

#Name	: copyCfgFile():
#Purpose: copy sw_dbd.cfg to tmpdir to compare in case issues
def copyCfgFile():

    sw_dbd_cfg = autodesk + "/sw/cfg/sw_dbd.cfg"	    #set the sw_dbd.cfg file

    if os.path.isfile(sw_dbd_cfg):			    #if sw_dbd.cfg file exists
	print ("copy %s -> %s" %(sw_dbd_cfg,tmpdir))	    #if it does copy to tmpdir

	try:
	    shutil.copy(sw_dbd_cfg,tmpdir)
	except:
	    print ("\nWarning : I was not able to copy %s -> %s" %(sw_dbd_cfg,tmpdir))



#Name	: recoveryIsEnabled():
#Purpose: returns True or False
#	  True : if mirror recovery is enabled
#	  False: if mirror recovery is disabled
def recoveryIsEnabled(autodesk):

    defaultDictionaty = {"Enabled" : "yes"}		   #set the [Recovery] default to Enabled=yes

    sw_dbd_cfg = autodesk + "/sw/cfg/sw_dbd.cfg"	    #set the sw_dbd.cfg file

    if os.path.exists(sw_dbd_cfg):			   #sw_dbd.cfg file exists so parse the file to see if it is enabled

	config = ConfigParser.ConfigParser(defaultDictionaty)		    #Parse the sw_dbd.cfg file
	config.read(sw_dbd_cfg)

	if config.has_section("Recovery"):							   #[Recovery] keyword is in the file
	    status = config.get("Recovery","Enabled")						   #get the status of [Recovery] and Enabled=
	    print ("\nAnalyzed %s: [Recovery] Enabled=%s\n"  %(sw_dbd_cfg,status.lower()))	   #print what recovery is
	    return status.lower()								   #return status.lower	 (everything in lowercase)

	else:											   #[Recovery] keyword is not in the file so assume yes
	    print ("\nAnalyzed %s [Recovery] Enabled=yes\n")
	    return "yes"

	#return config.get("Recovery","Enabled")	#returns the status of [Recovery] and Enabled=

    else:					#sw_dbd.cfg file does not exist so assume enabled by default
	print ("\n%s does not exist so [Recovery] Enabled=yes\n" %sw_dbd_cfg)
	return "yes"

###
#Name	: getSWversion():
#Purpose: determine the version of stone+wire, making sure recovery feature was implimented
def getSWversion():

    swversion = ""						 #set stone+wire version to blank string
    output    = ""						 #set output to blank string

    print ("Analyzing stonewire version\n")

    if uname[0] == "Linux":	 #we are on a Linux system execute "rpm -qa | grep autodesk.stonewire.servers" to get stonewire version

	p1 = subprocess.Popen(["rpm", "-qa"], stdout=subprocess.PIPE)
	p2 = subprocess.Popen(["grep", "autodesk.stonewire.servers"], stdin=p1.stdout, stdout=subprocess.PIPE)
	output, err = p2.communicate()
	p1.stdout.close()
	output = output.rstrip('\n')
	#print ("\nstonewire: %s\n" %output)	 #print statement for troubleshooting

    else:			 #we are on MAC (Darwin) execute "pkgutil --pkg-info | grep version" to get stonewire version
	p1 = subprocess.Popen(["pkgutil", "--pkg-info", "com.autodesk.stonewire.servers.x86_64.pkg"], stdout=subprocess.PIPE)
	p2 = subprocess.Popen(["grep", "version"], stdin=p1.stdout, stdout=subprocess.PIPE)
	output, err = p2.communicate()
	p1.stdout.close()
	output = output.rstrip('\n')
	#print ("\nstonewire: %s\n" %output)	 #print statement for troubleshooting

    pattern = re.compile('.+(\d{4})\.\d+\.\d+') #set pattern to look for something like 2017.1.1
    swversion = pattern.match(output)		#compare to the output variable

    if swversion == "None":			#Then no stonewire version installed so exit
	print ("\nNo stonewire version detected, exiting\n")
	sys.exit(1)

    else:
	yrtuple = swversion.groups()		#get the year from the pattern regular expression
	year	=  int(yrtuple[0])		#set year from tuple
	print	("stonewire version : %s" %year)
	if year < RECOVERY_VERSION:
	    print ("\nYour version of stone+wire does not support mirror recovery")
	    print ("Recovery enabled in %s" %RECOVERY_VERSION)
	    print ("	Your version is %s\n" %year)
	    sys.exit(1)


#MAIN PROGRAM#

disclaimer()									     #Print disclaimer
usage()										     #Print program useage

if not ( (uname[0] == "Linux") ^ (uname[0] == "Darwin") ):				 #Proceed if OS is Linux or Darwin (MAC)
    print ("\nYour OS is %s.  This only runs on Linux or Darwin (MAC)\n" %uname[0])
    sys.exit(1)

										     #Determine if user has root access.  If they do not exit(1)
if whoami != "root":
    print ("You must be logged in as root user in the terminal")
    print ("Or try executing with sudo:	 sudo ./%s\n" %scriptname)
    sys.exit(1)

getSWversion()							   #do a check to verify version has RECOVERY capability (RECOVERY_VERSION or hiher)


autodesk,dbpath = getDBpath()					   #get path to datdase directory could be /opt/Autodesk or /usr/discreet

if recoveryIsEnabled(autodesk) != "yes":			   #do a check to verify the recovery is enabled
    print ("Mirror recovery is not enabled\n")
    sys.exit(0)

mktmpdir()							   #make temp directory; where database files will be moved to

DataBaseDict = getPartitions()					   #Get datbase partition numbers from user and put in adictionary

confirmRecovery()						   #confirm user wanrts to proceed with the move

stopStoneWireDB(autodesk)					   #Stop stone+wire datbase process

moveDbFiles(autodesk)						   #Move database files to temp directory

copyCfgFile()							   #copy sw_dbd.cfg to tmpdir

startStoneWireDB(autodesk)					   #Start stone+wire datbase process
