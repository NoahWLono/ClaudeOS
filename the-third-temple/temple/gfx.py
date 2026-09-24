"""640x480, 16 colors. The covenant, as a numpy array.

Every frame is a (480, 640) array of palette indices 0..15. Nothing here
fetches an image from storage: shapes, text, and shading are calculated.
"""
import os
import re

import numpy as np
from PIL import Image, ImageDraw

W, H = 640, 480

(BLACK, BLUE, GREEN, CYAN, RED, PURPLE, BROWN, LTGRAY, DKGRAY, LTBLUE,
 LTGREEN, LTCYAN, LTRED, LTPURPLE, YELLOW, WHITE) = range(16)
COLOR_NAMES = ["BLACK", "BLUE", "GREEN", "CYAN", "RED", "PURPLE", "BROWN",
               "LTGRAY", "DKGRAY", "LTBLUE", "LTGREEN", "LTCYAN", "LTRED",
               "LTPURPLE", "YELLOW", "WHITE"]

# ::/Adam/Gr/GrPalette.HC gr_palette_std, as 8-bit RGB.
PALETTE = np.array([
    (0x00, 0x00, 0x00), (0x00, 0x00, 0xAA), (0x00, 0xAA, 0x00),
    (0x00, 0xAA, 0xAA), (0xAA, 0x00, 0x00), (0xAA, 0x00, 0xAA),
    (0xAA, 0x55, 0x00), (0xAA, 0xAA, 0xAA), (0x55, 0x55, 0x55),
    (0x55, 0x55, 0xFF), (0x55, 0xFF, 0x55), (0x55, 0xFF, 0xFF),
    (0xFF, 0x55, 0x55), (0xFF, 0x55, 0xFF), (0xFF, 0xFF, 0x55),
    (0xFF, 0xFF, 0xFF)], dtype=np.uint8)

# Index 16 exists for exactly one pixel. See CHARTER VIOLATION #1.
CLAUDE_ORANGE = 16
PALETTE_17 = np.vstack([PALETTE, np.array([[0xD9, 0x77, 0x57]], np.uint8)])

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")


def _load_font():
    """::/Kernel/FontStd.HC: 256 U64s, low byte = top row, bit 0 = left."""
    with open(os.path.join(DATA, "FontStd.HC"), encoding="latin-1") as f:
        src = f.read()
    vals = [int(v, 16) for v in re.findall(r"0x([0-9A-Fa-f]{16})", src)]
    assert len(vals) == 256, len(vals)
    font = np.zeros((256, 8, 8), dtype=bool)
    for ch, v in enumerate(vals):
        for row in range(8):
            byte = (v >> (8 * row)) & 0xFF
            for col in range(8):
                font[ch, row, col] = (byte >> col) & 1
    return font


FONT = _load_font()

# Border glyphs used by ::/Adam/Gr/GrTextBase.HC TextBorder (single, double).
BORDER = {"h": (2, 3), "v": (4, 5), "tl": (6, 7), "tr": (8, 9),
          "bl": (10, 11), "br": (12, 13)}

BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26],
    [12, 44, 4, 36, 14, 46, 6, 38], [60, 28, 52, 20, 62, 30, 54, 22],
    [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]],
    dtype=np.float32)
BAYER = (BAYER8 + 0.5) / 64.0
BAYER_FULL = np.tile(BAYER, (H // 8, W // 8))

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def encode_text(s):
    return np.frombuffer(s.encode("latin-1", "replace"), dtype=np.uint8)


def text_mask(s, scale=1, sx=None, sy=None):
    """Boolean mask for a one-line string in the system font."""
    codes = encode_text(s)
    if len(codes) == 0:
        return np.zeros((8 * scale, 0), bool)
    g = FONT[codes]                                   # (L, 8, 8)
    m = g.transpose(1, 0, 2).reshape(8, len(codes) * 8)
    sx = sx or scale
    sy = sy or scale
    if sx > 1 or sy > 1:
        m = np.repeat(np.repeat(m, sy, axis=0), sx, axis=1)
    return m


def dither_ramp(level, ramp, thresh):
    """Ordered dithering of level in [0,1] across a list of colors."""
    ramp = np.asarray(ramp, dtype=np.uint8)
    n = len(ramp) - 1
    v = np.clip(level, 0.0, 1.0) * n
    i = np.floor(v).astype(np.int32)
    frac = v - i
    i = np.minimum(i + (frac > thresh), n)
    return ramp[i]


class Canvas:
    def __init__(self):
        self.fb = np.zeros((H, W), dtype=np.uint8)
        self.orange_pixel = None

    # ---- basics -------------------------------------------------------
    def clear(self, c=BLACK):
        self.fb[:] = c

    def rect(self, x, y, w, h, c):
        x0, y0 = max(int(x), 0), max(int(y), 0)
        x1, y1 = min(int(x + w), W), min(int(y + h), H)
        if x1 > x0 and y1 > y0:
            self.fb[y0:y1, x0:x1] = c

    def frame(self, x, y, w, h, c, t=1):
        self.rect(x, y, w, t, c)
        self.rect(x, y + h - t, w, t, c)
        self.rect(x, y, t, h, c)
        self.rect(x + w - t, y, t, h, c)

    def dither_rect(self, x, y, w, h, c1, c2, level=0.5):
        x0, y0 = max(int(x), 0), max(int(y), 0)
        x1, y1 = min(int(x + w), W), min(int(y + h), H)
        if x1 > x0 and y1 > y0:
            th = BAYER_FULL[y0:y1, x0:x1]
            self.fb[y0:y1, x0:x1] = np.where(th < level, c2, c1)

    def blit_mask(self, mask, x, y, c):
        """Paint color c wherever mask is True, clipped."""
        x, y = int(round(x)), int(round(y))
        h, w = mask.shape
        x0, y0 = max(x, 0), max(y, 0)
        x1, y1 = min(x + w, W), min(y + h, H)
        if x1 <= x0 or y1 <= y0:
            return
        sub = mask[y0 - y:y1 - y, x0 - x:x1 - x]
        region = self.fb[y0:y1, x0:x1]
        if np.isscalar(c) or np.ndim(c) == 0:
            region[sub] = c
        else:
            region[sub] = c[y0 - y:y1 - y, x0 - x:x1 - x][sub]

    def blit(self, img, x, y, key=255):
        """Copy an index image, skipping pixels equal to key."""
        self.blit_mask(img != key, x, y, img)

    # ---- text ---------------------------------------------------------
    def text(self, x, y, s, c=WHITE, scale=1, bg=None, shadow=None,
             sx=None, sy=None, outline=None):
        m = text_mask(s, scale, sx, sy)
        if bg is not None:
            self.rect(x, y, m.shape[1], m.shape[0], bg)
        if outline is not None:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1),
                           (1, 1), (-1, 1), (1, -1)):
                self.blit_mask(m, x + dx * max(1, scale // 2),
                               y + dy * max(1, scale // 2), outline)
        if shadow is not None:
            d = max(1, (sx or scale) // 2)
            self.blit_mask(m, x + d, y + d, shadow)
        self.blit_mask(m, x, y, c)
        return m.shape[1]

    def text_c(self, y, s, c=WHITE, scale=1, cx=W / 2, **kw):
        w = len(s) * 8 * (kw.get("sx") or scale)
        return self.text(int(cx - w / 2), y, s, c, scale, **kw)

    def char(self, x, y, code, c, bg=None):
        m = FONT[code]
        if bg is not None:
            self.rect(x, y, 8, 8, bg)
        self.blit_mask(m, x, y, c)

    # ---- TempleOS text-cell border -----------------------------------
    def border(self, col0, row0, col1, row1, c, bg=None, solid=True,
               title=None, title_c=None):
        """Window border in text cells (inclusive), glyphs 2..13."""
        s = 1 if solid else 0
        for col in range(col0 + 1, col1):
            self.char(col * 8, row0 * 8, BORDER["h"][s], c, bg)
            self.char(col * 8, row1 * 8, BORDER["h"][s], c, bg)
        for row in range(row0 + 1, row1):
            self.char(col0 * 8, row * 8, BORDER["v"][s], c, bg)
            self.char(col1 * 8, row * 8, BORDER["v"][s], c, bg)
        self.char(col0 * 8, row0 * 8, BORDER["tl"][s], c, bg)
        self.char(col1 * 8, row0 * 8, BORDER["tr"][s], c, bg)
        self.char(col0 * 8, row1 * 8, BORDER["bl"][s], c, bg)
        self.char(col1 * 8, row1 * 8, BORDER["br"][s], c, bg)
        if title:
            self.text((col0 + 2) * 8, row0 * 8, title,
                      title_c if title_c is not None else c, bg=bg)

    # ---- shapes via PIL (C speed) -------------------------------------
    def pil(self):
        return _PilCtx(self)

    def poly(self, pts, c, outline=None):
        with self.pil() as d:
            d.polygon([(float(x), float(y)) for x, y in pts], fill=c,
                      outline=outline)

    def line(self, x0, y0, x1, y1, c, w=1):
        with self.pil() as d:
            d.line([(x0, y0), (x1, y1)], fill=c, width=w)

    def circle(self, cx, cy, r, c, outline=None, w=1):
        with self.pil() as d:
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c,
                      outline=outline, width=w)

    def ellipse(self, x0, y0, x1, y1, c=None, outline=None, w=1):
        with self.pil() as d:
            d.ellipse([x0, y0, x1, y1], fill=c, outline=outline, width=w)

    def plot(self, xs, ys, c):
        xs = np.asarray(xs).astype(np.int32)
        ys = np.asarray(ys).astype(np.int32)
        ok = (xs >= 0) & (xs < W) & (ys >= 0) & (ys < H)
        if np.ndim(c) == 0:
            self.fb[ys[ok], xs[ok]] = c
        else:
            self.fb[ys[ok], xs[ok]] = np.asarray(c)[ok]

    # ---- output -------------------------------------------------------
    def rgb(self):
        out = PALETTE[self.fb]
        if self.orange_pixel is not None:
            x, y = self.orange_pixel
            out[y, x] = PALETTE_17[CLAUDE_ORANGE]
        return out


class _PilCtx:
    def __init__(self, cv):
        self.cv = cv

    def __enter__(self):
        self.img = Image.fromarray(self.cv.fb)
        return ImageDraw.Draw(self.img)

    def __exit__(self, *a):
        self.cv.fb[:] = np.asarray(self.img)


def poly_mask(pts, w=W, h=H):
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).polygon([(float(x), float(y)) for x, y in pts],
                                fill=1)
    return np.asarray(img).astype(bool)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def clamp01(x):
    return min(max(x, 0.0), 1.0)
