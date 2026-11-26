"""The modelling kit for everything held in the hand (guns.py builds the guns, attach.py the attachments,
held.py gathers every held item).

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
Each attachment (attach.py) adds its boxes to a bone a_<id> under the att_* bone of its slot; the gun's render
controller shows it when fitted and hides the def_* part it replaces (see docs/attachments.md). Held.mounts
records where each mount is, per gun.
"""
from __future__ import annotations

import math

from modelkit import Model, shade

GRIP = (-6.0, 13.5, 0.0)  # the middle of the right fist in the player's model space
SCALE = 0.25  # third person: quarter-pixel units
FP_SCALE = 0.28  # first person: a little larger, as guns read better close to the eye
LOW = [False]  # set LOW[0] = True to build a light version (the guns soldiers carry): plain rods, no pins
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
        # In the game the item bone is bound to the hand holding it; the player skeleton above it is only for the
        # previews (viewer.py, holds.py) and is not written out.
        item.binding = "q.item_slot_to_bone_name(c.item_slot)"
        self.model.export_skip = {name for name, _p, _v in SKELETON}
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

    def mount(self, slot, f, u, s=0.0, length=0, default=True, parent="gun", bore=2.0):
        """An attachment mount: bone att_<slot> pivoting at (f, u, s) (under `parent`, so attachments ride a
        moving part such as a pistol's slide), with an optional def_<slot> child for the factory part.
        `bore` is the barrel radius at a muzzle mount; `length` the usable rail length."""
        att = self.part(f"att_{slot}", f, u, s, parent=parent)
        att.locators = {slot: [round(v, 3) for v in self.at(f, u, s)]}
        self.mounts[slot] = {"f": f, "u": u, "s": s, "length": length, "bore": bore, "parent": parent}
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

    def rod(self, f0, f1, cu, cs, r, color, noise=2, bone=None, facets=None):
        """A round bar along the barrel axis. In full detail its section is a polygon of 4n sides made from n
        square boxes turned evenly about the axis (16 sides for thick bars); at LOW detail (soldiers' guns),
        a pixel circle of stacked slabs. Returns the boxes; marks painted on each land on every facet."""
        if LOW[0]:
            return self._rod_slabs(f0, f1, cu, cs, r, color, noise, bone)
        n = facets or (4 if r >= 2.75 else 3 if r >= 1.75 else 2 if r >= 0.9 else 1)
        size = max(1, round(2 * r))
        infl = r - size / 2
        out = []
        for i in range(n):
            ang = 90.0 * i / n
            c = self.box(f0, f1, cu - size / 2, cu + size / 2, cs - size / 2, cs + size / 2, color, noise,
                         inflate=infl, roll=ang if ang else 0.0, pivot=(0, cu, cs), bone=bone)
            _light_round(c, color, ang, noise, self.seed + i)
            out.append(c)
        return out

    def _rod_slabs(self, f0, f1, cu, cs, r, color, noise=2, bone=None):
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
        if not out:
            out.append(self.box(f0, f1, cu - 0.5, cu + 0.5, cs - 0.5, cs + 0.5, color, noise, bone=bone))
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

    # ------------------------------------------------------------ higher-detail parts
    def bevel(self, f0, f1, u0, u1, s0, s1, color, b=1.0, noise=3, bone=None, edges="all"):
        """A box with its four long edges (along f) chamfered at 45 degrees: two crossed core boxes and a
        slim box turned 45 degrees about the barrel axis along each edge."""
        out = [self.box(f0, f1, u0 + b, u1 - b, s0, s1, color, noise, bone=bone),
               self.box(f0, f1, u0, u1, s0 + b, s1 - b, color, noise, bone=bone)]
        infl = (b * math.sqrt(2) - 1) / 2
        corners = {"tl": (u1 - b, s1 - b), "tr": (u1 - b, s0 + b), "bl": (u0 + b, s1 - b), "br": (u0 + b, s0 + b)}
        for name, (cu, cs) in corners.items():
            if edges != "all" and name not in edges:
                continue
            light = 1.25 if name in ("tl", "tr") else 0.8  # the top edges catch the light
            c = self.box(f0, f1, cu - 0.5, cu + 0.5, cs - 0.5, cs + 0.5, shade(color, light), max(1, noise - 1),
                         inflate=infl, roll=45, pivot=(0, cu, cs), bone=bone)
            out.append(c)
        return out

    def teeth_rail(self, f0, f1, u, s0, s1, color=BLACK, bone=None, step=3, down=False):
        """A picatinny rail with real teeth: a base and a raised tooth every `step` units. It stands on `u`
        and rises 3 units (or, with `down`, hangs 3 units below `u`)."""
        k = -1 if down else 1
        lo = lambda a, b: (u + min(a, b) * 1, u + max(a, b) * 1) if not down else (u - max(a, b), u - min(a, b))
        u0, u1 = lo(0, 1)
        base = self.box(f0, f1, u0, u1, s0 + 1, s1 - 1, color, 2, bone=bone)
        u0, u1 = lo(1, 2)
        self.box(f0, f1, u0, u1, s0, s1, shade(color, 0.85), 2, bone=bone)
        teeth = []
        f = f0
        u0, u1 = lo(2, 3)
        while f + 2 <= f1:
            teeth.append(self.box(f, f + 2, u0, u1, s0, s1, shade(color, 1.1), 1, bone=bone))
            f += step
        return [base] + teeth

    def slotted_panel(self, f0, f1, u0, u1, s0, s1, color, slot_u, slot_len, every, inner=DARK, bone=None):
        """A box whose two sides have real through-slots (M-LOK, vents): a dark core, strips above and below
        the slots and posts between them."""
        su0, su1 = slot_u
        self.box(f0, f1, u0, u1, s0 + 1, s1 - 1, inner, 1, bone=bone)  # the dark inside seen through the slots
        self.box(f0, f1, u0, su0, s0, s1, color, 3, bone=bone)
        self.box(f0, f1, su1, u1, s0, s1, color, 3, bone=bone)
        f = f0
        posts = []
        while f < f1:
            end = min(f1, f + (every - slot_len))
            if end > f:
                posts.append(self.box(f, end, su0, su1, s0, s1, color, 3, bone=bone))
            f = end + slot_len
        return posts

    def pin(self, f, u, s, side, color=SILVER):
        """A pin or screw head standing proud of a side by half a unit."""
        ds = 0.5 if side == "left" else -1.5
        if LOW[0]:
            return None
        return self.box(f - 0.5, f + 0.5, u - 0.5, u + 0.5, s + ds, s + ds + 1, color, 1, inflate=-0.1)

    def ring(self, f0, f1, cu, cs, r, color, bone=None):
        """A band round a bar (a rod a size up, short)."""
        return self.rod(f0, f1, cu, cs, r, color, bone=bone)

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


def _light_round(c, color, ang, noise, seed):
    """Shade the four long faces of a box turned `ang` degrees about the barrel by how much each faces up,
    with a bright line where a face looks straight up: a lit round bar."""
    faces = {"front": 0.0, "right": 90.0, "back": 180.0, "left": 270.0}
    for name, base in faces.items():
        face = getattr(c, name)
        k = math.cos(math.radians(base + ang))
        face.fill(shade(color, 0.8 + 0.3 * k))
        if noise:
            face.noise(noise, seed + int(base))
        if k > 0.9:  # specular streak along the bar
            mid = face.w // 2
            for y in range(face.h):
                face.px(mid, y, shade(color, 1.35))


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


