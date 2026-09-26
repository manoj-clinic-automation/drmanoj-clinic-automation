#!/usr/bin/env python3
"""apply_s416.py -- kit S416_BUNDLE_ALLOWLIST (F-631). Makes the v1.8 code_bundle.py from the live v1.7 bytes (8200dcca)
by ONE appended block in SOURCES -- the S273/S318/S347 precedent: new entries, never an edit to an old one, so no file
carried today can stop being carried. F-631 (S279 close): five live files were in no nightly bundle --
  /root/portal/portal_sw.js                (root/portal carried *.py *.html *.json -- no *.js)
  /root/portal/http_ece.py                 (root/portal *.py -- carried IF the file exists; see the installer's note)
  /etc/systemd/system/ring-hook.service    (the unit patterns had clinic-* wa-* call-* staff-* ... -- no ring-*)
  /root/wa/casepack/casepack_page.html     (root/wa carried *.py only, and not the casepack/ sub-folder)
  /root/wa/fu_push_on_arrival.sh           (root/wa carried *.py only)
Usage: python apply_s416.py <v1.7 code_bundle.py> <out>"""
import hashlib, sys
b = open(sys.argv[1], "rb").read()
assert hashlib.md5(b).hexdigest() == "8200dcca2256a843ccabcdbd8250ec55", "the source is not the live v1.7 code_bundle.py"
s = b.decode("utf-8")
old = '''    ("root/finance/spine",           ("*.py", "*.json", "*.txt"),                   False, ()),
]
'''
new = '''    ("root/finance/spine",           ("*.py", "*.json", "*.txt"),                   False, ()),
    # v1.8 (S416, F-631, 26-Sep-2026): five live files the S279 close found in NO
    # nightly bundle, each coming back byte-identical only from its repository
    # kit. New entries, never an edit to an old one (the S273 precedent):
    #   root/portal *.js            -- portal_sw.js, the service worker (S366)
    #   ring-*.service              -- ring-hook.service, the caller pop-up's unit (S366)
    #   root/wa/casepack *.html/.py -- casepack_page.html (S216/S385) and its helpers
    #   root/wa *.sh                -- fu_push_on_arrival.sh (S376)
    # http_ece.py is already matched by root/portal *.py when it exists on disk.
    ("root/portal",                  ("*.js",),                                      False, ("users", "secret")),
    ("etc/systemd/system",           ("ring-*.service",),                            False, ()),
    ("root/wa/casepack",             ("*.html", "*.py"),                             False, ("users", "secret", "token")),
    ("root/wa",                      ("*.sh",),                                      False, ("users", "secret", "token")),
]
'''
assert s.count(old) == 1, "anchor"
s = s.replace(old, new)
open(sys.argv[2], "wb").write(s.encode("utf-8"))
print("S416 code_bundle.py md5", hashlib.md5(s.encode("utf-8")).hexdigest())
