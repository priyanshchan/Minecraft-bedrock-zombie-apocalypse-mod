"""The 3D models of everything that is not held in the hand: the AI soldiers (with their gear and their
guns), the jeep and the tank, the projectiles, the capture flag and the blocks with shapes of their own.

Everything is built with modelkit: boxes in Bedrock model space (Y up, the model faces -Z, its right side
on -X), each face painted texel by texel. Models painted at res 2 carry two texels per pixel.
"""
from __future__ import annotations

import math
import random
import zlib

import numpy as np
from PIL import Image

import held as H
import holds
from modelkit import Model, mix, rgba, shade

# =========================================================================== painting helpers


def blotches(w, h, cell, seed):
    """Smooth value noise in [0, 1] over a w x h grid (for camouflage and grime)."""
    rng = np.random.default_rng(seed)
    gw, gh = w // cell + 2, h // cell + 2
    grid = rng.random((gh, gw))
    ys, xs = np.mgrid[0:h, 0:w] / cell
    x0, y0 = xs.astype(int), ys.astype(int)
    fx, fy = xs - x0, ys - y0
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = grid[y0, x0], grid[y0, x0 + 1]
    c, d = grid[y0 + 1, x0], grid[y0 + 1, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def camo_face(face, base, spots, seed, cell=3):
    """Fill a face with a blotchy pattern: `spots` are (colour, threshold) layered over `base`."""
    if face.w == 0 or face.h == 0:
        return
    layers = [blotches(face.w, face.h, cell, seed + i * 101) for i in range(len(spots))]
    for y in range(face.h):
        for x in range(face.w):
            col = base
            for (c, t), n in zip(spots, layers):
                if n[y, x] > t:
                    col = c
            face.px(x, y, col)


def paint(c, base, spots=None, seed=0, cell=3, noise=5, top=None, bottom=0.72):
    """Paint every face of a box: a flat colour or a camouflage, light from above, grain."""
    for i, f in enumerate(c.faces):
        if spots:
            camo_face(f, rgba(base), [(rgba(s), t) for s, t in spots], seed * 13 + i, cell)
        else:
            f.fill(base)
        if noise:
            f.noise(noise, seed + i)
    if top:
        c.top.fill(top)
        c.top.noise(noise, seed + 9)
    for xx in range(c.bottom.w):
        for yy in range(c.bottom.h):
            c.bottom.px(xx, yy, shade(c.bottom.get(xx, yy), bottom))
    return c


def rivets(face, color, step=4, inset=1):
    for x in range(inset, face.w - inset, step):
        face.px(x, inset, color)
        face.px(x, face.h - 1 - inset, color)


def emblem(face, kind, cx=None, cy=None, r=None):
    """Team insignia painted on a face: NATO a white star in a blue disc, Red Fang a red fang."""
    cx = face.w // 2 if cx is None else cx
    cy = face.h // 2 if cy is None else cy
    r = r or max(2, min(face.w, face.h) // 3)
    if kind == "nato":
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    face.px(cx + x, cy + y, "#2d5fa8")
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rad = r * 0.82 if i % 2 == 0 else r * 0.34
            pts.append((cx + rad * math.cos(a), cy + rad * math.sin(a)))
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if _inside((cx + x + 0.5, cy + y + 0.5), pts):
                    face.px(cx + x, cy + y, "#f2f2ee")
    else:
        for y in range(-r, r + 1):
            for x in range(-r, r + 1):
                if x * x + y * y <= r * r:
                    face.px(cx + x, cy + y, "#1c1c1e")
        for y in range(-r + 1, r):
            half = max(0, int((r - 1 - (y + r - 1) * 0.55)))
            for x in range(-half, half + 1):
                face.px(cx + x - (y + r) // 4, cy + y, "#d02c28")


def _inside(p, poly):
    x, y = p
    inside = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            inside = not inside
    return inside


# =========================================================================== soldiers

SKIN_TONES = ["#c99a77", "#8d5b3e", "#e0b896", "#6b4430", "#b98563", "#a8754f"]

OUTFITS = {
    # NATO
    "nato_woodland": dict(team="nato", skin=0, uniform=("#5b6a3c", [("#3f4b29", 0.55), ("#6e5a3a", 0.62), ("#2a2d22", 0.72)]),
                          vest="#4b5534", helmet="#56603a", gloves="#2a2a26", boots="#2e2a22", hair="#3a2a1a"),
    "nato_woodland_b": dict(team="nato", skin=3, uniform=("#5b6a3c", [("#3f4b29", 0.55), ("#6e5a3a", 0.62), ("#2a2d22", 0.72)]),
                            vest="#8a7550", helmet="#56603a", gloves="#2a2a26", boots="#2e2a22", hair="#1a1410"),
    "nato_desert": dict(team="nato", skin=2, uniform=("#b49c6c", [("#9a8054", 0.55), ("#c9b689", 0.62), ("#7a6444", 0.74)]),
                        vest="#8a7550", helmet="#a48c5c", gloves="#5a4a36", boots="#6a5638", hair="#7a5a32"),
    "nato_marksman": dict(team="nato", skin=4, uniform=("#56603a", [("#3d4529", 0.5), ("#6b6040", 0.6), ("#7c8452", 0.7)]),
                          vest="#4b5534", helmet="#56603a", gloves="#2a2a26", boots="#2e2a22", hair="#3a2a1a", ghillie=True),
    "nato_heavy": dict(team="nato", skin=1, uniform=("#5b6a3c", [("#3f4b29", 0.55), ("#6e5a3a", 0.62), ("#2a2d22", 0.72)]),
                       vest="#3f4a2c", helmet="#4f5934", gloves="#2a2a26", boots="#2e2a22", hair="#1a1410", heavy=True),
    # Red Fang
    "redfang_black": dict(team="redfang", skin=5, uniform=("#26262a", []), vest="#3a3a32", mask="#18181b", gloves="#1a1a1c",
                          boots="#1e1c1a", pants="#202024", headgear="beanie", headgear_col="#202024"),
    "redfang_olive": dict(team="redfang", skin=0, uniform=("#4f5236", []), vest="#2e2e2a", mask="#7e1a17", gloves="#2a2a26",
                          boots="#3a2c20", pants="#3c4f6e", headgear="cap", headgear_col="#3a3a32"),
    "redfang_hoodie": dict(team="redfang", skin=1, uniform=("#55565c", []), vest="#1e1e20", mask="#18181b", gloves="#1a1a1c",
                           boots="#262422", pants="#2a2a2e", headgear="hood", headgear_col="#4a4b50"),
    "redfang_sniper": dict(team="redfang", skin=4, uniform=("#5a5040", [("#4a4234", 0.55), ("#6a5e48", 0.65)]), vest="#3a3428",
                           mask="#18181b", gloves="#2a2620", boots="#2a2420", pants="#4a4234", headgear="hood",
                           headgear_col="#4a4234", ghillie=True),
    "redfang_rpg": dict(team="redfang", skin=3, uniform=("#33332e", []), vest="#26261f", mask="#7e1a17", gloves="#1a1a1c",
                        boots="#1e1c1a", pants="#2a2a26", headgear="beanie", headgear_col="#7e1a17", heavy=True),
}

SOLDIER_GUN_CUBES = 90  # parts of a soldier's gun drawn (the largest); the player's own gun has them all


def soldier_gun(name):
    """The gun a soldier carries: the player's model of it, built light (plain rods, no pins) and bare, since
    many soldiers are on screen at once."""
    import guns as G
    from kit import LOW
    LOW[0] = True
    try:
        return G.GUNS[name]().finish()
    finally:
        LOW[0] = False


def gun_cubes(g):
    """Every box of a held model (all its bones below `item`), in model space: the parts carry no rotation of
    their own at rest, so the boxes can be gathered into one bone."""
    skeleton = {b[0] for b in H.SKELETON} | {"item"}
    return [c for b in g.model.bones if b.name not in skeleton for c in b.cubes]


def soldier(key, outfit_key, res=2):
    """One painted soldier model: entity `key` (which decides the gun) in the uniform `outfit_key`.
    Each uniform is a geometry of its own (gear differs), picked by the entity's variant."""
    o = OUTFITS[outfit_key]
    team = o["team"]
    rng = random.Random(zlib.crc32(outfit_key.encode()))
    seed = zlib.crc32(outfit_key.encode()) & 0xFFFF
    m = Model(f"soldier_{outfit_key}", bounds=(3.0, 3.0, 1.2), res=res)
    root = m.bone("root", (0, 0, 0))
    body = m.bone("body", (0, 24, 0), "root")
    head = m.bone("head", (0, 24, 0), "body")
    rarm = m.bone("rightArm", (-5, 22, 0), "body")
    larm = m.bone("leftArm", (5, 22, 0), "body")
    rleg = m.bone("rightLeg", (-1.9, 12, 0), "root")
    lleg = m.bone("leftLeg", (1.9, 12, 0), "root")
    ritem = m.bone("rightItem", (-6, 15, 1), "rightArm")

    skin = SKIN_TONES[o["skin"]]
    base, spots = o["uniform"]
    pants_base = o.get("pants", base)
    pants_spots = spots if "pants" not in o else []

    # ---- head and face
    hd = head.cube((-4, 24, -4), (8, 8, 8))
    paint(hd, skin, noise=3, seed=seed)
    f = hd.front
    k = res
    if o.get("mask"):
        for face in hd.faces:
            face.fill(o["mask"])
            face.noise(3, seed + 3)
        f.fill(skin, 1 * k, 3 * k, 7 * k, 5 * k)  # eye slit
    hair = o.get("hair", "#2a2018")
    f.fill(shade(skin, 0.7), 1 * k, 4 * k - 1, 3 * k, 4 * k)  # brows
    f.fill(shade(skin, 0.7), 5 * k, 4 * k - 1, 7 * k, 4 * k)
    for ex in (1, 5):  # eyes: white and iris
        f.fill("#ecebe6", ex * k, 4 * k, (ex + 2) * k, 4 * k + 2)
        f.fill("#2a3a4a" if rng.random() < 0.4 else "#3a2a1a", (ex + (1 if ex == 1 else 0)) * k, 4 * k,
               (ex + (1 if ex == 1 else 0)) * k + 1, 4 * k + 2)
    if not o.get("mask"):
        f.fill(shade(skin, 0.86), 3 * k + 1, 5 * k, 5 * k - 1, 6 * k)  # nose
        f.fill(shade(skin, 0.62), 3 * k, 6 * k + 1, 5 * k, 6 * k + 2)  # mouth
        for face in (hd.top, hd.back, hd.right, hd.left):
            face.fill(hair, 0, 0, face.w, 2 * k if face is not hd.top else face.h)
    elif o["mask"] != "#18181b":  # a bandana over nose and mouth, the rest of the face showing
        for face in (hd.front, hd.right, hd.left, hd.back):
            face.fill(skin, 0, 0, face.w, 5 * k)
            face.fill(o["mask"], 0, 5 * k, face.w, face.h)
            for x in range(0, face.w, 3):
                face.px(x, 6 * k, shade(o["mask"], 0.6))
        f.fill(hair, 0, 0, f.w, k)
        hd.top.fill(hair)
        for face in (hd.back, hd.right, hd.left):
            face.fill(hair, 0, 0, face.w, 3 * k)
        f.fill("#ecebe6", 1 * k, 4 * k - 1, 3 * k, 4 * k + 1)
        f.fill("#ecebe6", 5 * k, 4 * k - 1, 7 * k, 4 * k + 1)
        f.fill("#3a2a1a", 2 * k, 4 * k - 1, 2 * k + 1, 4 * k + 1)
        f.fill("#3a2a1a", 5 * k, 4 * k - 1, 5 * k + 1, 4 * k + 1)

    # ---- headgear
    if team == "nato":
        helmet = o["helmet"]
        dome = head.cube((-4, 29, -4), (8, 3, 8), inflate=0.75)
        paint(dome, helmet, [(shade(helmet, 0.75), 0.6), (shade(helmet, 1.2), 0.75)], seed + 20, noise=4)
        rim = head.cube((-4, 25, -1), (8, 3, 5), inflate=0.8)
        paint(rim, helmet, [(shade(helmet, 0.75), 0.6)], seed + 21, noise=4)
        for face in (dome.right, dome.left, dome.back):
            face.hline(face.h - 2, "#2a2a26")  # goggle band
        nvg = head.cube((-1, 29, -5.6), (2, 2, 1))
        paint(nvg, "#26262a", noise=2)
        head.cube((-4.8, 28, -1), (1, 2, 2), inflate=0.1).fill("#3a3a36")  # rail mounts
        head.cube((3.8, 28, -1), (1, 2, 2), inflate=0.1).fill("#3a3a36")
        for face in (hd.right, hd.left):  # chin strap
            face.vline(4 * k, "#2a2a26", 3 * k, face.h)
        if o.get("ghillie"):
            hood = head.cube((-4, 26, -4), (8, 6, 8), inflate=1.2)
            for i, face in enumerate(hood.faces):
                camo_face(face, rgba("#56603a"), [(rgba("#3d4529"), 0.5), (rgba("#7c8452"), 0.65), (rgba("#6b6040"), 0.75)],
                          seed + 30 + i, 2)
                for y in range(face.h):
                    for x in range(face.w):
                        if rng.random() < 0.18:
                            face.px(x, y, None)
            for x in range(hood.front.w):  # leave the face open
                for y in range(hood.front.h):
                    if 3 * k <= y and 1 * k <= x < 7 * k:
                        hood.front.px(x, y, None)
            hood.front.ragged_bottom(4, seed)
            for face in (hood.right, hood.left, hood.back):
                face.ragged_bottom(6, seed + 1)
    else:
        gear = o.get("headgear")
        col = o.get("headgear_col", "#202024")
        if gear == "beanie":
            cap = head.cube((-4, 29, -4), (8, 3, 8), inflate=0.5)
            paint(cap, col, noise=5, seed=seed + 22)
            for face in cap.sides:
                face.hline(face.h - 1, shade(col, 0.75))
        elif gear == "cap":
            cap = head.cube((-4, 29, -4), (8, 3, 8), inflate=0.45)
            paint(cap, col, noise=4, seed=seed + 22)
            brim = head.cube((-3, 29, -8), (6, 1, 4))
            paint(brim, shade(col, 0.85), noise=3)
        elif gear == "hood":
            hood = head.cube((-4, 24, -4), (8, 8, 8), inflate=0.9)
            paint(hood, col, noise=4, seed=seed + 23)
            for x in range(hood.front.w):
                for y in range(hood.front.h):
                    if 2 * k <= y and 1 * k <= x < 7 * k:
                        hood.front.px(x, y, None)
            hood.bottom.fill(None)

    # ---- torso
    torso = body.cube((-4, 12, -2), (8, 12, 4))
    paint(torso, base, spots, seed + 40, noise=4)
    if team == "nato":
        vest = body.cube((-4, 15, -2), (8, 8, 4), inflate=0.75)
        paint(vest, o["vest"], noise=5, seed=seed + 41)
        for face in (vest.front, vest.back):
            for y in range(2, face.h - 1, 3):
                face.hline(y, shade(o["vest"], 0.8))  # webbing rows
        emblem(vest.left, "nato", r=2 * k)  # a flag patch on the shoulder side
        for i, x in enumerate((-3.6, -1.0, 1.6)):
            p = body.cube((x, 15.2, -3.6), (2, 3, 1))
            paint(p, shade(o["vest"], 0.92), noise=4, seed=seed + 50 + i)
            p.top.fill(shade(o["vest"], 0.7))
        admin = body.cube((-2, 19.4, -3.4), (4, 2, 1))
        paint(admin, shade(o["vest"], 0.95), noise=3)
        pack = body.cube((-3, 14, 2.7), (6, 8, 3))
        paint(pack, o["vest"], noise=5, seed=seed + 60)
        for face in pack.sides:
            face.hline(1 * k, shade(o["vest"], 0.7))
        radio = body.cube((-3.6, 21, 2.9), (2, 3, 1))
        paint(radio, "#2a2a2a", noise=3)
        ant = body.cube((-3.2, 24, 3.2), (1, 9, 1), inflate=-0.35)
        paint(ant, "#1a1a1a", noise=1)
        if o.get("heavy"):
            for i, x in enumerate((-2.5, 0.5)):
                r = body.cube((x, 20, 5.2), (2, 9, 2))
                paint(r, "#4a5530", noise=3, seed=seed + 70 + i)
                r.top.fill("#2a2a26")
    else:
        rig = body.cube((-4, 14, -2), (8, 5, 4), inflate=0.6)
        paint(rig, o["vest"], noise=4, seed=seed + 41)
        for i, x in enumerate((-3.6, -1.0, 1.6)):
            p = body.cube((x, 14.2, -3.5), (2, 4, 1))
            paint(p, shade(o["vest"], 1.1), noise=4, seed=seed + 50 + i)
        strap = body.cube((-0.5, 12, -2.5), (1, 14, 1), rotation=(0, 0, 38), pivot=(0, 18, -2.5))
        paint(strap, "#3a3020", noise=3)
        for y in range(1, strap.front.h, 2 * k):
            strap.front.px(strap.front.w // 2, y, "#c9a43a")  # bandolier rounds
        if o.get("heavy"):
            bag = body.cube((-3, 14, 2.6), (6, 7, 3))
            paint(bag, "#3a3428", noise=5, seed=seed + 60)
            for i, x in enumerate((-2.5, 0.5)):
                r = body.cube((x, 21, 3.2), (2, 6, 2))
                paint(r, "#4a5530", noise=3, seed=seed + 70 + i)
                tip = body.cube((x + 0.5, 27, 3.7), (1, 2, 1))
                paint(tip, "#2a2a26", noise=2)
    belt = body.cube((-4, 12, -2), (8, 1, 4), inflate=0.45)
    paint(belt, "#26251f", noise=2)
    belt.front.fill("#8a8a80", 3 * k, 0, 5 * k, belt.front.h)  # buckle

    # ---- arms
    for bone, x0, side in ((rarm, -8, "right"), (larm, 4, "left")):
        arm = bone.cube((x0, 12, -2), (4, 12, 4))
        paint(arm, base, spots, seed + (80 if side == "right" else 90), noise=4)
        glove = bone.cube((x0, 12, -2), (4, 3, 4), inflate=0.18)
        paint(glove, o["gloves"], noise=3)
        if o.get("ghillie"):
            for face in arm.sides:
                for y in range(face.h // 2):
                    if rng.random() < 0.5:
                        face.px(rng.randrange(face.w), y, "#3d4529")
        outer = arm.right if side == "right" else arm.left
        if team == "nato" and side == "left":
            emblem(outer, "nato", cy=3 * k, r=int(1.5 * k))
        if team == "redfang" and side == "left":  # red armband
            for face in arm.sides:
                face.fill("#c8302c", 0, 3 * k, face.w, 5 * k)
                face.hline(3 * k, "#8a1a16")
            emblem(outer, "redfang", cy=4 * k, r=k)

    # ---- legs
    for bone, x0, side in ((rleg, -3.9, "right"), (lleg, -0.1, "left")):
        leg = bone.cube((x0, 0, -2), (4, 12, 4))
        paint(leg, pants_base, pants_spots, seed + (100 if side == "right" else 110), noise=4)
        boot = bone.cube((x0, 0, -2), (4, 3, 4), inflate=0.28)
        paint(boot, o["boots"], noise=3)
        boot.top.fill(shade(o["boots"], 0.9))
        for face in boot.sides:
            face.hline(face.h - 1, shade(o["boots"], 0.6))
        pad = bone.cube((x0, 4, -2.9), (4, 3, 1))
        paint(pad, "#26262a" if team == "nato" else shade(pants_base, 0.8), noise=3)
        if side == "right":
            holster = bone.cube((x0 - 1, 6, -1), (1, 4, 3))
            paint(holster, "#26251f", noise=2)

    # ---- the gun, as held in the aiming pose
    from defs import SOLDIERS
    g = soldier_gun(SOLDIERS[key]["gun"])
    # a level of detail for crowds: the soldier's gun keeps its largest parts (they make the silhouette)
    parts = gun_cubes(g)
    keep = set(map(id, sorted(parts, key=lambda c: -(c.size[0] * c.size[1] * c.size[2]))[:SOLDIER_GUN_CUBES]))
    third, _first = holds.compute()[g.hold]
    gun = m.bone("gun", H.GRIP, "rightItem", rotation=third[0])
    gun.scale = H.SCALE
    for c in parts:
        if id(c) not in keep:
            continue
        c.img = c.img.resize((c.img.width * res, c.img.height * res), Image.NEAREST)
        c.res = res
        c.bone = "gun"
        gun.cubes.append(c)
    gun.locators = {"muzzle": [round(H.GRIP[0], 3), round(H.GRIP[1] + g.muzzle[0], 3), round(H.GRIP[2] - g.muzzle[1], 3)]}
    m.gun_scale = H.SCALE
    return m


# =========================================================================== vehicles

def vehicle_palette(team):
    if team == "nato":
        return dict(base="#4f5a34", spots=[("#3e4628", 0.55), ("#2c2f22", 0.7), ("#6a6a44", 0.78)], trim="#2c2f22",
                    canvas="#6a6a48", seat="#2e2a22")
    return dict(base="#b8a070", spots=[("#9a8054", 0.5), ("#7a5a3a", 0.68), ("#8a4a2a", 0.8)], trim="#4a3a26",
                canvas="#8a6a4a", seat="#3a2a1e")


def panel(c, pal, seed, lines=True, rivet=True, camo=True):
    paint(c, pal["base"], pal["spots"] if camo else None, seed, cell=5, noise=4)
    for f in c.faces:
        if lines and f.w > 6 and f.h > 6:
            f.border(shade(pal["base"], 0.7))
        if rivet and f.w > 8 and f.h > 8:
            rivets(f, shade(pal["base"], 1.25), step=5, inset=2)
    for f in c.sides:  # mud splashed up from the ground
        for y in range(f.h * 2 // 3, f.h):
            for x in range(f.w):
                if random.Random(seed * 31 + x * 7 + y).random() < (y - f.h * 2 / 3) / (f.h / 3) * 0.5:
                    f.px(x, y, "#4a3a28")
    return c


def wheel(m, name, pivot, x0, size=12, width=4, res=1):
    b = m.bone(name, pivot, "body")
    px, py, pz = pivot
    tire = b.cube((x0, py - size / 2, pz - size / 2), (width, size, size))
    paint(tire, "#1e1f22", noise=3)
    for f in tire.faces:
        for i in range(0, max(f.w, f.h), 2):
            if f is tire.top or f is tire.bottom or f is tire.front or f is tire.back:
                f.hline(i % f.h, "#2c2d31")  # tread
    for f in (tire.right, tire.left):
        f.border("#141416")
    tire2 = b.cube((x0, py - size / 2, pz - size / 2), (width, size, size), rotation=(45, 0, 0), pivot=pivot, inflate=-0.9)
    paint(tire2, "#1e1f22", noise=3)
    hub_x = x0 - 0.3 if x0 < 0 else x0 + width - 0.7
    hub = b.cube((hub_x, py - 3, pz - 3), (1, 6, 6))
    paint(hub, "#5a5e46", noise=2)
    hub.right.fill("#8a8a80", 2, 2, 4, 4)
    hub.left.fill("#8a8a80", 2, 2, 4, 4)
    return b


def jeep():
    m = Model("vehicle_jeep", bounds=(5.0, 3.0, 1.0))
    m.bone("root", (0, 0, 0))
    m.bone("body", (0, 0, 0), "root")
    mg = m.bone("mounted_gun", (0, 16, 14), "body")
    m.bone("antenna", (12, 16, 22), "body")
    return m


def build_jeep(team):
    pal = vehicle_palette(team)
    m = jeep()
    b = {bn.name: bn for bn in m.bones}
    body = b["body"]
    s = 7 if team == "nato" else 8
    frame = body.cube((-12, 5, -30), (24, 3, 58))
    paint(frame, "#26272a", noise=3)
    tub = panel(body.cube((-14, 8, -14), (28, 9, 40)), pal, s)
    hood = panel(body.cube((-13, 8, -31), (26, 9, 17)), pal, s + 1)
    hood.front.fill(shade(pal["base"], 0.8))
    emblem(hood.front, team, r=5)  # insignia on the hood
    grille = body.cube((-9, 9, -32), (18, 7, 1))
    paint(grille, "#1e1f22", noise=2)
    for x in range(1, grille.front.w, 2):
        grille.front.vline(x, "#3a3c40")
    for x in (-12, 8):
        lamp = body.cube((x, 13, -32.5), (4, 3, 1))
        paint(lamp, "#f4ecc0", noise=1)
        lamp.front.fill("#fff6d0")
        lamp.front.border("#2a2a2a")
    for z, n in ((-30, "f"), (17, "r")):
        fender = panel(body.cube((-16, 12, z), (32, 2, 13)), pal, s + 2, rivet=False)
    bumper_f = body.cube((-15, 5, -34), (30, 3, 2))
    paint(bumper_f, "#26272a", noise=2)
    bumper_r = body.cube((-15, 5, 26), (30, 3, 2))
    paint(bumper_r, "#26272a", noise=2)
    for x in (-13, 10):
        tl = body.cube((x, 13, 26), (3, 2, 1))
        paint(tl, "#c8302c", noise=1)
    spare = body.cube((-5, 9, 26.5), (10, 10, 3))
    paint(spare, "#1e1f22", noise=2)
    spare.back.fill("#5a5e46", 3, 3, 7, 7)
    jerry = panel(body.cube((8, 17, 20), (5, 6, 3)), dict(pal, spots=None), s + 3, camo=False)
    # cabin
    dash = body.cube((-13, 17, -14), (26, 4, 3))
    paint(dash, "#2a2b2e", noise=2)
    dash.back.fill("#7fd08a", 4, 1, 8, 3)  # gauges
    dash.back.fill("#d9c040", 10, 1, 12, 3)
    for x in (-13, 12):
        post = body.cube((x, 17, -14), (1, 11, 1))
        paint(post, pal["trim"], noise=2)
    top = body.cube((-13, 28, -14), (26, 1, 1))
    paint(top, pal["trim"], noise=2)
    glass = body.cube((-12, 18, -13.6), (24, 10, 0))
    for f in glass.faces:
        f.fill("#8fb8cc")
        for i in range(0, f.w, 7):
            for j in range(min(f.h, 4)):
                f.px(i + j, j, "#d8eef6")
    for x in (-11, 3):
        seat = body.cube((x, 17, -10), (8, 3, 8))
        paint(seat, pal["seat"], noise=3)
        back = body.cube((x, 20, -3), (8, 8, 2))
        paint(back, pal["seat"], noise=3)
    bench = body.cube((-12, 17, 8), (24, 3, 8))
    paint(bench, pal["seat"], noise=3)
    bback = body.cube((-12, 20, 15), (24, 7, 2))
    paint(bback, pal["seat"], noise=3)
    col = body.cube((-8.5, 18, -12), (1, 6, 1), rotation=(-35, 0, 0), pivot=(-8, 18, -12))
    paint(col, "#1a1a1a", noise=1)
    wheel_ = body.cube((-11, 22, -10), (6, 6, 1), rotation=(-35, 0, 0), pivot=(-8, 25, -10))
    paint(wheel_, "#1a1a1a", noise=1)
    wheel_.front.fill("#3a3a3a", 2, 2, 4, 4)
    for x in (-14, 13):  # roll bar
        post = body.cube((x, 17, 4), (1, 14, 1))
        paint(post, "#2a2b2e", noise=2)
    rb = body.cube((-14, 31, 4), (28, 1, 1))
    paint(rb, "#2a2b2e", noise=2)
    for i, (x, z) in enumerate(((-15.5, -21), (13.5, -21), (-15.5, 17), (13.5, 17))):
        wheel(m, ["wheel_fl", "wheel_fr", "wheel_rl", "wheel_rr"][i], (x + 2, 6, z + 6), x, 12, 4)
    # Red Fang technicals carry a pintle-mounted machine gun; NATO jeeps a long radio whip.
    mg = b["mounted_gun"]
    post = mg.cube((-1, 16, 13), (2, 10, 2))
    paint(post, "#2a2b2e", noise=2)
    gun = mg.cube((-1.5, 26, 4), (3, 3, 14))
    paint(gun, "#2c2f34", noise=2)
    barrel = mg.cube((-0.5, 27, -8), (1, 1, 12))
    paint(barrel, "#1a1b1e", noise=1)
    shield = mg.cube((-5, 25, 6), (10, 6, 1))
    paint(shield, pal["base"], pal["spots"], s + 5, noise=3)
    ammo = mg.cube((1.5, 24, 9), (3, 3, 4))
    paint(ammo, "#4f5a34", noise=2)
    ant = b["antenna"].cube((12, 17, 22), (1, 24, 1), inflate=-0.3)
    paint(ant, "#1a1a1a", noise=1)
    return m


def build_tank(team):
    pal = vehicle_palette(team)
    m = Model("vehicle_tank", bounds=(7.0, 4.0, 1.5))
    m.bone("root", (0, 0, 0))
    body = m.bone("body", (0, 0, 0), "root")
    turret = m.bone("turret", (0, 17, 2), "body")
    barrel = m.bone("barrel", (0, 21, -14), "turret")
    s = 30 if team == "nato" else 31
    for x0 in (-24, 16):  # tracks with road wheels and sprockets
        track = body.cube((x0, 0, -38), (8, 10, 76))
        paint(track, "#26272a", noise=3)
        for f in (track.top, track.bottom, track.front, track.back):
            for row in range(0, f.h, 3):
                f.hline(row, "#3a3b3f")
        outer = track.right if x0 < 0 else track.left
        outer.fill("#1c1d20", 0, 2, outer.w, outer.h - 2)
        for i in range(7):
            z = -33 + i * 10
            wx = x0 - 0.6 if x0 < 0 else x0 + 7.6
            w = body.cube((wx, 1, z), (1, 7, 7))
            paint(w, "#3e4228", noise=2)
            (w.right if x0 < 0 else w.left).fill("#6a6e50", 2, 2, 5, 5)
    lower = panel(body.cube((-16, 3, -36), (32, 9, 72)), pal, s)
    deck = panel(body.cube((-24, 12, -34), (48, 5, 70)), pal, s + 1)
    emblem(deck.right, team, r=4)
    emblem(deck.left, team, r=4)
    glacis = panel(body.cube((-16, 5, -44), (32, 8, 9), rotation=(-28, 0, 0), pivot=(0, 12, -36)), pal, s + 2)
    for x in (-14, 10):
        lamp = body.cube((x, 13, -35), (4, 3, 1))
        paint(lamp, "#f4ecc0", noise=1)
    grille = body.cube((-12, 17, 22), (24, 1, 10))
    paint(grille, "#1e1f22", noise=2)
    for y in range(0, grille.top.h, 2):
        grille.top.hline(y, "#3a3c40")
    for x in (-10, 6):
        ex = body.cube((x, 13, 35), (4, 3, 2))
        paint(ex, "#3a3330", noise=3)
        ex.back.fill("#121212", 1, 1, 3, 2)
    for i, z in enumerate((-30, 28)):
        box = panel(body.cube((-22, 17, z - 3), (6, 3, 6)), pal, s + 10 + i, rivet=False)
        box2 = panel(body.cube((16, 17, z - 3), (6, 3, 6)), pal, s + 12 + i, rivet=False)
    # turret
    tb = panel(turret.cube((-14, 17, -12), (28, 9, 28)), pal, s + 3)
    emblem(tb.right, team, r=4)
    emblem(tb.left, team, r=4)
    for side, sx in ((-1, -14), (1, 8)):
        cheek = panel(turret.cube((sx, 17, -18), (6, 8, 8), rotation=(0, side * 20, 0), pivot=(sx + 3, 21, -12)), pal, s + 4)
    bustle = panel(turret.cube((-12, 18, 16), (24, 7, 8)), pal, s + 5)
    rack = turret.cube((-13, 25, 17), (26, 2, 8))
    paint(rack, "#2a2b2e", noise=2)
    for i in range(3):
        crate = turret.cube((-10 + i * 7, 27, 18), (6, 3, 5))
        paint(crate, "#5a6a3a" if i % 2 == 0 else "#6a5030", noise=4, seed=s + i)
    cup = panel(turret.cube((2, 26, -2), (8, 3, 8)), pal, s + 6, rivet=False)
    hatch = turret.cube((-9, 26, 2), (7, 1, 7))
    paint(hatch, shade(pal["base"], 0.85), noise=3)
    hmg = turret.cube((5, 29, -6), (2, 2, 8))
    paint(hmg, "#2c2f34", noise=2)
    hb = turret.cube((5.5, 29.5, -14), (1, 1, 8))
    paint(hb, "#1a1b1e", noise=1)
    for side_x in (-16, 13):
        for j in range(3):
            sm = turret.cube((side_x, 22 + (j % 2), -8 + j * 3), (3, 2, 2))
            paint(sm, "#3a3d30", noise=2)
    for x, h in ((-11, 26), (10, 20)):
        ant = turret.cube((x, 26, 20), (1, h, 1), inflate=-0.35)
        paint(ant, "#1a1a1a", noise=1)
    # barrel
    mant = panel(barrel.cube((-6, 17, -17), (12, 9, 5)), pal, s + 7, rivet=False)
    sleeve = barrel.cube((-2.5, 19, -34), (5, 5, 17))
    paint(sleeve, pal["base"], pal["spots"], s + 8, cell=5, noise=3)
    tube = barrel.cube((-1.5, 20, -62), (3, 3, 28))
    paint(tube, shade(pal["base"], 0.9), noise=3)
    evac = barrel.cube((-2, 19.5, -48), (4, 4, 5))
    paint(evac, shade(pal["base"], 0.8), noise=2)
    brake = barrel.cube((-2.5, 19, -67), (5, 5, 5))
    paint(brake, "#2a2b2e", noise=2)
    brake.front.fill("#0a0a0a", 3, 3, 7, 7)
    for f in (brake.right, brake.left):
        f.fill("#0a0a0a", 2, 2, f.w - 2, 4)
    return m


# =========================================================================== projectiles

def projectile_models():
    out = {}
    m = Model("projectile_bullet", bounds=(1, 1, 0))
    b = m.bone("root", (0, 0, 0))
    c = b.cube((-0.5, -0.5, -4), (1, 1, 8))
    for f in c.faces:
        f.fill("#ffe08a")
    c.top.fill("#fff6d0")
    out["bullet"] = m
    m = Model("projectile_sniper_bullet", bounds=(1, 1, 0))
    b = m.bone("root", (0, 0, 0))
    c = b.cube((-0.5, -0.5, -6), (1, 1, 12))
    for f in c.faces:
        f.fill("#fff0b0")
    out["sniper_bullet"] = m

    m = Model("projectile_rocket", bounds=(1.5, 1.5, 0))
    b = m.bone("root", (0, 0, 0))
    paint(b.cube((-1.5, -1.5, -6), (3, 3, 10)), "#5b6339", noise=3)
    paint(b.cube((-1, -1, -9), (2, 2, 3)), "#454b2b", noise=2)
    paint(b.cube((-0.5, -0.5, -10), (1, 1, 1)), "#1d1f23", noise=1)
    for rot in (0, 90):
        fin = b.cube((-3, -0.5, 3), (6, 1, 3), rotation=(0, 0, rot), pivot=(0, 0, 4))
        paint(fin, "#3d4148", noise=2)
    flame = b.cube((-1, -1, 4), (2, 2, 3))
    for f in flame.faces:
        f.fill("#ffb040")
    out["rocket"] = m

    m = Model("projectile_tank_shell", bounds=(1.5, 1.5, 0))
    b = m.bone("root", (0, 0, 0))
    paint(b.cube((-1.5, -1.5, -5), (3, 3, 9)), "#5a5e46", noise=2)
    paint(b.cube((-1, -1, -7), (2, 2, 2)), "#c9a43a", noise=2)
    paint(b.cube((-0.5, -0.5, -8), (1, 1, 1)), "#1d1f23", noise=1)
    glow = b.cube((-1, -1, 4), (2, 2, 2))
    for f in glow.faces:
        f.fill("#ff9030")
    out["tank_shell"] = m

    for key, builder in (("frag_grenade", H.frag_grenade), ("smoke_grenade", H.smoke_grenade)):
        g = builder()
        m = Model(f"projectile_{key}", bounds=(1, 1, 0))
        bone = m.bone("root", (0, 0, 0))
        for c in gun_cubes(g):
            ox, oy, oz = c.origin
            c.origin = (ox - H.GRIP[0], oy - H.GRIP[1], oz - H.GRIP[2])
            if c.pivot:
                px, py, pz = c.pivot
                c.pivot = (px - H.GRIP[0], py - H.GRIP[1], pz - H.GRIP[2])
            c.bone = "root"
            bone.cubes.append(c)
        bone.scale = H.SCALE
        out[key] = m
    return out


# =========================================================================== the capture flag

FLAG_SKINS = ["flag_neutral", "flag_nato", "flag_redfang"]


def capture_flag(owner):
    m = Model("capture_flag", bounds=(3.0, 6.0, 2.5))
    root = m.bone("root", (0, 0, 0))
    pole = m.bone("pole", (0, 0, 0), "root")
    cloth = m.bone("cloth", (1, 36, 0), "pole")
    paint(pole.cube((-1, 0, -1), (2, 48, 2)), "#b9bdc2", noise=2)
    paint(pole.cube((-1.5, 48, -1.5), (3, 2, 3)), "#d9c040", noise=2)
    paint(pole.cube((-3, 0, -3), (6, 2, 6)), "#5d636b", noise=3)
    colours = {"flag_neutral": ("#e9e7df", "#b9b7ae"), "flag_nato": ("#2d5fa8", "#1d4078"),
               "flag_redfang": ("#c8302c", "#7e1a17")}
    main, edge = colours[owner]
    segs = []
    for i in range(4):
        seg = m.bone(f"cloth{i}", (1 + i * 6, 36, 0), "cloth" if i == 0 else f"cloth{i - 1}")
        c = seg.cube((1 + i * 6, 24, -0.5), (6, 12, 1))
        paint(c, main, noise=3, seed=i)
        for f in (c.front, c.back):
            f.hline(0, edge)
            f.hline(f.h - 1, edge)
        segs.append(c)
    team = {"flag_nato": "nato", "flag_redfang": "redfang"}.get(owner)
    if team:
        for f in (segs[1].front, segs[1].back):
            emblem(f, team, cx=f.w - 1, cy=f.h // 2, r=4)
        for f in (segs[2].front, segs[2].back):
            emblem(f, team, cx=0, cy=f.h // 2, r=4)
    return m


# =========================================================================== blocks with shapes

def block_model(name):
    m = Model(f"block_{name}", bounds=(1.5, 1.5, 0.5))
    return m, m.bone("block", (0, 0, 0))


def sandbags():
    m, b = block_model("sandbags")
    rng = random.Random(4)
    for row in range(3):
        y = row * 5
        offset = -4 if row % 2 else 0
        for i in range(3):
            x = -8 + offset + i * 8
            x0, x1 = max(-8, x), min(8, x + 8)
            if x1 - x0 < 2:
                continue
            bag = b.cube((x0, y, -7), (x1 - x0, 5, 14), inflate=-0.15)
            tone = rng.choice(["#b8a77a", "#ab9a6c", "#c4b386"])
            paint(bag, tone, noise=6, seed=row * 3 + i)
            for f in bag.sides:
                f.border(shade(tone, 0.72))
                f.hline(f.h // 2, shade(tone, 0.85))
            bag.top.border(shade(tone, 0.8))
    return m


def barbed_wire():
    m, b = block_model("barbed_wire")
    for i, ang in enumerate((0, 45, 90, 135)):
        for z in (-5, 0, 5):
            ring = b.cube((-6, 2, z), (12, 12, 0), rotation=(0, 0, ang), pivot=(0, 8, z))
            for f in ring.faces:
                f.fill(None)
                f.border("#8a9098")
                for x in range(0, f.w, 3):
                    f.px(x, 0, "#c4c9cf")
                    f.px(x, f.h - 1, "#c4c9cf")
    for y, z in ((2, -8), (13, -8)):
        wire = b.cube((-8, y, -8), (0, 1, 16))
        for f in wire.faces:
            f.fill("#8a9098")
    paint(b.cube((-7, 0, -1), (1, 14, 1)), "#4a3a28", noise=2)
    paint(b.cube((6, 0, -1), (1, 14, 1)), "#4a3a28", noise=2)
    return m


def ammo_crate():
    m, b = block_model("ammo_crate")
    body = b.cube((-7, 0, -6), (14, 10, 12))
    paint(body, "#4d5a33", noise=5, seed=1)
    for f in body.sides:
        f.border("#3a4424")
        f.fill("#d9d2a0", 3, 3, f.w - 3, 4)
        f.fill("#d9d2a0", 3, 5, f.w - 6, 6)
    lid = b.cube((-7.5, 10, -6.5), (15, 2, 13))
    paint(lid, "#46522b", noise=4, seed=2)
    for x in (-8, 7):
        h_ = b.cube((x, 5, -2), (1, 2, 4))
        paint(h_, "#2a2b2e", noise=1)
    for x in (-5, 2):
        rope = b.cube((x, 12, -1), (3, 1, 2))
        paint(rope, "#2a2b2e", noise=1)
    rounds = b.cube((-5, 12, 2), (4, 2, 3))
    paint(rounds, "#c9a43a", noise=3)
    return m


def spawn_beacon():
    m, b = block_model("spawn_beacon")
    base = b.cube((-5, 0, -5), (10, 6, 10))
    paint(base, "#2f3438", noise=3)
    for f in base.sides:
        f.fill("#2b6fd6", 2, 1, f.w - 2, 2)
    top = b.cube((-4, 6, -4), (8, 2, 8))
    paint(top, "#3d4148", noise=2)
    top.top.fill("#7fd08a", 2, 2, 6, 4)
    ant = b.cube((2, 8, 2), (1, 8, 1), inflate=-0.25)
    paint(ant, "#1a1a1a", noise=1)
    lamp = b.cube((1.5, 15, 1.5), (2, 1, 2))
    for f in lamp.faces:
        f.fill("#6fb8ff")
    for x, z in ((-6, -6), (4, -6), (-6, 4), (4, 4)):
        leg = b.cube((x, 0, z), (2, 1, 2))
        paint(leg, "#1a1a1a", noise=1)
    return m


BLOCK_MODELS = {"sandbags": sandbags, "barbed_wire": barbed_wire, "ammo_crate": ammo_crate, "spawn_beacon": spawn_beacon}


# =========================================================================== small props for item icons

def prop(key, build):
    # ammunition is drawn side-on and tilted like the guns; other props from above
    g = H.Held(key, "pistol" if key.startswith("ammo_") and key not in ("ammo_9mm", "ammo_45acp") else "gear")
    build(g)
    return g


BRASS_C, COPPER_C, STEEL_C = "#c9a43a", "#b0703a", "#8d9299"


def _rounds(g, n, length, r, tip_len, spacing, case=BRASS_C, tip=COPPER_C):
    """A row of loose cartridges standing side by side."""
    for i in range(n):
        s = (i - (n - 1) / 2) * spacing
        g.rod(-length / 2, length / 2 - tip_len, 0, s, r, case)
        g.rod(-length / 2 - 1, -length / 2, 0, s, r * 0.9, shade(case, 0.8))
        g.rod(length / 2 - tip_len, length / 2 - tip_len / 3, 0, s, r * 0.75, tip)
        g.rod(length / 2 - tip_len / 3, length / 2, 0, s, max(0.5, r * 0.4), tip)


def _ammo_box(g, colour, label, rounds):
    box = g.box(-8, 8, -5, 3, -6, 6, colour)
    for side in ("right", "left"):
        H.mark(box, side, -6, 6, -3, 1, label)
    g.box(-8, 8, 3, 4, -6, 6, shade(colour, 0.8))
    for i, s in enumerate((-3, 0, 3)):
        g.rod(4, 4 + rounds[0], -1, s, rounds[1], BRASS_C)
        g.rod(4 + rounds[0], 4 + rounds[0] + 2, -1, s, rounds[1] * 0.7, COPPER_C)


def _ammo_9mm(g):
    _ammo_box(g, "#2d3b6a", "#e9e7df", (4, 1.2))


def _ammo_45acp(g):
    _ammo_box(g, "#6a2d2d", "#e9e7df", (4, 1.5))


def _ammo_556(g):  # a 10-round stripper clip of 5.56
    g.box(-1, 1, -4, 4, -8, 8, STEEL_C)
    _rounds(g, 5, 18, 1.1, 6, 3)


def _ammo_762x39(g):
    _rounds(g, 4, 18, 1.4, 6, 3.4, case="#9a8a5a")


def _ammo_762x54r(g):
    _rounds(g, 4, 24, 1.5, 8, 3.6)


def _ammo_338(g):
    _rounds(g, 3, 30, 1.9, 10, 4.6)


def _ammo_12g(g):
    for sx in (-3, 3):
        g.rod(-4, 8, 0, sx, 2.2, "#c8302c")
        g.rod(-7, -4, 0, sx, 2.4, BRASS_C)


def _ammo_84mm(g):
    g.rod(-14, 6, 0, 0, 4, "#6a7040")
    g.rod(6, 12, 0, 0, 3, "#4a5530")
    g.rod(12, 15, 0, 0, 1.5, "#1d1f23")
    g.rod(-16, -14, 0, 0, 4.2, BRASS_C)


def _ammo_pg7v(g):
    g.rod(-14, -2, 0, 0, 1.5, "#3a4228")
    g.rod(-2, 4, 0, 0, 3.5, "#4a5530")
    g.rod(4, 10, 0, 0, 4.5, "#4a5530")
    g.rod(10, 14, 0, 0, 3, "#4a5530")
    g.rod(14, 17, 0, 0, 1.5, "#1d1f23")
    g.box(-16, -12, -4, 4, -0.5, 0.5, "#3d4148")
    g.box(-16, -12, -0.5, 0.5, -4, 4, "#3d4148")


def _field_ration(g):
    pouch = g.box(-7, 8, -2, 2, -6, 6, "#8a7550")
    H.mark(pouch, "up", -2, 4, 0, 0, "#e9e7df", -4, 4)
    H.mark(pouch, "up", -1, 3, 0, 0, "#2a2a26", -3, 3)
    g.box(8, 9, -1.5, 1.5, -6, 6, "#6a5838")


PROPS = {"ammo_9mm": _ammo_9mm, "ammo_45acp": _ammo_45acp, "ammo_556": _ammo_556, "ammo_762x39": _ammo_762x39,
         "ammo_762x54r": _ammo_762x54r, "ammo_338": _ammo_338, "ammo_12g": _ammo_12g, "ammo_84mm": _ammo_84mm,
         "ammo_pg7v": _ammo_pg7v, "field_ration": _field_ration}


def props():
    """Models for the icons of items that are not held as 3D models: ammunition, rations and attachments."""
    import attach
    out = {k: prop(k, fn).finish() for k, fn in PROPS.items()}
    out.update({k: attach.standalone(k) for k in attach.CATALOGUE})
    return out
