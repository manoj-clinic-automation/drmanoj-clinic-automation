#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""patch_ca_and_numbers_s243.py -- S243_CA_AND_NUMBERS: two owner rulings of 13-Sep-2026.

FOUR live files, patched ON THE BOX (none of them is in the repository), every
anchor asserted to occur EXACTLY ONCE in the live bytes -- else REFUSED and
nothing is written. Never writes the live file: writes <file>.new.

Anchors were proven count==1 on the 13-Sep capture (finance_app f002defb, hub
cc349dd0, returns_desk.py dface15b, returns_desk.html 77e754e9) AND on the bytes
left by the sibling kits S243_SCREEN_FIXES -> S243_DARPAN_KAL (finance_app
f93f7430, hub 7dbb5e56), so this kit installs before or after them.

RULING A -- the chartered accountant: no cash/UPI correction in Marg any more.
  finance_app.py  (fa)
     M  mount accountant_upi_cash (guarded, before the __main__ block)
     H  health: the "Correction checklist" ✗/⚠ work item becomes an ⓘ line
        "Cash → UPI reclassifications: N bill(s) this month ... (accountant report)"
     U  health: "Cash / UPI split" is information, not a fault
     L  HEALTH_LINKS: both rows open the accountant report, not the worklist
     S  the app's own selftest follows (two lines), so it stays green
  finance_ui/finance_approvals.html  (hub)
     C  the "Cash ⇄ UPI Reclassified bills" card links the monthly report
     N  the tab strip gains "Accountant ↗" beside "Corrections ↗"

RULING B -- full phone numbers on the returns desk.
  returns_desk.py  (rd)
     Q  /api/search returns the full number from patient_ref.mobile where the
        column exists and is filled (the nightly patient sync writes it), else
        the last four; five or more typed digits search the full number.
  returns_desk.html  (rdh)
     P  the picker shows the full number where present, ***last4 otherwise
     K  the chosen patient's line carries the number

    FA_PATH=... HUB_PATH=... RD_PATH=... RDH_PATH=... python3 -B patch_ca_and_numbers_s243.py [fa|hub|rd|rdh|all]
    --selftest <finance_app.py> <finance_approvals.html> <returns_desk.py> <returns_desk.html>

Prints md5 before and after. ALREADY PATCHED -> exit 0 for that file.
"""
import hashlib
import io
import os
import sys

FA_TARGET = os.environ.get("FA_PATH", "/root/finance/finance_app.py")
HUB_TARGET = os.environ.get("HUB_PATH", "/root/finance/finance_ui/finance_approvals.html")
RD_TARGET = os.environ.get("RD_PATH", "/root/finance/returns_desk.py")
RDH_TARGET = os.environ.get("RDH_PATH", "/root/finance/returns_desk.html")
FA_MARK = "S243_CA_AND_NUMBERS begin"
HUB_MARK = "S243 ca accountant report"
RD_MARK = "S243_CA_AND_NUMBERS: full number"
RDH_MARK = "S243 full number"

# ---------------------------------------------------------------- finance_app.py
M_OLD = '\n\nif __name__ == "__main__":\n'
M_NEW = (
    "\n\n# --- S243_CA_AND_NUMBERS begin -- the monthly accountant report: UPI booked as cash (CA ruling 13-Sep) ---\n"
    "# No cash/UPI correction is made in Marg any more; the record (upi_match / mode_change_log /\n"
    "# marg_correction) is an English monthly page, a print view and a .xlsx for the accountant.\n"
    "# GUARDED (S209): a fault inside the module is printed and every other page keeps serving.\n"
    "try:\n"
    "    import accountant_upi_cash                                 # noqa: E402\n"
    "    accountant_upi_cash.init(app, db, require, unit=UNIT, login=PORTAL_LOGIN)\n"
    "except Exception as _ex_acu:                                   # noqa: BLE001\n"
    "    print(\"accountant_upi_cash NOT mounted: %s\" % _ex_acu, file=sys.stderr)\n"
    "# --- S243_CA_AND_NUMBERS end ---\n"
    "\n\nif __name__ == \"__main__\":\n")

H_OLD = (
    "        # A3+++: the disagreements as WORK -- who has it, when it is due.\n"
    "        try:\n"
    "            _cr = _correction_rows(con, 90)\n"
    "            if _cr:\n"
    "                _od = [r for r in _cr if r[\"due\"] and r[\"due\"] < today.isoformat()]\n"
    "                _cnt = {}\n"
    "                for r in _cr:\n"
    "                    _cnt[r[\"status\"]] = _cnt.get(r[\"status\"], 0) + 1\n"
    "                _lbl = {\"open\": \"not started\", \"sent\": \"with Amir\",\n"
    "                       \"corrected\": \"corrected, awaiting re-export\"}\n"
    "                add(\"corrlist\", \"Correction checklist\",\n"
    "                    \"bad\" if _od else \"warn\",\n"
    "                    \"%d day(s) to fix — %s%s\"\n"
    "                    % (len(_cr),\n"
    "                       \" · \".join(\"%d %s\" % (v, _lbl.get(k, k))\n"
    "                                  for k, v in sorted(_cnt.items())),\n"
    "                       (\" · %d OVERDUE\" % len(_od)) if _od else \"\"),\n"
    "                    \"<a href='/finance/marg-worklist'>Open the checklist</a> — it \"\n"
    "                    \"ticks itself off when a corrected day is re-exported and applied.\")\n"
    "        except Exception:\n"
    "            pass\n")
H_NEW = (
    "        # S243_CA_AND_NUMBERS -- the chartered accountant's ruling (13-Sep-2026): no cash/UPI\n"
    "        # correction is made in Marg any more (a corrected bill re-opens a closed sale to\n"
    "        # unauthorised edits). The record is kept and goes into the MONTHLY accountant pack --\n"
    "        # so this row is INFORMATION, never work, and the S195 checklist is no longer synced here.\n"
    "        try:\n"
    "            _ym0 = today.strftime(\"%Y-%m\")\n"
    "            _rc = con.execute(\"SELECT COUNT(*) n, COALESCE(SUM(txn_amount_p),0) p FROM upi_match \"\n"
    "                              \"WHERE unit=? AND status='cash' AND substr(business_date,1,7)=?\",\n"
    "                              (UNIT, _ym0)).fetchone()\n"
    "            add(\"corrlist\", \"Cash → UPI reclassifications\", \"info\",\n"
    "                \"%d bill(s) this month, %s — the bank proves UPI, Marg rang cash\"\n"
    "                % (int(_rc[\"n\"] or 0), rupees(int(_rc[\"p\"] or 0))),\n"
    "                \"Kept for the accountant report (no Marg correction — the CA's ruling, \"\n"
    "                \"13-Sep-2026). Open the month's report.\")\n"
    "        except Exception:\n"
    "            pass\n")

U_OLD = '            add("upisplit", "Cash / UPI split", "bad",\n'
U_NEW = '            add("upisplit", "Cash / UPI split", "info",     # S243_CA_AND_NUMBERS: recorded, not corrected in Marg\n'

L_OLD = (
    '        "upisplit": ("/finance/marg-worklist",\n'
    '                     "Open the correction checklist and fix the cash/UPI split "\n'
    '                     "for the listed days."),\n'
    '        "corrlist": ("/finance/marg-worklist",\n'
    '                     "Work through the open corrections &mdash; the list closes "\n'
    '                     "itself as days are fixed."),\n')
L_NEW = (
    '        # S243_CA_AND_NUMBERS: both rows open the monthly accountant report -- nothing is\n'
    '        # corrected in Marg any more (the CA\'s ruling, 13-Sep-2026).\n'
    '        "upisplit": ("/finance/accountant/upi-cash",\n'
    '                     "Open the accountant report &mdash; the month\'s cash/UPI record; "\n'
    '                     "no Marg correction."),\n'
    '        "corrlist": ("/finance/accountant/upi-cash",\n'
    '                     "Open the accountant report &mdash; the bills the bank proves were UPI; "\n'
    '                     "no Marg correction."),\n')

S1_OLD = '             "upisplit": "/finance/marg-worklist", "corrlist": "/finance/marg-worklist",\n'
S1_NEW = '             "upisplit": "/finance/accountant/upi-cash", "corrlist": "/finance/accountant/upi-cash",\n'
S2_OLD = '          (not _hcl) or ("Open the checklist" in _ht))\n'
S2_NEW = '          (not _hcl) or ("accountant report" in _ht))   # S243_CA_AND_NUMBERS wording\n'

# ---------------------------------------------------------------- the hub
C_OLD = ('<div class="card" id="reclassCard"><h2><span class="kick">Cash ⇄ UPI</span>Reclassified bills</h2>\n'
         '  <div id="reclass">loading&hellip;</div>\n')
C_NEW = ('<div class="card" id="reclassCard"><h2><span class="kick">Cash ⇄ UPI</span>Reclassified bills</h2>\n'
         '  <div class="note" style="margin:0 0 8px"><!-- ' + HUB_MARK + ' -->'
         'Since the CA\'s ruling of 13-Sep-2026 nothing is corrected in Marg: the month\'s record goes to the '
         '<a href="/finance/accountant/upi-cash">accountant report — UPI booked as cash ↗</a> '
         '(English, print view, .xlsx).</div>\n'
         '  <div id="reclass">loading&hellip;</div>\n')
N_OLD = '    <a class="ext" href="/finance/darpan/corrections">Corrections ↗</a>\n'
N_NEW = ('    <a class="ext" href="/finance/darpan/corrections">Corrections ↗</a>\n'
         '    <a class="ext" href="/finance/accountant/upi-cash">Accountant ↗</a>\n')

# ---------------------------------------------------------------- returns_desk.py
Q_OLD = (
    '@bp.route("/api/search")\n'
    'def api_search():\n'
    '    _u, err = _auth()\n'
    '    if err:\n'
    '        return err\n'
    '    q = (request.args.get("q") or "").strip()\n'
    '    if len(q) < 2:\n'
    '        return jsonify(ok=True, patients=[])\n'
    '    con = _con()\n'
    '    digits = re.sub(r"\\D", "", q)\n'
    '    rows = []\n'
    '    if digits and 2 <= len(digits) <= 4:\n'
    '        rows = con.execute(\n'
    '            "SELECT id, clinic_id, name, phone_last4 FROM patient_ref "\n'
    '            "WHERE merged_into IS NULL AND phone_last4 LIKE ? LIMIT 25",\n'
    '            ("%" + digits,)).fetchall()\n'
    '    if not rows:\n'
    '        rows = con.execute(\n'
    '            "SELECT id, clinic_id, name, phone_last4 FROM patient_ref "\n'
    '            "WHERE merged_into IS NULL AND (name LIKE ? OR clinic_id LIKE ?) "\n'
    '            "ORDER BY name LIMIT 25", ("%" + q + "%", "%" + q + "%")).fetchall()\n'
    '    return jsonify(ok=True, patients=[\n'
    '        dict(id=r["id"], clinic_id=r["clinic_id"], name=r["name"],\n'
    '             last4=r["phone_last4"]) for r in rows])\n')
Q_NEW = (
    '@bp.route("/api/search")\n'
    'def api_search():\n'
    '    # S243_CA_AND_NUMBERS: full number (owner ruling 13-Sep-2026, "full phone numbers\n'
    '    # everywhere, including the returns desk"). patient_ref.mobile is written by the\n'
    '    # nightly patient sync (finance_patient_sync.py, the 31-Aug ruling); where it is\n'
    '    # filled the desk shows and searches the whole number, where it is not the last\n'
    '    # four stand exactly as before. Read at request time; nothing is stored here.\n'
    '    _u, err = _auth()\n'
    '    if err:\n'
    '        return err\n'
    '    q = (request.args.get("q") or "").strip()\n'
    '    if len(q) < 2:\n'
    '        return jsonify(ok=True, patients=[])\n'
    '    con = _con()\n'
    '    digits = re.sub(r"\\D", "", q)\n'
    '    has_mobile = False\n'
    '    try:\n'
    '        has_mobile = any(str(c[1]).lower() == "mobile"\n'
    '                         for c in con.execute("PRAGMA table_info(patient_ref)").fetchall())\n'
    '    except Exception:\n'
    '        has_mobile = False\n'
    '    mob_col = "mobile" if has_mobile else "NULL AS mobile"\n'
    '    rows = []\n'
    '    if digits and len(digits) >= 5 and has_mobile:\n'
    '        rows = con.execute(\n'
    '            "SELECT id, clinic_id, name, phone_last4, mobile FROM patient_ref "\n'
    '            "WHERE merged_into IS NULL AND mobile LIKE ? ORDER BY name LIMIT 25",\n'
    '            ("%" + digits + "%",)).fetchall()\n'
    '    if not rows and digits and 2 <= len(digits) <= 4:\n'
    '        rows = con.execute(\n'
    '            "SELECT id, clinic_id, name, phone_last4, " + mob_col + " FROM patient_ref "\n'
    '            "WHERE merged_into IS NULL AND phone_last4 LIKE ? LIMIT 25",\n'
    '            ("%" + digits,)).fetchall()\n'
    '    if not rows:\n'
    '        rows = con.execute(\n'
    '            "SELECT id, clinic_id, name, phone_last4, " + mob_col + " FROM patient_ref "\n'
    '            "WHERE merged_into IS NULL AND (name LIKE ? OR clinic_id LIKE ?) "\n'
    '            "ORDER BY name LIMIT 25", ("%" + q + "%", "%" + q + "%")).fetchall()\n'
    '    return jsonify(ok=True, patients=[\n'
    '        dict(id=r["id"], clinic_id=r["clinic_id"], name=r["name"],\n'
    '             last4=r["phone_last4"],\n'
    '             mobile=(str(r["mobile"]).strip() if r["mobile"] else "")) for r in rows])\n')

# ---------------------------------------------------------------- returns_desk.html
P_OLD = """    +'<span class="sub">'+(p.clinic_id||'')+(p.last4?(' · ***'+p.last4):'')+'</span></span>'\n"""
P_NEW = """    +'<span class="sub">'+(p.clinic_id||'')+(p.mobile?(' · '+p.mobile):(p.last4?(' · ***'+p.last4):''))+'</span></span>' /* S243 full number */\n"""
K_OLD = " $('pname2').textContent=patient.name||'';\n"
K_NEW = " $('pname2').textContent=(patient.name||'')+(patient.mobile?(' · '+patient.mobile):(patient.last4?(' · ***'+patient.last4):'')); /* S243 full number */\n"


def md5(b):
    return hashlib.md5(b).hexdigest()


def _apply(src, mark, pairs, extra_refuse=None):
    if mark in src:
        return src, "already"
    for nm, old, _new in pairs:
        n = src.count(old)
        if n != 1:
            return src, "refused: anchor %s occurs %d times (need exactly 1)" % (nm, n)
    if extra_refuse:
        why = extra_refuse(src)
        if why:
            return src, "refused: " + why
    out = src
    for _nm, old, new in pairs:
        out = out.replace(old, new, 1)
    return out, "patched"


def patch_fa(src):
    return _apply(src, FA_MARK,
                  (("M", M_OLD, M_NEW), ("H", H_OLD, H_NEW), ("U", U_OLD, U_NEW),
                   ("L", L_OLD, L_NEW), ("S1", S1_OLD, S1_NEW), ("S2", S2_OLD, S2_NEW)),
                  lambda s: ("accountant_upi_cash is already imported without the mark"
                             if "import accountant_upi_cash" in s else None))


def patch_hub(src):
    return _apply(src, HUB_MARK, (("C", C_OLD, C_NEW), ("N", N_OLD, N_NEW)))


def patch_rd(src):
    return _apply(src, RD_MARK, (("Q", Q_OLD, Q_NEW),))


def patch_rdh(src):
    return _apply(src, RDH_MARK, (("P", P_OLD, P_NEW), ("K", K_OLD, K_NEW)))


FILES = {"fa": (FA_TARGET, patch_fa, FA_MARK), "hub": (HUB_TARGET, patch_hub, HUB_MARK),
         "rd": (RD_TARGET, patch_rd, RD_MARK), "rdh": (RDH_TARGET, patch_rdh, RDH_MARK)}


def selftest(paths):
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        if cond:
            ok += 1
            print("  PASS ", name)
        else:
            bad += 1
            print("  FAIL ", name)

    def kind_of(p):
        b = os.path.basename(p)
        if b.endswith(".py") and "returns_desk" in b:
            return "rd"
        if b.endswith(".html") and "returns_desk" in b:
            return "rdh"
        if b.endswith(".py"):
            return "fa"
        return "hub"

    for p in paths:
        k = kind_of(p)
        _t, fn, mark = FILES[k]
        s = io.open(p, encoding="utf-8").read()
        out, st = fn(s)
        check("%s [%s]: patches (%s)" % (os.path.basename(p), k, st), st == "patched")
        if st != "patched":
            continue
        if k in ("fa", "rd"):
            try:
                compile(out, p, "exec")
                check("  compiles", True)
            except SyntaxError as ex:
                check("  compiles (%s)" % ex, False)
        check("  mark present" + (" (on both edited lines)" if k == "rdh" else " once"),
              out.count(mark) == (2 if k == "rdh" else 1))
        check("  second run is a no-op", fn(out)[1] == "already")
        if k == "fa":
            check("  mount lands once, before __main__",
                  out.count("accountant_upi_cash.init(app, db, require, unit=UNIT, login=PORTAL_LOGIN)") == 1
                  and out.find("S243_CA_AND_NUMBERS begin") < out.find('if __name__ == "__main__":'))
            check("  the work item is gone: no 'Correction checklist' label, no _correction_rows in health",
                  '"Correction checklist"' not in out
                  and out.count("_correction_rows(con, 90)") == s.count("_correction_rows(con, 90)") - 1)
            check("  the info line and the new links are in",
                  out.count('add("corrlist", "Cash → UPI reclassifications", "info",') == 1
                  and out.count('"/finance/accountant/upi-cash"') == 4
                  and '"/finance/marg-worklist",\n                     "Open the correction checklist' not in out)
            check("  the worklist routes and the S195 checklist API survive untouched",
                  out.count('@app.route("/finance/marg-worklist")') == 1
                  and out.count('@app.route("/finance/api/marg-corrections")') == 1
                  and out.count("def _correction_sync(") == 1)
            check("  every other original line still present",
                  all(ln in out for ln in s.splitlines() if ln.strip() and ln not in H_OLD
                      and ln not in U_OLD and ln not in L_OLD and ln not in S1_OLD and ln not in S2_OLD))
        if k == "hub":
            check("  card link and tab once; DARPAN_KAL's anchors untouched",
                  out.count('href="/finance/accountant/upi-cash"') == 2
                  and out.count('id="reclassCard"') == 1 and out.count("function loadReclass()") == 1
                  and out.count('<!-- S194 ⭐2 -->\n<div class="card" id="homeMedCard">') == 1
                  and out.count("loadHomeMed(); loadReclass(); loadMPR(); loadReview(); loadStaffCards();") == 1)
            check("  only additions: every original line still present",
                  all(ln in out for ln in s.splitlines() if ln.strip()))
        if k == "rd":
            check("  the search still answers last4 and name, and now the full number",
                  out.count('phone_last4 LIKE ?') == 1 and out.count("mobile LIKE ?") == 1
                  and out.count('@bp.route("/api/search")') == 1 and "mobile=(str(r[\"mobile\"])" in out)
            check("  nothing stores a number: no INSERT/UPDATE added",
                  out.count("INSERT INTO") == s.count("INSERT INTO") and out.count("UPDATE ") == s.count("UPDATE "))
        if k == "rdh":
            check("  picker and chosen line show full where present else ***last4",
                  out.count("p.mobile?(' · '+p.mobile)") == 1 and out.count("patient.mobile?(' · '+patient.mobile)") == 1
                  and out.count("***'+p.last4") == 1)
    check("a stranger .py is refused", patch_fa("x = 1\n")[1].startswith("refused"))
    check("a stranger page is refused", patch_hub("<html></html>\n")[1].startswith("refused"))
    check("a stranger desk is refused", patch_rd("x = 1\n")[1].startswith("refused") and patch_rdh("<html>")[1].startswith("refused"))
    print("selftest: %d passed, %d failed" % (ok, bad))
    return 0 if bad == 0 else 1


def run_one(which):
    target, fn, _mark = FILES[which]
    raw = io.open(target, "rb").read()
    src = raw.decode("utf-8")
    print("source %s md5 %s" % (target, md5(raw)))
    new, st = fn(src)
    if st == "already":
        print("ALREADY PATCHED (%s) -- nothing to do" % which)
        return 0
    if st != "patched":
        print("REFUSED (%s): %s -- nothing written" % (which, st[len("refused: "):]))
        return 2
    if target.endswith(".py"):
        compile(new, target, "exec")
    io.open(target + ".new", "w", encoding="utf-8", newline="\n").write(new)
    print("wrote %s.new md5 %s" % (target, md5(new.encode("utf-8"))))
    return 0


def main(argv):
    if argv and argv[0] == "--selftest":
        return selftest(argv[1:])
    which = argv[0] if argv else "all"
    todo = ("fa", "hub", "rd", "rdh") if which == "all" else (which,)
    rc = 0
    for w in todo:
        if w not in FILES:
            print("unknown target %s (fa|hub|rd|rdh|all)" % w)
            return 2
        rc = max(rc, run_one(w))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
