"""make_s511.py -- S511_RECEPTION_MATCH. Builds clinic_money.py and tile_grants.json from the live bytes by exact edits.
    python3 make_s511.py <live dir> <out dir>   (the live dir holds both files)"""
import hashlib
import os
import sys

PINS = {"clinic_money.py": "683f75112920adb17c0a077602f4f9ec", "tile_grants.json": "64f8b04937e8841c405cb9070b604aad"}


def rep(s, a, b, what):
    n = s.count(a)
    assert n == 1, "%s: anchor found %d times: %r" % (what, n, a[:70])
    return s.replace(a, b)


def build(live, out):
    got = {}
    for name, pin in PINS.items():
        b = open(os.path.join(live, name), "rb").read()
        assert hashlib.md5(b).hexdigest() == pin, "%s: FROM pin differs" % name
        got[name] = b.decode("utf-8")
    s = got["clinic_money.py"]
    # F-796: the verdict names only the parts that have answered
    s = rep(s, '''        res["lines"] = [("%s: the counter sheet and Docterz agree; the bank part stands on the POS total (%s). Nothing to do."
                         % (dayword, standin["label"])) if standin is not None else                       # S496
                        "%s: the counter sheet, Docterz and the bank agree. Nothing to do." % dayword]''',
            '''        res["lines"] = [("%s: the counter sheet and Docterz agree; the bank part stands on the POS total (%s). Nothing to do."
                         % (dayword, standin["label"])) if standin is not None else                       # S496
                        ("%s: the counter sheet, Docterz and the bank agree. Nothing to do." % dayword) if bank_known else
                        ("%s: the counter sheet and Docterz agree. The bank's file has not come yet -- it is matched when it "
                         "comes. Nothing to do now." % dayword)]                                          # S511 (F-796)''',
            "verdict")
    # the landing: every day still waiting, oldest first
    s = rep(s, '''@bp.route("/finance/clinic/match")
def match_index():
    """Land on the day that needs the person: yesterday, or the newest day not yet closed."""
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Morning match", _denied())
    con = _db()
    _ensure(con)
    if _is_clinic_checker(u) and not _is_named_checker(con, u):
        return redirect("/finance/clinic/money")
    y = (_now().date() - dt.timedelta(days=1)).isoformat()
    return redirect("/finance/clinic/match/%s" % y)''', '''MATCH_FROM = "2026-10-01"          # S511: no staff screen shows a day before this (D687); setting clinic_money.match_from moves it later


def waiting_days(con, named, today=None):
    """S511 (the owner's list, S302 close: 'Morning match lists the October days still waiting for a first pass, oldest first'):
    every working day from MATCH_FROM to yesterday that had a clinic day (Docterz lines or a counter sheet) and is still open --
    and, for the named checker, the days waiting for his check. [(iso, word)], oldest first."""
    today = today or _now().date()
    start = max(MATCH_FROM, _setting(con, "clinic_money.match_from", MATCH_FROM) or MATCH_FROM)
    days = set()
    if _table(con, "clinic_day_line"):
        days |= {r[0] for r in con.execute("SELECT DISTINCT business_date FROM clinic_day_line WHERE business_date>=? AND business_date<?",
                                           (start, today.isoformat()))}
    if _table(con, "clinic_register_day"):
        days |= {r[0] for r in con.execute("SELECT business_date FROM clinic_register_day WHERE business_date>=? AND business_date<?",
                                           (start, today.isoformat()))}
    st = {r["business_date"]: r for r in con.execute("SELECT * FROM clinic_money_day WHERE business_date>=?", (start,))}
    out = []
    for d in sorted(days):
        if not _iso_ok(d) or dt.date.fromisoformat(d).weekday() == 6:
            continue
        r = st.get(d)
        if r is None or r["status"] == "open":
            out.append((d, "pehli jaanch baaki"))
        elif named and r["status"] == "maker_done":
            out.append((d, "aapki jaanch baaki (pehli jaanch: %s)" % (r["maker"] or "-")))
    return out


@bp.route("/finance/clinic/match")
def match_index():
    """S511: the days still waiting for this person, oldest first -- one day goes straight to it; none goes to yesterday."""
    u, err = _require("maker", "checker", unit=_unit)
    if err:
        return _shell("Morning match", _denied())
    con = _db()
    _ensure(con)
    if _is_clinic_checker(u) and not _is_named_checker(con, u):
        return redirect("/finance/clinic/money")
    wait = waiting_days(con, _is_named_checker(con, u))
    if len(wait) == 1:
        return redirect("/finance/clinic/match/%s" % wait[0][0])
    if not wait:
        y = (_now().date() - dt.timedelta(days=1)).isoformat()
        return redirect("/finance/clinic/match/%s" % y)
    items = "".join("<li><a class='btn' href='/finance/clinic/match/%s'>%s</a> <span class='mut'>%s</span></li>"
                    % (d, _esc(dt.date.fromisoformat(d).strftime("%A %d-%b")), _esc(w)) for d, w in wait)
    return _shell("Morning match", "<div class='card'><h2>Ye din abhi baaki hain — sabse purana pehle</h2>"
                  "<p class='mut'>%d din. Pehle wale din se shuru kijiye.</p><ul style='list-style:none;padding:0;line-height:2.4'>%s</ul></div>"
                  % (len(wait), items))''', "match_index")
    g = got["tile_grants.json"]
    g = rep(g, '''  "version": 33,''', '''  "version": 34,''', "grants version")
    g = rep(g, '''    "reception": {
      "extra": [
        "Call Tracker",
        "Call ke baad",
        "Purchase orders"
      ]
    }''', '''    "reception": {
      "extra": [
        "Call Tracker",
        "Call ke baad",
        "Docterz daily collection",
        "Morning match",
        "Check karein",
        "Purchase orders"
      ]
    }''', "grants reception")
    os.makedirs(out, exist_ok=True)
    for name, text in (("clinic_money.py", s), ("tile_grants.json", g)):
        with open(os.path.join(out, name), "wb") as fh:
            fh.write(text.encode("utf-8"))
        print("built %s %s" % (name, hashlib.md5(text.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])
