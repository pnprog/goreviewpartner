# -*- coding:Utf-8 -*-

import sys, os
print "STDIN encoding:",sys.stdin.encoding
print "STDOUT encoding:",sys.stdout.encoding
print "STDERR encoding:",sys.stderr.encoding
print "File system encoding:",sys.getfilesystemencoding()

try:
	from Tkinter import * 
except Exception, e:
	print "Could not import the Tkinter librairy, please double check it is installed:"
	print str(e)
	raw_input()
	sys.exit()


import dual_view
import settings
from toolbox import *
from toolbox import _
from live_analysis import LiveAnalysisLauncher


log("Checking availability of config file")
import ConfigParser
Config = ConfigParser.ConfigParser()
try:
	Config.readfp(open(config_file))
except Exception, e:
	show_error(_("Could not open the config file of Go Review Partner")+"\n"+str(e))
	sys.exit()

class Main(Toplevel):
	def __init__(self,parent):
		Toplevel.__init__(self,parent)
		self.parent=parent
		
		bg=self.cget("background")
		
		logo = Canvas(self,bg=bg,width=5,height=5)
		logo.pack(fill=BOTH,expand=1)
		logo.bind("<Configure>",lambda e: draw_logo(logo,e))

		label = Label(self, text=_("This is GoReviewPartner"), font="-weight bold")
		label.pack(padx=5, pady=5)

		self.popups=[]

		self.analysis_bouton=Button(self, text=_("Run a SGF file analysis"), command=self.launch_analysis)
		self.analysis_bouton.pack(fill=X,padx=5, pady=5)
		
		self.download_bouton=Button(self, text=_("Download a SGF file for analysis"), command=self.download_sgf_for_review)
		self.download_bouton.pack(fill=X,padx=5, pady=5)
		
		self.live_bouton=Button(self, text=_("Run a live analysis"), command=self.launch_live_analysis)
		self.live_bouton.pack(fill=X,padx=5, pady=5)
		
		review_bouton=Button(self, text=_("Open a RSGF file for review"), command=self.launch_review)
		review_bouton.pack(fill=X,padx=5, pady=5)
		
		bouton=Button(self, text=_("Settings"), command=self.launch_settings)
		bouton.pack(fill=X,padx=5, pady=5)

		self.protocol("WM_DELETE_WINDOW", self.close)
		
	def close(self):
		for popup in self.popups[:]:
			popup.close()
		log("closing Main")
		self.destroy()
		self.parent.remove_popup(self)

	def launch_analysis(self):
		filename = open_sgf_file(parent=self)
		log(filename)
		log("gamename:",filename[:-4])
		if not filename:
			return
		log("filename:",filename)
		
		new_popup=RangeSelector(self.parent,filename,bots=get_available("AnalysisBot"))

		self.parent.add_popup(new_popup)

	def download_sgf_for_review(self):	
		new_popup=DownloadFromURL(self.parent,bots=get_available("AnalysisBot"))
		self.parent.add_popup(new_popup)

	def launch_live_analysis(self):		
		new_popup=LiveAnalysisLauncher(self.parent)
		self.parent.add_popup(new_popup)

	def launch_review(self):
		filename = open_rsgf_file(parent=self.parent)
		log(filename)
		if not filename:
			return

		display_factor=.5
		
		screen_width = self.parent.winfo_screenwidth()
		screen_height = self.parent.winfo_screenheight()
		
		width=int(display_factor*screen_width)
		height=int(display_factor*screen_height)
		
		new_popup=dual_view.DualView(self.parent,filename,min(width,height))
		
		self.parent.add_popup(new_popup)

	def launch_settings(self):
		settings.OpenSettings(self)

	def refresh(self):
		log("refreshing")
		Config = ConfigParser.ConfigParser()
		Config.read(config_file)
		if len(get_available("AnalysisBot"))==0:
			self.analysis_bouton.config(state='disabled')
			self.download_bouton.config(state='disabled')
			self.live_bouton.config(state='disabled')
		else:
			self.analysis_bouton.config(state='normal')
			self.download_bouton.config(state='normal')
			self.live_bouton.config(state='normal')
		
		if len(get_available("LiveAnalysisBot"))==0:
			self.live_bouton.config(state='disabled')
		else:
			self.live_bouton.config(state='normal')


app = Application()
popup=Main(app)
popup.refresh()
app.add_popup(popup)

app.mainloop()
