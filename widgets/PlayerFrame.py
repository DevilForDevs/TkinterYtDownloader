import tkinter as tk
from tkinter import Label, X, BOTH

from widgets.commanWidgets.VideoPlayer import VideoPlayer


class PlayerFrame(tk.Frame):

    def __init__(self, master=None,title="VideoTitle",**kwargs):
        super().__init__(master, **kwargs)
        Label(self, text=title,anchor="w").pack(fill=X,padx=10,pady=5)
        self.player=VideoPlayer(self)
        self.player.pack(fill=BOTH,expand=True,padx=10,pady=5)

    def new_play(self,path):
        self.player.play(path)

    def playPause(self):
        self.player.toggle_play()






