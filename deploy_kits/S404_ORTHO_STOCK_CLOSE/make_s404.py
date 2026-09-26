#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s404.py -- builds the nine patched live files of kit S404_ORTHO_STOCK_CLOSE from the LIVE bytes by
anchored edits. Every anchor must occur exactly once, and every source must be at its FROM pin, or the
build stops with nothing written. Nothing is re-typed.

  stock_app.py        three cause values added as data (Darpan's chips); the rename memory applied at read time
                      in the count/stock lanes (_mrp_p, _feed_latest, reconcile, _sales_since, _purchases_since,
                      _item_life, _pursue_sales); match_answer() = the ONE door for a pair answer; the voucher
                      round takes a section filter (Orthotics only); the proof carries items_ok; the hub carries
                      the orthotic section; Amir's board carries the 22 renames + the tick route; api_snapshot
                      reads a ticked rename back from Marg's own export (F-529)
  stock_hub.html      '(Darpan)' beside a pair he answered; the Orthotics section card: verdict, four conditions,
                      Darpan's reason per open orthotic line with the owner's one-tap change, Make the orthotic round
  stock_amir.html     'Naam badlo (22)' card with one tick each; a round made of orthotic lines is labelled
  section_map.py      inherit(): the new name inherits the old name's section
  spine/spine_build.py a ticked rename is an alias new -> old (read-only from finance.db), recorded in sp_alias
  marg_ingest/marg_take.py  a VERIFIED closing-stock export marks the renames it carries (fail-soft)
  finance_app.py      the front gate learns the unit 'stockmatch' (/finance/stockmatch/...); the module is mounted
  portal.py           the tile 'Stock milaan' (roles ['doctor']; granted by name)
  tile_grants.json    v26 -> v27: the tile to darpan

Usage: make_s404.py --finance /root/finance --portal /root/portal --marg /root/marg_ingest --out DIR
Writes the nine files into DIR (flat) and prints each md5.
"""
import hashlib
import json
import os
import sys

FROM = {
    "stock_app.py": "1b473fbf586dea13edd40a6a993cb2ba",
    "stock_hub.html": "c4f3280b2d005b39c02d3f6eed13c3ec",
    "stock_amir.html": "14024b8dfc64c76959ec12f43e0a4f88",
    "section_map.py": "b05b0f08ad65519675e21c9a6f4e90a0",
    "spine_build.py": "1378c87de2f8d4b3796cd92c7ca50d8d",
    "marg_take.py": "75b8056cc43ad6f3034ea1fa819ed7a8",
    "finance_app.py": "d7ee72c51564a397f4e847e98eb80ddc",
    "portal.py": "592ccf99d02c361d4d5eb580995599c3",
    "tile_grants.json": "9231cefad0897a64aa127ce4a448f4fe",
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def load(path, name):
    raw = open(path, "rb").read()
    if md5(raw) != FROM[name]:
        sys.exit("REFUSED: %s is %s, not its FROM pin %s" % (path, md5(raw), FROM[name]))
    return raw.decode("utf-8")


def rep(s, old, new, what):
    n = s.count(old)
    if n != 1:
        sys.exit("REFUSED: anchor for %s found %d times (need exactly 1): %r" % (what, n, old[:80]))
    return s.replace(old, new)


# ---------------------------------------------------------------- stock_app.py
def build_stock_app(s):
    # 1 -- the three cause values, added as data; nothing existing changes
    s = rep(s, '''CAUSES = ("UNEXPLAINED", "EXPIRY", "BREAKAGE", "ISSUE", "RECEIVE",
          "BILLING", "FOUND", "THEFT")
''', '''CAUSES = ("UNEXPLAINED", "EXPIRY", "BREAKAGE", "ISSUE", "RECEIVE",
          "BILLING", "FOUND", "THEFT",
          "NOT_RETURNED", "DONT_KNOW", "BILLED_NOT_GIVEN")   # S404 (D619): Darpan's chips -- added, nothing existing changed
''', "CAUSES")
    s = rep(s, '''    "THEFT":       "taken",
}
''', '''    "THEFT":       "taken",
    "NOT_RETURNED": "went out, never came back",           # S404: Darpan -- 'Vaapas nahi aaya'
    "DONT_KNOW":    "staff does not know",                 # S404: Darpan -- 'Pata nahi' (a real answer, unlike UNEXPLAINED)
    "BILLED_NOT_GIVEN": "billed, not handed over",         # S404: Darpan on a surplus -- 'Bill bana, diya nahi'
}
''', "CAUSE_LABEL")
    # 2 -- the rename memory, applied at read time
    s = rep(s, '''def _sale_key(name):
    """finance_returns.norm_item(), verbatim: the key the sale lines are stored under."""
    s = _re221.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return _re221.sub(r"\\s+", " ", s).strip()
''', '''def _sale_key(name):
    """finance_returns.norm_item(), verbatim: the key the sale lines are stored under."""
    s = _re221.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return _re221.sub(r"\\s+", " ", s).strip()


# --- S404_ORTHO_STOCK_CLOSE begin (D620): the rename memory, applied where a name is keyed ------------
# Amir renames an item in Marg; every later export carries the NEW name while the count, its differences
# and its vouchers are keyed by the OLD one. item_alias.py (beside this file) holds the memory: a rename
# Amir has TICKED resolves the new name -- exact, or its 20 / 27-character clip, or their keys -- to the
# old one, HERE, at read time, for the count and stock lanes. An unticked rename maps nothing. Every
# helper is fail-soft: with no memory the lanes read exactly as they did before S404.
def _alias_map(con):
    try:
        import item_alias                                      # noqa: PLC0415
        return item_alias.resolve_map(con)
    except Exception:                                          # noqa: BLE001
        return {}


def _alias_names(con, item):
    """[item] + every spelling of its ticked NEW name (exact and clipped) -- for an IN (...) lookup."""
    out = [item]
    try:
        import item_alias                                      # noqa: PLC0415
        for f in item_alias.aliases_of(con, item):
            if f not in out:
                out.append(f)
    except Exception:                                          # noqa: BLE001
        pass
    return out


def _alias_sale_keys(con, item):
    """The sale_line_item.item_key forms of an item and of its ticked new name."""
    out = []
    for n in _alias_names(con, item):
        for k in (n, _sale_key(n)):
            if k and k not in out:
                out.append(k)
    return out


def _alias_fold_items(con, items):
    """{name: qty} read from an export -> keyed by the OLD name wherever a ticked rename applies."""
    m = _alias_map(con)
    if not m:
        return items
    out = {}
    for k, v in items.items():
        t = m.get(k, k)
        out[t] = out.get(t, 0) + v
    return out


def _alias_fold_keys(con, table, keyfn, merge):
    """Fold a lane's {key: row} dict: a row keyed under a ticked NEW name is merged into the OLD name's key."""
    try:
        import item_alias                                      # noqa: PLC0415
        rows = item_alias.done_rows(con)
    except Exception:                                          # noqa: BLE001
        return table
    for r in rows:
        ok = keyfn(r["old_name"])
        for form in item_alias.forms_of(r["new_name"]):
            nk = keyfn(form)
            if nk in table and nk != ok:
                table[ok] = merge(table.get(ok), table.pop(nk))
    return table
# --- S404_ORTHO_STOCK_CLOSE end ---------------------------------------------------------------------
''', "alias helpers")
    s = rep(s, '''        rows = con.execute(
            "SELECT amount_p, pack FROM sale_line_item WHERE item_key IN (?, ?) "
            "AND is_return=0 AND amount_p>0 ORDER BY business_date DESC LIMIT 200",
            (item, _sale_key(item))).fetchall()
''', '''        _ks = _alias_sale_keys(con, item)                     # S404: the ticked new name's keys too
        rows = con.execute(
            "SELECT amount_p, pack FROM sale_line_item WHERE item_key IN (%s) "
            "AND is_return=0 AND amount_p>0 ORDER BY business_date DESC LIMIT 200" % ",".join("?" * len(_ks)),
            tuple(_ks)).fetchall()
''', "_mrp_p")
    s = rep(s, '''    for key, v in best.items():
        v["items"] = {str(x[0]): int(x[1]) for x in con.execute(
            "SELECT item, qty FROM stock_feed WHERE as_on=? AND source=? "
            "AND received_at=?", (key[0], v["source"], v["received_at"]))}
    return best
''', '''    for key, v in best.items():
        v["items"] = _alias_fold_items(con, {str(x[0]): int(x[1]) for x in con.execute(   # S404: a renamed item reads under its old name
            "SELECT item, qty FROM stock_feed WHERE as_on=? AND source=? "
            "AND received_at=?", (key[0], v["source"], v["received_at"]))})
    return best
''', "_feed_latest")
    s = rep(s, '''        s = con.execute("SELECT qty FROM stock_snapshot WHERE as_on=? AND item=?",
                        (as_on, item)).fetchone()
''', '''        _ns = _alias_names(con, item)                          # S404: the export may carry the ticked new name
        s = con.execute("SELECT qty FROM stock_snapshot WHERE as_on=? AND item IN (%s)" % ",".join("?" * len(_ns)),
                        (as_on,) + tuple(_ns)).fetchone()
''', "reconcile")
    s = rep(s, '''        cur[0] += u; cur[1] += lo; cur[2] = max(cur[2], str(r[2] or ""))
        out[r[0]] = cur
    return out
''', '''        cur[0] += u; cur[1] += lo; cur[2] = max(cur[2], str(r[2] or ""))
        out[r[0]] = cur
    return _alias_fold_keys(con, out, _sale_key,                # S404: sales under the ticked new name count for the old item
                            lambda a, b: ([a[0] + b[0], a[1] + b[1], max(a[2], b[2])] if a else b))
''', "_sales_since")
    s = rep(s, '''        cur[0] += 1; cur[1] = max(cur[1], str(r[1] or "")); cur[2] = max(cur[2], q)
        out[k] = cur
    return out
''', '''        cur[0] += 1; cur[1] = max(cur[1], str(r[1] or "")); cur[2] = max(cur[2], q)
        out[k] = cur
    return _alias_fold_keys(con, out, _pad_norm,                # S404: purchases under the ticked new name count for the old item
                            lambda a, b: ([a[0] + b[0], max(a[1], b[1]), max(a[2], b[2])] if a else b))
''', "_purchases_since")
    s = rep(s, '''    names = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_line") if _pad_norm(r[0]) == key]
''', '''    _keys = {_pad_norm(n) for n in _alias_names(con, item)}   # S404: the ticked new name's 27-character form too
    names = [r[0] for r in con.execute("SELECT DISTINCT item FROM purchase_line") if _pad_norm(r[0]) in _keys]
''', "_item_life purchases")
    s = rep(s, '''    sk = _sale_key(item)
    sold_units, sold_bills, ret_units, ret_cns = 0, set(), 0, set()
    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "
                         "WHERE unit=? AND item_key IN (?, ?) AND business_date>=? AND business_date<=?",
                         (_unit, item, sk, since_iso, upto_iso)):
''', '''    sk = _sale_key(item)
    _sks = _alias_sale_keys(con, item)                        # S404: the ticked new name's keys too
    _skq = ",".join("?" * len(_sks))
    sold_units, sold_bills, ret_units, ret_cns = 0, set(), 0, set()
    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "
                         "WHERE unit=? AND item_key IN (%s) AND business_date>=? AND business_date<=?" % _skq,
                         (_unit,) + tuple(_sks) + (since_iso, upto_iso)):
''', "_item_life sales")
    s = rep(s, '''    for r in con.execute("SELECT as_on, qty FROM stock_snapshot WHERE item=?", (item,)):
        snaps.append((_dmy_to_iso(r[0]), int(r[1] or 0), r[0]))
    snaps.sort()
''', '''    _ns = _alias_names(con, item)                              # S404: Marg's later exports carry the ticked new name
    for r in con.execute("SELECT as_on, SUM(qty) FROM stock_snapshot WHERE item IN (%s) GROUP BY as_on" % ",".join("?" * len(_ns)), tuple(_ns)):
        snaps.append((_dmy_to_iso(r[0]), int(r[1] or 0), r[0]))
    snaps.sort()
''', "_item_life snapshots")
    s = rep(s, '''            for r in con.execute("SELECT is_return, qty_raw FROM sale_line_item WHERE unit=? AND item_key IN (?, ?) "
                                 "AND business_date>? AND business_date<=?", (_unit, item, sk, a_iso, b_iso)):
''', '''            for r in con.execute("SELECT is_return, qty_raw FROM sale_line_item WHERE unit=? AND item_key IN (%s) "
                                 "AND business_date>? AND business_date<=?" % _skq, (_unit,) + tuple(_sks) + (a_iso, b_iso)):   # S404
''', "_item_life docs")
    s = rep(s, '''    sk = _sale_key(item)
    units = 0
    bills = set()
    last = ""
    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "
                         "WHERE unit=? AND item_key IN (?, ?) AND business_date>=? AND business_date<=?",
                         (_unit, item, sk, a_iso, b_iso)):
''', '''    sk = _sale_key(item)
    _sks = _alias_sale_keys(con, item)                        # S404: the ticked new name's keys too
    units = 0
    bills = set()
    last = ""
    for r in con.execute("SELECT bill_no, is_return, qty_raw, business_date FROM sale_line_item "
                         "WHERE unit=? AND item_key IN (%s) AND business_date>=? AND business_date<=?" % ",".join("?" * len(_sks)),
                         (_unit,) + tuple(_sks) + (a_iso, b_iso)):
''', "_pursue_sales")
    # 3 -- one door for a pair answer
    s = rep(s, '''@bp.route("/api/pad/match/<int:cid>", methods=["POST"])
def api_pad_match(cid):
''', '''def match_answer(con, d, short, over, answer, note, who):
    """S404 (D619): THE ONE DOOR for an answer on a proposed pair -- the owner's hub and Darpan's 'Stock
    milaan' both land here. Append-only; only a pair the engine proposes today can be answered.
    Returns (ok, message, error_code)."""
    p = [m for m in d.get("matches") or [] if m["short"] == short and m["over"] == over]
    if not p:
        return False, "That pair is not proposed on this count.", "no_such_pair"
    con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                (d["count_id"], short, over, int(p[0]["qty"]), answer, note or None, who or "", now_iso()))
    con.commit()
    msg = {"YES": "Swap confirmed: %s billed for %s." % (over, short), "NO": "Not a swap: %s stays short." % short,
           "OPEN": "Answer taken back."}[answer]
    return True, msg, ""


@bp.route("/api/pad/match/<int:cid>", methods=["POST"])
def api_pad_match(cid):
''', "match_answer def")
    s = rep(s, '''    p = [m for m in d.get("matches") or [] if m["short"] == short and m["over"] == over]
    if not p:
        return jsonify(ok=False, error="no_such_pair", message="That pair is not proposed on this count."), 400
    con.execute("INSERT INTO stock_match (count_id, short_item, over_item, qty, answer, note, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                (d["count_id"], short, over, int(p[0]["qty"]), answer, note or None, (u or {}).get("user") or "", now_iso()))
    con.commit()
    msg = {"YES": "Swap confirmed: %s billed for %s." % (over, short), "NO": "Not a swap: %s stays short." % short,
           "OPEN": "Answer taken back."}[answer]
    return jsonify(ok=True, answer=answer, message=msg)
''', '''    ok, msg, code = match_answer(con, d, short, over, answer, note, (u or {}).get("user") or "")   # S404: the one door
    if not ok:
        return jsonify(ok=False, error=code, message=msg), 400
    return jsonify(ok=True, answer=answer, message=msg)
''', "api_pad_match body")
    # 4 -- the voucher round takes a section
    s = rep(s, '''def _voucher_rate_p(x):
''', '''def _item_section(con, x):
    """S404: the item's SECTION for a section round -- the stored map first (S313, the owner's word), the
    voucher word rule only for a name the map does not know."""
    if SECTION_MAP_OK:
        try:
            r = con.execute("SELECT section FROM stock_item_section WHERE item_key=?", (_sm.norm_key(x["item"]),)).fetchone()
            if r:
                return str(r[0])
        except Exception:                                      # noqa: BLE001
            pass
    return _voucher_section(x)[0]


def _voucher_rate_p(x):
''', "_item_section")
    s = rep(s, '''def _voucher_pending(con, d):
    """The lines the next round would carry: per item, what the Marg cleanup list now needs
    minus what earlier rounds already moved. Ordered section, family, item."""
''', '''def _voucher_pending(con, d, section=None):
    """The lines the next round would carry: per item, what the Marg cleanup list now needs
    minus what earlier rounds already moved. Ordered section, family, item.
    S404: with `section` ('Orthotics'), that section's lines only -- the rest stay for their own round."""
''', "_voucher_pending signature")
    s = rep(s, '''    for item in set(need) | set(frozen):
        x = by.get(item)
        if not x:
            continue
        ch = need.get(item, 0) - frozen.get(item, 0)
''', '''    for item in set(need) | set(frozen):
        x = by.get(item)
        if not x:
            continue
        if section and _item_section(con, x) != section:      # S404: a section round carries that section's lines only
            continue
        ch = need.get(item, 0) - frozen.get(item, 0)
''', "_voucher_pending filter")
    s = rep(s, '''def _voucher_make(con, d, user):
    """Freeze the pending lines as the next round: ISSUE and RECEIVE apart, sections kept
    together, at most `stock.voucher_lines` (6) lines a batch. Returns (round_no, lines) or (None, 0)."""
    _voucher_ensure(con)
    con.execute("BEGIN IMMEDIATE")
    try:
        pend = _voucher_pending(con, d)
''', '''def _voucher_make(con, d, user, section=None):
    """Freeze the pending lines as the next round: ISSUE and RECEIVE apart, sections kept
    together, at most `stock.voucher_lines` (6) lines a batch. Returns (round_no, lines) or (None, 0).
    S404: `section` restricts the round to that section's lines (the orthotic round)."""
    _voucher_ensure(con)
    con.execute("BEGIN IMMEDIATE")
    try:
        pend = _voucher_pending(con, d, section)
''', "_voucher_make")
    s = rep(s, '''    if con.in_transaction:
        con.commit()
    rno, n = _voucher_make(con, d, u)
''', '''    if con.in_transaction:
        con.commit()
    _sec = str((request.get_json(silent=True) or {}).get("section") or "").strip() or None   # S404: {'section': 'Orthotics'} = that section only
    if _sec and _sec not in _SECTION_ORDER:
        return jsonify(ok=False, error="bad_section", message="section must be one of: %s" % ", ".join(sorted(_SECTION_ORDER))), 400
    rno, n = _voucher_make(con, d, u, _sec)
''', "api_pad_vouchers_make")
    # 5 -- the proof carries items_ok; the hub carries the orthotic section
    s = rep(s, '''    return dict(base, state=("done" if proven else "now"), text=text, as_before=R, as_after=L, agree=agree, differ=differ,
                moved_without=moved_without, rows=rows[:40])
''', '''    return dict(base, state=("done" if proven else "now"), text=text, as_before=R, as_after=L, agree=agree, differ=differ,
                moved_without=moved_without, rows=rows[:40],
                items_ok={r_["item"]: bool(r_["ok"]) for r_ in rows})   # S404: every vouchered item's verdict, for the section
''', "_proof_state items_ok")
    s = rep(s, '''def _hub_data(con, cid):
    d = _pad_report_data(con, cid)
''', '''def _ortho_section_safe(con, d):
    """S404 (D619/D620): the orthotic section for the hub -- stockmatch.section_state; a fault here never
    takes the hub down."""
    try:
        import stockmatch                                      # noqa: PLC0415
        return stockmatch.section_state(con, d, for_owner=True)
    except Exception as e:                                     # noqa: BLE001
        return dict(ok=False, note="The orthotic section could not be read: %s" % str(e)[:160])


def _hub_data(con, cid):
    d = _pad_report_data(con, cid)
''', "_ortho_section_safe")
    s = rep(s, '''                pursue=_pursue_block(con, d, tot),   # S308 evidence + S312 the claim queue
''', '''                pursue=_pursue_block(con, d, tot),   # S308 evidence + S312 the claim queue
                ortho=_ortho_section_safe(con, d),   # S404: the orthotic section -- Darpan's answers, the orthotic round, the verdict
''', "_hub_data ortho")
    # 6 -- Amir's board: the 22 renames and the tick
    s = rep(s, '''    return dict(count_id=d["count_id"], day=d["day"], lookups=look, vouchers=vouchers, made=_voucher_state(con, d), tranches=tr,   # S301
''', '''    return dict(count_id=d["count_id"], day=d["day"], lookups=look, vouchers=vouchers, made=_voucher_state(con, d), tranches=tr,   # S301
                renames=_renames_safe(con),                    # S404 (D620): the 22 renames, one tick each
''', "_amir_board renames")
    s = rep(s, '''@bp.route("/api/pad/ortho/<int:cid>.xlsx")
def api_pad_ortho_xlsx(cid):
''', '''def _renames_safe(con):
    """S404: the rename memory for Amir's board; empty, never a fault, when the module is not there."""
    try:
        import item_alias                                      # noqa: PLC0415
        return dict(rows=item_alias.rows(con), summary=item_alias.summary(con))
    except Exception as e:                                     # noqa: BLE001
        return dict(rows=[], summary=None, note=str(e)[:120])


@bp.route("/api/pad/rename/tick", methods=["POST"])
def api_pad_rename_tick():
    """S404 (D620): Amir's 'Marg mein badal diya' on one of the 22 renames -- or clear=true to take it back
    (only until Marg's own export has shown the new name). The memory follows the tick: the section map
    (the new name inherits the section), the item spine's name table (kind 'alias'), the S229 rename task."""
    u, err = _require("checker", "maker", "viewer")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    old = str(b.get("old") or "").strip()
    if not old:
        return jsonify(ok=False, error="bad_request", message="Which name?"), 400
    con = _db()
    ensure_schema(con)
    try:
        import item_alias                                      # noqa: PLC0415
    except Exception as e:                                     # noqa: BLE001
        return jsonify(ok=False, error="unavailable", message="the rename memory is not loaded: %s" % str(e)[:80]), 503
    who = (u or {}).get("user") or ""
    if b.get("clear"):
        ok, msg, row = item_alias.untick(con, old, who)
    else:
        ok, msg, row = item_alias.tick(con, old, who)
    if not ok:
        return jsonify(ok=False, error="refused", message=msg), 400
    con.commit()
    return jsonify(ok=True, already=(msg == "already"), row=row, summary=item_alias.summary(con),
                   message=("Pehle hi ho chuka hai." if msg == "already" else
                            ("Wapas le liya." if b.get("clear") else
                             "Tick ho gaya: %s -> %s. Marg ke agle stock export mein dikhna chahiye." % (row["old_name"], row["new_name"]))))


@bp.route("/api/pad/ortho/<int:cid>.xlsx")
def api_pad_ortho_xlsx(cid):
''', "rename tick route")
    # 7 -- the snapshot door reads a ticked rename back (F-529)
    s = rep(s, '''    con.commit()
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
''', '''    con.commit()
    if _kind != "expected":                                   # S404 (D620, F-529): read a ticked rename back from Marg's own export
        try:
            import item_alias                                  # noqa: PLC0415
            item_alias.verify_closing(con, [(it.get("item") or "").strip() for it in items], as_on, None, "push_snapshot")
            con.commit()
        except Exception as _ex_ia:                            # noqa: BLE001 -- never breaks the push
            print("item_alias.verify_closing skipped: %s" % _ex_ia, file=sys.stderr)
    # S221 D-b -- "recalculate at export". Items with no rate should be rare;
''', "api_snapshot verify")
    return s


# ---------------------------------------------------------------- stock_hub.html
def build_hub(s):
    s = rep(s, '''      if(r.answer) a='<span class="said '+(r.answer==="YES"?"yes":"")+'">'+(r.answer==="YES"?"Yes — a swap":"No — not a swap")+'</span> <a class="chg" data-ans="OPEN" data-k="'+k+'">change</a>';
''', '''      if(r.answer) a='<span class="said '+(r.answer==="YES"?"yes":"")+'">'+(r.answer==="YES"?"Yes — a swap":"No — not a swap")+'</span>'+(r.answered_by==="darpan"?' <span class="sub">(Darpan)</span>':'')+' <a class="chg" data-ans="OPEN" data-k="'+k+'">change</a>';   /* S404: his answer, named */
''', "hub (Darpan) mark")
    s = rep(s, '''  document.getElementById("body").innerHTML=h;
  document.getElementById("foot").innerHTML='<a class="b" href="'+esc(L.count)+'">Start a new count</a>';
}
''', '''  h+=orthoCard(d.ortho);   // S404: the orthotic section -- Darpan's answers, the orthotic round, the verdict
  document.getElementById("body").innerHTML=h;
  document.getElementById("foot").innerHTML='<a class="b" href="'+esc(L.count)+'">Start a new count</a>';
}

/* ---- S404_ORTHO_STOCK_CLOSE (26-Sep-2026, D619/D620): the orthotic section of this round. Darpan answers the
   orthotic pairs and lines on his own page (Stock milaan); this card shows his answers beside each open orthotic
   line with a one-tap change, the orthotic voucher round (made here or by itself when he is all done), and the
   four conditions of "Orthotics section: CLOSED on <date>". Nothing else on the hub moves. ---- */
function orthoCard(O){
  if(!O) return '';
  if(O.ok===false) return '<section class="step wait" id="stepO"><div class="n">O</div><div><h2>Orthotics section</h2><div class="lead">'+esc(O.note||'')+'</div></div></section>';
  const st=O.closed?'done':'now', P=O.progress, V=O.vouchers, R=O.renames||{};
  const conds=O.conds.map(c=>'<div class="sub">'+(c.ok?'\\u2713 ':'\\u25cb ')+esc(c.en)+'</div>').join('');
  let body='<div class="figs"><span>Darpan: <b>'+esc(P.en)+'</b></span><span>Pairs <b>'+O.pairs.length+'</b></span><span>Lines open <b>'+O.open_lines+'</b></span>'
    +'<span>Not yet on a voucher <b>'+V.pending+'</b></span><span>Orthotic vouchers entered <b>'+(V.batches.length-V.not_entered)+' of '+V.batches.length+'</b></span>'
    +'<span>Renames seen in Marg <b>'+(R.verified||0)+' of '+(R.total||0)+'</b>'+(R.amber?' \\u00b7 <span class="err">'+R.amber+' ticked, not yet seen</span>':'')+'</span></div>'
    +conds
    +'<div class="links"><button class="b main" id="omake"'+(V.pending?'':' disabled')+'>Make the orthotic round ('+V.pending+')</button><a class="b" href="/finance/stockmatch">Darpan\\'s page \\u2014 Stock milaan</a><a class="b" href="'+esc(D.links.amir)+'#renames">The 22 renames \\u2014 Amir\\'s board</a></div><span class="msg" id="omsg"></span>';
  const L=(O.lines||[]).filter(l=>l.open);
  if(L.length){
    body+='<div class="sect">Orthotic lines still open \\u2014 Darpan\\'s reason, your one-tap change</div><div class="tbl"><table class="m"><colgroup><col style="width:24%"><col style="width:7%"><col style="width:7%"><col style="width:8%"><col style="width:18%"><col style="width:12%"><col style="width:24%"></colgroup><thead><tr><th>Item</th><th class="num">Marg</th><th class="num">Shelf</th><th class="num">Left</th><th>Darpan says</th><th>Your word</th><th>Change</th></tr></thead><tbody>';
    L.forEach(l=>{
      const chips=l.reasons.map(r=>'<button class="b" data-oreason="'+r.key+'" data-did="'+l.diff_id+'"'+(l.cause===r.key?' disabled':'')+'>'+esc(r.en)+'</button>').join('');
      body+='<tr class="'+(l.answered?'yes':'')+'"><td class="it" data-l="Item">'+esc(l.item)+'</td><td class="num" data-l="Marg">'+l.marg+'</td><td class="num" data-l="Shelf">'+l.counted+'</td><td class="num" data-l="Left">'+l.rem+(l.swapped?' <span class="sub">(swap '+l.swapped+')</span>':'')+'</td>'
        +'<td data-l="Darpan says">'+(l.reasoned?esc((l.cause_by==='darpan'?'Darpan: ':(l.cause_by?l.cause_by+': ':''))+l.cause_en)+(l.cause_at_text?' <span class="sub">'+esc(l.cause_at_text)+'</span>':''):'<span class="sub">\\u2014</span>')+'</td>'
        +'<td data-l="Your word">'+(l.word?esc(l.word):'<span class="sub">\\u2014</span>')+'</td><td data-l="Change"><div class="ans">'+chips+'</div></td></tr>';
    });
    body+='</tbody></table></div>';
  }
  const amber=(O.rename_rows||[]).filter(r=>r.state==='amber');
  if(amber.length) body+='<div class="sub">Ticked by Amir but not yet seen in Marg\\'s stock export (<i>Marg mein abhi dikha nahi</i>): '+amber.map(r=>esc(r.new_name)).join(', ')+'</div>';
  return step("O",st,"Orthotics section",'<b>'+esc(O.verdict_en)+'</b>',body);
}
''', "hub orthoCard")
    s = rep(s, '''  const nx=t.closest("button[data-next]");
  if(nx && !BUSY){ BUSY=true; document.getElementById("tmsg").textContent="Cutting…";
''', '''  const orz=t.closest("button[data-oreason]");   /* S404: the owner's one-tap change of Darpan's reason */
  if(orz && !BUSY){ BUSY=true;
    const j=await post("/finance/stockmatch/api/reason?count="+D.count_id,{diff_id:+orz.getAttribute("data-did"),reason:orz.getAttribute("data-oreason")}); BUSY=false;
    say("omsg", (j&&j.ok)?{ok:true,message:(j.already?"Already recorded.":"Recorded: "+(j.saved?j.saved.item+" \\u2014 "+j.saved.en:""))}:j); if(j&&j.ok){ setTimeout(load, 500); } return; }
  if(t.id==="omake" && !BUSY){ BUSY=true; t.disabled=true;   /* S404: the orthotic round only */
    const j=await post(BASE+"/api/pad/vouchers/"+D.count_id+"/make",{section:"Orthotics"}); BUSY=false;
    say("omsg", j); if(j&&j.ok){ setTimeout(load, 700); } return; }
  const nx=t.closest("button[data-next]");
  if(nx && !BUSY){ BUSY=true; document.getElementById("tmsg").textContent="Cutting…";
''', "hub click handlers")
    return s


# ---------------------------------------------------------------- stock_amir.html
def build_amir(s):
    s = rep(s, '''    +VM.rounds.slice().reverse().map(r=>'<h3 style="font-size:15px;margin:14px 0 2px">Round '+r.round_no+' — '+r.entered+' of '+r.total+' entered'+(r.closed?' · closed':'')+'</h3>''',
            '''    +VM.rounds.slice().reverse().map(r=>'<h3 style="font-size:15px;margin:14px 0 2px">Round '+r.round_no+(r.batches.every(b=>(b.sections||[]).length===1&&b.sections[0]==="Orthotics")?' — orthotics':'')+' — '+r.entered+' of '+r.total+' entered'+(r.closed?' · closed':'')+'</h3>''',
            "amir round label")
    s = rep(s, '''  document.getElementById("body").innerHTML=h;
  const hh=location.hash.slice(1);''', '''  // 6 -- S404 (D620): the 22 renames -- old name -> new name, one tick each: "Marg mein badal diya"
  const RN=(d.renames||{}).rows||[], RS=(d.renames||{}).summary;
  if(RN.length) h+='<div class="card" id="renames"><h2><span class="n">6</span>Naam badlo ('+RN.length+')</h2><div class="hi">Marg में इन '+RN.length+' नामों को ठीक वैसे ही बदलें जैसा लिखा है — फिर टिक करें</div>'
    +'<div class="lead">Change each item\\'s name in Marg to the NEW name exactly as written (the size moves forward; every name fits Marg\\'s 29 characters). Tick each one as you change it. The server reads Marg\\'s next stock export by itself: <b>'+(RS?RS.verified:0)+' of '+RN.length+'</b> seen in Marg so far'+(RS&&RS.amber?' · <span class="err">'+RS.amber+' ticked but not yet seen — Marg mein abhi dikha nahi</span>':'')+'.</div>'
    +RN.map(r=>'<div class="row'+(r.state==="verified"?' done':'')+'"><div><div class="it">'+esc(r.old_name)+'</div><div class="it" style="color:var(--accent)">→ '+esc(r.new_name)+'</div><div class="q">'+esc(r.family||'')+' · '+esc(r.state_hi)+(r.done_by?' · '+esc(r.done_by)+' '+esc((r.done_at||'').slice(0,16).replace('T',' ')):'')+(r.verified_as_on?' · Marg export '+esc(r.verified_as_on):'')+'</div></div>'
      +'<div class="r">'+(r.state==="planned"?'<button class="b main" data-rtick="'+esc(r.old_name)+'">Marg mein badal diya</button>':(r.state==="verified"?'✓':'<span class="'+(r.state==="amber"?'err':'msg')+'">'+(r.state==="amber"?'abhi dikha nahi':'✓ tick')+'</span> <button class="tg" data-runtick="'+esc(r.old_name)+'">undo</button>'))+'</div></div>').join("")
    +'<div class="msg" id="rmsg"></div></div>';
  document.getElementById("body").innerHTML=h;
  const hh=location.hash.slice(1);''', "amir renames card")
    s = rep(s, '''  const rt=e.target.closest("button[data-ret]"); if(rt){''', '''  const rk=e.target.closest("button[data-rtick],button[data-runtick]"); if(rk){ const m=document.getElementById("rmsg"); m.textContent="…";   // S404
    const r=await fetch(BASE+"/api/pad/rename/tick",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({old:rk.dataset.rtick||rk.dataset.runtick,clear:!!rk.dataset.runtick})}).catch(()=>null);
    const j=r?await r.json().catch(()=>null):null; m.textContent=(j&&j.message)||"the server did not answer"; if(j&&j.ok) setTimeout(load, 700); return; }
  const rt=e.target.closest("button[data-ret]"); if(rt){''', "amir tick handler")
    return s


# ---------------------------------------------------------------- section_map.py
def build_section_map(s):
    s = rep(s, '''def items_in(con, section):
    """THE WHOLE POINT, once the rungs above this one are built: the list of
    items a section-scoped round would carry. Nothing calls it yet."""
    ensure(con)
    return [str(r[0]) for r in con.execute(
        "SELECT item FROM stock_item_section WHERE section=? ORDER BY item", (section,))]
''', '''def items_in(con, section):
    """THE WHOLE POINT, once the rungs above this one are built: the list of
    items a section-scoped round would carry. Nothing calls it yet."""
    ensure(con)
    return [str(r[0]) for r in con.execute(
        "SELECT item FROM stock_item_section WHERE section=? ORDER BY item", (section,))]


def inherit(con, old_item, new_item, by_user="", ts=None):
    """S404 (D620): a renamed item keeps its section. Called when Amir ticks a rename
    (item_alias.tick): the NEW name's row is written from the OLD name's row -- source
    'rename', seeded_as = the section it inherited -- so the map knows the new spelling
    the moment Marg starts printing it. An owner's word on the new name is never
    overwritten. Returns (ok, message)."""
    ensure(con)
    ts = ts or now_iso()
    ko, kn = norm_key(old_item), norm_key(new_item)
    if not ko or not kn or ko == kn:
        return False, "no rename"
    row = con.execute("SELECT section FROM stock_item_section WHERE item_key=?", (ko,)).fetchone()
    if row is None:
        return False, "the old name is not in the map"
    sec = str(row[0])
    have = con.execute("SELECT section, source FROM stock_item_section WHERE item_key=?", (kn,)).fetchone()
    if have is None:
        con.execute("INSERT INTO stock_item_section (item_key, item, section, source, "
                    "seeded_as, by_user, at) VALUES (?,?,?,'rename',?,?,?)",
                    (kn, str(new_item), sec, sec, by_user, ts))
        return True, "inherited %s" % sec
    if str(have[1]) == "owner" or str(have[0]) == sec:
        return True, "already %s" % have[0]
    con.execute("UPDATE stock_item_section SET item=?, section=?, source='rename', seeded_as=?, "
                "by_user=?, at=? WHERE item_key=?", (str(new_item), sec, sec, by_user, ts, kn))
    return True, "moved to %s" % sec
''', "section_map inherit")
    return s


# ---------------------------------------------------------------- spine/spine_build.py
def build_spine(s):
    s = rep(s, '''* --acceptance: stock must equal Marg on EVERY item on EVERY checkable full closing (reference s8 item 4).
  Without it, a new difference is recorded as a dated finding (sp_finding) and does not block, because an
  unexported Marg voucher is a fact about Marg, not a fault in the spine.
"""
''', '''* --acceptance: stock must equal Marg on EVERY item on EVERY checkable full closing (reference s8 item 4).
  Without it, a new difference is recorded as a dated finding (sp_finding) and does not block, because an
  unexported Marg voucher is a fact about Marg, not a fault in the spine.
* S404 (D620): a rename Amir has TICKED in finance.db's marg_item_rename (read-only, the same door as gate
  check 5) is an alias new -> old at the 20-character clip: the renamed item stays ONE item under the old
  name's key, and the new name is recorded in sp_alias (kind 'rename'). An unticked rename maps nothing.
"""
''', "spine docstring")
    s = rep(s, '''

class Gate:
''', '''

def rename_aliases(finance_db):
    """S404 (D620): the rename memory -- every rename Amir has TICKED, as a 20-character alias new -> old,
    read from finance.db READ-ONLY. One item, two names, never two items."""
    out = {}
    if not finance_db:
        return out
    try:
        con = sqlite3.connect("file:%s?mode=ro" % finance_db, uri=True)
        if con.execute("SELECT 1 FROM sqlite_master WHERE name='marg_item_rename'").fetchone():
            for old, new in con.execute("SELECT old_name, new_name FROM marg_item_rename WHERE done_at IS NOT NULL"):
                if K(new) != K(old):
                    out[K(new)] = K(old)
        con.close()
    except sqlite3.Error:
        return {}
    return out


class Gate:
''', "spine rename_aliases")
    s = rep(s, '''    alias = {a: v["to"] for a, v in rules.get("aliases", {}).items()}
    fam = rules.get("families", {})
''', '''    alias = {a: v["to"] for a, v in rules.get("aliases", {}).items()}
    ren = rename_aliases(finance_db)                             # S404: ticked renames, new clip -> old clip
    for a, t in ren.items():
        alias.setdefault(a, t)
    fam = rules.get("families", {})
''', "spine build alias")
    s = rep(s, '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias)
''', '''                facts=facts, whole=whole, Z=Z, checkable=checkable, pending=pending, alias=alias, rename_alias=ren)
''', "spine build return")
    s = rep(s, '''    con.executemany("INSERT INTO sp_alias VALUES (?,?,?,?)", [(a, v["to"], v["kind"], v["source"]) for a, v in rules.get("aliases", {}).items()])
''', '''    con.executemany("INSERT INTO sp_alias VALUES (?,?,?,?)", [(a, v["to"], v["kind"], v["source"]) for a, v in rules.get("aliases", {}).items()])
    con.executemany("INSERT OR IGNORE INTO sp_alias VALUES (?,?,?,?)",                   # S404: the ticked renames
                    [(a, t, "rename", "marg_item_rename -- ticked by Amir (S404, D620)") for a, t in (B.get("rename_alias") or {}).items()])
''', "spine write alias")
    return s


# ---------------------------------------------------------------- marg_ingest/marg_take.py
def build_take(s):
    s = rep(s, '''# ------------------------------------------------------------------ the door
def take(raw, name="", source="manual", db=None, archive=None):
''', '''def _rename_verify(con, path, md5, stamp=""):
    """S404 (D620, F-529 -- never assume a rename happened): a VERIFIED closing-stock export has just been
    taken. Read its item names with the spine's certified reader and let the rename memory (item_alias,
    beside finance_app) mark every ticked rename the export now carries -- or count one more export that
    does not (an export captured before the tick counts for nothing). Fail-soft: the door never refuses
    a file because of this."""
    fin = os.path.join(os.path.dirname(HERE), "finance")
    try:
        for p in (fin, os.path.join(fin, "spine")):
            if p not in sys.path:
                sys.path.insert(0, p)
        import item_alias                                        # noqa: PLC0415
        import marg_read                                         # noqa: PLC0415
        fam, R, _m = marg_read.read_file(path)
        if fam != "STOCK_CLOSING" or R is None:
            return
        names = [i["name"] for i in (R.data.get("items") or []) if i.get("name")]
        as_on = R.data.get("as_on") or ""
        cap = None
        if re.match(r"^\\d{8}-\\d{6}$", stamp or ""):
            cap = "%s-%s-%sT%s:%s:%s" % (stamp[0:4], stamp[4:6], stamp[6:8], stamp[9:11], stamp[11:13], stamp[13:15])
        if names and as_on:
            item_alias.verify_closing(con, names, as_on, md5, "marg_take", captured=cap)
            con.commit()
    except Exception as e:                                       # noqa: BLE001
        print("marg_take: rename verification skipped (%s)" % str(e)[:120], file=sys.stderr)


# ------------------------------------------------------------------ the door
def take(raw, name="", source="manual", db=None, archive=None):
''', "marg_take _rename_verify")
    s = rep(s, '''            kept = 0
            if dest and os.path.exists(dest):
''', '''            if typ == "STOCK_CLOSING" and verdict == "VERIFIED":                    # S404 (D620, F-529)
                _rename_verify(con, dest if (dest and os.path.exists(dest)) else local, md5, stamp)
            kept = 0
            if dest and os.path.exists(dest):
''', "marg_take hook")
    return s


# ---------------------------------------------------------------- finance_app.py
def build_finance_app(s):
    s = rep(s, '''    if path == "/finance/salecheck" or path.startswith("/finance/salecheck/"):
        return "salecheck"   # S400: Bhati checks the pharmacy days (owner, 25-Sep-2026, D616). No medical row for him.
''', '''    if path == "/finance/salecheck" or path.startswith("/finance/salecheck/"):
        return "salecheck"   # S400: Bhati checks the pharmacy days (owner, 25-Sep-2026, D616). No medical row for him.
    if path == "/finance/stockmatch" or path.startswith("/finance/stockmatch/"):
        return "stockmatch"  # S404: Darpan's 'Stock milaan' -- the orthotic matches of the count (owner, 26-Sep-2026, D619).
''', "finance_app _unit_for_path")
    s = rep(s, '''# --- S400_MEDICAL_SALE_CHECK end ---


if __name__ == "__main__":
''', '''# --- S400_MEDICAL_SALE_CHECK end ---


# --- S404_ORTHO_STOCK_CLOSE begin -- Darpan's 'Stock milaan': the orthotic matches of the 06-Sep count (owner, 26-Sep-2026, D619) ---
# Its own unit 'stockmatch' (maker = darpan, checker = the owner). Reads the stock hub's own report and answers
# through the same doors the owner's hub uses (stock_app.match_answer, stock_diff.cause). GUARDED (S209):
# a fault inside the module is printed and every other page keeps serving.
try:
    import stockmatch                                          # noqa: E402
    stockmatch.init(app, db, require, unit=UNIT)
except Exception as _ex_sm:                                    # noqa: BLE001
    print("stockmatch NOT mounted: %s" % _ex_sm, file=sys.stderr)
# --- S404_ORTHO_STOCK_CLOSE end ---


if __name__ == "__main__":
''', "finance_app mount")
    return s


# ---------------------------------------------------------------- portal.py
def build_portal(s):
    s = rep(s, '''     "url": "/finance/salecheck",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', '''     "url": "/finance/salecheck",
     "roles": ["doctor"]},
    {"icon": "\\U0001F9B5", "name": "Stock milaan",
     # S404 NEW (owner, 26-Sep-2026, D619). Darpan closes the ORTHOTIC section of the 06-Sep stock check on his
     # phone or the PC: Adla-badli? (Haan / Nahi per proposed swap) and Kam kyun? (one reason chip per line).
     # Its own server unit ('stockmatch': darpan maker, the doctor checker). Granted by name in tile_grants.json
     # v27 to darpan; the doctor holds it by role.
     "desc": "Stock check \\u2014 orthotics ka milaan",
     "live": True,
     "url": "/finance/stockmatch",
     "roles": ["doctor"]},
    {"icon": "\\U0001F3EA", "name": "Daily Sale",
''', "portal tile")
    s = rep(s, '''    "Medical sale check": "Money & Accounts",
''', '''    "Medical sale check": "Money & Accounts",
    "Stock milaan": "Money & Accounts",
''', "portal section")
    return s


# ---------------------------------------------------------------- tile_grants.json
def build_grants(raw):
    d = json.loads(raw)
    if json.dumps(d, indent=2, ensure_ascii=False) != raw:          # the live file has no trailing newline
        sys.exit("REFUSED: tile_grants.json does not round-trip through json.dumps(indent=2) -- build by hand")
    if d.get("version") != 26:
        sys.exit("REFUSED: tile_grants.json is v%r, expected v26" % d.get("version"))
    ex = d["users"].setdefault("darpan", {}).setdefault("extra", [])
    if "Stock milaan" not in ex:
        ex.append("Stock milaan")
    d["version"] = 27
    d["_note"] += (" | v27 (S404, 26-Sep-2026): the NEW tile 'Stock milaan' (/finance/stockmatch) to darpan -- he closes the "
                   "orthotic section of the 06-Sep stock check from his phone or the PC (Adla-badli? Haan / Nahi per pair; "
                   "Kam kyun? one reason chip per line); the doctor holds it by role. Its gate is a NEW server unit 'stockmatch' "
                   "(darpan maker, the doctor checker; nobody else); nothing else in this file moves.")
    return json.dumps(d, indent=2, ensure_ascii=False)


def main(argv):
    a = dict(zip(argv[1::2], argv[2::2]))
    fin, por, mrg, out = a.get("--finance"), a.get("--portal"), a.get("--marg"), a.get("--out")
    if not (fin and por and mrg and out):
        print(__doc__)
        return 2
    os.makedirs(out, exist_ok=True)
    built = {
        "stock_app.py": build_stock_app(load(os.path.join(fin, "stock_app.py"), "stock_app.py")),
        "stock_hub.html": build_hub(load(os.path.join(fin, "stock_hub.html"), "stock_hub.html")),
        "stock_amir.html": build_amir(load(os.path.join(fin, "stock_amir.html"), "stock_amir.html")),
        "section_map.py": build_section_map(load(os.path.join(fin, "section_map.py"), "section_map.py")),
        "spine_build.py": build_spine(load(os.path.join(fin, "spine", "spine_build.py"), "spine_build.py")),
        "marg_take.py": build_take(load(os.path.join(mrg, "marg_take.py"), "marg_take.py")),
        "finance_app.py": build_finance_app(load(os.path.join(fin, "finance_app.py"), "finance_app.py")),
        "portal.py": build_portal(load(os.path.join(por, "portal.py"), "portal.py")),
        "tile_grants.json": build_grants(load(os.path.join(por, "tile_grants.json"), "tile_grants.json")),
    }
    for name, text in built.items():
        data = text.encode("utf-8")
        open(os.path.join(out, name), "wb").write(data)
        print("%s  %s" % (md5(data), name))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
