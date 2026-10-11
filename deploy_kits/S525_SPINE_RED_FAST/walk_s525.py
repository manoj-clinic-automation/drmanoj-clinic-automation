#!/usr/bin/env python3
"""walk_s525.py -- kit S525_SPINE_RED_FAST, walked before anything is placed. Read-only on the live estate.

PART 1, live shape: the old and the new freshness.py each read EVERY declared leg of their own legs file (the live one and
the kit's freshness_legs.json.kit), on this box, with collect() -- the job's own reading, nothing written (no state, no JSON, no HTML, no shout).
Every leg reads the same in both -- verdict, age, detail -- except a leg that names fail_field; that leg is STALE in the new
one exactly when its state file's failure time is newer than its success time, and otherwise reads as the old one does.
PART 2, made-up state files: success newer (OK); the newest run failed an hour after a good one (STALE, the detail says
FAILED) and the old file calls that OK (the fault); no failure recorded (age rule); an unreadable failure value (ERROR);
a leg that does not name fail_field (age rule, opt-in only); a failure dated before the success (OK).
  walk_s525.py <kit dir> [--live-py /root/finance/freshness.py] [--live-legs /root/finance/freshness_legs.json]
No secret is read: the conf (the ntfy address) is never opened by this walk."""
import argparse, importlib.util, json, os, shutil, sys, tempfile, time

N = [0]


def check(name, ok, detail=""):
    if not ok:
        print("FAIL %d: %s %s" % (N[0] + 1, name, detail))
        sys.exit(1)
    N[0] += 1


def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kit")
    ap.add_argument("--live-py", default="/root/finance/freshness.py")
    ap.add_argument("--live-legs", default="/root/finance/freshness_legs.json")
    a = ap.parse_args()
    old = load(a.live_py, "fresh_old")
    new = load(os.path.join(a.kit, "freshness.py"), "fresh_new")
    now = time.time()
    subs = {}
    legs_o = old.load_legs(a.live_legs, subs)
    legs_n = new.load_legs(os.path.join(a.kit, "freshness_legs.json.kit"), subs)
    check("the same legs, in the same order", [l["name"] for l in legs_o] == [l["name"] for l in legs_n])
    check("the kit's legs file differs from the live one in the spine gate leg only",
          [l["name"] for l, m in zip(legs_o, legs_n) if {k: v for k, v in l.items() if k not in ("note", "fail_field")}
           != {k: v for k, v in m.items() if k not in ("note", "fail_field")}] == []
          and [m["name"] for m in legs_n if m.get("fail_field")] == ["Marg spine gate (S331)"])
    ro, _ = old.collect(legs_o, now)
    rn, _ = new.collect(legs_n, now)
    n_same = n_ff = 0
    for x, y, leg in zip(ro, rn, legs_n):
        if leg.get("fail_field"):
            n_ff += 1
            if not os.path.exists(leg["target"]):
                check("%s: no state file -- the same row in both" % leg["name"], x == {**y, "note": x["note"]})
                print("   %s: no state file here (%s in both)" % (leg["name"], y["verdict"]))
                continue
            with open(leg["target"]) as fh:
                st = json.load(fh)
            fs, ff = new.parse_ts(st.get(leg["field"])), new.parse_ts(st.get(leg["fail_field"]))
            failing = ff is not None and fs is not None and ff > fs
            if failing:
                check("%s: the newest build failed, so the new file says STALE" % leg["name"], y["verdict"] == "STALE"
                      and "FAILED" in y["detail"] and "FAILED" in y["age_words"], y["verdict"])
            else:
                check("%s: the newest build passed, so the new file reads as the old" % leg["name"], y["verdict"] == x["verdict"])
            check("%s: the age is the same" % leg["name"], y["age_h"] == x["age_h"])
            print("   %s: old %s, new %s (%s)" % (leg["name"], x["verdict"], y["verdict"], "the newest build FAILED" if failing else "the newest build passed"))
        else:
            check("%s: the same row in both" % leg["name"], {k: v for k, v in x.items() if k != "note"} == {k: v for k, v in y.items() if k != "note"},
                  "%s / %s" % (x["verdict"], y["verdict"]))
            n_same += 1
    check("every live leg was read (%d)" % len(rn), len(rn) == len([l for l in legs_n if not l.get("disabled")]) and len(rn) >= 30)
    check("exactly one leg names fail_field", n_ff == 1)

    # PART 2
    d = tempfile.mkdtemp(prefix="s525_walk_")
    try:
        def leg(state, ff=True, name="t"):
            p = os.path.join(d, name + ".json")
            with open(p, "w") as fh:
                json.dump(state, fh)
            L = {"name": name, "group": "g", "kind": "state_json", "target": p, "field": "last_success_iso",
                 "max_age_h": 26.0, "note": "", "disabled": False, "bad": ""}
            if ff:
                L["fail_field"] = "last_failure_iso"
            return L
        iso = lambda t: time.strftime("%Y-%m-%dT%H:%M:%S+05:30", time.localtime(t)) if time.strftime("%z") == "+0530" else \
            time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t))
        L1 = leg({"last_success_iso": iso(now - 600), "last_failure_iso": iso(now - 7200)}, name="a")
        check("success newer than the failure: OK", new.check_leg(L1, now)["verdict"] == "OK")
        L2 = leg({"last_success_iso": iso(now - 3600), "last_failure_iso": iso(now - 300)}, name="b")
        r2 = new.check_leg(L2, now)
        check("the newest run failed an hour after a good one: STALE now, and the detail says FAILED",
              r2["verdict"] == "STALE" and "FAILED" in r2["detail"], str(r2))
        check("and the words the page, the table and the phone message show say FAILED too",
              "FAILED" in r2["age_words"] and "FAILED" in new.shout_body([r2], 1, "x"), str(r2))
        check("CONTROL: the old file calls that same state OK (the fault this kit mends)", old.check_leg(L2, now)["verdict"] == "OK")
        L3 = leg({"last_success_iso": iso(now - 3600), "last_failure_iso": ""}, name="c")
        check("no failure recorded: the age rule", new.check_leg(L3, now)["verdict"] == "OK")
        L3b = leg({"last_success_iso": iso(now - 3600)}, name="c2")
        check("the failure field absent from the file: the age rule", new.check_leg(L3b, now)["verdict"] == "OK")
        L4 = leg({"last_success_iso": iso(now - 3600), "last_failure_iso": "not a time"}, name="e")
        check("an unreadable failure value: ERROR, never a pass", new.check_leg(L4, now)["verdict"] == "ERROR")
        L5 = leg({"last_success_iso": iso(now - 3600), "last_failure_iso": iso(now - 300)}, ff=False, name="f")
        check("a leg that does not name fail_field: the age rule (opt-in only)", new.check_leg(L5, now)["verdict"] == "OK")
        L6 = leg({"last_success_iso": iso(now - 30 * 3600), "last_failure_iso": iso(now - 31 * 3600)}, name="g")
        check("an old success with an older failure: STALE by age, as before", new.check_leg(L6, now)["verdict"] == "STALE"
              and old.check_leg(L6, now)["verdict"] == "STALE")
    finally:
        shutil.rmtree(d, ignore_errors=True)
    print("   %d legs read live: %d the same row in both, %d judged by its failure field" % (len(rn), n_same, n_ff))
    print("WALK OK -- %d checks" % N[0])


if __name__ == "__main__":
    main()
