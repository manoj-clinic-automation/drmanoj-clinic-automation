#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""prove_s454_medical.py -- kit S454_BILL_REGISTER part 1, the medical PC's side: the LIVE watcher (marg_watch S397, 81145aa7, unchanged)
with the S454 reader beside it, in a scratch folder on this PC.

  1  the reader's own selftest (with the ORDER checks) passes; the watcher's own selftest passes with it beside;
  2  the watcher takes an order sheet saved as 'report.txt' (the default name): one .XLS in the spool, byte for byte the reader's own;
  3  a sheet cut short (no End line) is not converted: the watcher keeps it as refused with its reason (the PC's refusal note is part 4);
  4  parity: every text the S446 reader converted converts to the same bytes with the S454 one (the selftest samples; FromMedical\\refused_text).
The real sheet of 02-Oct is read from the owner's folder and never copied into the kit; nothing here prints a phone number.

    python -B prove_s454_medical.py --kit <medical dir> --watch <marg_watch.py S397> --old <marg_txt S446> [--real <the 02-Oct .txt>] [--refused <dir>] [--work <dir>]
"""
import argparse
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--watch", required=True)
    ap.add_argument("--old", required=True)
    ap.add_argument("--real", default="")
    ap.add_argument("--refused", default="")
    ap.add_argument("--work", default="", help="a scratch folder to work in (default: a new temporary folder)")
    a = ap.parse_args()
    ok = [0, 0]

    def ck(label, cond, got=None):
        ok[0] += 1
        if cond:
            ok[1] += 1
        print(("  ok   " if cond else "  FAIL ") + label + ("" if got is None else "   [%s]" % (got,)))
    work = tempfile.mkdtemp(prefix="s454med_", dir=(a.work or None))
    try:
        new_p = os.path.join(a.kit, "marg_txt.py")
        r = subprocess.run([sys.executable, "-B", new_p, "--selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        ck("1  the S454 reader's selftest passes (%d checks)" % r.stdout.count("  OK   "), "SELFTEST OK" in r.stdout)
        pc = os.path.join(work, "pc")
        os.makedirs(pc)
        shutil.copyfile(a.watch, os.path.join(pc, "marg_watch.py"))
        shutil.copyfile(new_p, os.path.join(pc, "marg_txt.py"))
        r = subprocess.run([sys.executable, "-B", os.path.join(pc, "marg_watch.py"), "--selftest"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=pc)
        ck("1  the live watcher's own selftest passes with the S454 reader beside it", "SELFTEST OK" in r.stdout, [l for l in r.stdout.splitlines() if "FAIL" in l][:3])
        sys.path.insert(0, pc)
        mt = load("marg_txt", os.path.join(pc, "marg_txt.py"))
        sys.modules["marg_txt"] = mt
        W = load("marg_watch_s454", os.path.join(pc, "marg_watch.py"))
        W.TXT_LIVE_FORCE = True
        spool = os.path.join(work, "spool")
        os.makedirs(spool)
        drop = os.path.join(work, "drop")
        os.makedirs(drop)
        lines = []
        sample = mt.ORDER_SAMPLE
        p = os.path.join(drop, "report.txt")
        with open(p, "wb") as fh:
            fh.write(sample)
        took = W.capture_text(p, spool, set(), lines.append)
        xs = [f for f in os.listdir(spool) if f.endswith(".XLS")]
        want = hashlib.md5(mt.convert(sample)[0]).hexdigest()
        ck("2  the watcher takes the sheet saved as 'report.txt': one .XLS in the spool, the reader's own bytes (%s)" % want[:8],
           took and len(xs) == 1 and hashlib.md5(open(os.path.join(spool, xs[0]), "rb").read()).hexdigest() == want and xs[0].endswith("__%s.XLS" % want[:8]), xs)
        ck("2  its log line names the reader S454", any("converted by marg_txt S454" in l for l in lines), lines[-1:])
        cut = sample[:sample.index(b"*** End of Report ***")]
        p2 = os.path.join(drop, "report2.txt")
        with open(p2, "wb") as fh:
            fh.write(cut)
        lines2 = []
        took2 = W.capture_text(p2, spool, set(), lines2.append)
        ref = os.path.join(work, "_captured_txt", "refused")
        kept = [f for f in os.listdir(ref)] if os.path.isdir(ref) else []
        ck("3  a sheet cut short is not converted; the watcher keeps it as refused, with its reason (the note reaches the owner in part 4)",
           not took2 and any(f.endswith(".why.txt") for f in kept) and len([f for f in os.listdir(spool) if f.endswith(".XLS")]) == 1, [lines2[-1:], kept])
        old = load("marg_txt_s446", a.old)
        texts = [("SELFTEST_SAMPLE", old.SELFTEST_SAMPLE), ("STOCK_SAMPLE", old.STOCK_SAMPLE)]
        if a.refused and os.path.isdir(a.refused):
            for n in sorted(os.listdir(a.refused)):
                if n.endswith(".txt") and not n.endswith(".why.txt"):
                    texts.append((n, open(os.path.join(a.refused, n), "rb").read()))
        same, diff = 0, []
        for n, raw in texts:
            ro = rn = None
            try:
                ro = hashlib.md5(old.convert(raw)[0]).hexdigest()
            except Exception as e:                                # noqa: BLE001
                ro = "refused: " + type(e).__name__
            try:
                rn = hashlib.md5(mt.convert(raw)[0]).hexdigest()
            except Exception as e:                                # noqa: BLE001
                rn = "refused: " + type(e).__name__
            if ro == rn:
                same += 1
            else:
                diff.append((n, ro, rn))
        ck("4  parity: %d texts the S446 reader read give the same verdict and the same bytes with S454's" % same, not diff, diff[:3])
        if a.real and os.path.isfile(a.real):
            raw = open(a.real, "rb").read()
            rows = mt.order_rows(raw)
            it = rows[2:-1]
            ck("5  Darpan's own sheet of 02-Oct (read from the owner's folder, not kept): ORDER, 11 suppliers, 32 lines, 4,046 units, 41,226",
               mt.kind(raw) == "ORDER" and len({r[0] for r in it}) == 11 and len(it) == 32 and rows[-1][6] == 4046.0 and rows[-1][10] == 41226.0)
            ck("5  old reader (S446): not recognised", old.kind(raw) is None)
    finally:
        shutil.rmtree(work, ignore_errors=True)
    print("PROVE_S454_MEDICAL %s -- %d of %d" % ("GREEN" if ok[0] == ok[1] else "RED", ok[1], ok[0]))
    return 0 if ok[0] == ok[1] else 1


if __name__ == "__main__":
    sys.exit(main())
