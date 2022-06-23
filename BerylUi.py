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
from GrblManager import GrblManager
from mpg import BerylMPG
from BerylLogger import BerylLogger
from BerylLogger import BerylLogLevel
from GCodes import gCodes
from GCodes import gProgram
import tkinter as tk
from tkinter import *
from tkinter import messagebox
from tkinter.font import Font
from tkinter import ttk
from tkinter.ttk import Progressbar
import time
import serial
import sys
import string
import threading
import math


######## Class Definitions ########
class BerylUi:
    ######## Constants ########


    ######## Public Methods ########
    def __init__(self, grblManIn, mpgIn):
        self.logger = BerylLogger(self.__class__.__name__, BerylLogLevel.DEBUG)
        if( not isinstance(grblManIn, GrblManager) ):
            raise ValueError('invalid grblManIn object passed')
        self.grblMan = grblManIn
        self.grblMan.addPositionCallback(self.onPositionCallback) #JTK commented until issues resolved
        self.mpg = mpgIn
        self.G0 = gCodes(0,0,0,0,0,0,0)
        self.G1 = gCodes(0,1,0,0,0,0,0)
        self.G2 = gCodes(0,2,0,0,0,0,0)
        self.G3 = gCodes(0,3,0,0,0,0,0)
        self.G4 = gCodes(0,4,0,0,0,0,0)
        self.gProg = gProgram()
        self.lineNumber = 0
        self.gcSelector = 1  #default to G1; feed rate and not rapid rate
        self.gcXvar = 0
        self.gcZvar = 0
        self.gcIvar = 0 #Used for G2 and G3 terms
        self.gcKvar = 0 #Used for G2 and G3 terms
        self.gcFvar = self.G0.getMaxCuts()
        #self.gcFvar = 10

        self.root = tk.Tk()  #root = blank window of Tkinter class
        self.root.title("Beryllium Lathe Controller - v1.6.1")
        #Automatically fill the screen, next two lines
        #width, height = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        #self.root.geometry('%dx%d+0+0' % (width,height))

        #Button Value Variables
        self.berylRadio = tk.DoubleVar()
        self.berylRadio.set(0)
        self.xStockVar = 0.6 #Variable used for handwheel  0.3750
        self.zStockVar = 1.5000 #Variable used for handwheel JTK 2/19/21 Need to resolve why this won't change default stock length when displayed
        self.moveXVar = 0
        self.moveZVar = 0
        self.vgVarWidth = 0.030
        self.vgVarWidthMin = 0.005
        self.vgVarWidthMax = 0.100 #Max width of Versagroove Tool
        self.vgVarRad = 0.005
        self.vgVarRadMin = 0.000
        self.vgVarRadMax = 0.050 #Max width of Versagroove Tool
        self.vgVarTheta = 90 #angle offset for Slicing
        self.vgVarThetaMin = 10
        self.vgVarThetaMax = 90
        self.vgVarRunout = 4 #Max allowed runout per slice batch from perimeter to part (0.5 for coding)
        self.vgVarRunoutMin = 0.1 #Multiplier of material diameter
        self.vgVarRunoutMax = 10 #Multiplier of material diameter
        self.coarseMode = 1
        self.coarseVar = 0.010
        self.coarseModeMax = 3
        self.retrVar = 0.050 #Parting retract distance
        self.retrVarMax = 0.5 #maximum retract distance
        self.retrVarMin = 0.001 #minimum retract distance
        self.peckVar = 0.030 #Parting pecking distance
        self.peckVarMax = 0.5 #maximum pecking distance
        self.peckVarMin = 0.001 #minimum pecking distance
        self.rghfrVar = 10 #Rough feed rate
        self.rghfrVarMax = 50 #maximum Rough feed rate
        self.rghfrVarMin = 1 #minimum Rough feed rate
        self.finfrVar = 5 #Finishing feed rate
        self.finfrVarMax = 50 #maximum Finishing feed rate
        self.finfrVarMin = 1 #minimum Finishing feed rate        
        self.rfrVar = 25 #Retract feed rate
        self.rfrVarMax = 50 #maximum Retract feed rate
        self.rfrVarMin = 1 #minimum Retract feed rate
        self.pfrVar = 1 #Peck feed rate
        self.pfrVarMax = 50 #maximum Peck feed rate
        self.pfrVarMin = 0.1 #minimum Peck feed rate
        self.pdVar = 0 #Parting OD
        self.pdVarMax = 0.750 #maximum Parting OD
        self.pdVarMin = -0.05 #minimum Parting OD, allow them to go past cutoff (X0).
        self.dzdxVar = 0.10 #CAM step size for all slicers
        self.dzdxVarMax = 0.25 #maximum 
        self.dzdxVarMin = 0.001 #minimum (probably don't want to step lower than this)
        self.finishVar = 0.01 #Roughing material depth in X left on the part
        self.finishVarMax = 0.025 #Roughing material depth in X left on the part Max
        self.finishVarMin = 0.001 #Roughing material depth in X left on the part Min
        self.fileNumVar = 1 #file extension used for naming Beryljob.nc files
        self.fileNumVarMax = 100 #maximum number of numbered files to allow the radio button to create (match this to predefined total of BerylJob files until something fancier written.)
        self.bMode = 0 #controls whether the resultant sliced vector space is shown
        self.bModeMin = 1 #Not going to be used unless we want to toggle various overlays 
        self.bModeMax = 2
        self.fovrVar = 100 #Feed Override 100%
        self.fovrVarMax = 500 #Max feed override
        self.fovrVarMin = 10 #Min feed override
        self.thetaLockState = 0 #When 1, movement of cutter is locked to Theta value
        self.zoneVar = -1 #-1 Defaults to all zones
        self.zoneVarMax = 100 #maximum 
        self.zoneVarMin = -1 #minimum, -1 Defaults to all zones
        self.zoomVar = 1 #Hardinge or mini lathe zoom (original)
        self.zoomVarMax = 3
        self.zoomVarMin = 1
        
        self.turnModeVar = 1 #Turning Mode
        self.turnModeVarMax = 2
        self.turnModeVarMin = 1
        
        self.FRP_Val = 100 #Feed Rate Percentage... NOTE:GRBL Limits to 10% min. Note: We are constructing/mimicking GRBL internal value

        #Canvas Management Variables
        self.zAxisCanvasLocation = 150  #Location of the axis labels
        self.xAxisCanvasLocation = 250  #Location of the axis labels (Probably not used due to variable X-Axis)
        self.canvasStockX = 0 #assumes cylindrical stock
        self.canvasStockZ = 0 #assumes cylindrical stock
        self.canvScaleFact = 150 #Scale X and Z by this amount to translate stock measurement to canvas units
        self.datumWindowZmin = -0.1000  #Window represented in inches
        self.datumWindowZmax = 2.0000   #Window represented in inches
        self.datumWindowXmin = -0.0250  #Window represented in inches
        self.datumWindowXmax = 1.2500   #Window represented in inches
        self.canvWindowXmin = 0    #Window represented in canvas units
        self.canvWindowXmax = 160  #Window represented in canvas units
        self.canvWindowZmin = 0    #Window represented in canvas units
        self.canvWindowZmin = 230  #Window represented in canvas units
        self.canvHeadStock= 10     #Location of theoretical headstock
        self.canvPartingLimit = (self.canvHeadStock + 10)
        self.reportedXVar = 0
        self.reportedZVar = 0

        self.canvasDatumX = 0 #displayed Z-X coordinate system
        self.canvasDatumZ = 0 #displayed Z-X coordinate system
        
        self.partCounter = 0 #Use for counting manufactured parts on canvas
        self.textID1 = None
        self.textID2 = None
        self.textID3 = None
        self.textID4 = None
        self.textID5 = None
        
        self.cursorOld = None
        self.cursorNew = None

        self.layoutUi()
        self.updateTextBox() #fill the text box with contents of program in RAM

    def start(self):
        # kick off our polling methods
        self.updateUiPeriodically()
        self.refreshPulseCount()        
        self.root.mainloop()

    ########Periodic Methods########
    def refreshPulseCount(self): #polling loop

        if self.gProg.berylRunBool == 1 and self.gProg.berylHoldBool == 0 and self.gProg.berylStopBool == 0: #if'we've started running a program...
            self.gProg.gRUN(self.grblMan, 1, 0) #Ping the RUN routine... (GRBL Manager, mode, initate value)

        if self.mpg.getFreshPulses() == 1:
            self.paintCanvas() #paint the canvas if we have a fresh pulse
            self.mpg.setFreshPulses(0) #clear this; reset by MPG code
            self.logger.debug(self.mpg.getPulseAddSub())

            if self.berylRadio.get() == 1:
                self.xStockVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.xStockVar <= 0:
                    self.xStockVar = 0
                if self.xStockVar >= 1.2500:
                    self.xStockVar = 1.2500
                self.xStockValue()

            if self.berylRadio.get() == 2:
                self.zStockVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.zStockVar >= 2.0000:
                    self.zStockVar = 2.0000
                if self.zStockVar <= 0.1000:
                    self.zStockVar = 0.1000
                self.zStockValue()

            if self.berylRadio.get() == 3: #fix zero float approximation bug with round()
                #self.moveXVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.thetaLockState == 1: #Handles Theta locked moves in Z
                    self.moveXVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                    self.moveZVar += -(self.mpg.getPulseAddSub() * self.coarseVar) / (math.tan(math.radians(self.vgVarTheta)))
                else:
                    self.moveXVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                #float(round(self.moveXVar, 4))
                self.moveXVar
                if self.moveXVar >= 0.625:
                    self.moveXVar = 0.625
                if self.moveXVar <= -0.625:
                    self.moveXVar = -0.625
                self.moveXValue()

            if self.berylRadio.get() == 4: #fix zero float approximation bug with round()
                self.moveZVar += (self.mpg.getPulseAddSub() * self.coarseVar)
                #float(round(self.moveZVar, 4))
                self.moveZVar
                if self.moveZVar >= 2.0000:
                     self.moveZVar = 2.0000
                if self.moveZVar <= -2.0000:
                     self.moveZVar = -2.0000
                self.moveZValue()

            if self.berylRadio.get() == 5:
                self.coarseMode += self.mpg.getPulseAddSub()
                if self.coarseMode >= self.coarseModeMax:
                    self.coarseMode = self.coarseModeMax    #limit this to the max GrblManager
                if self.coarseMode <= 0:
                    self.coarseMode = 0
                self.coarseValue()

            if self.berylRadio.get() == 6:
                self.fileNumVar += self.mpg.getPulseAddSub()
                if self.fileNumVar >= self.fileNumVarMax:
                    self.fileNumVar = self.fileNumVarMax    #limit this to the max GrblManager
                if self.fileNumVar <= 1:
                    self.fileNumVar = 1
                self.composeFileSelect()


            if self.berylRadio.get() == 8: #8-14 control the G-Code composer toolbar
                self.lineNumber += self.mpg.getPulseAddSub()
                if self.lineNumber <= 0:
                    self.lineNumber = 0
                self.term0Select()

            if self.berylRadio.get() == 9: #8-14 control the G-Code composer toolbar
                self.gcSelector += self.mpg.getPulseAddSub()
                if self.gcSelector <= 0:
                    self.gcSelector = 0
                if self.gcSelector >= 4:
                    self.gcSelector = 4
                self.term1Select()

            if self.berylRadio.get() == 10: #8-14 control the G-Code composer toolbar
                self.gcXvar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.gcXvar <= -0.050:
                    self.gcXvar = -0.050
                if self.gcXvar >= 0.6250:
                    self.gcXvar = 0.6250
                self.term2Select()

            if self.berylRadio.get() == 11: #8-14 control the G-Code composer toolbar
                self.gcZvar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.gcZvar <= -2:
                    self.gcZvar = -2
                if self.gcZvar >= 0.050:
                    self.gcZvar = 0.050
                self.term3Select()

            if self.berylRadio.get() == 12: #8-14 control the G-Code composer toolbar
                self.gcIvar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.gcIvar <= -0.050:
                    self.gcIvar = -0.050
                if self.gcIvar >= 0.625:
                    self.gcIvar = 0.625
                self.term4Select()

            if self.berylRadio.get() == 13: #8-14 control the G-Code composer toolbar
                self.gcKvar += (self.mpg.getPulseAddSub() * self.coarseVar)
                if self.gcKvar >= 0.050:
                    self.gcKvar = 0.050
                if self.gcKvar <= -2.0000:
                    self.gcKvar = -2.0000
                self.term5Select()

            if self.berylRadio.get() == 14: #8-14 control the G-Code composer toolbar
                self.gcFvar += (self.mpg.getPulseAddSub() * 0.1)
                if self.gcFvar <= 0:
                    self.gcFvar = 0
                if self.gcFvar >= self.G0.getMaxRapids():
                    self.gcFvar = self.G0.getMaxRapids()
                self.term6Select()

            if self.berylRadio.get() == 15: #15 Versagroove width selectionbutton
                self.vgVarWidth += (self.mpg.getPulseAddSub() * 0.001)
                if self.vgVarWidth <= self.vgVarWidthMin:
                    self.vgVarWidth = self.vgVarWidthMin
                if self.vgVarWidth >= self.vgVarWidthMax:
                    self.vgVarWidth = self.vgVarWidthMax
                self.versagrooveWidthValue()

            if self.berylRadio.get() == 16: #16 Versagroove radius selectionbutton
                self.vgVarRad += (self.mpg.getPulseAddSub() * 0.001)
                if self.vgVarRad <= self.vgVarRadMin:
                    self.vgVarRad = self.vgVarRadMin
                if self.vgVarRad >= self.vgVarRadMax:
                    self.vgVarRad = self.vgVarRadMax
                self.versagrooveRadValue()

            if self.berylRadio.get() == 17: #17 Angle angleValueSet
                self.vgVarTheta += (self.mpg.getPulseAddSub() * 1)
                if self.vgVarTheta <= self.vgVarThetaMin:
                    self.vgVarTheta = self.vgVarThetaMin
                if self.vgVarTheta >= self.vgVarThetaMax:
                    self.vgVarTheta = self.vgVarThetaMax
                self.angleValueSet()

            if self.berylRadio.get() == 18: #18 Runout runoutValueSet
                self.vgVarRunout += (self.mpg.getPulseAddSub() * 0.05)
                if self.vgVarRunout <= self.vgVarRunoutMin:
                    self.vgVarRunout = self.vgVarRunoutMin
                if self.vgVarRunout >= self.vgVarRunoutMax:
                    self.vgVarRunout = self.vgVarRunoutMax
                self.runoutValueSet()
                
            if self.berylRadio.get() == 19: #19 Parting Retract (RETR)
                self.retrVar += (self.mpg.getPulseAddSub() * 0.001)
                if self.retrVar <= self.retrVarMin:
                    self.retrVar = self.retrVarMin
                if self.retrVar >= self.retrVarMax:
                    self.retrVar = self.retrVarMax
                self.retrValue()
    
            if self.berylRadio.get() == 20: #20 Parting Peck (Peck)
                self.peckVar += (self.mpg.getPulseAddSub() * 0.001)
                if self.peckVar <= self.peckVarMin:
                    self.peckVar = self.peckVarMin
                if self.peckVar >= self.peckVarMax:
                    self.peckVar = self.peckVarMax
                self.peckValue()
                
            if self.berylRadio.get() == 21: #21 Retract feed rate
                self.rfrVar += (self.mpg.getPulseAddSub() * 0.5)
                if self.rfrVar <= self.rfrVarMin:
                    self.rfrVar = self.rfrVarMin
                if self.rfrVar >= self.rfrVarMax:
                    self.rfrVar = self.rfrVarMax
                self.rfrValue()
                
            if self.berylRadio.get() == 22: #22 Peck feed rate
                self.pfrVar += (self.mpg.getPulseAddSub() * 0.1)
                if self.pfrVar <= self.pfrVarMin:
                    self.pfrVar = self.pfrVarMin
                if self.pfrVar >= self.pfrVarMax:
                    self.pfrVar = self.pfrVarMax
                self.pfrValue()
                
            if self.berylRadio.get() == 23: #23 Parting OD
                self.pdVar += (self.mpg.getPulseAddSub() * 0.01)
                if self.pdVar <= self.pdVarMin:
                    self.pdVar = self.pdVarMin
                if self.pdVar >= self.pdVarMax:
                    self.pdVar = self.pdVarMax
                self.pdValue()
                
            if self.berylRadio.get() == 24: #24 dZdX CAM step size for all slicing
                self.dzdxVar += (self.mpg.getPulseAddSub() * 0.001)
                if self.dzdxVar <= self.dzdxVarMin:
                    self.dzdxVar = self.dzdxVarMin
                if self.dzdxVar >= self.dzdxVarMax:
                    self.dzdxVar = self.dzdxVarMax
                self.dzdxValue()
                
            if self.berylRadio.get() == 25: #25 roughing amount
                self.finishVar += (self.mpg.getPulseAddSub() * 0.001)
                if self.finishVar <= self.finishVarMin:
                    self.finishVar = self.finishVarMin
                if self.finishVar >= self.finishVarMax:
                    self.finishVar = self.finishVarMax
                self.roughValue()
                
            if self.berylRadio.get() == 26: #26 feed override
                self.fovrVar += (self.mpg.getPulseAddSub() * 10)
                if self.fovrVar <= self.fovrVarMin:
                    self.fovrVar = self.fovrVarMin
                if self.fovrVar >= self.fovrVarMax:
                    self.fovrVar = self.fovrVarMax
                self.fovrValue()

            if self.berylRadio.get() == 27: #27 Rough feed rate
                self.rghfrVar += (self.mpg.getPulseAddSub() * 0.5)
                if self.rghfrVar <= self.rghfrVarMin:
                    self.rghfrVar = self.rghfrVarMin
                if self.rghfrVar >= self.rghfrVarMax:
                    self.rghfrVar = self.rghfrVarMax
                self.rghfrValue()

            if self.berylRadio.get() == 28: #28 Finishing feed rate
                self.finfrVar += (self.mpg.getPulseAddSub() * 0.5)
                if self.finfrVar <= self.finfrVarMin:
                    self.finfrVar = self.finfrVarMin
                if self.finfrVar >= self.finfrVarMax:
                    self.finfrVar = self.finfrVarMax
                self.finfrValue()
            
            if self.berylRadio.get() == 29: #29 Slicer Zone number
                self.zoneVar += (self.mpg.getPulseAddSub() * 1)
                if self.zoneVar <= self.zoneVarMin:
                    self.zoneVar = self.zoneVarMin
                if self.zoneVar >= self.zoneVarMax:
                    self.zoneVar = self.zoneVarMax
                self.zoneValue()
                
            if self.berylRadio.get() == 30: #30 Canvas Zoom Setting
                self.zoomVar += (self.mpg.getPulseAddSub() * 1)
                if self.zoomVar <= self.zoomVarMin:
                    self.zoomVar = self.zoomVarMin
                if self.zoomVar >= self.zoomVarMax:
                    self.zoomVar = self.zoomVarMax
                self.zoomValue()
                
            if self.berylRadio.get() == 31: #31 Turning mode
                self.turnModeVar += (self.mpg.getPulseAddSub() * 1)
                if self.turnModeVar <= self.turnModeVarMin:
                    self.turnModeVar = self.turnModeVarMin
                if self.turnModeVar >= self.turnModeVarMax:
                    self.turnModeVar = self.turnModeVarMax
                self.turnModeValue()
                
        self.root.after(25, self.refreshPulseCount)  #polling loop

    ######## Position Callback Methods ########
    def onPositionCallback(self, isIdle, zPos, xPos):
        self.reportedXVar = xPos
        self.reportedZVar = zPos
        if isIdle:
            self.moveXVar = xPos
            self.moveZVar = zPos


    ######## UI Callback Methods #######
    def updateUiPeriodically(self):
        
        self.moveZButton["text"] = "Z-Pos:\n{:.4f}".format(self.reportedZVar)
        self.moveXButton["text"] = "X-Pos:\n{:.4f}".format(self.reportedXVar)
        
        zPO = self.canvasStockZ/self.canvScaleFact #Z Program Origin
        xPO = self.zAxisCanvasLocation/self.canvScaleFact #X Program Origin        
        self.cursorOld = self.cursorNew #Transfer the recent cursor to "old" status
        leZ = self.reportedZVar
        leX = self.reportedXVar
        convertedlineEndZ = (zPO+leZ)*self.canvScaleFact     #Converted for redering on canvas
        convertedlineEndX = (xPO-leX)*self.canvScaleFact      #Converted for redering on canvas         
        self.cursorNew=self.canvasFrame.create_oval(convertedlineEndZ-4,convertedlineEndX-4,convertedlineEndZ+4,convertedlineEndX+4,outline='yellow',fill='')                
        self.canvasFrame.delete(self.cursorOld)
        
        self.root.after(50, self.updateUiPeriodically)   # schedule to keep running
        
        
    def xStockValue(self): #berylRadio 1
        print("Adjusting xStockValue {}".format(self.xStockVar))
        self.xStockButton["text"] = "Work Diameter (X):\n{:.4f}".format(self.xStockVar)

    def zStockValue(self): #berylRadio 2
        print("Adjusting zStockValue {}".format(self.zStockVar))
        self.zStockButton["text"] = "Work Length (Z):\n{:.4f}".format(self.zStockVar)

    def versagrooveWidthValue(self):
        print("Testing vgWidthValue")
        self.toolWidthButton["text"] = "Tool Width:\n{:.3f}".format(self.vgVarWidth)

    def versagrooveRadValue(self):
        print("Testing vgRadValue")
        self.toolRadiusButton["text"] = "Tool Radius:\n{:.3f}".format(self.vgVarRad)

    def angleValueSet(self):
        print("Testing angleValueSet")
        self.angleButton["text"] = "Theta:{:.1f}".format(self.vgVarTheta)

    def runoutValueSet(self):
        print("Testing runoutValueSet")
        self.runoutButton["text"] = "Runout:{:.2f}D".format(self.vgVarRunout)
        
    def thetaLockZX(self):
        if self.thetaLockZXButton.config('relief')[-1] == 'sunken':
            self.thetaLockZXButton.config(relief='raised')
            self.thetaLockState = 0 #When 1, movement of cutter is locked to Theta value
            print("Theta LockZX OFF; Moves in Z or X are Normal")
        else:   
            self.thetaLockZXButton.config(relief='sunken')
            self.thetaLockState = 1 #When 1, movement of cutter is locked to Theta value
            print("Theta LockZX ON; Moves in Z or X follow Theta")
        self.paintCanvas() #paint the canvas if we have to update the text box


    def moveXValue(self):
        print("Testing moveXValue")
        self.moveXButton["text"] = "X-Pos:\n{:.4f}".format(self.moveXVar)
        self.moveZButton["text"] = "Z-Pos:\n{:.4f}".format(self.moveZVar)
        self.grblMan.sendGrblCommand("g0 x{:.4f} z{:.4f} f5".format(self.moveXVar,self.moveZVar))
        self.paintCanvas()

    def moveZValue(self):
        print("Testing moveZValue")
        self.moveXButton["text"] = "X-Pos:\n{:.4f}".format(self.moveXVar)
        self.moveZButton["text"] = "Z-Pos:\n{:.4f}".format(self.moveZVar)
        self.grblMan.sendGrblCommand("g0 x{:.4f} z{:.4f} f5".format(self.moveXVar,self.moveZVar))
        self.paintCanvas()
        
    def gotoOrg(self):
        print("Moving to Origin...")
        if self.turnModeVar == 1: #OD Profile Mode
            self.grblMan.sendGrblCommand("g1 x{} z{} f5".format((self.xStockVar/2+0.020),self.moveZVar))
            self.grblMan.sendGrblCommand("g1 x{} z0 f5".format(self.xStockVar/2+0.020))
            self.grblMan.sendGrblCommand("g1 x0 z0 f5")
        if self.turnModeVar == 2: #Boring mode  
            self.grblMan.sendGrblCommand("g1 x0 z{} f5".format(self.moveZVar))
            self.grblMan.sendGrblCommand("g1 x0 z0 f5")

    def coarseValue(self): #berylRadio 5
        print("Testing coarseMode {}".format(self.coarseMode))
        if self.coarseMode == 0:
            self.coarseVar = 0.100
        if self.coarseMode == 1:
            self.coarseVar = 0.010
        if self.coarseMode == 2:
            self.coarseVar = 0.001
        if self.coarseMode == 3:
            self.coarseVar = 0.0001 #Changed from 0.0002 JTK 10/17/21
        self.resButton["text"] = "MPG: {}".format(self.coarseVar)              

    def zeroXZ(self): #Zero the X and Z position
        self.moveXVar = 0
        self.moveZVar = 0
        print("Zeroing X and Z")
        self.moveXButton["text"] = "X-Pos:\n{:.4f}".format(self.moveXVar)
        self.moveZButton["text"] = "Z-Pos:\n{:.4f}".format(self.moveZVar)    
        self.grblMan.sendGrblCommand("G10 P1 L20 X0 Y0 Z0")
        self.paintCanvas() #Paint the canvas again so we can see the tool tip

    def zeroX(self): #Zero the X position
        self.moveXVar = 0
        print("Zeroing X")
        self.moveXButton["text"] = "X-Pos:\n{:.4f}".format(self.moveXVar)   
        self.grblMan.sendGrblCommand("G10 P1 L20 X0")
        self.paintCanvas() #Paint the canvas again so we can see the tool tip
        
    def zeroZ(self): #Zero the Z position
        self.moveZVar = 0
        print("Zeroing Z")
        self.moveZButton["text"] = "Z-Pos:\n{:.4f}".format(self.moveZVar)    
        self.grblMan.sendGrblCommand("G10 P1 L20 Z0")
        self.paintCanvas() #Paint the canvas again so we can see the tool tip
        
    def pgmStop(self):
        self.gProg.gSTOP()

    def pgmPause(self):
        self.gProg.gHOLD()

    def pgmRun(self):
        self.partCounter += 1
        print("Manufactured Parts Count:{}".format(self.partCounter))
        self.updateCanvasText()
        self.gProg.gRUN(self.grblMan, self.bMode) #GRBL Manager, run mode (constellation or resultant) initate value
        

    def composeFileSelect(self):
        self.bMode = 0 #Beryl G-Code Run Mode           
        self.gProg.gOpenFile('Beryljob{}.nc'.format(self.fileNumVar)) #Without passing the constellation and reference
        print("Selecting GCode File")
        self.FileSelectButton["text"] = "BerylJob{}.nc".format(self.fileNumVar)
        self.updateTextBox()
        
    def settingsMenu(self):
        print("PopUp Settings menu..")
        global popSM
        popSM = Toplevel(self.root)
        popSM.title("Settings Menu")
        #Position the popup window...
        self.root_x = self.root.winfo_rootx()
        self.root_y = self.root.winfo_rooty()
        popSM_x = self.root_x + 280
        popSM_y = self.root_y + 0        
        popSM.geometry("+{}+{}".format(popSM_x,popSM_y))
        #popSM.geometry("250x150")
            
        #Place all the SETTINGS buttons here:
        self.unitsButton = tk.Button(popSM, text="Units:\nIN",width=12, height=2, command=self.toggleUnits) #toggles between IN/MM
        self.unitsButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.toolWidthButton = tk.Radiobutton(popSM, text="Tool Width:\n{:.3f}".format(self.vgVarWidth), width=12, height=2, variable=self.berylRadio, value=15, indicatoron=0, command=self.versagrooveWidthValue)
        self.toolWidthButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.toolRadiusButton = tk.Radiobutton(popSM, text="Tool Radius:\n{:.3f}".format(self.vgVarRad), width=12, height=2, variable=self.berylRadio, value=16, indicatoron=0, command=self.versagrooveRadValue)
        self.toolRadiusButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.xStockButton = tk.Radiobutton(popSM, text="Work Diameter (X):\n{:.4f}".format(self.xStockVar), variable=self.berylRadio, value=1, indicatoron=0, command=self.xStockValue)
        self.xStockButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.zStockButton = tk.Radiobutton(popSM, text="Work Length (Z):\n{:.4f}".format(self.zStockVar), variable=self.berylRadio, value=2, indicatoron=0, command=self.zStockValue)
        self.zStockButton.pack(anchor=W, side="top", expand=True, fill='both')
        #self.settingsMenuButton["state"] = DISABLED #Need to re-enable the settings button after x-out of popup JTK 10/17/21
        #Code to populate label selection within zoomButton
        zoomText = None
        if self.zoomVar == 1:
            zoomText = "MultiForm"
        if self.zoomVar == 2:
            zoomText = "Custom 6x4"
        if self.zoomVar == 3:
            zoomText = "Custom 12x8"
        self.zoomButton = tk.Radiobutton(popSM, text="Canvas Zoom:\n{}".format(zoomText), width=12, height=2, variable=self.berylRadio, value=30, indicatoron=0, command=self.zoomValue)
        self.zoomButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.zoomButton["state"] = DISABLED
        #Code to populate label selection within turnModeButton
        turnModeText = None
        if self.turnModeVar == 1:
            turnModeText = "OD Profile"
        if self.turnModeVar == 2:
            turnModeText = "Boring"
        self.turnModeButton = tk.Radiobutton(popSM, text="Turn Mode:\n{}".format(turnModeText), width=12, height=2, variable=self.berylRadio, value=31, indicatoron=0, command=self.turnModeValue)
        self.turnModeButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.partCountButton = tk.Button(popSM, text="Clear Part Count", command=self.clearPartCount)
        self.partCountButton.pack(anchor=W, side="top", expand=True, fill='both')
        
    def screwWizard(self):
        print("Running Screw Wizard...")
    def ogiveWizard(self):
        print("Running Ogive Wizard...")
    def sphereWizard(self):
        print("Running Sphere Wizard...")
    
    
    def toggleUnits(self):
        #Code to toggle display units (default is Inches)
        print("Toggle display units...")
        
    def zoomValue(self):
        #Code to change the canvas zoom setting
        #self.zoomButton["text"] = "Zoom:\n{}".format(self.zoomVar)
        zoomText = None
        if self.zoomVar == 1:
            zoomText = "MultiForm"
        if self.zoomVar == 2:
            zoomText = "Custom 6x4"
        if self.zoomVar == 3:
            zoomText = "Custom 12x8"
        self.zoomButton["text"] = "Canvas Zoom:\n{}".format(zoomText)
        
    def turnModeValue(self):
        #Code to change the turn mode (OD Profile, etc)
        #self.turnModeButton["text"] = "Turn Mode:\n{}".format(self.turnModeVar)
        turnModeText = None
        if self.turnModeVar == 1:
            turnModeText = "OD Profile"
        if self.turnModeVar == 2:
            turnModeText = "Boring"
        self.turnModeButton["text"] = "Turn Mode:\n{}".format(turnModeText)
        self.updateCanvasText()

    def updateCanvasText(self):
        #On-canvas data
        #First clean up old text
        self.canvasFrame.delete(self.textID1)
        self.canvasFrame.delete(self.textID2)
        self.canvasFrame.delete(self.textID3)
        self.canvasFrame.delete(self.textID4)
        self.canvasFrame.delete(self.textID5)
        
        #Now write new text  
        self.textID4 = self.canvasFrame.create_text(20,25,fill="gray15",font="courier 10",text="Part Count:{}".format(self.partCounter), anchor="w")
        turnModeText = None
        if self.turnModeVar == 1:
            turnModeText = "OD Profile"
        if self.turnModeVar == 2:
            turnModeText = "Boring"
        self.textID5 = self.canvasFrame.create_text(20, 10, fill="gray15", font="courier 10", text="Status:{} Mode, Feed:{}%".format(turnModeText, self.FRP_Val), anchor="w")

    def paintCanvas(self):
        self.canvasStockX = (self.xStockVar*self.canvScaleFact)
        self.canvasStockZ = 10+(self.zStockVar*self.canvScaleFact)
        self.canvasFrame.delete(ALL) #clear the old canvas
        self.canvasFrame.create_rectangle(10,(self.zAxisCanvasLocation+((self.canvasStockX)/2)),self.canvasStockZ,(self.zAxisCanvasLocation-((self.canvasStockX)/2)),fill="LightSkyBlue2")

        self.canvasFrame.create_text((self.canvasStockZ+50),self.zAxisCanvasLocation,fill="darkblue",font="Times 20 italic bold",text="Z+")
        self.canvasFrame.create_text((self.canvasStockZ+20),((self.zAxisCanvasLocation-((self.canvasStockX)/2))-30),fill="darkblue",font="Times 20 italic bold",text="X+")
        self.canvasFrame.create_line(self.canvHeadStock,self.zAxisCanvasLocation,(self.canvasStockZ+25),self.zAxisCanvasLocation,dash=(4, 2)) #Z Axis
        self.canvasFrame.create_line(self.canvasStockZ,((self.zAxisCanvasLocation-((self.canvasStockX)/2))-5),self.canvasStockZ,((self.zAxisCanvasLocation-((self.canvasStockX)/2))-30),dash=(4, 2)) #X Axis
        self.canvasFrame.create_polygon(0,5,self.canvHeadStock,25,self.canvHeadStock,25,self.canvHeadStock,200,0,200, fill="gray28", outline="gray10")
        
        self.updateCanvasText() #update all of the text without destroying any slicer output


        if self.thetaLockState == 1:
            #print("Theta Lock ON")
            oppL = 0.5 #self.xStockVar/2  #Inches
            adjL = oppL/(math.tan(math.radians(self.vgVarTheta))) #Adjacent length, inches
            lsZ = self.moveZVar
            leZ = -adjL + self.moveZVar
            lsX = self.moveXVar
            leX = oppL + self.moveXVar
            self.thetaLine(lsZ, lsX, leZ, leX, "white")
        #else:
            #print("Theta Lock OFF")


        self.gProg.gDraw(self.canvasFrame, self.canvPartingLimit, (self.zAxisCanvasLocation), (self.canvasStockZ), (self.zAxisCanvasLocation-((self.canvasStockX)/2)), self.canvScaleFact, self.bMode) #pass the canvas, mode

    def thetaLine(self, lineStartZDec, lineStartXDec, lineEndZDec, lineEndXDec, lineColor): #Converts and plots decimal inch line on canvas from GUI   
        zPO = self.canvasStockZ/self.canvScaleFact #Z Program Origin
        xPO = self.zAxisCanvasLocation/self.canvScaleFact #X Program Origin
        lsZ = lineStartZDec
        lsX = lineStartXDec
        leZ = lineEndZDec
        leX = lineEndXDec
        color = lineColor
        convertedlineStartZ = (zPO+lsZ)*self.canvScaleFact #Converted for redering on canvas
        convertedlineStartX = (xPO-lsX)*self.canvScaleFact  #Converted for redering on canvas
        convertedlineEndZ = (zPO+leZ)*self.canvScaleFact     #Converted for redering on canvas
        convertedlineEndX = (xPO-leX)*self.canvScaleFact      #Converted for redering on canvas
        self.canvasFrame.create_line(convertedlineStartZ,convertedlineStartX,convertedlineEndZ,convertedlineEndX, dash=(2, 2),fill=color)

    def updateTextBox(self):  #Show contents of berylConstellation or berylResultant; used by other functions
        if self.bMode == 0:
            self.gCodeTextBox.delete(1.0, END)
            gCode_String = 'Empty' #only needed for debugging
            for index, dict in enumerate(self.gProg.berylConstellation, 0):
                if int(dict['G']) == 0: #if G0
                    gCode_String = 'BERYL N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(self.gProg.berylConstellation[index])
                elif int(dict['G']) == 1: #if G1
                    gCode_String = 'BERYL N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(self.gProg.berylConstellation[index])
                elif int(dict['G']) == 2: #if G2 CW Arc
                    gCode_String = 'BERYL N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(self.gProg.berylConstellation[index])
                elif int(dict['G']) == 3: #if G3 CCW Arc
                    gCode_String = 'BERYL N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(self.gProg.berylConstellation[index])
                elif int(dict['G']) == 4: #if G4
                    gCode_String = 'BERYL N{0[N]} G{0[G]} P{0[P]}'.format(self.gProg.berylConstellation[index])
                else:
                    gCode_String = 'GCode not found in iteration through self.gProg.berylConstellation'

                self.gCodeTextBox.insert(tk.END, gCode_String + '\n')
                self.paintCanvas() #paint the canvas if we have to update the text box
        elif self.bMode == 1:
            self.gCodeTextBox.delete(1.0, END)
            gCode_String = 'Empty' #only needed for debugging
            for index, dict in enumerate(self.gProg.berylResultant, 0):
                if int(dict['G']) == 0: #if G0
                    gCode_String = 'BERR N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(self.gProg.berylResultant[index])
                elif int(dict['G']) == 1: #if G1
                    gCode_String = 'BERR N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(self.gProg.berylResultant[index])
                elif int(dict['G']) == 2: #if G2 CW Arc
                    gCode_String = 'BERR N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(self.gProg.berylResultant[index])
                elif int(dict['G']) == 3: #if G3 CCW Arc
                    gCode_String = 'BERR N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(self.gProg.berylResultant[index])
                elif int(dict['G']) == 4: #if G4
                    gCode_String = 'BERR N{0[N]} G{0[G]} P{0[P]}'.format(self.gProg.berylResultant[index])
                else:
                    gCode_String = 'GCode not found in iteration through self.gProg.berylResultant'

                self.gCodeTextBox.insert(tk.END, gCode_String + '\n')
                self.paintCanvas() #paint the canvas if we have to update the text box
        else:
            self.paintCanvas() #paint the canvas if we have to update the text box        

    def sliceRadially(self):
        print("Slicing radially...")
        self.gProg.gSlice(self.canvasFrame, self.canvPartingLimit, (self.zAxisCanvasLocation), (self.canvasStockZ), (self.zAxisCanvasLocation-((self.canvasStockX)/2)), self.canvScaleFact, self.xStockVar, self.zStockVar, self.vgVarWidth, self.vgVarRad, self.vgVarTheta, self.vgVarRunout, self.retrVar, self.peckVar, self.rfrVar, self.pfrVar, self.pdVar, self.dzdxVar, self.finishVar, self.rghfrVar, self.finfrVar, self.zoneVar, 1) #pass the canvas, mode
        self.bMode = 1 #Run the resultant code when "RUN" button pressed
        print("Slicing Completed")
    def sliceAxially(self):
        self.gProg.gSlice(self.canvasFrame, self.canvPartingLimit, (self.zAxisCanvasLocation), (self.canvasStockZ), (self.zAxisCanvasLocation-((self.canvasStockX)/2)), self.canvScaleFact, self.xStockVar, self.zStockVar, self.vgVarWidth, self.vgVarRad, self.vgVarTheta, self.vgVarRunout, self.retrVar, self.peckVar, self.rfrVar, self.pfrVar, self.pdVar, self.dzdxVar, self.finishVar, self.rghfrVar, self.finfrVar, self.zoneVar, 2) #pass the canvas, mode
        self.bMode = 1 #Run the resultant code when "RUN" button pressed
        print("Slicing Completed")
    def sliceContour(self):
        self.gProg.gSlice(self.canvasFrame, self.canvPartingLimit, (self.zAxisCanvasLocation), (self.canvasStockZ), (self.zAxisCanvasLocation-((self.canvasStockX)/2)), self.canvScaleFact, self.xStockVar, self.zStockVar, self.vgVarWidth, self.vgVarRad, self.vgVarTheta, self.vgVarRunout, self.retrVar, self.peckVar, self.rfrVar, self.pfrVar, self.pdVar, self.dzdxVar, self.finishVar, self.rghfrVar, self.finfrVar, self.zoneVar, 3) #pass the canvas, mode
        self.bMode = 1 #Run the resultant code when "RUN" button pressed
        print("Slicing Completed")
    def camSimulate(self):
        simulatorStatus = self.gProg.camSimulate(self.canvasFrame, self.canvPartingLimit, (self.zAxisCanvasLocation), (self.canvasStockZ), (self.zAxisCanvasLocation-((self.canvasStockX)/2)), self.canvScaleFact, self.xStockVar, self.zStockVar, self.vgVarWidth, self.vgVarRad, self.vgVarTheta, self.vgVarRunout, self.retrVar, self.peckVar, self.rfrVar, self.pfrVar, self.pdVar, self.dzdxVar, self.finishVar, self.rghfrVar, self.finfrVar, 3) #pass the canvas, mode
        if simulatorStatus == 0:
            self.root.after(150, self.camSimulate)  #25 very fast
            print("Simulating...")
        else:
            print("Exiting simulator")
        print("Simulation Complete")


    def sendGC(self):
        self.grblMan.sendGrblCommand(self.gCodeEntry.get())
        
    def feedInc(self): #See commands.md in grbl-master/doc/markdown
        #Increase feed override 10%, by issuing command to GRBL
        print("Increase feed rate 10%...")
        self.grblMan.sendGrblCommand(bytes([0x91]))
        self.FRP_Val += 10
        if self.FRP_Val >= 200:
            self.FRP_Val = 200 #GRBL Limits to 200% max. Note: We are constructing/mimicking GRBL internal value
        self.updateCanvasText()

    def feedDec(self): #See commands.md in grbl-master/doc/markdown
        #Decrease feed override 10%, by issuing command to GRBL
        print("Decrease feed rate 10%...")
        self.grblMan.sendGrblCommand(bytes([0x92]))
        self.FRP_Val -= 10
        if self.FRP_Val <= 10:
            self.FRP_Val = 10 #GRBL Limits to 10% min. Note: We are constructing/mimicking GRBL internal value
        self.updateCanvasText()
    
    def feedPgmd(self): #See commands.md in grbl-master/doc/markdown
        #Set 100% of programmed feed rate
        print("Decrease feed rate 10%...")
        self.grblMan.sendGrblCommand(bytes([0x90]))
        self.FRP_Val = 100
        self.updateCanvasText()
    
    def clearPartCount(self): #Clears the part counter
        print("Clearing part counter...")
        popSM.destroy()
        self.partCounter = 0
        self.updateCanvasText()

    ######## Private Methods ########
    def layoutUi(self):

        #Set up fonts
        text = tk.Text(self.root) #Create a font object
        labelFont = Font(family="Times New Roman", size=12, weight="bold")
        text.configure(font=labelFont)
        zxPosFont = Font(family="Times New Roman", size=12, weight="bold")
        text.configure(font=zxPosFont)
        
        
        
        
        
        #Set up frame scheme
        self.Controls = tk.Frame(self.root)

        self.FineControls = tk.LabelFrame(self.Controls, text="G-Code Program Viewer", padx=5, pady=5, bd=2, font=labelFont)
        self.LargeControls = tk.LabelFrame(self.Controls, text="Motion Controls", padx=5, pady=5, bd=2, font=labelFont)
        self.OptionsFrame = tk.LabelFrame(self.Controls, text="Options", padx=5, pady=5, bd=2, font=labelFont)
        self.Options2Frame = tk.LabelFrame(self.Controls, text="CAM Config", padx=5, pady=5, bd=2, font=labelFont)

        ##Fine Controls
        self.EditorFrame = tk.Frame(self.FineControls)
        self.CanvasFrame = tk.Frame(self.FineControls)
        self.SlicerFrame = tk.Frame(self.FineControls)
        self.GCodeFrame = tk.LabelFrame(self.FineControls)

        ##Large Controls
        self.MotionFrame = tk.Frame(self.LargeControls)


        #EditorFrame Widgets
        self.FileSelectButton = tk.Radiobutton(self.EditorFrame, text="BerylJob1.nc", width=11, height=2, variable=self.berylRadio, value=6, indicatoron=0, command=self.composeFileSelect)
        self.FileSelectButton.pack(side="left")
        self.settingsMenuButton = tk.Button(self.EditorFrame, text="Settings", width=7, height=1, pady=7, command=self.settingsMenu)
        self.settingsMenuButton.pack(side="left")
        #self.wizardsMenuButton = tk.Button(self.EditorFrame, text="Wizards", width=7, height=1, pady=7, command=self.wizardsMenu)
        #self.wizardsMenuButton.pack(side="left")


        #CanvasFrame Widgets
        self.canvasFrame = tk.Canvas(self.CanvasFrame, width=425, height=200, background="gray")
        self.canvasFrame.pack(anchor=W, side="top",fill="both", expand=True)

        #GCodeFrame Widgets
        self.gCodeTextBox = tk.Text(self.GCodeFrame, state='disabled', width=60, height=6, wrap='none')
        self.gCodeTextBox.pack(anchor=W, side="top", expand=True, fill='both')
        self.gCodeTextBox['state'] = 'normal'

        #Motion Controls Frame Widgets
        self.pgmRunButtStop = tk.Button(self.MotionFrame, width=10, height=4, text="Cycle Stop", bg="red", command=self.pgmStop)
        self.pgmRunButtStop.pack(side="top", expand=True)
        self.pgmRunButtPause = tk.Button(self.MotionFrame, width=10, height=3, text="Feed Hold", bg="yellow", command=self.pgmPause)
        self.pgmRunButtPause.pack(side="top", expand=True)
        self.pgmRunButtPlay = tk.Button(self.MotionFrame, width=10, height=3, text="Cycle Start", bg="green", command=self.pgmRun)
        self.pgmRunButtPlay.pack(side="top", expand=True)       
        self.gotoOrgButton = tk.Button(self.MotionFrame, text="Move to\nORIGIN", width=8, pady=2, font=zxPosFont, command=self.gotoOrg)
        self.gotoOrgButton.pack(anchor=W, side="top", expand=True, fill='both')
        
        self.moveXButton = tk.Radiobutton(self.MotionFrame, text="X-Pos:\n{:.4f}".format(self.moveXVar), width=8, pady=2, font=zxPosFont, variable=self.berylRadio, value=3, indicatoron=0, command=self.moveXValue)
        self.moveXButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.moveZButton = tk.Radiobutton(self.MotionFrame, text="Z-Pos:\n{:.4f}".format(self.moveZVar), width=8, pady=2, font=zxPosFont, variable=self.berylRadio, value=4, indicatoron=0, command=self.moveZValue)
        self.moveZButton.pack(anchor=W, side="top", expand=True, fill='both')

        #Options Frame Widgets
        self.resButton = tk.Radiobutton(self.OptionsFrame, text="MPG: {}".format(self.coarseVar), width=8, variable=self.berylRadio, value=5, indicatoron=0, command=self.coarseValue)
        self.resButton.pack(anchor=W, side="top", expand=True, fill='both')        
        #Feed Override Buttons
        self.feedPgmdButton = tk.Button(self.OptionsFrame, text="Feed 100%", width=8, command=self.feedPgmd) #Increase feed rate 10%
        self.feedPgmdButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.feedIncButton = tk.Button(self.OptionsFrame, text="Feed +10%", width=8, command=self.feedInc) #Increase feed rate 10%
        self.feedIncButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.feedDecButton = tk.Button(self.OptionsFrame, text="Feed -10%", width=8, command=self.feedDec) #Increase feed rate 10%
        self.feedDecButton.pack(anchor=W, side="top", expand=True, fill='both')
        #Uncomment for XZ Angle Lock Feature
        #self.angleButton =  tk.Radiobutton(self.OptionsFrame, text="Theta:{:.1f}".format(self.vgVarTheta), width=8, variable=self.berylRadio, value=17, indicatoron=0, command=self.angleValueSet)
        #self.angleButton.pack(anchor=W, side="top", expand=True, fill='both')
        #self.thetaLockZXButton = tk.Button(self.OptionsFrame, text="Theta Lock", width=8, command=self.thetaLockZX) #locks Z,X to move by theta
        #self.thetaLockZXButton.pack(anchor=W, side="top", expand=True, fill='both')
        self.zeroXZButton = tk.Button(self.OptionsFrame, text="Zero XZ", width=8, command=self.zeroXZ)
        self.zeroXZButton.pack(anchor=W, side="top", expand=True, fill='both')       
        self.zeroXButton = tk.Button(self.OptionsFrame, text="Zero X", width=8, command=self.zeroX)
        self.zeroXButton.pack(anchor=W, side="top", expand=True, fill='both')    
        self.zeroZButton = tk.Button(self.OptionsFrame, text="Zero Z", width=8, command=self.zeroZ)
        self.zeroZButton.pack(anchor=W, side="top", expand=True, fill='both')
        
        #Vertical Packs within fine and large control frames
        self.EditorFrame.pack(anchor=W)
        self.CanvasFrame.pack(anchor=W)
        self.GCodeFrame.pack(anchor=W)

        self.MotionFrame.pack(anchor=W, side="top", expand=True, fill='both')


        #Left/Right pack of fine controls vs/ Large buttons
        self.FineControls.pack(side="left", fill="both", expand=True)
        self.OptionsFrame.pack(side="left", fill="both", expand=True)
        self.LargeControls.pack(side="left", fill="both", expand=True)
        self.Controls.pack(side="top", fill="both", expand=True)

        #GCode Manual Entry Line (Single Line Sender to GRBL)
        self.gCodeMan = tk.Frame(self.root)

        self.gCodeManLabel = tk.Label(self.gCodeMan, text="Send Command:", relief="sunken")
        self.gCodeManLabel.pack(anchor=W, side="left", expand=False, fill='both')
        self.gCodeEntry = tk.Entry(self.gCodeMan)
        self.gCodeEntry.insert(0, "G20 G18")
        self.gCodeEntry.pack(anchor=W, side="left", expand=False, fill='both')
        self.gCodeButtSend = tk.Button(self.gCodeMan, text="SEND", command=self.sendGC)
        self.gCodeButtSend.pack(anchor=W, side="left", expand=False, fill='both')
        self.ttyGRBL = tk.Label(self.gCodeMan, text="/dev/ttyS0 (Hard-Coded)")
        self.ttyGRBL.pack(anchor=W, side="left", expand=False, fill='both')

        #Uncomment the following line for the G-Code sender line.
        #self.gCodeMan.pack(anchor=W, side="top", expand=True, fill='both')
