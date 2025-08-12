import tkinter as tk
from tkinter import Label, Button
from tkinter.constants import X, BOTTOM


class SidebarFrame(tk.Frame):
    def __init__(self, master=None, home_cmd=None, downloads_cmd=None,
                 player_cmd=None, linksfile_cmd=None, **kwargs):
        super().__init__(master, **kwargs)  # kwargs allow bg, width, etc.

        Label(self, text="Downloader").pack()

        Button(self, text="Home", command=home_cmd).pack(fill=X, pady=10)
        Button(self, text="Downloads", command=downloads_cmd).pack(fill=X, pady=10)
        Button(self, text="Player", command=player_cmd).pack(fill=X, pady=10)
        Button(self, text="Links File", command=linksfile_cmd).pack(fill=X, pady=10)

        Label(self, text="v1.0.0").pack(side=BOTTOM, pady=10)





