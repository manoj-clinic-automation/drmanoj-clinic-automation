#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_clinic_day_mpr_s225.py -- S225: the bank MPR line ON the Day Revenue page, with a direct link.

The owner, 04-Sep-2026 15:35 IST: "/finance/clinic/bank/mpr isn't showing in the day sheet; on
/finance/clinic/day the report should be stated as applied or pending from bank or whatever, and a
direct link of the day's MPR to match then and there."

So, on finance_clinic_day.py (live pin dceb79a0…, the S223_DAY_PAGE_EDITS bytes -- S224_BANK_MPR_STATUS
§5 said this patch waits for that pin; the pin was read back on 04-Sep 13:05):
  (A) the day page gets a card under the header: bank_mpr_status's own line (APPLIED at / WAITING /
      LATE / REJECTED / NO ROWS / NOT RECEIVED), the day's own online (UPI) total beside the bank's
      applied total with the difference, and a link to /finance/clinic/bank/mpr/<date>;
  (B) the month table gets a "Bank" column: one word per day, linking to that day's MPR page.
One rule, read from one place: mpr_state() in bank_mpr_status.py (S224) -- nothing here re-decides
what the bank's state is (D349). If that module is absent the page says so and still renders.

Anchors are exact and each must match exactly once; the file's md5 must be the one you pass.
Run on the box:
    md5sum /root/finance/finance_clinic_day.py
    /root/wa/venv/bin/python3 -B /root/finance/patch_clinic_day_mpr_s225.py <that md5>
"""
import datetime as dt
import hashlib
import io
import os
import shutil
import sys

TARGET = os.environ.get("FCD_PATH", "/root/finance/finance_clinic_day.py")
MARK = "S225_DAY_MPR_LINE begin"

A_OLD = '''import calendar
import datetime as dt
import json
'''
A_NEW = '''import calendar
import datetime as dt
import json
# --- S225_DAY_MPR_LINE begin -- the bank's word, read from the one module that decides it ---
try:
    import bank_mpr_status as _mpr                                # S224, beside this file
except Exception:                                                 # noqa: BLE001
    _mpr = None


def _mpr_res(con, date):
    """bank_mpr_status.mpr_state for this clinic day, or None when the module is absent."""
    if _mpr is None:
        return None
    try:
        return _mpr.mpr_state(con, date, unit=_unit)
    except Exception:                                             # noqa: BLE001
        return None


_MPR_WORD = {"applied": "Applied", "late": "Applied late", "rejected": "Refused", "no_rows": "No UPI",
             "waiting": "Waiting", "not_received": "Not received", "bad_date": "—"}


def _mpr_card(con, date, online_p):
    """The day page's bank card: the line, the match, the link."""
    res = _mpr_res(con, date)
    link = ('<p class="noprint"><a class="btn" href="/finance/clinic/bank/mpr/%s">Open the day\\'s bank MPR ›</a></p>'
            % date)
    if res is None:
        return ('<div class="card"><h2>Bank MPR</h2><p>The bank-status module is not installed beside this page, '
                'so the bank\\'s word cannot be shown here.</p>%s</div>' % link)
    match = ""
    if res.get("state") in ("applied", "late"):
        bank_p = int(res.get("total_p") or 0)
        diff = bank_p - int(online_p or 0)
        if diff == 0:
            match = ('<p><b>Matches:</b> our online (UPI) for the day is ₹ %s and the bank applied ₹ %s.</p>'
                     % (_rupees(online_p), _rupees(bank_p)))
        else:
            match = ('<p><b>Does not match:</b> our online (UPI) for the day is ₹ %s; the bank applied ₹ %s — '
                     '<b>%s ₹ %s</b>. Open the MPR to see which entries differ.</p>'
                     % (_rupees(online_p), _rupees(bank_p), "bank is higher by" if diff > 0 else "bank is lower by",
                        _rupees(abs(diff))))
    return '<div class="card"><h2>Bank MPR</h2>%s%s%s</div>' % (_mpr.fragment(res), match, link)


def _mpr_cell(con, date):
    """The month table's one word, linking to the day's MPR page."""
    res = _mpr_res(con, date)
    if res is None:
        return "<td class='n'>—</td>"
    word = _MPR_WORD.get(res.get("state"), "—")
    col = getattr(_mpr, "_COLOUR", {}).get(res.get("state"), "#333")
    return ("<td class='n'><a href='/finance/clinic/bank/mpr/%s' style='color:%s;text-decoration:none'>%s</a></td>"
            % (date, col, word))
# --- S225_DAY_MPR_LINE end ---
'''

# (A) the day page: the card after the header card, before the splits query
B_OLD = '''                   _people(lines), day["total_count"],
                   day["free_revisits"], day["free_concession"])]

    splits = []
'''
B_NEW = '''                   _people(lines), day["total_count"],
                   day["free_revisits"], day["free_concession"])]
    out.append(_mpr_card(con, date, _tender(day)["online"]))          # S225_DAY_MPR_LINE

    splits = []
'''

# (B) the month table: a Bank column. The row builder gets `con` through a module global set by the
#     page (the function signature is left alone so nothing else that calls it changes).
C_OLD = '''    body = [_headline(latest),
            _month_table(rows, first, prev, nxt, y, m),
            _foot(span, u)]'''
C_NEW = '''    global _MPR_CON
    _MPR_CON = con                                                    # S225_DAY_MPR_LINE
    body = [_headline(latest),
            _month_table(rows, first, prev, nxt, y, m),
            _foot(span, u)]'''
D_OLD = '''            "<td class='n'>%s / %s</td></tr>" % (
                r["business_date"], _human(r["business_date"]), r["total_count"],'''
D_NEW = '''            "<td class='n'>%s / %s</td>%s</tr>" % (
                r["business_date"], _human(r["business_date"]), r["total_count"],'''
G_OLD = '''                r["evening"] if r["evening"] is not None else "—"))'''
G_NEW = '''                r["evening"] if r["evening"] is not None else "—",
                _mpr_cell(globals().get("_MPR_CON"), r["business_date"])))       # S225_DAY_MPR_LINE'''
E_OLD = '''            <th class="r">Split</th><th class="n">M / E</th>
          </tr></thead>'''
E_NEW = '''            <th class="r">Split</th><th class="n">M / E</th><th class="n">Bank</th>
          </tr></thead>'''
F_OLD = '''            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>
            <td></td></tr></tfoot>'''
F_NEW = '''            <td class="r">%s</td><td class="r">%s</td><td class="r">%s</td><td class="r">%s</td>
            <td></td><td></td></tr></tfoot>'''

PAIRS = (("imports", A_OLD, A_NEW), ("day page header card", B_OLD, B_NEW), ("month page body", C_OLD, C_NEW),
         ("month row", D_OLD, D_NEW), ("month row args", G_OLD, G_NEW), ("month head", E_OLD, E_NEW),
         ("month foot", F_OLD, F_NEW))


def main():
    if len(sys.argv) < 2 or len(sys.argv[1]) != 32:
        sys.exit("USAGE: patch_clinic_day_mpr_s225.py <md5 of the finance_clinic_day.py you are patching>")
    from_md5 = sys.argv[1].lower()
    if not os.path.exists(TARGET):
        sys.exit("REFUSING: %s not found" % TARGET)
    src = io.open(TARGET, encoding="utf-8").read()
    cur = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    if MARK in src:
        print("ALREADY PATCHED  (%s present); pin %s -- nothing to do" % (MARK, cur))
        return
    if cur != from_md5:
        sys.exit("REFUSING: %s is %s, you said %s. Read the box's pin again." % (TARGET, cur, from_md5))
    for label, old, _n in PAIRS:
        if src.count(old) != 1:
            sys.exit("REFUSING: anchor %r matched %d times, expected exactly 1" % (label, src.count(old)))
    new = src
    for _l, old, rep in PAIRS:
        new = new.replace(old, rep, 1)
    bak = TARGET + ".bak_S225_mpr_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(TARGET, bak)
    io.open(TARGET, "w", encoding="utf-8", newline="\n").write(new)
    try:
        import py_compile, tempfile
        fd, cf = tempfile.mkstemp(suffix=".pyc"); os.close(fd)
        try:
            py_compile.compile(TARGET, cfile=cf, doraise=True)
        finally:
            try: os.remove(cf)
            except OSError: pass
    except Exception as e:                                            # noqa: BLE001
        shutil.copy2(bak, TARGET)
        sys.exit("REFUSING: compile failed (%s); restored %s" % (e, bak))
    got = hashlib.md5(io.open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % from_md5)
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % got)


if __name__ == "__main__":
    main()
