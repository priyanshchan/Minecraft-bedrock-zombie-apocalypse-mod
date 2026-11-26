"""Barrett M82A1 (.50 BMG)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import curved_mag, gun, mag_bones


def barrett():
    g = gun("barrett", "rifle", "ar")
    g.bevel(-30, 40, 4, 20, -5, 5, PARK, 1.5)
    g.pistol_grip(-12, -4, 4, 16, 6, POLY, angle=12)
    g.teeth_rail(-20, 40, 20, -3, 3)
    g.part("charging_handle", 10, 14, -5)
    g.box(8, 14, 13, 16, -9, -5, BLACK, bone="charging_handle")
    g.rod(40, 120, 13, 0, 3, BLACK)
    g.muzzle = (134.0, 13.0)
    mag_bones(g, 6, 4)
    g.box(0, 14, -8, 4, -4, 4, BLACK)
    g.mag_profile = dict(f0=0, top=4, width=8, segs=[(0, 12)], color=BLACK, kind="sniper")
    g.mount("optic", 4, 23, length=40)
    g.mount("muzzle", 120, 13, bore=3)
    g.use("def_muzzle")
    g.bevel(120, 134, 8, 18, -5, 5, BLACK, 1)
    g.mount("underbarrel", 60, 6)
    g.mount("side", 30, 12, 5, length=10, default=False)
    g.mount("stock", -30, 12)
    g.use("def_stock")
    g.bevel(-62, -30, 2, 18, -4.5, 4.5, PARK, 1.5)
    g.use("frame")
    return g
