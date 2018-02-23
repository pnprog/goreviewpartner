# -*- coding: utf-8 -*-

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from Tkinter import *
import sys
import os

import ConfigParser

from time import sleep
import os
import threading
import ttk

from toolbox import *
from toolbox import _

import tkMessageBox


class LeelaZeroAnalysis():

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		
		leela_zero=self.leela_zero
		log()
		log("==============")
		log("move",str(current_move))
		
		additional_comments=""
		if player_color in ('w',"W"):
			log("leela Zero play white")
			answer=leela_zero.play_white()
		else:
			log("leela Zero play black")
			answer=leela_zero.play_black()
		
		if current_move>1:
			es=leela_zero.get_leela_zero_final_score()
			one_move.set("ES",es)
		
		best_answer=answer
		all_moves=leela_zero.get_all_leela_zero_moves()
		if (answer.lower() not in ["pass","resign"]):
			
			one_move.set("CBM",answer.lower()) #Computer Best Move

			all_moves2=all_moves[:]
			nb_undos=1
			#log("====move",current_move+1,all_moves[0],'~',answer)
			
			
			#making sure the first line of play is more than one move deep				
			while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]) and (nb_undos<=20):
				log("going deeper for first line of play (",nb_undos,")")

				if player_color in ('w',"W") and nb_undos%2==0:
					answer=leela_zero.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=leela_zero.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=leela_zero.play_black()
				else:
					answer=leela_zero.play_white()
				nb_undos+=1
				

				

				#linelog(all_moves[0],'+',answer)
				all_moves2=leela_zero.get_all_leela_zero_moves()
				if (answer.lower() not in ["pass","resign"]):
					
					#log('+',all_moves2)
					all_moves[0][1]+=" "+all_moves2[0][1]

					if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
						all_moves[0][2]=all_moves2[0][2]
					else:
						all_moves[0][2]=100-all_moves2[0][2]

				else:
					log()
					log("last play on the fist of play was",answer,"so leaving")
			
			for u in range(nb_undos):
				#log("undo...")
				leela_zero.undo()
			
			best_move=True
			#variation=-1
			log("Number of alternative sequences:",len(all_moves))
			#log(all_moves)
			for sequence_first_move,one_sequence,one_value_network,one_policy_network,one_nodes in all_moves[:self.maxvariations]:
				log("Adding sequence starting from",sequence_first_move)
				previous_move=one_move.parent
				current_color=player_color
									
				first_variation_move=True
				for one_deep_move in one_sequence.split(' '):
					if one_deep_move.lower() in ["pass","resign"]:
						log("Leaving the variation when encountering",one_deep_move.lower())
						break
					i,j=gtp2ij(one_deep_move)
					new_child=previous_move.new_child()
					new_child.set_move(current_color,(i,j))

					
					if player_color=='b':
						black_win_rate=str(one_value_network)+'%'
						white_win_rate=str(100-one_value_network)+'%'
					else:
						black_win_rate=str(100-one_value_network)+'%'
						white_win_rate=str(one_value_network)+'%'
						
					if first_variation_move:
						first_variation_move=False
						variation_comment=_("Value network black/white win probability for this move: ")+black_win_rate+'/'+white_win_rate
						new_child.set("BWR",black_win_rate) #Black value network
						new_child.set("WWR",white_win_rate) #White value network
						variation_comment+="\n"+_("Policy network value for this move: ")+str(one_policy_network)+'%'
						variation_comment+="\n"+_("Number of playouts used to estimate this variation: ")+str(one_nodes)
						new_child.add_comment_text(variation_comment)
					if best_move:
						best_move=False
						additional_comments+=_("Value network black/white win probability for this move: ")+black_win_rate+'/'+white_win_rate
						one_move.set("BWR",black_win_rate) #Black value network
						one_move.set("WWR",white_win_rate) #White value network
						
					
					previous_move=new_child
					if current_color in ('w','W'):
						current_color='b'
					else:
						current_color='w'
			log("==== no more sequences =====")
			
		else:
			log('adding "'+answer.lower()+'" to the sgf file')
			additional_comments+="\n"+_("For this position, %s would %s"%("Leela Zero",answer.lower()))
			if answer.lower()=="pass":
				leela_zero.undo()
			elif answer.lower()=="resign":
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
				else:
					leela_zero.undo_resign()
		
		one_move.add_comment_text(additional_comments)
		return best_answer
	
	def initialize_bot(self):
		leela_zero=leela_zero_starting_procedure(self.g,self.profile)
		self.leela_zero=leela_zero
		self.time_per_move=0
		return leela_zero

def leela_zero_starting_procedure(sgf_g,profile="slow",silentfail=False):
	if profile=="slow":
		timepermove_entry="SlowTimePerMove"
	elif profile=="fast":
		timepermove_entry="FastTimePerMove"

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	leela_zero=bot_starting_procedure("LeelaZero","Leela Zero",Leela_Zero_gtp,sgf_g,profile,silentfail)
	if not leela_zero:
		return False
	try:
		time_per_move=Config.get("LeelaZero", timepermove_entry)
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				leela_zero.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				#self.time_per_move=time_per_move #why is that needed???
	except:
		log("Wrong value for Leela thinking time:",Config.get("LeelaZero", timepermove_entry))
		log("Erasing that value in the config file")
		Config.set("LeelaZero",timepermove_entry,"")
		Config.write(open(config_file,"w"))
	
	return leela_zero



class RunAnalysis(LeelaZeroAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(LeelaZeroAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)


import ntpath
import subprocess
import threading, Queue

class Leela_Zero_gtp(gtp):

	def quick_evaluation(self,color):
		if color==2:
			answer=self.play_white()
		else:
			answer=self.play_black()
		
		all_moves=self.get_all_leela_zero_moves()
		
		if answer.lower()=="pass":
			self.undo()
		elif answer.lower()=="resign":
			self.undo_resign()
		else:
			self.undo()
		
		sequence_first_move,one_sequence,one_value_network,one_policy_network,one_nodes = all_moves[0]
		if color==1:
			black_win_rate=str(one_value_network)+'%'
			white_win_rate=str(100-one_value_network)+'%'
		else:
			black_win_rate=str(100-one_value_network)+'%'
			white_win_rate=str(one_value_network)+'%'
		return _("black/white win probability for this variation: ")+black_win_rate+'/'+white_win_rate

	def undo_resign(self):
		#apparently, Leela consider "resign" as a standard move that need to be undoed the same way as other move 
		self.undo()

	def __init__(self,command):
		self.c=1
		leela_zero_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		log("Leela Zero working directory:",leela_zero_working_directory)

		self.process=subprocess.Popen(command,cwd=leela_zero_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		
		self.stderr_queue=Queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()
	def get_leela_zero_final_score(self):
		self.write("final_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GtpException("GtpException in Get_leela_zero_final_score()")

	def get_leela_zero_influence(self):
		self.write("influence")
		one_line=self.readline() #empty line
		buff=[]
		while self.stderr_queue.empty():
			sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		buff.reverse()
		#log(buff)
		influence=[]
		for i in range(self.size):
			one_line=buff[i].strip()
			one_line=one_line.replace(".","0").replace("x","1").replace("o","2").replace("O","0").replace("X","0").replace("w","1").replace("b","2")
			one_line=[int(s) for s in one_line.split(" ")]
			influence.append(one_line)
		
		return influence

	def get_all_leela_zero_moves(self):
		buff_size=18
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()
		
		answers=[]
		for err_line in buff:
			if " ->" in err_line:
				if err_line[0]==" ":
					#log(err_line)
					one_answer=err_line.strip().split(" ")[0]
					nodes=int(err_line.strip().split("(")[0].split("->")[1].replace(" ",""))
					value_network=float(err_line.split("(V:")[1].split('%')[0].strip())
					policy_network=float(err_line.split("(N:")[1].split('%)')[0].strip())
					sequence=err_line.split("PV: ")[1].strip()
					
					answers=[[one_answer,sequence,value_network,policy_network,nodes]]+answers

		return answers

from leela_analysis import LeelaSettings

class LeelaZeroSettings(LeelaSettings):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.name="LeelaZero"
		self.initialize()


class LeelaZeroOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Leela Zero'
		self.my_starting_procedure=leela_zero_starting_procedure

LeelaZero={}
LeelaZero['name']="LeelaZero"
LeelaZero['gtp_name']="Leela Zero"
LeelaZero['analysis']=LeelaZeroAnalysis
LeelaZero['openmove']=LeelaZeroOpenMove
LeelaZero['settings']=LeelaZeroSettings
LeelaZero['gtp']=Leela_Zero_gtp
LeelaZero['liveanalysis']=LiveAnalysis
LeelaZero['runanalysis']=RunAnalysis
LeelaZero['starting']=leela_zero_starting_procedure

import getopt
if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = open_sgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		top = Tk()
		bot=LeelaZero
		
		slowbot=bot
		slowbot['profile']="slow"
		fastbot=dict(bot)
		fastbot['profile']="fast"
		RangeSelector(top,filename,bots=[slowbot, fastbot]).pack()
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		top=None
		batch=[]
		
		for filename in parameters[1]:
			
			move_selection,intervals,variation,komi,nogui=parse_command_line(filename,parameters[0])
			if nogui:
				log("File to analyse:",filename)
				app=RunAnalysis("no-gui",filename,move_selection,intervals,variation-1,komi)
				app.terminate_bot()
			else:
				if not top:
					top = Tk()
					top.withdraw()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi]
				batch.append(one_analysis)
		
		if not nogui:
			top.after(1,lambda: batch_analysis(top,batch))
			top.mainloop()
