#!/usr/bin/env python3
"""
selftest_returns_m7.py -- proves the SHIPPED BYTES, not a description of them.

The discipline this project paid for twice (S208, S209): a green selftest
proves the kit, not the join. So this one does not test hand-written code. It
copies the live files into a scratch directory, RUNS THE KIT'S OWN PATCHERS
over them, imports what comes out, and exercises that.

Run from inside the kit folder, on any machine that has the live sources:

  /root/wa/venv/bin/python3 -B selftest_returns_m7.py
  python -B selftest_returns_m7.py          (offline, with SRC= set)

SRC defaults to /root/finance.
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

KIT = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get("SRC", "/root/finance")
PY = sys.executable

_ok = [0]
_bad = []


def check(label, cond, extra=""):
    if cond:
        _ok[0] += 1
        print("  ok   %s" % label)
    else:
        _bad.append(label)
        print("  FAIL %s %s" % (label, extra))


# --------------------------------------------------------------------- setup
work = tempfile.mkdtemp(prefix="s219m7_")
need = ["finance_returns_audit.py", "finance_money.py", "darpan_app.py"]
for n in need:
    p = os.path.join(SRC, n)
    if not os.path.exists(p):
        raise SystemExit("missing source: %s (set SRC=)" % p)
    shutil.copyfile(p, os.path.join(work, n))
hub_src = os.path.join(SRC, "finance_ui", "finance_approvals.html")
if not os.path.exists(hub_src):
    hub_src = os.path.join(SRC, "finance_approvals.html")
have_hub = os.path.exists(hub_src)
if have_hub:
    shutil.copyfile(hub_src, os.path.join(work, "finance_approvals.html"))
shutil.copyfile(os.path.join(KIT, "finance_returns_escalate.py"),
                os.path.join(work, "finance_returns_escalate.py"))


def run_patch(script, envvar, target):
    env = dict(os.environ, **{envvar: os.path.join(work, target)})
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run([PY, "-B", os.path.join(KIT, script)],
                          capture_output=True, text=True, env=env)


print("\n1 -- THE PATCHERS APPLY TO THE LIVE BYTES, EXACTLY ONCE")
r1 = run_patch("patch_returns_stubguard_s219.py", "FRA_PATH", "finance_returns_audit.py")
check("stub-guard patcher applies cleanly", r1.returncode == 0, r1.stdout + r1.stderr)
r1b = run_patch("patch_returns_stubguard_s219.py", "FRA_PATH", "finance_returns_audit.py")
check("stub-guard patcher is IDEMPOTENT (says so and stops)",
      r1b.returncode == 0 and "already patched" in r1b.stdout, r1b.stdout)

r2 = run_patch("patch_darpan_m7_s219.py", "DARPAN_PATH", "darpan_app.py")
check("darpan patcher applies cleanly", r2.returncode == 0, r2.stdout + r2.stderr)
r2b = run_patch("patch_darpan_m7_s219.py", "DARPAN_PATH", "darpan_app.py")
check("darpan patcher is IDEMPOTENT", "already patched" in r2b.stdout, r2b.stdout)
_dtxt = open(os.path.join(work, "darpan_app.py"), encoding="utf-8").read()
check("darpan reads the cutover from a SETTING, not a constant",
      '_setting(con, "returns.act_from", "")' in _dtxt)
check("history raises no task on Darpan's desk",
      "needs = (r[\"verdict\"] != \"ok\") and not _hist" in _dtxt)
check("history is not counted as flagged either", "if not _hist and r[" in _dtxt)

if have_hub:
    r3 = run_patch("patch_hub_m7_s219.py", "HUB_PATH", "finance_approvals.html")
    check("hub patcher applies cleanly", r3.returncode == 0, r3.stdout + r3.stderr)
    hub = open(os.path.join(work, "finance_approvals.html"), encoding="utf-8").read()
    check('hub renders "identity needed" AMBER, not red',
          'n.verdict==="identity needed"' in hub and
          hub.index('n.verdict==="identity needed"') <
          hub.index("b-bad'+esc(n.verdict)" if "b-bad'+esc(n.verdict)" in hub
                    else '<span class="badge b-bad">\'+esc(n.verdict)'))
    check("hub shows the full mobile when the row carries one",
          "(n.mobile?' \xc2\xb7 '+esc(n.mobile)".replace("\xc2\xb7", "·") in hub
          or "n.mobile?" in hub)
else:
    print("  --   hub template not present at SRC; its two checks are SKIPPED")

# the app patcher is checked for anchor uniqueness only if the file is here
app_src = os.path.join(SRC, "finance_app.py")
if os.path.exists(app_src):
    shutil.copyfile(app_src, os.path.join(work, "finance_app.py"))
    r4 = run_patch("patch_finance_app_escalate_s219.py", "FA_PATH", "finance_app.py")
    check("finance_app escalation patcher applies cleanly", r4.returncode == 0,
          r4.stdout + r4.stderr)
    r4b = run_patch("patch_finance_app_escalate_s219.py", "FA_PATH", "finance_app.py")
    check("finance_app escalation patcher is IDEMPOTENT", "already patched" in r4b.stdout)
    txt = open(os.path.join(work, "finance_app.py"), encoding="utf-8").read()
    check("the escalation call sits INSIDE the wrapped after-apply",
          "_fre.escalate_day(con, iso, UNIT)" in txt)
    check("the watchdog sweep is hooked into api_shout",
          "_fre.escalate_recent(con, UNIT)" in txt)
else:
    print("  --   finance_app.py not present at SRC; its four checks are SKIPPED")

sys.path.insert(0, work)
import finance_returns_audit as FRA                                # noqa: E402
import finance_returns_escalate as FRE                             # noqa: E402


# ------------------------------------------------------------------ fixtures
SCHEMA = """
CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE,
                          name TEXT, phone_last4 TEXT %s);
CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT);
CREATE TABLE sale_item (id INTEGER PRIMARY KEY, day_entry_id INTEGER,
                        source_ref TEXT, amount_p INTEGER, patient_ref_id INTEGER,
                        service TEXT);
CREATE TABLE sale_line_item (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT,
                             bill_no TEXT, seq INTEGER, item_name TEXT, item_key TEXT,
                             pack TEXT, qty_raw TEXT, amount_p INTEGER, batch TEXT,
                             expiry_ym TEXT, is_return INTEGER DEFAULT 0);
CREATE TABLE recon_exception (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT,
                              kind TEXT, expected_p INTEGER, actual_p INTEGER,
                              diff_p INTEGER, severity TEXT, status TEXT, detail TEXT,
                              resolution TEXT, opened_at TEXT, closed_by TEXT,
                              closed_at TEXT, shout_count INTEGER DEFAULT 0,
                              last_shout_at TEXT,
                              UNIQUE (unit, business_date, kind));
CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
"""
D = "2026-08-27"
PRIOR = "2026-08-20"


def build(with_mobile=False):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA % (", mobile TEXT" if with_mobile else ""))
    # id 1 is the reserved pool, exactly as the live table has it
    con.execute("INSERT INTO patient_ref (id, clinic_id, name, phone_last4) "
                "VALUES (1,'WALK-IN','Walk-in / no clinic ID','')")
    con.execute("INSERT INTO patient_ref (id, clinic_id, name, phone_last4) "
                "VALUES (2,'7956','A REAL PATIENT','')")
    if with_mobile:
        con.execute("UPDATE patient_ref SET mobile='MOBILE-A' WHERE id=2")
    # the escalation sections test the MECHANISM, so the cutover is opened
    # back for them; section 9 tests the cutover itself.
    con.execute("INSERT INTO setting (key, value) VALUES ('returns.act_from','2026-01-01')")
    con.execute("INSERT INTO day_entry (id, unit, business_date) VALUES (9,'medical',?)", (D,))
    con.execute("INSERT INTO day_entry (id, unit, business_date) VALUES (8,'medical',?)", (PRIOR,))

    def sale(bill, pid, day, deid, amt, service="medicine"):
        con.execute("INSERT INTO sale_item (day_entry_id, source_ref, amount_p, "
                    "patient_ref_id, service) VALUES (?,?,?,?,?)",
                    (deid, bill, amt, pid, service))

    def line(bill, day, item, qty, rate, ret=0, seq=1, pack="1*10"):
        con.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, seq, "
                    "item_name, item_key, pack, qty_raw, amount_p, batch, expiry_ym, "
                    "is_return) VALUES ('medical',?,?,?,?,?,?,?,?,'B1','2027-01',?)",
                    (day, bill, seq, item, item.upper(), pack, qty, rate, ret))

    # (a) THE OWNER'S CASE: a return on the WALK-IN pool, item never in that pool
    sale("CN-STUB", 1, D, 9, -108000, "medicine_return")
    line("CN-STUB", D, "ITEM ALPHA", "1:0", 108000, ret=1)
    # (b) a return on a REAL patient who never bought the item -> stays an alarm
    sale("CN-REAL", 2, D, 9, -50000, "medicine_return")
    line("CN-REAL", D, "ITEM BETA", "1:0", 50000, ret=1)
    # (c) a return on a REAL patient who DID buy it, same qty, same rate -> ok
    sale("B-OLD", 2, PRIOR, 8, 30000)
    line("B-OLD", PRIOR, "ITEM GAMMA", "1:0", 30000, ret=0)
    sale("CN-OK", 2, D, 9, -30000, "medicine_return")
    line("CN-OK", D, "ITEM GAMMA", "1:0", 30000, ret=1)
    # (d) an ORPHAN: lines, no bill row
    line("CN-ORPH", D, "ITEM DELTA", "1:0", 20000, ret=1)
    con.commit()
    return con


def by_bill(rows):
    return {r["bill"]: r for r in rows}


print("\n2 -- THE OWNER'S CASE: A STUB POOL NO LONGER ACCUSES ANYBODY")
con = build()
rows, summ = FRA.returns_for_day(con, D)
R = by_bill(rows)
check("all four returns are still present -- nothing hidden", len(rows) == 4, sorted(R))
check('the WALK-IN return says "identity needed"',
      R["CN-STUB"]["verdict"] == "identity needed", R["CN-STUB"]["verdict"])
check("it is NOT accused of NEVER BOUGHT",
      R["CN-STUB"]["verdict"] != "NEVER BOUGHT")
check("its note explains the pooling in the owner's words",
      "placeholder" in R["CN-STUB"]["note"] and "everybody" in R["CN-STUB"]["note"])
check("its MONEY is still counted in full",
      R["CN-STUB"]["amount_p"] == 108000, R["CN-STUB"]["amount_p"])
check("the day's value still includes it",
      summ["value_p"] == 108000 + 50000 + 30000 + 20000, summ["value_p"])
check('a REAL patient who never bought it is STILL "NEVER BOUGHT"',
      R["CN-REAL"]["verdict"] == "NEVER BOUGHT", R["CN-REAL"]["verdict"])
check("a real patient who did buy it is still ok",
      R["CN-OK"]["verdict"] == "ok", R["CN-OK"]["verdict"])
check('an orphan is still "no patient attributed"',
      R["CN-ORPH"]["verdict"] == "no patient attributed", R["CN-ORPH"]["verdict"])
check("flagged counts ONE -- the real one only", summ["flagged"] == 1, summ["flagged"])
check('"identity needed" is not in the flagged tally',
      summ["tally"].get("identity needed") == 1 and summ["flagged"] == 1)

print("\n3 -- THE GUARD IS A LOOKUP, NOT A GUESS")
check("a real patient is not treated as a stub",
      FRA._stub_identity(con, 2) is None)
check("the reserved WALK-IN row IS", FRA._stub_identity(con, 1) is not None)
check("no patient at all is not a stub either", FRA._stub_identity(con, None) is None)
check("an unknown id is not a stub", FRA._stub_identity(con, 4242) is None)
con2 = sqlite3.connect(":memory:"); con2.row_factory = sqlite3.Row
check("a database with no patient_ref at all fails SOFT, never raises",
      FRA._stub_identity(con2, 1) is None)

print("\n4 -- A DISCOUNT ON A REFUND STILL SPEAKS, EVEN ON A STUB")
con = build()
# the goods are worth 1080.00 but only 900.00 left the drawer
con.execute("UPDATE sale_item SET amount_p=-90000 WHERE source_ref='CN-STUB'")
con.commit()
R = by_bill(FRA.returns_for_day(con, D)[0])
check("gross and net are both kept, not netted away",
      R["CN-STUB"]["gross_p"] == 108000 and R["CN-STUB"]["net_p"] == 90000,
      (R["CN-STUB"]["gross_p"], R["CN-STUB"]["net_p"]))
check('a material shortfall on a stub row still reads "DISCOUNTED RETURN"',
      R["CN-STUB"]["verdict"] == "DISCOUNTED RETURN", R["CN-STUB"]["verdict"])

print("\n5 -- D356: THE FULL MOBILE WHEN THE BOX HAS THE COLUMN, NEVER A GUESS")
con = build(with_mobile=False)
R = by_bill(FRA.returns_for_day(con, D)[0])
check("no mobile column -> the field is empty, not a crash",
      R["CN-REAL"]["mobile"] == "", repr(R["CN-REAL"]["mobile"]))
check("the last-four field still works as it always did",
      "mobile_last4" in R["CN-REAL"])
con = build(with_mobile=True)
R = by_bill(FRA.returns_for_day(con, D)[0])
check("mobile column present -> the full number comes through",
      R["CN-REAL"]["mobile"] == "MOBILE-A", repr(R["CN-REAL"]["mobile"]))
check("_has_col answers honestly both ways",
      FRA._has_col(con, "patient_ref", "mobile") is True and
      FRA._has_col(con, "patient_ref", "no_such_col") is False)

print("\n6 -- ESCALATION: THE OWNER HEARS, AND IS NOT SHOUTED AT")
con = build()
act = FRE.escalate_day(con, D)
row = con.execute("SELECT * FROM recon_exception WHERE kind='return_flagged'").fetchone()
check("a real flag opens exactly one exception", act == "opened" and row is not None, act)
check("it is one row per day, by construction",
      con.execute("SELECT COUNT(*) c FROM recon_exception").fetchone()["c"] == 1)
check("severity high for a NEVER BOUGHT", row["severity"] == "high", row["severity"])
check("the detail names the bill", "CN-REAL" in row["detail"], row["detail"])
check("the detail carries NO name, NO clinic ID, NO number (F-185)",
      "REAL PATIENT" not in row["detail"] and "7956" not in row["detail"],
      row["detail"])
check("the STUB return is NOT escalated to the owner",
      "CN-STUB" not in row["detail"], row["detail"])
check("running it again does not open a second row",
      FRE.escalate_day(con, D) == "updated" and
      con.execute("SELECT COUNT(*) c FROM recon_exception").fetchone()["c"] == 1)

con.execute("UPDATE recon_exception SET status='resolved', resolution='I know this one' "
            "WHERE kind='return_flagged'")
con.commit()
check("a decision the owner made is NOT undone by the next sweep",
      FRE.escalate_day(con, D) == "left-resolved")
# a genuinely new flag on the same day
con.execute("INSERT INTO sale_item (day_entry_id, source_ref, amount_p, patient_ref_id, "
            "service) VALUES (9,'CN-NEW',-70000,2,'medicine_return')")
con.execute("INSERT INTO sale_line_item (unit, business_date, bill_no, seq, item_name, "
            "item_key, pack, qty_raw, amount_p, batch, expiry_ym, is_return) "
            "VALUES ('medical',?,'CN-NEW',1,'ITEM EPS','ITEM EPS','1*10','1:0',70000,"
            "'B1','2027-01',1)", (D,))
con.commit()
check("but a NEW flag on that day RE-OPENS it -- the second failure is not silent",
      FRE.escalate_day(con, D) == "re-opened")

print("\n7 -- NOTHING TO SAY, NOTHING SAID")
con = build()
con.execute("DELETE FROM sale_item WHERE source_ref='CN-REAL'")
con.execute("DELETE FROM sale_line_item WHERE bill_no='CN-REAL'")
con.commit()
rows, summ = FRA.returns_for_day(con, D)
check("a day of stubs and orphans alone has ZERO flags", summ["flagged"] == 0,
      summ["tally"])
check("and escalates nothing at all", FRE.escalate_day(con, D) == "none" and
      con.execute("SELECT COUNT(*) c FROM recon_exception").fetchone()["c"] == 0)
con = build()
FRE.escalate_day(con, D)
con.execute("DELETE FROM sale_item WHERE source_ref='CN-REAL'")
con.execute("DELETE FROM sale_line_item WHERE bill_no='CN-REAL'")
con.commit()
check("an alarm whose condition has GONE is closed, not left standing",
      FRE.escalate_day(con, D) == "cleared")

print("\n8b -- THE PAST IS ACCEPTED (the owner's ruling, 02-Sep-2026)")
con = build()
con.execute("UPDATE setting SET value='2026-09-02' WHERE key='returns.act_from'")
con.commit()
check("a day BEFORE the cutover escalates nothing at all",
      FRE.escalate_day(con, D) == "historical" and
      con.execute("SELECT COUNT(*) c FROM recon_exception").fetchone()["c"] == 0)
rows, summ = FRA.returns_for_day(con, D)
check("...but its rows are all still there, verdicts and money intact",
      len(rows) == 4 and summ["value_p"] == 208000, (len(rows), summ["value_p"]))
check("...so the history is still the baseline, not deleted",
      any(r["verdict"] == "NEVER BOUGHT" for r in rows))
con.execute("UPDATE setting SET value=? WHERE key='returns.act_from'", (D,))
con.commit()
check("the cutover is a SETTING -- move it and the same day escalates",
      FRE.escalate_day(con, D) == "opened")
check("the default holds when the setting is empty",
      FRE.act_from(sqlite3.connect(":memory:")) == "2026-09-02")

print("\n8 -- THE SWEEP IS BOUNDED AND CHEAP")
con = build()
out = FRE.escalate_recent(con, "medical", days=3650)
check("the sweep reaches the day and opens it", out.get("opened") == 1, out)
check("it visits only days that HAVE returns", sum(out.values()) == 1, out)

shutil.rmtree(work, ignore_errors=True)
print("\n%s  %d checks passed, %d failed" %
      ("SELFTEST GREEN" if not _bad else "SELFTEST RED", _ok[0], len(_bad)))
for b in _bad:
    print("   FAILED: %s" % b)
sys.exit(1 if _bad else 0)
