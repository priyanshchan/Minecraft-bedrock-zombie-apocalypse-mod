"""The guns' own animations: firing (recoil, bolt or slide), reloading, clearing a jam and clearing a
malfunction, for every gun, in both first and third person.

How they are triggered: an attachable cannot see script state, but it can read the cooldown of the item
in the hand. Every gun item has a cooldown category of its own, and the script starts a cooldown of a
length that says which action is under way (TIMING, in ticks; each length is unique per gun). The
attachable plays the animation whose length matches `q.cooldown_time`, at the time the cooldown has run
(`anim_time_update`), so the animation follows the script's timing exactly.

Positions are in the gun's units (quarter pixels) in model space: forward is +Y, up is -Z.
Rotations: x tilts the muzzle (negative = muzzle up), y rolls the gun about the barrel, z yaws it.
"""
from __future__ import annotations

# Ticks of each action, per gun (the scripts read them from gundata.js). The four lengths of a gun differ by at
# least a tick, so the model can tell them apart.
TIMING = {
    "glock17": {"fire": 3, "reload": 30, "jam": 22, "malfunction": 48},
    "m1911": {"fire": 4, "reload": 34, "jam": 24, "malfunction": 52},
    "mp5": {"fire": 2, "reload": 42, "jam": 26, "malfunction": 60},
    "ump45": {"fire": 3, "reload": 40, "jam": 27, "malfunction": 61},
    "m4a1": {"fire": 3, "reload": 46, "jam": 28, "malfunction": 64},
    "ak47": {"fire": 4, "reload": 50, "jam": 29, "malfunction": 66},
    "m249": {"fire": 2, "reload": 100, "jam": 30, "malfunction": 72},
    "rem870": {"fire": 16, "reload": 72, "jam": 32, "malfunction": 58},
    "awm": {"fire": 30, "reload": 70, "jam": 34, "malfunction": 76},
    "svd": {"fire": 5, "reload": 54, "jam": 31, "malfunction": 68},
    "carl_gustaf": {"fire": 8, "reload": 80, "jam": 36, "malfunction": 84},
    "rpg7": {"fire": 8, "reload": 70, "jam": 37, "malfunction": 81},
}

SLOT = "'slot.weapon.mainhand', 0"
ELAPSED = f"q.cooldown_time({SLOT}) - q.cooldown_time_remaining({SLOT})"


def active(seconds):
    """Molang: true while a cooldown of exactly this length is running on the held item."""
    return f"q.cooldown_time_remaining({SLOT}) > 0.0 && math.abs(q.cooldown_time({SLOT}) - {seconds:.2f}) < 0.026"


class Anim:
    """Keyframes per bone and channel; values are lerped linearly between keys."""

    def __init__(self, length, bones=None):
        self.length = length
        self.bones = bones  # the model's bones: tracks for any other bone are left out
        self.tracks: dict[str, dict[str, dict[float, list[float]]]] = {}

    def key(self, bone, channel, t, value):
        t = round(min(max(t, 0.0), self.length), 3)
        self.tracks.setdefault(bone, {}).setdefault(channel, {})[t] = [round(float(v), 3) for v in value]
        return self

    def move(self, bone, channel, t0, t1, a, b):
        """From value a at t0 to value b at t1."""
        self.key(bone, channel, t0, a).key(bone, channel, t1, b)
        return self

    def rest(self, bone, channel, *times):
        zero = [1, 1, 1] if channel == "scale" else [0, 0, 0]
        for t in times:
            self.key(bone, channel, t, zero)
        return self

    def json(self):
        bones = {}
        for bone, channels in self.tracks.items():
            if self.bones is not None and bone not in self.bones:
                continue
            bones[bone] = {}
            for channel, keys in channels.items():
                zero = [1, 1, 1] if channel == "scale" else [0, 0, 0]
                if 0.0 not in keys:
                    keys[0.0] = zero
                if self.length not in keys:
                    keys[self.length] = zero
                bones[bone][channel] = {f"{t:.3f}".rstrip("0").rstrip(".") if t else "0.0": v for t, v in sorted(keys.items())}
        return {"loop": False, "animation_length": self.length, "anim_time_update": ELAPSED, "bones": bones}


# ------------------------------------------------------------------ building blocks

def tilt(a, t_in, t_out, rot, pos=(0, 0, 0), settle=0.2):
    """Cant the gun towards the eye for the length of a manipulation, then bring it back."""
    a.rest("gun", "rotation", 0.0)
    a.key("gun", "rotation", t_in, rot)
    a.key("gun", "rotation", t_out, rot)
    a.rest("gun", "rotation", min(a.length, t_out + settle))
    if any(pos):
        a.rest("gun", "position", 0.0)
        a.key("gun", "position", t_in, pos)
        a.key("gun", "position", t_out, pos)
        a.rest("gun", "position", min(a.length, t_out + settle))


def rack(a, bone, t, dist, back=0.1, hold=0.05, forward=0.08):
    """Pull a part back by `dist` units and let it go."""
    a.rest(bone, "position", t)
    a.key(bone, "position", t + back, (0, -dist, 0))
    a.key(bone, "position", t + back + hold, (0, -dist, 0))
    a.rest(bone, "position", t + back + hold + forward)


def mag_swap(a, t_out, t_in, depth, drop_tilt=(0, 0, 0)):
    """Old magazine out and away (it vanishes as it falls), a new one up from below and seated with a slap."""
    a.rest("mag", "position", 0.0, t_out)
    a.key("mag", "position", t_out + 0.2, (0, -2, depth))
    a.key("mag", "position", t_out + 0.3, (0, -4, depth * 1.8))
    a.rest("mag", "scale", 0.0, t_out + 0.27)
    a.key("mag", "scale", t_out + 0.3, (0, 0, 0))
    a.key("mag", "scale", t_in - 0.4, (0, 0, 0))
    a.rest("mag", "scale", t_in - 0.37)
    a.key("mag", "position", t_in - 0.37, (0, -2, depth * 1.2))
    a.key("mag", "position", t_in, (0, 0, 2))
    a.key("mag", "position", t_in + 0.05, (0, 0, -1.5))
    a.rest("mag", "position", t_in + 0.1)
    if any(drop_tilt):
        a.rest("mag", "rotation", t_out)
        a.key("mag", "rotation", t_out + 0.3, drop_tilt)
        a.key("mag", "rotation", t_in - 0.37, drop_tilt)
        a.rest("mag", "rotation", t_in)


def recoil(a, kick, push, bone=None, travel=0.0):
    a.rest("gun", "rotation", 0.0)
    a.key("gun", "rotation", 0.03, (-kick, 0, 0))
    a.rest("gun", "rotation", min(a.length, 0.03 + max(0.1, a.length * 0.6)))
    a.rest("gun", "position", 0.0)
    a.key("gun", "position", 0.03, (0, -push, 0))
    a.rest("gun", "position", min(a.length, 0.03 + max(0.1, a.length * 0.6)))
    if bone:
        a.rest(bone, "position", 0.0)
        a.key(bone, "position", 0.04, (0, -travel, 0))
        a.rest(bone, "position", min(a.length, 0.13))


# ------------------------------------------------------------------ per gun

def seconds(gun, action):
    return TIMING[gun][action] / 20


def build(gun, family=None, bones=None):
    """{action: Anim} for one gun. `family` is how the gun works (the model's `anim`: pistol, ar, lmg, pump,
    bolt, launcher_rear, launcher_front); `bones` the model's bones (tracks for missing parts are left out)."""
    if family is None or bones is None:
        import guns as G
        g = G.GUNS[gun]()
        family, bones = g.anim, set(g.bones)
    t = {k: seconds(gun, k) for k in TIMING[gun]}
    out = {}
    cant, lift = (-20, -50, -10), (0, 0, -12)  # rolled over and lifted: the magwell faces the eye

    def mk(length):  # every animation of this gun knows its bones
        return Anim(length, bones)

    lmg = family == "lmg"
    if family in ("ar", "lmg"):
        handle = "charging_handle"
        fire = mk(t["fire"])
        recoil(fire, {"m249": 3.5, "ak47": 5.5, "svd": 7.0, "mp5": 3.5}.get(gun, 4.5), 2.5, None if lmg else "bolt", 8)
        if "bolt" not in bones and not lmg:  # AK and SVD: the carrier and its handle cycle
            fire.rest(handle, "position", 0.0)
            fire.key(handle, "position", 0.04, (0, -8, 0))
            fire.rest(handle, "position", min(fire.length, 0.13))
        out["fire"] = fire

        r = mk(t["reload"])
        if lmg:
            tilt(r, 0.35, 3.9, (-10, -40, -8), (0, 0, -10))
            r.rest("cover", "rotation", 0.5)
            r.key("cover", "rotation", 0.8, (-70, 0, 0))
            r.key("cover", "rotation", 3.3, (-70, 0, 0))
            r.rest("cover", "rotation", 3.55)
            mag_swap(r, 1.0, 2.7, 30, (12, 0, 0))
            rack(r, handle, 3.7, 12, 0.15, 0.1, 0.12)
        else:
            tilt(r, 0.25, t["reload"] - 0.45, cant, lift)
            mag_swap(r, 0.3, min(1.35, t["reload"] - 1.0), 32, (8, 0, 0))
            rack(r, handle, t["reload"] - 0.75, 10)
            rack(r, "bolt", t["reload"] - 0.75, 8)
        out["reload"] = r

        j = mk(t["jam"])  # tap, rack, bang
        tilt(j, 0.15, t["jam"] - 0.3, (-10, -35, -6), (0, 0, -6))
        j.rest("mag", "position", 0.3)
        j.key("mag", "position", 0.36, (0, 0, -2))
        j.rest("mag", "position", 0.42)
        rack(j, handle, 0.55, 12)
        if not lmg:  # the LMG's bolt is hidden inside; only its handle shows
            rack(j, "bolt", 0.55, 8)
        out["jam"] = j

        m = mk(t["malfunction"])  # double feed: lock back, strip the mag, rack three times, reload, rack
        tilt(m, 0.2, t["malfunction"] - 0.35, cant, lift)
        m.rest(handle, "position", 0.3)
        m.key(handle, "position", 0.45, (0, -12, 0))
        m.key(handle, "position", 0.6, (0, -12, 0))
        m.rest(handle, "position", 0.7)
        if lmg:
            m.rest("cover", "rotation", 0.7)
            m.key("cover", "rotation", 0.95, (-70, 0, 0))
            m.key("cover", "rotation", 2.6, (-70, 0, 0))
            m.rest("cover", "rotation", 2.85)
            mag_swap(m, 1.0, 2.3, 30, (12, 0, 0))
            rack(m, handle, 2.95, 12)
        else:
            mag_swap(m, 0.75, 2.15, 32, (8, 0, 0))
            for i in range(3):
                rack(m, handle, 1.15 + i * 0.28, 10, 0.08, 0.03, 0.07)
                rack(m, "bolt", 1.15 + i * 0.28, 8, 0.08, 0.03, 0.07)
            rack(m, handle, 2.4, 10)
            rack(m, "bolt", 2.4, 8)
        out["malfunction"] = m

    elif family == "pistol":
        fire = mk(t["fire"])
        recoil(fire, 9 if gun == "m1911" else 7, 2, "slide", 7)
        if "hammer" in bones:  # the hammer is thrown back by the slide and stays cocked
            fire.rest("hammer", "rotation", 0.0)
            fire.key("hammer", "rotation", 0.04, (-20, 0, 0))
            fire.rest("hammer", "rotation", min(fire.length, 0.12))
        out["fire"] = fire
        r = mk(t["reload"])
        tilt(r, 0.15, t["reload"] - 0.25, (-15, -45, -10), (0, 0, -8))
        r.key("slide", "position", 0.0, (0, -7, 0))  # empty: the slide was locked back
        r.key("slide", "position", 1.05, (0, -7, 0))
        r.rest("slide", "position", 1.12)
        mag_swap(r, 0.12, 0.85, 26)
        out["reload"] = r
        j = mk(t["jam"])
        tilt(j, 0.1, t["jam"] - 0.2, (-10, -35, -6), (0, 0, -5))
        rack(j, "slide", 0.4, 7)
        out["jam"] = j
        m = mk(t["malfunction"])
        tilt(m, 0.15, t["malfunction"] - 0.25, (-15, -45, -10), (0, 0, -8))
        m.rest("slide", "position", 0.25)
        m.key("slide", "position", 0.4, (0, -7, 0))
        m.key("slide", "position", 1.6, (0, -7, 0))
        mag_swap(m, 0.45, 1.5, 26)
        rack(m, "slide", 1.9, 7)
        out["malfunction"] = m

    elif family == "pump":
        fire = mk(t["fire"])
        recoil(fire, 12, 4)
        rack(fire, "pump", 0.28, 11, 0.1, 0.06, 0.1)
        out["fire"] = fire
        r = mk(t["reload"])
        tilt(r, 0.3, t["reload"] - 0.5, (-20, -80, -10), (0, 0, -12))
        for i in range(4):
            s0 = 0.45 + i * 0.6
            r.rest("shell", "position", s0)
            r.key("shell", "position", s0 + 0.02, (0, -2, 16))
            r.key("shell", "position", s0 + 0.3, (0, -2, 8))
            r.rest("shell", "position", s0 + 0.45)
        rack(r, "pump", t["reload"] - 0.8, 11, 0.12, 0.06, 0.12)
        out["reload"] = r
        j = mk(t["jam"])  # short-stroked pump: slam it back and forward
        tilt(j, 0.12, t["jam"] - 0.25, (-10, -30, -6), (0, 0, -6))
        rack(j, "pump", 0.35, 11, 0.12, 0.1, 0.12)
        rack(j, "pump", 0.85, 11, 0.1, 0.05, 0.1)
        out["jam"] = j
        m = mk(t["malfunction"])  # a shell stuck in the port: rack, clear it, reload one
        tilt(m, 0.2, t["malfunction"] - 0.35, (-20, -80, -10), (0, 0, -12))
        rack(m, "pump", 0.35, 11, 0.12, 0.6, 0.12)
        m.rest("shell", "position", 0.4)
        m.key("shell", "position", 0.6, (0, 2, -6))
        m.key("shell", "position", 0.8, (0, 0, -16))
        m.rest("shell", "position", 0.82)
        m.key("shell", "position", 1.4, (0, -2, 16))
        m.key("shell", "position", 1.7, (0, -2, 8))
        m.rest("shell", "position", 1.9)
        rack(m, "pump", 2.2, 11)
        out["malfunction"] = m

    elif family == "bolt":
        def bolt_cycle(a, t0):
            a.rest("bolt", "rotation", t0)
            a.key("bolt", "rotation", t0 + 0.12, (0, -65, 0))
            a.rest("bolt", "position", t0 + 0.14)
            a.key("bolt", "position", t0 + 0.28, (0, -12, 0))
            a.key("bolt", "position", t0 + 0.34, (0, -12, 0))
            a.rest("bolt", "position", t0 + 0.48)
            a.key("bolt", "rotation", t0 + 0.5, (0, -65, 0))
            a.rest("bolt", "rotation", t0 + 0.6)

        fire = mk(t["fire"])
        recoil(fire, 14, 5)
        bolt_cycle(fire, 0.4)
        out["fire"] = fire
        r = mk(t["reload"])
        tilt(r, 0.25, t["reload"] - 0.4, cant, lift)
        r.rest("bolt", "rotation", 0.3)
        r.key("bolt", "rotation", 0.42, (0, -65, 0))
        r.key("bolt", "rotation", 2.4, (0, -65, 0))
        r.rest("bolt", "rotation", 2.5)
        r.rest("bolt", "position", 0.45)
        r.key("bolt", "position", 0.6, (0, -12, 0))
        r.key("bolt", "position", 2.2, (0, -12, 0))
        r.rest("bolt", "position", 2.35)
        mag_swap(r, 0.8, 1.9, 22)
        out["reload"] = r
        j = mk(t["jam"])
        tilt(j, 0.15, t["jam"] - 0.3, (-10, -35, -6), (0, 0, -6))
        bolt_cycle(j, 0.35)
        bolt_cycle(j, 0.95)
        out["jam"] = j
        m = mk(t["malfunction"])
        tilt(m, 0.2, t["malfunction"] - 0.35, cant, lift)
        m.rest("bolt", "rotation", 0.3)
        m.key("bolt", "rotation", 0.42, (0, -65, 0))
        m.key("bolt", "rotation", 2.95, (0, -65, 0))
        m.rest("bolt", "rotation", 3.05)
        m.rest("bolt", "position", 0.45)
        m.key("bolt", "position", 0.6, (0, -12, 0))
        for i in range(3):
            m.key("bolt", "position", 0.8 + i * 0.3, (0, -6, 0))
            m.key("bolt", "position", 0.95 + i * 0.3, (0, -12, 0))
        m.key("bolt", "position", 2.7, (0, -12, 0))
        m.rest("bolt", "position", 2.85)
        mag_swap(m, 1.0, 2.5, 22)
        out["malfunction"] = m

    elif family == "launcher_rear":  # Carl Gustaf: swing the venturi open, a round in from behind, close it
        fire = mk(t["fire"])
        recoil(fire, 7, 6)
        out["fire"] = fire
        r = mk(t["reload"])
        tilt(r, 0.3, t["reload"] - 0.5, (12, -20, -8), (0, 6, -4))
        r.rest("breech", "rotation", 0.4)
        r.key("breech", "rotation", 0.75, (0, 0, -95))
        r.key("breech", "rotation", 3.0, (0, 0, -95))
        r.rest("breech", "rotation", 3.35)
        r.rest("rocket", "scale", 0.0, 0.8)
        r.key("rocket", "scale", 0.85, (0, 0, 0))
        r.key("rocket", "scale", 1.5, (0, 0, 0))
        r.rest("rocket", "scale", 1.55)
        r.rest("rocket", "position", 0.0, 0.8)
        r.key("rocket", "position", 0.85, (0, -60, 0))
        r.key("rocket", "position", 1.55, (0, -60, 0))
        r.key("rocket", "position", 2.1, (0, -24, 0))
        r.rest("rocket", "position", 2.6)
        out["reload"] = r
        for action, length in (("jam", t["jam"]), ("malfunction", t["malfunction"])):  # a misfire: open, re-seat, close
            a = mk(length)
            tilt(a, 0.3, length - 0.5, (10, -18, -6), (0, 5, -3))
            a.rest("breech", "rotation", 0.5)
            a.key("breech", "rotation", 0.8, (0, 0, -95))
            a.key("breech", "rotation", length - 1.0, (0, 0, -95))
            a.rest("breech", "rotation", length - 0.7)
            a.rest("rocket", "position", 0.9)
            a.key("rocket", "position", 1.2, (0, -14, 0))
            a.key("rocket", "position", length - 1.4, (0, -14, 0))
            a.rest("rocket", "position", length - 1.1)
            out[action] = a

    elif family == "launcher_front":
        fire = mk(t["fire"])
        recoil(fire, 8, 5)
        out["fire"] = fire
        r = mk(t["reload"])
        tilt(r, 0.3, t["reload"] - 0.5, (10, -30, -10), (0, 8, -6))
        r.rest("rocket", "scale", 0.0, 0.45)
        r.key("rocket", "scale", 0.5, (0, 0, 0))
        r.key("rocket", "scale", 1.35, (0, 0, 0))
        r.rest("rocket", "scale", 1.4)
        r.key("rocket", "position", 1.4, (0, 40, 6))
        r.key("rocket", "position", 2.0, (0, 16, 0))
        r.rest("rocket", "position", 2.5)
        r.key("rocket", "position", 0.0, (0, 0, 0))
        r.key("rocket", "position", 0.5, (0, 0, 0))
        out["reload"] = r
        for action, length in (("jam", t["jam"]), ("malfunction", t["malfunction"])):  # a misfire: wait, re-seat
            a = mk(length)
            tilt(a, 0.3, length - 0.5, (8, -25, -8), (0, 6, -4))
            a.rest("rocket", "position", 0.6)
            a.key("rocket", "position", 0.9, (0, 10, 0))
            a.key("rocket", "position", length * 0.6, (0, 10, 0))
            a.rest("rocket", "position", length * 0.6 + 0.3)
            out[action] = a
    return out


def attachable_animations(ns, models=None):
    """Animation JSON for every gun: {name: animation} and, per gun, the animate entries. `models` maps each gun
    to its built model (for its animation family and bones)."""
    anims, animate = {}, {}
    for gun in TIMING:
        entries = []
        g = models[gun] if models else None
        built = build(gun, g.anim, set(g.bones)) if g else build(gun)
        for action, a in built.items():
            name = f"animation.{ns}.gun.{gun}.{action}"
            anims[name] = a.json()
            entries.append((action, name, active(seconds(gun, action))))
        animate[gun] = entries
    return anims, animate


def player_animations(ns):
    """Third-person arm motions the scripts play on the player (zero in first person)."""
    fp = "(1.0 - v.is_first_person)"

    def arms(length, keys):
        bones = {}
        for bone, frames in keys.items():
            bones[bone] = {"rotation": {str(t): [f"({v[0]}) * {fp}", f"({v[1]}) * {fp}", f"({v[2]}) * {fp}"]
                                        for t, v in frames.items()}}
        return {"loop": False, "animation_length": length, "bones": bones}

    return {
        f"animation.{ns}.player.reload": arms(2.0, {
            "leftArm": {0.0: (0, 0, 0), 0.3: (45, -25, 0), 0.9: (55, -30, 0), 1.3: (20, -10, 0), 1.6: (0, 15, 0), 2.0: (0, 0, 0)},
            "rightArm": {0.0: (0, 0, 0), 0.3: (-8, 6, 0), 1.6: (-8, 6, 0), 2.0: (0, 0, 0)},
        }),
        f"animation.{ns}.player.rack": arms(1.2, {
            "leftArm": {0.0: (0, 0, 0), 0.25: (-10, 30, 0), 0.5: (-5, 45, 0), 0.7: (-10, 30, 0), 1.2: (0, 0, 0)},
            "rightArm": {0.0: (0, 0, 0), 0.2: (-6, 8, 0), 1.0: (-6, 8, 0), 1.2: (0, 0, 0)},
        }),
    }
