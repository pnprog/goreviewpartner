# -*- coding: utf-8 -*-
from toolbox import *
from toolbox import _


def rsgf2sgf(rsgf_file):
	#log("Convertion of",rsgf_file,"into",rsgf_file+".sgf")
	g=open_sgf(rsgf_file)
	sgf_moves.indicate_first_player(g)
	gameroot=g.get_root()
	
	
	if gameroot.has_property("CA"):
		#log("Declared encoding in the RSGF file:",gameroot.get("CA"))
		if gameroot.get("CA")=="UTF-8":
			unicode_ok=True
		else:
			unicode_ok=False
	else:
		#log("The RSGF file does not contain encoding declaration")
		content=g.serialise()
		try:
			content.decode("utf") #let's check the content can be converted to UTF-8
			gameroot.set("CA","UTF-8") #let's add the CA property
			g = sgf.Sgf_game.from_string(g.serialise(),override_encoding="UTF-8") #let's recreate the game from a SGF content containing the CA property
			sgf_moves.indicate_first_player(g)
			gameroot=g.get_root()
			unicode_ok=True
			#log("But the RSGF can be converted to UTF, so no problem")
		except:
			log("The RSGF file",rsgf_file,"contains characters that cannot be converted to UTF-8")
			g = sgf.Sgf_game.from_string(content)
			sgf_moves.indicate_first_player(g)
			gameroot=g.get_root()
			unicode_ok=False
			
	max_move=get_moves_number(gameroot)

	current_move=1
	while current_move<=max_move:
		comments=get_position_comments(current_move,gameroot)
		if not unicode_ok:
			comments=comments.decode(errors='ignore')
		
		get_node(gameroot,current_move).set("C",comments)
		parent=get_node(gameroot,current_move-1)
		
		for a in range(1,len(parent)):
			one_alternative=parent[a]
			comments=get_variation_comments(one_alternative)
			one_alternative.set("C",comments)
		current_move+=1

	write_sgf(rsgf_file+".sgf",g)

import getopt
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
