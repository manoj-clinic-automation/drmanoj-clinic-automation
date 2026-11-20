#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s897.py -- kit S897: the two patched files, from the LIVE bytes (F-472), exact anchors, each used once.

  owner_console.py c8a2263d -> TO : (1) the Docterz-reports door mounted beside the off-days page (the same gate);
                                   (2) one console line that opens the door, after the 'Days not sitting' line.
  freshness_legs.json 35595a1e -> TO : one leg, 'clinic PC still sending after the switch' (S830's shape; pc_upload_watch).

    python3 make_s897.py <live owner_console.py> <live freshness_legs.json> <out dir>
"""
import hashlib, json, os, sys

OC_FROM = "c8a2263d"
LEGS_FROM = "35595a1e"


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def patch(s, old, new):
    if s.count(old) != 1:
        raise SystemExit("anchor not found exactly once: %r" % old[:70])
    return s.replace(old, new)


def main(oc, legs, out):
    for p, want in ((oc, OC_FROM), (legs, LEGS_FROM)):
        if md5(p)[:8] != want:
            raise SystemExit("%s is %s, not %s -- read the live file first" % (p, md5(p)[:8], want))
    s = open(oc, encoding="utf-8").read()
    s = patch(s, '''    try:                                                               # S868: the days he is not sitting (the same gate)
        import off_days as _s868_od                                    # noqa: PLC0415 -- beside this file
        _s868_od.init(app, db_getter, require_fn, unit)
    except Exception as _ex_s868:                                      # noqa: BLE001 -- the console stands without it
        print("off_days NOT mounted: %s" % _ex_s868, file=sys.stderr)
''', '''    try:                                                               # S868: the days he is not sitting (the same gate)
        import off_days as _s868_od                                    # noqa: PLC0415 -- beside this file
        _s868_od.init(app, db_getter, require_fn, unit)
    except Exception as _ex_s868:                                      # noqa: BLE001 -- the console stands without it
        print("off_days NOT mounted: %s" % _ex_s868, file=sys.stderr)
    try:                                                               # S897: the Docterz reports -- one door (the same gate)
        import docterz_door as _s897_dd                                # noqa: PLC0415 -- beside this file
        _s897_dd.init(app, db_getter, require_fn, unit)
    except Exception as _ex_s897:                                      # noqa: BLE001 -- the console stands without it
        print("docterz_door NOT mounted: %s" % _ex_s897, file=sys.stderr)
''')
    s = patch(s, '''        if os.path.exists(os.path.join(FIN, "off_days.py")):         # S868: one line that opens the not-sitting days
            out.append(L("n", "Not sitting today, or on a day ahead? Mark it -- nothing then asks for that day's consultation report",
                         href="/finance/console/off-days", link="Days not sitting"))
        return out
''', '''        if os.path.exists(os.path.join(FIN, "off_days.py")):         # S868: one line that opens the not-sitting days
            out.append(L("n", "Not sitting today, or on a day ahead? Mark it -- nothing then asks for that day's consultation report",
                         href="/finance/console/off-days", link="Days not sitting"))
        if os.path.exists(os.path.join(FIN, "docterz_door.py")):     # S897: one line that opens the Docterz reports door
            out.append(L("n", "Any Docterz CSV -- a long-period report, a clinical data report, a patient list -- goes in at one door",
                         href="/finance/console/docterz-reports", link="Docterz reports"))
        return out
''')
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "owner_console.py"), "w", encoding="utf-8", newline="").write(s)
    d = json.load(open(legs, encoding="utf-8"))
    names = {l.get("name") for l in d["legs"]}
    leg = {"name": "clinic PC still sending after the switch", "group": "Marg lane", "kind": "state_json",
           "target": "/root/followup_tracker/pc_upload_watch.state.json", "field": "last_ok_iso", "fail_field": "last_failure_iso",
           "max_age_h": 1,
           "note": "S897 (plan S492 s6.3) · pc_upload_watch.py every 10 min · before the switch always green ('not switched yet') · "
                   "red when the clinic PC uploads a call sheet AFTER the switch (the spare still feeding the readers: put _SPARE_MODE.txt on the PC); "
                   "clears by itself 26 h after the stray upload · red too when the watcher itself has stopped"}
    if leg["name"] in names:
        raise SystemExit("the leg is already in the live file")
    d["legs"].append(leg)
    raw = json.dumps(d, indent=1, ensure_ascii=False)
    open(os.path.join(out, "freshness_legs.json"), "w", encoding="utf-8", newline="\n").write(raw)
    for n in ("owner_console.py", "freshness_legs.json"):
        print("%s -> %s" % (n, md5(os.path.join(out, n))[:8]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
