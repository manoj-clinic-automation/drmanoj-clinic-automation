#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s454p1d.py -- kit S454_BILL_REGISTER, part 1D: the order tick runs again from the cron (a fault of part 1, found 03-Oct 16:30 IST).

Part 1 appended its block (the order sheet's cron pass, the one reminder of the day) BELOW order_rules.py's `if __name__ == "__main__":` line.
The cron runs the file as a script (`order_rules.py tick`): Python reaches that line, runs main() -> tick() -> _s454_pass(), and the name is
not defined yet -- NameError on every tick since 12:30 IST (order_rules.log). Inside the service (an import) nothing was wrong. The fix moves
the two guard lines to the end of the file, unchanged. CLAUDE.md rule 2: built from the live bytes, the anchor exactly once, FROM -> TO pinned.

    make_s454p1d.py --finance /root/finance --out DIR
"""
import argparse
import hashlib
import os

FROM = {"order_rules.py": "d29efa8e6425fa359ea28d38c0758ccc"}
GUARD = '\n\nif __name__ == "__main__":\n    sys.exit(main(sys.argv))\n'
TAIL = ('\n\nif __name__ == "__main__":                                   # S454 P1D: last in the file, so every definition above it exists when the\n'
        '    sys.exit(main(sys.argv))                                 # cron runs this file as a script (part 1 had appended below it)\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--finance", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    f = "order_rules.py"
    raw = open(os.path.join(a.finance, f), "rb").read()
    m = hashlib.md5(raw).hexdigest()
    if m != FROM[f]:
        raise SystemExit("STOP: %s is %s, not its FROM pin %s -- nothing built" % (f, m, FROM[f]))
    txt = raw.decode("utf-8")
    if txt.count(GUARD) != 1:
        raise SystemExit("STOP: the guard occurs %d times -- nothing built" % txt.count(GUARD))
    txt = txt.replace(GUARD, "\n", 1).rstrip("\n") + "\n" + TAIL
    out = txt.encode("utf-8")
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, f), "wb").write(out)
    print("built %-18s %s -> %s  (the guard moved to the end)" % (f, m[:8], hashlib.md5(out).hexdigest()))


if __name__ == "__main__":
    main()
