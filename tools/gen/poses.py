"""Third-person arm poses the scripts play on a player holding each kind of item (added to the game's own
'holding an item' pose, which already raises the right arm 18 degrees). The pose is multiplied by
(1 - v.is_first_person) in the animation, so the first-person view is untouched."""

POSES = {
    "rifle": {"rightArm": (-72.0, -8.0, 0.0), "leftArm": (-86.0, 38.0, 0.0)},
    "pistol": {"rightArm": (-72.0, -4.0, 0.0), "leftArm": (-80.0, 42.0, 0.0)},
    "launcher": {"rightArm": (-72.0, -8.0, 0.0), "leftArm": (-86.0, 34.0, 0.0)},
}
