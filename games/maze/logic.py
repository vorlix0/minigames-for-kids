"""Maze geometry and game rules, independent of the interface."""

from math import hypot


POINTS = (
    (95, 95), (325, 95), (325, 205), (175, 205), (175, 340),
    (470, 340), (470, 185), (650, 185), (650, 465), (365, 465),
    (365, 535), (710, 535),
)
CORRIDOR_HALF_WIDTH = 40
MARKER_RADIUS = 5
GOAL_RADIUS = 18
RESUME_DISTANCE = 15
START = POINTS[0]
FINISH = POINTS[-1]


def corridor_rectangles(inset=0):
    """Return corridor rectangles; inset accounts for the marker width."""
    half_width = CORRIDOR_HALF_WIDTH - inset
    return tuple(
        (
            min(a[0], b[0]) - half_width,
            min(a[1], b[1]) - half_width,
            max(a[0], b[0]) + half_width,
            max(a[1], b[1]) + half_width,
        )
        for a, b in zip(POINTS, POINTS[1:])
    )


def segment_interval(start, end, rect):
    """Return the segment interval inside the rectangle, parameterized from 0 to 1."""
    lower, upper = 0.0, 1.0
    for origin, delta, minimum, maximum in (
        (start[0], end[0] - start[0], rect[0], rect[2]),
        (start[1], end[1] - start[1], rect[1], rect[3]),
    ):
        if delta == 0:
            if not minimum <= origin <= maximum:
                return None
        else:
            first = (minimum - origin) / delta
            last = (maximum - origin) / delta
            lower = max(lower, min(first, last))
            upper = min(upper, max(first, last))
            if lower > upper:
                return None
    return lower, upper


def segment_in_corridor(start, end):
    intervals = sorted(
        interval
        for rect in corridor_rectangles(MARKER_RADIUS)
        if (interval := segment_interval(start, end, rect)) is not None
    )
    covered = 0.0
    for lower, upper in intervals:
        if lower > covered + 1e-9:
            return False
        covered = max(covered, upper)
        if covered >= 1.0 - 1e-9:
            return True
    return False


class MazeRun:
    def __init__(self, hard=False):
        self.hard = hard
        self.reset()

    def reset(self):
        self.position = START
        self.won = False

    def can_resume(self, point):
        return not self.won and hypot(
            point[0] - self.position[0], point[1] - self.position[1]
        ) <= RESUME_DISTANCE

    def move(self, point):
        if self.won:
            return "won"

        goal = (
            FINISH[0] - GOAL_RADIUS, FINISH[1] - GOAL_RADIUS,
            FINISH[0] + GOAL_RADIUS, FINISH[1] + GOAL_RADIUS,
        )
        goal_interval = segment_interval(self.position, point, goal)
        destination = point
        if goal_interval is not None:
            t = goal_interval[0]
            destination = (
                self.position[0] + (point[0] - self.position[0]) * t,
                self.position[1] + (point[1] - self.position[1]) * t,
            )

        if self.hard and not segment_in_corridor(self.position, destination):
            self.reset()
            return "reset"
        self.position = destination
        if goal_interval is not None:
            self.won = True
            return "won"
        return "moved"
