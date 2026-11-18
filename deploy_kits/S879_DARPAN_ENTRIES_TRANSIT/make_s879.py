"""make_s879.py <finance dir holding the FROM files> <out dir> -- kit S879_DARPAN_ENTRIES_TRANSIT (Session 483, 18-Nov-2026).
   darpan_kal.py    (d27ed062) two anchors: the expected cash reads the owner's day entries (hub_cash.entries -- the one store,
                    read only); a stored day whose expected moved because of those entries is re-decided on its next view (F-1468).
   darpan_kal.html  (b7d2d61e) two anchors: one row under the existing adjustment row on Darpan's card (Hindi, amount only)
                    and the same row in the doctor's own view (English).
   purchase_app.py  (c15bc1c5) two anchors: _in_transit leaves out a scan-tied order line its dealer's bill does not carry
                    (stock_figure.s825_bill_judged, read only; on any failure the old reading) -- the tables fallback no longer
                    counts such a line both in transit and on order (S825's open note).
Every anchor must occur exactly once at its FROM pin; nothing is written when one does not."""
import hashlib
import os
import sys

SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"darpan_kal.py": "d27ed062f73e3becbd23b5a9136f7ba0", "darpan_kal.html": "b7d2d61e946454d940f6836e5677f294",
        "purchase_app.py": "c15bc1c5806bb4a7aabd261b6cd580f9"}

P = {
"darpan_kal.py": [
 ('''    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"] + out["adjust_p"]\n''',
  '''    # S879 (F-1468): the owner's own entries on the day (hub_cash.py -- money paid into another account never reached
    # the drawer; cash taken out on a doctor's word left it) lower what Darpan hands over. Read only; 0 when absent.
    # While the day stands on Marg's own modes, a payment into another account is left out: Marg keyed it as UPI/card,
    # so it is already outside the cash -- the bank's statement (or the POS total) brings it in.
    _oth, _tak, out["owner_any"] = _s879_owner(con, iso)
    out["owner_p"] = _tak + (0 if out.get("online_source") == "marg" else _oth)
    out["expected_p"] = out["net_sale_p"] - out["home_p"] - out["proc_p"] - out["online_p"] + out["adjust_p"] - out["owner_p"]
'''),
 ('''             and int(row.get("online_p") or 0) != int(calc["online_p"])):      # S496: decided before the POS total was confirmed;\n''',
  '''             and int(row.get("online_p") or 0) != int(calc["online_p"])) or \\
            (calc["applied"] and calc.get("owner_any") and row.get("state") != "waiting_report"          # S879: the owner's entries
             and _s879_seen(con, iso) != int(calc.get("owner_p") or 0) and not _s879_spread(con, iso, row)):   # changed
        # S496: decided before the POS total was confirmed;
'''),
 ('''def _row(con, iso):''',
  '''def _s879_owner(con, iso):
    """S879: (the day's live 'other_account' entries, its live 'taken_out' entries -- paise -- and whether the day has ANY
    owner entry row, removed ones included). hub_cash.entries is the one reader of owner_day_entry; (0, 0, False) when the
    table or the module is absent."""
    try:
        if not _has(con, "owner_day_entry"):
            return 0, 0, False
        import hub_cash                                        # noqa: PLC0415 -- beside this file (S869)
        es = hub_cash.entries(con, _unit, iso, iso).get(iso, [])
        oth = sum(int(e["amount_p"]) for e in es if e.get("kind") == "other_account")
        tak = sum(int(e["amount_p"]) for e in es if e.get("kind") != "other_account")
        anyrow = con.execute("SELECT 1 FROM owner_day_entry WHERE unit=? AND business_date=? LIMIT 1", (_unit, iso)).fetchone() is not None
        return oth, tak, anyrow
    except Exception:                                         # noqa: BLE001 -- fail-soft: the old figure
        return 0, 0, False


def _s879_seen(con, iso):
    """S879: the owner entries' figure the stored day was last decided with (0 when never) -- a day is re-decided only when
    THAT moves, never for any other change in its books."""
    try:
        con.execute("CREATE TABLE IF NOT EXISTS darpan_kal_s879 (unit TEXT NOT NULL, business_date TEXT NOT NULL, "
                    "owner_p INTEGER NOT NULL, at TEXT, PRIMARY KEY (unit, business_date))")
        r = con.execute("SELECT owner_p FROM darpan_kal_s879 WHERE unit=? AND business_date=?", (_unit, iso)).fetchone()
        return int(r[0]) if r else 0
    except sqlite3.Error:
        return -1                                              # unreadable: never equal, but _s879_mark fails too -> no loop below


def _s879_mark(con, iso, owner_p):
    try:
        con.execute("INSERT INTO darpan_kal_s879 (unit, business_date, owner_p, at) VALUES (?,?,?,?) ON CONFLICT(unit, business_date) "
                    "DO UPDATE SET owner_p=excluded.owner_p, at=excluded.at", (_unit, iso, int(owner_p), now_iso()))
        return True
    except sqlite3.Error:
        return False


def _s879_spread(con, iso, row):
    """S879: True when the day's handover was recorded as paying for OTHER days too (a spread cover) -- such a day is left
    as it is, never collapsed by a re-decide."""
    try:
        mid = row.get("landed_movement_id")
        if not mid or not _has(con, "cash_handover_cover"):
            return False
        return con.execute("SELECT 1 FROM cash_handover_cover WHERE handover_src='movement' AND handover_id=? AND covers_date<>? LIMIT 1",
                           (mid, iso)).fetchone() is not None
    except sqlite3.Error:
        return True


def _row(con, iso):'''),
 ('''    return dict(state=state, diff_p=diff, verdict=verdict, reason=reason)\n''',
  '''    _s879_mark(con, iso, calc.get("owner_p") or 0)                # S879: the entries' figure this decision used
    return dict(state=state, diff_p=diff, verdict=verdict, reason=reason)
'''),
 ('''    for r in con.execute("SELECT business_date FROM darpan_kal_day WHERE unit=? AND business_date>=? "
                         "AND (online_provisional=1 OR state='waiting_report')", (_unit, since)):
        _refresh_if_needed(con, r["business_date"])
''',
  '''    _s879_e = _has(con, "owner_day_entry")                  # S879: a day the owner's entries touch is refreshed here too
    _s879_q = ("SELECT business_date FROM darpan_kal_day WHERE unit=? AND business_date>=? AND (online_provisional=1 OR state='waiting_report'"
               + (" OR business_date IN (SELECT business_date FROM owner_day_entry WHERE unit=?)" if _s879_e else "") + ")")
    for r in list(con.execute(_s879_q, (_unit, since, _unit) if _s879_e else (_unit, since))):
        _refresh_if_needed(con, r["business_date"])
'''),
],
"darpan_kal.html": [
 ('''   (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' सुधार (घर / प्रोसीजर की दवा वापस — cash नहीं)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+''',
  '''   (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' सुधार (घर / प्रोसीजर की दवा वापस — cash नहीं)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+
   (c.owner_p?'<div class="row"><span class="k">− डॉक्टर साहब की entry (drawer से बाहर)</span><span class="v">'+R(c.owner_p)+'</span></div>':'')+'''),
 ('''  (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' adjustment (home / procedure medicine returned, no cash)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+''',
  '''  (c.adjust_p?'<div class="row"><span class="k">'+(c.adjust_p>0?'+':'−')+' adjustment (home / procedure medicine returned, no cash)</span><span class="v">'+R(Math.abs(c.adjust_p))+'</span></div>':'')+
  (c.owner_p?'<div class="row"><span class="k">− your day entries (paid into another account / cash taken out)</span><span class="v">'+R(c.owner_p)+'</span></div>':'')+'''),
],
"purchase_app.py": [
 ('''"SELECT l.item, COALESCE(l.supplied, l.packs) AS got, l.pack_size, o.vendor, o.id AS oid, o.received_at "''',
  '''"SELECT l.id AS lid, l.item, COALESCE(l.supplied, l.packs) AS got, l.pack_size, o.vendor, o.id AS oid, o.received_at "'''),
 ('''        return out
    for r in rows:
        seen = con.execute(
            "SELECT 1 FROM purchase_line l WHERE l.supplier_norm=? AND l.item=? AND l.bill_date >= ? AND " + EFF_LINE + " LIMIT 1",''',
  '''        return out
    judged = None
    try:                                                   # S879 (S825's note): a scan-tied line its bill does not carry has not
        import stock_figure as _sf                         # arrived -- it stays on order, never also in transit. Read only.
        judged = _sf.s825_bill_judged(con) if rows else None
    except Exception:                                      # noqa: BLE001 -- the old reading
        judged = None
    for r in rows:
        if judged and judged.get(int(r["lid"])) is False:
            continue
        seen = con.execute(
            "SELECT 1 FROM purchase_line l WHERE l.supplier_norm=? AND l.item=? AND l.bill_date >= ? AND " + EFF_LINE + " LIMIT 1",'''),
],
}


def main():
    outs = {}
    for f, pin in FROM.items():
        b = open(os.path.join(SRC, f), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s is not at its FROM pin (%s)" % (f, hashlib.md5(b).hexdigest())
        t = b.decode("utf-8")
        for a, r in P[f]:
            n = t.count(a)
            assert n == 1, "%s: an anchor occurs %d times: %r" % (f, n, a[:70])
            t = t.replace(a, r)
        outs[f] = t
    os.makedirs(OUT, exist_ok=True)
    for f, t in outs.items():
        open(os.path.join(OUT, f), "wb").write(t.encode("utf-8"))
        print(f, hashlib.md5(t.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()
