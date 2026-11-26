// Conquest: a line of capture points between two headquarters, tickets, AI soldiers on both sides and vehicles.
import { BlockVolume, DisplaySlotId, system, world } from "@minecraft/server";
import {
  add, broadcast, cue, enemyOf, flatDistance, id, NS, particle, players, safe, sound, TEAM_KEYS, TEAMS, teamOf, tell,
} from "./core.js";
import { award, onKill, SOLDIER_TYPES } from "./teams.js";
import { paint } from "./vehicles.js";

/**
 * @typedef {import("@minecraft/server").Vector3} Vec
 * @typedef {{key: string, x: number, y: number, z: number, owner: number, progress: number, built: boolean}} Point
 * @typedef {{x: number, y: number, z: number, built: boolean}} HQ
 * @typedef {object} Battle
 * @property {boolean} active
 * @property {string} dim
 * @property {Point[]} points
 * @property {{nato: HQ, redfang: HQ}} hq
 * @property {{nato: number, redfang: number}} tickets
 * @property {number} max
 * @property {number} bots
 * @property {boolean} vehicles
 * @property {{x: number, z: number}} axis      from the NATO HQ towards the Red Fang HQ
 * @property {number} [endsAt]
 */

const KEY = "fl:battle";
const RADIUS = 8;
/** @type {Record<number, string>} */
const OWNER = { 0: "neutral", 1: "nato", 2: "redfang" };
/** @type {Record<number, string>} */
const FLAG_BLOCK = { 0: id("flag_neutral"), 1: id("flag_nato"), 2: id("flag_redfang") };

/** @type {Battle | undefined} */
let battle;
let dirty = false;

/** @returns {Battle | undefined} */
export function current() {
  if (battle === undefined) {
    const raw = safe(() => world.getDynamicProperty(KEY));
    try {
      battle = typeof raw === "string" ? JSON.parse(raw) : undefined;
    } catch {
      battle = undefined;
    }
  }
  return battle?.active ? battle : undefined;
}

function save() {
  safe(() => world.setDynamicProperty(KEY, battle ? JSON.stringify(battle) : undefined));
  dirty = false;
}

const dimOf = (/** @type {Battle} */ b) => world.getDimension(b.dim);

// ------------------------------------------------------------------ terrain and building

const SOFT = ["leaves", "log", "grass", "fern", "flower", "bush", "snow_layer", "vine", "mushroom", "sapling", "dead", "kelp",
  "seagrass", "torch", "tulip", "daisy", "poppy", "orchid", "allium", "bluet", "lily", "rose", "sugar_cane", "bamboo", "wood"];

/** The y of solid ground at x, z (below trees and plants), or undefined if not loaded. @param {import("@minecraft/server").Dimension} dim @param {number} x @param {number} z */
export function groundAt(dim, x, z) {
  const top = safe(() => dim.getTopmostBlock({ x, z }));
  if (!top) return undefined;
  let y = top.location.y;
  for (let i = 0; i < 30; i++) {
    const b = safe(() => dim.getBlock({ x, y, z }));
    if (!b) return undefined;
    const t = b.typeId;
    if (!b.isAir && !SOFT.some((s) => t.includes(s)) && !b.isLiquid) return y;
    if (b.isLiquid) return y;
    y--;
  }
  return y;
}

/** @param {import("@minecraft/server").Dimension} dim @param {Vec} at @param {string} type */
function put(dim, at, type) {
  safe(() => dim.getBlock(at)?.setType(type));
}
/** @param {import("@minecraft/server").Dimension} dim @param {Vec} a @param {Vec} b @param {string} type */
function fill(dim, a, b, type) {
  const done = safe(() => {
    dim.fillBlocks(new BlockVolume(a, b), type);
    return true;
  });
  if (done) return;
  for (let x = Math.min(a.x, b.x); x <= Math.max(a.x, b.x); x++)
    for (let y = Math.min(a.y, b.y); y <= Math.max(a.y, b.y); y++)
      for (let z = Math.min(a.z, b.z); z <= Math.max(a.z, b.z); z++) put(dim, { x, y, z }, type);
}

/** Whether every corner of an area is loaded. @param {import("@minecraft/server").Dimension} dim @param {Vec} c @param {number} r */
function loaded(dim, c, r) {
  for (const [dx, dz] of [[-r, -r], [r, -r], [-r, r], [r, r], [0, 0]]) {
    if (!safe(() => dim.getBlock({ x: c.x + dx, y: c.y, z: c.z + dz }))) return false;
  }
  return true;
}

/** @param {Battle} b @param {Point} p */
function buildPoint(b, p) {
  const dim = dimOf(b);
  const g = groundAt(dim, p.x, p.z);
  if (g === undefined || !loaded(dim, { x: p.x, y: g, z: p.z }, 5)) return false;
  p.y = g;
  const F = b.axis;
  const R = { x: -F.z, z: F.x };
  fill(dim, { x: p.x - 5, y: g + 1, z: p.z - 5 }, { x: p.x + 5, y: g + 8, z: p.z + 5 }, "minecraft:air");
  fill(dim, { x: p.x - 3, y: g, z: p.z - 3 }, { x: p.x + 3, y: g, z: p.z + 3 }, "minecraft:coarse_dirt");
  put(dim, { x: p.x, y: g, z: p.z }, FLAG_BLOCK[p.owner]);
  // cover: sandbag walls either side and a low wall at the front and back
  for (let k = -2; k <= 2; k++) {
    for (const side of [-4, 4]) {
      const at = { x: p.x + R.x * side + F.x * k, y: g + 1, z: p.z + R.z * side + F.z * k };
      put(dim, at, id("sandbags"));
      if (Math.abs(k) <= 1) put(dim, add(at, { x: 0, y: 1, z: 0 }), id("sandbags"));
    }
    for (const end of [-4, 4]) {
      if (Math.abs(k) === 2) continue;
      put(dim, { x: p.x + F.x * end + R.x * k, y: g + 1, z: p.z + F.z * end + R.z * k }, id("sandbags"));
    }
  }
  put(dim, { x: p.x + F.x * 2 + R.x * 2, y: g + 1, z: p.z + F.z * 2 + R.z * 2 }, id("ammo_crate"));
  put(dim, { x: p.x - F.x * 6 + R.x * 3, y: g + 1, z: p.z - F.z * 6 + R.z * 3 }, id("barbed_wire"));
  put(dim, { x: p.x - F.x * 6 - R.x * 3, y: g + 1, z: p.z - F.z * 6 - R.z * 3 }, id("barbed_wire"));
  spawnFlag(b, p);
  p.built = true;
  return true;
}

/** @param {Battle} b @param {Point} p */
function spawnFlag(b, p) {
  const dim = dimOf(b);
  const flag = safe(() => dim.spawnEntity(id("capture_flag"), { x: p.x + 0.5, y: p.y + 1, z: p.z + 0.5 }));
  if (!flag) return;
  safe(() => {
    flag.addTag("fl_battle");
    flag.addTag(`fl_flag_${p.key}`);
    flag.nameTag = `§l${p.key}`;
  });
  updateFlag(b, p, flag);
}

/** @param {Battle} b @param {import("./core.js").Team} team */
function buildHQ(b, team) {
  const hq = b.hq[team];
  const dim = dimOf(b);
  const g = groundAt(dim, hq.x, hq.z);
  if (g === undefined || !loaded(dim, { x: hq.x, y: g, z: hq.z }, 7)) return false;
  hq.y = g;
  const F = team === "nato" ? b.axis : { x: -b.axis.x, z: -b.axis.z }; // towards the enemy
  const R = { x: -F.z, z: F.x };
  const wool = TEAMS[team].wool;
  fill(dim, { x: hq.x - 7, y: g + 1, z: hq.z - 7 }, { x: hq.x + 7, y: g + 9, z: hq.z + 7 }, "minecraft:air");
  fill(dim, { x: hq.x - 6, y: g, z: hq.z - 6 }, { x: hq.x + 6, y: g, z: hq.z + 6 }, "minecraft:gravel");
  // the vehicle pad in front, the tent behind
  for (let a = -3; a <= 3; a++) for (let c = 1; c <= 6; c++) put(dim, { x: hq.x + R.x * a + F.x * c, y: g, z: hq.z + R.z * a + F.z * c }, "minecraft:polished_andesite");
  for (let a = -2; a <= 2; a++) {
    for (let c = -5; c <= -2; c++) {
      const base = { x: hq.x + R.x * a + F.x * c, y: g, z: hq.z + R.z * a + F.z * c };
      if (Math.abs(a) === 2) {
        put(dim, add(base, { x: 0, y: 1, z: 0 }), wool);
        put(dim, add(base, { x: 0, y: 2, z: 0 }), wool);
      }
      put(dim, add(base, { x: 0, y: Math.abs(a) === 2 ? 3 : Math.abs(a) === 1 ? 4 : 5, z: 0 }), wool);
      if (Math.abs(a) === 1) put(dim, add(base, { x: 0, y: 3, z: 0 }), "minecraft:air");
    }
  }
  for (const a of [-1, 1]) put(dim, { x: hq.x + R.x * a * 4 + F.x * -3, y: g + 1, z: hq.z + R.z * a * 4 + F.z * -3 }, id("ammo_crate"));
  for (let a = -6; a <= 6; a++) {
    if (Math.abs(a) <= 3) continue;
    put(dim, { x: hq.x + R.x * a + F.x * 6, y: g + 1, z: hq.z + R.z * a + F.z * 6 }, id("sandbags"));
  }
  hq.built = true;
  if (b.vehicles) {
    spawnVehicle(b, team, "jeep", -2);
    spawnVehicle(b, team, "jeep", 2);
    spawnVehicle(b, team, "tank", 0, 9);
  }
  return true;
}

/** @param {Battle} b @param {import("./core.js").Team} team @param {"jeep" | "tank"} kind @param {number} lateral @param {number} [forward] */
function spawnVehicle(b, team, kind, lateral, forward = 4) {
  const hq = b.hq[team];
  const F = team === "nato" ? b.axis : { x: -b.axis.x, z: -b.axis.z };
  const R = { x: -F.z, z: F.x };
  const dim = dimOf(b);
  const x = hq.x + R.x * lateral + F.x * forward;
  const z = hq.z + R.z * lateral + F.z * forward;
  const g = groundAt(dim, x, z) ?? hq.y;
  const v = safe(() => dim.spawnEntity(id(kind), { x: x + 0.5, y: g + 1.1, z: z + 0.5 }));
  if (!v) return;
  safe(() => {
    v.addTag("fl_battle");
    v.addTag(`fl_veh_${team}`);
    v.setRotation({ x: 0, y: Math.atan2(-F.x, F.z) * 180 / Math.PI });
  });
  paint(v, team);
}

// ------------------------------------------------------------------ starting and ending

/**
 * Lays out a battle from where `player` stands, their team's headquarters at their feet and the line of
 * capture points running the way they face (snapped to the nearest compass direction).
 * @param {import("@minecraft/server").Player} player
 * @param {{flags: number, tickets: number, bots: number, vehicles: boolean}} opts
 */
export function startBattle(player, opts) {
  if (current()) {
    tell(player, "§cA battle is already on. End it from the Field Radio first.");
    return;
  }
  const team = teamOf(player) ?? "nato";
  const yaw = player.getRotation().y;
  const dirs = [{ x: 0, z: 1 }, { x: -1, z: 0 }, { x: 0, z: -1 }, { x: 1, z: 0 }];
  const facing = dirs[((Math.round(yaw / 90) % 4) + 4) % 4];
  const axis = team === "nato" ? facing : { x: -facing.x, z: -facing.z };
  const base = { x: Math.floor(player.location.x), z: Math.floor(player.location.z) };
  const spacing = 36;
  const length = 32 + (opts.flags - 1) * spacing + 32;
  const R = { x: -facing.z, z: facing.x };
  const points = [];
  for (let i = 0; i < opts.flags; i++) {
    const along = 32 + i * spacing;
    const side = (i % 2 === 0 ? -1 : 1) * (opts.flags > 1 ? 8 : 0);
    points.push({ key: String.fromCharCode(65 + i), x: base.x + facing.x * along + R.x * side, y: 64, z: base.z + facing.z * along + R.z * side,
      owner: 0, progress: 0, built: false });
  }
  if (team === "redfang") points.reverse();
  points.forEach((p, i) => (p.key = String.fromCharCode(65 + i)));
  const far = { x: base.x + facing.x * length, z: base.z + facing.z * length };
  const ownHQ = { x: base.x, y: Math.floor(player.location.y), z: base.z, built: false };
  const enemyHQ = { x: far.x, y: Math.floor(player.location.y), z: far.z, built: false };
  battle = {
    active: true, dim: player.dimension.id, points, axis,
    hq: team === "nato" ? { nato: ownHQ, redfang: enemyHQ } : { nato: enemyHQ, redfang: ownHQ },
    tickets: { nato: opts.tickets, redfang: opts.tickets }, max: opts.tickets, bots: opts.bots, vehicles: opts.vehicles,
  };
  save();
  const lo = { x: Math.min(base.x, far.x) - 24, z: Math.min(base.z, far.z) - 24 };
  const hi = { x: Math.max(base.x, far.x) + 24, z: Math.max(base.z, far.z) + 24 };
  safe(() => player.dimension.runCommand("tickingarea remove fl_battle"));
  safe(() => player.dimension.runCommand(`tickingarea add ${lo.x} 0 ${lo.z} ${hi.x} 0 ${hi.z} fl_battle true`));
  for (const p of players()) {
    sound(p.dimension, `${NS}.battle_start`, p.location, 1);
    safe(() => p.onScreenDisplay.setTitle("§6CONQUEST", { subtitle: `§7${opts.flags} flags · ${opts.tickets} tickets each`, fadeInDuration: 10, stayDuration: 60, fadeOutDuration: 20 }));
  }
  broadcast(`§6[Battle] §f${player.name} started a conquest battle: §9NATO §fvs §cRed Fang§f. Capture the flags, drain the enemy's tickets.`);
  sidebar(true);
  for (const fn of onStart) safe(() => fn());
}

/** @type {Array<() => void>} */
export const onStart = [];

/** @param {import("./core.js").Team | undefined} winner */
export function endBattle(winner) {
  const b = current();
  if (!b) return;
  b.active = false;
  save();
  if (winner) {
    const t = TEAMS[winner];
    for (const p of players()) {
      const mine = teamOf(p) === winner;
      safe(() => p.onScreenDisplay.setTitle(mine ? "§aVICTORY" : teamOf(p) ? "§cDEFEAT" : `${t.color}${t.name} WINS`, {
        subtitle: `${t.color}${t.name} §7wins the battle`, fadeInDuration: 10, stayDuration: 80, fadeOutDuration: 20,
      }));
      cue(p, mine ? `${NS}.victory` : `${NS}.defeat`);
      if (mine) award(p, 500, "Victory", 1000);
    }
    broadcast(`§6[Battle] ${t.color}${t.name} §fwins! §7(NATO ${b.tickets.nato} · Red Fang ${b.tickets.redfang} tickets left)`);
  } else {
    broadcast("§6[Battle] §fThe battle was called off.");
  }
  system.runTimeout(() => cleanup(b), winner ? 200 : 20);
  sidebar(false);
}

/** Removes the battle's soldiers, vehicles and flags, and turns the flag bases to stone. @param {Battle} b */
function cleanup(b) {
  const dim = dimOf(b);
  for (const e of safe(() => dim.getEntities({ tags: ["fl_battle"] })) ?? []) {
    const rider = safe(() => e.getComponent("minecraft:rideable")?.getRiders().length) ?? 0;
    if (rider > 0) continue; // never yank a vehicle from under a player
    safe(() => e.remove());
  }
  for (const p of b.points) put(dim, { x: p.x, y: p.y, z: p.z }, "minecraft:polished_andesite");
  for (const p of players()) safe(() => p.removeTag("fl_in_battle"));
  safe(() => dim.runCommand("tickingarea remove fl_battle"));
}

// ------------------------------------------------------------------ flags

/** The flag entity of a point, if loaded. @param {Battle} b @param {Point} p */
function flagOf(b, p) {
  return safe(() => dimOf(b).getEntities({ tags: [`fl_flag_${p.key}`] })[0]);
}

/** @param {Battle} b @param {Point} p @param {import("@minecraft/server").Entity} [flag] */
function updateFlag(b, p, flag) {
  const f = flag ?? flagOf(b, p);
  if (!f) return;
  const shown = p.owner !== 0 ? p.owner : p.progress > 0 ? 1 : p.progress < 0 ? 2 : 0;
  safe(() => {
    if (f.getProperty(`${NS}:owner`) !== shown) f.setProperty(`${NS}:owner`, shown);
    const raise = Math.round(Math.abs(p.progress)) / 100;
    if (f.getProperty(`${NS}:raise`) !== raise) f.setProperty(`${NS}:raise`, raise);
    const col = shown === 1 ? "§9" : shown === 2 ? "§c" : "§f";
    f.nameTag = `${col}§l${p.key}`;
  });
}

/** Who stands at a point: [NATO, Red Fang]. @param {Battle} b @param {Point} p */
function presence(b, p) {
  const counts = { nato: 0, redfang: 0 };
  const dim = dimOf(b);
  const at = { x: p.x + 0.5, y: p.y + 1, z: p.z + 0.5 };
  for (const e of safe(() => dim.getEntities({ location: at, maxDistance: RADIUS + 2, families: ["frontline_soldier"] })) ?? []) {
    const t = teamOf(e);
    if (t && flatDistance(e.location, at) <= RADIUS && Math.abs(e.location.y - at.y) < 6) counts[t]++;
  }
  for (const pl of players()) {
    const t = teamOf(pl);
    if (!t || pl.dimension.id !== b.dim) continue;
    if (safe(() => pl.getComponent("minecraft:health")?.currentValue ?? 0) === 0) continue;
    if (flatDistance(pl.location, at) <= RADIUS && Math.abs(pl.location.y - at.y) < 6) counts[t]++;
  }
  return counts;
}

/** @param {Battle} b @param {Point} p @param {number} owner */
function setOwner(b, p, owner) {
  const before = p.owner;
  p.owner = owner;
  const dim = dimOf(b);
  put(dim, { x: p.x, y: p.y, z: p.z }, FLAG_BLOCK[owner]);
  const at = { x: p.x + 0.5, y: p.y + 2, z: p.z + 0.5 };
  if (owner === 0) {
    const lost = OWNER[before];
    broadcast(`§6[Battle] §fFlag §l${p.key}§r §fneutralised §7(was ${TEAMS[/** @type {"nato"} */ (lost)].color}${TEAMS[/** @type {"nato"} */ (lost)].name}§7)`);
    for (const pl of players()) if (teamOf(pl) === lost) cue(pl, `${NS}.capture_lost`);
  } else {
    const team = /** @type {import("./core.js").Team} */ (OWNER[owner]);
    const t = TEAMS[team];
    broadcast(`§6[Battle] ${t.color}${t.name} §fcaptured flag §l${p.key}`);
    particle(dim, `${NS}:capture_${team}`, at);
    for (const pl of players()) {
      if (teamOf(pl) === team) {
        cue(pl, `${NS}.capture`);
        if (flatDistance(pl.location, at) <= RADIUS + 1) award(pl, 150, `Captured ${p.key}`, 250);
      } else if (teamOf(pl)) cue(pl, `${NS}.capture_lost`);
    }
  }
}

function captureTick() {
  const b = current();
  if (!b) return;
  for (const p of b.points) {
    if (!p.built) continue;
    const c = presence(b, p);
    const net = Math.max(-3, Math.min(3, c.nato - c.redfang));
    const before = p.progress;
    if (net !== 0) p.progress = Math.max(-100, Math.min(100, p.progress + net * 4));
    else if (p.owner === 1 && p.progress < 100) p.progress = Math.min(100, p.progress + 1);
    else if (p.owner === 2 && p.progress > -100) p.progress = Math.max(-100, p.progress - 1);
    else if (p.owner === 0 && p.progress !== 0) p.progress += p.progress > 0 ? -1 : 1;
    if (p.progress === before) continue;
    dirty = true;
    if (p.owner === 1 && p.progress <= 0) setOwner(b, p, 0);
    else if (p.owner === 2 && p.progress >= 0) setOwner(b, p, 0);
    if (p.owner !== 1 && p.progress >= 100) setOwner(b, p, 1);
    else if (p.owner !== 2 && p.progress <= -100) setOwner(b, p, 2);
    updateFlag(b, p);
  }
}

/** The capture point (if any) a player stands at, with its progress, for the HUD. @param {import("@minecraft/server").Player} player */
export function pointAt(player) {
  const b = current();
  if (!b || player.dimension.id !== b.dim) return undefined;
  return b.points.find((p) => p.built && flatDistance(player.location, { x: p.x + 0.5, y: 0, z: p.z + 0.5 }) <= RADIUS);
}

// ------------------------------------------------------------------ tickets

function bleed() {
  const b = current();
  if (!b) return;
  const held = { nato: b.points.filter((p) => p.owner === 1).length, redfang: b.points.filter((p) => p.owner === 2).length };
  if (held.nato > held.redfang) b.tickets.redfang -= held.nato - held.redfang;
  else if (held.redfang > held.nato) b.tickets.nato -= held.redfang - held.nato;
  dirty = true;
  checkEnd(b);
}

/** @param {Battle} b */
function checkEnd(b) {
  for (const t of TEAM_KEYS) {
    b.tickets[t] = Math.max(0, b.tickets[t]);
    if (b.tickets[t] === 0) {
      endBattle(enemyOf(t));
      return;
    }
  }
  for (const t of TEAM_KEYS) {
    const left = b.tickets[t];
    if (left === Math.floor(b.max * 0.25) || left === 25) {
      for (const pl of players()) if (teamOf(pl) === t) safe(() => pl.onScreenDisplay.setTitle(" ", { subtitle: `§cYour team is low on tickets (${left})`, fadeInDuration: 5, stayDuration: 40, fadeOutDuration: 10 }));
    }
  }
}

/** @param {boolean} on */
function sidebar(on) {
  safe(() => {
    const board = world.scoreboard;
    const old = board.getObjective("fl_battle");
    if (old) board.removeObjective(old);
    if (!on) return;
    const o = board.addObjective("fl_battle", "§6§lCONQUEST");
    board.setObjectiveAtDisplaySlot(DisplaySlotId.Sidebar, { objective: o });
  });
  refreshSidebar();
}

function refreshSidebar() {
  const b = current();
  if (!b) return;
  safe(() => {
    const o = world.scoreboard.getObjective("fl_battle");
    o?.setScore("§9NATO", b.tickets.nato);
    o?.setScore("§cRed Fang", b.tickets.redfang);
  });
}

// ------------------------------------------------------------------ the AI director

/** Where a team's soldiers come in: the held flag closest to the enemy, else headquarters. @param {Battle} b @param {import("./core.js").Team} team */
export function frontline(b, team) {
  const owned = b.points.filter((p) => p.built && p.owner === (team === "nato" ? 1 : 2));
  const enemy = b.hq[enemyOf(team)];
  owned.sort((a, c) => flatDistance(a, enemy) - flatDistance(c, enemy));
  if (owned.length) return { x: owned[0].x, y: owned[0].y, z: owned[0].z, label: `Flag ${owned[0].key}` };
  return { x: b.hq[team].x, y: b.hq[team].y, z: b.hq[team].z, label: "Headquarters" };
}

/** @param {Battle} b @param {import("./core.js").Team} team */
function reinforce(b, team) {
  if (b.tickets[team] <= 0) return;
  const dim = dimOf(b);
  const alive = (safe(() => dim.getEntities({ tags: ["fl_battle", `fl_bot_${team}`] })) ?? []).length;
  if (alive >= b.bots) return;
  const at = frontline(b, team);
  const enemyArmour = (safe(() => dim.getEntities({ tags: [`fl_veh_${enemyOf(team)}`] })) ?? []).length;
  for (let i = 0; i < Math.min(2, b.bots - alive); i++) {
    const roll = Math.random();
    const [rifle, marksman, heavy] = SOLDIER_TYPES[team];
    const type = roll < (enemyArmour ? 0.6 : 0.72) ? rifle : roll < (enemyArmour ? 0.75 : 0.87) ? marksman : heavy;
    const x = at.x + Math.round(Math.random() * 6 - 3);
    const z = at.z + Math.round(Math.random() * 6 - 3);
    const g = groundAt(dim, x, z);
    if (g === undefined) continue;
    const s = safe(() => dim.spawnEntity(type, { x: x + 0.5, y: g + 1, z: z + 0.5 }));
    if (!s) continue;
    safe(() => {
      s.triggerEvent(`${NS}:make_persistent`);
      s.addTag("fl_battle");
      s.addTag(`fl_bot_${team}`);
    });
  }
}

/** @param {Battle} b */
function vehiclesBack(b) {
  if (!b.vehicles) return;
  const dim = dimOf(b);
  for (const team of TEAM_KEYS) {
    if (!b.hq[team].built) continue;
    const mine = safe(() => dim.getEntities({ tags: [`fl_veh_${team}`] })) ?? [];
    const jeeps = mine.filter((v) => v.typeId === id("jeep")).length;
    const tanks = mine.filter((v) => v.typeId === id("tank")).length;
    if (jeeps < 2) spawnVehicle(b, team, "jeep", jeeps === 0 ? -2 : 2);
    if (tanks < 1) spawnVehicle(b, team, "tank", 0, 9);
  }
}

// ------------------------------------------------------------------ the loop

export function init() {
  onKill.push((dead) => {
    const b = current();
    if (!b) return;
    const t = teamOf(dead);
    if (!t) return;
    if (dead.typeId === "minecraft:player" ? safe(() => dead.hasTag("fl_in_battle")) : safe(() => dead.hasTag("fl_battle"))) {
      b.tickets[t] -= 1;
      dirty = true;
      checkEnd(b);
    }
  });

  let tick = 0;
  system.runInterval(() => {
    tick++;
    const b = current();
    if (!b) return;
    // build what is not built yet, as its chunks load
    for (const p of b.points) if (!p.built && buildPoint(b, p)) dirty = true;
    for (const t of TEAM_KEYS) if (!b.hq[t].built && buildHQ(b, t)) dirty = true;
    captureTick();
    if (tick % 4 === 0) for (const t of TEAM_KEYS) reinforce(b, t);
    if (tick % 10 === 0) {
      bleed();
      refreshSidebar();
    }
    if (tick % 12 === 0) {
      for (const p of b.points) if (p.built && !flagOf(b, p) && safe(() => dimOf(b).getBlock({ x: p.x, y: p.y, z: p.z }))) spawnFlag(b, p);
    }
    if (tick % 60 === 0) vehiclesBack(b);
    if (dirty && tick % 4 === 0) save();
  }, 10);
}

/** A one-line summary of the battle for the HUD. */
export function hudLine() {
  const b = current();
  if (!b) return "";
  const flags = b.points.map((p) => {
    const col = p.owner === 1 ? "§9" : p.owner === 2 ? "§c" : p.progress > 0 ? "§b" : p.progress < 0 ? "§6" : "§7";
    return `${col}${p.key}`;
  }).join(" ");
  return `§9NATO ${b.tickets.nato} §8| ${flags} §8| §c${b.tickets.redfang} RED FANG`;
}

/** Spawn points a player of `team` may deploy to: headquarters and held flags (front first). @param {import("./core.js").Team} team */
export function deployPoints(team) {
  const b = current();
  if (!b) return [];
  const list = [{ label: "Headquarters", x: b.hq[team].x, y: b.hq[team].y, z: b.hq[team].z }];
  const enemy = b.hq[enemyOf(team)];
  const owned = b.points.filter((p) => p.built && p.owner === (team === "nato" ? 1 : 2));
  owned.sort((a, c) => flatDistance(a, enemy) - flatDistance(c, enemy));
  for (const p of owned) list.push({ label: `Flag ${p.key}`, x: p.x, y: p.y, z: p.z });
  return list;
}

