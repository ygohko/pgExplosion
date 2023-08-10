# -*- coding: utf-8 -*-

# Copyright (c) 2023 Yasuaki Gohko
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE ABOVE LISTED COPYRIGHT HOLDER(S) BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import sys
import math
import random
import struct
import pygame
from pygame.locals import *
from OpenGL.GL import *

rand = random.Random()
rand.seed()

def DrawCircle(radius,num_divide,r,g,b,a):
	glBegin(GL_TRIANGLE_FAN)
	glColor(r,g,b,a)
	glVertex(0.0,0.0,0.0)
	for i in range(num_divide + 1):
		angle = 2 * math.pi * i / num_divide
		glColor(0.0,0.0,0.0,0.0)
		glVertex(math.sin(angle) * radius,math.cos(angle) * radius,0.0) 
	glEnd()

class Vector:
	def __init__(self,x,y,z):
		self.x = x
		self.y = y
		self.z = z

	def __add__(self,vct):
		return Vector(self.x + vct.x,self.y + vct.y,self.z + vct.z)

	def __mul__(self,multi):
		return Vector(self.x * multi,self.y * multi,self.z * multi)

	def GetRandomNormal(cls):
		x = rand.random() - 0.5
		y = rand.random() - 0.5
		z = rand.random() - 0.5
		length = math.sqrt(x * x + y * y + z * z)
		if length == 0.0:
			return Vector(0.0,0.0,1.0)
		return Vector(x / length,y / length,z / length)

	def GetRandom(cls,min,range):
		return Vector.GetRandomNormal() * (min + rand.random() * range)

	GetRandomNormal = classmethod(GetRandomNormal)
	GetRandom = classmethod(GetRandom)

class Color:
	def __init__(self,r,g,b):
		self.r = r
		self.g = g
		self.b = b

class Particle:
	def __init__(self,position,delta,radius,radius_delta,color,cnt):
		self.position = position
		self.delta = delta
		self.radius = radius
		self.radius_delta = radius_delta
		self.color = color
		self.cnt = cnt
		self.cnt_begin = self.cnt

	def Process(self,speed = 1.0):
		if self.cnt > 0:
			self.cnt -= speed
			self.position += self.delta * speed
			self.radius += self.radius_delta * speed

	def Draw(self):
		if self.cnt > 0:
			alpha = 1.0 * self.cnt / self.cnt_begin
			glPushMatrix()
			glTranslated(self.position.x,self.position.y,self.position.z)
			DrawCircle(self.radius,16,self.color.r,self.color.g,self.color.b,alpha)
			glPopMatrix()

class Explosion:
	def __init__(self,position,radius,radius_delta,color,num_particle,power,power_min,cnt):
		self.particles = []
		for i in range(num_particle):
			self.particles.append(Particle(position,Vector.GetRandom(power_min,power),radius,radius_delta,color,cnt))

	def Process(self,speed = 1.0):
		for particle in self.particles:
			particle.Process(speed)

	def Draw(self):
		for particle in self.particles:
			particle.Draw()

class Pge:
	def __init__(self):
		self.explosions = []

	def InitSdl(self,width,height):
		pygame.init()
		pygame.display.set_mode((width,height),OPENGL | DOUBLEBUF)
		glViewport(0,0,width,height)
		glMatrixMode(GL_PROJECTION)
		glLoadIdentity()
		glMatrixMode(GL_MODELVIEW)
		glLoadIdentity()
		glClearColor(0.0,0.0,0.0,0.0)
		glFrustum(-1.0,1.0,-1.0,1.0,10.0,10000.0)
		glEnable(GL_BLEND)
		glBlendFunc(GL_SRC_ALPHA,GL_ONE)

	def Append(self,explosion):
		self.explosions.append(explosion)

	def SaveBmp(self,filename,width,height):
		raw = glReadPixels(0,0,width,height,GL_RGB,GL_UNSIGNED_BYTE)
		file = open(filename,"wb")
		file.write("BM")
		file.write(struct.pack("<l",14 + 40 + width * height * 3))
		file.write(struct.pack("<l",0))
		file.write(struct.pack("<l",54))
		file.write(struct.pack("<l",40))
		file.write(struct.pack("<l",width))
		file.write(struct.pack("<l",height))
		file.write(struct.pack("<h",1))
		file.write(struct.pack("<h",24))
		file.write(struct.pack("<l",0))
		file.write(struct.pack("<l",width * height * 3))
		file.write(struct.pack("<l",0))
		file.write(struct.pack("<l",0))
		file.write(struct.pack("<l",0))
		file.write(struct.pack("<l",0))
		length = len(raw) / 3
		for i in range(length):
			pos = i * 3
			file.write(raw[pos + 2])
			file.write(raw[pos + 1])
			file.write(raw[pos])

	def Preview(self,width,height):
		self.InitSdl(width,height)
		num_frame = 0
		while 1:
			for event in pygame.event.get():
				if event.type == KEYDOWN or event.type == QUIT:
					sys.exit(0)

			print "Processing frame %f" % num_frame

			glClear(GL_COLOR_BUFFER_BIT)
			glPushMatrix()
			glTranslated(0.0,0.0,-1000.0)

			for explosion in self.explosions:
				explosion.Process()
				explosion.Draw()

			glPopMatrix()
			pygame.display.flip()

			num_frame += 1

	def Process(self,width,height,basefilename,frame_begin,frame_end,num_divide):
		self.InitSdl(width,height)
		speed = 1.0 * (frame_end - frame_begin) / (num_divide - 1)
		num_image = 0
		num_frame = frame_begin
		if num_frame <= 0:
			num_frame = 0
		else:
			for explosion in self.explosions:
				explosion.Process(num_frame - speed)

		for i in range(num_divide):
			for event in pygame.event.get():
				if event.type == KEYDOWN or event.type == QUIT:
					sys.exit(0)

			print "Processing frame %f" % num_frame

			glClear(GL_COLOR_BUFFER_BIT)
			glPushMatrix()
			glTranslated(0.0,0.0,-1000.0)

			for explosion in self.explosions:
				explosion.Process(speed)
				explosion.Draw()

			glPopMatrix()
			pygame.display.flip()
			self.SaveBmp("%s%04d.bmp" % (basefilename,num_image),width,height)

			num_image += 1
			num_frame += speed

if __name__ == "__main__":
	pge = Pge()
	pge.Append(Explosion(Vector(10.0,5.0,1.0),20.0,0.2,Color(0.7,0.2,0.2),25,0.5,0.8,100))
	pge.Append(Explosion(Vector(-5.0,15.0,-20.0),20.0,0.2,Color(0.7,0.2,0.2),25,0.5,0.8,100))
	pge.Append(Explosion(Vector(0.0,-7.0,10.0),20.0,0.2,Color(0.7,0.2,0.2),25,0.5,0.8,100))
	pge.Append(Explosion(Vector(10.0,-10.0,0.0),20.0,0.2,Color(0.7,0.2,0.2),25,0.6,0.8,100))
	pge.Append(Explosion(Vector(0.0,0.0,0.0),20.0,0.1,Color(0.7,0.2,0.2),100,1.5,1.0,50))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	# pge.Append(Particle(Vector(0,0,0),Vector(0,0,0),128,-1,Color(0.7,0.2,0.2),100))
	pge.Preview(256,256)
	# pge.Process(32,32,"bulletexplosion",10,90,16)
