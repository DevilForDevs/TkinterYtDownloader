import tkinter as tk
from tkinter import X, Label, BOTH

from widgets.commanWidgets.DownloadListItem import DownloadListItem
from widgets.commanWidgets.ScrollableFrame import ScrollableFrame


class DownloadsFrame(tk.Frame):

    def __init__(self, master=None,runningDownloads=None,playFunction=None, **kwargs):
        super().__init__(master, **kwargs)
        Label(self,text="Downloads",anchor="w").pack(fill=X,padx=10,pady=10)
        self.scrollFrame = ScrollableFrame(self,bg="red")
        self.scrollFrame.pack(fill=BOTH, expand=True)
        for item in runningDownloads:
            DownloadListItem(self.scrollFrame.scrollable_frame,item=item,playFunction=playFunction).pack(fill=X,pady=5)









