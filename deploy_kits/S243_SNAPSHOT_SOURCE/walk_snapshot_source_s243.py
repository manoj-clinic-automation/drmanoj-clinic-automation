#!/usr/bin/env python3
"""walk_snapshot_source_s243.py -- LIVE-SHAPE WALK for kit S243_SNAPSHOT_SOURCE

Mounts stock_app on a real Flask app exactly as finance_app does
(stock_app.init(app, db, require, unit=..., marg_token=...)), builds a sqlite
database from the live stock_schema.sql plus the new stock_expected schema, and
drives the one door both senders use -- POST /finance/stock/api/snapshot with the
machine token -- with Marg's closing stock and our computed figure for the SAME
as_on. Then it looks at the tables, the way the count page and reconcile() do.

It runs the SAME shop twice: once on the UNPATCHED base (the 0b965da4 pin), once
on the patched file, and prints the difference. On the base the defect is shown,
not described: the later push becomes "Marg's figure", and an open difference
closes because OUR arithmetic agreed with the count. On the patched file
stock_snapshot holds only Marg, stock_expected holds ours, stock_feed holds both,
and every read-only endpoint (now / drift / readiness / open / healthz) answers 200
with the SAME JSON as before the patch.

Usage:  python3 walk_snapshot_source_s243.py [--base PATH] [--new PATH] [--schema-dir DIR]
        exit 0 = green; anything else = a FAIL line above it.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.dirname(HERE)
FIN = os.environ.get("FINANCE_DIR", "/root/finance")
FROM_PIN = "0b965da40816079a60c49a20946832b3"
TOKEN = "PUT-THE-TOKEN-HERE"       # a fixture; the walk only needs the header to match init()
FIXED_NOW = ["2026-09-10T22:31:00"]        # now_iso() is pinned so the two runs are byte-comparable

OK, BAD = [], []


def chk(name, cond, detail=""):
    (OK if cond else BAD).append(name + (("  -- " + str(detail)) if detail and not cond else ""))
    print(("  ok   " if cond else "  FAIL ") + name + (("   " + str(detail)) if detail and not cond else ""))


def md5f(p):
    return hashlib.md5(io.open(p, "rb").read()).hexdigest()


def find(name, extra=()):
    for c in list(extra) + [os.path.join(HERE, name), os.path.join(FIN, name)]:
        if c and os.path.exists(c):
            return c
    return None


def load(path, modname, schema):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[modname] = m
    spec.loader.exec_module(m)
    m.SCHEMA = schema
    m.now_iso = lambda: FIXED_NOW[0]
    return m


def build_db(path, schemas, extra_schema):
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path, check_same_thread=False)
    con.row_factory = sqlite3.Row                        # as finance_app.db() sets it
    # the tables finance_returns.sql leans on, in their live shape (the S226 walk's own list)
    con.executescript("""
      CREATE TABLE IF NOT EXISTS business_unit(code TEXT PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS ingest_batch(id INTEGER PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS day_entry(id INTEGER PRIMARY KEY);
      CREATE TABLE IF NOT EXISTS setting(key TEXT PRIMARY KEY, value TEXT, note TEXT);
      INSERT OR IGNORE INTO business_unit(code) VALUES ('medical');
      INSERT OR IGNORE INTO day_entry(id) VALUES (1);
    """)
    for s in schemas:
        con.executescript(io.open(s, encoding="utf-8").read())
    if extra_schema:
        con.executescript(io.open(extra_schema, encoding="utf-8").read())
    con.commit()
    return con


AS_ON = "09-09-2026"            # Marg's closing-stock export day (dd-mm-yyyy, as Marg writes it)
LATER = "10-09-2026"            # the computed feed's own day: as_on = the last SALE date, one day on
ITEMS = [("TYRO BR TAB", "1*10", 10), ("CHEAPO SALT TAB", "1*10", 10),
         ("KNEE BRACE UNISON", "1*1", 1), ("NOTCOMPUTED SYP", "1*1", 1)]
MARG = {"TYRO BR TAB": 700, "CHEAPO SALT TAB": 400, "KNEE BRACE UNISON": 5, "NOTCOMPUTED SYP": 8}
OURS = {"TYRO BR TAB": 1100, "CHEAPO SALT TAB": 370, "KNEE BRACE UNISON": 5, "ONLYOURS TAB": 250}
PACK = {n: (p, s) for n, p, s in ITEMS}
PACK["ONLYOURS TAB"] = ("1*10", 10)
SRC_MARG = "push_snapshot"                                   # push_snapshot.py L287, verbatim
SRC_OURS = "push_expected base=03-09-2026 pur_to=08-09-2026"  # push_expected.py L1278 shape


def body(as_on, source, figures):
    return {"as_on": as_on, "source": source,
            "items": [dict(item=n, qty=q, packing=PACK[n][0], pack_size=PACK[n][1], rate_p=900)
                      for n, q in figures.items()]}


def run(label, mod_path, modname, schemas, extra_schema, workdir):
    """One full shop on one stock_app. Returns the record dict."""
    print("\n---- %s: %s (%s)" % (label, mod_path, md5f(mod_path)[:8]))
    from flask import Flask
    dbp = os.path.join(workdir, "walk_%s.db" % modname)
    con = build_db(dbp, schemas, extra_schema)
    m = load(mod_path, modname, schemas[0])

    # the open difference reconcile() will look at: the count found 370 of CHEAPO
    # against a Marg figure of 400. Marg still says 400; OUR arithmetic says 370.
    con.execute("INSERT INTO stock_count (id, unit, marg_as_on, bill_no, bill_date, started_at, submitted_at, "
                "submitted_by, items_total, items_counted, status) VALUES (1,'medical',?,?,?,?,?,?,4,4,'submitted')",
                ("06-09-2026", "A003425", "2026-09-06", "2026-09-06T10:00:00", "2026-09-06T11:00:00", "walk"))
    con.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, pack_size, status) "
                "VALUES (1,'CHEAPO SALT TAB','06-09-2026',400,370,-30,10,'open')")
    con.commit()

    role = {"user": "walk", "roles": ["medical.checker"], "role": "checker"}

    def require(*roles):
        return dict(role), None

    app = Flask("walk_" + modname)
    m.init(app, lambda: con, require, unit="medical", marg_token=TOKEN)
    c = app.test_client()
    H = {"X-Finance-Marg": TOKEN}
    rec = dict(label=label, md5=md5f(mod_path))

    r1 = c.post("/finance/stock/api/snapshot", json=body(AS_ON, SRC_MARG, MARG), headers=H)
    chk("[%s] Marg's closing stock for %s lands through the machine token (200)" % (label, AS_ON), r1.status_code == 200, r1.status_code)
    rec["marg_reply"] = r1.get_json()
    FIXED_NOW[0] = "2026-09-10T22:40:00"                 # our computed push comes later that night
    r2 = c.post("/finance/stock/api/snapshot", json=body(AS_ON, SRC_OURS, OURS), headers=H)
    chk("[%s] our computed figure for the SAME %s lands (200)" % (label, AS_ON), r2.status_code == 200, r2.status_code)
    rec["ours_reply"] = r2.get_json()
    FIXED_NOW[0] = "2026-09-10T22:41:00"
    r3 = c.post("/finance/stock/api/snapshot", json=body(LATER, SRC_OURS, OURS), headers=H)
    chk("[%s] our computed figure for %s (a day Marg has not exported) lands (200)" % (label, LATER), r3.status_code == 200, r3.status_code)
    FIXED_NOW[0] = "2026-09-10T22:31:00"

    def snap(as_on):
        return {r["item"]: (int(r["qty"]), r["source"]) for r in
                con.execute("SELECT item, qty, source FROM stock_snapshot WHERE as_on=?", (as_on,))}

    def table(name):
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

    rec["snapshot"] = snap(AS_ON)
    rec["snapshot_later"] = snap(LATER)
    rec["snapshot_days"] = sorted(r[0] for r in con.execute("SELECT DISTINCT as_on FROM stock_snapshot"))
    rec["expected_table"] = table("stock_expected")
    rec["expected"] = ({r["item"]: (int(r["qty"]), r["source"]) for r in
                        con.execute("SELECT item, qty, source FROM stock_expected WHERE as_on=?", (AS_ON,))}
                       if rec["expected_table"] else None)
    rec["feed"] = {(r[0], r[1]): r[2] for r in con.execute(
        "SELECT as_on, source, COUNT(*) FROM stock_feed GROUP BY as_on, source")}
    rec["diff_status"] = con.execute("SELECT status, closed_as_on FROM stock_diff WHERE id=1").fetchone()[0]
    rec["newest"] = m._newest_snapshot(con)[0]
    _gn = m.stock_gate(con)
    rec["gate_newest"] = _gn["verdict"]
    rec["gate_newest_line"] = "%s on %s: %s" % (_gn["verdict"], _gn.get("as_on"), (_gn["reasons"] or _gn["notes"] or ["-"])[0][:80])
    rec["gate_marg_day"] = m.stock_gate(con, AS_ON)
    rec["three_way_src"] = m._snapshot_source(con, AS_ON)[0]
    rec["rate"] = {r[0]: int(r[1]) for r in con.execute("SELECT item, rate_p FROM stock_rate")}

    # the read-only endpoints, as the pages call them
    rec["api"] = {}
    for p in ("/finance/stock/api/healthz", "/finance/stock/api/now", "/finance/stock/api/drift",
              "/finance/stock/api/readiness", "/finance/stock/api/open"):
        r = c.get(p)
        chk("[%s] %s answers 200" % (label, p), r.status_code == 200, r.status_code)
        rec["api"][p] = r.get_json()
    con.close()
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=None, help="the UNPATCHED stock_app.py (0b965da4)")
    ap.add_argument("--new", default=os.path.join(HERE, "stock_app.py"))
    ap.add_argument("--schema-dir", default=None)
    a = ap.parse_args()

    base = a.base or find("stock_app.py", [os.path.join(UP, "S240_STOCK_GATE_R2", "stock_app.py")])
    if base and md5f(base) != FROM_PIN:
        alt = os.path.join(UP, "S240_STOCK_GATE_R2", "stock_app.py")
        base = alt if (os.path.exists(alt) and md5f(alt) == FROM_PIN) else None
    if not base:
        print("!! no unpatched base (0b965da4) found -- pass --base"); return 2
    if not os.path.exists(a.new):
        print("!! patched file not found: %s" % a.new); return 2
    sd = [a.schema_dir] if a.schema_dir else []
    schema = find("stock_schema.sql", [os.path.join(d, "stock_schema.sql") for d in sd] +
                  [os.path.join(UP, "S208_STOCK_LEDGER", "stock_schema.sql")])
    if not schema:
        print("!! stock_schema.sql not found -- pass --schema-dir"); return 2
    pur = find("purchase_schema.sql", [os.path.join(d, "purchase_schema.sql") for d in sd] +
               [os.path.join(UP, "S224_MARG_PURCHASES", "purchase_schema.sql")])
    ret = find("finance_returns.sql", [os.path.join(d, "finance_returns.sql") for d in sd] +
               [os.path.join(UP, "S204_VPS_LIVE", "root__finance__finance_returns.sql")])
    newsch = os.path.join(HERE, "stock_expected_schema.sql")
    print("== S243 SNAPSHOT SOURCE -- live-shape walk ==")
    print("base    %s  %s" % (md5f(base), base))
    print("patched %s  %s" % (md5f(a.new), a.new))
    print("schema  %s%s%s" % (schema, (" + " + pur) if pur else " (no purchase schema: readiness purchase block will say unknown)",
                              (" + " + ret) if ret else " (no sale_line_item: readiness sale block will say unknown)"))
    schemas = [schema] + ([pur] if pur else []) + ([ret] if ret else [])

    work = tempfile.mkdtemp(prefix="walk_s243_")
    try:
        B = run("BASE", base, "stock_app_base_s243", schemas, None, work)
        N = run("NEW", a.new, "stock_app_new_s243", schemas, newsch, work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    print("\n---- THE DEFECT, on the base (0b965da4)")
    chk("base: after both pushes stock_snapshot for %s holds OUR figure, called Marg (TYRO 1100, not 700)" % AS_ON,
        B["snapshot"].get("TYRO BR TAB", (None,))[0] == 1100, B["snapshot"].get("TYRO BR TAB"))
    chk("base: its source column says push_expected", str(B["snapshot"].get("TYRO BR TAB", ("", ""))[1]).startswith("push_expected"))
    chk("base: the open difference CLOSED because our arithmetic (370) agreed with the count -- Marg still says 400",
        B["diff_status"] == "reconciled", B["diff_status"])
    chk("base: the newest snapshot day is the computed feed's %s, a day Marg never exported" % LATER,
        B["newest"] == LATER, B["newest"])
    chk("base: the S228 provenance line already had to say not-Marg ('expected' or 'mixed') for %s" % AS_ON,
        B["three_way_src"] in ("expected", "mixed"), B["three_way_src"])

    print("\n---- THE FIX, on the patched file")
    chk("new: stock_snapshot for %s holds ONLY Marg's rows (%d items, all push_snapshot)" % (AS_ON, len(MARG)),
        set(N["snapshot"]) == set(MARG) and all(v[1] == SRC_MARG for v in N["snapshot"].values()), N["snapshot"])
    chk("new: Marg's figures are intact (TYRO 700, CHEAPO 400)",
        N["snapshot"]["TYRO BR TAB"][0] == 700 and N["snapshot"]["CHEAPO SALT TAB"][0] == 400)
    chk("new: stock_expected exists and holds the computed rows for %s (%d items, all push_expected)" % (AS_ON, len(OURS)),
        N["expected"] is not None and set(N["expected"]) == set(OURS) and all(v[1].startswith("push_expected") for v in N["expected"].values()), N["expected"])
    chk("new: the computed figures are intact there (TYRO 1100, ONLYOURS 250)",
        N["expected"] and N["expected"]["TYRO BR TAB"][0] == 1100 and N["expected"]["ONLYOURS TAB"][0] == 250)
    chk("new: the computed-only day %s wrote NOTHING to stock_snapshot" % LATER, N["snapshot_later"] == {}, N["snapshot_later"])
    chk("new: stock_snapshot days = [%s] only" % AS_ON, N["snapshot_days"] == [AS_ON], N["snapshot_days"])
    chk("new: stock_feed still holds BOTH pushes for %s (append-only, unchanged)" % AS_ON,
        N["feed"].get((AS_ON, SRC_MARG)) == len(MARG) and N["feed"].get((AS_ON, SRC_OURS)) == len(OURS), N["feed"])
    chk("new: stock_feed is identical to the base run", N["feed"] == B["feed"])
    chk("new: the open difference STAYS open -- Marg (400) still disagrees with the count (370)",
        N["diff_status"] == "open", N["diff_status"])
    chk("new: the newest snapshot day is Marg's %s -- the count page counts against Marg" % AS_ON, N["newest"] == AS_ON, N["newest"])
    chk("new: the count gate on the newest day no longer says 'no Marg STOCK CLOSING' (base verdict was %s)" % B["gate_newest"],
        not any("no Marg STOCK CLOSING" in x for x in N["gate_marg_day"]["reasons"]), N["gate_marg_day"]["reasons"])
    chk("new: the S228 provenance line now says 'marg' for %s" % AS_ON, N["three_way_src"] == "marg", N["three_way_src"])
    chk("new: the Marg push reply still carries items/reconciled (push_snapshot.py reads them) and says stored_in=stock_snapshot",
        N["marg_reply"].get("items") == len(MARG) and "reconciled" in N["marg_reply"] and N["marg_reply"].get("stored_in") == "stock_snapshot", N["marg_reply"])
    chk("new: the computed push reply says stored_in=stock_expected, reconciled=0",
        N["ours_reply"].get("stored_in") == "stock_expected" and N["ours_reply"].get("reconciled") == 0, N["ours_reply"])
    chk("new: stock_rate is written by both pushes as before (identical to the base run)", N["rate"] == B["rate"], (N["rate"], B["rate"]))

    print("\n---- THE READERS: same JSON before and after (they read stock_feed, not stock_snapshot)")
    for p in ("/finance/stock/api/now", "/finance/stock/api/drift", "/finance/stock/api/readiness"):
        jb, jn = B["api"][p], N["api"][p]
        # the readiness header carries the count gate, which reads stock_snapshot's newest day -- on the base that
        # day is the computed one (RED, 'no Marg STOCK CLOSING'); on the patch it is Marg's day. That change IS the fix.
        for j in (jb, jn):
            for k in ("as_of", "today"):
                j.pop(k, None)
            rd = j.get("readiness") if p != "/finance/stock/api/readiness" else j
            if isinstance(rd, dict):
                rd.pop("as_of", None); rd.pop("today", None)
                rd.pop("gate", None); rd["warnings"] = [w for w in rd.get("warnings", []) if not w.startswith("COUNT GATE")]
        same = json.dumps(jb, sort_keys=True) == json.dumps(jn, sort_keys=True)
        chk("%s: identical figures before and after the patch (gate block aside)" % p, same,
            "" if same else "\n      BASE " + json.dumps(jb, sort_keys=True)[:600] + "\n      NEW  " + json.dumps(jn, sort_keys=True)[:600])
    chk("/finance/stock/api/now shows ours vs Marg for %s from stock_feed on both" % LATER,
        N["api"]["/finance/stock/api/now"]["as_on"] == LATER and B["api"]["/finance/stock/api/now"]["as_on"] == LATER)
    print("      count gate on the NEWEST snapshot day, base: " + B["gate_newest_line"])
    print("      count gate on the NEWEST snapshot day, new : " + N["gate_newest_line"])
    gb = B["gate_marg_day"]
    gn = N["gate_marg_day"]
    print("      count gate for %s on the base: %s (%s)" % (AS_ON, gb.get("verdict"), (gb.get("reasons") or gb.get("notes") or ["-"])[0][:100]))
    print("      count gate for %s on the new : %s (%s)" % (AS_ON, gn.get("verdict"), (gn.get("reasons") or gn.get("notes") or ["-"])[0][:100]))
    ob, on = B["api"]["/finance/stock/api/open"], N["api"]["/finance/stock/api/open"]
    chk("/finance/stock/api/open: on the base the difference is gone (closed by our own arithmetic); on the new it is still open",
        ob.get("open") == 0 and on.get("open") == 1 and on["items"][0]["item"] == "CHEAPO SALT TAB", (ob.get("open"), on.get("open")))

    print("\nwalk: %d ok, %d FAIL" % (len(OK), len(BAD)))
    for b in BAD:
        print("  FAIL " + b)
    return 1 if BAD else 0


if __name__ == "__main__":
    sys.exit(main())
