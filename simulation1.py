#SIMULATION FOR POLAR 3D PRINTER

'''
TO DO LIST....
-Printer Object
	-independent and depented variabels
	-contain step converter
-GCODE Parser
	-gcode -> polar coordinates
-Step Converter
	-polar coordinates -> motor steps
-Visualizer
	-steps sizes
	-error
	-print

'''
from tkinter import *
import time
import math
import io
import numpy as np 
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from parse_gcode import parse_gcode
from printer_object import printer as p_obj

ROOT_WIDTH = 800
ROOT_HEIGHT = 600
THETA_SPR = 200

#GCODE PARAMETERS	
# GCODE_FILE_PATH = "sims/_smileycoin.gcode"
GCODE_FILE_PATH = "sims/test.gcode"

class PrintViz:
	def __init__(self, r):
		self.root = r
		self.root.wm_title("Printer Simulation")

		geo = str(ROOT_WIDTH) + "x" + str(ROOT_HEIGHT)
		self.root.geometry(geo)
		self.root.resizable(0, 0)
		self.master_frame = Frame(self.root, width=ROOT_WIDTH, height=ROOT_HEIGHT)
		self.master_frame.pack()
		# l = Label(self.master_frame, text='test')
		# l.pack()
		
		self.c0_frame = Frame(self.master_frame, width=ROOT_WIDTH*0.75, height=ROOT_HEIGHT)
		self.c1_frame = Frame(self.master_frame, width=ROOT_WIDTH*0.25, height=ROOT_HEIGHT)
		self.c0_frame.grid(row=0, column=0, padx=1, pady=1, sticky=W)
		self.c1_frame.grid(row=0, column=1, padx=1, pady=1, sticky=W)

		self.c0 = Canvas(self.c0_frame, width=ROOT_WIDTH*0.75, height=ROOT_HEIGHT*0.75, bd=3, relief="sunken")
		self.c1 = Canvas(self.c0_frame, width=ROOT_WIDTH*0.75, height=ROOT_HEIGHT*0.25, bd=3, relief="sunken")
		self.c0.pack()
		self.c1.pack()

class StepperMotor:
	event_time = 0
	error = 0
	pulse = False
	
	def __init__(self, spr):
		self.spr = spr
		self.start_time = time.time()
		
	def get_step_goal(self, a):
		angle = a + self.error
		theoretical = 0.5*angle*self.spr/math.pi 
		goal = round(theoretical)
		self.error = 2*math.pi*(theoretical-goal)/self.spr
		return goal 

	def execute_sync_step(self, delay):
		self.pulse = not self.pulse
		self.event_time += delay
		return [self.event_time, self.pulse]

class PolarPrinter:
	plot_x0 = []
	plot_y0 = []
	plot_x1 = []
	plot_y1 = []
	plot_x2 = []
	plot_y2 = []
	plot_x3 = []
	plot_y3 = []
	cmd_counter = 0
	steps = 100
	start_time = 0
	task_state = False
	task = []
	delay = [0, 0]
	min_step_delay = 0.001
	start_time = 0
	def __init__(self, s0, s1):
		self.stepper0 = s0
		self.stepper1 = s1
		self.fig = plt.figure()
		self.ax0 = self.fig.add_subplot(2,2,1)
		self.ax1 = self.fig.add_subplot(2,2,2)
		self.ax2 = self.fig.add_subplot(2,1,2)

	def set_start_time(self):
		self.start_time = time.time()

	def set_cmds(self, c):
		self.cmds = c

	def set_task(self, c):
		self.task_state = True
		self.task = []
		s0 = c[0]
		s1 = c[1]
		print("S0: " + str(s0) + " S1: " + str(s1))
		if s0 == 0:
			self.delay[1] = self.min_step_delay
			for i in range(2*abs(s1)):
				self.task.append([1, s1/abs(s1)])
		elif s1 == 0:
			self.delay[0] = self.min_step_delay
			for i in range(2*abs(s0)):
				self.task.append([0, s0/abs(s0)])
		else:
			ratio = abs(float(s0))/abs(float(s1))
			print("Ratio: " + str(ratio))
			if ratio >= 1:
				self.delay[0] = self.min_step_delay
				self.delay[1] = self.min_step_delay * ratio
				s1_count = 0
				for i in range(2*abs(s0)):
					self.task.append([0, s0/abs(s0)])
					if i * self.delay[0] > s1_count * self.delay[1]:
						self.task.append([1, s1/abs(s1)])
						s1_count += 1
			else:
				ratio = 1/ratio
				self.delay[0] = self.min_step_delay * ratio
				self.delay[1] = self.min_step_delay
				s0_count = 0
				for i in range(2*abs(s1)):
					self.task.append([1, s0/abs(s0)])
					if i * self.delay[1] > s0_count * self.delay[0]:
						self.task.append([0, s0/abs(s0)])
						s0_count += 1

		print("Delay: " + str(self.delay))
		print("Sync Steps: " + str(len(self.task)))
		print(self.task)
		print("\n")

	def execute_task(self):
		t = self.task.pop(0)
		motor = t[0]
		if len(self.task) == 0:
			self.task_state = False
		if motor == 0:
			x = self.stepper0.execute_sync_step(self.delay[0])
			return [0, x[0], x[1], t[1]*self.delay[0]]
		elif motor == 1:
			x = self.stepper1.execute_sync_step(self.delay[1])
			return [1, x[0], x[1], t[1]*self.delay[1]]

	def print(self, i):
		current = False
		if self.cmd_counter < len(self.cmds):
			if not self.task_state:
				self.set_task(self.cmds[self.cmd_counter])
				self.cmd_counter += 1

			while self.task_state and not current:
				data = self.execute_task()
				t = data[1]
				if t > time.time() - self.start_time:
					print("ANIMATION IS CURRENT")
					current = True
				if data[0] == 0:
					self.plot_x0.append(data[1]*1000)
					self.plot_y0.append(not data[2])
					self.plot_x0.append(data[1]*1000)
					self.plot_y0.append(data[2])
					self.plot_x2.append(data[1]*1000)
					self.plot_y2.append(data[3])
				elif data[0] == 1:
					self.plot_x1.append(data[1]*1000)
					self.plot_y1.append(not data[2])
					self.plot_x1.append(data[1]*1000)
					self.plot_y1.append(data[2])
					self.plot_x3.append(data[1]*1000)
					self.plot_y3.append(data[3])

			self.ax0.clear()
			self.ax0.set_xlim(self.plot_x0[-1]-10, self.plot_x0[-1])
			self.ax0.plot(self.plot_x0, self.plot_y0)
			self.ax1.clear()
			self.ax1.set_xlim(self.plot_x1[-1]-10, self.plot_x1[-1])
			self.ax1.plot(self.plot_x1, self.plot_y1)
			self.ax2.clear()
			# self.ax2.set_xlim(self.plot_x2[-1]-100, self.plot_x2[-1])
			# self.ax2.set_ylim(-0.005, 0.005)
			self.ax2.plot(self.plot_x3, self.plot_y3)
			self.ax2.plot(self.plot_x2, self.plot_y2)

stepper0 = StepperMotor(800)
stepper1 = StepperMotor(800)
pp = PolarPrinter(stepper0, stepper1)

if __name__ == "__main__":
	#Get and parse GCODE to polar coordinates
	gcode = open(GCODE_FILE_PATH, 'r').read()
	coordinate_list = parse_gcode(gcode)
	p = p_obj(6.75,5)

	cmd_list = []
	c_old = [0, 0, False] 
	for coordinates in coordinate_list:
		for c in coordinates:
			#delta = [dr, dtheta]
			delta = [c[0] - c_old[0], c[1] - c_old[1]]
			#R ANGLE
			a0 = p.get_belt_angle(delta[0])
			s0 = stepper0.get_step_goal(a0)
			#PLATE ANGLE
			a1 = delta[1]
			s1 = stepper1.get_step_goal(a1)
			#!!!!!!!!!!!!!!!EXTRUDER ANGLE!!!!!!!!!!!
			if c[2] != 0:
				#convert distance traveled -> volume -> syringe dx -> stepper angle
				a2 = 1
			else:
				a2 = 0
			c_old = c
			cmd_list.append([s0, s1])

	pp.set_cmds(cmd_list)
	pp.set_start_time()

	while True:
		try:
			ani = animation.FuncAnimation(pp.fig, pp.print, interval=1)
			plt.show()
		except KeyboardInterrupt:
			break
