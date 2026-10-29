#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s678.py -- kit S678_AMIR_PAIR_FROM_DOOR (29-Oct-2026, Sanjeevni session 367).

    python3 -B make_s678.py <root> <outdir>        reads <root>/finance/amir_day.py, writes <outdir>/finance/amir_day.py

WHY.  On 29-Oct Amir's two purchase exports (text, 09:07 and 09:08; the bill-wise again as Excel, 09:25) were VERIFIED at the server's
own door within seconds (mi_file).  His step 4 reads ONLY purchase_export, which is filled by manojz's ten-minute pull and push -- and
manojz did not pull from 00:22 to 09:43 IST.  So after six minutes his screen said "nahi aayi -- Dobara banaiye ... file band kijiye",
which was false: the server had both files.

WHAT.  One file, amir_day.py, six anchored edits in four places (each anchor must occur exactly once, else the builder refuses):
  1. KIT names this kit.
  2. _door_receipt(cx, kind, day, first): the server's own VERIFIED door receipt (mi_file, type PURCHASE_<kind>) stamped by Marg on
     `day` whose printed period covers the 1st..day -- the newest -- or None.
  3. _export_state (TODAY only -- a past day's reading is untouched; its exports were often superseded since): where the pair's report has no purchase_export row of the day (or only one that does not cover the 1st..day), a
     covering door receipt -- non-empty dates, not older than his newest step-2 tap, and (beside a non-covering row) newer than that row --
     makes the report "wait" with door = its hh:mm -- never "bad", never "dobara banaiye".  It does NOT become a
     tick: the tick and the bill list still need purchase_export's rows (the bills he taps come from them), so nothing is shown done
     that is not loaded.  When the rows arrive the screen turns green by itself (it already re-reads every EXPORT_POLL_SEC).
  4. _step4 (a door wait never hides a bad or not-yet report: then the old head and buttons rule): a door wait says so -- "Server par hh:mm baje aa gayi -- padhi ja rahi hai" -- and, when every wait is a door wait, the
     head says the report has reached the server and he need not export again, with no minutes counting down.
Nothing else changes: the re-export band (_export_fact already reads mi_file), the owner's 48-hour line, the tick, the bills.
"""
import hashlib
import os
import sys

REL = "finance/amir_day.py"
FROM = "3b7dae35699548b4db9c2dac498cda6a"

EDITS = [
    # 1 -- the kit line
    ('KIT = "S638_EXPIRY_WATCH"                                 # the kit that last placed this file (S533 built the page; S584 named it; '
     'S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner\'s 48-hour line; S638: the expiry '
     'watch\'s rows)',
     'KIT = "S678_AMIR_PAIR_FROM_DOOR"                          # the kit that last placed this file (S533 built the page; S584 named it; '
     'S587: the export step last, the re-export line; S603: the export fact, the covering export, the owner\'s 48-hour line; S638: the expiry '
     'watch\'s rows; S678: a report the server\'s own door holds is never "nahi aayi")'),

    # 2 -- the door receipt, just above _export_state
    ('\ndef _export_state(cx, day, wait_since=None):\n',
     '\ndef _door_receipt(cx, kind, day, first):\n'
     '    """S678: the server\'s OWN receipt of a pair report -- the newest VERIFIED mi_file of type PURCHASE_<kind> that Marg stamped on `day`\n'
     '    (its YYYYMMDD-HHMMSS name) and whose printed period covers first..day -> {stamp, at (hh:mm)}; None when there is none.  The door\n'
     '    takes the medical PC\'s push within seconds; purchase_export waits for manojz\'s pull (29-Oct: manojz asleep 00:22-09:43)."""\n'
     '    try:\n'
     '        if not _table_exists(cx, "mi_file"):\n'
     '            return None\n'
     '        r = cx.execute("SELECT stamp, received_at FROM mi_file WHERE verdict=\'VERIFIED\' AND type=? AND substr(stamp,1,8)=? "\n'
     '                       "AND date_from<>\'\' AND date_to<>\'\' "\n'
     '                       "AND substr(date_from,1,10)<=? AND substr(date_to,1,10)>=? ORDER BY stamp DESC LIMIT 1",\n'
     '                       ("PURCHASE_" + kind, str(day).replace("-", ""), first, day)).fetchone()\n'
     '    except Exception:                                                  # noqa: BLE001\n'
     '        return None\n'
     '    if not r:\n'
     '        return None\n'
     '    try:                                                               # a bill entered after this file: the re-export band rules, not the door\n'
     '        t = cx.execute("SELECT MAX(done_at) FROM amir_step_log WHERE day=? AND step=2", (day,)).fetchone() \\\n'
     '            if _table_exists(cx, "amir_step_log") else None\n'
     '    except Exception:                                                  # noqa: BLE001\n'
     '        t = None\n'
     '    t2 = _norm_ts(t[0]) if (t and t[0]) else None\n'
     '    if t2 and (_norm_ts(r[1]) or "") < t2:                             # the server\'s receipt clock against the server\'s tap clock\n'
     '        return None\n'
     '    return {"stamp": r[0], "at": _hhmm(r[0]) or _hhmm(r[1])}\n'
     '\n'
     '\ndef _export_state(cx, day, wait_since=None):\n'),

    # 3a -- no purchase_export row: a covering door receipt is a wait, not a miss
    ('        if row is None:\n'
     '            since = None\n'
     '            if wait_since is None:\n',
     '        door = _door_receipt(cx, kind, day, first) if str(day) >= _today() else None   # S678: today only -- a past day keeps its own reading\n'
     '        if row is None and door is not None:\n'
     '            out.append({"kind": kind, "label": label, "have": False, "state": "wait", "waited": waited, "door": door["at"],\n'
     '                        "reason": "server par %s baje aa gayi -- padhi ja rahi hai, dobara nahi nikaalni" % door["at"],\n'
     '                        "reason_en": "at the server since %s (VERIFIED at the door) -- its rows wait for the manojz leg" % door["at"]})\n'
     '            continue\n'
     '        if row is None:\n'
     '            since = None\n'
     '            if wait_since is None:\n'),

    # 3b -- a purchase_export row that does not cover, while the door holds one that does: a wait
    ('        if not (ok_from and ok_to):\n'
     '            arrived =',
     '        if not (ok_from and ok_to) and door is not None and (_norm_ts(door["stamp"]) or "") > (_norm_ts(d.get("export_stamp") or d.get("received_at")) or ""):   # S678: a NEWER covering one is at the door\n'
     '            out.append({"kind": kind, "label": label, "have": False, "state": "wait", "waited": waited, "door": door["at"],\n'
     '                        "reason": "server par %s baje aa gayi -- padhi ja rahi hai, dobara nahi nikaalni" % door["at"],\n'
     '                        "reason_en": "at the server since %s (VERIFIED at the door) -- its rows wait for the manojz leg" % door["at"]})\n'
     '            continue\n'
     '        if not (ok_from and ok_to):\n'
     '            arrived ='),

    # 4a -- the line of a door wait
    ('        elif st == "wait":\n'
     '            out.append("<div class=line><span class=\'big warn\'>%s &hellip;</span><br>"\n'
     '                       "<span class=sub>File abhi aa rahi hai.</span></div>" % _esc(e["label"]))\n',
     '        elif st == "wait" and e.get("door"):                           # S678\n'
     '            out.append("<div class=line><span class=\'big warn\'>%s &hellip;</span><br>"\n'
     '                       "<span class=sub>Server par %s baje aa gayi &mdash; padhi ja rahi hai.</span></div>"\n'
     '                       % (_esc(e["label"]), _esc(e["door"])))\n'
     '        elif st == "wait":\n'
     '            out.append("<div class=line><span class=\'big warn\'>%s &hellip;</span><br>"\n'
     '                       "<span class=sub>File abhi aa rahi hai.</span></div>" % _esc(e["label"]))\n'),

    # 4b -- the head when every wait is a door wait
    ('    if waiting:\n'
     '        head = ("<div class=card><h2 class=warn>Report aa rahi hai &mdash; %d min</h2>"',
     '    door_waits = [e for e in S.exports if e.get("state") == "wait"]                         # S678: a door wait never hides a\n'
     '    if waiting and (bad or notyet) and all(e.get("door") for e in door_waits):                 # wrong or missing report -- the\n'
     '        waiting = False                                                                    # bad / not-yet head and buttons rule\n'
     '    door_only = waiting and all(e.get("door") for e in door_waits)\n'
     '    if door_only:\n'
     '        head = ("<div class=card><h2 class=warn>Report server par aa gayi hai</h2>"\n'
     '                "<p class=big>Padhi ja rahi hai &mdash; bill ki list thodi der mein aayegi.</p>"\n'
     '                "<p>Aapko dobara nahi nikaalni. Aage ka kaam kijiye -- yeh screen khud dekhti rahegi.</p></div>")\n'
     '    elif waiting:\n'
     '        head = ("<div class=card><h2 class=warn>Report aa rahi hai &mdash; %d min</h2>"'),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def build(src_bytes):
    if md5(src_bytes) != FROM:
        raise SystemExit("REFUSED: %s is %s, not the FROM pin %s" % (REL, md5(src_bytes)[:8], FROM[:8]))
    s = src_bytes.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %d occurs %d times (must be exactly once)" % (i, n))
        s = s.replace(old, new, 1)
    return s.encode("utf-8")


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    root, outdir = sys.argv[1], sys.argv[2]
    with open(os.path.join(root, REL), "rb") as fh:
        out = build(fh.read())
    dst = os.path.join(outdir, REL)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        fh.write(out)
    print("built %s %s -> %s (%d edits)" % (REL, FROM[:8], md5(out)[:8], len(EDITS)))


if __name__ == "__main__":
    main()
