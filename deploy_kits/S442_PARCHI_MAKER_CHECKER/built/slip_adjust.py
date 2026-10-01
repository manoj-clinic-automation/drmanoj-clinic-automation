#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""slip_adjust.py -- kit S442_PARCHI_MAKER_CHECKER (session 287, 01-Oct-2026, D644 · F-663 · F-664 · F-668). PARENT.
Mounted by slip_log.init(); lives beside slip_log.py and reads/writes only its own table plus the slip it belongs to.

THE OWNER, 30-Sep / 01-Oct-2026 ("reception enters, Shavez or me approve"):
  * DISCOUNT AND FREE. Any X-ray or procedure line can take "Chhoot Rs ___" or "Free" (free = the whole rate), with a
    reason from a pick: staff/family · poor patient · repeat/redo · doctor's instruction · other. Reception (and Shavez,
    Bhati) enter it; Shavez or the owner approve; Dr Bhawna also approves. NOBODY APPROVES THEIR OWN ENTRY.
    The patient never waits: the line carries the discount the moment it is written (slip_item.discount_p, as S379
    already did); the approval comes later in the day; a rejected discount goes to the night report.
    Staff still apply the discount in Docterz -- this record is the record and the approval.
  * CANCELLED AFTER BILLING (Docterz cannot cancel). "Radd" on a parchi asks the clinic ID and one choice: money
    returned / money never taken. It is approved like a discount; once approved, that Docterz line leaves the expected
    cash / UPI (clinic_money) and shows under "Cancelled after billing". A parchi already marked cancelled with no ID
    (Tehzida Begum, 29-Sep, F-664) takes its ID here in one tap -- never guessed.
  * THE LATE PARCHI (F-663). The 7-day late entry exists (S401); the day stayed on "Aaj". The screen now PROPOSES the
    day: the ID is in the last Docterz day before today (and has no parchi there yet), or the number is below today's
    first number. One tap accepts; nothing is ever moved without it.
  * THE OWNER'S PAGE: the month's discounts and free lines -- who asked, who approved -- at /finance/slips/discounts.

ONE TABLE, created on first request (F-303):
    slip_adjust  id, slip_id, item_id, kind (discount | free | cancel), amount_p, reason, note, cancel_how, clinic_id,
                 day, made_by, made_at, state (pending | approved | rejected | replaced), checked_by, checked_at, check_note
Flask and the standard library only. No patient name, no number, no secret (F-185).
"""
import datetime as dt
import json

from flask import Blueprint, jsonify, redirect, request

bp = Blueprint("slip_adjust", __name__)
_db = _require = _audit = None
UNIT = "slips"
_done = False

REASONS = (("staff", "Staff / ghar wale", "staff / family"), ("poor", "Garib mareez", "poor patient"),
           ("redo", "Dobara / redo", "repeat / redo"), ("doctor", "Doctor ke kehne par", "doctor's instruction"),
           ("other", "Kuch aur", "other"))
REASON_HI = {k: h for k, h, _e in REASONS}
REASON_EN = {k: e for k, _h, e in REASONS}
APPROVERS_DEFAULT = "shavez,manoj,bhawna"
CANCEL_HOW = {"returned": ("Paise lauta diye", "money returned"), "never_taken": ("Paise liye hi nahi", "money never taken")}

SCHEMA = """
CREATE TABLE IF NOT EXISTS slip_adjust (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  slip_id     INTEGER NOT NULL,
  item_id     INTEGER,
  kind        TEXT NOT NULL CHECK (kind IN ('discount','free','cancel')),
  amount_p    INTEGER NOT NULL DEFAULT 0,
  reason      TEXT NOT NULL DEFAULT '',
  note        TEXT NOT NULL DEFAULT '',
  cancel_how  TEXT NOT NULL DEFAULT '',
  clinic_id   TEXT NOT NULL DEFAULT '',
  day         TEXT NOT NULL,
  made_by     TEXT NOT NULL,
  made_at     TEXT NOT NULL,
  state       TEXT NOT NULL DEFAULT 'pending' CHECK (state IN ('pending','approved','rejected','replaced')),
  checked_by  TEXT NOT NULL DEFAULT '',
  checked_at  TEXT NOT NULL DEFAULT '',
  check_note  TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS slip_adjust_slip ON slip_adjust(slip_id);
CREATE INDEX IF NOT EXISTS slip_adjust_day ON slip_adjust(day, state);
"""


class AdjustError(Exception):
    pass


def init(app, db_getter, require_fn, audit_fn=None, unit="slips"):
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
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
    import slip_log                                        # noqa: PLC0415 -- beside this file, mounted first
    return slip_log


def _now():
    return _SL()._now()


def _stamp():
    return _SL()._stamp()


def _who(u):
    return (u or {}).get("user", "") or ""


def _audit_safe(con, row_id, action, before, after, who):
    if not _audit:
        return
    try:
        _audit(con, "slip_adjust", row_id, action, before=before, after=after, who=who)
    except Exception:                                      # noqa: BLE001 -- the audit never blocks the work
        pass


def approvers(con):
    try:
        r = con.execute("SELECT value FROM setting WHERE key='slips.approvers'").fetchone()
        v = (r[0] if r and (r[0] or "").strip() else APPROVERS_DEFAULT)
    except Exception:                                      # noqa: BLE001
        v = APPROVERS_DEFAULT
    return [x.strip().lower() for x in v.replace(";", ",").split(",") if x.strip()]


def is_approver(con, u):
    return _who(u).lower() in approvers(con)


# ---------------------------------------------------------------- writing
def add_discount(con, who, slip_id, item_id, amount_p, free, reason, note=""):
    """One discount (or Free) on one X-ray / procedure line. Replaces an earlier one on the same line (marked
    'replaced', never deleted). The line carries the discount at once; the approval is the record."""
    ensure(con)
    SL = _SL()
    it = con.execute("SELECT i.*, s.day, s.state AS sstate, s.series FROM slip_item i JOIN slip s ON s.id=i.slip_id "
                     "WHERE i.id=? AND i.slip_id=?", (item_id, slip_id)).fetchone()
    if it is None or it["sstate"] != "ok":
        raise AdjustError("Yeh line nahi mili.")
    if it["kind"] not in ("xray", "proc"):
        raise AdjustError("Chhoot sirf X-ray / procedure par.")
    price = int(it["price_p"] or 0)
    if reason not in REASON_HI:
        raise AdjustError("Chhoot ki wajah chunein.")
    if free:
        if not price:
            raise AdjustError("Is line ka rate nahi hai — Free likhne ke liye rate chahiye.")
        amount_p, kind = price, "free"
    else:
        kind = "discount"
        if amount_p is None or amount_p <= 0:
            raise AdjustError("Chhoot mein rupaye likhein (jaise 100).")
        if price and amount_p > price:
            raise AdjustError("Chhoot %s rate %s se zyada nahi ho sakti." % (SL._rs(amount_p), SL._rs(price)))
    now = _stamp()
    con.execute("UPDATE slip_adjust SET state='replaced' WHERE item_id=? AND kind IN ('discount','free') AND state IN ('pending','approved')",
                (item_id,))
    cur = con.execute("INSERT INTO slip_adjust (slip_id, item_id, kind, amount_p, reason, note, day, made_by, made_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (slip_id, item_id, kind, int(amount_p), reason, (note or "")[:120], it["day"], who, now))
    con.execute("UPDATE slip_item SET discount_p=? WHERE id=?", (int(amount_p), item_id))
    con.execute("UPDATE slip SET updated_by=?, updated_at=? WHERE id=?", (who, now, slip_id))
    _audit_safe(con, cur.lastrowid, "slip_discount", json.dumps({"discount_p": int(it["discount_p"] or 0)}),
                json.dumps({"kind": kind, "amount_p": int(amount_p), "reason": reason, "item": item_id}), who)
    con.commit()
    return cur.lastrowid


def add_from_log(con, who, slip_id, item_id, amount_p, reason, free=False):
    """log_slip's hand-off: a discount typed at logging time becomes a pending entry, exactly as if added after."""
    ensure(con)
    kind = "free" if free else "discount"
    cur = con.execute("INSERT INTO slip_adjust (slip_id, item_id, kind, amount_p, reason, day, made_by, made_at) "
                      "SELECT ?, ?, ?, ?, ?, day, ?, ? FROM slip WHERE id=?",
                      (slip_id, item_id, kind, int(amount_p), reason if reason in REASON_HI else "other", who, _stamp(), slip_id))
    return cur.lastrowid


def add_cancel(con, who, slip_id, clinic_id, how, note=""):
    """Radd after billing: the clinic ID (never guessed) and one choice. A parchi with no ID takes it here."""
    ensure(con)
    SL = _SL()
    s = con.execute("SELECT * FROM slip WHERE id=? AND state<>'void'", (slip_id,)).fetchone()
    if s is None:
        raise AdjustError("Parchi nahi mili.")
    if s["state"] not in ("ok", "cancelled"):
        raise AdjustError("Sirf likhi hui ya radd parchi.")
    if (_now().date() - dt.date.fromisoformat(s["day"])).days > SL.LATE_DAYS:
        raise AdjustError("Yeh parchi %d din se purani hai." % SL.LATE_DAYS)
    cid = SL._clean_id(clinic_id) or s["clinic_id"]
    if not cid:
        raise AdjustError("Clinic ID likhein — Docterz mein jis ID par bill bana tha.")
    if how not in CANCEL_HOW:
        raise AdjustError("Chunein: paise lauta diye / paise liye hi nahi.")
    if con.execute("SELECT 1 FROM slip_adjust WHERE slip_id=? AND kind='cancel' AND state IN ('pending','approved')", (slip_id,)).fetchone():
        raise AdjustError("Is parchi ka radd pehle se likha hai.")
    now = _stamp()
    if not s["clinic_id"]:
        con.execute("UPDATE slip SET clinic_id=?, updated_by=?, updated_at=? WHERE id=?", (cid, who, now, slip_id))
        _audit_safe(con, slip_id, "slip_id_added", json.dumps({"clinic_id": ""}), json.dumps({"clinic_id": cid, "via": "radd"}), who)
    cur = con.execute("INSERT INTO slip_adjust (slip_id, kind, cancel_how, clinic_id, note, day, made_by, made_at) VALUES (?,?,?,?,?,?,?,?)",
                      (slip_id, "cancel", how, cid, (note or "")[:120], s["day"], who, now))
    _audit_safe(con, cur.lastrowid, "slip_cancel_asked", None, json.dumps({"slip": slip_id, "clinic_id": cid, "how": how}), who)
    con.commit()
    return cur.lastrowid


def decide(con, who, adj_id, ok, note=""):
    """The checker's tap. Nobody approves their own entry. The first decision stands."""
    ensure(con)
    a = con.execute("SELECT * FROM slip_adjust WHERE id=?", (adj_id,)).fetchone()
    if a is None:
        raise AdjustError("Nahi mila.")
    if a["state"] != "pending":
        raise AdjustError("Pehle hi tay ho chuka: %s (%s)." % (a["state"], a["checked_by"] or "-"))
    if who.lower() not in approvers(con):
        raise AdjustError("Manzoori sirf %s de sakte hain." % ", ".join(x.title() for x in approvers(con)))
    if (a["made_by"] or "").lower() == who.lower():
        raise AdjustError("Apni likhi hui entry aap manzoor nahi kar sakte.")
    if not ok and not (note or "").strip():
        raise AdjustError("Na-manzoor karne ki wajah likhein.")
    now = _stamp()
    st = "approved" if ok else "rejected"
    con.execute("UPDATE slip_adjust SET state=?, checked_by=?, checked_at=?, check_note=? WHERE id=? AND state='pending'",
                (st, who, now, (note or "")[:120], adj_id))
    if a["kind"] == "cancel" and ok:
        s = con.execute("SELECT state FROM slip WHERE id=?", (a["slip_id"],)).fetchone()
        if s is not None and s["state"] == "ok":
            con.execute("UPDATE slip SET state='cancelled', note=?, updated_by=?, updated_at=? WHERE id=?",
                        ("radd after billing (%s)" % CANCEL_HOW[a["cancel_how"]][1], who, now, a["slip_id"]))
    _audit_safe(con, adj_id, "slip_adjust_" + st, json.dumps({"state": "pending"}), json.dumps({"state": st, "note": note}), who)
    con.commit()
    return st


# ---------------------------------------------------------------- reading
def for_items(con, item_ids):
    """{item_id: the live adjust row (pending / approved / rejected)} -- the newest per line."""
    ensure(con)
    out = {}
    if not item_ids:
        return out
    for r in con.execute("SELECT * FROM slip_adjust WHERE item_id IN (%s) AND state<>'replaced' ORDER BY id" % ",".join("?" * len(item_ids)),
                         list(item_ids)):
        out[r["item_id"]] = dict(r)
    return out


def cancels_for_day(con, d, states=("approved",)):
    """Radd after billing on day d: [{slip_id, series, slip_no, clinic_id, how, made_by, checked_by, state}]."""
    ensure(con)
    try:
        rows = con.execute("SELECT a.*, s.series, s.slip_no FROM slip_adjust a JOIN slip s ON s.id=a.slip_id "
                           "WHERE a.kind='cancel' AND a.day=? AND a.state IN (%s) ORDER BY a.id" % ",".join("?" * len(states)),
                           [d] + list(states)).fetchall()
    except Exception:                                      # noqa: BLE001
        return []
    return [dict(r) for r in rows]


def pending(con):
    ensure(con)
    rows = con.execute("SELECT a.*, s.series, s.slip_no, s.clinic_id AS sid_clinic, i.name AS item_name, i.side, i.price_p "
                       "FROM slip_adjust a JOIN slip s ON s.id=a.slip_id LEFT JOIN slip_item i ON i.id=a.item_id "
                       "WHERE a.state='pending' ORDER BY a.day, a.id").fetchall()
    return [dict(r) for r in rows]


def month_rows(con, ym):
    ensure(con)
    rows = con.execute("SELECT a.*, s.series, s.slip_no, s.clinic_id AS sid_clinic, i.name AS item_name, i.side, i.price_p, i.kind AS item_kind "
                       "FROM slip_adjust a JOIN slip s ON s.id=a.slip_id LEFT JOIN slip_item i ON i.id=a.item_id "
                       "WHERE substr(a.day,1,7)=? AND a.state<>'replaced' ORDER BY a.day, a.id", (ym,)).fetchall()
    return [dict(r) for r in rows]


def month_summary(con, ym):
    """For the owner's money page: (total discount Rs in paise approved, lines, pending, rejected, cancels)."""
    rows = month_rows(con, ym)
    disc = [r for r in rows if r["kind"] in ("discount", "free")]
    return dict(approved_p=sum(r["amount_p"] for r in disc if r["state"] == "approved"),
                pending_p=sum(r["amount_p"] for r in disc if r["state"] == "pending"),
                lines=len(disc), pending=len([r for r in rows if r["state"] == "pending"]),
                rejected=len([r for r in rows if r["state"] == "rejected"]),
                cancels=len([r for r in rows if r["kind"] == "cancel" and r["state"] == "approved"]))


def propose_day(con, series, slip_no, clinic_id):
    """F-663: the day a late parchi most likely belongs to, or None. (iso, why_hi, why_en)."""
    SL = _SL()
    today = SL._today()
    t = dt.date.fromisoformat(today)
    lo = (t - dt.timedelta(days=SL.LATE_DAYS)).isoformat()
    n = SL._int(slip_no)
    if n is not None:
        first = con.execute("SELECT MIN(slip_no) FROM slip WHERE series=? AND day=? AND state<>'void' AND state<>'missing'",
                            (series, today)).fetchone()[0]
        if first is not None and n < int(first):
            r = con.execute("SELECT day FROM slip WHERE series=? AND slip_no<? AND state<>'void' AND day<? AND day>=? "
                            "ORDER BY slip_no DESC LIMIT 1", (series, n, today, lo)).fetchone()
            d = r[0] if r else (t - dt.timedelta(days=1)).isoformat()
            return d, "Aaj ki pehli parchi %d hai — %d usse pehle ki hai" % (first, n), "today's first number is %d" % first
    cid = SL._clean_id(clinic_id)
    if cid:
        secs = ("consult",) if series == "opd" else ("xray", "proc")
        try:
            if con.execute("SELECT 1 FROM clinic_day_line WHERE business_date=? AND clinic_id=? LIMIT 1", (today, cid)).fetchone():
                return None
            last = con.execute("SELECT MAX(business_date) FROM clinic_day_line WHERE business_date<? AND business_date>=?",
                               (today, lo)).fetchone()[0]
            if last and con.execute("SELECT 1 FROM clinic_day_line WHERE business_date=? AND clinic_id=? AND section IN (%s) LIMIT 1"
                                    % ",".join("?" * len(secs)), [last, cid] + list(secs)).fetchone():
                if not con.execute("SELECT 1 FROM slip WHERE series=? AND day=? AND clinic_id=? AND state='ok'", (series, last, cid)).fetchone():
                    return last, "ID %s %s ke Docterz mein hai" % (cid, SL._dmy(last)[:6]), "the ID is in Docterz of %s" % last
        except Exception:                                  # noqa: BLE001 -- no Docterz table: no proposal
            return None
    return None


# ---------------------------------------------------------------- routes
def _back(s, ok="", err=""):
    SL = _SL()
    return redirect("/finance/slips?s=%s%s%s" % (s, ("&ok=" + SL._q(ok)) if ok else "", ("&err=" + SL._q(err)) if err else ""), code=303)


@bp.route("/finance/slips/adjust", methods=["POST"])
def route_adjust():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = request.form
    back = f.get("back") if f.get("back") in ("list", "room", "approve") else "list"
    rs = SL._int((f.get("amount") or "").replace(",", "").strip())
    try:
        add_discount(con, _who(u), SL._int(f.get("slip_id")), SL._int(f.get("item_id")), (rs or 0) * 100 if rs is not None else None,
                     f.get("free") == "1", (f.get("reason") or "").strip(), f.get("note") or "")
    except AdjustError as ex:
        return _back(back, err=str(ex))
    return _back(back, ok="Chhoot likh di — manzoori ke liye gayi.")


@bp.route("/finance/slips/radd", methods=["POST"])
def route_radd():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    f = request.form
    back = f.get("back") if f.get("back") in ("list", "late") else "list"
    try:
        add_cancel(con, _who(u), SL._int(f.get("slip_id")), f.get("clinic_id") or "", (f.get("how") or "").strip(), f.get("note") or "")
    except AdjustError as ex:
        return _back(back, err=str(ex))
    return _back(back, ok="Radd likh diya — manzoori ke liye gaya.")


@bp.route("/finance/slips/decide/<int:aid>", methods=["POST"])
def route_decide(aid):
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    ok = request.form.get("act") == "approve"
    to = "/finance/slips/report" if request.form.get("back") == "report" else None
    try:
        st = decide(con, _who(u), aid, ok, request.form.get("note") or "")
    except AdjustError as ex:
        return redirect(to + "?err=" + SL._q(str(ex)), code=303) if to else _back("approve", err=str(ex))
    msg = ("Approved." if st == "approved" else "Rejected.") if to else ("Manzoor." if st == "approved" else "Na-manzoor.")
    return redirect(to + "?ok=" + SL._q(msg), code=303) if to else _back("approve", ok=msg)


@bp.route("/finance/slips/api/day")
def api_day():
    u, err = _require("maker", "checker", unit=UNIT)
    if err:
        return err
    SL = _SL()
    con = _db()
    SL.ensure(con)
    series = request.args.get("series") if request.args.get("series") in SL.SERIES_NAME else "opd"
    p = propose_day(con, series, request.args.get("no"), request.args.get("id"))
    if not p:
        return jsonify(ok=True, propose=None)
    return jsonify(ok=True, propose=p[0], word=SL._day_word(p[0]) + " (" + SL._dmy(p[0])[:6] + ")", why=p[1], why_en=p[2])


@bp.route("/finance/slips/discounts")
def owner_month():
    """The owner's page: the month's discounts, free lines and radd -- who asked, who approved."""
    u, err = _require("checker", "maker", unit=UNIT)
    SL = _SL()
    if err:
        return SL._shell("Discounts", SL._denied(), "en")
    con = _db()
    SL.ensure(con)
    ensure(con)
    if "checker" not in SL._roles(u) and not is_approver(con, u):
        return SL._shell("Discounts", SL._denied(), "en")
    ym = request.args.get("m") or SL._today()[:7]
    try:
        dt.date.fromisoformat(ym + "-01")
    except ValueError:
        ym = SL._today()[:7]
    return SL._shell("Discounts & free — %s" % dt.date.fromisoformat(ym + "-01").strftime("%b %Y"), month_html(con, ym), "en",
                     back="/finance/clinic/money", back_label="← Money")


def month_html(con, ym):
    SL = _SL()
    rows = month_rows(con, ym)
    y, m = int(ym[:4]), int(ym[5:])
    prev = "%04d-%02d" % ((y, m - 1) if m > 1 else (y - 1, 12))
    nxt = "%04d-%02d" % ((y, m + 1) if m < 12 else (y + 1, 1))
    disc = [r for r in rows if r["kind"] in ("discount", "free")]
    canc = [r for r in rows if r["kind"] == "cancel"]
    tot = lambda rs, st: sum(r["amount_p"] for r in rs if r["state"] == st)
    out = ['<p class="nav"><a href="/finance/slips/discounts?m=%s">← %s</a> · <b>%s</b> · <a href="/finance/slips/discounts?m=%s">%s →</a></p>'
           % (prev, prev, ym, nxt, nxt)]
    out.append('<div class="card"><p style="font-size:19px;margin:0"><b>%s</b> approved on %d line%s · %s pending · %d rejected · %d radd after billing</p></div>'
               % (SL._rs(tot(disc, "approved")), len([r for r in disc if r["state"] == "approved"]), "" if len(disc) == 1 else "s",
                  SL._rs(tot(disc, "pending")), len([r for r in rows if r["state"] == "rejected"]), len([r for r in canc if r["state"] == "approved"])))
    by_reason, by_who = {}, {}
    for r in disc:
        if r["state"] == "approved":
            by_reason[r["reason"]] = by_reason.get(r["reason"], 0) + r["amount_p"]
            k = "%s → %s" % (r["made_by"], r["checked_by"])
            by_who[k] = by_who.get(k, 0) + r["amount_p"]
    if by_reason:
        out.append('<details class="sec" open><summary><span>By reason · by who asked → who approved</span></summary><div class="body"><ul>%s</ul><ul>%s</ul></div></details>'
                   % ("".join("<li>%s: %s</li>" % (SL._esc(REASON_EN.get(k, k)), SL._rs(v)) for k, v in sorted(by_reason.items(), key=lambda x: -x[1])),
                      "".join("<li>%s: %s</li>" % (SL._esc(k), SL._rs(v)) for k, v in sorted(by_who.items(), key=lambda x: -x[1]))))
    head = "<tr><th>Day</th><th>Parchi</th><th>ID</th><th>Line</th><th>Rate</th><th>Discount</th><th>Why</th><th>Asked</th><th>Decided</th></tr>"
    body = "".join("<tr%s><td>%s</td><td>%s %d</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
        ' class="dim"' if r["state"] == "rejected" else "", SL._dmy(r["day"])[:6], "OPD" if r["series"] == "opd" else "XP", r["slip_no"],
        SL._esc(r["sid_clinic"] or "—"),
        SL._esc((r["item_name"] or "—") + ((" " + r["side"]) if r.get("side") else "")) if r["kind"] != "cancel" else "radd after billing",
        SL._rs(r["price_p"]) if r.get("price_p") else "—",
        ("FREE" if r["kind"] == "free" else SL._rs(r["amount_p"])) if r["kind"] != "cancel" else SL._esc(CANCEL_HOW.get(r["cancel_how"], ("", ""))[1]),
        SL._esc(REASON_EN.get(r["reason"], r["note"] or "")), SL._esc(r["made_by"]),
        SL._esc(("%s %s" % (r["state"], r["checked_by"])).strip() + ((" — " + r["check_note"]) if r["check_note"] else ""))) for r in rows)
    out.append('<details class="sec" open><summary><span>Every line</span><span class="badge">%d</span></summary><div class="body"><div class="tw">'
               '<table class="grid">%s%s</table></div></div></details>' % (len(rows), head, body or "<tr><td colspan=9>Nothing this month.</td></tr>"))
    return "".join(out)


def approve_html(con, u, english=False):
    """The approver's list: one line per pending entry, Approve / Reject (a reason for a reject). Own entries are shown
    without buttons -- someone else decides those."""
    SL = _SL()
    me = _who(u).lower()
    rows = pending(con)
    if not rows:
        return '<p class="sm">%s</p>' % ("Nothing waiting." if english else "Kuch baaki nahi.")
    out = []
    for r in rows:
        what = ("Radd after billing — %s" % CANCEL_HOW[r["cancel_how"]][1] if english else "Radd — %s" % CANCEL_HOW[r["cancel_how"]][0]) \
            if r["kind"] == "cancel" else ("%s %s: %s" % (r["item_name"] or "", r.get("side") or "",
                                                           "FREE" if r["kind"] == "free" else ("discount " if english else "chhoot ") + SL._rs(r["amount_p"])))
        why = REASON_EN.get(r["reason"], "") if english else REASON_HI.get(r["reason"], "")
        line = '<div class="lrow"><span class="no">%s %d</span> <b>%s</b> <span class="sm">ID %s · %s · %s%s · %s %s</span>' % (
            "OPD" if r["series"] == "opd" else "XP", r["slip_no"], SL._esc(what), SL._esc(r["clinic_id"] or r["sid_clinic"] or "—"),
            SL._esc(SL._dmy(r["day"])[:6]), SL._esc(why), (" — " + SL._esc(r["note"])) if r["note"] else "", SL._esc(r["made_by"]), SL._esc(r["made_at"][11:16]))
        if (r["made_by"] or "").lower() == me or me not in approvers(con):
            line += '<span class="sm">%s</span></div>' % ("(someone else approves)" if english else "(koi aur manzoor karega)")
        else:
            line += ('<form method="post" action="/finance/slips/decide/%d" class="vf">%s<input name="note" placeholder="%s" maxlength="120">'
                     '<button name="act" value="approve">%s</button><button name="act" value="reject" class="x">%s</button></form></div>'
                     % (r["id"], '<input type="hidden" name="back" value="report">' if english else "", "note" if english else "wajah (na ke liye)",
                        "Approve" if english else "Manzoor", "Reject" if english else "Na"))
        out.append(line)
    return "".join(out)
