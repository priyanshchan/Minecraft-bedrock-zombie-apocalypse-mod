// Weapon attachments: the catalogue (generated into gundata.js from tools/gen/attach.py), what is fitted to each
// gun item, how fitted attachments change a gun, and showing them on the gun in hand.
import { GUN_DATA } from "./gundata.js";
import { safe } from "./core.js";

/** @typedef {"optic" | "muzzle" | "underbarrel" | "side" | "stock" | "magazine"} Slot */
/** @type {Slot[]} */
export const SLOTS = ["optic", "muzzle", "underbarrel", "side", "stock", "magazine"];
export const SLOT_NAMES = /** @type {Record<Slot, string>} */ ({
  optic: "Optic", muzzle: "Muzzle", underbarrel: "Underbarrel", side: "Side rail", stock: "Stock", magazine: "Magazine",
});

/**
 * How a gun's fitted attachments change it. Multipliers of the gun's own values unless noted.
 * @typedef {object} Mods
 * @property {number} spread    hip-fire spread
 * @property {number} ads       spread while crouched (aiming)
 * @property {number} vrec      vertical recoil
 * @property {number} hrec      horizontal recoil
 * @property {number} velocity  muzzle velocity (flatter, longer flight)
 * @property {number} damage
 * @property {number} reload    reload time
 * @property {number} noise     how loud the shot is
 * @property {number} mag       magazine size
 * @property {number} mag_add   extra rounds (added)
 * @property {number} zoom      magnification while aiming (the largest)
 * @property {number} nv        night vision while aiming (0 / 1)
 * @property {number} laser     a laser dot (0 / 1)
 * @property {number} light     a flashlight (0 / 1)
 * @property {number} flash     no muzzle flash (0 / 1)
 * @property {number} bipod     braced when crouched (0 / 1)
 */

/**
 * @typedef {object} Attachment
 * @property {string} id        the attachment's item id
 * @property {string} key       the id without the namespace
 * @property {Slot} slot
 * @property {string} name
 * @property {string[]} guns    gun item ids it fits
 * @property {Partial<Mods>} mods
 * @property {string} category  the cooldown category that shows it on the gun
 */

/** @type {Map<string, Attachment>} */
const registry = new Map();
for (const [attId, a] of Object.entries(/** @type {Record<string, Omit<Attachment, "id">>} */ (/** @type {unknown} */ (GUN_DATA.attachments)))) {
  registry.set(attId, { id: attId, ...a });
}

/** Registers an attachment (the catalogue registers itself; other packs could add more). @param {Attachment} att */
export function registerAttachment(att) {
  registry.set(att.id, att);
}

/** @param {string} attId */
export function attachment(attId) {
  return registry.get(attId);
}

/** Every attachment, in catalogue order. */
export function allAttachments() {
  return [...registry.values()];
}

const GUN_SLOTS = /** @type {Record<string, {slots: Slot[]}>} */ (/** @type {unknown} */ (GUN_DATA.guns));

/** The slots a gun offers: every mount its model has, and its magazine. @param {string} gunId @returns {Slot[]} */
export function slotsOf(gunId) {
  return GUN_SLOTS[gunId]?.slots ?? [];
}

/** Whether an attachment fits a gun. @param {Attachment} att @param {string} gunId */
export function fits(att, gunId) {
  return slotsOf(gunId).includes(att.slot) && (att.guns.includes("*") || att.guns.includes(gunId));
}

/** Attachments that fit a gun in one slot. @param {string} gunId @param {Slot} slot */
export function choicesFor(gunId, slot) {
  return allAttachments().filter((a) => a.slot === slot && fits(a, gunId));
}

/** Attachments fitted to a gun item: slot -> attachment id. @param {import("@minecraft/server").ItemStack | undefined} item @returns {Partial<Record<Slot, string>>} */
export function fitted(item) {
  if (!item) return {};
  const raw = safe(() => item.getDynamicProperty("fl:att"));
  if (typeof raw !== "string") return {};
  try {
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

/**
 * Fits (or, with `attId` undefined, removes) an attachment on a gun item. Returns false if it does not fit.
 * The caller puts the changed item back into the inventory.
 * @param {import("@minecraft/server").ItemStack} item @param {Slot} slot @param {string | undefined} attId
 */
export function fit(item, slot, attId) {
  const current = fitted(item);
  if (attId) {
    const att = registry.get(attId);
    if (!att || att.slot !== slot || !fits(att, item.typeId)) return false;
    current[slot] = attId;
  } else {
    delete current[slot];
  }
  safe(() => item.setDynamicProperty("fl:att", Object.keys(current).length ? JSON.stringify(current) : undefined));
  return true;
}

const FLAGS = new Set(["nv", "laser", "light", "flash", "bipod"]);

/** No attachments: every multiplier 1, nothing added, no flags. @returns {Mods} */
export function noMods() {
  return { spread: 1, ads: 1, vrec: 1, hrec: 1, velocity: 1, damage: 1, reload: 1, noise: 1, mag: 1, mag_add: 0, zoom: 1, nv: 0, laser: 0, light: 0, flash: 0, bipod: 0 };
}

/** The combined effect of a gun item's attachments. @param {import("@minecraft/server").ItemStack | undefined} item @returns {Mods} */
export function modifiers(item) {
  const m = noMods();
  for (const attId of Object.values(fitted(item))) {
    const att = attId ? registry.get(attId) : undefined;
    if (!att) continue;
    for (const [k, v] of Object.entries(att.mods)) {
      const key = /** @type {keyof Mods} */ (k);
      const n = Number(v);
      if (!(key in m) || !Number.isFinite(n)) continue;
      if (key === "mag_add") m.mag_add += n;
      else if (key === "zoom") m.zoom = Math.max(m.zoom, n);
      else if (FLAGS.has(key)) m[key] = Math.max(m[key], n ? 1 : 0);
      else m[key] *= n;
    }
  }
  return m;
}

/** A short description of an attachment's effects, for menus. @param {Attachment} att */
export function describe(att) {
  const words = {
    spread: "hip spread", ads: "aim spread", vrec: "vertical recoil", hrec: "horizontal recoil", velocity: "velocity",
    damage: "damage", reload: "reload time", noise: "noise", mag: "magazine",
  };
  /** @type {string[]} */
  const out = [];
  for (const [k, v] of Object.entries(att.mods)) {
    const n = Number(v);
    if (k === "zoom") out.push(n > 1 ? `${n}x zoom` : "1x sight");
    else if (k === "mag_add") out.push(`+${n} rounds`);
    else if (k === "nv") out.push("night vision");
    else if (k === "laser") out.push("laser");
    else if (k === "light") out.push("flashlight");
    else if (k === "flash") out.push("no flash");
    else if (k === "bipod") out.push("braced when crouched");
    else if (k in words) {
      const pct = Math.round((n - 1) * 100);
      const good = k === "velocity" || k === "damage" || k === "mag" ? pct > 0 : pct < 0;
      out.push(`${good ? "§a" : "§c"}${pct > 0 ? "+" : ""}${pct}% ${words[/** @type {keyof typeof words} */ (k)]}§r`);
    }
  }
  return out.join(", ");
}
