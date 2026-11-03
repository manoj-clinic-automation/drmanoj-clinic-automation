#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s702.py -- the walk of kit S702_OWNER_REPORT_NOTICES (03-Nov-2026, Sanjeevni session 380).

    python3 -B walk_s702.py --new <root> --scratch <dir>      the checks on a root that carries the kit (all green)
    python3 -B walk_s702.py --old <root> --scratch <dir>      the CONTROL on the live root (the S702 checks go red)
    python3 -B walk_s702.py --proof --old-root <live root> --new <root> --db <copy of finance.db> --scratch <dir>
                                                              old and new reports_tile / reports_watch on a COPY of the live database,
                                                              every day of the last 35: the only differences are the kit's own

THE WALK STANDS ON ITS OWN ROWS (F-998): a scratch database made here, every row made up, every day in 2099; no live row is read and no
message can leave (OWNER_NOTICE_STUB is a scratch file; ORDER_PUSH_NONE is set; the database is not the live one).
"""
import datetime as dt
import json
import os
import shutil
import sqlite3
import subprocess
import sys

ARGS = sys.argv[1:]


def arg(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


SCR = os.path.abspath(arg("--scratch", "/tmp/s702_walk"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


# ====================================================================================================== the proof (old vs new, live copy)
def _dump(root, db, days):
    """reports_tile.status and reports_watch.decide for each day at 12:00 and 11:00, run in a child under <root>/finance."""
    code = r'''
import sys, json, datetime as dt, sqlite3, os
sys.path.insert(0, os.getcwd())
import reports_tile, reports_watch
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
con = sqlite3.connect("file:%s?mode=ro" % sys.argv[1], uri=True); con.row_factory = sqlite3.Row
out = {}
for d in sys.argv[2].split(","):
    day = dt.date.fromisoformat(d)
    now = dt.datetime(day.year, day.month, day.day, 12, 0, tzinfo=IST)
    s = reports_tile.status(con, day, now)
    rows = [{k: r.get(k) for k in ("key", "state", "at", "count", "due_ddmm")} for r in s["rows"]]
    dec = reports_watch.decide(s, 2, 600, dt.datetime(day.year, day.month, day.day, 11, 0, tzinfo=IST))
    out[d] = dict(due=s["due_day"], rows=rows, decide=[(x["key"], x["kind"]) for x in dec], line=s["line"])
print(json.dumps(out, default=str))
'''
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.run([sys.executable, "-B", "-c", code, db, ",".join(days)], cwd=os.path.join(root, "finance"), env=env,
                       capture_output=True, text=True, timeout=600)
    if p.returncode != 0:
        raise SystemExit("proof: the child under %s failed: %s" % (root, (p.stderr or "")[-400:]))
    return json.loads(p.stdout.strip().splitlines()[-1])


def proof():
    old_root, new_root, db = arg("--old-root"), arg("--new"), arg("--db")
    today = dt.datetime.now(IST).date()
    days = [(today - dt.timedelta(days=i)).isoformat() for i in range(35, -1, -1)]
    a, b = _dump(old_root, db, days), _dump(new_root, db, days)
    same = mondays = expiry = sundays = 0
    bad = []
    for d in days:
        day = dt.date.fromisoformat(d)
        x, y = a[d], b[d]
        xr = [r for r in x["rows"] if r["key"] != "STOCK_EXPIRY"]
        dropped = len(x["rows"]) - len(xr)
        if day.weekday() == 0:                       # a Monday: the due day moves from Saturday to Sunday -- the kit's own change
            ok = y["due"] == (day - dt.timedelta(days=1)).isoformat() and x["due"] == (day - dt.timedelta(days=2)).isoformat()
            print("  --  %s Monday: due %s -> %s; rows old %s / new %s" % (d, x["due"], y["due"],
                  " ".join("%s=%s" % (r["key"][:12], r["state"]) for r in x["rows"][:2]), " ".join("%s=%s" % (r["key"][:12], r["state"]) for r in y["rows"][:2])))
            if ok:
                mondays += 1
            else:
                bad.append("%s: Monday due %s -> %s" % (d, x["due"], y["due"]))
            continue
        if xr != y["rows"]:
            bad.append("%s: rows differ beyond Stock Expiry: old %s new %s" % (d, xr, y["rows"]))
            continue
        if dropped:
            expiry += 1
            print("  --  %s: Stock Expiry row gone (F-1090); every other row identical" % d)
        if day.weekday() == 6:
            sundays += 1
            print("  --  %s Sunday: the alarms old %s / new %s" % (d, x["decide"] or "none", y["decide"] or "none"))
            if x["decide"]:
                bad.append("%s: the OLD watch spoke on a Sunday" % d)
            continue
        if x["decide"] != y["decide"]:
            bad.append("%s: the alarms differ on a weekday: %s vs %s" % (d, x["decide"], y["decide"]))
            continue
        same += 1
    for m in bad:
        print("  RED  " + m)
    verdict = "CLEAN" if not bad else "%d UNEXPLAINED" % len(bad)
    print("proof: old vs new over %d days . %s . %d identical weekday(s), %d Monday(s) moved to Sunday, %d day(s) without Stock Expiry, %d Sunday(s) now told"
          % (len(days), verdict, same, mondays, expiry, sundays))
    return 0 if not bad else 1


# ====================================================================================================== the walk (own rows)
def walk(root, is_new):
    fails, oks = [], []

    def ck(name, cond):
        (oks if cond else fails).append(name)
        print("  %s  %s" % ("ok " if cond else "RED", name))

    shutil.rmtree(SCR, ignore_errors=True)
    os.makedirs(os.path.join(SCR, "readings"))
    os.environ.update(SPINE_READINGS=os.path.join(SCR, "readings"), SR_DB_PATH=os.path.join(SCR, "no_staff.db"),
                      OWNER_NOTICE_STUB=os.path.join(SCR, "sent.jsonl"), ORDER_PUSH_NONE="1", FINANCE_OFF_DIR=os.path.join(SCR, "_off"),
                      PYTHONDONTWRITEBYTECODE="1", MI_ARCHIVE=os.path.join(SCR, "archive"), OWNER_NOTICE_LOCK=os.path.join(SCR, "tick.lock"))
    here = os.path.dirname(os.path.abspath(__file__))                # the kit's own owner_notice.py must never answer for the root's
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != here]
    sys.path.insert(0, os.path.join(root, "finance"))
    import reports_tile as RT
    import reports_watch as RW
    try:
        import owner_notice as ON
    except ImportError:
        ON = None
    import order_sheet as OS
    import expiry_watch as EW
    import supplier_msg as SM
    try:
        import porders_s454 as PO
    except Exception:                                             # noqa: BLE001
        PO = None

    db = os.path.join(SCR, "walk.db")
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    con.executescript("""
      CREATE TABLE setting (key TEXT PRIMARY KEY, value TEXT, note TEXT);
      CREATE TABLE mi_file (md5 TEXT PRIMARY KEY, drive_id TEXT DEFAULT '', drive_name TEXT DEFAULT '', drive_folder TEXT DEFAULT '',
        drive_mtime TEXT DEFAULT '', size INTEGER DEFAULT 0, stamp TEXT DEFAULT '', type TEXT DEFAULT '', variant TEXT DEFAULT '',
        date_from TEXT DEFAULT '', date_to TEXT DEFAULT '', verdict TEXT DEFAULT '', reason TEXT DEFAULT '', server_name TEXT DEFAULT '',
        kept INTEGER DEFAULT 0, lines INTEGER DEFAULT 0, pc_type TEXT DEFAULT '', pc_verdict TEXT DEFAULT '', agree TEXT DEFAULT '',
        received_at TEXT NOT NULL, source TEXT DEFAULT '');
      CREATE TABLE purchase_export (md5 TEXT PRIMARY KEY, type TEXT, file TEXT, period_from TEXT, period_to TEXT, export_stamp TEXT,
        received_at TEXT, n_rows INTEGER, grand_amount_p INTEGER, superseded_by TEXT);
      CREATE TABLE purchase_salt_task (id INTEGER PRIMARY KEY, section TEXT, seq INTEGER, a TEXT, b TEXT, c TEXT, done INTEGER DEFAULT 0,
        done_by TEXT, done_at TEXT, answer TEXT, answer_by TEXT, answer_at TEXT, source_md5 TEXT, pushed_at TEXT);
      CREATE TABLE amir_day (day TEXT PRIMARY KEY, opened_at TEXT, closed_at TEXT, closed_by TEXT);
      CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, as_on TEXT, source TEXT, item TEXT, qty INTEGER, received_at TEXT);
    """)
    for fn in (getattr(OS, "ensure", None), getattr(EW, "ensure", None), getattr(EW, "fixes_ensure", None), getattr(SM, "ensure", None)):
        try:
            fn(con)
        except Exception as e:                                    # noqa: BLE001
            print("  --  ensure %s: %s" % (getattr(fn, "__module__", "?"), e.__class__.__name__))
    con.commit()

    def reading(md5, family, ok, **data):
        with open(os.path.join(SCR, "readings", md5 + ".json"), "w") as fh:
            json.dump(dict(md5=md5, family=family, ok=ok, failed=[], reader="S331.1", data=data), fh)

    def mi(md5, typ, dfrom, dto, verdict, received, server_name="", reason=""):
        con.execute("INSERT INTO mi_file (md5,type,date_from,date_to,verdict,reason,server_name,received_at) VALUES (?,?,?,?,?,?,?,?)",
                    (md5, typ, dfrom, dto, verdict, reason, server_name, received))
        con.commit()

    def at(day, h, m=0):
        return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=IST)

    def keys(now):
        if ON is None:
            return {}
        msgs, _e = ON.collect(con, now)
        return {m["key"]: m for m in msgs}

    # the days: a Monday in March 2099 after the 7th, its Sunday, and the 2nd of April
    MON = next(dt.date(2099, 3, d) for d in range(9, 20) if dt.date(2099, 3, d).weekday() == 0)
    TUE = MON + dt.timedelta(days=1)
    SUN = MON - dt.timedelta(days=1)
    SAT = MON - dt.timedelta(days=2)

    # ---- 1 the module, its table and settings; the since gate
    ck("owner_notice.py is on this root", ON is not None)
    if ON is not None:
        ON.ensure(con)
    n_set = con.execute("SELECT COUNT(*) FROM setting WHERE key LIKE 'owner_notice.%'").fetchone()[0]
    ck("ensure seeds the table and its 11 settings (to = manoj, since empty)", n_set == 11
       and con.execute("SELECT value FROM setting WHERE key='owner_notice.to'").fetchone()[0] == "manoj")
    # the pair of Tuesday (due Monday)
    mi("w_sale_mon", "SALE_BILLWISE", MON.isoformat(), MON.isoformat(), "VERIFIED", "%sT09:10:00+05:30" % TUE.isoformat())
    reading("w_sale_mon", "SALE_BILLWISE", True, bills=[{}] * 21)
    mi("w_cls_tue", "STOCK_CLOSING", TUE.isoformat(), TUE.isoformat(), "VERIFIED", "%sT09:12:00+05:30" % TUE.isoformat(), "STOCK_CLOSING_TOTALS__w.xls")
    reading("w_cls_tue", "STOCK_CLOSING", True, items=[{}] * 380, printed_total=1, lines_total=1)
    ck("nothing is said while owner_notice.since is unset (the install sets it)", keys(at(TUE, 9, 30)) == {})
    con.execute("UPDATE setting SET value='2099-01-01 00:00:00' WHERE key='owner_notice.since'")
    con.commit()

    # ---- 2 Shavez's pair
    k = keys(at(TUE, 9, 30))
    p = k.get("pair:%s" % MON.isoformat())
    ck("the pair certified -> 'Morning reports' once, with the due day and the later arrival (09:12)",
       bool(p) and p["body"] == "Sale %s ✓ · Closing %s ✓ — in by 09:12" % (MON.strftime("%d-%m"), MON.strftime("%d-%m")))
    con.execute("DELETE FROM mi_file WHERE md5='w_cls_tue'")
    con.commit()
    ck("only the sale report in -> no pair message", not any(x.startswith("pair:") for x in keys(at(TUE, 9, 30))))
    mi("w_cls_tue", "STOCK_CLOSING", TUE.isoformat(), TUE.isoformat(), "VERIFIED", "%sT09:12:00+05:30" % TUE.isoformat(), "STOCK_CLOSING_TOTALS__w.xls")

    # ---- 3 Sundays and Mondays
    ck("a Monday's due day is Sunday (Sunday's own sale report is asked for)", RT._due_day(MON) == SUN)
    ck("a Sunday's due day is Saturday", RT._due_day(SUN) == SAT)
    s = {"day": SUN.isoformat(), "due_day": SAT.isoformat(),
         "rows": [{"key": "SALE_BILLWISE", "pair": True, "state": "due", "s500": {}}, {"key": "STOCK_CLOSING", "pair": True, "state": "ok", "s500": {}}]}
    d = RW.decide(s, 2, 600, at(SUN, 10, 5))
    ck("Sunday: the sale report not in by 10:00 is told (not silent)", len(d) == 1 and d[0]["kind"] == "late")
    mi("w_sale_sat", "SALE_BILLWISE", SAT.isoformat(), SAT.isoformat(), "VERIFIED", "%sT09:40:00+05:30" % SUN.isoformat())
    reading("w_sale_sat", "SALE_BILLWISE", True, bills=[{}] * 30)
    mi("w_cls_sun", "STOCK_CLOSING", SUN.isoformat(), SUN.isoformat(), "VERIFIED", "%sT09:41:00+05:30" % SUN.isoformat(), "STOCK_CLOSING_TOTALS__s.xls")
    reading("w_cls_sun", "STOCK_CLOSING", True, items=[{}] * 380, printed_total=1, lines_total=1)
    ck("Sunday: Saturday's pair exported on Sunday is announced on Sunday", "pair:%s" % SAT.isoformat() in keys(at(SUN, 10, 0)))

    # ---- 4 the Stock Valuation, 1st-7th (F-1090: no Stock Expiry row)
    D2 = dt.date(2099, 4, 2)
    mi("w_s_0401", "SALE_BILLWISE", "2099-04-01", "2099-04-01", "VERIFIED", "2099-04-02T09:00:00+05:30")
    rows = RT.status(con, D2, at(D2, 9, 0))["rows"]
    ck("the 2nd: the monthly rows are the valuation alone (Stock Expiry retired)",
       [r["key"] for r in rows if r.get("monthly")] == ["STOCK_VALUATION"])
    ck("the 2nd at 19:59: the valuation not in -> nothing yet", not any(x.startswith("valuation") for x in keys(at(D2, 19, 59))))
    k = keys(at(D2, 20, 0))
    ck("the 2nd at 20:00: 'Stock Valuation not in yet', as on 31-03", "valuation_due:2099-04-02" in k
       and "As on 31-03" in k["valuation_due:2099-04-02"]["body"])
    mi("w_val", "STOCK_VALUATION", "2099-03-31", "2099-03-31", "VERIFIED", "2099-04-02T20:10:00+05:30")
    k = keys(at(D2, 20, 15))
    ck("the valuation arrives -> 'Stock Valuation ✓' with its time", k.get("valuation:2099-04", {}).get("body") == "As on 31-03 — in at 20:10"
       and "valuation_due:2099-04-02" not in k)

    # ---- 5 Amir's visit
    con.execute("INSERT INTO amir_day (day, opened_at) VALUES (?, 'x')", (TUE.isoformat(),))
    con.execute("INSERT INTO purchase_export VALUES ('w_pb','BILLWISE','f',?,?,?,?,3,0,NULL)",
                (TUE.replace(day=1).isoformat(), MON.isoformat(), TUE.strftime("%Y%m%d") + "-110000", "%sT11:00:10" % TUE.isoformat()))
    con.execute("INSERT INTO purchase_export VALUES ('w_pi','ITEMWISE','f',?,?,?,?,3,0,NULL)",
                (TUE.replace(day=1).isoformat(), MON.isoformat(), TUE.strftime("%Y%m%d") + "-110500", "%sT11:05:10" % TUE.isoformat()))
    con.commit()
    k = keys(at(TUE, 12, 0))
    ck("Amir: both purchase reports but no Batch Stock -> nothing before 23:40", not any(x.startswith("amir") for x in k))
    k = keys(at(TUE, 23, 40))
    ck("Amir at 23:40: 'not in: Batch Stock' (and only that)", k.get("amir_missing:%s" % TUE.isoformat(), {}).get("body") == "Amir came today; not in: Batch Stock.")
    mi("w_bs", "BATCH_STOCK", TUE.isoformat(), TUE.isoformat(), "VERIFIED", "%sT12:40:00+05:30" % TUE.isoformat(), "BATCH_STOCK__w.xls")
    con.execute("INSERT INTO stock_expiry_run (at, today, ok, kit, export_md5, export_items) VALUES (?,?,1,'walk','w_bs',400)",
                ("%sT12:44:00" % TUE.isoformat(), TUE.isoformat()))
    for st, done_at in (("done", "%sT12:44:00" % TUE.isoformat()), ("done", "%sT12:44:00" % TUE.isoformat()), ("open", None)):
        con.execute("INSERT INTO stock_batch_fix (kind,k20,item,pack,minus_batch,units,issue_batch,asked_run_id,asked_at,status,done_at) "
                    "VALUES ('wrong','WALK','WALK MED',10,'B1',5,'B2',1,'x',?,?)", (st, done_at))
    con.commit()
    k = keys(at(TUE, 12, 50))
    a = k.get("amir:%s" % TUE.isoformat(), {})
    ck("Amir's three in, the Batch Stock read -> 'Amir's work ✓' with the latest time (12:40) and the fixes 2 done, 1 left",
       a.get("body") == "Item-wise ✓ · Bill-wise ✓ · Batch Stock ✓ — in by 12:40\nBatch fixes: 2 done today, 1 left")
    ck("... and no 'not complete' line once his work is in", "amir_missing:%s" % TUE.isoformat() not in keys(at(TUE, 23, 45)))
    ck("no Amir day -> no Amir message", not any(x.startswith("amir") for x in keys(at(SUN, 23, 50))))

    # ---- 6 Darpan's order sheet
    con.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, n_lines, n_suppliers) VALUES "
                "('w_os1','x','walk','x',?,?,3,2)", ("%sT15:10:00" % TUE.isoformat(), TUE.isoformat()))
    sid = con.execute("SELECT id FROM order_sheet WHERE md5='w_os1'").fetchone()[0]
    for i, sup in enumerate(("WALK SUP A", "WALK SUP A", "WALK SUP B")):
        con.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, supplier, supplier_norm, line_date, kind, state, first_sheet, "
                    "last_sheet, created_at) VALUES (?,?,?,?,?,?,'new','open',?,?,'x')", ("E%d" % i, "WALK MED %d" % i, "WALK MED %d" % i, sup, sup,
                                                                                           TUE.isoformat(), sid, sid))
    con.commit()
    k = keys(at(TUE, 15, 15))
    ck("the order sheet taken -> 'Darpan's order sheet ✓' with 2 suppliers, 3 medicines, 15:10",
       k.get("sheet:%s" % sid, {}).get("body") == "2 suppliers, 3 medicines — in at 15:10")
    ck("a sheet is never announced before it was taken", "sheet:%s" % sid not in keys(at(TUE, 15, 5)))
    mi("w_osr", OS.TYPE, "", "", "REFUSED", "%sT16:00:00+05:30" % TUE.isoformat(), "", "not an order sheet: no item column")
    k = keys(at(TUE, 16, 5))
    ck("a refused order sheet -> 'refused', with the reason", any(x.startswith("sheet_refused:") and "no item column" in v["body"] for x, v in k.items()))

    # ---- 7 his three lists
    last = (TUE - dt.timedelta(days=6)).isoformat()                 # the salt list: limit 8 -> due Thursday
    mi("w_salt_old", "SALT_WISE_ITEM_LIST", last, last, "VERIFIED", "2099-01-02T10:00:00+05:30")
    due = TUE + dt.timedelta(days=2)
    ck("the salt list 2 days before its due day, before 09:00 -> nothing", not any(x.startswith("list_soon") for x in keys(at(TUE, 8, 55))))
    k = keys(at(TUE, 9, 0))
    ck("... at 09:00 -> 'due soon' with the day", k.get("list_soon:SALT_WISE_ITEM_LIST:%s" % due.isoformat(), {}).get("body")
       == "Salt list due %s %s (last as on %s)" % (due.strftime("%a"), due.strftime("%d-%m"), dt.date.fromisoformat(last).strftime("%d-%m")))
    k = keys(at(due, 9, 30))
    ck("on the due day -> 'due today'", "list_due:SALT_WISE_ITEM_LIST:%s" % due.isoformat() in k)
    mi("w_salt_new", "SALT_WISE_ITEM_LIST", due.isoformat(), due.isoformat(), "VERIFIED", "%sT10:14:00+05:30" % due.isoformat())
    ck("a list just arrived and not read yet -> nothing (the next tick says it)", "list_in:w_salt_new" not in keys(at(due, 10, 20)))
    reading("w_salt_new", "SALT_WISE_ITEM_LIST", True, n_items=412)
    k = keys(at(due, 10, 20))
    ck("the list read -> 'Salt list received ✓ -- 412 items, 10:14'",
       k.get("list_in:w_salt_new", {}).get("body") == "Checked by the server — 412 items — in at 10:14")
    mi("w_cat_bad", "CATEGORY_WISE_ITEM_LIST", "", "", "REFUSED", "%sT10:30:00+05:30" % due.isoformat(), "", "no signature matches this title")
    ck("a refused list -> 'Category list refused' with the reason", "no signature" in keys(at(due, 10, 35)).get("list_in:w_cat_bad", {}).get("body", ""))

    # ---- 8 the reception phone (F-1089)
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('supplier_msg.phone_token', 'walk-token')")
    con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES ('supplier_msg.phone_last', ?)", ("%sT08:00:00 200" % TUE.isoformat(),))
    con.commit()
    ck("the phone silent since 08:00: nothing at 09:59 (the window opened at 09:00)", not any(x.startswith("phone:") for x in keys(at(TUE, 9, 59))))
    k = keys(at(TUE, 10, 0))
    ph = [v for x, v in k.items() if x.startswith("phone:")]
    ck("... at 10:00 -> 'Reception phone silent since %s 08:00'" % TUE.strftime("%d-%m"),
       len(ph) == 1 and ph[0]["body"].startswith("Silent since %s 08:00" % TUE.strftime("%d-%m")))
    ck("Sunday after 14:00 -> nothing (the half day's window is shut)",
       not any(x.startswith("phone:") for x in keys(at(SUN, 14, 30))))
    ck("after 20:00 -> nothing", not any(x.startswith("phone:") for x in keys(at(TUE, 20, 5))))
    if PO is not None and hasattr(PO, "_s702_waoff"):
        w_en = PO._s702_waoff(con, True, "silent")
        w_hi = PO._s702_waoff(con, False, "silent")
        w_nk = PO._s702_waoff(con, True, "no_key")
        con.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_last'", ("%sT08:00:00 401" % TUE.isoformat(),))
        w_401 = PO._s702_waoff(con, True, "silent")
        con.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_last'", ("%sT08:00:00 200" % TUE.isoformat(),))
        con.commit()
    else:
        w_en = w_hi = w_nk = w_401 = ""
    ck("the order page's disabled WhatsApp line says since when (English)", w_en.startswith("The reception phone has been silent since %s 08:00" % TUE.strftime("%d-%m")))
    ck("... and in the staff's words", w_hi.startswith("Reception phone %s 08:00 se chup hai" % TUE.strftime("%d-%m")))
    ck("... no key: the old words; refused: says refused", w_nk == "The reception phone is not set up — order by call" and "refused (401)" in w_401)

    ck("the WhatsApp confirm screen says why too", PO is not None and "(esc(_s702_waoff(con, en, _why)), back," in open(PO.__file__, encoding="utf-8").read())
    con.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_last'", ("%sT10:58:00 401" % TUE.isoformat(),))
    con.commit()
    k = keys(at(TUE, 11, 0))
    ck("a phone that asks and is refused -> 'Reception phone refused' once a day (not 'silent')",
       "phone_refused:%s" % TUE.isoformat() in k and not any(x.startswith("phone:") for x in k))
    con.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_last'", ("%sT08:00:00 200" % TUE.isoformat(),))
    con.commit()

    # ---- 8b the evening pair, the overdue list, the ntfy title
    mi("w_sale_tue", "SALE_BILLWISE", TUE.isoformat(), TUE.isoformat(), "VERIFIED", "%sT22:40:00+05:30" % TUE.isoformat())
    reading("w_sale_tue", "SALE_BILLWISE", True, bills=[{}] * 18)
    mi("w_cls_tue_n", "STOCK_CLOSING", TUE.isoformat(), TUE.isoformat(), "VERIFIED", "%sT22:41:00+05:30" % TUE.isoformat(), "STOCK_CLOSING_TOTALS__n.xls")
    reading("w_cls_tue_n", "STOCK_CLOSING", True, items=[{}] * 380, printed_total=1, lines_total=1)
    ck("today's pair exported at 22:40 is said that evening (22:45), not at midnight", "pair:%s" % TUE.isoformat() in keys(at(TUE, 22, 45)))
    con.execute("DELETE FROM mi_file WHERE md5 IN ('w_sale_tue', 'w_cls_tue_n')")     # the walk replays time: no later check sees tonight's rows
    con.commit()
    ov = due + dt.timedelta(days=7)
    con.execute("DELETE FROM mi_file WHERE md5='w_salt_new'")
    con.commit()
    k = keys(at(ov, 9, 5))
    ck("an overdue list is said again a week after its due day", "list_overdue:SALT_WISE_ITEM_LIST:%s" % ov.isoformat() in k
       and "7 days overdue" in k["list_overdue:SALT_WISE_ITEM_LIST:%s" % ov.isoformat()]["body"])
    ck("... and not on the days between", not any(x.startswith("list_overdue") for x in keys(at(ov - dt.timedelta(days=3), 9, 5))))
    t = ON.ascii_title("Sanjeevni: Morning reports ✓ — x") if ON is not None and hasattr(ON, "ascii_title") else "✓"
    try:
        t.encode("latin-1")
        lat = True
    except UnicodeEncodeError:
        lat = False
    ck("the ntfy title is plain ASCII ('Morning reports OK - x'): a header never raises", lat and t == "Sanjeevni: Morning reports OK - x")
    if ON is not None:
        import fcntl
        lk = open(os.environ["OWNER_NOTICE_LOCK"], "a")
        fcntl.flock(lk.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        rb = ON.tick(con, at(TUE, 16, 9))
        lk.close()
    else:
        rb = {}
    ck("a second tick while one runs does nothing (one at a time)", bool(rb.get("busy")))

    # ---- 9 the tick: once, by the stub, never by the walk's database
    if ON is not None:
        r1 = ON.tick(con, at(TUE, 16, 10))
        r2 = ON.tick(con, at(TUE, 16, 15))
        sent = [json.loads(x) for x in open(os.environ["OWNER_NOTICE_STUB"], encoding="utf-8")] if os.path.exists(os.environ["OWNER_NOTICE_STUB"]) else []
    else:
        r1, r2, sent = {}, {}, []
    ck("the tick sends each message once (the stub), the second tick sends nothing", r1.get("sent", 0) >= 3 and r2.get("sent") == 0
       and r2.get("made") == 0 and len(sent) == r1.get("sent"))
    ck("each row is stamped sent with how it went", con.execute("SELECT COUNT(*) FROM owner_notice WHERE sent_at IS NULL").fetchone()[0] == 0
       if ON is not None else False)
    if ON is not None:
        os.environ.pop("OWNER_NOTICE_STUB")
        ok, how = ON.deliver(con, "x", "t", "b")
        os.environ["OWNER_NOTICE_STUB"] = os.path.join(SCR, "sent.jsonl")
    else:
        ok, how = True, ""
    ck("no stub: a database that is not the live one sends nothing", ok is False and "nothing sent" in how)
    if ON is not None:
        os.makedirs(os.path.join(SCR, "_off"), exist_ok=True)
        open(os.path.join(SCR, "_off", "OWNER_NOTICE_OFF"), "w").close()
        r3 = ON.tick(con, at(TUE, 16, 20))
        os.remove(os.path.join(SCR, "_off", "OWNER_NOTICE_OFF"))
    else:
        r3 = {}
    ck("the switch file stops it", r3.get("off") == "OWNER_NOTICE_OFF")
    con.execute("DROP TABLE order_sheet")
    con.commit()
    if ON is not None:
        msgs, errs = ON.collect(con, at(TUE, 16, 30))
    else:
        msgs, errs = [], ["no module"]
    ck("fail-soft: with the order sheets' table gone the other parts still speak", any(m["key"].startswith("pair:") for m in msgs) and not errs)
    con.close()
    tag = "S702 check(s)"
    print("%d of %d green" % (len(oks), len(oks) + len(fails)) if not fails else "%d %s red . %d green" % (len(fails), tag, len(oks)))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--proof" in ARGS:
        sys.exit(proof())
    if "--new" in ARGS:
        sys.exit(walk(arg("--new"), True))
    if "--old" in ARGS:
        sys.exit(walk(arg("--old"), False))
    print(__doc__)
    sys.exit(2)
