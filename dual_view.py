# -*- coding: utf-8 -*-  # Définition l'encodage des caractères

from Tkinter import *
from ScrolledText import *
import tkFont
import sys,time
import tkFileDialog
from functools import partial

import os

from gtp import gtp
import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read("config.ini")

bg='silver'

from goban import *

def get_node_number(node):
	k=0
	while node:
		node=node[0]
		k+=1
	return k

def get_node(root,number=0):
	if number==0:return root
	node=root
	k=0
	while k!=number:
		#print node.get_move()
		if not node:
			return False
		node=node[0]
		k+=1
	return node








def gtp2ij(move):
	#print "gtp2ij("+move+")"
	# a18 => (17,0)
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return int(move[1:])-1,letters.index(move[0].lower())


def ij2gtp(m):
	#print "ij2gtp("+str(m)+")"
	# (17,0) => a18
	
	if m==None:
		return "pass"
	i,j=m
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return letters[j]+str(i+1)



def alert(text_to_display):
	popup=Toplevel()
	label= Label(popup,text=text_to_display)
	label.pack()
	ok_button = Button(popup, text="OK", command=popup.destroy)
	ok_button.pack()
	#popup.mainloop()


class OpenMove():
	def __init__(self,parent,move,dim,sgf,goban_size=200):
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
		self.goban_size=goban_size
		self.initialize()
		
		
	def lock(self):
		self.locked=True

	def unlock(self,after=False):
		if after:
			print "unlocking 2/2"
			self.locked=False
		else:
			print "unlocking 1/2"
			self.popup.after(100,lambda: self.unlock(True))
	
	def close(self):
		if self.locked:
			return
		print "closing popup"
		self.popup.destroy()
		if self.okgnugo:
			print "killing gnugo"
			self.gnugo.close()
		if self.okleela:
			print "killing leela"
			self.leela.close()
		
		self.parent.all_popups.remove(self)
		
		print "done"
	
	def undo(self,event=None):
		print "UNDO"
		if self.locked:
			print "failed!"
			return

		if len(self.history)<1:
			return
		popup=self.popup
		self.grid,self.markup=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		if self.okgnugo:
			self.gnugo.undo()
		if self.okleela:
			self.leela.undo()


	def click_leela(self):
		if self.locked:
			return
		print "leela play"
		dim=self.dim
		color=self.next_color
		n0=time.time()
		self.lock()
		self.goban.display(self.grid,self.markup,True)
		if color==1:
			move=self.leela.play_black()
		else:
			move=self.leela.play_white()
		print "move=",move,"in",time.time()-n0,"s"
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			print 'i,j=',i,j
			
			if self.okgnugo:
				self.gnugo.place(move,color)
			
			self.history.append([copy(self.grid),copy(self.markup)])
			
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(dim)] for col in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			self.leela.undo()
			if color==1:
				alert("Leela/black: "+move)
			else:
				alert("Leela/white: "+move)
		
		self.goban.display(self.grid,self.markup)
		self.unlock()

	def click_gnugo(self):
		dim=self.dim
		if self.locked:
			return
		
		print "gnugo play"
		color=self.next_color
		n0=time.time()
		self.lock()
		self.goban.display(self.grid,self.markup,True)
		if color==1:
			move=self.gnugo.play_black()
		else:
			move=self.gnugo.play_white()
		print "move=",move,"in",time.time()-n0,"s"
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			print 'i,j=',i,j
			

			if self.okleela:
				self.leela.place(move,color)
			
			self.history.append([copy(self.grid),copy(self.markup)])
			
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(dim)] for col in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			self.gnugo.undo()
			self.goban.display(self.grid,self.markup)
			if color==1:
				alert("GnuGo/black: "+move)
			else:
				alert("GnuGo/white: "+move)

		self.goban.display(self.grid,self.markup)
		self.unlock()
	
	
	def click(self,event):
		dim=self.dim
		print "dim:::",dim
		#add/remove black stone
		#check pointer location
		i,j=self.goban.xy2ij(event.x,event.y)
		color=self.next_color
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			#inside the grid
			#what is under the pointer ?
			
			if self.grid[i][j] not in (1,2):
				#nothing, so we add a black stone			
				
				if self.okgnugo:
					if not self.gnugo.place(ij2gtp((i,j)),color):
						return
				if self.okleela:
					self.leela.place(ij2gtp((i,j)),color)
				
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
	
	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")
	
	def initialize(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		sgf=self.sgf
		komi=self.sgf.get_komi()
		gameroot=self.sgf.get_root()
		
		self.popup=Toplevel()
		popup=self.popup
		
		dim=self.dim
		move=self.move
		
		popup.configure(background=bg)
		self.locked=False
		panel=Frame(popup)
		panel.configure(background=bg)
		
		
		undo_button=Button(panel, text=' undo  ',command=self.undo)
		undo_button.grid(column=0,row=1)
		buttongnugo=Button(panel, text='Gnugo',command=self.click_gnugo)
		buttongnugo.grid(column=0,row=2)
		buttonleela=Button(panel, text=' Leela ',command=self.click_leela)
		buttonleela.grid(column=0,row=3)
		

		undo_button.bind("<Enter>",lambda e: self.set_status("Undo last move. Shortcut: mouse middle button."))
		buttongnugo.bind("<Enter>",lambda e: self.set_status("Ask GnuGo to play the next move."))
		buttonleela.bind("<Enter>",lambda e: self.set_status("Ask Leela to play the next move."))
		for button in [undo_button,buttongnugo,buttonleela]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		
		panel.grid(column=1,row=1,sticky=N)
		
		goban3 = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban3.space=self.goban_size/(dim+1+1)
		goban3.grid(column=2,row=1)
		
		Label(popup,text='   ',background=bg).grid(row=0,column=3)
		Label(popup,text='   ',background=bg).grid(row=2,column=0)
		
		self.status_bar=Label(popup,text='',background=bg)
		self.status_bar.grid(row=2,column=1,columnspan=2,sticky=W)
		
		grid3=[[0 for row in range(dim)] for col in range(dim)]
		markup3=[["" for row in range(dim)] for col in range(dim)]
		
		print "========================"
		print "opening move",move
		
		okleela=True
		try:
			leela_command_line=tuple(Config.get("Leela", "Command").split())
			leela=gtp(leela_command_line)
			leela.boardsize(dim)
			leela.reset()
			leela.komi(komi)
			time_per_move=int(Config.get("Analysis", "TimePerMove"))
			leela.set_time(main_time=time_per_move,byo_yomi_time=time_per_move,byo_yomi_stones=1)
			self.leela=leela
		except Exception, e:
			okleela=False
			print "Could not launch Leela"
			print e
			buttonleela.config(state="disabled")
			
			

		okgnugo=True
		try:
			gnugo_command_line=tuple(Config.get("GnuGo", "Command").split())
			gnugo=gtp(gnugo_command_line)
			gnugo.boardsize(dim)
			gnugo.reset()
			gnugo.komi(komi)
			self.gnugo=gnugo
		except Exception, e:
			okgnugo=False
			print "Could not launch GnuGo"
			print e
			buttongnugo.config(state="disabled")
		
		board, _ = sgf_moves.get_setup_and_moves(self.sgf)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid3,row,col,1)
				if okleela:
					leela.place_black(ij2gtp((row,col)))
				if okgnugo:
					gnugo.place_black(ij2gtp((row,col)))
			else:
				place(grid3,row,col,2)
				if okleela:
					leela.place_white(ij2gtp((row,col)))
				if okgnugo:
					gnugo.place_white(ij2gtp((row,col)))
				
		m=0
		for m in range(1,move):
			one_move=get_node(gameroot,m)
			if one_move==False:
				print "(0)leaving because one_move==False"
				return
			
			ij=one_move.get_move()[1]
			
			print ij
			
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			
			if okleela:
				leela.place(ij2gtp(ij),color)
			if okgnugo:
				gnugo.place(ij2gtp(ij),color)
			
			if ij==None:
				print "(0)skipping because ij==None",ij
				continue

			i,j=ij
			place(grid3,i,j,color)
		
		if m>0:
			markup3[i][j]=0
		
		try:
			if get_node(gameroot,move).get_move()[0].lower()=="w":
				self.next_color=2
			else:
				self.next_color=1
		except:
			print "error when trying to figure out next color to play, so black is selected"
			self.next_color=1
		goban3.display(grid3,markup3)
		
		self.goban=goban3
		self.grid=grid3
		self.markup=markup3
		self.okgnugo=okgnugo
		self.okleela=okleela
		
		popup.protocol("WM_DELETE_WINDOW", self.close)
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]
		
		

class DualView(Frame):
	def __init__(self,parent,filename,goban_size=200):
		Frame.__init__(self,parent)
		
		self.parent=parent
		self.filename=filename
		self.goban_size=goban_size
		
		self.initialize()
		
		self.current_move=1
		self.display_move(self.current_move)

		self.pressed=0

	def close_app(self):
		for popup in self.all_popups[:]:
			popup.close()
			"""
			if popup.okgnugo:
				print "killing gnugo"
				popup.gnugo.kill()
			if popup.okleela:
				print "killing leela"
				popup.leela.kill()
			"""
		self.destroy()
		self.parent.destroy()

	
	def prev_10_move(self,event=None):
		self.current_move=max(1,self.current_move-10)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())

	def prev_move(self,event=None):
		if self.current_move>1:
			self.pressed=time.time()
			self.current_move-=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())
	
	def next_10_move(self,event=None):
		self.current_move=min(get_node_number(self.gameroot),self.current_move+10)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
	
	def next_move(self,event=None):
		if self.current_move<get_node_number(self.gameroot):
			self.pressed=time.time()
			self.current_move+=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())
			
	def first_move(self,event=None):
		self.current_move=1
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
		
	def final_move(self,event=None):
		self.current_move=get_node_number(self.gameroot)
		self.pressed=time.time()
		pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
		self.parent.after(0,lambda: pf())
	

	def goto_move(self,move_number,pressed):
		self.move_number.config(text=str(move_number)+'/'+str(get_node_number(self.gameroot)))
		if self.pressed==pressed:
			self.display_move(self.current_move)
			
	def leave_variation(self,goban,grid,markup):
		self.comment_box2.delete(1.0, END)
		self.parent.bind("<Up>", lambda e: None)
		self.parent.bind("<Down>", lambda e: None)
		self.current_variation_sequence=None
		self.clear_status()
		goban.display(grid,markup)

	def show_variation(self,event,goban,grid,markup,i,j):
		sequence=markup[i][j]
		self.show_variation_move(goban,grid,markup,i,j,len(sequence))
	
	
	def show_variation_move(self,goban,grid,markup,i,j,move):
		sequence=markup[i][j]
		temp_grid=copy(grid)
		temp_markup=copy(markup)
		
		for u in range(self.dim):
			for v in range(self.dim):
				if temp_markup[u][v]!=0:
					temp_markup[u][v]=''
		
		k=1
		for color,(u,v),s,comment,displaycolor,letter_color in sequence[:move]:
			#temp_grid[u][v]=color
			place(temp_grid,u,v,color)
			temp_markup[u][v]=k
			k+=1
		
		goban.display(temp_grid,temp_markup)
		
		self.comment_box2.delete(1.0, END)
		if comment:
			self.comment_box2.insert(END,comment)
		u=i+goban.mesh[i][j][0]
		v=j+goban.mesh[i][j][1]
		local_area=goban.draw_point(u,v,1,color="",outline="")
		goban.tag_bind(local_area, "<Leave>", lambda e: self.leave_variation(goban,grid,markup))
		
		self.current_variation_goban=goban
		self.current_variation_grid=grid
		self.current_variation_markup=markup
		self.current_variation_i=i
		self.current_variation_j=j
		self.current_variation_move=move
		self.current_variation_sequence=sequence
		
		self.parent.bind("<Up>", self.show_variation_next)
		self.parent.bind("<Down>", self.show_variation_prev)
		self.parent.bind("<MouseWheel>", self.mouse_wheel)
		goban.tag_bind(local_area,"<Button-4>", self.show_variation_next)
		goban.tag_bind(local_area,"<Button-5>", self.show_variation_prev)
		self.set_status("Use mouse wheel or keyboard up/down keys to display the sequence move by move.")
	
	def mouse_wheel(self,event):
		if self.current_variation_sequence==None:
			return
		d = event.delta
		if d>0:
			self.show_variation_next()
		elif d<0:
			self.show_variation_prev()
	
	def show_variation_next(self,event=None):
		
		move=(self.current_variation_move+1)%(len(self.current_variation_sequence)+1)
		move=max(1,move)
		print move,'/',len(self.current_variation_sequence)
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)
	
	def show_variation_prev(self,event=None):
		move=(self.current_variation_move-1)%len(self.current_variation_sequence)
		if move<1:
			move=len(self.current_variation_sequence)
		
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)

	def show_territories(self,event=None):
		black_t=self.territories[0]
		white_t=self.territories[1]
		
		dim=self.dim
		markup=[["" for row in range(dim)] for col in range(dim)]
		
		for i,j in black_t:
			markup[i][j]=-1
		
		for i,j in white_t:
			markup[i][j]=-2
		
		self.goban1.display(self.current_grid,markup)
	
	def hide_territories(self,event=None):
		self.goban1.display(self.current_grid,self.current_markup)
	
	def display_move(self,move=1):
		dim=self.dim
		goban1=self.goban1
		goban2=self.goban2
		

		
		self.move_number.config(text=str(move)+'/'+str(get_node_number(self.gameroot)))
		print "========================"
		print "displaying move",move
		grid1=[[0 for row in range(dim)] for col in range(dim)]
		markup1=[["" for row in range(dim)] for col in range(dim)]
		grid2=[[0 for row in range(dim)] for col in range(dim)]
		markup2=[["" for row in range(dim)] for col in range(dim)]
		board, _ = sgf_moves.get_setup_and_moves(self.sgf)

		self.current_grid=grid1
		self.current_markup=markup1

		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid1,row,col,1)
				place(grid2,row,col,1)
			else:
				place(grid1,row,col,2)
				place(grid2,row,col,2)
		
		
		m=0
		for m in range(1,move):
			one_move=get_node(self.gameroot,m)
			if one_move==False:
				print "(0)leaving because one_move==False"
				return
			
			ij=one_move.get_move()[1]
			
			if ij==None:
				print "(0)skipping because ij==None",ij
				continue

			
			if one_move.get_move()[0]=='b':color=1
			else:color=2
			i,j=ij
			place(grid1,i,j,color)
			place(grid2,i,j,color)
			
			if len(one_move)==0:
				print "(0)leaving because len(one_move)==0"
				goban1.display(grid1,markup1)
				goban2.display(grid2,markup2)
				return
		

		
		self.territories=[[],[]]
		if m>0:
			if one_move.has_property("TB"):
				self.territories[0]=one_move.get("TB")
			if one_move.has_property("TW"):
				self.territories[1]=one_move.get("TW")
		if self.territories!=[[],[]]:
			self.territory_button.grid()
		else:
			self.territory_button.grid_remove()
		
		#indicating last play with delta
		self.comment_box1.delete(1.0, END)
		if m>0:
			if get_node(self.gameroot,m+1).has_property("C"):
				self.comment_box1.insert(END,get_node(self.gameroot,m+1).get("C"))
			markup1[i][j]=0
			markup2[i][j]=0



		self.comment_box2.delete(1.0, END)
		#next sequence in current game ############################################################################
		main_sequence=[]
		for m in range(self.realgamedeepness):
			one_move=get_node(self.gameroot,move+m)
			if one_move==False:
				print "(00)leaving because one_move==False"
				break
			ij=one_move.get_move()[1]
			if ij==None:
				print "(0)skipping because ij==None",ij
				break
			if one_move.get_move()[0]=='b':	c=1
			else: c=2
			main_sequence.append([c,ij,"A",None,"black","black"])
			if m==0:
				real_game_ij=ij
		try:
			#i,j=one_move=get_node(self.gameroot,move).get_move()[1]
			i,j=get_node(self.gameroot,move).get_move()[1]
		except:
			self.prev_move()
			return
		markup1[i][j]=main_sequence
		
		#alternative sequences ####################################################################################
		parent=get_node(self.gameroot,move-1)
		if parent==False:
			print "(1)leaving because one_move==False"
			return
		if len(parent)<=1:
			print "no alternative move"
			#display(goban1,grid1,markup1)
			#display(goban2,grid2,markup2)
			goban1.display(grid1,markup1)
			goban2.display(grid2,markup2)
			
			return
		
		for a in range(1,len(parent)):
			one_alternative=parent[a]
			ij=one_alternative.get_move()[1]
			
			
			
			displaycolor='black'
			
			
			if one_alternative.get_move()[0]=='b': c=1
			else: c=2

			if one_alternative.has_property("C"):
				comment=one_alternative.get("C")
				black_prob=float(one_alternative.get("C").split(": ")[1].replace("%","").split('/')[0])
				white_prob=100-black_prob
				#print "black_prob:",black_prob,'c=',c
				if c==1:
					if black_prob>=50:
						displaycolor="blue"
					else:
						displaycolor="red"
				else:
					if black_prob>50:
						displaycolor="red"
					else:
						displaycolor="blue"
			else: comment=''
			
			if ij==real_game_ij: letter_color="black"
			else: letter_color=displaycolor
			
			alternative_sequence=[[c,ij,chr(64+a),comment,displaycolor,letter_color]]
			while len(one_alternative)>0:
				one_alternative=one_alternative[0]
				ij=one_alternative.get_move()[1]
				if one_alternative.get_move()[0]=='b':c=1
				else:c=2
				alternative_sequence.append([c,ij,chr(64+a),comment,"whocare?","whocare"])
			i,j=parent[a].get_move()[1]
			markup2[i][j]=alternative_sequence
			
		goban1.display(grid1,markup1)
		goban2.display(grid2,markup2)
		

		
	def open_move(self):
		print "Opening move",self.current_move
		new_popup=OpenMove(self,self.current_move,self.dim,self.sgf,self.goban_size)
		self.all_popups.append(new_popup)
		
	def initialize(self):
		
		
		self.realgamedeepness=5
		try:
			self.realgamedeepness=int(Config.get("Review", "RealGameSequenceDeepness"))
		except:
			Config.set("Review", "RealGameSequenceDeepness",self.realgamedeepness)
			Config.write(open("config.ini","w"))
			
		txt = open(self.filename)
		self.sgf = sgf.Sgf_game.from_string(txt.read())
		txt.close()
		
		self.dim=self.sgf.get_size()
		self.komi=self.sgf.get_komi()
		
		print "boardsize:",self.dim
		#goban.dim=size
		
		#goban.prepare_mesh()
		self.gameroot=self.sgf.get_root()
		

		self.parent.title('GoReviewPartner')
		self.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		
		self.all_popups=[]
		
		self.configure(background=bg)
		
		Label(self,text='   ',background=bg).grid(column=0,row=0)
		
		buttons_bar=Frame(self,background=bg)
		buttons_bar.grid(column=1,row=1,columnspan=3)
		
		first_move_button=Button(buttons_bar, text='|<< ',command=self.first_move)
		first_move_button.grid(column=8,row=1)
		
		prev_10_moves_button=Button(buttons_bar, text=' << ',command=self.prev_10_move)
		prev_10_moves_button.grid(column=9,row=1)
		
		prev_button=Button(buttons_bar, text='prev',command=self.prev_move)
		prev_button.grid(column=10,row=1)
		
		Label(buttons_bar,text='          ',background=bg).grid(column=19,row=1)
		
		self.move_number=Label(buttons_bar,text='   ',background=bg)
		self.move_number.grid(column=20,row=1)
		

		
		Label(buttons_bar,text='          ',background=bg).grid(column=29,row=1)
		
		next_button=Button(buttons_bar, text='next',command=self.next_move)
		next_button.grid(column=30,row=1)
		
		next_10_moves_button=Button(buttons_bar, text=' >> ',command=self.next_10_move)
		next_10_moves_button.grid(column=31,row=1)
		
		final_move_button=Button(buttons_bar, text=' >>|',command=self.final_move)
		final_move_button.grid(column=32,row=1)
		
		buttons_bar2=Frame(self,background=bg)
		buttons_bar2.grid(column=1,row=2,sticky=W)
		
		open_button=Button(buttons_bar2, text='open',command=self.open_move)
		open_button.grid(column=1,row=1)
		
		self.territory_button=Button(buttons_bar2, text='territories')
		self.territory_button.grid(column=2,row=1)
		self.territory_button.bind('<Button-1>', self.show_territories)
		self.territory_button.bind('<ButtonRelease-1>', self.hide_territories)
		
		self.parent.bind('<Left>', self.prev_move)
		self.parent.bind('<Right>', self.next_move)

		#Label(app,background=bg).grid(column=1,row=2)

		row=10

		#Label(self,background=bg).grid(column=1,row=row-1)

		#self.goban1 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban1 = Goban(self.dim,master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		
		self.goban1.grid(column=1,row=row)
		Label(self, text='            ',background=bg).grid(column=2,row=row)
		#self.goban2 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2 = Goban(self.dim, master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2.grid(column=3,row=row)

		self.goban1.space=self.goban_size/(self.dim+1+1)
		self.goban2.space=self.goban_size/(self.dim+1+1)

		Label(self,text='   ',background=bg).grid(column=4,row=row+1)
		
		police = tkFont.nametofont("TkFixedFont")
		lpix = police.measure("a")

		self.comment_box1=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box1.grid(column=1,row=row+4)
		
		self.comment_box2=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box2.grid(column=3,row=row+4)
		
		self.status_bar=Label(self,text='',background=bg)
		self.status_bar.grid(column=1,row=row+5,sticky=W,columnspan=3)
		
		#Label(self,text='   ',background=bg).grid(column=4,row=row+6)
		
		goban.show_variation=self.show_variation
		
		first_move_button.bind("<Enter>",lambda e: self.set_status("Go to first move."))
		prev_10_moves_button.bind("<Enter>",lambda e: self.set_status("Go back 10 moves."))
		prev_button.bind("<Enter>",lambda e: self.set_status("Go back one move. Shortcut: keyboard left key."))
		open_button.bind("<Enter>",lambda e: self.set_status("Open this position onto a third goban to play out variations."))
		next_button.bind("<Enter>",lambda e: self.set_status("Go forward one move. Shortcut: keyboard right key."))
		next_10_moves_button.bind("<Enter>",lambda e: self.set_status("Go forward 10 moves."))
		final_move_button.bind("<Enter>",lambda e: self.set_status("Go to final move."))
		self.territory_button.bind("<Enter>",lambda e: self.set_status("Keep pressed to show territories."))
		for button in [first_move_button,prev_10_moves_button,prev_button,open_button,next_button,next_10_moves_button,final_move_button,self.territory_button]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		
	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")


from gomill import sgf, sgf_moves
import goban
goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

if __name__ == "__main__":

	if len(sys.argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf for review', '.rsgf')])
		temp_root.destroy()
		print filename

		if not filename:
			sys.exit()
	else:
		filename=sys.argv[1]
	
	top = Tk()
	
	display_factor=.5
	try:
		display_factor=float(Config.get("Review", "GobanScreenRatio"))
	except:
		Config.set("Review", "GobanScreenRatio",display_factor)
		Config.write(open("config.ini","w"))
	
	screen_width = top.winfo_screenwidth()
	screen_height = top.winfo_screenheight()
	
	width=int(display_factor*screen_width)
	height=int(display_factor*screen_height)

	DualView(top,filename,min(width,height)).pack(fill=BOTH,expand=1)
	top.mainloop()

	
	
