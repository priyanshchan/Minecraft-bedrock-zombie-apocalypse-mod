// A small stand-in for @minecraft/server: enough of the world for the add-on's scripts to run in Node.
// Flat terrain (stone up to y 63, air above), entities with tags, health, projectiles, riders and properties.

const signal = () => {
  const subs = [];
  return { subscribe: (f) => (subs.push(f), f), unsubscribe: (f) => subs.splice(subs.indexOf(f), 1), fire: (e) => subs.forEach((f) => f(e)) };
};

export let tick = 0;
const timers = [];
export const system = {
  get currentTick() { return tick; },
  run: (f) => (timers.push({ at: tick + 1, f }), 1),
  runTimeout: (f, t = 1) => (timers.push({ at: tick + Math.max(1, t), f }), 1),
  runInterval: (f, t = 1) => (timers.push({ every: Math.max(1, t), f }), 1),
};
export async function advance(n) {
  for (let i = 0; i < n; i++) {
    tick++;
    for (const t of [...timers]) {
      if (t.every ? tick % t.every === 0 : t.at === tick) {
        t.f();
        if (!t.every) timers.splice(timers.indexOf(t), 1);
      }
    }
    await Promise.resolve();
  }
}

export const GameMode = { Survival: "Survival", Creative: "Creative", Adventure: "Adventure", Spectator: "Spectator" };
export const EntityDamageCause = { projectile: "projectile", entityAttack: "entityAttack", entityExplosion: "entityExplosion", none: "none" };
export const DisplaySlotId = { List: "List", Sidebar: "Sidebar", BelowName: "BelowName" };
export const ObjectiveSortOrder = { Ascending: 0, Descending: 1 };
export const EquipmentSlot = { Head: "Head", Chest: "Chest", Legs: "Legs", Feet: "Feet", Mainhand: "Mainhand", Offhand: "Offhand" };
export const EntityInitializationCause = { Spawned: "Spawned", Loaded: "Loaded" };
export const EffectTypes = { get: (n) => ({ id: n }) };
export class BlockVolume { constructor(from, to) { this.from = from; this.to = to; } }
export const BlockPermutation = { resolve: (t) => ({ type: { id: t } }) };

export class ItemStack {
  constructor(typeId, amount = 1) {
    this.typeId = typeId;
    this.amount = amount;
    const single = ["glock17", "m1911", "mp5", "ump45", "m4a1", "ak47", "m249", "rem870", "awm", "svd", "carl_gustaf", "rpg7",
      "combat_knife", "field_radio", "binoculars", "repair_tool", "jeep_kit", "tank_kit"].map((n) => `frontline:${n}`);
    this.maxAmount = single.includes(typeId) || /helmet|chestplate/.test(typeId) ? 1 : typeId.endsWith("grenade") ? 4 : 64;
    this.props = new Map();
  }
  getDynamicProperty(k) { return this.props.get(k); }
  setDynamicProperty(k, v) { if (v === undefined) this.props.delete(k); else this.props.set(k, v); }
}

// ------------------------------------------------------------------ blocks
const blocks = new Map();
const key = (l) => `${Math.floor(l.x)},${Math.floor(l.y)},${Math.floor(l.z)}`;
export const placed = [];
function blockAt(dim, l) {
  const k = key(l);
  const type = blocks.get(k) ?? (Math.floor(l.y) <= 63 ? "minecraft:stone" : "minecraft:air");
  return {
    typeId: type, location: { x: Math.floor(l.x), y: Math.floor(l.y), z: Math.floor(l.z) }, dimension: dim,
    get isAir() { return this.typeId === "minecraft:air"; }, isLiquid: false,
    setType(t) { blocks.set(k, t); placed.push({ at: k, type: t }); this.typeId = t; },
  };
}
export const getBlockType = (l) => blocks.get(key(l)) ?? (Math.floor(l.y) <= 63 ? "minecraft:stone" : "minecraft:air");

// ------------------------------------------------------------------ entities
let nextId = 1;
export const entities = [];
export const sounds = [];
export const particles = [];
export const explosions = [];
export const commands = [];

function makeEntity(typeId, location, dim) {
  const e = {
    id: String(nextId++), typeId, location: { ...location }, dimension: dim, isValid: true, nameTag: "",
    tags: new Set(), props: new Map(), dyn: new Map(), effects: new Map(), events: [], anims: [], rotation: { x: 0, y: 0 },
    isSneaking: false, isSprinting: false, view: { x: 0, y: 0, z: 1 }, riders: [], ridingOn: undefined,
    health: { currentValue: 20, effectiveMax: 20, setCurrentValue(v) { this.currentValue = v; return true; } },
    hasTag(t) { return this.tags.has(t); }, addTag(t) { this.tags.add(t); return true; }, removeTag(t) { return this.tags.delete(t); },
    getTags() { return [...this.tags]; },
    getProperty(k) { return this.props.get(k); }, setProperty(k, v) { this.props.set(k, v); },
    getDynamicProperty(k) { return this.dyn.get(k); }, setDynamicProperty(k, v) { if (v === undefined) this.dyn.delete(k); else this.dyn.set(k, v); },
    triggerEvent(ev) { this.events.push(ev); if (ev.endsWith("paint_redfang")) this.props.set("frontline:team", 1); },
    remove() { this.isValid = false; const i = entities.indexOf(this); if (i >= 0) entities.splice(i, 1); },
    getRotation() { return { ...this.rotation }; }, setRotation(r) { this.rotation = { ...r }; },
    teleport(l) { this.location = { ...l }; },
    getHeadLocation() { return { x: this.location.x, y: this.location.y + 1.62, z: this.location.z }; },
    getViewDirection() { return this.view; },
    addEffect(t, d, o) { this.effects.set(typeof t === "string" ? t : t.id, { d, o }); },
    removeEffect(t) { return this.effects.delete(typeof t === "string" ? t : t.id); },
    getVelocity() { return { x: 0, y: 0, z: 0 }; }, isOnGround: true,
    playAnimation(n, o) { this.anims.push({ n, o }); },
    runCommand(c) { commands.push(c); return { successCount: 1 }; },
    matches(q) { return (q.families ?? []).every((f) => familiesOf(this).includes(f)); },
    applyDamage(n, opts) {
      if (!this.isValid) return false;
      this.health.currentValue -= n;
      world.afterEvents.entityHurt.fire({ hurtEntity: this, damage: n, damageSource: { cause: opts?.cause ?? "none", damagingEntity: opts?.damagingEntity } });
      if (this.health.currentValue <= 0) kill(this, opts?.damagingEntity);
      return true;
    },
    getEntitiesFromViewDirection(o) { return raycast(this.dimension, this.getHeadLocation(), this.view, o?.maxDistance ?? 64, this); },
    getComponent(c) {
      const self = this;
      if (c === "minecraft:health") return this.health;
      if (c === "minecraft:projectile") return this.projectile;
      if (c === "minecraft:rideable") return { getRiders: () => self.riders };
      if (c === "minecraft:riding") return self.ridingOn ? { entityRidingOn: self.ridingOn } : undefined;
      if (c === "minecraft:inventory") return this.inventory ? { container: this.inventory } : undefined;
      if (c === "minecraft:equippable") return this.equipment;
      return undefined;
    },
  };
  if (typeId.endsWith("bullet") || typeId.endsWith("rocket") || typeId.endsWith("shell") || typeId.endsWith("grenade")) {
    e.projectile = { owner: undefined, shot: undefined, shoot(v) { this.shot = v; } };
  }
  if (typeId === "frontline:tank") e.health = { ...e.health, currentValue: 400, effectiveMax: 400 };
  if (typeId === "frontline:jeep") e.health = { ...e.health, currentValue: 120, effectiveMax: 120 };
  if (/nato_|redfang_/.test(typeId)) e.health = { ...e.health, currentValue: 30, effectiveMax: 30 };
  return e;
}

export function familiesOf(e) {
  if (/frontline:nato_/.test(e.typeId)) return ["frontline_soldier", "nato", "human", "mob"];
  if (/frontline:redfang_/.test(e.typeId)) return ["frontline_soldier", "redfang", "human", "mob"];
  if (e.typeId === "minecraft:player") return ["player"];
  if (e.typeId === "frontline:jeep" || e.typeId === "frontline:tank") return ["frontline_vehicle"];
  return [];
}

export function kill(e, killer) {
  if (!e.isValid) return;
  world.afterEvents.entityDie.fire({ deadEntity: e, damageSource: { damagingEntity: killer, cause: "entityAttack" } });
  if (e.typeId !== "minecraft:player") e.remove();
  else e.health.currentValue = 0;
}

function raycast(dim, origin, dir, max, exclude) {
  const hits = [];
  for (const e of entities) {
    if (e === exclude || e.dimension !== dim || !e.isValid) continue;
    const c = { x: e.location.x, y: e.location.y + 0.9, z: e.location.z };
    const rel = { x: c.x - origin.x, y: c.y - origin.y, z: c.z - origin.z };
    const t = rel.x * dir.x + rel.y * dir.y + rel.z * dir.z;
    if (t < 0 || t > max) continue;
    const p = { x: origin.x + dir.x * t, y: origin.y + dir.y * t, z: origin.z + dir.z * t };
    if (Math.hypot(p.x - c.x, p.z - c.z) < 0.6 && Math.abs(p.y - c.y) < 1.1) hits.push({ entity: e, distance: t });
  }
  return hits.sort((a, b) => a.distance - b.distance);
}

function matchQuery(e, q, dim) {
  if (e.dimension !== dim || !e.isValid) return false;
  if (q.type && e.typeId !== q.type) return false;
  if (q.excludeTypes?.includes(e.typeId)) return false;
  if (q.tags && !q.tags.every((t) => e.tags.has(t))) return false;
  if (q.families && !q.families.every((f) => familiesOf(e).includes(f))) return false;
  if (q.location && q.maxDistance !== undefined) {
    const d = Math.hypot(e.location.x - q.location.x, e.location.y - q.location.y, e.location.z - q.location.z);
    if (d > q.maxDistance) return false;
  }
  return true;
}

function makeDimension(id) {
  const dim = {
    id,
    getBlock: (l) => blockAt(dim, l),
    getTopmostBlock: ({ x, z }) => {
      for (let y = 100; y > -64; y--) {
        const b = blockAt(dim, { x, y, z });
        if (!b.isAir) return b;
      }
      return undefined;
    },
    fillBlocks(vol, type) {
      const a = vol.from, b = vol.to;
      for (let x = Math.min(a.x, b.x); x <= Math.max(a.x, b.x); x++)
        for (let y = Math.min(a.y, b.y); y <= Math.max(a.y, b.y); y++)
          for (let z = Math.min(a.z, b.z); z <= Math.max(a.z, b.z); z++) blocks.set(key({ x, y, z }), typeof type === "string" ? type : type.id);
      return {};
    },
    spawnEntity(type, l) {
      const e = makeEntity(type, l, dim);
      entities.push(e);
      system.run(() => world.afterEvents.entitySpawn.fire({ entity: e, cause: "Spawned" }));
      return e;
    },
    getEntities: (q = {}) => entities.filter((e) => matchQuery(e, q, dim)),
    getPlayers: () => world.getAllPlayers().filter((p) => p.dimension === dim),
    getEntitiesFromRay: (o, d, opt) => raycast(dim, o, d, opt?.maxDistance ?? 64, undefined).filter((h) => !(opt?.excludeTypes ?? []).includes(h.entity.typeId)),
    getBlockFromRay(o, d, opt) {
      // march along the ray to the first solid block
      const max = opt?.maxDistance ?? 64;
      for (let t = 0; t <= max; t += 0.05) {
        const p = { x: o.x + d.x * t, y: o.y + d.y * t, z: o.z + d.z * t };
        const b = blockAt(dim, p);
        if (!b.isAir && !b.typeId.startsWith("minecraft:light_block")) {
          return { block: b, face: "Up", faceLocation: { x: p.x - b.location.x, y: p.y - b.location.y, z: p.z - b.location.z } };
        }
      }
      return undefined;
    },
    spawnParticle: (effect, l) => particles.push({ effect, l }),
    playSound: (s, l, o) => sounds.push({ s, l, o }),
    createExplosion: (l, r, o) => (explosions.push({ l, r, o }), true),
    runCommand: (c) => (commands.push(c), { successCount: 1 }),
    spawnItem: (stack, l) => entities.push(makeEntity("minecraft:item", l, dim)),
  };
  return dim;
}

const overworld = makeDimension("minecraft:overworld");
export const players = [];

export function makePlayer(name) {
  const p = makeEntity("minecraft:player", { x: 0.5, y: 64, z: 0.5 }, overworld);
  p.name = name;
  p.messages = [];
  p.bar = "";
  p.titles = [];
  p.heard = [];
  p.selectedSlotIndex = 0;
  p.mode = GameMode.Survival;
  p.getGameMode = () => p.mode;
  p.cooldowns = [];
  p.startItemCooldown = (category, ticks) => p.cooldowns.push({ category, ticks, at: tick });
  p.sendMessage = (m) => p.messages.push(m);
  p.playSound = (s) => p.heard.push(s);
  p.onScreenDisplay = { setActionBar: (t) => (p.bar = Array.isArray(t) ? t.join("") : t), setTitle: (t, o) => p.titles.push({ t, o }) };
  const slots = new Array(36).fill(undefined);
  p.inventory = {
    size: 36,
    getItem: (i) => slots[i],
    setItem: (i, s) => (slots[i] = s),
    addItem(s) {
      for (let i = 0; i < 36; i++) if (slots[i]?.typeId === s.typeId && slots[i].amount + s.amount <= slots[i].maxAmount) { slots[i].amount += s.amount; return undefined; }
      for (let i = 0; i < 36; i++) if (!slots[i]) { slots[i] = s; return undefined; }
      return s;
    },
    slots,
  };
  const worn = {};
  p.equipment = { getEquipment: (s) => worn[s], setEquipment: (s, i) => ((worn[s] = i), true), worn };
  entities.push(p);
  players.push(p);
  return p;
}

const objectives = new Map();
export const world = {
  props: new Map(),
  getDynamicProperty(k) { return this.props.get(k); },
  setDynamicProperty(k, v) { if (v === undefined) this.props.delete(k); else this.props.set(k, v); },
  getAllPlayers: () => players.filter((p) => p.isValid),
  getDimension: () => overworld,
  sendMessage() {},
  afterEvents: {
    worldLoad: signal(), itemUse: signal(), entitySpawn: signal(), entityDie: signal(), entityHurt: signal(), playerSpawn: signal(),
    projectileHitEntity: signal(), projectileHitBlock: signal(), playerPlaceBlock: signal(), playerBreakBlock: signal(),
    playerInteractWithBlock: signal(),
  },
  beforeEvents: { playerInteractWithBlock: signal() },
  scoreboard: {
    objectives,
    getObjective: (n) => objectives.get(n),
    addObjective(n, d) {
      const o = { id: n, displayName: d, scores: new Map(), setScore(p, v) { this.scores.set(typeof p === "string" ? p : p.name, v); } };
      objectives.set(n, o);
      return o;
    },
    removeObjective(o) { objectives.delete(typeof o === "string" ? o : o.id); },
    setObjectiveAtDisplaySlot() {},
  },
};
