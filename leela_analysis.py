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
		if player_color in ('w',"W"):
			log("leela play white")
			answer=leela.play_white()
		else:
			log("leela play black")
			answer=leela.play_black()
		nb_undos=1 #let's remember to undo that move from Leela
		
		best_answer=answer
		
		#all_moves=leela.get_all_leela_moves()
		position_evaluation=leela.get_all_leela_moves()

		if "estimated score" in position_evaluation:
			one_move.set("ES",position_evaluation["estimated score"])
			
		if (answer.lower() not in ["pass","resign"]):
			
			one_move.set("CBM",answer.lower()) #Computer Best Move
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
					new_child.set_move(current_color,(i,j))
					
					if first_variation_move==True:
						first_variation_move=False
						variation_comment=""
			
						if 'win rate' in variation:
							if player_color=='b':
								black_value=variation['win rate']
								white_value=opposite_rate(black_value)
							else:
								white_value=variation['win rate']
								black_value=opposite_rate(white_value)
							new_child.set("BWR",black_value)
							new_child.set("WWR",white_value)
							new_child.set("BWWR",black_value+'/'+white_value)
							variation_comment=_("black/white win probability for this variation: ")+black_value+'/'+white_value+"\n"
							
							if best_move:
								one_move.set("BWR",black_value)
								one_move.set("WWR",white_value)
								one_move.set("BWWR",black_value+'/'+white_value)
								additional_comments+=(_("%s black/white win probability for this position: ")%"Leela")+black_value+'/'+white_value+"\n"
								
						if 'monte carlo win rate' in variation:
							if player_color=='b':
								black_value=variation['monte carlo win rate']
								white_value=opposite_rate(black_value)
							else:
								white_value=variation['monte carlo win rate']
								black_value=opposite_rate(white_value)
							new_child.set("BMCWR",black_value)
							new_child.set("WMCWR",white_value)
							new_child.set("MCWR",black_value+'/'+white_value)
							variation_comment+=_("Monte Carlo win probalbility for this move: ")+black_value+'/'+white_value+"\n"
							if best_move:
								one_move.set("BMCWR",black_value)
								one_move.set("WMCWR",white_value)
								one_move.set("MCWR",black_value+'/'+white_value)
							
						if 'value network win rate' in variation:
							if player_color=='b':
								black_value=variation['value network win rate']
								white_value=opposite_rate(black_value)
							else:
								white_value=variation['value network win rate']
								black_value=opposite_rate(white_value)
							new_child.set("BVNWR",black_value)
							new_child.set("WVNWR",white_value)
							new_child.set("VNWR",black_value+'/'+white_value)
							variation_comment+=_("Value network black/white win probability for this move: ")+black_value+'/'+white_value+"\n"

						if 'move evaluation' in variation:
							new_child.set("EVAL",variation['move evaluation'])
							variation_comment+=_("Evaluation for this move: ")+variation['move evaluation']+"\n"
							
						if 'rapid action value estimation' in variation:
							new_child.set("RAVE",variation['rapid action value estimation'])
							variation_comment+=_("RAVE(x%: y) for this move: ")+variation['rapid action value estimation']+"\n"

						if 'policy network value' in variation:
							new_child.set("PNV",variation['policy network value'])
							variation_comment+=_("Policy network value for this move: ")+variation['policy network value']+"\n"

						if 'playouts' in variation:
							new_child.set("PLYO",variation['playouts'])
							variation_comment+=_("Number of playouts used to estimate this variation: ")+variation['playouts']
						
						if bookmove:
							bookmove=False
							variation_comment+=_("Book move")+"\n"
						
						new_child.add_comment_text(variation_comment)
						
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
				one_move.parent.set("TB",black_influence_points)
			
			if white_influence_points!=[]:
				one_move.parent.set("TW",white_influence_points)	
			
			for u in range(nb_undos):
				leela.undo()
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
				else:
					leela.undo_resign()
					
		one_move.add_comment_text(additional_comments)
		
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

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	leela=bot_starting_procedure("Leela","Leela",Leela_gtp,sgf_g,profile,silentfail)
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
		one_line=self.readline() #empty line
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
		
		all_moves=self.get_all_leela_moves()
		print all_moves[0]
		for e in all_moves[0]:
			print "\t",e
		if answer.lower()=="pass":
			self.undo()
			return _("That game is won")
		elif answer.lower()=="resign":
			self.undo_resign()
			return _("That game is lost")
		else:
			self.undo()
			sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes = all_moves[0]
			if color==1:
				black_win_rate=str(one_score)+'%'
				white_win_rate=str(100-one_score)+'%'
			else:
				black_win_rate=str(100-one_score)+'%'
				white_win_rate=str(one_score)+'%'
			return _("black/white win probability for this variation: ")+black_win_rate+'/'+white_win_rate
			
	def undo_resign(self):
		#apparently, Leela consider "resign" as a standard move that need to be undoed the same way as other move 
		self.undo()
		
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
		
		buff.reverse()
		
		answers=[]
		position_evaluation=Position()
		
		for err_line in buff:
			#log(err_line)
			
			if "score=" in err_line:
				position_evaluation["estimated score"]=err_line.split("score=")[1].strip()
			
			if "book moves" in err_line:
				log("book move")
				position_evaluation["book move"]=True
			
			if " ->" in err_line:
				variation=Variation()
				#log(err_line)
				one_answer=err_line.strip().split(" ")[0]
				variation["first move"]=one_answer
				one_score=err_line.split()[4][:-1]
				nodes=err_line.strip().split("(")[0].split("->")[1].replace(" ","")
				variation["playouts"]=nodes
				monte_carlo=err_line.split("(U:")[1].split('%)')[0].strip()+"%"
				variation["monte carlo win rate"]=monte_carlo
				if self.size==19:
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
					position_evaluation['variations']=[variation]+position_evaluation['variations']
		
		return position_evaluation



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
		SlowCommand.set(Config.get(bot,"SlowCommand"))
		Entry(self, textvariable=SlowCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		SlowParameters = StringVar()
		SlowParameters.set(Config.get(bot,"SlowParameters"))
		Entry(self, textvariable=SlowParameters, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		SlowTimePerMove = StringVar()
		SlowTimePerMove.set(Config.get(bot,"SlowTimePerMove"))
		Entry(self, textvariable=SlowTimePerMove, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Fast profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		FastCommand = StringVar()
		FastCommand.set(Config.get(bot,"FastCommand"))
		Entry(self, textvariable=FastCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		FastParameters = StringVar() 
		FastParameters.set(Config.get(bot,"FastParameters"))
		Entry(self, textvariable=FastParameters, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row,column=1,sticky=W)
		FastTimePerMove = StringVar() 
		FastTimePerMove.set(Config.get(bot,"FastTimePerMove"))
		Entry(self, textvariable=FastTimePerMove, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("%s availability")%bot).grid(row=row,column=1,sticky=W)
		row+=1
		
		value={"slow":_("Slow profile"),"fast":_("Fast profile"),"both":_("Both profiles"),"none":_("None")}

		Label(self,text=_("Static analysis")).grid(row=row,column=1,sticky=W)
		analysis_bot = StringVar()
		analysis_bot.set(value[Config.get(bot,"AnalysisBot")])
		OptionMenu(self,analysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis")).grid(row=row,column=1,sticky=W)
		liveanalysis_bot = StringVar()
		liveanalysis_bot.set(value[Config.get(bot,"LiveAnalysisBot")])
		OptionMenu(self,liveanalysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis as black or white")).grid(row=row,column=1,sticky=W)
		liveplayer_bot = StringVar()
		liveplayer_bot.set(value[Config.get(bot,"LivePlayerBot")])
		OptionMenu(self,liveplayer_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("When opening a position for manual play")).grid(row=row,column=1,sticky=W)
		review_bot = StringVar()
		review_bot.set(value[Config.get(bot,"ReviewBot")])
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
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set(bot,"SlowCommand",self.SlowCommand.get())
		Config.set(bot,"SlowParameters",self.SlowParameters.get())
		Config.set(bot,"SlowTimePerMove",self.SlowTimePerMove.get())
		Config.set(bot,"FastCommand",self.FastCommand.get())
		Config.set(bot,"FastParameters",self.FastParameters.get())
		Config.set(bot,"FastTimePerMove",self.FastTimePerMove.get())

		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		Config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		Config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		Config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		Config.set(bot,"ReviewBot",value[self.review_bot.get()])
		

		Config.write(open(config_file,"w"))




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
		top = Tk()
		bot=Leela
		
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

