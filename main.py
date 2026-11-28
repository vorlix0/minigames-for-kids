import tkinter as tk

from games.maze.view import MazeGame
from games.maze.themes import COLORS, THEMES


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Minigames for Kids")
        self.root.resizable(False, False)
        self.maze_theme = tk.StringVar(value="Space")
        self.maze_color = tk.StringVar(value="Blue")
        self.current_screen = None
        self.show_menu()

    def show_menu(self) -> None:
        if self.current_screen is not None:
            self.current_screen.destroy()
        self.current_screen = tk.Frame(self.root, padx=50, pady=50)
        self.current_screen.pack()
        tk.Label(
            self.current_screen, text="Minigames for Kids", font=("Arial", 24, "bold")
        ).pack(pady=(0, 25))
        tk.Button(
            self.current_screen,
            text="Maze",
            font=("Arial", 18),
            width=18,
            command=self.show_maze_options,
        ).pack()

    def show_maze_options(self) -> None:
        self.current_screen.destroy()
        self.current_screen = tk.Frame(self.root, padx=50, pady=50)
        self.current_screen.pack()
        tk.Label(
            self.current_screen, text="Maze", font=("Arial", 24, "bold")
        ).pack(pady=(0, 25))
        options = tk.Frame(self.current_screen)
        options.pack(pady=(0, 25))
        tk.Label(options, text="Theme:").grid(row=0, column=0, padx=8, pady=6)
        tk.OptionMenu(options, self.maze_theme, *THEMES).grid(row=0, column=1)
        tk.Label(options, text="Color:").grid(row=1, column=0, padx=8, pady=6)
        tk.OptionMenu(options, self.maze_color, *COLORS).grid(row=1, column=1)
        tk.Button(
            self.current_screen, text="Start", font=("Arial", 18), width=18,
            command=self.show_maze,
        ).pack(pady=(0, 10))
        tk.Button(self.current_screen, text="Back", command=self.show_menu).pack()

    def show_maze(self) -> None:
        self.current_screen.destroy()
        self.current_screen = MazeGame(
            self.root, self.show_maze_options,
            theme=self.maze_theme.get(), color=self.maze_color.get(),
        )
        self.current_screen.pack(padx=12, pady=12, fill="both", expand=True)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
