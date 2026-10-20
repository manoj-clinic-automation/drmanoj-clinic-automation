#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""proof_s604_reader.py -- kit S604_PAY_SHEET_FIXES (20-Oct-2026), the MEDICAL-PC half's proof, run on manojz before delivery.
    python -B proof_s604_reader.py --old <marg_txt S546 (a59a222f)> --new <the kit's marg_txt.py (S604)> --scratch <a scratch folder>
                                   --kept <_captured_txt> [--kept <_captured_txt\\refused> ...] --today <this morning's text> [--today ...]
1. The S604 reader's own --selftest (made-up blocks shaped as L.K. and KEDAR) -- green.
2. This morning's SUPPLIER/ITEM WISE texts: taken by S604, L.K.'s block (line 177) 'returns inside'; refused by S546 at line 177 (red on S546).
3. The real text altered: L.K.'s TOTAL +-0.02 refused by S604; KEDAR's TOTAL -100 refused by both at KEDAR's TOTAL line; KEDAR's TOTAL +0.02
   accepted by both (S546 goes on to its own refusal at line 177; S604 takes the text).
4. Every kept text converts to the SAME bytes under S604 as under S546 (or is refused by both with the same words); the only newly taken texts
   are this morning's SUPPLIER/ITEM WISE copies. Nothing a text says is printed -- names, figures and lines stay in the files.
The two readers are copied into the scratch folder and loaded from there (never imported from the kit folder). Prints 'PROOF OK S604 READER'."""
import argparse
import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

FAILS = []


def check(label, cond, got=None):
    print(("  ok   " if cond else "  FAIL ") + label + (("   [%s]" % (str(got)[:300],)) if (got is not None and not cond) else ""), flush=True)
    if not cond:
        FAILS.append(label)
    return bool(cond)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def outcome(rd, raw, mtime):
    try:
        x, info = rd.convert(raw, exported_at=mtime)
        return ("TAKEN", hashlib.md5(x).hexdigest())
    except Exception as ex:                                    # noqa: BLE001
        return ("REFUSED", "%s: %s" % (type(ex).__name__, str(ex)[:200]))


def respace(line, idx, delta):
    """The idx-th number on a printed line moved by delta, right-aligned in the same columns (the cutter reads where a word ENDS)."""
    ms = list(re.finditer(r"-?\d+\.\d{2}", line))
    m = ms[idx]
    new = "%.2f" % (float(m.group(0)) + delta)
    width = m.end() - m.start()
    if len(new) > width:
        start = m.end() - len(new)
        assert line[start:m.start()].strip() == "", "no room to print %s" % new
        return line[:start] + new + line[m.end():]
    return line[:m.start()] + new.rjust(width) + line[m.end():]


def alter_total(raw, total_line_no, delta):
    """The TOTAL line (1-based) with both its money figures (amount, net) moved by delta."""
    t = raw.decode("latin-1")
    eol = "\r\n" if "\r\n" in t else "\n"
    lines = t.split(eol)
    l = lines[total_line_no - 1]
    assert "TOTAL" in l, "line %d is not a TOTAL line" % total_line_no
    n = len(re.findall(r"-?\d+\.\d{2}", l))
    for i in range(n):
        l = respace(l, i, delta)
    lines[total_line_no - 1] = l
    return eol.join(lines).encode("latin-1")


def block_total_line(raw, supplier_prefix):
    """The 1-based line number of the TOTAL closing the first block whose supplier line starts with supplier_prefix."""
    t = raw.decode("latin-1")
    lines = t.replace("\r\n", "\n").split("\n")
    i0 = next(i for i, l in enumerate(lines) if l.startswith(supplier_prefix))
    return next(i for i in range(i0 + 1, len(lines)) if re.match(r"^\s+TOTAL\s", lines[i]) and not lines[i].lstrip().startswith("GRAND")) + 1


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.curdir) != here]
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--kept", action="append", default=[])
    ap.add_argument("--today", action="append", default=[])
    a = ap.parse_args()
    sc = os.path.abspath(a.scratch)
    for side, src in (("s546", a.old), ("s604", a.new)):
        os.makedirs(os.path.join(sc, side), exist_ok=True)
        shutil.copyfile(src, os.path.join(sc, side, "marg_txt.py"))
    old = load(os.path.join(sc, "s546", "marg_txt.py"), "marg_txt_s546")
    new = load(os.path.join(sc, "s604", "marg_txt.py"), "marg_txt_s604")
    print("-- the readers: S546 %s (VERSION %s) . S604 %s (VERSION %s)" % (hashlib.md5(open(a.old, "rb").read()).hexdigest()[:8], old.VERSION,
                                                                       hashlib.md5(open(a.new, "rb").read()).hexdigest()[:8], new.VERSION))
    # 1 the selftest
    t0 = time.time()
    r = subprocess.run([sys.executable, "-B", "marg_txt.py", "--selftest"], cwd=os.path.join(sc, "s604"), stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
    s604_lines = [l for l in r.stdout.splitlines() if "S604" in l]
    print("-- 1 the S604 reader's selftest (%.1fs):" % (time.time() - t0))
    for l in s604_lines:
        print("   " + re.sub(r"   \[.*$", "", l))
    check("1 --selftest: SELFTEST OK, every S604 check OK (%d)" % len(s604_lines), r.returncode == 0 and r.stdout.strip().endswith("SELFTEST OK")
          and len(s604_lines) == 10 and all(l.startswith("  OK ") for l in s604_lines), r.stdout[-400:])
    # 2 / 3 this morning's text
    print("-- 2/3 this morning's SUPPLIER/ITEM WISE texts")
    today_md5 = set()
    for p in a.today:
        raw = open(p, "rb").read()
        today_md5.add(hashlib.md5(raw).hexdigest())
        o, n = outcome(old, raw, None), outcome(new, raw, None)
        ri = list(new.RETURNS_INSIDE) if n[0] == "TAKEN" else None
        print("   %s: S546 %s . S604 %s, returns inside at %s" % (os.path.basename(p)[:40], o[0] + ((" -- " + o[1]) if o[0] == "REFUSED" else ""), n[0], ri))
        check("2 %s: taken by S604, L.K.'s block (line 177) 'returns inside'" % os.path.basename(p)[:24], n[0] == "TAKEN" and ri == [177], (n, ri))
        check("2 %s: refused by S546 at line 177 (the negative control)" % os.path.basename(p)[:24], o[0] == "REFUSED" and "line 177:" in o[1], o)
    raw = open(a.today[0], "rb").read()
    for d in (0.02, -0.02):
        o, n = outcome(old, alter_total(raw, 177, d), None), outcome(new, alter_total(raw, 177, d), None)
        check("3 L.K.'s TOTAL (line 177) %+.2f: refused by S604 at line 177 (the half-excess no longer matches)" % d, n[0] == "REFUSED" and "line 177:" in n[1], n)
    kl = block_total_line(raw, "KEDAR")
    print("   KEDAR's TOTAL is line %d" % kl)
    o, n = outcome(old, alter_total(raw, kl, -100), None), outcome(new, alter_total(raw, kl, -100), None)
    check("3 KEDAR's TOTAL -100: refused by both readers at its own TOTAL line %d" % kl, o[0] == n[0] == "REFUSED" and ("line %d:" % kl) in o[1] and ("line %d:" % kl) in n[1], (o, n))
    o, n = outcome(old, alter_total(raw, kl, 0.02), None), outcome(new, alter_total(raw, kl, 0.02), None)
    check("3 KEDAR's TOTAL +0.02: accepted by both (S546 goes on to its own refusal at line 177; S604 takes the text)",
          o[0] == "REFUSED" and "line 177:" in o[1] and n[0] == "TAKEN", (o, n))
    o, n = outcome(old, alter_total(raw, 177, -37.11), None), outcome(new, alter_total(raw, 177, -37.11), None)
    check("3 L.K.'s TOTAL moved by -37.11 (an excess no set of lines explains): refused by S604", n[0] == "REFUSED" and "line 177:" in n[1], n)
    # 4 every kept text
    print("-- 4 every kept text, S546 against S604")
    tally, newly, bad = {}, [], []
    files = []
    for d in a.kept:
        for f in sorted(os.listdir(d)):
            p = os.path.join(d, f)
            if os.path.isfile(p):
                files.append(p)
    for p in files:
        raw = open(p, "rb").read()
        mt = os.path.getmtime(p)
        o, n = outcome(old, raw, mt), outcome(new, raw, mt)
        if o == n:
            k = "the same bytes" if o[0] == "TAKEN" else "refused by both, the same words"
        elif o[0] == "REFUSED" and n[0] == "TAKEN":
            k = "newly taken"
            newly.append((os.path.basename(p), hashlib.md5(raw).hexdigest()))
        else:
            k = "DIFFERENT" if o[0] == n[0] == "TAKEN" else ("LOST" if o[0] == "TAKEN" else "refused, other words")
            bad.append((os.path.basename(p), k, o[1][:80], n[1][:80]))
        tally[k] = tally.get(k, 0) + 1
    print("   %d kept texts: %s" % (len(files), tally))
    for nm, md in newly:
        print("   newly taken: %s (md5 %s)%s" % (nm[:60], md[:8], " -- this morning's" if md in today_md5 else ""))
    for b in bad:
        print("   %s: %s" % (b[0][:60], b[1]))
    check("4 no kept text converts differently, is lost, or is refused with other words", not bad, bad[:3])
    check("4 the only newly taken texts are this morning's SUPPLIER/ITEM WISE copies", all(md in today_md5 for nm, md in newly), newly)
    print("PROOF %s S604 READER: %d failure(s)" % ("OK" if not FAILS else "RED", len(FAILS)))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
