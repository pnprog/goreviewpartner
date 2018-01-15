
class AbortedException(Exception):
    pass


def log(*args):
	for arg in args:
		try:
			try:
				arg=unicode(arg,errors='replace')
			except:
				pass
			try:
				arg=arg.encode(sys.stdout.encoding, 'replace')
			except:
				pass
			try:
				print arg,
			except:
				print "?"*len(arg),
		except:
			print "["+type()+"]",
	print

def linelog(*args):
	for arg in args:
		try:
			try:
				arg=unicode(arg,errors='replace')
			except:
				pass
			try:
				arg=arg.encode(sys.stdout.encoding, 'replace')
			except:
				pass
			try:
				print arg,
			except:
				print "?"*len(arg),
		except:
			print "["+type()+"]",

import tkMessageBox

def show_error(txt):
	try:
		tkMessageBox.showerror(_("Error"),txt)
		log("ERROR: "+txt)
	except:
		log("ERROR: "+txt)

def show_info(txt):
	try:
		tkMessageBox.showinfo(_("Information"),txt)
		log("INFO: "+txt)
	except:
		log("INFO: "+txt)

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
			log("return False")
			return False
		move=move[0]
		k+=1
	color=move.get_move()[0]
	if not color:
		log("SGF does not provive color information for move %d",move_number)
		previous_move=go_to_move(move_zero,move_number-1)
		previous_move_color=previous_move.get_move()[0]
		if previous_move_color.lower()=="b":
			log("=> it should be white to play")
			color="w"
		else:
			log("=> it should be black to play")
			color="b"
		move.set(color.upper(), move.get_move()[1])
	return move

def gtp2ij(move):
	try:
		#letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
		letters="abcdefghjklmnopqrstuvwxyz"
		return int(move[1:])-1,letters.index(move[0].lower())
	except:
		raise AbortedException("Cannot convert GTP coordinates "+move+" to grid coordinates!")

		


def ij2gtp(m):
	# (17,0) => a18
	try:
		if m==None:
			return "pass"
		i,j=m
		#letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
		letters="abcdefghjklmnopqrstuvwxyz"
		return letters[j]+str(i+1)
	except:
		raise AbortedException("Cannot convert grid coordinates "+str(m)+" to GTP coordinates!")


def ij2sgf(m):
	# (17,0) => ???
	try:
		if m==None:
			return "pass"
		i,j=m
		letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
		return letters[j]+letters[i]
	except:
		raise AbortedException("Cannot convert grid coordinates "+str(m)+" to SGF coordinates!")

from gomill import sgf, sgf_moves
from Tkinter import Tk, Label, Frame, StringVar, Radiobutton, N,W,E, Entry, END, Button, Toplevel, Listbox, OptionMenu
import tkFileDialog
import sys
import os
import urllib2


class DownloadFromURL(Frame):
	def __init__(self,parent,bots=None):
		Frame.__init__(self,parent)
		self.bots=bots
		self.parent=parent
		self.parent.title('GoReviewPartner')
		
		Label(self,text='   ').grid(column=0,row=0)
		Label(self,text='   ').grid(column=2,row=4)
		
		Label(self,text=_("Paste the URL to the SGF file (http or https):")).grid(row=1,column=1,sticky=W)
		self.url_entry=Entry(self)
		self.url_entry.grid(row=2,column=1,sticky=W)
		
		Button(self,text=_("Get"),command=self.get).grid(row=3,column=1,sticky=E)
		self.popup=None
		
	def get(self):
		user_agent = 'GoReviewPartner (https://github.com/pnprog/goreviewpartner/)'
		headers = { 'User-Agent' : user_agent }
		
		
		url=self.url_entry.get()
		if not url:
			return
		
		if url[:4]!="http":
			url="http://"+url
		
		log("Downloading",url)
		
		r=urllib2.Request(url,headers=headers)
		try:
			h=urllib2.urlopen(r)
		except:
			show_error(_("Could not download the URL"))
			return
		filename=""
		
		sgf=h.read()
		
		if sgf[:7]!="(;FF[4]":
			log("not a sgf file")
			show_error(_("Not a SGF file!"))
			log(sgf[:7])
			return
		
		try:
			filename=h.info()['Content-Disposition']
			if 'filename="' in filename:
				filename=filename.split('filename="')[0][:-1]
			if "''" in filename:
				filename=filename.split("''")[1]
		except:
			log("no Content-Disposition in header")
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
		
		log(filename)
		#text_file = open(filename, "w")
		#text_file.write(sgf)
		#text_file.close()
		
		write_rsgf(filename,sgf)
		
		#self.parent.destroy()
		self.destroy()
		#newtop=Tk()
		self.popup=RangeSelector(self.parent,filename,self.bots)
		self.popup.pack()
		#newtop.mainloop()

	def close_app(self):
		if self.popup:
			try:
				log("closing RunAlanlysis popup from RangeSelector")
				self.popup.close_app()
			except:
				log("RangeSelector could not close its RunAlanlysis popup")
				pass
		
		try:
			self.parent.destroy()
		except:
			pass


class WriteException(Exception):
    pass

def write_rsgf(filename,sgf_content):
	try:
		log("Saving RSGF file",filename)
		new_file=open(filename,'w')
		new_file.write(sgf_content)
		new_file.close()
	except Exception,e:
		log("Could not save the RSGF file",filename)
		log(e)
		raise WriteException(_("Could not save the RSGF file: ")+filename+"\n"+str(e))

def open_sgf(filename):
	try:
		log("Opening SGF file",filename)
		txt = open(filename)
		g = sgf.Sgf_game.from_string(clean_sgf(txt.read()))
		txt.close()
		return g
	except Exception,e:
		log("Could not open the SGF file",filename)
		log(e)
		raise WriteException(_("Could not save the SGF file: ")+filename+"\n"+str(e))


def clean_sgf(txt):
	return txt
	for private_property in ["MULTIGOGM","MULTIGOBM"]:
		if private_property in txt:
			log("removing private property",private_property,"from sgf content")
			txt1,txt2=txt.split(private_property+'[')				
			txt=txt1+"]".join(txt2.split(']')[1:])
	return txt


RunAnalysis=None

def get_all_sgf_leaves(root,deep=0):
	
	if len(root)==0:
		#this is a leave
		return [(root,deep)]
	
	leaves=[]
	deep+=1
	for leaf in root:
		leaves.extend(get_all_sgf_leaves(leaf,deep))
	
	return leaves

def keep_only_one_leaf(leaf):
	
	while 1:
		try:
			parent=leaf.parent
			for other_leaf in parent:
				if other_leaf!=leaf:
					log("deleting...")
					other_leaf.delete()
			leaf=parent
		except:
			#reached root
			return

def check_selection(selection,nb_moves):
	move_selection=[]
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
				if a<=b and a>0 and b<=nb_moves:
					move_selection.extend(range(a,b+1))
			except Exception, e:
				print e
				return False
	move_selection=list(set(move_selection))
	move_selection=sorted(move_selection)
	return move_selection

def check_selection_for_color(move_zero,move_selection,color):
	
	if color=="black":
		new_move_selection=[]
		for m in move_selection:
			one_move=go_to_move(move_zero,m)
			player_color,player_move=one_move.get_move()
			if player_color.lower()=='b':
				new_move_selection.append(m)
		return new_move_selection
	elif color=="white":
		new_move_selection=[]
		for m in move_selection:
			one_move=go_to_move(move_zero,m)
			player_color,player_move=one_move.get_move()
			if player_color.lower()=='w':
				new_move_selection.append(m)
		return new_move_selection
	else:
		return move_selection

class RangeSelector(Frame):
	def __init__(self,parent,filename,bots=None):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		root = self
		root.parent.title('GoReviewPartner')
		self.bots=bots
		
		#txt = open(self.filename)
		#content=txt.read()
		#txt.close()
		
		self.g=open_sgf(self.filename)
		content=self.g.serialise()
		#self.g = sgf.Sgf_game.from_string(clean_sgf(content))
		self.move_zero=self.g.get_root()
		nb_moves=get_moves_number(self.move_zero)
		self.nb_moves=nb_moves
		s = StringVar()
		s.set("all")
		row=0
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		if bots!=None:
			Label(self,text=_("Bot to use for analysis:")).grid(row=row,column=1,sticky=N+W)
			self.bot_selection = Listbox(self,height=len(bots))
			self.bot_selection.grid(row=row,column=2,sticky=W)
			for bot,f in bots:
				self.bot_selection.insert(END, bot)
			self.bot_selection.selection_set(0)
			self.bot_selection.configure(exportselection=False)
			row+=1
			Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Select variation to be analysed")).grid(row=3,column=1,sticky=W)
		self.leaves=get_all_sgf_leaves(self.move_zero)
		self.variation_selection=StringVar()
		self.variation_selection.trace("w", self.variation_changed)
		
		options=[]
		v=1
		for leaf,deep in self.leaves:
			options.append(_("Variation %i (%i moves)")%(v,deep))
			v+=1
		self.variation_selection.set(options[0])
		
		apply(OptionMenu,(self,self.variation_selection)+tuple(options)).grid(row=row,column=2,sticky=W)

		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text=_("Select moves to be analysed")).grid(row=row,column=1,sticky=W)
		
		row+=1
		self.r1=Radiobutton(self,text=_("Analyse all %i moves")%nb_moves,variable=s, value="all")
		self.r1.grid(row=row,column=1,sticky=W)
		self.after(0,self.r1.select)
		
		row+=1
		r2=Radiobutton(self,text=_("Analyse only those moves:"),variable=s, value="only")
		r2.grid(row=row,column=1,sticky=W)
		
		only_entry=Entry(self)
		only_entry.bind("<Button-1>", lambda e: r2.select())
		only_entry.grid(row=row,column=2,sticky=W)
		only_entry.delete(0, END)
		if nb_moves>0:
			only_entry.insert(0, "1-"+str(nb_moves))
		
		row+=3
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Select colors to be analysed")).grid(row=row,column=1,sticky=W)
		
		c = StringVar()
		c.set("both")
		
		row+=1
		c0=Radiobutton(self,text=_("Black & white"),variable=c, value="both")
		c0.grid(row=row,column=1,sticky=W)
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
		
		row+=1
		c1=Radiobutton(self,text=_("Black only")+black_player,variable=c, value="black")
		c1.grid(row=row,column=1,sticky=W)
		
		row+=1
		c2=Radiobutton(self,text=_("White only")+white_player,variable=c, value="white")
		c2.grid(row=row,column=1,sticky=W)
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text=_("Confirm the value of komi")).grid(row=row,column=1,sticky=W)
		
		komi_entry=Entry(self)
		komi_entry.grid(row=row,column=2,sticky=W)
		komi_entry.delete(0, END)
		
		try:
			komi=self.g.get_komi()
			komi_entry.insert(0, str(komi))
		except Exception, e:
			log("Error while reading komi value, please check:\n"+str(e))
			show_error(_("Error while reading komi value, please check:")+"\n"+str(e))
			komi_entry.insert(0, "0")
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		Label(self,text=_("Stop the analysis if the bot resigns")).grid(row=row,column=1,sticky=W)
		StopAtFirstResign = BooleanVar(value=Config.getboolean('Analysis', 'StopAtFirstResign'))
		StopAtFirstResignCheckbutton=Checkbutton(self, text="", variable=StopAtFirstResign,onvalue=True,offvalue=False)
		StopAtFirstResignCheckbutton.grid(row=row,column=2,sticky=W)
		StopAtFirstResignCheckbutton.var=StopAtFirstResign
		self.StopAtFirstResign=StopAtFirstResign
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Button(self,text=_("Start"),command=self.start).grid(row=row,column=2,sticky=E)
		self.mode=s
		self.color=c
		self.nb_moves=nb_moves
		self.only_entry=only_entry
		self.popup=None
		self.komi_entry=komi_entry
		
	def variation_changed(self,*args):
		log("variation changed!",self.variation_selection.get())
		try:
			self.after(0,self.r1.select)
			variation=int(self.variation_selection.get().split(" ")[1])-1
			deep=self.leaves[variation][1]
			self.only_entry.delete(0, END)
			if deep>0:
				self.only_entry.insert(0, "1-"+str(deep))
			
			self.r1.config(text="Analyse all % moves"%deep)
			
			self.nb_moves=deep
			
		except:
			pass
		
		
	
	
	def close_app(self):
		if self.popup:
			try:
				log("closing RunAlanlysis popup from RangeSelector")
				self.popup.close_app()
			except:
				log("RangeSelector could not close its RunAlanlysis popup")
				pass
	
	def start(self):
		
		if self.nb_moves==0:
			show_error(_("This variation is empty (0 move), the analysis cannot be performed!"))
			return
		
		try:
			komi=float(self.komi_entry.get())
		except:
			show_error(_("Incorrect value for komi (%s), please double check.")%self.komi_entry.get())
			return
		
		if self.bots!=None:
			bot_selection=int(self.bot_selection.curselection()[0])
			log("bot selection:",self.bots[bot_selection][0])
			RunAnalysis=self.bots[bot_selection][1]
		
		if self.mode.get()=="all":
			intervals="all moves"
			move_selection=range(1,self.nb_moves+1)
		else:
			selection = self.only_entry.get()
			intervals="moves "+selection
			move_selection=check_selection(selection,self.nb_moves)
			if move_selection==False:
				show_error(_("Could not make sense of the moves range.")+"\n"+_("Please indicate one or more move intervals (ie: \"10-20, 40,50-51,63,67\")"))
				return

		if self.color.get()=="black":
			intervals+=" (black only)"
			log("black only")
		elif self.color.get()=="white":
			intervals+=" (white only)"
			log("white only")
		else:
			intervals+=" (both colors)"

		move_selection=check_selection_for_color(self.move_zero,move_selection,self.color.get())
			
		log("========= move selection")
		log(move_selection)
		
		log("========= variation")
		variation=int(self.variation_selection.get().split(" ")[1])-1
		log(variation)
		
		####################################
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		Config.set("Analysis","StopAtFirstResign",self.StopAtFirstResign.get())
		Config.write(open(config_file,"w"))
		
		####################################
		self.parent.destroy()
		newtop=Tk()
		self.popup=RunAnalysis(newtop,self.filename,move_selection,intervals,variation,komi)
		self.popup.pack()
		newtop.mainloop()

import threading
import time
import ConfigParser
from Tkinter import *
import ttk

class RunAnalysisBase(Frame):
	def __init__(self,parent,filename,move_range,intervals,variation,komi):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.move_range=move_range
		self.lock1=threading.Lock()
		self.lock2=threading.Lock()
		self.intervals=intervals
		self.variation=variation
		self.komi=komi
		
		self.error=None
		try:
			self.bot=self.initialize_bot()
		except Exception,e:
			self.error=_("Error while initializing the GTP bot:")+"\n"+str(e)
			self.abort()
			return
		
		if not self.bot:
			return
		
		try:
			self.initialize_UI()
		except Exception,e:
			self.error=_("Error while initializing the graphical interface:")+"\n"+str(e)
			self.abort()
			return
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		self.maxvariations=int(Config.get("Analysis", "maxvariations"))
		
		try:
			if Config.getboolean('Analysis', 'StopAtFirstResign'):
				log("Stop_At_First_Resign is ON")
				self.stop_at_first_resign=True
			else:
				self.stop_at_first_resign=False
				log("Stop_At_First_Resign is OFF")
		except:
			self.stop_at_first_resign=False
			log("Stop_At_First_Resign is OFF")
		
		self.root.after(500,self.follow_analysis)
	
	def run_analysis(self,current_move):
		
		#################################################
		##### here is the place to perform analysis #####
		#################################################
		
		log("Analysis for this move is completed")
	
	
	def run_all_analysis(self):
		self.current_move=1
		#try:

			
		while self.current_move<=self.max_move:
			self.lock1.acquire()
			self.run_analysis(self.current_move)
			self.current_move+=1
			self.lock1.release()
			self.lock2.acquire()
			self.lock2.release()
		return
		"""except Exception,e:
			self.error=str(e)
			log("releasing lock")
			try:
				self.lock1.release()
			except:
				pass
			try:
				self.lock2.release()
			except:
				pass
			log("leaving thread")
			sys.exit()
		"""
			

	def abort(self):
		try:
			self.lab1.config(text=_("Aborted"))
			self.lab2.config(text="")
		except:
			pass
		log("Leaving follow_anlysis()")
		show_error(_("Analysis aborted:")+"\n\n"+self.error)

	def follow_analysis(self):
		if self.error:
			self.abort()
			return
		
		if self.lock1.acquire(False):
			if self.total_done>0:
				self.time_per_move=1.0*(time.time()-self.t0)/self.total_done+1
				#log(self.total_done,"move(s) analysed in",int(10*(time.time()-self.t0))/10.,"secondes =>",int(10*self.time_per_move)/10.,"s/m")
				#log("self.time_per_move=",(time.time()-self.t0),"/",self.total_done,"=",self.time_per_move)
			remaining_s=int((len(self.move_range)-self.total_done)*self.time_per_move)
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
			if self.time_per_move<>0:
				self.lab2.config(text=_("Remaining time: %ih, %imn, %is")%(remaining_h,remaining_m,remaining_s))
			self.lab1.config(text=_("Currently at move %i/%i")%(self.current_move,self.max_move))
			self.pb.step()
			self.update_idletasks()
			self.lock2.release()
			time.sleep(.001)
			self.lock1.release()
			self.lock2.acquire()
		if self.current_move<=self.max_move:
			self.root.after(1,self.follow_analysis)
		else:
			self.propose_review()

	def propose_review(self):
		self.lab1.config(text=_("Completed"))
		self.lab2.config(text="")
		self.pb["maximum"] = 100
		self.pb["value"] = 100
		
		try:
			import dual_view
			Button(self,text=_("Start review"),command=self.start_review).pack()
		except:
			pass

	def start_review(self):
		import dual_view
		app=self.parent
		screen_width = app.winfo_screenwidth()
		screen_height = app.winfo_screenheight()
		
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		display_factor=.5
		try:
			display_factor=float(Config.get("Review", "GobanScreenRatio"))
		except:
			Config.set("Review", "GobanScreenRatio",display_factor)
			Config.write(open("config.ini","w"))
		
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		#Toplevel()
		
		new_popup=dual_view.DualView(self.parent,self.filename[:-4]+".rsgf",min(width,height))
		new_popup.pack(fill=BOTH,expand=1)
		self.remove_app()
		
	
	def remove_app(self):
		################################################
		##### here is the place to kill the bot(s) #####
		################################################
		log("destroying")
		self.destroy()
	
	def close_app(self):
		self.remove_app()
		self.parent.destroy()
		log("RunAnalysis closed")

		
	def initialize_UI(self):

		self.max_move=get_moves_number(self.move_zero)
		if not self.move_range:
			self.move_range=range(1,self.max_move+1)

		self.total_done=0
		
		root = self
		root.parent.title('GoReviewPartner')
		root.parent.protocol("WM_DELETE_WINDOW", self.close_app)
		
		
		Label(root,text=_("Analysis of: %s")%os.path.basename(self.filename)).pack()
				
		self.lab1=Label(root)
		self.lab1.pack()
		
		self.lab2=Label(root)
		self.lab2.pack()
		
		self.lab1.config(text=_("Currently at move %i/%i")%(1,self.max_move))
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()

		current_move=1
		
		try:
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
		except Exception,e:
			show_error(str(e))
			self.lab1.config(text=_("Aborted"))
			self.lab2.config(text="")
			return

		self.lock2.acquire()
		self.t0=time.time()
		first_move=go_to_move(self.move_zero,1)
		first_comment=_("Analysis by GoReviewPartner")
		first_comment+="\n"+("Bot: %s/%s"%(self.bot.bot_name,self.bot.bot_version))
		first_comment+="\n"+("Komi: %0.1f"%self.komi)
		first_comment+="\n"+("Intervals: %s"%self.intervals)
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		if Config.getboolean('Analysis', 'SaveCommandLine'):
			first_comment+="\n"+("Command line: %s"%self.bot.command_line)
		
		first_move.add_comment_text(first_comment)
		threading.Thread(target=self.run_all_analysis).start()
		
		self.root=root


class BotOpenMove(Button):
	def __init__(self,parent):
		self.name='Bot'
		Button.__init__(self,parent)
		
	def undo(self):
		if self.okbot:
			self.bot.undo()
	
	def place(self,move,color):
		if self.okbot:
			if not self.bot.place(move,color):
				self.config(state='disabled')

	def click(self,color):
		log(self.name,"play")
		n0=time.time()
		if color==1:
			move=self.bot.play_black()
		else:
			move=self.bot.play_white()
		log("move=",move,"in",time.time()-n0,"s")
		return move

	def close(self):
		if self.okbot:
			log("killing",self.name)
			self.bot.close()

		

def bot_starting_procedure(bot_name,bot_gtp_name,bot_gtp,sgf_g):
	
	size=sgf_g.get_size()
	
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	
	
	try:
		bot_command_line=Config.get(bot_name, "Command")
	except:
		show_error(_("The config.ini file does not contain entry for %s command line!")%bot_name)
		return False
	
	if not bot_command_line:
		show_error(_("The config.ini file does not contain command line for %s!")%bot_name)
		return False
	log("Starting "+bot_name+"...")
	try:
		bot_command_line=[Config.get(bot_name, "Command")]+Config.get(bot_name, "Parameters").split()
		bot=bot_gtp(bot_command_line)
	except Exception,e:
		show_error((_("Could not run %s using the command from config.ini file:")%bot_name)+"\n"+Config.get(bot_name, "Command")+" "+Config.get(bot_name, "Parameters")+"\n"+str(e))
		return False
	log(bot_name+" started")
	log(bot_name+" identification through GTP...")
	try:
		answer=bot.name()
	except Exception, e:
		show_error((_("%s did not replied as expected to the GTP name command:")%bot_name)+"\n"+str(e))
		return False
	
	if answer!=bot_gtp_name:
		show_error((_("%s did not identified itself as expected:")%bot_name)+"\n'"+bot_gtp_name+"' != '"+answer+"'")
		return False
	
	log(bot_name+" identified itself properly")
	log("Checking version through GTP...")
	try:
		bot_version=bot.version()
	except Exception, e:
		show_error((_("%s did not replied as expected to the GTP version command:")%bot_name)+"\n"+str(e))
		return False
	log("Version: "+bot_version)
	log("Setting goban size as "+str(size)+"x"+str(size))
	try:
		ok=bot.boardsize(size)
	except:
		show_error((_("Could not set the goboard size using GTP command. Check that %s is running in GTP mode.")%bot_name))
		return False
	if not ok:
		show_error(_("%s rejected this board size (%ix%i)")%(bot_name,size,size))
		return False
	
	log("Clearing the board")
	bot.reset()
	
	log("Setting komi")
	bot.komi(sgf_g.get_komi())
	
	board, plays = sgf_moves.get_setup_and_moves(sgf_g)
	handicap_stones=""
	log("Adding handicap stones, if any")
	for colour, move0 in board.list_occupied_points():
		if move0 != None:
			row, col = move0
			move=ij2gtp((row,col))
			if colour in ('w',"W"):
				log("Adding initial white stone at",move)
				bot.place_white(move)
			else:
				log("Adding initial black stone at",move)
				bot.place_black(move)
	log(bot_name+" initialization completed")
	
	bot.bot_name=bot_gtp_name
	bot.bot_version=bot_version
	
	return bot





import getopt

import __main__
try:
	usage="usage: python "+__main__.__file__+" [--range=<range>] [--color=both] [--komi=<komi>] [--variation=<variation>] <sgf file1> <sgf file2> <sgf file3>"
except:
	log("Command line features are disabled")
	usage=""

def parse_command_line(filename,argv):
	
	g=open_sgf(filename)
	content=g.serialise()
	
	move_zero=g.get_root()
	
	leaves=get_all_sgf_leaves(move_zero)
	
	found=False
	for p,v in argv:
		if p=="--variation":
			try:
				variation=int(v)
				found=True
			except:
				show_error("Wrong variation parameter\n"+usage)
				sys.exit()
	if not found:
		variation=1
	
	log("Variation:",variation)
	
	if variation<1:
		show_error("Wrong variation parameter, it must be a positive integer")
		sys.exit()
	
	if variation>len(leaves):
		show_error("Wrong variation parameter, this SGF file has only "+str(len(leaves))+" variation(s)")
		sys.exit()
	
	nb_moves=leaves[variation-1][1]
	log("Moves for this variation:",nb_moves)
	
	if nb_moves==0:
		show_error("This variation is empty (0 move), the analysis cannot be performed!")
		sys.exit()
	
	#nb_moves=get_moves_number(move_zero)
	
	found=False
	for p,v in argv:
		if p=="--range":
			if v=="":
				show_error("Wrong range parameter\n"+usage)
				sys.exit()
			elif v=="all":
				break
			else:
				intervals=v
				log("Range:",v)
				move_selection=check_selection(v.replace('"',''),nb_moves)
				if move_selection==False:
					show_error("Wrong range parameter\n"+usage)
					sys.exit()
				found=True
				break
		
	if not found:
		move_selection=range(1,nb_moves+1)
		intervals="all moves"
		log("Range: all")
			
	found=False
	for p,v in argv:
		if p=="--color":
			
			if v in ["black","white"]:
				log("Color:",v)
				move_selection=check_selection_for_color(move_zero,move_selection,v)
				intervals+=" ("+v+"only)"
				found=True
				break
			elif v=="both":
				break
			else:
				show_error("Wrong color parameter\n"+usage)
				sys.exit()
	if not found:
		intervals+=" (both colors)"
		log("Color: both")
	
	print move_selection
	
	found=False
	for p,v in argv:
		if p=="--komi":
			try:
				komi=float(v)
				found=True
			except:
				show_error("Wrong komi parameter\n"+usage)
				sys.exit()
	if not found:
		try:
			komi=g.get_komi()
		except Exception, e:
			msg="Error while reading komi value, please check:\n"+str(e)
			msg+="\nPlease indicate komi using --komi parameter"
			log(msg)
			show_error(msg)
			sys.exit()
	
	log("Komi:",komi)
	
	return move_selection,intervals,variation,komi

# from http://www.py2exe.org/index.cgi/WhereAmI
def we_are_frozen():
	"""Returns whether we are frozen via py2exe.
	This will affect how we find out where we are located."""

	return hasattr(sys, "frozen")


def module_path():
	""" This will get us the program's directory,
	even if we are frozen using py2exe"""

	if we_are_frozen():
		print "Apparently running from the executable."
		return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

	return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))


import locale

lang=locale.getdefaultlocale()[0].split('_')[0]

translations={}



log("System langage:",lang)

def prepare_translations():
	global translations
	
	if lang=='en':
		return

	data_file_url=os.path.join(os.path.abspath(pathname),"translations",lang+".po")
	log("Loading translation file:",data_file_url)
	
	data_file = open(data_file_url,"r")
	translation_data=data_file.read()
	data_file.close()
	
	entry=""
	translation=""
	
	for line in translation_data.split('\n'):

		key="msgid"
		if line[:len(key)+2]==key+' "':
			entry=line[len(key)+2:-1]
			translation=""
		
		key="msgstr"
		if line[:len(key)+2]==key+' "':
			translation=line[len(key)+2:-1]
			
			if len(entry)>0 and len(translation)>0:
				translations[entry]=translation
			entry=""
			translation=""

def _(txt=None):
	global translations
	if not translations:
		return txt
	
	if translations.has_key(txt):
		return translations[txt]
	
	return txt


try:
	pathname=module_path()
except:
	pathname=os.path.dirname(__file__)

log('GRP path:', os.path.abspath(pathname))
config_file=os.path.join(os.path.abspath(pathname),"config.ini")
log('Config file:', config_file)

available_translations=["fr"]
if lang in available_translations:
	prepare_translations()
else:
	log("No translation file lang="+lang,"falling back on english.")

