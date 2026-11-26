"""FN SCAR-H Mk17 (7.62x51mm NATO) and PKM (7.62x54mmR)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, knurl, mag_bones, qd_cup, roll_mark, sling_swivel
from guns_b import (bore, cap_bevel, curve_mag, disc, edge, end_dot, knob, lines, loop, on_seg, pins, slotted, soften,
                    stitch, stitch_v, stud)


def scar_h():
    """FN SCAR-H Mk17 STD: monolithic aluminium upper with the full-length top rail, removable side rails and the
    bottom rail on its front, ejection port and brass deflector on the right, reciprocating charging handle on the
    left, polymer lower with the flared magwell, ambidextrous controls and the integral guard, gas block with the
    two-position regulator, folding front and rear sights, SCAR flash hider, the side-folding telescoping stock
    with its cheek riser, and the 20-round steel magazine. Flat dark earth."""
    g = gun("scar_h", "rifle", "ar")
    B = 13.5  # bore line
    UP = shade(TAN, 1.04)  # the anodised upper, a touch lighter than the polymer
    LO = shade(TAN, 0.94)
    MK = shade(TAN, 0.72)  # moulded and engraved lines
    # ------------------------------------------------ monolithic upper: core, walls round the ejection port
    core = g.box(-10, 66, 9, 19, -3.5, 3.5, UP)
    lw = g.box(-10, 66, 10, 18, 3.5, 4.5, UP)
    g.box(-10, 7, 10, 18, -4.5, -3.5, UP)
    rwf = g.box(19, 66, 10, 18, -4.5, -3.5, UP)
    g.box(7, 19, 10, 12, -4.5, -3.5, UP)
    g.box(7, 19, 16.5, 18, -4.5, -3.5, UP)
    for s in (3.5, -3.5):
        edge(g, -10, 66, 18, s, UP, 1.25)
        edge(g, -10, 66, 10, s, UP, 0.8)
    mark(core, "right", 7, 19, 12, 16.5, DARK)  # the inside of the port
    for c, side in ((lw, "left"), (rwf, "right")):
        mark(c, side, c.ext[0] + 1, 30, 13, 13.5, MK)  # the extrusion's groove
    mark(lw, "left", 14, 40, 15, 16.5, DARK)  # charging handle slot
    for f in (-8, 64):
        mark(lw, "left", f, f + 1, 10, 18, MK)
    g.box(-10.5, -10, 9.5, 18.5, -3, 3, shade(UP, 0.85), 2)  # rear face
    rail = g.teeth_rail(-10, 66, 19, -3, 3, color=UP)
    for i, f in enumerate(range(-9, 66, 3)):
        if i % 2 == 0:
            mark(rail[0], "left", f, f + 1, 19, 20, shade(WHITE, 0.75))  # slot numbers
    # brass deflector behind the port
    g.box(3.5, 6.5, 12, 18, -5.5, -4.5, UP, 2)
    g.box(1, 4, 12.5, 15.5, -5.2, -4.2, UP, 2, tilt=-35, pivot=(4, 15.5))
    # side rails at 3 and 9 o'clock on the front of the upper, with their screws
    for sg in (1, -1):
        s0 = 4.5 if sg > 0 else -5.5
        g.box(40, 63, 11.5, 15.5, s0, s0 + 1, shade(BLACK, 0.95), 2)
        for f in range(41, 62, 3):
            g.box(f, f + 2, 11, 16, s0 + sg * 1, s0 + sg * 1 + 1, shade(BLACK, 1.1), 1)
        for f in (40.5, 62.5):
            stud(g, f, 13.5, 4.5 * sg, "left" if sg > 0 else "right", shade(SILVER, 0.7), 0.8)
    teeth = g.teeth_rail(36, 64, 9, -3, 3, color=shade(BLACK, 0.95), down=True)  # bottom rail
    for f in (31, 33):
        pins(g, f, 11, 4.5, shade(UP, 1.3), 1.0)  # barrel clamp screws
    qd_cup(g, 64, 11.5, 4.5, "left", BLACK)  # front sling point
    qd_cup(g, -7, 11.5, 4.5, "left", BLACK)  # and the rear one
    # ------------------------------------------------ polymer lower: body, flared magwell, guard, grip
    body = g.box(-7, 24, 3, 9.5, -4, 4, LO)
    g.box(-7, 24, 3, 4, -3.5, 3.5, shade(LO, 0.85))
    well = g.box(7, 21, -0.5, 3, -4, 4, LO)
    g.bevel(6.5, 21.5, -2, 0, -4.5, 4.5, LO, 0.8)  # the flared mouth
    g.box(21, 25, 4, 9.5, -3.5, 3.5, LO, 2, tilt=12, pivot=(21, 4))  # front of the lower, under the upper
    roll_mark(body, "left", 9, 20, 6.5, MK)  # FN HERSTAL  SCAR-H
    roll_mark(well, "left", 9, 18, 0.5, MK)
    mark(body, "left", 0, 1, 8, 9, WHITE)  # S
    mark(body, "left", 3, 4, 8.5, 9.3, WHITE)  # 1
    # integral trigger guard, trigger
    g.box(-2, 8, -1, 0.5, -1.2, 1.2, LO, 2)
    g.box(6.5, 8, -1, 3, -1.2, 1.2, LO, 2)
    g.box(-3, -1, -0.5, 3.5, -1.2, 1.2, LO, 2, tilt=-20, pivot=(-2, 3.5))
    g.box(2.5, 3.5, 1, 3, -0.5, 0.5, BLACK, 1)
    g.box(2.5, 3.5, -0.5, 1.5, -0.5, 0.5, BLACK, 1, tilt=20, pivot=(3, 1.5))
    # ambidextrous selector, at SAFE
    for sg in (1, -1):
        s0 = 4 if sg > 0 else -5
        disc(g, -2, 7.3, s0, s0 + 1, 1.5, BLACK)
        g.box(-2, 2.5, 6.8, 7.8, s0 + sg * 0.5, s0 + sg * 0.5 + 1, BLACK, 1, tilt=12, pivot=(-2, 7.3))
    # bolt release (left) and the ambidextrous magazine release
    g.box(4, 7, 5.5, 8.5, 4, 5, BLACK, 1)
    bc = g.box(4.5, 6.5, 4.5, 6, 4.5, 5.5, BLACK, 1)
    lines(bc, "left", 4.5, 6.5, 4.5, 6, 2, shade(BLACK, 1.5), vertical=True)
    for sg in (1, -1):
        disc(g, 7.6, 5.5, 4 * sg - (0 if sg > 0 else 1), 4 * sg + (1 if sg > 0 else 0), 1.1, BLACK)
    # takedown pins, hammer and trigger pins
    for f, u in ((-5, 8), (23, 7.5)):
        disc(g, f, u, 4, 4.8, 1.0, STEEL)
        disc(g, f, u, -4.8, -4, 1.0, STEEL)
    for f, u in ((0.5, 5.5), (4.5, 5)):
        pins(g, f, u, 4, size=0.8)
    g.pistol_grip(-6.5, 1.5, 3, 15, 6, LO, angle=18)
    g.box(-8.5, -6, 0.5, 3.5, -2.5, 2.5, LO, 2, tilt=-18, pivot=(-2.5, 3))  # beavertail
    g.box(1.5, 2.5, -4.5, -1.5, -2.5, 2.5, LO, 2, tilt=-18, pivot=(-2.5, 3))  # finger nub
    # ------------------------------------------------ bolt (in the port) and the left charging handle
    g.part("bolt", 13, 14)
    bolt = g.box(7.5, 18.5, 12.5, 16, -4.4, -3.4, STEEL, 2, bone="bolt")
    mark(bolt, "right", 14.5, 18.5, 12.5, 16, shade(STEEL, 1.3))
    mark(bolt, "right", 15.5, 17, 14.5, 15.5, DARK)  # extractor
    g.part("charging_handle", 36, 15.5, 5)
    g.use("charging_handle")
    g.box(34, 39, 14.5, 16.5, 4, 5.5, BLACK, 2)
    g.box(35, 38, 14.8, 16.3, 5.5, 7.5, BLACK, 1)
    disc(g, 36.5, 15.5, 7.5, 10, 1.9, BLACK)
    disc(g, 36.5, 15.5, 10, 10.6, 1.2, shade(BLACK, 1.25))
    g.use("frame")
    # ------------------------------------------------ barrel, gas block with the regulator, folding front sight
    g.rod(30, 82, B, 0, 2.2, BLACK)
    g.box(66, 66.5, 9, 19, -3, 3, shade(UP, 0.8), 1)  # front face of the upper
    g.rod(66, 71, B, 0, 3.0, BLACK)
    g.box(66.5, 70.5, B, 17.5, -2.4, 2.4, BLACK)
    g.rod(66, 72, 17.5, 0, 2.2, BLACK)
    g.rod(72, 73.5, 17.5, 0, 1.6, STEEL)  # regulator
    g.box(72.5, 73.5, 16.5, 18.5, 1.6, 3.6, STEEL, 1)  # its lever, normal setting
    pins(g, 68.5, 11.5, 2.4, size=0.8)
    g.box(59, 66, 21.5, 23.5, -3.5, 3.5, BLACK, 2)  # front sight base clamped on the rail end
    for sg in (1, -1):
        g.box(59, 66, 19.5, 22, 3 * sg - (0 if sg > 0 else 1), 3 * sg + (1 if sg > 0 else 0), BLACK, 2)
        g.box(61, 64.5, 23.5, 28.5, 1.5 * sg - (0 if sg > 0 else 1), 1.5 * sg + (1 if sg > 0 else 0), BLACK, 1)
    g.box(62.5, 63.5, 23.5, 29, -0.5, 0.5, DARK, 1)  # post
    disc(g, 60.5, 22.5, -4.5, 4.5, 0.9, STEEL)  # the hinge
    g.muzzle = (90.0, B)
    g.mount("muzzle", 82, B, bore=2.2)
    g.use("def_muzzle")  # SCAR flash hider: six long slots, closed at the front
    g.rod(82, 84.5, B, 0, 2.7, BLACK)
    g.box(82.5, 84, B - 2.9, B + 2.9, -1.5, 1.5, shade(BLACK, 1.1), 1)  # wrench flats
    g.rod(84, 89.5, B, 0, 1.7, DARK, 0)
    for i in range(6):
        g.box(84.5, 89, B + 1.7, B + 2.7, -0.5, 0.5, BLACK, 1, roll=30 + 60 * i, pivot=(0, B, 0))
    g.rod(89, 90, B, 0, 2.7, BLACK)
    bore(g, 90, B, 1.4)
    g.use("frame")
    # ------------------------------------------------ 20-round steel magazine
    MF0, MTOP, MW = 8, 2, 7
    segs = [(0, 8), (0, 6), (1, 6)]
    mag_bones(g, MF0 + 5, MTOP)
    body = curve_mag(g, MF0, MTOP, MW, segs, BLACK, overlap=0.4)
    for i, seg in enumerate(body):
        c, df, ut, h, _a, _p = seg
        f = MF0 + df
        if i:  # the raised panel pressed into each side
            on_seg(g, seg, f + 1.5, f + 8.5, ut - h + 1, ut - 1, -4, 4, shade(BLACK, 1.15), 2)
        on_seg(g, seg, f + 9.4, f + 10.4, ut - h - 0.4, ut, -2.5, 2.5, shade(BLACK, 0.9), 1)  # front spine
        on_seg(g, seg, f - 0.4, f + 0.6, ut - h - 0.4, ut, -2.5, 2.5, shade(BLACK, 0.9), 1)  # rear spine
    on_seg(g, body[0], MF0 + 1, MF0 + 9, -2, -1, -4, 4, shade(BLACK, 1.15), 1)  # stop rib under the well
    c, df, ut, h, _a, _p = body[-1]
    on_seg(g, body[-1], MF0 + df - 1, MF0 + df + 11, ut - h - 2, ut - h, -4, 4, STEEL, 2)  # floor plate
    on_seg(g, body[-1], MF0 + df + 4, MF0 + df + 6, ut - h - 2.5, ut - h - 1.5, -1.5, 1.5, DARK, 1)
    mag_lips(g, MF0 + 1, MF0 + 9, MTOP, MW, BLACK, round_len=8, r=1.3)
    g.mag_profile = dict(f0=MF0, top=MTOP, width=MW, segs=segs, color=BLACK, kind="rifle")
    # ------------------------------------------------ mounts: folding rear sight, rails
    g.use("frame")
    g.mount("optic", 8, 22, length=36)
    g.use("def_optic")  # folding rear sight, up
    g.box(-9, -3, 22, 23.5, -3.5, 3.5, BLACK, 2)
    for sg in (1, -1):
        g.box(-9, -3, 19.5, 22, 3 * sg - (0 if sg > 0 else 1), 3 * sg + (1 if sg > 0 else 0), BLACK, 2)
        g.box(-8, -5, 23.5, 28, 1.5 * sg - (0 if sg > 0 else 1), 1.5 * sg + (1 if sg > 0 else 0), BLACK, 1)
    g.box(-7.5, -5.5, 23.5, 26, -1.5, 1.5, BLACK, 2)
    ap = g.box(-7.5, -5.5, 26, 27.5, -0.5, 0.5, BLACK, 1)
    end_dot(ap, DARK)
    disc(g, -6.5, 24, 3.5, 4.5, 1.2, BLACK)  # windage drum
    disc(g, -3.5, 22.8, -4.5, 4.5, 0.9, STEEL)  # hinge
    g.use("frame")
    g.mount("underbarrel", 44, 6, length=20, default=False)
    g.mount("side", 48, 13.5, 6, length=16, default=False)
    # ------------------------------------------------ side-folding telescoping stock
    g.mount("stock", -10, 13.5)
    g.use("def_stock")
    hinge = g.box(-14, -10, 8.5, 19, -4, 4, shade(TAN_D, 1.05))
    for u0 in (9, 13, 17):  # knuckles on the right (it folds to the right)
        knob(g, -12, -4.4, u0, u0 + 2, 1.4, BLACK)
    disc(g, -12, 14, 4, 5, 1.3, BLACK)  # folding latch
    top = g.bevel(-44, -14, 12, 19, -3.5, 3.5, TAN, 1)
    for c in top[:2]:
        for side in ("left", "right"):
            mark(c, side, -40, -16, 13.5, 17, shade(TAN, 0.86))  # the recessed side panel
            lines(c, side, -38, -18, 14.5, 16.5, 2, shade(TAN, 0.8))
    riser = g.bevel(-38, -18, 18.5, 21.5, -3, 3, TAN_D, 0.8)  # adjustable cheek riser
    for c in riser[:2]:
        for side in ("left", "right"):
            mark(c, side, -36, -20, 19, 19.5, shade(TAN_D, 0.75))  # the seam where it slides
    g.box(-37, -35, 18.5, 21, 3, 4, BLACK, 1)  # its lock button
    strut = g.box(-37, -14, 8, 12.5, -3, 3, TAN, tilt=19, pivot=(-14, 10.25))  # lower strut to the hinge
    web = g.box(-44, -34, 1, 12.5, -3.5, 3.5, TAN)
    mark(web, "left", -42, -38, 3, 5, DARK)  # sling slot
    mark(web, "right", -42, -38, 3, 5, DARK)
    qd_cup(g, -39, 9, 3.5, "left", BLACK)  # QD sling socket
    for sg in (1, -1):  # length-of-pull lock buttons
        disc(g, -16.5, 15.5, 3.5 * sg - (0 if sg > 0 else 1), 3.5 * sg + (1 if sg > 0 else 0), 1.1, BLACK)
    g.box(-34, -14, 11.3, 12.3, -1.5, 1.5, BLACK, 1)  # the telescoping beam under the top
    g.box(-24, -21, 10.5, 11.5, -2, 2, BLACK, 1)  # length-of-pull lever
    g.bevel(-46, -44, 0, 21, -4, 4, TAN, 0.8)
    pad = g.bevel(-49, -46, -0.5, 21.5, -4, 4, RUBBER, 1)
    for c in pad[:2]:
        lines(c, "left", -49, -46, 0.5, 21, 2, shade(RUBBER, 1.5))
        lines(c, "right", -49, -46, 0.5, 21, 2, shade(RUBBER, 1.5))
    g.use("frame")
    return g


def pkm():
    """PKM (7.62x54mmR): stamped receiver with its embossed channels and riveted trunnions, the belt window on the
    right, link exit and case port on the left, side scope rail, top cover (opens on reload) over the feed tray,
    tangent rear sight on the front of the receiver, quick-change fluted barrel with its carrying handle, gas
    cylinder under the barrel with the regulator, bipod folded back under it, eared front sight, slotted flash
    hider, skeleton wooden stock with the folding shoulder rest, and the 100-round box on the right with the belt
    rising into the feed."""
    g = gun("pkm", "rifle", "lmg")
    B = 14.0  # bore line
    RC = BLUED
    HI = shade(RC, 1.6)  # rivet heads
    EMB = shade(RC, 1.15)  # embossed channels catch the light
    # ------------------------------------------------ stamped receiver: core and side walls with their openings
    core = g.box(-12, 34, 4, 20, -3.5, 3.5, RC)
    lwr = g.box(-12, 3, 4.5, 20, 3.5, 4.5, RC)  # left wall: behind the link exit
    roll_mark(lwr, "left", -8, 1, 7.5, HI)  # factory mark and serial
    g.box(17, 34, 4.5, 20, 3.5, 4.5, RC)  # in front of it
    g.box(3, 17, 9.5, 15, 3.5, 4.5, RC)  # between the case port and the link exit
    g.box(3, 6, 4.5, 9.5, 3.5, 4.5, RC)
    g.box(16, 17, 4.5, 9.5, 3.5, 4.5, RC)
    g.box(-12, 3, 4.5, 20, -4.5, -3.5, RC)  # right wall: behind the belt window
    rwf = g.box(17, 34, 4.5, 20, -4.5, -3.5, RC)
    g.box(3, 17, 4.5, 15, -4.5, -3.5, RC)
    for side in ("left", "right"):
        mark(core, side, 3, 17, 15, 20, DARK)  # the belt passes through, right to left
    mark(core, "left", 6, 16, 4.5, 9.5, DARK)  # case ejection port
    mark(rwf, "right", 20, 33, 6.5, 8, DARK)  # charging handle slot
    for s in (3.5, -3.5):
        edge(g, -12, 34, 4.5, s, RC, 0.8)
    # embossed strengthening channels along both sides
    for sg, side in ((1, "left"), (-1, "right")):
        s0 = 4 if sg > 0 else -5
        g.box(-10, 3, 12.5, 13.5, s0, s0 + 1, EMB, 1)
        g.box(17, 31, 12.5, 13.5, s0, s0 + 1, EMB, 1)
        if sg > 0:
            g.box(-10, 6, 10.5, 11.5, s0, s0 + 1, EMB, 1)
            g.box(16, 31, 10.5, 11.5, s0, s0 + 1, EMB, 1)
        else:
            g.box(-10, 31, 10.5, 11.5, s0, s0 + 1, EMB, 1)
        for f, u in ((-10, 6), (-10, 9), (-7.5, 6), (-7.5, 17.5), (-10, 17.5),  # rear trunnion
                     (28, 6), (30.5, 6), (33, 6), (28, 9), (30.5, 9), (33, 9), (30.5, 17.5), (33, 17.5)):  # front
            stud(g, f, u, 4.5 * sg, side, HI, 0.9)
    plate = g.box(-13.5, -12, 4.5, 19.5, -3.5, 3.5, STEEL, 2)  # back plate
    g.box(34, 38, 6, 19, -4, 4, shade(RC, 0.85))  # front trunnion, the barrel socket
    disc(g, 36, 16.5, 4, 5, 1.4, STEEL)  # barrel lock
    g.box(35, 37.5, 12, 16.5, 4, 5, STEEL, 1)
    # the dovetail scope rail on the left, behind the link exit
    g.box(-10, 2, 14, 19, 4.5, 5, RC, 2)
    srail = g.box(-9.5, 1.5, 15, 18, 5, 6, shade(RC, 1.08), 2)
    edge(g, -9.5, 1.5, 18, 5, RC, 1.25)
    mark(srail, "left", -4, -3, 15, 18, DARK)
    # trigger housing, guard, trigger, safety, pistol grip
    th = g.box(-15, 2.5, 1.5, 4, -2.8, 2.8, RC)
    pins(g, -13.5, 2.8, 2.8, HI, 0.8)
    pins(g, 0.5, 2.8, 2.8, HI, 0.8)
    g.box(-5, 2.5, -2.5, -1.5, -1, 1, RC, 2)
    g.box(1, 2.5, -2.5, 2, -1, 1, RC, 2)
    g.box(-2.5, -1.5, -0.5, 1.5, -0.5, 0.5, STEEL, 1)
    g.box(-2.5, -1.5, -2, 0, -0.5, 0.5, STEEL, 1, tilt=20, pivot=(-2, 0))
    disc(g, -7, 3, 2.8, 3.8, 1.3, STEEL)  # safety (left), at fire
    g.box(-7, -3.5, 2.5, 3.5, 3.3, 4.3, STEEL, 1, tilt=-15, pivot=(-7, 3))
    grip = g.pistol_grip(-12, -4, 4, 16, 6, WOOD, angle=14, stipple=False)
    for side in ("left", "right"):
        knurl(grip, side, -11, -5, -9, 1, shade(WOOD, 0.72))  # checkered panels
    stud(g, -8, -6, 3, "left", shade(SILVER, 0.75), 1.0)  # grip screw
    # ------------------------------------------------ charging handle (right, low, in front of the box)
    g.part("charging_handle", 28, 7, -5)
    g.use("charging_handle")
    g.box(25.5, 30, 6, 8.5, -5.5, -4, RC, 2)
    g.box(27, 29, 6.5, 8, -8, -5.5, RC, 1)
    disc(g, 28, 7.25, -10.5, -8, 1.8, RC)
    g.use("frame")
    # ------------------------------------------------ feed tray (seen when the cover opens)
    tray = g.box(0, 20, 19.5, 20.5, -4, 4, STEEL, 1)
    for f in (3, 8, 13, 18):
        mark(tray, "up", f, f + 1, 0, 0, shade(STEEL, 0.65), -3.5, 3.5)
    g.box(2, 3, 20.5, 21.5, -4, 4, SILVER, 1)  # cartridge stop
    # ------------------------------------------------ top cover with its pressed ribs (hinged at the rear here)
    g.part("cover", -12, 21)
    g.use("cover")
    cov = g.bevel(-12, 22, 20, 23.5, -4.5, 4.5, RC, 1.2)
    for c in cov[:2]:
        for side in ("left", "right"):
            stitch(c, side, -9, 20, 21, shade(RC, 1.3), gap=4)  # spot welds
    for s0 in (1, -2):
        g.box(-9, 19, 23, 24, s0, s0 + 1, EMB, 1)  # the two pressed ribs
    g.box(4, 16, 23, 24.5, -0.5, 0.5, EMB, 1)  # feed lever housing
    disc(g, -11, 21.2, -4.8, 4.8, 1.2, STEEL)  # hinge
    g.box(19.5, 22.5, 21, 23, -5, -4.5, STEEL, 1)  # latch
    for s0 in (-3, 2):  # the feed pawls underneath
        g.box(5, 15, 20, 21, s0, s0 + 1, STEEL, 1)
    g.use("frame")
    # ------------------------------------------------ tangent rear sight on the front of the receiver
    rs = g.box(22.5, 33, 20, 22, -3, 3, RC)
    mark(rs, "left", 24, 32, 20.5, 21.5, shade(RC, 0.75))
    leaf = g.box(23, 32, 22, 23, -1.5, 1.5, GUNMETAL, 1, tilt=-4, pivot=(32, 22.5))
    for i, f in enumerate(range(24, 31)):
        mark(leaf, "up", f, f + 0.6, 0, 0, WHITE if i % 2 else shade(WHITE, 0.6), -0.5, 0.5)
    g.box(23, 24.5, 23, 24.2, -1.5, 1.5, GUNMETAL, 1)  # notch block
    g.box(23.5, 24.5, 23.6, 24.2, -0.5, 0.5, DARK, 0)
    g.box(27, 29.5, 21.5, 24, -2, 2, GUNMETAL, 1)  # slider
    for s0 in (2, -3):
        g.box(27.5, 29, 22, 23.5, s0, s0 + 1, SILVER, 1)
    # ------------------------------------------------ fluted barrel, carrying handle, gas cylinder and block
    g.rod(38, 104, B, 0, 2.2, RC)
    g.ring(38, 41, B, 0, 3.2, RC)  # barrel extension
    for c in g.rod(44, 76, B, 0, 2.6, RC):  # the fluted section
        for side in ("right", "left", "up", "down"):
            lines(c, side, 45, 75, c.ext[2], c.ext[3], 2, shade(RC, 0.6))
    g.ring(41, 44, B, 0, 3.3, STEEL)  # carrying handle clamp
    g.box(41.5, 43.5, 17, 24, -1.2, 1.2, STEEL, 2, tilt=-10, pivot=(42.5, 17))  # its arm
    hnd = g.bevel(42, 57, 23, 26.5, -1.8, 1.8, WOOD, 0.6)  # and the wooden grip, free at the front
    for c in hnd[:2]:
        lines(c, "left", 43, 56, 23.5, 26, 2, shade(WOOD, 0.75), vertical=True)
        lines(c, "right", 43, 56, 23.5, 26, 2, shade(WOOD, 0.75), vertical=True)
    g.box(56.5, 57.5, 23.5, 26, -1.2, 1.2, STEEL, 1)  # end cap
    g.rod(36, 80, 8, 0, 1.9, RC)  # gas cylinder
    g.box(36, 40, 6, 10.5, -2.2, 2.2, RC, 2)  # its rear seat on the trunnion
    g.rod(80, 86, B, 0, 3.2, RC)  # gas block
    g.box(80.5, 85.5, 8, B, -2.4, 2.4, RC)
    g.rod(80, 86, 8, 0, 2.5, RC)
    g.rod(86, 88, 8, 0, 2.0, GUNMETAL)  # regulator with its three notches
    for i, ang in enumerate((0, 60, 120)):
        g.box(86.5, 87.5, 8 + 1.8, 8 + 2.6, -0.4, 0.4, DARK if i else SILVER, 0, roll=ang - 60, pivot=(0, 8, 0))
    loop(g, 81, 85, 11.5, 15.5, 3.2, 4.2)  # front sling loop (left)
    # ------------------------------------------------ eared front sight
    g.rod(95, 100, B, 0, 3.0, RC)
    g.box(95.5, 99.5, 15, 19, -2, 2, RC)
    for s0 in (2, -3):
        g.box(95, 100, 17, 24, s0, s0 + 1, RC, 2)
    g.box(97, 98, 18, 23, -0.5, 0.5, DARK, 1)  # post
    disc(g, 97.5, 17.5, -2, 2, 1.0, shade(RC, 1.2))
    g.muzzle = (112.0, B)
    g.mount("muzzle", 104, B, bore=2.2)
    g.use("def_muzzle")  # slotted flash hider, four long slots
    g.rod(104, 106, B, 0, 3.0, RC)
    g.rod(105.5, 111.5, B, 0, 2.0, DARK, 0)
    for i in range(4):
        g.box(106, 111, B + 2.0, B + 3.0, -1.2, 1.2, RC, 1, roll=45 + 90 * i, pivot=(0, B, 0))
    g.rod(111, 112, B, 0, 3.0, RC)
    bore(g, 112, B, 1.5)
    g.use("frame")
    # ------------------------------------------------ bipod, folded back under the gas cylinder
    g.mount("underbarrel", 80, 6)
    g.use("def_underbarrel")
    g.rod(78, 82, 8, 0, 2.6, BLACK)  # clamp round the gas cylinder
    g.box(78.5, 81.5, 4.5, 7, -3, 3, BLACK, 2)  # yoke
    for ds in (-2.6, 2.6):
        disc(g, 80, 5.5, ds - 1, ds + 1, 1.3, STEEL)  # leg pivots
        g.box(62, 80, 4.8, 6.2, ds - 0.6, ds + 0.6, STEEL, 1)  # stamped legs
        g.box(62, 79, 5, 6, ds - 1, ds + 1, shade(STEEL, 0.85), 1)
        g.box(59, 62.5, 3.5, 6.5, ds - 1.2, ds + 1.2, BLACK, 1)  # spade feet
    g.box(66, 68, 4.5, 6.5, -3.6, 3.6, STEEL, 1)  # the clip that holds the legs together
    g.use("frame")
    g.mount("optic", 2, 24.5, 2, length=16, default=False)
    g.mount("side", 52, B, 3.2, length=10, default=False)
    # ------------------------------------------------ 100-round box on the right, the belt rising into the feed
    mag_bones(g, 14, 4)
    AM = "#4a5530"
    box = g.bevel(2, 26, -18, 3, -9, 5, AM, 1.2)
    for s0 in (4.5, -9.5):  # the stiffening ribs pressed into each side
        for u in (-14.5, -9, -3.5):
            g.box(4, 24, u, u + 1, s0, s0 + 1, shade(AM, 1.12), 1)
        for f in (4, 23):
            g.box(f, f + 1, -14.5, -2.5, s0, s0 + 1, shade(AM, 1.12), 1)
    lid = g.box(1.5, 26.5, 3, 4.5, -9.5, 5.5, shade(AM, 1.05), 2)
    mark(lid, "up", 2, 26, 0, 0, shade(AM, 0.8), -1, -0.5)
    g.box(4, 16, 3, 5.5, -9.5, -6, AM, 2)  # the belt mouth with its flap
    g.box(26, 27.5, -1, 4, -4, -1, STEEL, 1)  # lid latch
    g.box(27, 28, 0, 2, -3, -2, DARK, 1)
    for f in (6, 18):  # the hook that clips the box under the receiver
        g.box(f, f + 3, 4, 5.5, 1, 4, STEEL, 1)
    g.box(8, 20, 4.5, 5.2, -5, 0, STEEL, 1)  # folded carry handle on the lid
    g.box(1, 2, -15, -3, -2, 1, STEEL, 1)
    g.box(2, 26, -18.5, -17.5, -9.4, 5.4, shade(AM, 0.8), 1)  # base rim
    belt = [(5.6, -7.6), (7.5, -7.9), (9.4, -8.0), (11.3, -7.9), (13.2, -7.5), (14.9, -6.8), (16.4, -5.8), (17.8, -4.6)]
    for u, s in belt:
        cartridge(g, 4.5, u, s, length=11, r=0.9)
        g.box(4.5, 5, u - 1.1, u + 1.1, s - 1.1, s + 1.1, shade(BRASS, 0.75), 1)  # the rim
        g.box(6.5, 7.5, u - 1.1, u + 1.1, s - 1.1, s + 1.1, STEEL, 1)  # the link round the case
        g.box(9, 10, u - 1.1, u + 1.1, s - 1.1, s + 1.1, STEEL, 1)
    for s in (-1.5, 1.5):  # the rounds lying in the feed tray
        cartridge(g, 4.5, 21.4, s, length=11, r=0.9)
    g.mag_profile = dict(f0=2, top=4, width=14, segs=[(0, 22)], color=AM, kind="box")
    # ------------------------------------------------ skeleton wooden stock with the folding shoulder rest
    g.use("frame")
    g.mount("stock", -13.5, 13)
    g.use("def_stock")
    nose = g.box(-18, -13.5, 4.5, 19, -3.5, 3.5, WOOD)
    comb = g.bevel(-54, -15, 13, 19, -3.5, 3.5, WOOD, 1.2)
    low = g.box(-55, -15, 4.5, 8.5, -3, 3, WOOD, tilt=9, pivot=(-15, 6.5))  # lower edge, dropping to the toe
    heel = g.box(-54, -47, -2.5, 13.5, -3.5, 3.5, WOOD)
    for f, u in ((-18, 13), (-18, 8.2), (-47, 13), (-47, 3.2)):
        g.box(f - 1.3, f + 1.3, u - 1.3, u + 1.3, -3, 3, WOOD, 2, tilt=45, pivot=(f, u))
    for c in (nose, comb[0], low, heel):
        for side in ("left", "right"):
            lines(c, side, c.ext[0], c.ext[1], c.ext[2] + 1, c.ext[3], 2, shade(WOOD, 0.84))
    g.box(-18, -13.5, 19, 19.5, -1.5, 1.5, STEEL, 1)  # tang strap
    stud(g, -16, 16, 3.5, "left", HI, 1.0)
    stud(g, -16, 16, -3.5, "right", HI, 1.0)
    bp = g.bevel(-58, -54, -3, 19.5, -4, 4, STEEL, 1)  # butt plate
    mark(bp[0], "left", -58, -54, 2, 9, shade(STEEL, 0.75))
    g.box(-58.5, -57.5, 1, 9, -2, 2, shade(STEEL, 1.1), 1)  # the trapdoor to the cleaning kit
    g.box(-59.5, -58, 9, 19, -2, 2, STEEL, 1)  # the shoulder rest, folded down
    disc(g, -58.8, 18.8, -2.5, 2.5, 1.0, SILVER)
    loop(g, -51, -47, -1, 3, 3.5, 4.5)  # rear sling loop (left)
    g.use("frame")
    return g
