#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s577.py -- kit S577_STOCK_ON_SPINE (18-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s577.py --fin <scratch /root/finance with the files under test; its spine/spine.db = the NEW builder's scratch spine>
                            --old <folder holding the OLD shelf_figure.py> --db <COPY of finance.db> --adb <COPY of assets.db>
                            --marg <scratch marg_ingest> --portal <scratch portal *.py + tile_grants.json, no portal_config> --map <DUTY_MAP.json>
                            --readings <COPY of the readings store> --spine-old <the OLD builder's scratch spine (no sp_close_name)>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s577.py --state --fin ... --db ... --adb ... --marg ... --map ...        (the install-day state: before / after placing)
The real finance app in one process (the walk's own header session; never the live secret). Its own rows by key (W577 ...), never by
counting; the live rows by key. No phone number is printed (a run of ten digits is masked). The sections follow the brief's section 4:
  0  the live state (charter 7): the stage, the voucher lines and their verdicts, the provisional points, the newest three old gap sets,
     the desk cache, the system-written rows, the newest seven captures with end_day, the families of the newest capture, double packings
  1  a renamed item is judged (not 'not readable') and is approx; a renamed item alone under its key is not
  2  the 01-Oct Yuvika immobilizer line, its tie blanked, is not 'bill missing'
  3  the past-the-shelf test (five cases) on the walk's own item
  4  the capture rule (unchanged: the same on both files -- printed, not a red/green control)
  5  the desk only reads: two reads across a same-inputs spine rebuild = one build, nothing written outside the two cache tables; a new export
  6  settling and correcting points on their basis; an approx point: NULL gap, no verdict, out of month_leak
  7  shelf figures: no count -> None, the plan's no-count lines equal; every counted item whose figure moves, printed
  8  identity: key_of = the old key for every voucher item; stages A and C verdicts identical (printed)
  9  the gap sets: one s577 set for the newest covered end day, judged against the usable capture before it; a second pass writes nothing;
     s454_shelf_gap unchanged; the roster's reasons before and after
 10  a past_shelf held line prints the past_shelf sentence
 11  install order: with sp_close_name absent every lowering line is held with the not_ready words; record_gaps writes nothing
 12  an item absent from a full capture but known to sp_item reads 0; the staff words that change for it
 13  the grep tests (rule 2), the dead code gone
 14  staff-eye (CLAUDE.md, S444): every login's home tiles and pages; the lines whose words changed (against --old-dump)
 15  Amir's card and his pad under 2 s and 100 KB; no run of ten digits in this output
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control). Prints 'WALK OK S577 ...' on success."""
import argparse
import datetime as dt
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

KIT = "S577_STOCK_ON_SPINE"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
STAFF = ("amir", "darpan", "shavez", "reception")
FIX = "W577 FIX TAB"                                           # the walk's own item (the spine's scratch copy and the finance copy)
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


def load_old(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def app_env(a, dbp, token):
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB"):
        os.environ.pop(k, None)


def table_counts(dbp):
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    out = {}
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
        try:
            out[t] = c.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        except sqlite3.Error:
            out[t] = None
    c.close()
    return out


def gap_hash(dbp, table="s454_shelf_gap"):
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    try:
        rows = c.execute("SELECT * FROM %s ORDER BY 1, 2" % table).fetchall()
    except sqlite3.Error:
        rows = []
    c.close()
    return len(rows), hashlib.md5(repr(rows).encode("utf-8")).hexdigest()[:12]


def fn_body(src, name):
    """The text of one top-level def in a file (to the next top-level def / class / decorator)."""
    m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|# -{10,}|[A-Z_]+ = ))" % re.escape(name), src, flags=re.S | re.M)
    return m.group(0) if m else ""


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    """The owner's state by the files in --fin on a copy of the live database (the live ones before placing, the placed ones after)."""
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                    # noqa: E402
    import shelf_figure as SH                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    SA.ensure_schema(con)
    st = SA.amir_stage(con, 1) or {}
    A, C = st.get("A") or {}, st.get("C") or {}
    say("STATE %s: count #1 stage %s; A pending=%s held=%d unread=%s not_shelf=%s; C held=%d unread=%s not_shelf=%s wrong=%d; stage words: %s"
        % (label, st.get("stage"), A.get("pending"), len(A.get("held") or []), A.get("unread"), A.get("not_shelf", "-"), len(C.get("held") or []), C.get("unread"),
           C.get("not_shelf", "-"), len(C.get("wrong") or []), (SA._s521_stage_words(con, st) or {}).get("owner_en")))
    d = SA._pad_report_data(con, 1)
    o, h, u = SA._voucher_lines(con, d)
    say("STATE %s: pending voucher lines (unfrozen): offered %d, held %d, unread %d" % (label, len(o), len(h), len(u)))
    for x in o:
        say("   offered  %-30s %-7s %+d" % (x["item"], x["kind"], x["change"]))
    for x in h:
        say("   HELD     %-30s %-7s %+d  why=%s marg_now=%s shelf=%s after=%s" % (x["item"], x["kind"], x["change"], x.get("why", "below_zero"), x.get("marg_now"), x.get("shelf"), x.get("after")))
    for x in u:
        say("   unread   %-30s %-7s %+d  why=%s" % (x["item"], x["kind"], x["change"], x.get("why", "unread")))
    batches = SA._s446_batches(con, 1)
    ent = SA._s446_entered(con, 1)
    keys = [k for k in batches if k not in ent]
    hb, ub = SA._voucher_held_batches(con, 1, keys, batches)
    say("STATE %s: frozen batches not entered: %d; held among them: %d (%s); unreadable: %d" % (label, len(keys), len(hb), sorted(hb), len(ub)))
    sp = SW.Spine()
    cnt_names = sorted({r[0] for r in con.execute("SELECT item FROM stock_count_item WHERE count_id=1")})
    F = SH.figures(con, sp=sp, items=cnt_names)
    cnt = sum(1 for v in F.values() if v.get("shelf") is not None and v.get("named") not in ("no_count", "no_spine"))
    say("STATE %s: shelf figures over the count's %d names: %d with a figure, %d approx, %d below_zero, %d no_count; marg_as_on %s"
        % (label, len(cnt_names), cnt, sum(1 for v in F.values() if v.get("approx")), sum(1 for v in F.values() if v.get("named") == "below_zero"),
           sum(1 for v in F.values() if v.get("named") == "no_count"), sorted({str(v.get("marg_as_on")) for v in F.values()})))
    day, fl = SH.gap_flags(con)
    say("STATE %s: gap flags: newest set %s, %d flagged: %s" % (label, day, len(fl), ", ".join(x["item"] for x in fl)))
    rows = con.execute("SELECT day, item, reason, answered_at FROM stock_spot_roster WHERE day=(SELECT MAX(day) FROM stock_spot_roster) ORDER BY rank").fetchall()
    say("STATE %s: the roster's latest day %s, %d item(s):" % (label, rows[0][0] if rows else "-", len(rows)))
    for r in rows:
        say("   roster %-30s %s%s" % (r[1], r[2], "" if r[3] else "  (unanswered)"))
    sysrows = con.execute("SELECT 'stock_shelf_fix', item, at FROM stock_shelf_fix WHERE by_user='system' AND at>='2026-10-18' UNION ALL "
                          "SELECT 'stock_sales_test', item, at FROM stock_sales_test WHERE at>='2026-10-18' UNION ALL "
                          "SELECT 'stock_diff_lane', item, at FROM stock_diff_lane WHERE by_user='system' AND at>='2026-10-18'").fetchall()
    say("STATE %s: system-written desk rows on or after 2026-10-18: %d %s" % (label, len(sysrows), [tuple(r) for r in sysrows]))
    meta = con.execute("SELECT built_at, full_ms FROM stock_pile_cache_meta WHERE count_id=1").fetchone()
    say("STATE %s: stock_pile_cache_meta built_at %s (%s ms)" % (label, meta[0] if meta else None, meta[1] if meta else None))
    json.dump(dict(stage=st.get("stage"), pending=A.get("pending"), offered=sorted((x["item"], x["kind"], x["change"]) for x in o),
                   held=sorted((x["item"], x["kind"], x["change"]) for x in h), held_batches=sorted(str(k) for k in hb), sysrows=len(sysrows)),
              open(os.path.join(os.path.dirname(dbp), "state_%s.json" % label), "w"))
    con.rollback()
    say("STATE OK S577 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--old", "--portal", "--dump", "--old-dump", "--readings", "--spine-old"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S577_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not (a.old and a.portal and a.dump and a.readings and a.spine_old):
        ap.error("--old, --portal, --dump, --readings and --spine-old are needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S577 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import shelf_figure as SH                                 # noqa: E402
    import loss_piles as LP                                   # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    for m in (SA, SW, SH, LP, OR, PA):
        assert m.__file__.startswith(fin), m.__file__
    SF = None
    if os.path.exists(os.path.join(fin, "stock_figure.py")):
        import stock_figure as SF                             # noqa: E402
    SHO = load_old(os.path.join(os.path.abspath(a.old), "shelf_figure.py"), "shelf_figure_s577old")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none", "loaded" if SF else "ABSENT (old files)"))
    cl = fa.app.test_client(use_cookies=False)
    TIMES = []

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
    ctx = SF.Ctx(sqlite3.connect(dbp), sp) if SF else None
    today = dt.date.today().isoformat()
    cap = SF.capture_at(sp, None, ctx) if SF else None
    SC_ = {"con": None}

    def sc():
        if SC_["con"] is None:
            SC_["con"] = sqlite3.connect(spine_path)
        return SC_["con"]

    def sc_reopen():
        try:
            if SC_["con"] is not None:
                SC_["con"].close()
        except sqlite3.Error:
            pass
        SC_["con"] = None
    cap_md5 = cap["md5"] if cap else [r[0] for r in sc().execute("SELECT e.md5 FROM sp_export e WHERE e.md5 IN (SELECT md5 FROM sp_close_name) ORDER BY e.stamp DESC LIMIT 1")][0]

    # ============================================================================================ 0 the live state
    def s0():
        c = conn()
        st = SA.amir_stage(c, 1) or {}
        say("   count #1 stage %s; A %s; C entered %s/%s, lots %s, wrong %d" % (st.get("stage"), {k: st["A"].get(k) for k in ("total", "entered", "open", "pending")}, (st.get("C") or {}).get("entered"),
                                                                              (st.get("C") or {}).get("total"), (st.get("C") or {}).get("lots"), len((st.get("C") or {}).get("wrong") or [])))
        d = SA._pad_report_data(c, 1)
        o, h, u = SA._voucher_lines(c, d)
        say("   pending voucher lines: offered %d held %d unread %d; frozen batches not entered: %d" % (len(o), len(h), len(u), len([k for k in SA._s446_batches(c, 1) if k not in SA._s446_entered(c, 1)])))
        say("   provisional points: %s" % [tuple(r) for r in c.execute("SELECT id, item, at FROM stock_point WHERE status='provisional'")])
        say("   the newest three old gap sets (s454_shelf_gap): %s" % [tuple(r) for r in c.execute("SELECT as_on, COUNT(*), SUM(flagged) FROM s454_shelf_gap GROUP BY as_on ORDER BY as_on DESC LIMIT 3")])
        say("   stock_pile_cache_meta: %s" % [tuple(r)[:4] for r in c.execute("SELECT count_id, built_at, full_ms, last_partial_at FROM stock_pile_cache_meta")])
        rows = c.execute("SELECT 'stock_shelf_fix' t, item, at, by_user FROM stock_shelf_fix WHERE by_user='system' OR source='sales_test' UNION ALL SELECT 'stock_sales_test', item, at, '' FROM stock_sales_test "
                         "UNION ALL SELECT 'stock_point', item, at, by FROM stock_point WHERE source='sales_test' OR by='system' ORDER BY 3").fetchall()
        say("   rows by system / source sales_test: %d: %s" % (len(rows), [tuple(r) for r in rows]))
        today_rows = [r for r in rows if str(r[2]) >= "2026-10-18"]
        check("the 18-10 desk-row check (3.3 E): no system-written stock_shelf_fix / stock_sales_test / stock_point row dated 2026-10-18 or later", not today_rows, today_rows)
        caps = [dict(md5=r[0], as_on=r[1], stamp=r[2]) for r in sc().execute("SELECT e.md5, e.as_on, e.stamp FROM sp_export e WHERE e.md5 IN (SELECT md5 FROM sp_close_name) ORDER BY e.stamp DESC LIMIT 7")] if SF else []
        for x in caps:
            si = SF.stamp_iso(x["stamp"])
            say("   capture %s printed %s taken %s -> end of %s" % (x["md5"][:8], x["as_on"], si, SF.end_day(x["as_on"], si)))
        if SF:
            fams = {}
            for r in sc().execute("SELECT k20, name FROM sp_close_name WHERE md5=?", (cap_md5,)):
                fams.setdefault(r[0], set()).add(r[1])
            say("   families of the newest usable capture: %s" % {k: sorted(v) for k, v in fams.items() if len(v) > 1})
            two = [(r[0], r[1]) for r in sc().execute("SELECT name, COUNT(DISTINCT packing) FROM sp_close_name WHERE md5=? GROUP BY name HAVING COUNT(DISTINCT packing)>1", (cap_md5,))]
            say("   names printed with two packings in it: %d %s" % (len(two), two))
        c.close()
    section("0  the live state", s0)

    # ---- the walk's own item in the scratch spine and the finance copy (keyed by name W577 FIX TAB; nothing live) ----------------------
    def fixture():
        if not sc().execute("SELECT 1 FROM sp_item WHERE name=?", (FIX,)).fetchone():
            sc().execute("INSERT INTO sp_item VALUES (?,?,?,?,?,?)", (FIX, FIX, "1*10", "LOOSE", "2026-09-01", "2026-10-16"))
            if sc().execute("SELECT 1 FROM sqlite_master WHERE name='sp_close_name'").fetchone():
                sc().execute("INSERT INTO sp_close_name VALUES (?,?,?,?,?)", (cap_md5, FIX, "1*10", FIX, 90.0))
            sc().executemany("INSERT INTO sp_move VALUES (?,?,?,?,?)", [(FIX, "2026-10-13", "SALE", -20.0, "W577"), (FIX, "2026-10-15", "PURCHASE", 30.0, "W577/1"), (FIX, "2026-10-17", "PURCHASE", 50.0, "W577/2")])
            sc().commit()
        c = conn()
        SW.ensure(c)
        if not c.execute("SELECT 1 FROM stock_point WHERE item=? AND at='2026-10-12T19:00:00'", (FIX,)).fetchone():
            ins(c, "stock_point", dict(item_norm=FIX, item=FIX, at="2026-10-12T19:00:00", qty_units=100.0, source="spot", by="w577walk", expected_units=100.0, gap_units=0.0,
                                       status="settled", settled_at="2026-10-12T19:00:00", provisional_units=0, basis="shelf"))
            c.commit()
        c.close()
    fixture()
    # the fixture's figures: closing 90 at the end of 16-10; marg = 90 + 50 = 140; shelf = 100 - 20 + 30 + 50 = 160 (base 12-10: its sales in, purchases after)

    # ============================================================================================ 1 a renamed item is judged
    def s1():
        c = conn()
        G = SA._voucher_guard_base(c, 1)
        g = SA._voucher_guard(G, "KNEE SUPPORT HINGED L", -1)     # the voucher lines carry the OLD name; Marg prints KNEE SUPPORT L HINGED
        check("C: KNEE SUPPORT HINGED L (renamed; the voucher's name) is judged by the guard -- a closing is read (not 'not readable')",
              g.get("unread") is False and g.get("marg_now") is not None, g)
        m = SF.marg(c, sp, "KNEE SUPPORT HINGED L", None, ctx) if SF else None
        check("C: ... and its figure is approx=True (four sizes under one key: %s)" % ([x[0] for x in (m or {}).get("family") or []]), bool(m and m["approx"] and len(m["family"]) == 4), m)
        v = SF.marg(c, sp, "VINTAZ P 4500 INJ", None, ctx) if SF else None
        check("C: VINTAZ P 4500 INJ (renamed to VINTAZ P 4500, no other size under its key) is NOT approx; its closing read by name", bool(v and not v["approx"] and v["closing"]["by"] == "name"),
              (v or {}).get("closing"))
        c.close()
    section("1  a renamed item is judged (F-874)", s1)

    # ============================================================================================ 2 the Yuvika immobilizer line
    def s2():
        c = conn()
        r = c.execute("SELECT l.id, l.item, l.billed_bill_no, l.arrived_at FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id WHERE l.item='KNEE IMMOBILIZER UNISON L' "
                      "AND o.vendor LIKE 'YUVIKA%' AND l.arrived_at LIKE '2026-10-01%'").fetchone()
        check("the 01-Oct Yuvika immobilizer arrival is on the copy (by item, vendor and day)", r is not None, r)
        if r:
            c.execute("UPDATE purchase_order_line SET billed_bill_no='' WHERE id=?", (r["id"],))     # the tie blanked on the copy: the spine must answer it
            c.commit()
        lines = SW.bill_pending_lines(c, sp=sp)
        hit = [l for l in lines if l["item"] == "KNEE IMMOBILIZER UNISON L"]
        check("C: with its tie blanked, the line is NOT 'bill entry baaki' (the spine's purchase under the family key, by key_of)", not hit, [l["text"] for l in hit])
        say("   bill-entry-pending lines now: %d %s" % (len(lines), [(l["item"], l["date"]) for l in lines][:6]))
        c.close()
    section("2  bill entry baaki by identity (F-873)", s2)

    # ============================================================================================ 3 the past-the-shelf test
    def s3():
        c = conn()
        G = SA._voucher_guard_base(c, 1)
        gets = {}
        for ch, fr, unk in ((-40, False, 0), (15, False, 0), (0, True, 20), (40, False, 0), (50, False, 0)):
            G2 = dict(G, unkeyed=dict(G.get("unkeyed") or {}, **{FIX: unk}), not_judged=set())
            gets[(ch, fr)] = SA._voucher_guard(G2, FIX, ch if ch else -0, frozen=fr, pack=10) if not fr else SA._voucher_guard(G2, FIX, 20, frozen=True, pack=10)
        g = gets[(-40, False)]
        check("C: an ISSUE line overshooting the shelf by two packs is HELD with why=past_shelf (Marg 140 - 40 = 100 against the shelf 160, tol 10)",
              g.get("held") and g.get("why") == "past_shelf" and g.get("after") == 100.0 and g.get("shelf") == 160.0, g)
        g = gets[(15, False)]
        check("C: a line within the tolerance is offered (Marg 140 + 15 = 155 against 160, tol 10): judged against the shelf, not held", g.get("judged_shelf") and not g.get("held"), g)
        g = gets[(0, True)]
        check("C: a FROZEN batch line landing exactly on the shelf is NOT held (its +20 already inside unkeyed: 140 + 20 = 160)", g.get("judged_shelf") and not g.get("held") and g.get("after") == 160.0, g)
        g = gets[(40, False)]
        check("C: a RECEIVE line overshooting is HELD (140 + 40 = 180 > 160 + 10)", g.get("held") and g.get("why") == "past_shelf", g)
        g = gets[(50, False)]
        check("C: an item with a late-keyed bill (the residual 30 = the purchase of 15-10) is 'not judged against the shelf'", not g.get("held") and not g.get("judged_shelf") and g.get("marg_now") is not None, g)
        c.close()
    section("3  the past-the-shelf test (D715 a)", s3)

    # ============================================================================================ 4 the capture rule (unchanged)
    def s4():
        E = SF.end_day if SF else SA._s524_end_day
        S_ = SF.stamp_iso if SF else SA._s524_stamp_iso
        check("capture rule: printed 17-10, taken 18-10 05:17 -> the end of 17-10", E("2026-10-17", S_("20261018-051700")) == "2026-10-17")
        check("capture rule: printed 18-10, taken 09:37 -> unusable", E("2026-10-18", S_("20261018-093708")) is None)
        check("capture rule: printed 18-10, taken 22:30 -> the end of 18-10", E("2026-10-18", S_("20261018-223000")) == "2026-10-18")
        check("capture rule: the 06:00 capture printed 07-10 on 08-10 stands for the end of 07-10; the 09:54 one printed 08-10 is unusable",
              E("2026-10-07", S_("20261008-060018")) == "2026-10-07" and E("2026-10-08", S_("20261008-095436")) is None)
        if SF:
            cf = SF.capture_for(sp, "2026-10-07", ctx)
            check("the one choice rule: the capture standing for the end of 07-10 is the 06:00 one (63b8e3fb)", cf and cf["md5"].startswith("63b8e3fb"), cf)
            c10 = SF.capture_for(sp, "2026-10-10", ctx)
            check("the one choice rule: four captures stand for the end of 10-10; the newest by stamp (10:35, 76eb46af) is chosen", c10 and c10["md5"].startswith("76eb46af") and c10["stamp"] == "20261011-103520", c10)
            check("the newest usable capture today is the one printed 16-10, taken 17-10 09:20 (the 18-10 09:37 one is unusable)", cap["md5"].startswith("7f4d5832") and cap["end_day"] == "2026-10-16", cap)
        say("   (the rule is the same on both files: printed, not a red/green control)")
    section("4  the capture rule (charter 11, unchanged)", s4)

    # ============================================================================================ 5 the desk only reads
    def s5():
        before = table_counts(dbp)
        s, h = GET("manoj", "/finance/stock/api/loss/1/piles?lite=1")
        j = json.loads(h) if s == 200 else {}
        b1 = (j.get("cache") or {}).get("built")
        mid = table_counts(dbp)
        moved = sorted(t for t in mid if mid[t] != before.get(t))
        check("the first read of the piles builds the cache once (status %s, built=%s)" % (s, b1), s == 200 and b1 in ("full", "cache", "partial"), (s, b1))
        check("that build wrote nothing outside stock_pile_cache / stock_pile_cache_meta (tables whose row count moved: %s)" % moved,
              set(moved) <= {"stock_pile_cache", "stock_pile_cache_meta"}, moved)
        # the spine rebuilt from the SAME inputs (a new file, a new mtime)
        pr = subprocess.run([sys.executable, "-B", "spine_build.py", "--readings", os.path.abspath(a.readings), "--out", spine_path, "--finance-db", dbp], cwd=os.path.join(fin, "spine"),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        check("the scratch spine rebuilt from the same inputs (rc %d)" % pr.returncode, pr.returncode == 0 and "SWAPPED" in pr.stdout, pr.stdout[-300:])
        sc_reopen()                                                # the rebuild replaced the file: a fresh connection
        fixture()                                                  # the rebuild made a fresh spine: the walk's own rows again
        s, h = GET("manoj", "/finance/stock/api/loss/1/piles?lite=1")
        j = json.loads(h) if s == 200 else {}
        b2 = (j.get("cache") or {}).get("built")
        after = table_counts(dbp)
        moved2 = sorted(t for t in after if after[t] != mid.get(t))
        check("C: the second read after a same-inputs rebuild does NOT rebuild (built=%s) and writes nothing: one build across the two reads (tables moved: %s)" % (b2, moved2),
              s == 200 and b2 == "cache" and not moved2, (s, b2, moved2))
        # a new export forces one build, again with no outside write
        sc().execute("INSERT INTO sp_export VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("w577" + "0" * 28, "W577_NEW_EXPORT.XLS", "SALE_BILLWISE", "20991231-235959", "2099-12-31", "2099-12-31", "", 1, "[]", "READ", ""))
        sc().commit()
        s, h = GET("manoj", "/finance/stock/api/loss/1/piles?lite=1")
        j = json.loads(h) if s == 200 else {}
        b3 = (j.get("cache") or {}).get("built")
        last = table_counts(dbp)
        moved3 = sorted(t for t in last if last[t] != after.get(t))
        check("a new export in the spine forces one build (built=%s), with no write outside the two cache tables (%s)" % (b3, moved3), s == 200 and b3 == "full" and set(moved3) <= {"stock_pile_cache", "stock_pile_cache_meta"}, (s, b3, moved3))
        sc().execute("DELETE FROM sp_export WHERE md5=?", ("w577" + "0" * 28,))        # the walk's own row on the scratch spine
        sc().commit()
        s, h = GET("manoj", "/finance/stock/api/loss/1/piles")
        j = json.loads(h) if s == 200 else {}
        scl = j.get("system_closed")
        check("C: the Loss desk carries the owner's line about the two system closings of 27-09 (system_closed)", bool(scl) and scl.get("n") == 2 and "DOLOGESIC SP" in (scl.get("text") or "") and "yours to decide" in (scl.get("text") or ""), scl)
        say("   %s" % ((scl or {}).get("text") or "(no system_closed line)"))
        c = conn()
        # a line that sales_test would have CLOSED: an open shortage whose sales since the count day exceed counted + bought. Every shortage of
        # count #1 is written off today, so the line is the walk's own (a synthetic open line of ONKET DT; its sale of 500 strips on the scratch spine)
        picked = "ONKET DT"
        k = SF.key_of(sp, picked, ctx) if SF else sp.key(picked)
        sc().execute("INSERT INTO sp_move VALUES (?,?,?,?,?)", (k, "2026-10-17", "SALE", -5000.0, "W577SALE"))   # a sale beyond anything counted, on the scratch spine
        sc().execute("INSERT INTO sp_sale_line VALUES (?,?,?,?,?,?,?,?,?,?,?)", ("2026-10-17", "W577SALE", 1, picked[:20], k, "1*10", "500:0", 5000.0, 100, "", ""))
        sc().commit()
        C_ = LP._ctx(c, 1)
        x = dict(item=picked, diff=-50, counted=50, marg=100, pack=10, packing="1*10", word=None, swapped=0, mrp_p=-5000, cost_p=-3000, life=None)
        kind, line = LP._classify_one(c, x, C_)
        why = (line or {}).get("why") or ""
        check("C: an open shortage that sold more since the count than was counted + bought (%s: the walk's own sale of 500 strips) stays OPEN in its pile, its why 'sold after count: ...'" % picked,
              kind == "line" and why.startswith("sold after count:") and (line or {}).get("bucket") not in ("back", "written_off", None) and bool((line or {}).get("sold_after")),
              (kind, (line or {}).get("bucket"), why[:200]))
        say("   %s" % why[:220])
        n_fix0 = c.execute("SELECT COUNT(*) FROM stock_shelf_fix").fetchone()[0]
        n_tst0 = c.execute("SELECT COUNT(*) FROM stock_sales_test").fetchone()[0]
        GET("manoj", "/finance/stock/api/loss/1/piles?rebuild=1&lite=1")
        check("a full rebuild of the desk with that sale in the spine writes no stock_shelf_fix / stock_sales_test row (the desk only reads)",
              c.execute("SELECT COUNT(*) FROM stock_shelf_fix").fetchone()[0] == n_fix0 and c.execute("SELECT COUNT(*) FROM stock_sales_test").fetchone()[0] == n_tst0)
        sc().execute("DELETE FROM sp_move WHERE ref='W577SALE'")
        sc().execute("DELETE FROM sp_sale_line WHERE bill='W577SALE'")
        sc().commit()
        GET("manoj", "/finance/stock/api/loss/1/piles?rebuild=1&lite=1")
        c.close()
    section("5  the desk only reads (F-841)", s5)

    # ============================================================================================ 6 settling and correcting points
    def s6():
        c = conn()
        SW.ensure(c)
        # a provisional point of 17-10 (150 counted, 30 provisional): re-judged against the base BEFORE it (the 12-10 point: 100 - 20 + 30 + 50 = 160)
        pid = ins(c, "stock_point", dict(item_norm=FIX, item=FIX, at="2026-10-17T19:00:00", qty_units=150.0, source="spot", by="w577walk", expected_units=None, gap_units=None,
                                         status="provisional", provisional_units=30.0, basis="shelf"))
        c.commit()
        SW.settle_provisional(c, sp)
        r = c.execute("SELECT status, expected_units, gap_units, basis FROM stock_point WHERE id=?", (pid,)).fetchone()
        check("C: a shelf-basis provisional point is settled on the SHELF basis against the base before it (expected 160, gap -10, basis shelf)",
              r and r[0] == "settled" and r[1] == 160.0 and r[2] == -10.0 and r[3] == "shelf", tuple(r) if r else None)
        # a corrected spot count keeps its basis (the settled 17-10 point, 150, is now the newest base; nothing moved after it)
        rid = ins(c, "stock_spot_roster", dict(day=today, item_norm=FIX, item=FIX, reason="W577", reason_hi="W577", rank=99, asked_at=today + "T06:30:00", pack=10, packing="1*10", carried=0))
        c.commit()
        ok, msg, code, P = SW.answer_roster(c, rid, 158, "w577walk", sp=sp)
        check("the walk's spot answer is written on the shelf basis (basis %s, expected %s = the newest base 150)" % ((P or {}).get("basis"), (P or {}).get("expected")),
              ok and P and P.get("expected") == 150.0 and P.get("basis") == "shelf", (ok, msg))
        ok2, msg2, code2, P2 = SW.correct_roster(c, rid, 157, "w577walk", sp=sp)
        b2 = c.execute("SELECT basis, expected_units FROM stock_point WHERE id=?", (P2["id"],)).fetchone() if (ok2 and P2) else None
        check("C: a corrected spot count keeps its basis (shelf) and is judged on the old point's figure (150)", ok2 and b2 and b2[0] == "shelf" and b2[1] == 150.0, (ok2, msg2, tuple(b2) if b2 else None))
        # an approx point: a size that shares a family figure
        rid2 = ins(c, "stock_spot_roster", dict(day=today, item_norm=SW.norm_name("KNEE SUPPORT L HINGED"), item="KNEE SUPPORT L HINGED", reason="W577", reason_hi="W577", rank=98,
                                                asked_at=today + "T06:30:00", pack=1, packing="1*1", carried=0))
        c.commit()
        n_loss0 = c.execute("SELECT COUNT(*) FROM stock_watch_loss_line").fetchone()[0]
        n_tr0 = c.execute("SELECT COUNT(*) FROM stock_trace").fetchone()[0]
        ok3, msg3, code3, P3 = SW.answer_roster(c, rid2, 1, "w577walk", sp=sp)
        row = c.execute("SELECT expected_units, gap_units, basis FROM stock_point WHERE id=?", (P3["id"],)).fetchone() if (ok3 and P3) else None
        check("C: an approx point stores NULL expected and NULL gap with basis 'approx'", ok3 and row and row[0] is None and row[1] is None and row[2] == "approx", tuple(row) if row else (ok3, msg3))
        check("C: ... its receipt is the plain 'Likh liya: KNEE SUPPORT L HINGED — 1 nag.' with no verdict", ok3 and msg3 == "Likh liya: KNEE SUPPORT L HINGED — 1 nag." and (P3 or {}).get("verdict_hi") == "", msg3)
        check("C: ... no loss line and no trace were opened for it", c.execute("SELECT COUNT(*) FROM stock_watch_loss_line").fetchone()[0] == n_loss0 and c.execute("SELECT COUNT(*) FROM stock_trace").fetchone()[0] == n_tr0)
        ym = today[:7]
        L = SW.month_leak(c, ym, sp=sp) or {}
        pts = c.execute("SELECT COUNT(*) FROM stock_point WHERE substr(at,1,7)=? AND gap_units<0 AND source<>'full_count' AND status<>'superseded' AND item='KNEE SUPPORT L HINGED'", (ym,)).fetchone()[0]
        check("C: the approx point is absent from the month's leakage (no negative gap row of it; month_leak reads)", pts == 0 and isinstance(L, dict), (pts, L.get("text")))
        ok4, msg4, code4, P4 = SW.correct_roster(c, rid2, 2, "w577walk", sp=sp)
        row4 = c.execute("SELECT expected_units, gap_units, basis FROM stock_point WHERE id=?", (P4["id"],)).fetchone() if (ok4 and P4) else None
        check("C: a corrected approx point stays approx (NULL figure, no verdict)", ok4 and row4 and row4[2] == "approx" and row4[1] is None and msg4 == "Badal diya: KNEE SUPPORT L HINGED — 2 nag.", (msg4, tuple(row4) if row4 else None))
        ok5, msg5, code5, R5 = SW.gadbad(c, "KNEE SUPPORT L HINGED", "W577 walk: kuchh gadbad", "w577walk", qty_units=1, sp=sp)
        check("C: 'Kuchh gadbad hai' on an approx item records the text and opens NO trace", ok5 and R5 and R5.get("trace") is None and c.execute("SELECT COUNT(*) FROM stock_trace").fetchone()[0] == n_tr0, (msg5, (R5 or {}).get("trace")))
        say("   renderers of verdict_hi for an approx point: answer_roster -> %r; correct_roster -> %r; darpan_view traces -> none (no trace); the stockmatch page prints the roster's qty_hi only" % (msg3, msg4))
        # the owner's watch card line
        V = SW.owner_view(c, 1)
        check("C: the owner's watch card carries the English line for the approx count ('counted N against a family figure (approximate) -- not judged')",
              any("against a family figure (approximate)" in x for x in (V.get("approx_lines") or [])), V.get("approx_lines"))
        c.close()
    section("6  settling and correcting points on their basis", s6)

    # ============================================================================================ 7 shelf figures and the order plan
    def s7():
        c = conn()
        as_on, snap = PA._latest_snapshot(c)
        names = sorted({s["item"] for s in snap.values()} | {r[0] for r in c.execute("SELECT item FROM stock_count_item WHERE count_id=1")})
        Fn = SH.figures(c, sp=sp, items=names)
        Fo = SHO.figures(c, sp=sp, items=names)
        nc_old = [n for n in names if Fo.get(n, {}).get("named") == "no_count"]
        nc = [n for n in nc_old if Fn.get(n, {}).get("named") == "no_count"]
        now_counted = [n for n in nc_old if Fn.get(n, {}).get("named") != "no_count"]
        check("C: an item with no count has NO shelf figure (shelf=None, named='no_count') -- %d such items, e.g. %s" % (len(nc), nc[:3]),
              bool(nc) and all(Fn[n]["shelf"] is None for n in nc) and all(Fo[n]["shelf"] is not None for n in nc), [(n, Fn[n]["shelf"], Fn[n]["named"], Fo[n]["shelf"]) for n in nc[:4]])
        say("   renamed items that now reach their count under the old name (no_count before, a shelf figure now): %d %s" % (len(now_counted), [(n, Fn[n]["shelf"]) for n in now_counted]))
        new_snap, old_snap = OR._s454_shelf_snap(c, snap), snap
        nc_keys = [k for k, s in snap.items() if s["item"] in nc]
        check("the plan's lines for no-count items are equal before and after (qty unchanged, no marg_qty laid over) -- %d lines" % len(nc_keys),
              all(new_snap[k]["qty"] == old_snap[k]["qty"] and "marg_qty" not in new_snap[k] for k in nc_keys))
        say("   the plan's lines that change: the %d renamed items above (a shelf figure now stands in for Marg's)" % len([k for k, s in snap.items() if s["item"] in now_counted]))
        moved = []
        for n in names:
            o, nw = Fo.get(n) or {}, Fn.get(n) or {}
            if o.get("named") in ("no_count", "no_spine") or nw.get("named") == "no_count":
                continue
            if o.get("shelf") != nw.get("shelf"):
                why = []
                if nw.get("approx") != o.get("approx"):
                    why.append("family %s -> %s" % (o.get("approx"), nw.get("approx")))
                if o.get("marg_as_on") != nw.get("marg_as_on"):
                    why.append("Marg's closing %s -> %s (the usable capture)" % (o.get("marg_as_on"), nw.get("marg_as_on")))
                if (o.get("boundary") or 0) != (nw.get("boundary") or 0):
                    why.append("boundary %s -> %s" % (o.get("boundary"), nw.get("boundary")))
                if (o.get("arrived") or 0) != (nw.get("arrived") or 0):
                    why.append("arrived %s -> %s" % (o.get("arrived"), nw.get("arrived")))
                if abs((o.get("sold") or 0) - (nw.get("sold") or 0)) > 0.01 or abs((o.get("bought") or 0) - (nw.get("bought") or 0)) > 0.01:
                    why.append("movements by key_of / share (sold %s->%s, bought %s->%s)" % (o.get("sold"), nw.get("sold"), o.get("bought"), nw.get("bought")))
                moved.append((n, o.get("shelf"), nw.get("shelf"), "; ".join(why) or "the base (a superseded point no longer read)"))
        say("   counted items whose shelf figure moves: %d" % len(moved))
        for n, o, nw, why in moved[:60]:
            say("   moved  %-30s %6s -> %6s  %s" % (n, o, nw, why))
        json.dump(moved, open(os.path.join(a.dump, "shelf_moved.json"), "w"))
        c.close()
    section("7  shelf figures and the order plan", s7)

    # ============================================================================================ 8 identity and stage verdicts
    def s8():
        c = conn()
        items = sorted({r[0] for r in c.execute("SELECT DISTINCT l.item FROM stock_voucher_line l WHERE l.count_id=1 AND NOT EXISTS (SELECT 1 FROM stock_voucher_void v WHERE v.count_id=l.count_id AND v.round_no=l.round_no AND v.kind=l.kind AND v.batch_no=l.batch_no)")})

        def old_key(item):                                     # the old _s524_key_of: sp_item's k20 for the exact name, else sp.key
            r = sp.q("SELECT DISTINCT k20 FROM sp_item WHERE name=?", item)
            return str(r[0]["k20"]) if r else sp.key(item)
        diff = [(it, old_key(it), SA._s524_key_of(sp, it, {})) for it in items if old_key(it) != SA._s524_key_of(sp, it, {})]
        check("key_of equals the old key for every item of the %d voucher lines' %d items (all 37 non-void batches)" % (c.execute("SELECT COUNT(*) FROM stock_voucher_line WHERE count_id=1").fetchone()[0], len(items)), not diff, diff[:5])
        st = SA.amir_stage(c, 1) or {}
        AP = (st.get("A") or {}).get("proof") or {}
        say("   stage %s; A proof %s (as_after %s, rows %d); C wrong %d: %s" % (st.get("stage"), AP.get("state"), AP.get("as_after"), len(AP.get("rows") or []), len((st.get("C") or {}).get("wrong") or []),
                                                                             sorted(r["item"] for r in (st.get("C") or {}).get("wrong") or [])))
        json.dump(dict(stage=st.get("stage"), A=AP.get("state"), A_rows=sorted(r["item"] for r in AP.get("rows") or []), C_wrong=sorted(r["item"] for r in (st.get("C") or {}).get("wrong") or [])),
                  open(os.path.join(a.dump, "stage.json"), "w"))
        if a.old_dump and os.path.exists(os.path.join(a.old_dump, "stage.json")):
            o = json.load(open(os.path.join(a.old_dump, "stage.json")))
            check("stages A and C give identical verdicts on the old and the new files", o == dict(stage=st.get("stage"), A=AP.get("state"), A_rows=sorted(r["item"] for r in AP.get("rows") or []),
                                                                                             C_wrong=sorted(r["item"] for r in (st.get("C") or {}).get("wrong") or [])), o)
        c.close()
    section("8  identity and the stage verdicts", s8)

    # ============================================================================================ 9 the gap sets
    def s9():
        n0, h0 = gap_hash(dbp)
        c = conn()
        rows0 = [(r[0], r[1], r[2]) for r in c.execute("SELECT day, item, reason FROM stock_spot_roster WHERE day=(SELECT MAX(day) FROM stock_spot_roster WHERE day<?) ORDER BY rank", (today,))]
        say("   the roster's reasons BEFORE (the live roster's latest day): %s" % rows0)
        n = SH.record_gaps(c, sp)
        sets = [tuple(r) for r in c.execute("SELECT end_day, capture_md5, COUNT(*), SUM(flagged), SUM(approx) FROM s577_shelf_gap GROUP BY end_day")] if c.execute("SELECT 1 FROM sqlite_master WHERE name='s577_shelf_gap'").fetchone() else []
        R = SF.reach(sp) if SF else {}
        covered = sorted({x["end_day"] for x in SF.usable_captures(sp, ctx) if SF.tryable(x, R)[0]}) if SF else []
        check("C: the first pass writes ONE s577_shelf_gap set (%d rows) for the newest covered end day %s from its usable capture" % (n, covered[-1:] if covered else None),
              len(sets) == 1 and n > 300 and sets[0][0] == (covered[-1] if covered else None) and sets[0][1] == cap_md5, sets)
        prev = [x for x in SF.usable_captures(sp, ctx) if x["end_day"] < sets[0][0]][-1] if (SF and sets) else None
        say("   judged against the usable capture before it: %s (end of %s, taken %s)" % ((prev or {}).get("md5", "")[:8], (prev or {}).get("end_day"), (prev or {}).get("stamp_iso")))
        fl = [tuple(r) for r in c.execute("SELECT item, shelf, marg, gap, marg_move, voucher, why FROM s577_shelf_gap WHERE flagged=1 ORDER BY item")] if sets else []
        say("   flagged in the first new set: %d %s" % (len(fl), [f[0] for f in fl]))
        for f in fl[:40]:
            say("   flag %-30s shelf %s marg %s gap %s move %s vch %s -- %s" % f)
        oldset = [tuple(r) for r in c.execute("SELECT item FROM s454_shelf_gap WHERE as_on=(SELECT MAX(as_on) FROM s454_shelf_gap) AND flagged=1 ORDER BY item")]
        say("   flagged in the newest OLD set (%s): %d; of them flagged in the new set: %s" % (c.execute("SELECT MAX(as_on) FROM s454_shelf_gap").fetchone()[0], len(oldset), [o[0] for o in oldset if o[0] in {f[0] for f in fl}]))
        n2 = SH.record_gaps(c, sp)
        check("C: a second pass writes nothing", n2 == 0 and n > 0, n2)
        n1, h1 = gap_hash(dbp)
        check("s454_shelf_gap's row count and content hash are unchanged (%d rows, %s)" % (n0, h0), (n0, h0) == (n1, h1), (n1, h1))
        # the roster's reasons after: a fresh roster for the walk's own day (force=True) on the copy, its reasons printed
        S_ = SW.settings(c)
        Rv = SW.build_roster(c, dt.date.today() + dt.timedelta(days=1), S_, sp, who="w577walk", force=True)
        say("   the roster's reasons AFTER (a forced roster for tomorrow on the copy): %s" % [(x["item"], x["reason"]) for x in Rv.get("items") or []])
        c.close()
    section("9  the gap sets (R2-B6)", s9)

    # ============================================================================================ 10 the past_shelf sentence
    def s10():
        c = conn()
        st = SA.amir_stage(c, 1) or {}
        st2 = json.loads(json.dumps(dict(st, stage="C"), default=str))
        st2["C"] = dict(st2.get("C") or {}, held=[dict(item=FIX, change=-40, packing="1*10", pack=10, marg_now=90.0, as_on="2026-10-16", taken="2026-10-17T09:20:35", unkeyed=0,
                                                         shelf=160.0, after=100.0, why="past_shelf", key=(2, "ISSUE", 1), seq=7)], wrong=[], waiting_export=[], open=0, not_shelf=3, unread=1)
        sw = SA._s521_stage_words(c, st2)
        lines = [l["text"] for l in sw.get("owner_lines") or []]
        hit = [l for l in lines if FIX in l]
        check("C: a past_shelf held line prints the past_shelf sentence ('it would take Marg to 10 strips against the shelf figure 16 strips (closing of 16-10, taken 09:20): not given to Amir')",
              bool(hit) and "it would take Marg to 10 strips against the shelf figure 16 strips (closing of 16-10, taken 09:20): not given to Amir" in hit[0] and "holds" not in hit[0], hit)
        check("C: the summary gains 'not judged against the shelf for 3 item(s) (a family figure, no count, goods not yet billed, or a bill keyed after the closing)'",
              any("not judged against the shelf for 3 item(s) (a family figure, no count, goods not yet billed, or a bill keyed after the closing)" in l for l in lines), lines[-3:])
        check("the existing 'closing not readable for 1 item(s)' line stays beside it", any("closing not readable for 1 item(s)" in l for l in lines))
        st3 = json.loads(json.dumps(dict(st, stage="C"), default=str))
        st3["C"] = dict(st3.get("C") or {}, held=[dict(item=FIX, change=-40, packing="1*10", pack=10, marg_now=None, as_on=None, unkeyed=0, why="not_ready", key=(2, "ISSUE", 1), seq=7)], wrong=[], waiting_export=[], open=0)
        lines3 = [l["text"] for l in (SA._s521_stage_words(c, st3) or {}).get("owner_lines") or []]
        check("C: a not_ready held line prints 'held: the spine's closing table is not ready yet'", any("held: the spine's closing table is not ready yet" in l for l in lines3), lines3[:3])
        c.close()
    section("10 the owner's words", s10)

    # ============================================================================================ 11 install order
    def s11():
        c = conn()
        spo = SW.Spine(os.path.abspath(a.spine_old))
        check("the OLD builder's scratch spine opens and has no sp_close_name", spo.ok and not spo.q("SELECT 1 AS x FROM sqlite_master WHERE name='sp_close_name'"))
        if SF:
            ctx_o = SF.Ctx(c, spo)
            check("C: ready() is False while sp_close_name is absent", SF.ready(spo) is False)
            G = SA._voucher_guard_base(c, 1, ctx=ctx_o)
            g = SA._voucher_guard(G, "TYRO BR", -1)
            check("C: every lowering line is then HELD with why='not_ready' (never offered)", g.get("held") and g.get("why") == "not_ready", g)
            g2 = SA._voucher_guard(G, "TYRO BR", 5)
            check("C: a raising line is not held while not ready (nothing to judge it against)", not g2.get("held"), g2)
            n_before = c.execute("SELECT COUNT(*) FROM s577_shelf_gap").fetchone()[0] if c.execute("SELECT 1 FROM sqlite_master WHERE name='s577_shelf_gap'").fetchone() else 0
            n = SH.record_gaps(c, spo)
            n_after = c.execute("SELECT COUNT(*) FROM s577_shelf_gap").fetchone()[0]
            check("C: record_gaps writes nothing while ready() is False (%d rows, 0 written)" % n, n == 0 and n_after == n_before, (n, n_before, n_after))
        else:
            check("C: ready() is False while sp_close_name is absent", False, "stock_figure absent")
            check("C: every lowering line is then HELD with why='not_ready' (never offered)", False, "stock_figure absent")
            check("C: a raising line is not held while not ready (nothing to judge it against)", False, "stock_figure absent")
            check("C: record_gaps writes nothing while ready() is False (%d rows, 0 written)" % 0, False, "stock_figure absent")
        c.close()
    section("11 install order (sp_close_name absent)", s11)

    # ============================================================================================ 12 absent from a full capture
    def s12():
        c = conn()
        cl_ = SF.closing(c, sp, "PREDNOSIS 8", None, ctx) if SF else None
        check("C: PREDNOSIS 8 (counted, not printed in the capture, known to sp_item since %s) reads units=0 by='absent'" % ((cl_ or {}).get("as_on")), bool(cl_) and cl_["units"] == 0 and cl_["by"] == "absent", cl_)
        printed = {r[0] for r in sc().execute("SELECT name FROM sp_close_name WHERE md5=?", (cap_md5,))} if SF else set()
        absent = [r[0] for r in c.execute("SELECT item FROM stock_count_item WHERE count_id=1 ORDER BY item") if r[0] not in printed] if SF else []
        changed = []
        for n in absent:
            E = SW._s454_expected(c, sp, n)
            old = "Marg mein yeh item nahi mila -- ginti likh li" if (E.get("expected") is None and E.get("basis") != "approx") else ("(no verdict: approx)" if E.get("basis") == "approx" else "a verdict against %s (basis %s)" % (E.get("expected"), E.get("basis")))
            changed.append((n, E.get("basis"), E.get("expected"), old))
        say("   items absent from the capture (count names): %d; what a spot count of each would be judged against now:" % len(absent))
        for x in changed:
            say("   absent %-30s basis=%-7s expected=%-8s -> %s" % x)
        c.close()
    section("12 absence, named (R2-C4)", s12)

    # ============================================================================================ 13 the grep tests
    def s13():
        src = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in ("stock_app.py", "shelf_figure.py", "stock_watch.py", "loss_piles.py")}
        check("C: no 'def latest_snapshot' in shelf_figure.py", "def latest_snapshot" not in src["shelf_figure.py"])
        bodies = [fn_body(src["shelf_figure.py"], n) for n in ("figures", "record_gaps", "count_family", "points", "scan_arrivals")] + \
                 [fn_body(src["stock_app.py"], n) for n in ("_voucher_guard_base", "api_now", "api_drift")] + [fn_body(src["stock_watch.py"], n) for n in ("expected_units", "bill_pending_lines", "_arrivals")]
        check("no 'stock_snapshot' inside the moved readers (2.1 a rows 1-7)", all("stock_snapshot" not in b for b in bodies) and all(bodies), [i for i, b in enumerate(bodies) if not b or "stock_snapshot" in b])
        check("C: no 'sp.key(' in bill_pending_lines, _arrivals, scan_arrivals", all("sp.key(" not in fn_body(src["stock_watch.py"], n) for n in ("bill_pending_lines", "_arrivals")) and "sp.key(" not in fn_body(src["shelf_figure.py"], "scan_arrivals"))
        rule_files = [n for n in src if 'hm >= "22:00"' in src[n]]
        check("C: no second definition of the capture rule or the stamp parser (the rule lives in stock_figure.py only)", not rule_files and all(r'^\d{8}-\d{6}$' not in src[n] for n in src), rule_files)
        check("C: no 'sales_test(' call left", all(not re.search(r"(?<![A-Za-z_])sales_test\(", src[n]) for n in src))
        check("C: no '_s524_capture'", all("_s524_capture" not in src[n] for n in src))
        check("C: no 's454_shelf_gap' read anywhere in the four files (a record, read by nothing)", all("s454_shelf_gap" not in src[n] for n in src))
        check("C: dead code gone: no '_voucher_held(' and no 'latest_close_day'", all("_voucher_held(" not in src[n] and "latest_close_day" not in src[n] for n in src))
        check("_voucher_void is kept (the kit-only void door, S537 / S539)", "def _voucher_void(" in src["stock_app.py"])
        others = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in ("porders_s454.py", "order_sheet.py", "order_rules.py", "stockmatch.py", "amir_day.py")}
        check("no file outside the kit reads s454_shelf_gap or latest_snapshot of shelf_figure", all("s454_shelf_gap" not in t and "shelf_figure.latest_snapshot" not in t for t in others.values()))
    section("13 the grep tests (charter 2, 9)", s13)

    # ============================================================================================ 14 staff-eye
    def s14():
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u in %r: out[u]=[t['name'] for g, ts in po._visible_sections('staff', False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, list(STAFF)))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w577-walk-only", PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        check("staff-eye: each portal home renders its tiles for %s (the real portal.py + the grants file, a walk-only secret)" % ", ".join(STAFF), bool(tiles) and all(tiles.get(u) for u in STAFF),
              (tiles and {u: len(v) for u, v in tiles.items()}, pp.stdout[-200:]))
        say("   tiles: %s" % {u: v for u, v in tiles.items()})
        pages = [("amir", "/finance/amir", True), ("amir", "/finance/stock/api/pad/amir/1", False), ("amir", "/finance/amir/step/1", False), ("amir", "/finance/amir/step/7", False),
                 ("darpan", "/finance/stockmatch", False), ("darpan", "/finance/stockmatch/api/state", False), ("darpan", "/finance/darpan/kal", True),
                 ("shavez", "/finance/reports/aaj", True), ("reception", "/finance/porders", True),
                 ("manoj", "/finance/stock/page/hub?count=1", False), ("manoj", "/finance/stock/api/pad/hub/1", False), ("manoj", "/finance/stock/api/loss/1/piles?lite=1", False),
                 ("manoj", "/finance/stock/api/now", False), ("manoj", "/finance/stock/api/drift", False), ("manoj", "/finance/sanjeevni/api/needs-you", False)]
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
                    for l in gone[:6]:
                        say("      - %s" % l[:220])
                    for l in new[:6]:
                        say("      + %s" % l[:220])
                else:
                    say("   words unchanged on %s for %s" % (path, u))
        say("   pages whose words changed against the old files: %d" % changed_total)
        say("   no duty is added, moved or removed: DUTY_MAP is not changed by this kit")
    section("14 staff-eye (CLAUDE.md, S444)", s14)

    # ============================================================================================ 15 weight and numbers
    def s15():
        for u, path in (("amir", "/finance/amir"), ("amir", "/finance/stock/api/pad/amir/1")):
            ts = [t for t in TIMES if t[0] == u and t[1] == path]
            check("Amir's %s under 2 s and 100 KB (%.2f s, %d bytes)" % (path, ts[-1][2] if ts else 99, ts[-1][3] if ts else 0), bool(ts) and ts[-1][2] < 2.0 and ts[-1][3] < 100000)
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
    section("15 weight and numbers", s15)

    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S577: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S577: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S577: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S577: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
