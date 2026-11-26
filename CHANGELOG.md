# Changelog

## 1.1.0: the guns, rebuilt

- **Every weapon remodelled** at quarter-pixel detail: about 30% larger in third person, and larger and closer in first person.
  - The AR, SMG, LMG, shotgun, sniper rifle, pistol, rocket launcher, knife and grenades are all new.
  - So are the Red Fang rifle, marksman rifle and RPG the AI soldiers carry.
  - New detail: round barrels, chamfered receivers, rails with cross slots, M-LOK handguards, curved magazines, flip-up sights,
    glass in scopes and sights, bipods, and lighting painted from above.
- **Gun animations**, in first and third person:
  - firing: recoil, and bolt, slide or pump cycling
  - reloading: magazine out and in, then racking the gun; the shotgun loads shell by shell, the LMG swaps its box, the launcher loads a new rocket
  - jam clearing and malfunction clearing
  - other players see you reach for the magazine or rack the gun
- **Jams and malfunctions:** a small chance per round, cleared by double-tapping crouch. A jam costs one round. A malfunction strips the
  magazine, racks and reloads, and costs two rounds. Jams can be turned off in Settings.
- **Ready for attachments:**
  - every gun has optic, muzzle, underbarrel, side-rail, stock and magazine mounts, with its factory parts in separate bones
  - guns render through their own controller with a slot for showing and hiding parts
  - `scripts/attachments.js` stores fitted attachments on the gun and applies their effects
  - `docs/attachments.md` lists every mount
- Inventory icons rendered from the new models.

## 1.0.0

The first release: **Frontline: NATO vs Red Fang** (the repository first held plans for a zombie add-on; that was dropped for this).

- Conquest battles from the Field Radio: 3 to 5 capture flags with sandbag forts, headquarters for each side with vehicle pads,
  tickets, ticket bleed, flags that rise and fall as they are captured, a sidebar and a status bar.
- Six AI soldier types in two factions, with their own 3D gear and guns, that fight each other and push on the flags.
- Four classes (Assault, Engineer, Support, Recon) with deploy-anywhere-you-hold spawning and spawn beacons.
- Seven guns, a rocket launcher, frag and smoke grenades and a knife, all as 3D models in the hand. The guns have magazines, reloads,
  bursts, spread, headshots, tracers, muzzle flashes and recoil shake. Players holding a gun show an aiming pose to others.
- Drivable jeeps (4 seats) and tanks (turret follows the commander's view, main cannon), team paint, repairs and wrecks.
- Medkits, ammo boxes, binoculars (spotting), ammo crates, sandbags, barbed wire.
- Ranks on name tags, score, kills and deaths, a kill feed.
- AI patrols outside battles, reported by radio.
- 26 synthesised sounds, 13 particle effects, all art generated from code.
