#!/usr/bin/env python3
"""Paints the 2D images of the add-on: inventory icons (rendered from the 3D models, so the icon matches what
you hold), the flag-base block textures and the pack icon.

Usage:  python3 tools/gen/art.py            (writes into the packs)
        python3 tools/gen/art.py --preview  (also writes docs/images/items.png)
"""
from __future__ import annotations

import sys

import numpy as np
from PIL import Image

import held as H
import models as M
from defs import BP, NS, ROOT, RP, item_ids
from viewer import icon_render

OUTLINE = (24, 22, 20, 255)


def hexc(h, a=255):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)


def outline(img):
    a = np.asarray(img).copy()
    alpha = a[..., 3] > 0
    grow = np.zeros_like(alpha)
    grow[1:, :] |= alpha[:-1, :]
    grow[:-1, :] |= alpha[1:, :]
    grow[:, 1:] |= alpha[:, :-1]
    grow[:, :-1] |= alpha[:, 1:]
    a[grow & ~alpha] = OUTLINE
    return Image.fromarray(a, "RGBA")


def icon_for(key, g):
    """Guns and blades lie diagonally with the muzzle to the upper right; gear is shown from above."""
    if g.hold in ("rifle", "pistol", "launcher", "blade"):
        rot, yaw, pitch = (45.0, 0.0, 0.0), 90.0, 0.0
    elif key in ("frag_grenade", "smoke_grenade"):
        rot, yaw, pitch = (0.0, 0.0, 0.0), 60.0, 20.0
    else:
        rot, yaw, pitch = (60.0, 0.0, 0.0), 120.0, 25.0
    img = icon_render(g.model, {"item": (rot, (0, 0, 0), H.SCALE)}, yaw=yaw, pitch=pitch, size=32, margin=2)
    return outline(brighten(img))


def vehicle_icon(model):
    return outline(brighten(icon_render(model, {}, yaw=140.0, pitch=25.0, size=32, margin=1)))


def brighten(img, f=1.22):
    """Icons sit on the inventory's grey: lift dark gunmetal so the parts read."""
    a = np.asarray(img).astype(np.float32)
    a[..., :3] = np.clip(a[..., :3] * f + 10, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def items():
    out = RP / "textures" / "items" / NS
    out.mkdir(parents=True, exist_ok=True)
    built = H.build_all()
    built.update(M.props())
    icons = {}
    for key in item_ids():
        if key in built:
            img = icon_for(key, built[key])
        elif key == "jeep_kit":
            img = vehicle_icon(M.build_jeep("nato"))
        elif key == "tank_kit":
            img = vehicle_icon(M.build_tank("nato"))
        else:
            raise KeyError(f"no icon for {key}")
        img.save(out / f"{key}.png")
        icons[key] = img
    return icons


def flag_bases():
    out = RP / "textures" / "blocks" / NS
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(3)
    colours = {"flag_neutral": "#d8d8d8", "flag_nato": "#2d5fa8", "flag_redfang": "#c8302c"}
    for name, col in colours.items():
        img = Image.new("RGBA", (16, 16))
        c = hexc(col)
        for y in range(16):
            for x in range(16):
                edge = x < 2 or y < 2 or x > 13 or y > 13
                px = c if edge else (128, 130, 132, 255)
                f = 1 + rng.uniform(-0.06, 0.06)
                img.putpixel((x, y), tuple(int(min(255, v * f)) for v in px[:3]) + (255,))
        for y in range(5, 11):
            for x in range(5, 11):
                if (x - 7.5) ** 2 + (y - 7.5) ** 2 <= 9:
                    img.putpixel((x, y), c)
        img.save(out / f"{name}.png")


def pack_icon():
    size = 256
    yy, xx = np.mgrid[0:size, 0:size]
    d = np.clip(np.hypot(xx - 128, yy - 170) / 210, 0, 1)
    top, bottom = np.array([200, 120, 60]), np.array([30, 28, 30])
    bg = (top[None, None, :] * (1 - d[..., None]) + bottom[None, None, :] * d[..., None]).astype(np.uint8)
    img = Image.fromarray(np.dstack([bg, np.full((size, size), 255, np.uint8)]), "RGBA")
    tank = M.build_tank("nato")
    img.alpha_composite(icon_render(tank, {}, yaw=145.0, pitch=18.0, size=200, margin=4), (50, 60))
    soldier = M.soldier("nato_rifleman", "nato_woodland")
    pose = {"rightArm": ((-90.0, -8.0, 0.0), (0, 0, 0), 1.0), "leftArm": ((-86.0, 38.0, 0.0), (0, 0, 0), 1.0),
            "gun": ((0, 0, 0), (0, 0, 0), H.SCALE)}
    img.alpha_composite(icon_render(soldier, pose, yaw=-35.0, pitch=8.0, size=170, margin=4), (0, 86))
    for path in (BP / "pack_icon.png", RP / "pack_icon.png"):
        img.save(path)
    return img


def preview(icons):
    docs = ROOT / "docs" / "images"
    docs.mkdir(parents=True, exist_ok=True)
    names = list(icons)
    cols = 9
    rows = (len(names) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * 72 + 8, rows * 72 + 8), hexc("#2a2d33"))
    for i, name in enumerate(names):
        sheet.alpha_composite(icons[name].resize((64, 64), Image.NEAREST), (8 + (i % cols) * 72, 8 + (i // cols) * 72))
    sheet.save(docs / "items.png")


def main():
    icons = items()
    flag_bases()
    pack_icon()
    if "--preview" in sys.argv:
        preview(icons)
    print(f"art: {len(icons)} icons, flag bases, pack icon")


if __name__ == "__main__":
    main()
