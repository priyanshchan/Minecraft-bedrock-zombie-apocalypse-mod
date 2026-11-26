"""Shotgun, sniper rifle and launchers: Remington 870, AWM, Carl Gustaf M4, RPG-7."""
from __future__ import annotations

import math
import random

from gunbase import *  # noqa: F401,F403
from gunbase import curved_mag, gun, mag_bones
from kit import FACES, LOW

SHELL_RED = "#b02a28"
ANOD = "#2b2d31"       # black anodised aluminium
PAD = "#26272a"        # recoil pad rubber
IVORY = "#e6dcc2"


# =========================================================================== detail helpers (this file only)

def hi():
    """Full detail (the player's guns); soldiers carry a light build (kit.LOW) without the small parts."""
    return not LOW[0]


def _shade_face(face, fn):
    for x in range(face.w):
        for y in range(face.h):
            face.px(x, y, shade(face.get(x, y), fn(x, y, face.w, face.h)))


def _seg_light(c, color, ang, noise, seed, inner):
    """Light the outer face of a wall segment by how much it faces up; its inner face is the dark bore."""
    k = math.cos(math.radians(ang))
    c.front.fill(shade(color, 0.8 + 0.28 * k))
    if noise:
        c.front.noise(noise, seed)
    if k > 0.93:  # a streak of light along the top
        c.front.vline(c.front.w // 2, shade(color, 1.3))
    if inner:
        c.back.fill(inner)


def pipe(g, f0, f1, cu, cs, r, t, color, n=16, inner=DARK, noise=2, bone=None, keep=None):
    """A hollow round tube along f: n wall segments turned evenly about the axis (outer radius r, wall t).
    `keep(angle)` may leave segments out (ports, cuts); angle 0 is the top, 90 the right side (-s), 270 the
    left. Returns the segments; each has .ang. At LOW detail, a plain rod."""
    if LOW[0]:
        return g.rod(f0, f1, cu, cs, r, color, bone=bone)
    w = max(1, math.ceil(2 * r * math.tan(math.pi / n) - 0.05))
    t = max(1, round(t))
    out = []
    for i in range(n):
        ang = 360.0 * i / n
        if keep and not keep(ang):
            continue
        c = g.box(f0, f1, cu + r - t, cu + r, cs - w / 2, cs + w / 2, color, noise, roll=ang if ang else 0.0,
                  pivot=((f0 + f1) / 2, cu, cs), bone=bone)
        _seg_light(c, color, ang, noise, g.seed + i * 13 + int(f0), inner)
        c.ang = ang
        out.append(c)
    return out


def cone(g, f0, f1, cu, cs, r0, r1, t, color, n=16, inner=DARK, noise=2, bone=None):
    """A hollow cone along f, outer radius r0 at f0 and r1 at f1: n tilted wall segments turned about the axis.
    At LOW detail, two stepped rods."""
    if LOW[0]:
        fm = (f0 + f1) / 2
        return g.rod(f0, fm, cu, cs, max(0.5, r0 * 0.75 + r1 * 0.25), color, bone=bone) + \
            g.rod(fm, f1, cu, cs, max(0.5, r0 * 0.25 + r1 * 0.75), color, bone=bone)
    length = f1 - f0
    th = math.atan2(r1 - r0, length)
    seg = math.hypot(length, r1 - r0)
    t = max(1, round(t))
    rm = (r0 + r1) / 2 - t / 2
    rc, d = rm * math.cos(th), rm * math.sin(th)
    fm = (f0 + f1) / 2
    w = max(1, math.ceil(2 * max(r0, r1) * math.tan(math.pi / n) - 0.05))
    out = []
    for i in range(n):
        ang = 360.0 * i / n
        c = g.box(fm + d - seg / 2, fm + d + seg / 2, cu + rc - t / 2, cu + rc + t / 2, cs - w / 2, cs + w / 2, color,
                  noise, tilt=math.degrees(th), roll=ang, pivot=(fm, cu, cs), bone=bone)
        _seg_light(c, color, ang, noise, g.seed + i * 17 + int(f0), inner)
        c.ang = ang
        out.append(c)
    return out


def vcyl(g, f, s, u0, u1, r, color, noise=2, bone=None):
    """A round post standing along u (a shell in a side saddle, a turret, a knob): two crossed boxes."""
    b = r * 0.42
    out = [g.box(f - r, f + r, u0, u1, s - r + b, s + r - b, color, noise, bone=bone),
           g.box(f - r + b, f + r - b, u0, u1, s - r, s + r, color, noise, bone=bone)]
    for c in out:  # rounded: darker towards the front and back edges
        for face in (c.right, c.left):
            _shade_face(face, lambda x, y, w, h: 1.0 - 0.22 * abs((y + 0.5) / h * 2 - 1) ** 2)
    return out


def scyl(g, f, u, s0, s1, r, color, noise=2, bone=None):
    """A round knob or pin lying across the gun (along s): two crossed boxes."""
    b = r * 0.42
    out = [g.box(f - r, f + r, u - r + b, u + r - b, s0, s1, color, noise, bone=bone),
           g.box(f - r + b, f + r - b, u - r, u + r, s0, s1, color, noise, bone=bone)]
    return out


def stud(g, f, u, s, side, color=None, d=1.0, proud=0.5, bone=None):
    """A pin end or screw head on a side surface at s, standing `proud` out of it (none at LOW detail)."""
    if LOW[0]:
        return None
    col = color or shade(SILVER, 0.8)
    if side == "left":
        s0, s1 = s - 1 + proud, s + proud
    else:
        s0, s1 = s - proud, s + 1 - proud
    infl = (d - 1) / 2
    c = g.box(f - 0.5, f + 0.5, u - 0.5, u + 0.5, s0, s1, col, 1, inflate=infl, bone=bone)
    getattr(c, side).fill(col)
    getattr(c, side).px(0, 0, shade(col, 1.3))
    return c


def grain(c, color, seed=0, sides=("right", "left", "up", "down"), every=(2, 4)):
    """Wood: wavy darker and lighter streaks running along the length."""
    rnd = random.Random(seed)
    for side in sides:
        face = getattr(c, FACES[side])
        x0 = rnd.randint(0, 1)
        while x0 < face.w:
            ph, amp, per = rnd.random() * 6.3, rnd.choice((0.0, 0.6, 1.0, 1.4)), rnd.uniform(4, 9)
            k = rnd.choice((0.8, 0.84, 0.88, 1.1))
            for y in range(face.h):
                x = int(round(x0 + amp * math.sin(y / per + ph)))
                if 0 <= x < face.w:
                    face.px(x, y, shade(face.get(x, y), k))
            x0 += rnd.randint(*every)


def weave(c, sides=("up",), a=1.07, b=0.93):
    """Carbon fibre: a 2x2 basket weave."""
    for side in sides:
        face = getattr(c, FACES[side])
        _shade_face(face, lambda x, y, w, h: a if ((x // 2) + (y // 2)) % 2 else b)


def dashes(face, x0, x1, y0, y1, color, step=2, seed=0):
    """Stencilled lettering seen from afar: short strokes in rows (texture coordinates)."""
    rnd = random.Random(seed)
    for y in range(y0, y1):
        for x in range(x0, x1):
            if (x - x0) % step == 0 and rnd.random() < 0.7:
                face.px(x, y, color)


def ribbed(c, sides, every, color, start=1):
    for side in sides:
        face = getattr(c, FACES[side])
        for y in range(start, face.h, every):
            face.hline(y, color)


# =========================================================================== Remington 870

def rem870():
    """Remington 870 pump-action 12 gauge: blued receiver with ejection and loading ports, vent-rib barrel with a
    bead, magazine tube with the barrel ring and cap, ribbed walnut fore-end on twin action bars, walnut stock
    with a semi-pistol grip and recoil pad, and a six-shell side saddle on the receiver's left."""
    g = gun("rem870", "rifle", "pump")
    R = BLUED
    # ---- receiver: lower walls round the loading port, upper walls round the ejection port, a rounded top
    lower = g.box(-6, 22, 7, 11, -4, 4, R)
    roll_mark(lower, "right", 0, 20, 8.5)
    mark(lower, "down", 10, 21, 0, 0, DARK, -3, 3)  # the loading port's inside
    g.box(-6, 10, 6, 7, -4, 4, R)
    g.box(21, 22, 6, 7, -4, 4, R)
    for s0 in (-4, 3):
        g.box(10, 21, 6, 7, s0, s0 + 1, R)
    lift = g.box(11, 20, 6.5, 7.5, -2.5, 2.5, shade(STEEL, 1.1), 2)  # shell lifter (carrier)
    mark(lift, "down", 12, 19, 0, 0, shade(STEEL, 0.7), -0.5, 0.5)
    core = g.box(-6, 22, 11, 16, -3, 3, R)
    mark(core, "right", 2, 14, 11, 16, DARK)
    left = g.box(-6, 22, 11, 16, 3, 4, R)
    roll_mark(left, "left", 0, 20, 14)
    g.box(-6, 2, 11, 16, -4, -3, R)
    g.box(14, 22, 11, 16, -4, -3, R)
    g.box(2, 14, 11, 12, -4, -3, R)  # port sill
    top = g.bevel(-6, 22, 14, 18, -4, 4, R, 2, edges=("tl", "tr"))
    for c in top[:2]:
        mark(c, "up", -5, 21, 0, 0, shade(R, 0.8), -0.5, 0.5)  # matted sighting groove
    bolt = g.box(2, 13, 12, 16, -3.5, -2.5, "#7d838b", 2)  # the bolt, seen in the port
    mark(bolt, "right", 2, 13, 13.5, 14, shade("#7d838b", 0.6))
    mark(bolt, "right", 11, 13, 12, 16, shade("#7d838b", 1.25))  # bolt face and extractor
    mark(bolt, "right", 12, 13, 14, 15, DARK)
    g.box(13, 14, 12, 16, -3.2, -2.2, DARK, 1)  # gap to the barrel extension
    # receiver rear: the tang slopes down into the stock
    g.box(-9, -6, 9, 17, -3.5, 3.5, R, tilt=-12, pivot=(-6, 17))
    # a low scope rail on the receiver (the optic mount sits on it)
    base = g.box(1, 15, 18, 19, -2, 2, ANOD, 2)
    for f in range(2, 15, 2):
        mark(base, "up", f, f + 1, 0, 0, DARK, -2, 2)
        mark(base, "right", f, f + 1, 18, 19, DARK)
        mark(base, "left", f, f + 1, 18, 19, DARK)
    for f in (3, 13):
        stud(g, f, 18.5, 2, "left", DARK) if False else None
    # trigger plate pins (the side saddle hangs on the left ends)
    for f in (-3, 13):
        stud(g, f, 8.5, -4, "right")
    # ---- trigger group
    g.box(-6, 10, 5, 6, -2.5, 2.5, ANOD, 2)  # trigger plate
    g.box(-4, -2, 1.5, 5, -1, 1, ANOD, 2, tilt=12, pivot=(-3, 5))  # guard: rear
    g.box(-3, 8, 1, 2, -1, 1, ANOD, 2)  # bottom
    g.box(7.5, 9.5, 1.5, 5, -1, 1, ANOD, 2, tilt=-14, pivot=(8.5, 5))  # front
    if hi():
        g.box(-3.5, -2, 1, 2.5, -1, 1, ANOD, 1, tilt=45, pivot=(-2.75, 1.75))
        g.box(7, 8.5, 1, 2.5, -1, 1, ANOD, 1, tilt=-45, pivot=(7.75, 1.75))
    g.box(3, 4.5, 3.5, 5.5, -0.5, 0.5, "#24262a", 1)  # trigger blade, curling forward
    g.box(3.5, 5, 2.2, 3.7, -0.5, 0.5, "#24262a", 1, tilt=-30, pivot=(4.25, 3))
    for c in scyl(g, -1.5, 4.2, -3.4, 3.4, 0.8, shade(STEEL, 1.1), 1):  # crossbolt safety
        pass
    if hi():
        g.box(-2.3, -0.7, 3.4, 5, 2.6, 3.0, SHELL_RED, 0)  # the red ring: ready to fire
        g.box(9, 12.5, 4.3, 5.3, 2.4, 3.4, R, 1, tilt=-18, pivot=(9, 5))  # action bar lock release
    # ---- barrel: chamber, vent rib, beads, crowned muzzle
    g.rod(22, 30, 15, 0, 2.9, R)
    g.rod(30, 90, 15, 0, 2.6, R)
    g.rod(90, 92, 15, 0, 2.75, shade(STEEL, 0.9))  # flush choke tube
    g.box(91.4, 92.4, 13.5, 16.5, -1.5, 1.5, DARK, 0, inflate=-0.1)  # the bore
    rib = g.box(24, 91, 19, 20, -1, 1, R, 2)
    for f in range(24, 91, 2):
        mark(rib, "up", f, f + 1, 0, 0, shade(R, 0.75), -1, 1)  # matted top
    g.box(22, 24, 17, 19, -1, 1, R, 2, tilt=-20, pivot=(24, 19))  # the rib rising off the receiver
    for f in range(27, 91, 4):
        g.box(f, f + 1, 17, 19, -0.5, 0.5, shade(R, 0.9), 1)  # rib posts
    g.box(89, 90, 20, 21, -0.5, 0.5, IVORY, 0, inflate=0.15)  # front bead
    g.box(58, 59, 20, 21, -0.5, 0.5, SILVER, 0, inflate=-0.15)  # middle bead
    # ---- magazine tube, barrel ring and (in def_mag) the cap
    g.rod(22, 72, 9, 0, 2.6, R)
    g.rod(72, 76, 9, 0, 3.1, R)  # barrel ring round the magazine tube
    g.box(72.5, 75.5, 11, 13, -1.5, 1.5, R, 2)
    g.muzzle = (92.0, 15.0)
    # ---- pump: ribbed walnut fore-end on the twin action bars
    g.part("pump", 40, 9)
    g.use("pump")
    W = WALNUT_L
    core = g.bevel(33, 51, 4.5, 13.5, -4.5, 4.5, W, 2)
    for i, c in enumerate(core[:2]):
        grain(c, W, 11 + i)
    for i, c in enumerate(g.bevel(31, 33, 3.5, 14, -5.5, 5.5, W, 2.5)):  # rear flare
        grain(c, W, 21 + i) if i < 2 else None
    for f in range(34, 50, 2):  # the rings of the ribbed grip
        for c in (g.box(f, f + 1, 4, 14, -4, 4, W, 2), g.box(f, f + 1, 5.5, 12.5, -5, 5, W, 2)):
            grain(c, W, f)
    for s0 in (-5, 3.5):  # the fore-end's ears up the sides of the barrel
        c = g.box(33, 51, 13, 15, s0, s0 + 1.5, W, 2)
        grain(c, W, 40 + s0)
    g.rod(51, 53, 9, 0, 3, R)  # fore-end tube nut
    if hi():
        for s in (-1.8, 1.8):
            g.box(52.5, 53.5, 8.5, 9.5, s - 0.5, s + 0.5, DARK, 0)  # spanner notches
    for s0 in (-3.8, 2.8):  # action bars
        g.box(18, 33, 8, 10, s0, s0 + 1, shade(STEEL, 1.15), 1)
    g.use("frame")
    # ---- the shell being loaded (moved by the reload animation)
    g.part("shell", 7, 4)
    g.use("shell")
    hull = g.rod(2.5, 10, 8, 0, 1.5, SHELL_RED)
    for c in hull:
        for side in ("right", "left", "up", "down"):
            face = getattr(c, FACES[side])
            for y in range(0, face.h, 2):
                face.hline(y, shade(SHELL_RED, 0.85))
    g.rod(10, 11, 8, 0, 1.2, shade(SHELL_RED, 0.75))  # crimp
    g.rod(1, 3, 8, 0, 1.6, BRASS)
    g.rod(0.6, 1.6, 8, 0, 1.75, shade(BRASS, 0.85))  # rim
    if hi():
        g.box(0.2, 1.2, 7.5, 8.5, -0.5, 0.5, shade(SILVER, 0.9), 0)  # primer
    g.use("frame")
    # ---- magazine cap (def_mag): the factory magazine as attachments see it (mag_profile)
    mag_bones(g, 76, 9)
    for c in g.rod(76, 79, 9, 0, 3, R):
        for side in ("right", "left", "up", "down"):
            face = getattr(c, FACES[side])
            for y in range(0, face.h, 2):
                face.hline(y, shade(R, 1.3))  # knurled grip
    g.rod(79, 80, 9, 0, 2.4, R)
    if hi():
        g.box(77, 79, 4.5, 6.5, -0.5, 0.5, STEEL, 1)  # sling swivel stud and loop
        g.box(75.5, 80.5, 3, 4, -0.5, 0.5, STEEL, 1)
        g.box(75.5, 76.5, 3, 5, -0.5, 0.5, STEEL, 1)
        g.box(79.5, 80.5, 3, 5, -0.5, 0.5, STEEL, 1)
    g.mag_profile = dict(f0=76, top=9, width=6, color=BLUED, kind="tube")
    g.use("frame")
    # ---- side saddle: an aluminium plate on the trigger plate pins, a polymer carrier and six shells
    if hi():
        plate = g.box(-2, 21, 7, 17, 4, 5, ANOD, 2)
        for f, u in ((-1, 8), (20, 8), (-1, 16), (20, 16)):
            stud(g, f, u, 5, "left", shade(SILVER, 0.7))
        g.box(-2, 21, 9.5, 14.5, 5, 6.5, POLY, 2)  # carrier
        for i in range(6):
            f = 0.5 + 3.5 * i
            sh = vcyl(g, f, 7.3, 9, 17.5, 1.5, SHELL_RED)
            for c in sh:
                for face in (c.right, c.left):
                    for x in range(1, face.w, 2):
                        face.vline(x, shade(face.get(x, 0), 0.88))
                c.front.fill(shade(SHELL_RED, 0.7))  # crimped top
            vcyl(g, f, 7.3, 7, 9, 1.6, BRASS)
            g.box(f - 1.7, f + 1.7, 6.6, 7.2, 5.6, 9, shade(BRASS, 0.8), 1)  # rims
        for i in range(7):
            f = -1.25 + 3.5 * i
            g.box(f - 0.5, f + 0.5, 10, 14, 6.5, 8.3, POLY, 1)  # the carrier's fingers between the shells
    # ---- mounts
    g.mount("optic", 8, 19, length=12, default=False)
    g.mount("muzzle", 92, 15, bore=2.6)
    g.mount("side", 42, 9, 5, length=10, default=False, parent="pump")
    g.mount("stock", -6, 12)
    # ---- walnut stock (def_stock): semi-pistol grip, comb, white-line spacer and recoil pad, sling stud
    g.use("def_stock")
    W = WALNUT
    parts = []
    parts += g.bevel(-17, -8, 6, 16, -3.5, 3.5, W, 1.5)[:2]  # wrist
    parts += g.bevel(-52, -22, 9, 17, -4.5, 4.5, W, 2)[:2]  # comb and heel
    parts.append(g.box(-25, -12, 11, 16, -3.5, 3.5, W, tilt=-11, pivot=(-25, 16)))  # comb nose into the wrist
    parts.append(g.box(-52, -16, -0.5, 10, -4.5, 4.5, W, tilt=6, pivot=(-52, -0.5)))  # butt, toe line rising
    parts.append(g.box(-52, -17, -1, 4, -3.5, 3.5, W, tilt=6, pivot=(-52, -1)))  # rounded underside
    grip = g.box(-21, -11, 1.5, 9, -3.5, 3.5, W, tilt=-22, pivot=(-11, 9))  # the pistol grip
    parts.append(grip)
    parts.append(g.box(-12, -6, 5.5, 10, -3.5, 3.5, W, tilt=-30, pivot=(-6, 10)))  # grip front up to the guard
    for i, c in enumerate(parts):
        grain(c, W, 70 + i)
    knurl(parts[0], "right", -16, -9, 8, 14, shade(W, 0.7))  # checkering
    knurl(parts[0], "left", -16, -9, 8, 14, shade(W, 0.7))
    g.box(-22, -15, 0.5, 1.5, -3, 3, "#1e1e20", 1, tilt=-22, pivot=(-11, 9))  # grip cap
    g.box(-53, -52, -1, 17, -4.5, 4.5, IVORY, 1)  # white-line spacer
    pad = g.bevel(-56, -53, -1.5, 17.5, -4.75, 4.75, PAD, 1, noise=2)
    for c in pad[:2]:
        face = c.bottom  # the pad's back: ribs across it
        for x in range(1, face.w, 2):
            face.vline(x, shade(PAD, 0.7))
    if hi():
        g.box(-45.5, -44.5, -1.2, 0.5, -0.5, 0.5, STEEL, 1)  # sling stud
        g.box(-47, -43, -3, -2, -0.5, 0.5, STEEL, 1)
        g.box(-47, -46, -3, -1, -0.5, 0.5, STEEL, 1)
        g.box(-44, -43, -3, -1, -0.5, 0.5, STEEL, 1)
    g.use("frame")
    return g


# =========================================================================== AWM

def awm():
    g = gun("awm", "rifle", "bolt")
    g.rod(-16, 12, 15, 0, 4.5, STEEL)  # round action
    g.teeth_rail(-14, 22, 19.5, -3, 3)
    g.box(-16, 12, 6, 12, -4.5, 4.5, AWM_GREEN)  # chassis under the action
    fore = g.bevel(12, 54, 4, 14, -5, 5, AWM_GREEN, 1.5)
    for c in fore[:2]:
        slots(c, ("right", "left"), 16, 52, 7, 10, 6, 4, shade(AWM_GREEN, 0.6))
    g.trigger(-12, 6)
    g.pistol_grip(-18, -10, 8, 17, 6, AWM_GREEN, angle=8)
    g.rod(54, 96, 15, 0, 2.8, DARK)
    for c in g.rod(54, 86, 15, 0, 2.9, DARK):  # fluting
        for side in ("right", "left"):
            face = getattr(c, side)
            for x in range(0, face.w, 2):
                face.vline(x, GUNMETAL)
    g.muzzle = (104.0, 15.0)
    g.part("bolt", -8, 15, -4)
    g.use("bolt")
    g.rod(-22, -16, 15, 0, 2.5, STEEL)
    g.box(-8, -5, 14, 16, -10, -4, SILVER, 1)
    g.rod(-11, -3, 15, -12, 3, POLY)  # big bolt knob
    g.use("frame")
    mag_bones(g, 4, 6)
    mg = g.box(-2, 10, 0, 8, -3.5, 3.5, DARK)
    ribs(mg, ("right", "left"), 2, shade(DARK, 1.6))
    g.box(-3, 11, -2, 0, -4, 4, POLY)
    g.mag_profile = dict(f0=-2, top=8, width=7, segs=[(0, 10)], color=DARK, kind="sniper")
    g.mount("optic", 4, 22.5, length=36)
    g.use("def_optic")
    g.box(-2, 2, 22.5, 28, -3, 3, BLACK)  # rings
    g.box(18, 22, 22.5, 28, -3, 3, BLACK)
    g.rod(-12, 26, 29, 0, 3.5, POLY)  # factory 3-12x scope
    g.rod(26, 30, 29, 0, 4.5, POLY)
    g.rod(30, 42, 29, 0, 5.5, POLY)
    g.rod(-22, -12, 29, 0, 4.5, POLY)
    g.rod(-24, -22, 29, 0, 3.5, RUBBER)
    g.lens(42, 25, 33, -3, 3)
    g.lens(-25, 26, 32, -2, 2, "#7fd0f5")
    g.box(6, 10, 32, 36, -2, 2, BLACK)
    g.box(6, 10, 27, 31, -8, -3, BLACK)
    g.box(7, 9, 36, 37, -1, 1, SILVER, 1)
    g.mount("muzzle", 96, 15, bore=2.8)
    g.use("def_muzzle")
    brake = g.bevel(96, 104, 11, 19, -4, 4, DARK, 1)
    for c in brake[:2]:
        for side in ("right", "left"):
            mark(c, side, 98, 100, 13, 17, "#060607")
            mark(c, side, 101, 103, 13, 17, "#060607")
    g.mount("underbarrel", 42, 4)
    g.use("def_underbarrel")
    g.box(44, 48, 1, 4, -3, 3, BLACK)
    g.rod(22, 46, 2, -3, 1, SILVER)
    g.rod(22, 46, 2, 3, 1, SILVER)
    g.mount("side", 36, 10, 5, length=10, default=False)
    g.mount("stock", -18, 12)
    g.use("def_stock")
    g.box(-50, -18, 14, 18, -4, 4, AWM_GREEN)  # thumbhole stock: top bar
    g.box(-50, -24, 2, 6, -4, 4, AWM_GREEN)  # bottom bar
    g.box(-26, -18, 2, 14, -4, 4, AWM_GREEN)  # front post (behind the grip)
    g.bevel(-58, -46, 2, 18, -4.5, 4.5, AWM_GREEN, 1.5)  # butt
    g.box(-46, -28, 18, 21, -3, 3, AWM_GREEN)  # cheek piece
    g.box(-44, -42, 21, 22, -1, 1, SILVER, 1)
    g.bevel(-60, -58, 2, 18, -4.5, 4.5, RUBBER, 1)
    g.box(-52, -48, -4, 2, -1.5, 1.5, DARK)  # monopod
    g.use("frame")
    return g


# =========================================================================== launchers

def carl_gustaf():
    g = gun("carl_gustaf", "launcher", "launcher_rear")
    for c in g.rod(-40, 50, 22, 0, 9, CARBON):
        for side in ("right", "left", "up", "down"):
            for f0 in (-30, 10, 40):
                mark(c, side, f0, f0 + 2, c.ext[2], c.ext[3], shade(CARBON, 0.7))
    g.rod(48, 52, 22, 0, 10, BLACK)  # muzzle ring
    g.pistol_grip(-12, -6, 13, 14, 6, POLY, angle=8)
    g.trigger(-12, 13)
    g.box(6, 12, 0, 13, -2, 2, POLY, tilt=4)  # front grip
    g.box(-30, -14, 11, 13, -6, 6, RUBBER, 2)  # shoulder rest
    g.box(-6, 14, 31, 34, -1, 1, BLACK)  # carry handle
    g.box(-6, -4, 30, 31, -1, 1, BLACK)
    g.box(12, 14, 30, 31, -1, 1, BLACK)
    g.part("breech", -40, 22, 9)  # the venturi swings open to load
    g.rod(-56, -40, 22, 0, 10, DARK, bone="breech")
    g.rod(-60, -56, 22, 0, 11, "#0b0c0e", bone="breech")
    g.part("rocket", -24, 22)
    g.rod(-38, -10, 22, 0, 7.5, "#6a7040", bone="rocket")  # the round, inside the tube
    g.rod(-40, -38, 22, 0, 8, BRASS, bone="rocket")
    mag_bones(g, -24, 22)
    g.muzzle = (52.0, 22.0)
    g.mount("optic", 4, 30, 12, length=8)
    g.use("def_optic")
    g.box(-4, 12, 26, 34, 9, 15, DARK)
    g.lens(12, 27, 33, 10, 14)
    g.lens(-5, 28, 32, 11, 13, "#7fd0f5")
    g.use("frame")
    return g


def rpg7():
    g = gun("rpg7", "launcher", "launcher_front")
    g.rod(-40, 36, 20, 0, 4, BLUED)  # tube
    g.rod(-14, 14, 20, 0, 6, WOOD)  # heat shield
    for f0 in (-14, -2, 10):
        g.ring(f0, f0 + 1, 20, 0, 6.3, BLUED)
    g.rod(-44, -40, 20, 0, 4.6, BLUED)  # flare
    g.rod(-50, -44, 20, 0, 5.6, BLUED)
    g.rod(-56, -50, 20, 0, 7, DARK)
    g.rod(34, 36, 20, 0, 5, BLUED)
    g.pistol_grip(-4, 2, 15, 14, 6, BLUED, angle=10, stipple=False)
    g.pistol_grip(14, 20, 15, 12, 6, BLUED, angle=10, stipple=False)
    g.trigger(-4, 15)
    g.box(26, 28, 24, 30, -1, 1, BLUED)  # folding iron sights
    g.box(2, 4, 24, 29, -1.5, 1.5, BLUED)
    g.part("rocket", 40, 20)
    g.rod(36, 44, 20, 0, 2.5, "#3a4228", bone="rocket")
    g.rod(44, 48, 20, 0, 5.5, "#4a5530", bone="rocket")
    g.rod(48, 56, 20, 0, 7, "#4a5530", bone="rocket")
    g.ring(52, 53, 20, 0, 7.2, "#c9a43a", bone="rocket")
    g.rod(56, 62, 20, 0, 5.5, "#4a5530", bone="rocket")
    g.rod(62, 67, 20, 0, 3.5, "#3a4228", bone="rocket")
    g.rod(67, 71, 20, 0, 2, DARK, bone="rocket")
    g.rod(71, 74, 20, 0, 1, DARK, bone="rocket")
    mag_bones(g, 40, 20)
    g.muzzle = (74.0, 20.0)
    g.mount("optic", 2, 28, 8, length=8)
    g.use("def_optic")
    g.box(-4, 8, 22, 26, 4, 8, BLUED)  # PGO-7 bracket
    g.box(-8, 10, 25, 31, 8, 13, DARK)
    g.rod(-16, -8, 28, 10.5, 2.5, RUBBER)
    g.lens(10, 26, 30, 9, 12)
    g.use("frame")
    return g
