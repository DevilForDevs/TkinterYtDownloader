import os
import pathlib
import re
import subprocess
import threading
import tkinter
import tkinter as tk
from tkinter.constants import RIGHT, Y, BOTH

import requests

from utils.DownloadItem import DownloadItem
from utils.ToolBox import convert_bytes, txt2filename, getStreamingData
from utils.muxer import DashedWritter
from utils.muxer.DashedParser import DashedParser
from widgets.DownloadsFrame import DownloadsFrame
from widgets.HomeFrame import HomeFrame
from widgets.PlayerFrame import PlayerFrame
from widgets.SidebarFrame import SidebarFrame
import tkinter.font as tkfont

class DownloaderApp(tk.Tk):
    download_models_list = []

    def __init__(self):
        super().__init__()

        self.title("TinyDownloader")

        # Shared state
        self.continuationToken = tk.StringVar()
        self.collectedVideoIds = []



        # BodyContainer (right side)
        self.BodyContainer = tkinter.Frame(self)
        self.BodyContainer.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

        # Always pass shared state on creation
        self.CurrentBodyFrame = HomeFrame(
            self.BodyContainer,
            continuationvar=self.continuationToken,
            collectedVideos=self.collectedVideoIds,
            formatSelect=self.sortFormats
        )
        self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        def on_home():
            if self.CurrentBodyFrame is not None:
                # If current frame is PlayerFrame, toggle play (pause)
                if isinstance(self.CurrentBodyFrame, PlayerFrame):
                    self.CurrentBodyFrame.playPause()
                self.CurrentBodyFrame.pack_forget()
            self.CurrentBodyFrame = HomeFrame(
                self.BodyContainer,
                continuationvar=self.continuationToken,
                collectedVideos=self.collectedVideoIds,
                formatSelect=self.sortFormats
            )
            self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

        def on_downloads():
            if self.CurrentBodyFrame is not None:
                if isinstance(self.CurrentBodyFrame, PlayerFrame):
                    self.CurrentBodyFrame.playPause()
                self.CurrentBodyFrame.pack_forget()
            self.CurrentBodyFrame = DownloadsFrame(self.BodyContainer,runningDownloads=self.download_models_list,playFunction=self.playFunction)
            self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

        def on_playerFrame():
            if self.CurrentBodyFrame is not None:
                if isinstance(self.CurrentBodyFrame, PlayerFrame):
                    self.CurrentBodyFrame.playPause()
                self.CurrentBodyFrame.pack_forget()
            self.CurrentBodyFrame = PlayerFrame(self.BodyContainer)
            self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

        # LeftFrame (left sidebar)
        self.LeftFrame = SidebarFrame(
            self,
            home_cmd=on_home,
            downloads_cmd=on_downloads,
            player_cmd=on_playerFrame
        )
        self.LeftFrame.pack(pady=10, fill=Y, expand=Y, padx=10)

    def playFunction(self,filepath):
        if self.CurrentBodyFrame is not None:
            if isinstance(self.CurrentBodyFrame, PlayerFrame):
                self.CurrentBodyFrame.playPause()
            self.CurrentBodyFrame.pack_forget()
        self.CurrentBodyFrame = PlayerFrame(self.BodyContainer,filePath=filepath)
        self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)


    def format_selected(self, fmt1, fmt2,fileName,videoId,duration):
        item = DownloadItem(self)
        item.fileName=fileName
        item.videoId=videoId
        item.videoUrl = fmt1["url"]
        item.audioUrl = fmt2["url"]
        item.audioTs=int(fmt2["contentLength"])
        item.onWeb=int(fmt1["contentLength"])
        item.mimeType=fmt1["mimeType"]
        item.itag=fmt1["itag"]
        if fmt1==fmt2:
            item.isAudio=True
            item.fileName = f"{fileName}.mp3"
        else:
            item.fileName = f"{fileName}.mp4"
        self.download_models_list.append(item)
        self.downloader_function(item)


    def download_as_9mb(self,download_item, url: str, fos, total_bytes: int):

        chunk_size = 9437184  # 9 MB

        end_byte = min(download_item.onDisk + download_item.inRam + chunk_size, total_bytes)  # Range is inclusive

        headers = {
            "Range": f"bytes={download_item.onDisk + download_item.inRam}-{end_byte}"
        }

        response = requests.get(url, headers=headers, stream=True)

        if response.status_code in (200, 206):
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    fos.write(chunk)
                    download_item.inRam += len(chunk)
                    download_item.progress_percent.set(
                        (int(int(download_item.onDisk + download_item.inRam) / total_bytes * 100)))
                    download_item.progress_var.set(
                        f"Progress   {convert_bytes(download_item.inRam + download_item.onDisk)}/{convert_bytes(total_bytes)}    {download_item.progress_percent.get()}%   {download_item.suffix}")
                    print(f"{convert_bytes(download_item.inRam + download_item.onDisk)}/{convert_bytes(total_bytes)}    {download_item.progress_percent.get()}%   {download_item.suffix}")
                    if download_item.continue_flag is False:
                        return

        if download_item.onDisk + download_item.inRam == total_bytes:
            return True
        else:
            self.download_as_9mb(download_item, url, fos, total_bytes)

    def downloader_function(self,downloadItem):
        def file_downloader():
            mid = downloadItem.videoId
            if downloadItem.isAudio:
                print("audio")
            else:
                dir_path = "tempFiles"
                os.makedirs(dir_path, exist_ok=True)
                audio_file = f"{dir_path}/{mid}({downloadItem.itag}).mp3"
                video_file = f"{dir_path}/{mid}({downloadItem.itag}).mp4"
                downloadItem.suffix = "Downloading Video"
                if os.path.exists(video_file):
                    videoFileObject = open(video_file, "ab")
                    downloadItem.onDisk = os.path.getsize(video_file)
                    self.download_as_9mb(downloadItem, downloadItem.videoUrl, videoFileObject, downloadItem.onWeb)
                    videoFileObject.close()
                else:
                    videoFileObject = open(video_file, "wb")
                    self.download_as_9mb(downloadItem, downloadItem.videoUrl, videoFileObject, downloadItem.onWeb)
                    videoFileObject.close()
                downloadItem.onDisk = 0
                downloadItem.inRam = 0
                downloadItem.suffix = "Downloading Audio"
                downloadItem.progress_percent.set(0)
                if os.path.exists(audio_file):
                    audioFileObject = open(audio_file, "ab")
                    downloadItem.onDisk = os.path.getsize(audio_file)
                    self.download_as_9mb(downloadItem, downloadItem.audioUrl, audioFileObject, downloadItem.audioTs)
                    audioFileObject.close()
                else:
                    audioFileObject = open(audio_file, "wb")
                    self.download_as_9mb(downloadItem, downloadItem.audioUrl, audioFileObject, downloadItem.audioTs)
                    audioFileObject.close()
                downloads_folder = os.path.join(os.environ['USERPROFILE'], 'Downloads')
                file_path_final = os.path.join(downloads_folder, downloadItem.fileName)

                print("muxing")
                merged = self.merge_video_audio(downloadItem, audio_file, video_file, file_path_final)
                if merged:
                    final_size = os.path.getsize(file_path_final)
                    downloadItem.progress_var.set(f"Finished Download  {convert_bytes(final_size)}")

        threading.Thread(target=file_downloader).start()

    def merge_video_audio(self,downloadItem, audio: str, video: str, final: str) -> bool:

        if "webm" in downloadItem.videoUrl:
            cmd = [
                "ffmpeg",
                "-i", video,
                "-i", audio,
                "-c:v", "copy",
                "-y",
                "-map", "0:v:0",
                "-map", "1:a:0",
                final
            ]

            process = subprocess.Popen(
                cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8"
            )

            progress_regex = re.compile(r"time=([\d:.]+)")
            duration_regex = re.compile(r"Duration: ([\d:.]+),")

            total_duration = None
            while True:
                line = process.stderr.readline()
                if not line:
                    break

                # Get total duration
                if total_duration is None:
                    duration_match = duration_regex.search(line)
                    if duration_match:
                        total_duration = duration_match.group(1)

                # Get progress
                progress_match = progress_regex.search(line)
                if progress_match:
                    progress = progress_match.group(1)
                    if total_duration:
                        downloadItem.progress_var.set(f"Merging:  {progress}/{total_duration}")

            # Wait for the process to ensure ffmpeg has released the files
            success = process.wait() == 0
            return success
        else:
            audio = DashedParser(audio)
            audio.parse()
            video = DashedParser(video)
            video.parse()

            def muxingProgress(muxpg):
                downloadItem.progress_var.set(muxpg)

            writer = DashedWritter.DashedWriter(pathlib.Path(final), [audio, video], muxingProgress)
            writer.build_non_fmp4()
            return True

    def build_dialog(self, formats, on_select_itag, type):
        dlg = tk.Toplevel(self)
        dlg.title("Select Video Format")

        width, height = 500, 300
        dlg.geometry(f"{width}x{height}")

        dlg.update_idletasks()
        screen_width = dlg.winfo_screenwidth()
        screen_height = dlg.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        dlg.geometry(f"{width}x{height}+{x}+{y}")

        tk.Label(dlg, text="Available formats:").pack(pady=5)

        list_font = tkfont.Font(family="Helvetica", size=10)

        sb = tk.Scrollbar(dlg)
        sb.pack(side="right", fill="y")

        lb = tk.Listbox(dlg, yscrollcommand=sb.set, font=list_font)
        lb.pack(side="top", fill="both", expand=True, padx=5, pady=5)
        sb.config(command=lb.yview)

        # Dict to store format details and itags
        itag_map = {}
        display_map = {}

        for fmt in formats:
            mime = fmt["mimeType"]
            if type in mime:
                if "audio" in mime:
                    display = f'Audio {convert_bytes(fmt["bitrate"])}/s   {convert_bytes(int(fmt["contentLength"]))}'
                else:
                    if "webm" in mime:
                        display = f'{fmt["qualityLabel"]}   {convert_bytes(int(fmt["contentLength"]))}   {mime}'
                    else:
                        display = f'{fmt["qualityLabel"]}   {convert_bytes(int(fmt["contentLength"]))}   {mime} 👍'
                index = lb.size()
                lb.insert(tk.END, display)
                itag_map[index] = fmt["itag"]
                display_map[index] = display  # Save for button text

        # Button text will change dynamically
        download_btn = tk.Button(dlg, text="Download Selected Format", state="disabled", command=lambda: on_select())
        download_btn.pack(pady=10)

        def on_listbox_select(event):
            sel = lb.curselection()
            if sel:
                index = sel[0]
                # Enable and update button text
                download_btn.config(text=f"Download: {display_map[index]}", state="normal")

        def on_select():
            sel = lb.curselection()
            if sel:
                index = sel[0]
                selected_itag = itag_map.get(index)
                if selected_itag is not None:
                    on_select_itag(selected_itag)
                dlg.destroy()

        # Bind selection change
        lb.bind("<<ListboxSelect>>", on_listbox_select)

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
                        self.format_selected(selected_fmt, selected_fmt,videoTitle,videoId,"4:30")
                        return

                    # If it's video → decide container type
                    if "webm" in selected_fmt["mimeType"]:
                        containerType = "webm"

                    # Find matching audio track
                    audio_itag = 140 if containerType == "mp4" else 251
                    audio_fmt = next((f for f in collectedFmts if f["itag"] == audio_itag), None)

                    if audio_fmt:
                        self.format_selected(selected_fmt, audio_fmt,videoTitle,videoId,"4:30")
                    else:
                        print(f"No matching audio format found for {containerType}")

                self.build_dialog(playerResponse["streamingData"]["adaptiveFormats"], download_selected_format, type)
            else:
                print("formts not found")
        else:
            print("playerResponseNotFound")

    def on_close(self):
        for item in self.download_models_list:
            item.continue_flag.clear()
        self.destroy()  # actually close the window



if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()


