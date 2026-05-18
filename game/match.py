"""Domain object representing a single match (a series of rounds with scoring)."""


class Match:
    def __init__(self, win_target: int) -> None:
        self._win_target = win_target
        self._round_num: int = 0
        self._scores: dict = {}
        self._round_winner = None
        self._match_winner = None

    def register_players(self, players: list) -> None:
        for p in players:
            if p not in self._scores:
                self._scores[p] = 0

    def start_round(self) -> None:
        self._round_num += 1
        self._round_winner = None

    def award_round_winner(self, winner) -> None:
        self._round_winner = winner
        if winner is not None:
            self._scores[winner] = self._scores.get(winner, 0) + 1
            if self._win_target > 0 and self._scores[winner] >= self._win_target:
                self._match_winner = winner

    def is_complete(self) -> bool:
        return self._match_winner is not None

    def score_of(self, player) -> int:
        return self._scores.get(player, 0)

    @property
    def round_num(self) -> int:
        return self._round_num

    @property
    def round_winner(self):
        return self._round_winner

    @property
    def match_winner(self):
        return self._match_winner
