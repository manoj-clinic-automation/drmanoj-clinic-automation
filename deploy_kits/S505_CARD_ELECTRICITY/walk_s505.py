"""walk_s505.py -- S505_CARD_ELECTRICITY, session 304 (parent), 10-Oct-2026. The walk the installer runs BEFORE placing.

On a SCRATCH copy of finance.db and a scratch copy of /root/finance's programs (the kit's two over them, unless --control): the
packs state of last month through Flask's test client, signed in as the doctor. GREEN needs: the electricity bill a card paid is
taken from the card statement DATED in the month (the owner's ruling, 10-Oct) -- every card line with an electricity word on such a
statement is listed, worded 'on its statement dated ...'; the page answers and says 'spent ... (after refunds)'. The SAME walk on
the live programs (--control) must end RED. Prints words and counts only.
"""
import argparse
import os
import shutil
import sqlite3
import sys
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("--kit", required=True)
ap.add_argument("--fin", default="/root/finance")
ap.add_argument("--db", default="/root/finance/finance.db")
ap.add_argument("--venv", default="")
ap.add_argument("--control", action="store_true")
a = ap.parse_args()
scr = tempfile.mkdtemp(prefix="s505_walk_")
fin = os.path.join(scr, "fin")
os.makedirs(fin)
for n in os.listdir(a.fin):
    p = os.path.join(a.fin, n)
    if os.path.isfile(p) and n.endswith((".py", ".html", ".json")) and not n.startswith("."):
        shutil.copy2(p, os.path.join(fin, n))
if not a.control:
    for n in ("packs.py", "packs.html"):
        shutil.copy(os.path.join(a.kit, n), os.path.join(fin, n))
db = os.path.join(scr, "fin.db")
src = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True, timeout=60)
dst = sqlite3.connect(db)
src.backup(dst)
dst.close()
src.close()
os.environ.update(FINANCE_DB=db, STMT_INBOX=os.path.join(scr, "inbox"), PACKS_DIR=os.path.join(scr, "packs"), PACKS_MAIL_STUB=os.path.join(scr, "mail"),
                  PACKS_HANDOVER_DIR=os.path.join(scr, "handover"), FINANCE_DIR=fin)
sys.path.insert(0, fin)
os.chdir(fin)
red = []
try:
    import packs                                                   # noqa: E402
    from flask import Flask                                        # noqa: E402
    con = sqlite3.connect(db, timeout=60)
    m = packs._prev_month(packs._today().strftime("%Y-%m"))
    words = [w.strip().upper() for w in packs._setting(con, "packs.electricity_words", packs.SETTINGS["packs.electricity_words"][0]).split(",") if w.strip()]
    want = [r for r in con.execute("SELECT l.description FROM card_line l JOIN card_stmt s ON s.id=l.stmt_id WHERE l.credit=0 AND substr(s.statement_date,1,7)=?", (m,))
            if any(w in (r[0] or "").upper() for w in words)]
    got = packs.card_electricity(con, m, words)
    print("  pass %s: card lines with an electricity word on the card statements dated in it: %d . listed: %d (%s)"
          % (m, len(want), len(got), "; ".join(g.split(" (")[0] for g in got)[:160]))
    if not want:
        red.append("no card electricity line on last month's statements -- the walk cannot tell old from new on this data")
    elif len(got) != len(want) or not all("on its statement dated" in g for g in got):
        red.append("the card's electricity bill is not taken from the statement dated in the month")

    def _g():
        c = sqlite3.connect(db, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    app = Flask("walk_s505")
    packs.init(app, _g, lambda *x, **k: None)
    packs._owner = lambda: (dict(username="manoj", role="doctor", roles=["doctor"]), None)
    cl = app.test_client()
    j = cl.get("/finance/packs/api/state").get_json() or {}
    el = [r for r in (j.get("rows") or []) if "lectric" in (r.get("title") or "")]
    print("  pass the pack's electricity item: %s" % ((el[0]["status"] + " -- " + (el[0]["why"] or "")[:150]) if el else "MISSING"))
    pg = cl.get("/finance/packs")
    if pg.status_code != 200 or "(after refunds)".encode() not in pg.data:
        red.append("the page answered %d%s" % (pg.status_code, "" if b"(after refunds)" in pg.data else " without the new wording"))
    con.close()
except Exception as ex:                                            # noqa: BLE001
    red.append("%s: %s" % (type(ex).__name__, str(ex)[:200]))
finally:
    os.chdir("/")
    shutil.rmtree(scr, ignore_errors=True)
print("WALK_S505 %s%s" % ("RED: " if red else "GREEN", " | ".join(red)))
sys.exit(1 if red else 0)
