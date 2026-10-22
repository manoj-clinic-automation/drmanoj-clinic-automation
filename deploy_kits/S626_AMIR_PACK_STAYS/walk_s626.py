#!/usr/bin/env python3
"""walk_s626.py -- kit S626_AMIR_PACK_STAYS (F-988).  python3 -B walk_s626.py <finance folder> <a COPY of finance.db> OLD|NEW

Imports amir_day from the given folder and checks Amir's month packs on made-up shelves (packs.amir_pack replaced, the three
previous months fixed), then once on the database copy (never the live file).  NEW must pass every check; OLD must fail the F-988
checks (the negative control).  Prints PASS/FAIL per check and 'WALK <mode>: <pass>/<fail>'; exit 0 when the mode's expectation holds."""
import sqlite3
import sys
import types

fin, dbcopy, mode = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, fin)
import amir_day  # noqa: E402
import packs  # noqa: E402

MONTHS = ["2026-07", "2026-08", "2026-09"]
res = []


def check(name, ok, f988):
    res.append((name, bool(ok), f988))
    print("%s  %s%s" % ("PASS" if ok else "FAIL", name, "  [F-988]" if f988 else ""))


def shelf(state):
    """state: {month: 'seen' | 'unseen'}; a month absent is not ready."""
    real = packs.amir_pack

    def fake(cx, m):
        s = state.get(m)
        return dict(month=m, ready=s is not None, seen=(dict(by="amir", at="x") if s == "seen" else None))
    packs.amir_pack = fake
    amir_day._s446_prev_months = lambda n=3: list(MONTHS)
    try:
        got = amir_day._s446_packs(None)
    finally:
        packs.amir_pack = real
    return got


def months(got):
    return [(g[0] if isinstance(g, tuple) else g) for g in got]


def card(got, neft=None):
    S = types.SimpleNamespace(stage=None, sw={}, watch=dict(sunday=False, fixes=0), scans=[], rates=[], jobs={}, packs=got, neft_ok=neft or {})
    return amir_day._card_rows(S)


# 1. the case of 22-Oct: September ready and seen -> it stays
g = shelf({"2026-09": "seen"})
check("September ready and seen stays on his page", months(g) == ["2026-09"], True)
# 2. a seen newest month shows its links and no Dekh liya button
rows = card(g) if g else []
h = "".join(r[1] for r in rows)
check("a seen month keeps both statement links", "/finance/amir/pack/2026-09/yes" in h and "/finance/amir/pack/2026-09/icici" in h, True)
check("a seen month has no Dekh liya button", ("/seen'" not in h) and bool(h), True)
# 3. an unseen month keeps the button (unchanged behaviour)
g = shelf({"2026-09": "unseen"})
h = "".join(r[1] for r in card(g))
check("an unseen month shows the Dekh liya button", "/finance/amir/pack/2026-09/seen'" in h and "Dekh liya" in h, False)
# 4. older seen month leaves once a newer one is ready
g = shelf({"2026-08": "seen", "2026-09": "seen"})
check("two seen months: only the newest stays", months(g) == ["2026-09"], True)
g = shelf({"2026-08": "seen", "2026-09": "unseen"})
check("August seen, September unseen: only September", months(g) == ["2026-09"], False)
# 5. an older UNSEEN month still shows beside the newest (unchanged)
g = shelf({"2026-08": "unseen", "2026-09": "seen"})
check("August unseen + September seen: both, oldest first", months(g) == ["2026-08", "2026-09"], True)
# 6. next month not ready yet: the last ready month stays
g = shelf({"2026-08": "seen"})
check("September not on the shelf: August (seen) stays", months(g) == ["2026-08"], True)
# 7. nothing ready: nothing shown, and the card is empty
g = shelf({})
check("nothing ready: nothing shown", g == [] and card(g) == [], False)
# 8. the pack row never gates his day (his_line stays False) and the NEFT link follows neft_ok
g = shelf({"2026-09": "seen"})
rows = card(g, {"2026-09": True})
check("the pack row is not his Marg work (never a gate)", rows and all(r[3] is False for r in rows), False)
check("the paid NEFT link shows when the month's NEFT is confirmed", rows and "/finance/amir/pack/2026-09/neft" in rows[0][1], False)
# 9. the database copy: whatever is on the shelf, the newest ready month is listed (read through the real packs.amir_pack)
cx = sqlite3.connect(dbcopy)
cx.row_factory = sqlite3.Row
import importlib  # noqa: E402
importlib.reload(amir_day)
real = [m for m in amir_day._s446_prev_months(3) if packs.amir_pack(cx, m).get("ready")]
got = amir_day._s446_packs(cx)
gm = [g[0] if isinstance(g, tuple) else g for g in got]
print("       the copy: ready months %s; listed %s" % (real, gm))
check("the copy: the newest ready month is listed", (not real) or (gm and gm[-1] == real[-1]), True)
cx.close()

p = sum(1 for _n, ok, _f in res if ok)
f = len(res) - p
f988_fail = sum(1 for _n, ok, f9 in res if f9 and not ok)
print("WALK %s: %d/%d" % (mode, p, f))
if mode == "NEW":
    sys.exit(0 if f == 0 else 1)
sys.exit(0 if f988_fail > 0 else 1)          # OLD: the control must be red on F-988
