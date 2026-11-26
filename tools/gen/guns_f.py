"""Barrett M82A1 (.50 BMG)."""
from __future__ import annotations

import math

from gunbase import *  # noqa: F401,F403
from gunbase import gun, mag_bones, cartridge, sling_swivel, roll_mark
from guns_c import _seg_light, scyl, stud, vcyl
from kit import LOW, mark, ribs

PAD_R = "#26272a"     # recoil pad rubber
BBL = "#2b2d31"       # the barrel's black finish
SLV = "#50554b"       # the perforated barrel sleeve
UPPER = PARK          # parkerised sheet-steel receivers
MAGC = "#2a2c30"      # the magazine


def yaw_box(g, f0, f1, u0, u1, s0, s1, color, yaw, pivot, noise=2, bone=None):
    """A box turned `yaw` degrees about the up axis through pivot (f, s); positive swings its left (+s) end
    forward."""
    c = g.box(f0, f1, u0, u1, s0, s1, color, noise, bone=bone)
    pf, ps = pivot
    c.rotation = (0, 0, yaw)
    c.pivot = g.at(pf, (u0 + u1) / 2, ps)
    return c


def sleeve(g, f0, f1, cu, r, color, holes, n=12, t=1):
    """A round sleeve of n flat facets along f, drilled with holes in staggered rows: holes = (h0, h1, length,
    pitch) puts holes of `length` every `pitch` between h0 and h1, every other facet half a pitch on. Through
    the holes the dark inside (and whatever runs in the sleeve) shows. At LOW detail, a plain rod."""
    if LOW[0]:
        return g.rod(f0, f1, cu, 0, r, color)
    h0, h1, hl, pitch = holes
    w = max(1, math.ceil(2 * r * math.tan(math.pi / n) - 0.05))
    out = []
    for i in range(n):
        ang = 360.0 * i / n
        cuts = []
        h = h0 + (pitch / 2 if i % 2 else 0)
        while h + hl <= h1:
            cuts.append((h, h + hl))
            h += pitch
        edges = [f0] + [v for c in cuts for v in c] + [f1]
        for a, b in zip(edges[::2], edges[1::2]):
            if b - a < 0.5:
                continue
            c = g.box(a, b, cu + r - t, cu + r, -w / 2, w / 2, color, 2, roll=ang if ang else 0.0,
                      pivot=((a + b) / 2, cu, 0))
            _seg_light(c, color, ang, 2, g.seed + i * 13 + int(a), shade(color, 0.45))
            out.append(c)
    return out


def arrow_brake(g, points, cu, half, back, height, th, color, bone=None):
    """The M82's double-chamber brake: V-shaped baffles, their points forward at `points` (rear, middle, nose)
    and their ends swept `back`, closed top and bottom by chevron plates, the sides open between them."""
    ang = math.degrees(math.atan2(back, half))
    ln = math.hypot(back, half) + 0.6  # a little over the middle so the two halves meet
    hu = height
    out = []
    centres = [p - back / 2 - th / 2 for p in points]
    for k in (1, -1):  # the left half, then the right
        cs = k * half / 2
        for cf in centres:  # baffles
            c = yaw_box(g, cf - th / 2, cf + th / 2, cu - hu, cu + hu, cs - ln / 2, cs + ln / 2, color, -k * ang,
                        (cf, cs), bone=bone)
            c.back.fill(shade(color, 0.6))
            for face in (c.right, c.left):  # a lit outer edge
                face.vline(face.w - 1 if face is c.right else 0, shade(color, 1.4))
            out.append(c)
        for a, b in zip(centres, centres[1:]):  # top and bottom plates of each chamber
            fm, d = (a + b) / 2, (b - a) * math.cos(math.radians(ang)) / 2 + th / 2
            for u0, u1, inner in ((cu + hu - th, cu + hu, "back"), (cu - hu, cu - hu + th, "front")):
                c = yaw_box(g, fm - d, fm + d, u0, u1, cs - ln / 2, cs + ln / 2, color, -k * ang, (fm, cs),
                            bone=bone)
                getattr(c, inner).fill(shade(DARK, 1.2))
                out.append(c)
    return out


def barrett():
    """Barrett M82A1: tall pressed-steel upper receiver with the ejection port showing the bolt carrier, the
    lower receiver with the magazine well, big trigger guard and pistol grip, a long top rail and the folding
    carry handle, the perforated barrel sleeve with the fluted heavy barrel running through it, the
    double-chamber arrowhead muzzle brake, the folding bipod clamped under the sleeve, the stock with its cheek
    rest, thick recoil pad and rear monopod, the 10-round box magazine and the charging handle on the right."""
    g = gun("barrett", "rifle", "ar")
    A = 15  # the bore line
    hi = not LOW[0]
    # ================================================================ upper receiver
    # the right side is a skin plate laid over a recessed body, so the ejection port is a real opening
    up = g.bevel(-28, 44, 10, 22.5, -4.5, 5.5, UPPER, 1.5, edges=("tl", "tr", "bl"))
    core = up[0]  # u 11.5..21, s -4.5..5.5: its right face is the floor of the port
    mark(core, "right", 14, 31, 12.5, 19, DARK)
    skins = [g.box(-28, 14, 10, 21, -5.5, -4.5, UPPER), g.box(31, 44, 10, 21, -5.5, -4.5, UPPER),
             g.box(14, 31, 10, 12.5, -5.5, -4.5, UPPER), g.box(14, 31, 19, 21, -5.5, -4.5, UPPER)]
    for c in skins:
        mark(c, "right", c.ext[0], c.ext[1], 11, 11.5, shade(UPPER, 0.65))  # where the upper laps the lower
    mark(skins[2], "right", 14, 31, 12, 12.5, shade(UPPER, 1.35))  # the port's lit lower lip
    mark(skins[0], "right", -9, 8, 16, 17, DARK)  # the charging handle's slot
    mark(skins[0], "right", -9, 8, 17, 17.5, shade(UPPER, 1.3))
    mark(core, "left", -28, 44, 11, 11.5, shade(UPPER, 0.65))
    if hi:
        # the bolt carrier and bolt seen through the port
        bc = g.box(15, 30.5, 13.5, 18, -5, -4.5, "#5a5f66", 1)
        mark(bc, "right", 15, 26, 17.5, 18, shade("#5a5f66", 1.4))
        mark(bc, "right", 26, 27, 13.5, 18, DARK)  # the bolt head's gap
        for u in (14, 16.5):
            mark(bc, "right", 27.5, 30.5, u, u + 1, shade("#5a5f66", 1.3))  # locking lugs
        g.box(28, 30.5, 18.2, 18.8, -5.2, -4.7, STEEL, 1)  # extractor
        # markings and the stamped stiffening rib along each side
        roll_mark(core, "left", -18, 8, 17.5, shade(SILVER, 0.6))
        roll_mark(core, "left", 10, 22, 17.5, shade(SILVER, 0.6))
        mark(core, "left", -24, 42, 14.5, 15, shade(UPPER, 1.25))
        mark(core, "left", -24, 42, 14, 14.5, shade(UPPER, 0.7))
        for c in skins[:2]:
            mark(c, "right", c.ext[0] + 1, c.ext[1] - 1, 14.5, 15, shade(UPPER, 1.25))
        # the pressed stiffening rib along the top of each side
        g.box(-24, 42, 19.5, 20.5, 5.5, 6, shade(UPPER, 1.1), 1)
        g.box(-24, 42, 19.5, 20.5, -6, -5.5, shade(UPPER, 1.1), 1)
        # the barrel's recoil spring guides end in screws on each side of the front
        for f in (38, 41):
            stud(g, f, 19, 5.5, "left", shade(SILVER, 0.6))
            stud(g, f, 19, -5.5, "right", shade(SILVER, 0.6))
        g.box(-29, -28, 11.5, 21, -3.5, 3.5, DARK, 1)  # the rear face where the stock's buffer seats
    # ================================================================ lower receiver, grip, trigger
    lo = g.bevel(-28, 32, 4, 10.5, -4.5, 4.5, UPPER, 1)
    for c in lo[:2]:
        mark(c, "left", -28, 32, 9.5, 10, shade(UPPER, 1.3))
    # the magazine well: a frame round the magazine's top
    g.box(7, 9, 1.5, 5, -4.5, 4.5, UPPER, 2)
    g.box(28, 30, 1.5, 5, -4.5, 4.5, UPPER, 2)
    for s0 in (-4.5, 3.5):
        w = g.box(9, 28, 2, 5, s0, s0 + 1, UPPER, 2)
        mark(w, "left" if s0 > 0 else "right", 9, 28, 2, 2.5, shade(UPPER, 0.7))
    g.box(6.5, 9, 1, 2, -4.6, 4.6, shade(UPPER, 0.85), 1)  # its flared mouth
    g.box(28, 30.5, 1, 2, -4.6, 4.6, shade(UPPER, 0.85), 1)
    # trigger guard: a big loop for a gloved finger
    g.box(-6, 7, -1.5, 0, -1.5, 1.5, UPPER, 1)
    g.box(5.5, 7, -1.5, 4.5, -1.5, 1.5, UPPER, 1)
    g.box(-6, -4, -1.5, 1.5, -1.5, 1.5, UPPER, 1)
    g.box(-0.5, 1, 1.5, 4.5, -0.5, 0.5, SILVER, 1)  # trigger blade, curved
    g.box(0, 1.5, -0.2, 1.8, -0.5, 0.5, SILVER, 1, tilt=-25, pivot=(0.75, 1.8))
    g.pistol_grip(-13, -4, 5, 16, 7, POLY, angle=14)
    if hi:
        g.box(-11, -6, 7, 9, 4.5, 5.2, STEEL, 1)  # safety: a lever on the left above the grip
        g.box(-11, -9, 5.5, 8, 4.5, 5.2, STEEL, 1, tilt=-25, pivot=(-10, 8))
        stud(g, -8, 8, 4.5, "left", SILVER)
        mark(lo[0], "left", -9, -7, 9, 10, WHITE)  # F / S index marks
        mark(lo[0], "left", -5, -4, 8, 9, RED)
        g.box(4, 7, 2, 4, -1.5, 1.5, STEEL, 1)  # the magazine catch lever behind the well
        g.box(5, 7, 1, 2, -2.5, 2.5, STEEL, 1)
        for f in (-24, 30):  # the receivers' lock pins
            stud(g, f, 9, 4.5, "left", shade(SILVER, 0.7), d=1.6)
            stud(g, f, 9, -4.5, "right", shade(SILVER, 0.7), d=1.6)
        stud(g, -2, 7, 4.5, "left")  # trigger and hammer pins
        stud(g, 3, 7, 4.5, "left")
        sling_swivel(g, 34, 10, 0, True)
    # ================================================================ top rail and carry handle
    g.box(-26, 36, 22.5, 23.5, -2.5, 2.5, BLACK, 2)  # the rail's riser
    g.teeth_rail(-26, 36, 23.5, -3, 3, BLACK)
    if hi:
        for f in (-20, 0, 20):
            stud(g, f, 23, 2.5, "left", shade(SILVER, 0.6))  # rail screws
    # the M82A1's folding carry handle, standing up just ahead of the rail
    g.box(36, 47, 22.5, 24, -3, 3, BLACK, 2)  # base
    for f0 in (36.5, 44.5):
        scyl(g, f0 + 1, 25, -3, 3, 1.4, BLACK)  # hinge knuckles
    g.box(37, 39, 25, 30, -1.5, 1.5, BLACK, 2, tilt=-10, pivot=(38, 25))  # rear arm
    g.box(44, 46, 25, 30, -1.5, 1.5, BLACK, 2, tilt=10, pivot=(45, 25))  # front arm
    hb = g.bevel(36, 47, 29.5, 32.5, -2, 2, BLACK, 1)
    if hi:
        for c in hb[:2]:
            ribs(c, ("up", "right", "left"), 2, shade(BLACK, 0.7))
    # ================================================================ charging handle on the right
    g.part("charging_handle", 6, 16.5, -5.5)
    g.box(4.5, 7.5, 15.5, 17.5, -8, -5, BLACK, 1, bone="charging_handle")  # stalk out of the slot
    knob = scyl(g, 6, 16.5, -11.5, -8, 2.3, BLACK, bone="charging_handle")
    for c in knob:
        ribs(c, ("right",), 2, shade(BLACK, 1.4))
    scyl(g, 6, 16.5, -12, -11.5, 1.6, shade(BLACK, 0.8), bone="charging_handle")
    # ================================================================ barrel and its perforated sleeve
    g.use("frame")
    g.rod(40, 119, A, 0, 2.3, shade(BBL, 0.75))  # the fluted barrel: a core and eight lands
    if hi:
        for ang in (0, 45, 90, 135):
            c = g.box(46, 113, A - 3, A + 3, -0.5, 0.5, BBL, 2, inflate=-0.15, roll=ang if ang else 0.0,
                      pivot=(80, A, 0))
            for face in (c.front, c.back):
                face.vline(face.w // 2, shade(BBL, 1.5))
    g.rod(113, 119, A, 0, 2.9, BBL)  # the plain muzzle end the brake screws onto
    g.rod(117, 119, A, 0, 2.6, shade(BBL, 1.2))
    # the sleeve: twelve flat facets drilled through in staggered rows, the barrel showing through the holes
    R = 5.5
    g.rod(44, 47, A, 0, 4.5, shade(UPPER, 0.9))  # the bushing where it leaves the receiver
    g.rod(46, 74, A, 0, 3.1, "#151618")  # its dark inside, seen through the holes
    sleeve(g, 46, 74, A, R, SLV, holes=(47.5, 67.5, 3, 5))
    g.rod(73.5, 75, A, 0, 3.4, shade(SLV, 0.75))  # the front bushing round the barrel
    g.muzzle = (134.0, float(A))
    # ================================================================ magazine: 10 rounds of .50 BMG
    mag_bones(g, 9, 5)
    mg = g.box(9.5, 27.5, -9, 5, -3.5, 3.5, MAGC)
    for side in ("right", "left"):
        mark(mg, side, 10, 27, 4, 5, shade(MAGC, 0.7))
    for s0 in (-3.9, 3.4):  # the pressed reinforcing ribs along each side
        for u0 in (-6, -1):
            g.box(11, 26, u0, u0 + 1, s0, s0 + 0.5, shade(MAGC, 1.25), 1)
    g.box(8.5, 28.5, -11, -9, -4, 4, shade(MAGC, 0.8))  # floor plate
    if hi:
        g.box(27.5, 28.5, -10, -2, -2, 2, shade(MAGC, 0.9), 1)  # the spine for the bullets' tips
        g.box(9, 11, -11.5, -11, -3, 3, shade(MAGC, 0.7), 1)  # floor plate catch
        g.box(9.5, 27.5, 5, 6, -3.5, -2.5, shade(MAGC, 0.85), 1)  # feed lips with the top round between them
        g.box(9.5, 27.5, 5, 6, 2.5, 3.5, shade(MAGC, 0.85), 1)
        cartridge(g, 10, 5.3, -0.8, 17.5, 1.4)
    g.mag_profile = dict(f0=9.5, top=5, width=7, segs=[(0, 14)], color=MAGC, kind="sniper")
    # ================================================================ factory sights (def_optic)
    g.mount("optic", 4, 26.5, length=36)
    g.use("def_optic")
    # rear: a flip-up aperture on the back of the rail
    g.box(-24, -18, 26.5, 28, -3, 3, BLACK, 2)
    g.box(-22.5, -20.5, 28, 32.5, -2, 2, BLACK, 2)
    ap = g.box(-22, -21, 30, 32, -1, 1, BLACK, 1)
    mark(ap, "left", -22, -21, 30.5, 31.5, DARK)
    g.box(-21, -20, 28, 30, 2, 3.5, STEEL, 1)  # its windage knob
    # front: a folding post on the front of the rail
    g.box(30, 35, 26.5, 28, -3, 3, BLACK, 2)
    g.box(31.5, 33.5, 28, 30, -2.5, 2.5, BLACK, 2)
    g.box(31.5, 33.5, 30, 33, -2.5, -1.5, BLACK, 1)  # the post's guard ears
    g.box(31.5, 33.5, 30, 33, 1.5, 2.5, BLACK, 1)
    g.box(32, 33, 30, 33.5, -0.5, 0.5, STEEL, 1)  # the post
    # ================================================================ double-chamber arrowhead brake (def_muzzle)
    g.mount("muzzle", 119, A, bore=2.9)
    g.use("def_muzzle")
    BR = "#2a2c2f"
    g.rod(119, 122, A, 0, 3.6, BR)  # the threaded collar
    arrow_brake(g, (122.5, 128, 134), A, 7.0, 2.0, 5.0, 1.5, BR)
    g.box(132.5, 133.5, A - 1.5, A + 1.5, -1.5, 1.5, "#0c0c0d", 0, inflate=-0.1)  # the bore at the nose
    # ================================================================ folding bipod (def_underbarrel)
    g.mount("underbarrel", 69, A - R)
    g.use("def_underbarrel")
    g.box(65.5, 72.5, A - R - 2, A - R + 0.5, -4.5, 4.5, BLACK, 2)  # the clamp under the sleeve
    for k in (1, -1):
        s0 = 5.3 if k > 0 else -6.3
        g.box(66, 72, A - 3.5, A + 2, s0, s0 + 1, BLACK, 1)  # its straps up the sides
    g.box(66, 72, A + 1, A + 2, -6.3, 6.3, BLACK, 1, inflate=-0.05)
    stud(g, 69, A - 1, 6.3, "left", shade(SILVER, 0.7), d=1.6)  # clamp bolt
    stud(g, 69, A - 1, -6.3, "right", shade(SILVER, 0.7), d=1.6)
    g.box(66, 72, A - R - 4.5, A - R - 2, -3.5, 3.5, BLACK, 2)  # the yoke
    scyl(g, 70.5, A - R - 3.2, -5.5, 5.5, 1.3, STEEL)  # the legs' hinge pin
    if hi:
        g.box(67, 70, A - R - 5, A - R - 4.5, -1, 1, STEEL, 1)  # spring latch
    LEG = "#2e3034"
    for s in (-4, 4):
        u = A - R - 3.2
        scyl(g, 70.5, u, s - 1.2, s + 1.2, 1.6, LEG)  # knuckle
        g.rod(71, 95, u, s, 1.3, LEG)  # the leg tube, folded forward along the barrel
        for c in g.rod(92, 96, u, s, 1.7, shade(LEG, 1.25)):  # the leg's lock collar
            ribs(c, ("right", "left", "up", "down"), 2, shade(LEG, 0.8))
        g.rod(96, 103, u, s, 0.9, shade(SILVER, 0.8))  # the extension
        foot = g.box(102, 105, u - 4.5, u + 2.5, s - 1.5, s + 1.5, RUBBER, 1)  # the hinged spade foot
        ribs(foot, ("right", "left"), 2, shade(RUBBER, 1.5))
        g.box(105, 106, u - 4, u + 2, s - 1.2, s + 1.2, shade(RUBBER, 0.8), 1)
        stud(g, 103.5, u, s + 1.5, "left", shade(SILVER, 0.7))
        stud(g, 103.5, u, s - 1.5, "right", shade(SILVER, 0.7))
    # ================================================================ stock (def_stock)
    g.mount("stock", -28, 13)
    g.use("def_stock")
    # the buffer housing: the upper's line carried back to the pad, its top chamfered like the receiver
    hb_ = g.bevel(-55, -28, 12, 22.5, -4.5, 4.5, UPPER, 1.5, edges=("tl", "tr"))
    for c in hb_[:2]:
        for side in ("right", "left"):
            mark(c, side, -55, -28, 12, 12.5, shade(UPPER, 0.65))
    # the lower part: deep at the grip, its underside sweeping down to the heel of the pad
    g.bevel(-36, -28, 3, 12.5, -4, 4, UPPER, 1, edges=("bl", "br"))
    lean = math.degrees(math.atan2(3.5, 22))
    g.box(-57, -34, 3.5, 17, -4, 4, UPPER, 3, tilt=lean, pivot=(-34, 3.5))
    g.box(-57, -34, 2.5, 3.5, -3.5, 3.5, shade(UPPER, 0.8), 2, tilt=lean, pivot=(-34, 3.5))  # its rounded belly
    if hi:
        for side, s in (("left", 4.5), ("right", -4.5)):
            stud(g, -48, 17, s, side, shade(SILVER, 0.7), d=1.6)  # the rear lock pin
            stud(g, -33, 8, s, side, shade(SILVER, 0.6))
        sling_swivel(g, -40, 2.5, 0, True)
    # the cheek rest: a black pad on top, thicker on the left where the cheek lies
    cr = g.bevel(-51, -34, 22, 25.5, -3.5, 5, POLY, 1.2)
    g.box(-51, -36, 16, 23, 4.5, 5.6, POLY, 2)  # its flap down the left side
    g.box(-36, -30, 19, 25.5, -3, 4.5, POLY, 2, tilt=-40, pivot=(-36, 25.5))  # its front, sloping down
    if hi:
        for c in cr[:2]:
            for x in range(1, c.front.w, 2):
                c.front.px(x, 2, shade(POLY, 1.3))
        for f in (-48, -38):
            g.box(f - 1, f + 1, 21.5, 26, 5, 5.5, DARK, 1)  # the straps that hold it
    # the butt plate and the thick ribbed recoil pad
    g.box(-57, -55, 0.5, 23, -5, 5, BLACK, 2)
    pad = g.bevel(-63, -57, 0, 23.5, -5.5, 5.5, PAD_R, 1.5)
    for c in pad[:2]:
        for side in ("right", "left"):
            for u in range(2, 22, 3):
                mark(c, side, -62, -58, u, u + 1, shade(PAD_R, 0.6))
    g.box(-63.5, -62.5, 2, 21.5, -4, 4, shade(PAD_R, 0.85), 2)  # the pad's face
    # the rear monopod: housing, a screw leg with its knurled thumbwheel, and the foot
    g.box(-52, -45, -1.5, 2.5, -3, 3, BLACK, 2)
    g.box(-51, -46, -2.5, -1.5, -2, 2, shade(BLACK, 0.8), 1)
    vcyl(g, -48.5, 0, -8, 0, 0.9, SILVER)
    wheel = vcyl(g, -48.5, 0, -4.5, -2.5, 2.6, BLACK)
    for c in wheel:
        for face in (c.right, c.left):
            for y in range(0, face.h, 2):
                face.hline(y, shade(BLACK, 1.6))
    g.box(-51.5, -45.5, -10, -8, -2.5, 2.5, RUBBER, 2)
    g.box(-50.5, -46.5, -8, -7, -1.5, 1.5, BLACK, 1)
    g.use("frame")
    return g
