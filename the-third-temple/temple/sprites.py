"""Characters and props, drawn with primitives every frame."""
import math

import numpy as np

from .gfx import (BAYER_FULL, BLACK, BLUE, BROWN, DKGRAY, GREEN, H, LTBLUE,
                  LTCYAN, LTGRAY, LTGREEN, LTRED, PURPLE, RED, W, WHITE,
                  YELLOW, dither_ramp, poly_mask)


def elephant(cv, x, y, s=1.0, t=0.0, c=LTGRAY, o=DKGRAY, facing=1):
    """God's favorite animal (::/Adam/God/HSNotes.DD). x,y = feet center."""
    f = facing
    ph = t * 4.0
    with cv.pil() as d:
        for i, lx in enumerate((-26, -14, 10, 22)):
            sw = math.sin(ph + (i % 2) * math.pi) * 5 * s
            X = x + lx * s * f + sw * f
            d.rectangle([X - 5 * s, y - 26 * s, X + 5 * s, y], fill=c,
                        outline=o)
            d.rectangle([X - 5 * s, y - 3 * s, X + 5 * s, y], fill=o)
        d.ellipse([x - 38 * s, y - 62 * s, x + 34 * s, y - 18 * s], fill=c,
                  outline=o, width=max(1, int(s)))
        hx = x + 34 * s * f
        d.ellipse([hx - 18 * s, y - 70 * s, hx + 18 * s, y - 36 * s],
                  fill=c, outline=o, width=max(1, int(s)))
        ex = hx - 12 * s * f
        d.ellipse([ex - 14 * s, y - 72 * s, ex + 10 * s, y - 38 * s],
                  fill=c, outline=o)
        sw = math.sin(t * 2.2) * 6
        pts = []
        for k in range(12):
            u = k / 11
            pts.append((hx + (14 + 6 * u) * s * f + sw * u * u * s * f,
                        y - 48 * s + u * 40 * s))
        d.line(pts, fill=o, width=int(9 * s))
        d.line(pts, fill=c, width=int(7 * s))
        d.ellipse([hx + 5 * s * f - 2 * s, y - 60 * s, hx + 5 * s * f + 2 * s,
                   y - 56 * s], fill=BLACK)
        tx = x - 37 * s * f
        d.line([(tx, y - 50 * s), (tx - 8 * s * f,
                y - 34 * s + math.sin(t * 5) * 3 * s)], fill=o,
               width=max(1, int(2 * s)))


def bear(cv, x, y, s=1.0, t=0.0, c=BROWN, o=BLACK):
    with cv.pil() as d:
        d.ellipse([x - 30 * s, y - 50 * s, x + 30 * s, y], fill=c, outline=o)
        d.ellipse([x - 22 * s, y - 86 * s, x + 22 * s, y - 44 * s], fill=c,
                  outline=o)
        for ex in (-18, 18):
            d.ellipse([x + (ex - 8) * s, y - 92 * s, x + (ex + 8) * s,
                       y - 76 * s], fill=c, outline=o)
        d.ellipse([x - 10 * s, y - 64 * s, x + 10 * s, y - 50 * s],
                  fill=YELLOW, outline=o)
        d.ellipse([x - 3 * s, y - 62 * s, x + 3 * s, y - 57 * s], fill=BLACK)
        for ex in (-9, 9):
            d.ellipse([x + (ex - 3) * s, y - 74 * s, x + (ex + 3) * s,
                       y - 68 * s], fill=BLACK)
        wave = math.sin(t * 6) * 10
        d.line([(x + 26 * s, y - 36 * s), (x + 44 * s, y - 60 * s - wave * s)],
               fill=c, width=int(10 * s))


def bat(cv, x, y, s=1.0, t=0.0, c=PURPLE, o=BLACK):
    flap = math.sin(t * 14)
    with cv.pil() as d:
        for sgn in (-1, 1):
            tip_y = y - 16 * s * flap
            pts = [(x, y - 4 * s), (x + sgn * 16 * s, tip_y - 6 * s),
                   (x + sgn * 30 * s, tip_y), (x + sgn * 22 * s, y + 4 * s),
                   (x + sgn * 12 * s, y + 2 * s), (x + sgn * 6 * s, y + 6 * s)]
            d.polygon(pts, fill=c, outline=o)
        d.ellipse([x - 7 * s, y - 8 * s, x + 7 * s, y + 8 * s], fill=c,
                  outline=o)
        d.polygon([(x - 6 * s, y - 6 * s), (x - 3 * s, y - 14 * s),
                   (x - 1 * s, y - 6 * s)], fill=c)
        d.polygon([(x + 6 * s, y - 6 * s), (x + 3 * s, y - 14 * s),
                   (x + 1 * s, y - 6 * s)], fill=c)
        for ex in (-3, 3):
            d.rectangle([x + ex * s - s, y - 3 * s, x + ex * s + s,
                         y - 1 * s], fill=YELLOW)


def bird(cv, x, y, s=1.0, t=0.0, c=BROWN, o=BLACK, fish=False):
    flap = math.sin(t * 7)
    with cv.pil() as d:
        for sgn in (-1, 1):
            d.polygon([(x - 6 * s * sgn, y), (x + sgn * 34 * s,
                        y - 22 * s * flap - 4 * s), (x + sgn * 20 * s,
                        y + 6 * s)], fill=c, outline=o)
        d.ellipse([x - 12 * s, y - 7 * s, x + 12 * s, y + 7 * s], fill=c,
                  outline=o)
        d.ellipse([x + 8 * s, y - 12 * s, x + 20 * s, y], fill=WHITE,
                  outline=o)
        d.polygon([(x + 19 * s, y - 7 * s), (x + 27 * s, y - 4 * s),
                   (x + 19 * s, y - 3 * s)], fill=YELLOW)
        d.line([(x - 2 * s, y + 6 * s), (x - 4 * s, y + 14 * s)], fill=YELLOW,
               width=max(1, int(2 * s)))
        d.line([(x + 4 * s, y + 6 * s), (x + 6 * s, y + 14 * s)], fill=YELLOW,
               width=max(1, int(2 * s)))
    if fish:
        fishy(cv, x + 1 * s, y + 20 * s, s * 0.8, t)


def fishy(cv, x, y, s=1.0, t=0.0, c=LTCYAN, o=BLUE):
    wig = math.sin(t * 10) * 3 * s
    with cv.pil() as d:
        d.ellipse([x - 12 * s, y - 5 * s, x + 12 * s, y + 5 * s], fill=c,
                  outline=o)
        d.polygon([(x - 10 * s, y), (x - 20 * s, y - 7 * s + wig),
                   (x - 20 * s, y + 7 * s + wig)], fill=c, outline=o)
        d.rectangle([x + 6 * s, y - 2 * s, x + 7 * s, y - 1 * s], fill=BLACK)


def sheep(cv, x, y, s=1.0, t=0.0):
    bob = abs(math.sin(t * 5)) * 2 * s
    with cv.pil() as d:
        for lx in (-10, -3, 5, 11):
            d.rectangle([x + lx * s, y - 10 * s, x + (lx + 3) * s, y],
                        fill=BLACK)
        for bx, by, r in ((-8, -18, 9), (0, -21, 10), (8, -18, 9),
                          (-2, -13, 10), (6, -12, 8)):
            d.ellipse([x + (bx - r) * s, y + (by - r) * s - bob,
                       x + (bx + r) * s, y + (by + r) * s - bob], fill=WHITE,
                      outline=LTGRAY)
        d.ellipse([x + 12 * s, y - 26 * s - bob, x + 24 * s, y - 14 * s - bob],
                  fill=DKGRAY)
        d.rectangle([x + 19 * s, y - 23 * s - bob, x + 20 * s,
                     y - 22 * s - bob], fill=WHITE)


def stick(cv, x, y, s=1.0, t=0.0, c=BLACK, walk=True, staff=False,
          robe=None, arms_up=0.0):
    """TempleOS-style stick figure. x,y = feet."""
    ph = t * 6 if walk else 0.0
    L1 = math.sin(ph) * 0.5
    with cv.pil() as d:
        hip = (x, y - 22 * s)
        neck = (x, y - 42 * s)
        for sgn in (1, -1):
            a = L1 * sgn
            knee = (x + math.sin(a) * 11 * s, y - 11 * s)
            d.line([hip, knee, (x + math.sin(a) * 16 * s, y)], fill=c,
                   width=max(1, int(2 * s)))
        if robe is not None:
            d.polygon([(x - 9 * s, y - 8 * s), (x + 9 * s, y - 8 * s),
                       (x + 4 * s, y - 42 * s), (x - 4 * s, y - 42 * s)],
                      fill=robe)
        d.line([hip, neck], fill=c, width=max(1, int(2 * s)))
        for sgn in (1, -1):
            a = -L1 * sgn * 0.8 - arms_up * sgn * 1.2
            d.line([neck, (x + math.sin(a) * 14 * s * sgn + sgn * 3 * s,
                           y - 42 * s + math.cos(a) * 14 * s)], fill=c,
                   width=max(1, int(2 * s)))
        d.ellipse([x - 6 * s, y - 55 * s, x + 6 * s, y - 43 * s], fill=c)
        if staff:
            d.line([(x + 12 * s, y), (x + 12 * s, y - 60 * s)], fill=BROWN,
                   width=max(1, int(2 * s)))
            d.arc([x + 6 * s, y - 66 * s, x + 18 * s, y - 54 * s], 180, 360,
                  fill=BROWN, width=max(1, int(2 * s)))


def kid(cv, x, y, s=1.0, c=BLUE, head=YELLOW, t=0.0, jump=0.0):
    yy = y - abs(math.sin(t * 6)) * jump * s
    with cv.pil() as d:
        d.rectangle([x - 6 * s, yy - 22 * s, x + 6 * s, yy - 8 * s], fill=c)
        d.rectangle([x - 5 * s, yy - 8 * s, x - 2 * s, yy], fill=DKGRAY)
        d.rectangle([x + 2 * s, yy - 8 * s, x + 5 * s, yy], fill=DKGRAY)
        d.ellipse([x - 6 * s, yy - 34 * s, x + 6 * s, yy - 22 * s], fill=head)


def house(cv, x, y, s=1.0, c=RED, roof=BROWN):
    with cv.pil() as d:
        d.rectangle([x - 40 * s, y - 50 * s, x + 40 * s, y], fill=c,
                    outline=BLACK)
        d.polygon([(x - 48 * s, y - 50 * s), (x, y - 86 * s),
                   (x + 48 * s, y - 50 * s)], fill=roof, outline=BLACK)
        d.rectangle([x - 8 * s, y - 28 * s, x + 8 * s, y], fill=BROWN,
                    outline=BLACK)
        for wx in (-26, 26):
            d.rectangle([x + (wx - 8) * s, y - 40 * s, x + (wx + 8) * s,
                         y - 26 * s], fill=YELLOW, outline=BLACK)


def apple2(cv, x, y, s=1.0, t=0.0):
    """A beige 1977 home computer with a green screen. x,y = base center."""
    with cv.pil() as d:
        d.rectangle([x - 60 * s, y - 30 * s, x + 60 * s, y], fill=LTGRAY,
                    outline=BLACK)
        d.polygon([(x - 60 * s, y - 30 * s), (x + 60 * s, y - 30 * s),
                   (x + 52 * s, y - 42 * s), (x - 52 * s, y - 42 * s)],
                  fill=WHITE, outline=BLACK)
        for r in range(3):
            for k in range(11):
                kx = x - 46 * s + k * 8.5 * s + r * 3 * s
                ky = y - 26 * s + r * 7 * s
                d.rectangle([kx, ky, kx + 6 * s, ky + 5 * s], fill=DKGRAY)
        d.rectangle([x - 48 * s, y - 112 * s, x + 48 * s, y - 44 * s],
                    fill=LTGRAY, outline=BLACK)
        d.rectangle([x - 40 * s, y - 106 * s, x + 40 * s, y - 52 * s],
                    fill=BLACK)
    cv.text(x - 36 * s, y - 100 * s, "]", LTGREEN, scale=max(1, int(s)))
    if (t * 2) % 1 < 0.6:
        cv.rect(x - 28 * s, y - 100 * s, 7 * s, 8 * s, LTGREEN)


def vax(cv, x, y, s=1.0, t=0.0):
    """A row of 1980s minicomputer cabinets with blinkenlights."""
    rng = np.random.default_rng(int(t * 8))
    with cv.pil() as d:
        for k in range(3):
            cx = x + (k - 1) * 70 * s
            d.rectangle([cx - 32 * s, y - 180 * s, cx + 32 * s, y],
                        fill=LTGRAY, outline=BLACK)
            d.rectangle([cx - 28 * s, y - 172 * s, cx + 28 * s,
                         y - 150 * s], fill=BLUE, outline=BLACK)
            if k == 1:
                for rx in (-14, 14):
                    d.ellipse([cx + (rx - 11) * s, y - 128 * s,
                               cx + (rx + 11) * s, y - 106 * s], fill=DKGRAY,
                              outline=BLACK)
                    a = t * (3 if rx < 0 else -3)
                    d.line([(cx + rx * s, y - 117 * s),
                            (cx + rx * s + math.cos(a) * 9 * s,
                             y - 117 * s + math.sin(a) * 9 * s)], fill=WHITE)
            else:
                for row in range(6):
                    d.rectangle([cx - 26 * s, y - (140 - row * 16) * s,
                                 cx + 26 * s, y - (130 - row * 16) * s],
                                fill=DKGRAY)
    for k in range(3):
        cx = x + (k - 1) * 70 * s
        for i in range(10):
            on = rng.random() < 0.5
            cv.rect(cx - 25 * s + i * 5 * s, y - 166 * s, 3 * s, 3 * s,
                    LTRED if on else RED)
            on = rng.random() < 0.4
            cv.rect(cx - 25 * s + i * 5 * s, y - 158 * s, 3 * s, 3 * s,
                    YELLOW if on else BROWN)
    cv.text(x - 32 * s + 4, y - 196 * s, "VAX", BLACK, scale=max(1, int(s)))


def ticket(cv, x, y, s=1.0, t=0.0, angle=0.0, c=YELLOW):
    ca, sa = math.cos(angle), math.sin(angle)
    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    with cv.pil() as d:
        d.polygon([P(-40, -18), P(40, -18), P(40, 18), P(-40, 18)], fill=c,
                  outline=BROWN)
        d.line([P(18, -18), P(18, 18)], fill=BROWN)
        for k in range(-3, 4):
            d.line([P(-32, k * 4), P(10, k * 4)], fill=BROWN if k % 2 else RED)


def gradcap(cv, x, y, s=1.0):
    with cv.pil() as d:
        d.polygon([(x - 40 * s, y), (x, y - 16 * s), (x + 40 * s, y),
                   (x, y + 16 * s)], fill=BLACK, outline=DKGRAY)
        d.rectangle([x - 18 * s, y + 4 * s, x + 18 * s, y + 18 * s],
                    fill=BLACK)
        d.line([(x, y), (x + 30 * s, y + 6 * s), (x + 30 * s, y + 26 * s)],
               fill=YELLOW, width=max(1, int(2 * s)))


def kayak(cv, x, y, s=1.0, t=0.0):
    bob = math.sin(t * 2) * 3 * s
    with cv.pil() as d:
        d.polygon([(x - 60 * s, y + bob), (x + 60 * s, y + bob),
                   (x + 40 * s, y + 10 * s + bob), (x - 40 * s,
                                                    y + 10 * s + bob)],
                  fill=LTRED, outline=BLACK)
    stick(cv, x, y + bob - 2 * s, 0.55 * s, t, c=BLACK, walk=False)
    a = math.sin(t * 3) * 0.6
    with cv.pil() as d:
        d.line([(x - 34 * s * math.cos(a), y - 24 * s + bob - 20 * s *
                 math.sin(a)), (x + 34 * s * math.cos(a), y - 24 * s + bob +
                                20 * s * math.sin(a))], fill=BROWN,
               width=max(1, int(2 * s)))


def titanic(cv, x, y, s=1.0, t=0.0, sink=0.0):
    tilt = sink * 0.5
    ca, sa = math.cos(tilt), math.sin(tilt)
    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + sink * 60 * s +
                (px * sa + py * ca) * s)
    with cv.pil() as d:
        d.polygon([P(-110, -10), P(110, -10), P(90, 22), P(-96, 22)],
                  fill=BLACK, outline=DKGRAY)
        d.polygon([P(-100, -10), P(100, -10), P(100, -26), P(-100, -26)],
                  fill=WHITE, outline=DKGRAY)
        for k, fxp in enumerate((-50, -15, 20, 55)):
            d.polygon([P(fxp - 8, -26), P(fxp + 8, -26), P(fxp + 10, -58),
                       P(fxp - 6, -58)], fill=YELLOW if k < 4 else BROWN,
                      outline=BLACK)
            d.polygon([P(fxp - 6, -58), P(fxp + 10, -58), P(fxp + 10, -48),
                       P(fxp - 6, -48)], fill=BLACK)
        d.polygon([P(-90, 22), P(90, 22), P(80, 26), P(-80, 26)], fill=RED)


def water(cv, y, t, c1=BLUE, c2=LTBLUE):
    cv.rect(0, y, W, H - y, c1)
    for k in range(0, W, 16):
        yy = y + 3 * math.sin(t * 2 + k * 0.08)
        cv.line(k, yy, k + 10, yy, c2)


def mouse3(cv, x, y, s=1.0):
    with cv.pil() as d:
        d.rounded_rectangle([x - 26 * s, y - 40 * s, x + 26 * s, y + 40 * s],
                            radius=int(22 * s), fill=LTGRAY, outline=BLACK,
                            width=2)
        for k in (-1, 0, 1):
            d.rectangle([x + (k * 16 - 7) * s, y - 34 * s,
                         x + (k * 16 + 7) * s, y - 8 * s],
                        fill=WHITE if k else LTRED, outline=BLACK)
        d.line([(x, y - 40 * s), (x, y - 70 * s), (x + 30 * s, y - 90 * s)],
               fill=BLACK, width=2)


def candle(cv, x, y, s=1.0):
    """Candle body; the flame is Terry's (fx.terry_flame). x,y = wick."""
    with cv.pil() as d:
        d.rectangle([x - 12 * s, y + 2 * s, x + 12 * s, y + 90 * s],
                    fill=WHITE, outline=LTGRAY)
        d.polygon([(x - 12 * s, y + 2 * s), (x - 4 * s, y + 14 * s),
                   (x - 10 * s, y + 26 * s), (x - 12 * s, y + 26 * s)],
                  fill=LTGRAY)
        d.rectangle([x - 30 * s, y + 90 * s, x + 30 * s, y + 98 * s],
                    fill=BROWN, outline=BLACK)
        d.ellipse([x - 40 * s, y + 94 * s, x + 40 * s, y + 108 * s],
                  fill=BROWN, outline=BLACK)
        d.line([(x, y + 2 * s), (x, y - 3 * s)], fill=BLACK,
               width=max(1, int(s)))


def gavel(cv, x, y, s=1.0, angle=0.0):
    ca, sa = math.cos(angle), math.sin(angle)
    def P(px, py):
        return (x + (px * ca - py * sa) * s, y + (px * sa + py * ca) * s)
    with cv.pil() as d:
        d.polygon([P(-4, 0), P(4, 0), P(4, 70), P(-4, 70)], fill=BROWN,
                  outline=BLACK)
        d.polygon([P(-26, -14), P(26, -14), P(26, 14), P(-26, 14)],
                  fill=BROWN, outline=BLACK)
        d.polygon([P(-30, -16), P(-22, -16), P(-22, 16), P(-30, 16)],
                  fill=YELLOW, outline=BLACK)
        d.polygon([P(22, -16), P(30, -16), P(30, 16), P(22, 16)],
                  fill=YELLOW, outline=BLACK)


def cherub(cv, x, y, s=1.0, t=0.0, flip=1):
    """1 Kings 6:23 'two cherubims of olive tree'. Gold, wings raised."""
    flap = math.sin(t * 1.5) * 0.15
    with cv.pil() as d:
        for sgn, fill in ((1, YELLOW), (-1, BROWN)):
            wx = x - flip * 8 * s
            d.polygon([(wx, y - 30 * s), (wx - flip * sgn * 10 * s,
                        y - 70 * s - flap * 40 * s),
                       (wx + flip * 44 * s, y - 88 * s - flap * 30 * s),
                       (wx + flip * 30 * s, y - 40 * s)], fill=fill,
                      outline=BLACK)
        d.polygon([(x - 12 * s, y), (x + 12 * s, y), (x + 7 * s, y - 34 * s),
                   (x - 7 * s, y - 34 * s)], fill=YELLOW, outline=BLACK)
        d.ellipse([x - 8 * s, y - 50 * s, x + 8 * s, y - 34 * s], fill=YELLOW,
                  outline=BLACK)
        d.ellipse([x - 11 * s, y - 58 * s, x + 11 * s, y - 52 * s],
                  outline=WHITE, width=max(1, int(s)))


def ark(cv, x, y, s=1.0, t=0.0):
    with cv.pil() as d:
        d.rectangle([x - 50 * s, y - 36 * s, x + 50 * s, y], fill=YELLOW,
                    outline=BROWN, width=2)
        d.rectangle([x - 54 * s, y - 42 * s, x + 54 * s, y - 34 * s],
                    fill=YELLOW, outline=BROWN)
        for k in range(-40, 41, 20):
            d.rectangle([x + k * s - 4 * s, y - 30 * s, x + k * s + 4 * s,
                         y - 6 * s], fill=BROWN)
        d.line([(x - 70 * s, y - 14 * s), (x + 70 * s, y - 14 * s)],
               fill=BROWN, width=max(1, int(3 * s)))


def mountain(cv, x, y, s=1.0, snow=True):
    pts = [(x - 260 * s, y), (x - 120 * s, y - 150 * s), (x - 60 * s,
           y - 110 * s), (x, y - 240 * s), (x + 90 * s, y - 130 * s),
           (x + 150 * s, y - 170 * s), (x + 280 * s, y)]
    m = poly_mask(pts)
    lvl = np.clip((np.mgrid[0:H, 0:W][0] - (y - 240 * s)) / (240 * s), 0, 1)
    img = dither_ramp(1 - lvl * 0.9, [DKGRAY, BROWN, LTGRAY], BAYER_FULL)
    cv.fb[m] = img[m]
    if snow:
        cv.poly([(x - 34 * s, y - 190 * s), (x, y - 240 * s),
                 (x + 30 * s, y - 196 * s), (x + 8 * s, y - 204 * s),
                 (x - 10 * s, y - 188 * s)], WHITE)
    return m


def bush(cv, x, y, s=1.0, t=0.0, frame=0, fire=True):
    with cv.pil() as d:
        for bx, by, r in ((-16, -10, 14), (0, -16, 16), (16, -10, 14),
                          (-6, -4, 12), (8, -4, 12)):
            d.ellipse([x + (bx - r) * s, y + (by - r) * s, x + (bx + r) * s,
                       y + (by + r) * s], fill=GREEN, outline=BLACK)
    if fire:
        rng = np.random.default_rng(frame + 5)
        n = 220
        px = x + rng.normal(0, 13, n) * s
        age = rng.random(n)
        py = y - 16 * s - age * 46 * s + np.sin(px * 0.2 + t * 8) * 2
        col = np.where(age < 0.35, YELLOW, np.where(age < 0.7, LTRED, RED))
        cv.plot(px, py, col)
        cv.plot(px + 1, py, col)


def monster(cv, x, y, s=1.0, t=0.0):
    """A green castle monster, flat-headed, bolts in the neck."""
    with cv.pil() as d:
        d.rectangle([x - 26 * s, y - 70 * s, x + 26 * s, y], fill=GREEN,
                    outline=BLACK, width=max(1, int(s)))
        d.rectangle([x - 28 * s, y - 76 * s, x + 28 * s, y - 60 * s],
                    fill=BLACK)
        for ex in (-12, 12):
            d.rectangle([x + (ex - 6) * s, y - 50 * s, x + (ex + 6) * s,
                         y - 42 * s], fill=YELLOW, outline=BLACK)
        d.line([(x - 14 * s, y - 20 * s), (x + 14 * s, y - 20 * s)],
               fill=BLACK, width=max(1, int(3 * s)))
        for k in range(-12, 13, 6):
            d.line([(x + k * s, y - 24 * s), (x + k * s, y - 16 * s)],
                   fill=BLACK)
        for bx in (-1, 1):
            d.rectangle([x + bx * 26 * s - (8 if bx < 0 else 0) * s,
                         y - 14 * s, x + bx * 26 * s + (8 if bx > 0 else 0)
                         * s, y - 8 * s], fill=LTGRAY, outline=BLACK)
