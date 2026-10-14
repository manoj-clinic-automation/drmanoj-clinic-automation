#!/usr/bin/env python3
"""walk_s554.py -- kit S554_PHYSIO_BACKFILL (14-Oct-2026). Runs on a SCRATCH folder and a SCRATCH database only.
    python3 -B walk_s554.py --fin <scratch copy of /root/finance with the files under test> --db <a COPY of finance.db>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config> --kit <kit> [--expect-red]
Made-up rows only (patients 'W554 WALK ...', clinic ids W554-..., slip numbers from 95540001, no mobile at all); found by key,
never by counting. The REAL finance app is loaded from --fin with header sign-in for this process only (a walk-only session:
no live secret, no live user store). The register's clock is pinned (PHYSIO_BOOK_NOW); the duty's SQL has its 'now' replaced once.
  A  THE DEFAULT FLOOR (no setting physio_book.from), the clock at 14-Oct-2026 12:00 -- the owner's own case:
     the clinic tab offers 01-Oct and not 30-Sep; a slip dated 02-Oct is accepted, 30-Sep refused (the words name 01-Oct-2026),
     a future day refused; a home course started back on 01-Oct takes a visit and a payment dated 05-Oct, refuses 30-Sep for both;
     a course may not be started on 30-Sep; a course started today refuses a 05-Oct visit (not before its start);
     the report for October says 'Days are matched from 01-Oct-2026', 01-Oct is matched (a difference, then made to agree: a
     tick, then one slip more: the difference), and no October day reads 'before the register'; a September reception day does;
     the duty's SQL as shipped (now = 14-Oct) gives n = the days that disagree from 01-Oct and since = 01-Oct, computed here
     independently; when 01-Oct agrees, it moves on to the next day (01-Oct has cleared); the door ?day=2026-10-01 as bhati
     opens 01-Oct's match card with its 'Farq'.
  B  THE FLOOR READ FROM THE SETTING: physio_book.from moved to 2031-03-01, the clock 20-Mar-2031: a slip dated 02-Mar accepted,
     28-Feb refused, 02-Oct-2026 now refused too; the picker follows; the report for March 2031: 01-Mar a tick, 02-Mar the
     difference, February's 27th 'before the register'; the duty's SQL follows the setting (n = 2, since 02-Mar; the setting moved
     to 27-Feb -> n = 3, since 27-Feb); through the real app bhati's own list shows the line opening ?day=2031-03-02, the owner's
     view of bhati shows it; STAFF-EYE: bhati's portal home carries Physiotherapy -> /finance/physio, that page offers
     'Patient-wise register', the door page shows 02-Mar's 'Farq'; once his entries agree the SQL reads 0 and the line leaves.
  C  THE DATA STEP (seed_s554.py) on the copy: writes physio_book.from = 2026-10-01 once, a second run adds nothing, a value
     already there is kept. Static: no 10-digit number, Bhati's name never misspelt, the SQL writes nothing, physio_book.py writes
     only its own tables and the setting table, 2026-10-14 is nowhere in the two files, clinic_physio_day never written by the app.
--expect-red: the same walk on the OLD two files must fail, the 'BACKFILL:' checks among the failures (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import datetime as dt
import json
import os
import re
import sqlite3
import subprocess
import sys
import traceback

DID = "bhati.physio_register"
NOW_LIT = "'now','localtime'"
A_NOW, A_SQLNOW, A_TODAY = "2026-10-14T12:00:00", "2026-10-14 12:00:00", "2026-10-14"
B_NOW, B_SQLNOW = "2031-03-20T11:00:00", "2031-03-20 11:00:00"
B_FLOOR = "2031-03-01"
S0 = 95540001                                      # made-up slip numbers, far above any real book
WHO = "w554walk"
BASE = "https://followup.dr-manoj.in"
RUN, FAILS = [0], []


def check(label, cond, got=None):
    RUN[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))
    return cur.lastrowid


def text(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).strip()


def short(iso):
    return dt.date.fromisoformat(iso).strftime("%a %d-%b")


def report_row(h, day):
    """The day-wise row of the report for one day, as text (None when the day has no row)."""
    m = re.search(r"<tr><td class='d'>%s</td>(.*?)</tr>" % re.escape(short(day)), h or "")
    return text(m.group(1)) if m else None


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]      # never import from the kit folder
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    anywhere = os.environ.get("S554_WALK_ANYWHERE") == "1"
    assert dbp.startswith("/tmp/") or anywhere, "the walk runs on a scratch copy in /tmp only"
    assert fin.startswith("/tmp/") or anywhere, "the walk loads a scratch folder in /tmp only"
    print("-- S554 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))

    raw = sqlite3.connect(dbp, timeout=30)
    raw.row_factory = sqlite3.Row
    have = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"clinic_physio_day", "physio_session", "physio_course", "physio_patient", "physio_payment", "setting"} <= have, "the physio tables are not on this copy"
    assert raw.execute("SELECT COUNT(*) FROM clinic_physio_day WHERE business_date BETWEEN '2031-02-01' AND '2031-03-31'").fetchone()[0] == 0, \
        "the copy already holds Feb/Mar-2031 physio days -- the walk's days are not its own"
    assert raw.execute("SELECT COUNT(*) FROM physio_patient WHERE name LIKE 'W554 WALK%'").fetchone()[0] == 0, "the walk's patients are already on the copy"

    # ---- 0  made-up patients; the register open on the copy; the floor setting absent (the default is under test first)
    pid = {}
    for k, nm, cid in (("one", "W554 WALK ONE", "W554-0001"), ("two", "W554 WALK TWO", "W554-0002")):
        pid[k] = ins(raw, "physio_patient", dict(clinic_id=cid, name=nm, mobile="", created_by=WHO, created_at=A_SQLNOW))
    raw.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('physio_book.on', '1', 'S554 walk (copy)')")
    raw.execute("DELETE FROM setting WHERE key='physio_book.from'")
    on = raw.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    if not (on and "|" in str(on[0] or "")):
        raw.execute("DELETE FROM setting WHERE key='aaj.staff_on'")
        ins(raw, "setting", dict(key="aaj.staff_on", value="2031-03-01T00:00:00|%s" % WHO, note="S554 walk"))
    if raw.execute("SELECT 1 FROM sqlite_master WHERE name='aaj_cfg'").fetchone():
        raw.execute("DELETE FROM aaj_cfg WHERE person='bhati'")            # the seed's panel line (the copy only)
    # part B's reception days (made up): 27-Feb before the floor, 01-Mar agrees, 02-Mar UPI differs, 03-Mar nothing entered
    for d, cash, upi in (("2031-02-27", 25000, 0), ("2031-03-01", 25000, 0), ("2031-03-02", 25000, 25000), ("2031-03-03", 50000, 0)):
        ins(raw, "clinic_physio_day", dict(business_date=d, cash_p=cash, upi_p=upi, entered_by=WHO, entered_at=B_SQLNOW))
    raw.commit()
    cpd_before = [tuple(r) for r in raw.execute("SELECT * FROM clinic_physio_day ORDER BY business_date")]

    duties = json.load(open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8"))
    du = next((x for x in duties.get("extra") or [] if x.get("id") == DID), None)
    sql = (du or {}).get("sql") or ""
    check("the duties file holds %s, its SQL one read-only SELECT with its clock written once" % DID,
          du is not None and bool(re.match(r"(?is)^select\b", sql)) and ";" not in sql and sql.count(NOW_LIT) == 1, sql[:120])
    wdu = json.loads(json.dumps(duties))
    for x in wdu.get("extra") or []:
        if x.get("id") == DID and x.get("sql", "").count(NOW_LIT) == 1:
            x["sql"] = x["sql"].replace(NOW_LIT, "'%s'" % B_SQLNOW)
    wpath = os.path.join(os.path.dirname(dbp), "walk_s554_duties.json")
    with open(wpath, "w", encoding="utf-8") as fh:
        json.dump(wdu, fh, ensure_ascii=False)

    def duty(sqlnow):
        if not du or sql.count(NOW_LIT) != 1:
            return None, None
        r = raw.execute(sql.replace(NOW_LIT, "'%s'" % sqlnow)).fetchone()
        return r[0], r[1]

    def expect_due(floor, today):
        """The same rule, worked here in Python: reception days floor <= D < today with money, Bhati's live clinic slips unequal."""
        out = []
        for d, c_, u_ in raw.execute("SELECT business_date, COALESCE(cash_p,0), COALESCE(upi_p,0) FROM clinic_physio_day "
                                     "WHERE business_date >= ? AND business_date < ? ORDER BY business_date", (floor, today)).fetchall():
            if c_ + u_ <= 0:
                continue
            s = {m: raw.execute("SELECT COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                                "WHERE c.kind='clinic' AND s.day=? AND s.voided_at='' AND s.mode=?", (d, m)).fetchone()[0] for m in ("cash", "upi")}
            if s["cash"] != c_ or s["upi"] != u_:
                out.append(d)
        return out

    # ---- the real app on the copy
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", PHYSIO_BOOK_NOW=A_NOW, FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      AAJ_DUTIES_JSON=wpath)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                       # noqa: E402
    print("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    c = fa.app.test_client(use_cookies=False)

    def GET(u, path):
        r = c.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.get_data(as_text=True), r.headers.get("Location", "")

    def POST(u, path, data):
        r = c.post(path, base_url=BASE, data=data, headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.headers.get("Location", "")

    def live_slip(n):
        return raw.execute("SELECT * FROM physio_session WHERE slip_no=? AND voided_at=''", (n,)).fetchone()

    def slip(day, n, mode="cash", amount="250", who="bhati"):
        return POST(who, "/finance/physio/book/slip", dict(day=day, slip_no=str(n), amount=amount, mode=mode, pick="p%d" % pid["one"]))

    def rows_of(u, as_=None):
        s, h, _ = GET(u, "/finance/aaj/api/list" + ("?as=%s" % as_ if as_ else ""))
        try:
            j = json.loads(h)
        except ValueError:
            return s, None, []
        return s, j, [dict(r, section=sec["key"]) for sec in (j.get("sections") or []) for r in sec["rows"]]

    def part(name, fn):
        try:
            fn()
        except Exception:                          # noqa: BLE001 -- a part that breaks is a red check, the walk goes on
            check("%s ran to its end" % name, False, traceback.format_exc()[-400:])

    # ======================================================================== A
    def part_a():
        print("-- A  the default floor (no setting), the register's clock %s" % A_NOW)
        os.environ["PHYSIO_BOOK_NOW"] = A_NOW
        s, h, _ = GET("bhati", "/finance/physio/book")
        check("BACKFILL: the clinic tab as bhati (200) reaches back to 01-Oct (a choice for 2026-10-01) and not to 30-Sep; today is the default",
              s == 200 and "value='2026-10-01'" in h and "2026-09-30" not in h and "Slip likhiye — 14-Oct-2026" in text(h), (s, text(h)[:200]))
        s, h, _ = GET("bhati", "/finance/physio/book?day=2026-10-02")
        check("BACKFILL: ?day=2026-10-02 opens 02-Oct for slip entry", s == 200 and "Slip likhiye — 02-Oct-2026" in text(h), text(h)[:200])
        st, loc = slip("2026-10-02", S0)
        r = live_slip(S0)
        check("BACKFILL: a slip dated 02-Oct is accepted (saved, day 2026-10-02, Rs 250 cash)",
              st == 302 and "msg=saved" in loc and r is not None and r["day"] == "2026-10-02" and r["amount_p"] == 25000 and r["mode"] == "cash", (st, loc))
        st, loc = slip("2026-09-30", S0 + 1)
        s2, h2, _ = GET("bhati", loc.replace(BASE, "")) if loc else (0, "", "")
        check("a slip dated 30-Sep is refused, nothing written, and the words name the floor: 'Tareekh 01-Oct-2026 se aaj tak mein se ho.'",
              st == 302 and "err=day" in loc and live_slip(S0 + 1) is None and "Tareekh 01-Oct-2026 se aaj tak mein se ho." in text(h2), (loc, text(h2)[:200]))
        st, loc = slip("2026-10-15", S0 + 2)
        check("a slip dated tomorrow (15-Oct) is refused", "err=day" in loc and live_slip(S0 + 2) is None, loc)

        # home: a course started back on 01-Oct
        st, loc = POST("bhati", "/finance/physio/book/home/new", dict(pick="p%d" % pid["one"], rate="500", started="2026-10-01"))
        m = re.search(r"/finance/physio/book/home/(\d+)", loc or "")
        hc = int(m.group(1)) if m else None
        crow = raw.execute("SELECT * FROM physio_course WHERE id=?", (hc,)).fetchone() if hc else None
        check("BACKFILL: a home course can be started back on 01-Oct (its start reads 2026-10-01)",
              crow is not None and crow["kind"] == "home" and crow["started"] == "2026-10-01", (loc, dict(crow) if crow else None))
        hc = hc or 0
        st, loc = POST("bhati", "/finance/physio/book/home/visit", dict(course=str(hc), day="2026-10-05", amount="500"))
        v = raw.execute("SELECT * FROM physio_session WHERE course_id=? AND day='2026-10-05' AND voided_at=''", (hc,)).fetchone()
        check("BACKFILL: a home visit dated 05-Oct is accepted", "msg=visit" in loc and v is not None and v["amount_p"] == 50000 and v["slip_no"] is None, loc)
        st, loc = POST("bhati", "/finance/physio/book/home/pay", dict(course=str(hc), day="2026-10-05", amount="500", mode="cash"))
        p = raw.execute("SELECT * FROM physio_payment WHERE course_id=? AND day='2026-10-05' AND voided_at=''", (hc,)).fetchone()
        check("BACKFILL: a 'Payment received' dated 05-Oct is accepted", "msg=paid" in loc and p is not None and p["amount_p"] == 50000, loc)
        st, l1 = POST("bhati", "/finance/physio/book/home/visit", dict(course=str(hc), day="2026-09-30", amount="500"))
        st, l2 = POST("bhati", "/finance/physio/book/home/pay", dict(course=str(hc), day="2026-09-30", amount="500", mode="cash"))
        n930 = raw.execute("SELECT (SELECT COUNT(*) FROM physio_session WHERE course_id=? AND day='2026-09-30') + "
                           "(SELECT COUNT(*) FROM physio_payment WHERE course_id=? AND day='2026-09-30')", (hc, hc)).fetchone()[0]
        check("a visit and a payment dated 30-Sep are both refused (before the floor), nothing written", "err=day" in l1 and "err=day" in l2 and n930 == 0, (l1, l2, n930))
        s, h, _ = GET("bhati", "/finance/physio/book/home/%d" % hc)
        check("BACKFILL: that patient's page offers visit days back to 01-Oct, its payment date may go back to 01-Oct, and shows 'Shuru 01-Oct-2026'",
              s == 200 and "<option value='2026-10-01'>" in h and "<option value='2026-09-30'>" not in h and "min='2026-10-01'" in h
              and "Shuru 01-Oct-2026" in text(h), (s, text(h)[:200]))
        st, loc = POST("bhati", "/finance/physio/book/home/new", dict(pick="p%d" % pid["two"], rate="500", started="2026-09-30"))
        n2 = raw.execute("SELECT COUNT(*) FROM physio_course WHERE patient_id=? AND kind='home'", (pid["two"],)).fetchone()[0]
        check("a home course may not be started on 30-Sep (before the floor): refused, no course", "err=day" in loc and n2 == 0, (loc, n2))
        st, loc = POST("bhati", "/finance/physio/book/home/new", dict(pick="p%d" % pid["two"], rate="500"))
        m = re.search(r"/finance/physio/book/home/(\d+)", loc or "")
        hc2 = int(m.group(1)) if m else 0
        st, loc = POST("bhati", "/finance/physio/book/home/visit", dict(course=str(hc2), day="2026-10-05", amount="500"))
        nv = raw.execute("SELECT COUNT(*) FROM physio_session WHERE course_id=?", (hc2,)).fetchone()[0]
        s, h, _ = GET("bhati", "/finance/physio/book/home/%d" % hc2)
        check("a course started today (no start given) refuses a 05-Oct visit -- not before its start -- and does not offer that day",
              hc2 and "err=start" in loc and nv == 0 and "<option value='2026-10-05'>" not in h, (loc, nv))

        # the report and the duty on October's real reception days (read on the copy; nothing printed of them but dates and counts)
        first_oct = raw.execute("SELECT cash_p, upi_p FROM clinic_physio_day WHERE business_date='2026-10-01'").fetchone()
        if first_oct is None:
            ins(raw, "clinic_physio_day", dict(business_date="2026-10-01", cash_p=25000, upi_p=0, entered_by=WHO, entered_at=A_SQLNOW))
            raw.commit()
            cpd_before[:] = [tuple(r) for r in raw.execute("SELECT * FROM clinic_physio_day ORDER BY business_date")]
            print("   (this copy had no reception row for 01-Oct: the walk wrote its own)")
            first_oct = raw.execute("SELECT cash_p, upi_p FROM clinic_physio_day WHERE business_date='2026-10-01'").fetchone()
        exp = expect_due("2026-10-01", A_TODAY)
        n, since = duty(A_SQLNOW)
        print("   reception days from 01-Oct before 14-Oct that disagree with the register on this copy: %d (%s)" % (len(exp), ", ".join(exp) or "-"))
        check("BACKFILL: the duty's SQL as shipped, now = 14-Oct, the setting absent: n = %d, since = 01-Oct -- the oldest unmatched October day" % len(exp),
              exp[:1] == ["2026-10-01"] and (n, since) == (len(exp), exp[0] if exp else None), (n, since, exp[:3]))
        s, h, _ = GET("bhati", "/finance/physio/book?day=2026-10-01")
        t = text(h)
        check("BACKFILL: the door as bhati, ?day=2026-10-01 (200): 01-Oct's match card with its marker 'Farq', 01-Oct chosen in the day list",
              s == 200 and "Milaan — 01-Oct-2026" in t and "Farq:" in t and "<option value='2026-10-01' selected>" in h, (s, t[-300:]))
        s, h, _ = GET("manoj", "/finance/physio/book/report?m=2026-10")
        r1 = report_row(h, "2026-10-01")
        oct_before = [d for d in (r[0] for r in raw.execute("SELECT business_date FROM clinic_physio_day WHERE business_date BETWEEN '2026-10-01' AND '2026-10-31'"))
                      if "before the register" in (report_row(h, d) or "")]
        check("BACKFILL: the report for October (as manoj, 200) says 'Days are matched from 01-Oct-2026'; 01-Oct is matched (here: the difference); "
              "no October day reads 'before the register'",
              s == 200 and "Days are matched from 01-Oct-2026" in text(h) and r1 is not None and "before the register" not in r1 and "cash ₹" in r1
              and not oct_before, (s, r1, oct_before))
        s, h, _ = GET("bhawna", "/finance/physio/book/report?m=2026-10")
        check("Dr Bhawna's report for October answers 200 too", s == 200 and "Day-wise" in text(h), s)
        sep = raw.execute("SELECT MAX(business_date) FROM clinic_physio_day WHERE business_date < '2026-10-01' AND business_date >= '2026-09-01'").fetchone()[0]
        if sep:
            s, h, _ = GET("manoj", "/finance/physio/book/report?m=2026-09")
            rs = report_row(h, sep)
            check("a September reception day (%s) reads 'before the register'" % sep, s == 200 and rs is not None and "before the register" in rs, (s, rs))
        else:
            print("   (no September reception day on this copy: 'before the register' is shown in part B)")
        # 01-Oct made to agree (made-up slips on the copy, equal to what reception wrote)
        need = {}
        for mode, col in (("cash", "cash_p"), ("upi", "upi_p")):
            got = raw.execute("SELECT COALESCE(SUM(s.amount_p),0) FROM physio_session s JOIN physio_course c ON c.id=s.course_id "
                              "WHERE c.kind='clinic' AND s.day='2026-10-01' AND s.voided_at='' AND s.mode=?", (mode,)).fetchone()[0]
            need[mode] = (first_oct[col] or 0) - got
        ccr = raw.execute("SELECT id FROM physio_course WHERE patient_id=? AND kind='clinic'", (pid["one"],)).fetchone()
        cc = ccr[0] if ccr else ins(raw, "physio_course", dict(patient_id=pid["one"], kind="clinic", rate_p=25000, status="active",
                                                                  started="2026-10-01", changed_at=A_SQLNOW, changed_by=WHO))
        k = 10
        for mode in ("cash", "upi"):
            if need[mode] > 0:
                ins(raw, "physio_session", dict(course_id=cc, day="2026-10-01", slip_no=S0 + k, amount_p=need[mode], mode=mode, by_whom="bhati", at=A_SQLNOW))
                k += 1
        raw.commit()
        s, h, _ = GET("manoj", "/finance/physio/book/report?m=2026-10")
        r1 = report_row(h, "2026-10-01")
        check("BACKFILL: with 01-Oct entered to agree, the report's 01-Oct reads ✓", r1 is not None and "✓" in r1, r1)
        n2_, since2 = duty(A_SQLNOW)
        exp2 = expect_due("2026-10-01", A_TODAY)
        check("BACKFILL: and 01-Oct has cleared from the duty: n = %d, since = %s (the next unmatched day)" % (len(exp2), exp2[0] if exp2 else "-"),
              "2026-10-01" not in exp2 and (n2_, since2) == (len(exp2), exp2[0] if exp2 else None) and n2_ == n - 1, (n2_, since2))
        ins(raw, "physio_session", dict(course_id=cc, day="2026-10-01", slip_no=S0 + 19, amount_p=25000, mode="cash", by_whom="bhati", at=A_SQLNOW))
        raw.commit()
        s, h, _ = GET("manoj", "/finance/physio/book/report?m=2026-10")
        r1 = report_row(h, "2026-10-01")
        check("one slip more on 01-Oct: the report's 01-Oct shows the difference 'cash ₹ 250 · UPI ₹ 0'", r1 is not None and "cash ₹ 250 · UPI ₹ 0" in r1, r1)
        raw.execute("UPDATE physio_session SET voided_at=?, voided_by=?, void_why='twice' WHERE slip_no=?", (A_SQLNOW, WHO, S0 + 19))
        raw.commit()

    # ======================================================================== B
    def part_b():
        print("-- B  the floor read from the setting: physio_book.from = %s, the register's clock %s" % (B_FLOOR, B_NOW))
        os.environ["PHYSIO_BOOK_NOW"] = B_NOW
        raw.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('physio_book.from', ?, 'S554 walk (copy)')", (B_FLOOR,))
        raw.commit()
        s, h, _ = GET("bhati", "/finance/physio/book")
        check("BACKFILL: the picker follows the setting: 01-Mar-2031 offered, 28-Feb not, 02-Oct-2026 not",
              s == 200 and "value='2031-03-01'" in h and "2031-02-28" not in h and "2026-10-02" not in h, (s, text(h)[:160]))
        st, l1 = slip("2031-03-01", S0 + 20)
        st, l2 = slip("2031-03-02", S0 + 21)
        st, l3 = slip("2031-02-28", S0 + 22)
        st, l4 = slip("2026-10-02", S0 + 23)
        s5, h5, _ = GET("bhati", l3.replace(BASE, "")) if l3 else (0, "", "")
        check("BACKFILL: the rules follow the setting: slips dated 01-Mar and 02-Mar accepted; 28-Feb refused ('Tareekh 01-Mar-2031 se ...'); 02-Oct-2026 refused",
              live_slip(S0 + 20) is not None and live_slip(S0 + 21) is not None and "err=day" in l3 and live_slip(S0 + 22) is None
              and "err=day" in l4 and live_slip(S0 + 23) is None and "Tareekh 01-Mar-2031 se aaj tak mein se ho." in text(h5), (l1, l2, l3, l4))
        s, h, _ = GET("manoj", "/finance/physio/book/report?m=2031-03")
        r1, r2 = report_row(h, "2031-03-01"), report_row(h, "2031-03-02")
        check("BACKFILL: the report for March 2031: 'Days are matched from 01-Mar-2031'; 01-Mar ✓; 02-Mar the difference 'cash ₹ 0 · UPI ₹ -250'",
              s == 200 and "Days are matched from 01-Mar-2031" in text(h) and r1 is not None and "✓" in r1 and r2 is not None
              and "cash ₹ 0 · UPI ₹ -250" in r2, (r1, r2))
        s, h, _ = GET("manoj", "/finance/physio/book/report?m=2031-02")
        r0 = report_row(h, "2031-02-27")
        check("a day before the floor (27-Feb-2031) reads 'before the register'", s == 200 and r0 is not None and "before the register" in r0, r0)
        n, since = duty(B_SQLNOW)
        check("BACKFILL: the duty's SQL reads the setting: n = 2 (02-Mar UPI differs, 03-Mar not entered), since = 2031-03-02",
              (n, since) == (2, "2031-03-02"), (n, since))
        raw.execute("UPDATE setting SET value='2031-02-27' WHERE key='physio_book.from'")
        raw.commit()
        n3, since3 = duty(B_SQLNOW)
        raw.execute("UPDATE setting SET value=? WHERE key='physio_book.from'", (B_FLOOR,))
        raw.commit()
        check("the setting moved back to 27-Feb -> the SQL follows: n = 3, since = 2031-02-27", (n3, since3) == (3, "2031-02-27"), (n3, since3))

        s, j, rows = rows_of("bhati")
        mine = [r for r in rows if r.get("id") == DID]
        want = "/finance/physio/book?day=2031-03-02"
        check("BACKFILL: bhati's own list (signed in as bhati) shows the line under 'Aaj', opening %s, tile Physiotherapy" % want,
              s == 200 and len(mine) == 1 and mine[0]["door"] == want and mine[0]["section"] == "day" and mine[0]["tile"] == "Physiotherapy",
              (s, mine, (j or {}).get("error")))
        s, j, rows = rows_of("manoj", "bhati")
        check("the owner's view (/finance/aaj/api/list?as=bhati, signed in as manoj) shows it", s == 200 and len([r for r in rows if r.get("id") == DID]) == 1, s)
        s, h, _ = GET("manoj", "/finance/aaj?as=bhati")
        check("/finance/aaj?as=bhati as manoj answers 200", s == 200, s)

        # the staff-eye walk (CLAUDE.md, S444): his home's tile, the tile's page, the door page
        code = ("import json,sys; sys.path.insert(0, %r); import portal as po; "
                "print('TILES ' + json.dumps([[t['name'], t.get('url', '')] for g, ts in po._visible_sections('staff', False, 'bhati') for t in ts]))" % a.portal)
        pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                            env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w554-walk-only",
                                     PYTHONDONTWRITEBYTECODE="1"))
        tl = [ln for ln in pp.stdout.splitlines() if ln.startswith("TILES ")]
        tiles = json.loads(tl[-1][6:]) if tl else []
        check("staff-eye: bhati's portal home (the real portal.py + the grants file) carries the Physiotherapy tile -> /finance/physio",
              ["Physiotherapy", "/finance/physio"] in tiles, (tiles, pp.stdout[-300:]))
        s, h, _ = GET("bhati", "/finance/physio")
        check("staff-eye: /finance/physio as bhati (200) offers 'Patient-wise register ›'", s == 200 and "Patient-wise register ›" in h, s)
        s, h, _ = GET("bhati", want)
        t = text(h)
        check("BACKFILL: staff-eye: the door as bhati, %s (200): 02-Mar's match card with its marker 'Farq: Cash ₹ 0 · UPI ₹ 250'" % want,
              s == 200 and "Milaan — 02-Mar-2031" in t and "Farq: Cash ₹ 0 · UPI ₹ 250" in t, (s, t[-300:]))
        slip("2031-03-02", S0 + 24, mode="upi")
        slip("2031-03-03", S0 + 25)
        slip("2031-03-03", S0 + 26)
        n4, _s4 = duty(B_SQLNOW)
        s, j, rows = rows_of("bhati")
        check("BACKFILL: with 02-Mar and 03-Mar entered to agree, the SQL reads 0 and the line has left bhati's list by itself",
              n4 == 0 and s == 200 and not [r for r in rows if r.get("id") == DID], (n4, len(rows)))

    # ======================================================================== C
    def part_c():
        print("-- C  the data step, and the static checks")
        cpd_after = [tuple(r) for r in raw.execute("SELECT * FROM clinic_physio_day ORDER BY business_date")]
        check("clinic_physio_day was never written by the app (every row as it was before the first request)", cpd_after == cpd_before)

        def step():
            p = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "seed_s554.py"), dbp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               universal_newlines=True)
            return p.returncode, p.stdout.strip()
        raw.execute("DELETE FROM setting WHERE key='physio_book.from'")
        raw.commit()
        r1, o1 = step()
        r2, o2 = step()
        v = (raw.execute("SELECT value FROM setting WHERE key='physio_book.from'").fetchone() or [None])[0]
        raw.execute("UPDATE setting SET value='2026-09-15' WHERE key='physio_book.from'")
        raw.commit()
        r3, o3 = step()
        v3 = (raw.execute("SELECT value FROM setting WHERE key='physio_book.from'").fetchone() or [None])[0]
        print("   " + o1)
        check("data step: physio_book.from = 2026-10-01 written once ('1 added'); a second run adds nothing; a value already there is kept",
              r1 == 0 and "(1 added)" in o1 and v == "2026-10-01" and r2 == 0 and "(0 added)" in o2 and r3 == 0 and v3 == "2026-09-15", (o1, o2, o3, v, v3))
        pb = open(os.path.join(fin, "physio_book.py"), encoding="utf-8").read()
        written = set(re.findall(r"\bINSERT(?: OR \w+)? INTO (\w+) \(", pb)) | set(re.findall(r"\bUPDATE (\w+) SET\b", pb))
        # ('UPDATE %s SET' -- the void -- names physio_session / physio_payment through its own map, read below)
        written |= set(re.findall(r'"(?:session|payment)": "(\w+)"', pb))
        check("physio_book.py writes only its own tables and the setting table (%s)" % ", ".join(sorted(written)),
              written <= {"physio_patient", "physio_course", "physio_session", "physio_payment", "setting"} and "clinic_physio_day" not in written, written)
        dj = open(os.path.join(fin, "aaj_duties.json"), encoding="utf-8").read()
        check("BACKFILL: 2026-10-14 is nowhere in physio_book.py or aaj_duties.json; the floor is the setting physio_book.from in both",
              "2026-10-14" not in pb and "2026-10-14" not in dj and "physio_book.from" in pb and "physio_book.from" in sql)
        kit_text = "".join(open(os.path.join(a.kit, f), encoding="utf-8").read() for f in sorted(os.listdir(a.kit))
                           if f.endswith((".py", ".sh", ".md", ".kit", ".txt")))
        check("static: the kit holds no 10-digit number and never misspells Bhati's name; the duty's SQL writes nothing",
              not re.search(r"(?<![0-9A-Za-z])\d{10}(?![0-9A-Za-z])", kit_text) and "Bh" + "arti" not in kit_text
              and not re.search(r"(?i)\b(insert|update|delete|replace|drop|alter|create)\b", sql))

    part("part A", part_a)
    part("part B", part_b)
    part("part C", part_c)
    raw.close()
    red = len(FAILS)
    if a.expect_red:
        br = [f for f in FAILS if f.startswith("BACKFILL:")]
        if red and len(br) >= 8 and any(f.startswith("BACKFILL: a slip dated 02-Oct is accepted") for f in FAILS):
            print("WALK OK negative control: %d of %d checks red on the old files, %d of them 'BACKFILL:' -- the old files refuse 02-Oct" % (red, RUN[0], len(br)))
            return 0
        print("NEGATIVE CONTROL FAILED: only %d of %d red on the old files ('BACKFILL:' red: %d)" % (red, RUN[0], len(br)))
        return 1
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    print("WALK OK S554: %d checks green (02-Oct in, 30-Sep out, home 05-Oct in, the report from the floor, the duty from 01-Oct, "
          "the floor read from the setting, staff-eye, the data step)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
