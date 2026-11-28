"""Android (Kivy) version of the maze game. Also runs on the desktop for testing."""

import math
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import Label as CoreLabel
from kivy.core.window import Window
from kivy.graphics import (
    Color, Ellipse, Line, Mesh, Rectangle, RoundedRectangle,
    StencilPop, StencilPush, StencilUnUse, StencilUse,
)
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex

from games.maze.logic import (
    CORRIDOR_HALF_WIDTH,
    GOAL_RADIUS,
    POINTS,
    MazeRun,
    corridor_rectangles,
    direction_target,
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


class DirectionButton(Button):
    def __init__(self, direction, **kwargs):
        super().__init__(**kwargs)
        self.direction = direction
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        with self.canvas.before:
            self.button_color = Color(0.35, 0.35, 0.4, 1)
            self.button_shape = RoundedRectangle(radius=[dp(14)])
        with self.canvas.after:
            Color(1, 1, 1, 1)
            self.shaft = Line(width=dp(2.5), cap="round")
            self.arrowhead = Line(width=dp(2.5), cap="round", joint="round")
        self.bind(
            pos=self.update_arrow, size=self.update_arrow,
            state=self.update_button_color,
        )
        self.update_arrow()

    def update_button_color(self, *_):
        self.button_color.rgba = (
            (0.25, 0.25, 0.32, 1) if self.state == "down"
            else (0.35, 0.35, 0.4, 1)
        )

    def update_arrow(self, *_):
        self.button_shape.pos = self.pos
        self.button_shape.size = self.size
        cx, cy = self.center
        size = min(self.width, self.height) * 0.3
        dx, dy = self.direction
        # World coordinates use a downward-pointing y axis; Kivy uses upward.
        dy = -dy
        tip = (cx + dx * size, cy + dy * size)
        self.shaft.points = (
            cx - dx * size, cy - dy * size, *tip,
        )
        self.arrowhead.points = (
            cx - dy * size * 0.65, cy + dx * size * 0.65,
            *tip,
            cx + dy * size * 0.65, cy - dx * size * 0.65,
        )


class MazeWidget(Widget):
    def __init__(self, on_message, **kwargs):
        super().__init__(**kwargs)
        self.on_message = on_message
        self.theme_name = "Space"
        self.color_name = "Blue"
        self.points = POINTS
        self.run = MazeRun(points=self.points)
        self.trace = []
        self.heading = 0.0
        self.facing = 1
        self.direction = None
        self.move_event = None
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

    def flat(self, sx, sy):
        """Convert top-left based widget coordinates to Kivy window coordinates."""
        return self.x + sx, self.y + self.height - sy

    def restart(self, *_):
        self.stop_move()
        if self.explosion is not None:
            self.explosion.cancel()
            self.explosion = None
        self.run = MazeRun(points=self.points)
        self.trace = []
        first, second = self.points[0], self.points[1]
        self.heading = math.atan2(second[1] - first[1], second[0] - first[0])
        self.facing = 1 if second[0] >= first[0] else -1
        self.redraw()
        self.on_message("")

    def start_move(self, direction):
        if self.explosion is not None or self.direction == direction:
            return
        self.stop_move()
        self.direction = direction
        self.move_step(0)
        if self.direction is not None:
            self.move_event = Clock.schedule_interval(self.move_step, 0.05)

    def stop_move(self, direction=None):
        if direction is not None and direction != self.direction:
            return
        self.direction = None
        if self.move_event is not None:
            self.move_event.cancel()
            self.move_event = None

    def move_step(self, _dt):
        if self.direction is None or self.explosion is not None:
            return
        target = direction_target(self.run.position, self.direction)
        self.move_to(*self.to_screen(target))

    def new_random_maze(self, *_):
        self.points = generate_points()
        self.restart()

    def set_theme(self, name):
        self.theme_name = name
        self.redraw()

    def set_color(self, name):
        self.color_name = name
        self.redraw()

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
        self.stop_move()
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
    keys = {273: (0, -1), 276: (-1, 0), 274: (0, 1), 275: (1, 0)}

    def build(self):
        self.screen_root = BoxLayout(orientation="vertical")
        self.maze = None
        self.theme_name = "Space"
        self.color_name = "Blue"
        self.controls_side = "right"
        self.show_menu()
        Window.bind(
            on_key_down=self.key_down, on_key_up=self.key_up,
            on_focus=self.window_focus,
        )
        return self.screen_root

    def show_menu(self, *_):
        self.leave_game()
        self.screen_root.clear_widgets()
        menu = BoxLayout(orientation="vertical", padding=dp(24), spacing=dp(12))
        menu.add_widget(Label(text="Minigames for Kids", font_size=dp(28)))
        maze = Button(
            text="Maze", font_size=dp(22), size_hint=(0.6, None),
            height=dp(64), pos_hint={"center_x": 0.5},
        )
        maze.bind(on_release=self.show_options)
        menu.add_widget(maze)
        menu.add_widget(Widget())
        self.screen_root.add_widget(menu)

    def show_options(self, *_):
        self.leave_game()
        self.screen_root.clear_widgets()
        options = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(8))
        options.add_widget(Label(text="Maze", font_size=dp(26)))
        theme = Spinner(
            text=self.theme_name, values=list(THEMES), size_hint=(0.6, None),
            height=dp(56), pos_hint={"center_x": 0.5},
        )
        theme.bind(text=lambda _, value: setattr(self, "theme_name", value))
        color = Spinner(
            text=self.color_name, values=list(COLORS), size_hint=(0.6, None),
            height=dp(56), pos_hint={"center_x": 0.5},
        )
        color.bind(text=lambda _, value: setattr(self, "color_name", value))
        options.add_widget(theme)
        options.add_widget(color)
        start = Button(
            text="Start", font_size=dp(20), size_hint=(0.6, None),
            height=dp(56), pos_hint={"center_x": 0.5},
        )
        start.bind(on_release=self.show_game)
        options.add_widget(start)
        back = Button(
            text="Back", size_hint=(0.6, None), height=dp(56),
            pos_hint={"center_x": 0.5},
        )
        back.bind(on_release=self.show_menu)
        options.add_widget(back)
        options.add_widget(Widget())
        self.screen_root.add_widget(options)

    def show_game(self, *_):
        self.leave_game()
        self.screen_root.clear_widgets()
        bar = BoxLayout(size_hint_y=None, height=dp(64), spacing=dp(4), padding=dp(4))
        self.message = Label(font_size=dp(14))
        self.maze = MazeWidget(self.show_message)
        self.maze.set_theme(self.theme_name)
        self.maze.set_color(self.color_name)

        back = Button(text="Options")
        back.bind(on_release=self.show_options)
        new = Button(text="New maze")
        new.bind(on_release=self.maze.new_random_maze)
        restart = Button(text="Restart")
        restart.bind(on_release=self.maze.restart)
        for widget in (back, new, restart):
            bar.add_widget(widget)

        self.footer = BoxLayout(size_hint_y=None, height=dp(116), spacing=dp(4))
        with self.footer.canvas.before:
            Color(*rgba(THEMES[self.theme_name]["bg"]))
            self.footer_background = Rectangle()
        self.footer.bind(
            pos=self.update_footer_background, size=self.update_footer_background
        )
        self.update_footer_background()
        self.footer_info = BoxLayout(orientation="vertical")
        self.footer_info.add_widget(self.message)
        self.side_button = Button(
            text=f"Controls: {self.controls_side}", size_hint_y=None, height=dp(56)
        )
        self.side_button.bind(on_release=self.toggle_controls_side)
        self.footer_info.add_widget(self.side_button)
        self.direction_controls = GridLayout(
            cols=3, rows=2, size_hint_x=None, width=dp(200), spacing=dp(4)
        )
        for direction in (
            None, (0, -1), None,
            (-1, 0), (0, 1), (1, 0),
        ):
            if direction is None:
                self.direction_controls.add_widget(Widget())
                continue
            button = DirectionButton(direction)
            button.bind(
                on_press=lambda _, d=direction: self.maze.start_move(d),
                on_release=lambda _, d=direction: self.maze.stop_move(d),
            )
            self.direction_controls.add_widget(button)
        if self.controls_side == "right":
            self.footer.add_widget(self.footer_info)
            self.footer.add_widget(self.direction_controls)
        else:
            self.footer.add_widget(self.direction_controls)
            self.footer.add_widget(self.footer_info)
        self.screen_root.add_widget(bar)
        self.screen_root.add_widget(self.maze)
        self.screen_root.add_widget(self.footer)

    def update_footer_background(self, *_):
        self.footer_background.pos = self.footer.pos
        self.footer_background.size = self.footer.size

    def leave_game(self):
        if self.maze is None:
            return
        self.maze.stop_move()
        if self.maze.explosion is not None:
            self.maze.explosion.cancel()
            self.maze.explosion = None
        self.maze = None

    def toggle_controls_side(self, *_):
        self.maze.stop_move()
        on_right = self.side_button.text == "Controls: right"
        self.footer.remove_widget(self.footer_info)
        self.footer.remove_widget(self.direction_controls)
        if on_right:
            self.footer.add_widget(self.direction_controls)
            self.footer.add_widget(self.footer_info)
        else:
            self.footer.add_widget(self.footer_info)
            self.footer.add_widget(self.direction_controls)
        self.controls_side = "left" if on_right else "right"
        self.side_button.text = f"Controls: {self.controls_side}"

    def key_down(self, _window, key, _scancode, _codepoint, _modifiers):
        if self.maze is not None and key in self.keys:
            self.maze.start_move(self.keys[key])
            return True
        return False

    def key_up(self, _window, key, _scancode):
        if self.maze is not None and key in self.keys:
            self.maze.stop_move(self.keys[key])
            return True
        return False

    def on_pause(self):
        if self.maze is not None:
            self.maze.stop_move()
        return True

    def window_focus(self, _window, focused):
        if not focused and self.maze is not None:
            self.maze.stop_move()

    def on_stop(self):
        self.leave_game()
        Window.unbind(
            on_key_down=self.key_down, on_key_up=self.key_up,
            on_focus=self.window_focus,
        )

    def show_message(self, text):
        self.message.text = text


if __name__ == "__main__":
    MazeApp().run()
