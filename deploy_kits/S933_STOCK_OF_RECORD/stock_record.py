#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  stock_record.py  ·  v1.0  ·  kit S933_STOCK_OF_RECORD  ·  Session 504 (Sanjeevni)  ·  22-Nov-2026
#
#  THE STOCK OF RECORD -- one figure per item, written once, read everywhere (the owner's word, 22-Nov 19:28-19:33 IST: "a single truth
#  for stocks needs to populate system data"; "everywhere our system should read the stock from this place only").
#
#  What one row holds, and the rules (D-number at the close):
#    MARG      Marg's newest closing stock report, whatever date Shavez chose in it: a report printed for an earlier day stands for the END
#              of that day; a report printed on its own day in the morning stands for the end of the day BEFORE (the owner's 18-Oct rule:
#              a closing taken before the first sale is the end of yesterday) -- no hold, no verification wait (S587's start-capture hold
#              is NOT used here); a report printed on its own day from 22:00 stands for that day's end.
#              + the bills Amir keyed AFTER the print: a purchase bill dated on or before the end day whose first appearance in Amir's purchase
#                export (purchase_bill.first_seen_day, the Purchase bills page's own fact) is AFTER the print day is added whole (certain);
#                one first seen ON the print day is added only when the closing's shortfall against the record equals it (the ledger's reading,
#                made exact where the day decides); anything else is left to the Marg watch.
#              + the spine's own movements after the end day (sales, returns, purchases, reconciliations -- stock_figure.spine_move).
#    SHELF     the last count carried forward alone (stock_figure.shelf minus its arrivals) -- the count's own figure through the spine's
#              sales, purchases and vouchers after it (S928's rules: a count at or after the evening hour ends its day).
#    WAITING   deliveries on the shelf that Marg does not hold yet, each in ONE of three states read from the data (never from who worked first):
#              scan_not_in_marg (the order's scanned bill is not linked to any Marg bill: counts by the bill's quantity, the tap when unread),
#              tap_no_scan (no scan tied: the tap stands, stock_figure.carried rules a-e say Marg does not carry it), or carried (the scan is
#              linked to a Marg bill the spine holds / a Marg purchase line carries the tap) -- a carried line is NOT waiting.
#    GAP       shelf - Marg, the waiting left out of both. state: agree | look | waiting | no_shelf | marg_behind (Marg's figure would be
#              below zero: a bill is missing on Marg's side -- never shown as a gap) | consumable (the clinic's own use, loss_piles' list:
#              never a shop difference).
#  The table is REBUILT whole (one transaction) when its inputs moved: the spine's build stamp, the newest tap, tie, scan link, count point,
#  Marg bill (fingerprint()); rows() rebuilds on read when stale (a connection inside a transaction reads what is there); the cron line
#  `stock_record.py --build` keeps it fresh between reads. Readers: stock_check (the owner's Stock check page), item_ledger (the head figures);
#  kit 2 switches the count judgments, the Hub lines, the Expiry watch and the ordering engine to it.
#  English; strips:tabs by the item's pack; no patient data; no dialog anywhere.
import datetime as dt
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

VERSION = "1.0"
KIT = "S933_STOCK_OF_RECORD"
HERE = os.path.dirname(os.path.abspath(__file__))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
LATE_DAYS = 21                                              # a bill keyed after the print: dated within this many days on or before the end day
STALE_SECONDS = 6 * 3600                                    # a record older than this is rebuilt on read even with no input moved
TOL = 0.5
FINANCE_DB = os.environ.get("FINANCE_DB") or "/root/finance/finance.db"

DDL = (
    "CREATE TABLE IF NOT EXISTS stock_of_record (item TEXT PRIMARY KEY, k20 TEXT, pack INTEGER, pieces INTEGER, ortho INTEGER, consumable INTEGER, "
    "marg_units REAL, marg_closing REAL, marg_late REAL, marg_after REAL, marg_resid REAL, marg_late_json TEXT, marg_flag TEXT, "
    "shelf_units REAL, shelf_raw REAL, shelf_arrived REAL, shelf_named TEXT, base_kind TEXT, base_day TEXT, base_at TEXT, base_evening INTEGER, "
    "waiting_units REAL, waiting_json TEXT, gap_units REAL, state TEXT, words TEXT, approx INTEGER, forms_json TEXT, built_at TEXT)",
    "CREATE TABLE IF NOT EXISTS stock_record_meta (key TEXT PRIMARY KEY, value TEXT)",
)


def _sf():
    import stock_figure                                       # noqa: PLC0415 -- beside this file: the one stock function's parts
    return stock_figure


def _sw():
    import stock_watch                                        # noqa: PLC0415
    return stock_watch


def now_ist():
    return dt.datetime.now(IST).replace(microsecond=0, tzinfo=None).isoformat()


def today():
    return dt.datetime.now(IST).date()


def norm(s):
    return re.sub(r"\s+", " ", str(s or "").strip().upper())


def _has(con, t):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None
    except sqlite3.Error:
        return False


def ensure(con):
    for s in DDL:
        con.execute(s)


def _day_before(d):
    try:
        return (dt.date.fromisoformat(str(d)[:10]) - dt.timedelta(days=1)).isoformat()
    except ValueError:
        return None


def st(units, pack, signed=False):
    """'16:3' strips:tabs for a packed item, '25' pieces for pack 1; None -> '—'. signed: '+1:4' / '−2:12' / '0'."""
    if units is None:
        return "—"
    try:
        v = int(round(float(units)))
    except (TypeError, ValueError):
        return "—"
    p = int(pack or 1)
    neg = v < 0
    a = abs(v)
    body = ("%d:%d" % (a // p, a % p)) if p > 1 else "%d" % a
    if neg:
        return "−" + body
    if signed and v > 0:
        return "+" + body
    return body


def dmy(iso):
    s = str(iso or "")[:10]
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4]) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s) else s


# ------------------------------------------------------------------ the closing capture: the newest report, by the owner's rule
def capture(sp, SF=None):
    """The newest accepted FULL closing by its print stamp, with the day whose END it stands for. dict(md5, as_on, stamp, stamp_iso, print_day,
    end_day, kind) -- kind 'yesterday' (printed for an earlier day), 'morning' (printed on its own day before 22:00: the end of the day
    before), 'night' (printed on its own day from 22:00). None when the spine has none."""
    SF = SF or _sf()
    try:
        rows = sp.q("SELECT e.md5 AS md5, e.as_on AS as_on, e.stamp AS stamp FROM sp_export e WHERE e.ok=1 AND e.md5 IN (SELECT DISTINCT md5 FROM sp_close_name) "
                    "ORDER BY e.stamp DESC, e.md5 DESC")
    except sqlite3.Error:
        return None
    for r in rows:
        si = SF.stamp_iso(r["stamp"])
        as_on = str(r["as_on"] or "")[:10]
        if not si or len(as_on) != 10:
            continue
        pd, hm = si[:10], si[11:16]
        if as_on < pd:
            end, kind = as_on, "yesterday"
        elif as_on == pd:
            if hm >= "22:00":
                end, kind = as_on, "night"
            else:
                end, kind = _day_before(as_on), "morning"
        else:
            continue                                          # printed for a day after its own print: not a closing anyone can stand on
        if not end:
            continue
        return dict(md5=str(r["md5"]), as_on=as_on, stamp=str(r["stamp"] or ""), stamp_iso=si, print_day=pd, end_day=end, kind=kind)
    return None


def _first_seen(con, SW):
    """{(supkey, bill, bill_date): first_seen_day} from the Purchase bills page's register (purchase_bill) -- both the normalised and the printed
    supplier name reach the key. {} without the table."""
    out = {}
    if not _has(con, "purchase_bill"):
        return out
    sk = SW.supkey
    try:
        for sn, sup, bno, bdt, fs in con.execute("SELECT supplier_norm, supplier, bill_no, bill_date, first_seen_day FROM purchase_bill WHERE COALESCE(first_seen_day,'')<>''"):
            b = _bill(bno)
            d = str(bdt or "")[:10]
            for key in {(sk(sn), b, d), (sk(sup), b, d)}:
                if key[0]:
                    out[key] = min(str(fs)[:10], out.get(key, "9999-12-31"))
    except sqlite3.Error:
        pass
    return out


def _bill(b):
    """A bill number as a key, exactly as stock_figure._bill folds it: spacing and case folded, leading zeros before a digit dropped."""
    return re.sub(r"^0+(?=\d)", "", re.sub(r"\s+", "", str(b or "")).upper())


def late_hi(cap):
    """The last bill date the print could have missed: the end day -- or, for a morning print, its own print day (a bill dated the print day keyed
    before the print is inside it; keyed after, it is not: the same first-seen / shortfall reading decides, R2-B3 made exact)."""
    return cap["as_on"] if cap.get("kind") == "morning" else cap["end_day"]


def _late_bills(sp, k, cap, first_seen, resid):
    """The purchase bills (and returns, signed) of the key dated within LATE_DAYS on or before late_hi(cap), each with its first-seen day; the
    ones Marg's print did not hold: certain (first seen after the print day) added whole -- unless the closing's SURPLUS over the record equals
    them (then the print held them after all: Amir keyed before the print and exported after it, F-series S504); the ones first seen ON the
    print day only when they close the closing's shortfall (resid, negative when Marg is below the record) singly or in pairs.
    Returns (chosen rows, remainder of resid, candidates)."""
    hi = late_hi(cap)
    lo = (dt.date.fromisoformat(hi) - dt.timedelta(days=LATE_DAYS)).isoformat()
    try:
        rows = sp.q("SELECT l.supkey AS supkey, l.bill AS bill, l.date AS date, SUM(CASE WHEN l.direction IN ('RETURN','PURCHASE_RETURN') THEN -l.units ELSE l.units END) AS units, "
                    "MAX(b.supplier) AS supplier FROM sp_purchase_line l LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date "
                    "WHERE l.k20=? AND l.direction IN ('PURCHASE','RETURN','PURCHASE_RETURN') AND l.date<=? AND l.date>=? GROUP BY l.supkey, l.bill, l.date ORDER BY l.date, l.bill", k, hi, lo)
    except sqlite3.Error:
        rows = []
    cands = []
    for r in rows:
        fs = first_seen.get((str(r["supkey"] or ""), _bill(r["bill"]), str(r["date"] or "")[:10]))
        cands.append(dict(supkey=str(r["supkey"] or ""), supplier=str(r["supplier"] or r["supkey"] or ""), bill=str(r["bill"] or ""), date=str(r["date"] or "")[:10],
                          units=float(r["units"] or 0), first_seen=fs or "", how=("after" if (fs and fs > cap["print_day"]) else ("same_day" if fs == cap["print_day"] else "before"))))
    chosen = [c for c in cands if c["how"] == "after"]
    rem = float(resid or 0) + sum(c["units"] for c in chosen)          # what the shortfall still leaves after the certain ones
    if chosen and rem >= TOL:                                          # the print held one of them after all: the surplus names it (singly or in pairs)
        drop = None
        for c in chosen:
            if abs(rem - c["units"]) < TOL:
                drop = [c]
                break
        if drop is None:
            for i in range(len(chosen)):
                for j in range(i + 1, len(chosen)):
                    if abs(rem - chosen[i]["units"] - chosen[j]["units"]) < TOL:
                        drop = [chosen[i], chosen[j]]
                        break
                if drop:
                    break
        if drop:
            for c in drop:
                c["how"] = "after_but_inside"
            chosen = [c for c in chosen if c not in drop]
            rem -= sum(c["units"] for c in drop)
    maybe = [c for c in cands if c["how"] == "same_day"]
    if maybe and abs(rem) >= TOL:
        pick = None
        for c in maybe:
            if abs(rem + c["units"]) < TOL:
                pick = [c]
                break
        if pick is None:
            for i in range(len(maybe)):
                for j in range(i + 1, len(maybe)):
                    if abs(rem + maybe[i]["units"] + maybe[j]["units"]) < TOL:
                        pick = [maybe[i], maybe[j]]
                        break
                if pick:
                    break
        if pick:
            for c in pick:
                c["how"] = "same_day_matched"
            chosen += pick
            rem += sum(c["units"] for c in pick)
    return chosen, rem, cands


def _consumables(con, SF, sp, ctx):
    out = set()
    try:
        import loss_piles                                     # noqa: PLC0415 -- beside this file
        for nm in loss_piles.settings(con).get("consume_items") or []:
            out.add(norm(nm))
            try:
                out.add(("k", SF.key_of(sp, nm, ctx)))
            except Exception:                                 # noqa: BLE001
                pass
    except Exception:                                         # noqa: BLE001
        pass
    return out


def _ortho(con):
    try:
        return {norm(r[0]) for r in con.execute("SELECT item FROM stock_item_section WHERE section='Orthotics'")} if _has(con, "stock_item_section") else set()
    except sqlite3.Error:
        return set()


# ------------------------------------------------------------------ the deliveries: one of three states, from the data
def _scan_links(con):
    """{asset_bill_id: (supkey, bill, date)} -- every scan linked to a Marg bill in the purchase register."""
    out = {}
    if not (_has(con, "purchase_scan_link") and _has(con, "purchase_bill")):
        return out
    sk = _sw().supkey
    try:
        for aid, sn, sup, bno, bdt in con.execute("SELECT l.asset_bill_id, b.supplier_norm, b.supplier, b.bill_no, b.bill_date FROM purchase_scan_link l JOIN purchase_bill b ON b.id=l.bill_id"):
            out[int(aid)] = (sk(sn) or sk(sup), _bill(bno), str(bdt or "")[:10], sk(sup))
    except sqlite3.Error:
        pass
    return out


def _order_scans(con):
    """{order_id: [(asset_bill_id, stamp), ...]} -- every scan tied to an order, arrived or not (the tie is the fact; S928's arrived=1 gate is not applied here)."""
    out = {}
    if not _has(con, "order_scan_tie"):
        return out
    try:
        for oid, aid, stp in con.execute("SELECT order_id, asset_bill_id, stamp FROM order_scan_tie WHERE asset_bill_id IS NOT NULL"):
            out.setdefault(int(oid), []).append((int(aid), str(stp or "")))
    except sqlite3.Error:
        pass
    return out


def _spine_bills(sp):
    """{(supkey, bill, date)} the spine's purchase bills (Amir's keyed bills)."""
    try:
        return {(str(r["supkey"] or ""), _bill(r["bill"]), str(r["date"] or "")[:10]) for r in sp.q("SELECT supkey, bill, date FROM sp_purchase_bill")}
    except sqlite3.Error:
        return set()


def waiting_lines(con, sp, SF, SW, name, since_at, base_kind, ctx, X):
    """The item's arrival lines (taps and scan-tied lines) that are NOT in Marg yet, each with its state and the bill's word. X: the build's
    shared lookups (scan_links, order_scans, spine_bills)."""
    out = []
    try:
        lines = [a for a in SW._arrivals(con, name, str(since_at or ""), sp, ctx=ctx) if not str(a.get("billed_bill_no") or "").strip()]
        lines += SF.scan_lines(con, sp, name, (str(since_at or "")[:10] if base_kind == "count" else str(since_at or "")), ctx)
    except Exception:                                         # noqa: BLE001
        return out
    seen = set()
    for a in lines:
        lid = a.get("line_id")
        if lid in seen:
            continue
        seen.add(lid)
        try:
            if SF.expired(con, sp, a, ctx):
                continue                                      # Amir's board carries it (bill entry baaki); not the shelf's
        except Exception:                                     # noqa: BLE001
            continue
        oid = int(a.get("order_id") or 0)
        ties = X["order_scans"].get(oid, [])
        sids = [t[0] for t in ties]
        ps = int(a.get("pack_size") or 1) or 1
        tap = float(a.get("units") or 0)
        b = None
        try:
            b = SF.bill_units(con, sp, a, ctx) if hasattr(SF, "bill_units") else None
        except Exception:                                     # noqa: BLE001
            b = None
        bill_u = float(b["units"]) if (b is not None and b.get("units") is not None) else None
        if sids:
            linked = [X["scan_links"][s] for s in sids if s in X["scan_links"]]
            in_marg = [L for L in linked if (L[0], L[1], L[2]) in X["spine_bills"] or (L[3], L[1], L[2]) in X["spine_bills"]]
            if in_marg:
                continue                                      # carried: the scan's Marg bill is keyed (state 3) -- the spine's purchase has it on both sides
            try:
                if SF.carried(con, sp, a, ctx) is not None:
                    continue                                  # the link not made yet, but a Marg purchase line carries the tap (rules a-e): carried
            except Exception:                                 # noqa: BLE001
                pass
            if b is not None and b.get("on_bill") is False:
                units, word = 0.0, "tapped %s, NOT on the scanned bill — counts nothing" % st(tap, ps)
            elif bill_u is not None:
                units = bill_u
                word = ("scanned, bill says %s" % st(bill_u, ps)) + ((" · tapped %s — %s short, back on %s's next order" % (st(tap, ps), st(tap - bill_u, ps), (str(a.get("vendor") or "").split() or ["the dealer"])[0]))
                                                               if (tap and bill_u < tap - TOL) else (" · tapped %s" % st(tap, ps) if tap and abs(tap - bill_u) >= TOL else ""))
            elif not X.get("bill_over_tap", True):
                units, word = tap, "tapped %s (the bill-over-tap switch is off: the tap stands)" % st(tap, ps)
            else:
                units, word = tap, ("scanned, the quantity not read yet · tapped %s" % st(tap, ps) if a.get("kind") != "scan" else "scanned, the quantity not read yet")
            state = "scan_not_in_marg"
            stamp = next((t[1] for t in ties if b and t[0] == b.get("scan_id") and t[1]), "") or next((t[1] for t in ties if t[1]), "") or (("B-%s" % b.get("scan_id")) if (b and b.get("scan_id")) else "")
            word += " · waiting for Amir's Marg entry"
        else:
            try:
                if SF.carried(con, sp, a, ctx) is not None:
                    continue                                  # a Marg purchase line carries the tap (rules a-e)
            except Exception:                                 # noqa: BLE001
                continue
            units, state, stamp = tap, "tap_no_scan", ""
            word = "tapped %s, no scan yet · waiting for the bill" % st(tap, ps)
        out.append(dict(line_id=lid, vendor=a.get("vendor") or "", kind=a.get("kind") or "tap", at=str(a.get("arrived_at") or a.get("scan_at") or "")[:16],
                        units=units, tap=tap, bill=bill_u, stamp=stamp, state=state, word=word, pack=ps,
                        short=(bill_u - tap) if (bill_u is not None and tap and bill_u < tap - TOL) else 0.0))
    return out


# ------------------------------------------------------------------ the build
def fingerprint(con, sp):
    """What the record depends on: the spine's build stamp, the newest tap, tie, scan link, count point, Marg bill, the settings' rows."""
    parts = []
    try:
        parts.append(str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or ""))
    except Exception:                                         # noqa: BLE001
        parts.append("")
    for sql in ("SELECT MAX(arrived_at) FROM purchase_order_line", "SELECT MAX(tied_at) FROM order_scan_tie", "SELECT MAX(linked_at) FROM purchase_scan_link",
                "SELECT MAX(id) FROM stock_point", "SELECT COUNT(*) || MAX(first_seen_day) FROM purchase_bill",
                "SELECT GROUP_CONCAT(key || '=' || value) FROM (SELECT key, value FROM setting WHERE key LIKE 'count.%' OR key LIKE 'arrival.%' OR key LIKE 'stock.consume%' ORDER BY key)",
                "SELECT MAX(id) FROM stock_count_item", "SELECT MAX(rowid) FROM marg_item_rename"):
        try:
            parts.append(str(con.execute(sql).fetchone()[0]))
        except sqlite3.Error:
            parts.append("-")
    try:                                                      # the scans' readings (assets.db): a new reading moves the waiting lines
        import purchase_app as PA                             # noqa: PLC0415
        ac = PA._assets_con()
        if ac is not None:
            try:
                parts.append(str(tuple(ac.execute("SELECT COUNT(*), MAX(at) FROM claude_reading").fetchone())))
            finally:
                ac.close()
    except Exception:                                         # noqa: BLE001
        parts.append("~")
    return hashlib.md5("|".join(parts).encode("utf-8")).hexdigest()


def meta(con):
    if not _has(con, "stock_record_meta"):
        return {}
    try:
        return dict(con.execute("SELECT key, value FROM stock_record_meta").fetchall())
    except sqlite3.Error:
        return {}


def _may_write(con):
    try:
        return con is not None and not con.in_transaction
    except Exception:                                         # noqa: BLE001
        return False


def build(con, sp=None, log=None):
    """Rebuild the whole record in one transaction. Returns dict(ok, n, took, cap, reason)."""
    t0 = time.monotonic()
    SF, SW = _sf(), _sw()
    ensure(con)
    if not _may_write(con):
        return dict(ok=False, reason="the connection is inside a transaction; nothing written", n=0)
    sp = sp or SW.Spine()
    if not SF.ready(sp):
        return dict(ok=False, reason="the spine's closing table is not ready", n=0)
    ctx = SF.Ctx(con, sp)
    cap = capture(sp, SF)
    if cap is None:
        return dict(ok=False, reason="no closing report in the spine", n=0)
    S = SW.settings(con)
    first_seen = _first_seen(con, SW)
    X = dict(scan_links=_scan_links(con), order_scans=_order_scans(con), spine_bills=_spine_bills(sp), bill_over_tap=bool(S.get("bill_over_tap", True)))
    cons = _consumables(con, SF, sp, ctx)
    ortho = _ortho(con)
    by_n, _by_k = SF._cn_rows(sp, cap["md5"], ctx)
    try:
        R = SF.reach(sp)
    except Exception:                                         # noqa: BLE001
        R = {}
    sale_day_keys = set()
    if cap["kind"] == "morning" and str(R.get("last_sale") or "") >= cap["as_on"]:
        try:
            sale_day_keys = {str(r["k20"]) for r in sp.q("SELECT DISTINCT k20 FROM sp_move WHERE kind='SALE' AND date=?", cap["as_on"])}
        except sqlite3.Error:
            sale_day_keys = set()
    hi = late_hi(cap)
    t_iso = today().isoformat()
    built = now_ist()
    rows, covered, errs = [], set(), 0

    def one(n, forms, closing, packs, printed):
        """One row: the Marg figure, the shelf, the waiting lines, the state and the words. printed=False: a counted name Marg prints no stock for (closing 0)."""
        k = SF.key_of(sp, n, ctx)
        flags = []
        try:
            sx = SF.split_of(sp, n, ctx)                      # S613 (F-951): a split size is figured on its own key
        except Exception:                                     # noqa: BLE001
            sx = None
        if sx is not None:
            k = sx["new_k"]
            if cap["end_day"] < str(sx.get("day") or ""):
                flags.append("split_before")                  # the print is older than the split: the old key's shared history -- approximate
        pack = int(SF.pack_of(con, sp, n, ctx)[0] or 1)
        bal = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND date<=?", k, cap["end_day"])
        bal_end = float(bal[0]["u"] or 0) if bal else 0.0
        resid = closing - bal_end
        late, rem, cands = _late_bills(sp, k, cap, first_seen, resid)
        late_u = float(sum(c["units"] for c in late))
        after = float(SF.spine_move(sp, k, cap["end_day"], t_iso))
        if hi > cap["end_day"]:                               # a morning print: the bills dated its own day are judged with the late ones, never twice
            pd = sp.q("SELECT COALESCE(SUM(units),0) AS u FROM sp_move WHERE k20=? AND kind IN ('PURCHASE','PURCHASE_RETURN') AND date>? AND date<=?", k, cap["end_day"], hi)
            after -= float(pd[0]["u"] or 0) if pd else 0.0
        marg = closing + late_u + after
        try:
            fam = SF.family(sp, k, cap["md5"], ctx)
        except Exception:                                     # noqa: BLE001
            fam = [n]
        if packs > 1 or len(fam) > 1:
            flags.append("family")
        if k in sale_day_keys:
            flags.append("sold_before_print")
        if abs(rem) >= TOL:
            flags.append("marg_moved_unrecorded")
        if not printed:
            flags.append("not_printed")
        Sh = SF.shelf(con, sp, n, None, ctx)
        shelf_raw, arrived, named = Sh.get("shelf"), float(Sh.get("arrived") or 0), Sh.get("named")
        if shelf_raw is None:
            core = None
        elif named == "below_zero":
            core = 0                                          # the count carried forward went below zero: the shelf stands at nothing; judged, with its note
        else:
            core = int(round(shelf_raw - arrived))
        W = waiting_lines(con, sp, SF, SW, n, Sh.get("base_at") or "", Sh.get("base_kind") or "count", ctx, X)   # a counted item: arrivals after its count (the count holds the earlier ones); uncounted: every arrival not expired (Marg's print holds only what Amir keyed)
        wait_u = float(sum(w["units"] for w in W))
        is_cons = norm(n) in cons or ("k", k) in cons or any(norm(f) in cons for f in forms)
        is_ortho = norm(n) in ortho or any(norm(f) in ortho for f in forms)
        margi = int(round(marg))
        words = []
        if late:
            words.append("Marg's figure includes " + "; ".join("bill %s (%s, %s) keyed after the print" % (c["bill"], (str(c["supplier"] or c["supkey"]).split() or ["?"])[0], dmy(c["date"])) for c in late))
        if not printed:
            words.append("Marg prints no stock for it (zero) — the count carried forward is judged against zero")
        if "split_before" in flags:
            words.append("a size of a split name; the print is older than the split — approximate")
        if "sold_before_print" in flags:
            words.append("a sale on the report's own day may sit inside the report — approximate until tomorrow's report")
        if "marg_moved_unrecorded" in flags:
            words.append("Marg's closing differs from the record by %s with no bill or sale to show for it — the Marg watch's line" % st(rem, pack, signed=True))
        if named == "below_zero":
            words.append("the count carried forward went below zero (a purchase not yet in Marg, or a count to redo) — the shelf stands at 0 here")
        if margi < 0:
            state, gap = "marg_behind", None
            words.insert(0, "Marg's figure would be %s — a bill Marg holds is not in the record yet, or a bill is not keyed; no gap is judged" % st(margi, pack))
        elif core is None:
            state, gap = "no_shelf", None
        else:
            gap = core - margi
            if is_cons:
                state = "consumable"
                words.append("the clinic's own consumable — used without sale bills; not a shop difference")
            elif W:
                state = "waiting"
            else:
                state = "agree" if gap == 0 else "look"
        return (n, k, pack, int(pack <= 1), int(is_ortho), int(is_cons), float(margi), closing, late_u, after, rem, json.dumps(late, ensure_ascii=False),
                ",".join(flags), (float(core) if core is not None else None), (float(shelf_raw) if shelf_raw is not None else None), arrived, named or "",
                Sh.get("base_kind") or "", Sh.get("base_day") or "", Sh.get("base_at") or "", int(bool(Sh.get("base_evening"))),
                wait_u, json.dumps(W, ensure_ascii=False), (float(gap) if gap is not None else None), state, " · ".join(words), int(bool(flags)),
                json.dumps([f for f in forms if norm(f) != norm(n)], ensure_ascii=False), built)

    names = sorted({str(r["name"]) for r in sp.q("SELECT DISTINCT name FROM sp_close_name WHERE md5=?", cap["md5"]) if r["name"]})
    for n in names:
        try:
            forms = list(SF.printed_forms(con, n, ctx))
        except Exception:                                     # noqa: BLE001
            forms = [n]
        if norm(n) in covered:
            continue                                          # a rename partner already read under its Marg name (one row per medicine)
        covered.update(norm(f) for f in forms)
        covered.add(norm(n))
        try:
            hits = []
            for f in forms:
                hits.extend(by_n.get(norm(f), []))
            if not hits:
                continue
            rows.append(one(n, forms, float(sum(u for (_n, _p, u, _k) in hits)), len({p for (_n, p, _u, _k) in hits}), True))
        except Exception as ex:                               # noqa: BLE001 -- one item never takes the record down
            errs += 1
            if log:
                log("stock_record: %s skipped: %s: %s" % (n, type(ex).__name__, str(ex)[:120]))
    # the counted names the print does not carry: an item at ZERO in Marg (Marg prints only items with stock) is judged against zero when the spine
    # knows the name (sp_item, first seen on or before the print) -- stock_figure.closing()'s by='absent' rule; a name the spine never knew stays
    # the page's 'count names Marg no longer prints'
    try:
        counted = set(SF.count_family(con, ctx)) | {str(p.get("item") or nm) for nm, p in SF.points(con, ctx).items()}   # the full count's names and the spot points'
    except Exception:                                         # noqa: BLE001
        counted = set()
    for c in sorted(counted):
        if norm(c) in covered:
            continue
        try:
            k = SF.key_of(sp, c, ctx)
            fs = sp.q("SELECT MIN(first_seen) AS f FROM sp_item WHERE k20=?", k)
            f = str((fs[0]["f"] if fs else "") or "")
            if not f or f > cap["as_on"]:
                continue
            try:
                forms = list(SF.printed_forms(con, c, ctx))
            except Exception:                                 # noqa: BLE001
                forms = [c]
            covered.update(norm(x) for x in forms)
            covered.add(norm(c))
            rows.append(one(c, forms, 0.0, 1, False))
        except Exception as ex:                               # noqa: BLE001
            errs += 1
            if log:
                log("stock_record: %s (counted, not printed) skipped: %s: %s" % (c, type(ex).__name__, str(ex)[:120]))
    took = round(time.monotonic() - t0, 1)
    fp = fingerprint(con, sp)
    try:
        con.execute("BEGIN")
        con.execute("DELETE FROM stock_of_record")
        con.executemany("INSERT INTO stock_of_record VALUES (" + ",".join("?" * 29) + ")", rows)
        M = dict(built_at=built, fingerprint=fp, cap_md5=cap["md5"], cap_as_on=cap["as_on"], cap_end_day=cap["end_day"], cap_stamp_iso=cap["stamp_iso"], cap_kind=cap["kind"],
                 sale_to=str(R.get("last_sale") or ""), purchase_to=str(R.get("last_pur") or ""), n_rows=str(len(rows)), n_errors=str(errs), took_s=str(took),
                 spine_built=str((sp.q("SELECT value FROM sp_meta WHERE key='built'") or [{"value": ""}])[0]["value"] or ""), version=VERSION)
        con.executemany("INSERT OR REPLACE INTO stock_record_meta VALUES (?,?)", list(M.items()))
        con.commit()
    except sqlite3.Error as ex:
        try:
            con.rollback()
        except sqlite3.Error:
            pass
        return dict(ok=False, reason="write failed: %s" % str(ex)[:120], n=len(rows))
    return dict(ok=True, n=len(rows), errors=errs, took=took, cap=cap, built_at=built)


def is_stale(con, sp):
    M = meta(con)
    if not M.get("built_at"):
        return True
    try:
        age = (dt.datetime.fromisoformat(now_ist()) - dt.datetime.fromisoformat(M["built_at"])).total_seconds()
    except ValueError:
        return True
    if age > STALE_SECONDS:
        return True
    return M.get("fingerprint") != fingerprint(con, sp)


def rows(con, sp=None, refresh="auto"):
    """Every row of the record as dicts (waiting / late / forms decoded). refresh: 'auto' rebuilds when stale and the connection may write;
    'never' reads what is there; 'force' rebuilds. Returns (rows, meta)."""
    SW = _sw()
    ensure(con)
    sp = sp or SW.Spine()
    if refresh == "force" or (refresh == "auto" and _may_write(con) and is_stale(con, sp)):
        try:
            build(con, sp)
        except Exception as ex:                               # noqa: BLE001 -- a failed rebuild leaves the last record standing
            print("stock_record: rebuild failed: %r" % (ex,), file=sys.stderr)
    out = []
    rf = con.row_factory
    try:
        con.row_factory = sqlite3.Row
        for r in con.execute("SELECT * FROM stock_of_record ORDER BY item"):
            d = dict(r)
            for f, g in (("marg_late_json", "late"), ("waiting_json", "waiting"), ("forms_json", "forms")):
                try:
                    d[g] = json.loads(d.pop(f) or "[]")
                except (TypeError, ValueError):
                    d[g] = []
            out.append(d)
    finally:
        con.row_factory = rf
    return out, meta(con)


def row(con, name, sp=None, refresh="auto"):
    """One item's row by its Marg name, a printed form, or its key; None when the record has no such item."""
    sp = sp or _sw().Spine()
    rs, _M = rows(con, sp, refresh)
    nn = norm(name)
    for d in rs:
        if norm(d["item"]) == nn or d["k20"] == str(name) or any(norm(f) == nn for f in d.get("forms") or []):
            return d
    try:
        k = _sf().key_of(sp or _sw().Spine(), name)
        for d in rs:
            if d["k20"] == k:
                return d
    except Exception:                                         # noqa: BLE001
        pass
    return None


def words_for(d):
    """The record's own one-line reading of a row, for any page."""
    if d is None:
        return "not in the stock record"
    return d.get("words") or {"agree": "the shelf and Marg agree", "look": "the shelf and Marg differ", "waiting": "a delivery waits for Marg",
                              "no_shelf": "no count yet", "marg_behind": "Marg's figure is behind a bill", "consumable": "a clinic consumable"}.get(d.get("state"), "")


# ------------------------------------------------------------------ the cron / the shell
def main(argv):
    if "--build" in argv or "--check" in argv or "--force" in argv:
        sys.path.insert(0, HERE)
        con = sqlite3.connect(os.environ.get("FINANCE_DB") or FINANCE_DB, timeout=30)
        try:
            SW = _sw()
            sp = SW.Spine()
            if "--check" in argv:
                M = meta(con)
                print("stock_record v%s: built %s · closing %s (%s, the end of %s) · %s rows · stale=%s" % (VERSION, M.get("built_at", "never"), M.get("cap_as_on", "—"), M.get("cap_kind", "—"),
                                                                                                        M.get("cap_end_day", "—"), M.get("n_rows", "0"), is_stale(con, sp)))
                return 0
            ensure(con)
            if "--force" not in argv and not is_stale(con, sp):
                return 0                                      # fresh: nothing to do, nothing printed (the cron runs every ten minutes)
            r = build(con, sp, log=lambda s: print(s, file=sys.stderr))
            print("%s stock_record v%s: %s" % (now_ist(), VERSION, json.dumps({k: v for k, v in r.items() if k != "cap"}, default=str)))
            return 0 if r.get("ok") else 2
        finally:
            con.close()
    print("stock_record.py --build [--force] | --check", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
