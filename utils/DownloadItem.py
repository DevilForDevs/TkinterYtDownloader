import threading
import tkinter as tk

class DownloadItem:
    def __init__(self, master):
        self.continue_flag = threading.Event()
        self.continue_flag.set()  # allow download by default
        self.progress_var = tk.StringVar(master, value="Progress: 0%")
        self.progress_percent = tk.IntVar()  # for tracking raw percent
        self.itag=0
        self.inRam=0
        self.onDisk=0
        self.onWeb=0
        self.fileName=""
        self.mimeType=""
        self.videoId=""
        self.videoUrl=""
        self.audioUrl=""
        self.suffix=""
        self.audioTs=""
        self.isAudio=False

