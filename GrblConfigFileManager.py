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
import configparser
import hashlib


######## Class Definitions ########
class GrblConfigFileManager():
    ######## Constants ########
    CONFIG_FILE_NAME = "beryllium.ini"
    CONFIG_FILE_HASH_NAME = "beryllium.ini.hash"
    CONFIG_SECTION_NAME = "Beryllium Settings"

    HASH_BLOCKSIZE = 65536

    CONFIG_TO_DOLLAR_CMD_MAP = {
        "steppulsetime_us": 0,
        "stepidletime_ms": 1,
        "stepportinvertmask": 2,
        "directionportinvertmask": 3,
        "stepenableinvert_bool": 4,
        "limitpinsinvert_bool": 5,
        "probepininvert_bool": 6,
        "statusreportmask": 10,
        "junctiondeviation_mm": 11,
        "arctolerance_mm": 12,
        "reportinches_bool": 13,
        "softlimits_bool": 20,
        "hardlimits_bool": 21,
        "homingcycle_bool": 22,
        "homingdirectioninvertmask": 23,
        "homingfeed_mmpermin": 24,
        "homingseek_mmpermin": 25,
        "homingdebounce_ms": 26,
        "homingpulloff_mm": 27,
        "maxspindlespeed_rpm": 30,
        "minspindlespeed_rpm": 31,
        "lasermodeenable_bool": 32,
        "xstepspermm": 100,
        "ystepspermm": 101,
        "zstepspermm": 102,
        "xmaxrate_mmpermin": 110,
        "ymaxrate_mmpermin": 111,
        "zmaxrate_mmpermin": 112,
        "xacceleration_mmpersec2": 120,
        "yacceleration_mmpersec2": 121,
        "zacceleration_mmpersec2": 122,
        "xmaxtravel_mm": 130,
        "ymaxtravel_mm": 131,
        "zmaxtravel_mm": 132,
        "xhomingpulloff_mm": 0,
        "yhomingpulloff_mm": 0,
        "zhomingpulloff_mm": 0,
    }


    ######## Public Methods ########
    def __init__(self):
        self.logger = BerylLogger(self.__class__.__name__, BerylLogLevel.DEBUG)


    def hasConfigFileChanged(self):
        # open our hash file first (to see if we have anything to compare against)
        previousHash = None;
        try:
            with open(self.CONFIG_FILE_HASH_NAME, 'r') as hashFile:
                previousHash = hashFile.readline().strip();
        except:
            pass

        # if we don't have a previous hash, we should assume something has changed
        if( (previousHash is None) or (not previousHash) ):
            self.logger.debug("no valid hash in '{}'...assuming no hash".format(self.CONFIG_FILE_HASH_NAME))
            return True

        # if we made it here, we have a previous hash...generate one for our current file
        newHash = self.computeHashForFile(self.CONFIG_FILE_NAME)

        # if we couldn't generate a hash for the file, assume something has changed
        if( (newHash is None) or (not newHash) ):
            self.logger.debug("cannot open '{}'...cannot compute hash".format(fileIn))
            return True

        # if we made it here, we have two hashes...compare them
        return (previousHash != newHash)


    def applyConfigFileSaveHash(self, grblManIn):
        self.logger.debug("opening configuration file '{}'".format(self.CONFIG_FILE_NAME))

        config = configparser.ConfigParser()
        readFiles = config.read(self.CONFIG_FILE_NAME)
        if len(readFiles) < 1:
            self.logger.warn("cannot open '{}'...using default config".format(self.CONFIG_FILE_NAME))
            return

        # read and apply all of our settings here
        self.logger.debug("applying configuration to GRBL")
        self.applyConfigItems(config.items(self.CONFIG_SECTION_NAME), grblManIn)

        # compute and update our stored hash for this file
        newConfigHash = self.computeHashForFile(self.CONFIG_FILE_NAME)
        if( (newConfigHash is None) or (not newConfigHash) ):
            self.logger.warn("cannot compute config hash...this config may be applied multiple times")
            return

        try:
            with open(self.CONFIG_FILE_HASH_NAME, "w") as hashFile:
                hashFile.write(newConfigHash)
        except:
            self.logger.warn("cannot write config file hash to file...this config may be applied multiple times")


    ######## Private Methods ########
    def computeHashForFile(self, fileIn):
        # if we made it here, we have a previous hash...generate one for our current file
        hasher = hashlib.md5()
        wasHashSuccessful = True
        try:
            with open(fileIn, 'rb') as afile:
                buf = afile.read(self.HASH_BLOCKSIZE)
                while len(buf) > 0:
                    hasher.update(buf)
                    buf = afile.read(self.HASH_BLOCKSIZE)
        except:
            wasHashSuccessful = False

        return hasher.hexdigest() if wasHashSuccessful else None


    def applyConfigItems(self, itemsIn, grblManIn):
        from GrblManager import GrblManager

        for (currKey, currVal) in itemsIn:
            # get the dollarCommand from our map
            dollarCommand = self.CONFIG_TO_DOLLAR_CMD_MAP.get(currKey, None)
            if( dollarCommand is None ):
                self.logger.warn("unknown key '{}'...skipping".format(currKey))
                continue

            cmd = "${}={}".format(dollarCommand, currVal)
            grblManIn.sendGrblCommand(cmd)
