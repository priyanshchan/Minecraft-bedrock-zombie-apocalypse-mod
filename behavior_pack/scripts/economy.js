// Money: every player has a balance. Funding arrives on a timer (NATO's government, the Red Fang cell's backers),
// and kills, captures and victories pay extra. The Armory (shop.js) spends it.
import { system } from "@minecraft/server";
import { cue, getNumber, NS, players, safe, settings, teamOf, tell } from "./core.js";

export const START_MONEY = 1000;
export const SALARY = 300;

/** @param {import("@minecraft/server").Player} player */
export function money(player) {
  return getNumber(player, "fl:money", START_MONEY);
}

/** Adds (or with a negative amount takes) money. @param {import("@minecraft/server").Player} player @param {number} amount */
export function addMoney(player, amount) {
  const v = Math.max(0, money(player) + Math.round(amount));
  safe(() => player.setDynamicProperty("fl:money", v));
  return v;
}

/** Spends money if the player has enough. @param {import("@minecraft/server").Player} player @param {number} amount */
export function spend(player, amount) {
  if (money(player) < amount) return false;
  addMoney(player, -amount);
  return true;
}

/** "$1,250" @param {number} n */
export const fmt = (n) => `$${Math.round(n).toLocaleString("en-US")}`;

/** Who pays each side's funding. @param {import("@minecraft/server").Player} player */
function funder(player) {
  const team = teamOf(player);
  return team === "nato" ? "Government funding" : team === "redfang" ? "Cell funding" : "Funding";
}

/** Ticks of each player's next pay day. @type {Map<string, number>} */
const payday = new Map();

function pay() {
  const now = system.currentTick;
  const every = Math.max(1, settings().salaryMinutes) * 1200;
  for (const p of players()) {
    const due = payday.get(p.id);
    if (due === undefined) {
      payday.set(p.id, now + every);
      continue;
    }
    if (now < due) continue;
    payday.set(p.id, now + every);
    const v = addMoney(p, SALARY);
    tell(p, `§a+${fmt(SALARY)} §7${funder(p)} §8(balance ${fmt(v)})`);
    cue(p, `${NS}.resupply`, 0.6, 1.3);
  }
}

export function init() {
  system.runInterval(pay, 20);
}
