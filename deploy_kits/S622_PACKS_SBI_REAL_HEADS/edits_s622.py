#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s622.py -- kit S622 (session S336, 22-Oct-2026, D755): exact, counted edits on the two S621 files.
    python3 edits_s622.py py   LIVE OUT [KIT]     /root/finance/packs.py   6ed8e18a -> the S622 file
    python3 edits_s622.py html LIVE OUT [KIT]     /root/finance/packs.html da0cbb8c -> the S622 file
(exit 0 only if every anchor occurs exactly once and OUT = KIT)

FOUND ON THE LIVE SHELF, 22-Oct-2026 09:18 IST: the owner added his four 20-Oct SBI PDFs and typed their passwords. All four
opened. Dr Bhawna's savings was placed with its period; her loan was placed with NO period; his own savings and loan stayed
unplaced ("no slot's words are in the holder text"). Their heads, read through the owner-only text door (numbers masked):
  * SBI prints the holder on the line that carries 'State Bank of India' (to its right), with no 'Account Name' label --
    and it prints his name as 'MANOJ KUMARAGARWAL', no space between KUMAR and AGARWAL;
  * the loan statements (both 'Auto Loan') print the period as 'Statement : 01-04-2026 to 20-10-2026' -- no 'From'.
The S621 reader was built on made-up heads in other layouts (F-975). Now:
  * the holder is taken from that line when no label names it, and KUMARAGARWAL / MANOJKUMAR are read as two words;
  * 'Statement :' introduces a period as 'Statement From :' does;
  * on the page, a locked file added by hand gets a 'Go to its password box' button that opens the passwords card at once.
"""
import hashlib
import sys

EDITS = {
    "py": [
        ('_SBI_PERIOD = re.compile(r"(?i)(?:from|period)\\s*(?:date)?',
         '_SBI_PERIOD = re.compile(r"(?i)(?:from|period|statement)\\s*(?:date)?'),          # S622: the loans print 'Statement : a to b'
        ('def _sbi_fold(s):\n    """Bhavna is Bhawna: the slot words and the bank\'s spelling meet."""\n'
         '    return re.sub(r"\\bBHAVNA\\b", "BHAWNA", str(s or "").upper())\n',
         'def _sbi_fold(s):\n    """Bhavna is Bhawna: the slot words and the bank\'s spelling meet. S622: SBI prints MANOJ KUMARAGARWAL -- two words."""\n'
         '    s = re.sub(r"\\bBHAVNA\\b", "BHAWNA", str(s or "").upper())\n'
         '    s = re.sub(r"KUMAR(?=AGARWAL)", "KUMAR ", s)\n'
         '    return re.sub(r"\\bMANOJ(?=KUMAR)", "MANOJ ", s)\n'),
        ('            out["holder"] = _sbi_fold(nm)\n        m = _SBI_PERIOD.search(text)\n',
         '            out["holder"] = _sbi_fold(nm)\n'
         '        if not out["holder"]:                     # S622: no label -- the name sits left of \'State Bank of India\' on its line\n'
         '            for ln in head.splitlines():\n'
         '                if "STATE BANK OF INDIA" in ln.upper():\n'
         '                    nm = re.split(r"\\s{3,}", ln.strip())[0]\n'
         '                    if nm and "STATE BANK" not in nm.upper():\n'
         '                        out["holder"] = _sbi_fold(nm)\n'
         '                        break\n'
         '        m = _SBI_PERIOD.search(text)\n'),
    ],
    "html": [
        ("+esc(x.why||\"not placed\")+'</span>';\n    return '<div>'+esc(x.name)+' — '+p+'</div>'}",
         "+esc(x.why||\"not placed\")+'</span>'+(/^locked/.test(x.why||\"\")?' <button class=\"ghost\" onclick=\"goPw()\">Go to its password box</button>':'');\n"
         "    return '<div>'+esc(x.name)+' — '+p+'</div>'}"),
        ('function upload(){',
         '/* S622: a locked file added by hand -- one tap to the passwords card */\n'
         'function goPw(){var d=$("d_pw"); if(!d)return; d.open=true; d.scrollIntoView({behavior:"smooth",block:"start"})}\n'
         'function upload(){'),
    ],
}


def main():
    which, live, out = sys.argv[1], sys.argv[2], sys.argv[3]
    kit = sys.argv[4] if len(sys.argv) > 4 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS[which], 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: %s edit %d's anchor occurs %d times (expected 1)" % (which, i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %s: %d edits applied · rebuilt %s" % (which, len(EDITS[which]), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
