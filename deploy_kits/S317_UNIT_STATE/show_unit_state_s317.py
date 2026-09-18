#!/root/wa/venv/bin/python3
# =============================================================================
#  show_unit_state_s317.py  ·  S317_UNIT_STATE  ·  v1
#
#  READ-ONLY. IT NEED NOT BE RUN BY ANYONE: the nightly bundle carries this
#  same table as unit_state.txt from 01:35 onwards, and the owner's PC copy of
#  the bundle is where it should normally be read. This exists so the installer
#  can show the answer once, on the spot, and so a session that wants the live
#  picture between bundles can have it without touching anything.
#
#  It imports the live /root/state_backup/code_bundle.py and calls its own
#  capture_unit_state(). It writes nothing, uploads nothing, restarts nothing,
#  and asks systemd only is-enabled / is-active, which print one word each.
# =============================================================================
import importlib.util
import os
import sys

TARGET = "/root/state_backup/code_bundle.py"


def main(argv):
    target = TARGET
    for a in argv[1:]:
        if a.startswith("--file="):
            target = a.split("=", 1)[1]
    if not os.path.isfile(target):
        print("RED -- %s is not there" % target)
        return 3
    spec = importlib.util.spec_from_file_location("cb_live", target)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "capture_unit_state"):
        print("RED -- this code_bundle.py does not carry the S317 change yet")
        return 4
    files, _skipped, _hits = mod.gather()
    rels = [r for r, _ in files]
    text, ok = mod.capture_unit_state(rels)
    sys.stdout.write(text)
    units = [l for l in text.splitlines() if "is-enabled=" in l]
    off = [l.split()[0] for l in units if "wants-link=no" in l]
    print("")
    print("SUMMARY %d unit(s) carried · %d with no enable symlink: %s"
          % (len(units), len(off), ", ".join(off) or "-"))
    print("READ-ONLY -- nothing was written. capture_ok=%s" % ok)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
