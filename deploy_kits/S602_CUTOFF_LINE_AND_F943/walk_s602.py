#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s602.py -- kit S602_CUTOFF_LINE_AND_F943 (19-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s602.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s602.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... [--witness-dir /root/finance/spine]
    python3 -B walk_s602.py --jscheck <darpan_kal.html>        (the Python tokenizer check of the page's one <script> block; Node is not on the box)
The real finance app in one process (the walk's own header session -- its own secret and user store, never the live ones): Darpan,
reception, Amir, Shavez and the owner sign in and their pages are rendered as text (the page dumps strip <script>: renderOrder runs only
in a browser, so NO DOM is rendered anywhere -- R1-B1; the tab's data is proved on /finance/darpan/kal/api/order and the fragment is
proved in the built html). Its own rows by key (W602 ...), never by counting. The spine COPY is never written by the code under test
(bytes compared); the walk's two synthetic spines (emptied / a future bill) are second copies. No phone number is printed.
Sections follow the brief's section 4 (controls 1-8); the page dumps (4) run FIRST, before the walk writes its own rows. --expect-red is
the negative control: the same walk on the OLD files, every 'C:' check must be red. --state prints the install-day state. Prints
'WALK OK S602 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import importlib.util
import inspect
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

KIT = "S602_CUTOFF_LINE_AND_F943"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
FOUR = ("darpan_kal.py", "darpan_kal.html", "spine/spine_read.py", "stock_figure.py")
ANCHOR = "'</div>':'')+'</div>';"
TAIL = "</div>':'')+'</div>';"
FRAG = ("'</div>':'')+(j.purchase_upto?'<div class=\"muted\">Marg में खरीद '+esc(j.purchase_upto.slice(8,10)+'-'+j.purchase_upto.slice(5,7))"
        "+' के बिल तक चढ़ी है — उसके बाद आया माल इस सूची के स्टॉक में नहीं है</div>':'')+'</div>';")
FRAG_LINE = 427
STAYS = "stays pending"
RUN, FAILS, CTRL, OUT = [0], [], [], []


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:900] + "]") if (got is not None and not cond) else ""))
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


def text_lines(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"</(div|p|li|tr|h\d|button|a|td|th)>|<br\s*/?>", "\n", s)
    out = []
    for l in s.split("\n"):
        t = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", l))).strip()
        if t:
            out.append(t)
    return out


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
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "DUTY_MAP_JSON"):
        os.environ.pop(k, None)


def read(fin, name):
    return open(os.path.join(fin, name), encoding="utf-8").read()


def fn_body(src, name):
    m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|# -{10,}|[A-Z_]+ = ))" % re.escape(name), src, flags=re.S | re.M)
    return m.group(0) if m else ""


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def load_spine_read(fin):
    p = os.path.join(fin, "spine", "spine_read.py")
    spec = importlib.util.spec_from_file_location("spine_read_w602", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def pu_direct(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        return c.execute("SELECT MAX(date) FROM sp_purchase_bill WHERE direction='PURCHASE' AND date<=?", (dt.date.today().isoformat(),)).fetchone()[0]
    finally:
        c.close()


# ======================================================================================================= the JS check (R1-B1: no DOM)
JS_KW = ("return", "typeof", "in", "of", "new", "delete", "void", "throw", "case", "do", "else", "instanceof", "yield", "await")


def js_check(js):
    """A Python tokenizer over a <script> block (Node is not on the box): comments and regex literals skipped, every ' / \" string closed on
    its own line, every template literal closed, (), [], {} balanced. Returns (ok, problems, counts)."""
    i, n, line = 0, len(js), 1
    stack, probs = [], []
    pairs = {")": "(", "]": "[", "}": "{"}
    last = ""                                                  # the last significant token kind: decides regex vs divide
    counts = dict(strings=0, regex=0, comments=0, templates=0)
    while i < n and not probs:
        c = js[i]
        if c == "\n":
            line += 1
            i += 1
            continue
        if c in " \t\r":
            i += 1
            continue
        if js.startswith("//", i):
            j = js.find("\n", i)
            i = n if j < 0 else j
            counts["comments"] += 1
            continue
        if js.startswith("/*", i):
            j = js.find("*/", i + 2)
            if j < 0:
                probs.append("unclosed comment from line %d" % line)
                break
            line += js.count("\n", i, j)
            i = j + 2
            counts["comments"] += 1
            continue
        if c in "'\"":
            j = i + 1
            while j < n and js[j] != c and js[j] != "\n":
                j += 2 if js[j] == "\\" else 1
            if j >= n or js[j] != c:
                probs.append("unclosed %s string at line %d" % (c, line))
                break
            i = j + 1
            last = "v"
            counts["strings"] += 1
            continue
        if c == "`":
            j = i + 1
            while j < n and js[j] != "`":
                if js[j] == "\\":
                    j += 1
                elif js[j] == "\n":
                    line += 1
                j += 1
            if j >= n:
                probs.append("unclosed template literal from line %d" % line)
                break
            i = j + 1
            last = "v"
            counts["templates"] += 1
            continue
        if c == "/" and (last == "" or last in "(,=:[!&|?{};+-*%<>~^" or last == "k"):
            j, incls = i + 1, False
            while j < n and js[j] != "\n":
                ch = js[j]
                if ch == "\\":
                    j += 2
                    continue
                if incls:
                    if ch == "]":
                        incls = False
                elif ch == "[":
                    incls = True
                elif ch == "/":
                    break
                j += 1
            if j >= n or js[j] != "/":
                probs.append("unclosed regex literal at line %d" % line)
                break
            j += 1
            while j < n and js[j].isalpha():
                j += 1
            i = j
            last = "v"
            counts["regex"] += 1
            continue
        if c in "([{":
            stack.append((c, line))
            last = c
            i += 1
            continue
        if c in ")]}":
            if not stack or stack[-1][0] != pairs[c]:
                probs.append("unbalanced '%s' at line %d" % (c, line))
                break
            stack.pop()
            last = c
            i += 1
            continue
        if c.isalnum() or c in "_$":
            j = i
            while j < n and (js[j].isalnum() or js[j] in "_$"):
                j += 1
            w = js[i:j]
            last = "k" if w in JS_KW else "v"
            i = j
            continue
        last = c
        i += 1
    if not probs and stack:
        probs.append("unclosed '%s' from line %d" % stack[-1])
    return (not probs), probs, counts


def script_block(html):
    m = re.search(r"<script>(.*?)</script>", html, flags=re.S)
    return (m.group(1), html[:m.start(1)].count("\n")) if m else ("", 0)


def jscheck_file(path):
    h = open(path, encoding="utf-8").read()
    js, off = script_block(h)
    ok, probs, counts = js_check(js)
    print("jscheck %s: <script> block %d lines from line %d; %s; %s" % (os.path.basename(path), js.count("\n"), off + 1,
                                                                        "GREEN" if ok else "RED " + "; ".join(probs), counts))
    return 0 if ok and js else 1


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import order_rules as OR                                  # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    new = "read_only" in inspect.signature(SF.Ctx.__init__).parameters
    say("STATE %s: files %s; stock_figure v%s KIT %s" % (label, "NEW (S602)" if new else "OLD", SF.VERSION, SF.KIT))
    spine = os.path.join(fin, "spine", "spine.db")
    sr = load_spine_read(fin)
    direct = pu_direct(spine)
    meth = None
    if hasattr(sr.Spine, "purchases_upto"):
        sp = sr.Spine(spine)
        try:
            meth = sp.purchases_upto()
        finally:
            sp.con.close()
    say("STATE %s: purchases_upto on this side's spine copy: direct SQL %s; spine_read.purchases_upto() %s" % (label, direct, meth if hasattr(sr.Spine, "purchases_upto") else "(no such method: OLD)"))
    say("STATE %s: order.source %s; darpan_list_time %s; the list open now: %s" % (label, OS.source(con), OR.darpan_list_time(con), OR.darpan_list_open(con)))
    p = DK._s485_payload(con, ("staff", None))
    say("STATE %s: api/order's keys: %s" % (label, sorted(p.keys())))
    say("STATE %s: api/order purchase_upto = %s (opened %s, suppliers %d, source %s)" % (label, p.get("purchase_upto", "(absent)"), p["opened"], p["n_suppliers"], p["source"]))
    recent = (SF.today() - dt.timedelta(days=SF.LATE_DAYS)).isoformat()
    rows = [dict(r) for r in con.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at FROM stock_start_capture WHERE as_on>=? ORDER BY stamp_iso", (recent,))]
    say("STATE %s: stock_start_capture rows within LATE_DAYS (%d): %s" % (label, SF.LATE_DAYS, len(rows)))
    for r in rows:
        say("   %s printed %s taken %s -> end %s: %s%s (checked %s)" % (r["md5"][:8], r["as_on"], r["stamp_iso"], r["end_day"], r["verdict"], (" / " + r["reason"]) if r["reason"] else "", r["checked_at"]))
    wd = a.witness_dir or os.path.join(fin, "spine")
    files = sorted((os.path.getmtime(os.path.join(wd, f)), f) for f in os.listdir(wd) if f.startswith("stock_figure_witness_") and f.endswith(".txt")) if os.path.isdir(wd) else []
    if files:
        newest = files[-1][1]
        head = open(os.path.join(wd, newest), encoding="utf-8").readline().strip()
        say("STATE %s: the newest witness file %s (mtime %s): %s" % (label, newest, dt.datetime.fromtimestamp(files[-1][0]).replace(microsecond=0).isoformat(), head))
    else:
        say("STATE %s: no witness file in %s" % (label, wd))
    con.rollback()
    con.close()
    say("STATE OK S602 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    ap.add_argument("--jscheck", default="")
    for k in ("--fin", "--db", "--adb", "--marg"):
        ap.add_argument(k, default="")
    for k in ("--dump", "--old-dump", "--witness-dir"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    if a.jscheck:
        return jscheck_file(a.jscheck)
    for k in ("fin", "db", "adb", "marg"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S602_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S602 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    import porders as PO                                      # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    for m in (fa, SF, SW, OR, OS, DK, PO, PA):
        assert m.__file__.startswith(fin), m.__file__
    NEW = "read_only" in inspect.signature(SF.Ctx.__init__).parameters
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure v%s %s (%s)"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", SF.VERSION, SF.KIT, "NEW" if NEW else "OLD"))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    schema0 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
    spine_md5_0 = hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest()
    SRC = {n: read(fin, n) for n in FOUR}
    SR = load_spine_read(fin)
    HAS = hasattr(SR.Spine, "purchases_upto")
    today = dt.date.today()
    TODAY = today.isoformat()
    SIDE = "old" if a.expect_red else "new"
    PU = {"day": None}

    def GET(u, path, follow=False, role=None):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": role or ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def set_source(c, v):
        c.execute("INSERT INTO setting (key, value, note) VALUES ('order.source', ?, 'W602 walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (v,))
        c.commit()

    c_ = conn()
    PO.ensure_schema(c_)
    OR.ensure(c_)
    c_.commit()
    SRC0 = OS.source(c_)
    ORTHO = OR._ortho_norm(c_)
    c_.close()
    sw0 = SW.Spine()
    assert sw0.ok and SW.SPINE_DB == SPINE_PATH, (sw0.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    say("   today %s; order.source %s; the orthotic vendor %s; spine_read.Spine has purchases_upto: %s" % (TODAY, SRC0, ORTHO, HAS))

    # ============================================================================================ 4 (first) the pages and the APIs, dumped
    def s4():
        saved_detect = PO.detect_supplies                     # the screens are read with Marg's clearing held still
        PO.detect_supplies = lambda con: 0
        pages = [("darpan", "/finance/darpan/kal", True), ("darpan", "/finance/darpan/kal/api/day", False), ("darpan", "/finance/darpan/kal/api/order", False),
                 ("reception", "/finance/porders", True), ("reception", "/finance/porders/s454/order", False),
                 ("amir", "/finance/amir", True)] + [("amir", "/finance/amir/step/%d" % n, False) for n in range(1, 8)] + [
                 ("shavez", "/finance/reports/aaj", True), ("manoj", "/finance/darpan/kal/api/order", False), ("manoj", "/finance/stock/api/now", False),
                 ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed, got_pu = {}, {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            if u == "manoj" and path == "/finance/darpan/kal/api/order" and s == 403:
                s, h = GET(u, path, follow, role="checker")   # the owner's view through the walk's header session: the checker role
                say("   (the owner's api/order needed the checker role in the walk's header session; stated)")
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "date", "yesterday_date", "ours_at", "stored_at", "stored_text", "readiness", "cache", "refresh_ms", "watch", "now", "server_time", "user"):
                            j.pop(k, None)
                        if path.endswith("/api/order"):
                            got_pu[u] = ("absent" if "purchase_upto" not in j else j.pop("purchase_upto"))
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                    changed[(u, path)] = (gone, new)
                    say("   CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:6]:
                        say("      - %s" % l[:240])
                    for l in new[:6]:
                        say("      + %s" % l[:240])
                else:
                    say("   unchanged on %s for %s" % (path, u))
        PO.detect_supplies = saved_detect
        say("   api/order purchase_upto as served: darpan %s, the owner %s" % (got_pu.get("darpan"), got_pu.get("manoj")))
        DUMP["s4"] = dict(pu=got_pu)
        check("C: api/order (Darpan's, and the owner's read-only view) carries purchase_upto as an ISO day in the default state (%s)" % got_pu,
              NEW and re.match(r"^\d{4}-\d\d-\d\d$", str(got_pu.get("darpan"))) is not None and got_pu.get("manoj") == got_pu.get("darpan"), got_pu)
        if a.old_dump:
            check("every page dump (Darpan's tab page and day API, reception's order pages, Amir's steps, Shavez's, the owner's stock-now and needs-you) and api/order with purchase_upto masked are byte-equal to the OLD files' dumps (%d differ)" % len(changed),
                  not changed, {k: (v[0][:3], v[1][:3]) for k, v in changed.items()})
            check("the OLD dump served api/order WITHOUT purchase_upto and this one WITH it (the one new key)", OLD.get("s4", {}).get("pu", {}).get("darpan") == "absent" and got_pu.get("darpan") != "absent", OLD.get("s4"))
    section("4  the pages and the APIs dumped (no DOM is rendered; the page dumps strip <script>) -- byte-equal OLD vs NEW but the one key", s4)

    # ============================================================================================ 1 purchases_upto on the copy
    def s1():
        direct = pu_direct(SPINE_PATH)
        meth = None
        if HAS:
            sp = SR.Spine(SPINE_PATH)
            try:
                meth = sp.purchases_upto()
            finally:
                sp.con.close()
        PU["day"] = meth
        say("   direct SQL on the spine copy: MAX(date) of PURCHASE bills dated <= today = %s; purchases_upto() = %s" % (direct, meth if HAS else "(no such method)"))
        check("C: spine_read.purchases_upto() on the copy equals the direct MAX(date) (an ISO day)", HAS and meth == direct and re.match(r"^\d{4}-\d\d-\d\d$", str(meth)) is not None, (HAS, meth, direct))
        empty = os.path.join(os.path.dirname(dbp), "spine_empty_%s.db" % SIDE)
        copy_db(SPINE_PATH, empty)
        e = sqlite3.connect(empty)
        e.execute("DELETE FROM sp_purchase_bill")
        e.commit()
        e.close()
        pe = None
        if HAS:
            sp = SR.Spine(empty)
            try:
                pe = sp.purchases_upto()
            finally:
                sp.con.close()
        check("C: on a spine copy with sp_purchase_bill emptied purchases_upto() is None (MAX over an empty table: one row, d None)", HAS and pe is None, (HAS, pe))
        fut = os.path.join(os.path.dirname(dbp), "spine_future_%s.db" % SIDE)
        copy_db(SPINE_PATH, fut)
        f = sqlite3.connect(fut)
        tomorrow = (today + dt.timedelta(days=1)).isoformat()
        f.execute("INSERT INTO sp_purchase_bill (supplier, supkey, bill, date, amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?)",
                  ("W602 VENDOR", SW.supkey("W602 VENDOR"), "W602-FUTURE", tomorrow, 0, "PURCHASE", "w602"))
        f.commit()
        raw_max = f.execute("SELECT MAX(date) FROM sp_purchase_bill WHERE direction='PURCHASE'").fetchone()[0]
        f.close()
        pf = None
        if HAS:
            sp = SR.Spine(fut)
            try:
                pf = sp.purchases_upto()
            finally:
                sp.con.close()
        say("   a synthetic bill dated %s on a second copy: raw MAX(date) %s; purchases_upto() %s" % (tomorrow, raw_max, pf if HAS else "(no such method)"))
        check("C: a synthetic PURCHASE bill dated tomorrow leaves purchases_upto() unchanged (the future date ignored; raw MAX moved)", HAS and pf == direct and raw_max == tomorrow, (HAS, pf, direct, raw_max))
        DUMP["s1"] = dict(direct=direct, meth=meth, pe=pe, pf=pf)
    section("1  purchases_upto on the spine copy: equals the direct read; None on an emptied copy; a future bill ignored", s1)

    # ============================================================================================ 2 the payload
    def s2():
        c = conn()
        OR._s470_spine().con.close()                          # load the module once; then count every Spine the payload opens
        mod = OR._S470_MOD["mod"]
        made = []
        base_spine = mod.Spine

        class WSpine(base_spine):
            def __init__(self, *args, **kw):
                base_spine.__init__(self, *args, **kw)
                made.append(self)
        mod.Spine = WSpine
        try:
            p = DK._s485_payload(c, ("staff", None))
            n_made = len(made)

            def closed(s):
                try:
                    s.con.execute("SELECT 1")
                    return False
                except sqlite3.ProgrammingError:
                    return True
            n_closed = sum(1 for s in made if closed(s))
            say("   payload keys: %s" % sorted(p.keys()))
            say("   purchase_upto = %s; spine handles opened by the payload: %d, closed after it: %d" % (p.get("purchase_upto", "(absent)"), n_made, n_closed))
            check("C: _s485_payload carries purchase_upto equal to control 1's day", NEW and "purchase_upto" in p and p["purchase_upto"] == PU["day"] and PU["day"] is not None, (p.get("purchase_upto", "(absent)"), PU["day"]))
            check("C: the payload opened a fresh spine handle for the read and CLOSED it (R1-B2: %d opened, %d closed)" % (n_made, n_closed), NEW and n_made >= 1 and n_closed == n_made, (n_made, n_closed))
            masked = {k: v for k, v in p.items() if k != "purchase_upto"}
            DUMP["s2"] = dict(payload=masked, n_made=n_made)
            if OLD.get("s2"):
                op = OLD["s2"]["payload"]
                diff = [k for k in set(op) | set(masked) if json.loads(json.dumps(op.get(k), default=str)) != json.loads(json.dumps(masked.get(k), default=str))]
                check("C: every other key of the payload equals the OLD files' payload, key by key (R1-C7: the one new key masked)", NEW and not diff and "purchase_upto" not in op, diff)
                check("the payload opened exactly one more spine handle than on the OLD files (%d vs %d)" % (n_made, OLD["s2"]["n_made"]), n_made == OLD["s2"]["n_made"] + 1, (n_made, OLD["s2"]["n_made"]))
            missing = os.path.join(os.path.dirname(dbp), "no_such_spine_%s.db" % SIDE)
            os.environ["SPINE_DB"] = missing
            try:
                p2 = DK._s485_payload(c, ("staff", None))
            finally:
                os.environ.pop("SPINE_DB", None)
            m2 = {k: v for k, v in p2.items() if k != "purchase_upto"}
            say("   with SPINE_DB at a missing file: purchase_upto = %s; the rest equal: %s" % (p2.get("purchase_upto", "(absent)"), m2 == masked))
            check("C: with SPINE_DB pointed at a missing file the payload still answers, purchase_upto None and every other key equal (fail-soft, never a stand-in)",
                  NEW and "purchase_upto" in p2 and p2["purchase_upto"] is None and m2 == masked, (p2.get("purchase_upto", "(absent)"), [k for k in m2 if m2[k] != masked.get(k)]))
        finally:
            mod.Spine = base_spine
            c.close()
    section("2  the payload: purchase_upto; the spine handle closed; every other key as OLD; a missing spine leaves the line out", s2)

    # ============================================================================================ 3 the fragment, the JS check, the API
    def s3():
        ht = SRC["darpan_kal.html"]
        n_frag = ht.count(FRAG)
        n_anchor = ht.count(ANCHOR)
        n_tail = ht.count(TAIL)
        at = ht.find(FRAG)
        line_no = ht[:at].count("\n") + 1 if at >= 0 else None
        say("   the fragment occurs %d time(s) at line %s; the OLD anchor %r occurs %d time(s) (consumed by the fragment on NEW), the heading's closing %r %d time(s); the file has %d lines"
            % (n_frag, line_no, ANCHOR, n_anchor, TAIL, n_tail, ht.count("\n")))
        check("C: (a) the exact fragment is in the built html exactly once, at line %d, inside renderOrder, as the tail of the heading's concatenation (the OLD anchor consumed, the heading's closing once)" % FRAG_LINE,
              n_frag == 1 and line_no == FRAG_LINE and n_anchor == 0 and n_tail == 1 and ht.find("function renderOrder(") < at < ht.find("async function opakka("), (n_frag, line_no, n_anchor, n_tail))
        js, off = script_block(ht)
        ok, probs, counts = js_check(js)
        say("   the <script> block: %d lines from line %d; tokenizer %s %s" % (js.count("\n"), off + 1, "GREEN" if ok else "RED " + "; ".join(probs), counts))
        check("the page's one <script> block passes the Python tokenizer check (strings closed, brackets balanced; Node is not on the box)", ok and ht.count("<script") == 1, probs)
        bad_js = js.replace("स्टॉक में नहीं है</div>':'')", "स्टॉक में नहीं है</div>:'')") if NEW else js.replace("'</div>':'')+'</div>';", "'</div>:'')+'</div>';")
        ok2, probs2, _c2 = js_check(bad_js)
        check("the checker can go red: the same block with one quote of the fragment dropped is RED (%s)" % "; ".join(probs2)[:80], not ok2 and bad_js != js, (ok2, bad_js == js))
        DUMP["s3"] = dict(n_frag=n_frag, line_no=line_no, lines=ht.count("\n"))
        if OLD.get("s3"):
            check("the html has the same number of lines as the OLD file (one line changed, none added)", OLD["s3"]["lines"] == ht.count("\n"), (OLD["s3"]["lines"], ht.count("\n")))
        # (b) the API with the list open and a supplier present (walk_s593 s5's shape, R1-B1)
        c = conn()
        set_source(c, "darpan")
        os.environ["ORDER_CLOCK"] = "10:00"
        try:
            vend = c.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 AND supplier_norm<>? "
                             "AND supplier_norm NOT IN (SELECT supplier_norm FROM order_proposal WHERE day=? AND kind='fixed') ORDER BY supplier_norm LIMIT 1", (ORTHO, TODAY)).fetchone()
            kind = "fixed"
            if vend is None:                                  # every live rule already has today's fixed proposal: the walk's row is a 'darpan' kind of its own
                vend = c.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 AND supplier_norm<>? "
                                 "AND supplier_norm NOT IN (SELECT supplier_norm FROM order_proposal WHERE day=? AND kind='darpan') ORDER BY supplier_norm LIMIT 1", (ORTHO, TODAY)).fetchone()
                kind = "darpan"
            item = OR._s470_master(c, PA)[0][0]
            lines = [dict(item=item, on_hand=10, qty=10, unit="strip", pack_size=10, packing="1*10", rate_p=1000, per_day=1.0, cover_after=20.0, value_p=10000, confirm=False, why=["W602 walk"])]
            pid = ins(c, "order_proposal", dict(day=TODAY, supplier_norm=vend["supplier_norm"], vendor=vend["supplier"], kind=kind, status="open", lines=json.dumps(lines), total_p=10000, reason="W602 walk", prepared_at=OR.now_iso()))
            c.commit()
            say("   the walk's proposal: %s (%s, kind %s, id %s) beside today's real proposals" % (vend["supplier"], vend["supplier_norm"], kind, pid))
            s, h = GET("darpan", "/finance/darpan/kal/api/order")
            j = json.loads(h) if s == 200 else {}
            s2_, h2 = GET("manoj", "/finance/darpan/kal/api/order")
            if s2_ == 403:
                s2_, h2 = GET("manoj", "/finance/darpan/kal/api/order", role="checker")
            j2 = json.loads(h2) if s2_ == 200 else {}
            say("   Darpan's api/order (%s): opened %s, source %s, suppliers %s, purchase_upto %s; the owner's (%s): me %s, editable %s, purchase_upto %s"
                % (s, j.get("opened"), j.get("source"), [b.get("display") for b in j.get("suppliers", [])], j.get("purchase_upto", "(absent)"), s2_, j2.get("me"), j2.get("editable"), j2.get("purchase_upto", "(absent)")))
            check("C: (b) /finance/darpan/kal/api/order as darpan with the list OPEN and a supplier present (the walk's W602 proposal, source darpan, ORDER_CLOCK 10:00) carries purchase_upto = control 1's day",
                  NEW and s == 200 and j.get("opened") is True and j.get("source") == "darpan" and bool(j.get("suppliers")) and j.get("purchase_upto") == PU["day"] and PU["day"] is not None,
                  (s, j.get("opened"), j.get("source"), len(j.get("suppliers", [])), j.get("purchase_upto", "(absent)")))
            check("C: (b) the owner's call of the same API carries it too (me owner; his view is read-only in the browser: ro = j.me === 'owner')", NEW and s2_ == 200 and j2.get("me") == "owner" and j2.get("purchase_upto") == PU["day"],
                  (s2_, j2.get("me"), j2.get("purchase_upto", "(absent)")))
            c.execute("UPDATE order_proposal SET status='dropped' WHERE id=? AND reason='W602 walk'", (pid,))
            c.commit()
        finally:
            os.environ.pop("ORDER_CLOCK", None)
            set_source(c, "marg_sheet")
            check("order.source restored on the copy", OS.source(c) == "marg_sheet")
            c.close()
    section("3  the fragment in the built html (exactly once, anchored) and the JS check; api/order with the list open carries the day", s3)

    # ============================================================================================ 5 F-943: the witness on a read-only connection
    def s5():
        sw = SW.Spine()
        recent = (SF.today() - dt.timedelta(days=SF.LATE_DAYS)).isoformat()
        caps = SF.captures(sw, SF.Ctx(None, sw))              # no connection: nothing is judged here
        starts = [x for x in caps if x["start"] and x["as_on"] >= recent]
        check("a START capture within LATE_DAYS exists on the spine copy (the judge's food)", bool(starts), [(x["as_on"], x["stamp_iso"]) for x in caps if x["start"]][-3:])
        S = max(starts, key=lambda x: x["stamp"]) if starts else None
        c = conn()
        SF._ensure_start(c)
        c.commit()

        def row():
            r = c.execute("SELECT md5, as_on, stamp_iso, end_day, verdict, reason, checked_at, n_keys, n_excluded, n_unexplained FROM stock_start_capture WHERE md5=?", (S["md5"],)).fetchone() if S else None
            return dict(r) if r else None
        r0 = row()
        say("   the start capture: printed %s taken %s (%s); its row on the copy: %s" % (S["as_on"] if S else None, S["stamp_iso"] if S else None, (S["md5"][:8] if S else None), r0))
        if r0 and r0["verdict"] in SF.START_FINAL:
            c.execute("UPDATE stock_start_capture SET verdict='pending', reason='W602 walk: set back to pending on the copy' WHERE md5=?", (S["md5"],))
            c.commit()
            r0 = row()
            say("   (its verdict was final on the copy: set back to pending ON THE COPY so the judge has something to do -- stated)")
        c.close()
        con_ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True, timeout=60)
        err, saved = io.StringIO(), sys.stderr
        sys.stderr = err
        t0 = time.time()
        try:
            path = SF.witness(con_ro, SW.Spine(), out_dir=a.dump)
        finally:
            sys.stderr = saved
            con_ro.close()
        e = err.getvalue()
        c = conn()
        r1 = row()
        c.close()
        lines = open(path, encoding="utf-8").read().splitlines()
        say("   witness(con_ro, sp) in %.1fs -> %s (%d lines); stderr: %s" % (time.time() - t0, os.path.basename(path), len(lines), repr(e.strip()[:200]) if e.strip() else "(empty)"))
        say("   header: %s" % lines[0][:160])
        check("C: NEW: the witness on a mode=ro connection leaves stderr EMPTY of 'stays pending' (the judge stayed out: no write attempted)", NEW and STAYS not in e and "readonly" not in e, e.strip()[:300])
        check("C: the stock_start_capture row is unchanged by the read-only run", NEW and r1 == r0, (r0, r1))
        check("the witness file was written with its header and the capture line", len(lines) > 3 and lines[0].startswith("stock_figure witness") and "newest usable capture" in lines[1], lines[:2])
        DUMP["s5"] = dict(witness=lines[1:], row0=r0, stderr=e.strip())
        if OLD.get("s5"):
            o = OLD["s5"]["witness"]
            same = o == lines[1:]
            if not same:
                d = [(i, o[i] if i < len(o) else None, lines[1:][i] if i < len(lines) - 1 else None) for i in range(max(len(o), len(lines) - 1)) if (o[i] if i < len(o) else None) != (lines[1:][i] if i < len(lines) - 1 else None)]
                say("   witness lines that differ from the OLD run's: %d, e.g. %s" % (len(d), d[:3]))
            check("C: the witness file carries the SAME figures as the OLD files' run (every line after the header's timestamp equal) -- and the OLD run's stderr carried the line",
                  NEW and same and STAYS in OLD["s5"]["stderr"], (same, OLD["s5"]["stderr"][:160]))
        # the judge still works where it should: a writable connection
        c = conn()
        ctx = SF.Ctx(c, SW.Spine())
        t1 = time.time()
        SF.captures(SW.Spine(), ctx)
        r2 = row()
        c.close()
        say("   captures(sp, Ctx(con_rw, sp)) in %.1fs: the row now %s" % (time.time() - t1, r2))
        judged = r2 is not None and (r1 is None or (r2["checked_at"] or "") > (r1["checked_at"] or ""))
        check("the judge still runs on a WRITABLE copy connection: the pending capture's row written or re-checked (checked_at moved) -- equal on OLD and NEW", judged, (r1, r2))
        DUMP["s5"]["verdict_rw"] = (r2 or {}).get("verdict"), (r2 or {}).get("reason")
        if OLD.get("s5"):
            check("the writable judge's verdict / reason equal the OLD files' (%s)" % (DUMP["s5"]["verdict_rw"],), list(DUMP["s5"]["verdict_rw"]) == list(OLD["s5"].get("verdict_rw") or []), (DUMP["s5"]["verdict_rw"], OLD["s5"].get("verdict_rw")))
    section("5  F-943: the witness on a read-only connection (stderr, the row, the file); the judge still works on a writable one", s5)

    # ============================================================================================ 6 nothing else moved: the figures
    def s6():
        c = conn()
        sw = SW.Spine()
        ctx = SF.Ctx(c, sw)
        names = sorted({it for it, _p, _s in OR._s470_master(c, PA)} | {it["item"] for it in PO.ortho_items(c)[0]})
        t0 = time.time()
        F = SF.figures(c, sw, names, at=TODAY, ctx=ctx)
        fig = {n: dict(marg=(F[n]["marg"] or {}).get("figure"), taps=(F[n]["marg"] or {}).get("taps"), shelf=F[n]["shelf"].get("shelf"), arrived=F[n]["shelf"].get("arrived"), named=F[n]["shelf"].get("named")) for n in names}
        cap = SF.capture_at(sw, None, ctx)
        say("   figures() for %d names in %.1fs; capture_at: printed %s taken %s -> end %s" % (len(names), time.time() - t0, cap["as_on"], cap["stamp_iso"], cap["end_day"]))
        DUMP["figures"] = fig
        DUMP["cap"] = dict(md5=cap["md5"], end_day=cap["end_day"])
        if OLD.get("figures"):
            o = OLD["figures"]
            moved = [n for n in names if n in o and o[n] != fig[n]]
            for n in moved[:8]:
                say("   %-32s OLD %s -> NEW %s" % (n[:32], o[n], fig[n]))
            check("every counted item's marg() / shelf() figure equals the OLD files' on the copy (%d names, %d moved) and capture_at is the same capture" % (len(names), len(moved)),
                  not moved and OLD.get("cap") == DUMP["cap"], (moved[:5], OLD.get("cap"), DUMP["cap"]))
        else:
            say("   (no --old-dump: the figures are kept for the NEW run to compare)")
        c.close()
        schema1 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
        check("the spine copy's schema is unchanged by the walk", schema0 == schema1, [s for s in schema1 if s not in schema0])
        check("the spine copy's bytes are unchanged by the walk (no write by any code under test; the synthetic spines are second copies)", hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest() == spine_md5_0)
        try:
            r = subprocess.run([sys.executable, "-B", os.path.join(fin, "spine", "selftest_spine.py")], cwd=os.path.join(fin, "spine"), capture_output=True, text=True, timeout=600)
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            check("selftest_spine.py is green on the copy's spine code (%s)" % tail[0][:60], r.returncode == 0 and "SELFTEST OK" in (r.stdout or ""), (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
        except Exception as e:                                 # noqa: BLE001
            check("selftest_spine.py ran", False, str(e)[:200])
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("6  nothing else moved: capture_at / marg() / shelf() for every counted item OLD vs NEW; the spine untouched; selftest; healthz", s6)

    # ============================================================================================ 7 greps
    def s7():
        sf, sr, dk, ht = SRC["stock_figure.py"], SRC["spine/spine_read.py"], SRC["darpan_kal.py"], SRC["darpan_kal.html"]
        head = sf[:sf.find("\nclass Ctx")] if "\nclass Ctx" in sf else ""
        ctx_body = sf[sf.find("\nclass Ctx"):sf.find("\ndef _ctx(")] if "\nclass Ctx" in sf else ""
        allowed = head + ctx_body + fn_body(sf, "_may_write") + fn_body(sf, "witness")
        ro_lines = [l for l in sf.splitlines() if "read_only" in l]
        stray = [l for l in ro_lines if l not in allowed]
        check("C: read_only in stock_figure.py exactly in Ctx.__init__, _may_write, witness and the two docstrings (%d lines, 0 elsewhere)" % len(ro_lines),
              NEW and len(ro_lines) >= 4 and not stray and "read_only" in ctx_body and "read_only" in fn_body(sf, "_may_write") and "read_only=True" in fn_body(sf, "witness"), stray[:3])
        check("C: _may_write(con, ctx) once; _may_write( twice in all (the def and its one caller)", sf.count("_may_write(con, ctx)") == 1 and sf.count("_may_write(") == 2 and "_may_write(con)" not in sf, (sf.count("_may_write(con, ctx)"), sf.count("_may_write(")))
        check("C: KIT = \"S602 in stock_figure.py", 'KIT = "S602' in sf)
        check("C: def purchases_upto once in spine_read.py (plus its usage line in the docstring: 2 mentions)", sr.count("def purchases_upto(") == 1 and sr.count("purchases_upto") == 2, (sr.count("def purchases_upto("), sr.count("purchases_upto")))
        check("C: purchases_upto once in darpan_kal.py (the one read, inside _s485_payload) and purchase_upto once (the one key)",
              dk.count("purchases_upto") == 1 and dk.count("purchase_upto") == 1 and "purchases_upto" in fn_body(dk, "_s485_payload") and "purchase_upto=pu" in fn_body(dk, "_s485_payload"), (dk.count("purchases_upto"), dk.count("purchase_upto")))
        check("C: purchase_upto in darpan_kal.html in the one fragment only (three reads of the key inside it)", ht.count("j.purchase_upto") == 3 and ht.count("purchase_upto") == 3 and ht.count(FRAG) == 1, (ht.count("j.purchase_upto"), ht.count("purchase_upto")))
        others = []
        for root, _d, files in os.walk(fin):
            for f in files:
                p = os.path.join(root, f)
                rel = os.path.relpath(p, fin).replace(os.sep, "/")
                if rel in FOUR or not (f.endswith(".py") or f.endswith(".html")) or "/finance_ui/" in ("/" + rel):
                    continue
                try:
                    t = open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                if "purchases_upto" in t or "purchase_upto" in t:
                    others.append(rel)
        check("purchases_upto / purchase_upto nowhere else in the finance folder (%d other files)" % len(others), not others, others[:5])
        pb = dk.count("purchase_bill")
        DUMP["s7"] = dict(purchase_bill=pb)
        check("the count of 'purchase_bill' in darpan_kal.py is %d%s (charter 1: no new read of the tables)" % (pb, (" = OLD's %s" % OLD["s7"]["purchase_bill"]) if OLD.get("s7") else ""),
              pb == 0 and (not OLD.get("s7") or OLD["s7"]["purchase_bill"] == pb), (pb, (OLD.get("s7") or {}).get("purchase_bill")))
        check("no run of ten digits in the four files or the walk's own output", not re.search(r"\d{10}", "".join(SRC.values()) + "\n".join(OUT)))
        check("no code of the four files writes to the spine (no INSERT / UPDATE / DELETE on an sp_ table)", not any(re.search(r"(INSERT|UPDATE|DELETE)\s+(INTO\s+|FROM\s+)?sp_", SRC[n]) for n in FOUR))
        check("the Ctx default is writable (a default Ctx carries read_only False) and _ctx() is unchanged", (not NEW) or (SF.Ctx().read_only is False and "read_only" not in fn_body(sf, "_ctx")))
    section("7  the greps (one fact, one place; the read-only flag read by _may_write alone)", s7)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S602: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S602: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S602: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S602: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
