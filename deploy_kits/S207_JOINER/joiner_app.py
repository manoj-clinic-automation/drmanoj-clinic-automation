#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""joiner_app.py -- adding a person to the clinic's systems, and removing one.

WHAT THE ORDER IS FOR, AND WHY IT IS NOT ARBITRARY
    Read out of the code that already runs, not invented:

    * `build_staff_master.py` skips any roster row with no Emp Code --
      "no Emp Code -> not on the biometric device (salary-only)". A person
      without one never reaches staff_master.csv, so attendance cannot see
      them. That is CORRECT while the biometric is pending, and a silent hole
      if nobody is chasing it.
    * `staff_register.staff_for_user` maps a portal login to a staff row by
      `staff.username` first, and falls back to an unambiguous FIRST NAME. The
      fallback returns None when two people share a first name -- and None
      means no self page, with no error anywhere.
    * `build_staff_master.py` REFUSES rows whose `sunday_group` is not
      A/B/C/ARJ or whose `minutes_exempt` is not Y/N.

    So the roster row is the anchor and is created FIRST, the username is
    written onto it EXPLICITLY rather than left to the fallback, and the Emp
    Code is added to THAT SAME ROW when the biometric is finally captured --
    never as a new row, which would make one person two.

THE ONE STEP ALLOWED TO LAG
    BIOMETRIC. It needs the person physically present. Everything else can and
    should complete on day one, and the register keeps the biometric open and
    visible until it is done rather than letting the person quietly work
    uncovered.

Flask and the standard library only. No contact number is stored here (F-185).
"""
import datetime as dt
import io
import os

from flask import Blueprint, jsonify, request

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "joiner_schema.sql")

bp = Blueprint("joiner", __name__)

# Order matters. Each step's prerequisite is the step before it, except
# BIOMETRIC, which may be done at any point after ROSTER_ROW.
# S207.2, owner's flow: the two steps that used to fail silently are now
# engineered away rather than documented.
#
#   * LINK_USERNAME is gone. The username is DERIVED from the person's name, so
#     the portal login and the roster row cannot diverge -- there is nothing to
#     copy across and therefore nothing to forget.
#   * SCOPE_SET is gone as a separate step. The authorities are ticked at
#     DECIDED and applied with the account; they stay editable afterwards.
#
# Six steps, and only one of them can lag.
JOIN_STEPS = ("DECIDED", "ACCOUNT_CREATED", "CREDENTIALS_SENT",
              "FIRST_LOGIN", "BIOMETRIC", "STAFF_MASTER")
EXIT_STEPS = ("DECIDED", "PORTAL_DISABLED", "BIOMETRIC_REMOVED", "ROSTER_INACTIVE",
              "DUES_SETTLED", "ITEMS_RETURNED", "STAFF_MASTER")

LATE_OK = ("BIOMETRIC",)          # may be completed out of order
CHASE_AFTER_DAYS = 14             # a pending biometric is named after this

# "May lag" is not "may be skipped", and treating them as the same thing was a
# real bug the selftest caught: STAFF_MASTER was signed off while the Emp Code
# was still missing -- which is the exact hole this register exists to close,
# since build_staff_master.py would have skipped the row and the person would
# have been marked fully added while remaining invisible to attendance.
# So a late-ok step still has hard dependants, listed here.
HARD_REQUIRES = {"STAFF_MASTER": ("BIOMETRIC",)}

STEP_LABEL = {
    "DECIDED":          "name, role and authorities ticked",
    "ACCOUNT_CREATED":  "roster row and portal login created together",
    "CREDENTIALS_SENT": "WhatsApp sent -- link, user id and password",
    "FIRST_LOGIN":      "signed in once",
    "BIOMETRIC":        "enrolled on the device, Emp Code into the SAME row",
    "STAFF_MASTER":     "staff master rebuilt and the person appears",
    "PORTAL_DISABLED":  "portal login disabled",
    "BIOMETRIC_REMOVED": "removed from the biometric device",
    "ROSTER_INACTIVE":  "roster row marked inactive",
    "DUES_SETTLED":     "advances and dues settled",
    "ITEMS_RETURNED":   "dress, I-card and keys returned",
}

STEP_WHY = {
    "ACCOUNT_CREATED": ("The roster row is the anchor and carries the username, so the "
                        "portal login cannot drift from it. sunday_group must be A, B, "
                        "C or ARJ and minutes_exempt Y or N, or the staff-master "
                        "rebuild refuses the row."),
    "BIOMETRIC":       ("The Emp Code goes into the row that already exists. A second "
                        "row makes one person two, in attendance and in salary."),
}

EMPLOYMENT = ("FULLTIME", "PARTTIME", "BIWEEKLY")

# What a person may be given. Ticked at DECIDED, applied with the account, and
# editable afterwards -- the owner's flow, not a free-text field nobody audits.
AUTHORITIES = {
    "self":            "own attendance and month grid (no money)",
    "stock_count":     "counting stock",
    "expiry_check":    "the expiry list",
    "purchase_order":  "raising purchase orders",
    "purchase_entry":  "entering purchase bills",
    "returns":         "booking and moving purchase returns",
    "salt_fix":        "salt corrections in Marg",
    "reception":       "reception desk",
}


def default_username(name):
    """First name, lower case. The owner's convention, and the reason
    LINK_USERNAME no longer exists: derived, so it cannot be mistyped."""
    first = (name or "").strip().split()[0] if (name or "").strip() else ""
    return "".join(ch for ch in first.lower() if ch.isalnum())


def default_password(name):
    """First name + 1234, lower case. A FIRST password, not a permanent one --
    see force_change below."""
    u = default_username(name)
    return (u + "1234") if u else ""

_db = None
_require = None


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def today():
    return dt.date.today().isoformat()


def ensure_schema(con):
    with io.open(SCHEMA, "r", encoding="utf-8") as fh:
        con.executescript(fh.read())
    con.commit()


def init(app, db_getter, require_fn, url_prefix="/joiner"):
    global _db, _require
    _db, _require = db_getter, require_fn
    app.register_blueprint(bp, url_prefix=url_prefix)
    return bp


def _v(row, key, idx):
    return row[key] if hasattr(row, "keys") else row[idx]


def steps_for(kind):
    return EXIT_STEPS if kind == "EXIT" else JOIN_STEPS


def known_codes(con):
    """Every code this register has ever seen, live or retired."""
    return {int(_v(r, "code", 0)) for r in con.execute("SELECT code FROM emp_code")}


def next_emp_code(con, also_seen=()):
    """The next code to issue: one above the HIGHEST EVER SEEN, never a gap.

    THE RULE IS NEVER REUSE, AND IT IS NOT A PREFERENCE
        punches.csv is append-only and keyed on (user_id, datetime). It holds
        every punch ever taken, including people who left years ago. The name
        behind a user_id lives only in staff_master.csv, which is rebuilt from
        the roster sheet and holds only rows that still have an Emp Code.

        So a leaver's punches stay under a code with no name. Reissue that code
        and every historical punch under it becomes the new person's -- in
        attendance, in the month report, in salary -- silently.

        Filling a gap is therefore exactly the wrong instinct. Codes only ever
        go up. `also_seen` is where the high-water mark from punches.csv and
        the roster is passed in, so a code used before this register existed
        still counts.
    """
    seen = known_codes(con) | {int(x) for x in also_seen if str(x).strip().isdigit()}
    return (max(seen) + 1) if seen else 1


def issue_emp_code(con, code, person, source="manual", note=None):
    """Record a code against a person. Refuses a code already on the register."""
    code = int(code)
    r = con.execute("SELECT person, retired_on FROM emp_code WHERE code=?", (code,)).fetchone()
    if r:
        who, ret = _v(r, "person", 0), _v(r, "retired_on", 1)
        return False, ("Code %d already belongs to %s%s. A code is never reissued -- "
                       "every punch ever taken under it would become the new "
                       "person's." % (code, who, " (left %s)" % ret if ret else ""))
    con.execute("INSERT INTO emp_code (code,person,issued_on,source,note) "
                "VALUES (?,?,?,?,?)", (code, person, today(), source, note))
    con.commit()
    return True, ""


def retire_emp_code(con, code, when=None):
    """Mark a code retired. The row stays for ever; that is the whole point."""
    con.execute("UPDATE emp_code SET retired_on=? WHERE code=?",
                (when or today(), int(code)))
    con.commit()


def next_ref(con, kind, when=None):
    d = dt.date.fromisoformat(when) if when else dt.date.today()
    fy = d.year if d.month >= 4 else d.year - 1
    pre = "%s-%d-" % ("EXIT" if kind == "EXIT" else "JOIN", fy)
    r = con.execute("SELECT ref FROM joiner WHERE ref LIKE ? ORDER BY ref DESC LIMIT 1",
                    (pre + "%",)).fetchone()
    n = (int(_v(r, "ref", 0).rsplit("-", 1)[1]) + 1) if r else 1
    return "%s%04d" % (pre, n)


def done_steps(con, jid):
    return {_v(r, "step", 0) for r in con.execute(
        "SELECT step FROM joiner_step WHERE joiner_id=? AND done_on IS NOT NULL",
        (jid,)).fetchall()}


def blocked_by(kind, done, step):
    """(ok, why-not). Prerequisites are every earlier step except the late-ok ones."""
    order = steps_for(kind)
    if step not in order:
        return False, "'%s' is not a step of a %s." % (step, kind.lower())
    if step in done:
        return False, "Already done."
    i = order.index(step)
    missing = [s for s in order[:i] if s not in done and s not in LATE_OK]
    if not missing:
        # a late-ok step may be out of order, but never absent for a step that
        # genuinely cannot be true without it
        missing = [s for s in HARD_REQUIRES.get(step, ()) if s not in done]
    if missing:
        return False, ("Do '%s' first. %s" % (STEP_LABEL[missing[0]],
                                              STEP_WHY.get(missing[0], ""))).strip()
    return True, ""


def pending(con):
    """Open records, and which step each is waiting on."""
    out = []
    for r in con.execute("SELECT id,ref,kind,person,role,status,opened_on,username,emp_code "
                         "FROM joiner WHERE status != 'COMPLETE' ORDER BY opened_on, ref"):
        jid, kind = _v(r, "id", 0), _v(r, "kind", 2)
        done = done_steps(con, jid)
        order = steps_for(kind)
        waiting = [s for s in order if s not in done]
        age = (dt.date.today() - dt.date.fromisoformat(_v(r, "opened_on", 6))).days
        out.append({
            "ref": _v(r, "ref", 1), "kind": kind, "person": _v(r, "person", 3),
            "role": _v(r, "role", 4), "opened_on": _v(r, "opened_on", 6),
            "age_days": age,
            "username": _v(r, "username", 7), "emp_code": _v(r, "emp_code", 8),
            "done": [s for s in order if s in done],
            "waiting_on": waiting[0] if waiting else None,
            "waiting_label": STEP_LABEL.get(waiting[0]) if waiting else None,
            "still_to_do": waiting,
            "overdue": age >= CHASE_AFTER_DAYS and bool(waiting),
        })
    return out


# ------------------------------------------------------------------- routes
@bp.route("/api/healthz")
def healthz():
    con = _db()
    ensure_schema(con)
    p = pending(con)
    return jsonify(ok=True, open=len(p), overdue=sum(1 for x in p if x["overdue"]),
                   join_steps=list(JOIN_STEPS), exit_steps=list(EXIT_STEPS))


@bp.route("/api/open", methods=["POST"])
def api_open():
    """Start a joining or a leaving.

    Body: {"person":"Amir","role":"purchase","kind":"JOIN","opened_by":"Dr Manoj"}
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    person = (b.get("person") or "").strip()
    who = (b.get("opened_by") or "").strip()
    kind = (b.get("kind") or "JOIN").strip().upper()
    if kind not in ("JOIN", "EXIT"):
        return jsonify(ok=False, error="bad_kind", message="kind is JOIN or EXIT."), 400
    if not person or not who:
        return jsonify(ok=False, error="bad_request",
                       message="Both the person's name and who is opening this are "
                               "required."), 400
    con = _db()
    ensure_schema(con)
    dup = con.execute("SELECT ref FROM joiner WHERE kind=? AND LOWER(person)=? "
                      "AND status!='COMPLETE'", (kind, person.lower())).fetchone()
    if dup:
        return jsonify(ok=False, error="already_open",
                       message="%s is already open for %s. Continue that one rather "
                               "than starting a second." % (_v(dup, "ref", 0), person)), 409
    emp = (b.get("employment") or "FULLTIME").strip().upper()
    if emp not in EMPLOYMENT:
        return jsonify(ok=False, error="bad_employment",
                       message="employment is one of: %s" % ", ".join(EMPLOYMENT)), 400
    auth = [a for a in (b.get("authorities") or []) if a in AUTHORITIES]
    bad = [a for a in (b.get("authorities") or []) if a not in AUTHORITIES]
    if bad:
        return jsonify(ok=False, error="unknown_authority",
                       message="Not a thing anyone can be given: %s" % ", ".join(bad),
                       known=sorted(AUTHORITIES)), 400
    ref = next_ref(con, kind)
    cur = con.execute(
        "INSERT INTO joiner (ref,kind,person,role,employment,authorities,username,"
        "status,opened_on,opened_by,created_at,updated_at) "
        "VALUES (?,?,?,?,?,?,?,'DECIDED',?,?,?,?)",
        (ref, kind, person, (b.get("role") or "").strip() or None, emp,
         ",".join(auth) or None,
         (b.get("username") or default_username(person)) if kind == "JOIN" else None,
         today(), who, now_iso(), now_iso()))
    jid = cur.lastrowid
    con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                "VALUES (?,?,?,?,?)", (jid, "DECIDED", today(), who,
                                       (b.get("detail") or "").strip() or None))
    con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) "
                "VALUES (?,?,?,?,?)", (jid, now_iso(), u, "OPENED",
                                       "%s for %s" % (kind, person)))
    con.commit()
    out = {"ok": True, "ref": ref, "kind": kind, "person": person,
           "steps": list(steps_for(kind))}
    if kind == "JOIN":
        u = (b.get("username") or default_username(person))
        taken = con.execute("SELECT person FROM joiner WHERE LOWER(COALESCE(username,''))=? "
                            "AND ref!=?", (u.lower(), ref)).fetchone()
        out["username"] = u
        out["password"] = default_password(person)
        out["employment"] = emp
        out["authorities"] = auth
        out["force_change_at_first_login"] = True
        if taken:
            out["username_warning"] = (
                "%s already uses '%s'. Two people cannot share a login -- give this "
                "one a different username before creating the account."
                % (_v(taken, "person", 0), u))
    return jsonify(**out)


@bp.route("/api/step", methods=["POST"])
def api_step():
    """Tick one step, naming who did it.

    Body: {"ref":"JOIN-2026-0001","step":"PORTAL_USER","by":"Dr Manoj",
           "username":"amir","emp_code":"41","detail":"..."}
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    step = (b.get("step") or "").strip().upper()
    who = (b.get("by") or "").strip()
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id,kind,person FROM joiner WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_record",
                       message="No record called %s." % (ref or "(blank)")), 404
    jid, kind = _v(r, "id", 0), _v(r, "kind", 1)
    if not who:
        return jsonify(ok=False, error="no_person",
                       message="Who did this? A name is required on every step."), 400
    ok, why = blocked_by(kind, done_steps(con, jid), step)
    if not ok:
        return jsonify(ok=False, error="blocked", message=why, step=step), 409

    # The Emp Code is captured on the step that produces it, and it goes onto
    # the permanent register in the same action -- so "which codes have been
    # used" is never a question anybody has to answer from memory.
    if step == "BIOMETRIC":
        code = str(b.get("emp_code") or "").strip()
        if not code:
            return jsonify(ok=False, error="need_emp_code",
                           message="Record the Emp Code from the device. Without it the "
                                   "roster row stays invisible to the staff master."), 400
        if not code.isdigit():
            return jsonify(ok=False, error="bad_emp_code",
                           message="The Emp Code is the number the device shows, digits "
                                   "only."), 400
        person = con.execute("SELECT person FROM joiner WHERE id=?", (jid,)).fetchone()
        ok2, why2 = issue_emp_code(con, code, _v(person, "person", 0), source="joiner")
        if not ok2:
            return jsonify(ok=False, error="code_in_use", message=why2,
                           suggested=next_emp_code(con)), 409

    if step == "BIOMETRIC_REMOVED":
        r2 = con.execute("SELECT emp_code FROM joiner WHERE id=?", (jid,)).fetchone()
        c2 = _v(r2, "emp_code", 0)
        if c2:
            # retired, never deleted -- the row is what stops the code coming back
            retire_emp_code(con, c2)

    con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                "VALUES (?,?,?,?,?) ON CONFLICT(joiner_id,step) DO UPDATE SET "
                "done_on=excluded.done_on, done_by=excluded.done_by, detail=excluded.detail",
                (jid, step, today(), who, (b.get("detail") or "").strip() or None))
    sets, args = ["updated_at=?", "status=?"], [now_iso(), step]
    if (b.get("username") or "").strip():
        sets.append("username=?")
        args.append(b["username"].strip())
    if (b.get("emp_code") or "").strip():
        sets.append("emp_code=?")
        args.append(str(b["emp_code"]).strip())
    if (b.get("roster_row") or "").strip():
        sets.append("roster_row=?")
        args.append(b["roster_row"].strip())
    args.append(jid)
    con.execute("UPDATE joiner SET %s WHERE id=?" % ",".join(sets), args)
    con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) "
                "VALUES (?,?,?,?,?)", (jid, now_iso(), u, step, who))

    done = done_steps(con, jid) | {step}
    complete = all(s in done for s in steps_for(kind))
    if complete:
        con.execute("UPDATE joiner SET status='COMPLETE', closed_on=?, closed_by=? "
                    "WHERE id=?", (today(), who, jid))
    con.commit()
    remaining = [s for s in steps_for(kind) if s not in done]
    return jsonify(ok=True, ref=ref, step=step, label=STEP_LABEL.get(step, step),
                   complete=complete, still_to_do=remaining,
                   next=(remaining[0] if remaining else None),
                   next_label=(STEP_LABEL.get(remaining[0]) if remaining else None))


@bp.route("/api/pending")
def api_pending():
    """Everyone part-way in or part-way out, and the step each is waiting on."""
    con = _db()
    ensure_schema(con)
    p = pending(con)
    return jsonify(ok=True, count=len(p), overdue=sum(1 for x in p if x["overdue"]),
                   records=p)


@bp.route("/api/record")
def api_record():
    """One record, every step, with who did it and when."""
    con = _db()
    ensure_schema(con)
    ref = (request.args.get("ref") or "").strip()
    r = con.execute("SELECT id,kind,person,role,status,username,emp_code,opened_on "
                    "FROM joiner WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_record",
                       message="No record called %s." % (ref or "(blank)")), 404
    jid, kind = _v(r, "id", 0), _v(r, "kind", 1)
    got = {_v(x, "step", 0): (_v(x, "done_on", 1), _v(x, "done_by", 2), _v(x, "detail", 3))
           for x in con.execute("SELECT step,done_on,done_by,detail FROM joiner_step "
                                "WHERE joiner_id=?", (jid,)).fetchall()}
    steps = [{"step": s, "label": STEP_LABEL.get(s, s), "why": STEP_WHY.get(s),
              "done_on": got.get(s, (None, None, None))[0],
              "done_by": got.get(s, (None, None, None))[1],
              "detail": got.get(s, (None, None, None))[2],
              "late_ok": s in LATE_OK}
             for s in steps_for(kind)]
    return jsonify(ok=True, ref=ref, kind=kind, person=_v(r, "person", 2),
                   role=_v(r, "role", 3), status=_v(r, "status", 4),
                   username=_v(r, "username", 5), emp_code=_v(r, "emp_code", 6),
                   opened_on=_v(r, "opened_on", 7), steps=steps)


@bp.route("/api/next_code")
def api_next_code():
    """What Emp Code to give the next person, and why that one.

    Pass `seen` as a comma-separated list of codes already known from
    punches.csv and the roster, so codes issued before this register existed
    still count toward the high-water mark.
    """
    con = _db()
    ensure_schema(con)
    seen = [x for x in (request.args.get("seen") or "").replace(" ", "").split(",") if x]
    nxt = next_emp_code(con, seen)
    have = sorted(known_codes(con))
    return jsonify(ok=True, next_code=nxt, on_register=len(have),
                   highest_known=(max(have + [int(x) for x in seen if x.isdigit()])
                                  if (have or seen) else None),
                   rule=("One above the highest ever seen. Gaps are left alone: a gap "
                         "is a code somebody used, and punches.csv still holds their "
                         "punches under it."))


@bp.route("/api/codes")
def api_codes():
    """The permanent code register -- live and retired, never deleted."""
    con = _db()
    ensure_schema(con)
    rows = [{"code": _v(r, "code", 0), "person": _v(r, "person", 1),
             "issued_on": _v(r, "issued_on", 2), "retired_on": _v(r, "retired_on", 3),
             "source": _v(r, "source", 4)}
            for r in con.execute("SELECT code,person,issued_on,retired_on,source "
                                 "FROM emp_code ORDER BY code")]
    return jsonify(ok=True, count=len(rows), live=sum(1 for r in rows if not r["retired_on"]),
                   retired=sum(1 for r in rows if r["retired_on"]), codes=rows)


@bp.route("/api/seed_codes", methods=["POST"])
def api_seed_codes():
    """Load codes already in use, once, from the roster and punches.csv.

    Body: {"codes":[{"code":12,"person":"Darpan","retired":false}, ...]}

    THE ONE THING TO DO BEFORE ANYBODY ELSE IS ENROLLED. Until the codes that
    already exist are on the register, "the next code" is a guess -- and a guess
    that lands on a departed person's number silently rewrites their history.
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    rows = b.get("codes") or []
    con = _db()
    ensure_schema(con)
    added, skipped = 0, []
    for c in rows:
        code = str(c.get("code") or "").strip()
        person = (c.get("person") or "").strip() or "(name not recorded)"
        if not code.isdigit():
            continue
        ok2, why2 = issue_emp_code(con, code, person, source=b.get("source") or "seed",
                                   note=c.get("note"))
        if ok2:
            if c.get("retired"):
                retire_emp_code(con, code, c.get("retired_on"))
            added += 1
        else:
            skipped.append({"code": int(code), "why": why2})
    return jsonify(ok=True, added=added, already_known=skipped,
                   next_code=next_emp_code(con))


@bp.route("/api/message")
def api_message():
    """The WhatsApp to send a new joiner. Composed, never sent from here.

    The password is DERIVED, not stored -- nothing in this database holds it.
    """
    con = _db()
    ensure_schema(con)
    ref = (request.args.get("ref") or "").strip()
    link = request.args.get("link") or "https://followup.dr-manoj.in/portal"
    r = con.execute("SELECT person,username FROM joiner WHERE ref=?", (ref,)).fetchone()
    if not r:
        return jsonify(ok=False, error="no_such_record",
                       message="No record called %s." % (ref or "(blank)")), 404
    person = _v(r, "person", 0)
    user = _v(r, "username", 1) or default_username(person)
    text = ("Namaste %s,\n\n"
            "Aapka clinic portal login ban gaya hai.\n\n"
            "Link : %s\n"
            "User : %s\n"
            "Password : %s\n\n"
            "Pehli baar login karke password badal lijiye.\n"
            "Koi dikkat ho to bataiye."
            % (person, link, user, default_password(person)))
    return jsonify(ok=True, ref=ref, person=person, username=user, text=text,
                   note="Password is derived, never stored. Change it at first login.")


# ---------------------------------------------------------------- passwords
# Owner's ruling, 28-Aug: "STAFF LEVEL FRIENDLY IS THE CRUX. FORGET PASSWORD
# ISSUES. MAKE IT SIMPLEST POSSIBLE."
#
# So: staff never manage a password at all. They forget it, they say so, and it
# is put back to the default from the owner's own page. One button.
#
# WHY NOT AN OTP TO THEIR MOBILE, WHICH WAS THE OTHER IDEA
#     It reads simpler than it is. It needs sending wired up and paid for, and
#     it then fails in exactly the situations where somebody is already stuck:
#     no balance, no signal, phone at home, number changed and nobody updated
#     it. Every one of those becomes a support call to the same person who
#     would have clicked reset. A button that always works beats a message that
#     usually does.
#
# WHAT ACTUALLY LIMITS THE DAMAGE, since the password stays guessable:
#     not password strength -- the scope. Salary stays doctor-only (F-31), a
#     staff login sees its own tiles and its own attendance without money, and
#     every reset is recorded here with who did it and when. That bound already
#     exists in the portal; this keeps it honest.

@bp.route("/api/reset_password", methods=["POST"])
def api_reset_password():
    """Put a person's password back to the default. Owner action, recorded.

    Body: {"person":"Amir","by":"Dr Manoj","reason":"forgot"}
    Returns the password to read out. Nothing is stored.
    """
    u, err = _require("checker")
    if err:
        return err
    b = request.get_json(silent=True) or {}
    person = (b.get("person") or "").strip()
    who = (b.get("by") or "").strip()
    if not person or not who:
        return jsonify(ok=False, error="bad_request",
                       message="The person's name and who is resetting it are both "
                               "required."), 400
    con = _db()
    ensure_schema(con)
    r = con.execute("SELECT id,username FROM joiner WHERE kind='JOIN' AND LOWER(person)=? "
                    "ORDER BY id DESC LIMIT 1", (person.lower(),)).fetchone()
    user = (_v(r, "username", 1) if r else None) or default_username(person)
    if r:
        con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) "
                    "VALUES (?,?,?,?,?)",
                    (_v(r, "id", 0), now_iso(), u, "PASSWORD_RESET",
                     "%s -- %s" % (who, (b.get("reason") or "no reason given"))))
        con.commit()
    return jsonify(ok=True, person=person, username=user,
                   password=default_password(person),
                   recorded=bool(r),
                   message=("Set the portal password to this, then read it out. "
                            "It is not stored anywhere."),
                   text=("%s ka password reset ho gaya hai.\n"
                         "User : %s\nPassword : %s" % (person, user, default_password(person))))


@bp.route("/api/resets")
def api_resets():
    """Who has needed a reset, and how often. A person resetting weekly is a
    sign the flow is confusing them, not that they are careless."""
    con = _db()
    ensure_schema(con)
    rows = con.execute(
        "SELECT j.person, COUNT(*) n, MAX(e.at) last FROM joiner_event e "
        "JOIN joiner j ON j.id=e.joiner_id WHERE e.kind='PASSWORD_RESET' "
        "GROUP BY j.person ORDER BY n DESC").fetchall()
    return jsonify(ok=True, people=[{"person": _v(r, "person", 0),
                                     "resets": _v(r, "n", 1),
                                     "last": _v(r, "last", 2)} for r in rows])


# ------------------------------------------------------------ staff master
STAFF_MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")


@bp.route("/api/staff_master")
def api_staff_master():
    """The staff master as it stands, so the owner can check it after a join.

    ⚠ GATED TO THE OWNER. staff_master.csv CARRIES BASE SALARIES, and F-31 says
    salary is doctor-only. This route must never be opened to the manager role,
    however convenient that would be.
    """
    u, err = _require("checker")
    if err:
        return err
    if not os.path.exists(STAFF_MASTER):
        return jsonify(ok=False, error="not_found",
                       message="staff_master.csv is not at %s. Set ATT_STAFF_MASTER."
                               % STAFF_MASTER), 404
    import csv
    with io.open(STAFF_MASTER, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    codes = sorted(int(r["user_id"]) for r in rows if str(r.get("user_id", "")).isdigit())
    con = _db()
    ensure_schema(con)
    on_register = known_codes(con)
    missing = [c for c in codes if c not in on_register]
    return jsonify(
        ok=True, path=STAFF_MASTER, people=len(rows),
        highest_code=(max(codes) if codes else None),
        next_code=next_emp_code(con, codes),
        not_yet_on_register=missing,
        warning=(None if not missing else
                 "%d code(s) in staff_master are not on the code register yet. "
                 "Seed them before enrolling anybody, or the next code is a guess."
                 % len(missing)),
        rows=[{k: v for k, v in r.items() if k != "base_salary"} for r in rows],
        note="Base salary withheld from this view even for the owner -- read it in "
             "the sheet, not through an API that might later be opened up.")
