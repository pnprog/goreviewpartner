# -*- coding: utf-8 -*-  # Définition l'encodage des caractères

from Tkinter import *
from ScrolledText import *
import tkFont
import sys,time
import tkFileDialog
from functools import partial

from toolbox import log

import os

from gtp import gtp
import ConfigParser

Config = ConfigParser.ConfigParser()
Config.read("config.ini")

bg='#C0C0C0'

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
		if not node:
			return False
		node=node[0]
		k+=1
	return node

def gtp2ij(move):
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return int(move[1:])-1,letters.index(move[0].lower())


def ij2gtp(m):
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


class OpenChart():
	def __init__(self,parent,data):
		self.parent=parent
		
		self.data=data
		

		self.initialize()
	def close(self):
		log("closing popup")
		self.popup.destroy()			
		self.parent.all_popups.remove(self)
		log("done")
	
	def click(self,event):
		dim=self.dim
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
				
				if self.okray:
					self.ray.place(ij2gtp((i,j)),color)
				
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
				self.undo_button.config(state='normal')
	
	def initialize(self):
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		popup_width=self.parent.winfo_width()
		popup_height=self.parent.winfo_height()/2
		
		

		
		self.popup=Toplevel()
		popup=self.popup
		popup.geometry(str(popup_width)+'x'+str(popup_height))
		popup.configure(background=bg)
		
		top_frame=Frame(popup)
		top_frame.pack()
		top_frame.pack()
		
		self.graph_mode=StringVar()
		self.graph_mode.set("Win rate") # initialize		
		Radiobutton(top_frame, text="Win rate",command=self.display,variable=self.graph_mode, value="Win rate",indicatoron=0).pack(side=LEFT)
		Radiobutton(top_frame, text="Black comparison",command=self.display,variable=self.graph_mode, value="Black comparison",indicatoron=0).pack(side=LEFT)
		Radiobutton(top_frame, text="White comparison",command=self.display,variable=self.graph_mode, value="White comparison",indicatoron=0).pack(side=LEFT)
		
		self.chart = Canvas(popup,bg='white',bd=0, borderwidth=0)
		#self.chart.grid(sticky=N+S+W+E)
		
		self.chart.pack(fill=BOTH,expand=1)
		self.chart.bind("<Configure>",self.display)
		
		bottom_frame=Frame(popup)
		bottom_frame.pack(anchor=W)
		
		self.status_bar=Label(bottom_frame,text='',background=bg)
		self.status_bar.pack(anchor=W)
		bottom_frame.pack()
	
		self.clear_status()
		self.popup.bind('<Control-q>', self.save_as_ps)
	
	def set_status(self,event=None,msg=''):
		self.status_bar.config(text=msg)
	
	def clear_status(self,event=None):
		self.status_bar.config(text="<Ctrl+Q> to export goban as postscript image.")
	
	def goto_move(self,event=None,move=None):
		if move:
			log("goto move",move)
			#self.parent.parent.lift()
			#self.popup.after(500,self.parent.parent.deiconify)
			#self.parent.parent.lift(self.popup)
			
			"""
			self.parent.parent.grab_set()
			self.parent.parent.focus()
			self.parent.parent.focus_set()
			self.parent.parent.focus_force()
			"""
			
			"""
			self.parent.parent.call('wm', 'attributes', '.', '-topmost', True)
			self.parent.parent.after_idle(self.parent.parent.call, 'wm', 'attributes', '.', '-topmost', False)
			self.parent.parent.focus_force()
			"""
			
			"""
			self.parent.parent.lift()
			self.parent.parent.focus_force()
			self.parent.parent.grab_set()
			self.parent.parent.grab_release()
        	"""
        	
        	#none of the above solutions (or mix of them) does work on my Ubuntu :(
        	# :(
        	
			self.parent.goto_move(move_number=move)
		
	
	def display(self,event=None):
		if event:
			width=event.width
			height=event.height
			self.width=width
			self.height=height
		else:
			width=self.width
			height=self.height
		
		border=min(max(20,width/25),200)
		space=1.0*(width-2*border)/len(self.data)
		lpix=int(border/4)
		for item in self.chart.find_all():
			self.chart.delete(item)
		
		moves=[]
		if self.graph_mode.get()!="Win rate":
			if self.graph_mode.get()=="Black comparison":
				player_color='b'
			else:
				player_color='w'
				
			x00=border
			y00=height-border-(height-2*border)/2.
			for one_data in self.data:
				if one_data:
					if one_data["player_color"]==player_color:
						player_win_rate=one_data["player_win_rate"]
						move=one_data["move"]
						moves.append(move)
						x0=border+(move-1)*space
						x1=x0+space*2
						
						y0=height-border
						y1=height-border-player_win_rate*(height-2*border)/100.
						
						grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
						msg="Move "+str(move)+", win rate: "+str(player_win_rate)+"%"
						self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
						self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
						
						delta=one_data["delta"]
						if delta<>0:
							y2=y1+delta*(height-2*border)/100.
							if delta<0:
								red_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='red',outline='#aa0000')
								msg2="The computer believes it's own move win rate would be "+str(-delta)+"pp higher."
								self.chart.tag_bind(red_bar, "<Enter>", partial(self.set_status,msg=msg2))
								self.chart.tag_bind(red_bar, "<Leave>", self.clear_status)
								self.chart.tag_bind(red_bar, "<Button-1>",partial(self.goto_move,move=move))
							else:
								green_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='#00ff00',outline='#00aa00')
								msg2="The computer believes your move is "+str(delta)+"pp better than it's best move."
								self.chart.tag_bind(green_bar, "<Enter>", partial(self.set_status,msg=msg2))
								self.chart.tag_bind(green_bar, "<Leave>", self.clear_status)
								self.chart.tag_bind(green_bar, "<Button-1>",partial(self.goto_move,move=move))
								
						self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
						self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
						x00=x1
						y00=y1
		else:
			
			self.chart.create_text(border,border/2, text="Black win",fill='black',font=("Arial", str(lpix)))
			x00=border
			y00=height-border-(height-2*border)/2.
			for one_data in self.data:
				if one_data:
					move=one_data["move"]
					moves.append(move)
					x0=border+(move-1)*space
					x1=x0+space
					
					player_win_rate=one_data["player_win_rate"]
					if one_data["player_color"]=="w":
						player_win_rate=100.-player_win_rate
						color="White"
					else:
						color="Black"
					player_win_rate=float(int(player_win_rate*100)/100.)
					y0=height-border
					y1=height-border-player_win_rate*(height-2*border)/100.
					
					grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
					
					msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
					self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
					self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
					self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
					
					self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
					self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
					x00=x1
					y00=y1
		
		#drawing axis
		x0=border
		y0=height-border
		y1=border
		self.chart.create_line(x0, y0, x0, y1, fill='black')
		x1=width-border
		self.chart.create_line(x1, y0, x1, y1, fill='black')
		self.chart.create_line(x0, y0, x1, y0, fill='black')
		self.chart.create_line(x0, (y0+y1)/2, x1, (y0+y1)/2, fill='black')
		
		#drawing vertical graduation
		
		graduations=[x*10 for x in range(10+1)]
		y0=height+1000
		x0=border/2
		x1=width-border/2
		for g in graduations:
			y1=height-border-g*(height-2*border)/100.
			
			if y0-y1>=border:
				self.chart.create_text(x0,y1, text=str(g)+"%",fill='black',font=("Arial", str(lpix)))
				self.chart.create_text(x1,y1, text=str(g)+"%",fill='black',font=("Arial", str(lpix)))
				#self.chart.create_line(x0, y1, x1, y1, fill='black')
				y0=y1
		
		#drawing horizontal graduation
		graduations=[x for x in moves]
		x0=-1000
		y0=height-border/2
		y1=height-border
		for g in graduations:
			x1=border+(g)*(width-2*border)/len(self.data)*1.0
			
			if x1-x0>=border:
				self.chart.create_text(x1,y0, text=str(g),fill='black',font=("Arial", str(lpix)))
				self.chart.create_line(x1, y1, x1, (y0+y1)/2, fill='black')
				x0=x1
				



	def save_as_ps(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title='Choose a filename',filetypes = [('Postscript', '.ps')],initialfile=self.graph_mode.get()+' graph.ps')
		self.chart.postscript(file=filename, colormode='color')


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
			log("unlocking 2/2")
			self.locked=False
		else:
			log("unlocking 1/2")
			self.popup.after(100,lambda: self.unlock(True))
	
	def close(self):
		if self.locked:
			return
		log("closing popup")
		self.popup.destroy()
		if self.okgnugo:
			log("killing gnugo")
			self.gnugo.close()
		if self.okleela:
			log("killing leela")
			self.leela.close()
		if self.okray:
			log("killing ray")
			self.ray.close()
			
		self.parent.all_popups.remove(self)
		
		log("done")
	
	def undo(self,event=None):
		log("UNDO")
		if self.locked:
			log("failed!")
			return

		if len(self.history)<1:
			return
		elif len(self.history)==1:
			self.undo_button.config(state='disabled')
		popup=self.popup
		self.grid,self.markup=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		if self.okgnugo:
			self.gnugo.undo()
		if self.okleela:
			self.leela.undo()
		
		if self.okray:
			#Ray cannot undo
			self.okray=False
			self.buttonray.config(state='disabled')
			
	def click_leela(self):
		if self.locked:
			return
		log("leela play")
		dim=self.dim
		color=self.next_color
		n0=time.time()
		self.lock()
		self.goban.display(self.grid,self.markup,True)
		if color==1:
			move=self.leela.play_black()
		else:
			move=self.leela.play_white()
		log("move=",move,"in",time.time()-n0,"s")
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			log('i,j=',i,j)
			
			if self.okgnugo:
				self.gnugo.place(move,color)
			if self.okray:
				self.ray.place(move,color)
			
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
		self.undo_button.config(state='normal')
		self.unlock()

	def click_ray(self):
		dim=self.dim
		if self.locked:
			return
		
		log("ray play")
		color=self.next_color
		n0=time.time()
		self.lock()
		self.goban.display(self.grid,self.markup,True)
		if color==1:
			move=self.ray.play_black()
		else:
			move=self.ray.play_white()
		log("move=",move,"in",time.time()-n0,"s")
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			log('i,j=',i,j)
			

			if self.okleela:
				self.leela.place(move,color)
			if self.okgnugo:
				self.gnugo.place(move,color)
				
			self.history.append([copy(self.grid),copy(self.markup)])
			
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(dim)] for col in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			#self.ray.undo()
			self.okray=False
			self.buttonray.config(state='disabled')
			
			self.goban.display(self.grid,self.markup)
			if color==1:
				alert("Ray/black: "+move)
			else:
				alert("Ray/white: "+move)

		self.goban.display(self.grid,self.markup)
		self.undo_button.config(state='normal')
		self.unlock()

	def click_gnugo(self):
		dim=self.dim
		if self.locked:
			return
		
		log("gnugo play")
		color=self.next_color
		n0=time.time()
		self.lock()
		self.goban.display(self.grid,self.markup,True)
		if color==1:
			move=self.gnugo.play_black()
		else:
			move=self.gnugo.play_white()
		log("move=",move,"in",time.time()-n0,"s")
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			log('i,j=',i,j)
			

			if self.okleela:
				self.leela.place(move,color)
			if self.okray:
				self.ray.place(move,color)
				
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
		self.undo_button.config(state='normal')
		self.unlock()
	
	
	def click(self,event):
		dim=self.dim
		log("dim:::",dim)
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
				
				if self.okray:
					self.ray.place(ij2gtp((i,j)),color)
				
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
				self.undo_button.config(state='normal')
	
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
		undo_button.config(state='disabled')
		buttonray=Button(panel, text='Ray',command=self.click_ray)
		buttonray.grid(column=0,row=2)
		buttonleela=Button(panel, text=' Leela ',command=self.click_leela)
		buttonleela.grid(column=0,row=3)
		buttongnugo=Button(panel, text='Gnugo',command=self.click_gnugo)
		buttongnugo.grid(column=0,row=4)

		undo_button.bind("<Enter>",lambda e: self.set_status("Undo last move. Shortcut: mouse middle button."))
		buttongnugo.bind("<Enter>",lambda e: self.set_status("Ask GnuGo to play the next move."))
		buttonleela.bind("<Enter>",lambda e: self.set_status("Ask Leela to play the next move."))
		buttonray.bind("<Enter>",lambda e: self.set_status("Ask Ray to play the next move."))
		
		for button in [undo_button,buttongnugo,buttonleela,buttonray]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		
		panel.grid(column=1,row=1,sticky=N)
		
		goban3 = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban3.space=self.goban_size/(dim+1+1)
		goban3.grid(column=2,row=1)
		
		self.popup.bind('<Control-q>', self.save_as_ps)
		goban3.bind("<Enter>",lambda e: self.set_status("<Ctrl+Q> to export goban as postscript image."))
		goban3.bind("<Leave>",lambda e: self.clear_status())
		
		Label(popup,text='   ',background=bg).grid(row=0,column=3)
		Label(popup,text='   ',background=bg).grid(row=2,column=0)
		
		self.status_bar=Label(popup,text='',background=bg)
		self.status_bar.grid(row=2,column=1,columnspan=2,sticky=W)
		
		grid3=[[0 for row in range(dim)] for col in range(dim)]
		markup3=[["" for row in range(dim)] for col in range(dim)]
		
		log("========================")
		log("opening move",move)
		
		if Config.getboolean('Ray', 'NeededForReview'):
			okray=True
			try:
				ray_command_line=[Config.get("Ray", "Command")]+Config.get("Ray", "Parameters").split()
				ray=gtp(ray_command_line)
				ray.boardsize(dim)
				ray.reset()
				ray.komi(komi)
				self.ray=ray
				self.buttonray=buttonray
			except Exception, e:
				okray=False
				log("Could not launch Ray")
				log(e)
				buttonray.destroy()
		else:
			okray=False
			buttonray.destroy()
		
		if Config.getboolean('Leela', 'NeededForReview'):
			okleela=True
			try:
				leela_command_line=[Config.get("Leela", "Command")]+Config.get("Leela", "Parameters").split()
				leela=gtp(leela_command_line)
				leela.boardsize(dim)
				leela.reset()
				leela.komi(komi)
				time_per_move=int(Config.get("Leela", "TimePerMove"))
				leela.set_time(main_time=time_per_move,byo_yomi_time=time_per_move,byo_yomi_stones=1)
				self.leela=leela
			except Exception, e:
				okleela=False
				log("Could not launch Leela")
				log(e)
				buttonleela.destroy()
		else:
			okleela=False
			buttonleela.destroy()
		
		if Config.getboolean('GnuGo', 'NeededForReview'):
			okgnugo=True
			try:
				gnugo_command_line=[Config.get("GnuGo", "Command")]+Config.get("GnuGo", "Parameters").split()
				gnugo=gtp(gnugo_command_line)
				gnugo.boardsize(dim)
				gnugo.reset()
				gnugo.komi(komi)
				self.gnugo=gnugo
			except Exception, e:
				okgnugo=False
				log("Could not launch GnuGo")
				log(e)
				buttongnugo.destroy()
		else:
			okgnugo=False
			buttongnugo.destroy()
		
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
				if okray:
					ray.place_black(ij2gtp((row,col)))
			else:
				place(grid3,row,col,2)
				if okleela:
					leela.place_white(ij2gtp((row,col)))
				if okgnugo:
					gnugo.place_white(ij2gtp((row,col)))
				if okray:
					ray.place_white(ij2gtp((row,col)))
				
		m=0
		for m in range(1,move):
			one_move=get_node(gameroot,m)
			if one_move==False:
				log("(0)leaving because one_move==False")
				return
			
			ij=one_move.get_move()[1]
			
			log(ij)
			
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			
			if okleela:
				leela.place(ij2gtp(ij),color)
			if okgnugo:
				gnugo.place(ij2gtp(ij),color)
			if okray:
				ray.place(ij2gtp(ij),color)
				
			if ij==None:
				log("(0)skipping because ij==None",ij)
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
			log("error when trying to figure out next color to play, so black is selected")
			self.next_color=1
		goban3.display(grid3,markup3)
		
		self.goban=goban3
		self.grid=grid3
		self.markup=markup3
		self.okgnugo=okgnugo
		self.okleela=okleela
		self.okray=okray
		self.undo_button=undo_button
		popup.protocol("WM_DELETE_WINDOW", self.close)
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]

	def save_as_ps(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title='Choose a filename',filetypes = [('Postscript', '.ps')],initialfile='variation_move'+str(self.move)+'.ps')
		self.goban.postscript(file=filename, colormode='color')

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
	

	def goto_move(self,move_number,pressed=None):
		self.move_number.config(text=str(move_number)+'/'+str(get_node_number(self.gameroot)))
		if not pressed:
			self.current_move=move_number
			self.display_move(self.current_move)
		elif self.pressed==pressed:
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
		log(move,'/',len(self.current_variation_sequence))
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
	
	def prepare_data_for_chart(self):
		data=[]
		for m in range(1,get_node_number(self.gameroot)+1):
			
			try:
				one_data={}
				txt=""
				txt+="move "+str(m)
				
				one_move=get_node(self.gameroot,m)
				
				computer_move=one_move.get('CBM')
				
				player_color,player_move=one_move.get_move()
				player_move=ij2gtp(player_move)
				
				one_data['move']=m
				one_data['player_color']=player_color.lower()
				
				if player_color in ('w',"W"):
					computer_win_rate=one_move.get('WWR').replace("%","")
					player_win_rate=get_node(self.gameroot,m+1).get('WWR').replace("%","")
				else:
					log("#"+str(m)+"#BWR#",one_move.get('BWR'))
					log(one_move.get('BWR').replace("%",""))
					computer_win_rate=one_move.get('BWR').replace("%","")
					player_win_rate=get_node(self.gameroot,m+1).get('BWR').replace("%","")
				one_data['computer_win_rate']=float(computer_win_rate)
				one_data['player_win_rate']=float(player_win_rate)
				
				if player_move==computer_move:
					player_win_rate=computer_win_rate

				delta=float(player_win_rate.replace("%",""))-float(computer_win_rate.replace("%",""))
				one_data['delta']=delta

				data.append(one_data)
			except Exception, e:
				if str(e) in ("'BWR'","'WWR'"):
					log("No win rate information for move",m)
					log(e)
				elif str(e) in ("'CBM'"):
					log("No computer best move information for move",m)
					log(e)
				else:
					log(e)
				data.append(None)
		return data
	
	def show_graphs(self,event=None):

		
		new_popup=OpenChart(self,self.data_for_chart)
		self.all_popups.append(new_popup)
		
	
	def hide_territories(self,event=None):
		self.goban1.display(self.current_grid,self.current_markup)
	
	def display_move(self,move=1):
		dim=self.dim
		goban1=self.goban1
		goban2=self.goban2
		

		
		self.move_number.config(text=str(move)+'/'+str(get_node_number(self.gameroot)))
		log("========================")
		log("displaying move",move)
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
				log("(0)leaving because one_move==False")
				return
			
			ij=one_move.get_move()[1]
			
			if ij==None:
				log("(0)skipping because ij==None",ij)
				continue

			
			if one_move.get_move()[0]=='b':color=1
			else:color=2
			i,j=ij
			place(grid1,i,j,color)
			place(grid2,i,j,color)
			
			if len(one_move)==0:
				log("(0)leaving because len(one_move)==0")
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
		if m>=0:
			if get_node(self.gameroot,m+1).has_property("C"):
				self.comment_box1.insert(END,get_node(self.gameroot,m+1).get("C"))
		if m>0:
			markup1[i][j]=0
			markup2[i][j]=0



		self.comment_box2.delete(1.0, END)
		#next sequence in current game ############################################################################
		main_sequence=[]
		for m in range(self.realgamedeepness):
			one_move=get_node(self.gameroot,move+m)
			if one_move==False:
				log("(00)leaving because one_move==False")
				break
			ij=one_move.get_move()[1]
			if ij==None:
				log("(0)skipping because ij==None",ij)
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
			log("(1)leaving because one_move==False")
			return
		if len(parent)<=1:
			log("no alternative move")
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
				try:
					black_prob=float(one_alternative.get("C").split(": ")[1].replace("%","").split('/')[0])
					white_prob=100-black_prob
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
				except:
					pass
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
		log("Opening move",self.current_move)
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
		
		log("boardsize:",self.dim)
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
		
		self.data_for_chart=self.prepare_data_for_chart()
		for data in self.data_for_chart:
			if data<>None:
				
				
				self.charts_button=Button(self, text='graphs')
				self.charts_button.bind('<Button-1>', self.show_graphs)
				self.charts_button.grid(column=3,row=2,sticky=E)
				break
		
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
		
		self.parent.bind('<Control-q>', self.save_left_as_ps)
		self.parent.bind('<Control-w>', self.save_right_as_ps)
		
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
		
		self.goban1.bind("<Enter>",lambda e: self.set_status("<Ctrl+Q> to export goban as postscript image."))
		self.goban2.bind("<Enter>",lambda e: self.set_status("<Ctrl+W> to export goban as postscript image."))
		
		first_move_button.bind("<Enter>",lambda e: self.set_status("Go to first move."))
		prev_10_moves_button.bind("<Enter>",lambda e: self.set_status("Go back 10 moves."))
		prev_button.bind("<Enter>",lambda e: self.set_status("Go back one move. Shortcut: keyboard left key."))
		open_button.bind("<Enter>",lambda e: self.set_status("Open this position onto a third goban to play out variations."))
		next_button.bind("<Enter>",lambda e: self.set_status("Go forward one move. Shortcut: keyboard right key."))
		next_10_moves_button.bind("<Enter>",lambda e: self.set_status("Go forward 10 moves."))
		final_move_button.bind("<Enter>",lambda e: self.set_status("Go to final move."))
		self.territory_button.bind("<Enter>",lambda e: self.set_status("Keep pressed to show territories."))
		for button in [first_move_button,prev_10_moves_button,prev_button,open_button,next_button,next_10_moves_button,final_move_button,self.territory_button,self.goban1,self.goban2]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		
	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")

	def save_left_as_ps(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title='Choose a filename',filetypes = [('Postscript', '.ps')],initialfile='move'+str(self.current_move)+'.ps')
		self.goban1.postscript(file=filename, colormode='color')
	
	def save_right_as_ps(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title='Choose a filename',filetypes = [('Postscript', '.ps')],initialfile='move'+str(self.current_move)+'.ps')
		self.goban2.postscript(file=filename, colormode='color')

from gomill import sgf, sgf_moves
import goban
goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

if __name__ == "__main__":

	if len(sys.argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf for review', '.rsgf')])
		temp_root.destroy()
		log(filename)

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

	
	
