import subprocess
import threading, Queue

from time import sleep,time

from toolbox import log

class GtpException(Exception):
	pass

class gtp():
	def __init__(self,command):
		self.c=1
		self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		self.command_line=command[0]+" "+" ".join(command[1:])
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
					log("leaving consume_stderr thread")
					return
			except Exception, e:
				import sys, os
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				log(exc_type, fname, exc_tb.tb_lineno)
				log("leaving consume_stderr thread due to exception")
				return
	
	def write(self,txt):
		try:
			self.process.stdin.write(txt+"\n")
		except Exception, e:
			log("Error while writting to stdin\n"+str(e))
			self.kill()
		#self.process.stdin.write(str(self.c)+" "+txt+"\n")
		self.c+=1

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
		try:
			self.gtp_exit()
			sleep(0.5)
		except: pass
		
		try: self.process.kill()
		except: pass
		
		try: self.process.stdin.close()
		except: pass
		
		
	
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
	
	def name(self):
		self.write("name")
		answer=self.readline().strip()
		try:
			return " ".join(answer.split(" ")[1:])
		except Exception, e:
			raise GtpException("GtpException in name()\nanswer='"+answer+"'\n"+str(e))
	
	def version(self):
		self.write("version")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except Exception,e:
			raise GtpException("GtpException in version()\nanswer='"+answer+"'\n"+str(e))

	def play_black(self):
		self.write("genmove black")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except Exception, e:
			raise GtpException("GtpException in genmove_black()\nanswer='"+answer+"'\n"+str(e))

		
	def play_white(self):
		self.write("genmove white")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except Exception, e:
			raise GtpException("GtpException in genmove_white()\nanswer='"+answer+"'\n"+str(e))

	def set_free_handicap(self,positions):
		stones=""
		for p in positions:
			stones+=p+" "
		log("Setting handicap stones at",stones.strip())
		self.write("set_free_handicap "+stones.strip())
		answer=self.readline().strip()
		try:
			if answer[0]=="=":
				return True
			else:
				return False	
		except Exception, e:
			raise GtpException("GtpException in set_free_handicap()\nanswer='"+answer+"'\n"+str(e))
		
	def undo(self):
		self.write("undo")
		answer=self.readline()
		try:
			if answer[0]=="=":
				return True
			else:
				return False			
		except Exception, e:
			raise GtpException("GtpException in undo()\nanswer='"+answer+"'\n"+str(e))

	def countlib(self,move):
		self.write("countlib "+move)
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	#is that needed?
	def final_score(self):
		self.write("final_score")
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
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
			raise GtpException("GtpException in set_time()\nanswer='"+answer+"'\n"+str(e))

	def gtp_exit(self):
		self.write("quit")
		answer=self.readline()
		answer
		if answer[0]=="=":
			return True
		else:
			return False
	
	def kill(self):
		log("process.terminate()")
		self.process.terminate()
		sleep(0.5)
		log("process.kill()")
		self.process.kill()
		sleep(0.5)




