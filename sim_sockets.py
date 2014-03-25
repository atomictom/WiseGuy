#!/usr/bin/python

#This file represents the simulation as it receives commands from the ANN and executes an action depending on the command.

import threading
import time
import zmq

def connection(socket):
	while True:
		socket.send('Simulation')

		msg = socket.recv()
		print msg
		time.sleep(1)


def main():
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.bind('tcp://127.0.0.1:1234')
	socket.connect('tcp://127.0.0.1:1235')

	threading.Thread(target=connection, args=(socket,)).start()

if __name__ == "__main__":
	main()
