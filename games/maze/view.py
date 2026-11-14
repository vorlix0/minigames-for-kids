import tkinter as tk

from .logic import (
    CORRIDOR_HALF_WIDTH,
    FINISH,
    GOAL_RADIUS,
    MARKER_RADIUS,
    START,
    MazeRun,
    corridor_rectangles,
)


COLORS = {
    "Czerwony": "#e53935",
    "Niebieski": "#1e88e5",
    "Zielony": "#43a047",
    "Fioletowy": "#8e24aa",
    "Pomarańczowy": "#fb8c00",
}


class MazeGame(tk.Frame):
    def __init__(self, parent, on_back):
        super().__init__(parent)
        self.color = tk.StringVar(value="Niebieski")
        self.difficulty = tk.StringVar(value="easy")
        self.message = tk.StringVar()
        self.run = MazeRun()
        self.dragging = False

        controls = tk.Frame(self)
        controls.pack(fill="x", pady=(0, 8))
        tk.Button(controls, text="← Menu", command=on_back).pack(side="left")
        tk.Label(controls, text="Kolor mazaka:").pack(side="left", padx=(15, 3))
        tk.OptionMenu(controls, self.color, *COLORS).pack(side="left")
        tk.Label(controls, text="Poziom:").pack(side="left", padx=(15, 3))
        tk.Radiobutton(
            controls, text="Łatwy", variable=self.difficulty, value="easy",
            command=self.restart,
        ).pack(side="left")
        tk.Radiobutton(
            controls, text="Trudny", variable=self.difficulty, value="hard",
            command=self.restart,
        ).pack(side="left")
        tk.Button(controls, text="Od nowa", command=self.restart).pack(
            side="right"
        )

        self.canvas = tk.Canvas(
            self, width=800, height=610, bg="#55738a", highlightthickness=0
        )
        self.canvas.pack()
        tk.Label(self, textvariable=self.message, font=("Arial", 12)).pack(
            pady=(8, 0)
        )
        self.canvas.bind("<ButtonPress-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        self.restart()

    def restart(self):
        self.run = MazeRun(hard=self.difficulty.get() == "hard")
        self.dragging = False
        self.canvas.delete("all")
        for rectangle in corridor_rectangles():
            self.canvas.create_rectangle(
                *rectangle, fill="#fff9dc", outline="#fff9dc"
            )
        self.canvas.create_oval(
            START[0] - 25, START[1] - 25, START[0] + 25, START[1] + 25,
            fill="#a5d6a7", outline="",
        )
        self.canvas.create_text(*START, text="START", font=("Arial", 10, "bold"))
        self.canvas.create_rectangle(
            FINISH[0] - GOAL_RADIUS, FINISH[1] - GOAL_RADIUS,
            FINISH[0] + GOAL_RADIUS, FINISH[1] + GOAL_RADIUS,
            fill="#ffcc80", outline="",
        )
        self.canvas.create_text(
            FINISH[0], FINISH[1] - CORRIDOR_HALF_WIDTH - 10,
            text="META", fill="white", font=("Arial", 11, "bold"),
        )
        self.show_marker()
        self.message.set("Kliknij mazak na starcie i prowadź go do mety.")

    def show_marker(self):
        self.canvas.delete("marker")
        x, y = self.run.position
        self.canvas.create_oval(
            x - MARKER_RADIUS, y - MARKER_RADIUS,
            x + MARKER_RADIUS, y + MARKER_RADIUS,
            fill=COLORS[self.color.get()], outline="", tags="marker",
        )

    def start_drawing(self, event):
        if self.run.can_resume((event.x, event.y)):
            self.dragging = True
            self.move_to(event.x, event.y)

    def draw(self, event):
        if self.dragging:
            self.move_to(event.x, event.y)

    def stop_drawing(self, event):
        if self.dragging:
            self.move_to(event.x, event.y)
        self.dragging = False

    def move_to(self, x, y):
        previous = self.run.position
        result = self.run.move((x, y))
        if result == "reset":
            self.restart()
            self.message.set("Ups! Mazak wyszedł poza ścieżkę. Spróbuj jeszcze raz!")
            return
        self.canvas.create_line(
            *previous, *self.run.position, fill=COLORS[self.color.get()],
            width=MARKER_RADIUS * 2, capstyle="round", tags="trace",
        )
        self.show_marker()
        if result == "won":
            self.dragging = False
            self.message.set("Brawo! Udało Ci się dotrzeć do mety!")
