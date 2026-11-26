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
VERSION = [1, 3, 0]
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
# Firearms: id, name, rarity. Their stats are in GUN_STATS (written to behavior_pack/scripts/gundata.js).
GUNS = [
    ("glock17", "Glock 17", "common"),
    ("m1911", "Colt M1911A1", "common"),
    ("mp5", "H&K MP5A3", "uncommon"),
    ("ump45", "H&K UMP45", "uncommon"),
    ("m4a1", "Colt M4A1", "uncommon"),
    ("ak47", "AKM (AK-47)", "uncommon"),
    ("m249", "FN M249 SAW", "rare"),
    ("rem870", "Remington 870", "uncommon"),
    ("awm", "Accuracy International AWM", "rare"),
    ("svd", "SVD Dragunov", "rare"),
    ("carl_gustaf", "Carl Gustaf M4", "rare"),
    ("rpg7", "RPG-7", "rare"),
    ("deagle", "IWI Desert Eagle", "uncommon"),
    ("p90", "FN P90", "uncommon"),
    ("scar_h", "FN SCAR-H", "rare"),
    ("barrett", "Barrett M82A1", "epic"),
    ("pkm", "PKM", "rare"),
]

# Cartridges: id, name, stack, muzzle velocity m/s (in the guns that fire them), drag per block, bullet mass g.
# The drag is the fraction of speed lost per block flown at the start (v = v0 * e^(-drag * distance)).
AMMO = [
    ("ammo_9mm", "9x19mm Parabellum", 64),
    ("ammo_45acp", ".45 ACP", 64),
    ("ammo_556", "5.56x45mm NATO", 64),
    ("ammo_762x39", "7.62x39mm", 64),
    ("ammo_762x54r", "7.62x54mmR", 64),
    ("ammo_338", ".338 Lapua Magnum", 32),
    ("ammo_12g", "12 Gauge 00 Buckshot", 32),
    ("ammo_84mm", "84mm HEAT Round", 4),
    ("ammo_pg7v", "PG-7V Rocket", 4),
    ("ammo_50ae", ".50 Action Express", 32),
    ("ammo_57", "5.7x28mm", 64),
    ("ammo_762x51", "7.62x51mm NATO", 64),
    ("ammo_50bmg", ".50 BMG", 16),
]
CALIBER = {a[0]: a[1] for a in AMMO}

# Per gun: what it fires, how and how well. The script reads these through gundata.js.
#   ammo, mag (rounds), mode (auto | semi | pump | bolt | launcher), rpm (rounds per minute; semi: the fastest
#   follow-up), damage (per bullet or pellet at the muzzle), pellets, velocity (m/s), drag (per block),
#   headshot (multiplier), hip / ads (spread in degrees, hip fire / crouched), vrec / hrec (degrees of
#   vertical / random horizontal recoil per shot), bloom (degrees added per shot, decaying), sound, jam
#   (chance per round of a stoppage), pose (third-person hold).
GUN_STATS = {
    "glock17": dict(ammo="ammo_9mm", mag=17, mode="semi", rpm=500, damage=5.5, velocity=375, drag=0.0024, headshot=1.8,
                    hip=2.0, ads=0.9, vrec=1.5, hrec=0.6, bloom=0.5, sound="pistol", jam=0.0015, pose="pistol"),
    "m1911": dict(ammo="ammo_45acp", mag=7, mode="semi", rpm=420, damage=7.5, velocity=253, drag=0.0021, headshot=1.8,
                  hip=2.2, ads=1.0, vrec=2.6, hrec=0.8, bloom=0.7, sound="heavy_pistol", jam=0.0025, pose="pistol"),
    "mp5": dict(ammo="ammo_9mm", mag=30, mode="auto", rpm=800, damage=4.5, velocity=400, drag=0.0024, headshot=1.6,
                hip=2.4, ads=0.9, vrec=0.65, hrec=0.45, bloom=0.22, sound="smg", jam=0.002, pose="rifle"),
    "ump45": dict(ammo="ammo_45acp", mag=25, mode="auto", rpm=600, damage=6.0, velocity=285, drag=0.0021, headshot=1.6,
                  hip=2.6, ads=1.0, vrec=0.95, hrec=0.55, bloom=0.28, sound="smg", jam=0.0025, pose="rifle"),
    "m4a1": dict(ammo="ammo_556", mag=30, mode="auto", rpm=800, damage=6.0, velocity=910, drag=0.0012, headshot=1.9,
                 hip=2.4, ads=0.45, vrec=0.85, hrec=0.45, bloom=0.22, sound="assault_rifle", jam=0.003, pose="rifle"),
    "ak47": dict(ammo="ammo_762x39", mag=30, mode="auto", rpm=600, damage=7.0, velocity=715, drag=0.0011, headshot=1.9,
                 hip=2.8, ads=0.6, vrec=1.35, hrec=0.8, bloom=0.3, sound="ak47", jam=0.0015, pose="rifle"),
    "m249": dict(ammo="ammo_556", mag=200, mode="auto", rpm=800, damage=5.5, velocity=915, drag=0.0012, headshot=1.7,
                 hip=3.6, ads=1.0, vrec=0.8, hrec=0.65, bloom=0.2, sound="lmg", jam=0.004, pose="rifle"),
    "rem870": dict(ammo="ammo_12g", mag=4, mode="pump", rpm=70, damage=3.2, pellets=9, velocity=400, drag=0.006,
                   headshot=1.3, hip=5.5, ads=4.2, vrec=4.5, hrec=1.2, bloom=0.0, sound="shotgun", jam=0.004, pose="rifle"),
    "awm": dict(ammo="ammo_338", mag=5, mode="bolt", rpm=40, damage=26.0, velocity=914, drag=0.0005, headshot=2.5,
                hip=4.5, ads=0.05, vrec=5.5, hrec=1.0, bloom=0.0, sound="sniper", jam=0.001, pose="rifle"),
    "svd": dict(ammo="ammo_762x54r", mag=10, mode="semi", rpm=240, damage=13.0, velocity=830, drag=0.0008, headshot=2.2,
                hip=3.2, ads=0.18, vrec=3.0, hrec=0.8, bloom=0.6, sound="dmr", jam=0.002, pose="rifle"),
    "carl_gustaf": dict(ammo="ammo_84mm", mag=1, mode="launcher", rpm=20, damage=0, velocity=120, drag=0.0, headshot=1.0,
                        hip=1.2, ads=0.4, vrec=6.0, hrec=1.0, bloom=0.0, sound="rocket_launch", jam=0.006, pose="launcher",
                        projectile="rocket", power=4.2),
    "rpg7": dict(ammo="ammo_pg7v", mag=1, mode="launcher", rpm=20, damage=0, velocity=115, drag=0.0, headshot=1.0,
                 hip=1.6, ads=0.6, vrec=5.0, hrec=1.2, bloom=0.0, sound="rocket_launch", jam=0.01, pose="launcher",
                 projectile="rocket", power=3.4),
    "deagle": dict(ammo="ammo_50ae", mag=7, mode="semi", rpm=300, damage=11.0, velocity=470, drag=0.0020, headshot=1.9,
                   hip=2.6, ads=1.1, vrec=5.0, hrec=1.4, bloom=1.2, sound="heavy_pistol", jam=0.004, pose="pistol"),
    "p90": dict(ammo="ammo_57", mag=50, mode="auto", rpm=900, damage=4.6, velocity=715, drag=0.0019, headshot=1.7,
                hip=2.2, ads=0.8, vrec=0.5, hrec=0.4, bloom=0.18, sound="smg", jam=0.002, pose="rifle"),
    "scar_h": dict(ammo="ammo_762x51", mag=20, mode="auto", rpm=600, damage=9.0, velocity=790, drag=0.0009, headshot=2.0,
                   hip=2.8, ads=0.4, vrec=1.6, hrec=0.75, bloom=0.35, sound="dmr", jam=0.002, pose="rifle"),
    "barrett": dict(ammo="ammo_50bmg", mag=10, mode="semi", rpm=120, damage=40.0, velocity=853, drag=0.0004, headshot=2.0,
                    hip=6.0, ads=0.06, vrec=7.5, hrec=1.5, bloom=1.0, sound="sniper", jam=0.002, pose="rifle"),
    "pkm": dict(ammo="ammo_762x54r", mag=100, mode="auto", rpm=650, damage=7.5, velocity=825, drag=0.0008, headshot=1.8,
                hip=3.8, ads=1.1, vrec=1.1, hrec=0.8, bloom=0.25, sound="lmg", jam=0.003, pose="rifle"),
}

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
# weapon: rifle | sniper | launcher (decides projectile and firing rhythm); gun: the model they carry
SOLDIERS = {
    "nato_rifleman": dict(gun="m4a1", team="nato", name="NATO Rifleman", hp=30, speed=0.28, weapon="rifle", xp=6,
                          skins=["nato_woodland", "nato_woodland_b", "nato_desert"], egg=("#4f5d34", "#3f7fd0")),
    "nato_marksman": dict(gun="awm", team="nato", name="NATO Marksman", hp=24, speed=0.26, weapon="sniper", xp=8,
                          skins=["nato_marksman"], egg=("#5f6e3c", "#9ccff0")),
    "nato_heavy": dict(gun="carl_gustaf", team="nato", name="NATO Anti-Tank Gunner", hp=36, speed=0.25, weapon="launcher", xp=10,
                       skins=["nato_heavy"], egg=("#3a4424", "#25507e")),
    "redfang_fighter": dict(gun="ak47", team="redfang", name="Red Fang Fighter", hp=28, speed=0.29, weapon="rifle", xp=6,
                            skins=["redfang_black", "redfang_olive", "redfang_hoodie"], egg=("#1e1e22", "#c8302c")),
    "redfang_sniper": dict(gun="svd", team="redfang", name="Red Fang Sniper", hp=22, speed=0.26, weapon="sniper", xp=8,
                           skins=["redfang_sniper"], egg=("#3a3a2e", "#e05a4a")),
    "redfang_rpg": dict(gun="rpg7", team="redfang", name="Red Fang RPG Gunner", hp=32, speed=0.25, weapon="launcher", xp=10,
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
    "heavy_pistol", "ak47", "dmr", "suppressed", "attach", "bullet_crack",
]
LOUD_SOUNDS = {"pistol", "heavy_pistol", "smg", "assault_rifle", "ak47", "lmg", "shotgun", "sniper", "dmr", "rocket_launch", "explosion",
               "tank_fire", "alarm", "battle_start", "victory", "defeat"}


def attachment_items():
    """Attachment items: (id, name, slot), from the catalogue in attach.py."""
    from attach import CATALOGUE
    return [(k, v[0], v[1]) for k, v in CATALOGUE.items()]


def item_ids():
    ids = [g[0] for g in GUNS] + [a[0] for a in AMMO] + [a[0] for a in attachment_items()] + [t[0] for t in THROWABLES] + [g[0] for g in GEAR]
    ids += [m[0] for m in MELEE] + [f[0] for f in FOOD] + [v[0] for v in VEHICLE_KITS]
    return ids


def block_ids():
    return [b[0] for b in BLOCKS]


def entity_ids():
    return list(SOLDIERS) + list(PROJECTILES) + list(VEHICLES) + ["corpse"]
