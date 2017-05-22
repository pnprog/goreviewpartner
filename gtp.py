import subprocess
import threading, Queue

from time import sleep,time
class gtp():
	def __init__(self,command):
		self.c=1
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
			except Exception, e:
				import sys, os
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print exc_type, fname, exc_tb.tb_lineno
				print "leaving consume_stderr thread due to exception"
				return
	
	def write(self,txt):
		try:
			self.process.stdin.write(txt+"\n")
		except:
			print "Error while writting to stdin"
			self.kill()
		#self.process.stdin.write(str(self.c)+" "+txt+"\n")
		self.c+=1
	
	def get_leela_final_score(self):
		self.write("final_score")
		answer=self.readline()
		return " ".join(answer.split(" ")[1:])
	
	def get_gnugo_initial_influence_black(self):
		self.write("initial_influence black influence_regions")
		one_line=self.readline()
		#print "->",one_line
		one_line=one_line.split("= ")[1].strip().replace("  "," ")
		lines=[one_line]
		for i in range(self.size-1):
			one_line=self.readline().strip().replace("  "," ")
			lines.append(one_line)
		
		influence=[]
		for i in range(self.size):
			influence=[[int(s) for s in lines[i].split(" ")]]+influence
		return influence

	
	def get_gnugo_initial_influence_white(self):
		self.write("initial_influence white influence_regions")
		one_line=self.readline()
		#print "->",one_line
		one_line=one_line.split("= ")[1].strip().replace("  "," ")
		lines=[one_line]
		for i in range(self.size-1):
			one_line=self.readline().strip().replace("  "," ")
			lines.append(one_line)
		
		influence=[]
		for i in range(self.size):
			influence=[[int(s) for s in lines[i].split(" ")]]+influence
		return influence
	
	def get_gnugo_estimate_score(self):
		self.write("estimate_score")
		answer=self.readline().strip()
		return answer.split(" ")[1]

	def gnugo_top_moves_black(self):
		self.write("top_moves_black")
		answer=self.readline()[:-1]
		answer=answer.split(" ")[1:-1]
		answers_list=[]
		for value in answer:
			try:
				score=float(value)
			except:
				answers_list.append(value)
		return answers_list

	def gnugo_top_moves_white(self):
		self.write("top_moves_white")
		answer=self.readline()[:-1]
		answer=answer.split(" ")[1:-1]
		answers_list=[]
		for value in answer:
			try:
				score=float(value)
			except:
				answers_list.append(value)
		return answers_list

	
	def get_gnugo_experimental_score(self,color):
		self.write("experimental_score "+color)
		answer=self.readline().strip()
		return answer[2:]
		
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
				nodes=int(err_line.strip().split("(")[0].split("->")[1].replace(" ",""))
				neural_net=float(err_line.split("(N:")[1].split('%)')[0].strip())
				if one_score!="0.00%)":
					sequence=err_line.split("PV: ")[1].strip()
					#if float(one_score[:-2])>=100 or float(one_score[:-2])<0:
					#	print "one score:",one_score,one_score[:-2],float(one_score[:-2])
					#	print "err line:",err_line
					#	print
					#answers.append([one_answer,sequence,float(one_score[:-2]),nodes])
					answers=[[one_answer,sequence,float(one_score[:-2]),nodes,neural_net]]+answers
					
		#if len(answers)==1:
		#	if len(answers[0][1].split(' '))==1:
		#		print "\t\tNeed one move deeper analysis!"
		
		return answers
		#return sorted(answers,lambda x,y: int(1000*(y[2]-x[2])))

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
	
	def play_black(self):
		self.write("genmove black")
		answer=self.readline().strip()
		return answer.split(" ")[1]

		
	def play_white(self):
		self.write("genmove white")
		answer=self.readline().strip()
		return answer.split(" ")[1]

	def set_free_handicap(self,stones):
		self.write("set_free_handicap "+stones)
		answer=self.readline().strip()
		return answer.split("= ")[1]
	
	def undo(self):
		self.write("undo")
		answer=self.readline()
		if answer[0]=="=":
			return True
		else:
			return False
	
	def show_board(self):
		self.write("showboard")
		answer=self.readline(3+self.size).strip()
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
		answer=answer.strip()
		return " ".join(answer.split(" ")[1:])

	def set_time(self,main_time=30,byo_yomi_time=30,byo_yomi_stones=1):
		self.write("time_settings "+str(main_time)+" "+str(byo_yomi_time)+" "+str(byo_yomi_stones))
		answer=self.readline()
		if answer[0]=="=":return True
		else:return False

	def gtp_exit(self):
		self.write("quit")
		answer=self.readline()
		answer
		if answer[0]=="=":
			return True
		else:
			return False
	
	def kill(self):
		print "process.terminate()"
		self.process.terminate()
		sleep(0.5)
		print "process.kill()"
		self.process.kill()
		sleep(0.5)


