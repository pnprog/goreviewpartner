# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from Tkinter import *
from toolbox import *
from toolbox import _
from goban import *
from copy import deepcopy as copy

class InteractiveGoban(Frame):
	def __init__(self,parent,move,dim,sgf,**kwargs):
		Frame.__init__(self,parent,**kwargs)
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
		
		self.available_bots=[]
		for bot in get_available():
			self.available_bots.append(bot)
		
		self.available_gtp_bots=[]
		for bot in get_gtp_bots():
			self.available_gtp_bots.append(bot)
		self.initialize()
	
	def stone_sound(self):
		self.after(0,play_stone_sound)
	
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
		self.selected_action.set("do nothing")
		self.change_action()

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
		log("closing tab")
		if self.current_bot!=_("No bot"):
			self.menu_bots[self.current_bot].close()
		try:
			self.display_queue.put(0, False)
		except:
			pass
		self.destroy()
		log("done")
	
	def undo(self,event=None):
		log("UNDO")
		if self.undo_button.cget("state")=='disabled':
			return
		if len(self.history)<1:
			return
		elif len(self.history)==1:
			self.undo_button.config(state='disabled')
		
		self.grid,self.markup,unused=self.history.pop()
		self.next_color=3-self.next_color
		self.goban.display(self.grid,self.markup)
		
		if self.current_bot!=_("No bot"):
			self.menu_bots[self.current_bot].undo()
		

	def click_button(self,bot):
		dim=self.dim
		self.display_queue.put(3)
		self.display_queue.put(2)
		color=self.next_color
		move=bot.click(color)
		
		if move not in ["PASS","RESIGN"]:
			i,j=gtp2ij(move)

			self.history.append([copy(self.grid),copy(self.markup),(move,color)])
			
			place(self.grid,i,j,color)
			self.display_queue.put((i,j))
			
			self.grid[i][j]=color
			self.markup=[["" for r in range(dim)] for c in range(dim)]
			self.markup[i][j]=0
			self.next_color=3-color
		else:
			bot.undo()
			if color==1:
				self.display_queue.put(bot.name+" ("+_("Black")+"): "+move)
			else:
				self.display_queue.put(bot.name+" ("+_("White")+"): "+move)
			
			self.do_nothing()
			return
		
		if self.white_autoplay and self.black_autoplay:
			if move not in ["PASS","RESIGN"]:
				log("SELF PLAY")
				self.display_queue.put(2)
				one_thread=threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],))
				self.after(0,one_thread.start)
				return
			else:
				log("End of SELF PLAY")
				self.display_queue.put(4)
				self.display_queue.put(1)
				self.do_nothing()

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
				#nothing, so we add a stone
				
				if self.current_bot!=_("No bot"):
					bot=self.menu_bots[self.current_bot]
					if bot.place(ij2gtp((i,j)),color)==False:
						self.remove_bot(self.current_bot)
		
				self.history.append([copy(self.grid),copy(self.markup),(ij2gtp((i,j)),color)])
				
				place(self.grid,i,j,color)
				self.grid[i][j]=color
					
				self.markup=[["" for r in range(dim)] for c in range(dim)]
				self.markup[i][j]=0
					
				self.goban.display(self.grid,self.markup)
				if color==1:
					self.goban.black_stones[i][j].shine()
				else:
					self.goban.white_stones[i][j].shine()
				self.stone_sound()
				self.next_color=3-color
				self.undo_button.config(state='normal')
				
				if color==1:
					if self.white_autoplay:
						log("WHITE AUTOPLAY")
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])
				else:
					if self.black_autoplay:
						log("BLACK AUTOPLAY")
						threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
						#self.click_button(self.menu_bots[self.selected_bot.get()])

				
	def set_status(self,msg,event=None):
		try:
			self.status_bar.config(text=msg)
		except:
			log(msg)
		
	def clear_status(self):
		try:
			self.status_bar.config(text="")
		except:
			pass
		
	def click_play_one_move(self):
		log("Asking",self.selected_bot.get(),"to play one move")
		#self.white_button.config(relief=RAISED)
		#self.black_button.config(relief=RAISED)
		#self.selfplay_button.config(relief=RAISED)
		
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
		self.black_autoplay=True
		self.white_autoplay=True
		self.bots_menubutton.config(state="disabled")
		threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()

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
	
	def change_action(self):
		action=self.selected_action.get()
		log("action=",action)
		if action=="do nothing":
			self.black_autoplay=False
			self.white_autoplay=False
			if len(self.menu_bots)>0:
				self.bots_menubutton.config(state="normal")
			if len(self.history)>0:
				self.undo_button.config(state='normal')
		elif action=="quick evaluation":
			self.click_evaluation()
			self.selected_action.set("do nothing")
			self.black_autoplay=False
			self.white_autoplay=False
		elif action=="play one move":
			self.click_play_one_move()
			self.selected_action.set("do nothing")
			self.black_autoplay=False
			self.white_autoplay=False
		elif action=="self play":
			self.click_selfplay()
		elif action=="play as white":
			color=self.next_color
			self.white_autoplay=True
			if color==2: #it's white to play
				threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
		elif action=="play as black":
			color=self.next_color
			self.black_autoplay=True
			if color==1: #it's black to play
				threading.Thread(target=self.click_button,args=(self.menu_bots[self.selected_bot.get()],)).start()
	
	def remove_bot(self,bot):
		self.bots_menubutton.menu.delete(bot)
		self.actions_menubutton.config(state="disabled")
		del self.menu_bots[bot]
		if len(self.menu_bots)==0:
			self.bots_menubutton.config(state="disabled")
		self.current_bot=_("No bot")
	
	
	def change_bot(self):
		
		if self.current_bot!=_("No bot"):
			log("Bot changed from '"+self.current_bot+"' to '"+self.selected_bot.get()+"'")
			log("Terminating",self.current_bot)
			previous_bot=self.menu_bots[self.current_bot]
			previous_bot.close()
			self.current_bot=_("No bot")
		else:
			log("Bot selected:",self.selected_bot.get())
		
		if self.selected_bot.get()==_("No bot"):
			self.current_bot=_("No bot")
			self.actions_menubutton.config(state="disabled")
			return
		
		new_bot=self.menu_bots[self.selected_bot.get()]
		new_bot.start(silentfail=False)
		if not new_bot.okbot:
			self.remove_bot(self.selected_bot.get())
			self.selected_bot.set(_("No bot"))
			self.change_bot()
			return
			
		
		grp_config.set("Review", "LastBot",self.selected_bot.get() )
		
		gameroot=self.sgf.get_root()
		m=0
		for m in range(1,self.move):
			one_move=get_node(gameroot,m)
			if one_move==False:
				log("(0)leaving because one_move==False")
				break
			ij=one_move.get_move()[1]
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			if not new_bot.place(ij2gtp(ij),color):
				self.remove_bot(self.current_bot)
				self.selected_bot.set(_("No bot"))
				self.change_bot()
				return
		
		
		for __,__,move in self.history:
			if not new_bot.place(move[0],move[1]):
				self.remove_bot(self.current_bot)
				self.selected_bot.set(_("No bot"))
				self.change_bot()
				return
		
		self.current_bot=self.selected_bot.get()
		self.actions_menubutton.config(state="normal")
		
		print self.current_bot
		print [bot['gtp_name']+" - "+bot['profile'] for bot in self.available_gtp_bots]
		if self.current_bot in [bot['gtp_name']+" - "+bot['profile'] for bot in self.available_gtp_bots]:
			log("A GTP bot is selected")
			self.actions_menubutton.menu.entryconfig(_('Ask the bot for a quick evaluation'), state="disabled")
		else:
			self.actions_menubutton.menu.entryconfig(_('Ask the bot for a quick evaluation'), state="normal")
	
	def close_tab(self):
		log("Not implemented")
	
	def initialize(self):
		gameroot=self.sgf.get_root()
		popup=self
		
		dim=self.dim
		move=self.move
		self.locked=False
		panel=Frame(popup)
		undo_button=Button(panel, text=_('Undo'),command=self.undo)
		undo_button.pack(side=LEFT,fill=Y)
		undo_button.config(state='disabled')
		undo_button.bind("<Enter>",lambda e: self.set_status(_("Undo last move. Shortcut: mouse middle button.")))
		undo_button.bind("<Leave>",lambda e: self.clear_status())
		
		self.bots=[]
		self.menu_bots={}
		for available_bot in self.available_bots:
			one_bot=available_bot['openmove'](self.sgf,available_bot)
			self.bots.append(one_bot)
			self.menu_bots[one_bot.name+" - "+available_bot['profile']]=one_bot
		
		for available_bot in self.available_gtp_bots:
			one_bot=available_bot['openmove'](self.sgf,available_bot)
			self.bots.append(one_bot)
			self.menu_bots[one_bot.name+" - "+available_bot['profile']]=one_bot
		
		if len(self.menu_bots)>0:
			
			mb=Menubutton(panel, text=_("Select a bot")+" ▽", relief=RAISED)
			mb.pack(side=LEFT,fill=Y)
			mb.menu = Menu(mb,tearoff=0)
			mb["menu"]= mb.menu
			self.bots_menubutton=mb
			
			self.selected_bot=StringVar()
			#self.selected_bot.set(self.menu_bots.keys()[0])
			self.current_bot=_("No bot")
			
			list_of_bots=self.menu_bots.keys()
			list_of_bots.sort()
			if grp_config.get("Review", "LastBot") in list_of_bots:
				log("Placing",grp_config.get("Review", "LastBot") , "as playing bot first choice")
				list_of_bots.remove(grp_config.get("Review", "LastBot"))
				list_of_bots=[grp_config.get("Review", "LastBot")]+list_of_bots
			list_of_bots.append(_("No bot"))
			self.selected_bot.set(_("No bot"))
			for bot in list_of_bots:
				mb.menu.add_radiobutton(label=bot, value=bot, variable=self.selected_bot, command=self.change_bot)
			
			mb=Menubutton(panel, text=_("Action")+" ▽", relief=RAISED)
			mb.pack(side=LEFT,fill=Y)
			mb.menu = Menu(mb,tearoff=0)
			mb["menu"]= mb.menu
			self.actions_menubutton=mb
			mb.config(state="disabled")
			self.selected_action=StringVar()
			self.selected_action.set("do nothing")
			mb.menu.add_radiobutton(label=_('Do nothing'), value="do nothing", variable=self.selected_action, command=self.change_action)
			mb.menu.add_radiobutton(label=_('Play one move'), value="play one move", variable=self.selected_action, command=self.change_action)
			mb.menu.add_radiobutton(label=_('Play as white'), value="play as white", variable=self.selected_action, command=self.change_action)
			mb.menu.add_radiobutton(label=_('Play as black'), value="play as black", variable=self.selected_action, command=self.change_action)
			mb.menu.add_radiobutton(label=_('Let the bot take both sides and play against itself.'), value="self play", variable=self.selected_action, command=self.change_action)
			mb.menu.add_radiobutton(label=_('Ask the bot for a quick evaluation'), value="quick evaluation", variable=self.selected_action, command=self.change_action)
		
		Label(panel, text=' ', height=2).pack(side=LEFT, fill=X, expand=1)
		self.close_button=Button(panel, text='x', command=self.close_tab)
		self.close_button.pack(side=LEFT,fill=Y)
		
		self.black_autoplay=False
		self.white_autoplay=False
		
		panel.pack(fill=X)
		bg=popup.cget("background")
		goban3 = Goban(dim,1,master=popup,bg=bg,bd=0, borderwidth=0)
		goban3.space=1
		goban3.pack(fill=BOTH,expand=1)

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
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
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
		
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",self.shine)
		#goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]
		self.update_idletasks()

		self.goban.grid=grid3
		self.goban.markup=markup3
		
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
				self.stone_sound()
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
		#new_size=new_size-new_size%max(int((0.1*self.dim*self.goban.space)),1)
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		min_screen_size=min(screen_width, screen_height)
		new_size=new_size-new_size%max(int((0.05*min_screen_size)),1) #the goban is resized by increment of 5% of the screen size
		new_space=int(new_size/(self.dim+1+1+1))
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.reset()

	def save_as_png(self,event=None):
		filename = save_png_file(parent=self,filename='variation_move'+str(self.move)+'.png')
		canvas2png(self.goban,filename)
