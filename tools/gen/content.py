#!/usr/bin/env python3
"""Writes every JSON file of both packs, and the 3D models with their textures, from the tables in defs.py
and the model builders in held.py and models.py.

Usage:  python3 tools/gen/content.py
Generated folders are wiped and rewritten, so edit the tables and builders, not the output.
"""
from __future__ import annotations

import json
import shutil

import gunanims
import held as H
import holds
import models as M
import attach
from defs import (AI_WEAPONS, AMMO, BLOCKS, BP, CALIBER, DESCRIPTION, FOOD, GEAR, GUN_STATS, GUNS, MELEE, MIN_ENGINE, NS,
                  PROJECTILES, ROOT, RP, SOLDIERS, TEAMS, THROWABLES, TITLE, UUIDS, VEHICLE_KITS, VEHICLES, VERSION)
from poses import POSES

LANG: list[str] = []
RENDER_CONTROLLERS: dict[str, dict] = {}
ANIMATIONS: dict[str, dict] = {}
SOUND_ENTITIES: dict[str, dict] = {}
ITEM_TEXTURES: dict[str, str] = {}
TERRAIN: dict[str, str] = {}
BLOCK_SOUNDS: dict[str, dict] = {}


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def nid(name):
    return f"{NS}:{name}"


def other(team):
    return "redfang" if team == "nato" else "nato"


def save_model(model, folder, texture_name=None, texture=None):
    """Writes a model's geometry (and texture) into the resource pack."""
    write(RP / "models" / folder / f"{model.name}.geo.json", model.geometry())
    if texture_name:
        path = RP / "textures" / "models" / f"{texture_name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        (texture or model.hd()).save(path)


def same_layout(a, b):
    return [c.uv for bn in a.bones for c in bn.cubes] == [c.uv for bn in b.bones for c in bn.cubes]


# ====================================================================== manifests

def manifests():
    version_text = ".".join(map(str, VERSION))
    write(BP / "manifest.json", {
        "format_version": 2,
        "header": {"name": f"{TITLE} [BP]", "description": f"{DESCRIPTION} §7v{version_text}",
                   "uuid": UUIDS["bp_header"], "version": VERSION, "min_engine_version": MIN_ENGINE},
        "modules": [
            {"type": "data", "uuid": UUIDS["bp_data"], "version": VERSION},
            {"type": "script", "language": "javascript", "uuid": UUIDS["bp_script"], "entry": "scripts/main.js",
             "version": VERSION},
        ],
        "dependencies": [
            {"uuid": UUIDS["rp_header"], "version": VERSION},
            {"module_name": "@minecraft/server", "version": "2.0.0"},
            {"module_name": "@minecraft/server-ui", "version": "2.0.0"},
        ],
        "metadata": {"authors": ["Frontline add-on contributors"], "license": "MIT"},
    })
    write(RP / "manifest.json", {
        "format_version": 2,
        "header": {"name": f"{TITLE} [RP]", "description": f"{DESCRIPTION} §7v{version_text}",
                   "uuid": UUIDS["rp_header"], "version": VERSION, "min_engine_version": MIN_ENGINE},
        "modules": [{"type": "resources", "uuid": UUIDS["rp_resources"], "version": VERSION}],
        "dependencies": [{"uuid": UUIDS["bp_header"], "version": VERSION}],
        "metadata": {"authors": ["Frontline add-on contributors"], "license": "MIT"},
    })


# ====================================================================== items

def item(name, display, category="items", stack=64, rarity=None, extra=None):
    ITEM_TEXTURES[f"{NS}_{name}"] = f"textures/items/{NS}/{name}"
    LANG.append(f"item.{NS}.{name}.name={display}")
    comps = {
        "minecraft:icon": {"textures": {"default": f"{NS}_{name}"}},
        "minecraft:display_name": {"value": f"item.{NS}.{name}.name"},
        "minecraft:max_stack_size": stack,
    }
    if rarity and rarity != "common":
        comps["minecraft:rarity"] = rarity
    comps.update(extra or {})
    write(BP / "items" / f"{name}.json", {
        "format_version": "1.21.50",
        "minecraft:item": {"description": {"identifier": nid(name), "menu_category": {"category": category}},
                           "components": comps},
    })


def items():
    for name, display, rarity in GUNS:
        display = f"{display} ({CALIBER[GUN_STATS[name]['ammo']]})"
        item(name, display, "equipment", 1, rarity, {
            "minecraft:hand_equipped": True,
            "minecraft:can_destroy_in_creative": False,
            # Each gun's own cooldown category: the scripts start cooldowns of set lengths on it to tell
            # the 3D model which animation to play (see gunanims.py).
            "minecraft:cooldown": {"category": f"{NS}_{name}", "duration": 0.05},
        })
    for name, display, stack in AMMO:
        item(name, display, "equipment", stack)
    # Attachments. Each has a cooldown category of its own: while one is fitted to the gun in hand, the scripts
    # keep that category's cooldown running and the gun's model shows the attachment (see attachables()).
    for att_id, (display, slot, _guns, _mods) in attach.CATALOGUE.items():
        item(att_id, display, "equipment", 16, "uncommon" if slot == "optic" else None, {
            "minecraft:cooldown": {"category": attach.category(att_id), "duration": 0.05},
            "minecraft:can_destroy_in_creative": False,
        })
    for name, display, projectile in THROWABLES:
        item(name, display, "equipment", 4, None, {
            "minecraft:throwable": {"do_swing_animation": True, "launch_power_scale": 1.0, "max_launch_power": 1.3},
            "minecraft:projectile": {"projectile_entity": nid(projectile), "minimum_critical_power": 1.0},
        })
    for name, display, stack, rarity in GEAR:
        item(name, display, "equipment", stack, rarity, {"minecraft:can_destroy_in_creative": False})
    for name, display, damage, durability in MELEE:
        item(name, display, "equipment", 1, None, {
            "minecraft:hand_equipped": True,
            "minecraft:damage": damage,
            "minecraft:durability": {"max_durability": durability},
            "minecraft:enchantable": {"slot": "sword", "value": 10},
            "minecraft:can_destroy_in_creative": False,
        })
    for name, display, nutrition, saturation in FOOD:
        item(name, display, "items", 16, None, {
            "minecraft:use_animation": "eat",
            "minecraft:use_modifiers": {"use_duration": 1.6, "movement_modifier": 0.35},
            "minecraft:food": {"nutrition": nutrition, "saturation_modifier": saturation},
        })
    for name, display, entity in VEHICLE_KITS:
        item(name, display, "equipment", 1, "rare", {"minecraft:entity_placer": {"entity": nid(entity)}})
    write(RP / "textures" / "item_texture.json", {
        "resource_pack_name": NS, "texture_name": "atlas.items",
        "texture_data": {k: {"textures": v} for k, v in sorted(ITEM_TEXTURES.items())},
    })


def attachment_animation(g):
    """A looping animation that shows each attachment of gun g only while it is fitted, and hides the factory part it
    replaces, by scaling the bones to nothing. Each attachment's bone a_<id> shows while the cooldown category
    frontline_att_<id> runs on the holder (the scripts keep it running while that attachment is fitted to the gun in
    hand). Done with scale in an animation rather than render-controller part visibility so that, if a version of the
    game does not answer the query, the attachments stay hidden and the gun itself still draws."""
    bones = {}
    by_slot = {}
    for att_id in getattr(g, "attachments", []):
        slot = attach.CATALOGUE[att_id][1]
        by_slot.setdefault(slot, []).append(att_id)
        on = f"(q.cooldown_time_remaining('{attach.category(att_id)}') > 0.0 ? 1.0 : 0.0)"
        bones[f"a_{att_id}"] = {"scale": [on, on, on]}
    for slot, ids in by_slot.items():
        part = "def_mag" if slot == "magazine" else f"def_{slot}"
        if part in g.bones:
            shown = " || ".join(f"q.cooldown_time_remaining('{attach.category(a)}') > 0.0" for a in ids)
            off = f"(({shown}) ? 0.0 : 1.0)"
            bones[part] = {"scale": [off, off, off]}
    return {"loop": True, "bones": bones}


def attachables():
    """The 3D models drawn in the hand in place of the flat item icon, with the guns' animations."""
    built = H.build_all()
    hold_table = holds.compute()
    gun_anims, gun_animate = gunanims.attachable_animations(NS, {k: built[k] for k in gunanims.TIMING})
    ANIMATIONS.update(gun_anims)
    ANIMATIONS.update(gunanims.player_animations(NS))
    for key, g in built.items():
        save_model(g.model, "entity/held", f"held/{key}")  # the game reads models from models/entity
        animations = {"first": f"animation.{NS}.hold.{g.hold}.first_person",
                      "third": f"animation.{NS}.hold.{g.hold}.third_person"}
        animate = [{"first": "c.is_first_person"}, {"third": "!c.is_first_person"}]
        for action, name, condition in gun_animate.get(key, []):
            animations[action] = name
            animate.append({action: condition})
        controller = "controller.render.item_default"
        if getattr(g, "attachments", None):
            name = f"animation.{NS}.gun.{key}.attachments"
            ANIMATIONS[name] = attachment_animation(g)
            animations["attachments"] = name
            animate.append("attachments")
        write(RP / "attachables" / f"{key}.json", {
            "format_version": "1.10.0",
            "minecraft:attachable": {"description": {
                # The identifier must be the item's own: only then does the model replace the flat item.
                "identifier": nid(key),
                "materials": {"default": "entity_alphatest", "enchanted": "entity_alphatest_glint"},
                "textures": {"default": f"textures/models/held/{key}",
                             "enchanted": "textures/misc/enchanted_item_glint"},
                "geometry": {"default": f"geometry.{NS}.held_{key}"},
                "animations": animations,
                "scripts": {"animate": animate},
                "render_controllers": [controller],
            }},
        })
    for kind, (third, first) in hold_table.items():
        for view, (rot, pos), sc in (("third_person", third, H.SCALE), ("first_person", first, H.FP_SCALE)):
            ANIMATIONS[f"animation.{NS}.hold.{kind}.{view}"] = {
                "loop": True,
                "bones": {"item": {"rotation": list(rot), "position": [float(v) for v in pos], "scale": sc}},
            }
    # Third-person poses the scripts play on players holding a gun; zero in first person.
    for kind, pose in POSES.items():
        bones = {}
        for bone, (rx, ry, rz) in pose.items():
            pitch = " + q.target_x_rotation" if bone in ("rightArm", "leftArm") else ""
            bones[bone] = {"rotation": [f"({rx}{pitch}) * (1.0 - v.is_first_person)",
                                        f"({ry}) * (1.0 - v.is_first_person)", f"({rz}) * (1.0 - v.is_first_person)"]}
        ANIMATIONS[f"animation.{NS}.player.aim_{kind}"] = {"loop": True, "bones": bones}
    gun_data(built)
    return built


def gun_data(built):
    """Writes everything the scripts need to know about the guns and attachments (gundata.js), and the attachment
    reference (docs/attachments.md)."""
    names = dict((g[0], g[1]) for g in GUNS)
    guns = {}
    for k in gunanims.TIMING:
        st = dict(GUN_STATS[k])
        st["ammo"] = nid(st["ammo"])
        if "projectile" in st:
            st["projectile"] = nid(st["projectile"])
        st["sound"] = f"{NS}.{st['sound']}"
        guns[nid(k)] = {"key": k, "name": names[k], "caliber": CALIBER[GUN_STATS[k]["ammo"]], **st,
                        "timing": gunanims.TIMING[k],
                        "slots": [s for s in attach.SLOT_ORDER if s in built[k].mounts or
                                  (s == "magazine" and built[k].mag_profile is not None)],
                        "mounts": {slot: m for slot, m in built[k].mounts.items()}}
    atts = {nid(a): {"key": a, "name": v[0], "slot": v[1], "guns": [nid(x) for x in v[2]], "mods": v[3],
                     "category": attach.category(a)}
            for a, v in attach.CATALOGUE.items()}
    skin_index = {skin: i for i, skin in enumerate(all_skins())}
    soldiers = {nid(name): {"gun": nid(spec["gun"]), "skins": [skin_index[k] for k in spec["skins"]]}
                for name, spec in SOLDIERS.items()}
    data = {"guns": guns, "attachments": atts, "slots": attach.SLOT_ORDER, "soldiers": soldiers}
    js = ("// Generated by tools/gen/content.py from defs.py, attach.py, guns*.py and gunanims.py - do not edit.\n"
          "// guns: stats, animation timings (the cooldown lengths the 3D models listen for), slots and mounts.\n"
          "// attachments: name, slot, the guns each fits, its effects and the cooldown category that shows it.\n"
          "// soldiers: the gun each soldier type carries and the corpse skin of each of its uniforms.\n"
          f"export const GUN_DATA = {json.dumps(data, indent=2)};\n")
    (BP / "scripts" / "gundata.js").write_text(js, encoding="utf-8")
    lines = ["# Weapon attachments", "",
             "Generated by `tools/gen/content.py` from `tools/gen/attach.py`. Fit attachments with the **Gunsmith** "
             "(Field Radio > Gunsmith, or use an attachment item while it is in your inventory).", "",
             "## Effects", "",
             "Numbers multiply the gun's own value (0.7 = 30% less). `spread`: hip-fire spread; `ads`: spread while "
             "crouched (aiming); `vrec` / `hrec`: vertical / horizontal recoil; `velocity`: muzzle velocity (flatter "
             "and longer flight); `noise`: how loud; `reload`: reload time; `mag`: magazine size; `mag_add`: extra "
             "rounds; `zoom`: magnification while aiming; `nv`: night vision while aiming; `laser`: a laser dot; "
             "`light`: lights up where you aim; `flash`: hides the muzzle flash; `bipod`: much steadier when crouched.", "",
             "| Attachment | Slot | Effects | Fits |", "| --- | --- | --- | --- |"]
    for a, (name, slot, gs, mods) in attach.CATALOGUE.items():
        eff = ", ".join(f"{k} ×{v}" if isinstance(v, float) else f"{k} {v}" for k, v in mods.items())
        lines.append(f"| {name} | {slot} | {eff} | {', '.join(names[x] for x in gs)} |")
    lines += ["", "## How a fitted attachment shows on the gun", "",
              "- Every attachment is modelled onto every gun it fits, in a bone `a_<id>` under the gun's `att_<slot>` "
              "bone (under `mag` for magazines), placed from the gun's mount.",
              "- Each attachment item has a cooldown category `frontline_att_<id>`. While a gun with attachments is "
              "in hand, the scripts keep the categories of its fitted attachments running.",
              "- The gun's looping animation `animation.frontline.gun.<gun>.attachments` scales `a_<id>` to full size while "
              "`q.cooldown_time_remaining('frontline_att_<id>') > 0` (and to nothing otherwise), and scales the factory "
              "part `def_<slot>` to nothing while any attachment of that slot shows. Guns draw with the standard item "
              "render controller, so the gun always draws even if that query is not answered.",
              "- Cooldowns are the holder's own, so the attachments are drawn for the player holding the gun.", "",
              "## Mounts per gun", "",
              "Positions are in the gun's own frame and units (quarter pixels): `f` forward along the barrel, `u` up, "
              "`s` to the gun's left; `length` is the usable rail length.", ""]
    for k in gunanims.TIMING:
        lines += [f"### {names[k]} ({CALIBER[GUN_STATS[k]['ammo']]})", "", "| Slot | f | u | s | rail length |",
                  "| --- | --- | --- | --- | --- |"]
        for slot, m in built[k].mounts.items():
            lines.append(f"| {slot} | {m['f']} | {m['u']} | {m['s']} | {m['length'] or '-'} |")
        fits = [attach.CATALOGUE[a][0] for a in getattr(built[k], "attachments", [])]
        lines += ["", f"Takes: {', '.join(fits) if fits else 'none'}.", ""]
    (ROOT / "docs" / "attachments.md").write_text("\n".join(lines), encoding="utf-8")


# ====================================================================== blocks

def blocks():
    for name, display, sound, seconds, colour, light, render in BLOCKS:
        LANG.append(f"tile.{nid(name)}.name={display}")
        BLOCK_SOUNDS[nid(name)] = {"sound": sound}
        TERRAIN[f"{NS}_{name}"] = f"textures/blocks/{NS}/{name}"
        comps = {
            "minecraft:material_instances": {"*": {"texture": f"{NS}_{name}", "render_method": render}},
            "minecraft:map_color": colour,
        }
        if name in M.BLOCK_MODELS:
            model = M.BLOCK_MODELS[name]()
            save_model(model, "blocks")
            path = RP / "textures" / "blocks" / NS / f"{name}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            model.hd().save(path)
            comps["minecraft:geometry"] = f"geometry.{NS}.block_{name}"
        else:
            comps["minecraft:geometry"] = "minecraft:geometry.full_block"
        if seconds < 0:
            comps["minecraft:destructible_by_mining"] = False
            comps["minecraft:destructible_by_explosion"] = False
        else:
            comps["minecraft:destructible_by_mining"] = {"seconds_to_destroy": seconds}
            comps["minecraft:destructible_by_explosion"] = {"explosion_resistance": 8 if name == "sandbags" else 3}
        if light:
            comps["minecraft:light_emission"] = light
        if name == "barbed_wire":
            comps["minecraft:collision_box"] = False
            comps["minecraft:light_dampening"] = 0
        if name in ("ammo_crate", "spawn_beacon"):
            comps["minecraft:light_dampening"] = 0
            comps["minecraft:collision_box"] = {"origin": [-7, 0, -7], "size": [14, 12 if name == "ammo_crate" else 8, 14]}
            comps["minecraft:selection_box"] = {"origin": [-7, 0, -7], "size": [14, 12 if name == "ammo_crate" else 16, 14]}
        if name.startswith("flag_"):
            comps["minecraft:loot"] = "loot_tables/empty.json"
        write(BP / "blocks" / f"{name}.json", {
            "format_version": "1.21.80",
            "minecraft:block": {"description": {"identifier": nid(name), "menu_category": {"category": "construction"}},
                                "components": comps},
        })
    write(RP / "textures" / "terrain_texture.json", {
        "resource_pack_name": NS, "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4,
        "texture_data": {k: {"textures": v} for k, v in sorted(TERRAIN.items())},
    })
    write(RP / "blocks.json", {"format_version": "1.21.40", **BLOCK_SOUNDS})


# ====================================================================== soldiers

def team_test(team, subject="other"):
    return {"any_of": [{"test": "is_family", "subject": subject, "value": team},
                       {"test": "has_tag", "subject": subject, "value": f"fl_team_{team}"}]}


def soldier(name, spec):
    team, enemy = spec["team"], other(spec["team"])
    w = AI_WEAPONS[spec["weapon"]]
    skins = spec["skins"]
    LANG.append(f"entity.{nid(name)}.name={spec['name']}")
    LANG.append(f"item.spawn_egg.entity.{nid(name)}.name=Spawn {spec['name']}")
    groups = {
        f"{NS}:despawnable": {"minecraft:despawn": {"despawn_from_distance": {"min_distance": 64, "max_distance": 128}}},
    }
    for i in range(len(skins)):
        groups[f"{NS}:skin_{i}"] = {"minecraft:variant": {"value": i}}
    comps = {
        "minecraft:type_family": {"family": ["frontline_soldier", team, f"{NS}_{team}", "human", "mob"]},
        "minecraft:health": {"value": spec["hp"], "max": spec["hp"]},
        "minecraft:collision_box": {"width": 0.6, "height": 1.9},
        "minecraft:movement": {"value": spec["speed"]},
        "minecraft:movement.basic": {},
        "minecraft:jump.static": {},
        "minecraft:can_climb": {},
        "minecraft:navigation.walk": {"can_path_over_water": True, "avoid_water": True, "can_pass_doors": True,
                                      "can_open_doors": True, "avoid_damage_blocks": True, "can_walk": True},
        "minecraft:physics": {},
        "minecraft:pushable": {"is_pushable": True, "is_pushable_by_piston": True},
        "minecraft:nameable": {},
        "minecraft:follow_range": {"value": 64, "max": 64},
        "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0},
        "minecraft:experience_reward": {"on_death": f"query.last_hit_by_player ? {spec['xp']} : 0"},
        "minecraft:loot": {"table": f"loot_tables/entities/{name}.json"},
        "minecraft:is_hidden_when_invisible": {},
        "minecraft:conditional_bandwidth_optimization": {},
        "minecraft:hurt_on_condition": {"damage_conditions": [{
            "filters": {"test": "in_lava", "subject": "self", "operator": "==", "value": True},
            "cause": "lava", "damage_per_tick": 4}]},
        # Teammates' bullets (and players of the same team) never hurt.
        "minecraft:damage_sensor": {"triggers": [
            {"on_damage": {"filters": team_test(team)}, "deals_damage": False},
            {"cause": "fall", "damage_multiplier": 0.5},
        ]},
        "minecraft:shooter": {"def": nid(w["projectile"])},
        "minecraft:behavior.float": {"priority": 0},
        "minecraft:behavior.hurt_by_target": {"priority": 1, "entity_types": {"filters": {"none_of": [
            {"test": "is_family", "subject": "other", "value": team},
            {"test": "has_tag", "subject": "other", "value": f"fl_team_{team}"}]}}},
        "minecraft:behavior.nearest_attackable_target": {
            "priority": 2, "must_see": True, "must_see_forget_duration": 4.0, "reselect_targets": True,
            "scan_interval": 10, "within_radius": 56.0,
            "entity_types": [
                {"filters": team_test(enemy), "max_dist": 56},
                {"filters": {"all_of": [{"test": "is_family", "subject": "other", "value": "monster"}]}, "max_dist": 20},
            ],
        },
        "minecraft:behavior.ranged_attack": {
            "priority": 3, "attack_interval_min": w["interval"][0], "attack_interval_max": w["interval"][1],
            "attack_radius": w["radius"], "burst_shots": w["burst"], "burst_interval": 0.12,
            "speed_multiplier": 1.0, "target_in_sight_time": 0.4,
        },
        # With nobody to fight, soldiers advance on the nearest flag their team does not hold.
        "minecraft:behavior.move_to_block": {
            "priority": 5, "tick_interval": 60, "search_range": 40, "search_height": 6, "goal_radius": 3.5,
            "stay_duration": 30, "speed_multiplier": 1.0, "start_chance": 1.0, "target_selection_method": "nearest",
            "target_blocks": [nid("flag_neutral"), nid(f"flag_{enemy}")],
        },
        "minecraft:behavior.random_stroll": {"priority": 7, "speed_multiplier": 0.8},
        "minecraft:behavior.look_at_player": {"priority": 8, "look_distance": 8, "probability": 0.02},
        "minecraft:behavior.random_look_around": {"priority": 9},
    }
    spawned = [{"add": {"component_groups": [f"{NS}:despawnable"]}}]
    if len(skins) > 1:
        spawned.append({"randomize": [{"weight": 1, "add": {"component_groups": [f"{NS}:skin_{i}"]}}
                                      for i in range(len(skins))]})
    else:
        spawned[0]["add"]["component_groups"].append(f"{NS}:skin_0")
    write(BP / "entities" / f"{name}.json", {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {"identifier": nid(name), "is_spawnable": True, "is_summonable": True,
                            "is_experimental": False},
            "component_groups": groups,
            "components": comps,
            "events": {
                "minecraft:entity_spawned": {"sequence": spawned},
                f"{NS}:make_persistent": {"remove": {"component_groups": [f"{NS}:despawnable"]}},
            },
        },
    })

    # ---- client: one geometry and texture per uniform
    geos, texs = {}, {}
    for i, skin in enumerate(skins):
        model = M.soldier(name, skin)
        save_model(model, "entity", f"soldiers/{skin}")
        geos[f"skin_{i}"] = f"geometry.{NS}.soldier_{skin}"
        texs[f"skin_{i}"] = f"textures/models/soldiers/{skin}"
    write(RP / "entity" / f"{name}.entity.json", {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": nid(name),
            "materials": {"default": "entity_alphatest"},
            "textures": texs,
            "geometry": geos,
            "animations": {
                "look": f"animation.{NS}.soldier.look", "walk": f"animation.{NS}.soldier.walk",
                "aim": f"animation.{NS}.soldier.aim", "gun": f"animation.{NS}.soldier.gun",
            },
            "scripts": {"animate": ["look", "walk", "aim", "gun"]},
            "render_controllers": [f"controller.render.{NS}.{name}"],
            "spawn_egg": {"base_color": spec["egg"][0], "overlay_color": spec["egg"][1]},
        }},
    })
    RENDER_CONTROLLERS[f"controller.render.{NS}.{name}"] = {
        "arrays": {
            "textures": {"Array.skins": [f"Texture.skin_{i}" for i in range(len(skins))]},
            "geometries": {"Array.geos": [f"Geometry.skin_{i}" for i in range(len(skins))]},
        },
        "geometry": "Array.geos[query.variant]",
        "materials": [{"*": "Material.default"}],
        "textures": ["Array.skins[query.variant]"],
    }
    SOUND_ENTITIES[nid(name)] = {"volume": 1.0, "pitch": [0.9, 1.1],
                                 "events": {"hurt": "game.player.hurt", "death": "game.player.die",
                                            "step": {"sound": "step.gravel", "volume": 0.2, "pitch": 1.0}}}


def all_skins():
    """Every soldier uniform, in a fixed order (the corpse's skin property indexes it)."""
    return [skin for spec in SOLDIERS.values() for skin in spec["skins"]]


def corpse():
    """The body of a fallen soldier: takes the soldier's place, falls with a death animation (backward or forward),
    lies a while and sinks into the ground. The scripts set its uniform and which way it falls."""
    skins = all_skins()
    LANG.append(f"entity.{nid('corpse')}.name=Fallen Soldier")
    write(BP / "entities" / "corpse.json", {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {"identifier": nid("corpse"), "is_spawnable": False, "is_summonable": True, "is_experimental": False,
                            "properties": {
                                f"{NS}:skin": {"type": "int", "range": [0, len(skins) - 1], "default": 0, "client_sync": True},
                                f"{NS}:fall": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}},
            "component_groups": {f"{NS}:gone": {"minecraft:instant_despawn": {}}},
            "components": {
                "minecraft:type_family": {"family": ["frontline_corpse", "inanimate"]},
                "minecraft:health": {"value": 20, "max": 20},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                "minecraft:collision_box": {"width": 0.6, "height": 0.3},
                "minecraft:physics": {},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": True},
                "minecraft:knockback_resistance": {"value": 1.0},
                "minecraft:fire_immune": True,
                "minecraft:conditional_bandwidth_optimization": {},
                "minecraft:timer": {"looping": False, "time": 12.0, "time_down_event": {"event": f"{NS}:despawn"}},
            },
            "events": {f"{NS}:despawn": {"add": {"component_groups": [f"{NS}:gone"]}}},
        },
    })
    write(RP / "entity" / "corpse.entity.json", {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": nid("corpse"),
            "materials": {"default": "entity_alphatest"},
            "textures": {f"skin_{i}": f"textures/models/soldiers/{k}" for i, k in enumerate(skins)},
            "geometry": {f"skin_{i}": f"geometry.{NS}.soldier_{k}" for i, k in enumerate(skins)},
            "animations": {"back": f"animation.{NS}.corpse.fall_back", "front": f"animation.{NS}.corpse.fall_forward",
                           "sink": f"animation.{NS}.corpse.sink"},
            "scripts": {"animate": [{"back": f"q.property('{NS}:fall') == 0"}, {"front": f"q.property('{NS}:fall') == 1"}, "sink"]},
            "render_controllers": [f"controller.render.{NS}.corpse"],
        }},
    })
    prop = f"q.property('{NS}:skin')"
    RENDER_CONTROLLERS[f"controller.render.{NS}.corpse"] = {
        "arrays": {
            "textures": {"Array.skins": [f"Texture.skin_{i}" for i in range(len(skins))]},
            "geometries": {"Array.geos": [f"Geometry.skin_{i}" for i in range(len(skins))]},
        },
        "geometry": f"Array.geos[{prop}]",
        "materials": [{"*": "Material.default"}],
        "textures": [f"Array.skins[{prop}]"],
        "part_visibility": [{"*": True}, {"gun": False}],  # the gun was dropped
    }

    def keys(frames):
        return {f"{t:.2f}".rstrip("0").rstrip(".") if t else "0.0": list(v) for t, v in frames}

    # Shot and falling on its back: a jolt, knees buckle, arms fly up, it tips backward and lands with a bounce.
    ANIMATIONS[f"animation.{NS}.corpse.fall_back"] = {"loop": "hold_on_last_frame", "animation_length": 1.0, "bones": {
        "root": {"rotation": keys([(0, (0, 0, 0)), (0.18, (8, 0, 0)), (0.45, (-35, 0, 4)), (0.75, (-92, 0, 6)),
                                   (0.86, (-85, 0, 5)), (1.0, (-90, 0, 5))]),
                 "position": keys([(0, (0, 0, 0)), (0.18, (0, -1.5, 0)), (0.45, (0, -1, 0)), (0.75, (0, 2.4, 0)),
                                   (0.86, (0, 3.2, 0)), (1.0, (0, 2.2, 0))])},
        "body": {"rotation": keys([(0, (0, 0, 0)), (0.18, (14, 0, 0)), (0.75, (0, 0, 0))])},
        "head": {"rotation": keys([(0, (0, 0, 0)), (0.18, (28, 0, 0)), (0.6, (-25, 10, 0)), (1.0, (-8, 32, 0))])},
        "rightArm": {"rotation": keys([(0, (0, 0, 0)), (0.25, (-75, 0, 20)), (0.6, (-120, 0, 40)), (1.0, (-20, 0, 70))])},
        "leftArm": {"rotation": keys([(0, (0, 0, 0)), (0.25, (-55, 0, -18)), (0.6, (-100, 0, -35)), (1.0, (-30, 0, -55))])},
        "rightLeg": {"rotation": keys([(0, (0, 0, 0)), (0.25, (-28, 0, 0)), (0.6, (-40, 0, 6)), (1.0, (-6, 0, 12))])},
        "leftLeg": {"rotation": keys([(0, (0, 0, 0)), (0.25, (12, 0, 0)), (0.6, (-10, 0, -4)), (1.0, (2, 0, -9))])},
    }}
    # Falling forward onto the face: doubles over, drops to the knees and topples, arms out to break the fall.
    ANIMATIONS[f"animation.{NS}.corpse.fall_forward"] = {"loop": "hold_on_last_frame", "animation_length": 1.0, "bones": {
        "root": {"rotation": keys([(0, (0, 0, 0)), (0.15, (-7, 0, 0)), (0.45, (30, 0, -3)), (0.78, (92, 0, -5)),
                                   (0.88, (86, 0, -4)), (1.0, (90, 0, -4))]),
                 "position": keys([(0, (0, 0, 0)), (0.3, (0, -3, 0)), (0.5, (0, -3.5, 0)), (0.78, (0, 2.4, 0)),
                                   (0.88, (0, 3.0, 0)), (1.0, (0, 2.2, 0))])},
        "body": {"rotation": keys([(0, (0, 0, 0)), (0.3, (25, 0, 0)), (0.78, (5, 0, 0)), (1.0, (0, 0, 0))])},
        "head": {"rotation": keys([(0, (0, 0, 0)), (0.3, (20, 0, 0)), (0.78, (-30, -20, 0)), (1.0, (-25, -40, 0))])},
        "rightArm": {"rotation": keys([(0, (0, 0, 0)), (0.3, (-20, 0, 10)), (0.7, (-150, 0, 30)), (1.0, (-165, 0, 40))])},
        "leftArm": {"rotation": keys([(0, (0, 0, 0)), (0.3, (-10, 0, -10)), (0.7, (-60, 0, -40)), (1.0, (-15, 0, -60))])},
        "rightLeg": {"rotation": keys([(0, (0, 0, 0)), (0.3, (-50, 0, 0)), (0.78, (-10, 0, 8)), (1.0, (0, 0, 10))])},
        "leftLeg": {"rotation": keys([(0, (0, 0, 0)), (0.3, (-40, 0, 0)), (0.78, (5, 0, -6)), (1.0, (8, 0, -8))])},
    }}
    # Near the end of its time the body sinks into the ground before it is gone.
    ANIMATIONS[f"animation.{NS}.corpse.sink"] = {"loop": True, "bones": {
        "root": {"position": [0, "math.max(0.0, q.life_time - 10.5) * -10.0", 0]}}}


def soldier_animations():
    speed = "math.clamp(query.modified_move_speed, 0.0, 1.0)"
    swing = "math.cos(query.modified_distance_moved * 38.17)"
    swing_b = "math.cos(query.modified_distance_moved * 38.17 + 180.0)"
    ANIMATIONS[f"animation.{NS}.soldier.look"] = {"loop": True, "bones": {
        "head": {"rotation": ["query.target_x_rotation", "query.target_y_rotation", 0.0]}}}
    ANIMATIONS[f"animation.{NS}.soldier.walk"] = {"loop": True, "bones": {
        "rightLeg": {"rotation": [f"{swing} * 45.0 * {speed}", 0.0, 0.0]},
        "leftLeg": {"rotation": [f"{swing_b} * 45.0 * {speed}", 0.0, 0.0]},
        "body": {"rotation": [f"4.0 * {speed}", 0.0, 0.0]},
    }}
    right, left = POSES["rifle"]["rightArm"], POSES["rifle"]["leftArm"]
    ANIMATIONS[f"animation.{NS}.soldier.aim"] = {"loop": True, "bones": {
        "rightArm": {"rotation": [f"{-18 + right[0]} + query.target_x_rotation", right[1], right[2]]},
        "leftArm": {"rotation": [f"{left[0]} + query.target_x_rotation", left[1], left[2]]},
    }}
    ANIMATIONS[f"animation.{NS}.soldier.gun"] = {"loop": True, "bones": {"gun": {"scale": H.SCALE}}}


# ====================================================================== projectiles

def projectiles(models):
    for name, (power, gravity, damage) in PROJECTILES.items():
        on_hit = {"remove_on_hit": {}}
        if damage:
            on_hit["impact_damage"] = {"damage": damage, "knockback": False, "semi_random_diff_damage": False,
                                       "destroy_on_hit": True}
        if name in ("frag_grenade", "smoke_grenade"):
            on_hit = {"stick_in_ground": {"shake_time": 0.0}}
        proj = {"on_hit": on_hit, "power": power or 0.8, "gravity": gravity, "inertia": 1.0, "liquid_inertia": 0.6,
                "anchor": 1, "offset": [0, -0.1, 0], "uncertainty_base": 5.0 if name == "bullet" else 2.0,
                "uncertainty_multiplier": 0.0, "reflect_on_hurt": False}
        lifetime = 6 if name in ("frag_grenade", "smoke_grenade") else 4
        write(BP / "entities" / f"{name}.json", {
            "format_version": "1.21.0",
            "minecraft:entity": {
                "description": {"identifier": nid(name), "is_spawnable": False, "is_summonable": True,
                                "is_experimental": False, "runtime_identifier": "minecraft:snowball"},
                "component_groups": {f"{NS}:expire": {"minecraft:instant_despawn": {}}},
                "components": {
                    "minecraft:collision_box": {"width": 0.25, "height": 0.25},
                    "minecraft:projectile": proj,
                    "minecraft:physics": {},
                    "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": True},
                    "minecraft:conditional_bandwidth_optimization": {
                        "default_values": {"max_optimized_distance": 80.0, "max_dropped_ticks": 7,
                                           "use_motion_prediction_hints": True}},
                    "minecraft:timer": {"looping": False, "time": lifetime, "time_down_event": {"event": f"{NS}:expire"}},
                },
                "events": {f"{NS}:expire": {"add": {"component_groups": [f"{NS}:expire"]}}},
            },
        })
        model = models[name]
        save_model(model, "entity", f"projectiles/{name}")
        anims = {}
        animate = []
        if model.bones[0].scale != 1.0:
            anims["scale"] = f"animation.{NS}.projectile.small"
            animate.append("scale")
        write(RP / "entity" / f"{name}.entity.json", {
            "format_version": "1.10.0",
            "minecraft:client_entity": {"description": {
                "identifier": nid(name),
                "materials": {"default": "entity_emissive_alpha" if name in ("bullet", "sniper_bullet") else "entity_alphatest"},
                "textures": {"default": f"textures/models/projectiles/{name}"},
                "geometry": {"default": f"geometry.{NS}.projectile_{name}"},
                **({"animations": anims, "scripts": {"animate": animate}} if animate else {}),
                "render_controllers": [f"controller.render.{NS}.single"],
            }},
        })
    ANIMATIONS[f"animation.{NS}.projectile.small"] = {"loop": True, "bones": {"root": {"scale": H.SCALE}}}
    RENDER_CONTROLLERS[f"controller.render.{NS}.single"] = {
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]}


# ====================================================================== vehicles

def vehicles():
    for name, spec in VEHICLES.items():
        LANG.append(f"entity.{nid(name)}.name={spec['name']}")
        LANG.append(f"item.spawn_egg.entity.{nid(name)}.name=Spawn {spec['name']}")
        build = M.build_jeep if name == "jeep" else M.build_tank
        nato, red = build("nato"), build("redfang")
        nato.pack()
        red.pack()
        assert same_layout(nato, red), name
        save_model(nato, "entity", f"vehicles/{name}_nato")
        path = RP / "textures" / "models" / "vehicles" / f"{name}_redfang.png"
        red.hd().save(path)
        tank = name == "tank"
        seats = ([{"position": [0.0, 1.25, -0.1]}, {"position": [-0.5, 1.05, 0.95]}] if tank else
                 [{"position": [0.34, 0.5, 0.36]}, {"position": [-0.34, 0.5, 0.36]},
                  {"position": [0.36, 0.55, -0.72]}, {"position": [-0.36, 0.55, -0.72]}])
        comps = {
            "minecraft:type_family": {"family": ["frontline_vehicle", name, "inanimate"]},
            "minecraft:health": {"value": spec["hp"], "max": spec["hp"]},
            "minecraft:collision_box": {"width": 2.6 if tank else 1.9, "height": 1.7 if tank else 1.5},
            "minecraft:movement": {"value": spec["speed"]},
            "minecraft:movement.basic": {},
            "minecraft:input_ground_controlled": {},
            "minecraft:rideable": {"seat_count": spec["seats"], "family_types": ["player"],
                                   "interact_text": "action.interact.ride.horse", "pull_in_entities": False,
                                   "crouching_skip_interact": True, "seats": seats},
            "minecraft:variable_max_auto_step": {"base_value": 1.0625, "controlled_value": 1.0625,
                                                 "jump_prevented_value": 1.0625},
            "minecraft:physics": {},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:persistent": {},
            "minecraft:nameable": {},
            "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0, "breathes_water": True},
            "minecraft:damage_sensor": {"triggers": [
                {"cause": "fall", "deals_damage": False},
                {"cause": "suffocation", "deals_damage": False},
                {"cause": "projectile", "damage_multiplier": 0.04 if tank else 0.15},
                {"cause": "entity_attack", "damage_multiplier": 0.05 if tank else 0.2},
                {"cause": "fire", "damage_multiplier": 0.1 if tank else 0.5},
                {"cause": "fire_tick", "damage_multiplier": 0.1 if tank else 0.5},
            ]},
            "minecraft:is_hidden_when_invisible": {},
        }
        if tank:
            comps["minecraft:fire_immune"] = {}
        description = {"identifier": nid(name), "is_spawnable": True, "is_summonable": True, "is_experimental": False,
                       "properties": {f"{NS}:team": {"type": "int", "range": [0, 1], "default": 0, "client_sync": True}}}
        if tank:
            description["properties"][f"{NS}:turret"] = {"type": "float", "range": [-180.0, 180.0], "default": 0.0,
                                                         "client_sync": True}
            description["properties"][f"{NS}:pitch"] = {"type": "float", "range": [-25.0, 25.0], "default": 0.0,
                                                        "client_sync": True}
        write(BP / "entities" / f"{name}.json", {
            "format_version": "1.21.0",
            "minecraft:entity": {"description": description, "component_groups": {}, "components": comps,
                                 "events": {
                                     f"{NS}:paint_nato": {"set_property": {f"{NS}:team": 0}},
                                     f"{NS}:paint_redfang": {"set_property": {f"{NS}:team": 1}},
                                 }},
        })
        anims = {"wheels": f"animation.{NS}.{name}.wheels"} if not tank else {"turret": f"animation.{NS}.tank.turret"}
        write(RP / "entity" / f"{name}.entity.json", {
            "format_version": "1.10.0",
            "minecraft:client_entity": {"description": {
                "identifier": nid(name),
                "materials": {"default": "entity_alphatest"},
                "textures": {"nato": f"textures/models/vehicles/{name}_nato",
                             "redfang": f"textures/models/vehicles/{name}_redfang"},
                "geometry": {"default": f"geometry.{NS}.vehicle_{name}"},
                "animations": anims,
                "scripts": {"animate": list(anims)},
                "render_controllers": [f"controller.render.{NS}.{name}"],
                "spawn_egg": {"base_color": spec["egg"][0], "overlay_color": spec["egg"][1]},
            }},
        })
        controller = {
            "arrays": {"textures": {"Array.paint": ["Texture.nato", "Texture.redfang"]}},
            "geometry": "Geometry.default",
            "materials": [{"*": "Material.default"}],
            "textures": [f"Array.paint[query.property('{NS}:team')]"],
        }
        if not tank:
            controller["part_visibility"] = [{"*": True},
                                             {"mounted_gun": f"query.property('{NS}:team') == 1"},
                                             {"antenna": f"query.property('{NS}:team') == 0"}]
        RENDER_CONTROLLERS[f"controller.render.{NS}.{name}"] = controller
        SOUND_ENTITIES[nid(name)] = {"volume": 1.0, "pitch": [0.9, 1.0],
                                     "events": {"hurt": "random.anvil_land", "death": "random.explode",
                                                "step": {"sound": f"{NS}.engine", "volume": 0.5, "pitch": 1.0}}}
    spin = "query.modified_distance_moved * 150.0"
    ANIMATIONS[f"animation.{NS}.jeep.wheels"] = {"loop": True, "bones": {
        **{w: {"rotation": [spin, 0, 0]} for w in ("wheel_rl", "wheel_rr")},
        **{w: {"rotation": [spin, "math.clamp(query.target_y_rotation, -30, 30) * 0.5", 0]} for w in ("wheel_fl", "wheel_fr")},
    }}
    ANIMATIONS[f"animation.{NS}.tank.turret"] = {"loop": True, "bones": {
        "turret": {"rotation": [0, f"query.property('{NS}:turret')", 0]},
        "barrel": {"rotation": [f"query.property('{NS}:pitch')", 0, 0]},
    }}


# ====================================================================== the capture flag

def capture_flag():
    LANG.append(f"entity.{nid('capture_flag')}.name=Capture Point")
    models = {o: M.capture_flag(o) for o in M.FLAG_SKINS}
    for mo in models.values():
        mo.pack()
    first = models["flag_neutral"]
    for o, mo in models.items():
        assert same_layout(first, mo), o
        save_model(mo, "entity", f"flags/{o}")
    write(BP / "entities" / "capture_flag.json", {
        "format_version": "1.21.0",
        "minecraft:entity": {
            "description": {"identifier": nid("capture_flag"), "is_spawnable": False, "is_summonable": True,
                            "is_experimental": False, "properties": {
                                f"{NS}:owner": {"type": "int", "range": [0, 2], "default": 0, "client_sync": True},
                                f"{NS}:raise": {"type": "float", "range": [0.0, 1.0], "default": 0.0, "client_sync": True}}},
            "components": {
                "minecraft:type_family": {"family": ["frontline_flag", "inanimate"]},
                "minecraft:collision_box": {"width": 0.4, "height": 3.0},
                "minecraft:health": {"value": 1000, "max": 1000},
                "minecraft:damage_sensor": {"triggers": [{"cause": "all", "deals_damage": False}]},
                "minecraft:physics": {"has_gravity": False},
                "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
                "minecraft:knockback_resistance": {"value": 1.0},
                "minecraft:persistent": {},
                "minecraft:fire_immune": {},
                "minecraft:nameable": {"always_show": True, "allow_name_tag_renaming": False},
            },
        },
    })
    write(RP / "entity" / "capture_flag.entity.json", {
        "format_version": "1.10.0",
        "minecraft:client_entity": {"description": {
            "identifier": nid("capture_flag"),
            "materials": {"default": "entity_alphatest"},
            "textures": {o: f"textures/models/flags/{o}" for o in M.FLAG_SKINS},
            "geometry": {"default": f"geometry.{NS}.capture_flag"},
            "animations": {"wave": f"animation.{NS}.flag.wave", "raise": f"animation.{NS}.flag.raise"},
            "scripts": {"animate": ["wave", "raise"]},
            "render_controllers": [f"controller.render.{NS}.capture_flag"],
        }},
    })
    RENDER_CONTROLLERS[f"controller.render.{NS}.capture_flag"] = {
        "arrays": {"textures": {"Array.owner": [f"Texture.{o}" for o in M.FLAG_SKINS]}},
        "geometry": "Geometry.default", "materials": [{"*": "Material.default"}],
        "textures": [f"Array.owner[query.property('{NS}:owner')]"],
    }
    ANIMATIONS[f"animation.{NS}.flag.wave"] = {"loop": True, "bones": {
        f"cloth{i}": {"rotation": [0, f"math.sin(query.life_time * 220.0 - {i * 70}) * {6 + i * 5}", 0]} for i in range(4)}}
    ANIMATIONS[f"animation.{NS}.flag.raise"] = {"loop": True, "bones": {
        "cloth": {"position": [0, f"(query.property('{NS}:raise') - 1.0) * 22.0", 0]}}}


# ====================================================================== loot, recipes, particles

def entry(name, weight=1, lo=1, hi=1):
    e = {"type": "item", "name": name if ":" in name else nid(name), "weight": weight}
    if (lo, hi) != (1, 1):
        e["functions"] = [{"function": "set_count", "count": {"min": lo, "max": hi}}]
    return e


def loot_tables():
    # Soldiers drop their gear through the scripts (soldiers.js): the gun they carried, its ammunition, attachments.
    for name in SOLDIERS:
        write(BP / "loot_tables" / "entities" / f"{name}.json", {"pools": []})
    write(BP / "loot_tables" / "empty.json", {"pools": []})


def ingredient(name):
    if name.startswith("#"):
        return {"tag": name[1:]}
    return {"item": name if ":" in name else nid(name)}


def shaped(ident, pattern, key, result, count=1):
    write(BP / "recipes" / f"{ident}.json", {"format_version": "1.20.10", "minecraft:recipe_shaped": {
        "description": {"identifier": nid(ident)}, "tags": ["crafting_table"], "pattern": pattern,
        "key": {k: ingredient(v) for k, v in key.items()}, "unlock": {"context": "AlwaysUnlocked"},
        "result": {"item": nid(result), "count": count}}})


def shapeless(ident, ingredients, result, count=1):
    write(BP / "recipes" / f"{ident}.json", {"format_version": "1.20.10", "minecraft:recipe_shapeless": {
        "description": {"identifier": nid(ident)}, "tags": ["crafting_table"],
        "ingredients": [ingredient(i) for i in ingredients], "unlock": {"context": "AlwaysUnlocked"},
        "result": {"item": nid(result), "count": count}}})


_I, _N, _C, _R = "minecraft:iron_ingot", "minecraft:iron_nugget", "minecraft:copper_ingot", "minecraft:redstone"
_GL, _GP, _BS = "minecraft:glass", "minecraft:glass_pane", "minecraft:blackstone"
_SPY, _WOOL, _LEATHER = "minecraft:spyglass", "#minecraft:wool", "minecraft:leather"
ATTACHMENT_RECIPES = {  # id: (pattern, key, count)
    "reflex_sight": (["NGN"], {"N": _N, "G": _GP}, 1),
    "red_dot": (["NGN", " R "], {"N": _I, "G": _GP, "R": _R}, 1),
    "holo_sight": (["IGI", "NRN"], {"I": _I, "G": _GP, "N": _N, "R": _R}, 1),
    "holo_magnifier": (["IGI", "NRS"], {"I": _I, "G": _GP, "N": _N, "R": _R, "S": _SPY}, 1),
    "prism_2x": (["GIG", " R "], {"I": _I, "G": _GL, "R": _R}, 1),
    "combat_4x": (["IGS"], {"I": _I, "G": _GL, "S": _SPY}, 1),
    "variable_6x": (["IGS", " C "], {"I": _I, "G": _GL, "S": _SPY, "C": _C}, 1),
    "marksman_8x": (["ISS", " C "], {"I": _I, "S": _SPY, "C": _C}, 1),
    "sniper_12x": (["SSS", "ICI"], {"I": _I, "S": _SPY, "C": _C}, 1),
    "night_vision_4x": (["IGS", "ERE"], {"I": _I, "G": _GL, "S": _SPY, "R": _R, "E": "minecraft:emerald"}, 1),
    "pistol_suppressor": (["IWI"], {"I": _I, "W": _WOOL}, 1),
    "rifle_suppressor": (["IWI", "IWI"], {"I": _I, "W": _WOOL}, 1),
    "compensator": ([" N ", "NIN"], {"I": _I, "N": _N}, 1),
    "muzzle_brake": (["NIN", "NIN"], {"I": _I, "N": _N}, 1),
    "flash_hider": (["N N", " I "], {"I": _I, "N": _N}, 1),
    "full_choke": (["NIN"], {"I": _I, "N": _N}, 1),
    "cylinder_choke": (["NCN"], {"C": _C, "N": _N}, 1),
    "vertical_grip": (["I", "B", "B"], {"I": _I, "B": _BS}, 1),
    "angled_grip": (["IB", " B"], {"I": _I, "B": _BS}, 1),
    "stubby_grip": (["I", "B"], {"I": _I, "B": _BS}, 1),
    "handstop": (["IN"], {"I": _I, "N": _N}, 1),
    "bipod": (["NIN", "I I"], {"I": _I, "N": _N}, 1),
    "laser_sight": (["IRG"], {"I": _I, "R": _R, "G": _GP}, 1),
    "flashlight": (["ITG"], {"I": _I, "T": "minecraft:torch", "G": _GP}, 1),
    "laser_light": (["ITG", " R "], {"I": _I, "T": "minecraft:torch", "G": _GP, "R": _R}, 1),
    "heavy_stock": (["BBI", "B  "], {"I": _I, "B": _BS}, 1),
    "light_stock": (["NNI", "N  "], {"I": _I, "N": _N}, 1),
    "precision_stock": (["LBI", "B  "], {"I": _I, "B": _BS, "L": _LEATHER}, 1),
    "extended_mag": (["I", "I", "I"], {"I": _I}, 1),
    "drum_mag": (["III", "I I", "III"], {"I": _I}, 1),
    "quick_mag": (["I", "I", "L"], {"I": _I, "L": _LEATHER}, 1),
    "extended_tube": (["III"], {"I": _I}, 1),
    "big_box": (["III", "LIL"], {"I": _I, "L": _LEATHER}, 1),
}


def recipes():
    I, G, N, C, R = "minecraft:iron_ingot", "minecraft:gunpowder", "minecraft:iron_nugget", "minecraft:copper_ingot", "minecraft:redstone"
    P, W, B = "minecraft:blackstone", "#minecraft:planks", "minecraft:iron_block"
    shaped("glock17", ["II", " P"], {"I": I, "P": P}, "glock17")
    shaped("m1911", ["II", " W"], {"I": I, "W": W}, "m1911")
    shaped("mp5", ["III", " PI"], {"I": I, "P": P}, "mp5")
    shaped("ump45", ["III", "PPI"], {"I": I, "P": P}, "ump45")
    shaped("m4a1", ["III", "CPI", " C "], {"I": I, "P": P, "C": C}, "m4a1")
    shaped("ak47", ["III", "WPI", " C "], {"I": I, "P": P, "C": C, "W": W}, "ak47")
    shaped("m249", ["III", "BPI", "BC "], {"I": I, "P": P, "C": C, "B": B}, "m249")
    shaped("rem870", ["III", "WPI"], {"I": I, "P": P, "W": W}, "rem870")
    shaped("awm", ["GII", "IPI", " P "], {"I": I, "P": P, "G": "minecraft:spyglass"}, "awm")
    shaped("svd", ["GII", "IPI", " W "], {"I": I, "P": P, "G": "minecraft:spyglass", "W": W}, "svd")
    shaped("carl_gustaf", ["III", "TPT", "CCC"], {"I": I, "P": P, "T": "minecraft:tnt", "C": C}, "carl_gustaf")
    shaped("rpg7", ["III", "TPT", "WWW"], {"I": I, "P": P, "T": "minecraft:tnt", "W": W}, "rpg7")
    shaped("deagle", ["IIC", " P"], {"I": I, "P": P, "C": C}, "deagle")
    shaped("p90", ["PPP", "IPI"], {"I": I, "P": P}, "p90")
    shaped("scar_h", ["III", "CPC", " C "], {"I": I, "P": P, "C": C}, "scar_h")
    shaped("barrett", ["GII", "BPB", " P "], {"I": I, "P": P, "B": B, "G": "minecraft:spyglass"}, "barrett")
    shaped("pkm", ["III", "BPI", "WC "], {"I": I, "P": P, "C": C, "B": B, "W": W}, "pkm")
    shapeless("ammo_50ae", [G, G, C, N, N], "ammo_50ae", 7)
    shapeless("ammo_57", [G, C, C, N], "ammo_57", 50)
    shapeless("ammo_762x51", [G, G, C, C, I], "ammo_762x51", 20)
    shapeless("ammo_50bmg", [G, G, G, C, C, I], "ammo_50bmg", 5)
    shapeless("ammo_9mm", [G, C, N], "ammo_9mm", 17)
    shapeless("ammo_45acp", [G, C, N, N], "ammo_45acp", 14)
    shapeless("ammo_556", [G, G, C, N], "ammo_556", 30)
    shapeless("ammo_762x39", [G, G, C, I], "ammo_762x39", 30)
    shapeless("ammo_762x54r", [G, G, C, C, N], "ammo_762x54r", 10)
    shapeless("ammo_338", [G, G, G, C, I], "ammo_338", 5)
    shapeless("ammo_12g", [G, "minecraft:paper", N, N], "ammo_12g", 8)
    shapeless("ammo_84mm", ["minecraft:tnt", I, G, C], "ammo_84mm", 1)
    shapeless("ammo_pg7v", ["minecraft:tnt", I, G], "ammo_pg7v", 1)
    for att_id, recipe in ATTACHMENT_RECIPES.items():
        pattern, key, count = recipe
        shaped(att_id, pattern, key, att_id, count)
    shaped("frag_grenade", [" N ", "NGN", " N "], {"N": I, "G": G}, "frag_grenade", 2)
    shaped("smoke_grenade", [" N ", "NCN", " N "], {"N": I, "C": "minecraft:coal"}, "smoke_grenade", 2)
    shaped("combat_knife", ["I", "S"], {"I": I, "S": "minecraft:stick"}, "combat_knife")
    shapeless("medkit", ["minecraft:paper", "minecraft:string", "minecraft:glistering_melon_slice", "minecraft:red_dye"], "medkit", 2)
    shapeless("ammo_box", ["minecraft:chest", G, I], "ammo_box", 2)
    shaped("repair_tool", ["I ", "RI", " C"], {"I": I, "R": R, "C": C}, "repair_tool")
    shaped("binoculars", ["GIG"], {"G": "minecraft:glass_pane", "I": I}, "binoculars")
    shaped("field_radio", [" R", "IC", "II"], {"I": I, "R": R, "C": C}, "field_radio")
    shapeless("field_ration", ["minecraft:bread", "minecraft:cooked_beef", "minecraft:paper"], "field_ration", 2)
    shaped("sandbags", ["SSS", "SPS", "SSS"], {"S": "minecraft:sand", "P": "minecraft:paper"}, "sandbags", 4)
    shaped("barbed_wire", ["N N", " I ", "N N"], {"N": N, "I": I}, "barbed_wire", 3)
    shaped("ammo_crate", ["WGW", "WIW"], {"W": "#minecraft:planks", "G": G, "I": I}, "ammo_crate")
    shaped("spawn_beacon", [" R ", "ICI", "III"], {"I": I, "R": R, "C": "minecraft:compass"}, "spawn_beacon")
    shaped("jeep_kit", ["I I", "BCB", "O O"], {"I": I, "B": "minecraft:iron_block", "C": "minecraft:chest",
                                              "O": "minecraft:coal_block"}, "jeep_kit")
    shaped("tank_kit", ["BTB", "BRB", "OOO"], {"B": "minecraft:iron_block", "T": "minecraft:tnt",
                                              "R": "minecraft:redstone_block", "O": "minecraft:obsidian"}, "tank_kit")


def particle(name, comps, material="particles_alpha"):
    write(RP / "particles" / f"{name}.json", {"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": nid(name),
                        "basic_render_parameters": {"material": material, "texture": "textures/particle/particles"}},
        "components": comps}})


def dot(size, colour):
    return {"minecraft:particle_appearance_billboard": {
                "size": [size, size], "facing_camera_mode": "rotate_xyz",
                "uv": {"texture_width": 128, "texture_height": 128, "uv": [0, 0], "uv_size": [8, 8]}},
            "minecraft:particle_appearance_tinting": {"color": colour}}


def burst(count, speed, life, gravity, size, colour, radius=0.15):
    return {"minecraft:emitter_rate_instant": {"num_particles": count},
            "minecraft:emitter_lifetime_once": {"active_time": 0.1},
            "minecraft:emitter_shape_sphere": {"radius": radius, "direction": "outwards"},
            "minecraft:particle_lifetime_expression": {"max_lifetime": f"{life} + variable.particle_random_1 * {life / 2}"},
            "minecraft:particle_initial_speed": speed,
            "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, -gravity, 0], "linear_drag_coefficient": 1.5},
            "minecraft:particle_motion_collision": {"collision_radius": 0.05, "coefficient_of_restitution": 0.1,
                                                    "collision_drag": 6},
            **dot(size, colour)}


def smoke(count, rise, life, size_from, size_to, colour, radius=0.3, speed=0.4):
    return {"minecraft:emitter_rate_instant": {"num_particles": count},
            "minecraft:emitter_lifetime_once": {"active_time": 0.1},
            "minecraft:emitter_shape_sphere": {"radius": radius, "direction": "outwards"},
            "minecraft:particle_lifetime_expression": {"max_lifetime": f"{life} + variable.particle_random_1 * {life / 3}"},
            "minecraft:particle_initial_speed": speed,
            "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, rise, 0], "linear_drag_coefficient": 1.2},
            "minecraft:particle_appearance_billboard": {
                "size": [f"{size_from} + variable.particle_age / variable.particle_lifetime * {size_to - size_from}"] * 2,
                "facing_camera_mode": "rotate_xyz",
                "uv": {"texture_width": 128, "texture_height": 128,
                       "flipbook": {"base_UV": [56, 0], "size_UV": [8, 8], "step_UV": [-8, 0], "frames_per_second": 8,
                                    "max_frame": 8, "stretch_to_lifetime": True, "loop": False}}},
            "minecraft:particle_appearance_tinting": {"color": colour}}


def particles():
    particle("muzzle_flash", {"minecraft:emitter_rate_instant": {"num_particles": 3},
                              "minecraft:emitter_lifetime_once": {"active_time": 0.05},
                              "minecraft:emitter_shape_sphere": {"radius": 0.05, "direction": "outwards"},
                              "minecraft:particle_lifetime_expression": {"max_lifetime": 0.06},
                              "minecraft:particle_initial_speed": 0.5,
                              **dot(0.22, [1.0, 0.82, 0.4, 1.0])}, "particles_add")
    particle("tracer", {"minecraft:emitter_rate_instant": {"num_particles": 1},
                        "minecraft:emitter_lifetime_once": {"active_time": 0.05}, "minecraft:emitter_shape_point": {},
                        "minecraft:particle_lifetime_expression": {"max_lifetime": 0.07},
                        **dot(0.07, [1.0, 0.92, 0.6, 1.0])}, "particles_add")
    particle("gun_smoke", smoke(3, 0.7, 0.8, 0.1, 0.3, [0.8, 0.8, 0.8, 0.5]))
    particle("blood", burst(10, 2.5, 0.45, 14, 0.07, [0.55, 0.03, 0.03, 1.0]))
    particle("sparks", burst(9, 5.0, 0.25, 10, 0.05, [1.0, 0.78, 0.35, 1.0]), "particles_add")
    particle("impact_dust", burst(8, 2.0, 0.5, 6, 0.09, [0.55, 0.5, 0.42, 1.0]))
    particle("smoke_screen", smoke(10, 0.15, 9.0, 1.2, 3.4, [0.82, 0.82, 0.8, 0.92], radius=1.8, speed=1.2))
    particle("rocket_trail", smoke(2, 0.3, 1.0, 0.15, 0.6, [0.7, 0.7, 0.7, 0.7], radius=0.05, speed=0.1))
    particle("heal", burst(8, 1.0, 0.8, -1.5, 0.09, [0.4, 1.0, 0.45, 1.0], radius=0.5), "particles_add")
    particle("spot", {"minecraft:emitter_rate_instant": {"num_particles": 1},
                      "minecraft:emitter_lifetime_once": {"active_time": 0.05}, "minecraft:emitter_shape_point": {},
                      "minecraft:particle_lifetime_expression": {"max_lifetime": 1.05},
                      **dot(0.35, [1.0, 0.2, 0.15, 1.0])}, "particles_add")
    particle("capture_nato", burst(14, 1.5, 1.0, -2, 0.12, [0.3, 0.55, 1.0, 1.0], radius=1.0), "particles_add")
    particle("capture_redfang", burst(14, 1.5, 1.0, -2, 0.12, [1.0, 0.3, 0.25, 1.0], radius=1.0), "particles_add")
    particle("laser_dot", {"minecraft:emitter_rate_instant": {"num_particles": 1},
                           "minecraft:emitter_lifetime_once": {"active_time": 0.05}, "minecraft:emitter_shape_point": {},
                           "minecraft:particle_lifetime_expression": {"max_lifetime": 0.11},
                           **dot(0.09, [1.0, 0.08, 0.05, 1.0])}, "particles_add")
    particle("laser_beam", {"minecraft:emitter_rate_instant": {"num_particles": 1},
                            "minecraft:emitter_lifetime_once": {"active_time": 0.05}, "minecraft:emitter_shape_point": {},
                            "minecraft:particle_lifetime_expression": {"max_lifetime": 0.11},
                            **dot(0.025, [1.0, 0.1, 0.08, 0.7])}, "particles_add")
    particle("bullet_trail", {"minecraft:emitter_rate_instant": {"num_particles": 1},
                              "minecraft:emitter_lifetime_once": {"active_time": 0.05}, "minecraft:emitter_shape_point": {},
                              "minecraft:particle_lifetime_expression": {"max_lifetime": 0.12},
                              **dot(0.045, [1.0, 0.9, 0.55, 0.9])}, "particles_add")
    particle("wreck_fire", smoke(4, 1.5, 2.5, 0.4, 1.6, [0.25, 0.22, 0.2, 0.9], radius=0.8))


# ====================================================================== texts

def texts():
    lines = [f"pack.name={TITLE}", f"pack.description={DESCRIPTION}", "action.interact.mount=Get in"]
    body = "\n".join(lines + sorted(set(LANG))) + "\n"
    for pack in (BP, RP):
        (pack / "texts").mkdir(parents=True, exist_ok=True)
        (pack / "texts" / "en_US.lang").write_text(body, encoding="utf-8")
        write(pack / "texts" / "languages.json", ["en_US"])


GENERATED = [BP / d for d in ("entities", "items", "blocks", "recipes", "loot_tables", "spawn_rules", "texts")]
GENERATED += [RP / d for d in ("entity", "models", "animations", "render_controllers", "particles", "texts",
                               "attachables", "textures/models")]


def main():
    for folder in GENERATED:
        if folder.exists():
            shutil.rmtree(folder)
    manifests()
    items()
    attachables()
    blocks()
    for name, spec in SOLDIERS.items():
        soldier(name, spec)
    soldier_animations()
    corpse()
    projectiles(M.projectile_models())
    vehicles()
    capture_flag()
    loot_tables()
    recipes()
    particles()
    write(RP / "animations" / f"{NS}.animation.json", {"format_version": "1.10.0", "animations": ANIMATIONS})
    write(RP / "render_controllers" / f"{NS}.render_controllers.json",
          {"format_version": "1.8.0", "render_controllers": RENDER_CONTROLLERS})
    write(RP / "sounds.json", {"entity_sounds": {"entities": SOUND_ENTITIES}})
    texts()
    print(f"content: {len(ITEM_TEXTURES)} items, {len(SOLDIERS)} soldiers, {len(VEHICLES)} vehicles, "
          f"{len(PROJECTILES)} projectiles, {len(BLOCK_SOUNDS)} blocks")


if __name__ == "__main__":
    main()
