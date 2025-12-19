Minesweeper with Automated Solver (Python, pygame-ce)

This project is a complete implementation of the game Minesweeper written in Python
using pygame-ce. In addition to standard gameplay, it includes an automated solver
capable of playing the game using logical deduction and constraint satisfaction.

Features:
- Configurable board size, difficulty, and time limit
- First-click safety (bombs are never placed on the first click or its neighbors)
- Score system based on difficulty, time, and efficiency
- Automated solver that uses:
  - Frontier-based logic
  - Pairwise constraint deduction
  - Exhaustive constraint satisfaction on connected tile groups

Rule Modification:
Unlike classic Minesweeper, the number displayed on a revealed tile is dynamically
updated based on how many neighboring bombs remain unflagged. This makes logical
deduction clearer for both the player and the automated solver.

Controls:
- Left click: reveal tile
- Right click: flag/unflag tile
- A: activate automated solver (after first click)
- C: reveal board and end the game (debug/surrender)

How to run:
1. Install dependencies:
   pip install -r requirements.txt
2. Run the game:
   python Minesweeper.py
