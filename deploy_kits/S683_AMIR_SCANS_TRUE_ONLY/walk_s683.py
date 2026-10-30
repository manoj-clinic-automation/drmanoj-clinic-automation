#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s683.py -- the walk of kit S683_AMIR_SCANS_TRUE_ONLY.

    python3 -B walk_s683.py --new <root> --lib <root> --db <copy> --scratch <dir>           the walk (the file under test)
    python3 -B walk_s683.py --old <root> --lib <root> --db <copy> --scratch <dir>           the control: the live file must go red
    python3 -B walk_s683.py --proof --old-root <root> --new <root> --lib <root> --db <copy> --scratch <dir> [--assets <assets.db>]

<root>/finance/purchase_app.py is the file under test; --lib is where its neighbours live.  --db is a WRITABLE COPY of finance.db (never
the live one): the walk writes only its OWN rows -- suppliers WALKSIX / WALKTWO PHARMA, export md5 'walk683e1', scan ids 9683001..9683099,
purchase_month 2099-01 -- found by key, never by counting (F-998), and removes them again.  The scans themselves are the walk's own list
(scans_for_amir's reader of assets.db is replaced, and the matcher's re-match is not run).
--proof: on the copy's REAL rows and the REAL scans (assets.db, read only), scans_for_amir under the OLD and the NEW file: the new list
is a part of the old one; every scan that left it is held with an S683 reason; every scan the old file held is held alike.
Last line: "N of N green" (walk), "K S683 check(s) red . M green" (control) or "proof: ..." (proof).
"""
import argparse
import importlib.util
import os
import shutil
import sqlite3
import sys

MD5E = "walk683e1"
SIX, TWO = "WALKSIX PHARMA", "WALKTWO PHARMA          BAREILLY"
SID0 = 9683000


def load(root, lib, scratch, tag):
    mod_dir = os.path.join(scratch, "mod_" + tag)
    os.makedirs(mod_dir, exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "purchase_app.py"), os.path.join(mod_dir, "purchase_app.py"))
    for p in (os.path.join(lib, "finance"), os.path.join(lib, "finance", "spine")):
        if p not in sys.path:
            sys.path.append(p)
    spec = importlib.util.spec_from_file_location("purchase_app_" + tag, os.path.join(mod_dir, "purchase_app.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def clean(cx):
    ids = [r[0] for r in cx.execute("SELECT id FROM purchase_bill WHERE supplier IN (?,?)", (SIX, TWO))]
    for i in ids:
        cx.execute("DELETE FROM purchase_scan_link WHERE bill_id=?", (i,))
    cx.execute("DELETE FROM purchase_bill WHERE supplier IN (?,?)", (SIX, TWO))
    cx.execute("DELETE FROM purchase_export WHERE md5=?", (MD5E,))
    cx.execute("DELETE FROM purchase_scan_link WHERE asset_bill_id BETWEEN ? AND ?", (SID0, SID0 + 99))
    cx.execute("DELETE FROM purchase_scan_state WHERE asset_bill_id BETWEEN ? AND ?", (SID0, SID0 + 99))
    cx.execute("DELETE FROM purchase_month WHERE month='2099-01' AND finalised_by='WALK683'")
    cx.commit()


def bill(cx, sup, no, day, amt, scan=None, scan_bill_id=None):
    cx.execute("INSERT INTO purchase_bill (supplier_norm, supplier, bill_no, bill_date, month, amount_p, source_md5, bw_md5, bw_amount_p) "
               "VALUES (?,?,?,?,?,?,?,?,?)", (sup.split()[0], sup, no, day, day[:7], amt, MD5E, MD5E, amt))
    bid = cx.execute("SELECT id FROM purchase_bill WHERE supplier=? AND bill_no=? AND bill_date=?", (sup, no, day)).fetchone()[0]
    if scan_bill_id:
        cx.execute("UPDATE purchase_bill SET scan_bill_id=? WHERE id=?", (SID0 + scan_bill_id, bid))
    if scan:
        cx.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)",
                   (bid, SID0 + scan, "EXACT", "walk683", "2099-01-01T00:00:00"))
    return bid


def seed(cx):
    clean(cx)
    cx.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, superseded_by) "
               "VALUES (?,?,?,?,?,?,?,?,NULL)", (MD5E, "BILLWISE", "WALK683.XLS", "2099-01-01", "2099-03-31", "20990331-090000",
                                                  "2099-03-31T09:00:00", 9))
    cx.execute("INSERT INTO purchase_month (month, status, finalised_by, finalised_at) VALUES ('2099-01','final','WALK683','2099-02-01T00:00:00')")
    bill(cx, SIX, "783473", "2099-01-07", 84100, scan=90)      # January (final)
    bill(cx, SIX, "783473", "2099-03-07", 84100, scan=91)      # M1 -- has its scan
    bill(cx, SIX, "3499", "2099-03-03", 474700, scan=92)       # M2 -- has its scan
    bill(cx, SIX, "14538", "2099-03-20", 159700)               # M3 -- NO scan
    bill(cx, SIX, "9001", "2099-03-25", 50000)                 # M4 -- NO scan
    bill(cx, TWO, "50", "2099-01-02", 10000, scan=93)
    bill(cx, TWO, "60", "2099-03-10", 20000)                   # NO scan
    bill(cx, SIX, "A000678", "2099-03-22", 1292200, scan=94)   # has its scan; the OCR adds a digit (A0006678)
    bill(cx, TWO, "T5678", "2099-03-24", 30000, scan=95)       # has its scan; a paper 5 days later ends alike
    bill(cx, SIX, "220", "2099-03-14", 70000, scan=96)         # a sequential supplier: the next bill 222 is genuinely new
    bill(cx, SIX, "4444", "2099-03-26", 80000, scan_bill_id=97)  # its scan known by purchase_bill.scan_bill_id only
    cx.execute("INSERT INTO purchase_scan_state (asset_bill_id, why, detail, checked_at) VALUES (?,?,?,?)",
               (SID0 + 20, "dup", "walk683 second scan", "2099-03-01T00:00:00"))
    cx.commit()


def scan(n, vendor, no, bdate, created, amt=None):
    return dict(id=SID0 + n, stamp_no="W-%02d" % n, vendor=vendor, bill_no=no, bill_date=bdate, created_at=created + " 10:00:00",
                total_amount=amt, submitted_by="Reception")


SCANS = [
    scan(1, "WALKSIX PHARMA", "KT-078347", "2099-01-07", "2099-01-29", 842.70),     # final month
    scan(2, "WALKSIX PHARMA", "GST/2023-24/412", "2023-05-20", "2099-01-29", 29700),  # an old paper, scanned in a final month
    scan(3, "WALKSIX PHARMA", "KT-078347", "2099-03-07", "2099-03-07", 842.70),      # M1: second scan, number misread
    scan(4, "WALKSIX PHARMA", "SF 003499", "", "2099-03-03"),                        # M2: second scan, the same number
    scan(5, "WALKSIX PHARMA", "GST/2023-24/412", "2023-05-20", "2099-03-20", 29700),  # M3: near an unscanned bill
    scan(6, "WALKSIX PHARMA", "9001", "2099-03-25", "2099-03-25", 1.0),               # M4: Marg has it, not yet paired
    scan(7, "WALKSIX PHARMA", "A0006678", "2099-03-12", "2099-03-12", 615.32),        # G1: genuinely missing
    scan(8, "WALKTWO PHARMA", "77", "2099-03-28", "2099-03-28", 100),                 # G2: genuinely missing
    scan(9, "WALKTWO PHARMA", "88", "2099-03-18", "2099-03-18", 100),                 # G3: the unscanned bill is 8 days away
    scan(10, "WALKTWO PHARMA", "99", "2099-03-16", "2099-03-16", 100),                # G4: the unscanned bill is 6 days away
    scan(11, "WALKSIX PHARMA", "A0006678", "2099-04-12", "2099-03-21", 615.32),      # second scan, a digit added, the day 1 away
    scan(12, "WALKTWO PHARMA", "X91678", "2099-03-29", "2099-03-29", 100),            # last 3 alike but 5 days away: stays
    scan(13, "WALKTWO PHARMA", "Z777", "2099-01-30", "2099-02-02", 100),             # paper date in a final month, scanned in an open one
    scan(14, "WALKSIX PHARMA", "4444", "2099-03-26", "2099-03-27", 800),              # second scan via scan_bill_id
    scan(15, "WALKSIX PHARMA", "222", "2099-03-16", "2099-03-16", 700),               # genuinely new, 2 days after bill 220
    scan(20, "WALKTWO PHARMA", "500", "2099-03-20", "2099-03-20", 100),               # S452's own hold first: a second scan
    scan(21, "NOBODY KNOWN TRADERS", "501", "2099-03-20", "2099-03-20", 100),         # S452's own hold first: supplier unknown
]


def run(m, cx):
    m._rematch_if_changed = lambda con, who="x": None
    m._s452_scan_rows = lambda: [dict(s) for s in SCANS]
    r = m.scans_for_amir(cx)
    L = {x["id"] - SID0: x for x in r["list"]}
    H = {x["id"] - SID0: x.get("held") for x in r["held"]}
    return r, L, H


def walk(m, cx):
    seed(cx)
    try:
        r, L, H = run(m, cx)
        c = []
        c.append(("a scan of a FINALISED month is held", H.get(1) == "month finalised"))
        c.append(("an old paper scanned in a finalised month is held", H.get(2) == "month finalised"))
        c.append(("a second scan, number misread (78347 / 783473), is held", H.get(3) == "in Marg: second scan of bill 783473"))
        c.append(("a second scan, the same number (SF 003499 / 3499), is held", H.get(4) == "in Marg: second scan of bill 3499"))
        c.append(("a paper near an unscanned Marg bill, number and amount unlike, stays on the list (no 'nearby' rule)", 5 in L))
        c.append(("a paper whose number Marg has, not yet paired, is held", H.get(6) == "in Marg: bill 9001 not yet paired"))
        c.append(("a paper Marg does not have (only 3 digits alike) stays on the list", 7 in L))
        c.append(("a paper Marg does not have stays on the list", 8 in L))
        c.append(("an unscanned bill 8 days away does not hold it", 9 in L))
        c.append(("an unscanned bill 6 days away does not hold it", 10 in L))
        c.append(("a misread paper date in a finalised month does not hide an open month's scan", 13 in L))
        c.append(("a second scan known only by purchase_bill.scan_bill_id is held", H.get(14) == "in Marg: second scan of bill 4444"))
        c.append(("a sequential supplier's next bill, 2 days on, stays on the list", 15 in L))
        c.append(("a second scan whose number gained a digit, a day from the bill, is held", H.get(11) == "in Marg: second scan of bill A000678"))
        c.append(("last three digits alike but 5 days away does not hold it", 12 in L))
        c.append(("the list is exactly the eight it should be", sorted(L) == [5, 7, 8, 9, 10, 12, 13, 15]))
        c.append(("S452's second scan still held as before", H.get(20) == "second scan"))
        c.append(("S452's unknown supplier still held as before", H.get(21) == "supplier unknown"))
        k1 = m._s452_lookup(cx, SID0 + 3)[0]
        k2 = m._s452_lookup(cx, SID0 + 7)[0]
        c.append(("the download guard: a held second scan answers 'held'", k1 == "held"))
        c.append(("the download guard: a missing bill answers 'list'", k2 == "list"))
        c.append(("a listed line keeps its name and its fields", L.get(8, {}).get("name", "").startswith("W-08_WALKTWO_PHARMA_77_28-03-2099")))
        c.append(("held + listed = every scan", len(r["list"]) + len(r["held"]) == len(SCANS)))
        c.append(("the walk's rows are its own (export, bills, month)",
                  cx.execute("SELECT COUNT(*) FROM purchase_bill WHERE bw_md5=?", (MD5E,)).fetchone()[0] == 11))
        return c
    finally:
        clean(cx)
        left = cx.execute("SELECT COUNT(*) FROM purchase_bill WHERE supplier IN (?,?)", (SIX, TWO)).fetchone()[0]
        if left:
            print("!! the walk's rows were not all removed")


def proof(old, new, cx, assets, rematch=True):
    for m in (old, new):
        if assets:
            m._assets_db = assets
    try:
        if rematch:
            old._rematch_if_changed(cx, "walk683")                     # the matcher runs once, the same state for both
    except Exception as e:                                         # noqa: BLE001
        print("   (the re-match could not run: %s)" % e)
    for m in (old, new):
        m._rematch_if_changed = lambda con, who="x": None
    ro, rn = old.scans_for_amir(cx), new.scans_for_amir(cx)
    if not (ro.get("ok") and rn.get("ok")):
        return "proof: NOT RUN -- the scans' database is not readable"
    Lo = {x["id"]: x for x in ro["list"]}
    Ln = {x["id"]: x for x in rn["list"]}
    Ho = {x["id"]: x.get("held") for x in ro["held"]}
    Hn = {x["id"]: x.get("held") for x in rn["held"]}
    bad = []
    for i in Ln:
        if i not in Lo:
            bad.append("listed now, not before: %s" % Ln[i].get("stamp"))
        elif Ln[i] != Lo[i]:
            bad.append("a listed line changed: %s" % Ln[i].get("stamp"))
    for i in Lo:
        if i not in Ln:
            why = Hn.get(i)
            ok = bool(why) and (why == "month finalised" or why.startswith("in Marg:"))
            print("  --  %s %s (scan %s): %s" % (Lo[i].get("stamp"), Lo[i].get("supplier"), Lo[i].get("scan_ddmm"), why))
            if not ok:
                bad.append("left the list without an S683 reason: %s" % Lo[i].get("stamp"))
    for i, w in Ho.items():
        if Hn.get(i) != w:
            bad.append("an old hold changed: scan %s %s -> %s" % (i, w, Hn.get(i)))
    hidden, tried = genuine(new, cx)
    for b in bad:
        print("      RED  " + b)
    moved = len([i for i in Lo if i not in Ln])
    return ("proof: old %d listed / new %d listed . %d held by S683 . %d other difference(s) . genuine bills hidden %d of %d"
            % (len(Lo), len(Ln), moved, len(bad), hidden, tried))


def genuine(m, cx):
    """Every live-export bill of an OPEN month, taken out of the bills and offered to the rule as a NEW scan of itself (its supplier,
    number and date; scanned on its date): the rule must hold none of them -- a bill Marg does not have is never hidden."""
    EFF = m.EFF_BILL
    bills = [dict(b) for b in cx.execute("SELECT b.* FROM purchase_bill b WHERE " + EFF).fetchall()]
    final = m._s683_final_months(cx)
    taken = {int(x[0]) for x in cx.execute("SELECT bill_id FROM purchase_scan_link")} | {int(b["id"]) for b in bills if b.get("scan_bill_id")}
    hidden = tried = 0
    for b in bills:
        d = m._date_or_none_s439(b.get("bill_date"))
        if d is None or d.strftime("%Y-%m") in final:
            continue
        key, tails = m.supplier_key(b["supplier"]), m._bill_tails_s439(b["bill_no"])
        rest = [x for x in bills if not (m.supplier_key(x["supplier"]) == key and m._bill_tails_s439(x["bill_no"]) == tails)]
        tried += 1
        why = m._s683_hold(dict(bill_no=b["bill_no"]), key, d, d, rest, taken, final)
        if why:
            hidden += 1
            print("      HIDDEN  %s %s %s: %s" % (key, b["bill_no"], b["bill_date"], why))
    return hidden, tried


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new")
    ap.add_argument("--old")
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--old-root")
    ap.add_argument("--lib", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--assets")
    ap.add_argument("--no-rematch", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.scratch, exist_ok=True)
    cx = sqlite3.connect(a.db, timeout=30)
    cx.row_factory = sqlite3.Row
    if a.proof:
        old = load(a.old_root, a.lib, a.scratch, "old")
        new = load(a.new, a.lib, a.scratch, "new")
        print(proof(old, new, cx, a.assets, not a.no_rematch))
        return
    m = load(a.new or a.old, a.lib, a.scratch, "new" if a.new else "old")
    c = walk(m, cx)
    red = [t for t, ok in c if not ok]
    for t, ok in c:
        print("  %s  %s" % ("ok " if ok else "RED", t))
    if a.new:
        print("%d of %d green" % (len(c) - len(red), len(c)))
    else:
        print("%d S683 check(s) red . %d green" % (len(red), len(c) - len(red)))


if __name__ == "__main__":
    main()
