#!/usr/bin/python3

# This script is for interfacing with the EIGHTH REVISION prototype counter board (version 0.8).

# Parameters
counttime = 1 #Floating point number of seconds to count for (resolution determined by configuration flag; see pin assignments)
brightness = 100 #LED brightness from 0 to 100

# import and set up modules: 
import RPi.GPIO as GPIO
import spidev
from time import sleep
from datetime import datetime
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# set GPIO pins to be used:
GPIO.setup(17,GPIO.OUT) # Trigger
GPIO.setup(12,GPIO.IN) # Counter enable watcher
GPIO.setup(18,GPIO.OUT) # Global LED power control
GPIO.setup(25,GPIO.OUT) # Yellow user LED
GPIO.setup(27,GPIO.OUT) # Internal/External clock selector
GPIO.setup(21,GPIO.OUT) # Coincidence mode select
GPIO.setup(4,GPIO.OUT) # 1 second or 1/256 second resolution selector
spi0 = spidev.SpiDev() # SPI bus for channel 0
spi1 = spidev.SpiDev() # SPI bus for channel 1
spi0.open(0,0)
spi1.open(0,1)
spi0.max_speed_hz = 5000 # SPI bus speed can be 250 MHz divided by any even integer between 2 and 65536 inclusive.
spi1.max_speed_hz = 5000 # As of revision 0.8, the SPI ACT LED should still visibly flash even on very high bus speeds.

# define control instructions for counter IC:
conf = [0x88,0x00]
read = [0x60,0x00,0x00,0x00,0x00]
zero = [0x20]

#### Pin Assignments:
#
#### GPIO 12 - CNT_EN - Monitors the status of the clock output. Has a 1K resistor attached in series to prevent low-impedance mishaps.
#		 	
#### GPIO 17 - TRIG - Triggers clock cycle when set high for "any" length of time. If held high when the count cycle would
#		       normally end, the count will continue for another full cycle time without pausing.
#		       As much as one millisecond and as little as zero milliseconds may pass between the assertion of the trigger
#		       and the start of the count interval; this depends on the phase of the clock and is not normally predictable.
#
#### GPIO 18 - PWR LED PWR - If set high, indicator LEDs on the board will be enabled. If set low, they will be disabled.
#			   This pin can be used as a PWM output to adjust brightness as necessary.
#
#### GPIO 27 - INT/EXT - If set high, the internal clock will be bypassed and the counters will instead accept active-high
#			   timing control from the connector labeled "Ext. Timebase" on the PCB.
#
#### GPIO 04 - TIME RES - Selects counter clock resolution, either whole seconds (low) or 1/256 seconds (high). In either case, the timing 
#			   interval will be the time the trigger pin remains high, rounded up to the nearest whole interval. Using 1/256 mode 
#			   requires at least 1/256-second precision for the time the trigger pin is held high. 
#
#### GPIO 21 - COINCIDENCE MODE - Puts the board into coincidence mode if set high. This will make the counter of channel 0 receive the 
#			   AND of the two inputs, and the counter of channel 1 receive the OR of the two inputs. The INPUT ACT LEDs will follow what 
#			   the counters are receiving at all times, so their behavior will change when coincidence mode is enabled - in coincidence
#			   mode, a pulse at either input will cause the LED on channel 1 (OR) to flash, and a simultaneous pulse at both inputs will
#			   cause both LEDs (AND and OR) to flash.
#
#### GPIO 25 - USER LED - This pin controls a yellow LED (labeled USER on the PCB) which can be used for arbitrary purposes. 

GPIO.output(4,0) # 1-second mode
#GPIO.output(4,1) # 1/256-second mode
GPIO.output(27,0) # internal clock
GPIO.output(17,0) # Trigger low
GPIO.output(18,0) # LEDs off
GPIO.output(21,0) # Coincidence mode off
#GPIO.output(21,1) # Coincidence mode on
GPIO.output(25,1) # USER LED on

# PWM for indicator LEDs
# Note that PWM stops when the program exits, so this will make all LEDs turn off when the program is not running.
indpwm = GPIO.PWM(18,10000)
indpwm.start(brightness)

spi0.xfer2(conf)
spi1.xfer2(conf)

#logfile = open(datetime.now().strftime('%Y-%M-%d_%H:%m:%S')+'.txt','w')
n = 0
try:
	while True:
		n += 1		
		#input('>> ') # Wait for enter key to be pressed before each count. Comment for continuous counting.
		spi0.xfer2(zero)
		spi1.xfer2(zero)
		GPIO.output(17,1)
		sleep(counttime-(0.5/256))
		GPIO.output(17,0)
		sleep(0.01)
		while GPIO.input(12): sleep(0.001)
		sleep(0.01)
		readtime = datetime.now().strftime('%Y-%M-%d %H:%m:%S')
		countbytes0 = spi0.xfer2(read)
		countbytes1 = spi1.xfer2(read)
		count0 = countbytes0[-1]+countbytes0[-2]*256+countbytes0[-3]*65536+countbytes0[-4]*16777216
		count1 = countbytes1[-1]+countbytes1[-2]*256+countbytes1[-3]*65536+countbytes1[-4]*16777216
		print('1:: ',int(count0))
		print('2:: ',int(count1))
		if count0 == 0 and count1 == 0:
			GPIO.output(25,1) # USER LED signifies zero counts obtained - very basic error reporting
		else:
			GPIO.output(25,0)
		#logfile.write(readtime+' :: '+str(int(count))+'\n')
finally:
	#logfile.close()
	GPIO.output(17,0) # Ensure trigger is low
	GPIO.output(25,0) # USER LED off
	#GPIO.cleanup()
