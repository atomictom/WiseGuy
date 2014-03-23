#!/usr/bin/python

#This file represents the simulation as it receives commands from the ANN and executes an action depending on the command.

import threading
import time
import zmq

def receiving():
	msg = socket.recv()
	if msg == 'goUp':
		socket.send('ACK')
		print "I'm going up"
	elif msg == 'goDown':
		socket.send('ACK')
		print "I'm going Down"
	elif msg == 'goLeft':
		socket.send('ACK')
		print "I'm going Left"
	elif msg == 'goRight':
		socket.send('ACK')
		print "I'm going Right"
	else:
		socket.send('NACK')

	#continue with reading commands from the ANN.
	threading.Timer(1.0, receiving).start()


def main():
	# server for receiving commands from the ANN
	context = zmq.Context()
	global socket
	socket = context.socket(zmq.REP)
	socket.bind('tcp://127.0.0.1:1234')

	# client for outputing the input values to the ANN
	context = zmq.Context()
	socketOutput = context.socket(zmq.REQ)
	socketOutput.connect('tcp://127.0.0.1:1235')

	threading.Timer(0.0, receiving).start()

	while True:

		print "This block represents computations while reading input from the ANN, to show non-blocking capabilities"

		#testing sending different commands to the simulation
		socketOutput.send('wall')
		msg = socketOutput.recv()
		print msg

		socketOutput.send('enemy')
		msg = socketOutput.recv()
		print msg

		time.sleep(1)


if __name__ == "__main__":
	main()
