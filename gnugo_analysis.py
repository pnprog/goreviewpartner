# -*- coding: utf-8 -*-


from gtp import gtp
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

#from Tkinter import Tk, Label, Frame, StringVar, Radiobutton, W, E, Entry, END, Button, Toplevel, Button, BOTH
from Tkinter import *
import tkFileDialog
import sys
import os

import ConfigParser


import time, os

import ttk


from toolbox import *

def get_full_sequence_threaded(worker,current_color,deepness):
	sequence=get_full_sequence(worker,current_color,deepness)
	threading.current_thread().sequence=sequence

def get_full_sequence(worker,current_color,deepness):
	try:
		sequence=""
		undos=0
		for d in range(deepness):
			if current_color.lower()=="b":
				answer=worker.play_black()
				current_color="w"
			else:
				answer=worker.play_white()
				current_color="b"
			sequence+=answer+" "
			if answer.lower()=='resign':
				break
			if answer.lower()=='pass':
				undos+=1
				break
			undos+=1
		
		for u in range(undos):
			worker.undo()
		return sequence.strip()
	except Exception, e:
		return e



class RunAnalysis(RunAnalysisBase):

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		gnugo=self.gnugo
		if current_move in self.move_range:
			max_move=self.max_move
			linelog("move",str(current_move)+'/'+str(max_move))
			final_score=gnugo.get_gnugo_estimate_score()
			linelog(final_score)
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)
			additional_comments+="\nGnugo score estimation before the move was played: "+final_score

			if player_color in ('w',"W"):
				log("gnugo plays white")
				top_moves=gnugo.gnugo_top_moves_white()
				answer=gnugo.play_white()
			else:
				log("gnugo plays black")
				top_moves=gnugo.gnugo_top_moves_black()
				answer=gnugo.play_black()

			log("====","Gnugo answer:",answer)
			
			log("==== Gnugo top moves")
			for one_top_move in top_moves:
				log("\t",one_top_move)
			print
			top_moves=top_moves[:self.nb_variations]
			if (answer.lower() not in ["pass","resign"]):
				gnugo.undo()
				
				while len(top_moves)>0:
					all_threads=[]
					for worker in self.workers:
						worker.need_undo=False
						if len(top_moves)>0:
							one_top_move=top_moves.pop(0)
							
							if player_color in ('w',"W"):
								worker.place_white(one_top_move)
								one_thread=threading.Thread(target=get_full_sequence_threaded,args=(worker,'b',self.deepness))
							else:
								worker.place_black(one_top_move)
								one_thread=threading.Thread(target=get_full_sequence_threaded,args=(worker,'w',self.deepness))
							worker.need_undo=True
							one_thread.one_top_move=one_top_move
							one_thread.start()
							all_threads.append(one_thread)
							
					
					for one_thread in all_threads:
						one_thread.join()
					
					for worker in self.workers:
						if worker.need_undo:
							worker.undo()
						
					for one_thread in all_threads:
						if type(one_thread.sequence)!=type("abc"):
							raise AbortedException("GnuGo thread failed:\n"+str(one_thread.sequence))
						
						one_sequence=one_thread.one_top_move+" "+one_thread.sequence
						one_sequence=one_sequence.strip()
						log(">>>>>>",one_sequence)
						previous_move=one_move.parent
						current_color=player_color
						for one_deep_move in one_sequence.split(' '):
							
							if one_deep_move.lower() not in ['resign','pass']:
							
								i,j=gtp2ij(one_deep_move)
								new_child=previous_move.new_child()
								new_child.set_move(current_color,(i,j))

								previous_move=new_child
								if current_color in ('w','W'):
									current_color='b'
								else:
									current_color='w'

			else:
				log('adding "'+answer.lower()+'" to the sgf file')
				additional_comments+="\nFor this position, Gnugo would "+answer.lower()
				if answer.lower()=="pass":
					gnugo.undo()

			
			
			one_move.add_comment_text(additional_comments)

			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
			
			self.total_done+=1
			
			log("Creating the influence map")
			black_influence=gnugo.get_gnugo_initial_influence_black()
			black_influence_points=[]
			white_influence=gnugo.get_gnugo_initial_influence_white()
			white_influence_points=[]
			for i in range(self.size):
				for j in range(self.size):
					if black_influence[i][j]==-3:
						black_influence_points.append([i,j])
					if white_influence[i][j]==3:
						white_influence_points.append([i,j])

			if black_influence_points!=[]:
				one_move.parent.set("TB",black_influence_points)
			
			if white_influence_points!=[]:
				one_move.parent.set("TW",white_influence_points)			
			
			
		else:
			log("Move",current_move,"not in the list of moves to be analysed, skipping")
			
		linelog("now asking Gnugo to play the game move:")
		if player_color in ('w',"W"):
			log("white at",ij2gtp(player_move))
			gnugo.place_white(ij2gtp(player_move))
			for worker in self.workers:
				worker.place_white(ij2gtp(player_move))
		else:
			log("black at",ij2gtp(player_move))
			gnugo.place_black(ij2gtp(player_move))
			for worker in self.workers:
				worker.place_black(ij2gtp(player_move))
		
		log("Analysis for this move is completed")
	

	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		log("killing gnugo")
		self.gnugo.close()
		log("killing gnugo workers")
		for w in self.workers:
			w.close()
		
		log("destroying")
		self.destroy()
	
	def initialize_bot(self):
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		self.nb_variations=4
		try:
			self.nb_variations=int(Config.get("GnuGo", "variations"))
		except:
			Config.set("GnuGo", "variations",self.nb_variations)
			Config.write(open("config.ini","w"))
		
		self.deepness=4
		try:
			self.deepness=int(Config.get("GnuGo", "deepness"))
		except:
			Config.set("GnuGo", "deepness",self.deepness)
			Config.write(open("config.ini","w"))
		
		self.nb_workers=self.nb_variations
		
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
			gnugo_command_line=Config.get("GnuGo", "Command")
		except:
			show_error("The config.ini file does not contain entry for GnuGo command line!")
			return False
		
		if not gnugo_command_line:
			show_error("The config.ini file does not contain command line for GnuGo!")
			return False
		log("Starting Gnugo...")
		try:
			gnugo_command_line=[Config.get("GnuGo", "Command")]+Config.get("GnuGo", "Parameters").split()
			gnugo=gtp(gnugo_command_line)
		except Exception,e:
			show_error("Could not run GnuGo using the command from config.ini file: \n"+" ".join(gnugo_command_line)+"\n"+str(e))
			return False
		log("GnuGo started")
		log("GnuGo identification through GTP...")
		try:
			self.bot_name=gnugo.name()
		except Exception, e:
			show_error("GnuGo did not replied as expected to the GTP name command:\n"+str(e))
			return False
		
		if self.bot_name!="GNU Go":
			show_error("GnuGo did not identified itself as expected:\n'GNU Go' != '"+self.bot_name+"'")
			return False
		log("GnuGo identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=gnugo.version()
		except Exception, e:
			show_error("GnuGo did not replied as expected to the GTP version command:\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		try:
			gnugo.boardsize(size)
		except:
			show_error("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return False
		log("Clearing the board")
		gnugo.reset()
		self.gnugo=gnugo
		
		log("Setting komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		gnugo.komi(self.komi)
		
		log("Starting all GnuGo workers")
		self.workers=[]
		for w in range(self.nb_workers):
			log("\t Starting worker",w+1)
			gnugo_worker=gtp(gnugo_command_line)
			gnugo_worker.boardsize(size)
			gnugo_worker.reset()
			gnugo_worker.komi(self.komi)
			self.workers.append(gnugo_worker)
		log("All workers ready")
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		log("Adding handicap stones, if any")
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					gnugo.place_white(move)
					for worker in self.workers:
						worker.place_white(move)
				else:
					log("Adding initial black stone at",move)
					gnugo.place_black(move)
					for worker in self.workers:
						worker.place_black(move)
		log("GnuGo initialization completed")
		return True
		

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

		RangeSelector(top,filename,bots=[("GnuGo",RunAnalysis)]).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




