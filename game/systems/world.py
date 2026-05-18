"""Entity registry: owns all dynamic game-object collections for one round."""


class World:
    """Owns the six entity lists that GameController used to own directly.

    Walls are set once per round via :meth:`set_walls`.
    All other lists are cleared at the start of each round via :meth:`clear`.
    Properties return the actual lists so callers can mutate them in place
    (iterate-and-remove pattern used by the update loop).
    """

    def __init__(self) -> None:
        self._shots: list = []
        self._mines: list = []
        self._particles: list = []
        self._debris: list = []
        self._shockwaves: list = []
        self._walls: list = []

    # ---- walls (replaced once per round) --------------------------------
    def set_walls(self, walls: list) -> None:
        self._walls = walls

    @property
    def walls(self) -> list:
        return self._walls

    # ---- mutable entity lists -------------------------------------------
    @property
    def shots(self) -> list:
        return self._shots

    @property
    def mines(self) -> list:
        return self._mines

    @property
    def particles(self) -> list:
        return self._particles

    @property
    def debris(self) -> list:
        return self._debris

    @property
    def shockwaves(self) -> list:
        return self._shockwaves

    # ---- add helpers ----------------------------------------------------
    def add_shot(self, s) -> None:
        self._shots.append(s)

    def add_mine(self, m) -> None:
        self._mines.append(m)

    def add_particle(self, p) -> None:
        self._particles.append(p)

    def add_debris(self, d) -> None:
        self._debris.append(d)

    def add_shockwave(self, w) -> None:
        self._shockwaves.append(w)

    # ---- round lifecycle ------------------------------------------------
    def clear(self) -> None:
        """Discard all dynamic entities; walls are not affected."""
        self._shots = []
        self._mines = []
        self._particles = []
        self._debris = []
        self._shockwaves = []
