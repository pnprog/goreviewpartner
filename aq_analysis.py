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
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			linelog("move",str(current_move)+'/'+str(max_move))
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)

			if player_color in ('w',"W"):
				log("AQ plays white")
				answer=aq.play_white()
			else:
				log("AQ plays black")
				answer=aq.play_black()

			
			all_moves=aq.get_all_aq_moves()
			
			if (answer.lower() not in ["pass","resign"]):
				
				one_move.set("CBM",answer.lower()) #Computer Best Move
				
				log("====move",current_move+1,all_moves[0],'~',answer)
				
				#best_winrate=all_moves[0][2]
				
				best_move=True

				log("Number of alternative sequences:",len(all_moves))
				log(all_moves)
				
				#for sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes in all_moves:
				for sequence_first_move,_count,value,roll,_prob,one_sequence in all_moves:
					log("Adding sequence starting from",sequence_first_move)
					previous_move=one_move.parent
					current_color=player_color
					
					one_score=self.win_rate(current_move,value,roll)
					
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

						if player_color=='b':
							if first_variation_move:
								first_variation_move=False
								variation_comment="black/white win probability for this variation: "+str(one_score)+'%/'+str(100-one_score)+'%'
								new_child.add_comment_text(variation_comment)
								
								"""
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
								"""
							if best_move:
								
								best_move=False
								additional_comments+="\nAQ black/white win probability for this position: "+str(one_score)+'%/'+str(100-one_score)+'%'
								one_move.set("BWR",str(one_score)+'%') #Black Win Rate
								one_move.set("WWR",str(100-one_score)+'%') #White Win Rate
						else:
							if first_variation_move:
								first_variation_move=False
								variation_comment="black/white win probability for this variation: "+str(100-one_score)+'%/'+str(one_score)+'%'
								new_child.add_comment_text(variation_comment)
								"""
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
								"""
							if best_move:
								best_move=False
								additional_comments+="\nAQ black/white win probability for this position: "+str(100-one_score)+'%/'+str(one_score)+'%'
								one_move.set("WWR",str(one_score)+'%') #White Win Rate
								one_move.set("BWR",str(100-one_score)+'%') #Black Win Rate
							
						previous_move=new_child
						if current_color in ('w','W'):
							current_color='b'
						else:
							current_color='w'
				log("==== no more sequences =====")
				aq.undo()
			else:
				log('adding "'+answer.lower()+'" to the sgf file')
				additional_comments+="\nFor this position, AQ would "+answer.lower()
				if answer.lower()=="pass":
					aq.undo()
			
			
			one_move.add_comment_text(additional_comments)
			
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())

			self.total_done+=1
		else:
			log("Move",current_move,"not in the list of moves to be analysed, skipping")

		linelog("now asking AQ to play the game move:")
		if player_color in ('w',"W"):
			log("white at",ij2gtp(player_move))
			aq.place_white(ij2gtp(player_move))
		else:
			log("black at",ij2gtp(player_move))
			aq.place_black(ij2gtp(player_move))
		log("Analysis for this move is completed")
	
	
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		log("killing AQ")
		self.aq.kill()
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
			aq_command_line=Config.get("AQ", "Command")
		except:
			show_error("The config.ini file does not contain entry for AQ command line!")
			return False
		
		if not aq_command_line:
			show_error("The config.ini file does not contain command line for AQ!")
			return False
		log("Starting AQ...")
		try:
			aq_command_line=[Config.get("AQ", "Command")]
			aq=AQ_gtp(aq_command_line)
		except Exception, e:
			show_error("Could not run AQ using the command from config.ini file: \n"+" ".join(aq_command_line)+"\n"+str(e))
			return False
		log("AQ started")
		log("AQ identification through GTP..")
		try:
			self.bot_name=aq.name()
		except Exception, e:
			show_error("AQ did not replied as expected to the GTP name command:\n"+str(e))
			return False
		
		if self.bot_name!="AQ":
			show_error("AQ did not identified itself as expected:\n'AQ' != '"+self.bot_name+"'")
			return False
		log("AQ identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=aq.version()
		except Exception, e:
			show_error("AQ did not replied as expected to the GTP version command:\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		
		try:
			ok=aq.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return False
		if not ok:
			show_error("AQ rejected this board size ("+str(size)+"x"+str(size)+")")
			return False
		log("Clearing the board")
		aq.reset()
		self.aq=aq
		
		self.time_per_move=0
		
		#log("Setting time per move")
		#self.time_per_move=int(Config.get("Leela", "TimePerMove"))
		#leela.set_time(main_time=0,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		
		log("Setting komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		aq.komi(self.komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		log("Adding handicap stones, if any")
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					aq.place_white(move)
				else:
					log("Adding initial black stone at",move)
					aq.place_black(move)
		log("AQ initialization completed")
		return True

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
		Config.read("config.ini")
		
		row=0
		
		Label(self).grid(row=row,column=0)
		Label(self,text="AQ").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		AQCommand = StringVar() 
		AQCommand.set(Config.get("AQ","Command"))
		Entry(self, textvariable=AQCommand, width=30).grid(row=row+2,column=2)
		row+=1
		AQNeededForReview = BooleanVar(value=Config.getboolean('AQ', 'NeededForReview'))
		AQCheckbutton=Checkbutton(self, text="Needed for review", variable=AQNeededForReview,onvalue=True,offvalue=False)
		AQCheckbutton.grid(row=row+2,column=1)
		AQCheckbutton.var=AQNeededForReview
		row+=1
		Label(self,text="See AQ parameters in aq_config.txt").grid(row=row+2,column=1,columnspan=2)
		
		
		self.AQCommand=AQCommand
		self.AQNeededForReview=AQNeededForReview

	def save(self):
		log("Saving AQ settings")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		Config.set("AQ","Command",self.AQCommand.get())
		Config.set("AQ","NeededForReview",self.AQNeededForReview.get())
		
		Config.write(open("config.ini","w"))




class AQOpenMove(BotOpenMove):
	def __init__(self,parent,dim,komi):
		BotOpenMove.__init__(self,parent)
		self.name='AQ'
		self.configure(text=self.name)
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")

		if Config.getboolean('AQ', 'NeededForReview'):
			self.okbot=True
			try:
				aq_command_line=[Config.get("AQ", "Command")]
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
				self.config(state='disabled')
				self.okbot=False
		else:
			self.okbot=False
			self.config(state='disabled')

	def close(self):
		if self.okbot:
			log("killing",self.name)
			self.bot.kill()


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
	




