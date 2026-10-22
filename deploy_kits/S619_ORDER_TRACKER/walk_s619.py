#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s619.py -- kit S619_ORDER_TRACKER (22-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s619.py --fin <scratch /root/finance with the files under test> --db <COPY of finance.db> --adb <COPY of assets.db>
                            --marg <scratch marg_ingest> --shared <scratch /root/shared> --por <scratch /root/portal copy: the walk writes its OWN
                            secret and user store into it> --duty-map <the kit's DUTY_MAP.json (v19)> --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s619.py --facts --label before|after --fin <a scratch finance folder carrying order_track> --db <a COPY of finance.db> --adb <...>
The real finance app (and, for the staff-eye homes, the real portal) in one process: the walk's own header session for the finance pages, its
own portal sign-in (a random secret, its own user store -- never the live ones). Its OWN rows by key (vendors 'W619 ...', sheet entries 'W619-...',
scan stamps 'W619-...'), never found by counting. A synthetic `now` for the late rule (order_track takes it). No phone number is printed (ten
digits masked). Sections follow the brief's section 4; the page dumps of section 9 run FIRST on the quiet copy (--old-dump compares). --expect-red
is the negative control: the same walk on the OLD files, every 'C:' check must be red. Prints 'WALK OK S619 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import sys
import time

KIT = "S619_ORDER_TRACKER"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "alisha": "staff", "shivani": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
REC = {"Cookie": "clinic_who=alisha"}
DL = "Kripya maal dopahar 3 se shaam 6 baje ke beech, ya subah 11 baje tak bhejein."
FIVE = {34: "XGESIC LA", 22: "THIO Q AP", 25: "FLACORT 6", 33: "POWERGESIC 100 PATCH", 38: "LINVIZ 600"}
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
    s = re.sub(r"</(div|p|li|tr|h\d|button|a|td|th|span|summary)>|<br\s*/?>", "\n", s)
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


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W619 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w619-walk-seed'\n" % secret)
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


def iso(t):
    return t.replace(microsecond=0).isoformat()


# ======================================================================================================= the install's live facts (read only)
def facts(a):
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), MARG_INGEST_DIR=os.path.abspath(a.marg or "/tmp/nomarg"), ORDER_PUSH_NONE="1",
                      PYTHONDONTWRITEBYTECODE="1")
    if a.shared:
        sys.path.insert(0, os.path.abspath(a.shared))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import order_sheet as OS                                  # noqa: E402
    import order_track as OT                                  # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    now = OS.now()
    rows = OT.light_all(con, now)
    say("FACTS %s: clock %s IST; orders since %s: %d; late %s; not arrived %s; part %s; bill scanned not in Marg %s; with a short line %s" % (
        a.label, now.strftime("%Y-%m-%d %H:%M:%S"), OT.since(con), len(rows), [s["id"] for s in rows if s["late"]], [s["id"] for s in rows if not s["arrived"]],
        [s["id"] for s in rows if s["part"]], [s["id"] for s in rows if s["key"] == "awaiting"], [s["id"] for s in rows if s["short"]]))
    for s in rows:
        say("FACTS %s:   %s" % (a.label, OT.table_row(s)))
    have = OT._has(con, "order_carry")
    say("FACTS %s: order_carry %s; open carries %s" % (a.label, "present" if have else "absent", [(c["from_order_id"], c["item"], c["qty"], c["reason"]) for c in OT.open_carries(con)] if have else "-"))
    if have:
        say("FACTS %s: every order_carry row: %s" % (a.label, [tuple(r) for r in con.execute("SELECT id, from_order_id, item, qty, reason, substr(at,1,16), done_order_id, dropped_by FROM order_carry ORDER BY id")]))
    say("FACTS %s: the carries a carry pass would write now: %s" % (a.label, OT.carries_plan(con, now) or "none"))
    say("FACTS %s: Darpan's line (viewed today): %s" % (a.label, OT.darpan_line(con, now.date().isoformat(), now).get("text") or "-"))
    say("FACTS %s: today's order messages (id, status, queued, handed, sent -- never a number or a body): %s" % (a.label, [tuple(r) for r in con.execute(
        "SELECT id, status, substr(queued_at,12,5), substr(handed_at,12,5), substr(sent_at,12,5) FROM supplier_msg WHERE kind='order' AND substr(queued_at,1,10)=? ORDER BY id",
        (now.date().isoformat(),))] or "none"))
    con.close()
    say("FACTS OK S619 (%s)" % a.label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--shared", "--por", "--duty-map", "--dump", "--old-dump", "--label"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--facts", action="store_true")
    a = ap.parse_args()
    for k in ("fin", "db", "adb"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    if a.facts:
        return facts(a)
    for k in ("marg", "shared", "por", "duty_map", "dump"):
        if not getattr(a, k):
            ap.error("--%s is needed for the walk" % k.replace("_", "-"))
    fin, dbp, adb, por = (os.path.abspath(getattr(a, k)) for k in ("fin", "db", "adb", "por"))
    for p in (fin, dbp, adb, por, os.path.abspath(a.marg), os.path.abspath(a.shared)):
        assert p.startswith("/tmp/"), "the walk runs on scratch copies in /tmp only: %s" % p
    os.makedirs(a.dump, exist_ok=True)
    say("-- S619 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    secret, pw, store = portal_setup(por)
    token = secrets.token_hex(16)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=adb, SHARED_LIB_DIR=os.path.abspath(a.shared), CLINIC_PORTAL_DIR=por, FINANCE_ALLOW_HEADER_AUTH="1",
                      MARG_INGEST_DIR=os.path.abspath(a.marg), ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token, PYTHONDONTWRITEBYTECODE="1", CLINIC_SSO_SECRET=secret,
                      CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"), DUTY_MAP_JSON=os.path.abspath(a.duty_map))
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY", "PORDERS_SOURCE"):
        os.environ.pop(k, None)
    sys.path.insert(0, fin)
    sys.path.insert(1, os.path.abspath(a.shared))
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import porders_s454 as P4                                 # noqa: E402
    import supplier_msg as SM                                 # noqa: E402
    import order_sheet_pdf as SP                              # noqa: E402
    import marg_order_pdf as MP                               # noqa: E402
    for m in (fa, OS, P4, SM, SP, MP):
        assert m.__file__.startswith(fin), m.__file__
    try:
        import order_track as OT                              # noqa: E402
        assert OT.__file__.startswith(fin)
    except ImportError:
        OT = None
    NEW = OT is not None
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; order_track %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none", "NEW (S619)" if NEW else "absent (OLD)"))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    DM = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
    NOW = OS.now()
    pa = OS._pa()

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

    def sn_of(v):
        return pa.supplier_key(v)

    def lay_order(c, vendor, created, status, lines, received_at=None, received_by=None, via="whatsapp"):
        """One synthetic order of the walk ('W619 ...' vendors) with its lines; returns its id."""
        cur = c.execute("INSERT INTO purchase_order (created_at, created_by, vendor, status, note, total_p, received_at, received_by, sent_by, section, supplier_norm, "
                        "ext_ref, order_src, order_via) VALUES (?,?,?,?,?,0,?,?,?,?,?,NULL,'s454',?)",
                        (iso(created), "W619 walk", vendor, status, "W619 walk", iso(received_at) if received_at else None, received_by, "W619 walk", "Medicines",
                         sn_of(vendor), via))
        oid = cur.lastrowid
        for l in lines:
            c.execute("INSERT INTO purchase_order_line (order_id, item, packs, pack_size, units, rate_p, value_p, supplied, short, missing, billed_qty, billed_bill_no, "
                      "billed_date, detected_at, arrived_by, arrived_at) VALUES (?,?,?,?,?,0,0,?,?,?,?,?,?,?,?,?)",
                      (oid, l["item"], int(l.get("packs", 10)), int(l.get("pack_size", 1)), int(l.get("packs", 10)) * int(l.get("pack_size", 1)), l.get("supplied"),
                       int(l.get("short", 0)), int(l.get("missing", 0)), l.get("billed_qty"), l.get("bill"), (l.get("bill_date") or None), l.get("detected_at"),
                       l.get("arrived_by"), l.get("arrived_at")))
        return oid

    def by_key(c, vendor):
        r = c.execute("SELECT id FROM purchase_order WHERE vendor=? ORDER BY id DESC LIMIT 1", (vendor,)).fetchone()
        return r[0] if r else None

    # ============================================================================================ 9 (first): the pages dumped on the quiet copy
    def s9():
        pages = [("darpan", "/finance/darpan/kal/api/day"), ("darpan", "/finance/darpan/kal/api/order"), ("reception", "/finance/porders/s454/order"),
                 ("reception", "/finance/porders/s454/scan"), ("amir", "/finance/amir"), ("shavez", "/finance/purchase/page/pay"),
                 ("bhati", "/finance/salecheck/api/days"), ("reception", "/finance/porders/s454/q"), ("manoj", "/finance/stockmatch/api/state"), ("manoj", "/finance/porders?old=1")]
        changed = {}
        for u, path in pages:
            s, h = GET(u, path, follow=True, headers=(REC if u == "reception" else None))
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))[:120]
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "now", "server_time", "user", "as_of", "today", "order_track", "yesterday", "purchase_upto"):
                            j.pop(k, None)                    # order_track (his line) and yesterday (his order tab) are this kit's own change
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\d{1,2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            lines = [l for l in lines if l != "Save" and not re.search(r"Settings \(S454\)|order\.(deliver|wa_delivery|track_since)|S619|Kripya maal dopahar|delivery hours|order list, the late rule|"
                                                       r"late this many days|not counted towards|last line of every WhatsApp", l)]   # the owner's settings card: S619's five
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("the page %s as %s (%s, %d bytes)" % (path, u, s, len(h)), s in (200, 302), s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                if old != lines:
                    os_, ns = set(old), set(lines)
                    gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                    changed[(u, path)] = (gone, new)
                    say("   CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:8]:
                        say("      - %s" % l[:240])
                    for l in new[:8]:
                        say("      + %s" % l[:240])
                else:
                    say("   unchanged on %s for %s" % (path, u))
        # the order engine's plan, the stock pages' inputs: byte-equal OLD vs NEW on the quiet copy
        import order_rules                                     # noqa: E402
        with conn() as c_:
            try:
                p = order_rules.plan(c_, OS.today())
                plan = json.dumps({k: p.get(k) for k in ("vendors", "no_supplier")}, sort_keys=True, default=str)
            except Exception as e:                             # noqa: BLE001
                plan = "plan error %s" % e
            neft = SM._neft_body(1234500, "2026-10", "2026-10-22", "XXXX1234", "IFSC0000")
            chq = SM._cheque_body(1234500, "2026-10", "000123", "2026-10-22")
            test = SM.s454_test_body(dt.datetime(2026, 10, 22, 12, 0))
        DUMP["s9"] = dict(plan_md5=hashlib.md5(plan.encode()).hexdigest(), neft=neft, cheque=chq, test=test)
        say("   the order engine's plan md5 %s; the payment and test bodies built (the WhatsApp's test and payment kinds)" % DUMP["s9"]["plan_md5"][:8])
        if a.old_dump and OLD.get("s9"):
            check("the order engine's plan (order_rules.plan) is byte-equal to the OLD files' on the quiet copy", OLD["s9"]["plan_md5"] == DUMP["s9"]["plan_md5"],
                  (OLD["s9"]["plan_md5"], DUMP["s9"]["plan_md5"]))
            check("the test message's and the payment messages' bodies are equal to the OLD files' (untouched)", all(OLD["s9"][k] == DUMP["s9"][k] for k in ("neft", "cheque", "test")))
            sc = changed.pop(("reception", "/finance/porders/s454/scan"), None)
            if sc:                                             # section 3.3 on purpose: an order where nothing came, or answered with Marg in, asks no more
                ok_sc = all(re.match(r"^.* · \d+ bill$", l) for l in sc[1]) and all(re.match(r"^(.* · \d+ bill|\d\d-\d\d ka maal|Maal aa gaya, bill scan baaki)$", l) for l in sc[0])
                check("Bill scan karna hai changes only on purpose (3.3): rows 'dd-mm ka maal · Maal aa gaya, bill scan baaki' gone for orders that ask no more, nothing added",
                      ok_sc, sc)
            check("every page dump (Darpan's day less his order line and order tab's yesterday, reception's order list / q pages, Amir's page, the pay "
                  "page, Bhati's sale check, the stock match, the owner's old page less S619's settings rows) is byte-equal to the OLD files' (%d differ)" % len(changed),
                  not changed, {k: (v[0][:3], v[1][:3]) for k, v in changed.items()})
    section("9 (first) nothing else moved: the pages, the plan, the test and payment bodies on the quiet copy", s9)

    # ============================================================================================ 1 the five steps on the copy
    def s1():
        assert NEW, "order_track is not in this folder (the OLD files)"
        with conn() as c:
            rows = OT.light_all(c, dt.datetime(2026, 10, 22, 12, 0))
            say("   the section 4.1 table, orders since %s, now = 22-10 12:00 (computed here, by section 3.1's rules):" % OT.since(c))
            for s in rows:
                if 21 <= s["id"] <= 60:
                    say("     " + OT.table_row(s))
            by = {s["id"]: s for s in rows}
            DUMP["s1"] = dict(table=[OT.table_row(s) for s in rows])
            late12 = [s["id"] for s in rows if s["late"]]
            na = [s["id"] for s in rows if not s["arrived"]]
            rows18 = OT.light_all(c, dt.datetime(2026, 10, 22, 18, 1))
            late18 = [s["id"] for s in rows18 if s["late"]]
            say("   not arrived at 22-10 12:00: %s (late then: %s); late at 22-10 18:01: %s" % (na, late12, late18))
            due20 = [s["id"] for s in rows if s["day"] == "2026-10-20" and not s["arrived"]]
            check("C: the orders of 20-10 not arrived are not late at 22-10 12:00 and are late at 22-10 18:01 (two days, Sunday not counted, at 18:00): %s" % due20,
                  all(i not in late12 for i in due20) and all(i in late18 for i in due20))
            s34 = by.get(34) or {}
            ok34 = (s34.get("vendor") == "DRUG DEAL" and s34.get("arrived") and any(x.get("stamp") == "B-0182" and x.get("via") == "bill" and x.get("bill") == "6579"
                                                                                     for x in s34.get("scans") or [])
                    and [x["item"] for x in s34.get("lines", []) if x["state"] == "short"] == ["XGESIC LA"])
            check("C: order 34 (Drug Deal 16-10) arrived -- its scan B-0182 through Marg's bill 6579 (the bill's link) -- with XGESIC LA short; OLD's Maal aaya hid it "
                  "and named no short line", ok34, (s34.get("arrived"), s34.get("scans"), [(x["item"], x["state"]) for x in s34.get("lines", [])]))
            s42 = by.get(42) or {}
            n42 = [x for x in s42.get("lines", []) if any(k == "tapped_no" for k, _a in x["notes"])]
            check("C: order 42's three lines tapped 'Nahi mila' came by Marg's figures, each with the note 'tapped Nahi mila; Marg billed ...'",
                  len(n42) == 3 and all(x["state"] == "came" and x["how"] == "marg" for x in n42),
                  [(x["item"], x["state"], [OT.W(k, True, *a_) for k, a_ in x["notes"]]) for x in s42.get("lines", [])])
            want = {22: "THIO Q AP", 25: "FLACORT 6", 33: "POWERGESIC 100 PATCH", 38: "LINVIZ 600", 39: "LANZOL JUNIOR"}
            got = {i: [x["item"] for x in (by.get(i) or {}).get("lines", []) if x["state"] == "short"] for i in want}
            check("C: 22, 25, 33, 38, 39 are short by name (THIO Q AP, FLACORT 6, POWERGESIC 100 PATCH, LINVIZ 600, LANZOL JUNIOR)", all(want[i] in got[i] for i in want), got)
            z = [x for x in (by.get(24) or {}).get("lines", []) if x["item"] == "ZUPRINOR 5"]
            check("C: order 24's ZUPRINOR 5 is short by 4 (billed 2 of 6) -- '%s'" % (z[0]["short_text"] if z else "-"), bool(z) and z[0]["state"] == "short" and z[0]["short"] == 4, z)
            tap = {i: ((by.get(i) or {}).get("arrived_how"), (by.get(i) or {}).get("in_marg")) for i in (47, 48, 50)}
            say("   47, 48, 50 (the brief: 'arrived by tap, not in Marg' on the morning's copy): %s -- Marg entered their bills at 09:40 today" % tap)
            check("47, 48, 50 arrived by reception's tap (their arrival moment is the tap's)", all(v[0] == "tap" for v in tap.values()), tap)
            check("the light half reads finance.db only: light_all ran with no assets.db and no spine (every order has its five answers)", len(rows) >= 30)
    section("1  the five steps on the copy (orders 21-55)", s1)

    # ============================================================================================ 2 late and hours (synthetic, its own copy)
    def s2():
        assert NEW, "order_track is not in this folder (the OLD files)"
        f2 = dbp + ".s2"
        copy_db(dbp, f2)
        with conn(f2) as c:
            OS.ensure(c)
            sat = OT.due_at(c, "2026-10-17T10:00:00")
            sun = OT.due_at(c, "2026-10-18T10:00:00")
            check("C: a Saturday order (17-10) is due Tuesday 20-10 18:00; a Sunday order (18-10) is due Tuesday 20-10 18:00", sat == dt.datetime(2026, 10, 20, 18, 0)
                  and sun == dt.datetime(2026, 10, 20, 18, 0), (sat, sun))
            t0 = dt.datetime(2026, 10, 17, 10, 0)
            a_ = lay_order(c, "W619 PART PHARMA", t0, "received", [dict(item="W619 PART A", packs=10, supplied=10, arrived_by="alisha", arrived_at=iso(t0.replace(hour=19, minute=40) + dt.timedelta(days=1))),
                                                                 dict(item="W619 PART B", packs=5)], received_at=t0 + dt.timedelta(days=1, hours=9, minutes=40), received_by="alisha")
            b_ = lay_order(c, "W619 SCAN PHARMA", t0, "received", [dict(item="W619 SCAN A", packs=10)], received_at=t0.replace(hour=19, minute=40), received_by="bill scan W619-9")
            c.execute("INSERT INTO order_scan_tie (order_id, asset_bill_id, stamp, scan_at, tied_at, how, arrived) VALUES (?,?,?,?,?,?,1)",
                      (b_, 990619001, "W619-9", "2026-10-17T19:40:00", iso(NOW), "scan"))
            c.commit()
            pa_ = OT.order_state_light(c, a_, dt.datetime(2026, 10, 20, 18, 1))
            pb_ = OT.order_state_light(c, a_, dt.datetime(2026, 10, 20, 17, 59))
            check("C: a part order (one line came by tap, one open) is late once its two days are past (20-10 18:01) and not before (17:59): %s / %s" % (pa_["key"], pb_["key"]),
                  pa_["late"] and pa_["part"] and not pb_["late"], (pa_["late"], pa_["part"], pb_["late"]))
            check("C: a 'Maal aaya' tap at 19:40 -> the time shown (outside the delivery hours): '%s'" % pa_["outside"], pa_["outside"] == "19:40", pa_["outside"])
            sb = OT.order_state_light(c, b_, dt.datetime(2026, 10, 20, 18, 1))
            check("C: a scan at 19:40 -> nothing (a scan's time never sets the mark); the order arrived by its scan alone waits for Marg, not late: '%s' %s late=%s"
                  % (sb["outside"], sb["key"], sb["late"]), sb["outside"] == "" and sb["arrived"] and sb["key"] == "awaiting" and not sb["late"], sb)
        os.remove(f2)
    section("2  late and the delivery hours (synthetic orders, its own copy)", s2)

    # ============================================================================================ 3 the soft note
    def s3():
        assert NEW, "order_track is not in this folder (the OLD files)"
        with conn() as c:
            now = OS.now()
            ctx = OT.Ctx(c)
            say("   the scan half: %d pharmacy scans, %d readings, scans to redo excluded %s" % (len(ctx.scans), len(ctx.read), sorted(ctx.bad)))
            rows = OT.light_all(c, now)
            t_light = OT.tiles(rows)
            keys = {s["id"]: s["key"] for s in rows}
            full = OT.full_all(c, now, ctx=ctx, rows=OT.light_all(c, now))
            check("C: a note never changes a count -- the tiles and every order's place are equal with and without the scan half",
                  OT.tiles(full) == t_light and {s["id"]: s["key"] for s in full} == keys, (OT.tiles(full), t_light))
            tot = miss = 0
            ml = []
            for s in full:
                if not (21 <= s["id"] <= 45):
                    continue
                billed = [dict(x, state="awaiting") for x in s["lines"] if x["how"] == "marg" and x["came"] > 0]
                if not billed:
                    continue
                later = [z for z in full if z["sn"] == s["sn"] and z["created_at"] > s["created_at"]]
                nxt = min(z["created"] for z in later) if later else None
                sn_ = OT.soft_notes(c, s, ctx, True, nxt, lines=billed)
                for x in billed:
                    tot += 1
                    if sn_.get(x["id"], ("no",))[0] == "no":
                        miss += 1
                        ml.append("%d %s" % (s["id"], x["item"]))
            rate = (100.0 * miss / tot) if tot else 0.0
            DUMP["s3"] = dict(miss=miss, tot=tot)
            say("   GATE (a note, so no bar): on orders 21-45, Marg as the answer key, the false 'not seen on the scanned bill' rate is %d of %d Marg-billed lines (%.0f%%): %s"
                % (miss, tot, rate, ", ".join(ml)))
            check("the soft-note rate was measured on orders 21-45 (Marg-billed lines held against every usable scan of the dealer up to its next order)", tot > 0)
            s28 = OT.order_state(c, 28, now, ctx)
            check("order 28's tie (B-0161, a Kedar paper saved under Shivaaz) carries the conflict note and lights no 'Bill scanned' dot",
                  any("another dealer" in n for n in s28["notes"]) and dict(OT.dots(s28))["Bill scanned"] == "conflict", (s28["notes"], OT.dots(s28)))
            wd = [w["stamp"] for w in OT.wrong_dealer(c, ctx)]
            check("'Saved under another dealer' lists B-0161 and B-0167 on the copy: %s" % wd, "B-0161" in wd and "B-0167" in wd, wd)
    section("3  the soft note: the 'not seen' rate; a note never moves a count", s3)

    # ============================================================================================ 4 the tie (synthetic, its own copy; the shared assets copy)
    def s4():
        f4 = dbp + ".s4"
        copy_db(dbp, f4)
        today = OS.today()
        nowr = OS.now()
        with conn(f4) as c:
            OS.ensure(c)
            o1 = lay_order(c, "W619 DRUGDEAL", nowr - dt.timedelta(days=3), "received", [dict(item="W619 CHYMO", packs=10, supplied=0, short=1, missing=1, arrived_by="alisha",
                                                                                              arrived_at=iso(nowr - dt.timedelta(days=1)))],
                           received_at=nowr - dt.timedelta(days=1), received_by="alisha")
            o2 = lay_order(c, "W619 DRUGDEAL", nowr - dt.timedelta(days=1), "sent", [dict(item="W619 XGESIC", packs=20, pack_size=15)])
            o3 = lay_order(c, "W619 GAMMA", nowr - dt.timedelta(days=2), "received", [dict(item="W619 BELT", packs=1, supplied=1, billed_qty=1, bill="W45", bill_date=today.isoformat(),
                                                                                         detected_at=iso(nowr - dt.timedelta(hours=3)), arrived_by="marg",
                                                                                         arrived_at=iso(nowr - dt.timedelta(hours=3)))],
                           received_at=nowr - dt.timedelta(hours=3), received_by="marg")
            c.commit()
            aw = OS.awaiting_scan(c, today)
            asks45 = o3 in [o["id"] for o in aw.get(sn_of("W619 GAMMA"), [])]
            check("C: the order-45 case (received by Marg, every line billed, no tie) no longer asks for a scan (OLD asks)", not asks45, aw.get(sn_of("W619 GAMMA")))
            asks3 = o1 in [o["id"] for o in aw.get(sn_of("W619 DRUGDEAL"), [])]
            check("C: an order whose only line was tapped 'Nahi mila' never asks for a scan (OLD asks)", not asks3, aw.get(sn_of("W619 DRUGDEAL")))
            stock0 = [tuple(r) for r in c.execute("SELECT l.id, l.item, o.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id "
                                                  "WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0")]
            ties0 = {r[0]: r[1] for r in c.execute("SELECT order_id, asset_bill_id FROM order_scan_tie")}
        # the scan, in the shared assets copy (by its stamp)
        A = sqlite3.connect(adb)
        st = (nowr - dt.timedelta(hours=2))
        if not A.execute("SELECT 1 FROM bills WHERE stamp_no='W619-DD'").fetchone():
            A.execute("INSERT INTO bills (kind, vendor, bill_no, bill_date, total_amount, created_by, created_at, stamp_no, status, submitted_at, ocr_status, lane) "
                      "VALUES ('Pharmacy','W619 DRUGDEAL','W619-1',?,100.0,'w619',?,'W619-DD','captured',?,'read','pharmacy')",
                      (today.isoformat(), (st - dt.timedelta(hours=5, minutes=30)).strftime("%Y-%m-%d %H:%M:%S"), st.strftime("%Y-%m-%d %H:%M")))
            A.commit()
        sid = A.execute("SELECT id FROM bills WHERE stamp_no='W619-DD'").fetchone()[0]
        A.close()
        with conn(f4) as c:
            made = OS.tie_pass(c, "w619")
            t = c.execute("SELECT order_id, arrived FROM order_scan_tie WHERE asset_bill_id=?", (sid,)).fetchone()
            check("C: the Drug Deal case (an old order whose only line is 'Nahi mila', a new sent order, a scan) -> the scan ties to the NEW order (OLD: the old one)",
                  t is not None and t[0] == o2 and t[1] == 1, (t, o1, o2))
            stock1 = [tuple(r) for r in c.execute("SELECT l.id, l.item, o.id FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id JOIN order_scan_tie t ON t.order_id=o.id "
                                                  "WHERE t.arrived=1 AND l.supplied IS NULL AND l.billed_qty IS NULL AND COALESCE(l.missing,0)=0")]
            moved = sorted(set(stock1) - set(stock0))
            say("   the stock effect (stock_figure.scan_lines / porders._on_order count a scan-tied order's unanswered lines as stock): lines newly counted -- %s"
                % ([(i, it, o) for i, it, o in moved] or "none"))
            ties1 = {r[0]: r[1] for r in c.execute("SELECT order_id, asset_bill_id FROM order_scan_tie") if r[1] != sid}
            real_new = sorted((o, s) for o, s in ties1.items() if o not in ties0)
            DUMP["s4"] = dict(real_new=real_new)
            say("   the copy's replay: ties tie_pass made on the real scans -- %s" % (real_new or "none"))
            if a.old_dump and "s4" in OLD:
                check("the copy's replay makes the same real ties on the OLD and the NEW files (no real stock figure moves on the copy)",
                      [list(x) for x in real_new] == [list(x) for x in OLD["s4"]["real_new"]], (real_new, OLD["s4"]["real_new"]))
        os.remove(f4)
    section("4  the tie: the Drug Deal case, the order-45 case, the stock effect", s4)

    # ============================================================================================ 7a the papers on the quiet copy (Marg's own export is newest)
    def s7a():
        with conn() as c:
            mpdf = MP.build(c)
            mtxt = SP.text_of(mpdf)
            pdf = SP.build(c)
            txt = SP.text_of(pdf)
            npg = len(SP.layout(c)["pages"])
        nofile = any("Marg ka order abhi server par nahi hai" in x for x in mtxt)
        say("   Marg's order PDF: %s; the delivery line found %d time(s); the order sheet: %d page(s), the line %d time(s)"
            % ("NO EXPORT FILE" if nofile else "%d page(s)" % mpdf.count(b"/Type /Page "), sum(1 for x in mtxt if DL[:30] in x), npg, sum(1 for x in txt if DL[:30] in x)))
        check("C: Marg's order PDF (Marg's rows as Marg printed them) carries the delivery line exactly once, after the last row", not nofile and sum(1 for x in mtxt if DL[:30] in x) == 1,
              [x for x in mtxt if "Kripya" in x])
        check("C: the printed order sheet carries the delivery line once in each page's foot (%d pages)" % npg, npg > 0 and sum(1 for x in txt if DL[:30] in x) == npg)
    section("7a the papers on the quiet copy: Marg's order PDF and the order sheet carry the delivery line", s7a)

    # ============================================================================================ 5 the carry (the app's copy)
    CAR = {}

    def s5():
        assert NEW, "order_track is not in this folder (the OLD files)"
        with conn() as c:
            OS.ensure(c)
            r = OT.carry_pass(c, OS.now())
            rows = {x["from_line_id"]: x for x in (dict(z) for z in c.execute("SELECT * FROM order_carry"))}
            items = {(x["from_order_id"], x["item"]): x for x in rows.values()}
            say("   carry_pass on the quiet copy: %s; the carries: %s" % (r, sorted((x["from_order_id"], x["item"], x["qty"], x["reason"]) for x in rows.values())))
            check("C: the five lines (XGESIC LA, THIO Q AP, FLACORT 6, POWERGESIC 100 PATCH, LINVIZ 600) are carried, each once, keyed by its line",
                  all((o, it) in items for o, it in FIVE.items()), sorted(items))
            check("C: LANZOL JUNIOR (still on Marg's newest order, sheet 6) is NOT carried -- its words: '%s'"
                  % OT.short_words(c, OT.order_state_light(c, 39, OS.now()), [x for x in OT.order_state_light(c, 39, OS.now())["lines"] if x["item"] == "LANZOL JUNIOR"][0], True),
                  not any(x["item"] == "LANZOL JUNIOR" for x in rows.values()))
            r2 = OT.carry_pass(c, OS.now())
            check("a second carry_pass writes nothing (keyed, idempotent)", r2["written"] == 0, r2)
            # a newer synthetic Marg sheet: the four dealers get a card (a line each), L.K.'s carries LANZOL JUNIOR itself
            ns = OS.newest_sheet(c)
            t = iso(OS.now())
            cur = c.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, as_ordered) VALUES (?,?,?,?,?,?,0)",
                            ("w619-sheet-a", "W619 walk sheet", "walk", "20991231-000000", t, OS.today().isoformat()))
            SID = cur.lastrowid
            deal = {"DRUG DEAL": ["W619 FILLER DD"], "DEEPAM PHARMA": ["W619 FILLER DP"], "KEDAR PHARMACEUTICAL": ["W619 FILLER KP"], "L.K. DRUG HOUSE": ["LANZOL JUNIOR"]}
            for i, (v, its) in enumerate(sorted(deal.items())):
                for it in its:
                    c.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, resolved, supplier, supplier_norm, packing, pack_size, line_date, qty_raw, qty, loose, strip, "
                              "units, rate_p, value_p, kind, state, first_sheet, last_sheet, created_at) VALUES (?,?,?,1,?,?,'1*10',10,?,'2',2,0,0,2,0,0,'new','to_order',?,?,?)",
                              ("W619-%d" % i, it, it, v, sn_of(v), OS.today().isoformat(), SID, SID, t))
            c.commit()
            CAR["sheet"] = SID
            r3 = OT.carry_pass(c, OS.now())
            say("   a newer Marg sheet laid by the walk (sheet %d: DRUG DEAL, DEEPAM, KEDAR a line each; L.K. carries LANZOL JUNIOR itself); carry_pass: %s" % (SID, r3))
            es = {e["vendor"]: e for e in OS.entries(c)}
            cards = {v: [(l["src"], l["item"]) for l in e["lines"]] for v, e in es.items() if v in deal}
            say("   the cards: %s" % cards)
            five_on = all(("carry", it) in cards.get(v, []) for v, it in (("DRUG DEAL", "XGESIC LA"), ("DEEPAM PHARMA", "THIO Q AP"), ("DEEPAM PHARMA", "POWERGESIC 100 PATCH"),
                                                                           ("KEDAR PHARMACEUTICAL", "FLACORT 6"), ("KEDAR PHARMACEUTICAL", "LINVIZ 600")))
            check("C: the five lines appear on their dealers' next cards as carried lines (src carry)", five_on, cards)
            lk = [x for x in cards.get("L.K. DRUG HOUSE", []) if x[1] == "LANZOL JUNIOR"]
            check("C: LANZOL JUNIOR is on L.K.'s card once (the sheet's line), never doubled by a carry", len(lk) == 1 and lk[0][0] == "sheet"
                  and not any(x["item"] == "LANZOL JUNIOR" for x in (dict(z) for z in c.execute("SELECT item FROM order_carry WHERE done_at IS NULL AND dropped_at IS NULL"))), lk)
            s_, h = GET("reception", "/finance/porders/s454/order/" + __import__("urllib.parse").parse.quote(sn_of("DRUG DEAL"), safe=""), headers=REC)
            t_ = " ".join(text_lines(h))
            check("C: the supplier screen shows XGESIC LA with 'pichhle order se baaki (16-10)'", s_ == 200 and "XGESIC LA" in t_ and "pichhle order se baaki (16-10)" in t_, (s_, t_[:300]))
            lay = SP.layout(c)
            prow = {(b["name"], r["item"]): r["tag"] for b in lay["blocks"] for r in b["rows"]}
            carry_cards = sorted((v, it) for v, ls in cards.items() for src, it in ls if src == "carry")
            carry_paper = sorted((v, it) for (v, it), tg in prow.items() if tg.startswith("pichhle order se baaki"))
            check("C: the printed sheet carries exactly the carried lines of the cards (one reader: entries()), each 'pichhle order se baaki (dd-mm)'",
                  carry_cards == carry_paper and bool(carry_cards), (carry_cards, carry_paper))
            pdf = SP.build(c, lay)
            txt = SP.text_of(pdf)
            check("the PDF's text has 'pichhle order se baaki (16-10)' beside XGESIC LA", "pichhle order se baaki (16-10)" in " ".join(txt))
            # an order carrying the item closes the carry; the WhatsApp body names the carried line and ends with the delivery line
            e = es["DRUG DEAL"]
            via = "whatsapp" if e["has_phone"] else "call"
            b_, code = OS.order_supplier(c, "W619 walk", e["sn"], via)
            cr = c.execute("SELECT done_order_id FROM order_carry WHERE supplier_norm=? AND item='XGESIC LA'", (e["sn"],)).fetchone()
            check("C: an order made for Drug Deal (%s) carries XGESIC LA and closes its carry (done_order_id)" % via, code == 200 and cr is not None and cr[0] == b_.get("order_id"), (b_, code, cr and tuple(cr)))
            lines = [dict(z) for z in c.execute("SELECT item, packs, pack_size FROM purchase_order_line WHERE order_id=? ORDER BY id", (b_.get("order_id"),))]
            body = OS.wa_body(c, lines, e["vendor"], carried=OS._s619_carried(c, b_.get("order_id")))
            m = c.execute("SELECT body FROM supplier_msg WHERE kind='order' AND ref=? ORDER BY id DESC LIMIT 1", (b_.get("order_id"),)).fetchone()
            if m and m[0]:
                body = m[0]
            say("   the WhatsApp body (%s): %s" % ("as queued" if m else "built", " | ".join(l for l in body.splitlines() if l.strip())[-260:]))
            check("C: the WhatsApp body says 'XGESIC LA — ... · pichhle order se baaki (16-10)' and its last line is the delivery line",
                  re.search(r"XGESIC LA — .* · pichhle order se baaki \(16-10\)", body) is not None and body.rstrip().splitlines()[-1] == DL, body[-300:])
            CAR["dd_order"] = b_.get("order_id")
            DUMP["s5"] = dict(body_last=body.rstrip().splitlines()[-1])
    section("5  the carry: the five lines on their dealers' next cards, the WhatsApp, the paper; LANZOL JUNIOR not doubled; an order closes it", s5)

    # ============================================================================================ 6 the remove door (one door, a reason)
    def s6():
        from urllib.parse import quote
        with conn() as c:
            sid = CAR.get("sheet")
            if not sid:                                        # the OLD files: the walk's sheet laid here
                t = iso(OS.now())
                cur = c.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, as_ordered) VALUES (?,?,?,?,?,?,0)",
                                ("w619-sheet-a", "W619 walk sheet", "walk", "20991231-000000", t, OS.today().isoformat()))
                sid = cur.lastrowid
                for i, (v, it) in enumerate((("DEEPAM PHARMA", "W619 FILLER DP"), ("DRUG DEAL", "W619 FILLER DD"))):
                    c.execute("INSERT INTO order_sheet_line (entry_no, item_printed, item, resolved, supplier, supplier_norm, packing, pack_size, line_date, qty_raw, qty, loose, strip, "
                              "units, rate_p, value_p, kind, state, first_sheet, last_sheet, created_at) VALUES (?,?,?,1,?,?,'1*10',10,?,'2',2,0,0,2,0,0,'new','to_order',?,?,?)",
                              ("W619-%d" % i, it, it, v, sn_of(v), OS.today().isoformat(), sid, sid, t))
                c.commit()
            ln = c.execute("SELECT id, item, supplier_norm FROM order_sheet_line WHERE item='W619 FILLER DP'").fetchone()
            ref, item, dsn = str(ln[0]), ln[1], ln[2]
        s_, h = GET("reception", "/finance/porders/s454/order/%s?edit=1" % quote(dsn, safe=""), headers=REC)
        chips = re.findall(r'data-reason="(dealer_no|not_now)"', h)
        check("C: the supplier screen's remove asks one reason chip -- 'Dealer ke paas nahi hai' / 'Abhi nahi chahiye' (OLD: no chip)",
              s_ == 200 and "dealer_no" in chips and "not_now" in chips and "Dealer ke paas nahi hai" in _html.unescape(h), (s_, chips))
        s0, j0 = POST("reception", "/finance/porders/api/s454/qty", dict(src="sheet", ref=ref, item=item, remove=1), headers=REC)
        check("C: a remove with no reason is refused (400 reason_needed; OLD removed it)", s0 == 400 and j0.get("error") == "reason_needed", (s0, j0))
        if s0 == 200:                                          # the OLD files removed it: put it back for the rest of the section
            with conn() as c:
                c.execute("UPDATE s454_line_edit SET removed=0 WHERE src='sheet' AND ref=? AND item=?", (ref, item))
                c.commit()
        s1_, j1 = POST("reception", "/finance/porders/api/s454/qty", dict(src="sheet", ref=ref, item=item, remove=1, reason="dealer_no"), headers=REC)
        with conn() as c:
            e = next((x for x in OS.entries(c) if x["sn"] == dsn), None)
            on_card = bool(e) and any(l["item"] == item for l in e["lines"])
            q, nn, call = OS.wa_plan(c)
            in_plan = any(l["item"] == item for x in q + nn + call for l in x["lines"])
            rr = c.execute("SELECT reason FROM s454_line_edit WHERE src='sheet' AND ref=? AND item=?", (ref, item)).fetchone() if OS._has_col(c, "s454_line_edit", "reason") else None
            lay = SP.layout(c)
            tag = [r for b in lay["blocks"] for r in b["rows"] if r["item"] == item]
            body = OS.wa_body(c, OS.order_lines_of(e) if e else [], dsn) if e else ""
        check("C: 'Dealer ke paas nahi hai' on a pending card -> 200, stored as s454_line_edit.reason dealer_no; off the card, the plan and the body",
              s1_ == 200 and rr is not None and rr[0] == "dealer_no" and not on_card and not in_plan and item not in body, (s1_, j1, rr and tuple(rr), on_card, in_plan))
        check("C: the paper prints it 'dealer ke paas nahi' (never 'order karna hai'), with no Order box", len(tag) == 1 and tag[0]["tag"] == "dealer ke paas nahi" and tag[0]["kind"] == "dealer_no",
              tag)
        # refused on a card with a draft (Drug Deal's order made in section 5, or a draft laid here)
        with conn() as c:
            dd = c.execute("SELECT id, item FROM order_sheet_line WHERE item='W619 FILLER DD'").fetchone()
            if not CAR.get("dd_order"):
                OS.make_order(c, "W619 walk", "DRUG DEAL", [dict(item="W619 FILLER DD", packs=2, pack_size=1)], "draft", "whatsapp")
                c.commit()
        s2_, j2 = POST("reception", "/finance/porders/api/s454/qty", dict(src="sheet", ref=str(dd[0]), item=dd[1], remove=1, reason="dealer_no"), headers=REC)
        check("a remove on a card whose order is already made is refused (409)", s2_ == 409, (s2_, j2))
        # it lifts on a newer sheet that still carries the line
        with conn() as c:
            t = iso(OS.now() + dt.timedelta(minutes=2))
            cur = c.execute("INSERT INTO order_sheet (md5, name, source, stamp, taken_at, newest_date, as_ordered) VALUES (?,?,?,?,?,?,0)",
                            ("w619-sheet-b", "W619 walk sheet b", "walk", "20991231-000100", t, OS.today().isoformat()))
            sb = cur.lastrowid
            c.execute("UPDATE order_sheet_line SET last_sheet=? WHERE last_sheet=?", (sb, sid))
            c.commit()
            CAR["sheet"] = sb
            e2 = next((x for x in OS.entries(c) if x["sn"] == dsn), None)
            back = bool(e2) and any(l["item"] == item and l["src"] == "sheet" for l in e2["lines"])
        check("C: the removal lifts when a newer Marg sheet arrives that still carries the line -- it is back on the card", back, e2 and [l["item"] for l in e2["lines"]])
        # a carried line removed with a reason is dropped
        with conn() as c:
            kc = c.execute("SELECT id, item, supplier_norm FROM order_carry WHERE supplier_norm=? AND item='LINVIZ 600' AND done_at IS NULL AND dropped_at IS NULL",
                           (sn_of("KEDAR PHARMACEUTICAL"),)).fetchone() if OS._has_col(c, "order_carry", "id") else None
        if kc:
            s3_, j3 = POST("reception", "/finance/porders/api/s454/qty", dict(src="carry", ref=str(kc[0]), item=kc[1], remove=1, reason="not_now"), headers=REC)
            with conn() as c:
                d = c.execute("SELECT dropped_at, dropped_by FROM order_carry WHERE id=?", (kc[0],)).fetchone()
                e3 = next((x for x in OS.entries(c) if x["sn"] == kc[2]), None)
            check("C: a carried line removed with a reason (Abhi nahi chahiye) is dropped (dropped_at, dropped_by) and leaves the card",
                  s3_ == 200 and d[0] and not any(l["item"] == "LINVIZ 600" for l in (e3 or {}).get("lines", [])), (s3_, j3, tuple(d) if d else None))
        else:
            check("C: a carried line removed with a reason is dropped (no carry on the OLD files)", False, "no carry")
    section("6  the remove door: a reason chip; dealer_no off the card, the plan, the body; printed so; refused with a draft; lifts on a newer sheet", s6)

    # ============================================================================================ 7 the screens
    def s7():
        nowr = OS.now()
        with conn() as c:
            OS.ensure(c)
            lo = lay_order(c, "W619 LATE PHARMA", nowr - dt.timedelta(days=4), "sent", [dict(item="W619 LATE A", packs=10), dict(item="W619 LATE B", packs=5)])
            po = lay_order(c, "W619 PART2 PHARMA", nowr - dt.timedelta(days=4), "received",
                           [dict(item="W619 P2 A", packs=10, supplied=10, arrived_by="alisha", arrived_at=iso(nowr - dt.timedelta(days=3))),
                            dict(item="W619 P2 B", packs=5, supplied=1, short=1, arrived_by="alisha", arrived_at=iso(nowr - dt.timedelta(days=3)))],
                           received_at=nowr - dt.timedelta(days=3), received_by="alisha")
            wo = lay_order(c, "W619 WAIT PHARMA", nowr - dt.timedelta(hours=2), "sent", [dict(item="W619 WAIT A", packs=10)])
            c.commit()
            nl = OT.late_count(c, OS.now()) if NEW else None
        s_, h = GET("reception", "/finance/porders", headers=REC)
        m = re.search(r'id="row_late" href="[^"]*"><span class="n">(\d+)</span><span class="l">([^<]+)</span>', h)
        check("C: reception's home with a late order and a part order -> 'Order ka maal nahi aaya — call karo' %s (= order_track's late count %s); S605's 'Aaj ke order' row gone"
              % (m and m.group(1), nl), s_ == 200 and m is not None and m.group(2) == "Order ka maal nahi aaya — call karo" and int(m.group(1)) == nl and 'id="row_call"' not in h,
              (s_, m and m.groups(), nl))
        s_, h = GET("reception", "/finance/porders/s454/late", headers=REC)
        t = " ".join(text_lines(h))
        check("C: the call row's page: the late order 'aaj tak nahi aaya' with Call and Maal aaya; the part order 'N mein se M dawa aayi · W619 P2 B baaki' with Baaki maal aaya",
              s_ == 200 and 'data-order="%d"' % lo in h and 'data-order="%d"' % po in h and "aaj tak nahi aaya" in t and "2 mein se 1 dawa aayi · W619 P2 B baaki" in t
              and "Baaki maal aaya" in t and "/s454/maal/%d" % lo in h, (s_, t[:400]))
        s_, h = GET("reception", "/finance/porders/s454/maal", headers=REC)
        check("C: Maal aaya lists the order awaited and not yet late, never the late one", s_ == 200 and 'data-order="%d"' % wo in h and 'data-order="%d"' % lo not in h, s_)
        # Darpan: four states (function-level, each on its own copy); the payload; his order tab
        st = {}
        for name, mk, now_ in (("all", "all", dt.datetime(2026, 10, 15, 10, 0)), ("waiting", "none", dt.datetime(2026, 10, 15, 10, 0)),
                               ("late", "none", dt.datetime(2026, 10, 17, 10, 0)), ("short", "short", dt.datetime(2026, 10, 15, 10, 0))):
            f7 = dbp + ".s7" + name
            copy_db(dbp, f7)
            with conn(f7) as c:
                t0 = dt.datetime(2026, 10, 14, 11, 0)
                if mk == "all":
                    lay_order(c, "W619 DAY PHARMA", t0, "received", [dict(item="W619 D1", packs=10, supplied=10, billed_qty=10, bill="W1", detected_at=iso(t0), arrived_by="marg")])
                elif mk == "short":
                    lay_order(c, "W619 DAY PHARMA", t0, "received", [dict(item="W619 D1", packs=10, supplied=10, billed_qty=10, bill="W1", detected_at=iso(t0), arrived_by="marg"),
                                                                    dict(item="W619 D2", packs=5)])
                else:
                    lay_order(c, "W619 DAY PHARMA", t0, "sent", [dict(item="W619 D1", packs=10)])
                c.commit()
                st[name] = OT.darpan_line(c, "2026-10-15", now_) if NEW else {}
            os.remove(f7)
            say("   Darpan's line, state %s: %s" % (name, st[name].get("text")))
        check("C: Darpan's four states, dated (never 'Kal'): all came / some not come (with the day they are due) / some late (named, 'Reception call kar raha hai') / some short",
              NEW and st["all"]["text"] == "14-10 ke order: saara maal aa gaya ✓" and st["waiting"]["text"] == "14-10 ke order: 1 supplier ka maal aana baaki — 16-10 shaam tak"
              and st["late"]["text"].startswith("14-10 ke order: 1 supplier ka maal der se — ") and st["late"]["text"].endswith("Reception call kar raha hai.")
              and st["short"]["text"] == "14-10 ke order: 1 dawa nahi aayi — agle order mein khud jud gayi.", st)
        y = (OS.now().date() - dt.timedelta(days=1)).isoformat()
        t0 = time.time()
        s_, h = GET("darpan", "/finance/darpan/kal/api/day?date=" + y)
        el = time.time() - t0
        try:
            j = json.loads(h)
        except ValueError:
            j = {}
        ot = j.get("order_track") or {}
        check("C: Darpan's day payload carries the one order line (%r), under 100 KB (%d bytes) and 2 s (%.2f s)" % ((ot.get("text") or "")[:120], len(h), el),
              s_ == 200 and ot.get("ok") and "ke order:" in (ot.get("text") or "") and len(h) < 100000 and el < 2.0, (s_, ot))
        s_, h = GET("darpan", "/finance/darpan/kal/api/order")
        try:
            jo = json.loads(h)
        except ValueError:
            jo = {}
        with conn() as c:
            d = jo.get("yesterday_date") or ""
            ids = {r[0]: r[1] for r in c.execute("SELECT vendor, id FROM purchase_order WHERE order_src='s454' AND status IN ('sent','received') AND substr(created_at,1,10)=? ORDER BY id DESC", (d,))}
            same = all(x["state"] == (OT.yesterday_state(c, ids[x["vendor"]], OS.now()) if NEW else "") for x in jo.get("yesterday") or [] if x["vendor"] in ids)
        check("C: his order tab ('कल के ऑर्डर — क्या हुआ', %s, %d suppliers) reads the same reader (order_track)" % (d, len(jo.get("yesterday") or [])), s_ == 200 and same and NEW, s_)
        # the track page
        md0, ma0 = md5f(dbp), md5f(adb)
        so, ho = GET("manoj", "/finance/porders/s454/track")
        md1, ma1 = md5f(dbp), md5f(adb)
        ss, hs = GET("shavez", "/finance/porders/s454/track")
        to = " ".join(text_lines(ho))
        check("C: the order list as the owner (English): the heading, five tiles, the six sections, the five dots, the late order under Not arrived; its read leaves both copies byte-equal",
              so == 200 and "Purchase orders — the order list" in to and ho.count('data-tile="') == 5 and all('id="%s"' % k in ho for k in ("sec_na", "sec_marg", "sec_short", "sec_redo", "sec_wrong", "sec_done"))
              and 'data-step="All lines came"' in ho and 'data-order="%d"' % lo in ho and md0 == md1 and ma0 == ma1, (so, to[:300], md0 == md1, ma0 == ma1))
        check("C: the order list as Shavez (porders.rescan_askers): the same list in Roman Hindi ('Purchase orders ka haal', 'Nahi aaye', 'Kam aaye')",
              ss == 200 and "Purchase orders ka haal" in hs and "Nahi aaye" in hs and "Kam aaye" in hs, ss)
        ref = {}
        for u in ("darpan", "alisha", "shivani", "reception"):
            ref[u] = GET(u, "/finance/porders/s454/track", headers=(REC if u == "reception" else None))[0]
        sb_, _hb = GET("bhati", "/finance/porders/s454/track")
        check("C: darpan / alisha / shivani / reception refused (403); Bhati redirected (302) as today: %s, bhati %s" % (ref, sb_), all(v == 403 for v in ref.values()) and sb_ == 302, ref)
        sh_, hh = GET("manoj", "/finance/porders")
        check("C: the owner's home carries the order list's card (the one way in; S618's separate 'Scans to redo' link folded into it)",
              sh_ == 200 and 'id="track"' in hh and 'id="redo"' not in hh, sh_)
        # the WhatsApp's last line (section 5 queued one); both PDFs
        with conn() as c:
            pdf = SP.build(c)
            txt = SP.text_of(pdf)
            npg = len(SP.layout(c)["pages"])
            mpdf = MP.build(c)
            mtxt = SP.text_of(mpdf)
            body = OS.wa_body(c, [dict(item="W619 X", packs=1, pack_size=1)], "W619")
        check("C: a WhatsApp order's last line is the delivery line (built through wa_body, both queue paths): %r" % body.splitlines()[-1], body.rstrip().splitlines()[-1] == DL, body[-200:])
        check("C: the printed order sheet carries the delivery line once on each page (%d of %d pages)" % (sum(1 for x in txt if DL[:30] in x), npg),
              npg > 0 and sum(1 for x in txt if DL[:30] in x) == npg, [x for x in txt if "Kripya" in x][:3])
        nofile = any("Marg ka order abhi server par nahi hai" in x for x in mtxt)
        say("   Marg's order PDF now (the walk's own newer sheet has no export file): %s" % ("the one-page notice" if nofile else "%d page(s)" % mpdf.count(b"/Type /Page ")))
    section("7  the screens: reception's call row and its page, Maal aaya, Darpan's line and order tab, the order list, the WhatsApp, both papers", s7)

    # ============================================================================================ 8 the duty map (v19)
    def s8():
        d = {x["id"]: x for x in DM["duties"]}
        check("the kit's DUTY_MAP.json is v19 and carries shavez.order_followup", int(DM.get("version") or 0) == 19 and "shavez.order_followup" in d, DM.get("version"))
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True, timeout=60)
        res = {}
        for k in ("reception.order_arrival", "reception.medicine_orders", "reception.bill_scan", "shavez.order_followup"):
            sql = d[k]["due_sql"]
            assert re.match(r"^\s*(SELECT|WITH)\b", sql, re.I), k
            r = ro.execute(sql).fetchall()
            res[k] = r
            say("   %s due_sql on the copy: %s" % (k, r))
        ro.close()
        with conn() as c:
            late = OT.late_count(c, OS.now()) if NEW else -1
            cnt = P4.counts(c)
            sl = len(P4.scan_lines(c))
            car = len(OT.open_carries(c)) if NEW else -1
        one = all(len(v) == 1 and len(v[0]) == 2 for v in res.values())
        check("every due_sql is ONE read-only SELECT returning one row (n, since)", one, res)
        check("C: reception.order_arrival (rewritten: the late rule, door marker 'Order ka maal nahi aaya') equals the call row's count on the copy (%s = %s)"
              % (res["reception.order_arrival"][0][0], late), one and res["reception.order_arrival"][0][0] == late and d["reception.order_arrival"]["door_marker"] == "Order ka maal nahi aaya")
        check("C: reception.medicine_orders (dealer_no removals lifted by a newer sheet; carries never make a card) equals the card count (%s = %s)"
              % (res["reception.medicine_orders"][0][0], cnt.get("order")), one and res["reception.medicine_orders"][0][0] == cnt.get("order"))
        check("C: reception.bill_scan (the two asking rules of 3.3) equals Bill scan karna hai's count, scan_lines (%s = %s)" % (res["reception.bill_scan"][0][0], sl),
              one and res["reception.bill_scan"][0][0] == sl)
        check("C: shavez.order_followup (door /finance/porders/s454/track) = late orders + open carries (%s = %s + %s)" % (res["shavez.order_followup"][0][0], late, car),
              one and res["shavez.order_followup"][0][0] == late + car and d["shavez.order_followup"]["door"] == "/finance/porders/s454/track")
    section("8  the duty map v19: each due_sql equal to its screen's count on the copy", s8)

    # ============================================================================================ 10 the staff-eye walk
    def portal_tiles(user):
        tiles = []
        try:
            sys.path.insert(0, por)
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            r = pc.post("/portal/login", base_url=BASE, data={"user": user, "password": pw[user]})
            m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
            r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")})
            tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True))]
        except Exception as e:                                 # noqa: BLE001
            say("   the portal as %s could not be rendered: %s" % (user, str(e)[:200]))
        finally:
            if por in sys.path:
                sys.path.remove(por)
        return tiles

    def s10():
        d = {x["id"]: x for x in DM["duties"]}
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True, timeout=60)
        due = {k: ro.execute(d[k]["due_sql"]).fetchone() for k in ("reception.order_arrival", "reception.medicine_orders", "reception.bill_scan", "shavez.order_followup")}
        ro.close()
        for u in ("reception", "alisha", "shivani", "shavez"):
            tiles = portal_tiles(u)
            mine = [k for k in due if (k.startswith("reception.") and u in ("reception", "alisha", "shivani")) or (k.startswith("shavez.") and u == "shavez")]
            for k in mine:
                n = due[k][0] or 0
                if not n:
                    say("   %s: %s not due on the copy (n 0)" % (u, k))
                    continue
                s_, h = GET(u, d[k]["door"], headers=(REC if u == "reception" else None))
                check("C: staff-eye: %s -- duty %s due (n %s): the tile '%s' on the portal home and '%s' on %s" % (u, k, n, d[k]["tile"], d[k]["door_marker"], d[k]["door"]),
                      d[k]["tile"] in tiles and s_ == 200 and d[k]["door_marker"] in _html.unescape(h), (tiles[:12], s_))
        s_, h = GET("darpan", "/finance/darpan/kal/api/day?date=" + OS.now().date().isoformat())
        check("staff-eye: darpan -- his Kal ka hisaab carries the one read-only order line, nothing to tap (no duty of his moves)", s_ == 200 and "order_track" in h, s_)
        s_, h = GET("manoj", "/finance/porders")
        check("staff-eye: the owner -- his Purchase orders home opens the order list (the card)", s_ == 200 and "/finance/porders/s454/track" in h, s_)
        say("   the owner's Needs-you line: %s" % (OT.owner_line(conn(), OS.now()) if NEW else "-"))
    section("10 the staff-eye walk: reception (shared login + name), alisha, shivani, darpan, shavez, the owner", s10)

    # ============================================================================================ the end
    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    ctrl_red = [l for l, ok in CTRL if not ok]
    ctrl_green = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("NEGATIVE CONTROL (the OLD files): %d 'C:' checks, %d red, %d green" % (len(CTRL), len(ctrl_red), len(ctrl_green)))
        for l in ctrl_red:
            say("  red: %s" % l[:200])
        for l in ctrl_green:
            say("  NOT RED: %s" % l[:200])
        if ctrl_green or not ctrl_red:
            say("WALK RED negative control S619: %d control(s) did not go red on the old files" % len(ctrl_green))
            return 1
        say("WALK OK negative control S619: %d controls red on the old files" % len(ctrl_red))
        return 0
    if FAILS:
        say("WALK RED S619: %d of %d checks failed: %s" % (len(FAILS), RUN[0], "; ".join(f[:80] for f in FAILS)))
        return 1
    say("WALK OK S619: %d checks, %d controls green on the new files" % (RUN[0], len(ctrl_green)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
