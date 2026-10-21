#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""edits_s610.py -- kit S610 (session S331, 21-Oct-2026): exact, counted edits turning the live /root/att_dashboard.py
(ebd8bd85) into the S610 file.     python3 edits_s610.py LIVE OUT [KIT]   (exit 0 only if all anchors occur once, = KIT)

THE OWNER, 21-Oct-2026, on Surendra's October attendance at https://attendance.dr-manoj.in/month :
 18:56 IST "few days he has punched twice and is mentioned out there wrongly" -- he presses twice on arrival
       (09:22 and 09:22); the page showed the second press as his OUT time, and the day view "left early".
 19:03 IST "in attendance these 2 sundays are blank, absent isn't written there, and on top of page it's written
       present 14, absent 5" -- the page never counted a Sunday, while the salary sheet counts a Sunday-duty
       person's missed Sunday (7 absences for Surendra).
The page now follows the SALARY SHEET's own rules, read from att_month_report itself: its artefact window
(ARTEFACT_WINDOW_MIN) and its duty_shift().  Absences are written "A"; days off read "off".  Display only: no
attendance or salary figure changes -- the page now agrees with the sheet.
"""
import hashlib
import sys

EDITS = [
    # 1. the two rules, from the salary sheet's own module
    ('import att_config as cfg\nimport att_core as core\n',
     'import att_config as cfg\nimport att_core as core\n'
     '\n'
     '# S610: the attendance page follows the SALARY SHEET\'s own rules, read from att_month_report itself:\n'
     '#  * a second press within its artefact window is not an OUT punch;\n'
     '#  * a day is a duty day by its duty_shift() -- a Sunday-duty person\'s missed Sunday is an absence, written "A".\n'
     'try:\n'
     '    import att_month_report as _AMR\n'
     '    _ART_MIN = _AMR.ARTEFACT_WINDOW_MIN\n'
     'except Exception:                                   # noqa: BLE001\n'
     '    _AMR = None\n'
     '    _ART_MIN = 30\n'
     '\n'
     '\n'
     'def _real_out(rec):\n'
     '    """True only when the last punch is a real punch-out (not a double press on arrival)."""\n'
     '    try:\n'
     '        return rec["n"] >= 2 and (rec["last"] - rec["first"]).total_seconds() > _ART_MIN * 60\n'
     '    except Exception:                               # noqa: BLE001\n'
     '        return False\n'
     '\n'
     '\n'
     'def _pol_all():\n'
     '    try:\n'
     '        return _AMR.load_staff_policy() if _AMR else {}\n'
     '    except BaseException:                           # noqa: BLE001  (it can SystemExit on a bad group)\n'
     '        return {}\n'
     '\n'
     '\n'
     'def _duty_day(date, info, pol):\n'
     '    """Is `date` a duty day for this person -- the salary sheet\'s own duty_shift()."""\n'
     '    if not info or _AMR is None:\n'
     '        return date.weekday() != 6\n'
     '    try:\n'
     '        s, _e = _AMR.duty_shift(date, date.strftime("%Y-%m"), info, pol or {"sunday_group": ""})\n'
     '        return s is not None\n'
     '    except Exception:                               # noqa: BLE001\n'
     '        return date.weekday() != 6\n'),
    # 2-4. the day view: no "left early" / "out" / hours for a double press
    ('        if r["early"]:\n            badge += \' <span class="badge early">left early</span>\'',
     '        if r["early"] and _real_out(r):\n            badge += \' <span class="badge early">left early</span>\''),
    ('            badge += (\' <span class="badge inq">in</span>\' if r["likely_in"]',
     '            badge += (\' <span class="badge inq">in</span>\' if (r["likely_in"] or not _real_out(r))'),
    ('        if r["hours"] is not None:\n'
     '            meta = (f\'<div class="meta"><b>{hm(r["first"])} \\u2013 {hm(r["last"])}</b>\'\n'
     '                    f\'<br>{r["hours"]} hrs &middot; {r["n"]} punches</div>\')\n'
     '        else:\n'
     '            meta = f\'<div class="meta"><b>{hm(r["first"])}</b><br>single punch</div>\'',
     '        if r["hours"] is not None and _real_out(r):\n'
     '            meta = (f\'<div class="meta"><b>{hm(r["first"])} \\u2013 {hm(r["last"])}</b>\'\n'
     '                    f\'<br>{r["hours"]} hrs &middot; {r["n"]} punches</div>\')\n'
     '        else:\n'
     '            _one = "single punch" if r["n"] < 2 else "pressed %d times on arrival &middot; no out punch" % r["n"]\n'
     '            meta = f\'<div class="meta"><b>{hm(r["first"])}</b><br>{_one}</div>\''),
    # 5. the month: the policy, once
    ('    staff = core.load_staff()\n    punches = core.load_punches()\n    present_by_day = {}',
     '    staff = core.load_staff()\n    punches = core.load_punches()\n'
     '    pol_all = _pol_all()                             # S610: the salary sheet\'s duty days\n'
     '    present_by_day = {}'),
    # 6. the month table: out only when real; absent written "A" on duty days; "off" otherwise
    ('                out = rec["last"].strftime("%H:%M") if rec["n"] >= 2 else ""',
     '                out = rec["last"].strftime("%H:%M") if _real_out(rec) else ""'),
    ('            else:\n'
     '                if not sun:\n'
     '                    absent += 1\n'
     '                cells += f\'<td class="{base}abs">&middot;</td>\'',
     '            else:\n'
     '                if dcur == today:\n'
     '                    cells += f\'<td class="{base}">&nbsp;</td>\'       # S610: today is not an absence yet\n'
     '                elif _duty_day(dcur, info, pol_all.get(uid)):\n'
     '                    absent += 1\n'
     '                    cells += f\'<td class="{base}abs abd">A</td>\'     # S610: absent on a duty day, written\n'
     '                else:\n'
     '                    cells += f\'<td class="{base}off">off</td>\''),
    # 7. the phone view: the same
    ('    mdays, mcells = [], {str(u): {} for u in uids}',
     '    mdays, mcells = [], {str(u): {} for u in uids}\n'
     '    mduty = {}                                       # S610: duty days with no punch = absent'),
    ('                    "o": rec["last"].strftime("%H:%M") if rec["n"] >= 2 else "",',
     '                    "o": rec["last"].strftime("%H:%M") if _real_out(rec) else "",'),
    ('                    "l": 1 if rec["late"] else 0}\n'
     '    mdata = _json.dumps({"today": today.day if (today.year == y and today.month == m) else 0,\n'
     '                         "staff": mstaff, "days": mdays, "cells": mcells})',
     '                    "l": 1 if rec["late"] else 0}\n'
     '            elif dcur != today and _duty_day(dcur, staff.get(uid), pol_all.get(uid)):\n'
     '                mduty.setdefault(str(uid), {})[str(dd)] = 1\n'
     '    mdata = _json.dumps({"today": today.day if (today.year == y and today.month == m) else 0,\n'
     '                         "staff": mstaff, "days": mdays, "cells": mcells, "duty": mduty})'),
    ("      else { if(!dy.sun) ab++; html+=emptyCard(dy.wd+' '+dy.d,dy.sun); }",
     "      else { var du=((MD.duty||{})[pid]||{})[dy.d]; if(du) ab++; html+=emptyCard(dy.wd+' '+dy.d,!du); }"),
    ("      else html+=emptyCard(s.name,false);",
     "      else html+=emptyCard(s.name,!(((MD.duty||{})[String(s.uid)]||{})[did]));"),
    # 8. the styles and the key
    ('td.abs { color:#c9d0d8; }',
     'td.abs { color:#c9d0d8; }\ntd.abd { color:#c0392b; font-weight:700; }\ntd.off { color:#c9d0d8; font-size:8px; }'),
    ('&middot; = no punch. Shaded = Sunday. Orange = late. "P" = days present, "A" = working-day absences.',
     '<b>A</b> = absent on a duty day, counted as on the salary sheet (Sundays too, for those on Sunday duty); '
     '"off" = not a duty day.\nShaded = Sunday. Orange = late. "P" = days present, "A" column = absences.'),
]


def main():
    live, out = sys.argv[1], sys.argv[2]
    kit = sys.argv[3] if len(sys.argv) > 3 else None
    s = open(live, encoding="utf-8").read()
    for i, (old, new) in enumerate(EDITS, 1):
        n = s.count(old)
        if n != 1:
            print("  REFUSED: edit %d's anchor occurs %d times (expected 1)" % (i, n))
            return 1
        s = s.replace(old, new)
    with open(out, "w", encoding="utf-8", newline="") as fh:
        fh.write(s)
    a = hashlib.md5(open(out, "rb").read()).hexdigest()
    print("  %d edits applied · rebuilt %s" % (len(EDITS), a[:8]))
    if kit:
        b = hashlib.md5(open(kit, "rb").read()).hexdigest()
        print("  kit %s  %s" % (b[:8], "same" if a == b else "DIFFERENT"))
        return 0 if a == b else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
