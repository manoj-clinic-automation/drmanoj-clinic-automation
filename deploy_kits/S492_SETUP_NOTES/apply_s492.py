#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s492.py -- S492_SETUP_NOTES (session 298, 07-Oct-2026). Three edits to /root/finance/pc_kits.py, each on an exact
anchor read from the real file (the 07-Oct-2026 01:35 bundle, md5 708fd2030cdf7b13aa7232ba00ef4b7a, read whole at this
build): every anchor must be found EXACTLY ONCE or nothing is written.

  1. the module note: three lines saying what S492 adds.
  2. after PHONES_ROOT: a guarded import of setup_notes (missing or broken -> None, and the page is as before).
  3. on the page, after the phones and before the closing paragraph: the 'Other set-ups' section, under its own guard
     (the page never dies of a note).

   usage: apply_s492.py <path to pc_kits.py>      (edits that file in place; prints the new md5)
"""
import hashlib
import sys

FROM = "708fd2030cdf7b13aa7232ba00ef4b7a"

EDITS = [
    ("the module note",
     "    known PCs, and asks before going on when the name is not the expected one; the enrol door refuses those names too.\n\"\"\"\n",
     "    known PCs, and asks before going on when the name is not the expected one; the enrol door refuses those names too.\n"
     "\n"
     "S492 (07-Oct-2026): the page also carries 'Other set-ups' -- notes and links for the biometric machine, and the list of\n"
     "set-ups still to be built. The notes are data in setup_notes.py; this file only imports it under a guard and gives it one\n"
     "place on the page. No new door, nothing written, the same owner-only gate.\n"
     "\"\"\"\n"),
    ("the guarded import",
     "PHONES_ROOT = os.environ.get(\"PHONE_KITS_ROOT\", os.path.join(KIT_ROOT, \"macrodroid\"))\n",
     "PHONES_ROOT = os.environ.get(\"PHONE_KITS_ROOT\", os.path.join(KIT_ROOT, \"macrodroid\"))\n"
     "\n"
     "# S492: the other set-ups (the biometric machine first). If setup_notes.py is not there or does not load, the page is\n"
     "# exactly what it was.\n"
     "try:\n"
     "    import setup_notes as _setup_notes\n"
     "except Exception:                                              # noqa: BLE001\n"
     "    _setup_notes = None\n"),
    ("the section on the page",
     "    out.append(\"<p class=how>The button downloads one small file. Chrome asks <b>Keep</b>; you click the file and \"\n",
     "    # S492: the other set-ups -- notes and links only; never a password, key or token\n"
     "    if _setup_notes is not None:\n"
     "        try:\n"
     "            out.append(_setup_notes.section())\n"
     "        except Exception:                                      # noqa: BLE001 -- the page never dies of a note\n"
     "            pass\n"
     "    out.append(\"<p class=how>The button downloads one small file. Chrome asks <b>Keep</b>; you click the file and \"\n"),
]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: apply_s492.py <path to pc_kits.py>")
    path = sys.argv[1]
    with open(path, "rb") as fh:
        raw = fh.read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        sys.exit("pc_kits.py is %s, not %s -- nothing written" % (have, FROM))
    text = raw.decode("utf-8")
    for name, old, new in EDITS:
        n = text.count(old)
        if n != 1:
            sys.exit("anchor '%s' found %d times, not once -- nothing written" % (name, n))
        text = text.replace(old, new)
    out = text.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(out)
    print(hashlib.md5(out).hexdigest())


if __name__ == "__main__":
    main()
