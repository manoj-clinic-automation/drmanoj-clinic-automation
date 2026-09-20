#!/usr/bin/env python3
"""walk_s351.py -- the live-shape walk of xray_plan() after S351: the staff's REAL file-name shapes (copied
from the X-ray test page of 20-Sep-2026, names and IDs replaced by the walk's own) over a SCRATCH COPY of the
real finance.db, with the walk's own slips seeded on a day no real slip carries. Asserts ONLY about the rows it
made (F-581). Prints IDs and counts, never a real name.

Usage: FINANCE_DB=<scratch copy> python3 walk_s351.py <app dir> [<old records.py for the negative control>]
"""
import datetime as dt
import importlib.util
import os
import sqlite3
import sys

N = [0]
DAY = "2001-01-01"                     # no real slip lives here
IDS = ("909001", "909002", "909003", "909004", "909005", "909006", "909007")


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s %s" % (N[0], name, extra))
        sys.exit(1)


def load(path, modname):
    spec = importlib.util.spec_from_file_location(modname, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def utc(day, hhmm):
    t = dt.datetime.fromisoformat("%sT%s:00" % (day, hhmm)) - dt.timedelta(hours=5, minutes=30)
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def f(name, hhmm, md5=None):
    return {"name": name, "mimeType": "image/jpeg", "modifiedTime": utc(DAY, hhmm), "md5Checksum": md5 or ("m-" + name)}


def seed(con):
    """The walk's own slips: one X-ray per ID except 909002 (two views) and 909006 (no slip at all)."""
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (DAY,))
    con.execute("DELETE FROM slip WHERE day=?", (DAY,))
    con.execute("DELETE FROM patient_ref WHERE clinic_id IN (%s)" % ",".join("?" * len(IDS)), IDS)
    n = 0
    for cid in IDS:
        if cid == "909006":
            continue
        con.execute("INSERT INTO patient_ref(clinic_id, name) VALUES (?,?)", (cid, "WALK " + cid))
        n += 1
        cur = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_at) VALUES ('xp',?,?,?,'ok',?)",
                          (900000 + n, DAY, cid, DAY + " 16:57:54"))
        sid = cur.lastrowid
        views = ("Knee AP", "Knee Lateral") if cid == "909002" else ("Wrist AP",)
        for i, v in enumerate(views):
            con.execute("INSERT INTO slip_item(slip_id, kind, name, side, sort) VALUES (?,'xray',?,'',?)", (sid, v, i))
    con.commit()


def main():
    app = sys.argv[1]
    old = sys.argv[2] if len(sys.argv) > 2 else ""
    dbp = os.environ["FINANCE_DB"]
    assert "walk" in dbp or "scratch" in dbp or dbp.startswith("/tmp"), "refusing a non-scratch database"
    sys.path.insert(0, app)
    os.chdir(app)
    rec = load(os.path.join(app, "records.py"), "records_s351")
    con = sqlite3.connect(dbp)
    con.row_factory = sqlite3.Row
    rec.ensure(con)
    seed(con)

    # THE REAL SHAPES (X-ray test page, 20-Sep-2026), the walk's own names and IDs in place of the staff's:
    files = [
        f("AAAA BBBB 909001.jpg", "20:16"),                 # NAME ID            -> one X-ray on the slip -> matched
        f("CCCC 909002.jpg", "20:44"),                      # NAME ID  (view 1)  -> two X-rays on the slip -> matched
        f("CCCC 909002 ..jpg", "20:45"),                    # NAME ID .. (view 2)
        f("DDDD EEEE 909003.jpg", "19:34"),                 # NAME ID
        f("DDDD EEEE ..jpg", "19:35"),                      # NAME ..  -> no number: the sister rule gives 909003
        f("FFFF.jpg", "09:58"),                             # no number, no sister -> check folder
        f("909004 GGGG.jpg", "19:44"),                      # ID NAME (the old shape) -> still matched
        f("HHHH 909005 2.jpg", "19:50"),                    # two numbers -> check folder, never a guess
        f("IIII 909006.jpg", "19:52"),                      # an ID with no X-ray that day -> check folder
        f("JJJJ 909007.jpg", "19:55", md5="same"),          # a duplicate picture...
        f("JJJJ 909007 ..jpg", "19:56", md5="same"),        # ...kept once
    ]
    rows = {r["orig"]: r for r in rec.xray_plan(con, files)}
    check("eleven rows", len(rows) == 11)
    check("NAME ID matched", rows["AAAA BBBB 909001.jpg"]["kind"] == "ok", rows["AAAA BBBB 909001.jpg"]["verdict"])
    check("NAME ID proposed carries day, ID, name, study",
          rows["AAAA BBBB 909001.jpg"]["proposed"].startswith("2001-01-01 · 909001 · WALK 909001 · Wrist AP"),
          rows["AAAA BBBB 909001.jpg"]["proposed"])
    check("two views, two X-rays: view 1 matched", rows["CCCC 909002.jpg"]["kind"] == "ok")
    check("two views, two X-rays: view 2 matched", rows["CCCC 909002 ..jpg"]["kind"] == "ok")
    check("view 2 is the second study, by time", "Knee Lateral" in rows["CCCC 909002 ..jpg"]["proposed"],
          rows["CCCC 909002 ..jpg"]["proposed"])
    check("sister rule: the numberless file took 909003", rows["DDDD EEEE ..jpg"]["cid"] == "909003")
    check("sister rule: says so in the verdict", "taken from the sister file DDDD EEEE 909003.jpg" in rows["DDDD EEEE ..jpg"]["verdict"],
          rows["DDDD EEEE ..jpg"]["verdict"])
    check("sister pair vs one X-ray: numbered, not guessed", rows["DDDD EEEE ..jpg"]["kind"] == "differ"
          and rows["DDDD EEEE 909003.jpg"]["kind"] == "differ")
    check("no number, no sister: check folder", rows["FFFF.jpg"]["kind"] == "check" and "no clinic ID" in rows["FFFF.jpg"]["verdict"])
    check("ID NAME (old shape) still matched", rows["909004 GGGG.jpg"]["kind"] == "ok")
    check("two numbers: check folder", rows["HHHH 909005 2.jpg"]["kind"] == "check" and "two numbers" in rows["HHHH 909005 2.jpg"]["verdict"])
    check("two numbers: no ID guessed", rows["HHHH 909005 2.jpg"]["cid"] == "")
    check("ID without an X-ray that day: check folder", rows["IIII 909006.jpg"]["kind"] == "check"
          and "not in" in rows["IIII 909006.jpg"]["verdict"])
    check("duplicate kept once", sorted([rows["JJJJ 909007 ..jpg"]["kind"], rows["JJJJ 909007.jpg"]["kind"]]) == ["dup", "ok"])
    check("clock measured against the slip", abs(rows["AAAA BBBB 909001.jpg"]["clock"] - (20 * 60 + 16 - (16 * 60 + 57) - 54 / 60.0)) < 0.1,
          str(rows["AAAA BBBB 909001.jpg"].get("clock")))
    kinds = {}
    for r in rows.values():
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    check("counts: 5 matched", kinds.get("ok") == 5, str(kinds))
    check("counts: 2 numbered", kinds.get("differ") == 2, str(kinds))
    check("counts: 3 check", kinds.get("check") == 3, str(kinds))
    check("counts: 1 dup", kinds.get("dup") == 1, str(kinds))
    # the helpers on their own
    check("xray_id trailing", rec.xray_id("AJAY XYZ 6854.jpg") == ("6854", "one"))
    check("xray_id leading", rec.xray_id("6854 AJAY.jpg") == ("6854", "one"))
    check("xray_id dotted second view", rec.xray_id("SHALINI 8135 ..jpg") == ("8135", "one"))
    check("xray_id none", rec.xray_id("PHOOL WATI ..jpg") == ("", "none"))
    check("xray_id many", rec.xray_id("A 12 B 34.jpg") == ("", "many"))
    check("xray_id ignores the extension digits", rec.xray_id("RAMU 5.jp2"[:-4] + ".jpg") == ("5", "one"))
    check("xray_id: nine digits is not an ID", rec.xray_id("X 123456789.jpg") == ("", "none"))
    check("xray_stem", rec.xray_stem("PHOOL WATI ..jpg") == "PHOOL WATI" and rec.xray_stem("PHOOL WATI 3527.jpg") == "PHOOL WATI")
    # the sister rule must not cross days or stems
    files2 = [f("KKKK 909001.jpg", "10:00"), {"name": "KKKK ..jpg", "mimeType": "image/jpeg",
                                              "modifiedTime": utc("2001-01-02", "10:01"), "md5Checksum": "m-k2"}]
    r2 = {r["orig"]: r for r in rec.xray_plan(con, files2)}
    check("sister rule does not cross a day", r2["KKKK ..jpg"]["kind"] == "check" and r2["KKKK ..jpg"]["cid"] == "")
    files3 = [f("LLLL 909001.jpg", "10:00"), f("LLLL 909004.jpg", "10:02"), f("LLLL ..jpg", "10:03")]
    r3 = {r["orig"]: r for r in rec.xray_plan(con, files3)}
    check("two sisters with two IDs: no guess", r3["LLLL ..jpg"]["kind"] == "check" and r3["LLLL ..jpg"]["cid"] == "")

    # NEGATIVE CONTROL: the S346 bytes read the same shapes -> the trailing-ID files all go to the check folder
    if old:
        o = load(old, "records_s346")
        orows = {r["orig"]: r for r in o.xray_plan(con, files)}
        ok_old = sum(1 for r in orows.values() if r["kind"] == "ok")
        check("negative control: S346 matches only the ID-first file", ok_old == 1 and orows["909004 GGGG.jpg"]["kind"] == "ok", str(ok_old))
        check("negative control: S346 sends NAME ID to the check folder", orows["AAAA BBBB 909001.jpg"]["kind"] == "check")

    # leave the scratch copy as found for the walk's own rows
    con.execute("DELETE FROM slip_item WHERE slip_id IN (SELECT id FROM slip WHERE day=?)", (DAY,))
    con.execute("DELETE FROM slip WHERE day=?", (DAY,))
    con.execute("DELETE FROM patient_ref WHERE clinic_id IN (%s)" % ",".join("?" * len(IDS)), IDS)
    con.commit()
    print("WALK OK -- %d checks (S351: the staff's real name shapes read; sister rule; two-number refusal; negative control %s)"
          % (N[0], "run" if old else "skipped"))


if __name__ == "__main__":
    main()
