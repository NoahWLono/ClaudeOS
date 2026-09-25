"""Scenes made from Terry's own drawings: the guided tour, the elephants,
and the elephant cameos. Every sprite and mesh here is read from his
disks (data/relics, see relics.py)."""
import json
import math
import os

import numpy as np

from . import doodle as DD
from . import fx, ui
from . import relics as R
from . import sprites as S
from . import three_d as D
from .gfx import (BAYER_FULL, BLACK, BLUE, BROWN, CYAN, DKGRAY, GREEN, H,
                  LTBLUE, LTCYAN, LTGRAY, LTGREEN, LTPURPLE, LTRED, PURPLE,
                  RED, W, WHITE, YELLOW, clamp01, ease)

HERE = os.path.dirname(os.path.abspath(__file__))
ELE = "Demo/Graphics/Elephant.HC"
EWALK = "Demo/Games/ElephantWalk.HC"
TALONS = "Demo/Games/Talons.HC"
FLATTOPS = "Demo/Games/FlatTops.HC"
XCAL = "Apps/X-Caliber/X-Caliber.HC"
B17 = "Sup1Games/B17.HC"
MOUNTAIN = "Sup1Games/AfterEgypt/Mountain.HC"
GODTALK = "Sup1Games/AfterEgypt/GodTalking.HC"
FISH = "Demo/Graphics/WallPaperFish.HC"
KEEPAWAY = "Apps/KeepAway/KeepAway.HC"
CASTLE = "Demo/Games/CastleFrankenstein.HC"
CHESS = "Sup1Games/Chess.HC"
NIGHT = "Apps/Psalmody/Examples/night.HC"
FLAPBAT = "Demo/Games/FlapBat.HC"


def step(t, fps=10.0):
    return math.floor(t * fps) / fps


def tri(t, period):
    """Triangle wave 0..1..0, like TempleOS Tri()."""
    x = (t / period) % 1.0
    return 1.0 - abs(2.0 * x - 1.0)


# =====================================================================
# Terry's sprites as index images (255 = transparent)
# =====================================================================

_img = {}


def relic_image(path, num, scale=1.0, elems=None, key=None):
    """Draw a sprite at its native size (so Terry's flood fills stay
    inside his outlines), then scale it with nearest neighbour.
    Returns (img, ox, oy): where the sprite's origin lands in img."""
    ck = key or (path, num, round(scale, 3))
    if ck in _img:
        return _img[ck]
    el = elems if elems is not None else R.sprite(path, num)
    x0, y0, x1, y1 = R.bounds(el)
    pad = 3
    w = int(x1 - x0) + 2 * pad + 2
    h = int(y1 - y0) + 2 * pad + 2
    fb = np.full((h, w), 255, np.uint8)
    R.draw(fb, el, -x0 + pad, -y0 + pad)
    ox, oy = -x0 + pad, -y0 + pad
    if scale != 1.0:
        hh, ww = max(1, int(h * scale)), max(1, int(w * scale))
        yi = np.clip((np.arange(hh) / scale).astype(int), 0, h - 1)
        xi = np.clip((np.arange(ww) / scale).astype(int), 0, w - 1)
        fb = fb[yi][:, xi]
        ox, oy = ox * scale, oy * scale
    _img[ck] = (fb, ox, oy)
    return _img[ck]


def blit_at(cv, im, x, y, ax=0.0, ay=0.0, flip=False):
    """Blit so that sprite point (ax, ay) (in sprite units * scale, relative
    to the sprite origin) lands on screen (x, y)."""
    img, ox, oy = im
    if flip:
        img = img[:, ::-1]
        ox = img.shape[1] - ox
        ax = -ax
    cv.blit(img, int(round(x - ox - ax)), int(round(y - oy - ay)))


_ele_frames = None


def ele_frames(n=12):
    """SpriteInterpolate between Terry's two keyframes, precomputed."""
    global _ele_frames
    if _ele_frames is None:
        e1, e2 = R.sprite(ELE, 1), R.sprite(ELE, 2)
        _ele_frames = [R.interpolate(e1, e2, k / (n - 1)) for k in range(n)]
    return _ele_frames


# feet of Terry's elephant in sprite coordinates (bounds 181..385, -289..-79)
ELE_FEET = (283.0, -79.0)


def terry_elephant(cv, x, y, t, scale=1.0, flip=False):
    """Elephant.HC: Sprite3(dc, 0, h, 0, SpriteInterpolate(Tri(tS,2.0),
    <1>, <2>)). x, y = where his feet touch the ground."""
    frames = ele_frames()
    k = tri(t, 2.0)
    i = int(round(k * (len(frames) - 1)))
    im = relic_image(ELE, 1, scale, elems=frames[i],
                     key=("ele", i, round(scale, 3)))
    blit_at(cv, im, x, y, ELE_FEET[0] * scale, ELE_FEET[1] * scale, flip)


def elephant_walk_bitmap(cv, x, y, t, scale=1.0, sway=True, flip=False):
    """ElephantWalk.HC: Sprite3ZB(..., <1>, Sin(8*tS)/4), mirrored while
    it walks right (DCF_SYMMETRY|DCF_JUST_MIRROR)."""
    img, ox, oy = relic_image(EWALK, 1, scale)
    if flip:
        img = img[:, ::-1]
    if sway:
        img = ui.rotate_nearest(img, math.sin(8 * step(t, 15)) / 4)
    cv.blit(img, int(x - img.shape[1] / 2), int(y - img.shape[0] / 2))


def elephant_scenery(cv, h=472, y0=8, t=0.0):
    """Elephant.HC's DrawIt, sprite for sprite."""
    for n, x, y in ((3, 100, h - 60), (4, 194, h - 140), (5, 400, h - 10),
                    (6, 50, h - 160)):
        im = relic_image(ELE, n)
        blit_at(cv, im, x, y0 + y)
    terry_elephant(cv, ELE_FEET[0], y0 + h + ELE_FEET[1], t)


# =====================================================================
# Terry's 3D meshes
# =====================================================================

_mesh = {}


def mesh(path, num):
    key = (path, num)
    if key not in _mesh:
        vs, tris = R.mesh_of(path, num)
        v = vs.copy()
        v[:, 1] = -v[:, 1]
        v -= v.mean(0)
        faces, ramps = [], {}
        for (a, b, c), col in tris:
            col &= 15
            name = "c%d" % col
            if name not in ramps:
                base = col & 7
                if col in (7, 8, 15, 0):
                    ramps[name] = [DKGRAY, LTGRAY, WHITE] if col else \
                        [BLACK, DKGRAY]
                else:
                    ramps[name] = [BLACK, base, base | 8, WHITE]
            faces.append(([a, b, c], name))
        _mesh[key] = ((v, faces), ramps, float(np.abs(v).max()) + 1)
    return _mesh[key]


def draw_mesh(cv, path, num, R_, x, y, size, ambient=0.35):
    m, ramps, r = mesh(path, num)
    D.render(cv, m, R_, (0, 0, r * 3.0), focal=size * 3.0 / 2.0,
             center=(x, y), ambient=ambient, ramps=ramps, levels=2,
             cull=False)


# =====================================================================
# oracle additions (chapter V)
# =====================================================================

_doodle_states = None


def doodle_states():
    global _doodle_states
    if _doodle_states is None:
        log = json.load(open(os.path.join(HERE, "..", "data",
                                          "oracle_log.json")))
        e = next(x for x in log if x["kind"] == "doodle")
        _doodle_states = DD.states(e["ops"])
    return _doodle_states


def doodle_view(cv, ctx, it_doodle, stage):
    """GodDoodleSprite: white canvas under the menu row."""
    t = ctx.t
    ui.top_bar(cv, ctx.T, task="GodDoodle")
    st = doodle_states()
    if stage <= 1:
        cv.rect(0, 8, W, H - 8, WHITE)
        ui.window(cv, 12, 18, 67, 34, "PopUp", WHITE, BLUE)
        cv.text(120, 168, "The Holy Spirit can puppet you.", PURPLE)
        cv.text(120, 188, "Press <SPACE> until it finishes.", BLACK)
        cv.text(160, 188, "<SPACE>", GREEN)
        cv.rect(280, 236, 64, 14, GREEN)
        cv.text(296, 239, "OKAY", WHITE)
        return
    if it_doodle is not None and ctx.cur is it_doodle:
        k = clamp01((t - it_doodle["doodle_t0"]) / it_doodle["doodle_dur"])
    else:
        k = 1.0
    idx = min(int(k * len(st)), len(st) - 1)
    cv.fb[8:8 + st[idx].shape[0], :] = st[idx]
    blink = (t * 2) % 1 < 0.6
    if k < 1.0 and blink:
        cv.text_c(236, "Press <SPACE> repeatedly.", GREEN)
    elif k >= 1.0 and blink and stage == 2:
        cv.text_c(228, "Press <ESC> to insert sprite.", RED)
        cv.text_c(244, "Press <SHIFT-ESC> to throw-away sprite.", RED)
    if stage == 3:
        # squint: Terry's elephant, faintly, over God's doodle
        im = relic_image(ELE, 1, 1.4, elems=ele_frames()[0],
                         key=("ele_squint", 1.4))
        img, ox, oy = im
        mask = (img != 255) & (BAYER_FULL[:img.shape[0], :img.shape[1]] <
                               0.45 * clamp01(ctx.since() / 2.0))
        x0 = int(330 - img.shape[1] / 2)
        y0 = int(250 - img.shape[0] / 2)
        sub = cv.fb[y0:y0 + img.shape[0], x0:x0 + img.shape[1]]
        m = mask[:sub.shape[0], :sub.shape[1]]
        sub[m] = LTRED


GSRC = [("GSRC_NIST_BEACON", 0, "US government randomness beacon"),
        ("GSRC_HOTBITS", 1, "radioactive decay"),
        ("GSRC_ANU_NIST", 2, "quantum random numbers, Australia"),
        ("GSRC_GOOGLE", 3, None), ("GSRC_RANDOM_ORG", 4, None),
        ("GSRC_RANDOM_NUMBERS_INFO", 5, None), ("GSRC_PASSWORD", 6, None),
        ("GSRC_GENERATE_DATA", 7, None), ("GSRC_VIRTUAL_NOTARY", 8, None),
        ("GSRC_TIMER", 9, "the stopwatch")]


def sources_view(cv, ctx, t):
    """::/Demo/AcctExample/TOS/TOSExt.HC, Terry's own account files."""
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Ed")
    ui.window(cv, 0, 1, 79, 59, "::/Demo/AcctExample/TOS/TOSExt.HC",
              WHITE, BLUE)
    cv.text(24, 28, "#help_index \"Misc/TOS/God;God/TOS\"", BLUE)
    k = ctx.since()
    notes = [g for g in GSRC if g[2]]
    for i, (name, n, note) in enumerate(GSRC):
        y = 60 + i * 26
        hi = note is not None and k > 1.0 + notes.index((name, n, note)) * 1.3
        if hi:
            cv.rect(20, y - 5, 330, 18, YELLOW)
        cv.text(24, y, "#define", PURPLE, 1, sx=1, sy=2)
        cv.text(88, y, name, BLACK if hi else BLUE, 1, sx=1, sy=2)
        cv.text(310, y, "%d" % n, BLACK, 1, sx=1, sy=2)
        if hi:
            cv.text(364, y, note, RED, 1, sx=1, sy=2)
    cv.text(24, 340, "extern U0 GodVideoU32(U32 rand_u32,U8 *filename);",
            BLUE)
    cv.text(24, 352, "extern U0 TOSGodDoodle(I64 god_src,...);", BLUE)


def video_view(cv, ctx, it, t):
    e = it["entry"] if it else None
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Ed")
    ui.window(cv, 0, 1, 79, 59, "GodVideoU32(U32 rand_u32,U8 *filename)",
              WHITE, BLUE)
    cv.text(24, 28, "::/Sup1/Sup1Blog/YouTube.DD  754 title/serial pairs",
            RED)
    cv.text(24, 40, "Terry's function body isn't on the disks.", DKGRAY)
    cv.text(24, 50, "Rule used here: rand_u32 mod 754.", DKGRAY)
    if e is None:
        return
    k = t - it["t0"]
    if k > 0.6:
        cv.text(24, 80, "rand_u32 = 0x%08X" % e["rand_u32"], BLACK, 2)
    if k > 1.2:
        cv.text(24, 112, "0x%08X mod %d = %d" % (e["rand_u32"], e["num"],
                                                 e["index"]), BLUE, 2)
    if k > 2.0:
        ui.big_title(cv, 180, e["title"].upper()[:26], PURPLE, 3,
                     shadow=LTGRAY, outline=None)
        cv.text_c(226, "youtube.com/watch?v=" + e["serial"], DKGRAY)


def risen_view(cv, ctx, t, song):
    """::/Sup1/Sup1Hymns/risen.HC DrawIt: seven white birds circling."""
    cv.clear(LTCYAN)
    ui.top_bar(cv, ctx.T, task="JukeBox")
    dt = (t - song["song_t0"]) * 2.48 if song else 0.0
    dt = step(dt, 15)
    rng = np.random.default_rng(7)
    bx = rng.uniform(-5, 5, 7)
    by = rng.uniform(-5, 5, 7)
    with cv.pil() as d:
        for i in range(7):
            th = math.pi / 2 * i / 7 + 0.2 * math.pi * dt + math.pi / 2
            cx = 325 + (50 * math.cos(th) + bx[i]) * 2.2
            z = 30 * i / 7 + 4 * (dt % 20)
            cy = 170 + (50 * math.sin(th) + by[i]) * 0.9 - z * 0.8
            wing = math.sin(2 * math.pi * dt + i * 2 * math.pi / 7)
            s = 3.0
            for sgn in (-1, 1):
                d.polygon([(cx, cy - 2 * s), (cx, cy + 2 * s),
                           (cx + sgn * 6 * s * math.cos(wing * 0.9),
                            cy - 6 * s * math.sin(wing * 0.9))], fill=WHITE)
            d.line([(cx, cy - 2 * s), (cx, cy + 2 * s)], fill=LTGRAY)
    cv.text_c(330, "RISEN", BLACK, 4)
    cv.text_c(372, "one of Terry's oldest songs", BLUE, 1)
    cv.text_c(386, "\"He laughed and gave an epic song!\"", RED, 1)


# =====================================================================
# the guided tour (chapter VI)
# =====================================================================

MENU = ["Color (4-bit)", "Dither Color (4-bit)", "Thick", "Planar Symmetry",
        "", "Point", "Line", "Arrow", "Rect", "Circle", "Ellipse", "Polygon",
        "Text", "Text Box", "Text Diamond", "Flood Fill",
        "Flood Fill Not Color", "PolyLine", "PolyPoint", "BSpline2",
        "BSpline3", "BSpline2 Closed", "BSpline3 Closed",
        "Insert Scrn-Captured BitMap", "+] Create or Edit 3D Mesh",
        "+] Convert to BitMap or Edit BitMap", "+] Sprite Edit Menu",
        "Exit  Sprite", "Abort Sprite"]
ELEM_MENU = {R.SPT_COLOR: "Color (4-bit)", R.SPT_LINE: "Line",
             R.SPT_CIRCLE: "Circle", R.SPT_FLOOD_FILL: "Flood Fill",
             R.SPT_THICK: "Thick", R.SPT_POLYLINE: "PolyLine"}


def sprite_menu(cv, x, y, hi=None, rows=None):
    rows = rows or MENU
    ww = 260
    hh = len(rows) * 11 + 16
    cv.rect(x + 4, y + 4, ww, hh, BLACK)
    cv.rect(x, y, ww, hh, WHITE)
    cv.frame(x, y, ww, hh, LTBLUE, 2)
    cv.text(x + 8, y - 4, " Sprite Edit ", LTBLUE, bg=WHITE)
    for i, r in enumerate(rows):
        yy = y + 10 + i * 11
        if r == hi:
            cv.rect(x + 4, yy - 2, ww - 8, 11, BLUE)
            cv.text(x + 10, yy, r, WHITE)
        elif r:
            cv.text(x + 10, yy, r,
                    PURPLE if r.startswith("+]") else LTBLUE)


def replay_view(cv, ctx, k_frac):
    """Terry's elephant, one sprite element at a time."""
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Ed")
    ui.window(cv, 0, 1, 45, 59, "::/Demo/Graphics/Elephant.HC", WHITE, BLUE)
    el = R.sprite(ELE, 1)
    n_draw = len(el) - 1
    k = int(clamp01(k_frac) * n_draw)
    part = el[:k] + [(R.SPT_END,)]
    fb = np.full((250, 340), 255, np.uint8)
    R.draw(fb, part, -150, 300)
    m = fb != 255
    cv.fb[70:320, 8:348][m] = fb[m]
    cur = el[max(k - 1, 0)]
    name = ELEM_MENU.get(cur[0], "Line")
    sprite_menu(cv, 372, 40, hi=name if k_frac < 1.0 else None,
                rows=MENU[:20])
    cv.rect(8, 330, 350, 60, BLACK)
    cv.text(16, 338, "ELEMENT %2d / %d" % (k, n_draw), YELLOW, 2)
    detail = ""
    if cur[0] == R.SPT_LINE:
        detail = "(%d,%d)-(%d,%d)" % tuple(int(v) for v in cur[1:5])
    elif cur[0] == R.SPT_COLOR:
        detail = "color %d" % cur[1]
    elif cur[0] == R.SPT_CIRCLE:
        detail = "(%d,%d) r=%d" % tuple(int(v) for v in cur[1:4])
    elif cur[0] == R.SPT_FLOOD_FILL:
        detail = "at (%d,%d)" % tuple(int(v) for v in cur[1:3])
    cv.text(16, 362, name + "  " + detail, WHITE)


DOODLE_STROKES = [  # an elephant, drawn the Doodle.HC way (7 px lines)
    (LTGRAY, [(170, 250), (230, 190), (360, 185), (430, 230), (440, 300),
              (400, 330), (230, 330), (175, 300), (170, 250)]),
    (LTGRAY, [(430, 230), (480, 215), (520, 250), (515, 300), (495, 340),
              (500, 395)]),
    (LTGRAY, [(455, 240), (440, 290), (470, 300)]),
    (LTGRAY, [(230, 330), (225, 390)]), (LTGRAY, [(280, 330), (282, 392)]),
    (LTGRAY, [(360, 330), (362, 392)]), (LTGRAY, [(405, 325), (410, 390)]),
    (LTGRAY, [(172, 260), (140, 300)]),
    (BLACK, [(495, 245), (498, 249)]),
    (YELLOW, [(505, 300), (540, 310)]),
]


def doodle_prog_view(cv, ctx, k):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Doodle")
    cv.text(8, 12, "//This is a drawing program", GREEN)
    total = sum(len(p) - 1 for _, p in DOODLE_STROKES)
    done = k * total
    acc = 0
    cur_xy = None
    with cv.pil() as d:
        for col, pts in DOODLE_STROKES:
            for a, b in zip(pts, pts[1:]):
                if acc >= done:
                    break
                f = clamp01(done - acc)
                x = a[0] + (b[0] - a[0]) * f
                y = a[1] + (b[1] - a[1]) * f
                d.line([a, (x, y)], fill=col, width=7)
                cur_xy = (x, y)
                acc += 1
    # PopUpColor when the color changes
    if 0 < k < 1:
        frac = done - int(done)
        seg = int(done)
        cols = []
        for col, pts in DOODLE_STROKES:
            cols += [col] * (len(pts) - 1)
        if seg < len(cols) and (seg == 0 or cols[seg] != cols[seg - 1]) \
                and frac < 0.8:
            ui.window(cv, 60, 6, 77, 25, "Color", WHITE, BLUE)
            for i in range(16):
                cv.rect(492 + (i % 4) * 30, 64 + (i // 4) * 30, 26, 26, i)
                if i == cols[seg]:
                    cv.frame(490 + (i % 4) * 30, 62 + (i // 4) * 30, 30, 30,
                             RED, 2)
    if cur_xy:
        x, y = cur_xy
        cv.poly([(x, y), (x, y + 14), (x + 4, y + 10), (x + 10, y + 12)],
                BLACK, outline=WHITE)


_TMAP = {}


def talons_map(n=256):
    """A wrap-around height map (the game builds its own from a
    topographic sprite; this one is 1/f noise) and its 16-color look."""
    if not _TMAP:
        rng = np.random.default_rng(1969)
        kx = np.fft.fftfreq(n)[:, None]
        kz = np.fft.fftfreq(n)[None, :]
        k = np.sqrt(kx ** 2 + kz ** 2)
        k[0, 0] = 1.0
        spec = (rng.standard_normal((n, n)) +
                1j * rng.standard_normal((n, n))) / k ** 2.0
        spec[0, 0] = 0
        h = np.real(np.fft.ifft2(spec))
        h = (h - h.min()) / (h.max() - h.min())
        h = h * 170.0 - 55.0
        slope = np.roll(h, -1, 1) - h + (np.roll(h, -1, 0) - h) * 0.5
        lit = slope < 0
        col = np.full((n, n), GREEN, np.uint8)
        col[(h < 0) & ((np.indices((n, n)).sum(0) % 2) == 0)] = BLUE
        col[(h < 0) & ((np.indices((n, n)).sum(0) % 2) == 1)] = LTBLUE
        land = h >= 0
        col[land & (h < 6)] = YELLOW
        g = land & (h >= 6) & (h < 55)
        col[g & lit] = LTGREEN
        col[g & ~lit] = GREEN
        r = land & (h >= 55) & (h < 90)
        col[r & lit] = BROWN
        col[r & ~lit] = DKGRAY
        sn = land & (h >= 90)
        col[sn & lit] = WHITE
        col[sn & ~lit] = LTGRAY
        _TMAP["h"] = np.maximum(h, 0.0)
        _TMAP["c"] = col
        _TMAP["n"] = n
    return _TMAP


CORE_COLS = [(RED, LTRED), (BROWN, YELLOW), (GREEN, LTGREEN), (CYAN, LTCYAN)]


def voxel_terrain(cv, cam_x, cam_z, cam_h, yaw, horizon=170, y_top=20,
                  cores=False, far=420.0, scale_h=260.0):
    """Front-to-back height-field columns (320 wide, doubled)."""
    m = talons_map()
    hm, cm, n = m["h"], m["c"], m["n"]
    ncol = W // 2
    ybuf = np.full(ncol, H, np.int64)
    fx_ = np.linspace(-1.0, 1.0, ncol)
    fwd = (math.sin(yaw), math.cos(yaw))
    right = (math.cos(yaw), -math.sin(yaw))
    cols, y0s, y1s, cs = [], [], [], []
    z, dz = 2.0, 0.6
    while z < far:
        wx = cam_x + fwd[0] * z + right[0] * fx_ * z
        wz = cam_z + fwd[1] * z + right[1] * fx_ * z
        ix = wx.astype(np.int64) % n
        iz = wz.astype(np.int64) % n
        ys = ((cam_h - hm[iz, ix]) / z * scale_h + horizon).astype(np.int64)
        ys = np.clip(ys, y_top, H)
        vis = ys < ybuf
        if vis.any():
            c = cm[iz, ix]
            if cores:
                band = (iz * 4 // n)
                lit = (c == LTGREEN) | (c == WHITE) | (c == BROWN) | \
                    (c == YELLOW) | (c == LTBLUE)
                tint = np.array([[a, b] for a, b in CORE_COLS], np.uint8)
                c = tint[band, lit.astype(int)]
            idx = np.nonzero(vis)[0]
            cols.append(idx)
            y0s.append(ys[idx])
            y1s.append(ybuf[idx])
            cs.append(c[idx])
            ybuf = np.where(vis, ys, ybuf)
        z += dz
        dz *= 1.018
    if not cols:
        return
    col = np.concatenate(cols)
    y0 = np.concatenate(y0s)
    y1 = np.concatenate(y1s)
    c = np.concatenate(cs)
    ln = y1 - y0
    tot = int(ln.sum())
    if tot == 0:
        return
    rep_col = np.repeat(col, ln)
    start = np.repeat(y0 - np.concatenate([[0], np.cumsum(ln)[:-1]]), ln)
    rows = start + np.arange(tot)
    colr = np.repeat(c, ln)
    fb = cv.fb
    fb[rows, rep_col * 2] = colr
    fb[rows, rep_col * 2 + 1] = colr


def talons_bird(cv, x, y, size, t, yaw=0.0, pitch=-0.3, period=0.8):
    """Talons.HC: SpriteInterpolate(Tri(tS,0.2),<2>,<3>), a flapping bird.
    (period slowed so the flap survives 10 frames per second.)"""
    k = tri(t, period)
    key = (TALONS, "flap", round(k, 1))
    if key not in _mesh:
        (va, fa), ramps, r = mesh(TALONS, 2)
        (vb, _), _, _ = mesh(TALONS, 3)
        kk = round(k, 1)
        _mesh[key] = (((1 - kk) * va + kk * vb, fa), ramps, r)
    m, ramps, r = _mesh[key]
    D.render(cv, m, D.view(yaw, pitch), (0, 0, r * 3.0), focal=size * 1.5,
             center=(x, y), ambient=0.35, ramps=ramps, levels=2, cull=False)


def talons_view(cv, t, cores=0.0, bird=True):
    t = step(t, 10)
    fx.vgradient(cv, [LTBLUE, LTCYAN, WHITE], 20, 320)
    cam_z = t * 26.0
    cam_x = 128 + 40 * math.sin(t * 0.21)
    yaw = 0.25 * math.sin(t * 0.3)
    m = talons_map()
    ground = m["h"][int(cam_z) % m["n"], int(cam_x) % m["n"]]
    cam_h = max(ground, 60.0) + 70.0
    voxel_terrain(cv, cam_x, cam_z, cam_h, yaw, cores=cores > 0)
    if bird:
        talons_bird(cv, 430 + 30 * math.sin(t * 0.7), 120 + 10 *
                    math.sin(t * 1.3), 70, t, yaw=math.pi + 0.4)
        talons_bird(cv, 180, 150 + 8 * math.sin(t), 40, t + 0.3,
                    yaw=math.pi - 0.5)
    # Talons.HC's own heads-up display
    cv.rect(0, 0, W, 20, BLACK)
    cv.text(0, 1, "Pitch:%5.1f Roll:%5.1f Heading:%5.1f Height:%5d [Core "
            "Strip:%3d]" % (4.0 * math.sin(t), 9.0 * math.sin(t * 0.7),
                            (90 + math.degrees(yaw)) % 360, int(cam_h * 10),
                            int(t * 7) % 128), WHITE)
    cv.text(0, 11, "Fish Remaining:%d Time:%3.2f Best:%3.2f" % (
        10 - min(9, int(t / 4)), t, 9999.0), YELLOW)
    if cores > 0:
        for i in range(4):
            cv.rect(20 + i * 150, 440, 140, 20, BLACK)
            cv.text(28 + i * 150, 446, "CORE %d" % i, CORE_COLS[i][1])


def bird_view(cv, ctx, t):
    cv.clear(LTCYAN)
    fx.vgradient(cv, [LTBLUE, LTCYAN], 0, H)
    ts = step(t, 10)
    wing = 2 if (int(ts * 3) % 2 == 0) else 3
    draw_mesh(cv, TALONS, wing, D.view(ts * 0.8, -0.35), 320, 250, 300)
    cv.rect(20, 370, 600, 60, WHITE)
    cv.frame(20, 370, 600, 60, BLUE, 2)
    cv.text(32, 380, "::/Demo/Games/Talons.HC  <%d>  (wings %s)" % (
        wing, "up" if wing == 2 else "down"), BLUE)
    cv.text(32, 396, "U0 ClawsDraw(CTask *task,CDC *dc)", CYAN)
    cv.text(32, 410, "ClawDraw(dc,HAND_X-30,HAND_Y-50*claws_up,...", BLACK)


REGISTRY = ["$TR-UL,\"TempleOS\"$", "  $TR,\"EagleDive\"$",
            "    F64 best_score=147.6932;", "  $TR,\"DiningStars\"$",
            "    F64 best_score=9999.0000;", "  $TR,\"CircleTrace\"$",
            "    F64 best_score=4.9425;"]


def registry_box(cv, ctx):
    """::/Demo/AcctExample/Registry.HC: a best score, but no such game."""
    ui.window(cv, 6, 12, 52, 26, "::/Demo/AcctExample/Registry.HC", WHITE,
              BLUE)
    for i, ln in enumerate(REGISTRY):
        hi = i in (1, 2)
        cv.text(64, 116 + i * 10, ln, RED if hi else BLUE)
    if ctx.word_prog() > 0.45:
        cv.rect(64, 196, 300, 12, BLACK)
        cv.text(68, 198, "No file named EagleDive on the disk.", YELLOW)


def flattops_view(cv, t):
    t = step(t, 15)
    cv.clear(BLUE)
    for y in range(0, H, 24):
        for x in range(0, W, 48):
            xx = x + 16 * math.sin(t + y * 0.05)
            cv.rect(xx, y + 10, 10, 1, LTBLUE)
    for n, x, y, ang in ((1, 160, 300, -0.3), (4, 480, 160, 2.8)):
        im = relic_image(FLATTOPS, n, 2.0)
        img = ui.rotate_nearest(im[0], ang)
        cv.blit(img, int(x - img.shape[1] / 2), int(y - img.shape[0] / 2))
    for i in range(5):
        a = t * 0.6 + i * 1.3
        px = 320 + 220 * math.cos(a)
        py = 230 + 140 * math.sin(a * 1.3)
        n = 2 if i % 2 == 0 else 5
        im = relic_image(FLATTOPS, n, 1.5)
        img = ui.rotate_nearest(im[0], -a - math.pi / 2)
        cv.blit(img, int(px - img.shape[1] / 2), int(py - img.shape[0] / 2))
    cv.rect(0, 0, W, 14, BLACK)
    cv.text(8, 3, "FlatTops.HC   Player 1: 5   Player 2: 5   Game Speed: "
            " 1.00", WHITE)
    cv.text(8, 20, "FUEL %3d%%" % int(50 + 50 * math.sin(t * 0.7)), YELLOW,
            bg=BLACK)


def xcal_b17_view(cv, t, part):
    t = step(t, 15)
    if part == 0:
        cv.clear(BLACK)
        fx.STARS.draw(cv, t, speed=0.1)
        for i, n in enumerate((1, 4, 5, 6, 2, 3)):
            a = t * (0.5 + 0.1 * i) + i
            im = relic_image(XCAL, n, 4.0)
            img = ui.rotate_nearest(im[0], a)
            cv.blit(img, int(320 + 200 * math.cos(a) - img.shape[1] / 2),
                    int(240 + 120 * math.sin(1.3 * a) - img.shape[0] / 2))
        if (t % 4) > 2.8:
            cv.dither_rect(0, 0, W, H, BLACK, YELLOW, 0.2)
            cv.text_c(200, "SOLAR STORM", YELLOW, 4)
        cv.text(8, 4, "Level:3 Score:4200 High Score:9001", WHITE)
    else:
        fx.vgradient(cv, [LTBLUE, LTCYAN], 0, 420)
        cv.rect(0, 420, W, 60, GREEN)
        x = (t * 120) % (W + 300) - 150
        im = relic_image(B17, 1, 2.5)
        blit_at(cv, im, x, 140)
        for j in range(6):
            bt = (t * 2 + j * 0.5) % 3.0
            bx = x - 60 - bt * 60
            by = 150 + 0.5 * 90 * bt * bt
            if by < 420:
                blit_at(cv, relic_image(B17, 2, 3.0), bx, by)
            else:
                for r in range(1, 20):
                    cv.circle(bx, 420, r, None, outline=RED if r & 1 else
                              YELLOW)
        cv.text(8, 4, "::/Sup1/Sup1Games/B17.HC", WHITE, bg=BLACK)


def psalmody_view(cv, ctx, t):
    from . import music as M
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Psalmody")
    ui.window(cv, 0, 1, 79, 59, "Psalmody: ::/Sup1/Sup1Hymns/science.HC",
              WHITE, BLUE)
    for i in range(5):  # treble staff: E4 (ona 55) to F5 (ona 68)
        cv.rect(20, 120 + i * 12, 600, 1, BLACK)
    ns, L = M.notes(M.hymn("science"))
    tt = step(t, 15) % L
    for n in ns:
        if not n["ona"]:
            continue
        x = 260 + (n["t"] - tt) * 110
        if -10 < x < 630:
            y = 168 - (n["ona"] - 55) * 3.6
            on = n["t"] <= tt < n["t"] + n["dur"]
            cv.ellipse(x - 6, y - 4, x + 6, y + 4, RED if on else BLACK)
            cv.line(x + 6, y, x + 6, y - 26, BLACK)
    cv.rect(258, 86, 2, 110, RED)
    names = sorted(os.listdir(os.path.join(HERE, "..", "data", "relics",
                                           "Sup1Hymns")))
    off = int(step(t, 4) * 4) % len(names)
    for r in range(20):
        nm = names[(off + r) % len(names)][:-3]
        cv.text(24 + (r % 5) * 120, 240 + (r // 5) * 14, nm[:14], PURPLE)
    cv.text(24, 312, "%d HYMNS ON SUPPLEMENTAL DISK 1" % len(names), BLACK,
            2)


def span_view(cv, t):
    t = step(t, 15)
    fx.vgradient(cv, [LTCYAN, WHITE], 0, 300)
    cv.rect(0, 300, 120, 180, BROWN)
    cv.rect(520, 300, 120, 180, BROWN)
    cv.rect(120, 380, 400, 100, BLUE)
    n = 9
    load_x = 120 + (t * 60) % 400
    pts = []
    for i in range(n):
        x = 120 + i * 50
        sag = 26 * math.sin(math.pi * i / (n - 1)) * (0.8 + 0.2 * math.sin(
            t * 3)) + 30 * math.exp(-((x - load_x) / 60) ** 2)
        pts.append((x, 300 + sag))
    top = [(x, y - 40) for x, y in pts]
    with cv.pil() as d:
        d.line(pts, fill=BLACK, width=3)
        d.line(top, fill=BLACK, width=2)
        for i in range(n):
            d.line([pts[i], top[i]], fill=RED, width=2)
            if i + 1 < n:
                d.line([pts[i], top[i + 1]], fill=LTRED, width=1)
    cv.rect(load_x - 20, pts[min(int((load_x - 120) / 50), n - 1)][1] - 22,
            40, 18, YELLOW)
    cv.text(90, 4, "Cost:%12s" % "12,345.67", BLACK, bg=WHITE)
    cv.text(90, 12, "Time:%12.2f" % t, BLACK, bg=WHITE)
    cv.text(8, 460, "::/Apps/Span", WHITE, bg=BLACK)


LOGIC = "Apps/Logic/Logic.HC"
LOGIC_PROMPTS = [
    "Enter the available gate types in the order you prefer them to be used.",
    "Your choices are:",
    "NOT AND OR NAND NOR XOR AND3 OR3 NAND3 NOR3",
    " Gate: AND", " Gate: OR3", " Gate: ",
    "Table size in hex (3 input=0x100,4=0x10000): 0x100",
    "Enter the hex truth table column values of inputs.",
    "For example, enter A=0xF0, B=0xCC and C=0xAA.",
    "Input A: 0xF0   Input B: 0xCC   Input C: 0xAA",
    "Enter the hex truth table columns values of the outputs.",
    "Output A: 0xE8"]


def logic_view(cv, ctx, t):
    """::/Apps/Logic: majority vote (0xE8) from Terry's own gate symbols."""
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Logic")
    ui.window(cv, 0, 1, 79, 59, "::/Apps/Logic/Logic.HC", WHITE, BLUE)
    k = ctx.since()
    for i, ln in enumerate(LOGIC_PROMPTS):
        if k > i * 0.18:
            cv.text(16, 26 + i * 11, ln, BLUE if i % 3 else BLACK)
    if k < 2.4:
        return
    ins = {"A": 250, "B": 300, "C": 350}
    ands = [(240, 268, "A", "B"), (240, 318, "A", "C"),
            (240, 368, "B", "C")]
    with cv.pil() as d:
        for nm, y in ins.items():
            d.line([(40, y), (120, y)], fill=BLACK)
        for x, y, p, q in ands:
            for yy, src in ((y - 8, p), (y + 8, q)):
                xm = 120 + (ord(src) - 65) * 12
                d.line([(xm, ins[src]), (xm, yy), (x - 72, yy)], fill=RED)
            d.line([(x, y), (360, y), (360, 318 + (y - 318) // 4),
                    (398, 318 + (y - 318) // 4)], fill=RED)
        d.line([(470, 318), (560, 318)], fill=RED)
    for nm, y in ins.items():
        cv.text(24, y - 4, nm, BLACK)
    for x, y, p, q in ands:
        blit_at(cv, relic_image(LOGIC, 2, 2.0), x, y)       # AND
    blit_at(cv, relic_image(LOGIC, 8, 2.0), 470, 318)       # OR3
    cv.text(566, 314, "OUT", RED)
    cv.text(380, 420, "Pass : %d" % (1 + int(max(k - 2.4, 0) * 3) % 9),
            BLACK)


def keepaway_view(cv, t):
    t = step(t, 10)
    fx.vgradient(cv, [LTGRAY, WHITE], 0, 220)
    cv.rect(0, 220, W, 260, GREEN)
    cv.dither_rect(0, 220, W, 260, GREEN, LTGREEN, 0.3)
    for i, n in enumerate((5, 6, 7, 8)):
        try:
            draw_mesh(cv, KEEPAWAY, n, D.view(t * 0.9 + i * 1.6, -0.2),
                      110 + i * 140, 280 + 20 * math.sin(t * 2 + i), 150)
        except (KeyError, IndexError):
            pass
    draw_mesh(cv, KEEPAWAY, 1, D.view(t * 2, 0.3), 320 + 200 * math.sin(
        t * 1.2), 180 - 60 * abs(math.sin(t * 2.4)), 60)
    cv.text(8, 4, "::/Apps/KeepAway  (men from ::/Apps/GrModels)", BLACK,
            bg=WHITE)


def life_view(cv, t):
    cv.clear(BLACK)
    n = int(step(t, 8) * 8)
    g = _life_grid(n)
    h, w = g.shape
    big = np.repeat(np.repeat(g, 4, 0), 4, 1)
    cv.fb[40:40 + big.shape[0], 16:16 + big.shape[1]][big] = LTGREEN
    cv.text(16, 24, "Life.HC", WHITE)
    x0, y0 = 360, 60
    cv.text(x0, 24, "Hanoi.HC", WHITE)
    moves = _hanoi(5)
    k = min(int(step(t, 4) * 4), len(moves))
    pegs = [[5, 4, 3, 2, 1], [], []]
    for a, b in moves[:k]:
        pegs[b].append(pegs[a].pop())
    for p in range(3):
        cv.rect(x0 + 40 + p * 90, y0, 4, 110, BROWN)
        for j, disc in enumerate(pegs[p]):
            ww = disc * 14
            cv.rect(x0 + 42 + p * 90 - ww // 2, y0 + 100 - j * 12, ww, 10,
                    [RED, YELLOW, LTGREEN, LTCYAN, LTPURPLE][disc - 1])
    cv.text(x0, 200, "PredatorPrey.HC", WHITE)
    xs = np.arange(0, 250)
    prey = 60 + 40 * np.sin(xs * 0.06 + t)
    pred = 60 + 40 * np.sin(xs * 0.06 + t - 1.2)
    cv.plot(x0 + xs, 330 - prey, LTGREEN)
    cv.plot(x0 + xs, 330 - pred, LTRED)


_life_cache = {}


def _life_grid(n):
    if not _life_cache:
        rng = np.random.default_rng(3)
        _life_cache[0] = rng.random((96, 84)) < 0.3
    k = max(_life_cache)
    g = _life_cache[k]
    while k < n:
        nb = sum(np.roll(np.roll(g, dy, 0), dx, 1)
                 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                 if (dy, dx) != (0, 0))
        g = (nb == 3) | (g & (nb == 2))
        k += 1
        _life_cache[k] = g
    return _life_cache[n]


def _hanoi(n, a=0, b=2, c=1):
    if n == 0:
        return []
    return _hanoi(n - 1, a, c, b) + [(a, b)] + _hanoi(n - 1, c, b, a)


def fish_view(cv, ctx, t):
    t = step(t, 15)
    fx.vgradient(cv, [BLUE, LTBLUE], 8, H)
    ui.top_bar(cv, ctx.T, task="WallPaperFish")
    for i in range(9):
        n = 1 + (i % 9)
        x = (t * (30 + i * 7) + i * 120) % (W + 80) - 40
        y = 80 + (i * 43) % 320 + 8 * math.sin(t + i)
        blit_at(cv, relic_image(FISH, n, 2.0), x, y)
    for i, (title, body) in enumerate((("Budget", ["Groceries   42.00",
                                                   "Floppies     9.99"]),
                                       ("TimeClock", ["IN  09:00",
                                                      "OUT 17:00"]),
                                       ("VocabQuiz", ["abstruser?",
                                                      "a) more hidden"]))):
        x0 = 4 + i * 26
        ui.window(cv, x0, 44, x0 + 23, 55, title, WHITE, PURPLE)
        for j, ln in enumerate(body):
            cv.text((x0 + 2) * 8, (46 + j) * 8, ln, BLUE)


def sup_view(cv, ctx, t):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Sup1")
    for r in range(8):
        for c in range(8):
            cv.rect(30 + c * 30, 40 + r * 30, 30, 30,
                    BROWN if (r + c) % 2 else YELLOW)
    # Chess.HC: 1-6 wpawn wcastle wknight wbishop wqueen wking, 7-12 black
    back = [2, 3, 4, 5, 6, 4, 3, 2]
    for c in range(8):
        for num, row in ((back[c] + 6, 0), (7, 1), (1, 6), (back[c], 7)):
            img, _, _ = relic_image(CHESS, num, 0.7)
            cv.blit(img, 45 + c * 30 - img.shape[1] // 2,
                    55 + row * 30 - img.shape[0] // 2)
    cv.text(30, 290, "::/Sup1/Sup1Games/Chess.HC", RED)
    ui.window(cv, 36, 5, 78, 40, "::/Sup1/Sup1Blog", WHITE, BLUE)
    files = ["Movies100.DD", "Poems100.DD", "Paintings100.DD",
             "Paintings1000.DD", "Metallica.DD", "YouTube.DD", "Luthur.DD",
             "Temple.DD", "Elephant.DD", "Xeon.DD", "Benchmark.DD"]
    k = ctx.since()
    for i, f in enumerate(files):
        if k > i * 0.25:
            cv.text(300, 60 + i * 20, f, PURPLE if f == "Elephant.DD" else
                    BLUE, 1, sx=1, sy=2)
    cv.text(30, 330, "::/Sup1/Sup1Games/Pilgrims/Pilgrims.HC", RED)
    with cv.pil() as d:
        coast = [(30, 440), (60, 400), (90, 420), (120, 380), (160, 390),
                 (190, 350), (240, 360), (270, 400), (250, 440)]
        d.line(coast, fill=GREEN, width=2)
    blit_at(cv, relic_image("Sup1Games/AfterEgypt/Camp.HC", 7, 0.8), 150,
            420)


CHAT = [("ring0_enjoyer", "F7 F7 F7"), ("holyc_hacker", "\"Hello\\n\";"),
        ("elephant_fan_1969", "more elephants"), ("u0_void", "ZERO size"),
        ("kayak_not_titanic", "reboot is quick"),
        ("ring0_enjoyer", "is ring zero safe?"),
        ("nervous_dev", "will AI replace programmers?"),
        ("formatting_zealot", "tabs or spaces?"),
        ("dolDoc_dan", "SHIFT-F7!"), ("elephant_fan_1969", "elephants")]
COURT_Q = {1: 5, 2: 6, 3: 7}


def court_view(cv, ctx, t, stage):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Court")
    ui.window(cv, 0, 1, 49, 59, "Holding Court", WHITE, BLUE)
    ui.window(cv, 51, 1, 79, 59, "Congregation", BLACK, LTGREEN)
    shown = CHAT[:min(len(CHAT), 5 + stage * 1 + int(ctx.since()))]
    y = 30
    for name, msg in shown[-18:]:
        hi = stage in COURT_Q and CHAT.index((name, msg)) == COURT_Q[stage]
        cv.text(416, y, name[:22], LTGREEN if not hi else YELLOW)
        cv.text(424, y + 9, msg[:24], WHITE if not hi else YELLOW)
        y += 22
    from . import scenes as SC
    SC.spark(cv, t, 200, 120, dist=4.0, focal=220)
    if stage in COURT_Q:
        name, msg = CHAT[COURT_Q[stage]]
        cv.rect(20, 190, 370, 40, BLACK)
        cv.text(28, 198, name + " asks:", YELLOW)
        cv.text(28, 212, msg, WHITE, 2, sx=1, sy=2)
    if stage == 4:
        from . import sprites as S2
        k = ctx.since()
        S2.gavel(cv, 200, 300, 1.2, -1.0 + 1.1 * ease(k / 0.3))
        cv.text_c(380, "COURT IS ADJOURNED", RED, 2, cx=200)
    from .scenes import oracle_overlay
    if stage in (1, 2, 3):
        oracle_overlay(cv, ctx, 250)
    if ctx.cur and ctx.cur.get("tabs"):
        tabs_box(cv, ctx)


def tour_title(cv, t, n, name):
    ui.poster(cv, t, "THE GUIDED TOUR: STOP %d" % n, name, "", n)


def r_tour(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    stop, sit = ctx.sticky("stop", "intro")
    if cur.get("speaker") == "ANNOUNCER" and cur.get("type") == "line":
        n = {"paint": 1, "flight": 2, "misc": 3, "court": 4}.get(stop, 1)
        name = {"paint": "PAINT\nMODE", "flight": "THE FLIGHT\nSIMULATOR",
                "misc": "MISC.\nPROJECTS", "court": "HOLDING\nCOURT"}[stop]
        return tour_title(cv, ctx.since(), n, name)
    if stop == "intro":
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="Tour")
        ui.window(cv, 0, 1, 79, 59, "::/Misc/Tour", WHITE, BLUE)
        ui.window(cv, 10, 14, 70, 32, "Tour", YELLOW, PURPLE)
        cv.text(100, 136, "Press ", BLACK)
        cv.text(148, 136, "<F1>", GREEN)
        cv.text(184, 136, " for the main help index.", BLACK)
        cv.text(100, 156, "The ", BLACK)
        cv.text(132, 156, "<F1>", GREEN)
        cv.text(168, 156, " key works both in the editor and", BLACK)
        cv.text(100, 166, "at the command line.", BLACK)
        cv.text(100, 190, "Press <SHIFT-ESC> to abort and exit.", DKGRAY)
        from . import scenes as SC
        SC.spark(cv, t, 320, 340, dist=4.0, focal=220)
        return
    if stop == "paint":
        if "replay" in cur:
            r = cur["replay"]
            if r == 0:
                k = 0.0
            elif r == 1:
                k = clamp01(ctx.since() / (cur["t2"] - cur["t0"]))
            else:
                k = 1.0
            return replay_view(cv, ctx, k)
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="Ed")
        ui.window(cv, 0, 1, 79, 59, "::/Home/ForGod.DD", WHITE, BLUE)
        cv.text(24, 32, "A drawing for God:", BLUE, 2)
        terry_elephant(cv, 200, 300, t, 0.9)
        if cur.get("menu"):
            k = int(ctx.since() * 2.5) % 20
            sprite_menu(cv, 372, 40, hi=MENU[:20][k], rows=MENU[:20])
            cv.text(372, 280, "<CTRL-r>", GREEN, 2)
        return
    if stop == "doodle":
        p = cur.get("doodle_prog", 0)
        k = 0.0 if p == 0 else (clamp01(ctx.since() / (cur["t2"] -
                                                       cur["t0"]))
                                if p == 1 else 1.0)
        return doodle_prog_view(cv, ctx, k)
    if stop == "flight":
        f, fit = ctx.sticky("flight", "talons")
        ft = t - fit["t0"] if fit else t
        if f == "talons":
            multi = cur.get("tts", "").startswith("The landscape")
            talons_view(cv, t, cores=1.0 if multi and
                        ctx.word_prog() > 0.35 else 0.0)
            if cur.get("registry"):
                registry_box(cv, ctx)
            return
        if f == "bird":
            return bird_view(cv, ctx, ft)
        if f == "flattops":
            return flattops_view(cv, ft)
        if f == "b17":
            return xcal_b17_view(cv, ft, 0 if ctx.word_prog() < 0.55 else 1)
    if stop == "misc":
        p, pit = ctx.sticky("proj", "psalmody")
        pt = t - pit["t0"] if pit else t
        return {"psalmody": lambda: psalmody_view(cv, ctx, pt),
                "span": lambda: span_view(cv, pt),
                "logic": lambda: logic_view(cv, ctx, pt),
                "keepaway": lambda: keepaway_view(cv, pt),
                "life": lambda: life_view(cv, pt),
                "fish": lambda: fish_view(cv, ctx, pt),
                "sup": lambda: sup_view(cv, ctx, pt)}[p]()
    if stop == "court":
        stage, _ = ctx.sticky("court", 0)
        return court_view(cv, ctx, t, stage)


# =====================================================================
# the elephants (chapter VIII)
# =====================================================================

ELE_QUOTE = ("If the purpose of life is to know and love God, then a "
             "priest's job is to make everybody know and love God.  By "
             "saying God likes bears and elephants, I did more toward that "
             "end than all priests in history.")
KOAN = ("The master said to the novice, \"Create a 5-animated-frame "
        "elephant sprite in Gimp with 24-bit color and create a "
        "5-animated-frame elephant sprite in 16 color TempleOS.\"  The "
        "novice said, \"I don't want that 80's crap!\"  The master said, "
        "\"Just do it.\"  The novice did two elephant frames in 24-bit and "
        "was enlightened.")


def elephant_videos():
    with open(os.path.join(HERE, "..", "data", "relics", "Sup1Blog",
                           "YouTube.DD"), encoding="latin-1") as f:
        lines = f.read().split("\n")
    return [lines[i] for i in range(0, len(lines) - 1, 2)
            if "lephant" in lines[i] and "Cage the" not in lines[i]
            and "Sister Mary" not in lines[i]]


GOOD_VIDEOS = {"Baby Elephants Fighting", "BBC: Sunburned Baby Elephant",
               "Elephants Chasing Lions", "Elephant Pool Party"}


def savanna(cv, t):
    """Elephant.HC colors: 31 text rows of LTCYAN, then YELLOW."""
    cv.rect(0, 8, W, 248, LTCYAN)
    cv.rect(0, 256, W, H - 256, YELLOW)


def r_elephants(cv, ctx):
    t = ctx.t
    cur = ctx.cur or {}
    ele, eit = ctx.sticky("ele", "title")
    et = t - eit["t0"] if eit else t
    if ele == "title":
        savanna(cv, t)
        ui.top_bar(cv, ctx.T, task="Elephant")
        terry_elephant(cv, 330, 420, t, 1.3)
        ui.big_title(cv, 40, "THE ELEPHANTS", BLACK, 6, shadow=LTGRAY)
        return
    if ele == "quote":
        savanna(cv, t)
        ui.top_bar(cv, ctx.T, task="HSNotes")
        terry_elephant(cv, 470, 470, t, 0.55)
        S.bear(cv, 130, 470, 0.9, t)
        ui.quote_box(cv, et, ELE_QUOTE, "-- ::/Adam/God/HSNotes.DD",
                     width=32, y=30, title="HSNotes.DD", cps=34)
        return
    if ele == "demo":
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="Elephant")
        savanna(cv, t)
        elephant_scenery(cv, 472, 8, t)
        if cur.get("type") == "line" and cur.get("tts", "").startswith(
                "Two drawings"):
            cv.rect(360, 30, 270, 60, WHITE)
            cv.frame(360, 30, 270, 60, BLUE, 1)
            cv.text(368, 38, "U0 SongTask(I64)", CYAN)
            cv.text(368, 50, "{//Randomly generate (by God :-)", GREEN)
            cv.text(368, 66, "SpriteInterpolate(Tri(tS,2.0),", BLACK)
            cv.text(368, 76, "  <1>,<2>);", BLACK)
        return
    if ele == "walk":
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="ElephantWalk")
        # arrow keys move it 32 pixels at a time
        x = 200 + 32 * int(max(et - 0.8, 0) * 1.6)
        elephant_walk_bitmap(cv, x, 250, et, 1.0, flip=x > 200)
        cv.text(8, 16, "//The sprite was created with <CTRL-r>.", GREEN)
        cv.text(8, 460, "Sprite3ZB(gr.dc,x,y,0,<1>,Sin(8*tS)/4);", BLUE)
        return
    if ele == "koan":
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="Doc")
        ui.window(cv, 0, 1, 79, 59, "::/Sup1/Sup1Blog/Elephant.DD", WHITE,
                  BLUE)
        k = ctx.since(ctx.first("ele", "koan"))
        yy = 36
        budget = int(k * 38)
        for ln in ui.wrap(KOAN, 36):
            cv.text(24, yy, ln[:max(budget, 0)], BLUE, 2, sx=2, sy=2)
            budget -= len(ln) + 1
            yy += 20
        if cur.get("tts", "").startswith("Two frames"):
            for i in range(5):
                x = 70 + i * 120
                cv.frame(x - 55, 322, 110, 110, DKGRAY)
                im = relic_image(ELE, 1, 0.42, elems=ele_frames()[i * 11 // 4],
                                 key=("ele", i * 11 // 4, 0.42))
                blit_at(cv, im, x, 425, ELE_FEET[0] * 0.42,
                        ELE_FEET[1] * 0.42)
                cv.text(x - 40, 326, "FRAME %d" % (i + 1), BLACK)
            cv.text_c(440, "FIVE FRAMES. SIXTEEN COLORS. DONE.", RED, 2)
        return
    if ele == "videos":
        cv.clear(WHITE)
        ui.top_bar(cv, ctx.T, task="Doc")
        ui.window(cv, 0, 1, 79, 59, "::/Sup1/Sup1Blog/YouTube.DD", WHITE,
                  BLUE)
        vids = elephant_videos()
        k = ctx.since()
        for i, v in enumerate(vids):
            if k > i * 0.25:
                good = v in GOOD_VIDEOS
                cv.text(24 + (i // 9) * 300, 36 + (i % 9) * 22, v[:36],
                        RED if good else BLUE, 1, sx=1, sy=2)
        cv.text(24, 250, "%d ELEPHANT VIDEOS OUT OF 754" % len(vids), BLACK,
                2)
        terry_elephant(cv, 470, 450, t, 0.6)
        return
    if ele in ("oracle", "oracle2"):
        savanna(cv, t)
        ui.top_bar(cv, ctx.T, task="God")
        terry_elephant(cv, 330, 470, t, 0.8)
        from .scenes import oracle_overlay
        oracle_overlay(cv, ctx, 60)
        return
    if ele == "counter":
        savanna(cv, t)
        ui.top_bar(cv, ctx.T, task="Elephant")
        terry_elephant(cv, 520, 470, t, 0.5)
        rv = item_with(ctx, "counter_reveal")
        k = ctx.t - rv["t0"] if rv else 0.0
        if k > 0.8:
            n = count_at(ctx.T)
            cv.rect(120, 90, 400, 150, BLACK)
            cv.frame(120, 90, 400, 150, YELLOW, 3)
            cv.text_c(104, "ELEPHANTS SO FAR", YELLOW, 3)
            sc = 8 if k > 1.1 else 5
            cv.text_c(150 if sc == 8 else 162, "%d" % n, WHITE, sc,
                      outline=BLACK)
        return
    if ele == "parade":
        savanna(cv, t)
        ui.top_bar(cv, ctx.T, task="Elephant")
        parade(cv, ctx, eit, y=440, scale=0.45)
        cv.text_c(60, "PARADE OF THE PREFERRED", BLACK, 3)
        return


_EV = {"ev": [], "reveal": None}


def set_events(scenes):
    _EV["ev"] = elephant_events(scenes)
    _EV["reveal"] = reveal_time(scenes)
    return _EV


def count_at(T):
    import bisect
    return bisect.bisect_right(_EV["ev"], T)


def since_last(T):
    import bisect
    i = bisect.bisect_right(_EV["ev"], T)
    return T - _EV["ev"][i - 1] if i else 1e9


# =====================================================================
# more of Terry's drawings: candle, comics, After Egypt, FlapBat
# =====================================================================

def terry_candle(cv, x, y, scale=3.0):
    """night.HC sprite <1>; (x, y) is his (X, Y), where the flame starts."""
    blit_at(cv, relic_image(NIGHT, 1, scale), x, y)


COMICS = {"comic1": "Sup1Games/AfterEgypt/Comics/Moses01.DD",
          "comic2": "Sup1Games/AfterEgypt/Comics/Moses02.DD"}


def comic_view(cv, ctx, which, t):
    """A DolDoc page from the Moses comics: text runs and sprites where
    Terry put them ($WW,1$ word wrap, 8x8 cells)."""
    path = COMICS[which]
    cv.clear(WHITE)
    runs, anchors = R.doldoc_layout(path)
    rows = [r for r, _, _, _ in runs] + [r for r, _, _ in anchors]
    y0 = 24 - max(0, (max(rows) + 14) * 8 - 440) * clamp01(t / 12.0)
    for row, col, n in anchors:
        blit_at(cv, relic_image(path, n), col * 8, y0 + row * 8)
    for row, col, text, color in runs:
        cv.text(col * 8, y0 + row * 8, text.rstrip(), color or BLACK)
    ui.top_bar(cv, ctx.T, task="Doc")
    cv.rect(0, 8, W, 10, BLUE)
    cv.text(4, 9, "::/Sup1/Sup1Games/AfterEgypt/Comics/" +
            path.rsplit("/", 1)[1], WHITE)


MOUNTAIN_FRAMES = (2, 3, 4, 5, 6, 7)


def egypt_view(cv, ctx, t):
    """After Egypt: Mountain.HC's panorama and Moses's walk frames, then
    GodTalking.HC at the bush."""
    fx.vgradient(cv, [LTCYAN, WHITE], 8, 300)
    img, _, _ = relic_image(MOUNTAIN, 1, 1.0)
    cv.blit(img, -4, 300)
    cv.rect(0, 300 + img.shape[0] - 4, W, H, YELLOW)
    ex = ctx.first("exodus")
    it = ctx.first("game", "egypt")
    k = clamp01((t - 0.0) / max(it["t2"] - it["t0"], 1.0)) if it else 1.0
    if ex and ctx.t >= ex["t0"]:
        g = relic_image(GODTALK, 1 + (int(step(ctx.t, 4) * 4) % 2), 2.0)
        cv.blit(g[0], 360, 120)
        blit_at(cv, relic_image(GODTALK, 3, 1.6), 250, 250)
        cv.rect(20, 404, 600, 60, WHITE)
        cv.frame(20, 404, 600, 60, BROWN, 2)
        cv.text(32, 412, "put off thy shoes from off thy feet, for the place",
                BLUE)
        cv.text(32, 424, "whereon thou standest is holy ground.", BLUE)
        cv.text(32, 444, "Exodus 3:5 (King James)", PURPLE)
    else:
        blit_at(cv, relic_image(GODTALK, 3, 1.2), 430, 318)
        fr = MOUNTAIN_FRAMES[int(step(t, 8) * 8) % len(MOUNTAIN_FRAMES)]
        x = 60 + 330 * k
        y = 390 - 60 * k
        blit_at(cv, relic_image(MOUNTAIN, fr, 1.6), x, y)
    cv.text(8, 12, "::/Sup1/Sup1Games/AfterEgypt  (supplemental disk)", BLACK,
            bg=WHITE)


def flapbat_view(cv, t):
    """FlapBat.HC with Terry's four bat frames."""
    fx.vgradient(cv, [BLACK, PURPLE], 0, H)
    for k in range(6):
        x = (k * 200 - t * 120) % 1200 - 100
        gap = 170 + 70 * math.sin(k * 1.9)
        cv.rect(x, 0, 60, gap - 80, GREEN)
        cv.rect(x, gap + 80, 60, H, GREEN)
        cv.frame(x, 0, 60, gap - 80, BLACK)
        cv.frame(x, gap + 80, 60, H - gap - 80, BLACK)
    by = 240 + 70 * math.sin(t * 2.0)
    fr = 1 + int(step(t, 8) * 8) % 4
    img, _, _ = relic_image(FLAPBAT, fr, 3.0)
    cv.blit(img, 200 - img.shape[1] // 2, int(by - img.shape[0] / 2))
    cv.text(8, 8, "FlapBat.HC", WHITE, 1, bg=BLACK)
    cv.text(W - 110, 8, "SCORE: %d" % int(t * 2), YELLOW, 1, bg=BLACK)


def elephant_game_view(cv, t):
    """Chapter VII: Elephant Walk, and a bear for company."""
    cv.clear(WHITE)
    cv.rect(0, 360, W, 120, LTGREEN)
    x = 440 - 32 * int(t * 1.6)
    elephant_walk_bitmap(cv, x, 250, t, 1.0)
    S.bear(cv, x + 190, 380, 0.9, t)
    cv.text(8, 8, "ElephantWalk.HC", WHITE, 1, bg=BLACK)
    cv.text_c(40, "GOD'S FAVORITE ANIMALS", BLUE, 3)


# =====================================================================
# elephant cameos, the jury, the parades, and the counter
# =====================================================================

HIDE_COUNTER = {"ch8_card", "ch8", "ch9_card", "ch9"}


def elephant_events(scenes):
    """Global times of every elephant's entrance, in order. Items say
    elephants=N (optionally ele_dt=offset, ele_stagger=gap)."""
    ev = []
    for sc in scenes:
        for it in sc["items"]:
            n = it.get("elephants")
            if not n:
                continue
            t = sc["start"] + it["t0"] + it.get("ele_dt", 0.0)
            for i in range(n):
                ev.append(t + i * it.get("ele_stagger", 0.0))
    return sorted(ev)


def reveal_time(scenes):
    for sc in scenes:
        for it in sc["items"]:
            if it.get("counter_reveal"):
                return sc["start"] + it["t0"]
    return None


def cameo_walk(cv, t, y=452, scale=0.28, speed=90.0, right=True):
    """A small Terry elephant crossing the frame. At t=0 its nose is at
    the edge of the screen."""
    t = step(t, 15)
    half = 104 * scale
    if right:
        x = -half + speed * t
        flip = True
    else:
        x = W + half - speed * t
        flip = False
    if -half - 10 < x < W + half + 10:
        terry_elephant(cv, x, y, t, scale, flip=flip)


def item_with(ctx, key):
    for it in ctx.items:
        if it.get(key):
            return it
    return None


def cameo_for(cv, ctx, y=452, scale=0.28, right=True):
    """Draw the cameo of the first item in this scene that has one."""
    it = item_with(ctx, "elephants")
    if it is None:
        return
    t = ctx.t - it["t0"] - it.get("ele_dt", 0.0)
    if t >= -2.0:
        cameo_walk(cv, t, y, scale, right=right)


def parade(cv, ctx, it, y=440, scale=0.45, gap=None, speed=110.0):
    """it["elephants"] Terry elephants marching right; elephant i enters
    at ele_dt + i*ele_stagger, when the counter ticks."""
    n = it["elephants"]
    st = it.get("ele_stagger", 0.6) if gap is None else gap
    t0 = it["t0"] + it.get("ele_dt", 0.0)
    half = 104 * scale
    for i in range(n):
        tt = step(ctx.t - t0 - i * st, 15)
        x = -half + speed * tt
        if -half - 10 < x < W + half + 10:
            terry_elephant(cv, x, y - (i % 2) * 28 * scale / 0.45,
                           ctx.t + i * 0.3, scale, flip=True)


def jury_box(cv, t):
    """Three elephants and two bears. It seemed right."""
    cv.rect(150, 160, 340, 150, BROWN)
    cv.frame(150, 160, 340, 150, BLACK, 2)
    cv.text_c(166, "THE JURY", YELLOW, 2, cx=320)
    for i, x in enumerate((215, 320, 425)):
        terry_elephant(cv, x, 270, t + i * 0.5, 0.36, flip=i % 2 == 0)
    for x in (268, 372):
        S.bear(cv, x, 296, 0.8, t)
    cv.rect(150, 282, 340, 28, BROWN)
    cv.frame(150, 282, 340, 28, BLACK, 1)


def counter_badge(cv, n, pop=0.0, x=W - 104, y=12):
    """ELEPHANTS: n, with a tiny Terry elephant."""
    col = YELLOW if pop > 0 else LTGRAY
    cv.rect(x + 3, y + 3, 100, 32, BLACK)
    cv.rect(x, y, 100, 32, BLACK)
    cv.frame(x, y, 100, 32, col, 1)
    terry_elephant(cv, x + 16, y + 29, 0.0, 0.12, flip=True)
    cv.text(x + 32, y + 4, "ELEPHANTS", col)
    cv.text(x + 32, y + 14, "%d" % n, YELLOW if pop > 0 else WHITE, 1,
            sx=2, sy=2)


RISEN_NOTE = ["/*", "This is one of the oldest songs.  I picked",
              "the random name \"risen\" and said to God",
              "\"Oh, you're ambitious,\" thinking it was",
              "an epic name.  He laughed and gave an", "epic song!", "*/"]
RISEN_PLAY = ["Play(\"5eDEqFFetEEFqDeCDDEetCGF\");",
              "Play(\"5eDEqFFetEEFqDeCDDEetCGF\");",
              "Play(\"5eDCqDE4eAA5etEEFEDG4B5DCqF\");",
              "Play(\"5eDCqDE4eAA5etEEFEDG4B5DCqF\");"]


def risen_note_view(cv, ctx):
    cv.clear(WHITE)
    ui.top_bar(cv, ctx.T, task="Ed")
    ui.window(cv, 0, 1, 79, 59, "::/Sup1/Sup1Hymns/risen.HC", WHITE, BLUE)
    k = ctx.since()
    budget = int(k * 30)
    for i, ln in enumerate(RISEN_NOTE):
        cv.text(40, 60 + i * 26, ln[:max(budget, 0)], GREEN, 2, sx=1, sy=2)
        budget -= len(ln) + 1


def theme_view(cv, ctx, t):
    """Terry's own theme (::/Demo/AcctExample/TOS/TOSTheme.HC) plays the
    same four lines as risen.HC, faster, with the same seven birds."""
    cv.clear(LTCYAN)
    ui.top_bar(cv, ctx.T, task="TOSTheme")
    for col, (title, tempo) in enumerate(
            (("::/Sup1/Sup1Hymns/risen.HC", "2.480"),
             ("::/Demo/AcctExample/TOS/TOSTheme.HC", "2.85"))):
        x0 = 12 + col * 314
        cv.rect(x0, 30, 302, 150, WHITE)
        cv.frame(x0, 30, 302, 150, BLUE, 2)
        cv.text(x0 + 6, 36, title[-36:], BLUE)
        cv.text(x0 + 6, 56, "music.tempo= " + tempo + ";", PURPLE)
        cv.text(x0 + 6, 68, "#define BIRDS_NUM\t7".replace("\t", " "), PURPLE)
        for i, ln in enumerate(RISEN_PLAY):
            hi = int(step(t, 2) * 2) % 4 == i
            cv.text(x0 + 6, 92 + i * 16, ln[:37], RED if hi else BLACK)
    k = ctx.since()
    if k > 1.5:
        cv.rect(124, 196, 392, 24, BLACK)
        cv.text_c(200, "SAME NOTES. SAME BIRDS.", YELLOW, 2)
    # the birds, as in both DrawIts
    dt = step(t * 2.85, 15)
    with cv.pil() as d:
        for i in range(7):
            th = math.pi / 2 * i / 7 + 0.2 * math.pi * dt + math.pi / 2
            cx = 320 + 150 * math.cos(th)
            cy = 350 + 60 * math.sin(th)
            wing = math.sin(2 * math.pi * dt + i * 2 * math.pi / 7)
            s = 3.0
            for sgn in (-1, 1):
                d.polygon([(cx, cy - 2 * s), (cx, cy + 2 * s),
                           (cx + sgn * 6 * s * math.cos(wing * 0.9),
                            cy - 6 * s * math.sin(wing * 0.9))], fill=WHITE)
            d.line([(cx, cy - 2 * s), (cx, cy + 2 * s)], fill=LTGRAY)


TIPS_S2T = ("I use spaces-to-tab operations on all my src files to keep "
            "them small.")


def tabs_box(cv, ctx):
    ui.quote_box(cv, ctx.since(), TIPS_S2T, "-- ::/Doc/Tips.DD", width=26,
                 y=28, title="Tips.DD", scale=1, cps=40)
