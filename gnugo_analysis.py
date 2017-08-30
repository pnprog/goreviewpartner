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
import threading
import ttk


from toolbox import *

def get_full_sequence_threaded(worker,current_color,deepness):
	sequence=get_full_sequence(worker,current_color,deepness)
	threading.current_thread().sequence=sequence

def get_full_sequence(worker,current_color,deepness):
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


class RunAnalysis(Frame):
	def __init__(self,parent,filename,move_range,intervals,variation):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.move_range=move_range
		self.lock1=threading.Lock()
		self.lock2=threading.Lock()
		self.intervals=intervals
		self.variation=variation
		
		self.initialize()
		
	
	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		gnugo=self.gnugo
		if current_move in self.move_range:
			max_move=self.max_move
			print "move",str(current_move)+'/'+str(max_move),
			final_score=gnugo.get_gnugo_estimate_score()
			print final_score,
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)
			additional_comments+="\nGnugo score estimation before the move was played: "+final_score
			try:
				if player_color in ('w',"W"):
					print "gnugo plays white"
					top_moves=gnugo.gnugo_top_moves_white()
					answer=gnugo.play_white()
				else:
					print "gnugo plays black"
					top_moves=gnugo.gnugo_top_moves_black()
					answer=gnugo.play_black()
			except Exception, e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print exc_type, fname, exc_tb.tb_lineno
				print e
				print "leaving thread..."
				exit()
			
			print "====","Gnugo answer:",answer
			
			print "==== Gnugo top moves"
			for one_top_move in top_moves:
				print "\t",one_top_move
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
						one_sequence=one_thread.one_top_move+" "+one_thread.sequence
						one_sequence=one_sequence.strip()
						print ">>>>>>",one_sequence
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
				print 'adding "'+answer.lower()+'" to the sgf file'
				additional_comments+="\nFor this position, Gnugo would "+answer.lower()
				if answer.lower()=="pass":
					gnugo.undo()

			
			
			one_move.add_comment_text(additional_comments)

			new_file=open(self.filename[:-4]+".rsgf",'w')
			new_file.write(self.g.serialise())
			new_file.close()
			
			self.total_done+=1
			
			
			
			
			print "Creating the influence map"
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
			print "Move",current_move,"not in the list of moves to be analysed, skipping"
			
		print "now asking Gnugo to play the game move:",
		if player_color in ('w',"W"):
			print "white at",ij2gtp(player_move)
			gnugo.place_white(ij2gtp(player_move))
			for worker in self.workers:
				worker.place_white(ij2gtp(player_move))
		else:
			print "black at",ij2gtp(player_move)
			gnugo.place_black(ij2gtp(player_move))
			for worker in self.workers:
				worker.place_black(ij2gtp(player_move))
		
		print "Analysis for this move is completed"
	
	
	def run_all_analysis(self):
		self.current_move=1
		try:
			first_move=go_to_move(self.move_zero,1)
			first_comment="Analysis by GoReviewPartner"
			first_comment+="\nBot: "+self.gnugo.name()+'/'+self.gnugo.version()
			first_comment+="\nIntervals: "+self.intervals
			first_move.add_comment_text(first_comment)
			
			while self.current_move<=self.max_move:
				self.lock1.acquire()
				self.run_analysis(self.current_move)
				self.current_move+=1
				self.lock1.release()
				self.lock2.acquire()
				self.lock2.release()
		except Exception,e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print exc_type, fname, exc_tb.tb_lineno
			print e
			print "releasing lock"
			try:
				self.lock1.release()
			except:
				pass
			try:
				self.lock2.release()
			except:
				pass
			print "leaving thread"
			exit()
		
		

	def follow_analysis(self):
		if self.lock1.acquire(False):
			if self.total_done>0:
				self.time_per_move=1.0*(time.time()-self.t0)/self.total_done+1
				print "self.time_per_move=",(time.time()-self.t0),"/",self.total_done,"=",self.time_per_move
			remaining_s=int((len(self.move_range)-self.total_done)*self.time_per_move)
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
			if self.time_per_move<>0:
				self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
			self.lab1.config(text="Currently at move "+str(self.current_move)+'/'+str(self.max_move))
			self.pb.step()
			self.update_idletasks()
			self.lock2.release()
			time.sleep(.001)
			self.lock1.release()
			self.lock2.acquire()
		if self.current_move<=self.max_move:
			self.root.after(1,self.follow_analysis)
		else:
			self.lab1.config(text="Completed")
			self.pb["maximum"] = 100
			self.pb["value"] = 100
			
			try:
				import dual_view
				Button(self,text="Start review",command=self.start_review).pack()
			except:
				pass

	def start_review(self):
		import dual_view
		app=self.parent
		screen_width = app.winfo_screenwidth()
		screen_height = app.winfo_screenheight()
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		display_factor=.5
		try:
			display_factor=float(Config.get("Review", "GobanScreenRatio"))
		except:
			Config.set("Review", "GobanScreenRatio",display_factor)
			Config.write(open("config.ini","w"))
		
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		#Toplevel()
		
		new_popup=dual_view.DualView(self.parent,self.filename[:-4]+".rsgf",min(width,height))
		new_popup.pack(fill=BOTH,expand=1)
		self.remove_app()
		
	
	def remove_app(self):
		print "RunAnalysis beeing closed"
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		print "killing gnugo"
		self.gnugo.close()
		print "killing gnugo workers"
		for w in self.workers:
			w.close()
		
		print "destroying"
		self.destroy()
	
	def close_app(self):
		self.remove_app()
		self.parent.destroy()
		print "RunAnalysis closed"

		
	def initialize(self):
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
		print "keeping only variation",self.variation
		keep_only_one_leaf(leaves[self.variation][0])
		
		size=self.g.get_size()
		print "size of the tree:", size
		self.size=size
		try:
			gnugo_command_line=Config.get("GnuGo", "Command")
		except:
			alert("The config.ini file does not contain entry for GnuGo command line!")
			return
		
		if not gnugo_command_line:
			alert("The config.ini file does not contain command line for GnuGo!")
			return
		try:
			gnugo_command_line=[Config.get("GnuGo", "Command")]+Config.get("GnuGo", "Parameters").split()
			gnugo=gtp(gnugo_command_line)
		except:
			alert("Could not run GnuGo using the command from config.ini file: \n"+" ".join(gnugo_command_line))
			return
		try:
			gnugo.boardsize(size)
		except:
			alert("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return
		gnugo.reset()
		self.gnugo=gnugo
		
		self.workers=[]
		
		for w in range(self.nb_workers):
			gnugo_worker=gtp(gnugo_command_line)
			gnugo_worker.boardsize(size)
			gnugo_worker.reset()
			self.workers.append(gnugo_worker)
		
		self.move_zero=self.g.get_root()
		komi=self.g.get_komi()

		gnugo.komi(komi)
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					print "Adding initial white stone at",move
					gnugo.place_white(move)
					for worker in self.workers:
						worker.place_white(move)
					
				else:
					print "Adding initial black stone at",move
					gnugo.place_black(move)
					for worker in self.workers:
						worker.place_black(move)
					
						
			
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
		
		self.time_per_move=0
		"""
		remaining_s=len(self.move_range)*(2*self.deepness+1)
		remaining_h=remaining_s/3600
		remaining_s=remaining_s-3600*remaining_h
		remaining_m=remaining_s/60
		remaining_s=remaining_s-60*remaining_m
		"""
		self.lab1=Label(root)
		self.lab1.pack()
		
		self.lab2=Label(root)
		self.lab2.pack()
		
		self.lab1.config(text="Currently at move 1/"+str(self.max_move))
		#self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move, mode="determinate")
		self.pb.pack()

		current_move=1

		new_file=open(self.filename[:-4]+".rsgf",'w')
		new_file.write(self.g.serialise())
		new_file.close()

		self.lock2.acquire()
		self.t0=time.time()
		threading.Thread(target=self.run_all_analysis).start()
		
		self.root=root
		root.after(500,self.follow_analysis)
		







if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf', '.sgf')])
		temp_root.destroy()
		print filename
		print "gamename:",filename[:-4]
		if not filename:
			sys.exit()
		print "filename:",filename
		top = Tk()

		RangeSelector(top,filename,bots=[("GnuGo",RunAnalysis)]).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




