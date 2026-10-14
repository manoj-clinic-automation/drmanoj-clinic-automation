#!/usr/bin/env python3
"""walk_s543.py -- kit S543_ORDER_SHEET_MARG (14-Oct-2026). Runs on a SCRATCH folder and SCRATCH databases only.
    python3 -B walk_s543.py --fin <scratch copy of /root/finance with the files under test> --db <a COPY of finance.db>
                            --adb <a COPY of assets.db> --marg <scratch marg_ingest: marg_router.py, xlsx_stdlib.py, marg_take.py, archive/ORDER_PENDING>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config>
                            --map12 <DUTY_MAP.json v12> --map13 <DUTY_MAP.json v13> --kit <kit> [--expect-red]
Rows by key (entry number, item as printed), never by counting; made-up rows dated 2031 or named W543; no export cell, no PDF text and no
phone number is printed (the walk's own output is checked for a run of 10 digits at the end).
  1  ONE-TO-ONE WITH MARG (install-day copy, heal first): the four groups' union = the lines of Marg's newest file, each once; the heading on
     /s454/order for every reception login and the owner; the printed sheet's Marg rows = the same lines, each once, its head; the Aaya tick
     on every ordered row whose order is tied; both buttons with nothing to order.
  2  THE NAMED LINES: COCYP and UPRISE in the old group (/s454/old, their supplier pages, the sheet) with their words and buttons; the lines
     Marg has closed on no page and not on the sheet; a made-up order Marg has closed (CHYMORAL's case) off Maal aaya?, refused by the
     arrival page and its API, not counted by v13's order_arrival (counted by v12).
  3  MARG'S WORD MOVES THE LIST: a made-up newer export (COCYP and two Kedar lines gone, one new line, one line RECEIVE 4:0 / PENDING 6:0);
     a made-up OLDER export changes nothing and sends no notice; the clock 8 days on.
  4  NO GUESS REMOVES A LINE ON M (refresh with a matching Marg purchase); a tied order's line stays on the sheet.
  5  DRAFTS: a Kedar draft + a new Kedar line (printed at once, carded after the draft resolves); a dropped draft keeps its hour; the head
     with a WhatsApp part.
  6  UNITS: the brief's 26 words on the supplier pages and the sheet; the old block; CCM 3 botal; DYNAPAR's draft card 10 botal.
  7  MARG'S PDF: names, entry numbers, TOTAL, 110.00, title, foot, no overlap, landscape, the route + audit, the no-file page.
  8  REORDER: UPRISE yes; COCYP, a removed-by-edit line, a line off M, a line under Maal aaya? refused.
  9  HEAL: NULL before, filled after, a second run writes nothing (inside 1).
 10  THE MAP AGREES WITH THE SCREENS: v13's two counts = the Python's, plain and through aaj_kaam's floored reader; with a removed-edit line.
 11  NOT BROKEN: order_sheet.cron_pass twice, day_summary, darpan_card, owner_lines, on_message_done, marg_take on a loaded file, the home,
     the state API, wa_body byte-identical, page weight and time; the STAFF-EYE walk (portal home tile + door marker per login).
 12  GREPS: the retired names gone; every newest_sheet( caller listed.
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import datetime as dt
import glob
import hashlib
import html as _html
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

KIT = "S543_ORDER_SHEET_MARG"
BASE = "https://followup.dr-manoj.in"
ROLE = {"darpan": "staff", "shavez": "manager", "shivani": "staff", "alisha": "staff", "reception": "staff", "manoj": "doctor"}
RECEPTION = ("darpan", "shavez", "shivani", "alisha", "reception")
NEWEST_SQL = "SELECT id FROM order_sheet ORDER BY COALESCE(NULLIF(stamp,''),'0') DESC, taken_at DESC, id DESC LIMIT 1"
COCYP, UPRISE = ("OP-0334", "COCYP T SYP"), ("OP-0293", "UPRISE 6L INJ")
# §2.6 of the brief: the 26 words of the 12-10 export (Hindi) -- the walk asserts each line Marg's file carries
WORDS = {"RYCOBAL D3": "10 patte", "XQ10": "10 patte", "XYCAL K2": "10 patte", "DYNAPAR QPS PLUS": "10 botal", "DENGEN PLUS": "40 patte",
         "ROSIKA FORTE": "60 patte", "THIO Q AP": "10 patte", "DFO 4X GEL": "12 tube", "GEN D3 NANO": "10 patte", "JAKMAC 5": "30 patte",
         "SHELCAL XT": "10 patte", "KETOROL DT": "10 patte", "ZIXR R OD": "10 patte", "ZUPRINOR 5": "6 nag", "FLUXIC P": "20 patte",
         "PATOPAN DSR": "40 patte", "ASTOFEN R": "10 patte", "C2CALZ": "20 patte", "FLACORT 6": "20 patte", "LOFTYPRED 80 INJ": "30 vial",
         "SALAZAR DS": "20 patte", "ORICOX P": "40 patte", "UPRISE 6L INJ": "18 vial", "COCYP T SYP": "10 botal", "TOLTRIS PLUS": "50 patte",
         "TYNOR WRIST SPL LF L ELASTI": "1 nag"}
RUN, FAILS, CTRL, OUT = [0], [], [], []
W_AT = "2031-03-05T10:00:00"


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:400] + "]") if (got is not None and not cond) else ""))
    if label.startswith("C:"):
        CTRL.append((label, bool(cond)))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--portal", "--map12", "--map13", "--kit"):
        ap.add_argument(k, required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S543_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    say("-- S543 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map13), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import order_sheet_pdf as SP                              # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    import purchase_app as pa                                 # noqa: E402
    import qty_words as qw                                    # noqa: E402
    assert OS.__file__.startswith(fin) and PS.__file__.startswith(fin), (OS.__file__, PS.__file__)
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    cl = fa.app.test_client(use_cookies=False)
    TIMES = []

    def GET(u, path):
        t0 = time.time()
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        TIMES.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data(), r.headers

    def POST(u, path, body):
        r = cl.post(path, base_url=BASE, json=body, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        return r.status_code, (r.get_json(silent=True) or {})

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    pristine = dbp + ".pristine"
    copydb(dbp, pristine)

    def reset(src=None):
        copydb(src or pristine, dbp)
    m12 = json.load(open(a.map12, encoding="utf-8"))
    m13 = json.load(open(a.map13, encoding="utf-8"))

    def due(m, did):
        return next(d["due_sql"] for d in m["duties"] if d["id"] == did)

    def run_sql(sql, floored=False):
        if not floored:
            c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
            try:
                return tuple(c.execute(sql).fetchone())
            finally:
                c.close()
        import aaj_kaam                                       # noqa: PLC0415
        import aaj_seed                                       # noqa: PLC0415
        c, info = aaj_kaam.connect(dbp, mode="staff")
        try:
            return tuple(c.execute(sql).fetchone())
        finally:
            c.close()

    def floored_sql(m, did):
        import aaj_kaam                                       # noqa: PLC0415
        import aaj_seed                                       # noqa: PLC0415
        sql = due(m, did)
        rw = aaj_seed.REWRITE.get(did)
        c, info = aaj_kaam.connect(dbp, mode="staff")
        c.close()
        if rw:
            assert sql.count(rw[0]) == 1, "the aaj_seed REWRITE piece is not in %s exactly once" % did
            sql = sql.replace(rw[0], rw[1].replace("{floor}", info["floor"]))
        return sql

    # ---------------------------------------------------------------- the file and the oracle (independent of the files under test)
    def newest(c):
        return c.execute(NEWEST_SQL).fetchone()[0]

    def file_rows(c, sid=None):
        sid = sid or newest(c)
        s = c.execute("SELECT md5 FROM order_sheet WHERE id=?", (sid,)).fetchone()
        r = c.execute("SELECT server_name, date_from FROM mi_file WHERE md5=? AND type='ORDER_PENDING'", (s[0],)).fetchone()
        p = os.path.join(a.marg, "archive", "ORDER_PENDING", str(r[1])[:7], r[0])
        if a.marg not in sys.path:
            sys.path.insert(0, a.marg)
        import marg_router                                    # noqa: PLC0415
        sh = marg_router.open_sheet(p)
        return p, [[sh.cell_value(i, j) for j in range(sh.ncols)] for i in range(sh.nrows)]

    def file_lines(rows):
        hi = next(i for i, r in enumerate(rows) if [str(x).strip().upper() for x in r[:3]] == ["SUPPLIER", "PHONES", "ITEM NAME"])
        out = []
        for r in rows[hi + 1:]:
            if str(r[0]).strip().upper() == "TOTAL" and not str(r[2]).strip():
                break
            if str(r[2]).strip():
                out.append(r)
        return hi, out

    def M(c):
        return {(r["entry_no"], r["item_printed"]): dict(r) for r in c.execute("SELECT * FROM order_sheet_line WHERE last_sheet=?", (newest(c),))}

    def oracle(c, today):
        """The groups by the brief's §2.3 words, from the database alone."""
        tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
        removed = {(r[0], r[1]) for r in c.execute("SELECT ref, item FROM s454_line_edit WHERE src='sheet' AND removed=1")}
        mx = int(c.execute("SELECT value FROM setting WHERE key='order.sheet_max_age_days'").fetchone()[0])
        g = dict(to_order=set(), in_line=set(), ordered=set(), old=set())
        for k, l in M(c).items():
            o = c.execute("SELECT status, created_at FROM purchase_order WHERE id=?", (l["order_id"],)).fetchone() if l["order_id"] else None
            rm = (str(l["id"]), l["item"]) in removed
            if l["state"] == "to_order" and not rm:
                g["to_order"].add(k)
            elif l["state"] == "in_line":
                g["in_line"].add(k)
            elif l["state"] == "ordered" and o and ((o[0] == "sent" and l["order_id"] not in tied) or
                                                   (today - dt.date.fromisoformat(o[1][:10])).days < mx):
                g["ordered"].add(k)
            else:
                g["old"].add(k)
        return g

    def maal_oracle(c):
        tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
        Ml = list(M(c).values())
        out = []
        for o in c.execute("SELECT * FROM purchase_order WHERE status='sent' ORDER BY created_at, id").fetchall():
            if o["id"] in tied:
                continue
            ents = {x.strip() for x in str(o["ext_ref"] or "").split(",") if x.strip()}
            if ents:
                items = {r[0] for r in c.execute("SELECT item FROM purchase_order_line WHERE order_id=?", (o["id"],))}
                if not any(x["supplier_norm"] == o["supplier_norm"] and x["entry_no"] in ents and x["item"] in items for x in Ml):
                    continue
            out.append(o["id"])
        return out

    def stamp_text(c, full=False):
        s = c.execute("SELECT stamp, newest_date FROM order_sheet WHERE id=?", (newest(c),)).fetchone()
        m = re.match(r"^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)", str(s[0] or ""))
        if not m:
            d = str(s[1])
            return ("%s-%s-%s" % (d[8:10], d[5:7], d[:4])) if full else ("%s-%s" % (d[8:10], d[5:7]))
        return ("%s-%s-%s %s:%s" % (m.group(3), m.group(2), m.group(1), m.group(4), m.group(5)) if full
                else "%s-%s %s:%s" % (m.group(3), m.group(2), m.group(4), m.group(5)))

    def lid(c, key):
        r = c.execute("SELECT id FROM order_sheet_line WHERE entry_no=? AND item_printed=?", key).fetchone()
        return r[0] if r else None

    def block_of(h, line_id):
        m = re.search(r'<div class="ol" data-line="%d">(.*?)</div></div>' % line_id, h.decode("utf-8", "replace"), re.S)
        return m.group(1) if m else None

    def sheet_rows():
        c = conn()
        try:
            lay = SP.layout(c)
        finally:
            c.close()
        return lay, [dict(r, supplier=b["name"]) for b in lay["blocks"] for r in b["rows"]]

    def section(name, fn):
        say("-- " + name)
        try:
            fn()
        except Exception as e:                                # noqa: BLE001 -- a section that raises is red, the walk goes on
            import traceback                                  # noqa: PLC0415
            tb = traceback.format_exc().strip().splitlines()
            check("C: section '%s' ran to its end" % name.split()[0], False, "%s: %s | %s" % (type(e).__name__, str(e)[:160], " / ".join(x.strip() for x in tb[-4:])[:300]))

    today = dt.date.today()
    raw = conn()
    have_new = hasattr(OS, "open_order")
    W = {}                                                    # facts carried between sections

    def OO(c):
        """open_order on the new files; on the old files (no such reading) an empty one, so the walk goes on and its checks go red."""
        if have_new:
            return OS.open_order(c)
        return dict(lines=[], groups=dict(to_order=[], in_line=[], ordered=[], old=[]), count=0, suppliers=0)

    def QTY(l, **kw):
        f = getattr(OS, "qty_of", None)
        return f(l, **kw) if f else None

    # ============================================================================================ 1 + 9
    def s1():
        c = conn()
        OS.ensure(c)
        sid = newest(c)
        W["sid"] = sid
        p, rows = file_rows(c)
        hi, fl = file_lines(rows)
        fkeys = [(str(r[4]).strip(), str(r[2]).strip()) for r in fl]
        W["fkeys"], W["frows"], W["fpath"] = fkeys, rows, p
        Mk = M(c)
        check("Marg's newest export (sheet %d, stamp %s) has %d lines; the database's M carries exactly those keys" % (sid, stamp_text(c, True), len(fkeys)),
              sorted(fkeys) == sorted(Mk) and len(set(fkeys)) == len(fkeys), (len(fkeys), len(Mk)))
        cols = {r[1] for r in c.execute("PRAGMA table_info(order_sheet_line)")}
        nnull = c.execute("SELECT COUNT(*) FROM order_sheet_line WHERE last_sheet=? AND marg_pend_raw IS NULL", (sid,)).fetchone()[0] if "marg_pend_raw" in cols else -1
        if hasattr(OS, "heal_marg_cols"):
            h1 = OS.heal_marg_cols(c)
            h2 = OS.heal_marg_cols(c)
            filled = c.execute("SELECT COUNT(*) FROM order_sheet_line WHERE last_sheet=? AND marg_pend_raw IS NOT NULL", (sid,)).fetchone()[0]
        else:
            h1 = h2 = filled = None
        check("C: 9 heal: before heal_marg_cols the %d lines of M have no Marg RECEIVE / PENDING (%s NULL); it fills %s; a second run writes 0"
              % (len(fkeys), nnull, h1), nnull == len(fkeys) and h1 == len(fkeys) and h2 == 0 and filled == len(fkeys), (nnull, h1, h2, filled))
        if filled:
            byk = {(str(r[4]).strip(), str(r[2]).strip()): r for r in fl}
            bad = [k for k, l in M(c).items() if l["marg_pend_raw"] != (("%d" % int(byk[k][8])) if isinstance(byk[k][8], float) else str(byk[k][8]).strip())]
            check("the healed PENDING of every line equals Marg's own cell (shaped as qty_raw)", not bad, bad[:3])
        c.close()
        copydb(dbp, pristine)                                 # the install-day copy, healed: every later section starts from it
        c = conn()
        g = oracle(c, today)
        W["g"] = g
        say("   install-day groups (by the brief's rule, from the database): to_order %d · in_line %d · ordered %d · old %d"
            % tuple(len(g[k]) for k in ("to_order", "in_line", "ordered", "old")))
        oo = OO(c)
        mods = {k: {(l["entry_no"], l["item_printed"]) for l in v} for k, v in oo["groups"].items()}
        union = [(l["entry_no"], l["item_printed"]) for v in oo["groups"].values() for l in v]
        check("C: open_order: the four groups' union = the file's %d lines, each once; each group = the rule's (%s)"
              % (len(fkeys), " / ".join("%d" % len(mods[k]) for k in ("to_order", "in_line", "ordered", "old"))),
              sorted(union) == sorted(fkeys) and mods == g and oo["count"] == len(fkeys), {k: len(v) for k, v in mods.items()})
        sups = len({l["supplier_norm"] for l in M(c).values()})
        W["sups"], W["count"], W["stamp"] = sups, len(fkeys), stamp_text(c)
        hi_t = "Marg mein khula order (%s) · %d supplier, %d dawa" % (stamp_text(c), sups, len(fkeys))
        en_t = ("Marg's open order (%s) · %d suppliers, %d medicines" % (stamp_text(c), sups, len(fkeys))).replace("1 suppliers", "1 supplier")
        miss, olds = [], []
        for u in RECEPTION + ("manoj",):
            s, h, _ = GET(u, "/finance/porders/s454/order")
            t = text(h)
            want = en_t if u == "manoj" else hi_t
            m = re.search(r'id="(?:margopen|whose)">([^<]*)<', h.decode("utf-8", "replace"))
            olds.append("%s: %s" % (u, _html.unescape(m.group(1)) if m else "-"))
            if s != 200 or want not in t:
                miss.append(u)
        check("C: the heading '%s' on /s454/order for %s, and in English for manoj" % (hi_t, ", ".join(RECEPTION)), not miss, (miss, olds[:2]))
        s, h, _ = GET("shavez", "/finance/porders/s454/order")
        cnt = PS.counts(c)
        check("C: both buttons on the page with nothing to order (Order karna hai %d): 'Order sheet print karo' and 'Marg ka order (PDF)' -> marg.pdf"
              % cnt["order"], cnt["order"] > 0 or (b'id="print"' in h and b'id="margpdf"' in h and b'href="/finance/porders/s454/marg.pdf"' in h),
              (cnt, b'id="print"' in h, b'id="margpdf"' in h))
        lay, rows = sheet_rows()
        mitems = sorted(l["item"] for l in M(c).values())
        srows = sorted(r["item"] for r in rows if r.get("marg", True))
        check("C: the printed sheet's rows of Marg's lines = M's %d items, each once" % len(mitems), srows == mitems,
              "sheet %d rows, missing %s, extra %s" % (len(srows), sorted(set(mitems) - set(srows))[:4], sorted(set(srows) - set(mitems))[:4]))
        parts = [p for n, p in ((len(g["to_order"]), "%d order karna hai"), (len(g["in_line"]), "%d WhatsApp line mein"), (len(g["ordered"]), "%d order ho gaya"),
                                (len(g["old"]), "%d purane pending")) if n]
        parts = [p % n for n, p in ((len(g["to_order"]), "%d order karna hai"), (len(g["in_line"]), "%d WhatsApp line mein"),
                                    (len(g["ordered"]), "%d order ho gaya"), (len(g["old"]), "%d purane pending")) if n]
        head = "Marg ka khula order: %s  ·  %d supplier  ·  %d dawa: %s" % (stamp_text(c, True), sups, len(fkeys), ", ".join(parts))
        check("C: the sheet's head '%s'" % head, lay["line"].startswith(head), lay["line"])
        tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
        Mk = M(c)
        want_aaya = sorted(Mk[k]["item"] for k in g["ordered"] if Mk[k]["order_id"] in tied)
        got_aaya = sorted(r["item"] for r in rows if r.get("aaya"))
        s, pdf, _ = GET("shavez", "/finance/porders/s454/sheet.pdf")
        W["sheet_pdf"] = pdf
        check("C: the Aaya box ticked on the %d ordered rows whose order is tied to a bill scan (and only those); the PDF draws %d Aaya ticks"
              % (len(want_aaya), pdf.count(b"tick-col-aaya")), got_aaya == want_aaya and pdf.count(b"% tick-col-aaya") == len(want_aaya) and len(want_aaya) > 0,
              (len(got_aaya), pdf.count(b"tick-col-aaya")))
        cr = [r for r in rows if r["item"] == "COCYP T SYP"]
        check("C: COCYP T SYP prints once, as an old row, its Aaya empty (its order is tied, but it is old)", len(cr) == 1 and cr[0]["kind"] == "old" and not cr[0].get("aaya"), cr)
        c.close()
    section("1  one-to-one with Marg (and 9, the heal)", s1)

    # ============================================================================================ 2
    def s2():
        reset()
        c = conn()
        cid, uid = lid(c, COCYP), lid(c, UPRISE)
        check("COCYP T SYP and UPRISE 6L INJ are lines of Marg's newest export (found by key)", COCYP in M(c) and UPRISE in M(c), (cid, uid))
        s, h, _ = GET("shavez", "/finance/porders/s454/old")
        bc, bu = block_of(h, cid or 0), block_of(h, uid or 0)
        check("C: /s454/old shows both: COCYP 'Order 06-10 · maal aa gaya · Marg mein baaki' with no 'Dobara order karo'; UPRISE 'Marg mein baaki' with the button",
              bool(bc) and bool(bu) and "maal aa gaya · Marg mein baaki" in _html.unescape(bc) and "Order 06-10" in _html.unescape(bc) and "reorder" not in bc
              and "Marg mein baaki" in _html.unescape(bu) and "maal aa gaya" not in bu and "reorder" in bu, (text(bc or "-")[:120], text(bu or "-")[:120]))
        sp = {}
        for key, sn in ((COCYP, "SHIVAAZ%20FORMULATIONS"), (UPRISE, "RADHA%20MEDICAL%20%26%20SCIENTIFIC")):
            s2_, h2, _ = GET("shavez", "/finance/porders/s454/order/" + sn)
            sp[key[1]] = (s2_, b'data-line="%d"' % (lid(c, key) or 0) in h2)
        check("C: each on its supplier's page (Shivaaz, Radha)", all(v == (200, True) for v in sp.values()), sp)
        closed = [dict(r) for r in c.execute("SELECT id, item, supplier_norm FROM order_sheet_line WHERE state IN ('old','lapsed','closed_marg','dropped') AND last_sheet<>?",
                                             (newest(c),))]
        shown = [x["item"] for x in closed if (b'data-line="%d"' % x["id"]) in h]
        lay, rows = sheet_rows()
        printed = [x["item"] for x in closed if any(r["item"] == x["item"] and r["kind"] == "old" for r in rows)]
        say("   lines Marg has closed (old, off its newest export): %d -- %s" % (len(closed), ", ".join(x["item"] for x in closed)[:300]))
        check("C: none of the %d lines Marg has closed is on /s454/old or on the printed sheet" % len(closed), closed and not shown and not printed,
              "shown %s / printed %s" % (shown, printed))
        # CHYMORAL's case, made up: an order of Marg's sheet whose entry Marg no longer prints
        oid = ins(c, "purchase_order", dict(created_at=W_AT, created_by="w543walk", vendor="W543 WALK SUPPLIER", status="sent", note="S543 walk",
                                            total_p=0, supplier_norm="W543 WALK SUPPLIER", ext_ref="OP-W5430", order_src="s454", order_via="call"))
        ins(c, "purchase_order_line", dict(order_id=oid, item="W543 CLOSED ITEM", packs=2, pack_size=1, units=2))
        c.commit()
        n12 = run_sql(due(m12, "reception.order_arrival"))[0]
        n13 = run_sql(due(m13, "reception.order_arrival"))[0]
        mo = [o["id"] for o in PS.maal_orders(c)]
        check("C: a made-up order of Marg's sheet whose entry Marg no longer prints is off 'Maal aaya?' (the open ones by the rule: %s)" % maal_oracle(c),
              oid not in mo and mo == maal_oracle(c), mo)
        s, h, _ = GET("shavez", "/finance/porders/s454/maal/%d" % oid)
        check("C: its arrival page refuses it: 'Yeh order Marg mein band ho chuka hai.' with BACK", s == 200 and b'id="margband"' in h and
              "Yeh order Marg mein band ho chuka hai." in text(h), text(h)[:160])
        s, j = POST("shavez", "/finance/porders/api/s454/arrive", dict(order_id=oid, lines=[]))
        st = c.execute("SELECT status FROM purchase_order WHERE id=?", (oid,)).fetchone()[0]
        ar = c.execute("SELECT COUNT(*) FROM purchase_order_line WHERE order_id=? AND arrived_at IS NOT NULL", (oid,)).fetchone()[0]
        check("C: its arrival API refuses it (409, the same words), nothing written (status %s, %d lines arrived)" % (st, ar),
              s == 409 and j.get("message") == "Yeh order Marg mein band ho chuka hai." and st == "sent" and ar == 0, (s, j))
        check("the map: v12's order_arrival counts it (%d), v13's does not (%d) -- v13 = len(maal_orders) %d" % (n12, n13, len(mo)),
              n12 == n13 + 1 and n13 == len(maal_oracle(c)), (n12, n13, len(mo)))
        check("C: v13's order_arrival = the screen's Maal aaya? count with the made-up closed order present", n13 == len(mo), (n13, len(mo)))
        say("   Maal aaya? on the install-day copy: orders %s (the real CHYMORAL order 3 is %s)"
            % (maal_oracle(c), (c.execute("SELECT status FROM purchase_order WHERE id=3").fetchone() or ["-"])[0]))
        c.close()
    section("2  the named lines", s2)

    # ============================================================================================ 3 (+10 on its copy)
    def s3():
        reset()
        c = conn()
        rows = [list(r) for r in W["frows"]]
        hi, fl = file_lines(rows)
        gone = [COCYP] + [k for k in W["fkeys"] if k[0] == "OP-0343"][:2]
        check("the three lines the newer export drops are on today's M: COCYP and Kedar's %s" % [k[1] for k in gone[1:]], len(gone) == 3 and all(k in M(c) for k in gone), gone)
        part = next((k for k in W["fkeys"] if k[1] == "ASTOFEN R"), None)
        newer = []
        for r in rows:
            k = (str(r[4]).strip(), str(r[2]).strip())
            if k in gone:
                continue
            r = list(r)
            if k == part:
                r[7], r[8] = "4:0", "6:0"
            if str(r[0]).strip().upper() == "TOTAL":
                newer.append(["KEDAR PHARMACEUTICAL", "", "W543 WALK NEW", "1*10", "OP-W5431", today.strftime("%d-%m-%Y"), "5:0", "-", "5:0", 10.0, 50.0])
            newer.append(r)
        res = OS.load_rows(c, newer, hashlib.md5(b"w543-newer").hexdigest(), "W543_WALK_NEWER", "push", "20310301-100000")
        nsid = res.get("sheet_id")
        check("a made-up newer export (stamp 20310301-100000) loads and is Marg's word now", nsid and newest(c) == nsid, res)
        s, h, _ = GET("shavez", "/finance/porders/s454/old")
        ids = [lid(c, k) for k in gone]
        lay, srows = sheet_rows()
        oo_items = {l["item_printed"] for l in OO(c)["lines"]}
        check("the three dropped lines leave every page and the sheet (/s454/old, the printed sheet, open_order)",
              not any((b'data-line="%d"' % i) in h for i in ids) and not any(r["item"] in [k[1] for k in gone] for r in srows) and not (oo_items & {k[1] for k in gone}),
              [k[1] for k in gone if k[1] in oo_items])
        s, h, _ = GET("shavez", "/finance/porders/s454/order/KEDAR%20PHARMACEUTICAL")
        t = text(h)
        check("C: the new line is on Kedar's card, '5 patte'", s == 200 and "W543 WALK NEW 5 patte" in t, t[:200])
        pl = next((l for l in OO(c)["lines"] if (l["entry_no"], l["item_printed"]) == part), None)
        want = "Marg: %s aaya, %s baaki" % (qw.words(40, "1*10", lang="hi", pack=10, name="ASTOFEN R"), qw.words(60, "1*10", lang="hi", pack=10, name="ASTOFEN R"))
        check("C: the partial line (RECEIVE 4:0, PENDING 6:0) reads '%s'; its pending quantity %s" % (want, pl and QTY(pl, pend=True)),
              bool(pl) and want in OS.old_word(pl) and QTY(pl, pend=True) == qw.words(60, "1*10", lang="hi", pack=10, name="ASTOFEN R"), pl and OS.old_word(pl))
        g = oracle(c, today)
        twelve = {k for k, l in M(c).items() if l["order_id"] and (c.execute("SELECT substr(created_at,1,10) FROM purchase_order WHERE id=?", (l["order_id"],)).fetchone()[0] or "") >= "2026-10-12"}
        modg = {k: {(l["entry_no"], l["item_printed"]) for l in v} for k, v in OO(c)["groups"].items()}
        check("C: the %d lines of the 12-10 orders still on Marg's export stay 'ordered', not old (R2-2)" % len(twelve), twelve and twelve <= modg["ordered"] and twelve <= g["ordered"],
              sorted(twelve - modg["ordered"])[:4])
        mo = {o["id"] for o in PS.maal_orders(c)}
        both = [l["item"] for l in OO(c)["groups"]["old"] if l.get("order_id") in mo]
        check("nothing is on 'Maal aaya?' and 'Purane pending' both", not both, both)
        # 10 on this copy
        n13 = run_sql(due(m13, "reception.medicine_orders"))[0]
        a13 = run_sql(due(m13, "reception.order_arrival"))[0]
        check("10 (walk 3's copy): v13 medicine_orders %d = the screen's Order karna hai %d; v13 order_arrival %d = Maal aaya? %d"
              % (n13, PS.counts(c)["order"], a13, len(mo)), n13 == PS.counts(c)["order"] and a13 == len(mo), (n13, a13))
        # the OLDER export
        before = {k: (l["id"], l.get("marg_recv_raw"), l.get("marg_pend_raw")) for k, l in M(c).items()}
        older = [rows[0], rows[hi]] + [list(r) for r in fl[:5]] + [["KEDAR PHARMACEUTICAL", "", "W543 WALK OLDER", "1*10", "OP-W5432", "11-10-2026", "2:0", "-", "2:0", 10.0, 20.0],
                                                                  ["TOTAL", "", "", "", "", "", 0.0, "", 0.0, "", 0.0]]
        res2 = OS.load_rows(c, older, hashlib.md5(b"w543-older").hexdigest(), "W543_WALK_OLDER", "push", "20261011-090000")
        osid = res2.get("sheet_id")
        after = {k: (l["id"], l.get("marg_recv_raw"), l.get("marg_pend_raw")) for k, l in M(c).items()}
        nt = c.execute("SELECT notice FROM order_sheet WHERE id=?", (osid,)).fetchone()
        check("C: a made-up OLDER export (stamp 20261011-090000) loaded after it: newest_sheet unchanged", (OS.newest_sheet(c) or {}).get("id") == nsid, (OS.newest_sheet(c) or {}).get("id"))
        check("C: ... M unchanged line for line, Marg's columns of M unchanged (%d lines)" % len(before), before == after, "%d -> %d lines" % (len(before), len(after)))
        check("C: ... and no arrival notice queued for it", nt is not None and not nt[0], nt and str(nt[0])[:80])
        # the clock 8 days on
        os.environ["ORDER_TODAY"] = (today + dt.timedelta(days=8)).isoformat()
        try:
            tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
            Mk = M(c)
            tl = next((k for k, l in sorted(Mk.items()) if l["state"] == "ordered" and l["order_id"] in tied and k != part), None)
            sl = next((k for k, l in sorted(Mk.items()) if l["state"] == "ordered" and l["order_id"] in set(maal_oracle(c))), None)
            s, h, _ = GET("shavez", "/finance/porders/s454/old")
            oo = OO(c)
            gk = {k: {(l["entry_no"], l["item_printed"]) for l in v} for k, v in oo["groups"].items()}
            bt, bp = block_of(h, Mk[tl]["id"]) if tl else None, block_of(h, Mk[part]["id"]) if part in Mk else None
            check("C: 8 days on: a 12-10 line whose order is tied (%s) is old -- 'maal aa gaya · Marg mein baaki', no button" % (tl and tl[1]),
                  bool(tl) and tl in gk["old"] and bool(bt) and "maal aa gaya · Marg mein baaki" in _html.unescape(bt) and "reorder" not in bt, text(bt or "-")[:120])
            check("C: ... the partial line reads 'maal aa gaya · %s' with its pending quantity, no button" % want,
                  bool(bp) and ("maal aa gaya · " + want) in _html.unescape(bp) and qw.words(60, "1*10", lang="hi", pack=10, name="ASTOFEN R") in text(bp) and "reorder" not in bp,
                  text(bp or "-")[:160])
            check("C: ... a line whose order is still under 'Maal aaya?' (%s) stays 'ordered', off /s454/old" % (sl and sl[1]),
                  bool(sl) and sl in gk["ordered"] and (b'data-line="%d"' % Mk[sl]["id"]) not in h, sl)
        finally:
            os.environ.pop("ORDER_TODAY", None)
        c.close()
    section("3  Marg's word moves the list", s3)

    # ============================================================================================ 4
    def s4():
        reset()
        c = conn()
        uid = lid(c, UPRISE)
        c.execute("UPDATE order_sheet_line SET state='to_order', reorder_day=?, order_id=NULL WHERE id=?", ("2031-03-01", uid))
        exp = c.execute("SELECT md5 FROM purchase_export WHERE superseded_by IS NULL LIMIT 1").fetchone()
        sn = c.execute("SELECT supplier_norm FROM order_sheet_line WHERE id=?", (uid,)).fetchone()[0]
        ins(c, "purchase_line", dict(supplier_norm=sn, bill_no="W543-1", bill_date="2031-03-06", month="2031-03", item="UPRISE 6L INJ", qty=18,
                                     direction="PURCHASE", source_md5=exp[0], line_type="ITEMWISE"))
        off = ins(c, "order_sheet_line", dict(entry_no="OP-W5435", item_printed="W543 OFF ITEM", item="W543 OFF ITEM", resolved=1, supplier="W543 WALK SUPPLIER",
                                              supplier_norm="W543 WALK SUPPLIER", packing="1*1", pack_size=1, line_date="2031-03-01", qty_raw="2", qty=2,
                                              kind="new", state="to_order", first_sheet=1, last_sheet=1, created_at=W_AT))
        exp2 = exp[0]
        ins(c, "purchase_line", dict(supplier_norm="W543 WALK SUPPLIER", bill_no="W543-2", bill_date="2031-03-06", month="2031-03", item="W543 OFF ITEM", qty=2,
                                     direction="PURCHASE", source_md5=exp2, line_type="ITEMWISE"))
        c.commit()
        OS.refresh(c, dt.date(2031, 3, 2))
        st = c.execute("SELECT state FROM order_sheet_line WHERE id=?", (uid,)).fetchone()[0]
        st2 = c.execute("SELECT state FROM order_sheet_line WHERE id=?", (off,)).fetchone()[0]
        check("C: a to_order line ON Marg's export with a matching Marg purchase after its date stays to_order after refresh() (got %s)" % st, st == "to_order", st)
        check("a to_order line OFF Marg's export with a matching purchase still closes ('closed_marg', as before): %s" % st2, st2 == "closed_marg", st2)
        lay, rows = sheet_rows()
        tied = {r[0] for r in c.execute("SELECT order_id FROM order_scan_tie")}
        tl = [l["item"] for l in M(c).values() if l["state"] == "ordered" and l["order_id"] in tied and (l["entry_no"], l["item_printed"]) in W["g"]["ordered"]]
        printed = [r["item"] for r in rows if r["kind"] == "awaited"]
        check("C: the %d ordered lines whose order is tied stay on the sheet while Marg carries them" % len(tl), tl and all(x in printed for x in tl),
              sorted(set(tl) - set(printed))[:4])
        c.close()
    section("4  no guess removes a line on M", s4)

    # ============================================================================================ 5
    def s5():
        reset()
        c = conn()
        sid = newest(c)
        now = dt.datetime.now().replace(microsecond=0).isoformat()
        nl = ins(c, "order_sheet_line", dict(entry_no="OP-W5433", item_printed="W543 DRAFT LINE", item="W543 DRAFT LINE", resolved=1, supplier="KEDAR PHARMACEUTICAL",
                                             supplier_norm="KEDAR PHARMACEUTICAL", packing="1*10", pack_size=10, line_date=today.isoformat(), qty_raw="3:0", qty=3,
                                             strip=1, units=30, kind="new", state="to_order", first_sheet=sid, last_sheet=sid, created_at=now))
        d1 = ins(c, "purchase_order", dict(created_at=now, created_by="w543walk", vendor="KEDAR PHARMACEUTICAL", status="draft", total_p=0,
                                           supplier_norm="KEDAR PHARMACEUTICAL", ext_ref="OP-0345", order_src="s454", order_via="whatsapp"))
        ins(c, "purchase_order_line", dict(order_id=d1, item="ASTOFEN R", packs=10, pack_size=10, units=100))
        m1 = ins(c, "supplier_msg", dict(month=today.strftime("%Y-%m"), vendor_norm="KEDAR PHARMACEUTICAL", vendor="KEDAR PHARMACEUTICAL", kind="order", ref=d1,
                                         channel="whatsapp", body="W543 walk", status="queued", queued_at=now))
        d2 = ins(c, "purchase_order", dict(created_at=now, created_by="w543walk", vendor="W543 WALK SUPPLIER", status="draft", total_p=0,
                                           supplier_norm="W543 WALK SUPPLIER", ext_ref="OP-W5434", order_src="s454", order_via="whatsapp"))
        ins(c, "purchase_order_line", dict(order_id=d2, item="W543 DROPPED ITEM", packs=1, pack_size=1, units=1))
        ins(c, "supplier_msg", dict(month=today.strftime("%Y-%m"), vendor_norm="W543 WALK SUPPLIER", vendor="W543 WALK SUPPLIER", kind="order", ref=d2,
                                    channel="whatsapp", body="W543 walk", status="queued", queued_at=now))
        dy = lid(c, next(k for k in W["fkeys"] if k[1] == "DYNAPAR QPS PLUS"))
        d3 = ins(c, "purchase_order", dict(created_at=now, created_by="w543walk", vendor="BASS PHARMA DISTRIBUTORS PVT LTD", status="draft", total_p=0,
                                           supplier_norm="BASS PHARMA DISTRIBUTORS PVT LTD", ext_ref="OP-0348", order_src="s454", order_via="whatsapp"))
        ins(c, "purchase_order_line", dict(order_id=d3, item="DYNAPAR QPS PLUS", packs=10, pack_size=1, units=10))
        ins(c, "supplier_msg", dict(month=today.strftime("%Y-%m"), vendor_norm="BASS PHARMA DISTRIBUTORS PVT LTD", vendor="BASS PHARMA DISTRIBUTORS PVT LTD", kind="order",
                                    ref=d3, channel="whatsapp", body="W543 walk", status="queued", queued_at=now))
        c.execute("UPDATE order_sheet_line SET state='in_line', order_id=? WHERE id=?", (d3, dy))
        c.commit()
        lay, rows = sheet_rows()
        r = [x for x in rows if x["item"] == "W543 DRAFT LINE"]
        check("C: a new Kedar line on Marg's export while Kedar's WhatsApp is in the line: printed at once as a 'new' row", len(r) == 1 and r[0]["kind"] == "new", r)
        ek = next((e for e in OS.entries(c) if e["sn"] == "KEDAR PHARMACEUTICAL"), None)
        check("... on the screen Kedar's card is the draft (the new line not yet on it)", ek and ek.get("draft") and not any(l["item"] == "W543 DRAFT LINE" for l in ek["lines"]),
              ek and [l["item"] for l in ek["lines"]])
        g = oracle(c, today)
        parts_ok = ("%d WhatsApp line mein" % len(g["in_line"])) in lay["line"] and len(g["in_line"]) >= 1
        tot = sum(len(v) for v in g.values())
        check("C: the head carries the WhatsApp part ('%d WhatsApp line mein'); its parts add up to M (%d)" % (len(g["in_line"]), tot),
              parts_ok and sum(int(x) for x in re.findall(r"(\d+) (?:order karna hai|WhatsApp line mein|order ho gaya|purane pending)", lay["line"])) == tot, lay["line"])
        s, h, _ = GET("shavez", "/finance/porders/s454/order/BASS%20PHARMA%20DISTRIBUTORS%20PVT%20LTD")
        check("C: 6 DYNAPAR QPS PLUS on BASS's draft card reads '10 botal' (the sheet line's packing)", s == 200 and "DYNAPAR QPS PLUS 10 botal" in text(h), text(h)[:200])
        ew = next((e for e in OS.entries(c) if e["sn"] == "W543 WALK SUPPLIER"), None)
        check("a draft whose lines Marg does not carry keeps its card for its hour (WhatsApp line mein)", ew is not None and ew["state"] == "in_line", ew and ew["state"])
        import supplier_msg                                   # noqa: PLC0415
        supplier_msg.on_message_done(c, m1, True) if hasattr(supplier_msg, "on_message_done") else OS.on_message_done(c, m1, True)
        st = c.execute("SELECT status FROM purchase_order WHERE id=?", (d1,)).fetchone()[0]
        ek = next((e for e in OS.entries(c) if e["sn"] == "KEDAR PHARMACEUTICAL"), None)
        check("11 supplier_msg.on_message_done: the draft sent -> ordered (%s); then the new line is on Kedar's card" % st,
              st == "sent" and ek and any(l["item"] == "W543 DRAFT LINE" for l in ek["lines"]), (st, ek and [l["item"] for l in ek["lines"]]))
        _ = nl
        c.close()
    section("5  drafts", s5)

    # ============================================================================================ 6
    def s6():
        reset()
        c = conn()
        mk = M(c)
        c.execute("UPDATE order_sheet_line SET state='to_order', order_id=NULL, reorder_day=? WHERE last_sheet=?", (today.isoformat(), newest(c)))
        c.commit()
        bad, seen = [], 0
        for sn in sorted({l["supplier_norm"] for l in mk.values()}):
            s, h, _ = GET("shavez", "/finance/porders/s454/order/" + re.sub(r"[^A-Za-z0-9.]", lambda m: "%%%02X" % ord(m.group(0)), sn))
            t = text(h)
            for l in mk.values():
                if l["supplier_norm"] == sn and l["item"] in WORDS:
                    seen += 1
                    if (l["item"] + " " + WORDS[l["item"]]) not in t:
                        bad.append(l["item"])
        check("C: 6 the brief's words on the supplier pages, each of Marg's %d lines (e.g. DYNAPAR '10 botal', LOFTYPRED '30 vial', DFO '12 tube', ZUPRINOR '6 nag')" % seen,
              seen >= 1 and not bad, bad[:5])
        lay, rows = sheet_rows()
        sb = [r["item"] for r in rows if r["item"] in WORDS and r["qty"] != WORDS[r["item"]]]
        check("C: ... and on the printed sheet", rows and not sb, sb[:5])
        reset()
        c2 = conn()
        s, h, _ = GET("shavez", "/finance/porders/s454/old")
        t = text(h)
        check("C: the old block: UPRISE 6L INJ '18 vial', COCYP T SYP '10 botal'", "UPRISE 6L INJ 18 vial" in t and "COCYP T SYP 10 botal" in t, t[:200])
        ccm = dict(item="CCM", packing="1*40", pack_size=40, qty=3, loose=0, strip=1)
        got = QTY(ccm, con=c2)
        check("C: a made-up whole-unit line (CCM, 1*40, 3:0) reads '3 botal', never '120 botal'", got == "3 botal", got)
        c.close()
        c2.close()
    section("6  units", s6)

    # ============================================================================================ 7
    def s7():
        reset()
        c = conn()
        import marg_order_pdf as MP                           # noqa: PLC0415
        data = MP.build(c)
        tx = SP.text_of(data)
        rows = W["frows"]
        hi, fl = file_lines(rows)
        names = [str(r[2]).strip() for r in fl]
        ents = [str(r[4]).strip() for r in fl]
        tot = next(r for r in rows if str(r[0]).strip().upper() == "TOTAL")
        tfig = [MP.cell_text(tot[i], i) for i in (6, 10)]
        check("C: 7 Marg's PDF holds the %d item names, the %d distinct entry numbers (%d cells), the TOTAL figures %s, the title, the foot 'Marg se nikala: %s'"
              % (len(names), len(set(ents)), len(ents), "/".join(tfig), stamp_text(c, True)),
              all(n in tx for n in names) and all(tx.count(e) == ents.count(e) for e in set(ents)) and all(f in tx for f in tfig)
              and "PENDING ORDERS (PURCHASE)" in tx and any(("Marg se nikala: %s (Darpan)" % stamp_text(c, True)) in x for x in tx), "(text withheld)")
        rates = [r[9] for r in fl if isinstance(r[9], float)]
        check("the RATE column with two decimals (110.0 -> '110.00' where Marg has it), a whole number as an integer ('10.0' -> '10')",
              ("110.00" in tx) == (110.0 in rates) and all(("%.2f" % x) in tx for x in rates) and "10.0" not in tx, "(text withheld)")
        pages = re.findall(rb"stream\n(.*?)\nendstream", data, re.S)
        over = []
        for pi, st in enumerate(pages):
            runs = []
            for f, sz, x, y, s in re.findall(rb"BT /(F\d) ([\d.]+) Tf 0 g ([\d.-]+) ([\d.-]+) Td \((.*?)(?<!\\)\) Tj ET", st):
                s = s.decode("cp1252").replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\")
                sz, x, y = float(sz), float(x), float(y)
                w = SP.width(s, sz, f == b"F2")
                runs.append((x, y - 0.22 * sz, x + w, y + 0.75 * sz))
            for i in range(len(runs)):
                for j in range(i + 1, len(runs)):
                    p, q = runs[i], runs[j]
                    if p[0] < q[2] - 0.01 and q[0] < p[2] - 0.01 and p[1] < q[3] - 0.01 and q[1] < p[3] - 0.01:
                        over.append((pi, i, j))
        mb = re.findall(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", data)
        check("no two text runs overlap (%d pages, every run's box from its x, y and width); A4 landscape" % len(pages),
              not over and mb and all(float(w_) > float(h_) for w_, h_ in mb), (over[:3], mb[:1]))
        n0 = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s454_marg_pdf_printed'").fetchone()[0]
        rr = []
        for u in ("shavez", "manoj"):
            s, h, hd = GET(u, "/finance/porders/s454/marg.pdf")
            rr.append((u, s, hd.get("Content-Type"), h[:5] == b"%PDF-"))
        n1 = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='s454_marg_pdf_printed'").fetchone()[0]
        check("C: the route /finance/porders/s454/marg.pdf: 200, application/pdf for shavez and manoj; one audit row each", all(x[1:] == (200, "application/pdf", True) for x in rr)
              and n1 - n0 == 2, (rr, n1 - n0))
        p = W["fpath"]
        os.rename(p, p + ".w543")
        try:
            d2 = MP.build(c)
            s, h, _ = GET("shavez", "/finance/porders/s454/marg.pdf")
            t2 = SP.text_of(d2)
            check("no file on the server: the one-page 'Marg ka order abhi server par nahi hai ...' PDF, 200",
                  len(re.findall(rb"/Type /Page ", d2)) == 1 and any("Marg ka order abhi server par nahi hai" in x for x in t2) and s == 200, t2[:2])
        finally:
            os.rename(p + ".w543", p)
        sm = re.findall(rb"/MediaBox \[0 0 ([\d.]+) ([\d.]+)\]", W.get("sheet_pdf") or b"")
        check("the sheet's own PDF still A4 portrait (595.28 x 841.89)", sm and all(x == (b"595.28", b"841.89") for x in sm), sm[:1])
        c.close()
    section("7  Marg's PDF", s7)

    # ============================================================================================ 8
    def s8():
        reset()
        c = conn()
        sid = newest(c)
        uid, cid = lid(c, UPRISE), lid(c, COCYP)
        s, j = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=uid))
        st = c.execute("SELECT state FROM order_sheet_line WHERE id=?", (uid,)).fetchone()[0]
        es = [e["sn"] for e in OS.entries(c)]
        check("8 UPRISE (old, never ordered here) -> 'Dobara order karo' 200, to_order, a card for Radha", s == 200 and st == "to_order" and "RADHA MEDICAL & SCIENTIFIC" in es, (s, j, st))
        s, j = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=cid))
        check("COCYP (ordered here, in old) -> refused 409", s == 409, (s, j))
        now = dt.datetime.now().replace(microsecond=0).isoformat()
        e1 = ins(c, "order_sheet_line", dict(entry_no="OP-W5436", item_printed="W543 EDIT LINE", item="W543 EDIT LINE", resolved=1, supplier="W543 WALK SUPPLIER",
                                             supplier_norm="W543 WALK SUPPLIER", packing="1*1", pack_size=1, line_date="2026-10-01", qty_raw="1", qty=1,
                                             kind="new", state="lapsed", first_sheet=sid, last_sheet=sid, created_at=now))
        e2 = ins(c, "order_sheet_line", dict(entry_no="OP-W5437", item_printed="W543 EDIT LINE 2", item="W543 EDIT LINE 2", resolved=1, supplier="W543 WALK SUPPLIER",
                                             supplier_norm="W543 WALK SUPPLIER", packing="1*1", pack_size=1, line_date=today.isoformat(), qty_raw="1", qty=1,
                                             kind="new", state="to_order", first_sheet=sid, last_sheet=sid, created_at=now))
        for i, it in ((e1, "W543 EDIT LINE"), (e2, "W543 EDIT LINE 2")):
            c.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES ('sheet', ?, ?, NULL, 1, 'w543walk', ?)", (str(i), it, now))
        c.commit()
        s, h, _ = GET("shavez", "/finance/porders/s454/old")
        b1, b2 = block_of(h, e1), block_of(h, e2)
        s1_, j1 = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=e1))
        s2_, j2 = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=e2))
        check("C: a line removed by an edit (lapsed) shows no button and its door refuses it (409)", s1_ == 409 and (b1 is None or "reorder" not in b1), (s1_, j1))
        check("a to_order line removed by an edit shows no button and is refused (409)", s2_ == 409 and (b2 is None or "reorder" not in b2), (s2_, j2))
        off = c.execute("SELECT id FROM order_sheet_line WHERE state='old' AND last_sheet<>? ORDER BY id LIMIT 1", (sid,)).fetchone()
        s, j = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=off[0])) if off else (None, {})
        check("C: a line off Marg's export -> 409 'Yeh line ab Marg ke order mein nahi hai.'", s == 409 and j.get("message") == "Yeh line ab Marg ke order mein nahi hai.", (s, j))
        mo = set(maal_oracle(c))
        ln = c.execute("SELECT id FROM order_sheet_line WHERE last_sheet=? AND state='ordered' AND order_id IN (%s) LIMIT 1" % ",".join(str(x) for x in (mo or {0})), (sid,)).fetchone()
        s, j = POST("shavez", "/finance/porders/api/s454/reorder", dict(line=ln[0])) if ln else (409, {})
        check("a line whose order is under 'Maal aaya?' -> 409 (R3-17)", s == 409, (s, j))
        c.close()
    section("8  reorder: the door and the screen agree", s8)

    # ============================================================================================ 10
    def s10():
        reset()
        c = conn()
        for tag in ("install-day", "removed-edit line"):
            if tag == "removed-edit line":
                sid = newest(c)
                now = dt.datetime.now().replace(microsecond=0).isoformat()
                l1 = ins(c, "order_sheet_line", dict(entry_no="OP-W5438", item_printed="W543 MAP A", item="W543 MAP A", resolved=1, supplier="W543 WALK SUPPLIER",
                                                     supplier_norm="W543 WALK SUPPLIER", packing="1*1", pack_size=1, line_date=today.isoformat(), qty_raw="1", qty=1,
                                                     kind="new", state="to_order", first_sheet=sid, last_sheet=sid, created_at=now))
                l2 = ins(c, "order_sheet_line", dict(entry_no="OP-W5439", item_printed="W543 MAP B", item="W543 MAP B", resolved=1, supplier="W543 WALK SUPPLIER 2",
                                                     supplier_norm="W543 WALK SUPPLIER 2", packing="1*1", pack_size=1, line_date=today.isoformat(), qty_raw="1", qty=1,
                                                     kind="new", state="to_order", first_sheet=sid, last_sheet=sid, created_at=now))
                c.execute("INSERT INTO s454_line_edit (src, ref, item, qty, removed, by, at) VALUES ('sheet', ?, 'W543 MAP B', NULL, 1, 'w543walk', ?)", (str(l2), now))
                c.commit()
                _ = l1
            py_o, py_m = PS.counts(c)["order"], len(PS.maal_orders(c))
            r = {}
            for m, nm in ((m12, "v12"), (m13, "v13")):
                r[nm] = (run_sql(due(m, "reception.medicine_orders"))[0], run_sql(due(m, "reception.order_arrival"))[0],
                         run_sql(floored_sql(m, "reception.medicine_orders"), True)[0], run_sql(floored_sql(m, "reception.order_arrival"), True)[0])
            say("   %s: the screen: Order karna hai %d, Maal aaya? %d · v12 %s · v13 %s (plain, plain, floored, floored)" % (tag, py_o, py_m, r["v12"], r["v13"]))
            check("10 %s: v13's two counts = the screen's, on the plain connection and through aaj_kaam's floored reader" % tag,
                  r["v13"] == (py_o, py_m, py_o, py_m), (py_o, py_m, r["v13"]))
        check("the control: with a removed-edit line v12's medicine_orders counts it (%d), v13 does not" % r["v12"][0], r["v12"][0] == r["v13"][0] + 1, r)
        c.close()
    section("10 the map agrees with the screens", s10)

    # ============================================================================================ 11 + staff-eye
    def s11():
        reset()
        c = conn()
        o1 = OS.cron_pass(c, "w543")
        o2 = OS.cron_pass(c, "w543")
        check("order_sheet.cron_pass twice: no error; the second pass changes nothing (refresh %s, heal %s)" % (o2.get("refresh"), o2.get("heal", "-")),
              not any("error" in str(v) for v in list(o1.values()) + list(o2.values())) and o2.get("refresh") == 0 and o2.get("heal", 0) == 0, (o1, o2))
        ds = OS.day_summary(c)
        check("day_summary answers (n %s, unsent %s)" % (ds.get("n"), ds.get("unsent")), ds.get("ok") is True, ds)
        dc = OS.darpan_card(c)["sheet"]
        check("C: darpan_card counts the sheet he sent as reception does: %s dawa · %s supplier (= %d / %d)" % (dc and dc["dawa"], dc and dc["suppliers"], W["count"], W["sups"]),
              dc and (dc["dawa"], dc["suppliers"]) == (W["count"], W["sups"]), dc)
        ol = OS.owner_lines(c)
        import porders                                        # noqa: PLC0415
        ol2 = porders._s454_owner_lines(c)
        check("order_sheet.owner_lines (and through porders) answers a list (%d / %d lines)" % (len(ol), len(ol2)), isinstance(ol, list) and isinstance(ol2, list))
        n0 = c.execute("SELECT COUNT(*) FROM order_sheet").fetchone()[0]
        sys.path.insert(0, a.marg)
        try:
            import marg_take                                  # noqa: PLC0415
            s_ = c.execute("SELECT md5, name, source, stamp FROM order_sheet WHERE id=?", (newest(c),)).fetchone()
            marg_take._order_sheet(dbp, W["fpath"], s_[0], s_[1], s_[2], s_[3])
            ok_mt = True
        except Exception as e:                                # noqa: BLE001
            ok_mt = "raised %s" % type(e).__name__
        n1 = c.execute("SELECT COUNT(*) FROM order_sheet").fetchone()[0]
        check("marg_take._order_sheet on a file already loaded: 'already', nothing added (%d sheets)" % n1, ok_mt is True and n1 == n0, ok_mt)
        cnt = PS.counts(c)
        s, h, _ = GET("shavez", "/finance/porders")
        rows_ok = all(("id=\"row_%s\"" % k).encode() in h for k in ("order", "maal", "scan", "q") if cnt[k] > 0)
        check("/finance/porders (home) as shavez: 200, its rows the counts %s" % cnt, s == 200 and rows_ok, s)
        s, h, _ = GET("shavez", "/finance/porders/api/s454/state")
        j = json.loads(h.decode("utf-8")) if s == 200 else {}
        check("/finance/porders/api/s454/state as shavez: 200, the same counts", s == 200 and j.get("counts") == cnt, (s, j.get("counts")))
        lines = [dict(item="DYNAPAR QPS PLUS", packs=10, pack_size=1), dict(item="RYCOBAL D3", packs=10, pack_size=10), dict(item="CCM", packs=3, pack_size=40)]
        raw_ = c.execute("SELECT value FROM setting WHERE key='stock.whole_unit_items'").fetchone()
        qw.set_whole_units(json.loads(raw_[0]) if raw_ and str(raw_[0]).startswith("[") else [])
        body = []
        for l in lines:
            body.append("%s — %s" % (l["item"], qw.words(int(l["packs"]) * (int(l["pack_size"] or 1) if int(l["pack_size"] or 1) > 1 else 1), pack=int(l["pack_size"] or 1), name=l["item"])))
        want = pa.WA_HEADER + "\n\n" + "\n".join(body)
        check("wa_body for a made-up card is byte-identical to today's text (the supplier's message unchanged)", OS.wa_body(c, lines, "W543") == want)
        heavy = [(u, p, round(t_, 2), n) for u, p, t_, n in TIMES if (t_ >= 2.0 or n >= 100000) and not p.endswith(".pdf")]
        check("every staff page the walk opened: under 100 KB and under 2 s (%d reads)" % len([x for x in TIMES if not x[1].endswith(".pdf")]), not heavy, heavy[:4])
        # the staff-eye walk (CLAUDE.md, S444): every login the kit affects -- the tile on the portal home, the door's marker while due
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u in %r: out[u]=[t['name'] for g, ts in po._visible_sections('staff', False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, list(RECEPTION)))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w543-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        check("staff-eye: the 'Purchase orders' tile on the portal home of %s (the real portal.py + the grants file)" % ", ".join(RECEPTION),
              all("Purchase orders" in tiles.get(u, []) for u in RECEPTION), (tiles and {u: ("Purchase orders" in v) for u, v in tiles.items()}, pp.stdout[-200:]))
        n13 = run_sql(due(m13, "reception.order_arrival"))[0]
        miss = []
        for u in RECEPTION:
            s, h, _ = GET(u, "/finance/porders")
            if s != 200 or (n13 > 0 and "Maal aaya?" not in text(h)):
                miss.append((u, s))
        check("staff-eye: the door /finance/porders shows 'Maal aaya?' to every reception login while v13's order_arrival is due (n %d)" % n13, n13 > 0 and not miss, miss)
        s, h, _ = GET("alisha", "/finance/aaj/api/list")
        try:
            jj = json.loads(h.decode("utf-8"))
            rr = [x for sec in (jj.get("sections") or []) for x in sec.get("rows") or [] if x.get("id") == "reception.order_arrival"]
        except ValueError:
            rr = []
        check("staff-eye: Aaj ka kaam (alisha) carries 'Maal aaya hai: supplier ka bill scan kijiye' while it is due", s == 200 and (len(rr) == 1 or n13 == 0), (s, rr[:1]))
        c.close()
    section("11 not broken (and the staff-eye walk)", s11)

    # ============================================================================================ 12
    def s12():
        hits = {}
        callers = []
        for f in sorted(glob.glob(os.path.join(fin, "*.py"))):
            try:
                src = open(f, encoding="utf-8", errors="replace").read().splitlines()
            except OSError:
                continue
            for i, ln in enumerate(src, 1):
                for pat in ("old_visible", "old_done_days", "old_show_days", "qty_text(", "line_qty_text(", "_qty_of_order_line", "_sheet_of_order("):
                    if pat in ln:
                        hits.setdefault(pat, []).append("%s:%d" % (os.path.basename(f), i))
                if "FROM order_sheet_line WHERE state='to_order'" in ln:
                    hits.setdefault("FROM order_sheet_line WHERE state='to_order'", []).append("%s:%d" % (os.path.basename(f), i))
                if "newest_sheet(" in ln and "def newest_sheet" not in ln:
                    callers.append("%s:%d" % (os.path.basename(f), i))
        allowed = [x for x in hits.get("FROM order_sheet_line WHERE state='to_order'", [])]
        refresh_ok = len(allowed) <= 1 and all(x.startswith("order_sheet.py:") for x in allowed)
        rest = {k: v for k, v in hits.items() if k != "FROM order_sheet_line WHERE state='to_order'"}
        say("   12 greps: %s" % ({k: v for k, v in hits.items()} or "empty"))
        check("C: 12 the retired names are gone from every file (old_visible, old_done_days/old_show_days, qty_text(, line_qty_text(, _qty_of_order_line); "
              "'FROM order_sheet_line WHERE state='to_order'' only in refresh", not rest and refresh_ok, rest)
        say("   newest_sheet( callers: %s" % ", ".join(callers))
    section("12 greps", s12)

    # ---------------------------------------------------------------- the end
    raw.close()
    for p in (pristine,):
        try:
            os.remove(p)
        except OSError:
            pass
    leak = re.search(r"\d{10}", "\n".join(OUT))
    check("static: the walk's own output holds no run of 10 digits", not leak)
    red = len(FAILS)
    if a.expect_red:
        cr = [l for l, ok in CTRL if not ok]
        cg = [l for l, ok in CTRL if ok]
        for l in cr:
            say("  RED on the old files: " + l[:150])
        if CTRL and not cg:
            say("WALK OK negative control: every one of the %d 'C:' checks is red on the old files (%d of %d checks red)" % (len(CTRL), red, RUN[0]))
            return 0
        say("NEGATIVE CONTROL FAILED: %d 'C:' checks stayed green on the old files: %s" % (len(cg), "; ".join(x[:80] for x in cg)))
        return 1
    if FAILS:
        say("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    say("WALK OK S543: %d checks green (one-to-one with Marg, the named lines, Marg's word, no guess, drafts, units, Marg's PDF, reorder, heal, "
        "the map, not broken, staff-eye, greps)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
