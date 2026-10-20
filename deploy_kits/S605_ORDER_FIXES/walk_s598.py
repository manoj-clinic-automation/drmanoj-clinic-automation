#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s598.py -- kit S598_ARRIVALS_BY_LINE (19-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s598.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --kit <the kit folder: rejudge / undo>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s598.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --kit ...   (the install-day state)
The real finance app in one process (the walk's own header session -- its own secret and user store, never the live ones): every login the
kit's screens belong to (reception, darpan, amir, shavez, the owner) is signed in and its pages rendered. Its own rows by key (W598 ...),
never by counting; the live rows by key. The spine COPY is never written by the code under test (bytes compared); the walk's synthetic bills
go to a SECOND copy (spine_syn.db) through a plain rw connection, sp_meta.built bumped. No phone number is printed (ten digits masked).
Sections follow the brief's section 4 (controls 0-13); the re-judge (8) runs before the staff screens (10) so the screens show the
install-day state AFTER the data step; --old-dump compares with the OLD files' dumps. --expect-red is the negative control: the same walk on
the OLD files, every 'C:' check must be red. --state prints the install-day state (the brief's section 5). Prints 'WALK OK S598 ...'.
S605 (F-957): --rows-json <the S598 install's purchase_order_line JSON>: the walk LAYS ITS OWN ROWS -- the seven rows as S593 marked them,
put back on ITS COPY by id before anything is read (the live re-judge of 19-Oct no longer decides the walk); the KIT line may name a later
kit (S602 placed stock_figure since); on a spine built by S605 (F-951) the renamed sizes own their keys (sp_alias 'rename_family')."""
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
import time

KIT = "S598_ARRIVALS_BY_LINE"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
THREE = ("stock_figure.py", "stock_watch.py", "porders.py")
SINCE = "2026-10-19T08:03:00"
SEVEN = [2, 3, 28, 30, 36, 47, 50]
RENAMES = [("ANKLE BINDER BAMBOO M", "ANKLE BINDER M BAMBOO"), ("ANKLE BINDER BAMBOO L", "ANKLE BINDER L BAMBOO"),
           ("KNEE SUPPORT HINGED XL", "KNEE SUPPORT XL HINGED"), ("KNEE SUPPORT HINGED XXL UNISO", "KNEE SUPPORT XXL HINGED")]
XL, XXX, XXL, ABL = "KNEE SUPPORT HINGED XL", "L S BELT CONT GRAY UNISON XXX", "KNEE SUPPORT HINGED XXL UNISO", "ANKLE BINDER BAMBOO L"
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


def line_rows(con, ids=None):
    q = ("SELECT l.id, l.order_id, l.item, l.packs, l.pack_size, l.supplied, l.short, l.missing, l.billed_qty, l.billed_bill_no, l.billed_date, l.detected_at, l.arrived_by, "
         "l.arrived_at, o.vendor, o.created_at, o.status FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id")
    if ids:
        q += " WHERE l.id IN (%s)" % ",".join(str(int(i)) for i in ids)
    return {int(r[0]): dict(r) for r in con.execute(q + " ORDER BY l.id")}


def open_rows(con):
    return [r for r in line_rows(con).values() if r["billed_qty"] is None and r["status"] in ("sent", "received") and not r["missing"]]


def _w(name):
    """S605 (F-957): a size name by its words -- 'KNEE SUPPORT HINGED M' and 'KNEE SUPPORT M HINGED' (the rename Marg now prints on the old
    bills' lines) are the same size."""
    return tuple(sorted(str(name or "").split()))


def hit_text(h, packs=None):
    if not h:
        return "no carrying bill line"
    if h.get("how") == "a":
        return "(a) its own bill %s of %s, units %s" % (h["bill"], h["date"], h.get("units"))
    q = int(round(float(h.get("qty") or 0) + float(h.get("free") or 0))) if "qty" in h else packs
    return "(%s) bill %s of %s%s, packs %s, units %s" % (h["how"], h["bill"], h["date"], (" line %s %r" % (h.get("seq"), h.get("name27"))) if "seq" in h else "", q, h.get("units"))


def old_packs(sw, SF, item, hit, ctx):
    """detect_supplies' packs as the OLD porders read them (SUM(qty)+SUM(free) of the bill for the key) -- for the OLD side's table."""
    k20 = SF.key_of(sw, item, ctx)
    pr = sw.q("SELECT COALESCE(SUM(qty),0) AS q, COALESCE(SUM(free),0) AS f FROM sp_purchase_line WHERE k20=? AND supkey=? AND bill=? AND date=? AND direction='PURCHASE'",
              k20, hit["supkey"], hit["bill"], hit["date"])
    return int(round(float(pr[0]["q"] or 0) + float(pr[0]["f"] or 0))) if pr else 0


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    PO.ensure_schema(con)
    new = hasattr(SF, "_purchase_lines_of")
    say("STATE %s: files %s; stock_figure v%s KIT %s" % (label, "NEW (S598)" if new else "OLD", SF.VERSION, SF.KIT))
    S = {k: v for k, v in con.execute("SELECT key, value FROM setting WHERE key IN ('arrival.bill_grace_days','arrival.back_days','order.source','order.stock_basis','porders.ortho_vendor') ORDER BY key")}
    say("STATE %s: settings %s" % (label, S))
    sw = SW.Spine()
    rows = line_rows(con)
    seven = [r for r in rows.values() if r["detected_at"] and r["detected_at"] >= SINCE]
    say("STATE %s: S593's marks (detected_at >= %s): %d row(s) -- ids %s" % (label, SINCE, len(seven), [r["id"] for r in seven]))
    for r in sorted(rows.values(), key=lambda x: x["id"]):
        if r["id"] in SEVEN:
            say("   line %-4s order %-3s %-30s packs %3s supplied %-4s short %-4s billed %-4s by %-14s of %-10s detected %-19s arrived_by %-6s arrived_at %s"
                % (r["id"], r["order_id"], r["item"][:30], r["packs"], r["supplied"], r["short"], r["billed_qty"], r["billed_bill_no"], r["billed_date"], r["detected_at"], r["arrived_by"], r["arrived_at"]))
    opn = open_rows(con)
    say("STATE %s: open order lines (billed_qty NULL, sent / received): %d -- carried() under these files:" % (label, len(opn)))
    for r in opn:
        ctx = SF.Ctx(con, sw)
        h = SF.carried(con, sw, dict(line_id=r["id"], item=r["item"], vendor=r["vendor"], order_at=r["created_at"], billed_bill_no=None), ctx)
        say("   line %-4s order %-3s %-30s %-24s packs %3s supplied %-4s | %s" % (r["id"], r["order_id"], r["item"][:30], r["vendor"][:24], r["packs"], r["supplied"], hit_text(h)))
    for o in PO._orders(con):
        if o["id"] in (1, 20):
            say("STATE %s: reception's Orders card, order %s (%s, %s): open lines %d; %s" % (label, o["id"], o["vendor"][:20], o["status"], o["open_lines"],
                "; ".join("%s %s=%s" % (l["id"], l["item"][:26], l["state"]) for l in o["lines"])))
            say("   the 'all' button (open_lines > 0): %s" % ("shown" if o["open_lines"] else "hidden"))
    sh = PO.shelf(con)
    card = sorted((it["item"], it["short"]) for it in sh["items"] if it["short"] > 0)
    say("STATE %s: the orthotic shortage card: %d item(s) %s" % (label, len(card), card))
    say("STATE %s: on order (Yuvika, _on_order): %s" % (label, PO._on_order(con, sh["vendor"])))
    st = {o: r[0] for o in (1, 10, 13, 20) for r in [con.execute("SELECT status FROM purchase_order WHERE id=?", (o,)).fetchone() or (None,)]}
    say("STATE %s: purchase_order.status of 1, 10, 13, 20: %s" % (label, st))
    lines = SW.arrival_needs_you(con, SW.Spine())
    say("STATE %s: the owner's arrival lines (arrival_needs_you): %d" % (label, len(lines)))
    for l in lines:
        say("   %s" % l["text"])
    con.rollback()
    say("STATE OK S598 (%s)" % label)
    return 0


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--kit"):
        ap.add_argument(k, required=True)
    for k in ("--dump", "--old-dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--state", action="store_true")
    ap.add_argument("--label", default="now")
    ap.add_argument("--rows-json", default="")                 # S605 (F-957): the seven rows laid on the walk's copy
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S598_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S598 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    import item_alias as IA                                   # noqa: E402
    for m in (fa, SF, SW, PO, OR, OS, PA, IA):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(SF, "_purchase_lines_of")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; stock_figure v%s %s (%s)"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", SF.VERSION, SF.KIT, "NEW" if NEW else "OLD"))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    SYN_PATH = os.path.join(os.path.dirname(dbp), "spine_syn_%s.db" % ("old" if a.expect_red else "new"))
    schema0 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
    spine_md5_0 = hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest()
    SRC = {n: read(fin, n) for n in THREE}
    today = dt.date.today()
    TODAY = today.isoformat()
    KITDIR = os.path.abspath(a.kit)
    JSONP = os.path.join(a.dump, "rows_s598.json")

    def GET(u, path, follow=False):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def L(c, r, bno=None):
        return dict(line_id=r["id"], item=r["item"], vendor=r["vendor"], order_at=r["created_at"], billed_bill_no=bno, billed_date=(r.get("billed_date") if bno else None))

    c_ = conn()
    PO.ensure_schema(c_)
    OR.ensure(c_)
    c_.commit()
    if a.rows_json:                                            # S605 (F-957): the seven rows as S593 marked them, on THIS copy, by id
        J = json.load(open(a.rows_json, encoding="utf-8"))
        cols = [x for x in J["columns"] if x != "id"]
        laid = []
        for j in J["rows"]:
            if j["id"] in SEVEN:
                c_.execute("UPDATE purchase_order_line SET %s WHERE id=?" % ", ".join("%s=?" % x for x in cols), [j[x] for x in cols] + [j["id"]])
                laid.append(j["id"])
        c_.commit()
        say("   S605 (F-957): the walk laid its own rows on its copy -- lines %s as S593 marked them (the S598 install's JSON)" % laid)
    c_.close()
    sw0 = SW.Spine()
    assert sw0.ok and SW.SPINE_DB == SPINE_PATH, (sw0.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    c0 = conn()
    ORTHO = OR._ortho_norm(c0)
    OVEND = PO.vendor_of(c0)
    ROWS0 = line_rows(c0)
    c0.close()
    say("   today %s; the orthotic vendor %s (%s); arrival settings grace / back %s" % (TODAY, OVEND, ORTHO, SF._arr_settings(conn(), SF.Ctx(conn(), sw0))))

    # ============================================================================================ 0 the four renames
    def s0():
        c = conn()
        rows = {(r["old_name"], r["new_name"]): r["state"] for r in IA.done_rows(c)}
        for o, n in RENAMES:
            say("   rename %-30s -> %-30s %s" % (o, n, rows.get((o, n), "MISSING")))
        check("the four ticked renames the kit stands on are in item_alias.done_rows (R1-C1)", all((o, n) in rows for o, n in RENAMES), [p for p in RENAMES if p not in rows])
        seven = [r for r in ROWS0.values() if r["detected_at"] and r["detected_at"] >= SINCE]
        check("the seven rows S593's detect_supplies marked on 19-Oct are on the copy by id: %s" % SEVEN, sorted(r["id"] for r in seven) == SEVEN, sorted(r["id"] for r in seven))
        c.close()
    section("0  the four renames and the seven rows (R1-C1)", s0)

    # ============================================================================================ 1 bill 672, the real case
    def s1():
        c = conn()
        sw = SW.Spine()
        r3, r4, r1 = ROWS0[3], ROWS0[4], ROWS0[1]
        ctx = SF.Ctx(c, sw)
        h3 = SF.carried(c, sw, L(c, r3), ctx)
        fb3 = ctx.c.get(("fam_bill", 3))
        say("   line 3 %s (order 1, re-judged with billed_bill_no None): %s; family_bill %s" % (XL, hit_text(h3), fb3))
        check("C: line 3 KNEE SUPPORT HINGED XL -> carried() None (no XL line on 672 or any Yuvika bill) with family_bill = bill 672 of 28-09 [M, L]",
              h3 is None and bool(fb3) and SF._bill(fb3["bill"]) == "672" and fb3["date"] == "2026-09-28" and [_w(x) for x in fb3["sizes"]] == [_w("KNEE SUPPORT HINGED M"), _w("KNEE SUPPORT HINGED L")], (h3, fb3))
        ctx4 = SF.Ctx(c, sw)
        h4 = SF.carried(c, sw, L(c, r4), ctx4)
        fb4 = ctx4.c.get(("fam_bill", 4))
        say("   line 4 %s: %s; family_bill %s" % (XXL, hit_text(h4), fb4))
        check("C: line 4 KNEE SUPPORT HINGED XXL UNISO -> None with family_bill 672 [M, L] (None on OLD too, without the family bill)", h4 is None and bool(fb4) and SF._bill(fb4["bill"]) == "672", (h4, fb4))
        ha = SF.carried(c, sw, L(c, r1, r1["billed_bill_no"]), SF.Ctx(c, sw))
        say("   line 1 %s (S537's mark, rule a): %s" % (ABL, hit_text(ha)))
        check("C: line 1 ANKLE BINDER BAMBOO L by rule (a): the L line of 672 (1 pack, units 1) -- the LINE's figure, with its seq and name27",
              bool(ha) and ha.get("how") == "a" and ha.get("units") == 1.0 and ha.get("seq") is not None and _w(ha.get("name27")) == _w("ANKLE BINDER BAMBOO L"), ha)
        h3a = SF.carried(c, sw, L(c, r3, r3["billed_bill_no"]), SF.Ctx(c, sw))
        say("   line 3 as S593 marked it (rule a, bill 672): %s" % hit_text(h3a))
        check("C: line 3 by rule (a) as marked: carried (Marg's answer trusted) but units None -- no XL line on 672 (the OLD key sum said 6)",
              bool(h3a) and h3a.get("how") == "a" and h3a.get("units") is None, h3a)
        DUMP["s1"] = dict(h3=h3, fb3=fb3, h4=h4, fb4=fb4, ha=ha, h3a=h3a)
        c.close()
    section("1  bill 672, the real case (F942_READING 2): XL not on it; XXL; line 1 by rule (a); line 3's mark by rule (a)", s1)

    # ============================================================================================ 2 bill 2627, the real case
    def s2():
        c = conn()
        sw = SW.Spine()
        ctx = SF.Ctx(c, sw)
        r2, r48 = ROWS0[2], ROWS0[48]
        h2 = SF.carried(c, sw, L(c, r2), SF.Ctx(c, sw))
        q2 = int(round(float((h2 or {}).get("qty") or 0) + float((h2 or {}).get("free") or 0))) if h2 and "qty" in h2 else None
        say("   line 2 ANKLE BINDER BAMBOO M: %s -> packs %s (S593 wrote %s by %s)" % (hit_text(h2), q2, r2["billed_qty"], r2["billed_bill_no"]))
        check("C: line 2 ANKLE BINDER BAMBOO M -> bill 2627's 'ANKLE BINDER M BAMBOO' line (through the ticked rename), qty 1 -> packs 1 == S593's write (agree)",
              bool(h2) and h2.get("how") == "d" and SF._bill(h2["bill"]) == SF._bill(r2["billed_bill_no"]) and h2.get("name27") == "ANKLE BINDER M BAMBOO" and q2 == 1 == int(r2["billed_qty"]), (h2, q2))
        ctx48 = SF.Ctx(c, sw)
        h48 = SF.carried(c, sw, L(c, r48), ctx48)
        fb48 = ctx48.c.get(("fam_bill", 48))
        say("   line 48 ANKLE BINDER BAMBOO L (order 20): %s; family_bill %s" % (hit_text(h48), fb48))
        check("C: line 48 ANKLE BINDER BAMBOO L -> None with family_bill = 2627 of 07-10 [ANKLE BINDER M BAMBOO]",
              h48 is None and bool(fb48) and SF._bill(fb48["bill"]) == SF._bill(r2["billed_bill_no"]) and fb48["date"] == "2026-10-07" and fb48["sizes"] == ["ANKLE BINDER M BAMBOO"], (h48, fb48))
        keys = {}
        for nm in ("ANKLE BINDER BAMBOO M", "ANKLE BINDER M BAMBOO", "ANKLE BINDER BAMBOO L", "ANKLE BINDER L BAMBOO"):
            keys[nm] = SF.key_of(sw, nm, ctx)
            say("   key_of(%r) = %r%s" % (nm, keys[nm], ("; forms %s" % sorted(SF._line_forms(ctx, nm))) if NEW else ""))
        fam605 = bool(sw.q("SELECT 1 FROM sp_alias WHERE kind='rename_family' LIMIT 1"))
        if fam605:                                             # S605 (F-951): the old spellings share the old key; each new spelling owns its own
            check("the old spellings resolve to one key and each renamed size owns its own (S605, F-951: sp_alias 'rename_family')",
                  keys["ANKLE BINDER BAMBOO M"] == keys["ANKLE BINDER BAMBOO L"] and len(set(keys.values())) == 3, keys)
        else:
            check("the four spellings resolve to one key (the sp_alias fold; the per-line rule tells M and L apart)", len(set(keys.values())) == 1, keys)
        check("C: the M and L lines are told apart: the M line is carried by a bill LINE named M, the L line by none", bool(h2) and h2.get("name27") == "ANKLE BINDER M BAMBOO" and h48 is None)
        DUMP["s2"] = dict(h2=h2, q2=q2, h48=h48, fb48=fb48, keys=keys)
        c.close()
    section("2  bill 2627, the real case: the M line matched through the rename partner; the L line told apart", s2)

    # ============================================================================================ 7 the replay of S593's 24 lines
    def s7():
        c = conn()
        sw = SW.Spine()
        rows = [r for r in ROWS0.values() if (r["billed_qty"] is None and r["status"] in ("sent", "received") and not r["missing"]) or r["id"] in SEVEN]
        tab, dis, long = [], [], 0
        for r in rows:
            ctx = SF.Ctx(c, sw)
            h = SF.carried(c, sw, L(c, r), ctx)
            packs = None
            if h and h.get("how") in ("c", "d"):
                packs = int(round(float(h.get("qty") or 0) + float(h.get("free") or 0))) if "qty" in h else old_packs(sw, SF, r["item"], h, ctx)
            o = OLD.get("s7", {}).get("table", {}).get(str(r["id"]))
            row = dict(how=(h or {}).get("how"), bill=(h or {}).get("bill"), packs=packs, name27=(h or {}).get("name27"))
            tab.append((r["id"], r["item"], row))
            if len(r["item"].strip()) >= 27:
                long += 1
            if o is not None and (o.get("how"), o.get("bill"), o.get("packs")) != (row["how"], row["bill"], row["packs"]):
                dis.append(r["id"])
            say("   line %-4s %-30s %-22s | OLD %-38s | NEW %s" % (r["id"], r["item"][:30], r["vendor"][:22],
                ("(%s) %s packs %s" % (o["how"], o["bill"], o["packs"])) if (o and o.get("how")) else ("-" if o is None else "none"),
                ("(%s) %s packs %s %s" % (row["how"], row["bill"], row["packs"], (("line %r" % row["name27"]) if row["name27"] else ""))) if row["how"] else "none"))
        n_cd = sum(1 for _i, _n, x in tab if x["how"] in ("c", "d"))
        n_e = sum(1 for _i, _n, x in tab if x["how"] == "e")
        n_0 = sum(1 for _i, _n, x in tab if not x["how"])
        say("   %d lines: %d carried by the own vendor (c / d), %d by another supplier (e), %d no bill; open lines whose spelling is >= 27 characters: %d (R1-C2's reach)" % (len(tab), n_cd, n_e, n_0, long))
        say("   OLD vs NEW disagreements: %s" % (dis if OLD else "(no --old-dump: the OLD side's table is this run's)"))
        by = {i: x for i, _n, x in tab}
        check("C: line 3 (XL) -> None and line 50 (L S BELT XXX: the 07-10 bill's line names the XXL size) -> None under NEW; every other line of S593's seven still carried by its own bill line",
              by[3]["how"] is None and by[50]["how"] is None and all(by[i]["how"] in ("c", "d") and SF._bill(by[i]["bill"]) == SF._bill(ROWS0[i]["billed_bill_no"]) and by[i]["packs"] == int(ROWS0[i]["billed_qty"]) for i in (2, 28, 30, 36, 47)),
              {i: by[i] for i in SEVEN})
        if OLD:
            check("C: the disagreements OLD vs NEW are exactly lines 3 and 50 (rules c / d / e unchanged by date and vendor elsewhere)", sorted(dis) == [3, 50], dis)
        DUMP["s7"] = dict(table={str(i): x for i, _n, x in tab}, n_cd=n_cd, n_e=n_e, n_0=n_0, long=long, dis=dis)
        c.close()
    section("7  REPORT_S593 control 3's lines replayed (the open lines today plus S593's seven; a missing line left out): OLD vs NEW with how / bill / packs", s7)

    # ============================================================================================ 8 the re-judge on the copy, undo
    def s8():
        c = conn()
        st0 = {o: c.execute("SELECT status FROM purchase_order WHERE id=?", (o,)).fetchone()[0] for o in (1, 10, 13, 20)}
        before = line_rows(c, SEVEN)
        aud0 = c.execute("SELECT COALESCE(MAX(id), 0) FROM purchase_audit").fetchone()[0]       # S605 (F-957): the walk's own run's rows only
        c.close()
        r = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "rejudge_s598.py"), "--fin", fin, "--db", dbp, "--json", JSONP], cwd="/tmp", capture_output=True, text=True, timeout=600)
        for l in (r.stdout or "").splitlines():
            say("   | " + l)
        if r.stderr.strip():
            say("   | stderr: " + r.stderr.strip()[-400:])
        c = conn()
        after = line_rows(c, SEVEN)
        st1 = {o: c.execute("SELECT status FROM purchase_order WHERE id=?", (o,)).fetchone()[0] for o in (1, 10, 13, 20)}
        cleared = [i for i in SEVEN if after[i]["billed_qty"] is None and before[i]["billed_qty"] is not None]
        nulls = lambda i: all(after[i][k] is None for k in ("billed_qty", "billed_bill_no", "billed_date", "detected_at", "supplied", "arrived_by", "arrived_at")) and after[i]["short"] == 0   # noqa: E731
        same = [i for i in SEVEN if i not in (3, 50) and after[i] == before[i]]
        aud = {i: c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='line_rejudged_s598' AND ref=? AND id>?", (str(i), aud0)).fetchone()[0] for i in SEVEN}
        say("   cleared %s; untouched %s; audit line_rejudged_s598 rows %s; status before %s after %s" % (cleared, same, aud, st0, st1))
        check("C: rejudge_s598.py on the copy: REJUDGE OK, lines 3 and 50 cleared (billed_*, detected_at, supplied, arrived_by, arrived_at NULL, short 0 -- the system's write), the other five untouched, one audit row each",
              r.returncode == 0 and "REJUDGE OK S598" in (r.stdout or "") and cleared == [3, 50] and nulls(3) and nulls(50) and len(same) == 5 and aud[3] == 1 and aud[50] == 1 and all(aud[i] == 0 for i in same),
              (r.returncode, cleared, same, aud))
        check("purchase_order.status of 1, 10, 13, 20 equal before and after (R1-C7)", st0 == st1, (st0, st1))
        r2 = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "rejudge_s598.py"), "--fin", fin, "--db", dbp, "--json", JSONP + ".second", "--dry"], cwd="/tmp", capture_output=True, text=True, timeout=600)
        check("a second re-judge finds the five agreeing rows only and clears nothing (idempotent)", r2.returncode == 0 and "0 cleared" in (r2.stdout or "") and line_rows(c, SEVEN) == after, (r2.returncode, (r2.stdout or "")[-300:]))
        DUMP["s8"] = dict(before={str(i): before[i] for i in SEVEN}, after={str(i): after[i] for i in SEVEN}, cleared=cleared)
        # undo on a THIRD copy of the finance db (the walk's state after the re-judge must stay for the screens)
        udb = os.path.join(os.path.dirname(dbp), "undo_%s.db" % ("old" if a.expect_red else "new"))
        src = sqlite3.connect(dbp)
        dst = sqlite3.connect(udb)
        src.backup(dst)
        dst.close()
        src.close()
        c.close()
        u = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "undo_s598.py"), "--db", udb, "--json", JSONP], cwd="/tmp", capture_output=True, text=True, timeout=300)
        for l in (u.stdout or "").splitlines()[-4:]:
            say("   | " + l)
        uc = sqlite3.connect(udb)
        uc.row_factory = sqlite3.Row
        back = line_rows(uc, SEVEN)
        check("C: undo_s598.py on a copy restores all seven rows byte-equal from the JSON (the diff printed empty)", u.returncode == 0 and "UNDO OK S598" in (u.stdout or "") and back == before and "the diff after (restored rows against the JSON): empty" in (u.stdout or ""),
              (u.returncode, [i for i in SEVEN if back.get(i) != before.get(i)], (u.stdout or "")[-300:]))
        uc.execute("UPDATE purchase_order_line SET detected_at='2026-10-19T12:00:00' WHERE id=3")
        uc.commit()
        uc.close()
        u2 = subprocess.run([sys.executable, "-B", os.path.join(KITDIR, "undo_s598.py"), "--db", udb, "--json", JSONP], cwd="/tmp", capture_output=True, text=True, timeout=300)
        check("C: a row whose detected_at moved since the JSON is refused by undo and said so (R1-C6); the others already equal", u2.returncode == 0 and "line 3    KNEE SUPPORT HINGED XL         MOVED since the JSON -- refused" in (u2.stdout or "") and "1 refused as moved (3)" in (u2.stdout or ""), (u2.stdout or "")[-400:])
    section("8  the data step on the copy: rejudge_s598.py (the seven rows before / after), idempotent, undo_s598.py", s8)

    # ============================================================================================ 9 the owner's lines
    def s9():
        c = conn()
        lines = [l["text"] for l in SW.arrival_needs_you(c, SW.Spine())]
        for t in lines:
            say("   %s" % t)
        cl_ = {t.split(":")[0]: t for t in lines if "not this size)" in t}
        want = {XXL: ("672", "28-09", "KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L"), ABL: (ROWS0[2]["billed_bill_no"], "07-10", "ANKLE BINDER M BAMBOO"),
                XL: ("672", "28-09", "KNEE SUPPORT HINGED M, KNEE SUPPORT HINGED L"), XXX: ("738", "18-10", "L S BELT M CONT GRAY UNISON, L S BELT XL CONT GRAY UNIS"),
                "KNEE IMMOBILIZER UNISON XL": ("672", "28-09", "KNEE IMMOBILIZER UNISON L")}
        if SW.Spine().q("SELECT 1 FROM sp_alias WHERE kind='rename_family' LIMIT 1"):   # S605 (F-951): after the split day the bills of the sizes are theirs;
            want[XXX] = (ROWS0[2]["billed_bill_no"], "07-10", "L S BELT XXL CONT GRAY UNI")   # the old key's newest family bill is 07-10's (the XXL size)

        def _clause(t):
            m = re.search(r"\(its bill (\S+) of (\d\d-\d\d) carried (.*), not this size\)", t)
            return (m.group(1), m.group(2), sorted(_w(x) for x in m.group(3).split(", "))) if m else None
        ok = set(cl_) == set(want) and all(_clause(cl_[k]) == (b, d, sorted(_w(x) for x in s.split(", "))) for k, (b, d, s) in want.items())
        say("   lines with the clause: %s" % sorted(cl_))
        check("C: after the re-judge the owner's arrival lines carry the clause for XXL, ANKLE BINDER BAMBOO L, XL (new: its line re-opened, order 1 scan-tied), L S BELT XXX (new, bill 738 the newest family bill) and KNEE IMMOBILIZER UNISON XL -- each with the bill and the sizes as Marg printed them",
              ok, dict(got=cl_, want=want))
        check("every arrival line is English with no phone or patient text (a bill number is not a phone number: the '(its bill N' token is set apart)",
              all(re.match(r"^[A-Z0-9 .,'()/&-]+: counted as arrived", t) for t in lines) and not re.search(r"\d{10}", re.sub(r"\(its bill \S+ of", "(its bill", "\n".join(lines))),
              [t[:80] for t in lines if not re.match(r"^[A-Z0-9 .,'()/&-]+: counted as arrived", t)])
        if OLD.get("s9"):
            o = OLD["s9"]["lines"]
            gone = [t for t in o if t not in lines]
            new = [t for t in lines if t not in o]
            base = lambda t: t.split(" (its bill")[0]   # noqa: E731
            say("   against the OLD files: %d line(s) gone, %d new; items added: %s" % (len(gone), len(new), sorted({t.split(":")[0] for t in new} - {t.split(":")[0] for t in o})))
            check("C: the OLD lines all stand (XXL, ANKLE BINDER BAMBOO L among them); the XL and L S BELT XXX lines are added; the only other change is the clause",
                  all(any(base(t) == base(n) for n in lines) for t in o) and {t.split(":")[0] for t in lines} - {t.split(":")[0] for t in o} == {XL, XXX}, (gone, new))
        DUMP["s9"] = dict(lines=lines, clause=cl_)
        c.close()
    section("9  the owner's Needs-you lines after the re-judge (stock_watch.arrival_needs_you)", s9)

    # ============================================================================================ 10 the staff screens
    def s10():
        saved_detect = PO.detect_supplies                     # the screens are read with Marg's clearing held still (its writes are section 3 / the installer's)
        PO.detect_supplies = lambda con: 0
        pages = [("reception", "/finance/porders", True), ("reception", "/finance/porders/api/state", False), ("reception", "/finance/porders/s454/order", False),
                 ("reception", "/finance/porders/s454/maal", False), ("reception", "/finance/porders/s454/order/%s" % ORTHO, False),
                 ("darpan", "/finance/stockmatch", False), ("darpan", "/finance/stockmatch/api/state", False), ("darpan", "/finance/darpan/kal", True), ("darpan", "/finance/darpan/kal/api/day", False)] \
            + [("amir", "/finance/amir", True)] + [("amir", "/finance/amir/step/%d" % n, False) for n in range(1, 8)] \
            + [("shavez", "/finance/reports/aaj", True), ("manoj", "/finance/sanjeevni/api/needs-you", False), ("manoj", "/finance/stock/api/now", False), ("manoj", "/finance/porders/api/state", False)]
        changed, STATE = {}, {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    if isinstance(j, dict):
                        for k in ("you", "at", "generated_at", "built", "date", "yesterday_date", "ours_at", "stored_at", "stored_text", "readiness", "cache", "refresh_ms", "watch", "now", "server_time", "me", "user"):
                            j.pop(k, None)
                    if path == "/finance/porders/api/state":
                        STATE[u] = j
                    body = json.dumps(j, indent=0, sort_keys=True, ensure_ascii=False)
                except ValueError:
                    pass
            else:
                body = "\n".join(text_lines(h))
            lines = [re.sub(r"\d{2}:\d{2}(:\d{2})?( IST| am| pm)?", "HH:MM", l) for l in body.splitlines() if l.strip()]
            open(os.path.join(a.dump, name + ".txt"), "w", encoding="utf-8").write("\n".join(lines))
            if path == "/finance/porders/api/state":
                try:
                    STATE[u + ":masked"] = json.loads("\n".join(lines))   # the same masking as the dump, for the structural compare
                except ValueError:
                    STATE[u + ":masked"] = {}
            check("staff-eye: %s reads %s (%s, %d bytes)" % (u, path, s, len(h)), s == 200, s)
            if a.old_dump and os.path.exists(os.path.join(a.old_dump, name + ".txt")):
                old = open(os.path.join(a.old_dump, name + ".txt"), encoding="utf-8").read().splitlines()
                os_, ns = set(old), set(lines)
                gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                if gone or new:
                    changed[(u, path)] = (gone, new)
                    say("   CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:6]:
                        say("      - %s" % l[:240])
                    for l in new[:6]:
                        say("      + %s" % l[:240])
                else:
                    say("   unchanged on %s for %s" % (path, u))
        PO.detect_supplies = saved_detect
        # the three states: porders._orders (what the Orders card reads; the page lists the 20 newest received orders) and reception's api/state
        c = conn()
        ords = {o["id"]: o for o in PO._orders(c) if o["id"] in (1, 20)}
        c.close()
        o1, o20 = ords.get(1), ords.get(20)
        l3 = next((l for l in (o1 or {}).get("lines", []) if l.get("id") == 3), None)
        l50 = next((l for l in (o20 or {}).get("lines", []) if l.get("id") == 50), None)
        j = STATE.get("reception") or {}
        shown = [o.get("id") for o in (j.get("orders") or {}).get("received", []) + (j.get("orders") or {}).get("open", [])]
        card = sorted((l["item"], l["short"]) for l in (j.get("ortho") or {}).get("lines", []))
        onord = {r["item"]: r["on_order"] for r in j.get("all", []) if r["item"] in (XL, XXX)}
        say("   _orders: order 1 line 3 state %s (open lines %s -> the 'all' button %s); order 20 line 50 state %s (open lines %s); the page's 20 newest received orders hold order 1: %s, order 20: %s; the card %s; on order %s"
            % ((l3 or {}).get("state"), (o1 or {}).get("open_lines"), "shown" if (o1 or {}).get("open_lines") else "hidden", (l50 or {}).get("state"), (o20 or {}).get("open_lines"), 1 in shown, 20 in shown, card, onord))
        check("C: (i) order 1's line 3 reads 'open' again in _orders (reception's Orders card) and the 'all' button is back (open_lines > 0); order 20's line 50 likewise",
              (l3 or {}).get("state") == "open" and (o1 or {}).get("open_lines", 0) > 0 and (l50 or {}).get("state") == "open" and (o20 or {}).get("open_lines", 0) > 0, (l3, l50))
        check("C: (ii) on order: Yuvika KNEE SUPPORT HINGED XL x2 and L S BELT CONT GRAY UNISON XXX x1 are counted again (_on_order)", onord.get(XL) == 2 and onord.get(XXX) == 1, onord)
        check("C: (iii) the orthotic shortage card no longer lists KNEE SUPPORT HINGED XL 2 or L S BELT CONT GRAY UNISON XXX 1", not any(it in (XL, XXX) for it, _n in card), card)
        DUMP["s10"] = dict(l3=l3, l50=l50, card=card, onord=onord, open1=(o1 or {}).get("open_lines"), open20=(o20 or {}).get("open_lines"))
        if a.old_dump:
            # the structural diff of api/state: only lines 3 / 50 and the two items may differ
            bad = {}
            for (u, path), (gone, new) in changed.items():
                if path == "/finance/porders/api/state":
                    try:
                        oj = json.loads("\n".join(open(os.path.join(a.old_dump, "%s_%s.txt" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))), encoding="utf-8").read().splitlines()))
                    except ValueError:
                        bad[(u, path)] = "the old dump is not JSON"
                        continue
                    nj = STATE.get(u + ":masked") or {}
                    probs = []
                    for kind in ("open", "received"):
                        om = {o["id"]: o for o in (oj.get("orders") or {}).get(kind, [])}
                        nm = {o["id"]: o for o in (nj.get("orders") or {}).get(kind, [])}
                        if set(om) != set(nm):
                            probs.append(("orders.%s ids" % kind, sorted(set(om) ^ set(nm))))
                        for oid in om:
                            if oid not in nm:
                                continue
                            ol = {l["id"]: l for l in om[oid].get("lines", [])}
                            nl = {l["id"]: l for l in nm[oid].get("lines", [])}
                            d = [i for i in ol if ol[i] != nl.get(i)]
                            if [i for i in d if i not in (3, 50)]:
                                probs.append(("order %s lines" % oid, [i for i in d if i not in (3, 50)]))
                            rest_o = {k: v for k, v in om[oid].items() if k not in ("lines", "open_lines")}
                            rest_n = {k: v for k, v in nm[oid].items() if k not in ("lines", "open_lines")}
                            if rest_o != rest_n:
                                probs.append(("order %s head" % oid, [k for k in rest_o if rest_o[k] != rest_n.get(k)]))
                            if oid not in (1, 20) and om[oid].get("open_lines") != nm[oid].get("open_lines"):
                                probs.append(("order %s open_lines" % oid, (om[oid].get("open_lines"), nm[oid].get("open_lines"))))
                    for key in ("lines",):
                        ol = {l["item"]: l for l in (oj.get("ortho") or {}).get(key, [])}
                        nl = {l["item"]: l for l in (nj.get("ortho") or {}).get(key, [])}
                        d = [it for it in set(ol) | set(nl) if ol.get(it) != nl.get(it)]
                        if [it for it in d if it not in (XL, XXX)]:
                            probs.append(("ortho.lines", [it for it in d if it not in (XL, XXX)]))
                    oa = {r["item"]: r for r in oj.get("all", [])}
                    na = {r["item"]: r for r in nj.get("all", [])}
                    d = [it for it in set(oa) | set(na) if oa.get(it) != na.get(it)]
                    if [it for it in d if it not in (XL, XXX)]:
                        probs.append(("all", [it for it in d if it not in (XL, XXX)]))
                    for k in set(oj) | set(nj):
                        if k in ("orders", "ortho", "all"):
                            continue
                        if oj.get(k) != nj.get(k):
                            probs.append((k, "differs"))
                    on = (oj.get("ortho") or {}).get("n"), (nj.get("ortho") or {}).get("n")
                    if on[0] is not None and on[0] - on[1] != 2:
                        probs.append(("ortho.n", on))
                    if probs:
                        bad[(u, path)] = probs
                elif path == "/finance/sanjeevni/api/needs-you":   # the arrival lines (the clause, the two added lines) and the shortage card's count
                    ok = all(("counted as arrived" in l) or re.match(r'^"count": \d+,?$', l) or ("not offered for ordering" in l)
                             or re.match(r'^"text": "Orthotic shortages: \d+ items? -- (order not sent|an order is out, more still short)",?$', l) for l in gone + new)
                    if not ok:
                        bad[(u, path)] = (gone[:3], new[:3])
                elif path == "/finance/porders/s454/order":        # the orthotic card's heading count on reception's order page
                    ok = all(re.match(r"^\d+ (dawa|medicines?|items?)$", l) for l in gone + new)
                    if not ok:
                        bad[(u, path)] = (gone[:3], new[:3])
                elif path == "/finance/porders/s454/order/%s" % ORTHO:   # the orthotic card's two lines gone
                    ok = sorted(gone) == sorted(["KNEE SUPPORT HINGED XL 2 nag", "L S BELT CONT GRAY UNISON XXX 1 nag"]) and not new
                    if not ok:
                        bad[(u, path)] = (gone[:3], new[:3])
                elif path == "/finance/darpan/kal/api/day":        # Darpan's day API carries the orthotic card's n and lines
                    ok = all((XL in l) or (XXX in l) or re.match(r'^"(n|short|shelf|keep|on_order|family_shelf|topup)": -?\d+,?$', l)
                             or re.match(r'^("items": \[\]?,?|"approx": (true|false),?|[\[\]{},]+)$', l) for l in gone + new)   # S605 (D749): Darpan's section, its JSON shape
                    if not ok:
                        bad[(u, path)] = (gone[:3], new[:3])
                else:
                    bad[(u, path)] = (gone[:3], new[:3])
            check("C: against the OLD files' dumps the ONLY differences are the three states -- order 1 line 3 and order 20 line 50 open, on order, the orthotic card without XL / XXX (on reception's and the owner's api/state, the card's count and lines on reception's order page and Darpan's day API, the owner's shortage count) -- and the owner's arrival lines; no word differs on any staff page (%d page(s) differ)" % len(changed),
                  bool(changed) and not bad, bad)
    section("10 the staff screens (reception, Darpan, Amir, Shavez) and the owner's pages: the three states, no word changed", s10)

    # ============================================================================================ 11 nothing else moved: the figures
    def s11():
        c = conn()
        sw = SW.Spine()
        ctx = SF.Ctx(c, sw)
        names = sorted({it for it, _p, _s in OR._s470_master(c, PA)} | {it["item"] for it in PO.ortho_items(c)[0]})
        t0 = time.time()
        F = SF.figures(c, sw, names, at=TODAY, ctx=ctx)
        fig = {n: dict(marg=(F[n]["marg"] or {}).get("figure"), taps=(F[n]["marg"] or {}).get("taps"), shelf=F[n]["shelf"].get("shelf"), arrived=F[n]["shelf"].get("arrived"), named=F[n]["shelf"].get("named")) for n in names}
        say("   figures() for %d names in %.1fs" % (len(names), time.time() - t0))
        DUMP["figures"] = fig
        if OLD.get("figures"):
            o = OLD["figures"]
            moved = [n for n in names if n in o and o[n] != fig[n]]
            for n in moved[:12]:
                say("   %-32s OLD %s -> NEW %s" % (n[:32], o[n], fig[n]))
            arr_only = [n for n in moved if o[n].get("shelf") == fig[n].get("shelf") and o[n].get("marg") == fig[n].get("marg")]
            check("C: every counted item's shelf() / marg() figure equals the OLD files' on the copy; the only moves are arrivals (taps / scan_arrivals) of the re-opened lines' families, their shelf figures equal (%d moved: %s)" % (len(moved), moved[:6]),
                  bool(o) and moved == arr_only and all(n in (XL, XXX) or SF.key_of(sw, n, ctx) in (SF.key_of(sw, XL, ctx), SF.key_of(sw, XXX, ctx)) for n in moved), [(n, o[n], fig[n]) for n in moved if n not in arr_only][:5])
        else:
            say("   (no --old-dump: the figures are kept for the NEW run to compare)")
        c.close()
    section("11 nothing else moved: shelf() / marg() / figures() for every master and orthotic item, OLD vs NEW", s11)

    # ============================================================================================ 3-6 the synthetic bills on a SECOND spine copy
    def syn_spine():
        src = sqlite3.connect(SPINE_PATH)
        dst = sqlite3.connect(SYN_PATH)
        src.backup(dst)
        src.close()
        dst.execute("UPDATE sp_meta SET value=? WHERE key='built'", (dt.datetime.now().replace(microsecond=0).isoformat(),))   # S528 R3-9: the copy's build stamp bumped
        dst.commit()
        return dst

    def add_item(sp_, name, k20=None):
        k20 = k20 or re.sub(r"\s+", " ", name.strip())[:20].strip()
        sp_.execute("INSERT OR IGNORE INTO sp_item (k20, name, packing, unit_kind, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (k20, name, "1*1", "pcs", "2026-09-01", TODAY))
        return k20

    def add_bill(sp_, supplier, bill, date, lines):
        sk = SW.supkey(supplier)
        sp_.execute("INSERT OR IGNORE INTO sp_purchase_bill (supplier, supkey, bill, date, amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?)", (supplier, sk, bill, date, 0, "PURCHASE", "w598"))
        for seq, (name27, k20, qty, free) in enumerate(lines, 1):
            sp_.execute("INSERT INTO sp_purchase_line (supkey, bill, date, seq, name27, k20, packing, qty, free, units, amount_p, net_amount_p, direction, source_md5) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (sk, bill, date, seq, name27, k20, "1*1", qty, free, qty + free, 0, 0, "PURCHASE", "w598"))
        sp_.commit()

    def add_order(c, vendor, day, items):
        oid = ins(c, "purchase_order", dict(created_at="%sT09:00:00" % day, created_by="W598", vendor=vendor, status="sent", note="W598 walk", total_p=0,
                                            supplier_norm=PA.supplier_key(vendor), order_src="s454", order_via="call", section="Orthotics"))
        lids = [ins(c, "purchase_order_line", dict(order_id=oid, item=it, packs=p, pack_size=1, units=p, rate_p=0, value_p=0)) for it, p in items]
        c.commit()
        return oid, lids

    def s3456():
        sp_ = syn_spine()
        saved = SW.SPINE_DB
        SW.SPINE_DB = SYN_PATH
        c = conn()
        try:
            day = (today - dt.timedelta(days=5)).isoformat()
            VEND = "W598 VENDOR"
            # ---- 3: two lines of one shared key, NAME A x4 and NAME B x2; two open order lines A and B of one vendor and day
            kA = add_item(sp_, "W598 KNEE SUPPORT HINGED A")
            add_item(sp_, "W598 KNEE SUPPORT HINGED B", kA)
            add_bill(sp_, VEND, "W598-1", day, [("W598 KNEE SUPPORT HINGED A", kA, 4, 0), ("W598 KNEE SUPPORT HINGED B", kA, 2, 0)])
            oid, (la, lb) = add_order(c, VEND, day, [("W598 KNEE SUPPORT HINGED A", 4), ("W598 KNEE SUPPORT HINGED B", 2)])
            sw = SW.Spine()
            assert sw.ok and SW.SPINE_DB == SYN_PATH
            R = line_rows(c, [la, lb])
            hA = SF.carried(c, sw, L(c, R[la]), SF.Ctx(c, sw))
            hB = SF.carried(c, sw, L(c, R[lb]), SF.Ctx(c, sw))
            say("   3: A -> %s; B -> %s" % (hit_text(hA), hit_text(hB)))
            check("C: (3) A is carried by the A line (units 4) and B by the B line (units 2) of ONE bill under one shared key", bool(hA) and bool(hB) and hA.get("units") == 4.0 and hB.get("units") == 2.0 and hA.get("name27", "").endswith(" A") and hB.get("name27", "").endswith(" B"), (hA, hB))
            before = line_rows(c)
            n = PO.detect_supplies(c)
            after = line_rows(c)
            wrote = sorted(i for i in after if (after[i]["billed_qty"], after[i]["supplied"]) != (before[i]["billed_qty"], before[i]["supplied"]))
            say("   3: detect_supplies wrote %d line(s): %s -> A billed %s, B billed %s" % (n, wrote, after[la]["billed_qty"], after[lb]["billed_qty"]))
            check("C: (3) with A's mark written, B is still carried -- rule (b) is per LINE: both marked by the same bill, A 4 packs, B 2 packs",
                  after[la]["billed_qty"] == 4 and after[lb]["billed_qty"] == 2 and after[la]["billed_bill_no"] == after[lb]["billed_bill_no"] == "W598-1", (after[la], after[lb]))
            check("detect_supplies on the copy wrote the walk's own lines only (no live line newly marked: the next tick has nothing new to write)", all(i in (la, lb) for i in wrote), [i for i in wrote if i not in (la, lb)])
            # ---- 4 (i): two open lines of ONE renamed item on one day, one bill line under the partner spelling
            add_bill(sp_, VEND, "W598-2", day, [("ANKLE BINDER M BAMBOO", SF.key_of(sw, "ANKLE BINDER BAMBOO M", SF.Ctx(c, sw)), 1, 0)])
            oid2, (m1, m2) = add_order(c, VEND, day, [("ANKLE BINDER BAMBOO M", 1), ("ANKLE BINDER BAMBOO M", 1)])
            n2 = PO.detect_supplies(c)
            R2 = line_rows(c, [m1, m2])
            h2b = SF.carried(c, sw, L(c, R2[m2]), SF.Ctx(c, sw))
            say("   4(i): first line billed %s by %s; second line -> %s (%d written)" % (R2[m1]["billed_qty"], R2[m1]["billed_bill_no"], hit_text(h2b), n2))
            check("(4i) two open lines of ONE renamed item, one bill line under the partner spelling: the first is marked, the second -> None (never credited twice; green on OLD too, by bill)",
                  R2[m1]["billed_bill_no"] == "W598-2" and R2[m2]["billed_qty"] is None and h2b is None, (R2[m1], R2[m2], h2b))
            # ---- 4 (ii) + 5: a single-member key whose bill spelling differs by Marg's clip (the key fallback)
            kC = add_item(sp_, "W598 CLIPTEST ITEM XYZ")
            add_bill(sp_, VEND, "W598-3", day, [("W598 CLIPTEST ITM", kC, 3, 0)])
            oid3, (c1, c2) = add_order(c, VEND, day, [("W598 CLIPTEST ITEM XYZ", 3), ("W598 CLIPTEST ITEM XYZ", 3)])
            R3 = line_rows(c, [c1, c2])
            hc1 = SF.carried(c, sw, L(c, R3[c1]), SF.Ctx(c, sw))
            say("   5: key %r sib %s; order 'W598 CLIPTEST ITEM XYZ' vs bill name27 'W598 CLIPTEST ITM' -> %s" % (kC, SF._siblings(sw, kC, SF.Ctx(c, sw)) if NEW else "-", hit_text(hc1)))
            check("(5) the key fallback holds for a single-member key: the bill line of a different clip still carries the line (green on OLD and NEW: the rewrite did not narrow single items)",
                  bool(hc1) and hc1.get("bill") == "W598-3" and hc1.get("units") == 3.0, hc1)
            n3 = PO.detect_supplies(c)
            R3 = line_rows(c, [c1, c2])
            hc2 = SF.carried(c, sw, L(c, R3[c2]), SF.Ctx(c, sw))
            say("   4(ii): first line billed %s by %s; second -> %s (%d written)" % (R3[c1]["billed_qty"], R3[c1]["billed_bill_no"], hit_text(hc2), n3))
            check("(4ii) the same with a single-member key and a clipped bill spelling: the first marked, the second -> None (green on OLD too)", R3[c1]["billed_bill_no"] == "W598-3" and R3[c2]["billed_qty"] is None and hc2 is None, (R3[c1], R3[c2], hc2))
            real = []
            ctx = SF.Ctx(c, sw)
            for r in ROWS0.values():
                if not r["billed_bill_no"]:
                    continue
                k = SF.key_of(sw, r["item"], ctx)
                if NEW and SF._siblings(sw, k, ctx):
                    continue
                forms = SF._line_forms(ctx, r["item"]) if NEW else {SW.pad_norm(r["item"][:27]), SW.pad_norm(r["item"])}
                for p in sw.q("SELECT bill, name27 FROM sp_purchase_line WHERE k20=? AND direction='PURCHASE'", k):
                    if SF._bill(p["bill"]) == SF._bill(r["billed_bill_no"]) and SW.pad_norm(p["name27"]) not in forms and SW.pad_norm(p["name27"][:27]) not in forms:
                        real.append((r["id"], r["item"], p["name27"]))
            say("   5: real pairs on the copy (a billed single-member line whose bill spelling is outside its forms): %d %s -- none exist today: the three synthetic pairs above and below stand for them" % (len(real), real[:3]))
            # ---- 6: the two-batch bill
            kT = add_item(sp_, "W598 TWO BATCH ITEM")
            add_bill(sp_, VEND, "W598-4", day, [("W598 TWO BATCH ITEM", kT, 3, 0), ("W598 TWO BATCH ITEM", kT, 2, 1)])
            oid4, (t1,) = add_order(c, VEND, day, [("W598 TWO BATCH ITEM", 6)])
            ht = SF.carried(c, sw, L(c, line_rows(c, [t1])[t1]), SF.Ctx(c, sw))
            n4 = PO.detect_supplies(c)
            Rt = line_rows(c, [t1])[t1]
            say("   6: two batches on one bill -> %s; detect_supplies wrote billed_qty %s (%d)" % (hit_text(ht), Rt["billed_qty"], n4))
            check("C: (6) the same name on two lines of one bill (two batches) -> ONE hit with qty summed (3 + 2 + 1 free = 6 packs), units 6, one billed_qty 6",
                  bool(ht) and ht.get("qty") == 5.0 and ht.get("free") == 1.0 and ht.get("units") == 6.0 and Rt["billed_qty"] == 6 and Rt["billed_bill_no"] == "W598-4", (ht, Rt))
            # the two pairs of 4(i) / 4(ii) under the key fallback with the v1 design would both be carried -- asserted above by the second line's None
            c.execute("UPDATE purchase_order SET status='cancelled' WHERE created_by='W598'")
            c.commit()
        finally:
            SW.SPINE_DB = saved
            sp_.close()
            c.close()
    section("3-6 the synthetic bills on a second spine copy: per-line rule (b); never credited twice; the key fallback; two batches", s3456)

    # ============================================================================================ 12 greps
    def s12():
        sf, sw_, po = SRC["stock_figure.py"], SRC["stock_watch.py"], SRC["porders.py"]
        check("C: def _purchases_of and def _taken_bills are gone from stock_figure.py", "def _purchases_of" not in sf and "def _taken_bills" not in sf)
        check("C: the by-bill lumps are gone: 'GROUP BY supkey, bill, date ORDER BY date DESC' and 'GROUP BY supkey, bill, date ORDER BY date, bill' nowhere in stock_figure.py",
              "GROUP BY supkey, bill, date ORDER BY date DESC" not in sf and "GROUP BY supkey, bill, date ORDER BY date, bill" not in sf)
        check("C: def _line_forms, _siblings, _matches, _purchase_lines_of, _taken_lines, _family_bill once each in stock_figure.py",
              all(sf.count("def %s(" % n) == 1 for n in ("_line_forms", "_siblings", "_matches", "_purchase_lines_of", "_taken_lines", "_family_bill")))
        fns = {n: fn_body(sf, n) for n in ("_purchase_lines_of", "_matches", "_carried", "_family_bill")}
        others = sf
        for b in fns.values():
            others = others.replace(b, "")
        check("C: name27 appears in _purchase_lines_of, _matches, _carried, _family_bill only -- and _matches is the only place a name27 is compared with forms",
              all("name27" in b for b in fns.values()) and "name27" not in others and fns["_matches"].count(" in forms") == 2 and sf.count(" in forms") == 3 and "for f in forms:" in fn_body(sf, "_rename_groups"),
              (["name27" in b for b in fns.values()], sf.count(" in forms"), [l for l in others.splitlines() if "name27" in l][:3]))
        dsb = fn_body(po, "detect_supplies")
        check("C: SUM(qty) is nowhere in porders.detect_supplies; the packs are hit['qty'] + hit['free']", bool(dsb) and "SUM(qty)" not in dsb and 'hit.get("qty")' in dsb and 'hit.get("free")' in dsb)
        any_ = fn_body(sw_, "arrival_needs_you")
        check("C: family_bill in stock_watch.py only inside arrival_needs_you (the clause built once, used by both words lines)",
              sw_.count("family_bill") >= 1 and sw_.count("family_bill") == any_.count("family_bill") and any_.count(", not this size)\" %") == 1 and any_.count(", more)") == 2,
              (sw_.count("family_bill"), any_.count("family_bill"), any_.count(", not this size)\" %"), any_.count(", more)")))
        check("C: KIT = \"S598 in stock_figure.py (or a later kit's: S602 placed it since -- F-957)", bool(re.search(r'KIT = "S(59[89]|6[0-9][0-9])', sf)))
        check("no run of ten digits in the three files or the walk's own output", not re.search(r"\d{10}", sf + sw_ + po + "\n".join(OUT)))
        check("no code of the three files writes to the spine (no INSERT / UPDATE / DELETE on an sp_ table)", not any(re.search(r"(INSERT|UPDATE|DELETE)\s+(INTO\s+|FROM\s+)?sp_", SRC[n]) for n in THREE))
    section("12 the greps (one rule, one place)", s12)

    # ============================================================================================ 13 the spine untouched
    def s13():
        schema1 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
        check("the spine copy's schema is unchanged by the walk", schema0 == schema1, [s for s in schema1 if s not in schema0])
        check("the spine copy's bytes are unchanged by the walk (no write by any code under test; the synthetic bills went to spine_syn)", hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest() == spine_md5_0)
        try:
            r = subprocess.run([sys.executable, "-B", os.path.join(fin, "spine", "selftest_spine.py")], cwd=os.path.join(fin, "spine"), capture_output=True, text=True, timeout=600)
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            check("selftest_spine.py is green on the copy's spine code (%s)" % tail[0][:60], r.returncode == 0 and "SELFTEST OK" in (r.stdout or ""), (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
        except Exception as e:                                 # noqa: BLE001
            check("selftest_spine.py ran", False, str(e)[:200])
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("13 the spine untouched: schema, bytes, selftest green; healthz", s13)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S598: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S598: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S598: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S598: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
