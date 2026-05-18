"""Entry point for the Tankons tank battle game.

Usage:
    python3 main.py            # 2 players (local)
    python3 main.py 3          # 3 players (P1 WASD, P2 arrows, P3 IJKL)
    python3 main.py 4          # 4 players (adds numpad)
"""
import sys

from game.game_controller import GameController


def main() -> None:
    num_players = 2
    if len(sys.argv) > 1:
        try:
            num_players = max(2, min(4, int(sys.argv[1])))
        except ValueError:
            pass
    GameController(num_players=num_players).run()


if __name__ == "__main__":
    main()
