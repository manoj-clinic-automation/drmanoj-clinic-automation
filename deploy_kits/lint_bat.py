#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""lint_bat.py -- catch the batch hazards that fail SILENTLY and WRONGLY.

    python lint_bat.py FILE.bat [FILE.bat ...]      exit 0 clean, 1 problems

WHY THIS EXISTS
    A gate was added to PUBLISH_ALL.bat with this line inside an `if (...)`
    block:

        echo    DATA  - move the file to ...\\_config\\ (outside the repo)

    The bare `)` CLOSED THE BLOCK EARLY. Everything after it -- the rest of the
    message, the `pause`, and `exit /b 1` -- stopped being conditional and ran
    on every publish. The check passed, said so, and the script refused anyway.

    Batch does not report this. There is no error, no warning: the file simply
    means something other than what it looks like. That is exactly the class of
    fault this project keeps paying for, so it gets a program rather than care.

WHAT IT CHECKS
    1. Unescaped ( ) & | < > inside a parenthesised block  -- the fault above.
    2. %VAR% read inside a block after being SET in the same block, with
       delayed expansion available -- the classic stale-value trap.
    3. A `%%X%%` outside a FOR loop, which prints a literal percent.
    4. Unbalanced parentheses across the file.

WHAT IT DELIBERATELY DOES NOT CHECK, AND WHY
    `pause & exit /b 1` inside a block. A first version flagged it -- and the
    LIVE script, which has published this project for months, tripped it three
    times. `&` chains commands; only `)` ends a block. **The rule was wrong and
    the working file was the evidence.** A linter that cries wolf on code known
    to work is one nobody reads -- the same fault it exists to catch.
"""
import io
import re
import sys

ECHO = re.compile(r"^\s*echo(\.|\s)", re.I)
SETVAR = re.compile(r"^\s*set\s+(?:/a\s+)?\"?([A-Za-z_][A-Za-z0-9_]*)\s*=", re.I)
FORLOOP = re.compile(r"^\s*for\b", re.I)


def strip_caret(s):
    """Remove escaped characters so only UNescaped ones remain."""
    return re.sub(r"\^.", "", s)


def lint(path):
    lines = io.open(path, encoding="utf-8", errors="ignore").read().split("\n")
    problems = []
    depth = 0
    set_in_block = {}
    for i, raw in enumerate(lines, 1):
        line = raw.rstrip("\r")
        code = line.split("REM ", 1)[0] if line.strip().upper().startswith("REM") else line
        if line.strip().upper().startswith(("REM", "::")):
            continue
        bare = strip_caret(code)

        if depth > 0 and ECHO.match(line):
            for ch in "()&|<>":
                if ch in bare.split("echo", 1)[-1]:
                    problems.append((i, "unescaped '%s' in an echo INSIDE a block -- "
                                        "'%s' ends the block early; write ^%s"
                                     % (ch, ch, ch), line.strip()[:88]))
                    break


        m = SETVAR.match(line)
        if m and depth > 0:
            set_in_block[m.group(1).upper()] = i
        for var in list(set_in_block):
            if depth > 0 and re.search(r"%%%s%%" % re.escape(var), line, re.I) \
                    and not SETVAR.match(line):
                problems.append((i, "%%%s%% read inside the same block where it was set "
                                    "at line %d -- use !%s! with delayed expansion"
                                 % (var, set_in_block[var], var), line.strip()[:88]))
                set_in_block.pop(var, None)

        if "%%" in bare and not FORLOOP.match(line) and depth == 0:
            if not re.search(r"%%[A-Za-z]\b", bare):
                problems.append((i, "%%NAME%% outside a FOR loop prints a literal "
                                    "percent sign", line.strip()[:88]))

        depth += bare.count("(") - bare.count(")")
        if depth < 0:
            problems.append((i, "a ')' with no matching '(' -- a block closed early "
                                "somewhere above", line.strip()[:88]))
            depth = 0
            set_in_block.clear()
        if depth == 0:
            set_in_block.clear()

    if depth != 0:
        problems.append((len(lines), "file ends with %d unclosed '(' " % depth, ""))
    return problems


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip().split("\n")[2].strip())
        return 2
    bad = 0
    for path in sys.argv[1:]:
        try:
            probs = lint(path)
        except OSError as e:
            print("%s: cannot read -- %s" % (path, e))
            bad = 1
            continue
        if not probs:
            print("%-44s OK" % path)
            continue
        bad = 1
        print("%-44s %d problem(s)" % (path, len(probs)))
        for ln, why, text in probs:
            print("   line %-5d %s" % (ln, why))
            if text:
                print("             > %s" % text)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
