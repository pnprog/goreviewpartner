import ttk
from Tkinter import *

from time import sleep
import threading

root = Tk()

pb = ttk.Progressbar(root, orient="horizontal", length=200, mode="determinate")
pb.pack()

Button(root,text='quit',command=root.destroy).pack()


def starteuh(pb):
	k=1
	while k<5:
		print k
		k+=1
		pb.step()
		sleep(1)

	

def launch():
	t1=threading.Thread(target=starteuh,args=(pb,))
	t1.start()
	t1.join()
	root.destroy()
	

#root.protocol("WM_DELETE_WINDOW", app)

root.after(100,launch)

root.mainloop()
