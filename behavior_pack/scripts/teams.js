// Teams, ranks, score, the kill feed and friendly fire.
import { DisplaySlotId, ObjectiveSortOrder, system, world } from "@minecraft/server";
import {
  addNumber, broadcast, cue, getNumber, id, isSoldier, isVehicle, NS, players, safe, sameTeam, settings, TEAMS, teamOf, tell, notify,
} from "./core.js";
import { addMoney, fmt } from "./economy.js";

export const RANKS = [
  { score: 0, name: "Recruit", short: "Rct" },
  { score: 500, name: "Private", short: "Pvt" },
  { score: 1500, name: "Corporal", short: "Cpl" },
  { score: 3000, name: "Sergeant", short: "Sgt" },
  { score: 6000, name: "Lieutenant", short: "Lt" },
  { score: 10000, name: "Captain", short: "Cpt" },
  { score: 16000, name: "Major", short: "Maj" },
  { score: 25000, name: "Colonel", short: "Col" },
  { score: 40000, name: "General", short: "Gen" },
];

/** @param {number} score */
export function rankFor(score) {
  let r = RANKS[0];
  for (const rank of RANKS) if (score >= rank.score) r = rank;
  return r;
}

/** @param {import("@minecraft/server").Player} player @param {import("./core.js").Team} team */
export function joinTeam(player, team) {
  safe(() => {
    player.removeTag("fl_team_nato");
    player.removeTag("fl_team_redfang");
    player.addTag(`fl_team_${team}`);
  });
  refreshName(player);
  const t = TEAMS[team];
  safe(() => player.onScreenDisplay.setTitle(`${t.color}${t.name}`, {
    subtitle: team === "nato" ? "§7Hold the line. Take the flags." : "§7Strike hard. Take the flags.",
    fadeInDuration: 5, stayDuration: 50, fadeOutDuration: 15,
  }));
  cue(player, `${NS}.radio`);
  broadcast(`§7${player.name} joined ${t.color}${t.name}`);
}

/** The name above a player's head: team, rank and name. @param {import("@minecraft/server").Player} player */
export function refreshName(player) {
  const team = teamOf(player);
  const rank = rankFor(getNumber(player, "fl:score"));
  safe(() => {
    player.nameTag = team ? `${TEAMS[team].color}[${TEAMS[team].short}] §7${rank.short} §f${player.name}` : player.name;
  });
}

/** Score (and money) for something a player did. @param {import("@minecraft/server").Player} player @param {number} points @param {string} [why] @param {number} [cash] */
export function award(player, points, why, cash = 0) {
  const before = rankFor(getNumber(player, "fl:score"));
  const score = addNumber(player, "fl:score", points);
  const after = rankFor(score);
  if (cash) addMoney(player, cash);
  if (why) notify(player, `§e${points >= 0 ? "+" : ""}${points}${cash > 0 ? ` §a+${fmt(cash)}` : ""} §7${why}`);
  safe(() => world.scoreboard.getObjective("fl_score")?.setScore(player, score));
  if (after !== before) {
    safe(() => player.onScreenDisplay.setTitle("§6Promoted", { subtitle: `§f${after.name}`, fadeInDuration: 5, stayDuration: 50, fadeOutDuration: 15 }));
    cue(player, `${NS}.victory`, 0.6, 1.3);
    refreshName(player);
  }
}

/** A readable name for anyone in the kill feed. @param {import("@minecraft/server").Entity} e */
export function displayName(e) {
  const team = teamOf(e);
  const color = team ? TEAMS[team].color : "§7";
  if (e.typeId === "minecraft:player") return `${color}${/** @type {import("@minecraft/server").Player} */ (e).name}`;
  const tag = safe(() => e.nameTag);
  if (tag) return `${color}${tag}`;
  const base = e.typeId.replace(`${NS}:`, "").replace("minecraft:", "").replace(/_/g, " ");
  return `${color}${base.replace(/\b\w/g, (c) => c.toUpperCase()).replace("Nato", "NATO")}`;
}

/** Who last shot whom with what (for the kill feed and headshot bonus). @type {Map<string, {weapon: string, headshot: boolean, tick: number}>} */
const lastHits = new Map();
/** @param {import("@minecraft/server").Entity} target @param {string} weapon @param {boolean} headshot */
export function noteHit(target, weapon, headshot) {
  lastHits.set(target.id, { weapon, headshot, tick: system.currentTick });
}

/** Called for every death of a player, soldier or vehicle; `headshot` when a headshot finished it.
 * @type {Array<(dead: import("@minecraft/server").Entity, killer: import("@minecraft/server").Entity | undefined, headshot: boolean) => void>} */
export const onKill = [];

/** Money for a kill: soldiers, players (a bigger bounty) and vehicles; headshots pay extra. */
export const BOUNTY = { soldier: 150, player: 300, vehicle: 500, headshot: 75 };

export function init() {
  safe(() => {
    const board = world.scoreboard.getObjective("fl_score") ?? world.scoreboard.addObjective("fl_score", "§6Score");
    world.scoreboard.setObjectiveAtDisplaySlot(DisplaySlotId.List, { objective: board, sortOrder: ObjectiveSortOrder.Descending });
  });

  world.afterEvents.playerSpawn.subscribe(({ player }) => {
    system.runTimeout(() => refreshName(player), 10);
  });

  // Friendly fire is off by default: damage from a teammate is given back straight away.
  world.afterEvents.entityHurt.subscribe((e) => {
    const victim = e.hurtEntity;
    const source = e.damageSource.damagingEntity;
    if (!source || source === victim || settings().friendlyFire) return;
    if (victim.typeId !== "minecraft:player" || !sameTeam(victim, source)) return;
    safe(() => {
      const hp = victim.getComponent("minecraft:health");
      if (hp && hp.currentValue > 0) hp.setCurrentValue(Math.min(hp.effectiveMax, hp.currentValue + e.damage));
    });
  });

  world.afterEvents.entityDie.subscribe((e) => {
    const dead = e.deadEntity;
    if (!(dead.typeId === "minecraft:player" || isSoldier(dead) || isVehicle(dead))) return;
    let killer = e.damageSource.damagingEntity;
    if (killer && killer.typeId !== "minecraft:player" && !isSoldier(killer)) {
      const owner = safe(() => killer?.getComponent("minecraft:projectile")?.owner);
      if (owner) killer = owner;
    }
    const hit = safe(() => lastHits.get(dead.id));
    lastHits.delete(dead.id);
    const weapon = hit && system.currentTick - hit.tick < 40 ? hit.weapon : "";
    const head = hit && hit.headshot && system.currentTick - hit.tick < 40 ? " §e[HEADSHOT]" : "";
    if (dead.typeId === "minecraft:player") addNumber(/** @type {import("@minecraft/server").Player} */ (dead), "fl:deaths", 1);
    if (killer && killer.typeId === "minecraft:player" && killer !== dead) {
      const p = /** @type {import("@minecraft/server").Player} */ (killer);
      if (!sameTeam(p, dead)) {
        addNumber(p, "fl:kills", 1);
        const vehicle = isVehicle(dead);
        const cash = vehicle ? BOUNTY.vehicle : (dead.typeId === "minecraft:player" ? BOUNTY.player : BOUNTY.soldier) + (head ? BOUNTY.headshot : 0);
        award(p, vehicle ? 300 : 100 + (head ? 25 : 0), vehicle ? "Vehicle destroyed" : head ? "Headshot kill" : "Kill", cash);
        cue(p, `${NS}.kill`);
      } else {
        award(p, -50, "Team kill");
      }
    }
    const where = safe(() => dead.location);
    const dimId = safe(() => dead.dimension.id);
    if (killer && where && (teamOf(dead) || isVehicle(dead))) {
      const msg = `${displayName(killer)} §8» §7${weapon || "x"}${head} §8» ${displayName(dead)}`;
      for (const p of players()) {
        const near = safe(() => p.dimension.id === dimId && Math.hypot(p.location.x - where.x, p.location.z - where.z) < 160);
        if (near) tell(p, msg);
      }
    }
    for (const fn of onKill) safe(() => fn(dead, killer, Boolean(head)));
  });
}

export const SOLDIER_TYPES = {
  nato: [id("nato_rifleman"), id("nato_marksman"), id("nato_heavy")],
  redfang: [id("redfang_fighter"), id("redfang_sniper"), id("redfang_rpg")],
};
