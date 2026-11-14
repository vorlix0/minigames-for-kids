# Minigames for Kids

A collection of simple minigames written in Python. The first game is a maze.

## Getting Started

Python 3.8 or newer with Tkinter is required. From the project directory, run:

```powershell
py main.py
```

On systems where Python is available as `python3`, you can run
`python3 main.py`. Tkinter is usually included with Python; some Linux
distributions require installing it separately.

## Maze

Choose a marker color and difficulty, then click the marker at the start and
guide it to the goal while holding the left mouse button. After releasing the
button, you can continue from the end of the drawn path.

- **Easy:** the marker can leave the path.
- **Hard:** leaving the path clears the drawing and returns the marker to the start.

The **Restart** button starts a new game. Changing the difficulty also starts a
new game. The **Menu** button returns to the minigame selection screen.

## Extending and Testing

Each game has its own directory in `games`; new games can be added to the menu
in `main.py`. The maze logic is separate from the Tkinter interface.

```powershell
py -m unittest discover
```
