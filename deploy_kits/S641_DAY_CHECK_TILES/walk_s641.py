#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""walk_s641.py -- the LIVE-SHAPE walk of kit S641_DAY_CHECK_TILES. Made-up patients, a temp database (S636's days).

    python3 walk_s641.py <dir with the NEW day_check.py, clinic_money.py, aaj_seed.py, owner_console.py, portal.py>
                         <dir with the rest (/root/finance)> [--old]

Morning match on the 22-Oct shape: no counter-vs-Docterz flag to explain in words, a line pointing to the day check, no
'almost certainly' guess, the verdict never 'agree'; without day_check.py beside it, the old flag is back (older behaviour
kept). The day check page shows the bank part; the owner's tile lands on the oldest day with lines; Morning match is off
reception's list; the two tiles sit in their sections. --old on the live files: exactly the S641 checks go red."""
import ast
import os
import sys

NEW, REST = sys.argv[1], sys.argv[2]
OLD = "--old" in sys.argv
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], NEW, REST] + (["--old"] if OLD else [])
sys.path[:0] = [NEW, HERE, REST]
import walk_s636 as W                                     # noqa: E402

import flask                                              # noqa: E402

RES = []


def ok(name, cond, s641=True):
    RES.append((name, bool(cond), s641))
    print(("  ok   " if cond else "  RED  ") + name)


def main():
    import clinic_register as CR
    import clinic_money as CM
    import day_check as DC
    app = flask.Flask("walk")
    CR.init(app, W.db, W.require, W.audit, unit="clinic")
    try:
        CM.init(app, W.db, W.require, W.audit, unit="clinic")
    except Exception:                                    # noqa: BLE001
        pass
    with app.app_context():
        W.seed(W.db())
        m = CM.match_day(W.db(), W.D1)
    codes = [f["code"] for f in m["flags"]]
    ok("1  Morning match no longer asks for the counter-vs-Docterz total in words", "total_diff" not in codes)
    ok("2  ... it points to the day check instead", any("explained patient by patient on the day check" in n for n in m["notes"]))
    ok("3  ... and never says the records agree while they differ", "day check" in " ".join(m["lines"]) and m["verdict"] in ("day_check", "flags"))
    ok("4  no 'almost certainly <patient>' guess", not any(e["code"] == "rung_as_cash" for e in m["explained"]))
    real_imp = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

    def no_dc(name, *a, **k):
        if name == "day_check":
            raise ImportError("hidden by the walk")
        return real_imp(name, *a, **k)
    import builtins
    builtins.__import__ = no_dc
    try:
        with app.app_context():
            m0 = CM.match_day(W.db(), W.D1)
    finally:
        builtins.__import__ = real_imp
    ok("A  (older) without day_check.py beside it, Morning match is exactly as before", "total_diff" in [f["code"] for f in m0["flags"]],
       s641=False)
    cl = app.test_client()
    real_today = DC.dt.date

    class _D(real_today):                                 # 'today' is the day after the 22-Oct shape
        @classmethod
        def today(cls):
            return real_today(2026, 10, 23)
    DC.dt.date = _D
    W.CUR["user"] = "shivani"
    h = cl.get("/finance/clinic/check/%s" % W.D1).get_data(as_text=True)
    ok("5  the day check shows the bank part, the same for staff", "<h3 class='grp'>Bank</h3>" in h and "Bank:" in h)
    W.CUR["user"] = "manoj"
    h2 = cl.get("/finance/clinic/check/%s" % W.D1).get_data(as_text=True)
    ok("6  ... and for the owner", "<h3 class='grp'>Bank</h3>" in h2)
    r = cl.get("/finance/clinic/check/mine")
    ok("7  his tile lands on the oldest day of the week that still has lines", r.status_code == 302
       and r.headers.get("Location", "").endswith("/finance/clinic/check/%s#check" % W.D3))
    with app.app_context():
        r2 = cl.get("/finance/clinic/match/%s" % W.D1)
    ok("B  (older) the Morning match page still opens", r2.status_code in (200, 302), s641=False)
    DC.dt.date = real_today
    sys.modules.pop("aaj_seed", None)
    import aaj_seed as S
    rec = next((ln for p in S.PEOPLE if p["key"] == "reception" for ln in p["lines"] if ln["id"] == "rec.match"), None)
    ok("8  Morning match is off reception's list (the line stays on his panel, switched off)", rec is not None and rec["on"] is False)
    try:
        oc = open(os.path.join(NEW, "owner_console.py"), encoding="utf-8").read()
    except OSError:
        oc = ""
    ok("9  his console words the new verdict", '"day_check": ("see the day check", "w")' in oc)
    tiles, groups = [], {}
    try:
        tree = ast.parse(open(os.path.join(NEW, "portal.py"), encoding="utf-8").read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                keys = [k.value for k in node.keys if isinstance(k, ast.Constant)]
                if "name" in keys and "url" in keys:
                    dd = {k.value: v for k, v in zip(node.keys, node.values) if isinstance(k, ast.Constant)}
                    try:
                        tiles.append((ast.literal_eval(dd["name"]), ast.literal_eval(dd["url"]), ast.literal_eval(dd.get("roles", ast.Constant([])))))
                    except Exception:                    # noqa: BLE001
                        pass
            if isinstance(node, ast.Assign) and any(getattr(t, "id", "") == "_TILE_GROUP" for t in node.targets):
                groups = ast.literal_eval(node.value)
    except Exception:                                    # noqa: BLE001
        pass
    ok("10 a Day check tile for the doctor, in Docterz & clinic day", ("Day check", "/finance/clinic/check/mine", ["doctor"]) in tiles
       and groups.get("Day check") == "Docterz & clinic day")
    ok("11 a Parchi desk tile for the doctor, in Patients", ("Parchi desk", "/finance/slips/desk", ["doctor"]) in tiles
       and groups.get("Parchi desk") == "Patients")
    ok("C  (older) the existing slips tile is unchanged", ("OPD & X-ray/Proc Slips", "/finance/slips", ["doctor"]) in tiles, s641=False)
    red = [n for n, c, _s in RES if not c]
    green = len(RES) - len(red)
    if OLD:
        print("%d S641 check(s) red · %d older red · %d green" % (len([1 for n, c, s in RES if not c and s]),
                                                                   len([1 for n, c, s in RES if not c and not s]), green))
    else:
        print("%d of %d green" % (green, len(RES)))


if __name__ == "__main__":
    try:
        main()
    finally:
        import shutil
        shutil.rmtree(W.TMP, ignore_errors=True)
