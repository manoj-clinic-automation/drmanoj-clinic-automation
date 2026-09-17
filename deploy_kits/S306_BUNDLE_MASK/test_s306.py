#!/usr/bin/env python3
"""test_s306.py -- S306 (F-518) proof for code_bundle.py v1.4. Never prints a secret value.
Usage: python3 test_s306.py <dir holding the NEW code_bundle.py> <a ROOT to build from> [<dir holding the OLD code_bundle.py>]
With a real ROOT (the box, or an extracted nightly bundle) it builds into a temp folder only -- no network, no Drive,
and the live local copy /root/state_backup/code_nightly.tar.gz is never touched."""
import hashlib
import importlib.util
import os
import re
import sys
import tarfile
import tempfile

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def load(path, root, out_dir, tag):
    os.environ["ROOT"] = root
    spec = importlib.util.spec_from_file_location("cb_%s" % tag, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    m.OUT_DIR = out_dir
    m.OUT_PATH = os.path.join(out_dir, m.SLOT)
    m.capture_crontab = lambda: ("# crontab not captured in the test\n", True)
    return m


def members(path):
    out = {}
    with tarfile.open(path, "r:gz") as tf:
        for mem in tf.getmembers():
            if mem.isfile():
                out[mem.name] = tf.extractfile(mem).read()
    return out


def main():
    new_dir, root = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    old_dir = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else ""
    tmp = tempfile.mkdtemp(prefix="s306_")
    cb = load(os.path.join(new_dir, "code_bundle.py"), root, os.path.join(tmp, "new"), "new")
    # ---- the masker on its own ----------------------------------------------------------------
    t = ("[Service]\nEnvironment=APP_DB=/root/x.db\nEnvironment=APP_CRON_TOKEN=abcdefghijklmnopqrstuvwxyz0123456789ABCD\n"
         'Environment="HOOK_SECRET=zzzzzzzzzzzzzzzzzzzz" "PORT=8106"\n'
         "Environment=API_KEY=kkkkkkkkkkkkkkkkkkkk OTHER=plain\nEnvironmentFile=/root/wa/app.env\n"
         "# Environment=OLD_TOKEN=cccccccccccccccccccccc\nEnvironment=DB_PASSWORD=pppppppppppppppp\n"
         "Environment=PORTAL_LOGIN=https://example/login\nEnvironment=SSO_KEYRING_DIR=\n")
    mt, names = cb.mask_unit_text(t)
    check("names masked, in order", names == ["APP_CRON_TOKEN", "HOOK_SECRET", "API_KEY", "DB_PASSWORD"])
    check("no masked value survives", not any(v in mt for v in ("abcdefghijklmnop", "zzzzzzzz", "kkkkkkkk", "pppppppp")))
    check("names kept", all(("%s=MASKED_BY_CODE_BUNDLE" % n) in mt for n in names))
    check("quotes kept", '"HOOK_SECRET=MASKED_BY_CODE_BUNDLE" "PORT=8106"' in mt)
    check("non-secret values untouched", "APP_DB=/root/x.db" in mt and "OTHER=plain" in mt
          and "PORTAL_LOGIN=https://example/login" in mt)
    check("EnvironmentFile untouched", "EnvironmentFile=/root/wa/app.env" in mt)
    check("a commented line untouched", "# Environment=OLD_TOKEN=cccccccccccccccccccccc" in mt)
    check("an empty value is not a secret", "SSO_KEYRING_DIR=\n" in mt)
    check("every other line byte-identical", len(mt.split("\n")) == len(t.split("\n")))
    check("idempotent", cb.mask_unit_text(mt) == (mt, []))
    check("guard: unmasked text is caught", cb.unit_secret_left(t) is True)
    check("guard: masked text passes", cb.unit_secret_left(mt) is False)
    # ---- a full build from ROOT ---------------------------------------------------------------
    path, summ = cb.build()
    got = members(path)
    check("the build verifies against its own manifest", cb.verify_tarball(path) == [])
    unit_dir = os.path.join(root, "etc/systemd/system")
    secrets = []                                           # the real values, held in memory only
    masked_files = 0
    for name in sorted(os.listdir(unit_dir)) if os.path.isdir(unit_dir) else []:
        rel = "etc/systemd/system/" + name
        if rel not in got:
            continue
        raw = open(os.path.join(unit_dir, name), encoding="utf-8", errors="ignore").read()
        for line in raw.split("\n"):
            mm = cb._ENV_LINE.match(line)
            if mm:
                for p in cb._ENV_PAIR.finditer(mm.group(2)):
                    if p.group(3) and cb.UNIT_SECRET_NAME.search(p.group(2)):
                        secrets.append(p.group(3))
        if cb.unit_secret_left(raw):
            masked_files += 1
            info = got["BUNDLE_INFO.txt"].decode()
            om = hashlib.md5(open(os.path.join(unit_dir, name), "rb").read()).hexdigest()
            check("%s: BUNDLE_INFO records its original md5" % name, ("masked=%s original_md5=%s" % (rel, om)) in info)
    blob = b"".join(got.values())
    check("no secret value from any unit is anywhere in the bundle (%d values held)" % len(secrets),
          not any(s.encode() in blob for s in secrets if len(s) >= 8))
    check("the closing guard finds nothing", cb.units_with_secret(path) == [])
    check("BUNDLE_INFO names but never values", all(s not in got["BUNDLE_INFO.txt"].decode() for s in secrets if len(s) >= 8))
    if old_dir:
        ob = load(os.path.join(old_dir, "code_bundle.py"), root, os.path.join(tmp, "old"), "old")
        opath, osumm = ob.build()
        old = members(opath)
        check("same members as v1.3", sorted(old) == sorted(got))
        changed = sorted(k for k in got if k not in ("BUNDLE_INFO.txt", "MANIFEST.md5") and got[k] != old[k])
        check("only masked unit files differ from v1.3 (%s)" % ",".join(c.split("/")[-1] for c in changed),
              len(changed) == masked_files and all(c.startswith("etc/systemd/system/") for c in changed))
        check("v1.3 DID carry the values (the fault is real on this ROOT)" if secrets else "no unit secrets on this ROOT",
              (any(s.encode() in b"".join(old.values()) for s in secrets if len(s) >= 8)) if secrets else True)
    # ---- the guard refuses to ship --------------------------------------------------------------
    cb2 = load(os.path.join(new_dir, "code_bundle.py"), root, os.path.join(tmp, "neg"), "neg")
    cb2.mask_unit_text = lambda text: (text, [])
    if secrets:
        try:
            cb2.build()
            check("with masking switched off the guard must refuse", False)
        except SystemExit as e:
            check("with masking switched off the guard refuses (exit 23)", e.code == 23)
        check("and nothing was written", not os.path.exists(cb2.OUT_PATH))
    print("TEST OK — %d checks; %d unit file(s) masked, %d value(s) kept off the bundle; files=%d"
          % (N[0], masked_files, len(secrets), summ["files"]))


if __name__ == "__main__":
    main()
