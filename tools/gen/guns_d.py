"""IWI Desert Eagle (.50 AE) and FN P90 (5.7x28mm), built after the real guns part by part."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, knurl, mag_bones, roll_mark, sling_swivel
from guns_a import Raked, cham, edge, endmark, engrave, ridges, spin, stipple, text, vrod
from kit import FACES


def deagle():
    """IWI Desert Eagle Mark XIX, .50 AE: a big gas-operated pistol. Heavy slide with a slotted top rail, rear
    serrations and an ejection port showing the bolt, a wedge frame with an under rail, a big rounded trigger
    guard, ambidextrous safety, a wide raked grip with textured panels, and the barrel standing out of the slide."""
    g = gun("deagle", "pistol", "pistol")
    SL, FR = STEEL, shade(STEEL, 0.8)
    PL, PD, PLL = POLY, shade(POLY, 0.82), shade(POLY, 1.18)
    PIN = shade(SILVER, 0.55)
    gr = Raked(g, -18, (-3, 4))
    # ------------------------------------------------------------ frame
    cham(g, -9, -4, 6, 9, -2.5, 2.5, FR, t=0, b=1)  # beavertail tang
    g.box(-10, -9, 6.5, 8.5, -2, 2, FR)
    g.box(-5, 14, 4, 9, -2.5, 2.5, FR)
    fz = cham(g, 14, 30, 4, 9, -2.5, 2.5, FR, t=0, b=1)  # the heavy front
    g.box(29, 31, 5, 8.5, -2, 2, shade(FR, 1.15))
    edge(g, 29, 31, 5, 2, FR, 0.5)
    edge(g, 29, 31, 5, -2, FR, 0.5)
    g.teeth_rail(18, 30, 4, -2, 2, FR, down=True)  # accessory rail
    for c in (fz,):
        for side in ("right", "left"):
            mark(c, side, 14, 30, 8, 9, shade(FR, 0.65))
    engrave(fz, "right", 15, 6, text(10, 7), shade(SILVER, 0.55))  # serial
    # trigger guard: big and rounded, the front strap sloping up into the frame
    g.box(-1, 20, -0.5, 2, -1.5, 1.5, FR)
    g.box(-1, 1, 0, 6, -1.5, 1.5, FR)
    g.box(18.5, 21.5, 0, 5, -1.5, 1.5, FR, 2, tilt=-8, pivot=(20, 4))
    g.box(20.5, 21.5, -0.5, 0.5, -1.5, 1.5, FR, 1, inflate=-0.15, tilt=45)
    g.box(19, 20, 1.5, 2.5, -1.5, 1.5, FR, 1, inflate=-0.15, tilt=45)
    g.box(3, 4, 0.5, 4, -1.5, 1.5, FR)
    g.box(4, 14, 3, 4, -2, 2, FR)
    g.box(7, 9, 1.5, 5, -0.5, 0.5, SILVER, 1)  # trigger blade
    g.box(7.5, 9.5, 0.5, 2, -0.5, 0.5, SILVER, 1, tilt=22, pivot=(8.5, 2))
    # ambidextrous safety, slide release, magazine catch, pins
    for s0, d in ((2.5, 1), (-3.5, -1)):
        g.box(-6, -1, 8, 9.5, s0, s0 + 1, shade(SL, 0.85), 1)
        spin(g, -3.5, 8.5, s0, s0 + 1, 1.5, PIN)
        g.box(-8, -6, 7.5, 10, s0, s0 + 1, shade(SL, 0.9), 1)  # thumb pad
    g.box(6, 12, 7.5, 8.5, 2.5, 3.5, shade(SL, 0.85), 1)  # slide release (left)
    g.box(4.5, 6.5, 6.5, 8.5, 2.5, 3.5, shade(SL, 0.85), 1)
    g.box(1.5, 3.5, 2.5, 5, 2.5, 3.5, PD, 1)  # mag catch button
    g.box(1.5, 3.5, 2.5, 5, -3.5, -2.5, PD, 1)
    for f, u in ((-2.5, 6), (10, 5.5), (22, 6)):
        g.pin(f, u, 2.5, "left", PIN)
        g.pin(f, u, -2.5, "right", PIN)
    for f in (16, 19, 22, 25):  # frame rails and finger rests under the slide
        g.box(f, f + 1, 3.2, 4, -2.8, 2.8, shade(FR, 0.7), 1)
    g.box(4, 14, 8.2, 9, -3, 3, shade(FR, 1.1), 1)
    for s0 in (-3, 2):  # barrel lug under the muzzle end
        g.box(22, 30, 5, 8, s0, s0 + 1, shade(FR, 1.2), 1)
    # ------------------------------------------------------------ grip
    gr.box(-8, 2, -13, 5, -3.5, 3.5, PL)
    for f in (-8, 2):
        for s in (-3.5, 3.5):
            gr.vedge(f, s, -13, 4.5, PL)
    for h in (-2, -6, -10):  # finger grooves
        gr.box(1.5, 2.5, h - 0.5, h + 0.5, -2, 2, PD, 2, extra=45, inflate=0.207)
    gr.box(-9, -8, -10, -1, -2, 2, PL)  # backstrap swell
    for side, (s0, s1) in (("left", (3.5, 4.5)), ("right", (-4.5, -3.5))):
        p = gr.box(-7, 1, -12, 4, s0, s1, PL, 1)  # raised grip panels
        stipple(p, (side,), PL)
        for u in (-12.5, 4.5):
            gr.box(-7, 1, u - 0.5, u + 0.5, s0, s1, PL, 1, extra=45, inflate=-0.15)
        gr.box(-6, 0, -1, 0, s0, s1, PLL, 1)
    gr.box(-9, 3, -13, -12, -4, 4, PD, 2)  # magwell flare
    # ------------------------------------------------------------ barrel (fixed: the slide runs back over it)
    for c in g.rod(24, 37, 12.5, 0, 2.5, GUNMETAL, facets=3):
        endmark(c, "front", -0.8, 0.8, 11.7, 13.3, DARK)
    g.box(30, 37, 15, 16.5, -1, 1, shade(GUNMETAL, 1.1), 1)  # barrel rib
    g.box(33, 36, 16.5, 18.5, -0.5, 0.5, DARK, 1)  # front sight with its ramp
    g.box(31, 33, 16.5, 17.5, -0.5, 0.5, DARK, 1, tilt=25, pivot=(32, 16.5))
    g.box(34.5, 35.5, 17.5, 18.5, -0.3, 0.3, WHITE, 0)
    g.muzzle = (37.0, 12.5)
    # ------------------------------------------------------------ slide
    g.part("slide", 12, 12)
    g.use("slide")
    g.box(-6, 6, 9, 15, -3, 3, SL)
    sm1 = g.box(-6, 6, 9, 15, -3, 3, SL, 0)
    g.box(15, 30, 9, 15, -3, 3, SL)
    sm2 = g.box(15, 30, 9, 15, -3, 3, SL)
    g.box(6, 15, 9, 10.5, -3, 3, SL)  # under the ejection port
    g.box(6, 15, 10.5, 15, 0, 3, SL)  # the port's far wall
    g.box(6, 15, 15, 16, -3, 3, SL)
    g.box(6, 8, 10.5, 15, -3, 0, SL)  # hood of the port at the rear edge
    g.box(8, 15, 11, 15, -0.2, 0, DARK, 0)
    g.box(8, 15, 10.5, 14, -2.5, -0.2, GUNMETAL, 2)  # the barrel and its chamber, seen through the port
    g.box(8, 15, 13, 14.5, -3, -2.5, BRASS, 1)  # a case caught in the port
    g.box(-6, 6, 15, 16, -2, 2, SL)
    g.box(15, 30, 15, 16, -2, 2, SL)
    for f0, f1 in ((-6, 6), (15, 30)):
        edge(g, f0, f1, 15, 2, shade(SL, 1.25))
        edge(g, f0, f1, 15, -2, shade(SL, 1.25))
    edge(g, 6, 15, 15, 2, shade(SL, 1.25))
    edge(g, 6, 15, 15, -2, shade(SL, 1.25))
    g.box(29.5, 30.5, 9, 15, -2.5, 2.5, shade(SL, 1.1), 2)  # front face
    for s in (-3, 3):
        edge(g, 29.5, 30.5, 15, s, shade(SL, 1.1), 0.5)
    ridges(g, -5.5, 1.5, 9, 15, -3, 3, SL)  # rear serrations
    # the slotted top rail
    rl = g.box(-5, 29, 16, 17.5, -2.5, 2.5, shade(SL, 0.85), 2)
    for row in range(1, rl.front.h, 2):
        rl.front.hline(row, DARK)
    for f in range(-4, 28, 3):
        mark(rl, "left", f, f + 1, 16, 17.5, DARK)
        mark(rl, "right", f, f + 1, 16, 17.5, DARK)
    # rear sight in the rail: a notch block with white outlines
    for s0 in (-2.5, 1.5):
        p = g.box(-6, -2, 17.5, 19.5, s0, s0 + 1, DARK, 2)
        endmark(p, "rear", s0, s0 + 1, 17.5, 19.5, WHITE)
    g.box(-6, -3, 17.5, 18.5, -1.5, 1.5, DARK, 2)
    g.box(-6.3, -5.7, 17, 18, -0.5, 0.5, DARK, 0)
    g.box(-4, -3, 16.3, 17.3, 2.5, 3.2, SILVER, 1)  # windage screw
    # markings: DESERT EAGLE / MARK XIX / CAL .50 AE
    engrave(sm2, "left", 16, 13, text(11, 3, (0,)), shade(SILVER, 0.75))
    engrave(sm1, "left", -2, 13, text(7, 8), shade(SILVER, 0.6))
    engrave(sm2, "right", 16, 12, text(9, 5)[1:], shade(SILVER, 0.6))
    mark(sm2, "left", 15, 17, 9, 10, shade(SL, 0.6))
    # ------------------------------------------------------------ magazine
    mag_bones(g, -2, -10)
    mg = Raked(g, -18, (-3, 4))
    mgb = mg.box(-7, 1, -13, 4, -2.5, 2.5, SL, 2)
    for k in range(5):  # witness holes down the back
        endmark(mgb, "rear", 0, 1, -11 + 3 * k, -10 + 3 * k, BRASS)
    g.box(-5, 0, 5.5, 6, -2.5, -1.5, SL, 1)  # feed lips with the round
    g.box(-5, 0, 5.5, 6, 1.5, 2.5, SL, 1)
    cartridge(g, -5, 6.5, 0, 6, 1.5)
    bp = mg.box(-8, 2, -15, -13, -3, 3, shade(SL, 0.7), 2)
    mg.box(2, 3, -15, -14, -2.5, 2.5, shade(SL, 0.7), 2)
    mark(bp, "down", -7, 1, 0, 0, shade(SL, 0.5), -0.5, 0.5)
    g.mag_profile = dict(f0=-8, f1=2, top=-12, length=4, width=6, tilt=-18, pivot=(-3, 4), color=STEEL, kind="pistol")
    g.mount("optic", 6, 17.5, length=10, default=False, parent="slide")
    g.mount("muzzle", 37, 12.5, default=False, parent="slide", bore=2.2)
    g.mount("side", 24, 2, length=10, default=False)
    g.use("frame")
    return g


def p90():
    """FN P90, 5.7x28mm: a bullpup of smooth polymer with a thumbhole behind the grip, its translucent 50-round
    magazine lying along the top under the optics rail, a big trigger guard, ambidextrous cocking handle and
    safety, a rubber butt pad, and a short barrel with a slotted flash hider."""
    g = gun("p90", "rifle", "ar")
    PL, PD, PLL = "#3a3d38", shade("#3a3d38", 0.78), shade("#3a3d38", 1.2)
    PIN = shade(SILVER, 0.6)
    # ------------------------------------------------------------ body
    rear = cham(g, -44, -14, 4, 18, -4.5, 4.5, PL, t=2, b=2)  # the butt and cheek
    g.box(-46, -44, 4, 17, -4, 4, RUBBER)  # butt pad
    ribs(g.box(-47, -46, 5, 16, -3.5, 3.5, shade(RUBBER, 1.3), 2), ("right", "left"), 2, shade(RUBBER, 0.8))
    g.box(-46, -44, 6, 7, -4.5, 4.5, shade(RUBBER, 1.6), 1)
    body = cham(g, -14, 34, 9, 18, -5, 5, PL, t=2, b=2)
    hh = cham(g, 12, 33, 4, 10, -4.5, 4.5, PL, t=0, b=1.5)  # forward handhold
    ribs(hh, ("right", "left"), 3, shade(PL, 0.65))
    for c in (rear, body):
        for side in ("right", "left"):
            mark(c, side, c.ext[0] + 2, c.ext[1] - 2, c.ext[3] - 4, c.ext[3] - 3, shade(PL, 0.7))  # top seam
    engrave(rear, "left", -40, 14, text(10, 4), shade(SILVER, 0.6))  # FN P90
    engrave(body, "left", 20, 15, text(8, 2, (0,)), shade(SILVER, 0.6))
    mark(rear, "right", -42, -16, 5, 6, shade(PL, 0.7))
    # thumbhole: a lined rim around it
    g.box(-14, -6, 8.5, 9.5, -4, 4, PD)
    g.box(-15, -14, 4, 9, -4, 4, PD)
    # grip, trigger guard, trigger, safety
    g.pistol_grip(-6, 2, 9, 21, 6.5, PL, angle=12)
    g.box(-7, 3, -12.5, -11.5, -3.5, 3.5, PD, 2, tilt=-12, pivot=(-2, 9))
    g.box(-2, 15, -2, 0, -2, 2, PL)  # guard: a big loop
    g.box(14, 16, -2, 8, -2, 2, PL)
    g.box(15, 17, -2, -1, -2, 2, PL, 1, inflate=-0.2, tilt=45)
    g.box(1, 3, -2, 5, -2, 2, PL)
    g.box(5, 7, 2, 7, -0.5, 0.5, SILVER, 1)  # trigger
    g.box(5.5, 7.5, 0.5, 2.5, -0.5, 0.5, SILVER, 1, tilt=22, pivot=(6.5, 2))
    for s0 in (4.5, -5.5):  # ambidextrous safety lever above the trigger
        spin(g, 1, 7.5, s0, s0 + 1, 1.6, SILVER)
        g.box(-3, 2, 7, 8, s0, s0 + 1, PD if s0 > 0 else PL, 1)
    g.pin(-8, 7, 4.5, "left")
    g.pin(26, 12, 5, "left")
    g.pin(-30, 12, 4.5, "left")
    # barrel and hider
    g.rod(32, 40, 12, 0, 2, GUNMETAL, facets=3)
    g.rod(33, 36, 12, 0, 3, STEEL)
    g.muzzle = (45.0, 12.0)
    # cocking handles: both sides, riding in slots in the forward body
    for s0 in (4.5, -5.5):
        mark(g.box(12, 24, 12, 14, s0 - 0.01, s0 + 1, DARK, 0), "left" if s0 > 0 else "right", 12, 24, 12, 14, DARK)
    g.part("bolt", 0, 12)
    g.part("charging_handle", 14, 13, 5)
    for s0 in (5, -7):
        g.box(13, 17, 12.5, 14.5, s0, s0 + 2, BLACK, 2, bone="charging_handle")
        g.box(13, 17, 11.5, 15.5, s0 + (2 if s0 > 0 else -1), s0 + (4 if s0 > 0 else 1), PL, 2, bone="charging_handle")
    g.use("frame")
    # ------------------------------------------------------------ the translucent magazine on top
    mag_bones(g, -10, 18)
    MG, MGL = "#4c5961", "#6c7e88"
    mg = g.box(-30, 20, 18, 22, -3.5, 3.5, MG)
    for side in ("right", "left"):
        mark(mg, side, -29, 19, 18, 22, shade(MG, 1.1))
        for i in range(24):  # the rounds seen through the wall, side by side
            f = -29 + i * 2
            mark(mg, side, f, f + 1.5, 18.5 + (i % 2), 20 + (i % 2), BRASS)
            mark(mg, side, f + 1, f + 2, 18.5 + (i % 2), 19.5 + (i % 2), COPPER)
        mg.top.hline(0, MGL)
        mg.top.hline(mg.top.h - 1, MGL)
    mg.front.fill(shade(MG, 1.2))
    for i in range(5):
        mark(mg, "up", -29 + i * 10, -28 + i * 10, 0, 0, shade(MG, 0.6), -3, 3)
    g.box(-32, -30, 17, 23, -4, 4, PL)  # rear end cap with the latch
    g.box(-33, -32, 18, 22, -2, 2, BLACK, 1)
    g.box(-31, -29, 22, 23, -2, 2, PLL, 1)
    g.box(14, 22, 14, 18, -3, 3, shade(MG, 0.6))  # the feed neck dropping into the body
    g.box(20, 22, 17, 23, -3.5, 3.5, PL)  # front end cap
    g.mag_profile = None
    # side detail: forend slits, a vent row, sling loops, the lined rear body
    for f in range(18, 31, 3):
        g.box(f, f + 1, 6, 9, 4.2, 4.7, DARK, 0)
        g.box(f, f + 1, 6, 9, -4.7, -4.2, DARK, 0)
    for f in range(-40, -18, 4):
        g.box(f, f + 2, 7, 8, 4.3, 4.8, shade(PL, 0.6), 1)
        g.box(f, f + 2, 7, 8, -4.8, -4.3, shade(PL, 0.6), 1)
    sling_swivel(g, -38, 17, 4.6, down=False)
    sling_swivel(g, 28, 14, -4.6, down=False)
    g.box(-26, -16, 5, 6, -2, 2, PD)  # heel of the stock
    for f in (-30, -22, -14):
        g.box(f, f + 1, 4, 5, -2.5, 2.5, PD)
    # ------------------------------------------------------------ top rail housing
    g.box(-34, -29, 18, 23, -4.5, 4.5, PL)  # rear support
    g.box(-34, -29, 18, 23, -4.5, 4.5, PL, 0)
    g.box(21, 25, 18, 24, -4.5, 4.5, PL)  # front support
    g.box(-32, 23, 22, 23, -3, 3, PD)
    g.teeth_rail(-30, 23, 23, -2.5, 2.5, BLACK)
    g.box(-34, -29, 22, 23, -4, 4, PLL)
    g.mount("optic", -4, 26, length=18, default=False)
    g.mount("muzzle", 40, 12, bore=2)
    g.use("def_muzzle")
    for c in g.rod(40, 45, 12, 0, 2.4, BLACK):
        slots(c, ("right", "left"), 41, 44, c.ext[2], c.ext[3], 2, 1)
    g.box(40, 45, 14.2, 14.6, -0.5, 0.5, BLACK, 1)
    g.mount("side", 22, 12, 5, length=10, default=False)
    g.use("frame")
    return g
