# -*- coding: utf-8 -*-


from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import *
import tkFileDialog
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


class RunAnalysis(RunAnalysisBase):
	
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
		player_color,player_move=one_move.get_move()
		aq=self.aq
		max_move=self.max_move
		log()
		log("move",str(current_move)+'/'+str(max_move))
		
		additional_comments="Move "+str(current_move)
		if player_color in ('w',"W"):
			additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
			log("AQ plays white")
			answer=aq.play_white()
		else:
			additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))
			log("AQ plays black")
			answer=aq.play_black()

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
						variation_comment+="\nCount: "+str(count)
						variation_comment+="\nValue: "+str(value)
						variation_comment+="\nRoll: "+str(roll)
						variation_comment+="\nProb: "+str(prob)
						
						new_child.add_comment_text(variation_comment)
						
					if best_move:
						
						best_move=False
						additional_comments+="\n"+(_("%s black/white win probability for this position: ")%"AQ")+black_win_rate+'/'+white_win_rate
						one_move.set("BWR",black_win_rate) #Black Win Rate
						one_move.set("WWR",white_win_rate) #White Win Rate
					
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
		write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
		self.total_done+=1

	
	
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text=_("Now closing, please wait..."))
		self.update_idletasks()
		log("killing AQ")
		self.aq.kill()
		log("destroying")
		self.destroy()
	

	def initialize_bot(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		self.g=open_sgf(self.filename)
		
		leaves=get_all_sgf_leaves(self.g.get_root())
		log("keeping only variation",self.variation)
		keep_only_one_leaf(leaves[self.variation][0])
		
		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size

		log("Setting new komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)

		aq=bot_starting_procedure("AQ","AQ",AQ_gtp,self.g)
		self.aq=aq
		self.time_per_move=0

		log("AQ initialization completed")
		return aq

import ntpath
import subprocess
import threading, Queue

class AQ_gtp(gtp):
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
		
		row=0
		Label(self,text=_("%s settings")%"AQ", font="-weight bold").grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		AQCommand = StringVar() 
		AQCommand.set(Config.get("AQ","Command"))
		Entry(self, textvariable=AQCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		AQParameters = StringVar() 
		AQParameters.set(Config.get("AQ","Parameters"))
		Entry(self, textvariable=AQParameters, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		AQNeededForReview = BooleanVar(value=Config.getboolean('AQ', 'NeededForReview'))
		AQCheckbutton=Checkbutton(self, text=_("Needed for review"), variable=AQNeededForReview,onvalue=True,offvalue=False)
		AQCheckbutton.grid(row=row,column=1,sticky=W)
		AQCheckbutton.var=AQNeededForReview
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		ReviewAQCommand = StringVar() 
		ReviewAQCommand.set(Config.get("AQ","ReviewCommand"))
		Entry(self, textvariable=ReviewAQCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		ReviewAQParameters = StringVar() 
		ReviewAQParameters.set(Config.get("AQ","ReviewParameters"))
		Entry(self, textvariable=ReviewAQParameters, width=30).grid(row=row,column=2)
		
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("See AQ parameters in aq_config.txt")).grid(row=row,column=1,columnspan=2,sticky=W)
		
		
		self.AQCommand=AQCommand
		self.AQParameters=AQParameters
		self.AQNeededForReview=AQNeededForReview
		self.ReviewAQCommand=ReviewAQCommand
		self.ReviewAQParameters=ReviewAQParameters
		
	def save(self):
		log("Saving AQ settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set("AQ","Command",self.AQCommand.get())
		Config.set("AQ","Parameters",self.AQParameters.get())
		Config.set("AQ","NeededForReview",self.AQNeededForReview.get())
		Config.set("AQ","ReviewCommand",self.ReviewAQCommand.get())
		Config.set("AQ","ReviewParameters",self.ReviewAQParameters.get())
		
		
		Config.write(open(config_file,"w"))




class AQOpenMove(BotOpenMove):
	def __init__(self,dim,komi):
		BotOpenMove.__init__(self)
		self.name='AQ'
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)

		if Config.getboolean('AQ', 'NeededForReview'):
			self.okbot=True
			try:
				aq_command_line=[Config.get("AQ", "ReviewCommand")]+Config.get("AQ", "ReviewParameters").split()
				aq=AQ_gtp(aq_command_line)
				ok=aq.boardsize(dim)
				aq.reset()
				aq.komi(komi)

				self.bot=aq
				if not ok:
					raise AbortedException("Boardsize value rejected by "+self.name)
			except Exception, e:
				log("Could not launch "+self.name)
				log(e)
				self.okbot=False
		else:
			self.okbot=False

	def close(self):
		if self.okbot:
			log("killing",self.name)
			self.bot.kill()


if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title=_('Select a file'),filetypes = [('sgf', '.sgf')])
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		top = Tk()
		RangeSelector(top,filename,bots=[("AQ",RunAnalysis)]).pack()
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['range=', 'color=', 'komi=',"variation="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		for filename in parameters[1]:
			log("File to analyse:",filename)
			
			move_selection,intervals,variation,komi=parse_command_line(filename,parameters[0])
			
			top = Tk()
			app=RunAnalysis(top,filename,move_selection,intervals,variation-1,komi)
			app.propose_review=app.close_app
			app.pack()
			top.mainloop()
	




