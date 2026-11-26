"""Rifles: M4A1, AKM / AK-47, M249 SAW, SVD Dragunov.

Each is built after its real counterpart from boxes in the kit's (f, u, s) frame (see kit.py): real relief for
anything that stands proud (pins, levers, ribs, slots), painted marks for engravings. The helpers below add the
shapes the kit has no call for: round bosses across the gun or upright, studs, chamfered edges, through-slots."""
from __future__ import annotations

import math

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, gun, mag_bones, mag_lips, qd_cup, roll_mark, sling_swivel
from kit import GRIP, paint

R2 = (math.sqrt(2) - 1) / 2  # the inflation that turns a unit square turned 45 degrees into an octagon's flats


# ---------------------------------------------------------------- shapes

def rbox(g, f0, f1, u0, u1, s0, s1, color, noise=3, inflate=0.0, rot=(0.0, 0.0, 0.0), pivot=None, bone=None):
    """g.box with any turn (tilt, roll, yaw): yaw turns about the up axis (positive swings the front to the
    left). Used for upright round knobs."""
    size = (max(1, round(s1 - s0)), max(1, round(f1 - f0)), max(1, round(u1 - u0)))
    origin = (GRIP[0] + s0, GRIP[1] + f0, GRIP[2] - (u0 + size[2]))
    pf, pu, ps = pivot if pivot else ((f0 + f1) / 2, (u0 + u1) / 2, (s0 + s1) / 2)
    target = g.bones[bone] if bone else g.cur
    turn = tuple(float(v) for v in rot) if any(rot) else None
    c = target.cube(origin, size, inflate, turn, g.at(pf, pu, ps) if turn else None)
    c.ext = (f0, f0 + size[1], u0, u0 + size[2], s0, s0 + size[0])
    paint(c, color, noise, g.seed + len(target.cubes) * 7)
    return c


def _round(g, a, b, d, place, color, noise, bone, turn):
    """The cross-section of a round boss d units across, centred on (a, b) in the plane that `place` maps to a
    box: a plus for small heads, a cross with a square for d = 3, an octagon (two crossed boxes and four
    chamfers) from d = 4."""
    out = []
    if d <= 2:
        h = d / 2
        out.append(place(a - h, a + h, b - 0.5, b + 0.5, color, 0.0, None))
        out.append(place(a - 0.5, a + 0.5, b - h, b + h, color, 0.0, None))
    elif d == 3:
        out.append(place(a - 1.5, a + 1.5, b - 0.5, b + 0.5, color, 0.0, None))
        out.append(place(a - 0.5, a + 0.5, b - 1.5, b + 1.5, color, 0.0, None))
        out.append(place(a - 1, a + 1, b - 1, b + 1, color, 0.0, None))
    else:
        h = d / 2
        out.append(place(a - h, a + h, b - h + 1, b + h - 1, color, 0.0, None))
        out.append(place(a - h + 1, a + h - 1, b - h, b + h, color, 0.0, None))
        for da in (-1, 1):
            for db in (-1, 1):
                ca, cb = a + da * (h - 1), b + db * (h - 1)
                light = 1.15 if db > 0 else 0.85
                out.append(place(ca - 0.5, ca + 0.5, cb - 0.5, cb + 0.5, shade(color, light), R2, (ca, cb)))
    return out


def disc(g, f, u, s0, s1, r, color, noise=2, bone=None):
    """A round boss whose axis runs across the gun (along s), from s0 to s1: it reads round from the side
    (pins, knobs, swivels, turrets)."""
    def place(a0, a1, b0, b1, col, infl, centre):
        if centre is None:
            return g.box(a0, a1, b0, b1, s0, s1, col, noise, bone=bone)
        return g.box(a0, a1, b0, b1, s0, s1, col, noise, inflate=infl, tilt=45, pivot=(centre[0], centre[1], (s0 + s1) / 2), bone=bone)
    return _round(g, f, u, max(1, round(2 * r)), place, color, noise, bone, None)


def knob(g, f, s, u0, u1, r, color, noise=2, bone=None):
    """An upright round knob (axis along u), from u0 to u1: it reads round from above."""
    def place(a0, a1, b0, b1, col, infl, centre):
        if centre is None:
            return g.box(a0, a1, u0, u1, b0, b1, col, noise, bone=bone)
        return rbox(g, a0, a1, u0, u1, b0, b1, col, noise, infl, (0.0, 0.0, 45.0), (centre[0], (u0 + u1) / 2, centre[1]), bone)
    return _round(g, f, s, max(1, round(2 * r)), place, color, noise, bone, None)


def stud(g, f, u, s, side, color=None, size=1.0, proud=0.5, bone=None):
    """A rivet or pin head on a side whose surface is at s, standing `proud` out of it."""
    col = color or shade(SILVER, 0.8)
    h = size / 2
    if side == "left":
        s0, s1 = s + proud - 1, s + proud
    else:
        s0, s1 = s - proud, s - proud + 1
    return g.box(f - h, f + h, u - h, u + h, s0, s1, col, 1, inflate=-0.08, bone=bone)


def pins(g, f, u, half, color=None, size=1.0, bone=None):
    """The same pin seen on both sides of a part half as wide as `half`."""
    return [stud(g, f, u, half, "left", color, size, bone=bone), stud(g, f, u, -half, "right", color, size, bone=bone)]


def edge(g, f0, f1, u, s, color, light=1.2, bone=None, k=1.0):
    """A chamfer along f: a slim square turned 45 degrees about the barrel axis at (u, s)."""
    return g.box(f0, f1, u - k / 2, u + k / 2, s - k / 2, s + k / 2, shade(color, light), 1, inflate=R2 * k,
                 roll=45, pivot=(0, u, s), bone=bone)


def slotted(g, f0, f1, u0, u1, s0, s1, color, rows, inner=DARK, bone=None, noise=3):
    """A part whose two sides have real through-slots: `rows` is [(su0, su1, [(f0, f1), ...]), ...] from the
    bottom up. A dark core shows through the slots; strips run between the rows and posts between the slots."""
    g.box(f0, f1, u0, u1, s0 + 1, s1 - 1, inner, 1, bone=bone)
    out = []
    u = u0
    for su0, su1, cuts in rows:
        if su0 > u:
            out.append(g.box(f0, f1, u, su0, s0, s1, color, noise, bone=bone))
        edges = [f0] + [x for a, b in cuts for x in (a, b)] + [f1]
        for a, b in zip(edges[::2], edges[1::2]):
            if b > a:
                out.append(g.box(a, b, su0, su1, s0, s1, color, noise, bone=bone))
        u = su1
    if u1 > u:
        out.append(g.box(f0, f1, u, u1, s0, s1, color, noise, bone=bone))
    return out


def lines(c, side, f0, f1, u0, u1, every, color, vertical=False):
    """Parallel engraved lines over an area of a side: along f (laminations, grooves) or across it."""
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


def stitch(c, side, f0, f1, u, color, gap=2):
    """A dashed seam along f."""
    f = f0
    while f + 1 <= f1:
        mark(c, side, f, f + 1, u, u + 1, color)
        f += gap


def stitch_v(c, side, f, u0, u1, color, gap=2):
    """A dashed seam up a side."""
    u = u0
    while u + 1 <= u1:
        mark(c, side, f, f + 1, u, u + 1, color)
        u += gap


def end_dot(c, color, rear=True, front=True):
    """A dark centre on the end faces of a box (a bore, a peep hole)."""
    for face in ([c.bottom] if rear else []) + ([c.top] if front else []):
        cx, cy = face.w // 2, face.h // 2
        face.fill(color, max(0, cx - (1 if face.w > 3 else 0)), max(0, cy - (1 if face.h > 3 else 0)), cx + 1, cy + 1)


def bore(g, f, u, r, depth=1, bone=None):
    """The dark mouth of a bore facing forward."""
    return g.rod(f - depth, f + 0.02, u, 0, r, DARK, 0, bone=bone)


def soften(c, edges=("bottom",)):
    """Undo the painted edge light or shadow along the long edges of a box's two sides, for a box whose edge
    runs across another part of the same surface (a seam that should not show)."""
    for face, bottom_x, top_x in ((c.right, 0, c.right.w - 1), (c.left, c.left.w - 1, 0)):
        if face.w < 3:
            continue
        for name in edges:
            x = bottom_x if name == "bottom" else top_x
            nx = x + 1 if x == 0 else x - 1
            for y in range(face.h):
                face.px(x, y, face.get(nx, y))


def curve_mag(g, f0, top, width, segs, color, overlap=0.6, last_turn=None):
    """A curved box magazine following a mag_profile's segments: each segment is the profile's box, turned about
    the middle of its top edge so that its bottom meets the next segment (a smooth curve instead of steps).
    Returns [(box, df, u_top, h, angle, pivot)] so details can be added in each segment's own frame."""
    s = width / 2
    out = []
    u = top
    for i, (df, h) in enumerate(segs):
        if i + 1 < len(segs):
            step = segs[i + 1][0] - df
        else:
            step = (df - segs[i - 1][0]) * (last_turn if last_turn is not None else 1.0) if i else 0
        ang = math.degrees(math.atan2(step, h))
        piv = (f0 + df + 5, u)
        c = g.box(f0 + df, f0 + df + 10, u - h - overlap, u, -s, s, color, tilt=ang, pivot=piv)
        if i:
            soften(c, ("top",))
        out.append((c, df, u, h, ang, piv))
        u -= h
    return out


def on_seg(g, seg, f0, f1, u0, u1, s0, s1, color, noise=2, **kw):
    """A box placed in a magazine segment's own frame (see curve_mag): it turns with the segment."""
    _c, _df, _u, _h, ang, piv = seg
    return g.box(f0, f1, u0, u1, s0, s1, color, noise, tilt=ang, pivot=piv, **kw)


# =========================================================================== M4A1

def m4a1():
    """Colt M4A1: flat-top upper on a 6-position stock, M-LOK free-float handguard, A-frame front sight, A2
    birdcage and a 30-round PMAG."""
    g = gun("m4a1", "rifle", "ar")
    B = 13.5  # bore line
    LO = shade(BLACK, 0.92)  # the lower is a touch darker than the upper
    # ------------------------------------------------ lower receiver
    tower = g.box(-8, -5, 3, 13, -3.5, 3.5, LO)  # buffer tower behind the upper
    g.rod(-8, -5, B, 0, 3.3, LO)
    body = g.box(-5, 10, 3, 10, -3.5, 3.5, LO)  # fire-control housing
    g.box(-5, 10, 3, 4, -3, 3, shade(LO, 0.8))
    well = g.box(10, 23, 1, 10, -3.5, 3.5, LO)  # magazine well
    g.bevel(9.5, 23.5, -1, 2, -4.2, 4.2, LO, 0.8)  # its flared mouth
    g.box(22, 25, 6, 10, -2.5, 2.5, LO)  # front pivot lug
    g.box(10, 23, 9.5, 10.5, -3.7, 3.7, shade(LO, 1.1), 1)  # the lip under the upper
    for c in (well,):
        roll_mark(c, "left", 12, 21, 6, shade(LO, 1.55))  # COLT  M4A1 CARBINE
        roll_mark(c, "left", 12.5, 18, 3.5, shade(LO, 1.55))  # CAL 5.56 MM
        mark(c, "left", 14, 20, 2, 3, shade(LO, 1.4))  # serial number
    mark(body, "left", 3, 4, 8.5, 9.5, WHITE)  # SAFE
    mark(body, "left", -1.5, -0.5, 9.5, 10, WHITE)  # SEMI
    mark(body, "left", -4.5, -3.5, 8, 9, RED)  # AUTO
    mark(tower, "left", -7.5, -5.5, 4, 5, shade(LO, 0.7))
    # trigger guard and trigger
    g.box(1.5, 10, -1, 0, -1, 1, LO, 2)
    g.box(9, 10.5, -1, 3, -1, 1, LO, 2)
    g.box(0.5, 2.5, -1, 3, -1, 1, LO, 2, tilt=-18, pivot=(1.5, 3))
    pins(g, 9.8, 1.5, 1, size=0.8)
    g.box(4.5, 5.5, 1, 3, -0.5, 0.5, STEEL, 1)
    g.box(4.5, 5.5, -0.5, 1.5, -0.5, 0.5, STEEL, 1, tilt=22, pivot=(5, 1.5))
    # bolt catch (left), magazine release with its fence (right)
    g.box(7.5, 9.5, 5.5, 10, 3.2, 4.2, LO, 2)
    paddle = g.box(7, 10, 4.5, 6.5, 3.6, 4.6, shade(LO, 1.15), 1)
    lines(paddle, "left", 7, 10, 4.5, 6.5, 2, shade(LO, 0.6), vertical=True)
    stud(g, 8.5, 9, 4.2, "left", size=0.8)
    disc(g, 11.8, 7.2, -4.4, -3.4, 1.1, shade(STEEL, 0.9))
    g.box(9.5, 14, 4.5, 5.5, -4.1, -3.1, LO, 2)  # fence below the button
    g.box(13.5, 14.5, 4.5, 9, -4.1, -3.1, LO, 2)  # and in front of it
    # ambidextrous selector, pointing at SAFE
    disc(g, -1, 7.8, 3.2, 4.2, 1.5, LO)
    g.box(-1, 3.5, 7.2, 8.4, 3.7, 4.7, shade(LO, 1.2), 1)
    g.box(2.5, 4, 6.8, 8.8, 4.0, 5.0, shade(LO, 1.2), 1)
    disc(g, -1, 7.8, -4.2, -3.2, 1.5, LO)
    g.box(-4, -1, 7.3, 8.3, -4.7, -3.7, shade(LO, 1.2), 1)
    # takedown and pivot pins, hammer and trigger pins
    for f, u in ((-3.5, 9), (24, 8.3)):
        disc(g, f, u, 3.1, 4.1, 1.0, shade(LO, 1.3))
        disc(g, f, u, -4.1, -3.1, 1.0, shade(LO, 1.3))
    for f, u in ((2, 6.6), (5, 6.2)):
        pins(g, f, u, 3.5, size=1)
    # A2 pistol grip with its finger nub
    g.pistol_grip(-6, 2, 3, 15, 6, POLY, angle=18)
    g.box(2, 3, -4.5, -1.5, -2.5, 2.5, POLY, 2, tilt=-18, pivot=(-2, 3))
    g.box(-7, -5, 1, 3, -2.5, 2.5, POLY, 2, tilt=-18, pivot=(-2, 3))  # tang against the lower
    # ------------------------------------------------ upper receiver (port open, the carrier shows)
    core = g.box(-5, 25, 10, 17, -3, 3, BLACK)
    up_l = g.box(-5, 25, 11, 16, 3, 4, BLACK)
    g.box(-5, 4, 11, 16, -4, -3, BLACK)
    g.box(14, 25, 11, 16, -4, -3, BLACK)
    g.box(4, 14, 11, 12, -4, -3, BLACK)
    g.box(4, 14, 15, 16, -4, -3, BLACK)
    edge(g, -5, 25, 16, 3, BLACK)
    edge(g, -5, 25, 16, -3, BLACK)
    edge(g, -5, 25, 11, 3, BLACK, 0.85)
    mark(core, "right", 4, 14, 12, 15, DARK)  # the inside of the port
    mark(up_l, "left", 22, 25, 11, 16, shade(BLACK, 0.8))
    g.box(-5, 25, 17, 18, -3, 3, BLACK, 2)  # rail riser
    rail = g.teeth_rail(-5, 25, 18, -3, 3)
    for i, f in enumerate(range(-4, 25, 3)):
        mark(rail[0], "left", f, f + 1, 18, 19, shade(WHITE, 0.8)) if i % 2 == 0 else None  # T-marks
    # dust cover hanging open on its hinge rod
    g.rod(4, 14, 11.5, -4.2, 0.5, STEEL)
    dc = g.box(4, 14, 7.5, 11.5, -4.9, -3.9, BLACK, 2, roll=-12, pivot=(9, 11.5, -4.2))
    g.box(5, 13, 9, 10, -5.4, -4.4, shade(BLACK, 1.15), 1, roll=-12, pivot=(9, 11.5, -4.2))
    mark(dc, "right", 4, 5, 8, 10, DARK)
    # brass deflector behind the port
    g.box(1.5, 3.5, 12, 16.5, -5, -4, BLACK, 2)
    g.box(-1.5, 3, 12, 14, -5, -4, BLACK, 2, tilt=-38, pivot=(3, 14))
    # forward assist
    g.box(-5, 1, 12.5, 15, -4.5, -3.5, BLACK, 2)
    g.rod(-5, 1, 14.3, -4.3, 1.8, BLACK)
    g.rod(1, 2.5, 14.3, -4.3, 1.2, BLACK)
    g.rod(-7.5, -5, 14.3, -4.3, 1.4, STEEL)
    g.rod(-8, -7.5, 14.3, -4.3, 1.6, shade(STEEL, 0.8))
    # bolt carrier seen through the port (moves with the bolt)
    g.part("bolt", 9, 13)
    car = g.box(4.5, 13.5, 12.5, 14.5, -3.6, -2.6, STEEL, 2, bone="bolt")
    mark(car, "right", 10.5, 13.5, 12.5, 14.5, shade(STEEL, 1.25))  # the bolt head
    mark(car, "right", 11, 12, 13, 14, DARK)  # extractor
    mark(car, "right", 6, 9, 13, 14, shade(STEEL, 0.7))  # cam-pin slot
    # charging handle, latch on the left
    g.part("charging_handle", -10, 16)
    g.use("charging_handle")
    g.box(-5, -3, 17, 18.5, -1.5, 1.5, BLACK, 2)
    ch = g.box(-7.5, -5, 17, 18.5, -4, 4, BLACK, 2)
    edge(g, -7.5, -5, 17.5, 3.6, BLACK, 1.0)
    g.box(-7.5, -6, 16.8, 18.8, 4, 5.5, shade(BLACK, 1.15), 1)  # latch
    g.use("frame")
    # ------------------------------------------------ buffer tube, end plate and castle nut
    for c in g.rod(-30, -10, B, 0, 2.6, BLACK):
        for f in (-27, -24.5, -22, -19.5, -17, -14.5):
            mark(c, "down", f, f + 1, 0, 0, DARK, c.ext[4], c.ext[5])
    g.box(-30, -11, 10.4, 11.4, -0.5, 0.5, BLACK, 1)  # the key rail under it
    for c in g.rod(-11.5, -9, B, 0, 3.2, BLACK):
        for side in ("right", "left", "up", "down"):
            mark(c, side, -10.5, -9.5, c.ext[2], c.ext[2] + 1, DARK)
    plate = g.box(-9, -8, 8.5, 16.5, -3.6, 3.6, STEEL, 2)
    qd_cup(g, -8.5, 9.8, 3.6, "left", STEEL)
    stud(g, -9.5, 10.3, 3.3, "left", DARK, 0.8)  # staking
    # ------------------------------------------------ M-LOK free-float handguard
    HF0, HF1 = 25, 58
    g.box(HF0, HF0 + 1, 9, 18, -4.5, 4.5, shade(BLACK, 0.8))  # rear ring against the upper
    cuts = [(28, 33), (35, 40), (42, 47), (49, 54)]
    low = [(31, 34), (38, 41), (45, 48)]
    slotted(g, HF0 + 1, HF1, 9, 18, -5, 5, BLACK, [(10, 11, low), (13, 15, cuts)])
    top = g.box(HF0 + 1, HF1, 18, 19, -4, 4, BLACK)
    bot = g.box(HF0 + 1, HF1, 8, 9, -4, 4, BLACK)
    for u, s in ((18, 4), (18, -4), (9, 4), (9, -4)):
        edge(g, HF0 + 1, HF1, u, s, BLACK, 1.25 if u > 13 else 0.8)
    for a, b in cuts:  # the slots under it and on the chamfers
        mark(bot, "down", a, b, 0, 0, DARK, -1, 1)
    g.teeth_rail(HF0 + 1, HF1, 19, -3, 3)
    for f in (29.5, 55.5):
        qd_cup(g, f, 10.6, 5, "left")
        qd_cup(g, f, 10.6, -5, "right")
    for f in (27.5,):
        stud(g, f, 10.5, 5, "left", size=1)
        stud(g, f, 10.5, -5, "right", size=1)
    g.rod(50, HF1 + 0.5, B, 0, 2.3, STEEL)  # the barrel inside, seen from the front
    # ------------------------------------------------ front sight base (gas block), barrel
    g.rod(58, 62, B, 0, 2.9, BLACK)
    g.box(58, 62, 10.2, 12.5, -2, 2, BLACK, 2)
    for s0, s1 in ((1, 2), (-2, -1)):  # the A-frame ears
        g.box(58, 60, 15.5, 27, s0, s1, BLACK, 2)
        g.box(60, 62, 14, 26, s0, s1, BLACK, 2, tilt=12, pivot=(62, 14))
    g.box(58, 61, 15.5, 17, -2, 2, BLACK, 2)
    g.box(58.5, 59.5, 17, 26, -0.5, 0.5, DARK, 1)  # post
    fsb_top = g.box(58, 60, 15.5, 16.5, -1, 1, SILVER, 1)
    mark(fsb_top, "up", 58, 59, 0, 0, WHITE, -0.5, 0.5)  # "F"
    g.box(60, 63, 9, 10.5, -0.5, 0.5, BLACK, 1)  # bayonet lug
    g.box(61.5, 63, 8.5, 10.5, -1, 1, BLACK, 1)
    sling_swivel(g, 59.5, 10.2, 0, down=True, color=STEEL)
    for f in (58.8, 61.2):
        pins(g, f, 12, 2.9, size=0.8)
    g.rod(62, 66, B, 0, 2.2, STEEL)
    g.rod(66, 67, B, 0, 1.7, shade(STEEL, 0.8))  # the M203 cut
    g.rod(67, 77, B, 0, 2.0, STEEL)
    g.muzzle = (84.0, B)
    # ------------------------------------------------ STANAG magazine (PMAG)
    MF0, MTOP, MW = 11, 2, 6
    segs = [(0, 8), (0, 6), (1, 6), (2, 6)]
    mag_bones(g, MF0 + 5, MTOP)
    u = MTOP
    body = []
    for i, (df, h) in enumerate(segs):
        c = g.box(MF0 + df, MF0 + df + 10, u - h, u, -MW / 2, MW / 2, TAN)
        body.append((c, df, u - h, u))
        u -= h
    g.bevel(MF0 + segs[-1][0] - 1, MF0 + segs[-1][0] + 11, u - 2, u, -MW / 2 - 1, MW / 2 + 1, shade(TAN, 0.75), 0.6)
    g.box(MF0 + segs[-1][0] + 2, MF0 + segs[-1][0] + 8, u - 2.5, u - 1.5, -2, 2, shade(TAN, 0.65), 1)
    g.box(MF0 - 0.5, MF0 + 10.5, -2, -1, -3.5, 3.5, shade(TAN, 0.9), 2)  # over-insertion stop
    for c, df, u0, u1 in body:  # the raised spines front and back
        for s0 in (2.5, -3.5):
            g.box(MF0 + df, MF0 + df + 1, u0, u1, s0, s0 + 1, shade(TAN, 0.95), 1)
            g.box(MF0 + df + 9, MF0 + df + 10, u0, u1, s0, s0 + 1, shade(TAN, 0.95), 1)
        if u1 <= -8:  # grip ridges low on the body
            lines(c, "left", MF0 + df + 1, MF0 + df + 9, u0 + 1, u1, 2, shade(TAN, 0.78))
            lines(c, "right", MF0 + df + 1, MF0 + df + 9, u0 + 1, u1, 2, shade(TAN, 0.78))
    mark(body[1][0], "left", MF0 + 3, MF0 + 7, -11, -9, shade(TAN, 1.35))  # dot-matrix panel
    mag_lips(g, MF0 + 1, MF0 + 9, MTOP, MW, TAN, round_len=7)
    g.mag_profile = dict(f0=MF0, top=MTOP, width=MW, segs=segs, color=TAN, kind="rifle")
    # ------------------------------------------------ mounts and factory parts
    g.use("frame")
    g.mount("optic", 8, 21, length=33)
    g.use("def_optic")  # folding rear sight, up
    g.box(-4, 2, 21, 22, -3.5, 3.5, BLACK, 2)
    for s0, s1 in ((3, 4), (-4, -3)):
        g.box(-4, 2, 19, 21, s0, s1, BLACK, 2)
    disc(g, -1, 20, 4, 5, 1.1, SILVER)
    g.box(-3, 1, 22, 25, -2.5, 2.5, BLACK, 2)
    g.box(-2.5, 0.5, 25, 27, -1, 1, BLACK, 2)
    for s0, s1 in ((1.5, 2.5), (-2.5, -1.5)):
        g.box(-3, 1, 25, 28.5, s0, s1, BLACK, 2)
    ap = g.box(-2, 0, 27, 28, -1, 1, BLACK, 1)
    end_dot(ap, DARK)
    disc(g, -1, 23.5, -3.5, -2.5, 1.2, BLACK)
    g.mount("muzzle", 76, B, bore=2)
    g.use("def_muzzle")  # A2 birdcage
    g.rod(76, 77, B, 0, 2.3, STEEL)
    g.rod(77, 79, B, 0, 2.6, BLACK)
    for ang in (0, 50, -50, 100, -100):
        g.box(79, 83, B + 1.6, B + 2.6, -0.5, 0.5, BLACK, 1, roll=ang, pivot=(0, B, 0))
    g.box(79, 83, B - 2.6, B - 1.4, -1.2, 1.2, BLACK, 1)
    for ang in (28, -28):
        g.box(79, 83, B - 2.6, B - 1.6, -0.8, 0.8, BLACK, 1, roll=ang, pivot=(0, B, 0))
    g.rod(77.5, 83.5, B, 0, 1.3, DARK)
    g.rod(83, 84, B, 0, 2.6, BLACK)
    bore(g, 84, B, 1.2)
    g.mount("underbarrel", 42, 8, length=24, default=False)
    g.mount("side", 50, B, 5, length=10, default=False)
    g.mount("stock", -28, B)
    g.use("def_stock")  # 6-position carbine stock
    g.rod(-46, -28.5, B, 0, 3.4, BLACK)
    g.box(-46, -30, 15.5, 17.5, -2.5, 2.5, BLACK, 2)
    up = g.box(-47, -41, 3, 17, -3.5, 3.5, BLACK)
    g.box(-47, -40, 0, 1.5, -3.5, 3.5, BLACK)  # sling slot below
    g.box(-47, -46, 0, 3, -3.5, 3.5, BLACK)
    g.box(-42, -41, 0, 3, -3.5, 3.5, BLACK)
    g.box(-46, -42, 1, 3, -2.5, 2.5, DARK, 1)
    web = g.box(-42, -24, 1, 8, -3, 3, BLACK, tilt=38, pivot=(-42, 1))
    for c in (up,):
        mark(c, "left", -46, -42, 6, 14, shade(BLACK, 0.75))
        mark(c, "right", -46, -42, 6, 14, shade(BLACK, 0.75))
    for side in ("left", "right"):
        mark(web, side, -38, -28, 3, 6, shade(BLACK, 0.75))
    pad = g.bevel(-49, -47, -0.5, 17.5, -3.8, 3.8, RUBBER, 0.8)
    for c in pad[:2]:
        lines(c, "left", -49, -47, 0, 17, 2, shade(RUBBER, 1.5))
        lines(c, "right", -49, -47, 0, 17, 2, shade(RUBBER, 1.5))
    g.box(-36, -29.5, 9.2, 10.2, -1, 1, shade(BLACK, 1.2), 1)  # adjustment lever
    g.box(-37, -35, 8.5, 10, -1.5, 1.5, shade(BLACK, 1.2), 1)
    pins(g, -30.5, 9.8, 1.1, size=0.8)
    g.use("frame")
    return g


# =========================================================================== AKM / AK-47

def ak47():
    """AKM: stamped receiver with rivets and the magazine-well dimple, ribbed dust cover, tangent rear sight,
    laminated handguards, 90-degree gas block, hooded front post, slant brake, cleaning rod, wooden stock with a
    trapdoor butt plate and a 30-round Bakelite magazine."""
    g = gun("ak47", "rifle", "ar")
    B = 12.0  # bore line
    RCV = BLUED
    # ------------------------------------------------ stamped receiver: core and side plates with the dimple
    g.box(-10, 30, 4, 16, -3, 3, RCV)
    for s0, s1, side in ((3, 4, "left"), (-4, -3, "right")):
        top = g.box(-10, 30, 9, 15, s0, s1, RCV)
        g.box(-10, 13, 4, 9, s0, s1, RCV)
        g.box(18, 30, 4, 9, s0, s1, RCV)
        g.box(13, 18, 4, 6, s0, s1, RCV)
        dim = g.box(13, 18, 6, 9, s0 - 0.5 if side == "left" else s0 + 0.5, s1 - 0.5 if side == "left" else s1 + 0.5,
                    shade(RCV, 0.8), 2)
        mark(dim, side, 13, 18, 8, 9, shade(RCV, 0.65))
        if side == "left":
            roll_mark(top, side, 0, 8, 10.5, shade(RCV, 1.5))  # arsenal mark and serial
        else:
            mark(top, side, 0, 1, 12, 13, WHITE)  # "AB" (auto) and "OD" (semi) under the lever
            mark(top, side, 0, 1, 9.5, 10.5, WHITE)
    g.box(-10, 30, 15, 16, -3.6, 3.6, shade(RCV, 1.1), 2)  # the rolled top edges the cover rides on
    g.box(26, 30, 3, 4, -3.5, 3.5, RCV, 2)  # front trunnion foot
    for f, u in ((24, 5.5), (27, 5.5), (25.5, 7.5), (21.5, 5.5), (9, 5.5), (9, 8), (-8, 6.5), (-8, 11), (11.5, 11)):
        pins(g, f, u, 4, shade(RCV, 1.7), 1.0)  # rivets
    for f, u in ((-3, 8.5), (1.5, 7.5)):  # axis pins
        stud(g, f, u, 4, "left", shade(SILVER, 0.7), 1.0)
        stud(g, f, u, -4, "right", shade(SILVER, 0.7), 0.8)
    stud(g, -6, 12.5, 4, "left", shade(RCV, 1.4), 1.0)
    # trigger guard with the magazine release at its front, trigger
    g.box(-2, 10.5, -1, 0, -1, 1, RCV, 2)
    g.box(-3, -1, -0.5, 4, -1, 1, RCV, 2, tilt=-18, pivot=(-2, 4))
    g.box(9.5, 11, -1, 4, -1, 1, RCV, 2)
    g.box(10.5, 12.5, -1.5, 3, -1.8, 1.8, shade(RCV, 1.15), 1)  # release paddle
    g.box(11.8, 12.8, 2, 4, -1, 1, shade(RCV, 1.1), 1)
    pins(g, 10.2, 2.5, 1, size=0.8)
    g.box(1, 2, 1.5, 4, -0.5, 0.5, RCV, 1)
    g.box(1, 2, -0.2, 1.8, -0.5, 0.5, RCV, 1, tilt=20, pivot=(1.5, 1.8))
    # long safety lever on the right, at SAFE
    disc(g, 1.5, 10.5, -4.6, -4, 1.6, shade(RCV, 1.15))
    g.box(1, 5, 10.5, 13, -4.6, -4, shade(RCV, 1.15), 1, tilt=28, pivot=(1.5, 10.5))
    g.box(4, 20, 13, 14.5, -4.6, -4, shade(RCV, 1.15), 1)
    g.box(19, 20, 13.5, 14.5, -5, -4, shade(RCV, 1.15), 1)
    g.box(-1, 2.5, 7.5, 9.5, -5.2, -4.2, shade(RCV, 1.2), 1, tilt=-20, pivot=(1.5, 10))  # finger tab
    # pistol grip (Bakelite) with its grip screw
    grip = g.pistol_grip(-10, -2.5, 4, 14, 5.5, BAKELITE, angle=18, stipple=False)
    lines(grip, "left", -10, -2.5, -10, 4, 2, shade(BAKELITE, 0.82))
    lines(grip, "right", -10, -2.5, -10, 4, 2, shade(BAKELITE, 0.82))
    g.box(-11.5, -9.5, 0, 4, -2, 2, BAKELITE, 2, tilt=-18, pivot=(-6, 4))  # palm swell at the top rear
    # ------------------------------------------------ ribbed dust cover
    g.bevel(-10, 28, 16, 20, -3.5, 3.5, RCV, 1.5)
    for f in (-3, 0, 3, 6, 9, 12, 15, 18, 21):
        g.box(f, f + 1, 19, 20, -2, 2, shade(RCV, 1.12), 1, inflate=0.22)
    g.box(-11, -10, 16.5, 18.5, -1, 1, SILVER, 1)  # recoil spring guide button
    g.box(-10.5, -10, 15.5, 19, -2.5, 2.5, RCV, 2)
    # ------------------------------------------------ bolt carrier with its charging handle
    g.part("charging_handle", 22, 13, -5)
    g.use("charging_handle")
    car = g.box(4, 20.5, 13.2, 15.5, -3.6, -2.6, CHROME, 2)
    mark(car, "right", 16.5, 20.5, 13.2, 15.5, shade(STEEL, 1.4))  # the bolt head
    mark(car, "right", 17.5, 19, 14, 14.8, DARK)  # extractor
    mark(car, "right", 8, 13, 15, 15.5, shade(CHROME, 0.7))
    g.box(20.5, 23, 13.2, 14.6, -6.5, -3.5, CHROME, 1)
    disc(g, 22, 13.9, -9.2, -6.5, 1.5, CHROME)
    g.use("frame")
    # ------------------------------------------------ rear sight block and tangent leaf
    rs = g.box(28, 37, 14, 19, -3, 3, RCV)
    g.box(30, 37, 19, 20, -2.5, 2.5, RCV, 2)  # the ramp the slider rides
    leaf = g.box(28.5, 37, 20, 21, -1.5, 1.5, GUNMETAL, 1, tilt=-3, pivot=(37, 20.5))
    for i, f in enumerate(range(30, 36)):
        mark(leaf, "up", f, f + 0.6, 0, 0, WHITE if i % 2 else shade(WHITE, 0.6), -0.5, 0.5)
    g.box(28.5, 30, 21, 22, -1.5, 1.5, GUNMETAL, 1)  # the notch block
    g.box(29, 30, 21.5, 22, -0.5, 0.5, DARK, 0)
    g.box(32, 34.5, 19.5, 22, -2.2, 2.2, GUNMETAL, 1)  # slider
    for s0 in (2.2, -3.2):
        g.box(32.5, 34, 20, 21.5, s0, s0 + 1, SILVER, 1)
    disc(g, 36, 16.5, -4, -3, 1.0, RCV)  # gas tube lock lever
    g.box(36, 38.5, 16.5, 17.5, -4.2, -3.2, RCV, 1, tilt=15, pivot=(36, 17))
    mark(rs, "left", 30, 36, 15, 17, shade(RCV, 0.75))  # the leaf spring
    # ------------------------------------------------ handguards (laminated birch), gas tube, gas block
    g.box(30, 34, 6.5, 14, -4.3, 4.3, RCV)  # rear handguard ferrule
    lam = shade(WOOD, 0.86)
    low = g.bevel(34, 56, 6.5, 14.5, -4.6, 4.6, WOOD, 1.5)
    swell = g.bevel(50.5, 56.5, 6, 14.5, -5.2, 5.2, WOOD, 1.8)
    for c in low[:2] + swell[:2]:
        for side in ("right", "left"):
            lines(c, side, c.ext[0], c.ext[1], c.ext[2] + 1, c.ext[3], 2, lam)
    for side in ("right", "left"):
        mark(low[0], side, 38, 49, 10, 11, WOOD_D)  # the finger groove
    g.bevel(56.5, 58.5, 6, 15.5, -5.4, 5.4, RCV, 1.5)  # front retainer band
    g.box(55, 58.5, 9.5, 10.5, -6, -5.4, RCV, 1)  # its lever
    g.rod(36, 37.5, 18, 0, 2.3, RCV)  # gas tube rear cap
    uhg = g.bevel(37.5, 54, 15, 20.8, -3.3, 3.3, WOOD, 1.3)
    for c in uhg[:2]:
        for side in ("right", "left"):
            lines(c, side, 37.5, 54, 16, 20.8, 2, lam)
            mark(c, side, 41, 45, 16.5, 18.5, WOOD_D)
            mark(c, side, 47, 51, 16.5, 18.5, WOOD_D)
    for c in g.rod(54, 60, 18, 0, 1.8, RCV):
        for f in (55, 56.6, 58.2):
            for side in ("right", "left"):
                mark(c, side, f, f + 1, 17.5, 18.5, DARK)  # vents
    g.rod(59, 64, B, 0, 2.8, RCV)  # gas block round the barrel
    g.rod(58.5, 63, 18, 0, 2.3, RCV)  # and round the gas chamber
    g.box(59, 63, B, 18, -1.8, 1.8, RCV)
    g.rod(63, 64.5, 18, 0, 1.5, shade(RCV, 1.1))
    g.box(60, 63, 14, 15, 1.8, 3.6, STEEL, 1)  # front sling loop (left)
    g.box(60, 61, 11.5, 15, 3, 4, STEEL, 1)
    g.box(62, 63, 11.5, 15, 3, 4, STEEL, 1)
    g.box(60, 63, 11.5, 12.5, 3, 4, STEEL, 1)
    # ------------------------------------------------ barrel, front sight, cleaning rod
    g.rod(36, 59, B, 0, 2, RCV)
    g.rod(64, 82, B, 0, 2, RCV)
    g.rod(72, 77, B, 0, 2.8, RCV)
    g.box(72, 77, 7.5, 10.5, -1.8, 1.8, RCV, 2)  # the base under the barrel
    g.box(73, 76, 6, 7.5, -0.8, 0.8, RCV, 2)  # bayonet lug
    g.box(72.5, 76, 14, 17.5, -2, 2, RCV, 2)  # tower
    for ang in (60, 100, 140, 180, -60, -100, -140):  # the hood, open at the top
        g.box(72.5, 75.5, 20 + 2.4, 20 + 3.4, -0.9, 0.9, RCV, 1, roll=ang, pivot=(0, 20, 0))
    g.box(73.5, 74.5, 17, 21.5, -0.5, 0.5, DARK, 1)  # post
    disc(g, 74, 17.6, -1.8, 1.8, 1.0, shade(RCV, 1.2))  # windage drum
    stud(g, 76.5, 11, -2.8, "right", SILVER, 0.8)  # brake detent
    g.rod(34, 76, 8, 0, 0.6, STEEL)  # cleaning rod
    g.box(75.5, 77, 7.3, 8.8, -0.9, 0.9, STEEL, 1)
    g.muzzle = (88.0, B)
    # ------------------------------------------------ magazine (Bakelite, steel lips and spine)
    MF0, MTOP, MW = 13, 3, 6
    segs = [(0, 7), (2, 6), (5, 6), (9, 6), (14, 5)]
    mag_bones(g, MF0 + 4, MTOP)
    body = curve_mag(g, MF0, MTOP, MW, segs, BAKELITE, last_turn=1.1)
    for seg in body:
        c, df, u, h, ang, piv = seg
        f = MF0 + df
        for s0 in (2.6, -3.6):  # two stiffening ribs a side, along the curve
            on_seg(g, seg, f + 2.5, f + 3.5, u - h - 0.6, u, s0, s0 + 1, shade(BAKELITE, 1.12), 1)
            on_seg(g, seg, f + 6.5, f + 7.5, u - h - 0.6, u, s0, s0 + 1, shade(BAKELITE, 1.12), 1)
        on_seg(g, seg, f - 0.4, f + 0.6, u - h - 0.6, u, -2, 2, shade(BAKELITE, 0.85), 1)  # rear spine
        on_seg(g, seg, f + 9.4, f + 10.4, u - h - 0.6, u, -2.5, 2.5, shade(BAKELITE, 0.92), 1)  # front edge
    c, df, u, h, ang, piv = body[-1]
    f = MF0 + df
    plate = on_seg(g, body[-1], f - 1, f + 11, u - h - 2.4, u - h - 0.4, -MW / 2 - 0.8, MW / 2 + 0.8, RCV, 2)
    on_seg(g, body[-1], f + 1, f + 3, u - h - 2.9, u - h - 1.9, -1, 1, shade(RCV, 1.2), 1)  # its catch
    on_seg(g, body[0], MF0 + 8, MF0 + 11, MTOP, MTOP + 1.5, -1.5, 1.5, RCV, 1)  # front locking lug
    on_seg(g, body[0], MF0 - 1, MF0 + 1, MTOP - 2, MTOP, -1.5, 1.5, RCV, 1)  # rear lug
    mag_lips(g, MF0 + 1.5, MF0 + 8.5, MTOP, MW, RCV, round_len=7, r=1.3)
    g.mag_profile = dict(f0=MF0, top=MTOP, width=MW, segs=segs, color=BAKELITE, kind="ak")
    # ------------------------------------------------ mounts and factory parts
    g.use("frame")
    g.mount("optic", 10, 20, length=16, default=False)
    g.mount("muzzle", 82, B, bore=2)
    g.use("def_muzzle")  # slant compensator
    g.rod(82, 85.5, B, 0, 2.4, RCV)
    g.box(85.5, 88, B - 2.4, B, -2.2, 2.2, RCV, 2)
    g.box(85, 88, B - 1, B + 2, -2, 2, RCV, 2, tilt=-50, pivot=(85.5, B + 2.4))
    bore(g, 88, B, 1.1)
    g.mount("underbarrel", 48, 6, length=12, default=False)
    g.mount("side", 48, 10, 5, length=10, default=False)
    g.mount("stock", -10, 10)
    g.use("def_stock")  # laminated stock, steel butt plate with the trapdoor
    g.box(-12, -10, 4, 15.5, -3.2, 3.2, RCV, 2)  # the receiver tang
    wrist = g.bevel(-20, -10, 4.5, 14, -3.1, 3.1, WOOD, 1)
    upper = g.box(-47, -17, 6, 14, -3.8, 3.8, WOOD, tilt=6, pivot=(-17, 14))
    lower = g.box(-47, -17, -4.5, 3.5, -3.7, 3.7, WOOD, tilt=15, pivot=(-47, 3.5))
    soften(upper, ("bottom",))
    for c in (upper, lower) + tuple(wrist[:2]):
        for side in ("right", "left"):
            lines(c, side, c.ext[0], c.ext[1], c.ext[2] + 1, c.ext[3], 2, lam)
    g.box(-16, -11, 13.5, 14.5, -1.5, 1.5, RCV, 1)  # top tang strap
    plate = g.box(-49, -47, -5, 12, -4, 4, RCV, 2, tilt=9, pivot=(-48, 3))
    g.box(-49.6, -48.6, -1, 7, -2.2, 2.2, shade(RCV, 1.15), 1, tilt=9, pivot=(-48, 3))  # trapdoor
    g.box(-49.4, -48.4, 7, 8.5, -0.8, 0.8, SILVER, 1, tilt=9, pivot=(-48, 3))  # its latch
    g.box(-46, -44, 11.5, 12.5, -4.1, 4.1, RCV, 1, tilt=9, pivot=(-48, 3))  # plate tangs over the wood
    g.box(-46, -44, -3, -2, -4.1, 4.1, RCV, 1, tilt=9, pivot=(-48, 3))
    g.box(-24, -20, 12.5, 13.5, 3.8, 4.8, STEEL, 1)  # rear sling loop (left)
    g.box(-24, -23, 9.5, 13.5, 3.8, 4.8, STEEL, 1)
    g.box(-21, -20, 9.5, 13.5, 3.8, 4.8, STEEL, 1)
    g.use("frame")
    return g



# =========================================================================== M249 SAW

def m249():
    """FN M249 SAW: stamped receiver with its rivet rows, top cover with the feed tray under it and a rail on
    top, heat shield and carry handle on the barrel, gas regulator, folding bipod, hooded front post, slotted
    flash hider, ribbed stock with the buffer, and the 200-round pouch feeding a belt of linked rounds."""
    g = gun("m249", "rifle", "lmg")
    B = 14.5  # bore line
    RC = PARK
    # ------------------------------------------------ receiver
    rec = g.bevel(-12, 34, 4, 22, -6, 6, RC, 1.2)
    for c in rec[:2]:
        mark(c, "left", 6, 16, 18, 21, DARK)  # the feed opening the belt runs into
        mark(c, "right", 4, 15, 5, 8.5, DARK)  # ejection port
        mark(c, "right", 6, 13, 18.5, 20.5, DARK)  # link port
        mark(c, "right", -2, 30, 12.5, 13.5, shade(RC, 0.6))  # charging slot
        roll_mark(c, "left", -6, 2, 8.5, shade(RC, 1.5))
    for side_s, side in ((6, "left"), (-6, "right")):
        for f in range(-9, 34, 5):  # rivet rows along the top and bottom of the stamped box
            stud(g, f, 5.6, side_s, side, shade(RC, 1.5), 0.9)
            stud(g, f, 20.4, side_s, side, shade(RC, 1.5), 0.9)
        rib = (6, 6.6) if side_s > 0 else (-6.6, -6)
        g.box(-11, 33, 11, 12, rib[0] - 0.4, rib[1] - 0.4, shade(RC, 1.12), 1)  # the carrier guide rails
    g.box(-11, 33, 21.5, 22.5, -5, 5, shade(RC, 0.9), 2)  # cover seat
    g.box(32, 36, 8.5, 21, -5, 5, shade(RC, 0.85))  # front trunnion round the barrel socket
    disc(g, 34, 18, 5, 6.2, 1.5, STEEL)  # barrel latch (left)
    g.box(33, 35, 15, 17, 5.5, 6.5, STEEL, 1)
    # the magazine well on the left, its dust cover shut while the belt feeds
    mw = g.bevel(7, 19, 3, 12, 6, 8.5, RC, 0.8)
    mark(mw[0], "left", 8, 18, 4, 11, shade(RC, 0.8))
    g.box(9, 17, 11.5, 12.5, 8, 9, STEEL, 1)
    # the dust cover over the ejection port, hanging open
    g.box(4, 15, 2, 5, -7, -6, RC, 2, roll=-15, pivot=(9.5, 5, -6.3))
    # trigger housing, guard, trigger and pistol grip
    th = g.box(-15, 1, 1.5, 4.5, -2.8, 2.8, BLACK)
    pins(g, -13, 3, 2.8, size=0.8)
    pins(g, -1, 3, 2.8, size=0.8)
    g.box(-4.5, 1, -2.5, -1.5, -1, 1, BLACK, 2)
    g.box(0, 1, -2.5, 1.5, -1, 1, BLACK, 2)
    g.box(-2, -1, 0, 1.5, -0.5, 0.5, STEEL, 1)
    g.box(-2, -1, -1.5, 0.5, -0.5, 0.5, STEEL, 1, tilt=20, pivot=(-1.5, 0.5))
    g.pistol_grip(-12, -4, 5, 16, 6, POLY, angle=14)
    g.box(-13.5, -11.5, 0, 4, -2.5, 2.5, POLY, 2, tilt=-14, pivot=(-8, 5))
    # ------------------------------------------------ charging handle (right, folded forward)
    g.part("charging_handle", 20, 13, -7)
    g.use("charging_handle")
    g.box(22, 26, 11.5, 15, -7, -6, BLACK, 2)
    g.box(24, 31, 12, 14.5, -8.2, -7, BLACK, 2)
    disc(g, 30.5, 13.2, -8.8, -7, 1.3, BLACK)
    g.use("frame")
    # ------------------------------------------------ feed tray (seen when the cover opens)
    tray = g.box(2, 18, 21, 22, -5.5, 5.5, STEEL, 1)
    for f in (4, 8, 12, 16):
        mark(tray, "up", f, f + 1, 0, 0, shade(STEEL, 0.65), -5, 5)
    g.box(2, 3.5, 22, 23, -5.5, 5.5, SILVER, 1)  # cartridge stop
    g.box(15, 18, 22, 22.8, -1, 1, SILVER, 1)  # cartridge guide
    # ------------------------------------------------ top cover with its rail and rear sight (opens on reload)
    g.part("cover", -12, 23)
    g.use("cover")
    cov = g.bevel(-12, 24, 22, 26, -5.5, 5.5, RC, 1)
    for c in cov[:2]:
        mark(c, "left", 6, 16, 22, 23, DARK)
    g.box(-12, 24, 25.5, 26.5, -4, 4, RC, 2)
    g.teeth_rail(-4, 22, 26.5, -3, 3)
    for s0 in (5.5, -6.5):  # the latches at the back
        g.box(-11.5, -9, 22.5, 25, s0, s0 + 1, SILVER, 1)
    g.box(-12, -4, 26.5, 28, -3, 3, RC, 2)  # rear sight base
    g.box(-10, -6, 28, 31, -2, 2, BLACK, 2)
    for s0 in (1, -2):
        g.box(-10, -6, 31, 32.5, s0, s0 + 1, BLACK, 1)
    ap = g.box(-9, -7, 30.5, 32, -0.8, 0.8, BLACK, 1)
    end_dot(ap, DARK)
    disc(g, -8, 29.2, -3, -2, 1.2, BLACK)  # elevation knob
    disc(g, -8, 29.2, 2, 3, 1.0, BLACK)  # windage knob
    g.box(18, 24, 24.5, 26.2, -5.6, -4.6, RC, 1)  # feed lever housing
    g.use("frame")
    # ------------------------------------------------ barrel, heat shield, handguard, gas system
    g.rod(34, 102, B, 0, 2.6, STEEL)
    g.ring(36, 38, B, 0, 3.2, shade(STEEL, 0.8))
    vents = [(37.5, 39.5), (41.5, 43.5), (45.5, 47.5), (49.5, 51.5)]
    slotted(g, 36, 55, 17, 23, -3.8, 3.8, RC, [(18.5, 21, vents)])
    g.box(36, 55, 23, 23.6, -3, 3, RC, 2)
    for f in (40, 48):
        pins(g, f, 18, 3.8, size=0.8)
    hgd = g.bevel(36, 54, 3, 11.5, -4.8, 4.8, POLY, 1.5)  # lower handguard over the gas tube
    for c in hgd[:2]:
        for side in ("right", "left"):
            lines(c, side, 38, 52, 5, 10, 2, shade(POLY, 0.7))
    g.rod(54, 74, 8, 0, 2, GUNMETAL)  # gas cylinder
    g.box(72, 77, 6, 16, -2.6, 2.6, BLACK)  # gas block
    g.rod(72, 77, B, 0, 3.2, BLACK)
    g.rod(77, 80, 8, 0, 1.9, STEEL)  # the regulator plug and its lever
    g.box(77.5, 79, 8, 12, 1, 2.6, SILVER, 1)
    g.box(77, 79.5, 4.5, 6, -1, 1, STEEL, 1)
    # carry handle (left side of the barrel; it is also the barrel-change handle)
    g.box(46, 48, 17, 27, 2.5, 3.5, STEEL, 2)
    g.box(55, 57, 17, 27, 2.5, 3.5, STEEL, 2)
    g.box(45, 58, 16.5, 18, 2.5, 4, STEEL, 2)
    ch = g.bevel(44, 59, 26.5, 29.5, 0.5, 4.5, POLY, 0.6)
    for c in ch[:2]:
        lines(c, "left", 45, 58, 27, 29, 2, shade(POLY, 1.35), vertical=True)
    # front sight
    g.rod(93, 98, B, 0, 3.0, BLACK)
    g.box(93.5, 97.5, 16, 19, -2, 2, BLACK)
    for s0 in (1.2, -2.2):
        g.box(93.5, 97, 19, 25.5, s0, s0 + 1, BLACK, 2)
    g.box(95, 96, 19, 25, -0.5, 0.5, DARK, 1)
    pins(g, 95.5, 11.8, 2.4, size=0.8)
    g.muzzle = (110.0, B)
    # ------------------------------------------------ 200-round pouch with the belt rising into the tray
    mag_bones(g, 14, 4)
    pouch = g.bevel(2, 26, -18, 4, -9, 5, OD, 1.5)
    for c in pouch[:2]:
        for side in ("right", "left"):
            stitch(c, side, 3, 25, -16.5, OD_D)
            stitch(c, side, 3, 25, 2.5, OD_D)
            stitch_v(c, side, 3.5, -16, 2, OD_D)
            stitch_v(c, side, 24, -16, 2, OD_D)
            mark(c, side, 8, 20, -12, -5, shade(OD, 0.9))  # the stitched name-tape panel
            stitch(c, side, 8, 20, -12, OD_D)
            stitch(c, side, 8, 20, -6, OD_D)
    for u0 in (-15, -9):  # webbing straps round the pouch
        g.box(1.5, 26.5, u0, u0 + 2, -9.4, 5.4, OD_D, 2)
    flap = g.box(1.5, 26.5, 4, 5.5, -9.4, 5.4, shade(OD, 1.08), 2)  # the flap over the top
    g.box(25.5, 27, -2, 5.5, -6, 2, shade(OD, 1.08), 2)  # and its tongue down the front
    g.box(26.5, 27.5, -1, 1.5, -3.5, -0.5, BLACK, 1)  # buckle
    g.box(7, 21, 3.5, 5.5, -5, 3, BLACK, 2)  # the hard adapter that clips to the gun
    g.box(11, 17, 5.5, 6.5, -3, 1, BLACK, 1)
    g.box(-1, 2, -14, -4, -2, 0, OD_D, 1)  # carry strap loop at the back
    # the belt: rounds lie along the barrel, stacked up the left side of the receiver into the feed opening
    belt = [(4.8, 3.6), (6.6, 5.4), (8.4, 6.6), (10.2, 7.2), (12.0, 7.4), (13.8, 7.4), (15.6, 7.3), (17.4, 7.0),
            (19.2, 6.2)]
    for u, s in belt:
        cartridge(g, 7.5, u, s, length=9, r=0.85)
        g.box(9.5, 10.5, u - 0.9, u + 0.9, s - 1.1, s + 0.9, STEEL, 1)  # M27 links
        g.box(12.5, 13.5, u - 0.9, u + 0.9, s - 1.1, s + 0.9, STEEL, 1)
    for s in (2.6, -0.4):  # the rounds lying in the feed tray
        cartridge(g, 6.5, 22.9, s, length=9, r=0.85)
    g.mag_profile = dict(f0=2, top=4, width=14, segs=[(0, 22)], color=OD, kind="box")
    # ------------------------------------------------ mounts and factory parts
    g.use("frame")
    g.mount("optic", 9, 29.5, length=26, default=False, parent="cover")
    g.mount("muzzle", 102, B, bore=2.6)
    g.use("def_muzzle")  # slotted flash hider
    g.rod(102, 104, B, 0, 3.0, BLACK)
    for ang in (0, 60, 120, 180, -60, -120):
        g.box(104, 109, B + 1.9, B + 2.9, -0.6, 0.6, BLACK, 1, roll=ang + 30, pivot=(0, B, 0))
    g.rod(103.5, 109.5, B, 0, 1.6, DARK)
    g.rod(109, 110, B, 0, 2.9, BLACK)
    bore(g, 110, B, 1.4)
    g.mount("underbarrel", 80, 6)  # the factory bipod, folded back under the gas cylinder
    g.use("def_underbarrel")
    g.rod(79, 84, 8, 0, 2.4, BLACK)  # yoke round the gas cylinder
    g.box(80, 83, 3.5, 7, -3.5, 3.5, BLACK, 2)
    for ds in (-3, 3):
        disc(g, 81.5, 4.8, ds - 1, ds + 1, 1.2, STEEL)  # leg pivots
        g.rod(66, 82, 4.8, ds, 1.0, SILVER)  # upper leg
        g.rod(57, 66, 4.8, ds, 0.75, CHROME)  # lower leg, telescoped in
        g.box(64.5, 66.5, 3.6, 6, ds - 1.2, ds + 1.2, BLACK, 1)  # extension collar
        g.box(54.5, 57.5, 2.6, 6.6, ds - 1.4, ds + 1.4, RUBBER, 1)  # foot
        g.box(53.5, 54.5, 3.2, 6.0, ds - 1, ds + 1, RUBBER, 1)
    g.mount("side", 44, B, 6, length=10, default=False)
    g.mount("stock", -12, 14)
    g.use("def_stock")  # ribbed polymer stock with the hydraulic buffer
    g.rod(-18, -12, B, 0, 4.2, shade(POLY, 0.85))  # buffer housing
    main = g.bevel(-52, -16, 9, 20.5, -5, 5, POLY, 1.5)
    low = g.box(-52, -16, 3, 11, -4.9, 4.9, POLY, tilt=9, pivot=(-52, 3))
    for c in main[:2]:
        soften(c, ("bottom",))
    for u in (11, 14, 17):  # the ribs along its sides
        g.box(-48, -20, u, u + 1, -5.5, 5.5, shade(POLY, 1.12), 1)
    g.box(-50, -18, 20, 21, -3.5, 3.5, shade(POLY, 1.05), 2)
    pad = g.bevel(-56, -52, 1.5, 21.5, -5.2, 5.2, RUBBER, 1)
    for c in pad[:2]:
        lines(c, "left", -56, -52, 2, 21, 2, shade(RUBBER, 1.5))
        lines(c, "right", -56, -52, 2, 21, 2, shade(RUBBER, 1.5))
    g.box(-57, -55, 18, 23, -3.5, 3.5, STEEL, 1)  # shoulder rest, folded
    disc(g, -55, 19, -4, 4, 1.0, SILVER)
    grip = g.bevel(-47, -40, -1, 4, -1.8, 1.8, POLY, 0.5)  # the under-grip for the other hand
    for c in grip[:2]:
        lines(c, "left", -47, -40, -1, 4, 2, shade(POLY, 1.3))
        lines(c, "right", -47, -40, -1, 4, 2, shade(POLY, 1.3))
    sling_swivel(g, -50, 3.5, 0, down=True, color=STEEL)
    g.use("frame")
    return g


def svd():
    """SVD Dragunov (7.62x54mmR): milled receiver with the left dovetail scope rail, wooden upper handguard over
    the gas tube, slotted lower handguard, tangent rear sight, hooded front sight, long slotted flash hider,
    skeleton thumbhole stock, 10-round curved magazine and the PSO-1 scope on the left of the rail."""
    g = gun("svd", "rifle", "ar")
    B = 12.0
    # ------------------------------------------------ receiver
    rec = g.bevel(-10, 30, 6, 17, -4, 4, BLUED, 1)
    for c in rec[:2]:
        mark(c, "right", 6, 20, 11, 15, DARK)  # ejection port
        mark(c, "right", 2, 26, 8, 9, shade(BLUED, 0.7))  # milling line
        mark(c, "left", 2, 26, 8, 9, shade(BLUED, 0.7))
        roll_mark(c, "left", -6, 4, 9.5, shade(BLUED, 1.6))
    cov = g.bevel(-10, 30, 17, 20, -3, 3, BLUED, 1)  # dust cover
    mark(cov[1], "up", -10, 30, 0, 0, shade(BLUED, 0.7), -0.5, 0.5)
    g.box(-12, -10, 10, 17, -2, 2, GUNMETAL, 2)  # recoil spring cap
    g.box(0, 20, 10, 16, 4, 6, BLUED)  # side scope rail (dovetail)
    for f in range(1, 20, 4):
        g.box(f, f + 1.5, 10.5, 15.5, 5.6, 6.3, shade(BLUED, 1.3), 1)  # clamp serrations
    for f, u in ((-8, 7.5), (26, 7.5), (-8, 15.5), (26, 15.5)):
        pins(g, f, u, 4, size=0.9)
    g.box(2, 22, 12, 14, -4.6, -4, BLUED)  # safety lever
    g.box(4, 14, 13, 16, -4.3, -2, DARK)
    g.box(18, 21, 11, 15, -5.4, -4.4, BLUED, 1)  # safety tab
    g.part("charging_handle", 22, 14, -5)
    g.box(18, 26, 13, 15, -8, -4, GUNMETAL, 1, bone="charging_handle")
    g.box(24, 26, 12, 16, -9, -7, GUNMETAL, 1, bone="charging_handle")
    # magazine well, trigger group, pistol grip
    mw = g.bevel(10, 24, 2, 7, -4, 4, BLUED, 0.8)
    g.box(9, 11, 1, 4, -1.5, 1.5, STEEL, 1)  # magazine catch
    g.box(-6, 10, 3, 6, -2.8, 2.8, BLUED)
    g.trigger(-1, 3)
    g.pistol_grip(-10, -3, 6, 15, 6, WOOD, angle=14)
    g.box(-11, -9, -8, -2, -3.2, 3.2, shade(WOOD, 0.8), 2, tilt=-14, pivot=(-6, 6))
    # ------------------------------------------------ handguards, gas tube, barrel
    g.rod(30, 112, B, 0, 2, BLUED)
    g.rod(58, 96, 16.6, 0, 1.6, BLUED)  # gas tube
    g.rod(94, 100, 16.6, 0, 2.2, GUNMETAL)  # gas piston cap
    low = slotted(g, 34, 60, 6, 15.5, -4.6, 4.6, WOOD,
                  [(8.5, 13, [(37, 40), (43, 46), (49, 52), (55, 58)])], inner=DARK)
    for c in low:
        lines(c, "left", 34, 60, 6, 8.5, 2, shade(WOOD, 0.8))
    uhg = g.bevel(34, 58, 15, 21, -3.6, 3.6, WOOD, 1.2)  # upper handguard over the gas tube
    for c in uhg[:2]:
        for side in ("right", "left"):
            lines(c, side, 34, 58, 16, 21, 2, shade(WOOD, 0.75))
    g.box(58, 62, 6, 21, -4.8, 4.8, BLUED)  # ferrule where the handguard ends
    g.box(58, 62, 9, 19, 4.8, 5.4, shade(BLUED, 1.3), 1)
    pins(g, 60, 8, 4.8, size=0.9)
    # tangent rear sight on the front of the receiver cover
    g.box(26, 36, 19.5, 22, -2.5, 2.5, BLUED)
    g.box(27, 35, 22, 23, -1.2, 1.2, GUNMETAL, 1)
    leaf = g.box(28, 30, 22, 26.5, -1.5, 1.5, BLUED, 1, tilt=-18, pivot=(29, 22))
    g.box(28, 30, 25, 26.4, -0.4, 0.4, DARK, 1, tilt=-18, pivot=(29, 22))  # the notch
    for f in range(30, 36, 2):
        g.box(f, f + 1, 22, 22.6, -1.8, 1.8, shade(BLUED, 1.4), 1)
    # gas block and hooded front sight
    g.box(86, 92, 8, 20, -2.8, 2.8, BLUED)
    g.rod(86, 92, B, 0, 3.0, BLUED)
    g.box(100, 108, 9, 16, -2.6, 2.6, BLUED)
    g.rod(100, 108, B, 0, 3.0, BLUED)
    g.box(101, 107, 16, 19, -2, 2, BLUED)
    for s0 in (-3.2, 2.2):  # wings of the hood
        g.box(100.5, 108, 16, 21.5, s0, s0 + 1, BLUED, 2)
    g.box(103.5, 104.5, 19, 24, -0.5, 0.5, DARK, 1)  # the post
    g.box(103, 105, 23.5, 24.8, -0.8, 0.8, GUNMETAL, 1)
    pins(g, 104, 11, 2.6, size=0.8)
    g.muzzle = (122.0, 12.0)
    # ------------------------------------------------ 10-round magazine
    mag_bones(g, 17, 6)
    segs = [(0, 8), (1, 5), (3, 4)]
    cm = curve_mag(g, 12, 6, 6, segs, BLUED, overlap=0.4)
    for seg in cm:
        _c, df, ut, h, _a, _p = seg
        for u in (ut - h + 1.5, ut - h + 3.5):
            if u + 1 <= ut:
                on_seg(g, seg, 12 + df + 1, 12 + df + 9, u, u + 1, -3.3, 3.3, shade(BLUED, 1.25), 1)
    seg = cm[-1]
    _c, df, ut, h, _a, _p = seg
    on_seg(g, seg, 12 + df - 1, 12 + df + 11, ut - h - 1, ut - h + 1, -3.8, 3.8, STEEL)
    on_seg(g, cm[0], 12 + 8, 12 + 10.4, ut - 8 + 0, 6 - 1, -3.3, 3.3, DARK, 1)  # the front rib of the box
    g.mag_profile = dict(f0=12, top=6, width=6, segs=[(0, 8), (1, 5), (3, 4)], color=BLUED, kind="dmr")
    # ------------------------------------------------ PSO-1 scope
    g.use("frame")
    g.mount("optic", 8, 22, 4, length=12)
    g.use("def_optic")
    g.box(-2, 20, 16, 20, 3.5, 7.5, BLUED)  # base on the side rail
    g.box(-2, 20, 19.5, 23, 3.5, 6.5, BLUED)
    g.box(0, 16, 17, 22.6, 6.5, 8, BLUED, 2)  # clamp lever side
    g.box(14, 17, 17, 21, 7.5, 9.5, GUNMETAL, 1)  # clamp lever
    g.rod(-6, 24, 26, 5, 3, POLY)  # main tube
    g.rod(24, 33, 26, 5, 4.1, POLY)  # objective bell
    g.rod(33, 38, 26, 5, 4.4, shade(POLY, 0.8))  # sun-shade ring
    g.rod(-6, -2, 26, 5, 3.3, shade(POLY, 1.2))
    g.rod(-12, -6, 26, 5, 3.5, RUBBER)  # eyecup
    g.rod(-12.5, -11.5, 26, 5, 2.0, DARK, 0)  # the eyepiece lens
    g.rod(17, 19, 26, 5, 3.4, GUNMETAL)  # focus ring
    lc = g.rod(37.8, 38.6, 26, 5, 3.6, GLASS, 0)
    for c in lc:
        c.front.fill(GLASS)
        c.front.px(0, 0, WHITE)
    g.box(8, 12, 28.5, 30.5, 3.2, 6.8, POLY, 1)  # elevation drum
    knob(g, 10, 5, 29.5, 32, 1.8, GUNMETAL)
    disc(g, 10, 26, 8.5, 10.5, 1.8, GUNMETAL)  # windage drum on the left
    g.box(-2, 3, 28.5, 30, 4, 6, BLACK, 1)  # illumination battery housing / reticle lamp
    g.box(26, 30, 22.5, 24, 3, 7, BLUED, 1)
    # ------------------------------------------------ muzzle
    g.use("frame")
    g.mount("muzzle", 112, B, bore=2)
    g.use("def_muzzle")  # long slotted flash hider
    g.rod(112, 114, B, 0, 2.9, BLUED)
    for c in g.rod(114, 121, B, 0, 2.6, BLUED):
        slots(c, ("right", "left", "up"), 115, 121, c.ext[2], c.ext[3], 3, 1.5)
        slots(c, ("down",), 115, 121, c.ext[2], c.ext[3], 3, 1.5)
    g.rod(121, 122, B, 0, 2.8, BLUED)
    bore(g, 122, B, 1.4)
    g.use("frame")
    g.mount("underbarrel", 48, 6, length=10, default=False)
    # ------------------------------------------------ skeleton thumbhole stock
    g.mount("stock", -10, 10)
    g.use("def_stock")
    top = g.bevel(-58, -10, 12, 19, -3.4, 3.4, WOOD, 1.2)
    for c in top[:2]:
        lines(c, "left", -58, -10, 13, 18, 2, shade(WOOD, 0.8))
        lines(c, "right", -58, -10, 13, 18, 2, shade(WOOD, 0.8))
    g.box(-52, -28, 19, 21.5, -3, 3, WOOD, 2)  # cheek rest
    low = g.box(-58, -8, -3, 2, -3.2, 3.2, WOOD)  # lower strut to the grip
    g.box(-22, -14, 2, 12, -3.4, 3.4, WOOD, 2)  # the thumbhole post
    for f in (-52, -36):
        g.box(f, f + 3, 2, 12, -3.4, 3.4, WOOD, 2)
    butt = g.bevel(-62, -58, -6, 19, -4, 4, WOOD, 1.2)
    g.box(-65, -62, -7, 20, -4.2, 4.2, BLUED)  # steel butt plate
    for u in (-4, 1, 6, 11, 16):
        g.box(-65.5, -65, u, u + 1, -3, 3, shade(BLUED, 1.35), 1)
    sling_swivel(g, -52, -3, 0, down=True)
    g.use("frame")
    return g
