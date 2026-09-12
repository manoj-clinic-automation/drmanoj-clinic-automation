"""
selftest_amir_salts.py -- the salt sheet, round-tripped for real.

A real Flask app, a real sqlite database with the real shape of
purchase_salt_task, the real padwriter writing the workbook and the real
padreader reading it back.  The sheet is downloaded, filled the way Amir would
fill it, and uploaded -- over HTTP, not through a stub.

Run:  /usr/bin/python3 selftest_amir_salts.py
"""

import io
import os
import re
import sqlite3
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, g                                   # noqa: E402
import amir_salts                                            # noqa: E402
import padreader as PR                                       # noqa: E402

OK, BAD = [], []


def check(name, cond, detail=""):
    (OK if cond else BAD).append(name)
    print(("   ok   " if cond else "   FAIL ") + name + (("  -- " + detail) if detail and not cond else ""))


TASKS = [
    # id, section, seq, a, b, c, done
    (1, "rename", 1, "METHYLPREDNISOLONE 8", "METHYL PREDNISOLONE 8", "one molecule", 0),
    (2, "rename", 2, "ETOROCOXIB 90", "ETORICOXIB 90", "same molecule", 0),
    (3, "create", 1, "ANTIBIOTIC CREAM", "1", "SILVEREX-HEAL", 0),
    (4, "create", 2, "CALCIUM + CISSUS", "2", "CALFLIP CQ, CROCAL EXTRA TAB", 0),
    (5, "change", 1, "PRETOL-4", "METHYLPREDNISOLONE", "METHYL PREDNISOLONE 4", 0),
    (6, "change", 2, "DROTIN TAB", "DROTAVERIN", "DROTAVERINE 40", 0),
    (7, "cleanup", 1, "blank salts", "clear them", "", 0),
    (8, "change", 3, "ALREADY DONE ITEM", "x", "Y SALT", 1),
    (9, "waiting", 1, "TENDOZAC TAB", "(none)", "", 0),
]


def build_db(path):
    cx = sqlite3.connect(path)
    cx.executescript("""
    CREATE TABLE purchase_salt_task(
        id INTEGER PRIMARY KEY, section TEXT, seq INTEGER, a TEXT, b TEXT, c TEXT,
        done INTEGER DEFAULT 0, done_by TEXT, done_at TEXT,
        answer TEXT, answer_by TEXT, answer_at TEXT, source_md5 TEXT, pushed_at TEXT);
    CREATE TABLE purchase_new_item(
        item_norm TEXT PRIMARY KEY, item TEXT, first_seen TEXT, seen_in TEXT,
        supplier TEXT, packing TEXT, logged_at TEXT, note TEXT);
    """)
    cx.executemany("INSERT INTO purchase_salt_task(id,section,seq,a,b,c,done) "
                   "VALUES(?,?,?,?,?,?,?)", TASKS)
    cx.execute("INSERT INTO purchase_new_item(item_norm,item,first_seen,seen_in,supplier,packing)"
               " VALUES('zzz','ZZZ NEW TAB','%s-05','purchase','Yuvika','1*10')"
               % amir_salts._now().strftime("%Y-%m"))
    cx.commit()
    return cx


def make_app(dbpath, allow=True):
    app = Flask(__name__)
    app.config["TESTING"] = True

    def db():
        if "cx" not in g:
            g.cx = sqlite3.connect(dbpath)
            g.cx.row_factory = sqlite3.Row
        return g.cx

    def require(*roles, **kw):
        if not allow:
            return None, ({"error": "no_role_here"}, 403)
        return {"username": "amir"}, None

    @app.teardown_appcontext
    def _close(exc):
        cx = g.pop("cx", None)
        if cx is not None:
            cx.commit()
            cx.close()

    amir_salts.init(app, db, require, unit="medical")
    return app


def find_grid(raw, want="SALT KAAM"):
    for name, gr in PR.grids(io.BytesIO(raw)):
        if name.strip().upper().startswith(want):
            return gr
    return None


def header_cols(grid):
    """(header row, {UPPER TEXT: col})"""
    for (r, c), v in grid.items():
        if str(v).strip().upper() == "ID":
            row = {str(vv).strip().upper(): cc for (rr, cc), vv in grid.items() if rr == r}
            return r, row
    return None, {}


def refill(raw, ticks, remark=None, drop_id=False, blank_ids=()):
    """Rewrite the workbook's SALT KAAM sheet with HO GAYA filled in.

    Done by editing the sheet XML directly -- which is exactly what Excel gives
    back: a file whose cells now carry values the server never wrote.
    """
    import padwriter as PW
    grid = find_grid(raw)
    hr, cols = header_cols(grid)
    cid, ctick, crem = cols["ID"], None, cols.get("REMARK")
    for k, v in cols.items():
        if k.startswith("HO GAYA"):
            ctick = v
    sh = PW.Sheet()
    for (r, c), v in grid.items():
        if v is None or v == "":
            continue
        if c == cid and r > hr and drop_id:
            continue
        if isinstance(v, float) and c == cid:
            sh.num(r, c, int(v))
        else:
            sh.text(r, c, str(v))
    rows = sorted({r for (r, _c) in grid.keys() if r > hr})
    for r in rows:
        val = grid.get((r, cid))
        if val is None:
            continue
        try:
            tid = int(float(val))
        except (TypeError, ValueError):
            continue
        if tid in blank_ids:
            continue
        if tid in ticks:
            sh.text(r, ctick, ticks[tid])
            if remark and crem is not None:
                sh.text(r, crem, remark)
    return PW.workbook_bytes_multi([("SALT KAAM", sh)])


def post(c, raw, fn="SALT_KAAM_12-09-2026.xlsx"):
    return c.post("/finance/amir/salts",
                  data={"f": (io.BytesIO(raw), fn)},
                  content_type="multipart/form-data", follow_redirects=True)


def main():
    tmp = tempfile.mkdtemp(prefix="salts_")
    dbp = os.path.join(tmp, "t.db")
    cx = build_db(dbp)
    app = make_app(dbp)
    c = app.test_client()

    print("-- 1. the page")
    t = c.get("/finance/amir/salts").get_data(as_text=True)
    check("it says how many are left", "7 baaki" in t, t[t.find("Salt ka kaam --"):][:40])
    check("it offers the download", "/finance/amir/salts.xlsx" in t)
    check("it offers the upload", 'type=file' in t and "enctype='multipart/form-data'" in t)

    print("-- 2. the workbook")
    r = c.get("/finance/amir/salts.xlsx")
    raw = r.get_data()
    check("it is served as an attachment", "attachment" in r.headers.get("Content-Disposition", ""))
    check("it is a real xlsx (zip magic)", raw[:4] == b"PK\x03\x04")
    check("Excel can open it", zipfile.is_zipfile(io.BytesIO(raw)))
    names = [n for n, _g in PR.grids(io.BytesIO(raw))]
    check("the tabs are there", names[0].startswith("SALT KAAM") and "PADHIYE" in names, str(names))
    check("the doctor's questions ride along", any(n.startswith("DR SAHAB") for n in names), str(names))
    check("this month's new items ride along", any(n.startswith("NAYE ITEM") for n in names), str(names))

    grid = find_grid(raw)
    hr, cols = header_cols(grid)
    check("the ID column is there", "ID" in cols)
    check("the tick column is there", any(k.startswith("HO GAYA") for k in cols))
    ce = cols.get("YEH EXACT NAAM COPY KIJIYE")
    check("the exact-name column is there", ce is not None, str(sorted(cols)))

    print("-- 3. the exact spelling is in the sheet, letter for letter")
    vals = {}
    for r in sorted({r for (r, _c) in grid.keys() if r > hr}):
        i = grid.get((r, cols["ID"]))
        if i is None:
            continue
        vals[int(float(i))] = str(grid.get((r, ce)) or "")
    check("a rename carries the NEW spelling", vals.get(1) == "METHYL PREDNISOLONE 8", repr(vals.get(1)))
    check("a create carries the salt to create", vals.get(3) == "ANTIBIOTIC CREAM", repr(vals.get(3)))
    check("a change carries the CORRECT salt", vals.get(5) == "METHYL PREDNISOLONE 4", repr(vals.get(5)))
    check("the already-done row is not in the sheet", 8 not in vals)
    check("the doctor's row is not in his work tab", 9 not in vals)
    check("nothing is pre-ticked",
          all(str(grid.get((r, cols["HO GAYA (Y)"])) or "") == ""
              for r in sorted({r for (r, _c) in grid.keys() if r > hr})))

    print("-- 4. he fills three rows and uploads")
    filled = refill(raw, {1: "Y", 3: "y", 5: "haan"}, remark="kar diya")
    t = post(c, filled).get_data(as_text=True)
    check("it reports three ticked", "<b>3</b> kaam tick hue" in t, t[t.find("kaam tick"):][:60] if "kaam tick" in t else t[:200])
    done = dict(cx.execute("SELECT id, COALESCE(done,0) FROM purchase_salt_task").fetchall())
    check("those three are done in the table", done[1] == 1 and done[3] == 1 and done[5] == 1)
    check("the untouched ones are still open", done[2] == 0 and done[6] == 0 and done[7] == 0)
    who = cx.execute("SELECT done_by FROM purchase_salt_task WHERE id=1").fetchone()[0]
    check("the tick carries his name", who == "amir", repr(who))

    print("-- 5. the same file again changes nothing")
    t = post(c, filled).get_data(as_text=True)
    n = cx.execute("SELECT COUNT(*) FROM purchase_salt_task WHERE done=1").fetchone()[0]
    check("still four done (three plus the pre-existing one)", n == 4, "done=%d" % n)

    print("-- 6. the next sheet no longer carries what was done")
    raw2 = c.get("/finance/amir/salts.xlsx").get_data()
    g2 = find_grid(raw2)
    hr2, cols2 = header_cols(g2)
    ids2 = {int(float(g2[(r, cols2["ID"])])) for r in
            {r for (r, _c) in g2.keys() if r > hr2} if (r, cols2["ID"]) in g2}
    check("the ticked rows are gone", not ({1, 3, 5} & ids2), str(sorted(ids2)))
    check("the open ones remain", {2, 6, 7} <= ids2, str(sorted(ids2)))

    print("-- 7. a blank is blank, never a tick")
    filled2 = refill(raw2, {2: "", 6: "   "})
    t = post(c, filled2).get_data(as_text=True)
    done = dict(cx.execute("SELECT id, COALESCE(done,0) FROM purchase_salt_task").fetchall())
    check("nothing was ticked from blanks", done[2] == 0 and done[6] == 0)
    check("and it says they will come back", "agli baar phir aayenge" in t or "khaali" in t)

    print("-- 8. a word that is not yes does not tick")
    filled3 = refill(raw2, {2: "nahi", 6: "baad mein"})
    post(c, filled3)
    done = dict(cx.execute("SELECT id, COALESCE(done,0) FROM purchase_salt_task").fetchall())
    check("'nahi' is not a tick", done[2] == 0 and done[6] == 0)

    print("-- 9. an ID that does not exist is reported, not silently dropped")
    filled4 = refill(raw2, {2: "Y"})
    g4 = find_grid(filled4)
    hr4, cols4 = header_cols(g4)
    import padwriter as PW
    sh = PW.Sheet()
    for (r, cc), v in g4.items():
        if v is None or v == "":
            continue
        if cc == cols4["ID"] and r > hr4 and int(float(v)) == 2:
            sh.num(r, cc, 9999)
        elif isinstance(v, float) and cc == cols4["ID"]:
            sh.num(r, cc, int(v))
        else:
            sh.text(r, cc, str(v))
    t = post(c, PW.workbook_bytes_multi([("SALT KAAM", sh)])).get_data(as_text=True)
    check("the unknown id is named on the page", "pehchani nahin" in t, t[:400])

    print("-- 10. the wrong kind of file is refused readably")
    t = post(c, b"not a spreadsheet at all", fn="notes.txt").get_data(as_text=True)
    check("a .txt is refused", "sirf .xlsx" in t)
    t = post(c, b"not a spreadsheet at all", fn="x.xlsx").get_data(as_text=True)
    check("bytes that are not xlsx are refused", "sach mein Excel" in t)
    t = post(c, b"", fn="x.xlsx").get_data(as_text=True)
    check("an empty file is refused", "khaali hai" in t)
    big = b"PK\x03\x04" + b"0" * (amir_salts.MAX_BYTES + 10)
    t = post(c, big, fn="x.xlsx").get_data(as_text=True)
    check("an oversized file is refused", "bahut badi" in t)

    print("-- 11. a sheet with the ID column deleted is refused, not half-applied")
    noid = refill(raw2, {6: "Y"}, drop_id=True)
    before = cx.execute("SELECT COUNT(*) FROM purchase_salt_task WHERE done=1").fetchone()[0]
    t = post(c, noid).get_data(as_text=True)
    after = cx.execute("SELECT COUNT(*) FROM purchase_salt_task WHERE done=1").fetchone()[0]
    check("nothing was applied without ids", before == after, "%d -> %d" % (before, after))

    print("-- 12. no phone-shaped number anywhere on the page")
    t = c.get("/finance/amir/salts").get_data(as_text=True)
    check("none rendered", not re.search(r"(?<!\d)[6-9]\d{9}(?!\d)", re.sub(r"<[^>]+>", " ", t)))

    print("-- 13. a user without the role gets a readable refusal")
    app2 = make_app(dbp, allow=False)
    r = app2.test_client().get("/finance/amir/salts")
    check("403 with a sentence, not a trace", r.status_code == 403
          and "Yeh page aapke liye nahin hai" in r.get_data(as_text=True))

    print("")
    print("%d ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        for b in BAD:
            print("  FAILED: " + b)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
