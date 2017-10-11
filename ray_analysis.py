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


import time, os
import threading
import ttk

import toolbox
from toolbox import *




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
	
	def initialize(self):
		
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
			return
		
		if not ray_command_line:
			show_error("The config.ini file does not contain command line for Ray!")
			return
		try:
			ray_command_line=[Config.get("Ray", "Command")]+Config.get("Ray", "Parameters").split()
			ray=gtp(ray_command_line)
			#ray=gtp(tuple(ray_command_line.split()))
		except:
			show_error("Could not run Ray using the command from config.ini file: \n"+" ".join(ray_command_line))
			return
		
		try:
			self.bot_name=ray.name()
		except Exception, e:
			show_error("Ray did not replied as expected to the GTP name command:\n"+str(e))
			return
		
		if self.bot_name!="Ray":
			show_error("Ray did not identified itself as expected:\n'Ray' != '"+self.bot_name+"'")
			return
		
		try:
			self.bot_version=ray.version()
		except Exception, e:
			show_error("Ray did not replied as expected to the GTP version command:\n"+str(e))
			return
		
		try:
			ray.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return

		ray.reset()
		self.ray=ray
		
		#self.time_per_move=int(Config.get("Ray", "TimePerMove"))
		self.time_per_move=0
		#ray.set_time(main_time=self.time_per_move,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		self.move_zero=self.g.get_root()
		komi=self.g.get_komi()
		ray.komi(komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		
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
						
			
		self.max_move=get_moves_number(self.move_zero)
		if not self.move_range:
			self.move_range=range(1,self.max_move+1)
		#if 1 in self.move_range:
		#	self.move_range.remove(1)
			
		self.total_done=0
		
		root = self
		root.parent.title('GoReviewPartner')
		root.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		
		Label(root,text="Analysis of: "+os.path.basename(self.filename)).pack()
		

		remaining_s=len(self.move_range)*self.time_per_move
		remaining_h=remaining_s/3600
		remaining_s=remaining_s-3600*remaining_h
		remaining_m=remaining_s/60
		remaining_s=remaining_s-60*remaining_m
		
		self.lab1=Label(root)
		self.lab1.pack()
		
		self.lab2=Label(root)
		self.lab2.pack()
		
		self.lab1.config(text="Currently at move 1/"+str(self.max_move))
		if self.time_per_move<>0:
			self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()

		current_move=1
		
		try:
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
		except Exception,e:
			show_error(str(e))
			self.lab1.config(text="Aborted")
			self.lab2.config(text="")
			return

		self.lock2.acquire()
		self.t0=time.time()
		first_move=go_to_move(self.move_zero,1)
		first_comment="Analysis by GoReviewPartner"
		first_comment+="\nBot: "+self.bot_name+'/'+self.bot_version
		first_comment+="\nIntervals: "+self.intervals
		first_move.add_comment_text(first_comment)
		threading.Thread(target=self.run_all_analysis).start()
		
		self.root=root
		root.after(500,self.follow_analysis)
		








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
	




