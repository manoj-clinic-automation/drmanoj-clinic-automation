#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s468.py -- S468_FINANCE_SMALLS: the self-test keeps its bank statements to itself; the housekeeping only tidies -- walked.

  usage: walk_s468.py --apply <apply_s468.py> --report <report_s468.py> --finance <folder holding finance_app.py and its siblings>

PART 1. The finance app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's three
insertions), each with an EMPTY database. In each, the REAL selftest() is started. On an empty database it stops early
(it needs real days) -- but AFTER the block at its top that sandboxes its stores, which is the block this kit edits.
Then the two uploads the self-test makes later are made through the real routes: a made-up Yes Bank statement and a
made-up UPI MPR. Where each raw file landed is the finding: on the old file, in the app folder's own upi_statements /
yesbank_statements (the stand-in for the live folders); on the new one, in throwaway folders that are gone at exit.
PART 2. report_s468.py on made-up data: a made-up ledger and finance book, and a made-up folder of scans.
Nothing live is opened. Last line: WALK_S468 GREEN|RED.
"""
import argparse
import ast
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "72d2538222a8fbd6a12d5ac2434c5a4e"
TO = "8f69f192020205b302ac413a039f7c31"
MARK = "@@S468JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:700]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def child():
    import datetime
    import io
    appdir = os.getcwd()
    sys.path.insert(0, appdir)
    import finance_app as fa
    root = os.path.realpath(os.environ["S468_ROOT"]) + os.sep
    if not os.path.realpath(fa.DB_PATH).startswith(root):
        print(MARK + json.dumps({"abort": "the finance database is not the scratch one"}))
        return
    live_upi, live_yes = os.path.join(appdir, "upi_statements"), os.path.join(appdir, "yesbank_statements")
    out = {"default_is_app_folder": [fa.UPI_DIR == live_upi, fa.YESBANK_DIR == live_yes]}
    how = "returned"
    saved_out = sys.stdout
    sys.stdout = io.StringIO()
    try:
        fa.selftest()
    except BaseException as ex:                                      # noqa: BLE001 -- an empty database stops it early
        how = type(ex).__name__
    finally:
        sys.stdout = saved_out
    out["selftest_stopped_with"] = how
    out["during"] = {"upi": fa.UPI_DIR, "yes": fa.YESBANK_DIR, "scan": fa.SCAN_DIR, "db": fa.DB_PATH}
    # the two uploads the self-test makes further down, through the real routes, as it makes them
    fa.ALLOW_HEADER_AUTH = True
    os.environ["FINANCE_DEV_USER"], os.environ["FINANCE_DEV_ROLE"] = "selftest", "checker"
    c = fa.app.test_client()
    up = {}
    if fa.finance_yesbank is not None:
        r = c.post("/finance/api/yesbank-statement", data={"file": (io.BytesIO(fa.finance_yesbank.SAMPLE.encode()), "yesbank.csv")},
                   content_type="multipart/form-data")
        up["yes"] = r.status_code
    try:
        tb = fa.finance_upi._build_test_xlsx([(datetime.date(2026, 8, 13).strftime("%d-%b-%y").upper(), 999.0, "RRN1")], 999.0)
        r = c.post("/finance/api/upi-statement", data={"file": (io.BytesIO(tb), "mpr.xlsx")}, content_type="multipart/form-data")
        up["upi"] = r.status_code
    except Exception as ex:                                          # noqa: BLE001
        up["upi"] = "not built: %s" % type(ex).__name__
    out["uploads"] = up
    ls = lambda d: sorted(os.listdir(d)) if os.path.isdir(d) else None
    out["landed"] = {"app_upi": ls(live_upi), "app_yes": ls(live_yes), "run_upi": ls(fa.UPI_DIR), "run_yes": ls(fa.YESBANK_DIR)}
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html"):
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
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    # the walk's stand-ins for the two Yes Bank tables (that migration is not a file beside the app); empty
    con.executescript("""
        CREATE TABLE IF NOT EXISTS bank_statement_line(id INTEGER PRIMARY KEY, account_ref TEXT, txn_date TEXT,
            value_date TEXT, description TEXT, reference TEXT, withdrawal_p INT DEFAULT 0,
            deposit_p INT DEFAULT 0, balance_p INT, is_cash_deposit INT DEFAULT 0,
            source_file TEXT, sha256 TEXT, ingested_at TEXT,
            UNIQUE(account_ref,txn_date,reference,deposit_p,withdrawal_p));
        CREATE TABLE IF NOT EXISTS bank_statement_period(id INTEGER PRIMARY KEY, account_ref TEXT,
            period_from TEXT, period_to TEXT, opening_p INT, closing_p INT, source_file TEXT,
            sha256 TEXT, ingested_at TEXT, UNIQUE(account_ref,period_from,period_to));
        """)
    con.commit()
    con.close()
    e = dict(os.environ)
    for k in ("FINANCE_UPI_DIR", "FINANCE_YESBANK_DIR", "FINANCE_SCAN_DIR"):
        e.pop(k, None)                                               # as on the box: the service sets neither statement folder
    # the cron token below is made up afresh at every run -- it is never the box's, and no value is written in this file
    e.update({"S468_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp,
              "FINANCE_ALLOW_HEADER_AUTH": "1", "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "",
              "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "ASSETS_DB": os.path.join(base, "no_assets.db"), "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"),
              "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got, tmp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s468_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S468 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    have = md5(os.path.join(old, "finance_app.py"))
    check("0.1 the unpatched finance_app.py is the file this kit was built from (72d25382, S467's)", have == FROM, have)
    if have != FROM:
        return
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.2 the three insertions apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, so.splitlines(), sn.splitlines(), autojunk=False).get_opcodes() if o[0] != "equal"]
    tree = ast.parse(sn)
    st = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "selftest"][0]
    inside = all(st.lineno <= o[3] + 1 and o[4] <= st.end_lineno for o in ops)
    check("0.4 three insertions, nothing removed or changed, and EVERY added line is inside selftest() -- no route, no page, no setting",
          len(ops) == 3 and all(o[0] == "insert" for o in ops) and inside, [(o[0], o[3], o[4]) for o in ops])
    names = [n for n in ast.walk(st) if isinstance(n, ast.Global)]
    back = [n for n in ast.walk(st) if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id == "_s468_dirs_prev"]
    check("0.5 selftest() declares both folders global, and puts both names back at its end, right beside S461's own restore",
          any({"UPI_DIR", "YESBANK_DIR"} <= set(g.names) for g in names) and len(back) == 1
          and "    SCAN_DIR = _s461_scan_prev                                    # S461\n    UPI_DIR, YESBANK_DIR = _s468_dirs_prev" in sn)
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag], R[tag + "_tmp"] = run(root, tag, d)
        check("0.6 the %s app started its real self-test and made both uploads" % tag,
              bool(R[tag]) and "abort" not in R[tag] and R[tag]["uploads"].get("yes") == 200 and R[tag]["uploads"].get("upi") == 200,
              ((R[tag] or {}).get("uploads"), (R[tag] or {}).get("abort") or p.stderr[-500:]))
    if not (R.get("old") and R.get("new") and "landed" in R["old"] and "landed" in R["new"]):
        return
    o, n = R["old"], R["new"]
    check("1.1 as on the box, with no setting the two statement folders are the app's own (upi_statements, yesbank_statements)",
          o["default_is_app_folder"] == [True, True] and n["default_is_app_folder"] == [True, True])
    check("1.2 SHOWN on the old file: during the self-test both stores are still the app's own folders, and both made-up statements landed there",
          o["during"]["upi"].endswith("upi_statements") and o["during"]["yes"].endswith("yesbank_statements")
          and len(o["landed"]["app_upi"] or []) == 1 and len(o["landed"]["app_yes"] or []) == 1, o["landed"])
    tmpn = os.path.realpath(R["new_tmp"]) + os.sep
    check("1.3 new: during the self-test both stores are throwaway folders in temp",
          os.path.realpath(n["during"]["upi"]).startswith(tmpn) and os.path.realpath(n["during"]["yes"]).startswith(tmpn)
          and "smoke_upi_" in n["during"]["upi"] and "smoke_yesbank_" in n["during"]["yes"], n["during"])
    check("1.4 new: both made-up statements landed in the throwaway folders, and the app's own two folders were never even made",
          len(n["landed"]["run_upi"] or []) == 1 and len(n["landed"]["run_yes"] or []) == 1
          and n["landed"]["app_upi"] is None and n["landed"]["app_yes"] is None
          and not os.path.exists(os.path.join(new, "upi_statements")) and not os.path.exists(os.path.join(new, "yesbank_statements")), n["landed"])
    check("1.5 new: when the run ended -- it was cut short, as an install gate can be -- the throwaway folders, the scan folder and the database copy were removed",
          not any(os.path.exists(n["during"][k]) for k in ("upi", "yes", "scan", "db")), {k: os.path.exists(v) for k, v in n["during"].items()})
    check("1.6 the scan folder and the database copy are handled exactly as before (S461) on both files",
          all(os.path.realpath(x["during"]["scan"]).startswith(os.path.realpath(R[t + "_tmp"])) for t, x in (("old", o), ("new", n))))

    # ---- PART 2: the housekeeping script, on made-up data
    hk = os.path.join(root, "hk")
    os.makedirs(os.path.join(hk, "finance_scans", "2026-08"))
    os.makedirs(os.path.join(hk, "scans"))
    tiny = b"%PDF-1.4 smoke"
    files = {"finance_scans/a.pdf": tiny, "finance_scans/2026-08/b.pdf": tiny, "finance_scans/2026-08/named.pdf": tiny,
             "finance_scans/real.pdf": b"%PDF-1.4 " + b"x" * 4000, "finance_scans/tiny.txt": b"note", "scans/live_tiny.pdf": tiny}
    for rel, blob in files.items():
        with open(os.path.join(hk, rel), "wb") as fh:
            fh.write(blob)
    fdb = os.path.join(hk, "finance.db")
    con = sqlite3.connect(fdb)
    with open(os.path.join(old, "finance_schema.sql"), encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.execute("INSERT INTO staff_ref (id, name, is_pharmacy) VALUES (1,'Made-up One',1),(2,'Made-up Two',1),(3,'Made-up Three',1),(4,'Made-up Four',1),(5,'Made-up Five',1)")
    for i, (d, status) in enumerate((("2026-08-10", "approved"), ("2026-08-11", "approved"), ("2026-08-12", "approved"),
                                     ("2026-08-13", "approved"), ("2026-08-14", "submitted")), 1):
        con.execute("INSERT INTO day_entry (id,unit,business_date,status,source,entered_by,entered_at) VALUES (?,?,?,?,'app','walk',?)",
                    (i, "medical", d, status, d + "T09:00:00"))
    exp = [(1, 1, 200000, 1, 1, "aaa111"),      # stamped, row in the ledger
           (2, 2, 300000, 2, 0, None),          # no stamp, ledger has it by hand
           (3, 3, 150000, 3, 0, None),          # no stamp, nothing in the ledger
           (4, 4, 100000, 4, 1, "gone99"),      # stamped, row not in the ledger
           (5, 5, 50000, 1, 0, None),           # on a day not approved: not listed
           (6, 1, 70000, 5, 1, "ddd444")]       # stamped, and its row truly reversed in the ledger (an approved contra)
    for xid, eid, amt, staff, posted, ref in exp:
        con.execute("INSERT INTO day_expense (id,day_entry_id,amount_p,category_fixed,staff_id,ledger_posted,ledger_ref) VALUES (?,?,?,'salary_advance',?,?,?)",
                    (xid, eid, amt, staff, posted, ref))
    con.execute("INSERT INTO attachment (day_entry_id, doc_type, path) VALUES (1,'sale_report',?)", (os.path.join(hk, "finance_scans", "2026-08", "named.pdf"),))
    con.commit()
    con.close()
    led = os.path.join(hk, "ledger.jsonl")
    with open(led, "w", encoding="utf-8") as fh:
        for r in ({"id": "aaa111", "staff": "Made-up One", "category": "ADVANCE_ISSUE", "date_from": "2026-08-10", "amount": 2000, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "Salary advance, medical 2026-08-10 (finance expense #1)"},
                  {"id": "aaa112", "staff": "Made-up One", "category": "ADVANCE_INSTALMENT", "date_from": "2026-09", "amount": -500, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "an instalment collected: it points at the advance, and is not a reversal", "contra_of": "aaa111"},
                  {"id": "ddd444", "staff": "Made-up Five", "category": "ADVANCE_ISSUE", "date_from": "2026-08-09", "amount": 700, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "by hand"},
                  {"id": "ddd445", "staff": "Made-up Five", "category": "ADVANCE_ISSUE", "date_from": "2026-08-09", "amount": -700, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "contra of ddd444", "contra_of": "ddd444"},
                  {"id": "bbb222", "staff": "Made-up Two", "category": "ADVANCE_ISSUE", "date_from": "2026-08-12", "amount": 3000, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "advance, by hand"},
                  {"id": "ccc333", "staff": "Made-up Three", "category": "ADVANCE_ISSUE", "date_from": "2026-06-01", "amount": 1500, "status": "APPROVED",
                   "maker": "wdoctor", "narration": "an older one, two months before"}):
            fh.write(json.dumps(r) + "\n")
    before = {f: md5(f) for f in (fdb, led)}
    rp = lambda *args: subprocess.run([sys.executable, "-B", a.report] + list(args), capture_output=True, text=True)
    adv = rp("advances", led, fdb).stdout
    L = [l for l in adv.splitlines() if l.startswith("  2026-")]
    check("2.1 the advances report lists the five on approved days or stamped, and not the one on a day still waiting", len(L) == 5 and "2026-08-14" not in adv, adv)
    five = [l for l in L if "Made-up Five" in l]
    L = [l for l in L if "Made-up Five" not in l]
    check("2.1b F-714: an advance with an instalment collected against it is NOT called reversed (the instalment points at it too); one with an approved contra of its own kind IS",
          "REVERSED" not in L[0] and len(five) == 1 and "REVERSED there since" in five[0], (L[0], five))
    check("2.2 stamped with its row in the ledger: said so, with the row; no stamp but entered by hand two days later: 'the ledger has it', nothing to do",
          "Made-up One  Rs 2000" in L[0] and "STAMPED, and its row is in the ledger" in L[0] and "aaa111" in L[0] and "posted by the finance app" in L[0]
          and "Made-up Two  Rs 3000" in L[1] and "NO STAMP, but the ledger has it" in L[1] and "bbb222" in L[1] and "by hand" in L[1], L[:2])
    check("2.3 no stamp and nothing near it in the ledger (a row two months before does not count): 'never reached the Staff Ledger', to look at; "
          "stamped with a row the ledger does not hold: said so, to look at",
          "Made-up Three  Rs 1500" in L[2] and "never reached the Staff Ledger" in L[2] and "TO LOOK AT" in L[2]
          and "Made-up Four  Rs 1000" in L[3] and "NOT in the ledger" in L[3] and "TO LOOK AT" in L[3], L[2:])
    check("2.4 the report changed neither the finance database nor the ledger", {f: md5(f) for f in before} == before)
    fs, live = os.path.join(hk, "finance_scans"), os.path.join(hk, "scans")
    c1 = rp("scans", fs, fdb, live).stdout
    check("2.5 counting: two tiny test scans; the one a database row names stays; a full-size PDF and a small text file are not counted; nothing moved yet",
          "2 tiny test scan(s)" in c1 and "1 more are named by a row" in c1 and os.path.isfile(os.path.join(fs, "a.pdf")), c1)
    c2 = rp("scans", fs, fdb, live, "--move").stdout
    dest = os.path.join(hk, "finance_scans.test_scans_set_aside_S468")
    check("2.6 moving: the two are MOVED beside the folder, their sub-folder kept, bytes intact; the named one, the real PDF and the text file stay; nothing is deleted",
          "2 tiny test scan(s) moved" in c2 and os.path.isfile(os.path.join(dest, "a.pdf")) and os.path.isfile(os.path.join(dest, "2026-08", "b.pdf"))
          and open(os.path.join(dest, "a.pdf"), "rb").read() == tiny and not os.path.exists(os.path.join(fs, "a.pdf"))
          and all(os.path.isfile(os.path.join(fs, x)) for x in ("2026-08/named.pdf", "real.pdf", "tiny.txt")), c2)
    c3 = rp("scans", fs, fdb, live, "--move").stdout
    check("2.7 pasted again: nothing left to move", "0 tiny test scan(s) moved" in c3, c3)
    c4 = rp("scans", live, fdb, live, "--move").stdout
    check("2.8 pointed at the LIVE scan folder: refused, and the tiny file there is untouched", "REFUSED" in c4 and os.path.isfile(os.path.join(live, "live_tiny.pdf")), c4)
    c5 = rp("scans", os.path.join(hk, "not_there"), fdb, live, "--move").stdout
    bad = os.path.join(hk, "bad.db")
    with open(bad, "wb") as fh:
        fh.write(b"not a database " * 50)
    with open(os.path.join(fs, "late.pdf"), "wb") as fh:
        fh.write(tiny)
    c6 = rp("scans", fs, bad, live, "--move").stdout
    check("2.9 a folder that is not there: nothing to do; a database that cannot be read: NOTHING is moved",
          "nothing to do" in c5 and "nothing is moved" in c6 and os.path.isfile(os.path.join(fs, "late.pdf")), (c5, c6))
    up, ys = os.path.join(hk, "upi_statements"), os.path.join(hk, "yesbank_statements")
    os.makedirs(up)
    for f in ("abc_mpr.xlsx", "def_mpr.xlsx", "ghi_REAL_MPR_SEP.xlsx"):
        open(os.path.join(up, f), "wb").close()
    c7 = rp("statements", up, ys).stdout
    check("2.10 the statement folders are only counted: 3 files, 2 with the self-test's own name; a folder not there is said; nothing moved",
          "upi_statements holds 3 file(s); 2 carry" in c7 and "is not there" in c7 and len(os.listdir(up)) == 3, c7)
    check("2.11 nothing in the finance app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) == FROM)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
