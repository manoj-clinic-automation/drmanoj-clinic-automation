#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s809.py -- kit S809_WA_POST_VISIT_TEMPLATE. Remakes the kit's two files from the LIVE bytes.

    make_s809.py <the live portal_wa.py> <the live wa_ladder.py> <out folder>   -> <out>/portal/portal_wa.py, <out>/portal/wa_ladder.py

The owner's new post-visit wording (approved in the MyOperator panel on 13-Nov-2026 as copy_drmanoj_post_visit: it no
longer promises reports in the Docterz app) is ADDED to the portal sender's list of messages, and the "After today's visit"
list uses it. Nothing else changes: every other message, rule and page is as it was. Every anchor must be found exactly
once in a file whose md5 is the one this kit was built on; otherwise nothing is written.
"""
import hashlib
import os
import sys

FROM_WA = "e8b27db968b378261014c27b7b46ca32"          # /root/portal/portal_wa.py (S802)
FROM_LADDER = "5189a155cded969d0aa8fa75c29e0d47"      # /root/portal/wa_ladder.py as kit S808 leaves it

WA_EDITS = [
    ('''                   "ki shubhkaamnaayein. (Docterz app / follow-up date on prescription)"},
''',
     '''                   "ki shubhkaamnaayein. (Docterz app / follow-up date on prescription)"},
    "copy_drmanoj_post_visit": {                                         # S809: the owner's wording of 13-Nov-2026 -- no reports in Docterz
        "family": "numeric", "lang": "en", "group": "Follow-up",
        "title": "Post-visit (same day) - wording of Nov 2026",
        "fields": [{"key":"1","label":"Patient name","prefill":True,"type":"text"}],
        "preview": "Namaskar {1} ji, Dr. Manoj Agarwal Clinic mein aaj aapki visit complete hui. "
                   "Prescription ke liye Docterz app par registered mobile se login karein. "
                   "(medicines, instructions and the follow-up date are on the prescription)"},
'''),
]
LADDER_EDITS = [
    ('VERSION = "S808 1.4"\n', 'VERSION = "S809 1.5"\n'),
    ('''    ("post_visit", "After today's visit", "the same day", "drmanoj_post_visit"),
''',
     '''    ("post_visit", "After today's visit", "the same day", "copy_drmanoj_post_visit"),   # S809: the wording of 13-Nov-2026
'''),
]


def make(src, edits):
    s = src.decode("utf-8")
    for old, new in edits:
        if s.count(old) != 1:
            raise SystemExit("anchor not found exactly once: %r" % old[:60])
        s = s.replace(old, new)
    return s.encode("utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    out = {}
    for path, want, edits, name in ((sys.argv[1], FROM_WA, WA_EDITS, "portal_wa.py"), (sys.argv[2], FROM_LADDER, LADDER_EDITS, "wa_ladder.py")):
        with open(path, "rb") as fh:
            live = fh.read()
        if hashlib.md5(live).hexdigest() != want:
            raise SystemExit("the live %s is not the one this kit was built on (%s)" % (name, hashlib.md5(live).hexdigest()[:8]))
        out[name] = make(live, edits)
    os.makedirs(os.path.join(sys.argv[3], "portal"), exist_ok=True)
    for name, data in out.items():
        with open(os.path.join(sys.argv[3], "portal", name), "wb") as fh:
            fh.write(data)
        print("made", name, hashlib.md5(data).hexdigest())
