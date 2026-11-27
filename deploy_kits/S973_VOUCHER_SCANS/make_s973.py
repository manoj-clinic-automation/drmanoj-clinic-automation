#!/usr/bin/env python3
"""make_s973.py -- builds kit S973_VOUCHER_SCANS's files from the FROM bytes (each pinned by md5) and the blocks beside this file.
    python3 make_s973.py FROM_DIR OUT_DIR
Every anchor must be found exactly once; any miss stops the build with nothing written."""
import hashlib, os, shutil, sys

FROM, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
PIN = {"claude_reader.py": "5b27b2269f4f358a36cd62aef6b0eb7a", "asset_register.py": "a325d0f400923e1989ff4cd2a4df408d",
       "voucher_judge.py": "6c7259418481cd9f37099f93a9ca7b17", "voucher_inquiry.py": "ac76b9d339de6b58b7835cab7e46e08d",
       "amir_day.py": "27a2a128f8e6fbdbf0c015727db70538", "porders_s454.py": "3f52d1f390ff704d152fd3b96bba5afc",
       "scan_quality.py": "505a114f34452b5be994b04eca36e4b7"}
APPEND = {"claude_reader.py": "block_reader.py", "asset_register.py": "block_ar.py", "voucher_judge.py": "block_vj.py",
          "voucher_inquiry.py": "block_vi.py", "amir_day.py": "block_amir.py", "porders_s454.py": "block_porders.py",
          "scan_quality.py": "block_sq.py"}
EDITS = {
    "asset_register.py": [
        ("{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense','Summary','Pharmacy credit note') %}",
         "{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense','Summary','Pharmacy credit note','Stock voucher') %}"),
        ('kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense", "Summary", "Pharmacy credit note") else',
         'kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense", "Summary", "Pharmacy credit note", "Stock voucher") else'),
        ("_challanSet(false);_summarySet(false);if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;}",
         "_challanSet(false);_summarySet(false);if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;if(!window.SCANNER_CONFIG.uploadFields.vendor){delete window.SCANNER_CONFIG.uploadFields.bill_no;}}"),
        ("d.addEventListener('change',function(){setTimeout(function(){if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;}",
         "d.addEventListener('change',function(){setTimeout(function(){if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){delete window.SCANNER_CONFIG.uploadFields.rescan_of;if(!window.SCANNER_CONFIG.uploadFields.vendor){delete window.SCANNER_CONFIG.uploadFields.bill_no;}}")],
        "voucher_judge.py": [
        ('named = {(k, no, int(n)): (norm(p), it) for k, no, n, p, it in con.execute("SELECT kind, no, n, printed, item FROM mi_voucher_name")}',
         'named = {(k, no, int(n)): (norm(p), it, str(sc or "")) for k, no, n, p, it, sc in con.execute("SELECT kind, no, n, printed, item, source FROM mi_voucher_name")}   # S973: + its source'),
        ('d["item"], d["named_by"] = norm(nm[1]), "your Marg screen"',
         'd["item"], d["named_by"] = norm(nm[1]), ("the voucher\'s scan" if nm[2].startswith("scan") else "your Marg screen")   # S973')],
    "porders_s454.py": [
        ('or str(r.get("kind") or "") == "Summary")             # S765: a dealer\'s summary (its filed kind) is no bill',
         'or str(r.get("kind") or "") in ("Summary", "Stock voucher"))   # S765: a dealer\'s summary (its filed kind) is no bill; S973: nor a Marg stock voucher')],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


out = {}
for f, pin in PIN.items():
    b = open(os.path.join(FROM, f), "rb").read()
    if md5(b) != pin:
        sys.exit("STOP: %s is %s, not the pinned %s -- nothing written" % (f, md5(b), pin))
    s = b.decode("utf-8")
    if "S973" in s:
        sys.exit("STOP: %s already carries S973 -- nothing written" % f)
    for old, new in EDITS.get(f, []):
        if s.count(old) != 1:
            sys.exit("STOP: %s anchor found %d times: %s -- nothing written" % (f, s.count(old), old[:80]))
        s = s.replace(old, new, 1)
    blk = open(os.path.join(HERE, APPEND[f]), encoding="utf-8").read()
    out[f] = (s.rstrip("\n") + "\n" + blk.rstrip("\n") + "\n").encode("utf-8")
os.makedirs(OUT, exist_ok=True)
for f, b in out.items():
    open(os.path.join(OUT, f), "wb").write(b)
shutil.copy(os.path.join(HERE, "voucher_scan.py"), os.path.join(OUT, "voucher_scan.py"))
for f in sorted(list(out) + ["voucher_scan.py"]):
    print("%s  %s" % (md5(open(os.path.join(OUT, f), "rb").read()), f))
