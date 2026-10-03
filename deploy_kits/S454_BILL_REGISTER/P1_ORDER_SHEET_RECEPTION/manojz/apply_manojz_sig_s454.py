#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_manojz_sig_s454.py -- kit S454_BILL_REGISTER part 1, manojz (Dr Manoj's PC): the same ONE new signature, ORDER_PENDING, in
D:\\Downloads\\margsync\\MargPull\\signatures.json (the pull job's copy of the router's registry; not in the nightly bundle -- its hash read live
on 03-Oct: a987a08e). Pin check, a backup beside it (.bak_S454_<from8>), the anchored insertion (the anchor exactly once), the result parsed,
the md5 read back.

    python -B apply_manojz_sig_s454.py --file D:\\Downloads\\margsync\\MargPull\\signatures.json --entry <sig_entry_s454.json> [--dry]
"""
import argparse
import hashlib
import json
import os
import shutil

FROM = "a987a08e626ec210045e8f644536af99"
ANCHOR = '    }\n  ],\n  "_EXAMPLE_adding_a_new_type"'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--entry", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    raw = open(a.file, "rb").read()
    m = hashlib.md5(raw).hexdigest()
    entry = open(a.entry, "rb").read().decode("utf-8").rstrip("\n")
    txt = raw.decode("utf-8")
    if m != FROM:
        if json.loads(txt) and any(s.get("type") == "ORDER_PENDING" for s in json.loads(txt)["signatures"]):
            print("manojz signatures.json: ORDER_PENDING is there already (%s) -- nothing to do" % m)
            return 0
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing written" % (a.file, m, FROM))
    if txt.count(ANCHOR) != 1:
        raise SystemExit("STOP: the insertion anchor occurs %d times -- nothing written" % txt.count(ANCHOR))
    out = txt.replace(ANCHOR, "    },\n" + entry + "\n  ],\n  \"_EXAMPLE_adding_a_new_type\"", 1)
    j = json.loads(out)
    assert [s["type"] for s in j["signatures"]].count("ORDER_PENDING") == 1
    b = out.encode("utf-8")
    to = hashlib.md5(b).hexdigest()
    print("manojz signatures.json %s -> %s (%d signatures)" % (FROM[:8], to, len(j["signatures"])))
    if a.dry:
        return 0
    bak = a.file + ".bak_S454_" + FROM[:8]
    shutil.copy2(a.file, bak)
    with open(a.file + ".s454tmp", "wb") as fh:
        fh.write(b)
    os.replace(a.file + ".s454tmp", a.file)
    back = hashlib.md5(open(a.file, "rb").read()).hexdigest()
    print("placed; read back %s (%s); backup %s" % (back, "= built" if back == to else "DIFFERS", os.path.basename(bak)))
    return 0 if back == to else 1


if __name__ == "__main__":
    raise SystemExit(main())
