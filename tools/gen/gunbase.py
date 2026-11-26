"""Shared pieces for the gun files (guns_a.py, guns_b.py, guns_c.py): materials and helpers."""
from __future__ import annotations

from kit import (BLACK, BRASS, CHROME, COPPER, DARK, GLASS, GUNMETAL, Held, OD, OD_D, POLY, RED, RUBBER, SILVER,
                 STEEL, TAN, TAN_D, WHITE, WOOD, WOOD_D, mark, ribs, shade, slots)

BLUED = "#2f3238"       # blued steel
PARK = "#454a40"        # parkerised green-grey
BAKELITE = "#8a4a22"    # AK magazine
WALNUT = "#6e4226"
WALNUT_L = "#8b5a33"
AWM_GREEN = "#55613f"
CARBON = "#3a3f36"


def gun(key, hold, anim):
    g = Held(key, hold)
    g.anim = anim
    g.mag_profile = None
    return g


def mag_bones(g, f, u):
    g.part("mag", f, u)
    g.part("def_mag", f, u, parent="mag")
    g.use("def_mag")


def curved_mag(g, f0, width, top, segs, color, rib=2, base=True):
    """A magazine of stacked segments stepping forward as it goes down: segs = [(df, height), ...]."""
    u = top
    s = width / 2
    out = []
    for df, h in segs:
        c = g.box(f0 + df, f0 + df + 10, u - h, u, -s, s, color)
        ribs(c, ("right", "left"), rib, shade(color, 0.8))
        out.append(c)
        u -= h
    if base:
        df = segs[-1][0]
        g.box(f0 + df - 1, f0 + df + 11, u - 2, u, -s - 1, s + 1, shade(color, 0.75))
    return out


# ---------------------------------------------------------------- shared detail parts

def cartridge(g, f, u, s=0.0, length=8, r=1.2, case=BRASS, tip=COPPER, bone=None):
    """A round lying along the barrel axis, its base at f: brass case, rim groove, copper bullet."""
    g.rod(f, f + 1, u, s, r * 0.9, shade(case, 0.8), bone=bone)  # extractor groove
    g.rod(f + 1, f + length * 0.62, u, s, r, case, bone=bone)
    g.rod(f + length * 0.62, f + length * 0.85, u, s, r * 0.75, tip, bone=bone)
    g.rod(f + length * 0.85, f + length, u, s, max(0.4, r * 0.4), tip, bone=bone)


def mag_lips(g, f0, f1, top, width, color, round_len=8, r=1.2):
    """The feed lips at the top of a box magazine with the top round showing between them."""
    s = width / 2
    g.box(f0, f1, top, top + 1, -s, -s + 1, shade(color, 0.85), 2)
    g.box(f0, f1, top, top + 1, s - 1, s, shade(color, 0.85), 2)
    cartridge(g, f0 + 0.5, top + r * 0.6, 0, min(round_len, f1 - f0 - 1), r)


def sling_swivel(g, f, u, s=0.0, down=True, color=None):
    """A sling loop: two posts and a bar."""
    col = color or STEEL
    k = -1 if down else 1
    u0, u1 = (u - 3, u) if down else (u, u + 3)
    g.box(f - 2, f - 1, u0, u1, s - 0.5, s + 0.5, col, 1)
    g.box(f + 1, f + 2, u0, u1, s - 0.5, s + 0.5, col, 1)
    ub = u0 if down else u1 - 1
    g.box(f - 2, f + 2, ub, ub + 1, s - 0.5, s + 0.5, col, 1)
    return k


def qd_cup(g, f, u, s, side, color=BLACK):
    """A quick-detach sling cup on a side: a round boss with a dark hole."""
    d = 1 if side == "left" else -1
    s0, s1 = sorted((s, s + 1.5 * d))
    c = g.box(f - 1.5, f + 1.5, u - 1.5, u + 1.5, s0, s1, color, 2)
    mark(c, side, f - 0.5, f + 0.5, u - 0.5, u + 0.5, DARK)
    return c


def roll_mark(c, side, f0, f1, u0, color=None, text_len=None):
    """Engraved markings (a row of short strokes like letters) on a side."""
    col = color or shade(SILVER, 0.75)
    f = f0
    i = 0
    while f + 1 <= f1:
        h = 1 if i % 3 else 2
        mark(c, side, f, f + 1, u0, u0 + h, col)
        f += 1.5 if i % 4 != 3 else 2.5
        i += 1


def screw_head(g, f, u, s, side, color=None):
    """A slotted screw head standing proud of a side."""
    c = g.pin(f, u, s, side, color or shade(SILVER, 0.8))
    return c


def knurl(c, side, f0, f1, u0, u1, color):
    """Checkering or knurling: a staggered dot pattern (one texel per unit) over an area of a side."""
    for row, f in enumerate(range(int(f0), int(f1))):
        for u in range(int(u0) + row % 2, int(u1), 2):
            mark(c, side, f, f + 1, u, u + 1, color)
