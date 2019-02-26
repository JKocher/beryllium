from GrblManager import GrblManager
from BerylUi import BerylUi
import time


######## Main Script Execution ########
# setup our GRBL Manager
grblMan = GrblManager()

# for debugging only
print("Listing serial ports...")
ports = grblMan.listSerialPorts()
print ', '.join(map(str, ports))
print("\nChanging serial ports...")
grblMan.changeSerialPort(ports[1])

# setup our UI
#berylUi = BerylUi(grblMan)

# start everything
grblMan.start()
#berylUi.start()


#
# print("\nSending grbl command...")
# grblMan.sendGrblCommand("g0 x0.0 z0.0 f5")

while(True):
    time.sleep(0)
