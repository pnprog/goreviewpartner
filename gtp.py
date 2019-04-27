# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import subprocess,sys
import threading, Queue
from time import sleep
from toolbox import log,GRPException

class gtp():
	def __init__(self,command):
		self.c=1
		self.command_line=command[0]+" "+" ".join(command[1:])
		command=[c.encode(sys.getfilesystemencoding()) for c in command]
		self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		self.stderr_queue=Queue.Queue()
		self.stdout_queue=Queue.Queue()
		threading.Thread(target=self.consume_stderr).start()
		self.free_handicap_stones=[]
		self.history=[]

	####low level function####
	def consume_stderr(self):
		while 1:
			try:
				err_line=self.process.stderr.readline().decode("utf-8")
				if err_line:
					log("#",err_line.strip())
					self.stderr_queue.put(err_line)
				else:
					log("leaving consume_stderr thread")
					return
			except Exception,e:
				log("leaving consume_stderr thread due to exception")
				log(e)
				return
	
	def consume_stdout(self):
		while 1:
			try:
				line=self.process.stdout.readline().decode("utf-8")
				if line:
					self.stdout_queue.put(line)
				else:
					log("leaving consume_stdout thread")
					return
			except Exception, e:
				log("leaving consume_stdout thread due to exception")
				log(e)
				return
	
	def quick_evaluation(self,color):
		return "Feature not implemented"
	
	def write(self,txt):
		try:
			self.process.stdin.write(txt+"\n")
		except Exception, e:
			log("Error while writting to stdin\n"+unicode(e))
		#self.process.stdin.write(str(self.c)+" "+txt+"\n")
		self.c+=1

	def readline(self):
		answer=self.process.stdout.readline().decode("utf-8")
		while answer in ("\n","\r\n","\r"):
			answer=self.process.stdout.readline().decode("utf-8")
		return answer
	
	####hight level function####
	def boardsize(self,size=19):
		self.size=size
		self.write("boardsize "+str(size))
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False
		
	def reset(self):
		self.write("clear_board")
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False

	def komi(self,k):
		self.write("komi "+str(k))
		answer=self.readline()
		if answer[0]=="=":
			self.komi_value=k
			return True
		else:return False	

	def place_black(self,move):
		if move == "RESIGN":
			log("WARNING: trying to play RESIGN as GTP move")
			self.history.append(["b",move])
			return True
		self.write("play black "+move)
		answer=self.readline()
		if answer[0]=="=":
			self.history.append(["b",move])
			return True
		else:return False	
	
	def place_white(self,move):
		if move == "RESIGN":
			log("WARNING: trying to play RESIGN as GTP move")
			self.history.append(["w",move])
			return True
		self.write("play white "+move)
		answer=self.readline()
		if answer[0]=="=":
			self.history.append(["w",move])
			return True
		else:return False


	def play_black(self):
		self.write("genmove black")
		answer=self.readline().strip()
		try:
			move=answer.split(" ")[1].upper()
			self.history.append(["b",move])
			return move
		except Exception, e:
			raise GRPException("GRPException in genmove_black()\nanswer='"+answer+"'\n"+unicode(e))

		
	def play_white(self):
		self.write("genmove white")
		answer=self.readline().strip()
		try:
			move=answer.split(" ")[1].upper()
			self.history.append(["w",move])
			return move
		except Exception, e:
			raise GRPException("GRPException in genmove_white()\nanswer='"+answer+"'\n"+unicode(e))


	def undo(self):
		self.reset()
		self.komi(self.komi_value)
		try:
			#adding handicap stones
			if len(self.free_handicap_stones)>0:
				self.set_free_handicap(self.free_handicap_stones)
			self.history.pop()
			history=self.history[:]
			self.history=[]
			for color,move in history:
				if color=="b":
					if not self.place_black(move):
						return False
				else:
					if not self.place_white(move):
						return False
			return True			
		except Exception, e:
			raise GRPException("GRPException in undo()\n"+unicode(e))
	
	def place(self,move,color):
		if color==1:
			return self.place_black(move)
		else:
			return self.place_white(move)
	
	def name(self):
		self.write("name")
		answer=self.readline().strip()
		try:
			return " ".join(answer.split(" ")[1:])
		except Exception, e:
			raise GRPException("GRPException in name()\nanswer='"+answer+"'\n"+unicode(e))
	
	def version(self):
		self.write("version")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except Exception,e:
			raise GRPException("GRPException in version()\nanswer='"+answer+"'\n"+unicode(e))


	def set_free_handicap(self,positions):
		self.free_handicap_stones=positions[:]
		stones=""
		for p in positions:
			stones+=p+" "
		self.write("set_free_handicap "+stones.strip())
		answer=self.readline().strip()
		try:
			if answer[0]=="=":
				return True
			else:
				return False	
		except Exception, e:
			raise GRPException("GRPException in set_free_handicap()\nanswer='"+answer+"'\n"+unicode(e))
	
	def undo_standard(self):
		self.write("undo")
		answer=self.readline()
		try:
			if answer[0]=="=":
				return True
			else:
				return False			
		except Exception, e:
			raise GRPException("GRPException in undo()\nanswer='"+answer+"'\n"+unicode(e))
	
	def countlib(self,move):
		self.write("countlib "+move)
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	#is that needed?
	def final_score(self):
		self.write("final_score")
		answer=self.readline()
		return " ".join(answer.split(" ")[1:]).strip()
	
	#is that needed?
	def final_status(self,move):
		self.write("final_status "+move)
		answer=self.readline()
		answer=answer.strip()
		return " ".join(answer.split(" ")[1:])

	def set_time(self,main_time=30,byo_yomi_time=30,byo_yomi_stones=1):
		self.write("time_settings "+str(main_time)+" "+str(byo_yomi_time)+" "+str(byo_yomi_stones))
		answer=self.readline()
		try:
			if answer[0]=="=":return True
			else:return False
		except Exception, e:
			raise GRPException("GRPException in set_time()\nanswer='"+answer+"'\n"+unicode(e))

	def quit(self):
		self.write("quit")
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False	

	def terminate(self):
		t=10
		while 1:
			self.quitting_thread.join(0.0)	
			if not self.quitting_thread.is_alive():
				log("The bot has quitted properly")
				break
			elif t==0:
				log("The bot is still running...")
				log("Forcefully closing it now!")
				break
			t-=1
			log("Waiting for the bot to close",t,"s")
			sleep(1)
		
		try: self.process.kill()
		except: pass
		try: self.process.stdin.close()
		except: pass
		
	def close(self):
		log("Now closing")
		self.quitting_thread=threading.Thread(target=self.quit)
		self.quitting_thread.start()
		threading.Thread(target=self.terminate).start()
