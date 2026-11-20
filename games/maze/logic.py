"""Maze geometry and game rules, independent of the interface."""

from math import hypot
import random


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


GRID_COLUMNS = 6
GRID_ROWS = 5
GRID_X0, GRID_Y0 = 60, 55
GRID_STEP_X, GRID_STEP_Y = 130, 120
MIN_CELLS = 16


def generate_points(rng=None):
    """Return a random winding route as corner points on a coarse grid.

    The route is a self-avoiding walk, so corridors never touch each other
    and there are no shortcuts.
    """
    rng = rng or random.Random()
    start = (rng.randrange(GRID_COLUMNS), rng.randrange(GRID_ROWS))
    path = [start]
    visited = {start}
    # Iterative randomized backtracking until the walk is long enough.
    options = [_shuffled_neighbors(start, visited, rng)]
    while len(path) < MIN_CELLS and options:
        if options[-1]:
            cell = options[-1].pop()
            if cell in visited:
                continue
            path.append(cell)
            visited.add(cell)
            options.append(_shuffled_neighbors(cell, visited, rng))
        else:
            options.pop()
            visited.discard(path.pop())
    if len(path) < MIN_CELLS:
        return generate_points(rng)

    corners = [path[0]]
    for before, cell, after in zip(path, path[1:], path[2:]):
        if (cell[0] - before[0], cell[1] - before[1]) != (
            after[0] - cell[0], after[1] - cell[1]
        ):
            corners.append(cell)
    corners.append(path[-1])
    return tuple(
        (GRID_X0 + column * GRID_STEP_X, GRID_Y0 + row * GRID_STEP_Y)
        for column, row in corners
    )


def _shuffled_neighbors(cell, visited, rng):
    column, row = cell
    neighbors = [
        (column + dx, row + dy)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))
        if 0 <= column + dx < GRID_COLUMNS
        and 0 <= row + dy < GRID_ROWS
        and (column + dx, row + dy) not in visited
    ]
    rng.shuffle(neighbors)
    return neighbors


def corridor_rectangles(inset=0, points=POINTS):
    """Return corridor rectangles; inset accounts for the marker width."""
    half_width = CORRIDOR_HALF_WIDTH - inset
    return tuple(
        (
            min(a[0], b[0]) - half_width,
            min(a[1], b[1]) - half_width,
            max(a[0], b[0]) + half_width,
            max(a[1], b[1]) + half_width,
        )
        for a, b in zip(points, points[1:])
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


def segment_in_corridor(start, end, points=POINTS):
    intervals = sorted(
        interval
        for rect in corridor_rectangles(MARKER_RADIUS, points)
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
    def __init__(self, hard=False, points=POINTS):
        self.hard = hard
        self.points = points
        self.start = points[0]
        self.finish = points[-1]
        self.reset()

    def reset(self):
        self.position = self.start
        self.won = False

    def can_resume(self, point, distance=RESUME_DISTANCE):
        return not self.won and hypot(
            point[0] - self.position[0], point[1] - self.position[1]
        ) <= distance

    def move(self, point):
        if self.won:
            return "won"

        goal = (
            self.finish[0] - GOAL_RADIUS, self.finish[1] - GOAL_RADIUS,
            self.finish[0] + GOAL_RADIUS, self.finish[1] + GOAL_RADIUS,
        )
        goal_interval = segment_interval(self.position, point, goal)
        destination = point
        if goal_interval is not None:
            t = goal_interval[0]
            destination = (
                self.position[0] + (point[0] - self.position[0]) * t,
                self.position[1] + (point[1] - self.position[1]) * t,
            )

        if self.hard and not segment_in_corridor(
            self.position, destination, self.points
        ):
            self.reset()
            return "reset"
        self.position = destination
        if goal_interval is not None:
            self.won = True
            return "won"
        return "moved"
