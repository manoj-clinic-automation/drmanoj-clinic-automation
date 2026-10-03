#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s462.py -- S462_ADVANCE_POST_ONCE: a salary advance reaches the Staff Ledger once -- walked.

  usage: walk_s462.py --apply <apply_s462.py> --finance <folder holding finance_app.py> [--ledger-py <folder holding staff_ledger.py>]

The app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's edits); each gets an EMPTY
database made from the app's own schema and an EMPTY Staff Ledger in the scratch folder (LEDGER_DIR, STAFF_CSV and the
notification address all point there or nowhere -- the child refuses to post if the ledger folder is not the scratch
one). The box's own staff_ledger.py does the posting, so the ledger's rules are the real ones. Each fault is first
SHOWN on the old file, then shown gone on the new one. Nothing live is opened. Last line: WALK_S462 GREEN|RED.
"""
import argparse
import datetime as dt
import glob
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "26a532a6ec212ac66e6cfb41b37844eb"
TO = "27a162e6740140d4ce7d2e293eae9809"
MARK = "@@S462JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:400]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


# ============================================================================ the child: every scenario, one file
def child():
    root = os.environ["S462_ROOT"]
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    sl = fa._staff_ledger_module()
    if not os.path.realpath(sl.LEDGER_DIR).startswith(os.path.realpath(root) + os.sep):
        print(MARK + json.dumps({"abort": "the ledger folder is %s, not the scratch one" % sl.LEDGER_DIR}))
        return
    if getattr(sl, "NTFY_URL", ""):
        print(MARK + json.dumps({"abort": "a notification address is set"}))
        return
    out = {"ledger_dir_is_scratch": True}
    c = fa.app.test_client()
    con = sqlite3.connect(fa.DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("INSERT INTO staff_ref (name,is_pharmacy,active) VALUES ('Darpan',1,1)")
    sid = con.execute("SELECT id FROM staff_ref WHERE name='Darpan'").fetchone()[0]
    con.commit()
    with fa.app.test_request_context("/"):
        fa._expense_uid_col(fa.db())
        fa.db().commit()

    def mk(date, advs, status="submitted"):
        con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at) "
                    "VALUES ('medical',?,?,'app','darpan',?)", (date, status, date + "T09:00:00"))
        e = con.execute("SELECT id FROM day_entry WHERE unit='medical' AND business_date=?", (date,)).fetchone()[0]
        con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','cash',?)",
                    (e, 2000000))
        con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,'pharmacy_sale','upi',0)", (e,))
        for amt, uid in advs:
            con.execute("INSERT INTO day_expense (day_entry_id,amount_p,amount_known,category_fixed,staff_id,"
                        "category_text,expense_uid,ledger_posted) VALUES (?,?,1,'salary_advance',?,"
                        "'Salary advance - Darpan',?,0)", (e, amt, sid, uid))
        con.commit()
        return e

    def led(date):
        return [[r["amount"], r["status"], r.get("contra_of") or ""] for r in sl.load_ledger() if r["date_from"] == date]

    def stamps(e):
        return [[r["amount_p"], r["ledger_posted"], r["ledger_ref"] or ""] for r in con.execute(
            "SELECT amount_p, ledger_posted, ledger_ref FROM day_expense WHERE day_entry_id=? ORDER BY id", (e,))]

    def status(e):
        return con.execute("SELECT status FROM day_entry WHERE id=?", (e,)).fetchone()[0]

    def approve(date):
        r = c.post("/finance/api/approve/" + date)
        j = r.get_json() or {}
        return [r.status_code, j.get("error") or "", j.get("message") or "",
                len(j.get("salary_advances_pending_ledger") or []), len(j.get("posted_kept") or [])]

    def save(date, exps, total="20000"):
        r = c.post("/finance/api/day", json={"business_date": date, "total": total, "upi": "0", "action": "submit",
                                             "missing_scan_reason": "walk", "expenses": exps})
        j = r.get_json() or {}
        return [r.status_code, j.get("error") or "", j.get("message") or ""]

    def adv(amount, uid):
        return {"amount": amount, "category": "salary_advance_self", "uid": uid}

    # ---- 1 · two advances, the second not whole rupees
    d = "2026-05-04"
    e = mk(d, [(100000, "walkS1a00001"), (20050, "walkS1b00001")])
    s = {"first": approve(d), "ledger_after_first": led(d), "stamps_after_first": stamps(e), "status_after_first": status(e)}
    con.execute("UPDATE day_expense SET amount_p=20000 WHERE day_entry_id=? AND amount_p=20050", (e,))
    con.commit()
    s.update(second=approve(d), ledger_after_second=led(d), stamps_after_second=stamps(e), status_after_second=status(e))
    out["s1"] = s

    # ---- 2 · the day's two advances together are over the month ceiling
    d = "2026-06-04"
    e = mk(d, [(3000000, "walkS2a00001"), (4000000, "walkS2b00001")])
    out["s2"] = {"first": approve(d), "ledger": led(d), "stamps": stamps(e), "status": status(e),
                 "ceiling": sl.advance_ceiling("Darpan")}

    # ---- 3 · the ledger itself fails on the SECOND post (a full disk, say)
    d = "2026-07-06"
    e = mk(d, [(100000, "walkS3a00001"), (50000, "walkS3b00001")])
    real, n = sl.make_entry, [0]

    def flaky(*a, **k):
        n[0] += 1
        if n[0] == 2:
            raise OSError("the ledger could not be written (made by the walk)")
        return real(*a, **k)
    sl.make_entry = flaky
    s = {"first": approve(d), "ledger_after_first": led(d), "stamps_after_first": stamps(e), "status_after_first": status(e)}
    sl.make_entry = real
    s["audit"] = con.execute("SELECT COUNT(*) FROM audit_log WHERE action='advance_posted_day_not_approved'").fetchone()[0]
    s.update(second=approve(d), ledger_after_second=led(d), stamps_after_second=stamps(e), status_after_second=status(e))
    out["s3"] = s

    # ---- 4 · an APPROVED day is corrected, then approved again
    t = fa.today()
    da, db_, dc, dd, de, df = [(t - dt.timedelta(days=k)).isoformat() for k in (1, 2, 3, 4, 5, 6)]
    ea = mk(da, [(100000, "walkS4a00001")])
    s = {"approve1": approve(da), "ledger1": led(da), "stamps1": stamps(ea)}
    s.update(resave=save(da, [adv("1000", "walkS4a00001")]), stamps_resaved=stamps(ea), status_resaved=status(ea),
             revisions=con.execute("SELECT COUNT(*) FROM day_revision WHERE day_entry_id=?", (ea,)).fetchone()[0])
    s.update(approve2=approve(da), ledger2=led(da), stamps2=stamps(ea), status2=status(ea))
    out["s4a"] = s
    # 4b · an old row that carries no uid: matched by its amount
    eb = mk(db_, [(100000, None)])
    s = {"approve1": approve(db_)}
    s.update(resave=save(db_, [adv("1000", "walkS4b00001")]), stamps_resaved=stamps(eb), approve2=approve(db_), ledger2=led(db_))
    out["s4b"] = s
    # 4c · the posted advance is changed, then removed; then reversed in the ledger and changed
    ec = mk(dc, [(100000, "walkS4c00001")])
    s = {"approve1": approve(dc), "stamps1": stamps(ec)}
    s.update(change=save(dc, [adv("1500", "walkS4c00001")]), stamps_after_change=stamps(ec), status_after_change=status(ec),
             revisions_after_change=con.execute("SELECT COUNT(*) FROM day_revision WHERE day_entry_id=?", (ec,)).fetchone()[0])
    s.update(remove=save(dc, []), stamps_after_remove=stamps(ec), status_after_remove=status(ec))
    try:
        sl.make_contra(sl.load_users(), "manoj", [r["id"] for r in sl.load_ledger() if r["date_from"] == dc][0], "walk: reversed")
        s["contra"] = "made"
    except Exception as ex:                                          # noqa: BLE001
        s["contra"] = "FAILED %s" % ex
    s.update(change_after_contra=save(dc, [adv("1500", "walkS4c00001")]), stamps_after_contra=stamps(ec),
             approve2=approve(dc), ledger2=led(dc), stamps2=stamps(ec))
    out["s4c"] = s
    # 4d · the posted advance is kept and a NEW one is added
    ed_ = mk(dd, [(100000, "walkS4d00001")])
    s = {"approve1": approve(dd)}
    s.update(resave=save(dd, [adv("1000", "walkS4d00001"), adv("500", "walkS4d00002")]), stamps_resaved=stamps(ed_),
             approve2=approve(dd), ledger2=led(dd), stamps2=stamps(ed_))
    out["s4d"] = s
    # 4e · two advances of the SAME amount, both posted: each keeps its own ledger row
    ee = mk(de, [(70000, "walkS4e00001"), (70000, "walkS4e00002")])
    s = {"approve1": approve(de), "stamps1": stamps(ee)}
    s.update(resave=save(de, [adv("700", "walkS4e00002"), adv("700", "walkS4e00001")]), stamps_resaved=stamps(ee),
             approve2=approve(de), ledger2=led(de))
    s["uids_resaved"] = [[r["expense_uid"], r["ledger_ref"]] for r in con.execute(
        "SELECT expense_uid, ledger_ref FROM day_expense WHERE day_entry_id=? ORDER BY id", (ee,))]
    out["s4e"] = s

    # ---- 5 · unchanged: a plain day, a day with one advance, a first save
    ef = mk(df, [])
    out["s5_plain"] = {"approve": approve(df), "status": status(ef)}
    dg = "2026-04-06"
    eg = mk(dg, [(100000, "walkS5g00001")])
    out["s5_one"] = {"approve": approve(dg), "ledger": led(dg), "stamps": [x[:2] for x in stamps(eg)], "status": status(eg),
                     "again": approve(dg), "ledger_again": led(dg)}
    dh = t.isoformat()
    out["s5_new_day"] = {"save": save(dh, [adv("300", "walkS5h00001")]),
                         "rows": [[r["amount_p"], r["category_fixed"], r["ledger_posted"]] for r in con.execute(
                             "SELECT x.amount_p, x.category_fixed, x.ledger_posted FROM day_expense x JOIN day_entry e "
                             "ON e.id=x.day_entry_id WHERE e.business_date=?", (dh,))]}
    out["ledger_total"] = len(sl.load_ledger())
    print(MARK + json.dumps(out))


# ============================================================================ the parent
def make_app(src, dst):
    os.makedirs(dst)
    n = 0
    for pat in ("*.py", "*.sql", "*.html"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
                n += 1
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))
    return n


def make_db(appdir):
    con = sqlite3.connect(os.path.join(appdir, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    con.close()


def run(root, tag, appdir, ledger_py):
    led = os.path.join(root, "ledger_" + tag)
    os.makedirs(led)
    with open(os.path.join(led, "users.json"), "w") as fh:
        json.dump({"manoj": {"role": "checker"}}, fh)
    open(os.path.join(led, "ledger.jsonl"), "w").close()
    with open(os.path.join(led, "staff_master.csv"), "w") as fh:
        fh.write("name,base_salary,active\nDarpan,100000,Y\n")          # ceiling: 50 per cent = Rs 50,000
    tmp = os.path.join(root, "tmp_" + tag)
    os.makedirs(tmp)
    e = dict(os.environ)
    e.update({"S462_ROOT": root, "FINANCE_DB": os.path.join(appdir, "finance.db"),
              "FINANCE_SCAN_DIR": os.path.join(root, "scans_" + tag), "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp,
              "FINANCE_ALLOW_HEADER_AUTH": "1", "FINANCE_DEV_USER": "manoj", "FINANCE_DEV_ROLE": "checker",
              "LEDGER_DIR": led, "FINANCE_LEDGER_JSONL": os.path.join(led, "ledger.jsonl"),
              "STAFF_CSV": os.path.join(led, "staff_master.csv"), "NTFY_URL": "",
              "FINANCE_LEDGER_PY_DIR": ledger_py,
              "FINANCE_RENEWALS_STATE": os.path.join(root, "renewals.json"),
              "FINANCE_BACKUP_DIR": os.path.join(root, "backups"),
              "FINANCE_AUTOAPPLY_OFF": os.path.join(root, "AUTOAPPLY_OFF_absent"),
              "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=300)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--ledger-py", default=None)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s462_walk_")
    try:
        walk(a, root)
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S462 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    ledger_py = os.path.abspath(a.ledger_py or os.path.dirname(fin))
    check("0.1 the box's own staff_ledger.py is there to do the posting", os.path.isfile(os.path.join(ledger_py, "staff_ledger.py")),
          ledger_py)
    live_ledger = os.path.join(ledger_py, "staff_ledger", "ledger.jsonl")
    before = md5(live_ledger) if os.path.isfile(live_ledger) else "absent"
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    n = make_app(fin, old)
    check("0.2 the unpatched finance_app.py is the file this kit was built from (26a532a6)",
          md5(os.path.join(old, "finance_app.py")) == FROM, md5(os.path.join(old, "finance_app.py")))
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.3 the edits apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    check("0.4 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
    ol, nl = so.splitlines(), sn.splitlines()
    gone = [x for x in ol if x not in set(nl)]
    check("0.5 one old line is replaced (the refusal's message); nothing else is removed",
          len(gone) == 1 and "The day was NOT approved" in gone[0], gone)
    added = [x for x in nl if x not in set(ol)]
    check("0.6 no route, gate or role line is among the %d added lines" % len(added),
          not any(("@app.route" in x or "require(" in x or "PUBLIC_PATHS" in x) for x in added))
    for d in (old, new):
        make_db(d)

    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d, ledger_py)
        check("0.7 the %s app ran every scenario against a Staff Ledger in the scratch folder" % tag,
              bool(R[tag]) and R[tag].get("ledger_dir_is_scratch") and "abort" not in R[tag],
              (R[tag] or {}).get("abort") or p.stderr[-500:])
    if not (R.get("old") and R.get("new") and "s1" in R["old"] and "s1" in R["new"]):
        return
    o, nw = R["old"], R["new"]

    # ---- 1
    a1, b1 = o["s1"], nw["s1"]
    check("1.1 both refuse the day whose second advance is not whole rupees", a1["first"][0] == 409 and b1["first"][0] == 409
          and "whole rupees" in b1["first"][2])
    check("1.2 SHOWN on the old file: the first advance is already in the ledger, with no stamp",
          len(a1["ledger_after_first"]) == 1 and [x[1] for x in a1["stamps_after_first"]] == [0, 0], a1)
    check("1.3 SHOWN on the old file: after the correction the first advance is in the ledger TWICE",
          sorted(x[0] for x in a1["ledger_after_second"]) == [200, 1000, 1000], a1["ledger_after_second"])
    check("1.4 new: the refusal writes NOTHING to the ledger and the day stays submitted",
          b1["ledger_after_first"] == [] and [x[1] for x in b1["stamps_after_first"]] == [0, 0]
          and b1["status_after_first"] == "submitted", b1)
    check("1.5 new: after the correction each advance is in the ledger once, both stamped, the day approved",
          b1["second"][0] == 200 and sorted(x[0] for x in b1["ledger_after_second"]) == [200, 1000]
          and [x[1] for x in b1["stamps_after_second"]] == [1, 1] and b1["status_after_second"] == "approved", b1)

    # ---- 2
    a2, b2 = o["s2"], nw["s2"]
    check("2.1 the ledger's ceiling in this walk is Rs 50,000", a2["ceiling"] == 50000 and b2["ceiling"] == 50000)
    check("2.2 SHOWN on the old file: 30,000 + 40,000 -- the first is posted, the second refused, the day not approved",
          a2["first"][0] == 409 and [x[0] for x in a2["ledger"]] == [30000] and [x[1] for x in a2["stamps"]] == [0, 0], a2)
    check("2.3 new: the same day is refused BEFORE anything is posted, and the message says so",
          b2["first"][0] == 409 and b2["ledger"] == [] and b2["status"] == "submitted"
          and "ceiling" in b2["first"][2] and "Nothing was written" in b2["first"][2], b2)

    # ---- 3
    a3, b3 = o["s3"], nw["s3"]
    check("3.1 SHOWN on the old file: the ledger fails on the second post -- the first is in the ledger, unstamped; the retry posts it again",
          len(a3["ledger_after_first"]) == 1 and [x[1] for x in a3["stamps_after_first"]] == [0, 0]
          and sorted(x[0] for x in a3["ledger_after_second"]) == [500, 1000, 1000], a3)
    check("3.2 new: the same failure -- the day is not approved, and the advance the ledger took KEEPS its stamp and its ledger row's id",
          b3["first"][0] == 409 and b3["status_after_first"] == "submitted" and len(b3["ledger_after_first"]) == 1
          and [x[1] for x in b3["stamps_after_first"]] == [1, 0] and len(b3["stamps_after_first"][0][2]) == 12, b3)
    check("3.3 new: the refusal says what was kept, and the audit log has the line",
          "kept as posted" in b3["first"][2] and b3["first"][4] == 1 and b3["audit"] == 1 and a3["audit"] == 0, b3["first"])
    check("3.4 new: the retry posts ONLY the advance that was not taken; the day is approved",
          b3["second"][0] == 200 and b3["second"][3] == 1 and sorted(x[0] for x in b3["ledger_after_second"]) == [500, 1000]
          and [x[1] for x in b3["stamps_after_second"]] == [1, 1] and b3["status_after_second"] == "approved", b3)

    # ---- 4a
    a4, b4 = o["s4a"], nw["s4a"]
    check("4.1 both: the day approves and its advance is posted once", a4["approve1"][0] == 200 and b4["approve1"][0] == 200
          and len(a4["ledger1"]) == 1 and len(b4["ledger1"]) == 1 and b4["stamps1"][0][1] == 1)
    check("4.2 both: the doctor's correction of the approved day is saved, the old version kept as a revision",
          a4["resave"][0] == 200 and b4["resave"][0] == 200 and a4["revisions"] == 1 and b4["revisions"] == 1
          and b4["status_resaved"] == "submitted", (a4["resave"], b4["resave"]))
    check("4.3 SHOWN on the old file: the correction wiped the stamp, and re-approval posted the advance a SECOND time",
          a4["stamps_resaved"][0][1] == 0 and [x[0] for x in a4["ledger2"]] == [1000, 1000], a4)
    check("4.4 new: the stamp and the ledger row's id survive the correction",
          b4["stamps_resaved"] == b4["stamps1"] and b4["stamps_resaved"][0][1] == 1, (b4["stamps1"], b4["stamps_resaved"]))
    check("4.5 new: re-approval approves the day and posts nothing; the ledger holds the advance once",
          b4["approve2"][0] == 200 and b4["approve2"][3] == 0 and [x[0] for x in b4["ledger2"]] == [1000]
          and b4["status2"] == "approved", b4)
    # ---- 4b
    check("4.6 new: an old row with no uid is matched by its amount -- stamp kept, ledger once (old file: twice)",
          nw["s4b"]["stamps_resaved"][0][1] == 1 and [x[0] for x in nw["s4b"]["ledger2"]] == [1000]
          and [x[0] for x in o["s4b"]["ledger2"]] == [1000, 1000], (o["s4b"], nw["s4b"]))
    # ---- 4c
    a5, b5 = o["s4c"], nw["s4c"]
    check("4.7 SHOWN on the old file: changing a posted advance to 1,500 is accepted, and the ledger then holds 1,000 AND 1,500",
          a5["change"][0] == 200, a5["change"])
    check("4.8 new: changing a posted advance is refused in words that say what to do; the day is untouched",
          b5["change"][0] == 409 and b5["change"][1] == "advance_already_posted" and "Staff Ledger" in b5["change"][2]
          and b5["stamps_after_change"] == b5["stamps1"] and b5["status_after_change"] == "approved"
          and b5["revisions_after_change"] == 0, b5)
    check("4.9 new: removing a posted advance is refused the same way",
          b5["remove"][0] == 409 and b5["remove"][1] == "advance_already_posted" and b5["stamps_after_remove"] == b5["stamps1"]
          and b5["status_after_remove"] == "approved", b5["remove"])
    check("4.10 new: once the ledger has reversed it (an approved contra), the change is accepted and the new amount posts once",
          b5["contra"] == "made" and b5["change_after_contra"][0] == 200 and b5["stamps_after_contra"][0][:2] == [150000, 0]
          and b5["approve2"][0] == 200 and sorted(x[0] for x in b5["ledger2"]) == [-1000, 1000, 1500]
          and b5["stamps2"][0][1] == 1, b5)
    # ---- 4d
    b6 = nw["s4d"]
    check("4.11 new: a posted advance kept and a NEW one added -- only the new one is posted at re-approval",
          b6["resave"][0] == 200 and [x[:2] for x in b6["stamps_resaved"]] == [[100000, 1], [50000, 0]]
          and b6["approve2"][0] == 200 and b6["approve2"][3] == 1 and sorted(x[0] for x in b6["ledger2"]) == [500, 1000]
          and [x[1] for x in b6["stamps2"]] == [1, 1], b6)
    check("4.12 SHOWN on the old file: the same correction posts the old advance again",
          sorted(x[0] for x in o["s4d"]["ledger2"]) == [500, 1000, 1000], o["s4d"]["ledger2"])
    # ---- 4e
    b7 = nw["s4e"]
    refs1 = sorted(x[2] for x in b7["stamps1"])
    check("4.13 new: two advances of the same amount each keep their OWN ledger row through a correction",
          b7["resave"][0] == 200 and sorted(x[2] for x in b7["stamps_resaved"]) == refs1 and len(set(refs1)) == 2
          and [x[1] for x in b7["stamps_resaved"]] == [1, 1] and b7["approve2"][3] == 0
          and [x[0] for x in b7["ledger2"]] == [700, 700], b7)
    check("4.14 new: each kept its row by its uid, though the page sent them in the other order",
          len({tuple(x) for x in b7["uids_resaved"]}) == 2 and all(x[1] for x in b7["uids_resaved"]), b7["uids_resaved"])

    # ---- 5
    check("5.1 unchanged: a day with no advance approves the same, old and new",
          o["s5_plain"] == nw["s5_plain"] and nw["s5_plain"]["approve"][0] == 200 and nw["s5_plain"]["status"] == "approved")
    check("5.2 unchanged: a day with one advance -- approved, posted once, stamped; a second approval is refused and posts nothing",
          o["s5_one"] == nw["s5_one"] and nw["s5_one"]["approve"][0] == 200 and nw["s5_one"]["approve"][3] == 1
          and [x[0] for x in nw["s5_one"]["ledger"]] == [1000] and nw["s5_one"]["stamps"] == [[100000, 1]]
          and nw["s5_one"]["again"][0] == 409 and nw["s5_one"]["ledger_again"] == nw["s5_one"]["ledger"],
          (o["s5_one"], nw["s5_one"]))
    check("5.3 unchanged: a first save of a new day with an advance -- saved, not stamped",
          o["s5_new_day"] == nw["s5_new_day"] and nw["s5_new_day"]["save"][0] == 200
          and nw["s5_new_day"]["rows"] == [[30000, "salary_advance", 0]], (o["s5_new_day"], nw["s5_new_day"]))
    check("5.4 the count: the old file wrote %d ledger rows for these days, the new one %d" % (o["ledger_total"], nw["ledger_total"]),
          o["ledger_total"] > nw["ledger_total"])
    after = md5(live_ledger) if os.path.isfile(live_ledger) else "absent"
    check("5.5 the live Staff Ledger beside the box's staff_ledger.py is byte for byte what it was", before == after)
    check("5.6 nothing in the app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) in (FROM, TO))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
