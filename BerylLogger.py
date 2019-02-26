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
        if( not isinstance(nameIn, basestring) ):
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
