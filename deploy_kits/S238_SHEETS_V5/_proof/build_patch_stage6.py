#!/usr/bin/env python3
"""build_patch_stage6.py -- salary_policy.py v1.11 (05c04231..., LIVE since 11-Sep 05:41)
-> v1.12 (S238, the owner 11-Sep-2026): for cover-eligible staff (Shivani) a day whose
OUT-PUNCH is at or after cover_auto_from (17:00 -- the owner: an overstay of up to an
hour past her 16:00 shift end is overtime at 2x; beyond 17:00 the day is paid as cover duty) IS a cover day -- verified by the
punch, no register marking needed. It earns the extra-duty credit, and overtime
counts only beyond cover_end (21:00). Register-marked cover days still count.
Anchored, exactly-once edits; anything else aborts."""
import hashlib, sys
SRC, DST = sys.argv[1], sys.argv[2]
raw = open(SRC, "rb").read()
if hashlib.md5(raw).hexdigest() != "05c04231cdeae7d81af0cf438db1ddc9":
    sys.exit("source is not the live v1.11")
s = raw.decode("utf-8")
def rep(old, new, label):
    global s
    n = s.count(old)
    if n != 1:
        sys.exit("anchor %s found %d times" % (label, n))
    s = s.replace(old, new)

rep('''salary_policy.py — v1.11 (S238, the owner, 11-Sep-2026)''',
    '''salary_policy.py — v1.12 (S238, the owner, 11-Sep-2026) — the COVER DAY is verified by the
out-punch: for cover-eligible staff (Shivani) a punch-out at or after cover_auto_from
(17:00) makes the day a cover day -- extra-duty credit for that day, and overtime only
beyond cover_end (21:00). No register marking is needed; a marked day still counts.
v1.11 (S238, the owner, 11-Sep-2026)''', "doc")

rep('''    "cover_end": "21:00",''', '''    "cover_end": "21:00",
    "cover_auto_from": "17:00",  # S238 (owner 11-Sep): cover staff leaving at/after this = a cover day (extra-duty paid); before it, OT for the up-to-1-hour overstay''', "default")

rep('''        if k == "cover_end":''', '''        if k == "cover_auto_from":
            v = str(v or "").strip()
            if _hhmm(v) is None:
                return False, "cover_auto_from must be a time like 17:00"
            clean[k] = v
            continue
        if k == "cover_end":''', "save")

rep('''def _cover_dates(ym):''', '''def _cover_eligible():
    """Names (lower) the register marks cover_eligible -- only they get automatic cover days."""
    try:
        import sqlite3
        import salary_engine as E
        con = sqlite3.connect(E.DB_PATH)
        out = {(r[0] or "").strip().lower() for r in
               con.execute("SELECT name FROM staff WHERE cover_eligible = 1")}
        con.close()
        return out, ""
    except Exception as e:
        return set(), "%s: %s" % (type(e).__name__, e)


def _cover_dates(ym):''', "elig_fn")

rep('''    cover_dates, cover_err = _cover_dates(ym)''', '''    cover_dates, cover_err = _cover_dates(ym)
    cover_elig, _ce_err = _cover_eligible()
    cover_err = cover_err or _ce_err''', "elig_load")

rep('''        extra_rs = 0.0 if exempt else g.get("extra", 0) * s.get("extra_duty_rs", 200)''',
    '''        # S238 v1.12: a cover-eligible person's cover days = the register's marked days PLUS
        # every day her out-punch is at/after cover_auto_from (verified by the punch).
        _cov = set(cover_dates.get(name.strip().lower(), set()))
        _is_cover_staff = name.strip().lower() in cover_elig
        if _is_cover_staff and not exempt:
            _auto = _hhmm(s.get("cover_auto_from", "17:00")) or 1020
            for _d, _c in (a.get("grid") or {}).items():
                if isinstance(_c, dict) and _c.get("out"):
                    _o = _hhmm(_c.get("out"))
                    if _o is not None and _o >= _auto:
                        try:
                            _cov.add("%s-%02d" % (ym, int(_d)))
                        except (TypeError, ValueError):
                            pass
        extra_days = len(_cov) if _is_cover_staff else g.get("extra", 0)
        extra_rs = 0.0 if exempt else extra_days * s.get("extra_duty_rs", 200)''', "extra")

rep('''        _cov = cover_dates.get(name.strip().lower(), set())
        try:''', '''        try:''', "ot_cov")

rep('''            "night_rs": night_rs, "extra_rs": extra_rs, "outst_rs": outst_rs,''',
    '''            "night_rs": night_rs, "extra_rs": extra_rs, "extra_days": extra_days, "outst_rs": outst_rs,''', "out")

rep("""               'real out-punch; on an extra-duty (cover) day only the minutes after %s.%s%s%s</div>'""",
    """               'real out-punch; on a cover day (marked extra duty, or for cover staff a punch-out '
               'at/after %s) only the minutes after %s.%s%s%s</div>'""", "note_a")
rep("""               % (e(str(res["settings"].get("cover_end", "21:00"))),""",
    """               % (e(str(res["settings"].get("cover_auto_from", "17:00"))),
                  e(str(res["settings"].get("cover_end", "21:00"))),""", "note_b")
open(DST, "w", encoding="utf-8", newline="").write(s)
print("built", DST, hashlib.md5(s.encode("utf-8")).hexdigest())
