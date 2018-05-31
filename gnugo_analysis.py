# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from Tkinter import *
import os
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
		es=worker.get_gnugo_estimate_score()
		for u in range(undos):
			worker.undo()
		return [sequence.strip(),es]
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

		es=final_score.split()[0]
		
		
		if es[0]=="B":
			lbs="B%+d"%(-1*float(final_score.split()[3][:-1]))
			ubs="B%+d"%(-1*float(final_score.split()[5][:-1]))
		else:
			ubs="W%+d"%(float(final_score.split()[3][:-1]))
			lbs="W%+d"%(float(final_score.split()[5][:-1]))
		
		node_set(one_move,"ES",es)
		node_set(one_move,"UBS",ubs)
		node_set(one_move,"LBS",lbs)
		

		if player_color in ('w',"W"):
			log("gnugo plays white")
			top_moves=gnugo.gnugo_top_moves_white()
			answer=gnugo.play_white()
		else:
			log("gnugo plays black")
			top_moves=gnugo.gnugo_top_moves_black()
			answer=gnugo.play_black()

		log("====","Gnugo answer:",answer)
		node_set(one_move,"CBM",answer)
		
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
					if type(one_thread.sequence)!=type(["list"]):
						raise AbortedException(_("GnuGo thread failed:")+"\n"+str(one_thread.sequence))
					
					one_sequence=one_thread.one_top_move+" "+one_thread.sequence[0]
					es=one_thread.sequence[1]
					one_sequence=one_sequence.strip()
					log(">>>>>>",one_sequence)
					previous_move=one_move.parent
					current_color=player_color
					first_move=True
					for one_deep_move in one_sequence.split(' '):
						if one_deep_move.lower() not in ['resign','pass']:
							i,j=gtp2ij(one_deep_move)
							new_child=previous_move.new_child()
							node_set(new_child,current_color,(i,j))
							if first_move:
								first_move=False
								node_set(new_child,"ES",es)
							previous_move=new_child
							if current_color in ('w','W'):
								current_color='b'
							else:
								current_color='w'

		else:
			gnugo.undo()
		#one_move.add_comment_text(additional_comments)
		
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
			node_set(one_move.parent,"TB",black_influence_points)
		
		if white_influence_points!=[]:
			node_set(one_move.parent,"TW",white_influence_points)
		
		return answer #returning the best move, necessary for live analysis
	
	def play(self,gtp_color,gtp_move):#GnuGo needs to redifine this method to apply it to all its workers
		if gtp_color=='w':
			self.bot.place_white(gtp_move)
			for worker in self.workers:
				worker.place_white(gtp_move)
		else:
			self.bot.place_black(gtp_move)
			for worker in self.workers:
				worker.place_black(gtp_move)
	
	def undo(self):
		self.bot.undo()
		for worker in self.workers:
			worker.undo()
	
	def terminate_bot(self):
		log("killing gnugo")
		self.gnugo.close()
		log("killing gnugo workers")
		for w in self.workers:
			w.close()

	def initialize_bot(self):
		
		self.nb_variations=4
		try:
			self.nb_variations=int(grp_config.get("GnuGo", "variations"))
		except:
			grp_config.set("GnuGo", "variations",self.nb_variations)
		
		self.deepness=4
		try:
			self.deepness=int(grp_config.get("GnuGo", "deepness"))
		except:
			grp_config.set("GnuGo", "deepness",self.deepness)
		
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
	
	def quick_evaluation(self,color):
		return variation_data_formating["ES"]%self.get_gnugo_estimate_score()
	
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
				float(value)
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
				float(value)
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
		self.parent=parent
		log("Initializing GnuGo setting interface")
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
		Variations.set(grp_config.get(bot,"Variations"))
		Entry(self, textvariable=Variations, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Deepness for each variation")).grid(row=row,column=1,sticky=W)
		Deepness = StringVar() 
		Deepness.set(grp_config.get(bot,"Deepness"))
		Entry(self, textvariable=Deepness, width=30).grid(row=row,column=2)
		
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Slow profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		SlowCommand = StringVar() 
		SlowCommand.set(grp_config.get(bot,"SlowCommand"))
		Entry(self, textvariable=SlowCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		SlowParameters = StringVar() 
		SlowParameters.set(grp_config.get(bot,"SlowParameters"))
		Entry(self, textvariable=SlowParameters, width=30).grid(row=row,column=2)
		row+=1
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(GnuGo_gtp,"slow")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Fast profile parameters")).grid(row=row,column=1,sticky=W)

		row+=1
		Label(self,text=_("Command")).grid(row=row,column=1,sticky=W)
		FastCommand = StringVar() 
		FastCommand.set(grp_config.get(bot,"FastCommand"))
		Entry(self, textvariable=FastCommand, width=30).grid(row=row,column=2)
		row+=1
		Label(self,text=_("Parameters")).grid(row=row,column=1,sticky=W)
		FastParameters = StringVar() 
		FastParameters.set(grp_config.get(bot,"FastParameters"))
		Entry(self, textvariable=FastParameters, width=30).grid(row=row,column=2)
		row+=1
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(GnuGo_gtp,"fast")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("%s availability")%bot).grid(row=row,column=1,sticky=W)
		row+=1
		
		value={"slow":_("Slow profile"),"fast":_("Fast profile"),"both":_("Both profiles"),"none":_("None")}
		
		Label(self,text=_("Static analysis")).grid(row=row,column=1,sticky=W)
		analysis_bot = StringVar()
		analysis_bot.set(value[grp_config.get(bot,"AnalysisBot")])
		OptionMenu(self,analysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis")).grid(row=row,column=1,sticky=W)
		liveanalysis_bot = StringVar()
		liveanalysis_bot.set(value[grp_config.get(bot,"LiveAnalysisBot")])
		OptionMenu(self,liveanalysis_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("Live analysis as black or white")).grid(row=row,column=1,sticky=W)
		liveplayer_bot = StringVar()
		liveplayer_bot.set(value[grp_config.get(bot,"LivePlayerBot")])
		OptionMenu(self,liveplayer_bot,_("Slow profile"),_("Fast profile"),_("Both profiles"),_("None")).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text=_("When opening a position for manual play")).grid(row=row,column=1,sticky=W)
		review_bot = StringVar()
		review_bot.set(value[grp_config.get(bot,"ReviewBot")])
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
		
		bot="GnuGo"
		
		grp_config.set(bot,"SlowCommand",self.SlowCommand.get())
		grp_config.set(bot,"SlowParameters",self.SlowParameters.get())
		grp_config.set(bot,"Variations",self.Variations.get())
		grp_config.set(bot,"Deepness",self.Deepness.get())
		grp_config.set(bot,"FastCommand",self.FastCommand.get())
		grp_config.set(bot,"FastParameters",self.FastParameters.get())
		
		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		grp_config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		grp_config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		grp_config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		grp_config.set(bot,"ReviewBot",value[self.review_bot.get()])
				

		if self.parent.parent.refresh!=None:
			self.parent.parent.refresh()

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
		
		top = Application()
		bot=GnuGo
		
		slowbot=bot
		slowbot['profile']="slow"
		fastbot=dict(bot)
		fastbot['profile']="fast"
		popup=RangeSelector(top,filename,bots=[slowbot, fastbot])
		top.add_popup(popup)
		top.mainloop()
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation=", "profil="])
		except Exception, e:
			show_error(str(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		app=None
		batch=[]
		
		for filename in parameters[1]:
			move_selection,intervals,variation,komi,nogui,profil=parse_command_line(filename,parameters[0])
			if nogui:
				log("File to analyse:",filename)
				popup=RunAnalysis("no-gui",filename,move_selection,intervals,variation-1,komi,profil)
				popup.terminate_bot()
			else:
				if not app:
					app = Application()
				one_analysis=[RunAnalysis,filename,move_selection,intervals,variation-1,komi,profil]
				batch.append(one_analysis)
		
		if not nogui:
			app.after(100,lambda: batch_analysis(app,batch))
			app.mainloop()
