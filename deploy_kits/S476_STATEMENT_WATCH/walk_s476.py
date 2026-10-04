#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s476.py -- S476_STATEMENT_WATCH (session 294, 04-Oct-2026). Hermetic (F-709): the four files are copied into a scratch
folder (old as they are, new with the kit); an EMPTY database from packs.ensure(); a scratch inbox; throwaway Flask apps that
mount the packs blueprint with made-up logins; the backup's own gather() pointed at made-up folders. Nothing live is opened,
no network, no key, no Drive.

  1. THE ROAD (F-723), against fixed 'today's: an empty shelf says so; on the 3rd with nothing fetched this month and last
     month's cells empty -> WARN, naming the last arrival and the relay; on the 2nd (before the window) -> quiet; a file today ->
     quiet; four quiet days inside the window with some arrived -> a grey note that names what is missing, still on the 10th,
     gone on the 11th; NOTHING AT ALL this month stays amber after the 10th; every cell filled -> quiet whatever the dates; a
     CARD file is not a bank arrival; the three settings move the window; January looks back at December; cells that are only
     PARTIAL keep the amber but never make the grey note; a closed database is answered, never raised; the health row carries
     the same state.
  2. THE TEXT DOOR (F-725): the owner gets the text of the file as fetched, and of the unlocked copy when there is one
     (a real PDF through pdftotext when this machine has it); no-store; an unknown id is 404; a staff login gets nothing.
  3. THE PAGE: packs.html carries the road's place, its call and its function; the state door carries 'road'.
  4. THE HEALTH HOOK: finance_app.py gained exactly one block, straight after the Reception PC row's, and nothing else.
  5. THE BACKUP (F-243 and the two trees): the login store is taken as a file; the photos and the order snapshots as trees --
     every depth, a temp file skipped, a secret-named file skipped and counted, each tree ONE source, a pruned file changes
     nothing, an absent tree is 'missing' and not an error; no basename or label collides; the earlier lists are unchanged.
  6. SHOWN on the old files: no statement_road, no text door, no login store and neither tree in the backup's lists.
Last line: WALK_S476 GREEN|RED.
   usage: walk_s476.py --apply apply_s476.py --finance /root/finance --backup /root/state_backup
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FAILS, CHECKS = [], 0
FIN_FILES = ("packs.py", "packs.html", "stmt_shelf.py", "finance_icici.py", "finance_yesbank.py", "yes_branch.py")


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, str(detail)[:400]))


def md5(path):
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def load(folder, fname, tag):
    sys.path.insert(0, folder)
    for k in [k for k in sys.modules if k in ("packs", "finance_icici", "finance_yesbank", "yes_branch")]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location(tag, os.path.join(folder, fname))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def tiny_pdf(words):
    """A real one-page PDF with a text layer and a correct xref table."""
    body = ("BT /F1 18 Tf 20 100 Td (%s) Tj ET" % words).encode()
    objs = [b"<</Type/Catalog/Pages 2 0 R>>", b"<</Type/Pages/Kids[3 0 R]/Count 1>>",
            b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 400 144]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>",
            b"<</Length %d>>\nstream\n" % len(body) + body + b"\nendstream", b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>"]
    out, offs = b"%PDF-1.4\n", []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
    x = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1) + b"".join(b"%010d 00000 n \n" % o for o in offs)
    out += b"trailer\n<</Size %d/Root 1 0 R>>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, x)
    return out


def dbf(dbp):
    con = sqlite3.connect(dbp, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def add_file(con, drive_id, name, folder, fetched_at, slot_id=None, pf=None, pt=None, read_status=None, local=None, unlocked=None, locked=0):
    con.execute("INSERT INTO stmt_file (drive_id, name, folder, subfolder, fetched_at, slot_id, period_from, period_to, read_status, local_path,"
                " unlocked_path, locked) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (drive_id, name, folder, "", fetched_at, slot_id, pf, pt, read_status, local, unlocked, locked))
    con.commit()
    return con.execute("SELECT id FROM stmt_file WHERE drive_id=?", (drive_id,)).fetchone()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--backup", required=True)
    a = ap.parse_args()
    live = [os.path.join(a.finance, f) for f in ("packs.py", "packs.html", "finance_app.py")] + [os.path.join(a.backup, "clinic_state_backup.py")]
    before = [md5(p) for p in live]
    scr = tempfile.mkdtemp(prefix="s476_walk_")
    try:
        old = os.path.join(scr, "old"); new = os.path.join(scr, "new"); inbox = os.path.join(scr, "inbox")
        for d in (old, new, inbox):
            os.makedirs(d)
        for f in FIN_FILES:
            src = os.path.join(a.finance, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(old, f)); shutil.copy2(src, os.path.join(new, f))
        for src in (os.path.join(a.finance, "finance_app.py"), os.path.join(a.backup, "clinic_state_backup.py")):
            shutil.copy2(src, os.path.join(old, os.path.basename(src))); shutil.copy2(src, os.path.join(new, os.path.basename(src)))
        r = subprocess.run([sys.executable, "-B", a.apply] + [os.path.join(new, f) for f in ("packs.py", "packs.html", "finance_app.py", "clinic_state_backup.py")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-300:])
        os.environ.update(STMT_INBOX=inbox, PACKS_DIR=os.path.join(scr, "packs_store"), PACKS_ENV=os.path.join(scr, "no.env"),
                          ASSETS_UPLOADS=os.path.join(scr, "uploads"), STMT_VENV_PYTHON=sys.executable)
        os.environ.pop("PACKS_TODAY", None)
        dbp = os.path.join(scr, "finance.db")
        P = load(new, "packs.py", "packs_new")
        con = dbf(dbp)
        P.ensure(con)
        for d in ("CREATE TABLE IF NOT EXISTS clinic_day_revenue (business_date TEXT, revenue_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS app_setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)"):
            con.execute(d)
        con.commit()
        D = dt.date

        # ---- 1 the road
        r0 = P.statement_road(con, today=D(2026, 10, 3))
        check("1 an empty shelf says so, as a note", r0["state"] == "info" and "yet" in r0["text"], r0)
        add_file(con, "w-old-bank", "sept_cycle.pdf", "bank", "2026-09-12T05:40:11")
        r1 = P.statement_road(con, today=D(2026, 10, 3))
        check("1 the 3rd, nothing fetched this month, cells empty -> WARN", r1["state"] == "warn" and r1["this_month"] == 0 and r1["missing"] > 0, r1)
        check("1 the warning names the last arrival, the month and the relay",
              "12-Sep-2026" in r1["text"] and "21 days ago" in r1["text"] and "September 2026" in r1["text"] and "this month" in r1["text"]
              and "still awaited" in r1["text"] and "Janitor" in r1["hint"] and "05:40 and 07:30" in r1["hint"], r1)
        r2 = P.statement_road(con, today=D(2026, 10, 2))
        check("1 the 2nd is before the window -> quiet", r2["state"] == "ok", r2)
        add_file(con, "w-card-oct", "card_oct.pdf", "cards", "2026-10-03T05:40:12")
        r3 = P.statement_road(con, today=D(2026, 10, 5))
        check("1 a CARD file is not a bank arrival -> still WARN on the 5th", r3["state"] == "warn" and r3["this_month"] == 0, r3)
        add_file(con, "w-bank-oct", "e_statement.pdf", "bank", "2026-10-04T09:31:02")
        r4 = P.statement_road(con, today=D(2026, 10, 4))
        check("1 a bank file today -> quiet, and says 'today' and the count", r4["state"] == "ok" and "today" in r4["text"] and "1 this month" in r4["text"], r4)
        r5 = P.statement_road(con, today=D(2026, 10, 8))
        check("1 four quiet days inside the window with cells empty -> a grey note, never amber",
              r5["state"] == "info" and "for 4 days" in r5["text"] and "04-Oct-2026" in r5["text"] and "still missing" in r5["text"], r5)
        check("1 the note names what is missing (four at most)", "NK Pathology" in r5["text"] and r5["text"].count(",") <= 4, r5)
        r6 = P.statement_road(con, today=D(2026, 10, 6))
        check("1 two quiet days are not yet said", r6["state"] == "ok", r6)
        r7b = P.statement_road(con, today=D(2026, 10, 10))
        check("1 the 10th is still inside the window -> the grey note", r7b["state"] == "info" and "for 6 days" in r7b["text"], r7b)
        r7 = P.statement_road(con, today=D(2026, 10, 11))
        check("1 after the 10th, with something arrived this month -> quiet", r7["state"] == "ok" and r7["this_month"] == 1, r7)
        con.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.road_quiet_days','5')")
        con.commit()
        check("1 the setting packs.road_quiet_days moves the note (5 -> the 8th is quiet)", P.statement_road(con, today=D(2026, 10, 8))["state"] == "ok")
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.road_quiet_days','not a number')")
        con.commit()
        check("1 a setting that is not a number falls back to the default", P.statement_road(con, today=D(2026, 10, 8))["state"] == "info")
        con.execute("DELETE FROM setting"); con.execute("DELETE FROM stmt_file WHERE drive_id='w-bank-oct'"); con.commit()
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.road_from_day','6')"); con.commit()
        check("1 the setting packs.road_from_day moves the window (6 -> the 5th is quiet)", P.statement_road(con, today=D(2026, 10, 5))["state"] == "ok")
        con.execute("DELETE FROM setting"); con.commit()
        check("1 ... and without it the 5th is WARN again", P.statement_road(con, today=D(2026, 10, 5))["state"] == "warn")
        r9 = P.statement_road(con, today=D(2026, 10, 20))
        check("1 nothing at all this month stays AMBER after the 10th (waiting never turns it green)", r9["state"] == "warn" and "this month" in r9["text"]
              and "38 days ago" in r9["text"], r9)
        con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('packs.road_quiet_days','0')"); con.commit()
        check("1 a quiet-days setting of 0 is read as 1 (never 'for 0 days')", "for 0 days" not in P.statement_road(con, today=D(2026, 10, 5))["text"])
        con.execute("DELETE FROM setting"); con.commit()
        n = 0
        for s in con.execute("SELECT id, kind FROM stmt_slot").fetchall():
            if s["kind"] != "card":
                n += 1
                add_file(con, "w-full-%d" % s["id"], "sept_%d.pdf" % s["id"], "bank", "2026-09-30T05:40:00", slot_id=s["id"],
                         pf="2026-09-01", pt="2026-09-30", read_status="read")
        r8 = P.statement_road(con, today=D(2026, 10, 5))
        check("1 every bank cell of the month filled (%d) -> quiet whatever the dates" % n, n >= 6 and r8["state"] == "ok" and r8["missing"] == 0, r8)
        got = []
        P.statement_road_row(lambda *x: got.append(x), con)
        check("1 the health row: key, label, the same state (ok, every cell filled), the text, the hint", len(got) == 1 and got[0][0] == "stmtroad"
              and got[0][1] == "Bank statements reaching Drive" and got[0][2] == "ok" and got[0][3] == P.statement_road(con)["text"] and len(got[0]) == 5, got)
        conj = dbf(os.path.join(scr, "jan.db"))
        P.ensure(conj)
        add_file(conj, "j-old", "dec_cycle.pdf", "bank", "2026-12-20T05:40:00")
        rj = P.statement_road(conj, today=D(2027, 1, 5))
        check("1 January looks back at December: WARN names December 2026", rj["state"] == "warn" and "December 2026" in rj["text"] and rj["month"] == "2026-12", rj)
        check("1 ... and the 2nd of January is before the window", P.statement_road(conj, today=D(2027, 1, 2))["state"] == "ok")
        npart = 0
        for s in conj.execute("SELECT id, kind FROM stmt_slot").fetchall():
            if s["kind"] != "card":
                npart += 1
                add_file(conj, "j-part-%d" % s["id"], "cycle_%d.pdf" % s["id"], "bank", "2026-12-11T05:40:00", slot_id=s["id"],
                         pf="2026-11-11", pt="2026-12-10", read_status="read")
        rp = P.statement_road(conj, today=D(2027, 1, 5))
        check("1 every cell only PARTIAL and nothing this month -> still WARN (a partial cell is still awaited)",
              rp["state"] == "warn" and rp["missing"] == 0 and rp["waiting"] == npart and npart >= 6, rp)
        add_file(conj, "j-jan", "jan_first.pdf", "bank", "2027-01-04T07:30:00")
        rq = P.statement_road(conj, today=D(2027, 1, 8))
        check("1 partial cells alone never make the grey note (a cycle's second half is due after the 10th)", rq["state"] == "ok" and rq["waiting"] == npart, rq)
        conj.close()
        dead = dbf(os.path.join(scr, "dead.db")); dead.close()
        rd = P.statement_road(dead, today=D(2026, 10, 5))
        check("1 a closed database is answered, never raised", rd["state"] == "info" and "could not be read" in rd["text"], rd)
        got2 = []
        P.statement_road_row(lambda *x: got2.append(x), dead)
        check("1 ... and the health row still arrives", len(got2) == 1 and got2[0][2] == "info")

        # ---- 2 the text door
        from flask import Flask
        t1 = os.path.join(inbox, "fetched.txt"); t2 = os.path.join(inbox, "opened.txt"); t3 = os.path.join(inbox, "locked.pdf")
        open(t1, "w", encoding="utf-8").write("STATEMENT AS FETCHED\nline two\n")
        open(t2, "w", encoding="utf-8").write("THE UNLOCKED COPY\nPeriod line\nrow\n")
        open(t3, "wb").write(b"%PDF-1.4 not a real one")
        f1 = add_file(con, "w-text-1", "a.txt", "bank", "2026-10-04T09:31:00", local=t1)
        f2 = add_file(con, "w-text-2", "b.pdf", "bank", "2026-10-04T09:31:00", local=t3, unlocked=t2, locked=1, read_status="refused: made up")
        app = Flask("walk476_owner")
        P.init(app, lambda: dbf(dbp), lambda *roles, **kw: ({"user": "wmanoj", "role": "checker", "roles": ["checker"]}, None), unit="packs")
        c = app.test_client()
        r = c.get("/finance/packs/api/text/%d" % f1); j = r.get_json() or {}
        check("2 the owner gets the text of the file as fetched", r.status_code == 200 and j.get("ok") and j["text"] == "STATEMENT AS FETCHED\nline two\n"
              and j["source"] == "the file as fetched" and j["chars"] == 30 and j["lines"] == 2 and j["on_disk"] is True, j)
        check("2 the answer is never cached", r.headers.get("Cache-Control") == "no-store", dict(r.headers))
        r = c.get("/finance/packs/api/text/%d" % f2); j = r.get_json() or {}
        check("2 a locked file is answered from its unlocked copy", r.status_code == 200 and j.get("ok") and j["text"].startswith("THE UNLOCKED COPY")
              and j["source"] == "the unlocked copy" and j["locked"] is True and j["read_status"] == "refused: made up", j)
        r = c.get("/finance/packs/api/text/999999")
        check("2 an unknown id is 404", r.status_code == 404 and (r.get_json() or {}).get("error") == "not_on_shelf")
        if shutil.which("pdftotext"):
            t4 = os.path.join(inbox, "real.pdf")
            open(t4, "wb").write(tiny_pdf("HELLO S476 PERIOD"))
            f4 = add_file(con, "w-text-4", "real.pdf", "bank", "2026-10-04T09:31:00", local=t4)
            j = c.get("/finance/packs/api/text/%d" % f4).get_json() or {}
            check("2 a real PDF comes back as pdftotext reads it", j.get("ok") and "HELLO S476 PERIOD" in j.get("text", "") and j["still_locked"] is False, j)
        else:
            print("  note: pdftotext is not on this machine -- the real-PDF check of the text door is skipped here (it runs on the box)")
        rs = c.get("/finance/packs/api/state?month=2026-09"); js = rs.get_json() or {}
        check("3 the state door carries 'road' with a state and a text", rs.status_code == 200 and js.get("ok") and isinstance(js.get("road"), dict)
              and js["road"].get("state") in ("ok", "info", "warn") and "text" in js["road"], str(js)[:300])
        app2 = Flask("walk476_staff")
        P2 = load(new, "packs.py", "packs_new2")
        P2.init(app2, lambda: dbf(dbp), lambda *roles, **kw: ((None, ("not permitted", 403)) if "maker" not in roles else ({"user": "wshavez", "roles": ["maker"]}, None)), unit="packs")
        r = app2.test_client().get("/finance/packs/api/text/%d" % f1)
        check("2 a staff login gets nothing from the text door", r.status_code == 403 and b"STATEMENT AS FETCHED" not in r.data, r.status_code)

        # ---- 3 the page
        html = open(os.path.join(new, "packs.html"), encoding="utf-8").read()
        for w in ('<div id="road"></div>', "roadLine(j.road);", "function roadLine(r){", "S476 (F-723)"):
            check("3 packs.html carries %r" % w, html.count(w) >= 1)
        check("3 the road's place sits between the flash line and the summary card",
              html.index('<div id="flash"></div>') < html.index('<div id="road"></div>') < html.index('id="topcard"'))
        check("3 packs.html lost nothing (every old line is still there, in order)",
              [ln for ln in html.split("\n") if ln in set(open(os.path.join(old, "packs.html"), encoding="utf-8").read().split("\n"))]
              == open(os.path.join(old, "packs.html"), encoding="utf-8").read().split("\n"))

        # ---- 4 the health hook
        fo = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read()
        fn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
        A = 'add("reception", "Reception PC", "info", "could not be read (%s)" % ex)\n'
        i = fo.index(A) + len(A)
        added = fn[i:len(fn) - (len(fo) - i)]
        check("4 before and after the insertion finance_app.py is the original byte for byte", fn[:i] == fo[:i] and fn[i + len(added):] == fo[i:])
        check("4 the insertion is one guarded call to packs.statement_road_row", added.count('sys.modules["packs"].statement_road_row(add, con)') == 1
              and added.count("try:") == 1 and added.count("except Exception as ex:") == 1 and added.count('add("stmtroad"') == 1 and added.count("\n") == 9, added)
        check("4 it sits before the 'parts that did not load' row", fn.index('sys.modules["packs"].statement_road_row') < fn.index("# ---- S425: PARTS OF THE FINANCE APP THAT DID NOT LOAD"))
        try:
            compile(fn, "finance_app.py", "exec"); cok = ""
        except SyntaxError as ex:
            cok = str(ex)
        check("4 finance_app.py compiles", cok == "", cok)
        con.close()

        # ---- 5 the backup
        B = load(new, "clinic_state_backup.py", "csb_new")
        O = load(old, "clinic_state_backup.py", "csb_old")
        check("5 the login store is in SRC_FILES exactly once, last", B.SRC_FILES.count("/root/portal/clinic_users.json") == 1 and B.SRC_FILES[-1] == "/root/portal/clinic_users.json")
        check("5 the earlier SRC_FILES entries are unchanged and in order", B.SRC_FILES[:-1] == O.SRC_FILES and B.SRC_DIRS == O.SRC_DIRS)
        check("5 SRC_TREES is the old two and the new two, in order",
              B.SRC_TREES == O.SRC_TREES + ["/root/finance/statements/packs/handover", "/root/finance/spine/orders"])
        bn = [os.path.basename(p) for p in B.SRC_FILES]
        lb = [os.path.basename(p.rstrip("/")) for p in B.SRC_DIRS + B.SRC_TREES]
        check("5 no SRC_FILES basename and no folder label collides", len(bn) == len(set(bn)) and len(lb) == len(set(lb)) and not (set(bn) & set(lb)), (bn, lb))
        check("5 clinic_users.json is not taken for a secret by the file's own patterns", not B.is_secret("clinic_users.json"))
        fx = os.path.join(scr, "fx"); users = os.path.join(fx, "portal", "clinic_users.json")
        ho = os.path.join(fx, "finance", "statements", "packs", "handover"); orders = os.path.join(fx, "finance", "spine", "orders")
        for d in (os.path.dirname(users), os.path.join(ho, "2026-09"), os.path.join(orders, "before_S470")):
            os.makedirs(d)
        open(users, "w").write(json.dumps({"epoch": 1, "users": {"walk": {"role": "checker"}}}))
        open(os.path.join(ho, "2026-09", "12_20261004T101500.jpg"), "wb").write(b"\xff\xd8\xff\xe0" + b"\x00" * 32 + b"\xff\xd9")
        open(os.path.join(ho, "2026-09", "13_20261004T101700.png"), "wb").write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 16)
        open(os.path.join(ho, "2026-09", "upload.tmp"), "wb").write(b"half")
        open(os.path.join(orders, "order_score_latest.json"), "w").write('{"score": 1}')
        open(os.path.join(orders, "before_S470", "order_2026-10-03.json"), "w").write('{"lines": []}')
        open(os.path.join(orders, "api_token_note.json"), "w").write('{"x": 1}')
        B.SRC_FILES = [users]; B.SRC_DIRS = []; B.SRC_TREES = [ho, orders, os.path.join(fx, "not_there")]
        B._gather_shape = lambda conf, shape_dir, g: None
        B._write_inventory = lambda dest_root, g: None
        B.log = lambda *x: None
        stage = os.path.join(scr, "stage"); os.makedirs(stage)
        g = B.gather({}, stage)
        dd = os.path.join(stage, "data")
        check("5 gather() took the login store as data/clinic_users.json, byte for byte",
              os.path.isfile(os.path.join(dd, "clinic_users.json")) and md5(os.path.join(dd, "clinic_users.json")) == md5(users))
        check("5 the photos came with their month folder", os.path.isfile(os.path.join(dd, "handover", "2026-09", "12_20261004T101500.jpg"))
              and os.path.isfile(os.path.join(dd, "handover", "2026-09", "13_20261004T101700.png")))
        check("5 a temp file in the photo folder is not taken", not os.path.exists(os.path.join(dd, "handover", "2026-09", "upload.tmp")))
        check("5 the order snapshots came at every depth", os.path.isfile(os.path.join(dd, "orders", "order_score_latest.json"))
              and os.path.isfile(os.path.join(dd, "orders", "before_S470", "order_2026-10-03.json")))
        check("5 a secret-named file is skipped and counted, never copied", not os.path.exists(os.path.join(dd, "orders", "api_token_note.json")) and g.secrets_skipped == 1, g.secrets_skipped)
        check("5 each tree is ONE source; the file is its own", g.sources_present == [users, ho, orders], g.sources_present)
        check("5 an absent tree is 'missing', not an error", g.sources_missing == [os.path.join(fx, "not_there")], g.sources_missing)
        check("5 nothing was read as a database", g.databases == [], g.databases)
        os.remove(os.path.join(orders, "before_S470", "order_2026-10-03.json"))
        stage2 = os.path.join(scr, "stage2"); os.makedirs(stage2)
        g2 = B.gather({}, stage2)
        check("5 a pruned snapshot changes no source (so it can never refuse the night)", g2.sources_present == g.sources_present)

        # ---- 6 SHOWN on the old files
        Po = load(old, "packs.py", "packs_old")
        check("6 SHOWN: the old packs.py has no statement_road and no text door", not hasattr(Po, "statement_road") and not hasattr(Po, "api_text")
              and "road" not in open(os.path.join(old, "packs.html"), encoding="utf-8").read().split("<script>")[0].split("</style>")[1])
        check("6 SHOWN: the old backup lists hold neither the login store nor the two trees", "/root/portal/clinic_users.json" not in O.SRC_FILES
              and not any("handover" in t or "spine/orders" in t for t in O.SRC_TREES + O.SRC_DIRS))
        check("6 SHOWN: the old finance_app.py has no stmtroad row", "stmtroad" not in fo)
        check("hermetic: the four live files untouched", [md5(p) for p in live] == before)
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S476 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


if __name__ == "__main__":
    main()
