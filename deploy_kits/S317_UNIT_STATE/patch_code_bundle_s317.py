#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_code_bundle_s317.py  ·  Session 269 (parent)  ·  S317_UNIT_STATE  ·  v1
#
#  F-496: THE BUNDLE SAYS WHAT EACH SCHEDULED JOB IS. IT HAS NEVER SAID
#  WHETHER THE JOB IS SWITCHED ON.
#
#  /root/state_backup/code_bundle.py has carried the clinic unit files since
#  S243 and the root crontab since S250. Neither carries the one fact that
#  decides whether a job runs at all: the *.wants symlink. gather() skips
#  symlinks on purpose (os.path.islink), so no bundle in the estate's history
#  has ever contained one. A .timer that was never enabled is byte-identical,
#  in the bundle, to one that fires every night.
#
#  This patch adds ONE generated member, unit_state.txt, beside crontab.txt:
#  the enable symlinks read from the filesystem, and systemctl's own
#  is-enabled / is-active per carried unit when -- and only when -- the bundle
#  is being built against the real root.
#
#  WHAT IT DOES NOT DO. It does not read a unit's content (is-enabled prints
#  one word, so F-518 stays closed), it does not change what is gathered, it
#  never fails a bundle: an unreadable directory becomes a note in the file.
#
#  ANCHORED AND IDEMPOTENT. Every insertion is anchored on text read from the
#  live file (pin a70bf6e202a76fecc86306e39fdf9324, the 18-Sep 01:35 bundle's
#  own copy), each anchor must appear exactly once, and a second run says
#  ALREADY and writes nothing. --check changes nothing at all.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/state_backup/code_bundle.py"
FROM_MD5 = "a70bf6e202a76fecc86306e39fdf9324"
MARK = "S317, F-496"

NEWCODE = r'''
# --- v1.5 (S317, F-496): WHAT A UNIT IS, AND WHETHER IT IS SWITCHED ON --------
#  The bundle has carried the unit FILES since S243 and the root crontab since
#  S250. Both answer "what would run". NEITHER answers "is it switched on".
#  A .timer that was never enabled has no symlink in any *.wants directory and
#  never fires once, and its unit file in this bundle looks exactly like a
#  healthy one. That is F-496, and two cheap facts close it:
#
#    1. THE SYMLINKS. gather() skips symlinks by design (os.path.islink), so
#       /etc/systemd/system/*.wants/ has never been in a bundle at all. The
#       link IS the enabled state on disk: no link, not enabled, whatever the
#       unit file says.
#    2. SYSTEMCTL'S OWN ANSWER -- is-enabled and is-active, per unit, for the
#       units this bundle carries, on the box it is actually running on.
#
#  Fact 1 is read from ROOT and is therefore true in a test tree. Fact 2 asks
#  the live machine, so it is SKIPPED, IN WRITING, whenever ROOT is not "/":
#  a bundle built against a copied tree must never report that copy's units as
#  the live machine's. Nothing here reads a unit's CONTENT -- is-enabled and
#  is-active print one word each -- so no Environment= value can leak by this
#  route (F-518 stays closed).

def _systemctl_one(verb, unit):
    """One word from systemctl about one unit, or a word saying why not.
    A NON-ZERO EXIT IS NORMAL here: systemctl exits non-zero for a disabled or
    inactive unit and still prints the answer, so the output is read and the
    return code is not. Never raises."""
    try:
        p = subprocess.run(["systemctl", verb, "--no-pager", unit],
                           capture_output=True, text=True, timeout=15)
        word = (p.stdout or "").strip().splitlines()
        if word:
            return word[0].strip() or "?"
        err = (p.stderr or "").strip().splitlines()
        return ("error:" + err[0].strip()[:40]) if err else "?"
    except Exception as ex:
        return "unavailable:%s" % type(ex).__name__


def capture_wants():
    """(lines, ok) -- every *.wants / *.requires symlink under ROOT's
    /etc/systemd/system, as "dir/link -> target". Filesystem truth, and it
    works in a test tree because it never asks the running machine."""
    base = under_root("etc/systemd/system")
    lines = []
    try:
        for name in sorted(os.listdir(base)):
            d = os.path.join(base, name)
            if not (name.endswith(".wants") or name.endswith(".requires")):
                continue
            if not os.path.isdir(d):
                continue
            for link in sorted(os.listdir(d)):
                p = os.path.join(d, link)
                if os.path.islink(p):
                    tgt = os.path.basename(os.readlink(p))
                else:
                    tgt = "(not a symlink)"
                lines.append("%s/%s -> %s" % (name, link, tgt))
    except OSError as ex:
        return ["# %s could not be listed: %s" % (base, ex)], False
    return lines, True


def capture_unit_state(rels):
    """(text, ok). One line per unit file the bundle carries: is-enabled,
    is-active, and whether any *.wants link points at it. A note instead of a
    failure when something cannot be read -- this leg never stops a bundle."""
    units = sorted(set(r.split("/")[-1] for r in rels if r.startswith(UNIT_PREFIX)))
    wants, wants_ok = capture_wants()
    linked = set()
    for ln in wants:
        if " -> " in ln and "/" in ln:
            linked.add(ln.split("/", 1)[1].split(" -> ")[0])
    live = (ROOT == "/")
    out = ["# unit_state.txt -- S317 (F-496): whether each carried job is SWITCHED ON,",
           "# not merely what it would do. Read with crontab.txt, never instead of it.",
           "# root=%s host=%s built=%s" % (ROOT, socket.gethostname(),
                                           time.strftime("%Y-%m-%d %H:%M:%S")),
           "",
           "[enable symlinks under %s]" % under_root("etc/systemd/system")]
    out += wants or ["(none -- nothing under this tree is enabled by symlink)"]
    out += ["", "[units carried by this bundle: %d]" % len(units)]
    for u in units:
        if live:
            e, a = _systemctl_one("is-enabled", u), _systemctl_one("is-active", u)
        else:
            e = a = "not-asked"
        out.append("%-44s is-enabled=%-14s is-active=%-12s wants-link=%s"
                   % (u, e, a, "yes" if u in linked else "no"))
    if not units:
        out.append("(none)")
    if not live:
        out += ["",
                "# ROOT is not \"/\", so systemctl was NOT consulted and the two columns",
                "# above read not-asked. The symlink list above is still this tree's own",
                "# truth, and is the fact that matters most."]
    return "\n".join(out) + "\n", bool(wants_ok)

'''

# (anchor, replacement) -- each anchor must appear EXACTLY ONCE in the file.
EDITS = [
    # 1 · the member's name, beside the crontab's
    ('CRONFILE = "crontab.txt"\n',
     'CRONFILE = "crontab.txt"\nUNITSTATE = "unit_state.txt"          # v1.5 (S317, F-496)\n'),
    # 2 · the three functions, before the build banner
    ('# ---------------------------------------------------------------- build -----\n'
     'def build():',
     NEWCODE.lstrip("\n")
     + '# ---------------------------------------------------------------- build -----\n'
       'def build():'),
    # 3 · capture it where the crontab is captured
    ('    cron_text, cron_ok = capture_crontab()\n'
     '    if not cron_ok:\n'
     '        log("WARNING:", cron_text.strip())\n',
     '    cron_text, cron_ok = capture_crontab()\n'
     '    if not cron_ok:\n'
     '        log("WARNING:", cron_text.strip())\n'
     '\n'
     '    unit_text, unit_ok = capture_unit_state(rels)        # v1.5 (S317, F-496)\n'
     '    if not unit_ok:\n'
     '        log("WARNING: the enable symlinks could not be listed; unit_state.txt says so")\n'),
    # 4 · put it in the tarball and in the manifest, beside the crontab
    ('            cron_b = cron_text.encode("utf-8")\n'
     '            manifest_lines.append("%s  %s" % (md5_bytes(cron_b), CRONFILE))\n'
     '            add_bytes(tf, CRONFILE, cron_b)\n',
     '            cron_b = cron_text.encode("utf-8")\n'
     '            manifest_lines.append("%s  %s" % (md5_bytes(cron_b), CRONFILE))\n'
     '            add_bytes(tf, CRONFILE, cron_b)\n'
     '            unit_b = unit_text.encode("utf-8")           # v1.5 (S317, F-496)\n'
     '            manifest_lines.append("%s  %s" % (md5_bytes(unit_b), UNITSTATE))\n'
     '            add_bytes(tf, UNITSTATE, unit_b)\n'),
    # 5 · say so in BUNDLE_INFO.txt, where a reader looks first
    ('                    "finance_app_md5=%s\\ncrontab_captured=%s\\n"\n'
     '                    % (KIT, time.strftime("%Y-%m-%d %H:%M:%S"), socket.gethostname(),\n'
     '                       ROOT, len(files), content_bytes, key_md5, cron_ok))\n',
     '                    "finance_app_md5=%s\\ncrontab_captured=%s\\nunit_state_captured=%s\\n"\n'
     '                    % (KIT, time.strftime("%Y-%m-%d %H:%M:%S"), socket.gethostname(),\n'
     '                       ROOT, len(files), content_bytes, key_md5, cron_ok, unit_ok))\n'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    """(new text, [messages]) or (None, [why it stopped])."""
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S317 change"]
    msgs = []
    for i, (anchor, repl) in enumerate(EDITS, 1):
        n = text.count(anchor)
        if n != 1:
            return None, ["edit %d: its anchor appears %d time(s), not once -- refusing" % (i, n)]
        text = text.replace(anchor, repl, 1)
        msgs.append("edit %d applied" % i)
    return text, msgs


def main(argv):
    mode = "--check" if "--check" in argv else ("--apply" if "--apply" in argv else "")
    target = TARGET
    for a in argv[1:]:
        if a.startswith("--file="):
            target = a.split("=", 1)[1]
    if not mode:
        print("usage: patch_code_bundle_s317.py --check|--apply [--file=PATH]")
        return 2
    if not os.path.isfile(target):
        print("RED -- %s is not there" % target)
        return 3
    before = md5_file(target)
    with open(target, "r", encoding="utf-8") as fh:
        text = fh.read()
    print("    file  : %s (md5 %s)" % (target, before))
    if MARK not in text and before != FROM_MD5:
        print("    note  : this is not the pinned %s -- anchors decide, not the pin" % FROM_MD5[:8])
    new, msgs = apply_to_text(text)
    for m in msgs:
        print("      " + m)
    if new is None:
        print("RESULT RED -- nothing written")
        return 4
    if new == text:
        print("RESULT ALREADY -- nothing to change")
        return 0
    if mode == "--check":
        print("RESULT PENDING -- --apply would write the edits above")
        return 0
    bak = "%s.bak_S317_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=".s317_")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(new)
    try:
        py_compile.compile(tmp, cfile=tmp + ".pyc", doraise=True)
    except py_compile.PyCompileError as ex:
        os.unlink(tmp)
        print("RESULT RED -- the patched file does not compile: %s" % ex)
        return 5
    finally:
        if os.path.exists(tmp + ".pyc"):
            os.unlink(tmp + ".pyc")
    shutil.copymode(target, tmp)
    os.replace(tmp, target)
    after = md5_file(target)
    print("    backup: %s" % bak)
    print("    pin   : %s -> %s" % (before, after))
    print("RESULT APPLIED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
