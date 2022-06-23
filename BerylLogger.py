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
from enum import Enum
import time


######## Class Definitions ########
class BerylLogLevel(Enum):
    ERROR = 1
    WARN = 2
    INFO = 3
    DEBUG = 4


class BerylLogger():
    ######## Constants ########


    ######## Public Methods ########
    def __init__(self, nameIn, logLevelIn):
        if( not isinstance(nameIn, str) ): #basestring >> str (python3)
            raise ValueError('invalid name object passed')

        if( not isinstance(logLevelIn, BerylLogLevel) ):
            raise ValueError('invalid logLevel object passed')
        self.name = nameIn
        self.logLevel = logLevelIn


    def error(self, msgIn):
        self.checkLogLevelAndLog(BerylLogLevel.ERROR, msgIn)


    def warn(self, msgIn):
        self.checkLogLevelAndLog(BerylLogLevel.WARN, msgIn)


    def info(self, msgIn):
        self.checkLogLevelAndLog(BerylLogLevel.INFO, msgIn)


    def debug(self, msgIn):
        self.checkLogLevelAndLog(BerylLogLevel.DEBUG, msgIn)


    ######## Private Methods ########
    def checkLogLevelAndLog(self, levelIn, msgIn):
        if( levelIn.value <= self.logLevel.value ):
            print("{}  {}  {}  {}".format(time.time(), self.name, self.logLevel.name, msgIn))
