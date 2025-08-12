import tkinter as tk

class ScrollableFrame(tk.Frame):
    def __init__(self, parent, on_scroll_end=None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)

        self.on_scroll_end = on_scroll_end  # Store callback

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self._on_scroll)
        self.scrollable_frame = tk.Frame(self.canvas)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollable_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.scrollable_frame.grid_columnconfigure(0, weight=1)

        self.scrollable_frame.bind("<Enter>", self._bind_mousewheel)
        self.scrollable_frame.bind("<Leave>", self._unbind_mousewheel)

    def _on_scroll(self, *args):
        """Handles scroll from scrollbar or mousewheel."""
        self.canvas.yview(*args)
        self._check_scroll_end()

    def _check_scroll_end(self):
        """Check if the user scrolled to the end."""
        first, last = self.canvas.yview()
        if last >= 1.0:  # Fully at the bottom
            if callable(self.on_scroll_end):
                self.on_scroll_end()

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._check_scroll_end()  # In case content shrinks or grows

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)   # Windows
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)     # Linux scroll up
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)     # Linux scroll down

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if event.num == 4:  # Linux scroll up
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:  # Linux scroll down
            self.canvas.yview_scroll(1, "units")
        else:  # Windows / MacOS
            self.canvas.yview_scroll(-int(event.delta / 120), "units")
        self._check_scroll_end()



