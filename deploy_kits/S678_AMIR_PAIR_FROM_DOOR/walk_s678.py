#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s678.py -- the walk of kit S678_AMIR_PAIR_FROM_DOOR.

    python3 -B walk_s678.py --new <root> --lib <root> --db <copy> --scratch <dir> [--old-root <root> --since YYYY-MM-DD]
    python3 -B walk_s678.py --old <root> --lib <root> --db <copy> --scratch <dir>          (the control: the live file must go red)

<root>/finance/amir_day.py is the file under test; --lib is where its neighbours live (purchase_app, expiry_watch ...).  --db is a
WRITABLE COPY of finance.db (never the live one): the walk writes only its OWN rows -- day 2099-01-15, md5s beginning 'walk678', user
WALK678 -- found by key, never by counting (F-998), and removes them again.  With --old-root, the old = new proof: every day since --since
that has a step-3 tap or a purchase export is judged under the OLD and the NEW file on the copy's real rows -- identical, or the one
allowed difference (the new file says "at the server" where the old said "not received" while the door held a covering file).
Last line: "N of N green" (new) or "K S678 check(s) red . M green" (old).
"""
import argparse
import importlib.util
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
DAY = "2099-01-15"
FIRST = "2099-01-01"
STAMPDAY = "20990115"
USER = "WALK678"


def load(root, lib, scratch, tag):
    mod_dir = os.path.join(scratch, "mod_" + tag)
    os.makedirs(mod_dir, exist_ok=True)
    shutil.copyfile(os.path.join(root, "finance", "amir_day.py"), os.path.join(mod_dir, "amir_day.py"))
    for p in (os.path.join(lib, "finance", "spine"), os.path.join(lib, "finance")):
        if p not in sys.path:
            sys.path.append(p)
    sys.path.insert(0, mod_dir)
    spec = importlib.util.spec_from_file_location("amir_day_" + tag, os.path.join(mod_dir, "amir_day.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    sys.path.remove(mod_dir)
    return m


def now_minus(minutes):
    return (datetime.now(IST) - timedelta(minutes=minutes)).strftime("%Y-%m-%d %H:%M:%S")


def clean(cx):
    cx.execute("DELETE FROM mi_file WHERE md5 LIKE 'walk678%'")
    cx.execute("DELETE FROM purchase_export WHERE md5 LIKE 'walk678%'")
    cx.execute("DELETE FROM amir_step_log WHERE day=? AND by_user=?", (DAY, USER))
    cx.commit()


def door(cx, kind, n, frm=FIRST, to=DAY, stampday=STAMPDAY, verdict="VERIFIED", hhmmss="090735"):
    cx.execute("INSERT INTO mi_file (md5, type, variant, date_from, date_to, verdict, stamp, received_at, source) "
               "VALUES (?,?,?,?,?,?,?,?,?)",
               ("walk678d%02d%s" % (n, kind.lower()), "PURCHASE_" + kind, "DEFAULT", frm, to, verdict,
                "%s-%s" % (stampday, hhmmss), "%s-%s-%sT09:07:38+05:30" % (stampday[:4], stampday[4:6], stampday[6:]), "push"))


def pe(cx, kind, n, frm=FIRST, to=DAY):
    pe_at(cx, kind, n, frm, to, "090800")


def pe_at(cx, kind, n, frm=FIRST, to=DAY, hhmmss="090800"):
    cx.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, superseded_by) "
               "VALUES (?,?,?,?,?,?,?,?,NULL)",
               ("walk678p%02d%s" % (n, kind.lower()), kind, "WALK678.XLS", frm, to, STAMPDAY + "-" + hhmmss, DAY + "T09:43:22", 7))


def tap3(cx, minutes):
    cx.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note) VALUES (?,?,?,?,?)", (DAY, 3, now_minus(minutes), USER, ""))


def tap2(cx, at):
    cx.execute("INSERT INTO amir_step_log (day, step, done_at, by_user, note) VALUES (?,?,?,?,?)", (DAY, 2, at, USER, ""))


def states(m, cx, ws):
    return {e["kind"]: e for e in m._export_state(cx, DAY, ws)}


def run_cases(m, cx):
    """Each check: (name, passed, is_s678) -- is_s678 marks a check the OLD file must fail."""
    res = []
    old_ws = now_minus(20)

    def case(name, setup, ws, judge, s678):
        clean(cx)
        setup()
        cx.commit()
        try:
            ok = bool(judge(states(m, cx, ws)))
        except Exception as e:                                         # noqa: BLE001
            ok = False
            name += " (raised %s)" % type(e).__name__
        res.append((name, ok, s678))

    def both_door():
        door(cx, "ITEMWISE", 1)
        door(cx, "BILLWISE", 2)

    case("A  both reports at the door, none in purchase_export, tap 20 min ago -> both WAIT with the door's time",
         both_door, old_ws,
         lambda s: all(s[k]["state"] == "wait" and s[k].get("door") == "09:07" and "server par 09:07" in s[k]["reason"]
                       and "at the server since 09:07" in s[k]["reason_en"] for k in ("ITEMWISE", "BILLWISE")), True)
    case("B  nothing anywhere, tap 20 min ago -> both BAD 'nahi aayi' (unchanged)",
         lambda: None, old_ws, lambda s: all(s[k]["state"] == "bad" and "nahi aayi" in s[k]["reason"] for k in s), False)
    case("C  both in purchase_export covering -> both OK (unchanged)",
         lambda: (pe(cx, "ITEMWISE", 3), pe(cx, "BILLWISE", 4), both_door()), old_ws,
         lambda s: all(s[k]["state"] == "ok" and s[k]["have"] for k in s), False)
    case("D  door file NOT covering the 1st..day -> not counted, BAD",
         lambda: door(cx, "ITEMWISE", 5, frm="2099-01-02") or door(cx, "BILLWISE", 6, to="2099-01-14"), old_ws,
         lambda s: all(s[k]["state"] == "bad" and not s[k].get("door") for k in s), False)
    case("E  door file stamped ANOTHER day -> not counted, BAD",
         lambda: door(cx, "ITEMWISE", 7, stampday="20990114") or door(cx, "BILLWISE", 8, stampday="20990114"), old_ws,
         lambda s: all(s[k]["state"] == "bad" and not s[k].get("door") for k in s), False)
    case("F  door file REFUSED -> not counted, BAD",
         lambda: door(cx, "ITEMWISE", 9, verdict="REFUSED") or door(cx, "BILLWISE", 10, verdict="UNKNOWN"), old_ws,
         lambda s: all(s[k]["state"] == "bad" and not s[k].get("door") for k in s), False)
    case("G  purchase_export holds only an OLDER non-covering export, the door a newer covering one -> WAIT with the door",
         lambda: (pe_at(cx, "ITEMWISE", 11, to="2099-01-10", hhmmss="090000"), door(cx, "ITEMWISE", 12), pe(cx, "BILLWISE", 13),
                  door(cx, "BILLWISE", 14)),
         old_ws, lambda s: s["ITEMWISE"]["state"] == "wait" and s["ITEMWISE"].get("door") and s["BILLWISE"]["state"] == "ok", True)
    case("H  no tap yet, both at the door -> WAIT with the door (never 'abhi nikaali nahi gayi')",
         both_door, None, lambda s: all(s[k]["state"] == "wait" and s[k].get("door") for k in s), True)
    case("I  inside the six minutes, nothing anywhere -> WAIT without a door (unchanged)",
         lambda: None, now_minus(1), lambda s: all(s[k]["state"] == "wait" and not s[k].get("door") for k in s), False)
    case("J  only the bill-wise at the door -> bill-wise WAIT, item-detail BAD",
         lambda: door(cx, "BILLWISE", 15), old_ws,
         lambda s: s["BILLWISE"]["state"] == "wait" and s["BILLWISE"].get("door") and s["ITEMWISE"]["state"] == "bad", True)
    case("K  two door files of the day -> the NEWEST stamp's time is shown",
         lambda: (door(cx, "ITEMWISE", 16, hhmmss="090801"), door(cx, "ITEMWISE", 17, hhmmss="092504"),
                  door(cx, "BILLWISE", 18)), old_ws,
         lambda s: s["ITEMWISE"].get("door") == "09:25", True)

    case("R  the door's file is OLDER than a bill tapped in after it (step 2 at 10:00) -> not counted, BAD (the re-export band rules)",
         lambda: (both_door(), tap2(cx, DAY + " 10:00:00")), old_ws,
         lambda s: all(s[k]["state"] == "bad" and not s[k].get("door") for k in s), False)
    case("S  a door file with an EMPTY start date -> not counted, BAD",
         lambda: door(cx, "ITEMWISE", 23, frm="") or door(cx, "BILLWISE", 24, frm=""), old_ws,
         lambda s: all(s[k]["state"] == "bad" and not s[k].get("door") for k in s), False)
    case("T  purchase_export's non-covering export is NEWER than the door's covering file -> its own reading, BAD 'tareekh galat'",
         lambda: (door(cx, "ITEMWISE", 25, hhmmss="090735"), pe_at(cx, "ITEMWISE", 26, to="2099-01-10", hhmmss="110000"),
                  pe(cx, "BILLWISE", 27)), old_ws,
         lambda s: s["ITEMWISE"]["state"] == "bad" and "tareekh" in s["ITEMWISE"]["reason"] and not s["ITEMWISE"].get("door"), False)

    # a PAST day keeps its own reading: a covering door file of 15-01-2000 does not turn that day's miss into a wait
    clean(cx)
    for k, n in (("ITEMWISE", 21), ("BILLWISE", 22)):
        door(cx, k, n, frm="2000-01-01", to="2000-01-15", stampday="20000115")
    cx.commit()
    try:
        past = {e["kind"]: e for e in m._export_state(cx, "2000-01-15", "2000-01-15 09:30:00")}
        ok = all(past[k]["state"] == "bad" and not past[k].get("door") for k in past)
    except Exception:                                                  # noqa: BLE001
        ok = False
    res.append(("Q  a PAST day with a covering door file -> its own reading, BAD, no door (today only)", ok, False))
    cx.execute("DELETE FROM mi_file WHERE md5 LIKE 'walk678%'")
    cx.commit()

    # the page itself -- the whole state() on the copy, then step 4's html
    def page(setup, ws_min):
        clean(cx)
        setup()
        if ws_min is not None:
            tap3(cx, ws_min)
        cx.commit()
        S = m.state(cx, DAY, USER, step=4)
        return m._step4(S)

    for name, setup, ws_min, judge, s678 in (
            ("L  step 4's page with both at the door: 'Report server par aa gayi hai', the time, no 'Dobara banaiye', no minutes",
             both_door, 20,
             lambda h: ("Report server par aa gayi hai" in h and "Server par 09:07 baje aa gayi" in h and "Dobara banaiye" not in h
                        and "file band kijiye" not in h and "Report aa rahi hai &mdash;" not in h and "Aage ka kaam shuru kijiye" in h), True),
            ("M  step 4's page with nothing anywhere after six minutes: 'Dobara banaiye' (unchanged)",
             lambda: None, 20, lambda h: "Dobara banaiye" in h and "Report server par" not in h, False),
            ("N  step 4's page inside the six minutes, nothing anywhere: 'Report aa rahi hai -- N min' (unchanged)",
             lambda: None, 1, lambda h: "Report aa rahi hai &mdash;" in h and "Report server par" not in h, False),
            ("U  step 4's page: item-detail at the door, bill-wise WRONG (a non-covering export): the red head and "
             "'Dobara banaiye' rule -- never 'dobara nahi nikaalni'",
             lambda: (door(cx, "ITEMWISE", 28), pe_at(cx, "BILLWISE", 29, to="2099-01-10", hhmmss="091500")), 20,
             lambda h: "Dobara banaiye" in h and "dobara nahi nikaalni" not in h and "Report server par aa gayi hai" not in h, False),
            ("V  step 4's page: one at the door, nothing tapped and nothing of the other: 'Abhi report nikaali nahi gayi', never "
             "'dobara nahi nikaalni'",
             lambda: door(cx, "ITEMWISE", 30), None,
             lambda h: "Abhi report nikaali nahi gayi" in h and "dobara nahi nikaalni" not in h, False),
            ("O  step 4's page with both in purchase_export: 'Dono report mil gayi' (unchanged)",
             lambda: (pe(cx, "ITEMWISE", 19), pe(cx, "BILLWISE", 20)), 20,
             lambda h: "Dono report mil gayi" in h and "Report server par" not in h, False)):
        try:
            ok = bool(judge(page(setup, ws_min)))
        except Exception as e:                                         # noqa: BLE001
            ok = False
            name += " (raised %s: %s)" % (type(e).__name__, str(e)[:120])
        res.append((name, ok, s678))
    clean(cx)
    return res


def old_new(old, new, cx, since):
    """Every real day since `since` with a step-3 tap or a purchase export: the old and the new _export_state, on the copy's rows."""
    days = set()
    for (d,) in cx.execute("SELECT DISTINCT day FROM amir_step_log WHERE day>=? AND day<'2099'", (since,)):
        days.add(d)
    for (d,) in cx.execute("SELECT DISTINCT substr(export_stamp,1,4)||'-'||substr(export_stamp,5,2)||'-'||substr(export_stamp,7,2) "
                           "FROM purchase_export WHERE export_stamp>=?", (since.replace("-", ""),)):
        days.add(d)
    same, allowed, bad = 0, [], []
    for d in sorted(days):
        r = cx.execute("SELECT MAX(done_at) FROM amir_step_log WHERE day=? AND step=3", (d,)).fetchone()
        ws = r[0] if r else None
        a = old._export_state(cx, d, ws)
        b = new._export_state(cx, d, ws)
        for ea, eb in zip(a, b):
            ea = {k: v for k, v in ea.items() if k != "waited"}            # recomputed per call: a minute boundary is not a difference
            eb = {k: v for k, v in eb.items() if k != "waited"}
            if ea == eb:
                same += 1
            elif eb.get("door") and eb.get("state") == "wait" and ea.get("state") in ("bad", "none", "wait"):
                allowed.append("%s %s: old %s -> new at the server %s" % (d, ea["kind"], ea["state"], eb["door"]))
            else:
                bad.append("%s %s: old %r new %r" % (d, ea["kind"], (ea.get("state"), ea.get("reason_en")), (eb.get("state"), eb.get("reason_en"))))
    return len(days), same, allowed, bad


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--new")
    g.add_argument("--old")
    ap.add_argument("--lib")
    ap.add_argument("--db", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--old-root")
    ap.add_argument("--since", default="2026-09-01")
    a = ap.parse_args()
    root = a.new or a.old
    lib = a.lib or root
    os.makedirs(a.scratch, exist_ok=True)
    m = load(root, lib, a.scratch, "test")
    cx = sqlite3.connect(a.db, timeout=30)
    res = run_cases(m, cx)
    if a.new and a.old_root:
        old = load(a.old_root, lib, a.scratch, "old")
        n_days, same, allowed, bad = old_new(old, m, cx, a.since)
        print("  --  old = new since %s: %d day(s), %d report-day(s) identical, %d allowed (the door held it), %d other"
              % (a.since, n_days, same, len(allowed), len(bad)))
        for x in allowed[:20]:
            print("      %s" % x)
        for x in bad[:20]:
            print("      RED %s" % x)
        res.append(("P  old = new on every real day since %s (only the door's allowed difference)" % a.since, not bad, False))
    cx.close()
    for name, ok, s678 in res:
        print("  %s  %s" % ("ok " if ok else "RED", name))
    if a.new:
        g_ = sum(1 for r in res if r[1])
        print("%d of %d green" % (g_, len(res)))
        sys.exit(0 if g_ == len(res) else 1)
    red_s678 = sum(1 for r in res if not r[1] and r[2])
    red_older = sum(1 for r in res if not r[1] and not r[2])
    print("%d S678 check(s) red · %d older red · %d green" % (red_s678, red_older, sum(1 for r in res if r[1])))


if __name__ == "__main__":
    main()
