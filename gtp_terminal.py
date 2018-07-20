# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from Tkinter import *
import threading
from toolbox import *
from toolbox import _

class Terminal(Toplevel):
	def __init__(self,parent,bot_gtp,bot_command_line):
		Toplevel.__init__(self,parent)
		self.parent=parent
		self.protocol("WM_DELETE_WINDOW", self.close)
		try:
			self.bot=bot_gtp(bot_command_line)
		except Exception, e:
			self.close()
			show_error(_("Could not run the program:")+"\n"+unicode(e),self.parent)
			return
			
		threading.Thread(target=self.bot.consume_stdout).start()
		
		stdin_frame=Frame(self)
		stdin_frame.grid(row=1,column=1)
		
		self.gtp_command = StringVar() 
		self.gtp_command.set("genmove black")	
		entry=Entry(stdin_frame,textvariable=self.gtp_command)
		entry.grid(row=1,column=1,sticky=W)
		entry.bind("<Return>", self.send_gtp_command)
		
		Button(stdin_frame,text=_("Send GTP command"),command=self.send_gtp_command).grid(row=1,column=2,sticky=W)
		
		stdout_frame=Frame(self)
		stdout_frame.grid(row=2,column=1,sticky=N+S+E+W)
		self.stdout=Text(stdout_frame,width=60,height=10,bg="black",fg="white")
		self.stdout.pack(side="left", fill="both", expand=True)
		
		stderr_frame=Frame(self)
		stderr_frame.grid(row=3,column=1,sticky=N+S+E+W)
		self.stderr=Text(stderr_frame,width=60,height=20,bg="black",fg="white")
		self.stderr.pack(side="left", fill="both", expand=True)
		
		self.grid_columnconfigure(1, weight=1)
		self.grid_rowconfigure(2, weight=1)
		self.grid_rowconfigure(3, weight=1)
		
		self.follow_stdout()
		self.follow_stderr()
		
		
	def send_gtp_command(self,event=None):
		log("STDIN:",self.gtp_command.get())
		self.bot.write(self.gtp_command.get())
		
	def follow_stdout(self):
		try:
			msg=self.bot.stdout_queue.get(False)
			log("STDOUT:",msg)
			self.stdout.insert("end",msg)
			self.stdout.see("end")
			self.parent.after(10,self.follow_stdout)
		except:
			self.parent.after(500,self.follow_stdout)

	def follow_stderr(self):
		try:
			msg=self.bot.stderr_queue.get(False)
			log("STDERR:",msg)
			self.stderr.insert("end",msg)
			self.stderr.see("end")
			self.parent.after(10,self.follow_stderr)
		except:
			self.parent.after(500,self.follow_stderr)	

	def close(self):
		log("closing popup")
		try:
			self.bot.close()
		except:
			pass
		try:
			self.destroy()
			self.parent.remove_popup(self)
		except:
			pass
		log("done")

if __name__ == "__main__":
	from gnugo_analysis import *
	
	command=["gnugo","--mode=gtp"]
	
	top = Application()
	popup=Terminal(top,GnuGo_gtp,command)
	top.add_popup(popup)
	top.mainloop()

