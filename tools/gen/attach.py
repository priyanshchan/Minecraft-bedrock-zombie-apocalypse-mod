"""The attachment catalogue: what each attachment is, which guns take it, how it changes the gun, and its model.

Every attachment is modelled onto every gun it fits, in a bone a_<id> under the gun's att_<slot> bone (under
`mag` for magazines), positioned from the gun's mount. The gun's render controller shows a_<id> while the
holder's cooldown category frontline_att_<id> is running (the scripts start it while that attachment is fitted
to the gun in hand) and hides the factory part (def_<slot>) it replaces.

Mods are multipliers of the gun's own values unless noted:
    spread  hip-fire spread      ads    spread while crouched (aiming)    vrec / hrec  vertical / horizontal recoil
    velocity  muzzle velocity (range and drop)   damage   reload  reload time   noise  loudness
    mag   magazine size ×      mag_add  extra rounds    zoom  magnification while aiming
    nv  night vision while aiming   laser   light   flash (hides the muzzle flash)   bipod  steadier when crouched
"""
from __future__ import annotations

import math

from kit import BLACK, BRASS, CHROME, DARK, GLASS, Held, OD, OD_D, POLY, RED, RUBBER, SILVER, STEEL, TAN, WHITE, mark, ribs, shade

GROUPS = {
    "pistol": ["glock17", "m1911"],
    "smg": ["mp5", "ump45"],
    "rifle": ["m4a1", "ak47"],
    "lmg": ["m249"],
    "shotgun": ["rem870"],
    "sniper": ["awm"],
    "dmr": ["svd"],
}


def fits(*groups):
    return [g for grp in groups for g in GROUPS[grp]]


# id: (name, slot, guns, mods)
CATALOGUE = {
    # ---- optics
    "reflex_sight": ("Mini Reflex Sight", "optic", fits("pistol", "smg", "rifle", "shotgun"), {"zoom": 1, "ads": 0.85}),
    "red_dot": ("Red Dot Sight", "optic", fits("smg", "rifle", "lmg", "shotgun", "dmr"), {"zoom": 1, "ads": 0.8}),
    "holo_sight": ("Holographic Sight", "optic", fits("smg", "rifle", "lmg", "shotgun"), {"zoom": 1, "ads": 0.78, "spread": 0.97}),
    "holo_magnifier": ("Holographic Sight + 3x Magnifier", "optic", fits("rifle", "lmg", "dmr"), {"zoom": 3, "ads": 0.68}),
    "prism_2x": ("2x Prism Sight", "optic", fits("smg", "rifle", "lmg", "shotgun", "dmr"), {"zoom": 2, "ads": 0.72}),
    "combat_4x": ("4x Combat Scope", "optic", fits("rifle", "lmg", "dmr", "sniper"), {"zoom": 4, "ads": 0.6}),
    "variable_6x": ("1-6x Variable Scope", "optic", fits("rifle", "lmg", "dmr", "sniper"), {"zoom": 6, "ads": 0.55}),
    "marksman_8x": ("8x Marksman Scope", "optic", fits("rifle", "dmr", "sniper"), {"zoom": 8, "ads": 0.45}),
    "sniper_12x": ("12x Sniper Scope", "optic", fits("dmr", "sniper"), {"zoom": 12, "ads": 0.35}),
    "night_vision_4x": ("4x Night Vision Scope", "optic", fits("rifle", "lmg", "dmr", "sniper"), {"zoom": 4, "ads": 0.62, "nv": 1}),
    # ---- muzzles
    "pistol_suppressor": ("Pistol Suppressor", "muzzle", fits("pistol", "smg"), {"noise": 0.25, "flash": 1, "velocity": 0.95, "vrec": 0.92}),
    "rifle_suppressor": ("Rifle Suppressor", "muzzle", fits("rifle", "lmg", "dmr", "sniper"), {"noise": 0.3, "flash": 1, "velocity": 1.03, "vrec": 0.9, "hrec": 0.9}),
    "compensator": ("Compensator", "muzzle", fits("pistol", "smg", "rifle", "lmg"), {"hrec": 0.7, "vrec": 0.9, "noise": 1.1}),
    "muzzle_brake": ("Muzzle Brake", "muzzle", fits("rifle", "lmg", "dmr", "sniper"), {"vrec": 0.7, "noise": 1.2}),
    "flash_hider": ("Flash Hider", "muzzle", fits("smg", "rifle", "lmg", "dmr"), {"flash": 1, "vrec": 0.95}),
    "full_choke": ("Full Choke", "muzzle", fits("shotgun"), {"spread": 0.6, "ads": 0.6}),
    "cylinder_choke": ("Cylinder Choke", "muzzle", fits("shotgun"), {"spread": 0.82, "velocity": 1.05}),
    # ---- underbarrel
    "vertical_grip": ("Vertical Grip", "underbarrel", fits("smg", "rifle", "lmg"), {"vrec": 0.7}),
    "angled_grip": ("Angled Grip", "underbarrel", fits("smg", "rifle", "lmg"), {"hrec": 0.65, "ads": 0.95}),
    "stubby_grip": ("Stubby Grip", "underbarrel", fits("smg", "rifle", "lmg"), {"vrec": 0.85, "hrec": 0.85, "spread": 0.9}),
    "handstop": ("Handstop", "underbarrel", fits("smg", "rifle", "lmg", "dmr"), {"vrec": 0.9, "hrec": 0.9}),
    "bipod": ("Bipod", "underbarrel", fits("rifle", "lmg", "dmr", "sniper"), {"bipod": 1}),
    # ---- side rail
    "laser_sight": ("Laser Sight", "side", fits("pistol", "smg", "rifle", "shotgun", "lmg", "dmr", "sniper"), {"spread": 0.65, "laser": 1}),
    "flashlight": ("Tactical Flashlight", "side", fits("pistol", "smg", "rifle", "shotgun", "lmg", "dmr", "sniper"), {"light": 1}),
    "laser_light": ("Laser-Light Module", "side", fits("pistol", "smg", "rifle", "shotgun", "lmg", "dmr", "sniper"), {"spread": 0.8, "laser": 1, "light": 1}),
    # ---- stocks
    "heavy_stock": ("Heavy Stock", "stock", fits("smg", "rifle", "lmg", "shotgun"), {"vrec": 0.8, "ads": 0.9, "spread": 1.1}),
    "light_stock": ("Lightweight Stock", "stock", fits("smg", "rifle"), {"spread": 0.85, "vrec": 1.1}),
    "precision_stock": ("Precision Stock", "stock", fits("rifle", "dmr", "sniper"), {"ads": 0.8, "hrec": 0.8}),
    # ---- magazines
    "extended_mag": ("Extended Magazine", "magazine", fits("pistol", "smg", "rifle", "dmr", "sniper"), {"mag": 1.5, "reload": 1.1}),
    "drum_mag": ("Drum Magazine", "magazine", fits("smg", "rifle"), {"mag": 2.0, "reload": 1.4, "ads": 1.1}),
    "quick_mag": ("Quick-Pull Magazine", "magazine", fits("pistol", "smg", "rifle", "dmr", "sniper"), {"reload": 0.7}),
    "extended_tube": ("Extended Tube", "magazine", fits("shotgun"), {"mag_add": 3, "reload": 1.1}),
    "big_box": ("300-Round Box", "magazine", fits("lmg"), {"mag": 1.5, "reload": 1.25}),
}

SLOT_ORDER = ["optic", "muzzle", "underbarrel", "side", "stock", "magazine"]


def category(att_id):
    """The cooldown category that shows an attachment on the gun in hand."""
    return f"frontline_att_{att_id}"


# =========================================================================== models
# Each builder gets the gun (to add boxes), the mount (f, u, s, bore, length) and the bone to fill. Positions are
# relative to the mount: (df, du, ds).

class At:
    def __init__(self, g, m, bone):
        self.g, self.m, self.bone = g, m, bone

    def box(self, df0, df1, du0, du1, ds0, ds1, color, noise=3, **kw):
        m = self.m
        if kw.get("pivot") is not None:  # pivots are given relative to the mount too
            pv = kw["pivot"]
            kw["pivot"] = (m["f"] + pv[0], m["u"] + pv[1]) + ((m["s"] + pv[2],) if len(pv) > 2 else (m["s"],))
        return self.g.box(m["f"] + df0, m["f"] + df1, m["u"] + du0, m["u"] + du1, m["s"] + ds0, m["s"] + ds1, color,
                          noise, bone=self.bone, **kw)

    def rod(self, df0, df1, du, ds, r, color, noise=2):
        m = self.m
        return self.g.rod(m["f"] + df0, m["f"] + df1, m["u"] + du, m["s"] + ds, r, color, noise, bone=self.bone)

    def bevel(self, df0, df1, du0, du1, ds0, ds1, color, b=1.0, noise=3):
        m = self.m
        return self.g.bevel(m["f"] + df0, m["f"] + df1, m["u"] + du0, m["u"] + du1, m["s"] + ds0, m["s"] + ds1,
                            color, b, noise, bone=self.bone)

    def lens(self, df, du0, du1, ds0, ds1, color=GLASS):
        m = self.m
        return self.g.lens(m["f"] + df, m["u"] + du0, m["u"] + du1, m["s"] + ds0, m["s"] + ds1, color, bone=self.bone)

    def drum(self, df, du, ds0, ds1, r, color):
        """A disc with its axis across the gun (along s): rows of boxes forming a circle in the f-u plane."""
        out = []
        n = int(math.ceil(r))
        for y in range(-n, n):
            yc = y + 0.5
            if abs(yc) >= r:
                continue
            hw = round(math.sqrt(r * r - yc * yc))
            if hw > 0:
                out.append(self.box(df - hw, df + hw, du + y, du + y + 1, ds0, ds1, color))
        return out


def clamp(a, length=8, width=6, color=BLACK):
    """A rail clamp for anything that sits on a picatinny rail."""
    w = width / 2
    a.box(-length / 2, length / 2, 0, 2, -w, w, color)
    a.box(-length / 2, length / 2, 0, 1, -w - 1, -w, shade(color, 0.8))
    a.box(-1, 1, 0.5, 1.5, w, w + 1.5, SILVER, 1)  # throw lever


def scope(a, tube_r, f_back, f_front, bell_r, bell_len, eye_r, eye_len, height, color=POLY, turrets=True):
    """A tube scope on two rings: tube, objective bell, eyepiece, turrets and lenses."""
    cu = height + tube_r
    for df in (f_back + 4, f_front - 6):
        a.box(df, df + 3, 0, cu - tube_r + 1, -tube_r, tube_r, BLACK)
    a.rod(f_back, f_front, cu, 0, tube_r, color)
    a.rod(f_front, f_front + 2, cu, 0, (tube_r + bell_r) / 2, color)
    a.rod(f_front + 2, f_front + 2 + bell_len, cu, 0, bell_r, color)
    a.rod(f_back - eye_len, f_back, cu, 0, eye_r, color)
    a.rod(f_back - eye_len - 2, f_back - eye_len, cu, 0, eye_r - 0.5, RUBBER)
    a.lens(f_front + 2 + bell_len, cu - bell_r + 1, cu + bell_r - 1, -bell_r + 1, bell_r - 1)
    a.lens(f_back - eye_len - 3, cu - eye_r + 1, cu + eye_r - 1, -eye_r + 1, eye_r - 1, "#7fd0f5")
    if turrets:
        mid = (f_back + f_front) / 2
        a.box(mid - 2, mid + 2, cu + tube_r, cu + tube_r + 3, -2, 2, color)
        a.box(mid - 1.5, mid + 1.5, cu + tube_r + 3, cu + tube_r + 4, -1.5, 1.5, SILVER, 1)
        a.box(mid - 2, mid + 2, cu - 2, cu + 2, -tube_r - 3, -tube_r, color)


def b_reflex_sight(a):
    a.box(-3, 3, 0, 1, -2, 2, BLACK)
    a.box(-3, 3, 1, 5, -2, -1.5, BLACK)
    a.box(-3, 3, 1, 5, 1.5, 2, BLACK)
    a.box(-2, 3, 5, 6, -2, 2, BLACK)
    a.lens(1, 1, 5, -1.5, 1.5, "#7fc7d9")
    a.box(-2, -1, 1, 2, -0.5, 0.5, RED, 0)


def b_red_dot(a):
    clamp(a, 8, 6)
    a.box(-3, 3, 2, 5, -2, 2, BLACK)  # riser
    a.rod(-4, 5, 8, 0, 3, BLACK)
    a.rod(5, 6, 8, 0, 3.4, BLACK)
    a.box(-1, 2, 11, 13, -1, 1, BLACK)  # turret
    a.box(-1, 2, 7, 9, 3, 5, BLACK)
    a.lens(6, 6, 10, -2, 2, "#3fae6a")
    a.lens(-5, 6, 10, -2, 2, "#7fd0f5")
    a.box(0, 1, 7.5, 8.5, -0.5, 0.5, RED, 0)


def b_holo_sight(a):
    clamp(a, 10, 6)
    a.bevel(-6, 6, 2, 5, -3, 3, BLACK, 1)
    a.box(-6, 6, 5, 10, -3, -2, BLACK)
    a.box(-6, 6, 5, 10, 2, 3, BLACK)
    a.box(-6, 6, 10, 11, -3, 3, BLACK)
    a.lens(4, 5, 10, -2, 2, "#69b7a8")
    a.lens(-5, 5, 10, -2, 2, "#7fd0f5")
    a.box(-4, 0, 3.5, 4.5, 3, 3.5, DARK, 0)  # buttons
    a.box(0, 1, 7, 8, -0.5, 0.5, RED, 0)


def b_holo_magnifier(a):
    b_holo_sight(a)
    a.box(-18, -10, 0, 2, -3, 3, BLACK)
    a.box(-16, -13, 2, 5, -2, 2, BLACK)
    a.rod(-20, -10, 8, 0, 2.6, BLACK)
    a.lens(-10, 6, 10, -2, 2)
    a.lens(-21, 6, 10, -2, 2, "#7fd0f5")


def b_prism_2x(a):
    clamp(a, 10, 6)
    a.bevel(-5, 5, 2, 10, -3, 3, BLACK, 1)
    a.rod(5, 8, 7, 0, 3, BLACK)
    a.rod(-9, -5, 7, 0, 2.5, RUBBER)
    a.lens(8, 5, 9, -2, 2)
    a.lens(-10, 5, 9, -2, 2, "#7fd0f5")
    a.box(-1, 2, 10, 12, -1.5, 1.5, BLACK)


def b_combat_4x(a):
    clamp(a, 12, 6)
    a.box(-4, 4, 2, 4, -2.5, 2.5, BLACK)
    a.rod(-7, 8, 8, 0, 3.2, TAN)
    a.rod(8, 11, 8, 0, 3.6, TAN)
    a.rod(-10, -7, 8, 0, 3.0, TAN)
    a.box(-3, 6, 11, 12, -1, 1, TAN)  # fibre-optic housing
    a.box(-2, 5, 12, 12.5, -0.5, 0.5, RED, 0)
    a.lens(11, 5, 11, -3, 3)
    a.lens(-11, 6, 10, -2, 2, "#7fd0f5")


def b_variable_6x(a):
    scope(a, 2.5, -9, 10, 3.5, 6, 3.2, 6, 5)


def b_marksman_8x(a):
    scope(a, 2.8, -11, 12, 4.5, 8, 3.5, 7, 6)
    a.rod(22, 28, 6 + 2.8, 0, 4.6, POLY)  # sunshade


def b_sniper_12x(a):
    scope(a, 3.0, -13, 16, 5.5, 10, 4, 9, 7)
    a.box(0, 4, 10, 14, 3, 6, POLY)  # parallax knob


def b_night_vision_4x(a):
    clamp(a, 14, 6)
    a.bevel(-8, 10, 2, 11, -3.5, 3.5, OD_D, 1)
    a.rod(10, 14, 6.5, 0, 3.5, OD_D)
    a.lens(14, 4, 9, -2.5, 2.5, "#4fdc6a")
    a.rod(-14, -8, 6.5, 0, 3, RUBBER)
    a.rod(-4, 6, 8, 5, 1.5, BLACK)  # IR illuminator
    a.lens(6, 7, 9, 4, 6, "#a01818")
    a.box(-2, 2, 11, 13, -1.5, 1.5, BLACK)


def muzzle_r(a, extra):
    return a.m.get("bore", 2.0) + extra


def b_pistol_suppressor(a):
    r = muzzle_r(a, 1.2)
    for c in a.rod(0, 18, 0, 0, r, BLACK):
        ribs(c, ("right", "left"), 4, shade(BLACK, 1.4))
    a.rod(18, 19, 0, 0, r - 0.5, DARK)


def b_rifle_suppressor(a):
    r = muzzle_r(a, 1.6)
    a.rod(0, 4, 0, 0, r - 0.6, BLACK)
    for c in a.rod(4, 26, 0, 0, r, "#3d4139"):
        ribs(c, ("right", "left"), 5, shade("#3d4139", 1.3))
    a.rod(26, 27, 0, 0, r - 0.8, DARK)


def b_compensator(a):
    r = muzzle_r(a, 0.7)
    for c in a.rod(0, 7, 0, 0, r, BLACK):
        mark(c, "up", 2, 3, c.ext[2], c.ext[3], DARK)
        mark(c, "up", 4, 5, c.ext[2], c.ext[3], DARK)
    a.rod(7, 8, 0, 0, r - 0.5, DARK)


def b_muzzle_brake(a):
    r = muzzle_r(a, 1.4)
    b = a.bevel(0, 9, -r, r, -r - 0.5, r + 0.5, BLACK, 1)
    for c in b[:2]:
        for side in ("right", "left"):
            for f in (2, 5):
                mark(c, side, a.m["f"] + f, a.m["f"] + f + 2, a.m["u"] - 1.5, a.m["u"] + 1.5, "#060607")


def b_flash_hider(a):
    r = muzzle_r(a, 0.6)
    for c in a.rod(0, 7, 0, 0, r, BLACK):
        for side in ("right", "left", "up", "down"):
            mark(c, side, a.m["f"] + 3, a.m["f"] + 7, c.ext[2], c.ext[3], DARK) if c.ext[3] - c.ext[2] <= 1 else None
    for ds in (-1, 1):
        a.box(3, 7, -0.5, 0.5, ds - 0.5, ds + 0.5, DARK, 0)


def b_full_choke(a):
    r = muzzle_r(a, 0.6)
    for c in a.rod(0, 5, 0, 0, r, SILVER):
        ribs(c, ("right", "left"), 2, shade(SILVER, 0.7))


def b_cylinder_choke(a):
    a.rod(0, 3, 0, 0, muzzle_r(a, 0.4), "#c9a43a")


def b_vertical_grip(a):
    clamp(a, 8, 6)
    a.box(-2.5, 2.5, -2, 0, -2, 2, BLACK)
    g = a.bevel(-2, 2, -16, -2, -2, 2, POLY, 0.5)
    for c in g[:2]:
        ribs(c, ("right", "left"), 2, shade(POLY, 1.4))
    a.box(-2.5, 2.5, -17, -16, -2.5, 2.5, POLY)


def b_angled_grip(a):
    clamp(a, 14, 6)
    a.box(-6, 6, -3, 0, -2, 2, POLY)
    a.box(-6, 4, -8, -3, -2, 2, POLY, tilt=-32, pivot=(6, -3))


def b_stubby_grip(a):
    clamp(a, 8, 6)
    g = a.bevel(-2, 2, -8, 0, -2, 2, POLY, 0.5)
    for c in g[:2]:
        ribs(c, ("right", "left"), 2, shade(POLY, 1.4))


def b_handstop(a):
    clamp(a, 6, 6)
    a.box(1, 3, -5, 0, -2, 2, POLY, tilt=20, pivot=(2, 0))


def b_bipod(a):
    clamp(a, 8, 6)
    a.box(-3, 3, -4, 0, -3, 3, BLACK)
    for ds in (-2.5, 2.5):
        a.rod(-2, 20, -3, ds, 1, SILVER)
        a.box(18, 21, -4.5, -1.5, ds - 1, ds + 1, RUBBER, 1)


def side_dir(a):
    return 1 if a.m["s"] >= 0 else -1


def b_laser_sight(a):
    d = side_dir(a)
    lo, hi = sorted((0, 4 * d))
    a.box(-4, 4, -2.5, 2.5, lo, hi, BLACK)
    a.box(4, 5, -1, 1, lo + 0.5, hi - 0.5, "#e02020", 0)
    a.box(-2, 1, 2.5, 3.5, lo + 1, hi - 1, RED, 0)


def b_flashlight(a):
    d = side_dir(a)
    cs = 3 * d
    a.box(-2, 2, -1.5, 1.5, *sorted((0, 1.5 * d)), BLACK)
    a.rod(-7, 5, 0, cs, 2.2, BLACK)
    a.rod(5, 8, 0, cs, 2.8, BLACK)
    a.lens(8, -2, 2, cs - 2, cs + 2, "#f6f1d8")


def b_laser_light(a):
    d = side_dir(a)
    lo, hi = sorted((0, 5 * d))
    a.bevel(-5, 5, -3, 3, lo, hi, TAN, 1)
    a.lens(5, -2, 2, lo + 0.5, hi - 0.5, "#f6f1d8")
    a.box(5, 6, 2, 3, lo + 1.5, hi - 1.5, "#e02020", 0)


def b_heavy_stock(a):
    st = a.bevel(-22, -2, -8, 6, -4, 4, POLY, 1.5)
    a.box(-20, -6, 6, 8, -3, 3, POLY)
    a.bevel(-24, -22, -9, 7, -4.5, 4.5, RUBBER, 1)
    for c in st[:2]:
        ribs(c, ("right", "left"), 3, shade(POLY, 0.7))


def b_light_stock(a):
    a.rod(-20, -2, 2, 0, 1.2, SILVER)
    a.rod(-20, -4, -5, 0, 1, SILVER)
    a.box(-22, -20, -8, 5, -3.5, 3.5, RUBBER)


def b_precision_stock(a):
    a.bevel(-26, -2, -8, 5, -4, 4, TAN, 1.5)
    a.box(-22, -8, 5, 9, -3, 3, TAN)  # adjustable cheek riser
    a.box(-20, -18, 5, 9, -1, 1, SILVER, 1)
    for i in range(3):
        a.box(-28 - i, -27 - i, -9, 6, -4.5, 4.5, BLACK if i % 2 else RUBBER)  # spacers and pad
    a.box(-18, -14, -12, -8, -1.5, 1.5, BLACK)  # monopod


def mag_shape(a, profile, scale_len=1.0, color=None, extra=None):
    """A magazine following the gun's own magazine profile, longer by `scale_len`."""
    p = profile
    col = color or p["color"]
    kind = p["kind"]
    g = a.g
    if kind == "pistol":
        length = 4 + 10 * (scale_len - 1)
        g.box(p["f0"], p["f1"], p["top"] - length, p["top"], -p["width"] / 2, p["width"] / 2, col, bone=a.bone,
              tilt=p["tilt"], pivot=p["pivot"])
        g.box(p["f0"] - 1, p["f1"] + 1, p["top"] - length - 2, p["top"] - length, -p["width"] / 2 - 0.5,
              p["width"] / 2 + 0.5, shade(col, 0.75), bone=a.bone, tilt=p["tilt"], pivot=p["pivot"])
        return
    if kind == "tube":
        a.rod(0, 10 * scale_len, 0, 0, 2.6, col)
        a.rod(10 * scale_len, 10 * scale_len + 4, 0, 0, 3, col)
        return
    if kind == "box":
        h = 22 * scale_len
        a.bevel(p["f0"] - a.m["f"], p["f0"] - a.m["f"] + 26, -h, 0, -9, 5, col, 1.5)
        return
    segs = list(p["segs"])
    if scale_len != 1.0:  # a longer magazine: every segment taller, the curve a little stronger
        segs = [(df * (1 + (scale_len - 1) * 0.6), h * scale_len) for df, h in segs]
    s = p["width"] / 2
    u = p["top"]
    prev_df = segs[0][0]
    for i, (df, h) in enumerate(segs):
        # tilt each segment to the curve: the forward step between this segment and the next over its height
        nxt = segs[i + 1][0] if i + 1 < len(segs) else df + (df - prev_df)
        ang = math.degrees(math.atan2(nxt - df, h)) if nxt != df else 0.0
        c = g.box(p["f0"] + df, p["f0"] + df + 10, u - h - 0.5, u + 0.5, -s, s, col, bone=a.bone,
                  tilt=ang * 0.8, pivot=(p["f0"] + df + 5, u))
        ribs(c, ("right", "left"), 2, shade(col, 0.8))
        prev_df = df
        u -= h
    df = segs[-1][0] + (segs[-1][0] - (segs[-2][0] if len(segs) > 1 else segs[-1][0])) * 0.5
    g.box(p["f0"] + df - 1, p["f0"] + df + 11, u - 2, u, -s - 1, s + 1, shade(col, 0.75), bone=a.bone)
    if extra:
        extra(p["f0"] + df, u)


def b_extended_mag(a, profile):
    mag_shape(a, profile, 1.5)


def b_quick_mag(a, profile):
    def tab(f, u):
        a.g.box(f + 2, f + 8, u - 4, u - 2, -1, 1, "#e07b2a", bone=a.bone)
    if profile["kind"] == "pistol":
        mag_shape(a, profile, 1.0, color="#3a3d44")
        return
    mag_shape(a, profile, 1.0, color="#3a3d44", extra=tab)


def b_drum_mag(a, profile):
    p = profile
    s = p["width"] / 2
    a.g.box(p["f0"], p["f0"] + 10, p["top"] - 6, p["top"], -s, s, shade(p["color"], 0.9), bone=a.bone)
    fc = p["f0"] + 5 - a.m["f"]
    uc = p["top"] - 16 - a.m["u"]
    a.drum(fc, uc, -s - 3, s + 3, 11, "#2b2d31")
    a.drum(fc, uc, s + 3, s + 4, 6, "#3a3d44")
    a.drum(fc, uc, -s - 4, -s - 3, 6, "#3a3d44")


def b_extended_tube(a, profile):
    mag_shape(a, profile, 1.0)


def b_big_box(a, profile):
    mag_shape(a, profile, 1.5, color=OD_D)


BUILDERS = {k[0] if False else k: globals()[f"b_{k}"] for k in CATALOGUE}
MAGAZINE = {k for k, v in CATALOGUE.items() if v[1] == "magazine"}


def compatible(gun_key, mounts):
    """Attachments that fit a gun: listed for it and its model has the slot."""
    out = []
    for att_id, (_name, slot, guns, _mods) in CATALOGUE.items():
        if gun_key not in guns:
            continue
        if slot == "magazine" or slot in mounts:
            out.append(att_id)
    return out


def fit_all(g):
    """Adds every attachment that fits gun g to its model, each in a bone of its own."""
    g.attachments = []
    for att_id in compatible(g.key, g.mounts):
        slot = CATALOGUE[att_id][1]
        if slot == "magazine":
            p = g.mag_profile
            if p is None:
                continue
            m = {"f": p.get("f0", 0), "u": p.get("top", 0), "s": 0.0, "bore": 2.0, "length": 0}
            bone = g.part(f"a_{att_id}", m["f"], m["u"], parent="mag")
            BUILDERS[att_id](At(g, m, bone.name), p)
        else:
            m = g.mounts[slot]
            bone = g.part(f"a_{att_id}", m["f"], m["u"], m["s"], parent=f"att_{slot}")
            BUILDERS[att_id](At(g, m, bone.name))
        g.attachments.append(att_id)
    return g


def standalone(att_id):
    """An attachment on its own (for its inventory icon), on a stand-in rifle mount."""
    g = Held(f"att_{att_id}", "rifle")  # drawn side-on, like the guns
    slot = CATALOGUE[att_id][1]
    m = {"f": 0.0, "u": 0.0, "s": 0.0, "bore": 2.0, "length": 30}
    if slot == "side":
        m["s"] = 0.5
    bone = g.part(f"a_{att_id}", 0, 0)
    if slot == "magazine":
        import guns as G
        donor = {"extended_tube": "rem870", "big_box": "m249"}.get(att_id, "m4a1")
        p = dict(G.GUNS[donor]().mag_profile)
        m["f"], m["u"] = p.get("f0", 0), p.get("top", 0)
        BUILDERS[att_id](At(g, m, bone.name), p)
    else:
        BUILDERS[att_id](At(g, m, bone.name))
    return g.finish()


def loadout(gun_key, att_ids):
    """A gun model with only the given attachments on it and the factory parts they replace taken off, as the
    game shows it (for preview images)."""
    import guns as G
    g = G.GUNS[gun_key]()
    g.attachments = []
    for att_id in att_ids:
        slot = CATALOGUE[att_id][1]
        if slot == "magazine":
            p = g.mag_profile
            m = {"f": p.get("f0", 0), "u": p.get("top", 0), "s": 0.0, "bore": 2.0, "length": 0}
            bone = g.part(f"a_{att_id}", m["f"], m["u"], parent="mag")
            BUILDERS[att_id](At(g, m, bone.name), p)
            hide = "def_mag"
        else:
            m = g.mounts[slot]
            bone = g.part(f"a_{att_id}", m["f"], m["u"], m["s"], parent=f"att_{slot}")
            BUILDERS[att_id](At(g, m, bone.name))
            hide = f"def_{slot}"
        if hide in g.bones:
            g.bones[hide].cubes.clear()
        g.attachments.append(att_id)
    return g.finish()
