# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from functools import partial
fuzzy=0.0
from random import random,choice
from Tkinter import *
from Tkconstants import *
from math import sin, pi

class Intersection():
	def __init__(self,i,j,dim,space,anchor_x, anchor_y, offset, canvas):
		self.i=i
		self.j=j
		self.dim=dim
		self.space=space
		self.anchor_x=anchor_x
		self.anchor_y=anchor_y
		self.offset=offset
		self.canvas=canvas
		self.hidden=True
		
		x1=i+0.4
		y1=j
		x2=i-0.4
		y2=j
		self.s1=self.draw_line(x1,y1,x2,y2,color="black")
		
		x1=i
		y1=j+0.4
		x2=i
		y2=j-0.4
		self.s2=self.draw_line(x1,y1,x2,y2,color="black")

	def shine(self,remaining=100):
		if remaining==100:
			self.show()
		s=abs(sin((25-remaining)*(8*pi/100.))*5.)
		self.canvas.itemconfig(self.s1,width=int(s*self.space/22))
		self.canvas.itemconfig(self.s2,width=int(s*self.space/22))
		remaining-=1
		if remaining==0:
			self.hide()
		else:
			self.canvas.after(30,lambda: self.shine(remaining))

	def show(self):
		if self.hidden:
			self.canvas.move(self.s1,self.offset,self.offset)
			self.canvas.move(self.s2,self.offset,self.offset)
			self.hidden=False
	
	def hide(self):
		if not self.hidden:
			self.canvas.move(self.s1,-self.offset,-self.offset)
			self.canvas.move(self.s2,-self.offset,-self.offset)
			self.hidden=True

	def draw_line(self,i1,j1,i2,j2,color="black",width=1):
		x1,y1=self.ij2xy(i1,j1)
		x2,y2=self.ij2xy(i2,j2)
		
		if self.hidden:
			x1-=self.offset
			y1-=self.offset
			x2-=self.offset
			y2-=self.offset
		return self.canvas.create_line(x1,y1,x2,y2,fill=color,width=width)

	def ij2xy(self,i,j):
		space=self.space
		dim=self.dim
		y=(0.5+0.5+dim-i)*space+self.anchor_y
		x=(0.5+0.5+1.+j)*space+self.anchor_x
		return x,y

class Stone():
	def __init__(self,color,i,j,dim,space,anchor_x, anchor_y, offset, canvas, mesh, style):
		self.i=i
		self.j=j
		self.dim=dim
		self.space=space
		self.anchor_x=anchor_x
		self.anchor_y=anchor_y
		self.offset=offset
		self.mesh=mesh
		self.canvas=canvas
		self.style=style
		self.hidden=True
		
		if color=="black":
			self.create_black_stone()
		else:
			self.create_white_stone()

	def draw_point(self,i,j,diameter,color="black",outline="black",width=1):
		space=self.space
		x,y=self.ij2xy(i,j)
		if self.hidden:
			x-=self.offset
			y-=self.offset
		radius=diameter*space/2
		oval=self.canvas.create_oval(x-radius,y-radius,x+radius,y+radius,fill=color,outline=outline,width=width)
		return oval

	def create_black_stone(self):
		i=self.i
		j=self.j
		u=self.i+self.mesh[i][j][0]
		v=self.j+self.mesh[i][j][1]
		
		c1,c2,c3=self.style
		self.outline="black"
		
		self.s1=self.draw_point(u,v,.9,color=c1,outline=self.outline,width=1)
		self.s2=self.draw_point(u-0.1,v+0.1,.45,color=c2,outline="")
		self.s3=self.draw_point(u-0.15,v+0.15,.15,color=c3,outline="")
		self.s4=self.draw_point(u,v,.9,color="",outline=c1,width=0)
		
	def create_white_stone(self):
		i=self.i
		j=self.j
		u=self.i+self.mesh[i][j][0]
		v=self.j+self.mesh[i][j][1]
		
		c1,c2,c3=self.style
		self.outline="#808080"
		
		self.s1=self.draw_point(u,v,.9,color=c1,outline=self.outline,width=1)
		self.s2=self.draw_point(u-0.05,v+0.05,.7,color=c2,outline="")
		self.s3=self.draw_point(u-0.075,v+0.075,.5,color=c3,outline="")
		self.s4=self.draw_point(u,v,.9,color="",outline=c1,width=0)
		
	
	def shine(self,remaining=25):
		s=abs(sin((25-remaining)*(8*pi/100.))*2.)
		self.canvas.itemconfig(self.s4,width=int((0.1+s)*self.space/22))
		self.canvas.itemconfig(self.s1,outline="#D6AE72")
		
		remaining-=1
		if remaining==0:
			self.canvas.itemconfig(self.s4,width=0)
			self.canvas.itemconfig(self.s1,outline=self.outline)
		else:
			self.canvas.after(30,lambda: self.shine(remaining))
		
	def show(self):
		if self.hidden:
			self.canvas.move(self.s1,self.offset,self.offset)
			self.canvas.move(self.s2,self.offset,self.offset)
			self.canvas.move(self.s3,self.offset,self.offset)
			self.canvas.move(self.s4,self.offset,self.offset)
			self.hidden=False
	
	def hide(self):
		if not self.hidden:
			self.canvas.move(self.s1,-self.offset,-self.offset)
			self.canvas.move(self.s2,-self.offset,-self.offset)
			self.canvas.move(self.s3,-self.offset,-self.offset)
			self.canvas.move(self.s4,-self.offset,-self.offset)
			self.hidden=True
	
	def ij2xy(self,i,j):
		space=self.space
		dim=self.dim
		y=(0.5+0.5+dim-i)*space+self.anchor_y
		x=(0.5+0.5+1.+j)*space+self.anchor_x
		return x,y


class Goban(Canvas):
	def __init__(self,dim,size,**kwargs):
		self.space=size/(dim+1+1+1)
		self.dim=dim
		self.wood_color=(214,174,114) #same as gogui
		if "width" not in kwargs:
			kwargs["width"]=size
		if "height" not in kwargs:
			kwargs["height"]=size
		Canvas.__init__(self,**kwargs)
		
		self.anchor_x=0
		self.anchor_y=0
		
		self.define_goban_style()
		#self.create_goban()
		self.temporary_shapes=[]
		self.freeze=False
		
	def define_goban_style(self):
		f=fuzzy
		self.mesh=[[[0.0,0.0] for row in range(self.dim)] for col in range(self.dim)]
		if f>0:
			for i in range(self.dim):
				f1=random()*f-f/2
				f2=random()*f-f/2
				for j in range(self.dim):
					self.mesh[i][j][1]=f1+random()*.08-.04
					self.mesh[j][i][0]=f2+random()*.08-.04
		self.wood=[]
		dim=self.dim
		r,g,b=self.wood_color
		k0=0
		k1=random()*0.1 #width of vertical lines in wood texture
		t=7 #color shades 
		while k0<1:
			#tt=choice(range(-t,t+1))
			tt=2*random()*t-t
			r0=r+tt
			g0=g+tt
			b0=b+tt

			x1=0-.5+k0*dim
			y1=0-.5
			x2=0-.5+k1*dim
			y2=dim-1+.5
			
			self.wood.append([y1,(x1+x2)/2+random()-0.5,y2,(x1+x2)/2+random()-0.5,'#%02x%02x%02x' % (r0, g0, b0),(k1-k0)*dim])
			
			k0=k1
			k1+=0.005+random()*0.01
			k1=min(1,k1)
		
		
		self.black_stones_style=[[None for d in range(dim)] for dd in range(dim)]
		self.white_stones_style=[[None for d in range(dim)] for dd in range(dim)]
		t=10
		
		for i in range(dim):
			for j in range(dim):
				a,b,c=(25+choice(range(0,t)),8+choice(range(0,t/2)),8+choice(range(0,t/2)))
				style=['#%02x%02x%02x' % (a,a,a),'#%02x%02x%02x' % (a+b,a+b,a+b),'#%02x%02x%02x' % (a+b+c,a+b+c,a+b+c)]
				self.black_stones_style[i][j]=style
				
				a,b,c=(25+choice(range(0,t)),8+choice(range(0,t/2)),8+choice(range(0,t/2)))
				style=['#%02x%02x%02x' % (255-a,255-a,255-a),'#%02x%02x%02x' % (255-a+b,255-a+b,255-a+b),'#%02x%02x%02x' % (255-a+b+c,255-a+b+c,255-a+b+c)]
				self.white_stones_style[i][j]=style
	
	def create_goban(self):
		space=self.space
		if space<4:
			return
		
		dim=self.dim
		r,g,b=self.wood_color
		bg='#%02x%02x%02x' % (r, g, b)
		
		offset=-10000*space
		
		#let estimate the ratio fontsize/pixel
		idt=self.create_text(offset,offset, text="0",font=("Arial", 1000))
		x1,y1,x2,y2=self.bbox(idt) 
		ratio=max(x2-x1,y2-y1)/1000.
		fontsize=str(int(round(0.70*space/ratio)))
		self.font=("Arial",fontsize)
		
		self.draw_rectangle(0-1.5,0-1.5,dim-1+1.5,dim-1+1.5,bg)
		for x1,y1,x2,y2,c,w in self.wood:
			self.draw_line(x1,y1,x2,y2,c,width=w*space)
		
		bg0=self.cget("background")
		
		self.draw_rectangle(-1.5  ,  -1.5  ,   -.5,    dim-1+1.5,bg0)
		self.draw_rectangle(dim-1+1.5  ,  -1.5  ,   dim-1+.5,    dim-1+1.5,bg0)
		self.draw_rectangle(-1.5  ,  -1.5  ,   dim-1+1.5 ,  -.5,bg0)
		self.draw_rectangle(-1.5,    dim-1+1.5 ,   dim-1+1.5,    dim-1+.5,bg0)
		
		self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   -.5,    dim-1+.5+0.1,"black")
		self.draw_rectangle(dim-1+.5+0.1  ,  -0.1-.5  ,   dim-1+.5,    dim-1+.5+0.1,"black")
		self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   dim-1+.5 ,  -.5,"black")
		self.draw_rectangle(-.5,    dim-1+.5 ,   dim-1+.5+.1,    dim-1+.5+.1,"black")
		
		
		for i in range(dim):
			self.draw_line(i,0,i,dim-1,color="black",width=space/22.)
			self.draw_line(0,i,dim-1,i,color="black",width=space/22.)
			
			x,y=self.ij2xy(-1-0.1,i)
			self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=self.font)
			x,y=self.ij2xy(dim,i)
			self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=self.font)
			x,y=self.ij2xy(i,-1-0.1)
			self.create_text(x,y, text=str(i+1),font=self.font)
			x,y=self.ij2xy(i,dim+0.1)
			self.create_text(x,y, text=str(i+1),font=self.font)

		if dim==19:
			for i,j in [[3,3],[3,9],[9,9],[3,15],[15,15],[15,9],[9,15],[15,3],[9,3]]:
				self.draw_point(i,j,0.3,"black")
		
		#creating the stones
		self.black_stones=[[None for d in range(dim)] for dd in range(dim)]
		self.white_stones=[[None for d in range(dim)] for dd in range(dim)]
		self.intersections=[[None for d in range(dim)] for dd in range(dim)]
		for i in range(dim):
			for j in range(dim):
				style=self.black_stones_style[i][j]
				self.black_stones[i][j]=Stone("black",i,j,dim,self.space,self.anchor_x, self.anchor_y, offset, self, self.mesh,style)
				
				style=self.white_stones_style[i][j]
				self.white_stones[i][j]=Stone("white",i,j,dim,self.space,self.anchor_x, self.anchor_y, offset, self, self.mesh,style)
				
				self.intersections[i][j]=Intersection(i,j,dim,self.space,self.anchor_x, self.anchor_y, offset, self)
				
	def ij2xy(self,i,j):
		space=self.space
		dim=self.dim
		y=(0.5+0.5+dim-i)*space+self.anchor_y
		x=(0.5+0.5+1.+j)*space+self.anchor_x
		return x,y

	def xy2ij(self,x,y):
		dim=self.dim
		space=self.space

		x-=self.anchor_x
		y-=self.anchor_y

		return int(round(0.5+0.5+dim-1.*y/space)),int(round(1.*x/space-0.5-0.5)-1)

	def draw_point(self,i,j,diameter,color="black",outline="black",width=1):
		space=self.space
		x,y=self.ij2xy(i,j)
		radius=diameter*space/2
		oval=self.create_oval(x-radius,y-radius,x+radius,y+radius,fill=color,outline=outline,width=width)
		return oval

	def draw_line(self,i1,j1,i2,j2,color="black",width=1):
		x1,y1=self.ij2xy(i1,j1)
		x2,y2=self.ij2xy(i2,j2)
		return self.create_line(x1,y1,x2,y2,fill=color,width=width)

	def draw_rectangle(self,i1,j1,i2,j2,color="black",outline=""):
		x1,y1=self.ij2xy(i1,j1)
		x2,y2=self.ij2xy(i2,j2)
		return self.create_rectangle(x1,y1,x2,y2,fill=color,outline=outline)

	def reset(self):
		for item in self.find_all():
			self.delete(item)
		self.create_goban()
		
		try:
			self.grid
			self.markup
		except:
			self.grid=[[0 for row in range(self.dim)] for col in range(self.dim)]
			self.markup=[["" for row in range(self.dim)] for col in range(self.dim)]
		
		self.display(self.grid,self.markup,"keep")

	def display(self,grid,markup,freeze=False):
		if freeze!="keep":
			self.freeze=freeze
		self.grid=grid
		self.markup=markup
		space=self.space
		
		if space<4:
			return
		
		dim=self.dim
		for item in self.temporary_shapes:
			self.delete(item)
		self.temporary_shapes=[]
		

		
		if self.freeze:
			if freeze!="keep":
				self.config(cursor="watch")
			self.temporary_shapes.append(self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   -.5,    dim-1+.5+0.1,"red"))
			self.temporary_shapes.append(self.draw_rectangle(dim-1+.5+0.1  ,  -0.1-.5  ,   dim-1+.5,    dim-1+.5+0.1,"red"))
			self.temporary_shapes.append(self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   dim-1+.5 ,  -.5,"red"))
			self.temporary_shapes.append(self.draw_rectangle(-.5,    dim-1+.5 ,   dim-1+.5+.1,    dim-1+.5+.1,"red"))
			for i in range(dim):
				x,y=self.ij2xy(-1-0.1,i)
				self.temporary_shapes.append(self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=self.font,fill="red"))
				x,y=self.ij2xy(dim,i)
				self.temporary_shapes.append(self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=self.font,fill="red"))
				x,y=self.ij2xy(i,-1-0.1)
				self.temporary_shapes.append(self.create_text(x,y, text=str(i+1),font=self.font,fill="red"))
				x,y=self.ij2xy(i,dim+0.1)
				self.temporary_shapes.append(self.create_text(x,y, text=str(i+1),font=self.font,fill="red"))
		else:
			if freeze!="keep":
				self.config(cursor="cross")
		
		
		r,g,b=self.wood_color
		bg='#%02x%02x%02x' % (r, g, b)
		
		if int(self.cget("width"))==10:
			self.config(width=space*(dim+1+1+1), height=space*(dim+1+1+1))

		for i in range(dim):
			for j in range(dim):
				markup_color='black'
				u=i+self.mesh[i][j][0]
				v=j+self.mesh[i][j][1]
				if grid[i][j]==1:
					#black
					self.black_stones[i][j].show()
					self.white_stones[i][j].hide()
					markup_color='white'
				elif grid[i][j]==2:
					self.white_stones[i][j].show()
					self.black_stones[i][j].hide()
				else:
					self.black_stones[i][j].hide()
					self.white_stones[i][j].hide()
					
				if type(markup[i][j]) is int:
					if grid[i][j]==0:
						self.temporary_shapes.append(self.draw_point(u,v,0.6,color=bg,outline=bg))
					if markup[i][j]==0:
						self.temporary_shapes.append(self.draw_point(u,v,.4,color="",outline=markup_color,width=space/22.))

					elif markup[i][j]==-1:
						if grid[i][j]==0:
							self.temporary_shapes.append(self.draw_point(i,j,.4,"black"))
						else:
							self.temporary_shapes.append(self.draw_point(u,v,.4,"black"))
					elif markup[i][j]==-2:
						if grid[i][j]==0:
							self.temporary_shapes.append(self.draw_point(i,j,.4,"white"))
						else:
							self.temporary_shapes.append(self.draw_point(u,v,.4,"white"))
					else:
						x,y=self.ij2xy(u,v)
						self.temporary_shapes.append(self.create_text(x,y, text=str(markup[i][j]),font=self.font,fill=markup_color))
						
				elif type(markup[i][j])==type("abc"):
					
					if markup[i][j]!="":
						number_color="black"
						if grid[i][j]==1:
							number_color="white"
						elif grid[i][j]==0:
							self.temporary_shapes.append(self.draw_point(u,v,0.8,color=bg,outline=""))
						
						x,y=self.ij2xy(u,v)
						self.temporary_shapes.append(self.create_text(x,y, text=markup[i][j],font=self.font,fill=number_color))
				elif type(markup[i][j])==type([]):
					sequence=markup[i][j]
					markup_color=sequence[0][4]
					letter_color=sequence[0][5]
					x,y=self.ij2xy(u,v)
					self.temporary_shapes.append(self.draw_point(u,v,0.8,color=bg,outline=markup_color,width=space/22.))
					self.temporary_shapes.append(self.create_text(x,y, text=sequence[0][2],font=self.font,fill=letter_color))
					local_area=self.draw_point(u,v,1,color="",outline="")
					self.tag_bind(local_area, "<Enter>", partial(show_variation,goban=self,grid=grid,markup=markup,i=i,j=j))
					self.temporary_shapes.append(local_area)
				
				elif type(markup[i][j])==type(0.1): #heat map values
					value=markup[i][j]
					max_value=max([max([vv if type(vv)==type(0.1) else 0 for vv in ww]) for ww in markup])
					print value, "/", max_value, "=>", 
					value=value*1./max_value
					print value
					r1, g1, b1=self.wood_color
					r2, g2, b2=255, 0, 0
					r3, g3, b3=int(r1+(r2-r1)*value), int(g1+(g2-g1)*value), int(b1+(b2-b1)*value)
					print r1, g1, b1
					print r2, g2, b2
					print r3, g3, b3
					print "value", markup[i][j], value	
					color='#%02x%02x%02x' % (r3, g3, b3)
					print "value", markup[i][j], value, color
					self.temporary_shapes.append(self.draw_point(i,j,0.8,color=bg,outline=bg))
					self.temporary_shapes.append(self.draw_point(i,j,.7,color, outline=""))
		

		
		"""
		if freeze:
			self.no_redraw=[]
			self.update_idletasks()
		"""

def show_variation():
	pass



def countlib(grid,i,j,lib=0,tab=None):
	dim=len(grid)

	if not tab:
		start=True
		tab=[]
		for p in range(dim):tab.append([0]*dim)
	else:start=False
	color=grid[i][j]
	if color==0:
		return -1
	tab[i][j]=1

	for x,y in neighborhood(i,j,dim):
		if grid[x][y]==color and tab[x][y]==0:
			lib,tab=countlib(grid,x,y,lib,tab)
		elif grid[x][y]==0 and tab[x][y]==0:
			tab[x][y]=2
			lib+=1

	if start:
		return lib
	else:
		return lib,tab

def remove_group(grid,i,j):
	color=grid[i][j]
	grid[i][j]=0
	dim=len(grid)
	for x,y in neighborhood(i,j,dim):
		if grid[x][y]==color:
			remove_group(grid,x,y)

def place(grid,i,j,color):
	grid[i][j]=color
	dim=len(grid)
	for x,y in neighborhood(i,j,dim):
		if grid[x][y]>0 and grid[x][y]!=color:
			if countlib(grid,x,y)==0:
				remove_group(grid,x,y)


def neighborhood(i,j,dim):
	list=[]
	if 0 <= i+1 <= dim-1 and 0 <= j <= dim-1:
		list.append([i+1,j])
	if 0 <= i-1 <= dim-1 and 0 <= j <= dim-1:
		list.append([i-1,j])
	if 0 <= i <= dim-1 and 0 <= j-1 <= dim-1:
		list.append([i,j-1])
	if 0 <= i <= dim-1 and 0 <= j+1 <= dim-1:
		list.append([i,j+1])
	return list
