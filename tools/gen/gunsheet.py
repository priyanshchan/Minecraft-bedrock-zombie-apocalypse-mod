#!/usr/bin/env python3
"""Large left-side renders of every gun (muzzle to the right), for checking the models by eye.
Usage: python3 tools/gen/gunsheet.py [out.png] [--bare]   (--bare: without attachments)"""
import sys

from PIL import Image, ImageDraw

import held as H
import viewer


def side(model, size=420, yaw=-90.0):
    return viewer.icon_render(model, {"item": ((-90.0, 0, 0), (0, 0, 0), H.SCALE)}, yaw=yaw, pitch=0.0, size=size, margin=12)


def main(out, bare=False):
    W = 420
    cols = 3
    keys = H.GUNS
    sheet = Image.new("RGBA", (W * cols, W * 2 // 3 * ((len(keys) + cols - 1) // cols)), (150, 160, 172, 255))
    for i, k in enumerate(keys):
        g = H.G.GUNS[k]().finish() if bare else H.build_gun(k)
        img = side(g.model, W)
        y = (i // cols) * (W * 2 // 3) - W // 6
        sheet.alpha_composite(img, ((i % cols) * W, max(0, y)) if y >= 0 else ((i % cols) * W, 0))
        ImageDraw.Draw(sheet).text(((i % cols) * W + 8, (i // cols) * (W * 2 // 3) + 6), k, fill=(20, 20, 20, 255))
    sheet.save(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "docs/images/gun_sides.png", "--bare" in sys.argv)
