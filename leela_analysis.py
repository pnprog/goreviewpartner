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


class LeelaAnalysis():

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)

		leela=self.leela
		log()
		log("==============")
		log("move",str(current_move))
		
		additional_comments=""
		#additional_comments="Move "+str(current_move)
		if player_color in ('w',"W"):
			#additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
			log("leela play white")
			answer=leela.play_white()
		else:
			#additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))
			log("leela play black")
			answer=leela.play_black()
		
		if current_move>1:
			es=leela.get_leela_final_score()
			one_move.set("ES",es)
		
		best_answer=answer
		all_moves=leela.get_all_leela_moves()
		if (answer.lower() not in ["pass","resign"]):
			
			one_move.set("CBM",answer.lower()) #Computer Best Move
			
			if all_moves==[]:
				bookmove=True
				all_moves=[[answer,answer,666,666,666,666,666,666,666]]
			else:
				bookmove=False
			all_moves2=all_moves[:]
			nb_undos=1
			#log("====move",current_move+1,all_moves[0],'~',answer)
			
			#making sure the first line of play is more than one move deep

			while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]) and (nb_undos<=20):
				#log("going deeper for first line of play (",nb_undos,")")

				if player_color in ('w',"W") and nb_undos%2==0:
					answer=leela.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=leela.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=leela.play_black()
				else:
					answer=leela.play_white()
				nb_undos+=1
				

				

				#linelog(all_moves[0],'+',answer)
				all_moves2=leela.get_all_leela_moves()
				if (answer.lower() not in ["pass","resign"]):
					
					#log("all_moves2:",all_moves2)
					if all_moves2==[]:
						all_moves2=[[answer,answer,666,666,666,666,666,666,666]]

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
				leela.undo()
			

			best_move=True
			#variation=-1
			log("Number of alternative sequences:",len(all_moves))
			#log(all_moves)
			for sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes in all_moves[:self.maxvariations]:
				log("Adding sequence starting from",sequence_first_move)
				previous_move=one_move.parent
				current_color=player_color
				
				if best_move:
					if player_color=='b':
						linelog(str(one_score)+'%/'+str(100-one_score)+'%')
					else:
						linelog(str(100-one_score)+'%/'+str(one_score)+'%')
				
				first_variation_move=True
				for one_deep_move in one_sequence.split(' '):
					if one_deep_move.lower() in ["pass","resign"]:
						log("Leaving the variation when encountering",one_deep_move.lower())
						break
					i,j=gtp2ij(one_deep_move)
					new_child=previous_move.new_child()
					new_child.set_move(current_color,(i,j))						
					
					if player_color=='b':
						black_win_rate=str(one_score)+'%'
						white_win_rate=str(100-one_score)+'%'
						black_mc_win_rate=str(one_monte_carlo)+'%'
						white_mc_win_rate=str(100-one_monte_carlo)+'%'
					else:
						black_win_rate=str(100-one_score)+'%'
						white_win_rate=str(one_score)+'%'
						black_mc_win_rate=str(100-one_monte_carlo)+'%'
						white_mc_win_rate=str(one_monte_carlo)+'%'
					
					if first_variation_move:
						first_variation_move=False
						if not bookmove:
							variation_comment=_("black/white win probability for this variation: ")+black_win_rate+'/'+white_win_rate
							new_child.set("BWR",black_win_rate) #Black Win Rate
							new_child.set("WWR",white_win_rate) #White Win Rate
							variation_comment+="\n"+_("Monte Carlo win probalbility for this move: ")+black_mc_win_rate+'/'+white_mc_win_rate
							if one_value_network!=None:
								if player_color=='b':
									variation_comment+="\n"+_("Value network black/white win probability for this move: ")+str(one_value_network)+'%/'+str(100-one_value_network)+'%'
								else:
									variation_comment+="\n"+_("Value network black/white win probability for this move: ")+str(100-one_value_network)+'%/'+str(one_value_network)+'%'
							if one_policy_network!=None:
								variation_comment+="\n"+_("Policy network value for this move: ")+str(one_policy_network)+'%'
							if one_evaluation!=None:
								variation_comment+="\n"+_("Evaluation for this move: ")+str(one_evaluation)+'%'
							if one_rave!=None:
								variation_comment+="\n"+_("RAVE(x%: y) for this move: ")+str(one_rave)+'%'
							variation_comment+="\n"+_("Number of playouts used to estimate this variation: ")+str(one_nodes)
							new_child.add_comment_text(variation_comment)
						else:
							new_child.add_comment_text(_("Book move"))
					if best_move:
						best_move=False
						if not bookmove:
							additional_comments+="\n"+(_("%s black/white win probability for this position: ")%"Leela")+black_win_rate+'/'+white_win_rate
							one_move.set("BWR",black_win_rate) #Black Win Rate
							one_move.set("WWR",white_win_rate) #White Win Rate
					
					previous_move=new_child
					if current_color in ('w','W'):
						current_color='b'
					else:
						current_color='w'
			log("==== no more sequences =====")
			
			log("Creating the influence map")
			influence=leela.get_leela_influence()
			black_influence_points=[]
			white_influence_points=[]
			for i in range(self.size):
				for j in range(self.size):
					if influence[i][j]==1:
						black_influence_points.append([i,j])
					elif influence[i][j]==2:
						white_influence_points.append([i,j])

			if black_influence_points!=[]:
				one_move.parent.set("TB",black_influence_points)
			
			if white_influence_points!=[]:
				one_move.parent.set("TW",white_influence_points)	
				
		else:
			log('adding "'+answer.lower()+'" to the sgf file')
			additional_comments+="\n"+_("For this position, %s would %s"%("Leela",answer.lower()))
			if answer.lower()=="pass":
				leela.undo()
			elif answer.lower()=="resign":
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
					
		one_move.add_comment_text(additional_comments)
		
		return best_answer #returning the best move, necessary for live analysis

	def initialize_bot(self):
		leela=leela_starting_procedure(self.g,"slow") #analysis is always "slow"
		self.leela=leela
		self.time_per_move=0
		return leela

def leela_starting_procedure(sgf_g,profil="slow",silentfail=False):
	if profil=="slow":
		timepermove_entry="TimePerMove"
	elif profil=="fast":
		timepermove_entry="ReviewTimePerMove"

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	leela=bot_starting_procedure("Leela","Leela",Leela_gtp,sgf_g,profil,silentfail)
	if not leela:
		return False

	try:
		time_per_move=Config.get("Leela", timepermove_entry)
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				leela.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				#self.time_per_move=time_per_move #why is that needed???
	except:
		log("Wrong value for Leela thinking time:",Config.get("Leela", timepermove_entry))
		log("Erasing that value in the config file")
		Config.set("Leela",timepermove_entry,"")
		Config.write(open(config_file,"w"))
	
	return leela

class RunAnalysis(LeelaAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi)

class LiveAnalysis(LeelaAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename):
		LiveAnalysisBase.__init__(self,g,filename)

class Leela_gtp(gtp):
	
	def get_leela_final_score(self):
		self.write("final_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GtpException("GtpException in Get_leela_final_score()")

	def get_leela_influence(self):
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

	def get_all_leela_moves(self):
		buff_size=18
		buff=[]
		
		sleep(.01)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.01)
		
		buff.reverse()
		
		answers=[]
		for err_line in buff:
			if " ->" in err_line:
				#log(err_line)
				one_answer=err_line.strip().split(" ")[0]
				one_score= ' '.join(err_line.split()).split(' ')[4]
				nodes=int(err_line.strip().split("(")[0].split("->")[1].replace(" ",""))
				monte_carlo=float(err_line.split("(U:")[1].split('%)')[0].strip())
				
				if self.size==19:
					value_network=float(err_line.split("(V:")[1].split('%')[0].strip())
					policy_network=float(err_line.split("(N:")[1].split('%)')[0].strip())
					evaluation=None
					rave=None
				else:
					value_network=None
					policy_network=None
					evaluation=float(err_line.split("(N:")[1].split('%)')[0].strip())
					rave=err_line.split("(R:")[1].split(')')[0].strip()
				
				
				if one_score!="0.00%)":
					sequence=err_line.split("PV: ")[1].strip()
					answers=[[one_answer,sequence,float(one_score[:-2]),monte_carlo,value_network,policy_network,evaluation,rave,nodes]]+answers

		return answers


class LeelaSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.name="Leela"
		self.initialize()
		
	def initialize(self):
		bot=self.name
		log("Initializing "+bot+" setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		row=0
		title=Label(self,text=_("%s settings")%bot, font="-weight bold").grid(row=row,column=1,sticky=W)

		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		Command = StringVar() 
		Command.set(Config.get(bot,"Command"))
		Entry(self, textvariable=Command, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		Parameters = StringVar() 
		Parameters.set(Config.get(bot,"Parameters"))
		Entry(self, textvariable=Parameters, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		TimePerMove = StringVar() 
		TimePerMove.set(Config.get(bot,"TimePerMove"))
		Entry(self, textvariable=TimePerMove, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		NeededForReview = BooleanVar(value=Config.getboolean(bot, 'NeededForReview'))
		Cbutton=Checkbutton(self, text=_("Needed for review"), variable=NeededForReview,onvalue=True,offvalue=False)
		Cbutton.grid(row=row,column=1,sticky=W)
		Cbutton.var=NeededForReview
		
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		ReviewCommand = StringVar() 
		ReviewCommand.set(Config.get(bot,"ReviewCommand"))
		Entry(self, textvariable=ReviewCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		ReviewParameters = StringVar() 
		ReviewParameters.set(Config.get(bot,"ReviewParameters"))
		Entry(self, textvariable=ReviewParameters, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		ReviewTimePerMove = StringVar() 
		ReviewTimePerMove.set(Config.get(bot,"ReviewTimePerMove"))
		Entry(self, textvariable=ReviewTimePerMove, width=30).grid(row=row,column=2)
		


		self.Command=Command
		self.Parameters=Parameters
		self.TimePerMove=TimePerMove
		self.NeededForReview=NeededForReview
		self.ReviewCommand=ReviewCommand
		self.ReviewParameters=ReviewParameters
		self.ReviewTimePerMove=ReviewTimePerMove
		

	def save(self):
		bot=self.name
		log("Saving "+bot+" settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set(bot,"Command",self.Command.get())
		Config.set(bot,"Parameters",self.Parameters.get())
		Config.set(bot,"TimePerMove",self.TimePerMove.get())
		Config.set(bot,"NeededForReview",self.NeededForReview.get())
		Config.set(bot,"ReviewCommand",self.ReviewCommand.get())
		Config.set(bot,"ReviewParameters",self.ReviewParameters.get())
		Config.set(bot,"ReviewTimePerMove",self.ReviewTimePerMove.get())
		
		Config.write(open(config_file,"w"))




class LeelaOpenMove(BotOpenMove):
	def __init__(self,sgf_g):
		BotOpenMove.__init__(self,sgf_g)
		self.name='Leela'
		self.my_starting_procedure=leela_starting_procedure

Leela={}
Leela['name']="Leela"
Leela['gtp_name']="Leela"
Leela['analysis']=LeelaAnalysis
Leela['openmove']=LeelaOpenMove
Leela['settings']=LeelaSettings
Leela['gtp']=Leela_gtp
Leela['liveanalysis']=LiveAnalysis
Leela['runanalysis']=RunAnalysis
Leela['starting']=leela_starting_procedure

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
		RangeSelector(top,filename,bots=[Leela]).pack()
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

