#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s604_v2.py -- kit S613_S605_FOLLOWUP (22-Oct-2026), brief section 3.5 (F-957). S604's purchase-page scenarios, re-walked so
that they lay their OWN days. Runs on SCRATCH folders and SCRATCH databases only (/tmp).

    python3 -B walk_s604_v2.py --fin <scratch /root/finance with the purchase_app.py under test> --db <COPY of finance.db>
                               --adb <COPY of assets.db> --marg <scratch marg_ingest> --por <scratch /root/portal copy>
                               --dump <dir> [--expect-red]

Why a second walk: S604's walk_s604.py read the live day (20-Oct's refused export by --text, the Bass Pharma twin bills 542 / 579 that
data_s604.py has since merged on the live database), so on today's live bytes it reads 'WALK RED S604: 7 failure(s)' identically on the
new and the old file -- it proves nothing any more (F-957: a walk that lays no days of its own). This walk builds its OWN synthetic
exports -- the bill-wise, supplier-wise and item-wise pushes the medical PC sends to /api/push -- for January 2030 (as make_s604.py's
selftest dates its made-up text 01-01-2030 TO 31-01-2030), with its OWN suppliers ('W604V2 ...') and bills (9001-9006), and finds every
row again by key (supplier key + bill number + date, export md5, audit ref), never by counting (CLAUDE.md rule 3). Every scenario starts
from the quiet copy (restored by the sqlite backup API). The finance pages through the walk's own header session; /api/push through its
own random machine token; the portal homes through its own portal secret and user store (never the live ones).
--expect-red is the negative control: the same walk on purchase_app.py.bak_S604_60f2d846, every 'C:' check must be red.
The reader-side controls (marg_txt.py, the medical PC's reader) are not re-walked: their OLD (a59a222f) is not on the box.
No account or phone number is printed (ten digits or more masked). Prints 'WALK OK S604v2 ...'."""
import argparse
import datetime as dt
import hashlib
import html as _html
import importlib.util
import json
import os
import re
import secrets
import sqlite3
import sys
import time

KIT = "S613_S605_FOLLOWUP"
BASE = "https://followup.dr-manoj.in"
ROLE = {"manoj": "doctor", "shavez": "manager", "amir": "staff"}
P = "/finance/purchase"
M = "2030-01"                                   # the walk's own month (far future: no real bill can be in it)
FIRST, LAST = "2030-01-01", "2030-01-31"
LIVE_MONTHS = ("2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09", "2026-10")

# the walk's own suppliers: bill-wise prints the name with the city, supplier-wise the bare name (supplier_key joins them)
N_A_BW, N_A_SW = "W604V2 ALPHA PHARMA BAREILLY", "W604V2 ALPHA PHARMA"
N_R_BW, N_R_SW = "W604V2 RETURNS AGENCY BAREILLY", "W604V2 RETURNS AGENCY"
N_TL, N_TC = "W604V2 BASS PHARMA DISTRIBUTORS PVT LTD", "W604V2 BASS PHARMA DISTRIBUTORS PVT"   # the long name, the clipped one
N_MN, N_DP = "W604V2 MANNAT MEDICOS", "W604V2 DEEPAM AGENCIES"
K_A, K_R, K_TL, K_TC = "W604V2 ALPHA PHARMA", "W604V2 RETURNS AGENCY", N_TL, N_TC
# (bill-wise name, supplier-wise name, bill no, date, Marg amount in paise; a return carries Marg's minus sign)
BILLS = [(N_A_BW, N_A_SW, "9001", "2030-01-10", 100000),
         (N_A_BW, N_A_SW, "9002", "2030-01-12", 50000),
         (N_R_BW, N_R_SW, "9003", "2030-01-15", -30000),
         (N_TL, N_TC, "9004", "2030-01-20", 159700)]
# item lines (positive, as Marg prints them -- the return's lines too): (name, bill no, date, [net paise])
LINES = [(N_A_BW, "9001", "2030-01-10", [60000, 40000]),
         (N_A_BW, "9002", "2030-01-12", [50000]),
         (N_R_BW, "9003", "2030-01-15", [10000, 20000]),
         (N_TL, "9004", "2030-01-20", [159700])]
MARG_P = sum(b[4] for b in BILLS)               # 279700: the sheet, and the item-wise figure with the return counted as a return
R_REFUSED_STOP = "the medical PC refused it: PURCHASE text -- the reader refused it (line 177)"
R_REFUSED_OTHER = ("the medical PC refused it: PURCHASE text -- a purchase statement the reader cannot take (its title or column heads "
                   "are not the ones it knows)")
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


def h2(tag):
    """A 32-hex md5 for the walk's own pushes and rows (api/push takes nothing else); found again by this same key."""
    return hashlib.md5(("S604v2 walk " + tag).encode()).hexdigest()


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst, timeout=60)
    s.backup(d)
    d.close()
    s.close()


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def portal_setup(por):
    """The walk's OWN portal secret and user store in the scratch portal folder (S444's shape): never the live ones."""
    assert por.startswith("/tmp/"), "the walk writes its own portal_config only into a scratch folder"
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in ROLE}
    with open(os.path.join(por, "portal_config.py"), "w") as fh:
        fh.write("# W604v2 walk only -- a random secret and seed made for this walk\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\n"
                 "PORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(8)))
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


def app_env(a, dbp, token, secret, store):
    por = os.path.abspath(a.por)
    os.environ.update(FINANCE_DB=dbp, ASSETS_DB=os.path.abspath(a.adb), FINANCE_ALLOW_HEADER_AUTH="1", MARG_INGEST_DIR=os.path.abspath(a.marg),
                      ORDER_PUSH_NONE="1", FINANCE_SSO_DIR=por, RING_PORTAL_DIR=os.path.join(os.path.dirname(dbp), "nosso"), FINANCE_DEV_USER="",
                      FINANCE_DEV_ROLE="", FINANCE_MARG_TOKEN=token, CLINIC_PORTAL_DIR=por, PYTHONDONTWRITEBYTECODE="1",
                      CLINIC_SSO_SECRET=secret, CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(por, "tile_grants.json"))
    os.makedirs(os.environ["RING_PORTAL_DIR"], exist_ok=True)
    for k in ("ORDER_TODAY", "ORDER_PUSH_STUB", "ORDER_TICK", "ORDER_CLOCK", "FINANCE_CRON_TOKEN", "SPINE_DB", "SARVAM_API_KEY"):
        os.environ.pop(k, None)


class Ctx(object):
    """The loaded app, its client, the database path and the quiet copy."""

    def __init__(self, fin, dbp, token):
        self.fin, self.dbp, self.token = fin, dbp, token
        import finance_app as fa                              # noqa: E402
        import purchase_app as PA                             # noqa: E402
        for m in (fa, PA):
            assert m.__file__.startswith(fin), m.__file__
        self.fa, self.PA = fa, PA
        self.cl = fa.app.test_client(use_cookies=False)
        self.NEW = hasattr(PA, "_lock_gate")
        self.pristine = dbp + ".quiet"
        copy_db(dbp, self.pristine)

    def reset(self):
        copy_db(self.pristine, self.dbp)

    def conn(self):
        c = sqlite3.connect(self.dbp, timeout=60)
        c.row_factory = sqlite3.Row
        return c

    def GET(self, u, path):
        r = self.cl.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        return r.status_code, r.get_data().decode("utf-8", "replace")

    def POST(self, u, path, body):
        r = self.cl.post(path, base_url=BASE, json=body, headers={"X-Clinic-User": u, "X-Clinic-Role": ROLE[u]})
        j = r.get_json(silent=True)
        return r.status_code, (j if j is not None else r.get_data().decode("utf-8", "replace")[:300])

    def push(self, body):
        r = self.cl.post(P + "/api/push", base_url=BASE, json=body, headers={"X-Finance-Marg": self.token})
        return r.status_code, r.get_json(silent=True)

    def summary(self, c, m=M):
        return self.PA._month_summary(c, m)

    def gate(self, c, m=M):
        """(can, reasons) as the file under test decides the lock: _lock_gate on NEW, can_finalise on OLD."""
        s = self.PA._month_summary(c, m)
        if hasattr(self.PA, "_lock_gate"):
            return self.PA._lock_gate(c, m, s)
        return s["can_finalise"], s["reasons"]


# ---------------------------------------------------------------------------------------------- the walk's own synthetic exports
def body(typ, tag, stamp, rows, pf=FIRST, pt=LAST, grand=None):
    md5 = h2(tag)
    if grand is None:
        grand = sum(int(r.get("cash_p", 0)) + int(r.get("credit_p", 0)) for r in rows) if typ in ("BILLWISE", "SUPPLIERWISE") \
            else sum(int(r.get("net_amount_p") or 0) for r in rows)
    return {"type": typ, "md5": md5, "file": "W604V2_%s_%s.XLS" % (typ, md5[:8]), "period_from": pf, "period_to": pt,
            "export_stamp": stamp, "n_rows": len(rows), "grand_amount_p": grand, "rows": rows}


def bill_row(name, bno, d, amount_p):
    return {"supplier": name, "bill_no": bno, "bill_date": d, "cash_p": 0, "credit_p": amount_p}


def line_rows(skip=()):
    out = []
    for name, bno, d, nets in LINES:
        if bno in skip:
            continue
        for j, n in enumerate(nets):
            out.append({"supplier": name, "bill_no": bno, "bill_date": d, "item": "W604V2 TESTMED %s-%d" % (bno, j), "packing": "10'S",
                        "batch": "WB%s%d" % (bno, j), "expiry": "12/31", "tax": 5.0, "qty": 1.0, "free": 0.0, "rate_p": n,
                        "discount_pct": 0.0, "amount_p": n, "net_rate_p": n, "net_amount_p": n, "direction": "PURCHASE"})
    return out


def bill_id(c, key, bno, d):
    r = c.execute("SELECT id FROM purchase_bill WHERE supplier_norm=? AND bill_no=? AND bill_date=?", (key, bno, d)).fetchone()
    return r[0] if r else None


def bills_no(c, bno, d):
    return [dict(r) for r in c.execute("SELECT id, supplier_norm, bill_no, bill_date, bw_md5, sw_md5, reason FROM purchase_bill "
                                       "WHERE bill_no=? AND bill_date=? ORDER BY id", (bno, d))]


def eff_ids(c, ids):
    if not ids:
        return []
    q = ("SELECT b.id FROM purchase_bill b WHERE b.id IN (%s) AND EXISTS (SELECT 1 FROM purchase_export e WHERE e.superseded_by IS NULL "
         "AND (e.md5=b.bw_md5 OR e.md5=b.sw_md5))" % ",".join("?" * len(ids)))
    return sorted(r[0] for r in c.execute(q, ids))


# ======================================================================================================= the walk
def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]       # never import from the kit folder
    ap = argparse.ArgumentParser()
    for k in ("--fin", "--db", "--adb", "--marg", "--por", "--dump"):
        ap.add_argument(k, default="")
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    for k in ("fin", "db", "adb", "marg", "por", "dump"):
        if not getattr(a, k):
            ap.error("--%s is needed" % k)
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    for p in (fin, dbp, os.path.abspath(a.adb), os.path.abspath(a.marg), os.path.abspath(a.por)):
        assert p.startswith("/tmp/"), "the walk runs on scratch copies in /tmp only: %s" % p
    os.makedirs(a.dump, exist_ok=True)
    say("-- S604v2 walk on the %s: %s . db %s" % ("OLD file (negative control)" if a.expect_red else "new file", fin, os.path.basename(dbp)))
    say("   the reader-side controls (marg_txt.py, the medical PC's reader) are not re-walked: their OLD (a59a222f) is not on the box")
    say("   not re-walked either: data_s604.py (a one-time step on the live bills 542 / 579, done on 20-Oct) and the live months' figures")
    token = secrets.token_hex(16)
    secret, pw, store = portal_setup(os.path.abspath(a.por))
    app_env(a, dbp, token, secret, store)
    sys.path.insert(0, fin)
    os.chdir(fin)
    X = Ctx(fin, dbp, token)
    PA = X.PA
    say("   the real finance app loaded from the scratch folder; parts that did not load: %s; purchase_app %s (%s)"
        % ([n for n, _w in getattr(X.fa, "_MOUNT_FAILED", [])] or "none", hashlib.md5(open(os.path.join(fin, "purchase_app.py"), "rb").read()).hexdigest()[:8],
           "NEW" if X.NEW else "OLD"))
    DUMP = {}

    # ------------------------------------------------------------------------------------- the walk's month must be empty on the copy
    c = X.conn()
    occ = dict(bills=c.execute("SELECT 1 FROM purchase_bill WHERE month=? OR bill_no IN ('9001','9002','9003','9004','9005','9006') "
                               "AND bill_date LIKE '2030-%' LIMIT 1", (M,)).fetchone() is not None,
               lines=c.execute("SELECT 1 FROM purchase_line WHERE month=? LIMIT 1", (M,)).fetchone() is not None,
               exports=c.execute("SELECT 1 FROM purchase_export WHERE period_from<=? AND period_to>=? LIMIT 1", (LAST, FIRST)).fetchone() is not None,
               mine=c.execute("SELECT 1 FROM purchase_bill WHERE supplier_norm LIKE 'W604V2 %' LIMIT 1").fetchone() is not None,
               month=c.execute("SELECT 1 FROM purchase_month WHERE month=? LIMIT 1", (M,)).fetchone() is not None)
    c.close()
    if not check("the copy holds nothing in the walk's own month %s (no bill, line, export, month row, no 'W604V2' supplier)" % M, not any(occ.values()), occ):
        say("WALK RED S604v2: 1 failure(s): the walk's month is not empty on the copy -- nothing walked")
        return 1

    def lay(itemwise=True, skip_lines=(), sw=True, sw_pt=LAST, sw_tag="sw1"):
        """The walk's own January 2030 onto the quiet copy: bill-wise, then supplier-wise (Bass's clipped name), then item lines."""
        X.reset()
        got = {}
        st, j = X.push(body("BILLWISE", "bw1", "20300201-090000", [bill_row(b[0], b[2], b[3], b[4]) for b in BILLS]))
        got["bw"] = (st, j)
        if sw:
            st, j = X.push(body("SUPPLIERWISE", sw_tag, "20300201-090500", [bill_row(b[1], b[2], b[3], b[4]) for b in BILLS], pt=sw_pt))
            got["sw"] = (st, j)
        if itemwise:
            st, j = X.push(body("ITEMWISE", "iw1", "20300201-091000", line_rows(skip_lines)))
            got["iw"] = (st, j)
        ok = all(v[0] == 200 and isinstance(v[1], dict) and v[1].get("stored") is True for v in got.values())
        return ok, got

    # ============================================================================================ 1: returns counted as returns (3.2)
    def s1():
        ok, got = lay()
        check("the walk's own three exports (bill-wise, supplier-wise, item-wise, 01-31 Jan 2030) are taken by /api/push", ok, got)
        c = X.conn()
        s = X.summary(c)
        rid = bill_id(c, K_R, "9003", "2030-01-15")
        say("   January 2030: Marg %s, item-wise %s, %d bills, returns %s, signed %s, no lines %s"
            % (s["marg_p"], s["itemwise_p"], len(s["bills"]), [x["bill"]["id"] for x in s["returns"]], s.get("signed"),
               [(b["id"], b["bill_no"]) for b in s["no_lines"]]))
        check("the return bill 9003 is on the copy, carrying Marg's minus sign", rid is not None and any(b["id"] == rid and b["marg_p"] == -30000 for b in s["bills"]), rid)
        check("C: (2) the item-wise figure counts the return's positive lines as a return: %d paise (the sheet's own figure)" % MARG_P,
              s["itemwise_p"] == MARG_P, s["itemwise_p"])
        check("C: (2) the returns bucket is empty", s["returns"] == [], [x["bill"]["id"] for x in s["returns"]])
        check("C: (2) signed = the one bill carrying Marg's minus sign (9003)", (s.get("signed") or None) == [rid], (s.get("signed"), rid))
        _s, groups = PA._pay_rows(c, M)
        fl = {b["id"]: b["flag"] for g in groups for b in g["bills"] if b["id"] == rid}
        check("C: (2) the return reads 'a purchase return ... counted as a return' on the sheet, and no 'needs correcting'",
              len(fl) == 1 and "counted as a return" in fl[rid] and "needs correcting" not in fl[rid], fl)
        c.close()
        s_, h = X.GET("manoj", P + "/page/month/" + M)
        check("C: (2) the month page: the return reads 'agrees' with the return words (once)", s_ == 200 and h.count("counted as a return") == 1,
              (s_, h.count("counted as a return")))
        DUMP["s1"] = dict(itemwise=s["itemwise_p"], signed=s.get("signed"))
        # the money readers return on the walk's month and on every live month (no recursion); figures not asserted (live data)
        c = X.conn()
        bad = []
        for m in (M,) + LIVE_MONTHS:
            try:
                s2 = X.summary(c, m)
                PA._pay_rows(c, m)
                PA._advice_rows_s265(c, m)
                PA._verify_statement(c, m)
                X.gate(c, m)
            except Exception as e:                             # noqa: BLE001
                bad.append((m, "%s: %s" % (type(e).__name__, str(e)[:120])))
        c.close()
        check("(5) _month_summary, _pay_rows, _advice_rows_s265, _verify_statement and the gate return on January 2030 and April-October 2026", not bad, bad)
    section("1  returns counted as returns: the walk's own return bill, its positive lines, the sheet and the month page", s1)

    # ============================================================================================ 2: the clipped-name twin (3.3)
    def s2():
        ok, got = lay(itemwise=False)
        c = X.conn()
        rid = bill_id(c, K_TL, "9004", "2030-01-20")
        rows = bills_no(c, "9004", "2030-01-20")
        aud = [dict(r) for r in c.execute("SELECT ref, detail FROM purchase_audit WHERE action='twin_joined' AND ref=? AND detail LIKE ?",
                                          (str(rid), "%" + h2("sw1") + "%"))]
        say("   (a) bill-wise '%s' then supplier-wise '%s', 9004 20-Jan-2030: rows %s; twin_joined %d"
            % (N_TL, N_TC, [(r["id"], r["supplier_norm"], (r["bw_md5"] or "-")[:8], (r["sw_md5"] or "-")[:8]) for r in rows], len(aud)))
        check("the bill-wise and supplier-wise pushes are taken", ok, got)
        check("C: (3a) no new row: bill 9004 stays one row (the long name), it gains the supplier-wise md5, one twin_joined audit row naming both keys",
              rid is not None and len(rows) == 1 and rows[0]["id"] == rid and rows[0]["sw_md5"] == h2("sw1") and len(aud) == 1
              and N_TL in aud[0]["detail"] and N_TC in aud[0]["detail"], (rows, aud))
        # (b) a second supplier-wise push (new md5, later stamp, the whole month: it retires the first)
        st, j = X.push(body("SUPPLIERWISE", "sw2", "20300202-090000", [bill_row(b[1], b[2], b[3], b[4]) for b in BILLS]))
        r2 = bills_no(c, "9004", "2030-01-20")
        check("C: (3b) a second supplier-wise export of the clipped name after the join: still one row, the real bill takes the new md5",
              st == 200 and len(r2) == 1 and r2[0]["id"] == rid and r2[0]["sw_md5"] == h2("sw2"),
              (st, [(r["id"], r["supplier_norm"], (r["sw_md5"] or "-")[:8]) for r in r2]))
        # (e) a clipped name with a different amount stays two rows (both files)
        st, j = X.push(body("SUPPLIERWISE", "sw3", "20300202-100000", [bill_row(N_TC, "9004", "2030-01-20", 159800)], "2030-01-20", "2030-01-20"))
        r3 = bills_no(c, "9004", "2030-01-20")
        check("(3e) a clipped name with a different amount stays two rows (a new row, no join)", st == 200 and len(r3) == 2,
              (st, [(r["id"], r["supplier_norm"]) for r in r3]))
        c.close()
        # (c) a row retired as 'twin of bill N': a supplier-wise push of the clipped name lands on the real bill, the twin stays retired
        # (d) two true bills of the same number, date and amount, names not one inside the other: two rows, no join
        X.reset()
        st1, j1 = X.push(body("BILLWISE", "bw5", "20300203-090000", [bill_row(N_TL, "9005", "2030-01-22", 88800),
                                                                       bill_row(N_MN, "9006", "2030-01-18", 1064100),
                                                                       bill_row(N_DP, "9006", "2030-01-18", 1064100)]))
        c = X.conn()
        real = bill_id(c, K_TL, "9005", "2030-01-22")
        twin = ins(c, "purchase_bill", dict(supplier_norm=K_TC, supplier=N_TC, bill_no="9005", bill_date="2030-01-22", month=M, cash_p=0,
                                            credit_p=88800, amount_p=88800, source_md5=h2("twin5"), bw_md5=None, sw_md5=None,
                                            bw_amount_p=None, sw_amount_p=None, date_src="SUPPLIERWISE",
                                            reason="twin of bill %d (supplier-wise clipped the name; W604v2 walk)" % (real or 0)))
        c.commit()
        pair0 = sorted(r["id"] for r in bills_no(c, "9006", "2030-01-18"))
        st2, j2 = X.push(body("SUPPLIERWISE", "sw5", "20300203-090500", [bill_row(N_TC, "9005", "2030-01-22", 88800),
                                                                           bill_row(N_MN, "9006", "2030-01-18", 1064100),
                                                                           bill_row(N_DP, "9006", "2030-01-18", 1064100)]))
        r5 = {r["id"]: r for r in bills_no(c, "9005", "2030-01-22")}
        e5 = eff_ids(c, [i for i in (real, twin) if i])
        say("   (c) the retired twin %s of bill %s, then the clipped name pushed: %s -> real sw %s, twin sw %s; effective %s"
            % (twin, real, (st2, j2), (r5.get(real, {}).get("sw_md5") or "-")[:8], (r5.get(twin, {}).get("sw_md5") or "-")[:8], e5))
        check("C: (3c) a supplier-wise push of the clipped name onto a retired twin: the twin stays not effective, the real bill takes the md5",
              st1 == 200 and st2 == 200 and real is not None and twin in r5 and r5[twin]["sw_md5"] is None and r5[real]["sw_md5"] == h2("sw5")
              and e5 == [real], (st1, st2, e5, sorted(r5)))
        pair1 = sorted(r["id"] for r in bills_no(c, "9006", "2030-01-18"))
        tj = c.execute("SELECT COUNT(*) FROM purchase_audit WHERE action='twin_joined' AND detail LIKE ? AND detail LIKE ?",
                       ('%"9006"%', "%" + h2("sw5") + "%")).fetchone()[0]
        check("(3d) two true bills 9006 (same number, date and amount; neither name inside the other): a supplier-wise push of both stays two rows, no join",
              len(pair0) == 2 and pair1 == pair0 and tj == 0, (pair0, pair1, tj))
        c.close()
    section("2  the clipped-name twin: the join, the re-export, the retired twin, the true pair -- the walk's own bills", s2)

    # ============================================================================================ 3: the card and the lock (3.4 / 3.5)
    def card_lines(u="manoj"):
        s_, h = X.GET(u, P + "/page/pay/" + M)
        m = re.search(r"<!--s604card-->(.*?)<!--/s604card-->", h, flags=re.S)
        return s_, (text_lines(m.group(1)) if m else None)

    def line_of(lines, label):
        return next((l for l in (lines or []) if l.startswith(label)), "")

    def s3():
        span = "FROM 01-01-2030 TO 31-01-2030"
        ok, got = lay()
        check("the walk's own three exports are taken", ok, got)
        s_, L = card_lines()
        for l in L or ["(no card)"]:
            say("   [all three in] %s" % l)
        check("C: (4) the card is at the top of January 2030's payment page", s_ == 200 and L is not None and L[0] == "Month-end reports for January 2030",
              (s_, (L or [""])[0]))
        sw = line_of(L, "Supplier-wise statement")
        check("C: (4) supplier-wise: received, 01-31 Jan, 4 bills, its total Rs 2,797 agrees with the sheet",
              sw.startswith("Supplier-wise statement — Received ") and sw.endswith("01–31 Jan · 4 bills · its total ₹2,797 agrees with the sheet"), sw)
        bw = line_of(L, "Bill-wise statement")
        check("C: (4) bill-wise: received, 01-31 Jan, 4 bills", bw.startswith("Bill-wise statement — Received ") and bw.endswith("01–31 Jan · 4 bills"), bw)
        it = line_of(L, "Item lines")
        check("C: (4) item lines: received, 01-31 Jan, none missing", it.startswith("Item lines — Received ") and it.endswith("01–31 Jan"), it)
        c = X.conn()
        g = X.gate(c)
        c.close()
        check("C: (4)(5) all three in and agreeing: the green line, and the lock gate open",
              "All three reports are in and agree — the month can be locked." in (L or []) and g[0] is True, g)
        s_, h = X.GET("manoj", P + "/page/month/" + M)
        check("(5) the month page then shows the FINALISE button to the doctor", s_ == 200 and "FINALISE January 2030" in h, s_)
        # the supplier-wise statement removed (the walk's own export, by md5)
        c = X.conn()
        c.execute("DELETE FROM purchase_export WHERE md5=?", (h2("sw1"),))
        c.commit()
        c.close()
        s_, L = card_lines()
        check("C: (4) with the supplier-wise statement gone: 'Not yet -- export from Marg as a TEXT file: SUPPLIER WISE PURCHASE STATEMENT, %s'" % span,
              line_of(L, "Supplier-wise statement") == "Supplier-wise statement — Not yet — export from Marg as a TEXT file: SUPPLIER WISE PURCHASE STATEMENT, " + span,
              line_of(L, "Supplier-wise"))
        c = X.conn()
        g = X.gate(c)
        c.close()
        check("C: (5) ... the gate is closed with the supplier-wise reason",
              g[0] is False and any(r.startswith("the supplier-wise statement for 01–31 Jan has not reached the server") for r in g[1]), g)
        s_, h = X.GET("manoj", P + "/page/month/" + M)
        check("C: (5) ... and the month page shows no FINALISE button, the reason listed", s_ == 200 and "FINALISE January 2030" not in h
              and "has not reached the server" in h, s_)
        st, j = X.POST("manoj", P + "/api/finalise", {"month": M})
        say("   api/finalise as the doctor with the supplier-wise statement gone: %s %s" % (st, j))
        check("C: (5) api/finalise refuses January 2030 while the supplier-wise statement is missing (409, the reason named)",
              st == 409 and isinstance(j, dict) and any("supplier-wise" in r for r in j.get("reasons") or []), (st, j))
        c = X.conn()
        stt = c.execute("SELECT status FROM purchase_month WHERE month=?", (M,)).fetchone()
        c.close()
        check("(5) ... and January 2030 is not locked on the copy", st != 200 or stt is None or stt[0] != "final", stt and tuple(stt))
        # one bill's item lines missing
        ok, got = lay(skip_lines=("9004",))
        s_, L = card_lines()
        it = line_of(L, "Item lines")
        check("C: (4) one bill's item lines missing: 'but 1 bill still has no item lines (20 Jan)', and the export to make",
              ok and "but 1 bill still has no item lines (20 Jan)" in it
              and ("export SUPPLIER/ITEM WISE PURCHASE STATEMENT, %s, as a TEXT file" % span) in it, (ok, it))
        # a supplier-wise statement ending on the 28th
        ok, got = lay(sw_pt="2030-01-28", sw_tag="sw28")
        c = X.conn()
        v = PA._verify_statement(c, M)
        c.close()
        s_, L = card_lines()
        check("C: (4) a supplier-wise statement ending on the 28th: 'Not yet' on the card and the cross-check says 'No supplier-wise ...' (the old -28 rule took it)",
              ok and line_of(L, "Supplier-wise statement").startswith("Supplier-wise statement — Not yet") and v["problems"]
              and v["problems"][0].startswith("No supplier-wise") and v["export"] is None,
              (ok, line_of(L, "Supplier-wise"), v["problems"][:1], (v["export"] or {}).get("md5")))
        # the refusal line: after the month's end and after the covering exports; gone once a covering item report arrives after it
        ok, got = lay()
        c = X.conn()
        ins(c, "mi_file", dict(md5=h2("ref1"), drive_name="W604V2 refused 1", type="", verdict="REFUSED", pc_verdict="REFUSED",
                               reason=R_REFUSED_STOP, received_at="2030-02-02T09:00:00+05:30"))
        c.commit()
        c.close()
        s_, L = card_lines()
        want = "The medical PC refused a purchase report at 09:00 on 02-Feb — it could not read it (line 177). Nothing for you to redo."
        check("C: (4) a reader-stop refusal after 31-Jan and after the covering exports: one plain line under the card",
              ok and sum(1 for l in L or [] if l == want) == 1, [l for l in L or [] if "refused" in l])
        st, j = X.push(body("ITEMWISE", "iw2", "20300203-091000", line_rows()))
        c = X.conn()
        c.execute("UPDATE purchase_export SET received_at=? WHERE md5=?", ("2030-02-03T10:00:00", h2("iw2")))   # the walk's own row: it arrived after the refusal
        c.commit()
        c.close()
        s_, L = card_lines()
        check("C: (4) gone once a covering item report is received after it", st == 200 and L is not None and not any(l.startswith("The medical PC refused") for l in L),
              (st, [l for l in L or [] if "refused" in l]))
        c = X.conn()
        ins(c, "mi_file", dict(md5=h2("ref2"), drive_name="W604V2 refused 2", type="", verdict="REFUSED", pc_verdict="REFUSED",
                               reason=R_REFUSED_OTHER, received_at="2030-02-04T09:00:00+05:30"))
        c.commit()
        c.close()
        s_, L = card_lines()
        check("(4) another refusal reason: 'The medical PC refused a purchase report at hh:mm on dd-Mon: <its first clause>.'",
              any(l == "The medical PC refused a purchase report at 09:00 on 04-Feb: a purchase statement the reader cannot take." for l in L or []),
              [l for l in L or [] if "refused" in l])
        # the staff-eye: Shavez sees the same English card; the owner's and Shavez's portal homes render (the walk's own portal)
        s_, Ls = card_lines("shavez")
        say("   shavez on /page/pay/%s: %s; card %s" % (M, s_, "seen" if Ls else "not seen"))
        if s_ == 200:
            check("(4) staff-eye: Shavez, opening the payment page, sees the same English card", Ls is not None and Ls[0] == "Month-end reports for January 2030",
                  Ls and Ls[:1])
        homes = {}
        try:
            sys.path.insert(0, os.path.abspath(a.por))
            import portal as po                                # noqa: E402
            pc = po.app.test_client(use_cookies=False)
            for u in ("manoj", "shavez"):
                r = pc.post("/portal/login", base_url=BASE, data={"user": u, "password": pw[u]})
                m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
                r3 = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": "clinic_sso=" + (m.group(1) if m else "")})
                homes[u] = (r.status_code, r3.status_code)
        except Exception as e:                                 # noqa: BLE001
            homes["error"] = "%s: %s" % (type(e).__name__, str(e)[:200])
        finally:
            if os.path.abspath(a.por) in sys.path:
                sys.path.remove(os.path.abspath(a.por))
        say("   the portal (the walk's own secret and store): %s" % homes)
        check("(4) staff-eye: the owner's and Shavez's portal homes render (no duty is added, moved or removed)",
              homes.get("manoj", (0, 0))[1] == 200 and homes.get("shavez", (0, 0))[1] == 200, homes)
    section("3  the card on January 2030's page, the lock gate, api/finalise, the 28th, the refusal line -- the walk's own exports", s3)

    # ============================================================================================ 4: the two boxes (3.6)
    def s4():
        ok, got = lay()
        c = X.conn()
        _s, groups = PA._pay_rows(c, M)
        c.close()
        ga = next((g for g in groups if g["norm"] == K_A), None)
        gr = next((g for g in groups if g["norm"] == K_R), None)
        check("the copy carries the walk's two vendors on January 2030's sheet, nothing typed", ok and ga is not None and gr is not None
              and ga["carry_p"] is None and gr["carry_p"] is None, (ok, [g["norm"] for g in groups]))
        if ga is None or gr is None:
            return
        tot = ga["total_p"]
        typed = "−%d" % (tot // 100)
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_A, "carry_fwd": typed, "paid": ""})
        c = X.conn()
        row = c.execute("SELECT carry_fwd_p, paid_p, note FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (M, K_A)).fetchone()
        c.close()
        say("   post carry_fwd %r: %s %s; stored %s" % (typed, st, j if not isinstance(j, dict) else {k: j.get(k) for k in ("ok", "carry_fwd_p", "payable_p", "payable", "updated_by")},
                                                       tuple(row) if row else None))
        check("C: (6) carry_fwd '%s' (U+2212) is stored -%d and the reply says payable 0" % (typed, tot),
              st == 200 and row is not None and row[0] == -tot and isinstance(j, dict) and j.get("payable_p") == 0, (st, row and tuple(row), j))
        c = X.conn()
        before = c.execute("SELECT * FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (M, K_A)).fetchone()
        before = tuple(before) if before else None
        c.close()
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_A, "carry_fwd": "4OO", "paid": ""})
        c = X.conn()
        after = c.execute("SELECT * FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (M, K_A)).fetchone()
        after = tuple(after) if after else None
        c.close()
        check("C: (6) '4OO' answers 400 malformed with words, the row unchanged", st == 400 and isinstance(j, dict) and j.get("error") == "malformed"
              and "could not be read" in (j.get("message") or "") and after == before, (st, j, before == after))
        for typed2, want in (("–400", -40000), ("-400/-", -40000), ("400/-", 40000)):
            st, j = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_R, "carry_fwd": typed2, "paid": ""})
            c = X.conn()
            r_ = c.execute("SELECT carry_fwd_p FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (M, K_R)).fetchone()
            c.close()
            check("C: (6) carry_fwd %r is read as %d" % (typed2, want), st == 200 and r_ is not None and r_[0] == want, (st, r_ and r_[0]))
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_R, "carry_fwd": "", "paid": "", "note": "W604v2 walk note"})
        st2, j2 = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_R, "carry_fwd": "", "paid": ""})
        c = X.conn()
        n_ = c.execute("SELECT note FROM purchase_pay_line WHERE month=? AND vendor_norm=?", (M, K_R)).fetchone()
        c.close()
        check("C: (6) a stored note, then a post without the note key: the note is kept", st == 200 and st2 == 200 and n_ is not None
              and n_[0] == "W604v2 walk note", (st, st2, n_ and n_[0]))
        s_, h = X.GET("manoj", P + "/page/pay/" + M)
        saved = re.findall(r'<tr class="s604saved"><td[^>]*>(.*?)</td></tr>', h, flags=re.S)
        say("   the sheet: saved lines %s" % [_html.unescape(x)[:120] for x in saved][:4])
        check("C: (6) the sheet: no inputmode=\"numeric\" on any Carried-in box; Paid keeps its keypad",
              s_ == 200 and re.search(r'id="cf_[^"]*"', h) is not None and not re.search(r'id="cf_[^"]*" value="[^"]*" inputmode="numeric"', h)
              and re.search(r'id="pd_[^"]*" value="[^"]*" inputmode="numeric"', h) is not None, s_)
        check("C: (6) the sheet: 'Saved dd-Mon hh:mm by manoj -- payable now Rs 0' under the vendor carried to nothing, and the note under the vendor that has one",
              any(_html.unescape(x).startswith("Saved ") and " by manoj — payable now ₹0" in _html.unescape(x) for x in saved)
              and any("note: W604v2 walk note" in _html.unescape(x) for x in saved), [_html.unescape(x)[:100] for x in saved][:4])
        check("C: (6) the page's script shows 'Saved -- payable now' beside the box before the reload",
              "Saved \\u2014 payable now " in h and "setTimeout(function(){location.reload();},1200)" in h)
        # Paid moves no money figure
        c = X.conn()
        _s, g0 = PA._pay_rows(c, M)
        a0 = PA._advice_rows_s265(c, M)
        c.close()
        bs = load(os.path.join(fin, "bank_sms.py"), "bank_sms_w604v2")
        c = X.conn()
        n0 = bs.neft_portion_p(c, M)
        c.close()
        _, hc0 = X.GET("manoj", P + "/page/cheques/%s" % M)
        st, j = X.POST("manoj", P + "/api/pay-line", {"month": M, "vendor_norm": K_R, "carry_fwd": "", "paid": "12345"})
        c = X.conn()
        _s, g1 = PA._pay_rows(c, M)
        a1 = PA._advice_rows_s265(c, M)
        n1 = bs.neft_portion_p(c, M)
        c.close()
        _, hc1 = X.GET("manoj", P + "/page/cheques/%s" % M)
        check("(6) Paid typed moves no payable, advice line, NEFT portion or cheque register line",
              st == 200 and [(g["norm"], g["payable_p"]) for g in g0] == [(g["norm"], g["payable_p"]) for g in g1]
              and [(r["vendor"], r["rupees"]) for r in a0[0]] == [(r["vendor"], r["rupees"]) for r in a1[0]] and n0 == n1
              and text_lines(hc0) == text_lines(hc1), (st, n0, n1))
    section("4  the two boxes: a phone's minus, an unreadable figure refused, the note kept, the saved line, Paid moves nothing", s4)

    # ============================================================================================ 5: the greps
    def s5():
        src = open(os.path.join(fin, "purchase_app.py"), encoding="utf-8").read()

        def fbody(name):
            m = re.search(r"^def %s\(.*?(?=^(?:def |class |@|# =|[A-Z_]+ = )|\Z)" % re.escape(name), src, flags=re.S | re.M)
            return m.group(0) if m else ""
        ms = fbody("_month_summary")
        check("C: (7) one gate: _lock_gate defined once; read by api_finalise, page_hub, page_month and the card; _month_summary calls no gate, report or cross-check",
              src.count("def _lock_gate(") == 1 and "_lock_gate(" in fbody("api_finalise") and "_lock_gate(" in fbody("page_hub")
              and "_lock_gate(" in fbody("page_month") and "_lock_gate(" in fbody("_s604_reports_card") and bool(ms)
              and not any(x in ms for x in ("_lock_gate(", "_verify_statement(", "_month_reports(")))
        check("C: (7) one arrival reader: _month_reports defined once; the month's last day in _verify_statement, no '-28'",
              src.count("def _month_reports(") == 1 and '"-28"' not in fbody("_verify_statement") and "_s604_last_day(month)" in fbody("_verify_statement"))
        check("C: (7) the note=excluded.note of api_finalise untouched; api_pay_line writes the note only when the request carries it",
              src.count("note=excluded.note") == 3 and 'if "note" in b:' in fbody("api_pay_line"))
        check("no run of ten digits in the walk's own output", not re.search(r"\d{10}", "\n".join(OUT)))
        r = X.cl.get("/finance/healthz", base_url=BASE)
        check("/finance/healthz answers 200 (public)", r.status_code == 200, r.status_code)
    section("5  the greps (one fact, one place) and healthz", s5)

    json.dump(DUMP, open(os.path.join(a.dump, "walk_v2.json"), "w"), default=str)
    reds = [l for l, ok in CTRL if not ok]
    greens = [l for l, ok in CTRL if ok]
    if a.expect_red:
        say("  RED on the old files: %d of %d controls" % (len(reds), len(CTRL)))
        for l in greens:
            say("  NOT RED %s" % l)
        if greens or not CTRL:
            say("WALK RED negative control S604v2: %d control(s) did not go red on the old files" % len(greens))
            return 1
        say("WALK OK negative control S604v2: %d controls red on the old files" % len(reds))
        return 0
    if FAILS:
        say("WALK RED S604v2: %d failure(s): %s" % (len(FAILS), FAILS[:6]))
        return 1
    say("WALK OK S604v2: %d checks, %d controls green on the new files" % (RUN[0], len(CTRL)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
