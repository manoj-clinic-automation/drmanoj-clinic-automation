#!/usr/bin/env python3
"""synth_s879.py <new finance dir> <old (live) finance dir> <a COPY of finance.db>
Kit S879's proof. Both dirs hold darpan_kal.py, darpan_kal.html, purchase_app.py and hub_cash.py (the live one, read).
Run on the rebuilt files: green. Run with the live files as 'new' (the control): red.
Writes only to the copy it is given; prints counts and dates, never a name or a number from a bill."""
import datetime as dt
import importlib.util
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import types

NEW, OLD, DB = [os.path.abspath(x) for x in sys.argv[1:4]]
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != HERE]   # never the kit's own copy (F-1441)
OK, BAD = [], []


def check(name, cond, why=""):
    (OK if cond else BAD).append(name)
    print(("  ok   " if cond else "  FAIL ") + name + ("" if cond else "  -- " + str(why)))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


TMP = tempfile.mkdtemp(prefix="s879_")
try:
    shutil.copy(os.path.join(OLD, "hub_cash.py"), TMP)       # the one store's reader, as live
    sys.path.insert(0, TMP)
    dk_new = load(os.path.join(NEW, "darpan_kal.py"), "dk_new")
    dk_old = load(os.path.join(OLD, "darpan_kal.py"), "dk_old")
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    for m in (dk_new, dk_old):
        m._unit = "medical"
    import hub_cash
    hub_cash.ensure_schema(con)
    # ---- 1. every applied day of the last 90: the new expected = the old expected less that day's live owner entries
    days = [r[0] for r in con.execute("SELECT business_date FROM day_entry WHERE unit='medical' AND business_date >= ? "
                                      "ORDER BY business_date", ((dt.date.today() - dt.timedelta(days=90)).isoformat(),))]
    ents = hub_cash.entries(con, "medical")
    bad, with_e = [], 0
    for d in days:
        a, b = dk_old.compute_day(con, d), dk_new.compute_day(con, d)
        if a["expected_p"] is None:
            continue
        es = ents.get(d, [])
        e = sum(x["amount_p"] for x in es if x["kind"] != "other_account") + \
            (0 if b.get("online_source") == "marg" else sum(x["amount_p"] for x in es if x["kind"] == "other_account"))
        with_e += 1 if e else 0
        if b.get("expected_p") != a["expected_p"] - e or b.get("owner_p") != e:
            bad.append(d)
    check("T1 every day: expected = the old figure less the owner's entries (another account only once the bank or POS is in) (%d days, %d with entries)" % (len(days), with_e),
          not bad and len(days) > 0, bad[:5])
    # ---- 2. a made-up entry on a handed day re-decides it on the next view; removing it re-decides it back
    row = con.execute("SELECT business_date, handed_p, expected_p, diff_p FROM darpan_kal_day WHERE unit='medical' AND handed_p IS NOT NULL "
                      "AND state <> 'waiting_report' AND business_date NOT IN (SELECT business_date FROM owner_day_entry) "
                      "ORDER BY business_date DESC LIMIT 1").fetchone()
    if row is None:
        check("T2 a handed day to try on", False, "no handed day without entries in the copy")
    else:
        d = row["business_date"]
        base = dk_new.compute_day(con, d)["expected_p"]        # today's books, no entry on the day
        handed = int(row["handed_p"])
        amt = 123400
        con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) "
                    "VALUES ('medical', ?, 'taken_out', ?, 'dr_bhawna', 'personal', 'synth S879', 'synth', ?)", (d, amt, dt.datetime.now().isoformat()))
        con.commit()
        dk_new._refresh_if_needed(con, d)
        seen = con.execute("SELECT owner_p FROM darpan_kal_s879 WHERE unit='medical' AND business_date=?", (d,)).fetchone()
        n0 = con.total_changes
        dk_new._refresh_if_needed(con, d)
        check("T2b the decision remembers the entries' figure; a second view writes nothing", seen is not None and seen[0] == amt
              and con.total_changes == n0, (seen and seen[0], con.total_changes - n0))
        after = con.execute("SELECT expected_p, diff_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", (d,)).fetchone()
        check("T2 an entry lowers the stored expected and the difference moves by it on the next view",
              after["expected_p"] == base - amt and after["diff_p"] == handed - (base - amt), (base, after["expected_p"]))
        con.execute("UPDATE owner_day_entry SET removed_at=? WHERE note='synth S879'", (dt.datetime.now().isoformat(),))
        con.commit()
        dk_new._refresh_if_needed(con, d)
        back = con.execute("SELECT expected_p, diff_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", (d,)).fetchone()
        check("T3 the entry removed: the stored figure goes back", back["expected_p"] == base and back["diff_p"] == handed - base,
              (base, back["expected_p"]))
        dk_old._refresh_if_needed(con, d)
        con.execute("INSERT INTO owner_day_entry (unit, business_date, kind, amount_p, party, purpose, note, entered_by, entered_at) "
                    "VALUES ('medical', ?, 'taken_out', ?, 'dr_bhawna', 'personal', 'synth S879b', 'synth', ?)", (d, amt, dt.datetime.now().isoformat()))
        con.commit()
        dk_old._refresh_if_needed(con, d)
        old_after = con.execute("SELECT expected_p FROM darpan_kal_day WHERE unit='medical' AND business_date=?", (d,)).fetchone()
        check("T4 (control inside) the live file ignores the entry", old_after["expected_p"] == base, old_after["expected_p"])
        con.execute("DELETE FROM owner_day_entry WHERE note LIKE 'synth S879%'")
        con.commit()
    # ---- 3. no owner table at all: the old figure, no error
    c2 = sqlite3.connect(":memory:")
    c2.row_factory = sqlite3.Row
    check("T5 no owner table: nothing, no error", hasattr(dk_new, "_s879_owner") and dk_new._s879_owner(c2, "2026-11-14") == (0, 0, False))
    src = open(os.path.join(NEW, "darpan_kal.py"), encoding="utf-8").read()
    check("T5b the doctor's own card refreshes the days the entries touch", "OR business_date IN (SELECT business_date FROM owner_day_entry WHERE unit=?)" in src)
    # ---- 4. the pages: one row each, amount only on Darpan's card
    h = open(os.path.join(NEW, "darpan_kal.html"), encoding="utf-8").read()
    check("T6 Darpan's card: one row, amount only (no party, no purpose)",
          h.count("c.owner_p?") == 2 and "डॉक्टर साहब की entry (drawer से बाहर)" in h and "your day entries" in h)
    js = re.findall(r"<script[^>]*>(.*?)</script>", h, re.S)
    if shutil.which("node"):
        p = os.path.join(TMP, "p.js")
        open(p, "w", encoding="utf-8").write("\n".join(js))
        r = subprocess.run(["node", "--check", p], capture_output=True, text=True)
        check("T7 the page's script parses", r.returncode == 0, r.stderr[:200])
    else:
        print("  skip T7 (no node here -- proven in the kit's build)")
    # ---- 5. the tables fallback: a scan-tied line its bill does not carry is not counted in transit
    sys.path.insert(0, NEW)
    pa_new = load(os.path.join(NEW, "purchase_app.py"), "pa_new")
    pa_old = load(os.path.join(OLD, "purchase_app.py"), "pa_old")
    sys.path.pop(0)
    last = con.execute("SELECT MAX(received_at) FROM purchase_order WHERE status='received'").fetchone()[0]
    today = (dt.date.fromisoformat(str(last)[:10]) + dt.timedelta(days=1)) if last else dt.date.today()
    fake = types.ModuleType("stock_figure")
    real_sf = sys.modules.get("stock_figure")
    try:
        sys.modules["stock_figure"] = fake
        fake.s825_bill_judged = lambda c, ctx=None: {}
        a, b = pa_old._in_transit(con, today), pa_new._in_transit(con, today)
        check("T8 nothing judged: in transit exactly as before (%d items)" % len(a), a == b and len(a) > 0, (len(a), len(b)))
        since = (today - dt.timedelta(days=pa_new.IN_TRANSIT_DAYS)).isoformat()
        rows = con.execute("SELECT l.id, l.item, COALESCE(l.supplied, l.packs) got, l.pack_size FROM purchase_order_line l JOIN purchase_order o "
                           "ON o.id=l.order_id WHERE o.status='received' AND o.received_at >= ? AND COALESCE(l.supplied, l.packs) > 0", (since,)).fetchall()
        one = next((r for r in rows if pa_new.norm(r["item"]) in a), None)
        fake.s825_bill_judged = lambda c, ctx=None: {int(one["id"]): False} if one else {}
        b2 = pa_new._in_transit(con, today)
        k = pa_new.norm(one["item"]) if one else None
        want = (a[k]["units"] - int(one["got"]) * int(one["pack_size"] or 1)) if one else None
        got = (b2.get(k) or {}).get("units", 0) if one else None
        check("T9 a line its bill does not carry leaves the in-transit count", one is not None and got == want, (want, got))
        def boom(c, ctx=None):
            raise RuntimeError("x")
        fake.s825_bill_judged = boom
        check("T10 the judge failing: the old reading", pa_new._in_transit(con, today) == a)
    finally:
        if real_sf is not None:
            sys.modules["stock_figure"] = real_sf
        else:
            sys.modules.pop("stock_figure", None)
finally:
    shutil.rmtree(TMP, ignore_errors=True)
print("S879 synth: %d ok, %d failed" % (len(OK), len(BAD)))
sys.exit(1 if BAD else 0)
