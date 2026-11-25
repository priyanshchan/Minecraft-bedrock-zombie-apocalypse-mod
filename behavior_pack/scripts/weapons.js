// Firearms: hitscan shots with spread, magazines and reloads, headshots, tracers and muzzle flashes, the
// third-person aiming pose, and the effects of the AI soldiers' shots.
import { EntityDamageCause, system, world } from "@minecraft/server";
import {
  add, countItem, cue, distance, dot, getNumber, id, isCreative, isSoldier, isVehicle, normalize, NS, particle, players,
  safe, sameTeam, scale, settings, shake, sound, spread, sub, takeItem, notify, onUse,
} from "./core.js";
import { noteHit } from "./teams.js";

/**
 * @typedef {object} Gun
 * @property {string} name
 * @property {string} ammo         reserve ammunition item
 * @property {number} mag          rounds per magazine
 * @property {number} damage       per pellet
 * @property {number} [pellets]
 * @property {number} rate         ticks between trigger pulls
 * @property {number} [burst]      rounds per trigger pull
 * @property {number} spread       degrees of cone (halved while crouching)
 * @property {number} range
 * @property {number} reload       ticks
 * @property {string} sound
 * @property {string} pose         third-person pose
 * @property {number} [headshot]   damage multiplier
 * @property {string} [projectile] fires an entity instead of a hitscan round
 * @property {number} [kick]       camera shake
 */

/** @type {Record<string, Gun>} */
export const GUNS = {
  [id("service_pistol")]: { name: "Service Pistol", ammo: id("pistol_ammo"), mag: 12, damage: 6, rate: 5, spread: 1.6, range: 48, reload: 30, sound: `${NS}.pistol`, pose: "pistol", headshot: 1.8, kick: 0.04 },
  [id("smg")]: { name: "Talon SMG", ammo: id("pistol_ammo"), mag: 30, damage: 4, rate: 6, burst: 3, spread: 3.0, range: 40, reload: 40, sound: `${NS}.smg`, pose: "rifle", headshot: 1.6, kick: 0.03 },
  [id("assault_rifle")]: { name: "Vanguard AR", ammo: id("rifle_ammo"), mag: 30, damage: 6, rate: 8, burst: 3, spread: 1.6, range: 90, reload: 45, sound: `${NS}.assault_rifle`, pose: "rifle", headshot: 1.8, kick: 0.05 },
  [id("lmg")]: { name: "Bulwark LMG", ammo: id("rifle_ammo"), mag: 100, damage: 5, rate: 10, burst: 5, spread: 2.8, range: 90, reload: 80, sound: `${NS}.lmg`, pose: "rifle", headshot: 1.6, kick: 0.06 },
  [id("shotgun")]: { name: "Breacher Shotgun", ammo: id("shotgun_shells"), mag: 6, damage: 3.5, pellets: 8, rate: 16, spread: 7, range: 22, reload: 60, sound: `${NS}.shotgun`, pose: "rifle", headshot: 1.3, kick: 0.12 },
  [id("sniper_rifle")]: { name: "Longshot Sniper", ammo: id("sniper_rounds"), mag: 5, damage: 22, rate: 30, spread: 0.3, range: 220, reload: 60, sound: `${NS}.sniper`, pose: "rifle", headshot: 2.5, kick: 0.15 },
  [id("rocket_launcher")]: { name: "Hornet Launcher", ammo: id("rocket"), mag: 1, damage: 0, rate: 20, spread: 0.4, range: 0, reload: 70, sound: `${NS}.rocket_launch`, pose: "launcher", projectile: id("rocket"), kick: 0.2 },
};

export const GUN_IDS = Object.keys(GUNS);
/** @type {Record<string, string[]>} */
const POSE_IDS = { rifle: [], pistol: [], launcher: [] };
for (const [key, g] of Object.entries(GUNS)) POSE_IDS[g.pose].push(key);

/** Ticks until which each player cannot fire, and active reloads. */
const nextShot = new Map();
/** @type {Map<string, {gun: string, done: number}>} */
const reloading = new Map();

/** Rounds in the magazine of a gun (stored per player and gun type; a new gun comes loaded). @param {import("@minecraft/server").Player} player @param {string} gun */
export function magOf(player, gun) {
  return getNumber(player, `fl:mag:${gun}`, GUNS[gun].mag);
}
/** @param {import("@minecraft/server").Player} player @param {string} gun @param {number} n */
function setMag(player, gun, n) {
  safe(() => player.setDynamicProperty(`fl:mag:${gun}`, n));
}

/** @param {import("@minecraft/server").Player} player @param {string} gun */
export function reserveOf(player, gun) {
  return isCreative(player) ? 999 : countItem(player, GUNS[gun].ammo);
}

/** @param {import("@minecraft/server").Player} player */
export function isReloading(player) {
  return reloading.has(player.id);
}

/** @param {import("@minecraft/server").Player} player @param {string} gun */
export function startReload(player, gun) {
  const g = GUNS[gun];
  if (reloading.has(player.id) || magOf(player, gun) >= g.mag) return;
  if (reserveOf(player, gun) <= 0) {
    cue(player, `${NS}.dry_fire`);
    notify(player, `§cNo ${g.ammo.replace(`${NS}:`, "").replace(/_/g, " ")} left`);
    return;
  }
  reloading.set(player.id, { gun, done: system.currentTick + g.reload });
  sound(player.dimension, `${NS}.reload`, player.location, 0.9, 30 / g.reload + 0.4);
}

function finishReloads() {
  const now = system.currentTick;
  for (const p of players()) {
    const r = reloading.get(p.id);
    if (!r || r.done > now) continue;
    reloading.delete(p.id);
    const g = GUNS[r.gun];
    const need = g.mag - magOf(p, r.gun);
    const got = isCreative(p) ? need : takeItem(p, g.ammo, need);
    setMag(p, r.gun, magOf(p, r.gun) + got);
    cue(p, `${NS}.click`, 0.8, 1.2);
  }
}

/** Cancels a reload when the player switches away. @param {import("@minecraft/server").Player} player @param {string | undefined} held */
export function checkReload(player, held) {
  const r = reloading.get(player.id);
  if (r && r.gun !== held) reloading.delete(player.id);
}

// ------------------------------------------------------------------ shooting

const SKIP_TYPES = [id("capture_flag"), id("bullet"), id("sniper_bullet"), id("rocket"), id("tank_shell"),
  id("frag_grenade"), id("smoke_grenade"), "minecraft:item", "minecraft:xp_orb", "minecraft:arrow"];

/** Whether a ray passes through the head of a target (for the headshot bonus). @param {import("@minecraft/server").Vector3} origin @param {import("@minecraft/server").Vector3} dir @param {import("@minecraft/server").Entity} target */
function throughHead(origin, dir, target) {
  if (!(target.typeId === "minecraft:player" || isSoldier(target) || target.matches({ families: ["zombie"] }) || target.matches({ families: ["skeleton"] }))) return false;
  const head = safe(() => target.getHeadLocation());
  if (!head) return false;
  const rel = sub(head, origin);
  const t = dot(rel, dir);
  const closest = add(origin, scale(dir, t));
  return distance(closest, head) < 0.36;
}

/** Fires one round. @param {import("@minecraft/server").Player} player @param {string} gunId @param {Gun} g */
function fireRound(player, gunId, g) {
  const dim = player.dimension;
  const eye = player.getHeadLocation();
  const look = player.getViewDirection();
  const steady = player.isSneaking ? 0.45 : player.isSprinting ? 1.8 : 1;
  const muzzle = add(eye, add(scale(look, 0.9), { x: -look.z * 0.25, y: -0.18, z: look.x * 0.25 }));
  particle(dim, `${NS}:muzzle_flash`, muzzle);
  particle(dim, `${NS}:gun_smoke`, muzzle);
  sound(dim, g.sound, eye, 1, 0.95 + Math.random() * 0.1);
  shake(player, g.kick ?? 0.05, 0.08);

  if (g.projectile) {
    const proj = safe(() => dim.spawnEntity(g.projectile ?? "", add(eye, scale(look, 1.4))));
    const comp = proj ? safe(() => proj.getComponent("minecraft:projectile")) : undefined;
    if (comp) {
      comp.owner = player;
      safe(() => comp.shoot(scale(normalize(spread(look, g.spread)), 2.2)));
    }
    return;
  }

  let hitAny = false;
  for (let p = 0; p < (g.pellets ?? 1); p++) {
    const dir = normalize(spread(look, g.spread * steady));
    const block = safe(() => dim.getBlockFromRay(eye, dir, { maxDistance: g.range, includeLiquidBlocks: false, includePassableBlocks: false }));
    const wall = block ? distance(eye, add(block.block.location, block.faceLocation)) : g.range;
    const hits = safe(() => dim.getEntitiesFromRay(eye, dir, { maxDistance: wall, excludeTypes: SKIP_TYPES })) ?? [];
    let target;
    let at = wall;
    for (const h of hits) {
      const e = h.entity;
      if (e === player || !safe(() => e.isValid)) continue;
      const riding = safe(() => player.getComponent("minecraft:riding")?.entityRidingOn);
      if (riding && riding === e) continue;
      if (!settings().friendlyFire && sameTeam(player, e)) continue;
      target = e;
      at = h.distance;
      break;
    }
    // tracer every 1.6 blocks (a few per shot so it reads as a streak)
    if (p === 0) {
      for (let d = 2; d < Math.min(at, 60); d += 1.6) particle(dim, `${NS}:tracer`, add(eye, scale(dir, d)));
    }
    const end = add(eye, scale(dir, at));
    if (!target) {
      if (block) particle(dim, `${NS}:impact_dust`, end);
      continue;
    }
    const head = throughHead(eye, dir, target);
    let dmg = g.damage * (at > g.range * 0.6 ? 0.75 : 1) * (head ? g.headshot ?? 1.5 : 1);
    if (safe(() => target.hasTag("fl_spotted"))) dmg *= 1.15;
    noteHit(target, g.name, head);
    safe(() => target.applyDamage(dmg, { cause: EntityDamageCause.projectile, damagingEntity: player }));
    particle(dim, isVehicle(target) ? `${NS}:sparks` : `${NS}:blood`, end);
    hitAny = true;
  }
  if (hitAny) cue(player, `${NS}.hitmarker`, 0.8, 1 + Math.random() * 0.1);
}

/** @param {import("@minecraft/server").Player} player @param {string} gunId */
export function pullTrigger(player, gunId) {
  const g = GUNS[gunId];
  const now = system.currentTick;
  if ((nextShot.get(player.id) ?? 0) > now) return;
  if (reloading.has(player.id)) return;
  const rounds = g.burst ?? 1;
  nextShot.set(player.id, now + g.rate + (rounds - 1) * 2);
  for (let i = 0; i < rounds; i++) {
    const fire = () => {
      if (!safe(() => player.isValid)) return;
      const held = safe(() => player.getComponent("minecraft:inventory")?.container?.getItem(player.selectedSlotIndex)?.typeId);
      if (held !== gunId || reloading.has(player.id)) return;
      const mag = magOf(player, gunId);
      if (mag <= 0) {
        cue(player, `${NS}.dry_fire`);
        startReload(player, gunId);
        return;
      }
      setMag(player, gunId, mag - 1);
      safe(() => fireRound(player, gunId, g));
      if (mag - 1 <= 0) system.runTimeout(() => startReload(player, gunId), 6);
    };
    if (i === 0) fire();
    else system.runTimeout(fire, i * 2);
  }
}

// ------------------------------------------------------------------ the aiming pose

/** What each player held last time we looked (to start and change the pose). */
const lastHeld = new Map();

/** @param {import("@minecraft/server").Player} player @param {string | undefined} held */
function updatePose(player, held) {
  const gun = held ? GUNS[held] : undefined;
  const pose = gun ? gun.pose : "";
  const key = `${pose}`;
  const prev = lastHeld.get(player.id);
  if (prev === key && system.currentTick % 100 !== 0) return;
  lastHeld.set(player.id, key);
  if (!gun) return;
  const ids = POSE_IDS[pose].map((x) => `'${x}'`).join(", ");
  safe(() => player.playAnimation(`animation.${NS}.player.aim_${pose}`, {
    controller: `${NS}_aim`,
    blendOutTime: 0.15,
    stopExpression: `!q.is_item_name_any('slot.weapon.mainhand', 0, ${ids})`,
  }));
}

/** @param {import("@minecraft/server").Player} player @param {string | undefined} held */
export function tickPlayer(player, held) {
  updatePose(player, held);
  checkReload(player, held);
}

/** The ammo readout for the HUD. @param {import("@minecraft/server").Player} player @param {string} held */
export function ammoText(player, held) {
  const g = GUNS[held];
  if (!g) return "";
  const r = reloading.get(player.id);
  if (r) {
    const pct = 1 - (r.done - system.currentTick) / g.reload;
    const bars = Math.round(Math.max(0, Math.min(1, pct)) * 10);
    return `§f${g.name} §6RELOADING §a${"|".repeat(bars)}§8${"|".repeat(10 - bars)}`;
  }
  const mag = magOf(player, held);
  const reserve = reserveOf(player, held);
  const magColor = mag === 0 ? "§c" : mag <= g.mag / 4 ? "§6" : "§f";
  return `§f${g.name} ${magColor}${mag}§7/${g.mag} §8| §7${isCreative(player) ? "∞" : reserve}`;
}

// ------------------------------------------------------------------ AI soldiers' shots

const BOT_SOUNDS = { [id("bullet")]: `${NS}.assault_rifle`, [id("sniper_bullet")]: `${NS}.sniper`, [id("rocket")]: `${NS}.rocket_launch` };
const lastBotSound = new Map();

export function init() {
  onUse((player, item) => {
    if (!GUNS[item.typeId]) return false;
    pullTrigger(player, item.typeId);
    return true;
  });

  world.afterEvents.entitySpawn.subscribe(({ entity }) => {
    const snd = BOT_SOUNDS[entity.typeId];
    if (!snd) return;
    const owner = safe(() => entity.getComponent("minecraft:projectile")?.owner);
    if (!owner || owner.typeId === "minecraft:player") return;
    const loc = safe(() => entity.location);
    if (!loc) return;
    particle(entity.dimension, `${NS}:muzzle_flash`, loc);
    const key = owner.id;
    if ((lastBotSound.get(key) ?? 0) + 2 > system.currentTick) return;
    lastBotSound.set(key, system.currentTick);
    sound(entity.dimension, snd, loc, 0.9, 0.95 + Math.random() * 0.1);
  });

  // Hits by the soldiers' bullets: blood or sparks, a hit to the kill feed, and the damage setting.
  world.afterEvents.projectileHitEntity.subscribe((e) => {
    const type = e.projectile?.typeId;
    if (type !== id("bullet") && type !== id("sniper_bullet")) return;
    const target = safe(() => e.getEntityHit().entity);
    if (!target) return;
    particle(e.dimension, isVehicle(target) ? `${NS}:sparks` : `${NS}:blood`, e.location);
    noteHit(target, type === id("bullet") ? "Rifle" : "Sniper Rifle", false);
    const f = settings().botDamage;
    if (target.typeId === "minecraft:player" && f !== 1) {
      system.run(() => safe(() => {
        const hp = target.getComponent("minecraft:health");
        if (!hp || hp.currentValue <= 0) return;
        const base = type === id("bullet") ? 4 : 13;
        hp.setCurrentValue(Math.max(1, Math.min(hp.effectiveMax, hp.currentValue + base * (1 - f))));
      }));
    }
  });
  world.afterEvents.projectileHitBlock.subscribe((e) => {
    const type = e.projectile?.typeId;
    if (type === id("bullet") || type === id("sniper_bullet")) particle(e.dimension, `${NS}:impact_dust`, e.location);
  });

  system.runInterval(finishReloads, 1);

  // Double-tap crouch to reload (crouching itself steadies the aim).
  /** @type {Map<string, {down: boolean, last: number}>} */
  const sneak = new Map();
  system.runInterval(() => {
    for (const p of players()) {
      const down = safe(() => p.isSneaking) ?? false;
      const s = sneak.get(p.id) ?? { down: false, last: -100 };
      if (down && !s.down) {
        if (system.currentTick - s.last <= 8) {
          const held = safe(() => p.getComponent("minecraft:inventory")?.container?.getItem(p.selectedSlotIndex)?.typeId);
          if (held && GUNS[held]) startReload(p, held);
          s.last = -100;
        } else s.last = system.currentTick;
      }
      s.down = down;
      sneak.set(p.id, s);
    }
  }, 1);
}
