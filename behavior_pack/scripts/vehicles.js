// Jeeps and tanks: team paint, the tank's turret following the commander's view, its cannon, repairs and wrecks.
import { system, world } from "@minecraft/server";
import { add, cue, id, isVehicle, NS, particle, players, ready, safe, scale, shake, sound, teamOf, notify, onUse } from "./core.js";
import { explode } from "./explosives.js";

/** Vehicles seen in loaded chunks. @type {Set<import("@minecraft/server").Entity>} */
const known = new Set();

/** @param {import("@minecraft/server").Entity} vehicle @param {import("./core.js").Team} team */
export function paint(vehicle, team) {
  safe(() => vehicle.triggerEvent(`${NS}:paint_${team}`));
  safe(() => vehicle.addTag(`fl_team_${team}`));
}

/** @param {number} a */
const wrap = (a) => ((((a + 180) % 360) + 360) % 360) - 180;

/** The player in the driver's (commander's) seat, if any. @param {import("@minecraft/server").Entity} vehicle */
export function driverOf(vehicle) {
  return safe(() => vehicle.getComponent("minecraft:rideable")?.getRiders()[0]);
}

/** @param {import("@minecraft/server").Player} player */
export function ridingOn(player) {
  return safe(() => player.getComponent("minecraft:riding")?.entityRidingOn);
}

/** @param {import("@minecraft/server").Player} player @param {import("@minecraft/server").Entity} tank */
function fireCannon(player, tank) {
  if (!ready(tank, "cannon", 80)) {
    cue(player, `${NS}.dry_fire`, 1, 0.6);
    return;
  }
  const dir = player.getViewDirection();
  const flat = Math.hypot(dir.x, dir.z) || 1;
  const muzzle = add(tank.location, { x: (dir.x / flat) * 4.2, y: 1.35 + dir.y * 3, z: (dir.z / flat) * 4.2 });
  const shell = safe(() => tank.dimension.spawnEntity(id("tank_shell"), muzzle));
  const proj = shell ? safe(() => shell.getComponent("minecraft:projectile")) : undefined;
  if (proj) {
    proj.owner = player;
    safe(() => proj.shoot(scale(dir, 3.5)));
  }
  sound(tank.dimension, `${NS}.tank_fire`, muzzle, 1.4);
  particle(tank.dimension, `${NS}:gun_smoke`, muzzle);
  particle(tank.dimension, `${NS}:muzzle_flash`, muzzle);
  particle(tank.dimension, `${NS}:wreck_fire`, muzzle);
  shake(player, 0.25, 0.3);
}

export function init() {
  world.afterEvents.entitySpawn.subscribe(({ entity }) => {
    if (!isVehicle(entity)) return;
    known.add(entity);
    if (safe(() => entity.hasTag("fl_battle") || entity.hasTag("fl_team_nato") || entity.hasTag("fl_team_redfang"))) return;
    // A vehicle placed from a kit takes the colours of whoever placed it.
    let best;
    let bestD = 9;
    for (const p of players()) {
      const d = safe(() => (p.dimension.id === entity.dimension.id ? Math.hypot(p.location.x - entity.location.x, p.location.z - entity.location.z) : 99)) ?? 99;
      if (d < bestD) {
        bestD = d;
        best = p;
      }
    }
    const team = best ? teamOf(best) : undefined;
    if (team) paint(entity, team);
  });

  world.afterEvents.entityDie.subscribe(({ deadEntity }) => {
    if (!isVehicle(deadEntity)) return;
    known.delete(deadEntity);
    const at = safe(() => deadEntity.location);
    const dim = safe(() => deadEntity.dimension);
    if (!at || !dim) return;
    explode(dim, add(at, { x: 0, y: 1, z: 0 }), deadEntity.typeId === id("tank") ? 4 : 3);
    for (let i = 1; i <= 10; i++) system.runTimeout(() => particle(dim, `${NS}:wreck_fire`, add(at, { x: 0, y: 1, z: 0 })), i * 20);
  });

  onUse((source, itemStack) => {
    const vehicle = ridingOn(source);
    if (vehicle?.typeId === id("tank") && driverOf(vehicle) === source) {
      fireCannon(source, vehicle);
      return true; // in the commander's seat every item fires the cannon
    }
    if (itemStack.typeId === id("repair_tool")) {
      if (!ready(source, "repair", 10)) return true;
      const hit = safe(() => source.getEntitiesFromViewDirection({ maxDistance: 5 }))?.find((h) => isVehicle(h.entity));
      if (!hit) {
        notify(source, "§7Look at a jeep or tank to repair it");
        return true;
      }
      const hp = hit.entity.getComponent("minecraft:health");
      if (!hp) return true;
      if (hp.currentValue >= hp.effectiveMax) {
        notify(source, "§aFully repaired");
        return true;
      }
      hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + 25));
      sound(source.dimension, `${NS}.repair`, hit.entity.location);
      particle(source.dimension, `${NS}:sparks`, add(hit.entity.location, { x: 0, y: 1, z: 0 }));
      notify(source, `§aRepairing §f${Math.round(hp.currentValue)}/${hp.effectiveMax}`);
      return true;
    }
    return false;
  });

  // The turret follows the commander's view; vehicles show their damage.
  system.runInterval(() => {
    for (const p of players()) {
      const v = ridingOn(p);
      if (v?.typeId !== id("tank") || driverOf(v) !== p) continue;
      const look = p.getRotation();
      const body = v.getRotation();
      const yaw = Math.round(wrap(look.y - body.y));
      const pitch = Math.max(-25, Math.min(25, Math.round(look.x)));
      safe(() => {
        if (v.getProperty(`${NS}:turret`) !== yaw) v.setProperty(`${NS}:turret`, yaw);
        if (v.getProperty(`${NS}:pitch`) !== pitch) v.setProperty(`${NS}:pitch`, pitch);
      });
    }
  }, 2);

  system.runInterval(() => {
    for (const v of known) {
      if (!safe(() => v.isValid)) {
        known.delete(v);
        continue;
      }
      const hp = v.getComponent("minecraft:health");
      if (hp && hp.currentValue < hp.effectiveMax * 0.35) particle(v.dimension, `${NS}:wreck_fire`, add(v.location, { x: 0, y: 1.4, z: 0 }));
    }
  }, 20);
}

/** The status line shown while in a vehicle. @param {import("@minecraft/server").Player} player */
export function vehicleText(player) {
  const v = ridingOn(player);
  if (!v || !isVehicle(v)) return "";
  const hp = v.getComponent("minecraft:health");
  const pct = hp ? Math.round((hp.currentValue / hp.effectiveMax) * 100) : 100;
  const col = pct > 60 ? "§a" : pct > 30 ? "§6" : "§c";
  const name = v.typeId === id("tank") ? "Tank" : "Jeep";
  const extra = v.typeId === id("tank") && driverOf(v) === player ? " §8| §7use any item to fire the cannon" : "";
  return `§f${name} ${col}${pct}%${extra}`;
}
