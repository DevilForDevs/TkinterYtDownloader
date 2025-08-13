import os
import subprocess
import sys
import tkinter
import tkinter as tk
from tkinter import Label, Button
from tkinter.constants import X, RIGHT, LEFT

from PIL import Image, ImageTk

from widgets.commanWidgets.SyncedProgressBar import SyncedProgressBar


class DownloadListItem(tk.Frame):
    def __init__(self, master=None,item=None,playFunction=None, **kwargs):
        super().__init__(master, **kwargs)
        dir_path = "thumbnail"
        self.downloadItem=item
        self.playFunction=playFunction
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
        Button(subINfo, text="Pause", width=20,command=self.pause ).pack(side=LEFT,padx=5)
        Button(subINfo, text="Play", width=20,command=self.play ).pack(side=LEFT)
        Button(subINfo, text="Open In Explorer", width=20, command=self.openInExplorer).pack(side=LEFT, padx=5 )
        Label(subINfo, text="4:30").pack(anchor="w",padx=5)
        subINfo.pack(fill=X,pady=10,padx=10)

    def openInExplorer(self):
        if "Finished" in self.downloadItem.progress_var.get():
            # Get Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(downloads_folder, self.downloadItem.fileName)

            # Ensure file exists
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return

            # Open folder and highlight file depending on OS
            if sys.platform.startswith("win"):  # Windows
                subprocess.run(f'explorer /select,"{file_path}"')
            elif sys.platform.startswith("darwin"):  # macOS
                subprocess.run(["open", "-R", file_path])
            else:  # Linux (file manager might vary)
                subprocess.run(["xdg-open", downloads_folder])
    def play(self):
        if "Finished" in self.downloadItem.progress_var.get():
            # Get Downloads folder path
            downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
            file_path = os.path.join(downloads_folder, self.downloadItem.fileName)

            # Ensure file exists
            if not os.path.exists(file_path):
                print(f"File not found: {file_path}")
                return
            self.playFunction(file_path)




    def pause(self):
        self.downloadItem.continue_flag.clear()