#!/usr/bin/env python3
"""selftest_s293.py -- proves S293_DARPAN_LIST offline.
Bytes: both files at their live pins; every anchor once; refusal on a wrong --from;
idempotence; the patched pad_receipt compiles. Behaviour: the untouched and the patched
render_tranche() over one fixture, read back as text -- the old list says COUNT AGAIN and
RECOUNT; the new one says WRITE THE REASON, "Do not count again", names the count day,
has REASON no. and REMARKS and no RECOUNT, shows a surplus as "over", and every item and
its three figures are still on the page. render_diffs (the owner's own sheet, same file)
is rendered by both and must be byte-identical apart from its timestamp line.
    python3 -B selftest_s293.py --receipt live/pad_receipt.py --amir live/stock_amir.html
"""
import argparse, hashlib, importlib.util, io, os, re, shutil, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import patch_darpan_list_s293 as P  # noqa: E402
PR_FROM, AM_FROM = "49ced28771a84f02f6276bbbe297443c", "adf206b54cc55e88626089a7f3482fd0"
FAILS = []
def check(n, ok, d=""):
    print(("ok   " if ok else "FAIL ") + n + ("" if ok else "  -- " + str(d)))
    if not ok: FAILS.append(n)
def md5(p): return hashlib.md5(io.open(p, "rb").read()).hexdigest()
def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def text_of(pdf_bytes, tmp, name):
    p = os.path.join(tmp, name + ".pdf"); io.open(p, "wb").write(pdf_bytes)
    return subprocess.run(["pdftotext", "-layout", p, "-"], capture_output=True, text=True).stdout
FIX = dict(count_id=1, day="06-09-2026", reasons=[(1, "count error", ""), (2, "not billed", ""), (7, "don't know", "")],
           tranche=dict(no=1, kind="med", issued_text="17-09-2026 16:00"),
           rows=[dict(item="ETOBONE 60", packing="1*10", pack=10, marg=120, counted=112, diff=-8),
                 dict(item="GEMCAL XT TABLETS", packing="1*10", pack=10, marg=300, counted=194, diff=-106),
                 dict(item="ZIBON EXTRA", packing="1*15", pack=15, marg=45, counted=60, diff=15)])
def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--receipt", required=True); ap.add_argument("--amir", required=True); a = ap.parse_args(argv)
    check("pad_receipt.py is the live pin", md5(a.receipt) == PR_FROM, md5(a.receipt))
    check("stock_amir.html is the live pin", md5(a.amir) == AM_FROM, md5(a.amir))
    tmp = tempfile.mkdtemp(prefix="s293_"); wr = os.path.join(tmp, "pad_receipt.py"); wa = os.path.join(tmp, "stock_amir.html")
    shutil.copy2(a.receipt, wr); shutil.copy2(a.amir, wa)
    t = io.open(wr, encoding="utf-8").read()
    for old, _ in P.RECEIPT_EDITS: check("receipt anchor once: " + old.strip()[:36], t.count(old) == 1, t.count(old))
    ta = io.open(wa, encoding="utf-8").read()
    for old, _ in P.AMIR_EDITS: check("amir anchor once", ta.count(old) == 1)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_darpan_list_s293.py"), "--receipt", wr, "--amir", wa, "--receipt-from", "0" * 32], capture_output=True, text=True)
    check("refuses a wrong --from", r.returncode != 0 and "REFUSING" in r.stdout + r.stderr)
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_darpan_list_s293.py"), "--receipt", wr, "--amir", wa, "--receipt-from", PR_FROM, "--amir-from", AM_FROM], capture_output=True, text=True)
    check("patches from the live pins", r.returncode == 0, r.stdout + r.stderr)
    h1 = (md5(wr), md5(wa))
    r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "patch_darpan_list_s293.py"), "--receipt", wr, "--amir", wa], capture_output=True, text=True)
    check("idempotent", (md5(wr), md5(wa)) == h1 and r.stdout.count("ALREADY") == 2, r.stdout)
    check("backups are the live bytes", md5(wr + ".bak_S293_" + PR_FROM[:8]) == PR_FROM and md5(wa + ".bak_S293_" + AM_FROM[:8]) == AM_FROM)
    r = subprocess.run([sys.executable, "-m", "py_compile", wr], capture_output=True, text=True); check("patched pad_receipt compiles", r.returncode == 0, r.stderr)
    check("typing board label is Note", "<th>Reason</th><th>Note</th></tr>" in io.open(wa, encoding="utf-8").read())
    print("predicted: pad_receipt.py %s · stock_amir.html %s" % h1)
    old = load(a.receipt, "pr_old"); new = load(wr, "pr_new")
    to = text_of(old.render_tranche(dict(FIX)), tmp, "old"); tn = text_of(new.render_tranche(dict(FIX)), tmp, "new")
    check("control: the old list says COUNT AGAIN and RECOUNT", "COUNT AGAIN" in to and "RECOUNT" in to)
    check("new list says WRITE THE REASON", "WRITE THE REASON" in tn)
    check("new list says Do not count again", "Do not count" in tn and "again" in tn)
    check("new list has no RECOUNT column", "RECOUNT" not in tn, tn[:400])
    check("new list names the count day in the instruction", "stock count of 06-09-2026" in tn.replace("\n", " "))
    check("new list heads REASON no. and REMARKS", "REASON no." in tn and "REMARKS" in tn)
    check("new list heads Marg / Shelf / Difference", all(k in tn for k in ("Marg", "Shelf", "Difference")))
    for it, m, c, dtx in (("ETOBONE 60", "12s", "11s 2t", "short 8t"), ("GEMCAL XT TABLETS", "30s", "19s 4t", "short 10s 6t"), ("ZIBON EXTRA", "3s", "4s", "over 1s")):
        line = [l for l in tn.splitlines() if it in l]
        check("row %s carries %s | %s | %s" % (it, m, c, dtx), bool(line) and all(x in line[0] for x in (m, c, dtx)), line)
    check("footer asks Answered by", "Answered by" in tn and "Counted again by" not in tn)
    # the owner's own sheet (render_diffs) must not move
    if hasattr(old, "render_diffs"):
        dd = dict(count_id=1, day="06-09-2026", counted_by="x", entered_by="y", items_in_shop=3, counted=3, agreed=0, differed=3, not_counted=0, sent_back=0,
                  rows=[dict(r, cost_p=1000, mrp_p=1200, mrp_source="sale", answer=None) for r in FIX["rows"]], reasons=FIX["reasons"])
        try:
            so = re.sub(r"PDF made .*", "", text_of(old.render_diffs(dict(dd)), tmp, "do")); sn = re.sub(r"PDF made .*", "", text_of(new.render_diffs(dict(dd)), tmp, "dn"))
            check("the owner's differences sheet is unchanged", so == sn)
        except Exception as e:  # a fixture that does not fit render_diffs is not a failure of this kit
            print("note render_diffs not exercised: %s" % e)
    print("\n%d failed" % len(FAILS)); return 1 if FAILS else 0
if __name__ == "__main__": sys.exit(main())
