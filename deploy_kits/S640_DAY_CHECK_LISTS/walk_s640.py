#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s640.py -- the LIVE-SHAPE walk of kit S640_DAY_CHECK_LISTS (D776 stage 3). Made-up patients, a temp database.

    python3 walk_s640.py <dir with the NEW day_check.py, aaj_seed.py, aaj_kaam.html, aaj_duties.json> <dir with the rest> [--old]

It borrows S636's made-up days (walk_s636.py beside it): the 22-Oct shape, the 07-Oct shape, a duplicate. Then: the staff's
door names their lines, Shavez sees both kinds, Bhati the parchi kind, the owner none; a tick takes a line off the staff's
list; a Docterz export after the tick that still shows the line brings it back as 'not fixed'; all Docterz lines ticked makes
his line read 'Re-export <day> from Docterz'; the duty files carry the two new lines; the list page shows a door's words.
--old runs it on the live files: exactly the S640 checks go red."""
import json
import os
import sys

NEW, REST = sys.argv[1], sys.argv[2]
OLD = "--old" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], NEW, REST] + (["--old"] if OLD else [])
sys.path[:0] = [NEW, HERE, REST]
import walk_s636 as W                                     # noqa: E402 -- its seed, its db, its require

import flask                                              # noqa: E402

RES = []


def ok(name, cond, s640=True):
    RES.append((name, bool(cond), s640))
    print(("  ok   " if cond else "  RED  ") + name)


def main():
    import clinic_register as CR
    import slip_log as SL
    import day_check as DC
    app = flask.Flask("walk")
    CR.init(app, W.db, W.require, W.audit, unit="clinic")
    SL.init(app, W.db, W.require, W.audit, unit="slips")
    with app.app_context():
        W.seed(W.db())
    cl = app.test_client()
    D1, D2 = W.D1, W.D2
    real_today = DC.dt.date

    class _D(real_today):                                 # 'today' is the day after the 22-Oct shape
        @classmethod
        def today(cls):
            return real_today(2026, 10, 23)
    DC.dt.date = _D

    def mine(who):
        W.CUR["user"] = who
        r = cl.get("/finance/clinic/check/api/mine")
        try:
            return r.status_code, r.get_json() or {}
        except Exception:                                # noqa: BLE001
            return r.status_code, {}

    st, j = mine("shivani")
    ok("1  Shivani's door counts her Docterz lines (22-Oct: 4, 21-Oct: 2)", st == 200 and j.get("open") == 6)
    ok("2  ... and names them, patient by patient", "Patient A8" not in (j.get("text") or "") and "Patient A3" in (j.get("text") or "")
       and "22-Oct" in (j.get("text") or ""))
    st, j2 = mine("shavez")
    ok("3  Shavez sees the Docterz lines and the parchi lines", j2.get("open") == j.get("open", 0) + 2)
    st, j3 = mine("bhati")
    ok("4  Bhati sees the parchi lines only", j3.get("open") == 2)
    st, j4 = mine("manoj")
    ok("5  the owner's door is empty (his line is on his console)", j4.get("open") == 0)
    W.CUR["user"] = "shivani"
    r = cl.get("/finance/clinic/check/mine")
    ok("6  the line opens the oldest day that still has lines", r.status_code == 302 and r.headers.get("Location", "").endswith("/finance/clinic/check/%s#check" % D2))
    with app.app_context():
        con = W.db()
        c1 = DC.check_day(con, D1)
        keys = [c["key"] for c in c1["cards"] if c["who"] == "docterz"]
        for k in keys:
            DC.add_tick(con, D1, k, "added" if not k.startswith("mode") else "changed", "alisha")
        con.execute("UPDATE day_check_tick SET at='2026-10-23 09:00:00' WHERE day=?", (D1,))
        con.commit()
    st, j = mine("shivani")
    ok("7  a ticked line leaves the staff's list (it waits for the re-export)", j.get("open") == 2)
    with app.app_context():
        c1 = DC.check_day(W.db(), D1)
    ok("8  every Docterz line ticked: his line reads 'Re-export 22-Oct from Docterz'",
       DC.summary_en(c1) == "22-Oct: Re-export 22-Oct from Docterz · 1 parchi to fix")
    with app.app_context():
        con = W.db()
        con.execute("UPDATE clinic_day_revenue SET taken_at='2026-10-23 21:30:00' WHERE business_date=?", (D1,))
        con.execute("INSERT INTO clinic_day_line (business_date,section,sn,patient,clinic_id,amount_p,mode) VALUES (?,?,?,?,?,?,?)",
                    (D1, "xray", 9, "Patient A8", "9108", 60000, "Cash"))   # the re-export carries the one added line, not the rest
        con.commit()
        c1 = DC.check_day(con, D1)
    ok("9  after the re-export: the fixed line is gone, the others come back 'not fixed'",
       c1.get("not_fixed") == 3 and DC.summary_en(c1).endswith("3 not fixed after the re-export"))
    st, j = mine("shivani")
    ok("10 ... back on the staff's list as 'Phir se'", j.get("open") == 5 and "Phir se" in (j.get("text") or ""))
    W.CUR["user"] = "shivani"
    h = cl.get("/finance/clinic/check/%s" % D1).get_data(as_text=True)
    ok("11 the card says it was not fixed, and its buttons are back", ("Theek nahi hua" in h) and ("Badal diya" in h))
    # the duty files
    sys.modules.pop("aaj_seed", None)
    import aaj_seed as S
    lines = {ln["id"]: ln for p in S.PEOPLE for ln in p["lines"]}
    ok("12 the seed carries the two new lines (reception, Shavez)", "reception.day_check" in lines and "shavez.day_check" in lines)
    try:
        x = json.load(open(os.path.join(NEW, "aaj_duties.json"), encoding="utf-8"))
        du = {d["id"]: d for d in x["extra"]}
    except Exception:                                    # noqa: BLE001
        du = {}
    f = (du.get("reception.day_check") or {}).get("fetch") or {}
    ok("13 the duties file reads them from the day check's own door, with its words", f.get("url") == "/finance/clinic/check/api/mine"
       and f.get("text_field") == "text" and (du.get("shavez.day_check") or {}).get("door") == "/finance/clinic/check/mine")
    try:
        import aaj_kaam as AK
        p = next(q for q in S.PEOPLE if q["key"] == "reception")
        merged = AK._merge(p, {"on": True, "lines": [{"id": ln["id"], "hi": ln["hi"], "en": ln["en"], "when": ln["when"], "on": True}
                                                      for ln in p["lines"] if ln["id"] != "reception.day_check"]})
        nl = next(ln for ln in merged["lines"] if ln["id"] == "reception.day_check")
        ok("14 on his saved panel a new line arrives OFF and marked new (his switch)", nl.get("on") is False and nl.get("new") is True)
    except Exception:                                    # noqa: BLE001
        ok("14 on his saved panel a new line arrives OFF and marked new (his switch)", False)
    try:
        html = open(os.path.join(NEW, "aaj_kaam.html"), encoding="utf-8").read()
    except OSError:
        html = ""
    ok("15 the list page shows a door's own words when it sends them", "r.fetch.text_field&&d[r.fetch.text_field]" in html)
    # older behaviour
    st, h = 0, ""
    W.CUR["user"] = "manoj"
    r = cl.get("/finance/clinic/check/%s" % D2)
    ok("A  (older) the day check page opens", r.status_code == 200, s640=False)
    ok("B  (older) the 07-Oct shape still reads its money line", "Docterz entry missing" in r.get_data(as_text=True), s640=False)
    DC.dt.date = real_today
    red = [n for n, c, _s in RES if not c]
    green = len(RES) - len(red)
    if OLD:
        print("%d S640 check(s) red · %d older red · %d green" % (len([1 for n, c, s in RES if not c and s]),
                                                                   len([1 for n, c, s in RES if not c and not s]), green))
    else:
        print("%d of %d green" % (green, len(RES)))


if __name__ == "__main__":
    try:
        main()
    finally:
        import shutil
        shutil.rmtree(W.TMP, ignore_errors=True)
