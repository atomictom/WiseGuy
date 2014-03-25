#!/usr/bin/python

# Simulation for Neural Network

import math
import pygame
import pygame.draw
import random

import threading
import time
import zmq
import pickle

from pygame.locals import *

# Notes:
# 	Currently there are no hazards, enemies are static, and walls and enemies are
# 	statically placed.

# TODO:
# High Priority:
# 	* [X] Replace tiles with walls (rectangles that can be anywhere and are impassable)
# 	* [X] Manually place walls and hazards
# Low Priority:
# 	* [ ] Rewrite the draw methods to use actual images (for enemies, player, hazards, and goal)
# 	* [ ] Consider using Sprite class as a base for the GameObject class

# For Matt and Diego:
# 	* [X] Implement the notify() method of the Player class to receive commands (from sockets), commands can be "turn left", "turn right", "forward", "stop" for now
# 	* [X] Implement the update() method of the Player class to act on command received from notify()
# 	* [X] Enemies need to move (write the 'update' function on the Enemy class)
# 	* [ ] Add controls to modify the environment/sim while the ANN is running (add/rm walls? add/rm enemies?)
# 	* [ ] Integrate socket code

# For Diego:
# 	* [X] Add socket code to connect to the ANN

# For Thomas:
# 	* [X] Consider alternative to add_objects() and super method draw/update -- I added a 'parent' parameter and a 'register' method
# 	* [ ] Collision detection on walls + enemies + player
# 	* [ ] Add feelers (wall/obstacle sensors) and radar (enemy sensor) to Player

# Walls and enemy locations are hardcoded here for predictability
WALLS = [
	[(50, 30), (25, 100)],
	[(120, 250), (200, 50)],
]

ENEMIES = [
	(200, 600),
	(80, 400),
	(500, 100),
]

PLAYER_START = (350, 350)

class Color(pygame.Color):
	white = pygame.Color(255, 255, 255)
	red = pygame.color.Color(255, 0, 0)
	yellow = pygame.color.Color(255, 255, 0)
	green = pygame.color.Color(0, 255, 0)
	blue = pygame.color.Color(0, 0, 255)
	black = pygame.color.Color(0, 0, 0)

class GameObject(object):

	def __init__(self, parent, position=(0, 0), dimension=(0, 0)):
		self.parent = parent
		self.objects = []
		if parent:
			parent.register(self)

		self._rect = pygame.Rect(position, dimension)

	def register(self, obj):
		self.objects.append(obj)

	def update(self):
		for obj in self.objects:
			obj.update()

	def draw(self, surface):
		for obj in self.objects:
			obj.draw(surface)

	def notify(self, *args, **kwargs):
		print args
		print kwargs

	@property
	def rect(self):
		return self._rect

	@rect.setter
	def rect(self, value):
		self._rect = value

class Enemy(GameObject):

	speed = 1.5

	def __init__(self, parent, position, radius=10):
		super(Enemy, self).__init__(parent, position, (2 * radius, 2 * radius))
		self.radius = radius
		self.game_map = parent
		self.speed = Enemy.speed

	def draw(self, surface):
		pygame.draw.circle(surface, Color.red, self.rect.topleft, self.radius)

	def update(self):
		screen_width = self.parent.rect.width
		self.rect.centerx = (self.rect.centerx + self.speed) % screen_width

class StaticEnemy(Enemy):

	def update(self):
		pass

class Player(GameObject):

	def __init__(self, parent, position, radius=10):
		super(Player, self).__init__(parent, position, dimension=(2 * radius, 2 * radius))
		self.radius = radius

		self.turn_right = False
		self.turn_left = False
		self.move_forward = False

		self.x, self.y = position
		self.speed = 2
		self.rotation_speed = .06
		# Start facing to the top of the screen. 0 degrees points to the right
		self.theta = math.pi

	def draw(self, surface):
		# When this is changed to use an image instead of a circle, rotate the image
		pygame.draw.circle(surface, Color.blue, self.rect.center, self.radius)
		pygame.draw.rect(surface, Color.yellow, self.rect)

	def update(self):

		# Might need to track x and y seperately from self.rect since it might
		# truncate values to integers, in which case two movements of 1.5 will
		# only go 2 units, not 3.
		if self.move_forward:
			self.go_forward()

		if self.turn_left:
			print 'Left'
			self.theta -= self.rotation_speed % (2 * math.pi)

		if self.turn_right:
			print 'Right'
			self.theta += self.rotation_speed % (2 * math.pi)

	def go_forward(self):
		print 'Forward'
		# Save the original position in case we collide and need to revert
		original_position = (self.x, self.y)

		# self.x and self.y are floats, self.rect.x and self.rect.y are ints
		# so we update them separately to avoid loss of precision
		self.x += self.speed * math.cos(self.theta)
		self.y += self.speed * math.sin(self.theta)

		# If there is a collision, move back to the original position (disallow it)
		if self.rect.collidelist(self.parent.walls) != -1:
			print "Collision!"
			self.x, self.y = original_position

		# Apply the position updates to the Player's rect
		self.rect.x = self.x
		self.rect.y = self.y

	#Function for computing the output that will go to the ANN
	def get_info(self):
		pass

	# Use this for moving the player
	def notify(self, command, state=True):
		if command == 'move_forward':
			self.move_forward = state
			print "go forward = " + str(state)
		elif command == 'turn_left':
			self.turn_left = state
			print "turn left = " + str(state)
		elif command == 'turn_right':
			self.turn_right = state
			print "turn right = " + str(state)
		else:
			print "Invalid command (this shouldn't happen!)"


class Wall(GameObject):
	""" Wall represents an impassable object that the player or enemies must navigate around

		Parameters:
			position -> the upper left corner of the wall's rectangle as a tuple
			dimension -> the width and height of the rectangle as a tuple
	"""

	def __init__(self, parent, position, dimension):
		super(Wall, self).__init__(parent, position, dimension)

	def draw(self, surface):
		wall_surface = surface.subsurface(self.rect)
		wall_surface.fill(Color.black)

class Map(GameObject):

	def __init__(self, width, height):
		super(Map, self).__init__(None, dimension=(width, height))

		self.width = width
		self.height = height

		# Create the walls, enemies, and player
		self.walls = self.create_walls()
		self.enemies = self.create_enemies()
		self.player = Player(self, PLAYER_START)

	def create_walls(self):
		walls = []
		for pos, dim in WALLS:
			new_wall = Wall(self, pos, dim)
			walls.append(new_wall)

		return walls

	def create_enemies(self):
		enemies = []
		for pos in ENEMIES:
			new_enemy = StaticEnemy(self, pos)
			enemies.append(new_enemy)

		return enemies

	def draw(self, surface):
		surface.fill(Color.white)
		super(Map, self).draw(surface)

class Simulation(object):

	def __init__(self):
		self.running = True
		# 64 * 13, 64 * 10, so the images can be powers of 2 and easy to scale
		self.resolution = (832, 640)
		self.title = 'Simulation'
		self.framerate = 60
		self.clock = pygame.time.Clock()

		self.game_map = Map(*self.resolution)

		# create the server and the client for communication with ANN.
		# server for receiving commands from the ANN
		context = zmq.Context()
		self.socket = context.socket(zmq.REQ)
		self.socket.bind('tcp://127.0.0.1:1234')
		self.socket.connect('tcp://127.0.0.1:1235')

		threading.Thread(target=connection, args=[self.socket, self.game_map.player]).start()

	def quit(self):
		self.running = false

	def keytoggle(self, key, state):
		if key == K_q:
			self.running = False
		if key == K_UP:
			self.game_map.player.notify("move_forward", state)
		if key == K_LEFT:
			self.game_map.player.notify("turn_left", state)
		if key == K_RIGHT:
			self.game_map.player.notify("turn_right", state)

	def check_input(self, events):
		for event in events:
			if event.type == QUIT:
				self.running = False
			elif event.type == KEYDOWN:
				self.keytoggle(event.key, True)
			elif event.type == KEYUP:
				self.keytoggle(event.key, False)

	def update(self):
		self.game_map.update()

	def draw(self, window):
		self.game_map.draw(window)

	def mainloop(self, window):
		while self.running:
			time = self.clock.tick(self.framerate)

			self.check_input(pygame.event.get())
			self.update()
			self.draw(window)

			pygame.display.flip()
			pygame.event.pump()

		self.socket.close()

def drawText(surface, msg, location = (0,0), size = 20, color = Color.white):
	font = pygame.font.Font(None, size)
	msgsurface = font.render(msg, False, color)
	rect = msgsurface.get_rect()
	rect.topleft = location
	surface.blit(msgsurface, rect)
	return rect

def connection(socket, player):
	while True:

		#send output to ANN.
		output_list = player.get_info()
		output_string = pickle.dumps(output_list)
		socket.send(output_string)

		#receive reply from ANN
		msg = socket.recv()
		list_message = pickle.loads(msg)
		if list_message:

			#position 1 will be turn right
			turn_right = list_message[0]
			if turn_right:
				player.notify('turn_right')

			#position 2 will be turn left
			turn_left = list_message[1]
			if turn_left:
				player.notify('turn_left')

			#position 3 will be move forward
			move_forward = list_message[2]
			if move_forward:
				player.notify('move_forward')
		else:
			print "Invalid commands"


def main():
	sim = Simulation()

	pygame.init()
	pygame.display.set_mode(sim.resolution)
	pygame.display.set_caption(sim.title)

	window = pygame.display.get_surface()
	sim.mainloop(window)

if __name__ == "__main__":
	main()
