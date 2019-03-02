# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
import sys
from Tkinter import *
from time import sleep
import threading
from toolbox import *
from toolbox import _

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

		if (answer not in ["PASS","RESIGN"]):
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

					if one_deep_move in ["PASS","RESIGN"]:
						log("Leaving the variation when encountering",one_deep_move)
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
			log('adding "'+answer+'" to the sgf file')
			aq.undo()


		return answer

	def initialize_bot(self):
		aq=aq_starting_procedure(self.g,self.profile)
		self.aq=aq
		self.time_per_move=0
		return aq

def aq_starting_procedure(sgf_g,profile,silentfail=False):
	return bot_starting_procedure("AQ","AQ",AQ_gtp,sgf_g,profile,silentfail)


class RunAnalysis(AQAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

class LiveAnalysis(AQAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile):
		LiveAnalysisBase.__init__(self,g,filename,profile)

import ntpath
import subprocess
import Queue

class AQ_gtp(gtp):

	def quit(self):
		self.write('\x03')

	def __init__(self,command):
		self.c=1
		aq_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		self.command_line=command[0]+" "+" ".join(command[1:])
		command=[c.encode(sys.getfilesystemencoding()) for c in command]
		aq_working_directory=aq_working_directory.encode(sys.getfilesystemencoding())
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
			self.play_white()
		else:
			self.play_black()
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

class AQSettings(BotProfiles):
	def __init__(self,parent,bot="AQ"):
		Frame.__init__(self,parent)
		self.parent=parent
		self.bot=bot
		self.profiles=get_bot_profiles(bot,False)
		profiles_frame=self
		
		self.listbox = Listbox(profiles_frame)
		self.listbox.grid(column=10,row=10,rowspan=10)
		self.update_listbox()
		
		row=10
		Label(profiles_frame,text=_("Profile")).grid(row=row,column=11,sticky=W)
		self.profile = StringVar()
		Entry(profiles_frame, textvariable=self.profile, width=30).grid(row=row,column=12)

		row+=1
		Label(profiles_frame,text=_("Command")).grid(row=row,column=11,sticky=W)
		self.command = StringVar() 
		Entry(profiles_frame, textvariable=self.command, width=30).grid(row=row,column=12)
		
		row+=1
		Label(profiles_frame,text=_("Parameters")).grid(row=row,column=11,sticky=W)
		self.parameters = StringVar() 
		Entry(profiles_frame, textvariable=self.parameters, width=30).grid(row=row,column=12)

		row+=10
		buttons_frame=Frame(profiles_frame)
		buttons_frame.grid(row=row,column=10,sticky=W,columnspan=3)
		Button(buttons_frame, text=_("Add profile"),command=self.add_profile).grid(row=row,column=1,sticky=W)
		Button(buttons_frame, text=_("Modify profile"),command=self.modify_profile).grid(row=row,column=2,sticky=W)
		Button(buttons_frame, text=_("Delete profile"),command=self.delete_profile).grid(row=row,column=3,sticky=W)
		Button(buttons_frame, text=_("Test"),command=lambda: self.parent.parent.test(self.bot_gtp,self.command,self.parameters)).grid(row=row,column=4,sticky=W)
		
		self.listbox.bind("<Button-1>", lambda e: self.after(100,self.change_selection))

		row+=1
		Label(buttons_frame,text="").grid(row=row,column=1)
		row+=1
		Label(buttons_frame,text=_("See AQ parameters in \"aq_config.txt\"")).grid(row=row,column=1,columnspan=2,sticky=W)
		
		self.index=-1
		
		self.bot_gtp=AQ_gtp


class AQOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
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
	main(AQ)
