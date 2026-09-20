#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_s338.py -- kit S338_SPINE_HEALTH (S274, Sanjeevni).

    python3 -B selftest_s338.py [--legs /root/finance/freshness_legs.json] [--freshness /root/finance/freshness.py]

Checks, on copies in a scratch folder: write_state() moves last_success_iso only on a passed gate, keeps it
on a failed one, records the failed checks, writes atomically, and the file reads as a state_json leg would
read it; apply_legs_s338 appends exactly two legs, changes no other leg, refuses a wrong pin, and is
idempotent; and freshness.py's own load_legs() finds no bad leg in the result.  Made to fail on purpose:
the wrong-pin refusal and the failed-gate case.
"""
import argparse
import datetime as dt
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS, FAILED = [], []


def ck(name, cond, detail=""):
    CHECKS.append(name)
    print(("  ok   " if cond else "  FAIL ") + name + (("  -- " + str(detail)[:160]) if detail and not cond else ""))
    if not cond:
        FAILED.append(name)


class G:
    def __init__(self, rows):
        self.rows = rows
        self.passed = all(r[2] for r in rows if r[1])


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--legs", default="/root/finance/freshness_legs.json")
    ap.add_argument("--freshness", default="/root/finance/freshness.py")
    a = ap.parse_args(argv)
    td = tempfile.mkdtemp(prefix="s338_")
    sb = load(os.path.join(HERE, "spine_build.py"), "spine_build_s338")
    ck("spine_build.py is the S338 one (write_state, STATE_NAME)", hasattr(sb, "write_state") and sb.STATE_NAME == "spine_state.json")
    out_db = os.path.join(td, "spine.db")
    open(out_db, "wb").close()
    rows_ok = [("check %d" % i, 1, 1, "") for i in range(14)] + [("a note", 0, 0, "informational")]
    B = {"G": G(rows_ok)}
    st = sb.write_state(out_db, B, True)
    p = os.path.join(td, "spine_state.json")
    ck("a passed gate writes spine_state.json beside the spine", os.path.exists(p) and not os.path.exists(p + ".tmp"))
    j = json.load(open(p))
    ck("... gate 14/14, passed, last_success_iso set, no failed names", j["gate"] == "14/14" and j["passed"] and j["last_success_iso"] and j["failed"] == [], j)
    ck("... the status line is present (fallback wording when spine_read cannot open an empty db)", bool(j["status"]), j["status"])
    ok_iso = j["last_success_iso"]
    rows_bad = list(rows_ok)
    rows_bad[3] = ("STOCK: the spine equals Marg on every item", 1, 0, "3 items off")
    st2 = sb.write_state(out_db, {"G": G(rows_bad)}, False)
    j2 = json.load(open(p))
    ck("NEGATIVE: a failed gate KEEPS last_success_iso from the good build and names the failed check",
       j2["last_success_iso"] == ok_iso and not j2["passed"] and j2["gate"] == "13/14" and "STOCK" in j2["failed"][0] and j2["last_failure_iso"], j2)
    ck("... its status line says GATE FAILED and that the last good spine stands", "GATE FAILED 13/14" in j2["status"] and "last good spine" in j2["status"], j2["status"])
    ts = dt.datetime.fromisoformat(j2["last_success_iso"])
    ck("last_success_iso parses as a timestamp (what read_state_json does)", ts.tzinfo is not None)

    # the legs
    legs_src = a.legs if os.path.exists(a.legs) else None
    if legs_src is None:
        print("   (no legs file at %s -- the legs checks run on a minimal fixture)" % a.legs)
        fixture = {"_about": "fixture", "legs": [{"name": "x", "group": "g", "kind": "file_mtime", "target": "/tmp/x", "max_age_h": 26}]}
        legs_src = os.path.join(td, "fixture_legs.json")
        json.dump(fixture, open(legs_src, "w"), indent=1)
    lp = os.path.join(td, "freshness_legs.json")
    shutil.copy2(legs_src, lp)
    import hashlib
    before = json.load(open(lp))
    pin = hashlib.md5(open(lp, "rb").read()).hexdigest()
    applier = os.path.join(HERE, "apply_legs_s338.py")
    r = subprocess.run([sys.executable, "-B", applier, "--file", lp, "--from", "00000000"], capture_output=True, text=True)
    ck("NEGATIVE: a wrong pin is refused and nothing is written", r.returncode == 3 and "REFUSED" in r.stdout
       and hashlib.md5(open(lp, "rb").read()).hexdigest() == pin, r.stdout)
    r = subprocess.run([sys.executable, "-B", applier, "--file", lp, "--from", pin[:8]], capture_output=True, text=True)
    after = json.load(open(lp))
    ck("the right pin applies: two legs added", r.returncode == 0 and "APPLIED: 2 leg(s)" in r.stdout and len(after["legs"]) == len(before["legs"]) + 2, r.stdout)
    ck("... every existing leg is unchanged in value", after["legs"][:len(before["legs"])] == before["legs"])
    ck("... the other top-level keys are unchanged", {k: v for k, v in after.items() if k != "legs"} == {k: v for k, v in before.items() if k != "legs"})
    names = [l["name"] for l in after["legs"][-2:]]
    ck("... the two are the spine gate and the spine compare", names == ["Marg spine gate (S331)", "Marg spine compare (S331)"], names)
    ck("... a backup sits beside the file", os.path.exists(lp + ".bak_S338_" + pin[:8]))
    r = subprocess.run([sys.executable, "-B", applier, "--file", lp], capture_output=True, text=True)
    ck("a second run answers ALREADY", r.returncode == 0 and "ALREADY" in r.stdout, r.stdout)
    if os.path.exists(a.freshness):
        fr = load(a.freshness, "freshness_live")
        try:
            legs = fr.load_legs(lp, {"STATE_FILE": "/tmp/x.json"})
            bad = [(l["name"], l["bad"]) for l in legs if l.get("bad")]
            ck("freshness.py's own load_legs finds %d legs and no bad declaration" % len(legs), not bad, bad)
            mine = [l for l in legs if l["name"].startswith("Marg spine")]
            ck("... the spine gate leg is state_json/last_success_iso 26 h; the compare leg file_mtime 26 h",
               len(mine) == 2 and mine[0]["kind"] == "state_json" and mine[0].get("field") == "last_success_iso"
               and mine[0]["max_age_h"] == 26 and mine[1]["kind"] == "file_mtime" and mine[1]["max_age_h"] == 26, mine)
            # read the leg against the state file this test wrote
            leg = dict(mine[0]); leg["target"] = p
            ts_epoch, verdict, detail = fr.read_state_json(leg)
            ck("read_state_json reads the state file the build wrote (last_success_iso)", ts_epoch is not None and verdict is None, (verdict, detail))
        except Exception as e:                                   # noqa: BLE001
            ck("freshness.py could be exercised", False, e)
    else:
        print("   (freshness.py not at %s -- its loader was not exercised here)" % a.freshness)
    shutil.rmtree(td, ignore_errors=True)
    print("selftest: %d/%d" % (len(CHECKS) - len(FAILED), len(CHECKS)))
    for f in FAILED:
        print("   FAILED: %s" % f)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
