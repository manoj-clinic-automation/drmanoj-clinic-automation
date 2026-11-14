#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s825.py -- S825_ARRIVALS_BY_THE_BILL (F-1220, D883; rebuilt at session 457 after the S455 review): makes three /root/finance files
from their LIVE bytes by exact, counted replacements; refuses any other starting file.
    python3 -B make_s825.py <live finance dir> <out dir>
THE CHANGE, one rule in three places:
  order_track.py -- size_of(): the size words a name prints; name_score() gives 0 when both names print a size and the sizes differ (a sibling
                    size is never the same item); match_lines(): for an Orthotics item a size on one side only is no match either.
  stock_figure.py -- s825_bill_judged(): for each scan-tied open order line, whether the bill tied to its order carries it, matched by THE
                    TRACKER'S OWN MATCHER (order_track.match_lines), judged only where a tied scan is usable and read; scan_lines() leaves
                    out a line judged NOT carried (it has not arrived).
  order_rules.py -- on the count basis a line judged NOT carried stays ON ORDER (on the way), so the engine does not propose it again.
Unread scans, an unreachable scan store, any failure: the old reading. Nothing written anywhere; no screen's layout changes."""
import hashlib
import os
import sys

FROM = {"order_track.py": "3f20faca36a159bc23dd45fc4bfce332", "stock_figure.py": "a0008c14353d5a7bda260854ff73b0e2", "order_rules.py": "bdefd058490dedb8b301a9f81ef3c5e1"}

R = {
"order_track.py": [
('''def name_score(form, read):
    """1.0 an exact name''',
 '''_S825_SIZE = {"XXS": "XXS", "XS": "XS", "S": "S", "M": "M", "L": "L", "XL": "XL", "XXL": "XXL", "XXXL": "XXXL", "XXXXL": "XXXXL",
              "SMALL": "S", "MEDIUM": "M", "LARGE": "L", "XXX": "XXXL", "2XL": "XXL", "3XL": "XXXL", "4XL": "XXXXL"}


def size_of(name):
    """S825 (F-1220, D883): the size words a name prints, as a frozenset -- SMALL / MEDIUM / LARGE are S / M / L, EXTRA LARGE is XL, XXX is
    XXXL, 2XL is XXL. A letter after a number (10'S) is a count, never a size; a lone letter before the name's first word of three letters or
    more (L.S. BELT) is an initial, never a size; UNIVERSAL names no size. Empty when the name prints none."""
    w = re.sub(r"[^A-Z0-9]+", " ", str(name or "").upper()).split()
    out, word_seen = set(), False
    for i, t in enumerate(w):
        if t == "LARGE" and i > 0 and w[i - 1] == "EXTRA":
            out.add("XL")
        elif t in _S825_SIZE and not (t == "LARGE" and i + 1 < len(w) and w[i + 1] == "EXTRA"):
            if len(t) == 1 and (not word_seen or (i > 0 and w[i - 1].isdigit())):
                pass
            else:
                out.add(_S825_SIZE[t])
        if len(t) >= 3 and t.isalpha():
            word_seen = True
    return frozenset(out)


def size_clash(form, read, one_sided=False):
    """S825: True when the two names print different sizes -- or, with one_sided (an Orthotics item), when only one of them prints a size."""
    a, b = size_of(form), size_of(read)
    if a and b:
        return a != b
    return bool(one_sided and (a or b))


def name_score(form, read):
    """1.0 an exact name'''),
('''    a, b = _nm(form), _nm(read)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    try:
        import med_names                                      # noqa: PLC0415
        lo = med_names.loose(read, form)''',
 '''    a, b = _nm(form), _nm(read)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    if size_clash(form, read):                                # S825 (F-1220): a sibling size is never the same item
        return 0.0
    try:
        import med_names                                      # noqa: PLC0415
        lo = med_names.loose(read, form)'''),
('''    """One-to-one: {item: (read name, stamp)} for the order items found among the scans' read names [(name, stamp)]."""
    pairs = []
    for it in items:
        fs = forms_of(con, sn, it, ctx)
        for j, (rn, st) in enumerate(reads):
            sc = max(name_score(f, rn) for f in fs)''',
 '''    """One-to-one: {item: (read name, stamp)} for the order items found among the scans' read names [(name, stamp)].
    S825 (F-1220, D883): for an Orthotics item (stock_item_section) a size printed on one side only is no match either."""
    pairs = []
    ortho = _s825_ortho(con)
    for it in items:
        fs = forms_of(con, sn, it, ctx)
        one = _pa().norm(it) in ortho
        for j, (rn, st) in enumerate(reads):
            sc = max((0.0 if (one and size_clash(f, rn, True)) else name_score(f, rn)) for f in fs)'''),
('''class Ctx(object):
    """What the scan half reads once per page''',
 '''def _s825_ortho(con):
    """S825: the Orthotics items (stock_item_section), by purchase_app.norm; empty when the table is absent."""
    try:
        return {_pa().norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")}
    except Exception:                                         # noqa: BLE001
        return set()


class Ctx(object):
    """What the scan half reads once per page'''),
],
"stock_figure.py": [
('''def scan_lines(con, sp, item=None, since_iso="", ctx=None):''',
 '''def s825_bill_judged(con, ctx=None):
    """S825 (F-1220, D883): {order line id: True | False} -- for each scan-tied open order line, whether the bill TIED to its order carries
    it: the tied scan's clearer copy (order_track.Ctx.head), usable as the tracker counts usable (not set aside, no rescan asked), as Claude
    read it, matched by THE TRACKER'S OWN MATCHER (order_track.match_lines: the item's printed forms and its learnt scan spellings, numbers
    and sizes agreeing). A line is judged only when one of its order's tied scans is usable and has its items read; otherwise -- a scan not
    read yet, a scan to redo, a scan before order.track_since, the scan store unreachable -- it is not judged and the old reading stands for
    it. {} when none is judged; None on any failure. READ ONLY (it calls nothing that writes; the connection's row factory is put back as it
    was). Once per Ctx."""
    ctx = _ctx(con, None, ctx)
    key = ("s825_judged",)
    if key in ctx.c:
        return ctx.c[key]
    con = ctx.con
    out = None
    rf = con.row_factory if con is not None else None
    try:
        con.row_factory = sqlite3.Row                         # as the tracker's own readers expect (its rescan list)
        rows = con.execute("SELECT l.id, l.item, l.order_id, o.vendor, o.supplier_norm, t.asset_bill_id FROM purchase_order_line l "
                           "JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id WHERE t.arrived=1 "
                           "AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 AND t.asset_bill_id IS NOT NULL").fetchall()
        out = {}
        if rows:
            import order_track as OT                          # noqa: PLC0415 -- beside this file
            octx = OT.Ctx(con)
            if not octx.ok:
                out = None
            else:
                pa = OT._pa()
                by = {}
                for r in rows:
                    e = by.setdefault(int(r["order_id"]), dict(sn=r["supplier_norm"] or pa.supplier_key(r["vendor"] or ""), items={}, sids=set()))
                    e["items"][int(r["id"])] = r["item"]
                    e["sids"].add(int(r["asset_bill_id"]))
                for e in by.values():
                    heads = []
                    for sid in sorted(e["sids"]):
                        h = octx.head(sid)
                        if h in octx.scans and h not in heads and octx.usable(h) and octx.names(h):
                            heads.append(h)
                    if not heads:
                        continue                              # no tied scan usable and read: not judged
                    reads = [(n, octx.scans[h].get("stamp_no") or "#%d" % h) for h in heads for n in octx.names(h)]
                    hit = OT.match_lines(con, e["sn"], list(dict.fromkeys(e["items"].values())), reads, octx.sf)
                    for lid, it in e["items"].items():
                        out[lid] = it in hit
    except Exception:                                         # noqa: BLE001 -- fail-soft: the old reading
        out = None
    finally:
        if con is not None:
            con.row_factory = rf
    ctx.c[key] = out
    return out


def scan_lines(con, sp, item=None, since_iso="", ctx=None):'''),
('''    12) or of every item (None). In _arrivals' shape: arrived_at = scan_at, arrived_by 'scan', units = packs x pack_size, kind 'scan'."""
    ctx = _ctx(con, sp, ctx)''',
 '''    12) or of every item (None). In _arrivals' shape: arrived_at = scan_at, arrived_by 'scan', units = packs x pack_size, kind 'scan'.
    S825 (F-1220, D883): a line the dealer's scanned bill does NOT carry (s825_bill_judged False) has not arrived and is left out -- it stays
    on order (order_rules); a line not judged keeps the old reading."""
    ctx = _ctx(con, sp, ctx)'''),
('''    for lid, nm, packs, size, vendor, created, oid, scan_at in rows:
        if keys is not None and sw.pad_norm(str(nm)[:27]) not in keys and sw.pad_norm(str(nm)) not in keys:
            continue
        out.append(dict(line_id=lid''',
 '''    judged = s825_bill_judged(con, ctx) if rows else None
    for lid, nm, packs, size, vendor, created, oid, scan_at in rows:
        if keys is not None and sw.pad_norm(str(nm)[:27]) not in keys and sw.pad_norm(str(nm)) not in keys:
            continue
        if judged and judged.get(int(lid)) is False:          # S825: not on the bill -- not arrived (on the way, order_rules)
            continue
        out.append(dict(line_id=lid'''),
],
"order_rules.py": [
('''def _s454_not_tied(con):
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " AND o.id NOT IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""''',
 '''def _s454_not_tied(con):
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " AND o.id NOT IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)" + _s825_not_carried(con)
    except sqlite3.Error:
        return ""


def _s825_not_carried(con):
    """S825 (F-1220, D883): ' OR l.id IN (...)' -- the scan-tied open lines the dealer's scanned bill does NOT carry
    (stock_figure.s825_bill_judged False) stay ON ORDER on the count basis: they have not arrived, so they are on the way and the engine does
    not propose them again. Inside the caller's bracket: (o.status='sent' AND o.id NOT IN tied OR l.id IN (...)). '' when none or unreadable."""
    try:
        import stock_figure as SF                             # noqa: PLC0415
        j = SF.s825_bill_judged(con) or {}
        ids = sorted(int(k) for k, v in j.items() if v is False)
    except Exception:                                         # noqa: BLE001
        return ""
    return (" OR l.id IN (%s)" % ",".join(str(i) for i in ids)) if ids else ""'''),
],
}


def main():
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    for fn in ("order_track.py", "stock_figure.py", "order_rules.py"):
        b = open(os.path.join(src, fn), "rb").read()
        h = hashlib.md5(b).hexdigest()
        if h != FROM[fn]:
            print("make_s825: %s is %s, not %s -- STOP" % (fn, h[:8], FROM[fn][:8]))
            return 2
        t = b.decode("utf-8")
        for i, (old, new) in enumerate(R[fn], 1):
            n = t.count(old)
            if n != 1:
                print("make_s825: %s replacement %d found %d times -- STOP" % (fn, i, n))
                return 2
            t = t.replace(old, new, 1)
        nb = t.encode("utf-8")
        open(os.path.join(dst, fn), "wb").write(nb)
        print("make_s825: %s %s -> %s" % (fn, FROM[fn][:8], hashlib.md5(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
