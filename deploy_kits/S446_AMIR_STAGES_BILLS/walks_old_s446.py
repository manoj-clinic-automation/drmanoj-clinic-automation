#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walks_old_s446.py -- kit S446_AMIR_STAGES_BILLS: the earlier walks of the board and of Amir's day, re-run on the patched files.

Each walk is COPIED to scratch (the kit folders are never edited) and run twice: UNADJUSTED on the box as it is (the baseline -- what
was already red before S446) and ADJUSTED on the box + S446. Each adjustment is an anchored replacement on the copy (anchor exactly
once, else STOP), named below with the reason. The gate: on the patched files a walk is green, or every one of its reds is in its
ACCEPT list AND red in the baseline too (a fact of today's data that a later kit or day moved, never something S446 moved).

    walks_old_s446.py --plan PLAN.json       (the installer writes the plan: each walk's file, its arguments for both runs, its env)
"""
import json
import os
import re
import subprocess
import sys

R = "S446-ADJUSTED"
ADJ = {
    "walk_s437.py": [
        ("D1", "the board is read as the owner: S446 shows Amir only his stage (7 orthotic vouchers now); the whole count -- every voucher, "
               "the CCM line, the proof's gate on the renames -- stays the owner's and the checker's view, which this walk asserts",
         'def amir():\n    return G("amir", "/finance/stock/api/pad/amir/1")[1]\n',
         'def amir():\n    return G("manoj", "/finance/stock/api/pad/amir/1")[1]   # ' + R + ' D1\n')],
    "walk_s436_s437.py": [
        ("D2", "as D1, for S436's walk (S437's copy)",
         'def amir():\n    return G("amir", "/finance/stock/api/pad/amir/1")[1]\n',
         'def amir():\n    return G("manoj", "/finance/stock/api/pad/amir/1")[1]   # ' + R + ' D2\n')],
    "walk_s444.py": [
        ("B1", "the card is staged (D649): Stage A reads 'Orthotic voucher baaki: N' and nothing of medicine -- the card's figures read as [orthotic, 0]",
         'card=[int(m.group(1)), int(m.group(2))] if m else None,', 'card=[int(m.group(1)), int(m.group(2) or 0)] if m else None,   # ' + R + ' B1\n                       '),
        ("B1b", "as B1, the regex of the step pages",
         'm = re.search(r"Stock voucher baaki: (\\d+) orthotic, (\\d+) dawa", h)\n        steps[n]',
         'm = re.search(r"(?:Stock|Orthotic) voucher baaki: (\\d+)(?: orthotic, (\\d+) dawa)?", h)   # ' + R + ' B1\n        steps[n]'),
        ("B1c", "as B1, after one voucher is entered",
         'm = re.search(r"Stock voucher baaki: (\\d+) orthotic, (\\d+) dawa", h1)\n    out["card_after"] = [int(m.group(1)), int(m.group(2))] if m else None',
         'm = re.search(r"(?:Stock|Orthotic) voucher baaki: (\\d+)(?: orthotic, (\\d+) dawa)?", h1)   # ' + R + ' B1\n    out["card_after"] = [int(m.group(1)), int(m.group(2) or 0)] if m else None'),
        ("B1d", "as B1, the expected figures: Stage A shows the orthotic vouchers only",
         'card = [exp["ortho"], exp["dawa"]] if exp else None', 'card = [exp["ortho"], 0] if exp else None   # ' + R + ' B1'),
        ("B2", "the renames' gate: S446 shows them to Amir once STAGE A is verified by its own proof (the orthotic lines), not on the whole "
               "count's _proof_state -- the crafted green proof patches that stage proof too",
         '        stock_app._proof_state = lambda con, d: {"state": "done"}       # walk only: the crafted green proof\n',
         '        stock_app._proof_state = lambda con, d: {"state": "done"}       # walk only: the crafted green proof\n'
         '        real_s446 = getattr(stock_app, "_s446_proof", None)          # ' + R + ' B2\n'
         '        stock_app._s446_proof = lambda con, root, keys, ent, batches: {"state": "done", "rows": []}\n'),
        ("B2b", "as B2, put back after",
         '        stock_app._proof_state = real_ps\n',
         '        stock_app._proof_state = real_ps\n        if real_s446:\n            stock_app._s446_proof = real_s446   # ' + R + ' B2\n'),
        ("B3", "the owner's line (d) is named by stage: 'Count vouchers waiting (Stage A, orthotic): N'",
         'len(nv) == 1 and ("(orthotic %d)" % card[0]) in nv[0]', 'len(nv) == 1 and ("(Stage A, orthotic): %d" % card[0]) in nv[0]   # ' + R + ' B3\n          ')],
}
ACCEPT = {
    "walk_s437.py": [("ONE run of kind receive_close", "today's data: S437's own rule already ran on the live database (28-Sep), so the walk's 'one run' finds two kinds"),
                     ("every shelf-more line has exactly ONE STOCK RECEIVE line on round 5", "today's data: round 5 was made on the live database by S437's seed"),
                     ("the statement reads 'Marg corrected", "today's data: as above, the statement reads the live round 5")],
    "walk_s444.py": [("NEGATIVE: KEDAR 195's claim stays open on the box as it is", "today's data: S444's own rule settled claim #1 on the live database at its install (01-Oct 22:09)")],
}


def adjust(name, src):
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
    for name, items in ADJ.items():
        for code, why, _o, _n in items:
            print("   %-4s %-20s %s" % (code, name, why))
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
            f = os.path.join(d, name)
            open(f, "w", encoding="utf-8").write(adjust(name, src) if side == "patched" else src)
            env = dict(os.environ, **w["env"][side])
            p = subprocess.run([sys.executable, "-B", f] + w["args"][side], cwd=d, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=2700)
            tally = [l for l in p.stdout.splitlines() if re.match(r"^WALK_\w+ (GREEN|RED)", l)]
            res[side] = dict(fails=fails(p.stdout), tally=(tally[-1] if tally else "NO TALLY (exit %s)" % p.returncode), tail=p.stdout.splitlines()[-15:])
            print("   %-9s %-20s %s" % (side, name, res[side]["tally"]))
            for x in res[side]["fails"]:
                print("               red: %s" % x[:240])
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
            print("   !! %s: red on the patched files beyond the accepted: %s" % (name, " | ".join(b[:120] for b in bad)))
        elif res["patched"]["fails"]:
            print("   %s: the same reds as on the box as it is, each accepted: %s" % (name, "; ".join("%s (%s)" % (a, why) for a, why in acc if any(x.startswith(a) for x in res["patched"]["fails"]))))
    if red:
        print("WALKS_OLD_S446 RED -- %s" % ", ".join(red))
        return 1
    print("WALKS_OLD_S446 GREEN -- S437's and S436's walks on the board, S444's walk: green on the patched files but for the named reds of today's data")
    return 0


if __name__ == "__main__":
    sys.exit(main())
