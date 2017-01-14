# -*- coding: utf-8 -*-


from gtp import gtp
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import Tk
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
	
	if current_move<=max_move:
		one_move=go_to_move(move_zero,current_move)
		player_color,player_move=one_move.get_move()
		
		print "move",str(current_move)+'/'+str(max_move),
		
		#final_score=leela.get_leela_final_score()
		final_score=gnugo.get_gnugo_estimate_score()
		
		"""
		if player_color in ('w',"W"):
			final_score+="\n"+gnugo.get_gnugo_experimental_score('black')
		else:
			final_score+="\n"+gnugo.get_gnugo_experimental_score('white')
		"""
		print final_score,
		
		one_move.add_comment_text("\nGnugo score estimation: "+final_score)
		
		try:
			if player_color in ('w',"W"):
				answer=leela.play_white()
			else:
				answer=leela.play_black()
		except KeyboardInterrupt:
			print "leaving..."
			leela.kill()
			gnugo.kill()
			exit()
		
		if (answer.lower() not in ["pass","resign"]):
			
			all_moves=leela.get_all_leela_moves()
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
		#print "variation",current_move,"saved"
		
		if player_color in ('w',"W"):
			leela.place_white(ij2gtp(player_move))
			gnugo.place_white(ij2gtp(player_move))
		else:
			leela.place_black(ij2gtp(player_move))
			gnugo.place_black(ij2gtp(player_move))
			

		
		current_move+=1
		print
		
		#run_analisys(current_move)
		pb.step()
		root.after(10,lambda: run_analisys(current_move))
	else:
		root.destroy()

import ttk
root = Tk()
pb = ttk.Progressbar(root, orient="horizontal", length=max_move,maximum=max_move, mode="determinate")
pb.pack()

current_move=1

#run_analisys(current_move)

new_file=open(filename[:-4]+".r.sgf",'w')
new_file.write(g.serialise())
new_file.close()

root.after(500,lambda: run_analisys(current_move))

root.mainloop()






gnugo.kill()
leela.kill()

sys.exit()

