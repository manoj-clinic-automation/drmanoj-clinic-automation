"""make_s849.py <code dir holding the FROM files> <out dir> -- kit S849_SCAN_NOT_IN_MARG: five files patched on exact anchors (each once), the
new scan_ask.py beside them. Every FROM file is checked against its pin first."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"sanjeevni_approvals.py": "7d75f9d51cbc14d4b3a2dd4d1668aef5", "amir_day.py": "c016278b8a4f9fb2aa42dbfe60008d26",
        "purchase_app.py": "d1999929730c394da5d00782c66e858e", "provisional_s781.py": "4d9cef5543b4d983561a5518d8fc0feb",
        "scan_register.py": "eb48202f1c6edbc2aa60a4ed211dd948"}
P = {}
P["purchase_app.py"] = [(
    "        if sid in linked:\n            continue\n        s = st.get(sid) or {}\n        why = s.get(\"why\") or \"\"\n        chosen",
    "        if sid in linked or sid in _s849_aside:                # S849: a paper answered 'not a purchase bill' is never Amir's to enter\n"
    "            continue\n        s = st.get(sid) or {}\n        why = s.get(\"why\") or \"\"\n        chosen"), (
    "    rows = _s452_scan_rows()\n    if rows is None:\n        return dict(list=[], held=[], ok=False)\n    linked = _s446_linked(con)\n",
    "    rows = _s452_scan_rows()\n    if rows is None:\n        return dict(list=[], held=[], ok=False)\n    linked = _s446_linked(con)\n"
    "    try:                                                       # S849 (D995): the scans answered 'not a purchase bill' (scan_ask.py)\n"
    "        import scan_ask as _s849                              # noqa: PLC0415\n"
    "        _s849_aside = _s849.aside_ids(con)\n"
    "    except Exception:                                          # noqa: BLE001 -- without it, the list as before\n"
    "        _s849_aside = set()\n")]
P["provisional_s781.py"] = [(
    "    linked = {int(r[0]) for r in con.execute(\"SELECT asset_bill_id FROM purchase_scan_link\")}\n    cand = []\n",
    "    linked = {int(r[0]) for r in con.execute(\"SELECT asset_bill_id FROM purchase_scan_link\")}\n"
    "    try:                                                      # S849 (D995): a paper answered 'not a purchase bill' waits for nothing\n"
    "        import scan_ask as _s849                             # noqa: PLC0415\n"
    "        linked |= _s849.aside_ids(con)\n"
    "    except Exception:                                         # noqa: BLE001\n"
    "        pass\n    cand = []\n")]
P["amir_day.py"] = [(
    "            jv = str(f.get(\"job\") or \"\")\n            if jv.startswith(\"ask:\") and f.get(\"ans\"):         # S814: the answer button names the answer",
    "            jv = str(f.get(\"job\") or \"\")\n"
    "            if jv.startswith(\"sna:\"):                          # S849: his answer to 'scanned bill not found in Marg'\n"
    "                try:\n"
    "                    import scan_ask                            # noqa: PLC0415\n"
    "                    scan_ask.amir_tap(cx, user, jv)\n"
    "                except Exception:                              # noqa: BLE001\n"
    "                    pass\n"
    "                return _go(n)\n"
    "            if jv.startswith(\"ask:\") and f.get(\"ans\"):         # S814: the answer button names the answer")]
P["sanjeevni_approvals.py"] = [(
    "        print(\"item_ledger NOT mounted: %s\" % _e845, file=_sys845.stderr)\n    return bp",
    "        print(\"item_ledger NOT mounted: %s\" % _e845, file=_sys845.stderr)\n"
    "    try:                                                      # S849 (17-Nov-2026): scanned bills not found in Marg (scan_ask.py; D995)\n"
    "        import scan_ask                                       # noqa: PLC0415 -- beside this file\n"
    "        scan_ask.init(app, db_getter, require_fn)\n"
    "    except Exception as _e849:                                # noqa: BLE001 -- these pages keep working without it\n"
    "        import sys as _sys849                                 # noqa: PLC0415\n"
    "        print(\"scan_ask NOT mounted: %s\" % _e849, file=_sys849.stderr)\n"
    "    return bp")]
TAIL = {
"sanjeevni_approvals.py": '''


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995): one Needs-you line while a pharmacy scan is not found in Marg past the days
#  (scan_ask.needs_lines; target 'scans' -> S761's group 'Bills & papers'); its href opens /finance/sanjeevni/not-in-marg. Added BEFORE S761 groups.
#  NEEDS_YOU_WITHOUT_S849=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it. Fail-soft.
_needs_you_before_s849 = _needs_you_before_s761


def _needs_you_before_s761(con):                         # noqa: F811 -- S849: S761's grouping reads this name at call time
    r = _needs_you_before_s849(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S849") == "1":
        return r
    try:
        import scan_ask as _sa849                            # noqa: PLC0415
        add = _sa849.needs_lines(con)
        if add:
            r["lines"] = list(r.get("lines") or []) + add
            r["count"] = int(r.get("count") or 0) + len(add)
    except Exception:                                    # noqa: BLE001
        pass
    return r
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------
''',
"amir_day.py": '''


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995) -------------------------------------------------------------------------
#  A scan still on his enter list after Marg's purchases moved the owner's days past its bill becomes ONE QUESTION, first on his card: the scan,
#  the dealer's likely Marg bill with its own scan and lines, one-tap answers (scan_ask.amir_view). While asked it leaves his plain enter list
#  (step 2 and the card's count). His tap is 'sna:<scan>:<answer>:<bill>' (step(), before every other job). Fail-soft: without scan_ask, as before.
_state_before_s849 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811 -- S849
    S = _state_before_s849(cx, day, who, step, owner)
    S.s849 = []
    try:
        import scan_ask                                        # noqa: PLC0415
        ids, S.s849 = scan_ask.amir_view(cx)
        if ids:
            S.scans = [b for b in (S.scans or []) if int(b.get("id") or 0) not in ids]
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S849: the questions could not be read: %s" % str(e)[:200], file=sys.stderr)
    return S


_card_rows_before_s849 = _card_rows


def _card_rows(S):                                            # noqa: F811 -- S849: the questions first on his card
    rows = _card_rows_before_s849(S)
    q = getattr(S, "s849", None) or []
    return [("s849", h, "a scanned bill not found in Marg", True) for h in q] + rows
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------
''',
"scan_register.py": '''


# ---- S849_SCAN_NOT_IN_MARG (17-Nov-2026, Sanjeevni session 473; D995): Amir also opens the scans of his card's question ----------------------
_s738_scan_ok_before_s849 = s738_scan_ok


def s738_scan_ok(con, sid, doctor, login):                   # noqa: F811 -- S849
    if _s738_scan_ok_before_s849(con, sid, doctor, login):
        return True
    try:
        import scan_ask                                       # noqa: PLC0415
        return scan_ask.amir_may_see(con, sid)
    except Exception:                                         # noqa: BLE001
        return False
# ---- S849 end ---------------------------------------------------------------------------------------------------------------------------
'''}
os.makedirs(OUT, exist_ok=True)
for n, pin in FROM.items():
    b = open(os.path.join(SRC, n), "rb").read()
    assert hashlib.md5(b).hexdigest() == pin, "%s is not at its FROM pin" % n
    t = b.decode("utf-8")
    for a, r in P.get(n, []):
        assert t.count(a) == 1, "%s: anchor not found exactly once: %r" % (n, a[:70])
        t = t.replace(a, r, 1)
    if n in TAIL:
        t = t.rstrip("\n") + TAIL[n]
    open(os.path.join(OUT, n), "wb").write(t.encode("utf-8"))
    print(n, hashlib.md5(t.encode("utf-8")).hexdigest())
