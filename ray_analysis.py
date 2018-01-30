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


import os
import threading
import ttk

from toolbox import *
from toolbox import _

from time import time


class RunAnalysis(RunAnalysisBase):

	def run_analysis(self,current_move):
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		ray=self.ray
		
		max_move=self.max_move
		log()
		linelog("move",str(current_move)+'/'+str(max_move))
		
		additional_comments="Move "+str(current_move)
		if player_color in ('w',"W"):
			additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
			log("ray play white")
			answer=ray.get_ray_stat("white")
		else:
			additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))
			log("ray play black")
			answer=ray.get_ray_stat("black")

		log(len(answer),"sequences")

		if len(answer)>0:
			best_move=True
			for sequence_first_move,count,simulation,policy,value,win,one_sequence in answer[:self.maxvariations]:
				log("Adding sequence starting from",sequence_first_move)
				previous_move=one_move.parent
				current_color=player_color
				one_sequence=player_color+' '+sequence_first_move+' '+one_sequence
				one_sequence=one_sequence.replace("b ",',b')
				one_sequence=one_sequence.replace("w ",',w')
				one_sequence=one_sequence.replace(" ",'')
				#log("one_sequence=",one_sequence[1:])
				first_variation_move=True
				for one_deep_move in one_sequence.split(',')[1:]:
					if one_deep_move.lower() in ["pass","resign"]:
						log("Leaving the variation when encountering",one_deep_move.lower())
						break
					current_color=one_deep_move[0]
					one_deep_move=one_deep_move[1:].strip()
					if one_deep_move.lower()!="pass":
						i,j=gtp2ij(one_deep_move)
						new_child=previous_move.new_child()
						new_child.set_move(current_color,(i,j))
						if first_variation_move:
							variation_comment=''
							if win:
								if current_color=='b':
									variation_comment+=_("black/white win probability for this variation: ")+str(win)+'%/'+str(100-float(win))+'%'
									new_child.set("BWR",str(win)+'%') #Black Win Rate
									new_child.set("WWR",str(100-float(win))+'%') #White Win Rate
								else:
									variation_comment+=_("black/white win probability for this variation: ")+str(100-float(win))+'%/'+str(win)+'%'
									new_child.set("WWR",str(win)+'%') #White Win Rate
									new_child.set("BWR",str(100-float(win))+'%') #Black Win Rate
							if count:
								variation_comment+="\nCount: "+count
							if simulation:
								variation_comment+="\nSimulation: "+simulation
							if policy:
								variation_comment+="\nPolicy: "+policy
							if value:
								variation_comment+="\nValue: "+value
							if best_move and win:
								#log("===BWR/WWR",win)
								best_move=False
								one_move.set("CBM",one_deep_move.lower())
								if current_color=='b':
									one_move.set("BWR",str(win)+'%') #Black Win Rate
									one_move.set("WWR",str(100-float(win))+'%') #White Win Rate
								else:
									one_move.set("WWR",str(win)+'%') #White Win Rate
									one_move.set("BWR",str(100-float(win))+'%') #Black Win Rate
								#log("===BWR/WWR")
							new_child.add_comment_text(variation_comment.strip())
						previous_move=new_child
					else:
						break

			log("==== no more sequences =====")
			
		else:
			log('adding "'+answer.lower()+'" to the sgf file')
			additional_comments+="\n"+_("For this position, %s would %s"%("Ray",answer.lower()))
			if answer.lower()=="pass":
				ray.undo()
			elif answer.lower()=="resign":
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
		
		one_move.add_comment_text(additional_comments)


	
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

		ray=bot_starting_procedure("Ray","Rayon",Ray_gtp,self.g)
		self.ray=ray
		self.time_per_move=0

		log("Ray initialization completed")
		return ray

class Ray_gtp(gtp):
	def __init__(self,command):
		gtp.__init__(self,command)
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
	
	def get_ray_stat(self,color):
		t0=time()
		self.write("ray-stat "+color)
		header_line=self.readline()
		log(">>>>>>>>>>>>",time()-t0)
		log("HEADER:",header_line)
		sequences=[]
		
		for i in range(10):
			one_line=answer=self.process.stdout.readline().strip()
			if one_line.strip()=="":
				break
			log("\t",[s.strip() for s in one_line.split("|")[1:]])
			sequences.append([s.strip() for s in one_line.split("|")[1:]])
		
		return sequences



class RaySettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		log("Initializing Ray setting interface")
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		row=0
		Label(self,text=_("%s settings")%"Ray", font="-weight bold").grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		Command = StringVar() 
		Command.set(Config.get("Ray","Command"))
		Entry(self, textvariable=Command, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		Parameters = StringVar() 
		Parameters.set(Config.get("Ray","Parameters"))
		Entry(self, textvariable=Parameters, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		NeededForReview = BooleanVar(value=Config.getboolean('Ray', 'NeededForReview'))
		Cbutton=Checkbutton(self, text=_("Needed for review"), variable=NeededForReview,onvalue=True,offvalue=False)
		Cbutton.grid(row=row,column=1,sticky=W)
		Cbutton.var=NeededForReview
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		ReviewCommand = StringVar() 
		ReviewCommand.set(Config.get("Ray","ReviewCommand"))
		Entry(self, textvariable=ReviewCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		ReviewParameters = StringVar() 
		ReviewParameters.set(Config.get("Ray","ReviewParameters"))
		Entry(self, textvariable=ReviewParameters, width=30).grid(row=row,column=2)

		
		self.Command=Command
		self.Parameters=Parameters
		self.NeededForReview=NeededForReview
		self.ReviewCommand=ReviewCommand
		self.ReviewParameters=ReviewParameters
	
	def save(self):
		log("Saving Ray settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set("Ray","Command",self.Command.get())
		Config.set("Ray","Parameters",self.Parameters.get())
		Config.set("Ray","NeededForReview",self.NeededForReview.get())
		Config.set("Ray","ReviewCommand",self.ReviewCommand.get())
		Config.set("Ray","ReviewParameters",self.ReviewParameters.get())
		
		Config.write(open(config_file,"w"))


class RayOpenMove(BotOpenMove):
	def __init__(self,dim,komi):
		BotOpenMove.__init__(self)
		self.name='Ray'
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)

		if Config.getboolean('Ray', 'NeededForReview'):
			self.okbot=True
			try:
				ray_command_line=[Config.get("Ray", "ReviewCommand")]+Config.get("Ray", "ReviewParameters").split()
				ray=Ray_gtp(ray_command_line)
				ok=ray.boardsize(dim)
				ray.reset()
				ray.komi(komi)
				self.bot=ray
				if not ok:
					raise AbortedException("Boardsize value rejected by "+self.name)
			except Exception, e:
				log("Could not launch "+self.name)
				log(e)
				self.okbot=False
		else:
			self.okbot=False

	"""
	def undo(self):
		if self.okbot:
			#ray cannot undo...
			self.config(state='disabled')
			#self.bot.undo()
	"""



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
		RangeSelector(top,filename,bots=[("Ray",RunAnalysis)]).pack()
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
				app=RunAnalysis(None,filename,move_selection,intervals,variation-1,komi)
				app.terminate_bot()
			else:
				if not top:
					top = Tk()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi]
				batch.append(one_analysis)
		
		if not nogui:
			top.after(1,lambda: batch_analysis(top,batch))
			top.mainloop()
