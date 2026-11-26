"""IWI Desert Eagle (.50 AE) and FN P90 (5.7x28mm)."""
from __future__ import annotations

from gunbase import *  # noqa: F401,F403
from gunbase import curved_mag, gun, mag_bones


def deagle():
    g = gun("deagle", "pistol", "pistol")
    g.box(-4, 30, 3, 9, -3, 3, STEEL)
    g.pistol_grip(-8, 2, 4, 18, 6, POLY, angle=18)
    g.part("slide", 12, 12)
    g.use("slide")
    g.bevel(-6, 32, 9, 16, -3.2, 3.2, STEEL, 1)
    g.muzzle = (32.0, 12.5)
    mag_bones(g, -2, -10)
    g.box(-9, 3, -15, -13, -3, 3, STEEL, tilt=-18, pivot=(-3, 4))
    g.mag_profile = dict(f0=-8, f1=2, top=-12, length=4, width=6, tilt=-18, pivot=(-3, 4), color=STEEL, kind="pistol")
    g.mount("optic", 6, 16, length=10, default=False, parent="slide")
    g.mount("muzzle", 32, 12.5, default=False, parent="slide", bore=2.2)
    g.mount("side", 24, 2, length=10, default=False)
    g.use("frame")
    return g


def p90():
    g = gun("p90", "rifle", "ar")
    g.bevel(-40, 30, 0, 18, -5, 5, POLY, 2)
    g.part("bolt", 0, 12)
    g.part("charging_handle", 10, 10, 5)
    g.box(8, 12, 9, 11, 5, 7, BLACK, bone="charging_handle")
    g.rod(30, 40, 12, 0, 2, STEEL)
    g.muzzle = (40.0, 12.0)
    mag_bones(g, -10, 18)
    g.box(-30, 20, 18, 22, -4, 4, "#3a3d36")
    g.mag_profile = None  # the magazine lies on top: no magazine attachments
    g.mount("optic", -4, 22, length=16, default=False)
    g.mount("muzzle", 40, 12, bore=2)
    g.mount("side", 10, 10, 5, length=10, default=False)
    g.use("frame")
    return g
