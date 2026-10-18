#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s584.py -- kit S584_SMALL_FIXES (18-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s584.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --map <DUTY_MAP.json>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s584.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --map ...   (the install-day state)
The real finance app in one process (the walk's own header session -- its own secret and user store, never the live ones). Its own rows
by key (W584 ...), never by counting; the live rows by key. No phone number is printed (a run of ten digits is masked). The sections follow
the brief's section 4 (one section per control, 1-15); --expect-red is the negative control: the same walk on the OLD files, every 'C:'
check must be red. --state prints the install-day state: the F-916 record (a supplier under both 'Still to order' and 'Done', its cause),
Amir's stage words, _s584_pur_landed, the readiness stock line, the nine settings rows, the system's closures. Prints 'WALK OK S584 ...'."""
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

KIT = "S584_SMALL_FIXES"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
NINE = ("amir.proof_wait_hours", "amir.refused_keep_hours", "amir.job_wait_days", "amir.salt_owed_days", "amir.self_exports",
        "amir.claim_open_days", "amir.voucher_visits", "owner.salt_list_days", "owner.item_lists_days")
HEADING = "Amir and the reports"
PUR_HI = "Purchase report nikaaliye"
LANDED_EN = "judged at the spine's next build (within 10 minutes)"
OLD_LIT = "(number nahi hai)"
WV = "W584 DEALER"                                            # the walk's own phone-book record (its display name differs in case only)
WV_DISP = "W584 Dealer"
WV_M1 = "w584  dealer"                                        # merged into it: the same name, lower case, two spaces
WV_M2 = "W584 DEALERS AND SONS"                               # merged into it: a truly different name
APPROX_ITEM = "W584 APPROX ITEM"
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:600] + "]") if (got is not None and not cond) else ""))
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
        check("C: section %s ran without an exception" % title, False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-700:]))


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


def read(fin, name):
    return open(os.path.join(fin, name), encoding="utf-8").read()


def synthetic_stage(stage):
    """A stage dict as amir_stage shapes it, in the 'export' state with why='pur_behind' -- the one state the E fix changes."""
    pr = dict(state="export", why="pur_behind", since="2026-10-17T19:05:00", last_at="2026-10-17T19:05:00", closing_day="18-10-2026",
              closing_at="2026-10-18T05:17:00", as_after=None, rows=[])
    if stage == "A":
        return dict(count_id=1, stage="A", A=dict(total=2, entered=2, open=0, pending=0, proof=pr, verified_at=None, held=[]), B=None, C={},
                    visible=[], renames_visible=False, numbers={})
    return dict(count_id=1, stage="C", A=dict(total=2, entered=2, open=0, pending=0, proof=dict(state="done"), verified_at="x", held=[]), B=None,
                C=dict(total=5, entered=5, released=5, verified=0, open=0, lots=1, wrong=[], waiting_export=[dict(proof=pr)]),
                visible=[], renames_visible=False, numbers={})


def f916_record(con, OS, PS):
    """F-916, read only: every supplier under BOTH 'Still to order' (order_sheet.entries) and 'Done' (porders_s454._done_today)."""
    out = []
    try:
        es = {e["sn"]: e for e in OS.entries(con)}
        done = PS._done_today(con)
        ns = OS.newest_sheet(con)
        taken = str((ns or {}).get("taken_at") or "")
        for d in done:
            e = es.get(d["sn"])
            if not e:
                continue
            out.append(dict(vendor=d["vendor"], sources=sorted(e.get("sources") or []), state=e.get("state"),
                            lines=[(l["item"], l["qty"], l["src"]) for l in e["lines"]],
                            done=dict(order_id=d["id"], created_at=str(d.get("sent_at") or ""), via=d.get("via")), sheet_taken_at=taken))
    except Exception as ex:                                    # noqa: BLE001
        out.append(dict(error="%s: %s" % (type(ex).__name__, str(ex)[:200])))
    return out


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    SA.ensure_schema(con)
    new = hasattr(SA, "_s584_pur_landed")
    sp = SW.Spine()
    say("STATE %s: files %s; spine ok %s" % (label, "NEW (S584)" if new else "OLD", sp.ok))
    say("STATE %s: readiness stock line: %s" % (label, SA._r_stock(con)["line"]))
    st = SA.amir_stage(con, 1) or {}
    W = SA._s521_stage_words(con, st)
    pr = SA._s488_stage_proof(st) or {}
    say("STATE %s: Amir's stage %s, proof state %s why %s; card_hi: %s" % (label, st.get("stage"), pr.get("state"), pr.get("why"), W.get("card_hi")))
    say("STATE %s: owner_en: %s" % (label, W.get("owner_en")))
    if new:
        say("STATE %s: _s584_pur_landed (a VERIFIED purchase export newer than the spine's purchase reach): %s" % (label, SA._s584_pur_landed(con, sp)))
        rows = [r for r in SW.settings_view(con) if r["heading"] == HEADING]
        say("STATE %s: the nine settings on the card (%d): %s" % (label, len(rows), ["%s=%s%s" % (r["key"], r["value"], "" if r["set"] else " (default)") for r in rows]))
    rec = f916_record(con, OS, PS)
    say("STATE %s: F-916 -- suppliers under both 'Still to order' and 'Done': %d" % (label, len(rec)))
    for r in rec:
        say("   %s" % json.dumps(r, ensure_ascii=False, default=str))
    try:
        import loss_piles as LP                               # noqa: E402
        sc = LP._system_closed(con, SA._desk_root(con, 1) or 1)
        say("STATE %s: the system's closures (loss_piles._system_closed): %s" % (label, (sc or {}).get("text")))
    except Exception as e:                                    # noqa: BLE001
        say("STATE %s: _system_closed could not be read: %s" % (label, str(e)[:120]))
    json.dump(dict(label=label, f916=rec, card_hi=W.get("card_hi"), owner_en=W.get("owner_en")), open(os.path.join(os.path.dirname(dbp), "state_%s.json" % label), "w"), default=str)
    con.rollback()
    say("STATE OK S584 (%s)" % label)
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
    anywhere = os.environ.get("S584_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S584 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stockmatch as SM                                   # noqa: E402
    import amir_day as AD                                     # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    import order_sheet_pdf as OP                              # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import loss_piles as LP                                   # noqa: E402
    import reports_tile as RT                                 # noqa: E402
    for m in (SA, SW, SF, SM, AD, PA, OP, PS, OS, LP, RT):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(SA, "_s584_pur_landed")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_watch v%s (%s); amir_day KIT %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", SW.VERSION, "NEW" if NEW else "OLD", AD.KIT))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}

    def GET(u, path, follow=False):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, json=body)
        try:
            return r.status_code, json.loads(r.get_data().decode("utf-8", "replace"))
        except ValueError:
            return r.status_code, {}

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    SA.ensure_schema(sqlite3.connect(dbp))
    sp = SW.Spine()
    assert sp.ok and SW.SPINE_DB == os.path.join(fin, "spine", "spine.db"), (sp.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    SRC = {n: read(fin, n) for n in ("stock_app.py", "stock_watch.py", "stock_now.html", "stock_drift.html", "stock_loss.html", "stockmatch.py",
                                     "amir_day.py", "purchase_app.py", "order_sheet_pdf.py")}
    c0 = conn()
    ROOT = SA._desk_root(c0, 1) or 1
    R = SF.reach(sp)
    say("   today %s; count root %s; the spine's reach: last_pur %s, pur_stamp %s -> %s" % (dt.date.today(), ROOT, R.get("last_pur"), R.get("pur_stamp"), SF.stamp_iso(R.get("pur_stamp"))))
    say("   the phone book switch (purchase.book_one_record.on): %s; book users: %s; advice senders: %s" % (PA.book_on(c0), sorted(PA._book_users(c0)), PA._s446_setting(c0, "supplier_msg.senders", "manoj,shavez")))
    c0.close()

    # ============================================================================================ 1 F-931 a: the drift page
    def s1():
        h = SRC["stock_drift.html"]
        check("C: stock_drift.html no longer prints i.last raw (\"'+i.last\" followed by a newline is gone)", "'+i.last\n" not in h)
        check("C: stock_drift.html draws the last-day gap through a null-to-dash helper (num(i.last); function num present)", "num(i.last)" in h and "function num(v)" in h)
        s, b = GET("manoj", "/finance/stock/api/drift")
        j = json.loads(b) if s == 200 else {}
        items = j.get("items") or []
        nulls = [i["item"] for i in items if i.get("last") is None]
        check("the drift API still sends `last` on every row (%d rows, %d with last=None on this copy)" % (len(items), len(nulls)), s == 200 and all("last" in i for i in items), (s, b[:200]))
        say("   rows with no PC estimate (the 'null' the owner saw): %d" % len(nulls))
    section("1  F-931 a: 'null' on the drift page becomes a dash", s1)

    # ============================================================================================ 2 F-931 b: _r_stock
    def s2():
        c = conn()
        st = SA._r_stock(c)
        say("   _r_stock line: %s" % st["line"])
        check("C: the line names Marg's closing as taken (the capture) and the shelf figure's basis", "taken" in st["line"] and "The shelf figure" in st["line"], st["line"])
        check("C: the words 'processed here' and 'Our computed figure' are gone from the line", "processed here" not in st["line"] and "Our computed figure" not in st["line"], st["line"])
        body = fn_body(SRC["stock_app.py"], "_r_stock").split("\n\n\n")[0]          # the function alone (two blank lines end it)
        check("C: _r_stock no longer reads stock_feed (nor _feed_latest)", bool(body) and "stock_feed" not in body and "_feed_latest" not in body)
        check("C: 'expected' is gone from _r_stock's dict", bool(body) and '"expected"' not in body)
        check("api_drift still reads stock_feed (the 4b-2 witness, not this kit's)", "stock_feed" in fn_body(SRC["stock_app.py"], "api_drift"))
        m = st.get("marg") or {}
        check("out['marg'] keeps its shape (as_on dd-mm-yyyy, processed_at, items) for readiness()'s warning", bool(m) and re.match(r"^\d{2}-\d{2}-\d{4}$", str(m.get("as_on") or "")) and "processed_at" in m and "items" in m, m)
        rd = SA.readiness(c)
        DUMP["warnings"] = rd.get("warnings") or []
        DUMP["rdy_stock_line"] = st["line"]
        say("   readiness warnings (%d): %s" % (len(DUMP["warnings"]), DUMP["warnings"]))
        if "warnings" in OLD:
            check("readiness()['warnings'] unchanged against the old files on the same copy", DUMP["warnings"] == OLD["warnings"], (OLD["warnings"], DUMP["warnings"]))
        c.close()
    section("2  F-931 b: the readiness stock line describes the figures of record", s2)

    # ============================================================================================ 3 F-932: the stock-now page
    def s3():
        s, b = GET("manoj", "/finance/stock/api/now")
        j = json.loads(b) if s == 200 else {}
        check("/stock/api/now as the doctor: pc_old_head present, a fifth column name", s == 200 and j.get("pc_old_head") and len(j.get("columns") or []) == 5, (s, j.get("pc_old_head"), j.get("columns")))
        DUMP["now_totals"] = dict((k, (j.get("totals") or {}).get(k)) for k in ("items", "agree", "differ", "below_zero"))
        say("   the owner's figures: %s; as_on %s, marg_at %s" % (DUMP["now_totals"], j.get("as_on"), j.get("marg_at")))
        other = None
        for u in ("darpan", "amir", "shavez"):
            s2_, b2 = GET(u, "/finance/stock/api/now")
            if s2_ == 200:
                other = (u, json.loads(b2))
                break
        check("/stock/api/now as a non-doctor (%s): pc_old_head absent, four columns" % (other[0] if other else "-"), bool(other) and not other[1].get("pc_old_head") and len(other[1].get("columns") or []) == 4,
              (other[0], other[1].get("pc_old_head"), other[1].get("columns")) if other else None)
        h = SRC["stock_now.html"]
        check("C: stock_now.html draws the fifth column only under pc_old_head (DATA.pc_old_head in the row; the <th> appended under j.pc_old_head)", "DATA.pc_old_head?" in h and "j.pc_old_head" in h and "pc_old_head" not in h.split("<script>")[0])
        check("C: stock_now.html carries the PC note under the tiles", "PC's old estimate (retiring): shown to you only, retired after the side-by-side week (4b-2)." in h and 'id="pcnote"' in h)
        check("C: the head line names the capture and the read moment (no 'processed')", "Marg&rsquo;s closing taken" in h and "; read " in h and "Our figure processed" not in h)
        if OLD.get("now_totals"):
            check("the owner's agree / differ figures are equal before and after (words changed, not figures)", OLD["now_totals"] == DUMP["now_totals"], (OLD["now_totals"], DUMP["now_totals"]))
    section("3  F-932: the fifth column and the head line of the stock-now page", s3)

    # ============================================================================================ 4 F-932: the Loss desk
    def s4():
        h = SRC["stock_loss.html"]
        check("C: stock_loss.html draws D.system_closed.text above the piles", "sysClosedHtml" in h and "D.system_closed" in h and "S.text" in h)
        check("C: stock_loss.html draws W.approx_lines as the group 'Approximate spot counts' in watchCard()", "approx_lines" in h and "Approximate spot counts" in h)
        check("C: watchSettings() groups the rows by heading (s.heading)", "s.heading" in h and "Amir and the reports" not in h.split("function watchSettings")[0])
        c = conn()
        if not c.execute("SELECT 1 FROM stock_point WHERE item=?", (APPROX_ITEM,)).fetchone():
            ins(c, "stock_point", dict(item_norm=SW.norm_name(APPROX_ITEM), item=APPROX_ITEM, at=SW.now_iso(), qty_units=3, source="spot", by="w584walk",
                                       status="settled", settled_at=SW.now_iso(), note="W584 walk: an approximate point", basis="approx", provisional_units=0))
            c.commit()
        V = SW.refresh_owner_view(c, ROOT, who="w584walk", lines=[])
        check("refresh_owner_view on the copy (the card is the STORED view): approx_lines carries the walk's point", any(APPROX_ITEM in x for x in (V.get("approx_lines") or [])), V.get("approx_lines"))
        c.close()
        s, b = GET("manoj", "/finance/stock/api/loss/%d/piles" % ROOT)
        j = json.loads(b) if s == 200 else {}
        sc = j.get("system_closed") or {}
        say("   D.system_closed: %s" % sc.get("text"))
        check("the desk JSON carries D.system_closed (the live copy: the system's closures) with a text", s == 200 and bool(sc.get("text")) and int(sc.get("n") or 0) >= 1, (s, sc))
        ax = (j.get("watch") or {}).get("approx_lines") or []
        check("the desk JSON carries D.watch.approx_lines with the walk's approximate point", any(APPROX_ITEM in x for x in ax), ax)
        DUMP["desk"] = dict(system_closed=sc.get("text"), approx_n=len(ax))
    section("4  F-932: the Loss desk -- the system's closures and the approximate spot counts", s4)

    # ============================================================================================ 5 the nine settings
    def s5():
        c = conn()
        rows = {r["key"]: r for r in SW.settings_view(c) if r.get("heading") == HEADING}
        check("C: settings_view returns the nine rows under the heading '%s'" % HEADING, sorted(rows) == sorted(NINE), sorted(rows))
        held = {k: (c.execute("SELECT value, note FROM setting WHERE key=?", (k,)).fetchone()) for k in NINE}
        defaults = dict(AD.S444_DEFAULTS)
        defaults.update({RT.S488_LIST_KEYS[t[0]]: t[2] for t in RT.OWNER_LISTS})
        ok_all = bool(rows)
        for k in NINE:
            r = rows.get(k) or {}
            row = held[k]
            want = str(row[0]).strip() if row is not None else str(defaults[k])
            good = str(r.get("value")) == want and bool(r.get("set")) == (row is not None) and r.get("kind") == "int" and bool(r.get("hint"))
            ok_all = ok_all and good
            say("   %-24s value %-4s set %-5s (the copy's row: %s; the module's default %s) hint: %s" % (k, r.get("value"), r.get("set"), (row[0] if row else "none"), defaults[k], str(r.get("hint") or "")[:70]))
        check("C: each row's value is the copy's setting row when one exists (set=True) and the module's default otherwise (set=False)", ok_all)
        check("C: the seven amir.* hints are amir_day.S444_NOTES (read, not copied)", all(rows.get(k, {}).get("hint") == AD.S444_NOTES[k] for k in AD.S444_DEFAULTS))
        src = SRC["stock_watch.py"]
        blk = src[src.find("S584: the nine rows below"):src.find("SETTING_BY_KEY = ")] if "S584: the nine rows below" in src else ""
        check("C: the nine keys appear once each in stock_watch.SETTINGS", all(src.count('key="%s"' % k) == 1 for k in NINE))
        check("C: no default of their own in those rows ('default=' absent; no \"48\" / \"36\" / \"8\" / \"35\" literal)", bool(blk) and "default=" not in blk and not re.search(r'"(48|36|8|35)"', blk))
        check("C: PREFIXES carries 'amir.' and 'owner.' (the desk's save door routes them to the watch)", "amir." in SW.PREFIXES and "owner." in SW.PREFIXES)
        before = held["amir.proof_wait_hours"]
        s, j = POST("manoj", "/finance/stock/api/loss/%d/pile/setting" % ROOT, dict(key="amir.proof_wait_hours", value=72))
        check("C: the desk's save door accepts amir.proof_wait_hours=72 (message: %s)" % j.get("message"), s == 200 and j.get("ok") is True, (s, j))
        c2 = conn()
        check("C: amir_day._setting then reads 72", AD._setting(c2, "amir.proof_wait_hours") == 72, AD._setting(c2, "amir.proof_wait_hours"))
        after = c2.execute("SELECT value, note FROM setting WHERE key='amir.proof_wait_hours'").fetchone()
        check("C: the row's S444 note survives the save (%s)" % (str((after or ["", ""])[1])[:50]), after is not None and before is not None and after[0] == "72" and after[1] == before[1] and bool(str(before[1] or "").strip()), (before, after))
        for bad in (0, 1000):
            s, j = POST("manoj", "/finance/stock/api/loss/%d/pile/setting" % ROOT, dict(key="amir.proof_wait_hours", value=bad))
            check("C: the door rejects %d with the range (message: %s)" % (bad, j.get("message")), s == 400 and not j.get("ok") and "Between" in str(j.get("message")), (s, j))
        check("72 still stands after the two refusals", c2.execute("SELECT value FROM setting WHERE key='amir.proof_wait_hours'").fetchone()[0] == "72")
        if before is not None:                                 # the copy's row put back as it was (the walk's own change, undone by key)
            c2.execute("UPDATE setting SET value=? WHERE key='amir.proof_wait_hours'", (before[0],))
        else:
            c2.execute("DELETE FROM setting WHERE key='amir.proof_wait_hours'")
        c2.commit()
        SW.refresh_owner_view(c2, ROOT, who="w584walk", lines=[])
        c2.close()
        c.close()
        s, b = GET("manoj", "/finance/stock/api/loss/%d/piles" % ROOT)
        j = json.loads(b) if s == 200 else {}
        ws = [r for r in ((j.get("watch") or {}).get("settings") or []) if r.get("heading") == HEADING]
        check("C: the desk's stored watch (D.watch.settings) carries the nine rows under the heading after a refresh", len(ws) == 9, [r.get("key") for r in ws])
        s, j = POST("manoj", "/finance/stock/api/loss/%d/pile/setting" % ROOT, dict(key="owner.salt_list_days", value=9))
        check("C: the door accepts owner.salt_list_days=9 and reports_tile._s488_list_limit reads 9", s == 200 and j.get("ok") and RT._s488_list_limit(conn(), "SALT_WISE_ITEM_LIST", 8) == 9, (s, j))
        c3 = conn()
        c3.execute("DELETE FROM setting WHERE key='owner.salt_list_days' AND value='9'")   # the walk's own row on the copy (it did not exist before)
        c3.commit()
        c3.close()
    section("5  the nine settings on the owner's card: rows, defaults, the save door, the S444 note", s5)

    # ============================================================================================ 6 E of D737
    def s6():
        c = conn()
        ps = SF.stamp_iso(R.get("pur_stamp"))
        check("the spine's purchase reach has a stamp (%s)" % ps, bool(ps))
        say("   mi_file VERIFIED purchase rows newer than the reach on the copy: %s" % [tuple(r) for r in c.execute(
            "SELECT type, substr(replace(received_at,'T',' '),1,19) FROM mi_file WHERE verdict='VERIFIED' AND type IN ('PURCHASE_BILLWISE','PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE') "
            "AND substr(replace(received_at,'T',' '),1,19) > ? ORDER BY received_at DESC LIMIT 4", (ps.replace("T", " "),))])
        live_landed = SA._s584_pur_landed(c, sp) if NEW else None
        say("   _s584_pur_landed on the live copy: %s" % live_landed)
        md5 = "w584" + secrets.token_hex(14)
        c.execute("DELETE FROM mi_file WHERE md5 LIKE 'w584%'")
        c.commit()
        stA, stC = synthetic_stage("A"), synthetic_stage("C")
        wA0, wC0 = SA._s521_stage_words(c, stA), SA._s521_stage_words(c, stC)
        say("   stage A words with no landed export: %s | %s" % (wA0["card_hi"], wA0["owner_en"]))
        check("with no later export: the do-this line '%s' stands in stage A and stage C (pur_behind)" % PUR_HI, PUR_HI in wA0["card_hi"] and PUR_HI in wC0["card_hi"] or (live_landed is not None),
              (wA0["card_hi"], wC0["card_hi"], live_landed))
        at = (dt.datetime.fromisoformat(ps) + dt.timedelta(minutes=7)).replace(microsecond=0)
        ins(c, "mi_file", dict(md5=md5, drive_id="", drive_name="W584 purchase bill-wise.xlsx", drive_folder="w584walk", drive_mtime="", size=1,
                               stamp=at.strftime("%Y%m%d-%H%M%S"), type="PURCHASE_BILLWISE", variant="DEFAULT", date_from="2026-10-01", date_to=at.date().isoformat(),
                               verdict="VERIFIED", reason="", server_name="", kept=0, lines=0, pc_type="", pc_verdict="", agree="",
                               received_at=at.isoformat() + "+05:30", source="w584walk"))
        c.commit()
        landed = SA._s584_pur_landed(c, sp) if NEW else None
        check("C: _s584_pur_landed sees the walk's VERIFIED purchase export (%s) landed after the reach %s" % (at.strftime("%Y-%m-%d %H:%M:%S"), ps), landed == at.strftime("%Y-%m-%d %H:%M:%S"), landed)
        wA, wC = SA._s521_stage_words(c, stA), SA._s521_stage_words(c, stC)
        say("   stage A words with the landed export: %s | %s" % (wA["card_hi"], wA["owner_en"]))
        say("   stage C words with the landed export: %s | %s" % (wC["card_hi"], wC["owner_en"]))
        check("C: stage A: the suffix '%s' is gone once his export has landed" % PUR_HI, PUR_HI not in wA["card_hi"] and PUR_HI not in wA["board_hi"], wA["card_hi"])
        check("C: stage C: the suffix is gone too", PUR_HI not in wC["card_hi"], wC["card_hi"])
        check("C: the owner's English says 'purchase report landed hh:mm -- %s'" % LANDED_EN, ("purchase report landed %s" % at.strftime("%H:%M")) in wA["owner_en"] and LANDED_EN in wA["owner_en"] and LANDED_EN in wC["owner_en"], (wA["owner_en"], wC["owner_en"]))
        check("the tick stays the stage's: the words' state is still 'export' (the judgment waits for the spine's next build)", wA["state"] == "export" and wC["state"] == "export", (wA["state"], wC["state"]))
        c.execute("DELETE FROM mi_file WHERE md5=?", (md5,))
        c.commit()
        wA2 = SA._s521_stage_words(c, stA)
        check("the walk's row removed: the suffix returns unless a real later export is on the copy (live landed: %s)" % live_landed, (PUR_HI in wA2["card_hi"]) == (live_landed is None), wA2["card_hi"])
        # guards
        if NEW:
            sp0 = SW.Spine(os.path.join(fin, "spine", "no_such_spine.db"))
            check("guard: a missing spine -> None (never 'every row is later')", SA._s584_pur_landed(c, sp0) is None)
            c0 = sqlite3.connect(":memory:")
            check("guard: no mi_file table -> None", SA._s584_pur_landed(c0, sp) is None)
        check("amir_day._s488_ending / _s488_wait_line are untouched (seen, not touched)", "waiting for a purchase export that reaches that day (Amir)" in SRC["amir_day.py"] and "def _s488_wait_line(" in SRC["amir_day.py"])
        c.close()
    section("6  E of D737: Amir's 'Purchase report nikaaliye' follows the fact", s6)

    # ============================================================================================ 7 F-875
    def s7():
        c = conn()
        sa = SM._sa()
        d = sa._pad_report_data(c, ROOT)
        check("the count's report reads on the copy (root %s)" % ROOT, d is not None)
        real = sa.amir_stage(c, ROOT, d=d) or {}
        say("   the live guard: A.held %d, A.pending %s, stage %s" % (len((real.get("A") or {}).get("held") or []), (real.get("A") or {}).get("pending"), real.get("stage")))
        st0 = SM.section_state(c, d)
        v0 = [x for x in st0["conds"] if x["key"] == "vouchers"][0]
        say("   the live orthotic tick: %s -- %s" % (v0["ok"], v0["en"]))
        DUMP["ortho_c2"] = dict(ok=v0["ok"], en=v0["en"])
        held_line = dict(item="W584 HELD BELT", why="not_shelf", marg_now=4, shelf=None, after=4)
        fake = dict(count_id=ROOT, stage="A", A=dict(total=0, entered=0, open=0, pending=0, proof=dict(state="done", as_after="18-10-2026", rows=[]), verified_at="x", held=[held_line]),
                    B=dict(total=0, verified=0, ticked=0, old=[], questions=0), C={}, visible=[], renames_visible=False, numbers={})
        keep = (sa.amir_stage, sa._voucher_pending, sa._voucher_state)
        try:
            sa.amir_stage = lambda con_, root_, d=None, ctx=None: fake
            sa._voucher_pending = lambda con_, d_, section=None: []
            sa._voucher_state = lambda con_, d_: dict(rounds=[])
            st1 = SM.section_state(c, d)
        finally:
            sa.amir_stage, sa._voucher_pending, sa._voucher_state = keep
        v1 = [x for x in st1["conds"] if x["key"] == "vouchers"][0]
        say("   with one held orthotic line (and nothing pending, nothing unentered): %s -- %s / %s" % (v1["ok"], v1["en"], v1["hi"]))
        check("C: F-875: a line the guard HOLDS keeps the orthotic tick off (c2 False) with the existing words", v1["ok"] is False and "not yet on a voucher" in v1["en"] and "Vouchers banane baaki" in v1["hi"], v1)
        body = fn_body(SRC["stockmatch.py"], "section_state")
        check("C: amir_stage is read once in section_state, above c2, and reused", body.count("sa.amir_stage(con, root, d=d)") == 1 and body.find("sa.amir_stage(con, root, d=d)") < body.find("c2 = ") and "(not held)" in body)
        c.close()
    section("7  F-875: the hub's orthotic tick waits on a held line", s7)

    # ============================================================================================ 8 F-881
    def s8():
        s, b = GET("amir", "/finance/amir/api/healthz")
        j = json.loads(b) if s == 200 else {}
        check("C: amir_day's /healthz names %s (got %s)" % (KIT, j.get("kit")), s == 200 and j.get("kit") == KIT, (s, b[:160]))
        check("C: KIT = \"S533 is nowhere in the finance folder", not any('KIT = "S533' in read(fin, n) for n in os.listdir(fin) if n.endswith(".py")))
    section("8  F-881: Amir's page names the kit that built it", s8)

    # ============================================================================================ 9 F-913
    def s9():
        c = conn()
        sk = PA.supplier_key(WV)
        c.execute("DELETE FROM purchase_vendor_contact WHERE vendor_norm LIKE 'W584%'")
        ins(c, "purchase_vendor_contact", dict(vendor_norm=sk, vendor=WV, display_name=WV_DISP, phone="", updated_at=SW.now_iso(), source="server"))
        ins(c, "purchase_vendor_contact", dict(vendor_norm="W584 DEALER (M1)", vendor=WV_M1, phone="", updated_at=SW.now_iso(), source="server", merged_into=sk))
        ins(c, "purchase_vendor_contact", dict(vendor_norm="W584 DEALER (M2)", vendor=WV_M2, phone="", updated_at=SW.now_iso(), source="server", merged_into=sk))
        c.commit()
        check("the walk's record is on the copy (display name differs from its vendor text in case only; two merged names)",
              c.execute("SELECT COUNT(*) FROM purchase_vendor_contact WHERE vendor_norm LIKE 'W584%'").fetchone()[0] == 3)
        c.close()
        on = PA.book_on(conn())
        check("the one-record phone book is ON on the copy (S574's switch)", on)
        s, h = GET("manoj", "/finance/purchase/page/book")
        check("the doctor's phone book page reads (%s)" % s, s == 200)
        m = re.search(r'<tr data-q="[^"]*W584 DEALER[^"]*">.*?</tr>', h, flags=re.S)
        row = text(m.group(0)) if m else ""
        also = re.search(r"also: ([^<]*)", m.group(0)) if m else None
        also_txt = _html.unescape(also.group(1)) if also else ""
        say("   the record's row: %s" % row[:200])
        say("   under 'also': %r" % also_txt)
        check("C: F-913: the record's own spelling (case / spacing) is not listed under 'also'", bool(m) and WV not in also_txt.split(", ") and WV_M1 not in also_txt, also_txt)
        check("a truly different merged name is still listed under 'also'", bool(m) and WV_M2 in also_txt, also_txt)
    section("9  F-913: a merged dealer no longer lists its own name under 'also'", s9)

    # ============================================================================================ 10 F-914
    def s10():
        res = {}
        for u in ("darpan", "shavez", "manoj"):
            s, h = GET(u, "/finance/purchase/page/book")
            res[u] = (s, "bookForm(" in h and "'bank')" in h, h.count("bank details</button>"), "no bank details" in h or "VERIFIED" in h)
            say("   %-8s page %s; bank button %s (%d); chip text present %s" % (u, s, res[u][1], res[u][2], res[u][3]))
        check("darpan is admitted to the book on the copy (the setting names him)", res["darpan"][0] == 200, res["darpan"])
        check("C: F-914: Darpan's book page has NO 'add / edit bank details' button (no bookForm(..,'bank'))", res["darpan"][0] == 200 and res["darpan"][1] is False and res["darpan"][2] == 0, res["darpan"])
        check("Darpan still sees the chip text (VERIFIED / UNVERIFIED / no bank details)", res["darpan"][3])
        check("Shavez's page keeps the bank button", res["shavez"][0] == 200 and res["shavez"][1] is True, res["shavez"])
        check("the owner's page keeps the bank button", res["manoj"][0] == 200 and res["manoj"][1] is True, res["manoj"])
        s, j = POST("darpan", "/finance/purchase/api/book", dict(action="bank", vendor=WV, acct_name="W584 walk"))
        check("the door still refuses 'bank' for Darpan (%s)" % s, s in (400, 403) and not j.get("ok"), (s, j))
    section("10 F-914: the bank-details button follows the door", s10)

    # ============================================================================================ 11 F-915
    def s11():
        want = PS.T["nonum"][0]
        g = OP._band_geom(dict(name="W584 SUPPLIER", phones=[]))
        say("   the band for a supplier with no number: %r" % g["ph"])
        check("C: F-915: the band says exactly porders_s454.T['nonum'][0] (%s), no 'Ph. ' prefix" % want, g["ph"] == [want], g["ph"])
        g2 = OP._band_geom(dict(name="W584 SUPPLIER", phones=["1234", "5678"]))
        check("with numbers: 'Ph. ' + the numbers as before", g2["ph"][0].startswith("Ph. 1234, 5678"), g2["ph"])
        c = conn()
        try:
            pdf = OP.build(c)
            tx = OP.text_of(pdf)
            check("the printed sheet builds on the copy (%d strings)" % len(tx), len(tx) > 0)
            check("the old literal '%s' is in no string of the sheet" % OLD_LIT, not any(OLD_LIT in t for t in tx))
            folded = OP._cdp()._latin(want)
            if any(folded in t for t in tx):
                say("   a supplier with no number is on this sheet: the sentence prints as %r (the dash folded by _latin)" % folded)
            else:
                say("   every supplier on this sheet has a number: the sentence is not on it today")
        except Exception as e:                                 # noqa: BLE001
            check("the printed sheet builds on the copy", False, str(e)[:200])
        c.close()
        check("C: the literal '%s' appears in no file of the finance folder" % OLD_LIT, not any(OLD_LIT in read(fin, n) for n in os.listdir(fin) if n.endswith((".py", ".html"))))
        check("C: order_sheet_pdf imports porders_s454 inside _band_geom (no top-level import, no copy of the sentence)", "import porders_s454" in fn_body(SRC["order_sheet_pdf.py"], "_band_geom") and not re.search(r"^import porders_s454", SRC["order_sheet_pdf.py"], flags=re.M))
    section("11 F-915: the printed sheet uses the screens' words for a supplier with no number", s11)

    # ============================================================================================ 12 F-916 read only
    def s12():
        c = conn()
        rec = f916_record(c, OS, PS)
        DUMP["f916"] = rec
        say("   F-916 -- suppliers under both 'Still to order' and 'Done' on this copy: %d" % len(rec))
        for r in rec:
            say("   %s" % json.dumps(r, ensure_ascii=False, default=str))
        check("the F-916 record could be read (nothing changed on that screen)", not any("error" in r for r in rec))
        c.close()
    section("12 F-916, read only: the cause from the live copy", s12)

    # ============================================================================================ 13 staff screens, the owner's figures
    def s13():
        pages = [("amir", "/finance/amir", True), ("amir", "/finance/stock/api/pad/amir/1", False), ("darpan", "/finance/stockmatch", False), ("darpan", "/finance/stockmatch/api/state", False),
                 ("darpan", "/finance/darpan/kal", True), ("darpan", "/finance/purchase/page/book", False), ("shavez", "/finance/reports/aaj", True), ("shavez", "/finance/purchase/page/book", False),
                 ("reception", "/finance/porders", True), ("manoj", "/finance/stock/api/now", False), ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed = {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if path.startswith("/finance/stock/api/") or path.endswith("/state") or path.endswith("needs-you"):
                try:
                    j = json.loads(h)
                    for k in ("you", "ours_at", "stored_at", "stored_text", "readiness", "cache", "refresh_ms", "watch", "at", "built"):
                        j.pop(k, None) if isinstance(j, dict) else None
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = text(h)
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            lines = [l for l in lines if "W584" not in l]                                    # the walk's own rows are not the screen's words
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                os_, ns = set(old), set(lines)
                gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                if gone or new:
                    changed[(u, path)] = (gone, new)
                    say("   WORDS CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:6]:
                        say("      - %s" % l[:240])
                    for l in new[:6]:
                        say("      + %s" % l[:240])
                else:
                    say("   words unchanged on %s for %s" % (path, u))
        if a.old_dump:
            # the differences the brief allows: Darpan's book page lacks the bank button; Amir's line without the suffix (and the owner's English
            # 'purchase report landed') when a later export is on the copy; the orthotic tick off while the guard holds a line (F-875, named)
            def strip_bank(g):
                return g.replace(" edit bank details", "").replace(" add bank details", "")

            def strip_pur(g):
                return g.replace(" · " + PUR_HI, "").replace(PUR_HI, "").strip()
            bad = {}
            for (u, path), (gone, new) in changed.items():
                if u == "darpan" and path.endswith("/page/book"):
                    ok = all("bank details" in g for g in gone) and all(any(strip_bank(g) == n for g in gone) for n in new)
                elif u == "amir" or path.endswith("needs-you"):
                    ok = all((PUR_HI in g) or ("waiting for a purchase export" in g) for g in gone) and \
                        all(any(strip_pur(g) == n.strip() for g in gone) or ("purchase report landed" in n) for n in new)
                elif u == "darpan" and path.startswith("/finance/stockmatch"):
                    ok = all(("orthotic round made and entered" in g) or ("Amir ke vouchers ho gaye" in g) or ("CLOSED" in g) or ("BAND" in g) for g in gone) and \
                        all(("not yet on a voucher" in n) or ("Vouchers banane baaki" in n) or ("open again" in n) or ("phir khul" in n) or ("still to follow" in n) or ("baaki:" in n) for n in new)
                else:
                    ok = False
                if not ok:
                    bad[(u, path)] = (gone[:3], new[:3])
            check("no staff screen changed its words beyond the brief's allowed differences (%d page(s) differ)" % len(changed), not bad, bad)
        say("   no duty is added, moved or removed: DUTY_MAP is not changed by this kit")
    section("13 the staff screens word for word; the owner's figures", s13)

    # ============================================================================================ 14 grep tests
    def s14():
        check("C: 'Our computed figure' / 'processed here' are not in _r_stock (the drift page's 176 witness line stays)", "processed here" not in fn_body(SRC["stock_app.py"], "_r_stock") and "Our computed figure" in SRC["stock_drift.html"])
        sw = SRC["stock_watch.py"]
        check("C: stock_watch.settings() and settings_view() read every row through _default (no s[\"default\"] in their bodies)",
              "def _default(s)" in sw and all('s["default"]' not in fn_body(sw, n) and "_default(s)" in fn_body(sw, n) for n in ("settings", "settings_view")))
        check("C: _s584_pur_landed is defined once and read by _s521_stage_words only", SRC["stock_app.py"].count("def _s584_pur_landed(") == 1 and SRC["stock_app.py"].count("_s584_pur_landed(con, _s524_spine())") == 1)
        check("C: the stock-now head no longer calls the read moment 'processed'", "Our figure processed" not in SRC["stock_now.html"])
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
    section("14 the grep tests (charter 2, 9); no ten-digit run", s14)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S584: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S584: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S584: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S584: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
