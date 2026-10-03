#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p3.py -- kit S454_BILL_REGISTER, part 3 (S454 section 9: one shelf figure, D667; why the system's list differs, F-696). CLAUDE.md
rule 2: every live file built from its live bytes (every anchor exactly once, FROM -> TO pinned); shelf_figure.py is new.

  order_rules.py   order.stock_basis = count (the default): the system's own list works from the shelf figure, Marg's figure beside it on each
                   line (the owner's); what arrived and is not in Marg is in the shelf figure (not counted again); on marg the plan is today's
                   line for line. Every tick records the gap at a new closing (shelf_figure.record_gaps).
  purchase_app.py  F-696 gap (3), proven by the data: Marg's sale export prints 20 characters of a name, so a stock item whose name is longer
                   never met its own sales (55 such items, none with a pace) -- the pace of its 20-character name, shared by the items that
                   carry it.
  stock_watch.py   a spot-count answer is compared with the shelf figure; a flagged gap is one more reason on the roster (never past the cap)
  stock_app.py     a count recorded stores the shelf figure beside Marg's on each row (stock_count_item.shelf_qty)
  order_sheet.py   the settings order.stock_basis and stock.gap_min_packs; the owner's line "Marg and the shelf figure moved apart on N items"
  porders_s454.py  the two settings on the owner's card; the gap card among the owner's ordering cards (S454 7.5)

    make_s454p3.py --finance /root/finance --kit DIR --out DIR
"""
import argparse
import hashlib
import os

FROM = {"order_rules.py": "6587dc84941f4e53ccc39d0847812123", "purchase_app.py": "4eee14b5e41a70c9450ed5cf6ff0bd29",
        "stock_watch.py": "9cca2f2a9e86e6523b9fcefb4f6df3bd", "stock_app.py": "f14a1cfaf9a47b1199a0763ac47d1006",
        "order_sheet.py": "b2e61034790ea37fde4272859ccd1f58", "porders_s454.py": "e2228b8f8434e8ea3766b00e5e5e1a2e"}
NEWF = ("shelf_figure.py",)

# ============================================================================================================== order_rules.py
OR = [('''def _snapshot_inputs(con, today):
    pa = _pa()
    as_on, snap = pa._latest_snapshot(con)
    pace = pa._pace(con, snap, today)
    purch = pa._last_purchase(con)
    transit = pa._in_transit(con, today)
    onord = _on_order_units(con, today)''',
       '''def _snapshot_inputs(con, today):
    pa = _pa()
    as_on, snap = pa._latest_snapshot(con)
    basis = _s454_basis(con)
    if basis == "count":                                       # S454 P3 (9.2): the shelf figure; Marg's figure kept beside it (marg_qty)
        snap = _s454_shelf_snap(con, snap)
    pace = pa._pace(con, snap, today)
    purch = pa._last_purchase(con)
    transit = pa._in_transit(con, today)
    onord = _on_order_units(con, today)
    if basis == "count":                                       # an item ON the shelf figure carries what arrived and is not yet in Marg:
        transit, onord = _s454_count_way(con, today, snap, transit, onord)   # only what is still on the way counts; an item with no count as before'''),
      ('''def _on_order_units(con, today):''', '''def _on_order_units(con, today, basis=None):'''),
      ('''                           "WHERE (o.status='sent'" + _s454_or_arrived(con) + ") AND o.created_at>=? AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",''',
       '''                           "WHERE (o.status='sent'" + (_s454_or_arrived(con) if basis != "count" else _s454_not_tied(con)) + ") AND o.created_at>=? "
                           "AND l.supplied IS NULL AND COALESCE(l.missing,0)=0",          # S454 P3: on count, an order arrived by its scan is in the shelf figure'''),
      ('''        lo["vendor_norm"] = vn
        v = vendors.setdefault(vn, dict(vendor=it["vendor"], vendor_norm=vn, lines=[], total_p=0, rule=r))''',
       '''        lo["vendor_norm"] = vn
        lo["marg_qty"] = s.get("marg_qty", s["qty"])            # S454 P3 (9.2): both figures, for the owner's eyes (no staff screen prints them)
        lo["shelf_qty"] = s["qty"] if "marg_qty" in s else None
        v = vendors.setdefault(vn, dict(vendor=it["vendor"], vendor_norm=vn, lines=[], total_p=0, rule=r))'''),
      ('''        return order_sheet.cron_pass(con, "cron")
    except Exception as e:                                    # noqa: BLE001
        return dict(error=str(e)[:120])''',
       '''        out = order_sheet.cron_pass(con, "cron")
        try:                                                  # S454 P3 (9.3): Marg's newest closing beside the shelf figure, once per closing
            import shelf_figure                               # noqa: PLC0415
            out["gaps"] = shelf_figure.record_gaps(con)
        except Exception as e2:                               # noqa: BLE001
            out["gaps"] = "error: %s" % str(e2)[:80]
        return out
    except Exception as e:                                    # noqa: BLE001
        return dict(error=str(e)[:120])''')]
OR_APPEND = '''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.2, D667): order.stock_basis -- count (the default): the system's own list works from the shelf
# figure (shelf_figure.figures: the newest physical count carried forward by the spine's sales and purchases, plus what arrived and is not
# in Marg); marg: Marg's closing stock, today's plan line for line. An item with no count keeps Marg's figure.
# ==========================================================================================================================================
def _s454_basis(con):
    try:
        import order_sheet                                    # noqa: PLC0415
        v = order_sheet.setting(con, "order.stock_basis")
    except Exception:                                         # noqa: BLE001
        v = "count"
    return v if v in ("count", "marg") else "count"


def _s454_shelf_snap(con, snap):
    """The snapshot with each item's qty replaced by its shelf figure (Marg's kept as marg_qty); fail-soft: Marg's snapshot as it is."""
    try:
        import shelf_figure                                   # noqa: PLC0415
        F = shelf_figure.figures(con, items=[s["item"] for s in snap.values()])
    except Exception:                                         # noqa: BLE001
        return snap
    out = {}
    for k, s in snap.items():
        f = F.get(s["item"]) or {}
        d = dict(s)
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            d["marg_qty"] = s["qty"]
            d["qty"] = int(f["shelf"])
        out[k] = d
    return out


def _s454_count_way(con, today, snap, transit, onord):
    """On count: on the way = a SENT order not yet arrived by its bill's scan, for every item. An order that arrived by its scan is marked
    'received' (order_sheet), so it is counted once -- by Marg's in-transit (purchase_app._in_transit) for an item with no count, and inside
    the shelf figure for an item on it (Marg's in-transit dropped there). On marg the old way stands, which counted such an order twice."""
    shelf = {k for k, s in snap.items() if "marg_qty" in s}
    transit = {k: v for k, v in transit.items() if k not in shelf}
    return transit, _on_order_units(con, today, "count")


def _s454_not_tied(con):
    try:
        con.execute("SELECT 1 FROM order_scan_tie LIMIT 1")
        return " AND o.id NOT IN (SELECT order_id FROM order_scan_tie WHERE arrived=1)"
    except sqlite3.Error:
        return ""
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== purchase_app.py
PA_APPEND = '''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.4, F-696): gap (3), proven by the data -- Marg's sale export prints 20 characters of an item's
# name, so _pace never found the sales of a stock item whose name is longer (55 such items on 03-Oct, not one with a pace) and plan() skipped
# them. Such an item now takes the pace of its 20-character name; items that share that name share it equally (approximate) -- on
# order.stock_basis = count (the default); on marg the plan stays today's, line for line. The other two
# suspected gaps were tested and not proven by the data (see the kit's report): not changed.
# ==========================================================================================================================================
_pace_before_s454 = _pace


def _pace(con, snap, today):                                       # noqa: F811
    out = _pace_before_s454(con, snap, today)
    try:
        r_ = con.execute("SELECT value FROM setting WHERE key='order.stock_basis'").fetchone()
        if r_ and str(r_[0] or "").strip() == "marg":
            return out                                         # on marg the plan is today's, line for line (S454 9.2)
        import item_alias as _ia                               # noqa: PLC0415
        clip = getattr(_ia, "SALE_CLIP", 20)
        fam = {}
        for k, s in snap.items():
            if len(str(s["item"])) > clip:
                fam.setdefault(norm(str(s["item"])[:clip]), []).append(k)
        if not fam:
            return out
        since = (today - dt.timedelta(days=PACE_DAYS)).isoformat()
        per, last = {}, {}
        for name, d, q, ret in con.execute("SELECT item_name, business_date, qty_raw, is_return FROM sale_line_item WHERE unit=? AND business_date>=? "
                                           "AND business_date<=?", (_unit, since, today.isoformat())):
            ck = norm(str(name)[:clip])
            if ck not in fam:
                continue
            size = (snap.get(fam[ck][0]) or {}).get("pack_size", 1)
            e = per.setdefault(ck, {"days": {}, "total": 0.0})
            u = _units(q, size) * (-1 if ret else 1)
            e["days"][d] = e["days"].get(d, 0.0) + u
            e["total"] += u
        for name, d in con.execute("SELECT item_name, MAX(business_date) FROM sale_line_item WHERE unit=? GROUP BY item_name", (_unit,)):
            ck = norm(str(name)[:clip])
            if ck in fam and (ck not in last or d > last[ck]):
                last[ck] = d
        for ck, members in fam.items():
            e = per.get(ck)
            n = len(members)
            for k in members:
                if k in out and out[k].get("rate_per_day"):
                    continue
                if e:
                    total = max(0.0, e["total"]) / n
                    peak = max(e["days"].values()) / n if e["days"] else 0.0
                    out[k] = dict(rate_per_day=total / PACE_DAYS, sell_days=sum(1 for v in e["days"].values() if v > 0),
                                  peak_share=(peak / total) if total > 0 else 0.0, approx_shared=n if n > 1 else 0)
                if ck in last:
                    try:
                        out.setdefault(k, dict(rate_per_day=0.0, sell_days=0, peak_share=0.0))["days_since_sale"] = (today - dt.date.fromisoformat(last[ck])).days
                    except ValueError:
                        pass
    except Exception:                                          # noqa: BLE001 -- the plan never fails for it: the old pace stands
        return out
    return out
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== stock_watch.py
SW = [('''    E = expected_units(con, sp, item)
    ts = now_iso()''',
       '''    E = _s454_expected(con, sp, item)                          # S454 P3 (9.2, D667): the shelf figure, else the records' expectation
    ts = now_iso()'''),
      ('''    keys = ("turnover", "movement", "arrival", "loss", "value", "stale")''',
       '''    keys = ("turnover", "movement", "arrival", "loss", "value", "stale", "gap")     # S454 P3 (9.3): the shelf figure and Marg moved apart'''),
      ('''    for m in keys:
        if not W.get(m):
            continue
        order = sorted(ks, key=lambda k: -float(cands[k][m] or 0))''',
       '''    for m in keys:
        if not (W.get(m) if m != "gap" else W.get(m, 3)):
            continue
        order = sorted(ks, key=lambda k: -float(cands[k].get(m) or 0))'''),
      ('''            while j + 1 < len(order) and cands[order[j + 1]][m] == cands[order[i]][m]:
                j += 1
            val = 1.0 - (i + j) / 2.0 / n if float(cands[order[i]][m] or 0) > 0 else 0.0
            for k in order[i:j + 1]:
                score[k] += W[m] * val''',
       '''            while j + 1 < len(order) and cands[order[j + 1]].get(m) == cands[order[i]].get(m):
                j += 1
            val = 1.0 - (i + j) / 2.0 / n if float(cands[order[i]].get(m) or 0) > 0 else 0.0
            for k in order[i:j + 1]:
                score[k] += (W.get(m) if m != "gap" else W.get(m, 3)) * val'''),
      ('''stale=since_days, last_point=lp)''', '''stale=since_days, last_point=lp, gap=_s454_gap_flag(con, nm))'''),
      ('''    en, hi = [], []
    if c["arrival"]:''',
       '''    en, hi = [], []
    if c.get("gap"):                                           # S454 P3 (9.3)
        en.append("the shelf figure and Marg moved apart"); hi.append("Marg aur shelf mein fark badla")
    if c["arrival"]:''')]
SW_APPEND = '''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.2 / 9.3, D667): a spot-count answer is compared with the SHELF FIGURE (shelf_figure: the newest
# count carried forward by the spine's sales and purchases, plus what arrived and is not yet in Marg) -- the records' expectation from Marg's
# latest closing stays the fallback (an item no count has reached, or no spine). An item flagged at the newest closing (the shelf figure and
# Marg moved apart with no voucher) is one more reason in the roster's ranking, never past its cap.
# ==========================================================================================================================================
def _s454_expected(con, sp, item):
    E = expected_units(con, sp, item)
    try:
        import shelf_figure                                   # noqa: PLC0415
        f = (shelf_figure.figures(con, sp=sp, items=[item]) or {}).get(item) or {}
        if f.get("shelf") is not None and f.get("named") not in ("no_count", "no_spine"):
            E = dict(E, expected=float(f["shelf"]), provisional=float(f.get("arrived") or 0), as_on=f.get("base_day"), close=f.get("base"),
                     sold=float(f.get("sold") or 0), bought=float(f.get("bought") or 0), basis="shelf", records=E.get("expected"))
    except Exception:                                         # noqa: BLE001 -- the count is never refused for it
        pass
    return E


def _s454_gap_flag(con, nm):
    try:
        import shelf_figure                                   # noqa: PLC0415
        return shelf_figure.gap_flag(con, nm)
    except Exception:                                         # noqa: BLE001
        return 0
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== stock_app.py
SA = [('''    snap = _snapshot_qty_map(con, b["marg_as_on"].strip())
    marg_claim_mismatch = []''',
       '''    snap = _snapshot_qty_map(con, b["marg_as_on"].strip())
    _s454_shelf = _s454_shelf_map(con, [(it.get("item") or "").strip() for it in items])   # S454 P3 (9.2): BEFORE this count becomes the base
    marg_claim_mismatch = []'''),
      ('''             it.get("at") or now_iso(),
             json.dumps(bat, ensure_ascii=False) if bat else None))
        if got != marg:''',
       '''             it.get("at") or now_iso(),
             json.dumps(bat, ensure_ascii=False) if bat else None))
        _s454_store_shelf(con, cid, name, _s454_shelf)        # S454 P3: the shelf figure beside Marg's on the row
        if got != marg:''')]
SA_APPEND = '''


# ==========================================================================================================================================
# S454_BILL_REGISTER part 3 (03-Oct-2026, S454 9.2, D667): when a count is recorded, the shelf figure of each item (worked out before the count
# becomes the newest base) is stored beside Marg's on its row (stock_count_item.shelf_qty) and shown to the owner on his ordering cards.
# The loss desk goes on judging by Marg's figure in this kit; judging a full count by the shelf figure is the next kit's.
# ==========================================================================================================================================
def _s454_shelf_map(con, names):
    try:
        cols = {r[1] for r in con.execute("PRAGMA table_info(stock_count_item)")}
        if "shelf_qty" not in cols:
            con.execute("ALTER TABLE stock_count_item ADD COLUMN shelf_qty REAL")
        import shelf_figure                                   # noqa: PLC0415
        return shelf_figure.shelf_map(con, names)
    except Exception:                                         # noqa: BLE001 -- a count is never refused for it
        return {}


def _s454_store_shelf(con, cid, name, m):
    try:
        if name in (m or {}):
            con.execute("UPDATE stock_count_item SET shelf_qty=? WHERE count_id=? AND item=?", (m[name], cid, name))
    except Exception:                                         # noqa: BLE001
        pass
# ---- S454 part 3 end -------------------------------------------------------------------------------------------------------------------
'''

# ============================================================================================================== order_sheet.py
OSE = [('''    "purchase.entry_wait_days": ("7", "S454 P2 (7.3): you see a read scan not yet entered in Marg after this many days (Amir is not told)"),''',
        '''    "purchase.entry_wait_days": ("7", "S454 P2 (7.3): you see a read scan not yet entered in Marg after this many days (Amir is not told)"),
    "order.stock_basis": ("count", "S454 P3 (9.2): count = the system's own list works from the shelf figure (the 6 Sep count carried forward); "
                                   "marg = from Marg's closing stock, line for line as before"),
    "stock.gap_min_packs": ("1", "S454 P3 (9.3): a change of the gap between the shelf figure and Marg smaller than this many packs of the item "
                                 "is not counted"),'''),
       ('''        rf = refused_sheet(con)
        if rf and str(rf["at"])[:10] == today().isoformat():''',
        '''        try:                                                  # S454 P3 (9.3): one line, the count of such items and their names
            import shelf_figure                               # noqa: PLC0415
            gl = shelf_figure.gap_line(con)
            if gl:
                out.append(gl)
        except Exception:                                     # noqa: BLE001
            pass
        rf = refused_sheet(con)
        if rf and str(rf["at"])[:10] == today().isoformat():''')]

# ============================================================================================================== porders_s454.py
PS = [('''    if key == "purchase.entry_mode":                          # S454 P2 (6): paper, or both; digital is not built
        return v in ("paper", "both"), v''',
       '''    if key == "purchase.entry_mode":                          # S454 P2 (6): paper, or both; digital is not built
        return v in ("paper", "both"), v
    if key == "order.stock_basis":                            # S454 P3 (9.2)
        return v in ("count", "marg"), v'''),
      ('''           "purchase.entry_wait_days": (1, 60)}.get(key)''',
       '''           "purchase.entry_wait_days": (1, 60), "stock.gap_min_packs": (0, 100)}.get(key)'''),
      ('''    h.append(phone_card(con, st))                              # S454 P1C (17.7): the reception phone's state and a test message''',
       '''    h.append(_s454_gap_card(con, st))                          # S454 P3 (7.5): Marg and the shelf figure
    h.append(phone_card(con, st))                              # S454 P1C (17.7): the reception phone's state and a test message''')]
PS_APPEND = '''


# ---- S454 part 3 (7.5 / 9.3): the owner's card "Marg and the shelf figure moved apart on N items" -----------------------------------------
def _s454_gap_card(con, st):
    try:
        import shelf_figure                                   # noqa: PLC0415
        as_on, fl = shelf_figure.gap_flags(con)
        basis = OS.setting(con, "order.stock_basis")
        lst = "".join("<li>%s: %s</li>" % (esc(x["item"]), esc(x["why"] or "")) for x in fl)
        cnt = con.execute("SELECT c.id, c.marg_as_on, COUNT(i.shelf_qty) FROM stock_count c JOIN stock_count_item i ON i.count_id=c.id "
                          "WHERE i.shelf_qty IS NOT NULL GROUP BY c.id ORDER BY c.id DESC LIMIT 1").fetchone() if _s454_has_shelf_col(con) else None
        return ('<div %s id="s454gap"><b>Marg and the shelf figure moved apart on %d item%s</b>%s'
                '<div style="color:#666;font-size:13px">The shelf figure is the 6 September count carried forward by sales and purchases, plus what arrived and '
                'is not yet in Marg. The system\\'s own list works from %s. A gap that moves with no voucher sends the item up Darpan\\'s spot-count list.%s</div>'
                '%s</div>' % (st, len(fl), "" if len(fl) == 1 else "s", (" (closing of %s)" % esc(OS.dmy(as_on))) if as_on else " (no closing recorded yet)",
                              "the shelf figure" if basis == "count" else "Marg's closing stock",
                              (" At the count of %s the shelf figure was stored beside Marg's on %d rows." % (esc(cnt[1]), cnt[2])) if cnt else "",
                              ("<details><summary>the items</summary><ul>%s</ul></details>" % lst) if lst else ""))
    except Exception:                                         # noqa: BLE001
        return ""


def _s454_has_shelf_col(con):
    try:
        return "shelf_qty" in {r[1] for r in con.execute("PRAGMA table_info(stock_count_item)")}
    except sqlite3.Error:
        return False
# ---- S454 part 3 end ---------------------------------------------------------------------------------------------------------------------
'''

EDITS = {"order_rules.py": OR, "stock_watch.py": SW, "stock_app.py": SA, "order_sheet.py": OSE, "porders_s454.py": PS}
APPEND = {"order_rules.py": OR_APPEND, "purchase_app.py": PA_APPEND, "stock_watch.py": SW_APPEND, "stock_app.py": SA_APPEND, "porders_s454.py": PS_APPEND}


GUARD = "\nif __name__ == \"__main__\":"


def place_block(txt, block):
    """The block goes ABOVE the file's `if __name__ == "__main__":` guard when it has one (a cron runs order_rules.py, stock_watch.py and
    purchase_app.py as scripts: a block below the guard is not defined yet when main() runs -- part 1's fault, mended by part 1D), else at the end."""
    c = txt.count(GUARD)
    if c > 1:
        raise SystemExit("STOP: the __main__ guard occurs %d times -- nothing built" % c)
    if c == 1:
        i = txt.index(GUARD)
        return txt[:i].rstrip("\n") + "\n" + block.rstrip("\n") + "\n\n" + txt[i:]
    return txt.rstrip("\n") + "\n" + block


def md5b(b):
    return hashlib.md5(b).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for f in sorted(FROM):
        raw = open(os.path.join(a.finance, f), "rb").read()
        m = md5b(raw)
        if m != FROM[f]:
            raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
        txt = raw.decode("utf-8")
        for old, new in EDITS.get(f, []):
            c = txt.count(old)
            if c != 1:
                raise SystemExit("STOP: an anchor occurs %d times in %s -- nothing built: %r" % (c, f, old[:90]))
            txt = txt.replace(old, new, 1)
        if f in APPEND:
            txt = place_block(txt, APPEND[f])
        out = txt.encode("utf-8")
        open(os.path.join(a.out, f), "wb").write(out)
        print("built %-18s %s -> %s  (%d edits%s)" % (f, m[:8], md5b(out), len(EDITS.get(f, [])), " + 1 block" if f in APPEND else ""))
    for f in NEWF:
        if os.path.exists(os.path.join(a.finance, f)):
            raise SystemExit("STOP: %s exists already on the box -- nothing built" % f)
        raw = open(os.path.join(a.kit, f), "rb").read()
        open(os.path.join(a.out, f), "wb").write(raw)
        print("new   %-18s %s" % (f, md5b(raw)))


if __name__ == "__main__":
    main()
