#!/usr/bin/env python3
"""WALK_gas_install.py — S234_GAS_WEEKLY

Drives install.sh in a sandbox against a stand-in gas_export.py, and proves the
property that matters: any failure leaves the conf byte-identical, so the
nightly bundle and the weekly export both run exactly as they did before.

Offline. No Google, no live path, no crontab (CRON_ON=0 throughout).
"""
import os
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
INSTALL = os.path.join(HERE, "install.sh")
REAL = os.path.join(HERE, "gas_export.py")
GAS_LINE = os.path.join(HERE, "GAS_LINE.txt")

fails, n = [], [0]


def check(name, cond):
    n[0] += 1
    if not cond:
        fails.append(name)
        print("  FAIL  %s" % name)


STUB = r'''#!/usr/bin/env python3
"""Stand-in for gas_export.py, driven by marker files in the sandbox."""
import os, sys
sb = os.environ["SB"]
mode = sys.argv[1] if len(sys.argv) > 1 else ""
if mode == "selftest":
    if os.path.exists(os.path.join(sb, "SELFTEST_FAILS")):
        print("selftest: 9 checks, 2 failures"); sys.exit(1)
    print("selftest: 24 checks, 0 failures"); sys.exit(0)
if mode == "preflight":
    if os.path.exists(os.path.join(sb, "NOT_SHARED")):
        print("REFUSED (41): PERMISSION — DailyClinicReports could not be opened")
        sys.exit(41)
    print("3 of 3 project(s) reachable"); print("PREFLIGHT OK"); sys.exit(0)
if mode == "run":
    if os.path.exists(os.path.join(sb, "RUN_FAILS")):
        print("REFUSED (42): came back smaller"); sys.exit(42)
    d = os.path.join(os.environ["GAS_DIR"], "DailyClinicReports")
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "Code.gs"), "w").write("function a(){}\n")
    open(os.path.join(os.environ["GAS_DIR"], "_TAKEN_AT.json"), "w").write("{}")
    print("gas_export ok"); sys.exit(0)
if mode == "list":
    print("last export  now"); sys.exit(0)
sys.exit(0)
'''


def sandbox(with_line=True, real_script=False):
    sb = tempfile.mkdtemp(prefix="s234gas_")
    kit = os.path.join(sb, "kit")
    dest = os.path.join(sb, "state_backup")
    os.makedirs(kit)
    os.makedirs(dest)
    src = REAL if real_script else None
    p = os.path.join(kit, "gas_export.py")
    if src:
        shutil.copy(src, p)
    else:
        open(p, "w").write(STUB)
    os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC)
    if with_line:
        shutil.copy(GAS_LINE, os.path.join(kit, "GAS_LINE.txt"))
    conf = os.path.join(sb, "conf")
    with open(conf, "w") as fh:
        fh.write("SA_JSON=%s\n" % os.path.join(sb, "sa.json"))
        fh.write("SHEETS=1aaa:tracker,1bbb:audit\n")
    open(os.path.join(sb, "sa.json"), "w").write(
        '{"client_email":"clinic-backup@example.iam.gserviceaccount.com"}')
    return sb, kit, conf, dest


def run(sb, kit, conf, dest):
    env = dict(os.environ)
    env.update({"CONF": conf, "DEST": dest, "KIT_DIR": kit,
                "PY": sys.executable, "CRON_ON": "0", "SB": sb,
                "GAS_DIR": os.path.join(sb, "gas"),
                "LOG": os.path.join(sb, "g.log")})
    p = subprocess.run(["bash", INSTALL], env=env, capture_output=True,
                       text=True)
    return p.returncode, p.stdout + p.stderr


def main():
    print("WALK_gas_install — S234_GAS_WEEKLY")

    # 1 · the ordinary install
    sb, kit, conf, dest = sandbox()
    rc, out = run(sb, kit, conf, dest)
    check("install: exits 0", rc == 0)
    check("install: the script is in place",
          os.path.exists(os.path.join(dest, "gas_export.py")))
    check("install: exactly one GAS= line was added",
          sum(1 for l in open(conf) if l.startswith("GAS=")) == 1)
    check("install: the SHEETS= line is untouched",
          any(l.startswith("SHEETS=1aaa:tracker,1bbb:audit")
              for l in open(conf)))
    check("install: three projects are named",
          len([l for l in open(conf) if l.startswith("GAS=")][0].split(","))
          == 3)
    check("install: it prints the three lines and an undo",
          "md5:" in out and "projects:" in out and "To undo" in out)

    # 2 · a second run does not duplicate the line
    rc2, out2 = run(sb, kit, conf, dest)
    check("second run: exits 0", rc2 == 0)
    check("second run: still exactly one GAS= line",
          sum(1 for l in open(conf) if l.startswith("GAS=")) == 1)
    check("second run: says it left the line alone", "already there" in out2)
    shutil.rmtree(sb)

    # 3 · a project is not shared yet
    sb, kit, conf, dest = sandbox()
    open(os.path.join(sb, "NOT_SHARED"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, dest)
    check("not shared: stops, non-zero", rc != 0)
    check("not shared: THE CONF IS PUT BACK BYTE FOR BYTE",
          open(conf).read() == before)
    check("not shared: it names the service-account address",
          "clinic-backup@example.iam.gserviceaccount.com" in out)
    check("not shared: it distinguishes permission from rate in its advice",
          "RATE LIMIT" in out and "PERMISSION" in out)
    shutil.rmtree(sb)

    # 4 · a failing selftest is never installed
    sb, kit, conf, dest = sandbox()
    open(os.path.join(sb, "SELFTEST_FAILS"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, dest)
    check("selftest fails: stops, non-zero", rc != 0)
    check("selftest fails: nothing was copied into state_backup",
          not os.path.exists(os.path.join(dest, "gas_export.py")))
    check("selftest fails: the conf was never touched",
          open(conf).read() == before)
    shutil.rmtree(sb)

    # 5 · the export itself refuses
    sb, kit, conf, dest = sandbox()
    open(os.path.join(sb, "RUN_FAILS"), "w").write("")
    before = open(conf).read()
    rc, out = run(sb, kit, conf, dest)
    check("export refuses: stops, non-zero", rc != 0)
    check("export refuses: the conf is put back byte for byte",
          open(conf).read() == before)
    check("export refuses: it prints the line that removes the script",
          "rm -f" in out)
    shutil.rmtree(sb)

    # 6 · the kit is incomplete
    sb, kit, conf, dest = sandbox(with_line=False)
    before = open(conf).read()
    rc, out = run(sb, kit, conf, dest)
    check("no GAS_LINE.txt: stops before anything is done", rc != 0)
    check("no GAS_LINE.txt: the conf was never touched",
          open(conf).read() == before)
    shutil.rmtree(sb)

    # 7 · the REAL script's selftest passes when driven by the installer
    sb, kit, conf, dest = sandbox(real_script=True)
    env = dict(os.environ)
    p = subprocess.run([sys.executable,
                        os.path.join(kit, "gas_export.py"), "selftest"],
                       capture_output=True, text=True, env=env)
    both = p.stdout + p.stderr
    check("the real gas_export.py selftest passes, 0 failures",
          p.returncode == 0 and ", 0 failures" in p.stdout)
    check("the real selftest exercises the denylist and it refuses",
          "forbidden to touch" in both)
    shutil.rmtree(sb)

    # 8 · the shipped GAS line must not name a denied project
    line = open(GAS_LINE).read()
    check("GAS_LINE.txt names exactly three projects",
          len(line.split(",")) == 3)
    check("GAS_LINE.txt does NOT name the callback tracker",
          "148sj" not in line)
    check("GAS_LINE.txt labels match the S230 export folder names",
          all(x in line for x in ("DailyClinicReports",
                                  "ClinicAccountingReports",
                                  "UPIReconciliation")))

    print("")
    print("WALK_gas_install: %d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        print("  FAILED: %s" % f)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
