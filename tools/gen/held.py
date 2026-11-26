"""Every item held in the hand as a detailed 3D model (attachables): the guns, the launcher, the knife, the
grenades and the gear - and the Red Fang's own guns that the AI soldiers carry.

Units and frame
---------------
Guns are built in quarter pixels (one unit = 1/4 px) and the hold animations scale the bone `item` by
SCALE (third person) or FP_SCALE (first person). Each item is built in a frame of its own:

    f  forward, along the barrel        (the model's +Y)
    u  up, from the grip to the sights   (the model's -Z)
    s  sideways, to the gun's left       (the model's +X); the ejection port is on the right (-s)

with the middle of the hand on the grip at the origin.

Bones (the same names on every gun, so animations and future attachments line up)
-------------------------------------------------------------------------------
    item                      hold transform (rotation, position, scale) per view
      gun                     the whole weapon; reload/jam animations tilt it
        frame                 the static parts (not "body": that name is the player's torso)
        mag > def_mag         the magazine (drops out on reloads); extended mags will sit beside def_mag
        bolt, charging_handle, slide, pump, cover, rocket, shell   moving parts (where the gun has them)
        att_optic > def_optic         optic mount on the top rail; iron sights / the factory scope
        att_muzzle > def_muzzle       muzzle thread; the factory flash hider or brake
        att_underbarrel > def_underbarrel   under rail; bipods where the gun has one
        att_side                      side rail (lasers, lights)
        att_stock > def_stock         the stock
A future attachment adds its boxes to the att_* bone and hides the def_* part beside it (see
docs/attachments.md). Held.mounts records where each mount is, per gun.
"""
from __future__ import annotations

import math

from modelkit import Model, shade

GRIP = (-6.0, 13.5, 0.0)  # the middle of the right fist in the player's model space
SCALE = 0.25  # third person: quarter-pixel units
FP_SCALE = 0.28  # first person: a little larger, as guns read better close to the eye
SKELETON = [  # the player's bones (no cubes): the item hangs from rightItem
    ("root", None, (0, 0, 0)), ("waist", "root", (0, 12, 0)), ("body", "waist", (0, 24, 0)),
    ("head", "body", (0, 24, 0)), ("leftArm", "body", (5, 22, 0)), ("leftItem", "leftArm", (6, 15, 1)),
    ("rightArm", "body", (-5, 22, 0)), ("rightItem", "rightArm", (-6, 15, 1)),
    ("leftLeg", "root", (1.9, 12, 0)), ("rightLeg", "root", (-1.9, 12, 0)),
]

# ---------------------------------------------------------------- materials
BLACK = "#3b3e44"     # anodised receiver
POLY = "#34363b"      # black polymer
STEEL = "#4b5058"     # parkerised steel
DARK = "#1b1c1f"      # bores, slots, shadows
GUNMETAL = "#666d76"
TAN = "#a48c68"       # coyote polymer
TAN_D = "#7d6a4d"
OD = "#5b6339"
OD_D = "#434929"
WOOD = "#82502c"
WOOD_D = "#5c3618"
RUBBER = "#1f2023"
BRASS = "#c9a43a"
COPPER = "#b5703c"
SILVER = "#aab0b7"
CHROME = "#d6dbdf"
GLASS = "#4fb0e6"
RED = "#c8302c"
WHITE = "#e9e7df"


class Held:
    """An item model in the making: boxes placed in the item's own (f, u, s) frame, in named bones."""

    def __init__(self, key, hold):
        self.key, self.hold = key, hold
        self.model = Model(f"held_{key}", bounds=(5.0, 5.0, 1.0))
        for name, parent, pivot in SKELETON:
            self.model.bone(name, pivot, parent)
        self.bones = {}
        item = self.model.bone("item", GRIP, "rightItem")
        item.scale = SCALE
        self.bones["item"] = item
        self.bones["gun"] = self.model.bone("gun", GRIP, "item")
        self.part("frame", 0, 0)
        self.cur = self.bones["frame"]
        self.muzzle = (0.0, 0.0)
        self.mounts = {}
        self.seed = sum(map(ord, key))

    # ------------------------------------------------------------ bones
    def at(self, f, u, s=0.0):
        """Model-space point of an item-frame point."""
        return (GRIP[0] + s, GRIP[1] + f, GRIP[2] - u)

    def part(self, name, f, u, s=0.0, parent="gun"):
        assert name not in {b[0] for b in SKELETON}, f"{name} is a player bone name"
        if name not in self.bones:
            self.bones[name] = self.model.bone(name, self.at(f, u, s), parent)
        return self.bones[name]

    def use(self, name):
        """Boxes made from now on go into bone `name`."""
        self.cur = self.bones[name]
        return self

    def mount(self, slot, f, u, s=0.0, length=0, default=True):
        """An attachment mount: bone att_<slot> pivoting at (f, u, s), with an optional def_<slot> child."""
        att = self.part(f"att_{slot}", f, u, s)
        att.locators = {slot: [round(v, 3) for v in self.at(f, u, s)]}
        self.mounts[slot] = {"f": f, "u": u, "s": s, "length": length}
        if default:
            self.part(f"def_{slot}", f, u, s, parent=f"att_{slot}")
        return att

    # ------------------------------------------------------------ boxes
    def box(self, f0, f1, u0, u1, s0, s1, color, noise=3, inflate=0.0, tilt=0.0, pivot=None, roll=0.0, bone=None):
        """A box spanning f0..f1, u0..u1, s0..s1. `tilt` turns it about the sideways axis (positive lifts its
        front), `roll` about the barrel axis; `pivot` is (f, u) or (f, u, s), by default the box's centre."""
        size = (max(1, round(s1 - s0)), max(1, round(f1 - f0)), max(1, round(u1 - u0)))
        origin = (GRIP[0] + s0, GRIP[1] + f0, GRIP[2] - (u0 + size[2]))
        rotation, piv = None, None
        if tilt or roll:
            pf, pu = pivot[:2] if pivot else ((f0 + f1) / 2, (u0 + u1) / 2)
            ps = pivot[2] if pivot and len(pivot) > 2 else (s0 + s1) / 2
            piv = self.at(pf, pu, ps)
            rotation = (tilt, roll, 0)  # Bedrock: +x lifts the front of a forward-pointing box
        target = self.bones[bone] if bone else self.cur
        c = target.cube(origin, size, inflate, rotation, piv)
        c.ext = (f0, f0 + size[1], u0, u0 + size[2], s0, s0 + size[0])
        paint(c, color, noise, self.seed + len(target.cubes) * 7)
        return c

    def rod(self, f0, f1, cu, cs, r, color, noise=2, bone=None):
        """A round bar along the barrel axis: its section drawn as a pixel circle of radius r (in units)."""
        rows = []
        n = int(math.ceil(r))
        for y in range(-n, n):
            yc = y + 0.5
            if abs(yc) >= r:
                continue
            hw = round(math.sqrt(r * r - yc * yc))
            if hw <= 0:
                continue
            if rows and rows[-1][2] == hw and rows[-1][1] == y:
                rows[-1][1] = y + 1
            else:
                rows.append([y, y + 1, hw])
        out = []
        for y0, y1, hw in rows:
            out.append(self.box(f0, f1, cu + y0, cu + y1, cs - hw, cs + hw, color, noise, bone=bone))
        if out:  # light along the top, shadow underneath: a round look
            out[-1].front.fill(shade(color, 1.18))
            out[-1].front.noise(noise, self.seed)
            out[0].back.fill(shade(color, 0.7))
        return out

    def rail(self, f0, f1, u, s0, s1, color=BLACK, bone=None):
        """A picatinny rail: a base and a slotted top, cross slots every 3 units."""
        self.box(f0, f1, u, u + 1, s0 + 1, s1 - 1, color, 2, bone=bone)
        top = self.box(f0, f1, u + 1, u + 3, s0, s1, color, 2, bone=bone)
        for row in range(1, top.front.h, 3):
            top.front.hline(row, DARK)
            for face in (top.right, top.left):
                face.hline(row, DARK)
        return top

    def pistol_grip(self, f0, f1, u_top, length, width, color, angle=16, stipple=True):
        s = width / 2
        g = self.box(f0, f1, u_top - length, u_top, -s, s, color, 3, tilt=-angle, pivot=((f0 + f1) / 2, u_top))
        self.box(f0 - 1, f1, u_top - length - 1, u_top - length + 1, -s, s, shade(color, 0.85), 2,
                 tilt=-angle, pivot=((f0 + f1) / 2, u_top))
        if stipple:
            for face in (g.right, g.left):
                for y in range(1, face.h - 1):
                    for x in range(2 + (y % 2), face.w - 2, 2):
                        face.px(x, y, shade(color, 1.35))
            for y in range(2, g.top.h, 3):  # finger grooves on the front strap
                g.top.hline(y, shade(color, 0.6))
        return g

    def trigger(self, f0, u0, width=2):
        s = width / 2
        self.box(f0, f0 + 10, u0 - 1, u0, -s, s, DARK, 1)  # guard bottom
        self.box(f0 + 9, f0 + 10, u0 - 1, u0 + 3, -s, s, DARK, 1)  # guard front
        return self.box(f0 + 3, f0 + 5, u0 - 1, u0 + 3, -0.5, 0.5, SILVER, 1)  # trigger blade

    def lens(self, f, u0, u1, s0, s1, color=GLASS, depth=1, bone=None):
        c = self.box(f, f + depth, u0, u1, s0, s1, color, 0, bone=bone)
        for face in c.faces:
            face.fill(color)
            for i in range(min(face.h, face.w)):
                face.px(i, i, shade(color, 1.5))  # a glint across the glass
            face.px(0, 0, WHITE)
        return c

    def screw(self, c, side, f, u):
        mark(c, side, f, f + 1, u, u + 1, shade(SILVER, 0.8))

    def finish(self):
        self.model.pack()
        f, u = self.muzzle
        self.bones["gun"].locators = {"muzzle": [round(v, 3) for v in self.at(f, u)]}
        return self


# ---------------------------------------------------------------- painting

def paint(c, color, noise, seed):
    """Fill a box with a material lit from above: the top face bright, the sides shading down from a
    highlighted top edge to a dark bottom edge, the underside and the far end in shadow, fine grain."""
    for i, face in enumerate(c.faces):
        face.fill(color)
        if noise:
            face.noise(noise, seed + i)

    def scale_face(face, fn):
        for xx in range(face.w):
            for yy in range(face.h):
                face.px(xx, yy, shade(face.get(xx, yy), fn(xx, yy, face.w, face.h)))

    # side faces: texture x runs bottom -> top on the right face and top -> bottom on the left face
    def side(top_at_right):
        def fn(x, y, w, h):
            t = x / max(1, w - 1) if top_at_right else 1 - x / max(1, w - 1)
            f = 0.86 + 0.2 * t
            if w >= 3 and (x == (w - 1 if top_at_right else 0)):
                f *= 1.18  # highlight along the top edge
            if w >= 3 and (x == (0 if top_at_right else w - 1)):
                f *= 0.82  # shadow along the bottom edge
            return f
        return fn
    scale_face(c.right, side(True))
    scale_face(c.left, side(False))
    scale_face(c.front, lambda x, y, w, h: 1.12 * (0.9 if w >= 3 and x in (0, w - 1) else 1.0))
    scale_face(c.back, lambda x, y, w, h: 0.7)
    scale_face(c.bottom, lambda x, y, w, h: 0.8)
    scale_face(c.top, lambda x, y, w, h: 0.96)


def face_rect(c, side, f0, f1, u0, u1, s0=None, s1=None):
    """Texel rectangle (x0, y0, x1, y1) on a face of box c for an item-frame area."""
    bf0, bf1, bu0, bu1, bs0, bs1 = c.ext
    if side == "right":
        return round(u0 - bu0), round(bf1 - f1), round(u1 - bu0), round(bf1 - f0)
    if side == "left":
        return round(bu1 - u1), round(bf1 - f1), round(bu1 - u0), round(bf1 - f0)
    s0 = bs0 if s0 is None else s0
    s1 = bs1 if s1 is None else s1
    if side == "up":
        return round(s0 - bs0), round(bf1 - f1), round(s1 - bs0), round(bf1 - f0)
    if side == "down":
        return round(bs1 - s1), round(bf1 - f1), round(bs1 - s0), round(bf1 - f0)
    raise ValueError(side)


FACES = {"right": "right", "left": "left", "up": "front", "down": "back"}


def mark(c, side, f0, f1, u0, u1, color, s0=None, s1=None):
    """Paint a rectangle onto one side of a box, in item-frame coordinates."""
    x0, y0, x1, y1 = face_rect(c, side, f0, f1, u0, u1, s0, s1)
    getattr(c, FACES[side]).fill(color, max(0, x0), max(0, y0), x1, y1)


def slots(c, sides, f0, f1, u0, u1, every, length, color=DARK):
    """A row of slots along f (M-LOK cuts, vents) on the given sides."""
    f = f0
    while f + length <= f1:
        for side in sides:
            mark(c, side, f, f + length, u0, u1, color)
        f += every


def ribs(c, sides, every, color):
    """Cross ribs along the length (magazine ribs, grooves)."""
    for side in sides:
        face = getattr(c, FACES[side])
        for row in range(1, face.h, every):
            face.hline(row, color)


# =========================================================================== the NATO / player guns

def assault_rifle():
    g = Held("assault_rifle", "rifle")
    lower = g.box(-6, 22, 2, 10, -4, 4, BLACK)
    g.box(7, 19, -1, 4, -5, 5, BLACK)  # magwell flare
    upper = g.box(-8, 25, 10, 17, -4, 4, BLACK)
    g.box(-8, 25, 17, 18, -3, 3, BLACK)
    mark(upper, "right", 4, 14, 11, 15, DARK)  # ejection port
    mark(upper, "right", 4, 14, 15, 16, shade(BLACK, 1.4))  # dust cover hinge
    mark(lower, "left", 8, 18, 3, 8, shade(BLACK, 1.35))  # stamped markings
    for f in (0, 3, 6):
        mark(lower, "left", f, f + 2, 7, 8, shade(BLACK, 1.5))
    g.screw(lower, "left", -4, 5)
    g.screw(lower, "left", 20, 5)
    g.rod(-2, 4, 12.5, -5, 1.5, STEEL)  # forward assist
    g.box(-3, -1, 11, 14, -6, -4, STEEL)
    g.box(6, 9, 5, 9, 4, 5, STEEL)  # bolt catch
    g.box(10, 13, 5, 7, -5, -4, SILVER, 1)  # magazine release
    g.box(-4, 0, 7, 9, 4, 5, SILVER, 1)  # selector
    g.trigger(-1, 2)
    g.pistol_grip(-6, 2, 3, 15, 6, POLY, angle=18)
    g.rail(-8, 25, 18, -3, 3)
    g.part("bolt", 9, 13)  # bolt carrier, seen through the ejection port
    g.box(5, 13, 11.5, 14.5, -4, -3, STEEL, 2, bone="bolt")
    g.part("charging_handle", -10, 16)
    g.box(-13, -8, 15, 17, -2, 2, BLACK, 2, bone="charging_handle")
    g.box(-13, -11, 15, 17, -5, 5, BLACK, 2, bone="charging_handle")
    hg = g.box(25, 58, 9, 18, -5, 5, TAN)  # octagonal handguard with M-LOK slots
    g.box(25, 58, 18, 19, -4, 4, TAN)
    g.box(25, 58, 8, 9, -4, 4, TAN)
    slots(hg, ("right", "left"), 29, 56, 12, 15, 6, 4)
    slots(hg, ("down",), 29, 56, 9, 10, 6, 4)
    g.box(25, 27, 8, 19, -5, 5, shade(TAN, 0.8))  # barrel nut ring
    g.rail(27, 58, 19, -3, 3)
    g.rail(46, 56, 12, 5, 6)  # a short side rail
    g.rod(58, 76, 13.5, 0, 2, STEEL)  # barrel
    g.box(59, 62, 11, 16, -2, 2, BLACK)  # gas block
    g.muzzle = (84.0, 13.5)
    g.rod(-30, -8, 13.5, 0, 3, BLACK)  # buffer tube
    g.box(-12, -8, 10, 17, -3, 3, BLACK)
    g.mount("stock", -30, 13)
    g.use("def_stock")
    stock = g.box(-46, -28, 4, 18, -4, 4, TAN)
    g.box(-44, -30, 18, 20, -3, 3, TAN)  # cheek weld
    g.box(-48, -46, 2, 19, -4, 4, RUBBER, 2)  # butt pad
    mark(stock, "right", -42, -34, 8, 13, shade(TAN, 0.75))
    mark(stock, "left", -42, -34, 8, 13, shade(TAN, 0.75))
    g.box(-32, -28, 2, 4, -1, 1, DARK)  # adjustment lever
    g.box(-41, -38, 1, 3, -1, 1, SILVER, 1)  # sling loop
    g.part("mag", 13, 2)
    g.part("def_mag", 13, 2, parent="mag")
    g.use("def_mag")
    g.box(8, 18, -6, 2, -3, 3, TAN)
    m2 = g.box(9, 19, -12, -6, -3, 3, TAN)
    m3 = g.box(10, 20, -18, -12, -3, 3, TAN)
    m4 = g.box(11, 21, -24, -18, -3, 3, TAN)
    g.box(10, 22, -26, -24, -4, 4, TAN_D)
    for c in (m2, m3, m4):
        ribs(c, ("right", "left"), 2, shade(TAN, 0.8))
    mark(m2, "left", 13, 16, -11, -7, DARK)  # witness window
    g.mount("optic", 8, 21, length=33)
    g.use("def_optic")
    g.box(-2, 3, 21, 23, -3, 3, BLACK)  # rear flip sight
    g.box(-1, 2, 23, 27, -2, 2, BLACK)
    g.box(-1, 2, 25, 26, -1, 1, DARK)
    g.box(52, 56, 22, 24, -3, 3, BLACK)  # front flip sight
    g.box(53, 55, 24, 28, -2, -1, BLACK)
    g.box(53, 55, 24, 28, 1, 2, BLACK)
    g.box(53, 55, 24, 27, -0.5, 0.5, DARK)
    g.mount("muzzle", 76, 13.5)
    g.use("def_muzzle")
    for c in g.rod(76, 84, 13.5, 0, 3, BLACK):
        slots(c, ("right", "left"), 78, 83, c.ext[2], c.ext[3], 2, 1)
    g.mount("underbarrel", 42, 8, length=24, default=False)
    g.mount("side", 51, 13.5, 6, length=10, default=False)
    g.use("frame")
    return g


def smg():
    g = Held("smg", "rifle")
    upper = g.box(-8, 26, 9, 18, -4, 4, POLY)
    g.box(-8, 26, 18, 19, -3, 3, POLY)
    g.box(-4, 20, 2, 9, -4, 4, POLY)
    mark(upper, "right", 6, 14, 12, 16, DARK)
    for f in range(-6, 24, 4):
        mark(upper, "left", f, f + 2, 10, 11, shade(POLY, 1.4))
    g.box(9, 19, -2, 3, -4, 4, POLY)  # magwell
    g.trigger(-2, 2)
    g.pistol_grip(-7, 0, 3, 15, 6, POLY, angle=14)
    g.box(-2, 1, 6, 8, 4, 5, SILVER, 1)  # selector
    g.rail(-6, 26, 19, -3, 3)
    shroud = g.box(26, 42, 9, 17, -4, 4, POLY)
    for f in range(28, 40, 4):
        mark(shroud, "right", f, f + 2, 11, 15, DARK)
        mark(shroud, "left", f, f + 2, 11, 15, DARK)
        mark(shroud, "up", f, f + 2, 0, 0, DARK, -2, 2)
    g.rail(28, 40, 6, -3, 3)
    g.rod(42, 46, 13, 0, 2, STEEL)
    g.muzzle = (50.0, 13.0)
    g.part("charging_handle", 30, 16, 5)
    g.box(24, 34, 15, 17, 4, 5, STEEL, 2, bone="charging_handle")
    g.box(31, 34, 14, 18, 5, 7, BLACK, 2, bone="charging_handle")
    g.part("bolt", 10, 14)
    g.box(6, 14, 12.5, 15.5, -4, -3, STEEL, 2, bone="bolt")
    g.mount("stock", -8, 11)
    g.use("def_stock")
    g.box(-10, -6, 4, 17, -4, 4, POLY)  # hinge block
    g.rod(-34, -10, 15.5, -3, 1, SILVER)
    g.rod(-34, -10, 15.5, 3, 1, SILVER)
    g.rod(-34, -10, 6, 0, 1, SILVER)
    g.box(-37, -34, 3, 18, -4, 4, RUBBER, 2)
    g.part("mag", 14, 2)
    g.part("def_mag", 14, 2, parent="mag")
    g.use("def_mag")
    mg = g.box(11, 17, -26, 2, -3, 3, DARK)
    ribs(mg, ("right", "left"), 3, shade(DARK, 1.5))
    g.box(10, 18, -28, -26, -4, 4, POLY)
    g.mount("optic", 10, 22, length=28)
    g.use("def_optic")
    g.box(-4, 0, 22, 26, -3, 3, POLY)
    g.box(-3, -1, 24, 25, -1, 1, DARK)
    g.box(20, 23, 22, 26, -1, 1, POLY)
    g.mount("muzzle", 46, 13)
    g.use("def_muzzle")
    g.rod(46, 50, 13, 0, 2.5, BLACK)
    g.mount("underbarrel", 34, 6, length=12, default=False)
    g.mount("side", 34, 13, 5, length=10, default=False)
    g.use("frame")
    return g


def lmg():
    g = Held("lmg", "rifle")
    recv = g.box(-10, 32, 4, 22, -6, 6, STEEL)
    g.box(-10, 32, 22, 23, -5, 5, STEEL)
    mark(recv, "right", 6, 18, 10, 16, DARK)  # ejection port
    for f in (-8, 30):
        g.screw(recv, "left", f, 6)
        g.screw(recv, "left", f, 20)
    g.trigger(-6, 4)
    g.pistol_grip(-10, -2, 5, 16, 6, POLY, angle=16)
    g.part("charging_handle", 20, 13, -7)
    g.box(16, 24, 12, 15, -8, -6, BLACK, 2, bone="charging_handle")
    g.box(14, 17, 11, 16, -10, -8, BLACK, 2, bone="charging_handle")
    g.part("cover", -10, 23)  # feed tray cover, hinged at the rear
    cov = g.box(-10, 22, 23, 27, -5, 5, GUNMETAL, bone="cover")
    g.rail(-6, 20, 27, -3, 3, bone="cover")
    g.box(-8, -4, 29, 34, -2, 2, BLACK, bone="cover")  # rear sight
    mark(cov, "left", 0, 20, 24, 25, shade(GUNMETAL, 0.7))
    jacket = g.box(32, 58, 9, 20, -5, 5, DARK)
    for f in range(34, 56, 4):
        for side in ("right", "left"):
            mark(jacket, side, f, f + 2, 11, 18, "#0b0c0e")
    g.box(38, 40, 20, 24, -1, 1, DARK)  # carry handle
    g.box(48, 50, 20, 24, -1, 1, DARK)
    g.box(36, 52, 24, 26, -2, 2, POLY)
    g.rod(58, 98, 14.5, 0, 2.5, STEEL)
    g.rod(32, 72, 8.5, 0, 1.5, GUNMETAL)  # gas tube
    g.box(70, 74, 7, 17, -2, 2, BLACK)  # gas block
    g.box(90, 93, 16, 25, -1, 1, BLACK)  # front sight
    g.muzzle = (106.0, 14.5)
    g.mount("stock", -10, 14)
    g.use("def_stock")
    stock = g.box(-50, -12, 6, 22, -5, 5, POLY)
    mark(stock, "right", -44, -20, 10, 18, shade(POLY, 0.6))
    mark(stock, "left", -44, -20, 10, 18, shade(POLY, 0.6))
    g.box(-52, -50, 4, 23, -5, 5, RUBBER, 2)
    g.box(-46, -40, 2, 6, -1, 1, DARK)  # rear grip
    g.part("mag", 14, 4)
    g.part("def_mag", 14, 4, parent="mag")
    g.use("def_mag")
    box = g.box(4, 26, -16, 4, -7, 7, OD)
    for side in ("right", "left"):
        mark(box, side, 6, 24, -14, -13, OD_D)
        mark(box, side, 6, 24, 2, 3, OD_D)
        mark(box, side, 9, 21, -9, -6, "#d9cf8a")  # stencil
    g.box(10, 20, -18, -16, -2, 2, DARK)  # handle
    g.box(22, 26, -6, 0, -8, -7, SILVER, 1)  # latch
    belt = g.box(6, 18, 4, 8, 6, 9, BRASS, 1)
    for row in range(0, belt.front.h, 2):
        belt.front.hline(row, COPPER)
        belt.left.hline(row, COPPER)
    g.mount("optic", 6, 31, length=26, default=False)
    g.mount("muzzle", 98, 14.5)
    g.use("def_muzzle")
    for c in g.rod(98, 106, 14.5, 0, 3.5, BLACK):
        slots(c, ("right", "left", "up"), 100, 105, c.ext[2], c.ext[3], 2, 1)
    g.mount("underbarrel", 80, 7)  # the factory bipod, folded
    g.use("def_underbarrel")
    g.box(78, 84, 5, 10, -3, 3, BLACK)
    g.rod(52, 80, 6, -3, 1, SILVER)
    g.rod(52, 80, 6, 3, 1, SILVER)
    g.box(52, 55, 4, 7, -4, -2, RUBBER, 1)
    g.box(52, 55, 4, 7, 2, 4, RUBBER, 1)
    g.mount("side", 46, 14.5, 6, length=10, default=False)
    g.use("frame")
    return g


def shotgun():
    g = Held("shotgun", "rifle")
    recv = g.box(-6, 20, 6, 18, -4, 4, STEEL)
    g.box(-6, 20, 18, 19, -3, 3, STEEL)
    mark(recv, "right", 2, 14, 11, 16, DARK)  # ejection port
    mark(recv, "down", 0, 14, 0, 0, DARK, -2, 2)  # loading port
    mark(recv, "left", -2, 16, 9, 10, shade(STEEL, 1.4))
    g.trigger(-2, 6)
    g.pistol_grip(-8, 0, 7, 15, 6, POLY, angle=20)
    g.rail(-2, 16, 19, -3, 3)
    g.rod(20, 82, 15, 0, 2.5, GUNMETAL)  # barrel
    g.rod(20, 72, 9, 0, 2.5, DARK)  # magazine tube
    g.rod(72, 76, 9, 0, 3, STEEL)  # cap
    g.box(74, 78, 8, 17, -1, 1, STEEL)  # barrel clamp
    g.muzzle = (84.0, 15.0)
    g.part("pump", 39, 9)
    pump = g.box(30, 48, 5, 13, -5, 5, POLY, bone="pump")
    g.box(30, 48, 13, 14, -4, 4, POLY, bone="pump")
    g.box(30, 48, 4, 5, -4, 4, POLY, bone="pump")
    ribs(pump, ("right", "left", "down"), 2, shade(POLY, 0.5))
    g.part("shell", 7, 4)  # a shell waiting inside the receiver; reloads bring it up from below
    g.rod(3, 11, 7, 0, 1.5, RED, bone="shell")
    g.rod(1, 3, 7, 0, 1.5, BRASS, bone="shell")
    saddle = g.box(2, 16, 8, 16, 4, 6, DARK)  # side saddle with spare shells
    for f in range(3, 15, 3):
        mark(saddle, "left", f, f + 2, 9, 14, RED)
        mark(saddle, "left", f, f + 2, 14, 15, BRASS)
    g.mount("stock", -6, 12)
    g.use("def_stock")
    stock = g.box(-46, -6, 5, 18, -4, 4, POLY)
    g.box(-44, -10, 18, 19, -3, 3, POLY)
    mark(stock, "right", -40, -14, 8, 15, shade(POLY, 0.6))
    mark(stock, "left", -40, -14, 8, 15, shade(POLY, 0.6))
    g.box(-48, -46, 4, 19, -4, 4, RUBBER, 2)
    g.box(-30, -27, 3, 5, -1, 1, SILVER, 1)
    g.part("mag", 46, 9)  # loads into the tube: an empty magazine bone keeps animations uniform
    g.part("def_mag", 46, 9, parent="mag")
    g.mount("optic", 7, 21, length=18)
    g.use("def_optic")
    g.box(12, 16, 21, 25, -3, -2, STEEL)  # ghost ring
    g.box(12, 16, 21, 25, 2, 3, STEEL)
    g.box(12, 16, 25, 26, -3, 3, STEEL)
    g.box(78, 80, 17, 19, -1, 1, CHROME, 0)  # bead
    g.mount("muzzle", 82, 15)
    g.use("def_muzzle")
    g.rod(82, 84, 15, 0, 3, STEEL)
    g.mount("underbarrel", 39, 4, length=12, default=False)
    g.mount("side", 40, 9, 5, length=8, default=False)
    g.use("frame")
    return g


def sniper_rifle():
    g = Held("sniper_rifle", "rifle")
    g.rod(-14, 12, 14, 0, 4, STEEL)  # round action
    g.box(-14, 12, 8, 12, -4, 4, TAN)  # chassis under the action
    fore = g.box(12, 46, 5, 14, -5, 5, TAN)
    g.box(12, 46, 14, 15, -4, 4, TAN)
    g.box(12, 46, 4, 5, -4, 4, TAN)
    slots(fore, ("right", "left"), 16, 44, 8, 11, 6, 4, TAN_D)
    g.trigger(-12, 6)
    g.pistol_grip(-16, -8, 8, 17, 6, TAN, angle=12)
    g.rod(46, 86, 14, 0, 2.5, DARK)
    for c in g.rod(46, 76, 14, 0, 2.6, DARK):  # fluting
        for side in ("right", "left"):
            face = getattr(c, FACES[side])
            for x in range(0, face.w, 2):
                face.vline(x, GUNMETAL)
    g.muzzle = (94.0, 14.0)
    g.part("bolt", -6, 14, -4)  # bolt handle with a tactical knob, on the right
    g.box(-7, -4, 13, 15, -9, -4, SILVER, 1, bone="bolt")
    g.rod(-8, -2, 14, -10, 2, POLY, bone="bolt")
    g.part("mag", 2, 6)
    g.part("def_mag", 2, 6, parent="mag")
    g.use("def_mag")
    mg = g.box(-2, 8, 0, 8, -3, 3, DARK)
    ribs(mg, ("right", "left"), 2, shade(DARK, 1.6))
    g.mount("stock", -16, 12)
    g.use("def_stock")
    butt = g.box(-52, -16, 3, 15, -4, 4, TAN)
    mark(butt, "right", -46, -24, 6, 11, TAN_D)
    mark(butt, "left", -46, -24, 6, 11, TAN_D)
    g.box(-46, -26, 15, 19, -3, 3, TAN)  # cheek riser
    g.box(-50, -48, 15, 16, -2, 2, SILVER, 1)
    g.box(-54, -52, 2, 16, -4, 4, RUBBER, 2)
    g.box(-42, -38, -2, 3, -2, 2, DARK)  # monopod
    g.mount("optic", 6, 19, length=36)
    g.use("def_optic")
    g.rail(-6, 26, 17, -3, 3)
    g.box(-2, 2, 19, 25, -3, 3, BLACK)  # rings
    g.box(20, 24, 19, 25, -3, 3, BLACK)
    g.rod(-12, 28, 25, 0, 3.5, POLY)  # tube
    g.rod(28, 32, 25, 0, 4.5, POLY)
    g.rod(32, 42, 25, 0, 5.5, POLY)  # objective bell
    g.rod(-22, -12, 25, 0, 4.5, POLY)  # eyepiece
    g.lens(42, 21, 29, -3, 3)
    g.lens(-23, 22, 28, -2, 2, "#7fd0f5")
    g.box(8, 12, 28, 32, -2, 2, BLACK)  # elevation turret
    g.box(8, 12, 22, 27, -8, -3, BLACK)  # windage turret
    g.box(9, 11, 32, 33, -1, 1, SILVER, 1)
    g.mount("muzzle", 86, 14)
    g.use("def_muzzle")
    brake = g.box(86, 94, 10, 18, -4, 4, DARK)
    for side in ("right", "left"):
        mark(brake, side, 88, 90, 12, 16, "#060607")
        mark(brake, side, 91, 93, 12, 16, "#060607")
    g.mount("underbarrel", 30, 4)
    g.use("def_underbarrel")
    g.box(36, 40, 2, 5, -3, 3, BLACK)
    g.rod(16, 38, 3, -3, 1, SILVER)
    g.rod(16, 38, 3, 3, 1, SILVER)
    g.mount("side", 30, 10, 5, length=10, default=False)
    g.use("frame")
    return g


def service_pistol():
    g = Held("service_pistol", "pistol")
    frame = g.box(-4, 24, 4, 8, -3, 3, POLY)
    mark(frame, "left", 2, 6, 5, 7, shade(POLY, 1.4))
    g.rail(14, 24, 2, -2, 2)  # dust cover rail
    g.box(-1, 9, 2, 3, -1, 1, POLY)  # trigger guard
    g.box(8, 9, 2, 5, -1, 1, POLY)
    g.box(2, 4, 2, 6, -0.5, 0.5, SILVER, 1)
    g.pistol_grip(-6, 3, 5, 18, 6, POLY, angle=18)
    g.box(-9, -5, 8, 10, -2, 2, POLY)  # beavertail
    g.box(-1, 3, 6, 8, 3, 4, STEEL)  # slide stop
    g.part("slide", 10, 11)
    slide = g.box(-6, 28, 8, 15, -3, 3, STEEL, bone="slide")
    g.box(-6, 28, 15, 16, -2, 2, STEEL, bone="slide")
    for side in ("right", "left"):
        for f in range(-5, 2, 2):
            mark(slide, side, f, f + 1, 9, 15, DARK)  # rear serrations
        for f in range(20, 26, 2):
            mark(slide, side, f, f + 1, 10, 15, DARK)  # front serrations
    mark(slide, "right", 6, 14, 12, 15, DARK)  # ejection port
    g.box(-5, -2, 16, 18, -2, 2, DARK, bone="slide")  # rear sight
    g.box(24, 26, 16, 18, -0.5, 0.5, DARK, bone="slide")  # front sight
    g.box(25, 26, 17, 18, -0.5, 0.5, WHITE, 0, bone="slide")
    g.box(28, 29, 10, 13, -1, 1, "#050505", 0, bone="slide")  # bore
    g.muzzle = (29.0, 11.5)
    g.part("mag", -2, -10)
    g.part("def_mag", -2, -10, parent="mag")
    g.use("def_mag")
    g.box(-8, 2, -14, -12, -3, 3, POLY, tilt=-18, pivot=(-1.5, 5))
    g.mount("optic", 4, 16, length=8, default=False)
    g.mount("muzzle", 28, 11.5, default=False)
    g.mount("side", 19, 2, length=8, default=False)
    g.use("frame")
    return g


def rocket_launcher():
    g = Held("rocket_launcher", "launcher")
    for c in g.rod(-50, 50, 20, 0, 8, OD):  # tube with bands and a stencil
        for side in ("right", "left", "up", "down"):
            for f0 in (-36, 0, 36):
                mark(c, side, f0, f0 + 2, c.ext[2], c.ext[3], OD_D)
        if c.ext[3] - c.ext[2] >= 4:
            mark(c, "left", -24, -6, c.ext[2], c.ext[3], "#d9cf8a")
    g.rod(-58, -50, 20, 0, 10, DARK)  # blast cone
    g.rod(-60, -58, 20, 0, 9, "#0d0e10")
    g.rod(46, 50, 20, 0, 9, OD_D)  # muzzle ring
    g.pistol_grip(-12, -4, 12, 14, 6, POLY, angle=10)
    g.trigger(-10, 12)
    g.box(6, 12, 2, 12, -2, 2, POLY, tilt=6)  # fore grip
    g.box(-32, -12, 10, 12, -6, 6, RUBBER, 2)  # shoulder pad
    g.mount("optic", 4, 28, 6, length=10)
    g.use("def_optic")
    g.box(-6, 14, 26, 34, 6, 12, DARK)
    g.lens(14, 27, 33, 7, 11)
    g.lens(-7, 28, 32, 8, 10, "#7fd0f5")
    g.box(0, 4, 20, 26, 7, 9, DARK)
    g.part("rocket", 52, 20)  # the warhead sticking out of the tube
    g.rod(50, 58, 20, 0, 7, "#4f5733", bone="rocket")
    g.rod(58, 62, 20, 0, 5, "#4f5733", bone="rocket")
    g.rod(62, 66, 20, 0, 3.5, "#3b4126", bone="rocket")
    g.rod(66, 69, 20, 0, 2, DARK, bone="rocket")
    g.part("mag", 52, 20)
    g.part("def_mag", 52, 20, parent="mag")
    g.muzzle = (69.0, 20.0)
    g.mount("side", 20, 20, -9, length=10, default=False)
    g.use("frame")
    return g


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


# =========================================================================== the Red Fang's guns (AI soldiers)

def fang_rifle():
    """A stamped-steel rifle with wooden furniture and a curved magazine."""
    g = Held("fang_rifle", "rifle")
    recv = g.box(-8, 30, 4, 16, -4, 4, STEEL)
    g.box(-8, 30, 16, 18, -3, 3, GUNMETAL)  # dust cover
    mark(recv, "right", 6, 18, 10, 14, DARK)
    g.box(4, 18, 11, 13, -7, -4, STEEL)  # safety lever
    g.trigger(-2, 4)
    g.pistol_grip(-8, 0, 5, 14, 6, WOOD_D, angle=18, stipple=False)
    hg = g.box(30, 52, 7, 15, -5, 5, WOOD)
    for side in ("right", "left"):
        mark(hg, side, 30, 52, 8, 9, WOOD_D)
        mark(hg, side, 30, 52, 13, 14, WOOD_D)
    g.box(30, 48, 15, 19, -3, 3, WOOD)  # upper guard
    g.rod(48, 64, 17, 0, 1.5, STEEL)  # gas tube
    g.rod(52, 76, 11, 0, 2, GUNMETAL)
    g.box(64, 68, 9, 24, -2, 2, DARK)  # front sight block
    g.rod(76, 82, 11, 0, 2.5, DARK)  # slant brake
    g.box(-2, 4, 18, 22, -2, 2, DARK)  # rear sight
    g.part("charging_handle", 22, 14, -5)
    g.box(18, 24, 13, 15, -7, -4, SILVER, 1, bone="charging_handle")
    g.part("mag", 14, 4)
    g.part("def_mag", 14, 4, parent="mag")
    g.use("def_mag")
    for i, (f0, u0) in enumerate(((10, -4), (12, -10), (15, -16), (18, -22))):
        c = g.box(f0, f0 + 10, u0, u0 + 6 + (2 if i == 0 else 0), -3, 3, "#4a3a2e" if i % 2 else "#55432f")
        ribs(c, ("right", "left"), 2, shade("#4a3a2e", 0.75))
    g.use("frame")
    stock = g.box(-44, -8, 3, 16, -4, 4, WOOD, tilt=5, pivot=(-8, 12))
    for side in ("right", "left"):
        mark(stock, side, -40, -12, 9, 10, WOOD_D)
    g.box(-46, -44, 2, 16, -4, 4, STEEL, tilt=5, pivot=(-8, 12))
    g.muzzle = (82.0, 11.0)
    return g


def fang_dmr():
    g = Held("fang_dmr", "rifle")
    g.box(-10, 30, 4, 16, -4, 4, STEEL)
    g.trigger(-4, 4)
    g.pistol_grip(-10, -2, 5, 14, 6, WOOD_D, angle=18, stipple=False)
    g.box(30, 62, 6, 16, -5, 5, WOOD)
    g.rod(62, 100, 11, 0, 2, GUNMETAL)
    g.rod(100, 106, 11, 0, 3, DARK)
    stock = g.box(-52, -10, 2, 16, -4, 4, WOOD)
    for side in ("right", "left"):
        mark(stock, side, -44, -22, 6, 11, WOOD_D)
    g.box(-54, -52, 1, 16, -4, 4, DARK)
    g.box(-2, 26, 16, 18, -3, 3, DARK)  # side mount
    g.rod(-6, 22, 23, 0, 3, POLY)
    g.rod(22, 30, 23, 0, 4.5, POLY)
    g.lens(30, 19, 27, -3, 3)
    g.part("mag", 12, 4)
    g.part("def_mag", 12, 4, parent="mag")
    g.box(6, 16, -10, 4, -3, 3, "#2e2a26", bone="def_mag")
    g.muzzle = (106.0, 11.0)
    return g


def fang_rpg():
    g = Held("fang_rpg", "launcher")
    g.rod(-52, 30, 20, 0, 4, GUNMETAL)  # tube
    g.rod(-14, 14, 20, 0, 6, WOOD)  # heat shield
    g.rod(-64, -52, 20, 0, 7, DARK)  # rear flare
    g.pistol_grip(-6, 2, 14, 14, 6, DARK, angle=10, stipple=False)
    g.pistol_grip(14, 20, 14, 12, 6, DARK, angle=10, stipple=False)
    g.box(0, 10, 26, 32, 5, 9, DARK)  # optic
    g.part("rocket", 34, 20)
    g.rod(30, 38, 20, 0, 3, "#4a5530", bone="rocket")
    g.rod(38, 48, 20, 0, 8, "#4a5530", bone="rocket")
    g.rod(48, 56, 20, 0, 6, "#4a5530", bone="rocket")
    g.rod(56, 62, 20, 0, 3.5, "#3a4228", bone="rocket")
    g.rod(62, 66, 20, 0, 1.5, DARK, bone="rocket")
    g.muzzle = (66.0, 20.0)
    return g


ALL = {
    "service_pistol": service_pistol, "smg": smg, "assault_rifle": assault_rifle, "lmg": lmg, "shotgun": shotgun,
    "sniper_rifle": sniper_rifle, "rocket_launcher": rocket_launcher, "combat_knife": combat_knife,
    "frag_grenade": frag_grenade, "smoke_grenade": smoke_grenade, "medkit": medkit, "ammo_box": ammo_box,
    "repair_tool": repair_tool, "binoculars": binoculars, "field_radio": field_radio,
}
FANG = {"fang_rifle": fang_rifle, "fang_dmr": fang_dmr, "fang_rpg": fang_rpg}
GUNS = ["service_pistol", "smg", "assault_rifle", "lmg", "shotgun", "sniper_rifle", "rocket_launcher"]


def build_all():
    return {key: fn().finish() for key, fn in ALL.items()}
