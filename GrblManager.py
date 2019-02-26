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


######## Class Definitions ########
class GrblManager():
    ######## Constants ########


    ######## Public Methods ########
    def __init__(self):
        self.logger = BerylLogger(self.__class__.__name__, BerylLogLevel.DEBUG)
        self.serialPort = None
        self.serialLock = threading.Lock()
        self.keepRunning = True

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True


    def start(self):
        self.logger.debug("start requested")
        self.thread.start()


    def stop(self):
        self.logger.debug("stop requested")
        self.keepRunning = False


    def listSerialPorts(self):
        retVal = list_ports.comports()
        # hardcode /dev/ttyS0...for some reason it's not being detected
        retVal.append(ListPortInfo(device="/dev/ttyS0"))
        return retVal


    def changeSerialPort(self, listPortInfoIn):
        if( not isinstance(listPortInfoIn, ListPortInfo) ):
            raise ValueError('invalid ListPortInfo object passed')
        # if we made it here, we have a valid serial port object
        self.logger.debug("changing serial port to {}".format(listPortInfoIn.device))
        self.serialPort = serial.Serial(port=listPortInfoIn.device, baudrate=115200, timeout=5)


    def sendGrblCommand(self, commandIn):
        if( self.serialPort is None ):
            raise ValueError('serial port has not be set')
        # if we made it here, we have a valid serial port...send the command

        # make sure we only send one command at a time, no matter what threads are calling us
        with self.serialLock:
            self.logger.debug("sending command: {}".format(commandIn))
            self.serialPort.write(commandIn + '\n') # Send g-code block to grbl
            grbl_out = self.serialPort.readline().strip()   # Wait for grbl response with carriage return
            if( (grbl_out is None) or (len(grbl_out) == 0) ):
                # timeout
                self.logger.warn("timeout waiting for response from controller")
                # raise RuntimeError("timeout waiting for response from controller")
            elif( grbl_out == "ok" ):
                # complete successfully
                return
            elif( grbl_out.startswith("error:") ):
                # error
                self.logger.warn("controller indicates error: '{}'".format(grbl_out))
                # raise RuntimeError(grbl_out)
            else:
                # unknown error
                self.logger.warn("unknown error waiting for response from controller")
                # raise RuntimeError("unknown error waiting for response from controller")


    ######## Private Methods ########
    def run(self):
        self.logger.debug("thread starting")

        # check our configuration file
        configFileMan = GrblConfigFileManager()
        self.logger.debug("checking configuration file for changes")
        if( configFileMan.hasConfigFileChanged() ):
            configFileMan.applyConfigFileSaveHash(self)

        while self.keepRunning:
            # yield to other read-to-run threads
            time.sleep(0)
        self.logger.debug("thread stopped")
