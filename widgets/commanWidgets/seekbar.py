import tkinter as tk

class CircleSeekbar(tk.Canvas):
    def __init__(self, parent, width=300, height=30, max_value=100, command=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg="white", highlightthickness=0, **kwargs)
        self.max_value = max_value
        self.value = 0
        self.command = command  # <-- Custom callback, store it here

        self.thumb_radius = 8
        self.track_height = 4
        self.track_color = "#ccc"
        self.thumb_color = "#007aff"

        self.bind("<Button-1>", self.on_click)
        self.bind("<B1-Motion>", self.on_drag)
        self.bind("<Configure>", lambda e: self.redraw())

    def redraw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        center_y = h // 2

        self.create_line(
            self.thumb_radius, center_y,
            w - self.thumb_radius, center_y,
            fill=self.track_color, width=self.track_height
        )

        x = self.thumb_radius + (w - 2 * self.thumb_radius) * (self.value / self.max_value)

        self.create_oval(
            x - self.thumb_radius, center_y - self.thumb_radius,
            x + self.thumb_radius, center_y + self.thumb_radius,
            fill=self.thumb_color, outline=""
        )

    def set_value(self, val):
        self.value = min(max(val, 0), self.max_value)
        self.redraw()

    def set_max(self, max_val):
        self.max_value = max_val
        self.set_value(self.value)  # re-render with new scale

    def on_click(self, event):
        self.update_value_from_event(event)

    def on_drag(self, event):
        self.update_value_from_event(event)

    def update_value_from_event(self, event):
        w = self.winfo_width()
        rel_x = min(max(event.x, self.thumb_radius), w - self.thumb_radius)
        self.value = (rel_x - self.thumb_radius) / (w - 2 * self.thumb_radius) * self.max_value
        self.redraw()

        # ✅ Call user-defined command
        if self.command:
            self.command(self.value)
