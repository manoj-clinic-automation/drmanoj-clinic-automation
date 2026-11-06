#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
proof_s726.py -- S726: OLD against NEW on real data, READ ONLY.  For 2026-09, 2026-10 and 2026-11: what the month's register shows by the
live files and by the rebuilt ones, on the same two databases opened read-only (mode=ro).  The new side also applies, IN MEMORY, the
AUTO links the S726 rule would undo at the next pass (purchase_app._s726_undo_plan, which only reads): their bills are shown unpaired.
No pass is run (_rematch is never called) and nothing is written; the freed scans re-pair at the next pass, by number or by reception's
question, which this proof does not guess.

    python3 -B proof_s726.py <old finance dir> <new finance dir> <finance.db> <assets.db>

Prints, for each month, every bill whose state or pairing changes (supplier, bill no., amount, old state -> new state), the counts per state before and
after, and one last line: "PROOF S726: N bills change (Sep a, Oct b, Nov c)" -- or "PROOF S726: REFUSED ..." / "PROOF S726: ERROR ...".
"""
import json
import os
import subprocess
import sys

MONTHS = ("2026-09", "2026-10", "2026-11")
SHORT = {"2026-09": "Sep", "2026-10": "Oct", "2026-11": "Nov"}


def side(d, db, adb, which):
    """One side, in its own process (the two sides' modules carry the same names). Prints one JSON line."""
    sys.path.insert(0, os.path.abspath(d))
    import warnings
    warnings.simplefilter("ignore")
    import sqlite3
    import purchase_app as PA
    import scan_register as SR
    PA._assets_db = adb
    con = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(db), uri=True, timeout=30)
    con.row_factory = sqlite3.Row
    out = dict(side=which, plan=[], months={})
    if which == "new":
        plan_fn = getattr(PA, "_s726_undo_plan", None)
        if plan_fn is None:
            raise SystemExit("the new side has no _s726_undo_plan")
        plan = plan_fn(con)
        if plan is None:
            raise SystemExit("the asset app's database is not readable")
        out["plan"] = plan
        drop = {int(x["bill"]): int(x["scan"]) for x in plan if not x.get("final")}      # a finalised month's link is kept
        orig = SR.links

        def links(c):
            return {k: v for k, v in orig(c).items() if not (k in drop and v["scan"] == drop[k])}
        SR.links = links
        quiet_orig = SR.s726_quiet_bills
        first = SR.Ctx(con).first
        parked_drop = {k for k in drop if str(next((x["bill_month"] for x in plan if int(x["bill"]) == k), "")) < first}

        def quiet(c):                                              # the audit rows the pass would write, in memory
            return quiet_orig(c) | parked_drop
        SR.s726_quiet_bills = quiet
    for m in MONTHS:
        r = SR.register(con, m)
        out["months"][m] = dict(cls=r["cls"], settled=r["settled"], total=r["total"], open_scans=r["open_scans"],
                                rows=[dict(id=x["id"], supplier=x["supplier"], bill_no=x["bill_no"], amount_p=x["amount_p"], state=x["state"],
                                           scan=x.get("scan"), stamp=x.get("stamp") or "", whose=x.get("whose") or "", diff=(x.get("agree") or {}).get("diff"))
                                      for x in r["rows"]])
    con.close()
    print(json.dumps(out))


def rs(p):
    v = str(int(round(abs(int(p or 0)) / 100.0)))
    if len(v) > 3:
        head, tail = v[:-3], v[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        v = ",".join(parts) + "," + tail
    return "Rs " + v


def run(d, db, adb, which):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("ORDER_TODAY", None)
    r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--side", d, db, adb, which], cwd="/tmp", env=env,
                       capture_output=True, text=True, timeout=900)
    lines = [x for x in r.stdout.splitlines() if x.startswith("{")]
    if r.returncode != 0 or not lines:
        raise RuntimeError("%s side: %s" % (which, (r.stderr.strip().splitlines() or r.stdout.strip().splitlines() or ["no output"])[-1][:200]))
    return json.loads(lines[-1])


def main(argv):
    if len(argv) >= 1 and argv[0] == "--side":
        side(*argv[1:5])
        return 0
    if len(argv) < 4:
        print(__doc__)
        return 2
    old_d, new_d, db, adb = argv[:4]
    for p in (db, adb):
        if not os.path.isfile(p):
            print("PROOF S726: ERROR -- %s is not there" % p)
            return 1
    try:
        old, new = run(old_d, db, adb, "old"), run(new_d, db, adb, "new")
    except Exception as e:                                             # noqa: BLE001
        print("PROOF S726: ERROR -- %s" % e)
        return 1
    first = "2026-10"
    try:
        import sqlite3
        c = sqlite3.connect("file:%s?mode=ro" % os.path.abspath(db), uri=True, timeout=30)
        v = (c.execute("SELECT value FROM setting WHERE key='purchase.register_from'").fetchone() or [""])[0] or ""
        c.close()
        if len(str(v)) >= 7 and str(v)[4] == "-" and str(v)[:4].isdigit() and str(v)[5:7].isdigit():
            first = str(v)[:7]
    except Exception:                                                  # noqa: BLE001
        pass
    plan = {int(x["bill"]): x for x in new["plan"] if not x.get("final")}
    kept = [x for x in new["plan"] if x.get("final")]
    print("S726 proof -- read only; the register of each month by the live files (old) and the rebuilt ones (new); counted from %s" % first)
    print("AUTO links the next pass undoes (counted months only, never a finalised one): %d" % len(plan))
    for x in new["plan"]:
        print("  %s %s %s (%s, bill month %s) <- scan #%s (scan month %s): %s"
              % ("KEPT (its month is final) --" if x.get("final") else "undo ", x["supplier"], x["bill_no"], rs(x["amount_p"]), x["bill_month"],
                 x["scan"], x["scan_month"] or "?", x["why"]))
    if kept:
        print("  FLAG: %d AUTO link(s) fail the rule but their month is final -- kept; the owner decides" % len(kept))
    bad = [x for x in new["plan"] if not (str(x["bill_month"]) >= first or str(x["scan_month"] or "") >= first)]
    if bad:
        print("PROOF S726: REFUSED -- %d link(s) of September (or earlier) only are in the undo plan" % len(bad))
        return 1
    changed = {}
    for m in MONTHS:
        o, n = old["months"][m], new["months"][m]
        ob = {x["id"]: x for x in o["rows"]}
        nb = {x["id"]: x for x in n["rows"]}
        lines = []
        for bid in sorted(set(ob) | set(nb), key=lambda i: ((ob.get(i) or nb.get(i))["supplier"], str((ob.get(i) or nb.get(i))["bill_no"]))):
            a, b = ob.get(bid), nb.get(bid)
            if a and b and a["state"] == b["state"] and a.get("scan") == b.get("scan"):
                continue
            x = b or a
            pair = ""
            if (a or {}).get("scan") != (b or {}).get("scan"):
                pair = "  [scan %s -> %s]" % ((a or {}).get("stamp") or "none", (b or {}).get("stamp") or "none")
            why = ("  (AUTO link undone: %s)" % plan[bid]["why"]) if bid in plan else ""
            if b and str(b.get("whose") or "").startswith("Nobody ("):
                why += "  -- " + b["whose"]
            lines.append("  %-30s %-12s %10s  %s -> %s%s%s" % (str(x["supplier"])[:30], str(x["bill_no"])[:12], rs(x["amount_p"]),
                                                             (a or {}).get("state", "-"), (b or {}).get("state", "-"), pair, why))
        changed[m] = len(lines)
        print("")
        print("%s (%s): %d bill(s), %d change" % (m, o["cls"], o["total"], len(lines)))
        for ln in lines:
            print(ln)
        states = sorted({x["state"] for x in o["rows"]} | {x["state"] for x in n["rows"]})
        print("  states before: %s" % " · ".join("%s %d" % (s, sum(1 for x in o["rows"] if x["state"] == s)) for s in states))
        print("  states after:  %s" % " · ".join("%s %d" % (s, sum(1 for x in n["rows"] if x["state"] == s)) for s in states))
        print("  settled before %d of %d · after %d of %d" % (o["settled"], o["total"], n["settled"], n["total"]))
        rnd = [x for x in n["rows"] if x["state"] in ("verified", "has_scan") and x.get("diff") and abs(int(x["diff"])) <= 100]
        print("  a rounding rupee now shown on %d settled bill(s) (no state change)" % len(rnd))
    total = sum(changed.values())
    print("")
    print("PROOF S726: %d bills change (Sep %d, Oct %d, Nov %d)" % (total, changed["2026-09"], changed["2026-10"], changed["2026-11"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
