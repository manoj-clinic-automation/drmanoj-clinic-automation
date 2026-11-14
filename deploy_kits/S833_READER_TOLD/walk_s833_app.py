#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s833_app.py -- S833_READER_TOLD on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch folder
with the given claude_reader.py, clinic_papers.py and reader_watch.py (TO -- or the live files for the control, where reader_watch.py
is absent), on a COPY of a database (SQLite's backup API) -- or a fresh one the app makes itself. Made-up rows only ("WALK833", dated
2031); the reader's call to Anthropic is REPLACED (no call leaves the process); the watcher's message goes to a stub file; the estate's
ALL_OFF is pointed at a scratch path. The scratch folder is removed at the end; the database given is only read (copied).

    python3 -B walk_s833_app.py --live <the app folder> --files <folder holding the files to test> [--db <assets.db>] [--expect-red]
"""
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES, SRC = opt("--live", "/root/assetapp"), opt("--files"), opt("--db")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("claude_reader.py", "clinic_papers.py", "reader_watch.py")
PARTS = ("clinic_papers", "sorting_desk", "asset_machine", "stationery", "batteries", "xray_costs", "procroom")
GREEN_BOTH = ("A0", "C2")                                            # the app loads; a plain bill is still sent home by its supplier's history

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s833app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        for f in KIT_FILES:
            p = os.path.join(FILES, f)
            if os.path.isfile(p):
                shutil.copy(p, os.path.join(app, f))
            elif os.path.exists(os.path.join(app, f)):
                os.remove(os.path.join(app, f))
        db = os.path.join(work, "assets.db")
        if SRC:
            s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True)
            d = sqlite3.connect(db)
            s.backup(d)
            d.close()
            s.close()
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        env = dict(os.environ, ASSETS_DB=db, ASSETS_UPLOADS=os.path.join(work, "uploads"), SHARED_LIB_DIR=os.path.join(work, "noshared"),
                   SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"), SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1",
                   CLINIC_PORTAL_DIR=os.path.join(work, "noportal"), FINANCE_LOCAL_URL="http://127.0.0.1:9",
                   FINANCE_DB_FOR_SCANS=os.path.join(work, "nofinance.db"), READER_WATCH_STATE=os.path.join(work, "rw_state.json"),
                   READER_WATCH_STUB=os.path.join(work, "rw_sent.jsonl"), READER_WATCH_ALL_OFF=os.path.join(work, "_off", "ALL_OFF"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=300)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S833" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S833_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]   # never the kit's own copies
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:400]) if (d and not ok) else ""))


def txt(h):
    return re.sub(r"\s+", " ", re.sub("<[^>]+>", " ", h)).replace("&#34;", '"').replace("&#39;", "'").replace("&amp;", "&")


import asset_register as ar                                          # noqa: E402

mods = {m: sys.modules.get(m) for m in PARTS}
ck("A0 the real app loads with its seven parts mounted (%s)" % ", ".join(m for m, x in mods.items() if x is not None), lambda: all(mods.values()))
cr = sys.modules.get("claude_reader") or __import__("claude_reader")
cp = mods["clinic_papers"]
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
if not db.execute("SELECT 1 FROM users WHERE username='walk_own_s833'").fetchone():
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_s833','Walk owner','owner','x',1)")
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
own = ar.app.test_client()
with own.session_transaction() as ss:
    ss["uid"] = db.execute("SELECT id FROM users WHERE username='walk_own_s833'").fetchone()[0]
    ss["epoch"] = epoch
was = (db.execute("SELECT value FROM settings WHERE key='read.claude'").fetchone() or [None])[0]
pic = os.path.join(WORK, "walk833.jpg")
open(pic, "wb").write(b"\xff\xd8\xff\xe0WALK833" + b"\x00" * 64)


def refuse(message):
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
    db.commit()
    cr._post = lambda body, key: (401, {"type": "error", "error": {"type": "authentication_error", "message": message}}, "")
    cr.read(pic, None, dbp)
    return (db.execute("SELECT value FROM settings WHERE key='read.claude'").fetchone() or [""])[0]


s1 = refuse("Your API key has expired. Please create a new key.")
adm = txt(own.get("/admin").get_data(as_text=True))
ck("R1 a refusal that says the key EXPIRED is named so: the reader stops with “the key has expired”, and his admin card reads “STOPPED — the key has expired”",
   lambda: s1 == "stopped:the key has expired" and "STOPPED — the key has expired" in adm, lambda: (s1, re.findall(r"STOPPED[^.]{0,60}", adm)[:2]))
s2 = refuse("invalid x-api-key")
ck("R2 any other refusal of the key is named as refused — expired or revoked (never only “refused”)",
   lambda: s2 == "stopped:the key was refused (expired or revoked)", lambda: s2)
# the watcher: what it would tell, once per stop; and the reader back on
rw = None
try:
    import reader_watch as rw                                        # noqa: E402
except ImportError:
    pass
SENT = os.environ["READER_WATCH_STUB"]


def sent():
    try:
        return [json.loads(l) for l in open(SENT, encoding="utf-8")]
    except OSError:
        return []


def dbmd5():
    return hashlib.md5(open(dbp, "rb").read()).hexdigest()


m0 = dbmd5()
t1 = rw.tick() if rw else "absent"
t2 = rw.tick() if rw else "absent"
s_ = sent()
ck("W1 a stopped reader is TOLD to him at once: one message “Scan app · paper reader STOPPED” naming the refused key and that scans wait; "
   "the next run says nothing more (once per stop); the watcher never writes the database",
   lambda: len(s_) == 1 and s_[0]["title"] == "Scan app · paper reader STOPPED" and "REFUSED -- it has expired or been revoked" in s_[0]["body"]
   and "Scans wait unread" in s_[0]["body"] and s_[0]["to"] == "manoj" and t2.endswith("nothing to say") and dbmd5() == m0, lambda: (t1, t2, s_))
refuse("Your API key has expired.")
t3 = rw.tick() if rw else "absent"
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")
db.commit()
t4 = rw.tick() if rw else "absent"
t5 = rw.tick() if rw else "absent"
s_ = sent()
ck("W2 a stop of other words is told again (now: EXPIRED, a new key needed); the reader on again is told once — “reading again” — and then nothing",
   lambda: len(s_) == 3 and "EXPIRED -- a new key (never expiring) is needed" in s_[1]["body"] and s_[2]["title"] == "Scan app · paper reader reading again"
   and t5.endswith("nothing to say"), lambda: (t3, t4, t5, [x["title"] for x in s_]))
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
db.commit()
t6 = rw.tick() if rw else "absent"
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','stopped:the credit has run out')")
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('reader_watch.on','off')")
db.commit()
t7 = rw.tick() if rw else "absent"
db.execute("DELETE FROM settings WHERE key='reader_watch.on'")
db.commit()
os.environ.pop("READER_WATCH_STUB")
t8 = rw.tick() if rw else "absent"
st8 = rw.load() if rw else {}
os.environ["READER_WATCH_STUB"] = SENT
ck("W3 his own OFF tap is never announced; the watcher's own switch (reader_watch.on = off) silences it; on a database that is not the live one, "
   "with no stub, NOTHING is sent and nothing is marked told (it tries again next run)",
   lambda: t6.endswith("nothing to say") and t7 == "off (reader_watch.on = off)" and "not the live database -- nothing sent" in t8
   and st8.get("told") == "on" and len(sent()) == 3, lambda: (t6, t7, t8, st8))
os.makedirs(os.path.dirname(os.environ["READER_WATCH_ALL_OFF"]), exist_ok=True)
open(os.environ["READER_WATCH_ALL_OFF"], "w").close()
t9 = rw.tick() if rw else "absent"
os.remove(os.environ["READER_WATCH_ALL_OFF"])
ck("W4 the estate's ALL_OFF stops it", lambda: t9 == "off (the estate's ALL_OFF)", lambda: t9)
db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude',?)", (was or "on",)) if was else db.execute("DELETE FROM settings WHERE key='read.claude'")
db.commit()
# F-1194: a dealer's summary is never moved by its supplier's history -- the start-up pass included


def mk(tag, lane, created, **cols):
    vals = dict(kind="Pharmacy", vendor="WALK833 PHARMA DISTRIBUTORS", stamp_no="Z-2031-" + tag, status="draft", lane=lane, created_at=created,
                submitted_at=created[:16], submitted_by="Walk", doc_kind="bill", bill_date=created[:10], ocr_status="read")
    vals.update(cols)
    return db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid


for k in range(3):
    mk("H%d" % k, "pharmacy", "2031-04-0%d 05:00:00" % (k + 1))
lane = lambda i: db.execute("SELECT lane FROM bills WHERE id=?", (i,)).fetchone()[0]    # noqa: E731
raw = getattr(cp.auto_home, "__wrapped__", cp.auto_home)              # the module's own rule, under S754's guard
BIL = mk("B1", "clinic", "2031-05-03 05:00:00")
db.commit()
d0 = raw(db, BIL)                                                     # a plain bill: its supplier's history sends it to the pharmacy lane
SUM = mk("S1", "clinic", "2031-05-01 05:00:00", kind="Summary", doc_kind="summary")
db.commit()
d1 = raw(db, SUM)
db.execute("UPDATE bills SET status='rejected' WHERE id=?", (SUM,))    # out of the history for the next one
SUM2 = mk("S2", "clinic", "2031-05-02 05:00:00", kind="Summary", doc_kind="summary")
db.commit()
orig = cp.auto_home
cp.auto_home = raw                                                    # the start-up pass as it runs at mount: before S754's guard
try:
    cp.heal_auto(db)
finally:
    cp.auto_home = orig
db.commit()
ck("C1 a dealer's summary on the clinic lane, its supplier's three earlier papers all on the pharmacy lane: the module's own rule moves it "
   "NOWHERE, and neither does the start-up pass (heal_auto, which runs before S754's guard is in place)",
   lambda: d1 == [] and lane(SUM) == "clinic" and lane(SUM2) == "clinic", lambda: (d1, lane(SUM), lane(SUM2)))
ck("C2 the rule itself is intact: a plain bill of the same supplier is sent to the pharmacy lane by that history", lambda: lane(BIL) == "pharmacy",
   lambda: lane(BIL))
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S833 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE (every new check red; the app and the rule itself green)" if not bad_
                                                   else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S833 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
