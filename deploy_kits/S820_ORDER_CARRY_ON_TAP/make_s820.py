#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s820.py ROOT OUT -- kit S820_ORDER_CARRY_ON_TAP (13-Nov-2026, Sanjeevni session 451): build the three changed files FROM THE LIVE BYTES.

The owner, 18:13 IST 13-Nov: today's supplier WhatsApp orders also carried the old undelivered lines, with nobody's confirmation.
His "Go", 18:15 IST: an undelivered medicine no longer rides on the dealer's next order by itself (S619's carry, his 22-Oct ruling,
REVISED) -- it waits in the red "Purane order" box (S778) and goes to the dealer only when the staff tap "Dobara order karo";
"Ab nahi milta" as before.

  ROOT/finance/order_sheet.py   53abf461 -> a new setting order.carry_on_card (default 0 = the box only; 1 = S619 as it was);
                                            entries() puts the open carries on a card only when it is 1. The screen, the WhatsApp
                                            text and the printed sheet all read entries(), so all three change together.
  ROOT/finance/order_s778.py    819f60ff -> red_lines(): with the setting at 0 an undelivered line is in the box AT ONCE (it is
                                            known not to have come), not only after three working days as a late order is.
  ROOT/finance/porders_s454.py  21bf0abc -> the owner's settings card accepts 0 / 1 for the new setting (his to change on the screen).
  ROOT/finance/order_track.py   6f4746c5 -> the words follow the setting (the cold review's must-fix): a short line on the order list,
                                            Darpan's line and the owner's Needs-you line no longer say "back on the next order by itself".
  ROOT/finance/order_track_page.py 4e6bd715 -> the order list's short section says where the line waits (not "nothing to do").

Every patch is an exact anchor that occurs once; anything else stops the build."""
import hashlib, os, sys

FROM = {"finance/order_sheet.py":  "53abf46175d3f22eb834be246e2233f6",
        "finance/order_s778.py":   "819f60ff71a0dfae73e1c36689082037",
        "finance/porders_s454.py": "21bf0abc4ab46aeeca90d644ac8c1598",
        "finance/order_track.py":  "6f4746c570323942bffb0d5eea4b3cba",
        "finance/order_track_page.py": "4e6bd715a27ecf64833107abf5c4fa76"}

P = {"finance/order_sheet.py": [
        ('    "order.track_since": ("2026-10-12", "S619: the order list, the late rule and the carry count the orders made on or after this day"),\n}\n',
         '    "order.track_since": ("2026-10-12", "S619: the order list, the late rule and the carry count the orders made on or after this day"),\n'
         '    "order.carry_on_card": ("0", "S820 (the owner, 13-Nov): 0 = a medicine that did not come waits in the red Purane order box and goes to the '
         'dealer only on Dobara order karo; 1 = it rides on the dealer\'s next order by itself (S619, as before)"),\n}\n'),
        ('    try:                                                      # S619 (3.4): a medicine that did not come rides on its dealer\'s NEXT card\n'
         '        for cr in _ot().open_carries(con):\n',
         '    try:                                                      # S619 (3.4): a medicine that did not come rides on its dealer\'s NEXT card\n'
         '        for cr in (_ot().open_carries(con) if setting(con, "order.carry_on_card") == "1" else []):   # S820: only when the owner says 1; '
         'else it waits in the Purane order box for Dobara order karo\n'),
     ],
     "finance/order_s778.py": [
        ('        age = workdays(day, t)\n        if age < OLD_AFTER:\n            continue\n',
         '        age = workdays(day, t)\n'
         '        if age < OLD_AFTER and not (c["kind"] == "carry" and carry_box):\n'
         '            continue                                           # S820: an undelivered line is in the box at once (it did not come)\n'),
        ('    cand = []\n    for c in OT.open_carries(con):\n',
         '    cand = []\n'
         '    carry_box = OS.setting(con, "order.carry_on_card") != "1"     # S820: undelivered lines wait here, not on the next card\n'
         '    for c in OT.open_carries(con):\n'),
     ],
     "finance/order_track.py": [
        ('    if c:\n        return "back on the next order by itself" if en else "agle order mein khud jud jayega"\n',
         '    if c:\n'
         '        if setting(con, "order.carry_on_card") != "1":            # S820: it waits in the Purane order box for a tap\n'
         '            return "waiting in the Old orders box -- goes only on Order again" if en else "Purane order box mein -- Dobara order karo dabane par hi jayegi"\n'
         '        return "back on the next order by itself" if en else "agle order mein khud jud jayega"\n'),
        ('        lines.append("%s ke order: %d dawa nahi aayi \u2014 agle order mein khud jud gayi." % (D, nshort))\n',
         '        lines.append(("%s ke order: %d dawa nahi aayi \u2014 agle order mein khud jud gayi." if setting(con, "order.carry_on_card") == "1" else\n'
         '                      "%s ke order: %d dawa nahi aayi \u2014 Purane order box mein, reception Dobara order karo dabaye tabhi jayegi.") % (D, nshort))   # S820\n'),
        ('    return dict(cls="warn", target="porders", text="Orders: %d late, %d medicine%s came short (back on the next order) \u2014 the order list"\n'
         '                % (n, m, "" if m == 1 else "s"))\n',
         '    w = "back on the next order" if setting(con, "order.carry_on_card") == "1" else "in the Old orders box, sent only on Order again"   # S820\n'
         '    return dict(cls="warn", target="porders", text="Orders: %d late, %d medicine%s came short (%s) \u2014 the order list"\n'
         '                % (n, m, "" if m == 1 else "s", w))\n'),
     ],
     "finance/order_track_page.py": [
        ('    "s708_sh_s": ("Jo dawa nahi aayi, woh agle order mein apne aap jaati hai. Aapko kuch nahi karna.",\n',
         '    "s820_sh_s": ("Jo dawa nahi aayi, woh order screen ke laal Purane order box mein hai \u2014 reception Dobara order karo dabaye tabhi dealer ko jaati hai.",\n'
         '                  "What did not come waits in the red Old orders box on reception\'s order screen \u2014 it goes to the dealer only when they tap Order again."),\n'
         '    "s708_sh_s": ("Jo dawa nahi aayi, woh agle order mein apne aap jaati hai. Aapko kuch nahi karna.",\n'),
        ('_L(en, "s708_sh_s")', '_L(en, "s708_sh_s" if _os().setting(con, "order.carry_on_card") == "1" else "s820_sh_s")'),
     ],
     "finance/porders_s454.py": [
        ('    if key == "porders.simple" or key == "order.sheet_print_old":\n',
         '    if key in ("porders.simple", "order.sheet_print_old", "order.carry_on_card"):   # S820: + the carry switch\n'),
     ]}


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: make_s820.py ROOT OUT")
    root, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    for rel, pats in P.items():
        with open(os.path.join(root, rel), "rb") as f:
            raw = f.read()
        if md5(raw) != FROM[rel]:
            sys.exit("STOP: %s is %s, expected %s -- it changed after this kit was built" % (rel, md5(raw)[:8], FROM[rel][:8]))
        s = raw.decode("utf-8")
        for a, b in pats:
            n = s.count(a)
            if n != 1:
                sys.exit("STOP: an anchor of %s occurs %d times (must be once): %r" % (rel, n, a[:70]))
            s = s.replace(a, b)
        dst = os.path.join(out, os.path.basename(rel))
        with open(dst, "wb") as f:
            f.write(s.encode("utf-8"))
        print("built %s %s -> %s" % (rel, FROM[rel][:8], md5(s.encode("utf-8"))[:8]))


if __name__ == "__main__":
    main()
