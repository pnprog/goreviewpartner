
from Tkinter import *
import ConfigParser
from gnugo_analysis import GnuGoSettings
from ray_analysis import RaySettings
from leela_analysis import LeelaSettings
from aq_analysis import AQSettings
from leela_zero_analysis import LeelaZeroSettings
from toolbox import log, config_file, _, available_translations, lang

class OpenSettings(Toplevel):


	def display_settings(self):
		if self.setting_frame:
			self.setting_frame.pack_forget()
		
		settings_dict={"GRP":self.display_GRP_settings, "AQ":AQSettings, "GnuGo":GnuGoSettings, "Leela":LeelaSettings, "Ray":RaySettings, "Leela Zero":LeelaZeroSettings}
		
		self.setting_frame=Frame(self.right_column)
		key=self.setting_mode.get()
		new_settings=settings_dict[key](self.setting_frame)
		new_settings.grid(row=0,column=0, padx=5, pady=5)
		
		Button(self.setting_frame,text=_("Save settings"),command=new_settings.save).grid(row=1,column=0, padx=5, pady=5,sticky=W)
		
		self.setting_frame.pack()
		self.focus()

			
	def display_GRP_settings(self,top_setting_frame):
		
		log("Initializing GRP setting interface")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)		
		
		setting_frame=Frame(top_setting_frame)
		
		row=0
		Label(setting_frame,text=_("%s settings")%"Go Review Partner", font="-weight bold").grid(row=row,column=1,sticky=W)
		row+=1
		Label(setting_frame,text="").grid(row=row,column=1)

		row+=1
		Label(setting_frame,text=_("General parameters")).grid(row=row,column=1,sticky=W)

		row+=1
		Label(setting_frame,text=_("Language")).grid(row=row,column=1,sticky=W)
		Language = StringVar()
		Language.set(available_translations[lang])		
		OptionMenu(setting_frame,Language,*tuple(available_translations.values())).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(setting_frame,text="").grid(row=row,column=1)
		row+=1
		Label(setting_frame,text=_("Parameters for the analysis")).grid(row=row,column=1,sticky=W)

		row+=1
		Label(setting_frame,text=_("Maximum number of variations to record during analysis")).grid(row=row,column=1,sticky=W)
		MaxVariationsToRecord = StringVar() 
		MaxVariationsToRecord.set(Config.get("Analysis","MaxVariations"))
		Entry(setting_frame, textvariable=MaxVariationsToRecord, width=30).grid(row=row,column=2)
		row+=1
		Label(setting_frame,text=_("Save bot command line into RSGF file")).grid(row=row,column=1,sticky=W)
		SaveCommandLine = BooleanVar(value=Config.getboolean('Analysis', 'SaveCommandLine'))
		SaveCommandLineCheckbutton=Checkbutton(setting_frame, text="", variable=SaveCommandLine,onvalue=True,offvalue=False)
		SaveCommandLineCheckbutton.grid(row=row,column=2,sticky=W)
		SaveCommandLineCheckbutton.var=SaveCommandLine
		row+=1
		Label(setting_frame,text=_("Stop the analysis if the bot resigns")).grid(row=row,column=1,sticky=W)
		StopAtFirstResign = BooleanVar(value=Config.getboolean('Analysis', 'StopAtFirstResign'))
		StopAtFirstResignCheckbutton=Checkbutton(setting_frame, text="", variable=StopAtFirstResign,onvalue=True,offvalue=False)
		StopAtFirstResignCheckbutton.grid(row=row,column=2,sticky=W)
		StopAtFirstResignCheckbutton.var=StopAtFirstResign

		row+=1
		Label(setting_frame,text="").grid(row=row,column=1)
		row+=1
		Label(setting_frame,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(setting_frame,text=_("Fuzzy Stone")).grid(row=row,column=1,sticky=W)
		FuzzyStonePlacement = StringVar() 
		FuzzyStonePlacement.set(Config.get("Review","FuzzyStonePlacement"))
		Entry(setting_frame, textvariable=FuzzyStonePlacement, width=30).grid(row=row,column=2)
		row+=1
		Label(setting_frame,text=_("Real game sequence deepness")).grid(row=row,column=1,sticky=W)
		RealGameSequenceDeepness = StringVar() 
		RealGameSequenceDeepness.set(Config.get("Review","RealGameSequenceDeepness"))
		Entry(setting_frame, textvariable=RealGameSequenceDeepness, width=30).grid(row=row,column=2)
		row+=1
		Label(setting_frame,text=_("Goban/screen ratio")).grid(row=row,column=1,sticky=W)
		GobanScreenRatio = StringVar() 
		GobanScreenRatio.set(Config.get("Review","GobanScreenRatio"))
		Entry(setting_frame, textvariable=GobanScreenRatio, width=30).grid(row=row,column=2)
		

		row+=1
		Label(setting_frame,text=_("Maximum number of variations to display during review")).grid(row=row,column=1,sticky=W)
		MaxVariationsToDisplay = StringVar() 
		MaxVariationsToDisplay.set(Config.get("Review","MaxVariations"))
		Entry(setting_frame, textvariable=MaxVariationsToDisplay, width=30).grid(row=row,column=2)

		self.Language=Language
		self.FuzzyStonePlacement=FuzzyStonePlacement
		self.RealGameSequenceDeepness=RealGameSequenceDeepness
		self.GobanScreenRatio=GobanScreenRatio
		self.MaxVariationsToRecord=MaxVariationsToRecord
		self.SaveCommandLine=SaveCommandLine
		self.StopAtFirstResign=StopAtFirstResign
		self.MaxVariationsToDisplay=MaxVariationsToDisplay
		
		setting_frame.save=self.save
		
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
		Radiobutton(left_column, text="Leela Zero",command=self.display_settings,variable=self.setting_mode, value="Leela Zero",indicatoron=0).pack(side=TOP, fill=X)


		self.right_column=right_column
		self.setting_frame=None
		self.display_settings()

	def save(self):
		global lang, translations
		log("Saving GRP settings")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		for lang2, language in available_translations.iteritems():
			if language==self.Language.get():
				if lang!=lang2:
					Config.set("General","Language",lang2)
				break
		Config.set("Review","FuzzyStonePlacement",self.FuzzyStonePlacement.get())
		Config.set("Review","RealGameSequenceDeepness",self.RealGameSequenceDeepness.get())
		Config.set("Review","GobanScreenRatio",self.GobanScreenRatio.get())
		Config.set("Analysis","MaxVariations",self.MaxVariationsToRecord.get())
		Config.set("Analysis","SaveCommandLine",self.SaveCommandLine.get())
		Config.set("Analysis","StopAtFirstResign",self.StopAtFirstResign.get())
		Config.set("Review","MaxVariations",self.MaxVariationsToDisplay.get())
		
		Config.write(open(config_file,"w"))
		
		if self.parent!=None:
			self.parent.refresh()
		
		
if __name__ == "__main__":
	top = Tk()
	OpenSettings()
	top.mainloop()
