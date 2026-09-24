"""Tiny 3D: meshes, painter's algorithm, flat shading, ordered dithering.
TempleOS rotates its 3D sprites on the fly; so do we."""
import math

import numpy as np
from PIL import Image, ImageDraw

from .gfx import (BAYER_FULL, BLACK, BLUE, BROWN, DKGRAY, H, LTBLUE, LTCYAN,
                  LTGRAY, LTRED, RED, W, WHITE, YELLOW, dither_ramp)

RAMPS = {
    "gold": [BLACK, BROWN, YELLOW, WHITE],
    "bronze": [BLACK, RED, BROWN, YELLOW],
    "stone": [BLACK, DKGRAY, LTGRAY, WHITE],
    "claude": [BLACK, RED, BROWN, LTRED, YELLOW],
    "blue": [BLACK, BLUE, LTBLUE, LTCYAN, WHITE],
    "white": [DKGRAY, LTGRAY, WHITE],
}


def rot(ax=0.0, ay=0.0, az=0.0):
    cx, sx = math.cos(ax), math.sin(ax)
    cy, sy = math.cos(ay), math.sin(ay)
    cz, sz = math.cos(az), math.sin(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def view(yaw=0.0, pitch=0.0, roll=0.0):
    """Turntable: spin the model about its own vertical axis, then tilt."""
    return rot(ax=pitch) @ rot(az=roll) @ rot(ay=yaw)


class Mesh:
    def __init__(self):
        self.v = []
        self.f = []   # (indices, material)

    def add_box(self, x0, y0, z0, x1, y1, z1, mat):
        b = len(self.v)
        for x in (x0, x1):
            for y in (y0, y1):
                for z in (z0, z1):
                    self.v.append((x, y, z))
        # vertex index = b + ix*4 + iy*2 + iz ; faces wound outward
        q = lambda a, c, d, e: self.f.append(([b + a, b + c, b + d, b + e],
                                              mat))
        q(0, 1, 3, 2)   # x0
        q(4, 6, 7, 5)   # x1
        q(0, 4, 5, 1)   # y0
        q(2, 3, 7, 6)   # y1
        q(0, 2, 6, 4)   # z0
        q(1, 5, 7, 3)   # z1

    def add_prism(self, cx, cz, r, y0, y1, n, mat, r1=None):
        r1 = r if r1 is None else r1
        b = len(self.v)
        for i in range(n):
            a = 2 * math.pi * i / n
            self.v.append((cx + r * math.cos(a), y0, cz + r * math.sin(a)))
            self.v.append((cx + r1 * math.cos(a), y1, cz + r1 * math.sin(a)))
        for i in range(n):
            j = (i + 1) % n
            self.f.append(([b + 2 * i, b + 2 * j, b + 2 * j + 1,
                            b + 2 * i + 1], mat))
        self.f.append(([b + 2 * i for i in range(n)][::-1], mat))
        self.f.append(([b + 2 * i + 1 for i in range(n)], mat))

    def add_poly_extrude(self, pts, z0, z1, mat):
        """Extrude a 2D polygon (x, y) between z0 and z1."""
        b = len(self.v)
        n = len(pts)
        for x, y in pts:
            self.v.append((x, y, z0))
            self.v.append((x, y, z1))
        for i in range(n):
            j = (i + 1) % n
            self.f.append(([b + 2 * i, b + 2 * i + 1, b + 2 * j + 1,
                            b + 2 * j], mat))
        self.f.append(([b + 2 * i for i in range(n)], mat))
        self.f.append(([b + 2 * i + 1 for i in range(n)][::-1], mat))

    def arrays(self):
        return np.array(self.v, dtype=np.float64), self.f


def temple_mesh():
    """Solomon's temple, loosely after 1 Kings 6-7: a platform, the
    house, a tall porch, and the two bronze pillars Jachin and Boaz."""
    m = Mesh()
    m.add_box(-7, -1.2, -7.5, 7, -0.6, 7.5, "stone")
    m.add_box(-6.2, -0.6, -6.7, 6.2, 0.0, 6.7, "stone")
    m.add_box(-3.5, 0.0, -2.5, 3.5, 5.0, 6.0, "gold")        # the house
    m.add_box(-2.2, 5.0, -1.0, 2.2, 5.6, 5.0, "gold")         # clerestory
    m.add_box(-4.2, 0.0, -4.8, 4.2, 7.5, -2.5, "gold")        # the porch
    m.add_box(-1.1, 0.0, -4.85, 1.1, 3.6, -4.7, "bronze")     # doorway
    for x in (-2.9, 2.9):                                     # the pillars
        m.add_prism(x, -6.0, 0.42, 0.0, 5.0, 8, "bronze")
        m.add_prism(x, -6.0, 0.62, 5.0, 5.9, 8, "gold", r1=0.5)
    return m.arrays()


def spark_mesh(rays=12, seed=5):
    """An asterisk of tapered rays, extruded. Claude, approximately."""
    rng = np.random.default_rng(seed)
    m = Mesh()
    for i in range(rays):
        a = 2 * math.pi * i / rays + rng.uniform(-0.08, 0.08)
        L = rng.uniform(0.75, 1.0)
        w0, w1 = 0.13, 0.05
        ca, sa = math.cos(a), math.sin(a)
        px, py = -sa, ca
        pts = [(px * w0, py * w0), (ca * L + px * w1, sa * L + py * w1),
               (ca * L - px * w1, sa * L - py * w1), (-px * w0, -py * w0)]
        m.add_poly_extrude(pts, -0.09, 0.09, "claude")
    return m.arrays()


def render(cv, mesh, R, pos, focal=420.0, center=(W / 2, H / 2),
           light=(-0.4, 0.7, -0.6), ambient=0.28, outline=None,
           ramps=None, gain=1.0, levels=2):
    v, faces = mesh
    ramps = ramps or RAMPS
    cam = v @ R.T + np.asarray(pos, dtype=np.float64)
    z = np.maximum(cam[:, 2], 0.05)
    sx = center[0] + focal * cam[:, 0] / z
    sy = center[1] - focal * cam[:, 1] / z
    L = np.asarray(light, dtype=np.float64)
    L /= np.linalg.norm(L)
    order = []
    for k, (idx, mat) in enumerate(faces):
        p = cam[idx]
        if np.any(p[:, 2] < 0.1):
            continue
        xs, ys = sx[idx], sy[idx]
        area = 0.0
        for i in range(len(idx)):
            j = (i + 1) % len(idx)
            area += xs[i] * ys[j] - xs[j] * ys[i]
        if area <= 0:  # back face (screen y points down)
            continue
        nrm = np.cross(p[1] - p[0], p[2] - p[0])
        nn = np.linalg.norm(nrm)
        if nn == 0:
            continue
        nrm /= nn
        if nrm @ p[0] > 0:  # visible faces face the camera
            nrm = -nrm
        lit = ambient + (1 - ambient) * max(0.0, float(nrm @ L))
        lit = min(lit * gain, 1.0)
        if levels:
            q = (len(ramps[mat]) - 1) * levels
            lit = round(lit * q) / q
        order.append((float(p[:, 2].mean()), k, lit))
    if not order:
        return None
    order.sort(reverse=True)
    idimg = Image.new("I", (W, H), 0)
    d = ImageDraw.Draw(idimg)
    lvl = np.zeros(len(order) + 1)
    mats = [None]
    for n, (_, k, lit) in enumerate(order, start=1):
        idx, mat = faces[k]
        d.polygon([(float(sx[i]), float(sy[i])) for i in idx], fill=n)
        lvl[n] = lit
        mats.append(mat)
    ids = np.asarray(idimg)
    hit = ids > 0
    if not hit.any():
        return None
    ids_h = ids[hit]
    th = BAYER_FULL[hit]
    out = np.zeros(ids_h.shape, np.uint8)
    mat_arr = np.array([m or "" for m in mats])
    per_pix_mat = mat_arr[ids_h]
    for mname in set(mats[1:]):
        sel = per_pix_mat == mname
        out[sel] = dither_ramp(lvl[ids_h[sel]], ramps[mname], th[sel])
    cv.fb[hit] = out
    if outline is not None:
        with cv.pil() as dd:
            for _, k, _ in order:
                idx, _ = faces[k]
                pts = [(float(sx[i]), float(sy[i])) for i in idx]
                dd.line(pts + [pts[0]], fill=outline, width=1)
    return hit
