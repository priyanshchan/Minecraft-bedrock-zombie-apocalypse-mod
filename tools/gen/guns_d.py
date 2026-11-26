"""IWI Desert Eagle (.50 AE) and FN P90 (5.7x28mm), built after the real guns part by part."""
from __future__ import annotations

import math

from gunbase import *  # noqa: F401,F403
from gunbase import cartridge, curved_mag, gun, knurl, mag_bones, roll_mark, sling_swivel
from guns_a import (Raked, boss, cham, edge, endmark, engrave, lines, ridges, side_rail, spin, stipple, stud,
                    studs, text, vrod)
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
    for s0 in (2.3, -3.3):  # the frame's rails, standing a hair proud under the slide
        g.box(-6, 24, 8.3, 9, s0, s0 + 1, shade(FR, 1.15), 1)
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
    for s0 in (-1.3, 0.3):  # the hammer's flanks round the firing-pin face
        hr.box(-0.6, 0.6, -0.5, 2.5, s0, s0 + 1, shade(SLD, 1.15), 1, inflate=-0.1)
    boss(g, -9.5, 9, -2.6, 2.6, 1, PIN)
    # trigger guard: big, thick and rounded, the front squared off with a gentle hook
    TG = FR
    g.box(0, 12, 0, 1.5, -1.5, 1.5, TG, 2)
    edge(g, 0, 12, 0.3, 0, shade(TG, 0.85), t=1.5)  # its rounded underside
    g.box(11.5, 13.5, 1, 4.5, -1.5, 1.5, TG, 2, tilt=-6, pivot=(12.5, 4.5))
    g.box(11.5, 13.5, -0.1, 1.9, -1.5, 1.5, TG, 2, inflate=0.1, tilt=45, pivot=(12.5, 0.9))
    gf = edge(g, 12.5, 13.8, 2.5, 0, shade(TG, 0.85), t=1.3)
    fg = g.box(13, 14, 1.5, 4, -1, 1, TG, 1, tilt=-6, pivot=(13.5, 4))  # the grooved front of the guard
    lines(fg, "up", 13, 14, 0, 1, 1, TG)
    for k in range(3):
        g.box(13.2, 14.2, 1.7 + k, 2.2 + k, -1, 1, shade(TG, 0.7), 0, tilt=-6, pivot=(13.5, 4))
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
    stud(g, 10, 8.3, 3.2, "left", PIN, 1)
    lt = g.box(15, 18.5, 6.5, 7.5, 2.5, 3.2, shade(FR, 1.2), 1)  # the barrel latch
    boss(g, 15.5, 7, 2.5, 3.6, 3, shade(FR, 1.2))
    mark(lt, "left", 17.5, 18.5, 6.5, 7.5, shade(FR, 0.7))
    mb = boss(g, 0, 3, 2.5, 3.6, 3, shade(FR, 1.25))  # magazine release button, chequered
    mark(mb[2], "left", -1, 1, 2, 4, shade(FR, 0.95))
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
        rimp = gr.box(-7.5, 2, -12.5, 3.5, s0 - 0.5 * d, s1 - 0.5 * d, shade(PL, 0.85), 1)  # its raised border
        sc = gr.box(-3, -2, -5, -4, s0 + 0.5 * d, s1 + 0.5 * d, shade(SILVER, 0.45), 1, inflate=-0.05)  # grip screw
    rim = gr.box(-9, 3, -14, -13, -3, 3, shade(FR, 0.9), 2)  # the magwell's flared edge
    mark(rim, "down", -7.5, 1.5, 0, 0, DARK, -2, 2)

    # ------------------------------------------------------------ barrel: fixed to the frame
    low = g.box(9, 38, 11, 14, -3, 3, BR)  # the lower body (its flat sides carry the markings)
    up = g.box(9, 38, 14, 16, -2, 2, BR)  # the triangular top
    for s in (2, -2):
        edge(g, 9, 38, 14, s, shade(BR, 1.18), t=1)
        edge(g, 9, 38, 16, s, shade(BR, 1.3), t=0.5)
    ME = shade(BR, 1.38)  # markings
    engrave(low, "left", 13, 13, ["x.x.xx.x.x.xx...x.x.xx.x.x"], ME)  # DESERT EAGLE PISTOL
    engrave(low, "left", 13, 12, ["x.x..x.xx"], shade(BR, 1.25))  # MARK XIX
    engrave(low, "right", 26, 13, [".x.xx..xx"], ME)  # .50 AE
    rail = g.box(11, 34, 16, 17, -1.5, 1.5, shade(BR, 0.9), 2)  # the cross-slotted rail: a base and its teeth
    for f in range(11, 33, 2):
        g.box(f, f + 1, 17, 18, -1.5, 1.5, shade(BR, 1.05), 1)
    g.box(11, 34, 17, 17.5, -0.5, 0.5, shade(BR, 0.6), 0)
    g.box(34, 37.5, 16, 17, -1, 1, BR, 2)  # front sight: a blade on its base, pinned
    fs = g.box(35, 37, 17, 19.5, -0.5, 0.5, DARK, 1)
    endmark(fs, "rear", -0.5, 0.5, 18.5, 19.5, WHITE)
    g.box(33.5, 35, 16.8, 18.3, -0.5, 0.5, DARK, 1, tilt=30, pivot=(35, 17))
    spin(g, 36, 16.5, -1.2, 1.2, 0.5, PIN)
    g.rod(37.5, 38.2, B, 0, 1.6, shade(BR, 1.2))  # the crowned muzzle
    g.rod(37.6, 38.25, B, 0, 1.0, DARK, 0)  # the bore
    g.box(37.5, 38.2, 11, 12, -2.5, 2.5, shade(BR, 0.85), 1)  # the barrel's lower lip at the muzzle
    for s in (2.5, -2.5):
        edge(g, 30, 38, 11, s, shade(BR, 0.8), t=0.5)
    ch = g.box(3.5, 9, 11.5, 14.5, -2.3, -1.3, shade(GUNMETAL, 1.1), 2)  # the chamber hood, through the port
    mark(ch, "right", 3.5, 5, 11.5, 14.5, shade(GUNMETAL, 0.6))  # the breech face's shadow
    g.box(3, 4, 11, 15, -2.4, -1.4, DARK, 0)
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
    g.box(PF0, PF1, 15, 16, -2.5, -2, SLD, 1)  # the port's upper lip
    g.box(PF1 - 1, PF1, 11, 15, -3, -2, SLD, 1)  # the port's front edge
    arms = g.box(PF1, 38, 9, 11, -3, 3, SL)  # the arms under the barrel, to the muzzle
    for s in (3, -3):
        edge(g, PF1, 38, 9, s, shade(SL, 0.85), t=0.5)
    nose = g.box(37, 38, 9, 11, -3, 3, SL, 2)
    for s in (-1.7, 1.7):  # the recoil guide rods' ends
        g.rod(37.9, 38.5, 10, s, 0.6, shade(SILVER, 0.7))
    engrave(m1, "left", -1, 13.5, text(8, 31)[1:], MK)  # MADE IN ISRAEL
    engrave(arms, "left", 12, 10.5, text(10, 33)[1:], shade(SL, 1.6))
    # the ambidextrous safety on the slide, set to fire
    for s0, d in ((3, 1), (-4, -1)):
        boss(g, -6, 13.5, s0, s0 + 1, 3, SLD)
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
    g.box(-9, -4, 15.6, 16.4, -2.6, 2.6, SLD, 1)  # the dovetail's base

    # ------------------------------------------------------------ magazine: seven rounds of .50 AE, single stack
    mag_bones(g, -3, -10)
    mg = Raked(g, -16, (-3, 4))
    body = mg.box(-7, 1, -14, 4.5, -2, 2, shade(STEEL, 0.95), 2)
    for k in range(4):  # witness holes on the left
        mark(body, "left", -2, -1, -11 + 3 * k, -10 + 3 * k, DARK)
    mg.box(-7.5, -6.5, -13, 4, -1.2, 1.2, shade(STEEL, 0.95), 2)  # the spine
    bp = mg.box(-8.5, 2, -15.5, -14, -2.5, 2.5, PD, 2)  # baseplate
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
    TAN16 = math.tan(math.radians(16))
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
    engrave(stock, "left", -43, 10, ["xxx.x.x...xx.xxx.xxx", "x...xxx...x..x.x.x.x"], shade(PL, 1.35))  # FN  P90
    engrave(body, "left", 8, 12, text(10, 41)[1:], shade(PL, 1.35))  # 5.7x28 / serial
    nose = g.bevel(30, 33, 7, 17, -4.5, 4.5, PL, 1.5)  # the rounded nose round the barrel
    endmark(nose[0], "front", -2, 2, B - 2, B + 2, PD)
    # the butt pad and its spacer
    g.box(-47, -46, 4.5, 19.5, -4, 4, PD, 2)
    for u0 in (6, 16):  # the pad's locking tabs
        g.box(-47.5, -45, u0, u0 + 2, -4.5, 4.5, PD, 1)
    pad = g.bevel(-48.5, -47, 4, 20, -4, 4, RUBBER, 1)
    for c in pad[:2]:
        lines(c, "left", -48.5, -47, 5, 19, 2, shade(RUBBER, 1.6))
        lines(c, "right", -48.5, -47, 5, 19, 2, shade(RUBBER, 1.6))
    # sling points: a loop on each side of the stock and of the hand stop
    for s0, d in ((4.5, 1), (-5.5, -1)):
        g.box(-41, -38, 15, 16, s0 + 0.5 * d, s0 + 1 + 0.5 * d, RL, 1)
        g.box(-41, -40, 15, 17, s0, s0 + 1, RL, 1)
        g.box(-39, -38, 15, 17, s0, s0 + 1, RL, 1)

    # ------------------------------------------------------------ the lower: one moulding, built row by row
    # Its side profile: the stock's underside sloping down to the grip's foot with the thumbhole cut through it,
    # the raked grip, the floor of the guard, the front grip sweeping forward up to the hand stop.
    GB = lambda u: -6 - (8 - u) * TAN16  # the grip's back and front edges
    GF = lambda u: 1.5 - (8 - u) * TAN16
    FB = lambda u: 12.5 + (u + 14) * 0.445  # the front grip's back and front edges (24 degrees forward)
    FF = lambda u: 19.5 + (u + 14) * 0.445

    def solid(f, u):
        if u >= 8:
            return False
        if f < -17:  # the stock's underside, down to a line sloping from the butt to the grip's foot
            return u >= 2 - (f + 46) * 16 / 37 and f >= -46.5 + max(0, 3 - u) * 0.6
        if (f + 12.5) ** 2 / 4.6 ** 2 + (u - 2.2) ** 2 / 5.2 ** 2 <= 1:  # the thumbhole
            return False
        if f < GB(u):
            return u >= 2 - (f + 46) * 16 / 37
        if f <= GF(u):
            return u >= -14 + (0.6 if f < GB(u) + 1.2 else 0)
        if u < -10:  # the floor, its front corner rounded into the front grip
            return f <= FF(u) - (1.6 if u < -13 else 0)
        if f < FB(u):  # the trigger opening
            return False
        if f <= FF(u):
            return True
        return u >= 3 and f <= 30 - (1.5 if u < 4 else 0)  # the hand stop

    lower = []
    for k in range(-14, 8):
        u = k + 0.5
        runs, cur = [], None
        for fi in range(-47, 31):
            on = solid(fi + 0.5, u)
            if on and cur is None:
                cur = fi
            if not on and cur is not None:
                runs.append((cur, fi))
                cur = None
        if cur is not None:
            runs.append((cur, 31))
        for f0, f1 in runs:
            cuts = [f0] + [x for x in (-17,) if f0 < x < f1] + [f1]
            for a0, a1 in zip(cuts, cuts[1:]):
                w = 4.5 if a1 <= -17 else 3.5
                c = g.box(a0, a1, k, k + 1, -w, w, PL, 2)
                lower.append(c)
    for c in lower:  # lit like the body's sides; a fine grain on the grip and front grip
        f0, f1, u0 = c.ext[0], c.ext[1], c.ext[2]
        for side in ("left", "right"):
            face = getattr(c, FACES[side])
            for y in range(face.h):
                col = shade(face.get(0, y), 1.12)
                if u0 < 4 and f0 > -12 and (y + int(u0)) % 2 == 0:
                    col = shade(col, 1.1)
                face.px(0, y, col)
    mark(body, "down", -15, -9, 0, 0, DARK, -2.5, 2.5)  # the ejection chute in the thumbhole's roof
    gr = Raked(g, -16, (-2, 8))
    for side, (s0, s1) in (("left", (3, 4)), ("right", (-4, -3))):  # the grip's textured panels
        p = gr.box(-5, 0.5, -11, 5, s0, s1, PL, 1)
        stipple(p, (side,), PL, 1.22)
    for side, s0 in (("left", 3), ("right", -4)):  # the front grip's textured panels
        p = g.box(13.5, 18.5, -11, 4, s0, s0 + 1, PL, 1, tilt=-24, pivot=(16, -14))
        stipple(p, (side,), PL, 1.22)
    for s in (3.5, -3.5):  # the floor's rounded edges
        edge(g, -6, 14, -14, s, shade(PL, 0.9), t=0.7)
        edge(g, 3, 12, -10, s, shade(PL, 1.2), t=0.6)
    for h in (-1.5, -6):  # finger ridges on the front strap
        gr.box(1, 2, h - 0.5, h + 0.5, -2.5, 2.5, PD, 2, extra=45, inflate=0.207)
    for s0, d in ((3, 1), (-4, -1)):  # the hand stop's sling loops
        g.box(25, 28, 4.5, 5.5, s0 + 1 * d, s0 + 1 + 1 * d, RL, 1)
        g.box(25, 26, 4.5, 5.5, s0 + 0.5 * d, s0 + 1 + 0.5 * d, RL, 1)
        g.box(27, 28, 4.5, 5.5, s0 + 0.5 * d, s0 + 1 + 0.5 * d, RL, 1)
    # trigger and the rotary selector dial under it (S / 1 / A)
    TR = shade(STEEL, 1.15)
    g.box(4, 5, 5.5, 8, -0.5, 0.5, TR, 1)
    g.box(4.2, 5.2, 4.5, 6, -0.5, 0.5, TR, 1, tilt=15, pivot=(4.7, 6))
    g.box(3, 6, 7.5, 8.5, -1.5, 1.5, PD, 1)
    vrod(g, 3.5, 4.5, 4.5, 0, 1.9, shade(PL, 1.35))
    dial = g.box(4, 5, 3.4, 4.6, -1.8, 1.8, shade(PL, 1.35), 1)
    mark(dial, "up", 4, 5, 0, 0, WHITE, -0.5, 0.5)
    g.box(5.7, 6.7, 3.6, 4.4, -0.5, 0.5, shade(PL, 1.35), 1)  # its finger tab
    for f, u in ((-6, 12), (6, 11), (22, 12), (-24, 12)):
        studs(g, f, u, 5, PIN, 0.9)

    # ------------------------------------------------------------ barrel, cocking handles
    g.rod(33, 40, B, 0, 1.4, GUNMETAL)
    g.rod(33, 34.5, B, 0, 2.2, STEEL)  # the barrel's locking collar
    for s in (2.5, -2.5):
        g.box(33, 34.5, B - 0.5, B + 0.5, s - 0.5, s + 0.5, STEEL, 1)  # its lugs
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
    MF0, MF1, MU0, MU1 = -29, 20, 18, 24
    mag_bones(g, (MF0 + MF1) / 2, MU0)
    MG = "#5d6e78"
    mg = g.box(MF0, MF1, MU0, MU1, -3.5, 3.5, MG, 1)
    for side in ("right", "left"):
        mark(mg, side, MF0, MF1, MU0, MU1, shade(MG, 0.9))
        RC = shade(BRASS, 0.95) if side == "left" else shade(COPPER, 0.9)  # heads on the left, tips on the right
        f = MF0 + 1
        k = 0
        while f + 2 <= MF1 - 4:  # the rounds lie crosswise in two staggered rows
            u = MU0 + 1 if k % 2 == 0 else MU0 + 3
            mark(mg, side, f, f + 2, u, u + 2, RC)
            mark(mg, side, f + 1, f + 2, u, u + 1, shade(RC, 0.7))
            mark(mg, side, f, f + 1, u + 1, u + 2, shade(RC, 1.2))
            f += 1.5 if k % 2 == 0 else 1.5
            f = round(f)
            k += 1
        mark(mg, side, MF0, MF1, MU1 - 1, MU1, shade(MG, 1.25))
    mg.front.fill(shade(MG, 1.15))
    lines(mg, "up", MF0 + 1, MF1 - 1, 0, 1, 1, shade(MG, 1.25))
    for s0 in (1.5, -2.5):  # the two ribs along its top
        g.box(MF0 + 1, MF1 - 4, MU1, MU1 + 0.5, s0, s0 + 1, shade(MG, 1.15), 1)
    g.box(MF0, MF0 + 3, MU0 + 0.5, MU1 - 0.5, -3.3, 3.3, shade(MG, 0.6), 1)  # the follower and its spring
    for s0 in (2.8, -3.8):  # the catch notches at the rear
        g.box(MF0 + 0.5, MF0 + 2, MU0 + 2, MU1 - 1, s0, s0 + 1, DARK, 0, inflate=-0.1)
    mark(mg, "up", MF0, MF1, 0, 0, shade(MG, 0.8), -0.5, 0.5)  # the seam of its two halves
    g.box(MF0 - 2, MF0, MU0, MU1, -4, 4, PD, 2)  # the rear cap the catches bite on
    for s0 in (3.5, -4.5):  # the ribbed pull tabs either side of it
        lines(g.box(MF0 - 1.5, MF0 + 2, MU0 + 1, MU1 - 1, s0, s0 + 1, PD, 1), "left" if s0 > 0 else "right",
              MF0 - 1.5, MF0 + 2, MU0 + 1, MU1 - 1, 1, shade(PD, 0.7), vertical=True)
    g.box(MF1 - 4, MF1, MU0 - 1, MU1, -3.5, 3.5, shade(MG, 0.8), 2)  # the feed end, where the rounds turn
    g.box(MF1 - 2, MF1 + 1, MU0 + 1, MU1 - 1, -3, 3, PD, 2)
    g.mag_profile = None
    g.use("frame")
    for s0 in (3.5, -4.5):  # the magazine catches on the stock
        g.box(-33, -30, 19, 22, s0, s0 + 1, shade(PL, 1.2), 2)
        lines(g.box(-33.5, -32, 19.5, 22, s0, s0 + 1, shade(PL, 1.35), 1), "left" if s0 > 0 else "right",
              -33.5, -32, 19.5, 22, 1, PD)

    # ------------------------------------------------------------ the rail bridge over the magazine
    fb = cham(g, 20, 30, 17, 24, -5, 5, PL, t=1.5, b=0)  # the front block
    g.box(-9, -5, 18, 24, -4.5, 4.5, PL, 2)  # the rear post
    plate = g.box(-9, 30, 24, 25, -3.5, 3.5, RL, 2)
    for s in (3.5, -3.5):
        edge(g, -9, 30, 24.5, s, shade(RL, 0.9), t=0.5)
    trl = g.teeth_rail(-8, 29, 25, -2.5, 2.5, RL)
    for i, f in enumerate(range(-7, 29, 3)):
        if i % 2 == 0:
            mark(trl[0], "left", f, f + 1, 25, 26, shade(WHITE, 0.75))
    side_rail(g, 21, 29, 20.5, 5, "left", RL)
    side_rail(g, 21, 29, 20.5, -5, "right", RL)
    for f in (-7, 22, 28):
        studs(g, f, 21.5, 4.5, PIN, 0.8)
    for f in (-6, 27):  # the rail's bolts from above
        for s in (-2.8, 2.8):
            g.box(f - 0.5, f + 0.5, 24.8, 25.2, s - 0.5, s + 0.5, PIN, 1)
    endmark(fb, "front", -3, 3, 18, 22, shade(PL, 0.8))

    # ------------------------------------------------------------ mounts and the factory flash hider
    g.mount("optic", 8, 28, length=30, default=False)
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
