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


def ij2sgf(m):
	# (17,0) => ???
	
	if m==None:
		return "pass"
	i,j=m
	letters=['a','b','c','d','e','f','g','h','j','k','l','m','n','o','p','q','r','s','t']
	return letters[j]+letters[i]

from gomill import sgf, sgf_moves
from Tkinter import Tk, Label, Frame, StringVar, Radiobutton, W,E, Entry, END,Button,Toplevel
import tkFileDialog
import sys
import os
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




