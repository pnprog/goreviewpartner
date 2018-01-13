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

from time import sleep
import os
import threading
import ttk

import toolbox
from toolbox import *
from toolbox import _

import tkMessageBox


class RunAnalysis(RunAnalysisBase):

	def run_analysis(self,current_move):
		
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		leela_zero=self.leela_zero
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			log()
			linelog("move",str(current_move)+'/'+str(max_move))
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
			else:
				additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))

			if player_color in ('w',"W"):
				log("leela Zero play white")
				answer=leela_zero.play_white()
			else:
				log("leela Zero play black")
				answer=leela_zero.play_black()

			
			all_moves=leela_zero.get_all_leela_zero_moves()
			if (answer.lower() not in ["pass","resign"]):
				
				one_move.set("CBM",answer.lower()) #Computer Best Move

				all_moves2=all_moves[:]
				nb_undos=1
				#log("====move",current_move+1,all_moves[0],'~',answer)
				
				
				#making sure the first line of play is more than one move deep				
				while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]) and (nb_undos<=20):
					log("going deeper for first line of play (",nb_undos,")")

					if player_color in ('w',"W") and nb_undos%2==0:
						answer=leela_zero.play_white()
					elif player_color in ('w',"W") and nb_undos%2==1:
						answer=leela_zero.play_black()
					elif player_color not in ('w',"W") and nb_undos%2==0:
						answer=leela_zero.play_black()
					else:
						answer=leela_zero.play_white()
					nb_undos+=1
					

					

					#linelog(all_moves[0],'+',answer)
					all_moves2=leela_zero.get_all_leela_zero_moves()
					if (answer.lower() not in ["pass","resign"]):
						
						#log('+',all_moves2)
						all_moves[0][1]+=" "+all_moves2[0][1]

						if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
							all_moves[0][2]=all_moves2[0][2]
						else:
							all_moves[0][2]=100-all_moves2[0][2]

					else:
						log()
						log("last play on the fist of play was",answer,"so leaving")
				
				for u in range(nb_undos):
					#log("undo...")
					leela_zero.undo()
				
				best_move=True
				#variation=-1
				log("Number of alternative sequences:",len(all_moves))
				#log(all_moves)
				for sequence_first_move,one_sequence,one_value_network,one_policy_network,one_nodes in all_moves[:self.maxvariations]:
					log("Adding sequence starting from",sequence_first_move)
					previous_move=one_move.parent
					current_color=player_color
										
					first_variation_move=True
					for one_deep_move in one_sequence.split(' '):
						if one_deep_move.lower() in ["pass","resign"]:
							log("Leaving the variation when encountering",one_deep_move.lower())
							break
						i,j=gtp2ij(one_deep_move)
						new_child=previous_move.new_child()
						new_child.set_move(current_color,(i,j))

						
						if player_color=='b':
							if first_variation_move:
								first_variation_move=False
								variation_comment=_("Value network black/white win probability for this move: ")+str(one_value_network)+'%/'+str(100-one_value_network)
								variation_comment+="\n"+_("Policy network value for this move: ")+str(one_policy_network)+'%'
								variation_comment+="\n"+_("Number of playouts used to estimate this variation: ")+str(one_nodes)
								new_child.add_comment_text(variation_comment)
							if best_move:
								best_move=False
								additional_comments+=_("Value network black/white win probability for this move: ")+str(one_value_network)+'%/'+str(100-one_value_network)+'%'
								one_move.set("BWR",str(one_value_network)+'%') #Black value network
								one_move.set("WWR",str(100-one_value_network)+'%') #White value network
						else:
							if first_variation_move:
								first_variation_move=False
								variation_comment=_("Value network black/white win probability for this move: ")+str(100-one_value_network)+'%/'+str(one_value_network)
								variation_comment+="\n"+_("Policy network value for this move: ")+str(one_policy_network)+'%'
								variation_comment+="\n"+_("Number of playouts used to estimate this variation: ")+str(one_nodes)
								new_child.add_comment_text(variation_comment)
							if best_move:
								best_move=False
								additional_comments+=_("Value network black/white win probability for this move: ")+str(100-one_value_network)+'%/'+str(one_value_network)+'%'
								one_move.set("WWR",str(one_value_network)+'%') #White value network
								one_move.set("BWR",str(100-one_value_network)+'%') #Black value network
									
						
						previous_move=new_child
						if current_color in ('w','W'):
							current_color='b'
						else:
							current_color='w'
				log("==== no more sequences =====")
				

			else:
				log('adding "'+answer.lower()+'" to the sgf file')
				additional_comments+="\n"+_("For this position, %s would %s"%("Leela Zero",answer.lower()))
				if answer.lower()=="pass":
					leela_zero.undo()
			
			
			one_move.add_comment_text(additional_comments)
			
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())

			self.total_done+=1
		else:
			log("Move",current_move,"not in the list of moves to be analysed, skipping")

		linelog("now asking Leela Zero to play the game move:")
		if player_color in ('w',"W"):
			log("white at",ij2gtp(player_move))
			leela_zero.place_white(ij2gtp(player_move))
		else:
			log("black at",ij2gtp(player_move))
			leela_zero.place_black(ij2gtp(player_move))
		log("Analysis for this move is completed")
	
	
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text=_("Now closing, please wait..."))
		self.update_idletasks()
		log("killing leela Zero")
		self.leela_zero.close()
		log("destroying")
		self.destroy()
	

	def initialize_bot(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		self.g=open_sgf(self.filename)
		
		leaves=get_all_sgf_leaves(self.g.get_root())
		log("keeping only variation",self.variation)
		keep_only_one_leaf(leaves[self.variation][0])
		
		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size

		try:
			leela_zero_command_line=Config.get("Leela_Zero", "Command")
		except:
			show_error(_("The config.ini file does not contain entry for %s command line!")%"Leela ZEro")
			return False
		
		if not leela_zero_command_line:
			show_error(_("The config.ini file does not contain command line for %s!")%"Leela Zero")
			return False
		log("Starting Leela Zero...")
		try:
			leela_zero_command_line=[Config.get("Leela_Zero", "Command")]+Config.get("Leela_Zero", "Parameters").split()
			leela_zero=Leela_Zero_gtp(leela_zero_command_line)
		except:
			show_error((_("Could not run %s using the command from config.ini file:")%"Leela Zero")+"\n"+" ".join(leela_zero_command_line)+"\n"+str(e))
			return False
		log("Leela Zero started")
		log("Leela Zero identification through GTP..")
		try:
			self.bot_name=leela_zero.name()
		except Exception, e:
			show_error((_("%s did not replied as expected to the GTP name command:")%"Leela Zero")+"\n"+str(e))
			return False
		
		if self.bot_name!="Leela Zero":
			show_error((_("%s did not identified itself as expected:")%"Leela Zero")+"\n'Leela Zero' != '"+self.bot_name+"'")
			return False
		log("Leela Zero identified itself properly")
		log("Checking version through GTP...")
		try:
			self.bot_version=leela_zero.version()
		except Exception, e:
			show_error((_("%s did not replied as expected to the GTP version command:")%"Leela Zero")+"\n"+str(e))
			return False
		log("Version: "+self.bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		
		try:
			ok=leela_zero.boardsize(size)
		except:
			show_error((_("Could not set the goboard size using GTP command. Check that %s is running in GTP mode.")%"Leela Zero"))
			return False
		if not ok:
			show_error(_("%s rejected this board size (%ix%i)")%("Leela Zero",size,size))
			return False
		log("Clearing the board")
		leela_zero.reset()
		self.leela_zero=leela_zero
		
		self.time_per_move=0
		try:
			time_per_move=Config.get("Leela_Zero", "TimePerMove")
			if time_per_move:
				time_per_move=int(time_per_move)
				if time_per_move>0:
					log("Setting time per move")
					leela_zero.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
					self.time_per_move=time_per_move
		except:
			log("Wrong value for Leela Zero thinking time:",Config.get("Leela_Zero", "TimePerMove"))
			log("Erasing that value in the config file")
			Config.set("Leela_Zero","TimePerMove","")
			Config.write(open(config_file,"w"))
		
		log("Setting komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)
		leela_zero.komi(self.komi)

		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		log("Adding handicap stones, if any")
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					leela_zero.place_white(move)
				else:
					log("Adding initial black stone at",move)
					leela_zero.place_black(move)
		log("Leela Zero initialization completed")
		
		return leela_zero


class Leela_Zero_gtp(gtp):

	def get_leela_zero_final_score(self):
		self.write("final_score")
		answer=self.readline()
		try:
			return " ".join(answer.split(" ")[1:])
		except:
			raise GtpException("GtpException in Get_leela_zero_final_score()")

	def get_leela_zero_influence(self):
		self.write("influence")
		one_line=self.readline() #empty line
		buff=[]
		while self.stderr_queue.empty():
			sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		buff.reverse()
		#log(buff)
		influence=[]
		for i in range(self.size):
			one_line=buff[i].strip()
			one_line=one_line.replace(".","0").replace("x","1").replace("o","2").replace("O","0").replace("X","0").replace("w","1").replace("b","2")
			one_line=[int(s) for s in one_line.split(" ")]
			influence.append(one_line)
		
		return influence

	def get_all_leela_zero_moves(self):
		buff_size=18
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		
		buff.reverse()
		
		answers=[]
		for err_line in buff:
			if " ->" in err_line:
				#log(err_line)
				one_answer=err_line.strip().split(" ")[0]
				nodes=int(err_line.strip().split("(")[0].split("->")[1].replace(" ",""))
				value_network=float(err_line.split("(V:")[1].split('%')[0].strip())
				policy_network=float(err_line.split("(N:")[1].split('%)')[0].strip())
				sequence=err_line.split("PV: ")[1].strip()
				
				answers=[[one_answer,sequence,value_network,policy_network,nodes]]+answers

		return answers


class LeelaZeroSettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		log("Initializing Leela Zero setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		row=0

		Label(self,text=_("%s settings")%"Leela Zero").grid(row=row+1,column=1)
		Label(self,text=_("Command")).grid(row=row+2,column=1)
		LeelaZeroCommand = StringVar() 
		LeelaZeroCommand.set(Config.get("Leela_Zero","Command"))
		Entry(self, textvariable=LeelaZeroCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row+2,column=1)
		LeelaZeroParameters = StringVar() 
		LeelaZeroParameters.set(Config.get("Leela_Zero","Parameters"))
		Entry(self, textvariable=LeelaZeroParameters, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text=_("Time per move (s)")).grid(row=row+2,column=1)
		TimePerMove = StringVar() 
		TimePerMove.set(Config.get("Leela_Zero","TimePerMove"))
		Entry(self, textvariable=TimePerMove, width=30).grid(row=row+2,column=2)
		row+=1
		LeelaZeroNeededForReview = BooleanVar(value=Config.getboolean('Leela_Zero', 'NeededForReview'))
		LeelaZeroCheckbutton=Checkbutton(self, text=_("Needed for review"), variable=LeelaZeroNeededForReview,onvalue=True,offvalue=False)
		LeelaZeroCheckbutton.grid(row=row+2,column=1)
		LeelaZeroCheckbutton.var=LeelaZeroNeededForReview

		self.LeelaZeroCommand=LeelaZeroCommand
		self.LeelaZeroParameters=LeelaZeroParameters
		self.TimePerMove=TimePerMove
		self.LeelaZeroNeededForReview=LeelaZeroNeededForReview

	def save(self):
		log("Saving Leela Zero settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set("Leela_Zero","Command",self.LeelaZeroCommand.get())
		Config.set("Leela_Zero","Parameters",self.LeelaZeroParameters.get())
		Config.set("Leela_Zero","TimePerMove",self.TimePerMove.get())
		Config.set("Leela_Zero","NeededForReview",self.LeelaZeroNeededForReview.get())
		
		Config.write(open(config_file,"w"))




class LeelaZeroOpenMove(BotOpenMove):
	def __init__(self,parent,dim,komi):
		BotOpenMove.__init__(self,parent)
		self.name='Leela Zero'
		self.configure(text=self.name)
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)

		if Config.getboolean('Leela_Zero', 'NeededForReview'):
			self.okbot=True
			try:
				leela_zero_command_line=[Config.get("Leela_Zero", "Command")]+Config.get("Leela_Zero", "Parameters").split()
				leela_zero=Leela_Zero_gtp(leela_zero_command_line)
				ok=leela_zero.boardsize(dim)
				leela_zero.reset()
				leela_zero.komi(komi)
				try:
					time_per_move=Config.get("Leela_Zero", "TimePerMove")
					if time_per_move:
						time_per_move=int(time_per_move)
						if time_per_move>0:
							leela_zero.set_time(main_time=time_per_move,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				except:
					pass #silent fail...
				self.bot=leela_zero
				if not ok:
					raise AbortedException("Boardsize value rejected by "+self.name)
			except Exception, e:
				log("Could not launch "+self.name)
				log(e)
				self.config(state='disabled')
				self.okbot=False
		else:
			self.okbot=False
			self.config(state='disabled')




if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title=_('Select a file'),filetypes = [('sgf', '.sgf')])
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		top = Tk()
		toolbox.RunAnalysis=RunAnalysis
		RangeSelector(top,filename,bots=[("Leela Zero",RunAnalysis)]).pack()
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
	




