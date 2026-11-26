// Class gear: medkits, ammo boxes, binoculars and spawn beacons; ammo crates and barbed wire.
import { system, world } from "@minecraft/server";
import {
  add, bearing, consumeHeld, countItem, cue, distance, giveItem, id, isSoldier, isVehicle, NS, particle, players, ready, safe,
  sameTeam, sound, TEAMS, teamOf, tell, notify, onUse,
} from "./core.js";
import { GUNS } from "./weapons.js";
import { award, displayName } from "./teams.js";

/** Teammates of a player within `radius` (including the player). @param {import("@minecraft/server").Player} player @param {number} radius */
function squadAround(player, radius) {
  return players().filter((p) => p === player || (sameTeam(p, player) && safe(() => p.dimension.id === player.dimension.id && distance(p.location, player.location) <= radius)));
}

/** @param {import("@minecraft/server").Entity} e @param {number} amount */
function heal(e, amount) {
  const hp = safe(() => e.getComponent("minecraft:health"));
  if (!hp || hp.currentValue <= 0) return false;
  if (hp.currentValue >= hp.effectiveMax) return false;
  hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + amount));
  return true;
}

/** Gives a player a magazine's worth of reserve ammo for every gun they carry. @param {import("@minecraft/server").Player} p @param {number} mags */
export function resupply(p, mags) {
  const seen = new Set();
  for (const [gunId, g] of Object.entries(GUNS)) {
    if (countItem(p, gunId) === 0 || seen.has(g.ammo)) continue;
    seen.add(g.ammo);
    giveItem(p, g.ammo, g.mag * mags);
  }
  if (countItem(p, id("frag_grenade")) < 2) giveItem(p, id("frag_grenade"), 1);
  return seen.size > 0;
}

/** Spawn beacons placed by players: one each. @returns {Record<string, {x: number, y: number, z: number, dim: string, team: string, name: string}>} */
export function beacons() {
  const raw = safe(() => world.getDynamicProperty("fl:beacons"));
  try {
    return typeof raw === "string" ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}
/** @param {Record<string, any>} b */
function saveBeacons(b) {
  safe(() => world.setDynamicProperty("fl:beacons", JSON.stringify(b)));
}

/** Enemies marked by binoculars: id -> until tick. @type {Map<import("@minecraft/server").Entity, number>} */
const spotted = new Map();

export function init() {
  onUse((player, itemStack, repeat) => {
    const type = itemStack.typeId;
    if (repeat || ![id("medkit"), id("ammo_box"), id("binoculars")].includes(type)) return false;

    if (type === id("medkit")) {
      if (!ready(player, "medkit", 30)) return;
      let healed = 0;
      for (const p of squadAround(player, 5)) {
        if (heal(p, p === player ? 8 : 6)) {
          healed++;
          safe(() => p.addEffect("regeneration", 100, { amplifier: 0, showParticles: false }));
          particle(p.dimension, `${NS}:heal`, add(p.location, { x: 0, y: 1, z: 0 }));
          if (p !== player) {
            tell(p, `§a${player.name} patched you up`);
            award(player, 20, "Heal");
          }
        }
      }
      if (healed === 0) {
        notify(player, "§7Nobody here needs healing");
        return true;
      }
      sound(player.dimension, `${NS}.heal`, player.location);
      consumeHeld(player);
    }

    if (type === id("ammo_box")) {
      if (!ready(player, "ammo_box", 40)) return;
      let given = 0;
      for (const p of squadAround(player, 6)) {
        if (resupply(p, 1)) {
          given++;
          if (p !== player) {
            tell(p, `§e${player.name} gave you ammo`);
            award(player, 20, "Resupply");
          }
        }
      }
      if (given === 0) {
        notify(player, "§7Nobody here carries a gun");
        return true;
      }
      sound(player.dimension, `${NS}.resupply`, player.location);
      consumeHeld(player);
    }

    if (type === id("binoculars")) {
      if (!ready(player, "spot", 20)) return;
      const hit = safe(() => player.getEntitiesFromViewDirection({ maxDistance: 160 }))?.find((h) => {
        const e = h.entity;
        return (isSoldier(e) || isVehicle(e) || e.typeId === "minecraft:player") && !sameTeam(e, player) && teamOf(e) !== undefined;
      });
      cue(player, `${NS}.radio`, 0.6, 1.3);
      if (!hit) {
        notify(player, "§7No enemy in sight");
        return true;
      }
      const e = hit.entity;
      spotted.set(e, system.currentTick + 200);
      safe(() => e.addTag("fl_spotted"));
      const d = Math.round(hit.distance);
      const where = bearing(player.location, e.location);
      for (const p of squadAround(player, 200)) tell(p, `§6[Spotted] §f${displayName(e)} §7- ${d} m ${where} of ${player.name}`);
      award(player, 10, "Spot");
    }
    return true;
  });

  world.afterEvents.playerPlaceBlock.subscribe(({ player, block }) => {
    if (block.typeId !== id("spawn_beacon")) return;
    const team = teamOf(player);
    if (!team) {
      tell(player, "§7Join a team first (Field Radio) to use a spawn beacon.");
      return;
    }
    const all = beacons();
    const old = all[player.id];
    if (old) {
      safe(() => {
        const b = world.getDimension(old.dim).getBlock(old);
        if (b?.typeId === id("spawn_beacon")) b.setType("minecraft:air");
      });
    }
    all[player.id] = { x: block.location.x, y: block.location.y, z: block.location.z, dim: block.dimension.id, team, name: player.name };
    saveBeacons(all);
    tell(player, `§bSpawn beacon set. ${TEAMS[team].color}${TEAMS[team].name}§b can deploy here.`);
    cue(player, `${NS}.radio`);
  });
  world.afterEvents.playerBreakBlock.subscribe(({ block, brokenBlockPermutation }) => {
    if (brokenBlockPermutation.type.id !== id("spawn_beacon")) return;
    const all = beacons();
    for (const [k, b] of Object.entries(all)) {
      if (b.x === block.location.x && b.y === block.location.y && b.z === block.location.z) delete all[k];
    }
    saveBeacons(all);
  });

  // Ammo crates resupply whoever uses them.
  world.beforeEvents.playerInteractWithBlock.subscribe((e) => {
    if (!e.isFirstEvent || e.block.typeId !== id("ammo_crate")) return;
    const player = e.player;
    system.run(() => {
      if (!ready(player, "crate", 300)) {
        notify(player, "§7The crate is being restocked...");
        return;
      }
      if (resupply(player, 2)) {
        sound(player.dimension, `${NS}.resupply`, player.location);
        notify(player, "§eResupplied");
      } else {
        notify(player, "§7You carry no gun to load");
      }
    });
  });

  // Barbed wire slows and cuts; spotted enemies are marked.
  system.runInterval(() => {
    for (const p of players()) {
      const feet = safe(() => p.dimension.getBlock(p.location)?.typeId);
      const body = safe(() => p.dimension.getBlock(add(p.location, { x: 0, y: 1, z: 0 }))?.typeId);
      if (feet === id("barbed_wire") || body === id("barbed_wire")) {
        safe(() => p.addEffect("slowness", 30, { amplifier: 3, showParticles: false }));
        if (system.currentTick % 20 === 0) safe(() => p.applyDamage(1));
      }
    }
    const now = system.currentTick;
    for (const [e, until] of spotted) {
      if (until < now || !safe(() => e.isValid)) {
        safe(() => e.removeTag("fl_spotted"));
        spotted.delete(e);
        continue;
      }
      if (now % 20 === 0) particle(e.dimension, `${NS}:spot`, add(e.location, { x: 0, y: 2.6, z: 0 }));
    }
  }, 10);
}
