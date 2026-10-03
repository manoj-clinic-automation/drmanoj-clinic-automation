#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""apply_s463.py -- S463_ROLE_LOCKS (session 292, 03-Oct-2026): the checker's figures answer only the checker.

Built from the real file (/root/finance/finance_app.py at 27a162e6, as S462 leaves it). F-707: the gate lets in any
login with ANY role on the unit, and these handlers had no check of their own -- so a 'viewer' (the returns desk) or
a maker could read the month's totals, every day's closing drawer, parked cash and the patient-named day lines by
typing the address. Each handler was read with every page that calls it (38 handlers; S292).

  the checker only      /finance/review · /finance/workbench · /finance/api/month/<ym> · /finance/api/days ·
                        /finance/api/parked · /finance/api/month/<ym>/close-check · /finance/api/sources ·
                        /finance/api/archive/queue (or the worker's token) ·
                        /finance/clinic/review · /finance/clinic/api/month/<ym> · /finance/clinic/api/days ·
                        /finance/clinic/api/parked
  maker or checker      /finance/api/day/<date>/lines · /finance/clinic/api/day/<date>
  LEFT AS THEY ARE      the clinic tile and clinic exceptions (reception's entry page reads both), both attachment
                        routes, /finance/api/shout, the clinic entry page, the five clinic 'not in this slice' stubs.
No page a maker uses calls a locked route. The five edits inside selftest() keep its own role assumptions true.
Each anchor must be found exactly once; anything else leaves the file as it was.   usage: apply_s463.py <finance_app.py>
"""
import hashlib
import sys

FROM = "27a162e6740140d4ce7d2e293eae9809"
EDITS = []

CHK = ('    u, err = require("checker")                                   # S463 (F-707): the checker\'s figures\n'
       '    if err:\n'
       '        return err\n')
CHK_PAGE = ('    u, err = require("checker")                                   # S463 (F-707): the checker\'s screen\n'
            '    if err:\n'
            '        return redirect(PORTAL_LOGIN, code=302)\n')
CCHK = ('    u, err = require("checker", unit=CLINIC_UNIT)                 # S463 (F-707): the checker\'s figures\n'
        '    if err:\n'
        '        return err\n')


def ed(name, old, new):
    EDITS.append((name, old, new))


def after(name, anchor, block):
    ed(name, anchor, anchor + block)


# ---- medical
after("page_review", '@app.route("/finance/review")\ndef page_review():\n', CHK_PAGE)
after("api_month", '@app.route("/finance/api/month/<ym>")\ndef api_month(ym):\n', CHK)
after("page_workbench", '@app.route("/finance/workbench")\ndef page_workbench():\n', CHK_PAGE)
after("api_sources", '@app.route("/finance/api/sources")\ndef api_sources():\n', CHK)
after("api_day_lines", '@app.route("/finance/api/day/<date_iso>/lines")\ndef api_day_lines(date_iso):\n',
      '    u, err = require("maker", "checker")                          # S463 (F-707): patient names -- never a viewer\n'
      '    if err:\n'
      '        return err\n')
after("api_days", '@app.route("/finance/api/days")\ndef api_days():\n', CHK)
after("api_parked", '@app.route("/finance/api/parked")\ndef api_parked():\n', CHK)
after("api_month_close_check", '@app.route("/finance/api/month/<ym>/close-check")\ndef api_month_close_check(ym):\n', CHK)
after("api_archive_queue",
      '    quietly stall — if this list stops draining, it is visible."""\n',
      '    if not _tok_ok(request.headers.get("X-Finance-Cron"), CRON_TOKEN):   # S463 (F-707): the worker\'s token,\n'
      '        u, err = require("checker")                               # or the checker -- nobody else\n'
      '        if err:\n'
      '            return err\n')
# ---- clinic
after("clinic_page_review",
      '    clinic endpoints answer \'not in this slice\' loudly rather than 404ing."""\n',
      '    u, err = require("checker", unit=CLINIC_UNIT)                 # S463 (F-707): the checker\'s screen\n'
      '    if err:\n'
      '        return redirect(PORTAL_LOGIN, code=302)\n')
after("clinic_api_day", '@app.route("/finance/clinic/api/day/<date_iso>")\ndef clinic_api_day(date_iso):\n',
      '    u, err = require("maker", "checker", unit=CLINIC_UNIT)        # S463 (F-707): reception and the checkers\n'
      '    if err:\n'
      '        return err\n')
after("clinic_api_month", '@app.route("/finance/clinic/api/month/<ym>")\ndef clinic_api_month(ym):\n', CCHK)
after("clinic_api_days", '@app.route("/finance/clinic/api/days")\ndef clinic_api_days():\n', CCHK)
after("clinic_api_parked", '@app.route("/finance/clinic/api/parked")\ndef clinic_api_parked():\n', CCHK)

# ---- selftest(): its own role assumptions, kept true (it ran these five as a maker)
ed("selftest: the review page",
   '    r = c.get("/finance/review")\n    check("review page 200", r.status_code == 200)\n',
   '    check("S463: the review page sends a maker back to the portal",\n'
   '          c.get("/finance/review").status_code == 302)\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "checker"            # S463: the review page is the checker\'s\n'
   '    r = c.get("/finance/review")\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "maker"\n'
   '    check("review page 200", r.status_code == 200)\n')
ed("selftest: the month, first",
   '    r = c.get("/finance/api/month/2026-08")\n    j = r.get_json()\n    check("month 200", j["ok"])\n',
   '    check("S463: the month is refused to a maker", c.get("/finance/api/month/2026-08").status_code == 403)\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "checker"            # S463: the month is the checker\'s\n'
   '    r = c.get("/finance/api/month/2026-08")\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "maker"\n'
   '    j = r.get_json()\n    check("month 200", j["ok"])\n')
ed("selftest: the day list",
   '    r = c.get("/finance/api/days?days=400")\n    j = r.get_json()\n',
   '    check("S463: the day list is refused to a maker", c.get("/finance/api/days?days=400").status_code == 403)\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "checker"            # S463: the day list is the checker\'s\n'
   '    r = c.get("/finance/api/days?days=400")\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "maker"\n'
   '    j = r.get_json()\n')
ed("selftest: the month, second",
   '    r = c.get("/finance/api/month/%s" % D1[:7])\n    j = r.get_json()\n',
   '    os.environ["FINANCE_DEV_ROLE"] = "checker"            # S463: the month is the checker\'s\n'
   '    r = c.get("/finance/api/month/%s" % D1[:7])\n'
   '    os.environ["FINANCE_DEV_ROLE"] = "maker"\n'
   '    j = r.get_json()\n')
ed("selftest: the medical review, read as a checker",
   '    _mrv = c.get("/finance/review").get_data(as_text=True)\n',
   '    _mrv = c.get("/finance/review", headers=DRM).get_data(as_text=True)   # S463: as a checker\n')


def apply(src):
    for name, old, new in EDITS:
        got = src.count(old)
        if got != 1:
            raise SystemExit("!! anchor '%s' found %d time(s), expected 1 - nothing written" % (name, got))
        src = src.replace(old, new)
    return src


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply_s463.py <path to finance_app.py>")
    path = sys.argv[1]
    raw = open(path, "rb").read()
    have = hashlib.md5(raw).hexdigest()
    if have != FROM:
        raise SystemExit("!! %s is %s, not %s - nothing written" % (path, have, FROM))
    out = apply(raw.decode("utf-8")).encode("utf-8")
    compile(out, path, "exec")
    with open(path, "wb") as fh:
        fh.write(out)
    print("finance_app.py %s -> %s (%d edits; %+d bytes)"
          % (have[:8], hashlib.md5(out).hexdigest()[:8], len(EDITS), len(out) - len(raw)))


if __name__ == "__main__":
    main()
