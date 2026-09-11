#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sale_attribution.py -- S240, Sanjeevni RUNG 2: each bill's discount, attributed to its lines.

WHY
  Marg prints a sale bill's item lines at GROSS and the discount ONCE, for the whole bill (F-385).
  Rung 1 (sale_bill, S237/S240) now keeps that bill discount. T1 (marg_item_discount, S236) holds
  the owner's own ruling for 93 products. This puts the two together: which line the discount
  belongs to, so an orthotic's revenue can be read NET instead of GROSS.

THE RULES (each one a sentence, each one selftested)
  1. A line's gross is the spine's own money model (marg_spine.mrp_value_p): amount_p is the RATE
     PER PACK, the line is (strips + loose/pack) x rate. A bill whose lines do not add up to its
     printed GROSS (within Rs 1) is NOT attributed -- verdict 'lines_disagree' -- never guessed.
  2. The product comes from the spine's resolver (marg_spine.Spine.resolve). An ambiguous clip is
     used ONLY when every candidate carries the same ruling (e.g. four KNEE SUPPORT HINGED sizes,
     all 20%) -- basis 'family'. Otherwise the line is 'undecided', and says so.
  3. Expected discount of a line = gross x the ruled percent. The bill's ACTUAL discount is spread
     over the ruled-discount lines in proportion to that expectation, to the paisa (largest
     remainder) -- so a single ruled product on a bill takes the whole discount, exactly.
     Allowed when the actual is within Rs 20 or 50% of the expectation (Marg rounds the net to a
     round figure; measured round-offs are under Rs 20). Beyond that, each ruled line takes only its
     expectation and the rest stays on the bill as 'residual' -- never pushed onto an unruled line.
  4. A bill with a discount and NO ruled-discount line keeps the discount at bill level:
     'round_off' when it is under Rs 10, 'unattributed' otherwise (an undecided product was
     discounted). Coverage is data, not a silence.
  5. A credit note is attributed the same way with its sign.

WRITES (derived only -- rebuilt in full every run, same inputs same answer; nothing reads them yet)
  sale_line_discount   one row per sale line on an attributed day
  sale_bill_attrib     one row per bill: expected, attributed, residual, verdict, coverage
  sale_attrib_run      one row per run

    python3 sale_attribution.py --db /root/finance/finance.db --build [--if-changed]
    python3 sale_attribution.py --db ... --report
    python3 sale_attribution.py --selftest
"""
import argparse
import datetime as dt
import json
import os
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

TOL_ABS_P = 2000            # Rs 20
TOL_REL = 0.50
ROUND_OFF_P = 1000          # Rs 10
LINES_TOL_P = 100           # Rs 1: lines vs printed gross

SCHEMA = """
CREATE TABLE IF NOT EXISTS sale_line_discount (
    line_id        INTEGER PRIMARY KEY,         -- sale_line_item.id
    unit           TEXT NOT NULL,
    business_date  TEXT NOT NULL,
    bill_no        TEXT NOT NULL,
    item_id        INTEGER,
    resolved_how   TEXT NOT NULL,
    gross_p        INTEGER NOT NULL,
    disc_p         INTEGER NOT NULL,
    net_p          INTEGER NOT NULL,
    ruling_pct     REAL,
    basis          TEXT NOT NULL,               -- ruled | ruled_family | mrp | undecided | internal | not_attributed
    run_id         INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_sld_bill ON sale_line_discount(unit, business_date, bill_no);
CREATE INDEX IF NOT EXISTS ix_sld_item ON sale_line_discount(item_id);
CREATE TABLE IF NOT EXISTS sale_bill_attrib (
    unit           TEXT NOT NULL,
    business_date  TEXT NOT NULL,
    bill_no        TEXT NOT NULL,
    gross_p        INTEGER NOT NULL,
    disc_p         INTEGER NOT NULL,
    lines          INTEGER NOT NULL,
    lines_gross_p  INTEGER,
    expected_p     INTEGER NOT NULL,
    attributed_p   INTEGER NOT NULL,
    residual_p     INTEGER NOT NULL,
    ruled_lines    INTEGER NOT NULL,
    undecided_lines INTEGER NOT NULL,
    verdict        TEXT NOT NULL,   -- no_discount | exact | scaled | partial | round_off | unattributed | lines_disagree | no_lines
    run_id         INTEGER NOT NULL,
    PRIMARY KEY (unit, business_date, bill_no)
);
CREATE TABLE IF NOT EXISTS sale_attrib_run (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at   TEXT NOT NULL,
    finished_at  TEXT,
    fingerprint  TEXT,
    bills        INTEGER, lines INTEGER,
    disc_p       INTEGER, attributed_p INTEGER, residual_p INTEGER,
    notes        TEXT
);
"""


def now_ist():
    return (dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")


def _exists(con, t):
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (t,)).fetchone() is not None


# ------------------------------------------------------------------ pure half
def spread(total, weights):
    """Split `total` paise over `weights` in proportion, summing EXACTLY to total (largest remainder).
    Sign follows total. Weights must be >= 0 with a positive sum."""
    s = sum(weights)
    if s <= 0:
        raise ValueError("no weight to spread over")
    sign = -1 if total < 0 else 1
    t = abs(total)
    raw = [t * w / float(s) for w in weights]
    base = [int(x) for x in raw]
    left = t - sum(base)
    order = sorted(range(len(raw)), key=lambda i: (-(raw[i] - base[i]), i))
    for i in order[:left]:
        base[i] += 1
    return [sign * b for b in base]


def ruling_for(rulings, item_id, how, candidates):
    """(pct, basis). pct None = no usable ruling. Pure."""
    def one(i):
        r = rulings.get(i)
        if r is None:
            return None
        state, pct = r
        if state == "internal":
            return ("internal", None)
        if state == "mrp":
            return ("mrp", 0.0)
        return ("ruled", float(pct or 0.0))
    if item_id is not None:
        x = one(item_id)
        if x is None:
            return None, "undecided"
        return x[1], x[0] if x[0] != "ruled" or x[1] > 0 else "mrp"
    if how == "ambiguous" and candidates:
        xs = [one(i) for i in candidates]
        if all(x is not None for x in xs) and len(set(xs)) == 1:
            kind, pct = xs[0]
            if kind == "internal":
                return None, "internal"
            return pct, "ruled_family" if pct else "mrp"
    return None, "undecided"


def attribute_bill(bill, lines):
    """bill: dict gross_p, disc_p. lines: list of dict line_id, gross_p (None if unreadable), pct, basis.
    Returns (verdict, expected_p, per_line_disc list, residual_p). Pure."""
    gross, disc = bill["gross_p"], bill["disc_p"]
    sign = -1 if gross < 0 else 1
    if not lines:
        return "no_lines", 0, [], disc
    if any(l["gross_p"] is None for l in lines):
        return "lines_disagree", 0, [0] * len(lines), disc
    lg = sum(l["gross_p"] for l in lines)
    if abs(lg - abs(gross)) > LINES_TOL_P:
        return "lines_disagree", 0, [0] * len(lines), disc
    exp = [int(round(l["gross_p"] * l["pct"])) if (l["pct"] or 0) > 0 else 0 for l in lines]
    E = sum(exp)
    D = abs(disc)
    if D == 0:
        return "no_discount", sign * E, [0] * len(lines), 0
    if E == 0:
        return ("round_off" if D < ROUND_OFF_P else "unattributed"), 0, [0] * len(lines), disc
    if abs(D - E) <= max(TOL_ABS_P, TOL_REL * E):
        per = spread(D, exp)
        verdict = "exact" if abs(D - E) <= 100 else "scaled"
        return verdict, sign * E, [sign * p for p in per], 0
    if D > E:
        return "partial", sign * E, [sign * p for p in exp], sign * (D - E)
    # D far below E: the counter gave less than ruled -- spread what was given, flag it
    per = spread(D, exp)
    return "scaled", sign * E, [sign * p for p in per], 0


# ------------------------------------------------------------------ the build
def fingerprint(con):
    fp = {}
    for t in ("sale_bill", "sale_line_item", "marg_item_discount", "marg_item_name"):
        if _exists(con, t):
            fp[t] = list(con.execute("SELECT COUNT(*), MAX(rowid) FROM %s" % t).fetchone())
    if _exists(con, "sale_bill"):
        fp["sale_bill_w"] = con.execute("SELECT MAX(written_at) FROM sale_bill").fetchone()[0]
    return json.dumps(fp, sort_keys=True)


def build(con, out=print, if_changed=False):
    import marg_spine
    for t in ("sale_bill", "marg_item_discount", "sale_line_item", "marg_item_name"):
        if not _exists(con, t):
            raise SystemExit("REFUSING: table %s is missing (Rung 1 and T1 must be installed first)" % t)
    con.executescript(SCHEMA)
    fp = fingerprint(con)
    if if_changed:
        r = con.execute("SELECT fingerprint FROM sale_attrib_run WHERE finished_at IS NOT NULL "
                        "ORDER BY id DESC LIMIT 1").fetchone()
        if r and r[0] == fp:
            out("attribution: nothing changed since the last run -- skipped")
            return None
    cur = con.execute("INSERT INTO sale_attrib_run (started_at, fingerprint) VALUES (?,?)", (now_ist(), fp))
    run_id = cur.lastrowid
    sp = marg_spine.Spine(con)
    rulings = {r[0]: (r[1], r[2]) for r in con.execute("SELECT item_id, state, discount_pct FROM marg_item_discount")}
    cache = {}
    line_rows, bill_rows = [], []
    tot = {"bills": 0, "lines": 0, "disc": 0, "attr": 0, "resid": 0}
    for b in con.execute("SELECT unit, business_date, bill_no, gross_p, disc_p FROM sale_bill "
                         "ORDER BY business_date, bill_no").fetchall():
        unit, day, bno, gross, disc = b
        ls = con.execute("SELECT id, item_name, amount_p, qty_raw, pack FROM sale_line_item "
                         "WHERE unit=? AND business_date=? AND bill_no=? ORDER BY seq, id", (unit, day, bno)).fetchall()
        lines = []
        for lid, name, amt, qty, pack in ls:
            if name not in cache:
                cache[name] = sp.resolve(name)
            iid, how, cands = cache[name]
            g = marg_spine.mrp_value_p(amt, qty, pack) if marg_spine.packs_sold(qty, pack) is not None else None
            pct, basis = ruling_for(rulings, iid, how, cands)
            lines.append({"line_id": lid, "item_id": iid, "how": how, "gross_p": g, "pct": pct, "basis": basis})
        verdict, E, per, resid = attribute_bill({"gross_p": gross, "disc_p": disc}, lines)
        attributed = sum(per)
        for l, dp in zip(lines, per):
            g = l["gross_p"] or 0
            basis = l["basis"] if verdict not in ("lines_disagree", "no_lines") else "not_attributed"
            line_rows.append((l["line_id"], unit, day, bno, l["item_id"], l["how"], g, dp,
                              (g if gross >= 0 else -g) - dp,
                              l["pct"], basis, run_id))
        bill_rows.append((unit, day, bno, gross, disc, len(lines),
                          sum(l["gross_p"] or 0 for l in lines) if lines else None, E, attributed, resid,
                          sum(1 for l in lines if (l["pct"] or 0) > 0),
                          sum(1 for l in lines if l["basis"] == "undecided"), verdict, run_id))
        tot["bills"] += 1; tot["lines"] += len(lines); tot["disc"] += disc
        tot["attr"] += attributed; tot["resid"] += resid
    con.execute("DELETE FROM sale_line_discount")
    con.execute("DELETE FROM sale_bill_attrib")
    con.executemany("INSERT INTO sale_line_discount VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", line_rows)
    con.executemany("INSERT INTO sale_bill_attrib VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", bill_rows)
    con.execute("UPDATE sale_attrib_run SET finished_at=?, bills=?, lines=?, disc_p=?, attributed_p=?, "
                "residual_p=? WHERE id=?", (now_ist(), tot["bills"], tot["lines"], tot["disc"], tot["attr"],
                                             tot["resid"], run_id))
    con.commit()
    report(con, out)
    return tot


def rs(p):
    return "Rs %s%s" % ("-" if p < 0 else "", "{:,.2f}".format(abs(p) / 100.0))


def report(con, out=print):
    r = con.execute("SELECT id, finished_at, bills, lines, disc_p, attributed_p, residual_p FROM sale_attrib_run "
                    "WHERE finished_at IS NOT NULL ORDER BY id DESC LIMIT 1").fetchone()
    if not r:
        out("no attribution run yet"); return
    out("RUNG 2 -- the bill discount attributed to its lines   (run %d, %s IST)" % (r[0], r[1].replace("T", " ")[:16]))
    out("  bills %d · lines %d · bill discount %s · on a ruled line %s · left on the bill %s"
        % (r[2], r[3], rs(r[4]), rs(r[5]), rs(r[4] - r[5])))
    for v, n, d in con.execute("SELECT verdict, COUNT(*), SUM(disc_p) FROM sale_bill_attrib GROUP BY verdict "
                               "ORDER BY COUNT(*) DESC"):
        out("    %-15s %4d bills   discount %s" % (v, n, rs(d or 0)))
    cov = con.execute("SELECT SUM(basis IN ('ruled','ruled_family','mrp')), SUM(basis='undecided'), COUNT(*) "
                      "FROM sale_line_discount").fetchone()
    out("  lines with a ruling %d · undecided %d · of %d" % (cov[0] or 0, cov[1] or 0, cov[2] or 0))


# ------------------------------------------------------------------ selftest
def selftest():
    fails = []

    def ck(n, c):
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    ck("spread sums exactly", sum(spread(87000, [23000, 34500, 27800])) == 87000)
    ck("spread with a negative total", sum(spread(-17000, [1, 1, 1])) == -17000)
    L = lambda g, pct, basis="ruled": {"line_id": 1, "gross_p": g, "pct": pct, "basis": basis}
    v, E, per, res = attribute_bill({"gross_p": 234900, "disc_p": 74900}, [L(234900, 0.30)])
    ck("A003160 shape: one brace, the whole 749.00 on it", v == "scaled" and per == [74900] and res == 0)
    v, E, per, res = attribute_bill({"gross_p": 47000, "disc_p": 12000}, [L(47000, 0.25)])
    ck("A003278 shape: arm sling 120.00 on the line", per == [12000])
    v, E, per, res = attribute_bill({"gross_p": 106000, "disc_p": 0}, [L(106000, 0.0, "mrp")])
    ck("A003136 shape: at M.R.P., nothing", v == "no_discount" and per == [0])
    lines = [L(19351 // 8, None, "undecided"), L(61500, 0.25), L(7000, None, "undecided")]
    v, E, per, res = attribute_bill({"gross_p": sum(l["gross_p"] for l in lines), "disc_p": 15375}, lines)
    ck("A003333 shape: 153.75 all on the Leukocrepe, none on medicines", per == [0, 15375, 0] and v == "exact")
    four = [L(18000, None, "undecided"), L(45000, 0.20), L(115000, 0.20), L(139000, 0.30)]
    v, E, per, res = attribute_bill({"gross_p": 317000, "disc_p": 87000}, four)
    ck("A003495 shape: 870.00 spread over the three ruled lines, sum exact", sum(per) == 87000 and per[0] == 0 and res == 0)
    v, E, per, res = attribute_bill({"gross_p": 100000, "disc_p": 111}, [L(100000, None, "undecided")])
    ck("a Rs 1.11 round-off with nothing ruled stays on the bill", v == "round_off" and per == [0] and res == 111)
    v, E, per, res = attribute_bill({"gross_p": 100000, "disc_p": 30000}, [L(50000, 0.10), L(50000, None, "undecided")])
    ck("discount far above the ruling: ruled line takes its 50.00, rest stays on the bill", v == "partial" and per == [5000, 0] and res == 25000)
    v, E, per, res = attribute_bill({"gross_p": 55666, "disc_p": 0}, [L(52300, 0.0, "mrp")])
    ck("lines that do not add up to the printed gross are not attributed", v == "lines_disagree")
    v, E, per, res = attribute_bill({"gross_p": -115000, "disc_p": -17000}, [L(115000, 0.15)])
    ck("a credit note keeps its sign", per == [-17000])
    rul = {1: ("discount", 0.2), 2: ("discount", 0.2), 3: ("discount", 0.3), 4: ("mrp", 0.0), 5: ("internal", None)}
    ck("ambiguous clip, same ruling -> family", ruling_for(rul, None, "ambiguous", [1, 2]) == (0.2, "ruled_family"))
    ck("ambiguous clip, different rulings -> undecided", ruling_for(rul, None, "ambiguous", [1, 3]) == (None, "undecided"))
    ck("no ruling row -> undecided, never zero", ruling_for(rul, 9, "exact", None) == (None, "undecided"))
    ck("internal -> no selling price", ruling_for(rul, 5, "exact", None) == (None, "internal"))
    print("sale_attribution selftest: %d checks, %d failures" % (15, len(fails)))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--db")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--if-changed", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.db:
        ap.error("--db is required")
    con = sqlite3.connect(a.db, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    if a.build:
        build(con, if_changed=a.if_changed)
    elif a.report:
        report(con)
    return 0


if __name__ == "__main__":
    sys.exit(main())
