# -*- coding: utf-8 -*-  # Définition l'encodage des caractères

from Tkinter import *
from tkSimpleDialog import askstring

import sys,time
import tkFileDialog

import os

from gtp import gtp

temp_root = Tk()
filename = tkFileDialog.askopenfilename(parent=temp_root,title='Choose a file',initialdir='/home2/pierre/Bureau/pandanet_games',filetypes = [('sgf', '.r.sgf')])
temp_root.destroy()
print filename


if not filename:
	sys.exit()

from gomill import sgf, sgf_moves
txt = open(filename)
g = sgf.Sgf_game.from_string(txt.read())
txt.close()

size=g.get_size()
komi=g.get_komi()
print "boardsize:",size
import goban
goban.dim=size
from goban import *




root=g.get_root()
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



def close_app():
	global app,all_popups
	for popup in all_popups:
		popup.destroy()
		print "killing gnugo"
		popup.gnugo.kill()
		print "killing leela"
		popup.leela.kill()
	app.destroy()


app=Tk()
app.protocol("WM_DELETE_WINDOW", close_app)

bg='silver'
app.configure(background=bg)

Label(app,text='   ',background=bg).grid(column=0,row=0)

def prev_move():
	global current_move
	if current_move>1:
		current_move-=1
		display_move(current_move)
def next_move():
	global current_move
	if current_move<get_node_number(root):
		current_move+=1
		display_move(current_move)


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


all_popups=[]


def lock_popup(popup):
	popup.locked=True

def unlock_popup(popup,after=False):
	if after:
		popup.locked=False
	else:
		popup.after(100,lambda: unlock_popup(popup,True))


def close_popup(popup):
	if popup.locked:
		return
	print "closing popup"
	popup.destroy()
	print "killing gnugo"
	popup.gnugo.kill()
	print "killing leela"
	popup.leela.kill()
	global all_popups
	all_popups.remove(popup)
	print "done"
	

def click_on_undo(popup):
	if popup.locked:
		print "failed!"
		return

	if len(popup.history)<1:
		return
	popup.grid,popup.markup=popup.history.pop()
	popup.next_color=3-popup.next_color
	display(popup.goban,popup.grid,popup.markup)
	popup.gnugo.undo()
	popup.leela.undo()


def alert(text_to_display):
	popup=Toplevel()
	label= Label(popup,text=text_to_display)
	label.pack()
	ok_button = Button(popup, text="OK", command=popup.destroy)
	ok_button.pack()
	popup.mainloop()


def click_gnugo(popup):
	if popup.locked:
		return
	
	print "gnugo play"
	color=popup.next_color
	n0=time.time()
	lock_popup(popup)
	display(popup.goban,popup.grid,popup.markup,True)
	if color==1:
		move=popup.gnugo.play_black()
	else:
		move=popup.gnugo.play_white()
	print "move=",move,"in",time.time()-n0,"s"
	
	if move.lower() not in ["pass","resign"]:
		i,j=gtp2ij(move)
		print 'i,j=',i,j
		
		popup.leela.place_black(move)
		popup.history.append([copy(popup.grid),copy(popup.markup)])
		
		place(popup.grid,i,j,color)
		popup.grid[i][j]=color
		popup.markup=[["" for row in range(dim)] for col in range(dim)]
		popup.markup[i][j]=0
		popup.next_color=3-color
	else:
		popup.gnugo.undo()
		display(popup.goban,popup.grid,popup.markup)
		if color==1:
			alert("GnuGo/black: "+move)
		else:
			alert("GnuGo/white: "+move)

	display(popup.goban,popup.grid,popup.markup)
	unlock_popup(popup)

def click_leela(popup):
	if popup.locked:
		return
	print "leela play"
	color=popup.next_color
	n0=time.time()
	lock_popup(popup)
	display(popup.goban,popup.grid,popup.markup,True)
	if color==1:
		move=popup.leela.play_black()
	else:
		move=popup.leela.play_white()
	print "move=",move,"in",time.time()-n0,"s"
	
	if move.lower() not in ["pass","resign"]:
		i,j=gtp2ij(move)
		print 'i,j=',i,j
		
		popup.gnugo.place_black(move)
		
		popup.history.append([copy(popup.grid),copy(popup.markup)])
		
		place(popup.grid,i,j,color)
		popup.grid[i][j]=color
		popup.markup=[["" for row in range(dim)] for col in range(dim)]
		popup.markup[i][j]=0
		popup.next_color=3-color
	else:
		popup.leela.undo()
		if color==1:
			alert("Leela/black: "+move)
		else:
			alert("Leela/white: "+move)
	
	display(popup.goban,popup.grid,popup.markup)
	unlock_popup(popup)
		

def click_on_popup(event,popup):

	#add/remove black stone
	#check pointer location
	i,j=xy2ij(event.x,event.y)
	color=popup.next_color
	if 0 <= i <= dim-1 and 0 <= j <= dim-1:
		#inside the grid
		#what is under the pointer ?
		
		if popup.grid[i][j] not in (1,2):
			#nothing, so we add a black stone			
			if popup.gnugo.place(ij2gtp((i,j)),color):
				popup.leela.place(ij2gtp((i,j)),color)
				popup.history.append([copy(popup.grid),copy(popup.markup)])
				
				place(popup.grid,i,j,color)
				popup.grid[i][j]=color
				
				popup.markup=[["" for row in range(dim)] for col in range(dim)]
				popup.markup[i][j]=0
				
				display(popup.goban,popup.grid,popup.markup)
				popup.next_color=3-color
				





def open_move():
	global all_popups
	popup=Toplevel()
	popup.configure(background=bg)
	popup.locked=False
	panel=Frame(popup)
	panel.configure(background=bg)
	
	Button(panel, text='undo',command=lambda :click_on_undo(popup)).grid(column=0,row=1)
	Button(panel, text='Gnugo',command=lambda :click_gnugo(popup)).grid(column=0,row=2)
	Button(panel, text='Leela',command=lambda :click_leela(popup)).grid(column=0,row=3)
	
	
	
	panel.grid(column=0,row=1,sticky=N)
	
	goban3 = Canvas(popup, width=10, height=10,bg=bg,bd=0, borderwidth=0)
	goban3.grid(column=1,row=1)
	
	
	
	grid3=[[0 for row in range(dim)] for col in range(dim)]
	markup3=[["" for row in range(dim)] for col in range(dim)]
	
	move=current_move
	print "========================"
	print "opening move",move
	
	leela=gtp(("/home/pierre-nicolas/Bureau/leela/leela_062_linux_x64", "--gtp", "--noponder"))
	leela.boardsize(dim)
	leela.reset()
	leela.komi(komi)
	
	gnugo=gtp(("gnugo", "--mode", "gtp"))
	gnugo.boardsize(dim)
	gnugo.reset()
	gnugo.komi(komi)
	
	all_popups.append(popup)
	
	board, _ = sgf_moves.get_setup_and_moves(g)
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
		one_move=get_node(root,m)
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
		popup.next_color=3-color
	except:
		popup.next_color=1
		
	display(goban3,grid3,markup3)
	popup.goban=goban3
	popup.grid=grid3
	popup.markup=markup3
	popup.gnugo=gnugo
	popup.leela=leela
	
	popup.protocol("WM_DELETE_WINDOW", lambda : close_popup(popup))
	goban3.bind("<Button-1>",lambda event: click_on_popup(event,popup))
	
	goban3.bind("<Button-2>",lambda event: click_on_undo(popup))
	goban3.bind("<Button-3>",lambda event: click_on_undo(popup))
	
	popup.history=[]
	
	
Button(app, text='prev',command=prev_move).grid(column=1,row=1)

Button(app, text='open',command=open_move).grid(column=2,row=1)
Button(app, text='next',command=next_move).grid(column=3,row=1)

move_number=Label(app,text='   ',background=bg)
move_number.grid(column=2,row=2)

app.bind('<Left>', lambda e: prev_move())
app.bind('<Right>', lambda e: next_move())

#Label(app,background=bg).grid(column=1,row=2)

row=10

Label(app,background=bg).grid(column=1,row=row-1)

goban1 = Canvas(app, width=10, height=10,bg=bg,bd=0, borderwidth=0)
goban1.grid(column=1,row=row)
Label(app, text='            ',background=bg).grid(column=2,row=row)
goban2 = Canvas(app, width=10, height=10,bg=bg,bd=0, borderwidth=0)
goban2.grid(column=3,row=row)

Label(app,text='   ',background=bg).grid(column=4,row=row+1)



comment1=Label(app,text='',background=bg)
comment1.grid(column=1,row=row+2)
comment2=Label(app,text='',background=bg)
comment2.grid(column=3,row=row+2)

Label(app,text='   ',background=bg).grid(column=4,row=row+3)

dim=size





def display_move(move):
	
	move_number.config(text=str(move)+'/'+str(get_node_number(root)))
	print "========================"
	print "displaying move",move
	grid1=[[0 for row in range(dim)] for col in range(dim)]
	markup1=[["" for row in range(dim)] for col in range(dim)]
	grid2=[[0 for row in range(dim)] for col in range(dim)]
	markup2=[["" for row in range(dim)] for col in range(dim)]
	board, _ = sgf_moves.get_setup_and_moves(g)

	for colour, move0 in board.list_occupied_points():
		if move0 is None:
			continue
		row, col = move0
		if colour=='b':
			place(grid1,row,col,1)
			place(grid2,row,col,1)
	
	m=0
	for m in range(1,move):
		one_move=get_node(root,m)
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
			display(goban1,grid1,markup1)
			display(goban2,grid2,markup2)
			return
	
	
	
	#indicating last play with delta
	if m>0:
		if one_move.has_property("C"):
			comment1.config(text=one_move.get("C"))
		markup1[i][j]=0
		markup2[i][j]=0
	comment2.config(text='')
	
	#next sequence in current game ############################################################################
	main_sequence=[]
	for m in range(5):
		one_move=get_node(root,move+m)
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
		i,j=one_move=get_node(root,move).get_move()[1]
	except:
		prev_move()
		return
	markup1[i][j]=main_sequence
	
	#alternative sequences ####################################################################################
	parent=get_node(root,move-1)
	if one_move==False:
		print "(1)leaving because one_move==False"
		return
	if len(parent)<=1:
		print "no alternative move"
		display(goban1,grid1,markup1)
		display(goban2,grid2,markup2)
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
		
	display(goban1,grid1,markup1)
	display(goban2,grid2,markup2)

		
def leave_variation(goban,grid,markup):
	comment2.config(text="")
	display(goban,grid,markup)


def show_variation(event,goban,grid,markup,i,j):
	global comment2
	sequence=markup[i][j]
	temp_grid=copy(grid)
	temp_markup=copy(markup)
	
	for u in range(dim):
		for v in range(dim):
			if temp_markup[u][v]!=0:
				temp_markup[u][v]=''
	
	k=1
	for color,(u,v),s,comment,displaycolor in sequence:
		temp_grid[u][v]=color
		temp_markup[u][v]=k
		k+=1
	
	display(goban,temp_grid,temp_markup)
	
	comment2.config(text=comment)

	u=i+mesh[i][j][0]
	v=j+mesh[i][j][1]
	local_area=draw_point(goban,u,v,1,color="",outline="")
	goban.tag_bind(local_area, "<Leave>", lambda e: leave_variation(goban,grid,markup))


goban.show_variation=show_variation

current_move=1
display_move(current_move)
app.mainloop()
