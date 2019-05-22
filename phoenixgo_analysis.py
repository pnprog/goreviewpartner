# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
import sys
from Tkinter import *
from time import sleep
import threading
from toolbox import *
from toolbox import _

class PhoenixGoAnalysis():
	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)
		
		phoenixgo=self.phoenixgo
		log()
		log("==============")
		log("move",str(current_move))
		
		if player_color in ('w',"W"):
			log("Phoenix Go play white")
			answer=phoenixgo.play_white()
		else:
			log("Phoenix Go play black")
			answer=phoenixgo.play_black()
			
		best_answer=answer
		node_set(one_move,"CBM",answer) #Computer Best Move

		position_evaluation=phoenixgo.get_all_phoenixgo_moves()
		
		if (answer in ["PASS","RESIGN"]):
			phoenixgo.undo()
		else:
			#let's make sure there is at least one variation available
			if len(position_evaluation['variations'])==0:
				position_evaluation['variations'].append({'sequence':answer})
			
			nb_undos=1 #let's remember to undo that move from Phoenix Go

			#let's make sure that there is more than one move for the first line of play
			#only one move could be a bookmove, or a very very forcing move
			first_sequence=position_evaluation['variations'][0]['sequence']
			new_sequence=first_sequence
			while len(new_sequence.split())<=1 and nb_undos<=5:
				log("first, let's ask phoenix go for the next move")
				if player_color in ('w',"W") and nb_undos%2==0:
					answer=phoenixgo.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=phoenixgo.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=phoenixgo.play_black()
				else:
					answer=phoenixgo.play_white()
				log(new_sequence,"=>", answer)
				nb_undos+=1 #one have to remember to undo that move later
				
				new_position_evaluation=phoenixgo.get_all_phoenixgo_moves() #let's get stats for this new move
				
				#let's make sure there is at least one variation available
				if len(new_position_evaluation['variations'])==0:
					new_position_evaluation['variations'].append({'sequence':answer})
				
				if (answer not in ["PASS","RESIGN"]):
					#let's check the lenght of the new sequence
					new_sequence=new_position_evaluation["variations"][0]["sequence"]
					#adding this new sequence to the old sequence
					position_evaluation['variations'][0]['sequence']+=" "+new_sequence

				else:
					#phoenixgo does not want to play further on this line of play
					#so let's stop there
					break

			for u in range(nb_undos):
				#log("undo...")
				phoenixgo.undo()
			
		best_move=True
		log("Number of alternative sequences:",len(position_evaluation['variations']))
		for variation in position_evaluation['variations'][:self.maxvariations]:
			#exemple: {'value network win rate': '50.22%', 'policy network value': '17.37%', 'sequence': 'Q16 D4 D17 Q4', 'playouts': '13', 'first move': 'Q16'}
			previous_move=one_move.parent
			current_color=player_color	
			first_variation_move=True
			for one_deep_move in variation['sequence'].split(' '):
				if one_deep_move in ["PASS","RESIGN"]:
					log("Leaving the variation when encountering",one_deep_move)
					break

				i,j=gtp2ij(one_deep_move)
				new_child=previous_move.new_child()
				node_set(new_child,current_color,(i,j))
				
				if first_variation_move==True:
					first_variation_move=False
					#variation_comment=""
		
					if 'value network win rate' in variation:
						if player_color=='b':
							black_value=variation['value network win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['value network win rate']
							black_value=opposite_rate(white_value)	
						node_set(new_child,"VNWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"VNWR",black_value+'/'+white_value)

					if 'policy network value' in variation:
						node_set(new_child,"PNV",variation['policy network value'])

					if 'playouts' in variation:
						node_set(new_child,"PLYO",variation['playouts'])
					
					#new_child.add_comment_text(variation_comment)
					
					if best_move:
						best_move=False
					
				previous_move=new_child
				if current_color in ('w','W'):
					current_color='b'
				else:
					current_color='w'
		log("==== no more sequences =====")
		try:
			max_reading_depth=position_evaluation['max reading depth']
			node_set(one_move,"MRD",str(max_reading_depth))
			average_reading_depth=position_evaluation['average reading depth']
			node_set(one_move,"ARD",str(average_reading_depth))
		except:
			pass
		#one_move.add_comment_text(additional_comments)
		return best_answer
	
	def initialize_bot(self):
		phoenixgo=phoenixgo_starting_procedure(self.g,self.profile)
		self.phoenixgo=phoenixgo
		self.time_per_move=0
		return phoenixgo

def phoenixgo_starting_procedure(sgf_g,profile,silentfail=False):

	phoenixgo=bot_starting_procedure("PhoenixGo","PhoenixGo",PhoenixGo_gtp,sgf_g,profile,silentfail)
	if not phoenixgo:
		return False
	try:
		phoenixgo.time_per_move=False
		time_per_move=profile["timepermove"]
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				phoenixgo.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				phoenixgo.time_per_move=time_per_move
	except:
		log("Wrong value for PhoenixGo thinking time:",time_per_move)

	return phoenixgo



class RunAnalysis(PhoenixGoAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

class LiveAnalysis(PhoenixGoAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile):
		LiveAnalysisBase.__init__(self,g,filename,profile)


import ntpath
import subprocess
import Queue

class Position(dict):
	def __init__(self):
		self['variations']=[]

class Variation(dict):
	pass

class Tree(dict):
	def __init__(self):
		self.leaves=[]
		self.branches={}
		self.data=""
	

class PhoenixGo_gtp(gtp):
	
	def play_black(self):
		self.write("genmove black")
		
		sleep(.5)
		while not self.stderr_queue.empty():#emptying
			while not self.stderr_queue.empty():
				self.stderr_queue.get()
			sleep(.5)
			
		answer=self.readline().strip()
		try:
			move=answer.split(" ")[1]
			self.history.append(["b",move])
			return move
		except Exception, e:
			raise GRPException("GRPException in genmove_black()\nanswer='"+answer+"'\n"+unicode(e))

		
	def play_white(self):
		self.write("genmove white")
		
		sleep(.5)
		while not self.stderr_queue.empty():#emptying
			while not self.stderr_queue.empty():
				self.stderr_queue.get()
			sleep(.5)
		
		answer=self.readline().strip()
		try:
			move=answer.split(" ")[1]
			self.history.append(["w",move])
			return move
		except Exception, e:
			raise GRPException("GRPException in genmove_white()\nanswer='"+answer+"'\n"+unicode(e))
	
	def quick_evaluation(self,color):
		if color==2:
			self.play_white()
		else:
			self.play_black()
		position_evaluation=self.get_all_phoenixgo_moves()
		self.undo()
		
		if color==1:
			black_win_rate=position_evaluation["variations"][0]["value network win rate"]
			white_win_rate=opposite_rate(black_win_rate)
		else:
			white_win_rate=position_evaluation["variations"][0]["value network win rate"]
			black_win_rate=opposite_rate(white_win_rate)
		txt=variation_data_formating["VNWR"]%(black_win_rate+'/'+white_win_rate)
		#txt+="\n\n"+variation_data_formating["ES"]%self.get_phoenixgo_final_score()
		return txt
		
	def __init__(self,command):
		self.c=1
		self.command_line=command[0]+" "+" ".join(command[1:])
		
		phoenixgo_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		command=[c.encode(sys.getfilesystemencoding()) for c in command]

		phoenixgo_working_directory=phoenixgo_working_directory.encode(sys.getfilesystemencoding())
		if phoenixgo_working_directory:
			log("Phoenix Go working directory:",phoenixgo_working_directory)
			self.process=subprocess.Popen(command,cwd=phoenixgo_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		else:
			self.process=subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		self.size=0
		
		self.stderr_queue=Queue.Queue()
		self.stdout_queue=Queue.Queue()
		
		threading.Thread(target=self.consume_stderr).start()
		self.free_handicap_stones=[]
		self.history=[]

	def undo(self):
		result=gtp.undo(self)
		if self.time_per_move:
			self.set_time(main_time=0,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		return result

	def consume_stderr(self):
		
		count=100
		while count:
			count-=1
			try:
				err_line=self.process.stderr.readline()
				if err_line:
					self.stderr_queue.put(err_line)
					if "enable_background_search: true" in err_line:
						log("=====================================================")
						log("=== WARNING: Pondering is currently enabled       ===")
						log("=== GRP works better with pondering disabled      ===")
						log("=== Please turn \"enable_background_search\" at 0   ===")
						log("=====================================================")
						log("\a")
				else:
					log("leaving consume_stderr thread")
					return
			except Exception, e:
				log("leaving consume_stderr thread due to exception:")
				log(e)
				return
		while 1:
			try:
				err_line=self.process.stderr.readline()
				if err_line:
					self.stderr_queue.put(err_line)
				else:
					log("leaving consume_stderr thread")
					return
			except Exception, e:
				log("leaving consume_stderr thread due to exception:")
				log(e)
				return

	def get_phoenixgo_final_score(self):
		self.write("final_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GRPException("GRPException in get_phoenixgo_final_score()")
	
	def coords2ij(self,m):
		# cj => 8,2
		a, b=m
		letters="abcdefghijklmnopqrstuvwxyz"
		i=letters.index(b)
		j=letters.index(a)
		return ij2gtp((i, j))

	def get_all_phoenixgo_moves(self):
		buff=[]
		
		sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		position_evaluation=Position()
		found=False
		tree=Tree()
		info_available=False
		for err_line in buff:
			if not found:
				if "========== debug info for" in err_line:
					found=True
					info_available=True
					log(err_line.strip())
			else:
				log("->",err_line.strip())
				if "main move path" in err_line:
					err_line=err_line.split("path: ")[1]
					all_moves=err_line.split("),")
					sequence=""
					first_move=True
					for move in all_moves:
						sequence_move=move.split("(")[0]
						if first_move:
							first_move=False
							best_first_move=sequence_move
							q=float(move.split("(")[1].split(",")[1])
							best_winrate=(q+1)*50
							best_winrate="%.2f%%"%best_winrate
							best_playouts=move.split("(")[1].split(",")[0]
							best_policy="%.2f%%"%(100*float(move.split("(")[1].split(",")[2]))
						try:
							sequence_move=self.coords2ij(sequence_move)
							sequence+=sequence_move+" "
						except:
							break
					best_sequence=sequence.strip()
				elif "model global step" in err_line:
					#we ignore this line
					pass
				elif "========== debug info for" in err_line:
					#end of the interesting data, time to build the variations
					found=False
					if best_first_move not in tree.leaves:
						log("Best move (",best_first_move,") not in tree, so manually adding it")
						variation=Variation()
						variation["sequence"]=best_sequence
						variation["value network win rate"]=best_winrate
						variation["playouts"]=best_playouts
						variation["policy network value"]=best_policy
						position_evaluation['variations'].append(variation)
						
					for move in tree.leaves:
						variation=Variation()
						log("\t",move)
						if move!=best_first_move:
							top_branch=tree.branches[move]
							print "111"
							print top_branch.data
							print "222"
							winrate=top_branch.data.split(", Q=")[1].split(", ")[0]
							winrate="%.2f%%"%((float(winrate)+1)*50.)
							variation["value network win rate"]=winrate
							policy=top_branch.data.split(", p=")[1].split(", ")[0]
							policy="%.2f%%"%(100*float(policy))
							variation["policy network value"]=policy
							playouts=top_branch.data.split(": N=")[1].split(", ")[0]
							variation["playouts"]=playouts
							sequence=self.coords2ij(move)
							log("\tdata",top_branch.data.strip())
							while top_branch.leaves:
								sequence_move=top_branch.leaves[0]
								sequence+=" "+self.coords2ij(sequence_move)
								top_branch=top_branch.branches[sequence_move]
							variation["sequence"]=sequence
							position_evaluation['variations'].append(variation)
							log("\twinrate",winrate)
							log("\tsequence",sequence)
							log("\tpolicy",policy)
							log("\tplayouts",playouts)
						else:
							variation["sequence"]=best_sequence
							variation["value network win rate"]=best_winrate
							variation["playouts"]=best_playouts
							variation["policy network value"]=best_policy
							position_evaluation['variations']=[variation]+position_evaluation['variations']
							log("\twinrate*",best_winrate)
							log("\tsequence*",best_sequence)
							log("\tpolicy*",variation["policy network value"])
							log("\tplayouts*",best_playouts)
						log()
					continue
				elif  "move path" not in err_line:
					#this line contains information on the tree
					path=err_line.split("] ")[1].split(":")[0]
					path=path.split(",")
					leaf=tree
					level=0
					for step in path:
						if level==0:
							if step not in leaf.branches:
								leaf.leaves.append(step) #this allow to remember what candidate move came first
								leaf.branches[step]=Tree() #for storing following leaves down the branch
								leaf.branches[step].data=err_line #data associated with that leaf
							leaf=leaf.branches[step]
						else:
							if not leaf.branches:
								leaf.leaves.append(step) #this allow to remember what candidate move came first
								leaf.branches[step]=Tree() #for storing following leaves down the branch
								leaf=leaf.branches[step]
							else:
								break
			
			
			try:
				if ", winrate=" in err_line:
					winrate=float(err_line.split(", winrate=")[1].split("%, ")[0])
					winrate="%.2f%%"%winrate
					if not "nan" in winrate:
						position_evaluation['variations'][0]["value network win rate"]=winrate
						log("winrate for first variation =>",winrate)
				
				if ", avg_height=" in err_line:
					max_reading_depth=int(err_line.split(", height=")[1].split(", ")[0])
					average_reading_depth=float(err_line.split(", avg_height=")[1].split(", ")[0])
					position_evaluation['max reading depth']=max_reading_depth
					position_evaluation['average reading depth']=average_reading_depth
			except:
				log(err_line.strip())
			
		if not info_available:
			log("=========================================================")
			log("=== WARNING: no information found in PhoenixGo output ===")
			log("=== Please make sure verbose level is 1    (--v=1)    ===")
			log("=========================================================")
			log("\a")

		return position_evaluation

class PhoenixGoSettings(BotProfiles):
	def __init__(self,parent,bot="PhoenixGo"):
		Frame.__init__(self,parent)
		self.parent=parent
		self.bot=bot
		self.profiles=get_bot_profiles(bot,False)
		profiles_frame=self
		
		self.listbox = Listbox(profiles_frame)
		self.listbox.grid(column=10,row=10,rowspan=10)
		self.update_listbox()
		
		row=10
		Label(profiles_frame,text=_("Profile")).grid(row=row,column=11,sticky=W)
		self.profile = StringVar()
		Entry(profiles_frame, textvariable=self.profile, width=30).grid(row=row,column=12)

		row+=1
		Label(profiles_frame,text=_("Command")).grid(row=row,column=11,sticky=W)
		self.command = StringVar() 
		Entry(profiles_frame, textvariable=self.command, width=30).grid(row=row,column=12)
		
		row+=1
		Label(profiles_frame,text=_("Parameters")).grid(row=row,column=11,sticky=W)
		self.parameters = StringVar()
		Entry(profiles_frame, textvariable=self.parameters, width=30).grid(row=row,column=12)
		
		row+=1
		Label(profiles_frame,text=_("Time per move (s)")).grid(row=row,column=11,sticky=W)
		self.timepermove = StringVar()
		Entry(profiles_frame, textvariable=self.timepermove, width=30).grid(row=row,column=12)
		

		row+=10
		buttons_frame=Frame(profiles_frame)
		buttons_frame.grid(row=row,column=10,sticky=W,columnspan=3)
		Button(buttons_frame, text=_("Add profile"),command=self.add_profile).grid(row=row,column=1,sticky=W)
		Button(buttons_frame, text=_("Modify profile"),command=self.modify_profile).grid(row=row,column=2,sticky=W)
		Button(buttons_frame, text=_("Delete profile"),command=self.delete_profile).grid(row=row,column=3,sticky=W)
		Button(buttons_frame, text=_("Test"),command=lambda: self.parent.parent.test(self.bot_gtp,self.command,self.parameters)).grid(row=row,column=4,sticky=W)
		
		self.listbox.bind("<Button-1>", lambda e: self.after(100,self.change_selection))

		self.index=-1

		self.bot_gtp=PhoenixGo_gtp

	def clear_selection(self):
		self.index=-1
		self.profile.set("")
		self.command.set("")
		self.parameters.set("")
		self.timepermove.set("")
		
	def change_selection(self):
		try:
			index=int(self.listbox.curselection()[0])
			self.index=index
		except:
			log("No selection")
			self.clear_selection()
			return
		data=self.profiles[index]
		self.profile.set(data["profile"])
		self.command.set(data["command"])
		self.parameters.set(data["parameters"])
		self.timepermove.set(data["timepermove"])

		
	def add_profile(self):
		profiles=self.profiles
		if self.profile.get()=="":
			return
		data={"bot":self.bot}
		data["profile"]=self.profile.get()
		data["command"]=self.command.get()
		data["parameters"]=self.parameters.get()
		data["timepermove"]=self.timepermove.get()
		
		self.empty_profiles()
		profiles.append(data)
		self.create_profiles()
		self.clear_selection()
		
	def modify_profile(self):
		profiles=self.profiles
		if self.profile.get()=="":
			return
		
		if self.index<0:
			log("No selection")
			return
		index=self.index
		
		profiles[index]["profile"]=self.profile.get()
		profiles[index]["command"]=self.command.get()
		profiles[index]["parameters"]=self.parameters.get()
		profiles[index]["timepermove"]=self.timepermove.get()
		
		self.empty_profiles()
		self.create_profiles()
		self.clear_selection()



class PhoenixGoOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='PhoenixGo'
		self.my_starting_procedure=phoenixgo_starting_procedure

PhoenixGo={}
PhoenixGo['name']="PhoenixGo"
PhoenixGo['gtp_name']="PhoenixGo"
PhoenixGo['analysis']=PhoenixGoAnalysis
PhoenixGo['openmove']=PhoenixGoOpenMove
PhoenixGo['settings']=PhoenixGoSettings
PhoenixGo['gtp']=PhoenixGo_gtp
PhoenixGo['liveanalysis']=LiveAnalysis
PhoenixGo['runanalysis']=RunAnalysis
PhoenixGo['starting']=phoenixgo_starting_procedure

if __name__ == "__main__":
	main(PhoenixGo)
