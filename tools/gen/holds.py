"""Works out the hold animations of the held items instead of guessing angles.

For each kind of item and each view the bone 'item' needs a rotation and a position such that, with the
arm where the game (and the add-on's pose) puts it, the item's frame lands where it should: the grip in the
hand (or at a chosen spot in first person), the barrel pointing where the player looks and the sights up.
Bedrock bone rotations are converted with the same convention the viewer and modelkit use.
"""
from __future__ import annotations

import math

import numpy as np

from held import GRIP
from viewer import FIRST_PERSON_ARM, PLAYER, rot_matrix, third_person_arms, transform


def euler(m):
    """Bedrock (rx, ry, rz) whose rot_matrix is m."""
    ay = math.asin(max(-1.0, min(1.0, -m[2, 0])))
    ax = math.atan2(m[2, 1], m[2, 2])
    az = math.atan2(m[1, 0], m[0, 0])
    rot = (-math.degrees(ax), math.degrees(ay), -math.degrees(az))
    assert np.allclose(rot_matrix(*rot), m, atol=1e-6), "euler extraction failed"
    return tuple(round(v, 2) for v in rot)


def frame(forward, up):
    """Rotation taking the item frame (+Y forward, -Z up, +X its left) to the given directions."""
    f = np.array(forward, float)
    f /= np.linalg.norm(f)
    u = np.array(up, float)
    u -= f * (u @ f)
    u /= np.linalg.norm(u)
    # item axes in item space: +Y = forward, -Z = up  =>  +Z = down; +X completes a right-handed set
    y_axis, z_axis = f, -u
    x_axis = np.cross(y_axis, z_axis)
    return np.stack([x_axis, y_axis, z_axis], axis=1)


def solve(anim, forward, up, grip_at=None):
    """Rotation and position for bone 'item' (child of rightItem) under the arm animation `anim`."""
    bones = {name: (parent, pivot, None) for name, (parent, pivot, _c) in PLAYER.items()}
    origin = np.array([[0.0, 0.0, 0.0]])
    t = transform(origin.copy(), "rightItem", bones, anim)[0]
    basis = transform(np.eye(3), "rightItem", bones, anim) - t
    m = basis.T  # parent-space vector -> model-space vector
    want = frame(forward, up)
    rot = euler(m.T @ want)
    g = np.array(GRIP)
    if grip_at is None:
        pos = (0.0, 0.0, 0.0)
    else:
        target = np.array(grip_at, float)
        pos = tuple(round(v, 2) for v in (np.linalg.solve(m, target - t) - g))
    return rot, pos


def compute():
    """(third person (rotation, position), first person (rotation, position)) for each kind of item."""
    holds = {}
    for kind in ("rifle", "pistol", "launcher"):
        third = solve(third_person_arms(kind), (0.0, -0.05, -1.0), (0.0, 1.0, 0.0))
        # In first person the gun sits in front of the arm the game draws at the lower right (whose fist is
        # about 11, 18, 17 from the model origin) and points a little inwards, at the crosshair far ahead.
        grip = {"rifle": (8.0, 15.0, 20.0), "pistol": (6.5, 16.0, 16.0), "launcher": (8.0, 13.5, 22.0)}[kind]
        aim = np.array([0.0, 23.0, 120.0]) - np.array(grip)
        first = solve(dict(FIRST_PERSON_ARM), aim, (-0.08, 1.0, 0.0), grip_at=grip)
        holds[kind] = (third, first)
    # Knives, grenades and gear are carried, not aimed: angled up and forward like a tool.
    for kind in ("blade", "gear", "grenade"):
        third = solve(third_person_arms(kind), (0.0, 0.55, -1.0), (0.0, 1.0, 0.4))
        first = solve(dict(FIRST_PERSON_ARM), (-0.35, 0.45, 1.0), (0.0, 1.0, -0.2), grip_at=(6.0, 16.5, 13.0))
        holds[kind] = (third, first)
    return holds


if __name__ == "__main__":
    for k, v in compute().items():
        print(k, v)
