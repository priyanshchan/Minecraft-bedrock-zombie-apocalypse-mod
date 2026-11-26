// Firearms: hitscan shots with spread, magazines and reloads, headshots, tracers and muzzle flashes, the
// third-person aiming pose, and the effects of the AI soldiers' shots.
import { EntityDamageCause, system, world } from "@minecraft/server";
import {
  add, countItem, cue, distance, dot, getNumber, id, isCreative, isSoldier, isVehicle, normalize, NS, particle, players,
  safe, sameTeam, scale, settings, shake, sound, spread, sub, takeItem, notify, onUse, heldItem,
} from "./core.js";
import { noteHit } from "./teams.js";
import { modifiers } from "./attachments.js";
import { GUN_DATA } from "./gundata.js";

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
 * @property {string} key          short name (animations, cooldown category)
 * @property {number} jam          chance per round of a stoppage (a quarter of them are malfunctions)
 */

/** @type {Record<string, Omit<Gun, "key" | "reload"> & {reload?: number}>} */
const STATS = {
  [id("service_pistol")]: { name: "Service Pistol", ammo: id("pistol_ammo"), mag: 12, damage: 6, rate: 5, spread: 1.6, range: 48, sound: `${NS}.pistol`, pose: "pistol", headshot: 1.8, kick: 0.04, jam: 0.0025 },
  [id("smg")]: { name: "Talon SMG", ammo: id("pistol_ammo"), mag: 30, damage: 4, rate: 6, burst: 3, spread: 3.0, range: 40, sound: `${NS}.smg`, pose: "rifle", headshot: 1.6, kick: 0.03, jam: 0.004 },
  [id("assault_rifle")]: { name: "Vanguard AR", ammo: id("rifle_ammo"), mag: 30, damage: 6, rate: 8, burst: 3, spread: 1.6, range: 90, sound: `${NS}.assault_rifle`, pose: "rifle", headshot: 1.8, kick: 0.05, jam: 0.0035 },
  [id("lmg")]: { name: "Bulwark LMG", ammo: id("rifle_ammo"), mag: 100, damage: 5, rate: 10, burst: 5, spread: 2.8, range: 90, sound: `${NS}.lmg`, pose: "rifle", headshot: 1.6, kick: 0.06, jam: 0.005 },
  [id("shotgun")]: { name: "Breacher Shotgun", ammo: id("shotgun_shells"), mag: 6, damage: 3.5, pellets: 8, rate: 16, spread: 7, range: 22, sound: `${NS}.shotgun`, pose: "rifle", headshot: 1.3, kick: 0.12, jam: 0.006 },
  [id("sniper_rifle")]: { name: "Longshot Sniper", ammo: id("sniper_rounds"), mag: 5, damage: 22, rate: 30, spread: 0.3, range: 220, sound: `${NS}.sniper`, pose: "rifle", headshot: 2.5, kick: 0.15, jam: 0.002 },
  [id("rocket_launcher")]: { name: "Hornet Launcher", ammo: id("rocket"), mag: 1, damage: 0, rate: 20, spread: 0.4, range: 0, sound: `${NS}.rocket_launch`, pose: "launcher", projectile: id("rocket"), kick: 0.2, jam: 0.01 },
};

/** Ticks of each animated action of a gun, from the generated gun data (the 3D model's animations match). */
const TIMING = /** @type {Record<string, Record<"fire" | "reload" | "jam" | "malfunction", number>>} */ (GUN_DATA.timing);

/** @type {Record<string, Gun>} */
export const GUNS = Object.fromEntries(Object.entries(STATS).map(([gid, st]) => {
  const key = gid.replace(`${NS}:`, "");
  return [gid, { ...st, key, reload: TIMING[key].reload }];
}));

/**
 * Tells the gun's 3D model which animation to play: a cooldown of the action's length on the gun's own
 * category (the model reads q.cooldown_time). Also the hotbar shows the action's progress.
 * @param {import("@minecraft/server").Player} player @param {string} gunId @param {"fire" | "reload" | "jam" | "malfunction"} action
 */
export function animate(player, gunId, action) {
  const g = GUNS[gunId];
  safe(() => player.startItemCooldown(`${NS}_${g.key}`, TIMING[g.key][action]));
}

export const GUN_IDS = Object.keys(GUNS);
/** @type {Record<string, string[]>} */
const POSE_IDS = { rifle: [], pistol: [], launcher: [] };
for (const [key, g] of Object.entries(GUNS)) POSE_IDS[g.pose].push(key);

/** Ticks until which each player cannot fire, and actions under way (reloads and clearing stoppages). */
const nextShot = new Map();
/** @typedef {"reload" | "jam" | "malfunction"} Action */
/** @type {Map<string, {gun: string, done: number, kind: Action}>} */
const reloading = new Map();
/** Guns that have stopped: player -> the gun and what went wrong. @type {Map<string, {gun: string, kind: "jam" | "malfunction"}>} */
const stopped = new Map();

/** The magazine size of the gun a player holds, with attachments (extended magazines). @param {import("@minecraft/server").Player} player @param {string} gun */
export function magSize(player, gun) {
  const item = heldItem(player);
  return GUNS[gun].mag + (item?.typeId === gun ? modifiers(item).magazine : 0);
}

/** Rounds in the magazine of a gun (stored per player and gun type; a new gun comes loaded). @param {import("@minecraft/server").Player} player @param {string} gun */
export function magOf(player, gun) {
  return getNumber(player, `fl:mag:${gun}`, GUNS[gun].mag);
}

/** What stopped a player's gun, if it has. @param {import("@minecraft/server").Player} player @param {string} gun */
export function stoppage(player, gun) {
  const s = stopped.get(player.id);
  return s && s.gun === gun ? s.kind : undefined;
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
  if (reloading.has(player.id)) return;
  if (stoppage(player, gun)) {
    clearStoppage(player, gun);
    return;
  }
  if (magOf(player, gun) >= magSize(player, gun)) return;
  if (reserveOf(player, gun) <= 0) {
    cue(player, `${NS}.dry_fire`);
    notify(player, `§cNo ${g.ammo.replace(`${NS}:`, "").replace(/_/g, " ")} left`);
    return;
  }
  const ticks = Math.round(g.reload * modifiers(heldItem(player)).reload);
  reloading.set(player.id, { gun, done: system.currentTick + ticks, kind: "reload" });
  animate(player, gun, "reload");
  playerMotion(player, "reload");
  sound(player.dimension, `${NS}.reload`, player.location, 0.9, 30 / g.reload + 0.4);
}

/** Clears a jam (tap and rack) or a malfunction (strip the magazine, rack, reload): the action the stoppage needs.
 * @param {import("@minecraft/server").Player} player @param {string} gun */
export function clearStoppage(player, gun) {
  const kind = stoppage(player, gun);
  if (!kind || reloading.has(player.id)) return;
  const g = GUNS[gun];
  reloading.set(player.id, { gun, done: system.currentTick + TIMING[g.key][kind], kind });
  animate(player, gun, kind);
  playerMotion(player, kind === "jam" ? "rack" : "reload");
  sound(player.dimension, `${NS}.reload`, player.location, 0.8, kind === "jam" ? 1.4 : 0.9);
  notify(player, kind === "jam" ? "§eClearing the jam..." : "§eClearing the malfunction...", TIMING[g.key][kind]);
}

/** The arm motion seen by others (third person) while reloading or racking. @param {import("@minecraft/server").Player} player @param {"reload" | "rack"} motion */
function playerMotion(player, motion) {
  safe(() => player.playAnimation(`animation.${NS}.player.${motion}`, { controller: `${NS}_action`, blendOutTime: 0.2 }));
}

function finishReloads() {
  const now = system.currentTick;
  for (const p of players()) {
    const r = reloading.get(p.id);
    if (!r || r.done > now) continue;
    reloading.delete(p.id);
    const g = GUNS[r.gun];
    if (r.kind === "jam") {
      stopped.delete(p.id);
      setMag(p, r.gun, Math.max(0, magOf(p, r.gun) - 1)); // the stuck round is thrown out
      cue(p, `${NS}.click`, 0.8, 1.2);
      notify(p, "§aCleared");
      continue;
    }
    if (r.kind === "malfunction") {
      stopped.delete(p.id);
      setMag(p, r.gun, Math.max(0, magOf(p, r.gun) - 2)); // two rounds lost in the double feed
    }
    const need = magSize(p, r.gun) - magOf(p, r.gun);
    const got = isCreative(p) ? need : takeItem(p, g.ammo, need);
    setMag(p, r.gun, magOf(p, r.gun) + got);
    cue(p, `${NS}.click`, 0.8, 1.2);
    if (r.kind === "malfunction") notify(p, "§aCleared and reloaded");
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
  const mods = modifiers(heldItem(player));
  const steady = (player.isSneaking ? 0.45 : player.isSprinting ? 1.8 : 1) * mods.spread;
  const range = g.range * mods.range;
  const muzzle = add(eye, add(scale(look, 0.9), { x: -look.z * 0.25, y: -0.18, z: look.x * 0.25 }));
  particle(dim, `${NS}:muzzle_flash`, muzzle);
  particle(dim, `${NS}:gun_smoke`, muzzle);
  sound(dim, g.sound, eye, Math.max(0.15, mods.noise), 0.95 + Math.random() * 0.1);
  shake(player, (g.kick ?? 0.05) * mods.recoil, 0.08);
  animate(player, gunId, "fire");

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
    const block = safe(() => dim.getBlockFromRay(eye, dir, { maxDistance: range, includeLiquidBlocks: false, includePassableBlocks: false }));
    const wall = block ? distance(eye, add(block.block.location, block.faceLocation)) : range;
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
    let dmg = g.damage * mods.damage * (at > range * 0.6 ? 0.75 : 1) * (head ? g.headshot ?? 1.5 : 1);
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
  const stuck = stoppage(player, gunId);
  if (stuck) {
    nextShot.set(player.id, now + 6);
    cue(player, `${NS}.dry_fire`);
    notify(player, stuck === "jam" ? "§cJAMMED §7- double-tap crouch to clear it" : "§cMALFUNCTION §7- double-tap crouch to clear it");
    return;
  }
  const rounds = g.burst ?? 1;
  nextShot.set(player.id, now + g.rate + (rounds - 1) * 2);
  for (let i = 0; i < rounds; i++) {
    const fire = () => {
      if (!safe(() => player.isValid)) return;
      const held = safe(() => player.getComponent("minecraft:inventory")?.container?.getItem(player.selectedSlotIndex)?.typeId);
      if (held !== gunId || reloading.has(player.id) || stoppage(player, gunId)) return;
      const mag = magOf(player, gunId);
      if (mag <= 0) {
        cue(player, `${NS}.dry_fire`);
        startReload(player, gunId);
        return;
      }
      setMag(player, gunId, mag - 1);
      safe(() => fireRound(player, gunId, g));
      // A stoppage now and then: a jam (tap, rack) or, a quarter of the time, a malfunction (strip, rack, reload).
      if (settings().malfunctions && mag - 1 > 0 && Math.random() < g.jam) {
        const kind = Math.random() < 0.25 ? "malfunction" : "jam";
        stopped.set(player.id, { gun: gunId, kind });
        system.runTimeout(() => {
          cue(player, `${NS}.dry_fire`, 1, 0.8);
          notify(player, kind === "jam" ? "§cJAMMED §7- double-tap crouch to clear it" : "§cMALFUNCTION §7- double-tap crouch to clear it", 60);
        }, 2);
        return;
      }
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
    const total = r.kind === "reload" ? g.reload : TIMING[g.key][r.kind];
    const pct = 1 - (r.done - system.currentTick) / total;
    const bars = Math.round(Math.max(0, Math.min(1, pct)) * 10);
    const what = r.kind === "reload" ? "RELOADING" : r.kind === "jam" ? "CLEARING JAM" : "CLEARING MALFUNCTION";
    return `§f${g.name} §6${what} §a${"|".repeat(bars)}§8${"|".repeat(10 - bars)}`;
  }
  const stuck = stoppage(player, held);
  if (stuck) return `§f${g.name} §c${stuck === "jam" ? "JAMMED" : "MALFUNCTION"} §7- double-tap crouch`;
  const mag = magOf(player, held);
  const size = magSize(player, held);
  const reserve = reserveOf(player, held);
  const magColor = mag === 0 ? "§c" : mag <= size / 4 ? "§6" : "§f";
  return `§f${g.name} ${magColor}${mag}§7/${size} §8| §7${isCreative(player) ? "∞" : reserve}`;
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
