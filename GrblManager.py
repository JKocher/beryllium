"""
Beryllium - Copyright (c) 2021 Jason Kocher

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
"""

######## Imports ########
from BerylLogger import BerylLogger
from BerylLogger import BerylLogLevel
from GrblConfigFileManager import GrblConfigFileManager
import serial
from serial.tools import list_ports
from serial.tools.list_ports_common import ListPortInfo
import time
import threading
import sys
import RPi.GPIO as GPIO
from gerbil.gerbil import Gerbil


######## Class Definitions ########
class GrblManager():
    ######## Constants ########


    ######## Public Methods ########
    def __init__(self):
        self.logger = BerylLogger(self.__class__.__name__, BerylLogLevel.DEBUG)
        self.serialPort = None
        self.grbl = Gerbil(self.gerbil_callback)
        self.grbl.setup_logging()
        self.callbacks = []
        self.isInAbortRecovery = False


    def start(self):
        self.logger.debug("start requested")
        if( self.grbl.is_connected() ):
            raise RuntimeError('already connected')
        if( self.serialPort == None ):
            raise RuntimeError('no serial port specified')
        # if we made it here, we have a valid serial port
        self.grbl.cnect(self.serialPort.name, 115200)
        
        time.sleep(1)


    def stop(self):
        self.logger.debug("stop requested")
        self.grbl.disconnect()


    def listSerialPorts(self):
        retVal = list_ports.comports()
        # hardcode /dev/ttyS0...for some reason it's not being detected
        retVal.append(ListPortInfo(device="/dev/ttyS0"))
        return retVal


    def changeSerialPort(self, listPortInfoIn):
        if( not isinstance(listPortInfoIn, ListPortInfo) ):
            raise ValueError('invalid ListPortInfo object passed')
        # if we made it here, we have a valid serial port object
        wasConnected = self.grbl.is_connected()
        if( wasConnected ):
            self.stop()
        # if we made it here, we are ready to change the port
        self.logger.debug("changing serial port to {}".format(listPortInfoIn.device))
        self.serialPort = serial.Serial(port=listPortInfoIn.device, baudrate=115200, timeout=0.25) #timeout=0.25 or 5 JTK
        if( wasConnected ):
            self.start()


    def sendGrblCommand(self, commandIn):
        if( not self.grbl.is_connected() ):
            print('not connected')
            return
        # if we made it here, we're connected
        self.logger.debug("sending command: {}".format(commandIn))
        self.grbl.send_immediately(commandIn)
        #return 99


    def createNewJob(self):
        self.grbl.job_new()
        
        
    def appendLineToCurrentJob(self, newLineIn):
        self.grbl.write(newLineIn)
        
        
    def startCurrentJob(self):
        #self.grbl._incremental_streaming = True  #Tried forcing the system to "Incremental Streaming" so commands are only sent after "OK" from GRBL. Seems to have fixed the issue.
        self.grbl.incremental_streaming = True
        self.grbl.job_run(0)  #Added 0 (starting buffer line number) to try to mitigate incorrect GRBL moves. JTK 3/29/21
        
        
    def hold(self):
        self.grbl.hold()
        
    def set_feed_override(self, val): #Incomplete JTK 4/29/21
        self.grbl.set_feed_override(val)
        
    def request_feed(self, requested_feed): #Incomplete JTK 4/29/21
        self.request_feed(requested_feed)
        
        
        
    def resume(self):
        self.grbl.resume()
        
        
    def haltCurrentJob(self):
        self.grbl.hold()
        time.sleep(2)
        self.grbl.job_halt()
        time.sleep(1)
        self.isInAbortRecovery = True
        self.grbl.abort()
        self.grbl.disconnect()
        time.sleep(2)
        self.isInAbortRecovery = False
        self.grbl.cnect(self.serialPort.name, 115200)
        
        
    def addPositionCallback(self, callback):
        self.callbacks.append(callback)
        

    ######## Private Methods ########
    # called automatically by Gerbil when events occur
    def gerbil_callback(self, eventstring, *data):
        args = []
        for d in data:
            args.append(str(d))
        self.logger.debug("gerbil_callback: event={} data={}".format(eventstring.ljust(30), ", ".join(args)))
        
        if (eventstring == "on_boot") and (self.isInAbortRecovery == False):
            self.sendGrblCommand('G20') #units inches
            self.sendGrblCommand('G18') #X-Z Plane
            configFileMan = GrblConfigFileManager()
            configFileMan.applyConfigFileSaveHash(self)
            self.sendGrblCommand("G54")
            self.grbl.poll_start()
            
        elif eventstring == "on_stateupdate":
            pos_x = data[2][0]
            pos_y = data[2][1]
            pos_z = data[2][2]
            for currCallback in self.callbacks:
                currCallback((data[0] == 'Idle'), pos_z, pos_x)