#!/usr/bin/python

# Simulation for Neural Network

import pygame
import pygame.draw
import random

from pygame.locals import *

# TODO:
# 	* [ ] Rewrite the draw methods to use actual images
# 	* [ ] Consider using Sprite class as a base for the GameObject class
# 	* [ ] Enemies need to move (finish the 'update' function)
# 	* [ ] Walls and hazards should be placed in smarter locations
# 	* [ ] Add feelers (wall/obstacle sensors) and radar (enemy sensor) to Player
# 	* [ ] Add socket code to connect to the ANN
# 	* [ ] Add controls for the ANN to modify the Player object
# 	* [ ] Clean it up a bit
# 	* [ ] Add controls to modify the environment while the ANN is running

class Color(pygame.Color):
	white = pygame.Color(255, 255, 255)
	red = pygame.color.Color(255, 0, 0)
	yellow = pygame.color.Color(255, 255, 0)
	green = pygame.color.Color(0, 255, 0)
	blue = pygame.color.Color(0, 0, 255)
	black = pygame.color.Color(0, 0, 0)

class GameObject(object):

	def __init__(self, position, dimension=(0, 0)):
		self._rect = pygame.Rect(position, dimension)

	def update(self):
		pass

	def draw(self, surface):
		pass

	def notify(self, *args, **kwargs):
		print args
		print kwargs

	@property
	def rect(self):
		return self._rect

	@rect.setter
	def rect(self, value):
		self._rect = value

class Tile(GameObject):

	types = ['normal', 'trap', 'wall']

	def __init__(self, position, dimension, tile_type):
		super(Tile, self).__init__(position, dimension)
		self.tile_type = tile_type

	def draw(self, surface):
		type_map = {
			'normal': Color.green,
			'end': Color.blue,
			'trap': Color.yellow,
			'wall': Color.black
		}

		tile_color = type_map[self.tile_type]
		surface.subsurface(self.rect).fill(tile_color)

class Enemy(GameObject):

	def __init__(self, game_map, position, radius=10):
		super(Enemy, self).__init__(position, (2 * radius, 2 * radius))
		self.radius = radius
		self.game_map = game_map

	def draw(self, surface):
		pygame.draw.circle(surface, Color.red, self.rect.topleft, self.radius)

	def update(self):
	# 	if not self.rect.collidelist(self.game_map.invalid_tiles):
		self.rect.centerx += 1

class Player(GameObject):

	def __init__(self, position, radius=10):
		super(Player, self).__init__(position)
		self.radius = radius

	def draw(self, surface):
		pygame.draw.circle(surface, Color.blue, self.rect.topleft, self.radius)

	# Use this for moving the player
	def notify(self, test):
		print test

class Map(GameObject):

	def __init__(self, width, height, tiles_x=16, tiles_y=12):
		self.width = width
		self.height = height
		# tiles_x and tiles_y are the number of tiles in the x and y directions
		self.tiles_x = tiles_x
		self.tiles_y = tiles_y
		self.tile_width = self.width / self.tiles_x
		self.tile_height = self.height / self.tiles_y

		self.create_tiles()
		self.create_enemies()
		self.player = Player((20, 20))
		self.player.notify('hi')

	# TODO: Break this up into smaller functions.
	# TODO: Break up creating a tile from giving it a type?
	def create_tiles(self):
		self.tiles = []
		tile_dimension = (self.tile_width, self.tile_height)

		# Create the tiles and assign random types
		for i in xrange(self.tiles_x):
			self.tiles.append([])

			for j in xrange(self.tiles_y):
				num_types = len(Tile.types)
				tile_choice = random.randint(0, num_types - 1)
				tile_type = Tile.types[tile_choice]

				tile_position = (i * tile_dimension[0], j * tile_dimension[1])

				new_tile = Tile(tile_position, tile_dimension, tile_type)
				self.tiles[i].append(new_tile)

		# Make a clear path to the end, and create the end
		path = [0, 0]
		end = [self.tiles_x - 1, self.tiles_y - 1]
		while path != end:
			self.tiles[path[0]][path[1]].tile_type = 'normal'

			movement_dir = random.randint(0, 1)

			if path[movement_dir] == end[movement_dir]:
				movement_dir = 1 - movement_dir

			path[movement_dir] += 1


		self.tiles[end[0]][end[1]].tile_type = 'end'

		# Find a list of all valid tiles to spawn in
		all_tiles = []
		for column in self.tiles:
			all_tiles.extend([tile for tile in column])
		self.valid_tiles = [tile for tile in all_tiles if tile.tile_type == 'normal']
		self.invalid_tiles = list(set(all_tiles) - set(self.valid_tiles))

	def create_enemies(self):
		self.enemies = []

		for i in xrange(3):
			# Keep enemies from being created in invalid locations
			tile_location = random.choice(self.valid_tiles)

			enemy_pos = tile_location.rect.center

			new_enemy = Enemy(self, enemy_pos)
			self.enemies.append(new_enemy)


	def draw(self, surface):
		tile_width = surface.get_width() / self.tiles_x
		tile_height = surface.get_height() / self.tiles_y
		tile_size = (tile_width, tile_height)

		for column in self.tiles:
			for tile in column:
				tile.draw(surface)

		for enemy in self.enemies:
			enemy.draw(surface)

		self.player.draw(surface)

	def update(self):
		for column in self.tiles:
			for tile in column:
				tile.update()

		for enemy in self.enemies:
			enemy.update()

		self.player.update()


class Simulation(object):

	def __init__(self):
		self.running = True
		# 64 * 13, 64 * 10, so the images can be powers of 2 and easy to scale
		self.resolution = (832, 640)
		self.title = 'Simulation'
		self.framerate = 60
		self.clock = pygame.time.Clock()

		self.game_map = Map(*self.resolution)

	def quit(self):
		self.running = false

	def keytoggle(self, key, state):
		if key == K_q:
			self.running = False

	def update_input(self, events):
		for event in events:
			if event.type == QUIT:
				self.running = False
			elif event.type == KEYDOWN:
				self.running = False
				# self.keytoggle(event.key, True)
			elif event.type == KEYUP:
				self.keytoggle(event.key, False)

	def update_logic(self):
		self.game_map.update()

	def update_screen(self, window):
		self.game_map.draw(window)

	def mainloop(self, window):
		while self.running:
			time = self.clock.tick(self.framerate)

			self.update_input(pygame.event.get())
			self.update_logic()
			self.update_screen(window)

			pygame.display.flip()
			pygame.event.pump()

def drawText(surface, msg, location = (0,0), size = 20, color = Color.white):
	font = pygame.font.Font(None, size)
	msgsurface = font.render(msg, False, color)
	rect = msgsurface.get_rect()
	rect.topleft = location
	surface.blit(msgsurface, rect)
	return rect

def main():
	sim = Simulation()

	pygame.init()
	pygame.display.set_mode(sim.resolution)
	pygame.display.set_caption(sim.title)

	window = pygame.display.get_surface()
	sim.mainloop(window)

main()
