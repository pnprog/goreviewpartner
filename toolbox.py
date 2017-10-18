
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
		tkMessageBox.showerror("Error",txt)
	except:
		log("ERROR: "+txt)

def show_info(txt):
	try:
		tkMessageBox.showinfo("Info",txt)
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
		
		log("Downloading",url)
		
		r=urllib2.Request(url,headers=headers)
		try:
			h=urllib2.urlopen(r)
		except:
			show_error("Could not download the URL")
			return
		filename=""
		
		sgf=h.read()
		
		if sgf[:7]!="(;FF[4]":
			log("not a sgf file")
			show_error("Not a sgf file!")
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
		text_file = open(filename, "w")
		text_file.write(sgf)
		text_file.close()
			
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
		new_file=open(filename,'w')
		new_file.write(sgf_content)
		new_file.close()
	except Exception,e:
		log("Could not save the RSGF file",filename)
		log(e)
		raise WriteException("Could not save the RSGF file: "+filename+"\n"+str(e))

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

class RangeSelector(Frame):
	def __init__(self,parent,filename,bots=None):
		Frame.__init__(self,parent)
		self.parent=parent
		self.filename=filename
		root = self
		root.parent.title('GoReviewPartner')
		self.bots=bots
		
		txt = open(self.filename)
		content=txt.read()
		txt.close()
		self.g = sgf.Sgf_game.from_string(clean_sgf(content))
		self.move_zero=self.g.get_root()
		nb_moves=get_moves_number(self.move_zero)
		self.nb_moves=nb_moves
		s = StringVar()
		s.set("all")
		row=0
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		if bots!=None:
			Label(self,text="Bot to use for analysis:").grid(row=row,column=1,sticky=N+W)
			self.bot_selection = Listbox(self,height=len(bots))
			self.bot_selection.grid(row=row,column=2,sticky=W)
			for bot,f in bots:
				self.bot_selection.insert(END, bot)
			self.bot_selection.selection_set(0)
			self.bot_selection.configure(exportselection=False)
			row+=1
			Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text="Select variation to be analysed").grid(row=3,column=1,sticky=W)
		self.leaves=get_all_sgf_leaves(self.move_zero)
		self.variation_selection=StringVar()
		self.variation_selection.trace("w", self.variation_changed)
		
		options=[]
		v=1
		for leaf,deep in self.leaves:
			options.append("Variation "+str(v)+" ("+str(deep)+" moves)")
			v+=1
		self.variation_selection.set(options[0])
		
		apply(OptionMenu,(self,self.variation_selection)+tuple(options)).grid(row=row,column=2,sticky=W)

		row+=1
		Label(self,text="").grid(row=row,column=1)
		
		row+=1
		Label(self,text="Select moves to be analysed").grid(row=row,column=1,sticky=W)
		
		row+=1
		self.r1=Radiobutton(self,text="Analyse all "+str(nb_moves)+" moves",variable=s, value="all")
		self.r1.grid(row=row,column=1,sticky=W)
		self.after(0,self.r1.select)
		
		row+=1
		r2=Radiobutton(self,text="Analyse only those moves: ",variable=s, value="only")
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
		Label(self,text="Select colors to be analysed").grid(row=row,column=1,sticky=W)
		
		c = StringVar()
		c.set("both")
		
		row+=1
		c0=Radiobutton(self,text="Black & white",variable=c, value="both")
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
		c1=Radiobutton(self,text="Black only"+black_player,variable=c, value="black")
		c1.grid(row=row,column=1,sticky=W)
		
		row+=1
		c2=Radiobutton(self,text="White only"+white_player,variable=c, value="white")
		c2.grid(row=row,column=1,sticky=W)
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Label(self,text="Confirm the value of komi").grid(row=row,column=1,sticky=W)
		
		komi_entry=Entry(self)
		komi_entry.grid(row=row,column=2,sticky=W)
		komi_entry.delete(0, END)
		
		try:
			komi=self.g.get_komi()
			komi_entry.insert(0, str(komi))
		except Exception, e:
			log("Error while reading komi value, please check:\n"+str(e))
			show_error("Error while reading komi value, please check:\n"+str(e))
			komi_entry.insert(0, "0")
		
		
		row+=10
		Label(self,text="").grid(row=row,column=1)
		row+=1
		Button(self,text="Start",command=self.start).grid(row=row,column=2,sticky=E)
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
			
			self.r1.config(text="Analyse all "+str(deep)+" moves")
			
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
			show_error("This variation is empty (0 move), the analysis cannot be performed!")
			return
		
		try:
			komi=float(self.komi_entry.get())
		except:
			show_error("Incorrect value for komi ("+str(self.komi_entry.get())+"), please double check.")
			return
		
		if self.bots!=None:
			bot_selection=int(self.bot_selection.curselection()[0])
			log("bot selection:",self.bots[bot_selection][0])
			RunAnalysis=self.bots[bot_selection][1]
		
		if self.mode.get()=="all":
			intervals="all moves"
			move_selection=range(1,self.nb_moves+1)
		else:
			move_selection=[]
			selection = self.only_entry.get()
			selection=selection.replace(" ","")
			intervals="moves "+selection
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
						show_error("Could not make sense of the move range.\nPlease indicate one or more move intervals (ie: \"10-20, 40,50-51,63,67\")")
						return
			move_selection=list(set(move_selection))
			move_selection=sorted(move_selection)
			
		if self.color.get()=="black":
			intervals+=" (black only)"
			log("black only")
			new_move_selection=[]
			for m in move_selection:
				one_move=go_to_move(self.move_zero,m)
				player_color,player_move=one_move.get_move()
				if player_color.lower()=='b':
					new_move_selection.append(m)
			move_selection=new_move_selection
		elif self.color.get()=="white":
			intervals+=" (white only)"
			log("white only")
			new_move_selection=[]
			for m in move_selection:
				one_move=go_to_move(self.move_zero,m)
				player_color,player_move=one_move.get_move()
				if player_color.lower()=='w':
					new_move_selection.append(m)
			move_selection=new_move_selection
		else:
			intervals+=" (both colors)"
			
		log("========= move selection")
		log(move_selection)
		
		log("========= variation")
		variation=int(self.variation_selection.get().split(" ")[1])-1
		log(variation)
		
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
			ok=self.initialize_bot()
		except Exception,e:
			self.error="Error while initializing the GTP bot:\n"+str(e)
			self.abort()
			return
		
		if not ok:
			return
		
		try:
			self.initialize_UI()
		except Exception,e:
			self.error="Error while initializing the graphical interface:\n"+str(e)
			self.abort()
			return
		self.root.after(500,self.follow_analysis)
	
	def run_analysis(self,current_move):
		
		#################################################
		##### here is the place to perform analysis #####
		#################################################
		
		log("Analysis for this move is completed")
	
	
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
			return
		except Exception,e:
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
			exit()
			

	def abort(self):
		try:
			self.lab1.config(text="Aborted")
			self.lab2.config(text="")
		except:
			pass
		log("Leaving follow_anlysis()")
		show_error("Analysis aborted:\n\n"+self.error)

	def follow_analysis(self):
		if self.error:
			self.abort()
			return
		
		if self.lock1.acquire(False):
			if self.total_done>0:
				self.time_per_move=1.0*(time.time()-self.t0)/self.total_done+1
				log("self.time_per_move=",(time.time()-self.t0),"/",self.total_done,"=",self.time_per_move)
			remaining_s=int((len(self.move_range)-self.total_done)*self.time_per_move)
			remaining_h=remaining_s/3600
			remaining_s=remaining_s-3600*remaining_h
			remaining_m=remaining_s/60
			remaining_s=remaining_s-60*remaining_m
			if self.time_per_move<>0:
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
			self.lab2.config(text="")
			self.pb["maximum"] = 100
			self.pb["value"] = 100
			
			try:
				import dual_view
				Button(self,text="Start review",command=self.start_review).pack()
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
		
		
		Label(root,text="Analysis of: "+os.path.basename(self.filename)).pack()
				
		self.lab1=Label(root)
		self.lab1.pack()
		
		self.lab2=Label(root)
		self.lab2.pack()
		
		self.lab1.config(text="Currently at move 1/"+str(self.max_move))
		
		self.pb = ttk.Progressbar(root, orient="horizontal", length=250,maximum=self.max_move+1, mode="determinate")
		self.pb.pack()

		current_move=1
		
		try:
			write_rsgf(self.filename[:-4]+".rsgf",self.g.serialise())
		except Exception,e:
			show_error(str(e))
			self.lab1.config(text="Aborted")
			self.lab2.config(text="")
			return

		self.lock2.acquire()
		self.t0=time.time()
		first_move=go_to_move(self.move_zero,1)
		first_comment="Analysis by GoReviewPartner"
		first_comment+="\nBot: "+self.bot_name+'/'+self.bot_version
		first_comment+="\nKomi: "+str(self.komi)
		first_comment+="\nIntervals: "+self.intervals
		first_move.add_comment_text(first_comment)
		threading.Thread(target=self.run_all_analysis).start()
		
		self.root=root


		



