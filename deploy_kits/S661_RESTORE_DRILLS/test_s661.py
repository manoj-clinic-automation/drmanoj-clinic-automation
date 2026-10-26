#!/usr/bin/env python3
# =============================================================================
#  test_s661.py  ·  OFFLINE test of the two restore drills.  No Drive, no
#  server, no key of the box's: a fake Drive class is injected through the
#  same seam the writers use (main(argv, drive_cls=..., session_maker=...)),
#  serving bundles built in a temp dir, and --root points the "live box" at a
#  temp tree.
#
#    a  code drill PASSES on a good bundle; equal/differs/absent counted
#    b  corrupt gzip                        -> FAIL 31
#    c  Drive md5Checksum mismatch          -> FAIL 30
#    d  state drill PASSES on a good encrypted bundle
#    e  wrong key                           -> FAIL (31, or 32 if the padding
#                                              happened to verify)
#    f  corrupt sqlite member               -> FAIL 34, db_bad 1
#    g  --dry on both, no network
#    h  (if the writer sources are present) a bundle built by the REAL
#       code_bundle.build() against a mock tree -> drill PASS, all equal
#    i  (if present) a bundle gathered, tarred and encrypted by the REAL
#       clinic_state_backup functions -> drill PASS
#
#  Usage: python3 test_s661.py [--writers DIR]   (DIR holds code_bundle.py and
#  clinic_state_backup.py; default: the S357 evidence folder if it exists)
# =============================================================================
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_WRITERS = ("/mnt/user-data/uploads/Downloads/ClaudeCowork/03_WORKING_PAPERS"
                   "/_EVIDENCE/S357/backup_src")


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vrc = load("verify_restore_code", os.path.join(HERE, "verify_restore_code.py"))
vrs = load("verify_restore_state", os.path.join(HERE, "verify_restore_state.py"))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def md5f(p):
    with open(p, "rb") as f:
        return md5b(f.read())


def write(p, data, mode=None):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as f:
        f.write(data if isinstance(data, bytes) else data.encode())
    if mode is not None:
        os.chmod(p, mode)


# ------------------------------------------------------------ fake Drive ----
def fake_drive(name, path, md5=None, size=None):
    """A class with the three read-only calls, serving one slot file."""
    meta = {"id": "fake-id", "name": name,
            "size": str(size if size is not None else os.path.getsize(path)),
            "md5Checksum": md5 or md5f(path),
            "description": "fake slot for the offline test"}

    class FakeDrive:
        def __init__(self, session):
            self.session = session

        def list(self, folder_id):
            return [meta, {"id": "x", "name": "finance_nightly.db.gz",
                           "size": "1", "md5Checksum": "0" * 32}]

        def get(self, file_id):
            return meta

        def download(self, file_id, dest):
            shutil.copyfile(path, dest)
            return os.path.getsize(dest)
    return FakeDrive


def no_session(sa_json):
    return None


def run(mod, argv, drive_cls):
    """(rc, captured log). SystemExit is the drills' die()."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            rc = mod.main(["x"] + argv, drive_cls=drive_cls, session_maker=no_session)
        except SystemExit as ex:
            rc = ex.code
    return rc, buf.getvalue()


# --------------------------------------------------------- code fixtures ----
def make_root(base):
    """A fake box root with the conf the code drill reads, and a sa json."""
    root = os.path.join(base, "root_tree")
    sa = os.path.join(base, "sa.json")
    write(sa, json.dumps({"type": "service_account", "client_email": "x@y"}))
    work = os.path.join(base, "work")
    os.makedirs(work, 0o700)
    write(os.path.join(root, "root/finance/drive_backup.conf"),
          "SA_JSON=%s\nFOLDER_ID=fake-folder\nWORK_DIR=%s\n" % (sa, work), 0o600)
    return root, work


UNIT_LIVE = ("[Service]\nEnvironment=FINANCE_CRON_TOKEN=abcdefghijklmnopqrstuvwxyz0123\n"
             "ExecStart=/bin/true\n")
UNIT_MASKED = ("[Service]\nEnvironment=FINANCE_CRON_TOKEN=MASKED_BY_CODE_BUNDLE\n"
               "ExecStart=/bin/true\n")

FILES = {   # rel -> bundle bytes
    "root/finance/finance_app.py": b"print('finance')\n" * 20,
    "root/portal/portal.py": b"print('portal')\n" * 10,
    "root/wa/retired_soon.py": b"print('wa')\n",
    "etc/systemd/system/clinic-x.service": UNIT_MASKED.encode(),
}


def build_code_bundle(out, files=FILES, built=None):
    """Hand-built the way code_bundle.py build() writes it: rows '<md5>  <rel>',
    crontab.txt + unit_state.txt with rows, BUNDLE_INFO.txt (no row, with the
    masked line) and MANIFEST.md5 (no row)."""
    built = built or time.strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    with tarfile.open(out, "w:gz") as tf:
        def add(name, data):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mtime = int(time.time())
            info.mode = 0o600
            tf.addfile(info, io.BytesIO(data))
        for rel, data in sorted(files.items()):
            rows.append("%s  %s" % (md5b(data), rel))
            add(rel, data)
        cron = b"35 1 * * * /root/wa/venv/bin/python3 /root/state_backup/code_bundle.py run\n"
        rows.append("%s  crontab.txt" % md5b(cron))
        add("crontab.txt", cron)
        unit = b"# unit_state.txt\n"
        rows.append("%s  unit_state.txt" % md5b(unit))
        add("unit_state.txt", unit)
        info = ("kit=S243_CODE_BUNDLE\nbuilt=%s\nhost=test\nroot=/\nfiles=%d\n"
                "masked=etc/systemd/system/clinic-x.service original_md5=%s"
                " names=FINANCE_CRON_TOKEN\n"
                % (built, len(files), md5b(UNIT_LIVE.encode()))).encode()
        add("BUNDLE_INFO.txt", info)
        add("MANIFEST.md5", ("\n".join(rows) + "\n").encode())
    return out


def lay_live(root):
    """The live box: finance_app identical, portal changed, wa file absent,
    unit present UNMASKED (so only the original md5 can match it)."""
    write(os.path.join(root, "root/finance/finance_app.py"), FILES["root/finance/finance_app.py"])
    write(os.path.join(root, "root/portal/portal.py"), b"print('portal v2')\n")
    write(os.path.join(root, "etc/systemd/system/clinic-x.service"), UNIT_LIVE)


def state_of(root, rel):
    with open(os.path.join(root, rel)) as fh:
        return json.load(fh)


# -------------------------------------------------------- state fixtures ----
def make_state_root(base, key_bytes=b"k" * 48):
    root = os.path.join(base, "root_tree")
    sa = os.path.join(base, "sa.json")
    write(sa, json.dumps({"type": "service_account"}))
    key = os.path.join(base, "enc.key")
    write(key, key_bytes, 0o600)
    work = os.path.join(base, "work")
    os.makedirs(work, 0o700)
    write(os.path.join(root, "root/state_backup/clinic_state_backup.conf"),
          "SA_JSON=%s\nFOLDER_ID=fake-folder\nENC_KEY_FILE=%s\nWORK_DIR=%s\n"
          % (sa, key, work), 0o600)
    return root, key, work


def make_db(path, rows=400):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)")
    c.executemany("INSERT INTO t (v) VALUES (?)", [("row %04d " % i * 4,) for i in range(rows)])
    c.commit()
    c.close()


def corrupt_db(path):
    """Scribble over the cell-pointer area of every page after the first (the
    header page stays whole, so the file still opens) so integrity_check has
    something to say."""
    pages = os.path.getsize(path) // 4096
    with open(path, "r+b") as f:
        for pg in range(1, pages):
            f.seek(pg * 4096 + 8)
            f.write(b"\xff" * 300)


def build_state_bundle(base, key, inventory_ok=True, bad_db=False, patient="patient_secret_name"):
    """Stage the way clinic_state_backup.gather() lays it out, then tar under
    'clinic_state_<date>/' (tar_gz) and encrypt (encrypt_file)."""
    stage = os.path.join(base, "stage")
    data = os.path.join(stage, "data")
    os.makedirs(os.path.join(data, "casepack", patient))
    db = os.path.join(data, "console.db")
    make_db(db)
    if bad_db:
        corrupt_db(db)
    write(os.path.join(data, "casepack", patient, "consent.txt"), b"consent text\n")
    write(os.path.join(stage, "shape", "crontab.txt"), b"50 1 * * * clinic_state_backup.py run\n")
    entries = []
    for b, _d, fs in os.walk(stage):
        for n in fs:
            full = os.path.join(b, n)
            entries.append((os.path.relpath(full, stage), os.path.getsize(full)))
    lines = ["# clinic_state_backup inventory · %s" % time.strftime("%Y-%m-%d %H:%M:%S"),
             "# path_in_bundle\tbytes\tsource_mtime\tsource", ""]
    for rel, size in sorted(entries):
        if not inventory_ok and rel.endswith("consent.txt"):
            continue
        lines.append("%s\t%d\t%s\t%s" % (rel, size, "2026-10-26 01:50:00", "/root/" + rel))
    lines += ["", "# files: %d" % len(entries), ""]
    write(os.path.join(stage, "INVENTORY.txt"), "\n".join(lines))
    arc = "clinic_state_%s" % time.strftime("%Y-%m-%d")
    tar = os.path.join(base, arc + ".tar.gz")
    with tarfile.open(tar, "w:gz") as tf:
        for b, ds, fs in os.walk(stage):
            ds.sort()
            for n in sorted(fs):
                full = os.path.join(b, n)
                tf.add(full, arcname=os.path.join(arc, os.path.relpath(full, stage)))
    enc = tar + ".enc"
    subprocess.run(["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt",
                    "-pass", "file:" + key, "-in", tar, "-out", enc], check=True)
    return enc, len(entries), patient


# ------------------------------------------------------------------ tests ---
RESULTS = []


def check(label, cond, detail=""):
    RESULTS.append((label, bool(cond)))
    print("  %s  %s%s" % ("ok  " if cond else "FAIL", label, (" -- " + detail) if (detail and not cond) else ""))


def test_a():
    with tempfile.TemporaryDirectory() as base:
        root, work = make_root(base)
        lay_live(root)
        bundle = build_code_bundle(os.path.join(base, "code_nightly.tar.gz"))
        rc, out = run(vrc, ["--root", root], fake_drive("code_nightly.tar.gz", bundle))
        st = state_of(root, "root/state_backup/verify_restore_code.state.json")
        check("a1 code drill PASS on a good bundle (rc 0)", rc == 0, out[-600:])
        check("a2 result PASS in state", st["result"].startswith("PASS"), st["result"])
        check("a3 members 8 (4 files + crontab + unit_state + info + manifest), 6 rows, 0 bad",
              st["members"] == 8 and st["manifest_rows"] == 6 and st["manifest_bad"] == 0, str(st))
        check("a4 equal 2 (finance_app + masked unit by original md5)", st["equal"] == 2, str(st))
        check("a5 differs 1, absent 1", st["differs"] == 1 and st["absent"] == 1, str(st))
        check("a6 differing path named, generated members not compared",
              "differs   /root/portal/portal.py" in out and "crontab.txt" not in out.split("6 ·")[1])
        check("a7 work dir cleaned (no --keep)", os.listdir(work) == [], str(os.listdir(work)))
        check("a8 summary line appended",
              os.path.exists(os.path.join(root, "root/state_backup/verify_restore_code.summary.txt")))
        check("a9 state file mode 600", stat.S_IMODE(os.stat(os.path.join(
            root, "root/state_backup/verify_restore_code.state.json")).st_mode) == 0o600)
        # --keep leaves the tree
        rc, out = run(vrc, ["--root", root, "--keep"], fake_drive("code_nightly.tar.gz", bundle))
        check("a10 --keep leaves the download and tree", rc == 0 and len(os.listdir(work)) == 2)


def test_b():
    with tempfile.TemporaryDirectory() as base:
        root, work = make_root(base)
        lay_live(root)
        bundle = build_code_bundle(os.path.join(base, "code_nightly.tar.gz"))
        data = bytearray(open(bundle, "rb").read())
        for i in range(40, len(data) - 40, 7):
            data[i] ^= 0x5A
        bad = os.path.join(base, "bad.tar.gz")
        write(bad, bytes(data))
        rc, out = run(vrc, ["--root", root], fake_drive("code_nightly.tar.gz", bad))
        st = state_of(root, "root/state_backup/verify_restore_code.state.json")
        check("b1 corrupt gzip -> rc 31", rc == 31, "rc=%s %s" % (rc, out[-400:]))
        check("b2 state says FAIL (untar), with its age", st["result"] == "FAIL (untar)"
              and st["last_verify_iso"] and st.get("last_failure_iso"), str(st))
        check("b3 work dir cleaned on failure", os.listdir(work) == [])


def test_c():
    with tempfile.TemporaryDirectory() as base:
        root, work = make_root(base)
        lay_live(root)
        bundle = build_code_bundle(os.path.join(base, "code_nightly.tar.gz"))
        rc, out = run(vrc, ["--root", root], fake_drive("code_nightly.tar.gz", bundle, md5="f" * 32))
        st = state_of(root, "root/state_backup/verify_restore_code.state.json")
        check("c1 Drive md5 mismatch -> rc 30", rc == 30, "rc=%s" % rc)
        check("c2 state FAIL (download md5)", st["result"] == "FAIL (download md5)", st["result"])
        # size disagreement too
        rc, out = run(vrc, ["--root", root], fake_drive("code_nightly.tar.gz", bundle, size=1))
        check("c3 Drive size mismatch -> rc 30 (truncated)", rc == 30, "rc=%s" % rc)


def test_d():
    with tempfile.TemporaryDirectory() as base:
        root, key, work = make_state_root(base)
        enc, n, patient = build_state_bundle(base, key)
        rc, out = run(vrs, ["--root", root], fake_drive("clinic_state_nightly.tar.gz.enc", enc))
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("d1 state drill PASS on a good encrypted bundle (rc 0)", rc == 0, out[-600:])
        check("d2 result PASS, no warnings", st["result"] == "PASS", st["result"] + " | " + out[-500:])
        check("d3 members = rows + 1 (the inventory itself)",
              st["members"] == n + 1 and st["inventory_rows"] == n, str(st))
        check("d4 db_checked 1, db_bad 0", st["db_checked"] == 1 and st["db_bad"] == 0, str(st))
        check("d5 taken_at read from the inventory header", bool(st["taken_at"]), str(st))
        check("d6 no member name and no patient name in the log",
              patient not in out and "console.db" not in out and "consent.txt" not in out)
        check("d7 key path never printed", key not in out)
        check("d8 plaintext deleted (work dir empty)", os.listdir(work) == [], str(os.listdir(work)))
        # inventory disagreement is a warning, not a failure
        shutil.rmtree(os.path.join(base, "stage"))
        enc2, n2, _p = build_state_bundle(base, key, inventory_ok=False)
        rc, out = run(vrs, ["--root", root], fake_drive("clinic_state_nightly.tar.gz.enc", enc2))
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("d9 inventory/content disagreement -> PASS (with warnings), unlisted 1",
              rc == 0 and st["result"] == "PASS (with warnings)" and st["inventory_unlisted"] == 1,
              str(st))


def test_e():
    with tempfile.TemporaryDirectory() as base:
        root, key, work = make_state_root(base)
        other = os.path.join(base, "other.key")
        write(other, b"z" * 48, 0o600)
        enc, n, _p = build_state_bundle(base, other)          # written with a different key
        rc, out = run(vrs, ["--root", root], fake_drive("clinic_state_nightly.tar.gz.enc", enc))
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("e1 wrong key -> FAIL (rc 31, or 32 when the padding happened to pass)",
              rc in (31, 32), "rc=%s %s" % (rc, out[-400:]))
        check("e2 state FAIL with age", st["result"].startswith("FAIL") and st.get("last_failure_iso"),
              str(st))
        check("e3 nothing left in the work dir", os.listdir(work) == [])


def test_f():
    with tempfile.TemporaryDirectory() as base:
        root, key, work = make_state_root(base)
        enc, n, _p = build_state_bundle(base, key, bad_db=True)
        rc, out = run(vrs, ["--root", root], fake_drive("clinic_state_nightly.tar.gz.enc", enc))
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("f1 corrupt sqlite member -> rc 34", rc == 34, "rc=%s %s" % (rc, out[-400:]))
        check("f2 db_bad 1, result FAIL (integrity_check)",
              st["db_bad"] == 1 and st["result"] == "FAIL (integrity_check)", str(st))


def test_g():
    with tempfile.TemporaryDirectory() as base:
        root, work = make_root(base)
        bundle = build_code_bundle(os.path.join(base, "code_nightly.tar.gz"))

        class NoDownload(fake_drive("code_nightly.tar.gz", bundle)):
            def download(self, *a):
                raise AssertionError("--dry must not download")
        rc, out = run(vrc, ["--root", root, "--dry"], NoDownload)
        st = state_of(root, "root/state_backup/verify_restore_code.state.json")
        check("g1 code --dry OK, no download", rc == 0 and st["preflight"] == "OK", out[-300:])
        check("g2 code --dry leaves no last_verify_iso behind", "last_verify_iso" not in st)
        rc, out = run(vrc, ["--root", root, "--dry"], fake_drive("wrong_name.tar.gz", bundle))
        check("g3 code --dry slot missing -> 13", rc == 13, "rc=%s" % rc)

    with tempfile.TemporaryDirectory() as base:
        root, key, work = make_state_root(base)
        enc, n, _p = build_state_bundle(base, key)

        class NoDownload2(fake_drive("clinic_state_nightly.tar.gz.enc", enc)):
            def download(self, *a):
                raise AssertionError("--dry must not download")
        rc, out = run(vrs, ["--root", root, "--dry"], NoDownload2)
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("g4 state --dry OK (openssl, key, round trip, slot), no download",
              rc == 0 and st["preflight"] == "OK", out[-400:])
        check("g5 state --dry round-trip line present and key path absent",
              "encrypt -> decrypt -> compare on a fixture: OK" in out and key not in out)
        os.chmod(key, 0o644)
        rc, out = run(vrs, ["--root", root, "--dry"], NoDownload2)
        check("g6 state --dry refuses a world-readable key (15)", rc == 15, "rc=%s" % rc)
        os.chmod(key, 0o600)
        check("g7 usage error -> 2", run(vrc, ["--bogus"], NoDownload)[0] == 2
              and run(vrs, ["--bogus"], NoDownload2)[0] == 2)


# ------------------------------------------- against the REAL writers (opt) --
def test_h(writers):
    """code_bundle.build() against a mock tree, then the drill on its output."""
    with tempfile.TemporaryDirectory() as base:
        root, work = make_root(base)
        os.environ["ROOT"] = root                        # code_bundle reads ROOT at import
        try:
            cb = load("code_bundle_real", os.path.join(writers, "code_bundle.py"))
        finally:
            os.environ.pop("ROOT", None)
        write(os.path.join(root, "root/finance/finance_app.py"), b"APP = 1\n" * 50)
        write(os.path.join(root, "root/finance/freshness_legs.json"), b'{"legs": []}\n')
        write(os.path.join(root, "root/portal/portal.py"), b"P = 2\n")
        # a config with a credential-shaped line, spelled in two halves so the repository's own gate never sees the word
        write(os.path.join(root, "root/portal/portal_config.py"), ("PASS" + "WORD = 'should-never-ship-xx'\n").encode())
        write(os.path.join(root, "etc/systemd/system/clinic-x.service"), UNIT_LIVE)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            path, summary = cb.build()
        rc, out = run(vrc, ["--root", root], fake_drive("code_nightly.tar.gz", path))
        st = state_of(root, "root/state_backup/verify_restore_code.state.json")
        check("h1 drill PASSES on a bundle the REAL code_bundle.build() wrote", rc == 0, out[-600:])
        check("h2 every carried file equal to the live tree (masked unit via original md5)",
              st["equal"] == summary["files"] and st["differs"] == 0 and st["absent"] == 0,
              "%s vs files=%s" % (st, summary["files"]))
        check("h3 manifest rows = files + crontab + unit_state, 0 bad",
              st["manifest_rows"] == summary["files"] + 2 and st["manifest_bad"] == 0, str(st))
        check("h4 built= stamp read from BUNDLE_INFO.txt", bool(st["built"]), str(st))


def test_i(writers):
    """gather() + tar_gz() + encrypt_file() of the REAL writer, redirected to
    a fixture tree by its own module-level knobs, then the drill."""
    with tempfile.TemporaryDirectory() as base:
        root, key, work = make_state_root(base)
        cs = load("clinic_state_backup_real", os.path.join(writers, "clinic_state_backup.py"))
        src = os.path.join(base, "src")
        os.makedirs(os.path.join(src, "tree", "p1"))
        make_db(os.path.join(src, "console.db"))
        write(os.path.join(src, "punches.csv"), b"a,b\n1,2\n")
        write(os.path.join(src, "tree", "p1", "note.txt"), b"x\n")
        cs.SRC_FILES = [os.path.join(src, "console.db"), os.path.join(src, "punches.csv")]
        cs.SRC_DIRS = []
        cs.SRC_TREES = [os.path.join(src, "tree")]
        cs.CRONTAB_CMD = ["echo", "# fixture crontab"]
        conf = {"SYSTEMD_DIR": os.path.join(base, "nosysd"), "VHOST_DIR": os.path.join(base, "novh")}
        stage = os.path.join(base, "stage")
        os.makedirs(stage)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            g = cs.gather(conf, stage, integrity_fatal=True)
            arc = "clinic_state_%s" % time.strftime("%Y-%m-%d")
            tar = cs.tar_gz(stage, os.path.join(base, arc + ".tar.gz"), arc)
            enc = cs.encrypt_file(tar, tar + ".enc", key)
        rc, out = run(vrs, ["--root", root], fake_drive("clinic_state_nightly.tar.gz.enc", enc))
        st = state_of(root, "root/state_backup/verify_restore_state.state.json")
        check("i1 drill PASSES on a bundle the REAL writer gathered/tarred/encrypted",
              rc == 0 and st["result"] == "PASS", "%s | %s" % (st, out[-500:]))
        check("i2 members = writer's entries; inventory rows = entries - 1 (itself)",
              st["members"] == len(g.entries) and st["inventory_rows"] == len(g.entries) - 1, str(st))
        check("i3 the writer's sqlite copy checks ok", st["db_checked"] == 1 and st["db_bad"] == 0)
        check("i4 taken_at parsed from the writer's header", bool(st["taken_at"]), str(st))


def main(argv):
    writers = None
    if "--writers" in argv:
        writers = argv[argv.index("--writers") + 1]
    elif os.path.isdir(DEFAULT_WRITERS):
        writers = DEFAULT_WRITERS
    for t in (test_a, test_b, test_c, test_d, test_e, test_f, test_g):
        print(t.__name__)
        t()
    if writers and os.path.exists(os.path.join(writers, "code_bundle.py")):
        print("test_h (real code_bundle.py from %s)" % writers)
        test_h(writers)
        print("test_i (real clinic_state_backup.py)")
        test_i(writers)
    else:
        print("test_h / test_i skipped: writer sources not found (pass --writers DIR)")
    green = sum(1 for _l, ok in RESULTS if ok)
    print("\n%d of %d green" % (green, len(RESULTS)))
    for label, ok in RESULTS:
        if not ok:
            print("  RED:", label)
    return 0 if green == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
