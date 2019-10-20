# Run command: sudo python3 /home/ludwigg/Python/MoveBall/moveBall.py
from graphics import *
import time
import math
import busio
import digitalio
import board
import adafruit_mcp3xxx.mcp3008 as MCP
from adafruit_mcp3xxx.analog_in import AnalogIn
import RPi.GPIO as GPIO # Raspberry Pi GPIO library
import random

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 640
BALL_RADIUS = 10
NUM_BALLS = 5
win = GraphWin("Dodge", SCREEN_WIDTH, SCREEN_HEIGHT, autoflush=False)
ballDiameter = BALL_RADIUS * 2
balls = []
velocities = []
message = Text(Point(100,100), "Dodge!")

play = True
reset = False

colors = ["Red",
          "Green",
          "Blue",
          "Purple",
          "Pink",
          "Yellow",
          "Orange",
          "Brown",
          "Gray"]

def GameReset():
	global reset
	global play
	
	for ball in balls:
		ball.undraw()
	
	balls.clear()
	velocities.clear()
	randomColors = random.sample(colors, NUM_BALLS)
	for i in range(NUM_BALLS):
		ball = Circle(Point(random.randint(ballDiameter, SCREEN_WIDTH - ballDiameter), random.randint(ballDiameter, SCREEN_HEIGHT - ballDiameter)), BALL_RADIUS)
		chosenColor = random.choice(randomColors)
		ball.setFill(chosenColor)
		randomColors.remove(chosenColor)
		velocity = [random.randint(-20, 21), random.randint(-20, 21)]
		balls.append(ball)
		velocities.append(velocity)
		
	# setup player ball
	ball = Circle(Point(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), BALL_RADIUS)
	ball.setFill("White")
	ballV = [0, 0]
	balls.append(ball)
	velocities.append(ballV)
	
	for ball in balls:
		ball.draw(win)
	
	message.setText("Move to begin!")
	message.setTextColor("white")
	message.setSize(20)
	
	play = True
	reset = False

def ResetButton(channel): 
	global reset
	
	if not play:
		reset = True

def main():
	global chan
	global chan2
	global zeroX
	global zeroY
	global play
	global reset
	
	win.setBackground(color_rgb(0, 0, 0))
	GameReset()
	message.draw(win)
	
	start = time.time()
	inPlay = False
	changed = False
	while(True):
		if not play:
			message.setText("Game Over!")
			if reset:
				GameReset()
		else:
			# moveX = -round(chan2.voltage/3.3 - zeroX, 1) * 30
			# moveY = round(chan.voltage/3.3 - zeroY, 1) * 30 # negative to orient joystick correctly
			moveY = -round(chan2.voltage/3.3 - zeroX, 1) * 30
			moveX = -round(chan.voltage/3.3 - zeroY, 1) * 30 # negative to orient joystick correctly
			# print("x: ", moveX)
			# print("y: ", moveY)
			if (moveX != 0 or moveY != 0) and not inPlay:
				inPlay = True
				message.setText("Dodge!")
				start = time.time()
			timePassed = round(time.time() - start, 2)
			if inPlay and timePassed > 2:
				message.setText(timePassed)
			velocities[NUM_BALLS][0] = moveX
			velocities[NUM_BALLS][1] = moveY
			changed = False

			for i in range(0, len(balls)):
				location = balls[i].getCenter()

				if location.x >= 480 - BALL_RADIUS:
					velocities[i][0] = -abs(velocities[i][0])
					changed = True
				elif location.x <= BALL_RADIUS:
					velocities[i][0] = abs(velocities[i][0])
					changed = True

				if location.y >= 640 - BALL_RADIUS:
					velocities[i][1] = -abs(velocities[i][1])
					changed = True
				elif location.y <= BALL_RADIUS:
					velocities[i][1] = abs(velocities[i][1])
					changed = True

				for j in range(i + 1, len(balls)):
					ball2Loct = balls[j].getCenter()
					if math.sqrt((ball2Loct.x - location.x)**2 + (ball2Loct.y - location.y)**2) <= (2 * BALL_RADIUS):
						if j == NUM_BALLS and inPlay:
							velocities[i][0] = -abs(velocities[i][0])
							velocities[i][1] = -abs(velocities[i][1])
							play = False
							inPlay = False
							message.setText("Game Over!")
						elif j != NUM_BALLS:
							temp = velocities[i][0]
							velocities[i][0] = velocities[j][0]
							velocities[j][0] = temp
							temp = velocities[i][1]
							velocities[i][1] = velocities[j][1]
							velocities[j][1] = temp

			for i in range(0, len(balls)):
				balls[i].move(velocities[i][0], velocities[i][1])
			
			update(30)
    #win.getMouse() # Pause to view result
	win.close()    # Close window when done
	
# Setup GPIO
GPIO.setwarnings(False) # Ignore warnings
GPIO.setmode(GPIO.BCM) # Use BCM Pin numbering
GPIO.setup(26, GPIO.IN)

GPIO.add_event_detect(26, GPIO.FALLING, callback=ResetButton, bouncetime=300)
	
# create the spi bus
spi = busio.SPI(clock=board.SCK, MISO=board.MISO, MOSI=board.MOSI)

# create the cs (chip select)
cs = digitalio.DigitalInOut(board.D5)

# create the mcp object
mcp = MCP.MCP3008(spi, cs)

# create an analog input channel on pin 0
chan = AnalogIn(mcp, MCP.P0)
chan2 = AnalogIn(mcp, MCP.P1)
zeroY = round(chan.voltage/3.3, 1)
zeroX = round(chan2.voltage/3.3, 1)
# print("zeroY: ", zeroY)
# print("zeroX: ", zeroX)

# print("x: ", (round(chan2.voltage/3.3, 1) - zeroX))
# print("y: ", (round(chan.voltage/3.3, 1) - zeroY))
try:
	main()

except KeyboardInterrupt: 
    # This code runs on a Keyboard Interrupt <CNTRL>+C
	print('\n\n' + 'Program exited on a Keyboard Interrupt' + '\n') 

except: 
    # This code runs on any error
	print('\n' + 'Errors occurred causing your program to exit' + '\n')

finally: 
    # This code runs on every exit and sets any used GPIO pins to input mode.
	GPIO.cleanup()