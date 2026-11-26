// The Field Radio: teams, classes and deployment, starting battles, settings, the field manual and records.
import { EquipmentSlot, ItemStack, system, world } from "@minecraft/server";
import { ActionFormData, FormCancelationReason, MessageFormData, ModalFormData } from "@minecraft/server-ui";
import {
  countItem, cue, getNumber, giveItem, id, NS, safe, settings, TEAMS, teamOf, tell, updateSettings,
} from "./core.js";
import { current, deployPoints, endBattle, groundAt, startBattle } from "./battle.js";
import { beacons } from "./gear.js";
import { joinTeam, rankFor, RANKS } from "./teams.js";

/** Shows a form, retrying while the player is busy (a chat or another screen open). @template T @param {import("@minecraft/server").Player} player @param {{show: (p: import("@minecraft/server").Player) => Promise<T>}} form @returns {Promise<T | undefined>} */
async function show(player, form) {
  for (let i = 0; i < 30; i++) {
    const res = await form.show(player).catch(() => undefined);
    if (!res) return undefined;
    // @ts-ignore cancelationReason exists on every form response
    if (res.canceled && res.cancelationReason === FormCancelationReason.UserBusy) {
      await new Promise((r) => system.runTimeout(() => r(0), 10));
      continue;
    }
    return res;
  }
  return undefined;
}

// ------------------------------------------------------------------ classes

export const CLASSES = {
  assault: {
    name: "Assault", desc: "Assault rifle, frag grenades and medkits: take ground and keep your squad alive.",
    kit: [["assault_rifle", 1], ["service_pistol", 1], ["rifle_ammo", 90], ["pistol_ammo", 36], ["frag_grenade", 2], ["medkit", 3], ["combat_knife", 1]],
  },
  engineer: {
    name: "Engineer", desc: "SMG, rocket launcher and a repair tool: kill armour, fix your own.",
    kit: [["smg", 1], ["service_pistol", 1], ["rocket_launcher", 1], ["rocket", 4], ["pistol_ammo", 120], ["repair_tool", 1], ["combat_knife", 1]],
  },
  support: {
    name: "Support", desc: "LMG, ammo boxes and smoke: suppress the enemy and keep everyone firing.",
    kit: [["lmg", 1], ["service_pistol", 1], ["rifle_ammo", 200], ["pistol_ammo", 36], ["ammo_box", 3], ["smoke_grenade", 2], ["combat_knife", 1]],
  },
  recon: {
    name: "Recon", desc: "Sniper rifle, binoculars and a spawn beacon: spot targets, pick them off, open a new front.",
    kit: [["sniper_rifle", 1], ["service_pistol", 1], ["sniper_rounds", 25], ["pistol_ammo", 36], ["binoculars", 1], ["spawn_beacon", 1], ["smoke_grenade", 1], ["combat_knife", 1]],
  },
};

/** Tops a player's inventory up to a class kit (never takes anything away). @param {import("@minecraft/server").Player} player @param {keyof typeof CLASSES} cls */
export function giveKit(player, cls) {
  for (const [item, n] of CLASSES[cls].kit) {
    const full = id(String(item));
    const have = countItem(player, full);
    if (have < Number(n)) giveItem(player, full, Number(n) - have);
  }
  if (countItem(player, id("field_ration")) < 2) giveItem(player, id("field_ration"), 2 - countItem(player, id("field_ration")));
  const eq = player.getComponent("minecraft:equippable");
  if (eq) {
    for (const [slot, item] of /** @type {const} */ ([[EquipmentSlot.Head, "minecraft:iron_helmet"], [EquipmentSlot.Chest, "minecraft:iron_chestplate"]])) {
      safe(() => {
        if (!eq.getEquipment(slot)) eq.setEquipment(slot, new ItemStack(item, 1));
      });
    }
  }
  safe(() => player.setDynamicProperty("fl:class", cls));
}

// ------------------------------------------------------------------ team, class, deploy

/** @param {import("@minecraft/server").Player} player */
export async function chooseTeam(player) {
  const form = new ActionFormData()
    .title("§lChoose your side")
    .body("§9NATO§r and the §cRed Fang§r cell fight for every flag.\n\nYour side decides who your soldiers are, which flags you capture and who shoots at you.")
    .button("§9§lNATO\n§r§8Coalition forces", "textures/items/frontline/assault_rifle")
    .button("§c§lRED FANG\n§r§8The terror cell", "textures/items/frontline/smg");
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return teamOf(player);
  const team = res.selection === 0 ? "nato" : "redfang";
  if (teamOf(player) !== team) joinTeam(player, team);
  return team;
}

/** Class and spawn point, then off you go. @param {import("@minecraft/server").Player} player */
export async function deploy(player) {
  const b = current();
  if (!b) return;
  let team = teamOf(player);
  if (!team) team = await chooseTeam(player);
  if (!team) return;
  const classes = /** @type {(keyof typeof CLASSES)[]} */ (Object.keys(CLASSES));
  const last = safe(() => player.getDynamicProperty("fl:class"));
  const cf = new ActionFormData().title("§lDeploy - choose a class")
    .body(`${TEAMS[team].color}${TEAMS[team].name}§r · tickets §9${b.tickets.nato}§r / §c${b.tickets.redfang}`);
  for (const c of classes) cf.button(`§l${CLASSES[c].name}${c === last ? " §8(last)" : ""}\n§r§8${CLASSES[c].desc.split(":")[0]}`);
  const cr = await show(player, cf);
  if (!cr || cr.canceled || cr.selection === undefined) return;
  const cls = classes[cr.selection];

  const points = deployPoints(team);
  for (const bcn of Object.values(beacons())) {
    if (bcn.team === team && bcn.dim === b.dim) points.push({ label: `Beacon (${bcn.name})`, x: bcn.x, y: bcn.y, z: bcn.z });
  }
  const sf = new ActionFormData().title("§lDeploy - choose where").body(CLASSES[cls].desc);
  for (const p of points) sf.button(`§l${p.label}`);
  const sr = await show(player, sf);
  if (!sr || sr.canceled || sr.selection === undefined) return;
  const at = points[sr.selection];
  const dim = world.getDimension(b.dim);
  const g = groundAt(dim, Math.floor(at.x), Math.floor(at.z));
  const target = { x: at.x + 0.5 + (Math.random() * 4 - 2), y: (g ?? at.y) + 1, z: at.z + 0.5 + (Math.random() * 4 - 2) };
  safe(() => player.teleport(target, { dimension: dim }));
  giveKit(player, cls);
  safe(() => player.addTag("fl_in_battle"));
  safe(() => player.addEffect("resistance", 60, { amplifier: 4, showParticles: false }));
  cue(player, `${NS}.radio`);
  safe(() => player.onScreenDisplay.setTitle(`§l${CLASSES[cls].name}`, { subtitle: `§7Deployed at ${at.label}`, fadeInDuration: 5, stayDuration: 30, fadeOutDuration: 10 }));
}

// ------------------------------------------------------------------ the radio menu

/** @param {import("@minecraft/server").Player} player */
export async function radio(player) {
  cue(player, `${NS}.radio`, 0.5, 1.2);
  const b = current();
  const team = teamOf(player);
  /** @type {Array<[string, () => Promise<unknown> | void]>} */
  const options = [];
  if (b) {
    options.push(["§lDeploy / redeploy\n§r§8Class and spawn point", () => deploy(player)]);
    options.push(["§lBattle status\n§r§8Tickets and flags", () => status(player)]);
  } else {
    options.push(["§lStart a conquest battle\n§r§8Flags, tickets, AI soldiers", () => setupBattle(player)]);
  }
  options.push([team ? `§lChange side\n§r§8Now ${TEAMS[team].color}${TEAMS[team].name}` : "§lChoose a side\n§r§8NATO or Red Fang", () => chooseTeam(player)]);
  options.push(["§lService record\n§r§8Rank, score, kills", () => record(player)]);
  options.push(["§lField manual\n§r§8How everything works", () => manual(player)]);
  options.push(["§lSettings\n§r§8World rules", () => settingsForm(player)]);
  if (b) options.push(["§c§lEnd the battle", () => confirmEnd(player)]);
  const form = new ActionFormData().title("§lField Radio").body(b ? "§6A battle is on." : "§7No battle is on. Patrols roam the land.");
  for (const [label] of options) form.button(label);
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return;
  await options[res.selection][1]();
}

/** @param {import("@minecraft/server").Player} player */
async function setupBattle(player) {
  if (!teamOf(player)) await chooseTeam(player);
  const flagsOpts = ["3", "4", "5"];
  const ticketOpts = ["100", "200", "300", "500"];
  const botOpts = ["4", "6", "8", "12", "16"];
  const form = new ModalFormData()
    .title("§lNew conquest battle")
    .label("Your headquarters will be built where you stand; the line of flags runs the way you face.")
    .dropdown("Capture points", flagsOpts, { defaultValueIndex: 0 })
    .dropdown("Tickets per side", ticketOpts, { defaultValueIndex: 1 })
    .dropdown("AI soldiers per side", botOpts, { defaultValueIndex: 2 })
    .toggle("Jeeps and tanks at each headquarters", { defaultValue: true });
  const res = await show(player, form);
  if (!res || res.canceled || !res.formValues) return;
  const v = res.formValues.filter((x) => x !== undefined);
  startBattle(player, {
    flags: Number(flagsOpts[Number(v[0])]), tickets: Number(ticketOpts[Number(v[1])]), bots: Number(botOpts[Number(v[2])]),
    vehicles: Boolean(v[3]),
  });
}

/** @param {import("@minecraft/server").Player} player */
async function confirmEnd(player) {
  const form = new MessageFormData().title("§lEnd the battle?").body("All AI soldiers, battle vehicles and flags will be removed.")
    .button1("§cEnd it").button2("Keep fighting");
  const res = await show(player, form);
  if (res && !res.canceled && res.selection === 0) endBattle(undefined);
}

/** @param {import("@minecraft/server").Player} player */
async function status(player) {
  const b = current();
  if (!b) return;
  const lines = [`§9NATO §f${b.tickets.nato}§7/${b.max} tickets`, `§cRed Fang §f${b.tickets.redfang}§7/${b.max} tickets`, ""];
  for (const p of b.points) {
    const who = p.owner === 1 ? "§9NATO" : p.owner === 2 ? "§cRed Fang" : "§7neutral";
    lines.push(`§fFlag §l${p.key}§r: ${who} §8(${p.progress > 0 ? "+" : ""}${Math.round(p.progress)})${p.built ? "" : " §8- not built yet (chunk loading)"}`);
  }
  lines.push("", "§7The side holding more flags drains the other's tickets. Every death costs one.");
  await show(player, new ActionFormData().title("§lBattle status").body(lines.join("\n")).button("Close"));
}

/** @param {import("@minecraft/server").Player} player */
async function record(player) {
  const score = getNumber(player, "fl:score");
  const rank = rankFor(score);
  const next = RANKS.find((r) => r.score > score);
  const kills = getNumber(player, "fl:kills");
  const deaths = getNumber(player, "fl:deaths");
  const body = [
    `§6${rank.name}§r - ${score} points`, next ? `§7Next: ${next.name} at ${next.score}` : "§7Highest rank reached", "",
    `Kills: §a${kills}§r   Deaths: §c${deaths}§r   K/D: §f${deaths ? (kills / deaths).toFixed(2) : kills}`,
  ].join("\n");
  await show(player, new ActionFormData().title("§lService record").body(body).button("Close"));
}

const MANUAL = {
  "Controls": [
    "§lGuns§r: use (right-click / hold-tap) to fire. Rifles fire short bursts.",
    "§lReload§r: automatic when empty, or double-tap crouch. Your gun's own reload plays: magazine out, a fresh one in, the bolt or slide racked.",
    "§lJams§r: now and then a gun stops. JAMMED: double-tap crouch to tap and rack it (one round lost). MALFUNCTION: double-tap crouch to strip the magazine, rack and reload (two rounds lost). Turn them off in Settings.",
    "§lAim§r: crouch to steady your aim (much tighter spread). Sprinting spreads it.",
    "§lHeadshots§r deal extra damage; sniper headshots kill almost anything.",
    "Spare ammo is an item in your inventory; each gun shows magazine | reserve on the HUD.",
  ],
  "Classes": Object.values(CLASSES).map((c) => `§l${c.name}§r: ${c.desc}`),
  "Conquest": [
    "Stand at a flag (8 blocks) with more of your side than the enemy's to raise your colours.",
    "An enemy flag must be pulled down to neutral before you can take it.",
    "The side holding more flags drains the other's tickets; every death costs a ticket.",
    "AI soldiers reinforce from their side's front-line flag and push on the nearest flag they don't hold.",
    "After dying you redeploy with any class at headquarters, a held flag or a team spawn beacon.",
  ],
  "Vehicles": [
    "§lJeep§r: 4 seats, fast. Passengers can shoot their guns.",
    "§lTank§r: the turret follows where the commander looks. Use any item in the commander's seat to fire the cannon (4 s reload).",
    "Bullets barely scratch armour: use rockets, grenades or the tank cannon.",
    "Engineers repair vehicles with the Repair Tool. Deployment kits place vehicles outside battles.",
  ],
  "Gear": [
    "§lMedkit§r heals you and teammates within 5 blocks.",
    "§lAmmo Box§r gives a magazine for every gun to you and teammates within 6 blocks.",
    "§lBinoculars§r mark an enemy for your side; marked enemies take more damage.",
    "§lSpawn Beacon§r (block): your side can deploy on it. §lAmmo Crates§r resupply you.",
    "§lSmoke Grenades§r hide everyone inside the cloud. §lBarbed Wire§r slows and cuts.",
  ],
};

/** @param {import("@minecraft/server").Player} player */
async function manual(player) {
  const pages = Object.keys(MANUAL);
  const form = new ActionFormData().title("§lField manual");
  for (const p of pages) form.button(`§l${p}`);
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return;
  const page = pages[res.selection];
  await show(player, new ActionFormData().title(`§l${page}`).body(MANUAL[/** @type {"Controls"} */ (page)].join("\n\n")).button("Back"));
  await manual(player);
}

/** @param {import("@minecraft/server").Player} player */
async function settingsForm(player) {
  const s = settings();
  const damage = [0.6, 1, 1.4];
  const form = new ModalFormData().title("§lSettings")
    .toggle("Friendly fire", { defaultValue: s.friendlyFire })
    .toggle("Explosions break blocks", { defaultValue: s.destruction })
    .toggle("AI patrols outside battles", { defaultValue: s.patrols })
    .slider("Minutes between patrols", 2, 10, { defaultValue: s.patrolMinutes, valueStep: 1 })
    .dropdown("AI damage", ["Low", "Normal", "High"], { defaultValueIndex: Math.max(0, damage.indexOf(s.botDamage)) })
    .toggle("Status bar (HUD)", { defaultValue: s.hud })
    .toggle("Weapon jams and malfunctions", { defaultValue: s.malfunctions });
  const res = await show(player, form);
  if (!res || res.canceled || !res.formValues) return;
  const v = res.formValues.filter((x) => x !== undefined);
  updateSettings({
    friendlyFire: Boolean(v[0]), destruction: Boolean(v[1]), patrols: Boolean(v[2]), patrolMinutes: Number(v[3]),
    botDamage: damage[Number(v[4])] ?? 1, hud: Boolean(v[5]), malfunctions: Boolean(v[6]),
  });
  tell(player, "§aSettings saved.");
}
