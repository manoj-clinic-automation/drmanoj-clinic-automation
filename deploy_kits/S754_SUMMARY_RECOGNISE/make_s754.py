#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s754.py -- S754_SUMMARY_RECOGNISE: the three live files remade from their pinned bytes.
    python3 -B make_s754.py <assetapp dir> <shared dir> <out dir> [<dir holding the S754 sections>]
Each FROM file must carry its pinned md5 (the live bytes of 08-Nov: S750's two TOs; scan_checks_s441 as in the 08-Nov bundle); every
anchor must stand EXACTLY the number of times named; the TO md5s are printed and, when TO_PINS.md5 sits beside this script, checked.
asset_register.py and claude_reader.py: one section appended (sec_ar754.txt, sec_reader754.txt), nothing above it edited.
scan_checks_s441.py: its S754 section (sec_s441_754.txt) inserted before the installer's __main__ block, and two counted edits in
run_pass check 1 (a complete statement is never a page; a continued statement page joins a Summary head only)."""
import hashlib
import os
import sys

FROM = {"assetapp/asset_register.py": "dfa0955ccae7d13aa32c069784f054ea",     # S750's TO (live 11:39 IST 08-Nov)
        "assetapp/claude_reader.py": "8e1ae6bf363f99719b6de5d2dbe01783",      # S750's TO
        "shared/scan_checks_s441.py": "10787cbf67b0480950134047efa74372"}     # the 08-Nov bundle (unchanged since S651)
APPEND = {"assetapp/asset_register.py": "sec_ar754.txt", "assetapp/claude_reader.py": "sec_reader754.txt"}

S441_MAIN = '''if __name__ == "__main__":                                    # the installer's first pass'''
S441_EDITS = [
    ('''        for a in (reversed(rows) if str(b["submitted_at"] or "")[:10] >= PAGES_FROM else ()):''',
     '''        _st754 = _s754_statement(db, b)                         # S754: a complete statement is never a page
        for a in (reversed(rows) if (str(b["submitted_at"] or "")[:10] >= PAGES_FROM and _st754 != "whole") else ()):''', 1),
    ('''            head = by_id.get(a["page_of"]) if a["page_of"] else a
            if head is None or head["status"] == "rejected":
                continue
''',
     '''            head = by_id.get(a["page_of"]) if a["page_of"] else a
            if head is None or head["status"] == "rejected":
                continue
            if _st754 == "continued" and str(head.get("kind") or "") != "Summary":
                continue                                            # S754: a statement's continued page joins a Summary only
''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    aapp, shared, out = sys.argv[1], sys.argv[2], sys.argv[3]
    here = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(os.path.abspath(__file__))
    want = {}
    tp = os.path.join(here, "TO_PINS.md5")
    if os.path.exists(tp):
        for ln in open(tp, encoding="utf-8"):
            p = ln.split()
            if len(p) == 2:
                want[p[1]] = p[0]
    bad = 0
    for rel, pin in FROM.items():
        src = os.path.join(aapp if rel.startswith("assetapp/") else shared, os.path.basename(rel))
        raw = open(src, "rb").read()
        if md5(raw) != pin:
            print("!! %s is %s, not the pinned %s -- refused" % (rel, md5(raw)[:8], pin[:8]))
            bad += 1
            continue
        text = raw.decode("utf-8")
        if rel in APPEND:
            sec = open(os.path.join(here, APPEND[rel]), "rb").read().decode("utf-8")
            text = text.rstrip("\n") + "\n\n\n" + sec.lstrip("\n")
            if not text.endswith("\n"):
                text += "\n"
        else:
            ok = True
            for old, new, n in S441_EDITS:
                c = text.count(old)
                if c != n:
                    print("!! %s: anchor stands %d time(s), expected %d: %r" % (rel, c, n, old[:70]))
                    ok = False
                    continue
                text = text.replace(old, new)
            if text.count(S441_MAIN) != 1:
                print("!! %s: the __main__ anchor stands %d time(s), expected 1" % (rel, text.count(S441_MAIN)))
                ok = False
            if not ok:
                bad += 1
                continue
            sec = open(os.path.join(here, "sec_s441_754.txt"), "rb").read().decode("utf-8")
            text = text.replace(S441_MAIN, sec + S441_MAIN)
        data = text.encode("utf-8")
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(data)
        got = md5(data)
        flag = ""
        if want:
            flag = "  = TO_PINS" if want.get(rel) == got else "  !! NOT the TO pin %s" % (want.get(rel) or "(none)")[:8]
            if want.get(rel) != got:
                bad += 1
        print("%s  %s -> %s%s" % (rel, pin[:8], got, flag))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
