import math
import random
import tkinter as tk

from .logic import (
    CORRIDOR_HALF_WIDTH,
    GOAL_RADIUS,
    POINTS,
    MazeRun,
    corridor_rectangles,
    generate_points,
    segment_in_corridor,
)


from .themes import (
    COLORS,
    EXPLOSION_FRAMES,
    RAINBOW_COLORS,
    STAR_COUNT,
    THEMES,
    TRAILS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
    blend,
    spaceship_parts,
    unicorn_parts,
)


class MazeGame(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent)
        self.root = parent
        self.on_back = on_back
        self.color = tk.StringVar(value="Blue")
        self.theme_name = tk.StringVar(value="Space")
        self.heading = 0.0
        self.facing = 1
        self.exploding = False
        self.boom_job = None
        self.difficulty = tk.StringVar(value="easy")
        self.message = tk.StringVar()
        self.run = MazeRun()
        self.points = POINTS
        self.dragging = False
        self.fullscreen = False
        self.scale = 1.0
        self.offset = (0.0, 0.0)
        self.trace = []
        rng = random.Random(7)
        self.stars = [
            (rng.random(), rng.random(), rng.choice((1, 1, 2, 3)),
             rng.randrange(3))
            for _ in range(STAR_COUNT)
        ]

        controls = tk.Frame(self)
        controls.pack(fill="x", pady=(0, 8))
        tk.Button(controls, text="← Menu", command=on_back).pack(side="left")
        tk.Label(controls, text="Theme:").pack(side="left", padx=(15, 3))
        tk.OptionMenu(
            controls, self.theme_name, *THEMES, command=lambda _: self.redraw()
        ).pack(side="left")
        tk.Label(controls, text="Color:").pack(side="left", padx=(15, 3))
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
        tk.Button(
            controls, text="🎲 New maze", command=self.new_random_maze
        ).pack(side="right", padx=(0, 8))
        tk.Button(
            controls, text="Classic maze", command=self.classic_maze
        ).pack(side="right", padx=(0, 8))

        self.canvas = tk.Canvas(
            self, width=WORLD_WIDTH, height=WORLD_HEIGHT,
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

    @property
    def theme(self):
        return THEMES[self.theme_name.get()]

    def destroy(self):
        if self.boom_job is not None:
            self.after_cancel(self.boom_job)
            self.boom_job = None
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
        if self.boom_job is not None:
            self.after_cancel(self.boom_job)
            self.boom_job = None
        self.exploding = False
        self.run = MazeRun(
            hard=self.difficulty.get() == "hard", points=self.points
        )
        self.dragging = False
        self.trace = []
        first, second = self.points[0], self.points[1]
        self.heading = math.atan2(second[1] - first[1], second[0] - first[0])
        self.facing = 1 if second[0] >= first[0] else -1
        self.redraw()
        self.message.set("Click the start and guide your ride to the goal.")

    def new_random_maze(self):
        self.points = generate_points()
        self.restart()

    def classic_maze(self):
        self.points = POINTS
        self.restart()

    def draw_background(self, width, height):
        theme = self.theme
        for index, color in enumerate(theme["nebula"]):
            cx = width * (0.25 + 0.3 * index)
            cy = height * (0.3 + 0.25 * (index % 2))
            radius = min(width, height) * (0.55 - 0.1 * index)
            self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=color, outline="",
            )
        for fx, fy, size, color_index in self.stars:
            x, y = fx * width, fy * height
            self.canvas.create_oval(
                x - size / 2, y - size / 2, x + size / 2, y + size / 2,
                fill=theme["sparkles"][color_index], outline="",
            )
        unit = min(width, height) / WORLD_HEIGHT
        for fx, fy, radius, light, dark, ring in theme["decor"]:
            cx, cy, r = fx * width, fy * height, radius * unit
            self.canvas.create_oval(
                cx - r, cy - r, cx + r, cy + r, fill=dark, outline=""
            )
            self.canvas.create_oval(
                cx - r, cy - r, cx + r * 0.7, cy + r * 0.7,
                fill=light, outline="",
            )
            if ring:
                self.canvas.create_oval(
                    cx - r * 1.6, cy - r * 0.35, cx + r * 1.6, cy + r * 0.35,
                    outline=ring, width=max(1, 2 * unit),
                )

    def draw_path(self):
        glow, edge, fill = self.theme["path"]
        for grow, color in ((8, glow), (3, edge), (0, fill)):
            for left, top, right, bottom in corridor_rectangles(points=self.points):
                x1, y1 = self.to_screen((left - grow, top - grow))
                x2, y2 = self.to_screen((right + grow, bottom + grow))
                self.canvas.create_rectangle(
                    x1, y1, x2, y2, fill=color, outline=color
                )
        guide = [c for point in self.points for c in self.to_screen(point)]
        self.canvas.create_line(
            *guide, fill=self.theme["guide"], width=max(1, 2 * self.scale),
            dash=(6, 8), capstyle="round", joinstyle="round",
        )

    def draw_start_and_goal(self):
        theme = self.theme
        s = self.scale
        outer, inner, text_color = theme["start"]
        x, y = self.to_screen(self.run.start)
        for radius, color in ((30, outer), (25, inner)):
            self.canvas.create_oval(
                x - radius * s, y - radius * s, x + radius * s, y + radius * s,
                fill=color, outline="",
            )
        self.canvas.create_text(
            x, y, text="START", fill=text_color,
            font=("Arial", max(7, int(10 * s)), "bold"),
        )
        goal_outer, goal_inner, glyph_color, glyph, label_color = theme["goal"]
        fx, fy = self.to_screen(self.run.finish)
        for radius, color in (
            (GOAL_RADIUS + 12, goal_outer), (GOAL_RADIUS + 5, goal_inner)
        ):
            self.canvas.create_oval(
                fx - radius * s, fy - radius * s, fx + radius * s, fy + radius * s,
                fill=color, outline="",
            )
        self.canvas.create_text(
            fx, fy, text=glyph, fill=glyph_color,
            font=("Arial", max(10, int(26 * s)), "bold"),
        )
        gx, gy = self.to_screen(
            (self.run.finish[0], self.run.finish[1] - CORRIDOR_HALF_WIDTH - 10)
        )
        self.canvas.create_text(
            gx, gy, text="GOAL", fill=label_color,
            font=("Arial", max(8, int(11 * s)), "bold"),
        )

    def redraw(self):
        width, height = self.update_transform()
        self.canvas.configure(bg=self.theme["bg"])
        self.canvas.delete("all")
        self.draw_background(width, height)
        self.draw_path()
        self.draw_start_and_goal()
        self.update_trail()
        self.show_marker()

    def update_trail(self):
        self.canvas.delete("exhaust")
        length_limit, taper, layers = TRAILS[self.theme["vehicle"]]
        background = self.theme["path"][2]
        travelled = 0.0
        for start, end in reversed(self.trace):
            length = math.hypot(end[0] - start[0], end[1] - start[1])
            if length < 0.5:
                continue
            used = min(length, length_limit - travelled)
            if used <= 0:
                break
            ux, uy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
            tail = (end[0] - ux * used, end[1] - uy * used)
            age = (travelled + used / 2) / length_limit
            travelled += used
            fade = age ** 1.5
            for shift, color, width in layers:
                dx, dy = -uy * shift, ux * shift
                self.canvas.create_line(
                    *self.to_screen((tail[0] + dx, tail[1] + dy)),
                    *self.to_screen((end[0] + dx, end[1] + dy)),
                    fill=blend(color, background, fade),
                    width=max(1.0, width * (1 - taper * age) * self.scale),
                    capstyle="round", tags="exhaust",
                )

    def show_marker(self):
        self.canvas.delete("marker")
        if self.exploding:
            return
        x, y = self.to_screen(self.run.position)
        if self.theme["vehicle"] == "unicorn":
            self.show_unicorn(x, y)
        else:
            self.show_spaceship(x, y)

    def draw_parts(self, x, y, size, angle, mirror, parts, outline, tag="marker"):
        cos, sin = math.cos(angle), math.sin(angle)
        for points, color in parts:
            coordinates = []
            for px, py in points:
                px *= mirror
                coordinates.extend((
                    x + (px * cos - py * sin) * size,
                    y + (px * sin + py * cos) * size,
                ))
            self.canvas.create_polygon(
                coordinates, fill=color, outline=outline, tags=tag
            )

    def show_spaceship(self, x, y):
        self.draw_parts(
            x, y, 16 * self.scale, self.heading, 1,
            spaceship_parts(COLORS[self.color.get()]), "#ffffff",
        )

    def show_unicorn(self, x, y, shrink=1.0, tag="marker"):
        if abs(math.cos(self.heading)) > 0.3:
            self.facing = 1 if math.cos(self.heading) > 0 else -1
        angle = self.heading if self.facing > 0 else self.heading - math.pi
        self.draw_parts(
            x, y, 12 * self.scale * shrink, angle, self.facing,
            unicorn_parts(COLORS[self.color.get()]), "#ce93d8", tag,
        )

    def crash_point(self, start, end):
        low, high = 0.0, 1.0
        for _ in range(20):
            middle = (low + high) / 2
            point = (
                start[0] + (end[0] - start[0]) * middle,
                start[1] + (end[1] - start[1]) * middle,
            )
            if segment_in_corridor(start, point, self.points):
                low = middle
            else:
                high = middle
        return (
            start[0] + (end[0] - start[0]) * low,
            start[1] + (end[1] - start[1]) * low,
        )

    def explode(self, crash_world):
        self.exploding = True
        self.dragging = False
        self.canvas.delete("marker")
        rng = random.Random()
        particles = [
            (rng.uniform(0, math.tau), rng.uniform(25, 70),
             rng.choice(self.theme["boom_particles"]))
            for _ in range(22)
        ]
        self.message.set(self.theme["crash"])
        self.explosion_step(crash_world, particles, 0)

    def explosion_step(self, crash_world, particles, frame):
        self.canvas.delete("boom")
        if frame >= EXPLOSION_FRAMES:
            self.boom_job = None
            self.restart()
            self.message.set(self.theme["retry"])
            return
        progress = frame / EXPLOSION_FRAMES
        x, y = self.to_screen(crash_world)
        if self.theme["vehicle"] == "unicorn":
            self.draw_rainbow_poof(x, y, progress, particles)
        else:
            self.draw_fireball(x, y, progress, particles)
        self.boom_job = self.after(
            40, self.explosion_step, crash_world, particles, frame + 1
        )

    def draw_rainbow_poof(self, x, y, progress, particles):
        background = self.theme["path"][2]
        if progress < 0.6:
            self.show_unicorn(x, y, 1 - progress / 0.6, "boom")
        grow = min(1.0, progress / 0.6)
        fade = max(0.0, (progress - 0.6) / 0.4)
        stripe = 5 * self.scale
        for index, color in enumerate(RAINBOW_COLORS):
            radius = (10 + 48 * grow - index * 5) * self.scale
            if radius <= stripe / 2:
                continue
            self.canvas.create_arc(
                x - radius, y - radius, x + radius, y + radius,
                start=0, extent=180, style="arc", width=stripe * 1.2,
                outline=blend(color, background, fade), tags="boom",
            )
        for angle, speed, color in particles:
            distance = speed * progress * self.scale
            size = max(1.0, (3 - 2 * progress) * self.scale)
            px = x + math.cos(angle) * distance
            py = y + math.sin(angle) * distance
            self.canvas.create_oval(
                px - size, py - size, px + size, py + size,
                fill=color, outline="", tags="boom",
            )

    def draw_fireball(self, x, y, progress, particles):
        radius = (14 + 46 * progress) * self.scale
        if progress < 0.7:
            for factor, color in self.theme["boom_rings"]:
                r = radius * factor
                self.canvas.create_oval(
                    x - r, y - r, x + r, y + r, fill=color, outline="",
                    tags="boom",
                )
        for angle, speed, color in particles:
            distance = speed * progress * self.scale
            size = max(1.0, (4 - 3 * progress) * self.scale)
            px = x + math.cos(angle) * distance
            py = y + math.sin(angle) * distance
            self.canvas.create_oval(
                px - size, py - size, px + size, py + size,
                fill=color, outline="", tags="boom",
            )

    def start_drawing(self, event):
        if self.exploding:
            return
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
            self.explode(self.crash_point(previous, self.to_world(x, y)))
            return
        dx = self.run.position[0] - previous[0]
        dy = self.run.position[1] - previous[1]
        if math.hypot(dx, dy) > 1:
            self.heading = math.atan2(dy, dx)
        self.trace.append((previous, self.run.position))
        self.update_trail()
        self.show_marker()
        if result == "won":
            self.new_random_maze()
            self.message.set("Great job! Here is a new maze - can you finish it too?")
