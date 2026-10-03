#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_old_s454p4a.py -- kit S454_BILL_REGISTER part 4A (a copy of part 3's planner): writes the plan walks_old_s454p4a.py runs. It prepares the per-walk scratch folders
(copies of the finance side, the asset app, the portal -- never the live secret or user store -- and the shared library) and databases (backup
API) under --work; nothing outside --work is written.

    plan_old_s454p4a.py --work DIR --fin-new DIR --fin-old DIR --ast DIR --por DIR --shared DIR --kits DIR --db PATH --adb PATH --spine PATH
                       --duty-map-old FILE --duty-map FILE --py PYTHON --out PLAN.json
"""
import argparse
import json
import os
import shutil
import sqlite3

WALKS = (  # name, kit folder, walk file, beside files, argument style
    ("403", "S403_PURCHASE_ORDERS_LIVE", "walk_s403.py", ["seed_s403.py"], "a403"),
    ("407", "S407_NEFT_MESSAGES", "walk_s407.py", ["seed_s407.py"], "app"),
    ("410", "S410_MEDICINE_ORDERING", "walk_s410.py", ["seed_s410.py"], "app"),
    ("414", "S414_RULES_PAGE_UX", "walk_s414.py", [], "app"),
    ("417", "S417_DAY_ONE_FIXES", "walk_s417.py", ["seed_s417.py", "name_search_s417.py"], "app"),
    ("428", "S428_STOCK_WATCH", "walk_s428.py", ["seed_s428.py"], "a428"),
    ("439", "S439_SCANS_SMS_SCROLL", "walk_s439.py", [], "a439"),
    ("440", "S440_SCAN_FLOW", "walk_s440.py", [], "a440"),
    ("441", "S441_SCAN_RATE", "walk_s441.py", [], "a441"),
    ("444", "S444_STAFF_SAFE", "walk_s444.py", [], "a444"),
    ("446", "S446_AMIR_STAGES_BILLS", "walk_s446.py", [], "a446"),
    ("452", "S452_AMIR_PANEL_FIXES", "walk_s452.py", [], "a452"),
)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def copytree(src, dst, skip_config=False):
    os.makedirs(dst, exist_ok=True)
    for n in os.listdir(src):
        p = os.path.join(src, n)
        if skip_config and n == "portal_config.py":
            continue
        if os.path.isfile(p) and (n.endswith(".py") or n.endswith(".js") or n.endswith(".json") or n.endswith(".html")):
            shutil.copy2(p, os.path.join(dst, n))


def stubcfg(d, tag):
    with open(os.path.join(d, "portal_config.py"), "w") as fh:
        fh.write("# S454 earlier walks only -- never the live secret\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = 's454-%s'\n"
                 % (os.urandom(24).hex(), tag))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--work", "--fin-new", "--fin-old", "--ast", "--por", "--shared", "--kits", "--db", "--adb", "--spine", "--duty-map-old", "--duty-map", "--py", "--out"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    O = a.work
    assert O.startswith("/tmp/"), "refusing a non-scratch work folder"
    fin = dict(b=a.fin_old, p=a.fin_new)
    dmap = dict(b=a.duty_map_old, p=a.duty_map)
    plan = []
    for name, kit, wf, beside, style in WALKS:
        src = os.path.join(a.kits, kit, wf)
        side_args, side_env = {}, {}
        for s in "bp":
            w = os.path.join(O, "w%s_%s" % (name, s))
            for sub in ("uploads", "stub", "ast", "ast_old", "por", "por_old", "shared", "up"):
                os.makedirs(os.path.join(w, sub), exist_ok=True)
            db, adb, sp = os.path.join(w, "scratch.db"), os.path.join(w, "assets_scratch.db"), os.path.join(w, "spine_scratch.db")
            copydb(a.db, db)
            copydb(a.adb, adb)
            if style in ("a428", "a439", "a440"):
                copydb(a.spine, sp)
            for d in ("ast", "ast_old"):
                copytree(a.ast, os.path.join(w, d))
            for d in ("por", "por_old"):
                copytree(a.por, os.path.join(w, d), skip_config=True)
                if style in ("a403",):
                    stubcfg(os.path.join(w, d), name)
            copytree(a.shared, os.path.join(w, "shared"))
            env = dict(FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=os.path.join(w, "por"), PETTY_UPLOAD_DIR=os.path.join(w, "uploads"),
                       RECORDS_DRIVE_STUB=os.path.join(w, "stub"), MARG_ARCHIVE="/root/marg_ingest/archive", FINANCE_DB=db, SPINE_DB=sp, ASSETS_DB=adb)
            if style == "app":
                args = ["--app", fin[s], "--old", a.fin_old, "--db", db]
            elif style == "a403":
                args = ["--app", fin[s], "--old", a.fin_old, "--assets-new", os.path.join(w, "ast"), "--assets-old", os.path.join(w, "ast_old"), "--db", db,
                        "--assets-db", adb, "--portal-new", os.path.join(w, "por"), "--portal-old", os.path.join(w, "por_old")]
            elif style == "a428":
                args = ["--app", fin[s], "--old", a.fin_old, "--db", db, "--spine", sp]
            elif style == "a439":
                args = ["--app", fin[s], "--old", a.fin_old, "--db", db, "--assets-db", adb, "--kit", os.path.join(a.kits, kit)]   # read only: it runs its replay from there
            elif style == "a440":
                args = ["--app", fin[s], "--old", a.fin_old, "--assets-new", os.path.join(w, "ast"), "--assets-old", os.path.join(w, "ast_old"), "--db", db, "--assets-db", adb]
            elif style == "a441":
                args = ["--new-fin", fin[s], "--old-fin", a.fin_old, "--new-ast", os.path.join(w, "ast"), "--old-ast", os.path.join(w, "ast_old"), "--shared",
                        os.path.join(w, "shared"), "--portal", os.path.join(w, "por"), "--db", db, "--adb", adb, "--uploads", os.path.join(w, "up")]
                env = {}
            elif style == "a444":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por-new", os.path.join(w, "por"), "--por-old", os.path.join(w, "por_old"), "--ast",
                        os.path.join(w, "ast"), "--shared", os.path.join(w, "shared"), "--db", db, "--adb", adb, "--kit", os.path.join(a.kits, kit), "--duty-map", dmap[s]]
                env = {}
            elif style == "a446":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por", os.path.join(w, "por"), "--ast", os.path.join(w, "ast"), "--shared", os.path.join(w, "shared"),
                        "--db", db, "--adb", adb, "--kit", os.path.join(a.kits, kit), "--duty-map", dmap[s]]
                env = {}
            else:                                              # a452
                copydb(a.spine, sp)
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por", os.path.join(w, "por"), "--ast", os.path.join(w, "ast"), "--shared", os.path.join(w, "shared"),
                        "--db", db, "--adb", adb, "--kit", os.path.join(a.kits, kit), "--duty-map", dmap[s], "--uploads", "/root/assetapp/uploads", "--spine", sp]
                env = {}
            side_args["baseline" if s == "b" else "patched"] = args
            side_env["baseline" if s == "b" else "patched"] = env
        plan.append(dict(name=name, src=src, work=os.path.join(O, "work%s" % name), beside=[os.path.join(a.kits, kit, x) for x in beside], py=a.py, fin=dict(baseline=a.fin_old, patched=a.fin_new),
                         args=side_args, env=side_env, db=dict(baseline=os.path.join(O, "w%s_b" % name, "scratch.db"), patched=os.path.join(O, "w%s_p" % name, "scratch.db"))))
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=1)
    print("plan: %d walks -> %s" % (len(plan), a.out))


if __name__ == "__main__":
    main()
