#!/usr/bin/env python3
"""Large left-side renders of every weapon (muzzle to the right), for checking the models by eye.
Usage: python3 tools/gen/gunsheet.py [out.png]"""
import sys

from PIL import Image

import held as H
import models as M
import viewer


def side(model, size=420):
    return viewer.icon_render(model, {"item": ((-90.0, 0, 0), (0, 0, 0), H.SCALE)}, yaw=-90.0, pitch=0.0, size=size, margin=12)


def main(out):
    keys = H.GUNS + ["combat_knife", "frag_grenade", "smoke_grenade"]
    items = H.build_all()
    models = [items[k].model for k in keys] + [fn().finish().model for fn in H.FANG.values()]
    W = 420
    cols = 3
    sheet = Image.new("RGBA", (W * cols, W * ((len(models) + cols - 1) // cols)), (150, 160, 172, 255))
    for i, m in enumerate(models):
        sheet.alpha_composite(side(m, W), ((i % cols) * W, (i // cols) * W))
    sheet.save(out)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "docs/images/gun_sides.png")
