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

import tkMessageBox


class RunAnalysis(RunAnalysisBase):

	def run_analysis(self,current_move):
		
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		leela=self.leela
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			linelog("move",str(current_move)+'/'+str(max_move))
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)

			if player_color in ('w',"W"):
				log("leela play white")
				answer=leela.play_white()
			else:
				log("leela play black")
				answer=leela.play_black()

			
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
				log("====move",current_move+1,all_moves[0],'~',answer)
				
				
				#making sure the first line of play is more than one move deep
				best_winrate=all_moves[0][2]
				while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]):	
					log("going deeper for first line of play (",nb_undos,")")

					if player_color in ('w',"W") and nb_undos%2==0:
						answer=leela.play_white()
					elif player_color in ('w',"W") and nb_undos%2==1:
						answer=leela.play_black()
					elif player_color not in ('w',"W") and nb_undos%2==0:
						answer=leela.play_black()
					else:
						answer=leela.play_white()
					nb_undos+=1
					

					

					linelog(all_moves[0],'+',answer)
					all_moves2=leela.get_all_leela_moves()
					if (answer.lower() not in ["pass","resign"]):
						
						log("all_moves2:",all_moves2)
						if all_moves2==[]:
							all_moves2=[[answer,answer,666,666,666,666,666,666,666]]

						log('+',all_moves2)
						all_moves[0][1]+=" "+all_moves2[0][1]
						
						
						if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
							all_moves[0][2]=all_moves2[0][2]
						else:
							all_moves[0][2]=100-all_moves2[0][2]

					else:
						log()
						log("last play on the fist of play was",answer,"so leaving")
				
				for u in range(nb_undos):
					log("undo...")
					leela.undo()
				
				
				#all_moves[0][2]=best_winrate #it would be best to sort again all variation based on new winrate...
				

				best_move=True
				#variation=-1
				log("Number of alternative sequences:",len(all_moves))
				log(all_moves)
				for sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes in all_moves:
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
						#new_child.add_comment_text("black/white win probability: "+str(one_score)+'%/'+str(100-one_score)+'%')
						
						
						if player_color=='b':
							if first_variation_move:
								first_variation_move=False
								if not bookmove:
									variation_comment="black/white win probability for this variation: "+str(one_score)+'%/'+str(100-one_score)+'%'
									variation_comment+="\nMonte Carlo win probalbility for this move: "+str(one_monte_carlo)+'%/'+str(100-one_monte_carlo)
									if one_value_network!=None:
										variation_comment+="\nValue network win probalbility for this move: "+str(one_value_network)+'%/'+str(100-one_value_network)
									if one_policy_network!=None:
										variation_comment+="\nPolicy network value for this move: "+str(one_policy_network)+'%'
									if one_evaluation!=None:
										variation_comment+="\nEvaluation for this move: "+str(one_evaluation)+'%'
									if one_rave!=None:
										variation_comment+="\nRAVE(x%: y) for this move: "+str(one_rave)+'%'
									variation_comment+="\nNumber of playouts used to estimate this variation: "+str(one_nodes)
									new_child.add_comment_text(variation_comment)
									#new_child.add_comment_text("black/white win probability for this variation: "+str(one_score)+'%/'+str(100-one_score)+'%\nNumber of playouts used to estimate this variation: '+str(one_nodes)+'\nNeural network value for this move: '+str(one_nn)+'%')
								else:
									new_child.add_comment_text("Book move")
							if best_move:
								best_move=False
								if not bookmove:
									additional_comments+="\nLeela black/white win probability for this position: "+str(one_score)+'%/'+str(100-one_score)+'%'
									one_move.set("BWR",str(one_score)+'%') #Black Win Rate
									one_move.set("WWR",str(100-one_score)+'%') #White Win Rate
						else:
							if first_variation_move:
								first_variation_move=False
								if not bookmove:
									variation_comment="black/white win probability for this variation: "+str(100-one_score)+'%/'+str(one_score)+'%'
									variation_comment+="\nMonte Carlo win probalbility for this move: "+str(100-one_monte_carlo)+'%/'+str(one_monte_carlo)
									if one_value_network!=None:
										variation_comment+="\nValue network win probalbility for this move: "+str(100-one_value_network)+'%/'+str(one_value_network)
									if one_policy_network!=None:
										variation_comment+="\nPolicy network value for this move: "+str(one_policy_network)+'%'
									if one_evaluation!=None:
										variation_comment+="\nEvaluation for this move: "+str(one_evaluation)+'%'
									if one_rave!=None:
										variation_comment+="\nRAVE(x%: y) for this move: "+str(one_rave)+'%'
									variation_comment+="\nNumber of playouts used to estimate this variation: "+str(one_nodes)
									new_child.add_comment_text(variation_comment)
									#new_child.add_comment_text("black/white win probability for this variation: "+str(100-one_score)+'%/'+str(one_score)+'%\nNumber of playouts used to estimate this variation: '+str(one_nodes)+'\nNeural network value for this move: '+str(one_nn)+'%')
								else:
									new_child.add_comment_text("Book move")
							if best_move:
								best_move=False
								if not bookmove:
									additional_comments+="\nLeela black/white win probability for this position: "+str(100-one_score)+'%/'+str(one_score)+'%'
									one_move.set("WWR",str(one_score)+'%') #White Win Rate
									one_move.set("BWR",str(100-one_score)+'%') #Black Win Rate
									
						
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
				additional_comments+="\nFor this position, Leela would "+answer.lower()
				if answer.lower()=="pass":
					leela.undo()
			
			
			one_move.add_comment_text(additional_comments)
			
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())

			self.total_done+=1
		else:
			log("Move",current_move,"not in the list of moves to be analysed, skipping")

		linelog("now asking Leela to play the game move:")
		if player_color in ('w',"W"):
			log("white at",ij2gtp(player_move))
			leela.place_white(ij2gtp(player_move))
		else:
			log("black at",ij2gtp(player_move))
			leela.place_black(ij2gtp(player_move))
		log("Analysis for this move is completed")
	
	
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		log("killing leela")
		self.leela.close()
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
			leela_command_line=Config.get("Leela", "Command")
		except:
			show_error("The config.ini file does not contain entry for Leela command line!")
			return
		
		if not leela_command_line:
			show_error("The config.ini file does not contain command line for Leela!")
			return
		try:
			leela_command_line=[Config.get("Leela", "Command")]+Config.get("Leela", "Parameters").split()
			leela=gtp(leela_command_line)
		except:
			show_error("Could not run Leela using the command from config.ini file: \n"+" ".join(leela_command_line))
			return
		
		try:
			self.bot_name=leela.name()
		except Exception, e:
			show_error("Leela did not replied as expected to the GTP name command:\n"+str(e))
			return
		
		if self.bot_name!="Leela":
			show_error("Leela did not identified itself as expected:\n'Leela' != '"+self.bot_name+"'")
			return
		
		try:
			self.bot_version=leela.version()
		except Exception, e:
			show_error("Leela did not replied as expected to the GTP version command:\n"+str(e))
			return
		
		
		try:
			leela.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return

		leela.reset()
		self.leela=leela
		
		self.time_per_move=int(Config.get("Leela", "TimePerMove"))
		leela.set_time(main_time=self.time_per_move,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		leela.komi(self.komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					leela.place_white(move)
				else:
					log("Adding initial black stone at",move)
					leela.place_black(move)
						

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
		RangeSelector(top,filename,bots=[("Leela",RunAnalysis)]).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




