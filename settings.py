
from Tkinter import *
import ConfigParser
from toolbox import log
from gnugo_analysis import GnuGoSettings
from ray_analysis import RaySettings
from leela_analysis import LeelaSettings

class OpenSettings(Toplevel):
	def __init__(self,parent=None):
		Toplevel.__init__(self)
		self.parent=parent
		log("Initializing GRP setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")

		row=0

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
		
		self.ray=RaySettings(self)
		self.ray.grid(row=row,column=1,columnspan=2)
		
		row+=3
		
		self.leela=LeelaSettings(self)
		self.leela.grid(row=row,column=1,columnspan=2)
		
		row+=3
		
		self.gnugo=GnuGoSettings(self)
		self.gnugo.grid(row=row,column=1,columnspan=2)
		
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
		
	def save(self):
		
		self.ray.save()
		self.leela.save()
		self.gnugo.save()
		
		log("Saving GRP settings")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")
		
		Config.set("Review","FuzzyStonePlacement",self.FuzzyStonePlacement.get())
		Config.set("Review","RealGameSequenceDeepness",self.RealGameSequenceDeepness.get())
		Config.set("Review","GobanScreenRatio",self.GobanScreenRatio.get())
		
		Config.write(open("config.ini","w"))
		
		if self.parent!=None:
			self.parent.refresh()
		
		
if __name__ == "__main__":
	top = Tk()
	OpenSettings()
	top.mainloop()
