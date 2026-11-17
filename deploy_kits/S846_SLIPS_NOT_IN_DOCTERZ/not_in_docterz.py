#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""not_in_docterz.py -- kit S846_SLIPS_NOT_IN_DOCTERZ (session S471, 16-Nov-2026; D980, D991). PARENT. NEW.
Mounted by day_check.init() and lives beside it. Flask and the standard library only.

THE OWNER, 16-Nov-2026 (07:34, 07:51, 11:01 IST): "backdated entries are possible from my login, and to keep the records
straight for future, I would like to do these entries in Docterz wherever needed myself" · "full mobile numbers, and still
few might not be entered in Docterz occasionally" · "go".

WHAT IT DOES. One list for him: every slip written since the slips began whose patient Docterz does not carry on that day
-- an OPD slip with no Docterz line at all for the ID, an X-ray or procedure slip with no Docterz line of that kind. Only
days whose Docterz export has been read; only slips with a clinic ID (a slip without one is the desk's own work, S844).
Each row: the date, what, the slip's amount, the name, the clinic ID, the FULL mobile (his page only -- the Call
Console's patient mirror, read-only), and four taps:
    Entered in Docterz        -- he has entered it back-dated; the row leaves the list (a later export of that day confirms)
    Not entering in Docterz   -- collected, kept outside Docterz; its amount is counted as "Slips outside Docterz" so the
                                 day still matches (day_check and clinic_money read outside_for_day())
    Free / staff / home       -- nothing collected; the row leaves the list
    Wrong slip                -- the slip should not count; the row leaves the list
Every tap can be undone. A row also leaves by itself the moment Docterz carries it.
The desk (parchi_desk) asks open_for_patient() when an ID is typed: an earlier slip of that patient still not in Docterz
shows one line while the patient is there.

ONE TABLE OF ITS OWN, created by his page's first request or tap (F-303); the readers never create it (S474 review):
    nid_mark  id, slip_id, kind (opd | xray | proc), act (entered | outside | free | wrong), amount_p, day, who, at,
              state (live | undone), undone_by, undone_at
It reads slip, slip_item, slip_adjust (radd), clinic_day_revenue, clinic_day_line, dx_visit, patient_ref, setting, and
/root/wa/console.db (read-only). It writes nid_mark only, every write audited.
No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import json
import os
import re
import sqlite3

from flask import Blueprint, redirect, request

bp = Blueprint("not_in_docterz", __name__)
_db = _require = _audit = None
OWNER_UNIT = "packs"                                      # the owner's console's own gate (owner_console.init)
SINCE_DEFAULT = "2026-09-23"                              # the first day of the slip book; setting 'nid.since' overrides
CONSOLE_DB = os.environ.get("NID_CONSOLE_DB", "/root/wa/console.db")
PAGE_URL = "/finance/clinic/not-in-docterz"
ACTS = (("entered", "Entered in Docterz"), ("outside", "Not entering in Docterz"),
        ("free", "Free / staff / home"), ("wrong", "Wrong slip"))
ACT_EN = dict(ACTS)
KIND_EN = {"opd": "OPD consultation", "xray": "X-ray", "proc": "Procedure"}
KIND_HI = {"opd": "OPD", "xray": "X-ray", "proc": "procedure"}
_done = False

SCHEMA = """
CREATE TABLE IF NOT EXISTS nid_mark (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  slip_id    INTEGER NOT NULL,
  kind       TEXT NOT NULL CHECK (kind IN ('opd','xray','proc')),
  act        TEXT NOT NULL CHECK (act IN ('entered','outside','free','wrong')),
  amount_p   INTEGER NOT NULL DEFAULT 0,
  day        TEXT NOT NULL,
  who        TEXT NOT NULL,
  at         TEXT NOT NULL,
  state      TEXT NOT NULL DEFAULT 'live' CHECK (state IN ('live','undone')),
  undone_by  TEXT NOT NULL DEFAULT '',
  undone_at  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS nid_mark_slip ON nid_mark(slip_id, kind, state);
CREATE INDEX IF NOT EXISTS nid_mark_day ON nid_mark(day, state);
CREATE UNIQUE INDEX IF NOT EXISTS nid_mark_live ON nid_mark(slip_id, kind) WHERE state='live';
"""


def init(app, db_getter, require_fn, audit_fn=None):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit
    _db, _require, _audit = db_getter, require_fn, audit_fn
    app.register_blueprint(bp)
    return bp


def ensure(con):
    global _done
    if _done:
        return
    con.executescript(SCHEMA)
    con.commit()
    _done = True


def _SL():
    import slip_log                                       # noqa: PLC0415
    return slip_log


def _stamp():
    return _SL()._stamp()


def _today():
    return _SL()._today()


def _who(u):
    return str((u or {}).get("user", "") or "")


def _audit_safe(con, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, "nid_mark", row_id, action, before=before, after=after, who=who)
    except Exception:                                      # noqa: BLE001 -- the audit never blocks the work
        pass


def _has(con, table):
    try:
        return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None
    except Exception:                                      # noqa: BLE001
        return False


def since(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='nid.since'").fetchone()
        v = str(r[0] if r else "").strip()
        dt.date.fromisoformat(v)
        return v
    except Exception:                                      # noqa: BLE001 -- no setting / not a date: the default
        return SINCE_DEFAULT


# ---------------------------------------------------------------- the rows
def rows(con, d_from=None, d_to=None, cid=None):
    """Every slip-kind (OPD / X-ray / procedure) since d_from whose patient Docterz does not carry that day.
    [{day, slip_id, series, slip_no, cid, kind, what, amount_p, name, mark}] -- mark is the live nid_mark dict or None.
    Pure read -- never creates nid_mark (a missing table = no answers yet). Days whose Docterz export has not been read are
    left out (not yet decidable)."""
    SL = _SL()
    d_from = d_from or since(con)
    d_to = d_to or _today()
    try:
        exported = {r[0] for r in con.execute("SELECT business_date FROM clinic_day_revenue WHERE business_date BETWEEN ? AND ?",
                                                (d_from, d_to))}
    except Exception:                                      # noqa: BLE001 -- no Docterz table on this box
        return []
    if not exported:
        return []
    one = " AND clinic_id=?" if cid else ""                 # S474 review: the desk asks for one patient -- read only theirs
    secs = {}
    for r in con.execute("SELECT business_date, clinic_id, section FROM clinic_day_line WHERE business_date BETWEEN ? AND ?" + one,
                         (d_from, d_to) + ((cid,) if cid else ())):
        secs.setdefault((r[0], str(r[1] or "").strip()), set()).add(r[2])
    dx = set()
    if _has(con, "dx_visit"):                              # Docterz's clinical report knows the visit too (a later export)
        for r in con.execute("SELECT visit_date, clinic_id FROM dx_visit WHERE substr(visit_date,1,10) BETWEEN ? AND ?" + one,
                             (d_from, d_to) + ((cid,) if cid else ())):   # S474 review: visit_date carries a time
            dx.add((str(r[0] or "")[:10], str(r[1] or "").strip()))
    radd = set()
    if _has(con, "slip_adjust"):
        radd = {r[0] for r in con.execute("SELECT slip_id FROM slip_adjust WHERE kind='cancel' AND state IN ('pending','approved')")}
    marks = {}
    if _has(con, "nid_mark"):
        for m in con.execute("SELECT * FROM nid_mark WHERE state='live' AND day BETWEEN ? AND ? ORDER BY id", (d_from, d_to)):
            marks[(m["slip_id"], m["kind"])] = dict(m)
    q = "SELECT * FROM slip WHERE state='ok' AND day BETWEEN ? AND ?"
    a = [d_from, d_to]
    if cid:
        q += " AND clinic_id=?"
        a.append(cid)
    slips = [dict(r) for r in con.execute(q + " ORDER BY day DESC, series, slip_no DESC", a)]
    its = {}
    ids = [s["id"] for s in slips if s["series"] != "opd"]
    for i in range(0, len(ids), 400):
        part = ids[i:i + 400]
        for it in con.execute("SELECT * FROM slip_item WHERE slip_id IN (%s) ORDER BY slip_id, sort" % ",".join("?" * len(part)), part):
            its.setdefault(it["slip_id"], []).append(dict(it))
    rejected = set()                                       # S474 review: a REJECTED chhoot puts the full rate back (as day_check)
    if _has(con, "slip_adjust"):
        iids = [it["id"] for v in its.values() for it in v]
        for i in range(0, len(iids), 400):
            part = iids[i:i + 400]
            rejected |= {r[0] for r in con.execute("SELECT item_id FROM slip_adjust WHERE state='rejected' AND item_id IN (%s)"
                                                   % ",".join("?" * len(part)), part)}
    fees = {}
    out = []
    for s in slips:
        d, sid = s["day"], s["id"]
        c = str(s.get("clinic_id") or "").strip()
        if d not in exported or sid in radd or s.get("no_id_name") or not c or not re.fullmatch(r"\d{1,12}", c):
            continue
        have = secs.get((d, c), set())
        name = (s.get("name_seen") or "").strip()
        if s["series"] == "opd":
            if have or (d, c) in dx:
                continue
            if d not in fees:
                try:
                    fees[d] = int(SL.usual_fee(con, d) or 0)
                except Exception:                          # noqa: BLE001
                    fees[d] = 0
            out.append(dict(day=d, slip_id=sid, series="opd", slip_no=s["slip_no"], cid=c, kind="opd", paid=s.get("paid_mode") or "",
                            what=KIND_EN["opd"], amount_p=fees[d], name=name, mark=marks.get((sid, "opd"))))
            continue
        for kind in ("xray", "proc"):
            mine = [it for it in its.get(sid, []) if it["kind"] == kind]
            if not mine or kind in have:
                continue
            net = sum(max(0, int(it["price_p"] or 0) - (0 if it["id"] in rejected else int(it.get("discount_p") or 0))) for it in mine)
            if net <= 0:                                   # a free line: nothing to bill, nothing to enter
                continue
            what = "%s: %s" % (KIND_EN[kind], ", ".join(("%s %s" % (it["name"] or "", it["side"] or "")).strip() for it in mine)[:120])
            out.append(dict(day=d, slip_id=sid, series=s["series"], slip_no=s["slip_no"], cid=c, kind=kind, paid=s.get("paid_mode") or "",
                            what=what, amount_p=net, name=name, mark=marks.get((sid, kind))))
    for r in out:                                          # the name: the slip's own, else the master's (Docterz's newest wins)
        if not r["name"]:
            try:
                p = SL.patient(con, r["cid"])
                r["name"] = (p[0] if p else "") or ""
            except Exception:                              # noqa: BLE001
                r["name"] = ""
    return out


def open_rows(con):
    return [r for r in rows(con) if not r["mark"]]


def marked_rows(con):
    return [r for r in rows(con) if r["mark"]]


def outside_for_day(con, d):
    """[amount_p, ...] of the day's rows he marked 'Not entering in Docterz' that Docterz still does not carry.
    Never raises: [] when anything cannot be read (the callers stand without it)."""
    try:
        return [int(r["amount_p"]) for r in rows(con, d, d) if r["mark"] and r["mark"]["act"] == "outside" and r["amount_p"] > 0]
    except Exception:                                      # noqa: BLE001
        return []


def explained_for_day(con, d):
    """[(amount_p, act), ...] -- the day's rows he answered 'Entered in Docterz' (back-dated, not in this day's export yet) or
    'Not entering in Docterz': money the counter holds that Docterz's export of the day does not. clinic_money reads it.
    Never raises: [] when anything cannot be read."""
    try:
        return [(int(r["amount_p"]), r["mark"]["act"]) for r in rows(con, d, d)
                if r["mark"] and r["mark"]["act"] in ("entered", "outside") and r["amount_p"] > 0]
    except Exception:                                      # noqa: BLE001
        return []


def upi_for_day(con, d):
    """[amount_p, ...] -- the day's answered slips (entered / outside) the slip did NOT mark as paid in cash: the only ones a
    stray bank UPI may be explained by (S474 review). Never raises."""
    try:
        return [int(r["amount_p"]) for r in rows(con, d, d) if r["mark"] and r["mark"]["act"] in ("entered", "outside")
                and r["amount_p"] > 0 and r.get("paid", "") != "cash"]
    except Exception:                                      # noqa: BLE001
        return []


def marks_for_day(con, d):
    """{(slip_id, kind): act} -- the day's live marks. Never raises; never creates the table."""
    try:
        if not _has(con, "nid_mark"):
            return {}
        return {(m["slip_id"], m["kind"]): m["act"] for m in con.execute("SELECT slip_id, kind, act FROM nid_mark WHERE day=? AND state='live'", (d,))}
    except Exception:                                      # noqa: BLE001
        return {}


def open_for_patient(con, cid, before):
    """The patient's earlier slips (before the given day) still not in Docterz and not answered: [{day, kind}]. Never raises."""
    try:
        c = str(cid or "").strip()
        if not c or not re.fullmatch(r"\d{1,12}", c):
            return []
        b = (dt.date.fromisoformat(before) - dt.timedelta(days=1)).isoformat()
        return [dict(day=r["day"], kind=r["kind"]) for r in rows(con, None, b, cid=c) if not r["mark"]]
    except Exception:                                      # noqa: BLE001
        return []


def counts(con):
    """(open, outside_total_p) for the owner's console. Never raises: (None, None)."""
    try:
        rr = rows(con)
        return (sum(1 for r in rr if not r["mark"]),
                sum(r["amount_p"] for r in rr if r["mark"] and r["mark"]["act"] == "outside"))
    except Exception:                                      # noqa: BLE001
        return None, None


# ---------------------------------------------------------------- the full mobile (his page only)
def _m10(s):
    d = re.sub(r"\D", "", str(s or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 and d[0] in "6789" else ""


def mobiles(cids):
    """{clinic_id: [mobiles]} from the Call Console's patient mirror, read-only. {} when it cannot be read."""
    want = {str(c) for c in cids if c}
    out = {}
    if not want or not os.path.exists(CONSOLE_DB):
        return out
    try:
        con = sqlite3.connect("file:%s?mode=ro" % CONSOLE_DB, uri=True, timeout=10)
        try:
            for ph, cid in con.execute("SELECT phone10, clinic_id FROM patients"):
                c = str(cid if cid is not None else "").strip()
                if re.match(r"^\d+\.0$", c):
                    c = c[:-2]
                m = _m10(ph)
                if m and c in want and m not in out.setdefault(c, []):
                    out[c].append(m)
        finally:
            con.close()
    except sqlite3.Error:
        return {}
    return out


# ---------------------------------------------------------------- writing
class MarkError(Exception):
    pass


def mark(con, who, slip_id, kind, act):
    ensure(con)
    if act not in ACT_EN:
        raise MarkError("Unknown answer.")
    if kind not in KIND_EN:
        raise MarkError("Unknown kind.")
    s = con.execute("SELECT day, clinic_id FROM slip WHERE id=? AND state='ok'", (slip_id,)).fetchone()
    if s is None:
        raise MarkError("This slip is no longer on the list.")
    r = next((x for x in rows(con, s["day"], s["day"], cid=str(s["clinic_id"] or "").strip())
              if x["slip_id"] == slip_id and x["kind"] == kind), None)
    if r is None:
        raise MarkError("Docterz already carries this one, or it has changed — the page is fresh now.")
    if r["mark"]:
        raise MarkError("Already answered: %s." % ACT_EN.get(r["mark"]["act"], r["mark"]["act"]))
    try:
        cur = con.execute("INSERT INTO nid_mark (slip_id, kind, act, amount_p, day, who, at) VALUES (?,?,?,?,?,?,?)",
                          (slip_id, kind, act, int(r["amount_p"] or 0), r["day"], who, _stamp()))
    except sqlite3.IntegrityError:                         # a double tap: the unique live index refuses the second
        con.rollback()
        raise MarkError("Already answered.")
    _audit_safe(con, cur.lastrowid, "nid_mark", None, json.dumps({"slip": slip_id, "kind": kind, "act": act}), who)
    con.commit()
    return cur.lastrowid


def undo(con, who, mark_id):
    ensure(con)
    m = con.execute("SELECT * FROM nid_mark WHERE id=? AND state='live'", (mark_id,)).fetchone()
    if m is None:
        raise MarkError("Already undone.")
    con.execute("UPDATE nid_mark SET state='undone', undone_by=?, undone_at=? WHERE id=? AND state='live'", (who, _stamp(), mark_id))
    _audit_safe(con, mark_id, "nid_mark_undone", json.dumps({"act": m["act"]}), json.dumps({"state": "undone"}), who)
    con.commit()


# ---------------------------------------------------------------- the page (English: his)
STYLE = """<style>
.nid .row{border-top:2px solid #c9d3da;padding:12px 0}.nid .row:first-of-type{border-top:0}
.nid .top{display:flex;justify-content:space-between;gap:10px;flex-wrap:wrap;font-weight:700}
.nid .sub{color:#3c464e;font-size:17px;margin:4px 0 8px}
.nid .acts{display:flex;flex-wrap:wrap;gap:8px}
.nid .acts form{margin:0}
.nid button{min-height:48px;border-radius:9px;border:2px solid #14456e;background:#fff;color:#14456e;font-size:16px;font-weight:600;padding:6px 14px;cursor:pointer}
.nid button.pri{background:#14456e;color:#fff}
.nid a.tel{font-weight:700;color:#14456e;white-space:nowrap}
.nid .ok{background:#dff0d8;color:#2c6e2f;padding:10px 14px;border-radius:8px;margin:0 0 12px}
.nid .bad{background:#fadbd8;color:#9c2a20;padding:10px 14px;border-radius:8px;margin:0 0 12px}
</style>"""


def _dm(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%a %d %b")
    except (ValueError, TypeError):
        return iso or "—"


def _esc(s):
    return _SL()._esc(s)


def _rs(p):
    return _SL()._rs(p)


def page_html(con, msg="", err=""):
    rr = rows(con)
    op = [r for r in rr if not r["mark"]]
    mk = [r for r in rr if r["mark"]]
    mob = mobiles({r["cid"] for r in rr})
    out = ["<div class='nid'>"]
    if msg:
        out.append("<div class='ok'>%s</div>" % _esc(msg))
    if err:
        out.append("<div class='bad'>%s</div>" % _esc(err))

    def who_line(r):
        ms = mob.get(r["cid"]) or []
        tel = " · ".join("<a class='tel' href='tel:%s'>%s</a>" % (m, m) for m in ms[:3]) or "<span>no mobile on record</span>"
        return "%s · ID %s · %s · slip %s-%s" % (_esc(r["name"] or "name not known"), _esc(r["cid"]), tel,
                                                  "OPD" if r["series"] == "opd" else "XP", r["slip_no"])

    out.append("<div class='card'><h2>To enter in Docterz (back-dated) — %d</h2>" % len(op))
    out.append("<p class='mut'>Slips written since %s whose patient is not in Docterz on that day. Enter each with the slip's date, "
               "then tap <b>Entered in Docterz</b>. A row also leaves by itself when a Docterz export of that day carries it.</p>"
               % _esc(_dm(since(con))))
    if not op:
        out.append("<p>Nothing to enter. ✓</p>")
    for r in op:
        out.append("<div class='row'><div class='top'><span>%s · %s</span><span>%s</span></div><div class='sub'>%s</div><div class='acts'>"
                   % (_esc(_dm(r["day"])), _esc(r["what"]), _rs(r["amount_p"]) if r["amount_p"] else "amount not known", who_line(r)))
        for a, word in ACTS:
            out.append("<form method='post' action='%s/act'><input type='hidden' name='slip' value='%d'>"
                       "<input type='hidden' name='kind' value='%s'><input type='hidden' name='act' value='%s'>"
                       "<button class='%s'>%s</button></form>" % (PAGE_URL, r["slip_id"], r["kind"], a, "pri" if a == "entered" else "", word))
        out.append("</div></div>")
    out.append("</div>")
    if mk:
        out.append("<div class='card'><h2>Answered by you — %d</h2><p class='mut'>Still not in Docterz's export of that day. "
                   "<b>Not entering in Docterz</b> counts in the day's money as \"Slips outside Docterz\".</p>" % len(mk))
        for r in mk:
            out.append("<div class='row'><div class='top'><span>%s · %s</span><span>%s</span></div><div class='sub'>%s<br><b>%s</b> · %s %s</div>"
                       "<div class='acts'><form method='post' action='%s/act'><input type='hidden' name='mark' value='%d'>"
                       "<input type='hidden' name='act' value='undo'><button>Undo</button></form></div></div>"
                       % (_esc(_dm(r["day"])), _esc(r["what"]), _rs(r["amount_p"]), who_line(r), _esc(ACT_EN.get(r["mark"]["act"], "")),
                          _esc(r["mark"]["who"]), _esc(str(r["mark"]["at"])[:16]), PAGE_URL, int(r["mark"]["id"])))
        out.append("</div>")
    out.append("<p class='navrow'><a class='btn' href='/finance/console'>← Console</a></p></div>")
    return "".join(out) + STYLE


def _gate():
    return _require("checker", unit=OWNER_UNIT)


def _CR():
    import clinic_register                                # noqa: PLC0415
    return clinic_register


@bp.route(PAGE_URL)
def page():
    u, err = _gate()
    CR = _CR()
    if err:
        return CR._shell("Slips not in Docterz", CR._denied())
    con = _db()
    _SL().ensure(con)
    ensure(con)
    return CR._shell("Slips not in Docterz", page_html(con, request.args.get("ok") or "", request.args.get("err") or ""))


@bp.route(PAGE_URL + "/act", methods=["POST"])
def act():
    u, err = _gate()
    if err:
        return redirect(PAGE_URL, code=303)
    con = _db()
    _SL().ensure(con)
    ensure(con)
    f = request.form
    a = str(f.get("act") or "")
    q = _SL()._q
    try:
        if a == "undo":
            undo(con, _who(u), int(f.get("mark") or 0))
            return redirect(PAGE_URL + "?ok=" + q("Undone."), code=303)
        mark(con, _who(u), int(f.get("slip") or 0), str(f.get("kind") or ""), a)
    except (MarkError, ValueError) as ex:
        return redirect(PAGE_URL + "?err=" + q(str(ex) if isinstance(ex, MarkError) else "Not understood."), code=303)
    return redirect(PAGE_URL + "?ok=" + q("Noted: %s." % ACT_EN[a]), code=303)
