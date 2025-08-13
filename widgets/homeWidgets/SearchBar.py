import tkinter
import tkinter as tk
from tkinter import Button
from tkinter.constants import X, RIGHT


class SearchFrame(tk.Frame):
    def __init__(self, master=None, on_search=None, **kwargs):
        super().__init__(master, **kwargs)
        self.on_search = on_search  # store the callback function

        Button(self, text="Go", command=self._handle_search).pack(side=RIGHT, padx=20)

        self.entry = tkinter.Entry(self)
        self.entry.pack(fill=X, pady=5)

        # Bind Enter key to trigger search
        self.entry.bind("<Return>", self._handle_search_event)

    def _handle_search_event(self, event):
        """Handle search triggered by Enter key."""
        self._handle_search()

    def _handle_search(self):
        """Internal handler for button click."""
        if self.on_search:  # if a callback is given
            text = self.entry.get()
            self.on_search(text)
