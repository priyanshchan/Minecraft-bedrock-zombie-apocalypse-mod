// Plays the add-on's scripts in a simulated world and checks what happens.
// Usage: node tools/sim/test.js   (copies the scripts next to the stand-in modules in a temp folder and runs them)
import assert from "node:assert";
import { cpSync, mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..");
const dir = mkdtempSync(join(tmpdir(), "frontline-sim-"));
cpSync(join(root, "behavior_pack", "scripts"), join(dir, "scripts"), { recursive: true });
for (const [name, file] of [["server", "server.js"], ["server-ui", "server-ui.js"]]) {
  const pkg = join(dir, "node_modules", "@minecraft", name);
  mkdirSync(pkg, { recursive: true });
  cpSync(join(here, file), join(pkg, "index.js"));
  writeFileSync(join(pkg, "package.json"), JSON.stringify({ name: `@minecraft/${name}`, type: "module", main: "index.js" }));
}
writeFileSync(join(dir, "package.json"), JSON.stringify({ type: "module" }));

// Seeded randomness so every run is the same.
let seed = 7;
Math.random = () => {
  seed = (seed + 0x6d2b79f5) >>> 0;
  let t = seed;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

const mc = await import(pathToFileURL(join(dir, "node_modules", "@minecraft", "server", "index.js")).href);
const ui = await import(pathToFileURL(join(dir, "node_modules", "@minecraft", "server-ui", "index.js")).href);
const { world, system, advance, makePlayer, ItemStack, entities, explosions, getBlockType, kill } = mc;
const load = (m) => import(pathToFileURL(join(dir, "scripts", m)).href);
await load("main.js");
const core = await load("core.js");
const weapons = await load("weapons.js");
const battle = await load("battle.js");
const patrols = await load("patrols.js");
const vehicles = await load("vehicles.js");

let passed = 0;
const check = (cond, msg) => {
  assert.ok(cond, msg);
  passed++;
};

world.afterEvents.worldLoad.fire({});

// ---- joining: a radio, then the side chosen on the form
const alice = makePlayer("Alice");
ui.answers.push(0); // NATO
world.afterEvents.playerSpawn.fire({ player: alice, initialSpawn: true });
await advance(80);
check(alice.inventory.slots.some((s) => s?.typeId === "frontline:field_radio"), "a new player gets a Field Radio");
check(alice.hasTag("fl_team_nato"), "choosing NATO tags the player");
check(alice.nameTag.includes("[NATO]"), "the name tag shows the team");

// ---- guns: automatic fire, the magazine, a hit, a reload
const AR = "frontline:m4a1";
const rifle = new ItemStack(AR, 1);
alice.inventory.slots[0] = rifle;
alice.inventory.slots[1] = new ItemStack("frontline:ammo_556", 60);
const body = { x: 0, y: -0.07, z: 1 };
const bl = Math.hypot(body.x, body.y, body.z);
alice.view = { x: body.x / bl, y: body.y / bl, z: body.z / bl }; // aim at the chest
const foe = world.getDimension("minecraft:overworld").spawnEntity("frontline:redfang_fighter", { x: 0.5, y: 64, z: 10.5 });
await advance(5);
const pitch0 = alice.rotation.x;
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(10);
const afterBurst = weapons.magOf(alice, AR);
check(afterBurst >= 25 && afterBurst <= 27, "a press of the trigger fires a short automatic burst at the gun's rate");
check(foe.health.currentValue < 30 && foe.health.currentValue > 0, "the burst hits the enemy in front (body shots)");
check(alice.heard.includes("frontline.hitmarker"), "a hit plays the hit marker");
check(alice.anims.some((a) => a.n === "animation.frontline.player.aim_rifle"), "holding a rifle plays the aiming pose");
check(mc.particles.some((p) => p.effect === "frontline:tracer"), "bullets leave tracers");
for (const down of [true, false, true, false]) {
  alice.isSneaking = down;
  await advance(2);
}
await advance(60);
check(weapons.magOf(alice, AR) === 30, "double-tapping crouch reloads to a full magazine");
check(core.countItem(alice, "frontline:ammo_556") === 60 - (30 - afterBurst), "the reload takes the rounds from the reserve");
check(alice.bar.includes("Colt M4A1") && alice.bar.includes("5.56x45mm"), "the HUD shows the gun, its caliber and its ammo");
check(alice.cooldowns.some((c) => c.category === "frontline_m4a1" && c.ticks === 3), "each shot starts the gun's fire animation (a 3-tick cooldown)");
check(alice.cooldowns.some((c) => c.category === "frontline_m4a1" && c.ticks === 46), "a reload starts the gun's reload animation (46 ticks)");
check(alice.anims.some((a) => a.n === "animation.frontline.player.reload"), "others see the reload arm motion");

// recoil: firing kicks the view upwards (pitch goes negative), then it settles part of the way back
alice.rotation = { x: 0, y: 0 };
alice.view = { x: 0, y: 0.5, z: -0.866 }; // into the sky, away from everyone
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(1);
check(alice.rotation.x < 0, "recoil kicks the view up");
await advance(5);
const kicked = alice.rotation.x; // the top of the burst's climb
await advance(30);
check(alice.rotation.x > kicked + 0.5 && alice.rotation.x < 0, "after the burst the view settles back part of the way");
for (const down of [true, false, true, false]) {
  alice.isSneaking = down;
  await advance(2);
}
await advance(60);

// a teammate in the line of fire is not shot
const buddy = world.getDimension("minecraft:overworld").spawnEntity("frontline:nato_rifleman", { x: 0.5, y: 64, z: 5.5 });
const foeBefore = foe.health.currentValue;
alice.view = { x: body.x / bl, y: body.y / bl, z: body.z / bl };
await advance(20);
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(10);
check(buddy.health.currentValue === 30, "friendly soldiers are not hit");
check(foe.health.currentValue < foeBefore, "shots pass a teammate and hit the enemy behind");
if (foe.isValid) {
  world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
  await advance(10);
}

// kills and headshots
check(!foe.isValid, "the enemy goes down");
check(core.getNumber(alice, "fl:score") >= 100, "a kill scores 100");
check(alice.messages.some((m) => m.includes("Colt M4A1")), "the kill feed names the weapon");
buddy.remove();
const foe2 = world.getDimension("minecraft:overworld").spawnEntity("frontline:redfang_fighter", { x: 0.5, y: 64, z: 12.5 });
alice.view = { x: 0, y: 0, z: 1 };
alice.isSneaking = true; // crouching aims: a much tighter spread
await advance(20);
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(10);
alice.isSneaking = false;
check(!foe2.isValid, "one aimed burst to the head kills");
check(alice.messages.some((m) => m.includes("HEADSHOT")), "the kill feed marks the headshot");
for (const down of [true, false, true, false]) {
  alice.isSneaking = down;
  await advance(2);
}
await advance(60);

// ---- ballistics: bullets fly at their real speed, slow down and drop
const bal = await load("ballistics.js");
const eye0 = { x: 0.5, y: 200, z: 0.5 };
bal.launch(alice, eye0, { x: 0, y: 0, z: 1 }, { speed: 375 / 20, drag: 0.0024, damage: 5, headshot: 1.8, weapon: "test" });
await advance(10);
const shot = bal.snapshot().at(-1);
check(shot && shot.flown > 100 && shot.flown < 10 * 375 / 20, "a 9mm bullet flies about 18 blocks a tick, slowed by drag");
check(shot && shot.pos.y < eye0.y - 0.8, "and drops under gravity (about a block after half a second)");
const vz = shot ? shot.vel.z : 99;
await advance(10);
const later = bal.snapshot().at(-1);
check(later && later.vel.z < vz && later.vel.y < shot.vel.y, "it keeps slowing and falls ever faster");
// a 9mm round fired level from head height: how long it takes to cover 140 blocks and how far it has dropped
const head0 = { x: 40.5, y: 65.62, z: 0.5 };
bal.launch(alice, head0, { x: 0, y: 0, z: 1 }, { speed: 375 / 20, drag: 0.0024, damage: 5, headshot: 1.8, weapon: "test" });
let ticksTo140 = 0;
let at140;
for (let i = 0; i < 30 && !at140; i++) {
  await advance(1);
  ticksTo140++;
  at140 = bal.snapshot().find((b) => Math.abs(b.pos.x - 40.5) < 0.01 && b.pos.z - 0.5 >= 140);
}
check(at140 && ticksTo140 >= 7, "a pistol round takes the better part of half a second to fly 140 blocks");
check(at140 && at140.pos.y < head0.y - 0.6, "by then it has dropped below head height: hold over at long range");
const pistol = new ItemStack("frontline:glock17", 1);
alice.inventory.slots[0] = pistol;
alice.inventory.slots[3] = new ItemStack("frontline:ammo_9mm", 34);
alice.view = { x: 0, y: 0.3, z: -0.95 };
await advance(10);
world.afterEvents.itemUse.fire({ source: alice, itemStack: pistol });
world.afterEvents.itemUse.fire({ source: alice, itemStack: pistol });
await advance(1);
check(weapons.magOf(alice, "frontline:glock17") === 16, "a semi-automatic fires once per press, however fast you press");
alice.inventory.slots[0] = rifle;
await advance(20);

// ---- stoppages: a jam is cleared by double-tapping crouch, a malfunction strips and reloads
alice.inventory.slots[0] = rifle;
alice.selectedSlotIndex = 0;
weapons.GUNS[AR].jam = 1; // every round jams
await advance(20);
const beforeJam = weapons.magOf(alice, AR);
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(10);
const kind = weapons.stoppage(alice, AR);
check(kind === "jam" || kind === "malfunction", "a round can jam the gun");
check(weapons.magOf(alice, AR) === beforeJam - 1, "a stoppage stops automatic fire after the round that jammed");
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(10);
check(weapons.magOf(alice, AR) === beforeJam - 1, "a stopped gun does not fire");
check(alice.bar.includes("JAMMED") || alice.bar.includes("MALFUNCTION"), "the status bar says the gun is stopped");
weapons.GUNS[AR].jam = 0;
for (const down of [true, false, true, false]) {
  alice.isSneaking = down;
  await advance(2);
}
check(alice.cooldowns.some((c) => c.category === "frontline_m4a1" && c.ticks === (kind === "jam" ? 28 : 64)), "clearing plays the gun's clearing animation");
await advance(70);
check(!weapons.stoppage(alice, AR), "double-tapping crouch clears the stoppage");
check(weapons.magOf(alice, AR) === (kind === "jam" ? beforeJam - 2 : 30), "a jam loses the stuck round; a malfunction strips and reloads");
// the same seeded run gives the other kind of stoppage too
weapons.GUNS[AR].jam = 1;
let other;
for (let i = 0; i < 40 && !other; i++) {
  alice.inventory.slots[1] = new ItemStack("frontline:ammo_556", 60);
  if (weapons.magOf(alice, AR) <= 2) {
    weapons.startReload(alice, AR);
    await advance(60);
  }
  await advance(20);
  world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
  await advance(4);
  const k = weapons.stoppage(alice, AR);
  if (k && k !== kind) other = k;
  if (k) {
    for (const down of [true, false, true, false]) {
      alice.isSneaking = down;
      await advance(2);
    }
    await advance(70);
  }
}
weapons.GUNS[AR].jam = 0;
check(other !== undefined && !weapons.stoppage(alice, AR), "both kinds of stoppage happen and both clear");

// ---- attachments: the catalogue, fitting, their effects and their models on the gun
const att = await load("attachments.js");
const smith = await load("gunsmith.js");
check(att.allAttachments().length >= 30, "there are 30+ attachments");
check(att.slotsOf(AR).includes("optic") && att.slotsOf(AR).includes("muzzle") && att.slotsOf(AR).includes("underbarrel") && att.slotsOf(AR).includes("magazine"), "the M4A1 offers optic, muzzle, underbarrel and magazine slots");
check(att.fit(rifle, "magazine", "frontline:extended_mag"), "an attachment fits its slot");
check(!att.fit(rifle, "optic", "frontline:extended_mag"), "an attachment does not fit another slot");
check(!att.fit(rifle, "optic", "frontline:sniper_12x"), "a 12x sniper scope does not fit an M4A1");
check(weapons.magSize(alice, AR) === 45, "an extended magazine holds half as many rounds again");
att.fit(rifle, "magazine", undefined);
check(weapons.magSize(alice, AR) === 30, "removing it restores the magazine");
const m = att.modifiers((() => { const it = new ItemStack(AR, 1); att.fit(it, "underbarrel", "frontline:vertical_grip"); att.fit(it, "muzzle", "frontline:compensator"); return it; })());
check(m.vrec < 0.7 && m.hrec < 0.8, "a vertical grip and a compensator cut both kinds of recoil");
alice.inventory.slots[4] = new ItemStack("frontline:red_dot", 1);
check(smith.swapAttachment(alice, 0, "optic", "frontline:red_dot"), "the gunsmith fits a carried attachment");
check(!alice.inventory.slots[4] || alice.inventory.slots[4].amount === 0 || core.countItem(alice, "frontline:red_dot") === 0, "fitting it uses up the attachment item");
check(att.fitted(alice.inventory.slots[0]).optic === "frontline:red_dot", "the gun remembers what is fitted");
alice.selectedSlotIndex = 0;
await advance(3);
check(alice.cooldowns.some((c) => c.category === "frontline_att_red_dot" && c.ticks > 1), "holding it shows the red dot on the model (its cooldown category runs)");
smith.swapAttachment(alice, 0, "optic", undefined);
check(core.countItem(alice, "frontline:red_dot") === 1, "removing it gives the attachment back");
await advance(3);
check(alice.cooldowns.some((c) => c.category === "frontline_att_red_dot" && c.ticks === 1), "and hides it on the model");
// the laser sight paints a dot where you aim; the flashlight lights it; the night-vision scope sees in the dark
const rifle2 = alice.inventory.slots[0];
att.fit(rifle2, "side", "frontline:laser_light");
att.fit(rifle2, "optic", "frontline:night_vision_4x");
alice.inventory.slots[0] = rifle2;
alice.view = { x: body.x / bl, y: body.y / bl, z: body.z / bl };
mc.particles.length = 0;
alice.isSneaking = true;
await advance(10);
check(mc.particles.some((p) => p.effect === "frontline:laser_dot"), "a laser puts a red dot where the gun points");
check(mc.placed.some((p) => p.type === "minecraft:light_block_13"), "a flashlight lights up where the gun points");
check(alice.effects.has("night_vision"), "aiming through the night-vision scope gives night vision");
check(alice.effects.has("slowness"), "a magnified scope zooms in while aiming");
alice.isSneaking = false;
att.fit(rifle2, "side", undefined);
att.fit(rifle2, "optic", undefined);
alice.inventory.slots[0] = rifle2;
await advance(10);
check(!alice.effects.has("night_vision"), "night vision ends when you stop aiming");
check(mc.placed.at(-1).type === "minecraft:air", "the flashlight's light goes out when it is taken off");

// ---- the rocket launcher fires a rocket entity; a hit explodes
const launcher = new ItemStack("frontline:rpg7", 1);
alice.inventory.slots[0] = launcher;
await advance(10);
world.afterEvents.itemUse.fire({ source: alice, itemStack: launcher });
await advance(2);
const rocket = entities.find((e) => e.typeId === "frontline:rocket");
check(rocket && rocket.projectile.owner === alice && rocket.projectile.shot, "the RPG-7 fires a rocket owned by the player");
world.afterEvents.projectileHitBlock.fire({ projectile: rocket, dimension: rocket.dimension, location: { x: 0, y: 64, z: 20 }, source: alice });
await advance(2);
check(explosions.length === 1 && explosions[0].o.breaksBlocks === false, "the rocket explodes without breaking blocks by default");

// ---- gear: medkit heals, ammo box refills, binoculars spot
alice.health.currentValue = 8;
const medkit = new ItemStack("frontline:medkit", 2);
alice.inventory.slots[2] = medkit;
alice.selectedSlotIndex = 2;
world.afterEvents.itemUse.fire({ source: alice, itemStack: medkit });
await advance(2);
check(alice.health.currentValue === 16, "a medkit heals 8");
check(alice.inventory.slots[2].amount === 1, "the medkit is used up");
alice.selectedSlotIndex = 0;

// ---- a tank: the turret follows the commander, any item fires the cannon
const dim = world.getDimension("minecraft:overworld");
const tank = dim.spawnEntity("frontline:tank", { x: 20.5, y: 64, z: 0.5 });
await advance(2);
tank.riders = [alice];
alice.ridingOn = tank;
alice.rotation = { x: 10, y: 45 };
tank.rotation = { x: 0, y: 0 };
await advance(4);
check(tank.props.get("frontline:turret") === 45, "the turret turns with the commander's view");
check(tank.props.get("frontline:pitch") === 10, "the barrel follows the commander's pitch");
alice.inventory.slots[0] = rifle;
const magInTank = weapons.magOf(alice, AR);
world.afterEvents.itemUse.fire({ source: alice, itemStack: rifle });
await advance(2);
check(entities.some((e) => e.typeId === "frontline:tank_shell" && e.projectile.owner === alice), "using an item in the tank fires the cannon");
check(weapons.magOf(alice, AR) === magInTank, "the gun does not fire from the tank");
tank.riders = [];
alice.ridingOn = undefined;
tank.remove();

// ---- conquest
alice.location = { x: 0.5, y: 64, z: 0.5 };
alice.rotation = { x: 0, y: 0 }; // facing south (+z)
ui.answers.length = 0;
battle.startBattle(alice, { flags: 3, tickets: 50, bots: 4, vehicles: true });
await advance(40);
let b = battle.current();
check(b && b.points.length === 3, "a battle lays out three flags");
check(b.points.every((p) => p.built), "every flag is built");
check(b.hq.nato.built && b.hq.redfang.built, "both headquarters are built");
check(getBlockType({ x: b.points[0].x, y: b.points[0].y, z: b.points[0].z }) === "frontline:flag_neutral", "flag bases start neutral");
check(dim.getEntities({ tags: ["fl_flag_A"] }).length === 1, "flag A has its flag");
check(dim.getEntities({ tags: ["fl_veh_nato"] }).length === 3, "NATO gets two jeeps and a tank");
await advance(100);
check(dim.getEntities({ tags: ["fl_bot_nato"] }).length > 0 && dim.getEntities({ tags: ["fl_bot_redfang"] }).length > 0, "both sides send soldiers");

// capture flag A: stand on it alone
for (const e of dim.getEntities({ families: ["frontline_soldier"] })) e.remove();
const A = b.points[0];
alice.location = { x: A.x + 0.5, y: A.y + 1, z: A.z + 0.5 };
alice.health.currentValue = 20;
await advance(20 * 15);
b = battle.current();
check(b.points[0].owner === 1, "standing on a flag captures it for NATO");
check(getBlockType({ x: A.x, y: A.y, z: A.z }) === "frontline:flag_nato", "the flag base turns NATO blue");
check(dim.getEntities({ tags: ["fl_flag_A"] })[0].props.get("frontline:owner") === 1, "the flag flies NATO colours");
const ticketsBefore = b.tickets.redfang;
await advance(120);
check(battle.current().tickets.redfang < ticketsBefore, "holding more flags bleeds the enemy's tickets");

// a Red Fang soldier dying costs a ticket
const bot = dim.spawnEntity("frontline:redfang_fighter", { x: 0.5, y: 64, z: 90.5 });
bot.addTag("fl_battle");
const t0 = battle.current().tickets.redfang;
kill(bot, alice);
check(battle.current().tickets.redfang === t0 - 1, "a soldier's death costs its side a ticket");

// the deploy screen: class then spawn point
const deployPoints = battle.deployPoints("nato");
check(deployPoints.some((p) => p.label === "Flag A"), "a held flag is a deploy point");
const ui_ = await load("ui.js");
ui.answers.push(1, deployPoints.findIndex((p) => p.label === "Flag A")); // Engineer at flag A
await ui_.deploy(alice);
check(core.countItem(alice, "frontline:carl_gustaf") >= 1 && core.countItem(alice, "frontline:repair_tool") === 1, "the NATO Engineer kit is given (Carl Gustaf)");
check(alice.inventory.slots.some((it) => it?.typeId === "frontline:mp5" && att.fitted(it).optic === "frontline:reflex_sight"), "kit guns come with their attachments fitted");
check(alice.hasTag("fl_in_battle"), "deploying joins the battle");

// run the enemy out of tickets
battle.current().tickets.redfang = 1;
await advance(120);
check(!battle.current(), "the battle ends when a side runs out of tickets");
check(alice.titles.some((t) => t.t.includes("VICTORY")), "the winners see VICTORY");
await advance(220);
check(dim.getEntities({ tags: ["fl_battle"] }).length === 0, "the battle's soldiers, vehicles and flags are cleared away");
check(mc.commands.some((c) => c.startsWith("tickingarea remove fl_battle")), "the ticking area is removed");

// ---- patrols
const n = patrols.sendPatrol(alice);
check(n >= 2, "a patrol of two or more soldiers is sent");
check(alice.messages.some((m) => m.includes("patrol")), "the radio reports the patrol");

console.log(`sim: ${passed} checks passed`);
process.exit(0);
