#!/root/wa/venv/bin/python3
# =============================================================================
#  patch_code_bundle_s318.py  ·  Session 269 (parent)  ·  S318_UNIT_GAP  ·  v1
#
#  ELEVEN LIVE ENABLED UNITS WERE IN NO STORE, AND S317 FOUND THEM ON ITS FIRST
#  RUN (18-Sep-2026, 19:50 IST, srv1746119).
#
#  The bundle's unit patterns have always been clinic-*.service, clinic-*.timer,
#  wa-*.service and call-*.service. Everything else the estate runs matched none
#  of them, so the CODE of the staff register and the asset app was backed up
#  while THE UNIT FILE THAT STARTS THEM was nowhere:
#
#    assetapp.service · attendance-dashboard.service · attlistener.service
#    staff-register.service · staff-ledger.service · call-recording-archive.timer
#    call-transcription.timer      (+ fitlog / gutlog / rxguard / email-agent,
#                                   carried only once the owner rules them ours)
#
#  TWO PARTS, and the second matters more than the first:
#
#    1. WIDEN what is carried -- as a SECOND entry for etc/systemd/system, never
#       an edit to the first, so that no file carried today can stop being
#       carried by this change (the file's own S273 precedent).
#    2. MAKE THE GAP REPORT ITSELF. unit_state.txt gains a section naming every
#       enabled unit OF OURS that the bundle does not carry. After this kit it
#       reads zero; the morning anyone adds a service without telling the
#       bundle, it reads one. Only ours are named -- a nightly list of the
#       hosting panel's fifty would be wallpaper inside a week (the S195
#       ruling) -- and the rest are counted, not listed.
#
#  Anchored, idempotent, and it refuses on any anchor that is not found exactly
#  once. FROM is v1.5 (S317); the pin is checked but the anchors decide.
# =============================================================================
import hashlib
import os
import py_compile
import shutil
import sys
import tempfile
import time

TARGET = "/root/state_backup/code_bundle.py"
FROM_MD5 = "c7f33e55e5ef409a34ff4557a2d77bc9"
MARK = "S318, the gap"

EDITS = [
    # 1 · OURS: the prefixes that make a unit this estate's own.
    ('UNITSTATE = "unit_state.txt"          # v1.5 (S317, F-496)\n',
     'UNITSTATE = "unit_state.txt"          # v1.5 (S317, F-496)\n'
     '# v1.6 (S318, the gap): what makes a unit OURS rather than the hosting\n'
     '# panel\'s or the distribution\'s. Used ONLY to decide which enabled units\n'
     '# are worth naming when they are missing from the bundle -- never to decide\n'
     '# what is carried (the patterns below do that). One line to widen.\n'
     'OURS = ("clinic-", "wa-", "call-", "staff-", "att", "assetapp",\n'
     '        "fitlog", "gutlog", "rxguard", "email-agent")\n'),
    # 2 · a SECOND entry for the unit directory, never an edit to the first
    ('    ("etc/systemd/system",           ("clinic-*.service", "clinic-*.timer",\n'
     '                                      "wa-*.service", "call-*.service"),            False, ()),\n'
     ']\n',
     '    ("etc/systemd/system",           ("clinic-*.service", "clinic-*.timer",\n'
     '                                      "wa-*.service", "call-*.service"),            False, ()),\n'
     '    # v1.6 (S318): the estate\'s OTHER units. S317\'s first run read every\n'
     '    # enable symlink on the box and eleven enabled units matched none of the\n'
     '    # four patterns above -- the staff register, the asset app, the two\n'
     '    # attendance services, the staff ledger, and the two call-* TIMERS whose\n'
     '    # services were already carried. A SECOND entry rather than an edit to\n'
     '    # the first, so that no file carried today can stop being carried by this\n'
     '    # change (the S273 precedent, three entries above).\n'
     '    ("etc/systemd/system",           ("call-*.timer", "staff-*.service",\n'
     '                                      "assetapp.service", "attlistener.service",\n'
     '                                      "attendance-*.service"),                      False, ()),\n'
     ']\n'),
    # 3 · the gap section, in the file the bundle carries
    ('    out += ["", "[units carried by this bundle: %d]" % len(units)]\n',
     '    # v1.6 (S318): THE GAP REPORTS ITSELF. An enabled unit this bundle does\n'
     '    # not carry is a unit file in no store at all. Ours are named; the rest\n'
     '    # are counted, because a nightly list of the panel\'s fifty would be\n'
     '    # wallpaper inside a week (the S195 ruling).\n'
     '    ours_linked = sorted(u for u in linked if u.startswith(OURS))\n'
     '    gap = [u for u in ours_linked if u not in units]\n'
     '    others = len([u for u in linked if not u.startswith(OURS)])\n'
     '    out += ["", "[enabled, ours, and NOT carried by this bundle: %d]" % len(gap)]\n'
     '    out += gap or ["(none -- every enabled unit of ours is in this bundle)"]\n'
     '    out += ["# %d other enabled unit(s) are not ours (the hosting panel\'s and"\n'
     '            " the distribution\'s) and are not listed here." % others]\n'
     '    out += ["", "[units carried by this bundle: %d]" % len(units)]\n'),
]


def md5_file(p):
    h = hashlib.md5()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def apply_to_text(text):
    if MARK in text:
        return text, ["ALREADY -- this file already carries the S318 change"]
    if "S317, F-496" not in text:
        return None, ["this file does not carry the S317 change yet -- install S317 first"]
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
        print("usage: patch_code_bundle_s318.py --check|--apply [--file=PATH]")
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
    bak = "%s.bak_S318_%s" % (target, time.strftime("%Y%m%d_%H%M%S"))
    shutil.copy2(target, bak)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(target), prefix=".s318_")
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
