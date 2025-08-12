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
from utils.ToolBox import convert_bytes
from utils.muxer import DashedWritter
from utils.muxer.DashedParser import DashedParser
from widgets.DownloadsFrame import DownloadsFrame
from widgets.HomeFrame import HomeFrame
from widgets.PlayerFrame import PlayerFrame
from widgets.SidebarFrame import SidebarFrame


class DownloaderApp(tk.Tk):
    download_models_list = []

    def __init__(self):
        super().__init__()

        self.title("Downloader App")

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
            formatSelect=self.format_selected
        )
        self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

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
                formatSelect=self.format_selected
            )
            self.CurrentBodyFrame.pack(side=RIGHT, anchor="n", fill=BOTH, expand=True)

        def on_downloads():
            if self.CurrentBodyFrame is not None:
                if isinstance(self.CurrentBodyFrame, PlayerFrame):
                    self.CurrentBodyFrame.playPause()
                self.CurrentBodyFrame.pack_forget()
            self.CurrentBodyFrame = DownloadsFrame(self.BodyContainer,runningDownloads=self.download_models_list)
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

if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()


