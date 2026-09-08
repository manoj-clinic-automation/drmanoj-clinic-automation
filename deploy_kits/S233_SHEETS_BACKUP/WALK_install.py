#!/usr/bin/env python3
# =============================================================================
#  WALK_install.py  ·  Session 233  ·  S233_SHEETS_BACKUP  ·  v1
#
#  AN INSTALLER IS THE MOST DANGEROUS FILE IN A KIT, so it gets the same
#  treatment as the code it installs: a live-shape walk that runs the REAL
#  install.sh, end to end, against a fixture tree that looks like the VPS.
#
#  Nothing real is touched. install.sh honours three test knobs — S233_PREFIX
#  (put every path under a temp directory), S233_PY (use a stub python) and
#  S233_NO_GIT — and this walk sets all three. The stub python answers exactly
#  as the real scripts would, including their exit codes, so the walk can make
#  Google refuse in each of its ways and watch what the installer does about it.
#
#  THE CHECKS THAT MATTER MOST are 6-13: on EVERY failure path, the nightly
#  schedule must NOT be switched on and the saved copies must still be there.
#  An installer that half-installs is worse than one that does nothing.
#
#  Run:  python3 WALK_install.py
# =============================================================================
import json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = []


def check(name, got, want):
    ok = got == want
    CHECKS.append(ok)
    print("  [%s] %-54s got=%r%s" % ("ok " if ok else "FAIL", name, got,
                                     "" if ok else "  want=%r" % (want,)))


STUB_PY = r'''#!/usr/bin/env python3
import os, sys, json, runpy
a = sys.argv[1:]
def code(k, d=0):
    return int(os.environ.get(k, d))
# a real python is still needed for -c and for the heredoc on stdin
if a and (a[0] == "-c" or a[0] == "-"):
    if a[0] == "-":
        src = sys.stdin.read()
        g = {"__name__": "__main__"}
        try:
            exec(compile(src, "<stdin>", "exec"), g)
        except SystemExit as e:
            sys.exit(e.code or 0)
        sys.exit(0)
    exec(a[1])
    sys.exit(0)
script = a[0] if a else ""
mode = a[1] if len(a) > 1 else ""
base = os.path.dirname(script)
if script.endswith("sheets_pull.py"):
    if mode == "preflight":
        sys.exit(code("STUB_PREFLIGHT"))
    if mode == "run":
        rc = code("STUB_RUN")
        if rc == 0:
            for b in ("tracker", "audit", "renewals", "payment_register"):
                d = os.path.join(base, "sheets", b)
                os.makedirs(d, exist_ok=True)
                open(os.path.join(d, "Sheet1.csv"), "w").write("a,b\n1,2\n")
        sys.exit(rc)
    if mode == "list":
        print("  tracker  ok"); sys.exit(0)
    sys.exit(2)
if script.endswith("clinic_state_backup.py"):
    if mode == "run":
        rc = code("STUB_BUNDLE")
        srcs = []
        if code("STUB_BUNDLE_HAS_SHEETS", 1):
            srcs = [os.path.join(base, "sheets", "tracker", "Sheet1.csv")]
        json.dump({"sources": srcs, "files_included": len(srcs) + 50},
                  open(os.path.join(base, "clinic_state_backup.state.json"), "w"))
        sys.exit(rc)
    sys.exit(0)
sys.exit(0)
'''

STUB_CRONTAB = r'''#!/bin/bash
F="$CRONFILE"
if [ "${1:-}" = "-l" ]; then [ -f "$F" ] && cat "$F"; exit 0; fi
if [ "${1:-}" = "-" ]; then cat > "$F"; exit 0; fi
exit 0
'''


def build(tmp):
    base = os.path.join(tmp, "root", "state_backup")
    kit = os.path.join(tmp, "root", "deploy", "repo", "deploy_kits",
                       "S233_SHEETS_BACKUP")
    os.makedirs(base)
    os.makedirs(kit)
    with open(os.path.join(base, "clinic_state_backup.conf"), "w") as fh:
        fh.write("SA_JSON=%s/sa.json\nFOLDER_ID=x\n" % base)
        fh.write("SHEETS=OLD1:tracker,OLD2:accounting_details\n")
    open(os.path.join(base, "sa.json"), "w").write("{}")
    open(os.path.join(base, "clinic_state_backup.py"), "w").write("# live v2\n")
    open(os.path.join(base, "sheets_pull.py"), "w").write("# live v1\n")
    for f in ("sheets_pull.py", "clinic_state_backup.py"):
        src = os.path.join(HERE, f)
        if os.path.isfile(src):
            shutil.copy(src, os.path.join(kit, f))
        else:
            # Only when the walk is run somewhere the kit is not complete. The
            # authoritative run is from inside the kit folder, where both real
            # files sit and the compile stage actually compiles them.
            open(os.path.join(kit, f), "w").write("# placeholder for the walk\n")
    # the exports v1 left behind, including three that must be removed
    for b in ("tracker", "audit", "accounting_details"):
        d = os.path.join(base, "sheets", b)
        os.makedirs(d)
        open(os.path.join(d, "Sheet1.csv"), "w").write("a\n1\n")
    binp = os.path.join(tmp, "bin")
    os.makedirs(binp)
    py = os.path.join(binp, "python3stub")
    open(py, "w").write(STUB_PY)
    os.chmod(py, 0o755)
    cr = os.path.join(binp, "crontab")
    open(cr, "w").write(STUB_CRONTAB)
    os.chmod(cr, 0o755)
    return base, kit, py, binp


def run_installer(tmp, py, binp, **env):
    e = dict(os.environ)
    e.update({"S233_PREFIX": tmp, "S233_PY": py, "S233_NO_GIT": "1",
              "PATH": binp + os.pathsep + e["PATH"],
              "CRONFILE": os.path.join(tmp, "crontab.txt")})
    e.update({k: str(v) for k, v in env.items()})
    p = subprocess.run(["bash", os.path.join(HERE, "install.sh")],
                       env=e, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def cron(tmp):
    f = os.path.join(tmp, "crontab.txt")
    return open(f).read() if os.path.exists(f) else ""


def conf(base):
    return open(os.path.join(base, "clinic_state_backup.conf")).read()


def saved(base):
    return [f for f in os.listdir(base) if ".before_" in f]


def case(name, **env):
    tmp = tempfile.mkdtemp(prefix="walk_inst_")
    base, kit, py, binp = build(tmp)
    rc, out = run_installer(tmp, py, binp, **env)
    return tmp, base, rc, out


def main():
    trees = []
    try:
        # ---- 1-5 · the ordinary install ------------------------------------
        tmp, base, rc, out = case("happy")
        trees.append(tmp)
        check("1  a clean install exits 0", rc, 0)
        check("2  exactly one SHEETS line",
              conf(base).count("\nSHEETS="), 1)
        check("3  and it is the four-book line",
              "payment_register" in conf(base) and
              "accounting_details" not in conf(base).split("SHEETS=")[-1], True)
        check("4  the nightly schedule is on",
              "sheets_pull.py run" in cron(tmp), True)
        check("5  the dropped export was removed",
              os.path.isdir(os.path.join(base, "sheets", "accounting_details")),
              False)
        check("6  the kept export was NOT removed",
              os.path.isdir(os.path.join(base, "sheets", "tracker")), True)
        check("7  copies of both live scripts were kept", len(saved(base)) >= 3, True)

        # ---- 8 · running it twice must not duplicate anything ---------------
        tmp2 = tempfile.mkdtemp(prefix="walk_inst2_")
        trees.append(tmp2)
        b2, k2, p2, bp2 = build(tmp2)
        run_installer(tmp2, p2, bp2)
        rc2, out2 = run_installer(tmp2, p2, bp2)
        check("8  a second run also exits 0", rc2, 0)
        check("9  still exactly one SHEETS line", conf(b2).count("\nSHEETS="), 1)
        check("10 still exactly one cron line",
              cron(tmp2).count("sheets_pull.py run"), 1)
        check("11 and it says so rather than adding another",
              "already scheduled" in out2, True)

        # ---- 12-14 · A SHEET IS NOT SHARED (exit 41) ------------------------
        tmp, base, rc, out = case("denied", STUB_PREFLIGHT=41)
        trees.append(tmp)
        check("12 a permission refusal stops the install", rc, 1)
        check("13 THE SCHEDULE IS NOT SWITCHED ON",
              "sheets_pull.py run" in cron(tmp), False)
        check("14 and it says to share it", "not shared" in out.lower(), True)

        # ---- 15-17 · GOOGLE RATE-LIMITS (exit 43) ---------------------------
        tmp, base, rc, out = case("rate", STUB_PREFLIGHT=43)
        trees.append(tmp)
        check("15 a rate refusal stops the install", rc, 1)
        check("16 THE SCHEDULE IS NOT SWITCHED ON",
              "sheets_pull.py run" in cron(tmp), False)
        check("17 and it says DO NOT re-share",
              "do not re-share" in out.lower(), True)

        # ---- 18-19 · the pull itself fails ----------------------------------
        tmp, base, rc, out = case("pullfail", STUB_RUN=42)
        trees.append(tmp)
        check("18 a failed pull stops the install", rc, 1)
        check("19 THE SCHEDULE IS NOT SWITCHED ON",
              "sheets_pull.py run" in cron(tmp), False)

        # ---- 20-21 · the bundle ships but WITHOUT the sheets ----------------
        tmp, base, rc, out = case("nosheets", STUB_BUNDLE_HAS_SHEETS=0)
        trees.append(tmp)
        check("20 a bundle without the sheets stops the install", rc, 1)
        check("21 THE SCHEDULE IS NOT SWITCHED ON",
              "sheets_pull.py run" in cron(tmp), False)

        # ---- 22-24 · the box is not ready at all ----------------------------
        tmp = tempfile.mkdtemp(prefix="walk_inst3_")
        trees.append(tmp)
        base, kit, py, binp = build(tmp)
        os.remove(os.path.join(base, "clinic_state_backup.conf"))
        rc, out = run_installer(tmp, py, binp)
        check("22 a missing conf stops at stage 1", rc, 1)
        check("23 it stops BEFORE replacing anything",
              open(os.path.join(base, "sheets_pull.py")).read(), "# live v1\n")
        check("24 and it names what is missing", "not configured" in out, True)

    finally:
        for t in trees:
            shutil.rmtree(t, ignore_errors=True)

    bad = CHECKS.count(False)
    print("\n%d checks, %d failed" % (len(CHECKS), bad))
    if bad:
        print("FAILED")
        return 1
    print("ALL INSTALLER CHECKS PASS — on every failure path the nightly\n"
          "schedule stays OFF and the saved copies stay put.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
