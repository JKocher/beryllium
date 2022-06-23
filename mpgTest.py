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

import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BOARD)
#GPIO.setmode(GPIO.BCM)
import time

#GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
#GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN)
GPIO.setup(18, GPIO.IN)
pulseCount = 0
countCW = 0
countCCW = 0
encoder_A = 0
encoder_A_Old = 0
encoder_B = 0
encoder_B_Old = 0

while True:
    encoder_A_Old = encoder_A
    encoder_B_Old = encoder_B
    encoder_A = GPIO.input(16)
    encoder_B = GPIO.input(18)

    if (encoder_A != encoder_A_Old) or (encoder_B != encoder_B_Old):
        if (encoder_A == 1 and encoder_B_Old == 0) or (encoder_A == 0 and encoder_B_Old == 1):
            #Clockwise rotation
            countCW += 1
            if(countCW > 3):
                countCW = 0
                #print("Clockwise")
                pulseCount += 1
                print(pulseCount)

        if (encoder_A == 1 and encoder_B_Old == 1) or (encoder_A == 0 and encoder_B_Old == 0):
            #Counter-clockwise rotation
            countCCW += 1
            if(countCCW > 3):
                countCCW = 0
                #print("Counter-Clockwise")
                pulseCount -= 1
                print(pulseCount)


##    if (stateA == False) or (stateB == False):
##        print("I saw a Zero!!")
    
    #time.sleep(0.250)
    #stateA = GPIO.input(16)
    #stateB = GPIO.input(18)

GPIO.cleanup()
