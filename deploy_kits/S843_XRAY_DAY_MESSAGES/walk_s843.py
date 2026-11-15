#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s843.py -- the walk for kit S843_XRAY_DAY_MESSAGES (session 469). Made-up data only; no patient anywhere.
  python3 walk_s843.py <kit dir>                 the walk -> last line 'WALK OK n/n'
  python3 walk_s843.py <kit dir> --control       five broken copies of the module -> last line 'CONTROL: red 5/5'
  python3 walk_s843.py <kit dir> --live <fin dir> <db> <day...>   live shape: the module's counts against records' own rule
                                                  on a copy (counts only; the copy's md5 must not move)
"""
import hashlib
import importlib.util
import json
import os
import sqlite3
import subprocess
import sys
import tempfile

KDIR = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
SRC = os.path.join(KDIR, "xray_day_messages.py")


def load(path, fin):
    os.environ["XD_FIN_DIR"] = fin
    os.environ["XD_STATE"] = os.path.join(fin, "state.json")
    spec = importlib.util.spec_from_file_location("xdm_%d" % abs(hash(path + fin)), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def row(st, sh, name="Made Up", cid="900001"):
    return {"cid": cid, "name": name, "st": st, "sh": sh, "sh_en": ""}


def summ(rows):
    return {"n": len(rows), "rows": rows}


def strip(ty, yy, tb=()):
    return [{"day": "2026-01-10", "dshort": "10-Jan", "today": True, "x": summ(list(ty)), "b": summ(list(tb))},
            {"day": "2026-01-09", "dshort": "09-Jan", "today": False, "x": summ(list(yy)), "b": summ([])}]


def checks(m, fin):
    ok, bad = [], []

    def t(name, cond):
        (ok if cond else bad).append(name)

    # ---- the morning
    kal = {"day": "2026-01-09", "dshort": "09-Jan", "n": 8, "filed": 6, "rows": [row("pending", "subah"), row("notdue", "shaam")],
           "older": [row("pending", "subah")]}
    tx, c = m.morning_text([], kal, "2026-01-10")
    s = tx.get("staff", ("", ""))
    t("m1 title counts", s[0] == "📷 X-ray 9 Jan: 8 mein se 6 ki photo aa gayi")
    t("m2 body yesterday by 3 pm + older", s[1] == "2 baaki — aaj 3 baje tak upload kijiye. Pichhle 7 din se 1 aur baaki. Naam ke liye dabaiye.")
    t("m3 counts", c["n"] == 8 and c["rest"] == 2 and c["older"] == 1)
    t("m4 only staff", set(tx) == {"staff"})
    k2 = dict(kal, day="2026-01-07", rows=[row("pending", "subah")], filed=2, older=[])
    tx, c = m.morning_text([], k2, "2026-01-10")
    t("m5 an older day says abhi", tx["staff"][1].startswith("1 baaki — abhi upload kijiye.") and "Pichhle" not in tx["staff"][1])
    t("m6 its N is filed + rest", tx["staff"][0] == "📷 X-ray 7 Jan: 3 mein se 2 ki photo aa gayi")
    k3 = dict(kal, rows=[], filed=5, older=[])
    tx, c = m.morning_text([], k3, "2026-01-10")
    t("m7 all in, nothing older", tx["staff"] == ("✅ X-ray 9 Jan: sab 5 ki photo aa gayi", "Pichhle 7 din se kuch baaki nahi."))
    k4 = dict(k3, older=[row("pending", "subah"), row("pending", "shaam")])
    tx, c = m.morning_text([], k4, "2026-01-10")
    t("m8 all in, older baaki", tx["staff"][1] == "Pichhle 7 din se 2 baaki. Naam ke liye dabaiye.")
    tx, c = m.morning_text([], None, "2026-01-10")
    t("m9 no X-ray day -> silent", tx == {})
    tx, c = m.morning_text([], dict(k3, day="2026-01-07"), "2026-01-10")
    t("m10 older day, nothing baaki -> silent", tx == {})
    tx, c = m.morning_text([], dict(k3, day="2026-01-07", older=[row("pending", "")]), "2026-01-10")
    t("m11 older day with older baaki -> sent", "staff" in tx)
    t("m12 no name or ID in any morning text", all("Made" not in x and "900001" not in x for x in tx["staff"]))
    tx, c = m.morning_text([], kal, "2026-01-11")
    t("m13 Sunday -> silent", tx == {})
    tx, c = m.morning_text([], dict(kal, rows=[], filed=0, older=[row("pending", "subah")]), "2026-01-10")
    t("m14 all 'not done', older baaki -> the older only", tx.get("staff") == ("📷 X-ray: pichhle 7 din se 1 baaki", "Naam ke liye dabaiye."))
    tx, c = m.morning_text([], dict(kal, rows=[], filed=0, older=[]), "2026-01-10")
    t("m15 all 'not done', nothing older -> silent", tx == {})

    # ---- the evening
    yy = [row("filed", "shaam"), row("filing", "shaam"), row("pending", ""), row("filed", "subah"), row("notdone", "shaam"),
          row("notdue", "shaam")]
    ty = [row("filed", "subah"), row("issue", "subah"), row("notdue", "shaam"), row("pending", "")]
    tb = [row("in", ""), row("in", ""), row("notdue", ""), row("answered", "")]
    tx, c = m.evening_text(strip(ty, yy, tb), 3)
    t("e1 due = yday evening + yday Docterz-only + today morning (not yday morning, not today evening, not not-done)",
      c["x_due"] == 6 and c["x_yday_evening"] == 4 and c["x_today_morning"] == 2)
    t("e2 in counts filed and filing", c["x_in"] == 3 and c["x_issue"] == 1 and c["x_miss"] == 2)
    t("e3 staff title", tx["staff"][0] == "📷 Aaj ki upload: 6 mein se 3 file — 3 baaki")
    t("e4 staff body", tx["staff"][1] == "2 ki photo nahi aayi, 1 mein dikkat. Kal 3 baje tak. Naam ke liye dabaiye.")
    t("e5 owner title", tx["owner"][0] == "Records today: X-rays 3 of 6 filed · Blood 2 of 4 in")
    t("e6 owner body", tx["owner"][1] == "2 X-rays pending · 1 X-ray photo needs a check · 2 blood reports not in yet · Check karein: 3 questions open.")
    tx, c = m.evening_text(strip([row("filed", "subah")], [row("filed", "shaam"), row("filing", "shaam")]), 0)
    t("e7 all in", tx["staff"] == ("✅ Aaj ki upload: 3 mein se 3 photo file ho gayi", "Kal shaam ki 2 aur aaj subah ki 1 — sab aa gayi."))
    t("e8 owner all in, nothing open", tx["owner"] == ("Records today: X-rays 3 of 3 filed", "Check karein: nothing open."))
    tx, c = m.evening_text(strip([row("filed", "subah")], []), 1)
    t("e9 only this morning's", tx["staff"][1] == "Aaj subah ki 1 — sab aa gayi." and tx["owner"][1] == "Check karein: 1 question open.")
    tx, c = m.evening_text(strip([row("notdue", "shaam")], [row("filed", "subah")]), 4)
    t("e10 nothing due, no blood -> silent", tx == {})
    tx, c = m.evening_text(strip([], [], [row("in", "")]), 0)
    t("e11 blood only -> him only", set(tx) == {"owner"} and tx["owner"][0] == "Records today: Blood 1 of 1 in")
    t("e12 a strip whose first day is not today -> nothing from 'yesterday'",
      m.due_today([dict(strip([], [row("filed", "shaam")])[1])])[0] == [])
    tx, c = m.evening_text(strip([], [row("pending", "shaam")]), 2)
    t("e14 no X-ray and no blood test today (a closed Sunday) -> silent", tx == {})
    sh = {("2026-01-10", "900001"): "morning", ("2026-01-09", "900001"): "morning"}
    tx, c = m.evening_text(strip([row("filed", "")], [row("filed", "")]), 0, sh)
    t("e15 Docterz-only lines by their shift: today's morning due, yesterday's morning not", c["x_due"] == 1 and c["x_today_morning"] == 1)
    tx, c = m.evening_text(strip([row("filed", "")], [row("pending", "")]), 0)
    t("e16 Docterz-only, no shift read: yesterday's due, today's not", c["x_due"] == 1 and c["x_yday_evening"] == 1 and c["x_miss"] == 1)
    t("e13 no name or ID in any evening text", all("Made" not in x and "900001" not in x for v in
                                                  m.evening_text(strip(ty, yy, tb), 3)[0].values() for x in v))

    # ---- the push
    calls = []

    def pusher(who, p):
        calls.append((who, p))
        return 1, 0
    out = m.send({"staff": ("a", "b"), "owner": ("c", "d")}, pusher)
    t("p1 staff to reception, shivani, alisha only", [w for w, p in calls if p["title"] == "a"] == ["reception", "shivani", "alisha"])
    t("p2 owner to manoj only", [w for w, p in calls if p["title"] == "c"] == ["manoj"])
    t("p3 urls", all(p["url"] == ("/finance/checks" if p["title"] == "a" else "/finance/records/xray-check") for w, p in calls))
    t("p4 the notice's slot", all(p["tag"] == "xray-photo" for w, p in calls) and out["manoj"] == [1, 0])
    calls.clear()
    m.send({"owner": ("c", "d")}, pusher)
    t("p5 owner-only text reaches no staff", [w for w, p in calls] == ["manoj"])

    # ---- the run: switches, faults
    calls.clear()
    os.makedirs(os.path.join(fin, "_off"), exist_ok=True)
    open(os.path.join(fin, "_off", "xray_day_messages"), "w").close()
    m.build = lambda mode: ({"staff": ("x", "y")}, {})
    rc = m.run("morning", pusher=pusher)
    st = json.load(open(os.path.join(fin, "state.json")))
    t("r1 the switch stops it", rc == 0 and calls == [] and str(st.get("sent", "")).startswith("off:"))
    os.remove(os.path.join(fin, "_off", "xray_day_messages"))
    open(os.path.join(fin, "_off", "ALL_OFF"), "w").close()
    m.run("evening", pusher=pusher)
    t("r2 ALL_OFF stops it", calls == [])
    os.remove(os.path.join(fin, "_off", "ALL_OFF"))
    m.run("morning", pusher=pusher)
    t("r3 on: sent to the three", [w for w, p in calls] == ["reception", "shivani", "alisha"])
    calls.clear()

    def boom(mode):
        raise RuntimeError("attempt to write a readonly database")
    m.build = boom
    rc = m.run("evening", pusher=pusher)
    st = json.load(open(os.path.join(fin, "state.json")))
    t("r4 a fault sends nothing and is recorded by its type only", rc == 1 and calls == [] and st.get("error") == "RuntimeError")
    m.build = lambda mode: ({}, {"x_due": 0})
    m.run("evening", pusher=pusher)
    st = json.load(open(os.path.join(fin, "state.json")))
    t("r5 silent day: nothing sent, recorded", calls == [] and st.get("sent") == "silent")
    t("r6 a wrong mode does nothing", m.run("noon", pusher=pusher) == 2 and calls == [])
    return ok, bad


def walk(path):
    with tempfile.TemporaryDirectory() as fin:
        m = load(path, fin)
        return checks(m, fin)


MUT = [("notdue counted as in", 'IN_ST = ("filed", "filing")', 'IN_ST = ("filed", "filing", "notdue")'),
       ("today's evening X-rays counted due", 'if sh(t, r) == "subah" and r["st"] not in GONE_ST]',
        'if sh(t, r) in ("subah", "shaam") and r["st"] not in GONE_ST]'),
       ("the error's text kept", 'st["error"] = type(e).__name__', 'st["error"] = str(e)'),
       ("Shavez added to reception", 'RECEPTION = ("reception", "shivani", "alisha")', 'RECEPTION = ("reception", "shivani", "alisha", "shavez")'),
       ("the switch ignored", "if off and not dry:", "if False:")]


def control():
    reds = 0
    src = open(SRC, encoding="utf-8").read()
    for name, a, b in MUT:
        assert src.count(a) == 1, "mutation anchor not found once: " + name
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "xray_day_messages.py")
            open(p, "w", encoding="utf-8").write(src.replace(a, b))
            ok, bad = walk(p)
            print("  %-40s %s" % (name, "RED (%d failed)" % len(bad) if bad else "GREEN -- the walk did not see it"))
            reds += bool(bad)
    print("CONTROL: red %d/%d" % (reds, len(MUT)) if reds == len(MUT) else "CONTROL: NOT RED %d/%d" % (reds, len(MUT)))


def live(fin, db, days):
    """Each day D at 19:00: the module's x_due / x_in against records' own XRAY_DUE + the 2-day photo window, read here
    from the copy (Docterz-only lines of D-1 added; 'not done' answers removed). Counts only. The copy must not move."""
    h0 = hashlib.md5(open(db, "rb").read()).hexdigest()
    sys.path.insert(0, fin)
    import records as R                                  # noqa: PLC0415
    con = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
    con.row_factory = sqlite3.Row
    good = True
    for d in days:
        env = dict(os.environ, RECORDS_NOW=d + " 19:00:00", XD_FIN_DIR=fin, FINANCE_DB=db, XD_STATE="/dev/null")
        out = subprocess.run([sys.executable, "-s", SRC, "evening", "--dry"], env=env, capture_output=True, text=True).stdout
        cnt = json.loads(out.split(" counts ", 1)[1].split("\n", 1)[0]) if " counts " in out else {}
        y = (__import__("datetime").date.fromisoformat(d) - __import__("datetime").timedelta(days=1)).isoformat()
        due = {(r[0], r[1]) for r in con.execute(
            "SELECT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id AND i.kind='xray' WHERE s.series='xp' "
            "AND s.state='ok' AND s.clinic_id<>'' AND s.day IN (?, ?) AND " + R.XRAY_DUE + " = ?", (y, d, d + " 15:00:00"))}
        for dd, want in ((y, "evening"), (d, "morning")):
            slips = {r[0] for r in con.execute("SELECT DISTINCT s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id AND "
                                               "i.kind='xray' WHERE s.series='xp' AND s.state='ok' AND s.clinic_id<>'' AND s.day=?", (dd,))}
            for (cid,) in con.execute("SELECT DISTINCT clinic_id FROM clinic_day_line WHERE section='xray' AND clinic_id<>'' "
                                      "AND business_date=?", (dd,)):
                if cid in slips:
                    continue
                f = con.execute("SELECT COALESCE((SELECT MIN(lower(trim(shift))) FROM clinic_day_line WHERE business_date=? AND "
                                "clinic_id=? AND section='xray' AND lower(trim(shift)) IN ('morning','evening')), (SELECT "
                                "MIN(lower(trim(shift))) FROM clinic_day_line WHERE business_date=? AND clinic_id=? AND "
                                "lower(trim(shift)) IN ('morning','evening')), 'evening')", (dd, cid, dd, cid)).fetchone()[0]
                if f == want:
                    due.add((dd, cid))
        nd = {k for k in due if con.execute("SELECT 1 FROM record_check WHERE key=? AND answer='not_done'",
                                            ("xm:%s:%s" % k,)).fetchone()}
        due -= nd
        filed = {k for k in due if con.execute("SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? "
                                               "AND day>=? AND day<=date(?, '+2 day')", (k[1], k[0], k[0])).fetchone()}
        same = cnt.get("x_due") == len(due) and cnt.get("x_in", -1) >= len(filed)
        good &= same
        print("  %s 19:00  module due %s in %s | records' rule due %d filed %d  %s" % (
            d, cnt.get("x_due"), cnt.get("x_in"), len(due), len(filed), "same" if same else "DIFFERENT"))
    h1 = hashlib.md5(open(db, "rb").read()).hexdigest()
    print("  the copy's md5 %s -> %s %s" % (h0[:8], h1[:8], "unchanged" if h0 == h1 else "CHANGED"))
    print("LIVE SHAPE OK" if good and h0 == h1 else "LIVE SHAPE NOT OK")


if __name__ == "__main__":
    a = sys.argv[2:]
    if a[:1] == ["--control"]:
        control()
    elif a[:1] == ["--live"]:
        live(a[1], a[2], a[3:])
    else:
        ok, bad = walk(SRC)
        for b in bad:
            print("BAD", b)
        n = len(ok) + len(bad)
        print("WALK OK %d/%d" % (n, n) if not bad else "WALK NOT OK %d/%d" % (len(ok), n))
