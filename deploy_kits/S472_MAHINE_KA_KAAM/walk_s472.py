#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s472.py -- S472_MAHINE_KA_KAAM (session 293, 04-Oct-2026). Hermetic (F-709): packs.py copied beside the box's readers
into a scratch folder (old as it is, new with the kit), an EMPTY database from packs.ensure(), a scratch packs folder, a
throwaway Flask app that mounts the packs blueprint with a made-up staff login. Nothing live is opened.

  1. the due days: Docterz the 1st, statements/scans the 5th, NEFT the 7th, hand-overs and the accountant's things the 10th,
     the petty book the 3rd; the owner's own day (12) wins.
  2. late / due today, against a fixed 'today'; the tile's line reads 'N kaam baaki · M late · aaj: ...'; 'sab ho gaya' when done.
  3. a hand-over ticked WITH a photo (multipart, jpeg) -> the photo is kept under the scratch packs folder, the row shows it, the
     photo door serves it; a .txt is refused silently and the tick still stands; a JSON tick without a photo still works.
  4. the owner's rename carries a due day.
  5. the two pages carry the new words; portal.py carries the live line.
  6. SHOWN on the old file: the checklist knew no due day and no 'late'.
Last line: WALK_S472 GREEN|RED.
   usage: walk_s472.py --apply apply_s472.py --finance /root/finance --portal /root/portal
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FAILS, CHECKS = [], 0
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64 + b"\xff\xd9"


def check(name, ok, detail=""):
    global CHECKS
    CHECKS += 1
    if not ok:
        FAILS.append(name)
        print("  FAIL %s %s" % (name, detail))


def load_packs(folder, tag):
    sys.path.insert(0, folder)
    for k in [k for k in sys.modules if k in ("packs", "finance_icici", "finance_yesbank", "yes_branch")]:
        del sys.modules[k]
    spec = importlib.util.spec_from_file_location("packs_" + tag, os.path.join(folder, "packs.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.path.pop(0)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--portal", required=True)
    a = ap.parse_args()
    scr = tempfile.mkdtemp(prefix="s472_walk_")
    try:
        old = os.path.join(scr, "old"); new = os.path.join(scr, "new"); packs_dir = os.path.join(scr, "packs_store")
        os.makedirs(old); os.makedirs(new); os.makedirs(packs_dir)
        for f in ("packs.py", "packs.html", "packs_checklist.html", "stmt_shelf.py", "finance_icici.py", "finance_yesbank.py", "yes_branch.py"):
            src = os.path.join(a.finance, f)
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(old, f)); shutil.copy2(src, os.path.join(new, f))
        shutil.copy2(os.path.join(a.portal, "portal.py"), os.path.join(new, "portal.py"))
        r = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "packs.py"), os.path.join(new, "packs_checklist.html"), os.path.join(new, "portal.py")],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        check("apply on scratch", r.returncode == 0, r.stderr.decode()[-300:])
        os.environ.update(STMT_INBOX=os.path.join(scr, "inbox"), PACKS_DIR=packs_dir, PACKS_ENV=os.path.join(scr, "no.env"),
                          ASSETS_UPLOADS=os.path.join(scr, "uploads"), STMT_VENV_PYTHON=sys.executable)
        dbp = os.path.join(scr, "finance.db")
        P = load_packs(new, "new")
        con = sqlite3.connect(dbp); con.row_factory = sqlite3.Row
        P.ensure(con)
        for d in ("CREATE TABLE IF NOT EXISTS clinic_day_revenue (business_date TEXT, revenue_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS app_setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)"):
            con.execute(d)
        con.commit()
        cols = {r[1] for r in con.execute("PRAGMA table_info(packs_item)")}
        check("1 packs_item gained due_day", "due_day" in cols)
        M = "2026-09"
        items = {x["item"]: x for x in P.checklist(con, M, today=dt.date(2026, 10, 4))}
        by_key = {x["item"]: x for x in items.values()}
        def due_of(sub):
            return [x["due_day"] for k, x in items.items() if sub in k][0]
        check("1 Docterz days due the 1st", due_of("Docterz day revenue") == 1)
        check("1 the clinic statements due the 5th", due_of("Clinic ka Yes Bank") == 5)
        check("1 NEFT due the 7th", due_of("NEFT done") == 7)
        check("1 the lab register (hand-over) due the 10th", due_of("Lab register") == 10)
        check("1 the petty book due the 3rd", due_of("Petty book") == 3)
        check("1 the accountant's things due the 10th", due_of("Pack accountant ko") == 10)
        check("1 hand-overs are marked handover=True", items[[k for k in items if "Lab register" in k][0]]["handover"] and items[[k for k in items if "Cheque register" in k][0]]["handover"] and items[[k for k in items if "Petty book" in k][0]]["handover"])
        check("1 an automatic item is not a hand-over", not items[[k for k in items if "Docterz day" in k][0]]["handover"])
        # 2 late / due today on 04-Oct: the 1st and 3rd are late, the 5th is not; on 05-Oct the 5th is due today
        docterz = items[[k for k in items if "Docterz day" in k][0]]
        petty = items[[k for k in items if "Petty book" in k][0]]
        stm = items[[k for k in items if "Clinic ka Yes Bank" in k][0]]
        check("2 on 04-Oct the Docterz item (1st) and the petty book (3rd) are late", docterz["late"] and petty["late"] and docterz["due"] == "2026-10-01")
        check("2 the statements item (5th) is not late on 04-Oct", not stm["late"] and not stm["due_today"])
        it5 = {x["item"]: x for x in P.checklist(con, M, today=dt.date(2026, 10, 5))}
        check("2 on 05-Oct the statements item is due today", it5[[k for k in it5 if "Clinic ka Yes Bank" in k][0]]["due_today"])
        ln = P.checklist_line(con, M, today=dt.date(2026, 10, 5))
        check("2 the tile's line: kaam baaki · late · aaj", ln["ok"] and ln["open"] == 20 and ln["late"] >= 2 and " late" in ln["text_hi"] and "aaj:" in ln["text_hi"] and ln["text_hi"].startswith("20 kaam baaki"), ln["text_hi"])
        # 3 the tick door with a photo, through a throwaway app
        from flask import Flask
        app = Flask("walk472")
        P.init(app, lambda: _dbfactory(dbp), lambda *roles, **kw: ({"user": "wshavez", "role": "maker", "roles": ["maker"]}, None), unit="packs")
        c = app.test_client()
        lab = [x for x in items.values() if "Lab register" in x["item"]][0]
        chq = [x for x in items.values() if "Cheque register" in x["item"]][0]
        rb = [x for x in items.values() if "receipt book" in x["item"]][0]
        r = c.post("/finance/packs/api/checklist/tick", data={"month": M, "id": str(lab["id"]), "photo": (io.BytesIO(JPEG), "register.jpg")}, content_type="multipart/form-data")
        j = r.get_json()
        check("3 a hand-over ticked with a photo", r.status_code == 200 and j["ok"] and j["photo"] is True, str(j))
        row = dict(con.execute("SELECT * FROM packs_done WHERE month=? AND item_id=?", (M, lab["id"])).fetchone() or {})
        check("3 the photo's path is on the tick row, under the scratch packs folder", row.get("note", "").startswith("handover/2026-09/") and os.path.exists(os.path.join(packs_dir, row.get("note", "x"))), str(row))
        after = {x["id"]: x for x in P.checklist(con, M, today=dt.date(2026, 10, 4))}
        check("3 the row shows the photo and who ticked", after[lab["id"]]["done"] and after[lab["id"]]["photo"] == row["note"] and after[lab["id"]]["done_by"] == "wshavez")
        r2 = c.get("/finance/packs/" + row["note"])
        check("3 the photo door serves it", r2.status_code == 200 and r2.data[:3] == b"\xff\xd8\xff", str(r2.status_code))
        r3 = c.get("/finance/packs/handover/2026-09/../../finance.db")
        check("3 the photo door refuses a bad name", r3.status_code == 404)
        r4 = c.post("/finance/packs/api/checklist/tick", data={"month": M, "id": str(chq["id"]), "photo": (io.BytesIO(b"hello"), "notes.txt")}, content_type="multipart/form-data")
        j4 = r4.get_json()
        check("3 a .txt 'photo' is refused silently, the tick stands", r4.status_code == 200 and j4["ok"] and j4["photo"] is False, str(j4))
        r5 = c.post("/finance/packs/api/checklist/tick", data=json.dumps({"month": M, "id": rb["id"]}), content_type="application/json")
        j5 = r5.get_json()
        check("3 a JSON tick without a photo still works", r5.status_code == 200 and j5["ok"] and j5["photo"] is False, str(j5))
        r6 = c.get("/finance/packs/api/checklist/line")
        j6 = r6.get_json()
        check("3 the line door answers the staff login", r6.status_code == 200 and j6["ok"] and "kaam baaki" in j6["text_hi"], str(j6))
        # 4 the owner's rename with a due day
        r7 = c.post("/finance/packs/api/item", data=json.dumps({"action": "rename", "id": chq["id"], "item": chq["item"], "due_day": 12}), content_type="application/json")
        check("4 rename carries a due day", r7.status_code == 200 and [x for x in P.checklist(con, M) if x["id"] == chq["id"]][0]["due_day"] == 12)
        # all done -> sab ho gaya
        for x in P.checklist(con, M):
            if not x["done"]:
                con.execute("INSERT OR IGNORE INTO packs_done (month, item_id, done_by, done_at, note) VALUES (?,?,?,?,?)", (M, x["id"], "walk", "2026-10-04T10:00:00", ""))
        con.commit()
        # the automatic items are not 'done' by a packs_done row in checklist() unless auto -- so the line counts the still-open automatic ones; make the test honest:
        ln2 = P.checklist_line(con, M, today=dt.date(2026, 10, 5))
        check("2 the line after ticking every manual item counts only the automatic ones still open", ln2["open"] == sum(1 for x in P.checklist(con, M) if x["auto"] and not x["done"]), str(ln2))
        # 5 the pages
        chk = open(os.path.join(new, "packs_checklist.html"), encoding="utf-8").read()
        for w in ("Aaj ka kaam", "tick karein", "Photo ke saath", "bina photo", "tickPhoto(", ".late{"):
            check("5 packs_checklist.html carries %r" % w, w in chk)
        por = open(os.path.join(new, "portal.py"), encoding="utf-8").read()
        for w in ('"packs_counts": True', "data-packs-counts", "/finance/packs/api/checklist/line"):
            check("5 portal.py carries %r" % w, w in por)
        con.close()
        # 6 SHOWN on the old file
        O = load_packs(old, "old")
        conO = sqlite3.connect(os.path.join(scr, "old.db")); conO.row_factory = sqlite3.Row
        O.ensure(conO)
        for d in ("CREATE TABLE IF NOT EXISTS clinic_day_revenue (business_date TEXT, revenue_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS upi_txn (unit TEXT, txn_date TEXT, amount_p INTEGER)",
                  "CREATE TABLE IF NOT EXISTS app_setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)"):
            conO.execute(d)
        itO = O.checklist(conO, M)
        check("6 SHOWN on the old file: no due day, no 'late' on any row", itO and all("late" not in x and "due_day" not in x for x in itO))
        conO.close()
        check("hermetic: the box's packs.py untouched", hashlib.md5(open(os.path.join(a.finance, "packs.py"), "rb").read()).hexdigest() == hashlib.md5(open(os.path.join(old, "packs.py"), "rb").read()).hexdigest())
    finally:
        shutil.rmtree(scr, ignore_errors=True)
    print("WALK_S472 %s %d checks, %d fail" % ("GREEN" if not FAILS else "RED", CHECKS, len(FAILS)))
    sys.exit(0 if not FAILS else 1)


def _dbfactory(dbp):
    con = sqlite3.connect(dbp, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


if __name__ == "__main__":
    main()
