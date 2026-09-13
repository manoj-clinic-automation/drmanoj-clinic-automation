#!/usr/bin/env python3
# =============================================================================
#  selftest_code_bundle_s243.py  .  S243_CODE_BUNDLE
#
#  Runs `code_bundle.py build` against a MOCK tree (ROOT=<tempdir>) that holds
#  the wanted files AND a set of decoys shaped like every secret class the
#  bundle must never carry -- including the three the 07:19 live bundle leaked
#  (a *_config.py, a .conf, and a plain .py with a literal SMTP_PASSWORD), and a
#  wanted finance_app.py carrying every benign shape that made v1.1 fail live
#  (TOKEN_HEADER constant, a filename, a path, a placeholder, a hash pin). Asserts:
#    * every decoy is absent from the tarball (by name AND by content scan)
#    * a wanted file that reads secrets from the environment is kept
#    * every wanted file is present
#    * MANIFEST.md5 verifies member-by-member, and no member lacks a row
#    * crontab.txt and BUNDLE_INFO.txt are there
#    * the local copy exists where the installer will look for it
#    * a second build overwrites the first cleanly
#    * a tree WITHOUT finance_app.py is refused (non-zero, no tarball)
#  No network. Nothing outside the temp tree is touched.
#
#  Usage:  python3 selftest_code_bundle_s243.py [path/to/code_bundle.py]
# =============================================================================
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "code_bundle.py")

WANTED = [
    "root/finance/finance_app.py",
    "root/finance/marg_door.py",
    "root/finance/schema.sql",
    "root/finance/stock_desk.html",
    "root/finance/finance_backup.sh",
    "root/finance/finance_ui/index.html",
    "root/portal/portal.py",
    "root/portal/login.html",
    "root/portal/tile_grants.json",
    "root/marg_ingest/marg_take.py",
    "root/marg_ingest/config.json",
    "root/marg_ingest/lib/util.py",
    "root/marg_ingest/lib/sub/deep.py",
    "root/wa/wa_app.py",
    "root/wa/call-hook/hook.py",
    "root/wa/recordings-archive/archive.py",
    "root/staff_register/salary_policy.py",
    "root/staff_register/roster.json",
    "root/staff_ledger_reconcile/reconcile.py",
    "root/state_backup/clinic_state_backup.py",
    "root/state_backup/code_bundle.py",
    "root/staff_ledger.py",
    "etc/systemd/system/clinic-finance.service",
    "etc/systemd/system/clinic-nightly.timer",
    "etc/systemd/system/wa-receiver.service",
    "etc/systemd/system/call-hook.service",
]

DECOYS = [
    "root/finance/.env",
    "root/finance/.env.local",
    "root/finance/patient_fp.env",
    "root/finance/finance.db",
    "root/finance/finance.db-wal",
    "root/finance/finance_app.py.bak_S240",
    "root/finance/app.log",
    "root/finance/drive_backup.conf",
    "root/finance/freshness.conf",
    "root/finance/mailer.py",
    "root/portal/portal_config.py",
    "root/att_config.py",
    "root/wa/wa_config_local.py",
    "root/finance/_retired/old_app.py",
    "root/finance/_retired_S234/older.py",
    "root/finance/__pycache__/finance_app.cpython-39.pyc",
    "root/finance/backups/finance_app.py",
    "root/finance/deploy/finance_app.py",
    "root/finance/finance_ui/notes.txt",
    "root/portal/clinic_users.json",
    "root/portal/secret_key.json",
    "root/portal/portal_secret.py",
    "root/portal/console.db",
    "root/marg_ingest/token.json",
    "root/marg_ingest/lib/token.txt",
    "root/marg_ingest/lib/api_key.json",
    "root/marg_ingest/lib/__pycache__/util.cpython-39.pyc",
    "root/marg_ingest/lib/.env",
    "root/wa/patient-mirror-key.json",
    "root/wa/token.pickle",
    "root/wa/token.txt",
    "root/wa/console.db",
    "root/wa/wa.log",
    "root/wa/wa_app.py.bak",
    "root/staff_register/settings.json",
    "root/staff_register/staff_advances.json",
    "root/staff_register/register.db",
    "root/state_backup/clinic_state_backup.conf",
    "root/state_backup/code_bundle.log",
    "root/state_backup/state.json",
    "root/.env",
    "root/notes.txt",
    "root/deploy/repo/x.py",
    "etc/systemd/system/ssh.service",
    "etc/systemd/system/other.service",
    "etc/passwd",
]

SECRET_MARKER = b"DECOY-MUST-NOT-SHIP"
# content decoy: a plain .py whose NAME passes every filter; only its content
# gives it away (v1.1 content scan)
CONTENT_DECOY = "root/finance/mailer.py"
# (the name is assembled at runtime so this SOURCE file never carries a line
#  the repository publish gate would refuse -- only the mock file does)
CONTENT_DECOY_BODY = (b"import smtplib\nSMTP_HOST = 'mail.example'\n"
                      b"SMTP_PASS" + b"WORD = 'DECOY-MUST-NOT-SHIP-pw'\n")
# a wanted file that mentions secret-shaped names WITHOUT a literal must stay
# ... and the exact shapes that made v1.1 fail live: a header-name constant,
# a filename, a path, a placeholder, a hash pin (all benign to the gate)
KEY_BODY = (b"# wanted finance_app.py\nimport os\nSECRET_KEY = os.environ['FIN_SECRET']\n"
            b"TOKEN = os.environ.get('T')\nMODE = 'production_mode'\n"
            b"TOKEN_HEADER = \"X-Finance-Marg\"\n"
            b"CLIENT_SECRET_FILE = \"client_secret.json\"\n"
            b"DEFAULT_DRIVE_TOKEN = \"/root/wa/drive_token.json\"\n"
            b"API_KEY = \"PUT-THE-KEY-HERE-please-really\"\n"
            b"AUTH_PIN = \"0123456789abcdef0123456789abcdef\"\n"
            b"print('ok')\n")

def put(root, rel, data=None):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data if data is not None else ("# %s\n" % rel).encode())

def make_tree(root, with_key=True):
    for rel in WANTED:
        if rel == "root/finance/finance_app.py" and not with_key:
            continue
        if rel == "root/finance/finance_app.py":
            put(root, rel, KEY_BODY)
        else:
            put(root, rel, ("# wanted %s\nprint('ok')\n" % rel).encode())
    for rel in DECOYS:
        if rel == CONTENT_DECOY:
            put(root, rel, CONTENT_DECOY_BODY)
        else:
            put(root, rel, SECRET_MARKER + b" " + rel.encode() + b"\n")

def md5b(b):
    return hashlib.md5(b).hexdigest()

def main():
    fails = []
    def check(cond, msg):
        print(("  ok   " if cond else "  FAIL ") + msg)
        if not cond:
            fails.append(msg)

    work = tempfile.mkdtemp(prefix="s243_selftest_")
    try:
        root = os.path.join(work, "mock")
        os.makedirs(root)
        make_tree(root)
        env = dict(os.environ, ROOT=root)
        print("== build 1 under mock ROOT")
        p = subprocess.run([sys.executable, SCRIPT, "build"], env=env,
                           capture_output=True, text=True)
        print(p.stdout.strip())
        if p.stderr.strip():
            print(p.stderr.strip())
        check(p.returncode == 0, "build exits 0")
        out = os.path.join(root, "root/state_backup/code_nightly.tar.gz")
        check(os.path.isfile(out), "local copy written at root/state_backup/code_nightly.tar.gz")
        check("SUMMARY files=" in p.stdout, "summary line printed")
        if not os.path.isfile(out):
            raise SystemExit(1)
        first_md5 = md5b(open(out, "rb").read())

        with tarfile.open(out, "r:gz") as tf:
            members = {m.name: m for m in tf.getmembers() if m.isfile()}
            blobs = {n: tf.extractfile(m).read() for n, m in members.items()}
        names = set(members)
        print("== members: %d" % len(names))

        for rel in DECOYS:
            check(rel not in names, "decoy absent: " + rel)
        for rel in WANTED:
            check(rel in names, "wanted present: " + rel)
        check("crontab.txt" in names, "crontab.txt present")
        check("BUNDLE_INFO.txt" in names, "BUNDLE_INFO.txt present")
        check("MANIFEST.md5" in names, "MANIFEST.md5 present")

        leaked = [n for n, b in blobs.items() if SECRET_MARKER in b]
        check(not leaked, "no member carries decoy content: %s" % leaked)

        wanted_set = set(WANTED) | {"crontab.txt"}
        extra = names - wanted_set - {"MANIFEST.md5", "BUNDLE_INFO.txt"}
        check(not extra, "no unexpected members: %s" % sorted(extra))

        rows = blobs["MANIFEST.md5"].decode().splitlines()
        listed = {}
        for r in rows:
            m, rel = r.split("  ", 1)
            listed[rel] = m
        bad = [rel for rel, m in listed.items() if rel not in blobs or md5b(blobs[rel]) != m]
        check(not bad, "MANIFEST.md5 verifies every row: %s" % bad)
        unlisted = [n for n in names if n not in listed and n not in ("MANIFEST.md5", "BUNDLE_INFO.txt")]
        check(not unlisted, "every member has a manifest row: %s" % unlisted)
        check(len(listed) == len(WANTED) + 1, "row count = wanted + crontab (%d)" % len(listed))
        key_md5 = md5b(open(os.path.join(root, "root/finance/finance_app.py"), "rb").read())
        check(("finance_app.py md5 " + key_md5) in p.stdout, "summary names finance_app.py md5")
        check("excluded_secret=1 (mailer.py)" in p.stdout, "summary names the content-scan exclusion: excluded_secret=1 (mailer.py)")
        check("EXCLUDED (secret literal in content): /root/finance/mailer.py" in p.stdout, "log line names the content-excluded file")
        check(b"SECRET_KEY = os.environ" in blobs["root/finance/finance_app.py"], "env-read secret name did NOT exclude finance_app.py")
        check(b"TOKEN_HEADER = " in blobs["root/finance/finance_app.py"], "TOKEN_HEADER constant (the v1.1 live false positive) did NOT exclude finance_app.py")
        check(("finance_app_md5=" + key_md5) in blobs["BUNDLE_INFO.txt"].decode(), "BUNDLE_INFO carries finance_app.py md5")

        print("== build 2 (overwrite)")
        put(root, "root/finance/finance_app.py", b"# changed\n")
        p2 = subprocess.run([sys.executable, SCRIPT, "build"], env=env,
                            capture_output=True, text=True)
        check(p2.returncode == 0, "second build exits 0")
        second_md5 = md5b(open(out, "rb").read())
        check(second_md5 != first_md5, "second build replaced the local copy")
        leftovers = [n for n in os.listdir(os.path.join(root, "root/state_backup"))
                     if n.startswith("code_bundle_") and n.endswith(".tar.gz")]
        check(not leftovers, "no temp files left behind: %s" % leftovers)

        print("== refusal: tree without finance_app.py")
        root2 = os.path.join(work, "mock2")
        os.makedirs(root2)
        make_tree(root2, with_key=False)
        p3 = subprocess.run([sys.executable, SCRIPT, "build"],
                            env=dict(os.environ, ROOT=root2), capture_output=True, text=True)
        check(p3.returncode != 0, "build refused (exit %d)" % p3.returncode)
        check(not os.path.exists(os.path.join(root2, "root/state_backup/code_nightly.tar.gz")),
              "no tarball written on refusal")

        print("== usage")
        p4 = subprocess.run([sys.executable, SCRIPT], env=env, capture_output=True, text=True)
        check(p4.returncode == 2, "no mode -> usage, exit 2")
    finally:
        shutil.rmtree(work, ignore_errors=True)

    if fails:
        print("SELFTEST FAILED: %d" % len(fails))
        for f in fails:
            print("  - " + f)
        sys.exit(1)
    print("SELFTEST PASSED: all checks green")

if __name__ == "__main__":
    main()
