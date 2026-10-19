#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s593.py -- kit S593_ORDER_ENGINE_ONE_SOURCE (19-Oct-2026). Runs on SCRATCH folders and SCRATCH databases only (/tmp).
    python3 -B walk_s593.py --fin <scratch /root/finance with the files under test; spine/spine.db = a backup-API copy of the live spine>
                            --db <COPY of finance.db> --adb <COPY of assets.db> --marg <scratch marg_ingest> --map <DUTY_MAP.json under test>
                            --dump <dir> [--old-dump <dir>] [--expect-red]
    python3 -B walk_s593.py --state --label before|new|after --fin ... --db ... --adb ... --marg ... --map ...   (the install-day state)
The real finance app in one process (the walk's own header session -- its own secret and user store, never the live ones). Its own rows
by key (W593 ...), never by counting; the live rows by key. The spine COPY is never written. No phone number is printed (a run of ten
digits is masked). The sections follow the brief's section 4 (controls 1-13; the staff screens, control 11, are dumped FIRST, before
the walk writes its own rows); --expect-red is the negative control: the same walk on the OLD files, every 'C:' check must be red.
--state prints the install-day state (the brief's section 5). Prints 'WALK OK S593 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import io
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

KIT = "S593_ORDER_ENGINE_ONE_SOURCE"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
SIX = ("order_rules.py", "porders.py", "porders_s454.py", "order_sheet.py", "darpan_kal.py", "spine/spine_read.py")
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


def text_lines(h):
    """The page as text, one line per block (div / p / li / tr / headings / buttons / links) -- the word-for-word compare's grain."""
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
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token)
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB"):
        os.environ.pop(k, None)


def read(fin, name):
    return open(os.path.join(fin, name), encoding="utf-8").read()


def wmd5(tag):
    return "w593" + hashlib.md5(("W593 " + tag).encode()).hexdigest()[4:]


def fn_body(src, name):
    m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|# -{10,}|[A-Z_]+ = ))" % re.escape(name), src, flags=re.S | re.M)
    return m.group(0) if m else ""


def old_days_left(l):
    """darpan_kal._s485_days_left as the OLD files had it (retired by this kit; the walk keeps the arithmetic to compare against)."""
    try:
        oh, pd = float(l.get("on_hand")), float(l.get("per_day"))
    except (TypeError, ValueError):
        return None
    if oh <= 0:
        return 0
    return int(round(oh / pd)) if pd > 0 else None


def old_snap(con, OR, PA):
    """order_rules._s470_snap as the OLD files had it (S470): the newest sp_close row per key by its PRINTED day, the key's figure shared
    equally among the master names under it. (as_on ISO, {norm: row}, missing)."""
    sp = OR._s470_spine()
    try:
        fam = {}
        for item, packing, size in OR._s470_master(con, PA):
            fam.setdefault(sp.key(item), []).append((item, packing, size))
        closes = {key: sp.closing(members[0][0]) for key, members in fam.items()}
        held = [c["as_on"] for c in closes.values() if c]
        latest = max(held)
        snap, missing = {}, []
        for key, members in fam.items():
            c = closes[key]
            if not c or c["as_on"] != latest:
                missing.extend(m[0] for m in members)
                continue
            n = len(members)
            base, rem = divmod(int(round(float(c["units"] or 0))), n)
            for i, (item, packing, size) in enumerate(members):
                snap[PA.norm(item)] = dict(item=item, qty=base + (1 if i < rem else 0), packing=packing, pack_size=size, key=key, n=n)
        return latest, snap, missing
    finally:
        sp.con.close()


def old_rhythm(con, OR, PA, today):
    """order_rules.rhythm as the OLD files had it: 90 days of purchase_bill through pa.EFF_BILL (the tables' NET bill amount)."""
    since = (today - dt.timedelta(days=90)).isoformat()
    out = {}
    rows = con.execute("SELECT b.supplier_norm, MAX(b.supplier), b.bill_date, SUM(b.amount_p) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND "
                       + PA.EFF_BILL + " GROUP BY b.supplier_norm, b.bill_date ORDER BY b.supplier_norm, b.bill_date", (since, today.isoformat())).fetchall()
    for sn, sup, d, amt in rows:
        e = out.setdefault(sn, dict(supplier=sup, dates=[], amount90_p=0, bills90=0))
        e["dates"].append(d)
        e["amount90_p"] += int(amt or 0)
    nb = con.execute("SELECT b.supplier_norm, COUNT(*) FROM purchase_bill b WHERE b.bill_date>=? AND b.bill_date<=? AND " + PA.EFF_BILL + " GROUP BY b.supplier_norm",
                     (since, today.isoformat())).fetchall()
    for sn, n in nb:
        if sn in out:
            out[sn]["bills90"] = int(n)
    minb = OR._int_setting(con, "order.min_bills_for_rhythm")
    import statistics
    for sn, e in out.items():
        ds = sorted(set(e["dates"]))
        gaps = []
        for i in range(len(ds) - 1):
            try:
                gaps.append((dt.date.fromisoformat(ds[i + 1]) - dt.date.fromisoformat(ds[i])).days)
            except ValueError:
                pass
        e["avg_month_p"] = int(e["amount90_p"] / 3.0)
        e["gap"] = statistics.median(gaps) if gaps else None
        e["cadence"] = OR.nearest_cadence(e["gap"]) if (len(ds) >= minb and gaps) else OR.tier_cadence(con, e["avg_month_p"])
    return out


def old_detect(con, IA, PA, item, vendor, created):
    """porders.detect_supplies' table match as the OLD files had it: the vendor's purchase_line rows dated on/after the order day, the item by
    its 20-letter clip and aliases. dict(q, bill, date) or None."""
    keys = {IA.pad_norm(IA.clip(item, IA.PURCHASE_CLIP))} | {IA.pad_norm(IA.clip(f, IA.PURCHASE_CLIP)) for f in IA.aliases_of(con, item)}
    vn = PA.supplier_key(vendor)
    for pl in con.execute("SELECT l.item, l.qty, l.free, l.bill_no, l.bill_date FROM purchase_line l WHERE l.supplier_norm=? AND l.bill_date>=? AND " + PA.EFF_LINE
                          + " ORDER BY l.bill_date, l.id", (vn, str(created or "")[:10])):
        if IA.pad_norm(pl[0]) in keys:
            return dict(q=int(round(float(pl[1] or 0) + float(pl[2] or 0))), bill=str(pl[3] or ""), date=str(pl[4] or ""))
    return None


def billed_rows(con):
    return {int(r[0]): dict(r) for r in con.execute("SELECT l.id, l.item, l.packs, l.billed_qty, l.billed_bill_no, l.billed_date, l.supplied, l.short, l.arrived_by, "
                                                    "o.vendor, o.created_at, o.id AS oid, o.status FROM purchase_order_line l JOIN purchase_order o ON o.id=l.order_id")}


def page_blocks(h):
    """The reception order page as text blocks: the banner, the headings, the cards' names, the done lines (vendor, mark, Call)."""
    out = dict(banner=[], still="", donehead="", whose="", cards=[], done=[], alldone=False)
    m = re.search(r'<div class="ok" id="wagone"><div class="t">(.*?)</div><div>(.*?)</div></div>', h, flags=re.S)
    if m:
        out["banner"] = [text(m.group(1)), text(m.group(2))]
    for key in ("still", "donehead", "whose"):
        m = re.search(r'<div class="mut" id="%s">(.*?)</div>' % key, h, flags=re.S)
        out[key] = text(m.group(1)) if m else ""
    out["cards"] = re.findall(r'<div class="card" data-sn="([^"]*)">', h)
    for m in re.finditer(r'<div class="ln"><div class="t"><div class="a">(.*?)</div><div class="s grn">(.*?)</div></div>(.*?)</div>', h, flags=re.S):
        out["done"].append((text(m.group(1)), text(m.group(2)), "Call" in text(m.group(3))))
    out["alldone"] = ('<div class="ok"><div class="t">' in h) and ("Sab kaam ho gaya" in text(h) or "All work is done" in text(h))
    return out


# ======================================================================================================= the install-day state
def state_look(a, fin, dbp, label):
    app_env(a, dbp, secrets.token_hex(16))
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    con = sqlite3.connect(dbp, timeout=60)
    con.row_factory = sqlite3.Row
    PO.ensure_schema(con)
    new = hasattr(OR, "days_left")
    today = dt.date.today()
    say("STATE %s: files %s; order_rules KIT %s" % (label, "NEW (S593)" if new else "OLD", OR.KIT))
    S = {k: v for k, v in con.execute("SELECT key, value FROM setting WHERE key IN ('order.source','order.engine_source','order.stock_basis','order.in_transit_days',"
                                      "'order.on_order_days','order.pace_days','order.lot_history_days','arrival.bill_grace_days','arrival.back_days','porders.ortho_vendor') ORDER BY key")}
    say("STATE %s: settings %s; order.model exists: %s" % (label, S, bool(con.execute("SELECT 1 FROM setting WHERE key='order.model'").fetchone())))
    t0 = time.time()
    P = OR.plan(con)
    say("STATE %s: plan() in %.1fs -- engine %s, as_on %s, %d suppliers / %d lines, no_closing %d: %s" % (label, time.time() - t0, P["engine"], P["as_on"], len(P["vendors"]),
        sum(len(v["lines"]) for v in P["vendors"].values()), len(P["no_closing"]), P["no_closing"][:6]))
    say("STATE %s: inputs %s" % (label, json.dumps(P.get("inputs"), ensure_ascii=False)))
    _as, snap, _pace, _purch, transit, _ortho = OR._s470_inputs(con, today)
    by = {}
    for s in snap.values():
        k = (s.get("_s470") or {}).get("by", "(old: raw closing)")
        by[k] = by.get(k, 0) + 1
    say("STATE %s: the engine's items %d: counted %d (shelf figure), on Marg's figure %d; closing by %s; transit %d (on the way %d)"
        % (label, len(snap), sum(1 for s in snap.values() if "marg_qty" in s), sum(1 for s in snap.values() if "marg_qty" not in s), by, len(transit), sum(1 for v in transit.values() if "on_way" in v)))
    rows = billed_rows(con)
    opn = [r for r in rows.values() if r["billed_qty"] is None and r["status"] in ("sent", "received")]
    say("STATE %s: open order lines (billed_qty NULL, sent / received): %d" % (label, len(opn)))
    for r in opn:
        say("   line %-4s order %-3s %-30s packs %3s supplied %-4s %-28s created %s" % (r["id"], r["oid"], r["item"][:30], r["packs"], r["supplied"], r["vendor"][:28], str(r["created_at"])[:16]))
    cl = fa.app.test_client(use_cookies=False)
    r = cl.get("/finance/porders/s454/order", base_url=BASE, headers={"X-Clinic-User": "reception", "X-Clinic-Role": "staff"})
    B = page_blocks(r.get_data().decode("utf-8", "replace"))
    say("STATE %s: reception's order page (%s): banner %s; whose '%s'; still '%s'; cards %s; donehead '%s'; done lines %s; all-done %s"
        % (label, r.status_code, B["banner"], B["whose"], B["still"], B["cards"], B["donehead"], B["done"], B["alldone"]))
    rowkeys = set()
    for p in DK._s485_rows(con, today.isoformat()):
        for l in p["lines"]:
            rowkeys |= set(DK._s485_line(p["id"], l).keys())
    if not rowkeys:
        p = con.execute("SELECT id, lines FROM order_proposal WHERE length(lines) > 5 ORDER BY id DESC LIMIT 1").fetchone()
        if p:
            for l in json.loads(p[1] or "[]")[:1]:
                rowkeys |= set(DK._s485_line(p[0], l).keys())
    say("STATE %s: Darpan's tab row keys (api/order lines): %s" % (label, sorted(rowkeys)))
    R = OR.rhythm(con, today)
    say("STATE %s: rhythm(): %d suppliers -- %s" % (label, len(R), "; ".join("%s %s (%d bills)" % (OR._short(e["supplier"] or sn), e["cadence"], e["bills90"]) for sn, e in sorted(R.items()))))
    con.rollback()
    say("STATE OK S593 (%s)" % label)
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
    anywhere = os.environ.get("S593_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.state:
        return state_look(a, fin, dbp, a.label)
    if not a.dump:
        ap.error("--dump is needed for the walk")
    os.makedirs(a.dump, exist_ok=True)
    say("-- S593 walk on the %s: %s . db %s . map %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp), a.map))
    token = secrets.token_hex(16)
    app_env(a, dbp, token)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_rules as OR                                  # noqa: E402
    import porders as PO                                      # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    import stock_figure as SF                                 # noqa: E402
    import stock_watch as SW                                  # noqa: E402
    import shelf_figure as SH                                 # noqa: E402
    import purchase_app as PA                                 # noqa: E402
    import item_alias as IA                                   # noqa: E402
    for m in (OR, PO, PS, OS, DK, SF, SW, SH, PA, IA):
        assert m.__file__.startswith(fin), m.__file__
    NEW = hasattr(OR, "days_left")
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; order_rules KIT %s (%s); stock_figure v%s %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", OR.KIT, "NEW" if NEW else "OLD", SF.VERSION, SF.KIT))
    cl = fa.app.test_client(use_cookies=False)
    DUMP = {}
    SPINE_PATH = os.path.join(fin, "spine", "spine.db")
    schema0 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
    spine_md5_0 = hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest()
    SRC = {n: read(fin, n) for n in SIX}
    MAP = json.load(open(a.map, encoding="utf-8"))
    today = dt.date.today()
    TODAY = today.isoformat()

    def GET(u, path, follow=False):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, follow_redirects=follow)
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]}, json=body)
        try:
            j = r.get_json()
        except Exception:                                     # noqa: BLE001
            j = None
        return r.status_code, (j if isinstance(j, dict) else {})

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def set_source(c, v):
        c.execute("INSERT INTO setting (key, value, note) VALUES ('order.source', ?, 'W593 walk') ON CONFLICT(key) DO UPDATE SET value=excluded.value", (v,))
        c.commit()

    c_ = sqlite3.connect(dbp, timeout=60)
    PO.ensure_schema(c_)
    OR.ensure(c_)
    c_.commit()
    c_.close()
    sw0 = SW.Spine()
    assert sw0.ok and SW.SPINE_DB == SPINE_PATH, (sw0.ok, SW.SPINE_DB)
    OLD = {}
    if a.old_dump and os.path.exists(os.path.join(a.old_dump, "walk.json")):
        OLD = json.load(open(os.path.join(a.old_dump, "walk.json")))
    SPTYPES = {}

    def wrap(mod, name, idx):
        orig = getattr(mod, name)

        def w(*args, **kw):
            sp_ = kw.get("sp") if "sp" in kw else (args[idx] if len(args) > idx else None)
            SPTYPES.setdefault(name, set()).add("%s.%s" % (type(sp_).__module__, type(sp_).__name__))
            return orig(*args, **kw)
        setattr(mod, name, w)
    for nm, idx in (("marg", 1), ("carried", 1), ("scan_arrivals", 1), ("capture_at", 0), ("shelf", 1)):
        wrap(SF, nm, idx)
    c0 = conn()
    SRC0 = OS.source(c0)
    ORTHO = OR._ortho_norm(c0)
    say("   today %s; order.source %s; the orthotic vendor %s; stock master %d names" % (TODAY, SRC0, ORTHO, len(OR._s470_master(c0, PA))))
    check("the walk starts with order.source = marg_sheet (the live setting; nothing here reaches reception's list)", SRC0 == "marg_sheet", SRC0)
    BILLED0 = billed_rows(c0)                                 # every order line's billed_* as the copy came (before any code under test wrote)
    c0.close()
    T = {}

    # ============================================================================================ 11 (first) the staff screens word for word
    def s11():
        c = conn()
        t0 = time.time()
        P = OR.plan(c)                                        # the owner's api/day serves the last plan's inputs note (NEW) -- made here first
        T["plan"] = time.time() - t0
        DUMP["plan_seconds"] = T["plan"]
        es = OS.entries(c)
        pend = [e for e in es if e["state"] != "in_line"]
        sn0 = pend[0]["sn"] if pend else ORTHO
        c.close()
        saved_detect = PO.detect_supplies                     # the WORDS are compared with Marg's clearing held still: its writes (section 3) are data, shown there
        PO.detect_supplies = lambda con: 0
        pages = [("reception", "/finance/porders", True), ("reception", "/finance/porders/s454/order", False), ("reception", "/finance/porders/s454/maal", False),
                 ("reception", "/finance/porders/s454/order/%s" % sn0, False), ("darpan", "/finance/darpan/kal", True), ("darpan", "/finance/darpan/kal/api/order", False),
                 ("darpan", "/finance/darpan/kal/api/day", False)] + [("amir", "/finance/amir/step/%d" % n, False) for n in range(1, 8)] + [
                 ("shavez", "/finance/reports/aaj", True), ("manoj", "/finance/porders/api/day", False), ("manoj", "/finance/sanjeevni/api/needs-you", False)]
        changed = {}
        for u, path, follow in pages:
            s, h = GET(u, path, follow)
            name = "%s_%s" % (u, re.sub(r"[^a-z0-9]+", "_", path.lower()).strip("_"))
            body = h
            if "/api/" in path:
                try:
                    j = json.loads(h)
                    for k in ("you", "at", "generated_at", "built", "date", "yesterday_date"):
                        j.pop(k, None) if isinstance(j, dict) else None
                    if path == "/finance/porders/api/day" and isinstance(j, dict):
                        inp = j.pop("inputs", None)           # the one key the owner's api/day gains (S593); the rest must read as before
                        check("the owner's api/day carries the inputs note (a dict with the capture)%s" % ("" if NEW else " -- absent on the OLD files, as expected"),
                              (isinstance(inp, dict) and bool((inp.get("capture") or {}).get("md5"))) == NEW, inp)
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
                os_, ns = set(old), set(lines)
                gone, new = [l for l in old if l not in ns], [l for l in lines if l not in os_]
                if gone or new:
                    changed[(u, path)] = (gone, new)
                    say("   WORDS CHANGED on %s for %s: %d line(s) gone, %d new" % (path, u, len(gone), len(new)))
                    for l in gone[:4]:
                        say("      - %s" % l[:300])
                    for l in new[:4]:
                        say("      + %s" % l[:300])
                else:
                    say("   words unchanged on %s for %s" % (path, u))
        PO.detect_supplies = saved_detect
        if a.old_dump:
            bad = {}
            for (u, path), (gone, new) in changed.items():
                if u == "darpan" and path == "/finance/darpan/kal/api/order":
                    ok = all(('"why"' in l or '"cover_days"' in l or l.strip() in ("[", "]", "],", "{", "}", "},")) for l in gone) and not new   # why / cover_days gone
                elif u == "reception" and path == "/finance/porders/s454/order":
                    # F-916: a done line ('✓ ...') of a supplier with a card gone, the 'Ho chuke' count moved with it, a date on an earlier day's line
                    ok = all((l.startswith("Ho chuke") or l.startswith("Done:") or l.startswith("✓") or l.startswith("Baaki ") or l.startswith("Show the other")) for l in gone + new)
                else:
                    ok = False                                 # the owner's api/day: its one new key is set apart above; anything else differing is a fault
                if not ok:
                    bad[(u, path)] = (gone[:3], new[:3])
            check("no staff screen changed its words beyond F-916's two (the filtered done block, an earlier day's date); the owner's api/day gains inputs; Darpan's rows lose why / cover_days (%d page(s) differ)"
                  % len(changed), not bad, bad)
    section("11 the staff screens word for word (dumped before the walk writes its own rows)", s11)

    # ============================================================================================ 1 the stock base, one function
    def s1():
        c = conn()
        P = OR.plan(c)
        inp = P.get("inputs")
        check("C: plan() runs on the spine (engine == 'spine') and carries inputs (the capture, the sale reach, the counts)",
              P["engine"] == "spine" and isinstance(inp, dict) and bool((inp.get("capture") or {}).get("md5")), (P["engine"], inp))
        say("   plan: engine %s, as_on %s, %d suppliers / %d lines, no_closing %d; inputs %s" % (P["engine"], P["as_on"], len(P["vendors"]), sum(len(v["lines"]) for v in P["vendors"].values()), len(P["no_closing"]), json.dumps(inp, ensure_ascii=False)))
        DUMP["plan_lines"] = sorted((vn, l["item"], l["qty"], l["on_hand"]) for vn, v in P["vendors"].items() for l in v["lines"])
        as_on, snap, pace, purch, transit, ortho = OR._s470_inputs(c, today)
        DUMP["as_on"] = as_on
        sw = SW.Spine()
        ctx = SF.Ctx(c, sw)
        master = OR._s470_master(c, PA)
        bad, want_u, absent, bykey, nomarg, arr_items = [], {}, [], [], [], []
        for item, packing, size in master:
            k = PA.norm(item)
            s = snap.get(k)
            m = SF.marg(c, sw, item, at=TODAY, ctx=ctx)
            if m is None:
                nomarg.append(item)
                if s is not None and NEW:
                    bad.append((item, "no figure yet in the snapshot"))
                continue
            scans = float(SF.scan_arrivals(c, sw, item, m["closing"]["stamp_iso"], ctx) or 0)
            taps = float(m.get("taps") or 0)
            want = max(0, int(round(float(m["figure"]) + taps + scans)))
            want_u[k] = (want, float(m["figure"]), taps, scans, m["closing"]["end_day"], m["closing"]["by"])
            if taps or scans:
                arr_items.append((item, float(m["figure"]), taps, scans))
            by = m["closing"]["by"]
            if by == "absent":
                absent.append(item)
            elif by == "key":
                bykey.append(item)
            if s is None:
                bad.append((item, "not in the snapshot"))
                continue
            if "marg_qty" in s:
                if int(s["marg_qty"]) != int(round(float(m["figure"]))):
                    bad.append((item, "marg_qty", s["marg_qty"], "marg", round(float(m["figure"]), 2)))
            elif int(s["qty"]) != want:
                bad.append((item, "qty", s["qty"], "want", want, "figure", round(float(m["figure"]), 2), "taps", taps, "scans", scans))
        counted = [s["item"] for s in snap.values() if "marg_qty" in s]
        F = SH.figures(c, sp=sw, items=counted, ctx=ctx)
        badsh = [(it, snap[PA.norm(it)]["qty"], (F.get(it) or {}).get("shelf")) for it in counted if (F.get(it) or {}).get("shelf") is not None and int(snap[PA.norm(it)]["qty"]) != int(F[it]["shelf"])]
        check("C: every uncounted item's qty == int(round(marg + taps + scans)) from a direct stock_figure call with stock_watch.Spine(); every counted item's marg_qty == Marg's pure figure",
              not bad and NEW, (len(bad), bad[:6]))
        check("every counted item's qty == shelf_figure.figures(...)['shelf'] (%d counted)" % len(counted), not badsh, badsh[:6])
        say("   %d master names: %d counted (shelf figure), %d on Marg's figure, %d with no figure (no capture holds the key): %s" % (len(master), len(counted), len(snap) - len(counted), len(nomarg), nomarg[:6]))
        # OLD _s470_snap: the raw printed-day closing, split equally
        try:
            latest_old, osnap, omiss = old_snap(c, OR, PA)
        except Exception as e:                                 # noqa: BLE001
            latest_old, osnap, omiss = "?", {}, []
            say("   the OLD _s470_snap could not be replayed: %s" % str(e)[:120])
        moved = []
        for k, s in snap.items():
            if "marg_qty" in s:
                continue
            o = osnap.get(k)
            if o is not None and int(o["qty"]) != int(s["qty"]):
                moved.append((s["item"], int(o["qty"]), int(s["qty"]), want_u.get(k, (None, None, None, None, "?"))[4]))
        say("   OLD _s470_snap: printed day %s, %d items, %d missing; NEW as_on %s. Uncounted items whose figure MOVED old -> new: %d" % (latest_old, len(osnap), len(omiss), as_on, len(moved)))
        for it, o, n_, ed in moved[:10]:
            say("      %-32s old %5d -> new %5d  (the capture's end_day %s)" % (it[:32], o, n_, ed))
        mx = max([abs(n_ - o) for _it, o, n_, _ed in moved] or [0])
        plan_items = {l["item"] for v in P["vendors"].values() for l in v["lines"]}
        abs_lines = sorted(set(absent) & plan_items)
        say("   items moved from 'missing' to qty 0 (by='absent'): %d (%s); the plan lines they produce: %d %s; items read by the whole key (by='key'): %d %s"
            % (len(absent), absent[:6], len(abs_lines), abs_lines[:6], len(bykey), bykey[:6]))
        say("   the largest move of an uncounted item's figure: %d units" % mx)
        DUMP["s1"] = dict(moved=len(moved), max_move=mx, absent=len(absent), absent_lines=len(abs_lines), bykey=len(bykey), counted=len(counted), nomarg=len(nomarg), as_on=as_on, old_as_on=latest_old)
        check("C: 'sp.closing(' is gone from order_rules.py (the engine's own closing read)", "sp.closing(" not in SRC["order_rules.py"])
        DUMP["arr_items"] = arr_items
        DUMP["transit"] = {k: dict(units=v["units"], on_way="on_way" in v) for k, v in transit.items()}
        c.close()
    section("1  the stock base, one function -- and the engine really on the spine (R1-B1, C1-C6)", s1)

    # ============================================================================================ 2 no second arrivals rule
    def s2():
        tr = DUMP.get("transit") or {}
        check("C: _s470_arrivals is gone from order_rules.py and transit holds only on-the-way (sent, unanswered) entries",
              "def _s470_arrivals" not in SRC["order_rules.py"] and "_s470_arrivals(" not in SRC["order_rules.py"] and all(v["on_way"] for v in tr.values()), (len(tr), [k for k, v in tr.items() if not v["on_way"]][:5]))
        say("   transit (on the way): %s" % {k: v["units"] for k, v in tr.items()})
        arr = DUMP.get("arr_items") or []
        say("   items with a tapped or scan-tied arrival since their closing's capture that the spine does not carry yet: %d" % len(arr))
        for it, fig, taps, scans in arr[:12]:
            say("      %-32s Marg %7.1f  taps %6.1f  scans %6.1f -> the engine's figure %d" % (it[:32], fig, taps, scans, max(0, int(round(fig + taps + scans)))))
    section("2  no second arrivals rule: the one function's figure carries the arrivals", s2)

    # ============================================================================================ 3 detect_supplies on the copy
    def s3():
        c = conn()
        sw = SW.Spine()
        before = billed_rows(c)
        check("no order line was marked billed by a page read so far (the words were compared with Marg's clearing held still)",
              all((before[i]["billed_qty"], before[i]["supplied"]) == (BILLED0[i]["billed_qty"], BILLED0[i]["supplied"]) for i in BILLED0))
        opn = [r for r in before.values() if r["billed_qty"] is None and r["status"] in ("sent", "received")]
        ortho0 = sorted((l["item"], l["qty"]) for e in OS.entries(c) if e["sn"] == ORTHO for l in e["lines"])
        arr0 = [l["text"] for l in SW.arrival_needs_you(c, sw)]
        say("   open order lines on the copy: %d -- OLD (the tables' match) vs NEW (carried(): rule, bill, date, PACKS):" % len(opn))
        side = {}
        for r in opn:
            ctx = SF.Ctx(c, sw)
            o = old_detect(c, IA, PA, r["item"], r["vendor"], r["created_at"])
            hit = SF.carried(c, sw, dict(line_id=r["id"], item=r["item"], vendor=r["vendor"], order_at=r["created_at"], billed_bill_no=None), ctx) if hasattr(SF, "carried") else None
            packs = None
            if hit and hit.get("how") in ("c", "d"):
                k20 = SF.key_of(sw, r["item"], ctx)
                pr = sw.q("SELECT COALESCE(SUM(qty),0) AS q, COALESCE(SUM(free),0) AS f FROM sp_purchase_line WHERE k20=? AND supkey=? AND bill=? AND date=? AND direction='PURCHASE'",
                          k20, hit["supkey"], hit["bill"], hit["date"])
                packs = int(round(float(pr[0]["q"] or 0) + float(pr[0]["f"] or 0))) if pr else 0
            side[r["id"]] = dict(old=o, hit=hit, packs=packs)
            say("      line %-4s %-30s %-24s created %s | OLD %-34s | NEW %s" % (r["id"], r["item"][:30], r["vendor"][:24], str(r["created_at"])[:10],
                ("bill %s of %s, %s packs" % (o["bill"], o["date"], o["q"])) if o else "no match",
                ("(%s) bill %s of %s, %s packs%s" % (hit["how"], hit["bill"], hit["date"], packs, " -- dated BEFORE the order day (rule c)" if hit["how"] == "c" else "")) if (hit and hit.get("how") in ("c", "d"))
                else (("(%s) another supplier's bill -- stock only, never this line" % hit["how"]) if hit else "no carrying bill")))
        # (i) the walk's own line, and the spine made unreadable: nothing written, one stderr line
        pl = c.execute("SELECT l.supplier_norm, l.item, l.bill_no, l.bill_date, l.qty, l.free FROM purchase_line l WHERE l.bill_date>=? AND l.direction='PURCHASE' AND " + PA.EFF_LINE
                       + " AND EXISTS (SELECT 1 FROM purchase_bill b WHERE b.supplier_norm=l.supplier_norm AND b.bill_no=l.bill_no) ORDER BY l.bill_date DESC, l.id LIMIT 1",
                       ((today - dt.timedelta(days=12)).isoformat(),)).fetchone()
        check("a recent table purchase line exists on the copy for the walk's own order (the old rule's food)", pl is not None)
        vend = c.execute("SELECT supplier FROM purchase_bill WHERE supplier_norm=? ORDER BY id DESC LIMIT 1", (pl[0],)).fetchone()[0] if pl else "W593 VENDOR"
        oid_a = ins(c, "purchase_order", dict(created_at="%sT09:00:00" % pl[3], created_by="W593", vendor=vend, status="sent", note="W593 walk", total_p=0, supplier_norm=pl[0], order_src="s454", order_via="call", section="Medicines"))
        lid_a = ins(c, "purchase_order_line", dict(order_id=oid_a, item=pl[1], packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
        c.commit()
        saved, SW.SPINE_DB = SW.SPINE_DB, os.path.join(os.path.dirname(dbp), "no_such_spine.db")
        err = io.StringIO()
        old_err, sys.stderr = sys.stderr, err
        try:
            n0 = PO.detect_supplies(c)
        finally:
            sys.stderr = old_err
            SW.SPINE_DB = saved
        after0 = billed_rows(c)
        wrote0 = [i for i in after0 if (after0[i]["billed_qty"], after0[i]["supplied"]) != ((before.get(i) or {}).get("billed_qty"), (before.get(i) or {}).get("supplied")) and i != lid_a] + ([lid_a] if after0[lid_a]["billed_qty"] is not None else [])
        check("C: with the spine unreadable detect_supplies returns 0, writes nothing and says so once on stderr", n0 == 0 and not wrote0 and err.getvalue().count("spine could not be read") == 1,
              (n0, wrote0[:5], err.getvalue()[:200]))
        # (ii) the real run on the copy
        n1 = PO.detect_supplies(c)
        after1 = billed_rows(c)
        newly = {i: after1[i] for i in after1 if after1[i]["billed_qty"] is not None and (before.get(i) or {}).get("billed_qty") is None and i != lid_a}
        say("   detect_supplies on the copy wrote %d line(s); newly billed (live lines): %d" % (n1, len(newly)))
        okp, same_bill_diff, by_e = True, [], []
        for i, r in sorted(newly.items()):
            s_ = side.get(i) or {}
            hit, packs, o = s_.get("hit"), s_.get("packs"), s_.get("old")
            how = (hit or {}).get("how")
            say("      line %-4s %-30s billed %4s by bill %-14s of %s  supplied %-4s short %s  rule %s" % (i, r["item"][:30], r["billed_qty"], r["billed_bill_no"], r["billed_date"], r["supplied"], r["short"], how or "(old rule)"))
            if NEW:
                if hit is None or how not in ("c", "d") or int(r["billed_qty"]) != int(packs or -1) or r["billed_bill_no"] != hit["bill"]:
                    okp = False
                if hit and SW.supkey(r["vendor"]) != hit["supkey"]:
                    by_e.append(i)
                if o and o["bill"] and SF._bill(o["bill"]) == SF._bill(hit["bill"]) and int(o["q"]) != int(r["billed_qty"]):
                    same_bill_diff.append((i, o["q"], r["billed_qty"]))
        check("C: every newly billed line carries the bill carried() chose by rule (c) or (d), with the PACKS of that bill's own line for the key (never units)", NEW and okp and bool(newly or not opn), (okp, len(newly)))
        check("no line is marked billed by a rule-(e) bill (another supplier's)", not by_e, by_e)
        check("where OLD and NEW hit the same bill the packs agree", not same_bill_diff, same_bill_diff)
        differ = [i for i in opn and [r["id"] for r in opn] if ((side[i]["old"] or {}).get("bill") or "") != (((side[i]["hit"] or {}).get("bill") or "") if (side[i]["hit"] or {}).get("how") in ("c", "d") else "")]
        say("   lines where OLD and NEW disagree (bill or none): %d of %d -- %s" % (len(differ), len(opn), differ[:12]))
        say("   rule-(c) hits (a bill dated before the order day; billed_date < created_at, lead_learned clamps it at 0): %s"
            % [(i, side[i]["hit"]["bill"], side[i]["hit"]["date"]) for i in side if (side[i]["hit"] or {}).get("how") == "c"])
        ortho1 = sorted((l["item"], l["qty"]) for e in OS.entries(c) if e["sn"] == ORTHO for l in e["lines"])
        arr1 = [l["text"] for l in SW.arrival_needs_you(c, SW.Spine())]
        say("   what the writes change on the screens -- the orthotic card (S403's shortage, keep - shelf - on order): before %s; after %s" % (ortho0, ortho1))
        say("   the owner's arrival lines (stock_figure.arrivals_open, rule b after the writes): before %d %s; after %d %s" % (len(arr0), arr0, len(arr1), arr1))
        fam = {}
        for i, r in newly.items():
            fam.setdefault((r["billed_bill_no"], r["billed_date"]), []).append((i, r["item"], r["packs"], r["billed_qty"]))
        shared = {k: v for k, v in fam.items() if len(v) > 1 or any(int(x[3] or 0) > int(x[2] or 0) for x in v)}
        say("   bills whose packs exceed a line's own order, or that answer two lines (a size family under one 20-letter key): %s" % (shared or "none"))
        DUMP["s3"] = dict(newly={str(i): dict(item=r["item"], packs=r["packs"], billed=r["billed_qty"], bill=r["billed_bill_no"], date=r["billed_date"], supplied=r["supplied"], short=r["short"],
                                              rule=((side.get(i) or {}).get("hit") or {}).get("how")) for i, r in newly.items()},
                          differ=differ, open=len(opn), ortho_before=ortho0, ortho_after=ortho1, arrival_lines_before=arr0, arrival_lines_after=arr1)
        # (iii) idempotence within one run: two open lines of one key from one vendor are carried by TWO bills (R1-C10); a second run writes nothing
        od = (today - dt.timedelta(days=20)).isoformat()
        pair = sw.q("SELECT l.k20 AS k, l.supkey AS s, COUNT(DISTINCT l.bill || '/' || l.date) AS n, MIN(l.date) AS d0, MAX(b.supplier) AS sup FROM sp_purchase_line l "
                    "LEFT JOIN sp_purchase_bill b ON b.supkey=l.supkey AND b.bill=l.bill AND b.date=l.date WHERE l.direction='PURCHASE' AND l.date>=? AND l.qty>0 "
                    "GROUP BY l.k20, l.supkey HAVING n>=2 ORDER BY n DESC, l.k20 LIMIT 1", od)
        check("the spine copy has a key with two PURCHASE bills from one supplier in the last 20 days (the idempotence case's food)", bool(pair), pair)
        if pair:
            k20, supk, sup = pair[0]["k"], pair[0]["s"], pair[0]["sup"]
            nm = (sw.q("SELECT name FROM sp_close_name WHERE k20=? ORDER BY name LIMIT 1", k20) or sw.q("SELECT name FROM sp_item WHERE k20=? ORDER BY name LIMIT 1", k20) or [{"name": k20}])[0]["name"]
            vn = sup if SW.supkey(sup) == supk else supk
            oid_b = ins(c, "purchase_order", dict(created_at="%sT09:00:00" % pair[0]["d0"], created_by="W593", vendor=vn, status="sent", note="W593 walk pair", total_p=0,
                                                   supplier_norm=PA.supplier_key(vn), order_src="s454", order_via="call", section="Medicines"))
            l1 = ins(c, "purchase_order_line", dict(order_id=oid_b, item=nm, packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
            l2 = ins(c, "purchase_order_line", dict(order_id=oid_b, item=nm, packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
            c.commit()
            n2 = PO.detect_supplies(c)
            r1 = c.execute("SELECT billed_bill_no, billed_date, billed_qty FROM purchase_order_line WHERE id=?", (l1,)).fetchone()
            r2 = c.execute("SELECT billed_bill_no, billed_date, billed_qty FROM purchase_order_line WHERE id=?", (l2,)).fetchone()
            say("   the pair (%s from %s, order of %s): line %s -> %s; line %s -> %s (%d written)" % (nm, vn, pair[0]["d0"], l1, tuple(r1), l2, tuple(r2), n2))
            check("C: two open lines of one key from one vendor are carried by TWO different bills in one run (a fresh Ctx per row)",
                  bool(r1[0]) and bool(r2[0]) and (r1[0], r1[1]) != (r2[0], r2[1]), (tuple(r1), tuple(r2)))
            snap_b = billed_rows(c)
            n3 = PO.detect_supplies(c)
            check("a second run writes nothing (idempotent): %d" % n3, n3 == 0 and billed_rows(c) == snap_b, n3)
        c.close()
    section("3  detect_supplies asks the one rule: old vs new side by side; packs; no rule-(e) write; idempotence; the spine unread", s3)

    # ============================================================================================ 4 the rhythm from the spine
    def s4():
        c = conn()
        R = OR.rhythm(c, today)
        O = old_rhythm(c, OR, PA, today)
        moved_c, diffs = [], []
        for sn in sorted(set(R) | set(O)):
            n_, o = R.get(sn), O.get(sn)
            if n_ is None or o is None:
                diffs.append((sn, "old only" if n_ is None else "new only", (o or n_)["bills90"], (o or n_)["cadence"]))
                continue
            if (n_["bills90"], n_["gap"], n_["amount90_p"]) != (o["bills90"], o["gap"], o["amount90_p"]):
                diffs.append((sn, "bills90 %s->%s" % (o["bills90"], n_["bills90"]), "gap %s->%s" % (o["gap"], n_["gap"]), "amount90_p %s->%s" % (o["amount90_p"], n_["amount90_p"])))
            if n_["cadence"] != o["cadence"]:
                moved_c.append((sn, o["cadence"], n_["cadence"]))
        say("   rhythm(): %d suppliers NEW vs %d OLD (purchase_bill, NET amounts); differences: %d" % (len(R), len(O), len(diffs)))
        for d in diffs[:30]:
            say("      %s" % (d,))
        say("   suppliers whose CADENCE moved: %s" % (moved_c or "none"))
        body = fn_body(SRC["order_rules.py"], "rhythm")
        check("C: rhythm() reads no purchase_bill (none between 'def rhythm' and the next def) and the spine's purchases_by_supplier", body and "purchase_bill" not in body and "purchases_by_supplier(" in body)
        check("C: def purchases_by_supplier occurs once in spine_read.py and is a SELECT", SRC["spine/spine_read.py"].count("def purchases_by_supplier(") == 1 and "FROM sp_purchase_bill b WHERE b.direction='PURCHASE'" in SRC["spine/spine_read.py"])
        check("the three other purchase_bill reads of order_rules.py stay (rung 5's; SEEN)", SRC["order_rules.py"].count("FROM purchase_bill") >= 2)
        DUMP["s4"] = dict(moved=moved_c, diffs=diffs[:40], n_new=len(R), n_old=len(O))
        c.close()
    section("4  the rhythm from the spine (old vs new per supplier; the money basis named)", s4)

    # ============================================================================================ 5 F-738
    def s5():
        c = conn()
        set_source(c, "darpan")
        rows = [dict(r) for r in c.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 AND supplier_norm<>? ORDER BY supplier_norm", (ORTHO,))]
        vend = next((r for r in rows if PA._wa_digits(PA.book_number(c, r["supplier"], "order"))), None)
        check("a supplier with an order WhatsApp number exists on the copy (the send's food)", vend is not None)
        item = OR._s470_master(c, PA)[0][0]
        lines = [dict(item=item, on_hand=10, qty=10, unit="strip", pack_size=10, packing="1*10", rate_p=1000, per_day=1.0, cover_after=20.0, value_p=10000, confirm=False, why=["W593 walk"])]
        pid = ins(c, "order_proposal", dict(day=TODAY, supplier_norm=vend["supplier_norm"], vendor=vend["supplier"], kind="fixed", status="open", lines=json.dumps(lines), total_p=10000, reason="W593 walk", prepared_at=OR.now_iso()))
        c.commit()
        with fa.app.test_request_context(base_url=BASE):      # _staff_send answers with jsonify: an app context
            body, code = OR.send_proposal(c, {"user": "W593"}, pid, None)
        check("C: on order.source = darpan an OPEN proposal is refused by send_proposal: 409 not_confirmed", code == 409 and body.get("error") == "not_confirmed", (code, body))
        s_, j = POST("darpan", "/finance/porders/api/send_med", {"vendor": vend["supplier"]})   # a sender of his own (the shared reception login would first ask who works, S441)
        check("C: on darpan api/send_med is refused outright: 409 not_confirmed", s_ == 409 and j.get("error") == "not_confirmed", (s_, j))
        c.execute("UPDATE order_proposal SET status='darpan_ok' WHERE id=?", (pid,))
        c.commit()
        with fa.app.test_request_context(base_url=BASE):
            body2, code2 = OR.send_proposal(c, {"user": "W593"}, pid, None)
        check("a darpan_ok proposal still goes out through send_proposal (200, an order made)%s" % ("" if NEW else " -- on the OLD files the open one already went: 'already'"),
              (code2 == 200 and body2.get("ok") and body2.get("order_id")) or (not NEW and body2.get("error") == "already"), (code2, body2))
        c.execute("UPDATE purchase_order SET note='W593 walk' WHERE id=?", (body2.get("order_id") or -1,))
        set_source(c, "marg_sheet")
        check("order.source restored on the copy", OS.source(c) == "marg_sheet")
        c.close()
    section("5  F-738: an open proposal never goes out on darpan; send_med refused; darpan_ok still sends", s5)

    # ============================================================================================ 6 days_left, three kinds of row
    def s6():
        c = conn()
        P = OR.plan(c)
        rows = [l for v in P["vendors"].values() for l in v["lines"]]
        bad = [(l["item"], l.get("days_left"), old_days_left(l)) for l in rows if l.get("days_left", "MISSING") != old_days_left(l)]
        check("C: (i) every _line_out row carries days_left == the OLD _s485_days_left arithmetic on the same row (%d lines)" % len(rows), bool(rows) and not bad and all("days_left" in l for l in rows), bad[:6])
        p = c.execute("SELECT id, lines FROM order_proposal WHERE length(lines) > 5 AND reason NOT LIKE 'W593%' ORDER BY id DESC LIMIT 1").fetchone()
        stored = json.loads(p[1] or "[]")
        served = [DK._s485_line(p[0], l) for l in stored]
        check("C: (ii) a proposal STORED before this install is served by _s485_line with the same days_left and WITHOUT why / cover_days",
              bool(served) and all(s_["days_left"] == old_days_left(l) for s_, l in zip(served, stored)) and all("why" not in s_ and "cover_days" not in s_ for s_ in served),
              [(s_.get("days_left"), old_days_left(l), sorted(s_.keys())) for s_, l in zip(served, stored)][:3])
        say("   stored proposal %s: %d lines; served keys %s" % (p[0], len(stored), sorted(served[0].keys()) if served else []))
        # (iii) Darpan's add door on the copy
        set_source(c, "darpan")
        os.environ["ORDER_CLOCK"] = "10:00"
        chips_sn = c.execute("SELECT supplier_norm FROM order_supplier_rule WHERE COALESCE(paused,0)=0 AND supplier_norm<>? ORDER BY supplier_norm LIMIT 1", (ORTHO,)).fetchone()[0]
        _as, snap, pace, purch, _t, _o = OR._s470_inputs(c, today)
        cand = next((s for k, s in snap.items() if k in pace and pace[k].get("rate_per_day") and (purch.get(k) or {}).get("vendor") and (purch.get(k) or {}).get("vendor") != ORTHO), None)
        check("an item with a pace and a supplier exists for Darpan's add door", cand is not None)
        s_, j = POST("darpan", "/finance/darpan/kal/api/order/add", {"item": cand["item"], "supplier_norm": chips_sn})
        os.environ.pop("ORDER_CLOCK", None)
        added = [l for b in j.get("suppliers", []) for l in b.get("lines", []) if l.get("added") and l.get("item") == cand["item"]]
        row = c.execute("SELECT lines FROM order_proposal WHERE day=? AND kind='darpan' AND reason='Darpan ne joda' ORDER BY id DESC LIMIT 1", (TODAY,)).fetchone()
        stored_added = next((l for l in json.loads(row[0] or "[]") if l.get("item") == cand["item"]), None) if row else None
        check("C: (iii) a line Darpan adds through his door is STORED with days_left (the one function) and served with it",
              s_ == 200 and bool(added) and stored_added is not None and "days_left" in stored_added and added[0].get("days_left") == stored_added["days_left"] == old_days_left(stored_added),
              (s_, j.get("error"), added[:1], stored_added))
        say("   Darpan added %s: stored %s; served %s" % (cand["item"], stored_added, added[:1]))
        keys = set()
        for b in j.get("suppliers", []):
            for l in b.get("lines", []):
                keys |= set(l.keys())
        check("C: Darpan's api rows carry days_left and NOT why / cover_days", bool(keys) and "days_left" in keys and "why" not in keys and "cover_days" not in keys, sorted(keys))
        set_source(c, "marg_sheet")
        c.close()
    section("6  days_left: the engine's row, a stored proposal, a Darpan-added line (R1-B3)", s6)

    # ============================================================================================ 7 F-916 on the copy
    WORD = {"whatsapp": "WhatsApp gaya", "whatsapp+call": "WhatsApp + call ho gaya", "call": "Call se order ho gaya", "scan": "Bill scan se order ho gaya"}

    def expected_done(c):
        """What the done block must read by D743: every done order (since the newest sheet) whose supplier has NO card, in _done_today's
        order -- '✓ <dd-mm> · <word>' for an earlier day, '✓ <word>' for today; the Call button when the book has a Calls number."""
        es = OS.entries(c)
        pend_sn = {e["sn"] for e in es if e["state"] != "in_line"}
        out = []
        for d in PS._done_today(c):
            if d["sn"] in pend_sn:
                continue
            w = WORD.get(d["via"], "Call se order ho gaya")
            mark = ("✓ %s" % w) if OS.ddmm(d["sent_at"]) == OS.ddmm(OS.now_iso()) else ("✓ %s · %s" % (OS.ddmm(d["sent_at"]), w))
            out.append((d["vendor"], mark, bool(d["phone"])))
        return out, pend_sn

    def s7():
        c = conn()
        es = OS.entries(c)
        pend = [e for e in es if e["state"] != "in_line"]
        done_all = PS._done_today(c)
        pend_sn = {e["sn"] for e in pend}
        s_, h = GET("reception", "/finance/porders/s454/order?all=1")
        B = page_blocks(h)
        say("   the page today (%s, ?all=1): banner %s; still '%s'; cards %s; donehead '%s'" % (s_, B["banner"], B["still"], B["cards"], B["donehead"]))
        for d in B["done"]:
            say("      %-34s %-36s %s" % (d[0][:34], d[1], "Call" if d[2] else "-"))
        want, _p = expected_done(c)
        overlap = [d["vendor"] for d in done_all if d["sn"] in pend_sn]
        say("   done orders since the newest sheet: %d; of suppliers with a card (not to be repeated): %s; earlier days among them: %d"
            % (len(done_all), overlap, sum(1 for d in done_all if OS.ddmm(d["sent_at"]) != OS.ddmm(OS.now_iso()))))
        check("the real install-day state has what D743 speaks of: a done order of an earlier day%s" % (" and a supplier under both lists" if overlap else ""), any("·" in w[1] for w in want) or bool(overlap))
        check("C: the done block reads exactly D743's list -- no supplier with a card, an earlier day's line with its date, today's without (%d lines)" % len(want), B["done"] == want,
              dict(got=B["done"][:6], want=want[:6]))
        if ORTHO in pend_sn and any(d["sn"] == ORTHO for d in done_all):
            yv = next(e for e in pend if e["sn"] == ORTHO)
            check("C: the real case -- %s has ONE card under 'Abhi baaki' and is NOT repeated under 'Ho chuke'; the banner stays (%s)" % (OR._short(yv["vendor"]), B["banner"]),
                  B["cards"].count(ORTHO) == 1 and not any(yv["vendor"] == d[0] for d in B["done"]) and ("Abhi baaki" in B["still"] or "Still to order" in B["still"]) and bool(B["banner"]), B)
        else:
            say("   the real 18-10 case (Yuvika under both lists) does not stand on this copy (pend %s, done %s) -- the constructed cases decide" % (sorted(pend_sn), [d["sn"] for d in done_all][:6]))
        # the constructed cases: a done order of TODAY for a supplier WITH a card (filtered); a 16-10 order and a today's order of a supplier with NO card
        tgt = pend[0] if pend else None
        check("a supplier with a card exists on the copy (the constructed case's food)", tgt is not None)
        oid1 = ins(c, "purchase_order", dict(created_at="%sT07:30:00" % TODAY, created_by="W593", vendor=tgt["vendor"], status="sent", note="W593 walk", total_p=0,
                                              supplier_norm=tgt["sn"], order_src="s454", order_via="whatsapp", section="Medicines"))
        ins(c, "purchase_order_line", dict(order_id=oid1, item="W593 ITEM A", packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
        others = [dict(r) for r in c.execute("SELECT DISTINCT vendor, supplier_norm FROM purchase_order WHERE order_src='s454' AND supplier_norm IS NOT NULL ORDER BY vendor")]
        oth = next((o for o in others if o["supplier_norm"] not in pend_sn and o["supplier_norm"] != ORTHO and PA.book_number(c, o["vendor"], "call")), None)
        check("a supplier with no card and a Calls number exists on the copy", oth is not None)
        day16 = "2026-10-16"
        oid2 = ins(c, "purchase_order", dict(created_at="%sT13:50:00" % day16, created_by="W593", vendor=oth["vendor"], status="sent", note="W593 walk", total_p=0,
                                              supplier_norm=oth["supplier_norm"], order_src="s454", order_via="whatsapp", section="Medicines"))
        ins(c, "purchase_order_line", dict(order_id=oid2, item="W593 ITEM B", packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
        ins(c, "supplier_msg", dict(month=day16[:7], vendor_norm=oth["supplier_norm"], vendor=oth["vendor"], kind="order", ref=oid2, channel="whatsapp", to_number="", body="W593 walk",
                                    status="sent", queued_at="%sT13:50:30" % day16, sent_at="%sT13:52:00" % day16, sent_by="W593", attempts=1))
        oid3 = ins(c, "purchase_order", dict(created_at="%sT08:10:00" % TODAY, created_by="W593", vendor=oth["vendor"], status="sent", note="W593 walk", total_p=0,
                                              supplier_norm=oth["supplier_norm"], order_src="s454", order_via="whatsapp", section="Medicines"))
        ins(c, "purchase_order_line", dict(order_id=oid3, item="W593 ITEM C", packs=1, pack_size=1, units=1, rate_p=0, value_p=0))
        c.commit()
        s_, h = GET("reception", "/finance/porders/s454/order?all=1")
        B2 = page_blocks(h)
        want2, _p2 = expected_done(c)
        mine = [d for d in B2["done"] if d[0] == oth["vendor"] and d[1] in ("✓ 16-10 · WhatsApp gaya", "✓ WhatsApp gaya")]
        say("   with the walk's three orders: cards %s; donehead '%s'; %s's lines %s; %s's lines %s" % (B2["cards"], B2["donehead"], tgt["vendor"], [d for d in B2["done"] if d[0] == tgt["vendor"]], oth["vendor"], mine))
        check("C: a supplier with a card is not repeated under 'Ho chuke' (its order of today is filtered); the 'Abhi baaki' heading stays",
              B2["cards"].count(tgt["sn"]) == 1 and not any(tgt["vendor"] == d[0] for d in B2["done"]) and bool(B2["still"]), (B2["cards"], B2["still"]))
        check("C: the walk's 16-10 WhatsApp order reads '✓ 16-10 · WhatsApp gaya' with its Call button and today's '✓ WhatsApp gaya'; the whole block still reads D743's list",
              ("✓ 16-10 · WhatsApp gaya" in [m[1] for m in mine]) and ("✓ WhatsApp gaya" in [m[1] for m in mine]) and all(m[2] for m in mine) and B2["done"] == want2, (mine, B2["done"][:4], want2[:4]))
        c.execute("UPDATE purchase_order SET status='cancelled' WHERE id IN (?,?,?)", (oid1, oid2, oid3))
        c.commit()
        DUMP["s7"] = dict(real=B, constructed=B2)
        c.close()
    section("7  F-916: the real case on the copy, a supplier with a card not repeated, an earlier day's date (D743)", s7)

    # ============================================================================================ 8 F-739 / the duty
    def s8():
        c = conn()
        set_source(c, "darpan")
        osn = ORTHO
        ortho_item = c.execute("SELECT item FROM stock_item_section WHERE section='Orthotics' ORDER BY item LIMIT 1").fetchone()[0]
        c.execute("INSERT INTO porder_keep (item, keep, source, set_by, set_at) VALUES (?, 60, 'owner', 'W593', ?) ON CONFLICT(item) DO UPDATE SET keep=60, source='owner', set_by='W593'", (ortho_item, OR.now_iso()))
        sups = [dict(r) for r in c.execute("SELECT supplier_norm, supplier FROM order_supplier_rule WHERE COALESCE(paused,0)=0 AND supplier_norm<>? ORDER BY supplier_norm LIMIT 2", (osn,))]
        master = OR._s470_master(c, PA)
        mk = lambda it: dict(item=it, on_hand=5, qty=10, unit="strip", pack_size=10, packing="1*10", rate_p=1000, per_day=1.0, cover_after=15.0, value_p=10000, confirm=False, why=["W593"])   # noqa: E731
        pidA = ins(c, "order_proposal", dict(day=TODAY, supplier_norm=sups[0]["supplier_norm"], vendor=sups[0]["supplier"], kind="interim", status="darpan_ok",
                                              lines=json.dumps([mk(master[1][0]), mk(master[2][0])]), total_p=20000, reason="W593 walk", prepared_at=OR.now_iso()))
        pidY = ins(c, "order_proposal", dict(day=TODAY, supplier_norm=osn, vendor=PO.vendor_of(c), kind="interim", status="darpan_ok",
                                              lines=json.dumps([mk(master[3][0])]), total_p=10000, reason="W593 walk", prepared_at=OR.now_iso()))
        c.commit()
        es = OS.entries(c)
        src_of = {e["sn"]: sorted(set(e.get("sources") or [])) for e in es}
        med = [e for e in es if set(e.get("sources") or []) != {"ortho"}]
        n_med, m_med = len(med), sum(1 for e in med for l in e["lines"] if l.get("src") != "ortho")
        say("   entries on darpan: %s; the old count %d suppliers / %d lines; the medicine count %d suppliers / %d medicine lines"
            % (src_of, len(es), sum(len(e["lines"]) for e in es), n_med, m_med))
        yv = next((e for e in es if e["sn"] == osn), None)
        check("the orthotic vendor's card is MIXED on this copy (an ortho line and a proposal line on one card)", yv is not None and set(yv["sources"]) == {"ortho", "proposal"}, (yv or {}).get("sources"))
        s_, h = GET("reception", "/finance/porders/s454/order")
        B = page_blocks(h)
        m = re.search(r"(\d+) supplier, (\d+) dawa|(\d+) suppliers?, (\d+) medicines?", B["whose"])
        got = (int(m.group(1) or m.group(3)), int(m.group(2) or m.group(4))) if m else None
        say("   the heading: '%s' -> %s" % (B["whose"], got))
        check("C: the darpan heading counts the cards less the orthotic-only card, medicine lines only (a mixed card once): %d / %d" % (n_med, m_med),
              got == (n_med, m_med) and (n_med, m_med) != (len(es), sum(len(e["lines"]) for e in es)), got)
        duty = next(d for d in MAP["duties"] if d["id"] == "reception.medicine_orders")
        n_sql = c.execute(duty["due_sql"]).fetchone()[0]
        say("   DUTY_MAP v%s (%s): reception.medicine_orders due_sql on the copy -> n = %s" % (MAP.get("version"), MAP.get("kit"), n_sql))
        check("C: the duty map has the darpan arm (v15) and its SELECT returns the heading's supplier count (the NEW files' heading)",
              NEW and "= 'darpan' THEN" in duty["due_sql"] and MAP.get("version") == 15 and int(n_sql) == n_med, (NEW, MAP.get("version"), n_sql, n_med))
        c.execute("UPDATE order_proposal SET status='merged', merged_into='2026-01-01' WHERE id IN (?,?)", (pidA, pidY))
        c.execute("DELETE FROM porder_keep WHERE set_by='W593'")   # the walk's own keep row on the COPY only
        set_source(c, "marg_sheet")
        c.close()
    section("8  F-739 / the duty: the heading and the duty map read one rule (charter 13)", s8)

    # ============================================================================================ 9 greps and the handle's type
    def s9():
        orr, por, dk, sr = SRC["order_rules.py"], SRC["porders.py"], SRC["darpan_kal.py"], SRC["spine/spine_read.py"]
        check("C: sp.closing( is nowhere in order_rules.py", "sp.closing(" not in orr)
        check("C: def _s470_arrivals is nowhere in order_rules.py", "def _s470_arrivals" not in orr)
        check("C: def _s485_days_left is nowhere in darpan_kal.py", "def _s485_days_left" not in dk)
        dsb = fn_body(por, "detect_supplies")
        check("C: FROM purchase_line, EFF_LINE and ia.clip are nowhere in detect_supplies (its table read and 20-letter clip are gone)",
              bool(dsb) and "purchase_line l" not in dsb and "EFF_LINE" not in dsb and "ia.clip" not in dsb and "carried(" in dsb)
        check("the one other purchase_line read of porders.py is S403's orthotic fallback _movements (the tables when the spine is not fresh) -- SEEN, not this kit's",
              "FROM purchase_line l WHERE l.supplier_norm" in fn_body(por, "_movements") and por.count("FROM purchase_line") == (1 if NEW else 2))
        check("statistics.median(lots) exactly once in order_rules.py (the ONE lot)", orr.count("statistics.median(lots)") == 1)
        rb = fn_body(orr, "rhythm")
        check("median(gaps) exactly once in order_rules.py, inside rhythm()", orr.count("median(gaps)") == 1 and "median(gaps)" in rb)
        check("C: def days_left( once in order_rules.py; its call sites: _line_out (days_left(out[...), the carried-short row (days_left=None), darpan_kal._s485_line and the add door (OR.days_left(",
              orr.count("def days_left(") == 1 and orr.count("days_left(out[") == 1 and orr.count("days_left=None") == 1 and orr.count("days_left(") == 3
              and dk.count("OR.days_left(") == 2 and dk.count("days_left(") == 2)
        check("C: ON_ORDER_DAYS is nowhere in order_rules.py", "ON_ORDER_DAYS" not in orr)
        check("C: KIT = \"S593 in order_rules.py", 'KIT = "S593' in orr)
        check("C: def purchases_by_supplier once in spine_read.py", sr.count("def purchases_by_supplier(") == 1)
        check("C: the dead loop of lead_learned is gone (no 'for sent, arr, billed')", "for sent, arr, billed" not in orr)
        check("C: order_rules' _s470_snap calls stock_figure.marg on a stock_watch.Spine() handle (SF.marg(con, sw, item) in the text; every stock_figure call this walk saw carried stock_watch.Spine)",
              "SF.marg(con, sw, item" in orr and "_s593_sw().Spine()" in orr and bool(SPTYPES.get("marg")) and all(t == "stock_watch.Spine" for ts in SPTYPES.values() for t in ts), SPTYPES)
        check("C: porders.detect_supplies opens stock_watch.Spine() and tests .ok; carried() is called", "sw = SW.Spine()" in por and 'getattr(sw, "ok", False)' in por and "SF.carried(con, sw, line, ctx)" in por and bool(SPTYPES.get("carried")))
        check("getattr(sp, \"ok\" / getattr(sw, \"ok\": no stock_figure call site in order_rules.py or porders.py hands it a spine_read.Spine (the type seen: %s)" % sorted({t for ts in SPTYPES.values() for t in ts}),
              all(t == "stock_watch.Spine" for ts in SPTYPES.values() for t in ts))
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
    section("9  the greps (one fact, one place) and the handle's type (R1-B1)", s9)

    # ============================================================================================ 10 F-717
    def s10():
        class C(sqlite3.Connection):
            rb = 0

            def rollback(self):
                self.rb += 1
                return super().rollback()
        c = sqlite3.connect(dbp, timeout=60, factory=C)
        c.row_factory = sqlite3.Row
        OS.ensure(c)
        d = os.path.join(os.path.abspath(a.marg), "archive", "ORDER_PENDING", "2026-10")
        os.makedirs(d, exist_ok=True)
        names = []
        for i in (1, 2):
            nm = "W593_ORDER_PENDING_%d.TXT" % i
            open(os.path.join(d, nm), "w").write("W593 walk\n")
            ins(c, "mi_file", dict(md5=wmd5("mi%d" % i), drive_name=nm, server_name=nm, date_from="2026-10-19", stamp="20261019-050000", type="ORDER_PENDING", verdict="VERIFIED",
                                   received_at="2026-10-19T05:00:0%d" % i, source="W593"))
            names.append(nm)
        c.commit()
        saved = OS.load_file

        def boom(*args, **kw):
            raise RuntimeError("W593: the loader fails on purpose")
        OS.load_file = boom
        err = io.StringIO()
        old_err, sys.stderr = sys.stderr, err
        try:
            n = OS.load_pending(c)
        finally:
            sys.stderr = old_err
            OS.load_file = saved
        tried = err.getvalue().count("not loaded")
        say("   two VERIFIED sheets the loader fails on: load_pending returned %s, tried %d, rollback() called %d time(s)" % (n, tried, c.rb))
        check("C: the fallback's except calls con.rollback() for each failed sheet and the loop goes on (2 tried, 2 rollbacks)", tried == 2 and c.rb == 2, (tried, c.rb))
        c.execute("DELETE FROM mi_file WHERE source='W593'")
        c.commit()
        c.close()
        for nm in names:
            try:
                os.remove(os.path.join(d, nm))
            except OSError:
                pass
    section("10 F-717: the fallback loader rolls back and goes on", s10)

    # ============================================================================================ 12 the spine untouched
    def s12():
        schema1 = sorted(r[0] or "" for r in sqlite3.connect(SPINE_PATH).execute("SELECT sql FROM sqlite_master WHERE type IN ('table','index')"))
        check("the spine copy's schema is unchanged by the walk (no table added to the spine)", schema0 == schema1, [s for s in schema1 if s not in schema0])
        check("the spine copy's bytes are unchanged by the walk (no write by any code under test)", hashlib.md5(open(SPINE_PATH, "rb").read()).hexdigest() == spine_md5_0)
        check("C: no code of the six files writes to the spine (no INSERT / UPDATE / DELETE on an sp_ table); purchases_by_supplier is a SELECT",
              not any(re.search(r"(INSERT|UPDATE|DELETE)\s+(INTO\s+|FROM\s+)?sp_", SRC[n]) for n in SIX) and "def purchases_by_supplier" in SRC["spine/spine_read.py"]
              and fn_body(SRC["spine/spine_read.py"].replace("    def ", "def "), "purchases_by_supplier").count("SELECT") == 1)
        try:
            r = subprocess.run([sys.executable, "-B", os.path.join(fin, "spine", "selftest_spine.py")], cwd=os.path.join(fin, "spine"), capture_output=True, text=True, timeout=600)
            tail = (r.stdout or "").strip().splitlines()[-1:] or [""]
            check("selftest_spine.py is green on the copy's spine code (%s)" % tail[0][:60], r.returncode == 0 and "SELFTEST OK" in (r.stdout or ""), (r.returncode, (r.stdout or "")[-300:], (r.stderr or "")[-300:]))
        except Exception as e:                                 # noqa: BLE001
            check("selftest_spine.py ran", False, str(e)[:200])
    section("12 the spine untouched: schema, bytes, no spine write, selftest green", s12)

    # ============================================================================================ 13 the health page and the score
    def s13():
        import importlib.util
        spec = importlib.util.spec_from_file_location("order_rehearsal_w593", os.path.join(fin, "spine", "order_rehearsal.py"))
        RH = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(RH)
        fin_ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        sp = OR._s470_spine()
        day = c_day = None
        for back in range(1, 8):
            d = (today - dt.timedelta(days=back)).isoformat()
            if fin_ro.execute("SELECT 1 FROM order_proposal WHERE day=? LIMIT 1", (d,)).fetchone():
                day = d
                break
        lines, props = RH.keep(fin_ro, sp, day or (today - dt.timedelta(days=1)).isoformat())
        sp.con.close()
        fin_ro.close()
        want = {"key", "item", "vendor", "vendor_norm", "kind", "source", "qty", "unit", "pack_size", "order_units", "value_p", "proposal_id", "lot", "free", "family"}
        check("order_rehearsal.keep() keeps a day on the copy (%s: %d lines, %d proposals) with its row keys unchanged" % (day, len(lines), len(props)), bool(lines) and all(set(l.keys()) == want for l in lines), [sorted(l.keys()) for l in lines[:1]])
        s_, h = GET("manoj", "/finance/health")
        check("/finance/health answers 200 to the owner", s_ == 200, s_)
        r = cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
        if a.old_dump and OLD.get("plan_seconds"):
            lim = max(OLD["plan_seconds"] * 1.5, OLD["plan_seconds"] + 0.5)
            check("plan() on the NEW files finishes under the OLD time x 1.5 (new %.2fs, old %.2fs, limit %.2fs -- one figuring per item, R1-C6)" % (T.get("plan", 0), OLD["plan_seconds"], lim), T.get("plan", 0) <= lim)
        else:
            say("   plan() took %.2fs on these files" % T.get("plan", 0))
    section("13 the health page and the score: order_rehearsal keeps a day; /finance/health; plan() time", s13)

    json.dump(DUMP, open(os.path.join(a.dump, "walk.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED (expected red on the old files): %s" % l)
        if greens:
            say("WALK RED S593: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("NEGATIVE CONTROL: every control red on the old files (%d)" % len(reds))
        say("WALK OK negative control S593: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S593: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S593: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
