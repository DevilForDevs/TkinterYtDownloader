import os
import tkinter
import tkinter as tk
from tkinter import Label, Button
from tkinter.constants import X, RIGHT, LEFT

from PIL import Image, ImageTk

from widgets.commanWidgets.SyncedProgressBar import SyncedProgressBar


class DownloadListItem(tk.Frame):
    def __init__(self, master=None,item=None, **kwargs):
        super().__init__(master, **kwargs)
        dir_path = "thumbnail"
        os.makedirs(dir_path, exist_ok=True)
        thumbnail_img = Image.open(f"{dir_path}/{item.videoId}.jpg")  # Use your actual image path
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
        Label(info,text=item.fileName,anchor="w").pack(fill=X,pady=5)
        SyncedProgressBar(info,item.progress_percent).pack(fill=X,pady=5)
        info.pack(fill=X,padx=10)
        Label(info,textvariable=item.progress_var,anchor="w").pack(fill=X)

        subINfo=tk.Frame(self)
        Button(subINfo, text="Play", width=20, ).pack(side=LEFT)
        Button(subINfo, text="Open In Explorer", width=20, ).pack(side=LEFT, padx=5 )
        Label(subINfo, text="4:30").pack(anchor="w",padx=5)
        subINfo.pack(fill=X,pady=10,padx=10)
