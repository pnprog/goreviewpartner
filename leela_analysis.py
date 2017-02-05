# -*- coding: utf-8 -*-


from gtp import gtp
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import Tk, Label, Frame
import tkFileDialog
import sys
import os

import ConfigParser


import time, os
import threading
import ttk


Config = ConfigParser.ConfigParser()
Config.read("config.ini")



def get_moves_number(move_zero):
	k=0
	move=move_zero
	while move:
		move=move[0]
		k+=1
	return k

def go_to_move(move_zero,move_number=0):
	
	if move_number==0:
		return move_zero
	move=move_zero
	k=0
	while k!=move_number:
		if not move:
			print "return False"
			return False
		move=move[0]
		k+=1
	return move


def gtp2ij(move):
	# a18 => (17,0)
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return int(move[1:])-1,letters.index(move[0])


def ij2gtp(m):
	# (17,0) => a18
	
	if m==None:
		return "pass"
	i,j=m
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return letters[j]+str(i+1)
















class RunAnalysis(Frame):
	def __init__(self,parent,filename):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.lock1=threading.Lock()
		self.lock2=threading.Lock()
		self.initialize()
	
	def run_analysis(self,current_move):
			gnugo=self.gnugo
			leela=self.leela
			max_move=self.max_move
			
			one_move=go_to_move(self.move_zero,current_move)
			player_color,player_move=one_move.get_move()
			
			print "move",str(current_move)+'/'+str(max_move),
			
			#final_score=leela.get_leela_final_score()
			final_score=gnugo.get_gnugo_estimate_score()
			
			print final_score,
			
			one_move.add_comment_text("\nGnugo score estimation: "+final_score)
			
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
			
			if (answer.lower() not in ["pass","resign"]):
				all_moves=leela.get_all_leela_moves()
				if all_moves==[]:
					all_moves=[[answer,answer,666]]
				all_moves2=all_moves[:]
				nb_undos=1
				print "====move",current_move,all_moves[0],'~',answer
				if all_moves[0][0]!=answer:
					print "Leela did not choose the strongest move!"
					print all_moves
					print "need to fix leela game tree: move at",answer,"is now at",all_moves[0][0]
					answer=all_moves[0][0]
					leela.undo()
					if player_color in ('w',"W"):
						leela.place_white(answer)
					else:
						leela.place_black(answer)
					
				#while ((len(all_moves2)==1) and (len(all_moves2[0][1].split(' '))==1)) and (answer.lower() not in ["pass","resign"]):
				while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]):	
					print "going deeper",nb_undos
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
					except Exception, e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print exc_type, fname, exc_tb.tb_lineno
						print e
						print "leaving thread..."
						exit()


					print all_moves[0],'+',answer,
					if (answer.lower() not in ["pass","resign"]):
						all_moves2=leela.get_all_leela_moves()
						
						if all_moves2[0][0]!=answer:
							print "\tLeela did not choose the strongest move!"
							answer=all_moves2[0][0]
							leela.undo()
							if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==0):
								leela.place_white(answer)
							else:
								leela.place_black(answer)
						
						print '+',all_moves2
						all_moves[0][1]+=" "+all_moves2[0][1]
						
						
						if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
							all_moves[0][2]=all_moves2[0][2]
						else:
							all_moves[0][2]=100-all_moves2[0][2]

					else:
						print
				for u in range(nb_undos):
					leela.undo()
				
				#print "all moves from leela:",all_moves
				best_move=True
				for _,one_sequence,one_score in all_moves:
					previous_move=one_move.parent
					current_color=player_color
					
					if best_move:
						best_move=False
						if player_color=='b':
							print str(one_score)+'%/'+str(100-one_score)+'%',
						else:
							print str(100-one_score)+'%/'+str(one_score)+'%',
					
					for one_deep_move in one_sequence.split(' '):
						i,j=gtp2ij(one_deep_move)
						new_child=previous_move.new_child()
						new_child.set_move(current_color,(i,j))
						#new_child.add_comment_text("black/white win probability: "+str(one_score)+'%/'+str(100-one_score)+'%')
						
						
						if player_color=='b':
							new_child.add_comment_text("black/white win probability for this variation: "+str(one_score)+'%/'+str(100-one_score)+'%')
						else:
							new_child.add_comment_text("black/white win probability for this variation: "+str(100-one_score)+'%/'+str(one_score)+'%')
						
						previous_move=new_child
						if current_color in ('w','W'):
							current_color='b'
						else:
							current_color='w'
			else:
				print answer.lower()
				
			new_file=open(self.filename[:-4]+".r.sgf",'w')
			new_file.write(self.g.serialise())
			new_file.close()
			
			if player_color in ('w',"W"):
				leela.place_white(ij2gtp(player_move))
				gnugo.place_white(ij2gtp(player_move))
			else:
				leela.place_black(ij2gtp(player_move))
				gnugo.place_black(ij2gtp(player_move))
		
	
	
	def run_all_analysis(self):
		self.current_move=1
		try:
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
			remaining_s=(self.max_move-self.current_move)*self.time_per_move
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
			self.lab1.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
			self.lab2.config(text=str(self.current_move-1)+'/'+str(self.max_move))
			self.pb.step()
			self.lock2.release()
			time.sleep(.1)
			self.lock1.release()
			self.lock2.acquire()
		if self.current_move<=self.max_move:
			self.root.after(500,self.follow_analysis)
		else:
			self.lab1.config(text="Completed")
	
	def close_app(self):
		print "RunAnalysis beeing closed"
		print "killing gnugo"
		self.gnugo.kill()
		print "killing leela"
		self.leela.kill()
		print "destroying"
		self.destroy()
		self.parent.destroy()
		print "RunAnalysis closed"

		
	def initialize(self):
		
		txt = open(self.filename)
		self.g = sgf.Sgf_game.from_string(txt.read())
		size=self.g.get_size()
		
		leela_command_line=tuple(Config.get("Leela", "Command").split())
		leela=gtp(leela_command_line)
		leela.boardsize(size)
		leela.reset()
		self.leela=leela
		
		gnugo_command_line=tuple(Config.get("GnuGo", "Command").split())
		gnugo=gtp(gnugo_command_line)
		gnugo.boardsize(size)
		gnugo.reset()
		self.gnugo=gnugo
		
		self.time_per_move=int(Config.get("Analysis", "TimePerMove"))
		leela.set_time(main_time=self.time_per_move,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		self.move_zero=self.g.get_root()
		komi=self.g.get_komi()
		leela.komi(komi)
		gnugo.komi(komi)
		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			move=ij2gtp((row,col))
			print colour,"handicap stone at",row, col, "=>",move
			
			if colour in ('w',"W"):
				leela.place_white(move)
				gnugo.place_white(move)
			else:
				leela.place_black(move)
				gnugo.place_black(move)

		self.max_move=get_moves_number(self.move_zero)
		
		
		root = self
		root.parent.title('GoReviewPartner')
		root.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		
		Label(root,text="Analysis of: "+os.path.basename(self.filename)).pack()
		self.lab1=Label(root)

		remaining_s=self.max_move*self.time_per_move
		remaining_h=remaining_s/3600
		remaining_s=remaining_s-3600*remaining_h
		remaining_m=remaining_s/60
		remaining_s=remaining_s-60*remaining_m
		self.lab1.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")


		self.lab1.pack()
		self.lab2=Label(root,text="0/"+str(self.max_move))
		self.lab2.pack()
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move, mode="determinate")
		self.pb.pack()

		current_move=1

		new_file=open(self.filename[:-4]+".r.sgf",'w')
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
	else:
		filename=argv[1]
	print "filename:",filename

	top = Tk()
	RunAnalysis(top,filename).pack()
	top.mainloop()





