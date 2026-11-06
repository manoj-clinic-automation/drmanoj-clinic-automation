#!/usr/bin/env python3
"""make_s733.py -- kit S733_EXIT_CODE_GUARD (session 394, the parent, 06-Nov-2026) . F-1147

Builds the new /root/finance/joiner_app.py from the LIVE bytes (6305b05d) by counted edits:
each anchor must occur exactly once, or nothing is written.

    python make_s733.py <live joiner_app.py> <out file> [--expect <md5 of the result>]

WHAT CHANGES (only the exit's machine code; joining is untouched)
  1. EXIT_WHY gains BIOMETRIC_REMOVED: what the tick does, in words on the page.
  2. helpers after retire_emp_code(): _norm_name(), _digits(), code_for_person() -- the ONE
     LIVE code the register ties to a name (exact name; never a first name, never a login)
     -- and code_owner_clash().
  3. /api/open, kind EXIT: the code is taken from the body (digits) or found by
     code_for_person() and written on the exit record.
  4. /api/step BIOMETRIC_REMOVED: the code is the typed one, else the record's, else found;
     none -> REFUSED (the step is not ticked); a typed code that differs from the record's,
     or ANY code the register gives to another person -> REFUSED; a code not on the register is
     entered there first; a code already retired KEEPS its date (S725 retired 20 on
     2026-09-30); 'last_day' (yyyy-mm-dd, not in the future) is the retirement date, else
     today. The record carries the code it retired.
  5. /api/healthz says kit S733.
"""
import hashlib
import sys

EDITS = []


def edit(old, new):
    EDITS.append((old, new))


# 1 -- the page says what the tick does
edit('''EXIT_WHY = {
    "STAFF_MASTER":     ("Claude does this step:''',
     '''EXIT_WHY = {
    # S733 (F-1147): the tick retires the person's machine code; it is refused when no code
    # can be found, so an exit never leaves a code live.
    "BIOMETRIC_REMOVED": ("Delete the person's finger on the machine, then tick. The register "
                          "retires the person's Emp Code so it is never given to anybody again. "
                          "If no code can be found for this person the tick is refused -- tell "
                          "Claude the number the machine showed."),
    "STAFF_MASTER":     ("Claude does this step:''')

# 2 -- the helpers
edit('''def retire_emp_code(con, code, when=None):
    """Mark a code retired. The row stays for ever; that is the whole point."""
    con.execute("UPDATE emp_code SET retired_on=? WHERE code=?",
                (when or today(), int(code)))
    con.commit()
''',
     '''def retire_emp_code(con, code, when=None):
    """Mark a code retired. The row stays for ever; that is the whole point."""
    con.execute("UPDATE emp_code SET retired_on=? WHERE code=?",
                (when or today(), int(code)))
    con.commit()


# ---- S733 EXIT CODE GUARD (F-1147, 06-Nov-2026) ------------------------------
# An exit opened without a code used to tick BIOMETRIC_REMOVED and retire nothing: the
# leaver's code stayed live (staff 20, S725 had to retire it by hand). The exit now finds
# the code when it is opened, and the tick is refused when there is still none.
def _norm_name(s):
    return " ".join(str(s or "").split()).lower()


def _digits(s):
    """Plain ASCII digits only -- str.isdigit() also accepts characters int() refuses."""
    s = str(s or "").strip()
    return s if (s and s.isascii() and s.isdigit()) else ""


def code_for_person(con, person):
    """The ONE LIVE machine code the register ties to `person` by exact name, or None.

    Exact name only (case and spaces aside), NEVER a first name and never a login:
    'Arjun' (code 20, left) and 'Arjun Dev' (login 'arjun', perhaps) are two people.
    Only codes still live on the code register count -- a retired code is never 'found',
    so a tick can never pass on it while another code of the same person stays live.
    The candidates: the register's live rows of that name, and the codes of joining
    records of that name that the register gives, live, to that same name. Two different codes = None
    (ambiguous): the tick is refused and asks, never guesses."""
    want = _norm_name(person)
    if not want:
        return None
    live = {int(_v(r, "code", 0)): _norm_name(_v(r, "person", 1))
            for r in con.execute("SELECT code, person FROM emp_code WHERE retired_on IS NULL")}
    found = {c for c, p in live.items() if p == want}
    for r in con.execute("SELECT person, emp_code FROM joiner WHERE kind='JOIN'"):
        c = _digits(_v(r, "emp_code", 1))
        if c and _norm_name(_v(r, "person", 0)) == want and live.get(int(c)) == want:
            found.add(int(c))
    return found.pop() if len(found) == 1 else None


def code_owner_clash(con, code, person):
    """The register's name for `code` when it is SOMEBODY ELSE's, else None."""
    r = con.execute("SELECT person FROM emp_code WHERE code=?", (int(code),)).fetchone()
    if r and _norm_name(_v(r, "person", 0)) != _norm_name(person):
        return _v(r, "person", 0)
    return None
# ---- end S733 ----------------------------------------------------------------
''')

# 3a -- /api/open: a typed code must be digits
edit('''    ref = next_ref(con, kind)
    cur = con.execute(
        "INSERT INTO joiner (ref,kind,person,role,employment,authorities,username,"''',
     '''    xcode = None                                        # S733 (F-1147): an exit's code
    if kind == "EXIT":
        raw = str(b.get("emp_code") or "").strip()
        if raw and not _digits(raw):
            return jsonify(ok=False, error="bad_emp_code",
                           message="The Emp Code is the number the device shows, digits "
                                   "only."), 400
        if raw and code_owner_clash(con, raw, person):
            return jsonify(ok=False, error="code_other_person",
                           message="Code %d belongs to %s on the register, not %s."
                                   % (int(raw), code_owner_clash(con, raw, person), person)), 409
        xcode = str(int(raw)) if raw else (str(code_for_person(con, person) or "") or None)
    ref = next_ref(con, kind)
    cur = con.execute(
        "INSERT INTO joiner (ref,kind,person,role,employment,authorities,username,"''')

# 3b -- /api/open: the exit record carries the code
edit('''    jid = cur.lastrowid
    con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                "VALUES (?,?,?,?,?)", (jid, "DECIDED", today(), who,''',
     '''    jid = cur.lastrowid
    if xcode:                                           # S733 (F-1147)
        con.execute("UPDATE joiner SET emp_code=? WHERE id=?", (xcode, jid))
    con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                "VALUES (?,?,?,?,?)", (jid, "DECIDED", today(), who,''')

# 3c -- /api/open: say which code the exit found
edit('''    out = {"ok": True, "ref": ref, "kind": kind, "person": person,
           "steps": list(steps_for(kind))}
''',
     '''    out = {"ok": True, "ref": ref, "kind": kind, "person": person,
           "steps": list(steps_for(kind))}
    if kind == "EXIT":                                  # S733 (F-1147)
        out["emp_code"] = xcode
''')

# 4 -- BIOMETRIC_REMOVED
edit('''    if step == "BIOMETRIC_REMOVED":
        r2 = con.execute("SELECT emp_code FROM joiner WHERE id=?", (jid,)).fetchone()
        c2 = _v(r2, "emp_code", 0)
        if c2:
            # retired, never deleted -- the row is what stops the code coming back
            retire_emp_code(con, c2)
''',
     '''    if step == "BIOMETRIC_REMOVED":
        # S733 (F-1147): never ticked while the leaver's code stays live. The code is the
        # typed one, else the record's, else the one the register ties to this name.
        r2 = con.execute("SELECT emp_code, person FROM joiner WHERE id=?", (jid,)).fetchone()
        on_row = str(_v(r2, "emp_code", 0) or "").strip()
        xperson = _v(r2, "person", 1)
        typed = str(b.get("emp_code") or "").strip()
        if typed and not _digits(typed):
            return jsonify(ok=False, error="bad_emp_code", step=step,
                           message="The Emp Code is the number the device shows, digits "
                                   "only."), 400
        if on_row and not _digits(on_row):
            return jsonify(ok=False, error="bad_emp_code", step=step,
                           message="This exit carries '%s' as its Emp Code, which is not a "
                                   "number. Nothing was ticked -- tell Claude." % on_row), 409
        if typed and on_row and int(typed) != int(on_row):
            return jsonify(ok=False, error="code_mismatch", step=step,
                           message="This exit already carries Emp Code %s, not %s. Nothing "
                                   "was ticked." % (on_row, typed)), 409
        c2 = typed or on_row or str(code_for_person(con, xperson) or "")
        if not c2:
            return jsonify(ok=False, error="need_emp_code", step=step,
                           message="No Emp Code can be found for %s, so it cannot be retired "
                                   "and the step was not ticked. Tell Claude the number the "
                                   "machine showed for this person." % xperson), 409
        c2 = str(int(c2))
        reg = con.execute("SELECT person, retired_on FROM emp_code WHERE code=?",
                          (int(c2),)).fetchone()
        if reg and code_owner_clash(con, c2, xperson):
            # whatever the source -- typed, on the record or found -- a code is retired only
            # for the person the register gives it to
            return jsonify(ok=False, error="code_other_person", step=step,
                           message="Code %s belongs to %s on the register, not %s. Nothing "
                                   "was ticked." % (c2, _v(reg, "person", 0), xperson)), 409
        last = str(b.get("last_day") or "").strip()
        if last:
            try:
                ok_day = dt.date.fromisoformat(last) <= dt.date.today()
            except ValueError:
                ok_day = False
            if not ok_day:
                return jsonify(ok=False, error="bad_last_day", step=step,
                               message="The last working day is a date (yyyy-mm-dd), not in "
                                       "the future."), 400
        if not reg:
            # a code from before the register: entered now, so it counts and cannot return
            issue_emp_code(con, c2, xperson, source="exit",
                           note="S733: first entered at this person's exit")
        if not reg or not _v(reg, "retired_on", 1):
            # retired, never deleted -- the row is what stops the code coming back;
            # a code already retired keeps the date it was retired on
            retire_emp_code(con, c2, last or None)
        con.execute("UPDATE joiner SET emp_code=? WHERE id=?", (c2, jid))
        if typed:
            b["emp_code"] = c2                          # the record keeps the clean number
''')

# 5 -- the health line names the kit
edit('''    return jsonify(ok=True, open=len(p), overdue=sum(1 for x in p if x["overdue"]),
                   join_steps=list(JOIN_STEPS), exit_steps=list(EXIT_STEPS))''',
     '''    return jsonify(ok=True, open=len(p), overdue=sum(1 for x in p if x["overdue"]),
                   join_steps=list(JOIN_STEPS), exit_steps=list(EXIT_STEPS),
                   kit="S733")''')

FROM = "6305b05dccf0d915924c9f698eddc94e"


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    src, dst = argv[1], argv[2]
    expect = argv[argv.index("--expect") + 1] if "--expect" in argv else None
    raw = open(src, "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM:
        print("REFUSED: the input is not joiner_app.py %s" % FROM[:8])
        return 1
    text = raw.decode("utf-8")
    for i, (old, new) in enumerate(EDITS, 1):
        n = text.count(old)
        if n != 1:
            print("REFUSED: edit %d's anchor occurs %d times (must be once)" % (i, n))
            return 1
        text = text.replace(old, new, 1)
    out = text.encode("utf-8")
    got = hashlib.md5(out).hexdigest()
    if expect and not got.startswith(expect):
        print("REFUSED: the result is %s, expected %s" % (got, expect))
        return 1
    open(dst, "wb").write(out)
    print("BUILT %s (%d counted edits) md5 %s" % (dst, len(EDITS), got))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
