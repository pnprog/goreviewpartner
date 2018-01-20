# -*- coding: utf-8 -*-

from Tkinter import *
from ScrolledText import *
import tkFont
import sys,time
import tkFileDialog
from functools import partial

from toolbox import *
from toolbox import _

from gnugo_analysis import GnuGoOpenMove
from leela_analysis import LeelaOpenMove
from ray_analysis import RayOpenMove
from aq_analysis import AQOpenMove
from leela_zero_analysis import LeelaZeroOpenMove

import os

from gtp import gtp
import ConfigParser

import threading, Queue

import mss
import mss.tools

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


class OpenChart():
	def __init__(self,parent,data,current_move=0):
		self.parent=parent
		
		self.data=data
		self.current_move=current_move

		self.initialize()
	def close(self):
		log("closing popup")
		self.popup.destroy()
		self.parent.all_popups.remove(self)
		log("done")

	def initialize(self):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		popup_width=self.parent.winfo_width()
		popup_height=self.parent.winfo_height()/2+10
		
		

		
		self.popup=Toplevel()
		popup=self.popup
		popup.geometry(str(popup_width)+'x'+str(popup_height))
		bg=popup.cget("background")
		#popup.configure(background=bg)
		
		top_frame=Frame(popup)
		top_frame.pack()
		top_frame.pack()
		
		self.graph_mode=StringVar()
		self.graph_mode.set("Win rate") # initialize
		Radiobutton(top_frame, text=_("Win rate"),command=self.display,variable=self.graph_mode, value="Win rate",indicatoron=0).pack(side=LEFT, padx=5)
		for data in self.data:
			if data:
				if "delta" in data:
					if data["player_color"]=="b":
						Radiobutton(top_frame, text=_("Black comparison"),command=self.display,variable=self.graph_mode, value="Black comparison",indicatoron=0).pack(side=LEFT, padx=5, pady=5)
						break
		for data in self.data:
			if data:
				if "delta" in data:
					if data["player_color"]=="w":
						Radiobutton(top_frame, text=_("White comparison"),command=self.display,variable=self.graph_mode, value="White comparison",indicatoron=0).pack(side=LEFT, padx=5, pady=5)
						break
		
		self.chart = Canvas(popup,bg='white',bd=0, borderwidth=0)
		#self.chart.grid(sticky=N+S+W+E)
		
		self.chart.pack(fill=BOTH,expand=1, padx=5)
		self.chart.bind("<Configure>",self.display)
		
		bottom_frame=Frame(popup)
		bottom_frame.pack(anchor=W)
		
		self.status_bar=Label(bottom_frame,text='',background=bg)
		self.status_bar.pack(anchor=W)
		bottom_frame.pack()
	
		self.clear_status()
		self.popup.bind('<Control-q>', self.save_as_png)
		
		self.popup.protocol("WM_DELETE_WINDOW", self.close)
		popup.focus()
	
	def set_status(self,event=None,msg=''):
		self.status_bar.config(text=msg)
	
	def clear_status(self,event=None):
		self.status_bar.config(text=_("<Ctrl+Q> to save the graph as an image."))
	
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
		
		self.chart.create_line(0, 0, width, 0, fill='#000000',width=4)
		self.chart.create_line(0, height, width, height, fill='#000000',width=4)
		
		self.chart.create_line(0, 0, 0, height, fill='#000000',width=4)
		
		self.chart.create_line(width, 0, width, height, fill='#000000',width=4)
		
		y00=height-border
		x0=border+(self.current_move-1)*space
		x1=x0+space
		y1=border
		yellow_bar=self.chart.create_rectangle(x0, y00, x1, y1, fill='#FFFF00',outline='#FFFF00')
		
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
					if (one_data["player_color"]==player_color) and ("delta" in one_data):
						position_win_rate=one_data["position_win_rate"]
						move=one_data["move"]
						moves.append(move)
						x0=border+(move-1)*space
						x1=x0+space*2
						
						y0=height-border
						y1=height-border-position_win_rate*(height-2*border)/100.
						
						grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
						
						delta=one_data["delta"]
						
						if player_color.lower()=="b":
							msg=_("Move %i: Black's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
						else:
							msg=_("Move %i: White's move win rate: %s, computer's move win rate: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
						
						self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
						self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
						self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
						
						if delta<>0:
							y2=y1-delta*(height-2*border)/100.
							if delta<0:
								red_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='red',outline='#aa0000')
								msg2=_("The computer believes it's own move win rate would be %.2fpp higher.")%(-delta)
								self.chart.tag_bind(red_bar, "<Enter>", partial(self.set_status,msg=msg2))
								self.chart.tag_bind(red_bar, "<Leave>", self.clear_status)
								self.chart.tag_bind(red_bar, "<Button-1>",partial(self.goto_move,move=move))
							else:
								green_bar=self.chart.create_rectangle(x0, y1, x1, y2, fill='#00ff00',outline='#00aa00')
								msg2=_("The computer believes the actual move is %.2fpp better than it's best move.")%(delta)
								self.chart.tag_bind(green_bar, "<Enter>", partial(self.set_status,msg=msg2))
								self.chart.tag_bind(green_bar, "<Leave>", self.clear_status)
								self.chart.tag_bind(green_bar, "<Button-1>",partial(self.goto_move,move=move))
								
						self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
						self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
						x00=x1
						y00=y1
		else:
			
			self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=("Arial", str(lpix)))
			x00=border
			y00=height-border-(height-2*border)/2.
			for one_data in self.data:
				if one_data:
					move=one_data["move"]
					moves.append(move)
					x0=border+(move-1)*space
					x1=x0+space
					
					position_win_rate=one_data["position_win_rate"]
					if one_data["player_color"]=="w":
						position_win_rate=100.-position_win_rate
						color=_("White")
					else:
						color=_("Black")
					player_win_rate=float(int(position_win_rate*100)/100.)
					y0=height-border
					y1=height-border-position_win_rate*(height-2*border)/100.
					
					grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
					
					#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
					msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(position_win_rate)+"%/"+str(100-player_win_rate)+"%"
					
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
				
	def save_as_png(self,e=None):
		top=Tk()
		top.withdraw()
		filename = tkFileDialog.asksaveasfilename(parent=top,title=_('Choose a filename'),filetypes = [('PNG', '.png')],initialfile=self.graph_mode.get()+' graph.png')
		top.destroy()
		canvas2png(self.chart,filename)

class OpenMove():
	def __init__(self,parent,move,dim,sgf,goban_size=200):
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
		self.goban_size=goban_size
		
		self.available_bots=[RayOpenMove, LeelaOpenMove, GnuGoOpenMove, AQOpenMove, LeelaZeroOpenMove]
		
		self.initialize()
		
	def lock(self):
		self.locked=True
		
		self.undo_button.config(state='disabled')
		self.menu.config(state='disabled')
		self.play_button.config(state='disabled')
		self.white_button.config(state='disabled')
		self.black_button.config(state='disabled')
		if (not self.white_autoplay) or (not self.black_autoplay):
			self.selfplay_button.config(state='disabled')

	def unlock(self,after=False):
		if after:
			log("unlocking 2/2")
			self.locked=False
		else:
			log("unlocking 1/2")
			self.popup.after(100,lambda: self.unlock(True))
			self.undo_button.config(state='normal')
			self.menu.config(state='normal')
			self.play_button.config(state='normal')
			self.white_button.config(state='normal')
			self.black_button.config(state='normal')
			self.selfplay_button.config(state='normal')
	
	def close(self):
		if self.locked:
			return
		log("closing popup")
		self.display_queue.put(0)
		self.popup.destroy()
		
		for bot in self.bots:
			bot.close()

		self.parent.all_popups.remove(self)
		
		log("done")
	
	def undo(self,event=None):
		log("UNDO")
		#if self.locked:
		#	log("failed!")
		#	return

		if len(self.history)<1:
			return
		elif len(self.history)==1:
			self.undo_button.config(state='disabled')
		popup=self.popup
		self.grid,self.markup=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		
		for bot in self.bots:
			bot.undo()
		

	def click_button(self,bot):
		dim=self.dim
		if not self.locked:
			self.lock()
			self.display_queue.put(2)
		
		color=self.next_color
		move=bot.click(color)
		
		if move.lower() not in ["pass","resign"]:
			i,j=gtp2ij(move)
			#log('i,j=',i,j)
			
			for other_bot in self.bots:
				if other_bot!=bot:
					try:
						other_bot.place(move,color)
					except:
						pass
			
			self.history.append([copy(self.grid),copy(self.markup)])
			
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(dim)] for col in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			bot.undo()
			self.display_queue.put(bot.name+" ("+_("Black")+"): "+move.lower())
		
		if self.white_autoplay and self.black_autoplay:
			if move.lower() not in ["pass","resign"]:
				log("SELF PLAY")
				self.display_queue.put(2)
				
				one_thread=threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],))
				self.popup.after(0,one_thread.start())
				return
			else:
				log("End of SELF PLAY")
				self.click_selfplay()
				self.display_queue.put(1)
				self.unlock()
				return
		else:
			self.display_queue.put(1)
			self.unlock()
			return
		
		
		
	def click(self,event):
		if self.locked:
			return
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
				for bot in self.bots:
					if bot.place(ij2gtp((i,j)),color)==False:
						del self.menu_bots[bot.name]
						self.menu.pack_forget()
						if len(self.menu_bots):
							self.selected_bot.set(self.menu_bots.keys()[0])
							self.selected_bot=StringVar()
							self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
							self.menu.pack(fill=BOTH,expand=1)
						else:
							self.menu.config(state='disabled')
							self.play_button.config(state='disabled')
							self.white_button.config(state='disabled')
							self.black_button.config(state='disabled')
							self.selfplay_button.config(state='disabled')
							
				self.history.append([copy(self.grid),copy(self.markup)])
					
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for row in range(dim)] for col in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				self.next_color=3-color
				self.undo_button.config(state='normal')
				
				if color==1:
					if self.white_autoplay:
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])
				else:
					if self.black_autoplay:
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])
						
	def set_status(self,msg,event=None):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")
	
	def click_play_one_move(self):
		#if self.locked:
		#	return
		log("Asking",self.selected_bot.get(),"to play one move")
		self.white_button.config(relief=RAISED)
		self.black_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
		#self.click_button(self.menu_bots[self.selected_bot.get()])


	def click_white_answer(self):
		
		if self.white_button.cget("relief")!=SUNKEN:
			self.white_button.config(relief=SUNKEN)
			self.white_autoplay=True
		else:
			self.white_button.config(relief=RAISED)
			self.white_autoplay=False
		
		self.black_autoplay=False
		
		self.black_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)
		
	def click_black_answer(self):
		
		if self.black_button.cget("relief")!=SUNKEN:
			self.black_button.config(relief=SUNKEN)
			self.black_autoplay=True
		else:
			self.black_button.config(relief=RAISED)
			self.black_autoplay=False
		
		self.white_autoplay=False
		
		self.white_button.config(relief=RAISED)
		self.selfplay_button.config(relief=RAISED)

	def click_selfplay(self):
		self.white_button.config(relief=RAISED)
		self.black_button.config(relief=RAISED)
		if self.selfplay_button.cget("relief")!=SUNKEN:
			if self.locked:
				self.selfplay_button.config(relief=RAISED)
				return
			self.selfplay_button.config(relief=SUNKEN)
			self.black_autoplay=True
			self.white_autoplay=True
			self.selfplay_button.config(text=_('Abort'))
			threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
		else:
			self.selfplay_button.config(relief=RAISED)
			self.black_autoplay=False
			self.white_autoplay=False
			self.selfplay_button.config(text=_('Self play'))
		
	def initialize(self):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		sgf=self.sgf
		komi=self.sgf.get_komi()
		gameroot=self.sgf.get_root()
		
		self.popup=Toplevel()
		popup=self.popup
		
		dim=self.dim
		move=self.move
		
		#popup.configure(background=bg)
		bg=popup.cget("background")
		self.locked=False
		panel=Frame(popup, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		panel.configure(background=bg)
		
		
		undo_button=Button(panel, text=_('Undo'),command=self.undo)
		undo_button.grid(column=0,row=1,sticky=E+W)
		undo_button.config(state='disabled')
		undo_button.bind("<Enter>",lambda e: self.set_status(_("Undo last move. Shortcut: mouse middle button.")))
		undo_button.bind("<Leave>",lambda e: self.clear_status())
		
		self.bots=[]
		self.menu_bots={}
		row=10
		for available_bot in self.available_bots:
			row+=2
			one_bot=available_bot(dim,komi)
			self.bots.append(one_bot)
			
			if one_bot.okbot:
				self.menu_bots[one_bot.name]=one_bot

		if len(self.menu_bots)>0:
			
			row+=10
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			
			row+=1
			self.selected_bot=StringVar()
			self.selected_bot.set(self.menu_bots.keys()[0])
			
			self.menu_wrapper=Frame(panel)
			self.menu_wrapper.grid(row=row,column=0,sticky=E+W)
			self.menu_wrapper.bind("<Enter>",lambda e: self.set_status(_("Select a bot.")))
			self.menu_wrapper.bind("<Leave>",lambda e: self.clear_status())
			
			self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
			self.menu.pack(fill=BOTH,expand=1)
			
			row+=1
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			
			row+=1
			self.play_button=Button(panel, text=_('Play one move'),command=self.click_play_one_move)
			self.play_button.grid(column=0,row=row,sticky=E+W)
			self.play_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play one move.")))
			self.play_button.bind("<Leave>",lambda e: self.clear_status())
			
			
			row+=1
			self.white_button=Button(panel, text=_('Play as white'),command=self.click_white_answer)
			self.white_button.grid(column=0,row=row,sticky=E+W)
			self.white_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play as White.")))
			self.white_button.bind("<Leave>",lambda e: self.clear_status())
			
			row+=1
			self.black_button=Button(panel, text=_('Play as black'),command=self.click_black_answer)
			self.black_button.grid(column=0,row=row,sticky=E+W)
			self.black_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play as Black.")))
			self.black_button.bind("<Leave>",lambda e: self.clear_status())
			
			row+=1
			self.selfplay_button=Button(panel, text=_('Self play'),command=self.click_selfplay)
			self.selfplay_button.grid(column=0,row=row,sticky=E+W)
			self.selfplay_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot to play alone.")))
			self.selfplay_button.bind("<Leave>",lambda e: self.clear_status())
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		goban3 = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban3.space=self.goban_size/(dim+1+1)
		goban3.grid(column=2,row=1,sticky=N+S+E+W)
		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		
		self.popup.bind('<Control-q>', self.save_as_png)
		goban3.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		goban3.bind("<Leave>",lambda e: self.clear_status())
		
		Label(popup,text='   ',background=bg).grid(row=0,column=3)
		Label(popup,text='   ',background=bg).grid(row=2,column=0)
		
		self.status_bar=Label(popup,text='',background=bg)
		self.status_bar.grid(row=2,column=1,columnspan=2,sticky=W)
		
		grid3=[[0 for row in range(dim)] for col in range(dim)]
		markup3=[["" for row in range(dim)] for col in range(dim)]
		
		log("========================")
		log("opening move",move)
		
		board, noneed = sgf_moves.get_setup_and_moves(self.sgf)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				color=1
			else:
				color=2
			
			place(grid3,row,col,color)
			for bot in self.bots:
				bot.place(ij2gtp((row,col)),color)
		
		m=0
		for m in range(1,move):
			one_move=get_node(gameroot,m)
			if one_move==False:
				log("(0)leaving because one_move==False")
				return
			
			ij=one_move.get_move()[1]
			
			#log(ij)
			
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			
			for bot in self.bots:
				bot.place(ij2gtp(ij),color)
			
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

		self.undo_button=undo_button
		
		popup.protocol("WM_DELETE_WINDOW", self.close)
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]

		self.goban.bind("<Configure>",self.redraw)
		popup.focus()
		
		self.display_queue=Queue.Queue(1)
		self.parent.after(100,self.wait_for_display)
	
	def wait_for_display(self):
		try:
			msg=self.display_queue.get(False)
			
			if msg==0:
				pass
			elif msg==1:
				self.goban.display(self.grid,self.markup)
				self.parent.after(250,self.wait_for_display)
			elif msg==2:
				self.goban.display(self.grid,self.markup,True)
				self.parent.after(250,self.wait_for_display)
			else:
				show_info(msg)
				self.goban.display(self.grid,self.markup)
				self.parent.after(0,self.wait_for_display)
		except:
			self.parent.after(250,self.wait_for_display)
		
	
	def redraw(self, event):
		new_size=min(event.width,event.height)
		new_space=new_size/(self.dim+1+1)
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.redraw()



	def save_as_png(self,e=None):
		top=Tk()
		top.withdraw()
		filename = tkFileDialog.asksaveasfilename(parent=top,title=_('Choose a filename'),filetypes = [('PNG', '.png')],initialfile='variation_move'+str(self.move)+'.png')
		top.destroy()
		#self.goban.postscript(file=filename, colormode='color')
		canvas2png(self.goban,filename)
		
class DualView(Frame):
	def __init__(self,parent,filename,goban_size=200):
		Frame.__init__(self,parent)
		
		self.parent=parent
		self.filename=filename
		self.goban_size=goban_size
		
		global Config, goban
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

		self.initialize()
		
		self.current_move=1
		self.display_move(self.current_move)

		self.pressed=0
		self.parent.focus()

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
			for popup in self.all_popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()
		
		elif self.pressed==pressed:
			self.display_move(self.current_move)
			for popup in self.all_popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()

		self.update_idletasks()
		
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
		self.set_status(_("Use mouse wheel or keyboard up/down keys to display the sequence move by move."))
	
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
		#log(move,'/',len(self.current_variation_sequence))
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
		for m in range(0,get_node_number(self.gameroot)+1):
			try:
				one_data={}
				data.append(one_data)
				one_move=get_node(self.gameroot,m)
				
				
				player_color,player_move=one_move.get_move()
				player_move=ij2gtp(player_move)

				#position win rate is the win rate for the position right before the player plays his move
				#so it is the win rate of the best move by the computer for this position
				#because we consider the bot plays perfectly
				
				if player_color in ('w',"W"):
					current_position_win_rate=float(one_move.get('WWR').replace("%",""))
				else:
					current_position_win_rate=float(one_move.get('BWR').replace("%",""))
				
				one_data['position_win_rate']=current_position_win_rate
				one_data['move']=m #move number
				one_data['player_color']=player_color.lower() #which turn it is to play
				
				#delta is the [position win rate of the next move] - [position win rate of the current move]
				#so it allows to compare how the game would evolve from that position:
				# 1/ in the case the computer best move is played (current_position_win_rate)
				# 2/ compared with when the actual game move was played (next_position_win_rate)
				# positive delta means the game evolves better when the actual game move is played
				# negative delta means the game evolves better when the computer move is played
				
				next_move=get_node(self.gameroot,m+1)
				if player_color in ('w',"W"):
					next_position_win_rate=float(next_move.get('WWR').replace("%",""))
				else:
					next_position_win_rate=float(next_move.get('BWR').replace("%",""))

				computer_move=one_move.get('CBM')
				if player_move==computer_move:
					# in case the computer best move is the actual game move then:
					# 1/ normally delta=0
					# 2/ let's update current_position_win_rate using next_position_win_rate because it is a better evaluation
					current_position_win_rate=next_position_win_rate
					one_data['position_win_rate']=next_position_win_rate
								
				delta=next_position_win_rate-current_position_win_rate
				
				one_data['delta']=delta

				
			except Exception, e:
				if str(e) in ("'BWR'","'WWR'"):
					#log("No win rate information for move",m)
					#log(e)
					pass
				elif str(e) in ("'CBM'"):
					#log("No computer best move information for move",m)
					#log(e)
					pass
				#else:
				#	log(e)
				#	data[-1]=None
		return data
	
	def show_graphs(self,event=None):
		new_popup=OpenChart(self,self.data_for_chart)
		new_popup.current_move=self.current_move
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
		board, noneed = sgf_moves.get_setup_and_moves(self.sgf)

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
		
		for a in range(1,min(len(parent),self.maxvariations+1)):
			one_alternative=parent[a]
			ij=one_alternative.get_move()[1]

			displaycolor='black'
			
			if one_alternative.get_move()[0]=='b': c=1
			else: c=2

			if one_alternative.has_property("BWR"):
				black_prob=float(one_alternative.get("BWR")[:-1])
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
				
			if one_alternative.has_property("C"):
				comment=one_alternative.get("C")
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
		new_popup.goban.mesh=self.goban1.mesh
		new_popup.goban.wood=self.goban1.wood
		new_popup.goban.black_stones=self.goban1.black_stones
		new_popup.goban.white_stones=self.goban1.white_stones
		new_popup.goban.no_redraw=[]
		
		new_popup.goban.display(new_popup.grid,new_popup.markup)
		
		self.all_popups.append(new_popup)
		
	def initialize(self):
		
		
		self.realgamedeepness=5
		try:
			self.realgamedeepness=int(Config.get("Review", "RealGameSequenceDeepness"))
		except:
			Config.set("Review", "RealGameSequenceDeepness",self.realgamedeepness)
			Config.write(open(config_file,"w"))
		
		self.maxvariations=10
		try:
			self.maxvariations=int(Config.get("Review", "MaxVariations"))
		except:
			Config.set("Review", "MaxVariations",self.maxvariations)
			Config.write(open(config_file,"w"))
		
		self.sgf = open_sgf(self.filename)

		self.dim=self.sgf.get_size()
		self.komi=self.sgf.get_komi()
		
		log("boardsize:",self.dim)
		#goban.dim=size
		
		#goban.prepare_mesh()
		self.gameroot=self.sgf.get_root()
		

		self.parent.title('GoReviewPartner')
		self.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		self.all_popups=[]
		
		bg=self.cget("background")
		#self.configure(background=bg)
		
		Label(self,text='   ',background=bg).grid(column=0,row=0)
		
		buttons_bar=Frame(self,background=bg)
		buttons_bar.grid(column=1,row=1,columnspan=3)
		
		first_move_button=Button(buttons_bar, text='|<< ',command=self.first_move)
		first_move_button.grid(column=8,row=1)
		
		prev_10_moves_button=Button(buttons_bar, text=' << ',command=self.prev_10_move)
		prev_10_moves_button.grid(column=9,row=1)
		
		prev_button=Button(buttons_bar, text=' <  ',command=self.prev_move)
		prev_button.grid(column=10,row=1)
		
		Label(buttons_bar,text='          ',background=bg).grid(column=19,row=1)
		
		self.move_number=Label(buttons_bar,text='   ',background=bg)
		self.move_number.grid(column=20,row=1)
		

		
		Label(buttons_bar,text='          ',background=bg).grid(column=29,row=1)
		
		next_button=Button(buttons_bar, text='  > ',command=self.next_move)
		next_button.grid(column=30,row=1)
		
		next_10_moves_button=Button(buttons_bar, text=' >> ',command=self.next_10_move)
		next_10_moves_button.grid(column=31,row=1)
		
		final_move_button=Button(buttons_bar, text=' >>|',command=self.final_move)
		final_move_button.grid(column=32,row=1)
		
		buttons_bar2=Frame(self,background=bg)
		buttons_bar2.grid(column=1,row=2,sticky=W)
		
		open_button=Button(buttons_bar2, text=_('Open position'),command=self.open_move)
		open_button.grid(column=1,row=1)
		
		self.territory_button=Button(buttons_bar2, text=_('Show territories'))
		self.territory_button.grid(column=2,row=1)
		self.territory_button.bind('<Button-1>', self.show_territories)
		self.territory_button.bind('<ButtonRelease-1>', self.hide_territories)
		
		self.data_for_chart=self.prepare_data_for_chart()
		for data in self.data_for_chart:
			if data<>None:
				self.charts_button=Button(self, text=_('Graphs'))
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
		

		
		self.goban1.grid(column=1,row=row,sticky=W+E+N+S)
		Label(self, text='            ',background=bg).grid(column=2,row=row)
		#self.goban2 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2 = Goban(self.dim, master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2.mesh=self.goban1.mesh
		self.goban2.wood=self.goban1.wood
		self.goban2.black_stones=self.goban1.black_stones
		self.goban2.white_stones=self.goban1.white_stones
		self.goban2.grid(column=3,row=row,sticky=W+E+N+S)
		
		self.grid_rowconfigure(row, weight=1)
		self.grid_columnconfigure(1, weight=1)
		self.grid_columnconfigure(3, weight=1)
		
		self.goban1.space=self.goban_size/(self.dim+1+1)
		self.goban2.space=self.goban_size/(self.dim+1+1)
		
		self.parent.bind('<Control-q>', self.save_left_as_png)
		self.parent.bind('<Control-w>', self.save_right_as_png)
		
		Label(self,text='   ',background=bg).grid(column=4,row=row+1)
		
		police = tkFont.nametofont("TkFixedFont")
		lpix = police.measure("a")
		self.lpix=lpix
		self.comment_box1=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box1.grid(column=1,row=row+4)
		
		self.comment_box2=ScrolledText(self,font=police,wrap="word",width=int(self.goban_size/lpix-2),height=5,foreground='black')
		self.comment_box2.grid(column=3,row=row+4)
		
		self.status_bar=Label(self,text='',background=bg)
		self.status_bar.grid(column=1,row=row+5,sticky=W,columnspan=3)
		
		#Label(self,text='   ',background=bg).grid(column=4,row=row+6)
		
		goban.show_variation=self.show_variation
		
		self.goban1.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		self.goban2.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+W> to save the goban as an image.")))
		
		first_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to first move.")))
		prev_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go back 10 moves.")))
		prev_button.bind("<Enter>",lambda e: self.set_status(_("Go back one move. Shortcut: keyboard left key.")))
		open_button.bind("<Enter>",lambda e: self.set_status(_("Open this position onto a third goban to play out variations.")))
		next_button.bind("<Enter>",lambda e: self.set_status(_("Go forward one move. Shortcut: keyboard right key.")))
		next_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go forward 10 moves.")))
		final_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to final move.")))
		self.territory_button.bind("<Enter>",lambda e: self.set_status(_("Keep pressed to show territories.")))
		for button in [first_move_button,prev_10_moves_button,prev_button,open_button,next_button,next_10_moves_button,final_move_button,self.territory_button,self.goban1,self.goban2]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		self.goban1.bind("<Configure>",self.redraw)
	
	def redraw(self, event):
		new_size=min(event.width,event.height)
		new_space=new_size/(self.dim+1+1)
		self.goban1.space=new_space
		self.goban2.space=new_space
		
		new_anchor_x=(event.width-new_size)/2
		self.goban1.anchor_x=new_anchor_x
		self.goban2.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2
		self.goban1.anchor_y=new_anchor_y
		self.goban2.anchor_y=new_anchor_y
		
		self.goban1.redraw()
		self.goban2.redraw()
		
		if sys.platform!="darwin":
			#https://github.com/pnprog/goreviewpartner/issues/7
			self.comment_box1.config(width=int(event.width/self.lpix-2))
			self.comment_box2.config(width=int(event.width/self.lpix-2))

	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")

	def save_left_as_png(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title=_('Choose a filename'),filetypes = [('PNG', '.png')],initialfile='move'+str(self.current_move)+'.png')
		canvas2png(self.goban1,filename)

		
	def save_right_as_png(self,e=None):
		filename = tkFileDialog.asksaveasfilename(parent=self.parent,title=_('Choose a filename'),filetypes = [('PNG', '.png')],initialfile='move'+str(self.current_move)+'.png')
		canvas2png(self.goban2,filename)
	
def canvas2png(goban,filename):
	top = goban.winfo_rooty()
	left = goban.winfo_rootx()
	width = goban.winfo_width()
	height = goban.winfo_height()
	monitor = {'top': top, 'left': left, 'width': width, 'height': height}
	sct_img = mss.mss().grab(monitor)
	mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)

from gomill import sgf, sgf_moves
import goban
#goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

if __name__ == "__main__":
	
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	
	if len(sys.argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title=_('Select a file'),filetypes = [('SGF file reviewed', '.rsgf')])
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
		Config.write(open(config_file,"w"))
	
	screen_width = top.winfo_screenwidth()
	screen_height = top.winfo_screenheight()
	
	width=int(display_factor*screen_width)
	height=int(display_factor*screen_height)
	
	DualView(top,filename,min(width,height)).pack(fill=BOTH,expand=1)
	top.mainloop()

	
	
