#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s467.py -- S467_WARRANTY_ON_HEALTH: a Dr MK expense warranty rides the owner's Renewals row -- walked.

  usage: walk_s467.py --apply <apply_s467.py> --finance <folder holding finance_app.py and its sibling files>

The finance app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's two insertions), each
with an EMPTY database made from the app's own schema. Each then answers the health page as the checker through the
SAME eleven situations: no asset database at all, one without the table, a damaged one, and made-up warranties against
a made-up renewals feed in every state the Renewals row has (no feed, quiet, soon, overdue). The old file's answer
is the yardstick: where no warranty is due the two must be byte for byte the same. The made-up asset database is
hashed before and after -- it is only ever read. Dates are counted from today. Nothing live is opened.
Last line: WALK_S467 GREEN|RED.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "49f52391f44643c10b052609cffc5bbe"
TO = "72d2538222a8fbd6a12d5ac2434c5a4e"
MARK = "@@S467JSON@@ "
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
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    root = os.environ["S467_ROOT"]
    if not os.path.realpath(fa.DB_PATH).startswith(os.path.realpath(root) + os.sep):
        print(MARK + json.dumps({"abort": "the finance database is not the scratch one"}))
        return
    con = sqlite3.connect(fa.DB_PATH)
    con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES ('medical','wdoctor','checker',1)")
    con.commit()
    con.close()
    c = fa.app.test_client()
    H = {"X-Clinic-User": "wdoctor"}
    today = datetime.date.today()
    day = lambda n: (today + datetime.timedelta(days=n)).isoformat()
    adb = os.path.join(root, "assets_madeup.db")
    feed = fa.RENEWALS_STATE

    def assets(rows, table=True):
        """rows: (what, days_from_today, remind_days, lane, status)"""
        for f in glob.glob(adb + "*"):
            os.remove(f)
        a = sqlite3.connect(adb)
        a.execute("CREATE TABLE bills (id INTEGER PRIMARY KEY, lane TEXT, status TEXT, vendor TEXT, stamp_no TEXT)")
        if table:
            a.execute("CREATE TABLE d664_warranty (bill_id INTEGER PRIMARY KEY, what TEXT NOT NULL, till TEXT NOT NULL, "
                      "remind_days INTEGER NOT NULL DEFAULT 30, set_by TEXT, set_at TEXT)")
        for i, (what, n, rd, lane, status) in enumerate(rows, 1):
            a.execute("INSERT INTO bills VALUES (?,?,?,?,?)", (i, lane, status, "Made-up Shop", "B-9%03d" % i))
            a.execute("INSERT INTO d664_warranty (bill_id, what, till, remind_days) VALUES (?,?,?,?)", (i, what, day(n), rd))
        a.commit()
        a.close()

    def set_feed(items):
        if items is None:
            if os.path.exists(feed):
                os.remove(feed)
            return
        with open(feed, "w", encoding="utf-8") as fh:
            json.dump({"received_at": datetime.datetime.now().isoformat(timespec="seconds"), "window_days": 30,
                       "items": [{"vendor": v, "dateISO": day(n), "note": ""} for v, n in items]}, fh)

    def look():
        r = c.get("/finance/api/health", headers=H)
        j = r.get_json() or {}
        row = [x for x in (j.get("checks") or []) if x.get("key") == "renewals"]
        rest = sorted((x["key"], x["state"], x["detail"]) for x in (j.get("checks") or []) if x.get("key") not in ("renewals", "nevfired"))
        hc = sqlite3.connect(fa.DB_PATH)
        hc.row_factory = sqlite3.Row
        try:
            head = fa._health_headline(hc)
        finally:
            hc.close()
        when = lambda t: re.sub(r"pushed \d{4}-\d\d-\d\d \d\d:\d\d", "pushed <when>", t or "") if t is not None else None
        for x in row:
            x["detail"] = when(x["detail"])
        head = when(head)
        return {"http": r.status_code, "row": row[0] if row else None, "n": len(row), "rest": rest, "worst": j.get("worst"),
                "culprit": "Renewals" in (j.get("culprits") or []), "head": head}

    DUE = [("Inverter battery (2)", 20, 30, "owner_expense", "captured")]
    QUIET = [("Fan", 3, 0, "owner_expense", "captured"), ("Kettle", -10, 30, "owner_expense", "captured"),
             ("Air conditioner", 400, 30, "owner_expense", "captured"), ("UPS", 20, 7, "owner_expense", "captured"),
             ("Rejected thing", 5, 30, "owner_expense", "rejected"), ("Left the lane", 5, 30, "clinic", "draft"),
             ("Other lane", 5, 30, "pharmacy", "captured")]
    out = {"days": {"d20": day(20), "d5": day(5), "d0": day(0)}}
    S = {}
    os.environ["ASSETS_DB"] = os.path.join(root, "no_such_assets.db")
    set_feed(None)
    S["A_no_assets_file"] = look()
    os.environ["ASSETS_DB"] = adb
    assets([], table=False)
    S["B_no_table"] = look()
    with open(adb, "wb") as fh:
        fh.write(b"this is not a database at all, only some bytes " * 40)
    S["C_damaged_file"] = look()
    assets(QUIET)
    S["D_none_in_window_no_feed"] = look()
    assets(DUE + QUIET)
    before = md5(adb)
    S["E_due_no_feed"] = look()
    set_feed([("GoDaddy domain", 40)])
    S["F_due_feed_quiet"] = look()
    set_feed([("GoDaddy domain", 3)])
    S["G_due_feed_warn"] = look()
    set_feed([("Arms licence", -5)])
    S["H_due_feed_overdue"] = look()
    set_feed([("GoDaddy domain", 40)])
    assets([("Geyser <b>x</b>", 5, 7, "owner_expense", "captured")] + DUE + QUIET)
    before2 = md5(adb)
    S["I_two_due_one_inside_7"] = look()
    page = c.get("/finance/health", headers=H)
    out["page"] = [page.status_code, "Geyser &lt;b&gt;x&lt;/b&gt;" in page.get_data(as_text=True), "Geyser <b>x</b>" in page.get_data(as_text=True)]
    out["read_only"] = [before2 == md5(adb), sorted(os.path.basename(f) for f in glob.glob(adb + "*"))]
    assets([("Ends today", 0, 7, "owner_expense", "captured")])
    S["J_ends_today"] = look()
    assets([("Kettle", -1, 30, "owner_expense", "captured"), ("Lamp", -400, 30, "owner_expense", "captured")])
    set_feed([("GoDaddy domain", 40)])
    S["K_only_ended"] = look()
    out["S"] = S
    out["first_hash_held"] = bool(before)
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))


def make_db(appdir):
    con = sqlite3.connect(os.path.join(appdir, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    con.close()


def run(root, tag, appdir):
    base = os.path.join(root, "run_" + tag)
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    e = dict(os.environ)
    # the cron token below is made up afresh at every run -- it is never the box's, and no value is written in this file
    e.update({"S467_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(base, "scans"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"), "PYTHONDONTWRITEBYTECODE": "1"})
    shutil.move(os.path.join(appdir, "finance.db"), os.path.join(base, "finance.db"))
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s467_walk_")
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
    print("WALK_S467 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    check("0.1 the unpatched finance_app.py is the file this kit was built from (49f52391, S463's)",
          md5(os.path.join(old, "finance_app.py")) == FROM, md5(os.path.join(old, "finance_app.py")))
    if md5(os.path.join(old, "finance_app.py")) != FROM:
        return
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.2 the two insertions apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read().splitlines()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read().splitlines()
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, so, sn, autojunk=False).get_opcodes() if o[0] != "equal"]
    added = [l for o in ops for l in sn[o[3]:o[4]]]
    check("0.4 two insertions and NOTHING removed or changed: every old line is still there, in order (%d lines added)" % len(added),
          len(ops) == 2 and all(o[0] == "insert" for o in ops), [(o[0], o[1], o[2]) for o in ops])
    check("0.5 the added lines write nothing: no INSERT, UPDATE, DELETE, commit, open(..., 'w') or add( among them",
          not any(k in l for l in added for k in ("INSERT ", "UPDATE ", "DELETE ", ".commit(", "open(", " add(", "os.remove", "os.replace")),
          [l for l in added if any(k in l for k in ("INSERT ", "UPDATE ", "DELETE ", ".commit(", "open(", " add("))][:4])
    for d in (old, new):
        make_db(d)
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d)
        check("0.6 the %s app answered the health page through all eleven situations" % tag,
              bool(R[tag]) and "abort" not in R[tag] and len(R[tag].get("S", {})) == 11 and all(v["http"] == 200 and v["n"] == 1 for v in R[tag]["S"].values()),
              (R[tag] or {}).get("abort") or p.stderr[-700:])
    if not (R.get("old") and R.get("new") and "S" in R["old"] and "S" in R["new"]):
        return
    o, n, D = R["old"]["S"], R["new"]["S"], R["new"]["days"]
    same = lambda k: n[k]["row"] == o[k]["row"] and n[k]["rest"] == o[k]["rest"] and n[k]["worst"] == o[k]["worst"] and n[k]["head"] == o[k]["head"]

    # ---- 1 · where no warranty is due, nothing has moved
    check("1.1 no asset database on the box: the Renewals row, every other row, the page's colour and the tile line are the old file's, byte for byte", same("A_no_assets_file"))
    check("1.2 an asset database without the table (S466 not installed): the same", same("B_no_table"))
    check("1.3 a damaged asset database: the health page still answers, and is the old page", same("C_damaged_file"))
    check("1.4 warranties exist but none is inside its window -- 'No reminder' 3 days out, a 7-day reminder 20 days out, one 400 days out, "
          "one ENDED, one on a rejected paper, one whose paper left the lane, one on another lane: the old page", same("D_none_in_window_no_feed"))
    check("1.5 only ended warranties (yesterday, and long ago): the old page -- an ended warranty is never 'overdue', never red", same("K_only_ended")
          and n["K_only_ended"]["row"]["state"] == "ok", n["K_only_ended"]["row"])
    check("1.6 in every situation, every OTHER row of the health page is the old file's", all(n[k]["rest"] == o[k]["rest"] for k in n))

    # ---- 2 · a warranty inside its window is said
    e = n["E_due_no_feed"]["row"]
    want = "warranty: Inverter battery (2) ends in 20 days (%s)" % D["d20"]
    check("2.1 SHOWN on the old file: with the battery's warranty 20 days from its end, the Renewals row says nothing of it",
          "warranty" not in o["E_due_no_feed"]["row"]["detail"] and "warranty" not in o["F_due_feed_quiet"]["row"]["detail"])
    check("2.2 new, no renewals feed yet: the row says it first, then what it said before; info (20 days is not yet a warning)",
          e["state"] == "info" and e["detail"] == want + " · " + o["E_due_no_feed"]["row"]["detail"], e)
    f = n["F_due_feed_quiet"]["row"]
    check("2.3 new, the feed quiet ('nothing inside 30 days', ok): the row is raised to info and leads with the warranty",
          o["F_due_feed_quiet"]["row"]["state"] == "ok" and f["state"] == "info"
          and f["detail"] == want + " · " + o["F_due_feed_quiet"]["row"]["detail"], f)
    check("2.4 info does not colour the page or reach the portal tile: worst, the named rows and the tile line are the old file's",
          n["F_due_feed_quiet"]["worst"] == o["F_due_feed_quiet"]["worst"] and n["F_due_feed_quiet"]["head"] == o["F_due_feed_quiet"]["head"]
          and n["F_due_feed_quiet"]["culprit"] is False, (n["F_due_feed_quiet"]["worst"], n["F_due_feed_quiet"]["head"]))
    g = n["G_due_feed_warn"]["row"]
    check("2.5 a renewal 3 days out already makes the row warn: its own words stay first, the warranty is added after, the state is unchanged",
          o["G_due_feed_warn"]["row"]["state"] == "warn" and g["state"] == "warn"
          and g["detail"] == o["G_due_feed_warn"]["row"]["detail"] + " · " + want, g)
    h = n["H_due_feed_overdue"]["row"]
    check("2.6 an OVERDUE renewal keeps the row red and its own words first; the warranty is added after; the tile line still names the overdue one",
          o["H_due_feed_overdue"]["row"]["state"] == "bad" and h["state"] == "bad"
          and h["detail"] == o["H_due_feed_overdue"]["row"]["detail"] + " · " + want
          and (n["H_due_feed_overdue"]["head"] or "").startswith((o["H_due_feed_overdue"]["head"] or "x")[:60]), (h, n["H_due_feed_overdue"]["head"]))
    i = n["I_two_due_one_inside_7"]
    check("2.7 a warranty inside 7 days makes the row WARN: nearest first, '1 more warranty reminder'; Renewals is now among the rows the page names as needing a look (it was not, on the old file)",
          i["row"]["state"] == "warn" and i["row"]["detail"].startswith("warranty: Geyser <b>x</b> ends in 5 days (%s) · 1 more warranty reminder · " % D["d5"])
          and i["culprit"] is True and o["I_two_due_one_inside_7"]["culprit"] is False
          and o["I_two_due_one_inside_7"]["row"]["state"] == "ok", (i["row"], i["culprit"]))
    j = n["J_ends_today"]["row"]
    check("2.8 the last day reads 'ends today'", j["state"] == "warn" and j["detail"].startswith("warranty: Ends today ends today (%s)" % D["d0"]), j)
    check("2.9 a name with markup in it is shown as text on the health page, never as markup", R["new"]["page"] == [200, True, False], R["new"]["page"])

    # ---- 3 · it only reads
    check("3.1 the asset database is byte for byte what it was after the health page read it, and nothing was made beside it (no journal, no -wal, no -shm)",
          R["new"]["read_only"][0] is True and R["new"]["read_only"][1] == ["assets_madeup.db"], R["new"]["read_only"])
    check("3.2 nothing in the finance app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) == FROM)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
