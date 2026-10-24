#!/usr/bin/python3
"""make_s636.py -- kit S636_DAY_CHECK: the counted edits on the REAL bytes of the 24-Oct bundle (F-472: no inferred anchor).
    python make_s636.py <clinic_register.py 38d0cb4f> <owner_console.py 2b985708> <out_dir>
Every anchor must occur exactly once or nothing is written."""
import hashlib, os, sys

FROM = {"clinic_register.py": "38d0cb4f0615c9aefcf16d3dee5dfea0", "owner_console.py": "2b985708b1dc3239fafbb7f41e969e55"}

CR_EDITS = [
 # 1 -- init mounts day_check beside the register (guarded: without it the register is exactly as before)
 ('''    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp
''', '''    _db, _require, _audit, _unit = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp, url_prefix=url_prefix)
    try:                                         # S636 (D776): the day's corrections page, day_check.py beside this file
        import day_check as _s636_dc             # noqa: PLC0415
        _s636_dc.init(app, db_getter, require_fn, audit_fn, unit=unit)
    except Exception as _ex_s636:                # noqa: BLE001 -- the register works without it
        import sys as _sys                       # noqa: PLC0415
        print("day_check NOT mounted: %s" % _ex_s636, file=_sys.stderr)
    return bp


def _s636_summary(con, d):
    """S636 (D776, F-1018): the day's check in words -- every kind named, 'all correct' on a clean day -- or None when
    day_check.py is absent or cannot read the day. Display only."""
    try:
        import day_check as _dc                  # noqa: PLC0415
        chk = _dc.check_day(con, d)
        if chk.get("state") != "checked":
            return None
        return _dc.summary_en(chk).split(": ", 1)[1], _dc.is_clean(chk)
    except Exception:                            # noqa: BLE001
        return None


def _s636_check(con, d, u):
    """S636 (D776): the day's corrections, as one-line cards with their buttons, under the three records."""
    try:
        import day_check as _dc                  # noqa: PLC0415
    except Exception:                            # noqa: BLE001
        return ""
    try:
        chk = _dc.check_day(con, d)
        eng = "checker" in set((u or {}).get("roles") or [])
        return ("<div class='card' id='check'><h2>%s</h2>%s</div>%s"
                % ("The day's corrections" if eng else "Din ki galtiyan", _dc.cards_html(con, chk, u, eng), _dc.STYLE))
    except Exception as ex:                      # noqa: BLE001
        return "<div class='card'><p class='mut'>day check: %s</p></div>" % _esc(ex)
'''),
 # 2 -- the day list's chip opens the day's corrections (F-1018: it was a label)
 ('''    for d in days:
        t = three_way(con, d)
        reg_tot = None if t["reg"] is None else (t["r_cash"] + t["r_upi"] + t["r_card"])
        body.append(
            "<tr><td class='d'>%s</td><td class='r'>%s</td>"
            "<td><span class='pill %s'>%s</span></td>"
            "<td class='noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a></td></tr>"
            % (_human(d), _r(reg_tot) if reg_tot is not None else "—",
               t["verdict"].replace(" ", "_"), _esc(t["verdict"] or "—"), d,
               "edit" if t["reg"] is not None else "FILL"))
''', '''    for d in days:
        t = three_way(con, d)
        reg_tot = None if t["reg"] is None else (t["r_cash"] + t["r_upi"] + t["r_card"])
        _sm = _s636_summary(con, d) if t["reg"] is not None else None          # S636 (D776, F-1018)
        if _sm is not None:
            chip = ("<a class='pill %s' href='/finance/clinic/check/%s'>%s</a>"
                    % ("all_agree" if _sm[1] else "docterz_differs", d, _esc(_sm[0])))
        else:
            chip = "<span class='pill %s'>%s</span>" % (t["verdict"].replace(" ", "_"), _esc(t["verdict"] or "—"))
        body.append(
            "<tr><td class='d'>%s</td><td class='r'>%s</td>"
            "<td>%s</td>"
            "<td class='noprint'><a class='btn' href='/finance/clinic/register/%s'>%s</a></td></tr>"
            % (_human(d), _r(reg_tot) if reg_tot is not None else "—",
               chip, d,
               "edit" if t["reg"] is not None else "FILL"))
'''),
 # 3 -- the Save says the day's check at once
 ('''                msg = "<div class='ok'><b>Saved.</b> %s</div>" % _esc(three_way(con, date)["why"])
''', '''                msg = "<div class='ok'><b>Saved.</b> %s</div>" % _esc(three_way(con, date)["why"])
                _sm = _s636_summary(con, date)                                  # S636 (D776): checked on the Save
                if _sm is not None:
                    msg += ("<div class='%s'><b>The day's check:</b> %s · <a href='#check'>see below</a></div>"
                            % ("ok" if _sm[1] else "bad", _esc(_sm[0])))
'''),
 # 4 -- the cards under the three records
 ('''                     date, date, _s249_blocks(con, date, u) + _drawer_html(con, date) + _compare_html(t, date))
''', '''                     date, date, _s249_blocks(con, date, u) + _drawer_html(con, date) + _compare_html(t, date)
                     + _s636_check(con, date, u))                               # S636 (D776)
'''),
 # 5 -- a chip that is a link looks like one
 ('''.pill.bank_differs,.pill.waiting_bank{background:#fdeecd}
''', '''.pill.bank_differs,.pill.waiting_bank{background:#fdeecd}
a.pill{color:var(--ink);text-decoration:underline;white-space:normal;display:inline-block}
'''),
]

OC_EDITS = [
 ('''    piece(lines, "The clinic's day", clinic)
    piece(lines, "Sanjeevni's day", sanj)
''', '''    piece(lines, "The clinic's day", clinic)

    def corrections():                                                 # S636 (D776): his line -- counts only, no patient
        import day_check as DC                                         # noqa: PLC0415
        out = []
        for i in range(7):
            day = (dt.date.fromisoformat(D) - dt.timedelta(days=i)).isoformat()
            chk = DC.check_day(con, day)
            if i and (chk.get("state") != "checked" or DC.is_clean(chk)):
                continue                                               # an earlier day shows only while it has lines
            dot = "g" if DC.is_clean(chk) else ("w" if chk.get("state") == "checked" else "n")
            out.append(L(dot, DC.summary_en(chk), href="/finance/clinic/check/%s" % day, link="corrections", sub=bool(i)))
        return out

    piece(lines, "The day's corrections", corrections)
    piece(lines, "Sanjeevni's day", sanj)
'''),
]


def apply(src, edits, name):
    for i, (a, b) in enumerate(edits, 1):
        n = src.count(a)
        if n != 1:
            sys.exit("STOP: %s edit %d anchor found %d times" % (name, i, n))
        src = src.replace(a, b)
    return src


def main():
    cr, oc, out = sys.argv[1], sys.argv[2], sys.argv[3]
    for p, n in ((cr, "clinic_register.py"), (oc, "owner_console.py")):
        h = hashlib.md5(open(p, "rb").read()).hexdigest()
        if h != FROM[n]:
            sys.exit("STOP: %s is %s, not the %s this kit was built from" % (p, h[:8], FROM[n][:8]))
    os.makedirs(out, exist_ok=True)
    for p, n, e in ((cr, "clinic_register.py", CR_EDITS), (oc, "owner_console.py", OC_EDITS)):
        s = apply(open(p, encoding="utf-8").read(), e, n)
        with open(os.path.join(out, n), "w", encoding="utf-8", newline="") as fh:
            fh.write(s)
        print("%s: %d counted edits -> %s" % (n, len(e), hashlib.md5(s.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()
