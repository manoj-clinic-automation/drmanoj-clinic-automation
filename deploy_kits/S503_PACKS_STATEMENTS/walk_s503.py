"""walk_s503.py -- S503_PACKS_STATEMENTS, session 304 (parent), 10-Oct-2026. The walk the installer runs on the box BEFORE placing.

On a SCRATCH copy of finance.db (sqlite backup API) and a scratch folder holding /root/finance's programs (the kit's four
over them, unless --control): process_inbox() as the 05:40 cron runs it, then the packs page's own routes through Flask's
test client, signed in as the doctor. Nothing live is written: the database, the inbox for opened copies, the pack folder
and the mail stub are all under the scratch folder. The SAME walk on the live programs (--control) must end RED.

GREEN needs: every Yes Bank file refused before for the layout ('does not print Period') is read now; no other file
becomes refused; the page answers 200 and carries its set-aside button; the state names every closed locked file;
set-aside on one takes it out of the count and put-back returns it. Prints counts and words only -- never a number of an
account in full, never a password, never an amount of a line.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

KIT_FILES = ("packs.py", "packs.html", "stmt_shelf.py", "yes_monthly.py")
ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="/root/wa/venv/bin/python3")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()

scr = tempfile.mkdtemp(prefix="s503_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".html", ".json")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))                       # the live programs, their times kept
if not a.control:
    for n in KIT_FILES:
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))   # the kit's, new times (as a placed file has)
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
os.environ.update(FINANCE_DB=db, STMT_INBOX=os.path.join(scr, "inbox"), PACKS_DIR=os.path.join(scr, "packs"),
                  PACKS_HANDOVER_DIR=os.path.join(scr, "handover"), PACKS_MAIL_STUB=os.path.join(scr, "mail"), STMT_VENV_PYTHON=a.venv,
                  FINANCE_DIR=fin)
for d in ("inbox", "packs", "handover", "mail"):
    os.makedirs(os.path.join(scr, d), exist_ok=True)
sys.path.insert(0, fin)
os.chdir(fin)
red = []
try:
    import packs                                                   # noqa: E402
    con = sqlite3.connect(db, timeout=60)
    con.row_factory = sqlite3.Row
    before = {r["id"]: (r["read_status"] or "") for r in con.execute("SELECT id, read_status FROM stmt_file")}
    lay = [i for i, s in before.items() if s.startswith("refused") and "Period" in s]
    res = packs.process_inbox(con)
    after = {r["id"]: (r["read_status"] or "") for r in con.execute("SELECT id, read_status FROM stmt_file")}
    still = [i for i in lay if after.get(i, "").startswith("refused")]
    newref = [i for i, s in after.items() if s.startswith("refused") and not before.get(i, "").startswith("refused")]
    print("  pass process_inbox: %s" % ({k: res[k] for k in ("placed", "read", "refused", "unlocked")},))
    print("  the files refused for the layout before: %d . read now: %d . still refused: %d . newly refused: %d"
          % (len(lay), len(lay) - len(still), len(still), len(newref)))
    if still:
        red.append("%d file(s) still refused for the layout: %s" % (len(still), ", ".join(str(x) for x in still)))
    if newref:
        red.append("%d file(s) newly refused: %s" % (len(newref), ", ".join(str(x) for x in newref)))
    from flask import Flask                                        # noqa: E402

    def _g():
        c = sqlite3.connect(db, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    app = Flask("walk_s503")
    packs.init(app, _g, lambda *x, **k: None)
    packs._owner = lambda: (dict(username="manoj", role="doctor", roles=["doctor"]), None)
    cl = app.test_client()
    st = cl.get("/finance/packs/api/state")
    j = st.get_json(silent=True) or {}
    sec = j.get("secrets") or {}
    if st.status_code != 200:
        red.append("the state answered %d" % st.status_code)
    pg = cl.get("/finance/packs")
    if pg.status_code != 200 or b"setAside(" not in pg.data:
        red.append("the page answered %d%s" % (pg.status_code, "" if b"setAside(" in pg.data else " without its set-aside button"))
    if "locked_files" not in sec:
        red.append("the state does not name the locked files")
    else:
        lf, sa = sec["locked_files"], sec.get("set_aside") or []
        print("  pass the state: month %s . %d cells . %d locked file(s) named . %d set aside . %d password box(es)"
              % (j.get("month"), len(j.get("cells") or []), len(lf), len(sa), len(sec.get("banks") or [])))
        for c in j.get("cells") or []:
            print("     %-48s %s%s" % ((c.get("label") or "")[:48], c.get("state") or "", (" . also on the shelf: %d" % len(c["copies"])) if c.get("copies") else ""))
        if lf:
            fid = lf[0]["id"]
            r1 = cl.post("/finance/packs/api/set-aside", json=dict(file=fid, why="walk"))
            s1 = (cl.get("/finance/packs/api/state").get_json() or {}).get("secrets") or {}
            r2 = cl.post("/finance/packs/api/set-aside", json=dict(file=fid, back=True))
            s2 = (cl.get("/finance/packs/api/state").get_json() or {}).get("secrets") or {}
            ok = (r1.status_code == 200 and r2.status_code == 200 and len(s1.get("locked_files", [])) == len(lf) - 1
                  and len(s2.get("locked_files", [])) == len(lf))
            print("  pass set aside / put back on file %d: %s" % (fid, "the count went %d -> %d -> %d" % (len(lf), len(s1.get("locked_files", [])), len(s2.get("locked_files", [])))))
            if not ok:
                red.append("set aside / put back did not move the count")
        r3 = cl.post("/finance/packs/api/set-aside", json=dict(file=0))
        if r3.status_code != 400:
            red.append("a bad set-aside answered %d" % r3.status_code)
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S503 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
