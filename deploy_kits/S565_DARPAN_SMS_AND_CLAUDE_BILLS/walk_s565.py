#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s565.py -- kit S565_DARPAN_SMS_AND_CLAUDE_BILLS (15-Oct-2026), part A.  Runs on SCRATCH folders and SCRATCH databases only.
    python3 -B walk_s565.py --fin <scratch finance, the files under test> --oldfin <scratch finance, the OLD files>
                            --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config> --map <DUTY_MAP.json> [--expect-red]
    python3 -B walk_s565.py --page --fin <a copy of the placed files> --db <a copy of the live database> ...   (after placing)
The real finance app (Flask's test client, the walk's own header session -- FINANCE_ALLOW_HEADER_AUTH on a scratch process, never a live
secret or user store).  Made-up Sanjeevni days in April / May 2027, found by their dates and W565 keys, never by counting; the SMS rows,
the MPR rows and the POS total are the walk's own; no phone number, no real account digit.
The page draws itself in the browser.  The box has no browser and no node, so the walk takes the page AS SERVED and runs, in the box's
Java JS engine (jjs), the exact expressions that draw the 'online' rows (Darpan's row, the owner's row, the owner's note ownerPos and the
smsAt helper) -- verbatim from the served page -- on the day's JSON as the page receives it; and lexes the page's whole <script> (strings,
regex literals, comments, brackets) so a broken quote is red.  A real browser render is done by the builder at kit time (the report).
  1  an SMS day (the switch on, no MPR): compute_day 'sms', 'बैंक SMS 07:02'; Darpan's row 'बैंक SMS 07:02 से — bank की report बाकी', one
     rupee figure, no difference; the owner's row 'provisional — bank SMS 07:02, MPR not in', no Devanagari; his note names the SMS.
  2  a day posted by Darpan on Marg's figure -> the SMS lands -> a page read re-decides it (online_p = the SMS) -> a made-up MPR -> re-decided
     again (statement_in, not provisional).
  3  a POS-confirmed day (the switch off): the 'pos' rows byte-identical to the OLD page's; an SMS received two days later reads '28-Apr 07:02'
     on the owner's row; a 'never' SMS day reads 'MPR never received'; the page lexes clean, and a broken quote is caught.
  S  staff-eye (CLAUDE.md, S444): darpan's and manoj's tiles on the portal home; each due duty's marker on /finance/darpan/kal.
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import datetime as dt
import html as _html
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time

KIT = "S565_DARPAN_SMS_AND_CLAUDE_BILLS"
BASE = "https://followup.dr-manoj.in"
ROLE = {"darpan": "staff", "manoj": "doctor"}
RUN, FAILS, CTRL, OUT = [0], [], [], []
W1, W2, W3, W4, W5 = "2027-04-05", "2027-04-12", "2027-04-19", "2027-04-26", "2027-05-03"
DEVA = re.compile(u"[\u0900-\u097F]")


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


def conn(dbp):
    c = sqlite3.connect(dbp, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def text(h):
    s = h.decode("utf-8", "replace") if isinstance(h, bytes) else h
    s = re.sub(r"<script.*?</script>|<style.*?</style>", " ", s, flags=re.S)
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s)))


def clock(iso):
    for k in ("CLINIC_MONEY_NOW", "BANK_STANDIN_NOW", "BANK_SMS_NOW"):
        if iso:
            os.environ[k] = iso
        else:
            os.environ.pop(k, None)


def app_env(fin, dbp, adb, marg, dmap):
    work = os.path.dirname(dbp)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(dmap), FINANCE_SSO_DIR=os.path.join(work, "nosso"),
                      RING_PORTAL_DIR=os.path.join(work, "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      BANK_SMS_KEY_FILE=os.path.join(work, "w565_no.key"), PYTHONDONTWRITEBYTECODE="1")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)
    sys.path.insert(0, fin)
    os.chdir(fin)


def load_app(fin):
    import finance_app as fa                                  # noqa: E402
    import bank_standin as BS                                 # noqa: E402
    import bank_sms as SMS                                    # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    for m in (BS, SMS, DK):
        assert os.path.abspath(m.__file__).startswith(fin), (m.__name__, m.__file__)
    return fa, BS, SMS, DK


class Client:
    def __init__(self, fa):
        self.cl = fa.app.test_client(use_cookies=False)
        self.times = []

    def get(self, u, path, follow=False):
        t0 = time.time()
        r = self.cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")}, follow_redirects=follow)
        self.times.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data()

    def post(self, u, path, js=None):
        r = self.cl.post(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")}, json=js)
        return r.status_code, r.get_data()

    def jget(self, u, path):
        s, b = self.get(u, path)
        try:
            return s, json.loads(b.decode("utf-8"))
        except ValueError:
            return s, {}


# ============================================================================================ the page's own drawing code, in jjs
def script_of(page):
    m = re.search(r"<script>(.*?)</script>", page, re.S)
    return m.group(1) if m else ""


def pieces(page):
    """The drawing expressions, verbatim from the served page: Darpan's online row, the owner's online row, ownerPos, smsAt."""
    s = script_of(page)
    got = {}
    for k, rx in (("e141", r"'<div class=\"row\"><span class=\"k\">− Online \(UPI / card\)'\+.*?R\(c\.online_p\)\+'</span></div>'"),
                  ("e313", r"'<div class=\"row\"><span class=\"k\">− online '\+.*?R\(c\.online_p\)\+'</span></div>'"),
                  ("ownerpos", r"function ownerPos\(j\)\{.*?\n return t;\n\}")):
        f = re.findall(rx, s, re.S if k == "ownerpos" else 0)
        got[k] = f[0] if len(f) == 1 else None
        got[k + "_n"] = len(f)
    f = re.findall(r"const smsAt=c=>\{(.*?)\};\n", s)
    got["smsat_n"] = len(f)
    got["smsat"] = ("var smsAt=function(c){%s};" % f[0].replace("const ", "var ")) if len(f) == 1 else "var smsAt=function(c){return \"\";};"
    return got


def js_ascii(s):
    return s.encode("ascii", "backslashreplace").decode("ascii")


def jjs_bin():
    return os.environ.get("JJS") or shutil.which("jjs") or ""


def render(page, cases, work, tag):
    """cases: [(what, payload)] -> [string drawn by the page's own expression] (or 'JSERROR ...' / 'MISSING ...')."""
    p = pieces(page)
    miss = [k for k in ("e141", "e313", "ownerpos") if p[k] is None]
    if miss or not jjs_bin():
        return ["MISSING %s%s" % (",".join(miss), "" if jjs_bin() else " jjs") for _ in cases]
    js = ("var esc=function(s){return (s==null?\"\":String(s)).replace(/[&<>\"]/g,function(ch){return {\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\",'\"':\"&quot;\"}[ch];});};\n"
          "var R=function(p){return p==null?\"\\u2014\":\"\\u20b9\"+(Math.round(p)/100);};\n"
          + p["smsat"] + "\n"
          "function e141(c){return " + p["e141"] + ";}\n"
          "function e313(c){return " + p["e313"] + ";}\n"
          + p["ownerpos"] + "\n"
          "var CASES=" + json.dumps([{"what": w, "j": j} for w, j in cases]) + ";\nvar OUT=[];\n"
          "for(var i=0;i<CASES.length;i++){var k=CASES[i],r;try{r=k.what==='e141'?e141(k.j.calc):k.what==='e313'?e313(k.j.calc):ownerPos(k.j);}catch(e){r='JSERROR '+e;}OUT.push(r);}\n"
          "print(JSON.stringify(OUT).replace(/[\\u0080-\\uffff]/g,function(ch){return '\\\\u'+('0000'+ch.charCodeAt(0).toString(16)).slice(-4);}));\n")
    f = os.path.join(work, "w565_draw_%s.js" % tag)
    with open(f, "w", encoding="ascii") as fh:
        fh.write(js_ascii(js))
    pr = subprocess.run([jjs_bin(), "--language=es6", f], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=300)
    line = [x for x in pr.stdout.splitlines() if x.startswith("[")]
    try:
        return json.loads(line[-1])
    except (ValueError, IndexError):
        return ["JSERROR %s" % pr.stdout.strip()[-300:] for _ in cases]


def js_lex(src):
    """(ok, why): strings, template literals, regex literals, comments and brackets of a JS source; a quote that breaks a line is red."""
    i, n, stack, prev, line = 0, len(src), [], None, 1
    pairs = {")": "(", "]": "[", "}": "{"}
    kw_re = {"return", "typeof", "case", "in", "of", "else", "new", "delete", "void", "throw", "do", "instanceof", "yield", "await"}
    while i < n:
        ch = src[i]
        if ch == "\n":
            line += 1
            i += 1
            continue
        if ch in " \t\r":
            i += 1
            continue
        if src.startswith("//", i):
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if src.startswith("/*", i):
            j = src.find("*/", i + 2)
            if j < 0:
                return False, "comment never closed (line %d)" % line
            line += src.count("\n", i, j)
            i = j + 2
            continue
        if ch in "'\"`":
            q, j = ch, i + 1
            while j < n and src[j] != q:
                if src[j] == "\\":
                    j += 2
                    continue
                if src[j] == "\n" and q != "`":
                    return False, "a %s string breaks at line %d" % (q, line)
                j += 1
            if j >= n:
                return False, "a %s string never closed (line %d)" % (q, line)
            line += src.count("\n", i, j)
            i, prev = j + 1, "str"
            continue
        if ch == "/" and (prev is None or prev in kw_re or (len(prev) == 1 and prev in "(,=:[!&|?{};+-*%<>~^")):
            j, cls = i + 1, False
            while j < n:
                c2 = src[j]
                if c2 == "\\":
                    j += 2
                    continue
                if c2 == "\n":
                    return False, "a regex breaks at line %d" % line
                if c2 == "[":
                    cls = True
                elif c2 == "]":
                    cls = False
                elif c2 == "/" and not cls:
                    break
                j += 1
            j += 1
            while j < n and (src[j].isalnum()):
                j += 1
            i, prev = j, "re"
            continue
        if ch == "\\" and not src.startswith("\\u", i):
            return False, "a stray backslash outside a string at line %d" % line
        if ch in "([{":
            stack.append((ch, line))
            i, prev = i + 1, ch
            continue
        if ch in ")]}":
            if not stack or stack[-1][0] != pairs[ch]:
                return False, "'%s' at line %d does not close %s" % (ch, line, stack[-1] if stack else "anything")
            stack.pop()
            i, prev = i + 1, ch
            continue
        if ch.isalnum() or ch in "_$" or ord(ch) > 127:
            j = i
            while j < n and (src[j].isalnum() or src[j] in "_$" or ord(src[j]) > 127):
                j += 1
            prev = src[i:j] if src[i:j] in kw_re else "word"
            i = j
            continue
        i, prev = i + 1, ch
    if stack:
        return False, "%d bracket(s) never closed (first %s at line %d)" % (len(stack), stack[0][0], stack[0][1])
    return True, ""


# ============================================================================================ the made-up world
def day_entry(c, unit, d, upi_p, cash_p):
    cur = c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES (?,?,'submitted','app','w565',?)",
                    (unit, d, d + " 21:00:00"))
    for mode, amt in (("upi", upi_p), ("cash", cash_p)):
        c.execute("INSERT INTO sale_item (day_entry_id, unit, service, description, amount_p, mode, source, source_ref) VALUES (?,?,?,?,?,?,?,?)",
                  (cur.lastrowid, unit, "pharmacy", "W565 walk", amt, mode, "manual", "W565-%s-%s" % (d[-5:], mode)))


def sms_row(SMS, dbp, unit, d, amount_p, received):
    c = conn(dbp)
    SMS._schema_done = False
    SMS._ensure(c)                                            # the table's full definition, from bank_sms.py itself
    credit = (dt.date.fromisoformat(d) + dt.timedelta(days=1)).isoformat()
    c.execute("INSERT INTO bank_sms_settlement (unit, credit_date, business_date, amount_p, balance_p, acct_tail, ref, sms_text, phone_sender, received_at) "
              "VALUES (?,?,?,?,?,?,?,?,?,?)", (unit, credit, d, amount_p, 500000, "000", "W565-%s" % d, "W565 walk -- a made-up settlement SMS", "W565-WALK", received))
    c.commit()
    c.close()


def land_mpr(dbp, unit, d, amount_p, taken):
    c = conn(dbp)
    mid = "W565-%s" % unit
    c.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
              (mid, unit, d, "W565_walk.csv", amount_p, 1, taken))
    c.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time, ingested_at) VALUES (?,?,?,?,?,?,?,?)",
              (mid, unit, d, amount_p, "W565R%s" % d[-5:].replace("-", ""), "UPI", "11:00", taken))
    c.commit()
    c.close()


def setting(dbp, key, value):
    c = conn(dbp)
    c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES (?,?,'W565 walk')", (key, value))
    c.commit()
    c.close()


# ============================================================================================ the page look, after placing
def page_look(a):
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    app_env(fin, dbp, a.adb, a.marg, a.map)
    clock("")
    fa, BS, SMS, DK = load_app(fin)
    C = Client(fa)
    s1, h1 = C.get("darpan", "/finance/darpan/kal")
    pg = h1.decode("utf-8", "replace")
    p = pieces(pg)
    s2, j = C.jget("darpan", "/finance/darpan/kal/api/day")
    s3, j3 = C.jget("manoj", "/finance/darpan/kal/api/day")
    ok_lex, why = js_lex(script_of(pg))
    say("   /finance/darpan/kal as darpan (the placed files, a copy of the live database, the real clock): %s, %d KB, smsAt helper %d, lexes %s; "
        "api/day as darpan %s (%s), as manoj %s (%s)" % (s1, len(h1) // 1024, p["smsat_n"], "clean" if ok_lex else "RED " + why,
                                                         s2, j.get("ok"), s3, (j3.get("me") or {}).get("kind")))
    ok = s1 == 200 and p["smsat_n"] == 1 and ok_lex and s2 == 200 and j.get("ok") and s3 == 200 and (j3.get("me") or {}).get("kind") == "owner"
    leak = re.search(r"\d{10}", "\n".join(OUT))
    say(("PAGE OK S565" if ok and not leak else "PAGE RED S565") + ": Darpan's Kal ka hisaab read as darpan and manoj on a copy")
    return 0 if ok and not leak else 1


# ============================================================================================ the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--oldfin", "--portal", "--dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true")
    a = ap.parse_args()
    anywhere = os.environ.get("S565_WALK_ANYWHERE") == "1"
    for p in (a.fin, a.db, a.adb, a.marg) + ((a.oldfin,) if a.oldfin else ()):
        assert os.path.abspath(p).startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.page:
        return page_look(a)
    if not (a.oldfin and a.portal):
        ap.error("--oldfin and --portal are needed for the walk")
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    work = os.path.dirname(dbp)
    say("-- S565 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    app_env(fin, dbp, a.adb, a.marg, a.map)
    fa, BS, SMS, DK = load_app(fin)
    UNIT = DK._unit
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; darpan_kal's unit: %s; jjs: %s"
        % ([n for n, _w in fa._MOUNT_FAILED] or "none", UNIT, "yes" if jjs_bin() else "MISSING"))
    check("the box's JS engine (jjs) is there to run the page's own drawing code", bool(jjs_bin()))
    C = Client(fa)
    old_page = open(os.path.join(os.path.abspath(a.oldfin), "darpan_kal.html"), encoding="utf-8").read()
    c = conn(dbp)
    for d in (W1, W2, W3, W4, W5):                             # the walk's own days are empty on the copy (by key)
        n = c.execute("SELECT (SELECT COUNT(*) FROM day_entry WHERE unit=? AND business_date=?) + (SELECT COUNT(*) FROM darpan_kal_day WHERE unit=? AND business_date=?) "
                      "+ (SELECT COUNT(*) FROM upi_statement WHERE unit=? AND statement_date=?)", (UNIT, d, UNIT, d, UNIT, d)).fetchone()[0]
        assert n == 0, "the walk's made-up day %s already has rows on the copy" % d
    c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('bank_mpr.expect_hhmm','10:00','W565 walk')")
    for d, upi in ((W1, 70000), (W2, 50000), (W3, 40000), (W4, 30000), (W5, 20000)):
        day_entry(c, UNIT, d, upi, 200000)
    c.commit()
    c.close()
    s, h = C.get("darpan", "/finance/darpan/kal")
    page = h.decode("utf-8", "replace")
    check("/finance/darpan/kal as darpan: 200, the page as served (%d KB)" % (len(h) // 1024), s == 200 and "<script>" in page, s)
    P = pieces(page)
    check("C: the served page carries the smsAt helper exactly once", P["smsat_n"] == 1, P["smsat_n"])
    check("the drawing expressions are found exactly once in the served page (Darpan's row %d, the owner's row %d, ownerPos %d)"
          % (P["e141_n"], P["e313_n"], P["ownerpos_n"]), P["e141_n"] == 1 and P["e313_n"] == 1 and P["ownerpos_n"] == 1)
    dumps = {}

    def section(name, fn):
        say("-- " + name)
        try:
            fn()
        except Exception as e:                                # noqa: BLE001 -- a section that raises is red, the walk goes on
            import traceback                                  # noqa: PLC0415
            tb = traceback.format_exc().strip().splitlines()
            check("C: section '%s' ran to its end" % name.split()[0], False, "%s: %s | %s" % (type(e).__name__, str(e)[:160], " / ".join(x.strip() for x in tb[-4:])[:300]))

    def rowd(d):
        c = conn(dbp)
        try:
            r = c.execute("SELECT * FROM darpan_kal_day WHERE unit=? AND business_date=?", (UNIT, d)).fetchone()
            return dict(r) if r else {}
        finally:
            c.close()

    # ============================================================================================ 1
    def s1():
        setting(dbp, "bank_sms.standin_on", "1")
        sms_row(SMS, dbp, UNIT, W1, 123400, "2027-04-06 07:02:00")
        clock("2027-04-06T11:30:00")
        c = conn(dbp)
        calc = DK.compute_day(c, W1)
        c.close()
        check("compute_day(%s): online_source 'sms', ₹1,234, standin.label 'बैंक SMS 07:02', provisional" % W1,
              calc["online_source"] == "sms" and calc["online_p"] == 123400 and (calc.get("standin") or {}).get("label") == "बैंक SMS 07:02"
              and calc["online_provisional"] == 1, (calc["online_source"], calc["online_p"], calc.get("standin")))
        s, jd = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W1)
        s2, jm = C.jget("manoj", "/finance/darpan/kal/api/day?date=%s" % W1)
        dumps["sms_darpan"], dumps["sms_manoj"] = jd, jm
        check("api/day %s: darpan 200 as staff, manoj 200 as owner" % W1, s == 200 and s2 == 200 and (jd.get("me") or {}).get("kind") == "staff"
              and (jm.get("me") or {}).get("kind") == "owner", (s, s2, jd.get("me"), jm.get("me")))
        st = json.dumps(jd.get("calc") or {}, ensure_ascii=False)
        check("Darpan's day carries no SMS-vs-MPR figure (no sms_diff / mpr_p / diff in calc)", not re.search(r"sms_diff|mpr_p|\"diff", st), st[:200])
        r = render(page, [("e141", jd), ("e313", jm), ("ownerpos", jm)], work, "s1")
        say("   drawn, Darpan's row: %s" % text(r[0]))
        say("   drawn, the owner's row: %s | his note: %s" % (text(r[1]), text(r[2])))
        want = "बैंक SMS 07:02 से — bank की report बाकी"
        check("C: Darpan's online row draws '%s'" % want, want in text(r[0]), text(r[0]))
        rup = re.findall(u"₹[\\d.,]+", text(r[0]))
        check("Darpan's online row shows one rupee figure only (the day's online total), no difference", len(rup) == 1 and "अंतर" not in r[0]
              and "difference" not in r[0].lower(), rup)
        check("C: the owner's online row draws 'provisional — bank SMS 07:02, MPR not in' and no Devanagari",
              "provisional — bank SMS 07:02, MPR not in" in text(r[1]) and not DEVA.search(text(r[1])), text(r[1]))
        check("C: the owner's note: 'UPI total from the bank's settlement SMS of 07:02 — the MPR mail is not in yet.'",
              "UPI total from the bank's settlement SMS of 07:02 — the MPR mail is not in yet." in text(r[2]), text(r[2]))
        rs = render(page, [("e141", jd)], work, "s1b")
        check("the drawing is repeatable (the same row twice)", rs[0] == r[0])
    section("1  an SMS day: Darpan's row, the owner's row", s1)

    # ============================================================================================ 2
    def s2():
        clock("2027-04-13T06:30:00")                          # Darpan posts the morning after, before the SMS
        c = conn(dbp)
        c.execute("INSERT INTO darpan_kal_day (unit, business_date, handed_p, handed_to, reason, reason_note, state, created_by, created_at, updated_at) "
                  "VALUES (?,?,?,?,NULL,NULL,'open','darpan',?,?)", (UNIT, W2, 200000, "dr_manoj", "2027-04-13 06:30:00", "2027-04-13 06:30:00"))
        row = dict(c.execute("SELECT * FROM darpan_kal_day WHERE unit=? AND business_date=?", (UNIT, W2)).fetchone())
        calc = DK.compute_day(c, W2)
        DK._decide(c, W2, calc, row, "darpan")                # what api_handover does (the API refuses a day in the future)
        c.commit()
        c.close()
        r0 = rowd(W2)
        check("the day %s posted on Marg's figure: online_p ₹500, provisional, decided" % W2,
              r0.get("online_p") == 50000 and r0.get("online_provisional") == 1 and r0.get("decided_at"), (r0.get("online_p"), r0.get("online_provisional")))
        sms_row(SMS, dbp, UNIT, W2, 60000, "2027-04-13 07:02:00")
        clock("2027-04-13T11:30:00")
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W2)
        r1 = rowd(W2)
        check("C: the SMS lands -> Darpan's page read re-decides the day: online_p = the SMS ₹600 (was ₹500), still provisional",
              s == 200 and r1.get("online_p") == 60000 and r1.get("online_provisional") == 1 and (j.get("calc") or {}).get("online_source") == "sms",
              (s, r1.get("online_p"), r1.get("online_provisional"), (j.get("calc") or {}).get("online_source")))
        land_mpr(dbp, UNIT, W2, 61000, "2027-04-13 12:10:00")
        clock("2027-04-13T12:30:00")
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W2)
        r2 = rowd(W2)
        check("a made-up MPR lands -> re-decided again: online_p = the MPR ₹610, not provisional, statement_in",
              s == 200 and r2.get("online_p") == 61000 and r2.get("online_provisional") == 0 and (j.get("calc") or {}).get("statement_in"),
              (s, r2.get("online_p"), r2.get("online_provisional")))
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W2)
        r3 = rowd(W2)
        check("no loop: a further page read leaves the day as it is (decided_at unchanged)", r3.get("decided_at") == r2.get("decided_at"),
              (r2.get("decided_at"), r3.get("decided_at")))
    section("2  a posted day worked again: the SMS, then the MPR", s2)

    # ============================================================================================ 3
    def s3():
        setting(dbp, "bank_sms.standin_on", "0")
        clock("2027-04-20T11:30:00")
        s, b = C.post("manoj", "/finance/darpan/kal/api/pos-total", js={"date": W3, "amount_p": 41000})
        check("the switch off: his POS total for %s stands (200)" % W3, s == 200, (s, b[:200]))
        s, jd = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W3)
        s2, jm = C.jget("manoj", "/finance/darpan/kal/api/day?date=%s" % W3)
        dumps["pos_darpan"], dumps["pos_manoj"] = jd, jm
        check("Darpan's day %s: online_source 'pos', ₹410" % W3, (jd.get("calc") or {}).get("online_source") == "pos" and (jd.get("calc") or {}).get("online_p") == 41000,
              ((jd.get("calc") or {}).get("online_source"), (jd.get("calc") or {}).get("online_p")))
        cases = [("e141", jd), ("e313", jm), ("ownerpos", jm)]
        rn, ro = render(page, cases, work, "s3n"), render(old_page, cases, work, "s3o")
        check("the 'pos' rows drawn byte for byte as the OLD page draws them (Darpan's row, the owner's row, his note)",
              rn == ro and "POS total से — bank की report बाकी" in rn[0] and "UPI total read from the POS machine" in rn[2], [text(x)[:90] for x in rn + ro])
        setting(dbp, "bank_sms.standin_on", "1")
        sms_row(SMS, dbp, UNIT, W4, 33000, "2027-04-28 07:02:00")
        clock("2027-04-28T11:00:00")
        s, j4 = C.jget("manoj", "/finance/darpan/kal/api/day?date=%s" % W4)
        dumps["late_manoj"] = j4
        r4 = render(page, [("e313", j4), ("ownerpos", j4)], work, "s3l")
        say("   drawn, SMS two days late, the owner's row: %s" % text(r4[0]))
        check("C: an SMS received two days later: the owner's row 'provisional — bank SMS 28-Apr 07:02, MPR not in'",
              "provisional — bank SMS 28-Apr 07:02, MPR not in" in text(r4[0]) and "of 28-Apr 07:02" in text(r4[1]), [text(x) for x in r4])
        sms_row(SMS, dbp, UNIT, W5, 22000, "2027-05-04 07:02:00")
        clock("2027-05-08T11:00:00")
        s, j5 = C.jget("manoj", "/finance/darpan/kal/api/day?date=%s" % W5)
        s6, j6 = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % W5)
        dumps["never_manoj"], dumps["never_darpan"] = j5, j6
        r5 = render(page, [("e313", j5), ("e141", j6)], work, "s3v")
        say("   drawn, a 'never' SMS day, the owner's row: %s | Darpan's row: %s" % (text(r5[0]), text(r5[1])))
        check("C: a 'never' SMS day: the owner's row 'provisional — bank SMS 07:02, MPR never received' (standin.never true)",
              ((j5.get("calc") or {}).get("standin") or {}).get("never") is True and "provisional — bank SMS 07:02, MPR never received" in text(r5[0]),
              (((j5.get("calc") or {}).get("standin") or {}).get("never"), text(r5[0])))
        check("a 'never' SMS day on Darpan's row: no difference, no English 'never' (the same SMS line, or the old plain line)",
              "never" not in text(r5[1]).lower() and len(re.findall(u"₹[\\d.,]+", text(r5[1]))) == 1, text(r5[1]))
        ok, why = js_lex(script_of(page))
        check("the served page's whole <script> lexes clean (strings, regexes, comments, brackets)", ok, why)
        broken = script_of(page).replace("Marg\\'s own non-cash", "Marg's own non-cash", 1)
        okb, whyb = js_lex(broken)
        check("the lexer can fail: the same script with 'Marg\\'s' unescaped is caught (%s)" % whyb, broken != script_of(page) and not okb, whyb)
        broken2 = script_of(page).replace("the bank\\'s settlement SMS", "the bank's settlement SMS", 1)
        if broken2 != script_of(page):
            okc, whyc = js_lex(broken2)
            rb = render(page.replace(script_of(page), broken2), [("ownerpos", jm)], work, "s3b")
            check("an unescaped apostrophe on the new note line is caught by the lexer and by jjs (%s; %s)" % (whyc, rb[0][:60]),
                  not okc and rb[0].startswith("JSERROR"), (whyc, rb[0][:120]))
    section("3  the POS day unchanged; a late SMS; a 'never' day; the page parses", s3)

    # ============================================================================================ S
    def ss():
        clock("")
        m = json.load(open(a.map, encoding="utf-8"))
        persons = ("darpan", "manoj")
        doors = ("/finance/darpan/kal",)
        duties = [d for d in m["duties"] if d.get("person") in persons and d.get("door") in doors]
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u, r in %r: out[u]=[t['name'] for g, ts in po._visible_sections(r, False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, [(u, ROLE[u]) for u in persons]))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w565-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        miss_t = [(d["person"], d["tile"]) for d in duties if d.get("tile") and d["tile"] not in tiles.get(d["person"], [])]
        check("staff-eye: each duty's tile at this door is on its person's portal home (%s; the real portal.py + the grants file, a walk-only secret)"
              % ", ".join(sorted(set("%s:%s" % (d["person"], d.get("tile")) for d in duties))), tiles and not miss_t, (miss_t, pp.stdout[-200:]))
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        due = {}
        for d in duties:
            try:
                due[d["id"]] = int(ro.execute(d["due_sql"]).fetchone()[0] or 0) if d.get("due_sql") else 0
            except sqlite3.Error as e:
                due[d["id"]] = "error %s" % str(e)[:60]
        ro.close()
        say("   duties at this door due now (their due_sql on the walk's copy): %s" % due)
        miss, old_miss = [], []
        for d in duties:
            s, h = C.get(d["person"], d["door"], follow=True)
            hh = h.decode("utf-8", "replace")
            hide = isinstance(due[d["id"]], int) and due[d["id"]] > 0 and d.get("door_marker") and d["door_marker"] not in hh and d["door_marker"] not in text(hh)
            if s != 200 or hide:
                miss.append(d)
                if d.get("door_marker") and d["door_marker"] not in old_page:
                    old_miss.append(d)
        mine = [(d["person"], d["id"]) for d in miss if d not in old_miss]
        check("staff-eye: the door answers 200 to darpan and manoj and shows each due duty's marker -- none hidden by this kit (%d duties%s)"
              % (len(duties), ("; the old page misses the same %d" % len(old_miss)) if old_miss else ""),
              duties and not mine and all(isinstance(v, int) for v in due.values()), mine[:4])
        heavy = [(u, p, round(t_, 2), n) for u, p, t_, n in C.times if (t_ >= 2.0 or n >= 100000) and u == "darpan"]
        check("every page Darpan's login read in the walk: under 100 KB and under 2 s (%d reads)" % len([x for x in C.times if x[0] == "darpan"]), not heavy, heavy[:4])
    section("S  staff-eye", ss)

    # ---------------------------------------------------------------- the end
    clock("")
    if a.dump:
        json.dump(dict(page_new=page, page_old=old_page, days=dumps), open(a.dump, "w", encoding="utf-8"), ensure_ascii=False)
        say("   the walk's own made-up days and both pages written to %s (for the builder's browser render)" % os.path.basename(a.dump))
    for x in os.listdir(work):
        if x.startswith("w565_draw_"):
            os.remove(os.path.join(work, x))
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
    say("WALK OK S565: %d checks green (the SMS on Darpan's row and the owner's; a posted day worked again for the SMS and the MPR; the POS rows "
        "unchanged; a late and a 'never' SMS; the page parses; staff-eye)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
