// The Armory: buy guns, ammunition, attachments, equipment and vehicles with the money from funding and kills.
// Opened from the Field Radio. Creative players buy for free.
import { ItemStack, system } from "@minecraft/server";
import { ActionFormData, FormCancelationReason } from "@minecraft/server-ui";
import { container, cue, id, isCreative, NS, safe, tell } from "./core.js";
import { allAttachments, SLOT_NAMES, SLOTS } from "./attachments.js";
import { GUNS } from "./weapons.js";
import { fmt, money, spend } from "./economy.js";

/** @template T @param {import("@minecraft/server").Player} player @param {{show: (p: import("@minecraft/server").Player) => Promise<T>}} form @returns {Promise<T | undefined>} */
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

/** Gun prices. */
export const GUN_PRICES = {
  glock17: 300, m1911: 350, deagle: 650, mp5: 900, ump45: 950, p90: 1200, rem870: 1000, m4a1: 1600, ak47: 1500,
  scar_h: 2200, m249: 2600, pkm: 2500, svd: 2400, awm: 3500, barrett: 4500, carl_gustaf: 2800, rpg7: 2200,
};
/** Ammunition: rounds per pack and the pack's price. */
export const AMMO_PACKS = {
  ammo_9mm: [34, 40], ammo_45acp: [28, 45], ammo_50ae: [14, 70], ammo_57: [50, 80], ammo_556: [60, 90],
  ammo_762x39: [60, 90], ammo_762x51: [40, 110], ammo_762x54r: [40, 110], ammo_338: [10, 150], ammo_50bmg: [10, 200],
  ammo_12g: [16, 60], ammo_84mm: [1, 250], ammo_pg7v: [1, 200],
};
/** Attachment prices. */
export const ATTACHMENT_PRICES = {
  reflex_sight: 150, red_dot: 200, holo_sight: 300, holo_magnifier: 550, prism_2x: 300, combat_4x: 450, variable_6x: 600,
  marksman_8x: 700, sniper_12x: 900, night_vision_4x: 1000, pistol_suppressor: 300, rifle_suppressor: 450, compensator: 150,
  muzzle_brake: 200, flash_hider: 100, full_choke: 150, cylinder_choke: 100, vertical_grip: 150, angled_grip: 150,
  stubby_grip: 120, handstop: 80, bipod: 250, laser_sight: 200, flashlight: 150, laser_light: 350, heavy_stock: 200,
  light_stock: 150, precision_stock: 300, extended_mag: 200, drum_mag: 450, quick_mag: 150, extended_tube: 200, big_box: 500,
};
/** Equipment: name, how many per purchase, price. */
export const EQUIPMENT = {
  frag_grenade: ["Frag Grenade", 1, 150], smoke_grenade: ["Smoke Grenade", 1, 80], medkit: ["Medkit", 1, 100],
  ammo_box: ["Ammo Box", 1, 150], binoculars: ["Binoculars", 1, 100], repair_tool: ["Repair Tool", 1, 300],
  combat_knife: ["Combat Knife", 1, 60], spawn_beacon: ["Spawn Beacon", 1, 400], sandbags: ["Sandbags", 8, 40],
  barbed_wire: ["Barbed Wire", 6, 60],
};
/** Vehicles: deployment kits. */
export const VEHICLE_PRICES = { jeep_kit: ["Jeep", 1500], tank_kit: ["Tank", 5000] };

/**
 * @typedef {object} Offer
 * @property {string} item   item id
 * @property {string} name
 * @property {number} count
 * @property {number} price
 * @property {string} [note]
 */

const icon = (/** @type {string} */ item) => `textures/items/${NS}/${item.replace(`${NS}:`, "")}`;

/** @returns {Offer[]} */
function gunOffers() {
  return Object.entries(GUN_PRICES).map(([k, price]) => {
    const g = GUNS[id(k)];
    return { item: id(k), name: g?.name ?? k, count: 1, price, note: g ? `${g.caliber}, ${g.mag} rds` : "" };
  });
}

/** @returns {Offer[]} */
function ammoOffers() {
  /** @type {Record<string, string>} */
  const calibers = {};
  for (const g of Object.values(GUNS)) calibers[g.ammo] = g.caliber;
  return Object.entries(AMMO_PACKS).map(([k, [count, price]]) => ({ item: id(k), name: calibers[id(k)] ?? k, count, price, note: `${count} rounds` }));
}

/** @param {import("./attachments.js").Slot} slot @returns {Offer[]} */
function attachmentOffers(slot) {
  return allAttachments().filter((a) => a.slot === slot)
    .map((a) => ({ item: a.id, name: a.name, count: 1, price: ATTACHMENT_PRICES[/** @type {keyof typeof ATTACHMENT_PRICES} */ (a.key)] ?? 200 }));
}

/** @returns {Offer[]} */
function equipmentOffers() {
  return Object.entries(EQUIPMENT).map(([k, [name, count, price]]) => ({ item: id(k), name: String(name), count: Number(count), price: Number(price) }));
}

/** @returns {Offer[]} */
function vehicleOffers() {
  return Object.entries(VEHICLE_PRICES).map(([k, [name, price]]) => ({ item: id(k), name: String(name), count: 1, price: Number(price), note: "deployment kit" }));
}

/** Buys an offer: takes the money and puts the items in the inventory (or at the player's feet). Returns false when
 * the player cannot afford it. @param {import("@minecraft/server").Player} player @param {Offer} o */
export function buy(player, o) {
  if (!isCreative(player) && !spend(player, o.price)) {
    tell(player, `§cYou need ${fmt(o.price)} for that; you have ${fmt(money(player))}.`);
    cue(player, `${NS}.dry_fire`);
    return false;
  }
  let left = o.count;
  while (left > 0) {
    const s = new ItemStack(o.item, 1);
    s.amount = Math.min(left, s.maxAmount);
    left -= s.amount;
    const rest = container(player)?.addItem(s);
    if (rest) safe(() => player.dimension.spawnItem(rest, player.location));
  }
  cue(player, `${NS}.resupply`, 0.8, 1.1);
  tell(player, `§aBought ${o.count > 1 ? `${o.count}x ` : ""}${o.name}§7 for ${fmt(o.price)} §8(balance ${fmt(money(player))})`);
  return true;
}

/** A list of offers to buy from; it stays open so several can be bought in a row.
 * @param {import("@minecraft/server").Player} player @param {string} title @param {Offer[]} offers */
async function offerList(player, title, offers) {
  for (;;) {
    const form = new ActionFormData().title(`§l${title}`).body(`§7Balance: §a${isCreative(player) ? "free (creative)" : fmt(money(player))}`);
    for (const o of offers) {
      const afford = isCreative(player) || money(player) >= o.price;
      form.button(`${afford ? "" : "§8"}§l${o.count > 1 && !o.note ? `${o.count}x ` : ""}${o.name}\n§r${afford ? "§2" : "§c"}${fmt(o.price)}${o.note ? ` §8· ${o.note}` : ""}`, icon(o.item));
    }
    form.button("§lBack");
    const res = await show(player, form);
    if (!res || res.canceled || res.selection === undefined || res.selection >= offers.length) return;
    buy(player, offers[res.selection]);
  }
}

/** The attachment counter: pick a slot first. @param {import("@minecraft/server").Player} player */
async function attachmentShop(player) {
  for (;;) {
    const form = new ActionFormData().title("§lArmory - Attachments").body(`§7Balance: §a${fmt(money(player))}`);
    for (const s of SLOTS) form.button(`§l${SLOT_NAMES[s]}\n§r§8${allAttachments().filter((a) => a.slot === s).length} items`);
    form.button("§lBack");
    const res = await show(player, form);
    if (!res || res.canceled || res.selection === undefined || res.selection >= SLOTS.length) return;
    await offerList(player, `Attachments - ${SLOT_NAMES[SLOTS[res.selection]]}`, attachmentOffers(SLOTS[res.selection]));
  }
}

/** The Armory, from the Field Radio. @param {import("@minecraft/server").Player} player */
export async function armory(player) {
  for (;;) {
    const form = new ActionFormData().title("§lArmory")
      .body(`§7Balance: §a${isCreative(player) ? "free (creative)" : fmt(money(player))}\n§7Funding arrives every few minutes; kills, captures and victories pay extra.`)
      .button("§lWeapons\n§r§8Pistols, SMGs, rifles, snipers, launchers", icon("m4a1"))
      .button("§lAmmunition\n§r§8Every cartridge", icon("ammo_556"))
      .button("§lAttachments\n§r§8Optics, muzzles, grips, lights...", icon("red_dot"))
      .button("§lEquipment\n§r§8Grenades, medkits, defences", icon("frag_grenade"))
      .button("§lVehicles\n§r§8Jeeps and tanks", icon("tank_kit"))
      .button("§lClose");
    const res = await show(player, form);
    if (!res || res.canceled || res.selection === undefined) return;
    if (res.selection === 0) await offerList(player, "Armory - Weapons", gunOffers());
    else if (res.selection === 1) await offerList(player, "Armory - Ammunition", ammoOffers());
    else if (res.selection === 2) await attachmentShop(player);
    else if (res.selection === 3) await offerList(player, "Armory - Equipment", equipmentOffers());
    else if (res.selection === 4) await offerList(player, "Armory - Vehicles", vehicleOffers());
    else return;
  }
}
