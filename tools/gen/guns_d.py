"""IWI Desert Eagle (.50 AE) and FN P90 (5.7x28mm), built after the real guns part by part."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, knurl, mag_bones, roll_mark, sling_swivel
from guns_a import (Raked, cham, edge, endmark, engrave, lines, ridges, side_rail, spin, stipple, stud, studs,
                    text, vrod)
from kit import FACES


def deagle():
    """IWI Desert Eagle Mark XIX, .50 AE: a gas-operated pistol whose fixed barrel is the big piece on top, its
    triangular section crowned by the cross-slotted rail with the front sight pinned at the muzzle; the slide
    runs under it, two arms reaching to the muzzle and a heavy rear block with serrations, the slide-mounted
    ambidextrous safety and the ejection port on the right; the steel frame with its external hammer, slide stop,
    barrel latch and magazine button, the big rounded trigger guard; a long raked grip with polymer panels round
    the long single-stack magazine of seven .50 rounds."""
    g = gun("deagle", "pistol", "pistol")
    B = 13.0
    SL = shade(STEEL, 1.02)  # slide
    BR = shade(STEEL, 1.12)  # barrel
    FR = shade(STEEL, 0.84)  # frame
    SLL, SLD = shade(SL, 1.28), shade(SL, 0.7)
    PL, PD = shade(POLY, 1.05), shade(POLY, 0.8)
    PIN = shade(SILVER, 0.6)
    MK = shade(SILVER, 0.82)
    gr = Raked(g, -16, (-3, 4))

    # ------------------------------------------------------------ frame
    fr = g.box(-6, 13, 4, 9, -2.5, 2.5, FR)  # receiver over the trigger
    dc = cham(g, 13, 24, 5, 9, -2.5, 2.5, FR, t=0, b=1)  # the dust cover, forward under the slide
    g.box(23.5, 24.5, 5.5, 8.5, -2, 2, FR, 2)
    for s in (2, -2):
        edge(g, 23, 24.5, 5.5, s, FR, t=0.5)
    g.box(11, 14, 4, 6, -2.5, 2.5, FR)
    g.box(12.5, 14.5, 4.2, 6.2, -2.5, 2.5, FR, 2, inflate=-0.3, tilt=45, pivot=(13.5, 5.2))
    rl = g.teeth_rail(15, 23, 5, -2, 2, FR, down=True)  # accessory rail
    for c in (fr, dc):
        for side in ("right", "left"):
            mark(c, side, c.ext[0], c.ext[1], 8, 9, shade(FR, 0.7))  # the frame rails under the slide
    engrave(dc, "right", 15, 7.5, text(7, 7)[1:], MK)  # serial
    engrave(fr, "left", 1, 6, text(9, 13)[1:], shade(FR, 1.55))  # MAGNUM RESEARCH INC.
    mark(fr, "down", 4, 6, 0, 0, DARK, -1, 1)  # trigger slot
    # the tang (a short beavertail) and the hammer standing behind the slide
    cham(g, -10, -6, 6, 9, -2.5, 2.5, FR, t=0, b=1)
    g.box(-11, -10, 6.5, 8.5, -2, 2, FR, 2)
    g.box(-11.5, -10.5, 6.8, 7.8, -1.5, 1.5, FR, 2, inflate=0.2, tilt=45, pivot=(-11, 7.3))
    hr = Raked(g, 18, (-9.5, 9))
    hr.box(-1, 1, -1, 1, -1, 1, SLD, 2)
    hr.box(-0.8, 0.8, 1, 3.5, -1, 1, SLD, 2)
    sp = hr.box(-1.8, 0.6, 3.5, 5, -1, 1, SLD, 2)  # the rounded spur, checkered
    knurl(sp, "up", -1.8, 0.6, 0, 1, shade(SLD, 1.5))
    hr.box(-2.2, -1.2, 3.7, 4.7, -1, 1, SLD, 1, extra=45, inflate=-0.1)
    spin(g, -9.5, 9, -2.6, 2.6, 0.7, PIN)
    # trigger guard: big, thick and rounded, the front squared off with a gentle hook
    TG = FR
    g.box(0, 12, 0, 1.5, -1.5, 1.5, TG, 2)
    edge(g, 0, 12, 0.3, 0, shade(TG, 0.85), t=1.5)  # its rounded underside
    g.box(11.5, 13.5, 1, 4.5, -1.5, 1.5, TG, 2, tilt=-6, pivot=(12.5, 4.5))
    g.box(11.5, 13.5, -0.1, 1.9, -1.5, 1.5, TG, 2, inflate=0.1, tilt=45, pivot=(12.5, 0.9))
    edge(g, 12.5, 13.8, 2.5, 0, shade(TG, 0.85), t=1.3)
    g.box(10.5, 11.5, 1.5, 2.5, -1.5, 1.5, TG, 1, inflate=-0.15, tilt=45)  # inner fillets
    g.box(0.5, 1.5, 1.5, 2.5, -1.5, 1.5, TG, 1, inflate=-0.15, tilt=45)
    g.box(-1, 1, 0.5, 4, -1.5, 1.5, TG, 2, tilt=-16, pivot=(0, 4))  # its root at the grip
    for s in (1.5, -1.5):  # the outer edges, rounded
        edge(g, 0, 12, 1, s, shade(TG, 1.15), t=0.5)
    # trigger: broad and curved
    TR = shade(STEEL, 1.25)
    g.box(4.5, 5.5, 2.5, 4, -1, 1, TR, 2)
    g.box(4.7, 5.7, 1, 2.5, -1, 1, TR, 2, tilt=18, pivot=(5.2, 2.5))
    g.box(4.4, 5.4, 0.2, 1.2, -1, 1, TR, 1, tilt=40, pivot=(4.9, 1.2))
    # slide stop (left), barrel latch, magazine button, pins
    g.box(3, 10, 8, 9, 2.5, 3.2, FR, 1)
    pad = g.box(1.5, 4, 7.5, 10, 2.7, 3.7, shade(FR, 1.15), 1)
    lines(pad, "left", 1.5, 4, 7.5, 10, 1, shade(FR, 0.7), vertical=True)
    spin(g, 10, 8.3, 2.5, 3.5, 0.8, PIN)
    lt = g.box(15, 18.5, 6.5, 7.5, 2.5, 3.2, shade(FR, 1.2), 1)  # the barrel latch
    spin(g, 15.5, 7, 2.5, 3.6, 1.1, shade(FR, 1.2))
    mark(lt, "left", 17.5, 18.5, 6.5, 7.5, shade(FR, 0.7))
    mb = spin(g, 0, 3, 2.5, 3.5, 1.2, PD)  # magazine release button
    for f, u in ((-3.5, 6.5), (2.5, 6), (7, 6.5), (21, 7)):
        studs(g, f, u, 2.5, PIN, 0.8)

    # ------------------------------------------------------------ grip: steel straps, polymer panels
    gr.box(-7.5, 1.5, -13, 5, -2.5, 2.5, FR)
    gr.box(-8.5, 2.5, -13, 5, -1.5, 1.5, FR)
    for f in (-7.5, 1.5):
        for s in (-1.5, 1.5):
            gr.vedge(f, s, -13, 4.5, FR)
    bs = gr.box(-9, -8, -12, 2, -1.2, 1.2, FR, 2)  # the backstrap, finely grooved
    endmark(bs, "rear", -1.2, 1.2, -12, 2, shade(FR, 0.9))
    for u in range(-11, 2, 2):
        endmark(bs, "rear", -1.2, 1.2, u, u + 1, shade(FR, 0.7))
    for side, (s0, s1), d in (("left", (2.5, 3.5), 1), ("right", (-3.5, -2.5), -1)):
        p = gr.box(-7, 1.5, -12, 3, s0, s1, PL, 2)
        stipple(p, (side,), PL, 1.18)
        for u in (-12.5, 3.5):
            gr.box(-7, 1.5, u - 0.5, u + 0.5, s0, s1, PL, 1, extra=45, inflate=-0.15)
        for f in (-7.5, 2):
            gr.box(f - 0.5, f + 0.5, -12, 3, s0, s1, PL, 1, extra=0, inflate=-0.15)
        sc = gr.box(-3.3, -1.7, -5.3, -3.7, s0 + 0.5 * d, s1 + 0.5 * d, PIN, 1, inflate=-0.1)  # grip screw
        mark(sc, side, -3, -2, -5, -4, shade(SILVER, 0.4))
    rim = gr.box(-9, 3, -14, -13, -3, 3, shade(FR, 0.9), 2)  # the magwell's flared edge
    mark(rim, "down", -7.5, 1.5, 0, 0, DARK, -2, 2)

    # ------------------------------------------------------------ barrel: fixed to the frame
    low = g.box(9, 38, 11, 14, -3, 3, BR)  # the lower body (its flat sides carry the markings)
    up = g.box(9, 38, 14, 16, -2, 2, BR)  # the triangular top
    for s in (2, -2):
        edge(g, 9, 38, 14, s, shade(BR, 1.18), t=1)
        edge(g, 9, 38, 16, s, shade(BR, 1.3), t=0.5)
    engrave(low, "left", 12, 13, ["xx.x.xx.xxx.x.xx...xx.x.xxx.x", "x.x.xx.x.x.xx.x...x.xx.x.x.xx"], MK)  # DESERT EAGLE PISTOL
    engrave(low, "right", 25, 13, ["x.xx.xx", "x.x.x.x"], MK)  # .50 AE
    rail = g.box(11, 34, 16, 17, -1.5, 1.5, shade(BR, 0.9), 2)  # the cross-slotted rail
    crown = g.box(11, 34, 17, 18, -1, 1, shade(BR, 0.95), 2)
    for f in range(12, 33, 2):
        for c in (rail, crown):
            mark(c, "left", f, f + 1, 16, 18, DARK)
            mark(c, "right", f, f + 1, 16, 18, DARK)
            mark(c, "up", f, f + 1, 0, 0, DARK)
    for s in (1.5, -1.5):
        edge(g, 11, 34, 17, s, shade(BR, 1.2), t=0.5)
    g.box(34, 37.5, 16, 17, -1, 1, BR, 2)  # front sight: a blade on its base, pinned
    fs = g.box(35, 37, 17, 19.5, -0.5, 0.5, DARK, 1)
    endmark(fs, "rear", -0.5, 0.5, 18.5, 19.5, WHITE)
    g.box(33.5, 35, 16.8, 18.3, -0.5, 0.5, DARK, 1, tilt=30, pivot=(35, 17))
    spin(g, 36, 16.5, -1.2, 1.2, 0.5, PIN)
    for c in g.rod(37, 38.02, B, 0, 1.15, DARK, 0):  # the bore
        pass
    g.box(3, 9, 11, 15, -2.6, -1.6, GUNMETAL, 2)  # the chamber, seen through the port
    g.box(3, 4, 11.5, 14.5, -2.8, -2, shade(GUNMETAL, 0.7), 1)
    g.muzzle = (38.0, B)

    # ------------------------------------------------------------ slide: a heavy rear block and two arms
    g.part("slide", 12, 12)
    g.use("slide")
    ridges(g, -9, -2, 9, 15, -3, 3, SL)  # rear serrations
    g.box(-9, -2, 15, 16, -2, 2, SL)
    edge(g, -9, -2, 15, 2, SLL)
    edge(g, -9, -2, 15, -2, SLL)
    rear = g.box(-9.5, -9, 9.5, 15.5, -2.5, 2.5, SLD, 1)
    endmark(rear, "rear", -0.5, 0.5, 11.5, 12.5, DARK)  # firing pin
    PF0, PF1 = 3, 9
    m1 = g.box(-2, PF1, 9, 15, -2, 3, SL)
    g.box(-2, PF0, 9, 15, -3, -2, SL)
    g.box(PF0, PF1, 9, 11, -3, -2, SL)
    g.box(-2, PF1, 15, 16, -2, 2, SL)
    edge(g, -2, PF1, 15, 2, SLL)
    edge(g, -2, PF0, 15, -2, SLL)
    mark(m1, "right", PF0, PF1, 11, 15, DARK)
    g.box(PF1 - 1, PF1, 11, 15, -3, -2, SLD, 1)  # the port's front edge
    arms = g.box(PF1, 38, 9, 11, -3, 3, SL)  # the arms under the barrel, to the muzzle
    for s in (3, -3):
        edge(g, PF1, 38, 9, s, shade(SL, 0.85), t=0.5)
    nose = g.box(37, 38, 9, 11, -3, 3, SL, 2)
    endmark(nose, "front", -2.2, -1.2, 9.5, 10.5, DARK)  # the recoil guide rods
    endmark(nose, "front", 1.2, 2.2, 9.5, 10.5, DARK)
    engrave(m1, "left", -1, 13.5, text(8, 31)[1:], MK)  # MADE IN ISRAEL
    engrave(arms, "left", 12, 10.5, text(10, 33)[1:], shade(SL, 1.6))
    # the ambidextrous safety on the slide, set to fire
    for s0, d in ((3, 1), (-4, -1)):
        spin(g, -6, 13.5, s0, s0 + 1, 1.3, SLD)
        lv = g.box(-10, -6, 13, 14, s0 + 0.3 * d, s0 + 1 + 0.3 * d, SLD, 1, tilt=-14, pivot=(-6, 13.5))
        g.box(-10.5, -9, 12.5, 14.5, s0 + 0.4 * d, s0 + 1 + 0.4 * d, shade(SLD, 1.2), 1, tilt=-14, pivot=(-6, 13.5))
    mark(m1, "left", 0, 1, 13, 14, RED)  # the fire dot
    # rear sight: a notch block with white bars in a dovetail
    g.box(-8.5, -4.5, 16, 17, -2.5, 2.5, SLD, 2)
    for s0 in (-2.5, 1.5):
        p = g.box(-8, -5, 17, 19, s0, s0 + 1, DARK, 2)
        endmark(p, "rear", s0, s0 + 1, 17.5, 18.5, WHITE)
    g.box(-8, -5, 17, 17.5, -1.5, 1.5, DARK, 1)
    g.box(-7, -6, 16.3, 17.3, 2.5, 3.1, SILVER, 1, inflate=-0.1)  # windage screw

    # ------------------------------------------------------------ magazine: seven rounds of .50 AE, single stack
    mag_bones(g, -3, -10)
    mg = Raked(g, -16, (-3, 4))
    body = mg.box(-7, 1, -14, 4.5, -2, 2, shade(STEEL, 0.95), 2)
    for k in range(4):  # witness holes on the left
        mark(body, "left", -2, -1, -11 + 3 * k, -10 + 3 * k, DARK)
    mg.box(-7.5, -6.5, -13, 4, -1.2, 1.2, shade(STEEL, 0.95), 2)  # the spine
    bp = mg.box(-8.5, 2, -15.5, -14, -2.5, 2.5, PD, 2)  # baseplate
    mg.box(2, 3, -15.5, -14.5, -2, 2, PD, 2)
    mark(bp, "down", -7, 1, 0, 0, shade(PD, 0.7), -0.5, 0.5)
    g.box(-6, 0, 5, 6, -2, -1, STEEL, 1)  # feed lips and the top round
    g.box(-6, 0, 5, 6, 1, 2, STEEL, 1)
    cartridge(g, -6, 6.3, 0, 7, 1.3)
    g.mag_profile = dict(f0=-7, f1=1, top=-14, length=3, width=4, tilt=-16, pivot=(-3, 4), color=STEEL, kind="pistol")

    g.mount("optic", 22, 18, length=18, default=False)  # on the barrel's rail: it does not move with the slide
    g.mount("muzzle", 38, B, default=False, bore=2.2)
    g.mount("side", 19, 2, length=8, default=False)
    g.use("frame")
    return g


def p90():
    """FN P90 (TR), 5.7x28mm: a bullpup shell of rounded polymer. The firing hand wraps a post with the thumbhole
    behind it and the trigger right in front, the rotary selector dial under the trigger; the guard sweeps
    forward into the support hand's grip and a hand stop under the muzzle. The translucent 50-round magazine lies
    along the top, its rounds crosswise in two staggered rows, latched at the stock; a rail bridge spans it with
    side rails at the front; cocking handles both sides; cases leave through the floor behind the grip; a
    ribbed butt pad; a short barrel with its slotted flash hider."""
    g = gun("p90", "rifle", "ar")
    B = 12.0
    PL = "#3e413d"
    PD, PLL = shade(PL, 0.76), shade(PL, 1.25)
    RL = shade(BLACK, 1.0)
    PIN = shade(SILVER, 0.6)
    MK = shade(PL, 1.8)

    # ------------------------------------------------------------ the shell: receiver body and stock
    body = cham(g, -30, 30, 8, 18, -5, 5, PL, t=2, b=1.5)
    stock = cham(g, -46, -30, 4, 20, -4.5, 4.5, PL, t=2, b=2)
    g.box(-31, -29, 8, 19, -4.5, 4.5, PL, 2)  # where the stock rises behind the magazine
    for c in (body, stock):
        for side in ("right", "left"):
            mark(c, side, c.ext[0] + 1, c.ext[1] - 1, c.ext[2] + 1, c.ext[2] + 2, PD)  # the parting line
    for side in ("left", "right"):  # the cheek recess on the stock, the moulded grip texture
        mark(stock, side, -44, -33, 11, 16, shade(PL, 0.88))
        lines(stock, side, -44, -33, 11, 11.5, 5, shade(PL, 0.72))
    engrave(stock, "left", -43, 9, ["xxx.xx.....xx.xxx.xxx", "x...x.x....x.x.x.x.x.x"], MK)  # FN  P90
    engrave(body, "left", 10, 13, text(10, 41)[1:], MK)  # 5.7x28 / serial
    nose = g.bevel(30, 33, 7, 17, -4.5, 4.5, PL, 1.5)  # the rounded nose round the barrel
    endmark(nose[0], "front", -2, 2, B - 2, B + 2, PD)
    # the butt pad and its spacer
    g.box(-47, -46, 4.5, 19.5, -4, 4, PD, 2)
    pad = g.bevel(-48.5, -47, 4, 20, -4, 4, RUBBER, 1)
    for c in pad[:2]:
        lines(c, "left", -48.5, -47, 5, 19, 2, shade(RUBBER, 1.6))
        lines(c, "right", -48.5, -47, 5, 19, 2, shade(RUBBER, 1.6))
    # sling points: a loop on each side of the stock and of the hand stop
    for s0, d in ((4.5, 1), (-5.5, -1)):
        g.box(-41, -38, 15, 16, s0 + 0.5 * d, s0 + 1 + 0.5 * d, RL, 1)
        g.box(-41, -40, 15, 17, s0, s0 + 1, RL, 1)
        g.box(-39, -38, 15, 17, s0, s0 + 1, RL, 1)

    # ------------------------------------------------------------ the lower: thumbhole, grip, guard, front grip
    st = g.box(-30, -6, 1, 4.5, -3.5, 3.5, PL, tilt=-36, pivot=(-30, 4.5))  # the strut under the thumbhole
    g.box(-30, -6, 3.5, 4.5, -2.5, 2.5, shade(PL, 1.1), 1, tilt=-36, pivot=(-30, 4.5))
    mark(body, "down", -16, -9, 0, 0, DARK, -2.5, 2.5)  # the ejection chute in the floor, behind the grip
    gr = Raked(g, -16, (-2, 8))
    gr.box(-5, 1, -12, 8, -3, 3, PL)
    gr.box(-6, 2, -12, 8, -2, 2, PL)
    for f in (-5, 1):
        for s in (-2, 2):
            gr.vedge(f, s, -12, 7.5, PL)
    for side, (s0, s1) in (("left", (2.5, 3.5)), ("right", (-3.5, -2.5))):
        p = gr.box(-4.5, 0.5, -10, 5, s0, s1, PL, 1)
        stipple(p, (side,), PL, 1.2)
    bar = g.box(-8, 16, -13, -10, -3, 3, PL)  # the floor of the guard, from the grip's foot to the front grip
    for s in (3, -3):
        edge(g, -8, 16, -12.5, s, shade(PL, 0.85), t=0.5)
        edge(g, -8, 16, -10.5, s, shade(PL, 1.15), t=0.5)
    ribs(bar, ("down",), 3, PD)
    fg = g.box(13, 18, -12, 8, -3.5, 3.5, PL, tilt=-28, pivot=(15.5, -12))  # the front grip sweeping forward
    for s in (3, -3):
        g.box(13, 14, -11, 7, s - 0.5, s + 0.5, PL, 2, inflate=0.2, tilt=-28, pivot=(15.5, -12), roll=0)
    for k in range(4):  # finger ridges up its back
        g.box(12.5, 13.5, -8 + 3.5 * k, -7 + 3.5 * k, -2.5, 2.5, shade(PL, 0.85), 1, inflate=0.1,
              tilt=-28, pivot=(15.5, -12))
    g.box(14, 19, -13, -10, -3, 3, PL, 2, inflate=0.1, tilt=-14, pivot=(16, -11.5))  # the turn at the bottom
    hs = g.box(23, 30, 4, 8, -4, 4, PL)  # the hand stop under the muzzle
    g.box(27, 30, 2, 5, -4, 4, PL, 2, inflate=0.1, tilt=20, pivot=(28.5, 4))
    edge(g, 23, 30, 4.5, 3.5, shade(PL, 0.85), t=0.5)
    edge(g, 23, 30, 4.5, -3.5, shade(PL, 0.85), t=0.5)
    for s0, d in ((4, 1), (-5, -1)):  # its sling loops
        g.box(25, 28, 5, 6, s0 + 0.5 * d, s0 + 1 + 0.5 * d, RL, 1)
    # trigger and the rotary selector dial under it (S / 1 / A)
    TR = shade(STEEL, 1.15)
    g.box(2.5, 3.5, 5.5, 8, -0.5, 0.5, TR, 1)
    g.box(2.7, 3.7, 4.5, 6, -0.5, 0.5, TR, 1, tilt=15, pivot=(3.2, 6))
    g.box(2, 4.5, 7.5, 8.5, -1.5, 1.5, PD, 1)
    for c in vrod(g, 3.5, 4.5, 3, 0, 1.9, shade(PL, 1.35)):
        pass
    dial = g.box(2.5, 3.5, 3.4, 4.6, -1.8, 1.8, shade(PL, 1.35), 1)
    mark(dial, "up", 2.5, 3.5, 0, 0, WHITE, -0.5, 0.5)
    g.box(4.2, 5.2, 3.6, 4.4, -0.5, 0.5, shade(PL, 1.35), 1)  # its finger tab
    for f, u in ((-6, 12), (6, 11), (22, 12), (-24, 12)):
        studs(g, f, u, 5, PIN, 0.9)

    # ------------------------------------------------------------ barrel, cocking handles
    g.rod(33, 40, B, 0, 1.4, GUNMETAL)
    g.rod(33, 34.5, B, 0, 2.2, STEEL)  # the barrel's locking collar
    for s0 in (4.5, -5.5):  # the cocking handles' slots
        g.box(6, 24, 9.5, 11, s0 - 0.01, s0 + 1, DARK, 0)
    g.part("bolt", 0, B)
    g.part("charging_handle", 21.5, 10.5, 5)
    g.use("charging_handle")
    for s0, d in ((5, 1), (-6, -1)):
        g.box(20, 23, 9.5, 11, s0, s0 + 1, shade(PL, 0.9), 2)
        kn = g.box(19.5, 23.5, 9, 12, s0 + d, s0 + 1 + d, PL, 2)
        lines(kn, "left" if d > 0 else "right", 19.5, 23.5, 9, 12, 1, PD, vertical=True)
    g.use("frame")

    # ------------------------------------------------------------ the magazine on top: translucent, 50 rounds
    MF0, MF1, MU0, MU1 = -29, 20, 18, 23
    mag_bones(g, (MF0 + MF1) / 2, MU0)
    MG = "#5d6e78"
    mg = g.box(MF0, MF1, MU0, MU1, -3.5, 3.5, MG, 1)
    for side in ("right", "left"):
        mark(mg, side, MF0, MF1, MU0, MU1, shade(MG, 0.92))
        for i in range(46):  # the rounds lie crosswise: their heads (left) or bullet tips (right) in two rows
            f = MF0 + 1 + i
            if f >= MF1 - 3:
                break
            u = MU0 + 1 if i % 2 == 0 else MU0 + 2.5
            mark(mg, side, f, f + 1, u, u + 1.5, BRASS if side == "left" else COPPER)
            if i % 2 == 0:
                mark(mg, side, f, f + 1, u + 1.5, u + 2.5, shade(MG, 0.75))
        mark(mg, side, MF0, MF1, MU1 - 1, MU1, shade(MG, 1.2))
        mark(mg, side, MF0, MF1, MU0, MU0 + 0.5, shade(MG, 0.7))
    mg.front.fill(shade(MG, 1.15))
    lines(mg, "up", MF0 + 1, MF1 - 1, 0, 1, 1, shade(MG, 1.25))
    mark(mg, "up", MF0, MF1, 0, 0, shade(MG, 0.8), -0.5, 0.5)  # the seam of its two halves
    g.box(MF0 - 2, MF0, MU0, MU1 + 0.5, -4, 4, PD, 2)  # the rear cap the catches bite on
    g.box(MF1 - 4, MF1, MU0 - 1, MU1, -3.5, 3.5, shade(MG, 0.8), 2)  # the feed end, where the rounds turn
    g.box(MF1 - 2, MF1 + 1, MU0 + 1, MU1 - 1, -3, 3, PD, 2)
    g.mag_profile = None
    g.use("frame")
    for s0 in (3.5, -4.5):  # the magazine catches on the stock
        g.box(-33, -30, 19, 22, s0, s0 + 1, shade(PL, 1.2), 2)
        lines(g.box(-33.5, -32, 19.5, 22, s0, s0 + 1, shade(PL, 1.35), 1), "left" if s0 > 0 else "right",
              -33.5, -32, 19.5, 22, 1, PD)

    # ------------------------------------------------------------ the rail bridge over the magazine
    fb = cham(g, 20, 30, 17, 23, -5, 5, PL, t=1.5, b=0)  # the front block
    g.box(-9, -5, 18, 23, -4.5, 4.5, PL, 2)  # the rear post
    g.box(-9, -5, 18, 23, -3.6, 3.6, PL, 2)
    plate = g.box(-9, 30, 23, 24, -3.5, 3.5, RL, 2)
    trl = g.teeth_rail(-8, 29, 24, -2.5, 2.5, RL)
    for i, f in enumerate(range(-7, 29, 3)):
        if i % 2 == 0:
            mark(trl[0], "left", f, f + 1, 24, 25, shade(WHITE, 0.75))
    side_rail(g, 21, 29, 20.5, 5, "left", RL)
    side_rail(g, 21, 29, 20.5, -5, "right", RL)
    for f in (-7, 28):
        studs(g, f, 21, 4.5, PIN, 0.8)

    # ------------------------------------------------------------ mounts and the factory flash hider
    g.mount("optic", 8, 27, length=30, default=False)
    g.mount("muzzle", 40, B, bore=1.4)
    g.use("def_muzzle")
    g.rod(40, 41, B, 0, 1.8, RL)
    for c in g.rod(41, 45, B, 0, 2.2, RL):
        slots(c, ("right", "left", "up", "down"), 41.5, 44.5, c.ext[2], c.ext[3], 4, 3)
    g.rod(41, 45.02, B, 0, 1.2, DARK, 0)
    g.muzzle = (45.0, B)
    g.mount("side", 25, 20.5, 8, length=8, default=False)
    g.use("frame")
    return g
