#!/usr/bin/env python3
"""The README's weapon images: side views of every gun, guns held in first and third person, attachment loadouts
and animation frames.

Usage:  python3 tools/gen/docsheets.py
"""
from __future__ import annotations

from PIL import Image, ImageDraw

import attach
import gunsheet
import held as H
import viewer
from defs import GUNS, ROOT

OUT = ROOT / "docs" / "images"
NAMES = dict((g[0], g[1]) for g in GUNS)


def label(img, text, xy=(8, 6), fill=(235, 235, 235, 255)):
    ImageDraw.Draw(img).text(xy, text, fill=fill)
    return img


def held_views():
    """Third person (two angles) and first person of a few guns."""
    keys = ["m4a1", "ak47", "awm", "glock17"]
    rows = []
    for k in keys:
        g = H.build_gun(k, False)
        a = viewer.third_person(g.model, g.hold, g.hold)
        b = viewer.third_person(g.model, g.hold, g.hold, yaw=30)
        c = viewer.first_person(g.model, g.hold)
        row = Image.new("RGB", (360 * 2 + 480, 420), (30, 32, 40))
        row.paste(a, (0, 0))
        row.paste(b, (360, 0))
        row.paste(c, (720, 60))
        label(row, NAMES[k])
        rows.append(row)
    sheet = Image.new("RGB", (rows[0].width, sum(r.height for r in rows)))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, i * r.height))
    sheet.save(OUT / "guns.png")


LOADOUTS = [
    ("m4a1", ["red_dot", "vertical_grip", "flash_hider"], "M4A1: red dot, vertical grip, flash hider"),
    ("m4a1", ["variable_6x", "rifle_suppressor", "bipod", "laser_light", "precision_stock"], "M4A1: 1-6x, suppressor, bipod, laser-light, precision stock"),
    ("m4a1", ["holo_magnifier", "compensator", "angled_grip", "drum_mag", "heavy_stock"], "M4A1: holo + magnifier, compensator, angled grip, drum, heavy stock"),
    ("ak47", ["combat_4x", "muzzle_brake", "stubby_grip", "extended_mag", "flashlight"], "AKM: 4x, brake, stubby grip, extended mag, flashlight"),
    ("awm", ["sniper_12x", "rifle_suppressor", "bipod"], "AWM: 12x scope, suppressor, bipod"),
    ("mp5", ["holo_sight", "pistol_suppressor", "laser_sight", "quick_mag"], "MP5A3: holo, suppressor, laser, quick-pull mag"),
    ("rem870", ["reflex_sight", "full_choke", "flashlight", "extended_tube"], "Remington 870: reflex, full choke, light, extended tube"),
    ("glock17", ["reflex_sight", "pistol_suppressor", "laser_light", "extended_mag"], "Glock 17: reflex, suppressor, laser-light, extended mag"),
    ("svd", ["night_vision_4x", "flash_hider"], "SVD: night-vision scope, flash hider"),
]


def loadouts():
    W, Hh = 560, 300
    cols = 3
    sheet = Image.new("RGBA", (W * cols, Hh * ((len(LOADOUTS) + cols - 1) // cols)), (150, 160, 172, 255))
    for i, (k, ids, text) in enumerate(LOADOUTS):
        g = attach.loadout(k, ids)
        img = gunsheet.side(g.model, W)
        img = img.crop((0, (img.height - Hh) // 2, W, (img.height - Hh) // 2 + Hh))
        sheet.alpha_composite(img, ((i % cols) * W, (i // cols) * Hh))
        label(sheet, text, ((i % cols) * W + 8, (i // cols) * Hh + 6), (20, 20, 20, 255))
    sheet.save(OUT / "attachments.png")


def animations():
    rows = [("m4a1", "reload", [0.3, 0.7, 1.4, 2.0]), ("awm", "fire", [0.05, 0.55, 0.75, 0.95]),
            ("rem870", "reload", [0.6, 1.2, 2.6, 3.2]), ("carl_gustaf", "reload", [0.3, 1.0, 1.9, 3.6])]
    imgs = []
    for k, action, times in rows:
        frames = viewer.frames(k, action, times)
        row = Image.new("RGB", (frames[0].width * len(frames), frames[0].height))
        for i, f in enumerate(frames):
            row.paste(f, (i * f.width, 0))
            label(row, f"{NAMES[k]} {action} {times[i]:.2f}s", (i * f.width + 8, 6))
        imgs.append(row)
    sheet = Image.new("RGB", (imgs[0].width, sum(i.height for i in imgs)))
    for j, r in enumerate(imgs):
        sheet.paste(r, (0, j * r.height))
    sheet.save(OUT / "animations.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gunsheet.main(str(OUT / "gun_sides.png"), bare=True)
    held_views()
    loadouts()
    animations()
    print("docsheets: gun_sides, guns, attachments, animations")


if __name__ == "__main__":
    main()
