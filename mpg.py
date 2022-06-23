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

from BerylLogger import BerylLogger
from BerylLogger import BerylLogLevel
import RPi.GPIO as GPIO
import time
import threading
import sys

######## Class Definitions ########
class BerylMPG():
    ######## Constants ########
    LOOP_SLEEP_TIME_S = 0.001

    ######## Public Methods ########
    def __init__(self):
        self.logger = BerylLogger(self.__class__.__name__, BerylLogLevel.DEBUG)
        self.keepRunning = True

        self.thread = threading.Thread(target=self.run, args=())
        self.thread.daemon = True

        GPIO.setmode(GPIO.BOARD)
        #GPIO.setmode(GPIO.BCM)

        #GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        #GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
        GPIO.setup(16, GPIO.IN)
        GPIO.setup(18, GPIO.IN)
        self.pulseCount = 0
        self.encoder_A_Old = 0
        self.pulseAddSub = 0 #used to return +1 to increment, -1 to decrement
        self.freshPulses = 1 #used to manage pulses that have been seen already

    def start(self):
        self.logger.debug("start requested")
        self.thread.start()


    def stop(self):
        self.logger.debug("stop requested")
        self.keepRunning = False

    def getPulseCount(self):
        return self.pulseCount

    def getPulseAddSub(self):
        return self.pulseAddSub

    def getFreshPulses(self):
        return self.freshPulses

    def setFreshPulses(self, flagVal):
        self.freshPulses = flagVal
        return

    ######## Private Methods ########
    def run(self):
        self.logger.debug("thread starting")

        while self.keepRunning:
            currA = GPIO.input(18)
            if( (currA == 1) and (currA != self.encoder_A_Old) ):
                currB = GPIO.input(16)
                if( currB == 1 ):
                    self.pulseCount += 1
                    self.pulseAddSub = 1
                    self.freshPulses = 1 #indicate we have a fresh pulse (cleared in the UI)
                else:
                    self.pulseCount -= 1
                    self.pulseAddSub =-1
                    self.freshPulses = 1 #indicate we have a fresh pulse (cleared in the UI)
                #self.logger.debug(self.pulseCount)
                #self.logger.debug(self.pulseAddSub)

            self.encoder_A_Old = currA
            # yield to other read-to-run threads
            time.sleep(BerylMPG.LOOP_SLEEP_TIME_S)
        self.logger.debug("thread stopped")
