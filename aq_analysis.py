# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import *

import sys
from time import sleep
import os
import threading
import ttk

from toolbox import *
from toolbox import _

import tkMessageBox


class AQAnalysis():

	def win_rate(self,current_move,value,roll):
		#see discussion at https://github.com/ymgaq/AQ/issues/20
		if current_move<=160:
			lmbd=0.8
		else:
			lmbd=0.8-min(0.3,max(0.0,(current_move-160)/600))
		rate=lmbd*value+(1-lmbd)*roll
		#print "winrate(m=",current_move,",v=",value,",r=",roll,")=",rate
		return rate

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		aq=self.aq
		log()
		log("==============")
		log("move",str(current_move))

		if player_color in ('w',"W"):
			log("AQ plays white")
			answer=aq.play_white()
		else:
			log("AQ plays black")
			answer=aq.play_black()

		if current_move>1:
			es=aq.final_score()
			#one_move.set("ES",es)
			node_set(one_move,"ES",es)

		log("AQ preferred move:",answer)
		node_set(one_move,"CBM",answer) #Computer Best Move

		all_moves=aq.get_all_aq_moves()

		if (answer.lower() not in ["pass","resign"]):
			#one_move.set("CBM",answer.lower()) #Computer Best Move
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
					node_set(new_child,current_color,(i,j))


					if player_color=='b':
						bwwr=str(one_score)+'%/'+str(100-one_score)+'%'
						mcwr=str(roll)+'%/'+str(100-roll)+'%'
						vnwr=str(value)+'%/'+str(100-value)+'%'
					else:
						bwwr=str(100-one_score)+'%/'+str(one_score)+'%'
						mcwr=str(100-roll)+'%/'+str(roll)+'%'
						vnwr=str(100-value)+'%/'+str(value)+'%'

					if first_variation_move:
						first_variation_move=False
						node_set(new_child,"BWWR",bwwr)
						node_set(new_child,"PLYO",str(count))
						node_set(new_child,"VNWR",vnwr)
						node_set(new_child,"MCWR",mcwr)
						node_set(new_child,"PNV",str(prob)+"%")


					if best_move:
						best_move=False
						node_set(one_move,"BWWR",bwwr)
						node_set(one_move,"MCWR",mcwr)
						node_set(one_move,"VNWR",vnwr)
						
					previous_move=new_child
					if current_color in ('w','W'):
						current_color='b'
					else:
						current_color='w'
			log("==== no more sequences =====")
			aq.undo()
		else:
			log('adding "'+answer.lower()+'" to the sgf file')
			aq.undo()


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
		
		if aq_working_directory:
			log("AQ working directory:",aq_working_directory)
			self.process=subprocess.Popen(command,cwd=aq_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		else:
			self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		self.stderr_queue=Queue.Queue()
		self.stdout_queue=Queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()

		self.history=[]
		self.free_handicap_stones=[]

	def quick_evaluation(self,color):
		if color==2:
			answer=self.play_white()
		else:
			answer=self.play_black()
		all_moves=self.get_all_aq_moves()
		self.undo()

		txt=""
		try:
			if color==1:
				black_win_rate=str(all_moves[0][2])+"%"
				white_win_rate=opposite_rate(black_win_rate)
			else:
				white_win_rate=str(all_moves[0][2])+"%"
				black_win_rate=opposite_rate(white_win_rate)
			txt+= variation_data_formating["VNWR"]%(black_win_rate+'/'+white_win_rate)
		except:
			pass

		return txt

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

				if sequence:
					answers=[[one_answer,int(count),value,float(roll),float(prob),sequence]]+answers

		return answers


class AQSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.parent=parent
		log("Initializing AQ setting interface")

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
		SlowCommand.set(grp_config.get(bot,"SlowCommand"))
		Entry(self, textvariable=SlowCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		SlowParameters = StringVar()
		SlowParameters.set(grp_config.get(bot,"SlowParameters"))
		Entry(self, textvariable=SlowParameters, width=30).grid(row=row,column=2)
		row+=1
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(AQ_gtp,"slow")).grid(row=row,column=1,sticky=W)
		
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
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(AQ_gtp,"fast")).grid(row=row,column=1,sticky=W)

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

		bot="AQ"

		grp_config.set(bot,"SlowCommand",self.SlowCommand.get())
		grp_config.set(bot,"SlowParameters",self.SlowParameters.get())
		grp_config.set(bot,"FastCommand",self.FastCommand.get())
		grp_config.set(bot,"FastParameters",self.FastParameters.get())

		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}

		grp_config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		grp_config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		grp_config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		grp_config.set(bot,"ReviewBot",value[self.review_bot.get()])


		if self.parent.parent.refresh!=None:
			self.parent.parent.refresh()


class AQOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='AQ'
		self.my_starting_procedure=aq_starting_procedure

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

		top = Application()
		bot=AQ
		
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
