"""Replay God's doodle (oracle ops from GodDoodle) onto a framebuffer,
step by step, the way GodDoodleSprite drew it."""
import numpy as np
from PIL import Image, ImageDraw

from .gfx import RED, WHITE


def smooth(img, num=3):
    """GodDoodleSmooth: each pixel becomes the most common color in its
    (2*num+1)^2 neighborhood; ties go to the lowest color number."""
    a = np.asarray(img)
    h, w = a.shape
    k = 2 * num + 1
    best = np.full(a.shape, -1)
    out = np.zeros_like(a)
    for c in range(16):
        m = (a == c).astype(np.int32)
        p = np.pad(m, num)
        s = p.cumsum(0).cumsum(1)
        s = np.pad(s, ((1, 0), (1, 0)))
        cnt = s[k:, k:] - s[:-k, k:] - s[k:, :-k] + s[:-k, :-k]
        upd = cnt > best
        best = np.where(upd, cnt, best)
        out = np.where(upd, c, out)
    return Image.fromarray(out.astype(np.uint8))


def states(ops, w=640, h=472):
    """Canvas after each op (list of uint8 arrays)."""
    img = Image.new("L", (w, h), WHITE)
    out = []
    for op in ops:
        d = ImageDraw.Draw(img)
        kind = op[0]
        if kind == "ellipse":
            _, x, y, rx, ry = op
            d.ellipse([x - rx, y - ry, x + rx, y + ry], outline=RED)
        elif kind == "circle":
            _, x, y, r = op
            d.ellipse([x - r, y - r, x + r, y + r], outline=RED)
        elif kind == "border":
            _, x1, y1, x2, y2 = op
            d.rectangle([min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)],
                        outline=RED)
        elif kind == "line":
            _, x1, y1, x2, y2 = op
            d.line([(x1, y1), (x2, y2)], fill=RED)
        elif kind == "fill":
            _, x, y, c = op
            xi, yi = int(x), int(y)
            if 0 <= xi < w and 0 <= yi < h:
                ImageDraw.floodfill(img, (xi, yi), c)
        elif kind == "smooth":
            img = smooth(img, op[1])
        out.append(np.asarray(img).copy())
    return out
