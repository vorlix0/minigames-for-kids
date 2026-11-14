"""Look and feel of the maze game, shared by the desktop and Android versions."""

COLORS = {
    "Red": "#e53935",
    "Blue": "#1e88e5",
    "Green": "#43a047",
    "Purple": "#8e24aa",
    "Orange": "#fb8c00",
}

WORLD_WIDTH = 800
WORLD_HEIGHT = 610
STAR_COUNT = 140
EXPLOSION_FRAMES = 16
RAINBOW_STRIPE_WIDTH = 3.6
RAINBOW_COLORS = (
    "#ff1744", "#ff9100", "#ffea00", "#00e676", "#2979ff", "#d500f9",
)
# vehicle -> (trail length, taper, ((sideways shift, color, width), ...))
TRAILS = {
    "unicorn": (
        170, 0.5,
        tuple(
            ((index - (len(RAINBOW_COLORS) - 1) / 2) * RAINBOW_STRIPE_WIDTH,
             color, RAINBOW_STRIPE_WIDTH * 1.15)
            for index, color in enumerate(RAINBOW_COLORS)
        ),
    ),
    "spaceship": (
        90, 0.9,
        ((0, "#ff3d00", 12), (0, "#ff9100", 8), (0, "#fff59d", 4)),
    ),
}
VEHICLE_SIZE = {"spaceship": 16, "unicorn": 12}
VEHICLE_OUTLINE = {"spaceship": "#ffffff", "unicorn": "#ce93d8"}

THEMES = {
    "Space": {
        "vehicle": "spaceship",
        "bg": "#0b0d2a",
        "nebula": ("#14123f", "#1b1650", "#241a5e"),
        "sparkles": ("#ffffff", "#cfd8ff", "#fff3b0"),
        "decor": (
            (0.88, 0.14, 38, "#ff8a65", "#bf5b3e", "#ffd9c7"),
            (0.10, 0.88, 26, "#4dd0e1", "#2a8a96", None),
        ),
        "path": ("#3a3f9e", "#7c83ff", "#1d2260"),
        "guide": "#4a52c4",
        "start": ("#1b5e20", "#66bb6a", "#06260a"),
        "goal": ("#7a4a00", "#ffb300", "#fff8e1", "★", "#ffe082"),
        "boom_rings": (
            (1.0, "#ff7043"), (0.65, "#ffca28"), (0.3, "#fffde7"),
        ),
        "boom_particles": ("#ff5722", "#ffc107", "#fff176", "#ffffff"),
        "crash": "Boom! The spaceship crashed into the wall!",
        "retry": "Oops! The ship crashed. Try again!",
    },
    "Unicorn": {
        "vehicle": "unicorn",
        "bg": "#ffe6f3",
        "nebula": ("#ffd6ec", "#e9d5ff", "#cdeafe"),
        "sparkles": ("#ffffff", "#ffd54f", "#f8a5d0"),
        "decor": (
            (0.88, 0.14, 38, "#fff59d", "#ffd54f", None),
            (0.10, 0.88, 26, "#f8bbd0", "#f06292", None),
        ),
        "path": ("#f8c8e0", "#f48fb1", "#fff8fc"),
        "guide": "#f3b3d6",
        "start": ("#689f38", "#c5e1a5", "#1b3a0a"),
        "goal": ("#ad1457", "#f06292", "#ffffff", "♥", "#ad1457"),
        "boom_rings": (
            (1.0, "#f48fb1"), (0.65, "#ffe082"), (0.3, "#ffffff"),
        ),
        "boom_particles": ("#ff80ab", "#ffd54f", "#ffffff", "#b388ff"),
        "crash": "Poof! The unicorn turned into a rainbow!",
        "retry": "Oops! The unicorn became a rainbow. Try again!",
    },
}


def blend(color, other, amount):
    """Mix two #rrggbb colors; amount 0 gives color, 1 gives other."""
    mixed = []
    for index in (1, 3, 5):
        first = int(color[index:index + 2], 16)
        second = int(other[index:index + 2], 16)
        mixed.append(round(first + (second - first) * amount))
    return "#%02x%02x%02x" % tuple(mixed)


def spaceship_parts(color):
    return (
        ([(-0.6, 0), (-1.5, -0.35), (-1.2, 0), (-1.5, 0.35)], "#ffb300"),
        ([(-0.2, -0.5), (-1.0, -1.0), (-0.8, -0.2)], "#b0bec5"),
        ([(-0.2, 0.5), (-1.0, 1.0), (-0.8, 0.2)], "#b0bec5"),
        ([(1.2, 0), (0.4, -0.5), (-0.8, -0.4), (-0.8, 0.4), (0.4, 0.5)], color),
        ([(0.8, 0), (0.3, -0.25), (0.3, 0.25)], "#b3e5fc"),
    )


def unicorn_parts(mane):
    white = "#ffffff"
    return (
        ([(-0.95, -0.1), (-1.6, -0.55), (-1.5, 0.05), (-1.75, 0.5),
          (-1.0, 0.3)], mane),
        ([(-0.8, 0.3), (-0.5, 0.3), (-0.5, 0.95), (-0.8, 0.95)], "#e1bee7"),
        ([(0.4, 0.3), (0.7, 0.3), (0.7, 0.95), (0.4, 0.95)], "#e1bee7"),
        ([(-1.0, -0.1), (-0.8, -0.5), (0, -0.6), (0.8, -0.5), (1.0, -0.1),
          (0.8, 0.4), (0, 0.5), (-0.8, 0.4)], white),
        ([(0.7, -0.5), (1.05, -1.0), (1.6, -1.0), (1.85, -0.6),
          (1.5, -0.35), (1.0, -0.1)], white),
        ([(0.6, -0.55), (0.85, -1.2), (1.15, -1.05), (0.95, -0.35)], mane),
        ([(1.4, -1.0), (1.58, -1.0), (1.8, -1.8)], "#ffd54f"),
        ([(1.45, -0.8), (1.6, -0.8), (1.6, -0.65), (1.45, -0.65)], "#4a148c"),
    )
