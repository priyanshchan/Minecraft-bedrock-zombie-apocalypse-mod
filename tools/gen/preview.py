#!/usr/bin/env python3
"""Renders every model (rest pose, soldiers in their aiming pose) into docs/images/models/*.png."""
from __future__ import annotations

import sys

from PIL import Image

from defs import ROOT, SOLDIERS
import models as M

AIM = {"rightArm": (-90.0, -8.0, 0.0), "leftArm": (-86.0, 38.0, 0.0)}


def sheet(images, cols, bg=(46, 50, 60)):
    w, h = images[0].size
    out = Image.new("RGBA", (w * cols, h * ((len(images) + cols - 1) // cols)), bg + (255,))
    for i, im in enumerate(images):
        out.paste(im, ((i % cols) * w, (i // cols) * h))
    return out


def posed(m):
    for b in m.bones:
        if b.name in AIM:
            b.rotation = AIM[b.name]
    img = m.preview(scale=7, size=(300, 340))
    for b in m.bones:
        if b.name in AIM:
            b.rotation = None
    return img


def main(which):
    out = ROOT / "docs" / "images" / "models"
    out.mkdir(parents=True, exist_ok=True)
    if not which or "soldiers" in which:
        imgs = [posed(M.soldier(key, skin)) for key, spec in SOLDIERS.items() for skin in spec["skins"]]
        sheet(imgs, 3).save(out / "soldiers.png")
    if not which or "vehicles" in which:
        imgs = [M.build_jeep(t).preview(scale=4, size=(420, 300)) for t in ("nato", "redfang")]
        imgs += [M.build_tank(t).preview(scale=3, size=(420, 300)) for t in ("nato", "redfang")]
        sheet(imgs, 2).save(out / "vehicles.png")
    if not which or "misc" in which:
        imgs = [M.capture_flag(o).preview(scale=3, size=(220, 240)) for o in M.FLAG_SKINS]
        imgs += [fn().preview(scale=9, size=(220, 240)) for fn in M.BLOCK_MODELS.values()]
        imgs += [m.preview(scale=14, size=(220, 240)) for m in M.projectile_models().values()]
        sheet(imgs, 4).save(out / "misc.png")
    print("preview: done")


if __name__ == "__main__":
    main(sys.argv[1:])
