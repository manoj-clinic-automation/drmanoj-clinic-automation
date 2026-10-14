#!/usr/bin/env python3
"""walk_s553.py -- kit S553_BHATI_SLIP_DUTY (14-Oct-2026). Runs on a SCRATCH folder and a SCRATCH database only.
    python3 -B walk_s553.py --fin <scratch copy of /root/finance with the files under test> --db <a COPY of finance.db>
                            --portal <scratch copy of /root/portal *.py + tile_grants.json, no portal_config> --kit <kit> [--expect-red]
Made-up rows only, dated March 2031 (no person, no number); rows found by key, never by counting.
  1  THE DUTY'S SQL as shipped, evaluated at a fixed clock: its two moving parts -- the floor '2026-10-14' and SQLite's
     'now','localtime' -- are each replaced (each must occur exactly once) by 2031-03-10 and 2031-03-20 10:00, so only the
     made-up days are in its window. Per day: agrees -> not due; no Bhati entries -> due; cash agrees, UPI differs -> due; a voided
     entry and a home visit ignored; reception's 0 -> not due; before the floor -> never; today -> never. Then the clock and the
     floor moved one day each to show those two exclusions are what keep the days out (the test can fail).
  2  THE LIST through the REAL finance app loaded from --fin (header sign-in for this process only: a walk-only session, no live
     secret, no live user store), with a walk-only copy of the duties file whose SQL carries the same fixed clock: bhati's own
     list shows the line under 'Aaj', opening /finance/physio/book?day=<the oldest day>; the owner's view of bhati shows it;
     nobody else's list does; the owner's console item reads n = 2 and the day.
  3  THE STAFF-EYE WALK (CLAUDE.md, S444): bhati's portal home (the real portal.py + the grants file) carries the Physiotherapy
     tile; the door page /finance/physio/book?day=<day> as bhati shows that day's match card and its 'Farq' while due.
  4  A SAVED PANEL: with a saved panel for bhati that predates the line, aaj_kaam shows it OFF (new) -- the data step
     (cfg_s553.py) puts it on, a second run changes nothing, a line the owner took off stays off; other people's rows untouched.
  5  IT LEAVES BY ITSELF: once Bhati's entries agree, the line is gone from his list.
--expect-red: the same walk on the OLD two files must fail, the 'LINE:' checks among the failures (the negative control).
Prints 'WALK OK ...' on success; exit 1 on any failure."""
import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys

DID = "bhati.physio_register"
FLOOR_LIT, NOW_LIT = "'2026-10-14'", "'now','localtime'"
W_FLOOR, W_NOW = "2031-03-10", "2031-03-20 10:00:00"
D_BEFORE, D_NONE, D_OK, D_UPI, D_VOID, D_ZERO, D_TODAY = ("2031-03-09", "2031-03-11", "2031-03-12", "2031-03-13", "2031-03-14",
                                                         "2031-03-15", "2031-03-20")
PHYSIO_NOW = "2031-03-17T11:00:00"                 # the register's own clock: 11-Mar is inside its seven days
S0 = 95530001                                      # made-up slip numbers, far above any real book
WHO = "w553walk"
BASE = "https://followup.dr-manoj.in"
OTHERS = ("alisha", "shivani", "reception", "shavez", "darpan", "sukhveer", "amir", "manoj")
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


def shift(sql, floor=W_FLOOR, now=W_NOW):
    return sql.replace(FLOOR_LIT, "'%s'" % floor).replace(NOW_LIT, "'%s'" % now)


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
    anywhere = os.environ.get("S553_WALK_ANYWHERE") == "1"
    assert dbp.startswith("/tmp/") or anywhere, "the walk runs on a scratch copy in /tmp only"
    assert fin.startswith("/tmp/") or anywhere, "the walk loads a scratch folder in /tmp only"
    print("-- S553 walk on the %s: %s . db %s" % ("OLD files (negative control)" if a.expect_red else "new files", fin, os.path.basename(dbp)))

    raw = sqlite3.connect(dbp, timeout=30)
    raw.row_factory = sqlite3.Row
    have = {r[0] for r in raw.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"clinic_physio_day", "physio_session", "physio_course", "physio_patient", "setting"} <= have, "the physio tables are not on this copy"
    clash = raw.execute("SELECT COUNT(*) FROM clinic_physio_day WHERE business_date BETWEEN '2031-03-01' AND '2031-03-31'").fetchone()[0]
    assert clash == 0, "the copy already holds March-2031 physio days -- the walk's days are not its own"

    # ---- 0  made-up rows (found by key: the patient's name, the slip numbers, the dates)
    for d, cash, upi in ((D_BEFORE, 25000, 0), (D_NONE, 25000, 25000), (D_OK, 50000, 0), (D_UPI, 25000, 50000), (D_VOID, 25000, 0),
                         (D_ZERO, 0, 0), (D_TODAY, 25000, 0)):
        ins(raw, "clinic_physio_day", dict(business_date=d, cash_p=cash, upi_p=upi, entered_by=WHO, entered_at=W_NOW))
    pid = ins(raw, "physio_patient", dict(clinic_id="W553-0001", name="W553 WALK", mobile="", created_by=WHO, created_at=W_NOW))
    cc = ins(raw, "physio_course", dict(patient_id=pid, kind="clinic", rate_p=25000, status="active", started=D_BEFORE, changed_at=W_NOW, changed_by=WHO))
    hc = ins(raw, "physio_course", dict(patient_id=pid, kind="home", rate_p=50000, status="active", started=D_BEFORE, changed_at=W_NOW, changed_by=WHO))

    def slip(day, n, mode, amt=25000, voided=False, course=None):
        ins(raw, "physio_session", dict(course_id=course or cc, day=day, slip_no=n, amount_p=amt, mode=mode, by_whom="bhati", at=W_NOW,
                                        voided_at=(W_NOW if voided else ""), voided_by=("bhati" if voided else ""), void_why=("twice" if voided else "")))
    slip(D_OK, S0, "cash")
    slip(D_OK, S0 + 1, "cash")
    slip(D_UPI, S0 + 2, "cash")
    slip(D_UPI, S0 + 3, "upi")
    slip(D_VOID, S0 + 4, "cash")
    slip(D_VOID, S0 + 5, "cash", voided=True)
    slip(D_VOID, None, "cash", amt=50000, course=hc)              # a home visit on the same day: never reception's money
    on = raw.execute("SELECT value FROM setting WHERE key='aaj.staff_on'").fetchone()
    if not (on and "|" in str(on[0] or "")):
        raw.execute("DELETE FROM setting WHERE key='aaj.staff_on'")
        ins(raw, "setting", dict(key="aaj.staff_on", value="2031-03-01T00:00:00|%s" % WHO, note="S553 walk"))
    raw.execute("UPDATE setting SET value='1' WHERE key='physio_book.on'")
    if raw.execute("SELECT 1 FROM sqlite_master WHERE name='aaj_cfg'").fetchone():
        n_del = raw.execute("DELETE FROM aaj_cfg WHERE person='bhati'").rowcount
        if n_del:
            print("   (this copy held a saved panel for bhati: taken off the COPY so part 2 starts from the seed; part 4 tests a saved panel)")
    raw.commit()

    # ---- 1  the duty's SQL as shipped
    print("-- 1  the duty's SQL at a fixed clock (floor %s, now %s)" % (W_FLOOR, W_NOW))
    duties_path = os.path.join(fin, "aaj_duties.json")
    duties = json.load(open(duties_path, encoding="utf-8"))
    du = next((x for x in duties.get("extra") or [] if x.get("id") == DID), None)
    check("LINE: the duties file holds %s (person bhati, kind sql, tile Physiotherapy)" % DID,
          du is not None and du.get("person") == "bhati" and du.get("kind") == "sql" and du.get("tile") == "Physiotherapy", du)
    sql = (du or {}).get("sql") or ""
    check("the SQL is one read-only SELECT (no ';'), its floor and its clock each written exactly once",
          bool(re.match(r"(?is)^select\b", sql)) and ";" not in sql and sql.count(FLOOR_LIT) == 1 and sql.count(NOW_LIT) == 1, sql[:120])
    if du is not None and sql.count(FLOOR_LIT) == 1 and sql.count(NOW_LIT) == 1:
        ws = shift(sql)
        n, since = raw.execute(ws).fetchone()
        check("all the made-up days: n = 2 (11-Mar no entries, 13-Mar UPI differs), since = %s" % D_NONE, (n, since) == (2, D_NONE), (n, since))
        expect = {D_BEFORE: 0, D_NONE: 1, D_OK: 0, D_UPI: 1, D_VOID: 0, D_ZERO: 0, D_TODAY: 0}
        why = {D_BEFORE: "before the floor -- never", D_NONE: "reception wrote Rs 250 + Rs 250, no Bhati entry -- due",
               D_OK: "reception Rs 500 cash, Bhati Rs 500 cash -- not due", D_UPI: "cash agrees, UPI Rs 500 vs Rs 250 -- due",
               D_VOID: "Rs 250 cash agrees; a voided Rs 250 and a Rs 500 home visit ignored -- not due",
               D_ZERO: "reception wrote nothing (0 / 0) -- not due", D_TODAY: "today -- never"}
        for d in sorted(expect):
            got = raw.execute(ws + " AND r.business_date = '%s'" % d).fetchone()[0]
            check("%s: %s" % (d, why[d]), got == expect[d], got)
        n2 = raw.execute(shift(sql, now="2031-03-21 10:00:00")).fetchone()[0]
        n3 = raw.execute(shift(sql, floor="2031-03-09")).fetchone()[0]
        check("the clock one day on -> 20-Mar becomes due (n = 3); the floor one day back -> 09-Mar becomes due (n = 3): the two exclusions are real",
              n2 == 3 and n3 == 3, (n2, n3))
        rn = raw.execute(sql).fetchone()
        print("   (the shipped SQL on this copy's real rows, today's clock: n = %s, since %s)" % (rn[0], rn[1] or "-"))

    # ---- 2  the list through the real app
    print("-- 2  the lists, through the real finance app on the copy")
    wdu = json.loads(json.dumps(duties))
    for x in wdu.get("extra") or []:
        if x.get("id") == DID:
            x["sql"] = shift(x["sql"])
    wpath = os.path.join(os.path.dirname(dbp), "walk_s553_duties.json")
    with open(wpath, "w", encoding="utf-8") as fh:
        json.dump(wdu, fh, ensure_ascii=False)
    os.environ.update(FINANCE_DB=dbp, FINANCE_ALLOW_HEADER_AUTH="1", PHYSIO_BOOK_NOW=PHYSIO_NOW, FINANCE_DEV_USER="", FINANCE_DEV_ROLE="",
                      AAJ_DUTIES_JSON=wpath)
    sys.path.insert(0, fin)
    os.chdir(fin)
    import finance_app as fa                       # noqa: E402
    import aaj_kaam                                # noqa: E402
    import aaj_seed                                # noqa: E402
    print("   the real finance app loaded from the scratch folder; parts that did not load: %s" % ([n for n, _w in fa._MOUNT_FAILED] or "none"))
    c = fa.app.test_client(use_cookies=False)

    def GET(u, path):
        r = c.get(path, base_url=BASE, headers={"X-Clinic-User": u, "X-Clinic-Role": ""})
        return r.status_code, r.get_data(as_text=True)

    def rows_of(u, as_=None):
        s, h = GET(u, "/finance/aaj/api/list" + ("?as=%s" % as_ if as_ else ""))
        try:
            j = json.loads(h)
        except ValueError:
            return s, None, []
        return s, j, [dict(r, section=sec["key"]) for sec in (j.get("sections") or []) for r in sec["rows"]]

    def mine(rows):
        return [r for r in rows if r.get("id") == DID]

    s, j, rows = rows_of("bhati")
    m = mine(rows)
    want_door = "/finance/physio/book?day=%s" % D_NONE
    check("LINE: bhati's own list (signed in as bhati) shows the line under 'Aaj', opening %s, tile Physiotherapy" % want_door,
          s == 200 and len(m) == 1 and m[0]["kind"] == "job" and m[0]["section"] == "day" and m[0]["door"] == want_door
          and m[0]["tile"] == "Physiotherapy", (s, m, (j or {}).get("error")))
    seed_line = next((ln for p in aaj_seed.PEOPLE if p["key"] == "bhati" for ln in p["lines"] if ln["id"] == DID), None)
    check("LINE: the words bhati reads are the panel line's ('%s')" % ((seed_line or {}).get("hi") or "-"),
          bool(m) and seed_line is not None and m[0]["text"] == seed_line["hi"] and "{since}" not in m[0]["text"], m[:1])
    s, j, rows = rows_of("manoj", "bhati")
    check("LINE: the owner's view of bhati (/finance/aaj/api/list?as=bhati, signed in as manoj) shows the line", s == 200 and len(mine(rows)) == 1, (s, mine(rows)))
    leak = []
    for u in OTHERS:
        s, j, rows = rows_of("manoj", u)
        if mine(rows) or s != 200:
            leak.append((u, s))
    s, j, rows = rows_of("alisha")
    if mine(rows):
        leak.append(("alisha signed in", s))
    check("nobody else's list shows it (the owner's view of %s, and alisha signed in)" % ", ".join(OTHERS), not leak, leak)
    res = aaj_kaam.build_all(dbp)
    it = next((i for i in res.get("items") or [] if i.get("id") == DID), None)
    check("LINE: the owner's console item: n = 2, since %s, 'Bhati: physiotherapy slips of 11...' , no error" % D_NONE,
          it is not None and it["n"] == 2 and it["since"] == D_NONE and not it.get("err") and str(it.get("en") or "").startswith("Bhati: physiotherapy slips of 11"),
          {k: (it or {}).get(k) for k in ("n", "since", "en", "err")})

    # ---- 3  the staff-eye walk: the tile on his home, the door page
    print("-- 3  the staff-eye walk")
    code = ("import json,sys; sys.path.insert(0, %r); import portal as po; "
            "print('TILES ' + json.dumps([[t['name'], t.get('url', '')] for g, ts in po._visible_sections('staff', False, 'bhati') for t in ts]))" % a.portal)
    pp = subprocess.run([sys.executable, "-B", "-c", code], cwd=a.portal, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True,
                        env=dict(os.environ, TILE_GRANTS_FILE=os.path.join(a.portal, "tile_grants.json"), CLINIC_SSO_SECRET="w553-walk-only",
                                 PYTHONDONTWRITEBYTECODE="1"))
    tl = [ln for ln in pp.stdout.splitlines() if ln.startswith("TILES ")]
    tiles = json.loads(tl[-1][6:]) if tl else []
    check("bhati's portal home (the real portal.py + the grants file) carries the Physiotherapy tile -> /finance/physio",
          ["Physiotherapy", "/finance/physio"] in tiles, (tiles, pp.stdout[-300:]))
    s, h = GET("bhati", want_door)
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    check("the door as bhati: %s answers 200 with 11-Mar's match card and its marker 'Farq: Cash ₹ 250 · UPI ₹ 250'" % want_door,
          s == 200 and "Milaan — 11-Mar-2031" in t and "Farq: Cash ₹ 250 · UPI ₹ 250" in t, (s, t[-300:]))

    # ---- 4  a saved panel
    print("-- 4  a saved panel for bhati that predates the line")
    lp = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "cfg_s553.py"), "--line"], stdout=subprocess.PIPE, universal_newlines=True)
    try:
        dline = json.loads(lp.stdout)
    except ValueError:
        dline = {}
    check("the data step's line is the seed's line, word for word, switched on, under 'Aaj'",
          seed_line is not None and dline == {k: seed_line[k] for k in ("id", "hi", "en", "when", "on")} and dline.get("on") is True, (dline, seed_line))
    raw.execute(aaj_kaam.CFG_SQL)
    old_lines = [dict(id=ln["id"], hi=ln["hi"], en=ln["en"], when=ln["when"], on=True) for p in aaj_seed.PEOPLE if p["key"] == "bhati"
                 for ln in p["lines"] if ln["id"] != DID]
    others_before = [tuple(r) for r in raw.execute("SELECT person, doc, edited_at, edited_by FROM aaj_cfg WHERE person <> 'bhati' ORDER BY person")]
    raw.execute("INSERT INTO aaj_cfg (person, doc, edited_at, edited_by) VALUES ('bhati', ?, '2031-03-01T09:00:00', ?)",
                (json.dumps(dict(on=True, note="", first_on=None, lines=old_lines, removed=[])), WHO))
    raw.commit()
    s, j, rows = rows_of("bhati")
    rd = aaj_kaam.Reader(dbp)
    try:
        pl = next((ln for ln in rd.people["bhati"]["lines"] if ln["id"] == DID), None)
    finally:
        rd.close()
    check("before the data step: aaj_kaam lays the line on the saved panel OFF and marked new -- not on his list", bool(pl) and pl.get("on") is False
          and pl.get("new") is True and not mine(rows), (pl, len(mine(rows))))

    def step():
        p = subprocess.run([sys.executable, "-B", os.path.join(a.kit, "cfg_s553.py"), dbp], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        return p.returncode, p.stdout.strip()
    rc1, o1 = step()
    print("   " + o1)
    s, j, rows = rows_of("bhati")
    rd = aaj_kaam.Reader(dbp)
    try:
        pl = next((ln for ln in rd.people["bhati"]["lines"] if ln["id"] == DID), None)
        bon = rd.people["bhati"]["on"]
    finally:
        rd.close()
    check("LINE: after the data step: on his saved panel switched on (not 'new'), his list shows it, his list still on",
          rc1 == 0 and "1 changed" in o1 and bool(pl) and pl.get("on") is True and not pl.get("new") and len(mine(rows)) == 1 and bon, (o1, pl, len(mine(rows))))
    rc2, o2 = step()
    check("a second run of the data step changes nothing ('0 changed')", rc2 == 0 and "0 changed" in o2, o2)
    doc = json.loads(raw.execute("SELECT doc FROM aaj_cfg WHERE person='bhati'").fetchone()[0])
    doc["removed"] = [dict(x, on=False) for x in doc["lines"] if x["id"] == DID]
    doc["lines"] = [x for x in doc["lines"] if x["id"] != DID]
    raw.execute("UPDATE aaj_cfg SET doc=? WHERE person='bhati'", (json.dumps(doc),))
    raw.commit()
    rc3, o3 = step()
    s, j, rows = rows_of("bhati")
    check("a line the owner took off his panel stays off: the data step leaves it ('0 changed'), not on the list",
          rc3 == 0 and "0 changed" in o3 and not mine(rows), (o3, len(mine(rows))))
    others_after = [tuple(r) for r in raw.execute("SELECT person, doc, edited_at, edited_by FROM aaj_cfg WHERE person <> 'bhati' ORDER BY person")]
    check("nobody else's saved panel was touched", others_before == others_after)
    raw.execute("DELETE FROM aaj_cfg WHERE person='bhati'")
    raw.commit()

    # ---- 5  it leaves by itself
    print("-- 5  Bhati's entries made to agree")
    slip(D_NONE, S0 + 6, "cash")
    slip(D_NONE, S0 + 7, "upi")
    slip(D_UPI, S0 + 8, "upi")
    raw.commit()
    s, j, rows = rows_of("bhati")
    n_after = raw.execute(shift(sql)).fetchone()[0] if du is not None else None
    check("LINE: with 11-Mar and 13-Mar entered to agree, the SQL reads 0 and the line has left bhati's list by itself",
          du is not None and n_after == 0 and s == 200 and not mine(rows), (n_after, len(mine(rows))))

    # ---- static
    kit_text = "".join(open(os.path.join(a.kit, f), encoding="utf-8").read() for f in sorted(os.listdir(a.kit))
                       if f.endswith((".py", ".sh", ".md", ".kit", ".txt")))
    check("static: the kit holds no 10-digit number and never misspells Bhati's name; the duty's SQL writes nothing",
          not re.search(r"(?<![0-9A-Za-z])\d{10}(?![0-9A-Za-z])", kit_text) and "Bh" + "arti" not in kit_text
          and not re.search(r"(?i)\b(insert|update|delete|replace|drop|alter|create)\b", sql))
    raw.close()
    red = len(FAILS)
    if a.expect_red:
        lr = [f for f in FAILS if f.startswith("LINE:")]
        if red and len(lr) >= 5:
            print("WALK OK negative control: %d of %d checks red on the old files, %d of them 'LINE:' (the line is nowhere)" % (red, RUN[0], len(lr)))
            return 0
        print("NEGATIVE CONTROL FAILED: only %d of %d red on the old files ('LINE:' red: %d)" % (red, RUN[0], len(lr)))
        return 1
    if FAILS:
        print("WALK RED: %d of %d checks failed" % (red, RUN[0]))
        return 1
    print("WALK OK S553: %d checks green (the SQL day by day, bhati's list and door, nobody else's, the console, the tile, the saved panel, leaves by itself)" % RUN[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
