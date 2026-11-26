"""Pistols and submachine guns: Glock 17, M1911A1, MP5A3, UMP-45.

Each is built after the real gun, part by part: chamfered slides with cut serrations and ejection ports, pins
and levers standing proud of the frame, sights as geometry, magazines complete with feed lips and a round (they
drop out whole on a reload). The helpers below add what the kit lacks: boxes in a raked frame (grips and
magazines), round bars along the vertical and sideways axes, chamfered top edges and serrated blocks.
"""
from __future__ import annotations

import math

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, knurl, mag_bones, qd_cup, roll_mark, sling_swivel
from kit import FACES, GRIP, LOW, paint


# =========================================================================== helpers

class Raked:
    """Boxes placed in a frame turned `tilt` degrees about the sideways axis through `pivot` (a raked grip or a
    magazine): coordinates are given as if the part stood upright. `extra` turns a box further about its own
    centre (a 45-degree `extra` on a 1x1 bar makes a chamfer along a sideways edge)."""

    def __init__(self, g, tilt, pivot):
        self.g, self.tilt, self.pivot = g, tilt, pivot

    def to_world(self, f, u):
        th = math.radians(self.tilt)
        pf, pu = self.pivot
        df, du = f - pf, u - pu
        return pf + df * math.cos(th) - du * math.sin(th), pu + df * math.sin(th) + du * math.cos(th)

    def box(self, f0, f1, u0, u1, s0, s1, color, noise=3, extra=0.0, **kw):
        if not extra:
            return self.g.box(f0, f1, u0, u1, s0, s1, color, noise, tilt=self.tilt, pivot=self.pivot, **kw)
        wf, wu = self.to_world((f0 + f1) / 2, (u0 + u1) / 2)
        hf, hu = (f1 - f0) / 2, (u1 - u0) / 2
        return self.g.box(wf - hf, wf + hf, wu - hu, wu + hu, s0, s1, color, noise, tilt=self.tilt + extra,
                          pivot=(wf, wu), **kw)

    def vedge(self, f, s, u0, u1, color, t=1.0, noise=2, **kw):
        """A chamfer strip along the raked frame's upright axis at the corner (f, s), from u0 to u1."""
        cf, cu = self.to_world(f, (u0 + u1) / 2)
        h = (u1 - u0) / 2
        infl = (t * math.sqrt(2) - 1) / 2
        rot = euler(_mul(_rm(self.tilt, 0, 0), _rm(0, 0, 45)))
        return rbox(self.g, cf - 0.5, cf + 0.5, cu - h, cu + h, s - 0.5, s + 0.5, color, rot, (cf, cu, s), noise,
                    infl, **kw)

    def pin(self, f, u, s0, s1, r, color, noise=1, **kw):
        """A cross pin (along s) at a point of the raked frame."""
        wf, wu = self.to_world(f, u)
        return spin(self.g, wf, wu, s0, s1, r, color, noise, **kw)


def _rm(rx, ry, rz):
    """The model-space matrix of a Bedrock cube rotation (x, then y, then z; x and z left-handed)."""
    ax, ay, az = math.radians(-rx), math.radians(ry), math.radians(-rz)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    mx = [[1, 0, 0], [0, cx, -sx], [0, sx, cx]]
    my = [[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]
    mz = [[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]
    return _mul(mz, _mul(my, mx))


def _mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def euler(m):
    """The Bedrock rotation (x, y, z) in degrees of a model-space rotation matrix: lets a box turn about an axis
    of a part that is itself turned (an edge chamfer on a raked grip)."""
    b = math.asin(max(-1.0, min(1.0, -m[2][0])))
    a = math.atan2(m[2][1], m[2][2])
    c = math.atan2(m[1][0], m[0][0])
    return (round(-math.degrees(a), 3), round(math.degrees(b), 3), round(-math.degrees(c), 3))


def rbox(g, f0, f1, u0, u1, s0, s1, color, rot, pivot=None, noise=3, inflate=0.0, bone=None):
    """A box turned by `rot` = (about s, about f, about u) degrees about `pivot` (f, u, s). The kit's box turns
    about s and f; this one also turns about the vertical axis (round posts, vertical chamfers)."""
    size = (max(1, round(s1 - s0)), max(1, round(f1 - f0)), max(1, round(u1 - u0)))
    origin = (GRIP[0] + s0, GRIP[1] + f0, GRIP[2] - (u0 + size[2]))
    pf, pu, ps = pivot if pivot else ((f0 + f1) / 2, (u0 + u1) / 2, (s0 + s1) / 2)
    target = g.bones[bone] if bone else g.cur
    c = target.cube(origin, size, inflate, tuple(rot), g.at(pf, pu, ps))
    c.ext = (f0, f0 + size[1], u0, u0 + size[2], s0, s0 + size[0])
    paint(c, color, noise, g.seed + len(target.cubes) * 7)
    return c


def vrod(g, u0, u1, cf, cs, r, color, noise=2, bone=None, facets=None):
    """A round bar standing along u (a post, a knob, a drum): square boxes turned evenly about the vertical."""
    n = facets or (4 if r >= 2.75 else 3 if r >= 1.75 else 2 if r >= 0.9 else 1)
    size = max(1, round(2 * r))
    infl = r - size / 2
    out = []
    for i in range(n):
        ang = 90.0 * i / n
        c = rbox(g, cf - size / 2, cf + size / 2, u0, u1, cs - size / 2, cs + size / 2, color,
                 (0, 0, ang), (cf, (u0 + u1) / 2, cs), noise, infl, bone)
        if i:
            for face in c.sides:
                face.fill(shade(color, 0.92 if i % 2 else 1.06))
        out.append(c)
    return out


def spin(g, cf, cu, s0, s1, r, color, noise=1, bone=None, facets=None):
    """A round bar across the gun (along s): a pin, a hinge, a sight drum's axle."""
    n = facets or (3 if r >= 1.75 else 2 if r >= 0.7 else 1)
    size = max(1, round(2 * r))
    infl = r - size / 2
    out = []
    for i in range(n):
        ang = 90.0 * i / n
        c = g.box(cf - size / 2, cf + size / 2, cu - size / 2, cu + size / 2, s0, s1, color, noise, inflate=infl,
                  tilt=ang, pivot=(cf, cu), bone=bone)
        out.append(c)
    return out


def edge(g, f0, f1, cu, cs, color, t=1.0, noise=2, bone=None):
    """A chamfer strip along f whose diamond section reaches t units from (cu, cs) along u and s."""
    infl = (t * math.sqrt(2) - 1) / 2
    return g.box(f0, f1, cu - 0.5, cu + 0.5, cs - 0.5, cs + 0.5, color, noise, inflate=infl, roll=45,
                 pivot=(0, cu, cs), bone=bone)


def cham(g, f0, f1, u0, u1, s0, s1, color, t=1.0, b=0.0, noise=3, bone=None, light=1.2, sides=("l", "r")):
    """A block with its top long edges (and with `b`, its bottom ones) chamfered: a body, a narrower cap and a
    45-degree strip along each chamfered edge. Returns the body (the box whose sides carry markings)."""
    body = g.box(f0, f1, u0 + b, u1 - t, s0, s1, color, noise, bone=bone)
    if t:
        g.box(f0, f1, u1 - t, u1, s0 + t, s1 - t, color, noise, bone=bone)
        if "l" in sides:
            edge(g, f0, f1, u1 - t, s1 - t, shade(color, light), t, bone=bone)
        if "r" in sides:
            edge(g, f0, f1, u1 - t, s0 + t, shade(color, light), t, bone=bone)
    if b:
        g.box(f0, f1, u0, u0 + b, s0 + b, s1 - b, color, noise, bone=bone)
        edge(g, f0, f1, u0 + b, s1 - b, shade(color, 0.8), b, bone=bone)
        edge(g, f0, f1, u0 + b, s0 + b, shade(color, 0.8), b, bone=bone)
    return body


def ridges(g, f0, f1, u0, u1, s0, s1, color, pitch=1.5, depth=0.5, groove=None, bone=None):
    """Serrations cut across a block: a core `depth` narrower each side and full-width ridges `pitch` apart,
    with grooves (pitch - 1 wide) between them."""
    g.box(f0, f1, u0, u1, s0 + depth, s1 - depth, groove or shade(color, 0.55), 1, bone=bone)
    out = []
    f = f0
    while f + 1 <= f1 + 1e-6:
        out.append(g.box(f, f + 1, u0, u1, s0, s1, color, 2, bone=bone))
        f += pitch
    return out


def endmark(c, end, s0, s1, u0, u1, color):
    """Paint a rectangle onto the front (muzzle-facing) or rear end of a box."""
    bf0, bf1, bu0, bu1, bs0, bs1 = c.ext
    r = lambda v: int(math.floor(v + 0.5))
    x0, x1 = r(s0 - bs0), r(s1 - bs0)
    if end == "front":
        y0, y1, face = r(u0 - bu0), r(u1 - bu0), c.top
    else:
        y0, y1, face = r(bu1 - u1), r(bu1 - u0), c.bottom
    face.fill(color, max(0, x0), max(0, y0), x1, y1)


def stipple(c, sides, color, k=1.14):
    """Grip texture: a fine staggered pattern of light and dark texels over whole sides."""
    for side in sides:
        face = getattr(c, FACES[side])
        for y in range(face.h):
            for x in range(face.w):
                if (x + y) % 2 == 0:
                    face.px(x, y, shade(color, k))
                elif (x * 3 + y * 5) % 7 == 0:
                    face.px(x, y, shade(color, 0.85))


def engrave(c, side, f0, u, rows, color):
    """Stamp markings onto a side: `rows` are strings of 'x' (a texel) and '.', the first at u, the next one
    unit lower, one character per unit of f from f0."""
    bf0, bf1, bu0, bu1, bs0, bs1 = c.ext
    face = getattr(c, FACES[side])
    fl = lambda v: int(math.floor(v + 1e-6))
    for j, row in enumerate(rows):
        uu = u - j
        for i, ch in enumerate(row):
            if ch != "x":
                continue
            ff = f0 + i
            x = fl(uu - bu0) if side == "right" else fl(bu1 - uu - 1)
            face.px(x, fl(bf1 - ff - 1), color)


def text(n, seed=0, tall=()):
    """Two rows of letter-like strokes, n units long (roll marks too small to spell)."""
    import random
    rnd = random.Random(seed)
    top, low = [], []
    i = 0
    while i < n:
        w = rnd.choice((1, 1, 2))
        if i in tall or rnd.random() < 0.25:
            top.append("x" * w)
        else:
            top.append("." * w)
        low.append("x" * w)
        i += w
        if i < n:
            gap = 2 if rnd.random() < 0.2 else 1
            top.append("." * gap)
            low.append("." * gap)
            i += gap
    return ["".join(top)[:n], "".join(low)[:n]]


def repaint(c, side, fn):
    """Repaint a side texel by texel: fn(f, u, old) gives the new colour (or None to keep it), (f, u) being the
    texel's centre in the box's own (unturned) coordinates."""
    bf0, bf1, bu0, bu1, bs0, bs1 = c.ext
    face = getattr(c, FACES[side])
    for y in range(face.h):
        for x in range(face.w):
            f = bf1 - y - 0.5
            u = bu0 + x + 0.5 if side == "right" else bu1 - x - 0.5
            col = fn(f, u, face.get(x, y))
            if col is not None:
                face.px(x, y, col)


def coil(g, f0, f1, cu, cs, r, color, pitch=2, bone=None):
    """A coil spring along f: turns every `pitch` units round a thin core."""
    g.rod(f0, f1, cu, cs, r * 0.55, shade(color, 0.6), 1, bone=bone)
    f = f0
    while f + 1 <= f1:
        g.rod(f, f + 1, cu, cs, r, color, 1, bone=bone)
        f += pitch


def stud(g, f, u, s, side, color=None, size=1.0, proud=0.5, bone=None):
    """A rivet, pin or screw head on a side whose surface is at s, standing `proud` out of it (none at LOW
    detail)."""
    if LOW[0]:
        return None
    col = color or shade(SILVER, 0.7)
    h = size / 2
    s0, s1 = (s + proud - 1, s + proud) if side == "left" else (s - proud, s - proud + 1)
    return g.box(f - h, f + h, u - h, u + h, s0, s1, col, 1, inflate=-0.08, bone=bone)


def studs(g, f, u, half, color=None, size=1.0, bone=None):
    """The two ends of a cross pin through a part `half` wide each side of the middle."""
    return [stud(g, f, u, half, "left", color, size, bone=bone), stud(g, f, u, -half, "right", color, size, bone=bone)]


def boss(g, f, u, s0, s1, d, color, noise=2, bone=None):
    """A small round head across the gun (axis along s), d units across: a plus for d <= 2, a cross over a
    square for d = 3, an octagon (two crossed boxes and four 45-degree corners) from d = 4. Reads round from
    the side without the star points of turned squares."""
    d = max(1, int(round(d)))
    h = d / 2
    out = []
    if d <= 2:
        out.append(g.box(f - h, f + h, u - 0.5, u + 0.5, s0, s1, color, noise, bone=bone))
        if d == 2:
            out.append(g.box(f - 0.5, f + 0.5, u - h, u + h, s0, s1, color, noise, bone=bone))
        return out
    if d == 3:
        out.append(g.box(f - 1.5, f + 1.5, u - 0.5, u + 0.5, s0, s1, color, noise, bone=bone))
        out.append(g.box(f - 0.5, f + 0.5, u - 1.5, u + 1.5, s0, s1, color, noise, bone=bone))
        out.append(g.box(f - 1, f + 1, u - 1, u + 1, s0, s1, color, noise, bone=bone))
        return out
    r2 = (math.sqrt(2) - 1) / 2
    out.append(g.box(f - h, f + h, u - h + 1, u + h - 1, s0, s1, color, noise, bone=bone))
    out.append(g.box(f - h + 1, f + h - 1, u - h, u + h, s0, s1, color, noise, bone=bone))
    for df in (-1, 1):
        for du in (-1, 1):
            cf, cu = f + df * (h - 1), u + du * (h - 1)
            out.append(g.box(cf - 0.5, cf + 0.5, cu - 0.5, cu + 0.5, s0, s1, shade(color, 1.12 if du > 0 else 0.88),
                             noise, inflate=r2, tilt=45, pivot=(cf, cu), bone=bone))
    return out


def lines(c, side, f0, f1, u0, u1, every, color, vertical=False):
    """Parallel engraved lines over an area of a side: along f, or (vertical) across it."""
    if vertical:
        f = f0
        while f < f1:
            mark(c, side, f, f + 1, u0, u1, color)
            f += every
    else:
        u = u0
        while u < u1:
            mark(c, side, f0, f1, u, u + 1, color)
            u += every


def hoop(g, f0, f1, cu, cs, r, color, t=1.0, arc=(-135, 135), step=45, noise=2, bone=None):
    """A ring round an axis along f (a sight hood, a band): flat segments turned about the axis, from arc[0]
    to arc[1] degrees (0 at the top)."""
    w = max(1, round(2 * r * math.tan(math.radians(step / 2)) + 0.4))
    out = []
    a = arc[0]
    while a <= arc[1] + 1e-6:
        out.append(g.box(f0, f1, cu + r - t, cu + r, cs - w / 2, cs + w / 2, color, noise, roll=float(a),
                         pivot=(0, cu, cs), bone=bone))
        a += step
    return out


def side_rail(g, f0, f1, cu, s, side, color=BLACK, bone=None, step=3):
    """A short picatinny rail on a side (surface at s): a base 4 units tall and a tooth every `step` units."""
    d = 1 if side == "left" else -1
    lo = lambda a, b: (s + a, s + b) if d > 0 else (s - b, s - a)
    base = g.box(f0, f1, cu - 2, cu + 2, *lo(0, 1), color, 2, bone=bone)
    g.box(f0, f1, cu - 2.5, cu + 2.5, *lo(1, 2), shade(color, 0.85), 2, bone=bone)
    f = f0
    while f + 2 <= f1:
        g.box(f, f + 2, cu - 2.5, cu + 2.5, *lo(2, 3), shade(color, 1.12), 1, bone=bone)
        f += step
    return base


def bend_mag(g, f0, top, width, depth, segs, color, overlap=0.6, noise=3):
    """A curved box magazine: segs = [(df, h), ...] from the top down. Each segment is turned about the middle of
    its top edge so its bottom meets the next one (a smooth curve, not steps). Returns the segments as
    (box, df, u_top, h, angle, pivot); seg_box() places more boxes in a segment's own frame."""
    s = width / 2
    out = []
    u = top
    for i, (df, h) in enumerate(segs):
        if i + 1 < len(segs):
            step = segs[i + 1][0] - df
        else:
            step = df - segs[i - 1][0] if i else 0.0
        ang = math.degrees(math.atan2(step, h))
        piv = (f0 + df + depth / 2, u)
        c = g.box(f0 + df, f0 + df + depth, u - h - overlap, u, -s, s, color, noise, tilt=ang, pivot=piv)
        soften(c, (("top",) if i else ()) + (("bottom",) if i + 1 < len(segs) else ()))
        out.append((c, df, u, h, ang, piv))
        u -= h
    return out


def soften(c, edges=("bottom",)):
    """Undo the painted edge light or shadow along the top or bottom long edges of a box's two sides (where the
    box runs on into another part of the same surface, as magazine segments do)."""
    for face, bottom_x, top_x in ((c.right, 0, c.right.w - 1), (c.left, c.left.w - 1, 0)):
        if face.w < 3:
            continue
        for name in edges:
            x = bottom_x if name == "bottom" else top_x
            nx = x + 1 if x == 0 else x - 1
            for y in range(face.h):
                face.px(x, y, face.get(nx, y))


def seg_box(g, seg, f0, f1, u0, u1, s0, s1, color, noise=2, **kw):
    """A box in a magazine segment's own frame (see bend_mag): it turns with the segment."""
    _c, _df, _u, _h, ang, piv = seg
    return g.box(f0, f1, u0, u1, s0, s1, color, noise, tilt=ang, pivot=piv, **kw)


# =========================================================================== pistols

def glock17():
    """Glock 17 (Gen 4/5), 9x19mm: a polymer frame raked 22 degrees with finger grooves and textured panels, a
    boxy nitrided slide with front and rear serrations, the barrel hood filling the ejection port, a U-notch
    rear sight and a dot front sight."""
    g = gun("glock17", "pistol", "pistol")
    PL, PD, PLL = POLY, shade(POLY, 0.82), shade(POLY, 1.18)
    SL = BLUED
    PIN = shade(SILVER, 0.55)
    gr = Raked(g, -22, (-3, 5))  # the grip, raked 22 degrees

    # ------------------------------------------------------------ frame: tang, receiver, dust cover, rail
    cham(g, -10, -5, 6, 9, -2.5, 2.5, PL, t=0, b=1)  # tang (the short beavertail over the web of the hand)
    g.box(-11, -10, 6.5, 8.5, -2, 2, PL)
    g.box(-11.5, -10.5, 7, 8, -1.5, 1.5, PL, inflate=0.2, tilt=45, pivot=(-11, 7.5))
    g.box(-10, -5, 8.5, 9, -2, 2, shade(STEEL, 0.9), 1)  # steel slide rails at the rear
    fr = g.box(-5, 12, 4, 9, -2.5, 2.5, PL)  # receiver over the trigger
    dc = cham(g, 12, 27, 4, 9, -2.5, 2.5, PL, t=0, b=1)  # dust cover
    g.box(26, 27, 5, 8.5, -2, 2, PLL)  # its rounded nose
    edge(g, 25.5, 27, 5, 2, PL, 0.5)
    edge(g, 25.5, 27, 5, -2, PL, 0.5)
    g.teeth_rail(15, 27, 4, -2, 2, PL, down=True)  # accessory rail
    for c in (fr, dc):
        for side in ("right", "left"):
            mark(c, side, c.ext[0], c.ext[1], 8, 9, shade(PL, 0.7))  # the frame rails under the slide
    mark(fr, "left", -4, 0, 5, 7, PLL)  # the GLOCK logo by the thumb
    engrave(fr, "left", -4, 6, ["x.xx", "xxxx"], shade(PL, 0.6))
    engrave(dc, "right", 14, 6, text(6, 3), shade(SILVER, 0.6))  # serial plate
    mark(fr, "down", 3.5, 6, 0, 0, DARK, -1, 1)  # trigger slot

    # trigger guard: squared, with a hooked front
    tg = g.box(0.5, 12, 0, 1, -1, 1, PL)
    g.box(11, 12, 0.5, 4, -1, 1, PL, tilt=8, pivot=(11.5, 4))
    g.box(12, 13, 0, 1, -1, 1, PL)
    g.box(12.5, 13.5, 0, 1, -1, 1, PL, inflate=-0.15, tilt=45, pivot=(13, 0.5))
    g.box(10.5, 11.5, 0.5, 1.5, -1, 1, PL, inflate=-0.15, tilt=45)  # inner fillets
    g.box(0.5, 1.5, 0.5, 1.5, -1, 1, PL, inflate=-0.15, tilt=45)
    edge(g, 0.5, 13, 0.5, 0.5, shade(PL, 0.85), 0.5)  # rounded underside
    # trigger: a curved shoe with the safety blade standing out of its face, the trigger bar behind it
    TR = shade(POLY, 0.7)
    g.box(4, 5, 3, 5, -1, 1, TR, 2)
    g.box(4, 5, 2, 3, -1, 1, TR, 2, tilt=15, pivot=(4.5, 3))
    g.box(4.3, 5.3, 1, 2, -1, 1, TR, 2, tilt=35, pivot=(4.8, 2))
    g.box(4.6, 5.6, 2.3, 3.6, -0.5, 0.5, PLL, 1, tilt=12, pivot=(5.1, 3.6))
    g.box(4.9, 5.9, 1.3, 2.3, -0.5, 0.5, PLL, 1, tilt=34, pivot=(5.4, 2.3))
    g.box(2, 4, 3.5, 4.5, -1, -0.5, STEEL, 1)  # trigger bar

    # controls: slide stop (both sides, Gen 5), takedown lever, pins, magazine catch
    for s0, d in ((2.5, 1), (-3.5, -1)):
        g.box(2, 9, 8, 9, s0, s0 + 1, SL, 1)
        g.box(0.5, 2.5, 7, 9, s0 + 0.5 * d, s0 + 1 + 0.5 * d, SL, 1)  # its thumb tab
        g.box(9.5, 10.5, 7.5, 8.5, s0, s0 + 1, SL, 1)  # its pivot
    g.box(10.5, 12.5, 7.5, 8.5, -3, 3, SL, 1)  # takedown lever
    g.box(11.5, 12.5, 7, 8, -3, 3, SL, 1)
    for c in (fr, dc):
        for side in ("right", "left"):
            mark(c, side, 10, 13, 7, 9, DARK)
    for f, u in ((-3.5, 6.5), (4, 6), (9, 5)):  # trigger housing, trigger and locking block pins
        g.box(f, f + 1, u, u + 1, -3, 3, PIN, 1, inflate=-0.12)
    g.box(-0.5, 1.5, 1.5, 3.5, 3, 4, PD, 1)  # magazine catch
    g.box(-0.5, 1.5, 1.5, 3.5, -4, -3, PD, 1)

    # ------------------------------------------------------------ grip: rounded, finger grooves, textured panels
    gr.box(-7, 1, -13, 5, -3, 3, PL)
    gr.box(-8, 2, -13, 5, -2, 2, PL)
    for f in (-7, 1):
        for s in (-2, 2):
            gr.vedge(f, s, -13, 4.5, PL)
    for h in (-2.5, -7.5):  # finger grooves: ridges between the fingers
        gr.box(1.5, 2.5, h - 0.5, h + 0.5, -1.5, 1.5, PD, 2, extra=45, inflate=0.207)
    gr.box(-9, -8, -10, -3, -1.5, 1.5, PL)  # backstrap palm swell
    gr.box(-9, -8, -11, -10, -1.5, 1.5, PL, extra=45, inflate=-0.15)
    gr.box(-9, -8, -3, -2, -1.5, 1.5, PL, extra=45, inflate=-0.15)
    for side, (s0, s1) in (("left", (2.5, 3.5)), ("right", (-3.5, -2.5))):
        p = gr.box(-6.5, 0.5, -11, 1, s0, s1, PL, 1)  # raised texture panel
        stipple(p, (side,), PL)
        for u in (-11.5, 1.5):  # its bevelled top and bottom
            gr.box(-6.5, 0.5, u - 0.5, u + 0.5, s0, s1, PL, 1, extra=45, inflate=-0.15)
    rim = gr.box(-8.5, 1.5, -13, -12, -3.5, 3.5, PD, 2)  # flared magwell
    mark(rim, "down", -7.5, 0.5, 0, 0, DARK, -2.5, 2.5)
    for side in ("right", "left"):
        mark(rim, side, -8.5, -6.5, -13, -12, DARK)  # lanyard cut

    # ------------------------------------------------------------ barrel (stays put while the slide runs back)
    for c in g.rod(13, 29.5, 12, 0, 1.5, GUNMETAL, facets=4):
        endmark(c, "front", -0.5, 0.5, 11.5, 12.5, DARK)
    g.box(7, 13, 10.5, 15.5, -2, 1, GUNMETAL, 2)  # chamber hood in the ejection port
    g.box(7, 13, 14.5, 15.5, -2, 1, shade(GUNMETAL, 1.15), 1)
    g.box(7, 8, 13, 15, -2.2, -1.2, shade(GUNMETAL, 0.7), 1)  # chamber mouth
    coil(g, 20, 29, 10, 0, 0.9, shade(SILVER, 0.75), 2)  # recoil spring round its guide rod
    g.rod(28, 29.5, 10, 0, 0.5, shade(STEEL, 1.1))  # guide rod tip
    g.muzzle = (29.5, 12.0)

    # ------------------------------------------------------------ slide
    g.part("slide", 11, 12)
    g.use("slide")
    rear = g.box(-6, -5, 9, 15, -3, 3, SL)
    endmark(rear, "rear", -2, 2, 10, 14, shade(SL, 0.78))  # slide cover plate
    endmark(rear, "rear", -0.5, 0.5, 11.5, 12.5, DARK)  # striker channel
    g.box(-6.5, -5.5, 10.5, 13.5, -1.5, 1.5, shade(SL, 0.85), 1)
    ridges(g, -5, 1, 9, 15, -3, 3, SL)  # rear serrations
    m1 = g.box(1, 6, 9, 15, -3, 3, SL)
    g.box(6, 13, 9, 13, -3, 3, SL)  # under the ejection port
    g.box(6, 13, 13, 15, 0, 3, SL)  # the port's far wall
    g.box(6, 7, 13, 15, -2.5, 0, DARK, 0)  # breech face shadow
    m2 = g.box(13, 20, 9, 15, -3, 3, SL)
    ridges(g, 20, 26, 9, 15, -3, 3, SL)  # front serrations
    g.box(26, 28, 11, 15, -3, 3, SL)  # nose, open below for the recoil spring
    for s0 in (-3, 1):
        g.box(26, 28, 9, 11, s0, s0 + 2, SL)
    g.box(28, 29, 11, 15, -2, 2, SL)  # muzzle face
    for s0 in (-2, 1):
        g.box(28, 29, 9, 11, s0, s0 + 1, SL)
    for s in (-2, 2):  # the Gen 5 nose: front corners chamfered
        rbox(g, 27.5, 28.5, 9, 15, s - 0.5, s + 0.5, SL, (0, 0, 45), (28, 12, s), 2, 0.207)
    g.box(27.5, 28.5, 14.5, 15.5, -2, 2, shade(SL, 1.15), 2, inflate=0.207, tilt=45, pivot=(28, 15))
    # the top: flat with chamfered edges, cut on the right for the ejection port
    g.box(-6, 6, 15, 16, -2, 2, SL)
    g.box(6, 13, 15, 16, 0, 2, SL)
    g.box(13, 28, 15, 16, -2, 2, SL)
    edge(g, -6, 28, 15, 2, shade(SL, 1.25))
    edge(g, -6, 6, 15, -2, shade(SL, 1.25))
    edge(g, 13, 28, 15, -2, shade(SL, 1.25))
    g.box(2.5, 6, 13, 14, -3.5, -2.5, STEEL, 1)  # extractor with its loaded-chamber bump
    g.box(4, 5, 13.5, 14.5, -3.7, -3, STEEL, 1, inflate=-0.1)
    engrave(m2, "left", 13.5, 12, text(6, 1, (0,)), shade(SILVER, 0.7))  # GLOCK 17 / AUSTRIA 9x19
    engrave(m1, "left", 1, 11, text(5, 2), shade(SILVER, 0.6))
    engrave(m2, "right", 14, 10, text(4, 4)[1:], shade(SILVER, 0.6))  # serial
    mark(m1, "left", 1, 3, 9, 10, shade(SL, 0.6))  # slide stop notch
    # rear sight: dovetailed U notch with a white outline; front sight: a post with a white dot
    rs = g.box(-5, -2, 16, 17, -2, 2, DARK, 2)
    endmark(rs, "rear", -1, 1, 16, 17, WHITE)
    for s0 in (-2, 1):
        p = g.box(-5, -3, 17, 19, s0, s0 + 1, DARK, 2)
        endmark(p, "rear", s0, s0 + 1, 17, 19, WHITE)
        g.box(-3, -2, 17, 18, s0, s0 + 1, DARK, 2)
        g.box(-2.5, -1.5, 16.5, 17.5, s0, s0 + 1, DARK, 1, inflate=-0.15, tilt=45, pivot=(-2, 17))
    g.box(-5.5, -1.5, 15.5, 16.5, -2.5, 2.5, shade(SL, 0.8), 1)  # dovetail
    g.box(-4, -3, 15.7, 16.7, -2.9, -2.4, SILVER, 1, inflate=-0.1)  # windage set screw
    g.box(24.5, 27.5, 16, 17, -1, 1, DARK, 2)
    fs = g.box(25, 27, 17, 19, -0.5, 0.5, DARK, 1)
    endmark(fs, "rear", -0.5, 0.5, 18, 19, WHITE)
    g.box(27, 28, 16, 17.5, -0.5, 0.5, DARK, 1, tilt=40, pivot=(27, 16))

    # ------------------------------------------------------------ magazine (whole: it drops out on a reload)
    mag_bones(g, -2, -10)
    mg = Raked(g, -22, (-3, 5))
    body = mg.box(-6.5, 0.5, -13, 4, -2, 2, POLY, 2)
    for k in range(5):  # witness holes down the back
        endmark(body, "rear", 0, 1, -11 + 3 * k, -10 + 3 * k, BRASS)
    mg.box(-7, -6, -12, 3, -1, 1, POLY, 2)  # spine
    g.box(-5.5, 0, 5, 6, -2, -1, STEEL, 1)  # feed lips
    g.box(-5.5, 0, 5, 6, 1, 2, STEEL, 1)
    cartridge(g, -5.5, 6.3, 0, 5.5, 0.95)
    bp = mg.box(-7.5, 1.5, -15, -13, -2.5, 2.5, PD, 2)  # baseplate with its front lip
    mg.box(1.5, 2.5, -15, -14, -2, 2, PD, 2)
    mark(bp, "down", -6, 0, 0, 0, shade(PD, 0.7), -0.5, 0.5)
    g.mag_profile = dict(f0=-6.5, f1=0.5, top=-13, length=2, width=4, tilt=-22, pivot=(-3, 5), color=POLY,
                         kind="pistol")

    g.mount("optic", 4, 16, length=8, default=False, parent="slide")
    g.mount("muzzle", 29.5, 12, default=False, parent="slide", bore=2)
    g.mount("side", 22, 1, length=10, default=False)
    g.use("frame")
    return g


def m1911():
    """Colt M1911A1, .45 ACP: a blued slide with a rounded top, fine rear serrations, a low ejection port and a
    nose that wraps the barrel bushing and the recoil spring plug; a spur hammer (cocked), the grip safety's
    short tang, the thumb safety, plunger tube and slide stop on the left, checkered walnut grips with their
    screws, an arched mainspring housing with the lanyard loop."""
    g = gun("m1911", "pistol", "pistol")
    BL, BD, BLL = BLUED, shade(BLUED, 0.8), shade(BLUED, 1.25)
    PIN = shade(SILVER, 0.6)
    gr = Raked(g, -16, (-3, 4))  # the grip, raked 16 degrees

    # ------------------------------------------------------------ frame
    fr = g.box(-6, 14, 4, 9, -2.5, 2.5, BL)  # receiver over the trigger
    dc = cham(g, 14, 25, 6, 9, -2.5, 2.5, BL, t=0, b=1)  # dust cover round the recoil spring
    g.box(11, 14, 4, 6, -2.5, 2.5, BL)
    g.box(13, 15, 4.5, 6.5, -2.5, 2.5, BL, inflate=-0.3, tilt=45, pivot=(14, 5.5))
    for side in ("right", "left"):
        mark(fr, side, -6, 14, 8, 9, BD)  # frame rails under the slide
        mark(dc, side, 14, 25, 8, 9, BD)
        mark(fr, side, 0, 3, 4, 7, shade(BL, 0.85))  # A1 finger relief cuts behind the trigger
    engrave(fr, "left", 2, 6, text(7, 11), shade(BL, 1.6))  # UNITED STATES PROPERTY / M1911A1 U.S. ARMY
    engrave(dc, "right", 15, 7, text(7, 12)[1:], shade(BL, 1.6))  # serial
    mark(fr, "down", 2.5, 5, 0, 0, DARK, -1, 1)  # trigger slot
    # grip safety tang over the web of the hand
    g.box(-11, -6, 6.5, 9, -2, 2, BL)
    g.box(-11.5, -10.5, 6.75, 8.75, -1.5, 1.5, BL, inflate=0.1, tilt=45, pivot=(-11, 7.75))
    edge(g, -11, -6, 6.5, 1.5, BD, 0.5)
    edge(g, -11, -6, 6.5, -1.5, BD, 0.5)
    # trigger guard: round-fronted
    g.box(1, 10, 0, 1, -1, 1, BL)
    g.box(9.5, 11, 0.2, 1.2, -1, 1, BL, tilt=30, pivot=(10.3, 0.7))
    g.box(10.8, 11.8, 1, 3, -1, 1, BL)
    g.box(10.3, 11.3, 2.8, 4.6, -1, 1, BL, tilt=-30, pivot=(10.8, 3.7))
    edge(g, 1, 10, 0.5, 0.5, BD, 0.5)
    g.box(0.5, 1.5, 0.5, 1.5, -1, 1, BL, inflate=-0.15, tilt=45)
    # short A1 trigger with a serrated face
    tr = g.box(3, 4, 1.5, 5, -1, 1, shade(STEEL, 1.1), 2)
    g.box(3.2, 4.2, 0.7, 1.7, -1, 1, shade(STEEL, 1.1), 2, tilt=25, pivot=(3.7, 1.7))
    for u in (2, 4):
        endmark(tr, "front", -1, 1, u, u + 1, shade(STEEL, 0.7))
    # slide stop: checkered thumb pad, lever arm forward to its pin (whose end shows on the right)
    pad = g.box(1, 4, 8, 10, 2.5, 3.5, BL, 1)
    knurl(pad, "left", 1, 4, 8, 10, BD)
    g.box(3, 9.5, 7.5, 8.5, 2.5, 3.2, BL, 1, tilt=-12, pivot=(3, 8))
    spin(g, 9.5, 7, 2.5, 3.5, 0.9, BL, facets=2)
    g.box(9, 10, 6.5, 7.5, -3, -2, PIN, 1)
    # plunger tube (staked to the frame) between slide stop and thumb safety
    g.rod(-3, 1, 8.5, 3, 0.6, BL, facets=1)
    g.box(-2.5, 0.5, 7.5, 8.5, 2.5, 3.2, BD, 1)
    g.box(0.5, 1, 8.2, 8.8, 3.2, 3.8, BL, 1, inflate=-0.1)
    # thumb safety
    g.box(-8, -5, 8, 10, 2.5, 3.5, BL, 1)
    g.box(-8.5, -7.5, 8.5, 9.5, 2.5, 3.5, BL, 1, inflate=0.2, tilt=45, pivot=(-8, 9))
    g.box(-5, -2, 9, 10, 2.5, 3.5, BL, 1)
    ts = g.box(-3, -1.5, 9, 10, 3, 4, BLL, 1)
    knurl(ts, "left", -3, -1, 9, 10, BD)
    # pins on the right side: hammer, sear, thumb safety shaft
    for f, u in ((-8.5, 8), (-5, 7), (-8.5, 9.5)):
        g.box(f, f + 1, u, u + 1, -3, -2, PIN, 1, inflate=-0.1)
    g.box(-0.5, 1.5, 2.5, 4.5, 2.6, 3.6, shade(BL, 1.15), 1)  # magazine catch, checkered
    g.box(0, 1, 3, 4, 3.4, 3.9, BD, 1, inflate=-0.1)

    # ------------------------------------------------------------ grip: walnut double-diamond panels
    gr.box(-7, 1, -13, 4, -2.5, 2.5, BL)
    gr.box(-8, 2, -13, 4, -1.5, 1.5, BL)
    for f in (-7, 1):
        for s in (-1.5, 1.5):
            gr.vedge(f, s, -13, 3.5, BL)
    gr.box(-8.5, -7.5, -4, 3, -1.5, 1.5, BL, 2)  # grip safety lever
    msh = gr.box(-9, -8, -11, -5, -1.5, 1.5, BL)  # arched mainspring housing
    gr.box(-9, -8, -12, -11, -1.5, 1.5, BL, extra=45, inflate=-0.15)
    gr.box(-9, -8, -5, -4, -1.5, 1.5, BL, extra=45, inflate=-0.15)
    for u in range(-11, -5, 2):
        endmark(msh, "rear", -1.5, 1.5, u, u + 1, BD)  # its serrations
    for side, (s0, s1), d in (("left", (2.5, 3.5), 1), ("right", (-3.5, -2.5), -1)):
        p = gr.box(-6.5, 0.5, -11, 2, s0, s1, WALNUT, 2)

        def checker(f, u, old, side=side):
            di = min(abs(f + 3) / 2.6 + abs(u - h) / 3.2 for h in (-8.5, -0.5))
            if di <= 1:
                return shade(WALNUT_L, 1.0 + 0.1 * (1 - di))  # the smooth diamonds round the screws
            return shade(WALNUT, 0.72) if (int(f + 20) + int(u + 20)) % 2 else shade(WALNUT_L, 0.95)
        repaint(p, side, checker)
        for u in (-11.5, 2.5):
            gr.box(-6.5, 0.5, u - 0.5, u + 0.5, s0, s1, WALNUT, 1, extra=45, inflate=-0.15)
        for u in (-8.5, -0.5):  # grip screws
            sc = gr.box(-3.5, -2.5, u - 0.5, u + 0.5, s0 + 0.5 * d + 0.5, s1 + 0.5 * d - 0.5, PIN, 1, inflate=0.1)
            mark(sc, side, -3.5, -2.5, u - 0.5, u + 0.5, shade(SILVER, 0.75))
    gr.pin(-8.5, -12, -2, 2, 0.5, PIN)  # mainspring housing pin
    # lanyard loop
    for f0 in (-9.5, -7.5):
        gr.box(f0, f0 + 1, -15, -13, -0.5, 0.5, STEEL, 1)
    gr.box(-9.5, -6.5, -15.5, -14.5, -0.5, 0.5, STEEL, 1)

    # ------------------------------------------------------------ barrel (stays put while the slide runs back)
    for c in g.rod(6, 30, 12, 0, 1.4, GUNMETAL, facets=3):
        endmark(c, "front", -0.5, 0.5, 11.5, 12.5, DARK)
    g.box(7, 11, 10.5, 14.5, -2, 1, GUNMETAL, 2)  # chamber hood in the ejection port
    g.box(7, 8, 11, 13, -2.2, -1.2, shade(GUNMETAL, 0.7), 1)
    g.muzzle = (30.0, 12.0)

    # ------------------------------------------------------------ hammer: the A1 spur hammer, cocked
    g.part("hammer", -8, 8.5)
    hr = Raked(g, 40, (-8, 8.5))
    hr.box(-1, 1, -1, 1, -1, 1, BL, 2, bone="hammer")
    hr.box(-1, 1, -1, 1, -1, 1, BL, 2, extra=45, inflate=0.15, bone="hammer")
    hr.box(-0.8, 1, 1, 3.5, -1, 1, BL, 2, bone="hammer")
    spur = hr.box(-2, 0.5, 3.5, 5, -1, 1, BL, 2, bone="hammer")
    for f in (-1.5, -0.5):
        mark(spur, "up", f, f + 0.5, 0, 0, BD)
    hr.box(-2.5, -1.5, 3.7, 4.7, -1, 1, BL, 2, extra=45, inflate=-0.1, bone="hammer")

    # ------------------------------------------------------------ slide
    g.part("slide", 10, 12)
    g.use("slide")
    rear = g.box(-7, -6, 9, 14, -2.5, 2.5, BL)
    endmark(rear, "rear", -1, 1, 10, 13, BD)  # firing pin stop
    endmark(rear, "rear", -0.5, 0.5, 11.5, 12.5, DARK)
    ridges(g, -6, 0, 9, 14, -2.5, 2.5, BL)  # rear serrations
    m1 = g.box(0, 6, 9, 14, -2.5, 2.5, BL)
    g.box(6, 11, 9, 11, -2.5, 2.5, BL)  # under the ejection port
    g.box(6, 11, 11, 14, 0, 2.5, BL)
    g.box(6, 7, 11, 14, -2, 0, DARK, 0)
    m2 = g.box(11, 29, 9, 14, -2.5, 2.5, BL)
    g.box(-7, 6, 14, 15, -1.5, 1.5, BL)  # the top, rounded over
    g.box(6, 11, 14, 15, 0, 1.5, BL)
    g.box(11, 29, 14, 15, -1.5, 1.5, BL)
    edge(g, -7, 29, 14, 1.5, BLL)
    edge(g, -7, 6, 14, -1.5, BLL)
    edge(g, 11, 29, 14, -1.5, BLL)
    g.box(-7, 29, 14.6, 15.2, -1, 1, shade(BL, 1.1), 1)  # matted sight plane
    nose = g.box(25, 29, 6, 9, -2.5, 2.5, BL)  # the nose wraps the recoil spring plug
    edge(g, 25, 29, 6.5, 2, BD, 0.5)
    edge(g, 25, 29, 6.5, -2, BD, 0.5)
    g.box(28.5, 29.5, 5.5, 6.5, -2.5, 2.5, BL, inflate=-0.3, tilt=45, pivot=(29, 6))
    for c in g.rod(28.5, 29.5, 12, 0, 2, shade(BL, 1.1), facets=3):  # barrel bushing
        pass
    for c in g.rod(28.5, 29.5, 8, 0, 1.1, shade(BL, 1.15), facets=2):  # recoil spring plug
        endmark(c, "front", -0.5, 0.5, 7.5, 8.5, BD)
    mark(m1, "left", 1, 4, 9, 10, BD)  # slide stop notch
    mark(m2, "left", 11, 13, 9, 10, BD)  # disassembly notch
    engrave(m2, "left", 12, 12, text(13, 21, (0, 6)), shade(BL, 1.6))  # PATENTED ... / COLT'S PT. F.A. MFG. CO.
    engrave(m2, "left", 12, 10, text(11, 22)[1:], shade(BL, 1.6))
    engrave(m2, "right", 15, 12, text(10, 23, (0,)), shade(BL, 1.6))  # MODEL OF 1911. U.S. ARMY
    # sights: a small notch rear sight and the staked half-moon front blade
    g.box(-6, -3, 15, 16, -1.5, 1.5, BD, 1)
    for s0 in (-1.5, 0.5):
        g.box(-6, -3.5, 16, 17, s0, s0 + 1, BD, 1)
    g.box(24, 26, 15, 17, -0.5, 0.5, BD, 1)
    g.box(25.5, 26.5, 15, 16.5, -0.5, 0.5, BD, 1, tilt=40, pivot=(26, 15))

    # ------------------------------------------------------------ magazine: seven rounds of .45, flat base
    mag_bones(g, -3, -10)
    mg = Raked(g, -16, (-3, 4))
    body = mg.box(-6.5, 0, -13, 3, -2, 2, STEEL, 2)
    for side in ("right", "left"):
        for u in (-10, -7, -4):  # witness holes
            mark(body, side, -4, -3, u, u + 1, DARK)
    base = mg.box(-7, 0.5, -14, -13, -2, 2, shade(STEEL, 0.85), 2)
    mark(base, "down", -6, 0, 0, 0, shade(STEEL, 0.6), -0.5, 0.5)
    g.box(-6, 0, 4, 5, -2, -1, STEEL, 1)  # feed lips
    g.box(-6, 0, 4, 5, 1, 2, STEEL, 1)
    cartridge(g, -6, 5.4, 0, 6.2, 1.15)
    g.mag_profile = dict(f0=-6.5, f1=0, top=-13, length=1, width=4, tilt=-16, pivot=(-3, 4), color=STEEL,
                         kind="pistol")
    g.mount("muzzle", 30, 12, default=False, parent="slide", bore=2.3)
    g.use("frame")
    return g


# =========================================================================== submachine guns

def mp5():
    """H&K MP5A3, 9x19mm: a stamped sheet-steel receiver with its pressed rib and rivets, the ejection port with
    the roller-locked bolt showing and the brass-deflector bump behind it; the polymer Navy trigger group with
    its integral grip and big guard, ambidextrous selector and pictograms, the paddle magazine release; the
    gently curved 30-round steel magazine; the cocking tube with its slot and the folding HK slap handle; the
    tropical handguard with its flared lip; the drum rear sight, the claw-mount rail, the ringed front sight on
    its barrel clamp, the three-lug barrel and thread protector; the A3 retractable stock on two struts."""
    g = gun("mp5", "rifle", "ar")
    B = 12.0  # bore line
    BK = shade(BLACK, 1.2)  # the painted receiver (the polymer parts sit a shade darker, the steel lighter)
    BKD, BKL = shade(BK, 0.74), shade(BK, 1.32)
    PL = shade(POLY, 1.1)
    PD, PLL = shade(PL, 0.78), shade(PL, 1.4)
    ST, STL = STEEL, shade(STEEL, 1.25)
    PIN = shade(SILVER, 0.62)
    MK = shade(SILVER, 0.68)  # stamped markings
    R0, R1, U0, U1 = -10, 24, 9.5, 18.5

    # ------------------------------------------------------------ receiver: a stamped sheet-steel tube
    core = g.box(R0, R1, U0 + 1, U1 - 1, -2.5, 2.5, BK)
    g.box(R0, R1, U1 - 1, U1, -2.5, 2.5, BK)
    g.box(R0, R1, U0, U0 + 1, -2.5, 2.5, BKD)
    for s in (2.5, -2.5):
        edge(g, R0, R1, U1 - 1, s, BKL)
        edge(g, R0, R1, U0 + 1, s, shade(BK, 0.85))
    wl = g.box(R0, R1, U0 + 1, U1 - 1, 2.5, 3.5, BK)
    PF0, PF1, PU0, PU1 = 3, 12, 12, 15.5  # the ejection port on the right
    wr = g.box(PF1, R1, U0 + 1, U1 - 1, -3.5, -2.5, BK)
    g.box(R0, PF0, U0 + 1, U1 - 1, -3.5, -2.5, BK)
    g.box(PF0, PF1, U0 + 1, PU0, -3.5, -2.5, BK)
    g.box(PF0, PF1, PU1, U1 - 1, -3.5, -2.5, BK)
    mark(core, "right", PF0, PF1, PU0, PU1, DARK)
    for s0 in (3, -4):  # the pressed stiffening rib along each side
        g.box(R0 + 1.5, R1 - 1.5, 16, 17, s0, s0 + 1, shade(BK, 1.12), 2)
    g.box(1, 3, 12, 15.5, -4, -3, shade(BK, 1.08), 2)  # the brass-deflector bump behind the port
    for f in (21.5,):  # the trunnion rivets at the front, the end-cap rivets at the back
        for u in (11.5, 14.5):
            studs(g, f, u, 3.5, PIN, 0.9)
    for u in (11.5, 14.5):
        studs(g, -8.5, u, 3.5, PIN, 0.9)
    studs(g, -5.5, 17.5, 3.5, shade(BK, 1.3), 1)  # the stock-pin bosses
    # markings: MP5 A3  Kal 9mm x19 / serial / the HK logo over the magazine well
    engrave(wl, "left", 13, 14, text(8, 5)[1:], MK)
    engrave(wl, "left", 14, 12.5, text(6, 6)[1:], shade(BK, 1.45))
    engrave(wr, "right", 14, 13, text(6, 8)[1:], shade(BK, 1.45))
    mark(wl, "left", R0, R1, U0 + 1, U0 + 2, shade(BK, 0.8))  # the seam over the trigger group
    # the front of the receiver steps down to the cocking tube
    g.box(R1 - 1, R1, U1 - 1, U1, -2.5, 2.5, BK, 2, inflate=0.2, tilt=45, pivot=(R1, U1))

    # ------------------------------------------------------------ bolt, seen through the port
    g.part("bolt", 8, 13.5)
    bc = g.box(PF0 + 0.5, PF1 - 0.5, PU0 + 0.5, PU1 - 0.5, -3, -2, ST, 2, bone="bolt")
    mark(bc, "right", 8.5, 11.5, 12.5, 15, STL)  # the bolt head
    mark(bc, "right", 4, 8, 13, 14, shade(ST, 0.65))  # the carrier's cocking groove
    g.box(9, 11, 14, 15, -3.2, -2.2, SILVER, 1, inflate=-0.1, bone="bolt")  # extractor
    g.box(4, 6, 12.5, 13.5, -3.2, -2.2, shade(ST, 0.8), 1, inflate=-0.1, bone="bolt")
    g.use("frame")

    # ------------------------------------------------------------ magazine well and paddle release
    MW0, MW1 = 12, 21
    well = g.box(MW0, MW1, 2.5, U0, -3, 3, BK)
    mouth = g.box(MW0 - 0.5, MW1 + 0.5, 1.5, 2.5, -3.5, 3.5, BKD, 2)
    mark(mouth, "down", MW0 + 0.5, MW1 - 0.5, 0, 0, DARK, -2.5, 2.5)
    for s0 in (2.5, -3.5):  # pressed stiffeners down the well
        g.box(MW1 - 2, MW1 - 1, 3, 9, s0, s0 + 1, shade(BK, 1.1), 2)
    engrave(well, "left", MW0 + 1, 7, ["xx.x.xx", "x.xxx.x"], MK)
    g.box(10.5, 11.5, -0.5, 3.5, -1, 1, PD, 1)  # paddle release: its arm
    pad = g.box(10, 12, -1.5, -0.5, -2, 2, PD, 2, tilt=-15, pivot=(11, -0.5))
    lines(pad, "down", 10, 12, 0, 1, 1, shade(PD, 0.7))

    # ------------------------------------------------------------ Navy trigger group: housing, selector, grip, guard
    TH0, TH1 = -9.5, 11
    hs = cham(g, TH0, TH1, 3.5, U0, -3.5, 3.5, PL, t=0, b=1)
    g.box(TH0 - 1, TH0, 6, U0, -3, 3, PL)  # its rear tab under the end cap
    mark(hs, "left", TH0, TH1, U0 - 1, U0, shade(PL, 0.7))
    mark(hs, "right", TH0, TH1, U0 - 1, U0, shade(PL, 0.7))
    # pictograms round the selector: white (safe), one red round (semi), a burst of red rounds (auto)
    mark(hs, "left", -9, -8, 6.5, 8, WHITE)
    mark(hs, "left", -6.5, -5.5, 7.5, 8.5, RED)
    for f in (-2.5, -1.5, -0.5):
        mark(hs, "left", f, f + 0.8, 7.5, 8.5, RED)
    SEL = shade(ST, 1.05)  # selector: a steel pivot boss and the long thumb lever (at safe)
    boss(g, -4, 6, 3.5, 4.5, 3, SEL)
    endmark(g.box(-4.5, -3.5, 5.5, 6.5, 4, 5, WHITE, 0, inflate=-0.2), "front", 4, 5, 5.5, 6.5, WHITE)
    g.box(-9, -4, 5.5, 6.5, 4.3, 5.3, SEL, 1, tilt=-12, pivot=(-4, 6))
    lv = g.box(-10.5, -8.5, 4.8, 7.2, 4.5, 5.5, shade(SEL, 1.15), 1, tilt=-12, pivot=(-4, 6))
    lines(lv, "left", -10.5, -8.5, 4.8, 7.2, 2, shade(SEL, 0.7), vertical=True)
    boss(g, -4, 6, -4.5, -3.5, 3, SEL)
    g.box(-7.5, -4, 5.5, 6.5, -5.3, -4.3, SEL, 1, tilt=-12, pivot=(-4, 6))
    for f, u in ((2.5, 6), (6, 6.5), (-7.5, 5)):  # trigger, hammer and catch pins
        studs(g, f, u, 3.5, PIN, 0.8)
    for f in (TH0 + 0.5, TH1 - 1):  # the two push pins that hold the group to the receiver
        g.box(f - 0.5, f + 0.5, U0 - 0.5, U0 + 0.5, -4, 4, STL, 1, inflate=-0.05)
        g.box(f - 2, f + 0.5, U0 - 0.7, U0 - 0.3, 4, 4.5, shade(SILVER, 0.7), 1, inflate=-0.1)  # its wire clip
    # the grip, cast with the housing: finger grooves in front, stippled sides, a flared base
    gr = Raked(g, -15, (-4.5, 3.5))
    gr.box(-8, -1, -12, 4, -3, 3, PL)
    gr.box(-9, 0, -12, 4, -2, 2, PL)
    for f in (-8, -1):
        for s in (-2, 2):
            gr.vedge(f, s, -12, 3.5, PL)
    for h in (-1.5, -5.5):  # finger grooves: ridges between the fingers
        gr.box(-0.5, 0.5, h - 0.5, h + 0.5, -1.5, 1.5, PD, 2, extra=45, inflate=0.207)
    for side, (s0, s1) in (("left", (2.5, 3.5)), ("right", (-3.5, -2.5))):
        p = gr.box(-7.5, -1.5, -11, 2, s0, s1, PL, 1)
        stipple(p, (side,), PL, 1.3)
    rim = gr.box(-9.5, 0.5, -13, -12, -3.5, 3.5, PD, 2)
    mark(rim, "down", -8.5, -0.5, 0, 0, shade(PD, 0.7), -2.5, 2.5)
    # the big rounded guard
    g.box(-1.5, 9.5, -1, 0, -1.5, 1.5, PL, 2)
    edge(g, -1.5, 9.5, -0.5, 0, PD, t=1.4)  # its rounded underside
    g.box(9, 10, -0.5, 3.5, -1.5, 1.5, PL, 2)
    g.box(9, 10, -1, 0, -1.5, 1.5, PL, 2, inflate=0.2, tilt=45, pivot=(9.5, -0.5))
    edge(g, 9.5, 10.5, -0.5, 0, PD, t=1.2)
    g.box(8, 9, 0, 1, -1.5, 1.5, PL, 1, inflate=-0.15, tilt=45)  # inner fillet
    mark(hs, "down", 1.5, 3.5, 0, 0, DARK, -0.5, 0.5)  # the trigger slot
    TR = shade(ST, 1.15)  # the curved trigger
    g.box(2, 3, 1.5, 3.5, -0.5, 0.5, TR, 1)
    g.box(2.2, 3.2, -0.5, 1.5, -0.5, 0.5, TR, 1, tilt=18, pivot=(2.7, 1.5))
    g.box(1.8, 2.8, -1, 0, -0.5, 0.5, TR, 1, tilt=40, pivot=(2.3, -0.5))

    # ------------------------------------------------------------ cocking tube and slap handle
    CU = 16
    g.rod(R1 - 4, 47, CU, 0, 2.1, BK)
    g.rod(47, 48, CU, 0, 1.5, BKD)  # its end plug
    g.rod(R1 - 0.5, R1 + 0.5, CU, 0, 2.4, BKD)  # the weld collar where it leaves the receiver
    g.box(26, 41, CU - 0.5, CU + 0.5, 1.25, 2.25, DARK, 0)  # the slot on the left
    g.box(26, 27, CU, CU + 1.5, 1.25, 2.25, DARK, 0)  # and its hold-open notch
    g.part("charging_handle", 39.5, CU, 2)
    g.use("charging_handle")
    HR = dict(roll=-30, pivot=(39.5, CU, 2))
    g.box(38.5, 40.5, CU - 0.5, CU + 0.5, 1.5, 6, shade(ST, 0.95), 1, **HR)  # the folding arm
    g.box(38.5, 40.5, CU - 1, CU + 1, 1.5, 3, shade(ST, 0.8), 1, **HR)  # its hinge
    kn = g.box(37.5, 41.5, CU - 1.5, CU + 1.5, 5.5, 7.5, PL, 2, **HR)  # the knob
    lines(kn, "up", 37.5, 41.5, 0, 1, 1, PD, vertical=True)
    lines(kn, "down", 37.5, 41.5, 0, 1, 1, PD, vertical=True)
    g.box(38, 41, CU - 1, CU + 1, 7.5, 8, PLL, 1, **HR)
    g.use("frame")

    # ------------------------------------------------------------ tropical handguard
    HG0, HG1 = R1, 42
    hg = cham(g, HG0, HG1, 7, 14, -4, 4, PL, t=1, b=1)
    for u in (9, 11):  # its lengthwise ribs
        for s0 in (3.5, -4.5):
            g.box(HG0 + 2, HG1 - 1, u, u + 1, s0, s0 + 1, shade(PL, 1.25), 1)
    mark(hg, "down", HG0 + 1, HG1, 0, 0, PD, -1, 1)
    lip = g.bevel(HG1, HG1 + 2, 6, 14, -4.5, 4.5, PL, 1)  # the flared lip in front of the hand
    g.box(HG0, HG0 + 1, 7.5, 13.5, -4.2, 4.2, PD, 2)  # the rear collar against the receiver
    studs(g, HG0 + 2, 12.5, 4, PIN, 0.9)  # retaining pin
    g.box(HG0 + 0.5, HG1 - 0.5, 13.5, 14.5, -2.5, 2.5, DARK, 0)  # the gap under the cocking tube

    # ------------------------------------------------------------ barrel, front sight, three lugs
    g.rod(HG1 - 1, 52.5, B, 0, 1.6, GUNMETAL)
    FS0, FS1 = 44, 48
    fsb = g.box(FS0, FS1, 10, U1, -2.5, 2.5, BK)  # the sight base, clamped round barrel and tube
    for s in (2, -2):
        edge(g, FS0, FS1, U1 - 0.5, s, BKL, t=0.7)
    g.rod(FS0, FS1, B, 0, 2.5, BK)  # the barrel clamp
    g.box(FS0 + 0.5, FS1 - 0.5, 8.5, 10, -1.5, 1.5, BK, 2)  # the clamp's lug and its bolt
    g.rod(FS0 - 0.5, FS1 + 0.5, 9, 0, 0.6, PIN)
    g.box(FS0, FS1, U1, U1 + 1, -2, 2, BK, 2)
    hoop(g, FS0 + 0.5, FS1 - 0.5, 21.5, 0, 2.7, BK, 1, (-135, 135))  # the ring hood round the post
    g.box(45.5, 46.5, U1, 21.5, -0.5, 0.5, DARK, 1)  # the post
    g.box(45.5, 46.5, 21, 22, -0.5, 0.5, shade(BK, 1.2), 1, inflate=-0.1)
    for s0, s1 in ((2.5, 3.5),):  # sling loop on the left
        g.box(FS0 + 0.5, FS1 - 0.5, 11.5, 12.5, s0 + 1, s1 + 1, ST, 1)
        g.box(FS0 + 0.5, FS0 + 1.5, 11.5, 12.5, s0, s1, ST, 1)
        g.box(FS1 - 1.5, FS1 - 0.5, 11.5, 12.5, s0, s1, ST, 1)
    engrave(fsb, "left", FS0 + 1, 16, ["x.x", ".x."], MK)
    for a in (0, 120, 240):  # three lugs for the suppressor and grenade launcher
        g.box(49.5, 51.5, B + 1.1, B + 2.3, -1, 1, BK, 2, roll=float(a), pivot=(0, B, 0))

    # ------------------------------------------------------------ magazine: 30 rounds, gently curved
    MF, MTOP, MD, MW = 12.5, 8.5, 8, 5
    segs = [(0, 6), (0, 6), (0.6, 6), (1.6, 6), (3.0, 6.5)]
    mag_bones(g, MF + MD / 2, MTOP)
    MG = shade(STEEL, 0.9)
    sg = bend_mag(g, MF, MTOP, MW, MD, segs, MG)
    for i, seg in enumerate(sg):
        c, df, u, h, ang, piv = seg
        seg_box(g, seg, MF + df + 1.5, MF + df + 2.5, u - h - 0.6, u, -3, 3, shade(MG, 1.12), 2)  # pressed rib
        seg_box(g, seg, MF + df + MD - 1, MF + df + MD, u - h - 0.6, u, -2.5, 2.5, shade(MG, 1.18), 2)  # front
        for side in ("right", "left"):
            mark(c, side, MF + df + MD - 1, MF + df + MD, u - h, u, shade(MG, 1.25))
        if i == 1:
            engrave(c, "left", MF + df + 3, u - 2, ["x.x.xx", "xxx.x."], shade(MG, 1.5))
    last = sg[-1]
    _c, df, u, h, ang, piv = last
    fp = seg_box(g, last, MF + df - 0.5, MF + df + MD + 1, u - h - 1.6, u - h - 0.6, -3, 3, shade(MG, 0.8), 2)
    seg_box(g, last, MF + df + MD, MF + df + MD + 1.5, u - h - 1.6, u - h - 0.2, -2, 2, shade(MG, 0.8), 2)
    mark(fp, "down", MF + df + 1, MF + df + MD - 1, 0, 0, shade(MG, 0.6), -1, 1)
    g.box(MF + 1, MF + MD - 1, MTOP, MTOP + 1, -2.5, -1.5, MG, 1)  # feed lips and the top round
    g.box(MF + 1, MF + MD - 1, MTOP, MTOP + 1, 1.5, 2.5, MG, 1)
    cartridge(g, MF + 1, MTOP + 0.6, 0, MD - 2, 0.9)
    g.mag_profile = dict(f0=MF - 1, top=MTOP, width=MW, segs=segs, color=MG, kind="smg")

    # ------------------------------------------------------------ claw-mount rail over the receiver
    g.use("frame")
    CM0, CM1 = 0, 20
    g.box(CM0, CM1, U1, U1 + 1, -2.5, 2.5, BKD, 2)
    for f in (CM0 + 1, CM1 - 4):  # the four claws gripping the recesses in the receiver top
        for s0 in (2.5, -3.5):
            g.box(f, f + 3, U1 - 2, U1 + 1, s0, s0 + 1, BKD, 2)
            g.box(f, f + 3, U1 - 2.5, U1 - 1.5, s0 - 0.5 if s0 > 0 else s0 + 0.5, (s0 - 0.5 if s0 > 0 else s0 + 0.5) + 1,
                  BKD, 1)
    boss(g, 9.5, U1 - 0.5, 3, 4.5, 3, shade(ST, 0.9))  # the clamping nut and lever on the left
    endmark(g.box(9, 10, U1 - 1, U1, 4, 4.7, DARK, 0), "front", 4, 4.7, U1 - 1, U1, DARK)
    g.box(9.5, 14, U1 - 0.5, U1 + 0.5, 4, 5, shade(BLACK, 0.95), 1, tilt=-8, pivot=(9.5, U1))
    rl = g.teeth_rail(CM0, CM1, U1 + 1, -2.5, 2.5, shade(BLACK, 0.95))

    # ------------------------------------------------------------ factory sights, muzzle, stock
    g.mount("optic", 10, U1 + 4, length=20)
    g.use("def_optic")  # the drum rear sight (it stands aside for an optic)
    g.box(-9, -3, U1, U1 + 1, -2.5, 2.5, BK, 2)
    g.box(-8.5, -3.5, U1 + 1, U1 + 2, -2, 2, BK, 2)
    dr = spin(g, -6, 21.5, -1.5, 1.5, 2.3, shade(BK, 1.05), 2)
    endmark(dr[0], "rear", -0.5, 0.5, 21, 22, DARK)  # the aperture in use
    endmark(dr[0], "front", -0.5, 0.5, 21, 22, DARK)
    for s0 in (1.5, -2.5):  # the knurled rims
        for c in spin(g, -6, 21.5, s0, s0 + 1, 2.5, shade(BK, 1.25), 2):
            pass
    g.box(-6.5, -5.5, 19.5, 20.5, 2.5, 3.5, WHITE, 0, inflate=-0.2)  # range index
    g.box(-8, -5, U1, U1 + 1.5, -4, -2.5, shade(SILVER, 0.7), 1, inflate=-0.1)  # windage screw
    endmark(g.box(-7, -6, U1 + 0.2, U1 + 1.2, -4.3, -3.8, DARK, 0), "rear", -4.3, -3.8, U1, U1 + 1, DARK)
    g.mount("muzzle", 52.5, B, bore=1.6)
    g.use("def_muzzle")  # knurled thread protector
    for c in g.rod(52.5, 56.5, B, 0, 2.0, BK):
        lines(c, "up", 53, 56.5, 0, 1, 1.5, BKD, vertical=True)
    g.rod(56.5, 57, B, 0, 1.6, BK)
    g.rod(56, 57.02, B, 0, 0.8, DARK, 0)
    g.muzzle = (57.0, B)
    g.use("frame")
    g.mount("underbarrel", 34, 7, length=12, default=False)
    g.mount("side", 34, 10, 4.5, length=10, default=False)
    g.mount("stock", -11, 15)
    g.use("def_stock")  # A3 retractable stock: a housing on the end cap, two struts and a buttplate
    hb = cham(g, -14, -10, U0, U1, -3.5, 3.5, BKD, t=1, b=1)
    for s in (4.4, -4.4):  # the strut guides along the receiver sides
        g.rod(-14, -6, 16.5, s, 1.3, BKD)
        g.rod(-6.5, -5.5, 16.5, s, 1.5, BK)
        g.rod(-14.5, -14, 16.5, s, 1.5, shade(BK, 1.15))
    for f0 in (-13.5, -11.5):  # the sling loop on the left
        g.box(f0, f0 + 1, 11, 12, 3.5, 5, ST, 1)
    g.box(-13.5, -10.5, 11, 12, 5, 6, ST, 1)
    g.box(-15, -12, U1, U1 + 1, -1.5, 1.5, STL, 1)  # the release paddle on top
    g.box(-15.5, -14.5, U1 - 1, U1 + 1, -1.5, 1.5, STL, 1)
    for s in (4.4, -4.4):
        g.rod(-41, -14, 16.5, s, 0.9, STL)  # the struts
    g.rod(-41, -40, 16.5, 4.4, 1.3, ST)
    g.rod(-41, -40, 16.5, -4.4, 1.3, ST)
    bp = g.bevel(-43, -41, 4, 19.5, -5, 5, ST, 1)  # the stamped buttplate and its rubber pad
    g.box(-41, -40, 14, 19, -4, 4, ST, 2)
    pad = g.bevel(-44.5, -43, 3.5, 20, -4.5, 4.5, RUBBER, 1)
    lines(pad[0], "right", -44.5, -43, 4, 19, 2, shade(RUBBER, 1.6))
    lines(pad[0], "left", -44.5, -43, 4, 19, 2, shade(RUBBER, 1.6))
    g.box(-43, -41, 4, 7, -2, 2, ST, 2, tilt=30, pivot=(-41, 7))  # the toe
    g.use("frame")
    return g


def ump45():
    """H&K UMP45, .45 ACP: a long polymer receiver with a rail along the top and three more round the front, its
    recessed side panels and moulded ribs; the ejection port with the bolt showing; the cocking handle at the
    front left; the lower with its ambidextrous selector and pictograms, the grip joined at its foot by the big
    trigger guard, the paddle release; the straight 25-round magazine of smoked polymer with the rounds showing
    through; the drum rear sight, the hooded front post, a short barrel and thread protector; the side-folding
    skeleton stock with its rubber pad."""
    g = gun("ump45", "rifle", "ar")
    B = 13.0
    PL = shade(POLY, 1.14)  # the upper receiver
    PD, PLL = shade(PL, 0.78), shade(PL, 1.32)
    LO = shade(POLY, 0.98)  # the lower, a touch darker
    RL = shade(BLACK, 1.0)  # rails
    ST = STEEL
    PIN = shade(SILVER, 0.6)
    MK = shade(PL, 1.75)  # moulded lettering
    R0, R1, U0, U1 = -11, 37, 10, 20

    # ------------------------------------------------------------ upper receiver
    core = g.box(R0, R1, U0 + 1, U1 - 1, -3, 3, PL)
    g.box(R0, R1, U1 - 1, U1, -3, 3, PL)
    for s in (3, -3):
        edge(g, R0, R1, U1 - 1, s, PLL)
    wl = g.box(R0, R1, U0, U1 - 1, 3, 4, PL)
    PF0, PF1, PU0, PU1 = 3, 11, 13.5, 17.5
    wr = g.box(PF1, R1, U0, U1 - 1, -4, -3, PL)
    wr0 = g.box(R0, PF0, U0, U1 - 1, -4, -3, PL)
    g.box(PF0, PF1, U0, PU0, -4, -3, PL)
    g.box(PF0, PF1, PU1, U1 - 1, -4, -3, PL)
    mark(core, "right", PF0, PF1, PU0, PU1, DARK)
    g.box(R0, R1, U0, U0 + 1, -3, 3, PD)
    for s0 in (3.5, -4.5):  # the lip along the foot of the upper
        g.box(R0 + 1, 21, U0, U0 + 1, s0, s0 + 1, shade(PL, 1.15), 1)
    for side, c in (("left", wl), ("right", wr0)):  # the recessed side panels (rear)
        mark(c, side, -9, 2 if side == "right" else 20, 12, 17.5, shade(PL, 0.86))
        lines(c, side, -9, 2 if side == "right" else 20, 12, 12.5, 6, shade(PL, 0.7))
    mark(wr, "right", 12, 20, 12, 17.5, shade(PL, 0.86))
    engrave(wl, "left", 6, 16.5, ["x.x..xx.x.x.xxx.xxx", "xxx..x..x.xxx.x...x"], MK)  # HK  UMP45
    engrave(wl, "left", 7, 14, text(9, 17)[1:], MK)  # KAL .45 ACP / serial
    g.box(R0 - 1, R0, U0 + 1, U1 - 1, -3.5, 3.5, PD, 2)  # rear cap
    endmark(g.box(R0 - 1.5, R0 - 0.5, 13, 17, -2, 2, PD, 1), "rear", -1, 1, 14, 16, DARK)
    for s0 in (2.5, -3.5):  # the rail's end screws
        stud(g, R0 + 1.5, U1 + 1.5, 2.5 if s0 > 0 else -2.5, "left" if s0 > 0 else "right", PIN, 0.8)
        stud(g, R1 - 1.5, U1 + 1.5, 2.5 if s0 > 0 else -2.5, "left" if s0 > 0 else "right", PIN, 0.8)
    for f, u in ((-7, 12), (17, 12), (34, 12)):  # moulded-in steel pins
        studs(g, f, u, 4, PIN, 0.9)
    # the front: a chamfered nose round the barrel
    g.box(R1 - 1, R1, U1 - 1, U1, -3, 3, PL, 2, inflate=0.25, tilt=45, pivot=(R1, U1))
    nose = g.box(R1, R1 + 1, U0 - 2, U1 - 2, -3.5, 3.5, PD, 2)
    endmark(nose, "front", -2.5, 2.5, B - 2.5, B + 2.5, shade(PD, 0.7))

    # ------------------------------------------------------------ bolt in the port
    g.part("bolt", 7, 15.5)
    bc = g.box(PF0 + 0.5, PF1 - 0.5, PU0 + 0.5, PU1 - 0.5, -3.5, -2.5, ST, 2, bone="bolt")
    mark(bc, "right", 7.5, 10.5, 14, 17, shade(ST, 1.3))
    mark(bc, "right", 4, 7, 15, 16, shade(ST, 0.65))
    g.box(8.5, 10.5, 16, 17, -3.7, -2.7, SILVER, 1, inflate=-0.1, bone="bolt")
    g.box(4, 5, 14, 15, -3.7, -2.7, shade(ST, 0.8), 1, inflate=-0.1, bone="bolt")  # the cocking stop
    g.use("frame")

    # ------------------------------------------------------------ front: lower handguard, rails, cocking handle
    hgl = g.box(21, R1, 7, U0, -3.5, 3.5, PL)
    for s in (3, -3):
        edge(g, 21, R1, 7.5, s, shade(PL, 0.85), t=0.5)
    for f in range(23, 35, 3):  # moulded finger ribs on the lower front
        g.box(f, f + 1.5, 7.5, 9.5, 3, 4, shade(PL, 1.2), 1)
        g.box(f, f + 1.5, 7.5, 9.5, -4, -3, shade(PL, 1.2), 1)
    g.teeth_rail(24, R1 - 1, 7, -2.5, 2.5, RL, down=True)
    trl = g.teeth_rail(R0 + 1, R1 - 1, U1, -2.5, 2.5, RL)
    for i, f in enumerate(range(R0 + 2, R1 - 1, 3)):
        if i % 2 == 0:
            mark(trl[0], "left", f, f + 1, U1, U1 + 1, shade(WHITE, 0.75))  # the slot numbers
    side_rail(g, 25, R1 - 1, 13.5, 4, "left", RL)
    side_rail(g, 25, R1 - 1, 13.5, -4, "right", RL)
    for f in (25.5, R1 - 1.5):  # the side rails' screws, the bottom rail's
        stud(g, f, 11, 4, "left", PIN, 0.8)
        stud(g, f, 11, -4, "right", PIN, 0.8)
    for f0 in (22, 24):  # the front sling loop on the left
        g.box(f0, f0 + 1, 10.5, 11.5, 4, 5.5, ST, 1)
    g.box(22, 25, 10.5, 11.5, 5.5, 6.5, ST, 1)
    g.box(1, 3, 13.5, 17.5, -4.5, -3.5, shade(PL, 1.12), 2)  # the case deflector behind the port
    g.box(1.5, 2.5, 17, 18, -4.3, -3.3, shade(PL, 1.12), 1, inflate=0.15, tilt=45, pivot=(2, 17.5))
    g.box(18, 34, 17, 18, 3.5, 4.2, DARK, 0)  # the cocking handle's slot on the left
    g.part("charging_handle", 32, 17.5, 4)
    g.use("charging_handle")
    g.box(31, 33, 17, 18, 3.5, 6, shade(ST, 0.85), 1)
    knob = g.box(30, 34, 16, 19, 5.5, 7.5, LO, 2)
    lines(knob, "left", 30, 34, 16, 19, 1, shade(LO, 0.7), vertical=True)
    g.box(30.5, 33.5, 16.5, 18.5, 7.5, 8, shade(LO, 1.2), 1)
    g.use("frame")

    # ------------------------------------------------------------ lower: housing, selector, magazine well, release
    lo = cham(g, -10, 12, 4, U0, -3.5, 3.5, LO, t=0, b=1)
    mark(lo, "left", -10, 12, U0 - 1, U0, shade(LO, 0.7))
    mark(lo, "right", -10, 12, U0 - 1, U0, shade(LO, 0.7))
    for side in ("left", "right"):  # pictograms: safe, semi, auto
        mark(lo, side, -9.5, -8.5, 7, 8.5, WHITE)
        mark(lo, side, -7, -6, 8, 9, RED)
        for f in (-3, -2, -1):
            mark(lo, side, f, f + 0.8, 8, 9, RED)
    for s0, d in ((3.5, 1), (-4.5, -1)):  # ambidextrous selector, at safe
        boss(g, -4.5, 6.5, s0, s0 + 1, 3, shade(LO, 1.3))
        g.box(-9.5 if d > 0 else -7.5, -4.5, 6, 7, s0 + 0.5 * d, s0 + 1 + 0.5 * d, shade(LO, 1.5), 1,
              tilt=-12, pivot=(-4.5, 6.5))
    for f, u in ((-7.5, 5.5), (2, 6.5), (6, 6.5), (10.5, 8.5), (-9, 8.5)):
        studs(g, f, u, 3.5, PIN, 0.8)
    well = g.box(12, 21, 2, U0, -3.5, 3.5, LO)
    mouth = g.box(11.5, 21.5, 1, 2, -4, 4, shade(LO, 0.8), 2)
    mark(mouth, "down", 12.5, 20.5, 0, 0, DARK, -2.5, 2.5)
    lines(well, "left", 13, 20, 4, 9, 2, shade(LO, 0.8))
    lines(well, "right", 13, 20, 4, 9, 2, shade(LO, 0.8))
    for s0 in (3.5, -4.5):  # the magazine catch's cross-bolt ends
        g.box(11, 12.5, 6, 8, s0, s0 + 1, PD, 1)
    g.box(10.5, 11.5, 0, 4, -1, 1, PD, 1)  # paddle release
    pad = g.box(10, 12, -1, 0, -2, 2, PD, 2, tilt=-15, pivot=(11, 0))
    lines(pad, "down", 10, 12, 0, 1, 1, shade(PD, 0.7))

    # ------------------------------------------------------------ grip and the guard that joins its foot
    gr = Raked(g, -14, (-4.5, 4))
    gr.box(-8, -1, -12, 4, -3, 3, LO)
    gr.box(-9, 0, -12, 4, -2, 2, LO)
    for f in (-8, -1):
        for s in (-2, 2):
            gr.vedge(f, s, -12, 3.5, LO)
    for side, (s0, s1) in (("left", (2.5, 3.5)), ("right", (-3.5, -2.5))):
        p = gr.box(-7.5, -1.5, -10.5, 2.5, s0, s1, LO, 1)
        stipple(p, (side,), LO, 1.3)
    for h in (-0.5, -4.5):  # the finger ridges on the front strap
        gr.box(-0.5, 0.5, h - 0.5, h + 0.5, -1.5, 1.5, shade(LO, 0.85), 2, extra=45, inflate=0.207)
    gr.box(-10, -9, -9, 1, -1.5, 1.5, LO, 2)  # palm swell
    foot = gr.box(-10, 1, -14, -12, -3.5, 3.5, PD, 2)
    mark(foot, "down", -9, 0, 0, 0, shade(PD, 0.7), -2.5, 2.5)
    for side in ("left", "right"):
        mark(foot, side, -9.5, -8, -14, -12, DARK)  # the lanyard slot
    # the guard: from the lower's front, down and back to join the grip low on its front strap
    g.box(8.5, 10, -9, 4, -1.5, 1.5, LO, 2)
    g.box(-4, 9.5, -10, -9, -1.5, 1.5, LO, 2)
    edge(g, -4, 9.5, -9.5, 0, shade(LO, 0.8), t=1.3)  # its rounded underside
    g.box(8.8, 9.8, -10, -9, -1.5, 1.5, LO, 2, inflate=0.25, tilt=45, pivot=(9.3, -9.5))
    edge(g, 9.3, 10.3, -9.5, 0, shade(LO, 0.8), t=1.2)
    g.box(7.8, 8.8, -9, -8, -1.5, 1.5, LO, 1, inflate=-0.15, tilt=45)  # inner fillets
    g.box(7.8, 8.8, 2.5, 3.5, -1.5, 1.5, LO, 1, inflate=-0.15, tilt=45)
    g.box(-1, 1, 3, 4, -1, 1, LO, 1)
    mark(lo, "down", 1.5, 3.5, 0, 0, DARK, -0.5, 0.5)
    TR = shade(ST, 1.15)
    g.box(2, 3, 1.5, 3.5, -0.5, 0.5, TR, 1)
    g.box(2.2, 3.2, -0.5, 1.5, -0.5, 0.5, TR, 1, tilt=18, pivot=(2.7, 1.5))
    g.box(1.8, 2.8, -1, 0, -0.5, 0.5, TR, 1, tilt=40, pivot=(2.3, -0.5))

    # ------------------------------------------------------------ barrel and front sight
    g.rod(R1, 43, B, 0, 1.6, GUNMETAL)
    g.rod(R1 + 1, R1 + 2.5, B, 0, 2.3, ST)  # barrel nut
    fs = g.box(30, 35, U1 + 3, U1 + 4, -2, 2, RL, 2)  # front sight: a clamp on the rail, a hood and a post
    g.box(30, 35, U1 + 1, U1 + 3, -3.5, -2.5, RL, 2)
    g.box(30, 35, U1 + 1, U1 + 3, 2.5, 3.5, RL, 2)
    hoop(g, 30.5, 34.5, U1 + 6.5, 0, 2.6, RL, 1, (-135, 135))
    g.box(32, 33, U1 + 4, U1 + 6.5, -0.5, 0.5, DARK, 1)
    boss(g, 32.5, U1 + 2, 3.5, 4.5, 2, PIN)
    for s0 in (2, -3):  # the hood's protective wings
        g.box(30.5, 34.5, U1 + 4, U1 + 6, s0, s0 + 1, RL, 2)

    # ------------------------------------------------------------ magazine: straight, 25 rounds, smoked polymer
    MF, MTOP, MD, MW = 12.5, 9, 8, 5
    MG = "#3c4149"
    mag_bones(g, MF + MD / 2, MTOP)
    mb = g.box(MF, MF + MD, MTOP - 31, MTOP, -MW / 2, MW / 2, MG, 2)
    for side in ("right", "left"):
        for k in range(10):  # the rounds through the wall: brass cases and their bullets, staggered
            u = MTOP - 3 - 2 * k
            off = 0 if k % 2 == 0 else 1
            mark(mb, side, MF + 0.5 + off, MF + 4.5 + off, u - 1, u, shade(BRASS, 0.8))
            mark(mb, side, MF + 4.5 + off, MF + 6.5 + off, u - 1, u, shade(COPPER, 0.75))
        mark(mb, side, MF + 1, MF + MD - 1, MTOP - 24, MTOP - 23, shade(MG, 0.6))  # the follower
        for k in range(3):  # the spring
            mark(mb, side, MF + 1 + k % 2, MF + MD - 2 + k % 2, MTOP - 26 - 2 * k, MTOP - 25 - 2 * k, shade(MG, 0.75))
    for f0 in (MF, MF + MD - 1):  # the solid spines front and back
        g.box(f0, f0 + 1, MTOP - 31, MTOP - 1, -3, 3, shade(MG, 1.2), 2)
    g.box(MF - 0.5, MF + MD + 0.5, MTOP - 10, MTOP - 9, -3, 3, shade(MG, 1.25), 1)  # the stop rib
    g.box(MF, MF + MD, MTOP - 4, MTOP - 1, -3, 3, shade(MG, 1.1), 2)  # the thick top band at the lips
    for s0 in (2.5, -3.5):  # the catch slots in the spine
        g.box(MF + 0.5, MF + 1.5, MTOP - 7, MTOP - 5, s0, s0 + 1, DARK, 0, inflate=-0.1)
    g.box(MF + 2, MF + 6, MTOP - 34, MTOP - 33, -1.5, 1.5, shade(PD, 1.3), 1)  # the floorplate catch
    fp = g.bevel(MF - 1, MF + MD + 1, MTOP - 33, MTOP - 31, -3.5, 3.5, PD, 0.7)
    g.box(MF + MD + 0.5, MF + MD + 1.5, MTOP - 33, MTOP - 30, -2, 2, PD, 2)
    g.box(MF + 1, MF + MD - 1, MTOP, MTOP + 1, -2.5, -1.5, MG, 1)
    g.box(MF + 1, MF + MD - 1, MTOP, MTOP + 1, 1.5, 2.5, MG, 1)
    cartridge(g, MF + 1, MTOP + 0.7, 0, MD - 2, 1.1)
    g.mag_profile = dict(f0=MF - 1, top=MTOP, width=MW, segs=[(0, 31)], color=MG, kind="smg_straight")

    # ------------------------------------------------------------ factory sights, muzzle, stock
    g.use("frame")
    g.mount("optic", 12, U1 + 3, length=36)
    g.use("def_optic")  # the drum rear sight on the rail
    g.box(-9.5, -3.5, U1 + 3, U1 + 4, -2, 2, RL, 2)
    for s0 in (2.5, -3.5):
        g.box(-9.5, -3.5, U1 + 1, U1 + 3, s0, s0 + 1, RL, 2)
    g.box(-9, -4, U1 + 4, U1 + 5, -1.5, 1.5, RL, 2)
    dr = spin(g, -6.5, U1 + 6.5, -1.5, 1.5, 2.3, shade(RL, 1.05), 2)
    endmark(dr[0], "rear", -0.5, 0.5, U1 + 6, U1 + 7, DARK)
    endmark(dr[0], "front", -0.5, 0.5, U1 + 6, U1 + 7, DARK)
    for s0 in (1.5, -2.5):
        spin(g, -6.5, U1 + 6.5, s0, s0 + 1, 2.5, shade(RL, 1.25), 2)
    g.box(-7, -6, U1 + 4.5, U1 + 5.5, 2.5, 3.5, WHITE, 0, inflate=-0.2)
    g.box(-8.5, -5.5, U1 + 3, U1 + 4.5, -4, -2.5, shade(SILVER, 0.7), 1, inflate=-0.1)  # windage knob
    endmark(g.box(-7.5, -6.5, U1 + 3.2, U1 + 4.2, -4.3, -3.8, DARK, 0), "rear", -4.3, -3.8, U1 + 3, U1 + 4, DARK)
    boss(g, -6.5, U1 + 2, -4.5, -3.5, 2, PIN)
    g.mount("muzzle", 43, B, bore=1.6)
    g.use("def_muzzle")
    g.rod(43, 44, B, 0, 2.2, shade(RL, 1.1))  # collar
    for c in g.rod(44, 46, B, 0, 2.0, RL):
        lines(c, "up", 44, 46, 0, 1, 1, shade(RL, 0.7), vertical=True)
    g.rod(45.5, 46.02, B, 0, 0.9, DARK, 0)
    g.muzzle = (46.0, B)
    g.use("frame")
    g.mount("underbarrel", 30, 4, length=10, default=False)
    g.mount("side", 30, 13.5, 7, length=10, default=False)
    g.mount("stock", -12, 14)
    g.use("def_stock")  # the side-folding skeleton stock (it folds to the right)
    hb = g.box(-14.5, -12, 8, U1, -3.5, 3.5, LO)  # hinge block
    for u0, u1 in ((9, 12), (16, 19)):
        vrod(g, u0, u1, -12, -4, 1.2, ST)  # hinge knuckles on the right
    boss(g, -13, 14, 3.5, 4.5, 3, shade(SILVER, 0.75))  # release button on the left
    g.box(-14.5, -12, 7, 8, -3, 3, LO, 2)  # the hinge's lower lug
    endmark(g.box(-15, -14.5, 10, 18, -3, 3, PD, 1), "rear", -2, 2, 13, 15, shade(PD, 0.7))
    top = g.box(-40, -14, 16, 19.5, -2.5, 2.5, LO)  # the comb
    edge(g, -40, -14, 19, 2, shade(LO, 1.3), t=1)
    edge(g, -40, -14, 19, -2, shade(LO, 1.3), t=1)
    for side in ("left", "right"):
        mark(top, side, -38, -16, 17, 18, shade(LO, 0.75))
    st = Raked(g, 11, (-14, 9))  # the lower strut, down to the toe
    lowb = st.box(-40, -14, 7, 10, -2, 2, LO)
    for side in ("left", "right"):
        mark(lowb, side, -36, -18, 8, 9, shade(LO, 0.75))
    stud(g, -16, 17.5, 2.5, "left", PIN, 0.8)
    stud(g, -16, 17.5, -2.5, "right", PIN, 0.8)
    for f0 in (-38, -36):  # the rear sling loop through the comb
        g.box(f0, f0 + 1, 15, 16, -1, 1, ST, 1)
    g.box(-38, -35, 14, 15, -1, 1, ST, 1)
    bt = g.bevel(-43, -39, 2, 20, -3.5, 3.5, LO, 1)  # the butt
    pad = g.bevel(-44.5, -43, 1.5, 20.5, -3.5, 3.5, RUBBER, 0.8)
    lines(pad[0], "right", -44.5, -43, 2, 20, 2, shade(RUBBER, 1.6))
    lines(pad[0], "left", -44.5, -43, 2, 20, 2, shade(RUBBER, 1.6))
    g.box(-41, -40, 4, 6, 3.5, 4, DARK, 0)  # the sling slot
    g.use("frame")
    return g


# =========================================================================== rifles
