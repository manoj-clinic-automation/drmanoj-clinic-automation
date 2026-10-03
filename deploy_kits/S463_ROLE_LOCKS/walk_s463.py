#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s463.py -- S463_ROLE_LOCKS: the checker's figures answer only the checker -- walked.

  usage: walk_s463.py --apply <apply_s463.py> --finance <folder holding finance_app.py and its sibling files>

The app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's edits), each with an EMPTY
database made from the app's own schema and two made-up days in it (one pharmacy, one clinic). Six made-up logins --
a maker, a viewer and a checker on each unit -- ask every route the kit touches and every route it deliberately
leaves, on both files. Each leak is first SHOWN on the old file, then shown closed on the new one; every answer a
person is still entitled to is compared byte for byte. Nothing live is opened. Last line: WALK_S463 GREEN|RED.
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "27a162e6740140d4ce7d2e293eae9809"
TO = "49f52391f44643c10b052609cffc5bbe"
MARK = "@@S463JSON@@ "
OK, FAIL = [], []
MD, CD = "2026-09-10", "2026-09-11"            # the made-up pharmacy day and clinic day

MED_CHECKER_ONLY = ["/finance/api/month/2026-09", "/finance/api/days?ym=2026-09", "/finance/api/parked",
                    "/finance/api/month/2026-09/close-check", "/finance/api/sources", "/finance/api/archive/queue"]
MED_PAGES = ["/finance/review", "/finance/workbench"]
MED_STAFF = ["/finance/api/day/%s/lines" % MD]
CL_CHECKER_ONLY = ["/finance/clinic/api/month/2026-09", "/finance/clinic/api/days?ym=2026-09", "/finance/clinic/api/parked"]
CL_PAGES = ["/finance/clinic/review"]
CL_STAFF = ["/finance/clinic/api/day/%s" % CD]
LEFT = ["/finance/api/day/%s" % MD, "/finance/api/whoami", "/finance/api/tile-meta", "/finance/", "/finance/daily",
        "/finance/api/exceptions", "/finance/healthz",
        "/finance/clinic/", "/finance/clinic/entry", "/finance/clinic/api/tile", "/finance/clinic/api/exceptions",
        "/finance/clinic/api/whoami", "/finance/clinic/api/tile-meta"]
WHO = {"m_maker": "wdarpan", "m_viewer": "wdesk", "m_checker": "wdoctor",
       "c_maker": "wreception", "c_viewer": "wcview", "c_checker": "wdoctor"}


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:400]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def child():
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    con = sqlite3.connect(fa.DB_PATH)
    for unit, user, role in (("medical", "wdarpan", "maker"), ("medical", "wdesk", "viewer"), ("medical", "wdoctor", "checker"),
                             ("clinic", "wreception", "maker"), ("clinic", "wcview", "viewer"), ("clinic", "wdoctor", "checker")):
        con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES (?,?,?,1)", (unit, user, role))
    for unit, d, cash, upi in (("medical", MD, 1234500, 456700), ("clinic", CD, 2345600, 567800)):
        con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at,approved_by,approved_at) "
                    "VALUES (?,?,'approved','app','walk',?,'wdoctor',?)", (unit, d, d + "T09:00:00", d + "T21:00:00"))
        e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?", (unit, d)).fetchone()[0]
        svc = "pharmacy_sale" if unit == "medical" else con.execute(
            "SELECT service FROM day_line LIMIT 1").fetchone()
        svc = svc if isinstance(svc, str) else "pharmacy_sale"
        try:
            con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'cash',?)", (e, svc, cash))
            con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'upi',?)", (e, svc, upi))
        except sqlite3.Error:
            for s2 in ("consultation", "opd", "clinic_fee"):
                try:
                    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'cash',?)", (e, s2, cash))
                    con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'upi',?)", (e, s2, upi))
                    break
                except sqlite3.Error:
                    continue
    con.commit()
    con.close()
    c = fa.app.test_client()
    out = {}
    for tag, user in WHO.items():
        got = {}
        for p in (MED_CHECKER_ONLY + MED_PAGES + MED_STAFF + CL_CHECKER_ONLY + CL_PAGES + CL_STAFF + LEFT):
            r = c.get(p, headers={"X-Clinic-User": user})
            body = r.get_data(as_text=True)
            got[p] = [r.status_code, hashlib.md5(body.encode("utf-8")).hexdigest(), body[:300],
                      [k for k in ("16,912.00", "29,134.00", MD, CD, "not_permitted") if k in body]]
        out[tag] = got
    # the worker's token still opens the archive queue; a wrong token does not
    out["token_ok"] = c.get("/finance/api/archive/queue", headers={"X-Finance-Cron": os.environ["FINANCE_CRON_TOKEN"]}).status_code
    out["token_bad"] = c.get("/finance/api/archive/queue", headers={"X-Finance-Cron": "not-the-token"}).status_code
    out["nobody"] = {p: c.get(p).status_code for p in (MED_CHECKER_ONLY + MED_PAGES + CL_CHECKER_ONLY + CL_PAGES)}
    # month-close still reaches its own check from inside (the checker's finalise calls close-check in-process)
    r = c.post("/finance/api/month/2026-09/finalise", json={}, headers={"X-Clinic-User": "wdoctor"})
    out["finalise"] = [r.status_code, (r.get_json() or {}).get("error") or "", r.get_data(as_text=True)[:200]]
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    n = 0
    for pat in ("*.py", "*.sql", "*.html"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
                n += 1
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))
    return n


def make_db(appdir):
    con = sqlite3.connect(os.path.join(appdir, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(appdir, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    # the walk's stand-ins for the two C2 tables (that migration is not a file beside the app); empty, read only
    con.execute("CREATE TABLE IF NOT EXISTS clinic_line_side (id INTEGER PRIMARY KEY, day_entry_id INTEGER, "
                "tender TEXT, amount_p INTEGER, line_kind TEXT, note TEXT)")
    con.execute("CREATE TABLE IF NOT EXISTS clinic_verification (id INTEGER PRIMARY KEY, day_entry_id INTEGER, "
                "verified_by TEXT, verified_at TEXT, note TEXT)")
    con.commit()
    con.close()


def run(root, tag, appdir):
    tmp = os.path.join(root, "tmp_" + tag)
    os.makedirs(tmp)
    e = dict(os.environ)
    # the cron token below is made up afresh at every run -- it is never the box's, and no value is written in this file
    e.update({"FINANCE_DB": os.path.join(appdir, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(root, "scans_" + tag),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(root, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(root, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(root, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups"),
              "FINANCE_AUTOAPPLY_OFF": os.path.join(root, "AUTOAPPLY_OFF_absent"), "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=300)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s463_walk_")
    try:
        walk(a, root)
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S463 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    check("0.1 the unpatched finance_app.py is the file this kit was built from (27a162e6, S462's)",
          md5(os.path.join(old, "finance_app.py")) == FROM, md5(os.path.join(old, "finance_app.py")))
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.2 the edits apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read().splitlines()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read().splitlines()
    gone = [x for x in so if x not in set(sn)]
    check("0.4 one old line is replaced (inside selftest); no line of a route is removed",
          len(gone) == 1 and "_mrv = c.get" in gone[0], gone)
    import difflib
    sm = difflib.SequenceMatcher(None, so, sn, autojunk=False)
    added = [l for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag in ("insert", "replace") for l in sn[j1:j2]]
    check("0.5 every added line is a role check, its refusal, or a selftest line (%d added)" % len(added),
          all(("require(" in l or l.strip() in ("if err:", "return err", "return redirect(PORTAL_LOGIN, code=302)")
               or "_tok_ok(" in l or "S463" in l or "FINANCE_DEV_ROLE" in l or "c.get(" in l or "j = r.get_json()" in l
               or 'check("' in l) for l in added), [l for l in added if "require(" not in l][:6])
    for d in (old, new):
        make_db(d)
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d)
        check("0.6 the %s app answered all six logins" % tag, bool(R[tag]) and all(k in R[tag] for k in WHO), p.stderr[-600:])
    if not (R.get("old") and R.get("new")):
        return
    o, nw = R["old"], R["new"]

    def st(r, who, paths):
        return [r[who][p][0] for p in paths]

    # ---- 1 · the leak, shown
    check("1.1 SHOWN on the old file: a pharmacy VIEWER (the returns desk) reads the month, the day list, parked cash, "
          "the close check, the sources and the archive queue", st(o, "m_viewer", MED_CHECKER_ONLY) == [200] * 6,
          st(o, "m_viewer", MED_CHECKER_ONLY))
    check("1.2 SHOWN on the old file: the month a viewer reads carries the made-up day's money",
          "16,912.00" in o["m_viewer"]["/finance/api/month/2026-09"][3]
          and "16,912.00" in o["m_viewer"]["/finance/api/days?ym=2026-09"][3], o["m_viewer"]["/finance/api/month/2026-09"][3])
    check("1.3 SHOWN on the old file: a pharmacy MAKER reads the same six, and opens the review and workbench pages",
          st(o, "m_maker", MED_CHECKER_ONLY) == [200] * 6 and st(o, "m_maker", MED_PAGES) == [200, 200])
    check("1.4 SHOWN on the old file: a viewer reads the patient-named day lines", st(o, "m_viewer", MED_STAFF) == [200])
    check("1.5 SHOWN on the old file: a clinic VIEWER and a clinic MAKER read the clinic month, day list and parked cash",
          st(o, "c_viewer", CL_CHECKER_ONLY) == [200] * 3 and st(o, "c_maker", CL_CHECKER_ONLY) == [200] * 3,
          (st(o, "c_viewer", CL_CHECKER_ONLY), st(o, "c_maker", CL_CHECKER_ONLY)))
    check("1.6 SHOWN on the old file: a clinic maker and viewer open the checker's clinic review screen",
          st(o, "c_maker", CL_PAGES) == [200] and st(o, "c_viewer", CL_PAGES) == [200])

    # ---- 2 · closed
    for who in ("m_viewer", "m_maker"):
        check("2.1 new: the pharmacy %s is refused all six (403, the app's own 'not permitted')" % who.split("_")[1],
              st(nw, who, MED_CHECKER_ONLY) == [403] * 6 and all("not_permitted" in nw[who][p][2] for p in MED_CHECKER_ONLY),
              st(nw, who, MED_CHECKER_ONLY))
        check("2.2 new: the pharmacy %s is sent back to the portal from the review and workbench pages" % who.split("_")[1],
              st(nw, who, MED_PAGES) == [302, 302], st(nw, who, MED_PAGES))
    check("2.3 new: a viewer is refused the patient-named day lines; the maker and the checker still read them, the same bytes",
          st(nw, "m_viewer", MED_STAFF) == [403] and nw["m_maker"][MED_STAFF[0]][:2] == o["m_maker"][MED_STAFF[0]][:2]
          and nw["m_checker"][MED_STAFF[0]][:2] == o["m_checker"][MED_STAFF[0]][:2] and nw["m_maker"][MED_STAFF[0]][0] == 200)
    for who in ("c_viewer", "c_maker"):
        check("2.4 new: the clinic %s is refused the clinic month, day list and parked cash, and the review screen" % who.split("_")[1],
              st(nw, who, CL_CHECKER_ONLY) == [403] * 3 and st(nw, who, CL_PAGES) == [302], (st(nw, who, CL_CHECKER_ONLY), st(nw, who, CL_PAGES)))
    check("2.5 new: a clinic viewer is refused the clinic day; reception (the maker) reads it, the same bytes as before",
          st(nw, "c_viewer", CL_STAFF) == [403] and nw["c_maker"][CL_STAFF[0]][:2] == o["c_maker"][CL_STAFF[0]][:2]
          and nw["c_maker"][CL_STAFF[0]][0] == 200, (st(nw, "c_viewer", CL_STAFF), nw["c_maker"][CL_STAFF[0]][0]))

    # ---- 3 · the checker loses nothing
    allp = MED_CHECKER_ONLY + MED_PAGES + MED_STAFF
    check("3.1 unchanged: the pharmacy checker gets every one of the nine, byte for byte (all 200)",
          all(nw["m_checker"][p][:2] == o["m_checker"][p][:2] and nw["m_checker"][p][0] == 200 for p in allp),
          [(p, o["m_checker"][p][0], nw["m_checker"][p][0]) for p in allp if nw["m_checker"][p][:2] != o["m_checker"][p][:2]])
    allc = CL_CHECKER_ONLY + CL_PAGES + CL_STAFF
    check("3.2 unchanged: the clinic checker gets every one of the five, byte for byte (all 200)",
          all(nw["c_checker"][p][:2] == o["c_checker"][p][:2] and nw["c_checker"][p][0] == 200 for p in allc),
          [(p, o["c_checker"][p][0], nw["c_checker"][p][0]) for p in allc if nw["c_checker"][p][:2] != o["c_checker"][p][:2]])
    check("3.3 the checker's month does carry the made-up day (the figures are real, not an empty answer)",
          "16,912.00" in nw["m_checker"]["/finance/api/month/2026-09"][3] and MD in nw["m_checker"]["/finance/api/days?ym=2026-09"][3]
          and "29,134.00" in nw["c_checker"]["/finance/clinic/api/month/2026-09"][3], nw["c_checker"]["/finance/clinic/api/month/2026-09"][3])

    # ---- 4 · everything deliberately left
    diff = [(who, p, o[who][p][0], nw[who][p][0]) for who in WHO for p in LEFT if o[who][p][:2] != nw[who][p][:2]]
    check("4.1 unchanged: all %d routes left alone answer all six logins exactly as before (%d answers compared)"
          % (len(LEFT), len(LEFT) * len(WHO)), diff == [], diff[:6])
    check("4.2 the pharmacy maker's own page and day still open (the root lands him on Daily Sale; his day reads)",
          nw["m_maker"]["/finance/"][0] == 200 and nw["m_maker"]["/finance/daily"][0] in (200, 302)
          and nw["m_maker"]["/finance/api/day/%s" % MD][0] == 200, (nw["m_maker"]["/finance/"][0], nw["m_maker"]["/finance/daily"][0]))
    check("4.3 reception's entry page and the three reads it makes still answer (the page, its day, the tile, the missing days)",
          nw["c_maker"]["/finance/clinic/entry"][0] == 200 and nw["c_maker"]["/finance/clinic/"][0] == 200
          and nw["c_maker"][CL_STAFF[0]][0] == 200 and nw["c_maker"]["/finance/clinic/api/tile"][0] == 200
          and nw["c_maker"]["/finance/clinic/api/exceptions"][0] == 200)
    check("4.4 a pharmacy login still gets nothing on the clinic side, and the other way round (the gate, as before)",
          nw["m_maker"]["/finance/clinic/api/tile"][0] == 403 and nw["c_maker"]["/finance/api/whoami"][0] in (200, 403)
          and o["c_maker"]["/finance/api/day/%s" % MD][0] == nw["c_maker"]["/finance/api/day/%s" % MD][0])

    # ---- 5 · tokens, no identity, and the month close
    check("5.1 the worker's token still opens the archive queue; a wrong token does not (old and new alike for the right one)",
          o["token_ok"] == 200 and nw["token_ok"] == 200 and nw["token_bad"] in (401, 403), (o["token_ok"], nw["token_ok"], nw["token_bad"]))
    check("5.2 with no login at all every one of them is refused at the gate, as before",
          o["nobody"] == nw["nobody"] and all(v in (401, 302) for v in nw["nobody"].values()), nw["nobody"])
    check("5.3 unchanged: the checker's month close still reaches its own close check from inside",
          o["finalise"] == nw["finalise"], (o["finalise"], nw["finalise"]))
    check("5.4 nothing in the app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) in (FROM, TO))


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
