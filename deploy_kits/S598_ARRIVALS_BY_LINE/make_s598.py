#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s598.py -- kit S598_ARRIVALS_BY_LINE: the builder. Anchored edits on the LIVE bytes of three files; no new file placed, no new
setting, no new table.

    python3 -B make_s598.py --finance /root/finance --out DIR

Every file is pinned (FROM md5, the brief's section 1); every anchor must occur exactly once in the live text, else STOP (exit 2, nothing
written). Writes the three files into DIR and prints each md5 -- the installer compares them with PINS.sh.
The brief: claude_code_briefs/S598_ARRIVALS_BY_LINE.md (v2, 19-Oct-2026, Sanjeevni session 328). Closes F-942: the bill LINE is the unit of
the one arrivals rule -- a bill line answers only the size it names; one bill line is never credited to two order lines.
"""
import argparse
import hashlib
import os
import sys

FROM = {
    "stock_figure.py": "92367a196b360f0cded4cda6a5ded700",
    "stock_watch.py": "c5f3ce21a785c45df58f21932cf920e7",
    "porders.py": "78ea72be7d87a7c56c65de7d4c96a952",
}

# =============================================================================================================== stock_figure.py (3.1)
SF = []
SF.append(("F1 the kit line and the S598 head note", '''VERSION = "1.2"
KIT = "S587_MORNING_FLOW"                                      # v1.1 was S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
''', '''VERSION = "1.3"
KIT = "S598_ARRIVALS_BY_LINE"                                  # v1.2 was S587_MORNING_FLOW, v1.1 S583_ARRIVALS_ONE_RULE, v1.0 S577_STOCK_ON_SPINE
#  v1.3 (S598, 19-Oct-2026, F-942): THE BILL LINE IS THE UNIT OF THE ARRIVALS RULE. Sizes of one orthotic share a 20-letter spine key, so
#  the by-bill rule credited one size's order line with the whole family's bill (KNEE SUPPORT HINGED XL ordered 2, 'billed 6' by a bill that
#  carried M and L). Now an order line is matched to a bill LINE of its own printed name (_line_forms: every spelling Marg or the count has
#  printed for the item, clipped to 27 as Marg's bill clips; _matches), the key alone deciding only for an item with no sibling under its key
#  (_siblings). Rule (b) is per bill line, keyed on the match (_taken_lines): one bill line is never credited to two order lines of one item.
#  carried() returns the LINE's units / qty / free (two batches of one bill summed), its seq and printed name; when nothing matches, the family's bill
#  that carried OTHER sizes is kept for the owner's words (_family_bill -> arrivals_open()['family_bill']). _purchases_of and _taken_bills are
#  retired. Sizes that still agree in their first 27 letters stay one lump (Marg's report cannot tell them apart) -- named, not fixed.
'''))
SF.append(("F2 _taken_bills retired; _line_forms, _siblings, _matches, _taken_lines", '''def _taken_bills(sp, k20, line_id, ctx):
    """{(supplier key, bill)} -- the billed_bill_no of every OTHER order line of the key, with its order's vendor key (rule b): Marg's answer to
    another line never carries this one. Read once per key and Ctx."""
    ck = ("taken", k20)
    if ck not in ctx.c:
        out = {}
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    if key_of(sp, item, ctx) == k20:
                        out.setdefault((_sw().supkey(vendor), _bill(bno)), set()).add(int(lid))
        except sqlite3.Error:
            out = {}
        ctx.c[ck] = out
    me = {int(line_id)} if line_id is not None else set()
    return {k for k, ids in ctx.c[ck].items() if ids - me}
''', '''def _line_forms(ctx, name):
    """S598: the set of spellings a bill line of THIS item may print, as the estate clips them -- {pad_norm(f[:27]), pad_norm(f)} over
    printed_forms (the name, its ticked rename partner, the accepted seen_names). A CLIPPED order spelling (27 letters or more: Marg's
    order report clips too) also takes every rename group that holds a form starting with it, so the clip still reaches its partner
    (R1-C2). pad_norm is stock_watch's (the clip _arrivals / scan_lines match an order line by). Cached per name and Ctx."""
    sw = _sw()
    name = str(name or "")
    ck = ("forms", norm(name))
    if ck in ctx.c:
        return ctx.c[ck]
    fs = list(printed_forms(ctx.con, name, ctx))
    if len(name.strip()) >= 27:
        nn = norm(name)
        groups, _index = _rename_groups(ctx.con, ctx)
        for g in groups:
            if any(norm(f).startswith(nn) for f in g):
                fs.extend(g)
    out = set()
    for f in fs:
        out.add(sw.pad_norm(str(f)[:27]))
        out.add(sw.pad_norm(str(f)))
    out.discard("")
    ctx.c[ck] = out
    return out


def _siblings(sp, k20, ctx):
    """S598: True when more than one ITEM lives under the key -- sp_item's names under k20, two spellings of one renamed item folded into one
    member (the fold family() does). A key with one item is matched by the key alone, whatever Marg's clip printed. Cached per key and Ctx."""
    ck = ("sib", k20)
    if ck in ctx.c:
        return ctx.c[ck]
    names = []
    try:
        if sp is not None and getattr(sp, "ok", False):
            names = [str(r["name"] or "") for r in sp.q("SELECT DISTINCT name FROM sp_item WHERE k20=?", k20)]
    except Exception:                                         # noqa: BLE001
        names = []
    _groups, index = _rename_groups(ctx.con, ctx)
    tags = set()
    for n in names:
        if not n.strip():
            continue
        gi = index.get(norm(n))
        tags.add(("g", gi) if gi is not None else ("n", norm(n)))
    ctx.c[ck] = len(tags) > 1
    return ctx.c[ck]


def _matches(ctx, sp, k20, forms, sib, name27):
    """S598: THE one match of a bill line to an order line -- its printed name (name27, as Marg's BILL/ITEM WISE report clips it) in the
    line's forms; or the key alone when the key has no sibling (sib False). The only place a name27 is compared with forms."""
    sw = _sw()
    s = str(name27 or "")
    if sw.pad_norm(s) in forms or sw.pad_norm(s[:27]) in forms:
        return True
    return not sib


def _taken_lines(sp, k20, line_id, ctx):
    """S598 (rule b, per bill LINE; R1-B1): for every OTHER order line of the key that carries a billed_bill_no, one entry
    (its order's vendor key, _bill(its bill), ITS forms by _line_forms, sib of its key) -- a bill line is TAKEN when (supkey, bill) equals an
    entry's and _matches(entry.forms, entry.sib, its printed name) is True: the same match the other line itself used, so one bill line is never
    credited to two order lines of one item, whatever the two spellings. Read once per key and Ctx (a fresh Ctx per row keeps it honest)."""
    ck = ("taken", k20)
    if ck not in ctx.c:
        out = []
        try:
            if ctx.con is not None:
                for lid, item, bno, vendor in ctx.con.execute("SELECT l.id, l.item, l.billed_bill_no, o.vendor FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                                               "WHERE COALESCE(l.billed_bill_no,'')<>''"):
                    if key_of(sp, item, ctx) == k20:
                        out.append((int(lid), _sw().supkey(vendor), _bill(bno), _line_forms(ctx, item), _siblings(sp, k20, ctx)))
        except sqlite3.Error:
            out = []
        ctx.c[ck] = out
    me = int(line_id) if line_id is not None else None
    return [t for t in ctx.c[ck] if t[0] != me]
'''))
SF.append(("F3 _purchases_of retired; _purchase_lines_of (one row per bill LINE)", '''def _purchases_of(sp, k20, since_day, ctx):
    """The spine's PURCHASE bills of the key dated on or after since_day, oldest first: dict(supkey, bill, date, units, supplier) -- one row per
    bill (its lines of the key summed), the supplier's name from sp_purchase_bill when the spine has it."""
    ck = ("pur", k20, since_day)
    if ck not in ctx.c:
        try:
            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, SUM(l.units) AS units, MAX(b.supplier) AS supplier FROM sp_purchase_line l "
                        "LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                        "WHERE l.k20=? AND l.direction='PURCHASE' AND l.date>=? GROUP BY l.supkey, l.bill, l.date ORDER BY l.date, l.bill", k20, since_day)
        except sqlite3.Error:
            rows = sp.q("SELECT supkey, bill, date, SUM(units) AS units, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' AND date>=? "
                        "GROUP BY supkey, bill, date ORDER BY date, bill", k20, since_day)
        ctx.c[ck] = rows
    return ctx.c[ck]
''', '''def _purchase_lines_of(sp, k20, since_day, ctx):
    """S598: the spine's PURCHASE LINES of the key dated on or after since_day (since_day '' = every line of the key), oldest first, the
    lines of one bill together in Marg's order: dict(supkey, bill, date, seq, name27, qty, free, units, supplier) -- ONE ROW PER BILL LINE
    (never summed by bill), the supplier's name from sp_purchase_bill when the spine has it."""
    ck = ("plines", k20, since_day)
    if ck not in ctx.c:
        try:
            rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, l.seq AS seq, l.name27 AS name27, l.qty AS qty, l.free AS free, l.units AS units, "
                        "MAX(b.supplier) AS supplier FROM sp_purchase_line l LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                        "WHERE l.k20=? AND l.direction='PURCHASE' AND l.date>=? GROUP BY l.supkey, l.bill, l.date, l.seq ORDER BY l.date, l.bill, l.seq", k20, since_day)
        except sqlite3.Error:
            rows = sp.q("SELECT supkey, bill, date, seq, name27, qty, free, units, supkey AS supplier FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' "
                        "AND date>=? ORDER BY date, bill, seq", k20, since_day)
        ctx.c[ck] = rows
    return ctx.c[ck]
'''))
SF.append(("F4 carried(): the docstring names the line rule (F-942)", '''    """THE ONE RULE: the purchase of Marg's that carries an arrival line, or None. `line` is the dict stock_watch._arrivals yields (line_id, item,
    vendor, order_at, arrived_at, billed_bill_no; scan_at for a scan-tied line). Returns dict(supplier, supkey, bill, date, units, how) -- `how`
    the rule's letter. None while sp.ok is False (the spine unread: nothing is dropped). In order:
      (a) the line's own billed_bill_no (Marg's answer, S537) -> carried, whatever the spine shows;
      (b) a purchase whose bill is the billed_bill_no of ANOTHER order line of the same key never carries this line;
      (c) a purchase dated BEFORE the order day carries only from the order's own vendor key, dated within arrival.back_days before the order day;
      (d) a purchase from the order's own vendor key dated on or after the order day carries (the rule before S583);
      (e) a purchase from another supplier carries only when dated on or after the order day.
    The first eligible purchase, oldest date first, wins. A carrying bill dated on or before the item's count day still drops the arrival: the goods
    are inside the count (the brief's named edge)."""
''', '''    """THE ONE RULE: the purchase LINE of Marg's that carries an arrival line, or None. `line` is the dict stock_watch._arrivals yields (line_id,
    item, vendor, order_at, arrived_at, billed_bill_no; scan_at for a scan-tied line). Returns dict(supplier, supkey, bill, date, units, qty,
    free, seq, the bill line's printed name, how) -- `how` the rule's letter; units / qty / free are THE MATCHED BILL LINE's (two batches of
    one item on one bill summed), never the family's. None while sp.ok is False (the spine unread: nothing is dropped). In order:
      (a) the line's own billed_bill_no (Marg's answer, S537) -> carried, whatever the spine shows (units None when no line of that bill
          matches: the figure unknown, the answer trusted);
      (b) a bill LINE that answered ANOTHER order line of the same item (by the same match) never carries this line -- S598, per line;
      (c) a purchase dated BEFORE the order day carries only from the order's own vendor key, dated within arrival.back_days before the order day;
      (d) a purchase from the order's own vendor key dated on or after the order day carries (the rule before S583);
      (e) a purchase from another supplier carries only when dated on or after the order day.
    S598 (F-942): a bill line is eligible only when it MATCHES the order line -- its printed name among the item's spellings (_line_forms /
    _matches), the key alone only for an item with no sibling under its key (_siblings): a sibling size never takes it. The first eligible
    matching line, oldest date first, wins. No matching line -> None, and the family's bill that carried OTHER sizes is kept for the owner's
    words (ctx ('fam_bill', line_id) -> arrivals_open). A carrying bill dated on or before the item's count day still drops the arrival: the
    goods are inside the count (the brief's named edge)."""
'''))
SF.append(("F5 _carried on bill LINES; _family_bill", '''def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a)
        hit = [p for p in sp.q("SELECT supkey, bill, date, SUM(units) AS units FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' GROUP BY supkey, bill, date ORDER BY date DESC", k)
               if _bill(p["bill"]) == bno]
        p = hit[0] if hit else {}
        return dict(supplier=str(line.get("vendor") or ""), supkey=str(p.get("supkey") or own), bill=str(line.get("billed_bill_no") or ""),
                    date=str(p.get("date") or line.get("billed_date") or "")[:10], units=(float(p["units"] or 0) if p else None), how="a")
    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    taken = _taken_bills(sp, k, line.get("line_id"), ctx)
    for p in _purchases_of(sp, k, lo, ctx):
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if (sk, _bill(p["bill"])) in taken:                   # (b)
            continue
        if d < od:
            how = "c" if (own and sk == own) else None        # (c)
        else:
            how = "d" if (own and sk == own) else "e"         # (d) / (e)
        if how:
            return dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0), how=how)
    return None
''', '''def _carried(ctx, sp, line):
    sw = _sw()
    k = key_of(sp, line.get("item"), ctx)
    own = sw.supkey(line.get("vendor"))
    forms = _line_forms(ctx, line.get("item"))
    sib = _siblings(sp, k, ctx)
    bno = _bill(line.get("billed_bill_no"))
    if bno:                                                   # (a): the lines of that bill that MATCH, summed; the newest bill of the number
        hit = [p for p in _purchase_lines_of(sp, k, "", ctx) if _bill(p["bill"]) == bno and _matches(ctx, sp, k, forms, sib, p["name27"])]
        if hit:
            top = max((str(p["date"] or "")[:10], str(p["supkey"] or "")) for p in hit)
            hit = [p for p in hit if (str(p["date"] or "")[:10], str(p["supkey"] or "")) == top]
        p = hit[0] if hit else {}
        return dict(supplier=str(line.get("vendor") or ""), supkey=str(p.get("supkey") or own), bill=str(line.get("billed_bill_no") or ""),
                    date=str(p.get("date") or line.get("billed_date") or "")[:10], units=(sum(float(x["units"] or 0) for x in hit) if hit else None),
                    qty=(sum(float(x["qty"] or 0) for x in hit) if hit else None), free=(sum(float(x["free"] or 0) for x in hit) if hit else None),
                    seq=(p.get("seq") if hit else None), name27=(str(p.get("name27") or "") if hit else ""), how="a")
    od = str(line.get("order_at") or "")[:10]
    try:
        lo = (dt.date.fromisoformat(od) - dt.timedelta(days=_arr_settings(ctx.con, ctx)[1])).isoformat()
    except ValueError:
        return None
    lid = line.get("line_id")
    taken = _taken_lines(sp, k, lid, ctx)
    hit, hkey = None, None
    for p in _purchase_lines_of(sp, k, lo, ctx):
        sk, d, b = str(p["supkey"] or ""), str(p["date"] or "")[:10], _bill(p["bill"])
        if hit is not None and (sk, b, d) != hkey:
            break                                             # the first matching bill's lines are summed (two batches); a later bill never joins
        if any(t[1] == sk and t[2] == b and _matches(ctx, sp, k, t[3], t[4], p["name27"]) for t in taken):   # (b) per line
            continue
        if not _matches(ctx, sp, k, forms, sib, p["name27"]):
            continue
        if d < od:
            how = "c" if (own and sk == own) else None        # (c)
        else:
            how = "d" if (own and sk == own) else "e"         # (d) / (e)
        if not how:
            continue
        if hit is None:
            hit = dict(supplier=str(p.get("supplier") or sk), supkey=sk, bill=str(p["bill"] or ""), date=d, units=float(p["units"] or 0),
                       qty=float(p["qty"] or 0), free=float(p["free"] or 0), seq=p["seq"], name27=str(p["name27"] or ""), how=how)
            hkey = (sk, b, d)
        else:
            hit["units"] += float(p["units"] or 0)
            hit["qty"] += float(p["qty"] or 0)
            hit["free"] += float(p["free"] or 0)
    if hit is not None:
        return hit
    if lid is not None:
        ctx.c[("fam_bill", lid)] = _family_bill(ctx, sp, k, lo, od, own, forms, sib)
    return None


def _family_bill(ctx, sp, k20, lo, od, own, forms, sib):
    """S598 (R1-C9): when no bill line matches the order line -- the family's bill that carried OTHER sizes: among the lines of the key
    since lo that pass the loop's own vendor-and-date test (c: the own vendor before the order day; d / e: any supplier on or after it) and
    do NOT match the line's forms (so only when sib is True), the newest bill -> dict(supplier, supkey, bill, date, sizes=[name27 as Marg
    printed it, deduped by pad_norm, that bill's lines of the key only]); None when there is none. A line already credited to the sibling
    order line still counts here: the clause says what the bill carried. Read by arrivals_open for the owner's words (stock_watch)."""
    sw = _sw()
    best, lines = None, {}
    for p in _purchase_lines_of(sp, k20, lo, ctx):
        sk, d = str(p["supkey"] or ""), str(p["date"] or "")[:10]
        if d < od and not (own and sk == own):
            continue
        if _matches(ctx, sp, k20, forms, sib, p["name27"]):
            continue
        key = (d, sk, _bill(p["bill"]))
        lines.setdefault(key, []).append(p)
        if best is None or key > best:
            best = key
    if best is None:
        return None
    seen, sizes = set(), []
    for p in lines[best]:
        pn = sw.pad_norm(str(p["name27"] or ""))
        if pn and pn not in seen:
            seen.add(pn)
            sizes.append(str(p["name27"] or "").strip())
    p0 = lines[best][0]
    return dict(supplier=str(p0.get("supplier") or p0["supkey"] or ""), supkey=str(p0["supkey"] or ""), bill=str(p0["bill"] or ""), date=best[0], sizes=sizes)
'''))
SF.append(("F6 arrivals_open: the docstring", '''    """Every tapped or scan-tied line that is EXPIRED and not carried, without a billed_bill_no: dict(line_id, item, units, at (the arrival
    moment), who ('scan' for a scan-tied line, else who tapped), vendor, order_id, kind 'tap' | 'scan', scan_tied (its order has a scan tie)).
    Sorted by item, then moment. The owner's Needs-you (stock_watch.arrival_needs_you) names the scan-tied ones; an untied tap stays with D712."""
''', '''    """Every tapped or scan-tied line that is EXPIRED and not carried, without a billed_bill_no: dict(line_id, item, units, at (the arrival
    moment), who ('scan' for a scan-tied line, else who tapped), vendor, order_id, kind 'tap' | 'scan', scan_tied (its order has a scan tie),
    family_bill (S598: the family's bill that carried OTHER sizes of the item -- dict(bill, date, sizes) -- or None)).
    Sorted by item, then moment. The owner's Needs-you (stock_watch.arrival_needs_you) names the scan-tied ones; an untied tap stays with D712."""
'''))
SF.append(("F7 arrivals_open: each entry carries family_bill", '''            out.append(dict(line_id=a["line_id"], item=a["item"], units=float(a["units"] or 0), at=str(a.get("arrived_at") or ""),
                            who=("scan" if a.get("kind") == "scan" else (a.get("arrived_by") or "")), vendor=a.get("vendor") or "", order_id=a.get("order_id"),
                            kind=a.get("kind") or "tap", scan_tied=(int(a.get("order_id") or 0) in tied)))
''', '''            out.append(dict(line_id=a["line_id"], item=a["item"], units=float(a["units"] or 0), at=str(a.get("arrived_at") or ""),
                            who=("scan" if a.get("kind") == "scan" else (a.get("arrived_by") or "")), vendor=a.get("vendor") or "", order_id=a.get("order_id"),
                            kind=a.get("kind") or "tap", scan_tied=(int(a.get("order_id") or 0) in tied), family_bill=ctx.c.get(("fam_bill", a["line_id"]))))
'''))

# =============================================================================================================== porders.py (3.3)
PO = []
PO.append(("P1 detect_supplies' docstring: the matched line's packs (S598)", '''    never marks this line billed. The packs are the spine's own line: SUM(qty) + SUM(free) of that bill for the key (never units / pack_size:
    a 'whole' key's units are its qty). A fresh Ctx per row, so rule (b) sees each write (two lines of one key, two bills). The spine unread
    (sw.ok False): nothing written, one stderr line. The tables (purchase_line) and the 20-letter clip are read no more. Idempotent."""
''', '''    never marks this line billed. The packs are THE MATCHED BILL LINE's own: qty + free as carried() returns them (S598, F-942: the line of
    the order line's own printed name, never the family's sum for the key; two batches of one item on one bill arrive summed; never
    units / pack_size: a 'whole' key's units are its qty). A fresh Ctx per row, so rule (b) sees each write (two lines of one key, two bills).
    The spine unread (sw.ok False): nothing written, one stderr line. The tables (purchase_line) and the 20-letter clip are read no more. Idempotent."""
'''))
PO.append(("P2 the key-level packs query replaced by the matched line's packs", '''            k20 = SF.key_of(sw, item, ctx)
            pr = sw.q("SELECT COALESCE(SUM(qty),0) AS q, COALESCE(SUM(free),0) AS f FROM sp_purchase_line WHERE k20=? AND supkey=? AND bill=? AND date=? "
                      "AND direction='PURCHASE'", k20, hit["supkey"], hit["bill"], hit["date"])
            q = int(round(float(pr[0]["q"] or 0) + float(pr[0]["f"] or 0))) if pr else 0
''', '''            q = int(round(float(hit.get("qty") or 0) + float(hit.get("free") or 0)))   # S598: the matched bill LINE's packs
'''))

# =============================================================================================================== stock_watch.py (3.4)
SW = []
SW.append(("W1 arrival_needs_you: the docstring (S598)", '''    tapped line on an untied order stays with amir_day._d712_owner_lines (D712), so no arrival is said twice. English, one line each. Fail-soft."""
''', '''    tapped line on an untied order stays with amir_day._d712_owner_lines (D712), so no arrival is said twice. English, one line each. Fail-soft.
    S598 (F-942): where the family's bill carried OTHER sizes of the item (arrivals_open's family_bill), the line says so -- ' (its bill N of
    dd-mm carried SIZE, SIZE, not this size)', the sizes as Marg printed them; the clause is built here, once, and nowhere else (charter 8)."""
'''))
SW.append(("W2 the clause, built once", '''            when = "%s %s" % (dmy(str(a["at"])[:10])[:5], str(a["at"])[11:16])
            if a.get("kind") == "scan":
''', '''            when = "%s %s" % (dmy(str(a["at"])[:10])[:5], str(a["at"])[11:16])
            fb = a.get("family_bill") or {}
            more = (" (its bill %s of %s carried %s, not this size)" % (fb.get("bill") or "", dmy(str(fb.get("date") or "")[:10])[:5], ", ".join(fb.get("sizes") or []))) if fb else ""
            if a.get("kind") == "scan":
'''))
SW.append(("W3 the scan line's words", '''                text = "%s: counted as arrived when the %s bill was scanned %s -- not in Marg's purchases up to %s" % (a["item"], a["vendor"] or "supplier's", when, upto)
''', '''                text = "%s: counted as arrived when the %s bill was scanned %s -- not in Marg's purchases up to %s%s" % (a["item"], a["vendor"] or "supplier's", when, upto, more)
'''))
SW.append(("W4 the tapped line's words", '''                text = "%s: counted as arrived when %s tapped it %s (%s) -- not in Marg's purchases up to %s" % (a["item"], a["who"] or "staff", when, a["vendor"] or "-", upto)
''', '''                text = "%s: counted as arrived when %s tapped it %s (%s) -- not in Marg's purchases up to %s%s" % (a["item"], a["who"] or "staff", when, a["vendor"] or "-", upto, more)
'''))

EDITS = {"stock_figure.py": SF, "stock_watch.py": SW, "porders.py": PO}


def apply(src, edits, label, pin):
    raw = open(src, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != pin:
        print("STOP: %s is %s, not the FROM pin %s -- nothing built" % (src, m, pin))
        return None
    t = raw.decode("utf-8")
    for name, old, new in edits:
        n = t.count(old)
        if n != 1:
            print("STOP: %s anchor %s occurs %d times (must be exactly 1) -- nothing built" % (label, name, n))
            return None
        t = t.replace(old, new, 1)
        print("edit %s %s: anchored once, applied" % (label, name))
    return t.encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    built = {}
    for label, edits in EDITS.items():
        out = apply(os.path.join(a.finance, label), edits, label, FROM[label])
        if out is None:
            return 2
        built[label] = out
    sf = built["stock_figure.py"].decode("utf-8")
    for s in ("def _purchases_of", "def _taken_bills", "GROUP BY supkey, bill, date ORDER BY date DESC", "GROUP BY supkey, bill, date ORDER BY date, bill"):
        assert s not in sf, "retired text still in stock_figure.py: %s" % s
    for s in ("def _line_forms(", "def _siblings(", "def _matches(", "def _purchase_lines_of(", "def _taken_lines(", "def _family_bill("):
        assert sf.count(s) == 1, "%s must occur once" % s
    po = built["porders.py"].decode("utf-8")
    assert "SUM(qty)" not in po[po.index("def detect_supplies"):po.index("def _close_complete_orders")], "SUM(qty) still in detect_supplies"
    os.makedirs(a.out, exist_ok=True)
    for label, out in built.items():
        dst = os.path.join(a.out, label)
        with open(dst, "wb") as fh:
            fh.write(out)
        print("built %s md5 %s  (FROM %s)" % (dst, hashlib.md5(out).hexdigest(), FROM[label]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
