#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_old_s444.py -- kit S444_STAFF_SAFE: the earlier walks of the files S444 changes, re-run on the patched files.

  * Amir's day: S246's three walks (S246 / S245 / S244), S243's visit walk, S241's two selftests -- each COPIED to a scratch
    folder beside the amir_day.py (and amir_salts.py) under test; the kit folders are never edited.
  * S440's walk (Purchase orders, the asset app) on the box's finance files + S444's, against the S440 backups as its control.

A walk older than the file it tests asserts facts later kits moved. Each such assertion is adjusted on the COPY by an anchored
replacement (the anchor exactly once, else STOP), named below with the kit that moved the fact. Every walk runs twice: UNADJUSTED
on the box as it is (the baseline -- which assertions were already red before S444), and ADJUSTED on the patched files (green).

    walk_old_s444.py --live FIN_COPY --new FIN_COPY_WITH_S444 --kits DEPLOY_KITS --work DIR [--s440 ...see the installer]
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

R = "S444-ADJUSTED"
ADJ = {
    "S246_AMIR_LIST_REOPEN/walk_amir_reopen_s246.py": [
        ("A1", "G2: S285 added 'supplier', S444 adds 'self' -- seven answers",
         '[c for c, _l in amir_day.REASONS] == ["ok", "short", "nodeal", "discount", "other"])',
         '[c for c, _l in amir_day.REASONS] == ["ok", "self", "short", "nodeal", "discount", "supplier", "other"])   # ' + R + ' A1')],
    "S246_AMIR_LIST_REOPEN/walk_amir_billtap_s245.py": [
        ("A2", "A8: one radio per answer per bill -- 4 bills x the answers there are now (seven)",
         'len(k["r"]) == 20 and', 'len(k["r"]) == 4 * len(amir_day.REASONS) and   # ' + R + ' A2\n     '),
        ("A3", "F2: as A1",
         '[c for c, _l in amir_day.REASONS] == ["ok", "short", "nodeal", "discount", "other"])',
         '[c for c, _l in amir_day.REASONS] == ["ok", "self", "short", "nodeal", "discount", "supplier", "other"])   # ' + R + ' A3')],
    "S246_AMIR_LIST_REOPEN/walk_amir_processing_s244.py": [],
    "S243_AMIR_VISIT/walk_amir_visit_s243.py": [
        ("A4", "healthz: S246 renamed the module's healthz kit to S246_AMIR_LIST_REOPEN (red before S444)",
         'j.get("kit") == "S243_AMIR_VISIT", j)', 'j.get("kit") in ("S243_AMIR_VISIT", "S246_AMIR_LIST_REOPEN"), j)   # ' + R + ' A4'),
        ("A5", "step 4: S244 added the 'Jaanch poori ho gayi' tick, a third check mark on the page (red before S444)",
         'h.count("&#10003;") == 2 and', 'h.count("&#10003;") >= 2 and   # ' + R + ' A5\n   '),
        ("A6", "the salt list in _left(): S444 (brief 3.4) names it there as words -- never a gate; the gate steps are asserted instead",
         'and not any("SALT" in i for i in AD._left(w)), (w["done"], AD._left(w)))',
         'and AD.GATE_STEPS == (2, 4, 5, 6) and any("SALT" in i for i in AD._left(w)), (w["done"], AD._left(w)))   # ' + R + ' A6'),
        ("A7", "the hub: S368 moved the loader's call into loadMargFold() (red before S444)",
         '"loadAmirVisit(); loadHomeMed();" in h)', '"loadAmirVisit();" in h)   # ' + R + ' A7')],
    "S241_AMIR_SALTS/selftest_amir_day.py": [],
    "S241_AMIR_SALTS/selftest_amir_salts.py": [],
}
# S241's selftest of amir_day asserts the S241 DESIGN of step 4 and step 5, which S244 (processing / wait) and S245 (one tap, no
# 'required') replaced -- their own walks carry those facts (S244 62/62, S245 53/53, both re-run above). These eight are red on the
# box as it is; the gate for this one walk is: the SAME eight on the patched files, and no other.
ACCEPT = {"S241_AMIR_SALTS/selftest_amir_day.py": [
    ("both reports reported missing", "S244: after the export tap the pair is 'ban rahi hai' (in transit), not missing"),
    ("it says dobara banaiye", "S244: 'dobara banaiye' only once the grace window has run out"),
    ("it names the open Excel", "S244: the open-Excel note rides with 'dobara banaiye'"),
    ("one verified, one not", "S244: the other report shows as in transit, not as a cross"),
    ("wrong period named, not just missing", "S244: a wrong-period file older than the export tap waits out the grace window"),
    ("both verified", "S244: a third check mark ('Jaanch poori ho gayi')"),
    ("verified pair leads to the bills", "S244: the jump from step 4"),
    ("the choice is forced on every option of every bill", "S245: 'required' removed on purpose (a required radio in a closed <details> blocks the submit)")]}


def adjust(src, items, path):
    for code, why, old, new in items:
        n = src.count(old)
        if n != 1:
            raise SystemExit("STOP: %s -- adjustment %s anchor occurs %d times" % (path, code, n))
        src = src.replace(old, new, 1)
    return src


def tally(out):
    for pat in (r"== (\d+) checks, (\d+) ok, (\d+) failed", r"walk: (\d+) passed, (\d+) failed", r"(\d+) ok, (\d+) failed"):
        m = re.findall(pat, out)
        if m:
            g = m[-1]
            if len(g) == 3:
                return int(g[1]), int(g[2])
            return int(g[0]), int(g[1])
    return None


def fails(out):
    return [l.strip() for l in out.splitlines() if re.match(r"\s*(FAILED:|FAIL\b|  FAIL)", l)][:8]


def run(cmd, cwd, env=None):
    p = subprocess.run(cmd, cwd=cwd, env=env or dict(os.environ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=900)
    return p.returncode, p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--kits", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--adj", default="", help="extra adjustments file (python dict ADJ_EXTRA)")
    a = ap.parse_args()
    extra = {}
    if a.adj:
        ns = {}
        exec(open(a.adj, encoding="utf-8").read(), ns)
        extra = ns.get("ADJ_EXTRA", {})
    allg = dict(ADJ)
    for k, v in extra.items():
        allg[k] = allg.get(k, []) + v
    py = sys.executable
    red = []
    print("-- the adjustments (each made on a scratch COPY of the frozen walk; the kit folders are never edited):")
    for k, items in sorted(allg.items()):
        for code, why, _o, _n in items:
            print("   %s  %s -- %s" % (code, k, why))
    for side, src in (("baseline", a.live), ("patched", a.new)):
        adjusted = side == "patched"
        print("-- %s: %s" % ("UNADJUSTED walks on the box as it is" if not adjusted else "ADJUSTED walks on the box + S444", src))
        # S246's three walks: argv names the amir_day.py
        d = os.path.join(a.work, side, "s246")
        os.makedirs(d, exist_ok=True)
        shutil.copyfile(os.path.join(src, "amir_day.py"), os.path.join(d, "amir_day.py"))
        for rel in ("S246_AMIR_LIST_REOPEN/walk_amir_reopen_s246.py", "S246_AMIR_LIST_REOPEN/walk_amir_billtap_s245.py", "S246_AMIR_LIST_REOPEN/walk_amir_processing_s244.py"):
            s = open(os.path.join(a.kits, rel), encoding="utf-8").read()
            if adjusted:
                s = adjust(s, allg.get(rel, []), rel)
            w = os.path.join(d, os.path.basename(rel))
            open(w, "w", encoding="utf-8").write(s)
            rc, out = run([py, "-B", w, os.path.join(d, "amir_day.py")], d)
            t = tally(out)
            print("   %-48s %s%s" % (rel, ("%d ok, %d failed" % t) if t else "NO TALLY (exit %d)" % rc, ("  " + " | ".join(fails(out))) if (t and t[1]) or not t else ""))
            if adjusted and (not t or t[1] or rc != 0):
                red.append(rel)
                if not t:
                    print("\n".join("      " + l for l in out.splitlines()[-12:]))
        # S243's visit walk and S241's selftests load amir_day.py from their OWN folder: the kit folder is copied to scratch
        for kit, cmds in (("S243_AMIR_VISIT", [["walk_amir_visit_s243.py"]]), ("S241_AMIR_SALTS", [["selftest_amir_day.py"], ["selftest_amir_salts.py"]])):
            d = os.path.join(a.work, side, kit)
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(os.path.join(a.kits, kit), d)
            for f in ("amir_day.py", "amir_salts.py", "padreader.py", "padwriter.py"):
                if os.path.exists(os.path.join(src, f)) and (f.startswith("amir") or not os.path.exists(os.path.join(d, f))):
                    shutil.copyfile(os.path.join(src, f), os.path.join(d, f))
            for c in cmds:
                rel = "%s/%s" % (kit, c[0])
                w = os.path.join(d, c[0])
                if adjusted:
                    s = adjust(open(w, encoding="utf-8").read(), allg.get(rel, []), rel)
                    open(w, "w", encoding="utf-8").write(s)
                env = dict(os.environ, FIN_APP=os.path.join(src, "finance_app.py"), FIN_MODS=src, SIBLINGS=a.kits)
                rc, out = run([py, "-B", w], d, env)
                t = tally(out)
                print("   %-48s %s%s" % (rel, ("%d ok, %d failed" % t) if t else "NO TALLY (exit %d)" % rc, ("  " + " | ".join(fails(out))) if (t and t[1]) or not t else ""))
                if adjusted and (not t or t[1]):
                    acc = ACCEPT.get(rel)
                    bad = [l for l in out.splitlines() if re.match(r"^\s*FAIL\s", l)]
                    if acc and t and t[1] == len(acc) and len(bad) == len(acc) and all(any(x in l for x, _w in acc) for l in bad):
                        print("      the same %d as on the box as it is, and no other -- each superseded by a later kit:" % len(acc))
                        for x, why in acc:
                            print("        - %s -- %s" % (x, why))
                        continue
                    red.append(rel)
                    if not t:
                        print("\n".join("      " + l for l in out.splitlines()[-12:]))
    for root, dirs, _f in os.walk(a.work):
        for x in list(dirs):
            if x == "__pycache__":
                shutil.rmtree(os.path.join(root, x), ignore_errors=True)
    if red:
        print("WALK_OLD_S444 RED -- %s" % ", ".join(red))
        return 1
    print("WALK_OLD_S444 GREEN -- S246 / S245 / S244, S243 and S241's walks on the patched files, the adjustments named above")
    return 0


if __name__ == "__main__":
    sys.exit(main())
