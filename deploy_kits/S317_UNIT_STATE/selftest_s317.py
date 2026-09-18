#!/root/wa/venv/bin/python3
# =============================================================================
#  selftest_s317.py  ·  S317_UNIT_STATE  ·  v1
#
#  Proves the patch on a COPY of the live code_bundle.py, against a FAKE ROOT
#  tree in /tmp. It never touches /root/state_backup, never reaches Drive, and
#  never asks the real systemd anything except in the two stubbed checks, where
#  subprocess.run is replaced.
#
#  WHAT IS PROVED
#    the patch applies and the result compiles · the built tarball carries
#    unit_state.txt · its manifest row matches its bytes · the tarball still
#    verifies against its own manifest · the enable symlinks are listed with
#    their targets · an enabled unit reads wants-link=yes and a disabled one no
#    · with ROOT not "/" the two systemctl columns read not-asked and the file
#    says so · every member the UNPATCHED build carried is still carried, the
#    difference being exactly unit_state.txt · BUNDLE_INFO records the capture
#    · a unit's Environment= VALUE never reaches unit_state.txt · the live
#    branch reports systemctl's words, including when systemctl exits non-zero,
#    and says "unavailable" when there is no systemctl at all · an unlistable
#    /etc/systemd/system is a note in the file, not a failed bundle.
#
#  NEGATIVE CONTROLS (each must turn a green check red):
#    a manifest row removed for the new member  -> verify_tarball must object
#    capture_wants forced to raise OSError      -> ok False and a "# ... could
#                                                  not be listed" line
# =============================================================================
import importlib.util
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIVE = "/root/state_backup/code_bundle.py"
OK, BAD = [], []


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, root):
    os.environ["ROOT"] = root
    spec = importlib.util.spec_from_file_location("cb_%d" % len(sys.modules), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fake_tree(base):
    """A small root: one finance file (the bundle refuses without it), three
    unit files, and two enable symlinks -- one of the three is NOT enabled."""
    os.makedirs(os.path.join(base, "root", "finance"), exist_ok=True)
    with open(os.path.join(base, "root", "finance", "finance_app.py"), "w") as fh:
        fh.write("# a stand-in for the real thing\nprint('hello')\n")
    ud = os.path.join(base, "etc", "systemd", "system")
    os.makedirs(os.path.join(ud, "timers.target.wants"), exist_ok=True)
    os.makedirs(os.path.join(ud, "multi-user.target.wants"), exist_ok=True)
    for name, body in (
        ("clinic-alpha.service", "[Service]\nExecStart=/bin/true\nEnvironment=API_TOKEN=sup3rsecretvalue\n"),
        ("clinic-alpha.timer", "[Timer]\nOnCalendar=*-*-* 01:35\n"),
        ("clinic-ghost.timer", "[Timer]\nOnCalendar=*-*-* 04:00\n"),
    ):
        with open(os.path.join(ud, name), "w") as fh:
            fh.write(body)
    os.symlink(os.path.join(ud, "clinic-alpha.timer"),
               os.path.join(ud, "timers.target.wants", "clinic-alpha.timer"))
    os.symlink(os.path.join(ud, "clinic-alpha.service"),
               os.path.join(ud, "multi-user.target.wants", "clinic-alpha.service"))


def members(path):
    with tarfile.open(path, "r:gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}


def main(argv):
    src = LIVE
    for a in argv[1:]:
        if a.startswith("--file="):
            src = a.split("=", 1)[1]
    if not os.path.isfile(src):
        print("RED -- %s is not there" % src)
        return 3
    sys.path.insert(0, HERE)
    import patch_code_bundle_s317 as P

    tmp = tempfile.mkdtemp(prefix="s317_")
    plain = os.path.join(tmp, "plain.py")
    patched = os.path.join(tmp, "patched.py")
    shutil.copy2(src, plain)
    with open(src, "r", encoding="utf-8") as fh:
        text = fh.read()
    new, msgs = P.apply_to_text(text)
    check("the patch applies to this file", new is not None and new != text)
    if new is None:
        print("   ".join(msgs))
        return 4
    with open(patched, "w", encoding="utf-8") as fh:
        fh.write(new)
    rc = subprocess.run([sys.executable, "-m", "py_compile", patched]).returncode
    check("the patched file compiles", rc == 0)

    # --- two builds of the same fake tree: before and after ------------------
    base_a, base_b = os.path.join(tmp, "A"), os.path.join(tmp, "B")
    fake_tree(base_a)
    fake_tree(base_b)
    mod_a = load(plain, base_a)
    mod_b = load(patched, base_b)
    out_a, sum_a = mod_a.build()
    out_b, sum_b = mod_b.build()
    ma, mb = members(out_a), members(out_b)
    check("the unpatched build does NOT carry unit_state.txt", "unit_state.txt" not in ma)
    check("the patched build carries unit_state.txt", "unit_state.txt" in mb)
    check("and that is the ONLY new member", set(mb) - set(ma) == {"unit_state.txt"})
    check("no member the old build carried was dropped", not (set(ma) - set(mb)))
    check("the same number of gathered files", sum_a["files"] == sum_b["files"])

    us = mb.get("unit_state.txt", b"").decode("utf-8")
    manifest = mb["MANIFEST.md5"].decode("utf-8")
    check("unit_state.txt has a manifest row", " unit_state.txt" in manifest)
    check("its manifest row matches its bytes",
          mod_b.md5_bytes(mb["unit_state.txt"]) + "  unit_state.txt" in manifest)
    check("the tarball still verifies against its own manifest", not mod_b.verify_tarball(out_b))
    check("crontab.txt is still there", "crontab.txt" in mb)
    check("BUNDLE_INFO records the capture",
          "unit_state_captured=True" in mb["BUNDLE_INFO.txt"].decode("utf-8"))

    check("the enabled timer's symlink is listed with its target",
          "timers.target.wants/clinic-alpha.timer -> clinic-alpha.timer" in us)
    check("the enabled service's symlink is listed",
          "multi-user.target.wants/clinic-alpha.service -> clinic-alpha.service" in us)
    check("the enabled timer reads wants-link=yes",
          any(l.startswith("clinic-alpha.timer") and "wants-link=yes" in l for l in us.splitlines()))
    check("THE NEVER-ENABLED TIMER READS wants-link=no  (this is F-496)",
          any(l.startswith("clinic-ghost.timer") and "wants-link=no" in l for l in us.splitlines()))
    check("all three carried units appear",
          all(u in us for u in ("clinic-alpha.service", "clinic-alpha.timer", "clinic-ghost.timer")))
    check("with ROOT not \"/\" the systemctl columns read not-asked", "is-enabled=not-asked" in us)
    check("and the file says why in writing", 'ROOT is not "/"' in us)
    check("A UNIT'S Environment= VALUE NEVER REACHES unit_state.txt",
          "sup3rsecretvalue" not in us)
    check("nor does any Environment line", "Environment=" not in us)

    # --- the live branch, with systemctl stubbed -----------------------------
    class R(object):
        def __init__(self, out, err="", rc=0):
            self.stdout, self.stderr, self.returncode = out, err, rc
    real_run = mod_b.subprocess.run
    mod_b.subprocess.run = lambda *a, **k: R("enabled\n", "", 1)
    old_root, mod_b.ROOT = mod_b.ROOT, "/"
    old_ur = mod_b.under_root
    mod_b.under_root = lambda rel: os.path.join(base_b, rel.lstrip("/"))
    live_text, live_ok = mod_b.capture_unit_state(
        ["etc/systemd/system/clinic-alpha.timer", "etc/systemd/system/clinic-ghost.timer"])
    check("the live branch reports systemctl's word", "is-enabled=enabled" in live_text)
    check("a NON-ZERO systemctl exit is still read, not treated as failure",
          "not-asked" not in live_text)
    mod_b.subprocess.run = lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("systemctl"))
    nosys_text, _ok = mod_b.capture_unit_state(["etc/systemd/system/clinic-alpha.timer"])
    check("no systemctl at all says unavailable, and nothing raises",
          "unavailable:FileNotFoundError" in nosys_text)
    mod_b.subprocess.run = real_run
    mod_b.ROOT = old_root

    # --- negative control 1: an unlistable unit directory --------------------
    mod_b.under_root = lambda rel: os.path.join(base_b, "no", "such", rel.lstrip("/"))
    gone_text, gone_ok = mod_b.capture_unit_state(["etc/systemd/system/clinic-alpha.timer"])
    check("NEGATIVE CONTROL -- an unlistable unit directory is a note, not a crash",
          gone_ok is False and "could not be listed" in gone_text)
    mod_b.under_root = old_ur

    # --- negative control 2: a manifest row removed ---------------------------
    broken = os.path.join(tmp, "broken.tar.gz")
    with tarfile.open(out_b, "r:gz") as src_tf, tarfile.open(broken, "w:gz") as dst:
        for m in src_tf.getmembers():
            data = src_tf.extractfile(m).read() if m.isfile() else b""
            if m.name == "MANIFEST.md5":
                rows = [r for r in data.decode("utf-8").splitlines()
                        if not r.endswith("  unit_state.txt")]
                data = ("\n".join(rows) + "\n").encode("utf-8")
                m.size = len(data)
            import io as _io
            dst.addfile(m, _io.BytesIO(data))
    check("NEGATIVE CONTROL -- drop its manifest row and the verifier objects",
          bool(mod_b.verify_tarball(broken)))

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("SELFTEST OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
