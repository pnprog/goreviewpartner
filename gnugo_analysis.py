# -*- coding: utf-8 -*-

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from Tkinter import *
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



class GnuGoAnalysis():

	def run_analysis(self,current_move):
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		
		gnugo=self.gnugo
		log()
		log("==============")
		log("move",str(current_move))
		
		final_score=gnugo.get_gnugo_estimate_score()
		#linelog(final_score)
		additional_comments=_("Move %i")%current_move


		es=final_score.split()[0]
		one_move.set("ES",es) #estimated score
		
		if es[0]=="B":
			lbs="B%+d"%(-1*float(final_score.split()[3][:-1]))
			ubs="B%+d"%(-1*float(final_score.split()[5][:-1]))
		else:
			ubs="W%+d"%(float(final_score.split()[3][:-1]))
			lbs="W%+d"%(float(final_score.split()[5][:-1]))
		
		one_move.set("UBS",ubs) #upper bound score
		one_move.set("LBS",lbs) #lower bound score
		
		additional_comments=""
		"""
		if player_color in ('w',"W"):
			additional_comments+="\n"+(_("White to play, in the game, white played %s")%ij2gtp(player_move))
		else:
			additional_comments+="\n"+(_("Black to play, in the game, black played %s")%ij2gtp(player_move))
		"""
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
		log()
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
			elif answer.lower()=="resign":
				if self.stop_at_first_resign:
					log("")
					log("The analysis will stop now")
					log("")
					self.move_range=[]
		
		
		one_move.add_comment_text(additional_comments)
		
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
		
		return answer #returning the best move, necessary for live analysis
		
	def run_all_analysis(self):
		#GnuGo needs to rewrite this method because it additionnaly deals with all the workers
		self.current_move=1
		
		while self.current_move<=self.max_move:
			if self.current_move in self.move_range:
				self.run_analysis(self.current_move)
			elif self.move_range:
				log("Move",self.current_move,"not in the list of moves to be analysed, skipping")
			
			if self.move_range:
				linelog("now asking "+self.bot.bot_name+" to play the game move:")
				one_move=go_to_move(self.move_zero,self.current_move)
				player_color,player_move=one_move.get_move()
				if player_color in ('w',"W"):
					log("white at",ij2gtp(player_move))
					self.bot.place_white(ij2gtp(player_move))
					for worker in self.workers:
						worker.place_white(ij2gtp(player_move))
				else:
					log("black at",ij2gtp(player_move))
					self.bot.place_black(ij2gtp(player_move))
					for worker in self.workers:
						worker.place_black(ij2gtp(player_move))
				
				log("Analysis for this move is completed")
			else:
				#the bot has proposed to resign, and resign_at_first_stop is ON
				pass
			
			self.current_move+=1
			self.update_queue.put(self.current_move)
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
			self.total_done+=1
			
	def terminate_bot(self):
		log("killing gnugo")
		self.gnugo.close()
		log("killing gnugo workers")
		for w in self.workers:
			w.close()

	def initialize_bot(self):
		
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
		
		gnugo=gnugo_starting_procedure(self.g,"slow")
		self.nb_workers=self.nb_variations

		log("Starting all GnuGo workers")
		self.workers=[]
		for w in range(self.nb_workers):
			log("\t Starting worker",w+1)
			gnugo_worker=gnugo_starting_procedure(self.g,"slow")
			self.workers.append(gnugo_worker)
		log("All workers ready")
		
		self.gnugo=gnugo
		self.time_per_move=0
		return gnugo

def gnugo_starting_procedure(sgf_g,profil="slow",silentfail=False):
	return bot_starting_procedure("GnuGo","GNU Go",GnuGo_gtp,sgf_g,profil,silentfail)


class RunAnalysis(GnuGoAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi)

class LiveAnalysis(GnuGoAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename):
		LiveAnalysisBase.__init__(self,g,filename)

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
			return answer[2:]
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
		Label(self,text=_("%s settings")%"GnuGo", font="-weight bold").grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		Command = StringVar() 
		Command.set(Config.get("GnuGo","Command"))
		Entry(self, textvariable=Command, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		Parameters = StringVar() 
		Parameters.set(Config.get("GnuGo","Parameters"))
		Entry(self, textvariable=Parameters, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Maximum number of variations")).grid(row=row,column=1,sticky=W)
		Variations = StringVar()
		Variations.set(Config.get("GnuGo","Variations"))
		Entry(self, textvariable=Variations, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Deepness for each variation")).grid(row=row,column=1,sticky=W)
		Deepness = StringVar() 
		Deepness.set(Config.get("GnuGo","Deepness"))
		Entry(self, textvariable=Deepness, width=30).grid(row=row,column=2)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		NeededForReview = BooleanVar(value=Config.getboolean('GnuGo', 'NeededForReview'))
		Cbutton=Checkbutton(self, text=_("Needed for review"), variable=NeededForReview,onvalue=True,offvalue=False)
		Cbutton.grid(row=row,column=1,sticky=W)
		Cbutton.var=NeededForReview

		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		ReviewCommand = StringVar() 
		ReviewCommand.set(Config.get("GnuGo","ReviewCommand"))
		Entry(self, textvariable=ReviewCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		ReviewParameters = StringVar() 
		ReviewParameters.set(Config.get("GnuGo","ReviewParameters"))
		Entry(self, textvariable=ReviewParameters, width=30).grid(row=row,column=2)

		self.Command=Command
		self.Parameters=Parameters
		self.Variations=Variations
		self.Deepness=Deepness
		self.NeededForReview=NeededForReview
		self.ReviewCommand=ReviewCommand
		self.ReviewParameters=ReviewParameters

	def save(self):
		log("Saving GnuGo settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Config.set("GnuGo","Command",self.Command.get())
		Config.set("GnuGo","Parameters",self.Parameters.get())
		Config.set("GnuGo","Variations",self.Variations.get())
		Config.set("GnuGo","Deepness",self.Deepness.get())
		Config.set("GnuGo","NeededForReview",self.NeededForReview.get())
		Config.set("GnuGo","ReviewCommand",self.ReviewCommand.get())
		Config.set("GnuGo","ReviewParameters",self.ReviewParameters.get())
		
		
		Config.write(open(config_file,"w"))

class GnuGoOpenMove(BotOpenMove):
	def __init__(self,sgf_g):
		BotOpenMove.__init__(self,sgf_g)
		self.name='Gnugo'
		self.my_starting_procedure=gnugo_starting_procedure

	
GnuGo={}
GnuGo['name']="GnuGo"
GnuGo['gtp_name']="GNU Go"
GnuGo['analysis']=GnuGoAnalysis
GnuGo['openmove']=GnuGoOpenMove
GnuGo['settings']=GnuGoSettings
GnuGo['gtp']=GnuGo_gtp
GnuGo['liveanalysis']=LiveAnalysis
GnuGo['runanalysis']=RunAnalysis
GnuGo['starting']=gnugo_starting_procedure

import getopt
if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = open_sgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			sys.exit()
		log("filename:",filename)
		
		top = Tk()
		RangeSelector(top,filename,bots=[GnuGo]).pack()
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		top=None
		batch=[]
		
		for filename in parameters[1]:
			
			move_selection,intervals,variation,komi,nogui=parse_command_line(filename,parameters[0])
			if nogui:
				log("File to analyse:",filename)
				app=RunAnalysis("no-gui",filename,move_selection,intervals,variation-1,komi)
				app.terminate_bot()
			else:
				if not top:
					top = Tk()
					top.withdraw()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi]
				batch.append(one_analysis)
		
		if not nogui:
			top.after(1,lambda: batch_analysis(top,batch))
			top.mainloop()

