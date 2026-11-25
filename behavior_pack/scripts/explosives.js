// Grenades, smoke, rockets and tank shells.
import { EffectTypes, EntityDamageCause, system, world } from "@minecraft/server";
import { distance, id, isVehicle, NS, particle, players, safe, settings, shake, sound } from "./core.js";
import { noteHit } from "./teams.js";

/** An explosion: blocks break only when the Destruction setting is on. @param {import("@minecraft/server").Dimension} dim @param {import("@minecraft/server").Vector3} at @param {number} radius @param {import("@minecraft/server").Entity} [source] */
export function explode(dim, at, radius, source) {
  safe(() => dim.createExplosion(at, radius, { breaksBlocks: settings().destruction, causesFire: false, source }));
  sound(dim, `${NS}.explosion`, at, 1.2, 0.9 + Math.random() * 0.2);
  particle(dim, `${NS}:wreck_fire`, at);
  for (const p of players()) {
    const d = safe(() => (p.dimension.id === dim.id ? distance(p.location, at) : 999)) ?? 999;
    if (d < 30) shake(p, Math.min(0.6, 3 / (d + 2)), 0.5);
  }
}

/** Live rockets and tank shells, for their smoke trails. @type {Set<import("@minecraft/server").Entity>} */
const flying = new Set();
/** Smoke clouds: where, until when. @type {Array<{dim: import("@minecraft/server").Dimension, at: import("@minecraft/server").Vector3, until: number}>} */
const clouds = [];

const WARHEADS = { [id("rocket")]: { radius: 3.2, direct: 80 }, [id("tank_shell")]: { radius: 3.8, direct: 140 } };

export function init() {
  world.afterEvents.entitySpawn.subscribe(({ entity }) => {
    const type = entity.typeId;
    if (WARHEADS[type]) {
      flying.add(entity);
      return;
    }
    if (type === id("frag_grenade")) {
      sound(entity.dimension, `${NS}.grenade_pin`, entity.location);
      const owner = safe(() => entity.getComponent("minecraft:projectile")?.owner);
      system.runTimeout(() => {
        if (!safe(() => entity.isValid)) return;
        const at = entity.location;
        const dim = entity.dimension;
        safe(() => entity.remove());
        explode(dim, at, 3.0, owner);
      }, 50);
    }
    if (type === id("smoke_grenade")) {
      sound(entity.dimension, `${NS}.grenade_pin`, entity.location, 1, 0.8);
      system.runTimeout(() => {
        if (!safe(() => entity.isValid)) return;
        const at = entity.location;
        const dim = entity.dimension;
        safe(() => entity.remove());
        sound(dim, "random.fizz", at, 1, 0.6);
        clouds.push({ dim, at, until: system.currentTick + 20 * 20 });
      }, 30);
    }
  });

  /** @param {{projectile: import("@minecraft/server").Entity, dimension: import("@minecraft/server").Dimension, location: import("@minecraft/server").Vector3, source?: import("@minecraft/server").Entity}} e @param {import("@minecraft/server").Entity} [hit] */
  const warhead = (e, hit) => {
    const type = safe(() => e.projectile.typeId);
    const w = type ? WARHEADS[type] : undefined;
    if (!w) return;
    flying.delete(e.projectile);
    const owner = e.source ?? safe(() => e.projectile.getComponent("minecraft:projectile")?.owner);
    if (hit && isVehicle(hit)) {
      noteHit(hit, type === id("rocket") ? "Rocket" : "Tank Cannon", false);
      safe(() => hit.applyDamage(w.direct, { cause: EntityDamageCause.entityExplosion, damagingEntity: owner }));
    }
    const at = e.location;
    const dim = e.dimension;
    system.run(() => explode(dim, at, w.radius, owner));
  };
  world.afterEvents.projectileHitBlock.subscribe((e) => warhead(e));
  world.afterEvents.projectileHitEntity.subscribe((e) => warhead(e, safe(() => e.getEntityHit().entity)));

  system.runInterval(() => {
    for (const r of flying) {
      if (!safe(() => r.isValid)) {
        flying.delete(r);
        continue;
      }
      particle(r.dimension, `${NS}:rocket_trail`, r.location);
    }
  }, 2);

  // Smoke screens: a thick cloud, and anyone inside is hidden (invisible to sight-based targeting).
  system.runInterval(() => {
    const now = system.currentTick;
    for (let i = clouds.length - 1; i >= 0; i--) {
      const c = clouds[i];
      if (c.until < now) {
        clouds.splice(i, 1);
        continue;
      }
      particle(c.dim, `${NS}:smoke_screen`, c.at);
      for (const e of safe(() => c.dim.getEntities({ location: c.at, maxDistance: 4.5 })) ?? []) {
        if (e.typeId === "minecraft:player" || e.typeId.startsWith(`${NS}:nato_`) || e.typeId.startsWith(`${NS}:redfang_`)) {
          safe(() => e.addEffect(EffectTypes.get("invisibility") ?? "invisibility", 30, { showParticles: false }));
        }
      }
    }
  }, 15);
}
