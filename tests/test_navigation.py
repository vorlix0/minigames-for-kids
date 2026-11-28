import tkinter as tk
import unittest

from main import App
from games.maze.view import MazeGame


class NavigationTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(f"Tk display unavailable: {error}")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = App(self.root)

    def button(self, text):
        def find(widget):
            for child in widget.winfo_children():
                if isinstance(child, tk.Button) and child.cget("text") == text:
                    return child
                result = find(child)
                if result is not None:
                    return result
            return None

        result = find(self.app.current_screen)
        self.assertIsNotNone(result, text)
        return result

    def test_menu_options_game_and_back(self):
        self.button("Maze").invoke()
        self.assertIsNotNone(self.button("Start"))
        self.app.maze_theme.set("Unicorn")
        self.app.maze_color.set("Red")
        self.button("Start").invoke()
        game = self.app.current_screen
        self.assertIsInstance(game, MazeGame)
        self.assertEqual(game.theme_name.get(), "Unicorn")
        self.assertEqual(game.color.get(), "Red")
        game.start_move((1, 0))
        self.button("← Options").invoke()
        self.assertIsNone(game.move_job)
        self.assertEqual(self.app.maze_theme.get(), "Unicorn")
        self.assertEqual(self.app.maze_color.get(), "Red")
        self.button("Back").invoke()
        self.assertIsNotNone(self.button("Maze"))


if __name__ == "__main__":
    unittest.main()
