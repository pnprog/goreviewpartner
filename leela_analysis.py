# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
from Tkinter import *
from time import sleep
from toolbox import *
from toolbox import _

class LeelaAnalysis():

	def run_analysis(self,current_move):
		one_move=go_to_move(self.move_zero,current_move)
		player_color=guess_color_to_play(self.move_zero,current_move)

		leela=self.leela
		log()
		log("==============")
		log("move",str(current_move))
		#additional_comments=""
		if player_color in ('w',"W"):
			log("leela play white")
			answer=leela.play_white()
		else:
			log("leela play black")
			answer=leela.play_black()
		
		
		best_answer=answer
		node_set(one_move,"CBM",answer) #Computer Best Move
		
		#all_moves=leela.get_all_leela_moves()
		position_evaluation=leela.get_all_leela_moves()

		if "estimated score" in position_evaluation:
			node_set(one_move,"ES",position_evaluation["estimated score"])
		if (answer in ["PASS","RESIGN"]):
			bookmove=False
			leela.undo()
			nb_undos=0
		else:
			nb_undos=1 #let's remember to undo that move from Leela
			
			if 'book move' in position_evaluation:
				bookmove=True
			else:
				bookmove=False
			
			#let's make sure there is at least one variation available
			if len(position_evaluation['variations'])==0:
				position_evaluation['variations'].append({'sequence':answer})

				
			#let's make sure that there is more than one move for the first line of play
			#only one move could be a bookmove, or a very very forcing move
			first_sequence=position_evaluation['variations'][0]['sequence']
			new_sequence=first_sequence
			while len(new_sequence.split())<=1 and nb_undos<=5:
				log("first, let's ask leela for the next move")
				if player_color in ('w',"W") and nb_undos%2==0:
					answer=leela.play_white()
				elif player_color in ('w',"W") and nb_undos%2==1:
					answer=leela.play_black()
				elif player_color not in ('w',"W") and nb_undos%2==0:
					answer=leela.play_black()
				else:
					answer=leela.play_white()
				nb_undos+=1 #one have to remember to undo that move later
				
				new_position_evaluation=leela.get_all_leela_moves() #let's get stats for this new move
				
				#let's make sure there is at least one variation available
				if len(new_position_evaluation['variations'])==0:
					new_position_evaluation['variations'].append({'sequence':answer})
				
				if (answer not in ["PASS","RESIGN"]):
					#let's check the lenght of the new sequence
					new_sequence=new_position_evaluation["variations"][0]["sequence"]
					#adding this new sequence to the old sequence
					position_evaluation['variations'][0]['sequence']+=" "+new_sequence
					
					#we continue only if this is still a book move
					if "book move" not in new_position_evaluation:
						break

				else:
					#leela does not want to play further on this line of play
					#so let's stop there
					break

			
		best_move=True
		log("Number of alternative sequences:",len(position_evaluation['variations']))
		for variation in position_evaluation['variations']:
			#exemple: variation={'first move': 'M10', 'value network win rate': '21.11%', 'monte carlo win rate': '36.11%', 'sequence': 'M10 M9', 'playouts': '22', 'win rate': '27.46%', 'policy network value': '3.6%'}
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
					
					if 'monte carlo win rate' in variation:
						if player_color=='b':
							black_value=variation['monte carlo win rate']
							white_value=opposite_rate(black_value)
						else:
							white_value=variation['monte carlo win rate']
							black_value=opposite_rate(white_value)
						node_set(new_child,"MCWR",black_value+'/'+white_value)
						if best_move:
							node_set(one_move,"MCWR",black_value+'/'+white_value)
					
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
					
					if 'move evaluation' in variation:
						node_set(new_child,"EVAL",variation['move evaluation'])
						
					if 'rapid action value estimation' in variation:
						node_set(new_child,"RAVE",variation['rapid action value estimation'])
						
					if 'policy network value' in variation:
						node_set(new_child,"PNV",variation['policy network value'])
					
					if 'playouts' in variation:
						node_set(new_child,"PLYO",variation['playouts'])
						
					if bookmove:
						bookmove=False
						node_set(new_child,"BKMV","yes")
					
					if best_move:
						best_move=False
					
				previous_move=new_child
				if current_color in ('w','W'):
					current_color='b'
				else:
					current_color='w'
			
		log("==== no more sequences =====")
		
		for u in range(nb_undos):
			leela.undo()
		
		log("Creating the influence map")
		influence=leela.get_leela_influence()
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

		return best_answer #returning the best move, necessary for live analysis

	def initialize_bot(self):
		leela=leela_starting_procedure(self.g,self.profile)
		self.leela=leela
		self.time_per_move=0
		return leela

def leela_starting_procedure(sgf_g,profile,silentfail=False):


	leela=bot_starting_procedure("Leela","Leela",Leela_gtp,sgf_g,profile,silentfail)
	if not leela:
		return False

	try:
		time_per_move=profile["timepermove"]
		if time_per_move:
			time_per_move=int(time_per_move)
			if time_per_move>0:
				log("Setting time per move")
				leela.set_time(main_time=0,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				#self.time_per_move=time_per_move #why is that needed???
	except:
		log("Wrong value for Leela thinking time:",time_per_move)
	
	return leela

class RunAnalysis(LeelaAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

class LiveAnalysis(LeelaAnalysis,LiveAnalysisBase):
	def __init__(self,g,filename,profile):
		LiveAnalysisBase.__init__(self,g,filename,profile)

class Position(dict):
	def __init__(self):
		self['variations']=[]

class Variation(dict):
	pass

class Leela_gtp(gtp):

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
		letters="ABCDEFGHJKLMNOPQRST"[:self.size]
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

	def showboard(self):
		self.write("showboard")
		self.readline() #empty line
		buff=[]
		while self.stderr_queue.empty():
			sleep(.1)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.1)
		for line in buff:
			log(line.strip())
		
	def quick_evaluation(self,color):
		if color==2:
			self.play_white()
		else:
			self.play_black()
		position_evaluation=self.get_all_leela_moves()
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
			txt+="\n\n"+variation_data_formating["ES"]%self.get_leela_final_score()
		except:
			txt+=variation_data_formating["ES"]%self.get_leela_final_score()

		return txt
	
	def get_leela_final_score(self):
		self.write("final_score")
		answer=self.readline().strip()
		try:
			return answer.split(" ")[1]
		except:
			raise GRPException("GRPException in Get_leela_final_score()")

	def get_leela_influence(self):
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

	def get_all_leela_moves(self):
		buff=[]
		
		sleep(.01)
		while not self.stderr_queue.empty():
			while not self.stderr_queue.empty():
				buff.append(self.stderr_queue.get())
			sleep(.01)
		
		position_evaluation=Position()
		
		for err_line in buff:
			#log(err_line[:-1])
			
			if "score=" in err_line:
				position_evaluation["estimated score"]=err_line.split("score=")[1].strip()
			
			if "book moves" in err_line:
				log("book move")
				position_evaluation["book move"]=True
			
			if " ->" in err_line:
				variation=Variation()
				#log(err_line[:-1])
				one_answer=err_line.strip().split(" ")[0]
				variation["first move"]=one_answer
				one_score=err_line.split()[4][:-1]
				nodes=err_line.strip().split("(")[0].split("->")[1].replace(" ","")
				variation["playouts"]=nodes
				if self.size==19:
					monte_carlo=err_line.split("(U:")[1].split('%)')[0].strip()+"%"
					variation["monte carlo win rate"]=monte_carlo
					value_network=err_line.split("(V:")[1].split('%')[0].strip()+"%"
					variation["value network win rate"]=value_network
					policy_network=err_line.split("(N:")[1].split('%)')[0].strip()+"%"
					variation["policy network value"]=policy_network
					evaluation=None
					rave=None
				else:
					value_network=None
					policy_network=None
					evaluation=err_line.split("(N:")[1].split('%)')[0].strip()
					variation["move evaluation"]=evaluation
					rave=err_line.split("(R:")[1].split(')')[0].strip().replace(":","")
					rave1=rave.split()[0]
					rave2=rave.split()[1]
					variation["rapid action value estimation"]=rave1+' '+rave2
				
				if one_score!="0.00%":
					variation["win rate"]=one_score
					sequence=err_line.split("PV: ")[1].strip()
					variation["sequence"]=sequence.upper()
					position_evaluation['variations'].append(variation)
		return position_evaluation


class LeelaSettings(BotProfiles):
	def __init__(self,parent,bot="Leela"):
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

		self.bot_gtp=Leela_gtp

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



class LeelaOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='Leela'
		self.my_starting_procedure=leela_starting_procedure

Leela={}
Leela['name']="Leela"
Leela['gtp_name']="Leela"
Leela['analysis']=LeelaAnalysis
Leela['openmove']=LeelaOpenMove
Leela['settings']=LeelaSettings
Leela['gtp']=Leela_gtp
Leela['liveanalysis']=LiveAnalysis
Leela['runanalysis']=RunAnalysis
Leela['starting']=leela_starting_procedure

if __name__ == "__main__":
	main(Leela)
