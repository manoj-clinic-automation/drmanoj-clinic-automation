#!/usr/bin/env python3
"""walk_s556.py -- kit S556_REFUSED_TEXT_ROAD (14-Oct-2026, F-893): the server's walk. Runs on SCRATCH copies in /tmp only.
    python3 -B walk_s556.py --fin <scratch copy of /root/finance with the files under test> --old <a folder holding the OLD reports_tile.py,
                            reports_watch.py, order_sheet.py> --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json> --map13 <DUTY_MAP.json v13> --map14 <DUTY_MAP.json v14>
                            [--expect-red]
    python3 -B walk_s556.py --page --fin <scratch copy of the PLACED /root/finance> --db <a COPY of finance.db> --adb ... --marg ... --map14 ...
The walk's own rows are found by their md5 key (W556...), never by counting; times are today's (the map reads SQLite's real date) at fixed
clock times, in the take door's own received_at shape read from a live row. Only state names, times, counts and md5 keys are printed -- never
a rendered staff page or a reason body of a live row.
  0  SETUP (before anything else): today's live mi_file rows of SALE_BILLWISE / STOCK_CLOSING / ORDER_PENDING (and the due day's) and today's
     marg_report_alert rows deleted ON THE COPY (their md5 / keys logged); sale_bill (medical) trimmed below the due day -> v13 sale_report n >= 1;
     the due day's and today's push snapshots deleted -> v13 closing_stock n >= 1; v13 darpan.order_sheet n = 0. Halts on a Sunday.
  1  SALE STOP 09:23 (line 43): held, wrong 0, no loose line; every login granted the reports tile sees the held words and none of Galat hai /
     dobara / koshish in the sale row; manoj also the reader's line; arrived one higher than the OLD file; decide -> one 'reader' item (also
     after the late hour); v14 does not count the due day; Shavez's Aaj ka kaam has no sale line; the owner's line; hindi_reason.
  2  THEN RIGHT 09:40 (a reading in the walk's own readings): Sahi hai, the hold gone; the map's sale_report n = 1 (sale_bill not yet written).
  3  NOT STOPS (each its own run): the page, its rows and decide byte-identical to the OLD file's.
  4  ORDER OF THINGS: stop 09:23 + cut short 09:30 -> held, no loose line; then a VERIFIED SUMMARY1 -> the stop dropped, the cut-short line back,
     the SUMMARY1 a wrong try.
  5  STOCK: (1) for STOCK_CLOSING.
  6  DARPAN: cut short 08:00 + stop 08:05 -> nothing shown, n 0; a stop alone -> his card and the API his page draws from say not refused,
     owner_lines still names it, n 0; a cut-short one -> refused, n 1 (v13 and v14).
  8  the walk's own output holds no run of 10 digits.
--expect-red: the same walk on the OLD files and map v13 (the negative control, 7): every 'C:' check must be red. 'WALK OK S556' on success."""
import argparse
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
import tempfile

KIT = "S556_REFUSED_TEXT_ROAD"
BASE = "https://followup.dr-manoj.in"
RUN, FAILS, CTRL, OUT = [0], [], [], []
STOP43 = "the medical PC refused it: the reader refused it (line 43)"
CUT_SALE = "the medical PC refused it: a bill-wise report, but without the '*** End of Report ***' line at the end (cut short?)"
CUT_ORDER = "the medical PC refused it: an order sheet without the '*** End of Report ***' line at the end (cut short?)"
STOP_ORDER = "the medical PC refused it: the reader refused it (line 21)"
STOP_STOCK = "the medical PC refused it: the reader refused it (line 12)"
NOT_STOPS = [   # (label, type, reason, one-day for the due day)
    ("the bare 'the reader refused it'", "SALE_BILLWISE", "the medical PC refused it: the reader refused it", False),
    ("'(line 4x)'", "SALE_BILLWISE", "the medical PC refused it: the reader refused it (line 4x)", False),
    ("a SALE_SHORT text", "SALE_BILLWISE", "the medical PC refused it: SALE_SHORT text -- the reader refused it (line 4)", False),
    ("cut short", "SALE_BILLWISE", CUT_SALE, False),
    ("TODAY_NOTE", "SALE_BILLWISE", "the medical PC refused it: the reader refused it: aaj ki report -- kal ki tareekh chun kar dobara banaiye", False),
    ("EMPTY_NOTE", "SALE_BILLWISE", "the medical PC refused it: the reader refused it: an empty report -- kept, not yet verified", False),
    ("a PURCHASE text", "", "the medical PC refused it: PURCHASE text -- a purchase statement without the '*** End of Report ***' line at the end (cut short?)", False),
    ("not a report the reader knows", "", "the medical PC refused it: not a report the reader knows", False),
    ("a server refusal", "SALE_BILLWISE", "deep parse failed: truncated", True),
]


def say(s):
    s = re.sub(r"\d{10,}", lambda m: "#" * len(m.group(0)), str(s))
    OUT.append(s)
    print(s, flush=True)


def check(label, cond, got=None):
    RUN[0] += 1
    say(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
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
    con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def load_as(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def row_html(page, label):
    """One morning row's HTML out of a page (from its label to the next row or the card's end)."""
    s = page.decode("utf-8", "replace") if isinstance(page, bytes) else page
    i = s.find("<span class=big>%s</span>" % label)
    if i < 0:
        return ""
    j = s.find("<div class=line>", i + 10)
    k = s.find("</div>", i)
    return s[i:min(x for x in (j, k) if x > 0)] if (j > 0 or k > 0) else s[i:]


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map14"):
        ap.add_argument(k, required=True)
    for k in ("--old", "--portal", "--map13"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg)):
        assert p.startswith("/tmp/") or os.environ.get("S556_WALK_ANYWHERE") == "1", "the walk runs on scratch copies in /tmp only: %s" % p
    tmp = tempfile.mkdtemp(prefix="w556_", dir=os.path.dirname(dbp))
    for d in ("readings", "archive", "off", "nosso"):
        os.makedirs(os.path.join(tmp, d))
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(a.map14), FINANCE_SSO_DIR=os.path.join(tmp, "nosso"),
                      RING_PORTAL_DIR=os.path.join(tmp, "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      SPINE_READINGS=os.path.join(tmp, "readings"), SPINE_DB=os.path.join(tmp, "spine.db"), MI_ARCHIVE=os.path.join(tmp, "archive"),
                      REPORTS_NTFY_STUB=os.path.join(tmp, "ntfy.jsonl"), REPORTS_WATCH_OFF_DIR=os.path.join(tmp, "off"))
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                                  # noqa: E402
    import reports_tile as RT                                 # noqa: E402
    import reports_watch as RW                                # noqa: E402
    import order_sheet as OS                                  # noqa: E402
    assert RT.__file__.startswith(fin) and RW.__file__.startswith(fin) and OS.__file__.startswith(fin), (RT.__file__, OS.__file__)
    assert RT.SPINE_READINGS.startswith(tmp), "the walk's readings folder is not the reports page's"
    cl = fa.app.test_client(use_cookies=False)
    ROLE = {"manoj": "doctor", "shavez": "manager"}

    def GET(u, path):
        r = cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")})
        return r.status_code, r.get_data()

    def conn():
        c = sqlite3.connect(dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    if a.page:                                                # after placing: the two pages on a copy of the placed files
        s1, h1 = GET("shavez", "/finance/reports/aaj")
        s2, h2 = GET("darpan", "/finance/darpan/kal")
        s3, h3 = GET("darpan", "/finance/darpan/kal/api/day?date=%s" % dt.date.today().isoformat())
        say("   /finance/reports/aaj as shavez %s (%d bytes) . /finance/darpan/kal as darpan %s . its api/day %s" % (s1, len(h1), s2, s3))
        ok = s1 == 200 and s2 == 200 and s3 == 200 and b"Aaj ki reports" in h1
        say("PAGE OK" if ok else "PAGE RED")
        return 0 if ok else 1

    say("-- S556 walk on the %s: %s . db %s" % ("OLD files and map v13 (negative control)" if a.expect_red else "new files and map v14", fin,
                                                os.path.basename(dbp)))
    RT0 = load_as("w556_reports_tile_old", os.path.join(a.old, "reports_tile.py"))
    RW0 = load_as("w556_reports_watch_old", os.path.join(a.old, "reports_watch.py"))
    m13 = json.load(open(a.map13, encoding="utf-8"))
    m14 = json.load(open(a.map14, encoding="utf-8"))

    def due(m, did):
        return next(d["due_sql"] for d in m["duties"] if d["id"] == did)

    def nmap(m, did):
        c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        try:
            r = c.execute(due(m, did)).fetchone()
            return int(r[0] or 0), r[1]
        finally:
            c.close()

    # ---------------------------------------------------------------- 0 the clock and the setup
    now_real = RT._now()
    today = now_real.date()
    tiso = today.isoformat()
    c = conn()
    sq = c.execute("SELECT date('now','localtime')").fetchone()[0]
    if not check("0 the clock: SQLite's date('now','localtime') %s is the IST date %s; not a Sunday (decide is quiet then)" % (sq, tiso),
                 sq == tiso and today.weekday() != 6):
        say("WALK RED: the clock -- halted")
        return 1
    y = RT._due_day(today)
    yiso = y.isoformat()
    sample = c.execute("SELECT received_at FROM mi_file WHERE verdict='VERIFIED' AND source<>'' ORDER BY received_at DESC LIMIT 1").fetchone()
    sample = str(sample[0]) if sample else "2026-01-01T00:00:00+05:30"
    sep, tail = (sample[10], sample[19:]) if len(sample) >= 19 else ("T", "+05:30")
    say("   today %s, the due day %s; the door's received_at shape '<date>%s<time>%s' (read from a live row)" % (tiso, yiso, sep, tail))

    def at(h, m, s=0, micro=False):
        return "%s%s%02d:%02d:%02d%s%s" % (tiso, sep, h, m, s, ".123456" if micro else "", tail)

    def clock(h, m):
        return dt.datetime(today.year, today.month, today.day, h, m, tzinfo=RT.IST)
    gone = c.execute("SELECT substr(md5,1,8), type FROM mi_file WHERE type IN ('SALE_BILLWISE','STOCK_CLOSING','ORDER_PENDING') AND "
                     "(substr(received_at,1,10)=? OR substr(date_from,1,10)>=?)", (tiso, yiso)).fetchall()
    c.execute("DELETE FROM mi_file WHERE type IN ('SALE_BILLWISE','STOCK_CLOSING','ORDER_PENDING') AND (substr(received_at,1,10)=? OR substr(date_from,1,10)>=?)",
              (tiso, yiso))
    alerts = c.execute("SELECT key FROM marg_report_alert WHERE day=?", (tiso,)).fetchall() if RT._table_exists(c, "marg_report_alert") else []
    if alerts:
        c.execute("DELETE FROM marg_report_alert WHERE day=?", (tiso,))
    nsb = c.execute("SELECT COUNT(*) FROM sale_bill WHERE unit='medical' AND business_date>=?", (yiso,)).fetchone()[0]
    c.execute("DELETE FROM sale_bill WHERE unit='medical' AND business_date>=?", (yiso,))
    asons = (y.strftime("%d-%m-%Y"), today.strftime("%d-%m-%Y"))
    nsf = c.execute("SELECT COUNT(*) FROM stock_feed WHERE source LIKE 'push_snapshot%' AND as_on IN (?,?)", asons).fetchone()[0]
    c.execute("DELETE FROM stock_feed WHERE source LIKE 'push_snapshot%' AND as_on IN (?,?)", asons)
    nst = 0
    if RT._table_exists(c, "marg_push_staging"):              # the older pushed-report door proves arrival of the due day's sale: cleared too
        nst = c.execute("SELECT COUNT(*) FROM marg_push_staging WHERE substr(received_at,1,10)=? OR survey_json LIKE ?",
                        (tiso, '%"' + yiso + '"%')).fetchone()[0]
        c.execute("DELETE FROM marg_push_staging WHERE substr(received_at,1,10)=? OR survey_json LIKE ?", (tiso, '%"' + yiso + '"%'))
    c.commit()
    c.close()
    say("   setup on the copy: %d mi_file rows of the three types removed (%s); %d alert row(s) of today (%s); %d sale_bill rows from the due day; "
        "%d push-snapshot rows; %d pushed-report staging rows of the due day or today" % (
            len(gone), ", ".join("%s %s" % (r[0], r[1]) for r in gone) or "none", len(alerts), ", ".join(str(r[0]) for r in alerts) or "none",
            nsb, nsf, nst))
    n13s, n13c, n13o = nmap(m13, "shavez.sale_report"), nmap(m13, "shavez.closing_stock"), nmap(m13, "darpan.order_sheet")
    if not check("0 the setup holds: v13 sale_report n %d >= 1, closing_stock n %d >= 1, darpan.order_sheet n %d = 0" % (n13s[0], n13c[0], n13o[0]),
                 n13s[0] >= 1 and n13c[0] >= 1 and n13o[0] == 0):
        say("WALK RED: the setup -- halted")
        return 1
    pristine = dbp + ".pristine"
    copydb(dbp, pristine)

    def reset():
        copydb(pristine, dbp)
        for f in os.listdir(os.path.join(tmp, "readings")):
            os.remove(os.path.join(tmp, "readings", f))
        RT._READ_CACHE.clear()

    def key(tag):
        return hashlib.md5(("W556-" + tag).encode()).hexdigest()

    def pc_refusal(tag, typ, reason, when):
        c = conn()
        ins(c, "mi_file", dict(md5=key(tag), drive_name="report.txt", drive_folder="pc_note", stamp=when[:10].replace("-", "") + "-" + when[11:19].replace(":", ""),
                               type=typ, variant="", date_from="", date_to="", verdict="REFUSED", reason=reason, pc_type="X", pc_verdict="REFUSED",
                               received_at=when, source="push"))
        c.commit()
        c.close()

    def server_refusal(tag, typ, reason, when):
        c = conn()
        ins(c, "mi_file", dict(md5=key(tag), drive_name="REPORT_1.XLS", stamp=when[:10].replace("-", "") + "-" + when[11:19].replace(":", ""), type=typ,
                               variant="", date_from=yiso, date_to=yiso, verdict="REFUSED", reason=reason, received_at=when, source="push"))
        c.commit()
        c.close()

    def verified(tag, typ, variant, when, reading=None):
        c = conn()
        ins(c, "mi_file", dict(md5=key(tag), drive_name="REPORT_1.XLS", stamp=when[:10].replace("-", "") + "-" + when[11:19].replace(":", ""), type=typ,
                               variant=variant, date_from=yiso, date_to=yiso, verdict="VERIFIED", reason="", server_name="W556_%s.xls" % tag,
                               received_at=when, source="push"))
        c.commit()
        c.close()
        if reading:
            with open(os.path.join(tmp, "readings", key(tag) + ".json"), "w") as fh:
                json.dump(dict(md5=key(tag), family=typ, ok=True, failed=[], reader="W556", data=reading), fh)

    def st(mod=RT, h=9, m=45):
        c = conn()
        try:
            return mod.status(c, today, clock(h, m))
        finally:
            c.close()

    def row(s, k):
        return next(r for r in s["rows"] if r.get("key") == k)
    # the logins the reports tile is granted to (the real portal.py and the grants file), and the owner
    code = ("import json,sys; sys.path.insert(0, %r); import portal as po; g=json.load(open(%r)); out={}\n"
            "for u in sorted((g.get('users') or {})): out[u]=[t['name'] for gg, ts in po._visible_sections('staff', False, u) for t in ts]\n"
            "print('TILES ' + json.dumps(out))" % (a.portal, os.path.join(a.portal, "tile_grants.json")))
    pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                        env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w556-walk-only",
                                 PYTHONDONTWRITEBYTECODE="1"))
    tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
    tiles = json.loads(tl[-1][6:]) if tl else {}
    staff = sorted(u for u, v in tiles.items() if "Aaj ki reports" in v)
    logins = staff + ["manoj"]
    check("0 staff-eye: the 'Aaj ki reports' tile is on the portal home of %s (the real portal.py + the grants file); the owner too"
          % ", ".join(staff), "shavez" in staff, (tiles and {u: ("Aaj ki reports" in v) for u, v in tiles.items()}, pp.stdout[-200:]))

    def aaj_rows(u):
        s, h = GET(u, "/finance/aaj/api/list")
        try:
            j = json.loads(h.decode("utf-8"))
        except ValueError:
            return s, None
        return s, [x for sec in (j.get("sections") or []) for x in sec.get("rows") or []]

    def stop_case(typ, reason, label, tag, hh, mm):
        """(1) / (5): one reader stop of `typ` received today at hh:mm."""
        k = "SALE_BILLWISE" if typ == "SALE_BILLWISE" else "STOCK_CLOSING"
        did = "shavez.sale_report" if typ == "SALE_BILLWISE" else "shavez.closing_stock"
        name = "sale report" if typ == "SALE_BILLWISE" else "closing stock"
        reset()
        pc_refusal(tag, typ, reason, at(hh, mm, 0, micro=(typ == "SALE_BILLWISE")))
        s, s0 = st(), st(RT0)
        r, r0 = row(s, k), row(s0, k)
        line = re.search(r"\(line ([0-9]+)\)", reason).group(1)
        say("   %s: the new page says %s (wrong %s, loose %d); the old page said %s (wrong %s, loose %d)"
            % (label, r["state"], (r.get("s500") or {}).get("wrong"), len(r.get("loose") or []), r0["state"], (r0.get("s500") or {}).get("wrong"),
               len(r0.get("loose") or [])))
        check("C: %s: the %s row is HELD at %02d:%02d, wrong 0, no loose line" % (label, name, hh, mm),
              r["state"] == "held" and r.get("at") == "%02d:%02d" % (hh, mm) and int((r.get("s500") or {}).get("wrong") or 0) == 0 and not r.get("loose"), r)
        check("C: %s: arrived %d is one higher than the OLD file gives on the same copy (%d)" % (label, s["arrived"], s0["arrived"]),
              s["arrived"] == s0["arrived"] + 1)
        check("C: %s: all_in stays false (no 'Sab reports aa gayi; 0 ki jaanch' over a held report); the owner's line names it" % label,
              not s["all_in"] and ("%s held: the reader could not read it (line %s)" % (name, line)) in s["line"], s["line"][-200:])
        lab = "1 · Bikri report" if k == "SALE_BILLWISE" else "2 · Closing stock"
        bad_logins = []
        for u in logins:
            code_, page = GET(u, "/finance/reports/aaj")
            rh = text(row_html(page, lab))
            ok = (code_ == 200 and "Report aa gayi" in rh and "Aapko ab kuch nahi karna." in rh
                  and any(t in rh for t in ("Doctor sahab ko khabar chali gayi hai.", "Doctor sahab ko khabar ja rahi hai.", "Doctor sahab ko bataiye."))
                  and not any(w in rh for w in ("Galat hai", "dobara", "koshish")))
            own = ("could not read it (line %s)" % line) in rh
            if not ok or own != (u == "manoj"):
                bad_logins.append((u, code_, "held words" if not ok else "the reader's line %s" % ("missing" if u == "manoj" else "shown to staff")))
        check("C: %s: /finance/reports/aaj as %s -- the row says 'Report aa gayi (..) Aapko ab kuch nahi karna.' and who has been told; none of "
              "'Galat hai', 'dobara', 'koshish'; only manoj also reads \"could not read it (line %s)\"" % (label, ", ".join(logins), line),
              not bad_logins, bad_logins)
        d1 = [x for x in RW.decide(s, 2, 600, clock(9, 45)) if x["key"] == k]
        sl = st(h=10, m=45)
        d2 = [x for x in RW.decide(sl, 2, 600, clock(10, 45)) if x["key"] == k]
        want = "The %s of %s came at %02d:%02d, but the medical PC's reader could not read it (line %s); the staff were not asked to redo it." % (
            name, y.strftime("%d-%m"), hh, mm, line)
        check("C: %s: decide -> ONE 'reader' item in the brief's words, no 'wrong' or 'late' (09:45 and 10:45, after reports.late_hhmm)" % label,
              len(d1) == 1 and d1[0]["kind"] == "reader" and d1[0]["text"] == want and len(d2) == 1 and d2[0]["kind"] == "reader", (d1, d2))
        n13, n14 = nmap(m13, did), nmap(m14, did)
        check("C: %s: v14 %s does not count the due day (v13 n %d, v14 n %d)" % (label, did, n13[0], n14[0]), n14[0] == n13[0] - 1 and n14[0] == 0,
              (n13, n14))
        sc, rows = aaj_rows("shavez")
        hit = [x for x in (rows or []) if x.get("id") == did]
        say("   %s: Shavez's Aaj ka kaam answers %s with %d line(s); %s among them: %s" % (label, sc, len(rows or []), did, bool(hit)))
        check("C: %s: staff-eye -- Shavez's Aaj ka kaam (/finance/aaj/api/list) has no %s line" % (label, did), sc == 200 and rows is not None and not hit,
              (sc, [x.get("id") for x in hit[:1]]))
        return s
    # ---------------------------------------------------------------- 1 the sale stop
    s1 = stop_case("SALE_BILLWISE", STOP43, "1 sale stop", "sale-stop", 9, 23)
    check("C: 1 hindi_reason of a reader stop: 'Medical PC is file ko padh nahi paya — aapko kuch nahi karna.' (the unknown-file card's words)",
          RT.hindi_reason(STOP43) == "Medical PC is file ko padh nahi paya — aapko kuch nahi karna.", RT.hindi_reason(STOP43))
    c = conn()
    t1 = RW.tick(c, clock(9, 46))
    t2 = RW.tick(c, clock(9, 56))
    rows_ = c.execute("SELECT key, kind, sent_at IS NOT NULL FROM marg_report_alert WHERE day=?", (tiso,)).fetchall()
    c.close()
    sa = st(h=9, m=57)
    _c, pg = GET("shavez", "/finance/reports/aaj")
    check("C: 1 the ten-minute tick: one 'reader' row for the sale report, sent once (to the walk's stub); the row then says 'khabar chali gayi hai'",
          [tuple(r) for r in rows_ if r[0] == "SALE_BILLWISE"] == [("SALE_BILLWISE", "reader", 1)] and t2.get("sent", 0) == 0
          and "Doctor sahab ko khabar chali gayi hai." in text(row_html(pg, "1 · Bikri report")), (t1, t2, [tuple(r) for r in rows_]))
    # ---------------------------------------------------------------- 2 then right
    verified("sale-right", "SALE_BILLWISE", "DETAIL", at(9, 40), reading=dict(bills=[{}] * 5))
    s2 = st()
    r2 = row(s2, "SALE_BILLWISE")
    _c, pg = GET("shavez", "/finance/reports/aaj")
    n13, n14 = nmap(m13, "shavez.sale_report"), nmap(m14, "shavez.sale_report")
    check("2 then right: a VERIFIED DETAIL at 09:40 with its reading -> 'Sahi hai', the hold gone (state %s); the map's sale_report n = 1 in v13 "
          "and v14 (sale_bill not yet written, as every day)" % r2["state"],
          r2["state"] == "ok" and "Sahi hai" in text(row_html(pg, "1 · Bikri report")) and "Report aa gayi" not in text(row_html(pg, "1 · Bikri report"))
          and n13[0] == 1 and n14[0] == 1, (r2["state"], n13, n14))
    # ---------------------------------------------------------------- 3 not stops
    def row_new(r):
        try:
            return RT._row_html(r, "shavez")
        except TypeError:                                     # the old file (the negative control) takes one argument
            return RT._row_html(r)
    diffs = []
    for i, (label, typ, reason, oneday) in enumerate(NOT_STOPS):
        reset()
        (server_refusal if oneday else pc_refusal)("notstop-%d" % i, typ, reason, at(9, 23))
        s, s0 = st(), st(RT0)
        s["you"] = s0["you"] = "shavez"
        sm, sm0 = dict(s), dict(s0)
        sm["you"] = sm0["you"] = "manoj"
        same = (RT.render(s) == RT0.render(s0) and RT.render(sm) == RT0.render(sm0) and s["line"] == s0["line"]
                and all(row_new(r) == RT0._row_html(r0) for r, r0 in zip(s["rows"], s0["rows"]))
                and RW.decide(s, 2, 600, clock(9, 45)) == RW0.decide(s0, 2, 600, clock(9, 45))
                and RW.decide(st(h=10, m=45), 2, 600, clock(10, 45)) == RW0.decide(st(RT0, 10, 45), 2, 600, clock(10, 45))
                and RT.hindi_reason(reason) == RT0.hindi_reason(reason))
        say("   3 not a stop -- %s: the sale row %s, unknown card %d; byte-identical to the old file: %s"
            % (label, row(s, "SALE_BILLWISE")["state"], len(s["unknown_today"]), same))
        if not same:
            diffs.append(label)
    check("3 not stops (9 kinds, each its own run): the page for shavez and for manoj, every row, the owner's line and decide byte-identical to "
          "the OLD file's", not diffs, diffs)
    # ---------------------------------------------------------------- 4 order of things
    reset()
    pc_refusal("ord-stop", "SALE_BILLWISE", STOP43, at(9, 23))
    pc_refusal("ord-cut", "SALE_BILLWISE", CUT_SALE, at(9, 30))
    s = st()
    r = row(s, "SALE_BILLWISE")
    _c, pg = GET("shavez", "/finance/reports/aaj")
    rh = text(row_html(pg, "1 · Bikri report"))
    check("C: 4 a stop at 09:23 and a cut short at 09:30 -> held, wrong 0, and no loose line on a staff login (state %s, %d loose kept for "
          "the owner's count)" % (r["state"], len(r.get("loose") or [])),
          r["state"] == "held" and int(r["s500"]["wrong"]) == 0 and "manzoor nahi hui" not in rh and "Report aa gayi" in rh, (r["state"], rh[:200]))
    verified("ord-summary", "SALE_BILLWISE", "SUMMARY1", at(9, 50))
    s = st(h=9, m=55)
    r = row(s, "SALE_BILLWISE")
    lz = r.get("loose") or []
    check("C: 4 then a VERIFIED SUMMARY1 at 09:50 -> the hold ends: the stop dropped (no line for 09:23), the cut-short line back (09:30), the "
          "SUMMARY1 a wrong try (state %s, wrong %s, loose %s)" % (r["state"], r["s500"]["wrong"], [l.get("at") for l in lz]),
          r["state"] in ("refused", "bad") and int(r["s500"]["wrong"]) == 1 and [l.get("at") for l in lz] == ["09:30"], (r["state"], lz))
    # ---------------------------------------------------------------- 5 stock
    stop_case("STOCK_CLOSING", STOP_STOCK, "5 stock stop", "stock-stop", 9, 24)
    # ---------------------------------------------------------------- 6 Darpan
    reset()
    pc_refusal("ord-cut-0800", "ORDER_PENDING", CUT_ORDER, at(8, 0))
    pc_refusal("ord-stop-0805", "ORDER_PENDING", STOP_ORDER, at(8, 5))
    c = conn()
    dc = OS.darpan_card(c)
    c.close()
    n13, n14 = nmap(m13, "darpan.order_sheet"), nmap(m14, "darpan.order_sheet")
    check("C: 6 cut short 08:00 then a stop 08:05 -> Darpan's card shows nothing (refused %s); v14 n %d (v13 n %d)" % (dc["refused"], n14[0], n13[0]),
          dc["refused"] is False and n14[0] == 0 and n13[0] == 1, (dc, n13, n14))
    reset()
    pc_refusal("ord-stop-only", "ORDER_PENDING", STOP_ORDER, at(8, 5))
    c = conn()
    dc = OS.darpan_card(c)
    ol = [x for x in OS.owner_lines(c) if "order sheet refused today" in str(x.get("text"))]
    c.close()
    sc, h = GET("darpan", "/finance/darpan/kal/api/day?date=%s" % tiso)
    try:
        api = (json.loads(h.decode("utf-8")) or {}).get("order_sheet") or {}
    except ValueError:
        api = {}
    n13, n14 = nmap(m13, "darpan.order_sheet"), nmap(m14, "darpan.order_sheet")
    check("C: 6 an ORDER_PENDING stop newer than the last taken sheet -> darpan_card refused False; /finance/darpan/kal/api/day as darpan (what "
          "his page draws 'Order sheet adhoori thi' from) refused False; v14 n %d" % n14[0],
          dc["refused"] is False and sc == 200 and api.get("refused") is False and n14[0] == 0, (dc.get("refused"), sc, api.get("refused"), n14))
    check("6 ... owner_lines still names it ('Darpan's order sheet refused today'); v13 counted it (n %d)" % n13[0], len(ol) == 1 and n13[0] == 1, ol)
    reset()
    pc_refusal("ord-cut-only", "ORDER_PENDING", CUT_ORDER, at(8, 0))
    c = conn()
    dc = OS.darpan_card(c)
    c.close()
    n13, n14 = nmap(m13, "darpan.order_sheet"), nmap(m14, "darpan.order_sheet")
    check("6 a cut-short sheet alone -> refused True, n 1 in v13 and v14 (as today)", dc["refused"] is True and n13[0] == 1 and n14[0] == 1, (dc, n13, n14))
    # ---------------------------------------------------------------- the map and the page read ONE rule (charter 13; s2.0's SQL = the Python)
    reasons = [STOP43, STOP_ORDER, STOP_STOCK, "the medical PC refused it: the reader refused it (line 7)"] + [r[2] for r in NOT_STOPS] + [
        "the medical PC refused it: the reader refused it (line 43) ", "the medical PC refused it: the reader refused it (line )",
        "the medical PC refused it: the reader refused it (line 4) (x)", "x the medical PC refused it: the reader refused it (line 4)"]
    glob = re.search(r"reason GLOB '[^']*' AND reason NOT GLOB '[^']*'", due(m14, "shavez.sale_report"))
    c = sqlite3.connect(":memory:")
    agree = []
    for rs in reasons:
        sq_ =bool(c.execute("SELECT (? GLOB 'the medical PC refused it: the reader refused it (line [0-9]*)' AND ? NOT GLOB '*(line *[^0-9]*)')",
                             (rs, rs)).fetchone()[0])
        agree.append(sq_ == bool(getattr(RT, "reader_stop", lambda x: False)(rs)))
    c.close()
    check("C: the map's GLOB (v14, in all three duties) gives the same answer as reports_tile.reader_stop on %d reasons, (line 4x) included"
          % len(reasons), glob is not None and all(agree) and all(("reason GLOB 'the medical PC refused it: the reader refused it (line [0-9]*)' AND "
                                                                   "reason NOT GLOB '*(line *[^0-9]*)'") in due(m14, d)
                                                                  for d in ("shavez.sale_report", "shavez.closing_stock", "darpan.order_sheet")), agree)
    check("C: DUTY_MAP v14, kit S556 (version %s, kit %s)" % (m14.get("version"), m14.get("kit")), m14.get("version") == 14 and m14.get("kit") == KIT)
    # ---------------------------------------------------------------- the end
    try:
        os.remove(pristine)
    except OSError:
        pass
    leak = re.search(r"\d{10}", "\n".join(OUT))
    check("8 static: the walk's own output holds no run of 10 digits", not leak)
    red = len(FAILS)
    if a.expect_red:
        cr = [l for l, ok in CTRL if not ok]
        cg = [l for l, ok in CTRL if ok]
        for l in cr:
            say("  RED on the old files: " + l[:150])
        if CTRL and not cg:
            say("WALK OK negative control: every one of the %d 'C:' checks is red on the old files and map v13 (%d of %d checks red)" % (len(CTRL), red, RUN[0]))
            return 0
        say("NEGATIVE CONTROL FAILED: %d 'C:' checks stayed green on the old files: %s" % (len(cg), "; ".join(x[:80] for x in cg)))
        return 1
    if FAILS:
        say("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    say("WALK OK S556: %d checks green (the sale stop held, then right, nine not-stops unchanged, the order of things, the stock stop, Darpan's "
        "card, the map's one rule, staff-eye)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
