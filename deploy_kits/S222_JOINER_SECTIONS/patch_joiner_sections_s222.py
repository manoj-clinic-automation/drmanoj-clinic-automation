#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_joiner_sections_s222.py -- S222: the joiner form, told the truth by system.

THE OWNER: "what he may do should be section wise not like this. Like the purchase entry,
expiry check, purchase order, returns, salt fix. These are part of the Marg / Sanjeevni system.
Similarly, for the attendance and salary management system, and then the scan app system...
Search the KB for the attendance and salary sharing on the staff portal and build controls
accordingly. Similarly, there are certain restrictions for staff in the scan app. Find them and
apply them too."

WHAT THE KB ACTUALLY SAYS -- read before anything was built, and it changes the form's shape.

  SCAN APP (assetapp).  Access is NOT a tick box and must never be drawn as one. The portal
  role maps straight through: `staff` -> asset role `reception`, `doctor` -> owner,
  `manager` -> manager, anything else -> NO ACCESS AT ALL (fail-closed, asset_register.py).
  And A-D21 fixes exactly what a reception user may reach:

      RECEPTION_OK = {intake, intake_submit, intake_scan_submit,
                      intake_slip_last, intake_slip, scanner_widget_js, login, logout}
      "the ONLY endpoints a reception user may reach. Everything else 403s server-side,
       regardless of what the UI shows. Fail-closed by construction."

  So a staff login can open the scan screen, submit a bill and its scan, and take the slip --
  and nothing else in that app. The dashboard redirects him to intake rather than 403ing, which
  is a kindness, not a permission. A tick box here would be a lie: he has it the moment he has
  a staff login, and he cannot be given more of it from this page.

  ATTENDANCE & SALARY.  Also mostly not a tick box.
    D337 -- staff see their OWN month and may raise remarks; the visibility windows are
            settings (running month live, completed month until lock+5 days).
    D334 -- a staff member with no machine punch may REQUEST present, under five binding
            rules, request-time-as-punch.
    D338 -- past-day presence correction is APPROVER-ONLY; staff self-requests stay as they are.
    F-31 -- salary is doctor-only. staff_master.csv carries base salaries; the Salary and Staff
            Ledger tiles are doctor, Ledger Entry is manager. A staff member is never shown
            money, and this form cannot grant it.
  The one authority that IS a choice here is `self` -- and its own label has always said
  "(no money)".

SO THE FORM SHOWS FOUR SECTIONS, and only two of them have ticks:

    Sanjeevni — Marg & pharmacy   6 choices
    Front desk                    1 choice
    Attendance & salary           1 choice, plus what everyone gets and what nobody gets
    Scan app — bills              NO CHOICES. What the login already grants, and its limit.

THREE MORE THINGS THE OWNER ASKED FOR, all data instead of code:

  * employment kinds become a SETTING (`joiner.employment_kinds`) so a new kind can be added
    without a deploy; the code tuple is the fallback, so an empty or broken setting changes
    nothing. /api/open validates against the same list, never against the tuple alone.
  * jobs become a SETTING (`joiner.jobs`) merged with every job already used on a record, so
    the list grows itself and is chosen, not typed.
  * a free username is SUGGESTED, checking both the register and the portal store, so a second
    Amir gets `amir2` instead of a collision the owner discovers later.

Target: /root/finance/joiner_app.py   (live pin d3f4c802182c386daf644953bf215595)
Run on the box:  /root/wa/venv/bin/python3 -B /root/finance/patch_joiner_sections_s222.py
Offline:         JA_PATH=./joiner_app.py python3 -B patch_joiner_sections_s222.py
"""

import datetime as dt
import hashlib
import os
import shutil
import sys

TARGET = os.environ.get('JA_PATH', '/root/finance/joiner_app.py')
MARK = "S222 SECTIONS"
EXPECT_FROM = "d3f4c802182c386daf644953bf215595"


# ---- A: the section map, the settings-backed lists, and the helpers ----------
A_OLD = '''@bp.route("/api/authorities")
def api_authorities():
'''

A_NEW = '''# ---- S222 SECTIONS ---------------------------------------------------------
# Which system each authority belongs to. Presentation, served by the register so
# no page ever splits this list by hand.
AUTHORITY_GROUP = {
    "stock_count":    "marg",
    "expiry_check":   "marg",
    "purchase_order": "marg",
    "purchase_entry": "marg",
    "returns":        "marg",
    "salt_fix":       "marg",
    "reception":      "desk",
    "self":           "attendance",
}

# The fourth section has no choices in it, and that is the point: the scan app's
# limit is set by A-D21 in asset_register.py, and attendance's by D334/D337/D338
# and F-31. Written here so the form states what is true rather than offering a
# tick that would not mean anything.
GROUPS = [
    {"key": "marg", "name": "Sanjeevni \\u2014 Marg & pharmacy",
     "note": "Stock, expiry, purchases and returns inside Marg."},
    {"key": "desk", "name": "Front desk",
     "note": "The counter itself."},
    {"key": "attendance", "name": "Attendance & salary",
     "note": "Everyone already sees their OWN month and can raise a remark (D337), and may "
             "request present when the machine has no punch (D334). A past-day correction is "
             "approver-only (D338). SALARY IS NEVER SHOWN TO STAFF (F-31) and cannot be "
             "granted here."},
    {"key": "scan", "name": "Scan app \\u2014 bills",
     "note": "Comes with the portal login, not from this page. A staff login opens the scan "
             "screen, submits a bill and its scan, and takes the slip \\u2014 and nothing else "
             "in that app: A-D21 lists the only endpoints a reception user may reach and "
             "everything else refuses server-side, whatever the screen shows."},
]

DEFAULT_JOBS = ("purchase", "counter", "reception", "pharmacy", "housekeeping")


def _csv_setting(con, key, fallback):
    """A comma-separated setting, or the fallback when it is absent or blank.

    Absent means NOT CONFIGURED, and not configured means nothing changes -- the
    same fail-safe shape as returns.desk_users."""
    try:
        r = con.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
        raw = (_v(r, "value", 0) if r else "") or ""
    except Exception:
        raw = ""
    out = [p.strip() for p in str(raw).split(",") if p.strip()]
    return out or list(fallback)


def employment_kinds(con):
    """The kinds of employment, from a setting so a new one needs no deploy."""
    return [e.strip().upper() for e in _csv_setting(con, "joiner.employment_kinds", EMPLOYMENT)]


def job_list(con):
    """Jobs to choose from: the setting, plus every job already on a record, so
    the list grows itself and nothing has to be typed twice."""
    jobs = _csv_setting(con, "joiner.jobs", DEFAULT_JOBS)
    try:
        for r in con.execute("SELECT DISTINCT role FROM joiner WHERE role IS NOT NULL "
                             "AND TRIM(role)!=''"):
            j = str(_v(r, "role", 0)).strip()
            if j and j.lower() not in [x.lower() for x in jobs]:
                jobs.append(j)
    except Exception:
        pass
    return jobs


def free_username(con, name, wanted=None):
    """A username nobody is using -- in the register OR in the portal store.

    A second Amir must not be discovered as a collision after the account is
    made; he is offered amir2 before anybody types anything."""
    base = (wanted or "").strip().lower() or default_username(name)
    base = "".join(ch for ch in base if ch.isalnum()) or "user"
    taken = set()
    try:
        for r in con.execute("SELECT LOWER(COALESCE(username,'')) u FROM joiner"):
            if _v(r, "u", 0):
                taken.add(_v(r, "u", 0))
    except Exception:
        pass
    CU, path, _why = _portal_users()
    if CU:
        try:
            for x in CU.list_users(path):
                taken.add(str(x.get("user", "")).lower())
        except Exception:
            pass
    if base not in taken:
        return base, False
    n = 2
    while "%s%d" % (base, n) in taken:
        n += 1
    return "%s%d" % (base, n), True


@bp.route("/api/username_suggest")
def api_username_suggest():
    """S222 SECTIONS -- a free username for this name. Read only."""
    u, err = _require("checker")
    if err:
        return err
    name = (request.args.get("name") or "").strip()
    wanted = (request.args.get("want") or "").strip()
    con = _db()
    ensure_schema(con)
    user, bumped = free_username(con, name, wanted)
    return jsonify(ok=True, username=user, suffixed=bumped,
                   base=default_username(name))


@bp.route("/api/employment/add", methods=["POST"])
def api_employment_add():
    """S222 SECTIONS -- add a kind of employment without a deploy. Owner only."""
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    kind = (b.get("kind") or "").strip().upper()
    if not kind or not kind.replace("_", "").replace("-", "").isalnum():
        return jsonify(ok=False, error="bad_kind",
                       message="A kind is one word, letters and digits."), 400
    con = _db()
    ensure_schema(con)
    kinds = employment_kinds(con)
    if kind in kinds:
        return jsonify(ok=True, employment=kinds, added=False,
                       message="%s is already there." % kind)
    kinds.append(kind)
    try:
        con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    ("joiner.employment_kinds", ",".join(kinds),
                     "S222 -- kinds of employment offered on the joiner form. Blank or "
                     "deleted falls back to the code's own list."))
    except Exception:
        con.execute("UPDATE setting SET value=? WHERE key=?",
                    (",".join(kinds), "joiner.employment_kinds"))
    con.commit()
    return jsonify(ok=True, employment=kinds, added=True,
                   message="%s added." % kind)


@bp.route("/api/authorities")
def api_authorities():
'''


# ---- B: the payload itself -------------------------------------------------
B_OLD = '''    return jsonify(ok=True,
                   authorities=[{"key": k, "label": AUTHORITIES[k]}
                                for k in sorted(AUTHORITIES)],
                   employment=list(EMPLOYMENT),
                   default_employment=EMPLOYMENT[0])
'''

B_NEW = '''    con = _db()
    ensure_schema(con)
    kinds = employment_kinds(con)
    return jsonify(ok=True,
                   authorities=[{"key": k, "label": AUTHORITIES[k],
                                 "group": AUTHORITY_GROUP.get(k, "other")}
                                for k in sorted(AUTHORITIES)],
                   groups=GROUPS,
                   jobs=job_list(con),
                   employment=kinds,
                   default_employment=kinds[0] if kinds else EMPLOYMENT[0])
'''


# ---- C: /api/open validates against the settings list, not the tuple --------
C_OLD = '''    emp = (b.get("employment") or "FULLTIME").strip().upper()
    if emp not in EMPLOYMENT:
        return jsonify(ok=False, error="bad_employment",
                       message="employment is one of: %s" % ", ".join(EMPLOYMENT)), 400
'''

C_NEW = '''    kinds = employment_kinds(con)                       # S222 SECTIONS
    emp = (b.get("employment") or (kinds[0] if kinds else "FULLTIME")).strip().upper()
    if emp not in kinds:
        return jsonify(ok=False, error="bad_employment",
                       message="employment is one of: %s" % ", ".join(kinds)), 400
'''


PAIRS = [("A", A_OLD, A_NEW), ("B", B_OLD, B_NEW), ("C", C_OLD, C_NEW)]


def main():
    src = open(TARGET, encoding="utf-8").read()
    if MARK in src:
        print("already patched -- nothing to do")
        return 0
    before = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("current pin  %s" % before)
    if before != EXPECT_FROM:
        raise SystemExit("REFUSED: this file is %s, not the %s this kit was built against. "
                         "NOTHING was changed." % (before, EXPECT_FROM))
    for nm, old, _new in PAIRS:
        n = src.count(old)
        if n != 1:
            raise SystemExit("REFUSED: anchor %s matches %d times (need exactly 1). "
                             "NOTHING was changed." % (nm, n))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    bak = TARGET + ".bak_S222_sections_" + stamp
    shutil.copyfile(TARGET, bak)
    out = src
    for _nm, old, new in PAIRS:
        out = out.replace(old, new, 1)
    open(TARGET, "w", encoding="utf-8").write(out)
    try:
        compile(out, TARGET, "exec")
    except SyntaxError as ex:
        shutil.copyfile(bak, TARGET)
        raise SystemExit("REFUSED: the result does not compile (%s). RESTORED from %s."
                         % (ex, bak))
    pin = hashlib.md5(open(TARGET, "rb").read()).hexdigest()
    print("patched  %s" % TARGET)
    print("backup   %s" % bak)
    print("NEW PIN  %s   <-- this is the line the close records (A0: never from memory)" % pin)
    return 0


if __name__ == "__main__":
    sys.exit(main())
