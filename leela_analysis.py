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

from time import sleep
import os
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
			return False
		
		if not leela_command_line:
			show_error("The config.ini file does not contain command line for Leela!")
			return False
		log("Starting Leela...")
		try:
			leela_command_line=[Config.get("Leela", "Command")]+Config.get("Leela", "Parameters").split()
			leela=Leela_gtp(leela_command_line)
		except:
			show_error("Could not run Leela using the command from config.ini file: \n"+" ".join(leela_command_line))
			return False
		log("Leela started")
		log("Leela identification through GTP..")
		try:
			self.bot_name=leela.name()
		except Exception, e:
			show_error("Leela did not replied as expected to the GTP name command:\n"+str(e))
			return False
		
		if self.bot_name!="Leela":
			show_error("Leela did not identified itself as expected:\n'Leela' != '"+self.bot_name+"'")
			return False
		log("Leela identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=leela.version()
		except Exception, e:
			show_error("Leela did not replied as expected to the GTP version command:\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		
		try:
			ok=leela.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return False
		if not ok:
			show_error("Leela rejected this board size ("+str(size)+"x"+str(size)+")")
			return False
		log("Clearing the board")
		leela.reset()
		self.leela=leela
		
		log("Setting time per move")
		self.time_per_move=int(Config.get("Leela", "TimePerMove"))
		leela.set_time(main_time=0,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		
		log("Setting komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		leela.komi(self.komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		log("Adding handicap stones, if any")
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
		log("Leela initialization completed")
		return True


class Leela_gtp(gtp):

	def get_leela_final_score(self):
		self.write("final_score")
		answer=self.readline()
		try:
			return " ".join(answer.split(" ")[1:])
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
		log(buff)
		influence=[]
		for i in range(self.size):
			one_line=buff[i].strip()
			one_line=one_line.replace(".","0").replace("x","1").replace("o","2").replace("O","0").replace("X","0").replace("w","1").replace("b","2")
			one_line=[int(s) for s in one_line.split(" ")]
			influence.append(one_line)
		
		return influence

	def get_all_leela_moves(self):
		buff_size=18
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()
		
		answers=[]
		for err_line in buff:
			if " ->" in err_line:
				log(err_line)
				one_answer=err_line.strip().split(" ")[0]
				one_score= ' '.join(err_line.split()).split(' ')[4]
				nodes=int(err_line.strip().split("(")[0].split("->")[1].replace(" ",""))
				monte_carlo=float(err_line.split("(U:")[1].split('%)')[0].strip())
				
				if self.size==19:
					value_network=float(err_line.split("(V:")[1].split('%')[0].strip())
					policy_network=float(err_line.split("(N:")[1].split('%)')[0].strip())
					evaluation=None
					rave=None
				else:
					value_network=None
					policy_network=None
					evaluation=float(err_line.split("(N:")[1].split('%)')[0].strip())
					rave=err_line.split("(R:")[1].split(')')[0].strip()
				
				
				if one_score!="0.00%)":
					sequence=err_line.split("PV: ")[1].strip()
					answers=[[one_answer,sequence,float(one_score[:-2]),monte_carlo,value_network,policy_network,evaluation,rave,nodes]]+answers

		return answers


class LeelaSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		log("Initializing Leela setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		row=0
		
		Label(self).grid(row=row,column=0)
		Label(self,text="Leela").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		LeelaCommand = StringVar() 
		LeelaCommand.set(Config.get("Leela","Command"))
		Entry(self, textvariable=LeelaCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Parameters").grid(row=row+2,column=1)
		LeelaParameters = StringVar() 
		LeelaParameters.set(Config.get("Leela","Parameters"))
		Entry(self, textvariable=LeelaParameters, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Time per move").grid(row=row+2,column=1)
		TimePerMove = StringVar() 
		TimePerMove.set(Config.get("Leela","TimePerMove"))
		Entry(self, textvariable=TimePerMove, width=30).grid(row=row+2,column=2)
		row+=1
		LeelaNeededForReview = BooleanVar(value=Config.getboolean('Leela', 'NeededForReview'))
		LeelaCheckbutton=Checkbutton(self, text="Needed for review", variable=LeelaNeededForReview,onvalue=True,offvalue=False)
		LeelaCheckbutton.grid(row=row+2,column=1)
		LeelaCheckbutton.var=LeelaNeededForReview

		self.LeelaCommand=LeelaCommand
		self.LeelaParameters=LeelaParameters
		self.TimePerMove=TimePerMove
		self.LeelaNeededForReview=LeelaNeededForReview

	def save(self):
		log("Saving Leela settings")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		Config.set("Leela","Command",self.LeelaCommand.get())
		Config.set("Leela","Parameters",self.LeelaParameters.get())
		Config.set("Leela","TimePerMove",self.TimePerMove.get())
		Config.set("Leela","NeededForReview",self.LeelaNeededForReview.get())
		
		Config.write(open("config.ini","w"))




class LeelaOpenMove(BotOpenMove):
	def __init__(self,parent,dim,komi):
		BotOpenMove.__init__(self,parent)
		self.name='Leela'
		self.configure(text=self.name)
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")

		if Config.getboolean('Leela', 'NeededForReview'):
			self.okbot=True
			try:
				leela_command_line=[Config.get("Leela", "Command")]+Config.get("Leela", "Parameters").split()
				leela=Leela_gtp(leela_command_line)
				ok=leela.boardsize(dim)
				leela.reset()
				leela.komi(komi)
				time_per_move=int(Config.get("Leela", "TimePerMove"))
				leela.set_time(main_time=time_per_move,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				self.bot=leela
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
	




