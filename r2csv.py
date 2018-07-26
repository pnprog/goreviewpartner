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
	headers_bot=["Move", "Win rate", "Value Network", "Monte Carlo", "Evaluation", "Rave", "Score Estimation", "Policy Network", "Simulations", "Follow up"]
	headers_game=["Move", "Win rate", "Value Network", "Monte Carlo", "Evaluation", "Rave", "Score Estimation", "Policy Network", "Simulations", "Follow up"]
	
	table=[headers_left[:]+headers_bot[:]+headers_game[:]]
	
	columns_sgf_properties=["CBM","BWWR","VNWR","MCWR","EVAL","RAVE","ES","PNV","PLYO","nothing_here"]
	
	
	
	for m in range(1,max_move):
		one_move=get_node(gameroot,m)
		
		table.append(["" for i in range(len(table[0]))])
		#-- Move number
		table[m][0]=m
		
		#-- colour
		color=guess_color_to_play(gameroot,m)
		table[m][1]=color.upper()
		
		c=len(headers_left)
		for header, sgf_property in zip(headers_bot,columns_sgf_properties):
			if header=="Follow up":
				break
			try:
				one_move=get_node(gameroot,m)
				if sgf_property in ("PNV","PLYO"):
					one_move=one_move.parent[1]
				
				if node_has(one_move,sgf_property):
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
		
		

		one_move=get_node(gameroot,m)
		c=len(headers_left+headers_bot)
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
						value=ij2gtp(value).upper()
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


	for c in range(len(table[0])):
		for m in range(len(table[1:])):
			if table[1+m][c]!="":
				break
		if table[1+m][c]=="":
			table[0][c]=""
	
	csv.write(",,")
	c=2
	for header in table[0][len(headers_left):]:
		if header!="":
			if c<=len(headers_bot):
				csv.write("Bot move,")
			else:
				csv.write("Game move,")
		c+=1
	csv.write("\n")
	
	for m in table:
		line=""
		for value, header in zip(m,table[0]):
			if header!="":
				line+=str(value).strip()+","
		print line
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
