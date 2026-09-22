#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""day_resync.py -- S367_DAY_TRUTH_4 (S355 -> S356 -> S357 -> this): an unapproved pharmacy day follows
Marg's latest bills and the bank, and carries its home / procedure medicine bills and their credit notes.

S367 (F-613, the owner's ruling D602 of 22-Sep-2026)
    04-Sep was filed at 09:03 on 05-Sep from Marg's 08:53 export (17 bills, 23,675). Marg's next
    export (06-Sep 09:03) carried an 18th bill for 04-Sep, A003396, 200 cash. The bills were
    refreshed; the filed day never was, so the day read 200 short of Marg.
    PASS 0 -- MARG.  For every unapproved, autofiled, never-corrected pharmacy day: when Marg's
    bills (sale_bill, the latest export) add up to a different net than the day was filed at,
    the cash line becomes Marg's net - the UPI line (UPI stays the bank's), with one audit_log
    row 'resync_marg' (before / after, the export it followed). A day whose UPI exceeds Marg's
    net is left alone and named. An APPROVED day that differs is never touched: it is named
    here and on the day panel's "Needs you", and a person corrects it visibly.

THE FAULT (S275, 20-Sep-2026, read from the 01:35 nightly database)
    The D354 autofile builds a pharmacy day the moment Marg's sale report
    arrives: net sale from the report, UPI from the bank AS KNOWN AT THAT
    MOMENT, cash = net - UPI.  The bank's statement usually lands hours
    later, so the day is frozen with UPI 0 and cash overstated; the
    statement then opens a 'upi_vs_statement' exception that nobody can
    close, and the approval section shows a cash figure that is not true.
    Nine of the sixteen September days were filed this way.

WHAT THIS DOES
    PASS 1 -- UPI.  For every pharmacy day_entry that is (a) not yet
    approved, (b) written by the autofile and never corrected by a person,
    and (c) has a bank statement: set the UPI line to the bank's settled
    total, the cash line to net - UPI, write one audit_log row (before /
    after), and re-run finance_upi.reconcile_upi so the exception closes
    itself.  A day whose bank total exceeds its net sale is left alone and
    named (it needs a person).  Idempotent.
    PASS 2 -- HOME / PROCEDURE MEDICINE.  For every unapproved pharmacy day:
    each Marg bill whose customer text is one of Darpan's labels (setting
    noncash.home_words / noncash.proc_words; "HOME MEDI", "PROSIJ...") --
    found in the review queue where the ingest parks a bill with no ID and
    no phone, or tagged home_med by the ingest -- becomes one
    day_noncash_bill row (the row his old form used to write), once.  A CREDIT
    NOTE on such a bill (goods back, no cash -- the owner's ruling of 20-Sep)
    becomes one cash_adjustment row of +amount, once, so the drawer is not
    read short by it.

WHAT IT NEVER DOES
    Touch an approved or locked day.  Touch a day a person has corrected
    (audit action 'correct' on the entry) in pass 1.  Edit or remove a
    noncash bill anyone typed (pass 2 only ADDS a row for a bill that has
    none).  Touch expenses, movements, Marg, sale_item, the review queue.
    Change any parent file.

RUN
    /root/wa/venv/bin/python3 -B /root/finance/day_resync.py            # apply
    /root/wa/venv/bin/python3 -B /root/finance/day_resync.py --dry-run  # say only
    --db PATH   another database (the walk)     --since YYYY-MM-DD (default 2026-09-01)
    Honours /root/finance/_off/ALL_OFF (sanjeevni_switch.sh).  Cron: every
    30 minutes 07-23 under flock.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import sqlite3
import sys

KIT = "S367_DAY_TRUTH_4"
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
DB_DEFAULT = os.environ.get("FINANCE_DB", os.path.join(HERE, "finance.db"))
OFF_DIR = os.environ.get("SANJEEVNI_OFF_DIR", os.path.join(HERE, "_off"))
UNIT = "medical"
WHO = "day_resync"


def now_iso():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def rupees(p):
    return "%d.%02d" % (p // 100, p % 100) if p >= 0 else "-" + rupees(-p)


def switched_off():
    return os.path.exists(os.path.join(OFF_DIR, "ALL_OFF")) or \
        os.path.exists(os.path.join(OFF_DIR, "ALL_OFF.txt"))


def open_db(path):
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout = 30000")
    con.execute("PRAGMA foreign_keys = ON")
    return con


def candidates(con, since):
    """Unapproved, autofiled, never corrected by a person, statement in."""
    rows = con.execute(
        "SELECT e.id, e.business_date, e.status, e.source "
        "FROM day_entry e WHERE e.unit=? AND e.status IN ('submitted','draft') "
        "AND e.source='app' AND e.business_date>=? "
        "AND EXISTS (SELECT 1 FROM audit_log a WHERE a.table_name='day_entry' "
        "            AND a.row_id=e.id AND a.action='autofile') "
        "AND NOT EXISTS (SELECT 1 FROM audit_log a WHERE a.table_name='day_entry' "
        "            AND a.row_id=e.id AND a.action='correct') "
        "ORDER BY e.business_date", (UNIT, since)).fetchall()
    return rows


def day_lines(con, eid):
    cash = con.execute("SELECT id, amount_p FROM day_line WHERE day_entry_id=? "
                       "AND service='pharmacy_sale' AND mode='cash'", (eid,)).fetchall()
    upi = con.execute("SELECT id, amount_p FROM day_line WHERE day_entry_id=? "
                      "AND service='pharmacy_sale' AND mode='upi'", (eid,)).fetchall()
    return cash, upi


def bank_total(con, iso):
    st = con.execute("SELECT parsed_total_p, txn_count FROM upi_statement "
                     "WHERE unit=? AND statement_date=?", (UNIT, iso)).fetchone()
    if st is None:
        return None, 0
    return int(st["parsed_total_p"] or 0), int(st["txn_count"] or 0)


def resync_day(con, e, apply, reconcile):
    """Returns (verdict, line). Verdicts: SAME · FIXED · WOULD_FIX · NO_BANK ·
    OVER_NET · SHAPE."""
    eid, iso = e["id"], e["business_date"]
    bank_p, n_txn = bank_total(con, iso)
    if bank_p is None:
        return "NO_BANK", "%s  no bank statement yet" % iso
    cash, upi = day_lines(con, eid)
    if len(cash) != 1 or len(upi) > 1:
        return "SHAPE", "%s  unexpected line shape (cash %d, upi %d) -- left alone" % (
            iso, len(cash), len(upi))
    cash_p = int(cash[0]["amount_p"] or 0)
    upi_p = int(upi[0]["amount_p"] or 0) if upi else 0
    net_p = cash_p + upi_p
    if bank_p == upi_p:
        return "SAME", "%s  UPI %s already the bank's" % (iso, rupees(upi_p))
    if bank_p > net_p:
        return "OVER_NET", "%s  bank UPI %s exceeds the net sale %s -- needs a person" % (
            iso, rupees(bank_p), rupees(net_p))
    new_cash = net_p - bank_p
    line = "%s  UPI %s -> %s (%d txns) · cash %s -> %s · net %s" % (
        iso, rupees(upi_p), rupees(bank_p), n_txn, rupees(cash_p), rupees(new_cash), rupees(net_p))
    if not apply:
        return "WOULD_FIX", line
    before = dict(date=iso, cash_p=cash_p, upi_p=upi_p, net_p=net_p)
    after = dict(date=iso, cash_p=new_cash, upi_p=bank_p, net_p=net_p,
                 bank_txns=n_txn, rule="D354 marg+bank, re-read from the statement", kit=KIT)
    con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (new_cash, cash[0]["id"]))
    if upi:
        con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (bank_p, upi[0]["id"]))
    else:
        con.execute("INSERT INTO day_line (day_entry_id, service, mode, amount_p) "
                    "VALUES (?,'pharmacy_sale','upi',?)", (eid, bank_p))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, "
                "by_whom, at) VALUES ('day_entry', ?, 'resync_upi', ?, ?, ?, ?)",
                (eid, json.dumps(before), json.dumps(after), WHO, now_iso()))
    con.commit()
    if reconcile is not None:
        r = reconcile(con, UNIT, iso, now=now_iso())
        if r is not None:
            line += " · exception %s" % ("closed" if r.get("match") else "still open")
    return "FIXED", line


# ------------------------------------------------------------------ pass 0
# MARG (S367, F-613).  The day follows Marg's latest bills until it is approved.

def marg_net(con, iso):
    r = con.execute("SELECT COUNT(*), COALESCE(SUM(net_p),0), MAX(source_stamp) FROM sale_bill "
                    "WHERE unit=? AND business_date=?", (UNIT, iso)).fetchone()
    if not r or not r[0]:
        return None, 0, None
    return int(r[1]), int(r[0]), r[2]


def resync_marg(con, e, apply):
    """Returns (verdict, line). Verdicts: SAME · FIXED · WOULD_FIX · NO_MARG · OVER_NET · SHAPE."""
    eid, iso = e["id"], e["business_date"]
    m_p, n_bills, stamp = marg_net(con, iso)
    if m_p is None:
        return "NO_MARG", "%s  no Marg bills on record" % iso
    cash, upi = day_lines(con, eid)
    if len(cash) != 1 or len(upi) > 1:
        return "SHAPE", "%s  unexpected line shape (cash %d, upi %d) -- left alone" % (iso, len(cash), len(upi))
    cash_p = int(cash[0]["amount_p"] or 0)
    upi_p = int(upi[0]["amount_p"] or 0) if upi else 0
    if cash_p + upi_p == m_p:
        return "SAME", "%s  filed net = Marg's %s" % (iso, rupees(m_p))
    if upi_p > m_p:
        return "OVER_NET", "%s  UPI %s exceeds Marg's net %s -- needs a person" % (iso, rupees(upi_p), rupees(m_p))
    new_cash = m_p - upi_p
    line = "%s  Marg's latest export (%s, %d bills) nets %s; filed %s · cash %s -> %s" % (
        iso, stamp or "?", n_bills, rupees(m_p), rupees(cash_p + upi_p), rupees(cash_p), rupees(new_cash))
    if not apply:
        return "WOULD_FIX", line
    before = dict(date=iso, cash_p=cash_p, upi_p=upi_p, net_p=cash_p + upi_p)
    after = dict(date=iso, cash_p=new_cash, upi_p=upi_p, net_p=m_p, marg_bills=n_bills, marg_export=stamp,
                 rule="D354 marg+bank, re-read from Marg's latest export (F-613)", kit=KIT)
    con.execute("UPDATE day_line SET amount_p=? WHERE id=?", (new_cash, cash[0]["id"]))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, before_json, after_json, "
                "by_whom, at) VALUES ('day_entry', ?, 'resync_marg', ?, ?, ?, ?)",
                (eid, json.dumps(before), json.dumps(after), WHO, now_iso()))
    con.commit()
    return "FIXED", line


def approved_differs(con, since):
    """Approved / locked pharmacy days whose filed net is not Marg's -- named, never touched."""
    out = []
    for eid, iso in con.execute("SELECT id, business_date FROM day_entry WHERE unit=? AND business_date>=? "
                                "AND status NOT IN ('submitted','draft') ORDER BY business_date", (UNIT, since)):
        m_p, n, stamp = marg_net(con, iso)
        if m_p is None:
            continue
        f = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM day_line WHERE day_entry_id=? "
                        "AND service='pharmacy_sale'", (eid,)).fetchone()[0]
        if int(f) != m_p:
            out.append("%s  APPROVED at %s; Marg's bills now net %s -- a person corrects it" % (
                iso, rupees(int(f)), rupees(m_p)))
    return out


# ------------------------------------------------------------------ pass 2
# HOME / PROCEDURE MEDICINE.  Darpan bills these to a label instead of a person
# ("HOME MEDICINE" / "HOME MEDISUN", "PROSIJER <name>" -- his spellings).  A bill
# with no clinic ID and no phone cannot be attached to a patient, so the ingest
# parks it in sale_item_review, and nothing ever turned it into the day's
# home / procedure deduction once the old typed form went (D354).  Here the
# label decides: every such bill becomes one day_noncash_bill row -- the same
# row Darpan's form used to write -- and v_cash_ledger subtracts it.

HOME_DEFAULT = "HOME MEDI"
PROC_DEFAULT = "PROSIJ,PROSEJ,PROCIJ,PROCED,PROSED,PRUSIJ"
WORD_SETTINGS = (("noncash.home_words", HOME_DEFAULT,
                  "S357: substrings (comma-separated, any case) of a Marg bill's customer text that mean HOME MEDICINE"),
                 ("noncash.proc_words", PROC_DEFAULT,
                  "S357: substrings that mean PROCEDURE MEDICINE (Darpan's spellings; add more here, never in code)"))


def _has(con, table):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None


def words(con, key, default):
    v = default
    if _has(con, "setting"):
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        if r is not None and (r[0] or "").strip():
            v = r[0]
    return [w.strip().upper() for w in v.split(",") if w.strip()]


def seed_settings(con):
    """The word lists live in the setting table so a new spelling is a data edit."""
    if not _has(con, "setting"):
        return
    cols = {r[1] for r in con.execute("PRAGMA table_info(setting)")}
    for key, val, note in WORD_SETTINGS:
        if "note" in cols:
            con.execute("INSERT OR IGNORE INTO setting (key, value, note) VALUES (?,?,?)", (key, val, note))
        else:
            con.execute("INSERT OR IGNORE INTO setting (key, value) VALUES (?,?)", (key, val))
    con.commit()


def head_for(text, home_w, proc_w):
    t = " ".join((text or "").upper().split())
    if any(w in t for w in home_w):
        return "home_medicine"
    if any(w in t for w in proc_w):
        return "procedure_medicine"
    return None


def label_bills(con, e, home_w, proc_w):
    """Every bill of the day whose customer text is a label: from the review
    queue (open or resolved, by the parked line's own text) and from sale_item
    rows the ingest tagged home_med=1.  Returns [(bill_no, bill_date, head, amount_p, where)]."""
    eid, iso = e["id"], e["business_date"]
    out, seen = [], set()
    if _has(con, "sale_item_review"):
        for r in con.execute("SELECT raw_text, guess_name, amount_p FROM sale_item_review "
                             "WHERE day_entry_id=? ORDER BY id", (eid,)):
            try:
                raw = json.loads(r["raw_text"] or "{}")
            except ValueError:
                raw = {}
            text = r["guess_name"] or raw.get("patient_name") or raw.get("description") or ""
            head = head_for(text, home_w, proc_w)
            if not head:
                continue
            bill = str(raw.get("bill_no") or "").strip()
            bdate = str(raw.get("bill_date") or iso).strip() or iso
            amt = int(r["amount_p"] or 0)
            if not bill or (bill, bdate) in seen:
                continue
            seen.add((bill, bdate))
            out.append((bill, bdate, head, amt, "review"))
    cols = {c[1] for c in con.execute("PRAGMA table_info(sale_item)")} if _has(con, "sale_item") else set()
    if "home_med" in cols:
        for r in con.execute("SELECT source_ref, amount_p FROM sale_item WHERE day_entry_id=? "
                             "AND home_med=1 AND service NOT LIKE '%return%'", (eid,)):
            bill = str(r["source_ref"] or "").strip()
            if not bill or (bill, iso) in seen:
                continue
            seen.add((bill, iso))
            out.append((bill, iso, "home_medicine", int(r["amount_p"] or 0), "tag"))
    return out


def noncash_candidates(con, since):
    """Unapproved pharmacy days (any source: a typed day may also carry an
    un-deducted label bill -- the row is added only when absent)."""
    return con.execute(
        "SELECT id, business_date, status FROM day_entry WHERE unit=? "
        "AND status IN ('submitted','draft') AND business_date>=? ORDER BY business_date",
        (UNIT, since)).fetchall()


def noncash_day(con, e, home_w, proc_w, apply):
    """Returns (verdict, line): ADDED · WOULD_ADD · NONE · PRESENT, plus notes."""
    eid, iso = e["id"], e["business_date"]
    bills = label_bills(con, e, home_w, proc_w)
    if not bills:
        return "NONE", "%s  no home / procedure bill" % iso
    added, present, notes, adjusts = [], [], [], []
    for bill, bdate, head, amt, where in bills:
        ex = con.execute("SELECT id, head, amount_p FROM day_noncash_bill WHERE unit=? AND bill_no=? AND bill_date=?",
                         (UNIT, bill, bdate)).fetchone()
        if ex is not None:
            present.append("%s %s %s" % (bill, ex["head"][:4], rupees(int(ex["amount_p"] or 0))))
            continue
        if amt <= 0:
            # THE OWNER'S RULING (20-Sep-2026): a home / procedure medicine credit note is a
            # bookkeeping entry -- goods came back to the shop, no cash left the drawer.  The
            # day's net sale already carries the minus, so the drawer is put back by the same
            # amount as ONE cash_adjustment row (the ledger's own +/- column), once per bill.
            if amt == 0:
                continue
            reason = "%s credit note %s: goods returned, no cash moved (owner 20-Sep-2026, %s)" % (
                head.replace("_", " "), bill, KIT)
            ex_adj = con.execute("SELECT id FROM cash_adjustment WHERE day_entry_id=? AND reason LIKE ?",
                                 (eid, "%credit note " + bill + ":%")).fetchone()
            if ex_adj is not None:
                present.append("%s CN +%s (adjustment)" % (bill, rupees(-amt)))
            else:
                adjusts.append((bill, head, -amt, reason))
            continue
        added.append((bill, bdate, head, amt, where))
    line = "%s  " % iso + " · ".join(
        ["%s %s %s" % (b, h[:4], rupees(a)) for b, d, h, a, w in added] +
        ["%s CN +%s back to the drawer (goods returned, no cash)" % (b, rupees(a)) for b, h, a, r in adjusts] +
        (["already: " + ", ".join(present)] if present else []) + notes)
    if not added and not adjusts:
        return ("PRESENT" if present else "NONE"), line
    if not apply:
        return "WOULD_ADD", line
    now = now_iso()
    for bill, head, amt, reason in adjusts:
        con.execute("INSERT INTO cash_adjustment (day_entry_id, amount_p, reason, source, status, explanation) "
                    "VALUES (?,?,?,'manual','explained',?)",
                    (eid, amt, reason, "A credit note on a home / procedure medicine bill returns goods to the shop; "
                                       "the money never entered the drawer, so the drawer is not short by it (the owner's ruling, 20-Sep-2026)."))
    for bill, bdate, head, amt, where in added:
        con.execute("INSERT OR IGNORE INTO day_noncash_bill (day_entry_id, unit, bill_date, head, bill_no, amount_p, "
                    "note, entered_by, entered_at, noncash_uid) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (eid, UNIT, bdate, head, bill, amt,
                     "from Marg's customer text (%s), %s" % (where, KIT), WHO, now,
                     "nc" + hashlib.md5(("%s|%s|%s" % (UNIT, bill, bdate)).encode()).hexdigest()[:14]))
    con.execute("INSERT INTO audit_log (table_name, row_id, action, after_json, by_whom, at) "
                "VALUES ('day_entry', ?, 'noncash_sync', ?, ?, ?)",
                (eid, json.dumps(dict(date=iso, added=[dict(bill=b, head=h, amount_p=a, source=w)
                                                          for b, d, h, a, w in added],
                                      adjustments=[dict(bill=b, head=h, amount_p=a) for b, h, a, r in adjusts],
                                      kit=KIT)), WHO, now))
    con.commit()
    return "ADDED", line


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DB_DEFAULT)
    ap.add_argument("--since", default="2026-09-01")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-reconcile", action="store_true", help="walk only")
    a = ap.parse_args(argv)
    if switched_off():
        print("%s: Sanjeevni jobs are OFF (%s) -- nothing done" % (KIT, OFF_DIR))
        return 0
    if not os.path.exists(a.db):
        print("%s: no database at %s" % (KIT, a.db))
        return 2
    reconcile = None
    if not a.no_reconcile:
        try:
            import finance_upi  # noqa: PLC0415
            reconcile = finance_upi.reconcile_upi
        except Exception as ex:  # noqa: BLE001
            print("%s: finance_upi not importable (%s) -- lines fixed, exception left to the next bank load" % (KIT, ex))
    con = open_db(a.db)
    mode = "DRY RUN" if a.dry_run else "APPLY"
    # ---- pass 0: the day follows Marg's latest bills (S367, F-613)
    rows0 = candidates(con, a.since)
    counts0 = {}
    print("%s %s -- MARG: %d unapproved autofiled day(s) since %s" % (KIT, mode, len(rows0), a.since))
    for e in rows0:
        v, line = resync_marg(con, e, apply=not a.dry_run)
        counts0[v] = counts0.get(v, 0) + 1
        if v != "SAME":
            print("  %-9s %s" % (v, line))
    for line in approved_differs(con, a.since):
        print("  %-9s %s" % ("APPROVED", line))
    print("summary0: " + (" · ".join("%s %d" % (k, counts0[k]) for k in sorted(counts0)) if counts0 else "nothing to do"))
    # ---- pass 1: UPI from the bank
    rows = candidates(con, a.since)
    counts = {}
    print("%s %s -- UPI: %d unapproved autofiled day(s) since %s in %s" % (KIT, mode, len(rows), a.since, a.db))
    for e in rows:
        v, line = resync_day(con, e, apply=not a.dry_run, reconcile=reconcile)
        counts[v] = counts.get(v, 0) + 1
        print("  %-9s %s" % (v, line))
    print("summary: " + (" · ".join("%s %d" % (k, counts[k]) for k in sorted(counts)) if counts else "nothing to do"))
    # ---- pass 2: home / procedure medicine from the label bills
    if not a.dry_run:
        seed_settings(con)
    home_w, proc_w = words(con, "noncash.home_words", HOME_DEFAULT), words(con, "noncash.proc_words", PROC_DEFAULT)
    rows2 = noncash_candidates(con, a.since)
    counts2 = {}
    print("%s %s -- HOME/PROCEDURE: %d unapproved day(s); home words %s · procedure words %s" % (
        KIT, mode, len(rows2), "/".join(home_w), "/".join(proc_w)))
    for e in rows2:
        v, line = noncash_day(con, e, home_w, proc_w, apply=not a.dry_run)
        counts2[v] = counts2.get(v, 0) + 1
        if v != "NONE":
            print("  %-9s %s" % (v, line))
    print("summary2: " + (" · ".join("%s %d" % (k, counts2[k]) for k in sorted(counts2)) if counts2 else "nothing to do"))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
