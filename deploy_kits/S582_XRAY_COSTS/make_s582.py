#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s582.py -- S582_XRAY_COSTS: batteries.py rebuilt from the pinned live bytes (S575's TO, 40eb8a91) with exactly TWO counted
edits, and the new file xray_costs.py put beside it (copied byte for byte from this kit). asset_register.py, sorting_desk.py,
clinic_papers.py, asset_machine.py, stationery.py, scanner_widget.js, packs.py and every finance / Sanjeevni file are never touched
(asset_register.py and sorting_desk.py stand at drift 8 -- F-836 -- so the mount and the menu go through batteries.py).

    python3 make_s582.py <dir with the live batteries.py> <out dir>

Refuses when the input is not at its FROM pin, when xray_costs.py is not at its pin, or when an anchor is not found exactly once.
Every byte of the built batteries.py comes from the live file plus these two edits (BUILD_NORM_v1). The brief:
claude_code_briefs/S582_XRAY_COSTS.md (v2) with its review S582_BRIEF_R1.md (md5 d3e0fa69...)."""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"batteries.py": "40eb8a916aee48ef5a49337d3c4cc81d"}
NEW = "xray_costs.py"

BT_EDITS = [
    # E1 -- batteries.menu_items: "X-ray costs" appended right after Batteries (the owner only -- xray_costs.menu_items decides);
    #       guarded, so a failure there leaves the Batteries item exactly as before
    ('''        if role == "owner" or (role == "manager" and switch_on(AR.get_db())):
            return [("s571_page", "Batteries", url_for("s571_page"))]
''',
     '''        if role == "owner" or (role == "manager" and switch_on(AR.get_db())):
            out = [("s571_page", "Batteries", url_for("s571_page"))]
            try:                                                      # S582_XRAY_COSTS: "X-ray costs" right after Batteries -- the owner only
                xc = sys.modules.get("xray_costs")
                if xc is not None and getattr(xc, "MOUNTED", False):
                    out += list(xc.menu_items(role))
            except Exception as ex:                                   # noqa: BLE001
                print("S582 menu: %s" % ex, file=sys.stderr)
            return out
''', 1),
    # E2 -- the end of batteries.init: the guarded mount of xray_costs (a failure prints to stderr; the Batteries pages run as before)
    ('''    app.jinja_env.globals.update(s571_battery_card=renewals_card)
    MOUNTED = True
    return VERSION
''',
     '''    app.jinja_env.globals.update(s571_battery_card=renewals_card)
    MOUNTED = True
    try:                                                              # S582_XRAY_COSTS (D736): the owner's X-ray expenses page, guarded
        import xray_costs as _xray_costs
        _xray_costs.init(ar)
    except Exception as _ex_s582:                                     # noqa: BLE001
        print("xray_costs NOT mounted: %s" % _ex_s582, file=sys.stderr)
    return VERSION
''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def pin(name):
    with open(os.path.join(HERE, name), encoding="ascii") as fh:
        return fh.read().strip()


def apply(name, text, edits):
    n = 0
    for old, new, cnt in edits:
        k = text.count(old)
        if k != cnt:
            raise SystemExit("REFUSED: an anchor in %s was found %d times, not %d: %r" % (name, k, cnt, old[:70]))
        text = text.replace(old, new)
        n += 1
    return text, n


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    f = "batteries.py"
    with open(os.path.join(src, f), "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[f]:
        raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
    text, n = apply(f, raw.decode("utf-8"), BT_EDITS)
    b = text.encode("utf-8")
    with open(os.path.join(out, f), "wb") as fh:
        fh.write(b)
    print("%-18s %s -> %s  (%d counted edits, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n))
    with open(os.path.join(HERE, NEW), "rb") as fh:
        x = fh.read()
    want = pin("PIN_TO_xray_costs.txt")
    if md5(x) != want:
        raise SystemExit("REFUSED: the kit's %s is %s, not its pin %s" % (NEW, md5(x)[:8], want[:8]))
    with open(os.path.join(out, NEW), "wb") as fh:
        fh.write(x)
    print("%-18s new      -> %s  (the kit's file, byte for byte)" % (NEW, md5(x)[:8]))


if __name__ == "__main__":
    main()
