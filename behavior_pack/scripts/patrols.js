// Outside battles, small squads of either side roam the land and fight whoever they meet.
import { system } from "@minecraft/server";
import { bearing, enemyOf, NS, players, safe, settings, TEAM_KEYS, TEAMS, teamOf, tell, cue } from "./core.js";
import { current, groundAt } from "./battle.js";
import { SOLDIER_TYPES } from "./teams.js";

/** Tick of each player's next patrol. @type {Map<string, number>} */
const next = new Map();

/** @param {import("@minecraft/server").Player} player */
export function sendPatrol(player) {
  const dim = player.dimension;
  if (dim.id !== "minecraft:overworld") return 0;
  const near = safe(() => dim.getEntities({ location: player.location, maxDistance: 80, families: ["frontline_soldier"] }).length) ?? 0;
  if (near >= 10) return 0;
  const mine = teamOf(player);
  const team = mine && Math.random() < 0.65 ? enemyOf(mine) : TEAM_KEYS[Math.floor(Math.random() * 2)];
  const angle = Math.random() * Math.PI * 2;
  const dist = 40 + Math.random() * 20;
  const x = Math.floor(player.location.x + Math.cos(angle) * dist);
  const z = Math.floor(player.location.z + Math.sin(angle) * dist);
  const g = groundAt(dim, x, z);
  if (g === undefined) return 0;
  const ground = safe(() => dim.getBlock({ x, y: g, z }));
  if (!ground || ground.isLiquid || ground.typeId.includes("water")) return 0;
  const [rifle, marksman, heavy] = SOLDIER_TYPES[team];
  const size = 2 + Math.floor(Math.random() * 3);
  let n = 0;
  for (let i = 0; i < size; i++) {
    const type = i === 0 ? rifle : Math.random() < 0.6 ? rifle : Math.random() < 0.5 ? marksman : heavy;
    const s = safe(() => dim.spawnEntity(type, { x: x + 0.5 + (i % 2), y: g + 1, z: z + 0.5 + Math.floor(i / 2) }));
    if (s) {
      safe(() => s.addTag("fl_patrol"));
      n++;
    }
  }
  if (n && mine) {
    const t = TEAMS[team];
    const friendly = team === mine;
    tell(player, `§7[Radio] ${friendly ? "§aFriendly" : "§cEnemy"} patrol§7: ${n} ${t.color}${t.name}§7 soldiers, about ${Math.round(dist)} m ${bearing(player.location, { x, y: g, z })}.`);
    cue(player, `${NS}.radio`, 0.6);
  }
  return n;
}

export function init() {
  system.runInterval(() => {
    if (!settings().patrols || current()) return;
    const now = system.currentTick;
    for (const p of players()) {
      const at = next.get(p.id);
      const gap = settings().patrolMinutes * 60 * 20;
      if (at === undefined) {
        next.set(p.id, now + gap / 2);
        continue;
      }
      if (now < at) continue;
      next.set(p.id, now + gap * (0.75 + Math.random() * 0.5));
      sendPatrol(p);
    }
  }, 200);
}
