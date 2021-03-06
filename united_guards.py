#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#version 0.2 alpha, released on September 03, 2012 by Vojtěch Polášek <vojtech.polasek@gmail.com>
#This is the first testing version of my first game, so nothing is guaranteed actually
#see included README file for more info

#initialisation
import time
import pygame
import os.path
import random
import sys
import gettext
import locale

import menu
import speech

#gettext initialisation
gettext.bindtextdomain('messages', 'lang')
gettext.textdomain('messages')
_ = gettext.gettext

#pygame initialisation
pygame.init()
pygame.display.set_mode((320, 200))
pygame.display.set_caption ('United guards')
#pygame.event.set_allowed([pygame.QUIT, pygame.KEYUP, pygame.KEYDOWN])

#initialisation of speech
try:
	lang=locale.getdefaultlocale()[0]
except AtributeError, IndexError:
	lang=None
if lang and (os.path.exists(os.path.normpath("lang/" + lang)) or os.path.exists(os.path.normpath("lang/" + lang.split("_")[0]))):
	lang=lang.split("_")[0]
else:
	lang="en"
s =speech.Speaker(language=lang)

#pass needed functions to menu module
menu.s = s
#menu._ = gettext.gettext

#define menus
#define main menu
start = menu.menuitem(_("Start the game"), "__main__.g.startgame(5, 3)")
instructions = menu.menuitem(_("Read instructions"), "__main__.readmanual()")
quit = menu.menuitem(_("Quit the game"), "__main__.g.quit ()")
main_menu = menu.menu(_("Welcome to the main menu. Use up and down arrows to select an item, enter to confirm and escape to quit."), [start, instructions, quit])
#define pause game prompt
continuegame = menu.menuitem(_("Continue the game"), "__main__.g.resumegame()")
abort = menu.menuitem(_("Abort the game and return to the main menu."), "__main__.g.abortgame()")
abortprompt = menu.menu(_("Do you really want to abort the game?"), [continuegame, abort])


#channel initialisation
pygame.mixer.set_reserved(2)
chan=pygame.mixer.Channel(0)
mgchan = pygame.mixer.Channel(1)


class game:

	def __init__(self):
		self.lives = None
		self.delay = None  #delay between attacks
		self.rand = None  #used in generating of direction and checking user input
		self.score = 0
		self.target_falling = False  #True when attack is pending
		self.previous = None  #stores last needed time
		self.remaining = None #stores time when game is paused
		self.paused = False
		self.pressed = False
		self.menu_active = None #indicates if we are in menu
		self.game_active = None #indicates if we are in actual game
		self.running = True #indicates if main loop is running
		self.current_menu = None
		self.initSounds()

	def position(self):
		"""sets random positionn of falling sound."""
		self.target_falling = True
		self.previous = time.time()
		self.rand = random.randrange(0, 3)
		if self.rand == 0:
			self.left = 1
			self.right = 0.1
		elif self.rand == 1:
			self.left = 1
			self.right = 1
		elif self.rand == 2:
			self.left = 0.1
			self.right = 1
		self.planenum = random.randrange (0, self.planeCount)
		self.cutplane = self.soundcut(self.planeSounds[self.planenum], self.orig_delay - self.delay)
		chan.play(self.cutplane)
		chan.set_volume(self.left, self.right)

	def check(self, input):
		"""checks user input"""
		self.pressed = True
		if input == self.rand and time.time() < self.previous + self.delay:
			self.score += 100 * round ((time.time () - self.previous), 3)
			self.missileSounds[input].play()			
			pygame.time.delay(250)
			mgchan.play(self.planehitSounds[0])
			mgchan.set_volume(self.left, self.right)
			chan.fadeout (200)
			self.rand=None
			self.delay -= 0.05
			self.previous = time.time() + self.delay * 1.2
			self.target_falling = False
		else:
			self.missileSounds[input].play ()
			pygame.time.delay(int(self.missileSounds[input].get_length()*1000))
			self.die()
			self.lives -= 1
			self.previous = time.time()
			self.target_falling = False
			self.previous = time.time() + self.cutplane.get_length() - (time.time() - self.previous)

	def die(self):
		rand = random.randrange (0, self.mgCount)
		mgchan.play (self.mgSounds[rand])
		mgchan.set_volume (self.left, self.right)
		for i in range (3):
			randvar = random.randrange (0, self.ricochetCount)
			self.ricochetSounds[randvar].play()
			pygame.time.delay(100)
		for i in range (2):
			randvar = random.randrange (0, self.bhitCount)
			self.bhitSounds[randvar].play()
			pygame.time.delay(100)
		randvar = random.randrange (0, self.deadCount)
		self.deadSounds[randvar].play()

	def soundcut (self, sound, time_to_cut):
		"""Accepts pygame sound object and cuts time_to_cut from its beginning, using numpy array slicing. Returns pygame sound object."""
		length = sound.get_length()
		snd_array = pygame.sndarray.array(sound)
		frame_rate = len(snd_array) / length
		cut_frames = frame_rate * time_to_cut
		result = snd_array [cut_frames:]
		soundresult = pygame.sndarray.make_sound (result)
		return soundresult

	def startgame(self, lives, delay):
		"""starts  game and initialises variables."""		
		self.previous = time.time()
		self.lives = lives
		self.orig_delay = self.delay = delay
		self.score = 0
		self.target_falling = False
		self.rand = None
		self.remaining = None
		self.pressed = False
		self.game_active = True
		self.menu_active = False
		self.position()

	def loop(self):
		"""main game loop."""
		while self.running == True:
			pygame.time.delay(1)
			event = pygame.event.poll ()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					if self.game_active == True:
						self.pausegame()
				elif event.key ==  pygame.K_RETURN:
					if self.menu_active == True:
						self.current_menu.select()
				elif event.key == pygame.K_LEFT:
					if self.game_active == True:
						if self.pressed == False:
							self.check(0)
				elif event.key == pygame.K_UP:
					if self.menu_active == True:
						self.current_menu.moveup()
					elif self.game_active == True:
						if self.pressed == False:
							self.check(1)
				elif event.key == pygame.K_RIGHT:
					if self.game_active == True:
						if self.pressed == False:
							self.check(2)
				elif event.key == pygame.K_DOWN:
					if self.menu_active == True:
						self.current_menu.movedown()
				elif event.key == pygame.K_s:
					if self.game_active == True:
						s.say(_("Your score is {0}.").format(self.score), 1)
				elif event.key == pygame.K_l:
					if self.game_active == True:
						s.say (_("You have {0} lives remaining.").format(self.lives), 1)
				elif event.key == pygame.K_LCTRL or event.key == pygame.K_RCTRL:
					s.stop()
			if self.game_active == True:
				#print "game part"
				if self.lives <= 0:
					pygame.time.delay(1000)
					s.say (_("Game Over. Your final score is {0}.").format(self.score), 1)
					self.current_menu = main_menu.init ()
					self.game_active = False
					self.menu_active = True
				if (time.time() >= self.previous + self.delay - self.aimSounds[0].get_length()) and self.target_falling == True:
#					print "aiming"
					mgchan.play (self.aimSounds[0])
#					mgchan.set_volume (self.left, self.right)
				if (time.time() >= self.previous + self.delay) and self.target_falling == True:
					self.pressed = True
					mgchan.stop()
					self.die()
					self.previous = time.time() + self.cutplane.get_length() - self.delay
					self.lives -=1
					self.target_falling = False
				elif (time.time() >= self.previous) and self.target_falling == False:
#					print "next plane"
					self.position()
					self.pressed = False

	def pausegame(self):
		pygame.mixer.pause()
		self.remaining = time.time() - (self.previous + self.delay)
		self.game_active = False
		self.menu_active = True
		self.current_menu = abortprompt.init()

	def resumegame(self):
		self.previous = time.time() + self.remaining
		pygame.mixer.unpause()
		self.menu_active = False
		self.game_active = True

	def abortgame(self):
		pygame.mixer.stop()
		self.remaining = None
		self.current_menu = main_menu.init()

	def quit (self):
		s.say (_("Exiting now."), 1)
		s.quit ()
		pygame.quit ()
		sys.exit ()

	def initSounds(self):
		self.planehitSounds = [
			pygame.mixer.Sound (os.path.normpath("sounds/planehit.ogg"))
		]
		self.aimSounds =[
			pygame.mixer.Sound(os.path.normpath("sounds/aim.ogg"))
		]
		staticSounds =[
			"planehit.ogg",
			"aim.ogg"
		]
		self.planeSounds=[]
		self.mgSounds=[]
		self.missileSounds=[]
		self.deadSounds=[]
		self.bhitSounds=[]
		self.ricochetSounds=[]
		dir="sounds"
		for fileName in os.listdir(dir):
			if not os.path.isfile(os.path.normpath("%s/%s"%(dir,fileName))) and not fileName.endswith(".ogg") or fileName in staticSounds:
				continue
			if fileName.startswith("plane"):
				self.planeSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("mg"):
				self.mgSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("aim"):
				self.aimSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("missile"):
				self.missileSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("dead"):
				self.deadSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("bhit"):
				self.bhitSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
			if fileName.startswith("ricoch"):
				self.ricochetSounds.append(pygame.mixer.Sound(os.path.normpath("%s/%s"%(dir,fileName))))
				continue
		self.planeCount=len(self.planeSounds)
		self.mgCount=len(self.mgSounds)
		self.missileCount=len(self.missileSounds)
		self.deadCount=len(self.deadSounds)
		self.bhitCount=len(self.bhitSounds)
		self.ricochetCount=len(self.ricochetSounds)
		print("ricochet sounds %d"%self.ricochetCount)


def readmanual():
	s.say (_("This is very simple. Listen for incoming planes and press corresponding arrow (Left, Up or Right) to launch a missile in given direction.\nPress L to announce number of remaining lives and S to announce your score.\nPress ESCAPE to pause the game.\nHave fun!"), 1)


if __name__ == "__main__":
	s.say(_("Welcome to the game."), 1)
	g = game()
	g.current_menu = main_menu.init()
	g.menu_active = True
	g.game_active = False
	g.loop()

