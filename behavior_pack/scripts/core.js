// Shared constants and helpers: teams, settings, vectors, safe wrappers.
import { GameMode, ItemStack, system, world } from "@minecraft/server";

export const NS = "frontline";
export const id = (/** @type {string} */ name) => `${NS}:${name}`;
export const TICKS = 20;

/** @typedef {"nato" | "redfang"} Team */

export const TEAMS = {
  nato: { key: "nato", name: "NATO", short: "NATO", color: "§9", wool: "minecraft:blue_wool", owner: 1 },
  redfang: { key: "redfang", name: "Red Fang", short: "RFNG", color: "§c", wool: "minecraft:red_wool", owner: 2 },
};
/** @type {Team[]} */
export const TEAM_KEYS = ["nato", "redfang"];

/** @param {Team} team @returns {Team} */
export const enemyOf = (team) => (team === "nato" ? "redfang" : "nato");

/** The team of a player (from its tag) or of a soldier (from its type). @param {import("@minecraft/server").Entity} entity @returns {Team | undefined} */
export function teamOf(entity) {
  try {
    if (entity.typeId === "minecraft:player") {
      if (entity.hasTag("fl_team_nato")) return "nato";
      if (entity.hasTag("fl_team_redfang")) return "redfang";
      return undefined;
    }
    if (entity.typeId.startsWith(`${NS}:nato_`)) return "nato";
    if (entity.typeId.startsWith(`${NS}:redfang_`)) return "redfang";
    if (entity.hasTag("fl_team_nato")) return "nato";
    if (entity.hasTag("fl_team_redfang")) return "redfang";
  } catch {
    // entity gone
  }
  return undefined;
}

/** @param {import("@minecraft/server").Entity} a @param {import("@minecraft/server").Entity} b */
export function sameTeam(a, b) {
  const ta = teamOf(a);
  return ta !== undefined && ta === teamOf(b);
}

export const isSoldier = (/** @type {import("@minecraft/server").Entity} */ e) =>
  e.typeId.startsWith(`${NS}:nato_`) || e.typeId.startsWith(`${NS}:redfang_`);
export const isVehicle = (/** @type {import("@minecraft/server").Entity} */ e) => e.typeId === id("jeep") || e.typeId === id("tank");

// ------------------------------------------------------------------ settings

export const DEFAULT_SETTINGS = {
  friendlyFire: false,
  destruction: false,
  patrols: true,
  patrolMinutes: 4,
  botDamage: 1,
  hud: true,
  malfunctions: true,
};

/** @type {typeof DEFAULT_SETTINGS | undefined} */
let settingsCache;

/** @returns {typeof DEFAULT_SETTINGS} */
export function settings() {
  if (!settingsCache) {
    let stored = {};
    try {
      const raw = world.getDynamicProperty("fl:settings");
      if (typeof raw === "string") stored = JSON.parse(raw);
    } catch {
      stored = {};
    }
    settingsCache = { ...DEFAULT_SETTINGS, ...stored };
  }
  return settingsCache;
}

/** @param {Partial<typeof DEFAULT_SETTINGS>} changes */
export function updateSettings(changes) {
  settingsCache = { ...settings(), ...changes };
  world.setDynamicProperty("fl:settings", JSON.stringify(settingsCache));
}

// ------------------------------------------------------------------ vectors

/** @typedef {import("@minecraft/server").Vector3} Vec */

/** @param {Vec} a @param {Vec} b */
export const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
/** @param {Vec} a @param {Vec} b */
export const sub = (a, b) => ({ x: a.x - b.x, y: a.y - b.y, z: a.z - b.z });
/** @param {Vec} a @param {number} k */
export const scale = (a, k) => ({ x: a.x * k, y: a.y * k, z: a.z * k });
/** @param {Vec} a @param {Vec} b */
export const dot = (a, b) => a.x * b.x + a.y * b.y + a.z * b.z;
/** @param {Vec} a */
export const length = (a) => Math.sqrt(dot(a, a));
/** @param {Vec} a @param {Vec} b */
export const distance = (a, b) => length(sub(a, b));
/** @param {Vec} a @param {Vec} b */
export const flatDistance = (a, b) => Math.hypot(a.x - b.x, a.z - b.z);
/** @param {Vec} a */
export const normalize = (a) => {
  const l = length(a) || 1;
  return scale(a, 1 / l);
};

/** A direction turned by a random angle of up to `degrees` (a cone of fire). @param {Vec} dir @param {number} degrees */
export function spread(dir, degrees) {
  if (degrees <= 0) return dir;
  const r = (degrees * Math.PI) / 180;
  const jitter = () => (Math.random() * 2 - 1) * Math.tan(r);
  return normalize({ x: dir.x + jitter(), y: dir.y + jitter() * 0.7, z: dir.z + jitter() });
}

/** Compass words for a direction from `from` to `to`. @param {Vec} from @param {Vec} to */
export function bearing(from, to) {
  const angle = (Math.atan2(to.x - from.x, -(to.z - from.z)) * 180) / Math.PI;
  const names = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"];
  return names[Math.round(((angle + 360) % 360) / 45) % 8];
}

// ------------------------------------------------------------------ safety

/** Runs `fn`, swallowing the errors the world throws for entities that left or chunks that unloaded. @template T @param {() => T} fn @returns {T | undefined} */
export function safe(fn) {
  try {
    return fn();
  } catch {
    return undefined;
  }
}

/** @param {import("@minecraft/server").Player} p */
export const isCreative = (p) => safe(() => p.getGameMode() === GameMode.Creative) ?? false;

/** @param {import("@minecraft/server").Player} player @param {string} text */
export function tell(player, text) {
  safe(() => player.sendMessage(text));
}

/** @param {string} text */
export function broadcast(text) {
  for (const p of world.getAllPlayers()) tell(p, text);
}

/** @param {import("@minecraft/server").Player} player @param {string} sound @param {number} [volume] @param {number} [pitch] */
export function cue(player, sound, volume = 1, pitch = 1) {
  safe(() => player.playSound(sound, { volume, pitch }));
}

/** @param {import("@minecraft/server").Dimension} dim @param {string} sound @param {Vec} at @param {number} [volume] @param {number} [pitch] */
export function sound(dim, sound, at, volume = 1, pitch = 1) {
  safe(() => dim.playSound(sound, at, { volume, pitch }));
}

/** @param {import("@minecraft/server").Dimension} dim @param {string} effect @param {Vec} at */
export function particle(dim, effect, at) {
  safe(() => dim.spawnParticle(effect, at));
}

/** Shakes the camera of a player (guns, explosions). @param {import("@minecraft/server").Player} player @param {number} intensity @param {number} seconds */
export function shake(player, intensity, seconds) {
  safe(() => player.runCommand(`camerashake add @s ${intensity.toFixed(2)} ${seconds.toFixed(2)} rotational`));
}

// ------------------------------------------------------------------ inventory

/** @param {import("@minecraft/server").Player} player */
export function container(player) {
  return player.getComponent("minecraft:inventory")?.container;
}

/** How many of an item a player carries. @param {import("@minecraft/server").Player} player @param {string} typeId */
export function countItem(player, typeId) {
  const inv = container(player);
  if (!inv) return 0;
  let n = 0;
  for (let i = 0; i < inv.size; i++) {
    const s = inv.getItem(i);
    if (s?.typeId === typeId) n += s.amount;
  }
  return n;
}

/** Removes up to `amount` of an item; returns how many were removed. @param {import("@minecraft/server").Player} player @param {string} typeId @param {number} amount */
export function takeItem(player, typeId, amount) {
  const inv = container(player);
  if (!inv) return 0;
  let left = amount;
  for (let i = 0; i < inv.size && left > 0; i++) {
    const s = inv.getItem(i);
    if (s?.typeId !== typeId) continue;
    const take = Math.min(left, s.amount);
    left -= take;
    if (take >= s.amount) inv.setItem(i, undefined);
    else {
      s.amount -= take;
      inv.setItem(i, s);
    }
  }
  return amount - left;
}

/** Gives items, dropping what does not fit at the player's feet. @param {import("@minecraft/server").Player} player @param {string} typeId @param {number} amount */
export function giveItem(player, typeId, amount) {
  const inv = container(player);
  let left = amount;
  while (left > 0) {
    const stack = new ItemStack(typeId, 1);
    const max = stack.maxAmount;
    const n = Math.min(left, max);
    stack.amount = n;
    left -= n;
    const rest = inv ? inv.addItem(stack) : stack;
    if (rest) safe(() => player.dimension.spawnItem(rest, player.location));
  }
}

/** Uses up one of the item in the main hand (not in creative). @param {import("@minecraft/server").Player} player */
export function consumeHeld(player) {
  if (isCreative(player)) return;
  const inv = container(player);
  if (!inv) return;
  const slot = player.selectedSlotIndex;
  const s = inv.getItem(slot);
  if (!s) return;
  if (s.amount <= 1) inv.setItem(slot, undefined);
  else {
    s.amount -= 1;
    inv.setItem(slot, s);
  }
}

/** The item in a player's main hand. @param {import("@minecraft/server").Player} player */
export function heldItem(player) {
  return safe(() => container(player)?.getItem(player.selectedSlotIndex));
}

/** Per-player cooldowns keyed by name: true when ready (and starts the cooldown). @type {Map<string, number>} */
const cooldowns = new Map();
/** @param {import("@minecraft/server").Entity} entity @param {string} key @param {number} ticks */
export function ready(entity, key, ticks) {
  const k = `${entity.id}:${key}`;
  const now = system.currentTick;
  if ((cooldowns.get(k) ?? 0) > now) return false;
  cooldowns.set(k, now + ticks);
  return true;
}

/** @param {import("@minecraft/server").Player} player @param {string} key @param {number} [fallback] */
export function getNumber(player, key, fallback = 0) {
  const v = safe(() => player.getDynamicProperty(key));
  return typeof v === "number" ? v : fallback;
}

/** @param {import("@minecraft/server").Player} player @param {string} key @param {number} delta */
export function addNumber(player, key, delta) {
  const v = getNumber(player, key) + delta;
  safe(() => player.setDynamicProperty(key, v));
  return v;
}

/** Players currently in the world, safely. */
export function players() {
  return safe(() => world.getAllPlayers()) ?? [];
}

// ------------------------------------------------------------------ messages on the action bar

/** Tick until which the HUD leaves a message on the action bar alone. @type {Map<string, number>} */
export const hudHold = new Map();

/** Shows a short message on the action bar and holds the HUD back for a moment. @param {import("@minecraft/server").Player} player @param {string} text @param {number} [ticks] */
export function notify(player, text, ticks = 40) {
  hudHold.set(player.id, system.currentTick + ticks);
  safe(() => player.onScreenDisplay.setActionBar(text));
}

// ------------------------------------------------------------------ using items

/**
 * Handlers for using one of the add-on's items. Called for item use in the air and for a tap or right-click on a
 * block (which the game reports as interacting with the block). `repeat` is true while the button is held on a
 * block; return true to stop later handlers.
 * @type {Array<(player: import("@minecraft/server").Player, item: import("@minecraft/server").ItemStack, repeat: boolean) => boolean | void>}
 */
const useHandlers = [];
/** @param {(player: import("@minecraft/server").Player, item: import("@minecraft/server").ItemStack, repeat: boolean) => boolean | void} fn */
export function onUse(fn) {
  useHandlers.push(fn);
}
/** @param {import("@minecraft/server").Player} player @param {import("@minecraft/server").ItemStack} item @param {boolean} repeat */
export function dispatchUse(player, item, repeat) {
  for (const fn of useHandlers) {
    if (safe(() => fn(player, item, repeat))) return;
  }
}
