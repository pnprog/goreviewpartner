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
from toolbox import _

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
			log()
			linelog("move",str(current_move)+'/'+str(max_move))
			final_score=gnugo.get_gnugo_estimate_score()
			#linelog(final_score)
			additional_comments=_("Move %i")%current_move
			if player_color in ('w',"W"):
				additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
			else:
				additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))
			additional_comments+="\n"+_("Gnugo score estimation before the move was played: ")+final_score

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
			top_moves=top_moves[:min(self.nb_variations,self.maxvariations)]
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
							raise AbortedException(_("GnuGo thread failed:")+"\n"+str(one_thread.sequence))
						
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
				additional_comments+="\n"+_("For this position, %s would %s"%("GnuGo",answer.lower()))
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
		self.lab2.config(text=_("Now closing, please wait..."))
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
		Config.read(config_file)
		self.nb_variations=4
		try:
			self.nb_variations=int(Config.get("GnuGo", "variations"))
		except:
			Config.set("GnuGo", "variations",self.nb_variations)
			Config.write(open(config_file,"w"))
		
		self.deepness=4
		try:
			self.deepness=int(Config.get("GnuGo", "deepness"))
		except:
			Config.set("GnuGo", "deepness",self.deepness)
			Config.write(open(config_file,"w"))
		
		self.nb_workers=self.nb_variations
		
		self.g=open_sgf(self.filename)

		leaves=get_all_sgf_leaves(self.g.get_root())
		log("keeping only variation",self.variation)
		keep_only_one_leaf(leaves[self.variation][0])
		
		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size
		
		try:
			gnugo_command_line=Config.get("GnuGo", "Command")
		except:
			show_error(_("The config.ini file does not contain entry for %s command line!")%"GnuGo")
			return False
		
		if not gnugo_command_line:
			show_error(_("The config.ini file does not contain command line for %s!")%"GnuGo")
			return False
		log("Starting Gnugo...")
		try:
			gnugo_command_line=[Config.get("GnuGo", "Command")]+Config.get("GnuGo", "Parameters").split()
			gnugo=GnuGo_gtp(gnugo_command_line)
		except Exception,e:
			show_error((_("Could not run %s using the command from config.ini file:")%"GnuGo")+"\n"+" ".join(gnugo_command_line)+"\n"+str(e))
			return False
		log("GnuGo started")
		log("GnuGo identification through GTP...")
		try:
			self.bot_name=gnugo.name()
		except Exception, e:
			show_error((_("%s did not replied as expected to the GTP name command:")%"GnuGo")+"\n"+str(e))
			return False
		
		if self.bot_name!="GNU Go":
			show_error((_("%s did not identified itself as expected:")%"GnuGo")+"\n'GNU Go' != '"+self.bot_name+"'")
			return False
		log("GnuGo identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=gnugo.version()
		except Exception, e:
			show_error((_("%s did not replied as expected to the GTP version command:")%"GnuGo")+"\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		try:
			ok=gnugo.boardsize(size)
		except:
			show_error((_("Could not set the goboard size using GTP command. Check that %s is running in GTP mode.")%"GnuGo"))
			return False
		if not ok:
			show_error(_("%s rejected this board size (%ix%i)")%("GnuGo",size,size))
			return False
		log("Clearing the board")
		gnugo.reset()
		self.gnugo=gnugo
		
		self.time_per_move=0
		
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
		return gnugo
		


class GnuGo_gtp(gtp):

	def get_gnugo_initial_influence_black(self):
		self.write("initial_influence black influence_regions")
		one_line=self.readline()
		one_line=one_line.split("= ")[1].strip().replace("  "," ")
		lines=[one_line]
		for i in range(self.size-1):
			one_line=self.readline().strip().replace("  "," ")
			lines.append(one_line)
		
		influence=[]
		for i in range(self.size):
			influence=[[int(s) for s in lines[i].split(" ")]]+influence
		return influence

	def get_gnugo_initial_influence_white(self):
		self.write("initial_influence white influence_regions")
		one_line=self.readline()
		one_line=one_line.split("= ")[1].strip().replace("  "," ")
		lines=[one_line]
		for i in range(self.size-1):
			one_line=self.readline().strip().replace("  "," ")
			lines.append(one_line)
		
		influence=[]
		for i in range(self.size):
			influence=[[int(s) for s in lines[i].split(" ")]]+influence
		return influence
	
	def get_gnugo_estimate_score(self):
		self.write("estimate_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GtpException("GtpException in get_gnugo_estimate_score()")
	
	def gnugo_top_moves_black(self):
		self.write("top_moves_black")
		answer=self.readline()[:-1]
		try:
			answer=answer.split(" ")[1:-1]
		except:
			raise GtpException("GtpException in get_gnugo_top_moves_black()")
		answers_list=[]
		for value in answer:
			try:
				score=float(value)
			except:
				answers_list.append(value)
		return answers_list

	def gnugo_top_moves_white(self):
		self.write("top_moves_white")
		answer=self.readline()[:-1]
		try:
			answer=answer.split(" ")[1:-1]
		except:
			raise GtpException("GtpException in get_gnugo_top_moves_white()")
		answers_list=[]
		for value in answer:
			try:
				score=float(value)
			except:
				answers_list.append(value)
		return answers_list

	
	def get_gnugo_experimental_score(self,color):
		self.write("experimental_score "+color)
		answer=self.readline().strip()
		return answer[2:]


class GnuGoSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		log("Initializing GnuGo setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		row=0
		
		Label(self,text=_("%s settings")%"GnuGo").grid(row=row+1,column=1)
		Label(self,text=_("Command")).grid(row=row+2,column=1)
		GnugoCommand = StringVar() 
		GnugoCommand.set(Config.get("GnuGo","Command"))
		Entry(self, textvariable=GnugoCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row+2,column=1)
		GnugoParameters = StringVar() 
		GnugoParameters.set(Config.get("GnuGo","Parameters"))
		Entry(self, textvariable=GnugoParameters, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text=_("Maximum number of variations")).grid(row=row+2,column=1)
		GnugoVariations = StringVar() 
		GnugoVariations.set(Config.get("GnuGo","Variations"))
		Entry(self, textvariable=GnugoVariations, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text=_("Deepness for each variation")).grid(row=row+2,column=1)
		GnugoDeepness = StringVar() 
		GnugoDeepness.set(Config.get("GnuGo","Deepness"))
		Entry(self, textvariable=GnugoDeepness, width=30).grid(row=row+2,column=2)
		row+=1
		GnugoNeededForReview = BooleanVar(value=Config.getboolean('GnuGo', 'NeededForReview'))
		GnugoCheckbutton=Checkbutton(self, text=_("Needed for review"), variable=GnugoNeededForReview,onvalue=True,offvalue=False)
		GnugoCheckbutton.grid(row=row+2,column=1)
		GnugoCheckbutton.var=GnugoNeededForReview

		self.GnugoCommand=GnugoCommand
		self.GnugoParameters=GnugoParameters
		self.GnugoVariations=GnugoVariations
		self.GnugoDeepness=GnugoDeepness
		self.GnugoNeededForReview=GnugoNeededForReview
		

	def save(self):
		log("Saving GnuGo settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set("GnuGo","Command",self.GnugoCommand.get())
		Config.set("GnuGo","Parameters",self.GnugoParameters.get())
		Config.set("GnuGo","Variations",self.GnugoVariations.get())
		Config.set("GnuGo","Deepness",self.GnugoDeepness.get())
		Config.set("GnuGo","NeededForReview",self.GnugoNeededForReview.get())
		
		Config.write(open(config_file,"w"))

class GnuGoOpenMove(BotOpenMove):
	def __init__(self,parent,dim,komi):
		BotOpenMove.__init__(self,parent)
		self.name='Gnugo'
		self.configure(text=self.name)
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		if Config.getboolean('GnuGo', 'NeededForReview'):
			self.okbot=True
			try:
				gnugo_command_line=[Config.get("GnuGo", "Command")]+Config.get("GnuGo", "Parameters").split()
				gnugo=GnuGo_gtp(gnugo_command_line)
				ok=gnugo.boardsize(dim)
				gnugo.reset()
				gnugo.komi(komi)
				self.bot=gnugo
				if not ok:
					raise AbortedException("Boardsize value rejected by %s"%self.name)
			except Exception, e:
				log("Could not launch "+self.name)
				log(e)
				self.config(state='disabled')
				self.okbot=False
		else:
			self.okbot=False
			self.config(state='disabled')


import getopt
if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title=_('Select a file'),filetypes = [(_('SGF file'), '.sgf')])
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
		try:
			parameters=getopt.getopt(argv[1:], '', ['range=', 'color=', 'komi=',"variation="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		for filename in parameters[1]:
			log("File to analyse:",filename)
			
			move_selection,intervals,variation,komi=parse_command_line(filename,parameters[0])
			
			top = Tk()
			app=RunAnalysis(top,filename,move_selection,intervals,variation-1,komi)
			app.propose_review=app.close_app
			app.pack()
			top.mainloop()





