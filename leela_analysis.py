# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from Tkinter import *

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
		#additional_comments=""
		if player_color in ('w',"W"):
			log("leela play white")
			answer=leela.play_white()
		else:
			log("leela play black")
			answer=leela.play_black()
		
		
		best_answer=answer
		node_set(one_move,"CBM",answer) #Computer Best Move
		
		#all_moves=leela.get_all_leela_moves()
		position_evaluation=leela.get_all_leela_moves()

		if "estimated score" in position_evaluation:
			node_set(one_move,"ES",position_evaluation["estimated score"])
		if (answer.lower() in ["pass","resign"]):
			bookmove=False
			leela.undo()
			nb_undos=0
		else:
			nb_undos=1 #let's remember to undo that move from Leela
			
			#one_move.set("CBM",answer.lower()) #Computer Best Move
			if 'book move' in position_evaluation:
				bookmove=True
			else:
				bookmove=False
			
			#let's make sure there is at least one variation available
			if len(position_evaluation['variations'])==0:
				position_evaluation['variations'].append({'sequence':answer})

				
			#let's make sure that there is more than one move for the first line of play
			#only one move could be a bookmove, or a very very forcing move
			first_sequence=position_evaluation['variations'][0]['sequence']
			new_sequence=first_sequence
			while len(new_sequence.split())<=1 and nb_undos<=5:
				log("first, let's ask leela for the next move")
				if player_color in ('w',"W") and nb_undos%2==0:
					answer=leela.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=leela.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=leela.play_black()
				else:
					answer=leela.play_white()
				nb_undos+=1 #one have to remember to undo that move later
				
				new_position_evaluation=leela.get_all_leela_moves() #let's get stats for this new move
				
				#let's make sure there is at least one variation available
				if len(new_position_evaluation['variations'])==0:
					new_position_evaluation['variations'].append({'sequence':answer})
				
				if (answer.lower() not in ["pass","resign"]):
					#let's check the lenght of the new sequence
					new_sequence=new_position_evaluation["variations"][0]["sequence"]
					#adding this new sequence to the old sequence
					position_evaluation['variations'][0]['sequence']+=" "+new_sequence
					
					#we continue only if this is still a book move
					if "book move" not in new_position_evaluation:
						break

				else:
					#leela does not want to play further on this line of play
					#so let's stop there
					break

			
		best_move=True
		log("Number of alternative sequences:",len(position_evaluation['variations']))
		for variation in position_evaluation['variations']:
			#exemple: variation={'first move': 'M10', 'value network win rate': '21.11%', 'monte carlo win rate': '36.11%', 'sequence': 'M10 M9', 'playouts': '22', 'win rate': '27.46%', 'policy network value': '3.6%'}
			previous_move=one_move.parent
			current_color=player_color	
			first_variation_move=True
			for one_deep_move in variation['sequence'].split(' '):
				if one_deep_move.lower() in ["pass","resign"]:
					log("Leaving the variation when encountering",one_deep_move.lower())
					break

				i,j=gtp2ij(one_deep_move)
				new_child=previous_move.new_child()
				node_set(new_child,current_color,(i,j))
				
				if first_variation_move==True:
					first_variation_move=False
					#variation_comment=""
		
					if 'win rate' in variation:
						if player_color=='b':
							black_value=variation['win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['win rate']
							black_value=opposite_rate(white_value)
						node_set(new_child,"BWWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"BWWR",black_value+'/'+white_value)
					
					if 'monte carlo win rate' in variation:
						if player_color=='b':
							black_value=variation['monte carlo win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['monte carlo win rate']
							black_value=opposite_rate(white_value)
						node_set(new_child,"MCWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"MCWR",black_value+'/'+white_value)
					
					if 'value network win rate' in variation:
						if player_color=='b':
							black_value=variation['value network win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['value network win rate']
							black_value=opposite_rate(white_value)
						node_set(new_child,"VNWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"VNWR",black_value+'/'+white_value)
					
					if 'move evaluation' in variation:
						node_set(new_child,"EVAL",variation['move evaluation'])
						
					if 'rapid action value estimation' in variation:
						node_set(new_child,"RAVE",variation['rapid action value estimation'])
						
					if 'policy network value' in variation:
						node_set(new_child,"PNV",variation['policy network value'])
					
					if 'playouts' in variation:
						node_set(new_child,"PLYO",variation['playouts'])
						
					if bookmove:
						bookmove=False
						node_set(new_child,"BKMV","yes")
					
					if best_move:
						best_move=False
					
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
			node_set(one_move.parent,"TB",black_influence_points)
		if white_influence_points!=[]:
			node_set(one_move.parent,"TW",white_influence_points)
			
		for u in range(nb_undos):
			leela.undo()

		return best_answer #returning the best move, necessary for live analysis

	def initialize_bot(self):
		leela=leela_starting_procedure(self.g,self.profile)
		self.leela=leela
		self.time_per_move=0
		return leela

def leela_starting_procedure(sgf_g,profile="slow",silentfail=False):
	if profile=="slow":
		timepermove_entry="SlowTimePerMove"
	elif profile=="fast":
		timepermove_entry="FastTimePerMove"

	leela=bot_starting_procedure("Leela","Leela",Leela_gtp,sgf_g,profile,silentfail)
	if not leela:
		return False

	try:
		time_per_move=grp_config.get("Leela", timepermove_entry)
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				leela.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				#self.time_per_move=time_per_move #why is that needed???
	except:
		log("Wrong value for Leela thinking time:",grp_config.get("Leela", timepermove_entry))
		log("Erasing that value in the config file")
		grp_config.set("Leela",timepermove_entry,"")
	
	return leela

class RunAnalysis(LeelaAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(LeelaAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)

class Position(dict):
	def __init__(self):
		self['variations']=[]

class Variation(dict):
	pass

class Leela_gtp(gtp):

	def showboard(self):
		self.write("showboard")
		self.readline() #empty line
		buff=[]
		while self.stderr_queue.empty():
			sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		for line in buff:
			log(line.strip())
		
	def quick_evaluation(self,color):
		if color==2:
			answer=self.play_white()
		else:
			answer=self.play_black()
		position_evaluation=self.get_all_leela_moves()
		self.undo()
		
		txt=""
		try:
			if color==1:
				black_win_rate=position_evaluation["variations"][0]["win rate"]
				white_win_rate=opposite_rate(black_win_rate)
			else:
				white_win_rate=position_evaluation["variations"][0]["win rate"]
				black_win_rate=opposite_rate(white_win_rate)
			txt+= variation_data_formating["BWWR"]%(black_win_rate+'/'+white_win_rate)
			txt+="\n\n"+variation_data_formating["ES"]%self.get_leela_final_score()
		except:
			txt+=variation_data_formating["ES"]%self.get_leela_final_score()

		return txt
	
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
		buff=[]
		
		sleep(.01)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.01)
		
		position_evaluation=Position()
		
		for err_line in buff:
			#log(err_line[:-1])
			
			if "score=" in err_line:
				position_evaluation["estimated score"]=err_line.split("score=")[1].strip()
			
			if "book moves" in err_line:
				log("book move")
				position_evaluation["book move"]=True
			
			if " ->" in err_line:
				variation=Variation()
				#log(err_line[:-1])
				one_answer=err_line.strip().split(" ")[0]
				variation["first move"]=one_answer
				one_score=err_line.split()[4][:-1]
				nodes=err_line.strip().split("(")[0].split("->")[1].replace(" ","")
				variation["playouts"]=nodes
				if self.size==19:
					monte_carlo=err_line.split("(U:")[1].split('%)')[0].strip()+"%"
					variation["monte carlo win rate"]=monte_carlo
					value_network=err_line.split("(V:")[1].split('%')[0].strip()+"%"
					variation["value network win rate"]=value_network
					policy_network=err_line.split("(N:")[1].split('%)')[0].strip()+"%"
					variation["policy network value"]=policy_network
					evaluation=None
					rave=None
				else:
					value_network=None
					policy_network=None
					evaluation=err_line.split("(N:")[1].split('%)')[0].strip()
					variation["move evaluation"]=evaluation
					rave=err_line.split("(R:")[1].split(')')[0].strip().replace(":","")
					rave1=rave.split()[0]
					rave2=rave.split()[1]
					variation["rapid action value estimation"]=rave1+' '+rave2
				
				if one_score!="0.00%":
					variation["win rate"]=one_score
					sequence=err_line.split("PV: ")[1].strip()
					variation["sequence"]=sequence
					position_evaluation['variations'].append(variation)
		return position_evaluation



class LeelaSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.name="Leela"
		self.gtp=Leela_gtp
		self.parent=parent
		self.initialize()
		
	def initialize(self):
		bot=self.name
		log("Initializing "+bot+" setting interface")

		bot=self.name
		
		row=0
		Label(self,text=_("%s settings")%bot, font="-weight bold").grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Slow profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		SlowCommand = StringVar() 
		SlowCommand.set(grp_config.get(bot,"SlowCommand"))
		Entry(self, textvariable=SlowCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		SlowParameters = StringVar()
		SlowParameters.set(grp_config.get(bot,"SlowParameters"))
		Entry(self, textvariable=SlowParameters, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		SlowTimePerMove = StringVar()
		SlowTimePerMove.set(grp_config.get(bot,"SlowTimePerMove"))
		Entry(self, textvariable=SlowTimePerMove, width=30).grid(row=row,column=2)
		row+=1
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(self.gtp,"slow")).grid(row=row,column=1,sticky=W)

		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Fast profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		FastCommand = StringVar()
		FastCommand.set(grp_config.get(bot,"FastCommand"))
		Entry(self, textvariable=FastCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		FastParameters = StringVar() 
		FastParameters.set(grp_config.get(bot,"FastParameters"))
		Entry(self, textvariable=FastParameters, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		FastTimePerMove = StringVar() 
		FastTimePerMove.set(grp_config.get(bot,"FastTimePerMove"))
		Entry(self, textvariable=FastTimePerMove, width=30).grid(row=row,column=2)
		row+=1
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(self.gtp,"fast")).grid(row=row,column=1,sticky=W)
		
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("%s availability")%bot).grid(row=row,column=1,sticky=W)
		row+=1
		
		value={"slow":_("Slow profile"),"fast":_("Fast profile"),"both":_("Both profiles"),"none":_("None")}

		Label(self,text=_("Static analysis")).grid(row=row,column=1,sticky=W)
		analysis_bot = StringVar()
		analysis_bot.set(value[grp_config.get(bot,"AnalysisBot")])
		OptionMenu(self,analysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis")).grid(row=row,column=1,sticky=W)
		liveanalysis_bot = StringVar()
		liveanalysis_bot.set(value[grp_config.get(bot,"LiveAnalysisBot")])
		OptionMenu(self,liveanalysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis as black or white")).grid(row=row,column=1,sticky=W)
		liveplayer_bot = StringVar()
		liveplayer_bot.set(value[grp_config.get(bot,"LivePlayerBot")])
		OptionMenu(self,liveplayer_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("When opening a position for manual play")).grid(row=row,column=1,sticky=W)
		review_bot = StringVar()
		review_bot.set(value[grp_config.get(bot,"ReviewBot")])
		OptionMenu(self,review_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		

		self.SlowCommand=SlowCommand
		self.SlowParameters=SlowParameters
		self.SlowTimePerMove=SlowTimePerMove
		self.FastCommand=FastCommand
		self.FastParameters=FastParameters
		self.FastTimePerMove=FastTimePerMove
		
		self.analysis_bot=analysis_bot
		self.liveanalysis_bot=liveanalysis_bot
		self.liveplayer_bot=liveplayer_bot
		self.review_bot=review_bot

	def save(self):
		bot=self.name
		log("Saving "+bot+" settings")
		
		grp_config.set(bot,"SlowCommand",self.SlowCommand.get())
		grp_config.set(bot,"SlowParameters",self.SlowParameters.get())
		grp_config.set(bot,"SlowTimePerMove",self.SlowTimePerMove.get())
		grp_config.set(bot,"FastCommand",self.FastCommand.get())
		grp_config.set(bot,"FastParameters",self.FastParameters.get())
		grp_config.set(bot,"FastTimePerMove",self.FastTimePerMove.get())

		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		grp_config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		grp_config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		grp_config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		grp_config.set(bot,"ReviewBot",value[self.review_bot.get()])

		if self.parent.parent.refresh!=None:
			self.parent.parent.refresh()

class LeelaOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
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

		top = Application()
		bot=Leela
		
		slowbot=bot
		slowbot['profile']="slow"
		fastbot=dict(bot)
		fastbot['profile']="fast"
		popup=RangeSelector(top,filename,bots=[slowbot, fastbot])
		top.add_popup(popup)
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation=", "profil="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		app=None
		batch=[]
		
		for filename in parameters[1]:
			move_selection,intervals,variation,komi,nogui,profil=parse_command_line(filename,parameters[0])
			if nogui:
				log("File to analyse:",filename)
				popup=RunAnalysis("no-gui",filename,move_selection,intervals,variation-1,komi,profil)
				popup.terminate_bot()
			else:
				if not app:
					app = Application()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi,profil]
				batch.append(one_analysis)
		
		if not nogui:
			app.after(100,lambda: batch_analysis(app,batch))
			app.mainloop()
