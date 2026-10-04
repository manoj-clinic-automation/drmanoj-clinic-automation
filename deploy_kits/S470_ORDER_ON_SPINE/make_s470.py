#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""make_s470.py -- kit S470_ORDER_ON_SPINE (D672, D673; F-718, F-719): the anchored patcher. CLAUDE.md rule 2: every file is built from the
LIVE bytes (FROM pinned), every anchor exactly once, else STOP and nothing is written.

  order_rules.py            the S470 block above the __main__ guard (the spine source, the arrivals rule, the six settings) + five edits
                            inside plan() / _on_order_units (dead_after passed to plan_line; no_supplier; engine; order.on_order_days)
  purchase_app.py           ONE edit: plan_line(it, cad_days, dead_after=None) reads `dead_after or DEAD_AFTER_DAYS`
  porders_s454.py           the owner's card (the weekly line, no-supplier, a family said as such) and the six settings on the settings card
  spine/spine_read.py       the read door's methods for the engine (sales_daily, stock_series, purchase_lines, family, last_sale, closing)
  spine/selftest_spine.py   one check per new method
  spine/order_rehearsal.py  REPLACED WHOLE by the kit's file (pinned FROM the live S341 file): it keeps and scores order_proposal

    make_s470.py --finance /root/finance --out DIR        (writes DIR/<file> and DIR/spine/<file>; prints FROM -> TO)
"""
import argparse
import hashlib
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {
    "order_rules.py": "734fc6bcd67bb23da1bea2a6e927fcad",
    "purchase_app.py": "979391b6e191e0d2468f3db6fc57366e",
    "porders_s454.py": "c3562c5bc5602ecdb32e416a231ba30c",
    "spine/spine_read.py": "ab55344ee280b0b4847a45cebe6d3843",
    "spine/selftest_spine.py": "bfa607b980e4e838dfc7198f0bc7c9c9",
    "spine/order_rehearsal.py": "02582fbea29f51606a6ba8bb8694d3fc",
}


def kit(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return fh.read()


def between(text, a, b):
    """The lines of a kit block file between its two marker lines (each marker exactly once)."""
    assert text.count(a) == 1 and text.count(b) == 1, "a block marker is not there exactly once: %s" % a
    i = text.index(a) + len(a)
    return text[i:text.index(b)].lstrip("\n").rstrip(" ")


def edits():
    spine_methods = between(kit("spine_read_block_s470.py"), "    # >>> S470 methods\n", "    # <<< S470 methods")
    selftest = between(kit("selftest_block_s470.py"), "# >>> S470 selftest\n", "# <<< S470 selftest")
    return {
        "order_rules.py": [
            # B.8: the dead-after days are a setting, read once per plan and handed to plan_line (purchase_app's one edit)
            ('''    min_line = _int_setting(con, "order.min_line_p")
''',
             '''    min_line = _int_setting(con, "order.min_line_p")
    dead_after = _s470_days(con, "order.dead_after_days")       # S470 (B.8): a setting, at its present value
    no_supplier = []                                            # S470 (B.7): sold, never bought -- named, not dropped silently
'''),
            # B.7: a sold item with no supplier on record is skipped as before, and named
            ('''        if not vn or vn == ortho_v:
            continue
        if suppliers is not None and vn not in suppliers:
''',
             '''        if not vn:                                             # S470 (B.7)
            no_supplier.append(dict(item=s["item"], on_hand=s["qty"], rate_per_day=round(p["rate_per_day"], 2)))
            continue
        if vn == ortho_v:
            continue
        if suppliers is not None and vn not in suppliers:
'''),
            ('''        line = pa.plan_line(it, cad)
''',
             '''        line = pa.plan_line(it, cad, dead_after)               # S470 (B.8)
'''),
            ('''    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items)
''',
             '''    no_supplier.sort(key=lambda x: x["item"])
    return dict(as_on=as_on, today=today.isoformat(), vendors=vendors, held_items=held_items, no_supplier=no_supplier, engine=_s470_engine(),   # S470
                no_closing=_s470_missing())
'''),
            # B.8: order.on_order_days replaces the constant (kept above for whoever reads it; nothing does)
            ('''    since = (today - dt.timedelta(days=ON_ORDER_DAYS)).isoformat()
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
''',
             '''    since = (today - dt.timedelta(days=_s470_days(con, "order.on_order_days"))).isoformat()   # S470 (B.8): the setting, 4 as before
    out = {}
    try:
        rows = con.execute("SELECT l.item, l.packs, l.pack_size, o.id, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
'''),
            # the block: above the __main__ guard, so the cron's script run has it (S454 P1D's lesson, F-711)
            ('''if __name__ == "__main__":                                   # S454 P1D: last in the file, so every definition above it exists when the
''',
             kit("order_rules_block_s470.py").lstrip("\n")
             + '''if __name__ == "__main__":                                   # S454 P1D: last in the file, so every definition above it exists when the
'''),
        ],
        "purchase_app.py": [
            ('''def plan_line(it, cad_days):
''',
             '''def plan_line(it, cad_days, dead_after=None):               # S470 (B.8): order.dead_after_days, handed in by order_rules.plan
'''),
            ('''    if strips and it["days_since_sale"] > DEAD_AFTER_DAYS:
''',
             '''    if strips and it["days_since_sale"] > (dead_after or DEAD_AFTER_DAYS):
'''),
        ],
        "porders_s454.py": [
            # the six settings: the same route, the same card
            ('''    key = str(b.get("key") or "")
    if key not in OS.SETTINGS:
''',
             '''    key = str(b.get("key") or "")
    if key in _s470_keys():                                   # S470 (B.8): the engine's six settings
        return _s470_set(con, u, key, b.get("value"))
    if key not in OS.SETTINGS:
'''),
            ('''    h.append(_s454_gap_card(con, st))                          # S454 P3 (7.5): Marg and the shelf figure
''',
             '''    rows.extend(_s470_setting_rows(con))                       # S470 (B.8): the engine's six settings on the same card
    h.append(_s454_gap_card(con, st))                          # S454 P3 (7.5): Marg and the shelf figure
'''),
            # the owner's card: after "Who decides the order", outside the sheet's condition -- it shows always
            ('''    ns = OS.newest_sheet(con)
    if ns and ns.get("cmp"):
''',
             '''    h.append(_s470_card(con, st))                              # S470 (D): the weekly line; no-supplier; a family; the source
    ns = OS.newest_sheet(con)
    if ns and ns.get("cmp"):
'''),
            ("__APPEND__", kit("porders_block_s470.py")),
        ],
        "spine/spine_read.py": [
            ('''    sp.gate()                             # the last build's gate rows
''',
             '''    sp.gate()                             # the last build's gate rows
    sp.sales_daily(n, d1, d2) · sp.stock_series(n, d1, d2) · sp.purchase_lines(n) · sp.family(n) · sp.last_sale(n) · sp.closing(n)
                                          # S470: what the order engine reads (returns deducted; day-end stock; Marg's own closing figure)
'''),
            ('''No screen reads the spine yet (rung 3 of S272_SPINE_ARCHITECTURE). This module is what rung 4 will import.
''',
             '''Rung 4a of S272_SPINE_ARCHITECTURE (kit S470): the order engine (order_rules.py) reads its sale rate, stock and supplier through this
door, and the nightly trial (order_rehearsal.py) scores against it.
'''),
            ('''    # ---------------------------------------------------------------- health
''',
             spine_methods + '''
    # ---------------------------------------------------------------- health
'''),
        ],
        "spine/selftest_spine.py": [
            ('''if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
''',
             selftest + '''

if __name__ == "__main__":
    test_readers()
    test_evidence()
    test_builder()
    test_s470()
'''),
        ],
    }


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    E = edits()
    for name, frm in FROM.items():
        raw = open(os.path.join(a.finance, name), "rb").read()
        if md5b(raw) != frm:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (name, md5b(raw), frm))
        if name == "spine/order_rehearsal.py":                 # replaced whole by the kit's file
            built[name] = open(os.path.join(HERE, "order_rehearsal.py"), "rb").read()
            continue
        txt = raw.decode("utf-8")
        for old, new in E[name]:
            if old == "__APPEND__":
                txt = txt.rstrip("\n") + "\n" + new
                continue
            c = txt.count(old)
            if c != 1:
                raise SystemExit("STOP: %s -- an anchor occurs %d times; nothing built: %r" % (name, c, old[:90]))
            txt = txt.replace(old, new, 1)
        built[name] = txt.encode("utf-8")
    os.makedirs(os.path.join(a.out, "spine"), exist_ok=True)
    for name, b in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(b)
        print("built %-26s %s -> %s  (%s)" % (name, FROM[name][:8], md5b(b), "replaced whole" if name.endswith("order_rehearsal.py") else "%d anchored edits" % len(E[name])))


if __name__ == "__main__":
    main()
