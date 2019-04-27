# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys, os

if (sys.version_info > (3, 0)):
	print("GoReviewPartner needs Python version 2 (e.g. 2.7.9) to run.")
	print("GoReviewPartner cannot work with verions 3 of Python at the moment.")
	print("Sorry about that :/")
	input()
	exit()

print("STDIN encoding:",sys.stdin.encoding)
print("STDOUT encoding:",sys.stdout.encoding)
print("STDERR encoding:",sys.stderr.encoding)
print("File system encoding:",sys.getfilesystemencoding())

try:
	from Tkinter import * 
except Exception:
	print("Could not import the Tkinter librairy, please double check it is installed.")
	raw_input()
	sys.exit()


import dual_view
import settings
from toolbox import *
from toolbox import _
from live_analysis import LiveAnalysisLauncher
from r2sgf import rsgf2sgf
from r2csv import rsgf2csv

class Main(Toplevel):
	def __init__(self,parent):
		Toplevel.__init__(self,parent)
		self.parent=parent
		
		bg=self.cget("background")


		self.popups=[]

		self.control_frame = Frame(self)
		
		label = Label(self.control_frame, text=_("This is GoReviewPartner"), font="-weight bold")
		label.pack(padx=5, pady=5)

		self.analysis_bouton=Button(self.control_frame, text=_("Run a SGF file analysis"), command=self.launch_analysis)
		self.analysis_bouton.pack(fill=X,padx=5, pady=5)
		
		self.download_bouton=Button(self.control_frame, text=_("Download a SGF file for analysis"), command=self.download_sgf_for_review)
		self.download_bouton.pack(fill=X,padx=5, pady=5)
		
		self.live_bouton=Button(self.control_frame, text=_("Run a live analysis"), command=self.launch_live_analysis)
		self.live_bouton.pack(fill=X,padx=5, pady=5)
		
		review_bouton=Button(self.control_frame, text=_("Open a RSGF file for review"), command=self.launch_review)
		review_bouton.pack(fill=X,padx=5, pady=5)
		
		r2sgf_bouton=Button(self.control_frame, text=_("Convert RSGF file to SGF file"), command=self.r2sgf)
		r2sgf_bouton.pack(fill=X,padx=5, pady=5)
		
		r2csv_bouton=Button(self.control_frame, text=_("Convert RSGF file to CSV file"), command=self.r2csv)
		r2csv_bouton.pack(fill=X,padx=5, pady=5)
		
		bouton=Button(self.control_frame, text=_("Settings"), command=self.launch_settings)
		bouton.pack(fill=X,padx=5, pady=5)

		self.control_frame.pack(fill=X, side=BOTTOM)
		
		self.logo_frame = Frame(self)

		logo = Canvas(self.logo_frame,bg=bg,width=5,height=5)
		logo.pack(fill=BOTH, expand=1)
		logo.bind("<Configure>",lambda e: draw_logo(logo,e))
		self.logo_frame.pack(fill=BOTH, side=BOTTOM, expand=1)

		self.protocol("WM_DELETE_WINDOW", self.close)
	
	def r2sgf(self):
		filename = open_rsgf_file(parent=self.parent)
		if not filename:
			return
		rsgf2sgf(filename)
		show_info(_("The file %s has been converted to %s")%(os.path.basename(filename),os.path.basename(filename)+".sgf"),parent=self.parent)

	def r2csv(self):
		filename = open_rsgf_file(parent=self.parent)
		if not filename:
			return
		rsgf2csv(filename)
		show_info(_("The file %s has been converted to %s")%(os.path.basename(filename),os.path.basename(filename)+".csv"),parent=self.parent)

	def close(self):
		for popup in self.popups[:]:
			popup.close()
		log("closing Main")
		self.destroy()
		self.parent.remove_popup(self)

	def launch_analysis(self):
		filename = open_sgf_file(parent=self)
		if not filename:
			return
		
		log("filename:",filename)
		
		new_popup=RangeSelector(self.parent,filename,bots=get_available())

		self.parent.add_popup(new_popup)

	def download_sgf_for_review(self):	
		new_popup=DownloadFromURL(self.parent,bots=get_available())
		self.parent.add_popup(new_popup)

	def launch_live_analysis(self):		
		new_popup=LiveAnalysisLauncher(self.parent)
		self.parent.add_popup(new_popup)

	def launch_review(self):
		filename = open_rsgf_file(parent=self.parent)
		if not filename:
			return
		
		new_popup=dual_view.DualView(self.parent,filename)
		
		self.parent.add_popup(new_popup)

	def launch_settings(self):
		new_popup=settings.OpenSettings(self.parent,refresh=self.refresh)
		self.parent.add_popup(new_popup)

	def refresh(self):
		log("refreshing")
		if len(get_available())==0:
			self.analysis_bouton.config(state='disabled')
			self.download_bouton.config(state='disabled')
			self.live_bouton.config(state='disabled')
		else:
			self.analysis_bouton.config(state='normal')
			self.download_bouton.config(state='normal')
			self.live_bouton.config(state='normal')
		
		if len(get_available())==0:
			self.live_bouton.config(state='disabled')
		else:
			self.live_bouton.config(state='normal')


if __name__ == "__main__":
	app = Application()
	if len(sys.argv)==1:
		popup=Main(app)
		popup.refresh()
		app.add_popup(popup)
		app.mainloop()
		
	else:
		
		opened=0
		for filename in argv[1:]:
			log(filename,"???")
			extension=filename[-4:].lower()
			log("extension",extension)
			if extension=="rsgf":
				opened+=1
				log("Opening",filename)
				popup=dual_view.DualView(app,filename)
				app.add_popup(popup)
			elif extension==".sgf":
				log("Opening",filename)
				popup=RangeSelector(app,filename,bots=get_available())
				app.add_popup(popup)
				opened+=1

		if not opened:
			popup=Main(app)
			popup.refresh()
			app.add_popup(popup)
		

	app.mainloop()

