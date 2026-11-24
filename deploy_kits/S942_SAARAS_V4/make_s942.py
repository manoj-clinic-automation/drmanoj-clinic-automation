#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s942.py -- kit S942 (the parent, S511, 24-Nov-2026): builds call_transcription.py (TO) from the live bytes (FROM ee8d3e41)
by TWO exact single-line replacements -- the Sarvam model saaras:v3 -> saaras:v4 (Sarvam's 16-Oct-2026 mail: v3 is legacy, same
request shape, same price) and the docstring's word. Nothing else moves.
    python3 make_s942.py <call_transcription.py FROM> <call_transcription.py TO>
"""
import hashlib
import sys

FROM_MD5 = "ee8d3e4134ff78d0c01f4e2ecd34a215"
EDITS = [
    ('SARVAM_MODEL = "saaras:v3"\n',
     'SARVAM_MODEL = "saaras:v4"        # S942 (24-Nov-2026): Sarvam\'s 16-Oct mail -- v3 is legacy; same request, same price\n'),
    ("  link-expiry risk), sends it to Sarvam (Saaras v3) for transcription, uploads\n",
     "  link-expiry risk), sends it to Sarvam (Saaras v4; v3 until S942) for transcription, uploads\n"),
]


def main():
    src_p, dst_p = sys.argv[1], sys.argv[2]
    raw = open(src_p, "rb").read()
    got = hashlib.md5(raw).hexdigest()
    if got != FROM_MD5:
        sys.exit("FROM is %s, not %s -- read the live bytes first (F-472)" % (got[:8], FROM_MD5[:8]))
    text = raw.decode("utf-8")
    for old, new in EDITS:
        if text.count(old) != 1:
            sys.exit("anchor not found exactly once: %r" % old[:60])
        text = text.replace(old, new)
    out = text.encode("utf-8")
    open(dst_p, "wb").write(out)
    print("TO %s (%d bytes; FROM %d bytes)" % (hashlib.md5(out).hexdigest(), len(out), len(raw)))


if __name__ == "__main__":
    main()
