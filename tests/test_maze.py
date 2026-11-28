import random
import unittest

from games.maze.logic import (
    FINISH,
    POINTS,
    START,
    MazeRun,
    corridor_rectangles,
    direction_target,
    generate_points,
    segment_in_corridor,
)


class MazeTests(unittest.TestCase):
    def test_arrow_steps_follow_world_coordinates_and_stay_visible(self):
        self.assertEqual(direction_target((100, 100), (0, -1)), (100, 92))
        self.assertEqual(direction_target((100, 100), (1, 0)), (108, 100))
        self.assertEqual(direction_target((0, 0), (-1, 0)), (0, 0))
        self.assertEqual(direction_target((800, 610), (0, 1)), (800, 610))

    def test_arrow_step_detects_wall_collision(self):
        game = MazeRun()
        game.move((130, 130))
        self.assertEqual(game.move(direction_target(game.position, (0, 1))), "reset")
        self.assertEqual(game.position, START)

    def test_entire_route_is_valid(self):
        game = MazeRun()
        for point in POINTS[1:-1]:
            self.assertEqual(game.move(point), "moved")
        self.assertEqual(game.move(FINISH), "won")
        self.assertTrue(game.won)

    def test_crossing_wall_resets_run(self):
        game = MazeRun()
        self.assertEqual(game.move((325, 95)), "moved")
        self.assertEqual(game.move((325, 340)), "reset")
        self.assertEqual(game.position, START)
        self.assertFalse(game.won)

    def test_marker_width_is_checked_at_corridor_edge(self):
        self.assertTrue(segment_in_corridor(START, (150, 130)))
        self.assertFalse(segment_in_corridor(START, (150, 131)))

    def test_crossing_goal_wins(self):
        game = MazeRun()
        for point in POINTS[1:-1]:
            self.assertEqual(game.move(point), "moved")
        self.assertEqual(game.move((750, 535)), "won")

    def test_random_mazes_are_solvable_and_stay_on_canvas(self):
        for seed in range(50):
            points = generate_points(random.Random(seed))
            game = MazeRun(points=points)
            for point in points[1:-1]:
                self.assertEqual(game.move(point), "moved")
            self.assertEqual(game.move(points[-1]), "won")
            for left, top, right, bottom in corridor_rectangles(points=points):
                self.assertGreaterEqual(min(left, top), 0)
                self.assertLessEqual(right, 800)
                self.assertLessEqual(bottom, 610)

    def test_random_maze_has_no_shortcuts(self):
        points = generate_points(random.Random(3))
        rectangles = corridor_rectangles(points=points)
        for index, first in enumerate(rectangles):
            for second in rectangles[index + 2:]:
                self.assertTrue(
                    first[2] <= second[0] or second[2] <= first[0]
                    or first[3] <= second[1] or second[3] <= first[1]
                )

    def test_resume_requires_click_near_current_position(self):
        game = MazeRun()
        game.move((200, 95))
        self.assertFalse(game.can_resume(START))
        self.assertTrue(game.can_resume((205, 95)))
        for point in POINTS[1:]:
            game.move(point)
        self.assertFalse(game.can_resume(FINISH))

    def test_resume_allows_a_larger_touch_target_when_requested(self):
        game = MazeRun()
        self.assertFalse(game.can_resume((126, 95)))
        self.assertTrue(game.can_resume((126, 95), distance=31))


if __name__ == "__main__":
    unittest.main()
