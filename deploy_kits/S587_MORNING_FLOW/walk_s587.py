#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s587.py -- kit S587_MORNING_FLOW (18-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s587.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --map <DUTY_MAP.json>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s587.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --map ...   (the install-day state)
The real finance app in one process (the walk's own header session -- its own secret and user store, never the live ones). Its own rows
by key (W587 ...), never by counting; the live rows by key. The spine COPY is written through a plain rw connection with sp_meta.built
bumped (R3-9 of S528) -- the live spine is never touched. No phone number is printed (a run of ten digits is masked). The sections follow
the brief's section 4 (one section per control, 1-15); --expect-red is the negative control: the same walk on the OLD files, every 'C:'
check must be red. --state prints the install-day state: the stage and its proof, the start captures of the last 7 days with their
verdicts, purchase_cover per closing of the last 7 days, Amir's banner. Prints 'WALK OK S587 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys

KIT = "S587_MORNING_FLOW"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
START_MD5 = "6d7180602f42fc203810c71a21a66ed6"            # the real 18-10 09:37 start capture (R2-B2's named control)
FIX_ITEMS = ("KT ROS DT", "VINBACTUM DS", "FOLITRAX 15 MG TAB", "OSTOVAXL DM")    # the four live amir_job 'fix:' rows (done 18-10 09:2x)
GATE_HI = "Purchase report dobara nikaalni hai \u2014 bill entry export ke baad hui hai"
BAND_HI = "Purchase report dobara nikaaliye \u2014 bill entry export ke baad hui hai"
BANNER_NEW = "1 Punch · 2 Bill entry · 3 Marg sudhar · 4 Export · 5 Check · 6 Bills · 7 Band"
BANNER_OLD = "1 Punch · 2 Bill entry · 3 Export · 4 Check · 5 Bills · 6 Marg sudhar · 7 Band"
STATES = {"done", "skipped", "not yet", "not done", "not needed", "partly", "open"}
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:700] + "]") if (got is not None and not cond) else ""))
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
        check("C: section %s ran without an exception" % title, False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-900:]))


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def banner_of(h):
    m = re.search(r"<div class=steps>(.*?)</div>", h, flags=re.S)
    if not m:
        return ""
    return " · ".join(re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", " ", a))).strip() for a in re.findall(r"<a [^>]*>(.*?)</a>", m.group(1), flags=re.S))


def strip_banner(h):
    """The page without its banner block and its 'Step N of 7' foot -- the two differences the brief allows on Amir's pages."""
    h = re.sub(r"<div class=steps>.*?</div>", " ", h, flags=re.S)
    return re.sub(r"Step \d of 7", "Step N of 7", h)


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def app_env(a, dbp, token):
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB"):
        os.environ.pop(k, None)


def read(fin, name):
    return open(os.path.join(fin, name), encoding="utf-8").read()


def wmd5(tag):
    return "w587" + hashlib.md5(("W587 " + tag).encode()).hexdigest()[4:]


def reach_asof(sp, day):
    """stock_figure.reach as the spine stood at the END of `day` (exports stamped on or before it; the walk's own rows set apart) -- the replay
    of control 8."""
    hi = day.replace("-", "") + "-235959"
    W = " AND COALESCE(note,'')<>'W587 walk' "

    def last(fam_sql):
        return str(sp.q("SELECT MAX(date_to) AS d FROM sp_export WHERE ok=1 AND stamp<=? " + W + " AND " + fam_sql, hi)[0]["d"] or "")

    def stamp_of(fam_sql, d):
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND stamp<=? AND date_to=? " + W + " AND " + fam_sql, hi, d)[0]["s"] or "") if d else ""

    def newest(fam_sql):
        return str(sp.q("SELECT MAX(stamp) AS s FROM sp_export WHERE ok=1 AND stamp<=? " + W + " AND " + fam_sql, hi)[0]["s"] or "")
    S, B, I = "family='SALE_BILLWISE'", "family='PURCHASE_BILLWISE'", "family IN ('PURCHASE_ITEMWISE','PURCHASE_BILLITEMWISE')"
    ls, lb, li = last(S), last(B), last(I)
    lp = min(lb, li) if (lb and li) else ""
    nb, ni = newest(B), newest(I)
    return dict(last_sale=ls, sale_stamp=stamp_of(S, ls), last_pur=lp, pur_stamp=(min(stamp_of(B, lb), stamp_of(I, li)) if lp else ""),
                pur_newest=(min(nb, ni) if (nb and ni) else ""))


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import finance_app as fa                                  # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    SA.ensure_schema(con)
    new = hasattr(SF, "verify_start")
    sp = SW.Spine()
    say("STATE %s: files %s; spine ok %s; stock_figure v%s %s" % (label, "NEW (S587)" if new else "OLD", sp.ok, SF.VERSION, SF.KIT))
    R = SF.reach(sp)
    say("STATE %s: the spine's reach: last_sale %s (%s), last_pur %s (%s)" % (label, R.get("last_sale"), R.get("sale_stamp"), R.get("last_pur"), R.get("pur_stamp")))
    root = SA._desk_root(con, 1) or 1
    st = SA.amir_stage(con, root) or {}
    W = SA._s521_stage_words(con, st)
    pr = SA._s488_stage_proof(st) or {}
    C = st.get("C") or {}
    say("STATE %s: count #%s stage %s; proof state %s why %s; C: %s entered of %s, %s released, %s verified, %d wrong row(s), %d lot(s) waiting"
        % (label, root, st.get("stage"), pr.get("state"), pr.get("why"), C.get("entered"), C.get("total"), C.get("released"), C.get("verified"), len(C.get("wrong") or []), len(C.get("waiting_export") or [])))
    say("STATE %s: Amir's card: %s" % (label, W.get("card_hi")))
    say("STATE %s: the owner's English: %s" % (label, W.get("owner_en")))
    for l in W.get("owner_lines") or []:
        say("STATE %s:    owner line [%s]: %s" % (label, l.get("cls"), l.get("text")))
    if new:
        say("STATE %s: the start captures of the last 7 days (stock_figure verify-start on this copy):" % label)
        for l in SF.verify_start_cli(con, sp, days=7):
            say("   " + l)
        ctx = SF.Ctx(con, sp)
        lo = (dt.date.today() - dt.timedelta(days=7)).isoformat()
        say("STATE %s: purchase_cover per closing of the last 7 days (today's reach | the reach as the closing's day ended):" % label)
        for c in SF.captures(sp, ctx):
            if c["as_on"] < lo:
                continue
            cc = dict(c, end_day=(c["end_day"] or c.get("start_day")))
            how_now = SF.purchase_cover_how(con, sp, cc, R, ctx)
            how_then = SF.purchase_cover_how(con, sp, cc, reach_asof(sp, c["stamp_iso"][:10]), ctx)
            say("   closing printed %s taken %s stands for %s%s: today %s | then %s" % (c["as_on"], c["stamp_iso"], cc["end_day"], " (start, %s)" % c["verdict"] if c["start"] else "",
                                                                                       how_now if not isinstance(how_now, dict) else "c (visit %s, export %s)" % (how_now["visit"], how_now["at"]),
                                                                                       how_then if not isinstance(how_then, dict) else "c (visit %s, export %s)" % (how_then["visit"], how_then["at"])))
        S = SW.settings(con)
        say("STATE %s: settings count.start_capture %s, count.start_unexplained_max %s" % (label, S.get("start_capture"), S.get("start_unexplained_max")))
        say("STATE %s: the owner's start-capture lines: %s" % (label, [l["text"] for l in SW.start_capture_lines(con, sp)]))
    cl = fa.app.test_client(use_cookies=False)
    r = cl.get("/finance/amir/step/6", base_url=BASE, headers={"X-Clinic-User": "amir", "X-Clinic-Role": "staff"})
    h = r.get_data().decode("utf-8", "replace")
    say("STATE %s: Amir's banner (%s): %s; foot: %s" % (label, r.status_code, banner_of(h), (re.search(r"Step \d of 7", h) or [""])[0] if re.search(r"Step \d of 7", h) else "-"))
    con.rollback()
    say("STATE OK S587 (%s)" % label)
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
    anywhere = os.environ.get("S587_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S587 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import shelf_figure as SHF                                # noqa: E402
    import amir_day as AD                                     # noqa: E402
    for m in (SA, SW, SF, SHF, AD):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(SF, "verify_start")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure v%s (%s); amir_day KIT %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", SF.VERSION, "NEW" if NEW else "OLD", AD.KIT))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    schema0 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))

    def GET(u, path, follow=False):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def FORM(u, path, data):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, data=data)
        return r.status_code, r.headers.get("Location", "")

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def spine_rw():
        return sqlite3.connect(SPINE_PATH, timeout=60)

    def bump_built(tag):
        spc = spine_rw()
        spc.execute("UPDATE sp_meta SET value=? WHERE key='built'", ("%s+W587-%s" % (str(spc.execute("SELECT value FROM sp_meta WHERE key='built'").fetchone()[0])[:25], tag),))
        spc.commit()
        spc.close()
        SA._S446_PROOF_CACHE.clear()
        SA._S524_REPORT_CACHE.clear()

    def fresh():
        """A fresh spine door and context after a write on the copy."""
        sp_ = SW.Spine()
        return sp_, SF.Ctx(conn(), sp_)

    SA.ensure_schema(sqlite3.connect(dbp))
    sp = SW.Spine()
    assert sp.ok and SW.SPINE_DB == SPINE_PATH, (sp.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    SRC = {n: read(fin, n) for n in ("stock_figure.py", "shelf_figure.py", "stock_app.py", "amir_day.py", "stock_watch.py", "stock_now.html")}
    c0 = conn()
    ROOT = SA._desk_root(c0, 1) or 1
    R0 = SF.reach(sp)
    today = dt.date.today().isoformat()
    say("   today %s; count root %s; the spine's reach: last_sale %s (%s), last_pur %s (%s)" % (today, ROOT, R0.get("last_sale"), R0.get("sale_stamp"), R0.get("last_pur"), R0.get("pur_stamp")))
    fixrows = [tuple(r) for r in c0.execute("SELECT id, key, subject, done_at, done_how FROM amir_job WHERE key LIKE 'fix:%' ORDER BY id")]
    say("   the live amir_job 'fix:' rows on this copy: %s" % fixrows)
    check("the four corrected items' fix rows are on the copy, called done by his tap on 18-10", sorted(r[2] for r in fixrows) == sorted(FIX_ITEMS) and all(str(r[3] or "").startswith("2026-10-18") and r[4] == "tap" for r in fixrows), fixrows)
    c0.close()

    def tryable_old(c, R):
        d = c.get("end_day") or ""
        if not d or R["last_sale"] < d or not SF.covers(R["last_sale"], R["sale_stamp"], c, d):
            return False
        return bool(R["last_pur"]) and R["last_pur"] >= d and SF.covers(R["last_pur"], R["pur_stamp"], c, d)

    def lots_of(c):
        ortho_b = SA._s446_batches(c, ROOT)
        ortho = [k for k, b in ortho_b.items() if "Orthotics" in b["secs"]]
        lots = [("A", ortho)]
        for i, r in enumerate(c.execute("SELECT ref FROM stock_stage_event WHERE count_id=? AND stage='C' AND event='release' ORDER BY id", (ROOT,))):
            lots.append(("C%d" % (i + 1), [SA._s446_unkey(x) for x in (r[0] or "").split(",") if x]))
        return ortho_b, lots

    def proof_map(c):
        """{item: dict(v, day, why, lot)} as the screens read it (amir_stage's own calls: _s446_proof per stage-A set and per C lot)."""
        batches, lots = lots_of(c)
        ent = SA._s446_entered(c, ROOT)
        out = {}
        for name, keys in lots:
            ek = [k for k in keys if k in ent]
            if not ek:
                continue
            pr = SA._s446_proof(c, ROOT, ek, ent, batches)
            for it, day in (pr.get("proven_on") or {}).items():
                out[it] = dict(v="proven", day=day, why="", lot=name)
            for r in pr.get("rows") or []:
                out[r["item"]] = dict(v="wrong", day=r.get("closing_day"), why="", lot=name)
            for r in pr.get("unseen") or []:
                out[r["item"]] = dict(v="unseen", day=r.get("closing_day"), why=r.get("why"), lot=name)
        return out

    # ============================================================================================ 1 the proof identical where nothing changed
    def s1():
        bump_built("s1")
        c = conn()
        pm = proof_map(c)
        DUMP["proof"] = pm
        tally = {}
        for it, v in pm.items():
            tally[v["v"] if v["v"] != "unseen" else "unseen:" + str(v["why"])] = tally.get(v["v"] if v["v"] != "unseen" else "unseen:" + str(v["why"]), 0) + 1
        say("   the proof on this copy, as the screens read it: %d items -- %s" % (len(pm), dict(sorted(tally.items()))))
        check("C: _s524_table reads stock_figure.captures() by md5 -- 'sp_close WHERE as_on' and _s524_closings( are gone from stock_app.py",
              "sp_close WHERE as_on" not in SRC["stock_app.py"] and "_s524_closings(" not in SRC["stock_app.py"] and "_sf.captures(sp, kctx)" in SRC["stock_app.py"])
        if "proof" in OLD:
            old = OLD["proof"]
            diff = {}
            for it in sorted(set(old) | set(pm)):
                o, n = old.get(it), pm.get(it)
                if (o or {}).get("v") != (n or {}).get("v") or ((o or {}).get("v") == "unseen" and (o or {}).get("why") != (n or {}).get("why")):
                    diff[it] = (o, n)
            say("   verdicts differing old -> new: %d of %d" % (len(diff), len(pm)))
            # name the rule behind each difference: a try on an accepted start capture (D740), a try the old files never made (R2-B5), his correction after the judged capture (F-933)
            batches, lots = lots_of(c)
            ent = SA._s446_entered(c, ROOT)
            win = SA._s446_window(c, ROOT)
            at_of = {k: str(win.get(k) or v[1] or "") for k, v in ent.items()}
            kof = {}
            Ts = {}
            for name, keys in lots:
                ek = [k for k in keys if k in ent]
                if ek:
                    fa_, la_ = min(at_of[k] for k in ek)[:19], max(at_of[k] for k in ek)[:19]
                    Ts[name] = SA._s524_table(c, sp, ROOT, ent, batches, fa_, la_, at_of)
                    kof.update(Ts[name]["kof"])
            unexplained = {}
            for it, (o, n) in diff.items():
                rule = None
                T = Ts.get((n or o or {}).get("lot") or "")
                k = (T or {}).get("kof", {}).get(it) or kof.get(it)
                e = ((T or {}).get("keys") or {}).get(k) or {}
                if (n or {}).get("v") == "unseen" and (n or {}).get("why") == "pending_fix":
                    rule = "F-933 pending_fix (his correction %s after the judged capture)" % ((e.get("pending_fix") or {}).get("done_at"))
                elif (n or {}).get("v") == "proven" and (o or {}).get("v") != "proven":
                    X = (e.get("L") or {}).get("X") or {}
                    if X.get("start"):
                        rule = "D740 start capture (proven on the %s capture, end_day %s)" % (X.get("stamp_iso"), X.get("end_day"))
                    elif T is not None:
                        old_tries = [x for x in T["after"] if tryable_old(x, T["reach"])]
                        old_set = ([T["after"][0]] if (old_tries and old_tries[0] is T["after"][0]) else []) + ([old_tries[-1]] if (old_tries and old_tries[-1] is not T["after"][0]) else [])
                        if X and all(X is not y for y in old_set):
                            rule = "R2-B5 (proven on the %s capture, which the old files never tried)" % X.get("stamp_iso")
                elif (n or {}).get("v") == "unseen" and (o or {}).get("v") == "unseen":
                    rule = "the reach word (%s -> %s)" % ((o or {}).get("why"), (n or {}).get("why"))
                if rule is None:
                    unexplained[it] = (o, n)
                say("   %-28s %s -> %s   [%s]" % (it[:28], (o or {}).get("v"), (n or {}).get("v") + (("/" + str((n or {}).get("why"))) if (n or {}).get("v") == "unseen" else ""), rule or "UNEXPLAINED"))
            check("every differing verdict is explained by D740 (a start capture), R2-B5 (a try the old files never made) or F-933 (pending_fix) -- %d unexplained" % len(unexplained), not unexplained, unexplained)
        c.close()
    section("1  the proof identical where nothing changed (old vs new, the rule behind each difference)", s1)

    # ============================================================================================ 2 the real 18-10 09:37 start capture
    def s2():
        c = conn()
        if not NEW:
            check("C: stock_figure has verify_start / start_ready / purchase_cover (the start-of-day rule)", False, "old files")
            c.close()
            return
        ctx = SF.Ctx(c, sp)
        cap = SF.capture_of(sp, START_MD5, ctx)
        check("C: the 18-10 09:37 capture is a START capture (printed 18-10, taken 09:37) that may stand for the end of 17-10", bool(cap) and cap["start"] and cap["start_day"] == "2026-10-17" and not cap["usable"], cap)
        rd = SF.start_ready(c, sp, cap, ctx)
        check("C: with 18-10's sale report absent it is PENDING (sale_short), never set aside", cap["verdict"] == "pending" and rd == (False, "sale_short"), (cap["verdict"], rd))
        row = c.execute("SELECT verdict, reason FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()
        check("C: the record says pending / sale_short", tuple(row or ()) == ("pending", "sale_short"), tuple(row or ()))
        # (ii) the sale report of 18-10 lands (a synthetic SALE_BILLWISE export row on the spine COPY; no 18-10 sale lines are known today), no purchase export after the 09:35 tap
        spc = spine_rw()
        spc.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (wmd5("sale18"), "W587 SALE_BILLWISE_DETAIL__2026-10-18__20261019-051000.XLS", "SALE_BILLWISE", "20261019-051000", "2026-10-18", "2026-10-18", "", 1, "[]", "READ", "W587 walk"))
        spc.commit()
        spc.close()
        bump_built("s2a")
        sp2, ctx2 = fresh()
        R2 = SF.reach(sp2)
        cap2 = SF.capture_of(sp2, START_MD5, ctx2)
        rd2 = SF.start_ready(ctx2.con, sp2, cap2, ctx2)
        say("   with the 18-10 sale report in: reach last_sale %s; start_ready %s; purchase_cover_how %s" % (R2["last_sale"], rd2, SF.purchase_cover_how(ctx2.con, sp2, dict(cap2, end_day=cap2["start_day"]), R2, ctx2)))
        check("C: with the sale report in but no purchase export after the 09:35 tap it is still PENDING (pur_short) -- never set aside for a short cover (R1-B3)", rd2 == (False, "pur_short") and cap2["verdict"] == "pending", (rd2, cap2["verdict"]))
        # (iii) a purchase export after the 09:35 tap, with the same bills: purchase_export rows (the fact Amir's page reads) and sp_export rows (the spine's reach)
        b = c.execute("SELECT n_rows, grand_amount_p FROM purchase_export WHERE type='BILLWISE' AND export_stamp LIKE '20261018-%' ORDER BY export_stamp DESC LIMIT 1").fetchone()
        i = c.execute("SELECT n_rows, grand_amount_p FROM purchase_export WHERE type='ITEMWISE' AND export_stamp LIKE '20261018-%' ORDER BY export_stamp DESC LIMIT 1").fetchone()
        for typ, md5, r in (("BILLWISE", wmd5("purB"), b), ("ITEMWISE", wmd5("purI"), i)):
            c.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p, superseded_by) VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                      (md5, typ, "W587 %s" % typ, "2026-10-01", "2026-10-18", "20261018-094500", "2026-10-18T09:47:00", r[0] if r else 0, r[1] if r else 0))
        c.commit()
        spc = spine_rw()
        for fam, md5 in (("PURCHASE_BILLWISE", wmd5("purB")), ("PURCHASE_ITEMWISE", wmd5("purI"))):
            spc.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (md5, "W587 %s__2026-10-01_to_2026-10-18__20261018-094500.XLS" % fam, fam, "20261018-094500", "2026-10-01", "2026-10-18", "", 1, "[]", "READ", "W587 walk"))
        spc.commit()
        spc.close()
        bump_built("s2b")
        sp3, ctx3 = fresh()
        caps3 = SF.captures(sp3, ctx3)
        cap3 = SF.capture_of(sp3, START_MD5, ctx3)
        row3 = ctx3.con.execute("SELECT verdict, reason, n_keys, n_excluded, n_unexplained, detail, prev_md5 FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()
        d3 = json.loads(row3["detail"] or "{}") if row3 else {}
        say("   VERDICT of the real 18-10 09:37 capture on this copy (18-10 sale report in, a purchase export after the 09:35 tap, the same bills): %s%s; keys %s, excluded %s, unexplained %s; the previous verified capture %s %s"
            % (row3["verdict"], (" / " + row3["reason"]) if row3["reason"] else "", row3["n_keys"], row3["n_excluded"], row3["n_unexplained"], str(row3["prev_md5"] or "")[:8], (d3.get("prev") or {}).get("stamp_iso")))
        say("   excluded by cause: %s" % {k: len(v) for k, v in (d3.get("excluded") or {}).items()})
        fixk = {x[1] for x in (d3.get("excluded") or {}).get("fix", [])}
        say("   the four 'fix:' items among the excluded: %s" % sorted(fixk))
        say("   purchases dated 18-10 excluded: %d key(s); bills first seen on or after the previous capture's day: %d key(s); the consumption list: %d; vouchers in the window: %d"
            % tuple(len((d3.get("excluded") or {}).get(k, [])) for k in ("purchase", "bill_new", "consume", "vouchers")))
        say("   deciding keys -- a sale before it: %s" % [(x[1], x[2], x[3]) for x in d3.get("sale_before") or []])
        say("   deciding keys -- unexplained: %s" % [(x[1], x[2]) for x in d3.get("unexplained") or []])
        say("   excluded keys that moved (the morning's known work): %s" % [(x[1], x[2]) for x in (d3.get("changed_excluded") or [])[:16]])
        DUMP["start_verdict"] = dict(verdict=row3["verdict"], reason=row3["reason"], n_keys=row3["n_keys"], n_excluded=row3["n_excluded"], n_unexplained=row3["n_unexplained"])
        check("C: the verdict is final (accepted or set_aside), written once on the copy", row3["verdict"] in ("accepted", "set_aside"), tuple(row3))
        check("C: the four corrected items are excluded by cause 'fix' (his taps 18-10 09:2x lie in the window)", fixk == set(FIX_ITEMS), fixk)
        check("C: no set_aside by sale_before on a key whose only drop is a 'fix:' tap", not any(x[1] in FIX_ITEMS for x in d3.get("sale_before") or []), d3.get("sale_before"))
        check("C: purchases dated 18-10 are excluded (the morning's bills are inside the capture)", len((d3.get("excluded") or {}).get("purchase", [])) >= 1)
        check("C: the previous verified capture is the 17-10 09:20 one (end of 16-10)", str(row3["prev_md5"] or "").startswith("7f4d5832"), row3["prev_md5"])
        check("C: usable follows the verdict (accepted -> stands for the end of 17-10)", cap3["usable"] == (row3["verdict"] == "accepted") and (cap3["end_day"] == "2026-10-17" if cap3["usable"] else cap3["end_day"] is None), (cap3["usable"], cap3["end_day"]))
        say("   NOTE: the live verdict is given on the server tomorrow morning, when the real 18-10 sale report lands and Amir's next export covers it; the walk's is on a copy with a synthetic reach")
        c.close()
    section("2  the real 18-10 09:37 start capture: pending twice, then the verdict with the deciding keys (R2-B2)", s2)

    def rejudge_start(tag):
        """The walk's own re-judgment of the 09:37 capture on the copy: the record row is the walk's (section 2 wrote it), removed and judged again."""
        c = conn()
        c.execute("DELETE FROM stock_start_capture WHERE md5=?", (START_MD5,))
        c.commit()
        c.close()
        bump_built(tag)
        sp_, ctx_ = fresh()
        SF.captures(sp_, ctx_)
        row = ctx_.con.execute("SELECT verdict, reason, detail FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()
        return sp_, ctx_, (row["verdict"], row["reason"], json.loads(row["detail"] or "{}")) if row else (None, None, {})

    def quiet_key(ctx_, d3, n=1, avoid=()):
        """n keys of the capture with change 0 and no exclusion -- the walk's clean subjects."""
        excl = {str(x[0]) for ks in (d3.get("excluded") or {}).values() for x in ks} | {str(x[0]) for x in d3.get("unexplained") or []} | set(avoid)
        uS, nS = SF._units_by_key(ctx_.sp, START_MD5, ctx_)
        out = []
        for k in sorted(uS):
            if k in excl or uS[k] < 5 or k in FIX_ITEMS:
                continue
            out.append(k)
            if len(out) == n:
                break
        return out

    # ============================================================================================ 3 a sale before the capture
    def s3():
        if not NEW:
            check("C: a sale before the capture sets it aside (sale_before)", False, "old files")
            return
        sp_, ctx_, (v, r, d) = rejudge_start("s3a")
        ks = quiet_key(ctx_, d, 1)
        check("a clean subject key for the control exists on the copy", bool(ks))
        K = ks[0]
        spc = spine_rw()
        spc.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,?,?,?)", (K, "2026-10-18", "SALE", -3.0, "W587SALE"))
        spc.execute("UPDATE sp_close_name SET units = units - 3 WHERE md5=? AND k20=?", (START_MD5, K))
        spc.commit()
        spc.close()
        sp2, ctx2, (v2, r2, d2) = rejudge_start("s3b")
        say("   %s sold 3 on 18-10 before the capture (its units lowered by 3): verdict %s / %s; deciding: %s" % (K, v2, r2, [(x[1], x[2], x[3]) for x in d2.get("sale_before") or []]))
        check("C: set_aside, reason sale_before, the key in detail", v2 == "set_aside" and r2 == "sale_before" and any(x[0] == K for x in d2.get("sale_before") or []), (v2, r2))
        cap2 = SF.capture_of(sp2, START_MD5, ctx2)
        check("C: a set-aside start capture is unusable (capture_for 17-10 does not return it)", not cap2["usable"] and ((SF.capture_for(sp2, "2026-10-17", ctx2) or {}).get("md5") != START_MD5))
        lines = SW.start_capture_lines(ctx2.con, sp2)
        say("   the owner's line: %s" % [l["text"] for l in lines])
        check("C: the owner's Needs-you line says 'Closing stock printed 18-10 09:37 set aside -- a sale came before it (%s)'" % K,
              any(("Closing stock printed 18-10 09:37 set aside" in l["text"]) and ("a sale came before it" in l["text"]) and (K in l["text"]) for l in lines), [l["text"] for l in lines])
        spc = spine_rw()
        spc.execute("DELETE FROM sp_move WHERE ref='W587SALE'")
        spc.execute("UPDATE sp_close_name SET units = units + 3 WHERE md5=? AND k20=?", (START_MD5, K))
        spc.commit()
        spc.close()
    section("3  a sale before the capture -> set_aside sale_before", s3)

    # ============================================================================================ 4 unexplained changes against the threshold
    def s4():
        if not NEW:
            check("C: unexplained changes beyond count.start_unexplained_max set the capture aside; within it, accepted and approx", False, "old files")
            return
        sp_, ctx_, (v, r, d) = rejudge_start("s4a")
        base_un = len(d.get("unexplained") or [])
        n = 3
        ks = quiet_key(ctx_, d, n)
        check("three clean subject keys exist on the copy (the copy's own unexplained so far: %d)" % base_un, len(ks) == n, ks)
        spc = spine_rw()
        for K in ks:
            spc.execute("UPDATE sp_close_name SET units = units + 1 WHERE md5=? AND k20=?", (START_MD5, K))
        spc.commit()
        spc.close()
        c = conn()
        before = c.execute("SELECT value FROM setting WHERE key='count.start_unexplained_max'").fetchone()
        ok_, msg = SW.set_setting(c, "count.start_unexplained_max", str(base_un + n - 1), "w587walk")
        check("the save door takes count.start_unexplained_max=%d (%s)" % (base_un + n - 1, msg), ok_, msg)
        c.close()
        sp2, ctx2, (v2, r2, d2) = rejudge_start("s4b")
        say("   %d keys raised by 1 with max %d: verdict %s / %s; unexplained: %s" % (n, base_un + n - 1, v2, r2, [(x[1], x[2]) for x in d2.get("unexplained") or []]))
        check("C: more unexplained keys than the setting -> set_aside unexplained", v2 == "set_aside" and r2 == "unexplained" and len(d2.get("unexplained") or []) == base_un + n, (v2, r2))
        lines = SW.start_capture_lines(ctx2.con, sp2)
        check("C: the owner's line says '%d items changed with no Marg reason'" % (base_un + n), any("set aside" in l["text"] and ("%d items changed with no Marg reason" % (base_un + n)) in l["text"] for l in lines), [l["text"] for l in lines])
        c = conn()
        SW.set_setting(c, "count.start_unexplained_max", str(base_un + n), "w587walk")
        c.close()
        sp3, ctx3, (v3, r3, d3) = rejudge_start("s4c")
        check("C: with max = the count -> accepted, the keys listed as unexplained", v3 == "accepted" and {x[0] for x in d3.get("unexplained") or []} >= set(ks), (v3, r3, d3.get("unexplained")))
        M = SF.marg(ctx3.con, sp3, SF._units_by_key(sp3, START_MD5, ctx3)[1][ks[0]], None, ctx3)
        check("C: such a key is approx on that capture (marg().approx_reason start_unexplained)", bool(M) and M["approx"] and M.get("approx_reason") == "start_unexplained" and M["closing"]["md5"] == START_MD5, M and (M["approx"], M.get("approx_reason"), M["closing"]["md5"][:8]))
        spc = spine_rw()
        for K in ks:
            spc.execute("UPDATE sp_close_name SET units = units - 1 WHERE md5=? AND k20=?", (START_MD5, K))
        spc.commit()
        spc.close()
        c = conn()
        if before is None:
            c.execute("DELETE FROM setting WHERE key='count.start_unexplained_max'")
        else:
            c.execute("UPDATE setting SET value=? WHERE key='count.start_unexplained_max'", (before[0],))
        c.commit()
        c.close()
    section("4  unexplained changes against count.start_unexplained_max; accepted keys approx", s4)

    # ============================================================================================ 5 the switch
    def s5():
        if not NEW:
            check("C: count.start_capture = 0 makes every start capture unusable and writes nothing", False, "old files")
            return
        c = conn()
        before = c.execute("SELECT value FROM setting WHERE key='count.start_capture'").fetchone()
        c.execute("DELETE FROM stock_start_capture WHERE md5=?", (START_MD5,))
        ok_, msg = SW.set_setting(c, "count.start_capture", "0", "w587walk")
        c.commit()
        check("the save door takes count.start_capture=0 (%s)" % msg, ok_)
        rows = {r["key"]: r for r in SW.settings_view(c) if r["key"] in ("count.start_capture", "count.start_unexplained_max")}
        check("C: the two settings are on the card under 'Counts & watch' (kind choice / int)", set(rows) == {"count.start_capture", "count.start_unexplained_max"} and all(r["heading"] == "Counts & watch" for r in rows.values())
              and rows["count.start_capture"]["kind"] == "choice" and rows["count.start_unexplained_max"]["kind"] == "int", {k: (r["kind"], r["heading"], r["value"]) for k, r in rows.items()})
        c.close()
        bump_built("s5a")
        sp_, ctx_ = fresh()
        cap = SF.capture_of(sp_, START_MD5, ctx_)
        n = ctx_.con.execute("SELECT COUNT(*) FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()[0]
        check("C: switch off -> the start capture is unusable (verdict 'off'), nothing written", cap["verdict"] == "off" and not cap["usable"] and n == 0, (cap["verdict"], cap["usable"], n))
        check("C: switch off -> capture_at today is the 17-10 09:20 capture (the old rule)", SF.capture_at(sp_, None, ctx_)["stamp_iso"] == "2026-10-17T09:20:35", SF.capture_at(sp_, None, ctx_)["stamp_iso"])
        c = conn()
        SW.set_setting(c, "count.start_capture", "1", "w587walk")
        if before is None:
            c.execute("DELETE FROM setting WHERE key='count.start_capture'")
        c.commit()
        c.close()
        sp2, ctx2, (v2, r2, d2) = rejudge_start("s5b")
        check("C: switch back on -> judged again (a verdict row written: %s)" % v2, v2 in ("accepted", "set_aside"), v2)
    section("5  the owner's switch count.start_capture", s5)

    # ============================================================================================ 6 the chooser
    def s6():
        if not NEW:
            check("C: an accepted start capture is the newest capture for its end_day; closing() reads the corrected units", False, "old files")
            return
        c = conn()
        before = c.execute("SELECT value FROM setting WHERE key='count.start_unexplained_max'").fetchone()
        SW.set_setting(c, "count.start_unexplained_max", "50", "w587walk")      # the walk needs the 09:37 capture ACCEPTED for the chooser (the live verdict is the server's tomorrow)
        c.close()
        sp_, ctx_, (v, r, d) = rejudge_start("s6a")
        check("the 09:37 capture is accepted on the copy for this control (verdict %s)" % v, v == "accepted", (v, r))
        cf = SF.capture_for(sp_, "2026-10-17", ctx_) or {}
        ca = SF.capture_at(sp_, None, ctx_) or {}
        check("C: capture_for(17-10) is the 09:37 start capture (the newest usable capture standing for the end of 17-10)", cf.get("md5") == START_MD5, cf.get("stamp_iso"))
        check("C: capture_at(today) is the 09:37 start capture", ca.get("md5") == START_MD5, ca.get("stamp_iso"))
        cl_ = SF.closing(ctx_.con, sp_, "FOLITRAX 15 MG TAB", None, ctx_) or {}
        say("   closing() of FOLITRAX 15 MG TAB today: %s units on the %s capture (the 17-10 09:20 capture printed 132; Amir's correction of 18-10 09:24 lowered it)" % (cl_.get("units"), cl_.get("stamp_iso")))
        check("C: closing() of a corrected item reads its post-correction units from the start capture", cl_.get("md5") == START_MD5 and cl_.get("units") == 120.0, (cl_.get("md5"), cl_.get("units")))
        s, b = GET("manoj", "/finance/stock/api/now")
        j = json.loads(b) if s == 200 else {}
        rows = {r_["item"]: r_ for r_ in j.get("rows") or []}
        DUMP["now_marg"] = {it: r_["marg"] for it, r_ in rows.items()}
        DUMP["now_capture"] = (j.get("capture") or {}).get("md5")
        say("   /stock/api/now reads the capture %s (as_on %s, %d rows)" % ((j.get("capture") or {}).get("md5"), j.get("as_on"), len(rows)))
        check("C: /stock/api/now stands on the 09:37 start capture", (j.get("capture") or {}).get("md5") == START_MD5[:8], j.get("capture"))
        if OLD.get("now_marg"):
            moved = sorted(it for it in rows if OLD["now_marg"].get(it) is not None and rows[it]["marg"] is not None and OLD["now_marg"][it] != rows[it]["marg"])
            allowed_keys = {str(x[0]) for ks in (d.get("excluded") or {}).values() for x in ks} | {str(x[0]) for x in d.get("unexplained") or []}
            stray = [it for it in moved if SF.key_of(sp_, it, ctx_) not in allowed_keys]
            say("   Marg figures that moved against the old files on the same copy: %d of %d (the keys whose closing moved between the two captures, or with a purchase dated 18-10)" % (len(moved), len(rows)))
            check("C: the figures moved only for keys whose closing moved (unexplained / known morning work / a purchase of the day) -- %d stray" % len(stray), not stray and moved, stray[:12] or moved[:3])
        s2, b2 = GET("manoj", "/finance/stock/api/loss/%d/piles" % ROOT)
        j2 = json.loads(b2) if s2 == 200 else {}
        say("   the Loss desk reads (%s): %d pile(s), summary %s" % (s2, len(j2.get("piles") or []), json.dumps(j2.get("summary") or j2.get("totals") or {}, default=str)[:200]))
        check("the Loss desk reads on the start capture", s2 == 200)
        c = conn()
        if before is None:
            c.execute("DELETE FROM setting WHERE key='count.start_unexplained_max'")
        else:
            c.execute("UPDATE setting SET value=? WHERE key='count.start_unexplained_max'", (before[0],))
        c.commit()
        c.close()
    section("6  the chooser: the accepted start capture is the newest for its end_day", s6)

    # ============================================================================================ 7 R2-B3: a purchase dated D on a start capture is counted once
    def s7():
        if not NEW:
            check("C: marg() on a start capture never adds the printed day's purchases again (approx purchase_on_start)", False, "old files")
            return
        sp_, ctx_ = fresh()
        c = ctx_.con
        row = c.execute("SELECT detail FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()
        d = json.loads(row["detail"] or "{}") if row else {}
        pk = [(x[0], x[1]) for x in (d.get("excluded") or {}).get("purchase", [])]
        check("keys with a purchase dated 18-10 inside the capture exist on the copy (%d)" % len(pk), bool(pk))
        uS, nS = SF._units_by_key(sp_, START_MD5, ctx_)
        K, name = pk[0]
        pD = SF._purchases_on(sp_, "2026-10-18", ctx_).get(K)
        M = SF.marg(c, sp_, name, None, ctx_)
        twice = uS[K] + SF.spine_move(sp_, K, "2026-10-17", today)
        say("   %s: printed %g in the 09:37 capture; purchase dated 18-10 in the spine %s; marg().figure %s (the old arithmetic would say %g); approx %s / %s"
            % (name, uS[K], pD, M and M["figure"], twice, M and M["approx"], M and M.get("approx_reason")))
        check("C: marg().figure counts the purchase once (= the capture's units, nothing dated 18-10 added)", M is not None and abs(M["figure"] - uS[K]) < 0.5 and abs(twice - M["figure"] - pD[1]) < 0.5, (M and M["figure"], uS[K], twice))
        check("C: the key is approx with reason purchase_on_start", M is not None and M["approx"] and M.get("approx_reason") == "purchase_on_start")
        check("C: the proof table skips it on that capture (morning_skip_keys)", SF.morning_skip_keys(sp_, SF.capture_of(sp_, START_MD5, ctx_), ctx_).get(K) == "purchase_on_start")
        F = SHF.figures(c, sp=sp_, items=[name], upto=today, ctx=ctx_)[name]
        check("C: the shelf-gap flags skip it (shelf_figure.figures approx=True)", bool(F.get("approx")), F.get("approx"))
        check("C: marg() at the capture's own end day (17-10) still names it (approx, the purchase inside)", (SF.marg(c, sp_, name, "2026-10-17", ctx_) or {}).get("approx_reason") == "purchase_on_start")
        check("C: the voucher guard reads marg()'s approx reason -- early_bill( is in no file of the finance folder",
              not any("early_bill(" in read(fin, n) for n in os.listdir(fin) if n.endswith(".py")) and 'approx_reason") == "purchase_on_start"' in SRC["stock_app.py"])
    section("7  R2-B3: a purchase dated the printed day on a start capture is counted once", s7)

    # ============================================================================================ 8 visit cover, the real days
    def s8():
        if not NEW:
            check("C: purchase_cover has the visit clause (c)", False, "old files")
            return
        sp_, ctx_ = fresh()
        c = ctx_.con

        def how(cap, R):
            h = SF.purchase_cover_how(c, sp_, cap, R, ctx_)
            return h if not isinstance(h, dict) else "c"

        def hv(cap, R):
            return SF.purchase_cover_how(c, sp_, cap, R, ctx_)
        say("   every closing of 02 -> 18-Oct, the reach as its day ended (exports stamped on or before it); the start captures as they would stand:")
        res = {}
        for cap in SF.captures(sp_, ctx_):
            if not ("2026-10-02" <= cap["as_on"] <= "2026-10-18") or cap["md5"].startswith("w587"):
                continue
            cc = dict(cap, end_day=(cap["end_day"] or cap.get("start_day")))
            R = reach_asof(sp_, cap["stamp_iso"][:10])
            h = hv(cc, R)
            res[cap["stamp_iso"]] = h if not isinstance(h, dict) else "c"
            say("   %s %s -> end %s%s: reach then last_pur %s (%s): cover %s%s | old rule (a only): %s"
                % (cap["as_on"], cap["stamp_iso"], cc["end_day"], " START" if cap["start"] else "", R["last_pur"], R["pur_stamp"], res[cap["stamp_iso"]],
                   (" (visit %s, last bill-entry tap %s, export %s%s)" % (h["visit"], h["t2"], h["at"], ", identical to the visit's own export" if h.get("identical") else "")) if isinstance(h, dict) else "",
                   tryable_old(cc, R)))
        check("C: 15-10's 09:10 export is NOT cover for the 15-10 10:05 and 10:22 closings (the re-taps 10:05 / 10:06 came after it)", res.get("2026-10-15T10:05:40") is None and res.get("2026-10-15T10:22:38") is None, (res.get("2026-10-15T10:05:40"), res.get("2026-10-15T10:22:38")))
        c16 = dict(md5="w587synth16", as_on="2026-10-16", stamp="20261016-140000", stamp_iso="2026-10-16T14:00:00", end_day="2026-10-15", usable=True, start=False, early=False)
        h16 = hv(c16, reach_asof(sp_, "2026-10-16"))
        say("   a closing on 16-10 14:00 (end 15-10), the reach as 16-10 ended: %s" % h16)
        check("C: the owner's 16-10 13:03 export (identical to 15-10's: 38 bills / 81 lines) IS cover for a 16-10 closing after 13:03 -- clause (c), identical", isinstance(h16, dict) and h16["visit"] == "2026-10-15" and h16["at"].startswith("2026-10-16 13:04") and h16.get("identical"), h16)
        check("C: the 17-10 09:20 closing (end 16-10) is covered by (c) through the same export, where the reach rule (a) alone said 'pur'", res.get("2026-10-17T09:20:35") == "c", res.get("2026-10-17T09:20:35"))
        check("C: 04-10's 10:10 export (stamped at his 10:10 bill-entry tap) covers the 10:22 closing -- the same-day clause", res.get("2026-10-04T10:22:10") == "c", res.get("2026-10-04T10:22:10"))
        check("C: 18-10's 09:25 / 09:27 exports are not cover for the 09:37 closing (tap 09:35 after them) -- it waits for the next export", res.get("2026-10-18T09:37:08") is None, res.get("2026-10-18T09:37:08"))
        c17 = SF.capture_of(sp_, "7f4d58322c2b50f37048b32591026a9b", ctx_)
        R17 = reach_asof(sp_, "2026-10-17")
        check("C: tryable() of the 17-10 closing with the reach as 17-10 ended: the new rule True, the old rule (reach only) False", SF.tryable(c17, R17, c, ctx_) == (True, "") and not tryable_old(c17, R17), (SF.tryable(c17, R17, c, ctx_), tryable_old(c17, R17)))
        check("C: with con None the visit clause does not run (only the reach and the newest exports)", SF.tryable(c17, R17) == (False, "pur"), SF.tryable(c17, R17))
        check("C: shelf_figure.record_gaps passes con / ctx to tryable (one cover with the proof)", "SF.tryable(c, R, con, ctx)" in SRC["shelf_figure.py"])
        DUMP["cover"] = res
    section("8  visit cover (R2-B4): the real days replayed", s8)

    # ============================================================================================ 9 R2-B5: agrees = right at once
    def s9():
        c = conn()
        bump_built("s9")
        sp_ = SW.Spine()
        ctx_ = SF.Ctx(c, sp_)
        T_at = "2026-10-17T12:00:00"
        if NEW:
            row = c.execute("SELECT detail FROM stock_start_capture WHERE md5=?", (START_MD5,)).fetchone()
            d = json.loads(row["detail"] or "{}") if row else {}
            ks = quiet_key(ctx_, d, 2)
        else:
            ks = [r_[0] for r_ in sqlite3.connect(SPINE_PATH).execute("SELECT k20 FROM sp_close_name WHERE md5=? AND units>=5 ORDER BY k20 LIMIT 2", (START_MD5,))]
        K3, K4 = ks[0], ks[1]
        n3 = [r_[0] for r_ in sqlite3.connect(SPINE_PATH).execute("SELECT name FROM sp_close_name WHERE md5=? AND k20=?", (START_MD5, K3))][0]
        n4 = [r_[0] for r_ in sqlite3.connect(SPINE_PATH).execute("SELECT name FROM sp_close_name WHERE md5=? AND k20=?", (START_MD5, K4))][0]
        # the purchase cover of the 09:37 capture withdrawn (the walk's own export rows removed): the capture stays accepted (a record), but N is outside the purchase reach
        c.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w587%'")
        c.commit()
        spc = spine_rw()
        spc.execute("DELETE FROM sp_export WHERE md5 IN (?,?)", (wmd5("purB"), wmd5("purI")))
        spc.execute("UPDATE sp_close_name SET units = units - 2 WHERE md5=? AND k20=?", (START_MD5, K3))     # Marg's 09:37 closing carries the ISSUE voucher of K3 (-2)
        spc.commit()
        spc.close()
        bump_built("s9b")
        sp_ = SW.Spine()
        batches = {(9, "ISSUE", 1): dict(secs={"Medicine"}, lines=[(n3, -2, 0)], made=T_at, pk={n3: ("", 1)}),
                   (9, "ISSUE", 2): dict(secs={"Medicine"}, lines=[(n4, -5, 0)], made=T_at, pk={n4: ("", 1)})}
        ent = {k: ("W587", T_at, "17-10-2026", "amir") for k in batches}
        at_of = {k: T_at for k in batches}
        T = SA._s524_table(c, sp_, ROOT, ent, batches, T_at, T_at, at_of)
        kk3, kk4 = T["kof"].get(n3), T["kof"].get(n4)
        e3, e4 = (T["keys"].get(kk3) or {}), (T["keys"].get(kk4) or {})
        say("   R %s; after %s; tries %s; N %s (inside both reaches: %s, short %s)" % ((T["R"] or {}).get("stamp_iso"), [x["stamp_iso"] for x in T["after"]], [x["stamp_iso"] for x in T["tries"]],
                                                                                    (T["N"] or {}).get("stamp_iso"), T.get("N_ok"), T.get("N_short")))
        say("   %s (voucher -2, Marg's 09:37 closing agrees): proven %s wrong %s pending_reach %s on %s" % (n3, e3.get("proven"), e3.get("wrong"), e3.get("pending_reach"), ((e3.get("L") or {}).get("X") or {}).get("stamp_iso")))
        say("   %s (voucher -5, Marg's closing did not move): proven %s wrong %s pending_reach %s" % (n4, e4.get("proven"), e4.get("wrong"), e4.get("pending_reach")))
        check("C: a voucher that agrees on a usable closing not yet purchase-covered is PROVEN at once (R2-B5)", e3.get("proven") is True and ((e3.get("L") or {}).get("X") or {}).get("md5") == START_MD5, e3)
        check("C: a disagreeing voucher is not 'wrong' while N is outside the purchase reach -- it waits (pending_reach)", e4.get("wrong") is False and e4.get("pending_reach") is True, e4)
        V = SA._s524_verdict(c, sp_, T, list(batches), batches, T_at)
        check("C: the verdict: state export, the waiting key unseen with why reach_pur, the proven one in proven_on", V["state"] == "export" and n3 in V.get("proven_on", {}) and any(u["item"] == n4 and u["why"] == "reach_pur" for u in V.get("unseen") or []), (V["state"], V.get("proven_on"), [(u["item"], u["why"]) for u in V.get("unseen") or []]))
        # the cover returns (the walk's export rows on both sides: the spine's reach and the purchase_export fact): N inside both reaches -> the disagreeing voucher is wrong
        for typ, md5 in (("BILLWISE", wmd5("purB")), ("ITEMWISE", wmd5("purI"))):
            c.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at, n_rows, grand_amount_p, superseded_by) VALUES (?,?,?,?,?,?,?,?,?,NULL)",
                      (md5, typ, "W587 %s" % typ, "2026-10-01", "2026-10-18", "20261018-094500", "2026-10-18T09:47:00", 0, 0))
        c.commit()
        spc = spine_rw()
        for fam, md5 in (("PURCHASE_BILLWISE", wmd5("purB")), ("PURCHASE_ITEMWISE", wmd5("purI"))):
            spc.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (md5, "W587 %s__2026-10-01_to_2026-10-18__20261018-094500.XLS" % fam, fam, "20261018-094500", "2026-10-01", "2026-10-18", "", 1, "[]", "READ", "W587 walk"))
        spc.commit()
        spc.close()
        bump_built("s9c")
        sp_ = SW.Spine()
        T2 = SA._s524_table(c, sp_, ROOT, ent, batches, T_at, T_at, at_of)
        f3, f4 = (T2["keys"].get(kk3) or {}), (T2["keys"].get(kk4) or {})
        say("   with the purchase cover back (N inside both reaches): %s proven %s; %s wrong %s" % (n3, f3.get("proven"), n4, f4.get("wrong")))
        check("C: once N is inside both reaches the disagreeing voucher is WRONG (S528's rule kept)", f3.get("proven") is True and f4.get("wrong") is True, (f3.get("proven"), f4.get("wrong")))
        DUMP["s9"] = dict(K3=K3, K4=K4, n3=n3, n4=n4)
        c.close()
    section("9  R2-B5: an agreeing voucher is proven at once; a disagreeing one waits for the cover, then is wrong", s9)

    # ============================================================================================ 10 F-933 pending_fix
    def s10():
        c = conn()
        d9 = DUMP.get("s9") or {}
        n3, n4 = d9.get("n3"), d9.get("n4")
        if not n4:
            check("C: F-933: a wrong key with a fix: row done after the judged capture is pending_fix", False, "section 9 left no subject")
            c.close()
            return
        T_at = "2026-10-17T12:00:00"
        batches = {(9, "ISSUE", 1): dict(secs={"Medicine"}, lines=[(n3, -2, 0)], made=T_at, pk={n3: ("", 1)}),
                   (9, "ISSUE", 2): dict(secs={"Medicine"}, lines=[(n4, -5, 0)], made=T_at, pk={n4: ("", 1)})}
        ent = {k: ("W587", T_at, "17-10-2026", "amir") for k in batches}
        at_of = {k: T_at for k in batches}
        c.execute("DELETE FROM amir_job WHERE key LIKE 'fix:W587:%'")
        ins(c, "amir_job", dict(key="fix:W587:" + n4, kind="tap", subject=n4, text_hi="W587 walk", sub_hi="", created_at="2026-10-18 09:50:00", created_by="w587walk",
                                show_from="2026-10-18", said_at="2026-10-18 10:00:00", said_by="amir", said_what="done", done_at="2026-10-18 10:00:00", done_how="tap"))
        c.commit()
        bump_built("s10")
        sp_ = SW.Spine()
        T = SA._s524_table(c, sp_, ROOT, ent, batches, T_at, T_at, at_of)
        e4 = T["keys"].get(T["kof"].get(n4)) or {}
        say("   %s: fix: row done 18-10 10:00, judged capture %s -> wrong %s, pending_fix %s" % (n4, (T["N"] or {}).get("stamp_iso"), e4.get("wrong"), e4.get("pending_fix")))
        check("C: the key is not wrong: pending_fix (his tap after the judged capture)", e4.get("wrong") is False and (e4.get("pending_fix") or {}).get("item") == n4, e4)
        V = SA._s524_verdict(c, sp_, T, list(batches), batches, T_at)
        check("C: the verdict carries the row as unseen why pending_fix and in pending_fix[] (state export)", V["state"] == "export" and any(u["item"] == n4 and u["why"] == "pending_fix" for u in V["unseen"]) and any(p["item"] == n4 for p in V.get("pending_fix") or []), (V["state"], V.get("pending_fix")))
        check("C: a proof waiting only on his corrections says why='pending_fix' with the judged closing's day (never 'no_figure')", V.get("why") == "pending_fix" and V.get("closing_day") == "18-10-2026", (V.get("why"), V.get("closing_day")))
        stC = dict(count_id=ROOT, stage="C", A=dict(total=2, entered=2, open=0, pending=0, proof=dict(state="done"), verified_at="x", held=[]), B=None,
                   C=dict(total=5, entered=5, released=5, verified=0, open=0, lots=1, wrong=[], waiting_export=[dict(proof=V)], pending_fix=list(V.get("pending_fix") or [])),
                   visible=[], renames_visible=False, numbers={})
        W = SA._s521_stage_words(c, stC)
        want = "%s: Amir marked it done 18-10 10:00 \u2014 judged on the next closing taken after it" % n4
        say("   the owner's lines: %s" % [l["text"] for l in W["owner_lines"]])
        say("   Amir's card: %s" % W["card_hi"])
        check("C: the owner's line reads '%s'" % want, any(l["text"] == want and l["cls"] == "info" for l in W["owner_lines"]), [l["text"] for l in W["owner_lines"]])
        say("   the owner's English: %s" % W["owner_en"])
        check("C: the stage's English says '1 item Amir marked done after Marg's closing of 18-10-2026 -- judged on the next closing taken after it' (no 'waiting for our own figure')",
              "1 item Amir marked done after Marg's closing of 18-10-2026 — judged on the next closing taken after it" in W["owner_en"] and "our own figure" not in W["owner_en"], W["owner_en"])
        check("Amir's line carries no 'Purchase report nikaaliye' for a pending_fix wait (his export is not the wait)", "Purchase report nikaaliye" not in W["card_hi"], W["card_hi"])
        DUMP["card_hi_pf"] = W["card_hi"]
        if "card_hi_pf" in OLD:
            check("Amir's card is unchanged old vs new for the same stage (D708: the staff words do not change)", OLD["card_hi_pf"] == W["card_hi"], (OLD["card_hi_pf"], W["card_hi"]))
        # a usable capture after done_at: a synthetic 18-10 22:00 closing on the spine copy (the 09:37 rows copied under a new md5) -> judged normally again
        spc = spine_rw()
        m22 = wmd5("close22")
        spc.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (m22, "W587 STOCK_CLOSING_TOTALS__2026-10-18__20261018-220000.XLS", "STOCK_CLOSING", "20261018-220000", "", "", "2026-10-18", 1, "[]", "READ", "W587 walk"))
        spc.execute("INSERT INTO sp_close_name (md5, name, packing, k20, units) SELECT ?, name, packing, k20, units FROM sp_close_name WHERE md5=?", (m22, START_MD5))
        spc.commit()
        spc.close()
        bump_built("s10b")
        sp2 = SW.Spine()
        T2 = SA._s524_table(c, sp2, ROOT, ent, batches, T_at, T_at, at_of)
        f4 = T2["keys"].get(T2["kof"].get(n4)) or {}
        say("   with a usable 18-10 22:00 capture after his tap: N %s -> wrong %s pending_fix %s" % ((T2["N"] or {}).get("stamp_iso"), f4.get("wrong"), f4.get("pending_fix")))
        check("C: once a usable capture after done_at exists the key is judged on it like any other (wrong again here)", (T2["N"] or {}).get("md5") == m22 and f4.get("wrong") is True and not f4.get("pending_fix"), f4)
        spc = spine_rw()
        spc.execute("DELETE FROM sp_close_name WHERE md5=?", (m22,))
        spc.execute("DELETE FROM sp_export WHERE md5=?", (m22,))
        spc.commit()
        spc.close()
        c.execute("DELETE FROM amir_job WHERE key LIKE 'fix:W587:%'")
        c.commit()
        c.close()
        bump_built("s10c")
    section("10 F-933: Amir marked it done after the judged capture -> pending_fix, the owner's line", s10)

    # ============================================================================================ 11 Amir's page: the export step last
    def s11():
        s6_, h6 = GET("amir", "/finance/amir/step/6")
        s3_, h3 = GET("amir", "/finance/amir/step/3")
        b6 = banner_of(h6)
        say("   the banner as amir: %s" % b6)
        DUMP["banner"] = b6
        check("C: the banner reads '%s'" % BANNER_NEW, s6_ == 200 and b6 == BANNER_NEW, b6)
        check("C: /finance/amir/step/6 shows 'Step 3 of 7' and the Marg sudhar card", "Step 3 of 7" in h6 and ("Marg sudhar" in text(h6)), re.findall(r"Step \d of 7", h6))
        check("C: /finance/amir/step/3 shows 'Step 4 of 7' and the export screen ('Do report nikaaliye')", "Step 4 of 7" in h3 and "Do report nikaaliye" in text(h3), re.findall(r"Step \d of 7", h3))
        DUMP["step3_body"] = text(strip_banner(h3))
        if "step3_body" in OLD:
            check("the export screen's words are unchanged word for word (banner and 'Step N of 7' set apart)", OLD["step3_body"] == DUMP["step3_body"], (OLD["step3_body"][:200], DUMP["step3_body"][:200]))
        check("C: STEPS keeps its seven ids once each; ORDER = (1, 2, 6, 3, 4, 5, 7) once", all(SRC["amir_day.py"].count("    (%d, " % i) == 1 for i in range(1, 8)) and SRC["amir_day.py"].count("ORDER = (1, 2, 6, 3, 4, 5, 7)") == 1
              and tuple(n for n, _l in AD.STEPS) == (1, 2, 3, 4, 5, 6, 7))
        check("GATE_STEPS stays (2, 4, 5, 6) by id", AD.GATE_STEPS == (2, 4, 5, 6))
        c = conn()
        before = {int(r[0]) for r in c.execute("SELECT id FROM amir_step_log WHERE day=?", (today,))}
        for n in (2, 6, 3):
            s_, loc = FORM("amir", "/finance/amir/step/%d" % n, {"tick": str(n), "go": str(n)})
            say("   tap step id %d -> %s %s" % (n, s_, loc))
        new = [tuple(r) for r in c.execute("SELECT step, note FROM amir_step_log WHERE day=? AND id NOT IN (%s) ORDER BY id" % (",".join(str(i) for i in before) or "0"), (today,))]
        say("   the walk's own step-log rows: %s" % new)
        check("amir_step_log.step keeps the ids (2, 6, 3) for the taps on positions 2, 3, 4 (history is never renumbered)", [x[0] for x in new] == [2, 6, 3], new)
        s_, loc = FORM("amir", "/finance/amir/step/6", {"tick": "6", "go": "6"})
        say("   after the Marg sudhar tap the page moves to: %s (the export step, position 4)" % loc)
        posf = getattr(AD, "pos", None)
        check("C: the POST redirect steps by position (amir_day.pos): after the Marg sudhar tap (position 3) he lands on a step at position >= 3",
              posf is not None and "/finance/amir/step/" in loc and posf(int(loc.rsplit("/", 1)[-1])) >= 3, loc)
        c.execute("DELETE FROM amir_step_log WHERE day=? AND id NOT IN (%s) AND step=6 AND id=(SELECT MAX(id) FROM amir_step_log WHERE day=? AND step=6)" % (",".join(str(i) for i in before) or "0"), (today, today))
        c.commit()
        s_, b = GET("manoj", "/finance/amir/day/api/visit-summary?d=%s" % today)
        j = json.loads(b) if s_ == 200 else {}
        keys = sorted(j.keys())
        states = {st["state"] for st in j.get("steps") or []}
        DUMP["visit_keys"] = keys
        say("   the visit summary: %d keys (the brief counts 16; the live JSON has %d); steps states %s; next_step %s" % (len(keys), len(keys), sorted(states), j.get("next_step")))
        check("the visit summary reads with only the known state literals", s_ == 200 and bool(keys) and states <= STATES, (s_, len(keys), states))
        if "visit_keys" in OLD:
            check("the visit summary's keys and steps[].state literals are unchanged against the old files", OLD["visit_keys"] == keys, (OLD["visit_keys"], keys))
        c.close()
    section("11 Amir's page: the banner's order, 'Step N of 7', the ids under every tap", s11)

    # ============================================================================================ 12 the new line: bill entry after the export
    def s12():
        c = conn()
        FORM("amir", "/finance/amir/step/2", {"tick": "2", "go": "2"})            # a bill entered after the walk's step-3 tap
        s7_, h7 = GET("amir", "/finance/amir/step/7")
        s5_, h5 = GET("amir", "/finance/amir/step/5")
        sd, hd = GET("manoj", "/finance/amir/day")
        t7, t5, td = text(h7), text(h5), text(hd)
        say("   step 7 as amir: %s" % t7[:300])
        check("C: the gate holds the day: step 7 says 'Abhi kuch baaki hai' with the line '%s'" % GATE_HI, "Abhi kuch baaki hai" in t7 and GATE_HI in t7, t7[:400])
        check("C: the red band on a later position (Bills, position 6): '%s. Kholiye' linking to the export step" % BAND_HI, (BAND_HI in t5) and ("id=reexport" in h5) and ("href='/finance/amir/step/3'" in h5.split("id=reexport")[1][:400] if "id=reexport" in h5 else False), t5[:300])
        s2_, h2 = GET("amir", "/finance/amir/step/2")
        check("no band on an earlier position (Bill entry, position 2)", BAND_HI not in text(h2))
        check("C: the owner's view says 're-export due since hh:mm'", sd == 200 and re.search(r"re-export due since \d\d:\d\d", td) is not None, td[:300])
        FORM("amir", "/finance/amir/step/3", {"tick": "3", "go": "3"})            # the export taken again
        s7b, h7b = GET("amir", "/finance/amir/step/7")
        s5b, h5b = GET("amir", "/finance/amir/step/5")
        check("a fresh step-3 tap clears it (no gate line, no band)", GATE_HI not in text(h7b) and BAND_HI not in text(h5b))
        FORM("amir", "/finance/amir/step/2", {"tick": "2", "go": "2"})
        s7c, h7c = GET("amir", "/finance/amir/step/7")
        check("C: due again after another bill-entry tap", GATE_HI in text(h7c))
        at = (dt.datetime.now() + dt.timedelta(minutes=1)).replace(microsecond=0)
        c.execute("DELETE FROM mi_file WHERE md5 LIKE 'w587%'")
        ins(c, "mi_file", dict(md5=wmd5("mifile"), drive_id="", drive_name="W587 purchase bill-wise.xlsx", drive_folder="w587walk", drive_mtime="", size=1,
                               stamp=at.strftime("%Y%m%d-%H%M%S"), type="PURCHASE_BILLWISE", variant="DEFAULT", date_from="2026-10-01", date_to=today,
                               verdict="VERIFIED", reason="", server_name="", kept=0, lines=0, pc_type="", pc_verdict="", agree="", received_at=at.isoformat() + "+05:30", source="w587walk"))
        c.commit()
        s7d, h7d = GET("amir", "/finance/amir/step/7")
        check("a VERIFIED purchase export landing in mi_file after the step-2 tap clears it too (the fact, not the tap)", GATE_HI not in text(h7d), text(h7d)[:300])
        c.execute("DELETE FROM mi_file WHERE md5 LIKE 'w587%'")
        c.commit()
        FORM("amir", "/finance/amir/step/3", {"tick": "3", "go": "3"})            # leave the copy's day not due for the screens below
        c.close()
    section("12 the new line (F-926 / D737 D): a bill entered after the export holds the day until a fresh export", s12)

    # ============================================================================================ 13 staff screens word for word
    def s13():
        pages = [("amir", "/finance/amir/step/%d" % n, False) for n in range(1, 8)] + [
            ("darpan", "/finance/stockmatch", False), ("darpan", "/finance/stockmatch/api/state", False), ("darpan", "/finance/darpan/kal", True),
            ("shavez", "/finance/reports/aaj", True), ("reception", "/finance/porders", True), ("manoj", "/finance/stock/api/now", False), ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed = {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if path.startswith("/finance/stock/api/") or path.endswith("/state") or path.endswith("needs-you"):
                try:
                    j = json.loads(h)
                    for k in ("you", "ours_at", "stored_at", "stored_text", "readiness", "cache", "refresh_ms", "watch", "at", "built", "generated_at"):
                        j.pop(k, None) if isinstance(j, dict) else None
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = text(strip_banner(h) if u == "amir" else h)
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            lines = [l for l in lines if "W587" not in l]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                os_, ns = set(old), set(lines)
                gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                if gone or new:
                    changed[(u, path)] = (gone, new)
                    say("   WORDS CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:4]:
                        say("      - %s" % l[:240])
                    for l in new[:4]:
                        say("      + %s" % l[:240])
                else:
                    say("   words unchanged on %s for %s" % (path, u))
        if a.old_dump:
            bad = {}
            for (u, path), (gone, new) in changed.items():
                if u == "manoj":
                    ok = True                                   # the owner's pages gain the lines named (the start capture's figures, pending_fix, the start-capture lines)
                elif u == "amir":
                    ok = False                                  # Amir's pages: the banner and 'Step N of 7' are set apart by strip_banner -- nothing else may differ
                elif u == "darpan" and path.startswith("/finance/stockmatch"):
                    # the stage's proof may now stand on a later capture (the accepted start capture is the newest try): its day moves, the words are the stage's own
                    ok = all(("Amir" in g or "voucher" in g.lower() or "proof" in g.lower() or "as_after" in g or "closing of" in g) for g in gone + new)
                else:
                    ok = False
                if not ok:
                    bad[(u, path)] = (gone[:3], new[:3])
            check("no staff screen changed its words beyond the brief's allowed differences (%d page(s) differ)" % len(changed), not bad, bad)
    section("13 the staff screens word for word (the banner's order and 'Step N of 7' set apart); the owner's pages", s13)

    # ============================================================================================ 14 greps
    def s14():
        pys = [n for n in os.listdir(fin) if n.endswith(".py")]
        check("C: _s524_closings is nowhere in the finance folder's .py files", not any("_s524_closings(" in read(fin, n) for n in pys))
        check("C: 'sp_close WHERE as_on' is not in stock_app.py", "sp_close WHERE as_on" not in SRC["stock_app.py"])
        check("C: early_bill( is nowhere", not any("early_bill(" in read(fin, n) for n in pys))
        check("C: def purchase_cover( / def verify_start( / def start_ready( once each in stock_figure.py", all(SRC["stock_figure.py"].count("def %s(" % f) == 1 for f in ("purchase_cover", "verify_start", "start_ready")))
        check("C: shelf_figure passes con to tryable", "SF.tryable(c, R, con, ctx)" in SRC["shelf_figure.py"])
        check("C: KIT = \"S587 in amir_day; stock_figure and stock_watch name the kit", 'KIT = "S587' in SRC["amir_day.py"] and SF.KIT == KIT and SW.KIT == KIT)
        check("C: the two settings appear once each in stock_watch.SETTINGS", SRC["stock_watch.py"].count('key="count.start_capture"') == 1 and SRC["stock_watch.py"].count('key="count.start_unexplained_max"') == 1)
        check("C: stock_now.html appends the fifth heading to the items table by id (#itemtbl), never the first thead on the page", 'querySelector("#itemtbl thead tr")' in SRC["stock_now.html"] and 'id="itemtbl"' in SRC["stock_now.html"] and 'querySelector("table thead tr")' not in SRC["stock_now.html"])
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
    section("14 the grep tests (charter 2, 9); no ten-digit run", s14)

    # ============================================================================================ 15 the spine untouched
    def s15():
        schema1 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
        check("the spine copy's schema is unchanged by the walk (no table added to the spine)", schema0 == schema1, [s for s in schema1 if s not in schema0])
        check("C: no new code writes to the spine: stock_figure writes finance.db's stock_start_capture only (one INSERT, one UPDATE, both on stock_start_capture)",
              SRC["stock_figure.py"].count("INSERT OR IGNORE INTO stock_start_capture") == 1 and SRC["stock_figure.py"].count("UPDATE stock_start_capture") == 1
              and not re.search(r"(INSERT|UPDATE|DELETE)\s+(INTO\s+|FROM\s+)?sp_", SRC["stock_figure.py"]) and "mode=ro" in read(fin, "stock_watch.py"))
        try:
            r = subprocess.run([sys.executable, "-B", os.path.join(fin, "spine", "selftest_spine.py")], cwd=os.path.join(fin, "spine"), capture_output=True, text=True, timeout=600)
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            check("selftest_spine.py is green on the copy's spine code (%s)" % tail[0][:60], r.returncode == 0 and "SELFTEST OK" in (r.stdout or ""), (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
        except Exception as e:                                 # noqa: BLE001
            check("selftest_spine.py ran", False, str(e)[:200])
    section("15 the spine untouched: schema, no spine write, selftest green", s15)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S587: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S587: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S587: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S587: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
