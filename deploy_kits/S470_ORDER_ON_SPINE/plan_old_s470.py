#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plan_old_s470.py -- kit S470_ORDER_ON_SPINE (S454 part 4A's planner, with S454's own walks added): writes the plan walks_old_s470.py runs. It prepares the per-walk scratch folders
(copies of the finance side, the asset app, the portal -- never the live secret or user store -- and the shared library) and databases (backup
API) under --work; nothing outside --work is written.

    plan_old_s470.py --work DIR --fin-new DIR --fin-old DIR --ast DIR --por DIR --shared DIR --kits DIR --db PATH --adb PATH --spine PATH
                  --duty-map-old FILE --duty-map FILE --py PYTHON --out PLAN.json [--marg DIR]
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
    # S454's own walks (S470's brief, walk step 11): the parts that touch what S470 changes. Not run: P1 (its walk no longer runs on the box
    # as it is -- part 1C changed the printed sheet's layout its probe reads, KeyError 'old' -- and P1C's walk, which is run, took its place);
    # P1B (it needs the owner's real order sheet, which is not in the repository); P4A and P4C (the medical PC's refusal note: marg_door and
    # the watcher, nothing S470 touches).
    ("454p1c", "S454_BILL_REGISTER/P1C_SHEET_PAGE_AND_PHONE", "walk_s454p1c.py", [], "p1c"),
    ("454p1d", "S454_BILL_REGISTER/P1D_TICK_GUARD", "walk_s454p1d.py", [], "p1d"),
    ("454p2", "S454_BILL_REGISTER/P2_PAIRING_REGISTER", "walk_s454p2.py", [], "p2"),
    ("454p3", "S454_BILL_REGISTER/P3_SHELF_FIGURE", "walk_s454p3.py", [], "p3"),
    ("454p3b", "S454_BILL_REGISTER/P3B_FIRST_DAY", "walk_s454p3b.py", [], "p3"),
    ("454p5", "S454_BILL_REGISTER/P5_ITEMS", "walk_s454p5.py", [], "p3"),
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
    ap.add_argument("--marg", default="/root/marg_ingest")
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
            if style in ("a428", "a439", "a440", "p1", "p3"):
                copydb(a.spine, sp)
            for d in ("ast", "ast_old"):
                copytree(a.ast, os.path.join(w, d))
            for d in ("por", "por_old"):
                copytree(a.por, os.path.join(w, d), skip_config=True)
                if style in ("a403",):
                    stubcfg(os.path.join(w, d), name)
                if style in ("p1", "p1c", "p2", "p3") and os.path.exists(os.path.join(a.por, "tile_grants.json")):
                    shutil.copy2(os.path.join(a.por, "tile_grants.json"), os.path.join(w, d, "tile_grants.json"))
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
            elif style == "p1":                                # S454 part 1: the sheet's road needs a copy of the marg_ingest side
                for sub in ("marg_new", "marg_old"):
                    copytree(a.marg, os.path.join(w, sub))
                kd = os.path.join(a.kits, kit)
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--marg-new", os.path.join(w, "marg_new"), "--marg-old", os.path.join(w, "marg_old"), "--por",
                        os.path.join(w, "por"), "--ast", os.path.join(w, "ast"), "--shared", os.path.join(w, "shared"), "--db", db, "--adb", adb, "--spine", sp, "--kit", kd,
                        "--duty-map", dmap[s], "--uploads", "/root/assetapp/uploads", "--reader-new", os.path.join(kd, "medical", "marg_txt.py"), "--reader-old",
                        os.path.join(a.kits, "S446_AMIR_STAGES_BILLS", "medical", "marg_txt.py")]
                env = {}
            elif style == "p1c":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por", os.path.join(w, "por"), "--db", db, "--adb", adb, "--work", os.path.join(w, "wk"),
                        "--data-mod", os.path.join(a.kits, kit, "data_s454p1c.py")]
                env = {}
            elif style == "p1d":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--db", db, "--work", os.path.join(w, "wk")]
                env = {}
            elif style == "p2":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por", os.path.join(w, "por"), "--db", db, "--adb", adb, "--work", os.path.join(w, "wk"),
                        "--duty-map-new", dmap[s], "--duty-map-old", dmap[s]]
                env = {}
            elif style == "p3":
                args = ["--fin-new", fin[s], "--fin-old", a.fin_old, "--por", os.path.join(w, "por"), "--db", db, "--adb", adb, "--spine", sp, "--work",
                        os.path.join(w, "wk"), "--duty-map", dmap[s]]
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
