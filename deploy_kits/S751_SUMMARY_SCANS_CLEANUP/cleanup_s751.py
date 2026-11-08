#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""cleanup_s751.py -- kit S751_SUMMARY_SCANS_CLEANUP (08-Nov-2026, Sanjeevni session 407). The owner's word 13:25 / 13:42 IST.

Removes the SIXTEEN papers Shivani scanned 11:54-12:04 IST on 08-Nov-2026 (B-0274 .. B-0289: fourteen dealers' October summaries scanned
without the SUMMARY tick, so the server read them as ordinary bills) -- exactly as the app's own Delete button does (asset_register.bill_delete,
S563): one 'paper_deleted' audit row per paper (kept for ever), assets.bill_id cleared, bill_items then bills deleted; plus the rows DERIVED
from each paper and keyed by its id alone (claude_reading, scan_check_s441, scan_question, scan_lie) so a later paper that gets a reused id
inherits nothing; and on finance.db the pairing scratch rows purchase_scan_state / purchase_scan_link for these scan ids.

ALL OR NOTHING. Every paper must be the one that was read on the screen (id, stamp, amount to the rupee, scanned 08-Nov-2026, by Shivani,
the vendor as read) or NOTHING is changed. REFUSES when anything a person decided or paid points at one of them (paper_payment_bill,
proc_paper / proc_line, stationery_line, d664_warranty, an outside paper's dup_of / challan_of (a later paper's dup_cand question or rescan_of link is CLEARED with the paper), finance.db's
s736_decision / s749_act / s750_dealer_of). Backs up both databases first (sqlite backup API) and prints every count before and after.

    python3 cleanup_s751.py --assets /root/assetapp/assets.db --finance /root/finance/finance.db            # DRY: reads, prints, writes nothing
    python3 cleanup_s751.py --assets /root/assetapp/assets.db --finance /root/finance/finance.db --real     # the deletion, after the backups
"""
import json
import os
import shutil
import sqlite3
import sys
import time

KIT = "S751_SUMMARY_SCANS_CLEANUP"
DAY = "2026-11-08"
WHO = "Shivani"
# id, stamp, vendor as the list read it ('' = no vendor), the amount in rupees as read
TARGETS = [
    (274, "B-0274", "YOGENDRA AGENCIES", 8512),
    (275, "B-0275", "DAANSHI PHARMA", 8603),
    (276, "B-0276", "AGARWAL SURGICAL & MEDICALS", 1238),
    (277, "B-0277", "ESS KAY AGENCIES (EXTN)", 6859),
    (278, "B-0278", "DEEPAM PHARMA", 32114),
    (279, "B-0279", "GUNINA PHARMACEUTIC PVT. LTD.", 60682),
    (280, "B-0280", "MANNAT PHARMA", 24212),
    (281, "B-0281", "MANNAT PHARMA", 24212),
    (282, "B-0282", "", 3656),
    (283, "B-0283", "JANTA PHARMACEUTICALS", 13146),
    (284, "B-0284", "SHIVAAZ FORMULATIONS", 65357),
    (285, "B-0285", "DRUG DEALS", 1557),
    (286, "B-0286", "RADHA MEDICAL & SCIENTIFIC", 4038),
    (287, "B-0287", "A.A.PHARMACEUTICALS", 12818),
    (288, "B-0288", "SHRADDHA MEDICOSE", 9395),
    (289, "B-0289", "YUVIKA SURGICALS", 5940),
]
IDS = [t[0] for t in TARGETS]
Q = ",".join("?" * len(IDS))
# derived rows keyed by the paper's id alone (assets.db) -- removed with the paper
DERIVED = ["bill_items", "claude_reading", "scan_check_s441", "scan_question", "scan_lie"]
# rows a person decided or paid (assets.db) -- a hit REFUSES the run
REFUSE_A = [("paper_payment_bill", "bill_id"), ("proc_paper", "bill_id"), ("proc_line", "bill_id"), ("proc_photo", "bill_id"), ("stationery_line", "bill_id"),
            ("d664_warranty", "bill_id"), ("d664_join", "head_id"), ("d664_join", "page_id"), ("paper_payment", "proof_bill_id")]
# finance.db: scratch rows removed with the paper / decisions that refuse
FIN_DERIVED = [("purchase_scan_state", "asset_bill_id"), ("purchase_scan_link", "asset_bill_id"), ("purchase_sarvam_check", "asset_bill_id")]
FIN_REFUSE = [("s736_decision", "asset_bill_id"), ("s749_act", "scan"), ("s750_dealer_of", "scan")]
FIN_REPORT = [("purchase_scan_alias", "scan_id")]


def arg(n, d=None):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def has_table(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


def has_col(con, t, c):
    return has_table(con, t) and c in {r[1] for r in con.execute("PRAGMA table_info(%s)" % t)}


def count_in(con, t, c):
    if not has_col(con, t, c):
        return None
    return con.execute("SELECT COUNT(*) FROM %s WHERE %s IN (%s)" % (t, c, Q), IDS).fetchone()[0]


def vendor_ok(read, have):
    a = "".join(ch for ch in (read or "").upper() if ch.isalnum())
    b = "".join(ch for ch in (have or "").upper() if ch.isalnum())
    if not a:
        return not b
    return a[:6] == b[:6]


def now_ist():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 19800))


def main():
    adb, fdb, real = arg("--assets"), arg("--finance"), "--real" in sys.argv
    if not adb or not fdb:
        print(__doc__)
        return 2
    for p in (adb, fdb):
        if not os.path.isfile(p):
            print("!! not a file: %s -- nothing done" % p)
            return 2
    print("%s -- %s  assets=%s  finance=%s  %s" % (KIT, now_ist(), adb, fdb, "REAL" if real else "DRY (nothing written)"))
    a = sqlite3.connect(adb, timeout=30)
    a.row_factory = sqlite3.Row
    f = sqlite3.connect(fdb, timeout=30)
    f.row_factory = sqlite3.Row
    bad = []
    # ---- 1 · each paper is the one read on the screen
    users = {}
    if has_table(a, "users"):
        users = {int(r[0]): str(r[1] or "") for r in a.execute("SELECT id, display_name FROM users")}
    print("1  the sixteen papers")
    for bid, stamp, vendor, rs in TARGETS:
        r = a.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        if r is None:
            bad.append("%s (#%d) is not in bills" % (stamp, bid))
            print("   !! %s #%d: NOT FOUND" % (stamp, bid))
            continue
        probs = []
        if (r["stamp_no"] or "") != stamp:
            probs.append("stamp is %r" % r["stamp_no"])
        amt = r["total_amount"]
        if amt is None or abs(float(amt) - rs) > 1.0:
            probs.append("amount is %r, read %d" % (amt, rs))
        when = str(r["submitted_at"] or r["created_at"] or "")
        created = str(r["created_at"] or "")
        if not (when.startswith(DAY) or created.startswith(DAY)):
            probs.append("scanned %r, not %s" % (when or created, DAY))
        who = str(r["submitted_by"] or "") or users.get(int(r["created_by"] or 0), "")
        if WHO.lower() not in who.lower():
            probs.append("scanned by %r, not %s" % (who, WHO))
        if not vendor_ok(vendor, r["vendor"]):
            probs.append("vendor is %r, read %r" % (r["vendor"], vendor))
        line = "   %s #%d  %-32s %10s  %s  %-8s %-9s %s  %s" % (stamp, bid, (r["vendor"] or "(no vendor)")[:32], ("%.0f" % float(amt)) if amt is not None else "-",
                                                             when[:16], r["kind"] or "", r["status"] or "", r["lane"] or "", who)
        print(line + ("   !! " + "; ".join(probs) if probs else ""))
        if probs:
            bad.append("%s: %s" % (stamp, "; ".join(probs)))
    # ---- 2 · nothing a person decided or paid points at them
    print("2  what else points at them (assets.db)")
    for t, c in REFUSE_A:
        n = count_in(a, t, c)
        print("   %-22s.%-14s %s" % (t, c, "no table/column" if n is None else n))
        if n:
            bad.append("%s.%s names %d of them" % (t, c, n))
    n_cand = n_resc = 0
    for c in ("dup_of", "dup_cand", "challan_of", "rescan_of"):
        if has_col(a, "bills", c):
            n = a.execute("SELECT COUNT(*) FROM bills WHERE %s IN (%s) AND id NOT IN (%s)" % (c, Q, Q), IDS + IDS).fetchone()[0]
            if c == "dup_cand":
                n_cand = n
                print("   bills.%-16s from OUTSIDE the sixteen: %d  (a 'second scan of ...?' question on a later paper: cleared with the paper it asks about)" % (c, n))
                continue
            if c == "rescan_of":                                      # S618: a later RESCAN of one of them already set the old one aside; the link
                n_resc = n                                            # names a paper that is going -- cleared, the new scan stands as a plain scan
                for rr in a.execute("SELECT id, stamp_no, rescan_of, kind, lane, status FROM bills WHERE rescan_of IN (%s) AND id NOT IN (%s)" % (Q, Q), IDS + IDS):
                    print("   bills.rescan_of        from OUTSIDE: %s #%d (%s, %s, %s) is the rescan of #%d -- the link is cleared, the new scan stays as it is"
                          % (rr["stamp_no"], rr["id"], rr["kind"], rr["lane"], rr["status"], rr["rescan_of"]))
                if not n:
                    print("   bills.%-16s from OUTSIDE the sixteen: 0" % c)
                continue
            print("   bills.%-16s from OUTSIDE the sixteen: %d" % (c, n))
            if n:
                bad.append("an outside paper's bills.%s names one of them (%d)" % (c, n))
    n_assets = count_in(a, "assets", "bill_id")
    print("   assets.bill_id (cleared, as the app's Delete does): %s" % n_assets)
    print("3  the derived rows that go with them (assets.db)")
    der = {}
    for t in DERIVED:
        der[t] = count_in(a, t, "bill_id")
        print("   %-22s %s" % (t, "no table" if der[t] is None else der[t]))
    n_audit = count_in(a, "bill_audit", "bill_id")
    print("   bill_audit rows (KEPT, history): %s" % n_audit)
    print("4  finance.db")
    fder = {}
    for t, c in FIN_DERIVED:
        fder[(t, c)] = count_in(f, t, c)
        print("   %-22s.%-14s %s  (removed with the paper)" % (t, c, "no table/column" if fder[(t, c)] is None else fder[(t, c)]))
    if has_col(f, "purchase_scan_state", "confirmed_by"):                  # S440: what a PERSON decided on a scratch row -- refuses
        cols = {r[1] for r in f.execute("PRAGMA table_info(purchase_scan_state)")}
        conds = [x for x in ("COALESCE(confirmed_by,'')<>''", "COALESCE(chosen_vendor,'')<>''", "dup_ok IS NOT NULL") if x.split("(")[-1].split(",")[0].split(" ")[0] in cols]
        if conds:
            n = f.execute("SELECT COUNT(*) FROM purchase_scan_state WHERE asset_bill_id IN (%s) AND (%s)" % (Q, " OR ".join(conds)), IDS).fetchone()[0]
            print("   purchase_scan_state rows a person decided on (confirmed / vendor chosen / dup ok): %d  (a decision: refuses)" % n)
            if n:
                bad.append("finance purchase_scan_state carries a person's decision on %d of them" % n)
    for t, c in FIN_REFUSE:
        n = count_in(f, t, c)
        print("   %-22s.%-14s %s  (a decision: refuses)" % (t, c, "no table/column" if n is None else n))
        if n:
            bad.append("finance %s.%s names %d of them" % (t, c, n))
    for t, c in FIN_REPORT:
        n = count_in(f, t, c)
        print("   %-22s.%-14s %s  (kept: a learned spelling)" % (t, c, "no table/column" if n is None else n))
    n_bills_before = a.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
    print("   bills in all: %d" % n_bills_before)
    if bad:
        print("REFUSED -- nothing changed:")
        for b in bad:
            print("   - " + b)
        return 1
    if not real:
        print("DRY OK -- every guard green; run again with --real to remove the sixteen.")
        return 0
    # ---- 5 · the backups, then the one transaction per database
    stamp = time.strftime("%Y%m%d_%H%M%S")
    for src, con in ((adb, a), (fdb, f)):
        dst = "%s.bak_S751_%s" % (src, stamp)
        bk = sqlite3.connect(dst)
        con.backup(bk)
        bk.close()
        print("5  backup %s (%d B)" % (dst, os.path.getsize(dst)))
    at = now_ist()[:16]                                                  # as _now_ist writes the history column
    try:
        a.execute("BEGIN IMMEDIATE")
        for bid, stamp_no, vendor, rs in TARGETS:
            r = a.execute("SELECT stamp_no, created_at, vendor, total_amount, kind, lane, status FROM bills WHERE id=?", (bid,)).fetchone()
            if r is None:
                raise RuntimeError("%s vanished between the read and the write" % stamp_no)
            na = a.execute("UPDATE assets SET bill_id=NULL WHERE bill_id=?", (bid,)).rowcount if has_col(a, "assets", "bill_id") else 0
            if has_col(a, "bills", "dup_cand"):
                a.execute("UPDATE bills SET dup_cand=NULL, dup_flag=NULL, dup_why=NULL WHERE dup_cand=? AND id NOT IN (%s)" % Q, [bid] + IDS)
            if has_col(a, "bills", "rescan_of"):
                for rr in a.execute("SELECT id, stamp_no FROM bills WHERE rescan_of=? AND id NOT IN (%s)" % Q, [bid] + IDS).fetchall():
                    a.execute("UPDATE bills SET rescan_of=NULL WHERE id=?", (rr["id"],))
                    a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                              (rr["id"], at, "S751 (the owner's line)", "rescan_link_cleared",
                               json.dumps({"was_rescan_of": bid, "old_stamp": stamp_no, "why": "the old scan removed by S751; this scan stands on its own"})))
            detail = {"stamp": r["stamp_no"], "created_at": r["created_at"], "payments_voided": [], "assets_cleared": na,
                      "kit": KIT, "why": "a dealer's October summary scanned without the SUMMARY tick; rescanned properly by staff (the owner, 13:25 IST 08-Nov)",
                      "vendor": r["vendor"], "amount": r["total_amount"], "kind": r["kind"], "lane": r["lane"], "status": r["status"]}
            a.execute("INSERT INTO bill_audit(bill_id, at, who, action, detail) VALUES(?,?,?,?,?)",
                      (bid, at, "S751 (the owner's line)", "paper_deleted", json.dumps(detail, ensure_ascii=False)[:500]))
            for t in DERIVED:
                if der.get(t) is not None:
                    a.execute("DELETE FROM %s WHERE bill_id=?" % t, (bid,))
            a.execute("DELETE FROM bills WHERE id=?", (bid,))
        a.commit()
    except Exception as e:                                            # noqa: BLE001
        a.rollback()
        print("!! assets.db: %s -- rolled back, nothing changed there; finance.db untouched" % repr(e)[:200])
        return 1
    try:
        f.execute("BEGIN IMMEDIATE")
        for t, c in FIN_DERIVED:
            if fder.get((t, c)) is not None:
                f.execute("DELETE FROM %s WHERE %s IN (%s)" % (t, c, Q), IDS)
        f.commit()
    except Exception as e:                                            # noqa: BLE001
        f.rollback()
        print("!! finance.db: %s -- rolled back; assets.db already changed (its backup above)" % repr(e)[:200])
        return 1
    # ---- 6 · read back
    left = a.execute("SELECT COUNT(*) FROM bills WHERE id IN (%s)" % Q, IDS).fetchone()[0]
    n_bills_after = a.execute("SELECT COUNT(*) FROM bills").fetchone()[0]
    aud = a.execute("SELECT COUNT(*) FROM bill_audit WHERE action='paper_deleted' AND who='S751 (the owner''s line)' AND bill_id IN (%s)" % Q, IDS).fetchone()[0]
    print("6  read back: %d of the sixteen left in bills (want 0) · bills %d -> %d · %d paper_deleted audit rows written" % (left, n_bills_before, n_bills_after, aud))
    for t in DERIVED:
        if der.get(t) is not None:
            print("   %-22s left for them: %d" % (t, count_in(a, t, "bill_id")))
    for t, c in FIN_DERIVED:
        if fder.get((t, c)) is not None:
            print("   finance %-14s left for them: %d" % (t, count_in(f, t, c)))
    seq = a.execute("SELECT value FROM settings WHERE key='stamp_seq'").fetchone() if has_table(a, "settings") else None
    try:
        nxt = "B-%04d" % (int(seq[0]) + 1)
    except (TypeError, ValueError):
        nxt = "?"
    print("   stamp counter stays at %s -- the next paper is %s (stamps are never reused, A-D21)" % (seq[0] if seq else "?", nxt))
    if n_cand:
        left_c = a.execute("SELECT COUNT(*) FROM bills WHERE dup_cand IN (%s)" % Q, IDS).fetchone()[0]
        print("   later papers' 'second scan of ...?' questions about them cleared: %d -> %d left" % (n_cand, left_c))
    if n_resc:
        left_r = a.execute("SELECT COUNT(*) FROM bills WHERE rescan_of IN (%s)" % Q, IDS).fetchone()[0]
        print("   later papers' rescan links to them cleared: %d -> %d left (each audited 'rescan_link_cleared')" % (n_resc, left_r))
    ok = left == 0 and aud == len(IDS) and n_bills_after == n_bills_before - len(IDS)
    print("%s: %s" % (KIT, "DONE." if ok else "CHECK -- the read-back is not what was expected"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
