from functools import partial
from copy import deepcopy as copy

space=10

fuzzy=0.2


from random import random,seed,choice

from Tkinter import Canvas


class Goban(Canvas):
	def __init__(self,dim,**kwargs):
		self.dim=dim
		self.space=space
		self.wood_color=(.9*236,.9*206,.9*124)
		Canvas.__init__(self,**kwargs)
		self.prepare_mesh()
		self.no_redraw=[]
		
		
	def prepare_mesh(self):
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
		k1=random()*0.05
		t=20
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
			
			self.wood.append([(x1+x2)/2-random()/2,y1,(x1+x2)/2+0.3+random()/2,y2,'#%02x%02x%02x' % (r0, g0, b0),(k1-k0)*dim])
			
			k0=k1
			k1+=0.005+random()*0.01
			k1=min(1,k1)
		t=10
		self.black_stones=[[(25+choice(range(0,t)),8+choice(range(0,t/2)),8+choice(range(0,t/2))) for d in range(dim)] for dd in range(dim)]
		self.white_stones=[[(25+choice(range(0,t)),8+choice(range(0,t/2)),8+choice(range(0,t/2))) for d in range(dim)] for dd in range(dim)]
		for i in range(dim):
			for j in range(dim):
				a,b,c=self.black_stones[i][j]
				self.black_stones[i][j]=['#%02x%02x%02x' % (a,a,a),'#%02x%02x%02x' % (a+b,a+b,a+b),'#%02x%02x%02x' % (a+b+c,a+b+c,a+b+c)]
				a,b,c=self.white_stones[i][j]
				self.white_stones[i][j]=['#%02x%02x%02x' % (255-a,255-a,255-a),'#%02x%02x%02x' % (255-a+b,255-a+b,255-a+b),'#%02x%02x%02x' % (255-a+b+c,255-a+b+c,255-a+b+c)]
				
	def ij2xy(self,i,j):
		space=self.space
		dim=self.dim
		y=(0.5+dim-i)*space
		x=(0.5+1.+j)*space
		return x,y

	def xy2ij(self,x,y):
		dim=self.dim
		space=self.space
		return int(round(0.5+dim-1.*y/space)),int(round(1.*x/space-0.5)-1)

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

	def draw_black_stone(self,i,j):
		u=i+self.mesh[i][j][0]
		v=j+self.mesh[i][j][1]
		c1,c2,c3=self.black_stones[i][j]
		self.draw_point(u,v,.9,color=c1,outline="#808080",width=1)
		self.draw_point(u-0.1,v+0.1,.5,color=c2,outline="")
		self.draw_point(u-0.1,v+0.1,.2,color=c3,outline="")
		
		#self.draw_point(u,v,.95,"black")
	
	def draw_white_stone(self,i,j):
		u=i+self.mesh[i][j][0]
		v=j+self.mesh[i][j][1]
		c1,c2,c3=self.white_stones[i][j]
		self.draw_point(u,v,.9,color=c1,outline="#808080",width=1)
		self.draw_point(u-0.1,v+0.1,.5,color=c2,outline="")
		self.draw_point(u-0.1,v+0.1,.2,color=c3,outline="")
		
		
		
		#self.draw_point(u,v,.95,"white")



	def display(self,grid,markup,freeze=False):
		if freeze:
			black="red"
			self.no_redraw=[]
		else:
			black="black"
		
		space=self.space
		dim=self.dim
		r,g,b=self.wood_color
		bg='#%02x%02x%02x' % (r, g, b)
		for item in self.find_all():
			if item not in self.no_redraw:
				self.delete(item)
		
		self.config(width=space*(1+dim+1), height=space*(1+dim+1))
		
		
		if len(self.no_redraw)==0:
			#self.no_redraw.append(self.draw_rectangle(-0.1-.5,-0.1-.5,dim-1+.5+0.1,dim-1+.5+0.1,black))
			#self.no_redraw.append(self.draw_rectangle(0-.5,0-.5,dim-1+.5,dim-1+.5,bg))
			self.no_redraw.append(self.draw_rectangle(0-1.5,0-1.5,dim-1+1.5,dim-1+1.5,bg))
			
			for x1,y1,x2,y2,c,w in self.wood:
				self.no_redraw.append(self.draw_line(x1,y1,x2,y2,c,width=w*space))
				
				#self.no_redraw.append(self.draw_line((x1+x2)/2,y1,(x1+x2)/2+0.3,y2,'#%02x%02x%02x' % (r0, g0, b0),width=(k1-k0)*dim*space+1))

			
			bg0=self.cget("background")
			
			self.no_redraw.append(self.draw_rectangle(-1.5  ,  -1.5  ,   -.5,    dim-1+1.5,bg0))
			self.no_redraw.append(self.draw_rectangle(dim-1+1.5  ,  -1.5  ,   dim-1+.5,    dim-1+1.5,bg0))
			self.no_redraw.append(self.draw_rectangle(-1.5  ,  -1.5  ,   dim-1+1.5 ,  -.5,bg0))
			self.no_redraw.append(self.draw_rectangle(-1.5,    dim-1+1.5 ,   dim-1+1.5,    dim-1+.5,bg0))
			
			self.no_redraw.append(self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   -.5,    dim-1+.5+0.1,"black"))
			self.no_redraw.append(self.draw_rectangle(dim-1+.5+0.1  ,  -0.1-.5  ,   dim-1+.5,    dim-1+.5+0.1,"black"))
			self.no_redraw.append(self.draw_rectangle(-0.1-.5  ,  -0.1-.5  ,   dim-1+.5 ,  -.5,"black"))
			self.no_redraw.append(self.draw_rectangle(-.5,    dim-1+.5 ,   dim-1+.5+.1,    dim-1+.5+.1,"black"))
			
			
			for i in range(dim):
				self.no_redraw.append(self.draw_line(i,0,i,dim-1,color=black))
				self.no_redraw.append(self.draw_line(0,i,dim-1,i,color=black))
				
				x,y=self.ij2xy(-1-0.1,i)
				self.no_redraw.append(self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=("Arial", str(int(space/2.5)))))
				x,y=self.ij2xy(dim,i)
				self.no_redraw.append(self.create_text(x,y, text="ABCDEFGHJKLMNOPQRSTUVWXYZ"[i],font=("Arial", str(int(space/2.5)))))
				x,y=self.ij2xy(i,-1-0.1)
				self.no_redraw.append(self.create_text(x,y, text=str(i+1),font=("Arial", str(int(space/2.5)))))
				x,y=self.ij2xy(i,dim+0.1)
				self.no_redraw.append(self.create_text(x,y, text=str(i+1),font=("Arial", str(int(space/2.5)))))

			if dim==19:
				for i,j in [[3,3],[3,9],[9,9],[3,15],[15,15],[15,9],[9,15],[15,3],[9,3]]:
					self.no_redraw.append(self.draw_point(i,j,0.3,black))
		
		
		
		for i in range(dim):
			for j in range(dim):
				markup_color='black'
				u=i+self.mesh[i][j][0]
				v=j+self.mesh[i][j][1]
				if grid[i][j]==1:
					#black
					#self.draw_point(u,v,.95,"black")
					self.draw_black_stone(i,j)
					markup_color='white'
				if grid[i][j]==2:
					#self.draw_point(u,v,.95,"white")
					self.draw_white_stone(i,j)
				
				if type(markup[i][j]) is int:
					if grid[i][j]==0:
						self.draw_point(u,v,0.6,color=bg,outline=bg)
					if markup[i][j]==0:
						
						k=0.6
						
						self.draw_line(u+0.5*k,v-0*k,u-0.255*k,v+0.435*k,markup_color,width=2)
						self.draw_line(u-0.255*k,v+0.435*k,u-0.255*k,v-0.435*k,markup_color,width=2)
						self.draw_line(u-0.255*k,v-0.435*k,u+0.5*k,v-0*k,markup_color,width=2)
					elif markup[i][j]==-1:
						if grid[i][j]==0:
							self.draw_point(i,j,.4,"black")
						else:
							self.draw_point(u,v,.4,"black")
					elif markup[i][j]==-2:
						if grid[i][j]==0:
							self.draw_point(i,j,.4,"white")
						else:
							self.draw_point(u,v,.4,"white")
					else:
						x,y=self.ij2xy(u,v)
						self.create_text(x,y, text=str(markup[i][j]),font=("Arial", str(int(space/2))),fill=markup_color)
						
						
				elif markup[i][j]=="":
					#do nothing
					pass
				else:
					sequence=markup[i][j]
					markup_color=sequence[0][4]
					letter_color=sequence[0][5]
					x,y=self.ij2xy(u,v)
					self.draw_point(u,v,0.8,color=bg,outline=markup_color)
					self.create_text(x,y, text=sequence[0][2],font=("Arial", str(int(space/2))),fill=letter_color)
					local_area=self.draw_point(u,v,1,color="",outline="")
					self.tag_bind(local_area, "<Enter>", partial(show_variation,goban=self,grid=grid,markup=markup,i=i,j=j))

		if freeze:
			self.no_redraw=[]
			self.update_idletasks()


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
