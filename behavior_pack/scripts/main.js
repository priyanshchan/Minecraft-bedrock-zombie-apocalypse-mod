// Frontline: NATO vs Red Fang - entry point.
import { ItemStack, system, world } from "@minecraft/server";
import { container, countItem, dispatchUse, heldItem, hudHold, id, onUse, players, ready, safe, settings, teamOf } from "./core.js";
import * as teams from "./teams.js";
import * as weapons from "./weapons.js";
import * as explosives from "./explosives.js";
import * as vehicles from "./vehicles.js";
import * as gear from "./gear.js";
import * as battle from "./battle.js";
import * as patrols from "./patrols.js";
import * as ui from "./ui.js";
import * as gunsmith from "./gunsmith.js";

let started = false;
const PLACEABLE = new Set(["sandbags", "barbed_wire", "ammo_crate", "spawn_beacon", "jeep_kit", "tank_kit"].map(id));

function start() {
  if (started) return;
  started = true;
  teams.init();
  vehicles.init(); // before weapons: in a tank's commander seat every item fires the cannon
  weapons.init();
  gunsmith.init();
  explosives.init();
  gear.init();
  battle.init();
  patrols.init();

  onUse((player, item, repeat) => {
    if (item.typeId !== id("field_radio")) return false;
    if (!repeat && ready(player, "radio", 10)) ui.radio(player);
    return true;
  });

  world.afterEvents.itemUse.subscribe(({ source, itemStack }) => {
    if (source.typeId === "minecraft:player") dispatchUse(source, itemStack, false);
  });
  // A tap or right-click on a block is reported as interacting with the block, not as using the item:
  // route it to the same handlers (held down, it repeats, so guns keep firing). Block items are left alone.
  world.beforeEvents.playerInteractWithBlock.subscribe((e) => {
    const item = e.itemStack;
    if (!item || !item.typeId.startsWith("frontline:") || PLACEABLE.has(item.typeId)) return;
    const player = e.player;
    const repeat = !e.isFirstEvent;
    system.run(() => dispatchUse(player, item, repeat));
  });

  world.afterEvents.playerSpawn.subscribe(({ player, initialSpawn }) => {
    system.runTimeout(() => welcome(player, initialSpawn), initialSpawn ? 60 : 10);
  });

  battle.onStart.push(() => {
    for (const p of players()) if (teamOf(p)) system.runTimeout(() => ui.deploy(p), 40);
  });

  // The status bar: the battle, the gun in hand or the vehicle you are in; and the aiming pose.
  let tick = 0;
  system.runInterval(() => {
    tick++;
    for (const p of players()) {
      const held = heldItem(p)?.typeId;
      weapons.tickPlayer(p, held);
      if (tick % 2 !== 0 || !settings().hud || (hudHold.get(p.id) ?? 0) > system.currentTick) continue;
      /** @type {string[]} */
      const lines = [];
      const b = battle.hudLine();
      if (b) {
        const point = battle.pointAt(p);
        const cap = point ? ` §8| §fFlag ${point.key} §7${point.progress > 0 ? "§9" : point.progress < 0 ? "§c" : ""}${Math.abs(Math.round(point.progress))}%` : "";
        lines.push(b + cap);
      }
      const v = vehicles.vehicleText(p);
      if (v) lines.push(v);
      else if (held && weapons.GUNS[held]) lines.push(weapons.ammoText(p, held));
      if (lines.length) safe(() => p.onScreenDisplay.setActionBar(lines.join("\n")));
    }
  }, 5);
}

/** First join: a radio and a side; after a death in battle: back to the deploy screen. @param {import("@minecraft/server").Player} player @param {boolean} first */
async function welcome(player, first) {
  if (!safe(() => player.isValid)) return;
  if (!safe(() => player.getDynamicProperty("fl:welcomed"))) {
    safe(() => player.setDynamicProperty("fl:welcomed", true));
    if (countItem(player, id("field_radio")) === 0) {
      const rest = container(player)?.addItem(new ItemStack(id("field_radio"), 1));
      if (rest) safe(() => player.dimension.spawnItem(rest, player.location));
    }
    safe(() => player.sendMessage("§6[Frontline] §fUse the §lField Radio§r to pick a side, start a conquest battle, change settings and read the field manual."));
  }
  teams.refreshName(player);
  if (!teamOf(player) && first) await ui.chooseTeam(player);
  if (battle.current() && teamOf(player) && (!first || !safe(() => player.hasTag("fl_in_battle")))) await ui.deploy(player);
}

world.afterEvents.worldLoad.subscribe(start);
system.run(() => {
  // a script reload in a running world (/reload) does not fire worldLoad again
  if (safe(() => world.getAllPlayers().length)) start();
});
