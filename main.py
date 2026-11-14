import tkinter as tk

from games.maze.view import MazeGame


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Minigames for Kids")
        self.root.resizable(False, False)
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
            command=self.show_maze,
        ).pack()

    def show_maze(self) -> None:
        self.current_screen.destroy()
        self.current_screen = MazeGame(self.root, self.show_menu)
        self.current_screen.pack(padx=12, pady=12)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
