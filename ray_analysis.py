# -*- coding: utf-8 -*-


from gtp import gtp
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

import toolbox
from toolbox import *

from time import time


class RunAnalysis(RunAnalysisBase):

	def run_analysis(self,current_move):
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		ray=self.ray
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			linelog("move",str(current_move)+'/'+str(max_move))
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)

			if player_color in ('w',"W"):
				log("ray play white")
				#answer=leela.play_white()
				answer=ray.get_ray_stat("white")
			else:
				log("ray play black")
				answer=ray.get_ray_stat("black")
				#answer=leela.play_black()
				
			log("*****************")
			log(len(answer),"sequences")
			
			
			
			#if (answer.lower() not in ["pass","resign"]):
			if len(answer)>0:
				best_move=True
				for sequence_first_move,count,simulation,policy,value,win,one_sequence in answer:
					log("Adding sequence starting from",sequence_first_move)
					previous_move=one_move.parent
					current_color=player_color
					one_sequence=player_color+' '+sequence_first_move+' '+one_sequence
					one_sequence=one_sequence.replace("b ",',b')
					one_sequence=one_sequence.replace("w ",',w')
					one_sequence=one_sequence.replace(" ",'')
					log("one_sequence=",one_sequence[1:])
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
										variation_comment+="black/white win probability for this variation: "+str(win)+'%/'+str(100-float(win))+'%'
									else:
										variation_comment+="black/white win probability for this variation: "+str(100-float(win))+'%/'+str(win)+'%'
								if count:
									variation_comment+="\nCount: "+count
								if simulation:
									variation_comment+="\nSimulation: "+simulation
								if policy:
									variation_comment+="\nPolicy: "+policy
								if value:
									variation_comment+="\nValue: "+value
								if best_move and win:
									log("===BWR/WWR",win)
									best_move=False
									one_move.set("CBM",one_deep_move.lower())
									if current_color=='b':
										one_move.set("BWR",str(win)+'%') #Black Win Rate
										one_move.set("WWR",str(100-float(win))+'%') #White Win Rate
									else:
										one_move.set("WWR",str(win)+'%') #White Win Rate
										one_move.set("BWR",str(100-float(win))+'%') #Black Win Rate
									log("===BWR/WWR")
								new_child.add_comment_text(variation_comment.strip())
							previous_move=new_child
						else:
							break

				log("==== no more sequences =====")
				

				
			else:
				log('adding "'+answer.lower()+'" to the sgf file')
				additional_comments+="\nFor this position, Ray would "+answer.lower()
				if answer.lower()=="pass":
					ray.undo()
			
			
			one_move.add_comment_text(additional_comments)

			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())

			self.total_done+=1
		else:
			log("Move",current_move,"not in the list of moves to be analysed, skipping")

		linelog("now asking Ray to play the game move:")
		if player_color in ('w',"W"):
			log("white at",ij2gtp(player_move))
			ray.place_white(ij2gtp(player_move))
		else:
			log("black at",ij2gtp(player_move))
			ray.place_black(ij2gtp(player_move))
		log("Analysis for this move is completed")
	
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		log("killing ray")
		self.ray.close()
		log("destroying")
		self.destroy()
	
	def initialize_bot(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		
		txt = open(self.filename)
		self.g = sgf.Sgf_game.from_string(clean_sgf(txt.read()))
		txt.close()
		
		leaves=get_all_sgf_leaves(self.g.get_root())
		log("keeping only variation",self.variation)
		keep_only_one_leaf(leaves[self.variation][0])
		
		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size

		try:
			ray_command_line=Config.get("Ray", "Command")
		except:
			show_error("The config.ini file does not contain entry for Ray command line!")
			return False
		
		if not ray_command_line:
			show_error("The config.ini file does not contain command line for Ray!")
			return False
		log("Starting Ray...")
		try:
			ray_command_line=[Config.get("Ray", "Command")]+Config.get("Ray", "Parameters").split()
			ray=Ray_gtp(ray_command_line)
			#ray=gtp(tuple(ray_command_line.split()))
		except:
			show_error("Could not run Ray using the command from config.ini file: \n"+" ".join(ray_command_line))
			return False
		log("Ray started")
		log("Ray identification through GTP...")
		try:
			self.bot_name=ray.name()
		except Exception, e:
			show_error("Ray did not replied as expected to the GTP name command:\n"+str(e))
			return False
		
		if self.bot_name!="Rayon":
			show_error("Ray did not identified itself as expected:\n'Rayon' != '"+self.bot_name+"'")
			return
		log("Ray identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=ray.version()
		except Exception, e:
			show_error("Ray did not replied as expected to the GTP version command:\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		try:
			ok=ray.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return False
		if not ok:
			show_error("Ray rejected this board size ("+str(size)+"x"+str(size)+")")
			return False
		log("Clearing the board")
		ray.reset()
		self.ray=ray
		

		self.time_per_move=0
		
		log("Setting komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		ray.komi(self.komi)

		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		log("Adding handicap stones, if any")
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					ray.place_white(move)
				else:
					log("Adding initial black stone at",move)
					ray.place_black(move)
		log("Ray initialization completed")
		return True


class Ray_gtp(gtp):
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
		Config.read("config.ini")
		
		row=0
		
		Label(self).grid(row=row,column=0)
		Label(self,text="Ray").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		RayCommand = StringVar() 
		RayCommand.set(Config.get("Ray","Command"))
		Entry(self, textvariable=RayCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Parameters").grid(row=row+2,column=1)
		RayParameters = StringVar() 
		RayParameters.set(Config.get("Ray","Parameters"))
		Entry(self, textvariable=RayParameters, width=30).grid(row=row+2,column=2)
		row+=1
		RayNeededForReview = BooleanVar(value=Config.getboolean('Ray', 'NeededForReview'))
		RayCheckbutton=Checkbutton(self, text="Needed for review", variable=RayNeededForReview,onvalue=True,offvalue=False)
		RayCheckbutton.grid(row=row+2,column=1)
		RayCheckbutton.var=RayNeededForReview
		
		self.RayCommand=RayCommand
		self.RayParameters=RayParameters
		self.RayNeededForReview=RayNeededForReview
	
	def save(self):
		log("Saving Ray settings")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		Config.set("Ray","Command",self.RayCommand.get())
		Config.set("Ray","Parameters",self.RayParameters.get())
		Config.set("Ray","NeededForReview",self.RayNeededForReview.get())
		
		Config.write(open("config.ini","w"))


class RayOpenMove(BotOpenMove):
	def __init__(self,parent,dim,komi):
		BotOpenMove.__init__(self,parent)
		self.name='Ray'
		self.configure(text=self.name)
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")

		if Config.getboolean('Ray', 'NeededForReview'):
			self.okbot=True
			try:
				ray_command_line=[Config.get("Ray", "Command")]+Config.get("Ray", "Parameters").split()
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
				self.config(state='disabled')
				self.okbot=False
		else:
			self.okbot=False
			self.config(state='disabled')

	def undo(self):
		if self.okbot:
			#ray cannot undo...
			self.config(state='disabled')
			#self.bot.undo()




if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf', '.sgf')])
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		top = Tk()
		toolbox.RunAnalysis=RunAnalysis
		RangeSelector(top,filename,bots=[("Ray",RunAnalysis)]).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




