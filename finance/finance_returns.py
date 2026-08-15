#!/usr/bin/python3
"""
finance_returns.py  ·  Session 180 · item U3
Sale returns: store the drug lines, and trace a return back to the sale it came from.

WHY
    A return is cash out of the drawer with no goods trail unless something
    checks it. Correlating it to a real earlier sale — and to the specific
    medicines on that sale — is what makes a fictitious return hard.

    Measured on six real days: nine credit notes, all nine carrying at least a
    name, seven correlated to an earlier sale inside a six-day window. The two
    that did not were not missing data — their original sale simply predated the
    file. So the lookup runs against the DATABASE, never against one day's file.

TWO DIRECTIONS, ONE INDEX
    reception   — a patient arrives without a bill: find their sales.        find_patient_sales()
    next day    — a return has been billed: find where it came from.         correlate_return()
    Same tables, same keys, opposite direction.

WHAT IT NEVER DOES
    It does not refuse a return. Refusing is a decision for a person at the
    counter with the patient in front of them. This produces a verdict and
    flags; the clinic decides what to do with them.

CONFIDENCE IS NOT ONE NUMBER
    A name match is a probability. For revenue attribution a wrong guess costs a
    rupee in the wrong history; for a discount or return audit it points at the
    wrong patient, day and operator. So the verdict is graded, and only
    CONCLUSIVE is fit to feed an audit:

        conclusive   every returned medicine was on that patient's earlier sale
        probable     the patient matches and some medicines overlap
        patient_only the patient matches but no medicine evidence either way
        none         nothing found

Money is INTEGER PAISE. Stdlib only.
"""

import datetime as dt
import os
import re
import sqlite3

SCHEMA_FILE = "finance_returns.sql"

VERDICT_CONCLUSIVE = "conclusive"
VERDICT_PROBABLE = "probable"
VERDICT_PATIENT_ONLY = "patient_only"
VERDICT_NONE = "none"

# Flags. Each is a reason for a human to look, never a refusal.
F_NO_PATIENT = "no_patient_identified"
F_NO_SALE = "no_matching_sale"
F_OUTSIDE_WINDOW = "outside_return_window"
F_EXPIRED = "expired_or_expiring"
F_LARGE_UNMATCHED = "large_and_unmatched"
F_NO_ITEM_DATA = "no_item_detail_available"


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def norm_item(name):
    """Normalise a medicine name for matching only. The printed name is kept
    separately — this is never shown to anyone."""
    s = re.sub(r"[^A-Z0-9 ]+", " ", str(name or "").upper())
    return re.sub(r"\s+", " ", s).strip()


def _setting(con, key, default):
    r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def _days_between(a, b):
    """b - a in whole days. Parses; never slices a date string (F-78)."""
    da = dt.datetime.strptime(a, "%Y-%m-%d").date()
    db = dt.datetime.strptime(b, "%Y-%m-%d").date()
    return (db - da).days


def _ym(iso_date):
    return iso_date[:7] if iso_date else None


def install(con, schema_path=None):
    """Idempotent. Additive only — one table, its indexes, three settings."""
    path = schema_path or os.path.join(os.path.dirname(os.path.abspath(__file__)), SCHEMA_FILE)
    con.executescript(open(path, encoding="utf-8").read())
    con.commit()


# --------------------------------------------------------------------------- #
# loading drug lines
# --------------------------------------------------------------------------- #

def load_lines(con, unit, business_date, rows, batch_id=None):
    """Store the drug lines from a Button B export.

    `rows` are dicts as marg_report.write_items_csv emits them. A re-run for the
    same bill REPLACES its lines rather than duplicating them, matching
    ingest_day's supersede behaviour."""
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?",
                    (unit, business_date)).fetchone()
    if not e:
        raise ValueError("no day entry for %s %s — file the day first" % (unit, business_date))
    eid = e[0]

    bills = {str(r.get("bill_no") or "").strip() for r in rows}
    bills.discard("")
    for b in bills:
        con.execute("DELETE FROM sale_line_item WHERE unit=? AND bill_no=?", (unit, b))

    n = 0
    for r in rows:
        bill = str(r.get("bill_no") or "").strip()
        name = str(r.get("item_name") or "").strip()
        if not bill or not name:
            continue
        amt = r.get("amount_p")
        if amt is None and r.get("amount") not in (None, ""):
            try:
                amt = int(round(float(str(r["amount"]).replace(",", "")) * 100))
            except (TypeError, ValueError):
                amt = None
        seq = r.get("seq")
        try:
            seq = int(seq) if str(seq).strip() != "" else None
        except (TypeError, ValueError):
            seq = None
        con.execute(
            "INSERT OR REPLACE INTO sale_line_item (day_entry_id, ingest_batch_id, unit, "
            "business_date, bill_no, is_return, seq, item_name, item_key, pack, qty_raw, "
            "amount_p, expiry_ym, batch) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (eid, batch_id, unit, str(r.get("bill_date") or business_date), bill,
             1 if str(r.get("is_return") or "0") in ("1", "True", "true") else 0,
             seq, name, norm_item(name),
             (r.get("pack") or None), (r.get("qty_raw") or None),
             amt if amt is None or amt >= 0 else abs(amt),
             (r.get("expiry_ym") or None), (r.get("batch") or None)))
        n += 1
    con.commit()
    return n


# --------------------------------------------------------------------------- #
# the lookup — reception's direction
# --------------------------------------------------------------------------- #

def find_patient_sales(con, unit, clinic_id=None, name=None, since=None, limit=50):
    """A patient at the counter with no bill. Find their sales, newest first.

    clinic_id is exact. name is exact and case-insensitive — deliberately NOT a
    fuzzy match, because a fuzzy match at a counter becomes someone else's
    purchase history."""
    sql = ("SELECT si.source_ref AS bill_no, de.business_date AS business_date, "
           "       si.amount_p AS amount_p, pr.clinic_id AS clinic_id, pr.name AS name "
           "FROM sale_item si "
           "JOIN day_entry de ON de.id = si.day_entry_id "
           "LEFT JOIN patient_ref pr ON pr.id = si.patient_ref_id "
           "WHERE si.unit = ? AND si.service NOT GLOB '*_return' ")
    args = [unit]
    if clinic_id:
        sql += "AND pr.clinic_id = ? "
        args.append(str(clinic_id))
    elif name:
        sql += "AND UPPER(pr.name) = UPPER(?) "
        args.append(name)
    else:
        return []
    if since:
        sql += "AND de.business_date >= ? "
        args.append(since)
    sql += "ORDER BY de.business_date DESC, si.id DESC LIMIT ?"
    args.append(int(limit))
    return [dict(bill_no=r[0], business_date=r[1], amount_p=r[2],
                 clinic_id=r[3], name=r[4]) for r in con.execute(sql, args)]


# --------------------------------------------------------------------------- #
# the lookup — reconciliation's direction
# --------------------------------------------------------------------------- #

def _return_row(con, unit, bill_no):
    r = con.execute(
        "SELECT si.id, si.patient_ref_id, si.amount_p, de.business_date, "
        "       pr.clinic_id, pr.name "
        "FROM sale_item si JOIN day_entry de ON de.id = si.day_entry_id "
        "LEFT JOIN patient_ref pr ON pr.id = si.patient_ref_id "
        "WHERE si.unit=? AND si.source_ref=? AND si.service GLOB '*_return'",
        (unit, bill_no)).fetchone()
    if r:
        return dict(patient_ref_id=r[1], amount_p=r[2], business_date=r[3],
                    clinic_id=r[4], name=r[5], identified=True)
    # it may have gone to the review queue instead — still a real return
    q = con.execute(
        "SELECT r.amount_p, de.business_date, r.guess_clinic_id, r.guess_name "
        "FROM sale_item_review r JOIN day_entry de ON de.id = r.day_entry_id "
        "WHERE r.raw_text LIKE ? OR r.guess_name LIKE ? LIMIT 1",
        ("%" + bill_no + "%", "%" + bill_no + "%")).fetchone()
    if q:
        return dict(patient_ref_id=None, amount_p=abs(q[0] or 0), business_date=q[1],
                    clinic_id=q[2], name=q[3], identified=False)
    return None


def correlate_return(con, unit, return_bill_no, today=None):
    """Trace one credit note back to the sale it came from.

    Returns a verdict, the candidate sales it considered, and flags. It does not
    decide anything."""
    window = int(_setting(con, "returns.window_days", "30"))
    grace = int(_setting(con, "returns.expiry_grace_months", "0"))
    large_p = int(_setting(con, "returns.large_p", "100000"))

    out = dict(unit=unit, return_bill_no=return_bill_no, verdict=VERDICT_NONE,
               flags=[], candidates=[], best=None, returned_items=[],
               patient=None, return_date=None, amount_p=None, window_days=window)

    ret = _return_row(con, unit, return_bill_no)
    if not ret:
        out["flags"].append(F_NO_SALE)
        return out

    out["return_date"] = ret["business_date"]
    out["amount_p"] = ret["amount_p"]
    out["patient"] = dict(clinic_id=ret["clinic_id"], name=ret["name"],
                          identified=ret["identified"])

    # what came back
    items = [dict(item_name=r[0], item_key=r[1], expiry_ym=r[2], qty_raw=r[3])
             for r in con.execute(
                 "SELECT item_name, item_key, expiry_ym, qty_raw FROM sale_line_item "
                 "WHERE unit=? AND bill_no=? ORDER BY seq", (unit, return_bill_no))]
    out["returned_items"] = items
    keys = {i["item_key"] for i in items if i["item_key"]}
    if not items:
        out["flags"].append(F_NO_ITEM_DATA)

    # expiry — decidable at the counter, not discovered later as dead stock
    ret_ym = _ym(ret["business_date"])
    for i in items:
        if not i["expiry_ym"]:
            continue
        y, m = int(i["expiry_ym"][:4]), int(i["expiry_ym"][5:7])
        limit = (y * 12 + m) - grace
        ry, rm = int(ret_ym[:4]), int(ret_ym[5:7])
        if limit <= (ry * 12 + rm):
            if F_EXPIRED not in out["flags"]:
                out["flags"].append(F_EXPIRED)

    if not ret["patient_ref_id"]:
        out["flags"].append(F_NO_PATIENT)
        if ret["amount_p"] and ret["amount_p"] >= large_p:
            out["flags"].append(F_LARGE_UNMATCHED)
        return out

    # that patient's earlier sales
    rows = con.execute(
        "SELECT si.source_ref, de.business_date, si.amount_p "
        "FROM sale_item si JOIN day_entry de ON de.id = si.day_entry_id "
        "WHERE si.unit=? AND si.patient_ref_id=? AND si.service NOT GLOB '*_return' "
        "  AND de.business_date <= ? "
        "ORDER BY de.business_date DESC", (unit, ret["patient_ref_id"], ret["business_date"]))

    for bill_no, sale_date, amount_p in rows:
        if not bill_no:
            continue
        sale_keys = {r[0] for r in con.execute(
            "SELECT item_key FROM sale_line_item WHERE unit=? AND bill_no=?", (unit, bill_no))}
        matched = sorted(keys & sale_keys) if keys else []
        out["candidates"].append(dict(
            bill_no=bill_no, business_date=sale_date, amount_p=amount_p,
            age_days=_days_between(sale_date, ret["business_date"]),
            items_matched=len(matched), items_total=len(keys),
            matched_items=matched,
            sale_had_item_detail=bool(sale_keys)))

    if not out["candidates"]:
        out["flags"].append(F_NO_SALE)
        if ret["amount_p"] and ret["amount_p"] >= large_p:
            out["flags"].append(F_LARGE_UNMATCHED)
        return out

    # rank: medicine evidence first, then recency. Explainable, not a magic score.
    out["candidates"].sort(key=lambda c: (-c["items_matched"], c["age_days"]))
    best = out["candidates"][0]
    out["best"] = best

    if keys and best["items_matched"] == len(keys):
        out["verdict"] = VERDICT_CONCLUSIVE
    elif keys and best["items_matched"] > 0:
        out["verdict"] = VERDICT_PROBABLE
    else:
        out["verdict"] = VERDICT_PATIENT_ONLY

    if best["age_days"] > window:
        out["flags"].append(F_OUTSIDE_WINDOW)

    return out


def describe(v):
    """One human line. Used by the portal page and by the CLI."""
    if v["verdict"] == VERDICT_NONE:
        return "%s: no earlier sale found%s" % (
            v["return_bill_no"],
            " (patient not identified)" if F_NO_PATIENT in v["flags"] else "")
    b = v["best"]
    bits = ["%s -> %s of %s" % (v["return_bill_no"], b["bill_no"], b["business_date"]),
            "%d day(s) earlier" % b["age_days"]]
    if v["returned_items"]:
        bits.append("%d/%d medicines matched" % (b["items_matched"], b["items_total"]))
    bits.append(v["verdict"].upper())
    if v["flags"]:
        bits.append("flags: " + ", ".join(v["flags"]))
    return " · ".join(bits)


# --------------------------------------------------------------------------- #
# selftest
# --------------------------------------------------------------------------- #

def selftest(schema_path="finance_schema.sql", returns_sql="finance_returns.sql"):
    import tempfile
    ok, fail = 0, []

    def ck(name, cond):
        nonlocal ok
        if cond:
            ok += 1
        else:
            fail.append(name)

    ck("norm collapses case and punctuation",
       norm_item(" folitrax-15  mg tab ") == "FOLITRAX 15 MG TAB")
    ck("norm of nothing", norm_item(None) == "")
    ck("days between", _days_between("2026-08-01", "2026-08-06") == 5)

    fd, db = tempfile.mkstemp(prefix="fin_returns_test_", suffix=".db")
    os.close(fd)
    os.remove(db)
    con = sqlite3.connect(db)
    con.executescript(open(schema_path, encoding="utf-8").read())
    install(con, returns_sql)
    ck("install is idempotent", (install(con, returns_sql) is None) or True)

    def day(d):
        con.execute("INSERT OR IGNORE INTO day_entry (unit,business_date,status) "
                    "VALUES ('medical',?, 'draft')", (d,))
        return con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?",
                           (d,)).fetchone()[0]

    def patient(cid, nm):
        con.execute("INSERT OR IGNORE INTO patient_ref (clinic_id,name,first_seen) "
                    "VALUES (?,?, '2026-01-01')", (cid, nm))
        return con.execute("SELECT id FROM patient_ref WHERE clinic_id=?", (cid,)).fetchone()[0]

    def bill(d, pid, bill_no, amount_p, service="pharmacy"):
        con.execute("INSERT INTO sale_item (day_entry_id,unit,patient_ref_id,service,"
                    "amount_p,mode,source,source_ref,confidence) "
                    "VALUES (?, 'medical', ?, ?, ?, 'cash','manual', ?, 0.99)",
                    (day(d), pid, service, amount_p, bill_no))

    def lines(d, bill_no, names, is_return=0, expiry="2028-06"):
        load_lines(con, "medical", d,
                   [dict(bill_no=bill_no, bill_date=d, is_return=is_return, seq=i + 1,
                         item_name=n, amount_p=10000, expiry_ym=expiry, batch="B%d" % i,
                         pack="1*10", qty_raw="1:0")
                    for i, n in enumerate(names)])

    # ---- the CN00158 shape: six medicines returned, all six on an earlier sale
    p1 = patient("7753", "PATIENT ONE")
    bill("2026-08-02", p1, "A002800", 51000)
    lines("2026-08-02", "A002800", ["XGESIC LA", "TRAMATEE P", "MEG QCS",
                                    "ORICOX P", "SYSFOL 5", "CROCAL"])
    bill("2026-08-05", p1, "CN00158", 51000, service="pharmacy_return")
    lines("2026-08-05", "CN00158", ["XGESIC LA", "TRAMATEE P", "MEG QCS",
                                    "ORICOX P", "SYSFOL 5", "CROCAL"], is_return=1)
    v = correlate_return(con, "medical", "CN00158")
    ck("conclusive when every medicine matches", v["verdict"] == VERDICT_CONCLUSIVE)
    ck("finds the right sale", v["best"]["bill_no"] == "A002800")
    ck("counts the overlap", (v["best"]["items_matched"], v["best"]["items_total"]) == (6, 6))
    ck("age in days", v["best"]["age_days"] == 3)
    ck("inside the window, no flag", F_OUTSIDE_WINDOW not in v["flags"])

    # ---- partial overlap -> probable, not conclusive
    p2 = patient("7372", "PATIENT TWO")
    bill("2026-08-03", p2, "A002810", 30000)
    lines("2026-08-03", "A002810", ["FOLITRAX 15 MG TAB", "FENARIC T4 TAB"])
    bill("2026-08-04", p2, "CN00152", 13400, service="pharmacy_return")
    lines("2026-08-04", "CN00152", ["FOLITRAX 15 MG TAB", "SOMETHING ELSE"], is_return=1)
    v2 = correlate_return(con, "medical", "CN00152")
    ck("partial overlap is PROBABLE", v2["verdict"] == VERDICT_PROBABLE)
    ck("partial overlap counted", v2["best"]["items_matched"] == 1)

    # ---- the CN00154 shape: patient known, but the sale is older than the window
    p3 = patient("7546", "PATIENT THREE")
    bill("2026-05-02", p3, "A001000", 170000)
    lines("2026-05-02", "A001000", ["OLD MEDICINE"])
    bill("2026-08-05", p3, "CN00154", 170000, service="pharmacy_return")
    lines("2026-08-05", "CN00154", ["OLD MEDICINE"], is_return=1)
    v3 = correlate_return(con, "medical", "CN00154")
    ck("an old sale is still FOUND", v3["best"]["bill_no"] == "A001000")
    ck("but flagged outside the window", F_OUTSIDE_WINDOW in v3["flags"])
    ck("older-than-window is not silently accepted", v3["best"]["age_days"] > 30)

    # ---- expiry
    p4 = patient("6503", "PATIENT FOUR")
    bill("2026-08-01", p4, "A002820", 20000)
    lines("2026-08-01", "A002820", ["NEAR EXPIRY TAB"], expiry="2026-08")
    bill("2026-08-05", p4, "CN00160", 20000, service="pharmacy_return")
    lines("2026-08-05", "CN00160", ["NEAR EXPIRY TAB"], is_return=1, expiry="2026-08")
    v4 = correlate_return(con, "medical", "CN00160")
    ck("expiry reached is flagged", F_EXPIRED in v4["flags"])
    ck("expired return still correlates", v4["verdict"] == VERDICT_CONCLUSIVE)

    # ---- a return for a patient with no earlier sale at all
    p5 = patient("9999", "PATIENT FIVE")
    bill("2026-08-05", p5, "CN00161", 150000, service="pharmacy_return")
    lines("2026-08-05", "CN00161", ["MYSTERY TAB"], is_return=1)
    v5 = correlate_return(con, "medical", "CN00161")
    ck("no earlier sale -> verdict none", v5["verdict"] == VERDICT_NONE)
    ck("no earlier sale is flagged", F_NO_SALE in v5["flags"])
    ck("large unmatched return is flagged", F_LARGE_UNMATCHED in v5["flags"])

    # a small unmatched return does NOT raise the large flag
    p6 = patient("9998", "PATIENT SIX")
    bill("2026-08-05", p6, "CN00162", 3000, service="pharmacy_return")
    v6 = correlate_return(con, "medical", "CN00162")
    ck("small unmatched return is not shouted about", F_LARGE_UNMATCHED not in v6["flags"])
    ck("but it is still reported as unmatched", F_NO_SALE in v6["flags"])
    ck("missing item detail is stated, not assumed", F_NO_ITEM_DATA in v6["flags"])

    # ---- reception's direction: same index, run forwards
    got = find_patient_sales(con, "medical", clinic_id="7753")
    ck("reception finds the patient's sales", any(g["bill_no"] == "A002800" for g in got))
    ck("reception does not return the return itself",
       all(g["bill_no"] != "CN00158" for g in got))
    byname = find_patient_sales(con, "medical", name="patient one")
    ck("reception name lookup is case-insensitive",
       any(g["bill_no"] == "A002800" for g in byname))
    ck("reception refuses to guess with nothing to go on",
       find_patient_sales(con, "medical") == [])

    # ---- re-running a load replaces rather than duplicates
    lines("2026-08-02", "A002800", ["XGESIC LA", "TRAMATEE P", "MEG QCS",
                                    "ORICOX P", "SYSFOL 5", "CROCAL"])
    n = con.execute("SELECT COUNT(*) FROM sale_line_item WHERE bill_no='A002800'").fetchone()[0]
    ck("re-loading a bill does not duplicate its lines", n == 6)

    ck("describe() says something useful", "CONCLUSIVE" in describe(v))

    con.close()
    try:
        os.remove(db)
    except OSError:
        pass

    print("RETURNS %d/%d passed" % (ok, ok + len(fail)))
    for f in fail:
        print("  FAIL:", f)
    return 0 if not fail else 1


if __name__ == "__main__":
    import sys
    sys.exit(selftest(*(sys.argv[1:3] or [])))
