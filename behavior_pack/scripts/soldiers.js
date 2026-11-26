// What happens when a soldier dies: the body falls with a death animation (a corpse entity takes the soldier's place,
// crumples forward or backward, lies a while and sinks away), and a soldier killed by a player drops the gun it
// carried (sometimes with attachments fitted), ammunition for it and now and then a spare attachment. Also keeps the
// world free of vanilla mobs (a setting): the battlefield belongs to the soldiers.
import { ItemStack, system, world } from "@minecraft/server";
import { id, isSoldier, safe, settings } from "./core.js";
import { choicesFor, fit, slotsOf } from "./attachments.js";
import { GUNS } from "./weapons.js";
import { onKill } from "./teams.js";
import { GUN_DATA } from "./gundata.js";

/** Per soldier type: the gun it carries and the corpse skin index of each of its uniforms. */
const SOLDIERS = /** @type {Record<string, {gun: string, skins: number[]}>} */ (/** @type {unknown} */ (GUN_DATA.soldiers));

/** @template T @param {T[]} list @returns {T | undefined} */
const pick = (list) => list[Math.floor(Math.random() * list.length)];

/** The gun a fallen soldier drops: the one it carried, with up to two attachments it had fitted. @param {string} gunId */
function droppedGun(gunId) {
  const item = new ItemStack(gunId, 1);
  const slots = slotsOf(gunId).filter((s) => s !== "magazine" || Math.random() < 0.3);
  const n = Math.random() < 0.35 ? 0 : Math.random() < 0.6 ? 1 : 2;
  for (let i = 0; i < n && slots.length; i++) {
    const slot = slots.splice(Math.floor(Math.random() * slots.length), 1)[0];
    const att = pick(choicesFor(gunId, slot));
    if (att) fit(item, slot, att.id);
  }
  return item;
}

/** Drops a fallen soldier's gear where it fell. @param {import("@minecraft/server").Entity} dead */
function dropGear(dead) {
  const spec = SOLDIERS[dead.typeId];
  const gun = spec ? GUNS[spec.gun] : undefined;
  const dim = dead.dimension;
  const at = { ...dead.location, y: dead.location.y + 0.6 };
  if (!spec || !gun) return;
  /** @type {ItemStack[]} */
  const items = [droppedGun(spec.gun)];
  const ammo = new ItemStack(gun.ammo, 1);
  ammo.amount = Math.max(1, Math.min(ammo.maxAmount, Math.round(gun.mag * (gun.mag <= 2 ? 2 : 1 + Math.random()))));
  items.push(ammo);
  if (Math.random() < 0.35) {
    const slot = pick(slotsOf(spec.gun));
    const att = slot ? pick(choicesFor(spec.gun, slot)) : undefined;
    if (att) items.push(new ItemStack(att.id, 1));
  }
  if (Math.random() < 0.2) items.push(new ItemStack(id("medkit"), 1));
  if (Math.random() < 0.25) items.push(new ItemStack(id("field_ration"), 1));
  for (const it of items) safe(() => dim.spawnItem(it, at));
}

/** A body that falls with a death animation where the soldier stood. @param {import("@minecraft/server").Entity} dead */
function fallBody(dead) {
  const spec = SOLDIERS[dead.typeId];
  if (!spec) return;
  const dim = dead.dimension;
  const at = { ...dead.location };
  const rot = safe(() => dead.getRotation()) ?? { x: 0, y: 0 };
  const variant = safe(() => dead.getComponent("minecraft:variant")?.value) ?? 0;
  const skin = spec.skins[Math.min(spec.skins.length - 1, Math.max(0, variant))] ?? spec.skins[0];
  const body = safe(() => dim.spawnEntity(id("corpse"), at));
  if (!body) return;
  safe(() => body.setProperty(id("skin"), skin));
  safe(() => body.setProperty(id("fall"), Math.random() < 0.5 ? 0 : 1));
  safe(() => body.setRotation({ x: 0, y: rot.y }));
}

// ------------------------------------------------------------------ vanilla mobs

const KEEP = new Set(["minecraft:player", "minecraft:armor_stand", "minecraft:ender_dragon", "minecraft:npc", "minecraft:agent"]);

/** Removes a vanilla mob unless vanilla mobs are allowed. Pets (tamed) and name-tagged mobs are spared.
 * @param {import("@minecraft/server").Entity} e */
function clearVanilla(e) {
  if (settings().vanillaMobs) return;
  const type = safe(() => e.typeId);
  if (!type || !type.startsWith("minecraft:") || KEEP.has(type)) return;
  if (!safe(() => e.matches({ families: ["mob"] }))) return;
  if (safe(() => e.getComponent("minecraft:is_tamed")) || safe(() => e.nameTag)) return;
  safe(() => e.remove());
}

/** Clears the vanilla mobs already in the loaded world (when the setting is turned off, and on start). */
export function sweepVanilla() {
  if (settings().vanillaMobs) return;
  for (const dimId of ["minecraft:overworld", "minecraft:nether", "minecraft:the_end"]) {
    const ents = safe(() => world.getDimension(dimId).getEntities({ families: ["mob"] })) ?? [];
    for (const e of ents) clearVanilla(e);
  }
}

export function init() {
  onKill.push((dead, killer) => {
    if (!isSoldier(dead)) return;
    const byPlayer = killer?.typeId === "minecraft:player";
    // the soldier's own body is taken away a tick later (after the battle has counted the death) and replaced
    system.run(() => {
      if (byPlayer) safe(() => dropGear(dead));
      safe(() => fallBody(dead));
      safe(() => dead.remove());
    });
  });
  world.afterEvents.entitySpawn.subscribe(({ entity }) => clearVanilla(entity));
  world.afterEvents.entityLoad.subscribe(({ entity }) => clearVanilla(entity));
  system.runTimeout(sweepVanilla, 40);
}
