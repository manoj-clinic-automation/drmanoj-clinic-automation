#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s533.py -- kit S533_AMIR_DAY_PAGE: the walk (the brief's section 9), on the server, on scratch copies only.

    python3 -B walk_s533.py --kit DIR --work /tmp/... --run DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            --built DIR --map-new FILE --map-old FILE --archive DIR --readings DIR

  run       the installer's scratch layout: <run>/new/finance (the built amir_day, stock_app, purchase_app, stockmatch), <run>/old/finance
            (the box as it is), each with marg_ingest beside it.
  por       a scratch copy of /root/portal's code; the walk writes its OWN secret and user store there (never the live ones).
  db/adb    backup-API copies of finance.db and assets.db; spine: of the LIVE spine.db.  Every probe works on its own further copies.
  built     the built files (the data step's --modules: amir_day.py, purchase_app.py).  map-new: the built DUTY_MAP.json v11.
Probes run as fresh processes per side (NEW / OLD), signed in through the walk-only portal as amir and as the owner, with
ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing reaches a phone.  The walk's own rows are found by key
(W533 ...), never by counting.  Every named control is the same probe on the OLD files and is printed red.  No person, phone or account
number is in this file."""
import argparse
import datetime as dt
import hashlib
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
import traceback

TAG = "W533JSON "
USERS = {"amir": "staff", "manoj": "doctor"}
BASE_URL = "https://followup.dr-manoj.in"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SUP_A = "W533 SUPPLIER A"
VENDOR = "W533 VENDOR"
BAD_WORDS = ("jaanch", "dekh lijiye", "wapas", "theek karna hai", "theek karke", "sahi nahi", "hona chahiye", "Marg = shelf", "Server ko bhejo",
             "Voucher kholiye", "abhi nahi dikhe")
BAD_BOUNDED = ("Excel", "desktop", "rows", "round", "trace", "server", "hisaab")
EXEMPT = ("closing stock export kijiye", "item list export kijiye", "purchase report nikaliye", "SALT WISE ITEM LIST", "STOCK ISSUE / RECEIVE",
          "Text ya Excel", "Din phir se kholiye", "Download", "Save kijiye", "Signed in:", "biometric punch",
          "Meri entry galat thi — Marg mein theek kar di", "Supplier galat likha", "Aur voucher kholiye")
KHOLIYE_OK = (r"board kholiye", r"kaam kholiye", r"Aur voucher kholiye", r"Internet dekh kar phir kholiye", r"list kholiye",
              r"'Theek nahi' kholiye", r"— kholiye$", r"Din phir se kholiye")
RETIRED = ("_salt_list_state", "_salt_prompt_amir", "_salt_owner_line", "_applied_line", "SALTS_STATE", "_STAMP_IN_NAME", "_s444_card", "_s444_left",
           "_s444_summary_rows", "_s444_open", "_s444_voucher_line", "_s444_duties", "_s444_state", "_s444_rs", "_s444_ddmm", "_s444_days_since",
           "_s444_login", "_s444_who_line", "_packs_card_s408", "_s446_bills_list", "_s446_summary_rows", "_s446_left", "_s446_voucher_line",
           "_s446_owner_lines", "_s452_extra_hi", "_s452_left_hi", "_s454_entry_mode", "_left", "_work", "_s446_state", "_s446_watch", "_s452_state",
           "_s494_spine", "S488_TAIL_HI", "_s488_tail_hi", "_s488_wait_html", "_s488_proof", "S494_JOBS", "s494_seed_jobs", "MARK_KIT",
           "S243_AMIR_VISIT", "S246_AMIR_LIST_REOPEN", "_s444_renames", "amir_duties", "_S444_RENAMES_CACHE", "scans_to_enter", "AMIR_BILLS_FROM")
OLD_TABLES = ("amir_step", "amir_bill_disposition")
KIT_LINES = ("#   (S533: _s444_renames retired with amir_day's rebuild).",
             "passed) (S533: its second reader _s444_renames is gone). NEVER handed to a route (api_pad_report writes into its d) and never written into.\"\"\"",
             "#   * (S533: scans_to_enter retired -- step 2 reads scans_for_amir)")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1500] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def red(label, cond, got=None):
    """A control: the same probe on the OLD files must show the fault (printed RED)."""
    N[0] += 1
    print(("  RED  control: " if cond else "  FAIL control did not go red: ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append("control: " + label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def vis(h):
    """The text a person sees: no style, no script, no title, no tags, entities read."""
    h = re.sub(r"(?is)<(style|script|title)[^>]*>.*?</\1>", " ", h or "")
    h = re.sub(r"(?s)<[^>]+>", " ", h)
    return re.sub(r"\s+", " ", _html.unescape(h)).strip()


def sweep(h):
    """D708's words over a staff page's visible text -> (bad hits, exemptions used, kholiye hits (ok, context))."""
    h = re.sub(r"(?is)<div class=card id=s452neft.*?(?=<p class=foot>)", " ", h or "")     # the NEFT block the owner kept
    t = vis(h)
    used = [e for e in EXEMPT if e.lower() in t.lower()]
    kh = []
    for m in re.finditer(r"kholiye", t, flags=re.I):
        ctx = t[max(0, m.start() - 70):m.end()]
        nxt = t[m.end():m.end() + 2]
        ok = any(re.search(p, ctx) for p in KHOLIYE_OK if not p.endswith("$")) or (re.search(r"— kholiye$", ctx) is not None)
        kh.append((ok, ctx[-80:]))
    tt = t
    for e in sorted(EXEMPT, key=len, reverse=True):
        tt = re.sub(re.escape(e), " ", tt, flags=re.I)
    bad = []
    for w in BAD_WORDS:
        for m in re.finditer(re.escape(w), tt, flags=re.I):
            bad.append((w, tt[max(0, m.start() - 40):m.end() + 20]))
    for w in BAD_BOUNDED:
        for m in re.finditer(r"\b%s\b" % re.escape(w), tt, flags=re.I):
            bad.append((w, tt[max(0, m.start() - 40):m.end() + 20]))
    for m in re.finditer(r"galat\s*\?", tt, flags=re.I):
        bad.append(("galat?", tt[max(0, m.start() - 40):m.end() + 10]))
    return bad, used, kh


# ============================================================================================================== the probe (one per side)
def probe():
    SIDE, FIN, POR = os.environ["SIDE"], os.environ["FINDIR"], os.environ["PORDIR"]
    DB, ADB, BASE, ADB0 = os.environ["FINANCE_DB"], os.environ["ASSETS_DB"], os.environ["W533_BASE"], os.environ["W533_ADB0"]
    BASE_SO = os.environ.get("W533_BASE_SO") or BASE
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import purchase_app as PA                                           # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import item_alias as IA                                             # noqa: E402
    assert AD.__file__.startswith(FIN) and SA.__file__.startswith(FIN) and PA.__file__.startswith(FIN), (AD.__file__, SA.__file__)
    NEW = hasattr(AD, "DUTY_SQL")
    R = dict(side=SIDE, new=NEW)
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W533J"])["pw"]
    ck = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE_URL, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}
    now = dt.datetime.now(IST).replace(tzinfo=None, microsecond=0)
    TODAY = now.date().isoformat()
    YDAY = (now.date() - dt.timedelta(days=1)).isoformat()
    MFIRST = TODAY[:8] + "01"

    def ts(d):                                                          # 'YYYY-MM-DD HH:MM:SS'
        return d.strftime("%Y-%m-%d %H:%M:%S")

    def iso(d):
        return d.strftime("%Y-%m-%dT%H:%M:%S")

    def stamp(d):
        return d.strftime("%Y%m%d-%H%M%S")

    def clear_caches():
        for nm in ("_S446_PROOF_CACHE", "_S524_REPORT_CACHE", "_S444_RENAMES_CACHE"):
            if hasattr(SA, nm):
                getattr(SA, nm).clear()

    def load(base=None):
        copydb(base or BASE, DB)
        copydb(ADB0, ADB)
        clear_caches()

    def C():
        c = sqlite3.connect(DB, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def cols(c, t):
        return [r[1] for r in c.execute("PRAGMA table_info(%s)" % t).fetchall()]

    def ins(c, table, row):
        row = dict(row)
        for _cid, name, typ, notnull, dflt, pk in c.execute("PRAGMA table_info(%s)" % table).fetchall():
            if notnull and dflt is None and not pk and name not in row:
                row[name] = 0 if "INT" in (typ or "").upper() else ""
        ks = [k for k in row if k in cols(c, table)]
        return c.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(ks), ", ".join("?" * len(ks))), [row[k] for k in ks]).lastrowid

    def md5t(tag):
        return hashlib.md5(("W533 " + tag).encode()).hexdigest()

    def export(c, tag, typ, pf, pt, when, received=None, sup_by=None):
        md5 = md5t(tag)
        ins(c, "purchase_export", dict(md5=md5, type=typ, file="w533_%s" % tag, period_from=pf, period_to=pt, export_stamp=stamp(when),
                                       received_at=iso(received or when), n_rows=1, grand_amount_p=0, superseded_by=sup_by))
        return md5

    def bill(c, bno, md5, amount=148200, first_seen=None, scan=None, sup=SUP_A, bdate=None):
        row = dict(supplier_norm=sup, supplier=sup, bill_no=bno, bill_date=bdate or TODAY, month=(bdate or TODAY)[:7], cash_p=0, credit_p=amount,
                   amount_p=amount, bw_amount_p=amount, source_md5=md5, bw_md5=md5, date_src="BILLWISE", scan_bill_id=scan)
        if "first_seen_day" in cols(c, "purchase_bill"):
            row["first_seen_day"] = first_seen or TODAY
        return ins(c, "purchase_bill", row)

    def answer(c, bid, bno, reason, at, by="amir", sup=SUP_A, bdate=None):
        if NEW:
            return ins(c, "amir_bill_answer", dict(bill_id=bid, supplier_norm=sup, bill_no=bno, bill_date=bdate or TODAY, day=at[:10], reason=reason,
                                                   by_user=by, at=at))
        c.execute("INSERT OR REPLACE INTO amir_bill_disposition (supplier_norm, bill_no, bill_date, day, reason, by_user, at) VALUES (?,?,?,?,?,?,?)",
                  (sup, bno, bdate or TODAY, at[:10], reason, by, at))
        return None

    def self_wait(c, bno, md5, export_at, marg_p, paper_p=None, bid=None, sup=SUP_A, bdate=None):
        row = dict(supplier_norm=sup, bill_no=bno, bill_date=bdate or TODAY, marked_at=ts(now - dt.timedelta(hours=1)), marked_by="amir", marg_p=marg_p,
                   paper_p=paper_p, paper_src=("scan" if paper_p is not None else None), export_md5=md5, export_at=export_at)
        if NEW:
            row["bill_id"] = bid
        else:
            c.execute("CREATE TABLE IF NOT EXISTS amir_self_wait (supplier_norm TEXT NOT NULL, bill_no TEXT NOT NULL, bill_date TEXT NOT NULL, marked_at TEXT NOT NULL, "
                      "marked_by TEXT, marg_p INTEGER, paper_p INTEGER, paper_src TEXT, export_md5 TEXT, export_at TEXT, cleared_at TEXT, cleared_how TEXT, "
                      "PRIMARY KEY(supplier_norm, bill_no, bill_date))")
        ins(c, "amir_self_wait", row)

    def steplog(c, step, at, note=None, day=None):
        day = day or TODAY
        c.execute("INSERT OR IGNORE INTO amir_day (day, opened_at) VALUES (?,?)", (day, at))
        if NEW:
            ins(c, "amir_step_log", dict(day=day, step=step, done_at=at, by_user="amir", note=note))
        else:
            c.execute("INSERT OR REPLACE INTO amir_step (day, step, done_at, by_user) VALUES (?,?,?,?)", (day, step, at, "amir"))

    def salt_tick(c, at, tag="W533 SALT TASK"):
        ins(c, "purchase_salt_task", dict(section="cleanup", seq=99533, a=tag, done=1, done_by="amir", done_at=at))

    def pair_today(c):
        e1 = export(c, "IW today", "ITEMWISE", MFIRST, TODAY, now.replace(hour=7, minute=50, second=0), now.replace(hour=7, minute=52, second=0))
        e2 = export(c, "BW today", "BILLWISE", MFIRST, TODAY, now.replace(hour=7, minute=30, second=0), now.replace(hour=7, minute=32, second=0))
        return e1, e2

    def GET(path, who):
        t0 = time.perf_counter()
        r = fc.get(path, base_url=BASE_URL, headers=ck[who])
        ms = int((time.perf_counter() - t0) * 1000)
        body = r.get_data(as_text=True)
        return r.status_code, body, ms, r.headers.get("Location", "")

    def POST(path, who, data):
        r = fc.post(path, base_url=BASE_URL, headers=ck[who], data=data)
        return r.status_code, r.headers.get("Location", "")

    # ---- call counters (per request): the stage, its words, the scans, the assets door
    calls = {}

    inside = [0]

    def counted(mod, name):
        real = getattr(mod, name)

        def f(*a, **k):
            calls[name] = calls.get(name, 0) + 1
            if name == "_assets_con" and inside[0]:
                calls["_assets_con_in_scans"] = calls.get("_assets_con_in_scans", 0) + 1
            if name == "scans_for_amir":
                inside[0] += 1
                try:
                    return real(*a, **k)
                finally:
                    inside[0] -= 1
            return real(*a, **k)
        setattr(mod, name, f)
        return real
    real_stage = counted(SA, "amir_stage")
    real_words = counted(SA, "_s521_stage_words")
    real_scans = counted(PA, "scans_for_amir")
    real_assets = counted(PA, "_assets_con")

    def block(name, fn):
        try:
            R[name] = fn()
        except Exception as e:                                          # noqa: BLE001
            R[name] = dict(error="%s: %s" % (type(e).__name__, str(e)[:300]), tb=traceback.format_exc()[-1500:])

    def setup_busy(c):
        """The busy day (by key): punched, the export just tapped (transit), today's bill-wise export with five walk bills -- today 2,
        carry 1, flagged 1, his own correction 1 -- a salt tick after the newest list, one open one-time job."""
        steplog(c, 1, ts(now - dt.timedelta(minutes=30)), "punched")
        steplog(c, 3, ts(now - dt.timedelta(minutes=2)), "export")
        e2 = export(c, "BW today", "BILLWISE", MFIRST, TODAY, now.replace(hour=7, minute=30, second=0), now.replace(hour=7, minute=32, second=0))
        ids = {}
        ids["W1"] = bill(c, "W533-1", e2, amount=148200, scan=145)
        ids["W2"] = bill(c, "W533-2", e2, amount=10000)
        ids["W3"] = bill(c, "W533-3", e2, amount=20000, first_seen=YDAY)
        ids["W4"] = bill(c, "W533-4", e2, amount=30000)
        ids["W5"] = bill(c, "W533-5", e2, amount=40000)
        answer(c, ids["W4"], "W533-4", "short", ts(now - dt.timedelta(hours=1)))
        answer(c, ids["W5"], "W533-5", "self", ts(now - dt.timedelta(hours=1)))
        self_wait(c, "W533-5", e2, iso(now.replace(hour=7, minute=32, second=0)), 40000, bid=ids["W5"])
        salt_tick(c, iso(now - dt.timedelta(minutes=10)))
        if "reopened_at" in cols(c, "amir_job") or not NEW:
            pass
        ins(c, "amir_job", dict(key="w533:vbill", kind="vendor_bill", subject=SUP_A, created_at=ts(now), created_by="W533", show_from=ts(now)))
        c.commit()
        return ids

    # ---------------------------------------------------------------------------------------------------- 0. the live state, by key
    def b0():
        load()
        c = C()
        out = {}
        root = SA._s446_root(c)
        st = real_stage(c, root)
        out["root"], out["stage"] = root, (st or {}).get("stage")
        A = (st or {}).get("A") or {}
        out["A"] = dict(total=A.get("total"), entered=A.get("entered"), open=A.get("open"), pending=A.get("pending"), proof=(A.get("proof") or {}).get("state"))
        out["B"] = {k: v for k, v in ((st or {}).get("B") or {}).items() if k in ("total", "verified", "ticked", "questions")}
        out["events"] = [tuple(r) for r in c.execute("SELECT stage, event FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,)).fetchall()]
        out["renames"] = [tuple(r) for r in c.execute("SELECT id, old_name, new_name, verified_at IS NOT NULL FROM marg_item_rename WHERE old_name IN (?,?)",
                                                       ("L S BELT CONT GRAY UNISON XXX", "TYNOR WRIST SPLINT LF M ELAS")).fetchall()]
        sc = real_scans(c)
        out["yuvika"] = [(x.get("supplier"), x.get("scan_day")) for x in sc.get("list") or [] if "YUVIKA" in str(x.get("supplier") or "")]
        out["scans_listed"], out["scans_held"] = len(sc.get("list") or []), len(sc.get("held") or [])
        out["roles"] = [tuple(r) for r in c.execute("SELECT unit, username, role FROM unit_role WHERE unit='medical' AND username IN ('amir','manoj') AND active=1").fetchall()]
        out["old_rows"] = {t: (c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0] if c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone() else None)
                           for t in OLD_TABLES + ("amir_step_log", "amir_bill_answer")}
        if NEW:
            out["duty_sql"] = AD.DUTY_SQL
            out["s494_open"] = AD.S494_OPEN
            import aaj_seed                                             # noqa: E402
            out["rewrite_piece"] = aaj_seed.REWRITE["amir.bills_answer"][0]
            so = sqlite3.connect("file:%s?mode=ro" % BASE_SO, uri=True)
            out["duty_rows_schema_only"] = {k: list(so.execute(s).fetchone()) for k, s in AD.DUTY_SQL.items()}
            so.close()
            out["duty_rows_full"] = {k: list(c.execute(s).fetchone()) for k, s in AD.DUTY_SQL.items()}
            S = AD.state(c, TODAY, "amir")
            out["bills_counts"] = dict(today=len(S.bills["today"]), carry=len(S.bills["carry"]), flagged=len(S.bills["flagged"]), waiting=len(S.bills["waiting"]))
            out["card"] = [r[2] for r in S.card]
        c.close()
        return out
    block("b0", b0)

    # ---------------------------------------------------------------------------------------------------- 1. one read, one word
    def one_state(name, prep):
        load()
        c = C()
        prep(c)
        c.commit()
        out = dict(name=name)
        if NEW:
            S = AD.state(c, TODAY, "amir")
            out["gate"] = [(g[1], g[2]) for g in S.gate_open]
            out["extra"] = [list(x) for x in S.extra]
            out["closed"] = bool(S.closed)
            out["head"], out["second"] = AD.owner_state_line(S)
            out["stage_en"] = (S.sw or {}).get("owner_en")
            out["root"] = (S.stage or {}).get("count_id")
            out["card_hi"] = [r[2] for r in S.card if r[0] == "stage"]
        c.close()
        calls.clear()
        code, h7, ms7, _l = GET("/finance/amir/step/7", "amir")
        out["s7"] = dict(code=code, text=vis(h7), calls=dict(calls), ms=ms7)
        calls.clear()
        code, h1, ms1, _l = GET("/finance/amir/step/1", "amir")
        out["s1"] = dict(code=code, text=vis(h1), calls=dict(calls), ms=ms1)
        code, hd, _ms, _l = GET("/finance/amir/day", "manoj")
        m = re.search(r"id=daystate>(.*?)</p>", hd, flags=re.S)
        m2 = re.search(r"id=daynothold>(.*?)</p>", hd, flags=re.S)
        out["owner"] = dict(code=code, head=_html.unescape(m.group(1)) if m else None, second=_html.unescape(m2.group(1)) if m2 else None, text=vis(hd)[:3000])
        r = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["manoj"])
        j = r.get_json(silent=True) or {}
        out["visit"] = dict(code=r.status_code, left=j.get("left"), s7=[s for s in (j.get("steps") or []) if s.get("n") == 7], state=j.get("state"))
        c = C()
        out["needs"] = [l.get("text") for l in AD.needs_you_lines(c)]
        c.close()
        return out

    def prep_empty(c):
        pass

    def prep_bad(c):
        steplog(c, 3, ts(now - dt.timedelta(minutes=20)), "export")
        export(c, "BW bad", "BILLWISE", MFIRST, YDAY, now.replace(hour=7, minute=10, second=0), now - dt.timedelta(minutes=15))

    def prep_closable(c):
        pair_today(c)
        steplog(c, 2, ts(now - dt.timedelta(minutes=25)))
        steplog(c, 6, ts(now - dt.timedelta(minutes=5)))

    def b1():
        out = []
        for name, prep in (("empty", prep_empty), ("busy", setup_busy), ("bad", prep_bad), ("closable", prep_closable)):
            out.append(one_state(name, prep))
        return out
    block("b1", b1)

    def b1c():
        """Where the old file asked the stage again: a one-time category job not yet shown (its refresh read the stage a second time)."""
        load()
        c = C()
        ins(c, "amir_job", dict(key="w533:cat0", kind="category", subject="W533 CAT ITEM", created_at=ts(now), created_by="W533"))
        c.commit()
        calls.clear()
        GET("/finance/amir/step/1", "amir")
        s1 = dict(calls)
        calls.clear()
        AD.needs_you_lines(c)
        ny = dict(calls)
        c.close()
        return dict(step1=s1, needs=ny)
    block("b1c", b1c)

    # ---------------------------------------------------------------------------------------------------- 2. append-only
    def b2():
        out = {}
        load()
        POST("/finance/amir/step/1", "amir", {"tick": "1", "punch": "yes", "go": "1"})
        POST("/finance/amir/step/1", "amir", {"tick": "1", "punch": "no", "go": "1"})
        c = C()
        if NEW:
            out["punch"] = [tuple(r) for r in c.execute("SELECT id, note, replaces FROM amir_step_log WHERE day=? AND step=1 ORDER BY id", (TODAY,)).fetchall()]
        else:
            out["punch"] = [tuple(r) for r in c.execute("SELECT day, step, done_at FROM amir_step WHERE day=? AND step=1", (TODAY,)).fetchall()]
        c.close()
        r = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["manoj"])
        out["punch_summary"] = [s for s in ((r.get_json(silent=True) or {}).get("steps") or []) if s.get("n") == 1]
        # a bill answered twice
        load()
        c = C()
        e2 = export(c, "BW today", "BILLWISE", MFIRST, TODAY, now.replace(hour=7, minute=30, second=0), now.replace(hour=7, minute=32, second=0))
        b1_ = bill(c, "W533-1", e2, amount=10000)
        c.commit()
        c.close()
        key = "%d|%s|%s|%s" % (b1_, SUP_A, "W533-1", TODAY) if NEW else "%s|%s|%s" % (SUP_A, "W533-1", TODAY)
        POST("/finance/amir/step/5", "amir", {"n": "1", "k_0": key, "r_0": "short", "go": "5"})
        POST("/finance/amir/step/5", "amir", {"n": "1", "k_0": key, "r_0": "ok", "go": "5"})
        c = C()
        if NEW:
            out["answers"] = [tuple(r) for r in c.execute("SELECT id, reason, by_user, replaces FROM amir_bill_answer WHERE bill_id=? ORDER BY id", (b1_,)).fetchall()]
        else:
            out["answers"] = [tuple(r) for r in c.execute("SELECT reason, by_user FROM amir_bill_disposition WHERE bill_no='W533-1'").fetchall()]
        out["claims"] = [tuple(r) for r in c.execute("SELECT state, settled_outcome FROM amir_claim WHERE bill_no='W533-1'").fetchall()]
        out["audit"] = [r[0] for r in c.execute("SELECT action FROM purchase_audit WHERE ref LIKE ? ORDER BY id", ("%W533-1%",)).fetchall()]
        c.close()
        # close, reopen, close, close again
        load()
        c = C()
        prep_closable(c)
        c.commit()
        c.close()
        seq = []
        for data in ({"go": "7"}, {"reopen": "1", "go": "7"}, {"go": "7"}, {"go": "7"}):
            seq.append(POST("/finance/amir/step/7", "amir", data))
        c = C()
        if NEW:
            out["step7"] = [tuple(r) for r in c.execute("SELECT id, note, replaces FROM amir_step_log WHERE day=? AND step=7 ORDER BY id", (TODAY,)).fetchall()]
        out["closed_at"] = c.execute("SELECT closed_at, reopened_at FROM amir_day WHERE day=?", (TODAY,)).fetchone()
        out["closed_at"] = list(out["closed_at"]) if out["closed_at"] else None
        c.close()
        out["posts7"] = seq
        r = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["manoj"])
        j = r.get_json(silent=True) or {}
        out["closed_json"] = dict(state=j.get("state"), closed_at=j.get("closed_at"), reopened_at=j.get("reopened_at"))
        if not NEW:
            # the old reopen: close (one step-7 row), then reopen -> the row is DELETEd
            load()
            c = C()
            prep_closable(c)
            c.commit()
            c.close()
            POST("/finance/amir/step/7", "amir", {"go": "7"})
            c = C()
            n1 = c.execute("SELECT COUNT(*) FROM amir_step WHERE day=? AND step=7", (TODAY,)).fetchone()[0]
            c.close()
            POST("/finance/amir/step/7", "amir", {"reopen": "1", "go": "7"})
            c = C()
            n2 = c.execute("SELECT COUNT(*) FROM amir_step WHERE day=? AND step=7", (TODAY,)).fetchone()[0]
            c.close()
            out["old_reopen_rows"] = [n1, n2]
        return out
    block("b2", b2)

    def self_case(kind):
        """One self-clear case on its own copy -> what settle did (NEW) or what the old clear did (OLD, case i only)."""
        load()
        c = C()
        e_old = export(c, "BW old", "BILLWISE", MFIRST, YDAY, now - dt.timedelta(days=1, hours=2), now - dt.timedelta(days=1, hours=2))
        e_new = export(c, "BW new", "BILLWISE", MFIRST, TODAY, now.replace(hour=7, minute=30, second=0), now.replace(hour=7, minute=32, second=0))
        bno, out = "W533-9", dict(kind=kind)
        if kind in ("i", "ib", "ib_same"):
            scan = 990533 if kind == "i" else None
            bid = bill(c, bno, e_new, amount=50000, scan=scan)
            if scan:
                ins(c, "purchase_scan_state", dict(asset_bill_id=scan, why="no_bill_yet"))
                if "paper_amount" in cols(c, "purchase_scan_state"):
                    c.execute("UPDATE purchase_scan_state SET paper_amount=? WHERE asset_bill_id=?", (50000, scan))
                out["paper_col"] = "paper_amount" in cols(c, "purchase_scan_state")
            ex_at = iso(now.replace(hour=7, minute=32, second=0)) if kind == "ib_same" else iso(now - dt.timedelta(days=1, hours=2))
            sa = answer(c, bid, bno, "self", ts(now - dt.timedelta(hours=3)))
            self_wait(c, bno, e_old, ex_at, 49000, (50000 if kind == "i" else None), bid=bid)
        elif kind in ("ii", "ii_live"):
            if kind == "ii":
                e_sup = export(c, "BW sup", "BILLWISE", MFIRST, TODAY, now.replace(hour=7, minute=40, second=0), now.replace(hour=7, minute=41, second=0))
                e_x = export(c, "BW x", "BILLWISE", MFIRST, YDAY, now - dt.timedelta(days=1, hours=4), now - dt.timedelta(days=1, hours=4), sup_by=e_sup)
                bid = bill(c, bno, e_x, amount=50000)
                ex_at = iso(now - dt.timedelta(days=1, hours=4))
            else:
                r = c.execute("SELECT md5, received_at FROM purchase_export WHERE type='BILLWISE' AND superseded_by IS NULL AND period_from=? AND period_to=?",
                              (TODAY[:5] + "09-01", TODAY[:5] + "09-30")).fetchone()
                e_x, ex_at = (r[0], r[1]) if r else (e_old, iso(now - dt.timedelta(days=1, hours=2)))
                bid = bill(c, bno, e_x, amount=50000, bdate=TODAY[:5] + "09-15")
                out["live_sept"] = bool(r)
            bdate = TODAY[:5] + "09-15" if kind == "ii_live" else None
            sa = answer(c, bid, bno, "self", ts(now - dt.timedelta(hours=3)), bdate=bdate)
            self_wait(c, bno, e_x, ex_at, 49000, bid=bid, bdate=bdate)
        else:                                                           # iii: he answered again
            bid = bill(c, bno, e_new, amount=50000)
            sa = answer(c, bid, bno, "self", ts(now - dt.timedelta(hours=3)))
            self_wait(c, bno, e_old, iso(now - dt.timedelta(days=1, hours=2)), 49000, bid=bid)
            answer(c, bid, bno, "ok", ts(now - dt.timedelta(hours=1)))
        c.commit()
        a0 = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='amir_self_cleared'").fetchone()[0]
        if NEW:
            S = AD.state(c, TODAY, "amir", step=5)
            notes = AD.settle(c, S)
            out["notes"] = len(notes)
            out["wait"] = list(c.execute("SELECT cleared_how FROM amir_self_wait WHERE bill_no=?", (bno,)).fetchone())
            out["rows"] = [tuple(r) for r in c.execute("SELECT id, reason, by_user, note, replaces FROM amir_bill_answer WHERE bill_id=? ORDER BY id", (bid,)).fetchall()]
            out["self_row"] = sa
            out["audit"] = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='amir_self_cleared'").fetchone()[0] - a0
            S2 = AD.state(c, TODAY, "amir", step=5)
            out["again"] = len(AD.settle(c, S2))
        else:
            before = list(c.execute("SELECT reason, by_user FROM amir_bill_disposition WHERE bill_no=?", (bno,)).fetchone())
            AD._s444_self_clear(c)
            after = list(c.execute("SELECT reason, by_user FROM amir_bill_disposition WHERE bill_no=?", (bno,)).fetchone())
            out["old_row"] = [before, after]
        c.close()
        return out

    def b2s():
        if not NEW:
            return dict(i=self_case("i"))
        return {k: self_case(k) for k in ("i", "ib", "ib_same", "ii", "ii_live", "iii")}
    block("b2s", b2s)

    # ---------------------------------------------------------------------------------------------------- 3. the bills
    def b3():
        load()
        c = C()
        ids = setup_busy(c)
        out = dict(ids=ids)
        if NEW:
            S = AD.state(c, TODAY, "amir", step=5)
            out["lists"] = {k: sorted(x["id"] for x in S.bills[k]) for k in ("today", "carry", "flagged", "waiting")}
            out["paper_w1"] = (S.bills["by_id"].get(ids["W1"]) or {}).get("paper")
            # a later push carrying W1 moves its bw_md5 and keeps its first sight; a new bill's first sight is its export's day
            md5n = export(c, "BW later", "BILLWISE", MFIRST, TODAY, now.replace(hour=9, minute=0, second=0) + dt.timedelta(days=1),
                          now.replace(hour=9, minute=1, second=0))
            c.commit()
            fs0 = c.execute("SELECT first_seen_day FROM purchase_bill WHERE id=?", (ids["W3"],)).fetchone()[0]
            PA._store_bills(c, "BILLWISE", md5n, [dict(supplier=SUP_A, bill_no="W533-3", bill_date=TODAY, cash_p=0, credit_p=20000),
                                                  dict(supplier=SUP_A, bill_no="W533-NEW", bill_date=TODAY, cash_p=0, credit_p=5000)])
            c.commit()
            r3 = c.execute("SELECT bw_md5, first_seen_day FROM purchase_bill WHERE id=?", (ids["W3"],)).fetchone()
            rn = c.execute("SELECT first_seen_day FROM purchase_bill WHERE bill_no='W533-NEW'").fetchone()
            out["move"] = dict(before=fs0, after=r3[1], moved=(r3[0] == md5n), new_first=rn[0] if rn else None,
                               new_expect=(now + dt.timedelta(days=1)).date().isoformat())
        else:
            w = AD._work(c, TODAY)
            out["old_lists"] = {k: sorted(x["bill_no"] for x in w[k]) for k in ("today_bills", "carry_bills", "flagged_bills")}
        c.close()
        load()
        c = C()
        setup_busy(c)
        c.close()
        code, h5, _ms, _l = GET("/finance/amir/step/5", "amir")
        code7, h7, _ms, _l = GET("/finance/amir/step/7", "amir")
        coded, hd, _ms, _l = GET("/finance/amir/day", "manoj")
        rx = r"Aaj aaye bill: (\d+) · Pichhle dinon ke baaki: (\d+) · Flag kiye hue: (\d+)"
        t5, t7, td = vis(h5), vis(h7), vis(hd)
        out["s5"] = dict(code=code, counts=re.findall(rx, t5), waiting_head=("Aapki sudhaar — Marg ki agli export ka intezaar: 1" in t5),
                         iso=re.findall(r"\d{4}-\d{2}-\d{2}", t5)[:5], paper=re.findall(r"Marg \(export [^)]*\): ₹[\d,]+ · Kaagaz \(scan [^)]*\): ₹[\d,]+ · mil gaya", t5),
                         marker=("Har bill par ek tap" in t5), self_marker=("Marg ki agli export ka intezaar" in t5))
        out["s7"] = dict(code=code7, counts=re.findall(rx, t7))
        out["owner"] = dict(code=coded, counts=[re.findall(r"Today's bills, still to tap: (\d+)", td), re.findall(r"Carried from earlier days: (\d+)", td),
                                                re.findall(r"Flagged: (\d+)", td), re.findall(r"His corrections awaiting Marg: (\d+)", td)])
        return out
    block("b3", b3)

    # ---------------------------------------------------------------------------------------------------- 4. the gate (nothing on the card)
    def b4():
        load()
        c = C()
        pair_today(c)
        steplog(c, 2, ts(now - dt.timedelta(minutes=25)))
        salt_tick(c, iso(now - dt.timedelta(minutes=10)))
        c.commit()
        c.close()
        saved = (SA.amir_stage, PA.scans_for_amir, SA.amir_rate_due, SW.amir_view, getattr(SA, "amir_duties", None))
        SA.amir_stage = lambda *a, **k: None
        PA.scans_for_amir = lambda con: dict(list=[], held=[], ok=True)
        SA.amir_rate_due = lambda con: []
        SW.amir_view = lambda con: dict(ok=True, plan=None, bill_pending=[], fixes=[])
        if not NEW:
            SA.amir_duties = lambda con: dict(counts=[], renames=None)
        out = {}
        try:
            c = C()
            if NEW:
                S = AD.state(c, TODAY, "amir")
                out["done6"], out["ready"], out["gate"], out["extra"] = S.done[6], AD._ready_to_close(S), [g[2] for g in S.gate_open], [x[1] for x in S.extra]
                out["card"] = [r[0] for r in S.card]
            else:
                w = AD._work(c, TODAY)
                out["old_left"] = AD._left(w)
                out["old_ready"] = AD._ready_to_close(w)
            c.close()
            _c, h6, _m, _l = GET("/finance/amir/step/6", "amir")
            _c, h7, _m, _l = GET("/finance/amir/step/7", "amir")
            _c, hd, _m, _l = GET("/finance/amir/day", "manoj")
            m = re.search(r"id=daystate>(.*?)</p>", hd, flags=re.S)
            m2 = re.search(r"id=daynothold>(.*?)</p>", hd, flags=re.S)
            out["s6_nothing"] = "Aaj Marg mein sudhaar ka kuch nahi hai" in vis(h6)
            out["s7_ready"] = "Din band karein?" in vis(h7)
            out["owner_head"] = _html.unescape(m.group(1)) if m else vis(hd)[:300]
            out["owner_second"] = _html.unescape(m2.group(1)) if m2 else None
        finally:
            SA.amir_stage, PA.scans_for_amir, SA.amir_rate_due, SW.amir_view = saved[:4]
            if saved[4] is not None:
                SA.amir_duties = saved[4]
        return out
    block("b4", b4)

    # ---------------------------------------------------------------------------------------------------- 5. D712
    def b5():
        load()
        c = C()
        oid = ins(c, "purchase_order", dict(created_at=iso(now - dt.timedelta(days=6)), created_by="W533", vendor=VENDOR, status="sent"))
        ins(c, "purchase_order_line", dict(order_id=oid, item="W533 ITEM", packs=1, pack_size=1, units=1, supplied=1, arrived_by="W533",
                                           arrived_at=iso(now - dt.timedelta(days=5))))
        c.commit()
        out = {}
        _c, h1, _m, _l = GET("/finance/amir/step/1", "amir")
        t1 = vis(h1)
        out["maal"] = "Maal aa gaya" in t1
        out["card_n"] = [int(x) for x in re.findall(r"Scan hua bill Marg mein baaki: (\d+)", t1)]
        _c, h2, _m, _l = GET("/finance/amir/step/2", "amir")
        out["s2_paper_n"] = [int(x) for x in re.findall(r"Scan ho chuke bill \((\d+)\)", vis(h2))]
        out["s2_paper_id"] = "id=scans" in h2
        if NEW:
            out["needs"] = [l["text"] for l in AD.needs_you_lines(c) if VENDOR in l.get("text", "")]
            # a held scan from that vendor (read_vendor), made 4 days ago
            a = sqlite3.connect(ADB)
            ins(a, "bills", dict(kind="Pharmacy", vendor=VENDOR, bill_no="W533S1", total_amount=777.0, created_at=ts(now - dt.timedelta(days=4)),
                                 stamp_no="W533-1", status="captured"))
            a.commit()
            a.close()
            S = AD.state(c, TODAY, "amir")
            out["held"] = [x.get("read_vendor") for x in S.held if x.get("read_vendor") == VENDOR]
            out["needs_held"] = [l["text"] for l in AD.needs_you_lines(c) if VENDOR in l.get("text", "")]
            # a listed scan by its supplier (the rule itself, on what state() read)
            S.held = []
            S.scans = [dict(supplier=VENDOR, scan_day=(now - dt.timedelta(days=4)).date().isoformat())]
            out["listed_near"] = [l["text"] for l in AD._d712_owner_lines(c, S) if VENDOR in l["text"]]
            S.scans = [dict(supplier=VENDOR, scan_day=(now - dt.timedelta(days=10)).date().isoformat())]
            out["listed_far"] = [l["text"] for l in AD._d712_owner_lines(c, S) if VENDOR in l["text"]]
            c.execute("INSERT INTO setting (key, value) VALUES ('purchase.entry_mode','both') ON CONFLICT(key) DO UPDATE SET value='both'")
            c.commit()
            _c, h2b, _m, _l = GET("/finance/amir/step/2", "amir")
            _c, h1b, _m, _l = GET("/finance/amir/step/1", "amir")
            out["s2_both_n"] = [int(x) for x in re.findall(r"Marg mein daalne ke bill \((\d+)\)", vis(h2b))]
            out["card_n_both"] = [int(x) for x in re.findall(r"Scan hua bill Marg mein baaki: (\d+)", vis(h1b))]
            out["s2_both_id"] = "id=scans" in h2b
            out["s2_both_sweep"] = sweep(h2b)
        c.close()
        return out
    block("b5", b5)

    # ---------------------------------------------------------------------------------------------------- 6. the salt list
    def b6():
        out = {}
        load()
        c = C()
        salt_tick(c, iso(now - dt.timedelta(minutes=60)))
        ins(c, "mi_file", dict(md5=md5t("salt list"), type="SALT_WISE_ITEM_LIST", verdict="VERIFIED", stamp=stamp(now - dt.timedelta(days=1)),
                               received_at=iso(now - dt.timedelta(minutes=30)) + "+05:30"))
        c.commit()
        if NEW:
            out["one_rule"] = AD._s444_salt(c)
        else:
            out["old_rule_a"] = AD._salt_list_state(c, TODAY).get("pending")
            out["old_rule_b"] = AD._s444_salt(c).get("pending")
        c.close()
        load()
        c = C()
        salt_tick(c, iso(now - dt.timedelta(minutes=10)))
        ins(c, "purchase_salt_task", dict(section="cleanup", seq=99534, a="W533 OPEN SALT TASK", done=0))      # one open task of the walk's own
        c.commit()
        if NEW:
            out["card0"] = AD._s444_salt_card({"s444": {"salt": AD._s444_salt(c)}})
            for d in ("2099-01-01", "2099-01-02"):
                c.execute("INSERT INTO amir_day (day, opened_at) VALUES (?,?)", (d, d + " 09:00:00"))
            out["card2"] = AD._s444_salt_card({"s444": {"salt": AD._s444_salt(c)}})
            c.execute("DELETE FROM amir_day WHERE day LIKE '2099-%'")       # the walk's own two rows, on its own copy
        c.commit()
        c.close()
        _c, h6, _m, _l = GET("/finance/amir/step/6", "amir")
        _c, h7, _m, _l = GET("/finance/amir/step/7", "amir")
        _c, hd, _m, _l = GET("/finance/amir/day", "manoj")
        _c, hs, _m, _l = GET("/finance/amir/salts", "amir")
        out["ids"] = dict(s6=h6.count("id=s444salt"), s7=h7.count("id=s444salt"), owner=hd.count("id=s444salt"), salts_page=hs.count("id=s444salt"))
        out["nikaalo"] = dict(s6=vis(h6).count("SALT WISE ITEM LIST nikaalo"), s7=vis(h7).count("SALT WISE ITEM LIST nikaalo"))
        out["door_with_rows"] = "id=saltsdoor" in h6
        out["salts_page"] = _c
        r = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["manoj"])
        out["hub_keys"] = sorted(((r.get_json(silent=True) or {}).get("salt_list") or {}).keys())
        out["hub_salt"] = (r.get_json(silent=True) or {}).get("salt_list")
        c = C()
        c.execute("UPDATE purchase_salt_task SET section='w533_' || section WHERE COALESCE(done,0)=0")   # the walk's own copy: no open task
        c.commit()
        c.close()
        _c, h6b, _m, _l = GET("/finance/amir/step/6", "amir")
        out["door_without_rows"] = "id=saltsdoor" in h6b
        return out
    block("b6", b6)

    # ---------------------------------------------------------------------------------------------------- 7. the duty map, the staff eye
    def b7():
        if not NEW:
            return {}
        out = {}
        load()
        c = C()
        setup_busy(c)
        c.close()
        dm = json.load(open(os.environ["DUTY_MAP_JSON"], encoding="utf-8"))
        ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
        duties = []
        for du in dm.get("duties") or []:
            if du.get("person") != "amir":
                continue
            row = dict(id=du["id"], marker=du.get("door_marker"), door=du.get("door"), due=None, seen=None)
            try:
                rr = ro.execute(str(du.get("due_sql") or "").rstrip(";")).fetchone()
                row["due"] = int((rr[0] if rr else 0) or 0)
            except Exception as e:                                      # noqa: BLE001
                row["due"] = "ERR " + str(e)[:80]
            if isinstance(row["due"], int) and row["due"] > 0 and row["door"] and row["marker"] and str(row["door"]).startswith("/finance/"):
                path, body = row["door"], ""
                for _hop in range(4):
                    r = fc.get(path, base_url=BASE_URL, headers=ck["amir"])
                    if r.status_code in (301, 302, 303) and r.headers.get("Location", "").replace(BASE_URL, "").startswith("/finance/"):
                        path = r.headers["Location"].replace(BASE_URL, "")
                        continue
                    body = r.get_data(as_text=True)
                    break
                row["seen"] = row["marker"] in _html.unescape(body)
            duties.append(row)
        ro.close()
        out["duties"] = duties
        r = fc.get("/finance/aaj/api/list", base_url=BASE_URL, headers=ck["amir"])
        j = r.get_json(silent=True) or {}
        txt = json.dumps(j, ensure_ascii=False)
        ids_ = sorted(set(re.findall(r'"id":\s*"(amir\.[a-z_]+)"', txt)))
        out["aaj"] = dict(code=r.status_code, ids=ids_, bills_line=("amir.bills_answer" in ids_ or "Har purchase bill par jawab" in txt),
                          arrival_line=("amir.arrival_bill_entry" in ids_ or "Maal aa gaya hai" in txt), unread=re.findall(r'"unread":\s*(\d+)', txt)[:3],
                          keys=sorted(j.keys())[:12], size=len(txt), error=str(j.get("error") or "")[:120])
        import aaj_kaam                                                 # noqa: E402
        rd = aaj_kaam.build_all(DB)
        out["aaj_items"] = {it["id"]: dict(n=it.get("n"), err=it.get("err")) for it in rd.get("items") or [] if str(it.get("id", "")).startswith("amir.")}
        import owner_console                                            # noqa: E402
        oc = owner_console.read_duties(DB)
        out["console"] = {d["id"]: dict(n=d["n"], err=d["err"], late=d["late"]) for d in oc["duties"] if str(d["id"]).startswith("amir.")}
        out["console_version"] = oc.get("version")
        return out
    block("b7", b7)

    # ---------------------------------------------------------------------------------------------------- 8. stockmatch c4
    def b8():
        out = {}

        def renames_cond():
            r = fc.get("/finance/stockmatch/api/state", base_url=BASE_URL, headers=ck["manoj"])
            j = r.get_json(silent=True) or {}
            found = []

            def walk_(x):
                if isinstance(x, dict):
                    if x.get("key") == "renames" and "en" in x:
                        found.append(dict(ok=x.get("ok"), en=x.get("en"), hi=x.get("hi")))
                    if "renames_wait_stage_a" in x:
                        found.append(dict(wait=x.get("renames_wait_stage_a"), total=(x.get("renames") or {}).get("total")))
                    for v in x.values():
                        walk_(v)
                elif isinstance(x, list):
                    for v in x:
                        walk_(v)
            walk_(j)
            return dict(code=r.status_code, found=found)
        load(BASE_SO)
        out["B_present"] = renames_cond()
        c = C()
        root = SA._s446_root(c)
        c.execute("DELETE FROM stock_stage_event WHERE count_id=? AND stage='A' AND event='verified'", (root,))   # the walk's own copy
        c.commit()
        c.close()
        clear_caches()
        out["B_absent"] = renames_cond()
        out["hub"] = GET("/finance/stock/api/pad/hub/%d" % root, "manoj")[0]
        out["statement"] = GET("/finance/stock/api/statement/%d" % root, "manoj")[0]
        out["sm_page"] = GET("/finance/stockmatch", "manoj")[0]
        return out
    block("b8", b8)

    # ---------------------------------------------------------------------------------------------------- 9. the spellings' control (OLD)
    def b9():
        if NEW:
            return {}
        load()
        c = C()
        r = c.execute("SELECT md5, stamp FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' ORDER BY stamp DESC LIMIT 1").fetchone()
        p = os.path.join(os.environ["W533_READINGS"], r[0] + ".json")
        j = json.load(open(p, encoding="utf-8"))
        names = [i.get("name") for i in ((j.get("data") or {}).get("items") or []) if i.get("name")]
        res = IA.sight_closing(c, names, (j.get("data") or {}).get("as_on"), r[0], r[1], source="W533 control")
        st = {x["old_name"]: x["state"] for x in IA.rows(c)}
        c.rollback()
        c.close()
        return dict(verified=res.get("verified"), states={k: st.get(k) for k in ("L S BELT CONT GRAY UNISON XXX", "TYNOR WRIST SPLINT LF M ELAS")})
    block("b9", b9)

    # ---------------------------------------------------------------------------------------------------- 10/11. idle reads, not broken
    def snapshot():
        c = sqlite3.connect(DB)
        out = {}
        for t in ("amir_step_log", "amir_bill_answer", "amir_self_wait", "amir_job", "purchase_audit", "setting", "amir_day", "amir_claim", "amir_step",
                  "amir_bill_disposition", "stock_stage_event"):
            if c.execute("SELECT 1 FROM sqlite_master WHERE name=?", (t,)).fetchone():
                rows = c.execute("SELECT * FROM %s" % t).fetchall()
                out[t] = hashlib.md5(repr(sorted(map(repr, rows))).encode()).hexdigest()[:12] + ":%d" % len(rows)
        c.close()
        return out

    def b10():
        load()
        c = C()
        setup_busy(c)
        c.close()
        GET("/finance/amir/step/1", "amir")
        s1 = snapshot()
        GET("/finance/amir/step/1", "amir")
        s2 = snapshot()
        return dict(first=s1, second=s2, same=(s1 == s2), moved=[k for k in s1 if s1[k] != s2.get(k)])
    block("b10", b10)

    def b11():
        out = {}
        load()
        r = fc.get("/finance/sanjeevni/api/needs-you", base_url=BASE_URL, headers=ck["manoj"])
        j = r.get_json(silent=True) or {}
        out["needs_you"] = dict(code=r.status_code, n=len(j.get("lines") or []),
                                bad=[l for l in (j.get("lines") or []) if not (isinstance(l, dict) and "cls" in l and "target" in l and "text" in l)][:3])
        r = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["manoj"])
        j = r.get_json(silent=True) or {}
        out["visit"] = dict(code=r.status_code, keys=sorted(j.keys()), states=sorted({s.get("state") for s in j.get("steps") or []}),
                            salt_keys=sorted((j.get("salt_list") or {}).keys()), bills_keys=sorted((j.get("bills") or {}).keys()))
        out["visit_amir"] = fc.get("/finance/amir/day/api/visit-summary", base_url=BASE_URL, headers=ck["amir"]).status_code
        for d in ("2026-10-08", "2026-09-22", "2026-09-17", "2026-01-05"):
            code, h, _m, _l = GET("/finance/amir/day?d=%s" % d, "manoj")
            m = re.search(r"id=daystate>(.*?)</p>", h, flags=re.S)
            r = fc.get("/finance/amir/day/api/visit-summary?date=%s" % d, base_url=BASE_URL, headers=ck["manoj"])
            jj = r.get_json(silent=True) or {}
            out["day_" + d] = dict(code=code, head=_html.unescape(m.group(1)) if m else vis(h)[:200], state=jj.get("state"), closed_at=jj.get("closed_at"),
                                   reopened_at=jj.get("reopened_at"))
        out["salts"] = GET("/finance/amir/salts", "amir")[0]
        prev = (now.replace(day=1) - dt.timedelta(days=1)).strftime("%Y-%m")
        out["pack_seen"] = POST("/finance/amir/pack/%s/seen" % prev, "amir", {"go": "1"})
        out["healthz"] = (fc.get("/finance/amir/api/healthz", base_url=BASE_URL, headers=ck["manoj"]).get_json(silent=True) or {}).get("kit")
        # the jobs card (the same jobs on both sides)
        c = C()
        ins(c, "amir_job", dict(key="w533:cat", kind="category", subject="W533 CAT ITEM", created_at=ts(now), created_by="W533", show_from=ts(now)))
        ins(c, "amir_job", dict(key="w533:vbill", kind="vendor_bill", subject=SUP_A, created_at=ts(now), created_by="W533", show_from=ts(now)))
        ins(c, "amir_job", dict(key="w533:tap", kind="tap", subject="W533 TAP", text_hi="W533 ka kaam Marg mein kijiye.", sub_hi="W533",
                                created_at=ts(now), created_by="W533", show_from=ts(now)))
        c.commit()
        jobs = AD._s494_read(c)["jobs"] if NEW else AD._s494_jobs(c)
        out["jobs_html"] = "".join(AD._s494_lines(jobs))
        c.close()
        # the board and the hub, the same copy both sides (the renames as the box has them -- NEW: schema-only base)
        load(BASE_SO)
        c = C()
        root = SA._s446_root(c)
        c.close()
        out["board_amir"] = fc.get("/finance/stock/api/pad/amir/%d" % root, base_url=BASE_URL, headers=ck["amir"]).get_json(silent=True)
        out["hub_owner"] = fc.get("/finance/stock/api/pad/hub/%d" % root, base_url=BASE_URL, headers=ck["manoj"]).get_json(silent=True)
        out["hub_page"] = GET("/finance/stock/page/hub?count=%d" % root, "manoj")[0]
        out["statement_page"] = GET("/finance/stock/page/statement?count=%d" % root, "manoj")[0]
        return out
    block("b11", b11)

    # ---------------------------------------------------------------------------------------------------- 12/13. words, weight
    def b12():
        out = {}
        for mode in ("paper", "both"):
            load()
            c = C()
            setup_busy(c)
            c.execute("INSERT INTO setting (key, value) VALUES ('purchase.entry_mode', ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (mode,))
            c.commit()
            c.close()
            pages = {}
            for n in range(1, 8):
                calls.clear()
                code, h, ms, _l = GET("/finance/amir/step/%d" % n, "amir")
                bad, used, kh = sweep(h)
                pages[n] = dict(code=code, bytes=len(h.encode("utf-8")), ms=ms, bad=bad, used=used, khol=kh, calls=dict(calls))
            out[mode] = pages
        load()
        c = C()
        setup_busy(c)
        t0 = time.perf_counter()
        AD.needs_you_lines(c)
        out["needs_ms"] = int((time.perf_counter() - t0) * 1000)
        c.close()
        return out
    block("b12", b12)

    print(TAG + json.dumps(R, default=str))


# ============================================================================================================== the walk
def run_probe(a, side, Wd, store, secret, pw, base, base_so, dmap):
    fin = os.path.join(a.run, side, "finance")
    ing = os.path.join(a.run, side, "marg_ingest")
    wd = os.path.join(Wd, "probe_%s" % side)
    for sub in ("noring", "nomarg"):
        os.makedirs(os.path.join(wd, sub))
    dbp, adbp, spp = [os.path.join(wd, "w533_%s.db" % x) for x in ("app", "assets", "spine")]
    copydb(base, dbp)
    copydb(a.adb, adbp)
    copydb(a.spine, spp)
    env = dict(os.environ, SIDE=side, FINDIR=fin, INGDIR=ing, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp,
               W533_BASE=base, W533_BASE_SO=base_so, W533_ADB0=a.adb, W533_READINGS=a.readings, DUTY_MAP_JSON=dmap,
               FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, CLINIC_PORTAL_DIR=a.por, CLINIC_USERS_FILE=store,
               TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W533J=json.dumps(dict(pw=pw)),
               MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"),
               ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"),
               ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
               CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
    for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE",
              "FINANCE_CRON_TOKEN", "AMIR_BILLS_FROM"):
        env.pop(k, None)
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=3000)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    print("   the %s probe ran %d s (exit %s)" % (side, int(time.time() - t0), p.returncode))
    if not js:
        print("-- the %s probe did not finish; its last lines:" % side)
        for l in p.stdout.splitlines()[-40:]:
            print("   " + mask(l)[:300])
        return None
    return json.loads(js[-1][len(TAG):])


def data_step(a, db, *extra):
    p = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "data_s533.py"), "--db", db, "--modules", a.built, "--finance",
                        os.path.join(a.run, "new", "finance"), "--archive", extra[0] if extra else a.archive,
                        "--readings", extra[1] if len(extra) > 1 else a.readings] + list(extra[2:]),
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=900,
                       cwd=os.path.join(a.run, "new", "finance"))
    return p.returncode, p.stdout


def norm_json(x):
    """Drop what moves between two reads of the same copy (stamps, timings) before old and new are compared."""
    if isinstance(x, dict):
        return {k: norm_json(v) for k, v in x.items() if not re.search(r"(^|_)(at|ms|now|generated|stamp|time|took|age)($|_)", k)}
    if isinstance(x, list):
        return [norm_json(v) for v in x]
    return x


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe":
        return probe()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--run", "--por", "--db", "--adb", "--spine", "--built", "--map-new", "--map-old", "--archive", "--readings"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W533 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    # ------------------------------------------------------------------------------------------------------------ 10. the greps
    print("-- 10 the greps (word-bounded) over the NEW finance folder and the portal copy; the same over the OLD folder (control)")

    def grep(folder, names):
        hits = []
        for fn in sorted(os.listdir(folder)):
            if not fn.endswith((".py", ".html")) or ".bak_" in fn:
                continue
            t = io.open(os.path.join(folder, fn), encoding="utf-8", errors="replace").read()
            for ln_no, line in enumerate(t.splitlines(), 1):
                if line.strip() in KIT_LINES or line.rstrip() in KIT_LINES or any(k in line for k in KIT_LINES):
                    continue
                for nm in names:
                    if re.search(r"(?<![A-Za-z0-9_])" + re.escape(nm) + r"(?![A-Za-z0-9_])", line):
                        hits.append((fn, ln_no, nm))
        return hits
    fin_new, fin_old = os.path.join(a.run, "new", "finance"), os.path.join(a.run, "old", "finance")
    hn = grep(fin_new, RETIRED) + grep(a.por, RETIRED)
    check("every retired name (%d) is gone from the NEW finance folder and the portal, the kit's own three comment lines aside" % len(RETIRED), not hn, hn[:12])
    ho = grep(fin_old, RETIRED)
    red("the OLD finance folder still carries them (%d hits, e.g. %s)" % (len(ho), ho[:3]), len(ho) > 10)
    ht = grep(fin_new, OLD_TABLES) + grep(a.por, OLD_TABLES)
    check("amir_step / amir_bill_disposition are read by no .py of the NEW folder (only the kit's data step names them)", not ht, ht[:6])
    t_ad = io.open(os.path.join(fin_new, "amir_day.py"), encoding="utf-8").read()
    t_ado = io.open(os.path.join(fin_old, "amir_day.py"), encoding="utf-8").read()
    check("the new amir_day carries no DELETE, no S494_JOBS, no rupee figure, no stock_stage_event write, no '/finance/purchase/page/salts'",
          "DELETE" not in t_ad and "S494_JOBS" not in t_ad and not re.search(r"₹\s*\d", t_ad) and "stock_stage_event" not in t_ad
          and "/finance/purchase/page/salts" not in t_ad, [w for w in ("DELETE", "S494_JOBS", "stock_stage_event", "/finance/purchase/page/salts") if w in t_ad])
    red("the OLD amir_day DELETEs (the reopen), carries the rupee seed and the second salts door", "DELETE FROM amir_step" in t_ado and re.search(r"₹\s*\d", t_ado)
        and "/finance/purchase/page/salts" in t_ado)
    sp_new = os.path.join(fin_new, "spine")
    p = subprocess.run([sys.executable, "-B", os.path.join(sp_new, "selftest_spine.py")], cwd=sp_new, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=900)
    check("selftest_spine.py is green on the scratch spine folder", p.returncode == 0 and "SELFTEST OK" in p.stdout, p.stdout.strip().splitlines()[-1:])

    # ------------------------------------------------------------------------------------------------------------ the bases, the data step
    print("-- 8 the data step on scratch copies (its lines below); 9 the two spellings")
    base_old = os.path.join(Wd, "base_old.db")
    base_new = os.path.join(Wd, "base_new.db")
    base_so = os.path.join(Wd, "base_new_schema.db")
    copydb(a.db, base_old)
    copydb(a.db, base_new)
    copydb(a.db, base_so)
    rc, out = data_step(a, base_new)
    for l in out.splitlines():
        print("   " + mask(l)[:330])
    check("the data step ran clean on a copy (exit 0, committed)", rc == 0 and "DATA_S533: committed" in out, rc)
    D = {}
    for l in out.splitlines():
        m = re.match(r"DATA_S533: (\d) ", l)
        if m:
            D.setdefault(m.group(1), []).append(l)
    check("8.3: the step history copied as close / reopen rows (a reopen row for the day reopened and never closed again)",
          any("reopen row" in l for l in D.get("3", [])), D.get("3"))
    check("8.4: the bill answers copied with their bill_id", any("amir_bill_answer:" in l for l in D.get("4", [])), D.get("4"))
    rc2, out2 = data_step(a, base_so, a.archive, a.readings, "--schema-only")
    check("the data step's schema part ran on another copy (exit 0)", rc2 == 0 and "DATA_S533: committed" in out2, out2.splitlines()[-3:])
    sp = [l for l in out.splitlines() if l.startswith("DATA_S533: 6 ")]
    check("9: both spellings respelt and verified by the closing on the box (respelt events, the after-lines verified)",
          sum(1 for l in sp if "respelt event" in l) == 2 and sum(1 for l in sp if "after   verified" in l) == 2, sp)
    c = sqlite3.connect(base_new)
    alias = []
    for new in ("L S BELT XXXL CONT GRAY UNISO", "TYNOR WRIST SPL LF M ELAS T"):
        key = re.sub(r"[^A-Z0-9]+", " ", new.upper()).strip()
        alias.append((new, c.execute("SELECT COUNT(*) FROM marg_item_name WHERE name=? AND kind='alias' AND active=1", (key,)).fetchone()[0]))
    ev = c.execute("SELECT COUNT(*) FROM marg_item_rename_event WHERE event='respelt' AND by_user='S533'").fetchone()[0]
    c.close()
    check("9: _follow's spine alias rows carry the new spellings (%s); two 'respelt' events" % alias, all(n >= 1 for _s, n in alias) and ev == 2, (alias, ev))
    again = os.path.join(Wd, "again.db")
    copydb(base_new, again)
    rc3, out3 = data_step(a, again)
    check("9 / 8: a second run writes nothing new (no respelt, no copy, the rows 'already verified')",
          rc3 == 0 and "respelt event" not in out3 and "0 step row(s) copied + 0 reopen" in out3 and " 0 copied," in out3 and out3.count("already verified") == 2,
          [l for l in out3.splitlines() if re.match(r"DATA_S533: [346] ", l)][:8])
    fake_r, fake_a = os.path.join(Wd, "fake_readings"), os.path.join(Wd, "fake_archive")
    os.makedirs(fake_r)
    os.makedirs(fake_a)
    c = sqlite3.connect("file:%s?mode=ro" % a.db, uri=True)
    md5c = c.execute("SELECT md5 FROM mi_file WHERE type='STOCK_CLOSING' AND verdict='VERIFIED' ORDER BY stamp DESC LIMIT 1").fetchone()[0]
    c.close()
    j = json.load(open(os.path.join(a.readings, md5c + ".json"), encoding="utf-8"))
    j["data"]["items"] = [i for i in j["data"]["items"] if not str(i.get("name") or "").startswith(("L S BELT XXXL", "TYNOR WRIST SPL LF M ELAS"))]
    json.dump(j, open(os.path.join(fake_r, md5c + ".json"), "w", encoding="utf-8"))
    lacks = os.path.join(Wd, "lacks.db")
    copydb(a.db, lacks)
    rc4, out4 = data_step(a, lacks, fake_a, fake_r)
    check("9: a closing that lacks the spellings -> each row skipped with its line, nothing respelt", rc4 == 0 and out4.count("does not print") == 2
          and "respelt event" not in out4, [l for l in out4.splitlines() if l.startswith("DATA_S533: 6")][:6])

    # ------------------------------------------------------------------------------------------------------------ the probes
    print("-- the probes: NEW (the built files on the data-step copy) and OLD (the box as it is), each a fresh process")
    PN = run_probe(a, "new", Wd, store, secret, pw, base_new, base_so, a.map_new)
    PO = run_probe(a, "old", Wd, store, secret, pw, base_old, base_old, a.map_old)
    if not check("both probes ran to the end", PN is not None and PO is not None):
        return finish()
    errs = {k: v.get("error") for P in (PN, PO) for k, v in P.items() if isinstance(v, dict) and v.get("error")}
    for k, v in errs.items():
        print("   probe block %s raised: %s" % (k, mask(v)))
    for P in (PN, PO):
        for k, v in P.items():
            if isinstance(v, dict) and v.get("tb"):
                print("   %s %s traceback: %s" % (P["side"], k, mask(v["tb"])[-900:]))
    check("no probe block raised", not errs, list(errs))

    # 0
    b0 = PN.get("b0") or {}
    print("   0 live state on the copy: root %s stage %s A %s B %s; events %s" % (b0.get("root"), b0.get("stage"), b0.get("A"), b0.get("B"), b0.get("events")))
    print("     the two rename rows (data-step copy): %s; Yuvika in scans_for_amir: %s; scans listed %s held %s" % (b0.get("renames"), b0.get("yuvika"), b0.get("scans_listed"), b0.get("scans_held")))
    print("     history rows: %s; bills %s; card %s" % (b0.get("old_rows"), b0.get("bills_counts"), b0.get("card")))
    roles = b0.get("roles") or []
    check("0: amir's medical role is not checker; the owner's is checker (the door checks mean something)",
          any(r[1] == "amir" and r[2] != "checker" for r in roles) and any(r[1] == "manoj" and r[2] == "checker" for r in roles), roles)
    check("0: a stage root exists (stage %s)" % b0.get("stage"), b0.get("stage") in ("A", "B", "C", "done"), b0.get("stage"))

    # 7 the map
    dm = json.load(open(a.map_new, encoding="utf-8"))
    by = {d["id"]: d for d in dm["duties"]}
    dsql = b0.get("duty_sql") or {}
    check("7: the map is v11 and its three due_sql strings == amir_day.DUTY_SQL, byte for byte",
          dm.get("version") == 11 and all(by[k]["due_sql"] == dsql.get(k) for k in ("amir.bills_answer", "amir.own_correction", "amir.salt_list")),
          {k: by[k]["due_sql"] == dsql.get(k) for k in ("amir.bills_answer", "amir.own_correction", "amir.salt_list")})
    check("7: aaj_seed's REWRITE piece occurs exactly once in DUTY_SQL['amir.bills_answer']", str(dsql.get("amir.bills_answer", "")).count(b0.get("rewrite_piece") or "@@") == 1,
          b0.get("rewrite_piece"))
    check("7: amir.marg_jobs' due_sql reads amir_day's S494_OPEN (one rule, the reopen)", (b0.get("s494_open") or "@@") in by["amir.marg_jobs"]["due_sql"], by["amir.marg_jobs"]["due_sql"])
    print("   7 the duty SQLs on the schema-only copy: %s; on the full data-step copy: %s" % (b0.get("duty_rows_schema_only"), b0.get("duty_rows_full")))
    check("7: each of the three runs on the copy after the schema step and returns one row (n, since)",
          all(isinstance(v, list) and len(v) == 2 for v in (b0.get("duty_rows_schema_only") or {}).values()) and len(b0.get("duty_rows_schema_only") or {}) == 3,
          b0.get("duty_rows_schema_only"))
    b7 = PN.get("b7") or {}
    print("   7 staff eye: %s" % mask(b7.get("duties")))
    print("   7 aaj list as amir: %s; aaj items %s" % (b7.get("aaj"), b7.get("aaj_items")))
    print("   7 owner console (v%s): %s" % (b7.get("console_version"), b7.get("console")))
    due = [d for d in b7.get("duties") or [] if isinstance(d.get("due"), int) and d["due"] > 0 and d.get("door") and d.get("marker")]
    check("7 staff-eye: every amir duty due on the busy copy shows its door_marker on its door page as amir (%s)" % ", ".join("%s %s" % (d["id"], d["due"]) for d in due),
          due and all(d.get("seen") for d in due) and not any(isinstance(d.get("due"), str) for d in b7.get("duties") or [])
          and {"amir.bills_answer", "amir.own_correction", "amir.salt_list", "amir.marg_jobs"} <= {d["id"] for d in due}, [d for d in b7.get("duties") or [] if not d.get("seen")])
    con_ = b7.get("console") or {}
    check("7: amir.arrival_bill_entry is neither due nor unread on the owner's console; bills_answer reads clean",
          (con_.get("amir.arrival_bill_entry") or {}).get("n") == 0 and not (con_.get("amir.arrival_bill_entry") or {}).get("err")
          and not (con_.get("amir.bills_answer") or {}).get("err") and (con_.get("amir.bills_answer") or {}).get("n", 0) >= 3, con_)
    ai = b7.get("aaj_items") or {}
    check("7: Aaj ka kaam reads amir's three map lines on the staff floor -- bills_answer, own_correction and salt_list due and read clean; arrival_bill_entry not due, not unread",
          all((ai.get(k) or {}).get("n", 0) >= 1 and not (ai.get(k) or {}).get("err") for k in ("amir.bills_answer", "amir.own_correction", "amir.salt_list"))
          and (ai.get("amir.arrival_bill_entry") or {}).get("n") == 0 and not (ai.get("amir.arrival_bill_entry") or {}).get("err"), ai)
    aj = b7.get("aaj") or {}
    check("7: his Aaj ka kaam list (the route, as amir) answers 200 and carries no arrival line (%s)" % aj, aj.get("code") == 200 and not aj.get("arrival_line"), aj)

    # 1 one read, one word
    for st in PN.get("b1") or []:
        nm = st.get("name")
        print("   1 %-8s gate %s | extra %s | head %r | second %r" % (nm, st.get("gate"), st.get("extra"), st.get("head"), st.get("second")))
        print("     owner page head %r; visit left %s; step-7 calls %s; step-1 calls %s (%d / %d ms)" % ((st.get("owner") or {}).get("head"), (st.get("visit") or {}).get("left"),
                                                                                                  (st.get("s7") or {}).get("calls"), (st.get("s1") or {}).get("calls"),
                                                                                                  (st.get("s7") or {}).get("ms", 0), (st.get("s1") or {}).get("ms", 0)))
        t7 = (st.get("s7") or {}).get("text") or ""
        en_all = [g[1] for g in st.get("gate") or []] + [x[1] for x in st.get("extra") or []]
        check("1 %s: Amir's step 7 prints every hi of the gate and the extras; the owner's day prints the same en (state line %r)" % (nm, st.get("head")),
              all(g[0] in t7 for g in st.get("gate") or []) and all(x[0] in t7 for x in st.get("extra") or []) and (st.get("owner") or {}).get("head") == st.get("head")
              and ((st.get("owner") or {}).get("second") or "") == (st.get("second") or ""), [g[0] for g in st.get("gate") or [] if g[0] not in t7])
        v = st.get("visit") or {}
        s7n = ((v.get("s7") or [{}])[0] or {}).get("note") or ""
        check("1 %s: the visit summary's left[] == the same en strings, and steps[7].note carries them" % nm,
              v.get("left") == en_all and all(e in s7n for e in en_all), (v.get("left"), s7n))
        if st.get("stage_en"):
            check("1 %s: Needs-you carries the owner's one stage sentence 'Count #%s: %s'" % (nm, st.get("root"), st.get("stage_en")),
                  ("Count #%s: %s" % (st.get("root"), st.get("stage_en"))) in (st.get("needs") or []), [x for x in st.get("needs") or [] if x.startswith("Count")])
        check("1 %s: his card (step 1) prints every stage line" % nm, all(h in (st.get("s1") or {}).get("text", "") for h in st.get("card_hi") or []), st.get("card_hi"))
        for which in ("s7", "s1"):
            cl = (st.get(which) or {}).get("calls") or {}
            mine = cl.get("_assets_con", 0) - cl.get("_assets_con_in_scans", 0)
            check("1 %s %s: amir_stage %s, _s521_stage_words %s, scans_for_amir %s -- once each; assets.db opened by the page itself %s (the paper pass; scans_for_amir's own %s are its)"
                  % (nm, which, cl.get("amir_stage"), cl.get("_s521_stage_words"), cl.get("scans_for_amir"), mine, cl.get("_assets_con_in_scans", 0)),
                  cl.get("amir_stage") == 1 and cl.get("_s521_stage_words", 0) <= 1 and cl.get("scans_for_amir") == 1 and mine <= 1, cl)
    c1n, c1o = PN.get("b1c") or {}, PO.get("b1c") or {}
    print("   1 with a category job not yet shown: NEW step 1 %s, Needs-you %s; OLD step 1 %s, Needs-you %s" % (c1n.get("step1"), c1n.get("needs"), c1o.get("step1"), c1o.get("needs")))
    check("1: amir_stage once per request also where the old file read it again (a category job not yet shown): step 1 %s, Needs-you %s"
          % ((c1n.get("step1") or {}).get("amir_stage"), (c1n.get("needs") or {}).get("amir_stage")),
          (c1n.get("step1") or {}).get("amir_stage") == 1 and (c1n.get("needs") or {}).get("amir_stage") == 1
          and (c1n.get("needs") or {}).get("_s521_stage_words") == 1, c1n)
    red("1 OLD: in that state the old file asked amir_stage %s times on a step and %s times on Needs-you" % ((c1o.get("step1") or {}).get("amir_stage"), (c1o.get("needs") or {}).get("amir_stage")),
        ((c1o.get("step1") or {}).get("amir_stage") or 0) > 1 or ((c1o.get("needs") or {}).get("amir_stage") or 0) > 1, c1o)

    # 2 append-only
    b2, o2 = PN.get("b2") or {}, PO.get("b2") or {}
    print("   2 NEW punch %s; summary %s; answers %s; claims %s; audit %s" % (b2.get("punch"), b2.get("punch_summary"), b2.get("answers"), b2.get("claims"), b2.get("audit")))
    print("   2 NEW step 7 rows %s; amir_day %s; posts %s; json %s" % (b2.get("step7"), b2.get("closed_at"), b2.get("posts7"), b2.get("closed_json")))
    pu = b2.get("punch") or []
    check("2: step 1 tapped twice (punched, then no punch) -> two rows, the second replaces the first, the first kept; the summary says 'no punch'",
          len(pu) == 2 and pu[0][1] == "punched" and pu[1][1] == "no_punch" and pu[1][2] == pu[0][0]
          and ((b2.get("punch_summary") or [{}])[0].get("note") or "").startswith("no punch"), (pu, b2.get("punch_summary")))
    red("2 OLD: the second step-1 tick overwrote the first (%d row)" % len(o2.get("punch") or []), len(o2.get("punch") or []) == 1, o2.get("punch"))
    an = b2.get("answers") or []
    check("2: a bill answered twice -> two rows (short, ok), the second replaces the first; the claim raised then settled 'amir_ok'; audited",
          len(an) == 2 and an[0][1] == "short" and an[1][1] == "ok" and an[1][3] == an[0][0] and b2.get("claims") == [["settled", "amir_ok"]]
          and b2.get("audit", []).count("amir_bill_answer") == 2 and "amir_claim_raised" in b2.get("audit", []) and "amir_claim_settled" in b2.get("audit", []),
          (an, b2.get("claims"), b2.get("audit")))
    red("2 OLD: the second answer overwrote the first (%d row)" % len(o2.get("answers") or []), len(o2.get("answers") or []) == 1, o2.get("answers"))
    s7 = b2.get("step7") or []
    check("2: close, reopen, close -> three step-7 rows chained by replaces; the fourth tap (close while closed) writes nothing; amir_day.closed_at never written",
          [r[1] for r in s7] == ["close", "reopen", "close"] and s7[1][2] == s7[0][0] and s7[2][2] == s7[1][0]
          and (b2.get("closed_at") or [None])[0] is None and (b2.get("closed_json") or {}).get("state") == "CLOSED"
          and re.match(r"^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d$", str((b2.get("closed_json") or {}).get("closed_at"))), (s7, b2.get("closed_at"), b2.get("closed_json")))
    red("2 OLD: the reopen DELETEs the day's step-7 row (%s -> %s)" % tuple((o2.get("old_reopen_rows") or [None, None])[:2]), o2.get("old_reopen_rows") == [1, 0], o2.get("old_reopen_rows"))
    sc = PN.get("b2s") or {}
    for k in ("i", "ib", "ib_same", "ii", "ii_live", "iii"):
        print("   2 self-clear %-7s %s" % (k, mask(sc.get(k))))

    def sys_row(x):
        return [r for r in x.get("rows") or [] if r[2] == "system"]
    x = sc.get("i") or {}
    check("2 (i): a later live export carrying the paper's amount -> cleared marg_matches; a system 'ok' row replaces his 'self' row, his row untouched; audited; a second read settles nothing",
          x.get("wait") == ["marg_matches"] and len(sys_row(x)) == 1 and sys_row(x)[0][4] == x.get("self_row") and sys_row(x)[0][1] == "ok"
          and any(r[0] == x.get("self_row") and r[1] == "self" and r[2] == "amir" for r in x.get("rows") or []) and x.get("audit") == 1 and x.get("again") == 0 and x.get("notes") == 1, x)
    x = sc.get("ib") or {}
    check("2 (i-b): no scan, a later export with a changed amount -> marg_changed, a system row", x.get("wait") == ["marg_changed"] and len(sys_row(x)) == 1, x)
    x = sc.get("ib_same") or {}
    check("2 (i-b) bound: the same export he flagged is not later -> not cleared", x.get("wait") == [None] and not sys_row(x), x)
    x = sc.get("ii") or {}
    check("2 (ii): the bill's own export superseded -> cleared left_export, a system row", x.get("wait") == ["left_export"] and len(sys_row(x)) == 1, x)
    x = sc.get("ii_live") or {}
    check("2 (ii) R1-1 control of the rule itself: a bill in the live September export, an October export present -> NOT cleared (live Sept export found: %s)" % x.get("live_sept"),
          x.get("wait") == [None] and not sys_row(x), x)
    x = sc.get("iii") or {}
    check("2 (iii): he answered again ('ok') -> cleared 'answered ok', no system row", x.get("wait") == ["answered ok"] and not sys_row(x), x)
    xo = ((PO.get("b2s") or {}).get("i") or {}).get("old_row")
    red("2 OLD (i): the old self-clear rewrote his own row (%s -> %s)" % tuple(xo or [None, None]), bool(xo) and xo[0] != xo[1] and xo[0][1] == "amir", xo)

    # 3 the bills
    b3, o3 = PN.get("b3") or {}, PO.get("b3") or {}
    ids = b3.get("ids") or {}
    print("   3 NEW lists %s; move %s; paper %s" % (b3.get("lists"), b3.get("move"), b3.get("paper_w1")))
    print("   3 NEW step5 %s; step7 %s; owner %s" % (b3.get("s5"), b3.get("s7"), b3.get("owner")))
    L3 = b3.get("lists") or {}
    check("3: the four states by key: today {W1, W2}, carry {W3 (first sight yesterday)}, flagged {W4}, waiting {W5}",
          L3.get("today") == sorted([ids.get("W1"), ids.get("W2")]) and L3.get("carry") == [ids.get("W3")] and L3.get("flagged") == [ids.get("W4")]
          and L3.get("waiting") == [ids.get("W5")], L3)
    mv = b3.get("move") or {}
    check("3: a later push that carries a bill moves its bw_md5 and keeps its first sight; a new bill's first sight is its export's day",
          mv.get("moved") and mv.get("before") == mv.get("after") and mv.get("new_first") == mv.get("new_expect"), mv)
    s5 = b3.get("s5") or {}
    check("3: the three counts named apart and equal on step 5, step 7 and the owner's page (2 · 1 · 1); the waiting bill under its own head",
          s5.get("counts") == [["2", "1", "1"]] and (b3.get("s7") or {}).get("counts") == [["2", "1", "1"]]
          and (b3.get("owner") or {}).get("counts") == [["2"], ["1"], ["1"], ["1"]] and s5.get("waiting_head"), (s5.get("counts"), b3.get("s7"), b3.get("owner")))
    check("3: no raw ISO date in step 5's visible text; the paper line names the export's stamp and the scan's day (%s)" % s5.get("paper"),
          not s5.get("iso") and s5.get("paper") and s5.get("marker") and s5.get("self_marker"), (s5.get("iso"), s5.get("paper")))
    ol = o3.get("old_lists") or {}
    red("3 OLD R2-25: the bill first seen yesterday and carried by today's export reads as TODAY in the old list", "W533-3" in (ol.get("today_bills") or []), ol)

    # 4 the gate
    b4, o4 = PN.get("b4") or {}, PO.get("b4") or {}
    print("   4 NEW %s" % b4)
    print("   4 OLD %s" % o4)
    check("4: nothing on the card -> step 6 done without a tap, step 7 ready while the salt list is owed; the owner reads 'OPEN — ready to close' / 'not holding: SALT WISE ITEM LIST not received'",
          b4.get("done6") is True and b4.get("ready") is True and b4.get("s6_nothing") and b4.get("s7_ready") and b4.get("owner_head") == "OPEN — ready to close"
          and "SALT WISE ITEM LIST not received" in str(b4.get("owner_second")), b4)
    red("4 OLD: the old owner's line lists the salt / name tick as missing (%s)" % o4.get("old_left"), "salt and name list not ticked" in (o4.get("old_left") or []) and o4.get("old_ready") is False, o4)

    # 5 D712
    b5, o5 = PN.get("b5") or {}, PO.get("b5") or {}
    print("   5 NEW %s" % mask({k: v for k, v in b5.items() if k != "s2_both_sweep"}))
    print("   5 OLD maal %s" % o5.get("maal"))
    check("5: an arrival tapped 5 days ago with no scan -> no 'Maal aa gaya' on his card, ONE owner line naming the vendor; a held scan of that vendor (read_vendor) -> no line",
          b5.get("maal") is False and len(b5.get("needs") or []) == 1 and "no bill scanned" in (b5.get("needs") or [""])[0] and b5.get("held") == [VENDOR]
          and not b5.get("needs_held"), b5)
    check("5: a listed scan of that supplier from on/after the arrival day less the grace -> no line; one from before it -> the line",
          b5.get("listed_near") == [] and len(b5.get("listed_far") or []) == 1, (b5.get("listed_near"), b5.get("listed_far")))
    cn = (b5.get("card_n") or [0])[0] if b5.get("card_n") else 0
    cnb = (b5.get("card_n_both") or [0])[0] if b5.get("card_n_both") else 0
    check("5: N on the card == N on step 2's heading, both modes, the card id 'scans' (paper %s/%s, both %s/%s)" % (cn, b5.get("s2_paper_n"), cnb, b5.get("s2_both_n")),
          b5.get("s2_paper_n") == [cn] and (b5.get("s2_both_n") or [0]) == [cnb] and b5.get("s2_paper_id") and (b5.get("s2_both_id") or cnb == 0), b5)
    red("5 OLD: the old card says 'Maal aa gaya, Marg mein bill baaki' for the reception tap", o5.get("maal") is True, o5.get("maal"))

    # 6 salt
    b6, o6 = PN.get("b6") or {}, PO.get("b6") or {}
    print("   6 NEW one rule %s; ids %s; nikaalo %s; door %s/%s; hub %s" % (b6.get("one_rule"), b6.get("ids"), b6.get("nikaalo"), b6.get("door_with_rows"), b6.get("door_without_rows"), b6.get("hub_salt")))
    print("   6 OLD rule A %s rule B %s; nikaalo %s" % (o6.get("old_rule_a"), o6.get("old_rule_b"), o6.get("nikaalo")))
    check("6: one rule -- a VERIFIED list received after the tick (Marg's stamp older) -> not owed", (b6.get("one_rule") or {}).get("pending") is False, b6.get("one_rule"))
    red("6 OLD: rule A still calls it owed (by the Marg stamp) while rule B does not", o6.get("old_rule_a") is True and o6.get("old_rule_b") is False, (o6.get("old_rule_a"), o6.get("old_rule_b")))
    ids6 = b6.get("ids") or {}
    check("6: the salt card once on step 6, once on step 7 (not ready), once on the owner's day, and on amir_salts' page (its hand-built w)",
          ids6 == dict(s6=1, s7=1, owner=1, salts_page=1) and b6.get("salts_page") == 200, ids6)
    check("6: the visit days -- two visits after the tick -> '2 visit'; none -> 'aaj ke tick ke baad'",
          "aapki 2 visit se nahi aayi" in str(b6.get("card2")) and "aaj ke tick ke baad" in str(b6.get("card0")), (vis(b6.get("card0") or ""), vis(b6.get("card2") or "")))
    check("6: the hub reads salt_list.pending / fresh / owner_line / css", set(b6.get("hub_keys") or []) == {"pending", "fresh", "owner_line", "css"}, b6.get("hub_keys"))
    check("6: the step-6 salts door only while the sheet has rows", b6.get("door_with_rows") is True and b6.get("door_without_rows") is False, (b6.get("door_with_rows"), b6.get("door_without_rows")))
    red("6 OLD: step 6 says the salt sentence twice (%s)" % (o6.get("nikaalo") or {}).get("s6"), ((o6.get("nikaalo") or {}).get("s6") or 0) >= 2, o6.get("nikaalo"))

    # 8 stockmatch c4
    b8, o8 = PN.get("b8") or {}, PO.get("b8") or {}
    print("   8 NEW %s" % b8)
    print("   8 OLD %s" % o8)

    def cond(x):
        return [f for f in (x or {}).get("found") or [] if "en" in f]

    def wait(x):
        return [f for f in (x or {}).get("found") or [] if "wait" in f]
    bp, ba = cond(b8.get("B_present")), cond(b8.get("B_absent"))
    check("8: with the stage's B present (21 of 23 on the copy without the spellings) -> '2 of 23 renames not yet verified (…)'; renames_wait_stage_a False",
          bp and bp[0]["en"].startswith("2 of 23 renames not yet verified") and wait(b8.get("B_present")) and wait(b8.get("B_present"))[0]["wait"] is False, (bp, wait(b8.get("B_present"))))
    check("8: a root with no 'A verified' event -> 'renames wait for stage A — the orthotic vouchers' proof', renames_wait_stage_a True; the record's total still read; hub, statement, page 200",
          ba and ba[0]["en"] == "renames wait for stage A — the orthotic vouchers' proof" and wait(b8.get("B_absent")) and wait(b8.get("B_absent"))[0]["wait"] is True
          and wait(b8.get("B_absent"))[0].get("total") and b8.get("hub") == 200 and b8.get("statement") == 200 and b8.get("sm_page") == 200, (ba, wait(b8.get("B_absent"))))
    oa = cond(o8.get("B_absent"))
    red("8 OLD: the root with no 'A verified' event still says '%s'" % ((oa or [{}])[0].get("en")), bool(oa) and "of 23 renames not yet verified" in oa[0]["en"], oa)

    # 9 control
    o9 = PO.get("b9") or {}
    red("9 OLD: the closing on the box does not verify the two rows under their old new_name (%s)" % o9.get("states"),
        o9.get("states") and all(v != "verified" for v in (o9.get("states") or {}).values()), o9)

    # 10 idle second read
    b10 = PN.get("b10") or {}
    check("10: a second identical GET writes nothing (settle idle): %s" % (b10.get("moved") or "no table moved"), b10.get("same") is True, b10.get("moved"))

    # 11 not broken
    b11, o11 = PN.get("b11") or {}, PO.get("b11") or {}
    print("   11 NEW needs-you %s; visit %s; days %s" % (b11.get("needs_you"), b11.get("visit"), {k: v for k, v in b11.items() if k.startswith("day_")}))
    check("11: Needs-you (sanjeevni_approvals) renders, each line dict(cls, target, text[, duty])", (b11.get("needs_you") or {}).get("code") == 200 and not (b11.get("needs_you") or {}).get("bad"), b11.get("needs_you"))
    v, vo = b11.get("visit") or {}, o11.get("visit") or {}
    check("11: the visit summary as the checker: the same top keys as the OLD file (%d), the step literals kept; salt_list reduced to the four; refused to amir"
          % len(v.get("keys") or []), v.get("code") == 200 and v.get("keys") == vo.get("keys") and set(v.get("states") or []) <= {"done", "skipped", "not yet", "not done", "not needed", "partly", "open"}
          and v.get("salt_keys") == ["css", "fresh", "owner_line", "pending"] and b11.get("visit_amir") == 403, (v, vo.get("keys")))
    d8, d22, d17, d1 = (b11.get("day_2026-10-08") or {}), (b11.get("day_2026-09-22") or {}), (b11.get("day_2026-09-17") or {}), (b11.get("day_2026-01-05") or {})
    check("11: /finance/amir/day for 08-10 -> CLOSED (the copied close row); 22-09 -> reopened; a day with no rows -> 200 OPEN",
          str(d8.get("head")).startswith("CLOSED at 09:47") and d8.get("state") == "CLOSED" and "reopened" in str(d22.get("head")) and d22.get("state") == "OPEN"
          and d22.get("reopened_at") and d1.get("code") == 200 and str(d1.get("head")).startswith("OPEN"), (d8, d22, d1))
    print("   11 17-09 (reopened and closed again; its reopen stays in amir_day.reopened_at, R3-6): %s" % d17)
    check("11: amir_salts' page 200; packs' 'seen' POST -> 303 /finance/amir; healthz names %s" % b11.get("healthz"),
          b11.get("salts") == 200 and (b11.get("pack_seen") or [0])[0] == 303 and str((b11.get("pack_seen") or ["", ""])[1]).endswith("/finance/amir")
          and b11.get("healthz") == "S533_AMIR_DAY_PAGE", (b11.get("salts"), b11.get("pack_seen"), b11.get("healthz")))

    def strip_cat(h):
        return re.sub(r"<div class=line><span class=big>(Is|In \d+) item ki category Marg mein[^<]*</span><br><span class=sub>[^<]*</span>"
                      r"(<br><span class=sub>Marg mein is category ka naam[^<]*</span>)?", "<CAT>", h or "")
    jn, jo = b11.get("jobs_html") or "", o11.get("jobs_html") or ""
    print("   11 the jobs card's category heading: NEW %r / OLD %r" % (re.findall(r"item ki category Marg mein[^<]*", jn), re.findall(r"item ki category Marg mein[^<]*", jo)))
    check("11: the Marg jobs card HTML is byte-equal old vs new except the category heading", jn and strip_cat(jn) == strip_cat(jo), (strip_cat(jn)[:300], strip_cat(jo)[:300]))
    bn, bo = norm_json(b11.get("board_amir")), norm_json(o11.get("board_amir"))
    hn_, ho_ = norm_json(b11.get("hub_owner")), norm_json(o11.get("hub_owner"))
    added = []

    def drop_added(x):
        if isinstance(x, dict):
            if "renames_wait_stage_a" in x:
                added.append(x.get("renames_wait_stage_a"))
            return {k: drop_added(v) for k, v in x.items() if k != "renames_wait_stage_a"}
        if isinstance(x, list):
            return [drop_added(v) for v in x]
        return x
    hn2 = drop_added(hn_)

    def diff(a_, b_, path=""):
        if isinstance(a_, dict) and isinstance(b_, dict):
            return [d for k in sorted(set(a_) | set(b_)) for d in diff(a_.get(k), b_.get(k), path + "/" + str(k))]
        if isinstance(a_, list) and isinstance(b_, list) and len(a_) == len(b_):
            return [d for i, (x_, y_) in enumerate(zip(a_, b_)) for d in diff(x_, y_, "%s[%d]" % (path, i))]
        return [] if a_ == b_ else ["%s: %r -> %r" % (path, str(b_)[:80], str(a_)[:80])]
    print("   11 the hub's orthotic section carries the new key renames_wait_stage_a = %s (stockmatch 5.2)" % added)
    check("11: stock_app's light board JSON (as amir) and the hub JSON (as the owner) byte-equal old vs new on the same copy (stamps dropped; the one key 5.2 adds aside)",
          bn and bn == bo and hn2 and hn2 == ho_ and added == [False], diff(bn, bo)[:6] + diff(hn2, ho_)[:6])
    check("11: the hub page and the statement page 200", b11.get("hub_page") == 200 and b11.get("statement_page") == 200, (b11.get("hub_page"), b11.get("statement_page")))

    # 12, 13 words and weight
    b12, o12 = PN.get("b12") or {}, PO.get("b12") or {}
    for mode in ("paper", "both"):
        for n in range(1, 8):
            pg = ((b12.get(mode) or {}).get(str(n))) or {}
            og = ((o12.get(mode) or {}).get(str(n))) or {}
            print("   12/13 %s step %d: %s, %d bytes, %d ms (OLD %s bytes, %s ms); exemptions used %s; kholiye %s" % (mode, n, pg.get("code"), pg.get("bytes", 0), pg.get("ms", 0),
                                                                                                         og.get("bytes"), og.get("ms"), pg.get("used"), [k[1][-40:] for k in pg.get("khol") or []]))
            check("12 %s step %d: no forbidden word on the page (%s)" % (mode, n, pg.get("bad")), pg.get("code") == 200 and not pg.get("bad"), pg.get("bad"))
            check("12 %s step %d: every 'kholiye' is a door's verb" % (mode, n), all(ok for ok, _c in pg.get("khol") or []), [c for ok, c in pg.get("khol") or [] if not ok])
            check("13 %s step %d: under 100 KB (%d bytes)" % (mode, n, pg.get("bytes", 0)), 0 < pg.get("bytes", 10 ** 9) < 100 * 1024, pg.get("bytes"))
    obad = sum(len((((o12.get("paper") or {}).get(str(n))) or {}).get("bad") or []) for n in range(1, 8))
    red("12 OLD: the old staff pages carry forbidden words (%d hits, e.g. %s)" % (obad, [((o12.get("paper") or {}).get(str(n)) or {}).get("bad") for n in (4, 6)]), obad > 0)
    print("   13 Needs-you: NEW %s ms, OLD %s ms" % (b12.get("needs_ms"), o12.get("needs_ms")))
    return finish()


def finish():
    if FAILS:
        print("WALK_S533 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:260])
        return 1
    print("WALK_S533 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
