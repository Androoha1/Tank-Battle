"""Procedural sound effects + ambient music. No asset files.

Builds short PCM buffers at startup with numpy, wraps them as pygame Sound
objects, and exposes simple play_* methods. Silently no-ops if the audio
device cannot be opened (e.g. headless test environments).
"""
import numpy as np
import pygame as pg


RATE = 22050


def _to_sound(mono: np.ndarray) -> pg.mixer.Sound:
    """Convert a mono float array (-1..1) into a stereo pygame Sound."""
    mono = np.clip(mono, -1.0, 1.0)
    pcm = (mono * 32767).astype(np.int16)
    stereo = np.column_stack((pcm, pcm)).copy(order="C")
    return pg.sndarray.make_sound(stereo)


def _shoot() -> pg.mixer.Sound:
    dur = 0.10
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(950, 230, n)
    phase = np.cumsum(2 * np.pi * freq / RATE)
    tone = np.sin(phase)
    noise = np.random.uniform(-0.4, 0.4, n)
    env = np.exp(-t * 18)
    return _to_sound((tone * 0.6 + noise * 0.4) * env * 0.55)


def _big_shoot() -> pg.mixer.Sound:
    dur = 0.25
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(180, 60, n)
    phase = np.cumsum(2 * np.pi * freq / RATE)
    tone = np.sin(phase)
    noise = np.random.uniform(-0.5, 0.5, n)
    env = np.exp(-t * 6)
    return _to_sound((tone * 0.7 + noise * 0.3) * env * 0.75)


def _mine_drop() -> pg.mixer.Sound:
    dur = 0.18
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(440, 180, n)
    phase = np.cumsum(2 * np.pi * freq / RATE)
    tone = np.sin(phase)
    env = np.exp(-t * 9)
    return _to_sound(tone * env * 0.45)


def _explosion() -> pg.mixer.Sound:
    dur = 0.7
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    # Low rumble + filtered noise.
    rumble = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 3)
    rumble += np.sin(2 * np.pi * 85 * t) * np.exp(-t * 4) * 0.7
    noise = np.random.uniform(-1.0, 1.0, n)
    # crude low-pass via cumulative average smoothing
    kernel = 9
    noise_lp = np.convolve(noise, np.ones(kernel) / kernel, mode="same")
    env = np.exp(-t * 4.5)
    out = (rumble * 0.6 + noise_lp * 0.7) * env * 0.8
    return _to_sound(out)


def _pickup() -> pg.mixer.Sound:
    dur = 0.28
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    freq = np.linspace(680, 1320, n)
    phase = np.cumsum(2 * np.pi * freq / RATE)
    tone = np.sin(phase) + 0.4 * np.sin(2 * phase)  # second harmonic
    env = np.where(t < 0.04, t / 0.04, np.exp(-(t - 0.04) * 5.5))
    return _to_sound(tone * env * 0.4)


def _shield_block() -> pg.mixer.Sound:
    dur = 0.35
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    f1 = 880
    tone = np.sin(2 * np.pi * f1 * t) + 0.5 * np.sin(2 * np.pi * f1 * 1.5 * t)
    env = np.exp(-t * 7)
    return _to_sound(tone * env * 0.55)


def _ambient_loop() -> pg.mixer.Sound:
    """8s seamless drone loop."""
    dur = 8.0
    n = int(RATE * dur)
    t = np.linspace(0, dur, n, endpoint=False)
    base = 55.0  # A1
    s1 = np.sin(2 * np.pi * base * t)
    s2 = np.sin(2 * np.pi * base * 1.5 * t) * 0.6     # E2
    s3 = np.sin(2 * np.pi * base * 2.005 * t) * 0.45  # A2 slightly detuned
    s4 = np.sin(2 * np.pi * base * 3.0 * t) * 0.25    # E3
    # Slow swell envelope so the loop end meets the start.
    swell = 0.5 + 0.5 * np.sin(2 * np.pi * (1.0 / dur) * t)
    sig = (s1 + s2 + s3 + s4) * 0.06 * swell
    return _to_sound(sig)


class SoundLibrary:
    """Lazy, fail-safe sound library; play_* methods are no-ops if disabled."""

    def __init__(self) -> None:
        self._enabled = False
        try:
            pg.mixer.pre_init(frequency=RATE, size=-16, channels=2, buffer=512)
            pg.mixer.init()
            self._shoot = _shoot()
            self._big = _big_shoot()
            self._mine = _mine_drop()
            self._explosion = _explosion()
            self._pickup = _pickup()
            self._shield = _shield_block()
            self._ambient = _ambient_loop()
            for s in (self._shoot, self._big, self._mine,
                      self._pickup, self._shield):
                s.set_volume(0.55)
            self._explosion.set_volume(0.65)
            self._ambient.set_volume(0.35)
            self._enabled = True
            self._ambient_channel: pg.mixer.Channel | None = None
        except Exception:
            self._enabled = False

    # --- public API ----
    @property
    def enabled(self) -> bool:
        return self._enabled

    def play_shoot(self, kind: str | None = None) -> None:
        if not self._enabled:
            return
        if kind == "big":
            self._big.play()
        elif kind == "mine":
            self._mine.play()
        else:
            self._shoot.play()

    def play_explosion(self) -> None:
        if not self._enabled:
            return
        self._explosion.play()

    def play_pickup(self) -> None:
        if not self._enabled:
            return
        self._pickup.play()

    def play_shield(self) -> None:
        if not self._enabled:
            return
        self._shield.play()

    def start_ambient(self) -> None:
        if not self._enabled or self._ambient_channel is not None:
            return
        self._ambient_channel = self._ambient.play(loops=-1, fade_ms=1500)

    def stop_ambient(self) -> None:
        if not self._enabled or self._ambient_channel is None:
            return
        self._ambient_channel.fadeout(800)
        self._ambient_channel = None
