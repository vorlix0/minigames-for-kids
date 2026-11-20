"""Android (Kivy) version of the maze game. Also runs on the desktop for testing."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.graphics import (
    Color, Ellipse, Line, Mesh, Rectangle,
    StencilPop, StencilPush, StencilUnUse, StencilUse,
)
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from games.maze.logic import (
    CORRIDOR_HALF_WIDTH,
    GOAL_RADIUS,
    POINTS,
    RESUME_DISTANCE,
    MazeRun,
    corridor_rectangles,
    generate_points,
    segment_in_corridor,
)
from games.maze.themes import (
    COLORS,
    EXPLOSION_FRAMES,
    RAINBOW_COLORS,
    STAR_COUNT,
    THEMES,
    TRAILS,
    VEHICLE_OUTLINE,
    VEHICLE_SIZE,
    WORLD_HEIGHT,
    WORLD_WIDTH,
    blend,
    spaceship_parts,
    unicorn_parts,
)


def rgba(color, alpha=1.0):
    red, green, blue, _ = get_color_from_hex(color)
    return red, green, blue, alpha


class MazeWidget(Widget):
    def __init__(self, on_message, **kwargs):
        super().__init__(**kwargs)
        self.on_message = on_message
        self.theme_name = "Space"
        self.color_name = "Blue"
        self.hard = False
        self.points = POINTS
        self.run = MazeRun(points=self.points)
        self.trace = []
        self.heading = 0.0
        self.facing = 1
        self.dragging = False
        self.drag_offset = (0.0, 0.0)
        self.explosion = None
        self.crash = None
        self.scale = 1.0
        self.offset = (0.0, 0.0)
        self.text_cache = {}
        rng = random.Random(7)
        self.stars = [
            (rng.random(), rng.random(), rng.choice((1, 1, 2, 3)),
             rng.randrange(3))
            for _ in range(STAR_COUNT)
        ]
        self.bind(pos=self.redraw, size=self.redraw)
        self.restart()

    @property
    def theme(self):
        return THEMES[self.theme_name]

    def to_screen(self, point):
        return (
            self.offset[0] + point[0] * self.scale,
            self.offset[1] + point[1] * self.scale,
        )

    def to_world(self, sx, sy):
        return (
            (sx - self.offset[0]) / self.scale,
            (sy - self.offset[1]) / self.scale,
        )

    def local(self, touch):
        return touch.x - self.x, self.height - (touch.y - self.y)

    def flat(self, sx, sy):
        """Convert top-left based widget coordinates to Kivy window coordinates."""
        return self.x + sx, self.y + self.height - sy

    def restart(self, *_):
        if self.explosion is not None:
            self.explosion.cancel()
            self.explosion = None
        self.run = MazeRun(hard=self.hard, points=self.points)
        self.dragging = False
        self.trace = []
        first, second = self.points[0], self.points[1]
        self.heading = math.atan2(second[1] - first[1], second[0] - first[0])
        self.facing = 1 if second[0] >= first[0] else -1
        self.redraw()
        self.on_message("Touch the start and guide your ride to the goal.")

    def new_random_maze(self, *_):
        self.points = generate_points()
        self.restart()

    def set_theme(self, name):
        self.theme_name = name
        self.redraw()

    def set_color(self, name):
        self.color_name = name
        self.redraw()

    def set_hard(self, hard):
        self.hard = hard
        self.restart()

    def polygon(self, points, fill, outline=None):
        flat = [value for point in points for value in self.flat(*point)]
        tess = Tesselator()
        tess.add_contour(flat)
        if not tess.tesselate(WINDING_ODD, TYPE_POLYGONS):
            return
        Color(*rgba(fill))
        for vertices, indices in tess.meshes:
            Mesh(vertices=vertices, indices=indices, mode="triangle_fan")
        if outline:
            Color(*rgba(outline))
            Line(points=flat, close=True, width=1)

    def circle(self, cx, cy, radius, fill):
        Color(*rgba(fill))
        x, y = self.flat(cx - radius, cy + radius)
        Ellipse(pos=(x, y), size=(radius * 2, radius * 2))

    def text(self, value, cx, cy, size, fill):
        key = (value, size, fill)
        label = self.text_cache.get(key)
        if label is None:
            label = CoreLabel(text=value, font_size=size, bold=True)
            label.refresh()
            self.text_cache[key] = label
        texture = label.texture
        x, y = self.flat(cx - texture.width / 2, cy + texture.height / 2)
        Color(*rgba(fill))
        Rectangle(texture=texture, pos=(x, y), size=texture.size)

    def redraw(self, *_):
        width, height = max(self.width, 1), max(self.height, 1)
        self.scale = min(width / WORLD_WIDTH, height / WORLD_HEIGHT)
        self.offset = (
            (width - WORLD_WIDTH * self.scale) / 2,
            (height - WORLD_HEIGHT * self.scale) / 2,
        )
        self.canvas.clear()
        with self.canvas:
            StencilPush()
            Rectangle(pos=self.pos, size=self.size)
            StencilUse()
            Color(*rgba(self.theme["bg"]))
            Rectangle(pos=self.pos, size=self.size)
            self.draw_background(width, height)
            self.draw_path()
            self.draw_start_and_goal()
            self.draw_trail()
            self.draw_vehicle()
            self.draw_explosion()
            StencilUnUse()
            Rectangle(pos=self.pos, size=self.size)
            StencilPop()

    def draw_background(self, width, height):
        theme = self.theme
        for index, color in enumerate(theme["nebula"]):
            cx = width * (0.25 + 0.3 * index)
            cy = height * (0.3 + 0.25 * (index % 2))
            radius = min(width, height) * (0.55 - 0.1 * index)
            self.circle(cx, cy, radius, color)
        for fx, fy, size, color_index in self.stars:
            self.circle(
                fx * width, fy * height, size * max(self.scale, 1) / 2,
                theme["sparkles"][color_index],
            )
        unit = min(width, height) / WORLD_HEIGHT
        for fx, fy, radius, light, dark, ring in theme["decor"]:
            cx, cy, r = fx * width, fy * height, radius * unit
            self.circle(cx, cy, r, dark)
            self.circle(cx - r * 0.15, cy - r * 0.15, r * 0.85, light)
            if ring:
                Color(*rgba(ring))
                x, y = self.flat(cx - r * 1.6, cy + r * 0.35)
                Line(ellipse=(x, y, r * 3.2, r * 0.7), width=max(1, 2 * unit))

    def draw_path(self):
        glow, edge, fill = self.theme["path"]
        for grow, color in ((8, glow), (3, edge), (0, fill)):
            Color(*rgba(color))
            for left, top, right, bottom in corridor_rectangles(points=self.points):
                x1, y1 = self.to_screen((left - grow, top - grow))
                x2, y2 = self.to_screen((right + grow, bottom + grow))
                px, py = self.flat(x1, y2)
                Rectangle(pos=(px, py), size=(x2 - x1, y2 - y1))
        Color(*rgba(self.theme["guide"]))
        guide = [v for p in self.points for v in self.flat(*self.to_screen(p))]
        Line(points=guide, width=max(1, 2 * self.scale), dash_length=6, dash_offset=8)

    def draw_start_and_goal(self):
        theme = self.theme
        s = self.scale
        outer, inner, text_color = theme["start"]
        x, y = self.to_screen(self.run.start)
        self.circle(x, y, 30 * s, outer)
        self.circle(x, y, 25 * s, inner)
        self.text("START", x, y, max(10, int(13 * s)), text_color)
        goal_outer, goal_inner, glyph_color, _glyph, label_color = theme["goal"]
        fx, fy = self.to_screen(self.run.finish)
        self.circle(fx, fy, (GOAL_RADIUS + 12) * s, goal_outer)
        self.circle(fx, fy, (GOAL_RADIUS + 5) * s, goal_inner)
        if theme["vehicle"] == "unicorn":
            self.draw_heart(fx, fy, 13 * s, glyph_color)
        else:
            self.draw_star(fx, fy, 14 * s, glyph_color)
        gx, gy = self.to_screen(
            (self.run.finish[0], self.run.finish[1] - CORRIDOR_HALF_WIDTH - 10)
        )
        self.text("GOAL", gx, gy, max(10, int(14 * s)), label_color)

    def draw_star(self, cx, cy, radius, color):
        points = []
        for index in range(10):
            r = radius if index % 2 == 0 else radius * 0.45
            angle = -math.pi / 2 + index * math.pi / 5
            points.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        self.polygon(points, color)

    def draw_heart(self, cx, cy, radius, color):
        self.circle(cx - radius * 0.5, cy - radius * 0.3, radius * 0.55, color)
        self.circle(cx + radius * 0.5, cy - radius * 0.3, radius * 0.55, color)
        self.polygon(
            [(cx - radius * 1.02, cy - radius * 0.1),
             (cx + radius * 1.02, cy - radius * 0.1),
             (cx, cy + radius * 1.0)],
            color,
        )

    def draw_trail(self):
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
                Color(*rgba(blend(color, background, fade)))
                Line(
                    points=[
                        *self.flat(*self.to_screen((tail[0] + dx, tail[1] + dy))),
                        *self.flat(*self.to_screen((end[0] + dx, end[1] + dy))),
                    ],
                    width=max(1.0, width * (1 - taper * age) * self.scale) / 2,
                    cap="round",
                )

    def draw_parts(self, x, y, size, angle, mirror, parts, outline):
        cos, sin = math.cos(angle), math.sin(angle)
        for points, color in parts:
            self.polygon(
                [
                    (x + (px * mirror * cos - py * sin) * size,
                     y + (px * mirror * sin + py * cos) * size)
                    for px, py in points
                ],
                color, outline,
            )

    def draw_vehicle(self, position=None, shrink=1.0):
        if self.explosion is not None and position is None:
            return
        x, y = self.to_screen(position or self.run.position)
        vehicle = self.theme["vehicle"]
        color = COLORS[self.color_name]
        size = VEHICLE_SIZE[vehicle] * self.scale * shrink
        if vehicle == "unicorn":
            if abs(math.cos(self.heading)) > 0.3:
                self.facing = 1 if math.cos(self.heading) > 0 else -1
            angle = self.heading if self.facing > 0 else self.heading - math.pi
            self.draw_parts(
                x, y, size, angle, self.facing, unicorn_parts(color),
                VEHICLE_OUTLINE[vehicle],
            )
        else:
            self.draw_parts(
                x, y, size, self.heading, 1, spaceship_parts(color),
                VEHICLE_OUTLINE[vehicle],
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
        self.dragging = False
        rng = random.Random()
        particles = [
            (rng.uniform(0, math.tau), rng.uniform(25, 70),
             rng.choice(self.theme["boom_particles"]))
            for _ in range(22)
        ]
        self.crash = {"at": crash_world, "particles": particles, "frame": 0}
        self.explosion = Clock.schedule_interval(self.explosion_step, 0.04)
        self.on_message(self.theme["crash"])
        self.vibrate()
        self.redraw()

    def explosion_step(self, _dt):
        self.crash["frame"] += 1
        if self.crash["frame"] >= EXPLOSION_FRAMES:
            self.explosion.cancel()
            self.explosion = None
            self.restart()
            self.on_message(self.theme["retry"])
            return
        self.redraw()

    def draw_explosion(self):
        if self.explosion is None:
            return
        progress = self.crash["frame"] / EXPLOSION_FRAMES
        x, y = self.to_screen(self.crash["at"])
        if self.theme["vehicle"] == "unicorn":
            self.draw_rainbow_poof(x, y, progress)
        else:
            self.draw_fireball(x, y, progress)
        for angle, speed, color in self.crash["particles"]:
            distance = speed * progress * self.scale
            size = max(1.0, (4 - 3 * progress) * self.scale)
            self.circle(
                x + math.cos(angle) * distance, y + math.sin(angle) * distance,
                size, color,
            )

    def draw_fireball(self, x, y, progress):
        if progress >= 0.7:
            return
        radius = (14 + 46 * progress) * self.scale
        for factor, color in self.theme["boom_rings"]:
            self.circle(x, y, radius * factor, color)

    def draw_rainbow_poof(self, x, y, progress):
        background = self.theme["path"][2]
        if progress < 0.6:
            self.draw_vehicle(self.crash["at"], 1 - progress / 0.6)
        grow = min(1.0, progress / 0.6)
        fade = max(0.0, (progress - 0.6) / 0.4)
        stripe = 5 * self.scale
        for index, color in enumerate(RAINBOW_COLORS):
            radius = (10 + 48 * grow - index * 5) * self.scale
            if radius <= stripe / 2:
                continue
            Color(*rgba(blend(color, background, fade)))
            px, py = self.flat(x, y)
            Line(circle=(px, py, radius, -90, 90), width=stripe * 0.6)

    def vibrate(self):
        try:
            from plyer import vibrator
            vibrator.vibrate(0.15)
        except Exception:
            pass

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos) or self.explosion is not None:
            return super().on_touch_down(touch)
        touch_local = self.local(touch)
        resume_distance = max(RESUME_DISTANCE, dp(24) / self.scale)
        if not self.dragging and self.run.can_resume(
            self.to_world(*touch_local), resume_distance
        ):
            self.dragging = True
            marker = self.to_screen(self.run.position)
            self.drag_offset = (
                touch_local[0] - marker[0],
                touch_local[1] - marker[1],
            )
            touch.grab(self)
            return True
        return False

    def on_touch_move(self, touch):
        if touch.grab_current is self and self.dragging:
            self.move_to(*self.drag_target(touch))
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.dragging:
                self.move_to(*self.drag_target(touch))
            self.dragging = False
            return True
        return False

    def drag_target(self, touch):
        sx, sy = self.local(touch)
        return sx - self.drag_offset[0], sy - self.drag_offset[1]

    def move_to(self, sx, sy):
        previous = self.run.position
        target = self.to_world(sx, sy)
        result = self.run.move(target)
        if result == "reset":
            self.explode(self.crash_point(previous, target))
            return
        dx = self.run.position[0] - previous[0]
        dy = self.run.position[1] - previous[1]
        if math.hypot(dx, dy) > 1:
            self.heading = math.atan2(dy, dx)
        self.trace.append((previous, self.run.position))
        if result == "won":
            self.new_random_maze()
            self.on_message("Great job! Here is a new maze - can you finish it too?")
            return
        self.redraw()


class MazeApp(App):
    title = "Minigames for Kids"

    def build(self):
        root = BoxLayout(orientation="vertical")
        bar = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(4), padding=dp(4))
        self.message = Label(size_hint_y=None, height=dp(32), font_size=dp(14))
        self.maze = MazeWidget(self.show_message)

        theme = Spinner(text="Space", values=list(THEMES))
        theme.bind(text=lambda _, value: self.maze.set_theme(value))
        color = Spinner(text="Blue", values=list(COLORS))
        color.bind(text=lambda _, value: self.maze.set_color(value))
        hard = ToggleButton(text="Hard")
        hard.bind(state=lambda _, state: self.maze.set_hard(state == "down"))
        new = Button(text="New maze")
        new.bind(on_release=self.maze.new_random_maze)
        restart = Button(text="Restart")
        restart.bind(on_release=self.maze.restart)
        for widget in (theme, color, hard, new, restart):
            bar.add_widget(widget)

        root.add_widget(bar)
        root.add_widget(self.maze)
        root.add_widget(self.message)
        return root

    def show_message(self, text):
        self.message.text = text


if __name__ == "__main__":
    MazeApp().run()
