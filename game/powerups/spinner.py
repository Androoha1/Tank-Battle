"""Spinner effect — debuff applied to OTHER players: forces them to auto-rotate."""
from .effect import PlayerEffect


class SpinnerEffect(PlayerEffect):
    NAME = "Spinner"
    COLOR = (255, 80, 230)
    ICON = "O"
    DURATION_MS = 4000

    @classmethod
    def dispatch(cls, picker, ctx) -> None:
        for other in ctx.players:
            if other is picker or not other.alive():
                continue
            other.add_effect(cls())

    def rotation_per_tick(self) -> float:
        return 6.0
