
import os
import threading
import tkinter as tk
from tkinter.constants import X, BOTH
from typing import Optional
import urllib.request
from utils.ToolBox import send_youtube_search_request, getStreamingData, extract_video_id
from widgets.commanWidgets.ScrollableFrame import ScrollableFrame
from widgets.commanWidgets.SearchItem import SearchItem
from widgets.commanWidgets.SyncedProgressBar import SyncedProgressBar
from widgets.homeWidgets.SearchBar import SearchFrame
from PIL import Image, ImageTk

class HomeFrame(tk.Frame):
    scrollFrame: Optional[ScrollableFrame] = None
    query = ""
    busy = False  # <-- New flag

    def __init__(self, master=None, continuationvar: Optional[tk.StringVar] = None,
                 collectedVideos: Optional[list] = None,formatSelect=None, **kwargs):
        super().__init__(master, **kwargs)
        self.sortFormats=formatSelect

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
        self.progressBar.pack(fill=X,padx=10)
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
                vid=videoId, title=vid["title"], duration=vid["duration"],formatSelect=self.askResolution
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
                    self.directDownload(query)
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
                                vid=vid, title=v["title"], duration=v["duration"],formatSelect=self.askResolution
                            ).pack(fill=X, pady=5)
            except Exception as e:
                self.busy=False
                self.hideProgress()
            finally:
                self.busy = False  # Release lock

        threading.Thread(target=task).start()

    def directDownload(self, query):
        def chooseContainer():
            try:
                videoId = extract_video_id(query)

                os.makedirs("thumbnail", exist_ok=True)
                thumb_path = f"thumbnail/{videoId}.jpg"
                urllib.request.urlretrieve(
                    f"https://img.youtube.com/vi/{videoId}/hqdefault.jpg",
                    thumb_path
                )
                self.hideProgress()

                dlg = tk.Toplevel(self)
                dlg.title("Direct Download")

                container = tk.Frame(dlg)
                container.pack(padx=10, pady=10)

                # LEFT: Image
                img = Image.open(thumb_path).resize((200, 200), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(container, image=photo, width=200, height=200)
                img_label.image = photo
                img_label.pack(side="left", padx=5, pady=5)

                # RIGHT: Buttons
                btn_frame = tk.Frame(container)
                btn_frame.pack(side="right", padx=5, pady=5, fill="y")

                def download_and_close(fmt):
                    self.askResolution(videoId, fmt)
                    dlg.destroy()  # close the dialog

                tk.Button(btn_frame, text="Download MP4", width=20,
                          command=lambda: download_and_close("video/mp4")).pack(pady=5)
                tk.Button(btn_frame, text="Download WebM", width=20,
                          command=lambda: download_and_close("video/webm")).pack(pady=5)
                tk.Button(btn_frame, text="Download MP3", width=20,
                          command=lambda: download_and_close("audio/mp4")).pack(pady=5)

            except Exception as e:
                print(e)
                self.hideProgress()

        threading.Thread(target=chooseContainer).start()

    def askResolution(self,videoId,containerType):
        self.showProgres()
        def getStreamingDataM():
            rawResponse=getStreamingData(videoId)
            if rawResponse.ok:
                self.hideProgress()
                responseJosn = rawResponse.json()
                self.sortFormats(responseJosn, containerType)
                return
            else:
                print(rawResponse.status_code)

        threading.Thread(target=getStreamingDataM).start()




