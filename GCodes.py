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

import os
import time
import tkinter as tk
#Vector math items
import math
import numpy
#import scipy
from scipy import linalg
from scipy.interpolate import interp1d
#from matplotlib import pyplot


class gCodes: #Used for G-Code composer toolbar
    #Usage for instantiation of all BerylCNC G-Codes:
    # gc_G0 = gCodes(0,0,0,0,0,0,0)
    # gc_G1 = gCodes(0,1,0,0,0,0,0)
    # gc_G2 = gCodes(0,2,0,0,0,0,0)
    # gc_G3 = gCodes(0,3,0,0,0,0,0)
    # gc_G4 = gCodes(0,4,0,0,0,0,0)


    feedRapid = 10 #ipm
    feedCut = 5 #ipm

    def __init__(self, term0, term1, term2, term3, term4, term5, term6):
        self.term0 = term0 #Line number
        self.term1 = term1 #Gxx
        self.term2 = term2 #Xx.xxxx or x.xxxx if G4 dwell time
        self.term3 = term3 #Zz.zzzz or Ff.f
        self.term4 = term4 #Ii.iiii
        self.term5 = term5 #Kk.kkkk
        self.term6 = term6 #Ff.f

    def getGCString(self): #Returns a string of the composed G-Code line
        if self.term1 == 0: #G00 (should be able to override the feed rate from the default class variable by stuffing an instance variable)
            return 'N{} G{} X{} Z{} F{}'.format(self.term0, self.term1, self.term2, self.term3, gCodes.feedRapid)
        if self.term1 == 1: #G01
            return 'N{} G{} X{} Z{} F{}'.format(self.term0, self.term1, self.term2, self.term3, gCodes.feedCut)
        if self.term1 == 2: #G02
            return 'N{} G{} X{} Z{} I{} K{} F{}'.format(self.term0, self.term1, self.term2, self.term3, self.term4, self.term5, self.term6)
        if self.term1 == 3: #G03
            return 'N{} G{} X{} Z{} I{} K{} F{}'.format(self.term0, self.term1, self.term2, self.term3, self.term4, self.term5, self.term6)
        if self.term1 == 4: #G04
            return 'N{} G{} P{}'.format(self.term0, self.term1, self.term2)
        return 'Error: String Not Available'

    def getGCDict(self): #Returns a Dictionary of the composed G-Code Line
        if self.term1 == 0: #G00 (should be able to override the feed rate from the default class variable by stuffing an instance variable)
            return {'DESCRIPTION':'BERYL','N':self.term0, 'G':self.term1, 'X':self.term2, 'Z':self.term3, 'F':self.term6}
        if self.term1 == 1: #G01
            return {'DESCRIPTION':'BERYL','N':self.term0, 'G':self.term1, 'X':self.term2, 'Z':self.term3, 'F':self.term6}
        if self.term1 == 2: #G02
            return {'DESCRIPTION':'BERYL','N':self.term0, 'G':self.term1, 'X':self.term2, 'Z':self.term3, 'I':self.term4, 'K':self.term5, 'F':self.term6}
        if self.term1 == 3: #G03
            return {'DESCRIPTION':'BERYL','N':self.term0, 'G':self.term1, 'X':self.term2, 'Z':self.term3, 'I':self.term4, 'K':self.term5, 'F':self.term6}
        if self.term1 == 4: #G04
            return {'DESCRIPTION':'BERYL','N':self.term0, 'G':self.term1, 'P':self.term2}
        return 'Error: Dict Not Available'

    def getMaxRapids(self):
        return self.feedRapid
    def getMaxCuts(self):
        return self.feedCut

class gProgram:

    def __init__(self):
        self.filename = "Beryljob1.nc"
        self.berylConstellation = [] #List of Dicts. Used to draw and maintain the constellation of un-sliced G-Codes
        self.cbc = [] #Corrected Beryl Constellation
        self.zbc = [] #Zonal Beryl Constellation
        self.tqConstellation = [] #List of Dicts, "Tool Quadrant Constellation" Used to parse sections of other constellations and generate new G-Codes with G1, G2, G3
        self.ttoConstellation = [] #List of Dicts. Used to parse sections of other constellations and generate new G-Codes with G1, G2, G3
        self.berylResultant = [] #List of Dicts. Stores the resulting machining toolpath
        self.berylRunBool = 0
        self.berylHoldBool = 0
        self.berylStopBool = 0
        self.gLineNumber = 0 #use this to hold line numbers for execution of G-code
        self.grblBusy = 0 #keep track of how many commands we've sent
        self.gBuffer = 0 #track how many times we've sent an instruction if timeouts occur
        self.vgRunout = 0 #Limits the unsupported runout length of parts
        self.vgTheta = 0 #Angle relative to Z-axis used for slicing
        self.pplZ = 0 #Stores the Z value of the "parametric parting line"
        self.splZ = 0 #Stores the Z value of the slicer's parting line
        self.zZoneDec = 0 #Z-Length per finishing zone in inches
        self.nZones = 0 #Stores the number of finishing zones calculated from runout value
        self.zStock = 0
        self.xStock = 0
        self.approachV = 0.025 #Material approach value for the slicer (No Button Yet)
        self.finishV = 0 #Rough material thickness from radio button
        self.nCutsODinZ = 0 #Number of cuts from the OD toward the center of part along Z
        self.nCutsPerZoneZ = 0 #Used to create the mega array housing the slicer lines
        self.rghfrV = 0 #Roughing Feed Rate
        self.finfrV = 0 #Finishing Feed Rate
        self.retrV = 0 #Retract value
        self.peckV = 0 #Peck value
        self.rfrV = 0 #Retract feedrate
        self.pfrV = 0 #Peck feedrate
        self.safeX = 0 #Safe X position for slicer moves
        self.reallySafeX = 0 #More safe X position for slicer moves
        #gSaveFile('Beryljob.nc')
        # os.chdir('/home/pi/beryllium/Programs')
        # with open('Beryljob.nc', 'r') as f:
        #     pass
        # os.chdir('/home/pi/beryllium')
        self.animator = 0 #Use for persistent storage between tkinter and simulator stepping
        self.cursorOld = None
        self.cursorNew = None
        self.stepTimeCount = 0
        self.stepTimeCountMax = 0
        self.lineTimeS = 0
        self.simTimeS = 0
        self.payPerSec = 0.0347
        print("gProgram Initialized")

    def gOpenFile(self, fileName):
        self.fileName = fileName
        progDict = {} #dictionary for appending to berylConstellation
        # self.term0 = term0 #Line number
        # self.term1 = term1 #Gxx
        # self.term2 = term2 #Xx.xxxx or x.xxxx if G4 dwell time
        # self.term3 = term3 #Zz.zzzz or Ff.f
        # self.term4 = term4 #Ii.iiii
        # self.term5 = term5 #Kk.kkkk
        # self.term6 = term6 #Ff.f
        os.chdir('/home/pi/beryllium/Programs')
        #lCounter = 0
        del self.berylConstellation[:] #clear the list in preparation for successive selected files
        del self.berylResultant[:]
        #if len(self.berylConstellation) > 0:
        #    self.berylConstellation.clear() #clear the list in preparation for successive selected files
        #with open('Beryljob.nc', 'r') as f: #Read the file
        with open(fileName, 'r') as f: #Read the file
            for line in f:  #line returns a string
                searchCountComment = line.count('(')
                if searchCountComment >= 1: #If we see an open-parenthesis, the line shall be a comment. Note: Syntax valid only on single-line-as-block G-code architecture. JTK 11/14/21
                    continue   
                #res = [int(i) for i in test_string.split() if i.isdigit()]
                #[int(s) for s in str.split() if s.isdigit()]
                #s.replace(" ", "")
                fLine = line.replace(" ", "") #Format line.. strip any spaces from line
                searchPosN = fLine.find('N')
                searchValNStart = (searchPosN + 1)
                searchValNEnd = searchValNStart    #start at the same positon as the character
                for i in fLine[searchValNStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValNEnd += 1
                    else:
                        break
                searchPosG = fLine.find('G') #The coveted "G" code term in the string
                if searchPosG == -1:
                    print('No G-Key Found in String')
                searchValGStart = (searchPosG + 1)
                if searchValGStart == -1:
                    print('No G-Value Found in String')
                searchValGEnd = searchValGStart    #start at the same positon as the character
                for i in fLine[searchValGStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValGEnd += 1
                    else:
                        break
                searchPosX = fLine.find('X')
                searchValXStart = (searchPosX + 1)
                searchValXEnd = searchValXStart    #start at the same positon as the character
                for i in fLine[searchValXStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValXEnd += 1
                    else:
                        break
                searchPosZ = fLine.find('Z')
                searchValZStart = (searchPosZ + 1)
                searchValZEnd = searchValZStart    #start at the same positon as the character
                for i in fLine[searchValZStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValZEnd += 1
                    else:
                        break
                searchPosI = fLine.find('I')
                searchValIStart = (searchPosI + 1)
                searchValIEnd = searchValIStart    #start at the same positon as the character
                for i in fLine[searchValIStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValIEnd += 1
                    else:
                        break

                searchPosK = fLine.find('K')
                searchValKStart = (searchPosK + 1)
                searchValKEnd = searchValKStart    #start at the same positon as the character
                for i in fLine[searchValKStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValKEnd += 1
                    else:
                        break
                searchPosF = fLine.find('F')
                searchValFStart = (searchPosF + 1)
                searchValFEnd = searchValFStart    #start at the same positon as the character
                for i in fLine[searchValFStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValFEnd += 1
                    else:
                        break
                searchPosP = fLine.find('P')
                searchValPStart = (searchPosP + 1)
                searchValPEnd = searchValPStart    #start at the same positon as the character
                for i in fLine[searchValPStart:]:  #Parse char by char after start position until next letter
                    if i.isdigit() or i.find('.')!=-1 or i.find('-')!=-1:
                        searchValPEnd += 1
                    else:
                        break

                #self.berylConstellation.append(progDict)
                #searchPosBeryl = line.find('BERYL')
                searchCountBeryl = fLine.count('BERYL')
                searchCountBerylResultant = fLine.count('BERR')                            
                
                #if searchPosBeryl == 0:   #if line has BERYL starting at index 0.. it's a constellation element
                if searchCountBeryl == 1:   #if line contains 1 instance of BERYL.. it's a constellation element
                    
                    if int(fLine[searchValGStart]) == 0: #G00
                        #print('Found G0')
                        progDict = {'DESCRIPTION':'BERYL','N':fLine[searchValNStart:searchValNEnd], 'G':fLine[searchValGStart:searchValGEnd], 'X':fLine[searchValXStart:searchValXEnd], 'Z':fLine[searchValZStart:searchValZEnd], 'F':fLine[searchValFStart:searchValFEnd]}
                    if int(fLine[searchValGStart]) == 1: #G01
                        #print('Found G1')
                        progDict = {'DESCRIPTION':'BERYL','N':fLine[searchValNStart:searchValNEnd], 'G':fLine[searchValGStart:searchValGEnd], 'X':fLine[searchValXStart:searchValXEnd], 'Z':fLine[searchValZStart:searchValZEnd], 'F':fLine[searchValFStart:searchValFEnd]}
                    if int(fLine[searchValGStart]) == 2: #G02
                        #print('Found G2')
                        progDict = {'DESCRIPTION':'BERYL','N':fLine[searchValNStart:searchValNEnd], 'G':fLine[searchValGStart:searchValGEnd], 'X':fLine[searchValXStart:searchValXEnd], 'Z':fLine[searchValZStart:searchValZEnd], 'I':fLine[searchValIStart:searchValIEnd], 'K':fLine[searchValKStart:searchValKEnd], 'F':fLine[searchValFStart:searchValFEnd]}
                    if int(fLine[searchValGStart]) == 3: #G03
                        #print('Found G3')
                        progDict = {'DESCRIPTION':'BERYL','N':fLine[searchValNStart:searchValNEnd], 'G':fLine[searchValGStart:searchValGEnd], 'X':fLine[searchValXStart:searchValXEnd], 'Z':fLine[searchValZStart:searchValZEnd], 'I':fLine[searchValIStart:searchValIEnd], 'K':fLine[searchValKStart:searchValKEnd], 'F':fLine[searchValFStart:searchValFEnd]}
                    if int(fLine[searchValGStart]) == 4: #G04
                        #print('Found G4')
                        progDict = {'DESCRIPTION':'BERYL','N':fLine[searchValNStart:searchValNEnd], 'G':fLine[searchValGStart:searchValGEnd], 'P':fLine[searchValPStart:searchValPEnd]}
                    
                    self.berylConstellation.append(progDict)
                    #bConstellation.append(progDict)
                    #print(line + 'BERYL found using .count()')
                    #print(self.berylConstellation[lCounter])
                    #print(bConstellation[lCounter])
                    #print('progDict found: DESCRIPTION:{0[DESCRIPTION]} N:{0[N]} G:{0[G]}'.format(progDict))
                    

                
                elif searchCountBerylResultant == 1:   #if line contains 1 instance of BERR.. it's a slicer output element:                                       
                    break #To save time, we are avoiding parsing BERR lines since we re-create on Slice function.
                
                else:                                                    
                    print(fLine + 'BERYL not found using .count()')


        os.chdir('/home/pi/beryllium')
        print('~~~Opened file for reading~~~')
        print('Constellation (List of Dictionaries):')
        for lines in self.berylConstellation:
            print(lines, "\n")
        print('Resultant (List of Dictionaries):')
        for lines in self.berylResultant:
            print(lines, "\n")                                 
        #return(1) #Used to kill our progress bar
            
            

    def gSaveFile(self, fileName):
        self.fileName = fileName
        os.chdir('/home/pi/beryllium/Programs')
        with open('Beryljob.nc', 'w') as f: #Write over the file
            pass
        os.chdir('/home/pi/beryllium')

    def gDraw(self, bCanvas, windXmin, windYmin, windXmax, windYmax, scale, bMode): #Renders the canvas with berylConstellation and berylResulant
        #bMode 1 = Only draw berylConstellation
        #bMode 2 = Draw berylConstellation and berylResultant
        self.bCanvas = bCanvas
        self.bMode = bMode
        self.scale = scale
        self.windXmin = windXmin
        self.windXmax = windXmax
        self.windYmin = windYmin
        self.windYmax = windYmax
        #draw the bounding box
        self.bCanvas.create_rectangle(self.windXmin,self.windYmin,self.windXmax,self.windYmax, outline='RoyalBlue2', fill="")
        #self.bCanvas.create_rectangle(0,0,20,20, outline='gold', fill="")
        #translate to X-Z plane
        #Xcanvas to Z program origin
        self.zPO = self.windXmax/self.scale #Z Program Origin
        self.xPO = self.windYmin/self.scale #X Program Origin
        cSize = 0.01 #circle size
        xTermStart = 0
        zTermStart = 0
        xTermEnd = 0
        zTermEnd = 0
        iTerm = 0
        kTerm = 0
        convertedXStart = 0
        convertedZStart = 0
        convertedXEnd = 0
        convertedZEnd = 0
        sectors = 3
        G2G3_Render_Rez = 10

        #Render the berylConstellation
        for index, dict in enumerate(self.berylConstellation, start=0):
            if int(dict['G']) == 4: #G4 Dwell
                #continue  #exit this iteration of for: and continue on with for:
                return
            if 'X' in dict:  #if an X term exists in the dictionary
                xTermStart = xTermEnd #save the X term if it exists
                xTermEnd = float(dict['X'])
            else:
                xTermEnd = xTermStart #copy over the previous X term if a new one on this line not found
            if 'Z' in dict: #if a Z term exists in the dictionary
                zTermStart = zTermEnd #save the Z term if it exists
                zTermEnd = float(dict['Z'])
            else:
                zTermEnd = zTermStart #copy over the previous Z term if a new one on this line not found
            if int(dict['G']) == 0 or int(dict['G']) == 1: #if it's a line move
                self.plotG1(zTermStart, xTermStart, zTermEnd, xTermEnd, 'green')
            if int(dict['G']) == 3: #G3 CCW Arc
                #Render a G3 arc
                Iterm = float(dict['I'])
                Kterm = float(dict['K'])
                self.plotG3(zTermStart, xTermStart, zTermEnd, xTermEnd, Iterm, Kterm, G2G3_Render_Rez, 'green')                               
            if int(dict['G']) == 2: #G2 CW Arc
                #Render a G2 arc
                Iterm = float(dict['I'])
                Kterm = float(dict['K'])
                self.plotG2(zTermStart, xTermStart, zTermEnd, xTermEnd, Iterm, Kterm, G2G3_Render_Rez, 'green')      
        
    def plotLine(self, lineStartZDec, lineStartXDec, lineEndZDec, lineEndXDec, lineColor): #Converts and plots decimal inch line on canvas from GUI
        lsZ = lineStartZDec
        lsX = lineStartXDec
        leZ = lineEndZDec
        leX = lineEndXDec
        color = lineColor
        convertedlineStartZ = (self.zPO+lsZ)*self.scale #Converted for redering on canvas
        convertedlineStartX = (self.xPO-lsX)*self.scale  #Converted for redering on canvas
        convertedlineEndZ = (self.zPO+leZ)*self.scale     #Converted for redering on canvas
        convertedlineEndX = (self.xPO-leX)*self.scale      #Converted for redering on canvas
        self.bCanvas.create_line(convertedlineStartZ,convertedlineStartX,convertedlineEndZ,convertedlineEndX,fill=color)
        
    def plotG1(self, lineStartZDec, lineStartXDec, lineEndZDec, lineEndXDec, color): #Converts and plots G1, in inches (line) on canvas from GUI
        lsZ = lineStartZDec
        lsX = lineStartXDec
        leZ = lineEndZDec
        leX = lineEndXDec
        convertedlineStartZ = (self.zPO+lsZ)*self.scale #Converted for redering on canvas
        convertedlineStartX = (self.xPO-lsX)*self.scale  #Converted for redering on canvas
        convertedlineEndZ = (self.zPO+leZ)*self.scale     #Converted for redering on canvas
        convertedlineEndX = (self.xPO-leX)*self.scale      #Converted for redering on canvas
        self.bCanvas.create_line(convertedlineStartZ,convertedlineStartX,convertedlineEndZ,convertedlineEndX,fill=color)    

    def plotG2(self,tZStart,tXStart,tZEnd,tXEnd, tI, tK, numChords, color): #Converts and plots G3, in inches (arc) on canvas from GUI
        #Creates and plots an n x 2 matrix of Z, X pairs of points to build G-Codes off of 
        G2_Chords = numpy.zeros((numChords,2)) #Quantity (chords) rows x 2 columns for storage of chord points as Z,X pairs
        G2_Polars = numpy.zeros((numChords,2)) #Quantity (chords) rows x 2 columns for storage of point thetas as +/- degrees from G3 center
        G2_Chords[0,0] = tZStart #Z,X Pairs
        G2_Chords[0,1] = tXStart
        G2_Chords[(numChords-1),0] = tZEnd
        G2_Chords[(numChords-1),1] = tXEnd
        #G3_Center = numpy.array([[tI,tK]])
        Xs = tXStart
        Xe = tXEnd
        Zs = tZStart
        Ze = tZEnd
        CircI = tI #Use to calculate polar radius
        CircK = tK #Use to calculate polar radius   
        #Find the polar Radius values (Circular means all the same radius obvi)
        G2_Polars[:,0] = numpy.sqrt(CircI**2+CircK**2)    
        Xc = Xs+tI  #Circle Center X calculated from starting point and I,K terms
        Zc = Zs+tK  #Circle Center Z calculated from starting point and I,K terms   
        OTz = -Zc #Origin Transform x (Beryl Z) (for Arctan2 function to operate at 0,0)
        OTx = -Xc #Origin Transform y (Beryl X) (for Arctan2 function to operate at 0,0)
        G2_Center = numpy.array([[Zc,Xc]])
        G2_TCenter = numpy.array([[OTz,OTx]]) #Transformed center coordinate move values for troubleshooting
        #First calculate boundary angles from initial start and end points, circle center from G-code input transformed to origin using OT.
        Zbounds = numpy.array([(tZStart+OTz), (tZEnd+OTz)]) #Arctan2 will use these about the origin 0,0 
        Xbounds = numpy.array([(tXStart+OTx), (tXEnd+OTx)])
        Thetas = numpy.rad2deg(numpy.arctan2(Xbounds,Zbounds)) #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds) * 180 / numpy.pi  #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds)   #Arctan2 is critically important for dealing with the edge cases on quadrants
        #print("G2 Thetas:",Thetas,"\n")        
        #Break the arctan matrix into individual theta start and end values
        Theta_Start = Thetas[0] #Tested correct all cases G2. Note: Start and End indices reversed for G3
        if Theta_Start < 0:
            Theta_Start += 360
        if Theta_Start == 0:
            Theta_Start = 360 #G2 correction so we linspace CCW direction
        G2_Polars[0,1] = Theta_Start
        Theta_End = Thetas[1]  #Tested correct all cases G2. Note: Start and End indices reversed for G3
        if Theta_End < 0:
            Theta_End += 360
        G2_Polars[(numChords-1),1] = Theta_End
        Theta_Total = abs(Theta_End - Theta_Start)
        Chord_Theta = Theta_Total / numChords
        Chord_Iterations = numChords-1 
        #print("G2 Theta Start", Theta_Start,"\n")
        #print("G2 Theta End", Theta_End,"\n")                
        #Populate polar matrix with all sub-angles using LINSPACE for the win.
        G2_Polars[0:numChords,1] = numpy.linspace(Theta_Start,Theta_End,(numChords)) #See note above about if Theta_Start =0, changed -> 360 so we Linspace CCW
        #print("G2 Polars", G2_Polars,"\n")
        #Populate the Chords matrix (cartesian) with coordinate pairs in Z,X
        ##G3_Chords[:,0] = -OTz+(G3_Polars[:,0] * numpy.cos(G3_Polars[:,1]))
        ##G3_Chords[:,1] = -OTx+(G3_Polars[:,0] * numpy.sin(G3_Polars[:,1]))
        G2_Chords[:,0] = -OTz+(numpy.multiply(G2_Polars[:,0], numpy.cos(numpy.deg2rad(G2_Polars[:,1]))))    
        G2_Chords[:,1] = -OTx+(numpy.multiply(G2_Polars[:,0], numpy.sin(numpy.deg2rad(G2_Polars[:,1]))))    
        #return G3_Chords, G3_Polars, G3_Center, Thetas, Theta_Start, Theta_End, Theta_Total, Chord_Theta, G3_TCenter        
        #Render chords using plotLine
        #Plot the circle center for R&D
        #self.plotReticle1(Zc, Xc)
        #self.plotReticle2(Zs, Xs)
        leZ = G2_Chords[0,0]
        leX = G2_Chords[0,1]
        gradColor = 0x00FF00 #Gradient color
        length, width = G2_Chords.shape
        for line in range(length):
            lsZ = leZ
            lsX = leX
            leZ = G2_Chords[line,0]
            leX = G2_Chords[line,1]           
            self.plotLine(lsZ,lsX,leZ,leX,color)
            #gradColor += int(255/numChords)
            #self.plotLine(lsZ,lsX,leZ,leX,"#{0:06X}".format(gradColor))

    def plotG3(self,tZStart,tXStart,tZEnd,tXEnd, tI, tK, numChords, color): #Converts and plots G3, in inches (arc) on canvas from GUI
        #Creates and plots an n x 2 matrix of Z, X pairs of points to build G-Codes off of 
        G3_Chords = numpy.zeros((numChords,2)) #Quantity (chords) rows x 2 columns for storage of chord points as Z,X pairs
        G3_Polars = numpy.zeros((numChords,2)) #Quantity (chords) rows x 2 columns for storage of point thetas as +/- degrees from G3 center
        G3_Chords[0,0] = tZStart #Z,X Pairs
        G3_Chords[0,1] = tXStart
        G3_Chords[(numChords-1),0] = tZEnd
        G3_Chords[(numChords-1),1] = tXEnd
        #G3_Center = numpy.array([[tI,tK]])
        Xs = tXStart
        Xe = tXEnd
        Zs = tZStart
        Ze = tZEnd
        CircI = tI #Use to calculate polar radius
        CircK = tK #Use to calculate polar radius   
        #Find the polar Radius values (Circular means all the same radius obvi)
        G3_Polars[:,0] = numpy.sqrt(CircI**2+CircK**2)    
        Xc = Xs+tI  #Circle Center X calculated from starting point and I,K terms
        Zc = Zs+tK  #Circle Center Z calculated from starting point and I,K terms   
        OTz = -Zc #Origin Transform x (Beryl Z) (for Arctan2 function to operate at 0,0)
        OTx = -Xc #Origin Transform y (Beryl X) (for Arctan2 function to operate at 0,0)
        G3_Center = numpy.array([[Zc,Xc]])
        G3_TCenter = numpy.array([[OTz,OTx]]) #Transformed center coordinate move values for troubleshooting
        #First calculate boundary angles from initial start and end points, circle center from G-code input transformed to origin using OT.
        Zbounds = numpy.array([(tZStart+OTz), (tZEnd+OTz)]) #Arctan2 will use these about the origin 0,0 
        Xbounds = numpy.array([(tXStart+OTx), (tXEnd+OTx)])
        Thetas = numpy.rad2deg(numpy.arctan2(Xbounds,Zbounds)) #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds) * 180 / numpy.pi  #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds)   #Arctan2 is critically important for dealing with the edge cases on quadrants
        #print("G3 Thetas:",Thetas,"\n")        
        #Break the arctan matrix into individual theta start and end values        
        Theta_Start = Thetas[0] #Tested correct all cases G3
        if Theta_Start < 0:
            Theta_Start += 360
        G3_Polars[0,1] = Theta_Start
        Theta_End = Thetas[1]  #Tested correct all cases G3
        if Theta_End < 0:
            Theta_End += 360
        G3_Polars[(numChords-1),1] = Theta_End
        Theta_Total = abs(Theta_End - Theta_Start)
        Chord_Theta = Theta_Total / numChords
        Chord_Iterations = numChords-1
        #print("G3 Theta Start", Theta_Start,"\n")
        #print("G3 Theta End", Theta_End,"\n")                
        #Populate polar matrix with all sub-angles using LINSPACE for the win.
        G3_Polars[0:numChords,1] = numpy.linspace(Theta_Start,Theta_End,(numChords))  
        #Populate the Chords matrix (cartesian) with coordinate pairs in Z,X
        ##G3_Chords[:,0] = -OTz+(G3_Polars[:,0] * numpy.cos(G3_Polars[:,1]))
        ##G3_Chords[:,1] = -OTx+(G3_Polars[:,0] * numpy.sin(G3_Polars[:,1]))
        G3_Chords[:,0] = -OTz+(numpy.multiply(G3_Polars[:,0], numpy.cos(numpy.deg2rad(G3_Polars[:,1]))))
        G3_Chords[:,1] = -OTx+(numpy.multiply(G3_Polars[:,0], numpy.sin(numpy.deg2rad(G3_Polars[:,1]))))    
        #return G3_Chords, G3_Polars, G3_Center, Thetas, Theta_Start, Theta_End, Theta_Total, Chord_Theta, G3_TCenter        
        #Render chords using plotLine
        #Plot the circle center for R&D
        #self.plotReticle1(Zc, Xc)
        #self.plotReticle2(Zs, Xs)
        leZ = G3_Chords[0,0]
        leX = G3_Chords[0,1]
        gradColor = 0x00FF00 #Gradient color
        length, width = G3_Chords.shape        
        for line in range (length):
            lsZ = leZ
            lsX = leX
            leZ = G3_Chords[line,0]
            leX = G3_Chords[line,1]           
            self.plotLine(lsZ,lsX,leZ,leX,color)
            #gradColor += int(255/numChords)
            #self.plotLine(lsZ,lsX,leZ,leX,"#{0:06X}".format(gradColor))
    
    def gRUN(self, gMan, bMode):
        #rMode 0 = Run berylConstellation
        #rMode 1 = Run berylResultant
        print("Execute gRUN")
        #start = time.clock()
        self.gMan = gMan #GRBL Manager passed in
        runMode = bMode
        #self.berylRUNbool = 1 #Don't indicate we're running unless we've been triggered with the "initiate" flag
        #self.initiate = initiate #(initate == 1) => Start, (initate == 0) => normal program flow
        self.gMan.sendGrblCommand('G20 G18')

        if runMode == 0:
            gCodeLinestoRun = self.berylConstellation
        elif runMode == 1:
            gCodeLinestoRun = self.berylResultant
        else:
            print("runMode error within gRUN")
        
        self.gMan.createNewJob()
        for index, dict in enumerate(gCodeLinestoRun, start=0): #Send all commands to Gerbil module - it will queue everything up and manage
            #index = self.gLineNumber                
            dict = gCodeLinestoRun[index]
            #Note: formats have to be fixed for latest Python. Shop test choked on ":.4f"
            if int(dict['G']) == 0: #if G0
                gCode_String = 'N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(gCodeLinestoRun[index])
                #gCode_String = 'G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(gCodeLinestoRun[index]) #Without sending line number
            if int(dict['G']) == 1: #if G1
                gCode_String = 'N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(gCodeLinestoRun[index]) 
                #gCode_String = 'G{0[G]} X{0[X]} Z{0[Z]} F{0[F]}'.format(gCodeLinestoRun[index]) #Without sending line number
            if int(dict['G']) == 2: #if G2 CW Arc
                gCode_String = 'N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(gCodeLinestoRun[index])
                #gCode_String = 'G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(gCodeLinestoRun[index]) #Without sending line number
            if int(dict['G']) == 3: #if G3 CCW Arc
                gCode_String = 'N{0[N]} G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(gCodeLinestoRun[index])
                #gCode_String = 'G{0[G]} X{0[X]} Z{0[Z]} I{0[I]} K{0[K]} F{0[F]}'.format(gCodeLinestoRun[index]) #Without sending line number
            if int(dict['G']) == 4: #if G4
                gCode_String = 'N{0[N]} G{0[G]} P{0[P]}'.format(gCodeLinestoRun[index])
                #gCode_String = 'G{0[G]} P{0[P]}'.format(gCodeLinestoRun[index])  #Without sending line number
            print("Beryllium sending string: {}\n".format(gCode_String))
            self.gMan.appendLineToCurrentJob(gCode_String)
            #time.sleep(0.1)
        self.gMan.startCurrentJob()
        
    print('Gerbil Job Started')


    def gHOLD(self):
        #rMode 1 = Run berylConstellation
        #rMode 2 = Run berylResultant
        if self.berylHoldBool:
            self.gMan.resume()
            self.berylHoldBool = 0
            print("Executing gResume")
        else:
            self.gMan.hold()
            self.berylHoldBool = 1
            print("Executing gHOLD")


    def gSTOP(self):
        #rMode 1 = Run berylConstellation
        #rMode 2 = Run berylResultant
        self.gMan.haltCurrentJob()
        self.berylRUNbool = 0
        self.berylHoldBool= 0
        self.berylStopBool= 0
        self.gLineNumber = 0
        print("Executing gSTOP")
    
        
    def G3_To_Chords(self,tXStart,tZStart,tXEnd,tZEnd,tI,tK,Chords): #t stands for "term" for now; I = X offset to center, K = Z offset to center, Chords = # of Chords
        #Outputs a n x 2 matrix of Z, X pairs of points to build G-Codes off of 
        G3_Chords = numpy.zeros((Chords,2)) #Quantity (chords) rows x 2 columns for storage of chord points as Z,X pairs
        G3_Polars = numpy.zeros((Chords,2)) #Quantity (chords) rows x 2 columns for storage of point thetas as +/- degrees from G3 center
        G3_Chords[0,0] = tZStart #Z,X Pairs
        G3_Chords[0,1] = tXStart
        G3_Chords[(Chords-1),0] = tZEnd
        G3_Chords[(Chords-1),1] = tXEnd
        #G3_Center = numpy.array([[tI,tK]])
        Xs = tXStart
        Xe = tXEnd
        Zs = tZStart
        Ze = tZEnd
        CircI = tI #Use to calculate polar radius
        CircK = tK #Use to calculate polar radius
    
        #Find the polar Radius values (Circular means all the same radius obvi)
        G3_Polars[:,0] = numpy.sqrt(CircI**2+CircK**2)
    
        Xc = Xs+tI  #Circle Center X calculated from starting point and I,K terms
        Zc = Zs+tK  #Circle Center Z calculated from starting point and I,K terms
    
        OTz = -Zc #Origin Transform x (Beryl Z) (for Arctan2 function to operate at 0,0)
        OTx = -Xc #Origin Transform y (Beryl X) (for Arctan2 function to operate at 0,0)
        G3_Center = numpy.array([[Zc,Xc]])
        G3_TCenter = numpy.array([[OTz,OTx]]) #Transformed center coordinate move values for troubleshooting

        #First calculate boundary angles from initial start and end points, circle center from G-code input transformed to origin using OT.
        Zbounds = numpy.array([-(tZStart+OTz), -(tZEnd+OTz)]) #Arctan2 will use these about the origin 0,0 
        Xbounds = numpy.array([(tXStart+OTx), (tXEnd+OTx)])
        Thetas = numpy.rad2deg(numpy.arctan2(Xbounds,Zbounds)) #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds) * 180 / numpy.pi  #Arctan2 is critically important for dealing with the edge cases on quadrants
        #Thetas = numpy.arctan2(Zbounds,Xbounds)   #Arctan2 is critically important for dealing with the edge cases on quadrants
    
        #Break the arctan matrix into individual theta start and end values
        Theta_Start = 180-Thetas[0] #Tested correct all cases G3
        G3_Polars[0,1] = Theta_Start
        Theta_End = 180-Thetas[1]  #Tested correct all cases G3
        if Theta_End == 0:
            Theta_End = 360 #Resolve the 180->360 south CCW arc problem JTK 5/19/20
        G3_Polars[(Chords-1),1] = Theta_End
        Theta_Total = abs(Theta_End - Theta_Start)
        Chord_Theta = Theta_Total / Chords
        Chord_Iterations = Chords-1
    
        #Populate polar matrix with all sub-angles using LINSPACE for the win.
        G3_Polars[0:Chords,1] = numpy.linspace(Theta_Start,Theta_End,(Chords))
    
        #Populate the Chords matrix (cartesian) with coordinate pairs in Z,X
        ##G3_Chords[:,0] = -OTz+(G3_Polars[:,0] * numpy.cos(G3_Polars[:,1]))
        ##G3_Chords[:,1] = -OTx+(G3_Polars[:,0] * numpy.sin(G3_Polars[:,1]))
        G3_Chords[:,0] = -OTz+(numpy.multiply(G3_Polars[:,0], numpy.cos(numpy.deg2rad(G3_Polars[:,1]))))
        G3_Chords[:,1] = -OTx+(numpy.multiply(G3_Polars[:,0], numpy.sin(numpy.deg2rad(G3_Polars[:,1]))))
    
        return G3_Chords, G3_Polars, G3_Center, Thetas, Theta_Start, Theta_End, Theta_Total, Chord_Theta, G3_TCenter
    
    
