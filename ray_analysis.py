# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
import sys
from Tkinter import *
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
					if one_deep_move in ["PASS","RESIGN"]:
						log("Leaving the variation when encountering",one_deep_move)
						break
					current_color=one_deep_move[0]
					one_deep_move=one_deep_move[1:].strip()
					if one_deep_move!="PASS":
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

def ray_starting_procedure(sgf_g,profile,silentfail=False):
	return bot_starting_procedure("Ray","RLO",Ray_gtp,sgf_g,profile,silentfail)


class RunAnalysis(RayAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

class LiveAnalysis(RayAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile):
		LiveAnalysisBase.__init__(self,g,filename,profile)

import subprocess
import Queue

class Ray_gtp(gtp):

	def __init__(self,command):
		self.c=1
		self.command_line=command[0]+" "+" ".join(command[1:])
		command=[c.encode(sys.getfilesystemencoding()) for c in command]
		self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		self.size=0
		
		self.stderr_starting_queue=Queue.Queue(maxsize=100)
		self.stderr_queue=Queue.Queue()
		self.stdout_queue=Queue.Queue()
		threading.Thread(target=self.consume_stderr).start()
		
		log("Checking Ray stderr to check for OpenCL SGEMM tuner running")
		delay=60
		while 1:
			try:
				err_line=self.stderr_starting_queue.get(True,delay)
				delay=10
				if "Started OpenCL SGEMM tuner." in err_line:
					log("OpenCL SGEMM tuner is running")
					show_info(_("Ray is currently running the OpenCL SGEMM tuner. It may take several minutes until Ray is ready."))
					break
				elif "Loaded existing SGEMM tuning.\n" in err_line:
					log("OpenCL SGEMM tuner has already been runned")
					break
				elif "BLAS Core:" in err_line:
					log("Could not find out, abandoning")
					break
				elif "Could not open weights file" in err_line:
					show_info(err_line.strip())
					break
				elif "Weights file is the wrong version." in err_line:
					show_info(err_line.strip())
					break

			except:
				log("Could not find out, abandoning")
				break
		
		
		self.free_handicap_stones=[]
		self.history=[]

	def consume_stderr(self):
		while 1:
			try:
				err_line=self.process.stderr.readline()
				if err_line:
					self.stderr_queue.put(err_line)
					try:
						self.stderr_starting_queue.put(err_line,block=False)
					except:
						#no need to keep all those log in memory, so there is a limit at 100 lines
						pass
				else:
					log("leaving consume_stderr thread")
					return
			except Exception, e:
				log("leaving consume_stderr thread due to exception:")
				log(e)
				return

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


class RaySettings(BotProfiles):
	def __init__(self,parent,bot="Ray"):
		BotProfiles.__init__(self,parent,bot)
		self.bot_gtp=Ray_gtp


class RayOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Ray'
		self.my_starting_procedure=ray_starting_procedure


Ray={}
Ray['name']="Ray"
Ray['gtp_name']="RLO"
Ray['analysis']=RayAnalysis
Ray['openmove']=RayOpenMove
Ray['settings']=RaySettings
Ray['gtp']=Ray_gtp
Ray['liveanalysis']=LiveAnalysis
Ray['runanalysis']=RunAnalysis
Ray['starting']=ray_starting_procedure

if __name__ == "__main__":
	main(Ray)
