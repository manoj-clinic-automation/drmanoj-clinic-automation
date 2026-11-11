


# ---- S781 (11-Nov-2026, Sanjeevni session 426, kit S781_PROVISIONAL_BILLS; D891, D892 -- the owner's mock V3 approved 04:29 IST) ------
#  The Purchase bills page (/page/scans) opens with provisional_s781.summary_html: the month in three parts (in Marg · scanned, not yet in
#  Marg · both), how reliable the scans are, the provisional list with each scan's read lines, and -- for the doctor -- where Marg's bill
#  differs from its scan, with Check here (the scan inline, the lines side by side) and his taps. NEVER into stock (D891).
#  POST /api/s781/mark {bill, action: amir|clear|return|flag|undo, flag, note} -- the doctor only. Fail-soft: an error in S781 leaves the
#  page exactly as it was before it.
KIT_S781 = "S781_PROVISIONAL_BILLS"
import sys as _sys_s781                                       # noqa: E402


def _s781():
    import provisional_s781                                   # noqa: PLC0415 -- beside this file
    return provisional_s781


_s781_register_page_before = _s454_register_page
S781_AT = '<div class="hd" id="s454heads">'


def _s454_register_page(con, u):                              # noqa: F811 -- S781: the provisional bills at the top
    out = _s781_register_page_before(con, u)
    try:
        page = out[0] if isinstance(out, tuple) else out          # _page answers (html, 200, headers)
        if isinstance(page, str) and S781_AT in page and request.args.get("legacy") != "1":
            SR = _s454_sr()
            months = SR.months_with_bills(con)
            month = str(request.args.get("month") or (months[0] if months else dt.date.today().strftime("%Y-%m")))[:7]
            if re.match(r"^\d{4}-\d{2}$", month):
                add = _s781().summary_html(con, month, request.script_root + _url_prefix, _is_doctor(u))
                page = page.replace(S781_AT, add + S781_AT, 1)
                out = ((page,) + tuple(out[1:])) if isinstance(out, tuple) else page
    except Exception as e:                                    # noqa: BLE001 -- the page as it was before S781
        print("S781 register page failed: %r" % (e,), file=_sys_s781.stderr)
    return out


@bp.route("/api/s781/mark", methods=["POST"])
def api_s781_mark():
    """The doctor's answer on a bill whose Marg entry differs from its scan: {bill, action, flag, note}."""
    u, err = _person("checker", "maker", "viewer")
    if err:
        return err
    if not _is_doctor(u):
        return jsonify(ok=False, error="owner_only", message="Only the doctor answers this."), 403
    b = request.get_json(silent=True) or {}
    try:
        bid = int(b.get("bill") or 0)
    except (TypeError, ValueError):
        bid = 0
    if bid <= 0:
        return jsonify(ok=False, error="bad_request", message="Which bill?"), 400
    con = _db()
    ok, msg, code = _s781().mark(con, _who(u), bid, str(b.get("action") or ""), str(b.get("flag") or ""), str(b.get("note") or ""))
    return jsonify(ok=ok, message=msg), code
# ---- S781 end ---------------------------------------------------------------------------------------------------------------------------
