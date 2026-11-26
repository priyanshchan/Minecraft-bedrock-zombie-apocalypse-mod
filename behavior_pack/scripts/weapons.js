// Firearms: the trigger (automatic fire while the trigger is held, single shots, pump and bolt actions), bullets
// handed to the ballistics simulation, the universal recoil (the view kicks up and sideways and recovers) and
// spread (hip, aimed, moving, bloom that grows with sustained fire), magazines and reloads, jams and malfunctions,
// attachments (their effects, their models on the gun, scopes, night vision, lasers and flashlights), the
// third-person aiming pose and the AI soldiers' shots.
import { system, world } from "@minecraft/server";
import {
  add, countItem, cue, getNumber, id, isCreative, isVehicle, normalize, NS, particle, players, safe, scale, settings,
  shake, sound, sub, takeItem, notify, onUse, heldItem, distance,
} from "./core.js";
import { noteHit } from "./teams.js";
import { attachment, fitted, modifiers } from "./attachments.js";
import * as ballistics from "./ballistics.js";
import { GUN_DATA } from "./gundata.js";

/**
 * A gun's stats (from tools/gen/defs.py through gundata.js).
 * @typedef {object} Gun
 * @property {string} key        short name (animations, cooldown category)
 * @property {string} name
 * @property {string} caliber
 * @property {string} ammo       reserve ammunition item
 * @property {number} mag        rounds per magazine
 * @property {"auto" | "semi" | "pump" | "bolt" | "launcher"} mode
 * @property {number} rpm        rounds per minute (semi: the fastest follow-up)
 * @property {number} damage     per bullet or pellet at the muzzle
 * @property {number} [pellets]
 * @property {number} velocity   muzzle velocity, m/s
 * @property {number} drag       fraction of speed lost per block
 * @property {number} headshot   damage multiplier
 * @property {number} hip        spread in degrees, hip fire
 * @property {number} ads        spread in degrees, crouched (aiming)
 * @property {number} vrec       degrees the view kicks up per shot
 * @property {number} hrec       degrees the view kicks sideways (either way) per shot
 * @property {number} bloom      degrees of spread added per shot (decays)
 * @property {string} sound
 * @property {number} jam        chance per round of a stoppage (a quarter of them are malfunctions)
 * @property {"rifle" | "pistol" | "launcher"} pose
 * @property {string} [projectile]  fires this entity instead of a bullet
 * @property {number} [power]       its launch speed
 * @property {Record<Action | "fire", number>} timing  ticks of each animated action
 * @property {string[]} slots
 * @property {number} reload     ticks (timing.reload)
 */
/** @typedef {"reload" | "jam" | "malfunction"} Action */

/** @type {Record<string, Gun>} */
export const GUNS = {};
for (const [gid, g] of Object.entries(/** @type {Record<string, Omit<Gun, "reload">>} */ (/** @type {unknown} */ (GUN_DATA.guns)))) {
  GUNS[gid] = { ...g, reload: g.timing.reload };
}
export const GUN_IDS = Object.keys(GUNS);

/** Where the sights are zeroed, blocks: the bullet crosses the line of sight again there. */
const ZERO = { pistol: 25, rifle: 100, launcher: 50 };
/** Ticks the trigger counts as held after a use (holding the button repeats the use every few ticks). */
const TRIGGER_WINDOW = 5;

/**
 * Tells the gun's 3D model which animation to play: a cooldown of the action's length on the gun's own
 * category (the model reads q.cooldown_time). Also the hotbar shows the action's progress.
 * @param {import("@minecraft/server").Player} player @param {string} gunId @param {Action | "fire"} action
 */
export function animate(player, gunId, action) {
  const g = GUNS[gunId];
  safe(() => player.startItemCooldown(`${NS}_${g.key}`, g.timing[action]));
}

/** @type {Record<string, string[]>} */
const POSE_IDS = { rifle: [], pistol: [], launcher: [] };
for (const [key, g] of Object.entries(GUNS)) POSE_IDS[g.pose].push(key);

// ------------------------------------------------------------------ per-player state

/**
 * @typedef {object} State
 * @property {number} next       tick of the next allowed shot
 * @property {number} trigger    tick until which the trigger is held
 * @property {boolean} firing    an automatic gun is firing
 * @property {number} acc        ticks banked towards the next automatic shot
 * @property {number} bloom      degrees of spread from sustained fire
 * @property {number} owed       degrees of vertical kick not yet recovered
 * @property {number} lastShot
 * @property {string} attKey     the attachments shown on the gun in hand
 * @property {string[]} attShown
 * @property {number} attRefresh
 * @property {boolean} nv        night vision given by a scope
 * @property {number} warned     tick of the last "stopped" warning
 */
/** @type {Map<string, State>} */
const states = new Map();
/** @param {import("@minecraft/server").Player} player @returns {State} */
function stateOf(player) {
  let s = states.get(player.id);
  if (!s) {
    s = { next: 0, trigger: 0, firing: false, acc: 0, bloom: 0, owed: 0, lastShot: -100, attKey: "", attShown: [], attRefresh: 0, nv: false, warned: -100 };
    states.set(player.id, s);
  }
  return s;
}

/** Actions under way (reloads and clearing stoppages). @type {Map<string, {gun: string, done: number, kind: Action}>} */
const reloading = new Map();
/** Guns that have stopped: player -> the gun and what went wrong. @type {Map<string, {gun: string, kind: "jam" | "malfunction"}>} */
const stopped = new Map();

/** The magazine size of a gun item (attachments change it). @param {string} gun @param {import("@minecraft/server").ItemStack | undefined} item */
export function magSizeOf(gun, item) {
  const m = modifiers(item?.typeId === gun ? item : undefined);
  return Math.max(1, Math.round(GUNS[gun].mag * m.mag) + m.mag_add);
}

/** The magazine size of the gun a player holds. @param {import("@minecraft/server").Player} player @param {string} gun */
export function magSize(player, gun) {
  return magSizeOf(gun, heldItem(player));
}

/** Rounds in the magazine of a gun (stored per player and gun type; a new gun comes loaded). @param {import("@minecraft/server").Player} player @param {string} gun */
export function magOf(player, gun) {
  return getNumber(player, `fl:mag:${gun}`, GUNS[gun].mag);
}

/** @param {import("@minecraft/server").Player} player @param {string} gun @param {number} n */
export function setMag(player, gun, n) {
  safe(() => player.setDynamicProperty(`fl:mag:${gun}`, n));
}

/** What stopped a player's gun, if it has. @param {import("@minecraft/server").Player} player @param {string} gun */
export function stoppage(player, gun) {
  const s = stopped.get(player.id);
  return s && s.gun === gun ? s.kind : undefined;
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
    notify(player, `§cNo ${g.caliber} left`);
    return;
  }
  stateOf(player).firing = false;
  const ticks = Math.max(8, Math.round(g.reload * modifiers(heldItem(player)).reload));
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
  reloading.set(player.id, { gun, done: system.currentTick + g.timing[kind], kind });
  animate(player, gun, kind);
  playerMotion(player, kind === "jam" ? "rack" : "reload");
  sound(player.dimension, `${NS}.reload`, player.location, 0.8, kind === "jam" ? 1.4 : 0.9);
  notify(player, kind === "jam" ? "§eClearing the jam..." : "§eClearing the malfunction...", g.timing[kind]);
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
    const got = need <= 0 ? 0 : isCreative(p) ? need : takeItem(p, g.ammo, need);
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

// ------------------------------------------------------------------ spread and recoil

/** A direction turned by a random angle inside a cone of `degrees` (evenly over the cone's disc).
 * @param {import("@minecraft/server").Vector3} dir @param {number} degrees */
export function cone(dir, degrees) {
  if (degrees <= 0) return dir;
  const r = Math.tan((degrees * Math.PI) / 180) * Math.sqrt(Math.random());
  const a = Math.random() * Math.PI * 2;
  // two directions square to dir
  const side = normalize(Math.abs(dir.y) > 0.99 ? { x: 1, y: 0, z: 0 } : { x: -dir.z, y: 0, z: dir.x });
  const up = { x: side.y * dir.z - side.z * dir.y, y: side.z * dir.x - side.x * dir.z, z: side.x * dir.y - side.y * dir.x };
  return normalize(add(dir, add(scale(side, Math.cos(a) * r), scale(up, Math.sin(a) * r))));
}

/** Whether the player is aiming (crouched with a gun). @param {import("@minecraft/server").Player} player */
const aiming = (player) => safe(() => player.isSneaking) ?? false;

/** The spread of the next shot in degrees: hip or aimed, how the player moves, and bloom from sustained fire.
 * @param {import("@minecraft/server").Player} player @param {Gun} g @param {import("./attachments.js").Mods} mods @param {State} st */
export function spreadOf(player, g, mods, st) {
  const aim = aiming(player);
  let s = aim ? g.ads * mods.ads : g.hip * mods.spread;
  if (aim && mods.bipod) s *= 0.5;
  const v = safe(() => player.getVelocity());
  const speed = v ? Math.hypot(v.x, v.z) : 0;
  if (safe(() => player.isSprinting)) s = s * 1.8 + 1;
  else if (speed > 0.05) s *= 1.25 + Math.min(1, speed * 2) * 0.35;
  if (safe(() => player.isOnGround) === false && !safe(() => player.getComponent("minecraft:riding"))) s = s * 1.6 + 1.5;
  return s + st.bloom * (aim ? 0.6 : 1);
}

/** Kicks the view: up by `v` degrees and sideways by `h`. @param {import("@minecraft/server").Player} player @param {State} st @param {number} v @param {number} h */
function kick(player, st, v, h) {
  if (!settings().cameraRecoil) return;
  const r = safe(() => player.getRotation());
  if (!r) return;
  const x = Math.max(-89, r.x - v);
  safe(() => player.setRotation({ x, y: r.y + h }));
  st.owed += r.x - x;
}

/** After a burst the view settles back down by part of the kick. @param {import("@minecraft/server").Player} player @param {State} st */
function recover(player, st) {
  if (st.owed <= 0.05 || system.currentTick - st.lastShot < 3) return;
  const back = Math.min(st.owed, Math.max(0.1, st.owed * 0.18));
  st.owed -= back;
  if (st.owed < 0.4 * back) st.owed = 0;
  if (!settings().cameraRecoil) return;
  const r = safe(() => player.getRotation());
  if (r) safe(() => player.setRotation({ x: Math.min(89, r.x + back * 0.6), y: r.y }));
}

// ------------------------------------------------------------------ shooting

/** Fires one round (or one load of pellets, or a rocket). @param {import("@minecraft/server").Player} player @param {string} gunId @param {Gun} g */
function fireRound(player, gunId, g) {
  const dim = player.dimension;
  const st = stateOf(player);
  const eye = player.getHeadLocation();
  const look = player.getViewDirection();
  const item = heldItem(player);
  const mods = modifiers(item);
  const aim = aiming(player);
  const right = normalize({ x: -look.z, y: 0, z: look.x });
  const muzzle = add(eye, add(scale(look, 1.1), add(scale(right, g.pose === "pistol" ? 0.2 : 0.28), { x: 0, y: -0.2, z: 0 })));

  if (!mods.flash) particle(dim, `${NS}:muzzle_flash`, muzzle);
  particle(dim, `${NS}:gun_smoke`, muzzle);
  const quiet = mods.noise < 0.5;
  sound(dim, quiet ? `${NS}.suppressed` : g.sound, eye, quiet ? 0.9 : Math.min(1.2, Math.max(0.2, mods.noise)), (quiet ? 1.1 : 0.95) + Math.random() * 0.1);
  animate(player, gunId, "fire");

  if (g.projectile) {
    const proj = safe(() => dim.spawnEntity(g.projectile ?? "", add(eye, scale(look, 1.4))));
    const comp = proj ? safe(() => proj.getComponent("minecraft:projectile")) : undefined;
    if (comp) {
      comp.owner = player;
      safe(() => comp.shoot(scale(cone(look, spreadOf(player, g, mods, st)), g.power ?? 2.5)));
    }
  } else {
    const spreadDeg = spreadOf(player, g, mods, st);
    const speed = (g.velocity * mods.velocity) / 20; // m/s to blocks a tick
    const base = ballistics.zeroed(look, speed, ZERO[g.pose] ?? 100);
    const pellets = g.pellets ?? 1;
    for (let i = 0; i < pellets; i++) {
      // pellets fan out around the aim point; the whole load also wanders by the shooter's spread
      const dir = pellets > 1 ? cone(base, i === 0 ? spreadDeg * 0.3 : spreadDeg) : cone(base, spreadDeg);
      ballistics.launch(player, eye, dir, {
        speed: speed * (pellets > 1 ? 0.94 + Math.random() * 0.12 : 1), drag: g.drag, damage: g.damage * mods.damage,
        headshot: g.headshot, weapon: g.name, tracer: pellets === 1 || i % 3 === 0,
      });
    }
  }

  // recoil: the view kicks up and to a random side; spread blooms; a little camera shake
  const braced = aim && mods.bipod ? 0.4 : 1;
  const v = g.vrec * mods.vrec * (aim ? 0.85 : 1) * braced * (0.8 + Math.random() * 0.4);
  const h = g.hrec * mods.hrec * (Math.random() * 2 - 1) * braced;
  kick(player, st, v, h);
  st.bloom = Math.min(g.bloom * 12, st.bloom + g.bloom * ((mods.vrec + mods.hrec) / 2));
  st.lastShot = system.currentTick;
  shake(player, Math.min(0.25, 0.015 + g.vrec * 0.02 * mods.vrec * braced), 0.06);
}

/** One round off the magazine and out of the barrel, if the gun can fire. Returns false when it cannot.
 * @param {import("@minecraft/server").Player} player @param {string} gunId */
function shoot(player, gunId) {
  const g = GUNS[gunId];
  if (!safe(() => player.isValid)) return false;
  if (heldItem(player)?.typeId !== gunId || reloading.has(player.id) || stoppage(player, gunId)) return false;
  const mag = magOf(player, gunId);
  if (mag <= 0) {
    cue(player, `${NS}.dry_fire`);
    startReload(player, gunId);
    return false;
  }
  setMag(player, gunId, mag - 1);
  safe(() => fireRound(player, gunId, g));
  // A stoppage now and then: a jam (tap, rack) or, a quarter of the time, a malfunction (strip, rack, reload).
  if (settings().malfunctions && mag - 1 > 0 && Math.random() < g.jam) {
    const kind = Math.random() < 0.25 ? "malfunction" : "jam";
    stopped.set(player.id, { gun: gunId, kind });
    stateOf(player).firing = false;
    system.runTimeout(() => {
      cue(player, `${NS}.dry_fire`, 1, 0.8);
      notify(player, kind === "jam" ? "§cJAMMED §7- double-tap crouch to clear it" : "§cMALFUNCTION §7- double-tap crouch to clear it", 60);
    }, 2);
    return false;
  }
  if (mag - 1 <= 0) {
    stateOf(player).firing = false;
    system.runTimeout(() => startReload(player, gunId), 6);
    return false;
  }
  return true;
}

/** The trigger is pressed (each use of the gun; holding the button repeats it).
 * @param {import("@minecraft/server").Player} player @param {string} gunId */
export function pullTrigger(player, gunId) {
  const g = GUNS[gunId];
  const now = system.currentTick;
  const st = stateOf(player);
  if (reloading.has(player.id)) return;
  const stuck = stoppage(player, gunId);
  if (stuck) {
    if (now - st.warned > 6) {
      st.warned = now;
      cue(player, `${NS}.dry_fire`);
      notify(player, stuck === "jam" ? "§cJAMMED §7- double-tap crouch to clear it" : "§cMALFUNCTION §7- double-tap crouch to clear it");
    }
    return;
  }
  if (g.mode === "auto") {
    st.trigger = now + TRIGGER_WINDOW;
    if (!st.firing && st.next <= now) {
      st.firing = true;
      st.acc = 0;
      if (!shoot(player, gunId)) st.firing = false;
      st.next = now + 1;
    }
    return;
  }
  if (st.next > now) return;
  // single shots: semi-automatics as fast as the trigger allows; pump and bolt guns once the action has cycled
  const cycle = g.mode === "pump" || g.mode === "bolt" || g.mode === "launcher" ? g.timing.fire : 0;
  st.next = now + Math.max(cycle, Math.ceil(1200 / g.rpm));
  shoot(player, gunId);
}

/** Automatic fire while the trigger is held, at the gun's rate of fire. */
function autoFire() {
  const now = system.currentTick;
  for (const p of players()) {
    const st = states.get(p.id);
    if (!st) continue;
    st.bloom = Math.max(0, st.bloom - (0.06 + st.bloom * 0.12));
    if (st.firing) {
      const gunId = heldItem(p)?.typeId;
      const g = gunId ? GUNS[gunId] : undefined;
      if (!g || !gunId || g.mode !== "auto" || now > st.trigger) {
        st.firing = false;
      } else {
        st.acc += 1;
        const interval = 1200 / g.rpm;
        while (st.firing && st.acc >= interval) {
          st.acc -= interval;
          if (!shoot(p, gunId)) st.firing = false;
        }
      }
    }
    if (!st.firing) recover(p, st);
  }
}

// ------------------------------------------------------------------ attachments on the gun in hand

const LIGHT_BLOCK = "minecraft:light_block_13";
/** Where each player's flashlight lights the world. @type {Map<string, {dim: string, x: number, y: number, z: number}>} */
const lights = new Map();

function saveLights() {
  safe(() => world.setDynamicProperty("fl:lights", JSON.stringify([...lights.values()])));
}

/** @param {{dim: string, x: number, y: number, z: number}} at */
function clearLight(at) {
  safe(() => {
    const b = world.getDimension(at.dim).getBlock(at);
    if (b && b.typeId.startsWith("minecraft:light_block")) b.setType("minecraft:air");
  });
}

/** Moves a player's flashlight spot to `at` (or turns it off). @param {import("@minecraft/server").Player} player @param {import("@minecraft/server").Vector3 | undefined} at */
function setLight(player, at) {
  const prev = lights.get(player.id);
  const next = at ? { dim: player.dimension.id, x: Math.floor(at.x), y: Math.floor(at.y), z: Math.floor(at.z) } : undefined;
  if (prev && next && prev.dim === next.dim && prev.x === next.x && prev.y === next.y && prev.z === next.z) return;
  if (prev) {
    clearLight(prev);
    lights.delete(player.id);
  }
  if (next) {
    const placed = safe(() => {
      const b = player.dimension.getBlock(next);
      if (!b || !b.isAir) return false;
      b.setType(LIGHT_BLOCK);
      return true;
    });
    if (placed) lights.set(player.id, next);
  }
  saveLights();
}

/** Where the player's aim meets a block or body, up to `max` blocks. @param {import("@minecraft/server").Player} player @param {number} max */
function aimPoint(player, max) {
  const eye = player.getHeadLocation();
  const look = player.getViewDirection();
  const hit = safe(() => player.dimension.getBlockFromRay(eye, look, { maxDistance: max, includeLiquidBlocks: false, includePassableBlocks: false }));
  let d = hit ? distance(eye, add(hit.block.location, hit.faceLocation)) : max;
  const ents = safe(() => player.dimension.getEntitiesFromRay(eye, look, { maxDistance: d, excludeTypes: ["minecraft:item"] })) ?? [];
  const first = ents.find((h) => h.entity !== player);
  if (first) d = first.distance;
  return { eye, look, d, hit: Boolean(hit || first) };
}

/** Keeps the gun in hand showing its fitted attachments: their cooldown categories run while it is held. Also the
 * scope's zoom and night vision while aiming. @param {import("@minecraft/server").Player} player @param {import("@minecraft/server").ItemStack | undefined} item @param {State} st */
function syncAttachments(player, item, st) {
  const gun = item && GUNS[item.typeId] ? item : undefined;
  const ids = gun ? Object.values(fitted(gun)).filter((a) => a && attachment(a)).map(String).sort() : [];
  const now = system.currentTick;
  const key = `${gun?.typeId ?? ""}|${ids.join(",")}`;
  if (key !== st.attKey) {
    for (const old of st.attShown) {
      if (!ids.includes(old)) safe(() => player.startItemCooldown(attachment(old)?.category ?? "", 1));
    }
    st.attKey = key;
    st.attShown = ids;
    st.attRefresh = 0;
  }
  if (ids.length && now >= st.attRefresh) {
    for (const a of ids) safe(() => player.startItemCooldown(attachment(a)?.category ?? "", 60));
    st.attRefresh = now + 40;
  }
}

/** Scopes, night vision, lasers and flashlights for one player. @param {import("@minecraft/server").Player} player @param {State} st @param {number} n */
function gunExtras(player, st, n) {
  const item = heldItem(player);
  const g = item ? GUNS[item.typeId] : undefined;
  syncAttachments(player, item, st);
  const mods = g ? modifiers(item) : undefined;
  const aim = g && aiming(player);
  if (n % 5 === 0) {
    if (mods && aim && mods.zoom >= 2) {
      // magnification: slowness narrows the field of view (with "FOV changes" on in Video settings)
      const amp = mods.zoom >= 12 ? 4 : mods.zoom >= 8 ? 3 : mods.zoom >= 6 ? 2 : mods.zoom >= 3 ? 1 : 0;
      safe(() => player.addEffect("slowness", 12, { amplifier: amp, showParticles: false }));
    }
    if (mods && aim && mods.nv) {
      safe(() => player.addEffect("night_vision", 400, { amplifier: 0, showParticles: false }));
      st.nv = true;
    } else if (st.nv) {
      st.nv = false;
      safe(() => player.removeEffect("night_vision"));
    }
  }
  if (mods && mods.laser && n % 2 === 0) {
    const { eye, look, d, hit } = aimPoint(player, 80);
    if (hit) particle(player.dimension, `${NS}:laser_dot`, add(eye, scale(look, d - 0.05)));
    const right = normalize({ x: -look.z, y: 0, z: look.x });
    const from = add(eye, add(scale(look, 0.9), add(scale(right, 0.3), { x: 0, y: -0.22, z: 0 })));
    const to = add(eye, scale(look, Math.min(d, 18)));
    const span = sub(to, from);
    const len = Math.hypot(span.x, span.y, span.z);
    for (let t = 1.2; t < len; t += 1.2) particle(player.dimension, `${NS}:laser_beam`, add(from, scale(span, t / len)));
  }
  if (n % 3 === 0) {
    if (mods && mods.light) {
      const { eye, look, d } = aimPoint(player, 28);
      setLight(player, add(eye, scale(look, Math.max(1.5, d - 0.6))));
    } else if (lights.has(player.id)) setLight(player, undefined);
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

const MODE_LABEL = { auto: "AUTO", semi: "SEMI", pump: "PUMP", bolt: "BOLT", launcher: "" };

/** The ammo readout for the HUD. @param {import("@minecraft/server").Player} player @param {string} held */
export function ammoText(player, held) {
  const g = GUNS[held];
  if (!g) return "";
  const r = reloading.get(player.id);
  if (r) {
    const total = r.kind === "reload" ? Math.max(8, Math.round(g.reload * modifiers(heldItem(player)).reload)) : g.timing[r.kind];
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
  const mode = MODE_LABEL[g.mode];
  return `§f${g.name} §8${g.caliber}${mode ? ` ${mode}` : ""} ${magColor}${mag}§7/${size} §8| §7${isCreative(player) ? "∞" : reserve}`;
}

// ------------------------------------------------------------------ AI soldiers' shots

/** The gun each kind of soldier carries: its sound and its name in the kill feed. */
const BOT_GUNS = {
  [id("nato_rifleman")]: ["assault_rifle", "Colt M4A1"], [id("nato_marksman")]: ["sniper", "AI AWM"],
  [id("nato_heavy")]: ["rocket_launch", "Carl Gustaf M4"], [id("redfang_fighter")]: ["ak47", "AKM"],
  [id("redfang_sniper")]: ["dmr", "SVD Dragunov"], [id("redfang_rpg")]: ["rocket_launch", "RPG-7"],
};
const lastBotSound = new Map();
/** The soldier who fired each AI projectile still in the air (for the kill feed). @type {Map<string, string>} */
const botShooter = new Map();

export function init() {
  ballistics.init();
  // Clear flashlight spots left by a world that closed with a light on.
  safe(() => {
    const raw = world.getDynamicProperty("fl:lights");
    if (typeof raw === "string") for (const at of JSON.parse(raw)) clearLight(at);
    world.setDynamicProperty("fl:lights", undefined);
  });

  onUse((player, item) => {
    if (!GUNS[item.typeId]) return false;
    pullTrigger(player, item.typeId);
    return true;
  });

  world.afterEvents.entitySpawn.subscribe(({ entity }) => {
    if (entity.typeId !== id("bullet") && entity.typeId !== id("sniper_bullet") && entity.typeId !== id("rocket")) return;
    const owner = safe(() => entity.getComponent("minecraft:projectile")?.owner);
    if (!owner || owner.typeId === "minecraft:player") return;
    const loc = safe(() => entity.location);
    if (!loc) return;
    const [snd, name] = BOT_GUNS[owner.typeId] ?? ["assault_rifle", "Rifle"];
    botShooter.set(entity.id, name);
    if (botShooter.size > 400) botShooter.delete(botShooter.keys().next().value ?? "");
    particle(entity.dimension, `${NS}:muzzle_flash`, loc);
    const key = owner.id;
    if ((lastBotSound.get(key) ?? 0) + 2 > system.currentTick) return;
    lastBotSound.set(key, system.currentTick);
    sound(entity.dimension, `${NS}.${snd}`, loc, 0.9, 0.95 + Math.random() * 0.1);
  });

  // Hits by the soldiers' bullets: blood or sparks, a hit to the kill feed, and the damage setting.
  world.afterEvents.projectileHitEntity.subscribe((e) => {
    const type = e.projectile?.typeId;
    if (type !== id("bullet") && type !== id("sniper_bullet")) return;
    const target = safe(() => e.getEntityHit().entity);
    if (!target) return;
    particle(e.dimension, isVehicle(target) ? `${NS}:sparks` : `${NS}:blood`, e.location);
    const shooter = safe(() => botShooter.get(e.projectile.id));
    noteHit(target, shooter ?? (type === id("bullet") ? "Rifle" : "Sniper Rifle"), false);
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
  system.runInterval(autoFire, 1);
  let n = 0;
  system.runInterval(() => {
    n++;
    for (const p of players()) safe(() => gunExtras(p, stateOf(p), n));
  }, 1);

  // Double-tap crouch to reload (crouching itself aims).
  /** @type {Map<string, {down: boolean, last: number}>} */
  const sneak = new Map();
  system.runInterval(() => {
    for (const p of players()) {
      const down = safe(() => p.isSneaking) ?? false;
      const s = sneak.get(p.id) ?? { down: false, last: -100 };
      if (down && !s.down) {
        if (system.currentTick - s.last <= 8) {
          const held = heldItem(p)?.typeId;
          if (held && GUNS[held]) startReload(p, held);
          s.last = -100;
        } else s.last = system.currentTick;
      }
      s.down = down;
      sneak.set(p.id, s);
    }
  }, 1);
}
