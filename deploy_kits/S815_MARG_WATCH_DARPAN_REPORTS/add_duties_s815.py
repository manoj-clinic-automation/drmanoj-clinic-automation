#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""add_duties_s815.py DUTY_MAP_JSON OUT -- kit S815: two staff duties into the duty map (shared with the parent; no existing row is touched,
so no aaj_seed REWRITE piece can stop fitting, F-1024). Writes OUT with the same layout (indent 1, ensure_ascii as the file has it)."""
import json, sys

ROWS = [
    {"id": "darpan.mw_ask", "person": "darpan",
     "duty": "Answer the owner's Marg watch question on his own page -- one tap of the answers offered, an optional short line, no take-back "
             "(S815; the question is the owner's, from a row of the Marg watch; it leaves his page by itself when the owner closes that row)",
     "duty_hi": "Doctor sahab ka sawaal -- jawab chuniye", "tile": "Kal ka hisaab", "door": "/finance/darpan/kal",
     "door_marker": "Doctor sahab ka sawaal",
     "due_sql": "SELECT COUNT(*) AS n, MIN(substr(asked_at,1,10)) AS since FROM marg_watch_ask WHERE to_whom = 'darpan' AND staff_ref = 'darpan:card' "
                "AND answered_at IS NULL",
     "allowed_days": 2, "raise": True,
     "owner_line": "Darpan has not answered your Marg watch question: {n} since {since}", "coded": None},
    {"id": "shavez.mw_report", "person": "shavez",
     "duty": "Make again the sale report (Detail) the owner -- or the Marg watch by itself when several items rise on one closing with no record "
             "(D929) -- asked for, for the dates on the card; the card ticks and leaves when the files have come (S815)",
     "duty_hi": "Doctor sahab ne yeh report dobara maangi hai", "tile": "Aaj ki reports", "door": "/finance/reports/aaj",
     "door_marker": "Doctor sahab ne yeh report dobara maangi hai",
     "due_sql": "SELECT COUNT(*) AS n, MIN(substr(asked_at,1,10)) AS since FROM marg_watch_report WHERE closed_at IS NULL",
     "allowed_days": 2,
     "owner_line": "A sale report asked for again is not in yet: {n} since {since} (Shavez)", "coded": None},
]


def main():
    src, out = sys.argv[1:3]
    raw = open(src, encoding="utf-8").read()
    d = json.loads(raw)
    have = {x.get("id") for x in d["duties"]}
    for r in ROWS:
        if r["id"] in have:
            raise SystemExit("%s already in the map -- stopped" % r["id"])
    d["duties"].extend(ROWS)
    d["version"] = int(d["version"]) + 1
    d["kit"] = "S815_MARG_WATCH_DARPAN_REPORTS"
    asc = "\\u" in raw
    open(out, "w", encoding="utf-8").write(json.dumps(d, indent=1, ensure_ascii=asc) + ("\n" if raw.endswith("\n") else ""))
    print("version", d["version"], "duties", len(d["duties"]))


if __name__ == "__main__":
    main()
