#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""py39_future.py -- kit S900 (the parent, S493, 20-Nov-2026): the engine stands on the box's Python 3.9.

THE FINDING (S899's import-check, 17:58 IST): /root/wa/venv is Python 3.9.25; processor.py (the PC's engine, unchanged
bytes, f1c02736) writes its type hints in the 3.10 way (`str | None`), which Python 3.9 evaluates at definition time and
refuses -- TypeError: unsupported operand type(s) for |. revenue.py and revenue_ingest.py already carry
`from __future__ import annotations` (hints kept as text, never evaluated) and fail only because they import processor.
THE FIX: the same one line, inserted into processor.py as its first statement after the module docstring -- nothing else
changes; on the PC's Python 3.10+ the line changes no behaviour either (hints are never read at run time there). The
replay's copy of the pre-10-Nov engine (replay/processor.py.bak_S777_0e7c129f, seeded) gets the same line.

    python3 py39_future.py <file> [--check]     --check: say whether the line is already there; exit 0 yes / 1 no / 2 unreadable
    python3 py39_future.py <file> --apply       insert the line (idempotent), write beside as <file>.s900 and move into place
"""
import ast
import os
import sys

LINE = "from __future__ import annotations\n"


def where(src):
    """the line index at which the __future__ import goes: right after the module docstring, before any other statement"""
    tree = ast.parse(src)
    if not tree.body:
        return 0
    first = tree.body[0]
    if isinstance(first, ast.Expr) and isinstance(getattr(first, "value", None), ast.Constant) and isinstance(first.value.value, str):
        return first.end_lineno                  # 0-based index of the line after the docstring
    return first.lineno - 1


def has_future(src):
    tree = ast.parse(src)
    for node in tree.body[:2]:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__" and any(a.name == "annotations" for a in node.names):
            return True
    return False


def apply(path):
    with open(path, encoding="utf-8", newline="") as fh:
        src = fh.read()
    if has_future(src):
        return "already"
    nl = "\r\n" if "\r\n" in src.split("\n", 1)[0] + "\n" else "\n"
    lines = src.splitlines(keepends=True)
    i = where(src)
    lines.insert(i, LINE.replace("\n", nl))
    out = "".join(lines)
    ast.parse(out)                               # still parses
    if not has_future(out):
        raise SystemExit("the line did not land first -- nothing written")
    tmp = path + ".s900"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(out)
    os.replace(tmp, path)
    return "inserted at line %d" % (i + 1)


def main(argv):
    if len(argv) < 2:
        raise SystemExit(__doc__)
    path = argv[1]
    try:
        src = open(path, encoding="utf-8", newline="").read()
    except OSError as ex:
        print("unreadable: %s" % ex)
        return 2
    if "--apply" in argv:
        print("%s: %s" % (os.path.basename(path), apply(path)))
        return 0
    ok = has_future(src)
    print("%s: %s" % (os.path.basename(path), "has the line" if ok else "lacks the line"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
