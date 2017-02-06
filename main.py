
from Tkinter import * 

import leela_analysis
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
		print "================closing popup"
		popup.close_app()
		print "================popup closed"
	print "closing"
	app.destroy()
	app.quit()
	exit()
	
def launch_analysis():
	global popups
	filename = tkFileDialog.askopenfilename(parent=app,title='Choose a file',filetypes = [('sgf', '.sgf')])
	print filename
	print "gamename:",filename[:-4]
	if not filename:
		return
	print "filename:",filename
	
	top = Toplevel()
	new_popup=leela_analysis.RunAnalysis(top,filename)
	new_popup.pack()
	popups.append(new_popup)
	top.mainloop()
	
Label(app).pack()
analysis_bouton=Button(app, text="Run *.sgf analysis", command=launch_analysis)
analysis_bouton.pack()


def launch_review():
	filename = tkFileDialog.askopenfilename(parent=app,title='Select a file',filetypes = [('sgf', '.r.sgf')])
	print filename
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
review_bouton=Button(app, text="Open *.r.sgf for review", command=launch_review)
review_bouton.pack()


def launch_settings():
	settings.OpenSettings(app)

def refresh():
	print "refreshing"
	global review_bouton, analysis_bouton
	Config = ConfigParser.ConfigParser()
	Config.read("config.ini")
	if Config.get("Leela","Command")=="" or Config.get("GnuGo","Command")=="":
		review_bouton.config(state='disabled')
		analysis_bouton.config(state='disabled')
	else:
		review_bouton.config(state='normal')
		analysis_bouton.config(state='normal')

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
print "terminated"
