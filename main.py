# -*- coding:Utf-8 -*-

import sys
print "STDIN encoding:",sys.stdin.encoding
print "STDOUT encoding:",sys.stdout.encoding
print "STDERR encoding:",sys.stderr.encoding
print "Fine system encoding:",sys.getfilesystemencoding()

from Tkinter import * 

import leela_analysis,gnugo_analysis,ray_analysis,aq_analysis
from toolbox import *
import dual_view
import settings
import ConfigParser
import tkFileDialog
app = Tk()

app.title('GoReviewPartner')
Label(app).pack()

label = Label(app, text="This is GoReviewPartner")
label.pack()


popups=[]
from sys import exit
from time import sleep
def close_app():
	global popups, app
	for popup in popups:
		log("================closing popup")
		popup.close_app()
		log("================popup closed")
	log("closing")
	app.destroy()
	app.quit()
	exit()
	
def launch_analysis():
	global popups
	filename = tkFileDialog.askopenfilename(parent=app,title='Choose a file',filetypes = [('sgf', '.sgf')])
	log(filename)
	log("gamename:",filename[:-4])
	if not filename:
		return
	log("filename:",filename)
	
	top = Toplevel()
	
	bots=[]
	Config = ConfigParser.ConfigParser()
	Config.read("config.ini")
	if Config.get("Ray","Command")!="":
		bots.append(("Ray",ray_analysis.RunAnalysis))
	if Config.get("Leela","Command")!="":
		bots.append(("Leela",leela_analysis.RunAnalysis))
	if Config.get("GnuGo","Command")!="":
			bots.append(("GnuGo",gnugo_analysis.RunAnalysis))
	
	new_popup=RangeSelector(top,filename,bots=bots)
	new_popup.pack()
	popups.append(new_popup)
	top.mainloop()

Label(app).pack()
analysis_bouton=Button(app, text="Run *.sgf analysis", command=launch_analysis)
analysis_bouton.pack()

def download_sgf_for_review():
	top = Toplevel()
	
	bots=[]
	Config = ConfigParser.ConfigParser()
	Config.read("config.ini")
	if Config.get("Ray","Command")!="":
		bots.append(("Ray",ray_analysis.RunAnalysis))
	if Config.get("Leela","Command")!="":
		bots.append(("Leela",leela_analysis.RunAnalysis))
	if Config.get("GnuGo","Command")!="":
		bots.append(("GnuGo",gnugo_analysis.RunAnalysis))
	if Config.get("AQ","Command")!="":
		bots.append(("AQ",aq_analysis.RunAnalysis))	
	new_popup=DownloadFromURL(top,bots=bots)
	new_popup.pack()
	popups.append(new_popup)
	top.mainloop()

Label(app).pack()
download_bouton=Button(app, text="Download *.sgf for analysis", command=download_sgf_for_review)
download_bouton.pack()

def launch_review():
	filename = tkFileDialog.askopenfilename(parent=app,title='Select a file',filetypes = [('sgf reviewed', '.rsgf')])
	log(filename)
	if not filename:
		return

	top = Toplevel()
	
	display_factor=.5
	
	screen_width = app.winfo_screenwidth()
	screen_height = app.winfo_screenheight()
	
	width=int(display_factor*screen_width)
	height=int(display_factor*screen_height)

	new_popup=dual_view.DualView(top,filename,min(width,height))
	new_popup.pack(fill=BOTH,expand=1)
	popups.append(new_popup)
	top.mainloop()
	
Label(app).pack()
review_bouton=Button(app, text="Open *.rsgf for review", command=launch_review)
review_bouton.pack()


def launch_settings():
	settings.OpenSettings(app)

def refresh():
	log("refreshing")
	global review_bouton, analysis_bouton
	Config = ConfigParser.ConfigParser()
	Config.read("config.ini")
	if Config.get("Leela","Command")=="" and Config.get("GnuGo","Command")=="" and Config.get("Ray","Command")=="" and Config.get("AQ","Command")=="":
		#review_bouton.config(state='disabled')
		analysis_bouton.config(state='disabled')
		download_bouton.config(state='disabled')
	else:
		#review_bouton.config(state='normal')
		analysis_bouton.config(state='normal')
		download_bouton.config(state='normal')

Label(app).pack()
bouton=Button(app, text="Settings", command=launch_settings)
bouton.pack()

Label(app).pack()
bouton=Button(app, text="Quit", command=close_app)
bouton.pack()

Label(app).pack()
app.protocol("WM_DELETE_WINDOW", close_app)

refresh()
app.refresh=refresh
app.mainloop()
log("terminated")
