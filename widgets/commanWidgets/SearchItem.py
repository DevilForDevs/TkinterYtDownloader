import os
import tkinter
import tkinter as tk
from tkinter import Label, Button
from tkinter.constants import X, RIGHT, LEFT

from PIL import Image, ImageTk


# https://www.youtube.com/watch?v=Mc_bgEn7FkA
class SearchItem(tk.Frame):

    def __init__(self, master=None,vid=None,title=None,duration=None,formatSelect=None, **kwargs):
        super().__init__(master, **kwargs)
        dir_path = "thumbnail"
        self.formatSelected=formatSelect
        os.makedirs(dir_path, exist_ok=True)
        thumbnail_img = Image.open(f"{dir_path}/{vid}.jpg")  # Use your actual image path
        thumbnail_img = thumbnail_img.resize((100, 100))
        thumbnail_photo = ImageTk.PhotoImage(thumbnail_img)
        thumbnail = tk.Label(self, image=thumbnail_photo) if thumbnail_photo else tk.Label(
            self,
            text="No Image",
            width=15)
        if thumbnail_photo:
            thumbnail.image = thumbnail_photo
        thumbnail.pack(side=RIGHT)
        info=tkinter.Frame(self,)
        Label(info,text=title,anchor="w").pack(fill=X,pady=5)
        Button(info, text="Download Mp4",command=lambda :self.formatSelected(vid,"video/mp4"), width=20, ).pack(side=LEFT,)
        Button(info, text="Download Webm",command=lambda :self.formatSelected(vid,"video/webm"), width=20,).pack(side=LEFT,padx=5)
        Button(info, text="Download Mp3",command=lambda :self.formatSelected(vid,"audio/mp4"), width=20).pack(side=LEFT)
        info.pack(fill=X,padx=10)

        subINfo=tk.Frame(self)
        Button(subINfo, text="Play", width=20, ).pack(side=LEFT)
        Button(subINfo, text="Save Link", width=20, ).pack(side=LEFT, padx=5 )
        Button(subINfo, text="Copy Link", width=20, ).pack(side=LEFT)
        Label(subINfo, text=duration).pack(anchor="w",padx=5)
        subINfo.pack(fill=X,pady=10,padx=10)
















