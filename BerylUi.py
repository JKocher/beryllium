######## Imports ########
from GrblManager import GrblManager
import Tkinter as tk
#from tkinter import
import time
import serial
import sys
import string


######## Class Definitions ########
class BerylUi:
    ######## Constants ########


    ######## Public Methods ########
    def __init__(self, grblManIn):
        if( not isinstance(grblManIn, GrblManager) ):
            raise ValueError('invalid grblManIn object passed')
        self.grblMan = grblManIn

        self.root = tk.Tk()  #root = blank window of Tkinter class
        self.root.title("Beryllium Lathe Controller - v0.0.1")

        self.layoutUi()

        #Variables
        grblSettings = "$$\r"
        testGCode = "G0 0.1 F1 \r"


    def start(self):
        self.root.mainloop()


    ######## UI Callback Methods #######
    def mpgX(self):
        print("Testing mpgX")

    def mpgZ(self):
        print("Testing mpgZ")

    def mpgFine(self):
        print("Testing mpgFine")

    def mpgMed(self):
        print("Testing mpgMed")

    def mpgCoarse(self):
        print("Testing mpgCoarse")

    def togUnits(self):
        print("Testing togUnits")

    def clearX(self):
        print("X axis zeroed")

    def clearZ(self):
        print("Z axis zeroed")

    def pgmStop(self):
        print("Testing pgmStop")

    def pgmPause(self):
        print("Testing pgmPause")

    def pgmPlay(self):
        print("Testing pgmPlay")

    def sendGC(self):
        self.grblMan.sendGrblCommand(self.gCodeEntry.get())


    ######## Private Methods ########
    def layoutUi(self):
        #MPG Control Banner Area ///////////// (Might be an extra unnecessary layer of frame defining here)
        self.mpgBanner = tk.Frame(self.root)
        self.mpgX = tk.Frame(self.mpgBanner)
        self.mpgZ = tk.Frame(self.mpgBanner)
        self.mpgFine = tk.Frame(self.mpgBanner)
        self.mpgMed = tk.Frame(self.mpgBanner)
        self.mpgCoarse = tk.Frame(self.mpgBanner)
        self.Units = tk.Frame(self.mpgBanner)

        self.mpgBannerButtMpgX = tk.Button(self.mpgX, width=9, height=5, text="MPG-X", command=self.mpgX)
        self.mpgBannerButtMpgX.pack()
        self.mpgBannerButtMpgZ = tk.Button(self.mpgZ, width=9, height=5, text="MPG-Z", command=self.mpgZ)
        self.mpgBannerButtMpgZ.pack()
        self.mpgBannerButtMpgFine = tk.Button(self.mpgFine, width=9, height=5, text="MPG-Fine", command=self.mpgFine)
        self.mpgBannerButtMpgFine.pack()
        self.mpgBannerButtMpgMed = tk.Button(self.mpgMed, width=9, height=5, text="MPG-Med", command=self.mpgMed)
        self.mpgBannerButtMpgMed.pack()
        self.mpgBannerButtMpgCoarse = tk.Button(self.mpgCoarse, width=9, height=5, text="MPG-Coarse", command=self.mpgCoarse)
        self.mpgBannerButtMpgCoarse.pack()
        self.mpgBannerButtMpgUnits = tk.Button(self.Units, width=9, height=5, text="Units", command=self.togUnits)
        self.mpgBannerButtMpgUnits.pack()

        self.mpgX.pack(side="left", fill="both", expand=True)
        self.mpgZ.pack(side="left", fill="both", expand=True)
        self.mpgFine.pack(side="left", fill="both", expand=True)
        self.mpgMed.pack(side="left", fill="both", expand=True)
        self.mpgCoarse.pack(side="left", fill="both", expand=True)
        self.Units.pack(side="left", fill="both", expand=True)

        #DRO Section ////////////////////
        self.dro = tk.Frame(self.root)
        self.droX = tk.Frame(self.dro)
        self.droZ = tk.Frame(self.dro)

            #Lathe Canvas area (Attached to DRO packs, first one)
        self.latheCanvasArea = tk.Canvas(self.dro, width=400, height=200, background="gray")
        self.latheCanvasArea.pack(side="left")

        self.droX.pack(side="top", fill="both", expand=True)
        self.droZ.pack(side="top", fill="both", expand=True)


        self.droButtX = tk.Button(self.droX, width=8, height=5, text="X=", command=self.clearX)
        self.droButtX.pack(side="left")
        self.droXLabel = tk.Label(self.droX, width=15, height=5, text="0.504", bg="white", relief="sunken")
        self.droXLabel.pack(side="left")


        self.droButtZ = tk.Button(self.droZ, width=8, height=5, text="Z=", command=self.clearZ)
        self.droButtZ.pack(side="left")
        self.droZLabel = tk.Label(self.droZ, width=15, height=5, text="0.999", bg="white", relief="sunken")
        self.droZLabel.pack(side="left")

        #Program Run Section //////////////
        self.pgmRun = tk.Frame(self.root)
        self.pgmRunStop = tk.Frame(self.pgmRun)
        self.pgmRunPause = tk.Frame(self.pgmRun)
        self.pgmRunPlay = tk.Frame(self.pgmRun)

        self.pgmRunStop.pack(side="top", fill="both", expand=True)
        self.pgmRunPause.pack(side="top", fill="both", expand=True)
        self.pgmRunPlay.pack(side="top", fill="both", expand=True)

        self.pgmRunButtStop = tk.Button(self.pgmRunStop, width=8, height=5, text="PGM STOP", bg="red", command=self.pgmStop)
        self.pgmRunButtStop.pack(side="left", expand=True)
        self.pgmRunButtPause = tk.Button(self.pgmRunPause, width=8, height=3, text="PGM PAUSE", bg="yellow", command=self.pgmPause)
        self.pgmRunButtPause.pack(side="left", expand=True)
        self.pgmRunButtPlay = tk.Button(self.pgmRunPlay, width=8, height=3, text="PGM PLAY", bg="green", command=self.pgmPlay)
        self.pgmRunButtPlay.pack(side="left", expand=True)


        #G-Code Canvas area packs
        self.gCodeCanvasArea = tk.Canvas(self.root, width=600, height=125, background="white")

        #GCode Manual Entry Line (Single Line Sender to GRBL)
        self.gCodeMan = tk.Frame(self.root)

        self.gCodeManLabel = tk.Label(self.gCodeMan, text="Send Command:", relief="sunken")
        self.gCodeManLabel.pack(side="left", expand=True)
        self.gCodeEntry = tk.Entry(self.gCodeMan)
        self.gCodeEntry.insert(0, "g0 x0.0 z0.0 f5")
        self.gCodeEntry.pack(side="left")
        self.gCodeButtSend = tk.Button(self.gCodeMan, text="SEND", command=self.sendGC)
        self.gCodeButtSend.pack(side="left")
        self.ttyGRBL = tk.Label(self.gCodeMan, text="/dev/ttyS0 (Hard-Coded)")
        self.ttyGRBL.pack(side="left")

        #Grand grid scheme here..
        self.mpgBanner.grid(row=0, sticky="w")
        #self.latheCanvasArea.grid(row=1, sticky="w")
        self.dro.grid(row=1, sticky="w")
        self.pgmRun.grid(row=1, column=1, sticky="w")
        self.gCodeCanvasArea.grid(row=2, sticky="w")
        self.gCodeMan.grid(row=3, sticky="w")

        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
