#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_old_s452.py -- kit S452_AMIR_PANEL_FIXES: writes the plan walks_old_s452.py runs (the installer prepares the folders and scratch
copies named here; this only names them).

    plan_old_s452.py --work DIR --fin-new DIR --fin-old DIR --kits DIR --kit DIR --por DIR --mrg DIR --duty-map-old FILE --duty-map FILE
                     --py PYTHON --out PLAN.json

  in --work: old446/ old444/ (the box as it is with that kit's .bak files put back -- that kit's own control);
             p446_{b,p}/{por,ast,shared} p444_{b,p}/{por_new,por_old,ast,shared} p408/ k434_{b,p}/ w434_{b,p}/ r408_{b,p}/;
             s446_{b,p}.db a446_{b,p}.db s444_{b,p}.db a444_{b,p}.db s407_{b,p}.db s434_{b,p}.db r408_{b,p}/scratch.db r408_{b,p}/assets.db;
             uploads/ stub/ work/
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    for k in ("--work", "--fin-new", "--fin-old", "--kits", "--kit", "--por", "--mrg", "--duty-map-old", "--duty-map", "--py", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    O, R = a.work, a.kits
    fin = dict(b=a.fin_old, p=a.fin_new)
    dmap = dict(b=a.duty_map_old, p=a.duty_map)

    def wenv(db):
        return dict(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=a.por, PETTY_UPLOAD_DIR=O + "/uploads", RECORDS_DRIVE_STUB=O + "/stub",
                    MARG_ARCHIVE=a.mrg + "/archive", FINANCE_DB=db)
    plan = []
    # S446's walk: its own control is the box before S446 (old446); the patched copy carries S452's setting (12 a visit), as the install will
    a446 = {s: ["--fin-new", fin[s], "--fin-old", O + "/old446", "--por", "%s/p446_%s/por" % (O, s), "--ast", "%s/p446_%s/ast" % (O, s),
                "--shared", "%s/p446_%s/shared" % (O, s), "--db", "%s/s446_%s.db" % (O, s), "--adb", "%s/a446_%s.db" % (O, s),
                "--kit", R + "/S446_AMIR_STAGES_BILLS", "--duty-map", dmap[s]] for s in "bp"}
    plan.append(dict(src=R + "/S446_AMIR_STAGES_BILLS/walk_s446.py", work=O + "/work/446", beside=[], py=a.py,
                     args=dict(baseline=a446["b"], patched=a446["p"]), env=dict(baseline={}, patched={}),
                     pre=dict(patched=[[a.py, "-B", a.kit + "/apply_s452.py", "--finance", a.fin_new, "--db", "%s/s446_p.db" % O, "--settings-only"]])))
    # S444's walk: its own control is the box before S444 (old444); the patched copy carries S452's data step's settings, as the install will
    a444 = {s: ["--fin-new", fin[s], "--fin-old", O + "/old444", "--por-new", "%s/p444_%s/por_new" % (O, s), "--por-old", "%s/p444_%s/por_old" % (O, s),
                "--ast", "%s/p444_%s/ast" % (O, s), "--shared", "%s/p444_%s/shared" % (O, s), "--db", "%s/s444_%s.db" % (O, s),
                "--adb", "%s/a444_%s.db" % (O, s), "--kit", R + "/S444_STAFF_SAFE", "--duty-map", dmap[s]] for s in "bp"}
    plan.append(dict(src=R + "/S444_STAFF_SAFE/walk_s444.py", work=O + "/work/444", beside=[], py=a.py,
                     args=dict(baseline=a444["b"], patched=a444["p"]), env=dict(baseline={}, patched={}),
                     pre=dict(patched=[[a.py, "-B", a.kit + "/apply_s452.py", "--finance", a.fin_new, "--db", "%s/s444_p.db" % O, "--settings-only"]])))
    # S407's walk: the NEFT card and the phone's setup page (its control, the box before S407, no longer exists: the box as it is)
    a407 = {s: ["--app", fin[s], "--old", a.fin_old, "--db", "%s/s407_%s.db" % (O, s)] for s in "bp"}
    plan.append(dict(src=R + "/S407_NEFT_MESSAGES/walk_s407.py", work=O + "/work/407", beside=[R + "/S407_NEFT_MESSAGES/seed_s407.py"], py=a.py,
                     args=dict(baseline=a407["b"], patched=a407["p"]),
                     env=dict(baseline=wenv("%s/s407_b.db" % O), patched=wenv("%s/s407_p.db" % O))))
    # S408's walk: Amir's pack route (its control, the box before S408, no longer exists: the box as it is)
    a408 = {s: ["--app", fin[s], "--old", a.fin_old, "--db", "%s/r408_%s/scratch.db" % (O, s), "--assets-db", "%s/r408_%s/assets.db" % (O, s),
                "--portal-new", O + "/p408", "--portal-old", O + "/p408"] for s in "bp"}
    plan.append(dict(src=R + "/S408_MONTH_END_PACKS/walk_s408.py", work=O + "/work/408", beside=[R + "/S408_MONTH_END_PACKS/seed_s408.py"], py=a.py,
                     args=dict(baseline=a408["b"], patched=a408["p"]),
                     env=dict(baseline=wenv("%s/r408_b/scratch.db" % O), patched=wenv("%s/r408_p/scratch.db" % O))))
    # S434's walk: packs.py on a copy of the live database (k434_b = the box's packs.py, k434_p = S452's)
    a434 = {s: ["%s/k434_%s" % (O, s), "%s/w434_%s" % (O, s), "%s/s434_%s.db" % (O, s), fin[s]] for s in "bp"}
    plan.append(dict(src=R + "/S434_PACKS_FIXES/walk_s434.py", work=O + "/work/434", beside=[], py=a.py,
                     args=dict(baseline=a434["b"], patched=a434["p"]), env=dict(baseline={}, patched={})))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1)
    print("plan: %d walks -> %s" % (len(plan), a.out))


if __name__ == "__main__":
    main()
