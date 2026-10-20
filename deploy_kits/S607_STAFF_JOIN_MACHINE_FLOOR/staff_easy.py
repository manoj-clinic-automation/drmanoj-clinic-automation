#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""staff_easy.py -- kit S606 (session S331, 20-Oct-2026): ADD STAFF in two touches.

THE OWNER, 20-Oct-2026, after the joining of Arjun Dev stopped at step 2 of the
old six-step ladder (/finance/staff):
    "I need such a flow which can be executed easily."
    "Few might not have whatsapp or smartphone occasionally, build this
     functionality, biometric new staff entry is also confusing for us."

WHAT WAS WRONG WITH THE LADDER (read from the live code and data, S331)
  * step 3 "WhatsApp sent" opened WhatsApp with NO number -- you hunt the contact;
  * step 4 "signed in once" asked for a tick nobody can know (the portal records
    no sign-ins -- S222 found the same);
  * step 6 "staff master" asked for a tick that no button made true: nothing on
    the page put the person into attendance or salary;
  * the attendance register keys a person on the MACHINE's number, so his row
    cannot exist before the machine has enrolled him -- the ladder said otherwise;
  * the username box took "arjun dev" (with a space) as typed.

THE NEW FLOW -- /finance/staff/new
  1. ONE FORM: name, mobile, what phone he has, job, full/part time, joining
     date, duty hours, Sunday duty, salary, offs. Save.
     The system makes a clean login (or none, if he has no phone).
  2. GIVE HIM HIS LOGIN, the way his phone allows: WhatsApp straight into HIS
     chat (his number, not a contact hunt) · SMS for a simple phone · a printed
     slip for a smartphone without WhatsApp · or nothing, if he has no phone
     (attendance then runs on the machine alone).
  3. THE MACHINE: enrol his finger the usual way, and ask him to press it once.
     The server sees the new number arrive from the machine and shows it:
     "New finger seen -- number 102 at 17:52. Is this Arjun Dev? [Yes]".
     Nobody reads a number off the machine or types it. One tap puts him into
     the attendance list (staff_master.csv) and the staff register (attendance
     and salary), and the joining closes by itself.

WHAT IT REUSES, UNEDITED
  joiner_app.py (S207/S222) is the register: its tables, its never-reuse code
  rule (emp_code), its step order (blocked_by), its default password. This file
  only drives it. The old page stays at /finance/staff as the fallback.

WHAT IT WRITES, AND WHERE
  finance.db       -- the joiner tables, through joiner_app's own rules. NO phone
                      number is ever written here (its schema's F-185 promise).
  staff_register.db-- its own new table joiner_pending (details + mobile, until
                      he is on the machine); then, ONCE, the new person's rows in
                      staff and staff_shift, for a machine number nobody has.
  staff_master.csv -- one appended row for him (backup first, atomic replace).
  the portal's user store -- his login (backup first, proved by signing in).

SALARY IS DOCTOR-ONLY (F-31): every route here is the owner's alone.

HEALS ITSELF (BUILD_NORM_v1 s1): every read of the list settles the open
joinings -- a login typed with a space or capitals is renamed to its clean
form while the joining is open; a step whose truth is measurable (in the
staff master and the register) is ticked when it becomes true.
"""
import csv
import datetime as dt
import io
import os
import re
import shutil
import sqlite3
import time

from flask import Blueprint, jsonify, request, send_file, Response

import joiner_app as J

KIT = "S607"
HERE = os.path.dirname(os.path.abspath(__file__))
SR_DB = os.environ.get("STAFF_EASY_SR_DB", "/root/staff_register/staff_register.db")
STAFF_MASTER = os.environ.get("ATT_STAFF_MASTER", "/root/staff_master.csv")
PUNCH_CSV = os.environ.get("ATT_PUNCH_CSV", "/root/punches.csv")
PORTAL_LINK = os.environ.get("STAFF_EASY_PORTAL_LINK", "https://followup.dr-manoj.in/portal")
OWNERS = {"manoj"}            # plus anyone whose portal role is doctor

bp = Blueprint("staffeasy", __name__)
_require = None

HANDOVER = {
    "whatsapp": "WhatsApp",
    "sms":      "SMS (simple phone)",
    "slip":     "printed slip (smartphone, no WhatsApp)",
    "none":     "no phone -- no login; attendance by the machine only",
}
SUNDAY = {
    "A": "1st and 3rd Sunday, full day",
    "B": "2nd and 4th Sunday, full day",
    "C": "Every Sunday, Sunday hours",
}
JOBS = ("Reception", "Clinic", "Pathology", "Pharmacy", "Purchase", "Cleaner")

PENDING_SQL = """
CREATE TABLE IF NOT EXISTS joiner_pending (
  ref            TEXT PRIMARY KEY,        -- the finance register's JOIN-2026-0002
  person         TEXT NOT NULL,
  mobile         TEXT,                    -- 10 digits; this store only (never finance.db)
  handover       TEXT NOT NULL DEFAULT 'whatsapp',
  department     TEXT,
  employment     TEXT,
  join_date      TEXT,
  wd_start       TEXT, wd_end TEXT,
  sunday_group   TEXT,
  sun_start      TEXT, sun_end TEXT,
  base_salary    INTEGER NOT NULL DEFAULT 0,
  allowed_offs   INTEGER NOT NULL DEFAULT 2,
  minutes_exempt INTEGER NOT NULL DEFAULT 0,
  emp_code       INTEGER,
  linked_on      TEXT,
  linked_by      TEXT,
  created_by     TEXT, created_at TEXT, updated_at TEXT
);
"""


# ---------------------------------------------------------------- plumbing
def init(app, require_fn):
    global _require
    _require = require_fn
    app.register_blueprint(bp)
    return bp


def _owner():
    """(user-name, error-response). The owner only -- salary is on these pages."""
    u, err = _require("checker")
    if err:
        return None, err
    name = (u.get("user") or "") if isinstance(u, dict) else str(u or "")
    role = (u.get("role") or "") if isinstance(u, dict) else ""
    if name.lower() not in OWNERS and role != "doctor":
        return None, (jsonify(ok=False, error="owner_only",
                              message="This page carries salaries; it is the doctor's own."), 403)
    return name or "owner", None


def _fin():
    con = J._db()
    J.ensure_schema(con)
    return con


def _sr():
    con = sqlite3.connect(SR_DB, timeout=15)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=15000")
    con.executescript(PENDING_SQL)
    return con


def _now():
    return dt.datetime.now().isoformat(timespec="seconds")


def _today():
    return dt.date.today().isoformat()


def _clean_mobile(s):
    d = re.sub(r"\D", "", s or "")
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    if len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d


def _hhmm(s, fallback=""):
    s = (s or "").strip()
    m = re.match(r"^(\d{1,2}):(\d{2})$", s)
    if not m:
        return fallback
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return fallback
    return "%02d:%02d" % (h, mi)


def _bad(msg, code=400, **kw):
    return jsonify(ok=False, message=msg, **kw), code


# ------------------------------------------------------------ the registers
def _jrow(con, ref):
    return con.execute("SELECT id,ref,kind,person,role,status,username,employment,"
                       "authorities,emp_code,opened_on FROM joiner WHERE ref=?",
                       (ref,)).fetchone()


def _steps(con, jid):
    out = {}
    for x in con.execute("SELECT step,done_on,done_by,detail FROM joiner_step "
                         "WHERE joiner_id=?", (jid,)).fetchall():
        out[J._v(x, "step", 0)] = {"on": J._v(x, "done_on", 1), "by": J._v(x, "done_by", 2),
                                   "detail": J._v(x, "detail", 3)}
    return out


def _tick(con, jid, step, who, detail, actor):
    """One step, by the register's own order rule -- exactly what api_step writes.
    Returns (ok, why). Never commits; the caller does."""
    kind = "JOIN"
    done = J.done_steps(con, jid)
    if step in done:
        return True, "already"
    ok, why = J.blocked_by(kind, done, step)
    if not ok:
        return False, why
    con.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                "VALUES (?,?,?,?,?) ON CONFLICT(joiner_id,step) DO UPDATE SET "
                "done_on=excluded.done_on, done_by=excluded.done_by, detail=excluded.detail",
                (jid, step, _today(), who, detail))
    con.execute("UPDATE joiner SET status=?, updated_at=? WHERE id=?", (step, _now(), jid))
    con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) VALUES (?,?,?,?,?)",
                (jid, _now(), actor, step, "%s -- %s (%s)" % (who, detail, KIT)))
    done = J.done_steps(con, jid) | {step}
    if all(s in done for s in J.JOIN_STEPS):
        con.execute("UPDATE joiner SET status='COMPLETE', closed_on=?, closed_by=? WHERE id=?",
                    (_today(), who, jid))
    return True, ""


def _event(con, jid, actor, kind, detail):
    con.execute("INSERT INTO joiner_event (joiner_id,at,actor,kind,detail) VALUES (?,?,?,?,?)",
                (jid, _now(), actor, kind, detail))


# ------------------------------------------------------------ staff master
def _master_rows():
    if not os.path.exists(STAFF_MASTER):
        return [], []
    with io.open(STAFF_MASTER, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh)
        return list(rd.fieldnames or []), list(rd)


def _master_codes():
    _h, rows = _master_rows()
    return {int(r["user_id"]) for r in rows if str(r.get("user_id", "")).strip().isdigit()}


def _master_first_names(exclude_code=None):
    _h, rows = _master_rows()
    out = set()
    for r in rows:
        if str(r.get("active", "Y")).strip().upper() not in ("Y", "1", "YES"):
            continue
        if exclude_code is not None and str(r.get("user_id")) == str(exclude_code):
            continue
        n = (r.get("name") or "").strip().split()
        if n:
            out.add(n[0].lower())
    return out


def _append_master(row):
    """Append one person to staff_master.csv: backup first, same columns, atomic."""
    head, rows = _master_rows()
    if not head:
        raise RuntimeError("staff_master.csv is missing or has no header (%s)" % STAFF_MASTER)
    if str(row["user_id"]) in {str(r.get("user_id")) for r in rows}:
        return "already"
    bak = "%s.bak_%s_%s" % (STAFF_MASTER, KIT, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copy2(STAFF_MASTER, bak)
    tmp = STAFF_MASTER + ".tmp_" + KIT
    with io.open(STAFF_MASTER, encoding="utf-8-sig", newline="") as fh:
        raw = fh.read()
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=head, extrasaction="ignore", lineterminator="\n")
    w.writerow({k: row.get(k, "") for k in head})
    if raw and not raw.endswith("\n"):
        raw += "\n"
    with io.open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(raw + buf.getvalue())
    st = os.stat(STAFF_MASTER)
    os.chmod(tmp, st.st_mode & 0o777)
    os.replace(tmp, STAFF_MASTER)
    return bak


# ------------------------------------------------------------ the machine
def _punches():
    """{code: [first, last, count]} for every machine number in punches.csv."""
    out = {}
    if not os.path.exists(PUNCH_CSV):
        return out
    with io.open(PUNCH_CSV, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            c = str(r.get("user_id") or "").strip()
            t = str(r.get("datetime") or "").strip()
            if not c.isdigit() or not t:
                continue
            c = int(c)
            x = out.get(c)
            if not x:
                out[c] = [t, t, 1]
            else:
                x[0] = min(x[0], t)
                x[1] = max(x[1], t)
                x[2] += 1
    return out


def _machine_view(con, since=None):
    """What the machine has sent that nobody owns yet, newest first.

    S607: only fingers pressed from the day before the joining was opened. The
    clinic's machine already carried test presses from its set-up day (07-Oct:
    number 2, and the retired 100) -- offered on a new joiner's page they invite
    a wrong "Yes"; number 2 is likely the owner's own administrator finger."""
    seen = _punches()
    master = _master_codes()
    reg = {}
    for r in con.execute("SELECT code,person,retired_on FROM emp_code"):
        reg[int(J._v(r, "code", 0))] = (J._v(r, "person", 1), J._v(r, "retired_on", 2))
    floor = (dt.date.today() - dt.timedelta(days=60)).isoformat()
    if since:
        try:
            floor = max(floor, (dt.date.fromisoformat(str(since)[:10]) - dt.timedelta(days=1)).isoformat())
        except ValueError:
            pass
    new, reused = [], []
    for code, (first, last, n) in seen.items():
        if last[:10] < floor:
            continue
        if code not in reg and code not in master:
            if first[:10] < floor:
                continue                      # an old unknown finger, not this joining's
            new.append({"code": code, "first": first, "last": last, "punches": n})
        elif code in reg and reg[code][1] and last[:10] > str(reg[code][1]):
            reused.append({"code": code, "last": last, "was": reg[code][0],
                           "left": reg[code][1]})
    new.sort(key=lambda x: x["first"], reverse=True)
    # the number to type is fixed BEFORE his finger arrives: a candidate's own
    # number must not push it up while the page is open
    cand = {x["code"] for x in new}
    nxt = J.next_emp_code(con, also_seen=[c for c in seen if c not in cand] + list(master))
    return new, reused, nxt


# ------------------------------------------------------------ logins
def _store():
    CU, path, why = J._portal_users()
    if not CU:
        raise RuntimeError(why)
    return CU, path


def _clean(s):
    return "".join(ch for ch in (s or "").lower() if ch.isalnum())


def _pick_username(con, person, own_ref=None):
    """First name if nobody else is called that; else the whole name; else numbered.
    A second Arjun must never share the first Arjun's name: the attendance
    register matches a login to a person by first name when nothing better is set."""
    taken = set()
    for r in con.execute("SELECT ref, LOWER(COALESCE(username,'')) u FROM joiner"):
        if J._v(r, "ref", 0) != own_ref and J._v(r, "u", 1):
            taken.add(J._v(r, "u", 1))
    try:
        CU, path = _store()
        for x in CU.list_users(path):
            taken.add(str(x.get("user", "")).lower())
    except Exception:
        pass
    first = J.default_username(person)
    full = _clean(person)
    others = _master_first_names()
    if first and first not in taken and first not in others:
        return first
    if full and full not in taken:
        return full
    base = full or first or "staff"
    n = 2
    while "%s%d" % (base, n) in taken:
        n += 1
    return "%s%d" % (base, n)


def _make_login(user, pw, role="staff"):
    """Create and prove a login. Backup first; any failure puts the store back."""
    CU, path = _store()
    store = CU.load_store(path)
    if user in (store.get("users") or {}):
        ok = bool(CU.verify_password(path, user, pw))
        return ok, ("exists" if ok else "exists, but the default password does not open it")
    if role not in (store.get("roles") or []):
        role = "staff"
    bak = "%s.bak_%s_%s" % (path, KIT, time.strftime("%Y%m%d-%H%M%S"))
    if os.path.exists(path):
        shutil.copyfile(path, bak)
    try:
        CU.add_user(path, user, role, pw)
        if not CU.verify_password(path, user, pw):
            raise RuntimeError("written but would not sign in")
    except Exception as ex:
        if os.path.exists(bak):
            shutil.copyfile(bak, path)
        return False, "not created (%s); the user store was put back" % ex
    return True, "created"


def _rename_login(old, new, pw):
    """A login typed with a space is replaced by its clean form (same role)."""
    CU, path = _store()
    store = CU.load_store(path)
    users = store.get("users") or {}
    if old not in users or new in users:
        return False
    role = users[old].get("role") or "staff"
    bak = "%s.bak_%s_%s" % (path, KIT, time.strftime("%Y%m%d-%H%M%S"))
    shutil.copyfile(path, bak)
    try:
        CU.add_user(path, new, role, pw)
        if not CU.verify_password(path, new, pw):
            raise RuntimeError("new login would not sign in")
        CU.del_user(path, old)
    except Exception:
        shutil.copyfile(bak, path)
        return False
    return True


# ------------------------------------------------------------ settle (heals)
def _settle(fin, sr, actor="system"):
    """Idempotent; runs on every list read. Changes only what is measurably due."""
    notes = []
    for r in fin.execute("SELECT id,ref,person,username,emp_code FROM joiner "
                         "WHERE kind='JOIN' AND status!='COMPLETE'").fetchall():
        jid, ref, person = J._v(r, "id", 0), J._v(r, "ref", 1), J._v(r, "person", 2)
        user = J._v(r, "username", 3) or ""
        st = _steps(fin, jid)
        # 1. a login typed with a space or capitals, while nobody has used it
        if user and _clean(user) != user and "FIRST_LOGIN" not in st:
            new = _pick_username(fin, person, own_ref=ref)
            try:
                if _rename_login(user, new, J.default_password(person)):
                    fin.execute("UPDATE joiner SET username=?, updated_at=? WHERE id=?",
                                (new, _now(), jid))
                    _event(fin, jid, actor, "LOGIN_RENAMED",
                           "'%s' -> '%s' (%s: a login with a space is hard to type)" % (user, new, KIT))
                    notes.append("%s: login %s -> %s" % (person, user, new))
            except Exception:
                pass
        # 2. STAFF_MASTER: true once he is in both files -- then ticked
        p = sr.execute("SELECT emp_code FROM joiner_pending WHERE ref=?", (ref,)).fetchone()
        code = p["emp_code"] if p else None
        if code and "STAFF_MASTER" not in st:
            in_master = code in _master_codes()
            in_reg = sr.execute("SELECT 1 FROM staff WHERE staff_id=? AND active=1",
                                (code,)).fetchone() is not None
            if in_master and in_reg:
                ok, _why = _tick(fin, jid, "STAFF_MASTER", "the system",
                                 "measured: number %s is in staff_master.csv and the staff "
                                 "register" % code, actor)
                if ok:
                    notes.append("%s: complete" % person)
    fin.commit()
    return notes


# ------------------------------------------------------------ views
def _person(fin, sr, ref):
    r = _jrow(fin, ref)
    if not r or J._v(r, "kind", 2) != "JOIN":
        return None
    jid = J._v(r, "id", 0)
    st = _steps(fin, jid)
    p = sr.execute("SELECT * FROM joiner_pending WHERE ref=?", (ref,)).fetchone()
    p = dict(p) if p else None
    person = J._v(r, "person", 3)
    user = J._v(r, "username", 6)
    handover = (p or {}).get("handover")
    login_needed = handover != "none"
    login = None
    if login_needed and user:
        login = {"user": user, "password": J.default_password(person)}
        try:
            CU, path = _store()
            rec = (CU.load_store(path).get("users") or {}).get(user)
            login["exists"] = bool(rec)
            login["active"] = bool(rec and rec.get("active"))
        except Exception as ex:
            login["exists"] = None
            login["why"] = str(ex)
    given = st.get("CREDENTIALS_SENT")
    code = (p or {}).get("emp_code") or J._v(r, "emp_code", 9)
    stage = ("details" if not p else
             "login" if not given else
             "machine" if not (p or {}).get("emp_code") else
             "done")
    if p and p.get("mobile"):
        p["mobile_masked"] = "xxxxxx" + p["mobile"][-4:]
    return {"ref": ref, "person": person, "status": J._v(r, "status", 5),
            "job": J._v(r, "role", 4), "employment": J._v(r, "employment", 7),
            "opened_on": J._v(r, "opened_on", 10), "username": user,
            "details": p, "login": login, "login_needed": login_needed,
            "given": given, "code": code, "stage": stage,
            "complete": J._v(r, "status", 5) == "COMPLETE",
            "steps": {k: v for k, v in st.items()}}


def _message(person, user, pw):
    return ("Namaste %s,\n\n"
            "Aapka clinic portal login ban gaya hai.\n\n"
            "Link : %s\n"
            "User : %s\n"
            "Password : %s\n\n"
            "Pehli baar login karke password badal lijiye.\n"
            "Koi dikkat ho to bataiye." % (person, PORTAL_LINK, user, pw))


# ------------------------------------------------------------ routes
@bp.route("/finance/staff/new")
def page_new():
    _u, err = _owner()
    if err:
        return err
    return send_file(os.path.join(HERE, "staff_easy.html"))


@bp.route("/finance/staff/easy/api/health")
def health():
    _u, err = _owner()
    if err:
        return err
    return jsonify(easy="ok", kit=KIT, staff_master=os.path.exists(STAFF_MASTER),
                   punches=os.path.exists(PUNCH_CSV), register=os.path.exists(SR_DB))


@bp.route("/finance/staff/easy/api/list")
def api_list():
    u, err = _owner()
    if err:
        return err
    fin = _fin()
    sr = _sr()
    try:
        notes = _settle(fin, sr, u)
        out = []
        for r in fin.execute("SELECT ref FROM joiner WHERE kind='JOIN' AND "
                             "(status!='COMPLETE' OR closed_on>=?) ORDER BY id DESC",
                             ((dt.date.today() - dt.timedelta(days=14)).isoformat(),)):
            x = _person(fin, sr, J._v(r, "ref", 0))
            if x:
                out.append({k: x[k] for k in ("ref", "person", "stage", "complete", "job",
                                              "opened_on", "code")})
        return jsonify(ok=True, people=out, settled=notes, jobs=list(JOBS),
                       employment=J.employment_kinds(fin), sunday=SUNDAY,
                       handover=HANDOVER, authorities=J.AUTHORITIES)
    finally:
        sr.close()


@bp.route("/finance/staff/easy/api/person")
def api_person():
    _u, err = _owner()
    if err:
        return err
    fin = _fin()
    sr = _sr()
    try:
        x = _person(fin, sr, (request.args.get("ref") or "").strip())
        if not x:
            return _bad("No joining with that reference.", 404)
        if x["login"] and x["details"]:
            x["message"] = _message(x["person"], x["login"]["user"], x["login"]["password"])
        return jsonify(ok=True, **x)
    finally:
        sr.close()


@bp.route("/finance/staff/easy/api/save", methods=["POST"])
def api_save():
    """Create a joining (no ref) or complete/change its details (ref)."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    person = re.sub(r"\s+", " ", (b.get("person") or "").strip())
    if len(person) < 2:
        return _bad("His full name is needed.")
    handover = (b.get("handover") or "").strip().lower()
    if handover not in HANDOVER:
        return _bad("Say what phone he has.")
    mobile = _clean_mobile(b.get("mobile"))
    if handover in ("whatsapp", "sms") and len(mobile) != 10:
        return _bad("A 10-digit mobile number is needed to send him his login by %s."
                    % HANDOVER[handover].split(" ")[0])
    if mobile and len(mobile) != 10:
        return _bad("The mobile number should have 10 digits.")
    fin = _fin()
    kinds = J.employment_kinds(fin)
    emp = (b.get("employment") or (kinds[0] if kinds else "FULLTIME")).strip().upper()
    if emp not in kinds:
        return _bad("Full-time or part-time?")
    job = re.sub(r"\s+", " ", (b.get("job") or "").strip())
    if not job:
        return _bad("Pick his job.")
    jd = (b.get("join_date") or _today()).strip()
    try:
        dt.date.fromisoformat(jd)
    except ValueError:
        return _bad("The joining date is not a date.")
    wd_s, wd_e = _hhmm(b.get("wd_start")), _hhmm(b.get("wd_end"))
    if not wd_s or not wd_e:
        return _bad("His weekday duty hours are needed (from and to).")
    grp = (b.get("sunday_group") or "").strip().upper()
    if grp not in SUNDAY:
        return _bad("Pick his Sunday duty.")
    sun_s, sun_e = _hhmm(b.get("sun_start")), _hhmm(b.get("sun_end"))
    if grp == "C" and (not sun_s or not sun_e):
        return _bad("His Sunday hours are needed (from and to).")
    if grp != "C":
        sun_s, sun_e = sun_s or wd_s, sun_e or wd_e
    try:
        salary = int(float(str(b.get("base_salary") or "0").replace(",", "")))
        offs = int(float(str(b.get("allowed_offs") if b.get("allowed_offs") not in (None, "") else 2)))
    except ValueError:
        return _bad("Salary and offs are numbers.")
    if salary < 0 or offs < 0 or offs > 31:
        return _bad("Salary and offs look wrong.")
    mexempt = 1 if str(b.get("minutes_exempt", "")).lower() in ("1", "true", "yes", "y") else 0
    auth = [a for a in (b.get("authorities") or ["self"]) if a in J.AUTHORITIES]
    if handover == "none":
        auth = []
    ref = (b.get("ref") or "").strip()
    sr = _sr()
    try:
        if ref:
            r = _jrow(fin, ref)
            if not r or J._v(r, "kind", 2) != "JOIN":
                return _bad("No joining with that reference.", 404)
            if J._v(r, "status", 5) == "COMPLETE":
                return _bad("This joining is complete; change him in the staff register.", 409)
            jid = J._v(r, "id", 0)
            p = sr.execute("SELECT emp_code FROM joiner_pending WHERE ref=?", (ref,)).fetchone()
            if p and p["emp_code"]:
                return _bad("He is already on the machine and in attendance; change him in "
                            "the staff register.", 409)
            fin.execute("UPDATE joiner SET person=?, role=?, employment=?, authorities=?, "
                        "updated_at=? WHERE id=?",
                        (person, job, emp, ",".join(auth) or None, _now(), jid))
        else:
            dup = fin.execute("SELECT ref FROM joiner WHERE kind='JOIN' AND LOWER(person)=? "
                              "AND status!='COMPLETE'", (person.lower(),)).fetchone()
            if dup:
                return _bad("%s is already being added (%s). Open him from the list."
                            % (person, J._v(dup, "ref", 0)), 409)
            ref = J.next_ref(fin, "JOIN")
            cur = fin.execute(
                "INSERT INTO joiner (ref,kind,person,role,employment,authorities,username,"
                "status,opened_on,opened_by,created_at,updated_at) "
                "VALUES (?,?,?,?,?,?,?,'DECIDED',?,?,?,?)",
                (ref, "JOIN", person, job, emp, ",".join(auth) or None, None,
                 _today(), u, _now(), _now()))
            jid = cur.lastrowid
            fin.execute("INSERT INTO joiner_step (joiner_id,step,done_on,done_by,detail) "
                        "VALUES (?,?,?,?,?)", (jid, "DECIDED", _today(), u,
                                               "details on the Add-staff form (%s)" % KIT))
            _event(fin, jid, u, "OPENED", "JOIN for %s (%s)" % (person, KIT))
        sr.execute(
            "INSERT INTO joiner_pending (ref,person,mobile,handover,department,employment,"
            "join_date,wd_start,wd_end,sunday_group,sun_start,sun_end,base_salary,"
            "allowed_offs,minutes_exempt,created_by,created_at,updated_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(ref) DO UPDATE SET "
            "person=excluded.person, mobile=excluded.mobile, handover=excluded.handover, "
            "department=excluded.department, employment=excluded.employment, "
            "join_date=excluded.join_date, wd_start=excluded.wd_start, wd_end=excluded.wd_end, "
            "sunday_group=excluded.sunday_group, sun_start=excluded.sun_start, "
            "sun_end=excluded.sun_end, base_salary=excluded.base_salary, "
            "allowed_offs=excluded.allowed_offs, minutes_exempt=excluded.minutes_exempt, "
            "updated_at=excluded.updated_at",
            (ref, person, mobile or None, handover, job, emp, jd, wd_s, wd_e, grp,
             sun_s, sun_e, salary, offs, mexempt, u, _now(), _now()))
        sr.commit()
        # the account: a login now (or, with no phone, an honest "none")
        r = _jrow(fin, ref)
        jid = J._v(r, "id", 0)
        st = _steps(fin, jid)
        msg = ""
        if handover == "none":
            if "ACCOUNT_CREATED" not in st:
                _tick(fin, jid, "ACCOUNT_CREATED", u,
                      "no login -- he has no phone; attendance by the machine only", u)
            if "CREDENTIALS_SENT" not in st:
                _tick(fin, jid, "CREDENTIALS_SENT", u, "not needed -- no phone", u)
            if "FIRST_LOGIN" not in st:
                _tick(fin, jid, "FIRST_LOGIN", u, "not needed -- no phone", u)
        else:
            user = J._v(r, "username", 6)
            if user and _clean(user) != user:          # typed with a space: rename, never orphan
                cleaned = _pick_username(fin, person, own_ref=ref)
                try:
                    if _rename_login(user, cleaned, J.default_password(person)):
                        _event(fin, jid, u, "LOGIN_RENAMED", "'%s' -> '%s' (%s)" % (user, cleaned, KIT))
                except Exception:
                    pass
                user = cleaned
            if not user:
                user = _pick_username(fin, person, own_ref=ref)
            ok, how = _make_login(user, J.default_password(person))
            if not ok:
                fin.commit()
                return _bad("His details are saved, but the login could not be made: %s" % how, 500,
                            ref=ref)
            fin.execute("UPDATE joiner SET username=?, updated_at=? WHERE id=?", (user, _now(), jid))
            if how == "created":
                _event(fin, jid, u, "PORTAL_USER_CREATED", "%s -- %s as staff, verified (%s)"
                       % (u, user, KIT))
            if "ACCOUNT_CREATED" not in st:
                _tick(fin, jid, "ACCOUNT_CREATED", u, "login %s made and proved" % user, u)
            msg = "Login %s is ready." % user
        fin.commit()
        return jsonify(ok=True, ref=ref, message=msg or "Saved.")
    finally:
        sr.close()


@bp.route("/finance/staff/easy/api/given", methods=["POST"])
def api_given():
    """He has his login (WhatsApp / SMS / slip), or none is needed."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    how = (b.get("how") or "").strip().lower()
    if how not in HANDOVER:
        return _bad("How was it given?")
    fin = _fin()
    sr = _sr()
    try:
        r = _jrow(fin, ref)
        if not r:
            return _bad("No joining with that reference.", 404)
        jid = J._v(r, "id", 0)
        ok, why = _tick(fin, jid, "CREDENTIALS_SENT", u, "login given by %s" % HANDOVER[how], u)
        if not ok:
            return _bad(why, 409)
        _tick(fin, jid, "FIRST_LOGIN", u,
              "not tracked -- the portal records no sign-ins; login given by %s" % HANDOVER[how], u)
        fin.commit()
        _settle(fin, sr, u)
        return jsonify(ok=True)
    finally:
        sr.close()


@bp.route("/finance/staff/easy/api/machine")
def api_machine():
    _u, err = _owner()
    if err:
        return err
    fin = _fin()
    since = None
    r = _jrow(fin, (request.args.get("ref") or "").strip())
    if r:
        since = J._v(r, "opened_on", 10)
    new, reused, nxt = _machine_view(fin, since)
    return jsonify(ok=True, new=new, reused=reused, next_code=nxt, now=_now())


@bp.route("/finance/staff/easy/api/link", methods=["POST"])
def api_link():
    """'Yes, this is him': the machine's number becomes his, everywhere, once."""
    u, err = _owner()
    if err:
        return err
    b = request.get_json(silent=True) or {}
    ref = (b.get("ref") or "").strip()
    code = str(b.get("code") or "").strip()
    if not code.isdigit():
        return _bad("Pick the number the machine sent.")
    code = int(code)
    fin = _fin()
    sr = _sr()
    try:
        r = _jrow(fin, ref)
        if not r or J._v(r, "kind", 2) != "JOIN":
            return _bad("No joining with that reference.", 404)
        jid, person = J._v(r, "id", 0), J._v(r, "person", 3)
        p = sr.execute("SELECT * FROM joiner_pending WHERE ref=?", (ref,)).fetchone()
        if not p:
            return _bad("Fill his details first.", 409)
        if p["emp_code"]:
            if int(p["emp_code"]) == code:
                return jsonify(ok=True, already=True)
            return _bad("He already has number %s." % p["emp_code"], 409)
        new, _reused, _n = _machine_view(fin, J._v(r, "opened_on", 10))
        if code not in {x["code"] for x in new}:
            return _bad("Number %d is not a new finger on the machine. Ask him to press his "
                        "finger once, wait a minute, and pick the number that appears." % code, 409)
        if sr.execute("SELECT 1 FROM staff WHERE staff_id=?", (code,)).fetchone():
            return _bad("Number %d is already somebody's in the staff register." % code, 409)
        user = J._v(r, "username", 6) if p["handover"] != "none" else None
        # 1. the staff register rows -- written, NOT yet committed
        sr.execute("BEGIN IMMEDIATE")
        sr.execute("INSERT INTO staff(staff_id,name,join_date,base_salary,sunday_group,"
                   "allowed_offs,minutes_exempt,cover_eligible,outstation_eligible,active,"
                   "username) VALUES(?,?,?,?,?,?,?,0,0,1,?)",
                   (code, person, p["join_date"], p["base_salary"], p["sunday_group"],
                    p["allowed_offs"], p["minutes_exempt"], user))
        sr.execute("INSERT INTO staff_shift(staff_id,effective_from,shift_start,shift_end) "
                   "VALUES(?,?,?,?)", (code, p["join_date"], p["wd_start"], p["wd_end"]))
        sr.execute("INSERT INTO audit_log(entity,entity_ref,action,old_value,new_value,actor,ts,note) "
                   "VALUES(?,?,?,?,?,?,?,?)",
                   ("staff", str(code), "join", "", person, u,
                    dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "%s Add staff -- %s" % (KIT, ref)))
        sr.execute("UPDATE joiner_pending SET emp_code=?, linked_on=?, linked_by=?, updated_at=? "
                   "WHERE ref=?", (code, _now(), u, _now(), ref))
        # 2. the attendance list
        try:
            _append_master({
                "user_id": code, "name": person, "department": p["department"] or "",
                "base_salary": p["base_salary"], "allowed_offs": p["allowed_offs"],
                "wd_start": p["wd_start"], "wd_end": p["wd_end"],
                "sun_start": p["sun_start"] or "", "sun_end": p["sun_end"] or "",
                "active": "Y", "timing_note": "", "sunday_group": p["sunday_group"],
                "minutes_exempt": "Y" if p["minutes_exempt"] else "N"})
        except Exception as ex:
            sr.rollback()
            return _bad("Nothing was changed: staff_master.csv could not be written (%s)." % ex, 500)
        sr.commit()
        # 3. the register of numbers (never reused) and the steps
        okc, why = J.issue_emp_code(fin, code, person, source="joiner")
        fin.execute("UPDATE joiner SET emp_code=?, updated_at=? WHERE id=?", (str(code), _now(), jid))
        first = next((x["first"] for x in new if x["code"] == code), "")
        _tick(fin, jid, "BIOMETRIC", u, "number %d -- his first punch reached the server %s"
              % (code, first), u)
        fin.commit()
        _settle(fin, sr, u)
        return jsonify(ok=True, code=code,
                       message="%s is number %d -- in attendance and salary from %s."
                       % (person, code, p["join_date"]))
    finally:
        sr.close()


@bp.route("/finance/staff/slip")
def page_slip():
    """A printed login slip, in Roman Hindi, for a smartphone without WhatsApp."""
    _u, err = _owner()
    if err:
        return err
    fin = _fin()
    sr = _sr()
    try:
        x = _person(fin, sr, (request.args.get("ref") or "").strip())
    finally:
        sr.close()
    if not x or not x["login"]:
        return Response("No login to print.", 404, mimetype="text/plain")
    esc = lambda s: (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    html = SLIP_HTML % {"person": esc(x["person"]), "link": esc(PORTAL_LINK),
                        "user": esc(x["login"]["user"]), "pw": esc(x["login"]["password"]),
                        "code": esc(x["code"] or "-")}
    return Response(html, mimetype="text/html")


SLIP_HTML = u"""<!doctype html><html lang="hi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Login slip</title>
<style>body{font:18px/1.6 system-ui,sans-serif;margin:0;padding:24px;color:#111;background:#fff}
.slip{max-width:420px;border:2px dashed #555;border-radius:12px;padding:18px 22px}
h1{font-size:20px;margin:0 0 6px}.k{color:#666;font-size:14px}.v{font-size:24px;font-weight:700;
letter-spacing:.03em;word-break:break-all}.row{margin:10px 0}.foot{font-size:14px;color:#444;margin-top:14px}
button{font-size:16px;padding:10px 16px;margin-top:16px;border-radius:8px;border:1px solid #2e6b34;
background:#2e6b34;color:#fff}@media print{button{display:none}body{padding:0}}</style></head><body>
<div class="slip"><h1>Dr Manoj Agarwal Clinic</h1>
<div>Namaste <b>%(person)s</b> -- aapka clinic portal login:</div>
<div class="row"><div class="k">Link (phone ke browser mein kholiye)</div><div class="v" style="font-size:18px">%(link)s</div></div>
<div class="row"><div class="k">User</div><div class="v">%(user)s</div></div>
<div class="row"><div class="k">Password</div><div class="v">%(pw)s</div></div>
<div class="foot">Pehli baar login karke password badal lijiye. Koi dikkat ho to reception par bataiye.</div>
</div><button onclick="window.print()">Print</button></body></html>"""
