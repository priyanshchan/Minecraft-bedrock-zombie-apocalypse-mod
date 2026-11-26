#!/usr/bin/env python3
"""Draws the held 3D items as the game shows them: in third person on the player's skeleton (in the aiming
pose the add-on plays for guns) and in first person from the player's eye.

The first-person arm uses the transform the game applies to the right arm in first person: rotation
(95, -45, 115) and translation (13.5, -10, 12), with the item bone moved (0, 0, -1), as documented in the
Bedrock wiki's attachables guide. Adapted from the Overlord add-on's tools/weapon_view.py.

Usage:  python3 tools/gen/viewer.py [key ...]     (writes docs/images/held/*.png)
"""
from __future__ import annotations

import math
import sys

import numpy as np
from PIL import Image, ImageDraw

from defs import ROOT
from modelkit import Model

SKIN, SHIRT, PANTS = (196, 150, 118), (74, 90, 60), (60, 66, 50)
PLAYER = {
    "body": (None, (0, 24, 0), [((-4, 12, -2), (8, 12, 4), SHIRT)]),
    "head": ("body", (0, 24, 0), [((-4, 24, -4), (8, 8, 8), SKIN)]),
    "rightArm": ("body", (-5, 22, 0), [((-8, 12, -2), (4, 12, 4), SKIN)]),
    "rightItem": ("rightArm", (-6, 15, 1), []),
    "leftArm": ("body", (5, 22, 0), [((4, 12, -2), (4, 12, 4), SKIN)]),
    "rightLeg": (None, (-1.9, 12, 0), [((-3.9, 0, -2), (4, 12, 4), PANTS)]),
    "leftLeg": (None, (1.9, 12, 0), [((-0.1, 0, -2), (4, 12, 4), PANTS)]),
}
FIRST_PERSON_ARM = {"rightArm": ((95, -45, 115), (13.5, -10, 12), 1.0), "rightItem": ((0, 0, 0), (0, 0, -1), 1.0)}


def third_person_arms(pose):
    """The vanilla 'holding an item' raise of the right arm plus the add-on's pose for that kind of item."""
    from poses import POSES
    p = POSES.get(pose, {})
    right = p.get("rightArm", (0, 0, 0))
    left = p.get("leftArm", (0, 0, 0))
    return {"rightArm": ((-18 + right[0], right[1], right[2]), (0, 0, 0), 1.0),
            "leftArm": (tuple(left), (0, 0, 0), 1.0)}


def rot_matrix(rx, ry, rz):
    """Bedrock bone rotation: X and Z rotate left-handed, Y right-handed (as modelkit renders it)."""
    ax, ay, az = math.radians(-rx), math.radians(ry), math.radians(-rz)
    cx, sx, cy, sy, cz, sz = math.cos(ax), math.sin(ax), math.cos(ay), math.sin(ay), math.cos(az), math.sin(az)
    mx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    my = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    mz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return mz @ my @ mx


def transform(points, bone, bones, anim):
    while bone is not None:
        parent, pivot, rotation = bones[bone]
        rot, pos, scale = anim.get(bone, ((0, 0, 0), (0, 0, 0), 1.0))
        total = tuple(a + b for a, b in zip(rotation or (0, 0, 0), rot))
        p = np.array(pivot, float)
        points = ((points - p) * scale) @ rot_matrix(*total).T + p + np.array(pos, float)
        bone = parent
    return points


class Canvas:
    def __init__(self, w, h, bg=(40, 42, 52)):
        self.w, self.h = w, h
        self.color = np.zeros((h, w, 3), np.float32)
        self.color[:] = bg
        self.depth = np.full((h, w), 1e9, np.float32)

    def quad(self, scr, z, sample, light):
        o, a, b = scr
        e1, e2 = a - o, b - o
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-9:
            return
        xs = [o[0], a[0], b[0], a[0] + e2[0]]
        ys = [o[1], a[1], b[1], a[1] + e2[1]]
        x0, x1 = max(0, int(min(xs))), min(self.w - 1, int(max(xs)) + 1)
        y0, y1 = max(0, int(min(ys))), min(self.h - 1, int(max(ys)) + 1)
        if x0 > x1 or y0 > y1:
            return
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        rx, ry = gx - o[0], gy - o[1]
        s = (rx * e2[1] - ry * e2[0]) / det
        t = (e1[0] * ry - e1[1] * rx) / det
        inside = (s >= 0) & (s < 1) & (t >= 0) & (t < 1)
        zz = z[0] + s * (z[1] - z[0]) + t * (z[2] - z[0])
        rgb, mask = sample(np.clip(s, 0, 0.9999), np.clip(t, 0, 0.9999))
        sub_d = self.depth[y0:y1 + 1, x0:x1 + 1]
        sub_c = self.color[y0:y1 + 1, x0:x1 + 1]
        m = inside & mask & (zz < sub_d)
        sub_c[m] = np.clip(rgb[m] * light, 0, 255)
        sub_d[m] = zz[m]

    def image(self):
        return Image.fromarray(self.color.astype(np.uint8), "RGB")


def faces(origin, size, inflate=0.0):
    x0, y0, z0 = (origin[i] - inflate for i in range(3))
    x1, y1, z1 = (origin[i] + size[i] + inflate for i in range(3))
    w, h, d = size
    return [
        ((x0, y1, z0), (x1, y1, z0), (x0, y0, z0), (d, d, w, h), 1.0),
        ((x1, y1, z1), (x0, y1, z1), (x1, y0, z1), (2 * d + w, d, w, h), 0.7),
        ((x0, y1, z1), (x0, y1, z0), (x0, y0, z1), (0, d, d, h), 0.82),
        ((x1, y1, z0), (x1, y1, z1), (x1, y0, z0), (d + w, d, d, h), 0.82),
        ((x0, y1, z1), (x1, y1, z1), (x0, y1, z0), (d, 0, w, d), 1.12),
        ((x0, y0, z0), (x1, y0, z0), (x0, y0, z1), (d + w, 0, w, d), 0.6),
    ]


def draw(canvas, project, model: Model, anim, show=("body", "head", "rightArm", "leftArm", "rightLeg", "leftLeg")):
    bones = {name: (parent, pivot, None) for name, (parent, pivot, _c) in PLAYER.items()}
    for b in model.bones:
        if b.name not in bones:
            bones[b.name] = (b.parent, b.pivot, b.rotation)
    for name, (parent, pivot, cubes) in PLAYER.items():
        if name not in show:
            continue
        for origin, size, col in cubes:
            for tl, tr, bl, _uv, light in faces(origin, size):
                pts = transform(np.array([tl, tr, bl], float), name, bones, anim)
                scr, z = project(pts)
                if scr is None:
                    continue
                canvas.quad(scr, z, lambda s, t, col=col: (np.broadcast_to(np.array(col, np.float32), s.shape + (3,)),
                                                          np.ones(s.shape, bool)), light)
    tex = np.asarray(model.hd()).astype(np.float32)
    K = model.res if model.res > 1 else model.HD
    for b in model.bones:
        for c in b.cubes:
            u, v = c.uv
            for tl, tr, bl, (du, dv, tw, th), light in faces(c.origin, c.size, c.inflate):
                if tw == 0 or th == 0:
                    continue
                pts = np.array([tl, tr, bl], float)
                if c.rotation:
                    pv = np.array(c.pivot or (0, 0, 0), float)
                    pts = (pts - pv) @ rot_matrix(*c.rotation).T + pv
                pts = transform(pts, b.name, bones, anim)
                scr, z = project(pts)
                if scr is None:
                    continue

                def sample(s, t, u=u + du, v=v + dv, tw=tw, th=th):
                    tx = np.clip(((u + s * tw) * K).astype(int), 0, tex.shape[1] - 1)
                    ty = np.clip(((v + t * th) * K).astype(int), 0, tex.shape[0] - 1)
                    px = tex[ty, tx]
                    return px[..., :3], px[..., 3] > 0
                canvas.quad(scr, z, sample, light)


def hold_anim(hold, view):
    from held import FP_SCALE, SCALE
    from holds import compute
    third, first = compute()[hold]
    rot, pos = third if view == "third" else first
    return {"item": (rot, pos, SCALE if view == "third" else FP_SCALE)}


def third_person(model, hold, pose, size=(360, 420), yaw=-60.0, pitch=12.0, scale=7.0, extra=None):
    canvas = Canvas(*size)
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    cam = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]]) @ np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])

    def project(pts):
        q = pts @ cam.T
        scr = np.stack([q[:, 0] * scale + size[0] / 2, size[1] - 50 - q[:, 1] * scale], axis=1)
        return scr, q[:, 2]
    anim = third_person_arms(pose)
    anim.update(hold_anim(hold, "third"))
    anim.update(extra or {})
    draw(canvas, project, model, anim)
    return canvas.image()


def first_person(model, hold, size=(480, 300), fov=70.0, extra=None):
    canvas = Canvas(*size, bg=(118, 168, 220))
    eye = np.array([0.0, 24.0, 0.0])
    f = (size[1] / 2) / math.tan(math.radians(fov / 2))

    def project(pts):
        q = pts - eye
        depth = q[:, 2]
        if np.any(depth < 0.5):
            return None, None
        scr = np.stack([size[0] / 2 + q[:, 0] / depth * f, size[1] / 2 - q[:, 1] / depth * f], axis=1)
        return scr, depth
    anim = dict(FIRST_PERSON_ARM)
    anim.update(hold_anim(hold, "first"))
    anim.update(extra or {})
    draw(canvas, project, model, anim, show=("rightArm",))
    img = canvas.image()
    d = ImageDraw.Draw(img)
    d.line([(size[0] / 2 - 6, size[1] / 2), (size[0] / 2 + 6, size[1] / 2)], fill=(255, 255, 255))
    d.line([(size[0] / 2, size[1] / 2 - 6), (size[0] / 2, size[1] / 2 + 6)], fill=(255, 255, 255))
    return img


def main(keys):
    from held import build_all
    out = ROOT / "docs" / "images" / "held"
    out.mkdir(parents=True, exist_ok=True)
    items = build_all()
    for key, item in items.items():
        if keys and key not in keys:
            continue
        side = item.model.render(yaw=-90, pitch=0, scale=13, size=(420, 220))
        a = third_person(item.model, item.hold, item.hold)
        b = third_person(item.model, item.hold, item.hold, yaw=30)
        c = first_person(item.model, item.hold)
        sheet = Image.new("RGB", (420 + 360 * 2 + 480, 420), (30, 32, 40))
        sheet.paste(side.convert("RGB"), (0, 100))
        sheet.paste(a, (420, 0))
        sheet.paste(b, (780, 0))
        sheet.paste(c, (1140, 60))
        sheet.save(out / f"{key}.png")
    print(f"viewer: drew {len(items)} items into {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main(sys.argv[1:])


def icon_render(model, anim, yaw=90.0, pitch=20.0, size=32, margin=1, light_dir=True):
    """An orthographic render of a model fitted into a size x size icon with a transparent background."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    cam = np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]]) @ np.array([[cy, 0, -sy], [0, 1, 0], [sy, 0, cy]])
    bones = {name: (parent, pivot, None) for name, (parent, pivot, _c) in PLAYER.items()}
    for b in model.bones:
        if b.name not in bones:
            bones[b.name] = (b.parent, b.pivot, b.rotation)
    pts_all = []
    for b in model.bones:
        for c in b.cubes:
            for tl, tr, bl, _uv, _l in faces(c.origin, c.size, c.inflate):
                pts = np.array([tl, tr, bl, (tr[0] + bl[0] - tl[0], tr[1] + bl[1] - tl[1], tr[2] + bl[2] - tl[2])], float)
                if c.rotation:
                    pv = np.array(c.pivot or (0, 0, 0), float)
                    pts = (pts - pv) @ rot_matrix(*c.rotation).T + pv
                pts_all.append(transform(pts, b.name, bones, anim) @ cam.T)
    allp = np.concatenate(pts_all)
    lo, hi = allp[:, :2].min(axis=0), allp[:, :2].max(axis=0)
    span = max(hi - lo) or 1.0
    scale = (size - 2 * margin) / span
    centre = (lo + hi) / 2
    canvas = Canvas(size, size, bg=(0, 0, 0))

    def project(pts):
        q = pts @ cam.T
        scr = np.stack([(q[:, 0] - centre[0]) * scale + size / 2, size / 2 - (q[:, 1] - centre[1]) * scale], axis=1)
        return scr, q[:, 2]
    draw(canvas, project, model, anim, show=())
    rgb = canvas.color.astype(np.uint8)
    alpha = (canvas.depth < 1e8).astype(np.uint8) * 255
    return Image.fromarray(np.dstack([rgb, alpha]), "RGBA")


def sample(anim, t):
    """Bone transforms {bone: (rotation, position, scale)} of an animation (gunanims JSON) at time t."""
    out = {}

    def at(keys):
        times = sorted((float(k), v) for k, v in keys.items())
        if t <= times[0][0]:
            return times[0][1]
        for (t0, v0), (t1, v1) in zip(times, times[1:]):
            if t0 <= t <= t1:
                k = 0 if t1 == t0 else (t - t0) / (t1 - t0)
                return [a + (b - a) * k for a, b in zip(v0, v1)]
        return times[-1][1]
    for bone, channels in anim["bones"].items():
        rot = at(channels["rotation"]) if "rotation" in channels else (0, 0, 0)
        pos = at(channels["position"]) if "position" in channels else (0, 0, 0)
        sc = at(channels["scale"])[0] if "scale" in channels else 1.0
        out[bone] = (tuple(rot), tuple(pos), sc)
    return out


def frames(key, action, times, view="first"):
    """Renders a held gun at several moments of one of its animations (first or third person)."""
    import gunanims
    from held import ALL
    g = ALL[key]().finish()
    a = gunanims.build(key)[action].json()
    imgs = []
    for t in times:
        extra = sample(a, t)
        if view == "first":
            img = first_person(g.model, g.hold, extra=extra)
        else:
            img = third_person(g.model, g.hold, g.hold, extra=extra)
        imgs.append(img)
    return imgs
