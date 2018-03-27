# -*- coding: utf-8 -*-

class AbortedException(Exception):
	pass

import threading

loglock=threading.Lock()
def log(*args):
	global loglock
	loglock.acquire()
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
			print "["+str(type(arg))+"]",
	print
	loglock.release()

def linelog(*args):
	global loglock
	loglock.acquire()
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
			print "["+str(type(arg))+"]",
	loglock.release()

import tkMessageBox

def show_error(txt,parent=None):
	try:
		tkMessageBox.showerror(_("Error"),txt,parent=parent)
		log("ERROR: "+txt)
	except:
		log("ERROR: "+txt)

def show_info(txt,parent=None):
	try:
		log("INFO: "+txt)
		tkMessageBox.showinfo(_("Information"),txt,parent=parent)
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
			log("The end of the sgf tree was reached before getting to move_number =",move_number)
			log("Returning False")
			return False
		move=move[0]
		k+=1
	return move

def gtp2ij(move):
	try:
		#letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
		letters="abcdefghjklmnopqrstuvwxyz"
		return int(move[1:])-1,letters.index(move[0].lower())
	except:
		raise AbortedException("Cannot convert GTP coordinates "+str(move)+" to grid coordinates!")




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
import sys
import os
import urllib2


class DownloadFromURL(Toplevel):
	def __init__(self,parent,bots=None):
		Toplevel.__init__(self,parent)
		self.bots=bots
		self.parent=parent
		self.title('GoReviewPartner')
		self.config(padx=10,pady=10)

		Label(self,text=_("Paste the URL to the SGF file (http or https):")).grid(row=1,column=1,sticky=W)
		self.url_entry=Entry(self)
		self.url_entry.grid(row=2,column=1,sticky=W)
		self.url_entry.focus()
		
		Button(self,text=_("Get"),command=self.get).grid(row=3,column=1,sticky=E)
		
		self.protocol("WM_DELETE_WINDOW", self.close)

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
			show_error(_("Could not download the URL"),parent=self)
			return
		filename=""

		sgf=h.read()

		if sgf[:7]!="(;FF[4]":
			log("not a sgf file")
			show_error(_("Not a SGF file!"),parent=self)
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
		write_rsgf(filename,sgf)

		popup=RangeSelector(self.parent,filename,self.bots)
		self.parent.add_popup(popup)
		self.close()

	def close(self):
		log("Closing DownloadFromURL()")
		self.parent.remove_popup(self)
		self.destroy()



class WriteException(Exception):
	pass

filelock=threading.Lock()
def write_rsgf(filename,sgf_content):
	filelock.acquire()
	try:
		log("Saving RSGF file",filename)
		new_file=open(filename,'w')
		if type(sgf_content)==type("abc"):
			new_file.write(sgf_content)
		else:
			new_file.write(sgf_content.serialise())
		new_file.close()
		filelock.release()
	except Exception,e:
		log("Could not save the RSGF file",filename)
		log(e)
		filelock.release()
		raise WriteException(_("Could not save the RSGF file: ")+filename+"\n"+str(e))
def write_sgf(filename,sgf_content):
	filelock.acquire()
	try:
		log("Saving SGF file",filename)
		new_file=open(filename,'w')
		if type(sgf_content)==type("abc"):
			new_file.write(sgf_content)
		else:
			new_file.write(sgf_content.serialise())
		new_file.close()
		filelock.release()
	except Exception,e:
		log("Could not save the SGF file",filename)
		log(e)
		filelock.release()
		raise WriteException(_("Could not save the SGF file: ")+filename+"\n"+str(e))
	

def open_sgf(filename):
	filelock.acquire()
	try:
		#log("Opening SGF file",filename)
		txt = open(filename)
		g = sgf.Sgf_game.from_string(clean_sgf(txt.read()))
		txt.close()
		filelock.release()
		return g
	except Exception,e:
		log("Could not open the SGF file",filename)
		log(e)
		filelock.release()
		raise WriteException(_("Could not save the SGF file: ")+filename+"\n"+str(e))
def clean_sgf(txt):
	return txt
	for private_property in ["MULTIGOGM","MULTIGOBM"]:
		if private_property in txt:
			log("removing private property",private_property,"from sgf content")
			txt1,txt2=txt.split(private_property+'[')
			txt=txt1+"]".join(txt2.split(']')[1:])
	return txt




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
			player_color,unused=one_move.get_move()
			if player_color.lower()=='b':
				new_move_selection.append(m)
		return new_move_selection
	elif color=="white":
		new_move_selection=[]
		for m in move_selection:
			one_move=go_to_move(move_zero,m)
			player_color,unused=one_move.get_move()
			if player_color.lower()=='w':
				new_move_selection.append(m)
		return new_move_selection
	else:
		return move_selection

class RangeSelector(Toplevel):
	def __init__(self,parent,filename,bots=None):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.config(padx=10,pady=10)
		root = self
		root.parent.title('GoReviewPartner')
		self.protocol("WM_DELETE_WINDOW", self.close)
		
		self.bots=bots

		self.g=open_sgf(self.filename)
		content=self.g.serialise()

		self.move_zero=self.g.get_root()
		nb_moves=get_moves_number(self.move_zero)
		self.nb_moves=nb_moves

		row=0
		Label(self,text="").grid(row=row,column=1)

		row+=1
		if bots!=None:
			Label(self,text=_("Bot to use for analysis:")).grid(row=row,column=1,sticky=N+W)
			value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
			bot_names=[bot['name']+value[bot['profile']] for bot in bots]
			self.bot_selection=StringVar()

			apply(OptionMenu,(self,self.bot_selection)+tuple(bot_names)).grid(row=row,column=2,sticky=W)
			self.bot_selection.set(bot_names[0])

			row+=1
			Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("Select variation to be analysed")).grid(row=row,column=1,sticky=W)
		self.leaves=get_all_sgf_leaves(self.move_zero)
		self.variation_selection=StringVar()
		self.variation_selection.trace("w", self.variation_changed)

		options=[]
		v=1
		for unused,deep in self.leaves:
			options.append(_("Variation %i (%i moves)")%(v,deep))
			v+=1
		self.variation_selection.set(options[0])

		apply(OptionMenu,(self,self.variation_selection)+tuple(options)).grid(row=row,column=2,sticky=W)

		row+=1
		Label(self,text="").grid(row=row,column=1)

		row+=1
		Label(self,text=_("Select moves to be analysed")).grid(row=row,column=1,sticky=W)

		row+=1
		s = StringVar()
		s.set("all")
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

		board, unused = sgf_moves.get_setup_and_moves(self.g)
		if len(board.list_occupied_points())>0:
			row+=1
			Label(self,text=_("This is a %i stones handicap game.")%len(board.list_occupied_points())).grid(row=row,column=1,columnspan=2,sticky=W)
			row+=1
			Label(self,text=_("You may want to adjust the value of komi based on the rule set and the bot used.")).grid(row=row,column=1,columnspan=2,sticky=W)

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
			show_error(_("Error while reading komi value, please check:")+"\n"+str(e),parent=self)
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
		self.komi_entry=komi_entry

		self.focus()
		self.parent.focus()

	def variation_changed(self,*unused):
		log("variation changed!",self.variation_selection.get())
		try:
			self.after(0,self.r1.select)
			variation=int(self.variation_selection.get().split(" ")[1])-1
			deep=self.leaves[variation][1]
			self.only_entry.delete(0, END)
			if deep>0:
				self.only_entry.insert(0, "1-"+str(deep))

			self.r1.config(text=_("Analyse all %i moves")%deep)

			self.nb_moves=deep

		except:
			pass

	def close(self):
		self.destroy()
		self.parent.remove_popup(self)

	def start(self):

		if self.nb_moves==0:
			show_error(_("This variation is empty (0 move), the analysis cannot be performed!"),parent=self)
			return

		try:
			komi=float(self.komi_entry.get())
		except:
			show_error(_("Incorrect value for komi (%s), please double check.")%self.komi_entry.get(),parent=self)
			return

		if self.bots!=None:
			bot=self.bot_selection.get()
			log("bot selection:",bot)
			value={"slow":" (%s)"%_("Slow profile"),"fast":" (%s)"%_("Fast profile")}
			bot={bot['name']+value[bot['profile']]:bot for bot in self.bots}[bot]

			#RunAnalysis={bot_label:bot['runanalysis'] for bot in self.bots}[bot]
			#profile={bot_label:bot['profile'] for bot in self.bots}[bot]
			RunAnalysis=bot['runanalysis']
			profile=bot['profile']

			#bot_selection=int(self.bot_selection.curselection()[0])
			#log("bot selection:",self.bots[bot_selection][0])
			#RunAnalysis=self.bots[bot_selection][1]

		if self.mode.get()=="all":
			intervals="all moves"
			move_selection=range(1,self.nb_moves+1)
		else:
			selection = self.only_entry.get()
			intervals="moves "+selection
			move_selection=check_selection(selection,self.nb_moves)
			if move_selection==False:
				show_error(_("Could not make sense of the moves range.")+"\n"+_("Please indicate one or more move intervals (ie: \"10-20, 40,50-51,63,67\")"),parent=self)
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
		
		popup=RunAnalysis(self.parent,self.filename,move_selection,intervals,variation,komi,profile)
		self.parent.add_popup(popup)
		self.close()




import Queue
import time
import ConfigParser
from Tkinter import *
import ttk


def guess_color_to_play(move_zero,move_number):

	one_move=go_to_move(move_zero,move_number)



	player_color,unused=one_move.get_move()
	if player_color != None:
		return player_color

	if one_move is move_zero:
		print 'move_zero.get("PL")=',move_zero.get("PL")
		if move_zero.get("PL").lower()=="b":
			return "w"
		if move_zero.get("PL").lower()=="w":
			return "b"

	previous_move_color=guess_color_to_play(move_zero,move_number-1)

	if previous_move_color.lower()=='b':
		print "guess_color_to_play(%i)=%s"%(move_number,"w")
		return "w"
	else:
		print "guess_color_to_play(%i)=%s"%(move_number,"b")
		return "b"

class LiveAnalysisBase():
	def __init__(self,g,filename,profile="slow"):
		self.g=g
		self.filename=filename
		self.profile=profile
		self.bot=self.initialize_bot()
		self.update_queue=Queue.PriorityQueue()
		self.label_queue=Queue.Queue()
		self.best_moves_queue=Queue.Queue()

		self.move_zero=self.g.get_root()
		
		self.no_variation_if_same_move=True
		
		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size

		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		self.no_variation_if_same_move=Config.getboolean('Analysis', 'NoVariationIfSameMove')
		
		self.maxvariations=int(Config.get("Analysis", "maxvariations"))

		self.stop_at_first_resign=False

		self.cpu_lock=threading.Lock()

	def start(self):
		threading.Thread(target=self.run_live_analysis).start()

	def play(self,gtp_color,gtp_move):
		if gtp_color=='w':
			self.bot.place_white(gtp_move)
		else:
			self.bot.place_black(gtp_move)
	
	def undo(self):
		self.bot.undo()
	
	def run_live_analysis(self):
		self.current_move=1
		wait=0
		while 1:
			while wait>0:
				time.sleep(0.1)
				wait-=0.1
				try:
					priority,msg=self.update_queue.get(False)
					if priority<1:
						log("Analyser received a high priority message")
						wait=0
					self.update_queue.put((priority,msg))
				except:
					continue
				
				
			if not self.cpu_lock.acquire(False):
				time.sleep(2) #let's wait just enough time in case human player already has a move to play
				continue
			
			try:
				priority,msg=self.update_queue.get(False)
			except:
				self.cpu_lock.release()
				time.sleep(.5)
				continue

			if msg==None:
				log("Leaving the analysis")
				self.cpu_lock.release()
				return

			if msg=="wait":
				log("Analyser iddle for five seconds")
				self.cpu_lock.release()
				wait=5
				continue

			if type(msg)==type("undo xxx"):
				print "msg=",msg
				move_to_undo=int(msg.split()[1])
				#move_to_undo=int(priority+1)
				log("received undo msg for move",move_to_undo,"and beyong")
				if move_to_undo>self.current_move:
					log("Analysis of move",move_to_undo,"has not started yet, so let's forget about it")
				else:
					log("Analysis of move",move_to_undo,"was completed already, let's remove that branch")
					while self.current_move>=move_to_undo:
						log("Undoing move",self.current_move,"through GTP")
						self.undo()
						self.current_move-=1

				log("Deleting the SGF branch")
				parent=go_to_move(self.move_zero,move_to_undo-1)
				new_branch=parent[0]
				old_branch=parent[1]

				for p in ["ES","CBM","BWWR","VNWR", "MCWR","UBS","LBS","C"]:
					if old_branch.has_property(p):
						new_branch.set(p,old_branch.get(p))

				old_branch.delete()

				write_rsgf(self.filename[:-4]+".rsgf",self.g)
				self.cpu_lock.release()
				self.update_queue.put((0,"wait"))
				write_rsgf(self.filename[:-4]+".rsgf",self.g)
				continue

			log("Analyser received msg to analyse move",msg)
			while msg>self.current_move:
				log("Analyser currently at move",self.current_move)
				log("So asking "+self.bot.bot_name+" to play the game move",self.current_move)
				one_move=go_to_move(self.move_zero,self.current_move)
				player_color,player_move=one_move.get_move()
				log("game move",self.current_move,"is",player_color,"at",player_move)
				if player_color in ('w',"W"):
					log("white at",ij2gtp(player_move))
					self.play("w",ij2gtp(player_move))
				else:
					log("black at",ij2gtp(player_move))
					self.play("b",ij2gtp(player_move))
				self.current_move+=1

			log("Analyser is currently at move",self.current_move)
			self.label_queue.put(self.current_move)
			log("starting analysis of move",self.current_move)
			answer=self.run_analysis(self.current_move)
			log("Analyser best move: move %i at %s"%(self.current_move,answer))
			self.best_moves_queue.put([self.current_move,answer])
			
			try:
				game_move=go_to_move(self.move_zero,self.current_move).get_move()[1]
				log("Game move:",game_move)
				if game_move:
					if self.no_variation_if_same_move:
						if ij2gtp(game_move)==answer.lower():
							log("Bot move and game move are the same ("+answer+"), removing variations for this move")
							parent=go_to_move(self.move_zero,self.current_move-1)
							for child in parent[1:]:
								child.delete()
			except:
				#what could possibly go wrong with this?
				pass
			
			if self.update_queue.empty():
				self.label_queue.put("")
			write_rsgf(self.filename[:-4]+".rsgf",self.g)
			self.cpu_lock.release()
			#self.current_move+=1
			time.sleep(.1) #enought time for Live analysis to grap the lock






class RunAnalysisBase(Toplevel):
	def __init__(self,parent,filename,move_range,intervals,variation,komi,profile="slow"):
		if parent!="no-gui":
			Toplevel.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		self.move_range=move_range
		self.update_queue=Queue.Queue(1)
		self.intervals=intervals
		self.variation=variation
		self.komi=komi
		self.profile=profile
		self.g=None
		self.move_zero=None

		self.current_move=None
		self.time_per_move=None
		
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		
		self.no_variation_if_same_move=self.no_variation_if_same_move=Config.getboolean('Analysis', 'NoVariationIfSameMove')
		
		self.error=None

		self.g=open_sgf(self.filename)
		sgf_moves.indicate_first_player(self.g)

		leaves=get_all_sgf_leaves(self.g.get_root())
		log("keeping only variation",self.variation)
		keep_only_one_leaf(leaves[self.variation][0])

		size=self.g.get_size()
		log("size of the tree:", size)
		self.size=size

		log("Setting new komi")
		self.move_zero=self.g.get_root()
		self.g.get_root().set("KM", self.komi)

		try:
			self.bot=self.initialize_bot()
		except Exception,e:
			self.error=_("Error while initializing the GTP bot:")+"\n"+str(e)
			self.abort()
			return

		if not self.bot:
			return

		self.max_move=get_moves_number(self.move_zero)
		self.total_done=0

		if parent!="no-gui":
			try:
				self.initialize_UI()
			except Exception,e:
				self.error=_("Error while initializing the graphical interface:")+"\n"+str(e)
				self.abort()
				return
			self.root.after(500,self.follow_analysis)

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



		self.completed=False

		if parent=="no-gui":
			self.run_all_analysis()
		else:
			threading.Thread(target=self.run_all_analysis).start()



	def initialize_bot(self):
		pass

	def run_analysis(self,current_move):
		log("Analysis of move",current_move)
		#################################################
		##### here is the place to perform analysis #####
		#################################################

		log("Analysis for this move is completed")
	
	def play(self,gtp_color,gtp_move):
		if gtp_color=='w':
			self.bot.place_white(gtp_move)
		else:
			self.bot.place_black(gtp_move)

	def run_all_analysis(self):
		self.current_move=1

		while self.current_move<=self.max_move:
			answer=""
			if self.current_move in self.move_range:
				answer=self.run_analysis(self.current_move)
				self.total_done+=1
				write_rsgf(self.filename[:-4]+".rsgf",self.g)
				log("For this position,",self.bot.bot_name,"would play:",answer)
				log("Analysis for this move is completed")
			elif self.move_range:
				log("Move",self.current_move,"not in the list of moves to be analysed, skipping")
			
			try:
				game_move=go_to_move(self.move_zero,self.current_move).get_move()[1]
				if game_move:
					if self.no_variation_if_same_move:
						if ij2gtp(game_move)==answer.lower():
							log("Bot move and game move are the same ("+answer+"), removing variations for this move")
							parent=go_to_move(self.move_zero,self.current_move-1)
							for child in parent[1:]:
								child.delete()
							write_rsgf(self.filename[:-4]+".rsgf",self.g)
			except:
				#what could possibly go wrong with this?
				pass
			
			if (answer.lower()=="resign") and (self.stop_at_first_resign==True):
				log("")
				log("The analysis will stop now")
				log("")
				self.move_range=[]
				#the bot has proposed to resign, and resign_at_first_stop is ON
			elif self.move_range:
				one_move=go_to_move(self.move_zero,self.current_move)
				player_color,player_move=one_move.get_move()
				if player_color in ('w',"W"):
					log("now asking "+self.bot.bot_name+" to play the game move: white at",ij2gtp(player_move))
					self.play('w',ij2gtp(player_move))
				else:
					log("now asking "+self.bot.bot_name+" to play the game move: black at",ij2gtp(player_move))
					self.play('b',ij2gtp(player_move))

			self.current_move+=1
			if self.parent!="no-gui":
				self.update_queue.put(self.current_move)
			
		return

	def abort(self):
		try:
			self.lab1.config(text=_("Aborted"))
			self.lab2.config(text="")
		except:
			pass
		log("Leaving follow_anlysis()")
		show_error(_("Analysis aborted:")+"\n\n"+self.error,parent=self)

	def follow_analysis(self):

		if self.error:
			self.abort()
			return
		msg=None
		try:
			msg=self.update_queue.get(False)
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
			
			

			if self.total_done==1:
				if not self.review_button:
					self.review_button=Button(self.right_frame,text=_("Start review"),command=self.start_review)
					self.review_button.pack()
				
			
		except:
			pass

		if self.current_move<=self.max_move:
			if msg==None:
				self.parent.after(250,self.follow_analysis)
			else:
				self.parent.after(10,self.follow_analysis)
		else:
			self.end_of_analysis()

	def end_of_analysis(self):
		self.lab1.config(text=_("Completed"))
		self.lab2.config(text="")
		self.pb["maximum"] = 100
		self.pb["value"] = 100

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

		popup=dual_view.DualView(app,self.filename[:-4]+".rsgf",min(width,height))
		self.parent.add_popup(popup)
		if (self.pb["maximum"] == 100) and (self.pb["value"] == 100):
			self.close()

	def terminate_bot(self):
		try:
			log("killing",self.bot.bot_name)
			self.bot.close()
		except Exception,e:
			log(e)
	def remove_app(self):
		log("RunAnalysis beeing closed")
		self.lab2.config(text=_("Now closing, please wait..."))
		self.update_idletasks()
		try:
			self.terminate_bot()
		except:
			pass
		self.destroy()

	def close(self):
		self.remove_app()
		self.destroy()
		self.parent.remove_popup(self)
		log("RunAnalysis closed")
		self.completed=True

	def initialize_UI(self):


		if not self.move_range:
			self.move_range=range(1,self.max_move+1)



		root = self
		root.title('GoReviewPartner')
		root.protocol("WM_DELETE_WINDOW", self.close)

		bg=root.cget("background")
		logo = Canvas(root,bg=bg,width=5,height=5)
		logo.pack(fill=BOTH,expand=1,side=LEFT)
		logo.bind("<Configure>",lambda e: draw_logo(logo,e,"vertical"))

		right_frame=Frame(root)
		right_frame.pack(side=LEFT,padx=5, pady=5)
		self.right_frame=right_frame
		Label(right_frame,text=_("Analysis of: %s")%os.path.basename(self.filename)).pack()

		self.lab1=Label(right_frame)
		self.lab1.pack()

		self.lab2=Label(right_frame)
		self.lab2.pack()

		self.lab1.config(text=_("Currently at move %i/%i")%(1,self.max_move))

		self.pb = ttk.Progressbar(right_frame, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()


		try:
			write_rsgf(self.filename[:-4]+".rsgf",self.g)
		except Exception,e:
			show_error(str(e),parent=self)
			self.lab1.config(text=_("Aborted"))
			self.lab2.config(text="")
			return

		self.t0=time.time()

		first_comment=_("Analysis by GoReviewPartner")
		first_comment+="\n"+("Bot: %s/%s"%(self.bot.bot_name,self.bot.bot_version))
		first_comment+="\n"+("Komi: %0.1f"%self.komi)
		first_comment+="\n"+("Intervals: %s"%self.intervals)

		Config = ConfigParser.ConfigParser()
		Config.read(config_file)

		if Config.getboolean('Analysis', 'SaveCommandLine'):
			first_comment+="\n"+("Command line: %s"%self.bot.command_line)

		self.move_zero.set("RSGF",first_comment+"\n")
		self.move_zero.set("BOT",self.bot.bot_name)
		self.move_zero.set("BOTV",self.bot.bot_version)

		self.root=root
		self.review_button=None



class BotOpenMove():
	def __init__(self,sgf_g,profile="slow"):
		self.name='Bot'
		self.bot=None
		self.okbot=False
		self.sgf_g=sgf_g
		self.profile=profile

	def start(self):
		try:
			result=self.my_starting_procedure(self.sgf_g,profile=self.profile,silentfail=True)
			if result:
				self.bot=result
				self.okbot=True
			else:
				self.okbot=False
		except Exception, e:
			log("Could not launch "+self.name)
			log(e)
			self.okbot=False
		return

	def undo(self):
		if self.okbot:
			self.bot.undo()

	def undo_resign(self):
		if self.okbot:
			self.bot.undo_resign()

	def place(self,move,color):
		if self.okbot:
			if not self.bot.place(move,color):
				#self.config(state='disabled')
				return False
			return True

	def quick_evaluation(self,color):
		return self.bot.quick_evaluation(color)

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


class LaunchingException(Exception):
	pass

def bot_starting_procedure(bot_name,bot_gtp_name,bot_gtp,sgf_g,profile="slow",silentfail=False):
	log("Bot starting procedure started with profile =",profile)
	log("\tbot name:",bot_name)
	log("\tbot gtp name",bot_gtp_name)
	if profile=="slow":
		command_entry="SlowCommand"
		parameters_entry="SlowParameters"
	elif profile=="fast":
		command_entry="FastCommand"
		parameters_entry="FastParameters"

	size=sgf_g.get_size()

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	try:
		try:
			bot_command_line=Config.get(bot_name, command_entry)
		except:
			raise LaunchingException(_("The config.ini file does not contain %s entry for %s !")%(command_entry, bot_name))


		if not bot_command_line:
			raise LaunchingException(_("The config.ini file %s entry for %s is empty!")%(command_entry, bot_name))

		log("Starting "+bot_name+"...")
		try:
			bot_command_line=[Config.get(bot_name, command_entry)]+Config.get(bot_name, parameters_entry).split()
			bot=bot_gtp(bot_command_line)
		except Exception,e:
			raise LaunchingException((_("Could not run %s using the command from config.ini file:")%bot_name)+"\n"+Config.get(bot_name, command_entry)+" "+Config.get(bot_name, parameters_entry)+"\n"+str(e))

		log(bot_name+" started")
		log(bot_name+" identification through GTP...")
		try:
			answer=bot.name()
		except Exception, e:
			raise LaunchingException((_("%s did not replied as expected to the GTP name command:")%bot_name)+"\n"+str(e))


		if answer!=bot_gtp_name:
			raise LaunchingException((_("%s did not identified itself as expected:")%bot_name)+"\n'"+bot_gtp_name+"' != '"+answer+"'")


		log(bot_name+" identified itself properly")
		log("Checking version through GTP...")
		try:
			bot_version=bot.version()
		except Exception, e:
			raise LaunchingException((_("%s did not replied as expected to the GTP version command:")%bot_name)+"\n"+str(e))

		log("Version: "+bot_version)
		log("Setting goban size as "+str(size)+"x"+str(size))
		try:
			ok=bot.boardsize(size)
		except:
			raise LaunchingException((_("Could not set the goboard size using GTP command. Check that %s is running in GTP mode.")%bot_name))

		if not ok:
			raise LaunchingException(_("%s rejected this board size (%ix%i)")%(bot_name,size,size))


		log("Clearing the board")
		bot.reset()

		board, unused = sgf_moves.get_setup_and_moves(sgf_g)

		log("Adding handicap stones, if any")
		positions=[]
		for colour, move0 in board.list_occupied_points():
			if move0 != None:
				row, col = move0
				move=ij2gtp((row,col))
				if colour in ('w',"W"):
					raise LaunchingException(_("The SGF file contains white handicap stones! %s cannot deal with that!")%bot_name)
				positions.append(move)
				"""
				if colour in ('w',"W"):
					log("Adding initial white stone at",move)
					bot.place_white(move)
				else:
					log("Adding initial black stone at",move)
					bot.place_black(move)
				"""
		if len(positions)>0:
			bot.set_free_handicap(positions)
			#log("Setting bot komi at",sgf_g.get_komi(),"+",len(positions))
			#bot.komi(sgf_g.get_komi()+len(positions))

		log("Setting komi at",sgf_g.get_komi())
		bot.komi(sgf_g.get_komi())

		log(bot_name+" initialization completed")

		bot.bot_name=bot_gtp_name
		bot.bot_version=bot_version
	except LaunchingException,e:
		if silentfail:
			log(e)
		else:
			show_error(e)
		return False
	return bot



def draw_logo(logo,event=None,stretch="horizontal"):

	for item in logo.find_all():
		logo.delete(item)

	width=event.width
	height=event.height

	if stretch=="horizontal":
		logo.config(height=width)
	else:
		logo.config(width=height)

	border=0.1
	w=width*(1-2*border)
	b=width*border

	for u in [1/4.,2/4.,3/4.]:
		for v in [1/4.,2/4.,3/4.]:
			x1=b+w*(u-1/8.)
			y1=b+w*(v-1/8.)
			x2=b+w*(u+1/8.)
			y2=b+w*(v+1/8.)

			logo.create_oval(x1, y1, x2, y2, fill="#ADC5E7", outline="")

	for k in [1/4.,2/4.,3/4.]:
		x1=b+k*w
		y1=b
		x2=x1
		y2=b+w
		logo.create_line(x1, y1, x2, y2, width=w*7/318., fill="#21409A")
		logo.create_line(y1, x1, y2, x2, width=w*7/318., fill="#21409A")

	for u,v in [(2/4.,1/4.),(3/4.,2/4.),(1/4.,3/4.),(2/4.,3/4.),(3/4.,3/4.)]:
		x1=b+w*(u-1/8.)
		y1=b+w*(v-1/8.)
		x2=b+w*(u+1/8.)
		y2=b+w*(v+1/8.)

		logo.create_oval(x1, y1, x2, y2, fill="black", outline="")




import getopt

import __main__
try:
	usage="usage: python "+__main__.__file__+" [--range=<range>] [--color=<both|black|white>] [--komi=<komi>] [--variation=<variation>] [--profil=<fast|slow>] [--no-gui] <sgf file1> <sgf file2> <sgf file3>"
except:
	log("Command line features are disabled")
	usage=""

def parse_command_line(filename,argv):
	g=open_sgf(filename)

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

	found=False
	for p,v in argv:
		if p=="--profil":
			if v.lower() in ("slow","fast"):
				profil=v
				found=True
			else:
				show_error("Wrong profil parameter\n"+usage)
				sys.exit()
	if not found:
		profil="slow"

	log("Profil:",profil)

	nogui=False
	for p,v in argv:
		if p=="--no-gui":
			nogui=True
			break

	return move_selection,intervals,variation,komi,nogui,profil

# from http://www.py2exe.org/index.cgi/WhereAmI
def we_are_frozen():
	"""Returns whether we are frozen via py2exe.
	This will affect how we find out where we are located."""

	return hasattr(sys, "frozen")


def module_path():
	""" This will get us the program's directory,
	even if we are frozen using py2exe"""

	if we_are_frozen():
		log("Apparently running from the executable.")
		return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))

	return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))



try:
	pathname=module_path()
except:
	pathname=os.path.dirname(__file__)

log('GRP path:', os.path.abspath(pathname))
config_file=os.path.join(os.path.abspath(pathname),"config.ini")
log('Config file:', config_file)

log("Reading language setting from config file")
Config = ConfigParser.ConfigParser()
Config.read(config_file)
lang=Config.get("General","Language")


available_translations={"en": u"English", "fr" : u"Français", "de" : u"Deutsch"}
if not lang:
	log("No language setting in the config file")
	log("System language detection:")
	import locale
	lang=locale.getdefaultlocale()[0].split('_')[0]
	log("System language:",lang,"("+locale.getdefaultlocale()[0]+")")
	if lang in available_translations:
		log("There is a translation available for lang="+lang)
	else:
		log("No translation available for lang="+lang)
		log("Falling back on lang=en")
		lang="en"
	log("Saving the lang parameter in config.ini")
	Config.set("General","Language",lang)
	Config.write(open(config_file,"w"))
else:
	if lang in available_translations:
		log("lang="+lang)
	else:
		log("Unkonwn language setting in config.ini (lang="+lang+")")
		log("Falling back on lang=en")
		lang="en"
		log("Saving the lang parameter in config.ini")
		Config.set("General","Language",lang)
		Config.write(open(config_file,"w"))

translations={}
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
			translation=translation.replace("\\\"","\"")
			if len(entry)>0 and len(translation)>0:
				translations[entry]=translation
			entry=""
			translation=""

prepare_translations()

def _(txt=None):
	global translations
	if not translations:
		return txt
	if translations.has_key(txt):
		return translations[txt]
	return txt

def batch_analysis(app,batch):
	#there appears to be a Tk 8.6 regression bug that leads to random "Tcl_AsyncDelete: async handler deleted by the wrong thread Abandon (core dumped)"
	#this happens when app=Tk() is detroyed after one analysis, and a new one is created for the next analysis
	#this bug is sidestepped by recycling the same app=Tk() for all analysis
	#see also: http://learning-python.com/python-changes-2014-plus.html#s35E
	
	try:
		if len(batch)==0:
			app.remove_popup(app)
			return
		
		app.add_popup(app)
		one_analysis=batch[0]

		if len(one_analysis)==1:
			if one_analysis[0].completed==False:
				app.after(1000,lambda: batch_analysis(app,batch))
			else:
				batch=batch[1:]
				app.after(1,lambda: batch_analysis(app,batch))
		else:
			run,filename,move_selection,intervals,variation,komi,profil=one_analysis
			log("File to analyse:",filename)
			popup=run(app,filename,move_selection,intervals,variation,komi,profil)
			app.add_popup(popup)
			popup.end_of_analysis=popup.close
			batch[0]=[popup]
			app.after(1,lambda: batch_analysis(app,batch))
	except Exception, e:
		log("Batch analysis failed")
		log(e)
		app.force_close()

		
def slow_profile_bots():
	from leela_analysis import Leela
	from gnugo_analysis import GnuGo
	from ray_analysis import Ray
	from aq_analysis import AQ
	from leela_zero_analysis import LeelaZero

	import ConfigParser

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	bots=[]
	for bot in [Leela, AQ, Ray, GnuGo, LeelaZero]:
		if Config.get(bot['name'],"SlowCommand")!="":
			bots.append(bot)
			bot['profile']="slow"
	return bots

def fast_profile_bots():
	from leela_analysis import Leela
	from gnugo_analysis import GnuGo
	from ray_analysis import Ray
	from aq_analysis import AQ
	from leela_zero_analysis import LeelaZero

	import ConfigParser

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	bots=[]
	for bot in [Leela, AQ, Ray, GnuGo, LeelaZero]:
		if Config.get(bot['name'],"FastReviewCommand")!="":
			bots.append(bot)
			bot['profile']="fast"
	return bots


def get_available(use):
	from leela_analysis import Leela
	from gnugo_analysis import GnuGo
	from ray_analysis import Ray
	from aq_analysis import AQ
	from leela_zero_analysis import LeelaZero

	import ConfigParser

	Config = ConfigParser.ConfigParser()
	Config.read(config_file)

	bots=[]
	for bot in [Leela, AQ, Ray, GnuGo, LeelaZero]:
		slow=False
		fast=False
		if Config.get(bot['name'],use)=="slow":
			slow=True
		elif Config.get(bot['name'],use)=="fast":
			fast=True
		elif Config.get(bot['name'],use)=="both":
			slow=True
			fast=True
		if slow:
			if Config.get(bot['name'],"SlowCommand")!="":
				bot2=dict(bot)
				bots.append(bot2)
				bot2['profile']="slow"
		if fast:
			if Config.get(bot['name'],"FastCommand")!="":
				bot2=dict(bot)
				bots.append(bot2)
				bot2['profile']="fast"
	return bots

try:
	if sys.platform=="darwin":
		raise Exception("wx and Tkinter do not work well together on MacOS")
	import wx
	wxApp = wx.App(None)
	def open_sgf_file(parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","sgffolder")
		dialog = wx.FileDialog(None,_('Select a file'), defaultDir=initialdir, wildcard=_("SGF file")+" (*.sgf;*.SGF)|*.sgf;*.SGF", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		filename = None
		if dialog.ShowModal() == wx.ID_OK:
			filename = dialog.GetPath()
		dialog.Destroy()
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","sgffolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

	def open_rsgf_file(parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","rsgffolder")
		dialog = wx.FileDialog(None, _('Select a file'), defaultDir=initialdir, wildcard=_("Reviewed SGF file")+" (*.rsgf;*.RSGF)|*.rsgf;*.RSGF", style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
		filename = None
		if dialog.ShowModal() == wx.ID_OK:
			filename = dialog.GetPath()
		dialog.Destroy()
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","rsgffolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

	def save_png_file(filename, parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","pngfolder")
		dialog = wx.FileDialog(None,_('Choose a filename'), defaultDir=initialdir,defaultFile=filename, wildcard=_("PNG image")+" (*.png;*.PNG)|*.png;*.PNG", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		filename = None
		if dialog.ShowModal() == wx.ID_OK:
			filename = dialog.GetPath()
		dialog.Destroy()
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","pngfolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

	def save_live_game(filename, parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","livefolder")
		dialog = wx.FileDialog(None,_('Choose a filename'), defaultDir=initialdir,defaultFile=filename, wildcard=_("SGF file")+" (*.sgf;*.SGF)|*.sgf;*.SGF", style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
		filename = None
		if dialog.ShowModal() == wx.ID_OK:
			filename = dialog.GetPath()
		dialog.Destroy()
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","livefolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

except Exception, e:
	print "Could not import the WX GUI library, please double check it is installed:"
	log(e)
	log("=> Falling back to tkFileDialog")
	import tkFileDialog
	def open_sgf_file(parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","sgffolder")
		filename=tkFileDialog.askopenfilename(initialdir=initialdir, parent=parent,title=_("Select a file"),filetypes = [(_('SGF file'), '.sgf')])
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","sgffolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename
	def open_rsgf_file(parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","rsgffolder")
		filename=tkFileDialog.askopenfilename(initialdir=initialdir, parent=parent,title=_('Select a file'),filetypes = [(_('Reviewed SGF file'), '.rsgf')])
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","rsgffolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

	def save_png_file(filename, parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","pngfolder")
		filename=tkFileDialog.asksaveasfilename(initialdir=initialdir, parent=parent,title=_('Choose a filename'),filetypes = [(_('PNG image'), '.png')],initialfile=filename)
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","pngfolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename

	def save_live_game(filename, parent=None):
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		initialdir = Config.get("General","livefolder")
		filename=tkFileDialog.asksaveasfilename(initialdir=initialdir, parent=parent,title=_('Choose a filename'),filetypes = [(_('SGF file'), '.sgf')],initialfile=filename)
		if filename:
			initialdir=os.path.dirname(filename)
			Config.set("General","livefolder",initialdir.encode("utf"))
			Config.write(open(config_file,"w"))
		return filename
		
def opposite_rate(value):
	return str(100-float(value[:-1]))+"%"

position_data_formating={}
position_data_formating["ES"]=_("%s score estimation before the move was played: %s")
position_data_formating["UBS"]=" • "+_("Upper bound: %s")
position_data_formating["LBS"]=" • "+_("Lower bound: %s")
position_data_formating["CBM"]=_("For this position, %s would play: %s")
position_data_formating["BWWR"]=_("%s black/white win probability for this position: %s")
position_data_formating["MCWR"]=_("%s Monte Carlo win probability for this move: %s")
position_data_formating["VNWR"]=_("%s Value Network win probability for this move: %s")
position_data_formating["B"]=_("Black to play, in the game, black played %s")
position_data_formating["W"]=_("White to play, in the game, white played %s")

def format_data(sgf_property,formating,value="",bot="Bot"):
	txt=formating[sgf_property]
	#print "formating["+sgf_property+"]",txt
	try:
		if sgf_property in ("ES","CBM","BWWR"):
			txt=txt%(bot,value)
	except:
		pass

	try:
		if sgf_property in ("B","W","BWWR","PNV","MCWR","VNWR","PLYO","EVAL","RAVE","UBS","LBS"):
			txt=txt%(value)
	except:
		pass

	try:
		if sgf_property in ("BKMV",):
			txt=txt
	except:
		pass

	return txt

variation_data_formating={}
variation_data_formating["ES"]=_("Score estimation for this variation: %s")
variation_data_formating["BWWR"]=_("black/white win probability for this variation: %s")
variation_data_formating["BKMV"]=_("Book move")
variation_data_formating["PNV"]=_("Policy network value for this variation: %s")
variation_data_formating["MCWR"]=_("Monte Carlo win probability for this variation: %s")
variation_data_formating["VNWR"]=_("Value network black/white win probability for this variation: %s")
variation_data_formating["PLYO"]=_("Number of playouts used to estimate this variation: %s")
variation_data_formating["EVAL"]=_("Evaluation for this variation: %s")
variation_data_formating["RAVE"]=_("RAVE(x%%: y) for this variation: %s")

def save_position_data(node,sgf_property,value):
	node.set(sgf_property,value)

def save_variation_data(node,sgf_property,value):
	node.set(sgf_property,value)


class Application(Tk):
	def __init__(self):
		Tk.__init__(self)
		self.popups=[]
		self.title('GoReviewPartner')
		try:
			ico = Image("photo", file="icon.gif")
			self.tk.call('wm', 'iconphoto', str(self), '-default', ico)
		except:
			log("(Could not load the application icon)")
		self.withdraw()
	
	def force_close(self):
		import os
		os._exit(0)
	
	def remove_popup(self,popup):
		log("Removing popup")
		self.popups.remove(popup)
		log("Totally",len(self.popups),"popups left")
		if len(self.popups)==0:
			time.sleep(2)
			log("")
			log("GoReviewPartner is leaving")
			log("Hope you enjoyed the experience!")
			log("")
			log("List of contributors")
			
			contributors_file_url=os.path.join(os.path.abspath(pathname),"AUTHORS")
			contributors_file = open(contributors_file_url,"r")
			contributors=contributors_file.read()
			contributors_file.close()

			for line in contributors.split('\n'):
				if not line:
					continue
				if line[0]=="#":
					continue
				log("\t",line)
			log("")
			log("You are welcomed to support GoReviewPartner (bug repports, code fixes, translations, ideas...). If you are interested, get in touch through Github Reddit, or Lifein19x19 !")
			if we_are_frozen():
				#running from py2exe
				raw_input()
			self.force_close()
			
	def add_popup(self,popup):
		if popup not in self.popups:
			log("Adding new popup")
			self.popups.append(popup)
			log("Totally",len(self.popups),"popups")
import mss
import mss.tools
def canvas2png(goban,filename):
	top = goban.winfo_rooty()
	left = goban.winfo_rootx()
	width = goban.winfo_width()
	height = goban.winfo_height()
	monitor = {'top': top, 'left': left, 'width': width, 'height': height}
	sct_img = mss.mss().grab(monitor)
	mss.tools.to_png(sct_img.rgb, sct_img.size, output=filename)


def get_variation_comments(one_variation):
	comments=''
	for sgf_property in ("BWWR","PNV","MCWR","VNWR","PLYO","EVAL","RAVE","ES","BKMV"):
		if one_variation.has_property(sgf_property):
			comments+=format_data(sgf_property,variation_data_formating,one_variation.get(sgf_property))+"\n"
	return comments
	
def get_position_comments(current_move,gameroot):
	comments=""
	if current_move==1:
		if gameroot.has_property("RSGF"):
			comments+=gameroot.get("RSGF")
		if gameroot.has_property("PB"):
			comments+=_("Black")+": "+gameroot.get("PB")+"\n"
		if gameroot.has_property("PW"):
			comments+=_("White")+": "+gameroot.get("PW")+"\n"
		
		if comments:
			comments+="\n"
	
	comments+=_("Move %i")%current_move
	game_move_color,game_move=get_node(gameroot,current_move).get_move()
	
	if not game_move_color:
		game_move_color=guess_color_to_play(gameroot,current_move)
	
	if game_move_color.lower()=="w":
		comments+="\n"+(position_data_formating["W"])%ij2gtp(game_move).upper()
	elif game_move_color.lower()=="b":
		comments+="\n"+(position_data_formating["B"])%ij2gtp(game_move).upper()
	
	node=get_node(gameroot,current_move)
	if node.has_property("CBM"):
		bot=gameroot.get("BOT")
		comments+="\n"+(position_data_formating["CBM"])%(bot,node.get("CBM"))
		try:
			if node[1].has_property("BKMV"):
				if node[1].get("BKMV")=="yes":
					comments+=" ("+variation_data_formating["BKMV"]+")"
		except:
			pass
	try:
		if node.has_property("BWWR"):
			if node[0].has_property("BWWR"):
				if node.get_move()[0].lower()=="b":
					comments+="\n\n"+_("Black win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("BWWR").split("/")[0]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("BWWR").split("/")[0]
					comments+=" (%+.2fpp)"%(float(node[0].get("BWWR").split("%/")[0])-float(node.get("BWWR").split("%/")[0]))
				else:
					comments+="\n\n"+_("White win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("BWWR").split("/")[1]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("BWWR").split("/")[1]
					comments+=" (%+.2fpp)"%(float(node[0].get("BWWR").split("%/")[1][:-1])-float(node.get("BWWR").split("%/")[1][:-1]))
	except:
		pass
	
	try:
		if node.has_property("VNWR"):
			if node[0].has_property("VNWR"):
				if node.get_move()[0].lower()=="b":
					comments+="\n\n"+_("Black Value Network win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("VNWR").split("/")[0]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("VNWR").split("/")[0]
					comments+=" (%+.2fpp)"%(float(node[0].get("VNWR").split("%/")[0])-float(node.get("VNWR").split("%/")[0]))
				else:
					comments+="\n\n"+_("White Value Network win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("VNWR").split("/")[1]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("VNWR").split("/")[1]
					comments+=" (%+.2fpp)"%(float(node[0].get("VNWR").split("%/")[1][:-1])-float(node.get("VNWR").split("%/")[1][:-1]))
	except:
		pass
	
	try:
		if node.has_property("MCWR"):
			if node[0].has_property("MCWR"):
				if node.get_move()[0].lower()=="b":
					comments+="\n\n"+_("Black Monte Carlo win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("MCWR").split("/")[0]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("MCWR").split("/")[0]
					comments+=" (%+.2fpp)"%(float(node[0].get("MCWR").split("%/")[0])-float(node.get("MCWR").split("%/")[0]))
				else:
					comments+="\n\n"+_("White Monte Carlo win probability:")
					comments+="\n • "+(_("before %s")%ij2gtp(game_move))+": "+node.get("MCWR").split("/")[1]
					comments+="\n • "+(_("after %s")%ij2gtp(game_move))+": "+node[0].get("MCWR").split("/")[1]
					comments+=" (%+.2fpp)"%(float(node[0].get("MCWR").split("%/")[1][:-1])-float(node.get("MCWR").split("%/")[1][:-1]))
	except:
		pass
	
	return comments

def get_node_number(node):
	k=0
	while node:
		node=node[0]
		if (node.get_move()[0]!=None) and (node.get_move()[1]!=None):
			k+=1
		else:
			break
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
