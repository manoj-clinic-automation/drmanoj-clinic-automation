#!/usr/bin/env python3
"""walk_s706.py -- S706 on a MADE-UP root (no real data, no phone): a copy of the bundle's /root/finance code with the kit's files over it,
a made-up spine.db (the spine's own schema) and a made-up finance.db.  Messages go to OWNER_NOTICE_STUB.
    python3 -B walk_s706.py <finance code dir to test> <spine_build.py for the schema>
CONTROL: run it on the unchanged bundle code -- every S706 check must go red."""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

CODE, BUILD = sys.argv[1], sys.argv[2]
ok = bad = 0


def check(name, cond):
    global ok, bad
    print(("  ok   " if cond else "  RED  ") + name)
    ok += bool(cond)
    bad += (not cond)


def spine_db(path, stage=1):
    src = open(BUILD).read()
    i = src.index("CREATE TABLE sp_meta")
    con = sqlite3.connect(path)
    con.executescript(src[i:src.index('"""', i)])
    days = ["2026-10-20", "2026-10-21", "2026-10-23", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28", "2026-10-30",
            "2026-10-31", "2026-11-02", "2026-11-04"] + (["2026-11-05"] if stage >= 2 else []) + (["2026-11-06"] if stage >= 3 else [])
    built = "2026-11-0%dT09:50:00+05:30" % (4 + stage)
    con.executemany("INSERT INTO sp_meta VALUES (?,?)", [("built", built), ("checkable", ""), ("pending", "")])
    # the sale exports cover every day but Sunday 1-Nov (its export is late) -- the holiday 22-Oct has no bill but IS covered (S1)
    for md, a_, b_ in (("s1", "2026-09-20", "2026-10-21"), ("s2", "2026-10-22", "2026-10-31"), ("s3", "2026-11-02", "2026-11-07")):
        con.execute("INSERT INTO sp_export (md5, family, date_from, date_to, ok) VALUES (?,?,?,?,1)", (md, "SALE_BILLWISE", a_, b_))
    con.execute("INSERT INTO sp_export (md5, family, date_from, date_to, ok) VALUES ('a','PURCHASE_BILLWISE','2026-09-20','2026-11-02',1)")
    con.execute("INSERT INTO sp_export (md5, family, date_from, date_to, ok) VALUES ('b','PURCHASE_ITEMWISE','2026-09-20','2026-11-02',1)")
    con.execute("INSERT INTO sp_export (md5, family, date_from, date_to, ok) VALUES ('x','SALE_BILLWISE','2026-11-01','2026-11-01',0)")
    items = {
        # name: (opening, {day: marg}, [(day, kind, units)])
        "CARTILOX SACHET": (3, {d: (3 if d < "2026-10-25" else 0) for d in days}, []),
        "DELIVERY TAB": (50, {d: (50 if d < "2026-11-04" else 150) for d in days}, [("2026-11-01", "PURCHASE", 100)]),
        "VFER 500": (35, {d: (35 if d < "2026-10-28" else 0) for d in days}, []),
        "V FER 500": (0, {d: (0 if d < "2026-10-28" else 35) for d in days}, []),
        "NORTIMER TAB": (-9, {d: (-9 if d < "2026-10-25" else 81) for d in days}, []),
        "LATE RISE CAP": (10, {d: (10 if d < "2026-11-04" else 130) for d in days}, []),
        "VOUCHER GEL": (8, {d: (8 if d < "2026-10-26" else 5) for d in days}, []),
        "BLIP SYP": (6, {d: (4 if d == "2026-10-27" else 6) for d in days}, []),
        "SLOW DELIVERY": (20, {d: (20 if d < "2026-10-31" else 60) for d in days}, [("2026-10-26", "PURCHASE", 40)]),
        "KNEE IMMOBILIZER M TYNOR": (1, {d: 1 for d in days}, [("2026-10-24", "SALE", -1)]),
        "EXLAIN A": (12, {d: (12 if d < "2026-11-04" else 0) for d in days}, []),
        "NEXT DAY DROP": (9, {d: (9 if d < "2026-11-05" else 4) for d in days}, []),
        "NIGHT DROP": (7, {d: (7 if d < "2026-11-06" else 2) for d in days}, []),
        "EARLY CAPTURE": (50, {d: (50 if d < "2026-10-28" else 150 if d == "2026-10-28" else 145) for d in days},
                          [("2026-10-26", "PURCHASE", 100), ("2026-10-28", "SALE", -5)]),
        "RETURN GEL": (30, {d: (30 if d < "2026-10-30" else 20) for d in days}, [("2026-10-24", "PURCHASE_RETURN", -10)]),
        "ZETA 500": (12, {d: (12 if d < "2026-11-04" else 0) for d in days}, []),
        "Z ETA 500": (0, {d: (0 if d < "2026-11-04" else 12) for d in days}, []),
        "SUNDAY SOLD": (10, {d: (10 if d < "2026-11-02" else 7) for d in days}, []),
    }
    for name, (opn, marg, mv) in items.items():
        k = name[:20].strip()
        con.execute("INSERT INTO sp_item (k20, name, packing, last_seen) VALUES (?,?,?,?)", (k, name, "1*10", "2026-11-04"))
        con.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-10-01", "OPENING", opn, "op"))
        for d, kind, u in mv:
            con.execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, d, kind, u, "ref"))
        for d in days:
            if name in ("V FER 500", "Z ETA 500") and marg[d] == 0:
                continue                                          # a new name is absent before the rename
            con.execute("INSERT INTO sp_close VALUES (?,?,?,?)", (d, k, marg[d], "m"))
        if name in ("CARTILOX SACHET", "VFER 500", "NORTIMER TAB"):                # a partial print on 29-Oct (S4): three items only
            con.execute("INSERT INTO sp_close VALUES (?,?,?,?)", ("2026-10-29", k, marg["2026-10-28"] if name != "NORTIMER TAB" else 5, "p"))
    con.commit()
    con.close()


def finance_db(path):
    con = sqlite3.connect(path)
    con.executescript("""
    CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
    CREATE TABLE stock_voucher_line (id INTEGER PRIMARY KEY, count_id INT, round_no INT, kind TEXT, batch_no INT, item TEXT, change REAL);
    CREATE TABLE stock_voucher_entered (id INTEGER PRIMARY KEY, count_id INT, round_no INT, kind TEXT, batch_no INT, marg_voucher_no TEXT,
       entered_on TEXT, by_user TEXT, at TEXT);
    """)
    con.execute("INSERT INTO setting VALUES ('owner_notice.since','2026-11-01 00:00:00','')")
    con.execute("CREATE TABLE amir_day (day TEXT PRIMARY KEY, opened_at TEXT)")
    con.executemany("INSERT INTO amir_day VALUES (?, '')", [("2026-10-25",), ("2026-11-04",)])
    con.execute("INSERT INTO stock_voucher_line VALUES (1,1,1,'ISSUE',1,'VOUCHER GEL',-3)")
    con.execute("INSERT INTO stock_voucher_entered VALUES (1,1,1,'ISSUE',1,'77','26-10-2026','amir','2026-10-26T10:00:00')")
    con.commit()
    con.close()


with tempfile.TemporaryDirectory() as t:
    fin = os.path.join(t, "root", "finance")
    os.makedirs(os.path.join(fin, "spine"))
    for sub in ("", "spine"):                                     # the code only: *.py and *.json, never a database or the readings
        for f in os.listdir(os.path.join(CODE, sub)):
            src = os.path.join(CODE, sub, f)
            if os.path.isfile(src) and f.endswith((".py", ".json")):
                shutil.copy2(src, os.path.join(fin, sub, f))
    sdb, fdb, stub = os.path.join(fin, "spine", "spine.db"), os.path.join(fin, "finance.db"), os.path.join(t, "stub.jsonl")
    spine_db(sdb)
    finance_db(fdb)
    env = dict(os.environ, OWNER_NOTICE_STUB=stub, ORDER_PUSH_NONE="", FINANCE_OFF_DIR=os.path.join(t, "off"), SPINE_DB=sdb,
               OWNER_NOTICE_LOCK=os.path.join(t, "lock"))
    env.pop("ORDER_PUSH_NONE")

    def py(code):
        r = subprocess.run([sys.executable, "-B", "-c", code], cwd=fin, env=env, capture_output=True, text=True)
        return (r.stdout + r.stderr).strip()

    have = os.path.exists(os.path.join(fin, "marg_hand_change.py"))
    check("the kit's new file is in the code under test", have)
    r1 = py("import sqlite3,json,datetime as dt,marg_hand_change as H; c=sqlite3.connect(%r); print(json.dumps(H.refresh(c, %r, finance_db=%r, "
            "force=True, now=dt.datetime(2026,11,5,9,55,tzinfo=H.IST))))" % (fdb, sdb, fdb)) if have else ""
    rows = py("import sqlite3; c=sqlite3.connect(%r); print('\\n'.join('|'.join(str(x) for x in r) for r in c.execute("
              "'SELECT item, kind, day_from, day_to, marg_from, marg_to, shift, status FROM marg_hand_change ORDER BY item')))" % fdb)
    print("    refresh:", r1[:200])
    print("    rows:\n      " + rows.replace("\n", "\n      "))
    R = {l.split("|")[0]: l.split("|") for l in rows.splitlines() if "|" in l}
    check("a fall by hand: CARTILOX SACHET 3 -> 0 between 23-Oct and 25-Oct, shift -3, open",
          R.get("CARTILOX SACHET", [""] * 8)[1:] == ["hand", "2026-10-23", "2026-10-25", "3.0", "0.0", "-3.0", "open"])
    check("a rise by hand once the purchases cover it: NORTIMER -9 -> 81, +90",
          R.get("NORTIMER TAB", [""] * 8)[1:7] == ["hand", "2026-10-23", "2026-10-25", "-9.0", "81.0", "90.0"])
    check("a sale Marg did not take: KNEE IMMOBILIZER M +1 between 23-Oct and 25-Oct",
          R.get("KNEE IMMOBILIZER M T", [""] * 8)[1:4] == ["hand", "2026-10-23", "2026-10-25"] or
          R.get("KNEE IMMOBILIZER M TYNOR", [""] * 8)[1:4] == ["hand", "2026-10-23", "2026-10-25"])
    check("a rename in Marg is a pair of kind 'rename', not two hand changes",
          R.get("VFER 500", [""] * 8)[1] == "rename" and R.get("V FER 500", [""] * 8)[1] == "rename")
    check("HELD: a fall on an Amir day after the purchase reports' cover waits (EXLAIN A, 4-Nov: he keys returns)", "EXLAIN A" not in R)
    check("NOT listed: a purchase return Marg took in five days after its bill date (owed back)", "RETURN GEL" not in R)
    check("a rename after the purchase cover is still a rename, never a lone fall (ZETA 500 / Z ETA 500)",
          R.get("ZETA 500", [""] * 8)[1] == "rename" and R.get("Z ETA 500", [""] * 8)[1] == "rename")
    check("NOT judged: a closing whose window holds a day with no accepted sale export (Sunday 1-Nov)", "SUNDAY SOLD" not in R)
    check("a holiday with no bill does not stop the judging (22-Oct covered by its export; CARTILOX found)", "CARTILOX SACHET" in R)
    check("a partial print (29-Oct, three items) is skipped: no fall and rise around it", R.get("NORTIMER TAB", [""] * 8)[3] == "2026-10-25"
          and len([x for x in R.values() if x[3] in ("2026-10-29", "2026-10-30")]) == 0)
    check("NOT listed: a delivery keyed after the export (owed, then paid by Marg's catch-up)", "DELIVERY TAB" not in R)
    check("NOT listed: a rise after the purchase reports' cover (waits)", "LATE RISE CAP" not in R)
    check("NOT listed: a change Amir's filed voucher explains", "VOUCHER GEL" not in R)
    check("NOT listed: a step undone the next closing", "BLIP SYP" not in R)
    check("NOT listed: a closing printed before the day's sales ended (+5 after a late bill, -5 the next closing)", "EARLY CAPTURE" not in R)
    check("NOT listed: a delivery Marg took in only five closings later (owed, then paid)", "SLOW DELIVERY" not in R)
    # the history is never announced
    col = py("import sqlite3,datetime as dt,owner_notice as O; c=sqlite3.connect(%r); c.row_factory=sqlite3.Row; "
             "m,e=O.collect(c, dt.datetime(2026,11,5,10,0,tzinfo=O.IST)); print([x['key'] for x in m if x['key'].startswith('hand:')])" % fdb)
    check("the first fill (the history) is on the page but never announced", col.strip().endswith("[]"))
    # a new day: a new fall is found after the first fill -> told, with the item, the days and the quantities
    os.remove(sdb)
    spine_db(sdb, stage=2)
    r2 = py("import sqlite3,json,datetime as dt,marg_hand_change as H; c=sqlite3.connect(%r); print(json.dumps(H.refresh(c, %r, finance_db=%r, "
            "now=dt.datetime(2026,11,5,10,0,tzinfo=H.IST))))" % (fdb, sdb, fdb)) if have else ""
    print("    refresh 2:", r2[:200])
    night = py("import sqlite3,datetime as dt,owner_notice as O; c=sqlite3.connect(%r); c.row_factory=sqlite3.Row; "
               "m,e=O.collect(c, dt.datetime(2026,11,5,23,30,tzinfo=O.IST)); print([x['key'] for x in m if x['key'].startswith('hand:')])" % fdb)
    check("a finding is not told at night (after owner_notice.hand_to)", night.strip().endswith("[]"))
    py("import sqlite3; c=sqlite3.connect(%r); c.execute(\"UPDATE marg_hand_change SET status='explained' WHERE item='NEXT DAY DROP'\"); c.commit()" % fdb)
    gone = py("import sqlite3,datetime as dt,owner_notice as O; c=sqlite3.connect(%r); c.row_factory=sqlite3.Row; "
              "m,e=O.collect(c, dt.datetime(2026,11,5,10,3,tzinfo=O.IST)); print([x['key'] for x in m if x['key'].startswith('hand:')])" % fdb)
    check("a row explained before it is told is never told (B1)", gone.strip().endswith("[]"))
    py("import sqlite3; c=sqlite3.connect(%r); c.execute(\"UPDATE marg_hand_change SET status='open' WHERE item='NEXT DAY DROP'\"); c.commit()" % fdb)
    tk = py("import sqlite3,datetime as dt,json,owner_notice as O; c=sqlite3.connect(%r); print(json.dumps(O.tick(c, dt.datetime(2026,11,5,10,5,tzinfo=O.IST))))"
            % fdb)
    print("    tick:", tk[:220])
    msgs = [json.loads(l) for l in open(stub)] if os.path.exists(stub) else []
    hm = [m for m in msgs if m["key"].startswith("hand:")]
    print("    message:", json.dumps(hm, ensure_ascii=False)[:400])
    check("the morning it is found: one message naming the item, the days and the quantities shifted",
          len(hm) == 1 and "NEXT DAY DROP: 9 → 4 (-5), between 4-Nov and 5-Nov" in hm[0]["body"] and "1 item" in hm[0]["title"])
    check("the message leaves out the history", bool(hm) and "CARTILOX" not in hm[0]["body"])
    tk2 = py("import sqlite3,datetime as dt,json,owner_notice as O; c=sqlite3.connect(%r); print(json.dumps(O.tick(c, dt.datetime(2026,11,5,10,10,tzinfo=O.IST))))"
             % fdb)
    tk3 = py("import sqlite3,datetime as dt,json,owner_notice as O; c=sqlite3.connect(%r); print(json.dumps(O.tick(c, dt.datetime(2026,11,6,8,5,tzinfo=O.IST))))"
             % fdb)
    msgs2 = [json.loads(l) for l in open(stub)] if os.path.exists(stub) else []
    check("told once: a second tick, and the next morning's 08:00, send nothing new (R2's N1)",
          len([m for m in msgs2 if m["key"].startswith("hand:")]) == 1)
    os.remove(sdb)
    spine_db(sdb, stage=3)
    py("import sqlite3,datetime as dt,marg_hand_change as H; c=sqlite3.connect(%r); H.refresh(c, %r, finance_db=%r, now=dt.datetime(2026,11,6,22,30,tzinfo=H.IST))"
       % (fdb, sdb, fdb))
    for hh, mm, dd in ((22, 35, 6), (8, 5, 7), (8, 10, 7)):
        py("import sqlite3,datetime as dt,owner_notice as O; c=sqlite3.connect(%r); O.tick(c, dt.datetime(2026,11,%d,%d,%d,tzinfo=O.IST))" % (fdb, dd, hh, mm))
    msgs3 = [m for m in ([json.loads(l) for l in open(stub)] if os.path.exists(stub) else []) if m["key"].startswith("hand:")]
    print("    night:", json.dumps(msgs3[1:], ensure_ascii=False)[:300])
    check("found at night: held, then one 08:00 message with that row alone",
          len(msgs3) == 2 and msgs3[1]["key"] == "hand:2026-11-07 08:00 (overnight)" and "NIGHT DROP: 7 → 2 (-5)" in msgs3[1]["body"]
          and "NEXT DAY DROP" not in msgs3[1]["body"])
    url = py("import owner_notice as O; print(O._payload('hand:x','t','b').get('url'), O._payload('pair:x','t','b').get('url'))")
    check("the message opens the Expiry watch; the other messages still open the console", url.strip() == "/finance/sanjeevni/expiry /finance/console")
    # the page
    page = py("import sqlite3,datetime as dt,expiry_watch as X; c=sqlite3.connect(%r); c.row_factory=sqlite3.Row; "
              "print(X.owner_page(c, today=dt.date(2026,11,6)))" % fdb)
    top = page.split("<h1>", 1)[-1][:6000]
    check("the page: the section sits on top, under the title", '<details class="screen" id="hand"' in top and top.index('id="hand"') < 400)
    check("... collapsed (no 'open' on it)", '<details class="screen" id="hand" style' in page and '<details open class="screen" id="hand"' not in page)
    check("... with the red count of what is new", '<span class="count red">2 new</span>' in page)
    check("... the owner's own why for CARTILOX, and the remedy rule",
          "Changed by hand in Marg, 3 to 0 (24-25 Oct); no bill, sale or voucher." in page and "Count the shelf." in page)
    check("... the rename apart, not counted as open", "Renamed in Marg &mdash; no stock moved" in page)
    check("... no ten-digit run on the page", __import__("re").search(r"\d{10}", page) is None)
    s5 = py("import marg_hand_change as H; print(H.why_of(dict(k20='CARTILOX SACHET', item='CARTILOX SACHET', kind='hand', day_from='2026-11-05', "
            "day_to='2026-11-06', marg_from=2, marg_to=0, system_moved=0, shift=-2)))")
    check("the owner's 24-25 Oct note is not shown for a later change of the same item (S5)", s5.startswith("Marg went 2 to 0 between 5-Nov and 6-Nov"))
    bad_db = os.path.join(t, "novch.db")
    shutil.copy2(fdb, bad_db)
    py("import sqlite3; c=sqlite3.connect(%r); c.execute('DELETE FROM marg_hand_change'); c.execute('DROP TABLE stock_voucher_line'); "
       "c.execute(\"DELETE FROM setting WHERE key LIKE 'hand.%%'\"); c.commit()" % bad_db)
    b3 = py("import sqlite3,json,marg_hand_change as H; c=sqlite3.connect(%r); r=H.refresh(c, %r, finance_db=%r, force=True); "
            "print(r.get('ok'), c.execute('SELECT COUNT(*) FROM marg_hand_change').fetchone()[0])" % (bad_db, sdb, bad_db))
    check("vouchers on file but unreadable: the refresh stops and writes nothing (B3)", b3.strip().endswith("False 0"))
    ph = py("import owner_notice as O, inspect; print('clinic Wi-Fi' in inspect.getsource(O._part_phone))")
    check("the phone line says the clinic Wi-Fi is fine (the owner, 05-Nov)", ph.strip() == "True")
print("WALK S706: %d ok, %d red" % (ok, bad))
sys.exit(1 if bad else 0)
