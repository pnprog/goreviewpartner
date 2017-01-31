# -*- coding: utf-8 -*-


from gtp import gtp
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import Tk, Label
import tkFileDialog
import sys
import os

import ConfigParser
Config = ConfigParser.ConfigParser()
Config.read("config.ini")

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



txt = open(filename)
g = sgf.Sgf_game.from_string(txt.read())

size=g.get_size()

leela_command_line=tuple(Config.get("Leela", "Command").split())
leela=gtp(leela_command_line)

leela.boardsize(size)
leela.reset()

gnugo_command_line=tuple(Config.get("GnuGo", "Command").split())
gnugo=gtp(gnugo_command_line)
gnugo.boardsize(size)
gnugo.reset()

time_per_move=int(Config.get("Analysis", "TimePerMove"))
print "time setting:",leela.set_time(main_time=time_per_move,byo_yomi_time=time_per_move,byo_yomi_stones=1)
move_zero=g.get_root()
komi=g.get_komi()
print "komi=",komi
leela.komi(komi)
gnugo.komi(komi)

def get_moves_number(move_zero):
	k=0
	move=move_zero
	while move:
		move=move[0]
		k+=1
	return k

def go_to_move(move_zero,move_number=0):
	
	if move_number==0:
		#print "going to move_zero"
		return move_zero
	#print "going to move",move_number
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


board, plays = sgf_moves.get_setup_and_moves(g)

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

print "=============================="


max_move=get_moves_number(move_zero)





def run_analisys(current_move):
	

		one_move=go_to_move(move_zero,current_move)
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
		except KeyboardInterrupt:
			print "leaving..."
			leela.kill()
			gnugo.kill()
			exit()
		
		if (answer.lower() not in ["pass","resign"]):
			
			all_moves=leela.get_all_leela_moves()
			all_moves2=all_moves[:]
			nb_undos=1
			while len(all_moves2)==1 and len(all_moves2[0][1].split(' '))==1:
				#print "going deeper"
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
				except KeyboardInterrupt:
					print "leaving..."
					leela.kill()
					gnugo.kill()
					exit()

					
				if (answer.lower() in ["pass","resign"]):
					break
				
				all_moves2=leela.get_all_leela_moves()
				all_moves[0][1]+=" "+all_moves2[0][1]

				
				#all_moves[0][2]=all_moves2[0][2]
				
				if player_color=='b' and nb_undos%2==1:
					all_moves[0][2]=all_moves2[0][2]
				elif player_color=='b' and nb_undos%2==0:
					all_moves[0][2]=100-all_moves2[0][2]
				elif player_color=='w' and nb_undos%2==1:
					all_moves[0][2]=all_moves2[0][2]
				else:
					all_moves[0][2]=100-all_moves2[0][2]
				
				
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
			
		new_file=open(filename[:-4]+".r.sgf",'w')
		new_file.write(g.serialise())
		new_file.close()
		
		if player_color in ('w',"W"):
			leela.place_white(ij2gtp(player_move))
			gnugo.place_white(ij2gtp(player_move))
		else:
			leela.place_black(ij2gtp(player_move))
			gnugo.place_black(ij2gtp(player_move))
		




def run_all_analisys():
	global current_move
	current_move=1
	try:
		while current_move<=max_move:
			lock1.acquire()
			run_analisys(current_move)
			current_move+=1
			lock1.release()
			lock2.acquire()
			lock2.release()
	except:
		return
		

def follow_analisys():
	if lock1.acquire(False):
		remaining_s=(max_move-current_move)*time_per_move
		remaining_h=remaining_s/3600
		remaining_s=remaining_s-3600*remaining_h
		remaining_m=remaining_s/60
		remaining_s=remaining_s-60*remaining_m
		lab1.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
		lab2.config(text=str(current_move-1)+'/'+str(max_move))
		pb.step()
		lock2.release()
		time.sleep(.1)
		lock1.release()
		lock2.acquire()
	if current_move<=max_move:
		root.after(500,follow_analisys)
	else:
		lab1.config(text="Completed")

		

import time, os
import threading
import ttk
root = Tk()
root.title('GoReviewPartner')
Label(root,text="Analisys of: "+os.path.basename(filename)).pack()
lab1=Label(root,text="Remaining time: ")
lab1.pack()
lab2=Label(root,text="hello")
lab2.pack()
pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=max_move, mode="determinate")
pb.pack()

current_move=1


new_file=open(filename[:-4]+".r.sgf",'w')
new_file.write(g.serialise())
new_file.close()

lock1=threading.Lock()
lock2=threading.Lock()


lock2.acquire()
threading.Thread(target=run_all_analisys).start()
root.after(500,follow_analisys)
root.mainloop()

gnugo.kill()
leela.kill()



