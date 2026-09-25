"""Terry's own sprites, read from the DolDoc binary section of his files.

A DolDoc file is text, a NUL, then entries of CDocBin (U32 num, flags,
size, use_cnt) followed by `size` bytes of sprite elements
(::/Adam/Gr/Gr.HH, sizes from ::/Adam/Gr/SpriteNew.HC; HolyC classes are
packed). The git mirror we read from turned some CR LF pairs inside the
binary data into LF. Every element has a known size, so we put the CRs
back wherever that makes the element stream parse to exactly `size`.
"""
import itertools
import math
import os
import struct

import numpy as np
from PIL import Image, ImageDraw

TEMPLEOS = os.environ.get("TEMPLEOS_SRC", "/home/user/cia-foundation/templeos")

(SPT_END, SPT_COLOR, SPT_DITHER_COLOR, SPT_THICK, SPT_PLANAR_SYMMETRY,
 SPT_TRANSFORM_ON, SPT_TRANSFORM_OFF, SPT_SHIFT, SPT_PT, SPT_POLYPT,
 SPT_LINE, SPT_POLYLINE, SPT_RECT, SPT_ROTATED_RECT, SPT_CIRCLE,
 SPT_ELLIPSE, SPT_POLYGON, SPT_BSPLINE2, SPT_BSPLINE2_CLOSED, SPT_BSPLINE3,
 SPT_BSPLINE3_CLOSED, SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT, SPT_BITMAP,
 SPT_MESH, SPT_SHIFTABLE_MESH, SPT_ARROW, SPT_TEXT, SPT_TEXT_BOX,
 SPT_TEXT_DIAMOND) = range(30)

BASE = [1, 2, 3, 5, 17, 1, 1, 9, 9, 13, 17, 5, 17, 25, 13, 25, 29, 5, 5, 5,
        5, 9, 9, 17, 9, 21, 17, 9, 9, 9]
TRANSPARENT = 0xFF


def elem_size(buf, p):
    """Size of the element at p, or None if it can't be one."""
    if p >= len(buf):
        return None
    t = buf[p] & 0x7F
    if t >= len(BASE):
        return None
    n = BASE[t]
    if p + n > len(buf):
        return None
    i32 = lambda o: struct.unpack_from("<i", buf, p + o)[0]
    if t == SPT_POLYLINE:
        k = i32(1)
        if not 0 < k < 4096:
            return None
        n += k * 8
    elif t in (SPT_TEXT, SPT_TEXT_BOX, SPT_TEXT_DIAMOND):
        z = buf.find(b"\0", p + 9)
        if z < 0:
            return None
        n = z + 1 - p
    elif t == SPT_BITMAP:
        w, h = i32(9), i32(13)
        if not (0 < w < 1024 and 0 < h < 1024):
            return None
        n += ((w + 7) & ~7) * h
    elif t == SPT_POLYPT:
        k = i32(1)
        if not 0 < k < 65536:
            return None
        n += (k * 3 + 7) >> 3
    elif t in (SPT_BSPLINE2, SPT_BSPLINE3, SPT_BSPLINE2_CLOSED,
               SPT_BSPLINE3_CLOSED):
        k = i32(1)
        if not 0 < k < 4096:
            return None
        n += k * 12
    elif t == SPT_MESH:
        v, tr = i32(1), i32(5)
        if not (0 < v < 65536 and 0 < tr < 65536):
            return None
        n += v * 12 + tr * 16
    elif t == SPT_SHIFTABLE_MESH:
        v, tr = i32(13), i32(17)
        if not (0 < v < 65536 and 0 < tr < 65536):
            return None
        n += v * 12 + tr * 16
    return n


def plausible(buf, p, t):
    """Reject elements with absurd coordinates (a sign of misalignment)."""
    if t in (SPT_PT, SPT_SHIFT, SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT, SPT_LINE,
             SPT_RECT, SPT_ARROW, SPT_CIRCLE, SPT_PLANAR_SYMMETRY):
        vals = struct.unpack_from("<ii", buf, p + 1)
        return all(abs(v) < 4000 for v in vals)
    if t == SPT_COLOR:
        return buf[p + 1] < 16
    if t == SPT_THICK:
        return 0 <= struct.unpack_from("<i", buf, p + 1)[0] < 64
    return True


def walk(buf):
    """Element offsets if buf is exactly one valid element stream."""
    p, offs = 0, []
    while True:
        n = elem_size(buf, p)
        if n is None:
            return None
        t = buf[p] & 0x7F
        if not plausible(buf, p, t):
            return None
        offs.append(p)
        if t == SPT_END:
            return offs if p + 1 == len(buf) else None
        p += n


def repair(raw, size):
    """Re-insert CR bytes before some LF bytes so walk() succeeds."""
    missing = size - len(raw)
    if missing == 0:
        return raw if walk(raw) is not None else None
    lfs = [i for i, b in enumerate(raw) if b == 0x0A]
    for combo in itertools.combinations(lfs, missing):
        b = bytearray()
        last = 0
        for i in combo:
            b += raw[last:i] + b"\r"
            last = i
        b += raw[last:]
        if walk(bytes(b)) is not None:
            return bytes(b)
    return None


ISO_PATH = os.environ.get("TEMPLEOS_ISO",
                          "/home/user/templeos_iso/TempleOS.ISO")
_iso = None


RELIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                         "data", "relics")


def from_iso(relpath):
    """Exact bytes of one of Terry's files: data/relics/ if extracted
    (see MANIFEST.txt), else straight from TempleOS.ISO (tosiso.py)."""
    global _iso
    local = os.path.join(RELIC_DIR, relpath)
    if os.path.exists(local):
        with open(local, "rb") as f:
            return f.read()
    if _iso is None:
        from .tosiso import ISO
        _iso = ISO(ISO_PATH)
    return _iso.get(relpath)


_sprite_cache = {}


def sprite(relpath, num):
    key = (relpath, num)
    if key not in _sprite_cache:
        _sprite_cache[key] = sprites(relpath)[num]
    return _sprite_cache[key]


def mesh_of(relpath, num):
    """A sprite's SPT_MESH as (vertices, [(tri, color)]) for three_d."""
    for e in sprite(relpath, num):
        if e[0] in (SPT_MESH, SPT_SHIFTABLE_MESH):
            vs = e[1].astype(float)
            tris = [((int(a), int(b), int(c)), int(col))
                    for col, a, b, c in e[2]]
            return vs, tris
    raise KeyError((relpath, num))


def doldoc_layout(relpath):
    """Text runs and sprite anchors of a DolDoc page (comics, blog).
    Returns ([(row, col, text, color)], [(row, col, bin_num)])."""
    import re
    data = from_iso(relpath)
    z = data.find(b"\0")
    text = (data[:z] if z >= 0 else data).decode("latin-1")
    runs, anchors = [], []
    color = 0
    for row, line in enumerate(text.split("\n")):
        col = 0
        pos = 0
        for m in re.finditer(r"\$([^$]*)\$", line):
            seg = line[pos:m.start()]
            if seg:
                runs.append((row, col, seg, color))
                col += len(seg)
            cmd = m.group(1)
            if cmd.startswith("FG,"):
                color = int(cmd[3:].split(",")[0]) & 15
            elif cmd == "FG":
                color = 0
            elif cmd.startswith("SP,"):
                bi = re.search(r"BI=(\d+)", cmd)
                if bi:
                    anchors.append((row, col, int(bi.group(1))))
            pos = m.end()
        seg = line[pos:]
        if seg.strip():
            runs.append((row, col, seg, color))
    return runs, anchors


def parse_bins(data):
    """DocLoad: text, NUL, then CDocBin headers each followed by data."""
    z = data.index(b"\0")
    p = z + 1
    out = {}
    while p + 16 <= len(data):
        n, f, s, u = struct.unpack_from("<IIII", data, p)
        buf = data[p + 16:p + 16 + s]
        if walk(buf) is None:
            raise ValueError("bin %d does not parse" % n)
        out[n] = buf
        p += 16 + s
    return out


def sprites(relpath):
    """Decoded sprites {num: elements} straight from the ISO."""
    return {n: elements(b) for n, b in parse_bins(from_iso(relpath)).items()}


def load_bins(relpath):
    """{bin_num: element bytes} recovered from the git mirror's copy."""
    data = open(os.path.join(TEMPLEOS, relpath), "rb").read()
    z = data.index(b"\0")
    heads = []
    for off in range(z + 1, len(data) - 16):
        n, f, s, u = struct.unpack_from("<IIII", data, off)
        if 1 <= n <= 64 and f == 0 and 8 < s < 200000 and 1 <= u <= 64:
            heads.append((off, n, s))
    out = {}
    for i, (off, n, s) in enumerate(heads):
        end = heads[i + 1][0] if i + 1 < len(heads) else len(data)
        raw = data[off + 16:end]
        if len(raw) > s:
            raw = raw[:s]
        fixed = repair(raw, s)
        if fixed is not None:
            out[n] = fixed
    return out


def elements(buf):
    """Decode into (type, fields) tuples."""
    out = []
    for p in walk(buf):
        t = buf[p] & 0x7F
        i32 = lambda o: struct.unpack_from("<i", buf, p + o)[0]
        if t == SPT_COLOR:
            out.append((t, buf[p + 1]))
        elif t == SPT_DITHER_COLOR:
            out.append((t, struct.unpack_from("<H", buf, p + 1)[0]))
        elif t == SPT_THICK:
            out.append((t, i32(1)))
        elif t in (SPT_PT, SPT_SHIFT, SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT):
            out.append((t, i32(1), i32(5)))
        elif t in (SPT_LINE, SPT_RECT, SPT_ARROW, SPT_PLANAR_SYMMETRY):
            out.append((t, i32(1), i32(5), i32(9), i32(13)))
        elif t == SPT_CIRCLE:
            out.append((t, i32(1), i32(5), i32(9)))
        elif t in (SPT_ELLIPSE, SPT_POLYGON):
            ang = struct.unpack_from("<d", buf, p + 17)[0]
            sides = i32(25) if t == SPT_POLYGON else 0
            out.append((t, i32(1), i32(5), i32(9), i32(13), ang, sides))
        elif t == SPT_ROTATED_RECT:
            ang = struct.unpack_from("<d", buf, p + 17)[0]
            out.append((t, i32(1), i32(5), i32(9), i32(13), ang))
        elif t == SPT_POLYLINE:
            k = i32(1)
            pts = struct.unpack_from("<%di" % (2 * k), buf, p + 5)
            out.append((t, list(zip(pts[::2], pts[1::2]))))
        elif t in (SPT_BSPLINE2, SPT_BSPLINE3, SPT_BSPLINE2_CLOSED,
                   SPT_BSPLINE3_CLOSED):
            k = i32(1)
            pts = struct.unpack_from("<%di" % (3 * k), buf, p + 5)
            out.append((t, list(zip(pts[::3], pts[1::3]))))
        elif t == SPT_POLYPT:
            k, x, y = i32(1), i32(5), i32(9)
            bits = int.from_bytes(buf[p + 13:p + 13 + ((k * 3 + 7) >> 3)],
                                  "little")
            pts = [(x, y)]
            for j in range(k):
                code = (bits >> (3 * j)) & 7
                d = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1),
                     (0, 1), (1, 1)][code]
                x, y = x + d[0], y + d[1]
                pts.append((x, y))
            out.append((t, pts))
        elif t == SPT_BITMAP:
            x, y, w, h = i32(1), i32(5), i32(9), i32(13)
            ww = (w + 7) & ~7
            px = np.frombuffer(buf, np.uint8, ww * h, p + 17).reshape(h, ww)
            out.append((t, x, y, px[:, :w].copy()))
        elif t in (SPT_TEXT, SPT_TEXT_BOX, SPT_TEXT_DIAMOND):
            z = buf.index(b"\0", p + 9)
            out.append((t, i32(1), i32(5), buf[p + 9:z].decode("latin-1")))
        elif t in (SPT_MESH, SPT_SHIFTABLE_MESH):
            o = 1 if t == SPT_MESH else 13
            v, tr = i32(o), i32(o + 4)
            vs = np.frombuffer(buf, "<i4", v * 3, p + o + 8).reshape(v, 3)
            ts = np.frombuffer(buf, "<i4", tr * 4, p + o + 8 + v * 12
                               ).reshape(tr, 4)
            out.append((t, vs.copy(), ts.copy()))
        else:
            out.append((t,))
    return out


def bspline(ctrl, closed=False, steps=10):
    """Uniform cubic B-spline through the control polygon."""
    P = np.array(ctrl, float)
    if len(P) < 3:
        return [tuple(p) for p in P]
    if closed:
        P = np.vstack([P, P[:3]])
    else:
        P = np.vstack([P[:1], P[:1], P, P[-1:], P[-1:]])
    out = []
    for i in range(len(P) - 3):
        p0, p1, p2, p3 = P[i:i + 4]
        for s in np.linspace(0, 1, steps, endpoint=False):
            b0 = (1 - s) ** 3 / 6
            b1 = (3 * s ** 3 - 6 * s ** 2 + 4) / 6
            b2 = (-3 * s ** 3 + 3 * s ** 2 + 3 * s + 1) / 6
            b3 = s ** 3 / 6
            out.append(tuple(b0 * p0 + b1 * p1 + b2 * p2 + b3 * p3))
    if not closed:
        out.append(tuple(P[-1]))
    return out


def interpolate(ea, eb, k):
    """::/Adam/Gr/SpriteNew.HC SpriteInterpolate: same shape, blended."""
    out = []
    for a, b in zip(ea, eb):
        if a[0] != b[0] or len(a) != len(b):
            out.append(a)
            continue
        t = a[0]
        if t in (SPT_POLYLINE, SPT_BSPLINE2, SPT_BSPLINE3,
                 SPT_BSPLINE2_CLOSED, SPT_BSPLINE3_CLOSED, SPT_POLYPT):
            if len(a[1]) != len(b[1]):
                out.append(a)
                continue
            pts = [(pa[0] + (pb[0] - pa[0]) * k, pa[1] + (pb[1] - pa[1]) * k)
                   for pa, pb in zip(a[1], b[1])]
            out.append((t, pts))
        elif t in (SPT_PT, SPT_SHIFT, SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT,
                   SPT_LINE, SPT_RECT, SPT_ARROW, SPT_CIRCLE, SPT_ELLIPSE,
                   SPT_POLYGON, SPT_ROTATED_RECT):
            vals = tuple(va + (vb - va) * k if isinstance(va, (int, float))
                         else va for va, vb in zip(a[1:], b[1:]))
            out.append((t,) + vals)
        else:
            out.append(a)
    return out


def draw(fb, elems, x0, y0, scale=1.0, flip=False, default_color=0,
         clip=None):
    """Render decoded elements onto a (H, W) index framebuffer, the way
    Sprite3 would: color and thickness are state, fills are flood fills."""
    H, W = fb.shape
    img = Image.fromarray(fb)
    d = ImageDraw.Draw(img)
    color = default_color
    thick = 1
    ox = oy = 0.0
    sgn = -1.0 if flip else 1.0

    def P(x, y):
        return (x0 + sgn * (x + ox) * scale, y0 + (y + oy) * scale)

    def lw():
        return max(1, int(round(thick * scale)))

    for e in elems:
        t = e[0]
        if t == SPT_COLOR:
            color = e[1] & 15
        elif t == SPT_DITHER_COLOR:
            color = e[1] & 15
        elif t == SPT_THICK:
            thick = max(e[1], 1)
        elif t == SPT_SHIFT:
            ox += e[1]
            oy += e[2]
        elif t == SPT_PT:
            d.point(P(e[1], e[2]), fill=color)
        elif t == SPT_LINE or t == SPT_ARROW:
            d.line([P(e[1], e[2]), P(e[3], e[4])], fill=color, width=lw())
        elif t == SPT_RECT:
            a, b = P(e[1], e[2]), P(e[3], e[4])
            d.rectangle([min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]),
                         max(a[1], b[1])], fill=color)
        elif t == SPT_CIRCLE:
            cx, cy = P(e[1], e[2])
            r = e[3] * scale
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color,
                      width=lw())
        elif t == SPT_ELLIPSE or t == SPT_POLYGON:
            cx, cy = e[1], e[2]
            w, h, ang = e[3], e[4], e[5]
            n = e[6] if t == SPT_POLYGON else 48
            pts = []
            for j in range(n + 1):
                a = 2 * math.pi * j / n
                px, py = w * math.cos(a), h * math.sin(a)
                pts.append(P(cx + px * math.cos(ang) - py * math.sin(ang),
                             cy + px * math.sin(ang) + py * math.cos(ang)))
            d.line(pts, fill=color, width=lw())
        elif t == SPT_POLYLINE or t == SPT_POLYPT:
            d.line([P(x, y) for x, y in e[1]], fill=color, width=lw())
        elif t in (SPT_BSPLINE2, SPT_BSPLINE3, SPT_BSPLINE2_CLOSED,
                   SPT_BSPLINE3_CLOSED):
            closed = t in (SPT_BSPLINE2_CLOSED, SPT_BSPLINE3_CLOSED)
            pts = [P(x, y) for x, y in bspline(e[1], closed)]
            d.line(pts, fill=color, width=lw())
        elif t in (SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT):
            px, py = P(e[1], e[2])
            px, py = int(round(px)), int(round(py))
            if 0 <= px < W and 0 <= py < H:
                if t == SPT_FLOOD_FILL:
                    ImageDraw.floodfill(img, (px, py), color)
                else:
                    ImageDraw.floodfill(img, (px, py), color, border=color)
        elif t == SPT_BITMAP:
            bx, by = P(e[1], e[2])
            bm = e[3]
            if scale != 1.0:
                hh = max(1, int(bm.shape[0] * scale))
                ww = max(1, int(bm.shape[1] * scale))
                yi = (np.arange(hh) / scale).astype(int)
                xi = (np.arange(ww) / scale).astype(int)
                bm = bm[yi][:, xi]
            if flip:
                bm = bm[:, ::-1]
                bx -= bm.shape[1]
            arr = np.asarray(img).copy()
            x1, y1 = int(bx), int(by)
            hh, ww = bm.shape
            xa, ya = max(x1, 0), max(y1, 0)
            xb, yb = min(x1 + ww, W), min(y1 + hh, H)
            if xb > xa and yb > ya:
                sub = bm[ya - y1:yb - y1, xa - x1:xb - x1]
                reg = arr[ya:yb, xa:xb]
                m = sub != TRANSPARENT
                reg[m] = sub[m] & 15
                img = Image.fromarray(arr)
                d = ImageDraw.Draw(img)
        elif t in (SPT_TEXT, SPT_TEXT_BOX, SPT_TEXT_DIAMOND):
            pass
    fb[:] = np.asarray(img)


def bounds(elems):
    xs, ys = [], []
    for e in elems:
        t = e[0]
        if t in (SPT_POLYLINE, SPT_POLYPT, SPT_BSPLINE2, SPT_BSPLINE3,
                 SPT_BSPLINE2_CLOSED, SPT_BSPLINE3_CLOSED):
            xs += [p[0] for p in e[1]]
            ys += [p[1] for p in e[1]]
        elif t in (SPT_LINE, SPT_RECT, SPT_ARROW):
            xs += [e[1], e[3]]
            ys += [e[2], e[4]]
        elif t in (SPT_PT, SPT_FLOOD_FILL, SPT_FLOOD_FILL_NOT):
            xs.append(e[1])
            ys.append(e[2])
        elif t == SPT_CIRCLE:
            xs += [e[1] - e[3], e[1] + e[3]]
            ys += [e[2] - e[3], e[2] + e[3]]
        elif t == SPT_BITMAP:
            xs += [e[1], e[1] + e[3].shape[1]]
            ys += [e[2], e[2] + e[3].shape[0]]
    if not xs:
        return (0, 0, 0, 0)
    return (min(xs), min(ys), max(xs), max(ys))
