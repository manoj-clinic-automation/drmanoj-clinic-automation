#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s605.py -- kit S605_ORDER_FIXES (20-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s605.py --fin <scratch /root/finance with the files under test; spine/ = that side's spine copy and its state>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --por <scratch /root/portal copy:
                            every .py but portal_config.py, tile_grants.json -- the walk writes its OWN secret and user store into it>
                            --duty-map <the kit's DUTY_MAP.json (v17)> --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s605.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --por ... --duty-map ...
The real finance app (and, for the staff-eye homes, the real portal) in one process: the walk's own header session for the finance pages, its
own portal sign-in (a random secret, its own user store -- never the live ones) and its own reception-phone key on the copy. Its own rows by
key (W605 ...): its own suppliers, orders and messages, the keep numbers of the orthotic lines it puts to Darpan (porder_keep, on the copy),
and its own sale lines on a SECOND spine copy (the side's spine is never written: bytes compared). The clock of the hand-out is the walk's
(the modules' own now() set in process). No phone number is printed (ten digits masked). Sections follow the brief's section 4: the page
dumps (8) run FIRST on the quiet copy (--old-dump compares); --expect-red is the negative control: the same walk on the OLD files, every
'C:' check must be red. Prints 'WALK OK S605 ...'."""
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

KIT = "S605_ORDER_FIXES"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "darpan": "staff", "reception": "staff", "bhati": "staff", "shavez": "manager", "amir": "staff"}
NINE = ("order_sheet.py", "porders_s454.py", "supplier_msg.py", "order_sheet_pdf.py", "marg_order_pdf.py", "darpan_kal.py", "darpan_kal.html")
RIB, ANKLE = "RIB BELT UNIVERSAL UNISON", "ANKLE BINDER BAMBOO M"
S605_TEXTS = ("not offered for ordering", "never confirmed it")
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
        check("C: section %s ran without an exception" % title[:40], False, "%s: %s | %s" % (type(e).__name__, str(e)[:300], traceback.format_exc()[-1200:]))


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


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W605 walk only -- a random secret made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 'w605-walk-seed'\n" % secret)
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


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import order_sheet as OS                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import porders_s454 as P4                                 # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    OS.ensure(con)
    new = hasattr(OS, "ortho_offer")
    say("STATE %s: files %s; clock %s IST; order.source %s" % (label, "NEW (S605)" if new else "OLD", OS.now().strftime("%Y-%m-%d %H:%M:%S"), OS.source(con)))
    es = OS.entries(con)
    ol = [(l["item"], l["qty"]) for e in es for l in e["lines"] if l["src"] == "ortho"]
    say("STATE %s: the orthotic card's lines on reception's order: %s" % (label, ol or "none"))
    sh = PO.shelf(con)
    short = [(it["item"], it["short"], it["shelf"], it.get("family_shelf"), it.get("marg")) for it in sh["items"] if it["short"] > 0]
    say("STATE %s: porders' orthotic shortage (item, short, shelf, family figure, Marg): %s" % (label, short or "none"))
    if new:
        d = OS.darpan_ortho(con)
        say("STATE %s: put to Darpan (Orthotic kam hai -- %s): %s; yes %s no %s" % (label, d.get("n"), [(x["item"], x["short"]) for x in d.get("items") or []],
                                                                                  d.get("yes_at") or "-", d.get("no_at") or "-"))
        say("STATE %s: the S605 owner lines: %s" % (label, [l["text"] for l in OS._s605_owner_lines(con)] or "none"))
        q, nn, call = OS.wa_plan(con)
        say("STATE %s: 'Sab ko WhatsApp bhejo' would queue %s; no number %s; call %s" % (label, [e["vendor"] for e in q], [e["vendor"] for e in nn], [e["vendor"] for e in call]))
    c = P4.counts(con)
    rowcall = len(P4._done_today(con)) if (c["order"] <= 0 and new) else 0
    say("STATE %s: reception's home rows: Order karna hai %d%s; Maal aaya? %d; Bill scan karna hai %d; Photo dekh kar bataiye %d" % (
        label, c["order"], ("; Aaj ke order -- call karo %d" % rowcall) if rowcall else "", c["maal"], c["scan"], c["q"]))
    say("STATE %s: today's order messages: %s" % (label, [tuple(r) for r in con.execute(
        "SELECT id, vendor, status, attempts, substr(queued_at,12,5), substr(handed_at,12,5), substr(sent_at,12,5) FROM supplier_msg WHERE kind='order' "
        "AND substr(queued_at,1,10)=? ORDER BY id", (OS.now().date().isoformat(),))] or "none"))
    con.rollback()
    con.close()
    say("STATE OK S605 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--por", "--duty-map", "--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    a = ap.parse_args()
    for k in ("fin", "db", "adb", "marg"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S605_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)) + ((os.path.abspath(a.por),) if a.por else ()):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump or not a.por or not a.duty_map:
        ap.error("--dump, --por and --duty-map are needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S605 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
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
    import order_sheet_pdf as SP                              # noqa: E402
    import marg_order_pdf as MP                               # noqa: E402
    for m in (fa, OS, PO, P4, SM, SP, MP):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(OS, "ortho_offer")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; order_sheet %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none", "NEW (S605)" if NEW else "OLD"))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    spine_md5_0 = md5f(SPINE_PATH)
    SRC = {n: open(os.path.join(fin, n), encoding="utf-8").read() for n in NINE}
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    DM = json.load(open(os.path.abspath(a.duty_map), encoding="utf-8"))
    PHONE = "w605" + secrets.token_hex(12)                     # the walk's own reception-phone key, on the copy only
    real_now, real_sm_now = OS.now, SM._now
    NOW0 = OS.now()

    def GET(u, path, follow=False, headers=None):
        hd = {"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}
        hd.update(headers or {})
        r = cl.get(path, base_url=BASE, headers=hd, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, json=body)
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
        """The hand-out's clock: order_sheet.now and supplier_msg._now, in process (None = the real clock)."""
        OS.now = (lambda: t) if t else real_now
        SM._now = (lambda: t) if t else real_sm_now

    def sn_of(v):
        return OS._pa().supplier_key(v)

    F951 = []

    def K20(n):
        return re.sub(r"\s+", " ", (n or "").strip())[:20].strip()

    with conn() as c_:
        OS.ensure(c_)
        SM.ensure(c_)
        rn = [K20(r[0]) for r in c_.execute("SELECT old_name FROM marg_item_rename WHERE done_at IS NOT NULL")]
        FAMOLD = {k for k in rn if rn.count(k) > 1}            # F-951: the old keys more than one ticked rename shares
        YV = PO.vendor_of(c_)
        YSN = sn_of(YV)
        c_.execute("UPDATE setting SET value=? WHERE key='supplier_msg.phone_token'", (PHONE,))
        c_.commit()
    say("   today %s, now %s; the orthotic vendor %s; the copy's reception-phone key replaced by the walk's own" % (NOW0.date(), NOW0, YV))

    # ============================================================================================ 8 (first): the pages and the APIs dumped on the quiet copy
    def s8():
        pages = [("darpan", "/finance/darpan/kal/api/day"), ("darpan", "/finance/darpan/kal/api/order"), ("reception", "/finance/porders"),
                 ("reception", "/finance/porders/s454/order"), ("reception", "/finance/porders/s454/maal"), ("reception", "/finance/porders/s454/scan"),
                 ("amir", "/finance/amir"), ("manoj", "/finance/sanjeevni/api/needs-you"), ("shavez", "/finance/purchase/page/pay")]
        with conn() as c_:
            oo = OS.open_order(c_)
            sup = (oo["lines"][0]["supplier_norm"] if oo["lines"] else None)
        if sup:
            from urllib.parse import quote
            pages.append(("reception", "/finance/porders/s454/order/" + quote(sup, safe="")))
        changed = {}
        for u, path in pages:
            s, h = GET(u, path, follow=True)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))[:120]
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "now", "server_time", "user", "as_of", "today", "ortho_short", "purchase_upto"):
                            j.pop(k, None)                    # ortho_short: Darpan's orthotic section (D749) is this kit's own change
                        if isinstance(j.get("lines"), list):
                            j["lines"] = [l for l in j["lines"] if not any(t in str(l.get("text")) for t in S605_TEXTS)]
                            j.pop("count", None)
                            for l in j["lines"]:                # F-951's own change: the newest FAMILY bill of an orthotic size (its own key now)
                                t = str(l.get("text") or "")
                                if K20(t.split(":")[0]) in FAMOLD and re.search(r" \(its bill .*?, not this size\)", t):
                                    F951.append(t)
                                    l["text"] = re.sub(r" \(its bill .*?, not this size\)", " (its bill <the family's newest bill: F-951>)", t)
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = []
            for l in body.splitlines():
                if not l.strip() or re.search(r"^(Call: |WhatsApp: )|· WhatsApp: ", l) or "Aaj ke order — call karo" in l or "Today's orders — call" in l \
                        or "Reception phone unlocked rakhiye" in l:
                    continue                                  # sections 3.3-3.5: the numbers, the call row, the unlock line
                lines.append(re.sub(r"\d{1,2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l))
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
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
        say("   F-951's own change, masked in the owner's arrival lines (the family's newest bill of an orthotic size): %s" % (F951 or "none"))
        DUMP["s8"] = dict(pages=[p for _u, p in pages], f951=F951)
        if a.old_dump:
            ok_ = not changed or all(set(v[0]) == set(v[1]) or _only_count(v) for v in changed.values())
            check("every page dump (Darpan's day less its orthotic section, his order tab, reception's home / order list / supplier / maal / scan pages "
                  "less the numbers, the call row and the unlock line, Amir's page, the approvals Needs-you less the S605 lines, the pay page) is "
                  "byte-equal to the OLD files' dumps (%d differ)" % len(changed), ok_, {k: (v[0][:3], v[1][:3]) for k, v in changed.items()})

    def _only_count(v):
        """The home's lone count line of the call row (its words are masked; the number stands on its own line)."""
        gone, new = v
        return not gone and all(re.match(r"^\d+$", l) for l in new)
    section("8 (first) the pages and the APIs dumped on the quiet copy -- byte-equal OLD vs NEW but sections 3.3-3.5", s8)

    # ---- the walk's own orthotic lines: keep numbers on the copy, sales on a SECOND spine copy
    SYN = os.path.join(os.path.dirname(dbp), "spine_syn_%s" % ("old" if a.expect_red else "new"))
    if os.path.isdir(SYN):
        shutil.rmtree(SYN)
    os.makedirs(SYN)
    copy_db(SPINE_PATH, os.path.join(SYN, "spine.db"))
    for f in ("spine_state.json",):
        if os.path.exists(os.path.join(fin, "spine", f)):
            shutil.copy(os.path.join(fin, "spine", f), os.path.join(SYN, f))
    PO.SPINE_DIR = SYN                                        # porders reads the walk's own spine copy (its sales are the walk's)
    W = {}

    def shelf(c):
        return {it["item"]: it for it in PO.shelf(c)["items"]}

    def keep(c, item, k):
        c.execute("UPDATE porder_keep SET keep=?, source='w605', set_by='w605walk' WHERE item=?", (int(k), item))
        c.commit()

    def sale(item, units, n):
        s = sqlite3.connect(os.path.join(SYN, "spine.db"))
        s.execute("INSERT INTO sp_sale_line (date, bill, seq, name20, k20, pack, qty_raw, units, rate_p, batch, expiry) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                  (NOW0.date().isoformat(), "W605%03d" % n, 1, re.sub(r"\s+", " ", item)[:20], "W605", "1*1", str(units), float(units), 0, "", ""))
        s.commit()
        s.close()

    def ortho_lines(c):
        return sorted((l["item"], int(l["qty"])) for e in OS.entries(c) for l in e["lines"] if l["src"] == "ortho")

    def sheet_rows(c):
        lay = SP.layout(c)
        return sorted((r["item"], r["qty"]) for b in lay["blocks"] if sn_of(b["name"]) == YSN for r in b["rows"] if r["kind"] in ("new", "line") and not r["marg"])

    def darpan_items():
        s, h = GET("darpan", "/finance/darpan/kal/api/day")
        o = (json.loads(h) if s == 200 else {}).get("ortho_short") or {}
        return [(x["item"], x["short"]) for x in o.get("items") or []], o

    def answer(action, items):
        return POST("darpan", "/finance/darpan/kal/api/ortho", dict(action=action, items=[dict(item=i, qty=q) for i, q in items]))

    def wa_all_copy():
        """whatsapp_all on a THIRD copy (its writes stay there): the suppliers whose order message it queues."""
        p3 = dbp + ".wa3"
        copy_db(dbp, p3)
        c3 = conn(p3)
        c3.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('supplier_msg.phone_last', ?, 'w605')", (OS.now_iso() + " 200",))
        c3.commit()
        m0 = c3.execute("SELECT COALESCE(MAX(id),0) FROM supplier_msg").fetchone()[0]
        if NEW:
            q = [e["sn"] for e in OS.wa_plan(c3)[0]]
            OS.whatsapp_all(c3, "w605walk", expect=q)
        else:
            OS.whatsapp_all(c3, "w605walk")
        got = [r[0] for r in c3.execute("SELECT vendor_norm FROM supplier_msg WHERE id>? AND kind='order'", (m0,))]
        c3.close()
        os.remove(p3)
        return got

    # ============================================================================================ 1 Darpan's yes to the orthotic list (D749, F-959)
    def s1():
        c = conn()
        sh = shelf(c)
        assert RIB in sh and ANKLE in sh, "the two lines of the brief are on porders' orthotic list"
        bad = ANKLE if (sh[ANKLE]["shelf"] < 0 or (sh[ANKLE].get("family_shelf") or 0) < 0) else None
        say("   on the copy: %s shelf %s (family %s, Marg %s, on order %s); %s shelf %s (on order %s)" % (
            ANKLE, sh[ANKLE]["shelf"], sh[ANKLE].get("family_shelf"), sh[ANKLE].get("marg"), sh[ANKLE]["on_order"], RIB, sh[RIB]["shelf"], sh[RIB]["on_order"]))
        if bad is None:                                        # the copy no longer holds the brief's -1: lay one (a single-size item, the walk's own sales)
            cand = sorted(x for x, it in sh.items() if it.get("family_n", 1) == 1 and it["shelf"] >= 0 and x != RIB)
            bad = cand[0]
            for n in range(int(sh[bad]["shelf"]) + 1):
                sale(bad, 1, 900 + n)
            say("   the copy holds no impossible figure for %s -- the walk lays one: %s sold below zero on its own spine copy" % (ANKLE, bad))
            sh = shelf(c)
        keep(c, RIB, int(sh[RIB]["shelf"]) + int(sh[RIB]["on_order"]) + 1)       # RIB short 1
        keep(c, bad, max(1, int(sh[bad]["on_order"]) + 2))                          # the impossible line short too
        sh = shelf(c)
        W.update(rib_short=sh[RIB]["short"], bad=bad, bad_short=sh[bad]["short"])
        say("   the walk's keep numbers on the copy: %s short %s; %s short %s (shelf %s)" % (RIB, sh[RIB]["short"], bad, sh[bad]["short"], sh[bad]["shelf"]))
        # no yes yet
        ol, rows, wq = ortho_lines(c), sheet_rows(c), wa_all_copy()
        say("   no answer yet: the orthotic card %s; the printed sheet's orthotic rows %s; whatsapp_all queues %s" % (ol, rows, wq))
        check("C: (1) no yes yet -> no orthotic card on reception's order (entries)", not ol, ol)
        check("C: (1) no yes yet -> no orthotic row on the printed sheet (layout)", not rows, rows)
        check("C: (1) no yes yet -> 'Sab ko WhatsApp bhejo' queues no orthotic message", YSN not in wq, wq)
        items, o = darpan_items()
        say("   Darpan's section (api/day ortho_short): n %s, lines %s, who %s" % (o.get("n"), items, o.get("who")))
        check("C: (1) Darpan is put %s x%d and never %s (its figure is below zero)" % (RIB, W["rib_short"], bad), (RIB, W["rib_short"]) in items and not any(i == bad for i, _q in items), items)
        s, j = GET("manoj", "/finance/sanjeevni/api/needs-you")
        nl = [l.get("text") for l in (json.loads(j).get("lines") or [])] if s == 200 else []
        ol_ = [t for t in nl if bad in str(t) and "not offered for ordering" in str(t)]
        say("   the owner's Needs-you: %s" % (ol_ or "no line for %s" % bad))
        check("C: (1) the owner's line: '%s — the system's ... figure is −N (Marg M): not offered for ordering; the count or a sale needs a look'" % bad,
              len(ol_) == 1 and "the count or a sale needs a look" in ol_[0], nl[:8])
        # the staff-eye walk (CLAUDE.md, every duty has a door): Darpan's portal home and his door while the list waits for him
        tiles = portal_tiles("darpan")
        sd, hd = GET("darpan", "/finance/darpan/kal")
        check("staff-eye: Darpan's portal home shows 'Kal ka hisaab' (the door of his orthotic duty)", "Kal ka hisaab" in tiles, tiles)
        check("C: staff-eye: the door /finance/darpan/kal draws 'Orthotic kam hai — N · <vendor> ko order?' with हाँ / इस बार नहीं / हटाओ while a line waits (n %s)" % o.get("n"),
              sd == 200 and "ko order?" in hd and "हाँ, ऑर्डर में डालो" in hd and "इस बार नहीं" in hd and "हटाओ" in hd and (o.get("n") or 0) >= 1, (sd, o.get("n")))
        s, j = POST("bhati", "/finance/darpan/kal/api/ortho", dict(action="yes", items=[dict(item=RIB, qty=W["rib_short"])]))
        say("   Bhati at the new door: %s" % s)
        check("(1) Bhati's view is refused at the new door (no medical role: the login gate)", s in (302, 401, 403, 404), s)
        # yes with RIB kept
        s, j = answer("yes", [(RIB, W["rib_short"])])
        say("   हाँ (%s x%d): %s %s" % (RIB, W["rib_short"], s, j))
        check("C: (1) Darpan's हाँ is taken at /finance/darpan/kal/api/ortho (200)", s == 200 and j.get("ok"), (s, j))
        ol, rows = ortho_lines(c), sheet_rows(c)
        say("   after हाँ: the card %s; the sheet %s" % (ol, rows))
        check("C: (1) after हाँ the card and the sheet carry %s x%d only" % (RIB, W["rib_short"]), ol == [(RIB, W["rib_short"])] and [r[0] for r in rows] == [RIB], (ol, rows))
        items, o = darpan_items()
        check("C: (1) after हाँ his section shows '✓ ऑर्डर में गया · HH:MM' and the kept line is off his list", o.get("yes_at") and not any(i == RIB for i, _q in items), o)
        # हटाओ, then हाँ: two lines of the walk's own
        cand = sorted(x for x, it in sh.items() if it.get("family_n", 1) == 1 and it["shelf"] >= 0 and (it.get("family_shelf") or 0) >= 0
                      and x not in (RIB, bad) and it["short"] == 0)
        P, Q, R = cand[0], cand[1], cand[2]
        W.update(P=P, Q=Q, R=R)
        for x in (P, Q):
            keep(c, x, int(sh[x]["shelf"]) + int(sh[x]["on_order"]) + 2)
        sh = shelf(c)
        items, o = darpan_items()
        say("   the walk's two more lines (single sizes, short 2 each): %s, %s -> put to him %s" % (P, Q, items))
        s1_, j1 = answer("remove", [(P, sh[P]["short"])])
        items, o = darpan_items()
        s2_, j2 = answer("yes", items)
        ol = ortho_lines(c)
        say("   हटाओ %s: %s; then हाँ %s: %s -> the card %s" % (P, s1_, items, s2_, ol))
        check("C: (1) हटाओ then हाँ -> only the kept lines on the card (%s, %s), %s not" % (RIB, Q, P),
              s1_ == 200 and s2_ == 200 and items == [(Q, sh[Q]["short"])] and [x[0] for x in ol] == sorted([RIB, Q]), (ol, s1_, s2_, items))
        items, o = darpan_items()
        check("C: (1) the removed line is not put to him again while its shortage is unchanged", s1_ == 200 and not any(i == P for i, _q in items), items)
        # इस बार नहीं: the walk's third line
        keep(c, R, int(sh[R]["shelf"]) + int(sh[R]["on_order"]) + 2)
        items, o = darpan_items()
        s3_, j3 = answer("no", items)
        items2, o2 = darpan_items()
        ol = ortho_lines(c)
        say("   इस बार नहीं %s: %s -> put to him %s; the card %s; his section '%s'" % (items, s3_, items2, ol, o2.get("no_at")))
        os.environ["ORDER_TODAY"] = (NOW0.date() + dt.timedelta(days=1)).isoformat()
        items3, _o3 = darpan_items()
        ol3 = ortho_lines(c)
        os.environ.pop("ORDER_TODAY", None)
        check("C: (1) इस बार नहीं -> nothing on the card from it, and nothing put to him again -- on the next day too -- while the shortage is unchanged",
              s3_ == 200 and items == [(R, 2)] and not items2 and not items3 and R not in [i for i, _q in ol + ol3], (s3_, items, items2, items3, ol))
        sale(R, 1, 1)
        items4, _o4 = darpan_items()
        say("   a sale of %s on the walk's own spine copy moves its shortage -> put to him %s" % (R, items4))
        check("C: (1) a sale moves the shortage -> the line is put to him again", s3_ == 200 and any(i == R for i, _q in items4), items4)
        s, j = answer("yes", [(RIB, 99)])
        check("(1) a stale list is refused (409 list_changed), nothing written", s in (404, 409), (s, j))
        DUMP["s1"] = dict(W=W)
        c.close()

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
    section("1  Darpan's yes (D749, F-959): no yes -> nothing; हाँ / हटाओ / इस बार नहीं; the impossible figure; the door", s1)

    # ---- the walk's own suppliers, orders and messages (section 2)
    def mk_order(c, name, status="draft"):
        oid = OS.make_order(c, "w605walk", name, [dict(item="W605 ITEM " + name[-1], packs=1, pack_size=1, rate_p=0)], status, "whatsapp")
        c.commit()
        return oid

    def mk_msg(c, name, kind, ref, queued_at, month=None):
        c.execute("INSERT INTO supplier_msg (month, vendor_norm, vendor, kind, ref, to_number, body, status, queued_at) VALUES (?,?,?,?,?,?,?,?,?)",
                  (month or NOW0.strftime("%Y-%m"), sn_of(name), name, kind, ref, "w605-not-a-number", "W605 walk message", "queued", queued_at))
        c.commit()
        return c.execute("SELECT id FROM supplier_msg WHERE kind=? AND ref=? AND vendor=?", (kind, ref, name)).fetchone()[0]

    def nxt(t):
        clock(t)
        s, h = GET("manoj", "/finance/api/supplier-msg/next", headers={"X-Phone-Token": PHONE})
        try:
            return (json.loads(h) or {}).get("id")
        except ValueError:
            return "HTTP %s" % s

    def done(t, mid, ok):
        clock(t)
        r = cl.post("/finance/api/supplier-msg/done", base_url=BASE, headers={"X-Phone-Token": PHONE}, json=dict(id=mid, ok=ok, error="" if ok else "w605: not sent"))
        return r.status_code

    def msg(c, mid):
        return dict(c.execute("SELECT id, status, handed_at, last_error, attempts FROM supplier_msg WHERE id=?", (mid,)).fetchone())

    def card(c, sn):
        return next((e for e in OS.entries(c) if e["sn"] == sn), None)

    def park(c, *mids):
        c.execute("UPDATE supplier_msg SET status='skipped', last_error='w605: the walk is done with it' WHERE id IN (%s) AND status IN ('queued','failed')" % ",".join("?" * len(mids)), mids)
        c.commit()

    # ============================================================================================ 2 one hand-out (F-960, F-702)
    def s2():
        c = conn()
        T0 = NOW0.replace(second=0, microsecond=0)
        t = lambda m: T0 + dt.timedelta(minutes=m)              # noqa: E731
        iso = lambda m: t(m).isoformat()                        # noqa: E731
        A, B, C = "W605 SUPPLIER A", "W605 SUPPLIER B", "W605 SUPPLIER C"
        oa = mk_order(c, A)
        ma = mk_msg(c, A, "order", oa, "2000-01-01T00:00:01")
        h0 = nxt(t(0))
        h11 = nxt(t(11))
        say("   order message %s (%s): handed at T %s -> %s; at T+11 the phone asks again -> %s" % (ma, A, t(0).strftime("%H:%M"), h0, h11))
        check("(2) the phone is handed the walk's order message at T", h0 == ma, h0)
        check("C: (2) at T+11 min the same message is NOT handed again (F-960)", h11 != ma, h11)
        mb_o = mk_order(c, B)
        mb = mk_msg(c, B, "order", mb_o, iso(0))
        clock(t(61))
        n = OS.withdraw_late(c)
        c.commit()
        ra, rb = msg(c, ma), msg(c, mb)
        oA = dict(c.execute("SELECT status, order_via, sent_by FROM purchase_order WHERE id=?", (oa,)).fetchone())
        aud = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s454_whatsapp_unconfirmed' AND ref=?", (str(oa),)).fetchone()[0]
        eA, eB = card(c, sn_of(A)), card(c, sn_of(B))
        say("   T+61: withdraw_late -> %s; A: message %s, order %s, card %s, audit unconfirmed %s; B (never handed): message %s, card %s" % (
            n, (ra["status"], (ra["last_error"] or "")[:60]), oA, (eA or {}).get("state"), aud, (rb["status"], (rb["last_error"] or "")[:40]), (eB or {}).get("state")))
        check("C: (2) handed, no done, T+61: the order is sent by WhatsApp, marked unconfirmed (audit, the message 'unconfirmed: ...', never 'sent'), the supplier not pending",
              oA["status"] == "sent" and oA["order_via"] == "whatsapp" and aud == 1 and ra["status"] == "skipped" and (ra["last_error"] or "").startswith("unconfirmed:") and eA is None,
              (oA, ra, aud, (eA or {}).get("state")))
        r = OS.order_supplier(c, "w605walk", sn_of(A), "whatsapp")
        c.commit()
        ra2 = msg(c, ma)
        check("C: (2) a send-all queues nothing for it (the message is never queued again)", ra2["status"] != "queued", (r, ra2))
        s, j = GET("manoj", "/finance/sanjeevni/api/needs-you")
        nl = [l.get("text") for l in (json.loads(j).get("lines") or [])] if s == 200 else []
        ln = [x for x in nl if str(x).startswith(A + " — the reception phone took the order at")]
        say("   the owner's line: %s" % (ln or "none"))
        check("C: (2) the owner's line: '%s — the reception phone took the order at %s but never confirmed it. It was not sent again.'" % (A, t(0).strftime("%H:%M")),
              len(ln) == 1 and ("at %s but never confirmed it. It was not sent again." % t(0).strftime("%H:%M")) in ln[0], nl[:6])
        check("(2) never handed by T+61 -> withdrawn, its supplier pending again ('WhatsApp nahi gaya')", rb["status"] == "skipped" and (eB or {}).get("state") == "withdrawn", (rb, (eB or {}).get("state")))
        r = OS.order_supplier(c, "w605walk", sn_of(B), "whatsapp")
        c.commit()
        rb2 = msg(c, mb)
        check("(2) ... and re-queued on a tap (it never reached the phone)", rb2["status"] == "queued" and rb2["handed_at"] is None, (r, rb2))
        park(c, mb)
        # ok:false -> withdrawn; never queued again once handed
        oc = mk_order(c, C)
        mc = mk_msg(c, C, "order", oc, "2000-01-01T00:00:02")
        hc = nxt(t(62))
        dc = done(t(63), mc, False)
        rc = msg(c, mc)
        eC = card(c, sn_of(C))
        check("(2) the phone answers ok:false -> withdrawn at once, the supplier pending again", hc == mc and dc == 200 and rc["status"] == "skipped" and (eC or {}).get("state") == "withdrawn", (hc, dc, rc, (eC or {}).get("state")))
        r = OS.order_supplier(c, "w605walk", sn_of(C), "whatsapp")
        c.commit()
        rc2 = msg(c, mc)
        check("C: (2) ... and a send-all never queues again a message the phone was handed (call instead)", rc2["status"] != "queued", (r, rc2))
        park(c, mc)
        # a payment message: handed, no done -> never again; failed -> retried after RETRY_MIN
        mp = mk_msg(c, "W605 PAYEE", "neft", 605, "2000-01-01T00:00:03", month="2000-01")
        h1 = nxt(t(70))
        h2 = nxt(t(81))
        check("C: (2) a payment message handed, no done: not handed again at T+11", h1 == mp and h2 != mp, (h1, h2))
        dp = done(t(82), mp, False)
        h3 = nxt(t(82 + SM.RETRY_MIN + 1))
        check("(2) a payment message the phone said it could not send is retried after RETRY_MIN (%d min)" % SM.RETRY_MIN, dp == 200 and h3 == mp, (dp, h3))
        park(c, mp)
        mt = mk_msg(c, "Test message", "test", 605605, "2000-01-01T00:00:04", month="test")
        h4 = nxt(t(120))
        h5 = nxt(t(131))
        check("(2) the owner's test message is handed again after the gap, as before", h4 == mt and h5 == mt, (h4, h5))
        park(c, mt)
        clock(None)
        s, h = GET("manoj", "/finance/purchase/page/phone-setup")
        check("C: (2) the phone-setup page says 'Ek message server ek hi baar deta hai.' and no longer '10 minute tak dobara nahi milta'",
              s == 200 and "Ek message server ek hi baar deta hai." in h and "10 minute tak dobara nahi milta" not in h, s)
        # the walk's suppliers leave the order: their drafts made sent (their own rows)
        c.execute("UPDATE purchase_order SET status='cancelled' WHERE created_by='w605walk' AND vendor LIKE 'W605 SUPPLIER %'")
        c.commit()
        c.close()
    section("2  one hand-out (F-960, F-702): never handed twice; unconfirmed -> sent, the owner's line; never-handed withdrawn; ok:false; payments; test", s2)

    # ============================================================================================ 3 the confirm screen (F-961)
    def s3():
        clock(None)
        c = conn()
        c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('supplier_msg.phone_last', ?, 'w605')", (OS.now_iso() + " 200",))
        c.commit()
        N = "W605 NO NUMBER"
        onn = mk_order(c, N)                                   # a pending card with no number (a draft whose message never was)
        c.execute("UPDATE purchase_order SET status='draft' WHERE id=?", (onn,))
        c.commit()
        W["nonum_order"] = onn
        s, h = GET("reception", "/finance/porders/s454/order")
        check("C: (3) the order list's 'Sab ko WhatsApp bhejo' is a link to the confirm screen -- no direct POST from #waall",
              'id="waall"' in h and "/s454/order/whatsapp" in h and "api/s454/whatsapp" not in h, re.findall(r'<[^>]*id="waall"[^>]*>', h)[:1])
        m0 = md5f(dbp)
        s, h = GET("reception", "/finance/porders/s454/order/whatsapp")
        m1 = md5f(dbp)
        shown = re.findall(r'data-sn="([^"]+)"', h)
        nonum = re.findall(r'data-nonum="([^"]+)"', h)
        q = [e["sn"] for e in OS.wa_plan(c)[0]] if NEW else []
        say("   the confirm screen (%s): shows %s; no number %s; wa_plan queues %s; finance.db md5 before %s after %s" % (s, shown, nonum, q, m0[:8], m1[:8]))
        check("(3) its read writes nothing (the copy's md5 before = after; true of the OLD address too -- a supplier page -- so not a control)", s == 200 and m0 == m1, (s, m0, m1))
        check("C: (3) the screen lists exactly what 'Sab ko WhatsApp bhejo' queues now, each with its numbers, and the no-number line",
              s == 200 and NEW and [_html.unescape(x) for x in shown] == q and _html.unescape(nonum[0] if nonum else "") == sn_of(N) and "number nahi hai, call kijiye" in h
              and "Haan, WhatsApp bhejo" in h and "Nahi, wapas" in h and ("WhatsApp: " in h if q else True), (shown, nonum, q))
        before = (c.execute("SELECT COALESCE(MAX(id),0) FROM supplier_msg").fetchone()[0], c.execute("SELECT COALESCE(MAX(id),0) FROM purchase_order").fetchone()[0])
        s1_, j1 = POST("darpan", "/finance/porders/api/s454/whatsapp", dict(sns=q + ["W605 GHOST"]))
        after = (c.execute("SELECT COALESCE(MAX(id),0) FROM supplier_msg").fetchone()[0], c.execute("SELECT COALESCE(MAX(id),0) FROM purchase_order").fetchone()[0])
        say("   a stale list -> %s %s; rows before %s after %s" % (s1_, j1.get("error"), before, after))
        check("C: (3) a POST with a list that is not the list now -> 409, nothing queued", s1_ == 409 and j1.get("error") == "list_changed" and before == after, (s1_, j1, before, after))
        s2_, j2 = POST("darpan", "/finance/porders/api/s454/whatsapp", dict(sns=q))
        qd = [r[0] for r in c.execute("SELECT vendor_norm FROM supplier_msg WHERE id>? AND kind='order'", (before[0],))]
        say("   the list shown -> %s queued %s" % (s2_, qd))
        check("(3) the list shown -> queued, one message per supplier shown", s2_ == 200 and j2.get("ok") and sorted(qd) == sorted(q), (s2_, j2, qd))
        nw = c.execute("SELECT COUNT(*) FROM supplier_msg WHERE kind='order' AND status='queued' AND to_number IS NOT NULL AND substr(queued_at,1,10)=?",
                       (OS.now().date().isoformat(),)).fetchone()[0]
        s, h = GET("reception", "/finance/porders/s454/order")
        want = "Reception phone unlocked rakhiye. WhatsApp khud khulega, har minute ek supplier (%d minute)." % nw
        check("C: (3) the order list then says '%s'" % want, nw >= 1 and want in _html.unescape(h), nw)
        c.close()
    section("3  the confirm screen (F-961): a read that writes nothing; the list; 409 on a stale list; the unlock line", s3)

    # ============================================================================================ 4 the home's call row (F-962)
    def s4():
        c = conn()
        s, h = GET("reception", "/finance/porders")
        cnt = P4.counts(c)
        say("   with a pending card (the walk's no-number supplier): counts %s; rows %s" % (cnt, re.findall(r'id="(row_[a-z]+)"', h)))
        check("(4) some pending -> only 'Order karna hai' (no second row to the same page)", 'id="row_order"' in h and 'id="row_call"' not in h, re.findall(r'id="(row_[a-z]+)"', h))
        c.execute("UPDATE purchase_order SET status='cancelled' WHERE id=?", (W.get("nonum_order") or 0,))
        c.commit()
        s, h = GET("reception", "/finance/porders")
        nd = len(P4._done_today(c))
        m = re.search(r'id="row_call"[^>]*><span class="n">(\d+)</span><span class="l">([^<]+)</span>', h)
        say("   nothing left to order: rows %s; the Ho chuke list %d; the call row %s" % (re.findall(r'id="(row_[a-z]+)"', h), nd, m.groups() if m else None))
        check("C: (4) nothing left to order -> 'Aaj ke order — call karo' with the Ho chuke count (%d)" % nd, bool(m) and int(m.group(1)) == nd and nd >= 1
              and "Aaj ke order — call karo" in m.group(2) and 'id="row_order"' not in h, (m.groups() if m else None, nd))
        c.close()
    section("4  the home: the call row once nothing is left to order (F-962)", s4)

    # ============================================================================================ 5 the numbers on the screens and both papers
    def s5():
        c = conn()
        s, h = GET("reception", "/finance/porders/s454/order")
        t = text_lines(h)
        nums = [l for l in t if l.startswith("Call: ") and " · WhatsApp: " in l]
        say("   the order list (%s): %d line(s) 'Call: … · WhatsApp: …' (e.g. %s)" % (s, len(nums), nums[:2]))
        check("C: (5) the cards and the Ho chuke lines carry 'Call: … · WhatsApp: …' for a sender", s == 200 and len(nums) >= 1, nums[:2])
        s, h = GET("bhati", "/finance/porders/s454/order")
        check("(5) none for Bhati: the order screen is not his (refused, no number)", s != 200 or "WhatsApp: " not in h, s)
        pdf = SP.build(c)
        tx = SP.text_of(pdf)
        bands = [x for x in tx if x.startswith("Call: ") or x.startswith("Number nahi")]
        say("   the order sheet PDF: %d band line(s) (e.g. %s); 'Ph. ' %d" % (len(bands), bands[:2], sum(1 for x in tx if x.startswith("Ph. "))))
        check("C: (5) the order sheet prints 'Call: … · WhatsApp: …' under each supplier, never 'Ph.'", bands and all(" · WhatsApp: " in x or x.startswith("Number nahi") for x in bands)
              and not any(x.startswith("Ph. ") for x in tx), tx[:6])
        mp = MP.build(c)
        mt = SP.text_of(mp)
        pb = [x for x in mt if x.startswith("Phone book - ")]
        oo = OS.open_order(c)
        groups = len({l["supplier_norm"] for l in oo["lines"]})
        say("   Marg's order PDF: %d 'Phone book' line(s) for %d supplier group(s) (e.g. %s)" % (len(pb), groups, pb[:2]))
        check("C: (5) Marg's PDF carries one shaded 'Phone book — Call: … · WhatsApp: …' line under each supplier's group (Marg's rows as Marg printed them)",
              groups >= 1 and len(pb) == groups and all(("Call: " in x and "WhatsApp: " in x) or "Number nahi" in x for x in pb), (len(pb), groups, pb[:3]))
        c.close()
    section("5  the numbers: the order screens (a sender, not Bhati) and both PDFs", s5)

    # ============================================================================================ 6 F-951 on this side's spine
    def s6():
        s = sqlite3.connect("file:%s?mode=ro" % SPINE_PATH, uri=True)
        fam = s.execute("SELECT alias, source FROM sp_alias WHERE kind='rename_family' ORDER BY alias").fetchall()
        own = [k for k, _s in fam if s.execute("SELECT 1 FROM sp_close WHERE k20=? LIMIT 1", (k,)).fetchone()]
        g = s.execute("SELECT COUNT(*), SUM(ok) FROM sp_gate WHERE blocking=1").fetchone()
        say("   this side's spine: %d renamed size(s) keep their own key (%d with Marg's closings under it); gate %s/%s" % (len(fam), len(own), g[1], g[0]))
        check("C: (6) the eight orthotic families' new names own their keys after their split day (22 sizes, sp_alias 'rename_family')", len(fam) == 22 and len(own) >= 15, (len(fam), len(own)))
        check("(6) the spine's gate passes on this side", g[0] and g[0] == g[1], tuple(g))
        s.close()
    section("6  F-951 on this side's spine (the scratch build OLD vs NEW is the installer's: spine_cmp_s605.py)", s6)

    # ============================================================================================ 9 the greps and nothing else moved
    def s9():
        o, p = SRC["order_sheet.py"], SRC["porders_s454.py"]
        check("C: entries() reads the kept lines (ortho_kept), never the shortage ('\"ortho:\" + t.isoformat()' gone)", "ortho_kept(con)" in o and '"ortho:" + t.isoformat()' not in o)
        check("C: one list for the send-all (wa_plan), the screen reads it", "def wa_plan(" in o and "OS.wa_plan(con)" in p)
        check("C: nums_text once in porders_s454 and read by both PDFs", p.count("def nums_text(") == 1 and "nums_text(" in SRC["order_sheet_pdf.py"] and "nums_text(" in SRC["marg_order_pdf.py"])
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
        check("the side's spine copy is unchanged by the walk (its sales went to a second copy)", md5f(SPINE_PATH) == spine_md5_0)
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("9  the greps, the spine copy untouched, healthz", s9)

    clock(None)
    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S605: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S605: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S605: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S605: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
