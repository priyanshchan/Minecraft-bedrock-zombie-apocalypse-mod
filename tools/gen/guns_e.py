"""FN SCAR-H Mk17 (7.62x51mm NATO) and PKM (7.62x54mmR)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, mag_bones, qd_cup, roll_mark, sling_swivel
from guns_b import bore, curve_mag, disc, edge, knob, lines, on_seg, pins, slotted, soften, stitch, stitch_v, stud


def scar_h():
    """FN SCAR-H: monolithic upper with a full-length top rail, free-float handguard with side and bottom
    rails, left reciprocating charging handle, folding adjustable stock, 20-round steel magazine."""
    g = gun("scar_h", "rifle", "ar")
    B = 13.5
    # ------------------------------------------------ upper and lower receiver
    up = g.bevel(-8, 36, 8, 19, -4.5, 4.5, TAN, 1)
    for c in up[:2]:
        mark(c, "right", 6, 18, 11, 16, DARK)  # ejection port
        mark(c, "right", 18, 32, 14, 15, shade(TAN, 0.7))
        mark(c, "left", 8, 34, 14.5, 15.5, DARK)  # charging handle slot
        roll_mark(c, "right", -4, 4, 16.5, shade(TAN, 0.6))
        roll_mark(c, "left", -4, 4, 16.5, shade(TAN, 0.6))
    low = g.box(-6, 22, 2, 9, -4, 4, TAN)
    mark(low, "left", 8, 20, 3, 8, shade(TAN, 0.85))
    g.box(24, 34, 5, 9, -4, 4, shade(TAN, 0.9), 2)
    g.teeth_rail(-8, 66, 19, -3, 3)  # one long top rail, receiver to handguard
    for f, u in ((-5, 10), (30, 10)):
        pins(g, f, u, 4.5, size=0.9)
        pins(g, f + 2, u + 3, 4.5, size=0.9)
    g.box(-12, -8, 9, 19, -4, 4, shade(TAN, 0.8), 2)  # hinge block
    disc(g, -10, 14, -4.6, 4.6, 1.3, STEEL)
    # pistol grip, trigger, guard
    g.pistol_grip(-6, 2, 3, 15, 6, TAN, angle=18)
    g.box(-5, 8, 1, 2, -2.2, 2.2, TAN, 2)
    g.trigger(-2, 1.5)
    g.box(3, 7, 3.5, 5.5, -4.6, -4, STEEL, 1)  # selector, right
    g.box(-1, 5, 7, 9, 4, 4.8, STEEL, 1)
    # folding sights on the rail
    g.box(-4, 2, 22, 24, -2.2, 2.2, BLACK, 2)
    g.box(-4, -2, 24, 27.5, -2, 2, BLACK, 1)
    g.box(-3.5, -2.5, 25, 27, -0.5, 0.5, DARK, 1)  # aperture
    g.box(58, 66, 22, 24, -2, 2, BLACK, 1)
    g.box(61, 63, 24, 29, -0.5, 0.5, BLACK, 1)  # front post
    for s0 in (-2.2, 1.2):
        g.box(60.5, 63.5, 24, 28, s0, s0 + 1, BLACK, 1)
    # ------------------------------------------------ bolt (seen in the ejection port) and charging handle
    g.part("bolt", 9, 13)
    g.box(8, 15, 12.5, 15.5, -4.6, -4, STEEL, 1, bone="bolt")
    g.part("charging_handle", 20, 15, 5)
    g.use("charging_handle")
    g.box(18, 24, 14, 16.5, 4.5, 6.5, BLACK, 2)
    g.box(19, 25, 13.5, 17, 6.5, 8, BLACK, 2)  # the T-handle
    for f in (20, 22, 24):
        g.box(f, f + 0.8, 13.5, 17, 7.8, 8.4, shade(BLACK, 1.4), 1)
    g.use("frame")
    # ------------------------------------------------ handguard with side and bottom rails
    hg = g.bevel(34, 70, 8, 19, -3.8, 3.8, TAN, 1.2)
    for c in hg[:2]:
        for side in ("left", "right"):
            for f in range(38, 68, 6):
                mark(c, side, f, f + 3, 16, 17.5, DARK)  # vent slots
                mark(c, side, f, f + 3, 9.5, 11, DARK)
    for sgn in (1, -1):  # side rails (keymod-style teeth)
        for f in range(38, 68, 3):
            s0 = 3.8 if sgn > 0 else -5.4
            g.box(f, f + 2, 12, 15, s0, s0 + 1.6, shade(BLACK, 1.1), 1)
        s0 = 3.4 if sgn > 0 else -4.2
        g.box(38, 68, 12.5, 14.5, s0, s0 + 0.8, shade(BLACK, 0.85), 1)
    g.teeth_rail(40, 66, 8, -2.5, 2.5, down=True)
    g.box(68, 72, 8, 19, -4.4, 4.4, TAN_D)  # handguard end cap
    sling_swivel(g, 54, 5, 0, down=True)
    # ------------------------------------------------ barrel and muzzle
    g.rod(34, 80, B, 0, 2.2, STEEL)
    g.rod(72, 76, B, 0, 3.0, BLACK)  # gas block
    g.muzzle = (90.0, B)
    g.mount("muzzle", 80, B, bore=2.2)
    g.use("def_muzzle")  # SCAR flash hider
    g.rod(80, 82, B, 0, 2.8, BLACK)
    for c in g.rod(82, 89, B, 0, 2.7, BLACK):
        slots(c, ("right", "left", "up"), 83, 89, c.ext[2], c.ext[3], 3, 1.5)
    g.rod(89, 90, B, 0, 2.9, BLACK)
    bore(g, 90, B, 1.4)
    g.use("frame")
    # ------------------------------------------------ magazine
    mag_bones(g, 13, 2)
    g.use("frame")
    g.box(6, 20, 1, 3, -4, 4, TAN, 2)  # mag well
    g.use("def_mag")
    segs = [(0, 8), (0, 6), (1, 6)]
    cm = curve_mag(g, 8, 2, 7, segs, BLACK, overlap=0.4)
    for seg in cm:
        _c, df, ut, h, _a, _p = seg
        for u in (ut - h + 1.5, ut - h + 3.5):
            if u + 1 <= ut - 0.5:
                on_seg(g, seg, 8 + df + 1, 8 + df + 9, u, u + 1, -3.8, 3.8, shade(BLACK, 1.3), 1)
        on_seg(g, seg, 8 + df + 8.5, 8 + df + 9.5, ut - h + 0.5, ut - 0.5, -3.8, 3.8, DARK, 1)
    _c, df, ut, h, _a, _p = cm[-1]
    on_seg(g, cm[-1], 8 + df - 1, 8 + df + 11, ut - h - 1.5, ut - h + 0.5, -4, 4, STEEL)
    on_seg(g, cm[-1], 8 + df + 4, 8 + df + 6, ut - h - 0.5, ut - h + 0.5, -4.4, 4.4, DARK, 1)
    g.mag_profile = dict(f0=8, top=2, width=7, segs=[(0, 8), (0, 6), (1, 6)], color=BLACK, kind="rifle")
    # ------------------------------------------------ mounts
    g.use("frame")
    g.mount("optic", 8, 22, length=36)
    g.mount("underbarrel", 38, 8, length=14, default=False)
    g.mount("side", 40, 13.5, 4.5, length=10, default=False)
    # ------------------------------------------------ folding adjustable stock
    g.mount("stock", -8, 13)
    g.use("def_stock")
    top = g.bevel(-44, -12, 10, 19, -3.7, 3.7, TAN, 1)
    for c in top[:2]:
        for side in ("left", "right"):
            lines(c, side, -42, -14, 12, 17, 2, shade(TAN, 0.85))
    g.box(-44, -12, 3, 8, -3.5, 3.5, TAN, tilt=0)
    for f0, f1 in ((-44, -38), (-27, -22), (-16, -12)):
        g.box(f0, f1, 7.5, 10.5, -3.5, 3.5, TAN, 2)
    g.box(-36, -18, 19, 21, -3, 3, TAN_D, 2)  # cheek riser
    for f in range(-34, -20, 3):
        g.box(f, f + 1, 21, 21.5, -2.4, 2.4, shade(TAN_D, 0.7), 1)
    g.box(-14, -12, 5, 12, 3.7, 4.5, STEEL, 1)  # fold latch
    pins(g, -30, 14.5, 3.7, size=1.0)  # adjustment pin
    pins(g, -30, 5.5, 3.5, size=1.0)
    butt = g.bevel(-49, -44, 1, 21, -4, 4, RUBBER, 1)
    for c in butt[:2]:
        lines(c, "left", -49, -44, 2, 20, 2, shade(RUBBER, 1.5))
        lines(c, "right", -49, -44, 2, 20, 2, shade(RUBBER, 1.5))
    sling_swivel(g, -30, 3, 0, down=True)
    g.use("frame")
    return g


def pkm():
    """PKM: stamped receiver with its embossed channels, hinged top cover with the tangent rear sight, fluted
    barrel with the carry handle, hooded front sight, slotted flash hider, folded bipod, skeleton wooden stock,
    and the 100-round box on the right feeding a belt up into the receiver."""
    g = gun("pkm", "rifle", "lmg")
    B = 14.0
    # ------------------------------------------------ receiver
    rec = g.bevel(-12, 34, 4, 20, -5, 5, BLUED, 1.5)
    for c in rec[:2]:
        mark(c, "right", 3, 17, 12, 18, DARK)  # belt feed opening
        mark(c, "right", 18, 32, 5, 7, DARK)  # ejection port
        mark(c, "left", -10, 30, 11, 12, shade(BLUED, 0.65))  # embossed channels
        mark(c, "right", -10, 2, 11, 12, shade(BLUED, 0.65))
        mark(c, "left", -10, 30, 7, 8, shade(BLUED, 0.65))
        mark(c, "right", 18, 30, 11, 12, shade(BLUED, 0.65))
        roll_mark(c, "left", -8, 2, 15, shade(BLUED, 1.6))
    for side_s, side in ((5, "left"), (-5, "right")):
        for f in range(-9, 34, 6):  # rivets
            stud(g, f, 5.8, side_s, side, shade(BLUED, 1.6), 0.9)
            stud(g, f, 18.4, side_s, side, shade(BLUED, 1.6), 0.9)
    g.box(30, 36, 6, 19, -4.8, 4.8, shade(BLUED, 0.85))  # front trunnion
    g.box(-14, -12, 6, 19, -4, 4, STEEL, 1)  # rear plate
    # trigger group
    g.pistol_grip(-12, -4, 5, 16, 6, WOOD, angle=14)
    g.box(-5, 2, 0, 1, -1, 1, DARK, 1)
    g.box(1, 2, 0, 4, -1, 1, DARK, 1)
    g.box(-2, 0, 0, 4, -0.5, 0.5, SILVER, 1)
    g.box(-12, 2, 3, 4.5, -2, 2, BLUED, 1)
    # charging handle on the right
    g.part("charging_handle", 20, 12, -6)
    g.box(16, 24, 11, 14, -8, -5, BLUED, bone="charging_handle")
    g.box(22, 26, 10.5, 15, -9.5, -7.5, BLUED, 1, bone="charging_handle")
    # ------------------------------------------------ top cover with tangent sight
    g.part("cover", -12, 21)
    g.use("cover")
    cov = g.bevel(-12, 26, 20, 24, -4.5, 4.5, BLUED, 1)
    for f in range(-8, 24, 4):
        mark(cov[1], "up", f, f + 1, 0, 0, shade(BLUED, 0.7), -3.5, 3.5)
    g.box(-12, 26, 24, 25, -2, 2, BLUED, 1)
    g.box(-12, -4, 24, 26, -3, 3, BLUED)  # sight base
    g.box(-11, -7, 26, 31, -1.8, 1.8, BLUED, 1, tilt=-12, pivot=(-9, 26))  # tangent leaf
    g.box(-10, -8, 30, 31, -0.4, 0.4, DARK, 1)
    for f in (-10, -7):
        g.box(f, f + 1, 26, 26.8, -2.4, 2.4, shade(BLUED, 1.4), 1)
    disc(g, -7, 25.5, 3, 4.2, 1.2, GUNMETAL)  # windage knob
    g.box(24, 30, 20.5, 22.5, -3, 3, GUNMETAL, 1)  # cover latch
    g.box(26, 28, 19, 21, -4.6, 4.6, STEEL, 1)
    g.use("frame")
    # feed tray (visible when the cover is open)
    g.box(0, 22, 19.5, 20.5, -4, 4, STEEL, 1)
    g.box(2, 4, 20.5, 21.5, -4, 4, SILVER, 1)
    # ------------------------------------------------ barrel, gas system, carry handle, sights
    g.rod(34, 104, B, 0, 2.4, BLUED)
    for c in g.rod(38, 80, B, 0, 3.2, BLUED):  # fluted jacket
        for side in ("right", "left", "up", "down"):
            lines(c, side, 38, 80, c.ext[2], c.ext[3], 2, shade(BLUED, 0.6))
    g.ring(36, 38, B, 0, 3.6, STEEL)
    g.ring(80, 82, B, 0, 3.6, STEEL)
    g.rod(36, 86, 9, 0, 1.8, BLUED)  # gas tube under the barrel
    g.box(34, 40, 6, 13, -2.5, 2.5, BLUED)
    g.rod(84, 92, 9.5, 0, 2.2, GUNMETAL)  # regulator
    g.box(82, 92, 8, 14, -2.4, 2.4, BLUED)
    g.box(86, 90, 9, 11, 2.4, 3.6, STEEL, 1)
    for f in (58, 74):  # carry handle clamps and loop
        g.rod(f, f + 3, B, 0, 3.8, STEEL)
        g.box(f + 0.5, f + 2.5, 16, 25, -1.2, 1.2, STEEL, 1)
    g.box(57, 78, 24, 26.5, -1.7, 1.7, BLUED, 2)
    for f in range(59, 76, 3):
        g.box(f, f + 1, 24, 26.8, -2, 2, shade(BLUED, 1.3), 1)
    g.box(94, 99, 9, 18, -2.8, 2.8, BLUED)  # front sight base
    g.rod(94, 99, B, 0, 3.2, BLUED)
    g.box(95.5, 97.5, 17.5, 22, -0.5, 0.5, DARK, 1)
    for s0 in (-3, 2):
        g.box(94.5, 98.5, 17.5, 22.5, s0, s0 + 1, BLUED, 1)
    g.muzzle = (112.0, B)
    g.mount("muzzle", 104, B, bore=2.4)
    g.use("def_muzzle")
    g.rod(104, 106, B, 0, 3.0, BLUED)
    for c in g.rod(106, 111, B, 0, 2.8, BLUED):
        slots(c, ("right", "left", "up", "down"), 107, 111, c.ext[2], c.ext[3], 2, 1)
    g.rod(111, 112, B, 0, 3.0, BLUED)
    bore(g, 112, B, 1.4)
    g.use("frame")
    # folded bipod: the legs lie forward under the barrel
    g.mount("underbarrel", 80, 8)
    g.use("def_underbarrel")
    g.rod(78, 84, B, 0, 3.8, BLACK)  # collar round the barrel
    g.box(79, 83, 6, 11, -3.6, 3.6, BLACK, 2)
    for ds in (-3.2, 3.2):
        disc(g, 81, 6, ds - 1, ds + 1, 1.2, STEEL)
        g.rod(82, 104, 6, ds, 0.9, STEEL)
        g.box(100, 104, 4.5, 7.5, ds - 1, ds + 1, BLACK, 1)  # foot
    g.box(82, 104, 4.5, 7.5, -3.3, -2.9, BLUED, 1)
    g.use("frame")
    g.mount("optic", 6, 25, -5, length=20, default=False)
    g.mount("side", 44, 14, 5, length=10, default=False)
    # ------------------------------------------------ 100-round box on the right, belt rising into the feed
    mag_bones(g, 14, 4)
    box = g.bevel(2, 26, -18, 4, -9, 5, "#4a5530", 1.5)
    for c in box[:2]:
        for side in ("right", "left"):
            stitch(c, side, 4, 24, -16, shade("#4a5530", 0.6))
            mark(c, side, 6, 22, -12, -6, shade("#4a5530", 1.12))
            roll_mark(c, side, 8, 20, -9, shade("#4a5530", 0.55))
    for f in (6, 13, 20):  # stamped ribs down the right face
        g.box(f, f + 1.5, -15, 2, -9.5, -9, shade("#4a5530", 1.15), 1)
    g.box(1.5, 26.5, 3, 4.5, -9.4, 5.4, "#4a5530", 2)  # lid flange
    for f in (4, 21):  # hinges
        g.box(f, f + 3, 2, 5, -9.8, -9, STEEL, 1)
    g.box(26, 28, -2, 4, -4, 0, STEEL, 1)  # latch
    g.box(26.5, 27.5, -1, 1, -3, -1, DARK, 1)
    g.box(-1, 2, -14, -3, -2, 1, shade("#4a5530", 0.8), 1)  # carry loop
    g.box(2, 26, -19, -17.5, -9.4, 5.4, STEEL, 1)  # base rim
    belt = [(5.2, -6.0), (7.0, -6.4), (8.8, -6.7), (10.6, -6.9), (12.4, -7.0), (14.2, -7.0), (16.0, -6.7), (17.5, -6.0)]
    for u, s in belt:
        cartridge(g, 4.5, u, s, length=9, r=0.85)
        g.box(6.5, 7.5, u - 0.9, u + 0.9, s - 1.1, s + 0.9, STEEL, 1)  # links
        g.box(9.5, 10.5, u - 0.9, u + 0.9, s - 1.1, s + 0.9, STEEL, 1)
    g.mag_profile = dict(f0=2, top=4, width=14, segs=[(0, 22)], color="#4a5530", kind="box")
    # ------------------------------------------------ skeleton wooden stock
    g.use("frame")
    g.mount("stock", -12, 13)
    g.use("def_stock")
    top = g.bevel(-54, -14, 10, 18, -3.6, 3.6, WOOD, 1.2)
    for c in top[:2]:
        for side in ("left", "right"):
            lines(c, side, -53, -15, 11, 17, 2, shade(WOOD, 0.8))
    g.box(-54, -26, 2, 7, -3.4, 3.4, WOOD, 2)  # lower rail
    g.box(-26, -12, 2, 6, -3.4, 3.4, WOOD, 2)
    for f0, f1 in ((-54, -47), (-26, -20)):
        g.box(f0, f1, 6.5, 10.5, -3.4, 3.4, WOOD, 2)
    g.box(-16, -12, 10, 12, -4, 4, STEEL, 1)  # tang
    pad = g.bevel(-58, -54, 0, 19, -4, 4, STEEL, 1)
    for c in pad[:2]:
        lines(c, "left", -58, -54, 1, 18, 2, shade(STEEL, 1.3))
    g.box(-58.5, -57.5, 15, 18, -2, 2, STEEL, 1)
    sling_swivel(g, -48, 2, 0, down=True)
    g.use("frame")
    return g
