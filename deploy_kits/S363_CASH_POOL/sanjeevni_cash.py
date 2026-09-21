#!/usr/bin/env python3
# =============================================================================
#  sanjeevni_cash.py  ·  v1.1  ·  kits S361_CASH_CORE, S363_CASH_POOL  ·  Session 280 (Sanjeevni)
#
#  THE ONE CASH CALCULATION FOR SANJEEVNI.
#  Where every rupee of the counter's cash is, on any date: in Darpan's drawer,
#  with Dr Bhawna, with Dr Manoj, in the bank -- and the month table the owner
#  asked for (21-Sep): total sale, UPI, cash, home and procedure medicine.
#
#  WHY IT EXISTS (S280_CASH_ARCHITECTURE_AND_MONTH_TABLE.md): two rulings built
#  two models of the same cash, both live. S189 wrote a handover to a doctor as
#  a LOCATION note in cash_custody_event; S194/S243/S359 write it as cash OUT of
#  the drawer in cash_movement. August holds six handovers one way and two the
#  other, so every screen that picked one register showed a different drawer
#  (4,36,597 · 2,29,459 · 2,29,452 · 2,29,652, and negatives on the workbench).
#
#  THE RULE HERE: start from a COUNTED position (cash_anchor), then move day by
#  day; every handover that left the drawer after the anchor is read from BOTH
#  registers and counted ONCE. Nothing is guessed: a figure this cannot prove
#  is returned as None with the reason, never as 0.
#
#  PROVEN against two physical counts: 17-Aug-2026 (drawer 0, Dr Bhawna
#  1,56,235, Dr Manoj 18,963) and 25-Aug-2026 (drawer 43,903, before that day's
#  handover). August closes at drawer 7, Dr Bhawna 2,98,155, Dr Manoj 79,703.
#
#  v1.1 (S363) -- THE OWNER'S RULING OF 21-SEP-2026: "Darpan handed all cash daily
#  from 1st to 19th Sept, and Dr Bhawna's receivings and yours go to the same pool,
#  so maintain that flow; I will mark each day of Sept in approvals."  So:
#    * the doctors hold ONE POOL (with_doctors = Dr Bhawna + Dr Manoj + pool);
#    * a day the owner APPROVES is a day whose drawer cash went to the pool --
#      unless a handover is already recorded for it (then that record stands);
#    * a cash deposit made from the pool is its own record (cash_pool_deposit),
#      never a drawer movement -- 03-Sep Rs 3,00,000 and 15-Sep Rs 1,00,000.
#  So until a day is approved its cash shows in the drawer, labelled as waiting.
#
#  Read-only against every existing table. It writes only its own three tables,
#  and only through seed_august(), which is idempotent and audited.
#  Stdlib only.
# =============================================================================

import datetime as dt
import json
import sqlite3
import sys

VERSION = "1.1"
UNIT = "medical"
DOCTORS = ("dr_bhawna", "dr_manoj")
DRAWER_SIDE = ("drawer", "counter")          # custody names for Darpan's side

SCHEMA = """
CREATE TABLE IF NOT EXISTS cash_anchor (
    unit TEXT NOT NULL, anchor_date TEXT NOT NULL,
    drawer_p INTEGER NOT NULL, bhawna_p INTEGER NOT NULL, manoj_p INTEGER NOT NULL,
    bank_p INTEGER NOT NULL DEFAULT 0,
    pre_anchor_expense_uids TEXT NOT NULL DEFAULT '[]',
    pre_anchor_custody_ids TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL, note TEXT, entered_by TEXT, entered_at TEXT,
    PRIMARY KEY (unit, anchor_date));
CREATE TABLE IF NOT EXISTS cash_handover_cover (
    id INTEGER PRIMARY KEY,
    unit TEXT NOT NULL, handover_src TEXT NOT NULL CHECK (handover_src IN ('movement','custody')),
    handover_id INTEGER NOT NULL, covers_date TEXT NOT NULL, amount_p INTEGER NOT NULL,
    note TEXT, entered_by TEXT, entered_at TEXT,
    UNIQUE (handover_src, handover_id, covers_date));
CREATE TABLE IF NOT EXISTS cash_bill_ruling (
    id INTEGER PRIMARY KEY,
    unit TEXT NOT NULL, business_date TEXT NOT NULL, bill_no TEXT NOT NULL,
    amount_p INTEGER NOT NULL,
    ruling TEXT NOT NULL CHECK (ruling IN ('received_elsewhere')),
    received_at_place TEXT, note TEXT, ruled_by TEXT, ruled_at TEXT,
    UNIQUE (unit, business_date, bill_no));
CREATE TABLE IF NOT EXISTS cash_pool_deposit (
    id INTEGER PRIMARY KEY,
    unit TEXT NOT NULL, deposit_date TEXT NOT NULL, amount_p INTEGER NOT NULL,
    bank TEXT NOT NULL, place TEXT, evidence TEXT, note TEXT, entered_by TEXT, entered_at TEXT,
    UNIQUE (unit, deposit_date, amount_p, bank));
CREATE TABLE IF NOT EXISTS cash_period_close (
    id INTEGER PRIMARY KEY,
    unit TEXT NOT NULL, date_from TEXT NOT NULL, date_to TEXT NOT NULL,
    residual_p INTEGER NOT NULL, ruling TEXT NOT NULL CHECK (ruling IN ('rounding')),
    note TEXT, ruled_by TEXT, ruled_at TEXT,
    UNIQUE (unit, date_from, date_to));
"""


def ensure_schema(con):
    """Statement by statement (never executescript, which would commit a caller's
    open transaction and so defeat the all-or-nothing seed)."""
    for stmt in [s.strip() for s in SCHEMA.split(";") if s.strip()]:
        con.execute(stmt)


def _has(con, name):
    return con.execute("SELECT 1 FROM sqlite_master WHERE name=?", (name,)).fetchone() is not None


def _j(s):
    try:
        return json.loads(s or "[]")
    except ValueError:
        return []


# ------------------------------------------------------------------ the anchor
def anchor(con, unit=UNIT):
    """The newest counted position. None when no anchor is recorded -- then no
    position can be stated, and every caller must say so rather than show 0."""
    if not _has(con, "cash_anchor"):
        return None
    r = con.execute("SELECT * FROM cash_anchor WHERE unit=? ORDER BY anchor_date DESC LIMIT 1",
                    (unit,)).fetchone()
    if not r:
        return None
    cols = [c[0] for c in con.execute("SELECT * FROM cash_anchor LIMIT 0").description]
    a = dict(zip(cols, r))
    a["pre_anchor_expense_uids"] = _j(a["pre_anchor_expense_uids"])
    a["pre_anchor_custody_ids"] = _j(a["pre_anchor_custody_ids"])
    return a


# ------------------------------------------------------------------ handovers
def handovers(con, since, until, unit=UNIT, anchor_custody_ids=()):
    """Every rupee that left Darpan's drawer on (since..until), from BOTH
    registers, each counted once.

    cash_movement direction 'out' (any party) is one handover each.
    cash_custody_event FROM the drawer side TO a doctor or the bank is one
    handover -- unless it is part of the anchor, or a cash_movement of the same
    date, party and amount already carries it (darpan_kal refuses to land such
    a pair, and an old tab could have written both)."""
    out = []
    mv = con.execute(
        "SELECT m.id, e.business_date d, m.party, m.amount_p, COALESCE(m.reference,'') ref "
        "FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id "
        "WHERE e.unit=? AND m.direction='out' AND e.business_date BETWEEN ? AND ? "
        "ORDER BY e.business_date, m.id", (unit, since, until)).fetchall()
    keys = set()
    for mid, d, party, amt, ref in mv:
        out.append(dict(src="movement", id=mid, date=d, to=party, amount_p=int(amt), note=ref))
        keys.add((d, party, int(amt)))
    if _has(con, "cash_custody_event"):
        for cid, d, frm, to, amt, note in con.execute(
                "SELECT id, event_date, from_party, to_party, amount_p, COALESCE(note,'') "
                "FROM cash_custody_event WHERE unit=? AND event_date BETWEEN ? AND ? "
                "ORDER BY event_date, id", (unit, since, until)):
            if cid in anchor_custody_ids or frm not in DRAWER_SIDE or to in DRAWER_SIDE:
                continue
            if (d, to, int(amt)) in keys:
                continue
            out.append(dict(src="custody", id=cid, date=d, to=to, amount_p=int(amt), note=note))
    out.sort(key=lambda h: (h["date"], h["src"], h["id"]))
    return out


# ------------------------------------------------------------------ one day
def _rulings(con, unit):
    if not _has(con, "cash_bill_ruling"):
        return {}
    res = {}
    for d, bill, amt in con.execute("SELECT business_date, bill_no, amount_p FROM cash_bill_ruling "
                                    "WHERE unit=? AND ruling='received_elsewhere'", (unit,)):
        res.setdefault(d, []).append((str(bill), int(amt)))
    return res


APPROVED = ("approved", "locked")


def pool_deposits(con, unit=UNIT):
    if not _has(con, "cash_pool_deposit"):
        return []
    return [dict(id=r[0], date=r[1], amount_p=int(r[2]), bank=r[3], place=r[4], note=r[5] or "")
            for r in con.execute("SELECT id, deposit_date, amount_p, bank, place, note FROM cash_pool_deposit "
                                 "WHERE unit=? ORDER BY deposit_date, id", (unit,))]


def _covered(con, unit):
    if not _has(con, "cash_handover_cover"):
        return set()
    return {r[0] for r in con.execute("SELECT DISTINCT covers_date FROM cash_handover_cover WHERE unit=?", (unit,))}


def days(con, date_from, date_to, unit=UNIT):
    """Per filed day from the anchor: the day's books, where its cash went, and
    where every rupee stands at the close. Days before the anchor are refused.
    v1.1: an approved day with no recorded handover sends its drawer cash to the
    doctors' pool (the owner's ruling of 21-Sep); a pool deposit leaves the pool."""
    a = anchor(con, unit)
    if not a:
        return dict(ok=False, error="no_anchor",
                    message="no counted cash position is recorded, so no position can be stated")
    start = max(date_from, a["anchor_date"])
    ex_uids = set(a["pre_anchor_expense_uids"])
    hand = handovers(con, a["anchor_date"], date_to, unit, set(a["pre_anchor_custody_ids"]))
    by_day = {}
    for h in hand:
        by_day.setdefault(h["date"], []).append(h)
    covered = _covered(con, unit)
    deps = [x for x in pool_deposits(con, unit) if a["anchor_date"] <= x["date"] <= date_to]
    rul = _rulings(con, unit)
    pos = dict(drawer=a["drawer_p"], dr_bhawna=a["bhawna_p"], dr_manoj=a["manoj_p"], pool=0, bank=a["bank_p"])

    def snap():
        p = dict(pos)
        p["with_doctors"] = p["dr_bhawna"] + p["dr_manoj"] + p["pool"]
        return p
    rows = []
    for (eid, d, status, cash_in, upi, revenue, noncash, back, adjust) in con.execute(
            "SELECT v.day_entry_id, v.business_date, e.status, v.cash_in_p, upi_in_p, revenue_p, noncash_p, "
            " cash_back_p, adjust_p FROM v_day_cash v JOIN day_entry e ON e.id=v.day_entry_id "
            "WHERE v.unit=? AND v.business_date BETWEEN ? AND ? ORDER BY v.business_date, v.day_entry_id",
            (unit, a["anchor_date"], date_to)):
        exp = con.execute("SELECT COALESCE(SUM(amount_p),0) FROM day_expense WHERE day_entry_id=? "
                          "AND amount_known=1 AND COALESCE(expense_uid,'') NOT IN (%s)"
                          % ",".join("?" * len(ex_uids) or ["''"]) if ex_uids else
                          "SELECT COALESCE(SUM(amount_p),0) FROM day_expense WHERE day_entry_id=? AND amount_known=1",
                          (eid, *sorted(ex_uids)) if ex_uids else (eid,)).fetchone()[0]
        elsewhere = sum(a2 for _, a2 in rul.get(d, []))
        into_drawer = int(cash_in) - int(noncash) - int(exp) + int(back) + int(adjust)
        pos["drawer"] += into_drawer
        moved = []
        for h in by_day.get(d, []):
            pos["drawer"] -= h["amount_p"]
            pos[h["to"] if h["to"] in pos else "bank"] += h["amount_p"]
            moved.append(h)
        implied = (status in APPROVED and not moved and d not in covered and into_drawer > 0)
        if implied:
            h = dict(src="approval", id=None, date=d, to="pool", amount_p=into_drawer,
                     note="the owner approved this day: its cash went to the doctors' pool (ruling of 21-Sep)")
            pos["drawer"] -= into_drawer
            pos["pool"] += into_drawer
            moved.append(h)
        banked = []
        while deps and deps[0]["date"] <= d:
            x = deps.pop(0)
            pos["pool"] -= x["amount_p"]
            pos["bank"] += x["amount_p"]
            banked.append(x)
        if d < start:
            continue
        rows.append(dict(date=d, status=status, sale_p=int(revenue), upi_p=int(upi), cash_p=int(cash_in),
                         without_cash_p=int(noncash) - elsewhere, received_elsewhere_p=elsewhere,
                         expense_p=int(exp), adjust_p=int(adjust) + int(back),
                         into_drawer_p=into_drawer, handed=moved, banked=banked,
                         waiting_approval=(status not in APPROVED and not moved and d not in covered),
                         close=snap()))
    if deps and rows:                                      # a deposit after the last filed day
        for x in deps:
            pos["pool"] -= x["amount_p"]; pos["bank"] += x["amount_p"]
            rows[-1]["banked"].append(x)
        rows[-1]["close"] = snap()
    return dict(ok=True, anchor=a, rows=rows)


def month_moves(con, unit=UNIT):
    """{ym: {to_manoj_p, to_bhawna_p, to_pool_p, to_bank_p}} from the anchor on --
    every handover once (both registers, and approved days to the pool) and every
    pool deposit."""
    r = days(con, "0000-00-00", "9999-12-31", unit)
    out = {}
    if not r.get("ok"):
        return out
    key = {"dr_manoj": "to_manoj_p", "dr_bhawna": "to_bhawna_p", "pool": "to_pool_p", "bank": "to_bank_p"}
    for row in r["rows"]:
        m = out.setdefault(row["date"][:7], dict(to_manoj_p=0, to_bhawna_p=0, to_pool_p=0, to_bank_p=0, to_other_p=0))
        for h in row["handed"]:
            m[key.get(h["to"], "to_other_p")] += h["amount_p"]
        for x in row["banked"]:
            m["to_bank_p"] += x["amount_p"]
    return out


def position(con, as_of, unit=UNIT):
    """Where the cash is at the close of as_of."""
    r = days(con, "0000-00-00", as_of, unit)
    if not r["ok"]:
        return r
    a = r["anchor"]
    last = r["rows"][-1]["close"] if r["rows"] else dict(
        drawer=a["drawer_p"], dr_bhawna=a["bhawna_p"], dr_manoj=a["manoj_p"], pool=0, bank=a["bank_p"],
        with_doctors=a["bhawna_p"] + a["manoj_p"])
    waiting = [x["date"] for x in r["rows"] if x["waiting_approval"]]
    return dict(ok=True, as_of=as_of, anchor_date=a["anchor_date"], **last,
                in_unit=last["drawer"] + last["with_doctors"],
                waiting_days=waiting,
                waiting_p=sum(x["into_drawer_p"] for x in r["rows"] if x["waiting_approval"]))


# ------------------------------------------------------------------ coverage
def coverage(con, date_from, date_to, unit=UNIT):
    """Which counter days are paid over, and by which handover. A day is DONE
    when its drawer cash is fully covered (within the period's closed residual)."""
    r = days(con, date_from, date_to, unit)
    if not r["ok"]:
        return r
    cov = {}
    if _has(con, "cash_handover_cover"):
        for src, hid, d, amt in con.execute("SELECT handover_src, handover_id, covers_date, amount_p "
                                            "FROM cash_handover_cover WHERE unit=? AND covers_date BETWEEN ? AND ?",
                                            (unit, date_from, date_to)):
            cov.setdefault(d, []).append(dict(src=src, id=hid, amount_p=int(amt)))
    closes = []
    if _has(con, "cash_period_close"):
        closes = con.execute("SELECT date_from, date_to, residual_p FROM cash_period_close WHERE unit=? "
                             "AND date_to >= ? AND date_from <= ?", (unit, date_from, date_to)).fetchall()
    out = []
    for row in r["rows"]:
        d = row["date"]
        paid = sum(c["amount_p"] for c in cov.get(d, []))
        due = row["into_drawer_p"]
        closed = any(f <= d <= t for f, t, _ in closes)
        implied = any(h.get("src") == "approval" for h in row["handed"])
        out.append(dict(date=d, due_p=due, covered_p=(due if implied else paid), diff_p=(0 if implied else paid - due),
                        by=cov.get(d, []), by_approval=implied,
                        done=implied or (bool(cov.get(d)) and (paid == due or closed))))
    return dict(ok=True, days=out)


# ------------------------------------------------------------------ the month table
def month_rows(con, unit=UNIT):
    """The owner's month table (21-Sep): total sale, UPI, cash, home medicine,
    procedure medicine, other billed-without-cash, cash received elsewhere, and
    the cash income. Marg's own sale beside it for the days Marg's bill-wise
    export reached the server, with the number of days it covers."""
    rul = {}
    if _has(con, "cash_bill_ruling"):
        for d, amt in con.execute("SELECT business_date, amount_p FROM cash_bill_ruling WHERE unit=? "
                                  "AND ruling='received_elsewhere'", (unit,)):
            rul[d[:7]] = rul.get(d[:7], 0) + int(amt)
    rows = {}
    for ym, n, sale, upi, cash in con.execute(
            "SELECT substr(business_date,1,7), COUNT(*), SUM(revenue_p), SUM(upi_in_p), SUM(cash_in_p) "
            "FROM v_day_cash WHERE unit=? GROUP BY 1 ORDER BY 1", (unit,)):
        rows[ym] = dict(ym=ym, days=n, sale_p=int(sale or 0), upi_p=int(upi or 0), cash_p=int(cash or 0),
                        home_p=0, proc_p=0, other_p=0, received_elsewhere_p=rul.get(ym, 0),
                        marg_sale_p=None, marg_days=0)
    for ym, head, amt in con.execute(
            "SELECT substr(e.business_date,1,7), b.head, SUM(b.amount_p) FROM day_noncash_bill b "
            "JOIN day_entry e ON e.id=b.day_entry_id WHERE b.unit=? GROUP BY 1, 2", (unit,)):
        if ym in rows:
            k = {"home_medicine": "home_p", "procedure_medicine": "proc_p"}.get(head, "other_p")
            rows[ym][k] += int(amt or 0)
    if _has(con, "sale_bill"):
        for ym, amt, nd in con.execute(
                "SELECT substr(business_date,1,7), SUM(net_p), COUNT(DISTINCT business_date) FROM sale_bill "
                "WHERE unit=? GROUP BY 1", (unit,)):
            if ym in rows:
                rows[ym]["marg_sale_p"], rows[ym]["marg_days"] = int(amt or 0), int(nd)
    for m in rows.values():
        m["other_p"] -= m["received_elsewhere_p"]          # a ruled bill is paid, not without-cash
        m["cash_income_p"] = m["cash_p"] - m["home_p"] - m["proc_p"] - m["other_p"]
        m["income_p"] = m["cash_income_p"] + m["upi_p"]
    return [rows[k] for k in sorted(rows)]


# ------------------------------------------------------------------ seeding (owner's rulings, 21-Sep)
AUG_ANCHOR = dict(
    anchor_date="2026-08-17", drawer_p=0, bhawna_p=15623500, manoj_p=1896300, bank_p=0,
    pre_anchor_expense_uids=["exS202darpan20k17aug"], pre_anchor_custody_ids=[1, 2, 3, 4],
    source="cash_count 2026-08-17 (physical count, 1,75,198) + cash_custody_event 1-4 (S189)",
    note="Counted before the 17-Aug sales: drawer emptied; Dr Bhawna 1,56,235 (7,309 of 06-Aug + 3,926 of "
         "15-Aug + 1,45,000); Dr Manoj 18,963. The 20,000 August salary advance was paid out of that "
         "clearing (day_expense exS202darpan20k17aug), so it is not a charge on the 17-Aug sales. "
         "Re-proved by the 25-Aug count: drawer 43,903 before that day's handover.")

# (handover_src, match: date, party, amount) -> covers
AUG_COVER = [
    (("movement", "2026-08-20", "dr_manoj", 5193000), [("2026-08-17", 1340100), ("2026-08-18", 1846900),
                                                      ("2026-08-19", 1512400), ("2026-08-20", 493600)]),
    (("movement", "2026-08-25", "dr_bhawna", 4390000), [("2026-08-21", 2141300), ("2026-08-22", 1492200),
                                                       ("2026-08-24", 756500)]),
    (("custody", "2026-08-27", "dr_bhawna", 2313000), [("2026-08-25", 1580900), ("2026-08-26", 732100)]),
    (("movement", "2026-08-31", "dr_bhawna", 2618000), [("2026-08-27", 2618000)]),
    (("movement", "2026-08-31", "dr_bhawna", 871000), [("2026-08-28", 871000)]),
    (("movement", "2026-08-31", "dr_bhawna", 1600000), [("2026-08-29", 1600000)]),
    (("movement", "2026-08-31", "dr_bhawna", 2400000), [("2026-08-31", 2400000)]),
    (("custody", "2026-08-31", "dr_manoj", 881000), [("2026-08-31", 881000)]),
]
AUG_RULING = dict(business_date="2026-08-20", bill_no="2777", amount_p=300000,
                  received_at_place="clinic_counter",
                  note="Owner, 21-Sep-2026: 'Pawan Fibre cast' -- the patient paid at the clinic counter for the "
                       "procedure and later needed a pharmacy bill for the plaster material. A Sanjeevni sale, paid; "
                       "the cash is with us. Received, never pending.")
AUG_CLOSE = dict(date_from="2026-08-17", date_to="2026-08-31", residual_p=700,
                 note="Rs 7 left in the drawer by four handovers that differ from their days by -3, +1, -6, +1. "
                      "Closed as rounding (within the Rs 50 tolerance of darpan_kal.tolerance_p), carried in the drawer.")


def _find_handover(con, src, d, party, amt, unit):
    if src == "movement":
        r = con.execute("SELECT m.id FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id "
                        "WHERE e.unit=? AND e.business_date=? AND m.direction='out' AND m.party=? AND m.amount_p=?",
                        (unit, d, party, amt)).fetchall()
    else:
        r = con.execute("SELECT id FROM cash_custody_event WHERE unit=? AND event_date=? AND to_party=? "
                        "AND amount_p=? AND from_party IN ('drawer','counter')", (unit, d, party, amt)).fetchall()
    if len(r) != 1:
        raise RuntimeError("expected exactly one %s handover on %s to %s of %d paise, found %d"
                           % (src, d, party, amt, len(r)))
    return r[0][0]


def seed_august(con, who, now, unit=UNIT):
    """Idempotent. Refuses (raises, writes nothing) if any handover it names is
    not found exactly once, or if a row it would write already exists with
    different content. Returns a dict of what it wrote."""
    ensure_schema(con)
    wrote = dict(anchor=0, cover=0, ruling=0, close=0)
    a = AUG_ANCHOR
    ex = con.execute("SELECT drawer_p, bhawna_p, manoj_p FROM cash_anchor WHERE unit=? AND anchor_date=?",
                     (unit, a["anchor_date"])).fetchone()
    if ex and tuple(ex) != (a["drawer_p"], a["bhawna_p"], a["manoj_p"]):
        raise RuntimeError("cash_anchor for %s exists with different figures -- not overwritten" % a["anchor_date"])
    count = con.execute("SELECT counted_p FROM cash_count WHERE unit=? AND business_date=?",
                        (unit, a["anchor_date"])).fetchone()
    if not count or int(count[0]) != a["drawer_p"] + a["bhawna_p"] + a["manoj_p"]:
        raise RuntimeError("the anchor does not add up to the physical count of %s" % a["anchor_date"])
    if not ex:
        con.execute("INSERT INTO cash_anchor (unit, anchor_date, drawer_p, bhawna_p, manoj_p, bank_p, "
                    "pre_anchor_expense_uids, pre_anchor_custody_ids, source, note, entered_by, entered_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (unit, a["anchor_date"], a["drawer_p"], a["bhawna_p"], a["manoj_p"], a["bank_p"],
                     json.dumps(a["pre_anchor_expense_uids"]), json.dumps(a["pre_anchor_custody_ids"]),
                     a["source"], a["note"], who, now))
        wrote["anchor"] = 1
    for (src, d, party, amt), covers in AUG_COVER:
        hid = _find_handover(con, src, d, party, amt, unit)
        if sum(c for _, c in covers) != amt:
            raise RuntimeError("cover rows for %s %s do not add to the handover" % (src, d))
        for cd, camt in covers:
            cur = con.execute("INSERT OR IGNORE INTO cash_handover_cover (unit, handover_src, handover_id, "
                              "covers_date, amount_p, note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?)",
                              (unit, src, hid, cd, camt, "S361: August handovers mapped to their days", who, now))
            wrote["cover"] += cur.rowcount if cur.rowcount > 0 else 0
    r = AUG_RULING
    nc = con.execute("SELECT b.amount_p FROM day_noncash_bill b JOIN day_entry e ON e.id=b.day_entry_id "
                     "WHERE e.unit=? AND e.business_date=? AND b.bill_no=?",
                     (unit, r["business_date"], r["bill_no"])).fetchone()
    if not nc or int(nc[0]) != r["amount_p"]:
        raise RuntimeError("bill %s of %s is not the %d paise without-cash bill the ruling names"
                           % (r["bill_no"], r["business_date"], r["amount_p"]))
    cur = con.execute("INSERT OR IGNORE INTO cash_bill_ruling (unit, business_date, bill_no, amount_p, ruling, "
                      "received_at_place, note, ruled_by, ruled_at) VALUES (?,?,?,?, 'received_elsewhere', ?,?,?,?)",
                      (unit, r["business_date"], r["bill_no"], r["amount_p"], r["received_at_place"],
                       r["note"], "manoj (owner ruling, recorded by S361)", now))
    wrote["ruling"] = cur.rowcount if cur.rowcount > 0 else 0
    c = AUG_CLOSE
    cur = con.execute("INSERT OR IGNORE INTO cash_period_close (unit, date_from, date_to, residual_p, ruling, "
                      "note, ruled_by, ruled_at) VALUES (?,?,?,?, 'rounding', ?,?,?)",
                      (unit, c["date_from"], c["date_to"], c["residual_p"], c["note"], who, now))
    wrote["close"] = cur.rowcount if cur.rowcount > 0 else 0
    return wrote


SEP_POOL_DEPOSITS = [
    dict(deposit_date="2026-09-03", amount_p=30000000, bank="Yes Bank", place="Bareilly",
         evidence="Yes Bank statement 01-Aug..20-Sep-2026 (owner's PDF, read S280): CASH DEP-SELF-SANJEEVNI MEDICOS-BAREILLY"),
    dict(deposit_date="2026-09-15", amount_p=10000000, bank="Yes Bank", place="Moradabad",
         evidence="Yes Bank statement 01-Aug..20-Sep-2026 (owner's PDF, read S280): CASH DEP-SELF-SANJEEVNI MEDICOS-MORADABAD"),
]
POOL_NOTE = ("Owner, 21-Sep-2026: the cash Dr Bhawna and he receive goes to one pool, and the pool's cash "
             "was deposited to Yes Bank. Recorded from the pool, never as a drawer movement.")


def seed_september(con, who, now, unit=UNIT):
    """Idempotent: the two September pool deposits. Refuses if a cash_movement
    to the bank already carries either (it would then be counted twice)."""
    ensure_schema(con)
    n = 0
    for d in SEP_POOL_DEPOSITS:
        clash = con.execute("SELECT COUNT(*) FROM cash_movement m JOIN day_entry e ON e.id=m.day_entry_id "
                            "WHERE e.unit=? AND m.party='bank' AND m.direction='out' AND m.amount_p=? "
                            "AND e.business_date BETWEEN date(?, '-3 day') AND date(?, '+3 day')",
                            (unit, d["amount_p"], d["deposit_date"], d["deposit_date"])).fetchone()[0]
        if clash:
            raise RuntimeError("a bank deposit of %d paise near %s is already recorded as a drawer movement"
                               % (d["amount_p"], d["deposit_date"]))
        cur = con.execute("INSERT OR IGNORE INTO cash_pool_deposit (unit, deposit_date, amount_p, bank, place, "
                          "evidence, note, entered_by, entered_at) VALUES (?,?,?,?,?,?,?,?,?)",
                          (unit, d["deposit_date"], d["amount_p"], d["bank"], d["place"], d["evidence"],
                           POOL_NOTE, who, now))
        n += cur.rowcount if cur.rowcount > 0 else 0
    return n


# ------------------------------------------------------------------ the proof
CHECKPOINTS = [
    # (label, date, key, expected paise)
    ("17-Aug count: Dr Bhawna", "2026-08-16", None, None),
    ("25-Aug physical count: drawer before that day's handover", "2026-08-24", "drawer", 4390300),
    ("31-Aug: drawer (the Rs 7)", "2026-08-31", "drawer", 700),
    ("31-Aug: Dr Bhawna", "2026-08-31", "dr_bhawna", 29815500),
    ("31-Aug: Dr Manoj", "2026-08-31", "dr_manoj", 7970300),
]


def prove(con, unit=UNIT):
    """Every checkpoint, every August day covered, the month table adding up."""
    res = []
    for label, d, key, want in CHECKPOINTS:
        if key is None:
            continue
        p = position(con, d, unit)
        got = p.get(key) if p.get("ok") else None
        res.append((label, want, got, got == want))
    cv = coverage(con, "2026-08-17", "2026-08-31", unit)
    undone = [x["date"] for x in cv["days"] if not x["done"]] if cv.get("ok") else ["no coverage"]
    res.append(("every counter day 17-31 Aug is paid over", 0, len(undone), not undone))
    ms = {m["ym"]: m for m in month_rows(con, unit)}
    aug = ms.get("2026-08")
    res.append(("August: the Rs 3,000 of 20-Aug is paid, not without-cash",
                0, aug["other_p"] if aug else None, bool(aug) and aug["other_p"] == 0))
    r = days(con, "2026-09-01", "9999-12-31", unit)
    if r.get("ok") and r["rows"]:
        deps = [x for x in pool_deposits(con, unit) if x["date"] >= "2026-09-01"]
        if r["rows"][-1]["date"] >= "2026-09-15":
            res.append(("September: the two pool deposits (3,00,000 + 1,00,000) are recorded once",
                        40000000, sum(x["amount_p"] for x in deps),
                        len(deps) == 2 and sum(x["amount_p"] for x in deps) == 40000000))
        p31 = position(con, "2026-08-31", unit)
        now = r["rows"][-1]["close"]
        into = sum(x["into_drawer_p"] for x in r["rows"])
        dep_p = sum(x["amount_p"] for x in deps)
        res.append(("cash is conserved: in the unit = 31-Aug + September's cash - the deposits",
                    p31["in_unit"] + into - dep_p, now["drawer"] + now["with_doctors"],
                    now["drawer"] + now["with_doctors"] == p31["in_unit"] + into - dep_p))
        out_p = sum(h["amount_p"] for x in r["rows"] for h in x["handed"])
        res.append(("the drawer = the Rs 7 + September's cash - what left it (approved days, recorded handovers)",
                    p31["drawer"] + into - out_p, now["drawer"], now["drawer"] == p31["drawer"] + into - out_p))
    ok_all = all(r[3] for r in res)
    return ok_all, res


def _rs(p):
    if p is None:
        return "--"
    s = "%.0f" % (p / 100.0)
    neg = s.startswith("-")
    s = s.lstrip("-")
    if len(s) > 3:
        head, tail = s[:-3], s[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:]); head = head[:-2]
        if head:
            parts.insert(0, head)
        s = ",".join(parts) + "," + tail
    return ("-" if neg else "") + s


def report(con, unit=UNIT, out=sys.stdout):
    ok, res = prove(con, unit)
    w = out.write
    w("SANJEEVNI CASH -- one calculation (sanjeevni_cash v%s)\n" % VERSION)
    for label, want, got, good in res:
        w("  %s %-58s expected %-10s got %s\n" % ("ok  " if good else "FAIL", label,
                                                  _rs(want) if "Rs" in label or want > 100 else want,
                                                  _rs(got) if isinstance(got, int) and abs(got) > 100 else got))
    for d in ("2026-08-31", dt.date.today().isoformat()):
        p = position(con, d, unit)
        if p.get("ok"):
            w("  position at close of %s: drawer %s (of which waiting for your approval %s, %d day(s)) · "
              "with the doctors (pool) %s · banked since the count %s · in the unit %s\n"
              % (p["as_of"], _rs(p["drawer"]), _rs(p["waiting_p"]), len(p["waiting_days"]),
                 _rs(p["with_doctors"]), _rs(p["bank"]), _rs(p["in_unit"])))
    w("  month      sale        UPI         cash        home     proc    other  paid-elsewhere  cash income   Marg sale (days)\n")
    for m in month_rows(con, unit):
        w("  %s  %10s  %10s  %10s  %7s  %6s  %6s  %8s  %12s   %s\n" % (
            m["ym"], _rs(m["sale_p"]), _rs(m["upi_p"]), _rs(m["cash_p"]), _rs(m["home_p"]), _rs(m["proc_p"]),
            _rs(m["other_p"]), _rs(m["received_elsewhere_p"]), _rs(m["cash_income_p"]),
            ("%s (%d)" % (_rs(m["marg_sale_p"]), m["marg_days"])) if m["marg_sale_p"] is not None else "not on the server"))
    w("PROOF %s\n" % ("GREEN" if ok else "RED"))
    return ok


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["report", "seed"])
    ap.add_argument("--db", required=True)
    ap.add_argument("--who", default="S361")
    a = ap.parse_args()
    if a.cmd == "report":
        c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
        sys.exit(0 if report(c) else 1)
    c = sqlite3.connect(a.db, isolation_level=None)
    try:
        c.execute("BEGIN IMMEDIATE")
        _now = dt.datetime.now().replace(microsecond=0).isoformat()
        w = seed_august(c, a.who, _now)
        w["pool_deposits"] = seed_september(c, a.who, _now)
        ok, _ = prove(c)
        if not ok:
            c.execute("ROLLBACK")
            report(c)
            print("SEED REFUSED -- the proof is red; nothing written")
            sys.exit(2)
        c.execute("COMMIT")
        print("SEEDED %s" % json.dumps(w))
        sys.exit(0)
    except Exception as e:
        if c.in_transaction:
            c.execute("ROLLBACK")
        print("SEED REFUSED -- %s; nothing written" % e)
        sys.exit(2)
