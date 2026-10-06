#!/usr/bin/env python3
"""fdiff_s488e.py -- kit S488 part E: a function-level diff of marg_watch.py 58b54f37 (OLD) against the NEW file beside this script.

Parses both with ast; every top-level statement is keyed (def/class by name, an assignment by its target names, the module
docstring, an import by its text, anything else by its kind and position among its kind); its source segment is compared.
Then every changed LINE (difflib over the whole files, comments included) is placed in the top-level statement it falls in, or
the comment block before the next one -- so a comment edited between statements is caught too. Expected to differ: the module
docstring (the S488 header note), share_refused, selftest; added: the S488 helpers and their constants. Nothing else.
"""
import ast
import difflib
import hashlib
import os
import sys
import warnings

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = [p for p in (os.path.abspath(os.path.join(HERE, *[".."] * k)) for k in (2, 3)) if os.path.isdir(os.path.join(p, "deploy_kits", "S480_MARG_TEXT_READERS"))][0]   # the kit folder or a scratch folder
OLD = os.path.join(REPO, "deploy_kits", "S480_MARG_TEXT_READERS", "marg_watch.py")
NEW = os.path.join(HERE, "marg_watch.py")
EXPECT_CHANGED = {"<module docstring>", "def share_refused", "def selftest"}
EXPECT_ADDED = {"def _may_leave", "def _read_or_none", "def _share_put", "def _safe_why", "def _withhold", "def _share_sweep",
                "def _s488_share_cases", "PHI_MOBILE_RE", "PHI_PERSON_WORDS", "PHI_SHOP_LINE_RE", "PHI_AD_LINE_RE",
                "PHI_PREAMBLE_LINES, PHI_SHOP_LINES, PHI_AD_LINES", "SHARE_KINDS", "WITHHELD_LINE", "WHY_STAMP_RE", "WHY_LINE_SAFE"}


def key_of(node, src, seen):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return ("class " if isinstance(node, ast.ClassDef) else "def ") + node.name
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str) and node.lineno <= 3:
        return "<module docstring>"
    if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        tg = node.targets if isinstance(node, ast.Assign) else [node.target]
        return " = ".join(ast.get_source_segment(src, x) for x in tg)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        return ast.get_source_segment(src, node)
    k = type(node).__name__
    seen[k] = seen.get(k, 0) + 1
    return "<%s #%d>" % (k, seen[k])


def table(path):
    src = open(path, encoding="utf-8").read()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)          # the '\h' in capture_text's HELD line is S480's own, unchanged
        tree = ast.parse(src)
    seen, out, spans = {}, {}, []
    for node in tree.body:
        k = key_of(node, src, seen)
        if k in out:
            k = "%s @%d" % (k, node.lineno)
        out[k] = ast.get_source_segment(src, node)
        start = node.lineno
        if getattr(node, "decorator_list", None):
            start = min(d.lineno for d in node.decorator_list)
        spans.append((start, node.end_lineno, k))
    return src, out, spans


def place(line_no, spans):
    """The statement a (1-based) line falls in; a line between statements belongs to the comment block before the next one."""
    for a, b, k in spans:
        if a <= line_no <= b:
            return k
    for a, b, k in spans:
        if line_no < a:
            return "(comments before) " + k
    return "(after the last statement)"


def main():
    so, to, spo = table(OLD)
    sn, tn, spn = table(NEW)
    print("OLD %s  md5 %s" % (OLD, hashlib.md5(open(OLD, "rb").read()).hexdigest()))
    print("NEW %s  md5 %s" % (NEW, hashlib.md5(open(NEW, "rb").read()).hexdigest()))
    changed = sorted(k for k in to if k in tn and to[k] != tn[k])
    added = sorted(k for k in tn if k not in to)
    removed = sorted(k for k in to if k not in tn)
    same = [k for k in to if k in tn and to[k] == tn[k]]
    print("\ntop-level statements: OLD %d, NEW %d; identical %d" % (len(to), len(tn), len(same)))
    print("CHANGED: " + (", ".join(changed) or "(none)"))
    print("ADDED  : " + (", ".join(added) or "(none)"))
    print("REMOVED: " + (", ".join(removed) or "(none)"))
    ol, nl = so.splitlines(), sn.splitlines()
    where = set()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ol, nl, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        for j in range(j1, j2):
            where.add(place(j + 1, spn))
        for i in range(i1, i2):
            k = place(i + 1, spo)
            where.add(k if k in tn or k.startswith("(") else "OLD-only " + k)
    print("\nevery changed line falls in:")
    for w in sorted(where):
        print("   " + w)
    allowed = EXPECT_CHANGED | EXPECT_ADDED
    ok_where = all(w in allowed or (w.startswith("(comments before) ") and w[len("(comments before) "):] in allowed) for w in where)
    unchanged_capture = [k for k in ("def capture", "def capture_text", "def _keep_refused", "def _kind_of", "def _note_reason",
                                     "def _why_not", "def retry_refused", "def publish_diagnostics", "def watch", "def main",
                                     "def notes_try", "def _note_one", "def note_of") if to.get(k) != tn.get(k)]
    print("\nthe capture path and the note path (capture, capture_text, _keep_refused, _kind_of, _note_reason, _why_not, "
          "retry_refused, publish_diagnostics, watch, main, notes_try, _note_one, note_of): %s"
          % ("byte-identical" if not unchanged_capture else "DIFFER: " + ", ".join(unchanged_capture)))
    ok = (set(changed) == EXPECT_CHANGED and set(added) == EXPECT_ADDED and not removed and ok_where and not unchanged_capture)
    print("\nFDIFF %s: only the module docstring, share_refused and selftest differ; added only the S488 helpers and their "
          "constants; nothing removed" % ("OK" if ok else "NOT AS EXPECTED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
