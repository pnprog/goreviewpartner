# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
import sys
from sys import argv
from Tkinter import *
from time import sleep
from toolbox import *
from toolbox import _

class PachiAnalysis():

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)

		pachi=self.pachi
		log()
		log("==============")
		log("move",str(current_move))
		#additional_comments=""
		if player_color in ('w',"W"):
			log("pachi play white")
			answer=pachi.play_white()
		else:
			log("pachi play black")
			answer=pachi.play_black()
		
		best_answer=answer
		node_set(one_move,"CBM",answer) #Computer Best Move
		
		position_evaluation=pachi.get_all_pachi_moves()

		if "estimated score" in position_evaluation:
			node_set(one_move,"ES",position_evaluation["estimated score"])
		if (answer.lower() in ["pass","resign"]):
			bookmove=False
			pachi.undo()
			nb_undos=0
		else:
			nb_undos=1 #let's remember to undo that move from Pachi
			
			"""if 'book move' in position_evaluation:
				bookmove=True
			else:
				bookmove=False"""
		
		best_move=True
		log("Number of alternative sequences:",len(position_evaluation['variations']))
		for variation in position_evaluation['variations']:
			#exemple: variation={'winrate': 0.493, 'sequence': 'K17 P18 O18 O17', 'first move': 'K17'}
			previous_move=one_move.parent
			current_color=player_color	
			first_variation_move=True
			for one_deep_move in variation['sequence'].split(' '):
				if one_deep_move.lower() in ["pass","resign"]:
					log("Leaving the variation when encountering",one_deep_move.lower())
					break

				i,j=gtp2ij(one_deep_move)
				new_child=previous_move.new_child()
				node_set(new_child,current_color,(i,j))
				
				if first_variation_move==True:
					first_variation_move=False
					#variation_comment=""
		
					if 'win rate' in variation:
						if player_color=='b':
							black_value=variation['win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['win rate']
							black_value=opposite_rate(white_value)
						node_set(new_child,"BWWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"BWWR",black_value+'/'+white_value)
					
					
					if best_move:
						best_move=False
					
				previous_move=new_child
				if current_color in ('w','W'):
					current_color='b'
				else:
					current_color='w'
			
		log("==== no more sequences =====")
		
		for u in range(nb_undos):
			pachi.undo()
		"""
		log("Creating the influence map")
		influence=pachi.get_pachi_influence()
		black_influence_points=[]
		white_influence_points=[]
		for i in range(self.size):
			for j in range(self.size):
				if influence[i][j]==1:
					black_influence_points.append([i,j])
				elif influence[i][j]==2:
					white_influence_points.append([i,j])
					
		if black_influence_points!=[]:
			node_set(one_move,"IBM",black_influence_points)
		if white_influence_points!=[]:
			node_set(one_move,"IWM",white_influence_points)
		
		if self.size==19:
			log("==== creating heat map =====")
			raw_heat_map=leela.get_heatmap()
			heat_map=""
			for i in range(self.size):
				for j in range(self.size):
					if raw_heat_map[i][j]>=0.01:#ignore values lower than 1% to avoid generating heavy RSGF file
						heat_map+=ij2sgf([i, j])+str(round(raw_heat_map[i][j],2))+","
			
			if heat_map:
				node_set(one_move,"HTM",heat_map[:-1]) #HTM: heat map
		"""
		return best_answer #returning the best move, necessary for live analysis

	def initialize_bot(self):
		pachi=pachi_starting_procedure(self.g,self.profile)
		self.pachi=pachi
		return pachi

def pachi_starting_procedure(sgf_g,profile,silentfail=False):
	pachi=bot_starting_procedure("Pachi","Pachi UCT",Pachi_gtp,sgf_g,profile,silentfail)
	if not pachi:
		return False
	
	try:
		pachi.time_per_move=False
		time_per_move=profile["timepermove"]
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move:",time_per_move,"s")
				pachi.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				pachi.time_per_move=time_per_move
	except:
		log("Wrong value for Pachi thinking time:",time_per_move)
	return pachi

class RunAnalysis(PachiAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

class LiveAnalysis(PachiAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile):
		LiveAnalysisBase.__init__(self,g,filename,profile)

class Position(dict):
	def __init__(self):
		self['variations']=[]

class Variation(dict):
	pass

from json import loads as json_loads
import ntpath
import subprocess
import Queue

class Pachi_gtp(gtp):

	def __init__(self,command):
		self.c=1
		self.command_line=command[0]+" "+" ".join(command[1:])
		pachi_working_directory=command[0][:-len(ntpath.basename(command[0]))]
		command=[c.encode(sys.getfilesystemencoding()) for c in command]
		
		pachi_working_directory=pachi_working_directory.encode(sys.getfilesystemencoding())
		if pachi_working_directory:
			log("Pachi working directory:",pachi_working_directory)
			self.process=subprocess.Popen(command,cwd=pachi_working_directory, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
	
	def play_black(self):
		move=gtp.play_black(self)
		self.undo()#this undo performs a clear board / reset, necessary for Pachi in self play
		if move.lower()!="resign":
			self.place_black(move)
		return move
		
	def play_white(self):
		move=gtp.play_white(self)
		self.undo()#this undo performs a clear board / reset, necessary for Pachi in self play
		if move.lower()!="resign":
			self.place_white(move)
		return move
		
	def get_heatmap(self):
		while not self.stderr_queue.empty():
			self.stderr_queue.get()
		self.write("heatmap")
		one_line=self.readline() #empty line
		buff=[]
		while len(buff)<self.size:
			buff.append(self.stderr_queue.get())
		buff.reverse()
		number_coordinate=1
		letters="abcdefghjklmnopqrst"[:self.size]
		pn=[["NA" for i in range(self.size)] for j in range(self.size)] #pn: policy network
		pn_values=[]
		for i in range(self.size):
			one_line=buff[i].strip()
			if "winrate" in one_line:
				continue
			if "pass" in one_line:
				continue
			one_line=one_line.strip()
			one_line=[int(s) for s in one_line.split()]
			new_values=[[letter_coordinate+str(number_coordinate),int(value)/1000.] for letter_coordinate,value in zip(letters,one_line)]
			for nv in new_values:
				pn_values.append(nv)
			number_coordinate+=1

		for coordinates,value in pn_values:
			i,j=gtp2ij(coordinates)
			pn[i][j]=value
		return pn

	def quick_evaluation(self,color):
		if color==2:
			self.play_white()
		else:
			self.play_black()
		position_evaluation=self.get_all_pachi_moves()
		self.undo()
		
		txt=""
		try:
			if color==1:
				black_win_rate=position_evaluation["variations"][0]["win rate"]
				white_win_rate=opposite_rate(black_win_rate)
			else:
				white_win_rate=position_evaluation["variations"][0]["win rate"]
				black_win_rate=opposite_rate(white_win_rate)
			txt+= variation_data_formating["BWWR"]%(black_win_rate+'/'+white_win_rate)
		except:
			pass
		
		try:
			if txt:
				txt+="\n"
			final_score=position_evaluation["estimated score"]
			txt+=variation_data_formating["ES"]%final_score
		except:
			pass
		
		return txt
	


	"""def get_leela_influence(self):
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
		
		return influence"""

	def get_all_pachi_moves(self):
		buff=[]
		
		sleep(.01)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get().strip())
			sleep(.01)
		
		position_evaluation=Position()
		
		for err_line in buff:
			if "Score Est: " in err_line:
				position_evaluation["estimated score"]=err_line.split("Score Est: ")[1]
			if '{"move": ' in err_line:
				#this line is the json report line
				#exemple: {"move": {"playouts": 5064, "extrakomi": 0.0, "choice": "H8", "can": [[{"H8":0.792},{"F2":0.778},{"G6":0.831},{"G7":0.815}], [{"K14":0.603},{"L13":0.593},{"M13":0.627},{"K13":0.593}], [{"M15":0.603},{"L13":0.724},{"M13":0.778},{"K13":0.700}], [{"M14":0.627},{"M15":0.647},{"N15":0.596}]]}}
				"""print
				print err_line
				print"""
				json=json_loads(err_line)
				position_evaluation["playouts"]=json["move"]["playouts"]
				for move in json["move"]["can"]:
					if not move:
						continue
					variation=Variation()
					first_move=move[0].keys()[0]
					winrate=move[0].values()[0]
					variation["first move"]=first_move
					variation["win rate"]=str(100*float(winrate))+"%"
					sequence=""
					for follow_up in move:
						sequence+=follow_up.keys()[0]+" "
					variation["sequence"]=sequence.strip()
					position_evaluation['variations'].append(variation)

		return position_evaluation


class PachiSettings(BotProfiles):
	def __init__(self,parent,bot="Pachi"):
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

		self.bot_gtp=Pachi_gtp

	def clear_selection(self):
		self.index=-1
		self.profile.set("")
		self.command.set("")
		self.parameters.set("")
		self.timepermove.set("")
		
	def change_selection(self):
		try:
			index=self.listbox.curselection()[0]
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



class PachiOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Pachi'
		self.my_starting_procedure=pachi_starting_procedure

Pachi={}
Pachi['name']="Pachi"
Pachi['gtp_name']="Pachi UCT"
Pachi['analysis']=PachiAnalysis
Pachi['openmove']=PachiOpenMove
Pachi['settings']=PachiSettings
Pachi['gtp']=Pachi_gtp
Pachi['liveanalysis']=LiveAnalysis
Pachi['runanalysis']=RunAnalysis
Pachi['starting']=pachi_starting_procedure

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
		bot=Pachi
		
		bots=[]
		profiles=get_bot_profiles(bot["name"])
		for profile in profiles:
			bot2=dict(bot)
			for key, value in profile.items():
				bot2[key]=value
			bots.append(bot2)
		if len(bots)>0:
			popup=RangeSelector(top,filename,bots=bots)
			top.add_popup(popup)
			top.mainloop()
		else:
			log("Not profiles available for "+bot["name"]+" in config.ini")
	else:
		try:
			parameters=getopt.getopt(argv[1:], '', ['no-gui','range=', 'color=', 'komi=',"variation=", "profil="])
		except Exception, e:
			show_error(unicode(e)+"\n"+usage)
			sys.exit()
		
		if not parameters[1]:
			show_error("SGF file missing\n"+usage)
			sys.exit()
		
		app=None
		batch=[]
		
		for filename in parameters[1]:
			move_selection,intervals,variation,komi,nogui,profil=parse_command_line(filename,parameters[0])
			filename2=".".join(filename.split(".")[:-1])+".rsgf"
			if nogui:
				popup=RunAnalysis("no-gui",[filename,filename2],move_selection,intervals,variation-1,komi,profil)
				popup.terminate_bot()
			else:
				if not app:
					app = Application()
				one_analysis=[RunAnalysis,[filename,filename2],move_selection,intervals,variation-1,komi,profil]
				batch.append(one_analysis)
	
		if not nogui:
			app.after(100,lambda: batch_analysis(app,batch))
			app.mainloop()
