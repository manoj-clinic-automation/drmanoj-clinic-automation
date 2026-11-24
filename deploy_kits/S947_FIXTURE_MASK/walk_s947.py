#!/usr/bin/python3
# walk_s947.py -- S947 (the parent, S513): proves a folder of the S947 files is masked and still works.
#   python3 walk_s947.py <FROM dir> <dir to judge> <NO_PHONE_NUMBERS.py> [python]
# Judges the four names (6 checks each) + the gate + the count: 26 checks. Digits are ASCII only.
# Judging the TO folder must be all PASS; judging the FROM folder itself is the CONTROL and must go red.
# Distinct originals staying distinct is asserted here too (one mapping, no two runs folded into one).
# Nothing patient-level is printed: counts and file names only.
import os, re, subprocess, sys, tempfile
NAMES = ["call_verdict.py", "daily_digest.py", "flag_investigator.py", "verdict_review.py"]
WANT = {"call_verdict.py": "SELFTEST: 42/42 PASS", "daily_digest.py": "SELFTEST: 81/81 PASS",
        "flag_investigator.py": "SELFTEST: 51/51 PASS", "verdict_review.py": "SELFTEST: 144 passed, 0 failed",
        }
RUN = re.compile(r"(?<![0-9])(?:\+?91[ -]?)?([6-9][0-9]{9})(?![0-9])")
src, dut, gate = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]), os.path.abspath(sys.argv[3])
py = sys.argv[4] if len(sys.argv) > 4 else sys.executable
NAMES = [n for n in NAMES if os.path.exists(os.path.join(dut, n))]
res = []
def check(name, ok):
    res.append(ok); print("  %-4s %s" % ("PASS" if ok else "FAIL", name))
for n in NAMES:
    a = open(os.path.join(src, n), "rb").read(); b = open(os.path.join(dut, n), "rb").read()
    check("%s: same length as FROM" % n, len(a) == len(b))
    spans = [m.span(1) for m in RUN.finditer(a.decode("utf-8"))]
    inrun = set(i for s, e in spans for i in range(s, e))
    # ascii-only digits move, so byte offsets equal char offsets wherever a digit sits (asserted: same length)
    au = a.decode("utf-8"); bu = b.decode("utf-8")
    moved = [i for i, (x, y) in enumerate(zip(au, bu)) if x != y]
    check("%s: every changed char is a digit inside a 6-9 run (%d changed)" % (n, len(moved)),
          len(au) == len(bu) and all(i in inrun and bu[i] in "0123456789" for i in moved))
    check("%s: every run's last four kept" % n, all(au[e - 4:e] == bu[e - 4:e] for s, e in spans))
    check("%s: no 6-9 run left" % n, not RUN.search(bu))
    with tempfile.TemporaryDirectory() as pc:   # the bytecode goes to a temp prefix, never beside the file
        ok = subprocess.run([py, "-m", "py_compile", os.path.join(dut, n)], capture_output=True,
                            env=dict(os.environ, PYTHONPYCACHEPREFIX=pc)).returncode == 0
    check("%s: compiles" % n, ok)
    with tempfile.TemporaryDirectory() as td:
        p = subprocess.run([py, "-B", os.path.join(dut, n), "--selftest"], capture_output=True, text=True, cwd=td,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=120)
    check("%s: selftest '%s'" % (n, WANT[n]), p.returncode == 0 and WANT[n] in p.stdout)
with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as lf:
    lf.write("\n".join(os.path.join(dut, n) for n in NAMES) + "\n")
g = subprocess.run([py, gate, "--files-from", lf.name], capture_output=True, text=True, cwd=os.path.dirname(gate))
os.unlink(lf.name)
flagged = len([l for l in g.stdout.splitlines() if re.match(r"\s+\S+\.py\s+line\s+\d+", l)])
check("NO_PHONE_NUMBERS over the five: exit 0, 0 lines flagged (%d)" % flagged, g.returncode == 0 and flagged == 0)
check("the four live files judged (%d)" % len(NAMES), len(NAMES) == 4)
pairs = {}
for n in NAMES:
    au = open(os.path.join(src, n), encoding="utf-8").read(); bu = open(os.path.join(dut, n), encoding="utf-8").read()
    for m in RUN.finditer(au):
        pairs.setdefault(m.group(1), set()).add(bu[m.start(1):m.end(1)])
outs = [v for s_ in pairs.values() for v in s_]
check("one mapping: each original one replacement, no two originals share one", all(len(v) == 1 for v in pairs.values()) and len(set(outs)) == len(outs))
print("WALK: %d/%d PASS" % (sum(res), len(res)))
sys.exit(0 if all(res) else 1)
