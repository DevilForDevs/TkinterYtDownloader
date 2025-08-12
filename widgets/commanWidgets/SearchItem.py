import os
import threading
import tkinter
import tkinter as tk
from tkinter import Label, Button
from tkinter.constants import X, RIGHT, LEFT

from PIL import Image, ImageTk
import tkinter.font as tkfont
from utils.ToolBox import getStreamingData, convert_bytes, txt2filename


# https://www.youtube.com/watch?v=Mc_bgEn7FkA
class SearchItem(tk.Frame):

    def __init__(self, master=None,vid=None,title=None,duration=None,showProgress=None,hideProgreess=None,formatSelect=None, **kwargs):
        super().__init__(master, **kwargs)
        dir_path = "thumbnail"
        self.showProgress=showProgress
        self.hideProgress=hideProgreess
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
        Button(info, text="Download Mp4",command=lambda :self.askResolution(vid,"video/mp4"), width=20, ).pack(side=LEFT,)
        Button(info, text="Download Webm",command=lambda :self.askResolution(vid,"video/webm"), width=20,).pack(side=LEFT,padx=5)
        Button(info, text="Download Mp3",command=lambda :self.askResolution(vid,"audio/mp4"), width=20).pack(side=LEFT)
        info.pack(fill=X,padx=10)

        subINfo=tk.Frame(self)
        Button(subINfo, text="Play", width=20, ).pack(side=LEFT)
        Button(subINfo, text="Save Link", width=20, ).pack(side=LEFT, padx=5 )
        Button(subINfo, text="Copy Link", width=20, ).pack(side=LEFT)
        Label(subINfo, text=duration).pack(anchor="w",padx=5)
        subINfo.pack(fill=X,pady=10,padx=10)

    def build_dialog(self,formats, on_select_itag,type):
        dlg = tk.Toplevel(self)
        dlg.title("Select Video Format")

        # Set initial size
        width, height = 500, 300
        dlg.geometry(f"{width}x{height}")

        # Center the dialog
        dlg.update_idletasks()
        screen_width = dlg.winfo_screenwidth()
        screen_height = dlg.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        dlg.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(dlg, text="Available formats:").pack(pady=5)

        # Font
        list_font = tkfont.Font(family="Helvetica", size=10)

        sb = tk.Scrollbar(dlg)
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(dlg, yscrollcommand=sb.set, font=list_font)
        lb.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        sb.config(command=lb.yview)

        # Dict to map Listbox index to itag
        itag_map = {}

        for fmt in formats:
            mime = fmt["mimeType"]
            if type in mime:
                if "audio" in mime:
                    display = f'Audio {convert_bytes(fmt["bitrate"])}/s   {convert_bytes(int(fmt["contentLength"]))}'
                    index = lb.size()
                    lb.insert(tkinter.END, display)
                    itag_map[index] = fmt["itag"]
                else:
                    if "webm" in mime:
                        display = f'{fmt["qualityLabel"]}   {convert_bytes(int(fmt["contentLength"]))}   {mime}'
                        index = lb.size()
                        lb.insert(tkinter.END, display)
                        itag_map[index] = fmt["itag"]
                    else:
                        display = f'{fmt["qualityLabel"]}   {convert_bytes(int(fmt["contentLength"]))}   {mime} 👍'
                        index = lb.size()
                        lb.insert(tkinter.END, display)
                        itag_map[index] = fmt["itag"]


        def on_select():
            sel = lb.curselection()
            if sel:
                index = sel[0]
                selected_itag = itag_map.get(index)
                if selected_itag is not None:
                    on_select_itag(selected_itag)  # Call your callback with the itag
                dlg.destroy()

        tkinter.Button(dlg, text="Select", command=on_select).pack(pady=5)

    def sortFormats(self,responseJosn,type):
        if "playerResponse" in responseJosn:
            playerResponse = responseJosn["playerResponse"]
            videoTitle = txt2filename(playerResponse["videoDetails"]["title"])
            videoId = txt2filename(playerResponse["videoDetails"]["videoId"])
            if "streamingData" in playerResponse:
                def download_selected_format(fmt):
                    print("sorting formats")
                    containerType = "mp4"
                    collectedFmts = playerResponse["streamingData"]["adaptiveFormats"]

                    found = False
                    selected_fmt = None

                    # Find the selected format
                    for fmt_ in collectedFmts:
                        if fmt_["itag"] == int(fmt):
                            found = True
                            selected_fmt = fmt_
                            break  # found our main format

                    if not found:
                        print("no formats found")
                        return

                    # If it's audio only
                    if "audio" in selected_fmt["mimeType"]:
                        self.formatSelected(selected_fmt,selected_fmt)
                        return

                    # If it's video → decide container type
                    if "webm" in selected_fmt["mimeType"]:
                        containerType = "webm"

                    # Find matching audio track
                    audio_itag = 140 if containerType == "mp4" else 251
                    audio_fmt = next((f for f in collectedFmts if f["itag"] == audio_itag), None)

                    if audio_fmt:
                        self.formatSelected(selected_fmt, audio_fmt,videoTitle,videoId,"4:30")
                    else:
                        print(f"No matching audio format found for {containerType}")

                self.build_dialog(playerResponse["streamingData"]["adaptiveFormats"], download_selected_format, type)
            else:
                print("formts not found")
        else:
            print("playerResponseNotFound")



    def askResolution(self,videoId,type):
        self.showProgress()
        def getStreamingDataM():
            rawResponse=getStreamingData(videoId)
            if rawResponse.ok:
                self.hideProgress()
                responseJosn = rawResponse.json()
                self.sortFormats(responseJosn,type)
                return
            else:
                print(rawResponse.status_code)

        threading.Thread(target=getStreamingDataM).start()










