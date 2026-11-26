"""FN SCAR-H (7.62x51mm NATO) and PKM (7.62x54mmR)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import curved_mag, gun, mag_bones


def scar_h():
    g = gun("scar_h", "rifle", "ar")
    g.bevel(-8, 50, 8, 19, -4.5, 4.5, TAN, 1)
    g.box(-6, 20, 2, 9, -4, 4, TAN)
    g.pistol_grip(-6, 2, 3, 15, 6, POLY, angle=18)
    g.teeth_rail(-8, 50, 19, -3, 3)
    g.part("bolt", 9, 13)
    g.part("charging_handle", 20, 15, 5)
    g.box(18, 22, 14, 16, 4.5, 7, BLACK, bone="charging_handle")
    g.rod(50, 76, 13.5, 0, 2.2, STEEL)
    g.muzzle = (82.0, 13.5)
    mag_bones(g, 13, 2)
    curved_mag(g, 8, 7, 2, [(0, 8), (0, 6), (1, 6)], BLACK)
    g.mag_profile = dict(f0=8, top=2, width=7, segs=[(0, 8), (0, 6), (1, 6)], color=BLACK, kind="rifle")
    g.mount("optic", 8, 22, length=36)
    g.mount("muzzle", 76, 13.5, bore=2.2)
    g.mount("underbarrel", 38, 8, length=14, default=False)
    g.mount("side", 40, 13.5, 4.5, length=10, default=False)
    g.mount("stock", -8, 13)
    g.use("def_stock")
    g.bevel(-44, -8, 4, 18, -4, 4, TAN, 1)
    g.use("frame")
    return g


def pkm():
    g = gun("pkm", "rifle", "lmg")
    g.bevel(-12, 34, 4, 20, -5, 5, BLUED, 1.5)
    g.pistol_grip(-12, -4, 5, 16, 6, WOOD, angle=14)
    g.part("charging_handle", 20, 12, -6)
    g.box(16, 24, 11, 14, -8, -5, BLUED, bone="charging_handle")
    g.part("cover", -12, 21)
    g.use("cover")
    g.bevel(-12, 24, 20, 24, -4.5, 4.5, BLUED, 1)
    g.use("frame")
    g.rod(34, 104, 14, 0, 2.4, BLUED)
    g.muzzle = (112.0, 14.0)
    mag_bones(g, 14, 4)
    g.bevel(2, 26, -18, 4, -9, 5, "#4a5530", 1.5)
    g.mag_profile = dict(f0=2, top=4, width=14, segs=[(0, 22)], color="#4a5530", kind="box")
    g.mount("optic", 6, 25, -5, length=20, default=False)
    g.mount("muzzle", 104, 14, bore=2.4)
    g.mount("underbarrel", 80, 8)
    g.mount("side", 44, 14, 5, length=10, default=False)
    g.mount("stock", -12, 13)
    g.use("def_stock")
    g.bevel(-54, -12, 4, 18, -4, 4, WOOD, 1.5)
    g.use("frame")
    return g
