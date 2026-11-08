#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s753.py -- S753_SUMMARY_SCANS_READ: the anchored changes and the appended section of the two live files (this project's only).
    python3 -B make_s753.py <finance dir> <out dir> [<dir holding sec_sr753.txt>]
Each FROM file must carry its pinned md5 (the live bytes of 08-Nov 11:39 IST: the 08-Nov bundle + kit S749 + kit S750); every anchor must
stand EXACTLY the number of times named; the TO md5s are printed. The section is read from sec_sr753.txt beside this script."""
import hashlib
import os
import sys

FROM = {"finance/scan_register.py": "fdb0960f83b98f68b90b340d0655aa37",     # S750's TO (live 08-Nov 11:39 IST)
        "finance/purchase_app.py": "262cafd311a7d1e9d3587aefc8ac6cd1"}      # S750's TO
APPEND = {"finance/scan_register.py": "sec_sr753.txt"}

# scan_register.py -- (old, new, how many times the anchor stands)
SR_EDITS = [
    # (1) the lines are read first; the month comes from the bills listed, then the period's last day, then reception's month, then the scan's
    ('''        pt = str((d.get("period_to") or "")) if r["read"] else ""
        bm = str(r.get("bill_month") or "")
        if re.match(r"^\\d{4}-\\d\\d-\\d\\d$", pt):
            r["month"] = pt[:7]
        elif re.match(r"^\\d{4}-\\d\\d$", bm) and bm != str(r.get("day") or "")[:7]:
            r["month"] = bm                                   # reception chose an earlier month on purpose
        elif r.get("day"):
            r["month"] = _s750_prev_month(str(r["day"])[:7])  # a summary is scanned early the next month; the intake's default month is the scan's
        else:
            r["month"] = bm
        lines = []
        for ln in (d.get("lines") or []) if r["read"] else []:
            if not isinstance(ln, dict):
                continue
            lines.append(dict(kind=str(ln.get("kind") or "other"), no=str(ln.get("no") or ""), date=str(ln.get("date") or "")[:10] if ln.get("date") else "",
                              amount_p=_amount_p(ln.get("amount"))))
        r["lines"] = lines
''',
     '''        lines = []
        for ln in (d.get("lines") or []) if r["read"] else []:
            if not isinstance(ln, dict):
                continue
            lines.append(dict(kind=str(ln.get("kind") or "other"), no=str(ln.get("no") or ""), date=str(ln.get("date") or "")[:10] if ln.get("date") else "",
                              amount_p=_amount_p(ln.get("amount"))))
        r["lines"] = lines
        pt = str((d.get("period_to") or "")) if r["read"] else ""
        bm = str(r.get("bill_month") or "")
        lm = _s753_lines_month(lines)                         # S753: the month the listed bills fall in -- the paper's own word, not its printing date
        if lm:
            r["month"] = lm
        elif re.match(r"^\\d{4}-\\d\\d-\\d\\d$", pt):
            r["month"] = pt[:7]
        elif re.match(r"^\\d{4}-\\d\\d$", bm) and bm != str(r.get("day") or "")[:7]:
            r["month"] = bm                                   # reception chose an earlier month on purpose
        elif r.get("day"):
            r["month"] = _s750_prev_month(str(r["day"])[:7])  # a summary is scanned early the next month; the intake's default month is the scan's
        else:
            r["month"] = bm
''', 1),
    # (2) the pharmacy's own name is never a candidate
    ('''        cands = [str(s.get("vendor") or ""), str((s.get("reading") or {}).get("dealer") or "")]
        key = ""
''',
     '''        cands = [_s753_not_us(s.get("vendor")), _s753_not_us((s.get("reading") or {}).get("dealer"))]   # S753: never the buyer, Sanjeevni itself
        key = ""
''', 1),
    # (3) the fallback: the dealer whose Marg bills the paper lists
    ('''                key = hit[0]
                break
        out[sid] = key
    return out
''',
     '''                key = hit[0]
                break
        s["dealer_by_bills"] = False
        if not key:                                           # S753: no printed name matched -- the bills on the paper name the dealer
            key = _s753_dealer_by_bills(con, s, sups)
            s["dealer_by_bills"] = bool(key)
        out[sid] = key
    return out
''', 1),
    # (2b) the unknown row never carries our own name
    ('''        out.append(dict(key="", name=str((s.get("reading") or {}).get("dealer") or s.get("vendor") or "a dealer the reader could not name"), bills=[],''',
     '''        out.append(dict(key="", name=_s753_not_us((s.get("reading") or {}).get("dealer")) or _s753_not_us(s.get("vendor")) or "a dealer the reader could not name", bills=[],''', 1),
    # (4) the footer: the count of bills beside their total; the word when the dealer was named by its bills
    ('''    tot = []
    if s.get("total_bills_p") is not None:
        tot.append("bills %s" % rs(s["total_bills_p"]))
''',
     '''    tot = []
    nb = sum(1 for x in (s.get("lines") or []) if isinstance(x, dict) and x.get("kind") == "bill")   # S753: the owner's ask (17:32 IST 8-Nov)
    if s.get("total_bills_p") is not None:
        tot.append(("%d bill%s %s" % (nb, "" if nb == 1 else "s", rs(s["total_bills_p"]))) if nb else ("bills %s" % rs(s["total_bills_p"])))
    elif nb:
        tot.append("%d bill%s" % (nb, "" if nb == 1 else "s"))
    if s.get("dealer_by_bills"):
        tot.append("dealer named by its bills")
''', 1),
]

# purchase_app.py -- the viewer serves a Summary too
PA_EDITS = [
    ('''def _s446_file_bytes(sid):
    """(name, bytes) of one captured pharmacy scan -- read only, from the asset app's store; None when it is not one."""''',
     '''def _s446_file_bytes(sid, kinds=("Pharmacy",)):           # S753: kinds -- the s738 viewer serves a dealer's Summary too
    """(name, bytes) of one captured pharmacy scan -- read only, from the asset app's store; None when it is not one."""''', 1),
    ('''        r = acon.execute("SELECT id, vendor, bill_no, bill_date, source_stored FROM bills WHERE id=? AND kind='Pharmacy' AND status='captured'",
                         (int(sid),)).fetchone()''',
     '''        r = acon.execute("SELECT id, vendor, bill_no, bill_date, source_stored FROM bills WHERE id=? AND kind IN (%s) AND status='captured'"
                         % ",".join("?" * len(kinds)), (int(sid),) + tuple(str(k) for k in kinds)).fetchone()''', 1),
    ('''    got = _s446_file_bytes(sid)
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    data = got[1]''',
     '''    got = _s446_file_bytes(sid, ("Pharmacy", "Summary"))    # S753: the folded viewer and 'Open the scan in a new tab' open a summary too
    if got is None:
        return jsonify(ok=False, error="not_found", message="Yeh scan nahi mila."), 404
    data = got[1]''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(text, edits, name):
    for old, new, n in edits:
        c = text.count(old)
        if c != n:
            sys.exit("!! %s: anchor stands %d time(s), expected %d:\n%s" % (name, c, n, old[:160]))
        text = text.replace(old, new)
    return text


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    fin, out = sys.argv[1], sys.argv[2]
    here = sys.argv[3] if len(sys.argv) > 3 else os.path.dirname(os.path.abspath(__file__))
    for rel, want in FROM.items():
        src = os.path.join(fin, os.path.basename(rel))
        b = open(src, "rb").read()
        if md5(b) != want:
            sys.exit("!! %s is %s, expected %s -- not the live bytes this kit was built on; STOP" % (src, md5(b)[:8], want[:8]))
        if b"\r\n" in b:
            sys.exit("!! %s carries CRLF; STOP" % src)
        t = b.decode("utf-8")
        t = apply(t, SR_EDITS if rel.endswith("scan_register.py") else PA_EDITS, rel)
        if rel in APPEND:
            sec = open(os.path.join(here, APPEND[rel]), "rb").read().decode("utf-8")
            if "KIT_S753" in t:
                sys.exit("!! %s already carries S753; STOP" % src)
            t = t.rstrip("\n") + "\n" + sec
        nb = t.encode("utf-8")
        d = os.path.join(out, os.path.dirname(rel))
        os.makedirs(d, exist_ok=True)
        open(os.path.join(out, rel), "wb").write(nb)
        print("%s  %s -> %s" % (rel, want[:8], md5(nb)))


if __name__ == "__main__":
    main()
