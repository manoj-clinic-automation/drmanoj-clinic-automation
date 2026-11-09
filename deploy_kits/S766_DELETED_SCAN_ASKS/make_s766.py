#!/usr/bin/env python3
"""make_s766.py -- kit S766_DELETED_SCAN_ASKS (S417, 09-Nov-2026; the owner 17:55 IST, urgent).

The 8 'Dobara scan karo' left on Alisha's list (B-0274 ... B-0288, server asks of 08-Nov) point at scans that no longer exist -- deleted in the
Scan App. The server's asking (S736) walks only the scans assets.db still holds, so its open ask on a DELETED scan was never withdrawn and
reception was asked for ever. One anchored edit:
  /root/finance/porders_s454.py   903df714 (S765) -> (out)  s736_plan withdraws its own open ask on a scan assets.db no longer holds,
                                                           unless that scan was rescanned (a newer scan names it in rescan_of: the rescan
                                                           closes the ask as done). An ask a PERSON sent stays.
usage: python make_s766.py <dir with porders_s454.py> <out_dir>
"""
import hashlib
import os
import sys

FROM = {"porders_s454.py": "903df7148662a18fa9825cc629322f74"}
OLD = '''        (out["escalated"] if item["tries"] >= S736_TRIES else out["ask"]).append(item)
    return out
'''
NEW = '''        (out["escalated"] if item["tries"] >= S736_TRIES else out["ask"]).append(item)
    for a in f["asks"]:                                       # S766: the scan was DELETED in the Scan App (assets.db no longer holds it,
        sid = int(a["asset_bill_id"])                         # _s736_facts fetched every asked id) -- the server's own open ask has no
        if (sid not in f["rows"] and sid not in f["kids"] and str(a.get("asked_by") or "") == S736_SERVER   # work left; a rescanned one
                and not a.get("done_at") and not a.get("withdrawn_at") and int(a["id"]) not in out["withdraw"]):   # is closed as done
            out["withdraw"].append(int(a["id"]))
    return out
'''


def md5(b):
    return hashlib.md5(b).hexdigest()


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    p = os.path.join(argv[1], "porders_s454.py")
    b = open(p, "rb").read()
    if md5(b) != FROM["porders_s454.py"]:
        sys.exit("STOP: porders_s454.py is %s, not the live %s -- nothing written" % (md5(b), FROM["porders_s454.py"]))
    t = b.decode("utf-8")
    if t.count(OLD) != 1:
        sys.exit("STOP: the anchor is found %d times -- nothing written" % t.count(OLD))
    nb = t.replace(OLD, NEW).encode("utf-8")
    os.makedirs(argv[2], exist_ok=True)
    open(os.path.join(argv[2], "porders_s454.py"), "wb").write(nb)
    print("porders_s454.py  903df714 -> %s  (%d B)" % (md5(nb), len(nb)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
