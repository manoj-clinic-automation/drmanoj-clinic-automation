#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""future_out_s910.py -- kit S910 (the parent, S495, 20-Nov-2026): the engine back to the PC's exact bytes.

Kit S900 put ONE line into the box's copy of the engine -- `from __future__ import annotations` as the first statement
after the module docstring -- because the runner then stood on /root/wa/venv (Python 3.9), which refuses the engine's
3.10-style hints. The runner now moves to /root/followup_tracker/venv (Python 3.11, kit S904), where the PC's own bytes
import as they are. This takes S900's line out again, nothing else: the file must then read byte for byte as the PC's
(the installer checks the md5 against the PC's known hashes before anything is kept).

    python3 future_out_s910.py <file> --check    exit 0: the line is NOT there (the PC's shape) / 1: it is / 2: unreadable
    python3 future_out_s910.py <file> --apply    remove the line (idempotent); written beside as <file>.s910, moved into place
"""
import ast
import os
import sys

WANT = "from __future__ import annotations"


def future_index(src):
    """0-based line index of S900's line when it is one of the module's first two statements; else None"""
    tree = ast.parse(src)
    for node in tree.body[:2]:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" and \
                [a.name for a in node.names] == ["annotations"] and node.lineno == node.end_lineno:
            return node.lineno - 1
    return None


def apply(path):
    with open(path, encoding="utf-8", newline="") as fh:
        src = fh.read()
    i = future_index(src)
    if i is None:
        return "already"
    lines = src.splitlines(keepends=True)
    if lines[i].strip() != WANT:
        raise SystemExit("line %d is not the bare __future__ line (%r) -- nothing written" % (i + 1, lines[i].strip()[:60]))
    del lines[i]
    out = "".join(lines)
    ast.parse(out)                               # still parses
    if future_index(out) is not None:
        raise SystemExit("a __future__ line remains -- nothing written")
    tmp = path + ".s910"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    os.replace(tmp, path)
    return "removed line %d" % (i + 1)


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    path = argv[1]
    try:
        with open(path, encoding="utf-8", newline="") as fh:
            src = fh.read()
        idx = future_index(src)
    except Exception as e:                        # noqa: BLE001
        print("%s: unreadable (%s)" % (os.path.basename(path), e))
        return 2
    if "--apply" in argv:
        print("%s: %s" % (os.path.basename(path), apply(path)))
        return 0
    if idx is None:
        print("%s: no __future__ line (the PC's shape)" % os.path.basename(path))
        return 0
    print("%s: __future__ line at %d (S900's)" % (os.path.basename(path), idx + 1))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
