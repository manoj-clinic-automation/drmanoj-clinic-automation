#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s932.py -- kit S932_ORTHO_ORDER_NAMES (22-Nov-2026, Sanjeevni session 503; F-1579). The TO files by EXACT anchors (each once):
   order_sheet.py 85ce2148 (the 22-Nov bundle) · porders.py ea014fbd (S925's TO).
    python3 -B make_s932.py <live_dir> <out_dir>"""
import hashlib
import io
import os
import sys

FROM = {"order_sheet.py": "85ce2148", "porders.py": "ea014fbd"}
BLOCK = '''
# ---- S932 (F-1579, 22-Nov-2026): an orthotic ORDER LINE carries Marg's CURRENT name -------------------------------------------------
#  The orthotic lane keys its rows by the count's names (the 06-Sep spellings): for the 22 renamed sizes Amir ticked (item_alias), that is
#  a name Marg no longer prints -- ANKLE BINDER BAMBOO M was ordered under it thrice. The lane's own keys stay as they are (porder_keep, the
#  section map, Darpan's yes rows); only what LEAVES the lane -- the order line reception sends, the dealer's sheet, Darpan's and his
#  flow rows -- carries the ticked NEW name, and the lane's lookups read both names (_s932_forms; porders._on_order folds a new name back).
def _s932_map(con):
    """{OLD name: NEW name} of the ticked renames, EXACT names only (never a clip: orthotic sizes differ only at the tail, so a 20-letter clip
    is shared by siblings). A chain (X->Y ticked and Y->Z ticked) folds nothing on Y: Y is also a lane key of its own. Fail-soft: {}."""
    try:
        rows = [r for r in _ia().done_rows(con) if r.get("old_name") and r.get("new_name")]
        olds = {str(r["old_name"]) for r in rows}
        return {str(r["old_name"]): str(r["new_name"]) for r in rows if str(r["new_name"]) not in olds}
    except Exception:                                         # noqa: BLE001
        return {}


def _s932_marg_name(con, name, m=None):
    """The ticked rename's NEW name for a count name (exact; a spacing/case difference is matched by item_alias.pad_norm); the name itself
    when no rename is ticked. Fail-soft."""
    m = _s932_map(con) if m is None else m
    if name in m:
        return m[name]
    try:
        pn = _ia().pad_norm(name)
        for o, n in m.items():
            if _ia().pad_norm(o) == pn:
                return n
    except Exception:                                         # noqa: BLE001
        pass
    return name


def _s932_forms(con, name, m=None):
    """[name, its ticked NEW name] -- the exact spellings an order line of this item may carry (never a clip: see _s932_map)."""
    mn = _s932_marg_name(con, name, m)
    return [name] if mn == name else [name, mn]


'''


def rd(p):
    with io.open(p, "r", encoding="utf-8", newline="") as fh:
        return fh.read()


def wr(p, t):
    with io.open(p, "w", encoding="utf-8", newline="") as fh:
        fh.write(t)


def sub(t, a, b, what):
    n = t.count(a)
    if n != 1:
        raise SystemExit("anchor %s occurs %d times, not once" % (what, n))
    return t.replace(a, b)


def main():
    live, out = sys.argv[1], sys.argv[2]
    for f, h in FROM.items():
        got = hashlib.md5(open(os.path.join(live, f), "rb").read()).hexdigest()[:8]
        if got != h:
            raise SystemExit("%s is %s, the kit was written on %s" % (f, got, h))
    t = rd(os.path.join(live, "order_sheet.py"))
    t = sub(t, '''def _s605_ordered_since(con, sn, item, at):
    """An order of the new flow to the orthotic vendor (draft, sent or received), made at or after `at`, carries the item."""
    return con.execute("SELECT 1 FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE o.order_src='s454' AND o.supplier_norm=? "
                       "AND o.status IN ('draft','sent','received') AND o.created_at>=? AND l.item=? LIMIT 1", (sn, at, item)).fetchone() is not None
''', BLOCK + '''def _s605_ordered_since(con, sn, item, at, m=None):
    """An order of the new flow to the orthotic vendor (draft, sent or received), made at or after `at`, carries the item -- under the count's
    name or Marg's current name (S932; m = _s932_map(con) built once by the caller)."""
    forms = _s932_forms(con, item, m)
    return con.execute("SELECT 1 FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE o.order_src='s454' AND o.supplier_norm=? "
                       "AND o.status IN ('draft','sent','received') AND o.created_at>=? AND l.item IN (%s) LIMIT 1" % ",".join("?" * len(forms)),
                       tuple([sn, at] + forms)).fetchone() is not None
''', "A1 ordered_since + block")
    t = sub(t, '''                    if pa.norm(a["item"]) in have:
                        continue                              # an item on both is shown once, with the sheet's quantity
                    ref = "ortho:%d" % a["id"]                # his yes row: reception's quantity edit keeps to the line
                    e = _edits(con, "ortho", ref).get(a["item"]) or {}
                    if e.get("removed"):
                        continue
                    c["lines"].append(dict(src="ortho", ref=ref, item=a["item"], qty=int(e["qty"]) if e.get("qty") is not None else int(a["qty"] or 0),''',
            '''                    mn = _s932_marg_name(con, a["item"])         # S932 (F-1579): the order line carries Marg's CURRENT name
                    if pa.norm(a["item"]) in have or pa.norm(mn) in have:
                        continue                              # an item on both is shown once, with the sheet's quantity
                    ref = "ortho:%d" % a["id"]                # his yes row: reception's quantity edit keeps to the line
                    ed = _edits(con, "ortho", ref)
                    e = ed.get(mn) or ed.get(a["item"]) or {}
                    if e.get("removed"):
                        continue
                    c["lines"].append(dict(src="ortho", ref=ref, item=mn, qty=int(e["qty"]) if e.get("qty") is not None else int(a["qty"] or 0),''', "A2 the card line")
    t = sub(t, '''    out = [a for a in _s605_answers(con).values() if a["answer"] == "yes" and not _s605_ordered_since(con, sn, a["item"], a["at"])]
''', '''    m = _s932_map(con)                                        # S932: the ticked renames read once for the whole list
    out = [a for a in _s605_answers(con).values() if a["answer"] == "yes" and not _s605_ordered_since(con, sn, a["item"], a["at"], m)]
''', "A3 ortho_kept the map once")
    t = sub(t, '''            sn = pa.supplier_key(vendor)
            if sn not in drafts:
                c = card(sn, vendor)
                have = {pa.norm(x["item"]) for x in c["lines"]}
                for a in kept:
''', '''            sn = pa.supplier_key(vendor)
            if sn not in drafts:
                c = card(sn, vendor)
                have = {pa.norm(x["item"]) for x in c["lines"]}
                m932 = _s932_map(con)                         # S932: once for the card
                for a in kept:
''', "A4 entries the map once")
    t = t.replace('mn = _s932_marg_name(con, a["item"])         # S932', 'mn = _s932_marg_name(con, a["item"], m932)   # S932')
    wr(os.path.join(out, "order_sheet.py"), t)
    p = rd(os.path.join(live, "porders.py"))
    p = sub(p, '''    out = {}
    try:
        for r in con.execute("SELECT l.item, l.packs FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.vendor=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",
                             (vendor,)):                   # S454 (4.4): arrived by its bill's scan = counted until Marg answers
            out[r[0]] = out.get(r[0], 0) + int(r[1] or 0)
''', '''    out = {}
    ren = {}                                                  # S932 (F-1579): {ticked NEW name: OLD name}, EXACT names only -- a line ordered under
    try:                                                      # Marg's current name counts for the lane's own (old) key; a clip never folds (siblings
        olds = set()                                          # share it); a chain's middle name (X->Y and Y->Z) folds nothing
        rows = [x for x in _ia().done_rows(con) if x.get("old_name") and x.get("new_name")]
        olds = {str(x["old_name"]) for x in rows}
        ren = {str(x["new_name"]): str(x["old_name"]) for x in rows if str(x["new_name"]) not in olds}
    except Exception:                                         # noqa: BLE001
        ren = {}
    try:
        for r in con.execute("SELECT l.item, l.packs FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                             "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.vendor=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",
                             (vendor,)):                   # S454 (4.4): arrived by its bill's scan = counted until Marg answers
            k = ren.get(r[0], r[0])
            out[k] = out.get(k, 0) + int(r[1] or 0)
''', "B1 _on_order fold")
    wr(os.path.join(out, "porders.py"), p)
    for f in ("order_sheet.py", "porders.py"):
        print("%s -> %s" % (f, hashlib.md5(open(os.path.join(out, f), "rb").read()).hexdigest()[:8]))


if __name__ == "__main__":
    main()
