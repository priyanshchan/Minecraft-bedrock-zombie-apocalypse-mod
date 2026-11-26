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


def grain(c, color, seed=0, sides=("right", "left", "up", "down"), every=(2, 4), flat=True):
    """Wood: wavy darker and lighter streaks running along the length. With `flat`, the sides are first
    repainted without the box's own top-to-bottom light, so pieces of one stock blend into each other."""
    rnd = random.Random(seed)
    for side in sides:
        face = getattr(c, FACES[side])
        if flat and side in ("right", "left"):
            face.fill(shade(color, 0.95))
            face.noise(3, seed + len(side))
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
    # a low scope rail on the receiver (the optic mount sits on it)
    base = g.box(1, 15, 18, 19, -2, 2, ANOD, 2)
    for f in range(2, 15, 2):
        mark(base, "up", f, f + 1, 0, 0, DARK, -2, 2)
        mark(base, "right", f, f + 1, 18, 19, DARK)
        mark(base, "left", f, f + 1, 18, 19, DARK)
    # trigger plate pins (the side saddle hangs on their left ends) and the cartridge stop rivets
    for f, u in ((-3, 8.5), (13, 8.5), (18.5, 9.5), (20.5, 8)):
        stud(g, f, u, -4, "right")
    g.rod(22, 23.5, 15, 0, 3.3, R)  # breech end of the barrel
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
        for side in ("right", "left", "down"):
            for f in range(35, 50, 2):
                mark(c, side, f, f + 1, 4.5, 13.5, shade(W, 0.62))  # the grooves between the ribs
    for i, c in enumerate(g.bevel(31, 33, 3.5, 14, -5.5, 5.5, W, 2.5)):  # rear flare
        grain(c, W, 21 + i) if i < 2 else None
    for f in range(34, 50, 2):  # the rings of the ribbed grip, their edges rounded
        for c in (g.box(f, f + 1, 4, 14, -3.5, 3.5, W, 2), g.box(f, f + 1, 5.5, 12.5, -5, 5, W, 2)):
            grain(c, W, f)
        if hi():
            for cu, cs in ((12.5, 3.5), (12.5, -3.5), (5.5, 3.5), (5.5, -3.5)):
                c = g.box(f, f + 1, cu - 0.5, cu + 0.5, cs - 0.5, cs + 0.5, shade(W, 0.95), 2, inflate=0.55, roll=45,
                          pivot=(f, cu, cs))
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
    # ---- walnut stock (def_stock): semi-pistol grip with a cap, comb, white-line spacer, recoil pad, sling stud
    g.use("def_stock")
    W = WALNUT
    parts = []
    parts += g.bevel(-10, -6, 6, 18, -4, 4, W, 2)[:2]  # the head, matching the receiver
    parts += g.bevel(-24, -9, 6.5, 15.5, -3.5, 3.5, W, 1.5)[:2]  # wrist
    parts += g.bevel(-52, -25, 8, 17, -4.5, 4.5, W, 2)[:2]  # comb and heel
    parts.append(g.box(-31, -19, 11, 16, -3.5, 3.5, W, tilt=-9, pivot=(-31, 16)))  # comb nose down into the wrist
    toe = math.degrees(math.atan2(2.5, 37))  # the line from the toe up to the grip cap
    parts.append(g.box(-52, -26, -0.5, 9, -4.5, 4.5, W, tilt=toe, pivot=(-52, -1)))  # butt
    parts.append(g.box(-52, -15, -1, 9, -3.5, 3.5, W, tilt=toe, pivot=(-52, -1)))  # its rounded underside
    parts.append(g.box(-34, -15, -0.5, 9, -3.75, 3.75, W, tilt=toe, pivot=(-52, -1)))  # into the grip
    parts.append(g.box(-17, -5, 1, 8, -3.5, 3.5, W, tilt=26, pivot=(-17, 1)))  # the grip's front, up to the guard
    for i, c in enumerate(parts):
        grain(c, W, 70 + i)
    for side in ("right", "left"):
        knurl(parts[2], side, -20, -11, 8, 14, shade(W, 0.72))  # checkering on the wrist
    g.box(-19, -15, 0.6, 1.6, -3, 3, "#1e1e20", 1, tilt=toe, pivot=(-52, -1))  # grip cap
    g.box(-53, -52, -1, 17, -4.5, 4.5, IVORY, 1)  # white-line spacer
    pad = g.bevel(-56, -53, -1.5, 17.5, -4.75, 4.75, PAD, 1, noise=2)
    for c in pad[:2]:
        face = c.bottom  # the pad's back: ribs across it
        for x in range(1, face.w, 2):
            face.vline(x, shade(PAD, 0.7))
    if hi():
        g.box(-45.5, -44.5, -0.5, 1, -0.5, 0.5, STEEL, 1)  # sling stud and swivel
        g.box(-47, -43, -2.5, -1.5, -0.5, 0.5, STEEL, 1)
        g.box(-47, -46, -2.5, -0.5, -0.5, 0.5, STEEL, 1)
        g.box(-44, -43, -2.5, -0.5, -0.5, 0.5, STEEL, 1)
    g.use("frame")
    return g


# =========================================================================== AWM

def awm():
    """Accuracy International AWM (.338 Lapua Magnum): round action with an ejection port showing the bolt,
    recoil lug and long top rail, the green AI stock on its aluminium chassis with hex screws and a side rail,
    fluted barrel, two-port muzzle brake, a 5-25x56 scope on rings, folding bipod, and the folding thumbhole
    stock with an adjustable cheek piece, spacers, butt pad and monopod."""
    g = gun("awm", "rifle", "bolt")
    G = AWM_GREEN
    ACT = "#3c3f44"
    BBL = "#2b2d31"
    # ---- action: a round receiver with the port on its upper right, bridge and front ring, recoil lug
    pipe(g, -16, -6, 15, 0, 3.5, 1, ACT, n=12)
    pipe(g, -6, 8, 15, 0, 3.5, 1, ACT, n=12, keep=lambda a: not 15 < a < 105)
    pipe(g, 8, 13, 15, 0, 3.5, 1, ACT, n=12)
    if hi():
        for f0, f1 in ((-16, -13), (9, 13)):
            pipe(g, f0, f1, 15, 0, 3.9, 1, ACT, n=12)  # rear bridge and front ring
        g.box(-15, -11, 15, 16.5, 3.5, 4.5, ANOD, 1)  # bolt release
        g.box(-15, -12, 15.5, 17, -4.5, -3.5, ANOD, 1)  # three-position safety
        g.box(-13, -11, 16.5, 18, -4.8, -3.8, ANOD, 1, tilt=30, pivot=(-12, 16.5))
    g.box(13, 15, 9.5, 19, -3.5, 3.5, "#26282c", 2)  # recoil lug
    g.rod(15, 22, 15, 0, 3.2, BBL)  # barrel shank
    # rail: a base on the action and a long picatinny rail
    g.box(-15, 21, 18, 20, -2, 2, ANOD, 2)
    g.teeth_rail(-14, 22, 19.5, -3, 3, ANOD)
    # ---- chassis: the green stock round the action, the black aluminium bedding, screws, magazine well
    body = g.box(-18, 13, 5, 13, -4.5, 4.5, G)
    g.box(-18, 13, 12, 13.5, -5, 5, ANOD, 2)  # chassis rails along the action
    for side, s0 in (("right", -4.5), ("left", 4.5)):
        for f in (-14, 9):
            stud(g, f, 10, s0, side, shade(SILVER, 0.6))
    roll_mark(body, "left", -10, 6, 8, shade(G, 1.35))
    for f0, f1, s0, s1 in ((-3.5, -2, -4.5, 4.5), (8, 9.5, -4.5, 4.5), (-3.5, 9.5, -4.5, -3.5), (-3.5, 9.5, 3.5, 4.5)):
        g.box(f0, f1, 3, 5, s0, s1, G, 2)  # magazine well
    # ---- fore-end: a channel for the floated barrel, end cap, flush cups, screws and a short side rail
    g.bevel(13, 56, 4, 10, -5, 5, G, 1.5, edges=("bl", "br"))
    for s0 in (-5, 3):
        wall = g.box(13, 56, 9, 15, s0, s0 + 2, G)
        mark(wall, "up", 13, 56, 0, 0, shade(G, 1.2), s0, s0 + 2)
    g.box(13, 56, 9, 10, -3, 3, shade(G, 0.55), 1)  # the channel floor
    g.box(56, 57, 4.5, 14.5, -4.5, 4.5, ANOD, 2)  # end cap
    for side, s0 in (("right", -5), ("left", 5)):
        for f in (20, 32, 46):
            stud(g, f, 7, s0, side, shade(SILVER, 0.6))
    if hi():
        qd_cup(g, 51, 7, -5, "right", ANOD)
        qd_cup(g, 51, 7, 5, "left", ANOD)
        side_rail = g.box(29, 43, 8, 12, 5, 5.5, ANOD, 2)
        for f in range(29, 42, 3):
            g.box(f, f + 2, 8, 12, 5.5, 6.5, shade(ANOD, 1.1), 1)
    # ---- trigger, guard and grip
    g.box(-12, -10, 0, 5, -1, 1, G, 2)  # guard rear
    g.box(-12, -2, -0.5, 1, -1, 1, G, 2)  # bottom
    g.box(-3.5, -2, -0.5, 5, -1, 1, G, 2)  # front
    g.box(-7.5, -6, 3, 5, -0.5, 0.5, SILVER, 1)  # trigger blade
    g.box(-7, -5.5, 1.5, 3.2, -0.5, 0.5, SILVER, 1, tilt=-25, pivot=(-6.25, 3))
    if hi():
        g.box(-5, -4, 1.5, 4, -1.5, 1.5, ANOD, 1, tilt=15, pivot=(-4.5, 4))  # magazine release paddle
    g.pistol_grip(-18, -10, 8, 17, 6, G, angle=8)
    # ---- barrel: shank, fluted middle (lands standing between the flutes), plain muzzle end
    g.rod(22, 28, 15, 0, 2.8, BBL)
    g.rod(28, 84, 15, 0, 2.2, shade(BBL, 0.8))
    if hi():
        for ang in (0, 45, 90, 135):
            c = g.box(28, 84, 12, 18, -0.5, 0.5, BBL, 2, inflate=-0.15, roll=ang if ang else 0.0, pivot=(56, 15, 0))
            for face in (c.front, c.back):
                face.vline(face.w // 2, shade(BBL, 1.5))  # the lands catch the light
    g.rod(84, 94, 15, 0, 2.8, BBL)
    g.rod(94, 96, 15, 0, 2.4, shade(BBL, 1.2))  # thread
    g.muzzle = (104.0, 15.0)
    # ---- bolt: body seen through the port, lugs, shroud with the cocking indicator, handle with a big knob
    g.part("bolt", -8, 15, 0)
    g.use("bolt")
    BOLT = "#8f959c"
    g.rod(-16, 8, 15, 0, 2.4, BOLT)
    for c in g.rod(5, 8, 15, 0, 2.5, shade(BOLT, 1.1)):  # locking lugs
        ribs(c, ("right", "left", "up", "down"), 2, shade(BOLT, 0.6))
    g.rod(-22, -16, 15, 0, 2.8, ANOD)  # shroud
    g.rod(-24, -22, 15, 0, 1.4, ANOD)
    if hi():
        g.box(-24.4, -23.4, 14.5, 15.5, -0.5, 0.5, RED, 0)  # cocked indicator
    KNOB = "#44474d"
    g.box(-11, -8, 14, 16, -10, -2, GUNMETAL, 2)  # handle
    g.rod(-12, -7, 15, -12, 2.6, KNOB)  # knob: three crossed rounds make a ball
    if hi():
        scyl(g, -9.5, 15, -14.5, -9.5, 2.4, KNOB)
        vcyl(g, -9.5, -12, 12.6, 17.4, 2.4, KNOB)
    g.use("frame")
    # ---- magazine (def_mag): .338 five-round box, exactly as mag_profile describes it
    mag_bones(g, 4, 6)
    MG = "#222428"
    mg = g.box(-2, 8, -2, 8, -3.5, 3.5, MG)
    for side in ("right", "left"):
        for u in (0, 3, 6):
            mark(mg, side, -1, 7, u, u + 1, shade(MG, 1.5))  # pressed ribs
    g.box(-3, 9, -4, -2, -4.5, 4.5, shade(MG, 0.85))  # floor plate
    if hi():
        g.box(7, 9, -3.5, -2, -4, 4, shade(MG, 1.1), 1)  # its lip
        mag_lips(g, -2, 8, 8, 7, MG, round_len=9, r=1.4)
    g.mag_profile = dict(f0=-2, top=8, width=7, segs=[(0, 10)], color=MG, kind="sniper")
    # ---- factory scope (def_optic): 5-25x56 on two rings
    g.mount("optic", 4, 22.5, length=36)
    g.use("def_optic")
    SC = "#26282c"
    for f0 in (-6, 14):
        g.box(f0, f0 + 4, 22.5, 26.5, -3, 3, ANOD, 2)  # ring base and clamp
        stud(g, f0 + 2, 23.8, 3, "left", shade(SILVER, 0.7), d=1.6)
        g.rod(f0 + 0.5, f0 + 3.5, 29, 0, 3.7, ANOD)  # ring
        if hi():
            g.box(f0 + 0.5, f0 + 3.5, 28.5, 29.5, -4, 4, shade(ANOD, 1.2), 1, inflate=-0.1)  # cap split and screws
    tube = g.rod(-11, 24, 29, 0, 3, SC)
    for c in tube:
        for side in ("left",):
            roll_mark(c, side, -9, 0, 28, shade(SILVER, 0.6))
    for c in g.bevel(1, 9, 25.5, 32.5, -3.5, 3.5, SC, 1.5):  # turret saddle
        pass
    el = vcyl(g, 5, 0, 32, 35, 2.4, SC)  # elevation turret, zero ring, cap
    vcyl(g, 5, 0, 32.5, 33.5, 2.7, shade(SC, 1.3))
    vcyl(g, 5, 0, 35, 36, 2.0, shade(SC, 0.8))
    for c in el:
        for face in (c.right, c.left):
            for y in range(0, face.h, 2):
                face.px(face.w - 1, y, WHITE)  # the click scale
    scyl(g, 5, 29, -7, -3.5, 2.2, SC)  # windage
    scyl(g, 5, 29, -8, -7, 1.8, shade(SC, 0.8))
    scyl(g, 5, 29, 3.5, 7, 2.2, SC)  # parallax
    illum = scyl(g, 5, 29, 7, 9, 1.6, shade(SC, 1.1))  # illumination
    for c in illum:
        c.left.px(0, 0, RED)
    cone(g, -14, -11, 29, 0, 3.7, 3.0, 1, SC, n=12)
    for c in g.rod(-17, -14, 29, 0, 3.7, SC):  # magnification ring
        ribs(c, ("right", "left", "up", "down"), 2, shade(SC, 1.4))
    g.box(-16, -15, 32, 34, -0.5, 0.5, SC, 1)  # its throw lever
    g.rod(-24, -17, 29, 0, 4, SC)  # ocular
    for c in g.rod(-24, -22, 29, 0, 4.1, SC):  # dioptre ring
        ribs(c, ("right", "left", "up", "down"), 2, shade(SC, 1.4))
    pipe(g, -27, -24, 29, 0, 3.8, 1, RUBBER, n=12)  # eyecup
    g.lens(-26, 26.5, 31.5, -2.5, 2.5, "#7fd0f5")
    cone(g, 24, 28, 29, 0, 3.0, 5.0, 1, SC)  # objective bell
    bell = pipe(g, 28, 42, 29, 0, 5, 1, SC)
    g.lens(38, 26, 32, -3, 3)
    # ---- muzzle brake (def_muzzle): two chambers with big side ports
    g.mount("muzzle", 96, 15, bore=2.8)
    g.use("def_muzzle")
    BR = "#2b2d31"
    g.rod(96, 98, 15, 0, 3.4, BR)
    for f0 in (98, 101):
        pipe(g, f0, f0 + 2, 15, 0, 3.4, 1, BR, n=12, keep=lambda a: not (50 < a < 130 or 230 < a < 310))
        g.rod(f0, f0 + 2, 15, 0, 1.4, DARK)  # the blast seen through the port
    g.rod(100, 101, 15, 0, 3.4, BR)
    g.rod(103, 104, 15, 0, 3.4, BR)
    g.box(103.4, 104.4, 13.5, 16.5, -1.5, 1.5, DARK, 0, inflate=-0.1)  # bore
    # ---- bipod (def_underbarrel): yoke on the fore-end, legs folded forward under the barrel
    g.mount("underbarrel", 42, 4)
    g.use("def_underbarrel")
    g.box(42, 48, 1.5, 4, -3.5, 3.5, ANOD, 2)
    g.box(43, 47, 0.5, 1.5, -2, 2, ANOD, 1)
    for s in (-2.5, 2.5):
        scyl(g, 46, 2.5, s - 1, s + 1, 1.3, ANOD)  # leg hinge
        g.rod(46, 64, 2.5, s, 1.0, ANOD)  # upper leg
        g.rod(64, 72, 2.5, s, 0.7, shade(SILVER, 0.85))  # extension
        g.box(63.5, 65, 1.5, 3.5, s - 1, s + 1, ANOD, 1)  # leg lock
        g.box(72, 74, 1.2, 3.8, s - 1.3, s + 1.3, RUBBER, 1)  # foot
    g.mount("side", 36, 10, 6.5, length=10, default=False)
    # ---- folding thumbhole stock (def_stock)
    g.mount("stock", -18, 12)
    g.use("def_stock")
    g.box(-37, -18, 8, 12, -4, 4, G)  # top bar under the bolt's travel
    g.box(-22, -18, 2, 9, -4, 4, G)  # hinge block behind the grip
    if hi():
        for u0 in (3, 6.5, 10):
            vcyl(g, -20, 4.7, u0, u0 + 2, 0.8, ANOD)  # hinge knuckles
        g.box(-21, -19, 2, 12.5, 4, 4.5, ANOD, 1)
    lean = -math.degrees(math.atan2(4.5, 17.5))
    g.box(-38, -18.5, -5, -1, -3.5, 3.5, G, tilt=lean, pivot=(-38, -5))  # bottom bar up to the grip's foot
    g.box(-41, -35, 0, 8, -4, 4, G, tilt=-35, pivot=(-37, 0))  # the thumbhole's rounded back
    butt = g.bevel(-58, -37, -5, 14, -4.5, 4.5, G, 1.5)
    for c in butt[:2]:
        for side in ("right", "left"):
            mark(c, side, -54, -40, 4, 5, shade(G, 0.75))  # moulded line
    if hi():
        for f in (-54, -41):
            vcyl(g, f, 0, 14, 15, 0.6, SILVER)  # cheek piece posts
        g.box(-51, -45, 14.5, 15.5, -1, 1, ANOD, 1)  # its clamp knob
        qd_cup(g, -52, 0, -4.5, "right", ANOD)
        qd_cup(g, -52, 0, 4.5, "left", ANOD)
    g.bevel(-56, -38, 15, 19, -3.5, 3.5, G, 1)  # adjustable cheek piece
    for i, f0 in enumerate((-59, -60)):  # spacers
        g.box(f0, f0 + 1, -5, 14, -4.25, 4.25, ANOD if i == 0 else shade(G, 0.8), 1)
    pad = g.bevel(-62, -60, -6, 15, -4.5, 4.5, RUBBER, 1)
    for c in pad[:2]:
        for x in range(1, c.bottom.w, 2):
            c.bottom.vline(x, shade(RUBBER, 0.6))
    # monopod: a knurled wheel and a retracted spike in the butt's foot
    vcyl(g, -52, 0, -9, -5, 0.8, SILVER)
    wheel = vcyl(g, -52, 0, -7.5, -6, 2.2, ANOD)
    for c in wheel:
        for face in (c.right, c.left):
            for y in range(0, face.h, 2):
                face.hline(y, shade(ANOD, 1.5))
    g.box(-54, -50, -10, -9, -1.5, 1.5, RUBBER, 1)
    g.use("frame")
    return g


# =========================================================================== launchers

def carl_gustaf():
    """Carl Gustaf M4 84mm recoilless rifle: a banded smooth tube open at both ends, the hinged venturi with its
    locking lever, shoulder rest, cheek pad, carry handle, trigger group with safety, fore grip, side sight."""
    g = gun("carl_gustaf", "launcher", "launcher_rear")
    U = 22
    TUBE = CARBON
    pipe(g, -40, 50, U, 0, 9, 2, TUBE, n=16)
    if hi():
        for f0 in (-22, 14, 38):  # reinforcing bands
            pipe(g, f0, f0 + 2, U, 0, 9.4, 1, shade(TUBE, 1.3), n=16)
    pipe(g, 46, 52, U, 0, 10, 2, BLACK, n=16)  # muzzle ring
    pipe(g, -42, -38, U, 0, 9.8, 2, STEEL, n=16)  # breech collar
    # ---- grips, trigger group
    g.pistol_grip(-12, -6, 13, 14, 6, POLY, angle=8)
    g.trigger(-12, 13)
    g.bevel(-16, 4, 9, 14, -3, 3, BLACK, 1)  # firing mechanism housing under the tube
    if hi():
        g.box(-9, -5, 11, 13, 2.5, 4.5, STEEL, 1, tilt=-12)  # safety lever on the left
        g.box(-4, 0, 10, 12, 2.5, 3.5, DARK, 1)
        g.pin(-1, 11, 3, "left")
    g.bevel(8, 14, 0, 11, -2.5, 2.5, POLY, 1)  # fore grip
    g.box(7, 15, 8, 12, -3, 3, BLACK)  # its clamp
    g.box(7.5, 14.5, -1.5, 0, -3, 3, RUBBER, 1)  # grip base
    # ---- shoulder rest and cheek pad
    pc = g.bevel(-34, -14, 8, 13, -5, 5, RUBBER, 1.5)
    g.box(-26, -22, 12, 15, -1.5, 1.5, BLACK, 1)  # rest bracket
    g.box(-18, -16, 11, 14, -1.5, 1.5, BLACK, 1)
    if hi():
        for c in pc[:2]:
            ribs(c, ("right", "left"), 3, shade(RUBBER, 1.5))
    g.bevel(-34, -16, 31, 34, -3.5, 3.5, RUBBER, 1)  # cheek pad
    g.box(-30, -20, 30, 31, -2, 2, BLACK, 1)
    # ---- carry handle
    g.box(-6, -3, 30, 32, -1.5, 1.5, BLACK)
    g.box(11, 14, 30, 32, -1.5, 1.5, BLACK)
    hb = g.bevel(-6, 14, 32, 35, -2, 2, BLACK, 1)
    if hi():
        for c in hb[:2]:
            ribs(c, ("up",), 2, shade(BLACK, 0.7))
        g.box(-4, 12, 31, 32, -1, 1, DARK, 1)
        sling_swivel(g, 30, 13, 0, True)
        sling_swivel(g, -36, 31, 0, False)
    # ---- the venturi: a hollow hourglass that swings open on a hinge on the left
    g.part("breech", -40, U, 9)
    cone(g, -48, -40, U, 0, 6.0, 9.4, 1, TUBE, n=12, bone="breech")
    cone(g, -60, -48, U, 0, 10.5, 6.0, 1, TUBE, n=12, bone="breech")
    g.rod(-47, -46, U, 0, 7.0, STEEL, bone="breech")  # throat ring
    g.rod(-61, -59.5, U, 0, 10.8, BLACK, bone="breech")  # nozzle lip
    g.box(-44, -36, 20, 24, -10.5, -8.5, STEEL, 1, bone="breech")  # locking lever on the right
    g.box(-37, -34, 17, 24, -11, -9, BLACK, 1, bone="breech", tilt=0)
    g.box(-44, -40, 19, 25, 8.5, 11.5, STEEL, 1, bone="breech")  # hinge knuckle on the left
    g.pin(-42, 22, 9, "left")
    # ---- the round, loaded in the tube
    g.part("rocket", -24, U)
    g.rod(-38, -37, U, 0, 5.6, BRASS, bone="rocket")  # case base
    g.rod(-37, -24, U, 0, 5.4, "#8a7a3a", bone="rocket")  # cartridge case
    g.rod(-24, -22, U, 0, 6.2, COPPER, bone="rocket")  # driving band
    g.rod(-22, -10, U, 0, 6.0, "#6a7040", bone="rocket")  # HEAT warhead
    g.ring(-18, -17, U, 0, 6.2, "#d8c040", bone="rocket")
    mag_bones(g, -24, U)
    g.muzzle = (52.0, float(U))
    # ---- the sight: a bracket and a short telescope on the left
    g.mount("optic", 4, 30, 12, length=8)
    g.use("def_optic")
    g.box(-4, 10, 28, 30, 6, 10, DARK)
    g.box(-1, 8, 26, 28, 8, 12, BLACK)
    g.rod(-6, 14, 32, 12, 2.6, BLACK)
    g.rod(10, 16, 32, 12, 3.4, BLACK)  # objective bell
    g.rod(-10, -6, 32, 12, 3.2, RUBBER)  # eye cup
    g.lens(16, 29, 35, 9, 15)
    g.lens(-11, 30, 34, 10, 14, "#7fd0f5")
    g.box(0, 4, 33, 36, 11, 13, STEEL, 1)  # elevation turret
    g.use("frame")
    return g


def rpg7():
    """RPG-7 with a PG-7V: tube with the flared nozzle and the muzzle flange, wooden heat shield in its two halves
    clamped by bands, trigger group with hammer and safety, pistol and fore grip, folding sights, the PGO-7
    optic on its side bracket, and the PG-7V round (sustainer, tapered shoulder, warhead, ogive, fuse probe)."""
    g = gun("rpg7", "launcher", "launcher_front")
    U = 20
    pipe(g, -40, 36, U, 0, 4, 1, BLUED, n=12)  # tube
    cone(g, -56, -40, U, 0, 7.0, 4.2, 1, BLUED, n=12)  # rear nozzle
    g.rod(-57, -55.5, U, 0, 7.3, STEEL)
    g.rod(-42, -40, U, 0, 4.7, STEEL)
    g.rod(30, 34, U, 0, 4.6, BLUED)  # muzzle flange
    pipe(g, 34, 36, U, 0, 5, 1, BLUED, n=12)
    # heat shield: two wooden halves with a split and three steel bands
    for i, c in enumerate(g.rod(-14, 14, U, 0, 6, WOOD)):
        grain(c, WOOD, i + 3, flat=False)
    for f0 in (-14, -2, 12):
        g.ring(f0, f0 + 2, U, 0, 6.3, STEEL)
    g.box(-12, 12, U - 0.5, U + 0.5, -6.2, 6.2, WOOD_D, 1)  # the seam between the halves
    for f in (-8, 6):
        g.pin(f, U + 1, 6, "left")
        g.pin(f, U + 1, -6, "right")
    # ---- trigger group
    g.pistol_grip(-4, 2, 15, 14, 6, WOOD, angle=10, stipple=False)
    g.bevel(-9, 6, 13, 19, -3, 3, BLUED, 1)  # mechanism housing
    g.trigger(-4, 15)
    g.box(-2, 1, 12, 14, 2.5, 4.5, DARK, 1)  # safety on the left
    g.box(-8, -5, 17, 19, 3, 5.5, STEEL, 1, tilt=20)  # cocking lever
    g.pin(2, 16, 3, "left")
    g.pistol_grip(14, 20, 15, 12, 6, WOOD, angle=10, stipple=False)
    g.box(11, 21, 14, 16, -3, 3, BLUED, 1)  # fore grip clamp
    # ---- iron sights, folded forward
    g.box(26, 28, 24, 30, -1, 1, BLUED)
    g.box(25, 29, 29, 30.5, -1.6, 1.6, BLUED)
    g.box(25.5, 26, 24, 30, -1.6, -1, BLUED)
    g.box(25.5, 26, 24, 30, 1, 1.6, BLUED)
    g.box(2, 4, 24, 29, -1.5, 1.5, BLUED)
    g.box(2, 4, 27, 28, -0.5, 0.5, DARK)
    sling_swivel(g, 30, 14, 0, True)
    sling_swivel(g, -30, 14, 0, True)
    # ---- the PG-7V rocket
    g.part("rocket", 40, U)
    G1, G2 = "#3a4228", "#4a5530"
    g.rod(36, 44, U, 0, 2.5, G1, bone="rocket")  # sustainer neck
    g.rod(44, 46, U, 0, 4.2, G1, bone="rocket")  # tapering shoulder
    g.rod(46, 48, U, 0, 5.2, G2, bone="rocket")
    g.rod(48, 50, U, 0, 6.0, G2, bone="rocket")
    g.rod(50, 52, U, 0, 6.8, G2, bone="rocket")
    g.rod(52, 60, U, 0, 7.0, G2, bone="rocket")  # warhead body
    g.ring(52, 53, U, 0, 7.2, BRASS, bone="rocket")
    g.ring(57, 58, U, 0, 7.2, "#d8c040", bone="rocket")
    g.rod(60, 63, U, 0, 6.2, G2, bone="rocket")  # ogive
    g.rod(63, 66, U, 0, 5.0, G2, bone="rocket")
    g.rod(66, 69, U, 0, 3.8, G2, bone="rocket")
    g.rod(69, 71, U, 0, 2.6, G1, bone="rocket")
    g.rod(71, 74, U, 0, 1.2, DARK, bone="rocket")  # fuse probe
    mag_bones(g, 40, U)
    g.muzzle = (74.0, float(U))
    # ---- the PGO-7 optic on its bracket on the left
    g.mount("optic", 2, 28, 8, length=8)
    g.use("def_optic")
    g.box(-4, 8, 22, 26, 4, 8, BLUED)
    g.box(-2, 6, 26, 28, 6, 10, DARK)
    g.rod(-8, 10, 29, 10.5, 2.6, BLACK)
    g.rod(10, 14, 29, 10.5, 3.3, BLACK)
    g.rod(-16, -8, 29, 10.5, 2.5, RUBBER)
    g.box(0, 3, 31.5, 34, 9.5, 11.5, STEEL, 1)
    g.lens(14, 26, 32, 7, 14)
    g.lens(-17, 27, 31, 9, 12, "#7fd0f5")
    g.use("frame")
    return g
