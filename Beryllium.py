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

from GrblManager import GrblManager
from BerylUi import BerylUi
from mpg import BerylMPG
import time


######## Main Script Execution ########
# setup our GRBL Manager
grblMan = GrblManager()
berylMPG = BerylMPG()

#setup MPG wheel
#bMPG = BerylMPG()

# for debugging only
print("Listing serial ports...")
ports = grblMan.listSerialPorts()
print (', '.join(map(str, ports)))
print("\nChanging serial ports...")
grblMan.changeSerialPort(ports[1])

# setup our UI
berylUi = BerylUi(grblMan, berylMPG)

# start everything
grblMan.start()
berylMPG.start()  #might need to be here to pass into berylUI
berylUi.start()

#
#print("\nSending grbl command...")
#grblMan.sendGrblCommand("g0 x0.0 z0.0 f5")

while(True):
    time.sleep(0)
