#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s679_pc.py -- the medical side of kit S679_SALE_BILLED_TO_PARTY, run where the kept texts are (never in the cloud workspace).

    python3 -B walk_s679_pc.py --new <dir: new marg_txt.py + marg_watch.py> --old <dir: the live two> --texts <dir> [--texts <dir> ...]
                               --scratch <dir> [--party-file <one refused text that must now name its bill>]

Checks, on made-up texts first (no real line ever printed):
  P1 a made-up sale text whose bill row carries a party word in D.R. -> refused naming the bill and the party (new); the old said only
     'payment head is not where the header says'
  P2 .CASH, .UPI, blank, a lone '#', '.CASH   #' -> read exactly as the old reader reads them (bytes equal)
  P3 a description run into the D.R. column, a payment word off its column -> the old refusal, word for word
  P4 the note: the bill number leaves the PC, the party's name never; idempotent; six-digit runs elsewhere still masked
  P5 every other reason the watcher has ever kept (.why.txt under --texts) -> the same note as the old watcher
  P6 every real kept text under --texts: the old and the new reader give the same bytes, or the same refusal -- except a party bill, which
     the new reader names (and only that)
  P7 (--party-file) the 28-Oct refused text: refused naming its bill; the party's name in the reason, never in the note
  P8 the new reader's own --selftest passes
Last line: "N of N green" -- or, with --control, the count of S679 checks the OLD files fail.
"""
import argparse
import glob
import hashlib
import importlib.util
import io
import os
import re
import shutil
import sys
from contextlib import redirect_stdout


def load(path, name, scratch):
    d = os.path.join(scratch, name)
    os.makedirs(d, exist_ok=True)
    for f in ("marg_txt.py", "marg_watch.py"):
        shutil.copyfile(os.path.join(path, f), os.path.join(d, f))
    sys.path.insert(0, d)
    try:
        out = {}
        for f in ("marg_txt", "marg_watch"):
            sys.modules.pop(f, None)
            spec = importlib.util.spec_from_file_location(f, os.path.join(d, f + ".py"))
            m = importlib.util.module_from_spec(spec)
            sys.modules[f] = m
            spec.loader.exec_module(m)
            out[f] = m
        return out
    finally:
        sys.path.remove(d)
        for f in ("marg_txt", "marg_watch"):
            sys.modules.pop(f, None)


HEAD = ("BILL NO.    DESCRIPTION                       D.R.          GROSS AMT.    DISCOUNT         TAX       DR/CR    NET AMT.        CASH")


def made_up(dr_field, desc="WALK PERSON", bill="A999901"):
    """A made-up bill-wise sale text: one bill, one item, its totals; D.R. holds `dr_field` (14 wide from column 46)."""
    p_dr = HEAD.find("D.R.")
    row = (bill.ljust(12) + desc.ljust(p_dr - 12))[:p_dr] + dr_field.ljust(14)[:14]
    row = row + "%10s%12s%12s%12s%12s%12s" % ("100.00", "0.00", "0.00", "0.00", "100.00", "100.00")
    item = "            1  11 WALKMED 10MG TAB     1*10           1      100.00  1/99 WALK1"
    rule = "-" * 132
    lines = ["SANJEEVNI MEDICOS", "                  BILL WISE SALES STATEMENT AS ON 01-01-2099", HEAD, rule, "01-01-2099",
             row, item, "", rule,
             "%s%s" % ("Total No. of Bills: 1".ljust(36) + "DAY TOTAL :".ljust(10),
                       "%14s%12s%12s%12s%12s%12s" % ("100.00", "0.00", "0.00", "0.00", "100.00", "100.00")),
             "%s%s" % ("Total No. of Bills: 1".ljust(36) + "GRAND TOTAL :".ljust(10),
                       "%14s%12s%12s%12s%12s%12s" % ("100.00", "0.00", "0.00", "0.00", "100.00", "100.00")),
             rule, "*** End of Report ***", ""]
    return "\r\n".join(lines).encode("latin-1")


def run(mods, raw):
    """('ok', md5 of bytes) or ('refused', reason) or ('other', exc name)."""
    mt = mods["marg_txt"]
    try:
        b, _info = mt.convert(raw, exported_at=4070908800.0)
        return ("ok", hashlib.md5(b).hexdigest())
    except mt.Refused as e:
        return ("refused", str(e))
    except mt.NotThisReport as e:
        return ("not", str(e))
    except Exception as e:                                             # noqa: BLE001
        return ("other", type(e).__name__ + ": " + str(e)[:80])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--new", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--texts", action="append", default=[])
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--party-file")
    ap.add_argument("--control", action="store_true", help="judge the OLD files as if new: the S679 checks must go red")
    a = ap.parse_args()
    new = load(a.old if a.control else a.new, "new", a.scratch)
    old = load(a.old, "old", a.scratch)
    res = []

    def ck(name, cond, s679):
        res.append((name, bool(cond), s679))

    # P1
    r = run(new, made_up("DEEPAM PHARM"))
    ck("P1 a party word in D.R. -> refused naming bill A999901 and the party, telling them to correct it in Marg",
       r[0] == "refused" and "bill A999901 is billed to the party account DEEPAM PHARM" in r[1] and "correct the bill in Marg" in r[1], True)
    ro = run(old, made_up("DEEPAM PHARM"))
    ck("P1b the old reader refused the same text (the generic words) -- the made-up text is the real shape",
       ro[0] == "refused" and "payment head is not where the header says" in ro[1], False)
    # P2
    same = []
    for f in (".CASH", ".UPI", "", "#", ".CASH      #", ".UPI       #"):
        x, y = run(new, made_up(f)), run(old, made_up(f))
        same.append(x == y and x[0] == "ok")
    ck("P2 .CASH, .UPI, blank, a lone '#', '.CASH #', '.UPI #' -> read, the same bytes as the old reader (6 of 6)", all(same), False)
    same2 = []
    for f in ("CASH", "UPI", "-CASH", "# .CASH", "cash"):
        x, y = run(new, made_up(f)), run(old, made_up(f))
        same2.append(x == y and x[0] == "refused" and "payment head" in x[1])
    ck("P2b a payment word printed oddly ('CASH', 'UPI', '-CASH', '# .CASH', 'cash') -> never called a party: the old refusal, word for word",
       all(same2), False)
    # P3
    p_dr = HEAD.find("D.R.")
    run_in = made_up("", desc="W" * (p_dr - 12) + "X")                  # the description runs into the D.R. column
    off = made_up(" .CASH")                                              # the payment word one column off
    x1, y1, x2, y2 = run(new, run_in), run(old, run_in), run(new, off), run(old, off)
    ck("P3 a description run into D.R. and a payment word off its column -> the old refusal, word for word",
       x1 == y1 and x2 == y2 and x1[0] == "refused" and x2[0] == "refused", False)
    # P4
    nr = new["marg_watch"]._note_reason
    why = ("the reader refused it: line 12: bill A999901 is billed to the party account SOME PARTY 123456, not cash or UPI -- "
           "correct the bill in Marg (Cash or UPI), then export again")
    n1 = nr(why)
    ck("P4 the note: 'bill A999901 is billed to a party account' -- no party name, no digits of it; idempotent",
       n1 == "the reader refused it: bill A999901 is billed to a party account, not cash or UPI" and "SOME" not in n1
       and "123456" not in n1 and nr(n1) == n1, True)
    ck("P4b a six-digit run elsewhere in an ordinary reason is still masked; a line reason is still '(line N)'",
       nr("the medical PC saw 1234567 rows") == old["marg_watch"]._note_reason("the medical PC saw 1234567 rows")
       and nr("the reader refused it: line 12: anything 1234567") == "the reader refused it (line 12)", False)
    # P5
    whys = []
    for d in a.texts:
        for p in glob.glob(os.path.join(d, "**", "*.why.txt"), recursive=True):
            for ln in open(p, "rb").read().decode("utf-8", "replace").splitlines():
                if ln.startswith("why:"):
                    whys.append(ln[4:].strip())
    pat = getattr(new["marg_watch"], "S679_PARTY", None)
    diff5 = [w for w in whys if nr(w) != old["marg_watch"]._note_reason(w) and not (pat and pat.match(" ".join(w.split())))]
    ck("P5 every kept .why.txt (%d) gives the old watcher's note -- the S679 shape apart" % len(whys), not diff5, False)
    # P6
    texts = []
    for d in a.texts:
        texts += [p for p in glob.glob(os.path.join(d, "**", "*.txt"), recursive=True)
                  if not p.endswith((".why.txt", ".note", ".withheld.txt")) and os.path.getsize(p) > 200]
    seen, same6, named, bad = set(), 0, 0, []
    for p in sorted(texts):
        raw = open(p, "rb").read()
        h = hashlib.md5(raw).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        x, y = run(new, raw), run(old, raw)
        if x == y:
            same6 += 1
        elif x[0] == "refused" and "is billed to the party account" in x[1] and y[0] == "refused" and "payment head" in y[1]:
            named += 1
        else:
            bad.append(os.path.basename(p)[:40] + ": old %s / new %s" % (y[0], x[0]))
    print("  --  real kept texts: %d distinct, %d the same under old and new, %d party bills now named, %d other" % (len(seen), same6, named, len(bad)))
    for b in bad[:10]:
        print("      RED " + b)
    ck("P6 every real kept text reads the same under the old and the new reader (bytes or refusal) -- a party bill apart", not bad and seen, False)
    # P7
    if a.party_file:
        raw = open(a.party_file, "rb").read()
        x = run(new, raw)
        m = re.search(r"bill ([A-Z]{1,3}[0-9]{3,9}) is billed to the party account", x[1]) if x[0] == "refused" else None
        note = nr("the reader refused it: " + x[1]) if m else ""
        party = x[1].split("party account ", 1)[1].split(",")[0] if m else "?"
        print("  --  the party file: %s" % (("refused naming bill %s" % m.group(1)) if m else x[0]))
        ck("P7 the 28-Oct text: refused naming its bill; the party's name in the reason, never in the note",
           m and party and party not in note and m.group(1) in note, True)
    # P8
    buf = io.StringIO()
    with redirect_stdout(buf):
        try:
            rc = new["marg_txt"].selftest()
        except SystemExit as e:
            rc = e.code
    fails = [l for l in buf.getvalue().splitlines() if l.strip().startswith("FAIL")]
    ck("P8 the reader's own --selftest: no FAIL line (%s)" % (fails[:2] if fails else "clean"), not fails, False)

    for name, ok, s679 in res:
        print("  %s  %s" % ("ok " if ok else "RED", name))
    if a.control:
        print("%d S679 check(s) red · %d older red · %d green" % (sum(1 for r in res if not r[1] and r[2]),
                                                              sum(1 for r in res if not r[1] and not r[2]), sum(1 for r in res if r[1])))
    else:
        g = sum(1 for r in res if r[1])
        print("%d of %d green" % (g, len(res)))
        sys.exit(0 if g == len(res) else 1)


if __name__ == "__main__":
    main()
