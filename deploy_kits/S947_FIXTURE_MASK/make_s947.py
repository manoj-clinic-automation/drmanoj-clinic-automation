#!/usr/bin/python3
# make_s947.py -- S947 (the parent, S513, 24-Nov-2026): F-1639 / F-1648. Builds the TO files from the FROM files.
# Every ten-digit run that starts 6-9 (the shape NO_PHONE_NUMBERS refuses) becomes 500000 + its own last four:
# obviously made up, never a mobile, and every mask() expectation ("******1234") stays true untouched.
# One mapping across all five files (a fixture shared between files stays the same fixture); two different runs
# with the same last four get 500001.., 500002.. so they stay distinct. Nothing is printed but counts and last-4s.
# Proves itself: same length, every changed byte a digit for a digit inside a replaced run (checked by walk_s947.py).
# A +91 / 91 prefix in front of a run is kept as it is (caller_number_raw fixtures): only the ten digits move.
import re, sys, os
NAMES = ["call_verdict.py", "daily_digest.py", "flag_investigator.py", "verdict_review.py"]
RUN = re.compile(r"(?<![0-9])(?:\+?91[ -]?)?([6-9][0-9]{9})(?![0-9])")   # an optional +91 / 91 prefix stays as it is
def build(src, dst):
    texts = {n: open(os.path.join(src, n), encoding="utf-8").read() for n in NAMES}
    uniq = sorted({m.group(1) for t in texts.values() for m in RUN.finditer(t)})
    mp, used = {}, set()
    for r in uniq:
        k = 0
        while True:
            new = "50000%d%s" % (k, r[-4:])
            if new not in used:
                break
            k += 1
        mp[r] = new; used.add(new)
    out = {}
    for n, t in texts.items():
        new = RUN.sub(lambda m: m.group(0)[:m.start(1) - m.start(0)] + mp[m.group(1)], t)
        olds = RUN.findall(t)
        assert len(new) == len(t), n
        assert [mp[o][-4:] for o in olds] == [o[-4:] for o in olds], n
        diff = sum(1 for x, y in zip(t, new) if x != y)
        out[n] = (new, len(olds), len(set(olds)), diff)
        with open(os.path.join(dst, n), "w", encoding="utf-8", newline="") as f:
            f.write(new)
    return out, len(uniq)
if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    out, nu = build(src, dst)
    for n, (new, k, u, d) in out.items():
        print("%-22s runs replaced %3d (unique %2d)  bytes changed %4d  6-9 runs left %d" % (n, k, u, d, len(RUN.findall(new))))
    print("unique runs mapped: %d" % nu)
