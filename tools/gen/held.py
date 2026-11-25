"""Every item held in the hand as a detailed 3D model (attachables): the guns, the launcher, the knife,
the grenades and the gear.

Models are built at about three times the size they are drawn and the hold animations scale them by
SCALE, so the parts can be a third of a pixel thin. Each item is built in a frame of its own:

    f  forward, along the barrel        (the model's +Y)
    u  up, from the grip to the sights   (the model's -Z, so it ends up on top when held)
    s  sideways, to the gun's left       (the model's +X)

with the middle of the hand on the grip at the origin. The hold animations then put the frame in the
player's hand; tools/gen/viewer.py draws every item held in first and third person to check them.
"""
from __future__ import annotations

import math

from modelkit import Model, shade, mix

GRIP = (-6.0, 13.5, 0.0)  # the middle of the right fist in the player's model space
SCALE = 0.34
SKELETON = [  # the player's bones (no cubes): the item hangs from rightItem
    ("root", None, (0, 0, 0)), ("waist", "root", (0, 12, 0)), ("body", "waist", (0, 24, 0)),
    ("head", "body", (0, 24, 0)), ("leftArm", "body", (5, 22, 0)), ("leftItem", "leftArm", (6, 15, 1)),
    ("rightArm", "body", (-5, 22, 0)), ("rightItem", "rightArm", (-6, 15, 1)),
    ("leftLeg", "root", (1.9, 12, 0)), ("rightLeg", "root", (-1.9, 12, 0)),
]

# ---------------------------------------------------------------- materials
POLYMER = "#2b2c30"
STEEL = "#3d4148"
DARK = "#1d1f23"
GUNMETAL = "#50555d"
TAN = "#9c8462"
OLIVE = "#5b6339"
OD_DARK = "#454b2b"
WOOD = "#7d5130"
RUBBER = "#222326"
BRASS = "#c9a43a"
GLASS = "#4fa7d8"
RED = "#c8302c"
WHITE = "#e9e7df"
SILVER = "#a9afb6"
ORANGE = "#d9762a"


class Held:
    """An item model in the making: boxes placed in the item's own (f, u, s) frame."""

    def __init__(self, key, hold):
        self.key, self.hold = key, hold
        self.model = Model(f"held_{key}", bounds=(4.0, 4.0, 1.0))
        for name, parent, pivot in SKELETON:
            self.model.bone(name, pivot, parent)
        self.bone = self.model.bone("item", GRIP, "rightItem")
        self.bone.scale = SCALE
        self.muzzle = (0.0, 0.0)  # (f, u) of the muzzle, for the flash

    def _place(self, f0, f1, u0, u1, s0, s1):
        """Model-space origin and size of a box spanning f0..f1, u0..u1, s0..s1."""
        size = (max(1, round(s1 - s0)), max(1, round(f1 - f0)), max(1, round(u1 - u0)))
        origin = (GRIP[0] + s0, GRIP[1] + f0, GRIP[2] - u1)
        return origin, size

    def box(self, f0, f1, u0, u1, s0, s1, color, noise=4, inflate=0.0, tilt=0.0, pivot=None, roll=0.0):
        """A box; `tilt` turns it about the sideways axis (positive lifts its front), `roll` about the barrel
        axis. `pivot` is (f, u) (or (f, u, s)) for the turn; it defaults to the box's centre."""
        origin, size = self._place(f0, f1, u0, u1, s0, s1)
        rotation, piv = None, None
        if tilt or roll:
            pf, pu = pivot[:2] if pivot else ((f0 + f1) / 2, (u0 + u1) / 2)
            ps = pivot[2] if pivot and len(pivot) > 2 else (s0 + s1) / 2
            piv = (GRIP[0] + ps, GRIP[1] + pf, GRIP[2] - pu)
            rotation = (-tilt, roll, 0)
        c = self.bone.cube(origin, size, inflate, rotation, piv)
        c.fill(color, noise=noise, seed=len(self.bone.cubes) * 7 + len(self.key))
        return c

    # The faces of a box, by what they face in the item frame.
    @staticmethod
    def up(c):
        return c.front

    @staticmethod
    def down(c):
        return c.back

    @staticmethod
    def fore(c):
        return c.top

    @staticmethod
    def aft(c):
        return c.bottom

    @staticmethod
    def sides(c):
        return (c.right, c.left)

    # ---------------------------------------------------------------- parts
    def cylinder(self, f0, f1, cu, cs, r, color, noise=4):
        """A round part along the barrel: a square box and the same box turned 45 degrees about its axis
        (an octagon in section)."""
        a = self.box(f0, f1, cu - r, cu + r, cs - r, cs + r, color, noise)
        b = self.box(f0, f1, cu - r, cu + r, cs - r, cs + r, shade(color, 0.92), noise, roll=45,
                     pivot=((f0 + f1) / 2, cu, cs), inflate=-0.12 * r)
        return a, b

    def grooves(self, c, every=2, color=None, along="f"):
        """Dark grooves round a box (grips, pump handles): lines across the side and top faces."""
        col = color or shade(c.front.get(0, 0), 0.6)
        for face in (c.front, c.back, c.right, c.left):
            if along == "f":
                for row in range(1, face.h, every):
                    face.hline(row, col)
            else:
                for x in range(1, face.w, every):
                    face.vline(x, col)

    def rail(self, f0, f1, u, s0, s1, color=DARK):
        """A picatinny rail: a strip with cross slots."""
        c = self.box(f0, f1, u, u + 1, s0, s1, color, noise=2)
        for row in range(0, c.front.h, 2):
            c.front.hline(row, shade(color, 1.6))
        return c

    def pistol_grip(self, f0, f1, u_top, length, width, color, angle=16):
        s = width / 2
        c = self.box(f0, f1, u_top - length, u_top, -s, s, color, tilt=-angle, pivot=((f0 + f1) / 2, u_top))
        for face in (c.right, c.left):
            for y in range(0, face.h, 2):
                for x in range(y % 4 // 2, face.w, 2):
                    face.px(x, y, shade(color, 1.25))  # stippling
        return c

    def trigger(self, f0, u0):
        self.box(f0 - 1, f0 + 5, u0 - 1, u0, -0.5, 0.5, DARK, noise=1)  # guard
        self.box(f0 + 4, f0 + 5, u0 - 1, u0 + 1, -0.5, 0.5, DARK, noise=1)
        self.box(f0 + 1, f0 + 2, u0 - 1, u0 + 1, -0.5, 0.5, SILVER, noise=1, inflate=-0.1)  # trigger

    def lens(self, f, u0, u1, s0, s1, color=GLASS):
        c = self.box(f, f + 1, u0, u1, s0, s1, color, noise=0, inflate=-0.05)
        for face in c.faces:
            face.fill(color)
            face.px(0, 0, shade(color, 1.6))
        return c

    def stencil(self, face, rows, color):
        """Paint tiny lettering / markings on a face (rows of '#' and '.')."""
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "#":
                    face.px(x, y, color)

    def finish(self):
        self.model.pack()
        f, u = self.muzzle
        self.bone.locators = {"muzzle": [round(GRIP[0], 3), round(GRIP[1] + f, 3), round(GRIP[2] - u, 3)]}
        return self


# =========================================================================== firearms

def assault_rifle():
    g = Held("assault_rifle", "rifle")
    g.pistol_grip(-3, 1, 3, 9, 3, POLYMER)
    lower = g.box(-4, 10, 2, 6, -2, 2, STEEL)
    upper = g.box(-5, 11, 6, 10, -2, 2, STEEL)
    for face in g.sides(upper):  # ejection port and its cover on the right
        face.fill(DARK, 2, 4, 5, 9)
    g.stencil(lower.left, ["#.#.##", "##..#.", "#.#.##"], shade(STEEL, 1.6))
    g.trigger(-1, 2)
    g.box(3, 5, 7, 9, 2, 3, DARK)  # forward assist
    g.box(-1, 2, 3, 5, -3, -2, SILVER, noise=1)  # magazine release
    mag_top = g.box(4, 9, -3, 2, -1.5, 1.5, TAN)
    mag = g.box(3, 8, -10, -3, -1.5, 1.5, TAN, tilt=14, pivot=(6.5, -3))
    for face in g.sides(mag_top) + g.sides(mag):
        for row in range(1, face.h, 3):
            face.hline(row, shade(TAN, 0.78))
    g.box(2, 9, -11, -9, -2, 2, DARK, tilt=14, pivot=(6.5, -3))  # base plate
    hand = g.box(11, 27, 5, 11, -2.5, 2.5, TAN)
    for face in g.sides(hand):  # cooling slots
        for row in range(2, face.h - 1, 4):
            face.fill(shade(TAN, 0.55), 2, row, 4, row + 2)
    g.rail(-4, 27, 10, -1.5, 1.5)
    g.rail(13, 25, 7, 2.5, 3.5)
    g.rail(13, 25, 7, -3.5, -2.5)
    g.cylinder(27, 35, 8, 0, 1, GUNMETAL)  # barrel
    g.box(28, 30, 6, 12, -1, 1, DARK)  # gas block and front sight post
    g.box(28, 30, 11, 13, -1.5, 1.5, DARK)
    brake = g.box(35, 40, 6, 10, -2, 2, DARK)
    for face in g.sides(brake):
        for x in range(1, face.w, 2):
            face.vline(x, "#0c0d0f")
    g.cylinder(-13, -5, 7.5, 0, 1.5, POLYMER)  # buffer tube
    stock = g.box(-20, -10, 1, 9, -2, 2, TAN)
    g.box(-18, -11, 9, 10, -1.5, 1.5, TAN)  # cheek rest
    g.box(-21, -20, 0, 9, -2, 2, RUBBER, noise=1)  # butt pad
    g.box(-15, -13, 0, 1, -0.5, 0.5, SILVER, noise=1)  # sling loop
    g.box(-6, -4, 9, 10, -3, 3, DARK)  # charging handle
    # red dot sight on the rail
    g.box(2, 8, 11, 12, -1.5, 1.5, DARK)
    body = g.box(2, 8, 12, 16, -2, 2, POLYMER)
    for face in g.sides(body):
        face.fill(shade(POLYMER, 1.4), 2, 1, 4, 3)  # brightness knob
    g.lens(8, 12.5, 15.5, -1.5, 1.5)
    g.lens(1, 12.5, 15.5, -1.5, 1.5, "#6fc4ef")
    g.box(4, 5, 13.5, 14.5, -0.5, 0.5, "#ff3a2a", noise=0, inflate=-0.2)  # the dot
    for face in g.sides(stock):
        face.hline(face.h // 2, shade(TAN, 0.8))
    g.muzzle = (40.0, 8.0)
    return g


def smg():
    g = Held("smg", "rifle")
    g.pistol_grip(-2, 2, 3, 9, 3, POLYMER)
    recv = g.box(-5, 12, 2, 9, -2, 2, POLYMER)
    for face in g.sides(recv):
        face.fill(DARK, 4, 1, 6, 6)  # cocking slot
    g.trigger(0, 2)
    g.box(5, 9, -9, 2, -1.5, 1.5, DARK)  # magazine
    g.box(4, 10, -10, -9, -2, 2, POLYMER)
    g.rail(-3, 11, 9, -1, 1)
    g.box(-3, -1, 10, 12, -1.5, 1.5, DARK)  # rear sight
    g.box(9, 11, 10, 12, -0.5, 0.5, DARK)  # front sight
    g.box(12, 18, 3, 8, -1.5, 1.5, STEEL)  # barrel shroud
    fore = g.box(12, 15, -5, 3, -1, 1, POLYMER)  # vertical foregrip
    g.grooves(fore, 2)
    sup = g.cylinder(18, 30, 5.5, 0, 2.5, DARK)  # suppressor
    for c in sup:
        for face in (c.right, c.left):
            face.hline(1, "#101114")
            face.hline(face.h - 2, "#101114")
    # folding wire stock
    g.box(-15, -5, 7, 8, -2, -1, SILVER, noise=1)
    g.box(-15, -5, 7, 8, 1, 2, SILVER, noise=1)
    g.box(-15, -5, 2, 3, -0.5, 0.5, SILVER, noise=1)
    g.box(-16, -15, 1, 9, -2, 2, RUBBER, noise=1)
    g.box(-6, -5, 8, 9, -2.5, 2.5, DARK)  # cocking handle
    g.muzzle = (30.0, 5.5)
    return g


def lmg():
    g = Held("lmg", "rifle")
    g.pistol_grip(-4, 0, 3, 9, 3, POLYMER)
    recv = g.box(-7, 14, 1, 11, -2.5, 2.5, STEEL)
    g.box(-7, 10, 11, 12, -2, 2, GUNMETAL)  # top cover
    g.rail(-5, 10, 12, -1, 1)
    for face in g.sides(recv):
        face.fill(DARK, 1, 6, 4, 14)
    g.trigger(-2, 1)
    box = g.box(1, 11, -9, 1, -3, 3, OLIVE)  # ammo box
    for face in g.sides(box):
        face.border(OD_DARK)
        face.fill("#d9cf8a", 2, 3, 6, 4)  # stencil
    g.box(4, 8, -10, -9, -1, 1, DARK)  # carry strap loop
    belt = g.box(3, 8, 1, 2, 2.5, 4, BRASS, noise=1)
    for x in range(0, belt.front.w):
        belt.front.vline(x, BRASS if x % 2 else "#7a6420")
    g.cylinder(14, 46, 6.5, 0, 1.5, GUNMETAL)  # barrel
    jacket = g.box(14, 27, 3, 10, -2.5, 2.5, DARK)  # heat shield
    for face in g.sides(jacket) + (jacket.front,):
        for row in range(1, face.h - 1, 3):
            face.fill("#0c0d0f", 1, row, face.w - 1, row + 1)
    g.box(17, 18, 10, 13, -0.5, 0.5, DARK)  # carry handle posts
    g.box(23, 24, 10, 13, -0.5, 0.5, DARK)
    g.box(16, 25, 13, 14, -1, 1, POLYMER)
    g.box(41, 43, 7, 12, -0.5, 0.5, DARK)  # front sight
    g.box(46, 50, 4.5, 8.5, -2, 2, DARK)  # flash hider
    # folded bipod under the barrel
    g.box(26, 40, 3, 4, -2, -1, SILVER, noise=1)
    g.box(26, 40, 3, 4, 1, 2, SILVER, noise=1)
    g.box(38, 41, 3, 6, -2, 2, DARK)
    g.cylinder(-14, -7, 7, 0, 1.5, POLYMER)
    g.box(-22, -12, 1, 10, -2, 2, POLYMER)  # stock
    g.box(-23, -22, 0, 10, -2, 2, RUBBER, noise=1)
    g.box(-3, -1, 12, 14, -1, 1, DARK)  # rear sight
    g.muzzle = (50.0, 6.5)
    return g


def shotgun():
    g = Held("shotgun", "rifle")
    g.pistol_grip(-3, 1, 3, 9, 3, POLYMER)
    recv = g.box(-4, 10, 2, 9, -2, 2, STEEL)
    for face in g.sides(recv):
        face.fill(DARK, 2, 3, 5, 9)  # loading port
    g.trigger(-1, 2)
    g.cylinder(10, 36, 7.5, 0, 1.5, GUNMETAL)  # barrel
    g.cylinder(10, 31, 4, 0, 1.5, DARK)  # tube magazine
    g.box(31, 32, 2.5, 5.5, -1.5, 1.5, STEEL)  # magazine cap
    pump = g.box(14, 24, 1.5, 6.5, -2.5, 2.5, POLYMER)
    g.grooves(pump, 2)
    g.box(35, 36, 9, 10, -0.5, 0.5, SILVER, noise=0)  # bead sight
    saddle = g.box(0, 9, 3, 8, 2, 3, DARK)  # side saddle with spare shells
    for x in range(1, saddle.left.w - 1, 2):
        saddle.left.vline(x, RED, 1, saddle.left.h - 3)
        saddle.left.vline(x, BRASS, saddle.left.h - 3, saddle.left.h - 1)
    g.box(-19, -4, 1, 9, -2, 2, POLYMER)  # stock
    g.box(-20, -19, 0, 9, -2, 2, RUBBER, noise=1)
    g.box(-4, -2, 9, 10, -1, 1, DARK)
    g.muzzle = (36.0, 7.5)
    return g


def sniper_rifle():
    g = Held("sniper_rifle", "rifle")
    g.pistol_grip(-6, -2, 4, 9, 3, TAN, angle=22)
    g.box(-8, 6, 4, 9, -1.5, 1.5, STEEL)  # action
    fore = g.box(4, 20, 2, 8, -2, 2, TAN)  # forend
    for face in g.sides(fore):
        face.hline(face.h // 2, shade(TAN, 0.8))
    g.trigger(-4, 3)
    g.box(0, 4, 0, 4, -1, 1, DARK)  # magazine
    g.cylinder(20, 50, 6, 0, 1, GUNMETAL)  # barrel
    brake = g.box(50, 55, 4, 8, -1.5, 1.5, DARK)
    for face in g.sides(brake):
        for x in range(1, face.w, 2):
            face.vline(x, "#0c0d0f")
    # bolt handle with a ball knob on the right
    g.box(-3, -2, 6, 7, -5, -1.5, SILVER, noise=1)
    g.box(-4, -1, 5, 8, -6, -4, SILVER, noise=1)
    g.box(-26, -8, 0, 8, -2, 2, TAN)  # buttstock
    g.box(-22, -10, 8, 10, -1.5, 1.5, TAN)  # cheek riser
    g.box(-27, -26, -1, 8, -2, 2, RUBBER, noise=1)
    g.box(-19, -15, 0, 2, -2.5, 2.5, DARK)  # rear monopod
    # scope
    g.box(-1, 1, 9, 11, -1, 1, DARK)
    g.box(9, 11, 9, 11, -1, 1, DARK)
    g.cylinder(-5, 14, 12.5, 0, 1.5, POLYMER)
    g.cylinder(14, 21, 12.5, 0, 2.5, POLYMER)  # objective bell
    g.cylinder(-10, -5, 12.5, 0, 2, POLYMER)  # eyepiece
    g.lens(21, 10.5, 14.5, -2, 2)
    g.lens(-11, 11, 14, -1.5, 1.5, "#6fc4ef")
    g.box(3, 6, 14, 16, -1, 1, DARK)  # elevation turret
    g.box(3, 6, 11.5, 13.5, -3.5, -1.5, DARK)  # windage turret
    # folded bipod
    g.box(18, 32, 1, 2, -2, -1, DARK)
    g.box(18, 32, 1, 2, 1, 2, DARK)
    g.muzzle = (55.0, 6.0)
    return g


def service_pistol():
    g = Held("service_pistol", "pistol")
    g.pistol_grip(-3, 2, 4, 11, 3, POLYMER, angle=18)
    slide = g.box(-5, 12, 5, 10, -1.5, 1.5, STEEL)
    for face in g.sides(slide):
        for x in range(1, 4):
            pass
        for row in range(face.h - 5, face.h - 1):  # rear serrations
            if row % 2 == 0:
                face.hline(row, DARK)
        face.fill(DARK, 1, 6, 3, 10)  # ejection port
    g.box(-2, 11, 3, 5, -1.5, 1.5, POLYMER)  # frame
    g.rail(5, 10, 2, -1, 1)
    g.box(12, 13, 7, 9, -0.5, 0.5, "#0c0d0f", noise=0)  # muzzle
    g.trigger(1, 3)
    g.box(-4, -2, 10, 11, -1, 1, DARK)  # rear sight
    g.box(10, 11, 10, 11, -0.5, 0.5, DARK)  # front sight
    g.box(-6, -5, 7, 9, -0.5, 0.5, DARK)  # hammer
    g.box(-6, 0, -8, -7, -1.5, 1.5, DARK, tilt=-18, pivot=(-0.5, 4))  # magazine base
    g.muzzle = (13.0, 8.0)
    return g


def rocket_launcher():
    g = Held("rocket_launcher", "launcher")
    tube = g.cylinder(-22, 18, 8, 0, 4, OLIVE)
    for c in tube:
        for face in (c.right, c.left, c.front, c.back):
            face.hline(face.h - 12, OD_DARK)
            face.hline(face.h - 30, OD_DARK)
            face.fill("#d9cf8a", 1, 10, 3, 20)  # stencil band
    g.cylinder(-27, -22, 8, 0, 5, DARK)  # rear blast cone
    g.cylinder(18, 22, 8, 0, 3, OLIVE)  # warhead body
    g.cylinder(22, 27, 8, 0, 2, OD_DARK)
    g.cylinder(27, 30, 8, 0, 1, DARK)  # nose
    g.pistol_grip(-2, 2, 4, 9, 3, POLYMER)
    g.trigger(0, 3)
    fg = g.box(6, 9, -3, 4, -1, 1, POLYMER)  # fore grip
    g.grooves(fg, 2)
    sight = g.box(-2, 7, 9, 14, 4, 6, DARK)
    for face in (sight.top, sight.bottom):
        face.fill(GLASS)
    g.box(-12, -2, 2, 4, -3, 3, RUBBER, noise=1)  # shoulder pad
    for f0 in (-15, 8):
        g.box(f0, f0 + 1, 3.5, 12.5, -4.5, 4.5, DARK, noise=1)  # straps
    g.muzzle = (30.0, 8.0)
    return g


# =========================================================================== close quarters and gear

def combat_knife():
    g = Held("combat_knife", "blade")
    h = g.box(-5, 3, -1.5, 1.5, -1, 1, RUBBER)
    g.grooves(h, 2)
    g.box(-6, -5, -2, 2, -1.5, 1.5, STEEL)  # pommel
    g.box(3, 4, -3, 3, -1.5, 1.5, STEEL)  # guard
    blade = g.box(4, 15, -1.5, 2, -0.5, 0.5, SILVER, noise=1)
    for face in g.sides(blade):
        face.vline(0, "#e8ecef")  # edge
        for row in range(face.h - 4, face.h):
            if row % 2:
                face.px(face.w - 1, row, DARK)  # serrations on the spine
    g.box(15, 17, -1, 1.5, -0.5, 0.5, SILVER, noise=1)
    g.box(17, 18, -0.5, 1, -0.5, 0.5, "#e8ecef", noise=0)
    return g


def frag_grenade():
    g = Held("frag_grenade", "grenade")
    g.box(-3, 3, -3, 3, -2, 2, OLIVE)
    g.box(-3, 3, -2, 2, -3, 3, OLIVE)
    core = g.box(-2, 4, -2, 2, -2, 2, OD_DARK)
    g.box(4, 6, -1, 1, -1, 1, SILVER, noise=1)  # fuse
    g.box(3, 7, 2, 3, -0.5, 0.5, SILVER, noise=1)  # spoon
    g.box(1, 4, 3, 4, -0.5, 0.5, SILVER, noise=1)
    g.box(5, 6, 1, 3, 1, 3, "#d8d8d8", noise=0)  # pin ring
    for face in g.sides(core):
        face.hline(1, "#d9cf8a")
    return g


def smoke_grenade():
    g = Held("smoke_grenade", "grenade")
    can = g.cylinder(-4, 5, 0, 0, 2.5, "#7d8288")
    for c in can:
        for face in (c.right, c.left, c.front, c.back):
            face.fill("#e9e7df", 0, 3, face.w, 5)  # white band
    g.box(5, 7, -1, 1, -1, 1, SILVER, noise=1)
    g.box(3, 8, 2.5, 3.5, -0.5, 0.5, SILVER, noise=1)
    g.box(6, 7, 1, 3, 1, 3, "#d8d8d8", noise=0)
    return g


def medkit():
    g = Held("medkit", "gear")
    bag = g.box(-4, 6, -2, 7, -3, 3, "#b02a26")
    for face in (bag.front, bag.back, bag.right, bag.left):
        face.border("#7e1a17")
    for face in g.sides(bag) + (g.up(bag),):
        cx, cy = face.w // 2, face.h // 2
        face.fill(WHITE, cx - 1, cy - 3, cx + 1, cy + 3)
        face.fill(WHITE, cx - 3, cy - 1, cx + 3, cy + 1)
    g.box(-2, 4, 7, 8, -0.5, 0.5, DARK)  # handle
    g.box(-4, 6, 2, 3, -3.5, 3.5, "#2a2a2a", noise=1)  # zip
    return g


def ammo_box():
    g = Held("ammo_box", "gear")
    can = g.box(-5, 6, -3, 6, -3, 3, OLIVE)
    for face in g.sides(can):
        face.border(OD_DARK)
        face.fill("#d9cf8a", 2, 3, face.w - 2, 4)
        face.fill("#d9cf8a", 2, 5, face.w - 4, 6)
    g.box(-5, 6, 6, 7, -3.5, 3.5, OD_DARK)  # lid
    g.box(-1, 2, 7, 8, -0.5, 0.5, DARK)  # handle
    g.box(5, 6, 3, 6, -3.5, 3.5, DARK)  # latch
    return g


def repair_tool():
    g = Held("repair_tool", "pistol")
    g.pistol_grip(-2, 2, 3, 8, 3, "#3a3a3e")
    tank = g.cylinder(-6, 6, 6, 0, 2.5, "#c8302c")
    for c in tank:
        c.top.fill(SILVER)
    g.box(6, 9, 5, 7, -1, 1, BRASS, noise=1)  # valve
    g.cylinder(9, 18, 6, 0, 0.7, SILVER)  # nozzle
    g.box(17, 19, 5, 7, -1, 1, DARK)
    g.box(-1, 1, 9, 10, -2.5, 2.5, BRASS, noise=1)  # knob
    g.muzzle = (19.0, 6.0)
    return g


def binoculars():
    g = Held("binoculars", "gear")
    for s in (-3, 3):
        g.cylinder(-2, 8, 4, s, 2, "#3b4030")
        g.lens(8, 2.5, 5.5, s - 1.5, s + 1.5)
        g.cylinder(-4, -2, 4, s, 1.5, RUBBER)
    g.box(0, 6, 3, 5, -1, 1, DARK)  # bridge
    g.box(2, 4, 5, 6, -0.5, 0.5, SILVER, noise=1)  # focus wheel
    return g


def field_radio():
    g = Held("field_radio", "gear")
    body = g.box(-4, 8, -2, 2, -2.5, 2.5, "#3b4030")
    face = g.up(body)
    face.fill("#7fd08a", 1, 2, face.w - 1, 5)  # screen
    for y in range(7, face.h - 1, 2):
        for x in range(1, face.w - 1, 2):
            face.px(x, y, DARK)  # keypad
    g.box(8, 10, -1, 1, 1, 2, DARK)  # knob
    g.cylinder(8, 22, 0, -1.5, 0.5, RUBBER)  # antenna
    g.box(-5, -4, -2.5, 2.5, -3, 3, DARK)
    return g


ALL = {
    "service_pistol": service_pistol, "smg": smg, "assault_rifle": assault_rifle, "lmg": lmg, "shotgun": shotgun,
    "sniper_rifle": sniper_rifle, "rocket_launcher": rocket_launcher, "combat_knife": combat_knife,
    "frag_grenade": frag_grenade, "smoke_grenade": smoke_grenade, "medkit": medkit, "ammo_box": ammo_box,
    "repair_tool": repair_tool, "binoculars": binoculars, "field_radio": field_radio,
}

def build_all():
    return {key: fn().finish() for key, fn in ALL.items()}
