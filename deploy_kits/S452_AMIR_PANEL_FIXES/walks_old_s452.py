#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walks_old_s452.py -- kit S452_AMIR_PANEL_FIXES: the earlier walks that touch what S452 changes, re-run on the patched files.

  S446's walk (Amir's stages, packs, the bill list), S444's walk (his day, the staff-eye walk), S407's walk (the NEFT card, the phone's
  setup page), S408's walk (Amir's pack route) and S434's walk (packs.py, the parent's file S452 edits once).

Each walk is COPIED to scratch (the kit folders are never edited) and run twice: UNADJUSTED on the box as it is (the baseline -- what was
already red before S452) and ADJUSTED on the box + S452. Every adjustment is an anchored replacement on the copy (anchor exactly once,
else STOP), named below with its reason. S446's own adjustments of S444's walk (B1-B3) ride BOTH runs: the box is S446 now. The gate: on
the patched files a walk is green, or every one of its reds is in its ACCEPT list AND red in the baseline too (a fact of today's data or
of a control that no longer exists, never something S452 moved).

    walks_old_s452.py --plan PLAN.json       (plan_old_s452.py writes it: each walk's file, its arguments and env for both runs)
"""
import json
import os
import re
import subprocess
import sys

R = "S452-ADJUSTED"
S446B = "S446-ADJUSTED"
BOTH = {                       # S446's adjustments of S444's walk -- the box is S446 now, so both runs carry them (copied from walks_old_s446)
    "walk_s444.py": [
        ("B1", 'card=[int(m.group(1)), int(m.group(2))] if m else None,', 'card=[int(m.group(1)), int(m.group(2) or 0)] if m else None,   # ' + S446B + ' B1\n                       '),
        ("B1b", 'm = re.search(r"Stock voucher baaki: (\\d+) orthotic, (\\d+) dawa", h)\n        steps[n]',
         'm = re.search(r"(?:Stock|Orthotic) voucher baaki: (\\d+)(?: orthotic, (\\d+) dawa)?", h)   # ' + S446B + ' B1\n        steps[n]'),
        ("B1c", 'm = re.search(r"Stock voucher baaki: (\\d+) orthotic, (\\d+) dawa", h1)\n    out["card_after"] = [int(m.group(1)), int(m.group(2))] if m else None',
         'm = re.search(r"(?:Stock|Orthotic) voucher baaki: (\\d+)(?: orthotic, (\\d+) dawa)?", h1)   # ' + S446B + ' B1\n    out["card_after"] = [int(m.group(1)), int(m.group(2) or 0)] if m else None'),
        ("B1d", 'card = [exp["ortho"], exp["dawa"]] if exp else None', 'card = [exp["ortho"], 0] if exp else None   # ' + S446B + ' B1'),
        ("B2", '        stock_app._proof_state = lambda con, d: {"state": "done"}       # walk only: the crafted green proof\n',
         '        stock_app._proof_state = lambda con, d: {"state": "done"}       # walk only: the crafted green proof\n'
         '        real_s446 = getattr(stock_app, "_s446_proof", None)          # ' + S446B + ' B2\n'
         '        stock_app._s446_proof = lambda con, root, keys, ent, batches: {"state": "done", "rows": []}\n'),
        ("B2b", '        stock_app._proof_state = real_ps\n',
         '        stock_app._proof_state = real_ps\n        if real_s446:\n            stock_app._s446_proof = real_s446   # ' + S446B + ' B2\n'),
        ("B3", 'len(nv) == 1 and ("(orthotic %d)" % card[0]) in nv[0]', 'len(nv) == 1 and ("(Stage A, orthotic): %d" % card[0]) in nv[0]   # ' + S446B + ' B3\n          ')],
    "walk_s408.py": [          # S446 (F-673) replaced S408's foot card: the month's pack rides in his card by state, and leaves it once "Dekh liya"
        ("A1", '"Pichle mahine ka pack" in str(am[1])', '"Mahine ka pack &mdash; August 2026" in str(am[1])'),
        ("A2", 'out["amir_card2"] = "dekh liya" in str(am2[1])', 'out["amir_card2"] = "Mahine ka pack &mdash; August 2026" not in str(am2[1])')],
}
ADJ = {                        # S452's own adjustments -- the patched run only
    "walk_s446.py": [
        ("C1", "Stage C is 12 a visit (amir.vouchers_per_visit, set to 12 by S452's data step on this scratch copy): the first lot is 12 (baaki 18)",
         '("Dawa voucher: aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 5)) in cc',
         '("Dawa voucher: aaj ke 12 (baaki %d)" % (len(W["key_items"]) - no - 12)) in cc   # ' + R + ' C1\n          '),
        ("C2", "as C1: the board lists those 12, numbered 1..12",
         'cb["n"] == 5 and cb["seq"] == [1, 2, 3, 4, 5]', 'cb["n"] == 12 and cb["seq"] == list(range(1, 13))   # ' + R + ' C2\n          '),
        ("C3", "as C1: a verified lot releases the next 12 -- the card counts what is open on his board (12, baaki 6)",
         '("aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 10)) in N["c_after_verified"] and N["c_board2"]["n"] == 5',
         '("aaj ke 12 (baaki %d)" % (len(W["key_items"]) - no - 24)) in N["c_after_verified"] and N["c_board2"]["n"] == 12   # ' + R + ' C3\n          '),
        ("C4", "the next visit opens the next lot, proved or not (S452: 1 visit, was 2); the unverified lot stays listed -- the card counts both "
               "lots open (12 + the last 6 = 18, baaki 0), the board lists 18",
         '("aaj ke 5 (baaki %d)" % (len(W["key_items"]) - no - 15)) in N["c_after_visits"] and N["c_board3"]["n"] == 10',
         '("aaj ke %d (baaki 0)" % (len(W["key_items"]) - no - 12)) in N["c_after_visits"] and N["c_board3"]["n"] == len(W["key_items"]) - no - 12   # ' + R + ' C4\n          '),
        ("F1", "S452 (F-686) holds a scan the matcher calls a second scan: the crafted W446-01 read 'W446A', whose digits (446) and supplier are those of "
               "the crafted bill W446B already linked to W446-02 -- held, rightly. Its number is crafted as 'W9446A' so it stays a bill Marg does not have",
         'bill_no="W446A", bill_date=TODAY.isoformat(), total_amount=500.0', 'bill_no="W9446A", bill_date=TODAY.isoformat(), total_amount=500.0'),
        ("F2", "as F1, the expected file name",
         'want_name = "%s_W446A_%s.pdf"', 'want_name = "%s_W9446A_%s.pdf"'),
        ("F3", "S452 (F-686): every file name now starts with the scan's stamp -- the zip's name is matched by its end, as the download's already is",
         'want_name in (N["f_zip"][1] or [])', 'any(x.endswith(want_name) for x in (N["f_zip"][1] or []))')],
    "walk_s407.py": [
        ("P1", "S452 (F-687): the setup page is the owner's and a checker's; the key shows on every open (shown-once retired) -- the two opens are the "
               "owner's, and Shavez's refusal is asserted by S452's own walk",
         'sp1 = G("shavez", "/finance/purchase/page/phone-setup"); sp2 = G("shavez", "/finance/purchase/page/phone-setup")',
         'sp1 = G("manoj", "/finance/purchase/page/phone-setup"); sp2 = G("manoj", "/finance/purchase/page/phone-setup")'),
        ("P1b", "as P1: the second open shows the key again, no 'ek baar dikha diya'",
         'N["setup"][3] is False and N["setup"][4] is True', 'N["setup"][3] is True and N["setup"][4] is False   # ' + R + ' P1\n          '),
        ("P2", "S452 (F-687): Shavez's pay page no longer links the setup page he cannot open (the owner's still does)",
         'N["page_shavez"] == [True, False, True, []]', 'N["page_shavez"] == [True, False, False, []]   # ' + R + ' P2\n          '),
        ("P3", "S452 (the owner, 02-Oct): Amir sees one NEFT line per confirmed month and no supplier list -- 'bata diya' is gone from his page",
         'N["amir"] == [200, True, True, True, True, []]', 'N["amir"] == [200, True, True, False, True, []]   # ' + R + ' P3\n          ')],
}
ACCEPT = {
    "walk_s444.py": [("NEGATIVE: KEDAR 195's claim stays open on the box as it is", "today's data: S444's own rule settled claim #1 on the live database at its install (01-Oct 22:09)"),
                     ("his board: BACK goes to /finance/amir", "today's data: Amir's board was opened as amir on 02-Oct 19:47:10 and 19:47:45 (the chat's live walk), so "
                                                              "stock_board_open already holds two rows before the walk's own"),
                     ("the owner's line (d) after 2 of his visits without the board", "today's data: as above -- his last look at the board is today, so no "
                                                                                     "two visits have passed without it")],
    "walk_s407.py": [("NEGATIVE:", "the control S407 compared with -- the box BEFORE S407 -- no longer exists: both runs use the box as it is, which carries S407"),
                     ("next with the token returns the oldest queued row", "today's data: the 18 live August messages (queued 26-Sep) are older than the walk's crafted one"),
                     ("done {ok:false} -> failed", "today's data: as above, the live queue's oldest row answers first"),
                     ("after 30 minutes next offers it again", "today's data: as above"),
                     ("30 minutes later it is 'Pending", "today's data: the 18 live August messages, queued since 26-Sep, make the Needs-you count 19, not 1"),
                     ("Bhejo: bhati refused", "today's data: as above -- the 18 live messages keep the Needs-you line on after the walk's one is sent")],
    "walk_s408.py": [("NEGATIVE:", "the control S408 compared with -- the box BEFORE S408 -- no longer exists: both runs use the box as it is"),
                     ("tile_grants.json is v29", "the portal moved on since S408 (v32 today)"),
                     ("the Yes Bank current statement -> Sanjeevni's slot", "today's data: the live shelf has held the branch's real statements since 26-Sep; the walk's fixture files meet them"),
                     ("the ICICI reader read the fixture", "today's data: as above -- the August period is already read from the real statement"),
                     ("the Yes Bank fixture is placed but its READ is refused", "today's data: as above"),
                     ("the August cells:", "today's data: the real August statements are read and placed"),
                     ("electricity:", "today's data: the real August statements carry the electricity lines the fixture expected to supply"),
                     ("the lab bundle:", "today's data: the live asset store's August bills meet the fixture's"),
                     ("a repeat within 10 minutes is not sent again", "today's data: the real August pack is larger, so the split runs to more parts than the fixture's")],
    "walk_s434.py": [],
    "walk_s446.py": [],
}


def adjust(name, src, patched):
    for code, old, new in (BOTH.get(name, [])):
        n = src.count(old)
        if n != 1:
            raise SystemExit("STOP: %s -- adjustment %s (S446's) anchor occurs %d times" % (name, code, n))
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
    red = []
    print("-- the adjustments (each made on a scratch COPY; the kit folders are never edited):")
    print("   B1-B3 walk_s444.py   S446's own adjustments (its walks_old_s446), on BOTH runs: the box is S446 now")
    print("   A1-A2 walk_s408.py   S446's card (F-673) in place of S408's foot card -- 'Mahine ka pack — August 2026', gone once 'Dekh liya' -- on BOTH runs")
    for name, items in ADJ.items():
        for code, why, _o, _n in items:
            print("   %-4s %-15s %s" % (code, name, why))
    for w in plan:
        name = os.path.basename(w["src"])
        src = open(w["src"], encoding="utf-8").read()
        res = {}
        for side in ("baseline", "patched"):
            d = os.path.join(w["work"], side)
            os.makedirs(d, exist_ok=True)
            for extra in w.get("beside") or []:
                with open(extra, "rb") as fh, open(os.path.join(d, os.path.basename(extra)), "wb") as gh:
                    gh.write(fh.read())
            for pre in (w.get("pre") or {}).get(side) or []:
                p = subprocess.run(pre, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=600)
                print("   %-9s %-15s pre: %s" % (side, name, (p.stdout.strip().splitlines() or ["(no output)"])[-1][:200]))
            f = os.path.join(d, name)
            open(f, "w", encoding="utf-8").write(adjust(name, src, side == "patched"))
            env = dict(os.environ, **w["env"][side])
            p = subprocess.run([w.get("py") or sys.executable, "-B", f] + w["args"][side], cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, timeout=3000)
            tally = [l for l in p.stdout.splitlines() if re.match(r"^WALK(_\w+)? (GREEN|RED|OK)", l)]
            res[side] = dict(fails=fails(p.stdout), tally=(tally[-1] if tally else "NO TALLY (exit %s)" % p.returncode), tail=p.stdout.splitlines()[-15:])
            print("   %-9s %-15s %s" % (side, name, res[side]["tally"][:200]))
            for x in res[side]["fails"]:
                print("               red: %s" % x[:700])
        acc = ACCEPT.get(name, [])
        bad = []
        for x in res["patched"]["fails"]:
            ok = any(x.startswith(a) for a, _w in acc) and any(b.startswith(x[:60]) for b in res["baseline"]["fails"])
            if not ok:
                bad.append(x)
        if "NO TALLY" in res["patched"]["tally"]:
            bad.append(res["patched"]["tally"])
            print("\n".join("      " + l for l in res["patched"]["tail"]))
        if bad:
            red.append(name)
            print("   !! %s: red on the patched files beyond the accepted: %s" % (name, " | ".join(b[:160] for b in bad)))
        elif res["patched"]["fails"]:
            print("   %s: the same reds as on the box as it is, each accepted: %s" % (name, "; ".join("%s (%s)" % (a, why) for a, why in acc
                                                                                                    if any(x.startswith(a) for x in res["patched"]["fails"]))))
    if red:
        print("WALKS_OLD_S452 RED -- %s" % ", ".join(red))
        return 1
    print("WALKS_OLD_S452 GREEN -- S446's, S444's, S407's, S408's and S434's walks: green on the patched files but for the named reds, each red on the box as it is too")
    return 0


if __name__ == "__main__":
    sys.exit(main())
