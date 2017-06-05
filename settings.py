
from Tkinter import *
import ConfigParser

class OpenSettings(Toplevel):
	def __init__(self,parent=None):
		Toplevel.__init__(self)
		self.parent=parent
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")

		row=0
		
		row+=3

		Label(self).grid(row=row,column=0)
		Label(self,text="Review").grid(row=row+1,column=1)
		Label(self,text="Fuzzy Stone").grid(row=row+2,column=1)
		FuzzyStonePlacement = StringVar() 
		FuzzyStonePlacement.set(Config.get("Review","FuzzyStonePlacement"))
		Entry(self, textvariable=FuzzyStonePlacement, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Real game sequence deepness").grid(row=row+2,column=1)
		RealGameSequenceDeepness = StringVar() 
		RealGameSequenceDeepness.set(Config.get("Review","RealGameSequenceDeepness"))
		Entry(self, textvariable=RealGameSequenceDeepness, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Goban/screen ratio").grid(row=row+2,column=1)
		GobanScreenRatio = StringVar() 
		GobanScreenRatio.set(Config.get("Review","GobanScreenRatio"))
		Entry(self, textvariable=GobanScreenRatio, width=30).grid(row=row+2,column=2)
		
		row+=3
		
		Label(self).grid(row=row,column=0)
		Label(self,text="Ray").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		RayCommand = StringVar() 
		RayCommand.set(Config.get("Ray","Command"))
		Entry(self, textvariable=RayCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Parameters").grid(row=row+2,column=1)
		RayParameters = StringVar() 
		RayParameters.set(Config.get("Ray","Parameters"))
		Entry(self, textvariable=RayParameters, width=30).grid(row=row+2,column=2)
		row+=1
		RayNeededForReview = BooleanVar(value=Config.getboolean('Ray', 'NeededForReview'))
		RayCheckbutton=Checkbutton(self, text="Needed for review", variable=RayNeededForReview,onvalue=True,offvalue=False)
		RayCheckbutton.grid(row=row+2,column=1)
		RayCheckbutton.var=RayNeededForReview
		
		row+=3
		
		Label(self).grid(row=row,column=0)
		Label(self,text="Leela").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		LeelaCommand = StringVar() 
		LeelaCommand.set(Config.get("Leela","Command"))
		Entry(self, textvariable=LeelaCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Parameters").grid(row=row+2,column=1)
		LeelaParameters = StringVar() 
		LeelaParameters.set(Config.get("Leela","Parameters"))
		Entry(self, textvariable=LeelaParameters, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Time per move").grid(row=row+2,column=1)
		TimePerMove = StringVar() 
		TimePerMove.set(Config.get("Leela","TimePerMove"))
		Entry(self, textvariable=TimePerMove, width=30).grid(row=row+2,column=2)
		row+=1
		LeelaNeededForReview = BooleanVar(value=Config.getboolean('Leela', 'NeededForReview'))
		LeelaCheckbutton=Checkbutton(self, text="Needed for review", variable=LeelaNeededForReview,onvalue=True,offvalue=False)
		LeelaCheckbutton.grid(row=row+2,column=1)
		LeelaCheckbutton.var=LeelaNeededForReview
		
		row+=3
		
		Label(self).grid(row=row,column=0)
		Label(self,text="GnuGo").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		GnugoCommand = StringVar() 
		GnugoCommand.set(Config.get("GnuGo","Command"))
		Entry(self, textvariable=GnugoCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Parameters").grid(row=row+2,column=1)
		GnugoParameters = StringVar() 
		GnugoParameters.set(Config.get("GnuGo","Parameters"))
		Entry(self, textvariable=GnugoParameters, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Variations").grid(row=row+2,column=1)
		GnugoVariations = StringVar() 
		GnugoVariations.set(Config.get("GnuGo","Variations"))
		Entry(self, textvariable=GnugoVariations, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Deepness").grid(row=row+2,column=1)
		GnugoDeepness = StringVar() 
		GnugoDeepness.set(Config.get("GnuGo","Deepness"))
		Entry(self, textvariable=GnugoDeepness, width=30).grid(row=row+2,column=2)
		row+=1
		GnugoNeededForReview = BooleanVar(value=Config.getboolean('GnuGo', 'NeededForReview'))
		GnugoCheckbutton=Checkbutton(self, text="Needed for review", variable=GnugoNeededForReview,onvalue=True,offvalue=False)
		GnugoCheckbutton.grid(row=row+2,column=1)
		GnugoCheckbutton.var=GnugoNeededForReview
		
		row+=3
		Label(self).grid(row=row,column=3)
		
		row+=3
		Button(self,text="Save settings",command=self.save).grid(row=row,column=1)
		Button(self,text="Close",command=self.destroy).grid(row=row,column=2)
		
		row+=100
		Label(self).grid(row=row,column=3)
		
		self.title('GoReviewPartner')
		
		self.FuzzyStonePlacement=FuzzyStonePlacement
		self.RealGameSequenceDeepness=RealGameSequenceDeepness
		self.GobanScreenRatio=GobanScreenRatio
		
		self.RayCommand=RayCommand
		self.RayParameters=RayParameters
		self.RayNeededForReview=RayNeededForReview
		
		self.LeelaCommand=LeelaCommand
		self.LeelaParameters=LeelaParameters
		self.TimePerMove=TimePerMove
		self.LeelaNeededForReview=LeelaNeededForReview
		
		self.GnugoCommand=GnugoCommand
		self.GnugoParameters=GnugoParameters
		self.GnugoVariations=GnugoVariations
		self.GnugoDeepness=GnugoDeepness
		self.GnugoNeededForReview=GnugoNeededForReview

		
	def save(self):
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		Config.set("Review","FuzzyStonePlacement",self.FuzzyStonePlacement.get())
		Config.set("Review","RealGameSequenceDeepness",self.RealGameSequenceDeepness.get())
		Config.set("Review","GobanScreenRatio",self.GobanScreenRatio.get())
		
		Config.set("Ray","Command",self.RayCommand.get())
		Config.set("Ray","Parameters",self.RayParameters.get())
		Config.set("Ray","NeededForReview",self.RayNeededForReview.get())
		
		Config.set("Leela","Command",self.LeelaCommand.get())
		Config.set("Leela","Parameters",self.LeelaParameters.get())
		Config.set("Leela","TimePerMove",self.TimePerMove.get())
		Config.set("Leela","NeededForReview",self.LeelaNeededForReview.get())
		
		Config.set("GnuGo","Command",self.GnugoCommand.get())
		Config.set("GnuGo","Parameters",self.GnugoParameters.get())
		Config.set("GnuGo","Variations",self.GnugoVariations.get())
		Config.set("GnuGo","Deepness",self.GnugoDeepness.get())
		Config.set("GnuGo","NeededForReview",self.GnugoNeededForReview.get())
		
		
		Config.write(open("config.ini","w"))
		
		if self.parent!=None:
			self.parent.refresh()
		
		
if __name__ == "__main__":
	top = Tk()
	OpenSettings()
	top.mainloop()
