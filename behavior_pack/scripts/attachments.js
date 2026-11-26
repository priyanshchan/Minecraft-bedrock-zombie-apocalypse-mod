// Weapon attachments: the slots every gun has, where fitted attachments are stored, and how they change a
// gun. No attachment items exist yet; this is the frame future ones plug into (see docs/attachments.md).
import { GUN_DATA } from "./gundata.js";
import { safe } from "./core.js";

/** @typedef {"optic" | "muzzle" | "underbarrel" | "side" | "stock" | "magazine"} Slot */
/** @type {Slot[]} */
export const SLOTS = ["optic", "muzzle", "underbarrel", "side", "stock", "magazine"];

/**
 * How an attachment changes a gun. Multipliers default to 1, `magazine` adds rounds.
 * @typedef {object} Mods
 * @property {number} spread    cone of fire
 * @property {number} recoil    camera kick and spread growth
 * @property {number} damage
 * @property {number} range
 * @property {number} reload    reload time
 * @property {number} noise     how far the shot is heard (suppressors)
 * @property {number} magazine  extra rounds
 */

/**
 * @typedef {object} Attachment
 * @property {string} id        the attachment's item id
 * @property {Slot} slot
 * @property {string} name
 * @property {string[]} guns    gun item ids it fits ("*" for every gun with the slot)
 * @property {Partial<Mods>} mods
 */

/** @type {Map<string, Attachment>} */
const registry = new Map();

/** Registers an attachment (future attachment items call this). @param {Attachment} att */
export function registerAttachment(att) {
  registry.set(att.id, att);
}

/** @param {string} id */
export function attachment(id) {
  return registry.get(id);
}

/** The slots a gun offers: every mount its model has, plus the magazine. @param {string} gunId @returns {Slot[]} */
export function slotsOf(gunId) {
  const mounts = /** @type {Record<string, Record<string, unknown>>} */ (GUN_DATA.mounts)[gunId];
  if (!mounts) return [];
  return /** @type {Slot[]} */ ([...Object.keys(mounts), "magazine"].filter((s) => SLOTS.includes(/** @type {Slot} */ (s))));
}

/** Whether an attachment fits a gun. @param {Attachment} att @param {string} gunId */
export function fits(att, gunId) {
  return slotsOf(gunId).includes(att.slot) && (att.guns.includes("*") || att.guns.includes(gunId));
}

/** Attachments fitted to a gun item: slot -> attachment id. @param {import("@minecraft/server").ItemStack | undefined} item @returns {Partial<Record<Slot, string>>} */
export function fitted(item) {
  if (!item) return {};
  const raw = safe(() => item.getDynamicProperty("fl:att"));
  if (typeof raw !== "string") return {};
  try {
    return JSON.parse(raw);
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
  safe(() => item.setDynamicProperty("fl:att", JSON.stringify(current)));
  return true;
}

/** The combined effect of a gun item's attachments. @param {import("@minecraft/server").ItemStack | undefined} item @returns {Mods} */
export function modifiers(item) {
  /** @type {Mods} */
  const m = { spread: 1, recoil: 1, damage: 1, range: 1, reload: 1, noise: 1, magazine: 0 };
  for (const attId of Object.values(fitted(item))) {
    const att = attId ? registry.get(attId) : undefined;
    if (!att) continue;
    for (const [k, v] of Object.entries(att.mods)) {
      const key = /** @type {keyof Mods} */ (k);
      if (key === "magazine") m.magazine += Number(v);
      else m[key] *= Number(v);
    }
  }
  return m;
}
