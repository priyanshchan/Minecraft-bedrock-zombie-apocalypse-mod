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
from kit import FACES, GRIP, paint


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
    """H&K MP5A3, 9x19mm: stamped receiver with its rib, ejection port with the bolt showing, trigger pack with
    four-position selector, straight curved magazine, slim handguard, cocking tube and handle, drum rear sight,
    hooded front sight on its barrel clamp, three-lug muzzle, retractable wire stock."""
    g = gun("mp5", "rifle", "ar")
    BK, BKD, BKL = BLACK, shade(BLACK, 0.8), shade(BLACK, 1.2)
    PL, PD = POLY, shade(POLY, 0.8)
    PIN = shade(SILVER, 0.6)
    # ------------------------------------------------------------ receiver
    g.box(-10, 34, 11, 19, -3, 3, BKD)
    wl = g.box(-10, 34, 10, 19, 3, 4, BK)
    for f0, f1, u0, u1 in ((-10, 4, 10, 19), (14, 34, 10, 19), (4, 14, 10, 13), (4, 14, 17, 19)):
        g.box(f0, f1, u0, u1, -4, -3, BK)
    cap = g.box(-10, 34, 19, 20, -3, 3, BK)
    edge(g, -10, 34, 19, 3, BKL)
    edge(g, -10, 34, 19, -3, BKL)
    edge(g, -10, 34, 11, 3, shade(BK, 0.8))
    edge(g, -10, 34, 11, -3, shade(BK, 0.8))
    for side in ("right", "left"):
        mark(wl, side, -8, 32, 14, 15, shade(BK, 1.3))  # the stamped rib
    mark(wl, "left", 15, 33, 11, 12, shade(BK, 0.7))
    engrave(wl, "left", 16, 17, text(8, 5), shade(SILVER, 0.65))  # H&K MP5A3 / serial
    g.box(-12, -10, 11, 19, -3, 3, BKD)  # rear cap
    g.box(-12, -10, 12, 18, -2, 2, BK)
    g.box(-11, -10, 14, 16, -1, 1, DARK, 1)  # stock hinge pin
    g.box(4, 5, 12.5, 17.5, -3, -2, DARK, 0)
    g.box(4, 14, 13, 17, -3, -2.9, DARK, 0)  # the ejection port: dark inside
    g.box(3, 4, 13, 17, -4.4, -3.5, BKD, 1)  # port deflector
    g.part("bolt", 9, 15)
    g.box(5, 13, 13.5, 16.5, -3.5, -2.5, STEEL, 2, bone="bolt")
    g.box(6, 8, 14.5, 15.5, -4, -3.5, SILVER, 1, bone="bolt")  # bolt face and extractor
    g.box(9, 12, 16.5, 17, -3.5, -2.5, shade(STEEL, 1.2), 1, bone="bolt")
    g.use("frame")
    # ------------------------------------------------------------ trigger pack and grip
    lower = cham(g, -8, 14, 3, 10, -4, 4, PL, t=0, b=1)
    mark(lower, "left", -6, 2, 6, 8, shade(POLY, 1.4))
    mark(lower, "right", -6, 2, 6, 8, shade(POLY, 1.4))
    for f, c in ((-6, WHITE), (-4, RED)):
        mark(lower, "left", f, f + 1, 8, 9, c)
    for s0 in (4, -5):  # selector: pivot disc and a long thumb lever
        spin(g, -5, 7.5, s0, s0 + 1, 1.5, SILVER)
        g.box(-9, -4, 7, 8.5, s0, s0 + 1, shade(POLY, 0.6) if s0 > 0 else POLY, 1)
        g.box(-9.5, -8.5, 6.5, 9, s0, s0 + 1, POLY, 1)
    g.pistol_grip(-10, -2, 4, 15, 6, POLY, angle=14)
    g.box(-11, -3, -11.5, -10.5, -3, 3, PD, 2, tilt=-14, pivot=(-6, 4))  # grip cap
    g.box(-2, 12, -1, 1, -1.5, 1.5, PL)  # trigger guard, rounded in front
    g.box(11, 12, -1, 3, -1.5, 1.5, PL)
    g.box(11.5, 12.5, -1, 0, -1.5, 1.5, PL, 1, inflate=-0.15, tilt=45)
    g.box(1, 3, 1, 4, -0.5, 0.5, SILVER, 1)  # curved trigger shoe
    g.box(1.5, 3.5, 0, 1.5, -0.5, 0.5, SILVER, 1, tilt=20, pivot=(2.5, 1.5))
    g.box(12, 22, 3, 10, -4, 4, BK)  # magwell, flared at its mouth
    g.box(11, 23, 2, 3.5, -4.6, 4.6, BKD, 2)
    g.box(10, 12, -1, 3, -1, 1, DARK)  # paddle release
    g.box(8, 11, 8, 11, 4, 4.8, STEEL, 1)  # slap lever on the left
    g.pin(12, 8, 4, "left")
    g.pin(-2, 8, 4, "left")
    # ------------------------------------------------------------ cocking tube, handguard, barrel
    g.rod(30, 50, 17.5, 0, 2, BK)
    g.part("charging_handle", 40, 18, 3)
    g.box(36, 40, 17, 19, 2, 7, BK, 2, bone="charging_handle")
    g.box(36, 40, 15.5, 20.5, 6.5, 9, PL, 2, bone="charging_handle")
    hg = cham(g, 22, 44, 7, 15, -4.5, 4.5, PL, t=1, b=1)
    for side in ("right", "left"):
        face = getattr(hg, FACES[side])
        for y in range(1, face.h, 3):
            face.hline(y, shade(POLY, 0.55))
    ribs(hg, ("down",), 3, shade(POLY, 0.6))
    g.box(21, 22, 8, 14, -4, 4, PD, 2)
    g.rod(44, 56, 12, 0, 2, GUNMETAL, facets=3)  # barrel
    g.rod(43, 46, 12, 0, 3, STEEL)  # barrel nut
    g.rod(46, 50, 12, 0, 3, BK)  # sight clamp
    for s in (-2.5, 1.5):  # hooded front sight
        g.box(44, 48, 14, 25, s, s + 1, BK)
    g.box(44, 48, 25, 26, -2.5, 2.5, BK)
    g.box(45, 47, 16, 23, -0.5, 0.5, DARK)
    sling_swivel(g, 40, 7, 0, True)  # sling loop under the handguard
    g.muzzle = (58.0, 12.0)
    # ------------------------------------------------------------ magazine
    mag_bones(g, 17, 4)
    segs = [(1, 8), (2, 6), (4, 6), (7, 6), (10, 5)]
    cs = curved_mag(g, 12, 6, 4, segs, STEEL)
    for c in cs:
        mark(c, "right", c.ext[0] + 7, c.ext[0] + 8, c.ext[3] - 4, c.ext[3] - 3, BRASS)  # witness holes
    g.box(13, 23, -23, -20, -3.5, 3.5, shade(STEEL, 0.7), 2)  # baseplate
    g.mag_profile = dict(f0=13, top=4, width=6, segs=segs, color=STEEL, kind="smg")
    # ------------------------------------------------------------ rail, rear sight, muzzle, stock
    g.teeth_rail(-2, 20, 20, -2, 2, BK)  # claw-mount rail
    g.mount("optic", 8, 23, length=20)
    g.use("def_optic")
    g.box(-8, -2, 20, 22, -3, 3, BK)  # drum rear sight
    sd = spin(g, -5, 24.5, -2.5, 2.5, 2.6, BK)
    g.box(-5.5, -4.5, 22, 27, -2.6, 2.6, DARK, 1, inflate=-0.3)
    spin(g, -5, 24.5, 2.5, 4, 1.6, BKL)  # elevation knob
    g.box(-7, -3, 26.5, 27.5, -1, 1, DARK, 1)
    g.mount("muzzle", 54, 12, bore=2)
    g.use("def_muzzle")
    for c in g.rod(52, 58, 12, 0, 2.6, BK):
        slots(c, ("right", "left"), 53, 57, c.ext[2], c.ext[3], 2, 1)
    g.box(53, 55, 14, 16, -0.5, 0.5, BK)  # three lugs
    g.box(53, 55, 9, 10, -3, -2, BK)
    g.box(53, 55, 9, 10, 2, 3, BK)
    g.use("frame")
    for f in range(25, 43, 3):  # finger ribs round the handguard
        for s0 in (4.5, -5):
            g.box(f, f + 1.5, 8, 14, s0, s0 + 0.5, shade(PL, 1.2), 1)
        g.box(f, f + 1.5, 6.5, 7, -3, 3, shade(PL, 1.2), 1)
    for f, u in ((-7, 6), (6, 5), (-8, 14), (26, 15)):
        g.pin(f, u, 4, "left")
        g.pin(f, u, -4, "right")
    for f in (31, 33, 47):  # bands on the cocking tube and barrel
        g.rod(f, f + 1.5, 17.5, 0, 2.5, STEEL)
    g.box(21, 23, 3, 11, -4.5, 4.5, BKD, 2)  # front of the magwell
    g.mount("underbarrel", 34, 7, length=12, default=False)
    g.mount("side", 34, 11, 5, length=10, default=False)
    g.mount("stock", -10, 13)
    g.use("def_stock")
    g.box(-14, -10, 8, 20, -4, 4, BK)  # collar with its release button
    g.box(-14, -11, 14, 16, 4, 5, SILVER, 1)
    for s in (-4, 4):
        g.rod(-42, -14, 16, s, 1, SILVER)  # struts and the lower rods
        g.rod(-42, -22, 6, s, 1, SILVER)
        g.rod(-22, -14, 11, s, 1, SILVER, bone=None)
    g.box(-30, -29, 6, 17, -4.5, -3.5, SILVER, 1)
    g.box(-30, -29, 6, 17, 3.5, 4.5, SILVER, 1)
    bp = g.bevel(-46, -42, 2, 20, -5, 5, RUBBER, 1)
    ribs(bp[0], ("right", "left"), 3, shade(RUBBER, 1.6))
    g.box(-44, -42, 16, 20, -5, 5, PL)
    g.use("frame")
    return g


def ump45():
    """H&K UMP45, .45 ACP: a polymer receiver with its moulded grooves, integral trigger guard and grip, ejection
    port with the bolt showing, ambidextrous selector, a translucent 25-round magazine, rails on top and sides,
    folding sight and a short barrel with a slotted hider, and the side-folding tubular stock."""
    g = gun("ump45", "rifle", "ar")
    PL, PD, PLL = POLY, shade(POLY, 0.78), shade(POLY, 1.2)
    # ------------------------------------------------------------ polymer body
    up = cham(g, -10, 36, 12, 20, -5, 5, PL, t=1.5, b=0)
    low = cham(g, -8, 34, 6, 12, -4.5, 4.5, PL, t=0, b=1)
    for c in (up, low):
        for side in ("right", "left"):
            for f in range(-6, 34, 5):
                mark(c, side, f, f + 1, c.ext[2] + 1, c.ext[3] - 1, shade(POLY, 0.7))
    for side in ("right", "left"):
        mark(up, side, 30, 36, 13, 14, PD)
    g.box(-12, -10, 11, 19, -4, 4, PD)  # rear cap
    engrave(up, "left", -2, 18, text(8, 9), shade(SILVER, 0.6))  # H&K UMP45
    g.box(4, 14, 13, 17, -5.3, -3, DARK)  # ejection port
    g.part("bolt", 9, 15)
    g.box(5, 13, 13.5, 16.5, -4.5, -3.5, STEEL, 2, bone="bolt")
    g.box(6, 8, 14.5, 15.5, -5, -4.5, SILVER, 1, bone="bolt")
    g.use("frame")
    # integral trigger guard, trigger, grip
    g.box(-4, 10, -4, -2, -1.5, 1.5, PL)
    g.box(9, 10, -4, 6, -1.5, 1.5, PL)
    g.box(9.5, 11, -4, -3, -1.5, 1.5, PL, 1, inflate=-0.15, tilt=45)
    g.box(-4, -3, -4, 6, -1.5, 1.5, PL)
    g.box(2, 4, -1, 5, -0.5, 0.5, SILVER, 1)
    g.box(1.5, 3.5, -2, -0.5, -0.5, 0.5, SILVER, 1, tilt=25, pivot=(2.5, -0.5))
    g.pistol_grip(-12, -4, 6, 16, 6, PL, angle=10)
    g.box(-13, -3, -10.5, -9.5, -3.5, 3.5, PD, 2, tilt=-10, pivot=(-8, 6))
    for s0 in (5, -6):  # selector lever with its marking disc
        spin(g, -4, 10, s0, s0 + 1, 1.6, SILVER)
        g.box(-8, -3, 9.5, 10.5, s0, s0 + 1, PD if s0 > 0 else PL, 1)
    mark(up, "left", -6, -4, 14, 15, WHITE)
    mark(up, "left", -4, -2, 14, 15, RED)
    g.box(8, 10, 1, 4, 4.5, 5.5, SILVER, 1)  # magazine catch, both sides
    g.box(8, 10, 1, 4, -5.5, -4.5, SILVER, 1)
    g.box(10, 20, 0, 6, -4, 4, PL)  # magwell
    g.box(9, 21, -1, 1, -4.5, 4.5, PD, 2)
    # rails
    g.teeth_rail(-8, 34, 20, -3, 3, PL)
    g.teeth_rail(24, 36, 14, 5, 6, PL)
    g.teeth_rail(24, 36, 6, -3, 3, PL, down=True)
    g.box(36, 38, 8, 18, -3.5, 3.5, PL)  # nose of the handguard
    # charging handle (a reciprocating knob on the left)
    g.part("charging_handle", 30, 16, 5)
    g.box(26, 32, 15, 17, 5, 8, BLACK, 2, bone="charging_handle")
    g.box(30, 32, 14, 18, 7, 9, PL, 2, bone="charging_handle")
    g.box(24, 34, 15, 17, 4.5, 5, DARK, 0)  # its slot
    # barrel
    g.rod(38, 44, 13, 0, 2, GUNMETAL, facets=3)
    g.muzzle = (46.0, 13.0)
    # ------------------------------------------------------------ translucent magazine
    mag_bones(g, 15, 0)
    mg = g.box(11, 19, -28, 2, -3, 3, "#2a2b30")
    ribs(mg, ("right", "left"), 3, shade("#2a2b30", 1.5))
    for side, x in (("left", 0), ("right", 0)):
        mark(mg, side, 12, 18, -22, -6, "#3d3f46")  # see-through window
        for k in range(6):
            mark(mg, side, 13 + (k % 2) * 2, 16 + (k % 2) * 2, -20 + k * 2.5, -19 + k * 2.5, BRASS)
    g.box(10, 20, -30, -28, -4, 4, PL)
    g.box(10, 20, -29, -28, 3.5, 4.5, PD)
    g.mag_profile = dict(f0=11, top=2, width=6, segs=[(0, 30)], color="#2a2b30", kind="smg_straight")
    # ------------------------------------------------------------ sights, muzzle, stock
    g.mount("optic", 12, 23, length=36)
    g.use("def_optic")
    rs = g.box(-6, -2, 23, 24, -3, 3, PL)  # folding rear sight
    for s0 in (-3, 2):
        g.box(-6, -2, 24, 27, s0, s0 + 1, PL)
    g.box(-5, -3, 25, 26, -2, 2, DARK, 1)
    g.box(-5, -3, 24, 26, -1, 1, DARK)
    g.box(30, 33, 23, 25, -1.5, 1.5, PL)  # folding front sight post
    g.box(31, 32, 25, 28, -0.5, 0.5, PL)
    g.mount("muzzle", 44, 13, bore=2)
    g.use("def_muzzle")
    for c in g.rod(43, 46, 13, 0, 2.5, BLACK):
        slots(c, ("right", "left"), 43.5, 45.5, c.ext[2], c.ext[3], 2, 1)
    g.use("frame")
    for f in range(22, 36, 3):  # grooves and ribs of the moulded forend
        for s0 in (5, -5.5):
            g.box(f, f + 1.5, 8, 12, s0, s0 + 0.5, shade(PL, 1.25), 1)
        g.box(f, f + 1.5, 6, 6.5, -3.5, 3.5, shade(PL, 1.25), 1)
    for f in range(-6, 8, 4):
        g.box(f, f + 2, 18, 19, -5.4, -5, shade(PL, 1.25), 1)
        g.box(f, f + 2, 18, 19, 5, 5.4, shade(PL, 1.25), 1)
    for f, u in ((-8, 8), (24, 9), (6, 9)):
        g.pin(f, u, 4.5, "left")
        g.pin(f, u, -4.5, "right")
    g.box(36, 37, 11, 15, -2, 2, DARK, 1)  # barrel shroud opening
    g.box(-2, 6, -4, -3, -2, 2, PD, 2)  # the thick guard floor
    g.box(-1, 0, -4, -2, -2, 2, PD, 1)
    g.mount("underbarrel", 30, 3, length=10, default=False)
    g.mount("side", 30, 15, 6, length=10, default=False)
    g.mount("stock", -10, 13)
    g.use("def_stock")
    g.box(-13, -10, 8, 18, -5, 5, PL)  # hinge with its latch
    g.box(-13, -11, 12, 15, 5, 6.5, BLACK, 1)
    spin(g, -12, 13, -5.5, 5.5, 1.2, SILVER)
    g.rod(-40, -12, 18, 0, 1.2, STEEL)  # tubular frame
    g.rod(-40, -14, 7, 0, 1.2, STEEL)
    g.box(-31, -29, 7, 18, -2, 2, PL)
    g.box(-31, -29, 8, 17, -1, 1, DARK, 0)
    bp = g.bevel(-43, -40, 4, 20, -4, 4, RUBBER, 1)
    ribs(bp[0], ("right", "left"), 3, shade(RUBBER, 1.6))
    g.use("frame")
    return g


# =========================================================================== rifles
