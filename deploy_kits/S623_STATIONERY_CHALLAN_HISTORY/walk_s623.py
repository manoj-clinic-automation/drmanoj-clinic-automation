#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s623.py -- S623's walk on MADE-UP databases (no live row, no patient; the supplier is 'MADE-UP STATIONERS').

    python3 -B walk_s623.py --app <folder with stationery.py> [--kit <folder with history_s623.py>]

Each made-up database has the live SHAPE read on 22-Oct-2026 14:2x IST from the owner's desk (read only): the 13 items and their
units, the nine opening counts of 18-Oct, S585's seven history issues, the six Variety challans in Stationery & packaging with their
readings, and B-0013's two lines already matched (the ring file, the token of 100) dated before the counts. Prints one line per
check and 'WALK S623: n green, m red'; exit 0 only when every check is green AND the negative control is red where it must be.
"""
import datetime
import importlib.util
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def arg(n, d):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


APP = arg("--app", "/root/assetapp")
KITD = arg("--kit", os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP)
import stationery as st                                              # noqa: E402

spec = importlib.util.spec_from_file_location("history_s623", os.path.join(KITD, "history_s623.py"))
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

GREEN = RED = 0


def chk(label, ok, detail=""):
    global GREEN, RED
    if ok:
        GREEN += 1
    else:
        RED += 1
    print("%s %s%s" % ("GREEN" if ok else "RED  ", label, (" -- " + str(detail)) if (detail and not ok) else ""))


def ts(y, m, d, hh=12, mm=0):
    return datetime.datetime(y, m, d, hh, mm, tzinfo=IST).timestamp()


ITEMS = (("A4 paper (75 gsm)", "ream"), ("Cheque book folder (small clear bag)", "piece"), ("Clear bag (economy)", "piece"),
         ("Clear bag (premium)", "piece"), ("Copy — Classmate 72 pages (24 x 18 cm)", "piece"), ("File folder DC-217", "piece"),
         ("Register 104 pages", "piece"), ("Register 192 pages", "piece"), ("Register 72 pages", "piece"), ("Ring file RBU-400", "piece"),
         ("Small copy — Anmol 96 pages (24 x 18 cm)", "piece"), ("Token, plain", "packet of 100"), ("X-ray envelope 8.5 x 10.5", "piece"))
COUNTS = (("Register 192 pages", 12), ("Register 104 pages", 14), ("Register 72 pages", 6), ("Copy — Classmate 72 pages (24 x 18 cm)", 6),
          ("Ring file RBU-400", 1), ("Clear bag (economy)", 5), ("Clear bag (premium)", 3), ("Small copy — Anmol 96 pages (24 x 18 cm)", 4),
          ("Cheque book folder (small clear bag)", 2))
HIST = (("Register 72 pages", 6, "reception"), ("Register 104 pages", 6, "reception"), ("Register 192 pages", 3, "lab"),
        ("Register 104 pages", 6, "lab"), ("Copy — Classmate 72 pages (24 x 18 cm)", 6, "sanjeevni"))
# (id, stamp, scanned, reading lines (name, qty, unit, rate))
PAPERS = ((3, "B-0003", "2026-08-25 10:00:00", (("A4 Ream 75gsm", 1, "ream", None),)),
          (13, "B-0013", "2026-09-15 11:00:00", (("File DC-217", 1, "", 240), ("Ring File RBU-400", 1, "", 340), ("Ay lam N Bon 192", 3, "", None),
                                                 ("ITC Copy 72p", 6, "", 40), ("Copy Annl", 4, "", 40), ("Register 17x23 92p A4", 6, "", None),
                                                 ("Register 104 Annl A4", 12, "", None), ("Estimate Book NK Parkm", 10, "", None),
                                                 ("Token (R) Plain", 100, "", 120))),
          (109, "B-0109", "2026-10-02 10:00:00", (("Register 192 pg Board", 6, "", None), ("Register 104 pg", 2, "", None), ("My Clear Bag", 2, "", None))),
          (114, "B-0114", "2026-10-03 10:00:00", (("Folder DC-217", 2, "", None),)),
          (133, "B-0133", "2026-10-07 10:00:00", (("A4 Ream (Star)", 20, "ream", None),)),
          (163, "B-0163", "2026-10-14 10:00:00", (("Envp 8.5 x 10.5 B- X Ray", 500, "", None),)))


def build(path, tweak=None):
    """A made-up database of the live shape. tweak(con, ids) changes it for a variant before the step."""
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript("""
CREATE TABLE bills(id INTEGER PRIMARY KEY, kind TEXT NOT NULL DEFAULT 'Consumable', vendor TEXT, bill_no TEXT, bill_date TEXT, total_amount REAL,
  notes TEXT, source_stored TEXT, source_orig TEXT, created_by INTEGER, created_at TEXT NOT NULL DEFAULT (datetime('now')),
  stamp_no TEXT, status TEXT NOT NULL DEFAULT 'draft', lane TEXT, dup_of INTEGER, dup_flag TEXT, doc_kind TEXT, challan_state TEXT,
  challan_of INTEGER, pe_who TEXT, subgroup TEXT, page_of INTEGER, mixed INTEGER);
CREATE TABLE bill_items(id INTEGER PRIMARY KEY, bill_id INTEGER NOT NULL, item_name TEXT NOT NULL, pack_size TEXT, quantity REAL, rate REAL, amount REAL,
  make TEXT, model TEXT, serial_no TEXT, batch TEXT, expiry TEXT, hsn TEXT);
CREATE TABLE claude_reading(bill_id INTEGER PRIMARY KEY, at TEXT NOT NULL, model TEXT, ok INTEGER NOT NULL DEFAULT 0, doc_kind TEXT, data TEXT, error TEXT);
CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE desk_audit(id INTEGER PRIMARY KEY, at TEXT NOT NULL, who TEXT, action TEXT NOT NULL, detail TEXT);
""")
    st.ensure(con)
    ids = {}
    for n, u in ITEMS:
        ids[n] = con.execute("INSERT INTO stationery_item(name, unit, active, made_by, made_at) VALUES(?,?,1,'walk','2026-10-16 10:00:00')", (n, u)).lastrowid
    cts = ts(2026, 10, 18, 14, 50)
    for k, (n, c) in enumerate(COUNTS):
        con.execute("INSERT INTO stationery_count(item_id, counted, stock_before, diff, opening, day, ts, by_whom, at) VALUES(?,?,0,?,1,'2026-10-18',?,'Dr Manoj','x')",
                    (ids[n], c, c, cts + k))
    for n, q, pl in HIST:
        con.execute("INSERT INTO stationery_move(item_id, qty, place, day, ts, stock_before, by_whom, at) VALUES(?,?,?,'2026-10-18',?,NULL,?,'x')",
                    (ids[n], q, pl, cts - 1, st.HISTORY_BY))
    for bid, stamp, made, lines in PAPERS:
        con.execute("INSERT INTO bills(id, vendor, created_at, stamp_no, status, lane, doc_kind, challan_state, subgroup) VALUES(?,?,?,?,'draft','clinic','challan','awaiting','stationery')",
                    (bid, "MADE-UP STATIONERS", made, stamp))
        con.execute("INSERT INTO claude_reading(bill_id, at, ok, doc_kind, data) VALUES(?,?,1,'challan',?)",
                    (bid, made, json.dumps({"items": [{"name": a, "qty": q, "unit": u, "rate": r} for a, q, u, r in lines]})))
    # an unrelated stationery paper and a pharmacy paper: never touched
    con.execute("INSERT INTO bills(id, vendor, created_at, stamp_no, status, lane, doc_kind, subgroup) VALUES(500,'MADE-UP OTHER','2026-10-10 10:00:00','B-0500','draft','clinic','challan','stationery')")
    con.execute("INSERT INTO bills(id, vendor, created_at, stamp_no, status, lane, doc_kind) VALUES(501,'MADE-UP PHARMA','2026-10-10 10:00:00','B-0501','captured','pharmacy','bill')")
    early = ts(2026, 10, 18, 10, 0)                                  # B-0013's first desk save: before the counts (the live figures say so)
    for no, n, q, rate, name in ((2, "Ring file RBU-400", 1, 340, "Ring File RBU-400"), (9, "Token, plain", 100, 120, "Token (R) Plain")):
        con.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at) "
                    "VALUES(13,'2026-09-15 11:00:00',?,?,?,'',?,?,0,'2026-10-18',?,'Shavez','x')", (no, name, q, rate, ids[n], early))
    con.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts, by_whom, at) "
                "VALUES(500,'2026-10-10 10:00:00',1,'Other file',4,'',NULL,?,0,'2026-10-10',?,'Shavez','x')", (ids["File folder DC-217"], ts(2026, 10, 10)))
    if tweak:
        tweak(con, ids)
    con.commit()
    con.close()
    return ids


def book(path):
    c = sqlite3.connect(path)
    c.row_factory = sqlite3.Row
    names = {i["id"]: i["name"] for i in st.item_rows(c)}
    b = {names[k]: v["stock"] for k, v in st.stock_book(c).items()}
    c.close()
    return b


def live_set(path):
    c = sqlite3.connect(path)
    r = sorted(c.execute("SELECT bill_id, bill_created_at, line_no, name, qty, unit, rate, item_id, not_stock, day, ts FROM stationery_line WHERE voided_at=''"))
    c.close()
    return r


def run(fn, *a):
    buf = []
    rc = fn(*a, app=APP, out=buf.append)
    return rc, buf


def q(path, sql, *p):
    c = sqlite3.connect(path)
    r = c.execute(sql, p).fetchall()
    c.close()
    return r


if "--make-db" in sys.argv:                                          # the rehearsal's made-up database (rehearse_s623.sh)
    build(arg("--make-db", ""))
    print("made-up database written")
    sys.exit(0)

tmp = tempfile.mkdtemp(prefix="s623walk_")
try:
    MAIN = os.path.join(tmp, "main.db")
    build(MAIN)
    before = book(MAIN)
    rows0 = live_set(MAIN)
    # ---------------------------------------------------------------- the negative control: the FROM state must go red
    rc, buf = run(H.verify, MAIN)
    chk("C0 control: verify on the FROM state is RED (%d red)" % rc, rc >= 10, "\n".join(buf))
    # ---------------------------------------------------------------- the step
    rc, buf = run(H.apply, MAIN)
    chk("W1 the step returns 0", rc == 0, "\n".join(buf))
    after = book(MAIN)
    cnt = [n for n, _c in COUNTS]
    chk("W2 the nine counted stocks unchanged and equal to the counts (12, 14, 6, 6, 1, 5, 3, 4, 2)",
        all(abs(before[n] - after[n]) < 1e-9 and abs(after[n] - c) < 1e-9 for n, c in COUNTS), {n: (before[n], after[n]) for n in cnt})
    exp = {"A4 paper (75 gsm)": 21, "File folder DC-217": 3, "X-ray envelope 8.5 x 10.5": 500, "Token, plain": -99}
    chk("W3 the four uncounted items move by A4 +21, DC-217 +3, X-ray envelope +500, Token -99",
        all(abs(after[n] - before[n] - d) < 1e-9 for n, d in exp.items()), {n: (before[n], after[n]) for n in exp})
    chk("W3b their stock now: A4 21, DC-217 3 + the other paper's 4, envelope 500, Token 1",
        (after["A4 paper (75 gsm)"], after["File folder DC-217"], after["X-ray envelope 8.5 x 10.5"], after["Token, plain"]) == (21, 7, 500, 1))
    n_new = q(MAIN, "SELECT COUNT(*) FROM stationery_line WHERE by_whom=? AND voided_at=''", H.MARK)[0][0]
    n_void = q(MAIN, "SELECT COUNT(*) FROM stationery_line WHERE voided_by=?", H.MARK)[0][0]
    chk("W4 13 new lines + the ring file and the token re-written = 15 live S623 lines; 2 voided and kept", (n_new, n_void) == (15, 2), (n_new, n_void))
    chk("W5 the token line: one live row, 1 packet, rate 120; the old 100 kept voided",
        q(MAIN, "SELECT qty, rate FROM stationery_line WHERE bill_id=13 AND line_no=9 AND voided_at=''") == [(1.0, 120.0)] and
        q(MAIN, "SELECT qty FROM stationery_line WHERE bill_id=13 AND line_no=9 AND voided_by=?", H.MARK) == [(100.0,)])
    chk("W6 the Estimate Book line (B-0013 line 8) is not written", not q(MAIN, "SELECT 1 FROM stationery_line WHERE bill_id=13 AND line_no=8"))
    chk("W7 one day and one ts per paper (the challan date 12:00 IST)",
        all(len(q(MAIN, "SELECT DISTINCT day, ts FROM stationery_line WHERE bill_id=? AND voided_at=''", b)) == 1 for b in (3, 13, 109, 114, 133, 163)) and
        q(MAIN, "SELECT DISTINCT day FROM stationery_line WHERE bill_id=13 AND voided_at=''") == [("2026-09-15",)] and
        abs(q(MAIN, "SELECT DISTINCT ts FROM stationery_line WHERE bill_id=163 AND voided_at=''")[0][0] - ts(2026, 10, 14)) < 1e-6)
    chk("W8 each line's unit is its item's own (A4 ream, the rest piece, token packet of 100)",
        q(MAIN, "SELECT COUNT(*) FROM stationery_line l JOIN stationery_item i ON i.id=l.item_id WHERE l.by_whom=? AND l.voided_at='' AND l.unit<>i.unit AND l.line_no<>2 AND NOT (l.bill_id=13 AND l.line_no=9)", H.MARK)[0][0] == 0)
    chk("W9 the unrelated paper and the pharmacy paper untouched",
        q(MAIN, "SELECT qty, by_whom, voided_at FROM stationery_line WHERE bill_id=500") == [(4.0, "Shavez", "")] and not q(MAIN, "SELECT 1 FROM stationery_line WHERE bill_id=501"))
    rc, buf = run(H.verify, MAIN)
    chk("W10 verify after the step: all green", rc == 0, "\n".join(buf))
    c = sqlite3.connect(MAIN)
    c.row_factory = sqlite3.Row
    inv = st.inventory(c, "2026-10")
    c.close()
    rec = {r["name"]: r["recv"] for r in inv["rows"]}
    chk("W11 October's Received: Register 192 6, Register 104 2, Clear bag (premium) 2, DC-217 2+4, A4 20, envelope 500; ring file 0, token 0",
        (rec["Register 192 pages"], rec["Register 104 pages"], rec["Clear bag (premium)"], rec["File folder DC-217"], rec["A4 paper (75 gsm)"],
         rec["X-ray envelope 8.5 x 10.5"], rec["Ring file RBU-400"], rec["Token, plain"]) == (6, 2, 2, 6, 20, 500, 0, 0), rec)
    lr = {r["name"]: (r["last_rate"], r["last_stamp"]) for r in inv["rows"]}
    chk("W12 Last rate paid: DC-217 240 (B-0114), Clear bag (premium) 44 (B-0109), Token 120, Ring 340 (B-0013)",
        lr["File folder DC-217"] == (240.0, "B-0114") and lr["Clear bag (premium)"] == (44.0, "B-0109") and lr["Token, plain"] == (120.0, "B-0013")
        and lr["Ring file RBU-400"] == (340.0, "B-0013"), lr)
    # ---------------------------------------------------------------- a second run writes nothing
    s1 = live_set(MAIN)
    rc, buf = run(H.apply, MAIN)
    chk("W13 a second run: 'already done', nothing written", rc == 0 and live_set(MAIN) == s1 and "already done" in buf[0], buf)
    # ---------------------------------------------------------------- a desk re-save after S623 keeps the challan date (MIN over the paper)
    c = sqlite3.connect(MAIN)
    c.row_factory = sqlite3.Row
    b = c.execute("SELECT * FROM bills WHERE id=133").fetchone()
    pn = st.panel(c, b, H.reading(c, 133))
    posted = [{"no": l["no"], "name": l["name"], "qty": "19", "unit": l["unit"], "rate": l["rate"], "item": l["item"]} for l in pn["lines"]]
    st.save_lines(c, b, posted, "walk-person")
    c.commit()
    d = c.execute("SELECT day, ts, qty FROM stationery_line WHERE bill_id=133 AND voided_at=''").fetchall()
    c.close()
    chk("W14 a person's later desk re-save of B-0133 keeps its challan date (the paper's earliest)", [tuple(x) for x in d] == [("2026-10-07", ts(2026, 10, 7), 19.0)], d)
    # ---------------------------------------------------------------- the undo: B-0133 re-saved by a person is left; the rest restored exactly
    rc, buf = run(H.undo, MAIN)
    rest = [r for r in live_set(MAIN) if r[0] != 133]
    chk("W15 undo: every other paper back exactly as before S623 (B-0013's ring file and token of 100 return)",
        rc == 0 and rest == [r for r in rows0 if r[0] != 133], "\n".join(buf))
    chk("W16 undo leaves B-0133 (re-saved by a person) as it is", [r[4] for r in live_set(MAIN) if r[0] == 133] == [19.0])
    chk("W17 undo never deletes: the 14 S623 rows still live (15 less B-0133 re-saved by the person) kept, voided by 'undo S623'", q(MAIN, "SELECT COUNT(*) FROM stationery_line WHERE voided_by=?", H.UNDO_BY)[0][0] == 14)
    chk("W18 the key stays after undo (a re-install writes nothing)", bool(q(MAIN, "SELECT 1 FROM settings WHERE key=?", H.KEY)))
    rc, buf = run(H.apply, MAIN)
    chk("W19 after an undo the key reads 'undone' and a re-install writes again (B-0133, re-saved by the person, left alone)",
        rc == 0 and q(MAIN, "SELECT COUNT(*) FROM stationery_line WHERE by_whom=? AND voided_at=''", H.MARK)[0][0] == 14 and
        any("B-0133: LEFT ALONE" in x for x in buf), "\n".join(buf))
    P2 = os.path.join(tmp, "moved.db")
    build(P2)
    run(H.apply, P2)
    c = sqlite3.connect(P2)
    c.row_factory = sqlite3.Row
    b13 = c.execute("SELECT * FROM bills WHERE id=13").fetchone()
    st.void_lines(c, b13, "Shavez", "saved on the desk to another group")
    c.execute("UPDATE bills SET subgroup='other' WHERE id=13")
    c.commit()
    c.close()
    rc, buf = run(H.undo, P2)
    chk("W20 undo leaves a paper a person took off Stationery (B-0013): its old lines are NOT brought back",
        rc == 0 and not q(P2, "SELECT 1 FROM stationery_line WHERE bill_id=13 AND voided_at=''") and any("taken off by a person" in x for x in buf), "\n".join(buf))
    # ---------------------------------------------------------------- variants
    def variant(label, tweak, test):
        p = os.path.join(tmp, "v%d.db" % (GREEN + RED))
        build(p, tweak)
        b0, l0 = book(p), live_set(p)
        rc, buf = run(H.apply, p)
        chk(label, test(p, rc, buf, b0, l0), "\n".join(buf))

    variant("V-a an absent item (the X-ray envelope renamed) skips only its row; the rest written",
            lambda c, i: c.execute("UPDATE stationery_item SET name='Envelope renamed' WHERE id=?", (i["X-ray envelope 8.5 x 10.5"],)),
            lambda p, rc, buf, b0, l0: rc == 0 and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=163") and
            q(p, "SELECT COUNT(*) FROM stationery_line WHERE by_whom=? AND voided_at=''", H.MARK)[0][0] == 14 and any("no item named" in x for x in buf))
    variant("V-b a retired item (Clear bag (premium)) skips only its row",
            lambda c, i: c.execute("UPDATE stationery_item SET active=0 WHERE id=?", (i["Clear bag (premium)"],)),
            lambda p, rc, buf, b0, l0: rc == 0 and q(p, "SELECT COUNT(*) FROM stationery_line WHERE bill_id=109 AND by_whom=?", H.MARK)[0][0] == 2 and any("retired" in x for x in buf))
    variant("V-c a paper not in Stationery & packaging (B-0114 moved) is left alone, never changed",
            lambda c, i: c.execute("UPDATE bills SET subgroup='other' WHERE id=114"),
            lambda p, rc, buf, b0, l0: rc == 0 and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=114") and
            q(p, "SELECT subgroup FROM bills WHERE id=114") == [("other",)] and any("B-0114: LEFT ALONE" in x for x in buf))
    variant("V-d a second live token line on B-0013 leaves B-0013 alone",
            lambda c, i: c.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, item_id, day, ts, by_whom, at) VALUES(13,'2026-09-15 11:00:00',10,'Token again',100,'',?,'2026-10-18',?,'Shavez','x')",
                                   (i["Token, plain"], ts(2026, 10, 18, 10))),
            lambda p, rc, buf, b0, l0: rc == 0 and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=13 AND by_whom=?", H.MARK) and any("B-0013: LEFT ALONE" in x for x in buf))
    variant("V-e B-0013's ring file saved AFTER its count: B-0013 left alone (re-dating would move a counted stock)",
            lambda c, i: c.execute("UPDATE stationery_line SET ts=? WHERE bill_id=13", (ts(2026, 10, 19),)),
            lambda p, rc, buf, b0, l0: rc == 0 and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=13 AND by_whom=?", H.MARK) and book(p)["Ring file RBU-400"] == b0["Ring file RBU-400"])
    variant("V-f a reading whose line differs (B-0133 line 1 another item) leaves that paper alone",
            lambda c, i: c.execute("UPDATE claude_reading SET data=? WHERE bill_id=133", (json.dumps({"items": [{"name": "Pencil box", "qty": 20}]}),)),
            lambda p, rc, buf, b0, l0: rc == 0 and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=133") and any("B-0133: LEFT ALONE" in x for x in buf))
    variant("V-g a paper already saved on the desk by a person (B-0109 has a line) is left alone",
            lambda c, i: c.execute("INSERT INTO stationery_line(bill_id, bill_created_at, line_no, name, qty, unit, item_id, day, ts, by_whom, at) VALUES(109,'2026-10-02 10:00:00',1,'Register 192 pg Board',6,'piece',?,'2026-10-20',?,'Shavez','x')",
                                   (i["Register 192 pages"], ts(2026, 10, 20))),
            lambda p, rc, buf, b0, l0: rc == 0 and q(p, "SELECT COUNT(*) FROM stationery_line WHERE bill_id=109")[0][0] == 1 and any("B-0109: LEFT ALONE" in x for x in buf))
    variant("V-h A4 counted 05-Oct: B-0003 (24-Aug, before the count) written and adds nothing; B-0133 (07-Oct, after it) left alone (R1 B1)",
            lambda c, i: c.execute("INSERT INTO stationery_count(item_id, counted, opening, day, ts, by_whom, at) VALUES(?,0,1,'2026-10-05',?,'walk','x')", (i["A4 paper (75 gsm)"], ts(2026, 10, 5))),
            lambda p, rc, buf, b0, l0: rc == 0 and abs(book(p)["A4 paper (75 gsm)"] - b0["A4 paper (75 gsm)"]) < 1e-9 and
            bool(q(p, "SELECT 1 FROM stationery_line WHERE bill_id=3 AND by_whom=?", H.MARK)) and not q(p, "SELECT 1 FROM stationery_line WHERE bill_id=133") and
            any("B-0133: LEFT ALONE" in x for x in buf))
    variant("V-i A4 counted 01-Aug (before both A4 challans): both A4 papers left alone, its counted stock unchanged (R1 B1)",
            lambda c, i: c.execute("INSERT INTO stationery_count(item_id, counted, opening, day, ts, by_whom, at) VALUES(?,0,1,'2026-08-01',?,'walk','x')", (i["A4 paper (75 gsm)"], ts(2026, 8, 1))),
            lambda p, rc, buf, b0, l0: rc == 0 and abs(book(p)["A4 paper (75 gsm)"] - b0["A4 paper (75 gsm)"]) < 1e-9 and
            not q(p, "SELECT 1 FROM stationery_line WHERE bill_id IN (3,133)"))
    variant("V-j all six papers out of Stationery: REFUSED, nothing written, the key not set",
            lambda c, i: c.execute("UPDATE bills SET subgroup='other' WHERE id IN (3,13,109,114,133,163)"),
            lambda p, rc, buf, b0, l0: rc == 1 and live_set(p) == l0 and not q(p, "SELECT 1 FROM settings WHERE key=?", H.KEY))
    # ---------------------------------------------------------------- a mutant of the step must be refused by its own guard
    mdir = os.path.join(tmp, "mut")
    os.makedirs(mdir)
    src = open(os.path.join(KITD, "history_s623.py"), encoding="utf-8").read()
    old = "            delta[iid] = delta.get(iid, 0.0) + _contrib(q, ts, iid, lc)"
    assert src.count(old) == 1
    open(os.path.join(mdir, "history_s623.py"), "w", encoding="utf-8").write(src.replace(old, old.replace("_contrib(q, ts, iid, lc)", "0.0 * _contrib(q, ts, iid, lc)")))
    mp = os.path.join(tmp, "mut.db")
    build(mp)
    l0 = live_set(mp)
    r = subprocess.run([sys.executable, "-B", os.path.join(mdir, "history_s623.py"), "--apply", mp, "--app", APP], capture_output=True, text=True)
    chk("M1 mutant (the guard's arithmetic wrong): the step REFUSES and rolls back -- nothing written", r.returncode == 1 and live_set(mp) == l0 and "REFUSED" in r.stdout, r.stdout[-400:])
    old2 = 'LEFT ALONE -- its reading\'s line %d is'
    src2 = src.replace("if word not in st.norm(r[\"name\"]) or", "if False and")
    assert src2 != src
    open(os.path.join(mdir, "history_s623.py"), "w", encoding="utf-8").write(src2)
    mp2 = os.path.join(tmp, "mut2.db")
    build(mp2, lambda c, i: c.execute("UPDATE claude_reading SET data=? WHERE bill_id=133", (json.dumps({"items": [{"name": "Pencil box", "qty": 20}]}),)))
    subprocess.run([sys.executable, "-B", os.path.join(mdir, "history_s623.py"), "--apply", mp2, "--app", APP], capture_output=True, text=True)
    c = sqlite3.connect(mp2)
    c.row_factory = sqlite3.Row
    bm = c.execute("SELECT * FROM bills WHERE id=133").fetchone()
    pn = st.panel(c, bm, H.reading(c, 133))
    c.close()
    chk("M2 control for V-f: with the reading check removed, the line goes on a line the paper does not read (the check matters)",
        bool(q(mp2, "SELECT 1 FROM stationery_line WHERE bill_id=133")) and pn["lines"][0]["name"] == "Pencil box", pn["lines"])
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print("WALK S623: %d green, %d red" % (GREEN, RED))
sys.exit(0 if RED == 0 else 1)
