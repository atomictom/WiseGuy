#!/usr/bin/python
# This file represents the ANN as it receives inputs from the simulation and does calculations depending on the input.

import threading
import time
import zmq

def receiving():
	msg = socket.recv()
	if msg == 'wall':
		socket.send('ACK')
		print "I'm doing something to avoid a wall"
	elif msg == 'enemy':
		socket.send('ACK')
		print "I'm doing something to avoid an enemy"
	else:
		socket.send('NACK')

	#continue with reading commands from the ANN.
	threading.Timer(1.0, receiving).start()

def main():
	# server for receiving input from simulation.
	context = zmq.Context()
	global socket
	socket = context.socket(zmq.REP)
	socket.bind('tcp://127.0.0.1:1235')

	# client for outputing the commands to the simulation
	context = zmq.Context()
	socketOutput = context.socket(zmq.REQ)
	socketOutput.connect('tcp://127.0.0.1:1234')

	threading.Timer(0.0, receiving).start()

	while True:
		print "This block represents computations while reading input from the simulation, to show non-blocking capabilities"

		#testing sending different commands to the simulation
		socketOutput.send('goUp')
		msg = socketOutput.recv()
		print msg

		socketOutput.send('goLeft')
		msg = socketOutput.recv()
		print msg

		socketOutput.send('goRight')
		msg = socketOutput.recv()
		print msg

		socketOutput.send('goDown')
		msg = socketOutput.recv()
		print msg

		time.sleep(1)

if __name__ == "__main__":
	main()
