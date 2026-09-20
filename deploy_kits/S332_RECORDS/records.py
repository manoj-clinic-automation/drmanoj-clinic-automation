#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""records.py -- S332 (session 273, 20-Sep-2026). The 360-degree patient record, step 1.

THE OWNER, 19/20-Sep-2026 (S271_BUILD_BRIEF section 2, every ruling his):
  * he wants any patient's papers when the patient comes again -- many forget them -- WITHOUT
    depending on Docterz. So this page becomes the record: patients of the day at the top, one click
    to a patient's whole history.
  * the FILES live in the clinic's own Google Drive (drmka.ortho@gmail.com). This server keeps only an
    index -- clinic ID, kind, date, Drive file id, source. Files never become public links; every open
    is logged here; only the doctors can open patient records (unit 'records': manoj, bhawna).
  * sections closed until tapped: Timeline, Visits (Docterz: fee / free / concession), X-rays & reports,
    Pharmacy (Sanjeevni bills and medicines, returns shown against the bill; ONLY bills the system is
    sure of -- walk-in and name-only bills are never guessed), Procedures, Hospital & surgery.

STEP 1 (this kit): blood reports. NK Pathology e-mails each report to the clinic mailbox; the mailbox's
Apps Script (VPS_Lab_Files.gs) saves the PDF into Drive -> Clinic Records / Blood / <Mon YYYY> / <DD-Mon>
and tells this server the file id through POST /finance/records/api/lab-file (X-Finance-Cron, the token
the Gmail pushes already use). GET /finance/records/api/reader (same token) tells the script which
account to share the folder with (this box's read-only Drive service account), so opening needs no
public link.

WHAT IT WRITES. Two tables of its own, created on first request (F-303):
    record_file   one row per filed document: clinic ID, kind, day, Drive id, name, source, who/when
    record_open   one row per open: which file, who, when, whether Drive answered
It READS patient_ref, patient_visit, clinic_day_line (Docterz), slip / slip_item / blood_order /
lab_report (the slip tile), sale_item / day_entry / sale_line_item / identity_dispute (Sanjeevni).
It writes none of them. No money is moved, nothing is sent to anyone.

Flask, requests and the standard library. No patient name, no number, no secret in this file (F-185).
"""
import datetime as dt
import glob
import hmac as _hmac
import json
import os
import re
from urllib.parse import quote

from flask import Blueprint, Response, jsonify, redirect, request

bp = Blueprint("records", __name__)

_db = None
_require = None
_audit = None
UNIT = "records"
P = "/finance/records"
_schema_done = False
DRIVE_API = "https://www.googleapis.com/drive/v3/files"
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
KINDS = (("blood", "Blood report"), ("xray", "X-ray"), ("scan", "MRI / CT"), ("other", "Other paper"))
KIND_NAME = dict(KINDS)
SURE_CONF = 0.95          # a pharmacy line below this, and never checked by a person, is not shown

SCHEMA = """
CREATE TABLE IF NOT EXISTS record_file (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  clinic_id   TEXT NOT NULL,
  kind        TEXT NOT NULL CHECK (kind IN ('blood','xray','scan','other')),
  day         TEXT NOT NULL,
  drive_id    TEXT NOT NULL DEFAULT '',
  file_name   TEXT NOT NULL DEFAULT '',
  mime        TEXT NOT NULL DEFAULT '',
  bytes       INTEGER NOT NULL DEFAULT 0,
  source      TEXT NOT NULL,
  source_ref  TEXT NOT NULL,
  state       TEXT NOT NULL DEFAULT 'ok' CHECK (state IN ('ok','void')),
  note        TEXT NOT NULL DEFAULT '',
  added_by    TEXT NOT NULL DEFAULT '',
  added_at    TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS record_file_src ON record_file(source, source_ref);
CREATE INDEX IF NOT EXISTS record_file_cid ON record_file(clinic_id, day);
CREATE TABLE IF NOT EXISTS record_open (
  id       INTEGER PRIMARY KEY AUTOINCREMENT,
  file_id  INTEGER NOT NULL,
  who      TEXT NOT NULL DEFAULT '',
  at       TEXT NOT NULL DEFAULT '',
  ok       INTEGER NOT NULL DEFAULT 0
);
"""


def init(app, db_getter, require_fn, audit_fn=None, unit="records"):
    """Mount only; touches no database (F-303)."""
    global _db, _require, _audit, UNIT
    _db, _require, _audit, UNIT = db_getter, require_fn, audit_fn, unit
    app.register_blueprint(bp)
    return bp


def ensure(con):
    global _schema_done
    if not _schema_done:
        con.executescript(SCHEMA)
        con.commit()
        _schema_done = True


# ---------------------------------------------------------------- small helpers
def _now():
    v = os.environ.get("RECORDS_NOW", "") or os.environ.get("SLIP_NOW", "")
    if v:
        try:
            return dt.datetime.fromisoformat(v)
        except ValueError:
            pass
    return dt.datetime.now().replace(microsecond=0)          # the box's clock is IST


def _stamp():
    return _now().strftime("%Y-%m-%d %H:%M:%S")


def _today():
    return _now().date().isoformat()


def _esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def _rs(p):
    return "₹{:,}".format(int(round((p or 0) / 100.0)))


def _dmy(iso):
    try:
        return dt.date.fromisoformat(str(iso)[:10]).strftime("%d-%b-%Y")
    except (ValueError, TypeError):
        return iso or "—"


def _clean_id(v):
    v = re.sub(r"\s+", "", str(v or ""))
    return v[:12] if re.fullmatch(r"[0-9A-Za-z\-/]{1,12}", v or "") else ""


def _who(u):
    return (u or {}).get("user", "")


def _tables(con):
    return {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _rows(con, sql, args=()):
    """A read that never breaks the page: a missing table or column is an empty section."""
    try:
        return [dict(r) for r in con.execute(sql, args)]
    except Exception:                                    # noqa: BLE001
        return []


def _cron_ok():
    tok = os.environ.get("FINANCE_CRON_TOKEN", "")
    given = request.headers.get("X-Finance-Cron", "")
    return bool(tok and given and _hmac.compare_digest(str(given), str(tok)))


def _denied():
    return Response(_shell("Patient records", '<div class="bad">This page is for the doctors only.</div>'),
                    status=403, mimetype="text/html")


def _gate():
    u, err = _require("checker", unit=UNIT)
    return u, (None if u else _denied())


# ---------------------------------------------------------------- Drive (read-only, service account)
def _sa_key():
    for d in ("/root/wa", "/root/wa/keys", "/root"):
        for path in sorted(glob.glob(os.path.join(d, "*.json"))):
            try:
                if b"service_account" in open(path, "rb").read():
                    return path
            except OSError:
                continue
    return ""


def sa_email():
    k = _sa_key()
    if not k:
        return ""
    try:
        return json.load(open(k)).get("client_email", "")
    except (OSError, ValueError):
        return ""


_cred = [None]


def drive_media(drive_id):
    """(bytes, mime) of one Drive file, or (None, reason). RECORDS_DRIVE_STUB=<dir> serves the walk."""
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", drive_id or ""):
        return None, "bad id"
    stub = os.environ.get("RECORDS_DRIVE_STUB", "")
    if stub:
        p = os.path.join(stub, drive_id)
        return (open(p, "rb").read(), "application/pdf") if os.path.exists(p) else (None, "not found")
    try:
        import requests
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request
        if _cred[0] is None or not _cred[0].valid:
            key = _sa_key()
            if not key:
                return None, "no service-account key on this box"
            c = service_account.Credentials.from_service_account_file(key, scopes=DRIVE_SCOPES)
            c.refresh(Request())
            _cred[0] = c
        h = {"Authorization": "Bearer " + _cred[0].token}
        r = requests.get(DRIVE_API + "/" + drive_id, params={"alt": "media"}, headers=h, timeout=60)
        if r.status_code != 200:
            return None, "Drive said %s" % r.status_code
        return r.content, r.headers.get("Content-Type", "application/octet-stream")
    except Exception as ex:                              # noqa: BLE001
        return None, "Drive not reachable (%s)" % type(ex).__name__


# ---------------------------------------------------------------- the patient, read-only
def person(con, cid):
    r = _rows(con, "SELECT name, phone_last4, merged_into FROM patient_ref WHERE clinic_id=? "
                   "ORDER BY (merged_into IS NULL OR merged_into='') DESC, id LIMIT 1", (cid,))
    if r:
        return {"name": r[0]["name"] or "", "last4": r[0]["phone_last4"] or "",
                "merged": r[0]["merged_into"] or ""}
    d = _rows(con, "SELECT patient FROM clinic_day_line WHERE clinic_id=? AND patient<>'' "
                   "ORDER BY business_date DESC LIMIT 1", (cid,))
    if d:
        return {"name": d[0]["patient"], "last4": "", "merged": ""}
    return None


SECTION_WORD = {"consult": "Consultation", "revisit": "Free revisit", "concession": "Free / concession",
                "xray": "X-ray", "proc": "Procedure"}


def _mode(m):
    m = (m or "").strip()
    return {"cash": "cash", "upi": "UPI"}.get(m.lower(), m)


def visits(con, cid):
    """Docterz's day lines for this ID (from 15-Jun-2026), plus earlier visit dates the visit list knows."""
    out = []
    for r in _rows(con, "SELECT business_date d, section, amount_p, mode FROM clinic_day_line WHERE clinic_id=? "
                        "ORDER BY business_date DESC, section", (cid,)):
        what = SECTION_WORD.get(r["section"], r["section"])
        money = (" " + _rs(r["amount_p"]) + (" " + _mode(r["mode"]) if r["mode"] else "")) if r["amount_p"] else ""
        out.append({"day": r["d"], "section": r["section"], "text": what + money})
    have = {v["day"] for v in out}
    for r in _rows(con, "SELECT DISTINCT visit_date d FROM patient_visit WHERE clinic_id=? ORDER BY visit_date DESC", (cid,)):
        if r["d"] and r["d"] not in have:
            out.append({"day": r["d"], "section": "visit", "text": "Visit"})
    out.sort(key=lambda v: v["day"], reverse=True)
    return out


def slips(con, cid):
    out = []
    for s in _rows(con, "SELECT id, series, slip_no, day FROM slip WHERE clinic_id=? AND state='ok' "
                        "ORDER BY day DESC, id DESC", (cid,)):
        items = _rows(con, "SELECT kind, name, side FROM slip_item WHERE slip_id=? ORDER BY sort, id", (s["id"],))
        s["items"] = items
        out.append(s)
    return out


def files(con, cid):
    ensure(con)
    return _rows(con, "SELECT * FROM record_file WHERE clinic_id=? AND state='ok' ORDER BY day DESC, id DESC", (cid,))


def blood(con, cid):
    orders = _rows(con, "SELECT day, outcome FROM blood_order WHERE clinic_id=? AND state='ok' ORDER BY day DESC", (cid,))
    reports = _rows(con, "SELECT msg_id, substr(received_at,1,10) d, received_at FROM lab_report WHERE clinic_id=? "
                         "ORDER BY received_at DESC", (cid,))
    return orders, reports


def pharmacy(con, cid):
    """Sanjeevni bills that the system is SURE belong to this clinic ID: the daily sheet's line is either
    checked by a person or matched at >= 0.95, and the bill is not in an open identity dispute. Walk-in
    (WA...) and name-only bills carry another ID and never reach here. Returns are shown under the
    patient's latest earlier bill that holds the same medicine; otherwise under their own date."""
    disputed = {r["bill_no"] for r in _rows(con, "SELECT bill_no FROM identity_dispute WHERE status='open' AND clinic_id=?", (cid,))}
    rows = _rows(con, """
        SELECT s.service, s.source_ref bill, s.amount_p, s.mode, d.business_date day, s.confidence, s.verified_by
        FROM sale_item s JOIN patient_ref p ON p.id = s.patient_ref_id JOIN day_entry d ON d.id = s.day_entry_id
        WHERE p.clinic_id = ? AND s.service IN ('pharmacy','pharmacy_return')
          AND ((s.verified_by IS NOT NULL AND s.verified_by <> '') OR s.confidence >= ?)
        ORDER BY d.business_date DESC, s.source_ref DESC""", (cid, SURE_CONF))
    bills, rets = [], []
    for r in rows:
        if r["bill"] in disputed:
            continue
        lines = _rows(con, "SELECT item_name, item_key, qty_raw, amount_p FROM sale_line_item "
                           "WHERE bill_no=? AND business_date=? ORDER BY seq", (r["bill"], r["day"]))
        r["lines"] = lines
        r["returns"] = []
        (rets if r["service"] == "pharmacy_return" else bills).append(r)
    loose = []
    for cn in rets:
        keys = {l["item_key"] for l in cn["lines"] if l.get("item_key")}
        home = None
        for b in bills:                                  # newest first -> the latest earlier bill wins
            if b["day"] <= cn["day"] and keys & {l["item_key"] for l in b["lines"] if l.get("item_key")}:
                home = b
                break
        (home["returns"].append(cn) if home else loose.append(cn))
    return bills, loose


def procedures(visit_list, slip_list):
    out = [{"day": v["day"], "text": v["text"]} for v in visit_list if v["section"] == "proc"]
    for s in slip_list:
        for it in s["items"]:
            if it["kind"] == "proc":
                out.append({"day": s["day"], "text": "%s%s (slip %s)" % (it["name"] or "Procedure",
                            " " + it["side"] if it["side"] else "", s["slip_no"])})
    out.sort(key=lambda x: x["day"], reverse=True)
    return out


# ---------------------------------------------------------------- the pages
@bp.route(P)
def home():
    u, err = _gate()
    if err:
        return err
    con = _db()
    ensure(con)
    q = (request.args.get("q") or "").strip()
    if q:
        cid = _clean_id(q)
        if cid and re.fullmatch(r"\d{1,8}", cid):
            return redirect("%s/p/%s" % (P, quote(cid)), code=303)
    return _home_html(con, q)


def _home_html(con, q):
    today = _today()
    body = ['<form class="find" method="get" action="%s"><input name="q" value="%s" placeholder="Clinic ID or name" '
            'autofocus inputmode="search"><button class="go">Open</button></form>' % (P, _esc(q))]
    if q:
        hits = _rows(con, "SELECT clinic_id, name FROM patient_ref WHERE name LIKE ? AND clinic_id<>'' "
                          "AND clinic_id NOT LIKE 'WA%' AND (merged_into IS NULL OR merged_into='') "
                          "ORDER BY CAST(clinic_id AS INTEGER) DESC LIMIT 30", ("%" + q + "%",))
        body.append('<h2>Matches for “%s”</h2>' % _esc(q))
        body.append(_plist([(h["clinic_id"], h["name"], "") for h in hits]) if hits
                    else '<p class="sm">No patient by that name.</p>')
    seen, day_list = set(), []
    for s in _rows(con, "SELECT clinic_id, no_id_name, series, slip_no, name_seen FROM slip WHERE day=? AND state='ok' "
                        "ORDER BY id", (today,)):
        cid = s["clinic_id"]
        if not cid or cid in seen:
            continue
        seen.add(cid)
        p = person(con, cid) or {}
        tags = []
        if s["series"] == "xp":
            tags.append("X-ray/Proc")
        day_list.append((cid, p.get("name") or s.get("name_seen") or "(new today)", " · ".join(tags)))
    body.append('<h2>Today · %s</h2>' % _dmy(today))
    body.append(_plist(day_list) if day_list else '<p class="sm">No slips logged yet today.</p>')
    since = (dt.date.fromisoformat(today) - dt.timedelta(days=3)).isoformat()
    rep = _rows(con, "SELECT clinic_id, MAX(day) d, COUNT(*) n FROM record_file WHERE kind='blood' AND state='ok' AND day>=? "
                     "GROUP BY clinic_id ORDER BY d DESC LIMIT 60", (since,))
    body.append('<h2>Blood reports filed · last 3 days</h2>')
    body.append(_plist([(r["clinic_id"], (person(con, r["clinic_id"]) or {}).get("name", ""),
                         _dmy(r["d"])[:6] + (" · %d" % r["n"] if r["n"] > 1 else "")) for r in rep])
                if rep else '<p class="sm">None yet.</p>')
    return _shell("Patient records", "".join(body))


def _plist(items):
    return '<div class="plist">' + "".join(
        '<a class="pi" href="%s/p/%s"><b>%s</b><span class="nm">%s</span><span class="tg">%s</span></a>'
        % (P, quote(c), _esc(c), _esc(n), _esc(t)) for c, n, t in items) + "</div>"


@bp.route(P + "/p/<cid>")
def patient_page(cid):
    u, err = _gate()
    if err:
        return err
    cid = _clean_id(cid)
    if not cid:
        return redirect(P, code=303)
    con = _db()
    ensure(con)
    return _patient_html(con, cid)


def _sec(key, title, badge, body):
    return ('<details class="sec" id="%s"><summary><span>%s</span><span class="badge">%s</span></summary>'
            '<div class="body">%s</div></details>' % (key, _esc(title), _esc(badge), body))


def _file_link(f):
    if not f["drive_id"]:
        return '<span class="sm">e-mail had no PDF</span>'
    return '<a class="fl" href="%s/file/%d" target="_blank" rel="noopener">Open</a>' % (P, f["id"])


def _patient_html(con, cid):
    p = person(con, cid)
    v = visits(con, cid)
    sl = slips(con, cid)
    fl = files(con, cid)
    orders, reports = blood(con, cid)
    bills, loose = pharmacy(con, cid)
    pr = procedures(v, sl)
    xr_lines = [x for x in v if x["section"] == "xray"]
    xr_slip = [(s, it) for s in sl for it in s["items"] if it["kind"] == "xray"]
    days = sorted({x["day"] for x in v} | {s["day"] for s in sl})
    name = (p or {}).get("name") or "Name not known yet"
    head = ['<div class="who"><div class="nm">%s</div><div class="id">ID %s%s</div>' % (
        _esc(name), _esc(cid), (" · ••••" + _esc(p["last4"])) if p and p.get("last4") else "")]
    if days:
        head.append('<div class="sm">First seen %s · last %s · %d visit day%s</div>' % (
            _dmy(days[0]), _dmy(days[-1]), len(days), "" if len(days) == 1 else "s"))
    else:
        head.append('<div class="sm">No visit on record yet (Docterz lines start 15-Jun-2026).</div>')
    head.append('<div class="cnt">%d X-ray%s · %d report file%s · %d pharmacy bill%s · %d procedure%s</div></div>' % (
        len(xr_lines) + len(xr_slip), "" if len(xr_lines) + len(xr_slip) == 1 else "s",
        len(fl), "" if len(fl) == 1 else "s", len(bills), "" if len(bills) == 1 else "s", len(pr), "" if len(pr) == 1 else "s"))
    if p and p.get("merged"):
        head.append('<div class="rem">This ID is marked as merged into %s in the patient list.</div>' % _esc(p["merged"]))
    # ---- timeline
    ev = [(x["day"], "Visit", x["text"]) for x in v]
    for s in sl:
        its = ", ".join((it["name"] or it["kind"]) + (" " + it["side"] if it["side"] else "") for it in s["items"])
        ev.append((s["day"], "Slip", "%s slip %s%s" % ("OPD" if s["series"] == "opd" else "X-ray/Proc", s["slip_no"],
                                                        (": " + its) if its else "")))
    for f in fl:
        ev.append((f["day"], KIND_NAME.get(f["kind"], f["kind"]), _file_link(f)))
    for o in orders:
        ev.append((o["day"], "Blood test", "ordered" + (" — not tested" if o["outcome"] == "not_tested" else "")))
    for b in bills:
        ev.append((b["day"], "Pharmacy", "Bill %s %s" % (_esc(b["bill"]), _rs(b["amount_p"]))
                   + ("".join(" · return %s %s" % (_esc(c["bill"]), _rs(c["amount_p"])) for c in b["returns"]))))
    for c in loose:
        ev.append((c["day"], "Pharmacy", "Return %s %s" % (_esc(c["bill"]), _rs(c["amount_p"]))))
    ev.sort(key=lambda e: e[0], reverse=True)
    tl = _table(["Date", "What", ""], [[_dmy(d), _esc(k), t] for d, k, t in ev[:300]], raw_last=True) if ev \
        else '<p class="sm">Nothing on record yet.</p>'
    # ---- visits
    vt = _table(["Date", "Docterz"], [[_dmy(x["day"]), _esc(x["text"])] for x in v]) if v \
        else '<p class="sm">No Docterz line for this ID.</p>'
    # ---- X-rays & reports
    xr = []
    if fl:
        xr.append(_table(["Date", "Kind", "File", ""], [[_dmy(f["day"]), _esc(KIND_NAME.get(f["kind"], f["kind"])),
                                                        _esc(f["file_name"]), _file_link(f)] for f in fl], raw_last=True))
    else:
        xr.append('<p class="sm">No file filed yet.</p>')
    got = {r["d"] for r in reports}
    filed_days = {f["day"] for f in fl if f["kind"] == "blood"}
    missing = sorted(got - filed_days, reverse=True)
    if missing:
        xr.append('<p class="sm">Lab e-mail received but the PDF is not filed yet: %s.</p>' % ", ".join(_dmy(d) for d in missing))
    if xr_lines or xr_slip:
        rows = [[_dmy(s["day"]), _esc((it["name"] or "X-ray") + (" " + it["side"] if it["side"] else "")), "slip %s" % s["slip_no"]]
                for s, it in xr_slip]
        slip_days = {s["day"] for s, _ in xr_slip}
        rows += [[_dmy(x["day"]), _esc(x["text"]), "Docterz"] for x in xr_lines if x["day"] not in slip_days]
        rows.sort(key=lambda r: dt.datetime.strptime(r[0], "%d-%b-%Y") if r[0] != "—" else dt.datetime.min, reverse=True)
        xr.append('<h3>X-rays taken</h3><p class="sm">The images join this page with the X-ray inbox (next step).</p>')
        xr.append(_table(["Date", "Study", "From"], rows))
    # ---- pharmacy
    if bills or loose:
        ph = []
        for b in bills:
            meds = "".join("<li>%s <span class=\"sm\">%s · %s</span></li>" % (_esc(l["item_name"]), _esc(l["qty_raw"] or ""),
                           _rs(l["amount_p"])) for l in b["lines"]) or '<li class="sm">medicine lines not in the Marg export for this bill</li>'
            rt = "".join('<div class="ret">Return %s · %s · %s<ul>%s</ul></div>' % (
                _esc(c["bill"]), _dmy(c["day"]), _rs(c["amount_p"]),
                "".join("<li>%s</li>" % _esc(l["item_name"]) for l in c["lines"])) for c in b["returns"])
            ph.append('<div class="bill"><div class="bh"><b>%s</b> · %s · %s %s</div><ul>%s</ul>%s</div>' % (
                _esc(b["bill"]), _dmy(b["day"]), _rs(b["amount_p"]), _esc(_mode(b["mode"])), meds, rt))
        for c in loose:
            ph.append('<div class="bill ret"><div class="bh"><b>Return %s</b> · %s · %s</div>'
                      '<p class="sm">No earlier bill of this patient holds these medicines.</p></div>' % (
                          _esc(c["bill"]), _dmy(c["day"]), _rs(c["amount_p"])))
        pht = "".join(ph)
    else:
        pht = '<p class="sm">No Sanjeevni bill is linked to this ID with certainty.</p>'
    # ---- procedures
    prt = _table(["Date", "Procedure"], [[_dmy(x["day"]), _esc(x["text"])] for x in pr]) if pr \
        else '<p class="sm">None on record.</p>'
    hs = '<p class="sm">Nothing recorded yet. Admissions and surgeries get an “Add event” form in a later step.</p>'
    body = "".join(head) + _sec("tl", "Timeline", str(len(ev)) if ev else "", tl) \
        + _sec("vi", "Visits", str(len(v)) if v else "", vt) \
        + _sec("xr", "X-rays & reports", str(len(fl)) if fl else "", "".join(xr)) \
        + _sec("ph", "Pharmacy", str(len(bills)) if bills else "", pht) \
        + _sec("pr", "Procedures", str(len(pr)) if pr else "", prt) \
        + _sec("hs", "Hospital & surgery", "", hs)
    return _shell("%s · %s" % (name, cid), body, back=P, back_label="← Records")


def _table(head, rows, raw_last=False):
    """Cells arrive already escaped by the caller (a file link is markup on purpose)."""
    h = "".join("<th>%s</th>" % _esc(x) for x in head)
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows)
    return '<div class="tw"><table class="grid"><tr>%s</tr>%s</table></div>' % (h, b)


@bp.route(P + "/file/<int:fid>")
def open_file(fid):
    u, err = _gate()
    if err:
        return err
    con = _db()
    ensure(con)
    f = con.execute("SELECT * FROM record_file WHERE id=? AND state='ok'", (fid,)).fetchone()
    if not f or not f["drive_id"]:
        return Response(_shell("Patient records", '<div class="bad">No such file.</div>', back=P, back_label="← Records"),
                        status=404, mimetype="text/html")
    data, mime = drive_media(f["drive_id"])
    con.execute("INSERT INTO record_open(file_id, who, at, ok) VALUES (?,?,?,?)", (fid, _who(u), _stamp(), 1 if data else 0))
    con.commit()
    if data is None:
        return Response(_shell("Patient records", '<div class="bad">The file could not be fetched from Drive: %s.</div>'
                               % _esc(mime), back="%s/p/%s" % (P, quote(f["clinic_id"])), back_label="← Patient"),
                        status=502, mimetype="text/html")
    safe = re.sub(r'[^A-Za-z0-9 ._\-]', "_", f["file_name"] or "report.pdf")[:120]
    return Response(data, mimetype=(f["mime"] or mime or "application/octet-stream"),
                    headers={"Content-Disposition": 'inline; filename="%s"' % safe,
                             "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


# ---------------------------------------------------------------- the mailbox's doors (cron token)
@bp.route(P + "/api/reader", methods=["GET"])
def api_reader():
    """Which account the Apps Script shares 'Clinic Records' with: this box's read-only service account."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    e = sa_email()
    return jsonify(ok=bool(e), email=e)


_DAY = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?")


@bp.route(P + "/api/lab-file", methods=["POST"])
def api_lab_file():
    """VPS_Lab_Files.gs: one entry per saved report PDF (or per report e-mail that had none):
    msg_id, clinic_id, received_at, drive_id, file_name, mime, bytes. Idempotent on (msg_id, drive_id)."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    rows = j.get("files") if isinstance(j.get("files"), list) else [j]
    con = _db()
    ensure(con)
    n = bad = 0
    for x in rows[:200]:
        mid = str(x.get("msg_id") or "")[:64]
        cid = _clean_id(x.get("clinic_id"))
        at = str(x.get("received_at") or "")[:19]
        did = str(x.get("drive_id") or "")[:200]
        if not (mid and cid and _DAY.fullmatch(at)) or (did and not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", did)):
            bad += 1
            continue
        try:
            nbytes = max(0, int(x.get("bytes") or 0))
        except (TypeError, ValueError):
            nbytes = 0
        n += con.execute("INSERT OR IGNORE INTO record_file(clinic_id, kind, day, drive_id, file_name, mime, bytes, source, "
                         "source_ref, note, added_by, added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                         (cid, "blood", at[:10], did, str(x.get("file_name") or "")[:200],
                          str(x.get("mime") or "")[:80], nbytes, "lab_mail", mid + "#" + (did or "none"),
                          "" if did else "no PDF in the e-mail", "mailbox", _stamp())).rowcount
    con.commit()
    return jsonify(ok=True, stored=n, refused=bad)


# ---------------------------------------------------------------- the frame
def _shell(title, body, back="/portal", back_label="← Portal"):
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5">
<meta name="robots" content="noindex,nofollow">
<title>%s</title><style>
:root{--ink:#14181c;--mut:#46525b;--line:#9fb0bb;--accent:#14456e;--paper:#fff;--bg:#e4eaee;
 --ok:#2c6e2f;--okbg:#dff0d8;--bad:#9c2a20;--badbg:#fadbd8;--warn:#8a5a00;--warnbg:#fdf0d5}
*{box-sizing:border-box}[hidden]{display:none!important}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.45 "Segoe UI",system-ui,-apple-system,sans-serif}
.top{position:sticky;top:0;z-index:5;display:flex;align-items:center;gap:10px;background:var(--accent);color:#fff;padding:8px 12px}
.top a.back{color:#fff;text-decoration:none;font-weight:600;border:2px solid #fff;border-radius:8px;padding:8px 12px;white-space:nowrap;min-height:44px;display:inline-flex;align-items:center}
.top h1{font-size:17px;margin:0;line-height:1.2;flex:1}.top .d{font-size:14px;opacity:.85;white-space:nowrap}
main{padding:10px 10px 24px;max-width:900px;margin:0 auto}
h2{font-size:16px;color:var(--accent);margin:16px 0 6px}h3{font-size:15px;margin:10px 0 4px;color:var(--mut)}
form.find{display:flex;gap:8px}form.find input{flex:1;font:inherit;font-size:18px;min-height:48px;padding:6px 10px;border:2px solid #6b7b86;border-radius:9px}
button.go{background:var(--accent);color:#fff;border:0;border-radius:9px;padding:0 22px;font-size:17px;font-weight:700;min-height:48px;cursor:pointer}
.plist{display:flex;flex-direction:column;gap:6px}
a.pi{display:flex;gap:10px;align-items:center;background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:10px 12px;color:var(--ink);text-decoration:none;min-height:48px}
a.pi b{font-family:ui-monospace,Consolas,monospace;color:var(--accent);min-width:64px}a.pi .nm{flex:1}a.pi .tg{font-size:13px;color:var(--mut)}
.who{background:var(--paper);border:2px solid var(--accent);border-radius:10px;padding:10px 12px;margin:0 0 10px}
.who .nm{font-size:20px;font-weight:700}.who .id{font-family:ui-monospace,Consolas,monospace;color:var(--accent)}
.cnt{font-size:14px;margin-top:4px}
details.sec{background:var(--paper);border:2px solid var(--line);border-radius:10px;margin:0 0 8px}
details.sec>summary{list-style:none;cursor:pointer;display:flex;justify-content:space-between;align-items:center;padding:10px 12px;font-weight:700;color:var(--accent)}
details.sec>summary::-webkit-details-marker{display:none}
details.sec>summary::after{content:"\\25BE";margin-left:8px}details.sec[open]>summary::after{content:"\\25B4"}
details.sec[open]>summary{border-bottom:1px solid var(--line)}
.body{padding:10px 12px}
.badge:empty{display:none}.badge{font-size:13px;font-weight:600;color:var(--mut);background:#eef2f4;border-radius:12px;padding:2px 9px;margin-left:auto}
.tw{overflow-x:auto}table.grid{border-collapse:collapse;width:100%%;font-size:14px}
.grid th,.grid td{border:1px solid #cbd6dd;padding:5px 7px;text-align:left;vertical-align:top}.grid th{background:#eef2f4}
a.fl{font-weight:700;color:var(--accent)}
.bill{border-bottom:1px solid #e1e7eb;padding:6px 0}.bill ul{margin:2px 0;padding-left:1.2em;font-size:14px}
.ret{background:var(--warnbg);border-left:4px solid var(--warn);padding:4px 8px;margin:4px 0;font-size:14px;border-radius:5px}
.sm{font-size:13px;color:var(--mut)}
.bad{background:var(--badbg);border-left:6px solid var(--bad);padding:8px 12px;border-radius:6px}
.rem{background:var(--warnbg);border-left:6px solid var(--warn);padding:8px 12px;margin:6px 0;border-radius:6px;font-size:15px}
</style></head><body><header class="top"><a class="back" href="%s">%s</a><h1>%s</h1><span class="d">%s</span></header>
<main>%s</main><script>
[].forEach.call(document.querySelectorAll('details.sec'),function(d){d.addEventListener('toggle',function(){
 if(d.open){[].forEach.call(document.querySelectorAll('details.sec'),function(o){if(o!==d)o.open=false;});}});});
</script></body></html>""" % (_esc(title), _esc(back), _esc(back_label), _esc(title), _dmy(_today())[:6], body)
