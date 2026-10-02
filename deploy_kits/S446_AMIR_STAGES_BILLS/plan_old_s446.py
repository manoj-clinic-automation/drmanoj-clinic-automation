#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_old_s446.py -- kit S446_AMIR_STAGES_BILLS: writes the plan walks_old_s446.py runs (the installer prepares the folders and
scratch copies named here; this only names them).

    plan_old_s446.py --work DIR --fin-new DIR --fin-old DIR --kits DIR --por DIR --mrg DIR --duty-map FILE --out PLAN.json

  in --work: old437/ old436/ old444/ (each the box as it is with that kit's .bak files put back -- that kit's own control),
             s437_{b,p}.db s436_{b,p}.db sp437_{b,p}.db sp436_{b,p}.db s444_{b,p}.db a444_{b,p}.db (scratch copies, one per run),
             p444_{b,p}/por_new por_old ast shared, uploads/ stub/ work/
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    for k in ("--work", "--fin-new", "--fin-old", "--kits", "--por", "--mrg", "--duty-map", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    O, R = a.work, a.kits
    seeds = [R + "/S437_COUNT_PAGES_FINAL/seed_s437.py", R + "/S436_STAFF_PAGES_CLEAN/seed_s436.py"]

    def wenv(db, sp):
        return dict(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, PETTY_UPLOAD_DIR=O + "/uploads", RECORDS_DRIVE_STUB=O + "/stub",
                    MARG_ARCHIVE=a.mrg + "/archive", FINANCE_DB=db, SPINE_DB=sp)
    plan = []
    for name, src, old in (("437", R + "/S437_COUNT_PAGES_FINAL/walk_s437.py", "old437"),
                           ("436", R + "/S437_COUNT_PAGES_FINAL/walk_s436_s437.py", "old436")):
        def args(s, app):
            return ["--app", app, "--old", O + "/" + old, "--db", "%s/s%s_%s.db" % (O, name, s), "--spine", "%s/sp%s_%s.db" % (O, name, s)]
        plan.append(dict(src=src, work=O + "/work/" + name, beside=seeds,
                         args=dict(baseline=args("b", a.fin_old), patched=args("p", a.fin_new)),
                         env=dict(baseline=wenv("%s/s%s_b.db" % (O, name), "%s/sp%s_b.db" % (O, name)),
                                  patched=wenv("%s/s%s_p.db" % (O, name), "%s/sp%s_p.db" % (O, name)))))

    def a444(s, fin):
        P = "%s/p444_%s" % (O, s)
        return ["--fin-new", fin, "--fin-old", O + "/old444", "--por-new", P + "/por_new", "--por-old", P + "/por_old", "--ast", P + "/ast",
                "--shared", P + "/shared", "--db", "%s/s444_%s.db" % (O, s), "--adb", "%s/a444_%s.db" % (O, s), "--kit", R + "/S444_STAFF_SAFE",
                "--duty-map", a.duty_map]
    plan.append(dict(src=R + "/S444_STAFF_SAFE/walk_s444.py", work=O + "/work/444", beside=[],
                     args=dict(baseline=a444("b", a.fin_old), patched=a444("p", a.fin_new)), env=dict(baseline={}, patched={})))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1)
    print("plan: %d walks -> %s" % (len(plan), a.out))


if __name__ == "__main__":
    main()
