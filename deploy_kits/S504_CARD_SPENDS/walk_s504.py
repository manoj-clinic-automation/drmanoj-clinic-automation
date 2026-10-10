"""walk_s504.py -- S504_CARD_SPENDS, session 304 (parent), 10-Oct-2026. The walk the installer runs on the box BEFORE placing.

On a SCRATCH copy of finance.db (sqlite backup API) and a scratch folder holding /root/finance's programs (the kit's three over
them, unless --control): process_inbox() as the 05:40 cron runs it, then the packs page's own routes through Flask's test client,
signed in as the doctor. Nothing live is written. The SAME walk on the live programs (--control) must end RED.

GREEN needs: the card statements on the shelf are read line by line and EVERY one proves against its own printed totals; a second
run reads none again; the state carries the month's card spends; the page carries its card section; naming a merchant answers 200
and a bad category 400; the pack's card row is there. Prints counts and words only -- never a card number, never a line's amount.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

KIT_FILES = ("packs.py", "packs.html", "card_lines.py")
ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="/root/wa/venv/bin/python3")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()

scr = tempfile.mkdtemp(prefix="s504_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".html", ".json")) and not n.startswith(".") and n != "card_lines.py":
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in KIT_FILES:
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))
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
    res = packs.process_inbox(con)
    n1 = res.get("cards_read")
    res2 = packs.process_inbox(con)
    print("  pass process_inbox: card statements read now %s . on a second run %s" % (n1, res2.get("cards_read")))
    if not n1:
        red.append("no card statement was read line by line")
    if res2.get("cards_read"):
        red.append("a second run read %s statement(s) again" % res2.get("cards_read"))
    try:
        st = con.execute("SELECT COUNT(*), SUM(proof_ok), SUM(lines) FROM card_stmt").fetchone()
        bad = [r[0] + " " + r[1] for r in con.execute("SELECT slot_key, statement_date FROM card_stmt WHERE proof_ok=0")]
        print("  pass the card statements: %d read . %d proved against their own totals . %d lines" % (st[0], st[1] or 0, st[2] or 0))
        if bad:
            red.append("%d statement(s) do not add up: %s" % (len(bad), "; ".join(bad)))
    except sqlite3.Error as ex:
        red.append("no card tables: %s" % ex)
    from flask import Flask                                        # noqa: E402

    def _g():
        c = sqlite3.connect(db, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    app = Flask("walk_s504")
    packs.init(app, _g, lambda *x, **k: None)
    packs._owner = lambda: (dict(username="manoj", role="doctor", roles=["doctor"]), None)
    cl = app.test_client()
    sj = cl.get("/finance/packs/api/state")
    j = sj.get_json(silent=True) or {}
    cs = j.get("cards") or {}
    if sj.status_code != 200:
        red.append("the state answered %d" % sj.status_code)
    if "statements" not in cs:
        red.append("the state carries no card spends")
    else:
        print("  pass the state, %s: %d card statement(s) dated in it (%s) . %d lines in %d categories . %d merchants still to name"
              % (j.get("month"), len(cs["statements"]), "all proved" if cs.get("all_proved") else "NOT all proved", len(cs.get("lines") or []),
                 len(cs.get("by_category") or []), len(cs.get("unnamed") or [])))
    pg = cl.get("/finance/packs")
    if pg.status_code != 200 or b"cardsView(" not in pg.data:
        red.append("the page answered %d%s" % (pg.status_code, "" if b"cardsView(" in pg.data else " without its card section"))
    row = [r for r in (j.get("rows") or []) if r.get("key") == "cards"]
    print("  pass the pack's card row: %s" % ((row[0]["title"] + " -- " + row[0]["status"]) if row else "MISSING"))
    if not row:
        red.append("the pack has no card row")
    un = cs.get("unnamed") or []
    if un:
        r1 = cl.post("/finance/packs/api/card-merchant", json=dict(merchant=un[0]["merchant"], category="clinic"))
        r2 = cl.post("/finance/packs/api/card-merchant", json=dict(merchant=un[0]["merchant"], category="repayment"))
        left = len(((cl.get("/finance/packs/api/state").get_json() or {}).get("cards") or {}).get("unnamed") or [])
        print("  pass naming a merchant (on the scratch copy): %d, a bad category %d, merchants still to name %d -> %d" % (r1.status_code, r2.status_code, len(un), left))
        if r1.status_code != 200 or r2.status_code != 400 or left != len(un) - 1:
            red.append("naming a merchant did not behave")
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S504 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
