
from Tkinter import *
import ConfigParser
from toolbox import log
from gnugo_analysis import GnuGoSettings
from ray_analysis import RaySettings
from leela_analysis import LeelaSettings
from aq_analysis import AQSettings

class OpenSettings(Toplevel):


	def display_settings(self):
		if self.setting_frame:
			self.setting_frame.pack_forget()
		
		settings_dict={"GRP":self.display_GRP_settings, "AQ":AQSettings, "GnuGo":GnuGoSettings, "Leela":LeelaSettings, "Ray":RaySettings}
		
		self.setting_frame=Frame(self.right_column)
		key=self.setting_mode.get()
		new_settings=settings_dict[key](self.setting_frame)
		new_settings.grid(row=0,column=0, padx=5, pady=5)
		
		Button(self.setting_frame,text="Save settings",command=new_settings.save).grid(row=1,column=0, padx=5, pady=5,sticky=W)
		
		self.setting_frame.pack()
		

			
	def display_GRP_settings(self,top_setting_frame):
		
		log("Initializing GRP setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read("config.ini")		
		
		setting_frame=Frame(top_setting_frame)
		
		row=0

		Label(setting_frame,text="Go Review Partner settings").grid(row=row+1,column=1)
		Label(setting_frame,text="Fuzzy Stone").grid(row=row+2,column=1)
		FuzzyStonePlacement = StringVar() 
		FuzzyStonePlacement.set(Config.get("Review","FuzzyStonePlacement"))
		Entry(setting_frame, textvariable=FuzzyStonePlacement, width=30).grid(row=row+2,column=2)
		row+=1
		Label(setting_frame,text="Real game sequence deepness").grid(row=row+2,column=1)
		RealGameSequenceDeepness = StringVar() 
		RealGameSequenceDeepness.set(Config.get("Review","RealGameSequenceDeepness"))
		Entry(setting_frame, textvariable=RealGameSequenceDeepness, width=30).grid(row=row+2,column=2)
		row+=1
		Label(setting_frame,text="Goban/screen ratio").grid(row=row+2,column=1)
		GobanScreenRatio = StringVar() 
		GobanScreenRatio.set(Config.get("Review","GobanScreenRatio"))
		Entry(setting_frame, textvariable=GobanScreenRatio, width=30).grid(row=row+2,column=2)
		
		setting_frame.save=self.save
		
		self.FuzzyStonePlacement=FuzzyStonePlacement
		self.RealGameSequenceDeepness=RealGameSequenceDeepness
		self.GobanScreenRatio=GobanScreenRatio
		
		return setting_frame
		
	def __init__(self,parent=None):
		Toplevel.__init__(self)
		self.parent=parent

		self.title('GoReviewPartner')
		
		left_column=Frame(self, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		left_column.grid(row=0,column=0,sticky=N)
		
		right_column=Frame(self, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		right_column.grid(row=0,column=1)		
		
		self.setting_mode=StringVar()
		self.setting_mode.set("GRP") # initialize		
		Radiobutton(left_column, text="Go Review Partner",command=self.display_settings,variable=self.setting_mode, value="GRP",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="AQ",command=self.display_settings,variable=self.setting_mode, value="AQ",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="GnuGo",command=self.display_settings,variable=self.setting_mode, value="GnuGo",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Leela",command=self.display_settings,variable=self.setting_mode, value="Leela",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Ray",command=self.display_settings,variable=self.setting_mode, value="Ray",indicatoron=0).pack(side=TOP, fill=X)
		


		self.right_column=right_column
		self.setting_frame=None
		self.display_settings()

		
		

		

		
	def save(self):
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
