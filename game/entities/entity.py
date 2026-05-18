"""Abstract base class for every drawable, updatable game object."""
from abc import ABC, abstractmethod
import pygame as pg


class Entity(ABC):
    """Polymorphic base type used by GameController for update/draw dispatch.

    Encapsulates position and an alive flag. Concrete entities expose a
    bounding rect and implement their own update/draw behaviour.
    """

    def __init__(self, x: float, y: float) -> None:
        self._x = float(x)
        self._y = float(y)
        self._alive = True

    @property
    def x(self) -> float:
        return self._x

    @property
    def y(self) -> float:
        return self._y

    @property
    def pos(self) -> tuple[float, float]:
        return self._x, self._y

    def alive(self) -> bool:
        return self._alive

    def kill(self) -> None:
        self._alive = False

    @property
    @abstractmethod
    def rect(self) -> pg.Rect: ...

    @abstractmethod
    def update(self, dt: float, ctx) -> None: ...

    @abstractmethod
    def draw(self, surface: pg.Surface) -> None: ...
