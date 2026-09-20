#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""grant_kal_s358.py -- S358_CASH_LOG: Dr Bhawna gets the 'Kal ka hisaab' tile.

A DATA EDIT on the parent's /root/portal/tile_grants.json (v23 a5f8b3b1, S342),
declared to the parent: 'Kal ka hisaab' is appended to bhawna's extra list, the
version becomes 24, one sentence joins the _note.  Written with the same
json.dumps shape the file already uses (indent 2, ensure_ascii False), so the
result is byte-predictable.  Nothing else in the file moves; the page's own gate
(bhawna is a medical viewer named in darpan_kal.recipients) is unchanged.

    python3 grant_kal_s358.py IN OUT
"""
import json
import sys

TILE = "Kal ka hisaab"
NOTE = (" | v24 (S358, 20-Sep-2026): 'Kal ka hisaab' to bhawna as well -- the owner's ruling that Darpan's daily cash "
        "goes to him or to Dr Bhawna and BOTH log what they received; her view of the page is the English "
        "'Cash handed to you' list with the log buttons (S358). Nothing else moves.")

d = json.load(open(sys.argv[1], encoding="utf-8"))
if int(d.get("version") or 0) != 23:
    raise SystemExit("!! tile_grants.json is version %s, not 23 -- nothing written" % d.get("version"))
u = d["users"].setdefault("bhawna", {})
extra = u.setdefault("extra", [])
if TILE not in extra:
    extra.append(TILE)
if TILE in (u.get("mask") or []):
    u["mask"].remove(TILE)
d["version"] = 24
d["_note"] = d["_note"] + NOTE
open(sys.argv[2], "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
print("tile_grants.json v23 -> v24: bhawna + '%s'" % TILE)
