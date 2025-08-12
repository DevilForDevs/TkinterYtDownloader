
import os
import threading
import tkinter as tk
from tkinter.constants import X, BOTH
from typing import Optional
import urllib.request
from utils.ToolBox import send_youtube_search_request
from widgets.commanWidgets.ScrollableFrame import ScrollableFrame
from widgets.commanWidgets.SearchItem import SearchItem
from widgets.commanWidgets.SyncedProgressBar import SyncedProgressBar
from widgets.homeWidgets.SearchBar import SearchFrame


class HomeFrame(tk.Frame):
    scrollFrame: Optional[ScrollableFrame] = None
    query = ""
    busy = False  # <-- New flag

    def __init__(self, master=None, continuationvar: Optional[tk.StringVar] = None,
                 collectedVideos: Optional[list] = None,formatSelect=None, **kwargs):
        super().__init__(master, **kwargs)
        self.formatSelect=formatSelect

        self.continuationvar = continuationvar or tk.StringVar(master=self, value="")
        self.collectedVideos = collectedVideos if collectedVideos is not None else []

        SearchFrame(self, on_search=self.print_search_query).pack(fill=X, pady=5)

        self.progressFrame = tk.Frame(self, pady=5)
        self.progressFrame.pack(fill=X)
        self.resultsFor = tk.Label(self.progressFrame, anchor="w")
        self.progress_var = tk.IntVar()
        self.progressBar = SyncedProgressBar(self.progressFrame, progress_var=self.progress_var)

        self.scrollFrame = ScrollableFrame(self, on_scroll_end=self.reachedBottom)
        self.scrollFrame.pack(fill=BOTH, expand=True)

        if collectedVideos:
            self.render_existing_videos()

    def showProgres(self):
        self.progressBar.pack(fill=X)
        self.progress_var.set(50)


    def hideProgress(self):
        self.progressBar.pack_forget()

    def reachedBottom(self):
        if self.collectedVideos and not self.busy:  # Prevent if already loading
            self.print_search_query(self.query)



    def render_existing_videos(self):
        dir_path = "thumbnail"
        os.makedirs(dir_path, exist_ok=True)

        for vid in self.collectedVideos:
            videoId = vid["videoId"]
            thumb_path = f"{dir_path}/{videoId}.jpg"

            if not os.path.exists(thumb_path):
                urllib.request.urlretrieve(
                    f"https://img.youtube.com/vi/{videoId}/hqdefault.jpg",
                    thumb_path
                )

            SearchItem(
                self.scrollFrame.scrollable_frame,
                bd=2, relief="groove",
                vid=videoId, title=vid["title"], duration=vid["duration"],showProgress=self.showProgres,hideProgreess=self.hideProgress,
                formatSelect=self.formatSelect
            ).pack(fill=X, pady=5)

    def print_search_query(self, query):
        if self.busy:  # If a request is already running, skip
            print("Request skipped — already busy")
            return

        self.busy = True
        self.query = query
        self.showProgres()
        os.makedirs("thumbnail", exist_ok=True)

        def task():
            try:
                if "http" in query:
                    print("for downloadad")
                else:
                    results = send_youtube_search_request(
                        query, self.continuationvar.get(), "EgIQAQ%3D%3D"
                    )
                    self.continuationvar.set(results["continuation"])

                    self.hideProgress()
                    self.resultsFor.pack(fill=X)
                    self.resultsFor.configure(text=query)

                    videos = results["videos"]
                    for v in videos:
                        if v["videoId"] not in [x["videoId"] for x in self.collectedVideos]:
                            vid = v["videoId"]
                            self.collectedVideos.append(v)
                            urllib.request.urlretrieve(
                                f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
                                f"thumbnail/{vid}.jpg"
                            )
                            SearchItem(
                                self.scrollFrame.scrollable_frame,
                                bd=2, relief="groove",
                                vid=vid, title=v["title"], duration=v["duration"], showProgress=self.showProgres,
                                hideProgreess=self.hideProgress,
                                formatSelect=self.formatSelect
                            ).pack(fill=X, pady=5)
            finally:
                self.busy = False  # Release lock

        threading.Thread(target=task).start()






