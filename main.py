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

import leela_analysis,gnugo_analysis,ray_analysis,aq_analysis,leela_zero_analysis
import dual_view
import settings
import tkFileDialog
from toolbox import *
from toolbox import _


log("Checking availability of config file")
import ConfigParser
Config = ConfigParser.ConfigParser()
try:
	Config.readfp(open(config_file))
except Exception, e:
	show_error(_("Could not open the config file of Go Review Partner")+"\n"+str(e))
	sys.exit()


app = Tk()

app.title('GoReviewPartner')

bg=app.cget("background")
logo = Canvas(app,bg=bg,width=5,height=5)
logo.pack(fill=BOTH,expand=1)

def draw_logo(event=None):
	global logo
	
	for item in logo.find_all():
		logo.delete(item)
	
	width=event.width
	height=event.height
	logo.config(height=width)
	
	border=0.1
	w=width*(1-2*border)
	b=width*border
	
	for u in [1/4.,2/4.,3/4.]:
		for v in [1/4.,2/4.,3/4.]:
			x1=b+w*(u-1/8.)
			y1=b+w*(v-1/8.)
			x2=b+w*(u+1/8.)
			y2=b+w*(v+1/8.)
			
			logo.create_oval(x1, y1, x2, y2, fill="#ADC5E7", outline="")
	
	for k in [1/4.,2/4.,3/4.]:
		x1=b+k*w
		y1=b
		x2=x1
		y2=b+w
		logo.create_line(x1, y1, x2, y2, width=w*7/318., fill="#21409A")
		logo.create_line(y1, x1, y2, x2, width=w*7/318., fill="#21409A")
	
	for u,v in [(2/4.,1/4.),(3/4.,2/4.),(1/4.,3/4.),(2/4.,3/4.),(3/4.,3/4.)]:
		x1=b+w*(u-1/8.)
		y1=b+w*(v-1/8.)
		x2=b+w*(u+1/8.)
		y2=b+w*(v+1/8.)
		
		logo.create_oval(x1, y1, x2, y2, fill="black", outline="")
	

	

logo.bind("<Configure>",draw_logo)

label = Label(app, text=_("This is GoReviewPartner"))
label.pack(padx=5, pady=5)


popups=[]
from sys import exit
from time import sleep
def close_app():
	global popups, app
	for popup in popups:
		popup.close_app()
	log("closing")
	app.destroy()
	app.quit()
	exit()
	
def launch_analysis():
	global popups
	filename = tkFileDialog.askopenfilename(parent=app,title=_("Select a file"),filetypes = [(_('SGF file'), '.sgf')])
	log(filename)
	log("gamename:",filename[:-4])
	if not filename:
		return
	log("filename:",filename)
	
	top = Toplevel()
	
	bots=[]
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	if Config.get("Leela","Command")!="":
		bots.append(("Leela",leela_analysis.RunAnalysis))
	if Config.get("AQ","Command")!="":
		bots.append(("AQ",aq_analysis.RunAnalysis))
	if Config.get("Ray","Command")!="":
		bots.append(("Ray",ray_analysis.RunAnalysis))
	if Config.get("GnuGo","Command")!="":
			bots.append(("GnuGo",gnugo_analysis.RunAnalysis))
	if Config.get("Leela_Zero","Command")!="":
			bots.append(("Leela Zero",leela_zero_analysis.RunAnalysis))
	new_popup=RangeSelector(top,filename,bots=bots)
	new_popup.pack()
	popups.append(new_popup)
	top.mainloop()

analysis_bouton=Button(app, text=_("Run a SGF file analysis"), command=launch_analysis)
analysis_bouton.pack(fill=X,padx=5, pady=5)

def download_sgf_for_review():
	top = Toplevel()
	
	bots=[]
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	if Config.get("Ray","Command")!="":
		bots.append(("Ray",ray_analysis.RunAnalysis))
	if Config.get("Leela","Command")!="":
		bots.append(("Leela",leela_analysis.RunAnalysis))
	if Config.get("GnuGo","Command")!="":
		bots.append(("GnuGo",gnugo_analysis.RunAnalysis))
	if Config.get("AQ","Command")!="":
		bots.append(("AQ",aq_analysis.RunAnalysis))
	if Config.get("Leela_Zero","Command")!="":
		bots.append(("Leela Zero",leela_zero_analysis.RunAnalysis))
	new_popup=DownloadFromURL(top,bots=bots)
	new_popup.pack()
	popups.append(new_popup)
	top.mainloop()

download_bouton=Button(app, text=_("Download a SGF file for analysis"), command=download_sgf_for_review)
download_bouton.pack(fill=X,padx=5, pady=5)

def launch_review():
	filename = tkFileDialog.askopenfilename(parent=app,title=_('Select a file'),filetypes = [(_('SGF file reviewed'), '.rsgf')])
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
	
review_bouton=Button(app, text=_("Open a RSGF file for review"), command=launch_review)
review_bouton.pack(fill=X,padx=5, pady=5)


def launch_settings():
	settings.OpenSettings(app)

def refresh():
	log("refreshing")
	global review_bouton, analysis_bouton
	Config = ConfigParser.ConfigParser()
	Config.read(config_file)
	if Config.get("Leela","Command")=="" and Config.get("GnuGo","Command")=="" and Config.get("Ray","Command")=="" and Config.get("AQ","Command")=="" and Config.get("Leela_Zero","Command")=="": #j'ai honte :)
		#review_bouton.config(state='disabled')
		analysis_bouton.config(state='disabled')
		download_bouton.config(state='disabled')
	else:
		#review_bouton.config(state='normal')
		analysis_bouton.config(state='normal')
		download_bouton.config(state='normal')


bouton=Button(app, text=_("Settings"), command=launch_settings)
bouton.pack(fill=X,padx=5, pady=5)



app.protocol("WM_DELETE_WINDOW", close_app)
#app.wm_iconphoto(True, PhotoImage(file='../logo.png'))
try:
	ico = Image("photo", file="icon.gif")
	app.tk.call('wm', 'iconphoto', str(app), '-default', ico)
except:
	log("(Could not load the application icon)")
refresh()
app.refresh=refresh
app.mainloop()
log("terminated")
