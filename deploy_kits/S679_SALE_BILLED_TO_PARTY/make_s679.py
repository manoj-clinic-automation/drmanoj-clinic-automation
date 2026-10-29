#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s679.py -- kit S679_SALE_BILLED_TO_PARTY (29-Oct-2026, Sanjeevni session 367).

    python3 -B make_s679.py --only pc     <dir with marg_txt.py + marg_watch.py>  <outdir>    -> <outdir>/pc/{marg_txt.py, marg_watch.py}
    python3 -B make_s679.py --only server <root>                                  <outdir>    -> <outdir>/finance/reports_tile.py

THE OWNER'S RULING (16:55 IST 29-Oct): a sale is only cash or UPI -- never billed to a party account.  On 28-Oct a stand-in at the
counter billed A004482 to DEEPAM PHARM; Marg's text export then carries the party's name in the D.R. column where .CASH / .UPI stands.
The medical PC's reader stopped at that line with "a bill row whose payment head is not where the header says", its note reached the
server as a READER STOP, and Shavez's Aaj ki reports said "aapko kuch nahi karna" -- so the 28-Oct sale never came and nobody was told why.

WHAT (each anchor must occur exactly once, else the builder refuses):
  marg_txt.py   (medical PC)  18fa8a83 -> a bill row whose D.R. column holds a WORD that is not a payment head (no leading '.', not
                              blank or '#', set off by a space on its left) is refused as "line N: bill <no> is billed to the party account
                              <name>, not cash or UPI -- correct the bill in Marg (Cash or UPI), then export again".  VERSION S679.
                              Every other bill row reads exactly as before; every other refusal keeps its words.
  marg_watch.py (medical PC)  39fa2773 -> _note_reason lets that reason leave the PC as "the reader refused it: bill <no> is billed to a
                              party account, not cash or UPI" -- the bill number (exempt from the six-digit mask) and never the party's
                              name; idempotent (the Drive .why passes it through again).  The start line says S679.
  reports_tile.py (server)    535b5790 -> hindi_reason names it first: "Bill <no> party ke khaate mein bana hai -- bikri sirf Cash ya UPI
                              mein hoti hai. Marg mein yeh bill Cash ya UPI mein theek kijiye, phir report dobara nikaaliye."  It is NOT a
                              reader stop (S556_STOP is an exact pattern), so the row is 'wrong' and the duty stays due -- he must act.
"""
import hashlib
import os
import sys

PINS = {
    "marg_txt.py": "18fa8a8382f5444cd3faa25a51fd0489",
    "marg_watch.py": "39fa27739757ff8e9c8731f77d07b40b",
    "reports_tile.py": "535b579011004ba2e8d8c41070067b2c",
}

EDITS = {
    "marg_txt.py": [
        ('VERSION = "S638"', 'VERSION = "S679"'),
        ('        if RE_BILL.match(c0):\n'
         '            blank = len(s) >= p_gross and s[p_dr - 1] == " " and s[p_dr:p_gross].strip(" #") == ""   # S546: no payment word\n',
         '        if RE_BILL.match(c0):\n'
         '            blank = len(s) >= p_gross and s[p_dr - 1] == " " and s[p_dr:p_gross].strip(" #") == ""   # S546: no payment word\n'
         '            party = s[p_dr:p_gross].strip(" #") if (len(s) >= p_gross and s[p_dr - 1] == " " and s[p_dr] not in " .") else ""\n'
         '            if party.startswith(".") or re.match(r"^[#\\-. ]*(?:CASH|UPI)\\b", party, re.I):\n'
         '                party = ""                                       # a payment word, however printed, is never a party\n'
         '            if party:                                            # S679 (the owner, 29-Oct): a sale is cash or UPI, never a party\n'
         '                raise Refused("line %d: bill %s is billed to the party account %s, not cash or UPI -- correct the bill in Marg "\n'
         '                              "(Cash or UPI), then export again" % (n, c0, party))\n'),
    ],
    "marg_watch.py": [
        ('    if w.startswith("the reader refused it"):\n'
         '        m = re.match(r"the reader refused it: line (\\d+)\\b", w)\n',
         '    mp = S679_PARTY.match(w)\n'
         '    if mp:                                                      # S679: the bill number may leave the PC; the party\'s name never\n'
         '        return "the reader refused it: bill %s is billed to a party account, not cash or UPI" % mp.group(1)\n'
         '    if w.startswith("the reader refused it"):\n'
         '        m = re.match(r"the reader refused it: line (\\d+)\\b", w)\n'),
        ('\ndef _note_reason(why):\n',
         '\nS679_PARTY = re.compile(r"the reader refused it: (?:line \\d+: )?bill ([A-Z]{1,3}[0-9]{3,9}) is billed to (?:the|a) party account\\b")\n'
         '\n\ndef _note_reason(why):\n'),
        ('    out("marg_watch S556 starting -- ', '    out("marg_watch S679 starting -- '),
    ],
    "reports_tile.py": [
        ('def hindi_reason(reason, verdict=""):\n'
         '    """The router\'s English reason -> one line a counter person can act on.  The English text is\n'
         '    shown beneath it in small type, so nothing is hidden from the owner."""\n',
         'S679_PARTY = re.compile(r"bill ([A-Z]{1,3}[0-9]{3,9}) is billed to (?:the|a) party account")\n'
         '\n\n'
         'def hindi_reason(reason, verdict=""):\n'
         '    """The router\'s English reason -> one line a counter person can act on.  The English text is\n'
         '    shown beneath it in small type, so nothing is hidden from the owner."""\n'
         '    mp = S679_PARTY.search(str(reason or ""))\n'
         '    if mp:                                                      # S679 (the owner, 29-Oct): a sale is cash or UPI, never a party\n'
         '        return ("Bill %s party ke khaate mein bana hai -- bikri sirf Cash ya UPI mein hoti hai. "\n'
         '                "Marg mein yeh bill Cash ya UPI mein theek kijiye, phir report dobara nikaaliye." % mp.group(1))\n'),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, src):
    if md5(src) != PINS[name]:
        raise SystemExit("REFUSED: %s is %s, not its FROM pin %s" % (name, md5(src)[:8], PINS[name][:8]))
    s = src.decode("utf-8")
    for i, (old, new) in enumerate(EDITS[name], 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: %s anchor %d occurs %d times (must be exactly once)" % (name, i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    a = sys.argv[1:]
    if len(a) != 4 or a[0] != "--only" or a[1] not in ("pc", "server"):
        raise SystemExit(__doc__)
    which, src_dir, out = a[1], a[2], a[3]
    jobs = ([("marg_txt.py", os.path.join(src_dir, "marg_txt.py"), os.path.join(out, "pc", "marg_txt.py")),
             ("marg_watch.py", os.path.join(src_dir, "marg_watch.py"), os.path.join(out, "pc", "marg_watch.py"))]
            if which == "pc" else
            [("reports_tile.py", os.path.join(src_dir, "finance", "reports_tile.py"), os.path.join(out, "finance", "reports_tile.py"))])
    for name, src, dst in jobs:
        with open(src, "rb") as fh:
            b = build(name, fh.read())
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "wb") as fh:
            fh.write(b)
        print("built %s %s -> %s (%d edits)" % (name, PINS[name][:8], md5(b)[:8], len(EDITS[name])))


if __name__ == "__main__":
    main()
