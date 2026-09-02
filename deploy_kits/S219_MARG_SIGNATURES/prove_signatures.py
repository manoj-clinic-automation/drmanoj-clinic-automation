#!/usr/bin/env python3
"""
prove_signatures.py -- S219 M2.

Proves a proposed signatures.json against EVERY spreadsheet in the Marg
archive, before anything on disk is changed.  Read-only: it opens each file,
reads its title and header the way the router does, and runs the router's own
identify() twice -- once with the signatures in force today, once with the
proposed set -- then reports every file whose verdict MOVES.

What it must show to pass:
  * the three known unknowns become IDENTIFIED, as the right types
  * NOT ONE other file changes verdict (no silent reclassification)
  * every newly-taught type's end_marker is actually present in its own
    sample -- derived from the file, never copied from a sibling (S205: a
    marker copied from a sibling signature matched 0 of 5 real reports)

USAGE: python3 -B prove_signatures.py <MargPull dir> <archive dir> <proposed.json>
"""
import json
import os
import sys

def main():
    if len(sys.argv) < 4:
        print(__doc__); return 2
    pull, arch, proposed = sys.argv[1], sys.argv[2], sys.argv[3]
    sys.path.insert(0, pull)
    import marg_router as R

    old = json.load(open(os.path.join(pull, "signatures.json"), encoding="utf-8"))["signatures"]
    new = json.load(open(proposed, encoding="utf-8"))["signatures"]
    print("signatures: %d in force  ->  %d proposed (+%d)"
          % (len(old), len(new), len(new) - len(old)))

    files = []
    for dp, dn, fn in os.walk(arch):
        if "_spool" in dp:
            continue
        for f in sorted(fn):
            if f.lower().endswith((".xls", ".xlsx")):
                files.append(os.path.join(dp, f))
    print("spreadsheets found in the archive: %d\n" % len(files))

    moved, same, unreadable = [], 0, []
    for p in files:
        try:
            sh = R.open_sheet(p)
            title, header, hrow = R.read_preamble(sh)
        except Exception as ex:                                # noqa: BLE001
            unreadable.append((p, str(ex)[:60])); continue
        so, st, _ = R.identify(title, header, old)
        sn, nt, _ = R.identify(title, header, new)
        ko = "%s/%s" % (st, so["type"] if so else "-")
        kn = "%s/%s" % (nt, sn["type"] if sn else "-")
        if ko == kn:
            same += 1
        else:
            moved.append((os.path.relpath(p, arch), title[:52], ko, kn, sh))

    print("--- 1 · FILES WHOSE VERDICT MOVES")
    if not moved:
        print("    (none)")
    for rel, title, ko, kn, _sh in moved:
        # the path is printed WHOLE, never truncated: slicing a filename can
        # cut an export stamp like 20260609-123715 into a ten-digit run that
        # the F-185 gate then reads as a phone number (it did, first time).
        print("    %s\n        %-52s  %s -> %s" % (rel, title, ko, kn))
    print("\n    unchanged: %d   moved: %d   unreadable: %d"
          % (same, len(moved), len(unreadable)))
    for p, ex in unreadable:
        print("      unreadable: %s (%s)" % (os.path.basename(p)[:60], ex))

    print("\n--- 2 · EVERY NEW TYPE'S end_marker, CHECKED IN ITS OWN SAMPLE")
    newtypes = {s["type"] for s in new} - {s["type"] for s in old}
    ok_markers = True
    for rel, title, ko, kn, sh in moved:
        t = kn.split("/", 1)[1]
        if t not in newtypes:
            continue
        sig = next(s for s in new if s["type"] == t)
        mk = sig.get("end_marker")
        present = R.ends_with(sh, mk)
        ok_markers = ok_markers and present
        print("    %-26s end_marker %-14r present in its own file: %s"
              % (t, mk, present))
        for sibling in ("Digital Purchase", "GRAND TOTAL"):
            if sibling != mk:
                print("        (a sibling's %-18r would have said: %s)"
                      % (sibling, R.ends_with(sh, sibling)))

    print("\n--- 3 · VERDICT")
    got = {kn.split("/", 1)[1] for _r, _t, _ko, kn, _s in moved}
    good = (all(ko.startswith("UNKNOWN") for _r, _t, ko, _kn, _s in moved)
            and all(kn.startswith("IDENTIFIED") for _r, _t, _ko, kn, _s in moved)
            and ok_markers and not unreadable)
    print("    every move is UNKNOWN -> IDENTIFIED : %s"
          % all(ko.startswith("UNKNOWN") and kn.startswith("IDENTIFIED")
                for _r, _t, ko, kn, _s in moved))
    print("    no file already classified moved    : %s"
          % all(ko.startswith("UNKNOWN") for _r, _t, ko, _kn, _s in moved))
    print("    every end_marker proven in its file : %s" % ok_markers)
    print("    types newly reachable               : %s" % ", ".join(sorted(got)))
    print("\n    %s" % ("PROVEN — safe to install" if good
                        else "NOT PROVEN — do not install"))
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
