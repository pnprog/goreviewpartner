# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from toolbox import *
from toolbox import _
from goban import *
from datetime import datetime
from Tkinter import *
from threading import Lock
from copy import deepcopy as copy
from ttk import Notebook
from tabbed import *

class LiveAnalysisLauncher(Toplevel):
	def __init__(self,parent):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.protocol("WM_DELETE_WINDOW", self.close)
		self.config(padx=10,pady=10)
		
		root = self
		root.parent.title('GoReviewPartner')

		row=1
		self.analysis_bots_names=[bot['name']+" - "+bot['profile'] for bot in get_available()]
		Label(self,text=_("Bot to use for analysis:")).grid(row=row,column=1,sticky=W)
		self.bot_selection=StringVar()	
		apply(OptionMenu,(self,self.bot_selection)+tuple(self.analysis_bots_names)).grid(row=row,column=2,sticky=W)
		
		self.bots_names=[bot['name']+" - "+bot['profile'] for bot in get_available()]
		self.gtp_bots_names=[bot['name']+" - "+bot['profile'] for bot in get_gtp_bots()]
		#row+=1
		#Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Black player")+":").grid(row=row,column=1,sticky=W)
		self.black_selection=StringVar()	
		self.black_selection_wrapper=Frame(self)
		self.black_selection_wrapper.grid(row=row,column=2,sticky=W)
		self.black_options=[_("Human player"),_("Bot used for analysis")]+self.bots_names+self.gtp_bots_names
		self.black_menu=apply(OptionMenu,(self.black_selection_wrapper,self.black_selection)+tuple(self.black_options))
		self.black_menu.pack()
		#row+=1
		#Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("White player")+":").grid(row=row,column=1,sticky=W)
		self.white_selection=StringVar()
		self.white_selection_wrapper=Frame(self)
		self.white_selection_wrapper.grid(row=row,column=2,sticky=W)
		self.white_options=[_("Human player"),_("Bot used for analysis")]+self.bots_names+self.gtp_bots_names
		self.white_menu=apply(OptionMenu,(self.white_selection_wrapper,self.white_selection)+tuple(self.white_options))
		self.white_menu.pack()
		
		row+=1
		self.overlap_thinking_wrapper=Frame(self)
		self.overlap_thinking_wrapper.grid(row=row,column=1,columnspan=2,sticky=W)
		self.overlap_thinking_widgets=[]
		
		self.no_overlap_thinking = BooleanVar(value=grp_config.getboolean("Live","NoOverlap"))
		
		row+=1
		Label(self,text="").grid(row=row,column=1)


		row+=1

		notebook=Notebook(self)
		self.notebook=notebook
		notebook.grid(row=row,column=1,columnspan=2,sticky=W+E)
		
		tab1=Frame(notebook)
		newgame_frame=Frame(tab1)
		newgame_frame.pack(fill=X,pady=10)
		notebook.add(tab1, text=_("New game"))

		row+=1
		Label(newgame_frame,text=_("Board size")).grid(row=row,column=1,sticky=W,padx=10)
		self.dim=Entry(newgame_frame)
		self.dim.grid(row=row,column=2,sticky=W)
		self.dim.delete(0, END)
		self.dim.insert(0, grp_config.get("Live", "size"))
		#row+=1
		#Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(newgame_frame,text=_("Komi")).grid(row=row,column=1,sticky=W,padx=10)
		self.komi=Entry(newgame_frame)
		self.komi.grid(row=row,column=2,sticky=W)
		self.komi.delete(0, END)
		self.komi.insert(0, grp_config.get("Live", "komi"))
		#row+=1
		#Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(newgame_frame,text=_("Handicap stones")).grid(row=row,column=1,sticky=W,padx=10)
		self.handicap=Entry(newgame_frame)
		self.handicap.grid(row=row,column=2,sticky=W)
		self.handicap.delete(0, END)
		self.handicap.insert(0, grp_config.get("Live", "handicap"))
		
		tab2=Frame(notebook)
		existinggame_frame=Frame(tab2)
		existinggame_frame.pack(fill=X,pady=10)
		notebook.add(tab2, text=_("From existing game"))
		
		self.notebook=notebook
		
		Label(existinggame_frame,text=_("Select a game record")+":").grid(row=row,column=1,sticky=W,padx=10)
		self.existing_game=Entry(existinggame_frame)
		self.existing_game.grid(row=row,column=2,sticky=W)
		self.existing_game.bind("<Button-1>",self.change_existing_game)
		
		row+=1
		Label(existinggame_frame,text=_("Select starting position:")+" "+_("Move")).grid(row=row,column=1,sticky=W,padx=10)
		self.existing_position=Entry(existinggame_frame)
		self.existing_position.grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("SGF file name")).grid(row=row,column=1,sticky=W)
		self.filename=Entry(self)
		self.filename.grid(row=row,column=2,sticky=W)
		self.filename.delete(0, END)
		filename=datetime.now().strftime('%Y-%m-%d_%H-%M_')+_('Human player')+'_vs_'+_('Human player')+'.sgf'
		self.filename.insert(0, filename)
		self.filename.bind("<Button-1>",self.change_filename)

		row+=1
		Label(self,text=_("Select colors to be analysed")).grid(row=row,column=1,sticky=W)

		self.color = StringVar()
		self.color.set("both")
		row+=1
		c0=Radiobutton(self,text=_("Black & white"),variable=self.color, value="both")
		c0.grid(row=row,column=1,sticky=W)
		self.after(0,c0.select)
		row+=1
		c1=Radiobutton(self,text=_("Black only"),variable=self.color, value="black")
		c1.grid(row=row,column=1,sticky=W)

		row+=1
		c2=Radiobutton(self,text=_("White only"),variable=self.color, value="white")
		c2.grid(row=row,column=1,sticky=W)
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1		
		Button(self,text=_("Start"),command=self.start).grid(row=row,column=2,sticky=E)

		self.bot_selection.set(self.analysis_bots_names[0])
		self.black_selection.set(_("Human player"))
		self.white_selection.set(_("Human player"))
		
		analyser=grp_config.get("Live","Analyser")
		if analyser in self.analysis_bots_names:
			self.bot_selection.set(analyser)
		self.change_parameters()
		
		black=grp_config.get("Live","black")
		if black in self.black_options:
			self.black_selection.set(black)
			
		white=grp_config.get("Live","white")
		if white in self.white_options:
			self.white_selection.set(white)
			
		self.change_parameters()
		
		self.bot_selection.trace("w", lambda a,b,c: self.change_parameters())
		self.black_selection.trace("w", lambda a,b,c: self.change_parameters())
		self.white_selection.trace("w", lambda a,b,c: self.change_parameters())
	
	def change_existing_game(self,event=None):
		filename=open_sgf_file(parent=self)
		if filename:
			try:
				sgfgame=open_sgf(filename)
				move_zero=sgfgame.get_root()
				nb_moves=get_moves_number(move_zero)
				
				self.existing_game.delete(0, END)
				self.existing_game.insert(0, filename)
				
				self.existing_position.delete(0, END)
				self.existing_position.insert(0, str(nb_moves+1))
			except Exception, e:
				print e
				show_error(_("Could not read file")+" \""+os.path.basename(filename)+"\":\n"+unicode(e),parent=self)
				
	def change_filename(self,event=None):
		filename=save_live_game(self.filename.get(), parent=self)
		if filename:
			filename=os.path.basename(filename)
			self.filename.delete(0, END)
			self.filename.insert(0, filename)
		
	def close(self):
		self.destroy()
		self.parent.remove_popup(self)
		
	def start(self):
		
		bots={bot['name']+" - "+bot['profile']:bot for bot in get_available()+get_gtp_bots()}
		analyser=bots[self.bot_selection.get()]

		b=self.selected_black_index()
		if b==0:
			black="human"
		elif b==1:
			black="analyser"
		else:
			black=bots[self.black_selection.get()]
		
		w=self.selected_white_index()
		if w==0:
			white="human"
		elif w==1:
			white="analyser"
		elif w==b:
			white="black"
		else:
			white=bots[self.white_selection.get()]
		
		grp_config.set("Live","analyser",self.bot_selection.get())
		grp_config.set("Live","black",self.black_selection.get())
		grp_config.set("Live","white",self.white_selection.get())
		
		filename=os.path.join(grp_config.get("General","livefolder"),self.filename.get())
		
		if self.notebook.index("current")==0:
			log("Starting a live game from scratch")
		
			komi=float(self.komi.get())
			dim=int(self.dim.get())
			handicap=int(self.handicap.get())
			
			grp_config.set("Live","komi",komi)
			grp_config.set("Live","size",dim)
			grp_config.set("Live","handicap",handicap)
			
			self.withdraw()
			popup=LiveAnalysis(self.parent,analyser,black,white,dim=dim,komi=komi,handicap=handicap,filename=filename,overlap_thinking=not self.no_overlap_thinking.get(),color=self.color.get())
			self.parent.add_popup(popup)
			self.close()
			
		else:
			try:
				sgfgame=open_sgf(self.existing_game.get())
				move_zero=sgfgame.get_root()
				nb_moves=get_moves_number(move_zero)
			except Exception, e:
				show_error(unicode(e))
				return
				
			try:
				if (int(self.existing_position.get()) < 1) or (int(self.existing_position.get()) > nb_moves+1):
					show_error(_("Move position out of range"))
					return
			except Exception, e:
				show_error(_("Incorrect move position")+"\n"+unicode(e))
				return
				
			log("Starting a live game from an existing position")
			self.withdraw()
			popup=LiveAnalysisFromExistingGame(self.parent,analyser,black,white,existing_game=self.existing_game.get(),starting_position=int(self.existing_position.get()),filename=filename,overlap_thinking=not self.no_overlap_thinking.get(),color=self.color.get())
			self.parent.add_popup(popup)
			self.close()


	def selected_black_index(self):
		i=0
		for bo in self.black_options:
			if bo==self.black_selection.get():
				return i
			i+=1

	def selected_white_index(self):
		i=0
		for wo in self.white_options:
			if wo==self.white_selection.get():
				return i
			i+=1

	def update_black_white_options(self):
		i=self.selected_black_index()
		self.black_options=[_("Human player"),_("Bot used for analysis")+": "+self.bot_selection.get()]+self.bots_names+self.gtp_bots_names
		self.black_menu.pack_forget()
		self.black_menu=apply(OptionMenu,(self.black_selection_wrapper,self.black_selection)+tuple(self.black_options))
		self.black_menu.pack()
		self.black_selection.set(self.black_options[i])

		j=self.selected_white_index()
		self.white_options=[_("Human player"),_("Bot used for analysis")+": "+self.bot_selection.get()]+self.bots_names+self.gtp_bots_names
		self.white_menu.pack_forget()
		self.white_menu=apply(OptionMenu,(self.white_selection_wrapper,self.white_selection)+tuple(self.white_options))
		self.white_menu.pack()
		self.white_selection.set(self.white_options[j])
		
		if i==1:
			black=self.bot_selection.get()
		else:
			black=self.black_selection.get()
			
		if j==1:
			white=self.bot_selection.get()
		else:
			white=self.white_selection.get()
			
		self.filename.delete(0, END)
		filename=datetime.now().strftime('%Y-%m-%d_%H-%M_')+black+'_vs_'+white+'.sgf'
		self.filename.insert(0, filename)

	def change_parameters(self):
		log("Bot selected for analysis is",self.bot_selection.get())
		self.update_black_white_options()
		self.update_overlap_thinking_option()
	
	def update_overlap_thinking_option(self):
		i=self.selected_black_index()
		j=self.selected_white_index()
		print i,j
		if i<=1 and j<=1:
			nb_bots=1
			print "a"
		elif (i>1 and j<=1) or (j>1 and i<=1):
			nb_bots=2
			print "b"
		elif (i>1 and j>1 and i==j):
			nb_bots=2
			print "c"
		elif (i>1 and j>1 and i!=j):
			nb_bots=3
			print "d"
		
		for widget in self.overlap_thinking_widgets:
			widget.grid_forget()
		self.overlap_thinking_widgets=[]
		
		if nb_bots>1:
			row=0
			
			row+=1
			widget=Label(self.overlap_thinking_wrapper,text=_("No overlap thinking time"))
			widget.grid(row=row,column=1,sticky=W)
			self.overlap_thinking_widgets.append(widget)
			
			widget=Checkbutton(self.overlap_thinking_wrapper, text="", variable=self.no_overlap_thinking,onvalue=True,offvalue=False)
			widget.grid(row=row,column=2,sticky=W)
			self.overlap_thinking_widgets.append(widget)

	

class LiveAnalysis(Toplevel):
	def __init__(self,parent,analyser=None,black=None,white=None,dim=19,komi=6.5,handicap=0,filename="Live.sgf",overlap_thinking=False,color="both"):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.dim=dim
		self.komi=komi
		self.handicap=handicap
		self.filename=filename
		import goban
		goban.fuzzy=grp_config.getfloat("Review", "FuzzyStonePlacement")
		self.rsgf_filename=".".join(filename.split(".")[:-1])+".rsgf"
		self.sgf_filename=".".join(filename.split(".")[:-1])+".sgf"
		self.overlap_thinking=overlap_thinking
		self.color=color
		
		self.analyser=analyser
		self.black=black
		self.white=white
		
		self.black_just_passed=False
		self.white_just_passed=False
		
		self.initialize()

	def save_as_png(self,event=None):
		filename=save_png_file(filename='move'+str(self.current_move)+'.png',parent=self)
		self.goban.parent=self
		canvas2png(self.goban,filename)

	def open_move(self):
		from dual_view import OpenMove
		log("Opening move",self.current_move)

		new_popup=OpenMove(self.parent,self.current_move,self.dim,self.g)
		new_popup.goban.mesh=self.goban.mesh
		new_popup.goban.wood=self.goban.wood
		new_popup.goban.black_stones=self.goban.black_stones_style
		new_popup.goban.white_stones=self.goban.white_stones_style
		
		new_popup.goban.reset()
		
		self.parent.after(100,lambda :new_popup.goban.display(new_popup.grid,new_popup.markup))
		
		self.parent.add_popup(new_popup)
	
	def refocus(self,widget):
		widget.focus()
	
	def new_goban(self,event=None):
		new_tab=InteractiveGoban(self.notebook,self.current_move,self.dim,self.g)
		new_tab.status_bar=self.status_bar
		new_tab.goban.space=self.goban.space
		
		new_tab.goban.mesh=self.goban.mesh
		new_tab.goban.wood=self.goban.wood
		new_tab.goban.black_stones=self.goban.black_stones_style
		new_tab.goban.white_stones=self.goban.white_stones_style
		new_tab.goban.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		new_tab.bind("<Visibility>",lambda event: self.refocus(new_tab))
		
		self.opened_tabs.append(new_tab)
		
		pos=len(self.notebook.tabs())-1
		self.notebook.insert(pos,new_tab, text=str(self.current_move))
		self.notebook.select(pos)

		new_tab.close_button.config(command=lambda: self.close_tab(new_tab))


	def close_tab(self, tab):
		id=self.notebook.index("current")
		log("closing tab", id)
		self.notebook.select(id-1)
		self.notebook.forget(id)
		tab.close()
		self.opened_tabs.remove(tab)
	
	def initialize(self):
		popup=self
		buttons_with_status=[]
		dim=self.dim
		self.opened_tabs=[]
		#popup.configure(background=bg)
		bg=popup.cget("background")
		panel=Frame(popup, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		display_factor=grp_config.getfloat("Live", "LiveGobanRatio")
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		self.goban_size=min(width,height)
		notebook=Notebook(popup)
		self.notebook=notebook
		notebook.grid(column=2,row=1,rowspan=2,sticky=N+S+E+W)
		
		live_tab=Frame(notebook)
		live_tab.bind("<Visibility>",lambda event: self.refocus(live_tab))
		
		toolbar=Frame(live_tab)
		toolbar.pack(fill=X)
		
		goban = Goban(dim,self.goban_size,master=live_tab,bg=bg,bd=0, borderwidth=0)
		goban.space=self.goban_size/(dim+1+1+1)
		goban.pack(fill=BOTH, expand=1)
		notebook.add(live_tab, text=_("Live game"))
		goban.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		buttons_with_status.append(goban)
		
		plus_tab=Frame(notebook)
		notebook.add(plus_tab, text="+")
		plus_tab.bind("<Visibility>",self.new_goban)

		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		grid=[[0 for r in range(dim)] for c in range(dim)]
		markup=[["" for r in range(dim)] for c in range(dim)]
		
		self.goban=goban
		self.grid=grid
		self.markup=markup

		self.history=[]

		self.g = sgf.Sgf_game(size=self.dim)
		node_set(self.g.get_root(),"KM", self.komi)
		self.g_lock=Lock()
		self.g.lock=self.g_lock
		
		#self.analyser=self.analyser[0](self.g,self.filename)
		self.analyser=self.analyser["liveanalysis"](self.g,self.rsgf_filename,self.analyser)
		
		first_comment=_("Analysis by GoReviewPartner")
		first_comment+="\n"+("Bot: %s/%s"%(self.analyser.bot.bot_name,self.analyser.bot.bot_version))
		first_comment+="\n"+("Komi: %0.1f"%self.komi)

		if grp_config.getboolean('Analysis', 'SaveCommandLine'):
			first_comment+="\n"+("Command line: %s"%self.analyser.bot.command_line)

		node_set(self.g.get_root(),"RSGF",first_comment+"\n")
		node_set(self.g.get_root(),"BOT",self.analyser.bot.bot_name)
		node_set(self.g.get_root(),"BOTV",self.analyser.bot.bot_version)
		
		self.cpu_lock=Lock()
		if not self.overlap_thinking:
			self.analyser.cpu_lock=self.cpu_lock #analyser and bot share the same cpu lock
		
		self.analyser.start()
			
		if type(self.black)!=type("abc"):
			#black is neither human nor analyser
			#so it's a bot
			log("Starting bot for black")
			#self.black=bot_starting_procedure(self.black[2],self.black[3],self.black[1],self.g,profil="fast")
			self.black=self.black["starting"](self.g,profile=self.black)
			log("Black bot started")
		
		
		if type(self.white)!=type("abc"):
			#white is neither human nor analyser not black
			#so it's a bot
			log("Starting bot for white")
			#self.white=bot_starting_procedure(self.white[2],self.white[3],self.white[1],self.g,profil="fast")
			self.white=self.white["starting"](self.g,profile=self.white)
			log("White bot started")
		

		
		row=1
		Label(panel,text=_("Game"), font="-weight bold").grid(column=1,row=row,sticky=W)

		row+=1
		if self.black=="human":
			player_black=_("Human player")
		elif self.black=="analyser":
			player_black=self.analyser.bot.bot_name
		else:
			player_black=self.black.bot_name
			
		self.game_label=Label(panel,text=_("Black")+": "+player_black)
		self.game_label.grid(column=1,row=row,sticky=W)
		node_set(self.g.get_root(),"PB",player_black)
		
		row+=1
		if self.white=="human":
			player_white=_("Human player")
		elif self.white=="analyser":
			player_white=self.analyser.bot.bot_name
		elif self.white=="black":
			player_white=player_black
		else:
			player_white=self.white.bot_name
			
		self.game_label=Label(panel,text=_("White")+": "+player_white)
		self.game_label.grid(column=1,row=row,sticky=W)
		node_set(self.g.get_root(),"PW",player_white)
		
		row+=1
		self.game_label=Label(panel,text=_("Komi")+": "+str(self.komi))
		self.game_label.grid(column=1,row=row,sticky=W)

		row+=1
		self.game_label=Label(panel,text=_("Currently at move %i")%1)
		self.game_label.grid(column=1,row=row,sticky=W)
		
		
		row+=1
		self.pass_button=Button(toolbar,text=_("Pass"),state="disabled",command=self.player_pass)
		self.pass_button.bind("<Enter>",lambda e: self.set_status(_("Pass for this move")))
		buttons_with_status.append(self.pass_button)
		
		self.undo_button=Button(toolbar,text=_("Undo"),state="disabled")
		self.undo_button.bind("<Enter>",lambda e: self.set_status(_("Undo to previous move")))
		buttons_with_status.append(self.undo_button)
		
		if (self.black=="human") or (self.white=="human"):
			self.pass_button.pack(side=LEFT)
			self.undo_button.pack(side=LEFT)
		row+=1
		if (self.black!="human") and (self.white!="human"):
			row+=1
			self.pause_button=Button(toolbar,text=_("Pause"),command=self.pause)
			self.pause_button.pack(side=LEFT)
			self.pause_button.bind("<Enter>",lambda e: self.set_status(_("Pause the game")))
			buttons_with_status.append(self.pause_button)
		self.pause_lock=Lock()
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis"), font="-weight bold").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis by %s")%self.analyser.bot.bot_name).grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Status:")).grid(column=1,row=row,sticky=W)
		
		row+=1
		self.analysis_label=Label(panel,text=_("Ready to start"))
		self.analysis_label.grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,fg=bg,text=_("Currently at move %i")%1000).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		row+=1
		Label(panel,fg=bg,text=_("Waiting for next move")).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		self.review_bouton_wrapper=Frame(panel)
		self.review_bouton_wrapper.grid(column=1,row=row,sticky=W+E)
		
		self.status_bar=Label(self,text='',background=bg)
		self.status_bar.grid(column=1,row=3,sticky=W,columnspan=2)
		
		for button in buttons_with_status:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		self.protocol("WM_DELETE_WINDOW", self.close)
		self.parent.after(500,self.follow_analysis)
	
		self.bind('<Control-q>', self.save_as_png)
	
		self.goban.bind("<Configure>",self.redraw)
		
		popup.focus()
		self.locked=False
		
		self.goban.bind("<Button-3>",self.shine)

		#self.starting()
		self.after(500, self.starting)

	def starting(self):
		if self.handicap>0:
			self.handicap_stones=[]
			self.history.append(None)
			show_info(_("Please place %i handicap stones on the board.")%self.handicap,self)
			self.goban.bind("<Button-1>",lambda e: self.place_handicap(e,self.handicap))
			
		else:
			self.next_color=1		
			self.current_move=1
			node_set(self.g.get_root(),"PL", "b")
			self.save_sgf()
			self.black_to_play()
		
	def save_sgf(self):
		try:
			write_rsgf(self.rsgf_filename,self.g)
		except Exception, e:
			log("Could not save the RSGF file!")
			log(e)
			log("\a")
		self.g_lock.acquire()
		try:
			sgf_game = sgf.Sgf_game(size=self.dim)
			node_set(sgf_game.get_root(),"KM", self.komi)
			try:
				node_set(sgf_game.get_root(),"AB",self.handicap_stones)
			except:
				pass
			node_set(sgf_game.get_root(),"PB",node_get(self.g.get_root(),"PB"))
			node_set(sgf_game.get_root(),"PW",node_get(self.g.get_root(),"PW"))
			for node in self.g.get_main_sequence():
				move=node.get_move()
				if "b" in move:
					move=move[1]
					new_node=sgf_game.extend_main_sequence()
					node_set(new_node,"b",move)
				elif "w" in move:
					move=move[1]
					new_node=sgf_game.extend_main_sequence()
					node_set(new_node,"w",move)
			write_rsgf(self.sgf_filename,sgf_game)
		except Exception, e:
			log("Could not save the SGF file!")
			log(e)
			log("\a")
		self.g_lock.release()
	
	def set_status(self,msg):
		self.status_bar.config(text=msg)
		
	def clear_status(self):
		self.status_bar.config(text="")

	def close(self):
		log("Closing analyser bot")
		self.game_label.config(text=_("Now closing, please wait..."))
		self.analysis_label.config(text=_("Now closing, please wait..."))
		log("Sending None msg to analyser")
		self.analyser.update_queue.put((0,None))
		if type(self.black)!=type("abc"):
			log("Closing black bot")
			self.black.close()
		if type(self.white)!=type("abc"):
			log("Closing white bot")
			self.white.close()
		
		self.analyser.bot.close()
		
		for tab in self.opened_tabs:
			tab.close()
		
		self.destroy()
		self.parent.remove_popup(self)
		
	def pause(self):
		if self.pause_button.cget("relief")!=SUNKEN:
			log("Pausing the game")
			self.pause_button.config(relief=SUNKEN)
			self.pause_button.config(text=_("Resume"))
			self.pause_lock.acquire()
			log("Game paused")
		else:
			log("Resuming the game")
			self.pause_button.config(relief=RAISED)
			self.pause_button.config(text=_("Pause"))
			self.pause_lock.release()
			log("Game resumed")
		
	def start_review(self):
		import dual_view
		new_popup=dual_view.DualView(self.parent,self.rsgf_filename)
		self.parent.add_popup(new_popup)

	def follow_analysis(self):
		msg=None
		try:
			msg=self.analyser.label_queue.get(False)
			if type(msg)==type(123):
				self.analysis_label.config(text=_("Currently at move %i")%msg)
				if msg>2 and len(self.review_bouton_wrapper.children)==0:
					button=Button(self.review_bouton_wrapper,text=_("Start the review"),command=self.start_review)
					button.pack(fill=X)
					button.bind("<Enter>",lambda e: self.set_status(_("Start the review")))
					button.bind("<Leave>",lambda e: self.clear_status())
			else:
				self.analysis_label.config(text=_("Waiting for next move"))
				

			
		except:
			pass
		
		if msg==None:
			self.parent.after(500,self.follow_analysis)
		else:
			self.parent.after(10,self.follow_analysis)

	def place_handicap(self,event,handicap):
		dim=self.dim
		#add/remove black stone
		#check pointer location
		i,j=self.goban.xy2ij(event.x,event.y)
		if 0 <= i <= dim-1 and 0 <= j <= dim-1:
			#inside the grid
			#what is under the pointer ?
			
			if self.grid[i][j] not in (1,2):
				
				self.history[0]=[copy(self.grid),copy(self.markup)]
				place(self.grid,i,j,1)
				
				self.grid[i][j]=1
				self.markup=[["" for r in range(dim)] for c in range(dim)]
				self.markup[i][j]=0
				self.goban.display(self.grid,self.markup)
				self.goban.black_stones[i][j].shine()
				self.stone_sound()
				
				self.handicap_stones.append([i,j])
					
				if handicap>1:
					self.goban.bind("<Button-1>",lambda e: self.place_handicap(e,handicap-1))
				else:
					node_set(self.g.get_root(),"AB",self.handicap_stones)
					self.save_sgf()
					self.analyser.bot.set_free_handicap([ij2gtp([i,j]) for i,j in self.handicap_stones])
					self.analyser.handicap_stones=self.handicap_stones
					if type(self.black)!=type("abc"):
						self.black.set_free_handicap([ij2gtp([i,j]) for i,j in self.handicap_stones])
					if type(self.white)!=type("abc"):
						self.white.set_free_handicap([ij2gtp([i,j]) for i,j in self.handicap_stones])
						
					show_info(_("The game is now starting!"),self)
					self.next_color=2
					
					node_set(self.g.get_root(),"PL", "w")
					
					self.current_move=1
					self.white_to_play()
	
	def stone_sound(self):
		play_stone_sound()
		
	def gtp_thread_wrapper(self,bot,color):
		self.cpu_lock.acquire()
		if color=="black":
			answer=bot.play_black()
		else:
			answer=bot.play_white()
		threading.current_thread().answer=answer
		threading.current_thread().bot=bot
	
	def undo_as_black(self, event=None):
		if self.undo_button.cget("state")=='disabled':
			return
		log("Black undo from move",self.current_move,"back to move",self.current_move-2)
		self.undo_button.config(state='disabled')
		self.pass_button.config(state='disabled')
		self.goban.display(self.grid,self.markup,freeze=True)
		self.parent.after(100,self.undo)
		#self.undo()

	def undo_as_white(self, event=None):
		if self.undo_button.cget("state")=='disabled':
			return
		log("White undo from move",self.current_move,"back to move",self.current_move-2)
		self.undo_button.config(state='disabled')
		self.pass_button.config(state='disabled')
		self.goban.display(self.grid,self.markup,freeze=True)
		self.parent.after(100,self.undo)
		#self.undo()
		
	def undo(self):
		log("Let's wait for the analyser to stop")
		self.analyser.cpu_lock.acquire()
		log("Analyser is now stopped")
		log("Adding a new branch to the SGF tree")
		self.g.lock.acquire()
		new_branch=self.latest_node.parent.parent.parent.new_child(0)
		self.g.lock.release()
		
		move2undo=self.current_move-2
		
		log("Let's clean the analyser update_queue from requests for moves following move",move2undo)
		nb_request=self.analyser.update_queue.qsize()
		requests=[]
		for r in range(nb_request):
			priority,msg=self.analyser.update_queue.get()
			if type(msg)==type(123):
				if msg<=move2undo:
					log("keeping",(priority,msg))
					requests.append((priority,msg))
					#self.analyser.update_queue.put((priority,msg))
				else:
					log("discarding",(priority,msg))
			else:
				log("keeping",(priority,msg))
				requests.append((priority,msg))
		for r in requests:
			self.analyser.update_queue.put(r)
		
		log("Sending a priority request to undo move",move2undo,"and beyong to analyser")
		msg1=(1./move2undo,"undo "+str(move2undo))
		self.analyser.update_queue.put(msg1)
		log("Releasing the analyser")
		self.analyser.cpu_lock.release()
		
		self.latest_node=new_branch
		if type(self.black)!=type("abc"):
			#black is a bot
			self.black.undo()
			self.black.undo()
		if type(self.white)!=type("abc"):
			#white is a bot
			self.white.undo()
			self.white.undo()
		self.history.pop()
		self.grid,self.markup=self.history.pop()
		self.current_move-=2
		self.game_label.config(text=_("Currently at move %i")%self.current_move)
		self.save_sgf()
		log("waiting for echo")
		t0=time.time()
		msg2=None
		while msg2!=msg1:
			msg2=self.analyser.best_moves_queue.get()
			log("...............",msg2)
		log("echo received after",time.time()-t0,"s")
		self.parent.after(100,self.after_undo) #enough time for analyser to grab the process lock and process the queue
		
	def after_undo(self):
		self.pass_button.config(state='normal')
		if self.current_move>=3:
			self.undo_button.config(state='normal')	
		self.goban.display(self.grid,self.markup,freeze=False)


	def player_pass(self):
		log("The human is passing")
		color=self.next_color
		
		if color==1:
			if self.white_just_passed:
				log("End of the game")
				if type(self.white)!=type("abc"):
					#white is a bot
					result=self.white.final_score()
					show_info(self.white.bot_name+": "+result,parent=self)
				return
		elif color==2:
			if self.black_just_passed:
				log("End of the game")
				if type(self.black)!=type("abc"):
					#black is a bot
					result=self.black.final_score()
					show_info(self.black.bot_name+": "+result,parent=self)
				return

		
		self.next_color=3-color
		self.current_move+=1
		self.history.append([copy(self.grid),copy(self.markup)])
		self.markup=[["" for r in range(self.dim)] for c in range(self.dim)]
		self.goban.display(self.grid,self.markup)
		if color==1:
			self.g.lock.acquire()
			node_set(self.latest_node,'b',None)
			self.g.lock.release()
			self.black_just_passed=True
			if type(self.white)!=type("abc"):
				#white is a bot
				log("Asking white (%s) to play the game move"%self.white.bot_name)
				self.white.place_black("pass")
			self.white_to_play()
		else:
			self.g.lock.acquire()
			node_set(self.latest_node,'w',None)
			self.g.lock.release()
			self.white_just_passed=True
			if type(self.black)!=type("abc"):
				#black is a bot
				log("Asking black (%s) to play the game move"%self.black.bot_name)
				self.black.place_white("pass")
			self.black_to_play()
				
	def bot_to_play(self):
		
		self.gtp_thread.join(0.0)
		
		if self.gtp_thread.is_alive():
			#the bot is still thinking
			self.parent.after(250,self.bot_to_play)
			return
		self.cpu_lock.release()
		move=self.gtp_thread.answer
		
		color=self.next_color
		if move=="RESIGN":
			log("The bot is resigning")
			self.goban.display(self.grid,self.markup)
			if color==1:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+move,parent=self)
				return
			elif color==2:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("White")+"): "+move,parent=self)
				return
		elif move=="PASS":
			log("The bot is passing")
			if color==1:
				show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+move,parent=self)
				if self.white_just_passed:
					self.goban.display(self.grid,self.markup)
					result=self.gtp_thread.bot.final_score()
					show_info(self.gtp_thread.bot.bot_name+" ("+_("Black")+"): "+result,parent=self)
					return
			elif color==2:
				show_info(self.gtp_thread.bot.bot_name+": "+move,parent=self)
				if self.black_just_passed:
					self.goban.display(self.grid,self.markup)
					result=self.gtp_thread.bot.final_score()
					show_info(self.gtp_thread.bot.bot_name+": "+result,parent=self)
					return
			self.next_color=3-color
			self.current_move+=1
			self.history.append([copy(self.grid),copy(self.markup)])
			self.markup=[["" for r in range(self.dim)] for c in range(self.dim)]
			self.goban.display(self.grid,self.markup,freeze=True)
			if color==1:
				self.g.lock.acquire()
				node_set(self.latest_node,'b',None)
				self.g.lock.release()
				self.black_just_passed=True
				if type(self.white)!=type("abc"):
					#white is a bot
					log("Asking white (%s) to play the game move"%self.white.bot_name)
					self.white.place_black("pass")
				self.white_to_play()
			else:
				self.g.lock.acquire()
				node_set(self.latest_node,'w',None)
				self.g.lock.release()
				self.white_just_passed=True
				if type(self.black)!=type("abc"):
					#black is a bot
					log("Asking black (%s) to play the game move"%self.black.bot_name)
					self.black.place_white("pass")
				self.black_to_play()
		else:
			i,j=gtp2ij(move)
			self.next_color=3-color
			self.current_move+=1
			self.game_label.config(text=_("Currently at move %i")%self.current_move)
			
			self.history.append([copy(self.grid),copy(self.markup)])
			place(self.grid,i,j,color)
			self.grid[i][j]=color
			self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
			self.markup[i][j]=0
			self.goban.display(self.grid,self.markup,freeze=True)
			if color==1:
				self.goban.black_stones[i][j].shine()
			else:
				self.goban.white_stones[i][j].shine()
			self.stone_sound()
			if color==1:
				#black juste played
				self.g.lock.acquire()
				node_set(self.latest_node,'b',(i,j))
				self.g.lock.release()
				self.black_just_passed=False
				if type(self.white)!=type("abc"):
					#white is a bot
					log("Asking white (%s) to play the game move"%self.white.bot_name)
					self.white.place_black(ij2gtp((i,j)))
				self.white_to_play()
			else:
				#white just played
				self.g.lock.acquire()
				node_set(self.latest_node,'w',(i,j))
				self.g.lock.release()
				self.white_just_passed=False
				if (type(self.black)!=type("abc")) and (self.white!="black"):
					#white and black are different bots
					log("Asking black (%s) to play the game move"%self.black.bot_name)
					self.black.place_white(ij2gtp((i,j)))
				self.black_to_play()
		
	def black_to_play(self):
		result=self.pause_lock.acquire(False)
		if not result:
			self.parent.after(250,self.black_to_play)
			return
		self.pause_lock.release()
		self.save_sgf()
		log("======== move %i ========="%self.current_move)
		log("black to play")
		
		self.g.lock.acquire()
		self.latest_node = self.g.extend_main_sequence()
		self.g.lock.release()
		if self.color!="white":
			log("Sending request to analyse move",self.current_move,"to analyser")
			self.analyser.update_queue.put((self.current_move,self.current_move))
		self.pass_button.config(state='disabled')
		self.undo_button.config(state='disabled')
		if self.black=="human":
			thinkbeforeplaying=grp_config.getfloat("Live","ThinkBeforePlaying")
			self.goban.display(self.grid,self.markup,freeze=False)
			if not thinkbeforeplaying:
				self.goban.bind("<Button-1>",self.click)
			else:
				self.goban.config(cursor="watch")
				log("Think",thinkbeforeplaying,"s before playing")
				self.after(int(thinkbeforeplaying*1000),lambda: self.goban.bind("<Button-1>",self.click))
				self.after(int(thinkbeforeplaying*1000),lambda: self.goban.config(cursor="cross"))
			self.pass_button.config(state='normal')
			if self.current_move>=3:
				self.undo_button.config(state='normal',command=self.undo_as_black)
				self.goban.bind("<Button-2>",self.undo_as_black)
			
		elif self.black=="analyser":
			self.goban.bind("<Button-1>",self.do_nothing)
			self.goban.display(self.grid,self.markup,freeze=True)
			self.analyser_to_play()
		else:
			#black is a bot
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting black gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.black,"black"))
			self.gtp_thread.start()
			self.goban.display(self.grid,self.markup,freeze=True)
			self.bot_to_play()
	
	def white_to_play(self):
		result=self.pause_lock.acquire(False)
		if not result:
			self.parent.after(250,self.white_to_play)
			return
		self.pause_lock.release()
		self.save_sgf()
		log("======== move %i ========="%self.current_move)
		log("White to play")
		
		self.g.lock.acquire()
		self.latest_node = self.g.extend_main_sequence()
		self.g.lock.release()
		if self.color!="black":
			log("Sending request to analyse move",self.current_move,"to analyser")
			self.analyser.update_queue.put((self.current_move,self.current_move))
		self.pass_button.config(state='disabled')
		self.undo_button.config(state='disabled')
		if self.white=="human":
			thinkbeforeplaying=grp_config.getfloat("Live","ThinkBeforePlaying")
			self.goban.display(self.grid,self.markup,freeze=False)
			if not thinkbeforeplaying:
				self.goban.bind("<Button-1>",self.click)
			else:
				self.goban.config(cursor="watch")
				log("Think",thinkbeforeplaying,"s before playing")
				self.after(int(thinkbeforeplaying*1000),lambda: self.goban.bind("<Button-1>",self.click))
				self.after(int(thinkbeforeplaying*1000),lambda: self.goban.config(cursor="cross"))
			self.pass_button.config(state='normal')
			if self.current_move>=3:
				self.undo_button.config(state='normal',command=self.undo_as_white)
				self.goban.bind("<Button-2>",self.undo_as_white)
		elif self.white=="analyser":
			self.goban.bind("<Button-1>",self.do_nothing)
			self.goban.display(self.grid,self.markup,freeze=True)
			self.analyser_to_play()
		elif self.white=="black":
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting white gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.black,"white"))
			self.gtp_thread.start()
			self.bot_to_play()
		else:
			#white is a bot
			self.goban.bind("<Button-1>",self.do_nothing)
			log("Starting white gtp thread")
			self.gtp_thread=threading.Thread(target=self.gtp_thread_wrapper,args=(self.white,"white"))
			self.gtp_thread.start()
			self.goban.display(self.grid,self.markup,freeze=True)
			self.bot_to_play()
	
	def analyser_to_play(self):
		try:
			msg=self.analyser.best_moves_queue.get(False)
		except:
			self.parent.after(250,self.analyser_to_play)
			return
		log("received msg from analyser:",msg)
		number,move=msg
		if number<self.current_move:
			log("msg received by analyser is for previous move")
			log("analyser needs to wait for a new message")
			self.parent.after(1,self.analyser_to_play)
		elif number>self.current_move:
			log("msg received by analyser is for next move")
			log("probably a canceled move")
			log("analyser needs to wait for a new message")
			self.parent.after(1,self.analyser_to_play)
		elif number==self.current_move:
			log("this is the message expected from analyser")
			color=self.next_color
			if move=="RESIGN":
				log("The analyser is resigning")
				self.goban.display(self.grid,self.markup)
				if color==1:
					show_info(self.analyser.bot.bot_name+" ("+_("Black")+"): "+move,parent=self)
					return
				elif color==2:
					show_info(self.analyser.bot.bot_name+" ("+_("White")+"): "+move,parent=self)
					return
			elif move=="PASS":
				log("The analyser is passing")
				if color==1:
					show_info(self.analyser.bot.bot_name+" ("+_("Black")+"): "+move,parent=self)
					if self.white_just_passed:
						self.goban.display(self.grid,self.markup)
						result=self.analyser.bot.final_score()
						show_info(self.analyser.bot.bot_name+" ("+_("Black")+"): "+result,parent=self)
						return
				elif color==2:
					show_info(self.analyser.bot.bot_name+" ("+_("White")+"): "+move,parent=self)
					if self.black_just_passed:
						self.goban.display(self.grid,self.markup)
						result=self.analyser.bot.final_score()
						show_info(self.analyser.bot.bot_name+": "+result,parent=self)
						return
				self.next_color=3-color
				self.current_move+=1
				self.history.append([copy(self.grid),copy(self.markup)])
				self.markup=[["" for r in range(self.dim)] for c in range(self.dim)]
				self.goban.display(self.grid,self.markup,freeze=True)
				if color==1:
					self.g.lock.acquire()
					node_set(self.latest_node,'b',None)
					self.g.lock.release()
					self.black_just_passed=True
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black("pass")
					self.white_to_play()
				else:
					self.g.lock.acquire()
					node_set(self.latest_node,'w',None)
					self.g.lock.release()
					self.white_just_passed=True
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white("pass")
					self.black_to_play()
			else:
				i,j=gtp2ij(move)
				self.next_color=3-color
				self.current_move+=1
				self.game_label.config(text=_("Currently at move %i")%self.current_move)
				
				self.history.append([copy(self.grid),copy(self.markup)])
				place(self.grid,i,j,color)
				self.grid[i][j]=color
				self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
				self.markup[i][j]=0
				self.goban.display(self.grid,self.markup,freeze=True)
				if color==1:
					self.goban.black_stones[i][j].shine()
				else:
					self.goban.white_stones[i][j].shine()
				self.stone_sound()
				if color==1:
					self.g.lock.acquire()
					node_set(self.latest_node,'b',(i,j))
					self.g.lock.release()
					self.black_just_passed=False
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black(ij2gtp((i,j)))
					self.white_to_play()
				else:
					self.g.lock.acquire()
					node_set(self.latest_node,'w',(i,j))
					self.g.lock.release()
					self.white_just_passed=False
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white(ij2gtp((i,j)))
					self.black_to_play()
			
			
	def do_nothing(self,event):
		pass

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
				#nothing, so we add a stone			
	
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
				self.stone_sound()
				self.next_color=3-color
				
				self.g.lock.acquire()
				node = self.latest_node
				if color==1:
					node_set(node,"b", (i,j))
				else:
					node_set(node,"w", (i,j))
				self.g.lock.release()
				
				
				self.current_move+=1
				self.game_label.config(text=_("Currently at move %i")%self.current_move)
				
				if self.next_color==1:
					self.white_just_passed=False
					if type(self.black)!=type("abc"):
						#black is a bot
						log("Asking black (%s) to play the game move"%self.black.bot_name)
						self.black.place_white(ij2gtp((i,j)))
					self.black_to_play()
				else:
					self.black_just_passed=False
					if type(self.white)!=type("abc"):
						#white is a bot
						log("Asking white (%s) to play the game move"%self.white.bot_name)
						self.white.place_black(ij2gtp((i,j)))
					self.white_to_play()
	
	def redraw(self, event, redrawing=None):		
		if not redrawing:
			redrawing=time.time()
			self.redrawing=redrawing
			self.after(200,lambda: self.redraw(event,redrawing))
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
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		ratio=1.0*new_size/min(screen_width,screen_height)
		grp_config.set("Live", "LiveGobanRatio",ratio)
			
		self.goban.space=new_space
		
		new_anchor_x=(event.width-new_size)/2.
		self.goban.anchor_x=new_anchor_x
		
		new_anchor_y=(event.height-new_size)/2.
		self.goban.anchor_y=new_anchor_y
		
		self.goban.reset()


class LiveAnalysisFromExistingGame(LiveAnalysis):
	def __init__(self,parent,analyser=None,black=None,white=None,existing_game=None,starting_position=None,filename="Live.sgf",overlap_thinking=False,color="both"):
		Toplevel.__init__(self,parent)
		self.parent=parent
		
		self.existing_game=existing_game
		self.starting_position=starting_position
		
		self.filename=filename
		import goban
		goban.fuzzy=grp_config.getfloat("Review", "FuzzyStonePlacement")
		self.rsgf_filename=".".join(filename.split(".")[:-1])+".rsgf"
		self.sgf_filename=".".join(filename.split(".")[:-1])+".sgf"
		self.overlap_thinking=overlap_thinking
		self.color=color
		
		self.analyser=analyser
		self.black=black
		self.white=white
		
		self.black_just_passed=False
		self.white_just_passed=False
		
		self.initialize()


	def initialize(self):
		
		sgfgame=open_sgf(self.existing_game)
		sgf_moves.indicate_first_player(sgfgame)
		move_zero=sgfgame.get_root()
		nb_moves=get_moves_number(move_zero)
		self.komi=sgfgame.get_komi()
		self.dim=sgfgame.get_size()
		dim=self.dim
		
		if self.starting_position<=nb_moves:
			one_node=get_node(move_zero,self.starting_position)
			one_node.delete()

		self.g = sgfgame
		
		popup=self
		buttons_with_status=[]
		self.opened_tabs=[]
		bg=popup.cget("background")
		panel=Frame(popup, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		
		panel.grid(column=1,row=1,sticky=N+S)
		
		display_factor=grp_config.getfloat("Live", "LiveGobanRatio")
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		self.goban_size=min(width,height)
		notebook=Notebook(popup)
		self.notebook=notebook
		notebook.grid(column=2,row=1,rowspan=2,sticky=N+S+E+W)
		
		live_tab=Frame(notebook)
		live_tab.bind("<Visibility>",lambda event: self.refocus(live_tab))
		
		toolbar=Frame(live_tab)
		toolbar.pack(fill=X)
		
		goban = Goban(dim,self.goban_size,master=live_tab,bg=bg,bd=0, borderwidth=0)
		goban.space=self.goban_size/(dim+1+1+1)
		goban.pack(fill=BOTH, expand=1)
		notebook.add(live_tab, text=_("Live game"))
		goban.bind("<Enter>",lambda e: self.set_status(_("<Ctrl+Q> to save the goban as an image.")))
		buttons_with_status.append(goban)
		
		plus_tab=Frame(notebook)
		notebook.add(plus_tab, text="+")
		plus_tab.bind("<Visibility>",self.new_goban)

		popup.grid_rowconfigure(1, weight=1)
		popup.grid_columnconfigure(2, weight=1)
		
		grid=[[0 for r in range(dim)] for c in range(dim)]
		markup=[["" for r in range(dim)] for c in range(dim)]
		
		#placing handicap stones
		board, unused = sgf_moves.get_setup_and_moves(self.g)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid,row,col,1)
			else:
				place(grid,row,col,2)
		
		#placing already played stones
		for m in range(1,self.starting_position):
			one_move=get_node(move_zero,m)
			ij=one_move.get_move()[1]
			if ij==None:
				continue #pass or resign move
			if one_move.get_move()[0]=='b':
				color=1
			else:
				color=2
			i,j=list(ij)
			place(grid,i,j,color)
		
		self.goban=goban
		self.grid=grid
		self.markup=markup

		self.history=[]

		self.g_lock=Lock()
		self.g.lock=self.g_lock
		
		#self.analyser=self.analyser[0](self.g,self.filename)
		self.analyser=self.analyser["liveanalysis"](self.g,self.rsgf_filename,self.analyser)
		
		
		first_comment=_("Analysis by GoReviewPartner")
		first_comment+="\n"+("Bot: %s/%s"%(self.analyser.bot.bot_name,self.analyser.bot.bot_version))
		first_comment+="\n"+("Komi: %0.1f"%self.komi)

		if grp_config.getboolean('Analysis', 'SaveCommandLine'):
			first_comment+="\n"+("Command line: %s"%self.analyser.bot.command_line)

		node_set(self.g.get_root(),"RSGF",first_comment+"\n")
		node_set(self.g.get_root(),"BOT",self.analyser.bot.bot_name)
		node_set(self.g.get_root(),"BOTV",self.analyser.bot.bot_version)
		
		self.cpu_lock=Lock()
		if not self.overlap_thinking:
			self.analyser.cpu_lock=self.cpu_lock #analyser and bot share the same cpu lock
		
		self.analyser.start()
			
		if type(self.black)!=type("abc"):
			#black is neither human nor analyser
			#so it's a bot
			log("Starting bot for black")
			self.black=self.black["starting"](self.g,profile=self.black)
			log("Black bot started")
		
		if type(self.white)!=type("abc"):
			#white is neither human nor analyser not black
			#so it's a bot
			log("Starting bot for white")
			self.white=self.white["starting"](self.g,profile=self.white)
			log("White bot started")

		self.next_color=None
		for node in self.g.get_main_sequence():
			move=node.get_move()
			if "b" in move:
				move=ij2gtp(move[1])
				self.analyser.bot.place_black(move)
				if type(self.black)!=type("abc"):
					self.black.place_black(move)
				if type(self.white)!=type("abc"):
					self.white.place_black(move)
				self.next_color=2
			elif "w" in move:
				move=ij2gtp(move[1])
				self.analyser.bot.place_white(move)
				if type(self.black)!=type("abc"):
					self.black.place_white(move)
				if type(self.white)!=type("abc"):
					self.white.place_white(move)
				self.next_color=1
		if not self.next_color:
			player_color=guess_color_to_play(move_zero,self.starting_position)
			log("Setting first color to play")
			if player_color.lower()=='b':
				self.next_color=1
			else:
				self.next_color=2
		row=1
		Label(panel,text=_("Game"), font="-weight bold").grid(column=1,row=row,sticky=W)

		row+=1
		if self.black=="human":
			player_black=_("Human player")
		elif self.black=="analyser":
			player_black=self.analyser.bot.bot_name
		else:
			player_black=self.black.bot_name
			
		self.game_label=Label(panel,text=_("Black")+": "+player_black)
		self.game_label.grid(column=1,row=row,sticky=W)
		node_set(self.g.get_root(),"PB",player_black)
		
		row+=1
		if self.white=="human":
			player_white=_("Human player")
		elif self.white=="analyser":
			player_white=self.analyser.bot.bot_name
		elif self.white=="black":
			player_white=player_black
		else:
			player_white=self.white.bot_name
			
		self.game_label=Label(panel,text=_("White")+": "+player_white)
		self.game_label.grid(column=1,row=row,sticky=W)
		node_set(self.g.get_root(),"PW",player_white)
		
		row+=1
		self.game_label=Label(panel,text=_("Komi")+": "+str(self.komi))
		self.game_label.grid(column=1,row=row,sticky=W)

		row+=1
		self.game_label=Label(panel,text=_("Currently at move %i")%1)
		self.game_label.grid(column=1,row=row,sticky=W)
		
		
		row+=1
		self.pass_button=Button(toolbar,text=_("Pass"),state="disabled",command=self.player_pass)
		self.pass_button.bind("<Enter>",lambda e: self.set_status(_("Pass for this move")))
		buttons_with_status.append(self.pass_button)
		
		self.undo_button=Button(toolbar,text=_("Undo"),state="disabled")
		self.undo_button.bind("<Enter>",lambda e: self.set_status(_("Undo to previous move")))
		buttons_with_status.append(self.undo_button)
		
		if (self.black=="human") or (self.white=="human"):
			self.pass_button.pack(side=LEFT)
			self.undo_button.pack(side=LEFT)
		row+=1
		if (self.black!="human") and (self.white!="human"):
			row+=1
			self.pause_button=Button(toolbar,text=_("Pause"),command=self.pause)
			self.pause_button.pack(side=LEFT)
			self.pause_button.bind("<Enter>",lambda e: self.set_status(_("Pause the game")))
			buttons_with_status.append(self.pause_button)
		self.pause_lock=Lock()
		Label(toolbar,text=" ", height=2).pack(side=LEFT)
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis"), font="-weight bold").grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Analysis by %s")%self.analyser.bot.bot_name).grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,text=_("Status:")).grid(column=1,row=row,sticky=W)
		
		row+=1
		self.analysis_label=Label(panel,text=_("Ready to start"))
		self.analysis_label.grid(column=1,row=row,sticky=W)
		
		row+=1
		Label(panel,fg=bg,text=_("Currently at move %i")%1000).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		row+=1
		Label(panel,fg=bg,text=_("Waiting for next move")).grid(column=1,row=row,sticky=W) #yes, this is a ugly hack :)
		
		row+=1
		Label(panel,text="").grid(column=1,row=row,sticky=W)
		
		row+=1
		self.review_bouton_wrapper=Frame(panel)
		self.review_bouton_wrapper.grid(column=1,row=row,sticky=W+E)
		
		self.status_bar=Label(self,text='',background=bg)
		self.status_bar.grid(column=1,row=3,sticky=W,columnspan=2)
		
		for button in buttons_with_status:
			button.bind("<Leave>",lambda e: self.clear_status())
		
		self.protocol("WM_DELETE_WINDOW", self.close)
		self.parent.after(500,self.follow_analysis)
	
		self.bind('<Control-q>', self.save_as_png)
	
		self.goban.bind("<Configure>",self.redraw)
		
		popup.focus()
		self.locked=False
		
		self.goban.bind("<Button-3>",self.shine)

		#self.starting()
		self.after(500, self.starting)

	def starting(self):
		self.current_move=self.starting_position
		self.save_sgf()
		if self.next_color==1:
			self.black_to_play()
		else:
			self.white_to_play()
		
	def save_sgf(self):
		try:
			write_rsgf(self.rsgf_filename,self.g)
		except Exception, e:
			log("Could not save the RSGF file!")
			log(e)
			log("\a")
		self.g_lock.acquire()
		try:
			sgf_game = sgf.Sgf_game(size=self.dim)
			node_set(sgf_game.get_root(),"KM", self.komi)
			#node_set(sgf_game.get_root(),"AB",self.handicap_stones)
			sgf_game.get_root().set_raw_list("AB",self.g.get_root().get_raw_list("AB"))
			node_set(sgf_game.get_root(),"PB",node_get(self.g.get_root(),"PB"))
			node_set(sgf_game.get_root(),"PW",node_get(self.g.get_root(),"PW"))
			for node in self.g.get_main_sequence():
				move=node.get_move()
				if "b" in move:
					move=move[1]
					new_node=sgf_game.extend_main_sequence()
					node_set(new_node,"b",move)
				elif "w" in move:
					move=move[1]
					new_node=sgf_game.extend_main_sequence()
					node_set(new_node,"w",move)
			write_rsgf(self.sgf_filename,sgf_game)
		except Exception, e:
			log("Could not save the SGF file!")
			log(e)
			log("\a")
		self.g_lock.release()

if __name__ == "__main__":
	top = Application()
	popup=LiveAnalysisLauncher(top)
	top.add_popup(popup)
	top.mainloop()
