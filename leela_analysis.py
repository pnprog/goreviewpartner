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
		leela=self.leela
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			print "move",str(current_move)+'/'+str(max_move),
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)

			try:
				if player_color in ('w',"W"):
					print "leela play white"
					answer=leela.play_white()
				else:
					print "leela play black"
					answer=leela.play_black()
			except Exception, e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print exc_type, fname, exc_tb.tb_lineno
				print e
				print "leaving thread..."
				exit()
			
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
				print "====move",current_move+1,all_moves[0],'~',answer
				
				
				#making sure the first line of play is more than one move deep
				best_winrate=all_moves[0][2]
				while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]):	
					print "going deeper for first line of play (",nb_undos,")"
					try:
						if player_color in ('w',"W") and nb_undos%2==0:
							#print "\tleela play white"
							answer=leela.play_white()
						elif player_color in ('w',"W") and nb_undos%2==1:
							#print "\tleela play black"
							answer=leela.play_black()
						elif player_color not in ('w',"W") and nb_undos%2==0:
							#print "\tleela play black"
							answer=leela.play_black()
						else:
							#print "\tleela play white"
							answer=leela.play_white()
						nb_undos+=1
						#if answer.lower()!="resign":
						#	nb_undos+=1
					except Exception, e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print exc_type, fname, exc_tb.tb_lineno
						print e
						print "leaving thread..."
						exit()


					print all_moves[0],'+',answer,
					all_moves2=leela.get_all_leela_moves()
					if (answer.lower() not in ["pass","resign"]):
						
						print "all_moves2:",all_moves2
						if all_moves2==[]:
							all_moves2=[[answer,answer,666,666,666,666,666,666,666]]

						print '+',all_moves2
						all_moves[0][1]+=" "+all_moves2[0][1]
						
						
						if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
							all_moves[0][2]=all_moves2[0][2]
						else:
							all_moves[0][2]=100-all_moves2[0][2]

					else:
						print
						print "last play on the fist of play was",answer,"so leaving"
				
				for u in range(nb_undos):
					print "undo..."
					leela.undo()
				
				
				#all_moves[0][2]=best_winrate #it would be best to sort again all variation based on new winrate...
				
				#print "all moves from leela:",all_moves
				best_move=True
				#variation=-1
				print "Number of alternative sequences:",len(all_moves)
				print all_moves
				for sequence_first_move,one_sequence,one_score,one_monte_carlo,one_value_network,one_policy_network,one_evaluation,one_rave,one_nodes in all_moves:
					print "Adding sequence starting from",sequence_first_move
					previous_move=one_move.parent
					current_color=player_color
					
					if best_move:
						if player_color=='b':
							print str(one_score)+'%/'+str(100-one_score)+'%',
						else:
							print str(100-one_score)+'%/'+str(one_score)+'%',
					
					#variation+=1
					#deepness=-1
					first_variation_move=True
					for one_deep_move in one_sequence.split(' '):
						#deepness+=1
						#print "variation:",variation,"deepness:",deepness,"gtp2ij(",one_deep_move,")"
						if one_deep_move.lower() in ["pass","resign"]:
							print "Leaving the variation when encountering",one_deep_move.lower()
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
				print "==== no more sequences ====="
				
				print "Creating the influence map"
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
				print 'adding "'+answer.lower()+'" to the sgf file'
				additional_comments+="\nFor this position, Leela would "+answer.lower()
				if answer.lower()=="pass":
					leela.undo()
			
			
			one_move.add_comment_text(additional_comments)
			new_file=open(self.filename[:-4]+".rsgf",'w')
			new_file.write(self.g.serialise())
			new_file.close()
			
			self.total_done+=1
		else:
			print "Move",current_move,"not in the list of moves to be analysed, skipping"

		print "now asking Leela to play the game move:",
		if player_color in ('w',"W"):
			print "white at",ij2gtp(player_move)
			leela.place_white(ij2gtp(player_move))
		else:
			print "black at",ij2gtp(player_move)
			leela.place_black(ij2gtp(player_move))
		print "Analysis for this move is completed"
	

	def run_all_analysis(self):
		self.current_move=1
		try:
			first_move=go_to_move(self.move_zero,1)
			first_comment="Analysis by GoReviewPartner"
			first_comment+="\nBot: "+self.leela.name()+'/'+self.leela.version()
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
			remaining_s=(len(self.move_range)-self.total_done)*self.time_per_move
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
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
		print "killing leela"
		self.leela.close()
		print "destroying"
		self.destroy()
	
	def close_app(self):
		self.remove_app()
		self.parent.destroy()
		print "RunAnalysis closed"


		
	def initialize(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		
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
			leela_command_line=Config.get("Leela", "Command")
		except:
			alert("The config.ini file does not contain entry for Leela command line!")
			return
		
		if not leela_command_line:
			alert("The config.ini file does not contain command line for Leela!")
			return
		try:
			leela_command_line=[Config.get("Leela", "Command")]+Config.get("Leela", "Parameters").split()
			leela=gtp(leela_command_line)
		except:
			alert("Could not run Leela using the command from config.ini file: \n"+" ".join(leela_command_line))
			return
		try:
			leela.boardsize(size)
		except:
			alert("Could not set the goboard size using GTP command. Check that the bot is running in GTP mode.")
			return

		leela.reset()
		self.leela=leela
		
		self.time_per_move=int(Config.get("Leela", "TimePerMove"))
		leela.set_time(main_time=self.time_per_move,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		self.move_zero=self.g.get_root()
		komi=self.g.get_komi()
		leela.komi(komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					print "Adding initial white stone at",move
					leela.place_white(move)
				else:
					print "Adding initial black stone at",move
					leela.place_black(move)
						
			
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
		self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()

		current_move=1

		new_file=open(self.filename[:-4]+".rsgf",'w')
		new_file.write(self.g.serialise())
		new_file.close()

		self.lock2.acquire()
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
		toolbox.RunAnalysis=RunAnalysis
		RangeSelector(top,filename,bots=[("Leela",RunAnalysis)]).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




