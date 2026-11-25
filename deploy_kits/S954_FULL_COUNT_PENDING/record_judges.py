#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  record_judges.py  ·  v1.0  ·  kit S952_RECORD_JUDGES  ·  Session 519 (Sanjeevni)  ·  25-Nov-2026  ·  D1065
#
#  KIT 2 OF THE STOCK OF RECORD -- the owner's "YES" (25-Nov 12:25 IST) to the four-part fix of the TYRO BR false loss, for every item:
#    1. every delivery matched to Marg's bill by its OWN SCANNED BILL, never by taps (the rule lives in stock_figure.carried, rule 0 --
#       this file holds the one-off and the every-pass REPAIR of matches made before it: scan_repair());
#    2. every count judged against THE ONE RECORD -- Marg's figure at the count's moment (the stock of record's Marg side carried back by
#       the spine's own movements) + the deliveries truly on the shelf and not yet in Marg -- never against an old count carried forward
#       (his 22-Nov ruling); each difference carries its cause in plain words (judge());
#    3. every count since 18-11 judged again by the same rule (REJUDGE_FROM); a loss line the re-judgment does not bear out is WITHDRAWN (void_at / void_why,
#       never deleted) (rejudge_all());
#    4. a daily self-check, READ ONLY, that names any item where the pages disagree or a stored judgment no longer stands (self_check()).
#
#  THE RULES (D1065; the design S952_RECORD_JUDGES_DESIGN.md, S518):
#    PAIRING (scan_repair). An order whose tied scan is linked to a Marg bill is answered by THAT bill only. For each order line of such an
#      order: the linked bill (as keyed in the spine) that carries a matching line of the medicine (stock_figure's own match) is its bill.
#      * the line holds another bill -> re-answered from its scanned bill (billed_* rewritten; supplied too when Marg wrote it);
#      * the line holds a bill no linked bill of its order carries, and THAT bill line is another line's scanned bill -> the bill is taken
#        off it (positive evidence only, F-1662); when Marg itself had marked the line supplied, the line becomes 'missing' (it never came on
#        its own order's bill); a person's own tap is never changed;
#      * a line reception marked MISSING never holds a bill (it never came) -> the bill is taken off;
#      * anything no rule can answer is LISTED, never guessed (two lines of one order on one bill line; two orders claiming one bill line;
#        a held bill nobody else's scan claims).
#      Every change: an audit row in purchase_audit (line_repaired_s952 / line_unbilled_s952 / line_missing_s952) and its before / after in
#      s952_line_undo (the undo reads it). Idempotent: a second pass finds nothing to do.
#    JUDGING (judge). D = the count's day, T = its moment.
#      * the Marg figure at the END of a day d = THE RECORD'S OWN MARG RULE applied to the print standing then: the newest closing print for d
#        or before (stock_figure.marg: the morning rule, a split's share, carried by the spine's movements to d) + the bills that print could
#        not hold (first seen in Amir's purchase export after its print day -- the record's "certain" late bills). The record's figure TODAY less
#        the movements since is NOT used: a write-off keyed in Marg later (a voucher, a correction) would hide the loss it wrote off (ZIBON
#        EXTRA, 18-11: Marg 359, counted 206; Marg corrected to 159 on 21/22-11);
#      * a count placed to its last sale bill N (Count now) whose day's sales are in: Marg at the end of D + D's sales billed after N;
#        an evening count (at or after count.evening_hour) whose day's sales are in: Marg at the end of D; any other count: the START of D
#        (Marg at the end of D-1) -- the moment as S928 / S934 defined it;
#      * + every delivery ON THE SHELF AT T and NOT IN MARG at that figure: arrived (tap / scan moment) at or before T and its Marg bill dated
#        after the figure's day or not keyed at all (within WAIT_DAYS of T; an older unkeyed tap is named, not counted) -- by the scanned bill's
#        quantity when it speaks (S928), else the tap;
#      * - every delivery IN MARG at that figure but NOT ON THE SHELF AT T: its Marg bill dated on or before the figure's day and its arrival
#        (tap / scan moment) after T;
#      * a purchase dated the figure's day with no arrival moment known: the gap is shown, never a loss (S934's rule, kept);
#      * an older loss already booked (a loss line, not withdrawn) and not yet written off in Marg (Marg's figure has not dropped by more than
#        the spine's movements explain since) is still inside Marg's figure: a short of that size is NOT a new loss (booked once, never twice);
#      * the words: matches Marg · x below Marg, within the allowance · x below Marg -- a loss since the last count · below Marg by about a
#        delivery (bill ...) -- was it on the shelf? · Marg still holds the older loss of dd-mm not yet written off -- not a new loss ·
#        x more than Marg -- noted, never a loss.
#      A family figure (two sizes under one Marg key) is not judged (basis 'approx'), as before. An item the record does not hold falls back
#      to stock_figure.expect_for_point's Marg branch (basis 'marg').
#    THE SWITCH: setting count.judge_by_record ('1' default; '0' puts every judgment back on stock_figure.expect_for_point exactly as before).
#
#  WRITES: purchase_order_line (scan_repair only), purchase_audit, s952_line_undo, stock_point (rejudge_all: expected_units, gap_units, basis,
#  judge_words), stock_watch_loss_line (void_at / void_why, gap_units, mrp_p), s952_point_undo, audit_log. READS everything else.
#  English; strips:tabs by the item's pack; no patient data; no dialog anywhere.
import datetime as dt
import json
import os
import re
import sqlite3
import sys

VERSION = "1.1"                                             # v1.1 S954: the full count's shortfalls read as Amir closed them
KIT = "S954_FULL_COUNT_PENDING"
HERE = os.path.dirname(os.path.abspath(__file__))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
TOL = 0.5
BACK_DAYS = 7                                               # a scanned bill dated this long before its order, or
AHEAD_DAYS = 21                                             # this long after it, never moves an answer (listed)
LATE_FROM = "2026-10-15"                                    # first_seen_day up to here is the purchase register's back-fill, not a keying day
REJUDGE_FROM = "2026-11-18"                                 # counts before this were judged while Marg still held the 06-Sep full count's
                                                            # shortfall (Amir's vouchers of 15-10) and the register's first-seen days were
                                                            # back-filled: not judged again (the design's 16 counts since 18-11 are)
WAIT_DAYS = 14                                              # an unkeyed delivery older than this before the count is named, never counted
SWITCH = "count.judge_by_record"

DDL = (
    "CREATE TABLE IF NOT EXISTS s952_line_undo (id INTEGER PRIMARY KEY AUTOINCREMENT, line_id INTEGER NOT NULL, at TEXT NOT NULL, action TEXT NOT NULL,"
    " before_json TEXT NOT NULL, after_json TEXT NOT NULL, why TEXT, undone_at TEXT)",
    "CREATE TABLE IF NOT EXISTS s952_point_undo (id INTEGER PRIMARY KEY AUTOINCREMENT, point_id INTEGER, loss_id INTEGER, at TEXT NOT NULL, action TEXT NOT NULL,"
    " before_json TEXT NOT NULL, after_json TEXT NOT NULL, undone_at TEXT)",
)


def _sf():
    import stock_figure                                       # noqa: PLC0415 -- beside this file
    return stock_figure


def _sw():
    import stock_watch                                        # noqa: PLC0415
    return stock_watch


def _sr():
    import stock_record                                       # noqa: PLC0415
    return stock_record


def now_iso():
    return dt.datetime.now(IST).replace(microsecond=0, tzinfo=None).isoformat()


def today():
    return dt.datetime.now(IST).date()


def _has(con, t):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
    except sqlite3.Error:
        return False


def _cols(con, t):
    try:
        return {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}
    except sqlite3.Error:
        return set()


def ensure(con):
    for d in DDL:
        con.execute(d)
    if _has(con, "stock_point") and "judge_words" not in _cols(con, "stock_point"):
        con.execute("ALTER TABLE stock_point ADD COLUMN judge_words TEXT")


def switch_on(con):
    """count.judge_by_record: on unless set to 0 / off / no."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (SWITCH,)).fetchone()
    except sqlite3.Error:
        return True
    return not (r and str(r[0] or "").strip().lower() in ("0", "off", "no", "false"))


def pair_on(con):
    """arrival.pair_by_scan: on unless set to 0 / off / no -- rule 0 (stock_figure) and the scan repair."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key='arrival.pair_by_scan'").fetchone()
    except sqlite3.Error:
        return True
    return not (r and str(r[0] or "").strip().lower() in ("0", "off", "no", "false"))


def set_switches(con, on):
    """Both switches at once ('1' / '0'), committed -- the install turns them on, the undo off FIRST (so no page re-applies a repair meanwhile)."""
    v = "1" if on else "0"
    for k in (SWITCH, "arrival.pair_by_scan"):
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)", (k, v, "S952: written by record_judges (install / undo)"))
    con.commit()


def dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s" % (s[8:10], s[5:7]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


def st(units, pack, signed=False):
    try:
        return _sr().st(units, pack, signed)
    except Exception:                                         # noqa: BLE001
        return str(int(round(float(units or 0))))


def _day_before(d):
    return (dt.date.fromisoformat(str(d)[:10]) - dt.timedelta(days=1)).isoformat()


def _audit_p(con, who, action, ref, detail):
    """An audit row in purchase_audit, as purchase_app writes it (the order book's own history)."""
    try:
        con.execute("INSERT INTO purchase_audit (at, who, action, ref, detail) VALUES (?,?,?,?,?)",
                    (now_iso(), who, action, str(ref), json.dumps(detail, sort_keys=True, default=str)))
    except sqlite3.Error:
        pass


def _audit_w(con, action, after, who, row_id=0):
    try:
        _sw()._audit(con, action, after, who, row_id)
    except Exception:                                         # noqa: BLE001
        pass


# ================================================================================================================ 1 · THE PAIRING REPAIR
LINE_FIELDS = ("billed_qty", "billed_bill_no", "billed_date", "billed_units", "supplied", "short", "missing", "arrived_by", "arrived_at", "detected_at")


def _line_row(con, lid):
    r = con.execute("SELECT %s FROM purchase_order_line WHERE id=?" % ", ".join(LINE_FIELDS), (lid,)).fetchone()
    return dict(zip(LINE_FIELDS, r)) if r else None


def _hit_on_bill(con, sp, ln, bill, date, supkey=None):
    """What bill `bill` (dated `date`) carries of the order line by stock_figure's own match (rule a on that bill number) -- dict(qty, free,
    units, seq, supkey, date, packing) -- or None when no matching line of that bill (that dealer, that date) carries it."""
    SF = _sf()
    ctx = SF.Ctx(con, sp)
    h = SF.carried(con, sp, dict(line_id=ln["id"], item=ln["item"], vendor=ln["vendor"], order_at=ln["order_at"], billed_bill_no=bill, billed_date=date), ctx)
    if not h or h.get("how") != "a" or h.get("units") is None:
        return None
    if str(h.get("date") or "")[:10] != str(date or "")[:10]:
        return None
    if supkey and str(h.get("supkey") or "") != str(supkey):
        return None
    return h


def plan_repair(con, sp):
    """READ ONLY: what scan_repair would do -- dict(actions=[...], listed=[...]). Each action: dict(line_id, kind 'repair' | 'unbill' |
    'unbill_missing' | 'clear_missing', item, order_id, old (bill, date, qty), new (bill, date, qty, units) or None, why)."""
    SF, SW = _sf(), _sw()
    ctx = SF.Ctx(con, sp)
    SB = SF._s952_scan_bills(ctx) or {}
    lines = []
    for r in con.execute("SELECT l.id, l.order_id, l.item, l.packs, l.pack_size, l.supplied, l.missing, l.billed_bill_no, l.billed_date, l.billed_qty, l.arrived_by, "
                         "o.vendor, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.status IN ('sent','received') ORDER BY l.id"):
        lines.append(dict(id=int(r[0]), order_id=int(r[1]), item=r[2], packs=int(r[3] or 0), pack_size=int(r[4] or 1), supplied=r[5], missing=int(r[6] or 0),
                          bill=SF._bill(r[7]), bill_raw=r[7] or "", bill_date=str(r[8] or "")[:10], billed_qty=r[9], arrived_by=str(r[10] or ""),
                          vendor=r[11] or "", order_at=str(r[12] or "")))
    actions, listed = [], []
    cand = {}                                                 # line id -> its scanned bill's hit
    for ln in lines:
        if ln["missing"]:
            continue
        keyed = SF._s952_keyed(ctx, sp, ln["order_id"])
        if not keyed:
            continue                                          # no link, or linked and not in the spine yet: Amir's entry is on its way
        hits = []
        for (sk, b, d) in sorted(keyed, key=lambda x: (x[2], x[1], x[0])):
            h = _hit_on_bill(con, sp, ln, b, d, sk)
            if h is not None and not any((x["supkey"], SF._bill(x["bill"]), x["date"]) == (h["supkey"], SF._bill(h["bill"]), h["date"]) for x in hits):
                hits.append(h)
        if hits:
            cur = [h for h in hits if SF._bill(h["bill"]) == ln["bill"]]
            h = cur[0] if cur else hits[0]
            try:
                od = dt.date.fromisoformat(ln["order_at"][:10])
                far = not (od - dt.timedelta(days=BACK_DAYS) <= dt.date.fromisoformat(h["date"]) <= od + dt.timedelta(days=AHEAD_DAYS))
            except ValueError:
                far = True
            if far and not cur:                               # a scanned bill far from its order's day: not trusted to move an answer
                listed.append(dict(line_id=ln["id"], item=ln["item"], order_id=ln["order_id"], why="its order's scanned bill %s is dated %s, far from the order of %s -- not changed" % (
                    h["bill"], dmy(h["date"]), dmy(ln["order_at"]))))
                continue
            cand[ln["id"]] = h
    # one bill line, one order line (rule b): claims by the bill line's identity
    claims = {}
    for lid, h in cand.items():
        claims.setdefault((h["supkey"], SF._bill(h["bill"]), h["date"], str(h.get("seq"))), []).append(lid)
    by_id = {ln["id"]: ln for ln in lines}
    owner = {}
    for key, lids in claims.items():
        if len(lids) == 1:
            owner[key] = lids[0]
            continue
        orders = {by_id[x]["order_id"] for x in lids}
        if len(orders) == 1:                                  # the same medicine twice on one order: the first line takes the bill line
            first = min(lids)
            owner[key] = first
            for x in lids:
                if x != first:
                    listed.append(dict(line_id=x, item=by_id[x]["item"], order_id=by_id[x]["order_id"], why="the same medicine twice on order %d; bill %s answers line %d" % (
                        by_id[x]["order_id"], key[1], first)))
                    cand.pop(x, None)
        else:                                                 # two orders' scans claim one bill line: nobody is changed, both are listed
            for x in lids:
                listed.append(dict(line_id=x, item=by_id[x]["item"], order_id=by_id[x]["order_id"], why="bill %s (%s) is the scanned bill of orders %s -- not changed" % (
                    key[1], dmy(key[2]), ", ".join(str(o) for o in sorted(orders)))))
                cand.pop(x, None)
    for ln in lines:
        lid = ln["id"]
        if ln["missing"]:
            if ln["bill"]:
                actions.append(dict(line_id=lid, kind="clear_missing", item=ln["item"], order_id=ln["order_id"], old=(ln["bill_raw"], ln["bill_date"], ln["billed_qty"]), new=None,
                                    why="reception marked it missing (never came); Marg's bill %s was matched to it -- a missing line holds no bill" % ln["bill_raw"]))
            continue
        h = cand.get(lid)
        if h is not None:
            if ln["bill"] == SF._bill(h["bill"]):
                continue                                      # agrees with its scan (the bill number is the answer; rule a trusts it)
            q, units = _packs(h, ln["pack_size"])
            if q <= 0 and not units:
                continue
            actions.append(dict(line_id=lid, kind="repair", item=ln["item"], order_id=ln["order_id"], old=(ln["bill_raw"], ln["bill_date"], ln["billed_qty"]),
                                new=(str(h["bill"]), h["date"], q, units), marg_wrote=(ln["arrived_by"] == "marg" or ln["supplied"] is None), packs=ln["packs"],
                                why="its order's scanned bill is %s (%s)" % (h["bill"], dmy(h["date"])) + (" -- it held %s" % ln["bill_raw"] if ln["bill"] else "")))
            continue
        if not ln["bill"] or not SB.get(ln["order_id"]) or any(x["line_id"] == lid for x in listed):
            continue                                          # a listed line is never changed
        if not SF._s952_keyed(ctx, sp, ln["order_id"]):
            continue
        hc = _hit_on_bill(con, sp, ln, ln["bill_raw"], ln["bill_date"])
        key = (hc["supkey"], SF._bill(hc["bill"]), hc["date"], str(hc.get("seq"))) if hc else None
        other = owner.get(key) if key else None
        if other is not None and other != lid:
            ol = by_id[other]
            kind = "unbill_missing" if ln["arrived_by"] == "marg" else "unbill"
            actions.append(dict(line_id=lid, kind=kind, item=ln["item"], order_id=ln["order_id"], old=(ln["bill_raw"], ln["bill_date"], ln["billed_qty"]), new=None,
                                why="bill %s is the scanned bill of order %d (line %d); this line's own order's scanned bill does not carry it%s" % (
                                    ln["bill_raw"], ol["order_id"], other, " -- it never came on its order (Marg had marked it)" if kind == "unbill_missing" else "")))
        else:
            listed.append(dict(line_id=lid, item=ln["item"], order_id=ln["order_id"], why="holds bill %s (%s); its order's scanned bill does not carry it and no other scan claims it -- kept" % (
                ln["bill_raw"], dmy(ln["bill_date"]))))
    return dict(actions=actions, listed=listed)


def _packs(hit, ps):
    """The packs a matched bill line brings in the order's unit -- porders' own rule (_s628_packs), fail-soft to qty + free."""
    try:
        import porders                                        # noqa: PLC0415
        return porders._s628_packs(hit, ps)
    except Exception:                                         # noqa: BLE001
        return int(round(float(hit.get("qty") or 0) + float(hit.get("free") or 0))), None


FP_KEY = "arrival.s952_repair_fp"


def repair_fp(con, sp):
    """What the repair depends on: the scan links, the ties, the order lines' answers and taps, the spine's build. One md5."""
    import hashlib                                            # noqa: PLC0415
    parts = []
    for sql in ("SELECT COUNT(*) || '/' || MAX(linked_at) FROM purchase_scan_link", "SELECT COUNT(*) || '/' || MAX(tied_at) FROM order_scan_tie",
                "SELECT COUNT(*) || '/' || MAX(arrived_at) || '/' || SUM(COALESCE(missing,0)) || '/' || COUNT(billed_bill_no) FROM purchase_order_line"):
        try:
            parts.append(str(con.execute(sql).fetchone()[0]))
        except sqlite3.Error:
            parts.append("-")
    try:
        parts.append(str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or ""))
    except Exception:                                         # noqa: BLE001
        parts.append("~")
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def repair_due(con, sp=None):
    """True when the repair's inputs moved since its last pass (detect_supplies runs on every page read: the repair only when it can matter)."""
    sp = sp or _sw().Spine()
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (FP_KEY,)).fetchone()
    except sqlite3.Error:
        return True
    return not r or r[0] != repair_fp(con, sp)


def scan_repair(con, sp=None, who="s952", write=True):
    """Apply plan_repair (write=True) -- one transaction, every change audited and kept for the undo. Returns dict(done, listed, actions)."""
    ensure(con)
    SW = _sw()
    sp = sp or SW.Spine()
    if not getattr(sp, "ok", False):
        return dict(done=0, listed=[], actions=[], reason="the spine could not be read")
    P = plan_repair(con, sp)
    if not write:
        return dict(done=0, listed=P["listed"], actions=P["actions"])
    if not P["actions"]:
        _remember(con, sp)
        return dict(done=0, listed=P["listed"], actions=P["actions"])
    ts = now_iso()
    done = 0
    try:
        for a in P["actions"]:
            lid = a["line_id"]
            before = _line_row(con, lid)
            if before is None:
                continue
            if a["kind"] == "repair":
                bno, bd, q, units = a["new"]
                con.execute("UPDATE purchase_order_line SET billed_qty=?, billed_bill_no=?, billed_date=?, billed_units=?, detected_at=? WHERE id=?",
                            (q, bno, bd, units, ts, lid))
                if a.get("marg_wrote"):                       # Marg wrote supplied (or nobody did): it follows the bill; a person's tap stays theirs
                    con.execute("UPDATE purchase_order_line SET supplied=?, short=?, arrived_by='marg', arrived_at=COALESCE(arrived_at, ?) WHERE id=?",
                                (q, 1 if q < int(a.get("packs") or 0) else 0, ts, lid))
                action = "line_repaired_s952"
            elif a["kind"] in ("unbill", "clear_missing"):
                con.execute("UPDATE purchase_order_line SET billed_qty=NULL, billed_bill_no=NULL, billed_date=NULL, billed_units=NULL WHERE id=?", (lid,))
                action = "line_unbilled_s952"
            elif a["kind"] == "unbill_missing":
                con.execute("UPDATE purchase_order_line SET billed_qty=NULL, billed_bill_no=NULL, billed_date=NULL, billed_units=NULL, supplied=0, short=1, missing=1 WHERE id=?", (lid,))
                action = "line_missing_s952"
            else:
                continue
            after = _line_row(con, lid)
            con.execute("INSERT INTO s952_line_undo (line_id, at, action, before_json, after_json, why) VALUES (?,?,?,?,?,?)",
                        (lid, ts, action, json.dumps(before, default=str), json.dumps(after, default=str), a["why"]))
            _audit_p(con, who, action, lid, dict(item=a["item"], order=a["order_id"], old=a["old"], new=a["new"], why=a["why"], kit=KIT))
            done += 1
        con.commit()
    except Exception:                                         # noqa: BLE001 -- all or nothing, whatever failed
        con.rollback()
        raise
    _remember(con, sp)
    return dict(done=done, listed=P["listed"], actions=P["actions"])


def _remember(con, sp):
    try:
        con.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,?)", (FP_KEY, repair_fp(con, sp), "S952: the scan repair's last inputs (written by it)"))
        con.commit()
    except sqlite3.Error:
        pass


def undo_repairs(con, who="s952-undo"):
    """Put every line the repair changed back as it was (newest first); marks the undo rows. Returns the count."""
    ensure(con)
    n = 0
    skipped = []
    for uid, lid, before, after in con.execute("SELECT id, line_id, before_json, after_json FROM s952_line_undo WHERE undone_at IS NULL ORDER BY id DESC").fetchall():
        b, a = json.loads(before), json.loads(after)
        now = _line_row(con, lid)
        if now is None or any(str(now.get(f)) != str(a.get(f)) for f in LINE_FIELDS if f not in ("detected_at", "arrived_at")):
            skipped.append(lid)                               # changed since the repair (a tap, an answer): left as it is now
            con.execute("UPDATE s952_line_undo SET undone_at=?, why=COALESCE(why,'') || ' · undo skipped: changed since' WHERE id=?", (now_iso(), uid))
            continue
        con.execute("UPDATE purchase_order_line SET %s WHERE id=?" % ", ".join("%s=?" % f for f in LINE_FIELDS), tuple(b.get(f) for f in LINE_FIELDS) + (lid,))
        con.execute("UPDATE s952_line_undo SET undone_at=? WHERE id=?", (now_iso(), uid))
        _audit_p(con, who, "line_undo_s952", lid, dict(restored=b, kit=KIT))
        n += 1
    con.commit()
    if skipped:
        print("S952 undo: %d order line(s) changed since the repair were left as they are: %s" % (len(skipped), ", ".join(str(x) for x in skipped[:20])), file=sys.stderr)
    return n


# ================================================================================================================ 2 · THE JUDGMENT
def _record_row(con, sp, item):
    try:
        return _sr().row(con, item, sp, "never")
    except Exception:                                         # noqa: BLE001
        return None


def _caps(sp, ctx):
    """stock_record.captures once per Ctx, by md5."""
    if "s952caps" not in ctx.c:
        try:
            ctx.c["s952caps"] = {c["md5"]: c for c in _sr().captures(sp, _sf())}
        except Exception:                                     # noqa: BLE001
            ctx.c["s952caps"] = {}
    return ctx.c["s952caps"]


def _first_seen(con, ctx):
    if "s952fs" not in ctx.c:
        try:
            ctx.c["s952fs"] = _sr()._first_seen(con, _sw())
        except Exception:                                     # noqa: BLE001
            ctx.c["s952fs"] = {}
    return ctx.c["s952fs"]


def late_certain(con, sp, k, cap, ctx):
    """The record's 'certain' late bills for a print: purchase bills (returns signed) of the key dated within LATE_DAYS on or before the print's
    last day (stock_record.late_hi) whose first appearance in Amir's purchase export is AFTER the print day -- the print could not hold them.
    -> (units, [bill])."""
    SR = _sr()
    try:
        hi = SR.late_hi(cap)
        lo = (dt.date.fromisoformat(hi) - dt.timedelta(days=SR.LATE_DAYS)).isoformat()
        rows = sp.q("SELECT supkey, bill, date, SUM(CASE WHEN direction IN ('RETURN','PURCHASE_RETURN') THEN -units ELSE units END) AS u FROM sp_purchase_line "
                    "WHERE k20=? AND direction IN ('PURCHASE','RETURN','PURCHASE_RETURN') AND date<=? AND date>=? GROUP BY supkey, bill, date", k, hi, lo)
    except Exception:                                         # noqa: BLE001
        return 0.0, []
    fs = _first_seen(con, ctx)
    tot, bills = 0.0, []
    for r in rows:
        f = fs.get((str(r["supkey"] or ""), SR._bill(r["bill"]), str(r["date"] or "")[:10]))
        if f and f > cap["print_day"] and f > LATE_FROM:
            tot += float(r["u"] or 0)
            bills.append(str(r["bill"]))
    return tot, bills


def marg_end(con, sp, item, day, R=None, ctx=None):
    """Marg's figure at the END of `day` by THE RECORD'S OWN RULE applied to the print standing then: the newest closing print whose day is on
    or before `day` (stock_figure.marg: the print, the morning rule, a split's share, carried by the spine's movements to `day`) + the bills the
    print could not hold (first seen in Amir's export after it: late_certain). -> dict(figure, k, approx, print_end, late, late_bills) or None."""
    SF = _sf()
    ctx = ctx or SF.Ctx(con, sp)
    R = R or _record_row(con, sp, item)
    try:
        M = SF.marg(con, sp, item, str(day)[:10], ctx)
    except Exception:                                         # noqa: BLE001
        M = None
    if M is None:
        return None
    k = M.get("key") or (R or {}).get("k20") or SF.key_of(sp, item, ctx)
    cap = _caps(sp, ctx).get(M["closing"]["md5"])
    late, bills = late_certain(con, sp, k, cap, ctx) if cap else (0.0, [])
    fam = bool((R or {}).get("approx")) or len(M.get("family") or []) > 1 or bool((M.get("closing") or {}).get("approx"))
    return dict(figure=float(M["figure"]) + late, k=k, family=fam, reason=M.get("approx_reason"), print_end=M["closing"]["end_day"], late=late, late_bills=bills)


def _line_moment(a):
    """The physical arrival moment of a delivery line: a person's tap (arrived_at) or the scan of its order; Marg's own detection is no
    arrival -- then the scan moment, else unknown (None)."""
    by = str(a.get("arrived_by") or "")
    m = str(a.get("scan_at") or "") if by in ("marg", "") else str(a.get("arrived_at") or a.get("scan_at") or "")
    if by in ("marg", "") and not m:
        return None
    m = m.strip().replace(" ", "T")[:19]
    return m or None


def deliveries(con, sp, item, ctx=None):
    """Every delivery line of the item (taps of any age, and scan-tied lines not yet answered): dict(line_id, order_id, vendor, moment,
    bill, bill_date (Marg's bill that carries it -- its answer, or the one rule's carried(); '' when none), units_marg (the bill line's
    units), units_shelf (what reached the shelf: the scanned bill's quantity when it speaks, else the tap), kind)."""
    SF, SW = _sf(), _sw()
    ctx = ctx or SF.Ctx(con, sp)
    out, seen = [], set()
    rows = list(SW._arrivals(con, item, "", sp, ctx=ctx)) + list(SF.scan_lines(con, sp, item, "", ctx))
    for a in rows:
        lid = a.get("line_id")
        if lid in seen:
            continue
        seen.add(lid)
        try:
            h = SF.carried(con, sp, a, ctx)
        except Exception:                                     # noqa: BLE001
            h = None
        try:
            shelf_u = float(SF._count_units(con, sp, a, ctx))
        except Exception:                                     # noqa: BLE001
            shelf_u = float(a.get("units") or 0)
        not_on_bill = False
        if h is None:                                         # rule 0: its order's scanned bill is keyed in Marg and does not carry it -- it did not come
            try:
                not_on_bill = bool(SF._s952_on(ctx) and SF._s952_keyed(ctx, sp, SF._s952_order_of(ctx, a)))
            except Exception:                                 # noqa: BLE001
                not_on_bill = False
            if not_on_bill:
                shelf_u = 0.0
        mu = float(h["units"]) if (h and h.get("units") is not None) else shelf_u
        out.append(dict(line_id=lid, order_id=a.get("order_id"), vendor=a.get("vendor") or "", moment=_line_moment(a), kind=a.get("kind") or "tap",
                        bill=(str(h.get("bill") or "") if h else ""), bill_date=(str(h.get("date") or "")[:10] if h else ""), units_marg=mu, units_shelf=shelf_u,
                        not_on_bill=not_on_bill))
    return out


def _allow(con, sp, item, pack, since, until):
    """S427's allowance for the window (since, until]: stock.allowance_pct % of the item's own sales in it, floor one strip / piece."""
    try:
        import loss_piles                                     # noqa: PLC0415
        LS = loss_piles.settings(con)
        pct, floor = float(LS["allowance_pct"]), int(LS["allowance_min_strips"])
    except Exception:                                         # noqa: BLE001
        pct, floor = 1.0, 1
    sold = float(sp.sales(item, str(since)[:10], str(until)[:10])["u"] or 0) if getattr(sp, "ok", False) else 0.0
    return max(int(pct / 100.0 * sold), floor * (pack if pack > 1 else 1))


def _pending_loss(con, sp, item, k, at, fday, exclude_id=None, ctx=None):
    """The older losses Marg still holds: loss lines of the item booked before `at` on a judgment against the record (basis 'record' -- a line
    booked against an old count carried forward says nothing of what Marg holds), not withdrawn, and the full count's shortfalls (06-Sep: no
    loss line, written off by Amir's vouchers -- when they were keyed in Marg), less what Marg has written off since --
    Marg's figure dropping more than the spine's movements explain (a filed voucher or a correction keyed in Marg) between the oldest of them
    and the figure's day. -> (units, oldest day)."""
    SWm = _sw()
    try:
        rows = con.execute("SELECT l.at, l.gap_units FROM stock_watch_loss_line l LEFT JOIN stock_point p ON p.id=l.point_id WHERE l.void_at IS NULL AND l.at<? "
                           "AND (p.item_norm=? OR l.item=?) AND (l.point_id IS NULL OR (l.point_id<>? AND p.basis='record'))", (str(at)[:19], SWm.norm_name(item), item, int(exclude_id or -1))).fetchall()
    except sqlite3.Error:
        return 0.0, ""
    fc, fc_day = _fc_pending(con, sp, item, k, at, ctx, fday)
    if not rows:
        return fc, fc_day
    losses = sorted((str(r[0])[:10], float(r[1] or 0)) for r in rows if float(r[1] or 0) > 0)
    if not losses:
        return fc, fc_day
    lo = losses[0][0]
    hi = str(fday)[:10]
    SF = _sf()
    ctx = ctx or SF.Ctx(con, sp)
    m_hi = marg_end(con, sp, item, hi, None, ctx)
    cache = {}

    def cover(d_i):
        """Marg's NET unexplained drop from d_i to the figure's day: its figure then less (its figure at d_i + the spine's movements between) --
        a write-off keyed in Marg; a bill keyed late drops and comes back, and nets out (a rise does too: NORTIMER, JAKMAC 5)."""
        if d_i >= hi or m_hi is None:
            return 0.0
        if d_i not in cache:
            m0 = marg_end(con, sp, item, d_i, None, ctx)
            cache[d_i] = max(0.0, -(m_hi["figure"] - (m0["figure"] + float(SF.spine_move(sp, k, d_i, hi))))) if m0 else 0.0
        return cache[d_i]
    pend, day = 0.0, lo
    for i, (d_i, _u) in enumerate(losses):                    # a write-off after a day covers only the losses booked by then (Hall's bound)
        tail = sum(u for (d, u) in losses[i:])
        if tail - cover(d_i) > pend + TOL:
            pend, day = tail - cover(d_i), d_i
    if fc >= TOL and pend < TOL:
        day = fc_day
    return max(0.0, pend) + fc, day


def _day_of(v):
    """'2026-10-15' or '04-10-2026' -> ISO day; '' when unreadable."""
    t = str(v or "").strip()[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", t):
        return t
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", t)
    return "%s-%s-%s" % (m.group(3), m.group(2), m.group(1)) if m else ""


def _fc_pending(con, sp, item, k, at, ctx=None, fday=None):
    """S954 (his question 17:14 25-Nov: "Amir already did all stock corrections in mid October, and the system verified"): the full count's
    shortfalls as they were CLOSED -- a shortfall closed FOUND (kept elsewhere, turned up; sold after the count), BILLING / BILLED_NOT_GIVEN
    (cleared by a bill) or reconciled is no loss and never pending;
    one written off by Amir's ISSUE voucher (stock_voucher_line, keyed on stock_voucher_entered.entered_on) is covered when Marg's own figure
    dropped by at least half of it in the days around that entry (entered_on - 7 .. + 5, beyond the spine's movements). What is left -- a
    voucher keyed but Marg's stock never moved by it, or a shortfall neither found nor written off -- is pending. -> (units, '2026-09-06'-like day)."""
    SWm, SF = _sw(), _sf()
    ctx = ctx or SF.Ctx(con, sp)
    try:
        pts = con.execute("SELECT at, -gap_units, count_id, item FROM stock_point WHERE source='full_count' AND item_norm=? AND gap_units<0 AND at<? "
                          "AND COALESCE(status,'') NOT IN ('superseded')", (SWm.norm_name(item), str(at)[:19])).fetchall()
    except sqlite3.Error:
        return 0.0, ""
    tot, day = 0.0, ""
    for p_at, short, cid, pitem in pts:
        try:
            found = con.execute("SELECT 1 FROM stock_diff WHERE item IN (?,?) AND (UPPER(COALESCE(cause,'')) IN ('FOUND','BILLING','BILLED_NOT_GIVEN') OR LOWER(COALESCE(status,''))='reconciled')" + (" AND count_id=?" if cid else ""),
                                (pitem, item) + ((cid,) if cid else ())).fetchone() if _has(con, "stock_diff") else None
        except sqlite3.Error:
            found = None
        if found:
            continue
        covered = 0.0
        try:
            vls = con.execute("SELECT l.change, e.entered_on FROM stock_voucher_line l LEFT JOIN stock_voucher_entered e ON e.id=(SELECT MAX(x.id) FROM stock_voucher_entered x "
                              "WHERE x.count_id=l.count_id AND x.round_no=l.round_no AND x.kind=l.kind AND x.batch_no=l.batch_no) "   # the newest row of a batch wins
                              "WHERE l.item IN (?,?) AND l.kind='ISSUE' AND l.change<0" + (" AND l.count_id=?" if cid else ""),
                              (pitem, item) + ((cid,) if cid else ())).fetchall() if _has(con, "stock_voucher_line") else []
        except sqlite3.Error:
            vls = []
        for ch, eon in vls:
            e = _day_of(eon)
            if not e:
                continue                                      # the batch was never marked entered in Marg: not covered
            try:
                d0 = (dt.date.fromisoformat(e) - dt.timedelta(days=7)).isoformat()
                d1 = min((dt.date.fromisoformat(e) + dt.timedelta(days=5)).isoformat(), today().isoformat())
                m0, m1 = marg_end(con, sp, item, d0, None, ctx), marg_end(con, sp, item, d1, None, ctx)
                un = (m1["figure"] - (m0["figure"] + float(SF.spine_move(sp, k, d0, d1)))) if (m0 and m1) else 0.0
            except Exception:                                 # noqa: BLE001
                un = 0.0
            if un <= float(ch) / 2.0:                         # Marg dropped by at least half the voucher: it took effect
                covered += -float(ch)
        try:                                                  # and Marg's NET drop since the count (a purchase inside the window can hide the voucher:
            hi = str(fday or _day_before(str(at)[:10]))[:10]  # IGURATI 25; a voucher that landed in two steps: DOLONEX 2 ML INJ)
            c0 = str(p_at)[:10]
            m0, m1 = marg_end(con, sp, item, c0, None, ctx), marg_end(con, sp, item, hi, None, ctx)
            net = max(0.0, -((m1["figure"] - (m0["figure"] + float(SF.spine_move(sp, k, c0, hi)))))) if (m0 and m1 and hi > c0) else 0.0
        except Exception:                                     # noqa: BLE001
            net = 0.0
        if vls:
            covered = max(covered, min(net, -sum(float(v[0]) for v in vls)))   # never more than Amir wrote off
        left = float(short) - covered
        if left >= TOL:
            tot += left
            day = day or str(p_at)[:10]
    return tot, day


def judge(con, sp, item, at, qty=None, last_bill=None, exclude_id=None, ctx=None, live=False):
    """THE ONE JUDGMENT of a count against the record (the rules at the head of this file). Returns dict(expected, basis 'record' | 'approx'
    | 'marg' | None, provisional 0.0, as_on (the figure's day), marg_at, waiting, after, never_loss (bool), pending_loss, words, awaits (the
    day's sales are needed and not in -- a bill-placed count waits), mode, terms). qty (the count) shapes the words; without it, none.
    live=True: the count being saved now (its day's sales cannot be in yet): an evening count is judged as the start of its day, worded."""
    SF, SW = _sf(), _sw()
    ctx = ctx or SF.Ctx(con, sp)
    at = str(at or now_iso()).replace(" ", "T")[:19]
    D = at[:10]
    R = _record_row(con, sp, item)
    if R is None:                                             # not in the record: Marg's branch of the old one, unchanged
        E = SF.expect_for_point(con, sp, item, ctx=ctx, basis="marg", exclude_id=exclude_id)
        E = dict(E, words=("judged against Marg's figure (the item is not in the stock record)" if E.get("expected") is not None else ""), never_loss=False,
                 waiting=0.0, after=0.0, pending_loss=0.0, awaits=False, mode="marg", marg_at=E.get("expected"))
        return E
    pack = int(R.get("pack") or 1) or 1
    if R.get("approx"):
        return dict(expected=None, basis="approx", provisional=0.0, as_on=D, approx=True, close=None, sold=0.0, bought=0.0, records=None, terms=[],
                    words="", never_loss=True, waiting=0.0, after=0.0, pending_loss=0.0, awaits=False, mode="approx", marg_at=None)
    S = SW.settings(con)
    ev_h = int(S.get("evening_hour", 17))
    N = SW._s934_bill_no(last_bill) if last_bill else None
    sales_in = SW._s934_sales_in(con, sp, D)
    ev = (N is None) and SF.evening_count(at, ev_h, D)
    notes = []
    if N is not None and sales_in:
        fday, mode = D, "to_bill"
    elif ev and sales_in:
        fday, mode = D, "evening"
    elif N is not None:
        return dict(expected=None, basis="record", provisional=0.0, as_on=D, awaits=True, words="waits for the day's sales", never_loss=True, mode="awaits",
                    waiting=0.0, after=0.0, pending_loss=0.0, marg_at=None, approx=False, close=None, sold=0.0, bought=0.0, records=None, terms=[])
    elif ev and live:                                         # the evening count being saved now: judged to its day's end once the sales are in
        return dict(expected=None, basis="record", provisional=0.0, as_on=D, awaits=True, words="an evening count -- judged to the day's end when its sale report is in",
                    never_loss=True, mode="awaits", waiting=0.0, after=0.0, pending_loss=0.0, marg_at=None, approx=False, close=None, sold=0.0, bought=0.0, records=None, terms=[])
    else:
        fday, mode = _day_before(D), "start"
        if ev:
            notes.append("an evening count judged as the start of its day (the day's sales are not in yet)")
    ME = marg_end(con, sp, item, fday, R, ctx)
    if ME is None:
        return dict(expected=None, basis="record", provisional=0.0, as_on=fday, awaits=False, words="no Marg print for that day -- counted and kept", never_loss=True,
                    mode=mode, waiting=0.0, after=0.0, pending_loss=0.0, marg_at=None, approx=False, close=None, sold=0.0, bought=0.0, records=None, terms=[])
    if ME["family"]:
        return dict(expected=None, basis="approx", provisional=0.0, as_on=fday, approx=True, close=None, sold=0.0, bought=0.0, records=None, terms=[],
                    words="", never_loss=True, waiting=0.0, after=0.0, pending_loss=0.0, awaits=False, mode="approx", marg_at=None)
    k = ME["k"]
    add = 0.0
    if mode == "to_bill":
        add = float(SF.day_sales_cut(sp, k, D, N, after=True))
    marg_at = ME["figure"] + add
    never = False
    if ME["reason"]:                                          # a morning print holding a purchase of its own day (S587): judged, shown, never a loss
        never = True
        notes.append("Marg's print of %s is a morning one holding a purchase of that day -- shown, never a loss" % dmy(ME["print_end"]))
    if ME["late_bills"]:
        notes.append("Marg's print of %s did not hold bill %s yet -- added" % (dmy(ME["print_end"]), ", ".join(ME["late_bills"])))
    waiting = after = 0.0
    W, A, old_taps, nob = [], [], [], []
    t_lo = (dt.datetime.fromisoformat(at) - dt.timedelta(days=WAIT_DAYS)).isoformat()
    known = set()
    for d in deliveries(con, sp, item, ctx):
        m = d["moment"]
        bd = d["bill_date"]
        if bd:
            known.add((SF._bill(d["bill"]), bd))
        if m is None:
            continue
        if d.get("not_on_bill"):
            if m <= at and m >= t_lo:
                nob.append(d)
            continue
        if m <= at and (not bd or bd > fday):
            if not bd and m < t_lo:
                old_taps.append(d)
                continue
            if d["units_shelf"] > 0:
                waiting += d["units_shelf"]
                W.append(d)
        elif m > at and bd and bd <= fday:
            after += d["units_marg"]
            A.append(d)
    unknown_day = []
    try:                                                      # a purchase dated the figure's day with no arrival moment known
        for p in sp.q("SELECT bill, date, SUM(units) AS u, supkey FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE' AND date=? GROUP BY supkey, bill, date", k, fday):
            if (SF._bill(p["bill"]), str(p["date"])[:10]) not in known:
                unknown_day.append(p)
    except Exception:                                         # noqa: BLE001
        unknown_day = []
    if unknown_day and mode in ("to_bill", "evening"):
        never = True
        notes.append("bill %s is dated that day and its arrival time is not known -- shown, never a loss" % ", ".join(str(p["bill"]) for p in unknown_day))
    expected = marg_at + waiting - after
    terms = dict(marg_at=marg_at, figure_day=fday, mode=mode, sales_after_bill=add, waiting=[(d["line_id"], d["units_shelf"]) for d in W],
                 after=[(d["line_id"], d["units_marg"]) for d in A], unkeyed_old=[d["line_id"] for d in old_taps])
    words = []
    if W:
        words.append("includes %s on the shelf not yet in Marg (%s)" % (st(waiting, pack), "; ".join("%s %s" % ((d["vendor"].split() or ["?"])[0], dmy(d["moment"])) for d in W)))
    if A:
        words.append("less %s in Marg that came after the count (%s)" % (st(after, pack), "; ".join("bill %s" % d["bill"] for d in A)))
    if old_taps:
        words.append("a tap of %s never reached Marg -- not counted" % ", ".join(dmy(d["moment"]) for d in old_taps))
    if nob:
        words.append("a tap of %s is not on its order's scanned bill -- not counted" % ", ".join(dmy(d["moment"]) for d in nob))
    pend, pend_day = _pending_loss(con, sp, item, k, at, fday, exclude_id, ctx)
    E = dict(expected=expected, basis="record", provisional=0.0, as_on=fday, approx=False, close=marg_at, sold=0.0, bought=0.0, records=marg_at, terms=terms,
             marg_at=marg_at, waiting=waiting, after=after, never_loss=never, pending_loss=pend, pending_day=pend_day, awaits=False, mode=mode, notes=notes, pack=pack,
             k=k, words="")
    if qty is not None:
        E = settle_words(con, sp, item, E, float(qty), at, exclude_id, words)
    else:
        E["words"] = " · ".join(words + notes)
    return E


def settle_words(con, sp, item, E, qty, at, exclude_id, words):
    """The verdict words, and the pending older loss taken out of a short it explains (expected moved by it, so the gap is the NEW part)."""
    pack = E["pack"]
    raw = qty - E["expected"]
    try:
        r = con.execute("SELECT at FROM stock_point WHERE item_norm=? AND at<? AND COALESCE(status,'') NOT IN ('superseded') AND COALESCE(id,-1)<>? ORDER BY at DESC LIMIT 1",
                        (_sw().norm_name(item), at, int(exclude_id or -1))).fetchone()
        since = str(r[0])[:10] if r else (dt.date.fromisoformat(at[:10]) - dt.timedelta(days=30)).isoformat()
    except (sqlite3.Error, ValueError):
        since = at[:10]
    allow = _allow(con, sp, item, pack, since, E["as_on"])
    E["allowance"] = allow
    head = ""
    if abs(raw) < TOL:
        head = "matches Marg"
    elif raw > 0:
        head = "%s more than Marg -- noted, never a loss" % st(raw, pack)
    else:
        short = -raw
        pend = float(E.get("pending_loss") or 0)
        take = 0.0
        if pend >= TOL and short > allow:                     # the older loss Marg still holds comes off first (booked once, never twice)
            take = min(pend, short)
            E["expected"] = E["expected"] - take
            E["pending_taken"] = take
        rest = short - take
        ptxt = ("Marg still holds the older loss of %s (%s) not yet written off" % (dmy(E.get("pending_day")), st(take, pack))) if take else ""
        if rest <= allow:
            head = (ptxt + " -- not a new loss") if take else ("%s below Marg -- within the allowance" % st(short, pack))
        else:
            near = _near_delivery(sp, E.get("k"), E["as_on"], at, rest, pack)
            if near is not None:                              # a delivery's worth short: a supply question, not a shop loss -- never booked
                E["near_delivery"] = near
                E["never_loss"] = True
                head = (ptxt + "; " if take else "") + "below Marg by about a delivery -- bill %s (%s, %s: %s) may not have been on the shelf; count again" % (
                    near["bill"], (str(near.get("supkey") or "").split() or ["?"])[0], dmy(near["date"]), st(near["units"], pack))
            elif take:
                head = "%s; %s below that -- a loss since the last count" % (ptxt, st(rest, pack))
            else:
                head = "%s below Marg -- a loss since the last count" % st(short, pack)
    E["words"] = " · ".join([head] + words + list(E.get("notes") or []))
    return E


def _near_delivery(sp, k, fday, at, short, pack):
    """A Marg purchase bill of the key dated the figure's day or the day before whose units are about the short (within half a strip / piece,
    or 10 %) -- the delivery that may not have been on the shelf."""
    if not k:
        return None
    try:
        lo = _day_before(fday)
        best = None
        for p in sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, SUM(l.units) AS u, MAX(b.supplier) AS supplier FROM sp_purchase_line l "
                      "LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date WHERE l.k20=? AND l.direction='PURCHASE' "
                      "AND l.date>=? AND l.date<=? GROUP BY l.supkey, l.bill, l.date", k, lo, str(at)[:10]):
            u = float(p["u"] or 0)
            d = abs(short - u)
            if u > 0 and d <= max(0.1 * u, pack / 2.0) and (best is None or d < best[0]):
                best = (d, dict(supkey=(p.get("supplier") or p["supkey"]), bill=p["bill"], date=str(p["date"])[:10], units=u))
        return best[1] if best else None
    except Exception:                                         # noqa: BLE001
        return None


def expect(con, sp, item, at=None, qty=None, last_bill=None, exclude_id=None, ctx=None, live=False):
    """The judgment write_point / settle_provisional / _s934_settle read: judge() when the switch is on, else None (the caller's old path)."""
    if not switch_on(con):
        return None
    return judge(con, sp, item, at or now_iso(), qty, last_bill, exclude_id, ctx, live)


# ================================================================================================================ 3 · JUDGE AGAIN
def rejudge_all(con, sp=None, who="s952", write=True, since=None, ids=None):
    """Every spot / darpan point (not superseded, not held) from `since`, oldest first, judged again by judge(). A point whose judgment
    moves: expected_units, gap_units, basis='record', judge_words rewritten (the old ones kept in s952_point_undo); its loss line WITHDRAWN when
    the re-judged short is within the allowance, a surplus, or never a loss (void_at, void_why in plain words); a loss line that stands is
    re-sized to the re-judged short. A point beyond the allowance with no loss line is LISTED (never booked after the fact). Returns
    dict(n, moved, withdrawn, resized, listed, rows)."""
    ensure(con)
    SW = _sw()
    sp = sp or SW.Spine()
    out = dict(n=0, moved=0, withdrawn=0, resized=0, listed=[], rows=[])
    since = since or REJUDGE_FROM
    if not getattr(sp, "ok", False):
        out["reason"] = "the spine could not be read"
        return out
    q = ("SELECT id, item, at, qty_units, expected_units, gap_units, basis, status, last_bill, judge_words FROM stock_point WHERE source IN ('spot','darpan') "
         "AND COALESCE(status,'') NOT IN ('superseded','recount','recounted','awaits_sales') AND at>=? ORDER BY at, id")
    ts = now_iso()
    for pid, item, at, qty, e0, g0, b0, status, lb, w0 in con.execute(q, (since,)).fetchall():
        if ids and int(pid) not in ids:
            continue
        out["n"] += 1
        try:
            E = judge(con, sp, item, at, float(qty or 0), lb, pid)
        except Exception as ex:                               # noqa: BLE001 -- one point never stops the pass
            out["rows"].append(dict(id=pid, item=item, error=str(ex)[:120]))
            continue
        if E.get("awaits") or E.get("expected") is None:
            out["rows"].append(dict(id=pid, item=item, at=str(at)[:16], qty=qty, old_expected=e0, old_gap=g0, old_basis=b0, expected=None, gap=None, basis=E.get("basis"),
                                    words="not judged (%s) -- left as it is" % (E.get("words") or E.get("basis") or "no figure"), never_loss=True, allowance=None, skipped=True))
            continue                                          # no figure to judge by: nothing withdrawn, nothing rewritten (positive evidence only)
        e1 = E.get("expected")
        g1 = None if e1 is None else round(float(qty or 0) - float(e1), 3)
        b1 = E.get("basis")
        pack = int(E.get("pack") or 1)
        row = dict(id=pid, item=item, at=str(at)[:16], qty=qty, old_expected=e0, old_gap=g0, old_basis=b0, expected=e1, gap=g1, basis=b1, words=E.get("words") or "",
                   never_loss=bool(E.get("never_loss")), allowance=E.get("allowance"))
        out["rows"].append(row)
        moved = (e1 is None) != (e0 is None) or (e1 is not None and e0 is not None and abs(float(e1) - float(e0)) >= TOL) or (b1 != b0) or ((E.get("words") or "") != (w0 or ""))
        losses = con.execute("SELECT id, gap_units, mrp_p, void_at FROM stock_watch_loss_line WHERE point_id=? AND void_at IS NULL", (pid,)).fetchall()
        allow = float(E.get("allowance") or 0)
        bad = g1 is not None and g1 < 0 and -g1 > allow and not E.get("never_loss") and b1 != "approx"
        keep = g1 is not None and g1 < 0 and -g1 > allow and bool(E.get("never_loss"))   # cannot be told exactly: the line is left as it stands
        if moved:
            out["moved"] += 1
        if write and moved:
            before = dict(expected_units=e0, gap_units=g0, basis=b0, judge_words=w0)
            con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, basis=?, judge_words=? WHERE id=?", (e1, g1, b1, E.get("words") or "", pid))
            con.execute("INSERT INTO s952_point_undo (point_id, loss_id, at, action, before_json, after_json) VALUES (?,?,?,?,?,?)",
                        (pid, None, ts, "point_rejudged", json.dumps(before, default=str), json.dumps(dict(expected_units=e1, gap_units=g1, basis=b1, judge_words=E.get("words")), default=str)))
            _audit_w(con, "point_rejudged_s952", dict(point_id=pid, item=item, old=before, expected=e1, gap=g1, basis=b1, words=E.get("words")), who, pid)
        for lid, lg, mrp, _v in losses:
            if keep:
                row["loss"] = "stands (not judged exactly: left as it is)"
                continue
            if not bad:
                why = "judged again against Marg (S952): %s -- withdrawn" % (E.get("words") or "no loss")
                if write:
                    con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why=? WHERE id=?", (ts, why[:400], lid))
                    con.execute("INSERT INTO s952_point_undo (point_id, loss_id, at, action, before_json, after_json) VALUES (?,?,?,?,?,?)",
                                (pid, lid, ts, "loss_withdrawn", json.dumps(dict(void_at=None, void_why=None)), json.dumps(dict(void_at=ts, void_why=why[:400]))))
                    _audit_w(con, "loss_withdrawn_s952", dict(loss_id=lid, point_id=pid, item=item, was=lg, why=why), who, lid)
                out["withdrawn"] += 1
                row["loss"] = "withdrawn"
            elif abs(float(lg or 0) - (-g1)) >= TOL:
                new_mrp = int(round(float(mrp) * (-g1) / float(lg))) if (mrp and lg) else mrp
                if write:
                    con.execute("UPDATE stock_watch_loss_line SET gap_units=?, mrp_p=? WHERE id=?", (-g1, new_mrp, lid))
                    con.execute("INSERT INTO s952_point_undo (point_id, loss_id, at, action, before_json, after_json) VALUES (?,?,?,?,?,?)",
                                (pid, lid, ts, "loss_resized", json.dumps(dict(gap_units=lg, mrp_p=mrp)), json.dumps(dict(gap_units=-g1, mrp_p=new_mrp))))
                    _audit_w(con, "loss_resized_s952", dict(loss_id=lid, point_id=pid, item=item, was=lg, now=-g1), who, lid)
                out["resized"] += 1
                row["loss"] = "resized %s -> %s" % (st(lg, pack), st(-g1, pack))
            else:
                row["loss"] = "stands"
        if bad and not losses:
            out["listed"].append(dict(id=pid, item=item, at=str(at)[:16], gap=g1, words=E.get("words")))
            row["loss"] = "listed (no loss line booked after the fact)"
        if write:
            con.commit()
    return out


def undo_rejudge(con, who="s952-undo", from_at=None):
    """Put every re-judged point and loss line back (newest first)."""
    ensure(con)
    n = 0
    for uid, pid, lid, action, before, after in con.execute("SELECT id, point_id, loss_id, action, before_json, after_json FROM s952_point_undo WHERE undone_at IS NULL AND (? IS NULL OR at>=?) ORDER BY id DESC", (from_at, from_at)).fetchall():
        b, a = json.loads(before), json.loads(after)
        if action == "point_rejudged":
            r = con.execute("SELECT expected_units, gap_units FROM stock_point WHERE id=?", (pid,)).fetchone()
            if r is None or str(r[0]) != str(a.get("expected_units")) or str(r[1]) != str(a.get("gap_units")):
                con.execute("UPDATE s952_point_undo SET undone_at=? WHERE id=?", (now_iso(), uid))
                continue                                      # judged again since (a correction): left as it is now
            con.execute("UPDATE stock_point SET expected_units=?, gap_units=?, basis=?, judge_words=? WHERE id=?", (b.get("expected_units"), b.get("gap_units"), b.get("basis"), b.get("judge_words"), pid))
        elif action == "loss_withdrawn":
            con.execute("UPDATE stock_watch_loss_line SET void_at=NULL, void_why=NULL WHERE id=? AND void_at=?", (lid, a.get("void_at")))
        elif action == "loss_resized":
            con.execute("UPDATE stock_watch_loss_line SET gap_units=?, mrp_p=? WHERE id=? AND gap_units=?", (b.get("gap_units"), b.get("mrp_p"), lid, a.get("gap_units")))
        elif action == "point_settled":                       # a count the install's one-off settled to its bill: back to waiting
            con.execute("UPDATE stock_point SET status=?, settled_at=?, expected_units=?, gap_units=?, basis=?, judge_words=? WHERE id=? AND status='settled'",
                        (b.get("status"), b.get("settled_at"), b.get("expected_units"), b.get("gap_units"), b.get("basis"), b.get("judge_words"), pid))
        elif action == "loss_created":                        # a loss line that settle booked: withdrawn (never deleted)
            con.execute("UPDATE stock_watch_loss_line SET void_at=?, void_why='S952 undo: booked by the install' WHERE id=? AND void_at IS NULL", (now_iso(), lid))
        con.execute("UPDATE s952_point_undo SET undone_at=? WHERE id=?", (now_iso(), uid))
        n += 1
    con.commit()
    _audit_w(con, "rejudge_undone_s952", dict(rows=n), who, 0)
    return n


# ================================================================================================================ 4 · THE DAILY SELF-CHECK (READ ONLY)
def self_check(con, sp=None):
    """READ ONLY. dict(ok, at, lines=[dict(item, kind, words)]) -- kinds: 'stored_judgment' (a stored judgment that a judgment today would move
    by a strip / piece or more, or whose loss line it would not bear out), 'pairing' (an answered order line its own scanned bill contradicts,
    a missing line holding a bill), 'record' (the record every page reads is not built, older than 12 hours, or skipped items)."""
    SW = _sw()
    sp = sp or SW.Spine()
    out = dict(ok=False, at=now_iso(), lines=[])
    if not getattr(sp, "ok", False):
        out["reason"] = "the spine could not be read"
        return out
    try:
        P = plan_repair(con, sp)
        for a in P["actions"]:
            out["lines"].append(dict(item=a["item"], kind="pairing", words="order %d: %s" % (a["order_id"], a["why"])))
    except Exception as ex:                                   # noqa: BLE001
        out["lines"].append(dict(item="", kind="error", words="the pairing check failed: %s" % str(ex)[:100]))
    try:
        R = rejudge_all(con, sp, who="s952-check", write=False, since=max(REJUDGE_FROM, (today() - dt.timedelta(days=60)).isoformat()))
        fresh = (today() - dt.timedelta(days=3)).isoformat()
        for r in R["rows"]:
            if r.get("error") or r.get("skipped"):
                continue
            e0, e1 = r.get("old_expected"), r.get("expected")
            moved = (e0 is None) != (e1 is None) or (e0 is not None and e1 is not None and abs(float(e0) - float(e1)) > float(r.get("allowance") or 1.0))
            loss = str(r.get("loss") or "")
            if moved or loss.startswith(("withdrawn", "resized")) or (loss.startswith("listed") and r["at"][:10] >= fresh):
                out["lines"].append(dict(item=r["item"], kind="stored_judgment", words="count of %s: stored %s, judged today %s%s -- %s" % (
                    dmy(r["at"]), _g(r.get("old_gap")), _g(r.get("gap")), (" (loss line: %s)" % r["loss"]) if r.get("loss") else "", r.get("words") or "")))
    except Exception as ex:                                   # noqa: BLE001
        out["lines"].append(dict(item="", kind="error", words="the judgment check failed: %s" % str(ex)[:100]))
    try:                                                      # the record every page reads: built, fresh, whole
        M = _sr().meta(con)
        if not M.get("built_at"):
            out["lines"].append(dict(item="", kind="record", words="the stock of record has never been built"))
        else:
            age = (dt.datetime.fromisoformat(now_iso()) - dt.datetime.fromisoformat(M["built_at"][:19])).total_seconds() / 3600.0
            if age > 12:
                out["lines"].append(dict(item="", kind="record", words="the stock of record was last built %s (%d hours ago) -- the pages show an old figure" % (M["built_at"][:16], age)))
            if int(M.get("n_errors") or 0):
                out["lines"].append(dict(item="", kind="record", words="the stock of record skipped %s item(s) at its last build" % M.get("n_errors")))
    except Exception as ex:                                   # noqa: BLE001
        out["lines"].append(dict(item="", kind="error", words="the record check failed: %s" % str(ex)[:100]))
    out["ok"] = True
    return out


def _g(v):
    return "—" if v is None else ("%+d" % int(round(float(v))))


def needs_you_line(con, sp=None):
    """One line for the owner's Needs-you when the self-check names anything, else None -- written by the cron (--check), read by the page."""
    C = self_check(con, sp)
    real = [x for x in C["lines"] if x["kind"] != "error"]
    if not real:
        return None
    items = sorted({x["item"] for x in real if x["item"]})
    return "Stock self-check: %d thing%s to look at (%s)" % (len(real), "" if len(real) == 1 else "s", ", ".join(items[:8]) + (" …" if len(items) > 8 else ""))


# ================================================================================================================ the shell
def main(argv):
    sys.path.insert(0, HERE)
    dbp = os.environ.get("FINANCE_DB") or os.path.join(HERE, "finance.db")
    con = sqlite3.connect(dbp, timeout=60)
    try:
        ensure(con)
        SW = _sw()
        sp = SW.Spine()
        if "--check" in argv:                                 # the daily self-check: READ ONLY; one notice for the owner when it names anything
            C = self_check(con, sp)
            for x in C["lines"]:
                print("%-10s %-28s %s" % (x["kind"], x["item"][:28], x["words"]))
            real = [x for x in C["lines"] if x["kind"] != "error"]
            print("%s record_judges v%s --check: %d line(s)" % (now_iso(), VERSION, len(real)))
            if "--notice" in argv:                            # an earlier day's line retired, whatever today finds (one line, today's)
                try:
                    con.execute("UPDATE stock_watch_notice SET until=? WHERE kind='s952_check' AND until>=? AND substr(at,1,10)<?",
                                (_day_before(today().isoformat()), today().isoformat(), today().isoformat()))
                    con.commit()
                except sqlite3.Error:
                    pass
            if real and "--notice" in argv:
                try:
                    items = sorted({x["item"] for x in real if x["item"]})
                    SW.notice(con, "s952_check", "owner", "Stock self-check: %d thing%s to look at -- %s" % (len(real), "" if len(real) == 1 else "s",
                              ", ".join(items[:8]) + (" …" if len(items) > 8 else "")), ref="/finance/stockcheck/", days=1, once_key="s952check:%s" % today().isoformat())
                    con.commit()
                except Exception as ex:                       # noqa: BLE001
                    print("notice not written: %s" % ex, file=sys.stderr)
            return 0
        if "--install" in argv:                               # the one-off at the install: pairs righted, the record rebuilt, every count since 18-11 judged again
            set_switches(con, True)
            R1 = scan_repair(con, sp, who="s952-install")
            B = _sr().build(con, sp)
            waiting = {int(r[0]): dict(status=r[1], settled_at=r[2], expected_units=r[3], gap_units=r[4], basis=r[5], judge_words=r[6]) for r in con.execute(
                "SELECT id, status, settled_at, expected_units, gap_units, basis, judge_words FROM stock_point WHERE status='awaits_sales'")}
            l0 = con.execute("SELECT COALESCE(MAX(id),0) FROM stock_watch_loss_line").fetchone()[0]
            n934 = SW._s934_settle(con, sp)
            ts = now_iso()
            for pid, before in waiting.items():
                r = con.execute("SELECT status, expected_units, gap_units, basis, judge_words FROM stock_point WHERE id=?", (pid,)).fetchone()
                if r and r[0] != "awaits_sales":
                    con.execute("INSERT INTO s952_point_undo (point_id, loss_id, at, action, before_json, after_json) VALUES (?,?,?,?,?,?)",
                                (pid, None, ts, "point_settled", json.dumps(before, default=str), json.dumps(dict(zip(("status", "expected_units", "gap_units", "basis", "judge_words"), r)), default=str)))
            for (lid, pid) in con.execute("SELECT id, point_id FROM stock_watch_loss_line WHERE id>?", (l0,)).fetchall():
                con.execute("INSERT INTO s952_point_undo (point_id, loss_id, at, action, before_json, after_json) VALUES (?,?,?,?,?,?)",
                            (pid, lid, ts, "loss_created", "{}", "{}"))
            con.commit()
            R3 = rejudge_all(con, sp, who="s952-install", write=True)
            print("S952 install: pairs righted %d (listed %d) · record %s rows · counts settled to their bill %d · judged again %d (moved %d, loss lines withdrawn %d, resized %d, listed %d)" % (
                R1.get("done", 0), len(R1.get("listed") or []), B.get("n"), n934, R3["n"], R3["moved"], R3["withdrawn"], R3["resized"], len(R3["listed"])))
            return 0
        if "--rejudge" in argv:                               # S954: every count since 18-11 judged again by this version (undo rows kept)
            ts = now_iso()
            R3 = rejudge_all(con, sp, who="s954-install", write=True)
            print("S954 rejudge at %s: judged again %d (moved %d, loss lines withdrawn %d, resized %d, listed %d)" % (ts, R3["n"], R3["moved"], R3["withdrawn"], R3["resized"], len(R3["listed"])))
            return 0
        if "--undo-rejudge-from" in argv:                     # S954's undo: only the judgments it re-made (from its own moment)
            ts = argv[argv.index("--undo-rejudge-from") + 1] if len(argv) > argv.index("--undo-rejudge-from") + 1 else ""
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", ts):
                print("S954 undo refused: the moment must be YYYY-MM-DDTHH:MM:SS (got %r)" % ts)
                return 2
            n = undo_rejudge(con, who="s954-undo", from_at=ts)
            print("S954 undo: %d judgment row(s) put back" % n)
            return 0
        if "--undo" in argv:                                  # the undo's data half: the switches OFF first (no page re-applies a repair), then judgments
            set_switches(con, False)                          # and loss lines back, then the order lines; the record is rebuilt by the OLD code afterwards
            n1 = undo_rejudge(con)
            n2 = undo_repairs(con)
            print("S952 undo: switches off; %d judgment row(s) and %d order line(s) put back" % (n1, n2))
            return 0
        if "--plan" in argv:
            P = plan_repair(con, sp)
            for a in P["actions"]:
                print("%-15s line %-5s order %-4s %-24s %s" % (a["kind"], a["line_id"], a["order_id"], a["item"][:24], a["why"]))
            for x in P["listed"]:
                print("%-15s line %-5s order %-4s %-24s %s" % ("LISTED", x["line_id"], x["order_id"], x["item"][:24], x["why"]))
            return 0
        if "--judge" in argv:
            for r in rejudge_all(con, sp, write=False)["rows"]:
                print(json.dumps(r, default=str))
            return 0
    finally:
        con.close()
    print("record_judges.py --check [--notice] | --plan | --judge | --install | --undo", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
