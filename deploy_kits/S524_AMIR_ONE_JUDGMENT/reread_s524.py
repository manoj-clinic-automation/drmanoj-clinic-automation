#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""reread_s524.py -- kit S524_AMIR_ONE_JUDGMENT, Part 0: re-read the two REFUSED purchase item-wise exports of 08-Oct with the repaired reader.

    python3 -B reread_s524.py --spine-dir DIR --archive /root/marg_ingest/archive --readings DIR --md5 <32 hex> [--md5 ...]

* --spine-dir holds spine_evidence.py and the NEW marg_read.py (a scratch copy of /root/finance/spine with the built reader placed in it);
  the record is made by spine_evidence's own machinery (marg_read.reading_record, the PHI check, read_at), with the reading's ORIGINAL
  name and folder (from the reading already in --readings), so the stamp the spine keys the export by does not move.
* --archive is the collector's local archive (the raw .xls of every export it took); the file is found by its md5, never by its name.
* A reading is written once and never changed (spine_evidence's rule) -- this script is the ONE exception, for the exports the gate
  named, and it writes <md5>.json.bak_S524_<old md5 of the reading, 8> beside the reading before replacing it (the builder loads *.json only).
Exit 0 when every md5 asked for was re-read and the new reading passes its own witness (ok true); 2 otherwise. Nothing else is written."""
import argparse
import hashlib
import json
import os
import sys


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--spine-dir", required=True)
    ap.add_argument("--archive", required=True)
    ap.add_argument("--readings", required=True)
    ap.add_argument("--md5", action="append", required=True)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.abspath(a.spine_dir))
    import spine_evidence as E                                  # noqa: E402  -- the scratch copy's
    import marg_read as M                                       # noqa: E402  -- the NEW reader beside it
    if not getattr(M, "READER_VERSION", "").startswith("S524"):
        print("STOP: marg_read in %s is %s, not the S524 reader" % (a.spine_dir, getattr(M, "READER_VERSION", "?")))
        return 2
    want = set(x.lower() for x in a.md5)
    found = {}
    for dp, _dns, fns in os.walk(a.archive):
        if any(part in E.SKIP_FOLDERS for part in os.path.relpath(dp, a.archive).split(os.sep)):
            continue
        for fn in fns:
            if not fn.lower().endswith((".xls", ".xlsx")):
                continue
            p = os.path.join(dp, fn)
            m = hashlib.md5(open(p, "rb").read()).hexdigest()
            if m in want:
                found[m] = p
    rc = 0
    for m in sorted(want):
        old_p = os.path.join(a.readings, m + ".json")
        if m not in found:
            print("STOP: %s: no file of this md5 in %s" % (m[:8], a.archive))
            rc = 2
            continue
        if not os.path.exists(old_p):
            print("STOP: %s: no reading to replace in %s" % (m[:8], a.readings))
            rc = 2
            continue
        old = json.load(open(old_p))
        old_md5 = hashlib.md5(open(old_p, "rb").read()).hexdigest()
        rec = M.reading_record(found[m], old.get("name") or os.path.basename(found[m]))
        rec["folder"] = old.get("folder", "")
        if rec.get("md5") != m:
            print("STOP: %s: the file read back as %s" % (m[:8], rec.get("md5")))
            rc = 2
            continue
        if not E.phi_free(rec):
            print("STOP: %s: the reading would carry a person's detail -- refused, nothing written" % m[:8])
            rc = 2
            continue
        rec["read_at"] = E.now()
        rec["reread_by"] = "S524_AMIR_ONE_JUDGMENT"
        bak = old_p + ".bak_S524_" + old_md5[:8]
        if not os.path.exists(bak):
            with open(bak, "wb") as fh:
                fh.write(open(old_p, "rb").read())
        with open(old_p + ".tmp", "w") as fh:
            json.dump(rec, fh)
        os.replace(old_p + ".tmp", old_p)
        print("  %-5s %-20s %s  reader %s -> %s  lines %d -> %d  failed %s" % (
            "ok" if rec.get("ok") else "FAIL", rec.get("family"), rec.get("name", "")[:80], old.get("reader"), rec.get("reader"),
            len((old.get("data") or {}).get("lines") or []), len((rec.get("data") or {}).get("lines") or []), rec.get("failed")))
        if not rec.get("ok"):
            rc = 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
