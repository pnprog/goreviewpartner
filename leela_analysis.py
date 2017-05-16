# -*- coding: utf-8 -*-


from gtp import gtp
import sys
from gomill import sgf, sgf_moves

from sys import exit,argv

from Tkinter import Tk, Label, Frame, StringVar, Radiobutton, W,E, Entry, END,Button,Toplevel
import tkFileDialog
import sys
import os

import ConfigParser


import time, os
import threading
import ttk

def alert(text_to_display):
	popup=Toplevel()
	label= Label(popup,text=text_to_display)
	label.pack()
	ok_button = Button(popup, text="OK", command=popup.destroy)
	ok_button.pack()

def get_moves_number(move_zero):
	k=0
	move=move_zero
	while move:
		move=move[0]
		k+=1
	return k

def go_to_move(move_zero,move_number=0):
	
	if move_number==0:
		return move_zero
	move=move_zero
	k=0
	while k!=move_number:
		if not move:
			print "return False"
			return False
		move=move[0]
		k+=1
	return move


def gtp2ij(move):
	#print "gtp2ij(",move,")"
	
	# a18 => (17,0)
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return int(move[1:])-1,letters.index(move[0].lower())

		


def ij2gtp(m):
	# (17,0) => a18
	
	if m==None:
		return "pass"
	i,j=m
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return letters[j]+str(i+1)
















class RunAnalysis(Frame):
	def __init__(self,parent,filename,move_range=None):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.move_range=move_range
		self.lock1=threading.Lock()
		self.lock2=threading.Lock()
		self.initialize()
	
	def run_analysis(self,current_move):
		
		
		one_move=go_to_move(self.move_zero,current_move)
		player_color,player_move=one_move.get_move()
		gnugo=self.gnugo
		leela=self.leela
		
		if current_move in self.move_range:
			
			max_move=self.max_move
			
			
			print "move",str(current_move)+'/'+str(max_move),
			
			#final_score=leela.get_leela_final_score()
			final_score=gnugo.get_gnugo_estimate_score()
			
			print final_score,
			
			#one_move.add_comment_text("\nGnugo score estimation: "+final_score)
			
			additional_comments="Move "+str(current_move)
			if player_color in ('w',"W"):
				additional_comments+="\nWhite to play, in the game, white played "+ij2gtp(player_move)
			else:
				additional_comments+="\nBlack to play, in the game, black played "+ij2gtp(player_move)
			additional_comments+="\nGnugo score estimation before the move was played: "+final_score
			
			"""
			if player_color in ('w',"W"):
				print "leela play white"
				answer=leela.play_white()
			else:
				print "leela play black"
				answer=leela.play_black()
			"""
			try:
				if player_color in ('w',"W"):
					print "leela play white"
					answer=leela.play_white()
				else:
					print "leela play black"
					answer=leela.play_black()
			except Exception, e:
				exc_type, exc_obj, exc_tb = sys.exc_info()
				fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
				print exc_type, fname, exc_tb.tb_lineno
				print e
				print "leaving thread..."
				exit()
			
			all_moves=leela.get_all_leela_moves()
			if (answer.lower() not in ["pass","resign"]):
				
				if all_moves==[]:
					bookmove=True
					all_moves=[[answer,answer,666,666,666]]
				else:
					bookmove=False
				all_moves2=all_moves[:]
				nb_undos=1
				print "====move",current_move+1,all_moves[0],'~',answer
				
				
				#making sure the first line of play is more than one move deep
				best_winrate=all_moves[0][2]
				while (len(all_moves2[0][1].split(' '))==1) and (answer.lower() not in ["pass","resign"]):	
					print "going deeper for first line of play (",nb_undos,")"
					try:
						if player_color in ('w',"W") and nb_undos%2==0:
							#print "\tleela play white"
							answer=leela.play_white()
						elif player_color in ('w',"W") and nb_undos%2==1:
							#print "\tleela play black"
							answer=leela.play_black()
						elif player_color not in ('w',"W") and nb_undos%2==0:
							#print "\tleela play black"
							answer=leela.play_black()
						else:
							#print "\tleela play white"
							answer=leela.play_white()
						nb_undos+=1
						#if answer.lower()!="resign":
						#	nb_undos+=1
					except Exception, e:
						exc_type, exc_obj, exc_tb = sys.exc_info()
						fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
						print exc_type, fname, exc_tb.tb_lineno
						print e
						print "leaving thread..."
						exit()


					print all_moves[0],'+',answer,
					all_moves2=leela.get_all_leela_moves()
					if (answer.lower() not in ["pass","resign"]):
						
						print "all_moves2:",all_moves2
						if all_moves2==[]:
							all_moves2=[[answer,answer,666,666,666]]

						print '+',all_moves2
						all_moves[0][1]+=" "+all_moves2[0][1]
						
						
						if (player_color.lower()=='b' and nb_undos%2==1) or (player_color.lower()=='w' and nb_undos%2==1):
							all_moves[0][2]=all_moves2[0][2]
						else:
							all_moves[0][2]=100-all_moves2[0][2]

					else:
						print
						print "last play on the fist of play was",answer,"so leaving"
				
				for u in range(nb_undos):
					print "undo..."
					leela.undo()
				
				
				#all_moves[0][2]=best_winrate #it would be best to sort again all variation based on new winrate...
				
				#print "all moves from leela:",all_moves
				best_move=True
				#variation=-1
				print "Number of alternative sequences:",len(all_moves)
				print all_moves
				for sequence_first_move,one_sequence,one_score,one_nodes,one_nn in all_moves:
					print "Adding sequence starting from",sequence_first_move
					previous_move=one_move.parent
					current_color=player_color
					
					if best_move:
						if player_color=='b':
							print str(one_score)+'%/'+str(100-one_score)+'%',
						else:
							print str(100-one_score)+'%/'+str(one_score)+'%',
					
					#variation+=1
					#deepness=-1
					for one_deep_move in one_sequence.split(' '):
						#deepness+=1
						#print "variation:",variation,"deepness:",deepness,"gtp2ij(",one_deep_move,")"
						if one_deep_move.lower() in ["pass","resign"]:
							print "Leaving the variation when encountering",one_deep_move.lower()
							break
						i,j=gtp2ij(one_deep_move)
						new_child=previous_move.new_child()
						new_child.set_move(current_color,(i,j))
						#new_child.add_comment_text("black/white win probability: "+str(one_score)+'%/'+str(100-one_score)+'%')
						
						
						if player_color=='b':
							if not bookmove:
								new_child.add_comment_text("black/white win probability for this variation: "+str(one_score)+'%/'+str(100-one_score)+'%\nNumber of playouts used to estimate this variation: '+str(one_nodes)+'\nNeural network value for this move: '+str(one_nn)+'%')
							if best_move:
								best_move=False
								if not bookmove:
									additional_comments+="\nLeela black/white win probability for this position: "+str(one_score)+'%/'+str(100-one_score)+'%'
						else:
							if not bookmove:
								new_child.add_comment_text("black/white win probability for this variation: "+str(100-one_score)+'%/'+str(one_score)+'%\nNumber of playouts used to estimate this variation: '+str(one_nodes)+'\nNeural network value for this move: '+str(one_nn)+'%')
							if best_move:
								best_move=False
								if not bookmove:
									additional_comments+="\nLeela black/white win probability for this position: "+str(100-one_score)+'%/'+str(one_score)+'%'
						
						previous_move=new_child
						if current_color in ('w','W'):
							current_color='b'
						else:
							current_color='w'
				print "==== no more sequences ====="
			else:
				print 'adding "'+answer.lower()+'" to the sgf file'
				additional_comments+="\nFor this position, Leela would "+answer.lower()
				if answer.lower()=="pass":
					leela.undo()
			
			
			one_move.add_comment_text(additional_comments)

			new_file=open(self.filename[:-4]+".rsgf",'w')
			new_file.write(self.g.serialise())
			new_file.close()
			
			self.total_done+=1
		else:
			print "Move",current_move,"not in the list of moves to be analysed, skipping"

		print "now asking Leela to play the game move:",
		if player_color in ('w',"W"):
			print "white at",ij2gtp(player_move)
			leela.place_white(ij2gtp(player_move))
			gnugo.place_white(ij2gtp(player_move))
		else:
			print "black at",ij2gtp(player_move)
			leela.place_black(ij2gtp(player_move))
			gnugo.place_black(ij2gtp(player_move))
		
		print "Analysis for this move is completed"
	
	
	def run_all_analysis(self):
		self.current_move=1
		try:
			while self.current_move<=self.max_move:
				self.lock1.acquire()
				self.run_analysis(self.current_move)
				self.current_move+=1
				self.lock1.release()
				self.lock2.acquire()
				self.lock2.release()
		except Exception,e:
			exc_type, exc_obj, exc_tb = sys.exc_info()
			fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
			print exc_type, fname, exc_tb.tb_lineno
			print e
			print "releasing lock"
			try:
				self.lock1.release()
			except:
				pass
			try:
				self.lock2.release()
			except:
				pass
			print "leaving thread"
			exit()

		

	def follow_analysis(self):
		if self.lock1.acquire(False):
			remaining_s=(len(self.move_range)-self.total_done)*self.time_per_move
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
			self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
			self.lab1.config(text="Currently at move "+str(self.current_move)+'/'+str(self.max_move))
			self.pb.step()
			self.update_idletasks()
			self.lock2.release()
			time.sleep(.001)
			self.lock1.release()
			self.lock2.acquire()
		if self.current_move<=self.max_move:
			self.root.after(1,self.follow_analysis)
		else:
			self.lab1.config(text="Completed")
			self.pb["maximum"] = 100
			self.pb["value"] = 100
	
	def close_app(self):
		print "RunAnalysis beeing closed"
		self.lab2.config(text="Now closing, please wait...")
		self.update_idletasks()
		print "killing gnugo"
		self.gnugo.close()
		print "killing leela"
		self.leela.close()
		print "destroying"
		self.destroy()
		self.parent.destroy()
		print "RunAnalysis closed"

		
	def initialize(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		
		txt = open(self.filename)
		self.g = sgf.Sgf_game.from_string(clean_sgf(txt.read()))
		txt.close()
		size=self.g.get_size()
		
		leela_command_line=tuple(Config.get("Leela", "Command").split())
		leela=gtp(leela_command_line)
		leela.boardsize(size)
		leela.reset()
		self.leela=leela
		
		gnugo_command_line=tuple(Config.get("GnuGo", "Command").split())
		gnugo=gtp(gnugo_command_line)
		gnugo.boardsize(size)
		gnugo.reset()
		self.gnugo=gnugo
		
		self.time_per_move=int(Config.get("Analysis", "TimePerMove"))
		leela.set_time(main_time=self.time_per_move,byo_yomi_time=self.time_per_move,byo_yomi_stones=1)
		self.move_zero=self.g.get_root()
		komi=self.g.get_komi()
		leela.komi(komi)
		gnugo.komi(komi)
		
		
		
		board, plays = sgf_moves.get_setup_and_moves(self.g)
		handicap_stones=""
		
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					print "Adding initial white stone at",move
					leela.place_white(move)
					gnugo.place_white(move)
				else:
					print "Adding initial black stone at",move
					leela.place_black(move)
					gnugo.place_black(move)
						
			
		self.max_move=get_moves_number(self.move_zero)
		if not self.move_range:
			self.move_range=range(1,self.max_move+1)
		#if 1 in self.move_range:
		#	self.move_range.remove(1)
			
		self.total_done=0
		
		root = self
		root.parent.title('GoReviewPartner')
		root.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		
		Label(root,text="Analysis of: "+os.path.basename(self.filename)).pack()
		

		remaining_s=len(self.move_range)*self.time_per_move
		remaining_h=remaining_s/3600
		remaining_s=remaining_s-3600*remaining_h
		remaining_m=remaining_s/60
		remaining_s=remaining_s-60*remaining_m
		
		self.lab1=Label(root)
		self.lab1.pack()
		
		self.lab2=Label(root)
		self.lab2.pack()
		
		self.lab1.config(text="Currently at move 2/"+str(self.max_move))
		self.lab2.config(text="Remaining time: "+str(remaining_h)+"h, "+str(remaining_m)+"mn, "+str(remaining_s)+"s")
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()

		current_move=1

		new_file=open(self.filename[:-4]+".rsgf",'w')
		new_file.write(self.g.serialise())
		new_file.close()

		self.lock2.acquire()
		threading.Thread(target=self.run_all_analysis).start()
		
		self.root=root
		root.after(500,self.follow_analysis)
		

import urllib2
class DownloadFromURL(Frame):
	def __init__(self,parent):
		Frame.__init__(self,parent)
		self.parent=parent
		self.parent.title('GoReviewPartner')
		
		Label(self,text='   ').grid(column=0,row=0)
		Label(self,text='   ').grid(column=2,row=4)
		
		Label(self,text="Paste the URL to the sgf file (http or https):").grid(row=1,column=1,sticky=W)
		self.url_entry=Entry(self)
		self.url_entry.grid(row=2,column=1,sticky=W)
		
		Button(self,text="Get",command=self.get).grid(row=3,column=1,sticky=E)
		self.popup=None
		
	def get(self):
		user_agent = 'GoReviewPartner (https://github.com/pnprog/goreviewpartner/)'
		headers = { 'User-Agent' : user_agent }
		
		
		url=self.url_entry.get()
		if not url:
			return
		
		if url[:4]!="http":
			url="http://"+url
		
		print "Downloading",url
		
		r=urllib2.Request(url,headers=headers)
		try:
			h=urllib2.urlopen(r)
		except:
			alert("Could not download the URL")
			return
		filename=""
		
		sgf=h.read()
		
		if sgf[:7]!="(;FF[4]":
			print "not a sgf file"
			alert("Not a sgf file!")
			print sgf[:7]
			return
		
		try:
			filename=h.info()['Content-Disposition']
			if 'filename="' in filename:
				filename=filename.split('filename="')[0][:-1]
			if "''" in filename:
				filename=filename.split("''")[1]
		except:
			print "no Content-Disposition in header"
			black='black'
			white='white'
			date=""
			if 'PB[' in sgf:
				black=sgf.split('PB[')[1].split(']')[0]
			if 'PW[' in sgf:
				white=sgf.split('PW[')[1].split(']')[0]
			if 'DT[' in sgf:
				date=sgf.split('DT[')[1].split(']')[0]

			filename=""
			if date:
				filename=date+'_'
			filename+=black+'_VS_'+white+'.sgf'
		
		print filename
		text_file = open(filename, "w")
		text_file.write(sgf)
		text_file.close()
			
		#self.parent.destroy()
		self.destroy()
		#newtop=Tk()
		self.popup=RangeSelector(self.parent,filename)
		self.popup.pack()
		#newtop.mainloop()

	def close_app(self):
		if self.popup:
			try:
				print "closing RunAlanlysis popup from RangeSelector"
				self.popup.close_app()
			except:
				print "RangeSelector could not close its RunAlanlysis popup"
				pass
		
		try:
			self.parent.destroy()
		except:
			pass
def clean_sgf(txt):
	return txt
	for private_property in ["MULTIGOGM","MULTIGOBM"]:
		if private_property in txt:
			print "removing private property",private_property,"from sgf content"
			txt1,txt2=txt.split(private_property+'[')				
			txt=txt1+"]".join(txt2.split(']')[1:])
	return txt

class RangeSelector(Frame):
	def __init__(self,parent,filename):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		root = self
		root.parent.title('GoReviewPartner')

		txt = open(self.filename)
		content=txt.read()
		txt.close()
		self.g = sgf.Sgf_game.from_string(clean_sgf(content))
		self.move_zero=self.g.get_root()
		nb_moves=get_moves_number(self.move_zero)
		self.nb_moves=nb_moves
		s = StringVar()
		s.set("all")

		Label(self,text="Select moves to be analysed").grid(row=0,column=1,sticky=W)
		
		r1=Radiobutton(self,text="Analyse all "+str(nb_moves)+" moves",variable=s, value="all")
		r1.grid(row=1,column=1,sticky=W)
		self.after(0,r1.select)
		
		r2=Radiobutton(self,text="Analyse only those moves: ",variable=s, value="only")
		r2.grid(row=2,column=1,sticky=W)
		
		only_entry=Entry(self)
		only_entry.bind("<Button-1>", lambda e: r2.select())
		only_entry.grid(row=2,column=2,sticky=W)
		only_entry.delete(0, END)
		only_entry.insert(0, "1-"+str(nb_moves))
		
		Label(self,text="").grid(row=8,column=1)
		Label(self,text="Select colors to be analysed").grid(row=9,column=1,sticky=W)
		
		c = StringVar()
		c.set("both")
		
		c0=Radiobutton(self,text="Black & white",variable=c, value="both")
		c0.grid(row=10,column=1,sticky=W)
		self.after(0,c0.select)
		
		if 'PB[' in content:
			black_player=content.split('PB[')[1].split(']')[0]
			if black_player.lower().strip() in ['black','']:
				black_player=''
			else:
				black_player=' ('+black_player+')'
		else:
			black_player=''
		
		if 'PW[' in content:
			white_player=content.split('PW[')[1].split(']')[0]
			if white_player.lower().strip() in ['white','']:
				white_player=''
			else:
				white_player=' ('+white_player+')'
		else:
			white_player=''
			
		c1=Radiobutton(self,text="Black only"+black_player,variable=c, value="black")
		c1.grid(row=11,column=1,sticky=W)
		
		c2=Radiobutton(self,text="White only"+white_player,variable=c, value="white")
		c2.grid(row=12,column=1,sticky=W)
		
		Label(self,text="").grid(row=99,column=1)
		Button(self,text="Start",command=self.start).grid(row=100,column=2,sticky=E)
		self.mode=s
		self.color=c
		self.nb_moves=nb_moves
		self.only_entry=only_entry
		self.popup=None
	
	def close_app(self):
		if self.popup:
			try:
				print "closing RunAlanlysis popup from RangeSelector"
				self.popup.close_app()
			except:
				print "RangeSelector could not close its RunAlanlysis popup"
				pass
	
	def start(self):
		if self.mode.get()=="all":
			move_selection=range(1,self.nb_moves+1)
		else:
			move_selection=[]
			selection = self.only_entry.get()
			selection=selection.replace(" ","")
			for sub_selection in selection.split(","):
				if sub_selection:
					try:
						if "-" in sub_selection:
							a,b=sub_selection.split('-')
							a=int(a)
							b=int(b)
						else:
							a=int(sub_selection)
							b=a
						if a<=b and a>0 and b<=self.nb_moves:
							move_selection.extend(range(a,b+1))
					except:
						alert("Could not make sens of the move range.\nPlease indicate one or more move intervals (ie: \"10-20, 40,50-51,63,67\")")
						return
			move_selection=list(set(move_selection))
			move_selection=sorted(move_selection)
			
		if self.color.get()=="black":
			print "black only"
			new_move_selection=[]
			for m in move_selection:
				one_move=go_to_move(self.move_zero,m)
				player_color,player_move=one_move.get_move()
				if player_color.lower()=='b':
					new_move_selection.append(m)
			move_selection=new_move_selection
		elif self.color.get()=="white":
			print "white only"
			new_move_selection=[]
			for m in move_selection:
				one_move=go_to_move(self.move_zero,m)
				player_color,player_move=one_move.get_move()
				if player_color.lower()=='w':
					new_move_selection.append(m)
			move_selection=new_move_selection
		
		print "========= move selection"
		print move_selection
		
		self.parent.destroy()
		newtop=Tk()
		self.popup=RunAnalysis(newtop,self.filename,move_selection)
		self.popup.pack()
		newtop.mainloop()








if __name__ == "__main__":
	if len(argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf', '.sgf')])
		temp_root.destroy()
		print filename
		print "gamename:",filename[:-4]
		if not filename:
			sys.exit()
		print "filename:",filename
		top = Tk()
		RangeSelector(top,filename).pack()
		top.mainloop()
	else:
		filename=argv[1]
		top = Tk()
		RunAnalysis(top,filename).pack()
		top.mainloop()
	




