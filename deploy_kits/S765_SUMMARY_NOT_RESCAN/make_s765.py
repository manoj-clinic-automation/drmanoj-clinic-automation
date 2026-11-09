#!/usr/bin/env python3
"""make_s765.py -- kit S765_SUMMARY_NOT_RESCAN (S417, 09-Nov-2026; the owner 17:34 IST).

Alisha's reception list showed the dealers' month summaries she scanned on 08-Nov as 'Yeh bill nahi hai -- asli bill dhoondh kar scan kijiye',
and Aaj ka bill kaam said 'Dobara scan karo 22'. A summary (bills.kind 'Summary', S750) lands on the pharmacy lane, so scan_quality judged it
as a bill (no bill kind, no total) and the server's asking (porders_s454 S736) asked for it to be scanned again. Two anchored edits:
  /root/shared/scan_quality.py    16fb2402 -> (out)  detail(): a Summary paper is never judged -- None, so no 'bill nahi hai' anywhere
  /root/finance/porders_s454.py   c463b87c -> (out)  s736_plan: a Summary paper is 'gone' for the server's asking -- never asked, and the
                                                     server's own open ask on it is withdrawn (an ask a PERSON sent stays)
usage: python make_s765.py <src_dir> <out_dir>    (the box builds from /root/shared and /root/finance: give the file's own folder each time)
"""
import hashlib
import os
import sys

FROM = {"scan_quality.py": "16fb24029610ce7c0c0ecd502f529f7b", "porders_s454.py": "c463b87cf70212c8c20fcbb23beb6c38"}

EDITS = {
    "scan_quality.py": [(
        '''    if str(b.get("lane") or "") != "pharmacy" or str(b.get("status") or "") == "rejected" or b.get("page_of"):
        return None
''',
        '''    if str(b.get("lane") or "") != "pharmacy" or str(b.get("status") or "") == "rejected" or b.get("page_of"):
        return None
    if is_summary(b, reading):                                 # S765: a dealer's month summary is not a bill -- never judged as one
        return None
'''), (
        '''def detail(bill, reading, lie, settings=None):
''',
        '''def is_summary(bill, reading=None):
    """S765 (09-Nov-2026): a dealer's month summary (S750: reception's 'summary' tick -> bills.kind 'Summary', doc_kind 'summary'; its
    reading doc_kind 'summary'). Decided on bills.kind alone -- S754's heal sets it on every ticked or recognised summary, and a person's
    undo of a wrong recognition puts it back to a bill kind. It is not a bill: no bill kind, no bill total -- scan_quality never asks for it to be scanned again."""
    return str((bill or {}).get("kind") or "") == "Summary"           # the filed kind alone: a reader's guess never hides a bill (review)


def detail(bill, reading, lie, settings=None):
''')],
    "porders_s454.py": [(
        '''                or sid in f["picked"] or sid in f["dup"] or r.get("dup_of"))
''',
        '''                or sid in f["picked"] or sid in f["dup"] or r.get("dup_of")
                or str(r.get("kind") or "") == "Summary")             # S765: a dealer's summary (its filed kind) is no bill
''')],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    out = argv[-1]
    srcs = argv[1:-1]
    done = 0
    os.makedirs(out, exist_ok=True)
    for n, want in FROM.items():
        p = next((os.path.join(s, n) for s in srcs if os.path.isfile(os.path.join(s, n))), None)
        if p is None:
            sys.exit("STOP: %s is in none of %s -- nothing written" % (n, srcs))
        b = open(p, "rb").read()
        if md5(b) != want:
            sys.exit("STOP: %s is %s, not the live %s -- nothing written" % (n, md5(b), want))
        t = b.decode("utf-8")
        for i, (old, new) in enumerate(EDITS[n], 1):
            if t.count(old) != 1:
                sys.exit("STOP: %s edit %d: the anchor is found %d times -- nothing written" % (n, i, t.count(old)))
            t = t.replace(old, new)
        nb = t.encode("utf-8")
        open(os.path.join(out, n), "wb").write(nb)
        print("%-16s %s -> %s  (%d B)" % (n, want[:8], md5(nb), len(nb)))
        done += 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
