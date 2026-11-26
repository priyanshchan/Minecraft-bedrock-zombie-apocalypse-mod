# Changelog

## 1.2.0: real guns, real ballistics, attachments

- **Five more guns** (seventeen in all): IWI Desert Eagle (.50 AE), FN P90 (5.7x28mm, its magazine on top), FN SCAR-H
  (7.62x51mm NATO), Barrett M82A1 (.50 BMG) and the PKM (7.62x54mmR), with four new cartridge items. Red Fang support
  soldiers now carry the PKM.
- **Detail pass on every gun**, now including the MP5A3, UMP45, SVD, Carl Gustaf and RPG-7.

- **Twelve real-world guns** replace the old seven, each firing its real cartridge:
  - pistols: Glock 17 (9x19mm), Colt M1911A1 (.45 ACP)
  - SMGs: H&K MP5A3 (9x19mm), H&K UMP45 (.45 ACP)
  - rifles: Colt M4A1 (5.56x45mm), AKM (7.62x39mm), FN M249 SAW (5.56x45mm)
  - Remington 870 (12 gauge), AI AWM (.338 Lapua Magnum), SVD Dragunov (7.62x54mmR)
  - launchers: Carl Gustaf M4 (84mm), RPG-7 (PG-7V)
- **Nine cartridge items** replace the old ammo: 9x19mm, .45 ACP, 5.56x45mm, 7.62x39mm, 7.62x54mmR, .338 Lapua Magnum, 12 gauge,
  84mm and PG-7V.
- **Far more detailed models:** the Glock, M1911, M4A1, AKM, M249, 870 and AWM rebuilt from 110 to 370 parts each, and every gun has round bars drawn as 12- and 16-sided sections. The
  details are real: rails with teeth, real slots, pins, screws, roll marks, feed lips with the top round, sights and scopes with glass.
  Soldiers carry lighter versions of the same guns.
- **33 attachments** with their own 3D models, fitted at the new **Gunsmith** (Field Radio) or by using the item:
  - optics: 10, from a reflex sight to a 12x sniper scope, including a 3x magnifier and a night-vision scope
  - muzzles: 7, including suppressors, a compensator, a brake, a flash hider and chokes
  - underbarrel: 5 grips and a bipod
  - side rail: lasers and flashlights
  - stocks and magazines: 3 stocks; extended, drum and quick-pull magazines, a shotgun tube and a 300-round box
  - They show on the gun in your hand, change its recoil, spread, velocity, noise, magazine and reload, and some add zoom, night
    vision, a laser dot or a flashlight that really lights the world. Craftable, and dropped by soldiers.
- **Real ballistics:** every round is a simulated bullet with its cartridge's muzzle velocity, air drag and gravity drop, stepped each
  tick. Sights are zeroed, damage falls off as the bullet slows, tracers show the arc and near misses crack past you.
- **Universal recoil and spread:**
  - the view kicks up and sideways with each shot and settles after
  - hip and aimed spread per gun, wider when moving, sprinting or jumping
  - bloom grows with sustained fire and recovers
- **Real fire modes:** hold for automatic fire at each gun's rate (600 to 800 rpm); semi-automatic, pump and bolt actions.
- New animations: the M1911's hammer, the AK's and SVD's carriers, the Carl Gustaf's venturi reload.
- New sounds: .45 pistol, AK, Dragunov, suppressed shot, attachment click, bullet crack.
- New settings: recoil moves the view, bullet drop (off/realistic/heavy), tracers.
- Class kits differ by side (NATO: M4A1, MP5, AWM, Carl Gustaf, Glock; Red Fang: AKM, UMP45, SVD, RPG-7, M1911), and kit guns come with
  attachments fitted.
- Old guns and ammunition from 1.1 are gone: worlds that had them lose those items.

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
