#!/usr/bin/env python3
"""S304_COUNT_PROOF -- step 7 of the stock check becomes a real proof, and stops reading "done" from the
counting close of 06-Sep.

stock_app.py (anchored edits over S301 5cc1328d)
  1. _proof_state before _hub_data: for each item with voucher lines ENTERED in Marg, drift = Marg minus our
     computed figure (same basis), on the last export day with both feeds before the first voucher was
     entered and the first after the last; proven when every item's drift moved by exactly its vouchers
     and nothing is left to make or enter. Reads only.
  2. the hub's step 7 takes _proof_state (it read the counting close -- wrong since S297).
stock_hub.html is shipped whole by the installer (over S301 a3bfab19): step 7 text and the lines that differ.

    python3 -B patch_count_proof_s304.py --app stock_app.py [--app-from M] [--dry-run]
"""
from __future__ import print_function
import argparse
import hashlib
import io
import shutil
import sys

PROOF_BLOCK = '# ---------------------------------------------------------------------------\n# S304 THE PROOF -- step 7 of the stock check: "the next Marg stock export after the vouchers must\n# read shelf plus movement". Movement is not ours to guess, so the test is the one the server can\n# make exactly: for each item, DRIFT = Marg\'s figure minus our computed figure (same basis), taken\n# on the last as-on day with both feeds BEFORE the first voucher was entered (R) and on the first\n# as-on day with both feeds AFTER the last one (L). Sales, purchases and returns move both figures\n# alike, so the drift moves only when Marg was changed without a document -- by a voucher. The item\n# is proven when drift(L) - drift(R) equals what its entered voucher lines moved. Nothing here writes;\n# the count\'s sealed figures are never touched. (Step 7 used to read "done" from the COUNTING close\n# of 06-Sep, which is a different thing -- corrected here.)\n# ---------------------------------------------------------------------------\ndef _proof_day_key(as_on):\n    s = str(as_on or "")\n    return s[6:10] + s[3:5] + s[0:2] if len(s) == 10 else ""\n\n\ndef _proof_pur_to(source):\n    """yyyymmdd the computed feed\'s purchases reach, from its \'pur_to=\' -- or \'\'."""\n    m = _re221.search(r"pur_to\\s*=\\s*(\\d{4}-\\d{2}-\\d{2}|\\d{2}-\\d{2}-\\d{4})", source or "")\n    if not m:\n        return ""\n    s = m.group(1)\n    return s.replace("-", "") if s[4] == "-" else s[6:10] + s[3:5] + s[0:2]\n\n\ndef _proof_basis(source):\n    m = _re221.search(r"base\\s*=\\s*(\\S+)", source or "")\n    return m.group(1) if m else ""\n\n\ndef _proof_state(con, d):\n    """{state, text, as_before, as_after, items, agree, differ, pending_lines, moved_without, rows}."""\n    _voucher_ensure(con)\n    root = d["count_id"]\n    ent = {}\n    for r in con.execute("SELECT round_no, kind, batch_no, marg_voucher_no, at FROM stock_voucher_entered WHERE count_id=? ORDER BY id", (root,)):\n        k = (r[0], r[1], r[2])\n        if (r[3] or "").strip():\n            ent[k] = r[4]\n        else:\n            ent.pop(k, None)\n    lines = con.execute("SELECT round_no, kind, batch_no, item, change FROM stock_voucher_line WHERE count_id=?", (root,)).fetchall()\n    need, waiting = {}, 0\n    for rno, kind, bno, item, ch in lines:\n        if (rno, kind, bno) in ent:\n            need[item] = need.get(item, 0) + int(ch)\n        else:\n            waiting += 1\n    vm_pending = len(_voucher_pending(con, d))\n    base = dict(items=len(need), agree=0, differ=0, pending_lines=waiting + vm_pending, moved_without=0, rows=[],\n                as_before="", as_after="")\n    if not ent:\n        return dict(base, state="wait", text="Waits for the vouchers: once Amir enters them in Marg, the next Marg stock export is checked item by item.")\n    first_at, last_at = min(ent.values())[:10], max(ent.values())[:19]\n    feeds = _feed_latest(con)\n    days = sorted({k[0] for k in feeds}, key=_proof_day_key)\n    # a day counts only when our computed figure carries that day\'s purchases (pur_to >= the day) --\n    # otherwise a purchase received that day moves Marg and not us, and looks like a voucher that went wrong\n    both = [x for x in days if (x, "marg") in feeds and (x, "expected") in feeds\n            and _proof_pur_to(feeds[(x, "expected")]["source"]) >= _proof_day_key(x)]\n    fk = first_at.replace("-", "")\n    before = [x for x in both if _proof_day_key(x) < fk]\n    after = [x for x in both if _proof_day_key(x) >= last_at[:10].replace("-", "") and feeds[(x, "marg")]["received_at"][:19] > last_at]\n    if not before:\n        return dict(base, state="now", text="Vouchers entered, but no Marg export with our own figures exists from before them to compare against.")\n    R = before[-1]\n    if not after:\n        return dict(base, as_before=R, state="now",\n                    text="Vouchers entered. Waiting for the next Marg stock export after the last one (entered %s IST), with that day\'s purchases in." % _r_stamp(last_at))\n    L = after[0]\n    if _proof_basis(feeds[(R, "expected")]["source"]) != _proof_basis(feeds[(L, "expected")]["source"]):\n        return dict(base, as_before=R, as_after=L, state="now",\n                    text="Marg\'s export of %s arrived, but our own figures were re-based between %s and %s; waiting for an export on the same basis." % (L, R, L))\n    def drift(x):\n        m, e = feeds[(x, "marg")]["items"], feeds[(x, "expected")]["items"]\n        return {i: m[i] - e[i] for i in m if i in e}\n    dR, dL = drift(R), drift(L)\n    rows, agree, differ = [], 0, 0\n    for item in sorted(need):\n        if item not in dR or item not in dL:\n            rows.append(dict(item=item, need=need[item], moved=None, ok=False, why="not in both exports"))\n            differ += 1\n            continue\n        moved = dL[item] - dR[item]\n        ok = moved == need[item]\n        agree += ok\n        differ += (not ok)\n        rows.append(dict(item=item, need=need[item], moved=moved, ok=ok, why=("" if ok else ("Marg moved %+d, the vouchers say %+d" % (moved, need[item])))))\n    moved_without = sum(1 for i in set(dR) & set(dL) if i not in need and dL[i] != dR[i])\n    rows.sort(key=lambda r: (r["ok"], r["item"]))\n    proven = differ == 0 and not base["pending_lines"]\n    if proven:\n        text = "PROVEN -- in Marg\'s export of %s every one of the %d vouchered items moved by exactly its voucher. Count #%d is proven: Marg agrees with the shelf." % (L, agree, root)\n    elif differ:\n        text = "Marg\'s export of %s: %d of %d vouchered items moved by exactly their voucher; %d did not -- listed below for Amir to look at in Marg." % (L, agree, len(need), differ)\n    else:\n        text = "Marg\'s export of %s: all %d entered items agree. Still to go: %d voucher line%s not yet entered or made." % (L, agree, base["pending_lines"], "" if base["pending_lines"] == 1 else "s")\n    return dict(base, state=("done" if proven else "now"), text=text, as_before=R, as_after=L, agree=agree, differ=differ,\n                moved_without=moved_without, rows=rows[:40])\n'

APP_EDITS = [
    ('def _hub_data(con, cid):\n', PROOF_BLOCK + '\n\ndef _hub_data(con, cid):\n'),
    ('                proof=dict(state=("done" if d.get("closed") else "wait")),\n',
     '                proof=_proof_state(con, d),                        # S304: the vouchers and Marg\'s next export, not the counting close\n'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def patch_one(path, edits, from_md5, marker, dry):
    raw = io.open(path, "rb").read()
    cur = md5(raw)
    text = raw.decode("utf-8")
    if marker in text:
        print("ALREADY PATCHED: %s is %s" % (path, cur))
        return cur
    if from_md5 and cur != from_md5.lower():
        sys.exit("REFUSING: %s is %s, expected %s" % (path, cur, from_md5))
    for old, new in edits:
        if text.count(old) != 1:
            sys.exit("REFUSING: anchor not found exactly once in %s: %r" % (path, old[:80]))
        text = text.replace(old, new)
    new = text.encode("utf-8")
    if dry:
        print("would write %s : %s -> %s" % (path, cur, md5(new)))
        return md5(new)
    shutil.copy2(path, "%s.bak_S304_%s" % (path, cur[:8]))
    with io.open(path, "wb") as fh:
        fh.write(new)
    back = md5(io.open(path, "rb").read())
    print("patched %s : %s -> %s" % (path, cur, back))
    if back != md5(new):
        sys.exit(4)
    return back


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--app-from", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    patch_one(a.app, APP_EDITS, a.app_from, "def _proof_state(con, d):", a.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
