#!/usr/bin/env python3
"""probe_s977.py -- the live shape of kit S977 on a COPY of finance.db (never the live one): the last 60 days checked by the
old code, by the new code with DAYCHK_REVENUE=0 (must equal the old exactly) and by the new code as installed (counts only;
0 errors; the day's sum holds on every day). Prints counts, never a name or a number of a patient. Last line ALL PASS | RED.
    probe_s977.py OLD_FINANCE_DIR NEW_FINANCE_DIR DB_COPY"""
import sys, os, json, hashlib, subprocess, shutil, tempfile, collections, datetime as dt

def dump(fin, db, rev):
    os.environ["DAYCHK_REVENUE"] = rev
    os.environ["EVCHK_LIVE_DB"] = "/nonexistent/live.db"
    sys.path.insert(0, fin)
    import sqlite3
    import day_check as dc
    con = sqlite3.connect(db); con.row_factory = sqlite3.Row
    lo = (dt.date.today() - dt.timedelta(days=61)).isoformat()
    days = [r[0] for r in con.execute("SELECT business_date FROM clinic_register_day WHERE business_date>=? ORDER BY 1", (lo,))]
    h, kinds, err, bad, clean = hashlib.md5(), collections.Counter(), 0, 0, 0
    for d in days:
        try:
            c = dc.check_day(con, d)
        except Exception as ex:                          # noqa: BLE001
            err += 1; continue
        _sl = c.pop("s977_left", None); c.pop("rev", None); (c.get("counts") or {}).pop("less", None)
        if _sl is not None:
            c["s977_left"] = _sl
        h.update(json.dumps(c, sort_keys=True, default=str).encode())
        if c.get("state") != "checked":
            continue
        tp = c["top"]
        if tp["reg"] != tp["doc"] + tp["nid"] - tp["back"] + tp["missing"] + tp["left"]:
            bad += 1
        if rev == "1" and c.get("rev") is not False and "s977_left" in c and c["s977_left"] != tp["left"]:
            bad += 1                                     # review S10: the card's figure is the page's one line
        if dc.is_clean(c):
            clean += 1
        for x in c["cards"]:
            kinds[x["kind"]] += 1
    print(json.dumps(dict(days=len(days), md5=h.hexdigest(), cards=sum(kinds.values()), kinds=dict(kinds), err=err, bad=bad, clean=clean)))

def run(fin, db, rev):
    t = tempfile.mkdtemp(prefix="p977_"); cp = os.path.join(t, "c.db")
    shutil.copyfile(db, cp); os.chmod(cp, 0o600)
    try:
        o = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--dump", fin, cp, rev], capture_output=True, text=True, timeout=900)
        return json.loads(o.stdout.strip().splitlines()[-1])
    finally:
        shutil.rmtree(t, ignore_errors=True)

if __name__ == "__main__":
    if sys.argv[1:2] == ["--dump"]:
        dump(sys.argv[2], sys.argv[3], sys.argv[4]); sys.exit(0)
    old, new, db = sys.argv[1:4]
    a, b0, b1 = run(old, db, "1"), run(new, db, "0"), run(new, db, "1")
    print("LIVE days %d . old cards %d %s . new cards %d %s . clean %d -> %d . errors %d/%d/%d . sum broken %d" % (
        a["days"], a["cards"], a["kinds"], b1["cards"], b1["kinds"], a["clean"], b1["clean"], a["err"], b0["err"], b1["err"], b1["bad"]))
    red = []
    if b0["md5"] != a["md5"]: red.append("switch off differs from the old code")
    if a["err"] or b0["err"] or b1["err"]: red.append("errors")
    if b1["bad"]: red.append("the day's sum broken")
    if any(k in b1["kinds"] for k in ("mode", "missing", "notbilled")): red.append("a mode / Docterz-edit card under the revenue match")
    print("ALL PASS" if not red else "RED: " + "; ".join(red))
    sys.exit(0 if not red else 1)
