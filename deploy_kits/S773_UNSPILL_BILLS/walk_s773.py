#!/usr/bin/env python3
"""walk_s773.py FILES_DIR SHARED_DIR FINANCE_DIR [--control]
A walk on MADE-UP rows (no live data): purchase_app.py and purchase_unspill.py from FILES_DIR (the kit's, or the live ones for the
control), the rest from FINANCE_DIR. The pushes go through the real /finance/purchase/api/push door. Last line: 'WALK S773 GREEN'
or, with --control on the live files, 'CONTROL S773 RED as it must be'."""
import os
import sqlite3
import sys
import tempfile

FILES, SHARED, FIN = sys.argv[1], sys.argv[2], sys.argv[3]
CONTROL = "--control" in sys.argv
import shutil  # noqa: E402
TMP = tempfile.mkdtemp(prefix="w773_")
RUN = os.path.join(TMP, "run")                                  # purchase_app reads purchase_schema.sql beside itself
os.makedirs(RUN)
for f in ("purchase_app.py", "purchase_unspill.py"):
    if os.path.exists(os.path.join(FILES, f)):
        shutil.copyfile(os.path.join(FILES, f), os.path.join(RUN, f))
shutil.copyfile(os.path.join(FIN, "purchase_schema.sql"), os.path.join(RUN, "purchase_schema.sql"))
sys.path[:0] = [RUN, FIN, SHARED]
for m in ("purchase_app", "purchase_unspill", "supplier_msg"):
    sys.modules.pop(m, None)

from flask import Flask, g, jsonify  # noqa: E402

DB = os.path.join(TMP, "f.db")
sqlite3.connect(DB).close()
app = Flask(__name__)


def db():
    if "db" not in g:
        g.db = sqlite3.connect(DB, timeout=30)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def _close(_e):
    c = g.pop("db", None)
    if c is not None:
        c.close()


def require(*roles, unit="medical"):
    return None, (jsonify(ok=False, error="not_permitted"), 403)


import purchase_app as PA  # noqa: E402

PA.init(app, db, require, unit="medical", marg_token="walk-token", assets_db=os.path.join(TMP, "none.db"))
cl = app.test_client()
H = {"X-Finance-Marg": "walk-token"}
RES = []


def check(name, ok):
    RES.append((name, bool(ok)))
    print(("GREEN " if ok else "RED   ") + name)


N = {"n": 0}


def push(typ, pf, pt, rows):
    N["n"] += 1
    body = dict(type=typ, md5="%032x" % (0xabc000 + N["n"]), period_from=pf, period_to=pt, export_stamp="202611%02d-0900%02d" % (N["n"], N["n"]),
                file="walk", rows=rows)
    return cl.post("/finance/purchase/api/push", json=body, headers=H)


def bill(sup, bno, d, amt):
    return dict(supplier=sup, bill_no=bno, bill_date=d, cash_p=0, credit_p=amt)


def line(sup, bno, item, qty=1, amt=10000):
    return dict(supplier=sup, bill_no=bno, item=item, qty=qty, rate_p=amt, amount_p=amt * qty, net_amount_p=amt * qty, direction="PURCHASE")


def lines(where, args=()):
    c = sqlite3.connect(DB)
    r = c.execute("SELECT supplier_norm, bill_no, bill_date, month, item FROM purchase_line WHERE " + where + " ORDER BY id", args).fetchall()
    c.close()
    return r


# the bills first (bill-wise), then the item lines with spilled numbers
r = push("BILLWISE", "2026-10-01", "2026-10-31", [
    bill("YUVIKA SURGICALS BAREILLY", "YS0706202627", "2026-10-07", 195800), bill("KEDAR PHARMACEUTICAL BAREILLY", "A000207_", "2026-10-06", 740000),
    bill("TWIN AGENCIES BAREILLY", "AB12345678", "2026-10-08", 1000), bill("TWIN AGENCIES BAREILLY", "CD12345678", "2026-10-09", 2000),
    bill("DIGIT HOUSE BAREILLY", "ZZ99887766", "2026-10-10", 3000), bill("EARLY TRADERS BAREILLY", "EE55443322", "2026-09-12", 4000),
    bill("PLAIN PHARMA BAREILLY", "EP001498", "2026-10-11", 5000)])
check("1 the bill-wise push is stored through the real door", r.status_code == 200 and (r.get_json() or {}).get("stored") is True)
if CONTROL:
    have = os.path.exists(os.path.join(FILES, "purchase_unspill.py"))
    r = push("ITEMWISE", "2026-10-01", "2026-10-31", [line("YUVIKA SURGICALS BAREILLY", None, "06202627CAST SHOE M TYNOR")])
    joined = lines("item='CAST SHOE M TYNOR' AND bill_no='YS0706202627'")
    print("CONTROL S773 RED as it must be" if r.status_code == 200 and not have and not joined else "CONTROL S773 NOT RED (%s, %s)" % (have, joined))
    sys.exit(0)

import purchase_unspill as U  # noqa: E402

check("2 purchase_unspill v1.0 of S773 sits beside purchase_app", U.KIT == "S773_UNSPILL_BILLS" and U.VERSION == "1.0")
r = push("ITEMWISE", "2026-10-01", "2026-10-31", [
    line("YUVIKA SURGICALS BAREILLY", None, "06202627CAST SHOE M TYNOR"),
    line("YUVIKA SURGICALS BAREILLY", None, "06202627L S BELT XXL CONT GRAY UNI"),
    line("KEDAR PHARMACEUTICAL BAREILLY", None, "A000207_TYRO BR", 50, 14800),
    line("TWIN AGENCIES BAREILLY", None, "12345678FOO GEL"),
    line("DIGIT HOUSE BAREILLY", None, "998877661 ML INJ"),
    line("EARLY TRADERS BAREILLY", None, "55443322ROLLER BANDAGE"),
    line("KEDAR PHARMACEUTICAL BAREILLY", None, "06202627SOMETHING ELSE"),
    line("PLAIN PHARMA BAREILLY", "EP001498", "VITANSIAL PLUS"),
    line("PLAIN PHARMA BAREILLY", None, "XY998877NOT A BILL")])
check("3 the item-wise push is stored (the repair never fails a push)", r.status_code == 200 and (r.get_json() or {}).get("stored") is True)
y = lines("supplier_norm='YUVIKA SURGICALS'")
check("4 Yuvika's spilled lines (the number's last 8 fused on) join bill YS0706202627, dated 07-Oct, the number cut off",
      [(x[1], x[2], x[3], x[4]) for x in y] == [("YS0706202627", "2026-10-07", "2026-10", "CAST SHOE M TYNOR"),
                                                ("YS0706202627", "2026-10-07", "2026-10", "L S BELT XXL CONT GRAY UNI")])
k = lines("supplier_norm='KEDAR PHARMACEUTICAL'")
check("5 Kedar's 'A000207_TYRO BR' joins bill A000207_ as 'TYRO BR'; another supplier's number never joins Kedar ('06202627SOMETHING ELSE' stays)",
      ("A000207_", "2026-10-06", "2026-10", "TYRO BR") in [(x[1], x[2], x[3], x[4]) for x in k]
      and (None, "06202627SOMETHING ELSE") in [(x[1], x[4]) for x in k])
check("6 two bills of one supplier ending alike (…12345678): not split -- one bill only", lines("item='12345678FOO GEL' AND bill_no IS NULL") != [])
check("7 a digit right after the number: not split (a number is never cut in the middle)", lines("item='998877661 ML INJ' AND bill_no IS NULL") != [])
check("8 a bill dated outside the export's own period: not used", lines("item='55443322ROLLER BANDAGE' AND bill_no IS NULL") != [])
check("9 a line that came with its bill is untouched; a prefix that is no bill of its supplier stays as it came",
      lines("item='VITANSIAL PLUS' AND bill_no='EP001498'") != [] and lines("item='XY998877NOT A BILL' AND bill_no IS NULL") != [])
c = sqlite3.connect(DB)
log = c.execute("SELECT COUNT(*), MIN(by_who), MAX(by_who) FROM purchase_unspill_log").fetchone()
c.close()
check("10 every change is logged with its old values (3 lines, by 'push')", log == (3, "push", "push"))
# item lines BEFORE their bill: they stay as they came, and the bill-wise push that follows joins them
push("ITEMWISE", "2026-11-01", "2026-11-30", [line("YUVIKA SURGICALS BAREILLY", None, "08202627ARM SLING XL UNISON")])
before = lines("item='08202627ARM SLING XL UNISON' AND bill_no IS NULL")
push("BILLWISE", "2026-11-01", "2026-11-30", [bill("YUVIKA SURGICALS BAREILLY", "YS0808202627", "2026-11-02", 40000)])
after = lines("item='ARM SLING XL UNISON' AND bill_no='YS0808202627'")
check("11 item lines that arrive before their bill: kept as they came, then joined by the bill-wise push that follows (dated 02-Nov)",
      before != [] and after and after[0][2] == "2026-11-02" and after[0][3] == "2026-11")
c = sqlite3.connect(DB)
p = U.plan(c)
n2 = U.unspill(c, by="again")
c.commit()
check("12 run again: nothing more to do (idempotent)", p == [] and n2 == 0)
nu = U.undo(c)
back = c.execute("SELECT COUNT(*) FROM purchase_line WHERE item IN ('06202627CAST SHOE M TYNOR','A000207_TYRO BR','08202627ARM SLING XL UNISON') AND bill_no IS NULL").fetchone()[0]
check("13 undo puts every logged line back exactly as it came, and empties the log", nu == 4 and back == 3
      and c.execute("SELECT COUNT(*) FROM purchase_unspill_log").fetchone()[0] == 0)
c.execute("CREATE TRIGGER boom BEFORE UPDATE ON purchase_line WHEN NEW.item='L S BELT XXL CONT GRAY UNI' BEGIN SELECT RAISE(ABORT, 'walk'); END")
c.commit()
try:
    U.unspill(c, by="boom")
    raised = False
except sqlite3.DatabaseError:
    raised = True
c.commit()
check("14 a failure part-way changes nothing (savepoint): every spilled line still as it came, the log empty",
      raised and c.execute("SELECT COUNT(*) FROM purchase_line WHERE supplier_norm='YUVIKA SURGICALS' AND item LIKE '06202627%' AND bill_no IS NULL").fetchone()[0] == 2
      and c.execute("SELECT COUNT(*) FROM purchase_unspill_log").fetchone()[0] == 0)
c.execute("DROP TRIGGER boom")
c.execute("CREATE TRIGGER boom BEFORE UPDATE ON purchase_line WHEN NEW.item='TYRO BR' BEGIN SELECT RAISE(ABORT, 'walk'); END")
c.commit()
c.close()
r = push("ITEMWISE", "2026-10-02", "2026-10-30", [line("KEDAR PHARMACEUTICAL BAREILLY", None, "A000207_TYRO BR", 50, 14800)])
check("15 the repair failing inside a push never fails the push: stored, the line as it came", r.status_code == 200 and (r.get_json() or {}).get("stored") is True
      and len(lines("item='A000207_TYRO BR' AND bill_no IS NULL")) >= 1)
c = sqlite3.connect(DB)
c.execute("DROP TRIGGER IF EXISTS boom")
c.execute("INSERT INTO purchase_month (month, status) VALUES ('2026-09', 'final')") if c.execute("SELECT 1 FROM sqlite_master WHERE name='purchase_month'").fetchone() else None
c.execute("INSERT INTO purchase_line (supplier_norm, bill_no, bill_date, month, item, qty, direction, source_md5, line_type) VALUES "
          "('YUVIKA SURGICALS', NULL, '2026-09-30', '2026-09', '06202627HELD IN SEPTEMBER', 1, 'PURCHASE', 'zz', 'ITEMWISE')")
c.commit()
U.unspill(c, by="final")
c.commit()
check("17 a bill-less line already counted in a FINAL month is never moved", c.execute(
    "SELECT COUNT(*) FROM purchase_line WHERE item='06202627HELD IN SEPTEMBER' AND bill_no IS NULL").fetchone()[0] == 1)
c.execute("UPDATE purchase_line SET item='CAST SHOE M TYNOR (EDITED)' WHERE item='CAST SHOE M TYNOR' AND bill_no='YS0706202627'")
c.commit()
nu2 = U.undo(c)
check("18 undo leaves alone a line changed since the repair (and says so); the others go back",
      U.UNDO_SKIPPED["n"] == 1 and nu2 >= 1 and c.execute("SELECT COUNT(*) FROM purchase_line WHERE item='CAST SHOE M TYNOR (EDITED)'").fetchone()[0] == 1)
c.close()
src = open(os.path.join(FILES, "purchase_app.py"), encoding="utf-8").read()
i_hook, i_redate = src.find("purchase_unspill.unspill(con, by=\"push\")"), src.find("    _redate_lines(con)\n")
i_push = src.find("def api_push():")
check("16 purchase_app: the hook is in api_push once, before the lines are re-dated", src.count("purchase_unspill.unspill(") == 1 and i_push < i_hook < i_redate)

bad = [n for n, ok in RES if not ok]
print("WALK S773 GREEN" if not bad else "WALK S773 RED (%d): %s" % (len(bad), "; ".join(bad)[:300]))
