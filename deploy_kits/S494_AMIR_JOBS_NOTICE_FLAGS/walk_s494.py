#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s494.py -- kit S494_AMIR_JOBS_NOTICE_FLAGS: the walk (the brief's section 5), on the server, on scratch copies only.

    python3 -B walk_s494.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            --duty-map DUTY_MAP.json(v9)

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the four built files, OLD is the box as it is.
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  db / adb / spine    backup-API copies (taken after the installer made the empty amir_job table on the live database); every probe works
                      on its OWN further copies of them (rule 3); the walk's rows are keyed W494 and found by key, never by counting.

Each side runs in its own process ("fn": sections 1-5, by function and by route, header auth; "eye": section 6, signed in through the portal
as each login), every one with ORDER_PUSH_STUB (a scratch file) and a scratch RING_PORTAL_DIR: no walk can reach a real phone. Each
section's named control is the same probe on the OLD side and must go red there. Nothing is imported from inside deploy_kits (rule 11).
No person, phone, account number or real export line is in this file: the walk's names are W494 inventions.
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TAG = "W494JSON "
USERS = {"amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff", "manoj": "doctor"}
HROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
LOGINS = ("darpan", "shavez", "alisha", "shivani", "reception", "bhati", "sukhveer", "manoj", "amir")
NEW_ID = "amir.marg_jobs"
MAP8_MD5 = "f27423b61e50857875bb8f7ba4e5c57c"
N, FAILS, NOTES = [0], [], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def steady(h):
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def spans(h):
    """The visible words of a page, span by span (tags dropped, entities read)."""
    return [_html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<span[^>]*>(.*?)</span>", h or "", re.S)]


def stamp_now():
    return dt.datetime.now().replace(microsecond=0)


# ============================================================================================================== the "fn" probe (1-5)
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W494_DB0"))
    NEW = SIDE == "new"
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE)
    STUB = os.environ["ORDER_PUSH_STUB"]

    def mk(name):
        p = os.path.join(WORK, "w494_%s.db" % name)
        copydb(DB0, p)
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        return p, c

    def stub_clear():
        open(STUB, "w").close()

    def stub_read():
        try:
            return [json.loads(l) for l in open(STUB, encoding="utf-8") if l.strip()]
        except FileNotFoundError:
            return []
    import finance_app as fa                                            # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import order_sheet as OS                                            # noqa: E402
    import order_rules as OR                                            # noqa: E402
    import shelf_figure as SF                                           # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import aaj_kaam as AK                                               # noqa: E402
    import owner_console as OC                                          # noqa: E402
    for m in (AD, OS, OR, SF, SW, SA, AK, OC):
        assert m.__file__.startswith(FIN), m.__file__
    cl = fa.app.test_client()
    today = dt.date.today()
    now = stamp_now()

    def H(u):
        return {"X-Clinic-User": u, "X-Clinic-Role": HROLE[u]}

    # ---------------------------------------------------------------- 1  the notice (F-767)
    s1 = {}
    _p, c = mk("notice")
    c.execute("UPDATE setting SET value='marg_sheet' WHERE key='order.source'")
    c.commit()
    dmy = today.strftime("%d-%m-%Y")

    def sheet_rows(entries):
        rows = [["W494 ORDER SHEET"], ["SUPPLIER", "PHONES", "ITEM NAME", "PACKING", "ENTRY", "DATE", "QTY", "", "", "RATE", "VALUE"]]
        for e, sup, item, pk, q in entries:
            rows.append([sup, "", item, pk, e, dmy, q, "", "", 10.0, 20.0])
        rows.append(["TOTAL", "", "", "", "", "", "", "", "", "", 40.0])
        return rows
    ROWS = {"W494-SHEET-1": sheet_rows([("W494-E1", "W494 SUPPLIER A", "W494 ITEM ONE", "1*10", "2:0"), ("W494-E2", "W494 SUPPLIER B", "W494 ITEM TWO", "1*1", "3")]),
            "W494-SHEET-2": sheet_rows([("W494-E3", "W494 SUPPLIER A", "W494 ITEM THREE", "1*1", "4")])}
    CUR = ["W494-SHEET-1"]
    OS.rows_from_file = lambda path: ROWS[CUR[0]]                      # the xls reader is not the subject: load_file's own path is

    def notice(md5):
        r = c.execute("SELECT notice FROM order_sheet WHERE md5=?", (md5,)).fetchone()
        try:
            return json.loads(r[0]) if r and r[0] else None
        except ValueError:
            return r[0]
    to = [x.strip().lower() for x in OR._setting(c, "order.notice_to").split(",") if x.strip()]
    s1["to"] = to

    def failed_shape(raw):
        try:
            nt = json.loads(raw)
            s = nt.get("sent") or {}
            return (isinstance(s, dict) and bool(s) and not any(k in nt for k in ("retried", "lapsed", "dropped"))
                    and all(int(v.get("sent") or 0) == 0 for v in s.values()) and any(int(v.get("failed") or 0) > 0 for v in s.values()))
        except Exception:                                               # noqa: BLE001
            return False
    real_failed, aside = [], []
    for md5_, taken, raw in c.execute("SELECT md5, taken_at, notice FROM order_sheet WHERE notice IS NOT NULL AND md5 NOT LIKE 'W494%'").fetchall():
        if str(taken)[:10] < today.isoformat() and failed_shape(raw):
            real_failed.append(md5_)
        elif str(taken)[:10] == today.isoformat() and (failed_shape(raw) or '"pending": true' in str(raw)):
            aside.append(md5_)                                          # a real sheet of today: set aside on this copy, so the W494 sends stand alone
    for md5_ in aside:
        c.execute("UPDATE order_sheet SET notice=? WHERE md5=?", (json.dumps(dict(text="W494 set aside", dropped="W494 walk")), md5_))
    c.commit()
    s1["aside"] = len(aside)
    stub_clear()
    os.environ["ORDER_PUSH_NONE"] = "1"
    try:
        s1["load1"] = {k: v for k, v in OS.load_file(c, "/nonexistent/w494_sheet_1.xls", "W494-SHEET-1", name="W494 sheet one", src="walk").items()
                       if k in ("ok", "already", "new")}
    except Exception as e:                                              # noqa: BLE001
        s1["load1"] = "RAISED %s: %s" % (type(e).__name__, str(e)[:200])
    os.environ.pop("ORDER_PUSH_NONE", None)
    s1["n1_after_load"] = notice("W494-SHEET-1")
    s1["stub_after_load"] = [(p["user"], p["payload"]["body"]) for p in stub_read()]
    stub_clear()
    s1["cron1"] = OS.cron_pass(c, "W494")
    s1["n1_after_cron1"] = notice("W494-SHEET-1")
    s1["stub_cron1"] = [(p["user"], p["payload"]["body"]) for p in stub_read()]
    s1["real_after_cron1"] = {m: notice(m) for m in real_failed}
    stub_clear()
    s1["cron2"] = OS.cron_pass(c, "W494")
    s1["stub_cron2"] = len(stub_read())
    t_now = now.isoformat()
    t_yday = (now - dt.timedelta(days=1)).isoformat()
    t_stale = (now - dt.timedelta(minutes=75)).isoformat()

    def failed(text, at):
        return json.dumps(dict(text=text, sent={"darpan": dict(sent=0, failed=0), "shavez": dict(sent=0, failed=1), "alisha": dict(sent=0, failed=2)}, at=at))

    def put(md5, taken, nt):
        c.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, as_ordered, notice) VALUES (?,?,?,?,?,?,0,?)",
                  (md5, "W494 " + md5, "walk", "", taken, today.isoformat(), nt))
        c.commit()
    put("W494-RETRY", t_now, failed("W494 retry text", t_now))
    put("W494-YDAY", t_yday, failed("W494 yesterday text", t_yday))
    put("W494-STALE", t_stale, failed("W494 stale text", t_stale))
    put("W494-PEND2", t_now, json.dumps(dict(text="W494 pending two", pending=True, at=t_now)))
    orig = OR._push
    OR._push = lambda u, p: (0, 1) if p.get("body") == "W494 pending two" else orig(u, p)   # its first send fails on every phone
    stub_clear()
    s1["cron3"] = OS.cron_pass(c, "W494")
    OR._push = orig
    s1["stub_cron3"] = [(p["user"], p["payload"]["body"]) for p in stub_read()]
    s1["shapes3"] = {m: notice(m) for m in ("W494-RETRY", "W494-YDAY", "W494-STALE", "W494-PEND2")}
    stub_clear()
    s1["cron4"] = OS.cron_pass(c, "W494")
    s1["stub_cron4"] = [(p["user"], p["payload"]["body"]) for p in stub_read()]
    s1["shapes4"] = {m: notice(m) for m in ("W494-RETRY", "W494-PEND2")}
    stub_clear()
    s1["cron5"] = OS.cron_pass(c, "W494")
    s1["stub_cron5"] = len(stub_read())
    c.execute("UPDATE setting SET value='system' WHERE key='order.source'")
    c.commit()
    put("W494-DROP", t_now, failed("W494 drop text", t_now))
    stub_clear()
    s1["cron6"] = OS.cron_pass(c, "W494")
    s1["stub_cron6"] = len(stub_read())
    s1["drop"] = notice("W494-DROP")
    c.execute("UPDATE setting SET value='marg_sheet' WHERE key='order.source'")
    c.commit()
    CUR[0] = "W494-SHEET-2"
    stub_clear()
    try:
        OS.load_file(c, "/nonexistent/w494_sheet_2.xls", "W494-SHEET-2", name="W494 sheet two", src="walk")
    except Exception as e:                                              # noqa: BLE001
        s1["load2_err"] = "%s: %s" % (type(e).__name__, str(e)[:200])
    s1["n2"] = notice("W494-SHEET-2")
    s1["stub_load2"] = [(p["user"], p["payload"]["body"]) for p in stub_read()]
    s1["setting_row"] = [tuple(r) for r in c.execute("SELECT value, note FROM setting WHERE key='order.sheet_notice_max_min'")]
    c.close()
    out["s1"] = s1

    # ---------------------------------------------------------------- 2  one spot-count line (F-771)
    s2 = {}
    _p, c = mk("spot")
    until = (today + dt.timedelta(days=7)).isoformat()
    for i, days in enumerate((5, 3, 1), 1):
        c.execute("INSERT INTO stock_watch_notice (at, kind, for_who, text, text_hi, ref, until, once_key) VALUES (?,?,?,?,?,?,?,?)",
                  ((today - dt.timedelta(days=days)).isoformat() + "T06:30:03", "spot_missed", "owner", "W494 spot missed, %d days ago" % days, "",
                   "W494", until, "W494-spot-%d" % i))
    for i in (1, 2):
        c.execute("INSERT INTO stock_watch_notice (at, kind, for_who, text, text_hi, ref, until, once_key) VALUES (?,?,?,?,?,?,?,?)",
                  ((today - dt.timedelta(days=i)).isoformat() + "T07:00:00", "trace_unexplained", "owner", "W494 trace %d unexplained" % i, "",
                   "W494", until, "W494-trace-%d" % i))
    c.commit()
    lines = [x.get("text") for x in SW.needs_you_lines(c)]
    s2["w494_spot"] = [x for x in lines if x.startswith("W494 spot missed")]
    s2["all_spot"] = [x for x in lines if x.startswith("W494 spot missed") or x.startswith("Spot counts:")]
    s2["trace"] = [x for x in lines if x.startswith("W494 trace")]
    s2["n_lines"] = len(lines)
    c.close()
    out["s2"] = s2

    # ---------------------------------------------------------------- 3  the re-judge (F-765)
    s3 = {}
    _p, c = mk("rejudge")
    spp = os.path.join(WORK, "w494_spine3.db")
    copydb(os.environ["SPINE_DB"], spp)
    spc = sqlite3.connect(spp, timeout=60)
    sp = SW.Spine(spp)
    G = {"G1": "W494 GAP ONE", "G2": "W494 GAP TWO", "G3": "W494 GAP THREE", "G4": "W494 GAP FOUR", "G5": "W494 GAP FIVE"}
    K = {g: sp.key(n) for g, n in G.items()}
    CA, CB, C1, C2, C3, C4 = "2031-02-10", "2031-02-12", "2031-03-01", "2031-03-03", "2031-03-05", "2031-03-07"
    BASE = "2031-02-20"
    W2 = "Marg moved -5 beyond its own sales and purchases on %s with no voucher filed" % C2
    WB = "Marg moved -5 beyond its own sales and purchases on %s with no voucher filed" % CB
    W2b = "Marg moved -6 beyond its own sales and purchases on %s with no voucher filed" % C2

    def ins(as_on, g, marg, flagged=0, why=None, approx=0, move=None):
        c.execute("INSERT INTO s454_shelf_gap (as_on, item, shelf, marg, gap, marg_move, voucher, base_day, pack, approx, flagged, why, at) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (as_on, G[g], marg, marg, 0.0, move, 0.0, BASE, 1, approx, flagged, why, as_on + "T10:40:03"))
    ins(C1, "G1", 20)
    ins(C2, "G1", 15, 1, W2, move=-5.0)
    ins(C3, "G1", 15, 1, W2, move=0.0)
    ins(C4, "G1", 15, 1, W2, move=0.0)
    ins(C1, "G2", 20)
    ins(C2, "G2", 14, 1, W2b, move=-6.0)
    ins(CA, "G3", 30)
    ins(CB, "G3", 25, 1, WB, move=-5.0)
    for d_ in (C1, C2, C3, C4):
        ins(d_, "G3", 25, 1, WB, move=0.0)
    ins(C1, "G4", 10)
    ins(C2, "G4", 50, 0, "a new count since the last closing (rebased)", move=40.0)
    ins(C1, "G5", 10)
    ins(C2, "G5", 5, 1, W2, approx=1, move=-5.0)
    c.commit()

    def sale(g, day, units, add=True):
        if add:
            spc.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,?,?,?)", (K[g], day, "SALE", -float(units), "W494"))
        else:
            spc.execute("DELETE FROM sp_move WHERE k20=? AND date=? AND ref='W494'", (K[g], day))
        spc.commit()
    sale("G3", "2031-02-11", 5)                                         # explains G3's origin -- outside the window
    sale("G5", "2031-03-02", 5)                                         # explains G5's row -- an approximate row

    def rows():
        return {"%s@%s" % (r["item"], r["as_on"]): [r[k] for k in r.keys()] for r in
                c.execute("SELECT * FROM s454_shelf_gap WHERE item LIKE 'W494 GAP %' ORDER BY item, as_on")}

    def whole():
        return md5b(json.dumps([list(r) for r in c.execute("SELECT * FROM s454_shelf_gap ORDER BY as_on, item")], default=str).encode())
    r0 = rows()
    s3["rg_a"] = SF.record_gaps(c, SW.Spine(spp))                       # nothing explains G1 yet
    r1 = rows()
    sale("G1", "2031-03-02", 5)                                         # the window's sale arrives at the spine after the flag
    s3["rg_b"] = SF.record_gaps(c, SW.Spine(spp))
    r2 = rows()
    s3["second"] = [SF.rejudge(c, SW.Spine(spp)) if NEW else None, whole()]
    s3["second_after"] = whole()
    sale("G1", "2031-03-02", 5, add=False)                              # the spine's evidence shrinks again
    s3["shrunk"] = SF.rejudge(c, SW.Spine(spp)) if NEW else None
    r3 = rows()
    try:
        b = whole()
        s3["nospine"] = [SF.rejudge(c, SW.Spine(os.path.join(WORK, "no_such_spine.db"))) if NEW else None,
                         SF.record_gaps(c, SW.Spine(os.path.join(WORK, "no_such_spine.db"))), b == whole()]
    except Exception as e:                                              # noqa: BLE001
        s3["nospine"] = "RAISED %s: %s" % (type(e).__name__, e)
    # a later W494 closing, recorded by record_gaps itself after the clear (the copy's newest snapshot becomes the W494 one)
    c.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES ('09-03-2031', ?, 15, '1*1', 1, ?, 'W494')",
              (G["G1"], "2031-03-09T10:00:00"))
    c.execute("INSERT INTO stock_point (item_norm, item, at, qty_units, source, by, status) VALUES (?,?,?,?,?,?,?)",
              (SW.norm_name(G["G1"]), G["G1"], BASE + "T08:00:00", 20, "spot", "W494", "settled"))
    c.commit()
    s3["rg_c"] = SF.record_gaps(c, SW.Spine(spp))
    r4 = rows()
    s3["rows"] = dict(r0=r0, r1=r1, r2=r2, r3=r3, r4=r4)
    c.close()
    spc.close()
    # the copy of the live rows, no W494: per closing in the window, first flags and carried flags before -> after (NEW only)
    if NEW:
        _p, c = mk("live3")
        sp = SW.Spine(os.environ["SPINE_DB"])

        def census():
            newest = c.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0]
            lo = (dt.date.fromisoformat(newest) - dt.timedelta(days=int(float(SF._setting(c, "stock.gap_rejudge_days", "7"))))).isoformat()
            res = {}
            for as_on, why, fl in c.execute("SELECT as_on, why, flagged FROM s454_shelf_gap WHERE as_on>=?", (lo,)).fetchall():
                e = res.setdefault(as_on, [0, 0, 0])
                if fl:
                    if str(why or "").startswith("Marg moved ") and (" on %s" % as_on) in str(why):
                        e[0] += 1
                    else:
                        e[1] += 1
                elif str(why or "").startswith("explained by a report that arrived later"):
                    e[2] += 1
            return lo, res
        lo, before = census()
        n = SF.rejudge(c, sp)
        _lo, after = census()
        mins = float(SF._setting(c, "stock.gap_min_packs", "1"))
        late, pos = 0, 0
        for d_, item, marg, pack in c.execute("SELECT as_on, item, marg, pack FROM s454_shelf_gap WHERE flagged=1 AND approx=0 AND as_on>=? AND why LIKE 'Marg moved %' "
                                              "AND instr(why, ' on ' || as_on) > 0", (lo,)).fetchall():
            prev = c.execute("SELECT MAX(as_on) FROM s454_shelf_gap WHERE as_on<?", (d_,)).fetchone()[0]
            p = c.execute("SELECT marg FROM s454_shelf_gap WHERE as_on=? AND item=?", (prev, item)).fetchone() if prev else None
            if not p or p[0] is None or marg is None:
                continue
            sold, ret, bought = SF.movements(sp, item, prev, d_, incl_from=False)
            move = float(marg) - float(p[0]) - (bought - sold + ret)
            if move <= 0:
                continue
            pos += 1
            thr = mins * (int(pack or 1) if int(pack or 1) > 1 else 1)
            d0 = (dt.date.fromisoformat(prev) - dt.timedelta(days=7)).isoformat()
            if any(abs(float(x["units"] or 0) - move) < thr for x in
                   sp.q("SELECT units FROM sp_move WHERE k20=? AND kind='PURCHASE' AND date>? AND date<=?", sp.key(item), d0, prev)):
                late += 1
        out["s3_live"] = dict(lo=lo, before=before, after=after, cleared=n, positive_left=pos, late_keyed=late)
        c.close()
    out["s3"] = s3

    # ---------------------------------------------------------------- 4  his card (D686) -- on the app's own copy, through the routes
    s4 = {}
    A = os.environ["FINANCE_DB"]
    ca = sqlite3.connect(A, timeout=60)
    ca.row_factory = sqlite3.Row
    REAL_STAGE = SA.amir_stage

    def step_get(n, who="amir"):
        r = cl.get("/finance/amir/step/%d" % n, headers=H(who))
        return r.status_code, r.get_data(as_text=True)

    def post(n, job):
        r = cl.post("/finance/amir/step/%d" % n, data={"job": job}, headers=H("amir"))
        return [r.status_code, (r.headers.get("Location") or "").replace("http://localhost", "")]
    # (a) no open job, the stage as it is: every step's page NEW = OLD (compared by the walk)
    s4["noj"] = {}
    for n in range(1, 8):
        code, h = step_get(n)
        s4["noj"][n] = "%s %s" % (code, md5b(steady(h).encode()))
    STG = [None]
    SA.amir_stage = lambda con, cid=None: STG[0]
    ts = now.strftime("%Y-%m-%d %H:%M:%S")

    def job(key, kind, subject, show=ts, thi=None, shi=None):
        ca.execute("INSERT INTO amir_job (key, kind, subject, text_hi, sub_hi, created_at, created_by, show_from) VALUES (?,?,?,?,?,?,?,?)",
                   (key, kind, subject, thi, shi, ts, "W494", show))
        return ca.execute("SELECT id FROM amir_job WHERE key=?", (key,)).fetchone()[0]

    def bill(bid, sup, no, day):
        ca.execute("INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (?,?,?,?,?,?,1000)",
                   (bid, sup, sup, no, day, day[:7]))
    J = {}
    J["c1"] = job("W494:cat:1", "category", "W494 ORTHO ONE", show=None)
    J["c2"] = job("W494:cat:2", "category", "W494 ORTHO TWO", show=None)
    J["va"] = job("W494:vbill:A", "vendor_bill", "W494 VENDOR A")
    J["vb"] = job("W494:vbill:B", "vendor_bill", "W494 VENDOR B")
    J["tap"] = job("W494:pay:1", "tap", "W494 VENDOR A", thi="W494 VENDOR A: ₹5 cash payment ki entry Marg mein kijiye.", shi="W494 ka purana balance.")
    J["hid"] = job("W494:pay:hidden", "tap", "W494 VENDOR B", show=None, thi="W494 hidden line", shi=None)
    bill(9494001, "W494 VENDOR A", "W494-A1", "2030-12-01")
    bill(9494002, "W494 VENDOR A", "W494-A2", "2031-01-15")
    bill(9494003, "W494 VENDOR B", "W494-B1", "2031-02-20")
    ca.commit()
    s4["J"] = J

    def jobs_state():
        return {r["key"]: [r["show_from"] is not None, r["said_what"], r["said_by"], r["done_how"], r["done_at"] is not None]
                for r in ca.execute("SELECT * FROM amir_job WHERE key LIKE 'W494:%' ORDER BY id")}

    def view(n=6, who="amir"):
        code, h = step_get(n, who)
        sp_ = [x for x in spans(h) if x]
        return dict(code=code, spans=sp_, has_jobs=("id=s494jobs" in h), buttons=sorted(set(re.findall(r"name=job value='?([a-z]+(?::\d+)?)'?", h))))
    STG[0] = None
    s4["none"] = view()
    STG[0] = {"stage": "A", "count_id": 948494, "A": {"open": 1, "total": 1, "entered": 0}, "B": {}, "C": {}, "numbers": {}}
    s4["stageA"] = view()
    STG[0] = {"stage": "B", "count_id": 948494, "A": {}, "B": {"open": [], "old": [], "total": 0, "verified": 0}, "C": {}, "numbers": {}}
    s4["stageB"] = view()
    s4["state_B"] = jobs_state()
    s4["owner_day"] = [x for x in spans(cl.get("/finance/amir/day", headers=H("manoj")).get_data(as_text=True)) if "one-time" in x] + \
        [x for x in re.findall(r"<p class=big>([^<]*)</p>", cl.get("/finance/amir/day", headers=H("manoj")).get_data(as_text=True)) if "one-time" in x]
    s4["gate"] = list(AD.GATE_STEPS)
    code7, h7 = step_get(7)
    s4["step7_before"] = [code7, [x for x in spans(h7) if x][:40], re.findall(r"<li>([^<]*)</li>", h7)]
    r = cl.post("/finance/amir/step/7", data={}, headers=H("amir"))
    s4["close"] = [r.status_code, [tuple(x) for x in ca.execute("SELECT closed_at IS NOT NULL, closed_by FROM amir_day WHERE day=?",
                                                                (dt.datetime.now(AD.IST).strftime("%Y-%m-%d"),))]]
    if NEW:
        s4["tap4"] = post(4, "tap:%d" % J["tap"])
        s4["after_tap"] = view()
        s4["state_tap"] = jobs_state()
        s4["cat5"] = post(5, "cat")
        s4["after_cat"] = view()
        s4["state_cat"] = jobs_state()
        noon = today.isoformat() + " 12:00:00"
        ca.execute("UPDATE amir_job SET said_at=? WHERE key LIKE 'W494:cat:%'", (noon,))
        ca.commit()
        spc = sqlite3.connect(os.environ["SPINE_DB"], timeout=60)
        yday = (today - dt.timedelta(days=1)).isoformat()

        def catlist(md5, hh, facts):
            ca.execute("INSERT INTO mi_file (md5, type, verdict, date_from, date_to, received_at, stamp) VALUES (?,?,?,?,?,?,?)",
                       (md5, "CATEGORY_WISE_ITEM_LIST", "VERIFIED", yday, yday, "%sT%s:00:00+05:30" % (today.isoformat(), hh), "W494"))
            ca.commit()
            for nm, v in facts:
                spc.execute("INSERT INTO sp_item_fact (name, packing, fact, value, as_on, source_md5) VALUES (?,?,?,?,?,?)", (nm, "1*1", "category", v, yday, md5))
            spc.commit()
        catlist("w494" + "0" * 27 + "1", "11", [("W494 ORTHO ONE", "COMMON")])               # received EARLIER the same day: no reopen
        s4["l1"] = view()
        s4["state_l1"] = jobs_state()
        catlist("w494" + "0" * 27 + "2", "13", [("W494 ORTHO ONE", "COMMON")])               # later the same day, still another category
        s4["l2"] = view()
        s4["state_l2"] = jobs_state()
        s4["owner_l2"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494" in x.get("text", "")]
        catlist("w494" + "0" * 27 + "3", "14", [("W494 ORTHO ONE", "ORTHOTICS")])            # the label: proved
        s4["l3"] = view()
        s4["state_l3"] = jobs_state()
        s4["owner_l3"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494" in x.get("text", "")]
        spc.close()
        # vendor B: the owner's 'not done' line at amir.job_wait_days (10)
        for d_ in (9, 11):
            ca.execute("UPDATE amir_job SET show_from=? WHERE id=?", ((now - dt.timedelta(days=d_)).strftime("%Y-%m-%d %H:%M:%S"), J["vb"]))
            ca.commit()
            s4["wait%d" % d_] = [x["text"] for x in AD.needs_you_lines(ca) if "one-time Marg jobs not done" in x.get("text", "")]
        s4["dutyline_wait"] = [x.get("text") for x in AD._s444_duty_lines(ca) if x.get("duty") == NEW_ID]
        s4["scan7"] = post(7, "scan:%d" % J["va"])
        s4["after_scan"] = view()
        s4["owner_scan"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494 VENDOR A" in x.get("text", "")]
        ca.execute("INSERT INTO purchase_vendor_contact (vendor_norm, vendor, updated_at, acct_no, ifsc, source) VALUES (?,?,?,?,?,?)",
                   ("W494 VENDOR A", "W494 VENDOR A", ts, "W494-ACCOUNT", "W494-IFSC", "W494"))
        ca.commit()
        s4["after_bank"] = view()
        s4["state_bank"] = jobs_state()
        s4["owner_bank"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494 VENDOR A" in x.get("text", "")]
        s4["nf6"] = post(6, "nf:%d" % J["vb"])
        s4["after_nf"] = view()
        s4["owner_nf"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494 VENDOR B" in x.get("text", "")]
        J["vc"] = job("W494:vbill:C", "vendor_bill", "W494 VENDOR C")
        bill(9494004, "W494 VENDOR C", "W494-C1", "2031-02-25")
        ca.execute("INSERT INTO purchase_scan_link (bill_id, asset_bill_id, grade, matched_on, linked_at) VALUES (?,?,?,?,?)", (9494004, 9494999, "EXACT", "W494", ts))
        ca.commit()
        s4["after_link"] = view()
        s4["state_link"] = jobs_state()
        s4["owner_link"] = [x["text"] for x in AD.needs_you_lines(ca) if "W494 VENDOR C" in x.get("text", "")]
        before = jobs_state()
        s4["bad_posts"] = [post(6, v) for v in ("tap:%d" % J["hid"], "scan:%d" % J["hid"], "tap:999999", "scan:abc", "nf:%d" % J["va"], "cat;drop", "tap:%d" % J["va"])]
        s4["bad_same"] = jobs_state() == before
        s4["audit"] = [tuple(x) for x in ca.execute("SELECT who, action, ref FROM purchase_audit WHERE action='job' AND ref LIKE 'W494:%' ORDER BY id")]
        # a broken table, then none: every step still renders
        ca.execute("ALTER TABLE amir_job RENAME TO amir_job_w494")
        ca.execute("CREATE TABLE amir_job (x)")
        ca.commit()
        s4["broken"] = {n: step_get(n)[0] for n in range(1, 8)}
        s4["broken_jobs"] = AD._s494_jobs(ca)
        ca.execute("DROP TABLE amir_job")
        ca.commit()
        s4["dropped"] = {n: step_get(n)[0] for n in range(1, 8)}
    SA.amir_stage = REAL_STAGE
    ca.close()
    out["s4"] = s4

    # ---------------------------------------------------------------- 5  the duty
    s5 = {}
    m9 = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    du = [d for d in m9["duties"] if d["id"] == NEW_ID]
    s5["entry"] = du[0] if du else None
    sql = du[0]["due_sql"] if du else "SELECT 0, NULL"
    _p, c = mk("duty")
    s5["due0"] = list(c.execute(sql).fetchone())
    for k, show, said, done in (("W494:d1", "2031-01-05 10:00:00", None, None), ("W494:d2", "2031-01-07 09:00:00", None, None),
                                ("W494:d3", "2031-01-01 09:00:00", "2031-01-02 09:00:00", None), ("W494:d4", "2031-01-01 09:00:00", None, "2031-01-03 09:00:00"),
                                ("W494:d5", None, None, None)):
        c.execute("INSERT INTO amir_job (key, kind, subject, created_at, created_by, show_from, said_at, done_at) VALUES (?,?,?,?,?,?,?,?)",
                  (k, "tap", "W494 " + k, "2031-01-01 09:00:00", "W494", show, said, done))
    c.commit()
    s5["due1"] = list(c.execute(sql).fetchone())
    c.execute("UPDATE amir_job SET said_at='2031-01-08 09:00:00' WHERE key LIKE 'W494:d%' AND said_at IS NULL AND done_at IS NULL")
    c.commit()
    s5["due2"] = list(c.execute(sql).fetchone())
    c.close()
    maps = {"v8": os.environ["MAP8"], "v9": os.environ["DUTY_MAP"]}
    s5["load_defs"] = {}
    cuts, items = {}, {}
    for tag, path in maps.items():
        AK.DUTY_MAP = path
        m, x = AK.load_defs()
        s5["load_defs"][tag] = [m.get("_err"), m.get("version"), x.get("_err")]
        rd = AK.Reader(DB0)
        try:
            cuts[tag] = {}
            for lg in LOGINS:
                k = AK.person_key(lg, rd.people)
                cuts[tag][lg] = json.dumps(AK.person_list(rd, rd.people[k]) if k else None, sort_keys=True, default=str)
        finally:
            rd.close()
        allp = AK.build_all(DB0, now=dt.datetime.combine(today, dt.time(11, 0)))
        items[tag] = {}
        for it in allp["items"]:
            items[tag].setdefault(str(it.get("person") or it.get("who") or "?"), []).append(json.dumps(it, sort_keys=True, default=str))
    s5["cuts_equal"] = {lg: cuts["v8"][lg] == cuts["v9"][lg] for lg in LOGINS}
    s5["items_v9_only"] = sorted({p: [json.loads(i).get("id") for i in v if i not in items["v8"].get(p, [])] for p, v in items["v9"].items()}.items())
    s5["items_v8_only"] = sorted({p: [json.loads(i).get("id") for i in v if i not in items["v9"].get(p, [])] for p, v in items["v8"].items()}.items())
    OC.DUTY_MAP = os.environ["DUTY_MAP"]
    try:
        rdu = OC.read_duties(DB0)
        s5["console"] = [rdu.get("version"), {d["id"]: [d.get("n"), d.get("err")] for d in rdu["duties"] if d["id"] == NEW_ID}, sum(1 for d in rdu["duties"] if d.get("err"))]
    except Exception as e:                                              # noqa: BLE001
        s5["console"] = "RAISED %s: %s" % (type(e).__name__, e)
    out["s5"] = s5
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "eye" probe (6)
def probe_eye():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    NEW = SIDE == "new"
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import shelf_figure as SF                                           # noqa: E402
    assert AD.__file__.startswith(FIN) and SF.__file__.startswith(FIN)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W494J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    out = dict(side=SIDE)
    cx = sqlite3.connect(DB, timeout=60)
    if NEW:                                                             # the box after the install: seeded, one refresh, the first tick's re-judge
        out["seed"] = AD.s494_seed_jobs(cx)
        out["refresh"] = AD._s494_refresh(cx)
        out["rejudge"] = SF.rejudge(cx)
        out["jobs"] = [list(r) for r in cx.execute("SELECT key, show_from IS NOT NULL, said_what, done_how FROM amir_job ORDER BY id")]
        du = [d for d in dm["duties"] if d["id"] == NEW_ID][0]
        out["due"] = list(cx.execute(du["due_sql"]).fetchone())
    out["gap_flags"] = len(SF.gap_flags(cx)[1])
    cx.close()

    def page(path, ck):
        body, code = "", 0
        for _hop in range(4):
            rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
            code = rr2.status_code
            if code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                path = rr2.headers["Location"].replace(BASE, "")
                continue
            body = rr2.get_data(as_text=True)
            break
        return code, body
    EXTRA = {"amir": ["/finance/amir"] + ["/finance/amir/step/%d" % n for n in range(1, 8)] + ["/finance/aaj"],
             "manoj": ["/finance/amir/day", "/finance/approvals", "/finance/console", "/finance/aaj", "/finance/sanjeevni/api/needs-you"],
             "darpan": ["/finance/stockmatch", "/finance/aaj"], "shavez": ["/finance/aaj"], "reception": ["/finance/aaj"]}
    cookies = {}
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    eye = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        cookies[who] = (m.group(1) if m else "")
        tok = cookies[who]
        ck = "clinic_sso=" + tok
        r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": ck})
        home = r.get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        pages = {"home": md5b(steady(home.replace(tok, "TOKEN")).encode())}
        texts = {}
        rows, doors = [], set(EXTRA[who])
        mine = {who, (dm.get("shared") or {}).get(who)}
        for du in dm.get("duties") or []:
            if du.get("person") not in mine:
                continue
            row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None, "door": du.get("door")}
            q = str(du.get("due_sql") or "").strip().rstrip(";")
            n = None
            if q:
                try:
                    rr = ro.execute(q).fetchone()
                    n = int((rr[0] if rr else 0) or 0)
                    row["since"] = rr[1] if rr is not None and len(rr) > 1 else None
                except Exception as e:                                  # noqa: BLE001
                    n = "ERR " + str(e)[:80]
            row["due_n"] = n
            door, mark = du.get("door"), du.get("door_marker")
            if door and str(door).startswith("/finance/"):
                doors.add(str(door))
                if mark and isinstance(n, int) and n > 0:
                    body = page(str(door), ck)[1]
                    row["door_seen"] = (mark in body) or (mark in _html.unescape(body))
            rows.append(row)
        for d in sorted(doors):
            code, body = page(d, ck)
            pages[d] = "%s %s" % (code, md5b(steady(body.replace(tok, "TOKEN")).encode()))
            if d in ("/finance/amir/step/6", "/finance/amir/day"):
                texts[d] = [x for x in spans(body) if x][:120] + re.findall(r"<p class=big>([^<]*)</p>", body)
        eye[who] = dict(status=r.status_code, n_tiles=len(seen), duties=rows, pages=pages, texts=texts)
    try:
        cx = sqlite3.connect(DB, timeout=60)
        eye["_needs_you"] = [x.get("text") for x in AD.needs_you_lines(cx)]
        import stock_watch as SW                                        # noqa: E402
        eye["_needs_you"] += [x.get("text") for x in SW.needs_you_lines(cx)]
        g = SF.gap_line(cx)
        eye["_needs_you"] += [g["text"]] if g else []
        cx.close()
    except Exception as e:                                              # noqa: BLE001
        eye["_needs_you"] = "RAISED %s" % e
    ro.close()
    out["eye"] = eye
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-eye"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_eye()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % W
    os.makedirs(W)
    # the v8 map, made back from v9 by taking out exactly what S494 added -- it must read back as the pinned v8 bytes
    m9raw = open(a.duty_map, "rb").read()
    m9 = json.loads(m9raw.decode("utf-8"))
    m8 = dict(m9, version=8, kit="S488_DATES_AND_WAITS", duties=[d for d in m9["duties"] if d["id"] != NEW_ID],
              _note=m9["_note"].split(" S494 (07-Oct-2026", 1)[0])
    m8raw = (json.dumps(m8, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    map8 = os.path.join(W, "DUTY_MAP_v8.json")
    open(map8, "wb").write(m8raw)
    if not check("the v9 map less S494's one duty reads back as the v8 map byte for byte (md5 %s = the brief's pin %s)" % (md5b(m8raw)[:8], MAP8_MD5[:8]),
                 md5b(m8raw) == MAP8_MD5 and m9["version"] == 9 and m9["kit"] == "S494_AMIR_JOBS_NOTICE_FLAGS" and len(m9["duties"]) == len(m8["duties"]) + 1):
        return finish()
    # the installer's table and the code's are one statement
    inst = open(os.path.join(a.kit, "install_S494_AMIR_JOBS_NOTICE_FLAGS.sh"), encoding="utf-8").read()
    dd = re.search(r'^DDL494="([^"]+)"$', inst, re.M)
    built = open(os.path.join(a.fin_new, "amir_day.py"), encoding="utf-8").read()
    bd = re.search(r'S494_DDL = \("([^"]+)"\n\s+"([^"]+)"\n\s+"([^"]+)"\)', built)
    check("the installer's CREATE TABLE amir_job (step 3, before the gates) is the code's S494_DDL letter for letter",
          bool(dd and bd) and dd.group(1) == "".join(bd.groups()), (dd.group(1)[:60] if dd else None))
    # the walk's own sign-in: a random secret and its own user store, in the scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W494 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, fin):
        wd = os.path.join(W, "%s_%s" % (mode, side))
        for sub in ("nosso", "nomarg", "noring"):
            os.makedirs(os.path.join(wd, sub))
        dbp, adbp, spp = [os.path.join(wd, "w494_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W494_DB0=a.db,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "eye" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, MAP8=map8, W494J=json.dumps(dict(pw=pw)), MARG_INGEST_DIR=os.path.join(wd, "nomarg"),
                   RING_PORTAL_DIR=os.path.join(wd, "noring"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"),
                   ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE",
                  "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    NW, OL = run("fn", "new", a.fin_new), run("fn", "old", a.fin_old)
    if not check("both function probes ran to the end (NEW = the box + S494, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()
    td = dt.date.today()

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  the arrival notice (F-767)")
    n1, o1 = NW["s1"], OL["s1"]
    to = n1["to"]
    text1 = (n1["n1_after_load"] or {}).get("text") if isinstance(n1["n1_after_load"], dict) else None
    check("load_file with ORDER_PUSH_NONE (the web process): the W494 sheet's notice is pending (%s) and the stub is empty (%d payloads)"
          % (n1["n1_after_load"], len(n1["stub_after_load"])),
          isinstance(n1["n1_after_load"], dict) and n1["n1_after_load"].get("pending") is True and "sent" not in n1["n1_after_load"]
          and n1["stub_after_load"] == [] and bool(text1), n1["load1"])
    check("control OLD (it ignores the switch): the stub holds one payload per login of order.notice_to at load (%s)" % sorted(u for u, _b in o1["stub_after_load"]),
          sorted(u for u, _b in o1["stub_after_load"]) == sorted(to) and len(to) > 0 and isinstance(o1["n1_after_load"], dict) and "sent" in o1["n1_after_load"])
    a1 = n1["n1_after_cron1"] or {}
    check("cron_pass (the tick, no switch): one payload per login %s carrying the stored text '%s'; the row reads pending false, sent filled, first_at kept; "
          "the tick's out says notices %s" % (sorted(to), text1, n1["cron1"].get("notices")),
          sorted(u for u, _b in n1["stub_cron1"]) == sorted(to) and all(b == text1 for _u, b in n1["stub_cron1"]) and a1.get("pending") is False
          and sorted(a1.get("sent") or {}) == sorted(to) and a1.get("first_at") == n1["n1_after_load"].get("at") and "retried" not in a1
          and n1["cron1"].get("notices") == 1, (a1, n1["cron1"]))
    check("a second cron_pass sends nothing (%d payloads; notices %s)" % (n1["stub_cron2"], n1["cron2"].get("notices")), n1["stub_cron2"] == 0 and n1["cron2"].get("notices") == 0)
    rl = n1["real_after_cron1"]
    check("the real rows of an earlier day in the failed shape (the 06-Oct sheet) are marked lapsed at the first tick and never sent (%d row(s))" % len(rl),
          all(isinstance(v, dict) and v.get("lapsed") is True and v.get("pending") is False for v in rl.values())
          and not any(b != text1 for _u, b in n1["stub_cron1"]), {k[:8]: (v or {}).get("lapsed") for k, v in rl.items()})
    sh = n1["shapes3"]
    bodies3 = [b for _u, b in n1["stub_cron3"]]
    check("W494 rows in the 06-Oct shape: taken now -> retried once (%s, sent %s); dated yesterday -> lapsed, not sent (%s); taken 75 minutes ago (setting 60) -> "
          "lapsed, not sent (%s)" % (sh["W494-RETRY"].get("retried"), sorted((sh["W494-RETRY"].get("sent") or {})), sh["W494-YDAY"].get("lapsed"), sh["W494-STALE"].get("lapsed")),
          sh["W494-RETRY"].get("retried") is True and bodies3.count("W494 retry text") == len(to) and sh["W494-RETRY"].get("first_at")
          and sh["W494-YDAY"].get("lapsed") is True and "W494 yesterday text" not in bodies3
          and sh["W494-STALE"].get("lapsed") is True and "W494 stale text" not in bodies3, sh)
    p2, p2b = sh["W494-PEND2"], n1["shapes4"]["W494-PEND2"]
    check("a pending row whose first send fails on every phone becomes the failed shape (%s) and is tried once more at the next tick (retried %s, %d payloads); "
          "the retried row is not sent again (%s)" % (sorted((p2.get("sent") or {}).items())[:2], p2b.get("retried"),
                                                      sum(1 for _u, b in n1["stub_cron4"] if b == "W494 pending two"), n1["stub_cron5"]),
          p2.get("pending") is False and "retried" not in p2 and all(v.get("sent") == 0 for v in (p2.get("sent") or {}).values())
          and p2b.get("retried") is True and sum(1 for _u, b in n1["stub_cron4"] if b == "W494 pending two") == len(to)
          and not any(b == "W494 retry text" for _u, b in n1["stub_cron4"]) and n1["stub_cron5"] == 0)
    check("order.source moved off marg_sheet -> dropped, not sent (%s; %d payloads)" % (n1["drop"], n1["stub_cron6"]),
          (n1["drop"] or {}).get("dropped") == "source" and n1["stub_cron6"] == 0)
    check("without the switch, _sheet_notice sends at once as today (%s; %d payloads)" % (sorted(((n1["n2"] or {}).get("sent") or {})), len(n1["stub_load2"])),
          isinstance(n1["n2"], dict) and sorted((n1["n2"].get("sent") or {})) == sorted(to) and len(n1["stub_load2"]) == len(to) and "pending" not in n1["n2"])
    check("the setting row order.sheet_notice_max_min is seeded by order_sheet.ensure() itself with its note: %s" % n1["setting_row"],
          n1["setting_row"] == [["60", "Order sheet arrived: minutes after which the arrival notice is no longer sent"]])

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  one spot-count line (F-771)")
    n2, o2 = NW["s2"], OL["s2"]
    check("three W494 spot_missed notices on three days of the last week: Needs-you carries exactly one spot line, the newest (%s)" % n2["all_spot"],
          n2["all_spot"] == ["W494 spot missed, 1 days ago"], n2)
    check("control OLD gives three W494 spot lines (%d; with the box's own: %d)" % (len(o2["w494_spot"]), len(o2["all_spot"])), len(o2["w494_spot"]) == 3)
    check("two trace_unexplained notices still make two lines (%s)" % n2["trace"], sorted(n2["trace"]) == ["W494 trace 1 unexplained", "W494 trace 2 unexplained"])

    # ------------------------------------------------------------------------------------------------------------------------------- 3
    print("-- 3  the re-judge (F-765)")
    n3, o3 = NW["s3"], OL["s3"]
    R, RO = n3["rows"], o3["rows"]
    COL = {"as_on": 0, "item": 1, "marg_move": 5, "voucher": 6, "approx": 9, "flagged": 10, "why": 11}

    def fl(rs, key):
        return (rs.get(key) or [None] * 13)[COL["flagged"]]
    g1 = ["W494 GAP ONE@2031-03-0%d" % d for d in (3, 5, 7)]
    check("before the sale reaches the spine nothing explains G1: record_gaps (NEW: re-judge first) leaves every W494 row as it was", R["r1"] == R["r0"])
    check("the window's sale added to the scratch spine after the flag: G1's first flag is cleared, its two copies with it (%s); the why: '%s'"
          % ([fl(R["r2"], k) for k in g1], (R["r2"][g1[0]] or [None] * 13)[COL["why"]]),
          [fl(R["r2"], k) for k in g1] == [0, 0, 0] and all(str(R["r2"][k][COL["why"]]).startswith("explained by a report that arrived later (first flagged 03-03 10:40; judged again ")
                                                            for k in g1) and R["r2"][g1[0]][COL["marg_move"]] == 0.0)
    check("control OLD: the three rows stay flagged after record_gaps is called again (%s)" % [fl(RO["r2"], k) for k in g1], [fl(RO["r2"], k) for k in g1] == [1, 1, 1])
    check("a second call writes nothing (rows %s, the table's checksum unchanged)" % n3["second"][0],
          n3["second"][0] == 0 and n3["second"][1] == n3["second_after"])
    check("the sale removed from the scratch spine again: nothing changes (re-judged %s; cleared stays cleared)" % n3["shrunk"],
          n3["shrunk"] == 0 and R["r3"] == R["r2"])
    check("a later W494 closing recorded by record_gaps after the clear does not carry the flag (G1@2031-03-09 flagged %s; control OLD carries it: %s)"
          % (fl(R["r4"], "W494 GAP ONE@2031-03-09"), fl(RO["r4"], "W494 GAP ONE@2031-03-09")),
          fl(R["r4"], "W494 GAP ONE@2031-03-09") == 0 and fl(RO["r4"], "W494 GAP ONE@2031-03-09") == 1)
    same = lambda pre: all(R[x][k] == R["r0"][k] for x in ("r1", "r2", "r3", "r4") for k in R["r0"] if k.startswith(pre))   # noqa: E731
    check("a first flag nothing explains stays, byte-equal (G2); a carried flag whose origin lies before the window stays, its origin too (G3, explained by the "
          "spine and untouched); an unflagged row is never flagged (G4); an approximate row is untouched (G5, flagged and explained)",
          same("W494 GAP TWO@") and same("W494 GAP THREE@") and same("W494 GAP FOUR@") and same("W494 GAP FIVE@"))
    check("with the spine absent nothing changes and nothing raises (%s)" % (n3["nospine"],), isinstance(n3["nospine"], list) and n3["nospine"][0] == 0 and n3["nospine"][2] is True)
    lv = NW.get("s3_live") or {}
    print("   the copy of the live rows (no W494), the window from %s: per closing -- first flags, carried flags, cleared by the re-judge" % lv.get("lo"))
    for d_ in sorted(set(lv.get("before") or {}) | set(lv.get("after") or {})):
        b, a_ = (lv["before"].get(d_) or [0, 0, 0]), (lv["after"].get(d_) or [0, 0, 0])
        print("      closing %s: first flags %d -> %d, carried %d -> %d (flagged %d -> %d)" % (d_, b[0], a_[0], b[1], a_[1], b[0] + b[1], a_[0] + a_[1]))
    print("   rows cleared: %s; of the first flags that remain with move > 0 (%s), a PURCHASE of the item within the seven days up to its prev whose units "
          "equal the move within one pack (a bill keyed later than its date): %s -- counted only, mended nowhere" % (lv.get("cleared"), lv.get("positive_left"), lv.get("late_keyed")))
    check("the re-judge ran on the copy of the live rows and only cleared (no closing gained a flag)",
          isinstance(lv.get("cleared"), int) and all(sum((lv["after"].get(d_) or [0, 0])[:2]) <= sum((lv["before"].get(d_) or [0, 0])[:2]) for d_ in lv.get("before") or {}))

    # ------------------------------------------------------------------------------------------------------------------------------- 4
    print("-- 4  his card (D686)")
    n4, o4 = NW["s4"], OL["s4"]
    J = n4["J"]
    VH2 = "In 2 vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye"
    VH1 = "Is vendor ka ek bill scan kijiye — poora naam aur bank details dikhne chahiye"
    VSUB = "Bill nikaal kar reception (Alisha / Shivani) se scan karwaiye."
    VA, VB = "W494 VENDOR A — bill W494-A2 (15-01-2031)", "W494 VENDOR B — bill W494-B1 (20-02-2031)"
    TAPT, TAPS = "W494 VENDOR A: ₹5 cash payment ki entry Marg mein kijiye.", "W494 ka purana balance."
    CH2, CH1 = "In 2 item ki category Marg mein ORTHOTIC kijiye", "Is item ki category Marg mein ORTHOTIC kijiye"
    CN2, LAB = "W494 ORTHO ONE · W494 ORTHO TWO", "Marg mein is category ka naam: ORTHOTICS"
    for tag in ("none", "stageA"):
        v = n4[tag]
        sp_ = v["spans"]
        check("stage %s: the card shows the heading, the vendor block (each vendor with its newest bill's number and date) and the tap line, and not the "
              "category line" % ("None" if tag == "none" else "A"),
              v["code"] == 200 and "Ek baar ke kaam" in sp_ and VH2 in sp_ and VSUB in sp_ and VA in sp_ and VB in sp_ and TAPT in sp_ and TAPS in sp_
              and CH2 not in sp_ and CH1 not in sp_ and "scan:%d" % J["va"] in v["buttons"] and "nf:%d" % J["vb"] in v["buttons"]
              and "tap:%d" % J["tap"] in v["buttons"] and "cat" not in v["buttons"], [x for x in sp_ if "W494" in x or "Ek baar" in x or "vendor" in x])
    check("control OLD: none of them (stage None, A and B)",
          all(not o4[t]["has_jobs"] and not any(("W494" in x) or x in ("Ek baar ke kaam", VH2, CH2) for x in o4[t]["spans"]) for t in ("none", "stageA", "stageB")))
    vb_ = n4["stageB"]["spans"]
    check("stage B (his rename list): the category line appears with its names, and Marg's own name of the category (%s)"
          % [x for x in vb_ if "categor" in x or "ORTHO" in x],
          CH2 in vb_ and CN2 in vb_ and LAB in vb_ and "cat" in n4["stageB"]["buttons"] and n4["state_B"]["W494:cat:1"][0] is True)
    check("the hidden row (show_from NULL) is never on the card", "W494 hidden line" not in vb_ and "tap:%d" % J["hid"] not in n4["stageB"]["buttons"])
    check("the owner's view of Amir's day says it in English: %s" % n4["owner_day"], any("one-time Marg jobs: 5 open" in x for x in n4["owner_day"]))
    check("the day closes exactly as before with jobs open: GATE_STEPS %s; the close POST gives %s, OLD %s; step 7's list %s = OLD"
          % (n4["gate"], n4["close"], o4["close"], n4["step7_before"][2]),
          n4["gate"] == o4["gate"] == [2, 4, 5, 6] and n4["close"] == o4["close"] and n4["step7_before"][2] == o4["step7_before"][2])
    check("posted from step 4: 'Kar diya' on the tap line lands (%s) and he stays on step 4; the line is gone, the row done by tap (%s)"
          % (n4["tap4"], n4["state_tap"]["W494:pay:1"]),
          n4["tap4"][0] == 303 and n4["tap4"][1].endswith("/finance/amir/step/4") and TAPT not in n4["after_tap"]["spans"]
          and n4["state_tap"]["W494:pay:1"][1:] == ["done", "amir", "tap", True])
    check("posted from step 5: 'Kar diya' on the category line lands (%s), he stays on step 5; the line is gone, the rows said" % (n4["cat5"],),
          n4["cat5"][0] == 303 and n4["cat5"][1].endswith("/finance/amir/step/5") and CH2 not in n4["after_cat"]["spans"]
          and n4["state_cat"]["W494:cat:1"][1:3] == ["done", "amir"] and n4["state_cat"]["W494:cat:2"][1:3] == ["done", "amir"])
    check("a category list received EARLIER the same day than his tap (11:00 < 12:00; as raw text it reads later) reopens nothing",
          n4["state_l1"]["W494:cat:1"][1] == "done" and CH1 not in n4["l1"]["spans"])
    check("a W494 category list received later the SAME day that still shows another category: back on his card (%s); the item absent from it stays said and "
          "the owner's line is there (%s)" % ([x for x in n4["l2"]["spans"] if "ORTHO" in x], n4["owner_l2"]),
          CH1 in n4["l2"]["spans"] and "W494 ORTHO ONE" in n4["l2"]["spans"] and n4["state_l2"]["W494:cat:1"][1] is None
          and n4["state_l2"]["W494:cat:2"][1] == "done"
          and ("W494 ORTHO TWO is not on Marg's category list of %s -- its category could not be proved" % (td - dt.timedelta(days=1)).strftime("%d-%m")) in n4["owner_l2"])
    check("one that shows the label: done, 'seen in Marg' (%s) -- a list whose export day (yesterday) is earlier than the day it was received is honoured "
          "(judged by its md5)" % (n4["state_l3"]["W494:cat:1"],),
          n4["state_l3"]["W494:cat:1"][3] == "seen in Marg" and n4["state_l3"]["W494:cat:1"][4] is True and CH1 not in n4["l3"]["spans"]
          and any("W494 ORTHO TWO is not on Marg's category list" in x for x in n4["owner_l3"]))
    check("the owner's 'not done' line: absent at 9 days (%s), one line at 11 (%s); the map's own owner line is not raised a second time (coded: %s)"
          % (n4["wait9"], n4["wait11"], n4["dutyline_wait"]),
          n4["wait9"] == [] and len(n4["wait11"]) == 1 and n4["wait11"][0].startswith("Amir's one-time Marg jobs not done: 1 -- since ")
          and n4["wait11"][0].endswith("(11 days): W494 VENDOR B") and n4["dutyline_wait"] == [])
    check("posted from step 7: 'Scan ho gaya' lands (%s), he stays on step 7; that vendor's line is gone, the other's head is singular; the owner's line: %s"
          % (n4["scan7"], n4["owner_scan"]),
          n4["scan7"][0] == 303 and n4["scan7"][1].endswith("/finance/amir/step/7") and VA not in n4["after_scan"]["spans"] and VB in n4["after_scan"]["spans"]
          and VH1 in n4["after_scan"]["spans"] and n4["owner_scan"] == ["Bank details to type for W494 VENDOR A -- Amir says its bill is scanned"])
    check("with a (non-numeric) account and IFSC on the copy the row is done, 'bank details on record', and the line is gone (%s / %s)"
          % (n4["state_bank"]["W494:vbill:A"], n4["owner_bank"]),
          n4["state_bank"]["W494:vbill:A"][3] == "bank details on record" and n4["owner_bank"] == [])
    check("'Bill nahi mila' (posted from step 6): the line is gone and the owner's 'could not find' line is there (%s)" % n4["owner_nf"],
          n4["nf6"][0] == 303 and n4["nf6"][1].endswith("/finance/amir/step/6") and VB not in n4["after_nf"]["spans"]
          and n4["owner_nf"] == ["Amir could not find a bill of W494 VENDOR B -- its bank details are still needed"])
    check("a W494 scan link: done, 'scan linked' (%s), and the owner's 'its bill is scanned' line (%s)" % (n4["state_link"].get("W494:vbill:C"), n4["owner_link"]),
          (n4["state_link"].get("W494:vbill:C") or [None] * 5)[3] == "scan linked" and n4["owner_link"] == ["Bank details to type for W494 VENDOR C -- its bill is scanned"])
    check("a job value for a row not shown, of the wrong kind, a made-up id, a non-number, a done row or a junk value changes nothing (%s)" % [x[0] for x in n4["bad_posts"]],
          n4["bad_same"] is True and all(x[0] == 303 for x in n4["bad_posts"]))
    check("each tap left one audit row (who, 'job', the row's key): %s" % n4["audit"],
          [x[2] for x in n4["audit"]] == ["W494:pay:1", "W494:cat:1", "W494:cat:2", "W494:vbill:A", "W494:vbill:B"] and all(x[0] == "amir" and x[1] == "job" for x in n4["audit"]))
    eq = [n for n in range(1, 8) if n4["noj"][str(n)] == o4["noj"][str(n)]]
    check("with no open job every step's page equals the OLD file's (steps equal: %s)" % eq, len(eq) == 7, {n: (n4["noj"][str(n)], o4["noj"][str(n)]) for n in range(1, 8)})
    check("_s494_jobs with the table broken (%s) and with it dropped: every step still renders (%s / %s)" % (n4["broken_jobs"], n4["broken"], n4["dropped"]),
          n4["broken_jobs"] == [] and all(v == 200 for v in n4["broken"].values()) and all(v == 200 for v in n4["dropped"].values()))

    # ------------------------------------------------------------------------------------------------------------------------------- 5
    print("-- 5  the duty (DUTY_MAP v9)")
    n5 = NW["s5"]
    e = n5["entry"] or {}
    check("the duty as the brief writes it: %s" % {k: e.get(k) for k in ("id", "person", "tile", "door", "door_marker", "allowed_days", "coded")},
          e.get("person") == "amir" and e.get("tile") == "Amir ka kaam" and e.get("door") == "/finance/amir/step/6" and e.get("door_marker") == "Ek baar ke kaam"
          and e.get("allowed_days") == 10 and e.get("coded") == "amir_day._s494_owner_lines" and e.get("duty_hi") == "Ek baar ke Marg ke kaam"
          and e.get("owner_line") == "Amir's one-time Marg jobs not done: {n} -- since {since} ({days} days)"
          and e.get("due_sql") == "SELECT COUNT(*) AS n, MIN(substr(show_from,1,10)) AS since FROM amir_job WHERE done_at IS NULL AND said_at IS NULL AND show_from IS NOT NULL")
    check("due_sql on the copy: %s on the empty table; two shown open of five W494 rows -> %s; all said -> %s" % (n5["due0"], n5["due1"], n5["due2"]),
          n5["due0"] == [0, None] and n5["due1"] == [2, "2031-01-05"] and n5["due2"] == [0, None])
    check("control: with the v8 map the duty is absent", NEW_ID not in [d["id"] for d in m8["duties"]])
    check("the v9 map loads in aaj_kaam.load_defs (%s) and in owner_console's reader (%s) without an error" % (n5["load_defs"].get("v9"), n5["console"]),
          n5["load_defs"]["v9"][0] is None and n5["load_defs"]["v9"][1] == 9 and isinstance(n5["console"], list) and n5["console"][0] == 9
          and n5["console"][1].get(NEW_ID) == [0, None])
    others = [lg for lg in LOGINS if lg != "amir"]
    check("for every login but amir (%s) the list cut with the v8 map and with the v9 map is identical" % ", ".join(others),
          all(n5["cuts_equal"][lg] for lg in others), n5["cuts_equal"])
    print("   amir's own /finance/aaj list (his panel, aaj_seed -- the clinic's file): identical under v8 and v9: %s -- the new duty has no line in the seed (a finding)"
          % n5["cuts_equal"]["amir"])
    print("   the console's items, v9 only: %s; v8 only: %s" % ([x for x in n5["items_v9_only"] if x[1]], [x for x in n5["items_v8_only"] if x[1]]))

    # ------------------------------------------------------------------------------------------------------------------------------- 6
    print("-- 6  staff-eye (D648): amir, darpan, shavez, reception and the owner, signed in on scratch copies (a walk-only store and secret)")
    EN, EO = run("eye", "new", a.fin_new), run("eye", "old", a.fin_old)
    if not check("both staff-eye probes ran to the end (NEW: seeded, refreshed and re-judged on its own copy as the install and the first tick will; OLD: the copy as it is)",
                 EN is not None and EO is not None):
        return finish()
    print("   NEW seed %s; refresh %s; re-judge %s rows; the jobs: %s" % (EN["seed"], EN["refresh"], EN["rejudge"], EN["jobs"]))
    check("the duty's due_sql after the seed and one refresh: %s (expected 3, today: the two vendors and the Kedar entry; AGARWAL closed by its linked scan)" % (EN["due"],),
          EN["due"] == [3, td.isoformat()])
    ALLOW_WHO = {("amir", "/finance/amir"): "his card: the jobs", ("amir", "/finance/aaj"): "his own Aaj line",
                 ("manoj", "/finance/approvals"): "Needs-you: the spot line once; the shelf-gap count; the lines of 4.6",
                 ("manoj", "/finance/sanjeevni/api/needs-you"): "Needs-you (the same, as JSON)",
                 ("manoj", "/finance/amir/day"): "_s446_left's line; the visit summary", ("manoj", "/finance/console"): "the by-person block: the new duty under Amir",
                 ("manoj", "/finance/aaj"): "the console's own list", ("darpan", "/finance/stockmatch"): "the spot-count roster: fewer flagged reasons"}
    for n in range(1, 8):
        ALLOW_WHO[("amir", "/finance/amir/step/%d" % n)] = "his card on step %d: the jobs" % n
    en, eo = EN["eye"], EO["eye"]
    for who in USERS:
        n, o = en[who], eo[who]
        diff = sorted(k for k in set(n["pages"]) | set(o["pages"]) if n["pages"].get(k) != o["pages"].get(k))
        allowed = {p: why for (w_, p), why in ALLOW_WHO.items() if w_ == who}
        unexplained = [d for d in diff if d not in allowed]
        check("%s: signs in (%s), %d tiles; %d pages compared NEW vs OLD; differences: %s"
              % (who, n["status"], n["n_tiles"], len(n["pages"]), ["%s (%s)" % (d, allowed.get(d, "NOT EXPLAINED")) for d in diff] or "none"),
              n["status"] == 200 and n["n_tiles"] == o["n_tiles"] and not unexplained and n["pages"].get("home") == o["pages"].get("home"), unexplained)

        def misses(side):
            due_ = [r for r in side["duties"] if isinstance(r.get("due_n"), int) and r["due_n"] > 0 and r.get("door")]
            return due_, sorted(r["id"] for r in due_ if (r.get("tile") and r.get("tile_seen") is False) or r.get("door_seen") is False)
        due, miss = misses(n)
        _d, miss_o = misses(o)
        errs = [r["id"] for r in n["duties"] if isinstance(r.get("due_n"), str)]
        before = [m for m in miss if m in miss_o]
        if before:
            NOTES.append("%s: due but not visible on either side (before this kit too): %s" % (who, before))
        check("   %s: %d duties in the map, %d due now -- each due one visible (its tile on the home, its marker on its door) as on the OLD side%s"
              % (who, len(n["duties"]), len(due), ("; NOT visible on either side, before this kit too: %s (a finding)" % before) if before else ""),
              not [m for m in miss if m not in miss_o] and not errs, (miss, miss_o, errs))
    aj = [r for r in en["amir"]["duties"] if r["id"] == NEW_ID]
    check("Amir's home shows the tile (%s) and step 6 shows 'Ek baar ke kaam' while the duty is due (%s; due %s)"
          % (aj[0].get("tile_seen") if aj else None, aj[0].get("door_seen") if aj else None, aj[0].get("due_n") if aj else None),
          bool(aj) and aj[0].get("tile_seen") is True and aj[0].get("door_seen") is True and aj[0].get("due_n") == 3)
    s6 = en["amir"]["texts"].get("/finance/amir/step/6") or []
    print("   Amir's step 6, the jobs as he sees them: %s" % [x for x in s6 if x in ("Ek baar ke kaam",) or "vendor" in x or "bill" in x.lower() or "KEDAR" in x or "July" in x][:12])
    print("   the owner's view of Amir's day, NEW: %s" % [x for x in (en["manoj"]["texts"].get("/finance/amir/day") or []) if "one-time" in x])
    ny_n, ny_o = en["_needs_you"], eo["_needs_you"]
    if isinstance(ny_n, list) and isinstance(ny_o, list):
        print("   the owner's Needs-you, NEW only: %s" % [x for x in ny_n if x not in ny_o])
        print("   the owner's Needs-you, OLD only: %s" % [x for x in ny_o if x not in ny_n])
    print("   Darpan's spot-count roster reads the shelf-gap flags at the newest closing: %s (OLD) -> %s (NEW)" % (EO["gap_flags"], EN["gap_flags"]))
    for x in NOTES:
        print("   FINDING (not this kit's): %s" % x)
    return finish()


def finish():
    if FAILS:
        print("WALK_S494 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:200])
        return 1
    print("WALK_S494 GREEN -- %d checks" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
