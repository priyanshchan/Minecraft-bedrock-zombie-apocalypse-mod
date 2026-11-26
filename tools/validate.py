#!/usr/bin/env python3
"""Checks that both packs hang together: every file parses, and every id, texture, model, animation,
render controller, sound, particle, loot table and language key that something refers to exists.

Usage:  python3 tools/validate.py      (exit code 1 on problems)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
BP, RP = ROOT / "behavior_pack", ROOT / "resource_pack"
NS = "frontline"
errors: list[str] = []


def err(msg):
    errors.append(msg)


def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        err(f"{path.relative_to(ROOT)}: does not parse ({e})")
        return {}


def jsons(folder):
    return sorted(folder.rglob("*.json")) if folder.exists() else []


def png(path_no_ext):
    return (RP / f"{path_no_ext}.png").exists()


# ------------------------------------------------------------------ parse everything
for f in jsons(BP) + jsons(RP):
    load(f)
if errors:
    print("\n".join(errors))
    sys.exit(1)

lang = {}
for line in (RP / "texts" / "en_US.lang").read_text(encoding="utf-8").splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        lang[k] = v

# ------------------------------------------------------------------ manifests
bpm, rpm = load(BP / "manifest.json"), load(RP / "manifest.json")
uuids = [bpm["header"]["uuid"], rpm["header"]["uuid"]] + [m["uuid"] for m in bpm["modules"] + rpm["modules"]]
if len(set(uuids)) != len(uuids):
    err("manifests: UUIDs are not unique")
if not any(d.get("uuid") == rpm["header"]["uuid"] for d in bpm["dependencies"]):
    err("BP manifest does not depend on the RP")
if not (BP / "pack_icon.png").exists() or not (RP / "pack_icon.png").exists():
    err("pack icons missing")

# ------------------------------------------------------------------ resource indexes
item_tex = load(RP / "textures" / "item_texture.json")["texture_data"]
terrain = load(RP / "textures" / "terrain_texture.json")["texture_data"]
for table, name in ((item_tex, "item_texture"), (terrain, "terrain_texture")):
    for k, v in table.items():
        if not png(v["textures"]):
            err(f"{name}: {k} -> {v['textures']}.png missing")

geometries = {}
for f in jsons(RP / "models"):
    for g in load(f).get("minecraft:geometry", []):
        ident = g["description"]["identifier"]
        geometries[ident] = g
animations = {}
for f in jsons(RP / "animations"):
    animations.update(load(f).get("animations", {}))
controllers = {}
for f in jsons(RP / "render_controllers"):
    controllers.update(load(f).get("render_controllers", {}))
particles = {load(f)["particle_effect"]["description"]["identifier"] for f in jsons(RP / "particles")}
sound_defs = load(RP / "sounds" / "sound_definitions.json")["sound_definitions"]
for k, v in sound_defs.items():
    for s in v["sounds"]:
        name = s["name"] if isinstance(s, dict) else s
        if not (RP / f"{name}.ogg").exists():
            err(f"sound {k}: {name}.ogg missing")


def bones_of(geo_id):
    return {b["name"] for b in geometries.get(geo_id, {}).get("bones", [])}


def check_geometry_texture(geo_id, tex_path, where):
    g = geometries.get(geo_id)
    if not g:
        err(f"{where}: geometry {geo_id} missing")
        return
    if not png(tex_path):
        err(f"{where}: texture {tex_path}.png missing")
        return
    w, h = g["description"]["texture_width"], g["description"]["texture_height"]
    with Image.open(RP / f"{tex_path}.png") as im:
        if im.width * h != im.height * w:
            err(f"{where}: {tex_path}.png is {im.size}, geometry {geo_id} expects ratio {w}x{h}")


def check_anim_bones(anim_ids, geo_ids, where):
    bones = set().union(*(bones_of(g) for g in geo_ids)) if geo_ids else set()
    for a in anim_ids:
        if a not in animations:
            err(f"{where}: animation {a} missing")
            continue
        for bone in animations[a].get("bones", {}):
            if bone not in bones:
                err(f"{where}: animation {a} moves bone '{bone}' that its geometry lacks")


# ------------------------------------------------------------------ behaviour pack ids
items = {}
for f in jsons(BP / "items"):
    d = load(f)["minecraft:item"]
    items[d["description"]["identifier"]] = d["components"]
blocks = {}
for f in jsons(BP / "blocks"):
    d = load(f)["minecraft:block"]
    blocks[d["description"]["identifier"]] = d
entities = {}
for f in jsons(BP / "entities"):
    d = load(f)["minecraft:entity"]
    entities[d["description"]["identifier"]] = d

for ident, comps in items.items():
    icon = comps["minecraft:icon"]["textures"]["default"]
    if icon not in item_tex:
        err(f"item {ident}: icon {icon} not in item_texture.json")
    name = comps.get("minecraft:display_name", {}).get("value")
    if name and name not in lang:
        err(f"item {ident}: no language entry {name}")
    for key in ("minecraft:entity_placer",):
        if key in comps and comps[key]["entity"] not in entities:
            err(f"item {ident}: places unknown entity {comps[key]['entity']}")
    if "minecraft:projectile" in comps and comps["minecraft:projectile"]["projectile_entity"] not in entities:
        err(f"item {ident}: throws unknown entity")

for ident, d in blocks.items():
    if f"tile.{ident}.name" not in lang:
        err(f"block {ident}: no language entry")
    comps = d["components"]
    for inst in comps.get("minecraft:material_instances", {}).values():
        if inst["texture"] not in terrain:
            err(f"block {ident}: texture {inst['texture']} not in terrain_texture.json")
    geo = comps.get("minecraft:geometry")
    if isinstance(geo, str) and geo.startswith(f"geometry.{NS}") and geo not in geometries:
        err(f"block {ident}: geometry {geo} missing")
    loot = comps.get("minecraft:loot")
    if loot and not (BP / loot).exists():
        err(f"block {ident}: loot table {loot} missing")

for ident, d in entities.items():
    comps = d["components"]
    for c in list(comps.values()) + [g for grp in d.get("component_groups", {}).values() for g in grp.values()]:
        pass
    loot = comps.get("minecraft:loot", {}).get("table")
    if loot and not (BP / loot).exists():
        err(f"entity {ident}: loot table {loot} missing")
    shooter = comps.get("minecraft:shooter", {}).get("def")
    if shooter and shooter not in entities:
        err(f"entity {ident}: shoots unknown {shooter}")
    mtb = comps.get("minecraft:behavior.move_to_block", {})
    for t in mtb.get("target_blocks", []):
        if t not in blocks:
            err(f"entity {ident}: moves to unknown block {t}")
    events = d.get("events", {})
    groups = d.get("component_groups", {})
    for ev in events.values():
        for part in [ev] + ev.get("sequence", []) + ev.get("randomize", []) + [r for s in ev.get("sequence", []) for r in s.get("randomize", [])]:
            for g in part.get("add", {}).get("component_groups", []) + part.get("remove", {}).get("component_groups", []):
                if g not in groups:
                    err(f"entity {ident}: event uses unknown component group {g}")
    if d["description"].get("is_spawnable") and f"item.spawn_egg.entity.{ident}.name" not in lang:
        err(f"entity {ident}: no spawn egg name")

# ------------------------------------------------------------------ client entities and attachables
client = {}
for f in jsons(RP / "entity"):
    d = load(f)["minecraft:client_entity"]["description"]
    client[d["identifier"]] = d
for ident in entities:
    if ident not in client:
        err(f"entity {ident}: no client entity in the resource pack")
for ident, d in client.items():
    if ident not in entities:
        err(f"client entity {ident}: no behaviour entity")
    geos = list(d.get("geometry", {}).values())
    for key, tex in d.get("textures", {}).items():
        if not png(tex):
            err(f"client entity {ident}: texture {tex}.png missing")
    for g in geos:
        if g not in geometries:
            err(f"client entity {ident}: geometry {g} missing")
    if len(geos) == len(d.get("textures", {})):
        for g, t in zip(geos, d["textures"].values()):
            check_geometry_texture(g, t, f"client entity {ident}")
    else:
        for t in d.get("textures", {}).values():
            check_geometry_texture(geos[0], t, f"client entity {ident}")
    check_anim_bones(list(d.get("animations", {}).values()), geos, f"client entity {ident}")
    for rc in d.get("render_controllers", []):
        name = rc if isinstance(rc, str) else next(iter(rc))
        if name not in controllers:
            err(f"client entity {ident}: render controller {name} missing")
            continue
        text = json.dumps(controllers[name])
        for ref in re.findall(r"Texture\.(\w+)", text):
            if ref not in d.get("textures", {}):
                err(f"render controller {name}: Texture.{ref} not defined by {ident}")
        for ref in re.findall(r"Geometry\.(\w+)", text):
            if ref not in d.get("geometry", {}):
                err(f"render controller {name}: Geometry.{ref} not defined by {ident}")
        for part in controllers[name].get("part_visibility", []):
            for bone in part:
                if bone != "*" and not any(bone in bones_of(g) for g in geos):
                    err(f"render controller {name}: part_visibility bone {bone} not in geometry")

for f in jsons(RP / "attachables"):
    d = load(f)["minecraft:attachable"]["description"]
    ident = d["identifier"]
    if ident not in items:
        err(f"attachable {ident}: not an item")
    g = d["geometry"]["default"]
    check_geometry_texture(g, d["textures"]["default"], f"attachable {ident}")
    check_anim_bones(list(d["animations"].values()), [g], f"attachable {ident}")

# ------------------------------------------------------------------ recipes and loot
known_items = set(items) | set(blocks)
for f in jsons(BP / "recipes"):
    text = f.read_text(encoding="utf-8")
    for ref in re.findall(rf'"({NS}:[a-z_]+)"', text):
        if ref not in known_items and not ref.endswith(f.stem) and ref != f"{NS}:{f.stem}":
            err(f"recipe {f.stem}: unknown item {ref}")
for f in jsons(BP / "loot_tables"):
    for ref in re.findall(rf'"({NS}:[a-z_]+)"', f.read_text(encoding="utf-8")):
        if ref not in known_items:
            err(f"loot table {f.name}: unknown item {ref}")

# ------------------------------------------------------------------ sounds.json
for ent, spec in load(RP / "sounds.json").get("entity_sounds", {}).get("entities", {}).items():
    for ev, snd in spec.get("events", {}).items():
        name = snd if isinstance(snd, str) else snd.get("sound")
        if name.startswith(f"{NS}.") and name not in sound_defs:
            err(f"sounds.json {ent}.{ev}: {name} not defined")

# ------------------------------------------------------------------ scripts
ids_known = known_items | set(entities) | particles
for d in entities.values():
    ids_known |= set(d.get("events", {}))  # entity events the scripts trigger
    ids_known |= set(d["description"].get("properties", {}))  # entity properties the scripts set
for f in sorted((BP / "scripts").glob("*.js")):
    text = f.read_text(encoding="utf-8")
    for ref in set(re.findall(rf'[`"\']({NS}:[a-z_]+)[`"\']', text)):
        if ref not in ids_known:
            err(f"{f.name}: unknown id {ref}")
    for ref in set(re.findall(r'id\("([a-z_]+)"\)', text)):
        if f"{NS}:{ref}" not in ids_known:
            err(f"{f.name}: id(\"{ref}\") is not defined")
    for ref in set(re.findall(r'\$\{NS\}:([a-z_]+)`', text)):
        if ref.endswith("_"):  # a type prefix such as nato_
            continue
        if f"{NS}:{ref}" not in ids_known:
            err(f"{f.name}: ${{NS}}:{ref} is not defined")
    for ref in set(re.findall(r'\$\{NS\}\.([a-z_]+)`', text)):
        if f"{NS}.{ref}" not in sound_defs:
            err(f"{f.name}: sound {NS}.{ref} is not defined")
    for ref in set(re.findall(r'animation\.\$\{NS\}\.([a-z_.]+)', text)):
        full = f"animation.{NS}.{ref}"
        if not ref.endswith(("_", ".")) and full not in animations:  # names built at run time end in _ or .
            err(f"{f.name}: animation {full} is not defined")
    for ref in set(re.findall(r'\$\{NS\}:capture_\$\{team\}', text)):
        pass

# ---- rules the game enforces that the cross-references above do not catch (found in the content log)
for f in sorted((RP / "models").rglob("*.json")):
    rel = f.relative_to(RP / "models").parts[0]
    if rel not in ("entity", "blocks"):
        err(f"{f}: models are only read from models/entity or models/blocks")
    for g in load(f).get("minecraft:geometry", []):
        names = [k for b in g.get("bones", []) for k in (b.get("locators") or {})]
        for n in set(names):
            if names.count(n) > 1:
                err(f"{f.name}: locator {n} appears {names.count(n)} times")
for f in sorted((BP / "recipes").glob("*.json")):
    pat = load(f).get("minecraft:recipe_shaped", {}).get("pattern", [])
    if len(pat) > 3 or any(len(r) > 3 for r in pat):
        err(f"{f.name}: a shaped recipe can be at most 3x3")
for f in sorted((RP / "entity").glob("*.json")):
    desc = load(f)["minecraft:client_entity"]["description"]
    for key in ("animations", "geometry", "textures", "materials"):
        if key in desc and not desc[key]:
            err(f"{f.name}: '{key}' is empty")
for name, v in load(RP / "sounds.json").get("entity_sounds", {}).get("entities", {}).items():
    if not v.get("events"):
        err(f"sounds.json: {name} has no sound events")

if errors:
    print(f"validate: {len(errors)} problem(s)")
    print("\n".join(sorted(set(errors))))
    sys.exit(1)
print(f"validate: OK ({len(items)} items, {len(blocks)} blocks, {len(entities)} entities, {len(geometries)} models, "
      f"{len(animations)} animations, {len(sound_defs)} sounds, {len(particles)} particles)")
