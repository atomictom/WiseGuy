#!/usr/bin/python
# This file represents the ANN as it receives inputs from the simulation and does calculations depending on the input.

import threading
import time
import zmq

def connection(socket):
	while True:
		msg = socket.recv()
		print msg

		socket.send('ANN')
		time.sleep(1)


def main():
	context = zmq.Context()
	socket = context.socket(zmq.REP)
	socket.bind('tcp://127.0.0.1:1235')
	socket.connect('tcp://127.0.0.1:1234')

	threading.Thread(target=connection, args=(socket,)).start()

if __name__ == "__main__":
	main()
