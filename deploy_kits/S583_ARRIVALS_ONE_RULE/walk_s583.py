#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s583.py -- kit S583_ARRIVALS_ONE_RULE (18-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s583.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --map <DUTY_MAP.json>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s583.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --map ...   (the install-day state)
The real finance app in one process (the walk's own header session; never the live secret). Its own rows by key (W583 ...), never by
counting; the live rows by key. No phone number is printed (a run of ten digits is masked). The sections follow the brief's section 4:
  0  print first: every scan-tied unanswered line and every tapped line not answered, with what (a)-(e) say; the 13 items of REPORT_S580
     with shelf() as the files under test read them; Darpan's receipt state (expect_for_point) for each; the reach and the two settings
  1  TOLTRIS PLUS: counted inside the grace (grace raised on the copy), EXPIRED under the live grace (the 18-10 09:27 export), on the owner's line
  2  CROCAL / PREGHYPE carried by (c); 3 PRETOL 8 carried by (e); 4 an order-32-style line (both A.A. bills answer other lines) NOT carried
  5  the raw-stamp trap goes red; a tap inside its grace still counts (the walk's own tapped line W583 FIX TAB)
  6  the order engine: a counted item with a scan-tied line inside its grace equal before and after; the expired ones' change printed
  7  a Marg-answered row is never counted and never on the owner's line
  8  spine missing: carried() None, expired() False, the arrivals keep counting
  9  the owner's lines: no overlap with D712's; bill_pending_lines equal before and after, every live line
 10  Darpan's receipt for an item whose arrival expired (write_point on the copy): judged at once, the existing words
 11  the grep tests: no scan_arrivals in shelf_figure; no supplier-key test in _arrivals / bill_pending_lines; one carried rule
 12  the 13 items old -> new; the voucher guard's not-judged count old -> new; staff screens' words against --old-dump; no ten-digit run
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control). Prints 'WALK OK S583 ...' on success."""
import argparse
import datetime as dt
import html as _html
import json
import os
import re
import secrets
import sqlite3
import sys
import time

KIT = "S583_ARRIVALS_ONE_RULE"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
FIX = "W583 FIX TAB"                                           # the walk's own tapped line (a vendor of its own, no spine purchase)
FIXV = "W583 FIX VENDOR"
ITEMS = ["TOLTRIS PLUS", "CROCAL", "FLACORT 6", "PREGHYPE NT TAB", "PRETOL 8", "THIO Q AP", "LINVIZ 600", "COCYP T SYP", "POWERGESIC 100 PATCH",
         "FINGER COT M", "SOFT COLLAR NEOLIFE L", "SHOULDER IMMOBILISE UNISON L", "SHOULDER IMMOBILISE UNISON M"]      # REPORT_S580 section 4
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:500] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def section(title, fn):
    say("-- %s" % title)
    try:
        fn()
    except Exception as e:                                     # noqa: BLE001
        import traceback
        check("C: section %s ran without an exception" % title, False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-600:]))


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def fn_body(src, name):
    m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|# -{10,}|[A-Z_]+ = ))" % re.escape(name), src, flags=re.S | re.M)
    return m.group(0) if m else ""


def app_env(a, dbp, token):
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB"):
        os.environ.pop(k, None)


def rule_words(SF, con, sp, line, ctx):
    """What (a)-(e) say of one line, in words, on the files under test (old files: no carried -> 'no rule')."""
    if not hasattr(SF, "carried"):
        return "no rule (old files)"
    c = SF.carried(con, sp, line, ctx)
    e = SF.expired(con, sp, line, ctx)
    if c:
        return "carried by (%s): %s bill %s of %s%s" % (c["how"], c.get("supplier") or c.get("supkey"), c["bill"], c["date"], (" %g units" % c["units"]) if c.get("units") is not None else "")
    return "not carried; %s" % ("EXPIRED (the reach passed it + grace)" if e else "inside its grace -> counts")


def dmhm(s):
    s = str(s or "")
    return "%s-%s %s" % (s[8:10], s[5:7], s[11:16]) if len(s) >= 16 else s[:10]


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    """The arrivals' state by the files in --fin on a copy of the live database (the live files before placing, the placed ones after)."""
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    SA.ensure_schema(con)
    sp = SW.Spine()
    ctx = SF.Ctx(con, sp)
    R = SF.reach(sp)
    new = hasattr(SF, "carried")
    say("STATE %s: files %s; spine ok %s; reach last_pur %s taken %s; grace %s back %s" % (label, "NEW (carried / expired)" if new else "OLD (supplier + date rule)", sp.ok, R.get("last_pur"),
        SF.stamp_iso(R.get("pur_stamp")), SW.settings(con)["bill_grace_days"], SW.settings(con).get("back_days", "-")))
    fig = {}
    for it in ITEMS:
        S = SF.shelf(con, sp, it, None, ctx)
        E = SF.expect_for_point(con, sp, it, ctx)
        fig[it] = dict(arrived=S.get("arrived"), shelf=S.get("shelf"), named=S.get("named"), basis=E.get("basis"), provisional=E.get("provisional"))
        say("   %-30s arrived %6s  shelf %6s  %-10s receipt basis %-6s provisional %s" % (it, S.get("arrived"), S.get("shelf"), S.get("named") or "", E.get("basis"), E.get("provisional")))
    opn = SF.arrivals_open(con, sp, ctx) if new else []
    say("STATE %s: arrivals_open (expired, not carried): %d" % (label, len(opn)))
    for x in opn:
        say("   %-30s %6g  %s  %s  %s  order %s%s" % (x["item"], x["units"], dmhm(x["at"]), x["who"], x["vendor"], x["order_id"], "" if x["scan_tied"] else "  (untied: D712's)"))
    lines = SW.arrival_needs_you(con, sp) if new else []
    say("STATE %s: the owner's arrival lines on Needs-you: %d" % (label, len(lines)))
    for l in lines:
        say("   %s" % l["text"])
    bp = SW.bill_pending_lines(con, sp=sp)
    say("STATE %s: Amir's 'bill entry baaki' lines: %d %s" % (label, len(bp), [(x["item"], x["vendor"], x["date"]) for x in bp]))
    st = SA.amir_stage(con, 1) or {}
    A, C = st.get("A") or {}, st.get("C") or {}
    say("STATE %s: the voucher guard -- A not judged against the shelf: %s, held %d; C not judged: %s, held %d" % (label, A.get("not_shelf", "-"), len(A.get("held") or []), C.get("not_shelf", "-"), len(C.get("held") or [])))
    json.dump(dict(label=label, figures=fig, open=[(x["item"], x["units"], x["at"]) for x in opn], owner=[l["text"] for l in lines], bill_pending=[(x["item"], x["vendor"], x["date"]) for x in bp],
                   not_shelf=[A.get("not_shelf"), C.get("not_shelf")]), open(os.path.join(os.path.dirname(dbp), "state_%s.json" % label), "w"))
    con.rollback()
    say("STATE OK S583 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S583_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S583 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import shelf_figure as SH                                 # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    import amir_day as AD                                     # noqa: E402
    for m in (SA, SW, SH, SF, OR, PA, AD):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(SF, "carried")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure v%s (%s)" % ([n for n, _w in fa._MOUNT_FAILED] or "none", SF.VERSION, "carried / expired present" if NEW else "OLD: no carried"))
    cl = fa.app.test_client(use_cookies=False)
    TIMES = []
    DUMP = {}

    def GET(u, path, follow=False):
        t0 = time.time()
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=follow)
        TIMES.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    SA.ensure_schema(sqlite3.connect(dbp))
    spine_path = os.path.join(fin, "spine", "spine.db")
    sp = SW.Spine()
    assert sp.ok and SW.SPINE_DB == spine_path, (sp.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    today = dt.date.today()
    R = SF.reach(sp)
    GRACE = SW.settings(sqlite3.connect(dbp))["bill_grace_days"]

    def fresh():
        return SF.Ctx(conn(), sp)

    def scan_rows(c):
        return [dict(r) for r in c.execute("SELECT l.id AS line_id, l.item, l.packs, l.pack_size, o.vendor, o.created_at AS order_at, o.id AS order_id, t.scan_at, "
                                           "t.scan_at AS arrived_at, '' AS billed_bill_no, 'scan' AS kind FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                           "JOIN order_scan_tie t ON t.order_id=o.id WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0 "
                                           "ORDER BY t.scan_at, l.id")]

    def tap_rows(c, answered):
        return [dict(r) for r in c.execute("SELECT l.id AS line_id, l.item, l.supplied, l.pack_size, l.arrived_at, l.arrived_by, l.billed_bill_no, l.billed_date, o.vendor, "
                                           "o.created_at AS order_at, o.id AS order_id, 'tap' AS kind FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                                           "WHERE l.arrived_at IS NOT NULL AND l.supplied>0 AND COALESCE(l.billed_bill_no,'')%s'' ORDER BY l.arrived_at, l.id" % ("<>" if answered else "="))]

    # ============================================================================================ 0 print first
    def s0():
        c = conn()
        ctx = SF.Ctx(c, sp)
        say("   today %s; the spine's reach: last_pur %s, pur_stamp %s -> %s; last_sale %s" % (today, R.get("last_pur"), R.get("pur_stamp"), SF.stamp_iso(R.get("pur_stamp")), R.get("last_sale")))
        S_ = SW.settings(c)
        say("   settings: arrival.bill_grace_days %s (raw %r); arrival.back_days %s (raw %r; the new setting reads its default, no row written)"
            % (S_["bill_grace_days"], S_["raw"].get("arrival.bill_grace_days"), S_.get("back_days", "-"), S_["raw"].get("arrival.back_days")))
        check("the setting arrival.back_days has no row in the copy of the live database (seed=None)", c.execute("SELECT COUNT(*) FROM setting WHERE key='arrival.back_days'").fetchone()[0] == 0)
        scans = scan_rows(c)
        say("   scan-tied unanswered lines: %d" % len(scans))
        for r in scans:
            say("     line %-4s %-30s %4s x %-3s order %-3s %-28s created %s scanned %s -> %s" % (r["line_id"], r["item"], r["packs"], r["pack_size"], r["order_id"], r["vendor"][:28], dmhm(r["order_at"]), dmhm(r["scan_at"]), rule_words(SF, c, sp, r, ctx)))
        taps = tap_rows(c, False)
        say("   tapped lines not answered by Marg (no billed_bill_no): %d" % len(taps))
        for r in taps:
            say("     line %-4s %-30s %4s x %-3s order %-3s %-28s tapped %s by %s -> %s" % (r["line_id"], r["item"], r["supplied"], r["pack_size"], r["order_id"], r["vendor"][:28], dmhm(r["arrived_at"]), r["arrived_by"], rule_words(SF, c, sp, r, ctx)))
        ans = tap_rows(c, True)
        say("   tapped lines ANSWERED by Marg (billed_bill_no set; rule a): %d -- never counted, never on the owner's line" % len(ans))
        say("   the 13 items of REPORT_S580 as the files under test read them (shelf(): arrived / shelf; expect_for_point: basis / provisional):")
        fig = {}
        for it in ITEMS:
            S = SF.shelf(c, sp, it, None, ctx)
            E = SF.expect_for_point(c, sp, it, ctx)
            fig[it] = dict(arrived=S.get("arrived"), shelf=S.get("shelf"), named=S.get("named"), base_day=S.get("base_day"), basis=E.get("basis"), provisional=E.get("provisional"), expected=E.get("expected"))
            say("     %-30s arrived %6s  shelf %6s %-11s base %s  receipt: basis %-6s provisional %s expected %s" % (it, S.get("arrived"), S.get("shelf"), S.get("named") or "", S.get("base_day"), E.get("basis"), E.get("provisional"), E.get("expected")))
        DUMP["figures"] = fig
        # the named edge: a carrying bill dated on or before the item's count day (the goods are inside the count; carried() still drops the arrival)
        if NEW:
            edge = []
            for r in scans + taps:
                cd = SF.carried(c, sp, r, ctx)
                S = SF.shelf(c, sp, r["item"], None, ctx)
                if cd and S.get("base_day") and cd.get("date") and cd["date"] <= S["base_day"]:
                    edge.append("%s (line %s): bill %s of %s, count day %s" % (r["item"], r["line_id"], cd["bill"], cd["date"], S["base_day"]))
            say("   the named edge -- a carrying bill dated on or before the count day (dropped, rightly: the goods are in the count): %d %s" % (len(edge), edge))
        c.close()
    section("0  print first: every line and what (a)-(e) say; the 13 items", s0)

    # ---- the walk's own rows on the finance copy: a tapped line inside its grace (W583 FIX TAB) and an order-32-style scan-tied line ------------
    FXI = {}

    def fixture():
        c = conn()
        if not c.execute("SELECT 1 FROM purchase_order WHERE vendor=?", (FIXV,)).fetchone():
            oid = ins(c, "purchase_order", dict(vendor=FIXV, created_at=dt.datetime.now().replace(microsecond=0, hour=8, minute=0, second=0).isoformat(), status="received"))
            ins(c, "purchase_order_line", dict(order_id=oid, item=FIX, packs=2, pack_size=10, supplied=2, arrived_at=dt.datetime.now().replace(microsecond=0).isoformat(), arrived_by="w583walk"))
            c.commit()
        r = c.execute("SELECT l.id, l.arrived_at, o.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.item=? AND o.vendor=?", (FIX, FIXV)).fetchone()
        FXI["tap"] = dict(line_id=r[0], item=FIX, vendor=FIXV, order_at=c.execute("SELECT created_at FROM purchase_order WHERE id=?", (r[2],)).fetchone()[0], arrived_at=r[1], billed_bill_no="", kind="tap")
        # an order-32-style line: a third A.A. order of RYCOBAL D3, scan-tied 17-10 18:22, unanswered -- both A.A. bills (467, 474) answered OTHER lines of the key
        o32 = c.execute("SELECT o.vendor, l.pack_size FROM purchase_order o JOIN purchase_order_line l ON l.order_id=o.id WHERE o.id=32 AND l.item='RYCOBAL D3'").fetchone()
        if o32 and not c.execute("SELECT 1 FROM purchase_order WHERE vendor=? AND created_at='2026-10-16T13:32:59'", (o32[0],)).fetchone():
            oid = ins(c, "purchase_order", dict(vendor=o32[0], created_at="2026-10-16T13:32:59", status="received"))
            ins(c, "purchase_order_line", dict(order_id=oid, item="RYCOBAL D3", packs=10, pack_size=int(o32[1] or 10)))
            ins(c, "order_scan_tie", dict(order_id=oid, scan_at="2026-10-17T18:22:00", tied_at="2026-10-17T18:22:00", how="w583walk", arrived=1))
            c.commit()
        if o32:
            r = c.execute("SELECT l.id, o.id, o.created_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE o.vendor=? AND o.created_at='2026-10-16T13:32:59'", (o32[0],)).fetchone()
            FXI["o32"] = dict(line_id=r[0], item="RYCOBAL D3", vendor=o32[0], order_at=r[2], arrived_at="2026-10-17T18:22:00", scan_at="2026-10-17T18:22:00", billed_bill_no="", order_id=r[1], kind="scan")
        c.close()
    fixture()

    # ============================================================================================ 1 TOLTRIS PLUS
    def s1():
        c = conn()
        ctx = SF.Ctx(c, sp)
        row = [r for r in scan_rows(c) if r["item"] == "TOLTRIS PLUS"]
        check("the live TOLTRIS PLUS scan-tied line is there (order 28, scanned 14-10 12:46, 50 x 10)", bool(row) and row[0]["order_id"] == 28 and str(row[0]["scan_at"]).startswith("2026-10-14T12:46"), row)
        line = row[0] if row else {}
        due = (dt.datetime.fromisoformat(line["scan_at"][:19]) + dt.timedelta(days=GRACE)).isoformat() if line else None
        say("   TOLTRIS PLUS: scanned %s + grace %d d = %s; the spine's purchase export taken %s reaches %s -> %s" % (dmhm(line.get("scan_at")), GRACE, due, SF.stamp_iso(R.get("pur_stamp")), R.get("last_pur"),
            "PAST it (the 18-10 09:27 export: expired)" if (due and SF.stamp_iso(R.get("pur_stamp")) > due and R.get("last_pur", "") >= due[:10]) else "not past it yet"))
        check("C: carried() is None for TOLTRIS PLUS (no TOLTRIS purchase in the spine from %s on)" % (dt.date.fromisoformat(line["order_at"][:10]) - dt.timedelta(days=2)).isoformat() if line else "-",
              NEW and line and SF.carried(c, sp, line, ctx) is None)
        check("C: expired() is True for TOLTRIS PLUS under the live grace (%d days): the export of %s is past 14-10 12:46 + grace" % (GRACE, SF.stamp_iso(R.get("pur_stamp"))), NEW and line and SF.expired(c, sp, line, ctx) is True)
        sa_ = SF.scan_arrivals(c, sp, "TOLTRIS PLUS", "2026-09-01", ctx) if NEW else SH.scan_arrivals(c, sp, "TOLTRIS PLUS", "2026-09-01", ctx=ctx)
        S = SF.shelf(c, sp, "TOLTRIS PLUS", None, ctx)
        check("C: TOLTRIS PLUS leaves the shelf: scan_arrivals 0 and shelf()['arrived'] 0 (was 500)", sa_ == 0 and float(S.get("arrived") or 0) == 0, (sa_, S.get("arrived"), S.get("shelf")))
        lines = SW.arrival_needs_you(c, sp) if NEW else []
        mine = [l["text"] for l in lines if l["text"].startswith("TOLTRIS PLUS:")]
        check("C: TOLTRIS PLUS is on the owner's Needs-you with the brief's words", bool(mine) and "counted as arrived when the SHIVAAZ FORMULATIONS bill was scanned 14-10 12:46" in mine[0] and "not in Marg's purchases up to %s" % SW.dmy(R.get("last_pur"))[:5] in mine[0], mine)
        for l in mine:
            say("   %s" % l)
        # inside the grace: the same line counts (the grace raised to 30 days on the COPY, then put back)
        prev = c.execute("SELECT value FROM setting WHERE key='arrival.bill_grace_days'").fetchone()
        if prev:
            c.execute("UPDATE setting SET value='30' WHERE key='arrival.bill_grace_days'")
            c.commit()
            ctx2 = SF.Ctx(c, sp)
            sa2 = SF.scan_arrivals(c, sp, "TOLTRIS PLUS", "2026-09-01", ctx2) if NEW else SH.scan_arrivals(c, sp, "TOLTRIS PLUS", "2026-09-01", ctx=ctx2)
            e2 = SF.expired(c, sp, line, ctx2) if NEW else None
            S2 = SF.shelf(c, sp, "TOLTRIS PLUS", None, ctx2)
            c.execute("UPDATE setting SET value=? WHERE key='arrival.bill_grace_days'", (prev[0],))
            c.commit()
            check("inside the grace (30 days on the copy): TOLTRIS PLUS counts 500 (scan_arrivals), shelf arrived 500, expired() False", sa2 == 500 and float(S2.get("arrived") or 0) == 500 and (e2 is False or not NEW), (sa2, S2.get("arrived"), e2))
            check("the grace setting on the copy is back to its value (%s)" % prev[0], c.execute("SELECT value FROM setting WHERE key='arrival.bill_grace_days'").fetchone()[0] == prev[0])
        else:
            say("   (no arrival.bill_grace_days row on this copy: the inside-the-grace read is skipped)")
        c.close()
    section("1  TOLTRIS PLUS: inside the grace counted, expired under the live export, on the owner's line", s1)

    # ============================================================================================ 2-3-4 the rules (c), (e) and (b)
    def s2():
        c = conn()
        ctx = SF.Ctx(c, sp)
        byname = {r["item"]: r for r in scan_rows(c)}
        for it, bill in (("CROCAL", "3463"), ("PREGHYPE NT TAB", "3463")):
            r = byname.get(it)
            cd = SF.carried(c, sp, r, ctx) if (NEW and r) else None
            check("C: %s (order 10 Shivaaz of 02-10) is carried by rule (c): Shivaaz bill %s of 01-10, one day before the order" % (it, bill), bool(cd) and cd["how"] == "c" and cd["bill"].strip() == bill and cd["date"] == "2026-10-01", cd)
            S = SF.shelf(c, sp, it, None, ctx)
            check("C: %s shelf()['arrived'] is 0 (was %s)" % (it, {"CROCAL": 300, "PREGHYPE NT TAB": 200}[it]), float(S.get("arrived") or 0) == 0, S.get("arrived"))
        r = byname.get("PRETOL 8")
        cd = SF.carried(c, sp, r, ctx) if (NEW and r) else None
        check("C: PRETOL 8 (ordered from Shivaaz 02-10) is carried by rule (e): Kedar's bill A000203 of 03-10, another supplier, on/after the order day", bool(cd) and cd["how"] == "e" and "A000203" in cd["bill"] and cd["date"] == "2026-10-03", cd)
        S = SF.shelf(c, sp, "PRETOL 8", None, ctx)
        check("C: PRETOL 8 shelf()['arrived'] is 0 (was 100)", float(S.get("arrived") or 0) == 0, S.get("arrived"))
        r = byname.get("POWERGESIC 100 PATCH")
        cd = SF.carried(c, sp, r, ctx) if (NEW and r) else None
        check("C: POWERGESIC 100 PATCH (ordered from Deepam 16-10) is carried by rule (e): Janta's bill 23672 of 18-10", bool(cd) and cd["how"] == "e" and "23672" in cd["bill"], cd)
        # (b): the order-32-style line -- both A.A. bills of RYCOBAL D3 answered OTHER lines (467 -> order 21, 474 -> order 32)
        o32 = FXI.get("o32")
        check("the walk's order-32-style line is on the copy (RYCOBAL D3, A.A., created 16-10, scan-tied 17-10 18:22, unanswered)", bool(o32), o32)
        k = SF.key_of(sp, "RYCOBAL D3", ctx)
        bills = [dict(x) for x in sp.q("SELECT bill, date, supkey, SUM(units) AS u FROM sp_purchase_line WHERE k20=? AND date>='2026-10-01' GROUP BY bill, date, supkey ORDER BY date", k)]
        say("   RYCOBAL D3 (key %s): the spine's bills since 01-10: %s" % (k, [(b["bill"], b["date"], b["supkey"], b["u"]) for b in bills]))
        taken = [tuple(x) for x in c.execute("SELECT l.id, l.order_id, l.billed_bill_no FROM purchase_order_line l WHERE l.item='RYCOBAL D3' AND COALESCE(l.billed_bill_no,'')<>'' ORDER BY l.id")]
        say("   RYCOBAL D3 order lines answered by Marg (line, order, bill): %s" % taken)
        seven = [b for b in bills if b["date"] >= (dt.date.fromisoformat(o32["order_at"][:10]) - dt.timedelta(days=7)).isoformat()] if o32 else []
        say("   a 7-day any-supplier rule would carry it by: %s" % [(b["bill"], b["date"]) for b in seven])
        cd = SF.carried(c, sp, o32, ctx) if (NEW and o32) else None
        check("C: rule (b): the order-32-style line is NOT carried -- 467 answered order 21's lines, 474 order 32's (a 7-day any-supplier rule goes red: it would take 467)",
              NEW and bool(o32) and cd is None and bool(seven) and any(str(b["bill"]).strip().lstrip("0") == "467" for b in seven), (cd, seven))
        if NEW and o32:
            say("   ... and it is %s (scanned 17-10 18:22 + %d days)" % ("EXPIRED" if SF.expired(c, sp, o32, ctx) else "inside its grace: it counts for now", GRACE))
        c.close()
    section("2-4 the rules: CROCAL / PREGHYPE by (c), PRETOL 8 and POWERGESIC by (e), the order-32-style line not carried (b)", s2)

    # ============================================================================================ 5 the raw-stamp trap; a tap inside its grace
    def s5():
        c = conn()
        ctx = SF.Ctx(c, sp)
        t = FXI["tap"]
        raw_wrong = str(R.get("pur_stamp")) > str(t["arrived_at"])         # 'YYYYMMDD-HHMMSS' against ISO: '2026...-...' > '2026-...' is always True
        say("   the walk's own tapped line %s (vendor %s, tapped %s, 2 x 10): raw compare pur_stamp %r > arrived_at %r = %s (the trap says 'passed')" % (FIX, FIXV, dmhm(t["arrived_at"]), R.get("pur_stamp"), t["arrived_at"], raw_wrong))
        e = SF.expired(c, sp, t, ctx) if NEW else None
        check("C: the raw-stamp compare would call the fresh tap passed (%s) -- expired() reads ISO against ISO and says False" % raw_wrong, NEW and raw_wrong and e is False, e)
        check("C: a tap inside its grace still counts: carried() None, taps() 20 units for %s" % FIX, NEW and SF.carried(c, sp, t, ctx) is None and SF.taps(c, sp, FIX, "2026-01-01", ctx) == 20.0, (SF.taps(c, sp, FIX, "2026-01-01", ctx)))
        arr = SW._arrivals(c, FIX, "2026-01-01", sp, ctx=ctx)
        check("_arrivals lists the walk's tap once, in_spine False, with scan_at '' (untied) and billed_bill_no ''", len(arr) == 1 and arr[0]["in_spine"] is False and arr[0].get("billed_bill_no") == "" and (not NEW or arr[0].get("scan_at") == ""), arr)
        c.close()
    section("5  the raw-stamp trap goes red; a tap inside its grace counts", s5)

    # ============================================================================================ 6 the order engine
    def s6():
        c = conn()
        ctx = SF.Ctx(c, sp)
        basis = OR._s454_basis(c)
        say("   order.stock_basis = %s" % basis)
        t0 = time.time()
        as_on, snap, pace, purch, transit, ortho = OR._s470_inputs(c, today)
        say("   _s470_inputs in %.1f s: %d items in the snapshot, as on %s; %d in transit" % (time.time() - t0, len(snap), as_on, len(transit)))
        eng = {}
        for it in ITEMS + ["RYCOBAL D3"]:
            k = PA.norm(it)
            s = snap.get(k) or {}
            eng[it] = dict(qty=s.get("qty"), marg_qty=s.get("marg_qty"), transit=(transit.get(k) or {}).get("units"))
            say("     %-30s engine qty %6s  marg_qty %6s  transit %s" % (it, s.get("qty"), s.get("marg_qty"), (transit.get(k) or {}).get("units")))
        DUMP["engine"] = eng
        o = OLD.get("engine") or {}
        if o:
            for it in ITEMS:
                if o.get(it, {}).get("qty") != eng[it]["qty"]:
                    say("   CHANGED on the ordering pages: %-30s %s -> %s" % (it, o[it]["qty"], eng[it]["qty"]))
        lin = [r for r in scan_rows(c) if r["item"] == "LINVIZ 600"]
        inside = bool(lin) and NEW and SF.carried(c, sp, lin[0], ctx) is None and not SF.expired(c, sp, lin[0], ctx)
        say("   LINVIZ 600 (order 38 Kedar, scanned 17-10 18:18): %s" % (rule_words(SF, c, sp, lin[0], ctx) if lin else "no line"))
        check("C: the order engine's quantity for a counted item with a genuine scan-tied line INSIDE its grace (LINVIZ 600) is equal before and after (%s -> %s)" % (o.get("LINVIZ 600", {}).get("qty"), eng["LINVIZ 600"]["qty"]),
              bool(o) and inside and o.get("LINVIZ 600", {}).get("qty") == eng["LINVIZ 600"]["qty"] and eng["LINVIZ 600"]["qty"] is not None)
        check("C: the order engine's quantity for TOLTRIS PLUS (expired) moves by -500 (%s -> %s)" % (o.get("TOLTRIS PLUS", {}).get("qty"), eng["TOLTRIS PLUS"]["qty"]),
              bool(o) and o.get("TOLTRIS PLUS", {}).get("qty") is not None and eng["TOLTRIS PLUS"]["qty"] is not None and o["TOLTRIS PLUS"]["qty"] - eng["TOLTRIS PLUS"]["qty"] == 500)
        c.close()
    section("6  the order engine (R1-B1): equal for a line inside its grace; the expired ones printed", s6)

    # ============================================================================================ 7 a Marg-answered row
    def s7():
        c = conn()
        ctx = SF.Ctx(c, sp)
        ans = tap_rows(c, True)
        r = [x for x in ans if x["item"] == "RYCOBAL D3" and str(x["billed_bill_no"]).strip() == "467"]
        r = r[0] if r else (ans[0] if ans else None)
        check("a Marg-answered row is on the copy (arrived_by %s, bill %s)" % ((r or {}).get("arrived_by"), (r or {}).get("billed_bill_no")), bool(r), r)
        cd = SF.carried(c, sp, r, ctx) if (NEW and r) else None
        check("C: carried() answers it by rule (a): its own billed_bill_no", bool(cd) and cd["how"] == "a" and cd["bill"].strip() == str(r["billed_bill_no"]).strip(), cd)
        arr = [x for x in SW._arrivals(c, r["item"], "2026-01-01", sp, ctx=ctx) if x["line_id"] == r["line_id"]] if r else []
        check("_arrivals marks it in_spine True", bool(arr) and arr[0]["in_spine"] is True, arr)
        opn = SF.arrivals_open(c, sp, ctx) if NEW else None
        check("C: it is not in arrivals_open and not on the owner's line", NEW and r and all(x["line_id"] != r["line_id"] for x in opn) and not any(l["text"].startswith(r["item"] + ":") and "tapped it" in l["text"] for l in SW.arrival_needs_you(c, sp)))
        c.close()
    section("7  a Marg-answered row is never counted, never on the owner's line", s7)

    # ============================================================================================ 8 spine missing
    def s8():
        c = conn()
        sp0 = SW.Spine(os.path.join(fin, "spine", "no_such_spine.db"))
        check("a Spine on a missing file has ok=False", sp0.ok is False)
        ctx0 = SF.Ctx(c, sp0)
        t = FXI["tap"]
        check("C: spine missing: carried() None, expired() False", NEW and SF.carried(c, sp0, t, ctx0) is None and SF.expired(c, sp0, t, ctx0) is False)
        check("spine missing: the arrivals keep counting -- taps() 20 for %s" % FIX, SF.taps(c, sp0, FIX, "2026-01-01", ctx0) == 20.0, SF.taps(c, sp0, FIX, "2026-01-01", ctx0))
        sa_ = SF.scan_arrivals(c, sp0, "TOLTRIS PLUS", "2026-09-01", ctx0) if NEW else SH.scan_arrivals(c, sp0, "TOLTRIS PLUS", "2026-09-01", ctx=ctx0)
        check("spine missing: TOLTRIS PLUS's scan line keeps counting (500) -- nothing is dropped while the spine is unread (charter 1b)", sa_ == 500.0, sa_)
        c.close()
    section("8  spine missing: nothing dropped", s8)

    # ============================================================================================ 9 the owner's lines and Amir's
    def s9():
        c = conn()
        bp = SW.bill_pending_lines(c, sp=sp)
        DUMP["bill_pending"] = [(x["item"], x["vendor"], x["date"], x["text_hi"]) for x in bp]
        say("   bill_pending_lines (Amir's 'bill entry baaki'): %d %s" % (len(bp), DUMP["bill_pending"]))
        if "bill_pending" in OLD:
            check("bill_pending_lines is equal before and after for every live line (%d lines)" % len(bp), [list(x) for x in DUMP["bill_pending"]] == [list(x) for x in OLD["bill_pending"]], (OLD["bill_pending"], DUMP["bill_pending"]))
        own = SW.arrival_needs_you(c, sp) if NEW else []
        DUMP["owner"] = [l["text"] for l in own]
        say("   the owner's arrival lines (scan-tied orders only): %d" % len(own))
        for l in own:
            say("     %s" % l["text"])
        d712 = []
        try:
            S_ = AD.state(c, today.isoformat(), "", owner=True)
            d712 = [l["text"] for l in AD._d712_owner_lines(c, S_)]
        except Exception as e:                                 # noqa: BLE001
            say("   (amir_day.state could not be read on the copy: %s)" % str(e)[:160])
        say("   D712's lines (untied taps with no scan from that supplier): %d %s" % (len(d712), d712))
        opn = SF.arrivals_open(c, sp, SF.Ctx(c, sp)) if NEW else []
        untied = [x for x in opn if not x["scan_tied"]]
        say("   arrivals_open on untied orders (left to D712, not on the owner's line): %d %s" % (len(untied), [(x["item"], x["vendor"]) for x in untied]))
        # D712 names a TAPPED line of an UNTIED order (bill_pending rows with no scan from that supplier); the owner's arrival line names a line of a
        # TIED order only -- the two sets cannot share a line. Overlap = a D712 line whose vendor and tap day match an owner arrival line's tap.
        overlap = [l for l in own if l["text"].split(":")[0] in {x["item"] for x in opn if x["kind"] == "tap" and not x["scan_tied"]}]
        check("C: the owner's arrival lines are one per scan-tied open arrival (%d) and name no untied tap (D712's: %d lines; overlap %d)" % (len([x for x in opn if x["scan_tied"]]), len(d712), len(overlap)),
              NEW and len(own) == len([x for x in opn if x["scan_tied"]]) and not overlap and all((x["item"] + ":") in " ".join(DUMP["owner"]) for x in opn if x["scan_tied"]))
        nl = SW.needs_you_lines(c)
        check("C: stock_watch.needs_you_lines carries the arrival lines (%d of %d lines)" % (len([l for l in nl if "counted as arrived" in l["text"]]), len(nl)), NEW and len([l for l in nl if "counted as arrived" in l["text"]]) == len(own) and len(own) > 0)
        s, h = GET("manoj", "/finance/sanjeevni/api/needs-you")
        j = json.loads(h) if s == 200 else {}
        texts = json.dumps(j, ensure_ascii=False)
        check("the owner's Needs-you page (/finance/sanjeevni/api/needs-you) answers 200 and %s the arrival lines" % ("carries" if NEW else "has none of"), s == 200 and (("counted as arrived" in texts) == NEW), (s, texts[:200]))
        c.close()
    section("9  the owner's lines: no overlap with D712; bill_pending_lines equal", s9)

    # ============================================================================================ 10 Darpan's receipt
    def s10():
        c = conn()
        ctx = SF.Ctx(c, sp)
        E = SF.expect_for_point(c, sp, "TOLTRIS PLUS", ctx)
        say("   TOLTRIS PLUS before the count: basis %s expected %s provisional %s" % (E["basis"], E["expected"], E["provisional"]))
        P = SW.write_point(c, "TOLTRIS PLUS", float(E["expected"] or 0), "darpan", "w583walk", sp=sp, note="W583 walk: Darpan's receipt on the copy")
        say("   Darpan's receipt (the existing words): status %s provisional %s basis %s | %s | %s" % (P["status"], P["provisional"], P["basis"], P["qty_hi"], P["verdict_hi"] or "(no verdict)"))
        check("C: Darpan's receipt for TOLTRIS PLUS (its arrival expired) is judged at once: status settled, provisional 0 (was provisional 500)", P["status"] == "settled" and float(P["provisional"] or 0) == 0, (P["status"], P["provisional"]))
        check("the receipt's words are the existing ones ('Marg se barabar' for a count equal to the figure)", P["verdict_hi"] == "Marg se barabar", P["verdict_hi"])
        n = SW.settle_provisional(c, sp)
        say("   settle_provisional on the copy settled %d point(s)" % n)
        c.close()
    section("10 Darpan's receipt for an expired arrival", s10)

    # ============================================================================================ 11 grep
    def s11():
        src = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in ("stock_figure.py", "shelf_figure.py", "stock_watch.py")}
        check("C: no 'scan_arrivals' in shelf_figure.py", "scan_arrivals" not in src["shelf_figure.py"])
        check("C: no supplier-key test in _arrivals / bill_pending_lines (no 'supkey=?' in their bodies)", all("supkey=?" not in fn_body(src["stock_watch.py"], n) and fn_body(src["stock_watch.py"], n) for n in ("_arrivals", "bill_pending_lines")))
        check("C: one carried rule: 'k20=? AND supkey=? AND date>=?' appears in none of the three files", all("k20=? AND supkey=? AND date>=?" not in t for t in src.values()))
        check("C: 'def carried(' once, 'def expired(' once, 'def scan_arrivals(' once -- all in stock_figure.py", sum(t.count("def carried(") for t in src.values()) == 1 and sum(t.count("def expired(") for t in src.values()) == 1
              and sum(t.count("def scan_arrivals(") for t in src.values()) == 1 and "def carried(" in src["stock_figure.py"] and "def scan_arrivals(" in src["stock_figure.py"])
        check("C: shelf() adds taps and scan_arrivals from this file (no _sf_shelf().scan_arrivals)", "_sf_shelf().scan_arrivals" not in src["stock_figure.py"] and "scan_arrivals(con, sp, name, mine[\"day\"], ctx)" in src["stock_figure.py"])
        check("C: _arrivals marks in_spine by carried() only", "carried(con, sp, a, ctx) is not None" in fn_body(src["stock_watch.py"], "_arrivals") and "expired(" not in fn_body(src["stock_watch.py"], "_arrivals"))
        check("C: the setting arrival.back_days is in stock_watch.SETTINGS with seed=None", 'key="arrival.back_days"' in src["stock_watch.py"] and re.search(r'key="arrival\.back_days".*?seed=None', src["stock_watch.py"], flags=re.S) is not None)
        others = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in ("porders.py", "order_rules.py", "amir_day.py", "stock_app.py", "order_sheet.py") if os.path.exists(os.path.join(fin, n))}
        check("no file outside the kit calls shelf_figure.scan_arrivals", all("scan_arrivals" not in t for t in others.values()))
        say("   left, named (the brief 3.4): porders.detect_supplies and order_rules._s470_arrivals keep their own same-vendor, date >= order-day test: %s"
            % ["%s: %s" % (n, "present" if ("def detect_supplies(" in t or "def _s470_arrivals(" in t) else "-") for n, t in others.items() if n in ("porders.py", "order_rules.py")])
    section("11 the grep tests (charter 2, 9)", s11)

    # ============================================================================================ 12 old -> new; the guard; staff screens
    def s12():
        c = conn()
        o = OLD.get("figures") or {}
        fig = DUMP.get("figures") or {}
        moved = []
        for it in ITEMS:
            if o and o.get(it) and fig.get(it) and (o[it]["arrived"] != fig[it]["arrived"] or o[it]["shelf"] != fig[it]["shelf"]):
                moved.append(it)
                say("   %-30s arrived %6s -> %-6s shelf %6s -> %-6s receipt provisional %s -> %s" % (it, o[it]["arrived"], fig[it]["arrived"], o[it]["shelf"], fig[it]["shelf"], o[it]["provisional"], fig[it]["provisional"]))
        if o:
            say("   items of the 13 whose figures moved: %d; unchanged: %s" % (len(moved), [it for it in ITEMS if it not in moved]))
        check("C: TOLTRIS PLUS arrived 500 -> 0 against the old files' dump", bool(o) and o.get("TOLTRIS PLUS", {}).get("arrived") == 500 and fig.get("TOLTRIS PLUS", {}).get("arrived") == 0)
        st = SA.amir_stage(c, 1) or {}
        A, C_ = st.get("A") or {}, st.get("C") or {}
        DUMP["not_shelf"] = [A.get("not_shelf"), C_.get("not_shelf")]
        say("   the voucher guard's 'not judged against the shelf': A %s, C %s%s" % (A.get("not_shelf"), C_.get("not_shelf"), ("  (old files: A %s, C %s)" % tuple(OLD["not_shelf"])) if OLD.get("not_shelf") else ""))
        check("the voucher guard still runs on the copy (stage %s)" % st.get("stage"), bool(st.get("stage")))
        pages = [("amir", "/finance/amir", True), ("amir", "/finance/stock/api/pad/amir/1", False), ("darpan", "/finance/stockmatch", False), ("darpan", "/finance/stockmatch/api/state", False),
                 ("darpan", "/finance/darpan/kal", True), ("shavez", "/finance/reports/aaj", True), ("reception", "/finance/porders", True),
                 ("manoj", "/finance/stock/api/now", False), ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed_total = 0
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if path.startswith("/finance/stock/api/") or path.endswith("/state") or path.endswith("needs-you"):
                try:
                    j = json.loads(h)
                    for k in ("you", "ours_at", "stored_at", "stored_text", "readiness", "cache", "refresh_ms", "watch"):
                        j.pop(k, None) if isinstance(j, dict) else None
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = text(h)
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                os_, ns = set(old), set(lines)
                gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                if gone or new:
                    changed_total += 1
                    say("   WORDS CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:8]:
                        say("      - %s" % l[:220])
                    for l in new[:8]:
                        say("      + %s" % l[:220])
                else:
                    say("   words unchanged on %s for %s" % (path, u))
        say("   pages whose words changed against the old files: %d (the state changes printed above; no new staff sentence)" % changed_total)
        say("   no duty is added, moved or removed: DUTY_MAP is not changed by this kit")
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
        c.close()
    section("12 the 13 items old -> new; the guard's count; the staff screens' words", s12)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S583: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S583: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S583: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S583: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
