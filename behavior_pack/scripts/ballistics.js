// Bullets in flight. Every round the players fire is a simulated bullet: it leaves the muzzle at its cartridge's
// real velocity, slows with air drag, falls with gravity and is stepped once a game tick (1 block = 1 m, 20 ticks
// a second), with a ray along each step for walls, bodies and heads. Near shots land at once; long shots take
// their real time of flight and drop on the way, so far targets need leading and holding over.
import { EntityDamageCause, system } from "@minecraft/server";
import {
  add, cue, distance, dot, isSoldier, isVehicle, length, NS, particle, players, safe, sameTeam, scale, settings, sub,
} from "./core.js";
import { noteHit } from "./teams.js";

/** Gravity in blocks per tick per tick (9.81 m/s² at 20 ticks a second). */
export const GRAVITY = 9.81 / 400;
/** Ticks a bullet may fly (4 s; nothing is that far away in loaded chunks). */
const MAX_TICKS = 80;
/** Below this speed (blocks a tick) a bullet is spent. */
const SPENT = 1.5;
/** The speed of sound in blocks a tick: faster bullets crack as they pass. */
const SOUND_SPEED = 343 / 20;

const SKIP_TYPES = [`${NS}:capture_flag`, `${NS}:corpse`, `${NS}:bullet`, `${NS}:sniper_bullet`, `${NS}:rocket`, `${NS}:tank_shell`,
  `${NS}:frag_grenade`, `${NS}:smoke_grenade`, "minecraft:item", "minecraft:xp_orb", "minecraft:arrow"];

/**
 * @typedef {object} Shot
 * @property {number} speed      muzzle velocity, blocks a tick
 * @property {number} drag       fraction of speed lost per block flown (v = v0·e^(-drag·d))
 * @property {number} damage     at the muzzle; scales with the bullet's remaining speed
 * @property {number} headshot   damage multiplier
 * @property {string} weapon     name for the kill feed
 * @property {boolean} [tracer]  draw its path
 */

/**
 * @typedef {object} Bullet
 * @property {import("@minecraft/server").Player} owner
 * @property {import("@minecraft/server").Dimension} dim
 * @property {import("@minecraft/server").Vector3} pos
 * @property {import("@minecraft/server").Vector3} vel  blocks a tick
 * @property {number} v0
 * @property {number} age
 * @property {number} flown  blocks so far
 * @property {number} born   the tick it was fired (its first step was taken then)
 * @property {Shot} shot
 */

/** @type {Bullet[]} */
const flying = [];
/** Owners already given a hit marker this tick. @type {Set<string>} */
const markedThisTick = new Set();
/** Players who heard a bullet crack this tick. @type {Set<string>} */
const crackedThisTick = new Set();

/** How many bullets are in the air (for tests and the debug readout). */
export const inFlight = () => flying.length;
/** Where the bullets in the air are and how fast they go (for tests). */
export const snapshot = () => flying.map((b) => ({ pos: { ...b.pos }, vel: { ...b.vel }, age: b.age, flown: b.flown }));

/** The direction to launch a bullet so it crosses the line of sight again at `zero` blocks (the sights are zeroed
 * there): tilted up by the angle its drop over that distance needs. @param {import("@minecraft/server").Vector3} dir @param {number} speed @param {number} zero */
export function zeroed(dir, speed, zero) {
  const g = GRAVITY * settings().bulletDrop;
  if (g <= 0 || speed <= 0) return dir;
  const angle = (g * zero) / (2 * speed * speed);
  const flat = Math.hypot(dir.x, dir.z);
  if (flat < 1e-6) return dir;
  const pitch = Math.atan2(dir.y, flat) + angle;
  return { x: (dir.x / flat) * Math.cos(pitch), y: Math.sin(pitch), z: (dir.z / flat) * Math.cos(pitch) };
}

/** Fires a bullet from `origin` along `dir` (a unit vector). The first step is taken at once.
 * @param {import("@minecraft/server").Player} owner @param {import("@minecraft/server").Vector3} origin
 * @param {import("@minecraft/server").Vector3} dir @param {Shot} shot */
export function launch(owner, origin, dir, shot) {
  /** @type {Bullet} */
  const b = { owner, dim: owner.dimension, pos: { ...origin }, vel: scale(dir, shot.speed), v0: shot.speed, age: 0, flown: 0, born: system.currentTick, shot };
  if (step(b)) flying.push(b);
}

/** Whether a stretch of a bullet's path passes through a target's head. @param {import("@minecraft/server").Vector3} from @param {import("@minecraft/server").Vector3} dir @param {number} upTo @param {import("@minecraft/server").Entity} target */
function throughHead(from, dir, upTo, target) {
  if (!(target.typeId === "minecraft:player" || isSoldier(target) || target.matches({ families: ["zombie"] }) || target.matches({ families: ["skeleton"] }))) return false;
  const head = safe(() => target.getHeadLocation());
  if (!head) return false;
  const t = Math.max(0, Math.min(upTo + 0.6, dot(sub(head, from), dir)));
  return distance(add(from, scale(dir, t)), head) < 0.36;
}

/** Moves a bullet one tick: hits along the way, then drag and gravity. Returns false when it is done.
 * @param {Bullet} b */
function step(b) {
  const len = length(b.vel);
  if (len < SPENT || b.age >= MAX_TICKS) return false;
  const dir = scale(b.vel, 1 / len);
  const dim = b.dim;
  const owner = b.owner;
  const block = safe(() => dim.getBlockFromRay(b.pos, dir, { maxDistance: len, includeLiquidBlocks: false, includePassableBlocks: false }));
  const wall = block ? distance(b.pos, add(block.block.location, block.faceLocation)) : len;
  const hits = safe(() => dim.getEntitiesFromRay(b.pos, dir, { maxDistance: wall, excludeTypes: SKIP_TYPES })) ?? [];
  const riding = safe(() => owner.getComponent("minecraft:riding")?.entityRidingOn);
  /** @type {import("@minecraft/server").Entity | undefined} */
  let target;
  let at = wall;
  for (const h of hits) {
    const e = h.entity;
    if (e === owner || (riding && e === riding) || !safe(() => e.isValid)) continue;
    if (!settings().friendlyFire && safe(() => owner.isValid) && sameTeam(owner, e)) continue;
    target = e;
    at = h.distance;
    break;
  }

  // the path drawn as a streak of tracer light (from 1.5 blocks out, so it does not cover the sights)
  if (b.shot.tracer !== false && settings().tracers) {
    const start = b.flown < 1.5 ? 1.5 - b.flown : 0;
    const gap = Math.max(1.4, at / 14);
    for (let d = start; d < at; d += gap) particle(dim, `${NS}:tracer`, add(b.pos, scale(dir, d)));
  }
  // a supersonic round cracks past anyone it misses closely
  if (len > SOUND_SPEED) {
    for (const p of players()) {
      if (p === owner || p.dimension.id !== dim.id || crackedThisTick.has(p.id)) continue;
      const head = safe(() => p.getHeadLocation());
      if (!head) continue;
      const t = dot(sub(head, b.pos), dir);
      if (t < 0 || t > at) continue;
      const miss = distance(add(b.pos, scale(dir, t)), head);
      if (miss < 3 && miss > 0.5) {
        crackedThisTick.add(p.id);
        cue(p, `${NS}.bullet_crack`, 0.7, 0.9 + Math.random() * 0.2);
      }
    }
  }

  const end = add(b.pos, scale(dir, at));
  if (target) {
    const head = throughHead(b.pos, dir, at, target);
    const energy = Math.max(0.25, len / b.v0);
    let dmg = b.shot.damage * energy * (head ? b.shot.headshot : 1);
    if (safe(() => target.hasTag("fl_spotted"))) dmg *= 1.15;
    noteHit(target, b.shot.weapon, head);
    const t = target;
    safe(() => t.applyDamage(dmg, { cause: EntityDamageCause.projectile, damagingEntity: owner }));
    particle(dim, isVehicle(t) ? `${NS}:sparks` : `${NS}:blood`, end);
    if (!markedThisTick.has(owner.id)) {
      markedThisTick.add(owner.id);
      cue(owner, `${NS}.hitmarker`, head ? 1 : 0.8, head ? 1.35 : 1 + Math.random() * 0.1);
    }
    return false;
  }
  if (block) {
    particle(dim, `${NS}:impact_dust`, end);
    return false;
  }

  // nothing in the way: fly on, slowed by the air and pulled down by gravity
  b.pos = end;
  b.flown += len;
  b.age++;
  const slowed = len * Math.exp(-b.shot.drag * len);
  b.vel = scale(dir, slowed);
  b.vel.y -= GRAVITY * settings().bulletDrop;
  if (b.pos.y < -70 || b.pos.y > 400) return false;
  if (!safe(() => dim.getBlock(b.pos))) return false; // flew out of the loaded world
  return true;
}

function tick() {
  markedThisTick.clear();
  crackedThisTick.clear();
  for (let i = flying.length - 1; i >= 0; i--) {
    const b = flying[i];
    if (b.born === system.currentTick) continue; // already stepped when fired
    if (!safe(() => step(b))) flying.splice(i, 1);
  }
}

export function init() {
  system.runInterval(tick, 1);
}
