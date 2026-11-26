"""The twelve firearms, each built after its real counterpart in quarter-pixel units (see kit.py for the frame
and the bones). Each gun also says how it animates (`anim`), where its attachments mount and what its
magazine looks like (`mag_profile`, which magazine attachments follow).

The models live in guns_a.py (pistols, SMGs), guns_b.py (rifles, LMG, DMR), guns_c.py (shotgun, sniper,
launchers), guns_d.py (Desert Eagle, P90), guns_e.py (SCAR-H, PKM) and guns_f.py (Barrett M82A1); gunbase.py holds
the shared materials and helpers.
"""
from __future__ import annotations

from guns_a import glock17, m1911, mp5, ump45
from guns_b import ak47, m249, m4a1, svd
from guns_c import awm, carl_gustaf, rem870, rpg7
from guns_d import deagle, p90
from guns_e import pkm, scar_h
from guns_f import barrett

GUNS = {
    "glock17": glock17, "m1911": m1911, "mp5": mp5, "ump45": ump45, "m4a1": m4a1, "ak47": ak47, "m249": m249,
    "rem870": rem870, "awm": awm, "svd": svd, "carl_gustaf": carl_gustaf, "rpg7": rpg7,
    "deagle": deagle, "p90": p90, "scar_h": scar_h, "barrett": barrett, "pkm": pkm,
}
