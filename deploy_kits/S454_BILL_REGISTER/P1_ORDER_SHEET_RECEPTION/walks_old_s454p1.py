#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walks_old_s454p1.py -- kit S454_BILL_REGISTER part 1: the earlier walks that touch what S454 changes, re-run on the patched files.

  S403 (the orthotic order screen), S407 (the NEFT messages and the phone's queue), S410 (the ordering day), S414 (the rules page), S417 (the
  stock beside an order), S428 (the stock watch), S439 (the matcher), S440 (Scan ka kaam), S441 (the scan checks), S444 (the staff-eye walk),
  S446 (Amir's stages) and S452 (Amir's panel).

Each walk is COPIED to scratch (the kit folders are never edited) and run twice: UNADJUSTED on the box as it is (the baseline) and ADJUSTED on
the box + S454. Every adjustment is an anchored replacement on the copy (anchor exactly once, else STOP), or a data step on that run's own scratch
copy, named below with its reason. The gate: on the patched files a walk is green, or every one of its reds is in its ACCEPT list AND red in the
baseline too (a fact of today's data, or a control that no longer exists -- never something S454 moved).

    walks_old_s454p1.py --plan PLAN.json
"""
import json
import os
import re
import sqlite3
import subprocess
import sys

R = "S454-ADJUSTED"
# P0 (every walk, the patched run): "?old=1 and porders.simple=0 serve today's page, and S440's and S410's walks pass on it" (the brief, 4.9).
# The earlier walks read the old Purchase-orders page and its API; on their own scratch copy the setting reads 0. The new screen is S454's own walk's.
PRE_SQL = ("INSERT INTO setting (key, value, note) VALUES ('porders.simple', '0', 'S454 walk: the earlier walks read the old page') "
           "ON CONFLICT(key) DO UPDATE SET value='0'")
# P2 (every walk, the patched run): the S454 tables exist on the scratch copy, as the install's first load leaves them on the box (the duty
# map's v4 queries read them).
P2_PY = ("import sys, sqlite3; sys.path.insert(0, sys.argv[1]); import order_sheet; c = sqlite3.connect(sys.argv[2]); order_sheet.ensure(c); c.close(); "
         "print('S454 tables made')")
PRE = {}  # name -> [(code, why, sql)] -- more data on the patched run's own scratch copy
NO_P0 = ("walk_s444.py",)      # its staff-eye walk reads the duty map v4, whose doors are the new screen's: the new screen it must see
BOTH = {  # file -> [(code, why, old, new)] -- on BOTH runs: the box moved on since that kit (never something S454 changes)
    "seed_s403.py": [("B1", "S441 (01-Oct) put the shared reception login on the porders unit: the seed's own list of roles carries it, on both runs",
                      'ROLES = [("darpan", "maker"), ("shavez", "maker"), ("shivani", "maker"), ("alisha", "maker"), ("manoj", "checker")]',
                      'ROLES = [("darpan", "maker"), ("shavez", "maker"), ("shivani", "maker"), ("alisha", "maker"), ("manoj", "checker"), ("reception", "maker")]   # S454-ADJUSTED B1')],
    "walk_s403.py": [("B2", "S441 (01-Oct): the asset app now names who scanned (g.user['username']); the walk's stand-in reception user carries a username, "
                            "on both runs",
                      'ar.g.user = {"display_name": "walk-reception", "role": "reception"}',
                      'ar.g.user = {"display_name": "walk-reception", "role": "reception", "username": "walk-reception"}   # S454-ADJUSTED B2')],
}
ADJ = {                        # name -> [(code, why, old, new)] -- the patched run only
    "walk_s410.py": [("P3", "order.source = system on its scratch copy, after the walk clears the order.* settings: S410's ordering day (its 09:00 notice, its "
                            "proposals, 'Order not sent', Darpan's count line) is what S454 keeps for the system's own list; Darpan's sheet (the default) is "
                            "S454's own walk's",
                      'db.execute("DELETE FROM setting WHERE key LIKE \'order.%\' OR key=\'porders.rules_approved\'")\n',
                      'db.execute("DELETE FROM setting WHERE key LIKE \'order.%\' OR key=\'porders.rules_approved\'")\n'
                      'db.execute("INSERT INTO setting (key, value, note) VALUES (\'order.source\', \'system\', \'S454-ADJUSTED P3\')")   # S454-ADJUSTED P3\n'),
                     ("P4", "S454 (D666): the 12:00 reminder goes -- the forced 12:00 tick says nothing",
                      r'''check("12:00 before any send: 'Aaj N order: 0 bheja, N baaki — …' naming W410 Weekly;''',
                      r'''check("S454-ADJUSTED P4: 12:00 says nothing (S454: the 12:00 reminder goes);'''),
                     ("P4", "(the same)",
                      r'''re.match(r"^Aaj (\d+) order: 0 bheja, \1 baaki — ", N["remind12"] or "") and "W410 Weekly" in N["remind12"] and ''',
                      r'''N["remind12"] is None and '''),
                     ("P5", "S454 (D666): the 15:00 reminder goes -- the forced 15:00 tick says nothing; Darpan's count line is checked as it was",
                      r'''check("15:00 reads 'Aaj N order: 1 bheja, N-1 baaki — …' without W410 Weekly;''',
                      r'''check("S454-ADJUSTED P5: 15:00 says nothing (S454: the 15:00 reminder goes);'''),
                     ("P5", "(the same)",
                      r'''re.match(r"^Aaj (\d+) order: 1 bheja, \d+ baaki — ", N["remind15"] or "") and "W410 Weekly" not in N["remind15"]''',
                      r'''N["remind15"] is None'''),
                     ("P6", "S454 (D666): ONE reminder at 17:00, 'Order baaki: <the suppliers still to be ordered>' (notice slot R1700); the pushes are "
                            "09:00's and 17:00's, four senders each (8, not 16)",
                      r'''check("17:00 with Fort Co still unsent speaks ('3 bheja', W410 Fort named, W410 Weekly not): '%s'; the notice log holds 0900/1200/1500/1700 once each;''',
                      r'''check("S454-ADJUSTED P6: 17:00 with Fort Co still unsent speaks ('Order baaki: ...', W410 Fort named, W410 Weekly not): '%s'; the notice log holds 0900 and S454's one reminder R1700;'''),
                     ("P6", "(the same)",
                      r'''"3 bheja" in (N["remind17"][0] or "") and "W410 Fort" in N["remind17"][0] and "W410 Weekly" not in N["remind17"][0] and [x["slot"] for x in N["notices"]] == ["0900", "1200", "1500", "1700"] and N["pushes"][0] == 16''',
                      r'''(N["remind17"][0] or "").startswith("Order baaki: ") and "W410 FORT" in N["remind17"][0].upper() and "W410 WEEKLY" not in N["remind17"][0].upper() and [x["slot"] for x in N["notices"]] == ["0900", "R1700"] and N["pushes"][0] == 8'''),
                     ("P7", "S454 (D666): the repeat is of the 17:00 slot (the only one left), its row is R1700; once every proposal is sent the reminder "
                            "names none of them -- silent, or only S403's orthotic card (S454 names that card on both settings: four more pushes)",
                      r'''os.environ["ORDER_TICK"] = "remind12"; out["already12"]''',
                      r'''os.environ["ORDER_TICK"] = "remind17"; out["already12"]'''),
                     ("P7", "(the same)",
                      r'''db.execute("DELETE FROM order_notice WHERE day=? AND slot='1700'", (T.isoformat(),))''',
                      r'''db.execute("DELETE FROM order_notice WHERE day=? AND slot='R1700'", (T.isoformat(),))'''),
                     ("P7", "(the same)",
                      r'''out["silent17"] = [s17.get("silent"), len(q("SELECT id FROM order_notice WHERE day=? AND slot='1700'", T.isoformat())), len([1 for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()])]''',
                      r'''out["silent17"] = [bool(s17.get("silent")) or not [v for v in (s17.get("text") or "")[len("Order baaki: "):].split(", ") if v in {r["vendor"] for r in q("SELECT vendor FROM order_proposal WHERE day=?", T.isoformat())}], len(q("SELECT id FROM order_notice WHERE day=? AND slot='R1700' AND text LIKE '%W410%'", T.isoformat())), len([1 for x in open(os.environ["ORDER_PUSH_STUB"], encoding="utf-8") if x.strip()]), bool(s17.get("silent")), s17.get("text")]   # S454-ADJUSTED P7'''),
                     ("P7", "(the same)",
                      r'''check("once every proposal of the day is sent the reminder is SILENT (no notice row, no push); a repeat of a slot already sent answers already", N["silent17"] == [True, 0, 16] and N["already12"] is True''',
                      r'''check("S454-ADJUSTED P7: once every proposal of the day is sent the 17:00 reminder names none of them -- silent, or only S403's orthotic card (S454 names it on both settings); a repeat of the 17:00 slot answers already", N["silent17"][:2] == [True, 0] and N["silent17"][2] == (8 if N["silent17"][3] else 12) and N["already12"] is True''')],
    "walk_s444.py": [("P8", "S444's bar check reads the old page's s440bar; with S454 /finance/porders is the one-task screen -- the old page stays at ?old=1 "
                            "and is checked there, word for word; the new screen is checked beside it: 'Signed in: alisha' on its home, '← BACK' once",
                      '''    s, hp, _l = FG("alisha", "/finance/porders")\n''',
                      '''    s, hp, _l = FG("alisha", "/finance/porders?old=1")   # S454-ADJUSTED P8\n'''
                      '''    _sn, _hn, _ln = FG("alisha", "/finance/porders")\n'''
                      '''    out["porders_new"] = dict(status=_sn, signed="Signed in: alisha" in _hn, backs=_hn.count("← BACK"))\n'''),
                     ("P8", "(the same)",
                      '''    check("Purchase orders: 'Signed in: alisha' inside the BACK bar; the bar once, '← BACK' once", P["status"] == 200 and P["signed_in_bar"] and P["bars"] == 1 and P["backs"] == 1, P)\n''',
                      '''    check("Purchase orders: 'Signed in: alisha' inside the BACK bar; the bar once, '← BACK' once", P["status"] == 200 and P["signed_in_bar"] and P["bars"] == 1 and P["backs"] == 1, P)\n'''
                      '''    check("S454-ADJUSTED P8: the new Purchase-orders screen (S454): 'Signed in: alisha' on its home, '← BACK' once", '''
                      '''N["porders_new"]["status"] == 200 and N["porders_new"]["signed"] and N["porders_new"]["backs"] == 1, N["porders_new"])\n''')],
}
ACCEPT_WHY = {                 # a patched red is accepted only when it is red, word for word, on the box as it is too -- and its walk is named here
    "walk_s403.py": "the walk's own control (the box before S403) is gone: --old is the box as it is, so its NEGATIVE checks are red on both runs; the "
                    "rest are today's data and the kits since (S410's ordering day, S440's scan flow, S441's reception login)",
    "walk_s407.py": "S452 (F-687) moved the setup page to the owner and a checker and renewed the key; the 18 live August NEFT messages queued since 26-Sep "
                    "answer the queue door first; the control (the box before S407) is gone",
    "walk_s410.py": "today's data (the Sarvam trial's owner line; September's real first-ever items carry no manufacturer in the item master); the "
                    "control (the box before S410) is gone",
    "walk_s414.py": "the control (the box before S414) is gone",
    "walk_s417.py": "the control (the box before S417) is gone; the card statements are read and placed on the live shelf since 26-Sep",
    "walk_s428.py": "today's data (the S427 ground moved with the first count's vouchers, a real arrival in the roster's window, October's leakage); the "
                    "control (the box before S428) is gone",
    "walk_s439.py": "the kits since S439 (S440's approve(), the matcher's own S440 decisions); the control (the box before S439) is gone",
    "walk_s440.py": "today's data (the real scans of 02/03-Oct in the groups; the intake's month line); the control (the box before S440) is gone",
    "walk_s441.py": "today's data (the real scans since 01-Oct in the S440 groups); the control (the box before S441) is gone",
    "walk_s444.py": "the kits since S444 (S446's stages, S452's Roman Hindi and 12 vouchers a visit, the claim settled by S444's own rule); the control "
                    "(the box before S444) is gone",
    "walk_s446.py": "S452's rulings (12 vouchers a visit, held scans, Amir's NEFT) and today's real scans; the control (the box before S446) is gone",
    "walk_s452.py": "today's real scans (B-0103..B-0113 of 03-Oct) on the list; the control (the box before S452) is gone",
}


def adjust(name, src, patched):
    for code, _why, old, new in BOTH.get(name, []):
        n = src.count(old)
        if n != 1:
            raise SystemExit("STOP: %s -- adjustment %s anchor occurs %d times" % (name, code, n))
        src = src.replace(old, new, 1)
    if patched:
        for code, _why, old, new in ADJ.get(name, []):
            n = src.count(old)
            if n != 1:
                raise SystemExit("STOP: %s -- adjustment %s anchor occurs %d times" % (name, code, n))
            src = src.replace(old, new, 1)
    return src


def fails(out):
    return [l.strip()[5:].strip() for l in out.splitlines() if re.match(r"^\s*FAIL\s", l)]


def main():
    plan = json.load(open(sys.argv[sys.argv.index("--plan") + 1], encoding="utf-8"))
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    red = []
    print("-- the adjustments (each made on a scratch COPY or on that run's own scratch database; the kit folders are never edited):")
    print("   P0   every walk but S444  porders.simple = 0 on the patched run's scratch copy: the earlier walks read the old page (the brief, 4.9); S444's "
          "staff-eye walk reads the duty map v4, whose doors are the new screen's")
    print("   P2   every walk     the S454 tables made on the patched run's scratch copy, as the install's first load leaves them (the duty map v4 reads them)")
    for name, items in PRE.items():
        for code, why, _sql in items:
            print("   %-4s %-14s %s" % (code, name, why))
    for name, items in list(BOTH.items()) + list(ADJ.items()):
        for code, why, _o, _n in items:
            print("   %-4s %-14s %s" % (code, name, why))
    for w in plan:
        if only and w["name"] not in only:
            continue
        name = os.path.basename(w["src"])
        src = open(w["src"], encoding="utf-8").read()
        res = {}
        for side in ("baseline", "patched"):
            d = os.path.join(w["work"], side)
            os.makedirs(d, exist_ok=True)
            for extra in w.get("beside") or []:
                bs = open(extra, encoding="utf-8").read()
                with open(os.path.join(d, os.path.basename(extra)), "w", encoding="utf-8") as gh:
                    gh.write(adjust(os.path.basename(extra), bs, False))
            if side == "patched":
                c = sqlite3.connect(w["db"][side])
                c.execute("CREATE TABLE IF NOT EXISTS setting (key TEXT PRIMARY KEY, value TEXT, note TEXT)")
                if name not in NO_P0:
                    c.execute(PRE_SQL)
                for _code, _why, sql in PRE.get(name, []):
                    c.execute(sql)
                c.commit()
                c.close()
                q2 = subprocess.run([w.get("py") or sys.executable, "-B", "-c", P2_PY, w["fin"][side], w["db"][side]], stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, timeout=300)
                if "S454 tables made" not in q2.stdout:
                    raise SystemExit("STOP: P2 failed on %s: %s" % (name, q2.stdout[-300:]))
            f = os.path.join(d, name)
            open(f, "w", encoding="utf-8").write(adjust(name, src, side == "patched"))
            env = dict(os.environ, **w["env"][side])
            for k in ("ORDER_TICK", "ORDER_TODAY", "SARVAM_API_KEY"):
                env.pop(k, None)
            p = subprocess.run([w.get("py") or sys.executable, "-B", f] + w["args"][side], cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=3600)
            tally = [l for l in p.stdout.splitlines() if re.match(r"^WALK(_\w+)? (GREEN|RED|OK)", l)]
            res[side] = dict(fails=fails(p.stdout), tally=(tally[-1] if tally else "NO TALLY (exit %s)" % p.returncode), tail=p.stdout.splitlines()[-15:])
            print("   %-9s %-15s %s" % (side, name, res[side]["tally"][:200]))
            for x in res[side]["fails"]:
                print("               red: %s" % re.sub(r"\d{10,}", "##########", x)[:700])
        why = ACCEPT_WHY.get(name)
        bad = []
        for x in res["patched"]["fails"]:
            ok = bool(why) and any(b[:60] == x[:60] for b in res["baseline"]["fails"])
            if not ok:
                bad.append(x)
        if "NO TALLY" in res["patched"]["tally"]:
            bad.append(res["patched"]["tally"])
            print("\n".join("      " + re.sub(r"\d{10,}", "##########", l) for l in res["patched"]["tail"]))
        if bad:
            red.append(name)
            print("   !! %s: red on the patched files beyond the accepted: %s" % (name, " | ".join(re.sub(r"\d{10,}", "##########", b)[:160] for b in bad)))
        elif res["patched"]["fails"]:
            print("   %s: %d red(s), each red word for word on the box as it is too -- %s" % (name, len(res["patched"]["fails"]), why))
    if red:
        print("WALKS_OLD_S454P1 RED -- %s" % ", ".join(red))
        return 1
    print("WALKS_OLD_S454P1 GREEN -- S403's, S407's, S410's, S414's, S417's, S428's, S439's, S440's, S441's, S444's, S446's and S452's walks: green on the "
          "patched files but for the named reds, each red on the box as it is too")
    return 0


if __name__ == "__main__":
    sys.exit(main())
