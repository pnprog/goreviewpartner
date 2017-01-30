# -*- coding: utf-8 -*-  # Définition l'encodage des caractères

from Tkinter import *


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



def alert(text_to_display):
	popup=Toplevel()
	label= Label(popup,text=text_to_display)
	label.pack()
	ok_button = Button(popup, text="OK", command=popup.destroy)
	ok_button.pack()
	#popup.mainloop()


class OpenMove():
	def __init__(self,parent,move,dim,sgf):
		self.parent=parent
		self.move=move
		self.dim=dim
		self.sgf=sgf
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
		print "killing gnugo"
		self.gnugo.kill()
		print "killing leela"
		self.leela.kill()
		
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
		self.gnugo.undo()
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
			
			#self.gnugo.place_black(move)
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
			
			#self.leela.place_black(move)
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
				if self.gnugo.place(ij2gtp((i,j)),color):
					self.leela.place(ij2gtp((i,j)),color)
					self.history.append([copy(self.grid),copy(self.markup)])
					
					place(self.grid,i,j,color)
					self.grid[i][j]=color
					
					self.markup=[["" for row in range(dim)] for col in range(dim)]
					self.markup[i][j]=0
					
					self.goban.display(self.grid,self.markup)
					self.next_color=3-color
	
		
	def initialize(self):
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
		
		#Button(panel, text='undo',command=lambda :click_on_undo(self)).grid(column=0,row=1)
		Button(panel, text='undo',command=self.undo).grid(column=0,row=1)
		Button(panel, text='Gnugo',command=self.click_gnugo).grid(column=0,row=2)
		Button(panel, text='Leela',command=self.click_leela).grid(column=0,row=3)
		
		
		panel.grid(column=0,row=1,sticky=N)
		
		goban3 = Goban(dim,master=popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		goban3.grid(column=1,row=1)
		
		
		
		grid3=[[0 for row in range(dim)] for col in range(dim)]
		markup3=[["" for row in range(dim)] for col in range(dim)]
		
		print "========================"
		print "opening move",move
		
		leela_command_line=tuple(Config.get("Leela", "Command").split())
		leela=gtp(leela_command_line)
		leela.boardsize(dim)
		leela.reset()
		leela.komi(komi)
		
		gnugo_command_line=tuple(Config.get("GnuGo", "Command").split())
		gnugo=gtp(gnugo_command_line)
		gnugo.boardsize(dim)
		gnugo.reset()
		gnugo.komi(komi)
		
		board, _ = sgf_moves.get_setup_and_moves(self.sgf)
		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid3,row,col,1)
				leela.place_black(ij2gtp((row,col)))
				gnugo.place_black(ij2gtp((row,col)))
			else:
				print "WTF? colour=",colour
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
			
			leela.place(ij2gtp(ij),color)
			gnugo.place(ij2gtp(ij),color)
			
			if ij==None:
				print "(0)skipping because ij==None",ij
				continue

			
			
			
			i,j=ij
			place(grid3,i,j,color)
		
		
		if m>0:
			markup3[i][j]=0
		
		try:
			self.next_color=3-color
		except:
			self.next_color=1
			
		#display(goban3,grid3,markup3)
		goban3.display(grid3,markup3)
		
		self.goban=goban3
		self.grid=grid3
		self.markup=markup3
		self.gnugo=gnugo
		self.leela=leela
		
		popup.protocol("WM_DELETE_WINDOW", self.close)
		#goban3.bind("<Button-1>",lambda event: click_on_popup(event,popup))
		goban3.bind("<Button-1>",self.click)
		goban3.bind("<Button-2>",self.undo)
		goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
		
		self.history=[]
		
		

class DualView(Frame):
	def __init__(self,parent,filename):
		#Tk.__init__(self,parent)
		Frame.__init__(self,parent)
		
		self.parent=parent
		self.filename=filename
		self.initialize()
		
		self.current_move=1
		self.display_move(self.current_move)
		
		
		self.pressed=0

	def close_app(self):
		for popup in self.all_popups:
			popup.close()
			print "killing gnugo"
			popup.gnugo.kill()
			print "killing leela"
			popup.leela.kill()
		self.destroy()
		self.parent.destroy()



	def prev_move(self,event=None):
		if self.current_move>1:
			self.pressed=time.time()
			self.current_move-=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())
	
	def next_move(self,event=None):
		if self.current_move<get_node_number(self.gameroot):
			self.pressed=time.time()
			self.current_move+=1
			pf=partial(self.goto_move,move_number=self.current_move,pressed=self.pressed)
			self.parent.after(0,lambda: pf())


	def goto_move(self,move_number,pressed):
		self.move_number.config(text=str(move_number)+'/'+str(get_node_number(self.gameroot)))
		if self.pressed==pressed:
			self.display_move(self.current_move)
			
	def leave_variation(self,goban,grid,markup):
		self.comment2.config(text="")
		goban.display(grid,markup)

	def show_variation(self,event,goban,grid,markup,i,j):
		sequence=markup[i][j]
		temp_grid=copy(grid)
		temp_markup=copy(markup)
		
		for u in range(self.dim):
			for v in range(self.dim):
				if temp_markup[u][v]!=0:
					temp_markup[u][v]=''
		
		k=1
		for color,(u,v),s,comment,displaycolor in sequence:
			temp_grid[u][v]=color
			temp_markup[u][v]=k
			k+=1
		
		goban.display(temp_grid,temp_markup)
		
		self.comment2.config(text=comment)

		u=i+goban.mesh[i][j][0]
		v=j+goban.mesh[i][j][1]
		local_area=goban.draw_point(u,v,1,color="",outline="")
		goban.tag_bind(local_area, "<Leave>", lambda e: self.leave_variation(goban,grid,markup))




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

		for colour, move0 in board.list_occupied_points():
			if move0 is None:
				continue
			row, col = move0
			if colour=='b':
				place(grid1,row,col,1)
				place(grid2,row,col,1)
		
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
		
		
		
		#indicating last play with delta
		if m>0:
			if one_move.has_property("C"):
				self.comment1.config(text=one_move.get("C"))
			markup1[i][j]=0
			markup2[i][j]=0
		self.comment2.config(text='')
		
		#next sequence in current game ############################################################################
		main_sequence=[]
		for m in range(5):
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
			main_sequence.append([c,ij,"A",None,"blue"])
			if m==0:
				real_game_ij=ij
		try:
			i,j=one_move=get_node(self.gameroot,move).get_move()[1]
		except:
			self.prev_move()
			return
		markup1[i][j]=main_sequence
		
		#alternative sequences ####################################################################################
		parent=get_node(self.gameroot,move-1)
		if one_move==False:
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
			
			if ij==real_game_ij: displaycolor="blue"
			else: displaycolor="red"
			
			if one_alternative.get_move()[0]=='b': c=1
			else: c=2

			if one_alternative.has_property("C"): comment=one_alternative.get("C")
			else: comment=''
			alternative_sequence=[[c,ij,chr(64+a),comment,displaycolor]]
			while len(one_alternative)>0:
				one_alternative=one_alternative[0]
				ij=one_alternative.get_move()[1]
				if one_alternative.get_move()[0]=='b':c=1
				else:c=2
				alternative_sequence.append([c,ij,chr(64+a),comment,"whocare?"])
			i,j=parent[a].get_move()[1]
			markup2[i][j]=alternative_sequence
			
		goban1.display(grid1,markup1)
		goban2.display(grid2,markup2)

	def open_move(self):
		new_popup=OpenMove(self,self.current_move,self.dim,self.sgf)
		self.all_popups.append(new_popup)
		
	def initialize(self):
		
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
		Button(self, text='prev',command=self.prev_move).grid(column=1,row=1)
		Button(self, text='open',command=self.open_move).grid(column=2,row=1)
		Button(self, text='next',command=self.next_move).grid(column=3,row=1)

		self.move_number=Label(self,text='   ',background=bg)
		self.move_number.grid(column=2,row=2)

		self.parent.bind('<Left>', self.prev_move)
		self.parent.bind('<Right>', self.next_move)

		#Label(app,background=bg).grid(column=1,row=2)

		row=10

		Label(self,background=bg).grid(column=1,row=row-1)

		#self.goban1 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban1 = Goban(self.dim,master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		
		self.goban1.grid(column=1,row=row)
		Label(self, text='            ',background=bg).grid(column=2,row=row)
		#self.goban2 = Canvas(self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2 = Goban(self.dim, master=self, width=10, height=10,bg=bg,bd=0, borderwidth=0)
		self.goban2.grid(column=3,row=row)

		Label(self,text='   ',background=bg).grid(column=4,row=row+1)



		self.comment1=Label(self,text='',background=bg)
		self.comment1.grid(column=1,row=row+2)
		self.comment2=Label(self,text='',background=bg)
		self.comment2.grid(column=3,row=row+2)

		Label(self,text='   ',background=bg).grid(column=4,row=row+3)

		goban.show_variation=self.show_variation
	



from gomill import sgf, sgf_moves
import goban
goban.fuzzy=float(Config.get("Review", "FuzzyStonePlacement"))

if __name__ == "__main__":

	if len(sys.argv)==1:
		temp_root = Tk()
		filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',filetypes = [('sgf', '.r.sgf')])
		temp_root.destroy()
		print filename

		if not filename:
			sys.exit()
	else:
		filename=sys.argv[1]
	
	top = Tk()
	DualView(top,filename).pack()
	top.mainloop()

	
	
