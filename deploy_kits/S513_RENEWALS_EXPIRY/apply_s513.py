#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s513.py -- S513_RENEWALS_EXPIRY (D689, closes F-775; session 304, 10-Oct-2026): exact edits in finance_app.py.

Built from the real file (/root/finance/finance_app.py at bff362c3, the 10-Oct bundle's bytes), read whole first
(13,538 lines) -- the drift on this file was 4.
THE OWNER'S RULING: a renewal comes up 45 days before its REAL expiry and is red only after it. Until now a row's
dateISO -- an early-alert day -- was read as the deadline, so the arms licence (alert 27-Sep, expiry 26-Dec) has
shown OVERDUE since 27-Sep. An alert day and a deadline are two fields:
  1  the window is 45 days (was 30);
  2  the push keeps an expiryISO beside dateISO; a row without a valid one (an older script) keeps its alert day as
     its expiry, exactly as before;
  3  the health row counts days to the expiry; one bad row is skipped instead of failing the whole row;
  4  its words: 'N expiring inside 45 days · nearest: X in N days (expires D)', 'OVERDUE: X (N days past expiry, D)',
     'nothing expires inside 45 days'; a stale feed still names a renewal inside the window;
  5  the selftest's renewals block follows (45 days; the arms-licence case held; the asset database kept out of it,
     so a real warranty can never colour the selftest).
Every anchor must be found exactly once.  usage: apply_s513.py <finance_app.py>
"""
import hashlib
import sys

FROM = "bff362c38ec61526ea0047fd136df826"

EDITS = [
    # 1 -- the window
    ('''RENEWALS_WINDOW_DAYS = 30       # the tile line's window (owner spec, Task #8)
''',
     '''RENEWALS_WINDOW_DAYS = 45       # S513 (D689): from 45 days before the REAL expiry (was 30, Task #8)
'''),
    # 2 -- the push keeps expiryISO
    ('''        items.append({"vendor": vendor, "dateISO": diso,
                      "note": str(it.get("note") or "").strip()[:200]})
''',
     '''        # S513 (D689/F-775): the REAL expiry rides beside the alert day. A row without a valid one (a script
        # older than S513) keeps its alert day as its expiry -- exactly what it meant before.
        eiso = str(it.get("expiryISO") or "").strip()[:10]
        try:
            dt.date.fromisoformat(eiso)
        except (ValueError, TypeError):
            eiso = diso
        items.append({"vendor": vendor, "dateISO": diso, "expiryISO": eiso,
                      "note": str(it.get("note") or "").strip()[:200]})
'''),
    # 3 -- the comment over section 6
    ('''    # renewal inside 7 days is warn (it reaches the portal tile line); inside
    # 30 days is info; a missing feed is info (the surface may not be wired
''',
     '''    # renewal inside 7 days is warn (it reaches the portal tile line); inside
    # 45 days is info; a missing feed is info (the surface may not be wired
    # [S513, D689: every day is counted to the row's REAL expiry -- expiryISO --
    # never to its early-alert day; red only after the expiry; was 30 days]
'''),
    # 4 -- days counted to the expiry; a bad row is skipped, never the whole row
    ('''            for it in st["items"]:
                try:
                    dd = (dt.date.fromisoformat(it["dateISO"]) - today).days
                except (ValueError, KeyError, TypeError):
                    continue
                decorated.append((dd, it["vendor"], it["dateISO"]))
''',
     '''            for it in st["items"]:
                try:
                    # S513: a row stored before S513 has no expiryISO -- its dateISO stands in, as before
                    eiso = str(it.get("expiryISO") or it["dateISO"])[:10]
                    dd = (dt.date.fromisoformat(eiso) - today).days
                    decorated.append((dd, str(it["vendor"]), eiso))
                except (ValueError, KeyError, TypeError, AttributeError):
                    continue
'''),
    # 5 -- the overdue words
    ('''                    "OVERDUE: %s (%d days past, %s)%s"
''',
     '''                    "OVERDUE: %s (%d days past expiry, %s)%s"
'''),
    ('''                    "Renew it, then advance the date in the RENEWALS list — "
                    "that is what silences this.")
''',
     '''                    "Renew it, then advance its date in the RENEWALS list and "
                    "write the new expiry in its note — that is what silences this.")
'''),
    # 6 -- a stale feed still names what is inside the window
    ('''                    "feed stale — last push %s" % pushed,
''',
     '''                    "feed stale — last push %s%s" % (pushed, (
                        " · nearest: %s in %d days (expires %s)" % (soon[0][1], soon[0][0], soon[0][2]))
                        if soon else ""),
'''),
    # 7 -- the inside-the-window and quiet words
    ('''                    "%d inside %d days · nearest: %s in %d days (%s)"
''',
     '''                    "%d expiring inside %d days · nearest: %s in %d days (expires %s)"
'''),
    ('''                    "nothing inside %d days · pushed %s"
''',
     '''                    "nothing expires inside %d days · pushed %s"
'''),
    # 8 -- selftest: the asset database kept out of the renewals block
    ('''    _rn_dir = tempfile.mkdtemp(prefix="smoke_renewals_")
''',
     '''    _rn_dir = tempfile.mkdtemp(prefix="smoke_renewals_")
    _rn_assets_saved = os.environ.get("ASSETS_DB")                # S513: no real warranty colours this block
    os.environ["ASSETS_DB"] = os.path.join(_rn_dir, "no_assets.db")
'''),
    ('''    globals()["RENEWALS_TOKEN"] = _rn_tok_saved
    globals()["RENEWALS_STATE"] = _rn_state_saved
''',
     '''    globals()["RENEWALS_TOKEN"] = _rn_tok_saved
    globals()["RENEWALS_STATE"] = _rn_state_saved
    if _rn_assets_saved is None:                                  # S513
        os.environ.pop("ASSETS_DB", None)
    else:
        os.environ["ASSETS_DB"] = _rn_assets_saved
'''),
    # 9 -- selftest: 45 days
    ('''    _rn_far = (dt.date.today() + dt.timedelta(days=40)).isoformat()
''',
     '''    _rn_far = (dt.date.today() + dt.timedelta(days=50)).isoformat()      # S513: beyond 45
'''),
    ('''                       "window_days": 30, "items": items}, _rf)
''',
     '''                       "window_days": 45, "items": items}, _rf)
'''),
    ('''    _cc = _rn_card()                          # written by the push above (40d)
    check("renewals: beyond 30 days the card is quiet ok",
          _cc is not None and _cc["state"] == "ok")
''',
     '''    _cc = _rn_card()                          # written by the push above (50d)
    check("renewals: beyond 45 days the card is quiet ok",
          _cc is not None and _cc["state"] == "ok")
    # S513 (D689/F-775): the push keeps the real expiry; a row without a valid one keeps its alert day
    _rn_d = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()
    r = c.post("/finance/api/renewals-push",
               headers={"X-Finance-Renewals": "smoke-renew"},
               json={"items": [
                   {"vendor": "Arms licence", "dateISO": _rn_d(-13), "expiryISO": _rn_d(77)},
                   {"vendor": "Older script row", "dateISO": _rn_d(60)},
                   {"vendor": "Bad expiry", "dateISO": _rn_d(61), "expiryISO": "31-12-2026"},
               ]})
    _rn_st = _renewals_read() or {}
    check("S513 renewals: the push keeps expiryISO; a row without a valid one keeps its alert day as its expiry",
          r.status_code == 200 and r.get_json().get("stored") == 3
          and [x.get("expiryISO") for x in _rn_st.get("items", [])] == [_rn_d(77), _rn_d(60), _rn_d(61)])
    _cc = _rn_card()
    check("S513 renewals: an alert day gone by is NOT overdue while the real expiry is 77 days off (F-775)",
          _cc is not None and _cc["state"] == "ok")
'''),
    ('''    check("renewals: inside 30 days -> info naming the nearest",
''',
     '''    check("renewals: inside 45 days -> info naming the nearest",
'''),
    ('''          and "2 inside 30 days" in _cc["detail"]
''',
     '''          and "2 expiring inside 45 days" in _cc["detail"]
'''),
    # 10 -- selftest: counted to the expiry, red only after it
    ('''    check("renewals: an overdue renewal is BAD and says so",
          _cc is not None and _cc["state"] == "bad"
          and "OVERDUE" in _cc["detail"] and "4 days past" in _cc["detail"])
''',
     '''    check("renewals: an overdue renewal is BAD and says so",
          _cc is not None and _cc["state"] == "bad"
          and "OVERDUE" in _cc["detail"] and "4 days past" in _cc["detail"])
    _rn_write([{"vendor": "Arms licence", "dateISO": (_rn_today - dt.timedelta(days=50)).isoformat(),
                "expiryISO": (_rn_today + dt.timedelta(days=40)).isoformat()}])
    _cc = _rn_card()
    check("S513 renewals: 40 days before the real expiry -> info, counted to the expiry",
          _cc is not None and _cc["state"] == "info" and "Arms licence in 40 days" in _cc["detail"])
    _rn_write([{"vendor": "Arms licence", "dateISO": (_rn_today - dt.timedelta(days=90)).isoformat(),
                "expiryISO": _rn_today.isoformat()}])
    _cc = _rn_card()
    check("S513 renewals: the expiry day itself is warn, not red",
          _cc is not None and _cc["state"] == "warn")
    _rn_write([{"vendor": "Arms licence", "dateISO": (_rn_today - dt.timedelta(days=91)).isoformat(),
                "expiryISO": (_rn_today - dt.timedelta(days=1)).isoformat()}])
    _cc = _rn_card()
    check("S513 renewals: red only AFTER the real expiry",
          _cc is not None and _cc["state"] == "bad" and "1 days past expiry" in _cc["detail"])
'''),
]


def apply(src):
    for n, (old, new) in enumerate(EDITS, 1):
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor %d was found %d time(s), expected 1 - nothing written" % (n, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s513.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d edits; %+d bytes)" % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
