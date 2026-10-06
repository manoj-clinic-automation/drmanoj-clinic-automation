#!/usr/bin/env python3
"""make_manifest_s488.py -- kit S488 part E: KIT_MANIFEST.txt with the S488 comment block, built from S480's bytes.

The repository keeps the manifest LF (.gitattributes: *.txt text eol=lf; S480's copy is LF, c9681701); Drive keeps it CRLF
(ea2b437a = S480's with CRLF). This appends the S488 comment after the last comment block (anchored: the S480 F-728 block's
last line must occur exactly once and end the file), writes KIT_MANIFEST.txt here LF, and byte-checks both forms:
the old LF -> CRLF is ea2b437a; the new CRLF is exactly the old CRLF plus the added lines in CRLF. Run with python -B.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = [p for p in (os.path.abspath(os.path.join(HERE, *[".."] * k)) for k in (2, 3)) if os.path.isdir(os.path.join(p, "deploy_kits", "S480_MARG_TEXT_READERS"))][0]   # the kit folder or a scratch folder
SRC = os.path.join(REPO, "deploy_kits", "S480_MARG_TEXT_READERS", "KIT_MANIFEST.txt")
LF_FROM, CRLF_FROM = "c9681701ac23d4cbcf8ed39bc23e2b48", "ea2b437a79f4829790820773e4ba26a9"
md5 = lambda b: hashlib.md5(b).hexdigest()

old = open(SRC, "rb").read()
if md5(old) != LF_FROM or b"\r" in old:
    print("STOP: %s is %s (or carries CR), not %s" % (SRC, md5(old), LF_FROM)); sys.exit(1)
old_crlf = old.replace(b"\n", b"\r\n")
if md5(old_crlf) != CRLF_FROM:
    print("STOP: S480's manifest with CRLF is %s, not the Drive pin %s" % (md5(old_crlf), CRLF_FROM)); sys.exit(1)
ANCHOR = b"# only after the Sanjeevni chat has read both files (F-715).\n"
if old.count(ANCHOR) != 1 or not old.endswith(ANCHOR):
    print("STOP: the S480 block's last line is not once, at the end"); sys.exit(1)
ADD = (b"#\n"
       b"# S488 (part E) -- marg_watch S488 (on the agent's built-in list; no line is needed for it): a refused text's body goes to Drive's\n"
       b"# FromMedical\\refused_text only when it can carry no person's detail -- a purchase statement, the salt, category or item list, a\n"
       b"# valuation, an expiry report or the closing stock, with no person word at its head and no mobile-shaped number but the shop's\n"
       b"# own and Marg's; any other leaves <stem>.withheld.txt there, and every .why.txt there is two lines, never the whole reason.\n"
       b"# _captured_txt\\refused on the medical PC is untouched. Packed by Claude Code on 06-Oct-2026 and delivered only after the\n"
       b"# Sanjeevni chat has read the file.\n")
new = old + ADD
new_crlf = new.replace(b"\n", b"\r\n")
assert new_crlf == old_crlf + ADD.replace(b"\n", b"\r\n")
assert b"\r" not in new and max(new) < 128
open(os.path.join(HERE, "KIT_MANIFEST.txt"), "wb").write(new)
back = open(os.path.join(HERE, "KIT_MANIFEST.txt"), "rb").read()
assert back == new
print("KIT_MANIFEST.txt  FROM LF %s / CRLF (Drive) %s" % (LF_FROM, CRLF_FROM))
print("                  TO   LF %s / CRLF (Drive) %s" % (md5(new), md5(new_crlf)))
print("byte-check: the new CRLF = the old CRLF (%s) + %d added lines in CRLF; no other byte moves; ASCII only" % (CRLF_FROM[:8], ADD.count(b"\n")))
