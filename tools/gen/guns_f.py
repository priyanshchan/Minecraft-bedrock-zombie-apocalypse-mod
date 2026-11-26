"""Barrett M82A1 (.50 BMG)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import curved_mag, gun, mag_bones, cartridge, sling_swivel, qd_cup, roll_mark, knurl
from kit import LOW, mark, ribs

PAD_R = "#26272a"
BBL = "#2b2d31"
SLV = "#3a3e36"


def _holes(boxes, color=DARK, step=3):
    """Round perforations on a rod's facets, staggered rows."""
    for k, c in enumerate(boxes):
        for face in (c.front, c.back, c.right, c.left):
            for y in range(1, face.h - 1, step):
                for x in ((face.w // 2,) if (y // step) % 2 else (face.w // 2 - 2, face.w // 2 + 2)):
                    if 0 <= x < face.w:
                        face.px(x, y, color)


def barrett():
    """Barrett M82A1: big upper and lower receivers, long top rail with carry handle, perforated barrel
    sleeve over a fluted barrel, double-chamber arrowhead muzzle brake, folding bipod, stock with recoil pad
    and monopod, 10-round box magazine, right-hand charging handle."""
    g = gun("barrett", "rifle", "ar")
    A = 15  # barrel axis height
    hi = not LOW[0]
    # ---- upper receiver with the ejection port and cocking slot on the right
    up = g.bevel(-26, 46, 10, 21, -5, 5, PARK, 1.5)
    core = up[0]
    mark(core, "right", 8, 30, 15, 16.5, DARK)  # cocking slot
    mark(core, "right", 24, 40, 12.5, 18.5, DARK)  # ejection port
    mark(core, "right", 24, 40, 18, 18.5, shade(PARK, 1.4))
    mark(core, "left", -20, -6, 12, 13, shade(PARK, 0.6))
    if hi:
        roll_mark(core, "left", -18, 6, 17, shade(SILVER, 0.7))
        for f in (-22, 6, 42):  # takedown and cross pins
            g.pin(f, 12, 5, "left")
            g.pin(f, 12, -5, "right")
        g.box(-28, -26, 11, 20, -4, 4, BLACK, 2)  # rear cap
        g.box(-29, -28, 13, 18, -2, 2, DARK, 1)
        g.box(44, 48, 9.5, 21.5, -5.5, 5.5, BLACK, 2)  # front block where the barrel enters
    # ---- lower receiver with the mag well, trigger guard, safety, mag catch
    lo = g.bevel(-26, 34, 5, 10, -4, 4, PARK, 1)
    g.box(8, 28, 4, 5.5, -4.5, 4.5, BLACK, 1)  # mag well lip
    g.box(-5, 9, 0, 1.5, -1.5, 1.5, DARK, 1)  # trigger guard bottom
    g.box(7.5, 9, 0, 5, -1.5, 1.5, DARK, 1)  # guard front
    g.box(0, 1.5, 1, 6, -0.5, 0.5, SILVER, 1, tilt=-18, pivot=(0.75, 6))  # trigger
    g.pistol_grip(-12, -4, 6, 16, 6, POLY, angle=12)
    if hi:
        g.box(-9, -5, 7, 9, 4, 5.5, STEEL, 1)  # safety lever on the left
        g.box(-9, -7, 6, 9, 4, 5.5, STEEL, 1, tilt=-20)
        g.box(9, 12, 5, 9, 4, 5.5, STEEL, 1)  # magazine catch
        g.pin(-1, 8, 4, "left")
        sling_swivel(g, -22, 5, 0, True)
        sling_swivel(g, 40, 10, 0, True)
    # ---- top rail, carry handle
    g.teeth_rail(-24, 46, 21, -3, 3, BLACK)
    g.box(36, 39, 24, 28.5, -1.5, 1.5, BLACK)  # carry handle posts and bar
    g.box(42, 45, 24, 28.5, -1.5, 1.5, BLACK)
    hb = g.bevel(34, 47, 28, 31, -2, 2, BLACK, 1)
    if hi:
        for c in hb[:2]:
            ribs(c, ("up",), 2, shade(BLACK, 0.7))
    # ---- charging handle on the right: a stalk and a knob that rides in the slot
    g.part("charging_handle", 10, 15, -5)
    g.box(9, 12, 15, 17, -8, -5, BLACK, 1, bone="charging_handle")
    g.box(9, 12, 14, 18, -5.5, -4.5, STEEL, 1, bone="charging_handle")
    from guns_c import scyl
    scyl(g, 10.5, 16, -11, -8, 2.2, BLACK, bone="charging_handle")
    # ---- barrel: extension nut, perforated sleeve, rings, fluted barrel
    g.use("frame")
    g.rod(48, 52, A, 0, 5.4, STEEL)
    sleeve = g.rod(52, 96, A, 0, 4.7, SLV)
    if hi:
        _holes(sleeve)
        for f0 in (52, 72, 94):
            g.rod(f0, f0 + 2, A, 0, 5.0, shade(SLV, 1.3))
    g.rod(96, 120, A, 0, 2.7, BBL)
    if hi:
        for ang in (0, 45, 90, 135):  # lands between the flutes
            c = g.box(97, 119, A - 3, A + 3, -0.5, 0.5, BBL, 2, inflate=-0.15, roll=ang if ang else 0.0,
                      pivot=(108, A, 0))
            for face in (c.front, c.back):
                face.vline(face.w // 2, shade(BBL, 1.5))
    g.rod(120, 123, A, 0, 2.4, shade(BBL, 1.2))
    g.muzzle = (134.0, float(A))
    # ---- mounts
    mag_bones(g, 9, 5)
    # ---- magazine: a 10 round box with count windows, ribs and a floor plate
    mg = g.box(9, 27, -10, 5, -3.5, 3.5, BLACK)
    ribs(mg, ("right", "left"), 3, shade(BLACK, 0.75))
    for i in range(5):
        mark(mg, "left", 12 + 3 * i, 13 + 3 * i, 0, 4, DARK)
    mark(mg, "left", 10, 26, -3, -2, shade(SILVER, 0.7))
    g.box(8, 28, -12, -10, -4, 4, STEEL, 2)
    g.box(9, 27, 4, 5.5, -3, -2, shade(BRASS, 0.9), 1)  # top round showing
    g.mag_profile = dict(f0=9, top=5, width=8, segs=[(0, 15)], color=BLACK, kind="sniper")
    g.mount("optic", 4, 24, length=30)
    g.use("def_optic")  # flip-up irons: rear aperture on the rail, front post on the sleeve
    g.box(-20, -17, 24, 28, -1.5, 1.5, BLACK)
    g.box(-19.5, -17.5, 26, 27.5, -0.5, 0.5, DARK)
    g.box(-20, -17, 28, 29, -2, 2, BLACK)
    g.box(80, 82, 19, 25, -0.5, 0.5, BLACK)
    g.box(79, 83, 19, 20, -1.5, 1.5, BLACK)
    g.mount("muzzle", 120, A, bore=3)
    g.use("def_muzzle")
    # ---- double-chamber arrowhead muzzle brake
    g.rod(120, 123, A, 0, 3.8, BLACK)
    g.bevel(123, 134, 10, 20, -3.5, 3.5, BLACK, 1)  # body
    g.box(124, 127, 11, 19, 3.5, 5.5, BLACK, 1)  # first chamber wings
    g.box(124, 127, 11, 19, -5.5, -3.5, BLACK, 1)
    wl = g.box(127, 130, 11, 19, 3.5, 6.5, BLACK, 1)
    wr = g.box(127, 130, 11, 19, -6.5, -3.5, BLACK, 1)
    wl2 = g.box(130, 134, 10, 20, 3.5, 8, BLACK, 1)  # second chamber wings
    wr2 = g.box(130, 134, 10, 20, -8, -3.5, BLACK, 1)
    for c, side in ((wl, "left"), (wr, "right"), (wl2, "left"), (wr2, "right")):
        mark(c, side, c.ext[0] + 1, c.ext[1] - 1, 12, 18, shade(BLACK, 0.55))
    mark(wl2, "left", 131, 133, 11, 19, DARK)
    mark(wr2, "right", 131, 133, 11, 19, DARK)
    g.rod(133, 134.3, A, 0, 2.2, DARK)  # the bore
    g.use("frame")
    # ---- bipod: folded legs lying back under the sleeve
    g.mount("underbarrel", 88, 9)
    g.use("def_underbarrel")
    g.box(84, 92, 7, 10, -4.5, 4.5, STEEL, 1)  # clamp
    g.box(85, 91, 5, 7, -4, 4, BLACK, 1)  # hinge block
    for s0 in (-4.5, 3.0):
        g.box(64, 87, 4.5, 7, s0, s0 + 1.5, BLACK, 1)  # leg tubes
        g.box(66, 80, 3, 4.5, s0 + 0.2, s0 + 1.2, STEEL, 1)  # extension
        g.box(62, 66, 2.5, 8, s0 - 0.3, s0 + 1.8, RUBBER, 1)  # foot
    g.box(70, 80, 5, 7, -3, 3, STEEL, 1)  # cross brace / spring
    g.pin(88, 8, 4.5, "left")
    g.pin(88, 8, -4.5, "right")
    # ---- stock: spade grip frame, cheek rest, rubber recoil pad, monopod
    g.mount("stock", -30, 12)
    g.use("def_stock")
    g.bevel(-50, -30, 5, 20, -3.5, 3.5, POLY, 1)
    g.box(-52, -34, 20, 22, -3, 3, PAD_R, 2)  # cheek rest
    g.box(-56, -50, 6, 17, -3, 3, POLY, 2)  # neck
    g.box(-57, -56, 2, 21, -4.5, 4.5, STEEL, 1)  # butt plate
    pad = g.box(-63, -57, 3, 20, -4.5, 4.5, PAD_R, 2)
    if hi:
        ribs(pad, ("right", "left"), 2, shade(PAD_R, 0.7))
        ribs(pad, ("up",), 3, shade(PAD_R, 1.4))
        g.pin(-52, 12, 3, "left")
        g.pin(-52, 12, -3, "right")
        sling_swivel(g, -44, 5, 0, True)
    g.box(-47, -44, 0, 5, -2, 2, BLACK, 1)  # monopod block
    g.box(-46.5, -44.5, -8, 0, -1, 1, STEEL, 1)  # monopod leg
    g.box(-48.5, -42.5, -10, -8, -2.5, 2.5, RUBBER, 1)  # foot
    g.box(-47, -44, -4, -2, 2, 3, STEEL, 1)  # locking knob
    g.use("frame")
    return g
