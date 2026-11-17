"""make_s855.py <code dir holding the FROM files> <out dir> -- kit S855_MONTH_ASKS: four files, each with ONE tail block appended (no anchor
inside the old text), the new month_asks.py beside them (copied from this script's folder). Every FROM file is checked against its pin first."""
import hashlib, os, shutil, sys
SRC, OUT = sys.argv[1], sys.argv[2]
FROM = {"purchase_app.py": "c54b1c315392d9c567f99bb1d589e008", "scan_register.py": "76ad0927829ef5d066101539834d1831",
        "sanjeevni_approvals.py": "960efdd342752b46bdecbc629bce533c", "amir_day.py": "22d962b8ef68dbdbbfc3e576ff1a9060"}
HEAD = ("# ---- S855_MONTH_ASKS (17-Nov-2026, Sanjeevni session 476; the owner 17:08-17:12): a month's open asks -- a Marg report to export again, a\n"
        "#  bill still marked Wrong -- shown wherever they apply (month_asks.py, one source). Fail-soft: without month_asks, every page as before.\n")
TAIL = {
"purchase_app.py": '''


''' + HEAD + '''#  Here: the card at the top of the payment sheet (above the month-end reports card), and the doctor's one tap on a Wrong mark nothing will clear.
_s604_reports_card_before_s855 = _s604_reports_card


def _s604_reports_card(con, month, s, final):                  # noqa: F811 -- S855: the month's asks first
    out = _s604_reports_card_before_s855(con, month, s, final)
    if final:
        return out
    try:
        import month_asks as _ma855                            # noqa: PLC0415 -- beside this file
        if month not in _ma855.months(con) or _s454_sr().month_class(con, month) != "counted":
            return out                                         # review S3: a parked month asks nothing (as the check's own seam)
        doctor = False
        try:
            u855, e855 = _person("checker", "maker", "viewer")
            doctor = bool(u855) and not e855 and _is_doctor(u855)
        except Exception:                                      # noqa: BLE001 -- no button then
            doctor = False
        return _ma855.card_html(con, month, request.script_root + _url_prefix, doctor, where="pay") + out
    except Exception as e:                                     # noqa: BLE001 -- the sheet as before S855
        print("S855 pay card failed: %r" % (e,), file=_sys_s781.stderr)
        return out


@bp.route("/api/s855/correct", methods=["POST"])
def api_s855_correct():
    """The doctor's tap on a bill marked Wrong that nothing will clear by itself: Correct, Marg's figure stands. {bill}."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
    b = request.get_json(silent=True) or {}
    if not isinstance(b, dict):                                # review L5
        b = {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        bid = 0
    if bid <= 0:
        return jsonify(ok=False, error="bad_request", message="Which bill?"), 400
    con = _db()
    try:
        import month_asks as _ma855                            # noqa: PLC0415
        ok, msg, code = _ma855.correct(con, _who(u), bid)
    except Exception as e:                                     # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                      # noqa: BLE001
            pass
        ok, msg, code = False, "Not saved (%s)." % e.__class__.__name__, 503
    return jsonify(ok=ok, message=msg), code
# ---- S855 end ---------------------------------------------------------------------------------------------------------------------------
''',
"scan_register.py": '''


''' + HEAD + '''#  Here: the purchase check -- row 8 counts them (no more "clear" while one is open) and the same card stands at the top of the page.
_s749_rows_before_s855 = s749_rows


def s749_rows(con, r, cx, prefix):                            # noqa: F811 -- S855: row 8 carries the month's asks
    rows, open_n = _s749_rows_before_s855(con, r, cx, prefix)
    try:
        month = r.get("month") or ""
        if month and month_class(con, month) == "counted" and len(rows) > 7:
            import month_asks as _ma855                        # noqa: PLC0415
            n, lines = _ma855.row8_lines(con, month)
            if n or lines:
                lab, sub, cnt, l8, grey = rows[7]
                tot = open_n + n
                rows[7] = (lab, sub, ("%d open" % tot) if tot else cnt, list(lines) + list(l8), grey)
                open_n = tot
    except Exception as e:                                    # noqa: BLE001 -- row 8 as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S855 row 8: %r" % (e,), file=_sys.stderr)
    return rows, open_n


_check_body_before_s855 = check_body


def check_body(con, month, prefix, months, r=None):          # noqa: F811 -- S855: the month's asks at the top
    h = _check_body_before_s855(con, month, prefix, months, r)
    try:
        if month_class(con, month) == "counted":
            import month_asks as _ma855                        # noqa: PLC0415
            card = _ma855.card_html(con, month, prefix, True, where="check")
            if card:
                at = h.find('<h1 id="s726head">')
                h = (h[:at] + card + h[at:]) if at >= 0 else (card + h)
    except Exception as e:                                    # noqa: BLE001 -- the page as before
        import sys as _sys                                    # noqa: PLC0415
        print("scan_register S855 card: %r" % (e,), file=_sys.stderr)
    return h
# ---- S855 end ---------------------------------------------------------------------------------------------------------------------------
''',
"sanjeevni_approvals.py": '''


''' + HEAD + '''#  Here: one Needs-you line per month with something open (target 'scans' -> 'Bills & papers'), opening that month's payment sheet.
#  NEEDS_YOU_WITHOUT_S855=1 is set ONLY by an older kit's frozen walk re-run; the service never sets it.
_needs_you_before_s855 = _needs_you_before_s761


def _needs_you_before_s761(con):                         # noqa: F811 -- S855: S761's grouping reads this name at call time
    r = _needs_you_before_s855(con)
    if os.environ.get("NEEDS_YOU_WITHOUT_S855") == "1":
        return r
    try:
        import month_asks as _ma855                          # noqa: PLC0415
        add = _ma855.needs_lines(con)
        if add:
            r["lines"] = list(r.get("lines") or []) + add
            r["count"] = int(r.get("count") or 0) + len(add)
    except Exception:                                    # noqa: BLE001
        pass
    return r
# ---- S855 end ---------------------------------------------------------------------------------------------------------------------------
''',
"amir_day.py": '''


''' + HEAD + '''#  Here: his card -- one Hindi "do this" line per Marg report to export, first on the card; it leaves by itself when the report arrives.
_state_before_s855 = state


def state(cx, day, who="", step=None, owner=False):           # noqa: F811 -- S855
    S = _state_before_s855(cx, day, who, step, owner)
    S.s855 = []
    try:
        import month_asks                                      # noqa: PLC0415
        S.s855 = month_asks.amir_lines(cx)
    except Exception as e:                                     # noqa: BLE001 -- his day never waits on it
        print("amir_day S855: the month's asks could not be read: %s" % str(e)[:200], file=sys.stderr)
    return S


_card_rows_before_s855 = _card_rows


def _card_rows(S):                                            # noqa: F811 -- S855: the Marg reports to export first on his card
    rows = _card_rows_before_s855(S)
    q = getattr(S, "s855", None) or []
    return [("s855", h, "a Marg report to export", True) for h in q] + rows
# ---- S855 end ---------------------------------------------------------------------------------------------------------------------------
'''}
os.makedirs(OUT, exist_ok=True)
for n, pin in FROM.items():
    b = open(os.path.join(SRC, n), "rb").read()
    assert hashlib.md5(b).hexdigest() == pin, "%s is not at its FROM pin" % n
    t = b.decode("utf-8").rstrip("\n") + TAIL[n]
    open(os.path.join(OUT, n), "wb").write(t.encode("utf-8"))
    print(n, hashlib.md5(t.encode("utf-8")).hexdigest())
here = os.path.dirname(os.path.abspath(__file__))
if os.path.abspath(OUT) != here:
    shutil.copy(os.path.join(here, "month_asks.py"), os.path.join(OUT, "month_asks.py"))
print("month_asks.py", hashlib.md5(open(os.path.join(OUT, "month_asks.py"), "rb").read()).hexdigest())
