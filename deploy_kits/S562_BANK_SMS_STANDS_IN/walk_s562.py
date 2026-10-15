#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s562.py -- kit S562_BANK_SMS_STANDS_IN (15-Oct-2026, D729).  Runs on SCRATCH folders and SCRATCH databases only.
    python3 -B walk_s562.py --fin <scratch finance, the files under test> --oldfin <scratch finance, the OLD files>
                            --db <a COPY of finance.db> --adb <a COPY of assets.db> --marg <scratch marg_ingest>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config> --map <DUTY_MAP.json> [--expect-red]
    python3 -B walk_s562.py --page --fin <a copy of the placed files> --db <a copy of the live database> ...   (after placing)
The real finance app (Flask's test client, the walk's own header session -- FINANCE_ALLOW_HEADER_AUTH on a scratch process, never a live
secret; the SMS door opened with a walk-only key file).  Made-up rows dated March 2027, found by their W562 keys, never by counting; made-up
merchant ids (tails 000561 / 000562) on the scratch copy only; no phone number, no real account digit; the walk prints counts, never a
real day's amount and never an SMS text.
  a  switch OFF: the old files and the new, each in a child process on its own copy at the same moment, give the same pages (the clinic
     card for two logins, Clinic money, Darpan's day, the owner's Kal card) and the same standing() / day() dicts; the ledger's SMS and
     MPR figures equal the old page's; the ledger shows the switch OFF.
  b  switch ON (his POST, audited; a staff POST refused): the SMS stands -- bank_day 'sms', match_day standin source 'sms', the card says
     'Bank SMS 07:02', Darpan's day online_source 'sms' with 'बैंक SMS 07:02'; nobody is offered the POS field after the expected time;
     the hooks fired and the stored mpr_missing flag cleared.
  c  the MPR lands equal: source 'mpr'; 'Bank SMS 07:02 ₹1,234 · MPR mail taken 09:56 ₹1,234 · same.'; no owner line; the hooks fired.
  d  the MPR differs beyond the tolerance: exactly one owner line, on his page only; no staff page shows a difference.
  e  no SMS, no MPR, past the time: the POS field offered as today; a confirmed POS stands with source 'pos'; an SMS arriving later wins;
     the MPR wins over both.
  f  the ledger: a table per unit of the statement store, 'SMS nahi aaya' on an MPR-only day, the summary counts; staff refused.
  g  two SMS on one business day sum; sms_at is the earlier.
  R  a copy of the live store, switch ON, the real clock: counts only -- days with both / same / differ, owner lines, per unit coverage.
  S  staff-eye (CLAUDE.md, S444): the portal tiles and each due duty's door marker for shavez, alisha, darpan and manoj, switch off and on.
  M  no money row written by the code: day_entry, sale_item, cash_movement, the counter sheet, Docterz -- unchanged; upi rows only the walk's.
--expect-red: the same walk on the OLD files; every 'C:' check must be red (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import sqlite3
import subprocess
import sys
import time

KIT = "S562_BANK_SMS_STANDS_IN"
BASE = "https://followup.dr-manoj.in"
ROLE = {"darpan": "staff", "shavez": "manager", "alisha": "staff", "manoj": "doctor", "bhawna": "doctor"}
RUN, FAILS, CTRL, OUT = [0], [], [], []
D1, D2, D3, D4, D5 = "2027-03-02", "2027-03-04", "2027-03-08", "2027-03-10", "2027-03-11"
MID = {"clinic": "000561", "medical": "000562"}
WALK_KEY = "w562-walk-only-door-key"
MONEY_TABLES = ("day_entry", "sale_item", "cash_movement", "clinic_register_day", "clinic_day_line", "clinic_day_tender", "darpan_kal_day")


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


def clock(iso):
    for k in ("CLINIC_MONEY_NOW", "BANK_STANDIN_NOW", "BANK_SMS_NOW"):
        if iso:
            os.environ[k] = iso
        else:
            os.environ.pop(k, None)


def app_env(fin, dbp, adb, marg, dmap):
    work = os.path.dirname(dbp)
    key = os.path.join(work, "w562_walk.key")
    with open(key, "w") as fh:
        fh.write(WALK_KEY)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(marg),
                      ORDER_PUSH_NONE="1", DUTY_MAP_JSON=os.path.abspath(dmap), FINANCE_SSO_DIR=os.path.join(work, "nosso"),
                      RING_PORTAL_DIR=os.path.join(work, "nosso"), FINANCE_DEV_USER="", FINANCE_DEV_ROLE="", BANK_SMS_KEY_FILE=key,
                      PYTHONDONTWRITEBYTECODE="1")
    os.makedirs(os.environ["FINANCE_SSO_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_CRON_TOKEN"):
        os.environ.pop(k, None)
    sys.path.insert(0, fin)
    os.chdir(fin)


def load_app(fin):
    import finance_app as fa                                  # noqa: E402
    import bank_standin as BS                                 # noqa: E402
    import bank_sms as SMS                                    # noqa: E402
    import clinic_money as CM                                 # noqa: E402
    import darpan_kal as DK                                   # noqa: E402
    for m in (BS, SMS, CM, DK):
        assert m.__file__.startswith(fin), (m.__name__, m.__file__)
    return fa, BS, SMS, CM, DK


class Client:
    def __init__(self, fa):
        self.cl = fa.app.test_client(use_cookies=False)
        self.times = []

    def get(self, u, path, follow=False):
        t0 = time.time()
        r = self.cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")}, follow_redirects=follow)
        self.times.append((u, path, time.time() - t0, len(r.get_data())))
        return r.status_code, r.get_data()

    def post(self, u, path, data=None, js=None, headers=None):
        h = {"X-Clinic-User": u, "X-Clinic-Role": ROLE.get(u, "staff")} if u else {}
        h.update(headers or {})
        r = self.cl.post(path, base_url=BASE, headers=h, data=data, json=js)
        return r.status_code, r.get_data()

    def jget(self, u, path):
        s, b = self.get(u, path)
        try:
            return s, json.loads(b.decode("utf-8"))
        except ValueError:
            return s, {}


def sms_text(unit, amount_rs, credit):
    """A made-up ICICI settlement SMS: account XX000, the walk's merchant tail, a made-up balance."""
    return ("ICICI Bank Account XX000 credited:Rs. %s on %s. Info EZY*ICICIPOS_SET_10XX%s_. Available Balance is Rs. 5,000.00."
            % ("{:,.2f}".format(amount_rs), dt.date.fromisoformat(credit).strftime("%d-%b-%y"), MID[unit]))


def conn(dbp):
    c = sqlite3.connect(dbp, timeout=60)
    c.row_factory = sqlite3.Row
    return c


def money_print(dbp):
    c = conn(dbp)
    out = {}
    for t in MONEY_TABLES:
        try:
            rows = c.execute("SELECT * FROM %s ORDER BY 1" % t).fetchall()
            out[t] = (len(rows), hashlib.md5(repr([tuple(r) for r in rows]).encode("utf-8")).hexdigest())
        except sqlite3.OperationalError:
            out[t] = None
    for t, k in (("upi_statement", "merchant_id NOT LIKE 'W562%'"), ("upi_txn", "merchant_id NOT LIKE 'W562%'")):
        rows = c.execute("SELECT * FROM %s WHERE %s ORDER BY 1" % (t, k)).fetchall()
        out[t] = (len(rows), hashlib.md5(repr([tuple(r) for r in rows]).encode("utf-8")).hexdigest())
    c.close()
    return out


def setup_rows(dbp):
    """The made-up March-2027 world on the scratch copy (W562 keys): made-up merchant tails, the counter sheet and Docterz for the clinic,
    a day report for Sanjeevni, the expected time 10:00 (walk-only)."""
    c = conn(dbp)
    c.execute("UPDATE business_unit SET merchant_id=? WHERE code='clinic'", ("W562XX" + MID["clinic"],))
    c.execute("UPDATE business_unit SET merchant_id=? WHERE code='medical'", ("W562XX" + MID["medical"],))
    c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('bank_mpr.expect_hhmm','10:00','W562 walk')")
    for d, amt in ((D1, 123400), (D2, 500000), (D3, 300000), (D4, 80000), (D5, 125000)):
        c.execute("INSERT INTO clinic_register_day (business_date, cons_upi_p, entered_by, entered_at) VALUES (?,?,?,?)", (d, amt, "w562", d + " 20:00:00"))
        c.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,?,?,?,?,?,?)",
                  (d, "consult", 1, "W562 WALK", "W562-1", amt, "Online Payment"))
    for d, amt in ((D1, 200000), (D2, 70000), (D3, 40000)):
        cur = c.execute("INSERT INTO day_entry (unit, business_date, status, source, entered_by, entered_at) VALUES ('medical',?,'submitted','app','w562',?)",
                        (d, d + " 21:00:00"))
        c.execute("INSERT INTO sale_item (day_entry_id, unit, service, description, amount_p, mode, source, source_ref) VALUES (?,?,?,?,?,?,?,?)",
                  (cur.lastrowid, "medical", "pharmacy", "W562 walk", amt, "upi", "manual", "W562-1"))
    c.commit()
    c.close()


def land_mpr(dbp, unit, d, amount_p, taken):
    c = conn(dbp)
    mid = "W562-%s" % unit
    c.execute("INSERT INTO upi_statement (merchant_id, unit, statement_date, filename, parsed_total_p, txn_count, ingested_at) VALUES (?,?,?,?,?,?,?)",
              (mid, unit, d, "W562_walk.csv", amount_p, 1, taken))
    c.execute("INSERT INTO upi_txn (merchant_id, unit, txn_date, amount_p, rrn, mode, txn_time, ingested_at) VALUES (?,?,?,?,?,?,?,?)",
              (mid, unit, d, amount_p, "W562R%s%s" % (unit[:1], d[-2:]), "UPI", "11:00", taken))
    c.commit()
    c.close()


# ============================================================================================ the child: render with one code folder
def child(a):
    spec = json.load(open(a.spec, encoding="utf-8"))
    app_env(os.path.abspath(a.fin), os.path.abspath(a.db), a.adb, a.marg, a.map)
    clock(spec["now"])
    fa, BS, SMS, CM, DK = load_app(os.path.abspath(a.fin))
    C = Client(fa)
    out = {}
    for pg in spec["pages"]:
        u, path = pg[0], pg[1]
        s, b = C.get(u, path, follow=bool(pg[2:] and pg[2]))
        out["%s %s" % (u, path)] = [s, b.decode("utf-8", "replace")]
    c = conn(os.path.abspath(a.db))
    now = dt.datetime.fromisoformat(spec["now"]) if spec["now"] else dt.datetime.now().replace(microsecond=0)
    for unit, d in spec["dicts"]:
        out["standing %s %s" % (unit, d)] = BS.standing(c, unit, d, now=now)
        dd = BS.day(c, unit, d, now=now)
        out["day %s %s" % (unit, d)] = {k: v for k, v in dd.items()}
        out["owner_items %s" % unit] = BS.owner_items(c, [unit], now=now)
    c.close()
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, sort_keys=True, default=str)
    return 0


def first_diff(x, y):
    if x == y:
        return ""
    n = min(len(x), len(y))
    i = next((k for k in range(n) if x[k] != y[k]), n)
    return "differs at %d: old ...%r... new ...%r..." % (i, x[max(0, i - 50):i + 70], y[max(0, i - 50):i + 70])


def old_ledger(html):
    """The OLD ledger's figures: {(unit, 'dd-Mon'): (sms, mpr)} from 'SMS ₹ X · MPR ₹ Y' cells (Sanjeevni, Clinic)."""
    out = {}
    for m in re.finditer(r"<tr><td class='d'>([^<]+)</td>(.*?)</tr>", html, re.S):
        cells = re.findall(r"<td[^>]*>(.*?)</td>", m.group(2), re.S)
        for unit, cell in zip(("medical", "clinic"), cells):
            f = re.search(r"SMS ₹ ([\d,—]+) · MPR ₹ ([\d,—]+)", cell)
            if f:
                out[(unit, m.group(1))] = (f.group(1), f.group(2))
    return out


def new_ledger(html):
    """The NEW ledger's rows: {(unit, iso): dict(src, cells)}."""
    out = {}
    for m in re.finditer(r"<tr data-unit='([^']+)' data-day='([^']+)' data-src='([^']*)'>(.*?)</tr>", html, re.S):
        cells = [text(x).strip() for x in re.findall(r"<td[^>]*>(.*?)</td>", m.group(4), re.S)]
        out[(m.group(1), m.group(2))] = dict(src=m.group(3), cells=cells)
    return out


# ============================================================================================ the page look, after placing
def page_look(a):
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    app_env(fin, dbp, a.adb, a.marg, a.map)
    clock("")
    fa, BS, SMS, CM, DK = load_app(fin)
    C = Client(fa)
    c = conn(dbp)
    on = BS.sms_on(c)
    c.close()
    s1, h1 = C.get("manoj", "/finance/bank-sms")
    s2, h2 = C.get("manoj", "/finance/clinic/money")
    t1 = text(h1)
    nl = new_ledger(h1.decode("utf-8", "replace"))
    cov = re.findall(r"([A-Za-z ]+): SMS came on (\d+) of (\d+) days", t1)
    say("   /finance/bank-sms (manoj, the placed files, a copy of the live database, the real clock): %s, switch %s, %d unit table(s), %d day rows; %s"
        % (s1, "ON" if on else "OFF", len(set(k[0] for k in nl)), len(nl), "; ".join("%s %s of %s" % (n.strip(), x, y) for n, x, y in cov)))
    say("   /finance/clinic/money (manoj): %s, %d KB" % (s2, len(h2) // 1024))
    ok = (s1 == 200 and s2 == 200 and not on and "Bank SMS stands in for the MPR: OFF" in t1 and "Switch ON" in t1 and len(nl) >= 60 and cov)
    leak = re.search(r"\d{10}", "\n".join(OUT))
    say(("PAGE OK S562" if ok and not leak else "PAGE RED S562") + ": the ledger and Clinic money read as manoj, the switch OFF")
    return 0 if ok and not leak else 1


# ============================================================================================ the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--map"):
        ap.add_argument(k, required=True)
    for k in ("--oldfin", "--portal", "--spec", "--out"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    ap.add_argument("--page", action="store_true")
    ap.add_argument("--child", action="store_true")
    a = ap.parse_args()
    anywhere = os.environ.get("S562_WALK_ANYWHERE") == "1"
    for p in (a.fin, a.db, a.adb, a.marg) + ((a.oldfin,) if a.oldfin else ()):
        assert os.path.abspath(p).startswith("/tmp/") or anywhere, "the walk runs on scratch copies in /tmp only: %s" % p
    if a.child:
        return child(a)
    if a.page:
        return page_look(a)
    if not (a.oldfin and a.portal):
        ap.error("--oldfin and --portal are needed for the walk")
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    work = os.path.dirname(dbp)
    say("-- S562 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))
    pristine = os.path.join(work, "w562_pristine.db")
    copydb(dbp, pristine)                                     # the live store as copied, before any made-up row (for R)
    setup_rows(dbp)
    app_env(fin, dbp, a.adb, a.marg, a.map)
    fa, BS, SMS, CM, DK = load_app(fin)
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    C = Client(fa)
    FIRED = []

    def spy(unit, fn):
        def _s(con, d):
            FIRED.append((unit, d))
            return fn(con, d)
        return _s
    for unit_, fn_ in list(BS._HOOKS.items()):
        BS._HOOKS[unit_] = spy(unit_, fn_)
    say("   the units' hooks are watched: %s" % sorted(BS._HOOKS))
    W = {}

    def section(name, fn):
        say("-- " + name)
        try:
            fn()
        except Exception as e:                                # noqa: BLE001 -- a section that raises is red, the walk goes on
            import traceback                                  # noqa: PLC0415
            tb = traceback.format_exc().strip().splitlines()
            check("C: section '%s' ran to its end" % name.split()[0], False, "%s: %s | %s" % (type(e).__name__, str(e)[:160], " / ".join(x.strip() for x in tb[-4:])[:300]))

    def door(unit, amount_rs, credit, at):
        clock(at)
        s, b = C.post("", "/finance/api/bank-sms", data={"text": sms_text(unit, amount_rs, credit), "sender": "W562-WALK"},
                      headers={"X-Bank-Sms-Key": WALK_KEY})
        try:
            j = json.loads(b.decode("utf-8"))
        except ValueError:
            j = {}
        return s, j

    def bday(unit, d, now):
        c = conn(dbp)
        try:
            return BS.bank_day(c, unit, d, now=dt.datetime.fromisoformat(now))
        finally:
            c.close()

    def mday(d, now):
        c = conn(dbp)
        try:
            return CM.match_day(c, d, now=dt.datetime.fromisoformat(now))
        finally:
            c.close()

    def flag_status(d, key):
        c = conn(dbp)
        try:
            r = c.execute("SELECT status FROM clinic_money_flag WHERE business_date=? AND key=?", (d, key)).fetchone()
            return r[0] if r else None
        finally:
            c.close()

    def setting(key):
        c = conn(dbp)
        try:
            r = c.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
            return r[0] if r else None
        finally:
            c.close()

    c0 = conn(dbp)
    TOL = BS.tolerance_p(c0)
    c0.close()
    money0 = [None]

    # ============================================================================================ a
    def sa():
        n1 = "2027-03-03T11:30:00"
        s, j = door("clinic", 1234, "2027-03-03", "2027-03-03T07:02:15")
        s2, j2 = door("medical", 2000, "2027-03-03", "2027-03-03T07:04:40")
        check("the door stores both made-up SMS (clinic, Sanjeevni) as today: 200, stored, business day %s" % D1,
              s == 200 and s2 == 200 and j.get("stored") and j2.get("stored") and j.get("business_date") == D1 and j2.get("unit") == "medical", (s, j, s2, j2))
        clock(n1)
        C.get("shavez", "/finance/clinic/match/%s" % D1)          # the page works the day (sync_flags) -- as staff open it
        check("switch OFF, past 10:00, no MPR: the stored flag mpr_missing is open for %s (today's behaviour)" % D1, flag_status(D1, "mpr_missing") == "open",
              flag_status(D1, "mpr_missing"))
        money0[0] = money_print(dbp)
        pages = [("shavez", "/finance/clinic/match/%s" % D1), ("alisha", "/finance/clinic/match/%s" % D1), ("manoj", "/finance/clinic/match/%s" % D1),
                 ("manoj", "/finance/clinic/money"), ("darpan", "/finance/darpan/kal/api/day?date=%s" % D1),
                 ("darpan", "/finance/darpan/kal/api/day?date=%s" % D3), ("manoj", "/finance/darpan/kal/api/owner"), ("shavez", "/finance/clinic/match/%s" % D3),
                 ("manoj", "/finance/bank-sms")]
        dicts = [("clinic", D1), ("medical", D1), ("clinic", D3), ("medical", D3)]
        res = {}
        for which, f in (("old", os.path.abspath(a.oldfin)), ("new", fin)):
            cdb = os.path.join(work, "w562_cmp_%s.db" % which)
            copydb(dbp, cdb)
            spec = os.path.join(work, "w562_spec_%s.json" % which)
            outp = os.path.join(work, "w562_out_%s.json" % which)
            json.dump(dict(now=n1, pages=pages, dicts=dicts), open(spec, "w"))
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", "--fin", f, "--db", cdb, "--adb", a.adb, "--marg", a.marg,
                                "--map", a.map, "--spec", spec, "--out", outp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               timeout=900, cwd="/tmp")
            if p.returncode != 0 or not os.path.isfile(outp):
                check("the %s files render the pages in a child process" % which, False, p.stdout[-600:])
                return
            res[which] = json.load(open(outp, encoding="utf-8"))
        O, N = res["old"], res["new"]
        for u, path in pages[:-1]:
            k = "%s %s" % (u, path)
            check("switch OFF: %s as %s -- byte for byte the old files' page (%s)" % (path, u, N[k][0]), O[k] == N[k] and N[k][0] == 200,
                  first_diff(O[k][1], N[k][1]))
        for unit, d in dicts:
            for kind in ("standing", "day"):
                k = "%s %s %s" % (kind, unit, d)
                check("switch OFF: %s(%s, %s) -- the same dict as the old file's" % (kind, unit, d), O[k] == N[k], (O[k], N[k]))
        for unit in ("clinic", "medical"):
            k = "owner_items %s" % unit
            check("switch OFF: owner_items([%s]) the same as the old file's" % unit, O[k] == N[k], (O[k], N[k]))
        k = "manoj /finance/bank-sms"
        ol, nl = old_ledger(O[k][1]), new_ledger(N[k][1])
        bad = []
        for (unit, dm), (sm, mp) in ol.items():
            iso = next((iso for (u2, iso) in nl if u2 == unit and dt.date.fromisoformat(iso).strftime("%d-%b") == dm), None)
            if iso is None:
                bad.append((unit, dm, "no row"))
                continue
            cells = nl[(unit, iso)]["cells"]
            nsms = cells[2].replace("₹", "").strip() if len(cells) > 3 else ""
            nmpr = cells[4].replace("₹", "").strip() if len(cells) > 5 else ""
            if (sm != "—" and sm != nsms) or (mp != "—" and mp != nmpr):
                bad.append((unit, dm))
        W["ledger_compared"] = len(ol)
        check("switch OFF: the ledger's SMS and MPR figures equal the old page's on every (unit, day) it showed (%d cells)" % len(ol), ol and not bad, bad[:4])
        rl = {}                                               # the same on the live store as copied, the real clock: the last 30 real days
        for which, f in (("old", os.path.abspath(a.oldfin)), ("new", fin)):
            cdb = os.path.join(work, "w562_cmpr_%s.db" % which)
            copydb(pristine, cdb)
            spec = os.path.join(work, "w562_specr_%s.json" % which)
            outp = os.path.join(work, "w562_outr_%s.json" % which)
            json.dump(dict(now="", pages=[["manoj", "/finance/bank-sms"]], dicts=[]), open(spec, "w"))
            p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", "--fin", f, "--db", cdb, "--adb", a.adb, "--marg", a.marg,
                                "--map", a.map, "--spec", spec, "--out", outp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                               timeout=900, cwd="/tmp")
            rl[which] = json.load(open(outp, encoding="utf-8"))[k][1] if p.returncode == 0 and os.path.isfile(outp) else ""
        ol, nl = old_ledger(rl["old"]), new_ledger(rl["new"])
        bad = []
        for (unit, dm), (sm, mp) in ol.items():
            iso = next((iso for (u2, iso) in nl if u2 == unit and dt.date.fromisoformat(iso).strftime("%d-%b") == dm), None)
            cells = nl[(unit, iso)]["cells"] if iso else []
            nsms = cells[2].replace("₹", "").strip() if len(cells) > 3 else ""
            nmpr = cells[4].replace("₹", "").strip() if len(cells) > 5 else ""
            if iso is None or (sm != "—" and sm != nsms) or (mp != "—" and mp != nmpr):
                bad.append((unit, dm))
        check("switch OFF, the live store as copied, the real clock: the ledger's SMS and MPR figures equal the old page's (%d unit-days compared)" % len(ol),
              len(ol) >= 20 and not bad, (len(ol), bad[:4]))
        t = text(N[k][1])
        check("the ledger shows the switch OFF, with the owner's 'Switch ON'", "Bank SMS stands in for the MPR: OFF" in t and "Switch ON" in t, t[:200])
    section("a  switch OFF: today's pages", sa)

    # ============================================================================================ b
    def sb():
        n1 = "2027-03-03T11:30:00"
        clock(n1)
        s, h = C.post("shavez", "/finance/bank-sms", data={"act": "sms_standin", "on": "1"})
        check("a staff checker's POST to the switch is refused and changes nothing", s == 200 and "Only Dr Manoj" in text(h) and setting("bank_sms.standin_on") in (None, "0"),
              (s, setting("bank_sms.standin_on")))
        FIRED.clear()
        s, h = C.post("manoj", "/finance/bank-sms", data={"act": "sms_standin", "on": "1"})
        c = conn(dbp)
        aud = c.execute("SELECT by_whom, after_json FROM audit_log WHERE table_name='setting' AND action='bank_sms.standin_on' ORDER BY id DESC LIMIT 1").fetchone()
        c.close()
        check("C: his POST switches it ON (setting '1'), the page says so, and it is audited (by manoj)",
              s == 200 and setting("bank_sms.standin_on") == "1" and "Bank SMS stands in for the MPR: ON" in text(h) and aud is not None and aud[0] == "manoj",
              (s, setting("bank_sms.standin_on"), aud and aud[0]))
        check("C: switching on worked the SMS days again through each unit's hook (clinic and Sanjeevni %s)" % D1,
              ("clinic", D1) in FIRED and ("medical", D1) in FIRED, FIRED)
        b = bday("clinic", D1, n1)
        check("C: bank_day(clinic, %s): source 'sms', ₹1,234, sms_at '07:02', no MPR" % D1,
              b["source"] == "sms" and b["amount_p"] == 123400 and b["sms_at"] == "07:02" and b["mpr_p"] is None, b)
        m = mday(D1, n1)
        check("C: match_day(%s)['standin']['source'] == 'sms'; no mpr_missing flag; the day's line says the bank's SMS" % D1,
              (m.get("standin") or {}).get("source") == "sms" and not [f for f in m["flags"] if f["code"] == "mpr_missing"]
              and "bank's SMS" in " ".join(m["lines"]), (m.get("standin"), [f["code"] for f in m["flags"]], m["lines"]))
        check("C: the stored mpr_missing flag was cleared by the hook (the day worked again by itself)", flag_status(D1, "mpr_missing") == "cleared",
              flag_status(D1, "mpr_missing"))
        for u in ("shavez", "alisha"):
            s, h = C.get(u, "/finance/clinic/match/%s" % D1)
            t = text(h)
            check("C: %s's card: 'Bank SMS 07:02: ₹1,234 credited — the bank's MPR mail has not come yet'; never 'POS total'; no POS field after 10:00" % u,
                  s == 200 and "Bank SMS 07:02: ₹1,234 credited — the bank's MPR mail has not come yet" in t and "POS" not in t
                  and 'id="postotal"' not in h.decode("utf-8", "replace") and 'name="amount"' not in h.decode("utf-8", "replace"), (s, t[:300]))
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D1)
        cc = j.get("calc") or {}
        check("C: Darpan's day %s: online_source 'sms', ₹2,000, label 'बैंक SMS 07:04'; the POS field not offered nor shown" % D1,
              s == 200 and cc.get("online_source") == "sms" and cc.get("online_p") == 200000 and (cc.get("standin") or {}).get("label") == "बैंक SMS 07:04"
              and not (j.get("pos_total") or {}).get("offer") and not (j.get("pos_total") or {}).get("show"), (s, cc.get("online_source"), cc.get("standin"), j.get("pos_total")))
        c = conn(dbp)
        sd = BS.day(c, "clinic", D1, now=dt.datetime.fromisoformat(n1))
        c.close()
        check("C: day(clinic, %s) after the expected time: not offered, not shown, the SMS beside it" % D1,
              not sd["offer"] and not sd["show"] and (sd.get("sms") or {}).get("source") == "sms", sd)
    section("b  switch ON, the SMS in, the MPR not", sb)

    # ============================================================================================ c
    def sc():
        n2 = "2027-03-03T12:10:00"
        land_mpr(dbp, "clinic", D1, 123400, "2027-03-03T09:56:10")
        land_mpr(dbp, "medical", D1, 200000, "2027-03-03T09:56:40")
        clock(n2)
        FIRED.clear()
        s, h = C.get("manoj", "/finance/clinic/money")            # his page reads owner_items -> the sweep sees the MPR replace the SMS
        t = text(h)
        check("C: the hooks fired when the MPR replaced the SMS (clinic and Sanjeevni %s)" % D1, ("clinic", D1) in FIRED and ("medical", D1) in FIRED, FIRED)
        check("no owner line for an SMS equal to its MPR", s == 200 and "Bank SMS against the bank's MPR" not in t and "difference ₹" not in t, t[:200])
        b = bday("clinic", D1, n2)
        check("C: bank_day(clinic, %s): source 'mpr', mpr_at '09:56', sms_at '07:02', diff 0" % D1,
              b["source"] == "mpr" and b["mpr_at"] == "09:56" and b["sms_at"] == "07:02" and b["diff_p"] == 0 and b["mpr_p"] == 123400, b)
        want = "Bank SMS 07:02 ₹1,234 · MPR mail taken 09:56 ₹1,234 · same."
        for u in ("shavez", "manoj"):
            s, h = C.get(u, "/finance/clinic/match/%s" % D1)
            check("C: %s's card after the MPR: '%s'" % (u, want), s == 200 and want in text(h), text(h)[:300])
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D1)
        check("Darpan's day %s: the bank's own figure now (online_source 'bank')" % D1, (j.get("calc") or {}).get("online_source") == "bank", j.get("calc", {}).get("online_source"))
        c = conn(dbp)
        it = [i for i in BS.owner_items(c, None, now=dt.datetime.fromisoformat(n2)) if i["kind"].startswith("sms")]
        c.close()
        check("C: owner_items: no SMS line for %s (equal)" % D1, it == [] and hasattr(BS, "bank_day"), it)
    section("c  the MPR lands, equal to the SMS", sc)

    # ============================================================================================ d
    def sd_():
        n3 = "2027-03-05T12:00:00"
        door("clinic", 5000, "2027-03-05", "2027-03-05T07:05:30")
        door("medical", 700, "2027-03-05", "2027-03-05T07:06:10")
        land_mpr(dbp, "clinic", D2, 500000 + TOL + 10000, "2027-03-05T09:56:00")
        land_mpr(dbp, "medical", D2, 70000, "2027-03-05T09:57:00")
        clock(n3)
        dz = (TOL + 10000) // 100
        line = "Clinic Thu 04-Mar-2027: Bank SMS ₹5,000 (07:05) · MPR ₹%s (09:56) · difference ₹%s" % ("{:,}".format(5000 + dz), "{:,}".format(dz))
        s, h = C.get("manoj", "/finance/clinic/money")
        t = text(h)
        check("C: his Clinic money page: exactly ONE SMS line -- '%s'" % line, s == 200 and t.count(line) == 1 and t.count("Bank SMS ₹") == 1, t[t.find("Bank SMS"):][:200])
        s, j = C.jget("manoj", "/finance/darpan/kal/api/owner")
        sl = [i for i in j.get("items") or [] if str(i.get("kind", "")).startswith("sms")]
        check("his Kal card (Sanjeevni): no SMS line (the Sanjeevni SMS equals its MPR)", s == 200 and sl == [], sl)
        s, h = C.get("bhawna", "/finance/clinic/money")
        check("Dr Bhawna's Clinic money page: no SMS line, no difference", s == 200 and "Bank SMS ₹" not in text(h) and line not in text(h), s)
        for u, path in (("shavez", "/finance/clinic/match/%s" % D2), ("alisha", "/finance/clinic/match/%s" % D2), ("shavez", "/finance/bank-sms")):
            s, h = C.get(u, path)
            t = text(h)
            check(("C: " if path == "/finance/bank-sms" else "") + "%s's %s: no difference text (no 'difference ₹', no 'differ', no SMS-vs-MPR line)" % (u, path),
                  s == 200 and "difference ₹" not in t and "differ" not in t and "MPR more" not in t and "Bank SMS 07:05" not in t
                  and (path != "/finance/bank-sms" or ("Business day" in t and "Difference" not in t)), (s, t[:160]))
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D2)
        check("Darpan's day %s: no difference text" % D2, s == 200 and "difference" not in json.dumps(j, ensure_ascii=False).lower(), s)
        s, h = C.get("manoj", "/finance/clinic/match/%s" % D2)
        check("C: his own card %s shows it: 'difference ₹%s (MPR more)'" % (D2, "{:,}".format(dz)), "difference ₹%s (MPR more)" % "{:,}".format(dz) in text(h), text(h)[:200])
    section("d  the MPR differs beyond the tolerance", sd_)

    # ============================================================================================ e
    def se():
        n4 = "2027-03-09T11:00:00"
        clock(n4)
        s, h = C.get("shavez", "/finance/clinic/match/%s" % D3)
        hh = h.decode("utf-8", "replace")
        check("no SMS, no MPR, past 10:00: the clinic card offers the one POS field, as today", s == 200 and hh.count('id="postotal"') == 1 and 'name="amount"' in hh, s)
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D3)
        check("…and Darpan's form offers it", (j.get("pos_total") or {}).get("offer") is True, j.get("pos_total"))
        s, h = C.post("manoj", "/finance/clinic/money", data={"act": "standin_type", "unit": "clinic", "date": D3, "amount": "3000"})
        s2, j2 = C.post("manoj", "/finance/darpan/kal/api/pos-total", js={"date": D3, "amount_p": 40000})
        c = conn(dbp)
        sp = BS.standing(c, "clinic", D3, now=dt.datetime.fromisoformat(n4))
        c.close()
        check("C: his own POS total stands for the clinic with source 'pos'", sp is not None and sp.get("source") == "pos" and sp["amount_p"] == 300000, sp)
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D3)
        check("…and for Sanjeevni: online_source 'pos'", (j.get("calc") or {}).get("online_source") == "pos", (s2, (j.get("calc") or {}).get("online_source")))
        door("clinic", 3000, "2027-03-09", "2027-03-09T11:05:00")
        door("medical", 400, "2027-03-09", "2027-03-09T11:06:00")
        n5 = "2027-03-09T11:20:00"
        clock(n5)
        c = conn(dbp)
        sp = BS.standing(c, "clinic", D3, now=dt.datetime.fromisoformat(n5))
        c.close()
        check("C: an SMS arriving afterwards wins over the confirmed POS: source 'sms', sms_at '11:05'", sp is not None and sp.get("source") == "sms" and sp["sms_at"] == "11:05", sp)
        s, h = C.get("shavez", "/finance/clinic/match/%s" % D3)
        t = text(h)
        check("C: the card says 'Bank SMS 11:05: ₹3,000 credited' and no POS box", "Bank SMS 11:05: ₹3,000 credited" in t and 'id="postotal"' not in h.decode("utf-8", "replace"), t[:300])
        s, j = C.jget("darpan", "/finance/darpan/kal/api/day?date=%s" % D3)
        check("C: Darpan's day: online_source 'sms' over his POS figure", (j.get("calc") or {}).get("online_source") == "sms", (j.get("calc") or {}).get("online_source"))
        land_mpr(dbp, "clinic", D3, 300000, "2027-03-09T15:56:00")
        land_mpr(dbp, "medical", D3, 40000, "2027-03-09T15:56:30")
        n6 = "2027-03-09T16:10:00"
        clock(n6)
        b = bday("clinic", D3, n6)
        c = conn(dbp)
        sp = BS.standing(c, "clinic", D3, now=dt.datetime.fromisoformat(n6))
        c.close()
        check("C: the MPR wins over both: bank_day source 'mpr' (mail taken 15:56), standing None", b["source"] == "mpr" and b["mpr_at"] == "15:56" and sp is None, (b, sp))
        s, h = C.get("manoj", "/finance/clinic/money")             # the sweep closes the POS row
        c = conn(dbp)
        rows = [r[0] for r in c.execute("SELECT status FROM bank_standin WHERE unit='clinic' AND business_date=? ORDER BY id", (D3,))]
        c.close()
        check("the POS row is kept, replaced by the bank (S496 as before)", rows == ["replaced"], rows)
    section("e  no SMS, no MPR: the POS field; then the SMS; then the MPR", se)

    # ============================================================================================ f
    def sf():
        land_mpr(dbp, "clinic", D4, 80000, "2027-03-11T08:56:00")
        n7 = "2027-03-12T12:00:00"
        clock(n7)
        s, h = C.get("manoj", "/finance/bank-sms")
        hh = h.decode("utf-8", "replace")
        nl = new_ledger(hh)
        c0f = conn(dbp)
        units = BS.units(c0f)
        per = {u: len([k for k in nl if k[0] == u]) for u in units}
        check("C: the ledger has one table per unit of the statement store (%s), 30 business days each" % ", ".join(units),
              s == 200 and units and all(per[u] == 30 for u in units) and all(("<h2>%s</h2><table" % BS.unit_label(c0f, u)) in hh for u in units), per)
        c0f.close()
        r4 = nl.get(("clinic", D4)) or {}
        check("C: an MPR-only day reads 'SMS nahi aaya' (clinic %s), what stands: MPR" % D4, r4.get("src") == "mpr" and r4.get("cells", [""])[1:2] == ["SMS nahi aaya"],
              r4)
        r1 = nl.get(("clinic", D1)) or {}
        check("C: clinic %s: SMS time 07:02 · MPR mail taken 09:56 · same · MPR" % D1, r1.get("cells", [])[1:2] == ["07:02"] and r1["cells"][3] == "09:56"
              and r1["cells"][5] == "same" and r1["cells"][6] == "MPR", r1)
        r5 = nl.get(("clinic", D5)) or {}
        check("a day with neither in the window reads '—'", any(v["cells"][1:2] and v["cells"][1].startswith("—") for k, v in nl.items() if k[0] == "lab"), "")
        c = conn(dbp)
        first = c.execute("SELECT MIN(business_date) FROM bank_sms_settlement").fetchone()[0]
        both = equal = 0
        for u, d in c.execute("SELECT DISTINCT unit, business_date FROM bank_sms_settlement WHERE business_date<?", (n7[:10],)).fetchall():
            st = c.execute("SELECT 1 FROM upi_statement WHERE unit=? AND statement_date=?", (u, d)).fetchone()
            if st is None:
                continue
            sm = c.execute("SELECT SUM(amount_p) FROM bank_sms_settlement WHERE unit=? AND business_date=?", (u, d)).fetchone()[0]
            mp = c.execute("SELECT COALESCE(SUM(amount_p),0), COUNT(*) FROM upi_txn WHERE unit=? AND txn_date=?", (u, d)).fetchone()
            mpv = mp[0] if mp[1] else (c.execute("SELECT parsed_total_p FROM upi_statement WHERE unit=? AND statement_date=?", (u, d)).fetchone()[0] or 0)
            both += 1
            equal += 1 if mpv == sm else 0
        cov = {}
        for u in units:
            r = c.execute("SELECT COUNT(*), SUM(EXISTS(SELECT 1 FROM bank_sms_settlement s WHERE s.unit=t.unit AND s.business_date=t.statement_date)) "
                          "FROM upi_statement t WHERE t.unit=? AND t.statement_date>=? AND t.statement_date<?", (u, first, n7[:10])).fetchone()
            cov[u] = (int(r[1] or 0), int(r[0] or 0))
        labels = {u: BS.unit_label(c, u) for u in units}
        c.close()
        t = text(h)
        want = "Since %s: %d days with both — %s." % (BS.human(first), both, "all equal" if both == equal else "%d equal, %d differ" % (equal, both - equal))
        check("C: the summary on top: '%s' (counted here independently)" % want, want in t, t[t.find("Since"):][:160])
        cw = ["%s: SMS came on %d of %d days" % (labels[u], cov[u][0], cov[u][1]) for u in units]
        check("C: per unit: %s" % " | ".join(cw), all(x in t for x in cw), t[t.find("SMS came"):][:200])
        for u in ("alisha", "darpan"):
            s, h = C.get(u, "/finance/bank-sms")
            check("a staff login (%s) is refused the ledger as today (403)" % u, s == 403, s)
    section("f  the ledger", sf)

    # ============================================================================================ g
    def sg():
        door("clinic", 1000, "2027-03-12", "2027-03-12T07:09:00")
        door("clinic", 250, "2027-03-12", "2027-03-12T07:01:00")
        b = bday("clinic", D5, "2027-03-12T12:30:00")
        check("C: two SMS on one business day sum (₹1,250) and sms_at is the earlier (07:01)", b["sms_p"] == 125000 and b["sms_at"] == "07:01" and b["source"] == "sms", b)
        clock("2027-03-12T12:30:00")
        s, h = C.get("alisha", "/finance/clinic/match/%s" % D5)
        check("C: the card: 'Bank SMS 07:01: ₹1,250 credited'", "Bank SMS 07:01: ₹1,250 credited" in text(h), text(h)[:200])
    section("g  two SMS on one day", sg)

    # ============================================================================================ M
    def sm():
        m1 = money_print(dbp)
        ch = [t for t in m1 if money0[0] and m1[t] != money0[0][t]]
        check("C: no money row written by the code: %s unchanged (upi rows: only the walk's own W562 rows were added)" % ", ".join(sorted(m1)),
              money0[0] is not None and not ch and hasattr(BS, "bank_day"), ch)
    section("M  no money row", sm)

    # ============================================================================================ R
    def sr():
        clock("")
        rp = os.path.join(work, "w562_real.db")
        copydb(pristine, rp)
        c = conn(rp)
        c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('bank_sms.standin_on','1','W562 walk, a copy')")
        c.commit()
        now = dt.datetime.now().replace(microsecond=0)
        days = c.execute("SELECT DISTINCT unit, business_date FROM bank_sms_settlement ORDER BY 2").fetchall()
        same = differ = standing = 0
        for u, d in days:
            b = BS.bank_day(c, u, d, now=now)
            if b["source"] == "mpr" and b["sms_p"] is not None:
                same += 1 if not b["diff_p"] else 0
                differ += 1 if b["diff_p"] else 0
            elif b["source"] == "sms":
                standing += 1
        lines = [i for i in BS.owner_items(c, None, now=now) if i["kind"].startswith("sms")]
        html = SMS._ledger(c, now.date(), True, BS)
        cov = re.findall(r"<li data-cov='([^']+)'>[^:]+: SMS came on (\d+) of (\d+) days</li>", html)
        c.close()
        W["R"] = dict(days=len(days), same=same, differ=differ, standing=standing, lines=len(lines), cov=cov)
        say("   R (a copy of the live store, switch ON, the real clock): %d SMS business days -- %d with both: %d same, %d differ; %d standing (MPR not in yet); "
            "%d owner line(s); SMS came on: %s" % (len(days), same + differ, same, differ, standing, len(lines), ", ".join("%s %s of %s" % x for x in cov)))
        check("C: R: every SMS day with an MPR is 'same' (%d), none differ, no owner line" % same, same >= 22 and differ == 0 and not lines, W["R"])
    section("R  the real store, counts only", sr)

    # ============================================================================================ S
    def ss():
        clock("")
        m = json.load(open(a.map, encoding="utf-8"))
        persons = ("shavez", "alisha", "darpan", "manoj")
        doors = ("/finance/clinic/match", "/finance/clinic/money", "/finance/darpan/kal", "/finance/approvals")
        duties = [d for d in m["duties"] if d.get("person") in persons and d.get("door") in doors]
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; out={}\n"
                "for u, r in %r: out[u]=[t['name'] for g, ts in po._visible_sections(r, False, u) for t in ts]\n"
                "print('TILES ' + json.dumps(out))" % (a.portal, [(u, ROLE[u]) for u in persons]))
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w562-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [x for x in pp.stdout.splitlines() if x.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else {}
        miss_t = [(d["person"], d["tile"]) for d in duties if d.get("tile") and d["tile"] not in tiles.get(d["person"], [])]
        check("staff-eye: each duty's tile at these doors is on its person's portal home (%s; the real portal.py + the grants file, a walk-only secret)"
              % ", ".join(sorted(set("%s:%s" % (d["person"], d["tile"]) for d in duties))), tiles and not miss_t, (miss_t, pp.stdout[-200:]))
        ro = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
        due = {}
        for d in duties:
            try:
                due[d["id"]] = int(ro.execute(d["due_sql"]).fetchone()[0] or 0) if d.get("due_sql") else 0
            except sqlite3.Error as e:
                due[d["id"]] = "error %s" % str(e)[:60]
        ro.close()
        say("   duties at these doors due now (their due_sql on the walk's copy): %s" % due)
        def seen(s, h, d):
            return s == 200 and not (isinstance(due[d["id"]], int) and due[d["id"]] > 0 and d.get("door_marker")
                                     and d["door_marker"] not in h and d["door_marker"] not in text(h))
        for sw in ("0", "1"):
            c = conn(dbp)
            c.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('bank_sms.standin_on',?,'W562 walk')", (sw,))
            c.commit()
            c.close()
            miss = []
            for d in duties:
                s, h = C.get(d["person"], d["door"], follow=True)
                if not seen(s, h.decode("utf-8", "replace"), d):
                    miss.append(d)
            old_miss = []
            if miss:                                          # the same doors on the OLD files (a child, its own copy): a gap they share is not this kit's
                cdb = os.path.join(work, "w562_eye_old.db")
                copydb(dbp, cdb)
                spec, outp = os.path.join(work, "w562_eye_spec.json"), os.path.join(work, "w562_eye_out.json")
                json.dump(dict(now="", pages=[[d["person"], d["door"], True] for d in miss], dicts=[]), open(spec, "w"))
                p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child", "--fin", os.path.abspath(a.oldfin), "--db", cdb, "--adb", a.adb,
                                    "--marg", a.marg, "--map", a.map, "--spec", spec, "--out", outp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   universal_newlines=True, timeout=900, cwd="/tmp")
                O = json.load(open(outp, encoding="utf-8")) if p.returncode == 0 and os.path.isfile(outp) else {}
                old_miss = [d for d in miss if ("%s %s" % (d["person"], d["door"])) in O and not seen(O["%s %s" % (d["person"], d["door"])][0],
                                                                                                         O["%s %s" % (d["person"], d["door"])][1], d)]
                for d in old_miss:
                    W.setdefault("eye_gap", set()).add("%s: marker '%s' not on %s (the old files too)" % (d["id"], d["door_marker"], d["door"]))
            mine = [(d["person"], d["id"]) for d in miss if d not in old_miss]
            check("staff-eye, switch %s: every door answers 200 to its person and shows each due duty's marker -- none hidden by this kit (%d duties%s)"
                  % ("ON" if sw == "1" else "OFF", len(duties), ("; the old files miss the same %d: %s" % (len(old_miss), ", ".join(d["id"] for d in old_miss))) if old_miss else ""),
                  duties and not mine and all(isinstance(v, int) for v in due.values()), mine[:4])
        for g in sorted(W.get("eye_gap", ())):
            say("   NOTE (outside this kit, for the report): %s" % g)
        heavy = [(u, p, round(t_, 2), n) for u, p, t_, n in C.times if (t_ >= 3.0 or n >= 150000) and u != "manoj"]
        check("every staff page the walk opened: under 150 KB and under 3 s (%d reads)" % len([x for x in C.times if x[0] != "manoj"]), not heavy, heavy[:4])
        led = [round(t_, 2) for u, p, t_, n in C.times if p == "/finance/bank-sms" and u == "manoj"]
        say("   the ledger page took %s s per read (manoj)" % led)
    section("S  staff-eye", ss)

    # ---------------------------------------------------------------- the end
    clock("")
    for p in (pristine,) + tuple(os.path.join(work, x) for x in os.listdir(work) if x.startswith("w562_") and (x.endswith(".db") or x.endswith(".json"))):
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
    say("WALK OK S562: %d checks green (switch off = today; the SMS stands; the MPR takes over; the owner's one line; the POS order; the ledger; "
        "two SMS; no money row; the real store; staff-eye)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
