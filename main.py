"""Entry point for the Tankons tank battle game.

Usage:
    python3 main.py        # local 2-player hot-seat
"""
from game.game_controller import GameController


def main() -> None:
    GameController().run()


if __name__ == "__main__":
    main()
