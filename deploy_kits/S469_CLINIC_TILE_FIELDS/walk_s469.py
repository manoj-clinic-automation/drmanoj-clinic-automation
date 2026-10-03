#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s469.py -- S469_CLINIC_TILE_FIELDS: reception is handed what its page shows, and no more -- walked.

  usage: walk_s469.py --apply <apply_s469.py> --finance <folder holding finance_app.py and its sibling files>

The app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with the kit's two edits), each with an
EMPTY database made from the app's own schema, one made-up clinic day and five made-up open exceptions. Four made-up
logins -- reception (maker), a viewer and a checker on the clinic, and a pharmacy login with no clinic role -- ask
the two routes with the bank limit not crossed and then crossed. Each leak is first SHOWN on the old file; the
checker's answers are compared whole, old against new; and the fields reception's own page reads are read off that
page's code and held against what a non-checker now gets. Nothing live is opened. Last line: WALK_S469 GREEN|RED.
"""
import argparse
import ast
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = "8f69f192020205b302ac413a039f7c31"
TO = "727a2e7a5b23a606776fa12d75f8dcc8"
MARK = "@@S469JSON@@ "
OK, FAIL = [], []
CD = "2026-09-11"
WHO = {"maker": "wreception", "viewer": "wcview", "checker": "wdoctor", "pharmacy_only": "wdarpan"}
SAME = ["/finance/clinic/api/tile-meta", "/finance/clinic/api/whoami", "/finance/clinic/entry", "/finance/clinic/"]


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:700]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def child():
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    root = os.path.realpath(os.environ["S469_ROOT"]) + os.sep
    if not os.path.realpath(fa.DB_PATH).startswith(root):
        print(MARK + json.dumps({"abort": "the finance database is not the scratch one"}))
        return
    con = sqlite3.connect(fa.DB_PATH)
    cu = fa.CLINIC_UNIT
    for unit, user, role in ((cu, "wreception", "maker"), (cu, "wcview", "viewer"), (cu, "wdoctor", "checker"),
                             ("medical", "wdarpan", "maker"), ("medical", "wdoctor", "checker")):
        con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES (?,?,?,1)", (unit, user, role))
    con.execute("INSERT INTO day_entry (unit,business_date,status,source,entered_by,entered_at,approved_by,approved_at) "
                "VALUES (?,?,'approved','app','walk',?,'wdoctor',?)", (cu, CD, CD + "T09:00:00", CD + "T21:00:00"))
    e = con.execute("SELECT id FROM day_entry WHERE unit=? AND business_date=?", (cu, CD)).fetchone()[0]
    placed = False
    for svc in ("pharmacy_sale", "consultation", "opd", "clinic_fee"):
        try:
            con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'cash',?)", (e, svc, 2345600))
            con.execute("INSERT INTO day_line (day_entry_id,service,mode,amount_p) VALUES (?,?,'upi',?)", (e, svc, 567800))
            placed = True
            break
        except sqlite3.Error:
            continue
    for unit, d, kind in ((cu, "2026-09-12", "missing_day"), (cu, "2026-09-13", "missing_day"), (cu, CD, "negative_cash"),
                          (cu, CD, "carry_forward_break"), (cu, CD, "upi_vs_statement"), ("medical", "2026-09-12", "missing_day")):
        con.execute("INSERT INTO recon_exception (unit,business_date,kind,diff_p,severity,status,detail) VALUES (?,?,?,?,?,'open',?)",
                    (unit, d, kind, 12300, "high", "made up for the walk: " + kind))
    con.commit()
    c = fa.app.test_client()

    def ask(path, user):
        r = c.get(path, headers={"X-Clinic-User": user} if user else {})
        return [r.status_code, r.get_json(silent=True), hashlib.md5(r.get_data()).hexdigest()]

    out = {"lines_placed": placed, "clinic_unit": cu}
    for scen, thr in (("not_due", None), ("due", "100")):
        if thr is not None:
            con.execute("INSERT OR REPLACE INTO setting (key, value) VALUES (?,?)", ("%s.deposit_threshold_p" % cu, thr))
            con.commit()
        got = {}
        for tag, user in list(WHO.items()) + [("nobody", "")]:
            got[tag] = {"tile": ask("/finance/clinic/api/tile", user), "exc": ask("/finance/clinic/api/exceptions", user)}
        out[scen] = got
    out["same"] = {tag: {p: ask(p, user)[::2] for p in SAME} for tag, user in WHO.items()}
    out["medical"] = {tag: {p: ask(p, user)[::2] for p in ("/finance/api/tile", "/finance/api/exceptions")}
                      for tag, user in (("checker", "wdoctor"), ("maker", "wdarpan"))}
    con.close()
    print(MARK + json.dumps(out))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024:
                shutil.copy2(f, dst)
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))


def run(root, tag, appdir):
    base = os.path.join(root, "run_" + tag)
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    con = sqlite3.connect(os.path.join(base, "finance.db"))
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
    e = dict(os.environ)
    # the cron token below is made up afresh at every run -- it is never the box's, and no value is written in this file
    e.update({"S469_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(base, "scans"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "ASSETS_DB": os.path.join(base, "no_assets.db"), "FINANCE_UPI_DIR": os.path.join(base, "upi"),
              "FINANCE_YESBANK_DIR": os.path.join(base, "yes"), "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"),
              "PYTHONDONTWRITEBYTECODE": "1"})
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=400)
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
    root = tempfile.mkdtemp(prefix="s469_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S469 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin = os.path.abspath(a.finance)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    have = md5(os.path.join(old, "finance_app.py"))
    check("0.1 the unpatched finance_app.py is the file this kit was built from (8f69f192, S468's)", have == FROM, have)
    if have != FROM:
        return
    shutil.copytree(old, new)
    p = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    got = md5(os.path.join(new, "finance_app.py"))
    check("0.2 the two edits apply and give the predicted bytes", p.returncode == 0 and got == TO, got + " " + p.stderr[-200:])
    p2 = subprocess.run([sys.executable, "-B", a.apply, os.path.join(new, "finance_app.py")], capture_output=True, text=True)
    check("0.3 applied twice: refused, the file left byte for byte", p2.returncode != 0 and md5(os.path.join(new, "finance_app.py")) == got)
    so = open(os.path.join(old, "finance_app.py"), encoding="utf-8").read()
    sn = open(os.path.join(new, "finance_app.py"), encoding="utf-8").read()
    import difflib
    ops = [o for o in difflib.SequenceMatcher(None, so.splitlines(), sn.splitlines(), autojunk=False).get_opcodes() if o[0] != "equal"]
    fn = {n.name: n for n in ast.parse(sn).body if isinstance(n, ast.FunctionDef) and n.name in ("clinic_api_tile", "clinic_api_exceptions")}
    inside = all(any(f.lineno <= o[3] + 1 and o[4] <= f.end_lineno for f in fn.values()) for o in ops)
    gone = [l for o in ops for l in so.splitlines()[o[1]:o[2]]]
    check("0.4 two places differ, both INSIDE clinic_api_tile and clinic_api_exceptions; the only old line removed is the one-line body of the exceptions route",
          len(ops) == 2 and len(fn) == 2 and inside and gone == ["    return jsonify(ok=True, exceptions=open_exceptions(db(), CLINIC_UNIT))"], (ops, gone))
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d)
        check("0.5 the %s app answered every login" % tag, bool(R[tag]) and "abort" not in R[tag] and "due" in R[tag] and R[tag]["lines_placed"],
              (R[tag] or {}).get("abort") or p.stderr[-600:])
    if not (R.get("old") and R.get("new") and "due" in R["old"] and "due" in R["new"]):
        return
    o, n = R["old"], R["new"]
    T = lambda r, scen, who: r[scen][who]["tile"]
    E = lambda r, scen, who: r[scen][who]["exc"]

    # ---- 1 · the tile, the bank limit not crossed
    om = T(o, "not_due", "maker")[1] or {}
    check("1.1 SHOWN on the old file: reception's login is handed the clinic's whole position -- cash in hand and who holds it, the month to date, drawings, the bank-trip clock, the shouts",
          T(o, "not_due", "maker")[0] == 200 and {"cash_in_hand", "cash_with", "month_to_date", "drawings_month_to_date", "days_since_bank_deposit",
                                                  "shouts", "awaiting_approval", "last_revenue", "noncash_month_to_date"} <= set(om) and len(om) >= 18, sorted(om))
    nm = T(n, "not_due", "maker")
    check("1.2 new: reception gets ok, the unit's name and 'deposit_due: false' -- three fields, no figure at all",
          nm[0] == 200 and nm[1] == {"ok": True, "unit_name": om.get("unit_name"), "deposit_due": False}, nm[1])
    check("1.3 a viewer gets the same three, and is NOT refused (nobody who gets in today is turned away)",
          T(n, "not_due", "viewer")[0] == 200 and T(n, "not_due", "viewer")[1] == nm[1] and T(o, "not_due", "viewer")[0] == 200)
    check("1.4 THE CHECKER'S tile is the old answer, whole", T(n, "not_due", "checker")[1] == T(o, "not_due", "checker")[1]
          and T(n, "not_due", "checker")[0] == 200 and len(T(n, "not_due", "checker")[1]) >= 18)

    # ---- 2 · the tile, the limit crossed
    ck = T(n, "due", "checker")[1] or {}
    dm = T(n, "due", "maker")
    check("2.1 with the limit crossed the checker's tile says deposit_due (and is the old answer, whole)",
          ck.get("deposit_due") is True and ck == T(o, "due", "checker")[1], ck.get("deposit_due"))
    check("2.2 new: reception now gets the banner's three figures too -- cash in hand, the limit, the excess -- and they are the checker's own figures",
          dm[0] == 200 and set(dm[1]) == {"ok", "unit_name", "deposit_due", "cash_in_hand", "deposit_threshold", "deposit_excess"}
          and dm[1]["deposit_due"] is True and all(dm[1][k] == ck[k] for k in ("cash_in_hand", "deposit_threshold", "deposit_excess", "unit_name")), dm[1])
    check("2.3 and still not who holds the cash, the month to date, drawings, the bank-trip clock or the shouts",
          not ({"cash_with", "month_to_date", "drawings_month_to_date", "days_since_bank_deposit", "shouts", "last_revenue", "awaiting_approval"} & set(dm[1])))
    check("2.4 a viewer: the same six", T(n, "due", "viewer")[1] == dm[1])

    # ---- 3 · the exceptions
    oe = (E(o, "due", "maker")[1] or {}).get("exceptions") or []
    ne = (E(n, "due", "maker")[1] or {}).get("exceptions") or []
    ce = (E(n, "due", "checker")[1] or {}).get("exceptions") or []
    kinds = lambda rows: sorted({x["kind"] for x in rows})
    check("3.1 SHOWN on the old file: reception's login is handed every open exception of the clinic -- negative cash, the carry-forward break, the UPI mismatch",
          {"negative_cash", "carry_forward_break", "upi_vs_statement", "missing_day"} <= set(kinds(oe)), kinds(oe))
    check("3.2 new: reception gets the missing-day rows only -- every one of them, and nothing else",
          E(n, "due", "maker")[0] == 200 and kinds(ne) == ["missing_day"] and ne == [x for x in ce if x["kind"] == "missing_day"] and len(ne) >= 2, (kinds(ne), len(ne)))
    check("3.3 THE CHECKER'S list is the old answer, whole; a viewer gets what reception gets",
          E(n, "due", "checker")[1] == E(o, "due", "checker")[1] and len(kinds(ce)) >= 4 and E(n, "due", "viewer")[1] == E(n, "due", "maker")[1])
    check("3.4 no medical row has strayed into the clinic's list", all(x["date"] != "" for x in ce) and len([x for x in ce if x["kind"] == "missing_day" and x["date"] == "2026-09-12"]) == 1)

    # ---- 4 · reception's own page still has everything it reads
    page = open(os.path.join(new, "finance_ui", "finance_entry_clinic.html"), encoding="utf-8").read()
    i = page.index("function loadShouts()")
    body = page[i:page.index("\n}\n", i)]
    tile_part, exc_part = body.split('fetch(API + "/exceptions")')
    reads_tile = set(re.findall(r"\bj\.(\w+)", tile_part))
    reads_exc = set(re.findall(r"\bx\.(\w+)", exc_part))
    check("4.1 read off the page's own code: from the tile it reads ok, deposit_due, cash_in_hand, deposit_threshold, deposit_excess -- every one is in what reception now gets",
          reads_tile == {"ok", "deposit_due", "cash_in_hand", "deposit_threshold", "deposit_excess"} and reads_tile <= set(dm[1])
          and (reads_tile - {"cash_in_hand", "deposit_threshold", "deposit_excess"}) <= set(nm[1]), sorted(reads_tile))
    check("4.2 the three figures are read only inside 'if (j.deposit_due)', so their absence when the limit is not crossed is never read",
          re.search(r"if \(j\.deposit_due\)\{(.*?)\n    \}", tile_part, re.S) is not None
          and all(k in re.search(r"if \(j\.deposit_due\)\{(.*?)\n    \}", tile_part, re.S).group(1) for k in ("j.cash_in_hand", "j.deposit_threshold", "j.deposit_excess"))
          and not re.search(r"j\.(cash_in_hand|deposit_threshold|deposit_excess)", re.sub(r"if \(j\.deposit_due\)\{.*?\n    \}", "", tile_part, flags=re.S)))
    check("4.3 from the exceptions it reads kind and date of the missing-day rows -- both are there",
          reads_exc == {"kind", "date"} and all({"kind", "date"} <= set(x) for x in ne), sorted(reads_exc))

    # ---- 5 · who is outside, and what must not move
    check("5.1 with no login, and with a pharmacy login that has no clinic role: both routes answer exactly what they answered before, in both situations",
          all(r_n[scen][who][k][0] == r_o[scen][who][k][0] and r_n[scen][who][k][2] == r_o[scen][who][k][2]
              for r_n, r_o in ((n, o),) for scen in ("not_due", "due") for who in ("nobody", "pharmacy_only") for k in ("tile", "exc")),
          [(scen, who, n[scen][who]["tile"][0], n[scen][who]["exc"][0]) for scen in ("not_due", "due") for who in ("nobody", "pharmacy_only")])
    check("5.2 the tile's wording (what the portal reads), whoami, the entry page and the clinic's front door are byte for byte the old ones for every login",
          n["same"] == o["same"], [k for k in n["same"] if n["same"][k] != o["same"][k]])
    check("5.3 the pharmacy's own tile and exceptions are untouched", n["medical"] == o["medical"])
    check("5.4 nothing in the finance app's own folder was written by this walk", md5(os.path.join(fin, "finance_app.py")) == FROM)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
