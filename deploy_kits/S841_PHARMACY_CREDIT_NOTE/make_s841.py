#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s841.py FROM_DIR OUT -- kit S841_PHARMACY_CREDIT_NOTE (14-Nov-2026, the Scan App chat's session 466; F-1419, F-1422).
Builds the two changed files FROM THE LIVE BYTES (md5-pinned; exact anchors counted; anything else stops the build).

  claude_reader.py   e2338b8b -> + the S841 block at the end (the pharmacy reader recognises a credit note).
  asset_register.py  63eba920 -> (1)(2) the bill edit page keeps kind 'Pharmacy credit note' (template + POST, one each);
                                              (3) + the S841 block at the end (marked at intake; healed; the history rule holds it).
"""
import hashlib, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FROM = {"claude_reader.py": "e2338b8b9636b67fbd60304ef56694da",
        "asset_register.py": "63eba9203b4bca4bf12b578ccbd5d019"}
EDITS = {"asset_register.py": [
    ("{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense','Summary') %}",
     "{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense','Summary','Pharmacy credit note') %}"),
    ('kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense", "Summary") else',
     'kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense", "Summary", "Pharmacy credit note") else'),
]}
TAIL = {"claude_reader.py": ('        out["against_no"] = _txt(data.get("against_no"), 60)\n    return out\n', "block_reader.py"),
        "asset_register.py": ("# ---- S754 end " + "-" * 123 + "\n", "block_ar.py")}


def main(root, out):
    os.makedirs(out, exist_ok=True)
    for name, md5 in FROM.items():
        src = os.path.join(root, name)
        raw = open(src, "rb").read()
        got = hashlib.md5(raw).hexdigest()
        if got != md5:
            sys.exit("STOP: %s is %s, not %s -- the live file moved; nothing built" % (name, got[:8], md5[:8]))
        s = raw.decode("utf-8")
        for old, new in EDITS.get(name, []):
            if s.count(old) != 1 or s.count(new) != 0:
                sys.exit("STOP: %s anchor found %d times (want 1): %s" % (name, s.count(old), old[:70]))
            s = s.replace(old, new, 1)
        tail, blk = TAIL[name]
        if not s.endswith(tail) or "S841" in s:
            sys.exit("STOP: %s does not end where it did (or already carries S841)" % name)
        s = s + open(os.path.join(HERE, blk), encoding="utf-8").read()
        data = s.encode("utf-8")
        open(os.path.join(out, name), "wb").write(data)
        print("built %s %s -> %s" % (name, md5[:8], hashlib.md5(data).hexdigest()[:8]))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: make_s841.py FROM_DIR OUT")
    main(sys.argv[1], sys.argv[2])
