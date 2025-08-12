import tkinter as tk
from tkinter import ttk

class SyncedProgressBar(ttk.Progressbar):
    def __init__(self, master, progress_var: tk.IntVar, length=200, **kwargs):
        super().__init__(master, length=length, mode='determinate', **kwargs)
        self.progress_var = progress_var
        self._poll()

    def _poll(self):
        # Sync the value of the progress bar with the IntVar
        self.config(value=self.progress_var.get())
        self.after(100, self._poll)




