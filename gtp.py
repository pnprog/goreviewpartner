#!/usr/bin/python
# -*- coding: utf-8 -*-

##   Copyright 2010, 2011 Pierre-Nicolas <pnprog@tuxfamily.org>

##   File: gtp.py
##   This file is part of GoSP 0.01.06, a program for training
##   at go with GNU Go.
##   Author: Pierre-Nicolas <pnprog@tuxfamily.org>
##   Date: Sat, 05 Mar 2011 22:18:46 +0800
##   For more information, see http://gosp.tuxfamily.org/

##   GoSP is free software: you can redistribute it and/or modify
##   it under the terms of the GNU General Public License as published by
##   the Free Software Foundation, either version 3 of the License, or
##   (at your option) any later version.
##
##   GoSP is distributed in the hope that it will be useful,
##   but WITHOUT ANY WARRANTY; without even the implied warranty of
##   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##   GNU General Public License for more details.
##
##   You should have received a copy of the GNU General Public License
##   along with GoSP.  If not, see <http://www.gnu.org/licenses/>.

# -*- coding:Utf-8 -*-

import subprocess
#import select

import threading, Queue

from time import sleep
class gtp():
	def __init__(self,command):
		self.c=1
		#self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		
		self.stderr_queue=Queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()
		
	####low level function####
	
	def consume_stderr(self):
		while 1:
			try:
				err_line=self.process.stderr.readline()
				if err_line:
					self.stderr_queue.put(err_line)
				else:
					print "leaving consume_stderr thread"
					return
			except:
				print "leaving consume_stderr thread due to exception"
				return
	
	def write(self,txt):
		self.process.stdin.write(txt+"\n")
		#self.process.stdin.write(str(self.c)+" "+txt+"\n")
		self.c+=1
	
	def get_leela_final_score(self):
		self.write("final_score")
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	
	def get_gnugo_estimate_score(self):
		self.write("estimate_score")
		answer=self.readline()[:-1]
		try:
			return answer.split(" ")[1]
		except:
			print "Error while parsing GNUGO white answer:", answer
	
	def get_gnugo_experimental_score(self,color):
		self.write("experimental_score "+color)
		answer=self.readline()[:-1]
		try:
			return answer[2:]
		except:
			print "Error while parsing GNUGO white answer:", answer
		
	def get_all_leela_moves(self):
		buff_size=18
		buff=[]
		
		
		"""
		ready,_,_=select.select([self.process.stderr.fileno()],[],[],0.1)
		while len(ready)>0:
			err_line=self.process.stderr.readline()
			buff.append(err_line)
			if len(buff)>buff_size:
				buff.pop(0)
			ready,_,_=select.select([self.process.stderr.fileno()],[],[],0.1)
		"""
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()
		#print "buff:",buff
		
		answers=[]
		for err_line in buff:
			if " ->" in err_line:
				one_answer=err_line.strip().split(" ")[0]
				one_score= ' '.join(err_line.split()).split(' ')[4]
				if one_score!="0.00%)":
					sequence=err_line.split("PV: ")[1].strip()
					#if float(one_score[:-2])>=100 or float(one_score[:-2])<0:
					#	print "one score:",one_score,one_score[:-2],float(one_score[:-2])
					#	print "err line:",err_line
					#	print
					answers.append([one_answer,sequence,float(one_score[:-2])])
		
		#if len(answers)==1:
		#	if len(answers[0][1].split(' '))==1:
		#		print "\t\tNeed one move deeper analysis!"
		
		return sorted(answers,lambda x,y: int(1000*(y[2]-x[2])))

	def readline(self):
		answer=self.process.stdout.readline()
		while answer in ("\n","\r\n","\r"):
			answer=self.process.stdout.readline()
		return answer
	
	####hight level function####
	def boardsize(self,size=19):
		self.size=size
		self.write("boardsize "+str(size))
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False
		
	def close(self):
		self.process.kill()
		self.process.stdin.close()
		
	
	def reset(self):
		self.write("clear_board")
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False

	def komi(self,k):
		self.write("komi "+str(k))
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False	

	def place_black(self,move):
		self.write("play black "+move)
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False	
	
	def place(self,move,color):
		if color==1:
			return self.place_black(move)
		else:
			return self.place_white(move)
	
	def place_white(self,move):
		self.write("play white "+move)
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False
	
	def play_black(self):
		self.write("genmove black")
		answer=self.readline()[:-1]
		try:
			return answer.split(" ")[1]
		except:
			print "Error while parsing GNUGO black answer:", answer
		
	def play_white(self):
		self.write("genmove white")
		answer=self.readline()[:-1]
		try:
			return answer.split(" ")[1]
		except:
			print "Error while parsing GNUGO white answer:", answer
	
	def undo(self):
		self.write("undo")
		answer=self.readline()
		if answer[0]=="=":
			return True
		else:
			return False
	
	def show_board(self):
		self.write("showboard")
		answer=self.readline(3+self.size)[:-1]
		return answer[4:]
	
	def countlib(self,move):
		self.write("countlib "+move)
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	def final_score(self):
		self.write("final_score")
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	def final_status(self,move):
		self.write("final_status "+move)
		answer=self.readline()
		answer=answer[:-1]
		return " ".join(answer.split(" ")[1:])

	def set_time(self,main_time=30,byo_yomi_time=30,byo_yomi_stones=1):
		self.write("time_settings "+str(main_time)+" "+str(byo_yomi_time)+" "+str(byo_yomi_stones))
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False

	def kill(self):
		#self.process.terminate()
		#sleep(1)
		self.process.kill()



"""
leela_command_line=('E:\\goreviewpartner\\Leela080GTP\\Leela080.exe', '--gtp', '--noponder')

leela=gtp(leela_command_line)
leela.boardsize(19)
leela.reset()
leela.komi(6.5)

leela.set_time(main_time=5,byo_yomi_time=5,byo_yomi_stones=1)

print leela.play_black()
print leela.play_white()
print leela.play_black()
print leela.play_white()
print leela.play_black()
print leela.play_white()
print leela.play_black()
print leela.play_white()
print leela.get_all_leela_moves()

"""
