# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from gtp import gtp
from Tkinter import *
from toolbox import *
from toolbox import _


def gtpbot_starting_procedure(sgf_g,profile,silentfail=False):
	return bot_starting_procedure("GtpBot","GtpBot",GtpBot_gtp,sgf_g,profile,silentfail)


class GtpBot_gtp(gtp):
	pass


class GtpBotSettings(BotProfiles):
	def __init__(self,parent,bot="GTP bot"):
		Frame.__init__(self,parent)
		self.parent=parent
		self.bot=bot
		self.profiles=get_bot_profiles(bot,False)
		profiles_frame=self
		
		self.listbox = Listbox(profiles_frame)
		self.listbox.grid(column=10,row=10,rowspan=10)
		self.update_listbox()
		
		row=10
		Label(profiles_frame,text=_("Profile")).grid(row=row,column=11,sticky=W)
		self.profile = StringVar()
		Entry(profiles_frame, textvariable=self.profile, width=30).grid(row=row,column=12)

		row+=1
		Label(profiles_frame,text=_("Command")).grid(row=row,column=11,sticky=W)
		self.command = StringVar() 
		Entry(profiles_frame, textvariable=self.command, width=30).grid(row=row,column=12)
		
		row+=1
		Label(profiles_frame,text=_("Parameters")).grid(row=row,column=11,sticky=W)
		self.parameters = StringVar()
		Entry(profiles_frame, textvariable=self.parameters, width=30).grid(row=row,column=12)

		row+=10
		buttons_frame=Frame(profiles_frame)
		buttons_frame.grid(row=row,column=10,sticky=W,columnspan=3)
		Button(buttons_frame, text=_("Add profile"),command=self.add_profile).grid(row=row,column=1,sticky=W)
		Button(buttons_frame, text=_("Modify profile"),command=self.modify_profile).grid(row=row,column=2,sticky=W)
		Button(buttons_frame, text=_("Delete profile"),command=self.delete_profile).grid(row=row,column=3,sticky=W)
		Button(buttons_frame, text=_("Test"),command=lambda: self.parent.parent.test(self.bot_gtp,self.command,self.parameters)).grid(row=row,column=4,sticky=W)
		self.listbox.bind("<Button-1>", lambda e: self.after(100,self.change_selection))
		
		self.index=-1
		
		self.bot_gtp=GtpBot_gtp

		
	def clear_selection(self):
		self.index=-1
		self.profile.set("")
		self.command.set("")
		self.parameters.set("")

	def change_selection(self):
		try:
			index=int(self.listbox.curselection()[0])
			self.index=index
		except:
			log("No selection")
			self.clear_selection()
			return
		data=self.profiles[index]
		self.profile.set(data["profile"])
		self.command.set(data["command"])
		self.parameters.set(data["parameters"])
		
	def add_profile(self):
		profiles=self.profiles
		if self.profile.get()=="":
			return
		data={"bot":self.bot}
		data["profile"]=self.profile.get()
		data["command"]=self.command.get()
		data["parameters"]=self.parameters.get()
		
		self.empty_profiles()
		profiles.append(data)
		self.create_profiles()
		self.clear_selection()
		
	def modify_profile(self):
		profiles=self.profiles
		if self.profile.get()=="":
			return
		
		if self.index<0:
			log("No selection")
			return
		index=self.index
		
		profiles[index]["profile"]=self.profile.get()
		profiles[index]["command"]=self.command.get()
		profiles[index]["parameters"]=self.parameters.get()
		
		self.empty_profiles()
		self.create_profiles()
		self.clear_selection()
		

class GtpBotOpenMove(BotOpenMove):
	def __init__(self,sgf_g,profile):
		BotOpenMove.__init__(self,sgf_g,profile)
		self.name='GtpBot'
		self.my_starting_procedure=gtpbot_starting_procedure

	
GtpBot={}
GtpBot['name']="GTP bot"
GtpBot['gtp_name']="GtpBot"
GtpBot['openmove']=GtpBotOpenMove
GtpBot['settings']=GtpBotSettings
GtpBot['gtp']=GtpBot_gtp
GtpBot['starting']=gtpbot_starting_procedure
