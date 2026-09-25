"""Backgrounds and effects. All calculated per frame from time alone."""
import math

import numpy as np

from .gfx import (BAYER_FULL, BLACK, BLUE, DKGRAY, H, LTBLUE, LTCYAN, LTGRAY,
                  LTGREEN, LTPURPLE, LTRED, RED, W, WHITE, XX, YELLOW, YY,
                  dither_ramp)

_polar = {}


def _polar_at(cx, cy):
    key = (int(cx), int(cy))
    if key not in _polar:
        dx, dy = XX - key[0], YY - key[1]
        _polar[key] = (np.arctan2(dy, dx), np.sqrt(dx * dx + dy * dy))
    return _polar[key]


def _step(t, fps):
    return math.floor(t * fps) / fps


def rays(cv, t, c1=BLUE, c2=LTBLUE, n=18, speed=0.15, cx=W / 2, cy=H / 2,
         center_glow=None, glow_r=60):
    t = _step(t, 10)
    th, r = _polar_at(cx, cy)
    k = np.floor((th / (2 * math.pi) + 0.5 + t * speed) * n).astype(np.int32)
    cv.fb[:] = np.where(k % 2 == 0, c1, c2)
    if center_glow is not None:
        lvl = np.clip(1.0 - r / glow_r, 0, 1)
        m = lvl > 0.02
        cv.fb[m] = dither_ramp(lvl[m], [c2] + list(center_glow),
                               BAYER_FULL[m])


def vgradient(cv, ramp, y0=0, y1=H, reverse=False):
    lvl = np.clip((YY[y0:y1] - y0) / max(y1 - y0 - 1, 1), 0, 1)
    if reverse:
        lvl = 1 - lvl
    cv.fb[y0:y1] = dither_ramp(lvl, ramp, BAYER_FULL[y0:y1])


def radial(cv, ramp, cx, cy, radius, y0=0, y1=H):
    th, r = _polar_at(cx, cy)
    lvl = np.clip(1 - r[y0:y1] / radius, 0, 1)
    cv.fb[y0:y1] = dither_ramp(lvl, ramp, BAYER_FULL[y0:y1])


class Stars:
    def __init__(self, n=420, seed=1):
        rng = np.random.default_rng(seed)
        self.x = rng.uniform(-1, 1, n)
        self.y = rng.uniform(-1, 1, n)
        self.z = rng.uniform(0.05, 1, n)

    def draw(self, cv, t, speed=0.12, cx=W / 2, cy=H / 2, twinkle=True):
        t = _step(t, 15)
        z = (self.z - t * speed) % 1.0 + 0.02
        sx = cx + self.x / z * 180
        sy = cy + self.y / z * 180
        col = np.where(z < 0.3, WHITE, np.where(z < 0.6, LTGRAY, DKGRAY))
        cv.plot(sx, sy, col)
        near = z < 0.18
        cv.plot(sx[near] + 1, sy[near], WHITE)
        cv.plot(sx[near], sy[near] + 1, WHITE)

    def static(self, cv, t, y1=H, seed_twinkle=0):
        t = _step(t, 5)
        sx = (self.x * 0.5 + 0.5) * W
        sy = (self.y * 0.5 + 0.5) * y1
        tw = np.sin(t * 3 + self.z * 40) > -0.3
        col = np.where(self.z < 0.2, WHITE, np.where(self.z < 0.6, LTGRAY,
                                                      DKGRAY))
        cv.plot(sx[tw], sy[tw], col[tw])


STARS = Stars()


def rain(cv, t, n=260, speed=420.0, c=LTBLUE, c2=BLUE, seed=4, length=7,
         wind=0.18, intensity=1.0):
    t = _step(t, 15)
    rng = np.random.default_rng(seed)
    x0 = rng.uniform(0, W + 80, n)
    y0 = rng.uniform(0, H, n)
    sp = rng.uniform(0.7, 1.3, n) * speed
    k = int(n * max(0.0, min(1.0, intensity)))
    y = (y0 + t * sp) % (H + 40) - 20
    x = (x0 - y * wind) % (W + 80) - 40
    for j in range(length):
        cv.plot(x[:k] - j * wind, y[:k] - j, c if j < length // 2 else c2)


def terry_flame(cv, X, Y, dt, frame, scale=1, sparkle=True):
    """The candle flame from ::/Apps/Psalmody/Examples/night.HC DrawIt,
    by Terry A. Davis. dt is in beats. Drawn only while dt<24, as his."""
    if dt >= 24:
        return
    frame //= 2
    rng = np.random.default_rng(frame * 7919 + 17)
    if sparkle and rng.random() < 0.7:
        for px, py in ((-12, 1), (-12, 2), (-11, 4), (10, 4), (4, 4),
                       (5, 4), (6, 4), (7, 5), (8, 5)):
            cv.rect(X + px * scale, Y + py * scale, scale, scale, YELLOW)
    n = 512
    x = 1.0 - rng.random(n) ** 3.0
    y = rng.random(n)
    x = 5.0 * np.sin(math.pi * np.sqrt(y)) * x
    y = 25.0 * y
    inner = rng.random(n) * (x * x + 2.0) * np.sqrt(y) < 4.0
    blue = rng.random(n) < 0.5
    col = np.where(inner, np.where(blue, BLUE, LTBLUE), YELLOW)
    flip = rng.integers(-32768, 32768, n) < 0
    x = np.where(flip, -x, x)
    x = x + 150.0 * math.sin(math.pi * dt) / (35 - y) ** 1.5
    px = (X + x * scale).astype(np.int32)
    py = (Y - y * scale).astype(np.int32)
    for dx in range(scale):
        for dy in range(scale):
            cv.plot(px + dx, py + dy, col)


def fireworks(cv, t, seed=9, rate=2.2, colors=(YELLOW, LTRED, LTCYAN,
              LTGREEN, LTPURPLE, WHITE, LTBLUE), gravity=60.0, y_max=300):
    t = _step(t, 15)
    rng = np.random.default_rng(seed)
    starts = np.cumsum(rng.uniform(0.3, 2.0 / rate, 600)) - 1.0
    for i, t0 in enumerate(starts):
        if t0 > t:
            break
        age = t - t0
        if age < 0 or age > 2.4:
            continue
        r2 = np.random.default_rng(seed * 1000 + i)
        cx = r2.uniform(60, W - 60)
        cy = r2.uniform(50, y_max)
        c = colors[i % len(colors)]
        m = 60
        a = np.linspace(0, 2 * math.pi, m, endpoint=False) + r2.uniform(0, 1)
        v = r2.uniform(70, 130) * (0.6 + 0.4 * r2.random(m))
        px = cx + np.cos(a) * v * age
        py = cy + np.sin(a) * v * age + 0.5 * gravity * age * age
        col = c if age < 1.2 else (RED if age < 1.8 else DKGRAY)
        cv.plot(px, py, col)
        cv.plot(px + 1, py, col)
        if age < 0.15:
            cv.circle(cx, cy, 6 + 40 * age, WHITE)


def glitch(cv, t, amount=8, seed=0):
    rng = np.random.default_rng(int(t * 30) + seed)
    for _ in range(6):
        y = rng.integers(0, H - 12)
        h = rng.integers(2, 12)
        s = int(rng.integers(-amount, amount + 1))
        cv.fb[y:y + h] = np.roll(cv.fb[y:y + h], s, axis=1)


def shake(cv, dx, dy):
    dx, dy = int(dx), int(dy)
    if dx or dy:
        cv.fb[:] = np.roll(np.roll(cv.fb, dy, axis=0), dx, axis=1)


def dissolve(prev, cur, level):
    """Bayer dissolve from prev to cur frame index arrays."""
    return np.where(BAYER_FULL < level, cur, prev)


def plasma(cv, t, ramp, scale=0.035, y0=0, y1=H):
    t = _step(t, 8)
    x = XX[y0:y1] * scale
    y = YY[y0:y1] * scale
    v = (np.sin(x + t) + np.sin(y * 1.3 - t * 0.7) +
         np.sin((x + y) * 0.7 + t * 0.5) + np.sin(np.sqrt(x * x + y * y) - t))
    lvl = (v + 4) / 8
    cv.fb[y0:y1] = dither_ramp(lvl, ramp, BAYER_FULL[y0:y1])


def scanline_wipe(cv, t, dur, c=BLACK):
    """A curtain of rows closing in from top and bottom."""
    k = int(min(max(t / dur, 0), 1) * H / 2)
    if k:
        cv.fb[:k] = c
        cv.fb[H - k:] = c
