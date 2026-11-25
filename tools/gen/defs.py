"""The single list of everything the add-on contains.

content.py turns these tables into pack JSON, models.py builds the 3D models, art.py paints the
textures and audio.py synthesises the sounds. The scripts in behavior_pack/scripts use the same ids,
and tools/validate.py checks that every id a script mentions is defined here.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BP = ROOT / "behavior_pack"
RP = ROOT / "resource_pack"

NS = "frontline"
TITLE = "Frontline: NATO vs Red Fang"
VERSION = [1, 0, 0]
MIN_ENGINE = [1, 21, 90]
DESCRIPTION = (
    "Large-scale battles between NATO and the Red Fang terror cell: capture flags, drain tickets, "
    "pick a class, drive jeeps and tanks and fight beside AI soldiers."
)

UUIDS = {
    "bp_header": "42f759db-d178-41e6-9c35-e3f792dd35be",
    "bp_data": "5110ae2f-1259-46e1-94e0-a82dbfa4d2f3",
    "bp_script": "bc78a123-5b8d-47a6-90d3-aa94a874d5de",
    "rp_header": "318b6965-393b-4691-ab71-abf4a284c06d",
    "rp_resources": "9fe53dce-673d-42f1-af07-9d09b79d714c",
}

TEAMS = {
    "nato": dict(name="NATO", colour="#3f7fd0", wool="minecraft:blue_wool", glass="minecraft:blue_stained_glass"),
    "redfang": dict(name="Red Fang", colour="#c8302c", wool="minecraft:red_wool", glass="minecraft:red_stained_glass"),
}

# ------------------------------------------------------------------ items
# Firearms (stats live in behavior_pack/scripts/weapons.js): id, name, rarity
GUNS = [
    ("service_pistol", "Service Pistol", "common"),
    ("smg", "Talon SMG", "uncommon"),
    ("assault_rifle", "Vanguard Assault Rifle", "uncommon"),
    ("lmg", "Bulwark LMG", "rare"),
    ("shotgun", "Breacher Shotgun", "uncommon"),
    ("sniper_rifle", "Longshot Sniper Rifle", "rare"),
    ("rocket_launcher", "Hornet Rocket Launcher", "rare"),
]

AMMO = [
    ("pistol_ammo", "Pistol Ammo"),
    ("rifle_ammo", "Rifle Ammo"),
    ("shotgun_shells", "Shotgun Shells"),
    ("sniper_rounds", "Sniper Rounds"),
    ("rocket", "Rocket"),
]

# Thrown items: id, name, projectile entity
THROWABLES = [
    ("frag_grenade", "Frag Grenade", "frag_grenade"),
    ("smoke_grenade", "Smoke Grenade", "smoke_grenade"),
]

# Gear used with right-click / hold-tap: id, name, stack, rarity
GEAR = [
    ("medkit", "Medkit", 8, "common"),
    ("ammo_box", "Ammo Box", 8, "common"),
    ("repair_tool", "Repair Tool", 1, "uncommon"),
    ("binoculars", "Binoculars", 1, "common"),
    ("field_radio", "Field Radio", 1, "uncommon"),
]

MELEE = [("combat_knife", "Combat Knife", 7, 400)]

FOOD = [("field_ration", "Field Ration", 8, 0.9)]

# Items that place a vehicle: id, name, entity
VEHICLE_KITS = [
    ("jeep_kit", "Jeep Deployment Kit", "jeep"),
    ("tank_kit", "Tank Deployment Kit", "tank"),
]

# ------------------------------------------------------------------ blocks
# id, name, sound, seconds to mine, map colour, light, render
BLOCKS = [
    ("sandbags", "Sandbags", "sand", 1.2, "#b8a77a", 0, "opaque"),
    ("barbed_wire", "Barbed Wire", "metal", 0.8, "#6e747a", 0, "alpha_test"),
    ("ammo_crate", "Ammo Crate", "wood", 2.0, "#4d5a33", 0, "opaque"),
    ("spawn_beacon", "Spawn Beacon", "metal", 1.0, "#2b6fd6", 9, "opaque"),
    ("flag_neutral", "Neutral Flag Base", "stone", -1, "#d8d8d8", 6, "opaque"),
    ("flag_nato", "NATO Flag Base", "stone", -1, "#3f7fd0", 10, "opaque"),
    ("flag_redfang", "Red Fang Flag Base", "stone", -1, "#c8302c", 10, "opaque"),
]

# ------------------------------------------------------------------ soldiers
# weapon: rifle | sniper | launcher (decides model, projectile and firing rhythm)
SOLDIERS = {
    "nato_rifleman": dict(team="nato", name="NATO Rifleman", hp=30, speed=0.28, weapon="rifle", xp=6,
                          skins=["nato_woodland", "nato_woodland_b", "nato_desert"], egg=("#4f5d34", "#3f7fd0")),
    "nato_marksman": dict(team="nato", name="NATO Marksman", hp=24, speed=0.26, weapon="sniper", xp=8,
                          skins=["nato_marksman"], egg=("#5f6e3c", "#9ccff0")),
    "nato_heavy": dict(team="nato", name="NATO Anti-Tank Gunner", hp=36, speed=0.25, weapon="launcher", xp=10,
                       skins=["nato_heavy"], egg=("#3a4424", "#25507e")),
    "redfang_fighter": dict(team="redfang", name="Red Fang Fighter", hp=28, speed=0.29, weapon="rifle", xp=6,
                            skins=["redfang_black", "redfang_olive", "redfang_hoodie"], egg=("#1e1e22", "#c8302c")),
    "redfang_sniper": dict(team="redfang", name="Red Fang Sniper", hp=22, speed=0.26, weapon="sniper", xp=8,
                           skins=["redfang_sniper"], egg=("#3a3a2e", "#e05a4a")),
    "redfang_rpg": dict(team="redfang", name="Red Fang RPG Gunner", hp=32, speed=0.25, weapon="launcher", xp=10,
                        skins=["redfang_rpg"], egg=("#2a2a2e", "#7e1a17")),
}

# Weapon behaviour for AI soldiers: projectile, burst, min/max seconds between bursts, range
AI_WEAPONS = {
    "rifle": dict(projectile="bullet", burst=3, interval=(1.4, 2.4), radius=28.0),
    "sniper": dict(projectile="sniper_bullet", burst=1, interval=(3.2, 4.5), radius=48.0),
    "launcher": dict(projectile="rocket", burst=1, interval=(5.5, 8.0), radius=34.0),
}

# Projectiles: id -> (power, gravity, impact damage or 0 when the script handles the hit)
PROJECTILES = {
    "bullet": (4.5, 0.0, 4),
    "sniper_bullet": (6.0, 0.0, 13),
    "rocket": (2.2, 0.0, 0),
    "tank_shell": (3.5, 0.01, 0),
    "frag_grenade": (0.0, 0.05, 0),
    "smoke_grenade": (0.0, 0.05, 0),
}

VEHICLES = {
    "jeep": dict(name="Jeep", hp=120, speed=0.36, seats=4, egg=("#5a6a3a", "#2c2f34"), skins=["jeep_nato", "jeep_redfang"]),
    "tank": dict(name="Tank", hp=400, speed=0.17, seats=2, egg=("#4f5d34", "#1e1e22"), skins=["tank_nato", "tank_redfang"]),
}

# ------------------------------------------------------------------ sounds (synthesised by audio.py)
SOUNDS = [
    "pistol", "smg", "assault_rifle", "lmg", "shotgun", "sniper", "rocket_launch", "explosion", "tank_fire",
    "dry_fire", "reload", "grenade_pin", "hitmarker", "kill", "capture", "capture_lost", "alarm", "battle_start",
    "victory", "defeat", "radio", "heal", "resupply", "repair", "click", "engine",
]
LOUD_SOUNDS = {"pistol", "smg", "assault_rifle", "lmg", "shotgun", "sniper", "rocket_launch", "explosion",
               "tank_fire", "alarm", "battle_start", "victory", "defeat"}


def item_ids():
    ids = [g[0] for g in GUNS] + [a[0] for a in AMMO] + [t[0] for t in THROWABLES] + [g[0] for g in GEAR]
    ids += [m[0] for m in MELEE] + [f[0] for f in FOOD] + [v[0] for v in VEHICLE_KITS]
    return ids


def block_ids():
    return [b[0] for b in BLOCKS]


def entity_ids():
    return list(SOLDIERS) + list(PROJECTILES) + list(VEHICLES)
