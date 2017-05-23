
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
		
		row+=3
		
		Label(self).grid(row=row,column=0)
		Label(self,text="Leela").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		LeelaCommand = StringVar() 
		LeelaCommand.set(Config.get("Leela","Command"))
		Entry(self, textvariable=LeelaCommand, width=30).grid(row=row+2,column=2)
		row+=1
		Label(self,text="Time per move").grid(row=row+2,column=1)
		TimePerMove = StringVar() 
		TimePerMove.set(Config.get("Leela","TimePerMove"))
		Entry(self, textvariable=TimePerMove, width=30).grid(row=row+2,column=2)
		
		row+=3
		
		Label(self).grid(row=row,column=0)
		Label(self,text="GnuGo").grid(row=row+1,column=1)
		Label(self,text="Command").grid(row=row+2,column=1)
		GnugoCommand = StringVar() 
		GnugoCommand.set(Config.get("GnuGo","Command"))
		Entry(self, textvariable=GnugoCommand, width=30).grid(row=row+2,column=2)
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
		
		
		row+=3
		Label(self).grid(row=row,column=3)
		
		row+=3
		Button(self,text="Save settings",command=self.save).grid(row=row,column=1)
		Button(self,text="Close",command=self.destroy).grid(row=row,column=2)
		
		row+=100
		Label(self).grid(row=row,column=3)
		
		self.title('GoReviewPartner')
		
		self.TimePerMove=TimePerMove
		self.FuzzyStonePlacement=FuzzyStonePlacement
		self.LeelaCommand=LeelaCommand
		self.GnugoCommand=GnugoCommand
		self.GnugoVariations=GnugoVariations
		self.GnugoDeepness=GnugoDeepness
		self.RealGameSequenceDeepness=RealGameSequenceDeepness
		
	def save(self):
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		Config.set("Leela","TimePerMove",self.TimePerMove.get())
		Config.set("Review","FuzzyStonePlacement",self.FuzzyStonePlacement.get())
		Config.set("Review","RealGameSequenceDeepness",self.RealGameSequenceDeepness.get())
		Config.set("Leela","Command",self.LeelaCommand.get())
		Config.set("GnuGo","Command",self.GnugoCommand.get())
		Config.set("GnuGo","Variations",self.GnugoVariations.get())
		Config.set("GnuGo","Deepness",self.GnugoDeepness.get())
		
		Config.write(open("config.ini","w"))
		
		if self.parent!=None:
			self.parent.refresh()
		
		
if __name__ == "__main__":
	top = Tk()
	OpenSettings()
	top.mainloop()
