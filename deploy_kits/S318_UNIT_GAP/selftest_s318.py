#!/root/wa/venv/bin/python3
# =============================================================================
#  selftest_s318.py  ·  S318_UNIT_GAP  ·  v1
#
#  Proves the patch on a COPY of the live code_bundle.py against a FAKE ROOT in
#  /tmp that is shaped like the real box: units the bundle already carried, the
#  five kinds it did NOT, one unit of ours that no pattern will ever match
#  (so the new gap section has something true to say), and one unit that is
#  plainly not ours (so it is counted and not named).
#
#  It never touches /root/state_backup, never reaches Drive, never asks systemd
#  anything (ROOT is not "/", so the patched code skips systemctl by design).
#
#  NEGATIVE CONTROLS, each of which must turn a green check red:
#    the widening reverted   -> the staff register is not carried, and the gap
#                               section names it
#    OURS emptied            -> the gap section can no longer name anything
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

SECRET = "PUT-THE-TOKEN-HERE"        # deliberately not a credential: the publish gate
                                      # refuses a secret-shaped literal, and it is right to (F-365)
BEFORE_UNITS = ("clinic-alpha.service", "clinic-alpha.timer",
                "call-recording-archive.service")
NEW_UNITS = ("call-recording-archive.timer", "staff-register.service",
             "staff-ledger.service", "assetapp.service", "attlistener.service",
             "attendance-dashboard.service")


def check(name, cond):
    (OK if cond else BAD).append(name)
    print("   %s %s" % ("ok  " if cond else "FAIL", name))


def load(path, root):
    os.environ["ROOT"] = root
    spec = importlib.util.spec_from_file_location("cb318_%d" % len(sys.modules), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fake_tree(base, with_fitlog=True):
    os.makedirs(os.path.join(base, "root", "finance"), exist_ok=True)
    with open(os.path.join(base, "root", "finance", "finance_app.py"), "w") as fh:
        fh.write("# a stand-in for the real thing\nprint('hello')\n")
    ud = os.path.join(base, "etc", "systemd", "system")
    tw = os.path.join(ud, "timers.target.wants")
    mw = os.path.join(ud, "multi-user.target.wants")
    os.makedirs(tw, exist_ok=True)
    os.makedirs(mw, exist_ok=True)
    units = list(BEFORE_UNITS) + list(NEW_UNITS) + ["mariadb.service"]
    if with_fitlog:
        units.append("fitlog.service")
    for name in units:
        body = "[Unit]\nDescription=%s\n" % name
        if name == "staff-register.service":
            body += "[Service]\nEnvironment=API_TOKEN=%s\n" % SECRET
        with open(os.path.join(ud, name), "w") as fh:
            fh.write(body)
    for name in units:
        d = tw if name.endswith(".timer") else mw
        os.symlink(os.path.join(ud, name), os.path.join(d, name))


def members(path):
    with tarfile.open(path, "r:gz") as tf:
        return {m.name: tf.extractfile(m).read() for m in tf.getmembers() if m.isfile()}


def build_in(path, base):
    mod = load(path, base)
    out, _summary = mod.build()
    return mod, members(out), out


def main(argv):
    src = LIVE
    for a in argv[1:]:
        if a.startswith("--file="):
            src = a.split("=", 1)[1]
    if not os.path.isfile(src):
        print("RED -- %s is not there" % src)
        return 3
    sys.path.insert(0, HERE)
    import patch_code_bundle_s318 as P

    tmp = tempfile.mkdtemp(prefix="s318_")
    plain, patched = os.path.join(tmp, "plain.py"), os.path.join(tmp, "patched.py")
    shutil.copy2(src, plain)
    with open(src, "r", encoding="utf-8") as fh:
        text = fh.read()
    new, msgs = P.apply_to_text(text)
    check("the patch applies to this file", new is not None and new != text)
    if new is None:
        print("   " + "; ".join(msgs))
        return 4
    with open(patched, "w", encoding="utf-8") as fh:
        fh.write(new)
    check("the patched file compiles",
          subprocess.run([sys.executable, "-m", "py_compile", patched]).returncode == 0)
    check("the ORIGINAL unit patterns are untouched (a second entry, not an edit)",
          '("clinic-*.service", "clinic-*.timer",' in new
          and new.count('("etc/systemd/system",') == 2)

    base_a, base_b = os.path.join(tmp, "A"), os.path.join(tmp, "B")
    fake_tree(base_a)
    fake_tree(base_b)
    _mod_a, ma, _oa = build_in(plain, base_a)
    mod_b, mb, out_b = build_in(patched, base_b)
    pre = "etc/systemd/system/"
    for u in NEW_UNITS:
        check("NOT carried before, carried now: %s" % u,
              (pre + u) not in ma and (pre + u) in mb)
    for u in BEFORE_UNITS:
        check("still carried: %s" % u, (pre + u) in ma and (pre + u) in mb)
    check("no member the old build carried was dropped", not (set(ma) - set(mb)))
    check("fitlog.service is NOT carried (no pattern matches it, by design)",
          (pre + "fitlog.service") not in mb)
    check("mariadb.service is NOT carried", (pre + "mariadb.service") not in mb)

    us = mb["unit_state.txt"].decode("utf-8")
    check("the gap section is there", "[enabled, ours, and NOT carried by this bundle: 1]" in us)
    check("AND IT NAMES THE ONE OF OURS THAT IS MISSING (fitlog.service)",
          any(l.strip() == "fitlog.service" for l in us.splitlines()))
    gap_sec = us.split("[enabled, ours, and NOT carried")[1].split("[units carried")[0]
    check("the GAP SECTION does not name the unit that is not ours "
          "(the symlink list above it names every link, as it should)",
          "mariadb.service" not in gap_sec and "mariadb.service" in us)
    check("but it counts it", "1 other enabled unit(s) are not ours" in us)
    check("the carried count grew by the six new units",
          "[units carried by this bundle: %d]" % (len(BEFORE_UNITS) + len(NEW_UNITS)) in us)
    check("the tarball still verifies against its own manifest", not mod_b.verify_tarball(out_b))
    check("A NEWLY CARRIED UNIT'S SECRET IS MASKED, not shipped",
          SECRET not in mb[pre + "staff-register.service"].decode("utf-8")
          and b"MASKED_BY_CODE_BUNDLE" in mb[pre + "staff-register.service"])
    check("and BUNDLE_INFO names what was masked, never the value",
          "masked=etc/systemd/system/staff-register.service" in mb["BUNDLE_INFO.txt"].decode("utf-8")
          and SECRET not in mb["BUNDLE_INFO.txt"].decode("utf-8"))

    # --- the clean case: nothing of ours enabled and uncarried ---------------
    base_c = os.path.join(tmp, "C")
    fake_tree(base_c, with_fitlog=False)
    _mod_c, mc, _oc = build_in(patched, base_c)
    usc = mc["unit_state.txt"].decode("utf-8")
    check("with nothing of ours missing the section reads none",
          "[enabled, ours, and NOT carried by this bundle: 0]" in usc
          and "every enabled unit of ours is in this bundle" in usc)

    # --- negative control 1: the widening reverted ---------------------------
    rev = new.replace('    ("etc/systemd/system",           ("call-*.timer", "staff-*.service",\n'
                      '                                      "assetapp.service", "attlistener.service",\n'
                      '                                      "attendance-*.service"),                      False, ()),\n', "")
    check("NEGATIVE CONTROL -- the widening can be removed from the text", rev != new)
    p_rev = os.path.join(tmp, "rev.py")
    with open(p_rev, "w", encoding="utf-8") as fh:
        fh.write(rev)
    base_d = os.path.join(tmp, "D")
    fake_tree(base_d)
    _mod_d, md_, _od = build_in(p_rev, base_d)
    usd = md_["unit_state.txt"].decode("utf-8")
    check("NEGATIVE CONTROL -- without the widening the staff register is not carried",
          (pre + "staff-register.service") not in md_)
    check("NEGATIVE CONTROL -- and the gap section names it, which is the point",
          "staff-register.service" in usd.split("[units carried")[0])

    # --- negative control 2: OURS emptied -----------------------------------
    p_ours = os.path.join(tmp, "noours.py")
    with open(p_ours, "w", encoding="utf-8") as fh:
        fh.write(new.replace('OURS = ("clinic-", "wa-", "call-", "staff-", "att", "assetapp",\n'
                             '        "fitlog", "gutlog", "rxguard", "email-agent")',
                             'OURS = ()'))
    base_e = os.path.join(tmp, "E")
    fake_tree(base_e)
    _mod_e, me, _oe = build_in(p_ours, base_e)
    use = me["unit_state.txt"].decode("utf-8")
    check("NEGATIVE CONTROL -- with OURS empty the gap can name nothing",
          "[enabled, ours, and NOT carried by this bundle: 0]" in use)

    shutil.rmtree(tmp, ignore_errors=True)
    print("\n%d check(s) ok, %d failed" % (len(OK), len(BAD)))
    if BAD:
        print("RED: " + "; ".join(BAD))
        return 1
    print("SELFTEST OK -- %d checks" % len(OK))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
