"""TempleOS furniture: the status bar, windows, the editor, subtitles,
rubber stamps, propaganda posters."""
import math
import re

import numpy as np

from . import fx
from .gfx import (BAYER_FULL, BLACK, BLUE, BROWN, CYAN, DKGRAY, GREEN, H, LTBLUE,
                  LTCYAN, LTGRAY, LTGREEN, LTPURPLE, LTRED, PURPLE, RED, W,
                  WHITE, YELLOW, clamp01, ease, text_mask)

SPARK = [
    "....X....",
    ".X..X..X.",
    "..X.X.X..",
    "...XXX...",
    "XXXXXXXXX",
    "...XXX...",
    "..X.X.X..",
    ".X..X..X.",
    "....X....",
]
SPARK_MASK = np.array([[c == "X" for c in row] for row in SPARK])


def spark_icon(cv, x, y, scale=1, c1=BROWN, c2=LTRED):
    m = np.repeat(np.repeat(SPARK_MASK, scale, 0), scale, 1)
    img = np.where((np.indices(m.shape).sum(0) % 2) == 0, c1, c2)
    cv.blit_mask(m, x, y, img.astype(np.uint8))


def clock_str(T):
    s = int(17 * 3600 + 58 * 60 + 44 + T)
    return "%02d:%02d:%02d" % ((s // 3600) % 24, (s // 60) % 60, s % 60)


def top_bar(cv, T, task="Term", cpu=None):
    """Row 0, like the WinMgr bar."""
    cv.rect(0, 0, W, 8, BLUE)
    x = 0
    x += cv.text(x, 0, " " + clock_str(T) + " ", WHITE, bg=BLUE)
    x += cv.text(x, 0, "Adam", YELLOW, bg=BLUE)
    x += cv.text(x, 0, " " + task + " ", LTCYAN, bg=BLUE)
    Tq = math.floor(T * 4) / 4
    load = cpu if cpu is not None else 0.35 + 0.3 * math.sin(Tq * 1.7) ** 2
    for i in range(4):
        v = clamp01(load + 0.15 * math.sin(Tq * 3.1 + i * 1.7))
        bars = int(v * 6)
        x += cv.text(x, 0, "CPU%d" % i, LTGRAY, bg=BLUE)
        x += cv.text(x, 0, "\xdb" * bars + "\xb0" * (6 - bars) + " ",
                     LTGREEN if v < 0.8 else LTRED, bg=BLUE)
    cv.text(W - 8 * 7, 0, "RING 0 ", LTRED, bg=BLUE)


def window(cv, c0, r0, c1, r1, title="Term", bg=WHITE, fg=BLUE,
           focused=True, title_c=None):
    cv.rect(c0 * 8, r0 * 8, (c1 - c0 + 1) * 8, (r1 - r0 + 1) * 8, bg)
    cv.border(c0, r0, c1, r1, fg, bg, focused, title=" %s " % title,
              title_c=title_c if title_c is not None else fg)


def typed(s, t, cps=18.0):
    n = int(max(t, 0) * cps)
    return s[:n], n >= len(s)


def cursor_on(t):
    return (t * 2.0) % 1.0 < 0.55


# ---- HolyC syntax colors (roughly what the TempleOS editor does) -------
KEYWORDS = {"for", "while", "if", "else", "return", "switch", "case",
            "break", "class", "public", "extern", "try", "catch", "do",
            "include", "define", "sizeof", "goto", "union"}
TYPES = {"U0", "I0", "I8", "U8", "I16", "U16", "I32", "U32", "I64", "U64",
         "F64", "Bool", "int", "void", "char", "CDC", "CTask"}
TOKEN = re.compile(r'(//.*$)|("(?:\\.|[^"\\])*"?)|(\'[^\']*\'?)|'
                   r'(#\w+)|(\b[A-Za-z_]\w*\b)|(\b\d[\w.]*\b)|(.)')


def code_line(cv, x, y, line, scale=1, default=BLUE):
    """Colorized HolyC. Returns width."""
    cx = x
    for m in TOKEN.finditer(line):
        s = m.group(0)
        if m.group(1):
            c = GREEN
        elif m.group(2) or m.group(3):
            c = RED
        elif m.group(4):
            c = PURPLE
        elif m.group(5):
            c = (CYAN if s in TYPES else PURPLE if s in KEYWORDS
                 else BLACK if s[0].isupper() else default)
        elif m.group(6):
            c = BROWN
        else:
            c = default
        cx += cv.text(cx, y, s, c, scale=scale)
    return cx - x


def code_block(cv, x, y, lines, scale=1, lh=None, upto=None):
    lh = lh or 10 * scale
    shown = 0
    for i, ln in enumerate(lines):
        if upto is not None:
            if shown >= upto:
                break
            ln = ln[:max(0, upto - shown)]
            shown += len(lines[i]) + 1
        code_line(cv, x, y + i * lh, ln, scale)


# ---- subtitles ---------------------------------------------------------
SUB_COLORS = {"CLAUDE": WHITE, "ANNOUNCER": YELLOW, "GOD": LTCYAN}


def wrap(text, width):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            if cur:
                lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def subtitle_pages(text, width=38, per_page=2):
    lines = wrap(text, width)
    return [lines[i:i + per_page] for i in range(0, len(lines), per_page)]


def subtitles(cv, text, speaker, prog, style="bar"):
    """prog in [0,1] picks the page, weighted by characters."""
    pages = subtitle_pages(text)
    if not pages:
        return
    sizes = [sum(len(l) for l in p) + 1 for p in pages]
    tot = sum(sizes)
    acc = 0
    idx = len(pages) - 1
    for i, s in enumerate(sizes):
        acc += s
        if prog * tot < acc:
            idx = i
            break
    lines = pages[idx]
    c = SUB_COLORS.get(speaker, WHITE)
    y0 = H - 12 - 18 * len(lines)
    for i, ln in enumerate(lines):
        w = len(ln) * 16
        x = (W - w) // 2
        y = y0 + i * 18
        cv.rect(x - 6, y - 2, w + 12, 18, BLACK)
        cv.text(x, y, ln, c, scale=2)
    if speaker == "CLAUDE":
        lw = len(lines[0]) * 16
        spark_icon(cv, (W - lw) // 2 - 6 - 22, y0 - 1, 2)
    elif speaker == "GOD":
        pass


# ---- stamps ------------------------------------------------------------
def rotate_nearest(img, angle, key=255):
    h, w = img.shape
    c, s = math.cos(angle), math.sin(angle)
    size = int(math.hypot(h, w)) + 2
    yy, xx = np.mgrid[0:size, 0:size]
    cx = cy = size / 2
    xs = (xx - cx) * c + (yy - cy) * s + w / 2
    ys = -(xx - cx) * s + (yy - cy) * c + h / 2
    ok = (xs >= 0) & (xs < w) & (ys >= 0) & (ys < h)
    out = np.full((size, size), key, np.uint8)
    out[ok] = img[ys[ok].astype(int), xs[ok].astype(int)]
    return out


_stamp_cache = {}


def stamp(cv, t, line1, line2="", c=RED, x=W / 2, y=H / 2 - 30,
          angle=-0.18, sc1=4, sc2=2, paper=WHITE, dim=True):
    """A rubber stamp thumping onto paper. t = seconds since it landed."""
    if t < 0:
        return
    key = (line1, line2, c, angle, sc1, sc2, paper)
    if key not in _stamp_cache:
        w1 = len(line1) * 8 * sc1
        w2 = len(line2) * 8 * sc2
        ww = max(w1, w2) + 36
        hh = 8 * sc1 + (8 * sc2 + 12 if line2 else 0) + 34
        img = np.full((hh, ww), paper, np.uint8)
        for k in range(4):
            img[k, :] = img[-1 - k, :] = c
            img[:, k] = img[:, -1 - k] = c
        img[8:10, 8:-8] = c
        img[-10:-8, 8:-8] = c
        img[8:-8, 8:10] = c
        img[8:-8, -10:-8] = c
        m1 = text_mask(line1, sc1)
        _blit(img, m1, (ww - w1) // 2, 17, c)
        if line2:
            m2 = text_mask(line2, sc2)
            _blit(img, m2, (ww - w2) // 2, 17 + 8 * sc1 + 10, c)
        rng = np.random.default_rng(len(line1) * 31 + len(line2))
        holes = rng.random(img.shape) < 0.10
        img[holes & (img == c)] = paper
        _stamp_cache[key] = rotate_nearest(img, angle)
    img = _stamp_cache[key]
    if dim:
        cv.fb[:] = np.where(BAYER_FULL < 0.5, cv.fb, BLACK)
    s = 1.0 + 0.9 * (1 - ease(t / 0.14))
    if s > 1.01:
        hh, ww = img.shape
        yi = (np.arange(int(hh * s)) / s).astype(int)
        xi = (np.arange(int(ww * s)) / s).astype(int)
        img = img[yi][:, xi]
    hh, ww = img.shape
    cv.blit(img, x - ww / 2, y - hh / 2)


def _blit(dst, mask, x, y, c):
    h, w = mask.shape
    dst[y:y + h, x:x + w][mask] = c


def stamp_shake(t):
    if 0 <= t < 0.3:
        a = (1 - t / 0.3) * 6
        return (a * math.sin(t * 90), a * math.cos(t * 77))
    return (0, 0)


# ---- posters -----------------------------------------------------------
def big_title(cv, y, s, c=YELLOW, scale=5, shadow=BROWN, outline=BLACK,
              cx=W / 2):
    cv.text_c(y, s, c, scale, cx=cx, shadow=shadow, outline=outline)


def fit_scale(s, max_w=600, max_scale=6):
    return max(1, min(max_scale, max_w // max(1, len(s) * 8)))


def poster(cv, t, top, title, sub="", scheme=0):
    schemes = [(RED, LTRED, YELLOW), (BLUE, LTBLUE, YELLOW),
               (PURPLE, LTPURPLE, YELLOW), (GREEN, LTGREEN, YELLOW),
               (BROWN, YELLOW, WHITE), (CYAN, LTCYAN, YELLOW)]
    c1, c2, tc = schemes[scheme % len(schemes)]
    fx.rays(cv, t, c1, c2, n=20, speed=0.02, cy=H * 0.62)
    cv.rect(0, 26, W, 30, BLACK)
    cv.text_c(33, top, WHITE, 2)
    lines = title.split("\n")
    sc = min(fit_scale(l, 600, 7) for l in lines)
    pop = ease(t / 0.35)
    y = 110 - (len(lines) - 1) * sc * 5
    for i, ln in enumerate(lines):
        yy = int(y + i * sc * 10 + (1 - pop) * 30)
        big_title(cv, yy, ln, tc, sc)
    if sub:
        for i, ln in enumerate(sub.split("\n")):
            yy = int(y + len(lines) * sc * 10 + 14 + i * 22)
            cv.rect((W - len(ln) * 16) // 2 - 8, yy - 4, len(ln) * 16 + 16,
                    24, BLACK)
            cv.text_c(yy, ln, WHITE, 2)


def chapter_card(cv, t, num, title, dark=False):
    cv.clear(BLACK)
    fx.STARS.draw(cv, t, speed=0.05)
    k = ease(t / 0.8)
    cw = int(W * k)
    cv.rect((W - cw) // 2, 150, cw, 2, BROWN if not dark else DKGRAY)
    cv.rect((W - cw) // 2, 330, cw, 2, BROWN if not dark else DKGRAY)
    if t > 0.3:
        cv.text_c(180, "CHAPTER " + num, LTGRAY if dark else LTRED, 3,
                  shadow=BLACK)
    if t > 0.7:
        sc = fit_scale(title, 600, 6)
        big_title(cv, 250 - sc * 2, title, LTGRAY if dark else YELLOW, sc,
                  shadow=DKGRAY if dark else BROWN)


def doc_window(cv, c0, r0, c1, r1, title, lines, t=None, cps=40,
               bg=WHITE, fg=BLUE, scale=1):
    """A DolDoc-ish text window; lines may carry (text, color)."""
    window(cv, c0, r0, c1, r1, title, bg, fg)
    budget = None if t is None else int(t * cps)
    y = (r0 + 2) * 8
    for ln in lines:
        s, c = (ln, fg) if isinstance(ln, str) else ln
        if budget is not None:
            if budget <= 0:
                break
            s = s[:budget]
            budget -= len(ln if isinstance(ln, str) else ln[0]) + 1
        cv.text((c0 + 2) * 8, y, s, c, scale=scale)
        y += 10 * scale


def quote_box(cv, t, text, who, width=34, y=None, c=BLUE, bg=WHITE,
              title="Quote", who_c=RED, scale=2, cps=45):
    lines = wrap(text, width)
    lh = 9 * scale + 3
    hh = len(lines) * lh + 44 + (18 if who else 0)
    ww = width * 8 * scale + 40
    x0 = (W - ww) // 2
    y0 = y if y is not None else (H - hh) // 2 - 30
    cv.rect(x0 + 6, y0 + 6, ww, hh, BLACK)
    cv.rect(x0, y0, ww, hh, bg)
    cv.frame(x0, y0, ww, hh, c, 2)
    cv.frame(x0 + 4, y0 + 4, ww - 8, hh - 8, c, 1)
    cv.text(x0 + 16, y0 - 4, " " + title + " ", c, bg=bg)
    budget = int(max(t, 0) * cps)
    yy = y0 + 20
    for ln in lines:
        s = ln[:max(0, budget)]
        budget -= len(ln) + 1
        cv.text(x0 + 20, yy, s, c, scale=scale)
        yy += lh
    if who and budget > 0:
        cv.text(x0 + ww - 20 - len(who) * 8 * 1, yy + 8, who, who_c, 1)
    return y0 + hh
