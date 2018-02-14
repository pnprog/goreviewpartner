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
		
		gnugo=gnugo_starting_procedure(self.g,self.profile)
		self.nb_workers=self.nb_variations

		log("Starting all GnuGo workers")
		self.workers=[]
		for w in range(self.nb_workers):
			log("\t Starting worker",w+1)
			gnugo_worker=gnugo_starting_procedure(self.g,self.profile)
			self.workers.append(gnugo_worker)
		log("All workers ready")
		
		self.gnugo=gnugo
		self.time_per_move=0
		return gnugo

def gnugo_starting_procedure(sgf_g,profile="slow",silentfail=False):
	return bot_starting_procedure("GnuGo","GNU Go",GnuGo_gtp,sgf_g,profile,silentfail)


class RunAnalysis(GnuGoAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(GnuGoAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)

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
		bot="GnuGo"
		row=0
		Label(self,text=_("%s settings")%bot, font="-weight bold").grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Maximum number of variations")).grid(row=row,column=1,sticky=W)
		Variations = StringVar()
		Variations.set(Config.get(bot,"Variations"))
		Entry(self, textvariable=Variations, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Deepness for each variation")).grid(row=row,column=1,sticky=W)
		Deepness = StringVar() 
		Deepness.set(Config.get(bot,"Deepness"))
		Entry(self, textvariable=Deepness, width=30).grid(row=row,column=2)
		
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Slow profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		SlowCommand = StringVar() 
		SlowCommand.set(Config.get(bot,"SlowCommand"))
		Entry(self, textvariable=SlowCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		SlowParameters = StringVar() 
		SlowParameters.set(Config.get(bot,"SlowParameters"))
		Entry(self, textvariable=SlowParameters, width=30).grid(row=row,column=2)

		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Fast profile parameters")).grid(row=row,column=1,sticky=W)

		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		FastCommand = StringVar() 
		FastCommand.set(Config.get(bot,"FastCommand"))
		Entry(self, textvariable=FastCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		FastParameters = StringVar() 
		FastParameters.set(Config.get(bot,"FastParameters"))
		Entry(self, textvariable=FastParameters, width=30).grid(row=row,column=2)

		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("%s availability")%bot).grid(row=row,column=1,sticky=W)
		row+=1
		
		value={"slow":_("Slow profile"),"fast":_("Fast profile"),"both":_("Both profiles"),"none":_("None")}
		
		Label(self,text=_("Static analysis")).grid(row=row,column=1,sticky=W)
		analysis_bot = StringVar()
		analysis_bot.set(value[Config.get(bot,"AnalysisBot")])
		OptionMenu(self,analysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis")).grid(row=row,column=1,sticky=W)
		liveanalysis_bot = StringVar()
		liveanalysis_bot.set(value[Config.get(bot,"LiveAnalysisBot")])
		OptionMenu(self,liveanalysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis as black or white")).grid(row=row,column=1,sticky=W)
		liveplayer_bot = StringVar()
		liveplayer_bot.set(value[Config.get(bot,"LivePlayerBot")])
		OptionMenu(self,liveplayer_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("When opening a position for manual play")).grid(row=row,column=1,sticky=W)
		review_bot = StringVar()
		review_bot.set(value[Config.get(bot,"ReviewBot")])
		OptionMenu(self,review_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		

		self.SlowCommand=SlowCommand
		self.SlowParameters=SlowParameters
		self.Variations=Variations
		self.Deepness=Deepness
		self.FastCommand=FastCommand
		self.FastParameters=FastParameters
		
		self.analysis_bot=analysis_bot
		self.liveanalysis_bot=liveanalysis_bot
		self.liveplayer_bot=liveplayer_bot
		self.review_bot=review_bot
		
		
	def save(self):
		log("Saving GnuGo settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		bot="GnuGo"
		
		Config.set(bot,"SlowCommand",self.SlowCommand.get())
		Config.set(bot,"SlowParameters",self.SlowParameters.get())
		Config.set(bot,"Variations",self.Variations.get())
		Config.set(bot,"Deepness",self.Deepness.get())
		Config.set(bot,"FastCommand",self.FastCommand.get())
		Config.set(bot,"FastParameters",self.FastParameters.get())
		
		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		Config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		Config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		Config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		Config.set(bot,"ReviewBot",value[self.review_bot.get()])
				
		Config.write(open(config_file,"w"))

class GnuGoOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
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
		bot=GnuGo
		
		slowbot=bot
		slowbot['profile']="slow"
		fastbot=dict(bot)
		fastbot['profile']="fast"
		RangeSelector(top,filename,bots=[slowbot, fastbot]).pack()
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

