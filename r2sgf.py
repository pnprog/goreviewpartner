# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from toolbox import *

def rsgf2sgf(rsgf_file):
	#log("Convertion of",rsgf_file,"into",rsgf_file+".sgf")
	g=open_sgf(rsgf_file)
	sgf_moves.indicate_first_player(g)
	gameroot=g.get_root()
			
	max_move=get_moves_number(gameroot)

	current_move=1
	while current_move<=max_move:
		comments=get_position_comments(current_move,gameroot)
		node_set(get_node(gameroot,current_move),"C",comments)
		parent=get_node(gameroot,current_move-1)
		
		for a in range(1,len(parent)):
			one_alternative=parent[a]
			comments=get_variation_comments(one_alternative)
			node_set(one_alternative,"C",comments)
		current_move+=1

	write_sgf(rsgf_file+".sgf",g)

if __name__ == "__main__":
	from sys import argv
	
	if len(argv)==1:
		temp_root = Tk()
		filename = open_rsgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		if not filename:
			sys.exit()
		rsgf2sgf(filename)
		
	else:
		for filename in argv[1:]:
			rsgf2sgf(filename)
