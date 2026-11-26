// The Gunsmith: fit and remove attachments on the guns in your inventory. Opened from the Field Radio, or by using
// an attachment item (which goes straight to fitting it).
import { ItemStack, system } from "@minecraft/server";
import { ActionFormData, FormCancelationReason } from "@minecraft/server-ui";
import { container, countItem, cue, giveItem, id, isCreative, NS, onUse, safe, takeItem, tell } from "./core.js";
import { allAttachments, attachment, choicesFor, describe, fit, fits, fitted, SLOT_NAMES, slotsOf } from "./attachments.js";
import { GUNS, magOf, magSizeOf, setMag } from "./weapons.js";

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

const icon = (/** @type {string} */ itemId) => `textures/items/${NS}/${itemId.replace(`${NS}:`, "")}`;

/** The guns in a player's inventory: [slot index, item]. @param {import("@minecraft/server").Player} player */
function gunsCarried(player) {
  const inv = container(player);
  /** @type {Array<[number, import("@minecraft/server").ItemStack]>} */
  const out = [];
  if (!inv) return out;
  for (let i = 0; i < inv.size; i++) {
    const it = safe(() => inv.getItem(i));
    if (it && GUNS[it.typeId]) out.push([i, it]);
  }
  // the gun in hand first
  const sel = player.selectedSlotIndex;
  out.sort((a, b) => (a[0] === sel ? -1 : b[0] === sel ? 1 : a[0] - b[0]));
  return out;
}

/** Puts an attachment on (or, with `attId` undefined, takes it off) the gun in inventory slot `slotIndex`: the new
 * part comes out of the inventory and the old one goes back into it. @param {import("@minecraft/server").Player} player
 * @param {number} slotIndex @param {import("./attachments.js").Slot} slot @param {string | undefined} attId */
export function swapAttachment(player, slotIndex, slot, attId) {
  const inv = container(player);
  const item = inv ? safe(() => inv.getItem(slotIndex)) : undefined;
  if (!inv || !item || !GUNS[item.typeId]) return false;
  const creative = isCreative(player);
  const old = fitted(item)[slot];
  if (old === attId) return true;
  if (attId) {
    const att = attachment(attId);
    if (!att || att.slot !== slot || !fits(att, item.typeId)) return false;
    if (!creative && countItem(player, attId) < 1) return false;
    if (!creative) takeItem(player, attId, 1);
  }
  fit(item, slot, attId);
  safe(() => inv.setItem(slotIndex, item));
  if (old && !creative) giveItem(player, old, 1);
  // a smaller magazine gives back the rounds that no longer fit
  if (slot === "magazine") {
    const size = magSizeOf(item.typeId, item);
    const loaded = magOf(player, item.typeId);
    if (loaded > size) {
      setMag(player, item.typeId, size);
      if (!creative) giveItem(player, GUNS[item.typeId].ammo, loaded - size);
    }
  }
  cue(player, `${NS}.attach`, 1, 0.95 + Math.random() * 0.1);
  return true;
}

/** @param {import("@minecraft/server").Player} player @param {number} slotIndex */
async function gunMenu(player, slotIndex) {
  const inv = container(player);
  const item = inv ? safe(() => inv.getItem(slotIndex)) : undefined;
  if (!item || !GUNS[item.typeId]) return;
  const g = GUNS[item.typeId];
  const on = fitted(item);
  const slots = slotsOf(item.typeId);
  const form = new ActionFormData().title(`§l${g.name}`)
    .body(`§7${g.caliber} · ${g.mode} · ${magSizeOf(item.typeId, item)} rounds\n§7Pick a slot to change what is fitted.`);
  for (const s of slots) {
    const a = on[s] ? attachment(on[s] ?? "") : undefined;
    form.button(`§l${SLOT_NAMES[s]}\n§r§8${a ? a.name : "factory"}`, a ? icon(a.id) : undefined);
  }
  form.button("§lDone");
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined || res.selection >= slots.length) return;
  await slotMenu(player, slotIndex, slots[res.selection]);
  await gunMenu(player, slotIndex);
}

/** @param {import("@minecraft/server").Player} player @param {number} slotIndex @param {import("./attachments.js").Slot} slot */
async function slotMenu(player, slotIndex, slot) {
  const inv = container(player);
  const item = inv ? safe(() => inv.getItem(slotIndex)) : undefined;
  if (!item || !GUNS[item.typeId]) return;
  const creative = isCreative(player);
  const current = fitted(item)[slot];
  const options = choicesFor(item.typeId, slot).filter((a) => creative || countItem(player, a.id) > 0 || a.id === current);
  const form = new ActionFormData().title(`§l${GUNS[item.typeId].name} - ${SLOT_NAMES[slot]}`)
    .body(options.length ? "§7Attachments you carry that fit this slot." : "§7You carry nothing that fits this slot. Craft attachments, or take them from fallen soldiers.");
  /** @type {Array<string | undefined>} */
  const picks = [];
  for (const a of options) {
    const have = creative ? "" : ` §8x${countItem(player, a.id)}`;
    form.button(`${a.id === current ? "§2" : ""}§l${a.name}${have}\n§r§8${describe(a).replace(/§./g, "")}`, icon(a.id));
    picks.push(a.id);
  }
  if (current) {
    form.button("§c§lRemove\n§r§8Back to the factory part");
    picks.push(undefined);
  }
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return;
  const pick = picks[res.selection];
  if (!swapAttachment(player, slotIndex, slot, pick)) tell(player, "§cThat does not fit.");
}

/** The Gunsmith, from the Field Radio. @param {import("@minecraft/server").Player} player */
export async function gunsmith(player) {
  const guns = gunsCarried(player);
  if (!guns.length) {
    tell(player, "§7Carry a gun to fit attachments.");
    return;
  }
  if (guns.length === 1) return gunMenu(player, guns[0][0]);
  const form = new ActionFormData().title("§lGunsmith").body("§7Choose a gun to work on.");
  for (const [, it] of guns) {
    const n = Object.keys(fitted(it)).length;
    form.button(`§l${GUNS[it.typeId].name}\n§r§8${GUNS[it.typeId].caliber}${n ? ` · ${n} attachment${n > 1 ? "s" : ""}` : ""}`, icon(it.typeId));
  }
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return;
  await gunMenu(player, guns[res.selection][0]);
}

/** Using an attachment item: pick which gun to fit it to. @param {import("@minecraft/server").Player} player @param {string} attId */
async function fitFromItem(player, attId) {
  const att = attachment(attId);
  if (!att) return;
  const guns = gunsCarried(player).filter(([, it]) => choicesFor(it.typeId, att.slot).some((a) => a.id === attId));
  if (!guns.length) {
    tell(player, `§7The ${att.name} fits: §f${att.guns.map((g) => GUNS[g]?.name ?? g).join(", ")}§7. Carry one of them to fit it.`);
    return;
  }
  const form = new ActionFormData().title(`§l${att.name}`).body(`§7${describe(att)}\n\nFit it to:`);
  for (const [, it] of guns) {
    const cur = fitted(it)[att.slot];
    form.button(`§l${GUNS[it.typeId].name}\n§r§8${cur ? `replaces ${attachment(cur)?.name}` : SLOT_NAMES[att.slot]}`, icon(it.typeId));
  }
  const res = await show(player, form);
  if (!res || res.canceled || res.selection === undefined) return;
  const [slotIndex] = guns[res.selection];
  if (swapAttachment(player, slotIndex, att.slot, attId)) tell(player, `§aFitted the ${att.name}.`);
}

/** A gun item with attachments already fitted (for class kits). @param {string} gunId @param {string[]} attIds */
export function gunWith(gunId, attIds) {
  const item = new ItemStack(gunId, 1);
  for (const a of attIds) {
    const att = attachment(id(a));
    if (att) fit(item, att.slot, att.id);
  }
  return item;
}

export function init() {
  const ids = new Set(allAttachments().map((a) => a.id));
  onUse((player, item, repeat) => {
    if (!ids.has(item.typeId)) return false;
    if (!repeat) fitFromItem(player, item.typeId);
    return true;
  });
}
