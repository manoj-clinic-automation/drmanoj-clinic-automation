#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s474.py -- S474_FINANCE_TIDY (session 293, 04-Oct-2026). Hermetic (F-709), on the S469 walk's harness: the app's CODE
is copied to a scratch folder twice ('old' as it is, 'new' with the kit's edits), each with an EMPTY database made from the
app's own schema, made-up logins, made-up days. Nothing live is opened. Each change is SHOWN on the old file first.

  1. the clinic tile: a non-checker (reception) is answered with the deposit banner and NOTHING is written -- on the old file
     the same call adds 'missing_day' rows to recon_exception; the checker's answer is the same on old and new.
  2. F-716: a day ingested, then a second export for the same day run with commit=False and rolled back -- the first day's
     bills are still the books (old file: the second export replaced them in spite of the rollback). The same for the drug
     lines (load_lines commit=False + rollback leaves none). Every other caller (commit left at its default) still commits.
  3. a file the reader refused is REFUSED again when the same bytes come back (old file: ALREADY-RECEIVED for ever).
  4. selftest teardown puts the ledger env back (read off the new file's text; pyflakes no longer names _f6_ledger_prev).
  5. CLINIC_TENDERS is gone and nothing names it.
Last line: WALK_S474 GREEN|RED.
   usage: walk_s474.py --apply apply_s474.py --finance /root/finance
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

MARK = "@@S474JSON@@ "
OK, FAIL = [], []
CD = "2026-09-11"


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:600]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


MARG = ("Bill No,Bill Date,Customer,Particulars,Net Amt\n"
        "H-9001,11/09/2026,4471 Ramesh Kumar,Tab Calcium,Rs 450.00\n"
        "H-9002,11/09/2026,Sunita Devi (5120),Knee cap,\"1,250.00\"\n")
MARG3 = MARG + "H-9003,11/09/2026,Walk in customer,Bandage,120\n"
ITEMS = [dict(bill_no="H-9001", bill_date="2026-09-11", seq="1", item_name="TAB CALCIUM 500", pack="10", qty_raw="1", amount="450.00", expiry_ym="2028-06", batch="B1"),
         dict(bill_no="H-9002", bill_date="2026-09-11", seq="1", item_name="KNEE CAP M", pack="1", qty_raw="1", amount="1250.00", expiry_ym="", batch="")]


def child():
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    import finance_ingest as fi
    import finance_returns as fr
    root = os.path.realpath(os.environ["S474_ROOT"]) + os.sep
    if not os.path.realpath(fa.DB_PATH).startswith(root):
        print(MARK + json.dumps({"abort": "the finance database is not the scratch one"}))
        return
    out = {}
    con = sqlite3.connect(fa.DB_PATH)
    con.row_factory = sqlite3.Row
    cu = fa.CLINIC_UNIT
    for unit, user, role in ((cu, "wreception", "maker"), (cu, "wdoctor", "checker"), ("medical", "wdoctor", "checker")):
        con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES (?,?,?,1)", (unit, user, role))
    # a clinic day FOUR days before today's walk date -> refresh_missing_days has days to insert
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at,approved_by,approved_at) "
                "VALUES (?,?,'approved','app','walk',?,'wdoctor',?)", (cu, CD, CD + "T09:00:00", CD + "T21:00:00"))
    con.commit()
    c = fa.app.test_client()

    def ask(path, user):
        r = c.get(path, headers={"X-Clinic-User": user} if user else {})
        return [r.status_code, r.get_json(silent=True)]

    n0 = con.execute("SELECT COUNT(*) FROM recon_exception WHERE unit=?", (cu,)).fetchone()[0]
    out["tile_maker"] = ask("/finance/clinic/api/tile", "wreception")
    n1 = con.execute("SELECT COUNT(*) FROM recon_exception WHERE unit=?", (cu,)).fetchone()[0]
    out["exc_before_after_maker"] = [n0, n1]
    out["tile_checker"] = ask("/finance/clinic/api/tile", "wdoctor")
    n2 = con.execute("SELECT COUNT(*) FROM recon_exception WHERE unit=?", (cu,)).fetchone()[0]
    out["exc_after_checker"] = n2

    # ---- F-716: the loaders under a rollback
    sid = con.execute("SELECT id FROM ingest_source WHERE unit='medical' AND adapter='marg_export'").fetchone()[0]
    con.execute("UPDATE ingest_source SET active=1, config_json=? WHERE id=?", (json.dumps({"delimiter": ",", "date_format": "%d/%m/%Y"}), sid))
    for f, col, req in (("bill_no", "Bill No", 1), ("bill_date", "Bill Date", 0), ("patient_name", "Customer", 1), ("amount", "Net Amt", 1), ("description", "Particulars", 0)):
        con.execute("INSERT OR REPLACE INTO ingest_column_map (source_id, our_field, their_column, transform, required) VALUES (?,?,?,?,?)",
                    (sid, f, col, "ddmmyyyy" if f == "bill_date" else None, req))
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) VALUES ('medical',?,'submitted','app','walk',?)", (CD, CD + "T20:00:00"))
    con.commit()
    eid = con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (CD,)).fetchone()[0]
    r1 = fi.ingest_day(con, "medical", CD, "marg_export", MARG, run_by="walk", source_ref="walk1.csv")          # the default: commits
    bills1 = con.execute("SELECT COUNT(*) FROM sale_item WHERE day_entry_id=?", (eid,)).fetchone()[0]
    try:
        r2 = fi.ingest_day(con, "medical", CD, "marg_export", MARG3, run_by="walk", source_ref="walk2.csv", commit=False)   # S474
        con.rollback()
        new_api = True
    except TypeError:                                            # the OLD module has no commit= -- do what the old caller did
        r2 = fi.ingest_day(con, "medical", CD, "marg_export", MARG3, run_by="walk", source_ref="walk2.csv")
        con.rollback()
        new_api = False
    bills2 = con.execute("SELECT COUNT(*) FROM sale_item WHERE day_entry_id=?", (eid,)).fetchone()[0]
    batches = [tuple(r) for r in con.execute("SELECT source_ref, status FROM ingest_batch WHERE unit='medical' AND day_entry_id=? ORDER BY id", (eid,))]
    out["f716"] = dict(new_api=new_api, read1=r1.get("rows_read"), read2=r2.get("rows_read"), bills_after_first=bills1, bills_after_rollback=bills2, batches=batches)
    # the drug lines
    bid = con.execute("SELECT id FROM ingest_batch WHERE day_entry_id=? ORDER BY id DESC LIMIT 1", (eid,)).fetchone()[0]
    try:
        n = fr.load_lines(con, "medical", CD, ITEMS, batch_id=bid, commit=False)
        con.rollback()
        lines_after_rollback = con.execute("SELECT COUNT(*) FROM sale_line_item WHERE day_entry_id=?", (eid,)).fetchone()[0]
        n_default = fr.load_lines(con, "medical", CD, ITEMS, batch_id=bid)
        con.rollback()
        lines_after_default = con.execute("SELECT COUNT(*) FROM sale_line_item WHERE day_entry_id=?", (eid,)).fetchone()[0]
        out["lines"] = dict(new_api=True, stored=n, after_rollback=lines_after_rollback, stored_default=n_default, after_default_rollback=lines_after_default)
    except TypeError:
        n = fr.load_lines(con, "medical", CD, ITEMS, batch_id=bid)
        con.rollback()
        out["lines"] = dict(new_api=False, stored=n, after_rollback=con.execute("SELECT COUNT(*) FROM sale_line_item WHERE day_entry_id=?", (eid,)).fetchone()[0])

    # ---- the rejected file sent twice (the reader refuses a file that is not a Marg report)
    tok = os.environ.get("FINANCE_MARG_TOKEN", "")
    import io
    def push():
        r = c.post("/finance/api/marg-push", headers={"X-Finance-Marg": tok}, data={"file": (io.BytesIO(b"not a marg report at all " * 20), "junk.xls")},
                   content_type="multipart/form-data")
        j = r.get_json(silent=True) or {}
        return [r.status_code, j.get("verdict")]
    p1 = push()
    p2 = push()
    out["push"] = [p1, p2, con.execute("SELECT COUNT(*) FROM marg_push_staging WHERE status='rejected'").fetchone()[0]]
    con.close()
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html", "*.json"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))


def run(root, tag, appdir):
    base = os.path.join(root, "run_" + tag)
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    con = sqlite3.connect(os.path.join(base, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql", "finance_returns.sql"):
        p = os.path.join(appdir, f)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as fh:
                con.executescript(fh.read())
    con.execute("CREATE TABLE IF NOT EXISTS clinic_line_side (id INTEGER PRIMARY KEY, day_entry_id INTEGER, tender TEXT, amount_p INTEGER, line_kind TEXT, note TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS clinic_verification (id INTEGER PRIMARY KEY, day_entry_id INTEGER, verified_by TEXT, verified_at TEXT, note TEXT)")
    # the two S193 columns that live on the box only (absent from finance_schema.sql; the ingest writes them)
    for col in ("gross_p INTEGER", "disc_p INTEGER"):
        try:
            con.execute("ALTER TABLE sale_item ADD COLUMN " + col)
        except sqlite3.OperationalError:
            pass
    con.commit()
    con.close()
    e = dict(os.environ)
    # every token below is made up afresh at each run -- never the box's; no value is written in this file
    e.update({"S474_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(base, "scans"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "FINANCE_MARG_TOKEN": "walkmarg-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "ASSETS_DB": os.path.join(base, "no_assets.db"), "FINANCE_UPI_DIR": os.path.join(base, "upi"),
              "FINANCE_YESBANK_DIR": os.path.join(base, "yes"), "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"),
              "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e, capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    if "--child" in sys.argv:
        child()
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s474_walk_")
    try:
        old = os.path.join(root, "old"); new = os.path.join(root, "new")
        make_app(a.finance, old); make_app(a.finance, new)
        r = subprocess.run([sys.executable, "-B", a.apply] + [os.path.join(new, f) for f in ("finance_app.py", "finance_ingest.py", "finance_returns.py", "marg_backfill.py")],
                           capture_output=True, text=True)
        check("apply on scratch", r.returncode == 0, r.stderr[-300:])
        src = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
        check("4 teardown puts LEDGER_DIR / FINANCE_LEDGER_JSONL / LEDGER_JSONL back", 'LEDGER_JSONL = _f6_ledger_prev[2]' in src and '("LEDGER_DIR", _f6_ledger_prev[0])' in src)
        check("5 CLINIC_TENDERS is gone and nothing names it", "CLINIC_TENDERS " not in src and "CLINIC_TENDERS=" not in src and "CLINIC_TENDERS_ALL" in src)
        i_tile = src.index('def clinic_api_tile():')
        body = src[i_tile:i_tile + 4000]
        check("1 the non-checker return precedes refresh_missing_days in the tile", body.index("return jsonify(**_out469)") < body.index("refresh_missing_days(con, CLINIC_UNIT)"))
        pO, gO = run(root, "old", old)
        pN, gN = run(root, "new", new)
        check("old app ran", gO is not None and "abort" not in gO, (pO.stderr or pO.stdout)[-500:])
        check("new app ran", gN is not None and "abort" not in gN, (pN.stderr or pN.stdout)[-500:])
        if gO and gN and "abort" not in gO and "abort" not in gN:
            # 1 the tile
            check("1 SHOWN on the old file: the maker's call wrote missing_day rows", gO["exc_before_after_maker"][1] > gO["exc_before_after_maker"][0], str(gO["exc_before_after_maker"]))
            check("1 on the new file the maker's call writes nothing", gN["exc_before_after_maker"][1] == gN["exc_before_after_maker"][0], str(gN["exc_before_after_maker"]))
            check("1 the maker still gets the banner (ok, deposit_due, nothing else)", gN["tile_maker"][0] == 200 and set((gN["tile_maker"][1] or {}).keys()) <= {"ok", "unit_name", "deposit_due", "cash_in_hand", "deposit_threshold", "deposit_excess"}, str(gN["tile_maker"]))
            check("1 the maker's banner reads the same on old and new", gO["tile_maker"][1] == gN["tile_maker"][1], "%s vs %s" % (gO["tile_maker"][1], gN["tile_maker"][1]))
            check("1 the checker's answer is the same on old and new", gO["tile_checker"] == gN["tile_checker"], json.dumps([gO["tile_checker"][1], gN["tile_checker"][1]])[:400])
            check("1 the checker's call still refreshes the missing days", gN["exc_after_checker"] > gN["exc_before_after_maker"][1], str([gN["exc_before_after_maker"], gN["exc_after_checker"]]))
            # 2 F-716
            fo, fn = gO["f716"], gN["f716"]
            check("2 both exports read (2 then 3 bills)", fn["read1"] == 2 and fn["read2"] == 3, str(fn))
            check("2 SHOWN on the old file: after the rollback the second export is the books (its batch committed, the first superseded)",
                  (not fo["new_api"]) and [b[0] for b in fo["batches"]] == ["walk1.csv", "walk2.csv"] and fo["batches"][0][1] == "superseded", str(fo))
            check("2 on the new file the rollback is real: the first export is still the books (2 bills, its batch not superseded)",
                  fn["new_api"] and fn["bills_after_first"] == 2 and fn["bills_after_rollback"] == 2 and [tuple(b) for b in fn["batches"]] == [("walk1.csv", "ok")] or
                  (fn["new_api"] and fn["bills_after_rollback"] == 2 and [b[0] for b in fn["batches"]] == ["walk1.csv"] and fn["batches"][0][1] != "superseded"), str(fn))
            lo, ln = gO["lines"], gN["lines"]
            check("2 SHOWN on the old file: drug lines survive a rollback", (not lo["new_api"]) and lo["after_rollback"] == 2, str(lo))
            check("2 on the new file load_lines(commit=False) + rollback leaves none; the default still commits", ln["new_api"] and ln["stored"] == 2 and ln["after_rollback"] == 0 and ln["stored_default"] == 2 and ln["after_default_rollback"] == 2, str(ln))
            # 3 the rejected file
            check("3 SHOWN on the old file: the same refused bytes answer ALREADY-RECEIVED", gO["push"][0][1] == "REFUSED" and gO["push"][1][1] == "ALREADY-RECEIVED", str(gO["push"]))
            check("3 on the new file they are read again (REFUSED twice, one rejected row)", gN["push"][0][1] == "REFUSED" and gN["push"][1][1] == "REFUSED" and gN["push"][2] == 1, str(gN["push"]))
        check("hermetic: the box's finance_app.py untouched", md5(os.path.join(a.finance, "finance_app.py")) == md5(os.path.join(old, "finance_app.py")))
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("WALK_S474 %s %d ok, %d fail" % ("GREEN" if not FAIL else "RED", len(OK), len(FAIL)))
    sys.exit(0 if not FAIL else 1)


if __name__ == "__main__":
    main()
