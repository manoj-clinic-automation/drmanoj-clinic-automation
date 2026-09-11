#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export_watch.py -- S240, Sanjeevni plan item 1 (the missed-export check, keyed to Amir's punches)

Amir's Marg exports are the purchase truth. On 06-11 Sep they stopped and nothing said so.
This says so, on the days it matters: a day on which Amir PUNCHED IN on the biometric machine.

On such a day, by close, the server expects:
    PURCHASE BILL WISE        exported that day, covering the 1st of the month to yesterday or later
    the item lines            PURCHASE BILL/ITEM WISE or SUPPLIER/ITEM WISE (either grouping), the same
    STOCK CLOSING             that night, or the next morning before the counter opens: Marg's "as on" date
                              is the day itself, or the next day if it reached here before 10:30. Until
                              10:30 next morning it is "due", never red (the owner, 11-Sep: "tomorrow morning
                              you will get the stock report before any sale at the counter; it can be done
                              tonight also")
    and ONLY on the 1st-5th:  PURCHASE SUPPLIER WISE for the whole previous month (month-end, D368)

The owner, 11-Sep-2026: "no need for purchase supplier wise [mid-month] as the supplier wise, item wise
purchase report contains the supplier details, the bill details and the item details. So why burden
anybody for exporting a report which is not required in the middle of the month?"  Supplier-wise stays
the month-end figure (D368), so it is asked for once, at month-end, and never daily.

    python3 export_watch.py --day today                      (cron 23:40 -- the close-of-day line)
    python3 export_watch.py --day yesterday --notify         (cron 10:45 -- final; pushes to your phone once)
    python3 export_watch.py --day 2026-09-11 --dry-run       (says what it would write)
    python3 export_watch.py --selftest

VERDICTS (one row per day in table export_watch)
    ok          punched, and everything expected arrived
    red         punched, and something is missing -- the list is stored and shown
    no_punch    Amir did not punch that day -- nothing expected
    unknown     the clinic PC (manojz) has not reported since the day ended, so a gap here could be
                the PC asleep rather than a missed export. Said plainly, never shown as red.

WHERE IT SHOWS
    a red line on the Marg Purchases hub (owner) and on Amir's salt page (Hinglish), both read
    from export_watch by purchase_app.py; and, with --notify, one ntfy push per red day through the
    same private topic the freshness watch uses (NTFY_URL in /root/finance/freshness.conf -- never
    printed).

READS ONLY: /root/punches.csv, /root/staff_register/staff_register.db (to find Amir's machine id),
finance.db purchase_export / stock_feed / purchase_feed / emp_code. WRITES ONLY export_watch.
"""
import argparse
import csv
import datetime as dt
import io
import json
import os
import sqlite3
import sys
import urllib.request

DEF_DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
DEF_PUNCHES = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
DEF_STAFF_DB = os.environ.get("SR_DB_PATH", "/root/staff_register/staff_register.db")
DEF_CONF = "/root/finance/freshness.conf"
WHO = "Amir Sohail"

SCHEMA = """
CREATE TABLE IF NOT EXISTS export_watch (
    day         TEXT NOT NULL,
    who         TEXT NOT NULL,
    staff_id    TEXT,
    punched     INTEGER NOT NULL,
    verdict     TEXT NOT NULL,
    missing     TEXT NOT NULL,
    have        TEXT NOT NULL,
    note        TEXT NOT NULL,
    checked_at  TEXT NOT NULL,
    notified_at TEXT,
    PRIMARY KEY (day, who)
);
"""
LABEL = {"BILLWISE": "PURCHASE BILL WISE", "SUPPLIERWISE": "PURCHASE SUPPLIER WISE for last month (month-end)",
         "LINES": "PURCHASE BILL ITEM WISE (or SUPPLIER/ITEM WISE)", "STOCK": "STOCK CLOSING"}
ORDER = ("BILLWISE", "LINES", "STOCK", "SUPPLIERWISE")
STOCK_BY = dt.time(10, 30)  # a next-morning closing counts if it reached the server before this
MONTH_END_DAYS = 5          # supplier-wise for last month is expected on punch days 1..5 only


def ist_now():
    return dt.datetime.utcnow() + dt.timedelta(hours=5, minutes=30)


def resolve_day(s, now=None):
    now = now or ist_now()
    if s in (None, "", "today"):
        return now.date()
    if s == "yesterday":
        return now.date() - dt.timedelta(days=1)
    return dt.date.fromisoformat(s)


# ------------------------------------------------------------------ who is Amir on the machine?
def staff_id_for(name, staff_db=DEF_STAFF_DB, fin_con=None):
    """The biometric user id. The staff register's staff_id IS the machine id (staff_register.py
    biometric_present_ids); emp_code in finance.db is the fallback. Returns (id, where)."""
    key = name.split()[0].lower()
    if staff_db and os.path.exists(staff_db):
        try:
            c = sqlite3.connect("file:%s?mode=ro" % staff_db, uri=True)
            rows = c.execute("SELECT staff_id, name FROM staff").fetchall()
            c.close()
            hits = [str(r[0]) for r in rows if (r[1] or "").lower().split()[:1] == [key]]
            if len(hits) == 1:
                return hits[0], "staff register"
        except sqlite3.Error:
            pass
    if fin_con is not None:
        try:
            hits = [str(r[0]) for r in fin_con.execute(
                "SELECT code FROM emp_code WHERE retired_on IS NULL AND lower(person) LIKE ?", (key + "%",))]
            if len(hits) == 1:
                return hits[0], "emp_code"
        except sqlite3.Error:
            pass
    return None, "not found"


def punched_on(staff_id, day, punches=DEF_PUNCHES):
    """Did this machine id punch on this day? punches.csv: user_id,datetime,io_mode,verify_mode,received_at."""
    d = day.isoformat()
    try:
        with io.open(punches, "r", encoding="utf-8-sig", errors="replace", newline="") as fh:
            for r in csv.reader(fh):
                if len(r) >= 2 and r[0].strip() == str(staff_id) and r[1].strip()[:10] == d:
                    return True
    except OSError:
        return None
    return False


# ------------------------------------------------------------------ what arrived?
def evidence(con, day):
    """Which of the four expected things exist for this day. Pure reads."""
    ymd = day.strftime("%Y%m%d")
    first = day.replace(day=1).isoformat()
    need_to = (day - dt.timedelta(days=1)).isoformat()
    if day.day == 1:                      # on the 1st, "1st to yesterday" is last month -- accept today
        need_to = day.isoformat()
        first = day.isoformat()
    have = {}
    for typ, pf, pt, st in con.execute(
            "SELECT type, period_from, period_to, export_stamp FROM purchase_export "
            "WHERE substr(export_stamp,1,8)=?", (ymd,)):
        ok = (pf or "9") <= first and (pt or "") >= need_to
        key = "LINES" if typ in ("ITEMWISE", "BILLITEMWISE") else typ
        if key in ("BILLWISE", "LINES"):
            prev = have.get(key)
            if ok or not prev:
                have[key] = {"stamp": st, "period": "%s..%s" % (pf, pt), "covers": ok}
    if day.day <= MONTH_END_DAYS:
        last = day.replace(day=1) - dt.timedelta(days=1)
        r = con.execute("SELECT export_stamp, period_from, period_to FROM purchase_export WHERE type='SUPPLIERWISE' "
                        "AND period_from<=? AND period_to>=? AND substr(export_stamp,1,8)>=? "
                        "ORDER BY export_stamp DESC LIMIT 1",
                        (last.replace(day=1).isoformat(), last.isoformat(),
                         day.replace(day=1).strftime("%Y%m%d"))).fetchone()
        if r:
            have["SUPPLIERWISE"] = {"stamp": r[0], "period": "%s..%s" % (r[1], r[2]), "covers": True}
    as_on = day.strftime("%d-%m-%Y")
    r = con.execute("SELECT MIN(received_at), COUNT(*) FROM stock_feed WHERE as_on=? "
                    "AND source LIKE 'push_snapshot%'", (as_on,)).fetchone()
    if r and r[1]:
        have["STOCK"] = {"stamp": r[0], "period": as_on, "covers": True}
    else:
        nxt = day + dt.timedelta(days=1)
        r = con.execute("SELECT MIN(received_at), COUNT(*) FROM stock_feed WHERE as_on=? "
                        "AND source LIKE 'push_snapshot%'", (nxt.strftime("%d-%m-%Y"),)).fetchone()
        by = dt.datetime.combine(nxt, STOCK_BY).strftime("%Y-%m-%dT%H:%M:%S")
        if r and r[1] and (r[0] or "9") <= by:
            have["STOCK"] = {"stamp": r[0], "period": nxt.strftime("%d-%m-%Y") + " (next morning)", "covers": True}
    return have


def pc_reported_after(con, when_iso):
    """Has manojz sent anything since this moment? (a purchase feed row or any purchase export)"""
    r = con.execute("SELECT MAX(at) FROM purchase_feed").fetchone()
    r2 = con.execute("SELECT MAX(received_at) FROM purchase_export").fetchone()
    latest = max([x for x in ((r or [None])[0], (r2 or [None])[0]) if x] or [""])
    return latest >= when_iso, latest


def expected(day):
    return [k for k in ORDER if k != "SUPPLIERWISE" or (day and day.day <= MONTH_END_DAYS)]


def judge(punched, have, pc_ok, day=None):
    missing = [k for k in expected(day) if not (have.get(k) or {}).get("covers")]
    if punched is None:
        return "unknown", missing, "the punch file could not be read"
    if not punched:
        return "no_punch", [], "no punch that day -- nothing expected"
    if not missing:
        return "ok", [], "everything expected arrived"
    if not pc_ok:
        return "unknown", missing, "the clinic PC has not reported since the day ended -- it may be asleep"
    return "red", missing, "missing by close"


def check(con, day, who=WHO, punches=DEF_PUNCHES, staff_db=DEF_STAFF_DB, now=None):
    now = now or ist_now()
    sid, where = staff_id_for(who, staff_db, con)
    punched = punched_on(sid, day, punches) if sid else None
    have = evidence(con, day)
    # the PC must have reported AFTER the evening push window of that day (or now, if earlier)
    cutoff = min(now, dt.datetime.combine(day, dt.time(22, 0)))
    pc_ok, latest = pc_reported_after(con, cutoff.strftime("%Y-%m-%dT%H:%M:%S"))
    verdict, missing, note = judge(punched, have, pc_ok, day)
    stock_due = dt.datetime.combine(day + dt.timedelta(days=1), STOCK_BY)
    if "STOCK" in missing and now < stock_due:
        missing = [k for k in missing if k != "STOCK"]
        if verdict in ("red", "unknown") and not missing:
            verdict = "ok"
        note = (note if missing else "everything else arrived") + \
            "; stock closing due by %s" % stock_due.strftime("%d-%m %H:%M")
    if sid is None:
        verdict, note = "unknown", "Amir's machine id was not found (%s)" % where
    return {"day": day.isoformat(), "who": who, "staff_id": sid, "id_from": where,
            "punched": punched, "verdict": verdict, "missing": missing, "have": have, "note": note,
            "pc_latest": latest}


def store(con, res, now=None):
    con.executescript(SCHEMA)
    now = (now or ist_now()).strftime("%Y-%m-%dT%H:%M:%S")
    con.execute("INSERT INTO export_watch (day, who, staff_id, punched, verdict, missing, have, note, checked_at) "
                "VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(day, who) DO UPDATE SET staff_id=excluded.staff_id, "
                "punched=excluded.punched, verdict=excluded.verdict, missing=excluded.missing, "
                "have=excluded.have, note=excluded.note, checked_at=excluded.checked_at",
                (res["day"], res["who"], res["staff_id"], 1 if res["punched"] else 0, res["verdict"],
                 json.dumps(res["missing"]), json.dumps(res["have"]), res["note"], now))
    con.commit()


def read_conf(path=DEF_CONF):
    out = {}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    out[k.strip()] = v.strip().strip('"').strip("'")
    except OSError:
        pass
    return out


def notify(con, res, conf_path=DEF_CONF, now=None):
    """One ntfy push per red day. Returns a line to print (never the URL)."""
    if res["verdict"] != "red":
        return "no push (verdict %s)" % res["verdict"]
    r = con.execute("SELECT notified_at FROM export_watch WHERE day=? AND who=?", (res["day"], res["who"])).fetchone()
    if r and r[0]:
        return "already pushed at %s" % r[0]
    url = read_conf(conf_path).get("NTFY_URL")
    if not url:
        return "NTFY_URL not set -- no push"
    body = ("Amir punched in on %s but these Marg exports did not arrive: %s."
            % (res["day"], ", ".join(LABEL[k] for k in res["missing"])))
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST",
                                 headers={"Title": "Marg exports missing %s" % res["day"],
                                          "Priority": "default", "Tags": "warning"})
    try:
        urllib.request.urlopen(req, timeout=20).read()
    except Exception as e:                                   # noqa: BLE001
        return "push FAILED (%s) -- will retry next run" % e.__class__.__name__
    con.execute("UPDATE export_watch SET notified_at=? WHERE day=? AND who=?",
                ((now or ist_now()).strftime("%Y-%m-%dT%H:%M:%S"), res["day"], res["who"]))
    con.commit()
    return "pushed to the owner's phone"


def line(res):
    miss = ", ".join(LABEL[k] for k in res["missing"]) or "-"
    return ("%s  %s (machine id %s, from %s): punched=%s  verdict=%s  missing: %s  -- %s"
            % (res["day"], res["who"], res["staff_id"] or "?", res["id_from"],
               {True: "yes", False: "no", None: "?"}[res["punched"]], res["verdict"].upper(), miss, res["note"]))


# ------------------------------------------------------------------ selftest
def selftest():
    import tempfile
    fails = []

    def ck(n, c):
        print(("  ok   " if c else "  FAIL ") + n)
        if not c:
            fails.append(n)
    td = tempfile.mkdtemp()
    con = sqlite3.connect(":memory:")
    con.executescript("""
      CREATE TABLE purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at,
                                    n_rows, grand_amount_p, superseded_by);
      CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on, source, item, qty, received_at);
      CREATE TABLE purchase_feed (id INTEGER PRIMARY KEY, at, host, pull_last, pull_age_min, state);
      CREATE TABLE emp_code (code, person, issued_on, retired_on, source, note);
      INSERT INTO emp_code VALUES (101, 'AMIR SOHAIL', '2026-09-03', NULL, 'joiner', NULL);""")
    sdb = os.path.join(td, "sr.db")
    s = sqlite3.connect(sdb); s.execute("CREATE TABLE staff (staff_id, name)")
    s.execute("INSERT INTO staff VALUES (101, 'Amir Sohail')"); s.execute("INSERT INTO staff VALUES (7, 'Alisha')")
    s.commit(); s.close()
    pcsv = os.path.join(td, "p.csv")
    with open(pcsv, "w") as fh:
        fh.write("user_id,datetime,io_mode,verify_mode,received_at\n101,2026-09-11 09:02:11,0,1,x\n7,2026-09-12 09:00:00,0,1,x\n")
    day = dt.date(2026, 9, 11)
    now = dt.datetime(2026, 9, 11, 23, 40)
    ck("Amir's id from the staff register", staff_id_for("Amir Sohail", sdb, con) == ("101", "staff register"))
    ck("emp_code fallback", staff_id_for("Amir Sohail", os.path.join(td, "none.db"), con) == ("101", "emp_code"))
    con.execute("INSERT INTO purchase_feed (at) VALUES ('2026-09-11T22:30:10')")
    r = check(con, day, punches=pcsv, staff_db=sdb, now=now)
    ck("punched, nothing arrived by 23:40 -> red: bill-wise and item lines (stock only due)", r["verdict"] == "red" and r["missing"] == ["BILLWISE", "LINES"])
    con.execute("INSERT INTO purchase_export VALUES ('a','BILLWISE','f','2026-09-01','2026-09-10','20260911-134235','x',1,0,NULL)")
    con.execute("INSERT INTO purchase_export VALUES ('b','ITEMWISE','f','2026-09-01','2026-09-11','20260911-140731','x',1,0,NULL)")
    r = check(con, day, punches=pcsv, staff_db=sdb, now=now)
    ck("today's real case at 23:40: nothing red -- the stock closing is only due", r["verdict"] == "ok" and r["missing"] == [] and "due by" in r["note"])
    r = check(con, day, punches=pcsv, staff_db=sdb, now=dt.datetime(2026, 9, 12, 10, 45))
    ck("next morning 10:45, still no closing -> red, stock closing only", r["verdict"] == "red" and r["missing"] == ["STOCK"])
    con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES ('12-09-2026','push_snapshot','X',1,'2026-09-12T09:40:00')")
    r = check(con, day, punches=pcsv, staff_db=sdb, now=dt.datetime(2026, 9, 12, 10, 45))
    ck("a next-morning closing before 10:30 counts for the day before", r["verdict"] == "ok")
    con.execute("DELETE FROM stock_feed")
    con.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES ('11-09-2026','push_snapshot','X',1,'2026-09-11T09:01:00')")
    r = check(con, day, punches=pcsv, staff_db=sdb, now=now)
    ck("everything there -> ok", r["verdict"] == "ok" and not r["missing"])
    r = check(con, dt.date(2026, 9, 12), punches=pcsv, staff_db=sdb, now=dt.datetime(2026, 9, 12, 23, 40))
    ck("no punch -> nothing expected", r["verdict"] == "no_punch")
    con2 = sqlite3.connect(":memory:")
    con2.executescript("CREATE TABLE purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at,"
                       " n_rows, grand_amount_p, superseded_by); CREATE TABLE stock_feed (id, as_on, source, item, qty,"
                       " received_at); CREATE TABLE purchase_feed (id, at, host, pull_last, pull_age_min, state);"
                       " CREATE TABLE emp_code (code, person, issued_on, retired_on, source, note);"
                       " INSERT INTO purchase_feed (at) VALUES ('2026-09-11T10:00:00');")
    r = check(con2, day, punches=pcsv, staff_db=sdb, now=now)
    ck("PC silent since the evening -> unknown, not red", r["verdict"] == "unknown")
    store(con, check(con, day, punches=pcsv, staff_db=sdb, now=now), now=now)
    store(con, check(con, day, punches=pcsv, staff_db=sdb, now=now), now=now)
    ck("one row per day, re-runs update it", con.execute("SELECT COUNT(*) FROM export_watch").fetchone()[0] == 1)
    ck("unreadable punch file -> unknown", judge(None, {}, True)[0] == "unknown")
    r = check(con, dt.date(2026, 10, 1), punches=pcsv, staff_db=sdb, now=dt.datetime(2026, 10, 1, 23, 40))
    ck("the 1st of a month does not demand last month's bill-wise", "BILLWISE" not in evidence(con, dt.date(2026, 10, 1)))
    ck("on the 1st-5th, last month's supplier-wise is expected", "SUPPLIERWISE" in expected(dt.date(2026, 10, 3))
       and "SUPPLIERWISE" not in expected(dt.date(2026, 10, 6)))
    con.execute("INSERT INTO purchase_export VALUES ('m','SUPPLIERWISE','f','2026-09-01','2026-09-30','20261002-100000','x',1,0,NULL)")
    ck("a whole-month supplier-wise exported after month-end satisfies it",
       evidence(con, dt.date(2026, 10, 3)).get("SUPPLIERWISE", {}).get("covers") is True)
    con.execute("INSERT INTO purchase_export VALUES ('n','SUPPLIERWISE','f','2026-09-01','2026-09-20','20261002-110000','x',1,0,NULL)")
    ck("a part-month supplier-wise is never the month-end one", evidence(con, dt.date(2026, 10, 3))["SUPPLIERWISE"]["stamp"] == "20261002-100000")
    print("export_watch selftest: %d checks, %d failures" % (15, len(fails)))
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default="today")
    ap.add_argument("--db", default=DEF_DB)
    ap.add_argument("--punches", default=DEF_PUNCHES)
    ap.add_argument("--staff-db", default=DEF_STAFF_DB)
    ap.add_argument("--notify", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    day = resolve_day(a.day)
    con = sqlite3.connect(a.db, timeout=30)
    res = check(con, day, punches=a.punches, staff_db=a.staff_db)
    print(line(res))
    if a.dry_run:
        print("DRY RUN -- nothing written")
        return 0
    store(con, res)
    if a.notify:
        print("notify: " + notify(con, res))
    return 0


if __name__ == "__main__":
    sys.exit(main())
