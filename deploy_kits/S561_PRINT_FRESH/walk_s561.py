#!/usr/bin/env python3
"""walk_s561.py -- kit S561_PRINT_FRESH (15-Oct-2026). Runs on a SCRATCH folder and SCRATCH databases only.
    python3 -B walk_s561.py --fin <scratch copy of /root/finance with the files under test> --old <a folder with the OLD order_sheet_pdf.py>
                            --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config> --map <DUTY_MAP.json> [--expect-red]
Rows by key (the newest sheet by the one rank, the duties by id), never by counting; the made-up sheet's lines are named W561 and carry no
phone number; no export cell and no PDF text is printed (only what the checks name); the walk's own output is checked for a run of 10 digits.
  1  THE BUTTONS: /s454/order for every reception login and the owner -- both links carry s=<the newest stamp>, &amp;t=<the server's moment>
     and data-fresh; two fixed moments give two different t; the click script once; S543's marg.pdf link re-checked as 'marg.pdf?s='.
  2  THE ROUTES: with the clock fixed, the same bytes with any s / t or none; 200; the file names from the newest sheet's stamp (read here, not
     typed) and the fixed moment; Cache-Control no-store, max-age=0 / Pragma no-cache / Expires 0; the audit rows carry the file name.
  3  NO SHEET (a copy with no order_sheet rows) and NO STAMP (every stamp ''): the names fall back to the fixed moment -- ORDER_TODAY set
     to another day changes nothing (one clock).
  4  THE PRINTED TIME: 'chhapa: <the fixed moment>  ·  Sanjeevni' once on every page; the heading line byte for byte as the OLD file draws
     it; the pages and the rows on each page as the OLD file's, for the install-day sheet and a made-up sheet of 120 lines; every row's
     bottom at or above the foot's top; the printed time inside the foot's room, above the bottom margin; no two text runs overlap.
  5  STAFF-EYE (CLAUDE.md, S444): the 'Purchase orders' tile on the portal home of every reception login; the door /finance/porders shows each
     of their duties' marker while its due_sql says it is due.
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import copy
import datetime as dt
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

KIT = "S561_PRINT_FRESH"
BASE = "https://followup.dr-manoj.in"
ROLE = {"darpan": "staff", "shavez": "manager", "shivani": "staff", "alisha": "staff", "reception": "staff", "manoj": "doctor"}
RECEPTION = ("darpan", "shavez", "shivani", "alisha", "reception")
NEWEST_SQL = "SELECT id, stamp FROM order_sheet ORDER BY COALESCE(NULLIF(stamp,''),'0') DESC, taken_at DESC, id DESC LIMIT 1"
STAMP = re.compile(r"^(\d{4})(\d\d)(\d\d)-(\d\d)(\d\d)")
OLD_SHEETPDF = "d0735df84f17a67474bc0cecd58e5c6c"
SHEET, MARG = "/finance/porders/s454/sheet.pdf", "/finance/porders/s454/marg.pdf"
RUN, FAILS, CTRL, OUT = [0], [], [], []
TXT = re.compile(rb"BT /(F\d) ([\d.]+) Tf 0 g ([\d.-]+) ([\d.-]+) Td \((.*?)(?<!\\)\) Tj ET")


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


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def pages_of(pdf):
    return re.findall(rb"stream\n(.*?)\nendstream", pdf, re.S)


def runs_of(stream):
    out = []
    for f, sz, x, y, s in TXT.findall(stream):
        out.append((f, float(sz), float(x), float(y), s.decode("cp1252").replace("\\(", "(").replace("\\)", ")").replace("\\\\", "\\")))
    return out


def app_env(a, dbp):
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map), FINANCE_SSO_DIR=os.path.join(os.path.dirname(dbp), "nosso"),
                      RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)


def page_look(a, fin, dbp):
    """After placing: the placed files (a copy of /root/finance) on a copy of the live database, the walk's own header session (no live
    secret), the real clock -- the order sheet's file name and its printed time, Marg's PDF's name, the buttons' address."""
    app_env(a, dbp)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    cl = fa.app.test_client(use_cookies=False)
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    r = c.execute(NEWEST_SQL).fetchone()
    c.close()
    st = str(r[1] or "") if r else ""
    m = STAMP.match(st)
    exp = ("%s-%s_%s%s" % (m.group(3), m.group(2), m.group(4), m.group(5))) if m else None
    hd = {"X-Clinic-User": "shavez", "X-Clinic-Role": "manager"}
    t0 = dt.datetime.now().replace(microsecond=0)
    rs = cl.get(SHEET + "?s=%s&t=%s" % (st, t0.strftime("%Y%m%d%H%M%S")), base_url=BASE, headers=hd)
    rm = cl.get(MARG, base_url=BASE, headers=hd)
    ro = cl.get("/finance/porders/s454/order", base_url=BASE, headers=hd)
    t1 = dt.datetime.now().replace(microsecond=0)
    fs = re.search(r'filename="(order_sheet_(\d\d-\d\d_\d{4})_(\d{6})\.pdf)"', rs.headers.get("Content-Disposition") or "")
    fm = re.search(r'filename="(marg_order_(\d\d-\d\d_\d{4})\.pdf)"', rm.headers.get("Content-Disposition") or "")
    okt = fs and t0.strftime("%H%M%S") <= fs.group(3) <= t1.strftime("%H%M%S") and (fs.group(2) == exp if exp else True)
    mins = {(t0 + dt.timedelta(seconds=k)).strftime("%d-%m-%Y %H:%M") for k in range(0, int((t1 - t0).total_seconds()) + 1)}
    tx = [s for stv in pages_of(rs.get_data()) for (_f, _z, _x, _y, s) in runs_of(stv)]
    ch = [s for s in tx if s.startswith("chhapa: ")]
    okc = ch and all(s[8:24] in mins and s.endswith("  ·  Sanjeevni") for s in ch) and len(ch) == len(pages_of(rs.get_data()))
    okm = fm and (fm.group(2) == exp if exp else True)
    btn = b'href="/finance/porders/s454/sheet.pdf?s=' in ro.get_data() and b'data-fresh="1"' in ro.get_data()
    say("   /finance/porders/s454/sheet.pdf (shavez, the placed files, a copy of the database, read %s): %s, %s, 'chhapa' on %d of %d page(s)"
        % (t0.strftime("%H:%M:%S"), rs.status_code, fs.group(1) if fs else rs.headers.get("Content-Disposition"), len(ch), len(pages_of(rs.get_data()))))
    say("   /finance/porders/s454/marg.pdf: %s, %s" % (rm.status_code, fm.group(1) if fm else rm.headers.get("Content-Disposition")))
    say("   /finance/porders/s454/order: %s, the buttons carry ?s=...&t=... and data-fresh: %s" % (ro.status_code, btn))
    ok = rs.status_code == 200 and rm.status_code == 200 and ro.status_code == 200 and okt and okc and okm and btn
    leak = re.search(r"\d{10}", "\n".join(OUT))
    say(("PAGE OK S561" if ok and not leak else "PAGE RED S561") + ": the new file names and the printed time (export %s)" % (exp or "none"))
    return 0 if ok and not leak else 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--old", "--portal"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true", help="after placing: the placed files (copied) on a copy of the database, the real clock")
    a = ap.parse_args()
    if not a.page and not (a.old and a.portal):
        ap.error("--old and --portal are needed for the walk")
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S561_WALK_ANYWHERE") == "1"
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)) + (() if a.page else (os.path.abspath(a.old),)):
        assert p.startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.page:
        return page_look(a, fin, dbp)
    say("-- S561 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    app_env(a, dbp)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    import order_sheet_pdf as SP                              # noqa: E402
    import porders_s454 as PS                                 # noqa: E402
    assert OS.__file__.startswith(fin) and PS.__file__.startswith(fin) and SP.__file__.startswith(fin), (OS.__file__, PS.__file__)
    op = os.path.join(os.path.abspath(a.old), "order_sheet_pdf.py")
    assert hashlib.md5(open(op, "rb").read()).hexdigest() == OLD_SHEETPDF, "--old must hold the OLD order_sheet_pdf.py (d0735df8)"
    spec = importlib.util.spec_from_file_location("order_sheet_pdf_s561old", op)
    SPO = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(SPO)
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    cl = fa.app.test_client(use_cookies=False)
    TIMES = []

    def GET(u, path):
        t0 = time.time()
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        TIMES.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data(), r.headers

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c
    pristine = dbp + ".pristine"
    copydb(dbp, pristine)

    def reset():
        copydb(pristine, dbp)

    today = dt.date.today()
    FIX1 = dt.datetime.combine(today, dt.time(14, 31, 7))
    FIX2 = dt.datetime.combine(today, dt.time(14, 33, 52))
    CLOCK = [FIX1]
    real_now = OS.now
    OS.now = lambda: CLOCK[0]                                 # the one clock, fixed for the walk (order_sheet.now -- every caller reads it)
    W = {}

    def section(name, fn):
        say("-- " + name)
        try:
            fn()
        except Exception as e:                                # noqa: BLE001 -- a section that raises is red, the walk goes on
            import traceback                                  # noqa: PLC0415
            tb = traceback.format_exc().strip().splitlines()
            check("C: section '%s' ran to its end" % name.split()[0], False, "%s: %s | %s" % (type(e).__name__, str(e)[:160], " / ".join(x.strip() for x in tb[-4:])[:300]))

    def newest_stamp():
        c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        try:
            r = c.execute(NEWEST_SQL).fetchone()
        finally:
            c.close()
        return (r[0], str(r[1] or "")) if r else (None, "")

    def names_for(st, n):
        m = STAMP.match(st or "")
        base = ("%s-%s_%s%s" % (m.group(3), m.group(2), m.group(4), m.group(5))) if m else n.strftime("%d-%m_%H%M")
        return "order_sheet_%s_%s.pdf" % (base, n.strftime("%H%M%S")), "marg_order_%s.pdf" % base

    def tag(h, ident):
        m = re.search(r'<a [^>]*id="%s"[^>]*>' % ident, h.decode("utf-8", "replace"))
        return m.group(0) if m else ""

    def href(t):
        m = re.search(r'href="([^"]*)"', t)
        return m.group(1) if m else ""

    # ============================================================================================ the install-day state
    c = conn()
    OS.ensure(c)
    sid, st = newest_stamp()
    import order_rules                                        # noqa: PLC0415
    oo = OS.open_order(c)
    frozen = bool(order_rules._frozen(c))
    pend = [e for e in OS.entries(c) if e["state"] != "in_line"]
    W["sid"], W["st"] = sid, st
    say("   install-day state: newest sheet id %s, its stamp %s (%s); order.source %s; ordering frozen: %s; Marg's open order %d line(s), %d supplier(s); "
        "suppliers still to order %d -> both PDF buttons %s" % (sid, st or "''", "the export's shape" if STAMP.match(st) else "no stamp", OS.source(c), frozen,
                                                                oo["count"], oo["suppliers"], len(pend), "shown" if (not frozen and (pend or oo["count"])) else "NOT shown"))
    c.close()
    sname, mname = names_for(st, FIX1)
    W["sname"], W["mname"] = sname, mname

    # ============================================================================================ 1
    def s1():
        want_q = {k: "s=%s&amp;t=%s" % (st if STAMP.match(st) else "", k.strftime("%Y%m%d%H%M%S")) for k in (FIX1, FIX2)}
        bad, seen_t, scripts, recheck = [], {}, {}, {}
        for u in RECEPTION + ("manoj",):
            for k in (FIX1, FIX2):
                CLOCK[0] = k
                s, h, hd = GET(u, "/finance/porders/s454/order")
                tp, tm = tag(h, "print"), tag(h, "margpdf")
                ok = (s == 200 and href(tp) == "/finance/porders/s454/sheet.pdf?" + want_q[k] and href(tm) == "/finance/porders/s454/marg.pdf?" + want_q[k]
                      and 'data-fresh="1"' in tp and 'data-fresh="1"' in tm and 'target="_blank"' in tp and 'target="_blank"' in tm)
                if not ok:
                    bad.append((u, k.strftime("%H:%M:%S"), s, bool(tp), bool(tm)))
                mt = re.search(r"[?&]t=(\d+)", _html.unescape(href(tp)))
                seen_t.setdefault(u, []).append(mt.group(1) if mt else None)
                scripts[u] = h.count(b"closest('a[data-fresh]')")
                recheck[u] = b'href="/finance/porders/s454/marg.pdf?s=' in h
                if u == "manoj" and k == FIX1:
                    W["en_words"] = ("Print the order sheet" in text(h)) and ("Marg's order (PDF)" in text(h))
                if u == "shavez" and k == FIX1:
                    W["hi_words"] = ("Order sheet print karo" in text(h)) and ("Marg ka order (PDF)" in text(h))
                    W["no_store"] = hd.get("Cache-Control") == "no-store"
        CLOCK[0] = FIX1
        check("C: both buttons on /s454/order for %s and manoj carry s=<the newest stamp %s>, &amp;t=<the server's moment>, data-fresh and target=_blank"
              % (", ".join(RECEPTION), st or "''"), not bad, bad[:4])
        diff = {u: v for u, v in seen_t.items() if not (len(v) == 2 and v[0] and v[1] and v[0] != v[1])}
        check("C: two fixed moments (14:31:07, 14:33:52) give two different t on each login's page", not diff, {u: [x and x[8:] for x in v] for u, v in diff.items()})
        check("C: the click script (sets t to the tap's moment on a[data-fresh]) is on the page exactly once, for every login",
              scripts and all(n == 1 for n in scripts.values()), scripts)
        check("C: S543's marg.pdf link re-checked as href=\"/finance/porders/s454/marg.pdf?s=\" (walk_s543.py 353)", recheck and all(recheck.values()), recheck)
        check("the same words on the buttons: 'Order sheet print karo' / 'Marg ka order (PDF)' (shavez), 'Print the order sheet' / \"Marg's order (PDF)\" (manoj); the page no-store",
              W.get("hi_words") and W.get("en_words") and W.get("no_store"), (W.get("hi_words"), W.get("en_words"), W.get("no_store")))
        other = [x for x in re.findall(r'<a [^>]*href="[^"]*"[^>]*>', GET("shavez", "/finance/porders/s454/order")[1].decode("utf-8", "replace"))
                 if "data-fresh" in x and 'id="print"' not in x and 'id="margpdf"' not in x]
        check("no other link on the page got data-fresh", not other, other[:2])
    section("1  the two buttons", s1)

    # ============================================================================================ 2
    def s2():
        CLOCK[0] = FIX1
        res = {}
        for path, want in ((SHEET, sname), (MARG, mname)):
            got = []
            for q in ("", "?s=%s&t=%s" % (st, FIX1.strftime("%Y%m%d%H%M%S")), "?s=W561&t=123", "?t=1&s="):
                for u in ("shavez", "manoj"):
                    s, b, hd = GET(u, path + q)
                    got.append((s, b, hd.get("Content-Disposition"), hd.get("Cache-Control"), hd.get("Pragma"), hd.get("Expires"), hd.get("Content-Type")))
            res[path] = got
            same = len({g[1] for g in got}) == 1
            check("%s: 200, application/pdf and the same bytes with no query, with s/t, with a wrong s and a short t (8 reads, shavez and manoj)" % path.rsplit("/", 1)[1],
                  same and all(g[0] == 200 and g[6] == "application/pdf" and g[1][:5] == b"%PDF-" for g in got), (same, [g[0] for g in got]))
            check("C: %s names the file '%s' (the newest sheet's stamp %s and the fixed moment 14:31:07)" % (path.rsplit("/", 1)[1], want, st or "''"),
                  all(g[2] == 'inline; filename="%s"' % want for g in got), got[0][2])
            check("C: %s sends Cache-Control 'no-store, max-age=0', Pragma 'no-cache', Expires '0'" % path.rsplit("/", 1)[1],
                  all(g[3:6] == ("no-store, max-age=0", "no-cache", "0") for g in got), got[0][3:6])
        W["sheet_pdf"] = res[SHEET][0][1]
        c = conn()
        aud = {}
        for action, want in (("s454_sheet_printed", sname), ("s454_marg_pdf_printed", mname)):
            r = c.execute("SELECT detail FROM purchase_audit WHERE action=? ORDER BY id DESC LIMIT 1", (action,)).fetchone()
            try:
                aud[action] = (json.loads(r[0] or "{}").get("file") == want) if r else False
            except ValueError:
                aud[action] = False
        c.close()
        check("C: the audit rows s454_sheet_printed and s454_marg_pdf_printed record the file name", aud and all(aud.values()), aud)
    section("2  the two routes", s2)

    # ============================================================================================ 3
    def s3():
        CLOCK[0] = FIX1
        os.environ["ORDER_TODAY"] = "2031-03-05"                # another day: the names must still follow the one clock
        try:
            reset()
            c = conn()
            c.execute("DELETE FROM order_sheet")               # this scratch copy only (reset below)
            c.commit()
            c.close()
            w_s, w_m = names_for("", FIX1)
            r = [(p, GET("shavez", p)) for p in (SHEET, MARG)]
            check("C: no order_sheet rows: '%s' and '%s' (today's dd-mm and the fixed HHMM; ORDER_TODAY set to another day changes nothing)" % (w_s, w_m),
                  r[0][1][0] == 200 and r[1][1][0] == 200 and r[0][1][2].get("Content-Disposition") == 'inline; filename="%s"' % w_s
                  and r[1][1][2].get("Content-Disposition") == 'inline; filename="%s"' % w_m, [(x[1][0], x[1][2].get("Content-Disposition")) for x in r])
            reset()
            c = conn()
            c.execute("UPDATE order_sheet SET stamp=''")       # older sheets carry '': the same fallback, and s= empty on the buttons
            c.commit()
            c.close()
            r = [(p, GET("shavez", p)) for p in (SHEET, MARG)]
            s, h, _ = GET("shavez", "/finance/porders/s454/order")
            hp = href(tag(h, "print"))
            check("C: every stamp '': the same fallback names and the buttons carry 's=&amp;t='",
                  r[0][1][2].get("Content-Disposition") == 'inline; filename="%s"' % w_s and r[1][1][2].get("Content-Disposition") == 'inline; filename="%s"' % w_m
                  and ("?s=&amp;t=%s" % FIX1.strftime("%Y%m%d%H%M%S")) in hp, [x[1][2].get("Content-Disposition") for x in r] + [bool(hp)])
        finally:
            os.environ.pop("ORDER_TODAY", None)
            reset()
    section("3  no sheet, no stamp (the fallback, one clock)", s3)

    # ============================================================================================ 4
    def build_with(mod, c, lay, n):
        try:
            return mod.build(c, lay, now=n)
        except TypeError:                                     # the OLD file has no now
            return mod.build(c, lay)

    def shape(lay):
        return [[(pc["block"], tuple(pc["rows"]), pc["cont"], pc["only_old_head"]) for pc in pg] for pg in lay["pages"]]

    def geometry(mod, pdf, label):
        """(chhapa count per page, problems) -- every row box's bottom vs the foot's top, the printed time's place, text overlaps."""
        foot_top = mod.BOT + mod._foot_h()
        want = "chhapa: %s  ·  Sanjeevni" % FIX1.strftime("%d-%m-%Y %H:%M")
        per, probs = [], []
        f2 = SP._foot_lines()[1]
        for pi, stream in enumerate(pages_of(pdf), 1):
            runs = runs_of(stream)
            ch = [r for r in runs if r[4] == want]
            per.append(len(ch))
            for y in (float(m) for m in re.findall(rb"0\.50 w 0\.250 G [\d.]+ ([\d.-]+) [\d.]+ [\d.]+ re S", stream)):
                if y < foot_top - 0.01:
                    probs.append("%s p%d: a row's bottom %.2f below the foot's top %.2f" % (label, pi, y, foot_top))
            if ch:
                f2y = min(r[3] for r in runs if r[4] in f2)
                cy = ch[0][3]
                if not (cy >= mod.BOT and cy + 0.75 * 8 < f2y - 0.22 * SP.FOOT2_SZ and ch[0][1] == 8.0 and ch[0][0] == b"F1"):
                    probs.append("%s p%d: the printed time at %.2f (bottom margin %.2f, last foot line %.2f), size %s %s" % (label, pi, cy, mod.BOT, f2y, ch[0][1], ch[0][0]))
            box = []
            for f, sz, x, y, s in runs:
                w = SP.width(s, sz, f == b"F2")
                box.append((x, y - 0.22 * sz, x + w, y + 0.75 * sz))
            for i in range(len(box)):
                for j in range(i + 1, len(box)):
                    p, q = box[i], box[j]
                    if p[0] < q[2] - 0.01 and q[0] < p[2] - 0.01 and p[1] < q[3] - 0.01 and q[1] < p[3] - 0.01:
                        probs.append("%s p%d: text runs %d and %d overlap" % (label, pi, i, j))
        return per, probs

    def s4():
        CLOCK[0] = FIX1
        reset()
        c = conn()
        pdf = W.get("sheet_pdf") or GET("shavez", SHEET)[1]
        per, probs = geometry(SP, pdf, "install-day")
        check("C: the order sheet's foot says 'chhapa: %s  ·  Sanjeevni' exactly once on every page (%d page(s), the route's bytes)"
              % (FIX1.strftime("%d-%m-%Y %H:%M"), len(per)), per and all(n == 1 for n in per), per)
        check("the install-day sheet: every row's bottom at or above the foot's top; the printed time above the bottom margin and under the last foot line, "
              "size 8 regular; no two text runs overlap", not probs, probs[:4])
        lay_n, lay_o = SP.layout(c), SPO.layout(c)
        old_pdf = SPO.build(c)
        hn = [r for r in runs_of(pages_of(pdf)[0]) if r[4] == lay_n["line"]]
        ho = [r for r in runs_of(pages_of(old_pdf)[0]) if r[4] == lay_o["line"]]
        check("the heading line byte for byte as the OLD file's layout line and drawn at the same place and size",
              lay_n["line"] == lay_o["line"] and hn and hn == ho, (lay_n["line"] == lay_o["line"], len(hn), len(ho)))
        np_n, np_o = len(re.findall(rb"/Type /Page ", pdf)), len(re.findall(rb"/Type /Page ", old_pdf))
        check("the install-day sheet: %d page(s) and the same rows on each page as the OLD file (%s)" % (np_n, [sum(len(pc["rows"]) for pc in pg) for pg in lay_n["pages"]]),
              shape(lay_n) == shape(lay_o) and np_n == np_o == len(lay_n["pages"]), (np_n, np_o))
        check("_foot_h and rows_per_page unchanged (%.2f pt, %d rows)" % (SP._foot_h(), SP.rows_per_page()),
              abs(SP._foot_h() - SPO._foot_h()) < 1e-9 and SP.rows_per_page() == SPO.rows_per_page(), (SP._foot_h(), SPO._foot_h()))
        # a made-up sheet of 120 lines: ten suppliers of nine, and thirty old lines of one more (longer than a page: continued)
        blocks = []
        for i in range(10):
            blocks.append(dict(name="W561 SUPPLIER %02d" % (i + 1), phones=[], only_old=False, ticks=dict(whatsapp=False, call=False),
                               rows=[dict(item="W561 ITEM %03d%s" % (i * 9 + j + 1, " EXTRA LONG NAME TO WRAP INSIDE ITS CELL" if j == 4 else ""),
                                          pack="1*10", qty="10 patte", kind=("awaited" if j % 3 == 2 else "new"), ticked=(j % 3 == 2), aaya=False,
                                          marg=True, tag="") for j in range(9)]))
        blocks.append(dict(name="W561 SUPPLIER OLD", phones=[], only_old=True, ticks=dict(whatsapp=False, call=False),
                           rows=[dict(item="W561 OLD %03d" % (k + 1), pack="1*15", qty="2 patte", kind="old", ticked=False, aaya=False, marg=True,
                                      tag="purana, 05-03 · Marg mein baaki") for k in range(30)]))
        made = dict(line="Marg ka khula order: 05-03-2031 10:00  ·  11 supplier  ·  120 dawa: 90 order karna hai, 30 purane pending", date="05-03-2031",
                    blocks=blocks, first_only=10, print_old=True, counts=dict(to_order=90, awaited=0, old=30), marg={})
        mn, mo = copy.deepcopy(made), copy.deepcopy(made)
        SP._measure(mn)
        SPO._measure(mo)
        pn, po_ = build_with(SP, c, mn, FIX1), SPO.build(c, mo)
        nrows = sum(len(b["rows"]) for b in made["blocks"])
        per2, probs2 = geometry(SP, pn, "made-up")
        check("C: the made-up sheet of %d lines: 'chhapa' once on each of its %d pages" % (nrows, len(per2)), nrows == 120 and per2 and all(n == 1 for n in per2), per2)
        np2n, np2o = len(re.findall(rb"/Type /Page ", pn)), len(re.findall(rb"/Type /Page ", po_))
        check("the made-up sheet: %d pages and the same rows on each page as the OLD file (%s); every row's bottom at or above the foot's top; no overlap"
              % (np2n, [sum(len(pc["rows"]) for pc in pg) for pg in mn["pages"]]), shape(mn) == shape(mo) and np2n == np2o and np2n >= 3 and not probs2,
              (np2n, np2o, probs2[:3]))
        c.close()
    section("4  the printed time on the order sheet", s4)

    # ============================================================================================ 5
    def s5():
        CLOCK[0] = FIX1
        reset()
        m = json.load(open(a.map, encoding="utf-8"))
        duties = [d for d in m["duties"] if d.get("person") == "reception" and d.get("door") == "/finance/porders" and d.get("door_marker")]
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u in %r: out[u]=[t['name'] for g, ts in po._visible_sections('staff', False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, list(RECEPTION)))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w561-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        check("staff-eye: the 'Purchase orders' tile on the portal home of %s (the real portal.py + the grants file, a walk-only secret)" % ", ".join(RECEPTION),
              tiles and all("Purchase orders" in tiles.get(u, []) for u in RECEPTION), (tiles and {u: ("Purchase orders" in v) for u, v in tiles.items()}, pp.stdout[-200:]))
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        due = {}
        for d in duties:
            try:
                due[d["id"]] = int(ro.execute(d["due_sql"]).fetchone()[0] or 0)
            except sqlite3.Error as e:
                due[d["id"]] = "error %s" % str(e)[:60]
        ro.close()
        say("   reception duties at the door /finance/porders, due now (their due_sql on this copy): %s" % due)
        miss = []
        for u in RECEPTION:
            s, h, _ = GET(u, "/finance/porders")
            t = text(h)
            for d in duties:
                if s != 200 or (isinstance(due[d["id"]], int) and due[d["id"]] > 0 and d["door_marker"] not in t):
                    miss.append((u, d["id"], s))
        check("staff-eye: the door /finance/porders shows each due duty's marker to every reception login (%s)" % ", ".join(d["door_marker"] for d in duties),
              duties and not miss and all(isinstance(v, int) for v in due.values()), miss[:4])
        heavy = [(u, p, round(t_, 2), n) for u, p, t_, n in TIMES if (t_ >= 2.0 or n >= 100000) and not p.split("?")[0].endswith(".pdf")]
        check("every staff page the walk opened: under 100 KB and under 2 s (%d reads)" % len([x for x in TIMES if not x[1].split("?")[0].endswith(".pdf")]),
              not heavy, heavy[:4])
    section("5  staff-eye", s5)

    # ---------------------------------------------------------------- the end
    OS.now = real_now
    try:
        os.remove(pristine)
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
    say("WALK OK S561: %d checks green (the buttons, the routes, the fallback, the printed time, the layout unchanged, staff-eye)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
