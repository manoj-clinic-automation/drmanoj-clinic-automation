#!/usr/bin/env python3
"""make_s948.py -- S948_STAFF_CONSOLE: makes the TO bytes of /root/portal/calls_console.py from its FROM bytes (the
24-Nov bundle, eb13790d) and tile_grants.json v47 -> v48. Every anchor must occur exactly once, or nothing is written.
  python make_s948.py <from calls_console.py> <from tile_grants.json> <out dir>
"""
import hashlib
import json
import os
import sys

FROM_CC = "eb13790d1a761fedf6d5b0e2faa37d50"
TILE = "My Call Console"
GRANT_TO = ("shivani", "alisha", "shavez", "manoj")

EDITS = [
    ('        return jsonify({"ok": True, "msg": "Accepted \u2014 the call is off their count." if ans == "accept" else "Saved: it stands."})\n',
     '        try:                                                    # S948: an accepted verdict dispute moves no figure\n'
     '            con_ = sqlite3.connect("file:%s?mode=ro" % _review_db(), uri=True, timeout=3)\n'
     '            try:\n'
     '                fig_ = (con_.execute("SELECT fig FROM dispute WHERE id=?", (did,)).fetchone() or [""])[0]\n'
     '            finally:\n'
     '                con_.close()\n'
     '        except Exception:\n'
     '            fig_ = ""\n'
     '        if ans == "accept" and fig_ == "verdict":\n'
     '            return jsonify({"ok": True, "msg": "Accepted \u2014 the Call verdict is marked wrong; her figures are unchanged."})\n'
     '        return jsonify({"ok": True, "msg": "Accepted \u2014 the call is off their count." if ans == "accept" else "Saved: it stands."})\n'),
    ('    accepted = {(x.get("ref"), x.get("staff")) for x in rdisp if x.get("answer") == "accept"}\n',
     '    # S948 (cold review MUST 1): an accepted "Wrong?" on the Call verdict (fig "verdict") takes the call off no figure\n'
     '    accepted = {(x.get("ref"), x.get("staff")) for x in rdisp if x.get("answer") == "accept" and x.get("fig") != "verdict"}\n'),
    ("<button type=\"button\" class=\"rb p\" onclick=\"dAns(this,'accept')\">Accept \u2014 take it off the count</button>",
     "<button type=\"button\" class=\"rb p\" onclick=\"dAns(this,'accept')\">{{ 'Accept \u2014 the verdict was wrong' if x.fig == 'verdict' "
     "else 'Accept \u2014 take it off the count' }}</button>"),
    ('FIGS = ("missed", "wa", "not_logged", "mismatch")    # the figures a staff member may dispute, one call at a time\n',
     'FIGS = ("missed", "wa", "not_logged", "mismatch", "verdict")    # the figures a staff member may dispute, one call at a '
     'time (S948: "verdict" -- "Wrong?" on the Call verdict, from the staff page)\n'),
    ('             "wa": "WhatsApp not answered", "missed": "missed on duty"}\n',
     '             "wa": "WhatsApp not answered", "missed": "missed on duty", "verdict": "Call verdict questioned"}\n'),
    ('             "not_logged": "counted as not logged", "mismatch": "counted as staff ≠ AI"}\n',
     '             "not_logged": "counted as not logged", "mismatch": "counted as staff ≠ AI",\n'
     '             "verdict": "says the Call verdict is wrong"}\n'),
    ('            return jsonify({"ok": True, "msg": "Doctor sahab ko bhej diya."})\n\n    return True\n',
     '            return jsonify({"ok": True, "msg": "Doctor sahab ko bhej diya."})\n\n'
     '    # S948_STAFF_CONSOLE (the parent, S515, 24-Nov-2026): the staff\'s own Call Console (calls_staff.py, beside this file),\n'
     '    # registered here so it shares these readers and gates. A fault in it costs that page only, never this one.\n'
     '    try:\n'
     '        import calls_staff\n'
     '        calls_staff.register(app, gate, who, cfg_get, sys.modules[__name__], staff_gate, sso_user, pm)\n'
     '    except Exception as _e_s948:                                    # noqa: BLE001\n'
     '        print("calls_staff NOT mounted: %r" % (_e_s948,), file=sys.stderr)\n'
     '    return True\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(a):
    src_cc, src_tg, out = a[1], a[2], a[3]
    raw = open(src_cc, "rb").read()
    if md5(raw) != FROM_CC:
        sys.exit("calls_console.py is not the FROM bytes (%s) -- stop" % md5(raw)[:8])
    txt = raw.decode("utf-8")
    for old, new in EDITS:
        n = txt.count(old)
        if n != 1:
            sys.exit("anchor found %d times -- stop: %r" % (n, old[:60]))
        txt = txt.replace(old, new)
    if not txt.endswith("    return True\n"):
        sys.exit("the file's end moved -- stop")
    tg = json.load(open(src_tg, encoding="utf-8"))
    if tg.get("version") != 47:
        sys.exit("tile_grants.json is not v47 -- stop")
    for u in GRANT_TO:
        ent = tg["users"].get(u)
        if not isinstance(ent, dict):
            sys.exit("no grants entry for %s -- stop" % u)
        ex = ent.setdefault("extra", [])
        if TILE in ex:
            sys.exit("already granted to %s -- stop" % u)
        ex.insert(ex.index("Call Tracker") + 1 if "Call Tracker" in ex else 0, TILE)
        if isinstance(ent.get("only"), list):
            sys.exit("%s has an 'only' list -- decide by hand" % u)
    tg["version"] = 48
    tg["_note"] = tg.get("_note", "") + ("  S948 v48 (S515, 24-Nov-2026, D1060): the NEW tile 'My Call Console' (the staff's own "
                                          "Call Console, /portal/console/staff) is granted by name to shivani, alisha and shavez, "
                                          "beside 'Call Tracker', and to manoj (his picker and ?as= view). Its tile carries no role, so a lost grants file shows it to nobody; "
                                          "the page's own gate is the phone-staff list plus PORTAL_STAFF_CONSOLE_EXTRA.")
    os.makedirs(out, exist_ok=True)
    b = txt.encode("utf-8")
    open(os.path.join(out, "calls_console.py"), "wb").write(b)
    tb = (json.dumps(tg, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    open(os.path.join(out, "tile_grants.json"), "wb").write(tb)
    print("calls_console.py %s -> %s  (%d -> %d bytes)" % (FROM_CC[:8], md5(b)[:8], len(raw), len(b)))
    print("tile_grants.json v47 -> v48 %s" % md5(tb)[:8])


if __name__ == "__main__":
    main(sys.argv)
