# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from Tkinter import *
from gnugo_analysis import GnuGoSettings
from ray_analysis import RaySettings
from leela_analysis import LeelaSettings
from aq_analysis import AQSettings
from leela_zero_analysis import LeelaZeroSettings
from pachi_analysis import PachiSettings
from phoenixgo_analysis import PhoenixGoSettings
from gtp_bot import GtpBotSettings
from toolbox import *
from toolbox import _

class OpenSettings(Toplevel):
	def display_settings(self):
		if self.setting_frame:
			self.setting_frame.pack_forget()
		
		settings_dict={"GRP":self.display_GRP_settings, "AQ":AQSettings, "GnuGo":GnuGoSettings, "Leela":LeelaSettings, "Ray":RaySettings, "Leela Zero":LeelaZeroSettings, "Pachi":PachiSettings, "PhoenixGo":PhoenixGoSettings, "GtpBot": GtpBotSettings}
		
		self.setting_frame=Frame(self.right_column)
		self.setting_frame.parent=self
		key=self.setting_mode.get()
		new_settings=settings_dict[key](self.setting_frame)
		new_settings.grid(row=0,column=0, padx=5, pady=5)
		self.current_settings=new_settings
		
		self.setting_frame.pack(fill=BOTH, expand=1)
		self.focus()

			
	def display_GRP_settings(self,top_setting_frame):
		
		log("Initializing GRP setting interface")

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
		MaxVariationsToRecord.set(grp_config.get("Analysis","MaxVariations"))
		Entry(setting_frame, textvariable=MaxVariationsToRecord, width=30).grid(row=row,column=2)
		
		row+=1
		Label(setting_frame,text=_("Only keep variations where game move and bot move differ")).grid(row=row,column=1,sticky=W)
		NoVariationIfSameMove = BooleanVar(value=grp_config.getboolean("Analysis","NoVariationIfSameMove")) 
		NoVariationIfSameMoveCheckbutton=Checkbutton(setting_frame, text="", variable=NoVariationIfSameMove,onvalue=True,offvalue=False)
		NoVariationIfSameMoveCheckbutton.grid(row=row,column=2,sticky=W)
		NoVariationIfSameMoveCheckbutton.var=NoVariationIfSameMove
		
		row+=1
		Label(setting_frame,text=_("Save bot command line into RSGF file")).grid(row=row,column=1,sticky=W)
		SaveCommandLine = BooleanVar(value=grp_config.getboolean('Analysis', 'SaveCommandLine'))
		SaveCommandLineCheckbutton=Checkbutton(setting_frame, text="", variable=SaveCommandLine,onvalue=True,offvalue=False)
		SaveCommandLineCheckbutton.grid(row=row,column=2,sticky=W)
		SaveCommandLineCheckbutton.var=SaveCommandLine
		row+=1
		Label(setting_frame,text=_("Stop the analysis if the bot resigns")).grid(row=row,column=1,sticky=W)
		StopAtFirstResign = BooleanVar(value=grp_config.getboolean('Analysis', 'StopAtFirstResign'))
		StopAtFirstResignCheckbutton=Checkbutton(setting_frame, text="", variable=StopAtFirstResign,onvalue=True,offvalue=False)
		StopAtFirstResignCheckbutton.grid(row=row,column=2,sticky=W)
		StopAtFirstResignCheckbutton.var=StopAtFirstResign

		row+=1
		Label(setting_frame,text="").grid(row=row,column=1)
		row+=1
		Label(setting_frame,text=_("Parameters for the review")).grid(row=row,column=1,sticky=W)
		
		row+=1
		Label(setting_frame,text=_("Natural stone placement")).grid(row=row,column=1,sticky=W)
		FuzzyStonePlacement = StringVar() 
		FuzzyStonePlacement.set(grp_config.get("Review","FuzzyStonePlacement"))
		Entry(setting_frame, textvariable=FuzzyStonePlacement, width=30).grid(row=row,column=2)
		row+=1
		
		Label(setting_frame,text=_("Real game sequence deepness")).grid(row=row,column=1,sticky=W)
		RealGameSequenceDeepness = StringVar() 
		RealGameSequenceDeepness.set(grp_config.get("Review","RealGameSequenceDeepness"))
		Entry(setting_frame, textvariable=RealGameSequenceDeepness, width=30).grid(row=row,column=2)
		row+=1
		
		Label(setting_frame,text=_("Maximum number of variations to display during review")).grid(row=row,column=1,sticky=W)
		MaxVariationsToDisplay = StringVar() 
		MaxVariationsToDisplay.set(grp_config.get("Review","MaxVariations"))
		Entry(setting_frame, textvariable=MaxVariationsToDisplay, width=30).grid(row=row,column=2)
		row+=1
		
		Label(setting_frame,text=_("Blue/red coloring of the variations")).grid(row=row,column=1,sticky=W)
		VariationsColoring = StringVar()
		coloring={"blue_for_winning":_("Win rate > 50% in blue"),"blue_for_best":_("The best variation in blue"),"blue_for_better":_("Variations better than actual game move in blue")}
		VariationsColoring.set(coloring[grp_config.get("Review","VariationsColoring")])
		OptionMenu(setting_frame,VariationsColoring,*tuple(coloring.values())).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(setting_frame,text=_("Labels for the variations")).grid(row=row,column=1,sticky=W)
		values={"letter":_("Letters"),"rate":_("Percentages")}
		VariationsLabel = StringVar()
		VariationsLabel.set(values[grp_config.get("Review","VariationsLabel")])
		OptionMenu(setting_frame,VariationsLabel,*tuple(values.values())).grid(row=row,column=2,sticky=W)
		
		row+=1
		Label(setting_frame,text=_("Inverted mouse wheel")).grid(row=row,column=1,sticky=W)
		InvertedMouseWheel = BooleanVar(value=grp_config.getboolean('Review', 'InvertedMouseWheel'))
		InvertedMouseWheelCheckbutton=Checkbutton(setting_frame, text="", variable=InvertedMouseWheel,onvalue=True,offvalue=False)
		InvertedMouseWheelCheckbutton.grid(row=row,column=2,sticky=W)
		InvertedMouseWheelCheckbutton.var=InvertedMouseWheel

		Button(self.setting_frame,text=_("Save settings"),command=self.save).grid(row=1,column=0, padx=5, pady=5,sticky=W)

		self.Language=Language
		self.FuzzyStonePlacement=FuzzyStonePlacement
		self.RealGameSequenceDeepness=RealGameSequenceDeepness
		#self.GobanScreenRatio=GobanScreenRatio
		self.MaxVariationsToRecord=MaxVariationsToRecord
		self.SaveCommandLine=SaveCommandLine
		self.StopAtFirstResign=StopAtFirstResign
		self.MaxVariationsToDisplay=MaxVariationsToDisplay
		self.VariationsColoring=VariationsColoring
		self.InvertedMouseWheel=InvertedMouseWheel
		self.NoVariationIfSameMove=NoVariationIfSameMove
		self.VariationsColoring=VariationsColoring
		self.VariationsLabel=VariationsLabel
		
		setting_frame.save=self.save
		
		return setting_frame
	
	def close(self):
		log("closing popup")
		self.destroy()
		self.parent.remove_popup(self)
		log("done")
	
	def __init__(self,parent,refresh=None):
		Toplevel.__init__(self)
		self.parent=parent
		
		self.refresh=refresh
		
		self.title('GoReviewPartner')
		
		left_column=Frame(self, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)
		left_column.pack(side=LEFT, fill=Y)
		
		right_column=Frame(self, padx=5, pady=5, height=2, bd=1, relief=SUNKEN)	
		right_column.pack(side=LEFT, fill=BOTH, expand=1)
		
		self.setting_mode=StringVar()
		self.setting_mode.set("GRP") # initialize		
		Radiobutton(left_column, text="Go Review Partner",command=self.display_settings,variable=self.setting_mode, value="GRP",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="AQ",command=self.display_settings,variable=self.setting_mode, value="AQ",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="GnuGo",command=self.display_settings,variable=self.setting_mode, value="GnuGo",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Leela",command=self.display_settings,variable=self.setting_mode, value="Leela",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Ray",command=self.display_settings,variable=self.setting_mode, value="Ray",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Leela Zero",command=self.display_settings,variable=self.setting_mode, value="Leela Zero",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="Pachi",command=self.display_settings,variable=self.setting_mode, value="Pachi",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="PhoenixGo",command=self.display_settings,variable=self.setting_mode, value="PhoenixGo",indicatoron=0).pack(side=TOP, fill=X)
		Radiobutton(left_column, text="GTP bots",command=self.display_settings,variable=self.setting_mode, value="GtpBot",indicatoron=0).pack(side=TOP, fill=X)
		
		self.right_column=right_column
		self.setting_frame=None
		self.display_settings()
		self.protocol("WM_DELETE_WINDOW", self.close)
		
	def save(self):
		global lang, translations
		log("Saving GRP settings")
		for lang2, language in available_translations.iteritems():
			if language==self.Language.get():
				if lang!=lang2:
					grp_config.set("General","Language",lang2)
				break
		grp_config.set("Review","FuzzyStonePlacement",self.FuzzyStonePlacement.get())
		grp_config.set("Review","RealGameSequenceDeepness",self.RealGameSequenceDeepness.get())
		#grp_config.set("Review","GobanScreenRatio",self.GobanScreenRatio.get())
		grp_config.set("Analysis","MaxVariations",self.MaxVariationsToRecord.get())
		grp_config.set("Analysis","SaveCommandLine",self.SaveCommandLine.get())
		grp_config.set("Analysis","StopAtFirstResign",self.StopAtFirstResign.get())
		grp_config.set("Review","MaxVariations",self.MaxVariationsToDisplay.get())
		coloring={_("Win rate > 50% in blue"):"blue_for_winning",_("The best variation in blue"):"blue_for_best",_("Variations better than actual game move in blue"):"blue_for_better"}
		grp_config.set("Review","VariationsColoring",coloring[self.VariationsColoring.get()])
		grp_config.set("Review","InvertedMouseWheel",self.InvertedMouseWheel.get())
		grp_config.set("Analysis","NoVariationIfSameMove",self.NoVariationIfSameMove.get())
		labeling={_("Letters"):"letter",_("Percentages"):"rate"}
		grp_config.set("Review","VariationsLabel",labeling[self.VariationsLabel.get()])
		
		
		
		if self.refresh!=None:
			self.refresh()
		
	def test(self,gtp_bot,command,parameters):
		from gtp_terminal import Terminal
		
		command=command.get()
		parameters=parameters.get().split()
			
		if not command:
			log("Empty command line!")
			return
		
		popup=Terminal(self.parent,gtp_bot,[command]+parameters)
		self.parent.add_popup(popup)
		
if __name__ == "__main__":
	app = Application()
	popup=OpenSettings(app)
	app.add_popup(popup)
	app.mainloop()
