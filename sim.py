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
# 	* [X] Integrate socket code

# For Diego:
# 	* [X] Add socket code to connect to the ANN

# For Thomas:
# 	* [X] Consider alternative to add_objects() and super method draw/update -- I added a 'parent' parameter and a 'register' method
# 	* [ ] Collision detection on walls + enemies + player -- partially done
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

	def __init__(self, parent, position=(0, 0), dimension=(0, 0), *args, **kwargs):
		super(GameObject, self).__init__(*args, **kwargs)

		self.parent = parent
		self.objects = []
		if parent:
			parent.register(self)

		self._rect = pygame.Rect(position, dimension)
		self.entered = False
		self.pressed = False

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

	# Matt: You should override this
	def mouse_click(self, pos):
		""" A hook to override to provide behavior to clicks """
		print "Clicked at: " + str(pos)

	def mouse_down(self, pos, button):
		""" Called on an element if a mouse button has been pressed over it """
		self.pressed = self.rect.collidepoint(pos)

		# Bubble the click updown to any descendants who may have also been clicked
		for obj in self.objects:
			obj.mouse_down(pos, button)

	def mouse_up(self, pos, button):
		""" Called on an element if it has been clicked """

		if self.rect.collidepoint(pos) and self.pressed:
			self.mouse_click(pos)

		self.pressed = False
		# Bubble the click down to any descendants who may have also been clicked
		for obj in self.objects:
			obj.mouse_up(pos, button)

	def mouse_enter(self):
		""" Called when the mouse enters an element's rect """
		self.entered = True

	def mouse_exit(self):
		""" Called when the mouse exits an element's rect """
		self.entered = False

	def mouse_move(self, pos, rel, buttons):
		""" 	Called on an element whenever the mouse moves (even if not over it) """
		# Bubble the click down to any descendants who may have also been clicked
		if self.rect.collidepoint(pos) and not self.entered:
			self.mouse_enter()
		if self.entered and not self.rect.collidepoint(pos):
			self.mouse_exit()

		for obj in self.objects:
			obj.mouse_move(pos, rel, buttons)

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
		# pygame.draw.rect(surface, Color.yellow, self.rect)

	def update(self):

		if self.move_forward:
			self.go_forward()

		if self.turn_left:
			self.theta -= self.rotation_speed % (2 * math.pi)

		if self.turn_right:
			self.theta += self.rotation_speed % (2 * math.pi)

	def go_forward(self):
		# Save the original position in case we collide and need to revert
		original_position = (self.x, self.y)

		# self.x and self.y are floats, self.rect.x and self.rect.y are ints
		# so we update them separately to avoid loss of precision
		self.x += self.speed * math.cos(self.theta)
		self.y += self.speed * math.sin(self.theta)

		# If there is a collision, move back to the original position (disallow it)
		new_pos = self.rect.copy()
		new_pos.x = self.x
		new_pos.y = self.y
		if new_pos.collidelist(self.parent.walls) != -1:
			print "Collision!"
			self.x, self.y = original_position
		else:
			# Apply the position updates to the Player's rect
			self.rect = new_pos

	def get_info(self):
		""" Return information to be sent to the ANN """
		pass

	# Use this for moving the player
	def notify(self, command, state=True):
		if command == 'move_forward':
			self.move_forward = state
		elif command == 'turn_left':
			self.turn_left = state
		elif command == 'turn_right':
			self.turn_right = state
		else:
			print "Invalid command (this shouldn't happen!)"


class Wall(GameObject):

	def __init__(self, parent, position, dimension):
		super(Wall, self).__init__(parent, position, dimension)

	def draw(self, surface):
		wall_surface = surface.subsurface(self.rect)
		wall_surface.fill(Color.black)

class Map(GameObject):

	def __init__(self, parent, position, dimension):
		super(Map, self).__init__(parent, position, dimension)

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

class Button(GameObject):

	def __init__(self, parent, position, dimension):
		super(Button, self).__init__(parent, position, dimension)

	def mouse_click(self, pos):
		print pos

class InfoBox(GameObject):

	def __init__(self, parent, position, dimension, game_map):
		super(InfoBox, self).__init__(parent, position, dimension)
		self.game_map = game_map

	# Gather all the data to draw on the next
	# draw() call
	def update(self):
		pass

	# Draw information about the 'player' and provide
	# some buttons to modify the game
	def draw(self, surface):
		pass

class Simulation(GameObject):

	def __init__(self, resolution=(840, 512)):
		super(Simulation, self).__init__(None, dimension=resolution)

		# Set resolution for top-level objects
		self.resolution = resolution
		# Game resolution width and height are multiples of 64 for easy image scaling
		self.game_resolution = (640, 512)
		self.infobox_resolution = (200, 512)

		# Global settings
		self.running = True
		self.title = 'Simulation'
		self.framerate = 60
		self.clock = pygame.time.Clock()

		# Create the game_map and infobox objects
		game_pos = (0, 0)
		infobox_pos = (self.game_resolution[0], 0)
		self.game_map = Map(self, game_pos, self.game_resolution)
		self.infobox = InfoBox(self, infobox_pos, self.infobox_resolution, self.game_map)

		# Start sending/receiving with the player (ANN)
		connection_thread = threading.Thread(target=connection, args=[self.game_map.player])
		connection_thread.daemon = True
		connection_thread.start()

	def quit(self):
		self.running = false

	def keytoggle(self, key, state):
		if key == K_ESCAPE:
			self.running = False
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
			elif event.type == MOUSEMOTION:
				self.mouse_move(event.pos, event.rel, event.buttons)
			elif event.type == MOUSEBUTTONDOWN:
				self.mouse_down(event.pos, event.button)
			elif event.type == MOUSEBUTTONUP:
				self.mouse_up(event.pos, event.button)

	def update(self):
		self.game_map.update()
		self.infobox.update()

	def draw(self, window):
		# Get the surface representing the game's drawing area
		game_surface_rect = Rect((0, 0), self.game_resolution)
		game_surface = window.subsurface(game_surface_rect)

		# Get the rest
		infobox_surface_rect = Rect((game_surface_rect.right, 0), self.infobox_resolution)
		infobox_surface = window.subsurface(infobox_surface_rect)

		# Draw the game
		self.game_map.draw(game_surface)

		# Draw the infobox
		self.infobox.draw(infobox_surface)

	def mainloop(self, window):
		while self.running:
			time = self.clock.tick(self.framerate)

			self.check_input(pygame.event.get())
			self.update()
			self.draw(window)

			pygame.display.flip()
			pygame.event.pump()

def drawText(surface, msg, location = (0,0), size = 20, color = Color.white):
	font = pygame.font.Font(None, size)
	msgsurface = font.render(msg, False, color)
	rect = msgsurface.get_rect()
	rect.topleft = location
	surface.blit(msgsurface, rect)
	return rect

def connection(player):
	# create the server and the client for communication with ANN.
	# server for receiving commands from the ANN
	context = zmq.Context()
	socket = context.socket(zmq.REQ)
	socket.bind('tcp://127.0.0.1:1234')
	socket.connect('tcp://127.0.0.1:1235')

	while True:
		# send output to ANN.
		output_list = player.get_info()
		output_string = pickle.dumps(output_list)
		socket.send(output_string)

		# receive reply from ANN
		msg = socket.recv()
		list_message = pickle.loads(msg)
		if list_message:

			# position 1 will be turn right
			turn_right = list_message[0]
			if turn_right:
				player.notify('turn_right')

			# position 2 will be turn left
			turn_left = list_message[1]
			if turn_left:
				player.notify('turn_left')

			# position 3 will be move forward
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
