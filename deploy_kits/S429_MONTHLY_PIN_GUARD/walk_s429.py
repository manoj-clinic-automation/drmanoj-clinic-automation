#!/usr/bin/env python3
"""walk_s429.py -- walk for S429_MONTHLY_PIN_GUARD. usage: walk_s429.py <original (S424)> <patched copy>
Runs the patched file's own monthly block against a fake Drive in five cases; checks the rest of the file is
untouched. No network, no key, no Drive. Prints WALK OK n/n."""
import sys
import textwrap
import time

ORIG, NEW = sys.argv[1], sys.argv[2]
o = open(ORIG, encoding="utf-8").read()
s = open(NEW, encoding="utf-8").read()
N = [0, 0]


def check(name, cond, extra=""):
    N[1] += 1
    if cond:
        N[0] += 1
        print("  ok  %s" % name)
    else:
        print("  RED %s %s" % (name, extra))


A, B = "        # ---- monthly: first verified run of the month", "        # ---- the state file"
check("outside the monthly block the file is the original byte for byte",
      o[:o.index(A)] == s[:s.index(A)] and o[o.index(B):] == s[s.index(B):])
compile(s, NEW, "exec")
check("compiles", True)
block = textwrap.dedent(s[s.index(A):s.index(B)])
code = compile("def _m(d, monthly, local_md5, desc, now, log, time, PIN_WARN, MONTHLY, enc='walk.enc'):\n" +
               textwrap.indent(block, "    ") + "\n    return monthly_done\n", "block", "exec")
ns = {}
exec(code, ns)


class FakeDrive:
    def __init__(self, md5_ok=True, revs=True, pin_fails=False):
        self.md5_ok, self.revs_, self.pin_fails = md5_ok, revs, pin_fails
        self.meta, self.pinned, self.updates = None, [], 0

    def update_content(self, fid, path):
        self.updates += 1

    def get(self, fid):
        return {"md5Checksum": "L" if self.md5_ok else "X"}

    def revisions(self, fid):
        return ([{"id": "r1", "keepForever": bool(self.pinned)}] if self.revs_ else [])

    def pin_revision(self, fid, rid):
        if self.pin_fails:
            raise RuntimeError("walk: drive refused the pin")
        self.pinned.append(rid)

    def patch_meta(self, fid, body):
        self.meta = body["description"]


def run(desc_before, **kw):
    d, logs = FakeDrive(**kw), []
    now = time.strptime("2026-10-01 01:30", "%Y-%m-%d %H:%M")
    done = ns["_m"](d, {"id": "M", "description": desc_before}, "L", "walk desc", now,
                    lambda *a: logs.append(" ".join(str(x) for x in a)), time, 180, "clinic_state_monthly.tar.gz.enc")
    return d, done, " | ".join(logs)


d, done, lg = run("month=2026-09 · x")
check("new month, pin confirmed: shipped, pinned, description 'month=2026-10', done",
      done and d.pinned == ["r1"] and (d.meta or "").startswith("month=2026-10"), lg)
d, done, lg = run("month=2026-09 · x", pin_fails=True)
check("pin refused: description NOT written (month stays open), warning logged",
      not done and d.meta is None and "NOT pinned" in lg and "pin failed" in lg, lg)
d, done, lg = run("month=2026-09 · x", revs=False)
check("no revision listed: description NOT written, warning logged", not done and d.meta is None and "NOT pinned" in lg, lg)
d, done, lg = run("month=2026-09 · x", md5_ok=False)
check("upload did not verify: nothing written, the old warning stands",
      not done and d.meta is None and "did not verify" in lg, lg)
d, done, lg = run("month=2026-10 · already")
check("month already closed: nothing shipped, nothing written", not done and d.updates == 0 and d.meta is None, lg)
print("WALK %s %d/%d" % ("OK" if N[0] == N[1] else "RED", N[0], N[1]))
sys.exit(0 if N[0] == N[1] else 1)
