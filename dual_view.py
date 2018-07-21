# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from Tkinter import *
from ttk import Notebook
from Tkconstants import *
from ScrolledText import *
import tkFont
import sys,time
from functools import partial
from toolbox import *
from toolbox import _
from tabbed import *
import os
import threading, Queue
from goban import *
from copy import deepcopy as copy

bg='#C0C0C0'

class OpenChart(Toplevel):
	def __init__(self,parent,data,nb_moves,current_move=0):
		Toplevel.__init__(self,parent)
		
		self.parent=parent
		self.nb_moves=nb_moves
		self.data=data
		self.current_move=current_move

		popup_width=self.parent.winfo_width()
		popup_height=self.parent.winfo_height()/2+10
		self.geometry(str(popup_width)+'x'+str(popup_height))
		
		self.last_graph=grp_config.get("Review","LastGraph")
		self.initialize()

	def close(self):
		log("closing popup")
		self.destroy()
		self.parent.remove_popup(self)
		log("done")

	def initialize(self):
		for widget in self.pack_slaves():
			widget.destroy()
		
		popup=self
		bg=popup.cget("background")
		
		top_frame=Frame(popup)
		top_frame.pack()
		
		self.graph_mode=StringVar()
		available_graphs=[]

		for data in self.data:
			if data:
				if "position_win_rate" in data:
					#self.graph_mode.set(_("Win rate")) # initialize
					available_graphs.append(_("Win rate"))
					break
		
		for data in self.data:
			if data:
				if "winrate_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("Black win rate delta"))
						break
		for data in self.data:
			if data:
				if "winrate_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("White win rate delta"))
						break
		
		for data in self.data:
			if data:
				if "value_network_win_rate" in data:
					available_graphs.append(_("Value Network win rate"))
					break
		
		for data in self.data:
			if data:
				if "vnwr_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("Black Value Network win rate delta"))
						break

		for data in self.data:
			if data:
				if "vnwr_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("White Value Network win rate delta"))
						break
		
		for data in self.data:
			if data:
				if "monte_carlo_win_rate" in data:
					available_graphs.append(_("Monte Carlo win rate"))
					break
		
		for data in self.data:
			if data:
				if "mcwr_delta" in data:
					if data["player_color"]=="w":
						available_graphs.append(_("Black Monte Carlo win rate delta"))
						break

		for data in self.data:
			if data:
				if "mcwr_delta" in data:
					if data["player_color"]=="b":
						available_graphs.append(_("White Monte Carlo win rate delta"))
						break
		
		for data in self.data:
			if data:
				if ("score_estimation" in data) or ("upper_bound_score" in data) or ("lower_bound_score" in data):
					#self.graph_mode.set(_("Score estimation")) # initialize
					available_graphs.append(_("Score estimation"))
					break
		
		self.graph_selection=apply(OptionMenu,(top_frame,self.graph_mode)+tuple(available_graphs))
		self.graph_selection.pack(side=LEFT, padx=5)
		if self.last_graph in [mode for mode in available_graphs]:
			self.graph_mode.set(self.last_graph)
		else:
			self.last_graph=available_graphs[0]
			self.graph_mode.set(self.last_graph)
			
		self.graph_mode.trace("w", lambda a,b,c: self.change_graph())
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
		self.bind('<Control-q>', self.save_as_png)
		
		self.protocol("WM_DELETE_WINDOW", self.close)
		popup.focus()
	
	def set_status(self,event=None,msg=''):
		self.status_bar.config(text=msg)
	
	def clear_status(self,event=None):
		self.status_bar.config(text=_("<Ctrl+Q> to save the graph as an image."))
	
	def goto_move(self,event=None,move=None):
		if move:
			log("goto move",move)
			self.parent.parent.lift()			
			self.parent.goto_move(move_number=move)
		
	
	def display_vertical_winrate_graduation(self,border,height,width):
		#drawing vertical graduation
		graduations=[x*10 for x in range(10+1)]
		y0=height+1000
		x0=border/2
		x1=width-border/2
		for g in graduations:
			y1=height-border-g*(height-2*border)/100.
			
			if y0-y1>=border:
				self.chart.create_text(x0,y1, text=str(g)+"%",fill='black',font=self.font)
				self.chart.create_text(x1,y1, text=str(g)+"%",fill='black',font=self.font)
				#self.chart.create_line(x0, y1, x1, y1, fill='black')
				y0=y1
	
	def display_vertical_score_graduation(self,border,height,width,maximum):
		#drawing vertical graduation
		graduations=[x*2 for x in range(0,int((maximum+2)/2.))]
		x0=border/2
		middle=height-border-(height-2*border)/2
		#placing 0 first
		y0=middle
		self.chart.create_text(x0,y0, text="0",fill='black',font=self.font)
		self.chart.create_line(border-3, y0, border+3, y0, fill='black')
		for g in graduations:
			y1=middle+g/2*(height-2*border)/maximum
			y2=middle-g/2*(height-2*border)/maximum
			if y1-y0>=border/2:
				self.chart.create_text(x0,y1, text=str(-g),fill='black',font=self.font)
				self.chart.create_text(x0,y2, text=str(g),fill='black',font=self.font)
				self.chart.create_line(border-3, y1, border+3, y1, fill='black')
				self.chart.create_line(width-border-3, y1, width-border+3, y1, fill='black')
				self.chart.create_line(border-3, y2, border+3, y2, fill='black')
				self.chart.create_line(width-border-3, y2, width-border+3, y2, fill='black')
				y0=y1
	
	def change_graph(self,event=None):
		self.last_graph=_(self.graph_mode.get())
		grp_config.set("Review","LastGraph",self.last_graph)
		self.display()
		
	def display(self,event=None):
		if event:
			width=event.width
			height=event.height
			self.width=width
			self.height=height
			
			#let's estimate the ratio fontsize/pixel
			offset=-1000000
			idt=self.chart.create_text(offset,offset, text="0",font=("TkFixedFont", 1000))
			x1,y1,x2,y2=self.chart.bbox(idt) 
			ratio=max(x2-x1,y2-y1)/1000.
			#let's measure one letter's size from a tkinter widget
			police = tkFont.nametofont("TkFixedFont")
			self.lpix = 2*police.measure("0")
			#let's adjust the fontsize to match the letter's size
			fontsize=int(round(self.lpix/ratio))
			self.border=4.5*fontsize
			self.font=("TkFixedFont",str(fontsize))
			
			
		else:
			width=self.width
			height=self.height
		
		border=self.border
		lpix=self.lpix
		space=1.0*(width-2*border)/(self.nb_moves+1)
		
		for item in self.chart.find_all():
			self.chart.delete(item)
		
		self.chart.create_line(0, 0, width, 0, fill='#000000',width=4)
		self.chart.create_line(0, height, width, height, fill='#000000',width=4)
		self.chart.create_line(0, 0, 0, height, fill='#000000',width=4)
		self.chart.create_line(width, 0, width, height, fill='#000000',width=4)
		
		y00=height-border
		x0=border+(self.current_move-1)*space
		x1=x0+space
		y1=border-5
		yellow=grp_config.get("Review","YellowBar")
		self.chart.create_rectangle(x0, y00, x1, y1, fill=yellow,outline=yellow)#yellow_bar
		
		mode=self.last_graph

		if mode in (_("Black win rate delta"),_("White win rate delta")):
			moves=self.display_winrate_delta(border,height,width)
		elif mode==_("Win rate"):
			moves=self.display_winrate_graph(border,height,width,lpix)
		elif mode==_("Score estimation"):
			moves=self.display_score_graph(border,height,width,lpix)
		elif mode==_("Monte Carlo win rate"):
			moves=self.display_monte_carlo_winrate_graph(border,height,width,lpix)
		elif mode==_("Value Network win rate"):
			moves=self.display_value_network_winrate_graph(border,height,width,lpix)
		elif mode in (_("Black Monte Carlo win rate delta"),_("White Monte Carlo win rate delta")):
			moves=self.display_monte_carlo_delta(border,height,width)
		elif mode in (_("Black Value Network win rate delta"),_("White Value Network win rate delta")):
			moves=self.display_value_network_delta(border,height,width)
		
		self.display_horizontal_graduation(moves,height,width,border,lpix)
		self.display_axis(height,width,border)

	def display_value_network_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()==_("Black Value Network win rate delta"):
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("vnwr_delta" in one_data):
				position_win_rate=one_data["value_network_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["vnwr_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: win rate of Black's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: win rate of White's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta!=0:
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
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_monte_carlo_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()==_("Black Monte Carlo win rate delta"):
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("mcwr_delta" in one_data):
				position_win_rate=one_data["monte_carlo_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["mcwr_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: win rate of Black's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: win rate of White's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta!=0:
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
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_winrate_delta(self,border,height,width):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		if self.graph_mode.get()==_("Black win rate delta"):
			player_color='b'
		else:
			player_color='w'

		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if (one_data["player_color"]==player_color) and ("winrate_delta" in one_data):
				position_win_rate=one_data["position_win_rate"]
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space*2
				
				y0=height-border
				y1=height-border-position_win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				delta=one_data["winrate_delta"]
				
				if player_color.lower()=="b":
					msg=_("Move %i: win rate of Black's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				else:
					msg=_("Move %i: win rate of White's move: %s; win rate of computer move: %s")%(move,str(position_win_rate+delta)+"%",str(position_win_rate)+"%")
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				if delta!=0:
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
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_value_network_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=self.font)
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "value_network_win_rate" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				
				win_rate=one_data["value_network_win_rate"]
				if one_data["player_color"]=="w":
					win_rate=100.-win_rate
					color=_("White")
				else:
					color=_("Black")
				player_win_rate=float(int(win_rate*100)/100.)
				y0=height-border
				y1=height-border-win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
				msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(win_rate)+"%/"+str(100-player_win_rate)+"%"
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves
		
	def display_monte_carlo_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=self.font)
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "monte_carlo_win_rate" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				
				win_rate=one_data["monte_carlo_win_rate"]
				if one_data["player_color"]=="w":
					win_rate=100.-win_rate
					color=_("White")
				else:
					color=_("Black")
				player_win_rate=float(int(win_rate*100)/100.)
				y0=height-border
				y1=height-border-win_rate*(height-2*border)/100.
				
				grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
				
				#msg="Move "+str(move)+" ("+color+"), black/white win rate: "+str(player_win_rate)+"%/"+str(100-player_win_rate)+"%"
				msg=(_("Move %i (%s), black/white win rate: ")%(move,color))+str(win_rate)+"%/"+str(100-player_win_rate)+"%"
				
				self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
				
				self.chart.create_line(x0, y1, x1, y1, fill='#0000ff',width=2)
				self.chart.create_line(x0, y1, x00, y00, fill='#0000ff')
				x00=x1
				y00=y1
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves


	def display_winrate_graph(self,border,height,width,lpix):
		moves=[]
		space=1.0*(width-2*border)/(self.nb_moves+1)
		
		self.chart.create_text(len(_("Black win rate"))*lpix/2,border/2, text=_("Black win rate"),fill='black',font=self.font)
		x00=border
		y00=height-border-(height-2*border)/2.
		for one_data in self.data:
			if "position_win_rate" in one_data:
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
		#drawing vertical graduation
		self.display_vertical_winrate_graduation(border,height,width)
		return moves

	def display_score_graph(self,border,height,width,lpix):
		self.chart.create_text(border+len(_("Win for Black"))*lpix/2,border+lpix, text=_("Win for Black"),fill='black',font=self.font)
		self.chart.create_text(border+len(_("Win for White"))*lpix/2,height-border-lpix, text=_("Win for White"),fill='black',font=self.font)
		moves=[]
		#checking graph limits
		maximum=-1000
		for one_data in self.data:
			if "score_estimation" in one_data:
				maximum=max(maximum,max([abs(x) for x in (one_data["upper_bound_score"],one_data["lower_bound_score"],one_data["score_estimation"])]))
		maximum+=5
		space=1.0*(width-2*border)/(self.nb_moves+1)
		middle=height-border-(height-2*border)/2
		x00=border
		y00=middle
		for one_data in self.data:
			if "score_estimation" in one_data:
				move=one_data["move"]
				moves.append(move)
				x0=border+(move-1)*space
				x1=x0+space
				estimated_score=one_data["score_estimation"]
				upper_bound_score=one_data["upper_bound_score"]
				lower_bound_score=one_data["lower_bound_score"]

				y0=middle-lower_bound_score*(height-2*border)/2./maximum
				y1=middle-upper_bound_score*(height-2*border)/2./maximum
				y2=middle-estimated_score*(height-2*border)/2./maximum
				y3=min(middle,y0,y1,y2)
				y4=max(middle,y0,y1,y2)
				
				white_bar=self.chart.create_rectangle(x0, y3, x1, y4, fill='#eeeeee',outline='')


				self.chart.create_line(x0, y2, x1, y2, fill='#0000ff',width=2)
				self.chart.create_line(x0, y2, x00, y00, fill='#0000ff')
				x00=x1
				y00=y2					
				
				if one_data["player_color"]=="w":
					color=_("White")
				else:
					color=_("Black")
				
				if estimated_score>=0:
					msg=(_("Move %i (%s), estimated score: ")%(move,color))
					msg+="B+"+str(estimated_score)
					if (lower_bound_score!=upper_bound_score):
						msg+=" [B%+.1f, B%+.1f]"%(lower_bound_score,upper_bound_score)
				else:
					msg=(_("Move %i (%s), estimated score: ")%(move,color))
					msg+="W+"+str(abs(estimated_score))
					if (lower_bound_score!=upper_bound_score):
						msg+=" [W%+.1f, W%+.1f]"%(-lower_bound_score,-upper_bound_score)
				
				self.chart.tag_bind(white_bar, "<Enter>", partial(self.set_status,msg=msg))
				self.chart.tag_bind(white_bar, "<Leave>", self.clear_status)
				self.chart.tag_bind(white_bar, "<Button-1>",partial(self.goto_move,move=move))
				if y0!=y1:
					grey_bar=self.chart.create_rectangle(x0, y0, x1, y1, fill='#aaaaaa',outline='grey')
					self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
					self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
					self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
					self.chart.tag_bind(grey_bar, "<Enter>", partial(self.set_status,msg=msg))
					self.chart.tag_bind(grey_bar, "<Leave>", self.clear_status)
					self.chart.tag_bind(grey_bar, "<Button-1>",partial(self.goto_move,move=move))
			
		self.display_vertical_score_graduation(border,height,width,maximum)
		return moves

	def display_axis(self,height,width,border):
		#drawing axis
		x0=border
		y0=height-border
		y1=border
		self.chart.create_line(x0, y0, x0, y1, fill='black')
		x1=width-border
		self.chart.create_line(x1, y0, x1, y1, fill='black')
		self.chart.create_line(x0, y0, x1, y0, fill='black')
		self.chart.create_line(x0, (y0+y1)/2, x1, (y0+y1)/2, fill='black')
	
	def display_horizontal_graduation(self,moves,height,width,border,lpix):
		#drawing horizontal graduation
		graduations=[x for x in moves]
		x0=-1000
		y0=height-border/2
		y1=height-border
		for g in graduations:
			x1=border+(g-0.5)*(width-2*border)/self.nb_moves*1.0
			
			if x1-x0>=border/1.5:
				self.chart.create_text(x1,y0, text=str(g),fill='black',font=self.font)
				self.chart.create_line(x1, y1, x1, (y0+y1)/2, fill='black')
				x0=x1
		
		
	def save_as_png(self,event=None):
		filename=save_png_file(filename=self.graph_mode.get()+' graph.png',parent=self)
		canvas2png(self.chart,filename)


class OpenMove(Toplevel):
	def __init__(self,parent,move,dim,sgf):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
		
		display_factor=grp_config.getfloat("Review", "OpenGobanRatio")
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		self.goban_size=min(width,height)

		self.available_bots=[]
		for bot in get_available("ReviewBot"):
			self.available_bots.append(bot)
		self.initialize()
		
	def lock(self):	
		self.undo_button.config(state='disabled')
		self.menu.config(state='disabled')
		self.play_button.config(state='disabled')
		self.white_button.config(state='disabled')
		self.black_button.config(state='disabled')
		self.evaluation_button.config(state='disabled')
		
		if (not self.white_autoplay) or (not self.black_autoplay):
			self.selfplay_button.config(state='disabled')

		self.goban.bind("<Button-1>",self.do_nothing)
		self.goban.bind("<Button-2>",self.do_nothing)
		self.locked=True

	def do_nothing(self,event=None):
		pass

	def unlock(self):
		self.undo_button.config(state='normal')
		self.menu.config(state='normal')
		self.play_button.config(state='normal')
		self.white_button.config(state='normal')
		self.black_button.config(state='normal')
		self.selfplay_button.config(state='normal')
		self.evaluation_button.config(state='normal')
		self.goban.bind("<Button-1>",self.click)
		self.goban.bind("<Button-2>",self.undo)
		self.locked=False
		
	def close(self):
		log("closing popup")
		self.display_queue.put(0)
		self.destroy()
		
		for bot in self.bots:
			bot.close()

		self.parent.remove_popup(self)
		log("done")
	
	def undo(self,event=None):
		log("UNDO")
		if self.undo_button.cget("state")=='disabled':
			return
		if len(self.history)<1:
			return
		elif len(self.history)==1:
			self.undo_button.config(state='disabled')
		
		self.grid,self.markup=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		
		for bot in self.bots:
			bot.undo()
		

	def click_button(self,bot):
		dim=self.dim
		self.display_queue.put(3)
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
			self.display_queue.put((i,j))
			
			self.grid[i][j]=color
			self.markup=[["" for r in range(dim)] for c in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			bot.undo()
			if color==1:
				self.display_queue.put(bot.name+" ("+_("Black")+"): "+move.lower())
			else:
				self.display_queue.put(bot.name+" ("+_("White")+"): "+move.lower())
		
		if self.white_autoplay and self.black_autoplay:
			if move.lower() not in ["pass","resign"]:
				log("SELF PLAY")
				self.display_queue.put(2)
				one_thread=threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],))
				self.after(0,one_thread.start)
				return
			else:
				log("End of SELF PLAY")
				self.click_selfplay()
				self.display_queue.put(4)
				self.display_queue.put(1)
				return
		else:
			self.display_queue.put(4)
			self.display_queue.put(1)
			return
		
	def shine(self,event):
		dim=self.dim
		i,j=self.goban.xy2ij(event.x,event.y)
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			color=self.goban.grid[i][j]
			if color==1:
				self.goban.black_stones[i][j].shine(100)
			elif color==2:
				self.goban.white_stones[i][j].shine(100)
			else:
				self.goban.intersections[i][j].shine(100)
		
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
				for bot in self.bots:
					if bot.place(ij2gtp((i,j)),color)==False:
						del self.menu_bots[bot.name]
						self.menu.pack_forget()
						if len(self.menu_bots):
							self.selected_bot.set(self.menu_bots.keys()[0])
							self.selected_bot=StringVar()
							#self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
							self.menu=apply(OptionMenu, (self.menu_wrapper, self.selected_bot) + tuple(self.menu_bots.keys()))
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
					
				self.markup=[["" for r in range(dim)] for c in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				if color==1:
					self.goban.black_stones[i][j].shine()
				else:
					self.goban.white_stones[i][j].shine()
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
	
	def click_evaluation(self):
		log("Asking",self.selected_bot.get(),"for quick estimation")
		self.display_queue.put(3)
		self.display_queue.put(2)
		threading.Thread(target=self.evaluation,args=(self.menu_bots[self.selected_bot.get()],)).start()
	
	def evaluation(self,bot):
		color=self.next_color
		result=bot.quick_evaluation(color)
		self.display_queue.put(4)
		if color==1:
			self.display_queue.put(result)
		else:
			self.display_queue.put(result)
		
	def initialize(self):
		gameroot=self.sgf.get_root()
		popup=self
		
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
		value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
		for available_bot in self.available_bots:
			row+=2
			one_bot=available_bot['openmove'](self.sgf,available_bot['profile'])
			one_bot.start()
			self.bots.append(one_bot)
			if one_bot.okbot:
				self.menu_bots[one_bot.name+value[available_bot['profile']]]=one_bot

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
			
			#self.menu=OptionMenu(self.menu_wrapper,self.selected_bot,*tuple(self.menu_bots.keys()))
			self.menu=apply(OptionMenu, (self.menu_wrapper, self.selected_bot) + tuple(self.menu_bots.keys()))
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
			self.selfplay_button.bind("<Enter>",lambda e: self.set_status(_("Let the bot take both sides and play against itself.")))
			self.selfplay_button.bind("<Leave>",lambda e: self.clear_status())
		
			row+=1
			Label(panel,text=" ").grid(column=0,row=row,sticky=E+W)
			row+=1
			self.evaluation_button=Button(panel, text=_('Quick evaluation'),command=self.click_evaluation)
			self.evaluation_button.grid(column=0,row=row,sticky=E+W)
			self.evaluation_button.bind("<Enter>",lambda e: self.set_status(_("Ask the bot for a quick evaluation")))
			self.evaluation_button.bind("<Leave>",lambda e: self.clear_status())
			
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		goban3 = Goban(dim,self.goban_size,master=popup,bg=bg,bd=0, borderwidth=0)
		goban3.space=self.goban_size/(dim+1+1+1)
		goban3.grid(column=2,row=1,sticky=N+S+E+W)
		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		
		self.bind('<Control-q>', self.save_as_png)
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
		
		
		board, unused = sgf_moves.get_setup_and_moves(self.sgf)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				color=1
			else:
				color=2
			place(grid3,row,col,color)

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
				log("(1)skipping because ij==None",ij)
				continue

			i,j=ij
			place(grid3,i,j,color)
		
		if m>0:
			markup3[i][j]=0
		
		try:
			if guess_color_to_play(gameroot,move)=="w":
				self.next_color=2
			else:
				self.next_color=1
		except:
			log("error when trying to figure out next color to play, so black is selected")
			self.next_color=1
		
		#goban3.display(grid3,markup3)
		
		self.goban=goban3
		self.grid=grid3
		self.markup=markup3

		self.undo_button=undo_button
		
		popup.protocol("WM_DELETE_WINDOW", self.close)
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",self.shine)
		#goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]
		self.update_idletasks()
		self.goban.reset()
		self.goban.bind("<Configure>",self.redraw)
		popup.focus()
		
		self.display_queue=Queue.Queue(2)
		self.parent.after(100,self.wait_for_display)
	
	def wait_for_display(self):
		try:
			msg=self.display_queue.get(False)
			if msg==0:
				pass
			elif msg==1:
				self.goban.display(self.grid,self.markup)
				self.parent.after(100,self.wait_for_display)
			elif msg==2:
				self.goban.display(self.grid,self.markup,True)
				self.parent.after(100,self.wait_for_display)
			elif msg==3:
				self.lock()
				self.wait_for_display()
			elif msg==4:
				self.unlock()
				self.wait_for_display()
			elif type(msg)==type((1,1)):
				i,j=msg
				if self.grid[i][j]==1:
					self.goban.black_stones[i][j].shine()
				else:
					self.goban.white_stones[i][j].shine()
				self.wait_for_display()
			else:
				show_info(msg,self)
				self.goban.display(self.grid,self.markup)
				self.wait_for_display()
		except:
			self.parent.after(250,self.wait_for_display)
	
	
	def redraw(self, event, redrawing=None):		
		if not redrawing:
			redrawing=time.time()
			self.redrawing=redrawing
			self.after(100,lambda: self.redraw(event,redrawing))
			return
		if redrawing<self.redrawing:
			return
		
		new_size=min(event.width,event.height)
		new_size=new_size-new_size%max(int((0.1*self.dim*self.goban.space)),1)
		
		new_space=int(new_size/(self.dim+1+1+1))
		

		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		ratio=1.0*new_size/min(screen_width,screen_height)
		grp_config.set("Review", "OpenGobanRatio",ratio)
			
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.reset()

	def save_as_png(self,event=None):
		filename = save_png_file(parent=self,filename='variation_move'+str(self.move)+'.png')
		canvas2png(self.goban,filename)

class TableWidget:
	def __init__(self,widget,parent,gameroot,current_move,grid,markup):
		log("creating table widget",current_move)
		
		self.parent=parent
		self.widget=widget
		self.gameroot=gameroot

		self.maxvariations=grp_config.getint("Review", "MaxVariations")
		self.my_labels={}
		self.dframe=None
		self.table_frame=None
		self.display_move(current_move,grid,markup)
		
		
	def get_label(self,name,container):
		if name in self.my_labels:
			return self.my_labels[name]
		if type(name)==type("abc"):
			if name=="node comments":
				new_label=Label(container,justify=LEFT)
				new_label.grid(row=1,column=1,columnspan=100,sticky=W+N)
				self.my_labels[name]=new_label
				return new_label
		else:
			row,column=name
			new_label=Label(container)
			new_label.grid(row=row,column=column,sticky=W+E)
			self.my_labels[name]=new_label
			return new_label
		
		
	def display_move(self,current_move,grid,markup):
		new_popup=self.widget
		
		for widget in self.my_labels.values():
			widget.config(text="")
			widget.unbind("<Enter>")
		
		self.current_move=current_move
		
		comments=get_position_short_comments(self.current_move,self.gameroot)
		one_label=self.get_label("node comments",self.widget) #get or create that label widget
		one_label.config(text=comments)
		
		columns_header=["MOVE",'nothing here',"WR","MCWR","VNWR","PNV","PO","EV","RAVE","SCORE"]
		columns_header_status_msg=[_("Move"),_("Move"),_("Win rate"),_("Monte Carlo win rate"),_("Value Network win rate"),_("Policy Network value"),_("Playouts"),_("Evaluation"),_("RAVE"),_("Score Estimation")]
		columns_sgf_properties=["nothing here","nothing here","BWWR","MCWR","VNWR","PNV","PLYO","EVAL","RAVE","ES"]
		parent=get_node(self.gameroot,self.current_move-1)
		nb_variations=min(len(parent),self.maxvariations+1)
		log(nb_variations,"variations")
		
		columns=[[None for r in range(nb_variations+1)] for c in range(len(columns_header))]
		color=guess_color_to_play(self.gameroot,current_move)
		for a in range(1,min(len(parent),self.maxvariations+1)):
			one_alternative=parent[a]
			c=0
			
			for key in columns_sgf_properties:
				if node_has(one_alternative,key):
					value=node_get(one_alternative,key)
					if "%/" in value:
						if color=="b":
							value=float(value.split("%/")[0])
							value=round(value,2)
							value=str(value)+"%"
						else:
							value=float(value.split("/")[1][:-1])
							value=round(value,2)
							value=str(value)+"%"
					columns[c][a]=value
				c+=1
			columns[0][a]="ABCDEFGHIJKLMNOPQRSTUVWXYZ"[a-1]
			columns[1][a]=ij2gtp(one_alternative.get_move()[1])
		
		try:
			columns[0][0]="A"
			columns[1][0]=ij2gtp(parent[0].get_move()[1])
			one_alternative=parent[0][1]
			c=0
			for key in columns_sgf_properties:
				if node_has(one_alternative,key):
					value=node_get(one_alternative,key)
					if "%/" in value:
						if parent[0].get_move()[0].lower()=="b":
							value=float(value.split("%/")[0])
							value=round(value,2)
							value=str(value)+"%"
						else:
							value=float(value.split("/")[1][:-1])
							value=round(value,2)
							value=str(value)+"%"
					columns[c][0]=value
				c+=1
		except:
			pass
		c=0
		for column in columns:
			empty=True
			for row in column:
				if row!=None:
					empty=False
					break
			if empty:
				columns_header[c]=None
			c+=1
		
		row=2
		if self.dframe==None:
			self.dframe=Frame(new_popup)
			self.dframe.grid(row=row,column=1,columnspan=100,sticky=W+N)

		c=0
		deltas_strings = ["WR","BWWR","MC", "MCWR","VN","VNWR"]
		deltas_strings_status_msg=[_("Win Rate"),"",_("Monte Carlo win rate"), "",_("Value Network win rate"),""]
		for i in range(0,len(deltas_strings),2):
			idx = columns_sgf_properties.index(deltas_strings[i+1])
			if columns[1][0]==columns[1][1]:
				delta = 0
				dtext = "+0pp"
				status_msg=""
			elif( columns_header[idx] and columns[idx][0] and columns[idx][1] ):
				delta = float(columns[idx][0].split("%")[0]) - float(columns[idx][1].split("%")[0])
				dtext = "%+.2fpp"%delta
				if delta > 0:
					status_msg="The computer believes the actual move is %.2fpp better than it's best move."%delta
				else:
					status_msg="The computer believes it's own move win rate would be %.2fpp higher."%(-delta)
			else:
				delta = None
				dtext = "NA"
				status_msg=_("Not available")
			one_label=self.get_label((0,c),self.dframe)
			one_label.config(text=deltas_strings[i]+":")
			one_label.bind("<Enter>",partial(self.set_status,msg=deltas_strings_status_msg[i]))
			one_label.bind("<Leave>",lambda e: self.clear_status())
			another_label=self.get_label((0,c+1),self.dframe)
			another_label.config(text=dtext+" ",fg="black" if delta is None or delta == 0 else "red" if delta < 0 else "darkgreen")
			another_label.bind("<Enter>",partial(self.set_status,msg=status_msg))
			another_label.bind("<Leave>",lambda e: self.clear_status())
			c = c + 2
		
		if not self.table_frame:
			row=10
			self.table_frame=LabelFrame(new_popup)
			self.table_frame.grid(row=row,column=10,sticky=W+N,pady=10)
		row=10
		c=0
		for header,status_msg in zip(columns_header,columns_header_status_msg):
			if header:
				if c==0:
					one_label=self.get_label((row,10+c),self.table_frame)
					one_label.config(text=header,relief=RIDGE,bd=2,width=6)
					one_label.grid(columnspan=2)
				elif c==1:
					pass
				else:
					one_label=self.get_label((row,10+c),self.table_frame)
					one_label.config(text=header,relief=RIDGE,bd=2,width=7)
				one_label.bind("<Enter>",partial(self.set_status,msg=status_msg))
				one_label.bind("<Leave>",lambda e: self.clear_status())
			c+=1
		row+=2
		
		for r in range(nb_variations):
			for c in range(len(columns)):
				if columns_header[c]:
					one_label=self.get_label((row+r,10+c),self.table_frame)
					one_label.config(text=columns[c][r],relief=RIDGE)
					
					if r>0:
						i,j=gtp2ij(columns[1][r])
						
						one_label.bind("<Enter>",partial(self.show_variation,one_label=one_label,i=i,j=j))
						"""
						if self.parent.right_notebook.raised()=="bot":
							grid, markup=self.parent.right_bot_goban.grid, self.parent.right_bot_goban.markup
							one_label.bind("<Enter>",partial(self.parent.show_variation,goban=self.parent.right_bot_goban,grid=grid,markup=markup,i=i,j=j))
							one_label.bind("<Leave>", lambda e: self.parent.leave_variation(self.parent.right_bot_goban,grid,markup))
						elif self.parent.left_notebook.raised()=="bot":
							grid, markup=self.parent.left_bot_goban.grid, self.parent.left_bot_goban.markup
							one_label.bind("<Enter>",partial(self.parent.show_variation,goban=self.parent.left_bot_goban,grid=grid,markup=markup,i=i,j=j))
							one_label.bind("<Leave>", lambda e: self.parent.leave_variation(self.parent.left_bot_goban,grid,markup))
						"""
					else:
						one_label.config(bd=2)
					
					if c==0:
						one_label.config(width=2)
					elif c==1:
						one_label.config(width=4)
	
	def show_variation(self,event,one_label,i,j):
		# https://stackoverflow.com/questions/14000944/finding-the-currently-selected-tab-of-ttk-notebook
		nb1=self.parent.left_notebook
		nb2=self.parent.right_notebook
		if nb2.index(nb2.select())==1:
			#if self.parent.right_notebook.raised()=="bot":
			grid, markup=self.parent.right_bot_goban.grid, self.parent.right_bot_goban.markup
			self.parent.show_variation(event=event,goban=self.parent.right_bot_goban,grid=grid,markup=markup,i=i,j=j)
			one_label.bind("<Leave>", lambda e: self.parent.leave_variation(self.parent.right_bot_goban,grid,markup))
		elif nb1.index(nb1.select())==1:
			#elif self.parent.left_notebook.raised()=="bot":
			grid, markup=self.parent.left_bot_goban.grid, self.parent.left_bot_goban.markup
			self.parent.show_variation(event=event,goban=self.parent.left_bot_goban,grid=grid,markup=markup,i=i,j=j)
			one_label.bind("<Leave>", lambda e: self.parent.leave_variation(self.parent.left_bot_goban,grid,markup))
	
	def clear_status(self):
		self.parent.clear_status()
	
	def set_status(self,event,msg):
		self.parent.set_status(msg)


class DualView(Toplevel):
	def __init__(self,parent,filename):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		import goban
		goban.fuzzy=grp_config.getfloat("Review", "FuzzyStonePlacement")
		goban.show_variation=self.show_variation
		
		#self.variation_color_mode=grp_config.get("Review", "VariationsColoring")
		self.inverted_mouse_wheel=grp_config.getboolean('Review', 'InvertedMouseWheel')
		#self.variation_label=grp_config.get('Review', 'VariationsLabel')
		
		self.initialize()
		
		self.current_move=1
		self.current_view=-1
		
		self.after(500,lambda: self.display_move(self.current_move))
		self.pressed=0
		self.parent.focus()
	
	def remove_popup(self,popup):
		log("Removing popup")
		self.popups.remove(popup)

	def add_popup(self,popup):
		log("Adding new popup")
		self.popups.append(popup)

	def close(self):
		for tab in self.left_side_opened_tabs+self.right_side_opened_tabs:
			tab.close()
		
		for popup in self.popups[:]:
			popup.close()
		self.destroy()
		self.parent.remove_popup(self)
	
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
			for popup in self.popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()
			# if the table is docked
			if self.table_frame and self.table_frame.grid_info() :
				self.table_widget.display_move(self.current_move,self.current_grid,self.current_markup)

		elif self.pressed==pressed:
			self.display_move(self.current_move)
			for popup in self.popups:
				if isinstance(popup,OpenChart):
					popup.current_move=self.current_move
					#self.parent.after(0,popup.display)
					popup.display()
			# if the table is docked
			if self.table_frame and self.table_frame.grid_info() :
				self.table_widget.display_move(self.current_move,self.current_grid,self.current_markup)
		self.update_idletasks()
		
	def leave_variation(self,goban,grid,markup):
		self.comment_box2.delete(1.0, END)
		self.comment_box2.insert(END,self.game_comments)
		self.parent.bind("<Up>", lambda e: None)
		self.parent.bind("<Down>", lambda e: None)
		self.current_variation_sequence=None
		self.clear_status()
		goban.display(grid,markup)

	def show_both_goban_variation(self,event,goban1,grid1,markup1,goban2,grid2,markup2,i,j):
		sequence=markup1[i][j]
		self.show_variation_move(goban1,grid1,markup1,i,j,len(sequence))
		sequence=markup2[i][j]
		self.show_variation_move(goban2,grid2,markup2,i,j,len(sequence))
		
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
		
		#displaying first move
		color,(u,v),unused,comment,unused,unused=sequence[0]
		place(temp_grid,u,v,color)
		temp_markup[u][v]=1
		
		#displaying following moves
		k=2
		for color,(u,v) in sequence[1:move]:
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
		goban.temporary_shapes.append(local_area)
		
		goban.tag_bind(local_area, "<Leave>", lambda e: self.leave_variation(goban,grid,markup))
		
		self.current_variation_goban=goban
		self.current_variation_grid=grid
		self.current_variation_markup=markup
		self.current_variation_i=i
		self.current_variation_j=j
		self.current_variation_move=move
		self.current_variation_sequence=sequence
		
		self.bind("<Up>", self.show_variation_next)
		self.bind("<Down>", self.show_variation_prev)
		self.bind("<MouseWheel>", self.mouse_wheel)
		if not self.inverted_mouse_wheel:
			self.bind("<Button-4>", self.show_variation_next)
			self.bind("<Button-5>", self.show_variation_prev)
		else:
			self.bind("<Button-5>", self.show_variation_next)
			self.bind("<Button-4>", self.show_variation_prev)
		self.set_status(_("Use mouse wheel or keyboard up/down keys to display the sequence move by move."))
	
	def mouse_wheel(self,event):
		if self.current_variation_sequence==None:
			return
		d = event.delta
		if self.inverted_mouse_wheel:
			d*=-1
		if d>0:
			self.show_variation_next()
		elif d<0:
			self.show_variation_prev()
	

	
	def show_variation_next(self,event=None):
		if self.current_variation_sequence==None:
			return
		move=(self.current_variation_move+1)%(len(self.current_variation_sequence)+1)
		move=max(1,move)
		#log(move,'/',len(self.current_variation_sequence))
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)
	
	def show_variation_prev(self,event=None):
		if self.current_variation_sequence==None:
			return
		move=(self.current_variation_move-1)%len(self.current_variation_sequence)
		if move<1:
			move=len(self.current_variation_sequence)
		
		self.show_variation_move(self.current_variation_goban,self.current_variation_grid,self.current_variation_markup,self.current_variation_i,self.current_variation_j,move)

	def show_territories(self,goban):
		
		goban.variation_index=0
		goban.history=[]
		
		black_t=self.territories[0]
		white_t=self.territories[1]
		dim=self.dim
		markup=[["" for r in range(dim)] for c in range(dim)]
		for i,j in black_t:
			markup[i][j]=-1
		for i,j in white_t:
			markup[i][j]=-2
		goban.display(self.current_grid,markup)
	
	def prepare_data_for_chart(self):
		data=[]
		for m in range(0,self.nb_moves+1):
			one_data={}
			data.append(one_data)
			one_move=get_node(self.gameroot,m)

			try:
				one_data['player_color']=guess_color_to_play(self.gameroot,m) #which turn it is to play
			except:
				pass
			
			try:
				player_color,player_move=one_move.get_move()
				player_move=ij2gtp(player_move).upper()
				one_data['move']=m #move number
			except:
				pass
			
			try:
				es=node_get(one_move,'ES')
				if es[0]=="B":	
					one_data['score_estimation']=float(es[1:])
				else:
					one_data['score_estimation']=-float(es[1:])
				
				one_data['lower_bound_score']=one_data['score_estimation']
				one_data['upper_bound_score']=one_data['score_estimation']
				
			except:
				pass
			
			try:
				ubs=node_get(one_move,'UBS')
				if ubs[0]=="B":	
					one_data['upper_bound_score']=float(ubs[1:])
				else:
					one_data['upper_bound_score']=-float(ubs[1:])
			except:
				pass
			
			try:
				lbs=node_get(one_move,'LBS')
				if lbs[0]=="B":	
					one_data['lower_bound_score']=float(lbs[1:])
				else:
					one_data['lower_bound_score']=-float(lbs[1:])
			except:
				pass
			
			try:
				winrate=node_get(one_move,'MCWR')
				if player_color in ('b',"B"):
					one_data['monte_carlo_win_rate']=float(winrate.split("%")[0])
				else:
					one_data['monte_carlo_win_rate']=float(winrate.split("/")[1][:-1])
			except:
				pass
			
			try:
				winrate=node_get(one_move,'VNWR')
				if player_color in ('b',"B"):
					one_data['value_network_win_rate']=float(winrate.split("%")[0])
				else:
					one_data['value_network_win_rate']=float(winrate.split("/")[1][:-1])
			except:
				pass
			
			#position win rate is the win rate for the position right before the player plays his move
			#so it is the win rate of the best move by the computer for this position
			#because we consider the bot plays perfectly
			try:
				winrate=node_get(one_move,'BWWR')
				if player_color in ('w',"W"):
					current_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					current_position_win_rate=float(winrate.split("%")[0])
				one_data['position_win_rate']=current_position_win_rate
			except:
				pass
			
			#delta is the [position win rate of the next move] - [position win rate of the current move]
			#so it allows to compare how the game would evolve from that position:
			# 1/ in the case the computer best move is played (current_position_win_rate)
			# 2/ compared with when the actual game move was played (next_position_win_rate)
			# positive delta means the game evolves better when the actual game move is played
			# negative delta means the game evolves better when the computer move is played
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=node_get(next_move,'BWWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=node_get(one_move,'CBM')
				if player_move==computer_move:
					# in case the computer best move is the actual game move then:
					# 1/ normally delta=0
					# 2/ let's update current_position_win_rate using next_position_win_rate because it is a better evaluation
					current_position_win_rate=next_position_win_rate
					one_data['position_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['position_win_rate'] #this will fail if the calculation of current_position_win_rate above failed, this is what we want
				one_data['winrate_delta']=delta
			except:
				pass
			
			#delta for monte carlo win rate
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=node_get(next_move,'MCWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=node_get(one_move,'CBM')
				if player_move==computer_move:
					current_position_win_rate=next_position_win_rate
					one_data['monte_carlo_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['monte_carlo_win_rate']
				one_data['mcwr_delta']=delta
			except:
				pass
			
			#delta for value network win rate
			try:
				next_move=get_node(self.gameroot,m+1)
				winrate=node_get(next_move,'VNWR')
				if player_color in ('w',"W"):
					next_position_win_rate=float(winrate.split("/")[1][:-1])
				else:
					next_position_win_rate=float(winrate.split("%")[0])
				computer_move=node_get(one_move,'CBM')
				if player_move==computer_move:
					current_position_win_rate=next_position_win_rate
					one_data['value_network_win_rate']=next_position_win_rate
				delta=next_position_win_rate-one_data['value_network_win_rate']
				one_data['vnwr_delta']=delta
			except:
				pass
			
			if len(one_data)<=2:
				#if move number and color are the only data available for this point
				#then we don't need that data point
				data.pop()
		return data
	
	def show_graphs(self,event=None):
		new_popup=OpenChart(self,self.data_for_chart,self.nb_moves)
		new_popup.current_move=self.current_move
		self.add_popup(new_popup)
		
	def open_table(self,event=None):
		# Variant A: popup
		#   new_popup=Table(self,self.gameroot,self.current_move,self.goban2.grid,self.goban2.markup)
		#   self.add_popup(new_popup)
		#
		# Variant B: widget
		# We should (1) hide comment, (2) show table (widget), (3) re-set button to close table
		self.comment_box2.grid_remove()

		bg=self.cget("background")

		# TODO: May be this should be moved to initialize, but need a solution to prevent blinking when greed() and greed_remove() instantly
		if self.table_frame == None:
			self.table_frame=Frame(self.lists_frame,background=bg)
			self.table_frame.grid(column=1,row=2,sticky=N+W, padx=10, pady=10)
			self.table_widget = TableWidget(self.table_frame,self,self.gameroot,self.current_move,self.current_grid, self.current_markup)
		else:
			# It was created and hidden already
			self.table_frame.grid()

		self.table_button["text"] = _("Comments")
		self.table_button["command"] = self.close_table



	def close_table(self,event=None):
		# We should (1) close table, (2) show comments, (3) re-set button to open table
		self.table_frame.grid_remove()
		self.comment_box2.grid()

		self.table_button["text"] = _("Table")
		self.table_button["command"] = self.open_table

	def hide_territories(self,goban):
		goban.display(self.current_grid,self.current_game_markup)
	
	def update_view(self,move):
		if self.current_view==move:
			return
		dim=self.dim

		self.current_grid=[[0 for row in range(dim)] for col in range(dim)]
		board, unused = sgf_moves.get_setup_and_moves(self.sgf)
		
		#placing handicap stones
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(self.current_grid,row,col,1)
			else:
				place(self.current_grid,row,col,2)
		
		#placing all previous stones
		for m in range(1,move):
			one_move=get_node(self.gameroot,m)
			ij=one_move.get_move()[1]
			if ij==None:
				continue #pass or resign move
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			i,j=list(ij)
			place(self.current_grid,i,j,color)
		
		self.current_markup=[["" for row in range(dim)] for col in range(dim)]
		try:
			#indicating last play with delta
			i,j=one_move.parent.get_move()[1]
			self.current_markup[i][j]=0
		except:
			pass #no previous move available

	def update_game_gobans(self,move):
		
		grid1=copy(self.current_grid)
		markup1=copy(self.current_markup)
		main_sequence=[]
		
		for m in range(self.realgamedeepness):
			one_move=get_node(self.gameroot,move+m)
			if one_move==False:
				break #pass or resign move
			ij=one_move.get_move()[1]
			if ij==None:
				break #pass or resign move
			
			if guess_color_to_play(self.gameroot,move+m)=='b':
				c=1
			else:
				c=2
			
			if m==0:
				main_sequence.append([c,ij,"A",None,"black","black"])
			else:
				main_sequence.append([c,ij])
		try:
			i,j=list(get_node(self.gameroot,move).get_move()[1])
			if main_sequence:
				markup1[i][j]=main_sequence
		except:
			pass
		
		self.current_game_markup=markup1
		
		self.left_game_goban.left_variation_index=0
		self.left_game_goban.history=[]
		self.left_game_goban.display(grid1,markup1)
		
		self.right_game_goban.left_variation_index=0
		self.right_game_goban.history=[]
		self.right_game_goban.display(grid1,markup1)
		
	def update_both_bot_gobans(self, move):
		parent=get_node(self.gameroot,move-1)
		if len(parent)<=1:
			self.table_button.config(state='normal')
		
		coloring=self.left_coloring_selection.get()
		labeling=self.left_labeling_selection.get()
		self.update_one_bot_goban(move, self.left_bot_goban, labeling, coloring)
		
		coloring=self.right_coloring_selection.get()
		labeling=self.right_labeling_selection.get()
		self.update_one_bot_goban(move, self.right_bot_goban, labeling, coloring)
	
	def update_one_bot_goban(self, move, goban, labeling, coloring):
		grid=copy(self.current_grid)
		markup=copy(self.current_markup)
		
		real_game_ij=(-1,-1)
		try:
			ij=one_move[0].get_move()[1]
			if ij:
				real_game_ij=ij
			else:
				pass #no next move available
		except:
			pass #no next move available
		
		parent=get_node(self.gameroot,move-1)
		if len(parent)<=1:
			log("no alternative move")
			goban.display(grid,markup)
			return

		for a in range(1,min(len(parent),self.maxvariations+1)):
			one_alternative=parent[a]
			ij=one_alternative.get_move()[1]

			displaycolor='black'
			
			if one_alternative.get_move()[0]=='b': c=1
			else: c=2
			black_prob=None
			white_prob=None
			if node_has(one_alternative,"BWWR") or node_has(one_alternative,"VNWR") or node_has(one_alternative,"MCWR"):
				if node_has(one_alternative,"BWWR"):
					black_prob=float(node_get(one_alternative,"BWWR").split("%")[0])
					white_prob=100-black_prob
				elif node_has(one_alternative,"VNWR"):
					black_prob=float(node_get(one_alternative,"VNWR").split("%")[0])
					white_prob=100-black_prob
				elif node_has(one_alternative,"MCWR"):
					black_prob=float(node_get(one_alternative,"MCWR").split("%")[0])
					white_prob=100-black_prob
				
				if c==1:
					if coloring=="blue_for_winning":
						if black_prob>=50:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif coloring=="blue_for_best":
						if a==1:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif coloring=="blue_for_better":
						try:
							if node_has(parent[0][0],"BWWR"):
								real_game_prob=float(node_get(parent[0][0],"BWWR").split("%")[0])
							elif node_has(parent[0][0],"VNWR"):
								real_game_prob=float(node_get(parent[0][0],"VNWR").split("%")[0])
							elif node_has(parent[0][0],"MCWR"):
								real_game_prob=float(node_get(parent[0][0],"MCWR").split("%")[0])
							else:
								raise Exception()
							if real_game_prob<black_prob:
								displaycolor="blue"
							elif real_game_prob>black_prob:
								displaycolor="red"
						except:
							pass							
				else:
					if coloring=="blue_for_winning":
						if black_prob>50:
							displaycolor="red"
						else:
							displaycolor="blue"
					elif coloring=="blue_for_best":
						if a==1:
							displaycolor="blue"
						else:
							displaycolor="red"
					elif coloring=="blue_for_better":
						try:
							if node_has(parent[0][0],"BWWR"):
								real_game_prob=100-float(node_get(parent[0][0],"BWWR").split("%")[0])
							elif node_has(parent[0][0],"VNWR"):
								real_game_prob=100-float(node_get(parent[0][0],"VNWR").split("%")[0])
							elif node_has(parent[0][0],"MCWR"):
								real_game_prob=100-float(node_get(parent[0][0],"MCWR").split("%")[0])
							else:
								raise Exception()
							if real_game_prob<white_prob:
								displaycolor="blue"
							elif real_game_prob>white_prob:
								displaycolor="red"
						except:
							pass	
			
			comments=get_variation_comments(one_alternative)
			if node_has(one_alternative,"C"):
				comments+=node_get(one_alternative,"C")

			if ij==real_game_ij: #in case the variation first move is the same as the game actual move, keep the label in black
				letter_color="black"
			else:
				letter_color=displaycolor
			
			if labeling=="letter":
				alternative_sequence=[[c,ij,chr(64+a),comments,displaycolor,letter_color]]
			else:
				if (c==1) and (black_prob):
					alternative_sequence=[[c,ij,str(int(round(black_prob))),comments,displaycolor,letter_color]]
				elif (c==2) and (white_prob):
					alternative_sequence=[[c,ij,str(int(round(white_prob))),comments,displaycolor,letter_color]]
				else:
					alternative_sequence=[[c,ij,chr(64+a),comments,displaycolor,letter_color]]
			
			while len(one_alternative)>0:
				one_alternative=one_alternative[0]
				ij=one_alternative.get_move()[1]
				if one_alternative.get_move()[0]=='b':c=1
				else:c=2
				alternative_sequence.append([c,ij])
			i,j=parent[a].get_move()[1]
			markup[i][j]=alternative_sequence
			
		goban.display(grid,markup)

		
	
	def update_territory(self,move):
		one_move=get_node(self.gameroot,move)
		self.territories=[[],[]]
		if node_has(one_move,"TB"):
			self.territories[0]=node_get(one_move,"TB")
		if node_has(one_move,"TW"):
			self.territories[1]=node_get(one_move,"TW")
		
		if self.territories!=[[],[]]:
			self.territory_button.config(state=NORMAL)
		else:
			self.territory_button.config(state=DISABLED)
	
	def update_comments(self,move):
		one_move=get_node(self.gameroot,move)
		self.game_comments=""
		self.comment_box2.delete(1.0, END)
		left_comments=get_position_comments(move,self.gameroot)
		if node_has(one_move.parent,"C"):
			left_comments+="\n\n==========\n"+node_get(one_move.parent,"C")
		self.game_comments=left_comments
		self.comment_box2.insert(END,self.game_comments)
	
	def display_move(self,move=1):
		
		self.move_number.config(text=str(move)+'/'+str(self.nb_moves))
		log("========================")
		log("displaying move",move)
		
		self.update_view(move)
		self.update_comments(move)
		self.update_territory(move)
		self.update_game_gobans(move)
		self.update_both_bot_gobans(move)
		
		
	def open_move(self):
		log("Opening move",self.current_move)
		
		new_popup=OpenMove(self,self.current_move,self.dim,self.sgf)
		new_popup.goban.mesh=self.left_game_goban.mesh
		new_popup.goban.wood=self.left_game_goban.wood
		new_popup.goban.black_stones=self.left_game_goban.black_stones_style
		new_popup.goban.white_stones=self.left_game_goban.white_stones_style
		
		new_popup.goban.grid=new_popup.grid
		new_popup.goban.markup=new_popup.markup
		new_popup.goban.reset()
		#new_popup.goban.display(new_popup.grid,new_popup.markup)
		
		self.add_popup(new_popup)

	def update_from_file(self):
		period=20
		try:
			if time.time()-os.path.getmtime(self.filename)<=period:
				log("Reloding the RSGF file from hard drive")
				old_sgf=self.sgf
				self.sgf=open_sgf(self.filename)
				log("Updating data")
				#self.dim=self.sgf.get_size()
				#self.komi=self.sgf.get_komi()
				self.gameroot=self.sgf.get_root()
				nb_moves=get_node_number(self.gameroot)
				if nb_moves!=self.nb_moves:
					log("Updating label")
					self.nb_moves=nb_moves
					self.move_number.config(text=str(self.current_move)+'/'+str(self.nb_moves))
				
				new_parent=get_node(self.gameroot,self.current_move-1)
				old_parent=get_node(old_sgf.get_root(),self.current_move-1)
				if len(old_parent)!=len(new_parent):
					#current move beeing displayed should be updated
					log("updating current display")
					self.pressed=time.time()
					pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
					self.parent.after(0,lambda: pf())
				
				log("Updating data for charts")
				self.data_for_chart=self.prepare_data_for_chart()
				for data in self.data_for_chart:
					if data!=None:
						# there was no chart up to this point
						self.charts_button.configure( state = NORMAL )
						break
				
				for popup in self.popups:
					if isinstance(popup,OpenChart):
						log("Updating chart")
						popup.nb_moves=self.nb_moves
						popup.data=self.data_for_chart
						popup.initialize()
						popup.display()
				log("Updating data for table")
				try:
					self.table_widget.gameroot=self.gameroot
				except:
					pass
				
		except:
			pass
		
		self.after(period*1000,self.update_from_file)
	
	def click_game_goban(self,event):
		goban=event.widget
		dim=self.dim
		i,j=goban.xy2ij(event.x,event.y)
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			if (goban.grid[i][j] not in (1,2)) or (type(goban.markup[i][j])==type(123)):
				
				if guess_color_to_play(self.gameroot,self.current_move+goban.left_variation_index)=="b":
					color=1
				else:
					color=2

				if goban.left_variation_index==0:
					goban.history=[[copy(self.current_grid),copy(self.current_markup)]]
					updated_markup=[["" for row in range(dim)] for col in range(dim)]
					updated_grid=copy(self.current_grid)
				else:
					goban.history=goban.history[:goban.left_variation_index+1]
					updated_markup=copy(goban.markup)
					updated_grid=copy(goban.grid)
				updated_markup[i][j]=unicode(goban.left_variation_index+1)
				place(updated_grid,i,j,color)
				goban.history.append([copy(updated_grid),copy(updated_markup)])
				goban.display(copy(updated_grid),updated_markup)
				
				if color==1:
					goban.black_stones[i][j].shine()
				else:
					goban.white_stones[i][j].shine()
				
				goban.left_variation_index+=1
				
				self.bind("<MouseWheel>", self.left_mouse_wheel)
				if not self.inverted_mouse_wheel:
					self.bind("<Button-4>", self.show_left_variation_next)
					self.bind("<Button-5>", self.show_left_variation_prev)
				else:
					self.bind("<Button-5>", self.show_left_variation_next)
					self.bind("<Button-4>", self.show_left_variation_prev)
				
				self.set_status(_("Use mouse middle click or wheel to undo move."))


	def shine(self,event):
		goban=event.widget
		dim=self.dim
		i,j=goban.xy2ij(event.x,event.y)
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			color=goban.grid[i][j]
			if color==1:
				goban.black_stones[i][j].shine(100)
			elif color==2:
				goban.white_stones[i][j].shine(100)
			else:
				goban.intersections[i][j].shine(100)
				
	def left_mouse_wheel(self,event):
		d = event.delta
		if self.inverted_mouse_wheel:
			d*=-1
		if d>0:
			self.show_left_variation_next(event)
		elif d<0:
			self.show_left_variation_prev(event)
	
	def show_left_variation_next(self,event):
		goban=event.widget
		if len(goban.history)<=1:
			return
		if goban.left_variation_index>=len(goban.history)-1:
			return
		updated_grid, updated_markup =goban.history[goban.left_variation_index+1]
		goban.display(copy(updated_grid),updated_markup)
		goban.left_variation_index+=1

	def show_left_variation_prev(self,event):
		goban=event.widget
		if len(goban.history)<=1:
			return
		if goban.left_variation_index==0:
			return
		updated_grid, updated_markup =goban.history[goban.left_variation_index-1]
		goban.display(copy(updated_grid),updated_markup)
		goban.left_variation_index-=1

	def undo(self,event=None):
		goban=event.widget
		if goban.left_variation_index>0:
			goban.history=goban.history[:goban.left_variation_index]
			grid,markup=goban.history[-1]
			goban.display(grid,markup)
			goban.left_variation_index-=1

	def change_left_display(self):
		coloring=self.left_coloring_selection.get()
		labeling=self.left_labeling_selection.get()
		grp_config.set("Review","VariationsColoring",coloring)
		grp_config.set("Review","VariationsLabel",labeling)
		self.update_one_bot_goban(self.current_move, self.left_bot_goban, labeling, coloring)
		
	def change_right_display(self):
		coloring=self.right_coloring_selection.get()
		labeling=self.right_labeling_selection.get()
		grp_config.set("Review","VariationsColoring",coloring)
		grp_config.set("Review","VariationsLabel",labeling)
		self.update_one_bot_goban(self.current_move, self.right_bot_goban, labeling, coloring)
		
	
	def new_right_goban(self,event=None):
		new_tab=InteractiveGoban(self.right_notebook,self.current_move,self.dim,self.sgf)
		new_tab.status_bar=self.status_bar
		new_tab.goban.space=self.right_game_goban.space
		new_tab.goban.mesh=self.left_game_goban.mesh
		new_tab.goban.wood=self.left_game_goban.wood
		new_tab.goban.black_stones=self.left_game_goban.black_stones_style
		new_tab.goban.white_stones=self.left_game_goban.white_stones_style
		
		self.right_side_opened_tabs.append(new_tab)
		
		pos=len(self.right_notebook.tabs())-1
		self.right_notebook.insert(pos,new_tab, text=str(self.current_move))
		self.right_notebook.select(pos)
		new_tab.close_button.config(command=lambda: self.close_right_tab(new_tab))

	def close_right_tab(self, tab):
		id=self.right_notebook.index("current")
		log("closing tab", id)
		self.right_notebook.select(id-1)
		self.right_notebook.forget(id)
		tab.close()
		self.right_side_opened_tabs.remove(tab)
		
	def new_left_goban(self,event=None):
		new_tab=InteractiveGoban(self.left_notebook,self.current_move,self.dim,self.sgf)
		new_tab.status_bar=self.status_bar
		new_tab.goban.space=self.left_game_goban.space
		new_tab.goban.mesh=self.left_game_goban.mesh
		new_tab.goban.wood=self.left_game_goban.wood
		new_tab.goban.black_stones=self.left_game_goban.black_stones_style
		new_tab.goban.white_stones=self.left_game_goban.white_stones_style
		
		self.left_side_opened_tabs.append(new_tab)
		
		pos=len(self.left_notebook.tabs())-1
		self.left_notebook.insert(pos,new_tab, text=str(self.current_move))
		self.left_notebook.select(pos)
		new_tab.close_button.config(command=lambda: self.close_left_tab(new_tab))
	
	def close_left_tab(self, tab):
		id=self.left_notebook.index("current")
		log("closing tab", id)
		self.left_notebook.select(id-1)
		self.left_notebook.forget(id)
		tab.close()
		self.left_side_opened_tabs.remove(tab)
		
	def initialize(self):
		
		self.left_side_opened_tabs=[]
		self.right_side_opened_tabs=[]
		
		self.realgamedeepness=grp_config.getint("Review", "RealGameSequenceDeepness")
		self.maxvariations=grp_config.getint("Review", "MaxVariations")
		
		self.sgf = open_sgf(self.filename)

		self.dim=self.sgf.get_size()
		self.komi=self.sgf.get_komi()
		
		log("boardsize:",self.dim)
		#goban.dim=size
		
		#goban.prepare_mesh()
		self.gameroot=self.sgf.get_root()
		self.nb_moves=get_node_number(self.gameroot)

		self.title('GoReviewPartner - '+os.path.basename(self.filename))
		self.protocol("WM_DELETE_WINDOW", self.close)
		
		self.popups=[]
		self.data_for_chart=self.prepare_data_for_chart()
		
		bg=self.cget("background")
		#self.configure(background=bg)
		
		# Such paned containers
		central_frame = PanedWindow(self, orient=HORIZONTAL,relief=SUNKEN)
		gobans_frame = PanedWindow(central_frame,relief=SUNKEN, orient=HORIZONTAL) #one paned frame for gobans, so that they resize at the same ratio
		
		# Such frames
		self.buttons_bar2=Frame(self)
		self.lists_frame=Frame(central_frame,relief=SUNKEN)
		self.table_frame = None
		

		# Such widgets for main window
		
		left_display_factor=grp_config.getfloat("Review", "LeftGobanRatio")
		right_display_factor=grp_config.getfloat("Review", "RightGobanRatio")
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		self.left_goban_size=min(left_display_factor*screen_width,left_display_factor*screen_height)
		self.right_goban_size=min(right_display_factor*screen_width,right_display_factor*screen_height)
		
		left_notebook=Notebook(gobans_frame)
		
		left_game_tab=Frame(left_notebook)
		left_notebook.add(left_game_tab, text=_("Actual game"))
		
		left_bot_tab=Frame(left_notebook)
		left_notebook.add(left_bot_tab, text=_("Analysis"))
		
		left_plus_tab=Frame(left_notebook)
		left_notebook.add(left_plus_tab, text="+")
		left_plus_tab.bind("<Visibility>",self.new_left_goban)
		
		right_notebook=Notebook(gobans_frame)
		
		right_game_tab=Frame(right_notebook)
		right_notebook.add(right_game_tab, text=_("Actual game"))
		
		right_bot_tab=Frame(right_notebook)
		right_notebook.add(right_bot_tab, text=_("Analysis"))
		
		right_plus_tab=Frame(right_notebook)
		right_notebook.add(right_plus_tab, text="+")
		right_plus_tab.bind("<Visibility>",self.new_right_goban)
		
		gobans_frame.add(left_notebook, stretch="always") #https://mail.python.org/pipermail/tkinter-discuss/2012-May/003146.html
		gobans_frame.add(right_notebook, stretch="always")
		
		
		#######################
		toolbar=Frame(left_game_tab)
		toolbar.pack(fill=X)
		left_territory_button=Button(toolbar,text=_("Show territories"))
		left_territory_button.pack(side=LEFT,fill=Y)
		self.left_game_goban = Goban(self.dim,self.left_goban_size,master=left_game_tab)
		self.left_game_goban.pack(fill=BOTH,expand=True)
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		
		#######################
		toolbar=Frame(left_bot_tab)
		toolbar.pack(fill=X)
		
		mb=Menubutton(toolbar, text=_("Display"), relief=RAISED)
		mb.pack(side=LEFT,fill=Y)
		mb.menu = Menu(mb,tearoff=0)
		mb["menu"]= mb.menu

		coloring_selection = StringVar()
		self.left_coloring_selection=coloring_selection
		coloring={"blue_for_winning":_("Win rate > 50% in blue"),"blue_for_best":_("The best variation in blue"),"blue_for_better":_("Variations better than actual game move in blue")}
		coloring_selection.set(grp_config.get("Review","VariationsColoring"))
		for value, label in coloring.items():
			mb.menu.add_radiobutton(label=label, value=value, variable=coloring_selection, command=self.change_left_display)
		
		mb.menu.add_separator()
		labeling_selection = StringVar()
		self.left_labeling_selection=labeling_selection
		labeling={"letter":_("Letters"),"rate":_("Percentages")}
		labeling_selection.set(grp_config.get("Review","VariationsLabel"))
		for value, label in labeling.items():
			mb.menu.add_radiobutton(label=label, value=value, variable=labeling_selection, command=self.change_left_display)
		
		#filter_button=Button(toolbar,text="Filter", state="disable")
		#filter_button.pack(side=LEFT)
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		
		self.left_bot_goban = Goban(self.dim,self.left_goban_size,master=left_bot_tab)
		self.left_bot_goban.pack(fill=BOTH,expand=True)
		
		#######################
		toolbar=Frame(right_game_tab)
		toolbar.pack(fill=X)
		right_territory_button=Button(toolbar,text=_("Show territories"))
		right_territory_button.pack(side=LEFT,fill=Y)
		self.right_game_goban = Goban(self.dim,self.right_goban_size,master=right_game_tab)
		self.right_game_goban.pack(fill=BOTH,expand=True)
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		
		#######################
		toolbar=Frame(right_bot_tab)
		toolbar.pack(fill=X)

		mb=Menubutton(toolbar, text=_("Display"), relief=RAISED)
		mb.pack(side=LEFT,fill=Y)
		mb.menu = Menu(mb,tearoff=0)
		mb["menu"]= mb.menu

		coloring_selection = StringVar()
		self.right_coloring_selection=coloring_selection
		coloring={"blue_for_winning":_("Win rate > 50% in blue"),"blue_for_best":_("The best variation in blue"),"blue_for_better":_("Variations better than actual game move in blue")}
		coloring_selection.set(grp_config.get("Review","VariationsColoring"))
		for value, label in coloring.items():
			mb.menu.add_radiobutton(label=label, value=value, variable=coloring_selection, command=self.change_right_display)
		
		mb.menu.add_separator()
		labeling_selection = StringVar()
		self.right_labeling_selection=labeling_selection
		labeling={"letter":_("Letters"),"rate":_("Percentages")}
		labeling_selection.set(grp_config.get("Review","VariationsLabel"))
		for value, label in labeling.items():
			mb.menu.add_radiobutton(label=label, value=value, variable=labeling_selection, command=self.change_right_display)
		
		#filter_button=Button(toolbar,text="Filter", state="disable")
		#filter_button.pack(side=LEFT)
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		
		self.right_bot_goban = Goban(self.dim,self.right_goban_size,master=right_bot_tab)
		self.right_bot_goban.pack(fill=BOTH,expand=True)
		
		for goban in [self.right_bot_goban, self.left_bot_goban, self.right_game_goban]:
			goban.mesh=self.left_game_goban.mesh
			goban.wood=self.left_game_goban.wood
			goban.black_stones_style=self.left_game_goban.black_stones_style
			goban.white_stones_style=self.left_game_goban.white_stones_style
		
		for goban in [self.left_bot_goban, self.left_game_goban]:
			goban.space=self.left_goban_size/(self.dim+1+1+1)
		
		for goban in [self.right_bot_goban, self.right_game_goban]:
			goban.space=self.right_goban_size/(self.dim+1+1+1)
		

		
		
		#creating the status bar widget
		self.status_bar=Label(self,text='',anchor=W,justify=LEFT)

		# Such widgets for the buttons_bar - game navigation
		first_move_button=Button(self.buttons_bar2, text='|<< ',command=self.first_move)
		prev_10_moves_button=Button(self.buttons_bar2, text=' << ',command=self.prev_10_move)
		prev_button=Button(self.buttons_bar2, text=' <  ',command=self.prev_move)
		self.move_number=Label(self.buttons_bar2,text='   ',background=bg,width=9)
		next_button=Button(self.buttons_bar2, text='  > ',command=self.next_move)
		next_10_moves_button=Button(self.buttons_bar2, text=' >> ',command=self.next_10_move)
		final_move_button=Button(self.buttons_bar2, text=' >>|',command=self.final_move)
		
		# Such widgets for the buttons_bar2 - commands and extra windows
		open_button=Button(self.buttons_bar2, text=_('Open position'),command=self.open_move)
		self.territory_button=Button(self.buttons_bar2, text=_('Show territories'))
		self.table_button=Button(self.buttons_bar2,text=_("Table"),command=self.open_table)
		self.charts_button=Button(self.buttons_bar2, text=_('Graphs'),command=self.show_graphs, state=DISABLED)

		for data in self.data_for_chart:
			if data!=None:
				self.charts_button.configure( state = NORMAL )
				break
		
		# Such widgets for the rightmost list frame
		police = tkFont.nametofont("TkFixedFont")
		lpix = police.measure("a")
		self.lpix=lpix
		right_panel_ratio=grp_config.getfloat("Review", "RightPanelRatio")
		right_panel_width=right_panel_ratio*screen_width
		self.comment_chars = int(right_panel_width/lpix)
		self.comment_box2=ScrolledText(self.lists_frame,font=police,wrap="word",width=self.comment_chars,foreground='black')
		
		#Place widgets in button_bar
		first_move_button.grid(column=1,row=1)
		prev_10_moves_button.grid(column=2,row=1)
		prev_button.grid(column=3,row=1)
		self.move_number.grid(column=5,row=1)
		next_button.grid(column=7,row=1)
		next_10_moves_button.grid(column=8,row=1)
		final_move_button.grid(column=9,row=1)
		
		#spacer to separate left and right groups of button
		Label(self.buttons_bar2,text='').grid(column=50,row=1,sticky=W+E)
		self.buttons_bar2.columnconfigure(50, weight=1)
		
		#Place widgets in command bar
		#open_button.grid(column=100,row=1)
		self.table_button.grid(column=101,row=1)
		self.charts_button.grid(column=102,row=1)
		self.territory_button.grid(column=103,row=1)
		
		#Place widgets in lists frame
		self.comment_box2.grid(column=1,row=2,sticky=N+S+E+W, padx=2, pady=2)
		self.lists_frame.grid_columnconfigure(1, weight=1)
		self.lists_frame.grid_rowconfigure(2, weight=1)

		#Place widgets in main frame
		self.buttons_bar2.pack(fill=X)
		
		
		central_frame.pack(fill=BOTH, expand=1)	
		
		central_frame.add(gobans_frame, stretch="always")
		central_frame.add(self.lists_frame, stretch="always")
		
		self.status_bar.pack(fill=X)
		
		# Such keybindings
		left_territory_button.bind('<Button-1>', lambda event: self.show_territories(self.left_game_goban))
		left_territory_button.bind('<ButtonRelease-1>', lambda event: self.hide_territories(self.left_game_goban))
		right_territory_button.bind('<Button-1>', lambda event: self.show_territories(self.right_game_goban))
		right_territory_button.bind('<ButtonRelease-1>', lambda event: self.hide_territories(self.right_game_goban))
		
		
		self.bind('<Control-q>', self.save_left_as_png)
		self.bind('<Control-w>', self.save_right_as_png)
		self.bind('<Left>', self.prev_move)
		self.bind('<Right>', self.next_move)
		
		# Such tooltips
		first_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to first move.")))
		prev_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go back 10 moves.")))
		prev_button.bind("<Enter>",lambda e: self.set_status(_("Go back one move. Shortcut: keyboard left key.")))
		open_button.bind("<Enter>",lambda e: self.set_status(_("Open this position onto a third goban to play out variations.")))
		next_button.bind("<Enter>",lambda e: self.set_status(_("Go forward one move. Shortcut: keyboard right key.")))
		next_10_moves_button.bind("<Enter>",lambda e: self.set_status(_("Go forward 10 moves.")))
		final_move_button.bind("<Enter>",lambda e: self.set_status(_("Go to final move.")))
		#self.charts_button.bind('<Button-1>', self.show_graphs)
		self.territory_button.bind("<Enter>",lambda e: self.set_status(_("Keep pressed to show territories.")))
		self.left_game_goban.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		self.right_bot_goban.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+W> to save the goban as an image.")))
		
		self.comment_box2.bind("<Configure>",self.redraw_panel)
		
		for button in [first_move_button,prev_10_moves_button,prev_button,open_button,next_button,next_10_moves_button,final_move_button,self.territory_button,self.left_game_goban,self.right_bot_goban]:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		for goban in [self.left_bot_goban, self.left_game_goban]:
			goban.bind("<Configure>",self.redraw_left)

		for goban in [self.right_bot_goban, self.right_game_goban]:
			goban.bind("<Configure>",self.redraw_right)
		
		#left_notebook.raise_page("game") #forcing a refresh/resize
		right_notebook.select(1)
		
		self.left_notebook=left_notebook
		self.right_notebook=right_notebook
		
		for goban in [self.left_game_goban, self.right_game_goban]:
			goban.bind("<Button-1>",self.click_game_goban)
			goban.bind("<Button-2>",self.undo)
			goban.bind("<Button-3>",self.shine)
		
		for goban in [self.left_bot_goban, self.right_bot_goban]:
			goban.bind("<Button-3>",self.shine)
		
		self.after(10000,self.update_from_file)
		
		
		
		

	def redraw_left(self, event, redrawing=None):
		if not redrawing:
			redrawing=time.time()
			self.redrawing_left=redrawing
			self.after(200,lambda: self.redraw_left(event,redrawing))
			return
		if redrawing<self.redrawing_left:
			return

		new_size=min(event.width,event.height)
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		min_screen_size=min(screen_width, screen_height)
		new_size=new_size-new_size%max(int((0.05*min_screen_size)),1) #the goban is resized by increment of 5% of the screen size
		new_space=int(new_size/(self.dim+1+1+1))
		
		ratio=1.0*new_size/min_screen_size
		grp_config.set("Review", "LeftGobanRatio",ratio)
		new_anchor_x=(event.width-new_size)/2
		new_anchor_y=(event.height-new_size)/2
		goban=event.widget
		goban.space=new_space
		goban.anchor_x=new_anchor_x
		goban.anchor_y=new_anchor_y
		goban.reset()
		
		"""
		for goban in [self.left_bot_goban, self.left_game_goban]+[tab.goban for tab in self.left_side_opened_tabs]:
			goban.space=new_space
			goban.anchor_x=new_anchor_x
			goban.anchor_y=new_anchor_y
			goban.reset()"""

	def redraw_right(self, event, redrawing=None):
		if not redrawing:
			redrawing=time.time()
			self.redrawing_right=redrawing
			self.after(200,lambda: self.redraw_right(event,redrawing))
			return
		if redrawing<self.redrawing_right:
			return
		
		new_size=min(event.width,event.height)
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		min_screen_size=min(screen_width, screen_height)
		new_size=new_size-new_size%max(int((0.05*min_screen_size)),1) #the goban is resized by increment of 5% of the screen size
		new_space=int(new_size/(self.dim+1+1+1))
		
		ratio=1.0*new_size/min(screen_width,screen_height)
		grp_config.set("Review", "RightGobanRatio",ratio)
		
		new_anchor_x=(event.width-new_size)/2
		new_anchor_y=(event.height-new_size)/2
		
		goban=event.widget
		goban.space=new_space
		goban.anchor_x=new_anchor_x
		goban.anchor_y=new_anchor_y
		goban.reset()
		
		"""for goban in [self.right_bot_goban, self.right_game_goban]+[tab.goban for tab in self.right_side_opened_tabs]:
			goban.space=new_space
			goban.anchor_x=new_anchor_x
			goban.anchor_y=new_anchor_y
			goban.reset()"""

	def redraw_panel(self, event):
		new_size=event.width
		screen_width = self.parent.winfo_screenwidth()
		ratio=1.0*new_size/screen_width
		grp_config.set("Review", "RightPanelRatio",ratio)

	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")

	def save_left_as_png(self,event=None):
		filename = save_png_file(parent=self,filename='move'+str(self.current_move)+'.png')
		canvas2png(self.goban1,filename)

	def save_right_as_png(self,event=None):
		filename = save_png_file(parent=self,filename='move'+str(self.current_move)+'.png')
		canvas2png(self.goban2,filename)
	
if __name__ == "__main__":
	if len(sys.argv)==1:
		temp_root = Tk()
		filename = open_rsgf_file(parent=temp_root)
		temp_root.destroy()
		log(filename)
		if not filename:
			sys.exit()
	else:
		filename=sys.argv[1]
	top = Application()
	popup=DualView(top,filename)
	top.add_popup(popup)
	top.mainloop()
