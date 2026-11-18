"""make_s867.py <code dir holding the FROM files> <out dir> -- kit S867_CONFIRM_WORDS: scan_register.py and purchase_app.py each get ONE tail
block (no anchor inside the old text). Every FROM file is checked against its pin first."""
import hashlib, os, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"scan_register.py": "1aec54b4a29cac99a5cfad77d0c2d00f", "purchase_app.py": "73e46df04dc6ed63c92e917ad305bf49"}
TAIL_SR = '''


# ---- S867_CONFIRM_WORDS (18-Nov-2026, Sanjeevni session 481; D1003 item 1) ------------------------------------------------------------------
#  An owner-confirmed dealer (Ravi Medical Agency: no summary; the owner's Confirm on row 3 stands for it) read 'your Confirm' on the payment sheet
#  and 'your Confirm on row 3 counts as the summary' on the dealer ledger and row 7 -- the same words whether he had confirmed or not. Now they
#  say which, PER DEALER, from the ONE tally (_s749_groups: row 3's bills waiting vs confirmed), in the purchase check's own words (S857):
#  'settled by your confirmation' or 'waiting for your confirmation (purchase check, row 3)'. A counted month only (row 3 exists only there).
#  The state, the figures, the holds and the payable never change -- words only. A tally that cannot be read reassures nobody ('see the
#  purchase check, row 3'). Fail-soft: any other error, the words as before. Re-entry guarded (the tally never asks for itself).
import threading as _s867_threading                        # noqa: E402
_S867_IN = _s867_threading.local()
S867_SHORT = {"settled": "settled by your confirmation", "waiting": "waiting for your confirmation (purchase check, row 3)",
              "unread": "your confirmation — see the purchase check, row 3"}
S867_LONG = {"settled": "Settled by your confirmation — it stands as the summary · Marg %s",
             "waiting": "Waiting for your confirmation on row 3 of the purchase check — it will stand as the summary · Marg %s",
             "unread": "Your confirmation stands as the summary — see row 3 of the purchase check for whether it is given · Marg %s"}


def s867_confirm_state(con, month):
    """READ ONLY: {dealer key: 'waiting' | 'settled'} for the owner-confirmed dealers' bills of a month (a bill on row 3 = waiting; only
    confirmed bills = settled; a dealer with neither is not listed), or None when the tally cannot be read."""
    try:
        r = register(con, month)
        g = _s749_groups(con, r, Ctx(con))
    except Exception as e:                                    # noqa: BLE001 -- unread: nothing reassuring
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867 tally: %r" % (e,), file=_sys.stderr)
        return None
    out = {}
    for x in g.get("confirmed") or []:
        out[str(x.get("supplier") or "")] = "settled"
    for x in g.get("confirm") or []:
        out[str(x.get("supplier") or "")] = "waiting"
    return out


def _s867_states(con, month, keys):
    """{key: 'settled' | 'waiting' | 'unread'} for the given confirm-state dealer keys of a counted month; {} when not counted, inside the
    tally itself, or on any error."""
    if not keys or getattr(_S867_IN, "on", False) or month_class(con, month) != "counted":
        return {}
    _S867_IN.on = True
    try:
        st = s867_confirm_state(con, month)
    finally:
        _S867_IN.on = False
    if st is None:
        return {k: "unread" for k in keys}
    return {k: st[k] for k in keys if k in st}


_s750_dealers_before_s867 = s750_dealers
_s750_sheet_before_s867 = s750_sheet


def s750_dealers(con, month, r=None, cx=None, scans=None):    # noqa: F811 -- S867: an owner-confirmed dealer's words say settled / waiting
    ds = _s750_dealers_before_s867(con, month, r, cx, scans)
    try:
        conf = [d for d in ds if d.get("state") == "confirm"]
        sts = _s867_states(con, month, [d["key"] for d in conf])
        for d in conf:
            s = sts.get(d["key"])
            if s:
                d["words"] = S867_LONG[s] % rs(d.get("net_p") or 0)
    except Exception as e:                                    # noqa: BLE001 -- the words as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867: %r" % (e,), file=_sys.stderr)
    return ds


def s750_sheet(con, month):                                   # noqa: F811 -- S867: the payment sheet's word for an owner-confirmed dealer
    out = _s750_sheet_before_s867(con, month)
    try:
        keys = [k for k, v in out.items() if v.get("state") == "confirm"]
        sts = _s867_states(con, month, keys)
        for k in keys:
            s = sts.get(k)
            if s:
                out[k] = dict(out[k], words=S867_SHORT[s])
    except Exception as e:                                    # noqa: BLE001 -- the words as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S867: %r" % (e,), file=_sys.stderr)
    return out
# ---- S867 end ---------------------------------------------------------------------------------------------------------------------------
'''
TAIL_PA = '''


# ---- S867_CONFIRM_WORDS (18-Nov-2026, Sanjeevni session 481; D1003 item 1): the payment sheet's chip for an owner-confirmed dealer -----------
#  scan_register.s750_sheet now says 'settled by your confirmation' (green, as 'agrees') or 'waiting for your confirmation (purchase check,
#  row 3)' / 'your confirmation — see the purchase check, row 3' (amber, the default for any other word). Words only; nothing else on the sheet.
_s750_chip_before_s867 = _s750_chip


def _s750_chip(i):                                            # noqa: F811 -- S867
    if i and str(i.get("words") or "") == "settled by your confirmation":
        return ' <span class="chip ok">%s</span>' % _esc(i["words"])
    return _s750_chip_before_s867(i)
# ---- S867 end ---------------------------------------------------------------------------------------------------------------------------
'''
os.makedirs(OUT, exist_ok=True)
for f, tail in (("scan_register.py", TAIL_SR), ("purchase_app.py", TAIL_PA)):
    b = open(os.path.join(SRC, f), "rb").read()
    assert hashlib.md5(b).hexdigest() == FROM[f], "%s is not at its FROM pin" % f
    t = (b.decode("utf-8").rstrip("\n") + tail).encode("utf-8")
    open(os.path.join(OUT, f), "wb").write(t)
    print(f, hashlib.md5(t).hexdigest())
