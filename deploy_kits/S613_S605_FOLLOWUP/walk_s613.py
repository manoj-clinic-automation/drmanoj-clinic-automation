#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s613.py -- kit S613_S605_FOLLOWUP (22-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s613.py --fin <scratch /root/finance with the files under test; spine/ = a copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --por <scratch /root/portal copy
                            (every .py but portal_config.py, tile_grants.json -- the walk writes its OWN secret and user store into it)>
                            --duty-map <the clone's DUTY_MAP.json> --spine-old605 <a scratch spine built by S605's OLD builder>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s613.py --facts --label before|after --fin <a copy of the finance code> --db <finance.db, opened READ ONLY>
                            --spine <spine.db, opened read only>           (the installer's live facts: SELECTs and a read-only Ctx, no page)
The real finance app (and, for the staff-eye homes, the real portal) in one process: the walk's own header session, its own portal sign-in
(a random secret, its own user store -- never the live ones), its own reception-phone key on the copy. Its own rows by key (W613 ...): its
orders and messages, one synthetic sale under a new key on a SECOND spine copy (the side's spine is never written: bytes compared). The
hand-out's clock is the walk's (order_sheet.now / supplier_msg._now set in process). No phone number is printed (ten digits masked).
Sections follow the brief's section 4; the page dumps run FIRST on the quiet copy (--old-dump compares); --expect-red is the negative control
(the same walk on the OLD files: every 'C:' check must be red). Prints 'WALK OK S613 ...'."""
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
import sys

KIT = "S613_S605_FOLLOWUP"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
OPEN_LINES = ((54, "ANKLE BINDER BAMBOO M"), (20, "ANKLE BINDER BAMBOO L"), (20, "L S BELT CONT GRAY UNISON XXX"), (20, "KNEE IMMOBILISER UNISON M"),
              (1, "KNEE SUPPORT HINGED XL"), (1, "KNEE SUPPORT HINGED XXL UNISO"), (1, "KNEE IMMOBILIZER UNISON XL"), (1, "SHOULDER IMMOBILISE UNISON XL"),
              (1, "L S BELT CONT GRAY UNISON XXX"))
SYN_OLD, SYN_NEW = "KNEE SUPPORT HINGED M", "KNEE SUPPORT M HINGED"      # the size the walk lays one sale under (its new key), found by name
LEFT_OUT = {"KNEE IMMOBILI?ER UNI (family)": "its old key also carries KNEE IMMOBILISER UNISON M (not one of the 22): that item's own share is "
                                             "taken over the newest capture's members, not the split's, so the 22's shares cannot sum to 1"}
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
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-1500:]))


def text_lines(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    s = re.sub(r"</(div|p|li|tr|h\d|button|a|td|th|span)>|<br\s*/?>", "\n", s)
    out = []
    for l in s.split("\n"):
        t = _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", l))).strip()
        if t:
            out.append(t)
    return out


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def h8(o):
    return hashlib.md5(json.dumps(o, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:12]


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W613 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w613-walk-seed'\n" % secret)
    sys.path.insert(0, por)
    import clinic_users                                        # noqa: E402
    store = os.path.join(por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for u, role in ROLE.items():
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
        clinic_users.add_user(store, u, role, pw[u])
    sys.path.remove(por)
    sys.modules.pop("clinic_users", None)
    return secret, pw, store


def app_env(a, dbp, token, secret=None, store=None):
    por = os.path.abspath(a.por) if a.por else os.path.join(os.path.dirname(dbp), "nosso")
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="",
                      FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token, CLINIC_PORTAL_DIR=por, PYTHONDONTWRITEBYTECODE="1")
    if secret:
        os.environ.update(CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"))
    if a.duty_map:
        os.environ["DUTY_MAP_JSON"] = os.path.abspath(a.duty_map)
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY", "PORDERS_SOURCE"):
        os.environ.pop(k, None)


def renames(con):
    return [(str(r[0]), str(r[1])) for r in con.execute("SELECT old_name, new_name FROM marg_item_rename WHERE id BETWEEN 1 AND 22 AND done_at IS NOT NULL ORDER BY id")]


# ======================================================================================================= the installer's live facts
def facts(a):
    """Read only: finance.db by URI mode=ro, the spine through stock_watch.Spine (mode=ro), a read-only Ctx. Never a page (pages write)."""
    fin = os.path.abspath(a.fin)
    sys.path.insert(0, fin)
    os.chdir(fin)
    os.environ["SPINE_DB"] = os.path.abspath(a.spine)
    import stock_watch as SW                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    con = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(a.db), uri=True, timeout=60)
    sp = SW.Spine(os.path.abspath(a.spine))
    ctx = SF.Ctx(con, sp, read_only=True)
    now = dt.datetime.now().replace(microsecond=0)
    say("FACTS %s: clock %s IST; stock_figure %s (%s); spine built %s" % (a.label, now.isoformat(" "), SF.VERSION, SF.KIT,
                                                                      (sp.q("SELECT value AS v FROM sp_meta WHERE key='built'") or [{}])[0].get("v")))
    say("FACTS %s: the 22 sizes by new name (name | key | Marg | shelf | approx):" % a.label)
    tab = {}
    for _o, n in renames(con):
        M = SF.marg(con, sp, n, None, ctx)
        S = SF.shelf(con, sp, n, None, ctx)
        tab[n] = (S.get("key"), M and M["figure"], S.get("shelf"), S.get("approx"))
        say("   %-32s | %-22s | %6s | %5s | %s" % (n[:32], S.get("key"), "-" if not M else "%g" % M["figure"], S.get("shelf"), S.get("approx")))
    say("FACTS %s: TABLE %s" % (a.label, json.dumps(tab, sort_keys=True)))
    if hasattr(SF, "split_of"):
        rows = SF._split_rows(sp, ctx)
        say("FACTS %s: split_of reads %d row(s):" % (a.label, len(rows)))
        for k in sorted(rows):
            r = rows[k]
            say("   %-22s <- %-30s split %s (note's old clip '%s'; printed %s)" % (k, r["old_k"], r["day"], r["old_clip"], r["new_name"]))
    else:
        say("FACTS %s: split_of -- not in these files (OLD)" % a.label)
    caps = [c for c in SF.captures(sp, ctx) if c["as_on"] == "2026-10-10"]
    say("FACTS %s: the 10-10 split captures (printed 10-10): %s" % (a.label, ["%s taken %s -> stands for %s (%s)" % (c["md5"][:8], c["stamp_iso"], c["end_day"],
        "morning: before 09:00" if c["stamp_iso"][11:16] < "09:00" else ("a later day" if c["stamp_iso"][:10] > c["as_on"] else "in the day"))
        for c in caps]))
    names = [x for p in renames(con) for x in p]
    try:
        q = ",".join("?" * len(names))
        g = con.execute("SELECT item, end_day, COUNT(*) FROM s577_shelf_gap WHERE item IN (%s) GROUP BY item, end_day ORDER BY end_day, item" % q, names).fetchall()
        gm = con.execute("SELECT MAX(end_day) FROM s577_shelf_gap").fetchone()[0]
    except sqlite3.Error as e:
        g, gm = "unreadable: %s" % e, None
    say("FACTS %s: s577_shelf_gap rows for the 44 spellings: %s (the table's newest end_day %s)" % (a.label, g or "none", gm))
    today = now.date().isoformat()
    rows = con.execute("SELECT id, vendor, order_via, substr(created_at,12,5) FROM purchase_order WHERE order_src='s454' AND status='sent' AND order_via<>'paper' "
                       "AND substr(created_at,1,10)=? ORDER BY id", (today,)).fetchall()
    say("FACTS %s: today's call-row count by SELECT (s454, sent, not paper, made today): %d -- %s" % (a.label, len(rows), [tuple(r) for r in rows] or "none"))
    m = con.execute("SELECT id, vendor, status, substr(queued_at,12,8), substr(COALESCE(handed_at,'-'),12,8), substr(COALESCE(sent_at,'-'),12,8), "
                    "substr(COALESCE(last_error,''),1,40) FROM supplier_msg WHERE kind='order' AND substr(queued_at,1,10)=? ORDER BY id", (today,)).fetchall()
    say("FACTS %s: today's order messages (id, vendor, status, queued, handed, sent, last_error -- no number, no body): %s" % (a.label, [tuple(r) for r in m] or "none"))
    con.close()
    say("FACTS OK S613 (%s)" % a.label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--por", "--duty-map", "--dump", "--old-dump", "--spine-old605", "--spine", "--label"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--facts", action="store_true")
    a = ap.parse_args()
    if a.facts:
        return facts(a)
    for k in ("fin", "db", "adb", "marg", "por", "duty_map", "dump", "spine_old605"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k.replace("_", "-"))
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg), os.path.abspath(a.por), os.path.abspath(a.spine_old605)):
        assert p.startswith("/tmp/"), "the walk runs on scratch copies in /tmp only: %s" % p
    os.makedirs(a.dump, exist_ok=True)
    say("-- S613 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    PRISTINE = dbp + ".pristine"
    copy_db(dbp, PRISTINE)                                     # the quiet copy before any page read (pages write: F-925)
    token = secrets.token_hex(16)
    secret, pw, store = portal_setup(os.path.abspath(a.por))
    app_env(a, dbp, token, secret, store)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import porders_s454 as P4                                 # noqa: E402
    import supplier_msg as SM                                 # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import stock_app as SA                                    # noqa: E402
    for m in (fa, OS, PO, P4, SM, SF, SW, SA):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(SF, "split_of")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure %s %s" % (
        [n for n, _w in fa._MOUNT_FAILED] or "none", SF.VERSION, "NEW (S613)" if NEW else "OLD"))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    spine_md5_0 = md5f(SPINE_PATH)
    PHONE = "w613" + secrets.token_hex(12)
    real_now, real_sm_now = OS.now, SM._now
    NOW0 = OS.now()
    TODAY = NOW0.date().isoformat()

    def GET(u, path, follow=False, headers=None):
        hd = {"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}
        hd.update(headers or {})
        r = cl.get(path, base_url=BASE, headers=hd, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body, headers=None):
        hd = {"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}
        hd.update(headers or {})
        r = cl.post(path, base_url=BASE, headers=hd, json=body)
        try:
            j = json.loads(r.get_data().decode("utf-8", "replace"))
        except ValueError:
            j = {}
        return r.status_code, j

    def conn(path=None):
        c = sqlite3.connect(path or dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def clock(t):
        OS.now = (lambda: t) if t else real_now
        SM._now = (lambda: t) if t else real_sm_now

    def sn_of(v):
        return OS._pa().supplier_key(v)

    with conn() as c_:
        OS.ensure(c_)
        SM.ensure(c_)
        REN = renames(c_)
        c_.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_token'", (PHONE,))
        c_.commit()
    N44 = {x for p in REN for x in p}
    say("   today %s, now %s; %d renamed sizes read from marg_item_rename (ids 1-22); the copy's reception-phone key replaced by the walk's own" % (TODAY, NOW0, len(REN)))
    check("the copy holds the 22 ticked renames of the brief (ids 1-22)", len(REN) == 22, len(REN))

    # ============================================================================================ 6 (first): the pages dumped on the quiet copy
    def s_pages():
        pages = [("darpan", "/finance/darpan/kal/api/day"), ("darpan", "/finance/darpan/kal/api/order"), ("reception", "/finance/porders"),
                 ("reception", "/finance/porders/s454/order"), ("reception", "/finance/porders/s454/maal"), ("reception", "/finance/porders/s454/scan"),
                 ("reception", "/finance/porders/s454/q"), ("amir", "/finance/amir"), ("manoj", "/finance/sanjeevni/api/needs-you"),
                 ("shavez", "/finance/purchase/page/pay"), ("bhati", "/finance/salecheck/api/days")]
        with conn() as c_:
            oo = OS.open_order(c_)
            sup = (oo["lines"][0]["supplier_norm"] if oo["lines"] else None)
        if sup:
            from urllib.parse import quote
            pages.append(("reception", "/finance/porders/s454/order/" + quote(sup, safe="")))
        changed, allowed = {}, []
        for u, path in pages:
            s, h = GET(u, path, follow=True, headers=({"Cookie": "clinic_who=alisha"} if u == "reception" else None))
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))[:120]
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "now", "server_time", "user", "as_of", "today", "purchase_upto"):
                            j.pop(k, None)
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\b\d+ (hours?|minutes?|ghante|minute)\b", r"N \1", re.sub(r"\d{1,2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l))
                     for l in body.splitlines() if l.strip()]      # the clock's own words masked (a wait of N hours moves between two runs)
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                    ok_ = all(_allowed(l) for l in gone + new)
                    (allowed if ok_ else [None]).append(path)
                    changed[(u, path)] = (gone, new, ok_)
                    say("   CHANGED on %s for %s: %d line(s) gone, %d new (%s)" % (path, u, len(gone), len(new), "only this kit's own changes" if ok_ else "NOT ALLOWED"))
                    for l in gone[:12]:
                        say("      - %s" % l[:260])
                    for l in new[:12]:
                        say("      + %s" % l[:260])
                else:
                    say("   unchanged on %s for %s" % (path, u))
        if a.old_dump:
            bad = {k: (v[0][:3], v[1][:3]) for k, v in changed.items() if not v[2]}
            check("every page dump (Darpan's day, his order tab, reception's home / order list / supplier / maal / scan / photo pages, Amir's page, the "
                  "approvals Needs-you, the pay page, Bhati's sale check) is byte-equal to the OLD files' dumps but for the 22 sizes' figures, the call "
                  "row's count and the orthotic family-bill words (%d page(s) differ only so)" % len(allowed), not bad, bad)

    def _allowed(l):
        u = l.upper()
        if any(n.upper() in u for n in N44):                   # a line naming one of the 22 sizes (old or new spelling): its figure / bill words
            return True
        if re.match(r"^\d+$", l.strip()) or l.strip() in ("Aaj ke order — call karo", "Today's orders — call"):   # the home's call row (its count)
            return True
        return False
    section("6 (first) the pages dumped on the quiet copy -- byte-equal OLD vs NEW but the 22 sizes' figures and the call row", s_pages)

    # ---- the walk's own spine copy (one synthetic sale under a new key); the side's spine is never written
    SYN = os.path.join(os.path.dirname(dbp), "spine_syn_%s" % ("old" if a.expect_red else "new"))
    if os.path.isdir(SYN):
        shutil.rmtree(SYN)
    os.makedirs(SYN)
    copy_db(SPINE_PATH, os.path.join(SYN, "spine.db"))

    def ctx_on(path, con):
        sp = SW.Spine(path)
        return sp, SF.Ctx(con, sp, read_only=True)

    # ============================================================================================ 1 F-951 on scratch spines (read only)
    def s1():
        c = conn(PRISTINE)
        sp, ctx = ctx_on(SPINE_PATH, c)
        # ---- split_of: the 22, and nothing else
        rows = {}
        try:
            for o, n in REN:
                s = SF.split_of(sp, n, ctx)
                rows[n] = s and (s["new_k"], s["old_k"], s["day"])
                say("   split_of %-32s -> %s" % (n[:32], rows[n]))
            nks = {v[0] for v in rows.values() if v}
            others = [str(r["name"]) for r in sp.q("SELECT DISTINCT name, k20 FROM sp_item") if str(r["name"]) not in N44 and str(r["k20"]) not in nks]
            hits = [x for x in others if SF.split_of(sp, x, ctx) is not None]
            oldsame = [o for o, n in REN if SF.split_of(sp, o, ctx) != SF.split_of(sp, n, ctx)]
        except AttributeError as e:
            rows, hits, others, oldsame = {}, ["no split_of: %s" % e], [], ["-"]
        days = {v[2] for v in rows.values() if v}
        check("C: (1) split_of reads all 22 sizes (new key, old key, day 2026-10-10 from the spine's own note) and the old name gives the same row",
              len([v for v in rows.values() if v]) == 22 and days == {"2026-10-10"} and not oldsame, (len(rows), days, oldsame[:3]))
        check("(1) every other printed name of sp_item -> no split (%d names)" % len(others), NEW and not hits, hits[:5])
        DUMP["split_rows"] = rows
        # ---- key_of unchanged (R1-B1): every name of the newest usable capture, the 6-Sep count, count 1's vouchers
        cap = SF.capture_at(sp, None, ctx)
        nm = {r[0] for rows_ in SF._cn_rows(sp, cap["md5"], ctx)[0].values() for r in rows_}
        nm |= {str(r[0]) for r in c.execute("SELECT DISTINCT item FROM stock_count_item WHERE count_id=1")}
        try:
            nm |= {str(r[0]) for r in c.execute("SELECT DISTINCT item FROM stock_voucher_line WHERE count_id=1")}
        except sqlite3.Error:
            pass
        kmap = {n: SF.key_of(sp, n, ctx) for n in sorted(nm)}
        DUMP["key_of"] = kmap
        say("   key_of over %d names (the newest usable capture %s, the 6-Sep count, count 1's vouchers): hash %s" % (len(kmap), cap["md5"][:8], h8(kmap)))
        if OLD.get("key_of"):
            dif = [n for n in kmap if OLD["key_of"].get(n) != kmap[n]]
            check("(1) key_of is byte-equal OLD vs NEW over %d names (stock_app's count-voucher proof keys stay)" % len(kmap), not dif and len(OLD["key_of"]) == len(kmap), dif[:5])
        # ---- Amir's count-voucher proof (stage A's orthotic batches) -- on a copy (amir_stage writes its events)
        p2 = dbp + ".amir"
        copy_db(PRISTINE, p2)
        c2 = conn(p2)
        st = SA.amir_stage(c2)
        pr = ((st or {}).get("A") or {}).get("proof") or {}
        amir = dict(stage=(st or {}).get("stage"), proof=pr.get("state"), pending=((st or {}).get("A") or {}).get("pending"), rows=len(pr.get("rows") or []))
        c2.close()
        os.remove(p2)
        DUMP["amir"] = amir
        say("   Amir's stage (amir_stage on a copy): %s" % amir)
        if OLD.get("amir"):
            check("(1) Amir's count-voucher proof (stage, stage A's proof state over the orthotic batches) is equal OLD vs NEW", OLD["amir"] == amir, (OLD["amir"], amir))
        # ---- the 22 sizes' figures, by old and by new name, on the side's spine
        tab = {}
        for o, n in REN:
            So, Sn = SF.shelf(c, sp, o, None, ctx), SF.shelf(c, sp, n, None, ctx)
            Mo, Mn = SF.marg(c, sp, o, None, ctx), SF.marg(c, sp, n, None, ctx)
            tab[n] = dict(old=o, key=Sn.get("key"), marg=(Mn or {}).get("figure"), shelf=Sn.get("shelf"), approx=Sn.get("approx"), sold=Sn.get("sold"),
                          bought=Sn.get("bought"), shelf_old=So.get("shelf"), sold_old=So.get("sold"), bought_old=So.get("bought"), marg_old=(Mo or {}).get("figure"),
                          pre=_pre(Sn), pre_old=_pre(So))
        DUMP["tab"] = tab
        say("   the 22 sizes (name | key | Marg | shelf | approx | by old name: shelf, sold, bought):")
        for n, t in tab.items():
            say("   %-32s | %-22s | %5s | %4s | %-5s | %4s %6s %6s" % (n[:32], t["key"], t["marg"], t["shelf"], t["approx"], t["shelf_old"], t["sold_old"], t["bought_old"]))
        same = [n for n, t in tab.items() if (t["shelf"], t["sold"], t["bought"]) != (t["shelf_old"], t["sold_old"], t["bought_old"])]
        check("C: (1) shelf() by old and by new name give the same figure for each of the 22", not same, same[:6])
        # by old name, the new key's moves since the split day (per size with a move after it)
        exp, own = {}, {}                                    # the walk's own reading of the split (never split_of): the alias note, sp_item
        for o, n in REN:
            k20n = re.sub(r"\s+", " ", n.strip())[:20].strip()
            al = sp.q("SELECT source FROM sp_alias WHERE kind='rename_family' AND alias=?", k20n)
            ok_ = sp.q("SELECT k20 FROM sp_item WHERE name=? LIMIT 1", o)
            m_ = re.search(r"\(split (\d{4}-\d{2}-\d{2}) from ", str((al or [{}])[0].get("source") or ""))
            if not (al and ok_ and m_):
                continue
            own[n] = s = (k20n, str(ok_[0]["k20"]), m_.group(1))
            a_ = sp.q("SELECT COALESCE(SUM(CASE WHEN kind='SALE' THEN -units ELSE 0 END),0) AS s, COALESCE(SUM(CASE WHEN kind IN ('PURCHASE','PURCHASE_RETURN') THEN units ELSE 0 END),0) AS b, "
                      "COUNT(*) AS n FROM sp_move WHERE k20=? AND date>? AND kind IN ('SALE','SALE_RETURN','PURCHASE','PURCHASE_RETURN')", s[0], s[2])[0]
            if a_["n"]:
                exp[o] = (float(a_["s"]), float(a_["b"]))
        say("   sizes with a move under their new key after 10-10 (sold, bought): %s" % exp)
        for o, (es, eb) in sorted(exp.items()):
            t = next(v for v in tab.values() if v["old"] == o)
            so_ = SF.shelf(c, sp, o, None, ctx)
            sh_, bd, sday = float(so_.get("share") or 0), str(so_.get("base_day") or ""), own[next(n for oo, n in REN if oo == o)][2]
            okk = own[next(n for oo, n in REN if oo == o)][1]
            p_ = sp.q("SELECT COALESCE(SUM(CASE WHEN kind='SALE' AND date>=? THEN -units ELSE 0 END),0) AS s, COALESCE(SUM(CASE WHEN kind IN ('PURCHASE','PURCHASE_RETURN') "
                      "AND date>? THEN units ELSE 0 END),0) AS b FROM sp_move WHERE k20=? AND date<=?", bd, bd, okk, sday)[0]
            xs, xb = round(sh_ * float(p_["s"]) + es, 2), round(sh_ * float(p_["b"]) + eb, 2)
            check("C: (1) by old name %s: shelf's sold %s / bought %s = its share %g of the old key's %g / %g to 10-10 + the new key's %g / %g since"
                  % (o, t["sold_old"], t["bought_old"], sh_, float(p_["s"]), float(p_["b"]), es, eb),
                  abs(float(t["sold_old"]) - xs) <= 0.02 and abs(float(t["bought_old"]) - xb) <= 0.02, (t["sold_old"], xs, t["bought_old"], xb))
        # ---- the walk's synthetic sale under a new key (its own spine copy), after the newest capture
        s = sqlite3.connect(os.path.join(SYN, "spine.db"))
        nk = s.execute("SELECT k20 FROM sp_item WHERE name=?", (SYN_NEW,)).fetchone()
        s.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,?,?,?)", (nk[0], TODAY, "SALE", -1.0, "W613 walk sale"))
        s.commit()
        s.close()
        sp2, ctx2 = ctx_on(os.path.join(SYN, "spine.db"), c)
        S0, S1 = SF.shelf(c, sp, SYN_OLD, None, ctx), SF.shelf(c, sp2, SYN_OLD, None, ctx2)
        say("   the walk's sale of 1 under %s dated %s (its own spine copy): by old name sold %s -> %s" % (nk[0], TODAY, S0["sold"], S1["sold"]))
        check("C: (1) by old name (%s) shelf() counts the walk's sale under the new key (sold +1)" % SYN_OLD, abs(float(S1["sold"]) - float(S0["sold"]) - 1.0) < 0.01, (S0["sold"], S1["sold"]))
        mm = {}
        for o, n in REN:
            Mo, Mn = SF.marg(c, sp2, o, None, ctx2), SF.marg(c, sp2, n, None, ctx2)
            mm[n] = ((Mo or {}).get("figure"), (Mn or {}).get("figure"))
        dif = {n: v for n, v in mm.items() if v[0] != v[1]}
        say("   marg() by old / new name with the walk's sale: %s differ%s" % (len(dif), (" -- %s" % dif) if dif else ""))
        check("C: (1) marg() by old and by new name equal for each of the 22, the walk's sale after the newest capture included", not dif and mm.get(SYN_NEW, (0, 0))[1] is not None, dif)
        # ---- conservation per family against S605's OLD builder (one fixed member set: the members at the split)
        if NEW:
            spo, ctxo = ctx_on(os.path.abspath(a.spine_old605), c)
            fams = {}
            for o, n in REN:
                fams.setdefault(rows[n][1], []).append(n)
            for ok_, sizes in sorted(fams.items()):
                if ok_ in LEFT_OUT:
                    say("   conservation: %s left out -- %s" % (ok_, LEFT_OUT[ok_]))
                    continue
                sx = SF.split_of(sp, sizes[0], ctx)
                mem = SF.split_members(sp, sx, ctx)
                bases = [SF.base(c, m[0], ctx) for m in mem]
                bday = min(b["day"] for b in bases if b)
                okey = SF.key_of(spo, mem[0][0], ctxo)
                so, ro, bo = SF.moves(spo, okey, bday, TODAY, incl_from=True)
                tot_old = sum(b["qty"] for b in bases if b) - so + ro + bo
                tot_new = sum(tab[x]["pre"] for x in sizes)
                say("   conservation %-30s members %d (%s) | S605's OLD builder (key %s): base %g - sold %g + returned %g + bought %g = %.2f | NEW: the sizes' shelf before the clamp, summed = %.2f"
                    % (ok_, len(mem), ", ".join(m[0] for m in mem), okey, sum(b["qty"] for b in bases if b), so, ro, bo, tot_old, tot_new))
                check("(1) conservation %s: the sizes' figures sum to the family's by S605's OLD builder within 0.5 x %d" % (ok_, len(mem)),
                      abs(tot_old - tot_new) <= 0.5 * len(mem) and len(mem) == len(sizes), (tot_old, tot_new, len(mem), len(sizes)))
        # ---- carried() for every open old-name line; detect_supplies on a copy of the quiet copy
        car = {}
        for oid, item in OPEN_LINES:
            r = c.execute("SELECT l.id, l.item, o.vendor, o.created_at, l.arrived_at, l.billed_bill_no FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                          "WHERE l.order_id=? AND l.item=?", (oid, item)).fetchone()
            if not r:
                car["%d %s" % (oid, item)] = "missing"
                continue
            cx = SF.Ctx(c, sp, read_only=True)
            line = dict(line_id=r[0], item=r[1], vendor=r[2], order_at=r[3], arrived_at=r[4], billed_bill_no=r[5] or "")
            h = SF.carried(c, sp, line, cx)
            fb = cx.c.get(("fam_bill", r[0]))
            car["%d %s" % (oid, item)] = dict(line=r[0], carried=(h and dict(bill=h["bill"], date=h["date"], units=h["units"], how=h["how"])),
                                                fam=(fb and dict(bill=fb["bill"], date=fb["date"], sizes=fb["sizes"])))
        DUMP["carried"] = car
        for k, v in car.items():
            say("   carried %-36s %s%s" % (k, v if isinstance(v, str) else v["carried"], "" if isinstance(v, str) else ("   family bill %s" % v["fam"])))
            if OLD.get("carried", {}).get(k) is not None and OLD["carried"][k] != v:
                say("      (OLD: %s   family bill %s)" % (OLD["carried"][k].get("carried"), OLD["carried"][k].get("fam")) if isinstance(OLD["carried"][k], dict) else "      (OLD: %s)" % OLD["carried"][k])
        o1 = [car.get("1 %s" % x) for x in ("KNEE SUPPORT HINGED XL", "KNEE SUPPORT HINGED XXL UNISO", "KNEE IMMOBILIZER UNISON XL", "SHOULDER IMMOBILISE UNISON XL")]
        check("(1) order 1's XL / XXL / KNEE IMMOBILIZER XL / SHOULDER XL lines are NOT carried by bill 672 (a sibling size's lines)",
              all(isinstance(v, dict) and (v["carried"] is None or str(v["carried"]["bill"]) != "672") for v in o1), o1)
        l9 = car.get("1 L S BELT CONT GRAY UNISON XXX")
        check("(1) order 1's L S BELT ... XXX (billed 672): branch (a) answers bill 672%s" % (" with OLD's units" if OLD.get("carried") else ""),
              isinstance(l9, dict) and l9["carried"] and l9["carried"]["how"] == "a" and str(l9["carried"]["bill"]) == "672"
              and (not OLD.get("carried") or (OLD["carried"].get("1 L S BELT CONT GRAY UNISON XXX") or {}).get("carried") == l9["carried"]), l9)
        l50 = car.get("20 L S BELT CONT GRAY UNISON XXX")
        check("(1) order 20's L S BELT ... XXX: carried() None (no XXX / XXXL line since 05-10)", isinstance(l50, dict) and l50["carried"] is None, l50)
        check("C: (1) order 20's L S BELT ... XXX: its family-bill words name bill 738 of 18-10 (the sibling sizes' new keys)",
              isinstance(l50, dict) and l50["fam"] and str(l50["fam"]["bill"]) == "738" and l50["fam"]["date"] == "2026-10-18", l50)
        p3 = dbp + ".ds"
        copy_db(PRISTINE, p3)
        c3 = conn(p3)
        snap = lambda: {r[0]: tuple(r[1:]) for r in c3.execute("SELECT id, billed_qty, billed_bill_no, supplied, arrived_at FROM purchase_order_line")}   # noqa: E731
        so_ = lambda: {r[0]: r[1] for r in c3.execute("SELECT id, status FROM purchase_order")}   # noqa: E731
        b0, o0 = snap(), so_()
        PO.detect_supplies(c3)
        c3.commit()
        b1, o1_ = snap(), so_()
        w = sorted(["line %d: %s -> %s" % (k, b0.get(k), v) for k, v in b1.items() if b0.get(k) != v] + ["order %d: %s -> %s" % (k, o0.get(k), v) for k, v in o1_.items() if o0.get(k) != v])
        c3.close()
        os.remove(p3)
        DUMP["detect"] = w
        say("   porders.detect_supplies on a copy of the quiet copy would write: %s" % (w or "nothing"))
        if OLD.get("detect") is not None:
            say("   ... and on the OLD files: %s" % (OLD["detect"] or "nothing"))
        check("(1) detect_supplies writes nothing new on the NEW files beyond the OLD files' (any NEW write is a stop)",
              (not w) or (OLD.get("detect") is not None and sorted(w) == sorted(OLD["detect"])), w[:6])
        # ---- every other name: shelf, marg, carried byte-equal OLD vs NEW
        others = sorted(n for n in kmap if n not in N44 and not (NEW and SF.split_of(sp, n, ctx)))
        cx = SF.Ctx(c, sp, read_only=True)
        sig = {}
        for n in others:
            S = SF.shelf(c, sp, n, None, cx)
            M = SF.marg(c, sp, n, None, cx)
            sig[n] = h8([S, M])
        lines = []
        for r in c.execute("SELECT l.id, l.item, o.vendor, o.created_at, l.arrived_at, l.billed_bill_no FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id "
                           "WHERE (l.arrived_at IS NOT NULL OR COALESCE(l.billed_bill_no,'')<>'') AND l.item NOT IN (%s)" % ",".join("?" * len(N44)), sorted(N44)):
            if NEW and SF.split_of(sp, r[1], cx):
                continue
            h = SF.carried(c, sp, dict(line_id=r[0], item=r[1], vendor=r[2], order_at=r[3], arrived_at=r[4], billed_bill_no=r[5] or ""), cx)
            lines.append((r[0], h8(h)))
            sig["line %d %s" % (r[0], r[1])] = "%s %s" % (h8(h), h and (h["bill"], h["date"], h["units"], h["how"]))
        DUMP["others"] = sig
        say("   every other name: %d names (shelf + marg) and %d order lines (carried) compared, KNEE IMMOBILISER UNISON M among them: %s"
            % (len(others), len(lines), "KNEE IMMOBILISER UNISON M" in sig))
        if OLD.get("others"):
            dif = ["%s: OLD %s NEW %s" % (n, OLD["others"].get(n), sig[n]) for n in sig if OLD["others"].get(n) != sig[n]]
            extra = sorted(set(OLD["others"]) - set(sig))     # the OLD side has no split_of: Marg's other spellings of the 22 are in its list
            say("   on the OLD side %d more key(s) were compared -- Marg's own spellings of the 22 sizes (split_of says so on NEW): %s" % (len(extra), extra[:8]))
            check("(1) every name not one of the 22: shelf, marg and carried byte-equal OLD vs NEW (%d names, %d lines)" % (len(others), len(lines)),
                  not dif and set(sig) <= set(OLD["others"]), dif[:6])
        # ---- the witness through witness(con, sp, out_dir) on the side's spine (never the CLI)
        wd = os.path.join(a.dump, "witness")
        os.makedirs(wd, exist_ok=True)
        wp = SF.witness(c, sp, out_dir=wd)
        wl = open(wp, encoding="utf-8").read().splitlines()[1:]
        DUMP["witness"] = wl
        if OLD.get("witness") is not None:
            dif = [l for l in wl if l not in set(OLD["witness"])] + [l for l in OLD["witness"] if l not in set(wl)]
            say("   the witness (its first line, the clock, apart): %d line(s), %d differ OLD vs NEW" % (len(wl), len(dif)))
            for l in dif[:8]:
                say("      %s" % l[:200])
            check("(1) the witness reads the same OLD vs NEW (a 'nothing moved' check: it iterates the new names)", not dif, dif[:4])
        c.close()

    def _pre(S):
        if S.get("base") is None:
            return None
        return float(S["base"]) - float(S["sold"] or 0) + float(S["returned"] or 0) + float(S["bought"] or 0) + float(S["boundary"] or 0)
    section("1  F-951: split_of; key_of unchanged; the 22 by old and new name; the walk's sale; conservation; carried; detect_supplies; the rest equal", s1)

    # ============================================================================================ 2 F-959 the second door
    def s2():
        c = conn()
        sh = PO.shelf(c)
        item = (sh["items"][0]["item"] if sh.get("items") else "W613 NO ITEM")
        for u in ("manoj", "darpan"):
            mx = lambda: tuple(c.execute("SELECT COALESCE(MAX(id),0) FROM %s" % t).fetchone()[0] for t in ("purchase_order", "purchase_order_line", "purchase_audit"))   # noqa: E731
            m0 = mx()
            s, j = POST(u, "/finance/porders/api/send", dict(lines=[dict(item=item, qty=1)]))
            m1 = mx()
            say("   POST /finance/porders/api/send as %s (%s x1): %s %s %s; rows before %s after %s" % (u, item, s, j.get("error"), (j.get("message") or "")[:90], m0, m1))
            want = ("Yuvika's order now goes from reception's order page, after Darpan's yes." if u == "manoj"
                    else "Yuvika ka order ab 'Order karna hai' se jaata hai, Darpan ki haan ke baad.")
            check("C: (2) api/send as %s -> 409 ortho_via_order_page ('%s'), nothing written" % (u, want), s == 409 and j.get("error") == "ortho_via_order_page"
                  and j.get("message") == want and m0 == m1, (s, j, m0, m1))
            c.rollback()
        s, h = GET("manoj", "/finance/porders?old=1")
        say("   the old page (?old=1) as the owner: %s, %d bytes" % (s, len(h)))
        check("C: (2) the old page has no send(), no 'Yuvika ko order bhejo', no -/+ (dq) and no size chips (ps)", s == 200 and "send()" not in h
              and "Yuvika ko order bhejo" not in h and "dq(" not in h and "ps(" not in h and "QTY" not in h and "PICK" not in h, s)
        check("(2) its orthotic table is still drawn (read only) and sendMed / sendDay stay", s == 200 and 'L("s1",s.ortho.n)' in h and "async function sendMed(" in h
              and "async function sendDay(" in h, s)
        s, j = GET("manoj", "/finance/porders/api/state")
        check("(2) the old page's state still carries the orthotic shortage list", s == 200 and "ortho" in (json.loads(j) if s == 200 else {}), s)
        c.close()
    section("2  F-959: the old Purchase orders page orders nothing from Yuvika", s2)

    # ============================================================================================ 3 F-962 the call row's count
    def s3():
        c = conn()
        real_counts = P4.counts
        P4.counts = lambda con, month=None: (dict(real_counts(con, month), order=0) if month is None else real_counts(con, month))   # the walk's: nothing left to order
        try:
            base_n = c.execute("SELECT COUNT(*) FROM purchase_order WHERE order_src='s454' AND status='sent' AND order_via<>'paper' AND substr(created_at,1,10)=?", (TODAY,)).fetchone()[0]
            yday = (NOW0 - dt.timedelta(days=1)).replace(microsecond=0).isoformat()
            mk = lambda v, st, via, at=None: OS.make_order(c, "w613walk", v, [dict(item="W613 ITEM", packs=1, pack_size=1, rate_p=0)], st, via, created_at=at)   # noqa: E731
            ids = dict(A=mk("W613 CALL A", "sent", "whatsapp"), B=mk("W613 CALL B", "sent", "call"), C=mk("W613 CALL C", "sent", "whatsapp"),
                       D=mk("W613 CALL D", "sent", "whatsapp", yday))
            c.execute("UPDATE purchase_order SET status='received', received_at=? WHERE id=?", (OS.now_iso(), ids["C"]))
            c.commit()
            exp_new = base_n + 2
            done = P4._done_today(c)
            exp_old = len(done)
            s, h = GET("reception", "/finance/porders", headers={"Cookie": "clinic_who=alisha"})
            m = re.search(r'id="row_call"[^>]*><span class="n">(\d+)</span>', h)
            got = int(m.group(1)) if m else None
            lst = ["%s %s %s" % (d["vendor"], d["via"], str(d["sent_at"])[:16]) for d in done]
            say("   the copy's own s454 orders sent today %d; the walk lays 2 sent today (WhatsApp, call), 1 received today, 1 sent yesterday" % base_n)
            say("   the home's call row: %s (NEW expects %d; the OLD rule would say %d); the Ho chuke list beside it: %s" % (got, exp_new, exp_old, lst))
            check("C: (3) the call row counts today's orders still awaited -- %d (the walk's 2 + the copy's %d), never the received or yesterday's" % (exp_new, base_n), got == exp_new, (got, exp_new, exp_old))
            p0 = dbp + ".q0"                                  # the comparison on a fresh copy of the quiet copy (section 2's OLD door made an order)
            copy_db(PRISTINE, p0)
            c0 = conn(p0)
            DUMP["done_today"] = [dict(d, phone=h8(d.get("phone")), wa=h8(d.get("wa"))) for d in P4._done_today(c0)]
            DUMP["counts"] = real_counts(c0)
            c0.close()
            os.remove(p0)
            say("   on the quiet copy: counts() %s; the Ho chuke list %d line(s)" % (DUMP["counts"], len(DUMP["done_today"])))
            if OLD.get("done_today") is not None:
                dd = [x for x in DUMP["done_today"] if x not in OLD["done_today"]] + [x for x in OLD["done_today"] if x not in DUMP["done_today"]]
                check("(3) the Ho chuke list (_done_today, its numbers through book_card) is equal OLD vs NEW (%d lines)" % len(DUMP["done_today"]), not dd, dd[:3])
                check("(3) counts() is equal OLD vs NEW", OLD["counts"] == DUMP["counts"], (OLD["counts"], DUMP["counts"]))
            c.execute("UPDATE purchase_order SET status='received', received_at=? WHERE order_src='s454' AND status='sent' AND substr(created_at,1,10)=?", (OS.now_iso(), TODAY))
            c.commit()
            P4.counts = lambda con, month=None: (dict(order=0, maal=0, scan=0, q=0) if month is None else real_counts(con, month))
            s, h = GET("reception", "/finance/porders", headers={"Cookie": "clinic_who=alisha"})
            say("   every order of today received, nothing else standing: rows %s; alldone %s" % (re.findall(r'id="(row_[a-z]+)"', h), 'id="alldone"' in h))
            check("C: (3) all of today's orders received -> no call row, and 'Sab kaam ho gaya' when nothing else stands", 'id="row_call"' not in h and 'id="alldone"' in h,
                  re.findall(r'id="(row_[a-z]+)"', h))
        finally:
            P4.counts = real_counts
        c.execute("UPDATE purchase_order SET status='cancelled' WHERE created_by='w613walk' AND vendor LIKE 'W613 CALL %'")
        c.commit()
        c.close()
    section("3  F-962: the call row counts today's orders still awaited", s3)

    # ============================================================================================ 4 F-960 three loose ends
    def mk_order(c, name, status="draft", at=None):
        oid = OS.make_order(c, "w613walk", name, [dict(item="W613 ITEM " + name[-1], packs=1, pack_size=1, rate_p=0)], status, "whatsapp", created_at=at)
        c.commit()
        return oid

    def mk_msg(c, name, kind, ref, queued_at, month=None):
        c.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) VALUES (?,?,?,?,?,?,?,?,?)",
                  (month or NOW0.strftime("%Y-%m"), sn_of(name), name, kind, ref, "w613-not-a-number", "W613 walk message", "queued", queued_at))
        c.commit()
        return c.execute("SELECT id FROM supplier_msg WHERE kind=? AND ref=? AND vendor=?", (kind, ref, name)).fetchone()[0]

    def hand(c, mid, t):
        c.execute("UPDATE supplier_msg SET handed_at=? WHERE id=?", (t.isoformat(), mid))     # the phone takes it (api_next's one write)
        c.commit()

    def nxt(t):
        clock(t)
        s, h = GET("manoj", "/finance/api/supplier-msg/next", headers={"X-Phone-Token": PHONE})
        try:
            return (json.loads(h) or {}).get("id")
        except ValueError:
            return "HTTP %s" % s

    def done(t, mid, ok):
        clock(t)
        r = cl.post("/finance/api/supplier-msg/done", base_url=BASE, headers={"X-Phone-Token": PHONE}, json=dict(id=mid, ok=ok, error="" if ok else "w613: not sent"))
        return r.status_code

    def msg(c, mid):
        return dict(c.execute("SELECT id, status, handed_at, sent_at, last_error FROM supplier_msg WHERE id=?", (mid,)).fetchone())

    def order(c, oid):
        return dict(c.execute("SELECT status, order_via, sent_by FROM purchase_order WHERE id=?", (oid,)).fetchone())

    def card(c, sn):
        return next((e for e in OS.entries(c) if e["sn"] == sn), None)

    def park(c, *mids):
        c.execute("UPDATE supplier_msg SET status='skipped', last_error='w613: the walk is done with it' WHERE id IN (%s) AND status IN ('queued','failed')" % ",".join("?" * len(mids)), mids)
        c.commit()

    def aud(c, oid, action):
        return c.execute("SELECT COUNT(*) FROM purchase_audit WHERE ref=? AND action=?", (str(oid), action)).fetchone()[0]

    class Racy(object):
        """A connection whose withdrawal UPDATE of one message is preceded by the phone taking it (api_next between the SELECT and the UPDATE)."""
        def __init__(self, real, mid, t):
            self._r, self._mid, self._t = real, mid, t

        def execute(self, sql, params=()):
            if sql.startswith("UPDATE supplier_msg SET status='skipped'") and params and params[-1] == self._mid:
                self._r.execute("UPDATE supplier_msg SET handed_at=? WHERE id=?", (self._t.isoformat(), self._mid))
            return self._r.execute(sql, params)

        def __getattr__(self, k):
            return getattr(self._r, k)

    def s4():
        c = conn()
        T0 = NOW0.replace(second=0, microsecond=0)
        t = lambda m: T0 + dt.timedelta(minutes=m)              # noqa: E731
        # ---- the wait from the hand-out
        D = "W613 SUPPLIER D"
        clock(t(0))
        od = mk_order(c, D)
        md = mk_msg(c, D, "order", od, t(0).isoformat())
        hand(c, md, t(50))
        clock(t(60))
        OS.withdraw_late(c)
        c.commit()
        r60 = msg(c, md)
        say("   %s: queued T, handed T+50, no done -> at T+60 the message %s (%s)" % (D, r60["status"], (r60["last_error"] or "")[:60]))
        check("C: (4) queued T, handed T+50, no done -> at T+60 still queued: not withdrawn, not unconfirmed (the wait runs from the hand-out)", r60["status"] == "queued", r60)
        clock(t(111))
        OS.withdraw_late(c)
        c.commit()
        r111, o111 = msg(c, md), order(c, od)
        say("   ... at T+50+61: message %s (%s), order %s" % (r111["status"], (r111["last_error"] or "")[:50], o111))
        check("(4) ... at T+50+61 unconfirmed: the order sent by WhatsApp, the message 'unconfirmed: ...'", r111["status"] == "skipped" and (r111["last_error"] or "").startswith("unconfirmed:")
              and o111["status"] == "sent", (r111, o111))
        # ---- never handed: withdrawn at T+60; a hand-out between the SELECT and the UPDATE is not withdrawn
        E, F = "W613 SUPPLIER E", "W613 SUPPLIER F"
        clock(t(0))
        oe, of = mk_order(c, E), mk_order(c, F)
        me, mf = mk_msg(c, E, "order", oe, t(0).isoformat()), mk_msg(c, F, "order", of, t(0).isoformat())
        clock(t(61))
        OS.withdraw_late(Racy(c, mf, t(60)))
        c.commit()
        re_, rf = msg(c, me), msg(c, mf)
        say("   %s never handed -> T+61 %s (%s); %s handed between withdraw_late's read and its write -> %s (%s)" % (E, re_["status"], (re_["last_error"] or "")[:40], F, rf["status"], (rf["last_error"] or "")[:40]))
        check("(4) a never-handed message is withdrawn at T+60 ('not sent within')", re_["status"] == "skipped" and "not sent within" in (re_["last_error"] or ""), re_)
        check("C: (4) a message the phone takes between withdraw_late's read and its write is not withdrawn (the guarded UPDATE)", rf["status"] == "queued" and rf["handed_at"], rf)
        park(c, mf)
        # ---- a late 'could not send' on an unconfirmed order: nothing arrived
        G = "W613 SUPPLIER G"
        clock(t(0))
        og = mk_order(c, G)
        sheet = c.execute("SELECT COALESCE(MAX(id),0) FROM order_sheet").fetchone()[0]
        c.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, resolved, supplier, supplier_norm, line_date, kind, state, order_id, first_sheet, last_sheet, created_at) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", ("W613-G", "W613 ITEM G", "W613 ITEM G", 1, G, sn_of(G), TODAY, "new", "in_line", og, -1, -1, OS.now_iso()))
        c.commit()
        mg = mk_msg(c, G, "order", og, t(0).isoformat())
        hand(c, mg, t(1))
        clock(t(62))
        OS.withdraw_late(c)
        c.commit()
        un = (order(c, og), msg(c, mg)["status"])
        dg = done(t(70), mg, False)
        og_, rg = order(c, og), msg(c, mg)
        sl = c.execute("SELECT state FROM order_sheet_line WHERE entry_no='W613-G'").fetchone()[0]
        eg = card(c, sn_of(G))
        s, h = GET("reception", "/finance/porders/s454/order?all=1", headers={"Cookie": "clinic_who=alisha"})
        tl = text_lines(h)
        cardtxt = any(G in l for l in tl) and any("WhatsApp nahi gaya — call kijiye" in l for l in tl)
        say("   %s: unconfirmed at T+62 %s; the phone's no at T+70 (%s) -> order %s, message %s, its sheet line %s, card %s, audit _no %d; on reception's order page: %s"
            % (G, un, dg, og_, rg["status"], sl, (eg or {}).get("state"), aud(c, og, "s454_whatsapp_unconfirmed_no"), cardtxt))
        check("C: (4) a late ok:false on an unconfirmed order, nothing arrived -> a draft again (sent_by NULL), its line in_line, reception's card 'WhatsApp nahi gaya — call kijiye', audit row",
              og_["status"] == "draft" and og_["sent_by"] is None and sl == "in_line" and (eg or {}).get("state") == "withdrawn" and cardtxt and rg["status"] == "skipped"
              and aud(c, og, "s454_whatsapp_unconfirmed_no") == 1, (og_, sl, (eg or {}).get("state"), cardtxt))
        # ... and may go again once (the phone's own no)
        q_, _nn, call = OS.wa_plan(c)
        r_ = OS.order_supplier(c, "w613walk", sn_of(G), "whatsapp")
        c.commit()
        say("   after the no: wa_plan queue %s / call %s; order_supplier -> %s; message %s" % (sn_of(G) in [e["sn"] for e in q_], sn_of(G) in [e["sn"] for e in call], r_, msg(c, mg)["status"]))
        check("C: (4) after the phone's no on the unconfirmed order it may be queued again (not under wa_plan's 'call'; order_supplier 200, queued)",
              sn_of(G) not in [e["sn"] for e in call] and r_[1] == 200 and msg(c, mg)["status"] == "queued", (r_, msg(c, mg)))
        park(c, mg)
        # ---- the same with a line arrived
        H = "W613 SUPPLIER H"
        clock(t(0))
        oh = mk_order(c, H)
        mh = mk_msg(c, H, "order", oh, t(0).isoformat())
        hand(c, mh, t(1))
        clock(t(62))
        OS.withdraw_late(c)
        c.commit()
        c.execute("UPDATE purchase_order_line SET supplied=1, arrived_at=?, arrived_by='w613walk' WHERE order_id=?", (t(65).isoformat(), oh))
        c.commit()
        dh = done(t(70), mh, False)
        oh_, rh = order(c, oh), msg(c, mh)
        clock(None)
        s, j = GET("manoj", "/finance/sanjeevni/api/needs-you")
        nl = [l.get("text") for l in (json.loads(j).get("lines") or [])] if s == 200 else []
        want = "%s — the reception phone said it could not send the order of %s, but goods have already come in on it. Nothing was changed." % (H, t(0).strftime("%H:%M"))
        say("   %s: unconfirmed, a line arrived, then the phone's no (%s) -> order %s, message %s, audit _no_arrived %d; the owner's line: %s"
            % (H, dh, oh_, rh["status"], aud(c, oh, "s454_whatsapp_unconfirmed_no_arrived"), [x for x in nl if str(x).startswith(H)] or "none"))
        check("C: (4) ... with a line arrived -> the order unchanged, the message skipped, the owner's line '%s'" % want,
              oh_["status"] == "sent" and rh["status"] == "skipped" and want in nl and aud(c, oh, "s454_whatsapp_unconfirmed_no_arrived") == 1, (oh_, rh, nl[:6]))
        # ---- handed + ok:false -> queued again; two cycles: no -> re-queued -> handed -> silence -> unconfirmed, never again
        J = "W613 SUPPLIER J"
        clock(t(0))
        oj = mk_order(c, J)
        mj = mk_msg(c, J, "order", oj, t(0).isoformat())
        hand(c, mj, t(1))
        dj = done(t(2), mj, False)
        q_, _nn, call = OS.wa_plan(c)
        inq, inc = sn_of(J) in [e["sn"] for e in q_], sn_of(J) in [e["sn"] for e in call]
        clock(t(3))
        r_ = OS.order_supplier(c, "w613walk", sn_of(J), "whatsapp")
        c.commit()
        rj = msg(c, mj)
        say("   %s: handed, the phone's no (%s) -> wa_plan queue %s / call %s; order_supplier %s; message %s" % (J, dj, inq, inc, r_, rj["status"]))
        check("C: (4) handed + the phone's ok:false -> wa_plan lists it to send again (not under 'call') and order_supplier re-queues it (once per no)",
              not inc and r_[1] == 200 and rj["status"] == "queued", (inq, inc, r_, rj))
        hand(c, mj, t(4))
        clock(t(4 + 61))
        OS.withdraw_late(c)
        c.commit()
        rj2, oj2 = msg(c, mj), order(c, oj)
        q_, _nn, call = OS.wa_plan(c)
        r2 = OS.order_supplier(c, "w613walk", sn_of(J), "whatsapp")
        c.commit()
        rj3 = msg(c, mj)
        say("   ... re-queued, handed again at T+4, the phone silent -> T+65: message %s (%s), order %s; a tap -> %s; message %s" % (rj2["status"], (rj2["last_error"] or "")[:40], oj2, r2, rj3["status"]))
        check("(4) two cycles: no -> re-queued -> handed -> silence -> unconfirmed at T+61, and never queued again (not in wa_plan's queue, a tap queues nothing)",
              rj2["status"] == "skipped" and (rj2["last_error"] or "").startswith("unconfirmed:") and sn_of(J) not in [e["sn"] for e in q_ + _nn] and rj3["status"] != "queued", (rj2, oj2, r2, rj3))
        if NEW:
            check("(4) the one rule says no for it now (its newest cycle row is _unconfirmed)", not OS._s613_phone_said_no(c, oj), oj)
        # ---- a late ok:true on an unconfirmed message -> sent, the order unchanged
        K = "W613 SUPPLIER K"
        clock(t(0))
        ok_ = mk_order(c, K)
        mk_ = mk_msg(c, K, "order", ok_, t(0).isoformat())
        hand(c, mk_, t(1))
        clock(t(62))
        OS.withdraw_late(c)
        c.commit()
        dk = done(t(70), mk_, True)
        rk, okk = msg(c, mk_), order(c, ok_)
        check("(4) a late ok:true on an unconfirmed message -> sent, the order unchanged (sent by WhatsApp)", dk == 200 and rk["status"] == "sent" and okk["status"] == "sent", (rk, okk))
        # ---- payment and test messages, as before
        mp = mk_msg(c, "W613 PAYEE", "neft", 613, "2000-01-01T00:00:03", month="2000-01")
        h1, h2 = nxt(t(70)), nxt(t(81))
        check("(4) a payment message handed, no done: not handed again at T+11 (unchanged)", h1 == mp and h2 != mp, (h1, h2))
        dp = done(t(82), mp, False)
        h3 = nxt(t(82 + SM.RETRY_MIN + 1))
        check("(4) a payment message the phone could not send is retried after RETRY_MIN (unchanged)", dp == 200 and h3 == mp, (dp, h3))
        park(c, mp)
        mt = mk_msg(c, "Test message", "test", 613613, "2000-01-01T00:00:04", month="test")
        h4, h5 = nxt(t(120)), nxt(t(131))
        check("(4) the owner's test message is handed again after the gap (unchanged)", h4 == mt and h5 == mt, (h4, h5))
        park(c, mt)
        clock(None)
        c.execute("UPDATE purchase_order SET status='cancelled' WHERE created_by='w613walk' AND vendor LIKE 'W613 SUPPLIER %'")
        c.commit()
        c.close()
    section("4  F-960: the wait from the hand-out; the guarded withdrawal; the late no (draft again / goods in); once per no; two cycles; ok:true; payments", s4)

    # ============================================================================================ 5 the staff-eye walk (reception, Amir) and DUTY_MAP
    def portal_tiles(user):
        tiles = []
        try:
            sys.path.insert(0, os.path.abspath(a.por))
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            r = pc.post("/portal/login", base_url=BASE, data={"user": user, "password": pw[user]})
            m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
            r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")})
            tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True))]
            say("   the portal as %s (the walk's own secret and user store): login %s, home %s, tiles %s" % (user, r.status_code, r3.status_code, tiles))
        except Exception as e:                                 # noqa: BLE001
            say("   the portal as %s could not be rendered: %s" % (user, str(e)[:200]))
        finally:
            if os.path.abspath(a.por) in sys.path:
                sys.path.remove(os.path.abspath(a.por))
        return tiles

    def s5():
        dm = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
        c = conn(PRISTINE)
        for who in ("reception", "amir"):
            tiles = portal_tiles(who)
            for d in [x for x in dm["duties"] if str(x.get("person")).lower() == who]:
                try:
                    r = c.execute(d["due_sql"]).fetchone()
                    n = int(r[0] or 0)
                except Exception as e:                         # noqa: BLE001
                    n = "unreadable: %s" % str(e)[:60]
                if not isinstance(n, int) or n <= 0:
                    say("   %s: %s not due on the copy (n %s)" % (who, d["id"], n))
                    continue
                s, h = GET(who, d["door"], headers=({"Cookie": "clinic_who=alisha"} if who == "reception" else None), follow=True)
                ok_ = d["tile"] in tiles and s == 200 and str(d.get("door_marker") or "") in _html.unescape(h)
                check("staff-eye: %s's duty %s is due (n %d): the tile '%s' on the home and '%s' on %s" % (who, d["id"], n, d["tile"], d.get("door_marker"), d["door"]), ok_,
                      (d["tile"] in tiles, s))
        s, h = GET("reception", "/finance/porders", headers={"Cookie": "clinic_who=alisha"})
        check("staff-eye: reception's home signs the shared login with its name cookie ('reception · Alisha')", s == 200 and "reception · Alisha" in _html.unescape(h), s)
        say("   DUTY_MAP: no change -- this kit adds, moves or removes no staff duty (the call row and the WhatsApp card are reception's existing duty "
            "'Order karna hai' / its call row; the owner's new line is his Needs-you). The clone's DUTY_MAP.json is read as it is: v%s" % dm.get("version"))
        c.close()
    section("5  the staff-eye walk: reception (the shared login, its name cookie) and Amir; DUTY_MAP unchanged", s5)

    # ============================================================================================ 9 the greps, the spine untouched, healthz
    def s9():
        src = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in ("stock_figure.py", "order_sheet.py", "porders_s454.py", "porders.py")}
        check("C: one place for the split (split_of) and one helper for its moves (split_moves) in stock_figure", "def split_of(" in src["stock_figure.py"] and src["stock_figure.py"].count("def split_moves(") == 1)
        check("C: one rule 'may it be sent again' (_s613_phone_said_no) read by order_supplier and wa_plan", src["order_sheet.py"].count("_s613_phone_said_no(con,") == 3)
        check("C: _done_today reads the numbers through book_card", "OS.book_card(con, o[\"vendor\"])" in src["porders_s454.py"])
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
        check("the side's spine copy is unchanged by the walk (its sale went to a second copy)", md5f(SPINE_PATH) == spine_md5_0)
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("9  the greps, the spine copy untouched, healthz", s9)

    clock(None)
    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    for p in (PRISTINE,):
        try:
            os.remove(p)
        except OSError:
            pass
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in reds:
            say("  red: %s" % l[:200])
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S613: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S613: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S613: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S613: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
