#!/usr/bin/env python3
"""walk_s552.py -- kit S552_PHYSIO_REGISTER (session 313, 14-Oct-2026, D646). Runs on a SCRATCH folder and a SCRATCH database only.
    python3 -B walk_s552.py --fin <scratch copy of /root/finance with the files under test> --db <a COPY of finance.db>
                            --portal <scratch copy of /root/portal *.py, no portal_config, no user store> --kit <kit folder> [--expect-red]
THE REAL finance app (finance_app.py with every module it mounts) is loaded from --fin on the copy, with header sign-in switched on
for this process only (a walk-only session: no live secret, no live user store). Made-up rows only, dated March 2031, no person,
no number: the made-up mobiles are built at run time. Rows are found by key, never by counting.
Signs in as bhati (maker), manoj and bhawna (checkers), a made-up outsider with a 'physio' row but none in 'physiobook', and
nobody. The staff-eye part renders bhati's portal tiles from the real portal.py and the grants file, his door (/finance/physio)
and the register itself. --expect-red: the same walk on the OLD files must fail -- and the link on the Physiotherapy page must be
among the failures (the negative control). Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import datetime
import io
import json
import os
import re
import sqlite3
import subprocess
import sys
import zipfile

NOW = "2031-03-12T11:00:00"
A, B, C, H1, H2 = "2031-03-10", "2031-03-11", "2031-03-12", "2031-03-08", "2031-03-09"
OLD_DAY = "2031-03-01"
MONTH = "2031-03"
S1 = 95520001                                    # made-up slip numbers, far above any real book
CID1, CID9, CID10 = "W552-0001", "W552-0009", "W552-0010"
N1, N2, N3 = "W552 WALK ONE", "W552 WALK TWO", "W552 WALK THREE"
OFF_LINE = "Yeh page abhi band hai — Dr Manoj ke kehne par khulega."
BASE = "https://followup.dr-manoj.in"

RUN, FAILS = [0], []


def P(*parts):
    return "".join(parts)


MOB2 = P("98765", "43210")                       # made up, built at run time (F-185)
MOB3 = P("91234", "50678")


def check(label, cond, got=None):
    RUN[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + str(got)[:300] + "]") if (got is not None and not cond) else ""))
    if not cond:
        FAILS.append(label)


def text(h):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h or "")).replace("&#39;", "'").replace("&amp;", "&").strip()


def ins(con, table, row):
    cols = {r[1]: r for r in con.execute("PRAGMA table_info(%s)" % table)}
    full = dict((k, v) for k, v in row.items() if k in cols)
    for name, r in cols.items():                 # a NOT NULL column with no default gets a neutral value
        if name not in full and r[3] and r[4] is None and not r[5]:
            full[name] = 0 if "INT" in (r[2] or "").upper() else ""
    con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(full), ", ".join("?" * len(full))), list(full.values()))


def xlsx_parts(b):
    if not b:
        return None
    z = zipfile.ZipFile(io.BytesIO(b))
    return dict((n, z.read(n)) for n in sorted(z.namelist()) if not n.startswith("docProps/"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--kit", required=True)
    ap.add_argument("--expect-red", action="store_true")
    a = ap.parse_args()
    fin, dbp = os.path.abspath(a.fin), os.path.abspath(a.db)
    assert dbp.startswith("/tmp/") or os.environ.get("S552_WALK_ANYWHERE") == "1", "the walk runs on a scratch copy in /tmp only"
    assert fin.startswith("/tmp/") or os.environ.get("S552_WALK_ANYWHERE") == "1", "the walk loads a scratch folder in /tmp only"
    side = "OLD files (negative control)" if a.expect_red else "new files"
    print("-- S552 walk on the %s: %s · db %s" % (side, fin, os.path.basename(dbp)))

    # ---- 0  the data step on the copy (the same script the installer runs) + the made-up rows
    s = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "seed_s552.py"), dbp, os.path.join(a.kit, "physio_book.py")],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    print("   " + s.stdout.strip().replace("\n", "\n   "))
    s2 = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "seed_s552.py"), dbp, os.path.join(a.kit, "physio_book.py")],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    raw = sqlite3.connect(dbp, timeout=30)
    raw.row_factory = sqlite3.Row
    q1 = lambda sql, *p: raw.execute(sql, p).fetchone()          # noqa: E731

    def v(sql, *p):
        r = raw.execute(sql, p).fetchone()
        return r[0] if r is not None else None
    roles = sorted((r[0], r[1]) for r in raw.execute("SELECT username, role FROM unit_role WHERE unit='physiobook' AND active=1"))
    check("data step: physiobook = bhati maker, bhawna checker, manoj checker (nobody else); the switch reads 0; second run adds nothing",
          s.returncode == 0 and roles == [("bhati", "maker"), ("bhawna", "checker"), ("manoj", "checker")]
          and (q1("SELECT value FROM setting WHERE key='physio_book.on'") or [None])[0] == "0" and s2.returncode == 0 and "(0 added)" in s2.stdout,
          (s.stdout[-200:], roles, s2.stdout[-120:]))
    ins(raw, "clinic_day_line", dict(business_date=A, section="consult", sn=S1, patient=N1, clinic_id=CID1, amount_p=60000, mode="Cash"))
    ins(raw, "clinic_physio_day", dict(business_date=A, cash_p=50000, upi_p=25000, entered_by="w552walk", entered_at=NOW))
    ins(raw, "clinic_physio_day", dict(business_date=B, cash_p=50000, upi_p=25000, entered_by="w552walk", entered_at=NOW))
    has_rev = q1("SELECT 1 FROM sqlite_master WHERE name='clinic_day_revenue'") is not None
    if has_rev:
        ins(raw, "clinic_day_revenue", dict(business_date=A, cons_count=1, cons_amount_p=60000, total_count=1, total_amount_p=60000,
                                            cash_amount_p=60000, cash_p=60000))
    if not q1("SELECT 1 FROM unit_role WHERE unit='physio' AND username='w552outsider'"):
        ins(raw, "unit_role", dict(unit="physio", username="w552outsider", role="maker", active=1, note="W552 walk"))
    raw.commit()
    cpd_before = [tuple(r) for r in raw.execute("SELECT * FROM clinic_physio_day ORDER BY business_date")]

    # ---- the real app on the copy
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", PHYSIO_BOOK_NOW=NOW, FINANCE_DEV_USER="", FINANCE_DEV_ROLE="")
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                     # noqa: E402
    import packs                                 # noqa: E402
    import clinic_money                          # noqa: E402
    print("-- the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    check("physio_book mounted inside the real app (not in its failed-mount list)", "physio_book" in sys.modules and
          not any(n == "physio_book" for n, _w in fa._MOUNT_FAILED), [n for n, _w in fa._MOUNT_FAILED])
    c = fa.app.test_client(use_cookies=False)

    def GET(u, path):
        r = c.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.get_data(as_text=True), r.headers.get("Location", "")

    def POST(u, path, data):
        r = c.post(path, base_url=BASE, data=data, headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.headers.get("Location", "")

    def follow(u, loc):
        loc = loc.replace(BASE, "")
        return GET(u, loc) if loc else (0, "", "")

    def income():
        out = {}
        for m in (MONTH, datetime.date.today().strftime("%Y-%m")):
            try:
                b, why = packs.build_income(raw, m)
                out[m] = (xlsx_parts(b), why)
            except Exception as ex:              # noqa: BLE001
                out[m] = ("raised", repr(ex)[:200])
        return out

    def match():
        try:
            return json.dumps(clinic_money.match_day(raw, A, now=datetime.datetime(2031, 3, 12, 11, 0, 0)), default=lambda o: dict(o) if isinstance(o, sqlite3.Row) else str(o), sort_keys=True)
        except Exception as ex:                  # noqa: BLE001
            return "raised " + repr(ex)[:200]

    inc0, mt0 = income(), match()

    def live(n):
        return raw.execute("SELECT * FROM physio_session WHERE slip_no=? AND voided_at=''", (n,)).fetchall()

    def pid_of(name):
        r = q1("SELECT id FROM physio_patient WHERE name=? ORDER BY id DESC LIMIT 1", name)
        return r[0] if r else None

    # ---- 1  the gate and the switch (off)
    print("-- 1  gates and the switch while it is off")
    st = [GET("", p)[0] for p in ("/finance/physio/book", "/finance/physio/book/report", "/finance/physio/book/home/1")]
    check("no login: the three new pages answer 302 (the login gate)", st == [302, 302, 302], st)
    s_, h, _ = GET("w552nobody", "/finance/physio/book")
    check("a login with no 'physio' row is sent away by the front gate (302)", s_ == 302, s_)
    s_, h, _ = GET("w552outsider", "/finance/physio/book")
    s2_, h2, _ = GET("w552outsider", "/finance/physio/book/report")
    check("a login with a 'physio' row but none in 'physiobook' is refused: the register 403 and the report 403",
          s_ == 403 and s2_ == 403 and "Not permitted" in h, (s_, s2_))
    s_, h, _ = GET("bhati", "/finance/physio/book")
    check("switch off: bhati sees one line, '%s', and no slip form" % OFF_LINE, s_ == 200 and OFF_LINE in h and "Slip likhiye" not in h, (s_, text(h)[:160]))
    s_, h, _ = GET("bhati", "/finance/physio/book/report")
    check("bhati (maker) cannot open the owner's report (403)", s_ == 403, s_)
    sm, hm, _ = GET("manoj", "/finance/physio/book?day=%s" % A)
    sb, hb, _ = GET("bhawna", "/finance/physio/book?tab=home")
    check("switch off: manoj and bhawna (checkers) see everything -- the preview", sm == 200 and "Slip likhiye" in hm and "Preview" in hm
          and sb == 200 and "Ghar ke patient" in hb, (sm, sb))
    POST("bhati", "/finance/physio/book/slip", dict(day=C, pick="c" + CID1, slip_no=str(S1), amount="250", mode="cash"))
    check("switch off: bhati's tap writes nothing", not live(S1), len(live(S1)))
    s_, loc = POST("manoj", "/finance/physio/book/switch", {"on": "1"})
    au = q1("SELECT by_whom, after_json FROM audit_log WHERE table_name='setting' AND action='physio_book.on' ORDER BY id DESC LIMIT 1")
    check("manoj opens the register: physio_book.on = 1, audited as manoj", (q1("SELECT value FROM setting WHERE key='physio_book.on'") or [None])[0] == "1"
          and au is not None and au[0] == "manoj" and '"1"' in (au[1] or ""), (s_, loc, tuple(au) if au else None))

    # ---- 2  the clinic slips
    print("-- 2  clinic slips, the duplicate, the void, the match, the missing numbers")
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s" % A)
    nxt = (v("SELECT MAX(slip_no) FROM physio_session WHERE slip_no IS NOT NULL AND voided_at=''") or 0) + 1
    check("switch on: bhati's Clinic tab -- slip number filled in with the highest live slip + 1 (%d), Rs 250 filled in, Cash and UPI buttons" % nxt,
          s_ == 200 and "Slip likhiye" in h and ("name='slip_no' class='amt' inputmode='numeric' value='%d'" % nxt) in h
          and "name='amount' class='amt' inputmode='decimal' value='250'" in h and "value='cash'" in h and "value='upi'" in h, (s_, text(h)[:200]))
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s&q=%s" % (A, CID1))
    check("search by Clinic ID finds the Docterz patient (a tap: pick=c%s)" % CID1, N1 in h and ("pick=c" + CID1) in h, text(h)[:200])
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s&q=WALK ON" % A)
    check("search by name finds the same patient", N1 in h, text(h)[:200])
    s_, loc = POST("bhati", "/finance/physio/book/slip", dict(day=A, pick="c" + CID1, slip_no=str(S1), amount="250", mode="cash"))
    r1 = live(S1)
    p1 = q1("SELECT * FROM physio_patient WHERE clinic_id=?", CID1)
    check("slip %d of a Docterz patient saved: Rs 250 cash on %s; the patient carries Clinic ID %s" % (S1, A, CID1),
          len(r1) == 1 and r1[0]["amount_p"] == 25000 and r1[0]["mode"] == "cash" and r1[0]["day"] == A and p1 is not None and p1["name"] == N1
          and "msg=saved" in loc, (loc, [dict(x) for x in r1]))
    s_, loc = POST("bhati", "/finance/physio/book/slip", dict(day=A, name=N2, mobile=MOB2, slip_no=str(S1 + 1), amount="250", mode="upi"))
    p2 = q1("SELECT * FROM physio_patient WHERE name=?", N2)
    check("a new patient with a mobile: saved with the mobile, slip %d UPI" % (S1 + 1), p2 is not None and p2["mobile"] == MOB2 and p2["clinic_id"] == ""
          and len(live(S1 + 1)) == 1 and live(S1 + 1)[0]["mode"] == "upi", loc)
    s_, loc = POST("bhati", "/finance/physio/book/slip", dict(day=A, name=N2, mobile="12345", slip_no=str(S1 + 40), amount="250", mode="upi"))
    check("a mobile that is not 10 digits is refused", "err=mobile" in loc and not live(S1 + 40), loc)
    pid2 = p2["id"] if p2 is not None else 0
    s_, loc = POST("bhati", "/finance/physio/book/slip", dict(day=A, pick="p%d" % pid2, slip_no=str(S1), amount="250", mode="cash"))
    sd, hd, _ = follow("bhati", loc)
    check("a slip number already entered is refused, naming its day and patient ('Slip %d pehle hi likhi hai — 10-Mar-2031, %s')" % (S1, N1),
          "err=dup" in loc and len(live(S1)) == 1 and ("Slip %d pehle hi likhi hai — 10-Mar-2031, %s" % (S1, N1)) in hd, (loc, text(hd)[:240]))
    POST("bhati", "/finance/physio/book/slip", dict(day=A, pick="c" + CID1, slip_no=str(S1 + 2), amount="250", mode="cash"))
    vid = live(S1 + 2)[0]["id"] if live(S1 + 2) else 0
    s_, loc = POST("bhati", "/finance/physio/book/void", dict(kind="session", id=str(vid), why="", back="/finance/physio/book?day=%s" % A))
    check("a void with no reason is refused", "err=why" in loc and len(live(S1 + 2)) == 1, loc)
    s_, loc = POST("bhati", "/finance/physio/book/void", dict(kind="session", id=str(vid), why="twice", back="/finance/physio/book?day=%s" % A))
    vr = q1("SELECT * FROM physio_session WHERE id=?", vid)
    check("'Galat entry hatao' (do baar entry): the row stays, its amount unchanged, marked voided by bhati",
          vr is not None and vr["voided_at"] != "" and vr["voided_by"] == "bhati" and vr["void_why"] == "twice" and vr["amount_p"] == 25000
          and not live(S1 + 2), dict(vr) if vr else None)
    POST("bhati", "/finance/physio/book/slip", dict(day=A, pick="c" + CID1, slip_no=str(S1 + 3), amount="250", mode="cash"))
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s" % A)
    t = text(h)
    check("day %s: Bhati cash Rs 500 / UPI Rs 250 = reception's -> '✓ Reception se mil gaya'" % A, "✓ Reception se mil gaya" in t, t[-400:])
    check("day %s: the voided slip's number is named missing ('is din ke beech: %d')" % (A, S1 + 2), ("is din ke beech: %d" % (S1 + 2)) in t, t[-300:])
    check("day %s: the voided slip is shown struck, with its reason ('hata di (do baar entry)')" % A, "hata di (do baar entry)" in t, t[-500:])
    POST("bhati", "/finance/physio/book/slip", dict(day=B, pick="c" + CID1, slip_no=str(S1 + 5), amount="250", mode="cash"))
    POST("bhati", "/finance/physio/book/slip", dict(day=B, pick="p%d" % pid2, slip_no=str(S1 + 6), amount="250", mode="upi"))
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s" % B)
    t = text(h)
    check("day %s: Bhati cash Rs 250 vs reception Rs 500 -> 'Farq: Cash ₹ 250 · UPI ₹ 0'" % B, "Farq: Cash ₹ 250 · UPI ₹ 0" in t, t[-400:])
    check("day %s: the number between the previous day's highest and this day's lowest is named ('pichhle din ke baad: %d')" % (B, S1 + 4),
          ("pichhle din ke baad: %d" % (S1 + 4)) in t, t[-300:])
    POST("bhati", "/finance/physio/book/slip", dict(day=C, pick="c" + CID1, slip_no=str(S1 + 7), amount="250", mode="cash"))
    s_, h, _ = GET("bhati", "/finance/physio/book?day=%s" % C)
    t = text(h)
    check("day %s: no reception row -> 'Reception ne abhi nahi likha'; the differing day %s is pointed to" % (C, B),
          "Reception ne abhi nahi likha" in t and "Farq wale aur din" in t, t[-300:])
    s_, loc = POST("bhati", "/finance/physio/book/slip", dict(day=OLD_DAY, pick="c" + CID1, slip_no=str(S1 + 30), amount="250", mode="cash"))
    check("a day outside the last 7 is refused", "err=day" in loc and not live(S1 + 30), loc)

    # ---- 3  home visits
    print("-- 3  home visits: three visits, two payments, the due; pause / restart / close; Clinic ID jodo")
    s_, loc = POST("bhati", "/finance/physio/book/home/new", dict(name=N3, mobile=MOB3, rate="500"))
    hc = q1("SELECT c.* FROM physio_course c JOIN physio_patient p ON p.id=c.patient_id WHERE p.name=? AND c.kind='home'", N3)
    check("+ Naya ghar patient: a home course at Rs 500 a visit", hc is not None and hc["rate_p"] == 50000 and hc["status"] == "active"
          and ("/finance/physio/book/home/%d" % hc["id"]) in loc, loc)
    cid = hc["id"] if hc else 0
    for d, amt in ((H1, "500"), (A, "500"), (C, "600")):
        POST("bhati", "/finance/physio/book/home/visit", dict(course=str(cid), day=d, amount=amt))
    POST("bhati", "/finance/physio/book/home/pay", dict(course=str(cid), day=H2, amount="700", mode="cash"))
    POST("bhati", "/finance/physio/book/home/pay", dict(course=str(cid), day=C, amount="500", mode="upi"))
    s_, loc = POST("bhati", "/finance/physio/book/home/visit", dict(course=str(cid), day=OLD_DAY, amount="500"))
    nv = v("SELECT COUNT(*) FROM physio_session WHERE course_id=? AND voided_at=''", cid)
    npay = v("SELECT COUNT(*) FROM physio_payment WHERE course_id=? AND voided_at=''", cid)
    check("three visits (Rs 500, 500, 600 -- no slip, no mode) and two payments (Rs 700 cash, Rs 500 UPI); a visit 11 days back refused",
          nv == 3 and npay == 2 and "err=day" in loc and v("SELECT COUNT(*) FROM physio_session WHERE course_id=? AND (slip_no IS NOT NULL OR mode<>'')", cid) == 0,
          (nv, npay, loc))
    s_, h, _ = GET("bhati", "/finance/physio/book/home/%d" % cid)
    t = text(h)
    check("the patient's page: charged Rs 1,600, Payment received Rs 1,200, due Rs 400; the full mobile shown (he visits them)",
          "₹ 1,600" in t and "₹ 1,200" in t and "Baaki ₹ 400" in t and MOB3 in h and "Payment received" in h and "Aaj visit hua ✓" in h, t[:400])
    s_, h, _ = GET("bhati", "/finance/physio/book?tab=home")
    row = re.search(r"%s.*?</tr>" % re.escape(N3), h, re.S)
    check("the Home tab: the patient with 3 visits and due Rs 400", row is not None and "₹ 400" in row.group(0) and ">3<" in row.group(0),
          row.group(0)[:300] if row else text(h)[:200])
    POST("bhati", "/finance/physio/book/home/status", dict(course=str(cid), status="paused"))
    st1 = v("SELECT status FROM physio_course WHERE id=?", cid)
    s_, loc = POST("bhati", "/finance/physio/book/home/visit", dict(course=str(cid), day=C, amount="500"))
    s_, h, _ = GET("bhati", "/finance/physio/book?tab=home")
    row = re.search(r"%s.*?</tr>" % re.escape(N3), h, re.S)
    check("Rok do: paused, shown 'ruka' among the running patients, no visit taken while paused", st1 == "paused" and "err=notactive" in loc
          and row is not None and "ruka" in row.group(0), (st1, loc))
    POST("bhati", "/finance/physio/book/home/status", dict(course=str(cid), status="active"))
    st2 = v("SELECT status FROM physio_course WHERE id=?", cid)
    POST("bhati", "/finance/physio/book/home/status", dict(course=str(cid), status="closed"))
    st3 = v("SELECT status FROM physio_course WHERE id=?", cid)
    s_, h, _ = GET("bhati", "/finance/physio/book?tab=home")
    band = h.split("<summary>Band (", 1)
    check("Phir shuru -> active; Band karo -> closed, listed under the folded 'Band' list", st2 == "active" and st3 == "closed"
          and len(band) == 2 and N3 in band[1], (st2, st3))
    POST("bhati", "/finance/physio/book/home/pay", dict(course=str(cid), day=C, amount="400", mode="cash"))
    POST("bhati", "/finance/physio/book/home/pay", dict(course=str(cid), day=C, amount="50", mode="cash"))
    pv = q1("SELECT id FROM physio_payment WHERE course_id=? AND amount_p=5000 AND voided_at=''", cid)
    POST("bhati", "/finance/physio/book/void", dict(kind="payment", id=str(pv[0] if pv else 0), why="amount", back="/finance/physio/book/home/%d" % cid))
    s_, h, _ = GET("bhati", "/finance/physio/book/home/%d" % cid)
    check("Payment received after closing (Rs 400) clears the due; a wrong Rs 50 payment voided ('galat amount') does not count",
          "Baaki ₹ 0" in text(h) and v("SELECT voided_at FROM physio_payment WHERE id=?", pv[0] if pv else 0) != "", text(h)[:300])
    pid3 = pid_of(N3)
    POST("bhati", "/finance/physio/book/patient/cid", dict(pid=str(pid3), clinic_id=CID9, back="/finance/physio/book/home/%d" % cid))
    s_, loc = POST("bhati", "/finance/physio/book/patient/cid", dict(pid=str(pid3), clinic_id=CID10, back="/finance/physio/book/home/%d" % cid))
    check("Clinic ID jodo: added once (%s); a second, different one refused -- never changed once set" % CID9,
          v("SELECT clinic_id FROM physio_patient WHERE id=?", pid3) == CID9 and "err=cidset" in loc, loc)

    # ---- 4  the owner's report
    print("-- 4  the owner's report (English)")
    s_, h, _ = GET("manoj", "/finance/physio/book/report?m=%s" % MONTH)
    t = text(h)
    check("report 200 for manoj; '1 day differs — reception and Bhati' with 11-Mar-2031 listed", s_ == 200 and "1 day differs — reception and Bhati" in t
          and "11-Mar-2031: Bhati cash ₹ 250, UPI ₹ 250 · reception cash ₹ 500, UPI ₹ 250" in t, t[:500])
    check("report: day-wise rows carry the clinic sessions, reception's figures, the match and the home visits / received",
          re.search(r"\w{3} 11-Mar\s*2\s*₹ 250\s*₹ 250\s*₹ 500\s*₹ 250\s*cash ₹ -250 · UPI ₹ 0", t) is not None
          and re.search(r"\w{3} 10-Mar\s*3\s*₹ 500\s*₹ 250\s*₹ 500\s*₹ 250\s*✓\s*1\s*₹ 500", t) is not None, t[t.find("Day-wise"):t.find("Day-wise") + 700])
    check("report: patient-wise home -- the home patient, 3 sessions, charged Rs 1,600, received Rs 1,600 (month), due Rs 0",
          re.search(r"%s · %s .{0,40}closed\s*3\s*₹ 1,600\s*₹ 1,600\s*₹ 0" % (re.escape(N3), CID9), t) is not None, t[t.find("home visits (Bhati"):][:500])
    check("report: patient-wise clinic lists the Docterz patient with its Clinic ID", re.search(r"%s · %s" % (re.escape(N1), CID1), t) is not None, t[:200])
    check("report: mobiles masked to the last four (no full mobile on the owner's page)", MOB2 not in h and MOB3 not in h and MOB3[-4:] in h and MOB2[-4:] in h)
    check("report: the month totals and the year", "Month totals — 2031" in t and "Year" in t)
    s_, h, _ = GET("bhawna", "/finance/physio/book/report?m=%s" % MONTH)
    check("report opens for bhawna (checker) too", s_ == 200 and "Day-wise" in h, s_)

    # ---- 5  the staff-eye walk: bhati's home, his door, his page
    print("-- 5  the staff-eye walk")
    code = ("import json,sys; sys.path.insert(0, %r); import portal as po; "
            "print('TILES ' + json.dumps([[t['name'], t.get('url', '')] for g, ts in po._visible_sections('staff', False, 'bhati') for t in ts]))" % a.portal)
    pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                        env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w552-walk-only",
                                 PYTHONDONTWRITEBYTECODE="1"))
    tl = [l for l in pp.stdout.splitlines() if l.startswith("TILES ")]
    tiles = json.loads(tl[-1][6:]) if tl else []
    check("bhati's portal home (the real portal.py + the grants file): the Physiotherapy tile -> /finance/physio (no tile granted or withdrawn by this kit)",
          ["Physiotherapy", "/finance/physio"] in tiles, (tiles, pp.stdout[-300:]))
    s_, h, _ = GET("bhati", "/finance/physio")
    check("LINK: bhati's door /finance/physio (Hindi page) shows 'Patient-wise register ›' -> /finance/physio/book, and no 'Report ›'",
          s_ == 200 and "href='/finance/physio/book'>Patient-wise register ›</a>" in h and "Report ›" not in h, (s_, text(h)[:200]))
    s_, h, _ = GET("manoj", "/finance/physio")
    check("LINK: manoj's /finance/physio (English page) shows 'Physio register ›' and 'Report ›'",
          s_ == 200 and "href='/finance/physio/book'>Physio register ›</a>" in h and "href='/finance/physio/book/report'>Report ›</a>" in h, text(h)[:200])
    s_, h, _ = GET("w552outsider", "/finance/physio")
    check("the Physiotherapy page for a login outside 'physiobook': unchanged, no link", s_ == 200 and "/finance/physio/book" not in h, s_)
    s_, h, _ = GET("bhati", "/finance/physio/book")
    check("bhati's door page while open: the slip entry and the match card are visible", s_ == 200 and "Slip likhiye" in h and "Milaan" in h, s_)

    # ---- 6  nothing else moved; the switch closes again
    print("-- 6  the accountants' income sheet, the morning match and reception's table unchanged; the switch off again")
    inc1, mt1 = income(), match()
    check("packs.build_income for March 2031 (a made-up day of revenue) and this month: byte-identical sheets before and after every physio row",
          inc0 == inc1 and inc0.get(MONTH, (None,))[0] is not None if has_rev else inc0 == inc1, [(k, w[1]) for k, w in inc1.items()])
    def _keys_differ(x, y):
        try:
            jx, jy = json.loads(x), json.loads(y)
            return [k for k in sorted(set(jx) | set(jy)) if jx.get(k) != jy.get(k)]
        except Exception:                        # noqa: BLE001
            return (x[:120], y[:120])
    check("the morning match of %s: identical before and after" % A, mt0 == mt1, _keys_differ(mt0, mt1))
    cpd_after = [tuple(r) for r in raw.execute("SELECT * FROM clinic_physio_day ORDER BY business_date")]
    check("clinic_physio_day (reception's table) not written by the register", cpd_before == cpd_after)
    n_aud = v("SELECT COUNT(*) FROM audit_log WHERE table_name IN ('physio_session','physio_payment','physio_course','physio_patient') AND by_whom='bhati' AND at>=?",
               "2000-01-01")
    check("every write audited through the app's own helper (bhati's audit rows present)", n_aud >= 15, n_aud)
    POST("manoj", "/finance/physio/book/switch", {"on": "0"})
    s_, h, _ = GET("bhati", "/finance/physio/book")
    check("manoj closes it: physio_book.on = 0 and bhati sees the one line again", (q1("SELECT value FROM setting WHERE key='physio_book.on'") or [None])[0] == "0"
          and OFF_LINE in h and "Slip likhiye" not in h)
    pb = os.path.join(fin, "physio_book.py")
    src = open(pb, encoding="utf-8").read() if os.path.exists(pb) else ""
    others = "".join(open(os.path.join(fin, f), encoding="utf-8").read() for f in ("packs.py", "clinic_register.py") if os.path.exists(os.path.join(fin, f)))
    check("static: the module never writes clinic_physio_day, holds no 10-digit number, never says 'Bharti'; packs.py and clinic_register.py never read physio_*",
          bool(src) and not re.search(r"(INSERT|UPDATE|DELETE)[^\"]{0,40}clinic_physio_day", src) and not re.search(r"\d{10}", src) and "Bharti" not in src
          and "physio_session" not in others and "physio_payment" not in others)

    raw.close()
    red = len(FAILS)
    if a.expect_red:
        link_red = [f for f in FAILS if f.startswith("LINK:")]
        if red and len(link_red) == 2:
            print("WALK OK negative control: %d of %d checks red on the old files, the link on the Physiotherapy page among them" % (red, RUN[0]))
            return 0
        print("NEGATIVE CONTROL FAILED: only %d of %d red on the old files (link red: %d)" % (red, RUN[0], len(link_red)))
        return 1
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    print("WALK OK S552: %d checks green (gates, switch, slips, duplicate, void, match ✓ and Farq, missing numbers, home course, report, staff-eye, income unchanged)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
