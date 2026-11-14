import random
import tkinter as tk

from .logic import (
    CORRIDOR_HALF_WIDTH,
    FINISH,
    GOAL_RADIUS,
    MARKER_RADIUS,
    POINTS,
    START,
    MazeRun,
    corridor_rectangles,
)


COLORS = {
    "Red": "#e53935",
    "Blue": "#1e88e5",
    "Green": "#43a047",
    "Purple": "#8e24aa",
    "Orange": "#fb8c00",
}

WORLD_WIDTH = 800
WORLD_HEIGHT = 610
SPACE_BG = "#0b0d2a"
NEBULA = ("#14123f", "#1b1650", "#241a5e")
PATH_GLOW = "#3a3f9e"
PATH_EDGE = "#7c83ff"
PATH_FILL = "#1d2260"
STAR_COUNT = 140


class MazeGame(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent)
        self.root = parent
        self.on_back = on_back
        self.color = tk.StringVar(value="Blue")
        self.difficulty = tk.StringVar(value="easy")
        self.message = tk.StringVar()
        self.run = MazeRun()
        self.dragging = False
        self.fullscreen = False
        self.scale = 1.0
        self.offset = (0.0, 0.0)
        self.trace = []
        rng = random.Random(7)
        self.stars = [
            (rng.random(), rng.random(), rng.choice((1, 1, 2, 3)),
             rng.choice(("#ffffff", "#cfd8ff", "#fff3b0")))
            for _ in range(STAR_COUNT)
        ]
        self.planets = [
            (0.88, 0.14, 38, "#ff8a65", "#bf5b3e"),
            (0.10, 0.88, 26, "#4dd0e1", "#2a8a96"),
        ]

        controls = tk.Frame(self)
        controls.pack(fill="x", pady=(0, 8))
        tk.Button(controls, text="← Menu", command=on_back).pack(side="left")
        tk.Label(controls, text="Marker color:").pack(side="left", padx=(15, 3))
        tk.OptionMenu(controls, self.color, *COLORS).pack(side="left")
        tk.Label(controls, text="Difficulty:").pack(side="left", padx=(15, 3))
        tk.Radiobutton(
            controls, text="Easy", variable=self.difficulty, value="easy",
            command=self.restart,
        ).pack(side="left")
        tk.Radiobutton(
            controls, text="Hard", variable=self.difficulty, value="hard",
            command=self.restart,
        ).pack(side="left")
        tk.Button(controls, text="Restart", command=self.restart).pack(
            side="right"
        )
        tk.Button(
            controls, text="⛶ Full screen (F11)", command=self.toggle_fullscreen
        ).pack(side="right", padx=(0, 8))

        self.canvas = tk.Canvas(
            self, width=WORLD_WIDTH, height=WORLD_HEIGHT, bg=SPACE_BG,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        tk.Label(self, textvariable=self.message, font=("Arial", 12)).pack(
            pady=(8, 0)
        )
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        self.canvas.bind("<Configure>", lambda event: self.redraw())
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.restart()

    def destroy(self):
        self.root.unbind("<F11>")
        self.root.unbind("<Escape>")
        self.set_fullscreen(False)
        super().destroy()

    def toggle_fullscreen(self, event=None):
        self.set_fullscreen(not self.fullscreen)

    def exit_fullscreen(self, event=None):
        self.set_fullscreen(False)

    def set_fullscreen(self, enabled):
        if enabled == self.fullscreen:
            return
        self.fullscreen = enabled
        if enabled:
            self.root.resizable(True, True)
            self.root.attributes("-fullscreen", True)
            self.pack_configure(padx=0, pady=0)
        else:
            self.root.attributes("-fullscreen", False)
            self.root.resizable(False, False)
            self.pack_configure(padx=12, pady=12)
            self.canvas.configure(width=WORLD_WIDTH, height=WORLD_HEIGHT)
            self.root.geometry("")

    def to_screen(self, point):
        return (
            self.offset[0] + point[0] * self.scale,
            self.offset[1] + point[1] * self.scale,
        )

    def to_world(self, x, y):
        return (
            (x - self.offset[0]) / self.scale,
            (y - self.offset[1]) / self.scale,
        )

    def update_transform(self):
        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), 1)
        self.scale = min(width / WORLD_WIDTH, height / WORLD_HEIGHT)
        self.offset = (
            (width - WORLD_WIDTH * self.scale) / 2,
            (height - WORLD_HEIGHT * self.scale) / 2,
        )
        return width, height

    def restart(self):
        self.run = MazeRun(hard=self.difficulty.get() == "hard")
        self.dragging = False
        self.trace = []
        self.redraw()
        self.message.set("Click the marker at the start and guide it to the goal.")

    def draw_background(self, width, height):
        for index, color in enumerate(NEBULA):
            cx = width * (0.25 + 0.3 * index)
            cy = height * (0.3 + 0.25 * (index % 2))
            radius = min(width, height) * (0.55 - 0.1 * index)
            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=color, outline="",
            )
        for fx, fy, size, color in self.stars:
            x, y = fx * width, fy * height
            self.canvas.create_oval(
                x - size / 2, y - size / 2, x + size / 2, y + size / 2,
                fill=color, outline="",
            )
        unit = min(width, height) / WORLD_HEIGHT
        for fx, fy, radius, light, dark in self.planets:
            cx, cy, r = fx * width, fy * height, radius * unit
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r, fill=dark, outline=""
            )
            self.canvas.create_oval(
                cx - r, cy - r, cx + r * 0.7, cy + r * 0.7,
                fill=light, outline="",
            )
        ring_r = self.planets[0][2] * unit
        cx, cy = self.planets[0][0] * width, self.planets[0][1] * height
        self.canvas.create_oval(
            cx - ring_r * 1.6, cy - ring_r * 0.35,
            cx + ring_r * 1.6, cy + ring_r * 0.35,
            outline="#ffd9c7", width=max(1, 2 * unit),
        )

    def draw_path(self):
        for grow, color in ((8, PATH_GLOW), (3, PATH_EDGE), (0, PATH_FILL)):
            for left, top, right, bottom in corridor_rectangles():
                x1, y1 = self.to_screen((left - grow, top - grow))
                x2, y2 = self.to_screen((right + grow, bottom + grow))
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline=color
                )
        guide = [c for point in POINTS for c in self.to_screen(point)]
        self.canvas.create_line(
            *guide, fill="#4a52c4", width=max(1, 2 * self.scale),
            dash=(6, 8), capstyle="round", joinstyle="round",
        )

    def draw_start_and_goal(self):
        s = self.scale
        x, y = self.to_screen(START)
        for radius, color in ((30, "#1b5e20"), (25, "#66bb6a")):
            self.canvas.create_oval(
                x - radius * s, y - radius * s, x + radius * s, y + radius * s,
                fill=color, outline="",
            )
        self.canvas.create_text(
            x, y, text="START", fill="#06260a",
            font=("Arial", max(7, int(10 * s)), "bold"),
        )
        fx, fy = self.to_screen(FINISH)
        for radius, color in ((GOAL_RADIUS + 12, "#7a4a00"), (GOAL_RADIUS + 5, "#ffb300")):
            self.canvas.create_oval(
                fx - radius * s, fy - radius * s, fx + radius * s, fy + radius * s,
                fill=color, outline="",
            )
        self.canvas.create_text(
            fx, fy, text="★", fill="#fff8e1",
            font=("Arial", max(10, int(26 * s)), "bold"),
        )
        gx, gy = self.to_screen((FINISH[0], FINISH[1] - CORRIDOR_HALF_WIDTH - 10))
        self.canvas.create_text(
            gx, gy, text="GOAL", fill="#ffe082",
            font=("Arial", max(8, int(11 * s)), "bold"),
        )

    def redraw(self):
        width, height = self.update_transform()
        self.canvas.delete("all")
        self.draw_background(width, height)
        self.draw_path()
        self.draw_start_and_goal()
        for previous, current in self.trace:
            self.draw_trace(previous, current)
        self.show_marker()

    def draw_trace(self, previous, current):
        self.canvas.create_line(
            *self.to_screen(previous), *self.to_screen(current),
            fill=COLORS[self.color.get()],
            width=MARKER_RADIUS * 2 * self.scale, capstyle="round",
            tags="trace",
        )

    def show_marker(self):
        self.canvas.delete("marker")
        x, y = self.to_screen(self.run.position)
        r = MARKER_RADIUS * self.scale
        self.canvas.create_oval(
            x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r,
            outline="#ffffff", tags="marker",
        )
        self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=COLORS[self.color.get()], outline="#ffffff", tags="marker",
        )

    def start_drawing(self, event):
        if self.run.can_resume(self.to_world(event.x, event.y)):
            self.dragging = True
            self.move_to(event.x, event.y)

    def draw(self, event):
        if self.dragging:
            self.move_to(event.x, event.y)

    def stop_drawing(self, event):
        if self.dragging:
            self.move_to(event.x, event.y)
        self.dragging = False

    def move_to(self, x, y):
        previous = self.run.position
        result = self.run.move(self.to_world(x, y))
        if result == "reset":
            self.restart()
            self.message.set("Oops! The marker left the path. Try again!")
            return
        self.trace.append((previous, self.run.position))
        self.draw_trace(previous, self.run.position)
        self.show_marker()
        if result == "won":
            self.dragging = False
            self.message.set("Great job! You reached the goal!")
