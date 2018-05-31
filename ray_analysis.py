# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp, GtpException
import sys
from gomill import sgf, sgf_moves
from sys import exit,argv
from Tkinter import *

import os
import threading
import ttk

from toolbox import *
from toolbox import _

from time import time


class RayAnalysis():

	def run_analysis(self,current_move):
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		ray=self.ray
		
		log()
		log("==============")
		log("move",current_move)
		
		#additional_comments=""
		if player_color in ('w',"W"):
			log("ray play white")
			answer=ray.get_ray_stat("white")
		else:
			log("ray play black")
			answer=ray.get_ray_stat("black")

		if current_move>2:
			es=ray.final_score()
			node_set(one_move,"ES",es)
			
		log(len(answer),"sequences")

		if len(answer)>0:
			best_move=True
			for sequence_first_move,count,simulation,policy,value,win,one_sequence in answer[:self.maxvariations]:
				log("Adding sequence starting from",sequence_first_move)
				if best_move:
					best_answer=sequence_first_move
					node_set(one_move,"CBM",best_answer)
					
				previous_move=one_move.parent
				current_color=player_color
				
				one_sequence=player_color+' '+sequence_first_move+' '+one_sequence
				one_sequence=one_sequence.replace("b ",',b')
				one_sequence=one_sequence.replace("w ",',w')
				one_sequence=one_sequence.replace(" ",'')
				#log("one_sequence=",one_sequence[1:])
				first_variation_move=True
				for one_deep_move in one_sequence.split(',')[1:]:
					if one_deep_move.lower() in ["pass","resign"]:
						log("Leaving the variation when encountering",one_deep_move.lower())
						break
					current_color=one_deep_move[0]
					one_deep_move=one_deep_move[1:].strip()
					if one_deep_move.lower()!="pass":
						i,j=gtp2ij(one_deep_move)
						new_child=previous_move.new_child()
						node_set(new_child,current_color,(i,j))
						if first_variation_move:
							first_variation_move=False
							if win:
								if current_color=='b':
									winrate=str(float(win))+'%/'+str(100-float(win))+'%'
								else:
									winrate=str(100-float(win))+'%/'+str(win)+'%'
								node_set(new_child,"BWWR",winrate)
								if best_move:
									node_set(one_move,"BWWR",winrate)
							
							if count:
								node_set(new_child,"PLYO",count)
								
							if simulation:
								simulation+="%"
								if current_color=='b':
									black_value=simulation
									white_value=opposite_rate(black_value)
								else:
									white_value=simulation
									black_value=opposite_rate(white_value)

								node_set(new_child,"MCWR",black_value+'/'+white_value)
								if best_move:
									node_set(one_move,"MCWR",black_value+'/'+white_value)
									
								
							if policy:
								node_set(new_child,"PNV",policy+"%")
								
							if value:
								if player_color=='b':
									black_value=value+"%"
									white_value=opposite_rate(black_value)
								else:
									white_value=value+"%"
									black_value=opposite_rate(white_value)
								node_set(new_child,"VNWR",black_value+'/'+white_value)
								if best_move:
									node_set(one_move,"VNWR",black_value+'/'+white_value)
							
							if best_move:
								best_move=False
							
						previous_move=new_child
					else:
						break

			log("==== no more sequences =====")
		
		#one_move.add_comment_text(additional_comments)
		return best_answer

	
	def initialize_bot(self):
		ray=ray_starting_procedure(self.g,self.profile)
		self.ray=ray
		self.time_per_move=0
		return ray

def ray_starting_procedure(sgf_g,profile="slow",silentfail=False):
	return bot_starting_procedure("Ray","Rayon",Ray_gtp,sgf_g,profile,silentfail)


class RunAnalysis(RayAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile)

class LiveAnalysis(RayAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile="slow"):
		LiveAnalysisBase.__init__(self,g,filename,profile)

class Ray_gtp(gtp):
	def quick_evaluation(self,color):
		
		if color==2:
			answer=self.get_ray_stat("white")
		else:
			answer=self.get_ray_stat("black")
		
		unused,unused,unused,unused,unused,win,unused=answer[0]
		
		txt=""
		if win:
			if color==1:
				winrate=str(float(win))+'%/'+str(100-float(win))+'%'
			else:
				winrate=str(100-float(win))+'%/'+str(win)+'%'
			txt+= variation_data_formating["BWWR"]%winrate

		return txt
	
	def get_ray_stat(self,color):
		t0=time()
		self.write("ray-stat "+color)
		header_line=self.readline()
		log(">>>>>>>>>>>>",time()-t0)
		log("HEADER:",header_line)
		sequences=[]
		
		for i in range(10):
			one_line=self.process.stdout.readline().strip()
			if one_line.strip()=="":
				break
			log(one_line)
			#log("\t",[s.strip() for s in one_line.split("|")[1:]])
			sequences.append([s.strip() for s in one_line.split("|")[1:]])
		
		if sequences[0][5]=="":
			log("===================================================================")
			log("=== WARNING: Ray thinking time is too short for proper analysis ===")
			log("===================================================================")
			log("\a") #let's make this annoying enough :)
		return sequences

class RaySettings(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.parent=parent
		log("Initializing Ray setting interface")
		
		bot="Ray"
		
		row=0
		Label(self,text=_("%s settings")%bot, font="-weight bold").grid(row=row,column=1,sticky=W)
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
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(Ray_gtp,"slow")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Fast profile parameters")).grid(row=row,column=1,sticky=W)
		row+=1
		
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
		Button(self, text=_("Test"),command=lambda: self.parent.parent.test(Ray_gtp,"fast")).grid(row=row,column=1,sticky=W)


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
		self.FastCommand=FastCommand
		self.FastParameters=FastParameters
		
		self.analysis_bot=analysis_bot
		self.liveanalysis_bot=liveanalysis_bot
		self.liveplayer_bot=liveplayer_bot
		self.review_bot=review_bot
	
	def save(self):
		log("Saving Ray settings")
		
		bot="Ray"
		
		grp_config.set(bot,"SlowCommand",self.SlowCommand.get())
		grp_config.set(bot,"SlowParameters",self.SlowParameters.get())
		grp_config.set(bot,"FastCommand",self.FastCommand.get())
		grp_config.set(bot,"FastParameters",self.FastParameters.get())
		
		value={_("Slow profile"):"slow",_("Fast profile"):"fast",_("Both profiles"):"both",_("None"):"none"}
		
		grp_config.set(bot,"AnalysisBot",value[self.analysis_bot.get()])
		grp_config.set(bot,"LiveanalysisBot",value[self.liveanalysis_bot.get()])
		grp_config.set(bot,"LivePlayerBot",value[self.liveplayer_bot.get()])
		grp_config.set(bot,"ReviewBot",value[self.review_bot.get()])
		
		if self.parent.parent.refresh!=None:
			self.parent.parent.refresh()

class RayOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile="slow"):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Ray'
		self.my_starting_procedure=ray_starting_procedure


Ray={}
Ray['name']="Ray"
Ray['gtp_name']="Rayon"
Ray['analysis']=RayAnalysis
Ray['openmove']=RayOpenMove
Ray['settings']=RaySettings
Ray['gtp']=Ray_gtp
Ray['liveanalysis']=LiveAnalysis
Ray['runanalysis']=RunAnalysis
Ray['starting']=ray_starting_procedure

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
		bot=Ray
		
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
