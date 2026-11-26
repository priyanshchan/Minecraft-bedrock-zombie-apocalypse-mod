"""Every item held in the hand as a 3D model (attachables): the twelve guns (guns.py) with their attachments
(attach.py), the knife, the grenades and the gear. The modelling kit is kit.py; its names are re-exported
here for the other generators.
"""
from __future__ import annotations

import math

from kit import *  # noqa: F401,F403  (Held, GRIP, SCALE, FP_SCALE, SKELETON, materials, mark, ribs, ...)
from kit import FACES, Held, mark, ribs, shade
from kit import BRASS, CHROME, DARK, OD, OD_D, RED, RUBBER, SILVER, STEEL, WHITE  # noqa: F401
import guns as G


# =========================================================================== close quarters

def combat_knife():
    g = Held("combat_knife", "blade")
    h = g.box(-14, 6, -3, 3, -2, 2, RUBBER)
    ribs(h, ("right", "left", "up", "down"), 2, shade(RUBBER, 1.6))
    g.box(-17, -14, -3.5, 3.5, -2.5, 2.5, STEEL)  # pommel
    g.box(6, 8, -6, 6, -2.5, 2.5, STEEL)  # guard
    blade = g.box(8, 34, -4, 4, -0.5, 0.5, SILVER, 1)
    for side in ("right", "left"):
        mark(blade, side, 8, 34, -4, -3, CHROME)  # edge
        mark(blade, side, 12, 30, 0, 1, shade(SILVER, 0.75))  # fuller
        for f in range(9, 18, 2):
            mark(blade, side, f, f + 1, 3, 4, DARK)  # spine serrations
    g.box(34, 38, -3, 3, -0.5, 0.5, SILVER, 1)
    g.box(38, 41, -2, 2, -0.5, 0.5, SILVER, 1)
    g.box(41, 43, -1, 1, -0.5, 0.5, CHROME, 0)
    return g


def _ovoid(g, f0, f1, r, color):
    """A body of revolution about the f axis: stacked rods following a rounded profile."""
    n = f1 - f0
    out = []
    for i in range(n):
        t = (i + 0.5) / n
        rr = r * math.sqrt(max(0.0, 1 - (2 * t - 1) ** 2)) ** 0.7
        out += g.rod(f0 + i, f0 + i + 1, 0, 0, max(1.0, rr), color, 2)
    return out


def frag_grenade():
    g = Held("frag_grenade", "grenade")
    for c in _ovoid(g, -10, 12, 8, OD):
        if c.ext[3] - c.ext[2] >= 6:
            for side in ("right", "left"):
                face = getattr(c, FACES[side])
                for x in range(0, face.w, 3):
                    face.vline(x, OD_D)  # segmented body
    g.rod(12, 15, 0, 0, 3, SILVER)  # fuse
    g.box(6, 18, 6, 7, -1.5, 1.5, SILVER, 1)  # spoon
    g.box(-2, 7, 7, 8, -1.5, 1.5, SILVER, 1, tilt=-8)
    g.box(14, 17, -6, -5, -3, 3, CHROME, 0)  # pin ring
    g.box(14, 17, -2, -1, -3, 3, CHROME, 0)
    g.box(14, 17, -6, -1, -3, -2, CHROME, 0)
    g.box(14, 17, -6, -1, 2, 3, CHROME, 0)
    return g


def smoke_grenade():
    g = Held("smoke_grenade", "grenade")
    for c in g.rod(-12, 12, 0, 0, 6, "#7d8288"):
        for side in ("right", "left", "up", "down"):
            mark(c, side, -2, 4, c.ext[2], c.ext[3], WHITE)
            mark(c, side, 8, 10, c.ext[2], c.ext[3], "#5a5e64")
    g.rod(12, 15, 0, 0, 3, SILVER)
    g.box(4, 18, 6, 7, -1.5, 1.5, SILVER, 1)
    g.box(14, 17, -6, -1, -3, -2, CHROME, 0)
    g.box(14, 17, -6, -1, 2, 3, CHROME, 0)
    g.box(14, 17, -6, -5, -3, 3, CHROME, 0)
    return g


# =========================================================================== gear (carried, not aimed)

def medkit():
    g = Held("medkit", "gear")
    bag = g.box(-16, 24, -8, 20, -12, 12, "#b02a26")
    for face in (bag.right, bag.left, bag.front):
        cx, cy = face.w // 2, face.h // 2
        face.fill(WHITE, cx - 2, cy - 7, cx + 2, cy + 7)
        face.fill(WHITE, cx - 7, cy - 2, cx + 7, cy + 2)
        face.border("#7e1a17")
    g.box(-8, 16, 20, 23, -2, 2, DARK)  # handle
    g.box(-16, 24, 6, 8, -13, 13, "#2a2a2a", 1)  # zip
    return g


def ammo_box():
    g = Held("ammo_box", "gear")
    can = g.box(-20, 24, -12, 24, -12, 12, OD)
    for side in ("right", "left"):
        mark(can, side, -16, 20, 8, 12, "#d9cf8a")
        mark(can, side, -16, 8, 2, 5, "#d9cf8a")
    g.box(-20, 24, 24, 28, -13, 13, OD_D)  # lid
    g.box(-4, 8, 28, 31, -2, 2, DARK)  # handle
    g.box(20, 24, 12, 24, -14, 14, DARK)  # latch
    return g


def repair_tool():
    g = Held("repair_tool", "pistol")
    g.pistol_grip(-6, 2, 10, 14, 6, "#3a3a3e", angle=12)
    g.rod(-24, 24, 22, 0, 9, RED)
    g.rod(-26, -24, 22, 0, 8, SILVER)
    g.rod(24, 34, 22, 0, 4, BRASS)
    g.rod(34, 66, 22, 0, 2, SILVER)
    g.rod(64, 72, 22, 0, 3, DARK)
    g.box(-4, 4, 31, 35, -6, 6, BRASS, 1)
    g.muzzle = (72.0, 22.0)
    return g


def binoculars():
    g = Held("binoculars", "gear")
    for s in (-10, 10):
        g.rod(-8, 24, 14, s, 7, "#3b4030")
        g.lens(24, 9, 19, s - 5, s + 5)
        g.rod(-16, -8, 14, s, 5, RUBBER)
    g.box(0, 18, 11, 17, -4, 4, DARK)
    g.rod(6, 12, 19, 0, 2.5, SILVER)
    return g


def field_radio():
    g = Held("field_radio", "gear")
    body = g.box(-14, 30, -8, 8, -9, 9, "#3b4030")
    mark(body, "up", 14, 26, 0, 0, "#7fd08a", -6, 6)
    for f in range(-10, 10, 4):
        for s in range(-6, 6, 4):
            mark(body, "up", f, f + 2, 0, 0, DARK, s, s + 2)
    g.rod(30, 36, 4, -5, 2, DARK)  # knob
    g.rod(30, 80, 0, 5, 1.5, RUBBER)  # antenna
    g.box(-18, -14, -9, 9, -11, 11, DARK)
    return g




GUNS = list(G.GUNS)
GEAR = {
    "combat_knife": combat_knife, "frag_grenade": frag_grenade, "smoke_grenade": smoke_grenade, "medkit": medkit,
    "ammo_box": ammo_box, "repair_tool": repair_tool, "binoculars": binoculars, "field_radio": field_radio,
}


def build_gun(key, with_attachments=True):
    """A gun model; with its attachments (hidden until fitted) unless asked for the bare gun."""
    g = G.GUNS[key]()
    if with_attachments:
        import attach
        attach.fit_all(g)
    return g.finish()


def build_all(bare=False):
    out = {key: build_gun(key, not bare) for key in GUNS}
    out.update({key: fn().finish() for key, fn in GEAR.items()})
    return out


ALL = {**G.GUNS, **GEAR}
