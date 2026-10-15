#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s565.py -- kit S565_DARPAN_SMS_AND_CLAUDE_BILLS (15-Oct-2026), part A: the anchored patcher.  Builds darpan_kal.html and
darpan_kal.py from the box's LIVE bytes by counted edits: each source must be at its FROM pin; each anchor must occur exactly once in
the text it is applied to, in order, else the build STOPS; each result must be at its TO pin.  Built in memory first; nothing is
written unless both build.
    python3 -B make_s565.py --fin /root/finance --out <dir>
Writes only into --out.  The change: Darpan's 'Kal ka hisaab' draws the bank's SMS when it stands in for the MPR ('बैंक SMS 07:02 से --
bank की report बाकी'; the owner's English view 'provisional -- bank SMS 07:02, MPR not in' / 'MPR never received'), and a day Darpan has
already posted is worked again when the SMS starts standing (as for a POS total)."""
import argparse
import hashlib
import os
import sys

PINS = {
    'darpan_kal.html': ('f5e279eb26e7f24827f29b79f95b2769', None),
    'darpan_kal.py': ('a8e11c31b9c80c1b01e63e948418d4a4', None),
}
TO = {
    'darpan_kal.html': '75d5a5b51b017abd5ad3aa408609a1ff',
    'darpan_kal.py': '8128598f745fca48a08472905f47da97',
}

EDITS = {
    'darpan_kal.html': [
        # 1 -- the helper, once: the SMS time out of the label ('07:02' / '16-Oct 07:02' / '')
        ("function sec(h){return '<div class=\"sec\">'+h+'</div>';}\n",
         "function sec(h){return '<div class=\"sec\">'+h+'</div>';}\n"
         "/* S565: the bank SMS's time, out of the stand-in's label ('बैंक SMS 07:02' / 'बैंक SMS 16-Oct 07:02'); '' when it has none */\n"
         "const smsAt=c=>{const m=String((c.standin&&c.standin.label)||\"\").match(/(\\d{2}-[A-Za-z]{3} )?\\d{2}:\\d{2}$/);return m?m[0]:\"\";};\n"),
        # 2 -- Darpan's view: the 'sms' case first; the 'pos' string and the plain fallback byte for byte
        ("(c.online_provisional?(c.online_source===\"pos\"?'<span class=\"badge amber\">POS total से — bank की report बाकी</span>'",
         "(c.online_provisional?(c.online_source===\"sms\"?'<span class=\"badge amber\">'+esc(c.standin&&c.standin.label||\"बैंक SMS\")+' से — bank की report बाकी</span>':"
         "c.online_source===\"pos\"?'<span class=\"badge amber\">POS total से — bank की report बाकी</span>'"),
        # 3 -- the owner's note under 'online' (English; the apostrophe escaped as Marg\'s is)
        (" if(c.online_source===\"pos\"&&c.standin) t+='<div class=\"muted\">UPI total read from the POS machine — '",
         " if(c.online_source===\"sms\") t+='<div class=\"muted\">UPI total from the bank\\'s settlement SMS of '+esc(smsAt(c))+' — the MPR mail is not in yet.</div>';   /* S565 */\n"
         " if(c.online_source===\"pos\"&&c.standin) t+='<div class=\"muted\">UPI total read from the POS machine — '"),
        # 4 -- the owner's 'online' row (English, never the Devanagari label); 'pos' and Marg byte for byte
        ("(c.online_provisional?(c.online_source===\"pos\"?'<span class=\"badge amber\">'+esc((c.standin&&c.standin.label)||\"provisional — POS total, bank not in\")+'</span>'",
         "(c.online_provisional?(c.online_source===\"sms\"?'<span class=\"badge amber\">provisional — bank SMS '+esc(smsAt(c))+(c.standin&&c.standin.never?', MPR never received':', MPR not in')+'</span>':"
         "c.online_source===\"pos\"?'<span class=\"badge amber\">'+esc((c.standin&&c.standin.label)||\"provisional — POS total, bank not in\")+'</span>'"),
    ],
    'darpan_kal.py': [
        # 1 -- _refresh_if_needed: a posted day is worked again when the SMS starts standing too
        ("            (calc[\"applied\"] and calc.get(\"online_source\") == \"pos\" and row.get(\"state\") != \"waiting_report\"\n"
         "             and int(row.get(\"online_p\") or 0) != int(calc[\"online_p\"])):      # S496: decided before the POS total was confirmed\n",
         "            (calc[\"applied\"] and calc.get(\"online_source\") in (\"pos\", \"sms\") and row.get(\"state\") != \"waiting_report\"\n"
         "             and int(row.get(\"online_p\") or 0) != int(calc[\"online_p\"])):      # S496: decided before the POS total was confirmed;\n"
         "        # S565: ... or before the bank's settlement SMS stood in (the MPR replacing it is the condition above)\n"),
    ],
}


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(name, src_bytes, check_to=True):
    frm = PINS[name][0]
    if md5(src_bytes) != frm:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- it changed after this kit was built" % (name, md5(src_bytes), frm))
    t = src_bytes.decode("utf-8")
    for i, (a, b) in enumerate(EDITS[name], 1):
        n = t.count(a)
        if n != 1:
            raise SystemExit("STOP: %s edit %d: its anchor occurs %d times (must be exactly once)" % (name, i, n))
        t = t.replace(a, b, 1)
    out = t.encode("utf-8")
    if check_to and md5(out) != TO[name]:
        raise SystemExit("STOP: %s built to %s, not its TO pin %s" % (name, md5(out), TO[name]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fin", default="/root/finance")
    ap.add_argument("--out", required=True)
    ap.add_argument("--print-to", action="store_true", help="build without the TO check and print the md5s (kit authoring only)")
    a = ap.parse_args()
    built = {}
    for name in PINS:                              # in memory first, both
        with open(os.path.join(a.fin, name), "rb") as fh:
            built[name] = build(name, fh.read(), check_to=not a.print_to)
    if a.print_to:
        for name, out in built.items():
            print("%s %s" % (name, md5(out)))
        if a.out != "-":
            os.makedirs(a.out, exist_ok=True)
            for name, out in built.items():
                with open(os.path.join(a.out, name), "wb") as fh:
                    fh.write(out)
        return 0
    os.makedirs(a.out, exist_ok=True)
    for name, out in built.items():
        with open(os.path.join(a.out, name), "wb") as fh:
            fh.write(out)
        print("built %s %s -> %s (%d counted edits)" % (name, PINS[name][0][:8], TO[name][:8], len(EDITS[name])))
    return 0


if __name__ == "__main__":
    sys.exit(main())
