#!/usr/bin/env python3
"""make_s784.py FINANCE_DIR OUT_DIR -- kit S784_HUB_GOTO_LABEL (S426, 11-Nov-2026, the Sanjeevni chat; the owner's go 06:38 IST).
finance_ui/finance_approvals.html: from its FROM pin, ONE line changed -- the Go-to link to the Purchase bills page gets its new name.
Refuses unless the live file is at its FROM pin and the old line is there exactly once."""
import hashlib
import os
import sys

FROM = "dcd94412d3c342b38c237d86d451178b"
OLD = '        <a href="/finance/purchase/page/scans">Scan register (bills ↔ Marg)</a>\n'
NEW = '        <a href="/finance/purchase/page/scans">Purchase bills — in Marg · scanned · differences</a>\n'


def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def main(fin, out):
    src = os.path.join(fin, "finance_ui", "finance_approvals.html")
    if md5(src) != FROM:
        print("REFUSED: finance_approvals.html is %s, not %s" % (md5(src)[:8], FROM[:8]))
        return 2
    s = open(src, encoding="utf-8").read()
    if s.count(OLD) != 1:
        print("REFUSED: the Go-to line is there %d times, not once" % s.count(OLD))
        return 2
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "finance_approvals.html"), "w", encoding="utf-8", newline="") as fh:
        fh.write(s.replace(OLD, NEW, 1))
    print("built finance_approvals.html %s -> %s" % (FROM[:8], md5(os.path.join(out, "finance_approvals.html"))[:8]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
