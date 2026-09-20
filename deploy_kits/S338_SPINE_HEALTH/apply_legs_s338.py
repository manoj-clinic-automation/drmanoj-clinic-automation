#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_legs_s338.py -- kit S338_SPINE_HEALTH (S274, Sanjeevni).  A DATA EDIT on the parent's
/root/finance/freshness_legs.json: two legs for the Marg spine (S331), appended, nothing else touched.

    python3 -B apply_legs_s338.py --file /root/finance/freshness_legs.json [--from 0e56aa9e...] [--dry]

  * refuses unless the file's md5 is the FROM pin (or --from is omitted), so an unread edit never lands;
  * appends the two legs only when a leg of that name is absent (idempotent: ALREADY);
  * backs up beside the file as .bak_S338_<md5-8>, writes atomically, prints the new md5;
  * every other leg is written back byte-for-byte in value (json.dump with the same indent the file uses).
Declared to the parent: freshness_legs.json is the parent's file (Sanjeevni START_HERE s3).
"""
import argparse
import hashlib
import json
import os
import sys

LEGS = [
    {"name": "Marg spine gate (S331)", "group": "Marg lane", "kind": "state_json",
     "target": "/root/finance/spine/spine_state.json", "field": "last_success_iso", "max_age_h": 26,
     "note": "spine_build.py every 10 min 08-23 (S331, state file by S338): last_success moves ONLY when the gate "
             "is 14/14, so a failing gate goes red here by itself · the one line: "
             "/root/wa/venv/bin/python3 -B /root/finance/spine/spine_read.py status"},
    {"name": "Marg spine compare (S331)", "group": "Marg lane", "kind": "file_mtime",
     "target": "/root/finance/spine/spine_compare_latest.txt", "max_age_h": 26,
     "note": "spine_compare.py 23:55 nightly (S331) — the screens against the spine, read-only; the file is the record"},
]


def md5_file(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def detect_indent(text):
    for line in text.splitlines():
        if line.startswith(" ") and line.strip():
            return len(line) - len(line.lstrip(" "))
    return 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default="/root/finance/freshness_legs.json")
    ap.add_argument("--from", dest="pin", default="")
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args(argv)
    if not os.path.exists(a.file):
        print("REFUSED: %s does not exist" % a.file)
        return 2
    cur = md5_file(a.file)
    with open(a.file, encoding="utf-8") as fh:
        text = fh.read()
    data = json.loads(text)
    legs = data.get("legs") if isinstance(data, dict) else None
    if not isinstance(legs, list):
        print("REFUSED: no 'legs' list in %s" % a.file)
        return 2
    names = {l.get("name") for l in legs if isinstance(l, dict)}
    todo = [l for l in LEGS if l["name"] not in names]
    if not todo:
        print("ALREADY: both legs present (%s)" % cur)
        return 0
    if a.pin and not cur.startswith(a.pin):
        print("REFUSED: %s is %s, not the pin %s -- nothing written" % (a.file, cur, a.pin))
        return 3
    legs.extend(todo)
    out = json.dumps(data, indent=detect_indent(text), ensure_ascii=False) + ("\n" if text.endswith("\n") else "")
    if a.dry:
        print("DRY: would add %d leg(s): %s" % (len(todo), ", ".join(l["name"] for l in todo)))
        return 0
    bak = a.file + ".bak_S338_" + cur[:8]
    if not os.path.exists(bak):
        with open(bak, "wb") as fh, open(a.file, "rb") as src:
            fh.write(src.read())
    with open(a.file + ".tmp", "w", encoding="utf-8") as fh:
        fh.write(out)
    os.replace(a.file + ".tmp", a.file)
    print("APPLIED: %d leg(s) added (%s); %s -> %s; backup %s" % (len(todo), ", ".join(l["name"] for l in todo), cur, md5_file(a.file), bak))
    return 0


if __name__ == "__main__":
    sys.exit(main())
