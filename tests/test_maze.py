import unittest

from games.maze.logic import FINISH, POINTS, START, MazeRun, segment_in_corridor


class MazeTests(unittest.TestCase):
    def test_entire_route_is_valid_in_hard_mode(self):
        game = MazeRun(hard=True)
        for point in POINTS[1:-1]:
            self.assertEqual(game.move(point), "moved")
        self.assertEqual(game.move(FINISH), "won")
        self.assertTrue(game.won)

    def test_hard_mode_detects_crossing_wall_between_mouse_events(self):
        game = MazeRun(hard=True)
        self.assertEqual(game.move((325, 95)), "moved")
        self.assertEqual(game.move((325, 340)), "reset")
        self.assertEqual(game.position, START)
        self.assertFalse(game.won)

    def test_marker_width_is_checked_at_corridor_edge(self):
        self.assertTrue(segment_in_corridor(START, (150, 130)))
        self.assertFalse(segment_in_corridor(START, (150, 131)))

    def test_easy_mode_allows_leaving_and_crossing_goal(self):
        game = MazeRun()
        self.assertEqual(game.move((710, 450)), "moved")
        self.assertEqual(game.move((710, 570)), "won")

    def test_resume_requires_click_near_current_position(self):
        game = MazeRun()
        game.move((200, 95))
        self.assertFalse(game.can_resume(START))
        self.assertTrue(game.can_resume((205, 95)))
        game.move(FINISH)
        self.assertFalse(game.can_resume(FINISH))


if __name__ == "__main__":
    unittest.main()
