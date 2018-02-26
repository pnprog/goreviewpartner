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


class AQAnalysis():
	
	def win_rate(self,current_move,value,roll):
		return roll
		#see discussion at https://github.com/ymgaq/AQ/issues/20
		if current_move<=160:
			lmbd=0.8
		else:
			lmbd=0.8-min(0.3,max(0.0,(current_move-160)/600))
		rate=lmbd*value+(1-lmbd)*roll
		return rate
	
	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		aq=self.aq
		log()
		log("==============")
		log("move",str(current_move))
		
		additional_comments=""
		if player_color in ('w',"W"):
			log("AQ plays white")
			answer=aq.play_white()
		else:
			log("AQ plays black")
			answer=aq.play_black()
		
		if current_move>1:
			es=aq.final_score()
			one_move.set("ES",es)
		
		log("AQ preferred move:",answer)
		all_moves=aq.get_all_aq_moves()
		
		if (answer.lower() not in ["pass","resign"]):
			one_move.set("CBM",answer.lower()) #Computer Best Move
			best_move=True

			log("Number of alternative sequences:",len(all_moves))
			#log(all_moves)
			
			#for sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes in all_moves:
			for sequence_first_move,count,value,roll,prob,one_sequence in all_moves[:self.maxvariations]:
				log("Adding sequence starting from",sequence_first_move)
				previous_move=one_move.parent
				current_color=player_color
				
				one_score=self.win_rate(current_move,value,roll)

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
					else:
						black_win_rate=str(100-one_score)+'%'
						white_win_rate=str(one_score)+'%'
						
					if first_variation_move:
						first_variation_move=False
						variation_comment=_("black/white win probability for this variation: ")+black_win_rate+'/'+white_win_rate
						new_child.set("BWR",black_win_rate) #Black Win Rate
						new_child.set("WWR",white_win_rate) #White Win Rate
						new_child.set("BWWR",black_win_rate+"/"+white_win_rate)
						
						variation_comment+="\nCount: "+str(count)
						new_child.set("PLYO",str(count))
						
						variation_comment+="\nValue: "+str(value)
						variation_comment+="\nRoll: "+str(roll)
						variation_comment+="\nProb: "+str(prob)+"%"
						#new_child.set("PNV",str(prob)+"%")
						
						new_child.add_comment_text(variation_comment)
						
					if best_move:
						
						best_move=False
						additional_comments+=(_("%s black/white win probability for this position: ")%"AQ")+black_win_rate+'/'+white_win_rate
						one_move.set("BWR",black_win_rate) #Black Win Rate
						one_move.set("WWR",white_win_rate) #White Win Rate
						one_move.set("BWWR",black_win_rate+"/"+white_win_rate)
						
					previous_move=new_child
					if current_color in ('w','W'):
						current_color='b'
					else:
						current_color='w'
			log("==== no more sequences =====")
			aq.undo()
		else:
			log('adding "'+answer.lower()+'" to the sgf file')
			additional_comments+="\n"+_("For this position, %s would %s"%("AQ",answer.lower()))
			if answer.lower()=="pass":
				aq.undo()
			elif answer.lower()=="resign":
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
		
		one_move.add_comment_text(additional_comments)
		
		return answer
		
	def initialize_bot(self):
		aq=aq_starting_procedure(self.g,self.profile)
		self.aq=aq
		self.time_per_move=0
		return aq

def aq_starting_procedure(sgf_g,profile="slow",silentfail=False):
	return bot_starting_procedure("AQ","AQ",AQ_gtp,sgf_g,profile,silentfail)


class RunAnalysis(AQAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(AQAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)

import ntpath
import subprocess
import threading, Queue

class AQ_gtp(gtp):
	
	def quit(self):
		self.write('\x03')
	
	def __init__(self,command):
		self.c=1
		
		aq_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		log("AQ working directory:",aq_working_directory)

		self.process=subprocess.Popen(command,cwd=aq_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		
		self.stderr_queue=Queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()

		self.history=[]
	
	def place_black(self,move):
		self.write("play black "+move)
		answer=self.readline()
		if answer[0]=="=":
			self.history.append(["b",move])
			return True
		else:return False	
	
	def place_white(self,move):
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
			move=answer.split(" ")[1]
			if move.lower()!="resign":
				self.history.append(["b",move])
			return move
		except Exception, e:
			raise GtpException("GtpException in genmove_black()\nanswer='"+answer+"'\n"+str(e))

		
	def play_white(self):
		self.write("genmove white")
		answer=self.readline().strip()
		try:
			move=answer.split(" ")[1]
			if move.lower()!="resign":
				self.history.append(["w",move])
			return move
		except Exception, e:
			raise GtpException("GtpException in genmove_white()\nanswer='"+answer+"'\n"+str(e))


	def undo(self):
		self.write("clear_board")
		answer=self.readline()
		try:
			if answer[0]!="=":
				return False
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
			raise GtpException("GtpException in undo()\n"+str(e))


	def get_all_aq_moves_old(self):
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()

		answers=[]
		for err_line in buff:
			if "total games=" in err_line:
				v1,v2=[int(v) for v in err_line.split("=")[-1].replace(")","").split("(")]
				if v2!=0:
					log("Computing requirement margin: "+str(int(100.*v1/v2)-100)+"%")
				if v1<v2:
					log("=======================================================")
					log("=== WARNING: AQ thinking time seems to be too low ! ===")
					log("=======================================================")
				elif v1==0 and v2==0:
					log("===============================================================================")
					log("=== WARNING: AQ thinking time IS too low for the analysis to be performed ! ===")
					log("===============================================================================")
					log("\a") #let's make this annoying enough :)
			if ("->" in err_line) and ('|' in err_line):
				log(err_line)
				sequence=err_line.split("|")[-1].strip()
				sequence=sequence.replace(" ","")
				sequence=sequence.replace("\t","")
				sequence=sequence.replace("->"," ")
				
				err_line=err_line.replace("|"," ")
				err_line=err_line.strip().split()
				#print err_line.strip().split()
				one_answer=err_line[0]
				count=err_line[1]
				try:
					value=float(err_line[2])
				except:
					value=0.0
				roll=err_line[3]
				prob=err_line[4]
				depth=err_line[5]

				if sequence:
					answers=[[one_answer,int(count),value,float(roll),float(prob),sequence]]+answers

		return answers



	def get_all_aq_moves(self):
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()

		answers=[]
		for err_line in buff:
			#log(err_line)
			if "total games=" in err_line:
				v1,v2=[int(v) for v in err_line.split("=")[-1].replace(")","").split("(")]
				if v2!=0:
					log("Computing requirement margin: "+str(int(100.*v1/v2)-100)+"%")
				if v1<v2:
					log("=======================================================")
					log("=== WARNING: AQ thinking time seems to be too low ! ===")
					log("=======================================================")
				elif v1==0 and v2==0:
					log("===============================================================================")
					log("=== WARNING: AQ thinking time IS too low for the analysis to be performed ! ===")
					log("===============================================================================")
					log("\a") #let's make this annoying enough :)
			if ("->" in err_line) and ('|' in err_line):
				log(err_line)
				sequence=err_line.split("|")[-1].strip()
				sequence=sequence.replace(" ","")
				sequence=sequence.replace("\t","")
				sequence=sequence.replace("->"," ")
				
				err_line=err_line.replace("|"," ")
				err_line=err_line.strip().split()
				#print err_line.strip().split()
				one_answer=err_line[0]
				count=err_line[1]
				try:
					value=float(err_line[2])
				except:
					value=0.0
				roll=err_line[3]
				prob=err_line[4]
				depth=err_line[5]

				if sequence:
					answers=[[one_answer,int(count),value,float(roll),float(prob),sequence]]+answers
		
		return answers


class AQSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		log("Initializing AQ setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		bot="AQ"
		
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
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("See AQ parameters in aq_config.txt")).grid(row=row,column=1,columnspan=2,sticky=W)
		
		self.SlowCommand=SlowCommand
		self.SlowParameters=SlowParameters
		self.FastCommand=FastCommand
		self.FastParameters=FastParameters
		
		self.analysis_bot=analysis_bot
		self.liveanalysis_bot=liveanalysis_bot
		self.liveplayer_bot=liveplayer_bot
		self.review_bot=review_bot
		
	def save(self):
		log("Saving AQ settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		bot="AQ"
		
		Config.set(bot,"SlowCommand",self.SlowCommand.get())
		Config.set(bot,"SlowParameters",self.SlowParameters.get())
		Config.set(bot,"FastCommand",self.FastCommand.get())
		Config.set(bot,"FastParameters",self.FastParameters.get())
		
		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		Config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		Config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		Config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		Config.set(bot,"ReviewBot",value[self.review_bot.get()])
		
		Config.write(open(config_file,"w"))




class AQOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='AQ'
		self.my_starting_procedure=leela_zero_starting_procedure

AQ={}
AQ['name']="AQ"
AQ['gtp_name']="AQ"
AQ['analysis']=AQAnalysis
AQ['openmove']=AQOpenMove
AQ['settings']=AQSettings
AQ['gtp']=AQ_gtp
AQ['liveanalysis']=LiveAnalysis
AQ['runanalysis']=RunAnalysis
AQ['starting']=aq_starting_procedure

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
		bot=AQ
		
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

