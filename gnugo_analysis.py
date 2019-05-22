# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
from Tkinter import *
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
			if answer=='RESIGN':
				break
			if answer=='PASS':
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
		if (answer not in ["PASS","RESIGN"]):
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
						raise GRPException(_("GnuGo thread failed:")+"\n"+str(one_thread.sequence))
					
					one_sequence=one_thread.one_top_move+" "+one_thread.sequence[0]
					es=one_thread.sequence[1]
					one_sequence=one_sequence.strip()
					log(">>>>>>",one_sequence)
					previous_move=one_move.parent
					current_color=player_color
					first_move=True
					for one_deep_move in one_sequence.split(' '):
						if one_deep_move not in ['RESIGN','PASS']:
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
		black_territories_points=[]
		black_influence_points=[]
		white_influence=gnugo.get_gnugo_initial_influence_white()
		white_territories_points=[]
		white_influence_points=[]
		for i in range(self.size):
			for j in range(self.size):
				if black_influence[i][j]==-3:
					black_territories_points.append([i,j])
				if white_influence[i][j]==3:
					white_territories_points.append([i,j])
				
				if black_influence[i][j]==-2:
					black_influence_points.append([i,j])
				if white_influence[i][j]==2:
					white_influence_points.append([i,j])

		if black_influence_points!=[]:
			node_set(one_move,"IBM",black_influence_points) #IBM: influence black map
			
		if black_territories_points!=[]:
			node_set(one_move,"TBM",black_territories_points) #TBM: territories black map
			
		if white_influence_points!=[]:
			node_set(one_move,"IWM",white_influence_points) #IWM: influence white map
			
		if white_territories_points!=[]:
			node_set(one_move,"TWM",white_territories_points) #TWM: territories white map
		
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
			self.nb_variations=int(self.profile["variations"])
		except:
			pass
			#grp_config.set("GnuGo", "variations",self.nb_variations)"""
		
		self.deepness=4
		try:
			self.deepness=int(self.profile["deepness"])
		except:
			pass
			#grp_config.set("GnuGo", "deepness",self.deepness)"""
		
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

def gnugo_starting_procedure(sgf_g,profile,silentfail=False):
	return bot_starting_procedure("GnuGo","GNU Go",GnuGo_gtp,sgf_g,profile,silentfail)


class RunAnalysis(GnuGoAnalysis,RunAnalysisBase):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow",existing_variations="remove_everything"):
		RunAnalysisBase.__init__(self,parent,filename,move_range,intervals,variation,komi,profile,existing_variations)

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
			raise GRPException("GRPException in get_gnugo_estimate_score()")
	
	def gnugo_top_moves_black(self):
		self.write("top_moves_black")
		answer=self.readline()[:-1]
		try:
			answer=answer.split(" ")[1:-1]
		except:
			raise GRPException("GRPException in get_gnugo_top_moves_black()")
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
			raise GRPException("GRPException in get_gnugo_top_moves_white()")
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


class GnuGoSettings(BotProfiles):
	def __init__(self,parent,bot="GnuGo"):
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
		Label(profiles_frame,text=_("Maximum number of variations")).grid(row=row,column=11,sticky=W)
		self.variations = StringVar()
		Entry(profiles_frame, textvariable=self.variations, width=30).grid(row=row,column=12)
		
		row+=1
		Label(profiles_frame,text=_("Deepness for each variation")).grid(row=row,column=11,sticky=W)
		self.deepness = StringVar()
		Entry(profiles_frame, textvariable=self.deepness, width=30).grid(row=row,column=12)
		

		row+=10
		buttons_frame=Frame(profiles_frame)
		buttons_frame.grid(row=row,column=10,sticky=W,columnspan=3)
		Button(buttons_frame, text=_("Add profile"),command=self.add_profile).grid(row=row,column=1,sticky=W)
		Button(buttons_frame, text=_("Modify profile"),command=self.modify_profile).grid(row=row,column=2,sticky=W)
		Button(buttons_frame, text=_("Delete profile"),command=self.delete_profile).grid(row=row,column=3,sticky=W)
		Button(buttons_frame, text=_("Test"),command=lambda: self.parent.parent.test(self.bot_gtp,self.command,self.parameters)).grid(row=row,column=4,sticky=W)
		self.listbox.bind("<Button-1>", lambda e: self.after(100,self.change_selection))
		
		self.index=-1
		
		self.bot_gtp=GnuGo_gtp

		
	def clear_selection(self):
		self.index=-1
		self.profile.set("")
		self.command.set("")
		self.parameters.set("")
		self.variations.set("")
		self.deepness.set("")

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
		self.variations.set(data["variations"])
		self.deepness.set(data["deepness"])
		
	def add_profile(self):
		profiles=self.profiles
		if self.profile.get()=="":
			return
		data={"bot":self.bot}
		data["profile"]=self.profile.get()
		data["command"]=self.command.get()
		data["parameters"]=self.parameters.get()
		data["variations"]=self.variations.get()
		data["deepness"]=self.deepness.get()
		
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
		profiles[index]["variations"]=self.variations.get()
		profiles[index]["deepness"]=self.deepness.get()
		
		self.empty_profiles()
		self.create_profiles()
		self.clear_selection()
		

class GnuGoOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
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

if __name__ == "__main__":
	main(GnuGo)
