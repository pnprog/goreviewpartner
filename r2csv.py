# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gomill import sgf_moves
from toolbox import *

def rsgf2csv(filename):
	game=open_sgf(filename)
	sgf_moves.indicate_first_player(game)
	gameroot=game.get_root()

	max_move=get_moves_number(gameroot)

	csv=open(filename+".csv","w")

	black=""
	if gameroot.has_property("PB"):
		black=gameroot.get("PB")
	new_line="black: "+black
	csv.write(new_line+"\n")


	white=""
	if gameroot.has_property("PW"):
		white=gameroot.get("PW")
	new_line="white: "+white
	csv.write(new_line+"\n")

	date=""
	if gameroot.has_property("DT"):
		date=gameroot.get("DT")
	new_line="date: "+date
	csv.write(new_line+"\n")

	event=""
	if gameroot.has_property("EV"):
		event=gameroot.get("EV")
	new_line="event: "+event
	csv.write(new_line+"\n")

	new_line=""
	csv.write(new_line+"\n")
	
	headers_left=["Move number", "Move color"]
	headers_game=["Move", "Win rate", "Value Network", "Monte Carlo", "Evaluation", "Rave", "Score Estimation", "Policy Network", "Simulations", "Follow up", "Variations"]
	headers_bot=headers_game[:]
	
	header_first_line=[""]*len(headers_left)+["Game move"]*len(headers_game)+["Bot move"]*len(headers_bot)
	
	table=[headers_left[:]+headers_game[:]+headers_bot[:]]
	
	nb_max_variations=1
	
	columns_sgf_properties=["CBM","BWWR","VNWR","MCWR","EVAL","RAVE","ES","PNV","PLYO","nothing_here","nothing_here"]
	
	for m in range(1,max_move):
		one_move=get_node(gameroot,m)
		table.append(["" for i in range(len(table[0]))])
		#-- Move number
		table[m][0]=m
		
		#-- colour
		color=guess_color_to_play(gameroot,m)
		table[m][1]=color.upper()
		
		#-- game move
		one_move=get_node(gameroot,m)
		c=len(headers_left)
		for header, sgf_property in zip(headers_bot,columns_sgf_properties):
			if header=="Follow up":
				break
			try:
				next_move=one_move[0] #taking data from the following move
				if sgf_property =="PLYO":
					next_move=one_move[1]
				if  sgf_property =="PNV":
					for variation in one_move.parent[1:]:
						if node_get(variation,color.upper())==node_get(one_move,color.upper()):
							next_move=variation
							break
					
				if sgf_property=="CBM":
					if color=="w":
						sgf_property="B"
					else:
						sgf_property="W"
				
				if node_has(next_move,sgf_property):
					if sgf_property=="B" or sgf_property=="W":
						value=node_get(one_move,color.upper())
						value=ij2gtp(value)
					else:
						value=node_get(next_move,sgf_property)
						
					if "%/" in value:
						if color=="b":
							value=float(value.split("%/")[0])
							value=round(value,2)
							value=str(value)+"%"
						else:
							value=float(value.split("/")[1][:-1])
							value=round(value,2)
							value=str(value)+"%"
					table[m][c]=value
			except:
				pass
			c+=1
		
		#-- variations
		
		if len(one_move.parent[1:])>nb_max_variations:
			nb_max_variations=len(one_move.parent[1:])
			headers_bot=headers_game[:]*nb_max_variations
			table[0]=headers_left[:]+headers_game[:]+headers_bot[:]*nb_max_variations
			header_first_line=[""]*len(headers_left)+["Game move"]*len(headers_game)+["Bot move"]*len(headers_game)
			for i in range(2,nb_max_variations+1):
				header_first_line+=["Bot move "+str(i)]*len(headers_game)
		
		c=len(headers_left+headers_game)
		if len(one_move.parent[1:]):
			table[m][c-1]=len(one_move.parent[1:])
		nbv=1
		for one_variation in one_move.parent[1:]:
			nbv+=1
			for header, sgf_property in zip(headers_bot,columns_sgf_properties):
				#if header=="Follow up":
				#	break
				try:
					#one_move=get_node(gameroot,m)
					#if sgf_property in ("PNV","PLYO"):
					#	one_move=one_variation
					one_move=one_variation
					
					if sgf_property=="CBM":
						if color=="w":
							sgf_property="W"
						else:
							sgf_property="B"
					
					if node_has(one_move,sgf_property):
						if sgf_property=="B" or sgf_property=="W":
							value=node_get(one_move,color.upper())
							value=ij2gtp(value)
						else:
							value=node_get(one_move,sgf_property)
						if "%/" in value:
							if color=="b":
								value=float(value.split("%/")[0])
								value=round(value,2)
								value=str(value)+"%"
							else:
								value=float(value.split("/")[1][:-1])
								value=round(value,2)
								value=str(value)+"%"
						table[m][c]=value
						
				except:
					pass
				c+=1

	
	#scanning for empty columns
	for c in range(len(table[0])): #checking column after column
		found=False
		for m in range(len(table[1:])): #for each columns checking for at least one value
			try:
				if table[1+m][c]!="": #one value was found, so let's keept that column
					found=True
					break
			except:
				#no data (probably no variation data, so keep searching)
				pass
		
		if not found:
			table[0][c]="" #no value found in the entire column, so let's remove the header to remeber to skip that column
	
	c=len(headers_left+headers_game)-1
	header_first_line[c]=""
	c=0
	for header in table[0]:
		if header!="":
			csv.write(header_first_line[c]+",")
		c+=1
	
	csv.write("\n")
	
	for m in table:
		line=""
		for value, header in zip(m,table[0]):
			if header!="":
				line+=str(value).strip()+","
		#print line
		csv.write(line+"\n")
	

	log("saving")
	csv.close()

if __name__ == "__main__":
	from sys import argv
	
	if len(argv)==1:
		temp_root = Tk()
		filename = open_rsgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		if not filename:
			sys.exit()
		rsgf2csv(filename)
		
	else:
		for filename in argv[1:]:
			rsgf2csv(filename)
