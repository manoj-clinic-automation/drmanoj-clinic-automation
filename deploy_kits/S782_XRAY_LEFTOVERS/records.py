#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""records.py -- S332 (session 273, 20-Sep-2026). The 360-degree patient record, step 1.
S345 (same session): step 5 -- outside MRI/CT, discharge papers and outside reports added by staff (Check karein ->
Kagaz jodein) or by the doctor on the patient page, and the doctor's "Add event" for hospital stays and surgeries,
with an optional paper. A file is kept on the box (0700 inbox) only until the mailbox script carries it to Drive
(GET /api/upload-pending, GET /api/upload-file/<id>, POST /api/upload-done); then the box's copy is deleted.
S344 (same session): step 4 -- photos and PDFs patients send on the clinic WhatsApp. The receiver's raw logs
(/root/wa/wa_logs, read-only) are swept when the mailbox script asks (GET /api/wa-pending); the script saves each
file into Drive -> Clinic Records / WhatsApp and reports the Drive id (POST /api/wa-file). The sender is kept only
as the salted mobile fingerprint + last four digits; the patients on that number are SUGGESTED. Reception confirms
in Check karein -- right patient + Blood / X-ray / MRI-CT / Other / Not a report -- and only then is it filed.
S340 (same session): step 3, "Check karein" -- one reception queue (unit 'checks': alisha, shivani, reception,
shavez; the doctors) at /finance/checks, in Hindi, one tap per answer with who and when, oldest first; and the
doctors' ONE collapsed line on the records page ("all clear" / "N need a look, oldest D days"). Items now:
a blood test ordered with no report after 2 days; a lab report whose clinic ID the clinic has never seen; a lab
e-mail with no PDF. X-ray and WhatsApp items join when those steps go live. Answers live in record_check.
S335 (same session): Drive reads go through records_drive.py under the venv python -- the web app's
system python has no Google libraries (found live: the first open answered ModuleNotFoundError).
S333 (same session): step 2's READ-ONLY X-ray test run -- /finance/records/xray-test reads the Drive folder
"Clinic Records / X-ray test" through the read-only reader account and shows, per file: original name ->
proposed name -> matched or not, and whether the X-ray PC's clock agrees with the slip. It renames NOTHING.
The mailbox script (VPS_Lab_Files.gs, S333 build) makes the X-ray folders and tells this server their ids
through POST /finance/records/api/folders.

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

S752 (S404, 08-Nov-2026, the owner's 'build it'): the pictures parked in Drive's "X-ray check" folder are re-tried on
every run -- filed when their ID is now on the day's X-ray list, or (once the day is over) when a name-only picture is
word for word the name of one X-ray patient of that day and no other shares a word of it; anything weaker is a
suggestion on Check karein, never filed by itself.

S757 (S413, 09-Nov-2026, D875 -- the owner's FINAL on mock-up YBLGcgEAGi18QB9PL1bRL4 v9): Check karein is drawn by check_screens.py
beside this file -- each parked X-ray picture with its photo and that day's patients (tap + 'Haan' answers it the S373 way),
Shavez's one queue of X-ray photos and lab reports with no blood slip, and the owner's page /finance/records/xray-check (four
tiles). Without check_screens (or on any fault in it) the page is the list it was; ?list=1 always shows that list.
S772 (S422, 10-Nov-2026, the owner's 'do all thats possible'): once xray_filmdate.py has read a parked X-ray's film, the
picture is planned on the date (and ID) printed on it, else on its ID's one X-ray day with no photo -- only for a patient
confirmed by the film's ID or a strict name; after the corrected copy is filed, its older parked copies and a copy filed
to another patient under a mistyped ID go to the duplicates folder -- never deleted.
S776 (S422, 10-Nov-2026, the owner's 'no work for staff in Check karein as much as possible'): a parked picture nothing
else placed is filed by the film's ID with a whole-word name and no one-digit neighbour that day, by a whole-word name
shared with ONE X-ray patient of the day whose photo is missing, or on a patient who came that day with no X-ray billed.
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
CREATE TABLE IF NOT EXISTS record_setting (
  key      TEXT PRIMARY KEY,
  value    TEXT NOT NULL DEFAULT '',
  set_at   TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS record_check (
  key          TEXT PRIMARY KEY,
  kind         TEXT NOT NULL,
  clinic_id    TEXT NOT NULL DEFAULT '',
  answer       TEXT NOT NULL,
  note         TEXT NOT NULL DEFAULT '',
  answered_by  TEXT NOT NULL DEFAULT '',
  answered_at  TEXT NOT NULL DEFAULT ''
);
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


def _helper(what, fid):
    """(bytes, None) or (None, reason): one Drive read through records_drive.py under the venv python (S335 --
    the web app's own python has no Google libraries). RECORDS_DRIVE_STUB=<dir> serves the walk in-process."""
    import subprocess
    here = os.path.dirname(os.path.abspath(__file__))
    py = os.environ.get("RECORDS_VENV", "/root/wa/venv/bin/python3")
    try:
        p = subprocess.run([py, "-B", os.path.join(here, "records_drive.py"), what, fid],
                           capture_output=True, timeout=150)
    except Exception as ex:                              # noqa: BLE001
        return None, "Drive helper did not run (%s)" % type(ex).__name__
    if p.returncode != 0:
        return None, (p.stderr.decode("utf-8", "replace").strip().splitlines() or ["Drive helper failed"])[-1][:160]
    return p.stdout, None


def drive_media(drive_id):
    """(bytes, mime) of one Drive file, or (None, reason)."""
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", drive_id or ""):
        return None, "bad id"
    stub = os.environ.get("RECORDS_DRIVE_STUB", "")
    if stub:
        p = os.path.join(stub, drive_id)
        return (open(p, "rb").read(), "application/pdf") if os.path.exists(p) else (None, "not found")
    data, why = _helper("media", drive_id)
    return (data, "application/octet-stream") if data is not None else (None, why)


def drive_list(folder_id):
    """(files, None) for the plain files in one Drive folder, or (None, reason). Stub: <dir>/list_<id>.json."""
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", folder_id or ""):
        return None, "folder not set up yet"
    stub = os.environ.get("RECORDS_DRIVE_STUB", "")
    if stub:
        p = os.path.join(stub, "list_%s.json" % folder_id)
        return (json.load(open(p)), None) if os.path.exists(p) else ([], None)
    data, why = _helper("list", folder_id)
    if data is None:
        return None, why
    try:
        return json.loads(data.decode("utf-8")), None
    except ValueError:
        return None, "Drive helper gave no list"


def setting(con, key):
    ensure(con)
    r = con.execute("SELECT value FROM record_setting WHERE key=?", (key,)).fetchone()
    return r["value"] if r else ""


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
    body = [_check_line_html(con), '<p style="margin:0 0 10px"><a class="view" href="%s/xray-check">X-ray photos &amp; lab reports '
            '\u2192</a></p>' % P,                         # S757 (D875): his four tiles
            '<form class="find" method="get" action="%s"><input name="q" value="%s" placeholder="Clinic ID or name" '
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
    body.append('<p class="sm" style="margin-top:18px"><a href="%s/xray-test">X-ray test run (read-only)</a></p>' % P)
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
    evs = events(con, cid)
    waiting = _rows(con, "SELECT kind, day FROM record_upload WHERE clinic_id=? AND state='new' AND event_id IS NULL", (cid,))
    paper_form, event_form = _add_forms(cid)
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
    for e in evs:
        ev.append((e["day"], "Hospital", _esc(" \u00b7 ".join(x for x in (e["hospital"], e["what"]) if x))))
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
    if waiting:
        xr.append('<p class="sm">On its way to Drive: %s.</p>' % ", ".join("%s %s" % (KIND_NAME.get(w["kind"], w["kind"]), _dmy(w["day"])) for w in waiting))
    xr.append(paper_form)
    if xr_lines or xr_slip:
        rows = [[_dmy(s["day"]), _esc((it["name"] or "X-ray") + (" " + it["side"] if it["side"] else "")), "slip %s" % s["slip_no"]]
                for s, it in xr_slip]
        slip_days = {s["day"] for s, _ in xr_slip}
        rows += [[_dmy(x["day"]), _esc(x["text"]), "Docterz"] for x in xr_lines if x["day"] not in slip_days]
        rows.sort(key=lambda r: dt.datetime.strptime(r[0], "%d-%b-%Y") if r[0] != "—" else dt.datetime.min, reverse=True)
        xr.append('<h3>X-rays taken</h3>' + xray_gallery(con, cid))
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
    if evs:
        hs = _table(["Date", "Hospital", "What was done", "Note", "Paper"], [[
            _dmy(e["day"]), _esc(e["hospital"]), _esc(e["what"]), _esc(e["note"]),
            (" ".join(_file_link(f) for f in e["files"]) + (' <span class="sm">on its way to Drive</span>' if e["waiting"] else "")) or "\u2014"]
            for e in evs])
    else:
        hs = '<p class="sm">Nothing recorded yet.</p>'
    hs += event_form
    m = request.args.get("msg", "")
    body = ('<div class="okb">%s</div>' % _esc(m) if m else "") + "".join(head) + _sec("tl", "Timeline", str(len(ev)) if ev else "", tl) \
        + _sec("vi", "Visits", str(len(v)) if v else "", vt) \
        + _sec("xr", "X-rays & reports", str(len(fl)) if fl else "", "".join(xr)) \
        + _sec("ph", "Pharmacy", str(len(bills)) if bills else "", pht) \
        + _sec("pr", "Procedures", str(len(pr)) if pr else "", prt) \
        + _sec("hs", "Hospital & surgery", str(len(evs)) if evs else "", hs)
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


# ---------------------------------------------------------------- S333: the X-ray test run (read-only)
IMG = re.compile(r"\.(jpe?g|png|bmp|tiff?|dcm)$", re.I)
_LEAD = re.compile(r"^\s*(\d{1,8})(?!\d)")
# S351: the staff write the clinic ID at the END of the name -- "NAME 1234.jpg", a second view as
# "NAME 1234 ..jpg" -- and sometimes leave it off the second file altogether. The ID is therefore the ONE
# standalone run of 1-8 digits anywhere in the name (start or end); two such runs is an ambiguity, not a
# guess; a file with no number takes the ID of a same-day sister file with the same name stem, and says so.
_NUM = re.compile(r"(?<!\d)(\d{1,8})(?!\d)")


def xray_id(name):
    """(clinic ID or '', how) -- how is 'one' / 'none' / 'many'. The extension never counts."""
    stem = IMG.sub("", name or "")
    nums = _NUM.findall(stem)
    if len(nums) == 1:
        return nums[0], "one"
    return "", ("none" if not nums else "many")


def xray_stem(name):
    """The name with its numbers, dots and extension gone, for the sister rule: 'PHOOL WATI ..jpg' and
    'PHOOL WATI 3527.jpg' share the stem 'PHOOL WATI'."""
    stem = IMG.sub("", name or "")
    stem = _NUM.sub(" ", stem)
    return re.sub(r"[\s._\-]+", " ", stem).strip().upper()


def file_time(f):
    """The file's own time, IST: the picture's own time when the file carries one, else Drive's modified
    time (the X-ray PC's clock, carried by the copy), shifted from UTC."""
    t = ((f.get("imageMediaMetadata") or {}).get("time") or "").strip()
    m = re.fullmatch(r"(\d{4}):(\d{2}):(\d{2}) (\d{2}):(\d{2}):(\d{2})", t)
    if m:
        try:
            return dt.datetime(*map(int, m.groups())), "picture"
        except ValueError:
            pass
    for k in ("modifiedTime", "createdTime"):
        v = f.get(k) or ""
        try:
            u = dt.datetime.strptime(v[:19], "%Y-%m-%dT%H:%M:%S")
            return u + dt.timedelta(hours=5, minutes=30), "file"
        except ValueError:
            continue
    return None, ""


# S353 -- FILMS PER STUDY, the owner's ruling (20-Sep-2026): "usually the AP and lateral are done on a single
# film" -- so a two-view study is ONE film, one photo. The one exception he named: Knee studies (K/S), where both
# knees AP standing go on one film and both knees lateral on a second -- TWO films, two photos. A study's films
# are what the day list counts, so a K/S patient with two pictures reads MATCHED, not "numbered".
TWO_FILM_STUDIES = (("knee studies", ("AP standing", "Lateral")),
                    ("k/s", ("AP standing", "Lateral")))


def study_films(name):
    """The films one study is taken on, in the order they are shot: ['name'] for almost every study,
    ['name -- AP standing', 'name -- Lateral'] for Knee studies (K/S)."""
    low = (name or "").lower()
    for key, films in TWO_FILM_STUDIES:
        if key in low:
            return ["%s \u2014 %s" % (name, f) for f in films]
    return [name]


def _day_studies(con, day, cid):
    """What the chamber recorded for this patient that day: the slip's X-rays in slip order, else
    Docterz's X-ray lines (study not named there). S353: each study expanded to its films."""
    st = []
    for s in _rows(con, "SELECT id, slip_no, logged_at FROM slip WHERE day=? AND clinic_id=? AND series='xp' AND state='ok' "
                        "ORDER BY id", (day, cid)):
        for it in _rows(con, "SELECT name, side FROM slip_item WHERE slip_id=? AND kind='xray' ORDER BY sort, id", (s["id"],)):
            for film in study_films(it["name"] or "X-ray"):
                st.append({"study": film + (" " + it["side"] if it["side"] else ""),
                           "slip": s["slip_no"], "logged_at": s["logged_at"]})
    if st:
        return st, "slip"
    n = _rows(con, "SELECT COUNT(*) n FROM clinic_day_line WHERE business_date=? AND clinic_id=? AND section='xray'", (day, cid))
    k = n[0]["n"] if n else 0
    return [{"study": "X-ray", "slip": None, "logged_at": ""} for _ in range(k)], ("docterz" if k else "")


def _safe(s):
    return re.sub(r'[\\/:*?"<>|]+', " ", str(s or "")).strip()


def xray_plan(con, files):
    """One row per file: original, time, ID, proposed name, verdict. Nothing is renamed."""
    rows, seen, groups = [], {}, {}
    for f in sorted(files, key=lambda x: x.get("name", "")):
        name = f.get("name", "")
        row = {"orig": name, "time": None, "src": "", "cid": "", "proposed": "", "verdict": "", "kind": "", "id": f.get("id", "")}
        rows.append(row)
        if not IMG.search(name) and not (f.get("mimeType") or "").startswith("image/"):
            row.update(verdict="not a picture \u2014 left alone", kind="skip")
            continue
        md5 = f.get("md5Checksum") or ""
        if md5 and md5 in seen:
            row.update(verdict="same picture as %s \u2014 kept once" % seen[md5], kind="dup")
            continue
        if md5:
            seen[md5] = name
        t, src = file_time(f)
        row["time"], row["src"] = t, src
        cid, how = xray_id(name)
        if how == "many":
            row.update(verdict="two numbers in the file name \u2014 which is the clinic ID? \u2192 check folder", kind="check")
            continue
        if not t:
            row.update(verdict="the file has no time \u2192 check folder", kind="check")
            continue
        row["cid"] = cid
        if not cid:
            row["_sister"] = True          # S351: decided below, once every sister is known
            continue
        groups.setdefault((t.date().isoformat(), row["cid"]), []).append(row)
    # S351: a file with no number takes the ID of a same-day sister with the same name stem -- exactly one.
    for r in rows:
        if not r.pop("_sister", False):
            continue
        day = r["time"].date().isoformat()
        st = xray_stem(r["orig"])
        sis = sorted({g["cid"] for g in rows if g is not r and g["cid"] and g["time"] and st
                      and g["time"].date().isoformat() == day and xray_stem(g["orig"]) == st})
        if len(sis) != 1:
            r.update(verdict="no clinic ID in the file name \u2192 check folder", kind="check")
            continue
        r["cid"] = sis[0]
        r["sister"] = next(g["orig"] for g in rows if g is not r and g["cid"] == sis[0] and g["time"]
                           and g["time"].date().isoformat() == day and xray_stem(g["orig"]) == st)
        groups.setdefault((day, r["cid"]), []).append(r)
    for (day, cid), grp in groups.items():
        grp.sort(key=lambda r: r["time"])
        studies, how = _day_studies(con, day, cid)
        ext = (IMG.search(grp[0]["orig"]).group(0).lower() if IMG.search(grp[0]["orig"]) else ".jpg")
        nm = _safe((person(con, cid) or {}).get("name") or "")
        if not studies:
            for r in grp:
                r.update(verdict="ID %s is not in %s's X-ray list \u2192 check folder" % (cid, _dmy(day)), kind="check")
            continue
        same = len(studies) == len(grp)
        for i, r in enumerate(grp):
            label = studies[i]["study"] if same else "X-ray %d" % (i + 1)
            r["proposed"] = " \u00b7 ".join(x for x in (day, cid, nm, _safe(label)) if x) + ext
            if same:
                r.update(verdict="matched (%s)" % ("slip %s" % studies[i]["slip"] if studies[i]["slip"] else "Docterz"),
                         kind="ok")
            else:
                r.update(verdict="%d file(s), %d X-ray(s) on the %s \u2014 numbered, not guessed" % (len(grp), len(studies), how),
                         kind="differ")
            if r.get("sister"):
                r["verdict"] += " \u00b7 ID %s taken from the sister file %s" % (cid, r["sister"])
            lg = studies[0]["logged_at"] if studies else ""
            if lg:
                try:
                    d = (r["time"] - dt.datetime.fromisoformat(lg)).total_seconds() / 60.0
                    r["clock"] = d
                except ValueError:
                    pass
    return rows


@bp.route(P + "/xray-test")
def xray_test():
    u, err = _gate()
    if err:
        return err
    con = _db()
    ensure(con)
    fid = setting(con, "xray_test_id")
    files, why = drive_list(fid)
    if files is None:
        return _shell("X-ray test run", '<div class="bad">%s. The mailbox script makes the folder when it is set up.</div>'
                      % _esc(why), back=P, back_label="\u2190 Records")
    rows = xray_plan(con, files)
    kinds = {}
    for r in rows:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    clocks = sorted(r["clock"] for r in rows if r.get("clock") is not None)
    head = ['<p class="sm">Read-only. Nothing in Drive is renamed or moved. Folder: Clinic Records / X-ray test.</p>',
            '<div class="who"><div class="cnt">%d file(s) \u00b7 <b>%d matched</b> \u00b7 %d numbered (counts differ) \u00b7 '
            '%d to the check folder \u00b7 %d duplicate(s) \u00b7 %d not pictures</div>' % (
                len(rows), kinds.get("ok", 0), kinds.get("differ", 0), kinds.get("check", 0), kinds.get("dup", 0), kinds.get("skip", 0))]
    if clocks:
        med = clocks[len(clocks) // 2]
        verdict = "agrees" if -30 <= med <= 180 else "looks WRONG"
        head.append('<div class="cnt">X-ray PC clock %s: the picture is taken a median %+d min after the slip is logged '
                    '(%d file(s) compared).</div>' % (verdict, int(round(med)), len(clocks)))
    head.append("</div>")
    tbl = _table(["Original name", "File time", "Proposed name", "Verdict"],
                 [[_esc(r["orig"]), (r["time"].strftime("%d-%b %H:%M") + ("" if r["src"] == "file" else " (picture)")) if r["time"] else "\u2014",
                   _esc(r["proposed"]) or "\u2014", '<span class="v-%s">%s</span>' % (r["kind"], _esc(r["verdict"]))] for r in rows])
    return _shell("X-ray test run", "".join(head) + (tbl if rows else '<p class="sm">The folder is empty.</p>'),
                  back=P, back_label="\u2190 Records")


# ---------------------------------------------------------------- S340: "Check karein"
CP = "/finance/checks"
CHECK_UNIT = "checks"
CHECK_FROM = os.environ.get("CHECK_FROM", "2026-09-19")      # the day blood orders began (S330)
REASK_DAYS = 3                                               # "asked the lab" comes back after this, if nothing came
BLOOD_WAIT_DAYS = 2                                          # a report normally arrives the next day
ANS = {
    "blood": [("not_tested", "Test nahi karaya"), ("asked", "Lab se report mangwayi")],
    "lab_id": [("id_ok", "ID sahi hai")],
    "no_pdf": [("asked", "Lab se PDF mangwaya"), ("not_needed", "Zaroorat nahi")],
    "wa": [],                                                # S344: its own form (patient + kind), see _wa_form
    "xray_file": [("not_xray", "Yeh X-ray nahi / bekaar")],   # S373 (+ the ID box, like lab_id)
    "xray_missing": [("asked", "File baad mein daalenge"), ("not_done", "X-ray nahi hua")],   # S373
}
ANS_EN = {"blood": "filed as blood report", "xray": "filed as X-ray", "scan": "filed as MRI/CT", "other": "filed as other paper",
          "not_report": "not a report", "not_tested": "not tested", "asked": "asked the lab", "id_ok": "ID confirmed", "not_needed": "not needed",
          "id_fixed": "ID corrected", "not_xray": "not an X-ray", "not_done": "X-ray not done"}


def _age(day):
    try:
        return (dt.date.fromisoformat(_today()) - dt.date.fromisoformat(day[:10])).days
    except (ValueError, TypeError):
        return 0


def _answers(con):
    ensure(con)
    return {r["key"]: r for r in _rows(con, "SELECT * FROM record_check")}


def _open_by_answer(key, answers):
    a = answers.get(key)
    if not a:
        return True, ""
    if a["answer"] == "asked" and _age(a["answered_at"]) >= REASK_DAYS:
        return True, "%s ne %s ko mangwaya tha" % (a["answered_by"], _dmy(a["answered_at"])[:6])
    return False, ""


def _known_id(con, cid):
    for sql in ("SELECT 1 FROM patient_ref WHERE clinic_id=? LIMIT 1",
                "SELECT 1 FROM clinic_day_line WHERE clinic_id=? LIMIT 1",
                "SELECT 1 FROM slip WHERE clinic_id=? LIMIT 1"):
        if _rows(con, sql, (cid,)):
            return True
    return False


def check_items(con):
    """The open items, oldest first. Computed from the sources every time; an answer closes one."""
    answers = _answers(con)
    today = _today()
    last = (dt.date.fromisoformat(today) - dt.timedelta(days=BLOOD_WAIT_DAYS)).isoformat()
    out = []
    for o in _rows(con, "SELECT day, clinic_id, name_seen, outcome FROM blood_order WHERE state='ok' AND day>=? AND day<=? "
                        "ORDER BY day", (CHECK_FROM, last)):
        if o["outcome"]:                                   # already answered on the Docterz-upload screen
            continue
        end = (dt.date.fromisoformat(o["day"]) + dt.timedelta(days=7)).isoformat() + " 23:59:59"
        if _rows(con, "SELECT 1 FROM lab_report WHERE clinic_id=? AND received_at>=? AND received_at<=? LIMIT 1",
                 (o["clinic_id"], o["day"], end)):
            continue
        key = "bo:%s:%s" % (o["day"], o["clinic_id"])
        op, why = _open_by_answer(key, answers)
        if op:
            out.append({"key": key, "kind": "blood", "clinic_id": o["clinic_id"], "day": o["day"],
                        "name": o["name_seen"] or (person(con, o["clinic_id"]) or {}).get("name", ""),
                        "hi": "Blood test likha tha, report nahi aayi", "en": "blood test ordered, no report",
                        "why": why})
    for f in _rows(con, "SELECT id, clinic_id, day, drive_id FROM record_file WHERE kind='blood' AND state='ok' "
                        "AND day>=? ORDER BY day, id", (CHECK_FROM,)):
        if not f["drive_id"]:
            if not _rows(con, "SELECT 1 FROM record_file WHERE kind='blood' AND state='ok' AND clinic_id=? AND drive_id<>'' "
                              "AND day>=? LIMIT 1", (f["clinic_id"], f["day"])):
                key = "np:%d" % f["id"]
                op, why = _open_by_answer(key, answers)
                if op:
                    out.append({"key": key, "kind": "no_pdf", "clinic_id": f["clinic_id"], "day": f["day"],
                                "name": (person(con, f["clinic_id"]) or {}).get("name", ""),
                                "hi": "Lab ki email mein PDF nahi tha", "en": "lab e-mail had no PDF", "why": why})
        key = "lu:%d" % f["id"]
        if key not in answers and not _known_id(con, f["clinic_id"]):
            out.append({"key": key, "kind": "lab_id", "clinic_id": f["clinic_id"], "day": f["day"], "name": "",
                        "hi": "Lab report ka ID %s hamari list mein nahi" % f["clinic_id"],
                        "en": "lab report for an ID the clinic has never seen", "why": "", "file_id": f["id"]})
    out.extend(wa_items(con))
    try:
        out.extend(xray_items(con))                         # S373
    except Exception:                                   # noqa: BLE001
        pass
    out.sort(key=lambda i: (i["day"], i["key"]))
    return out


# ---------------------------------------------------------------- S344: reports patients send on WhatsApp
def _wa_dir():
    return os.environ.get("RECORDS_WA_DIR", "/root/wa/wa_logs")


def _wa_from():
    return os.environ.get("RECORDS_WA_FROM", "2026-09-20")      # nothing older is swept in
WA_KINDS = (("blood", "Blood"), ("xray", "X-ray"), ("scan", "MRI / CT"), ("other", "Aur kagaz"))
_S3 = re.compile(r"^https://[A-Za-z0-9.\-]*(amazonaws\.com|myop[A-Za-z0-9\-]*)[^\s\"'<>]*$")
WA_SCHEMA = """
CREATE TABLE IF NOT EXISTS record_wa (
  msg_id       TEXT PRIMARY KEY,
  received_at  TEXT NOT NULL,
  mtype        TEXT NOT NULL DEFAULT '',
  link         TEXT NOT NULL DEFAULT '',
  fp           TEXT NOT NULL DEFAULT '',
  last4        TEXT NOT NULL DEFAULT '',
  suggest      TEXT NOT NULL DEFAULT '',
  state        TEXT NOT NULL DEFAULT 'new' CHECK (state IN ('new','saved','filed','not_report','failed')),
  drive_id     TEXT NOT NULL DEFAULT '',
  file_name    TEXT NOT NULL DEFAULT '',
  mime         TEXT NOT NULL DEFAULT '',
  bytes        INTEGER NOT NULL DEFAULT 0,
  clinic_id    TEXT NOT NULL DEFAULT '',
  kind         TEXT NOT NULL DEFAULT '',
  answered_by  TEXT NOT NULL DEFAULT '',
  answered_at  TEXT NOT NULL DEFAULT ''
);
"""
_wa_done = [False]


def wa_ensure(con):
    ensure(con)
    if not _wa_done[0]:
        con.executescript(WA_SCHEMA)
        con.commit()
        _wa_done[0] = True


def _dig(d, *paths):
    for p in paths:
        cur = d
        for k in p.split("."):
            cur = cur.get(k) if isinstance(cur, dict) else None
            if cur is None:
                break
        if cur not in (None, ""):
            return cur
    return None


def _fp_of(phone):
    try:
        import finance_patient_match as fpm
    except Exception:                                    # noqa: BLE001
        return "", ""
    m = fpm.normalise_mobile(phone)
    return (fpm.fingerprint(m, fpm.salt()) if m else ""), (m[-4:] if m else "")


def wa_scan(con):
    """Sweep the WhatsApp receiver's raw logs (read-only) for photos and PDFs patients sent. Each new one
    becomes a record_wa row: the sender kept only as the salted fingerprint and the last four digits,
    the patients on that number SUGGESTED (never chosen)."""
    wa_ensure(con)
    n = 0
    days = sorted(glob.glob(os.path.join(_wa_dir(), "????-??-??.jsonl")))[-4:]
    for fp_path in days:
        if os.path.basename(fp_path)[:10] < _wa_from():
            continue
        try:
            lines = open(fp_path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        for line in lines:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            b = rec.get("body") or {}
            mtype = str(_dig(b, "payload.data.type", "data.type", "payload.type", "type") or "").lower()
            if mtype not in ("image", "document"):
                continue
            if "out" in str(_dig(b, "direction", "payload.direction", "data.direction") or "").lower():
                continue
            mid = str(_dig(b, "payload.id", "payload.message_id", "data.id", "id", "message_id") or "")[:80]
            link = str(_dig(b, "payload.data.context.link", "data.context.link") or "")
            if not mid or not _S3.match(link):
                continue                                   # the first push often has no link yet; a later one does
            if con.execute("SELECT 1 FROM record_wa WHERE msg_id=?", (mid,)).fetchone():
                continue
            phone = _dig(b, "customer_identifier", "payload.customer_identifier", "data.customer_identifier",
                         "customer_number", "payload.customer_number", "payload.data.context.from") or ""
            fp, last4 = _fp_of(phone)
            sug = ",".join(r["clinic_id"] for r in _rows(
                con, "SELECT clinic_id FROM patient_ref WHERE mobile_fp=? AND clinic_id GLOB '[0-9]*' "
                     "AND (merged_into IS NULL OR merged_into='') ORDER BY CAST(clinic_id AS INTEGER) DESC LIMIT 6", (fp,))) if fp else ""
            at = str(rec.get("at") or "")[:19].replace("T", " ")
            con.execute("INSERT OR IGNORE INTO record_wa(msg_id, received_at, mtype, link, fp, last4, suggest) "
                        "VALUES (?,?,?,?,?,?,?)", (mid, at, mtype, link, fp, last4, sug))
            n += 1
    con.commit()
    return n


@bp.route(P + "/api/wa-pending", methods=["GET"])
def api_wa_pending():
    """The mailbox script asks what to save: new photos/PDFs (message id, link, type, time). No phone."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    con = _db()
    wa_scan(con)
    rows = _rows(con, "SELECT msg_id, link, mtype, received_at FROM record_wa WHERE state='new' ORDER BY received_at LIMIT 40")
    return jsonify(ok=True, items=rows)


@bp.route(P + "/api/wa-file", methods=["POST"])
def api_wa_file():
    """The mailbox script saved one into Drive (or could not)."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    con = _db()
    wa_ensure(con)
    n = 0
    for x in (j.get("files") if isinstance(j.get("files"), list) else [j])[:60]:
        mid = str(x.get("msg_id") or "")[:80]
        did = str(x.get("drive_id") or "")
        if did and not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", did):
            continue
        try:
            nb = max(0, int(x.get("bytes") or 0))
        except (TypeError, ValueError):
            nb = 0
        n += con.execute("UPDATE record_wa SET state=?, drive_id=?, file_name=?, mime=?, bytes=? WHERE msg_id=? AND state='new'",
                         ("saved" if did else "failed", did, str(x.get("file_name") or "")[:200],
                          str(x.get("mime") or "")[:80], nb, mid)).rowcount
    con.commit()
    return jsonify(ok=True, stored=n)


def wa_items(con):
    wa_ensure(con)
    out = []
    for w in _rows(con, "SELECT * FROM record_wa WHERE state='saved' ORDER BY received_at"):
        sug = [c for c in (w["suggest"] or "").split(",") if c]
        names = [(c, (person(con, c) or {}).get("name", "")) for c in sug]
        out.append({"key": "wa:" + w["msg_id"], "kind": "wa", "clinic_id": sug[0] if len(sug) == 1 else "",
                    "day": w["received_at"][:10], "name": names[0][1] if len(sug) == 1 else "",
                    "hi": "WhatsApp par %s aaya (••••%s)" % ("photo" if w["mtype"] == "image" else "PDF", w["last4"] or "?"),
                    "en": "WhatsApp %s from ••••%s" % ("photo" if w["mtype"] == "image" else "PDF", w["last4"] or "?"),
                    "why": "", "msg_id": w["msg_id"], "suggest": names})
    return out


def _wa_form(i):
    opts = "".join('<label class="pk"><input type="radio" name="cid" value="%s"%s> %s %s</label>' % (
        _esc(c), " checked" if len(i["suggest"]) == 1 else "", _esc(c), _esc(n)) for c, n in i["suggest"])
    if not i["suggest"]:
        opts = '<div class="sm">Is number par koi mareez nahi mila — ID likhein.</div>'
    kinds = "".join('<button name="a" value="%s">%s</button>' % (k, _esc(l)) for k, l in WA_KINDS)
    return ('<div class="ckb"><a class="view" href="%s/wa/%s" target="_blank" rel="noopener">File dekhein</a></div>'
            '<div class="pks">%s<input name="new_id" inputmode="numeric" placeholder="Doosri clinic ID" maxlength="8"></div>'
            '<div class="ckb">%s<button name="a" value="not_report" class="nr">Report nahi hai</button></div>' % (
                CP, quote(i["msg_id"]), opts, kinds))


@bp.route(CP + "/wa/<mid>")
def checks_wa_view(mid):
    u, err = _check_gate()
    if err:
        return err
    con = _db()
    wa_ensure(con)
    w = con.execute("SELECT rowid, * FROM record_wa WHERE msg_id=? AND drive_id<>''", (mid[:80],)).fetchone()
    if not w:
        return Response(_shell("Check karein", '<div class="bad">File nahi mili.</div>', back=CP, back_label="← Wapas", lang="hi"),
                        status=404, mimetype="text/html")
    data, why = drive_media(w["drive_id"])
    con.execute("INSERT INTO record_open(file_id, who, at, ok) VALUES (?,?,?,?)", (-int(w["rowid"]), _who(u), _stamp(), 1 if data else 0))
    con.commit()
    if data is None:
        return Response(_shell("Check karein", '<div class="bad">Drive se file nahi aayi: %s</div>' % _esc(why), back=CP,
                               back_label="← Wapas", lang="hi"), status=502, mimetype="text/html")
    return Response(data, mimetype=w["mime"] or "application/octet-stream",
                    headers={"Content-Disposition": "inline", "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


def wa_answer(con, u, item, a, form):
    """File the WhatsApp paper to a patient under a kind, or mark it 'not a report'. Returns an error or ''."""
    mid = item["msg_id"]
    if a == "not_report":
        con.execute("UPDATE record_wa SET state='not_report', answered_by=?, answered_at=? WHERE msg_id=? AND state='saved'",
                    (_who(u), _stamp(), mid))
        return ""
    if a not in dict(WA_KINDS):
        return "Jawab samajh nahi aaya, dobara dabayein."
    cid = _clean_id(form.get("new_id")) or _clean_id(form.get("cid"))
    if not (cid and re.fullmatch(r"\d{1,8}", cid) and _known_id(con, cid)):
        return "Mareez chunein ya sahi clinic ID likhein."
    w = con.execute("SELECT * FROM record_wa WHERE msg_id=? AND state='saved'", (mid,)).fetchone()
    if not w:
        return "Yeh pehle hi ho chuka hai."
    con.execute("INSERT OR IGNORE INTO record_file(clinic_id, kind, day, drive_id, file_name, mime, bytes, source, source_ref, "
                "note, added_by, added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (cid, a, w["received_at"][:10], w["drive_id"], w["file_name"], w["mime"], w["bytes"], "whatsapp", mid,
                 "sent by the patient on WhatsApp; confirmed by %s" % _who(u), _who(u), _stamp()))
    con.execute("UPDATE record_wa SET state='filed', clinic_id=?, kind=?, answered_by=?, answered_at=? WHERE msg_id=?",
                (cid, a, _who(u), _stamp(), mid))
    return ""


# ---------------------------------------------------------------- S345: papers staff add + hospital/surgery events
UP_EXT = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".heic": "image/heic",
          ".pdf": "application/pdf"}
UP_MAX = 12 * 1024 * 1024
UP_KINDS = (("scan", "MRI / CT"), ("other", "Discharge / aur kagaz"), ("blood", "Bahar ki blood report"), ("xray", "Bahar ka X-ray"))
UP_FOLDER = {"scan": "Scans", "other": "Papers", "blood": "Blood outside", "xray": "X-ray outside"}
UP_SCHEMA = """
CREATE TABLE IF NOT EXISTS record_upload (
  id           INTEGER PRIMARY KEY AUTOINCREMENT,
  clinic_id    TEXT NOT NULL,
  kind         TEXT NOT NULL CHECK (kind IN ('blood','xray','scan','other')),
  day          TEXT NOT NULL,
  local_name   TEXT NOT NULL DEFAULT '',
  ext          TEXT NOT NULL DEFAULT '',
  bytes        INTEGER NOT NULL DEFAULT 0,
  state        TEXT NOT NULL DEFAULT 'new' CHECK (state IN ('new','saved','failed')),
  drive_id     TEXT NOT NULL DEFAULT '',
  event_id     INTEGER,
  uploaded_by  TEXT NOT NULL DEFAULT '',
  uploaded_at  TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS record_event (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  clinic_id TEXT NOT NULL,
  day       TEXT NOT NULL,
  hospital  TEXT NOT NULL DEFAULT '',
  what      TEXT NOT NULL DEFAULT '',
  note      TEXT NOT NULL DEFAULT '',
  state     TEXT NOT NULL DEFAULT 'ok' CHECK (state IN ('ok','void')),
  added_by  TEXT NOT NULL DEFAULT '',
  added_at  TEXT NOT NULL DEFAULT ''
);
"""
_up_done = [False]


def up_ensure(con):
    ensure(con)
    if not _up_done[0]:
        con.executescript(UP_SCHEMA)
        con.commit()
        _up_done[0] = True


def _inbox():
    return os.environ.get("RECORDS_INBOX", "/root/finance/records_inbox")


def save_upload(con, who, cid, kind, day, fs, event_id=None):
    """Keep a photo/PDF on the box only until the mailbox script carries it to Drive. Returns (id, error)."""
    up_ensure(con)
    if kind not in UP_FOLDER:
        return None, "kind"
    if fs is None or not getattr(fs, "filename", ""):
        return None, "no file"
    ext = os.path.splitext(fs.filename)[1].lower()
    if ext not in UP_EXT:
        return None, "type"
    data = fs.read(UP_MAX + 1)
    if not data:
        return None, "empty"
    if len(data) > UP_MAX:
        return None, "too large"
    import uuid
    os.makedirs(_inbox(), mode=0o700, exist_ok=True)
    name = uuid.uuid4().hex + ext
    with open(os.path.join(_inbox(), name), "wb") as fh:
        fh.write(data)
    try:
        os.chmod(os.path.join(_inbox(), name), 0o600)
    except OSError:
        pass
    cur = con.execute("INSERT INTO record_upload(clinic_id, kind, day, local_name, ext, bytes, event_id, uploaded_by, uploaded_at) "
                      "VALUES (?,?,?,?,?,?,?,?,?)", (cid, kind, day, name, ext, len(data), event_id, who, _stamp()))
    con.commit()
    return cur.lastrowid, ""


def _day_ok(v):
    try:
        d = dt.date.fromisoformat(str(v or "")[:10])
    except ValueError:
        return ""
    return d.isoformat() if dt.date(2000, 1, 1) <= d <= dt.date.fromisoformat(_today()) else ""


_UP_ERR = {"no file": "File chunein.", "type": "Sirf photo ya PDF.", "too large": "File 12 MB se badi hai.",
           "empty": "File khali hai.", "kind": "Kagaz ki kism chunein."}


@bp.route(CP + "/add", methods=["GET", "POST"])
def checks_add():
    """Reception / the chamber add an outside paper for a patient: MRI/CT, discharge, outside report."""
    u, err = _check_gate()
    if err:
        return err
    con = _db()
    up_ensure(con)
    msg = ""
    if request.method == "POST":
        cid = _clean_id(request.form.get("cid"))
        day = _day_ok(request.form.get("day") or _today())
        if not (cid and re.fullmatch(r"\d{1,8}", cid) and _known_id(con, cid)):
            msg = "Clinic ID hamari list mein nahi — dobara dekhein."
        elif not day:
            msg = "Tareekh sahi nahi."
        else:
            uid, e = save_upload(con, _who(u), cid, request.form.get("kind") or "", day, request.files.get("file"))
            if uid:
                return redirect(CP + "/add?ok=" + quote("Jud gaya — %s. 15 minute mein Drive par chala jayega." % cid), code=303)
            msg = _UP_ERR.get(e, e)
    ok = request.args.get("ok", "")
    kinds = "".join('<label class="pk"><input type="radio" name="kind" value="%s"%s> %s</label>' % (
        k, " checked" if k == "scan" else "", _esc(l)) for k, l in UP_KINDS)
    body = (('<div class="okb">%s</div>' % _esc(ok) if ok else "") + ('<div class="bad">%s</div>' % _esc(msg) if msg else "") +
            '<form class="ck" method="post" enctype="multipart/form-data" action="%s/add">'
            '<div class="pks"><input name="cid" inputmode="numeric" placeholder="Clinic ID" maxlength="8" required>'
            '%s<input type="date" name="day" value="%s" max="%s">'
            '<input type="file" name="file" accept="image/*,application/pdf" required></div>'
            '<div class="ckb"><button>Jodein</button></div></form>' % (CP, kinds, _today(), _today()))
    return _shell("Kagaz jodein", body, back=CP, back_label="← Check karein", lang="hi")


@bp.route(P + "/p/<cid>/add", methods=["POST"])
def doctor_add(cid):
    """The doctor adds a paper, or a hospital/surgery event with an optional paper, from the patient page."""
    u, err = _gate()
    if err:
        return err
    cid = _clean_id(cid)
    con = _db()
    up_ensure(con)
    day = _day_ok(request.form.get("day") or _today())
    back = "%s/p/%s" % (P, quote(cid))
    if not (cid and day):
        return redirect(back + "?msg=" + quote("The date is not valid."), code=303)
    ev = None
    if request.form.get("what_kind") == "event":
        what = (request.form.get("what") or "").strip()[:300]
        if not what:
            return redirect(back + "?msg=" + quote("Say what was done.") + "#hs", code=303)
        cur = con.execute("INSERT INTO record_event(clinic_id, day, hospital, what, note, added_by, added_at) VALUES (?,?,?,?,?,?,?)",
                          (cid, day, (request.form.get("hospital") or "").strip()[:120], what,
                           (request.form.get("note") or "").strip()[:1000], _who(u), _stamp()))
        con.commit()
        ev = cur.lastrowid
        f = request.files.get("file")
        if f is None or not getattr(f, "filename", ""):
            return redirect(back + "?msg=" + quote("Event added.") + "#hs", code=303)
        kind = "other"
    else:
        kind = request.form.get("kind") or ""
    uid, e = save_upload(con, _who(u), cid, kind, day, request.files.get("file"), ev)
    if not uid:
        return redirect(back + "?msg=" + quote({"no file": "Choose a file.", "type": "Only a photo or a PDF.",
                                                "too large": "The file is over 12 MB.", "empty": "The file is empty.",
                                                "kind": "Choose what the paper is."}.get(e, e)) + ("#hs" if ev else "#xr"), code=303)
    return redirect(back + "?msg=" + quote("Added — it reaches Drive within 15 minutes.") + ("#hs" if ev else "#xr"), code=303)


@bp.route(P + "/api/upload-pending", methods=["GET"])
def api_upload_pending():
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    con = _db()
    up_ensure(con)
    out = []
    for r in _rows(con, "SELECT * FROM record_upload WHERE state='new' ORDER BY id LIMIT 30"):
        nm = _safe((person(con, r["clinic_id"]) or {}).get("name") or "")
        label = dict((("scan", "MRI-CT"), ("other", "Paper"), ("blood", "Blood report outside"), ("xray", "X-ray outside")))[r["kind"]]
        fname = " · ".join(x for x in (r["day"], r["clinic_id"], nm, label) if x) + " " + str(r["id"]) + r["ext"]
        out.append({"id": r["id"], "day": r["day"], "folder": UP_FOLDER[r["kind"]], "file_name": fname,
                    "mime": UP_EXT.get(r["ext"], "application/octet-stream")})
    return jsonify(ok=True, items=out)


@bp.route(P + "/api/upload-file/<int:uid>", methods=["GET"])
def api_upload_file(uid):
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    con = _db()
    up_ensure(con)
    r = con.execute("SELECT * FROM record_upload WHERE id=? AND state='new'", (uid,)).fetchone()
    if not r:
        return jsonify(ok=False, error="none"), 404
    p = os.path.join(_inbox(), r["local_name"])
    if not os.path.exists(p):
        return jsonify(ok=False, error="gone"), 404
    return Response(open(p, "rb").read(), mimetype=UP_EXT.get(r["ext"], "application/octet-stream"))


@bp.route(P + "/api/upload-done", methods=["POST"])
def api_upload_done():
    """Drive has it: file it on the patient and drop the box's copy."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    con = _db()
    up_ensure(con)
    n = 0
    for x in (j.get("files") if isinstance(j.get("files"), list) else [j])[:40]:
        try:
            uid = int(x.get("id"))
        except (TypeError, ValueError):
            continue
        did = str(x.get("drive_id") or "")
        if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", did):
            continue
        r = con.execute("SELECT * FROM record_upload WHERE id=? AND state='new'", (uid,)).fetchone()
        if not r:
            continue
        con.execute("INSERT OR IGNORE INTO record_file(clinic_id, kind, day, drive_id, file_name, mime, bytes, source, source_ref, "
                    "note, added_by, added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (r["clinic_id"], r["kind"], r["day"], did, str(x.get("file_name") or "")[:200], UP_EXT.get(r["ext"], ""),
                     r["bytes"], "upload", "up:%d" % uid, ("event %d" % r["event_id"]) if r["event_id"] else "",
                     r["uploaded_by"], _stamp()))
        con.execute("UPDATE record_upload SET state='saved', drive_id=? WHERE id=?", (did, uid))
        con.commit()
        try:
            os.remove(os.path.join(_inbox(), r["local_name"]))
        except OSError:
            pass
        n += 1
    return jsonify(ok=True, stored=n)


def events(con, cid):
    up_ensure(con)
    ev = _rows(con, "SELECT * FROM record_event WHERE clinic_id=? AND state='ok' ORDER BY day DESC, id DESC", (cid,))
    for e in ev:
        e["files"] = _rows(con, "SELECT * FROM record_file WHERE note=? AND clinic_id=? AND state='ok'", ("event %d" % e["id"], cid))
        e["waiting"] = _rows(con, "SELECT id FROM record_upload WHERE event_id=? AND state='new'", (e["id"],))
    return ev


def _add_forms(cid):
    kinds = "".join('<option value="%s">%s</option>' % (k, l) for k, l in
                    (("scan", "MRI / CT"), ("other", "Discharge / other paper"), ("blood", "Outside blood report"), ("xray", "Outside X-ray")))
    paper = ('<details class="add"><summary>Add a paper</summary><form method="post" enctype="multipart/form-data" action="%s/p/%s/add">'
             '<select name="kind">%s</select> <input type="date" name="day" value="%s" max="%s"> '
             '<input type="file" name="file" accept="image/*,application/pdf" required> <button class="go">Add</button></form></details>'
             % (P, quote(cid), kinds, _today(), _today()))
    event = ('<details class="add"><summary>Add event</summary><form method="post" enctype="multipart/form-data" action="%s/p/%s/add">'
             '<input type="hidden" name="what_kind" value="event"><input type="date" name="day" value="%s" max="%s"> '
             '<input name="hospital" placeholder="Hospital" maxlength="120"> <input name="what" placeholder="What was done" maxlength="300" required> '
             '<input name="note" placeholder="Note" maxlength="1000"> <input type="file" name="file" accept="image/*,application/pdf"> '
             '<button class="go">Add</button></form></details>' % (P, quote(cid), _today(), _today()))
    return paper, event


def check_line(con):
    """The doctors' one line: (text, n_open, oldest_days)."""
    items = check_items(con)
    if not items:
        return "Patient records: all clear", 0, 0
    old = max(_age(i["day"]) for i in items)
    return "Patient records: %d need%s a look · oldest %d day%s" % (
        len(items), "s" if len(items) == 1 else "", old, "" if old == 1 else "s"), len(items), old


def _check_gate():
    u, err = _require("maker", "checker", unit=CHECK_UNIT)
    if u:
        return u, None
    return None, Response(_shell("Check karein", '<div class="bad">Yeh page aapke login ke liye nahi hai.</div>', lang="hi"),
                          status=403, mimetype="text/html")


def _floor_items(con, u, items):
    """S495: a STAFF login is shown no item dated before the lists' floor (aaj_floor.py: 01-Oct-2026, and only while the
    lists are started). A doctor's page, the doctors' line (check_line) and an answer by its key are whole. An X-ray file
    with no day of its own is dated by the day it was first seen (xray_filing.planned_at) -- the list's own rule
    (aaj_seed.FLOOR), so the line and the page agree. Without the helper, or if ANYTHING here fails (the read below is
    made directly, not through _rows, so that a failed read is an error and not an empty answer), the page is what it has
    always been."""
    try:
        import aaj_floor                                         # noqa: PLC0415
        f = aaj_floor.floor_for(con, _require, u)
        if not f:
            return items
        seen = {}
        for r in con.execute("SELECT src_id, day, planned_at FROM xray_filing WHERE state='check'").fetchall():
            seen["xf:" + str(r[0])] = r[1] or str(r[2] or "")[:10]
        return [i for i in items if str((seen.get(i["key"]) if i.get("kind") == "xray_file" else i.get("day")) or "") >= f]
    except Exception:                                            # noqa: BLE001
        return items


@bp.route(CP)
def checks_page():
    u, err = _check_gate()
    if err:
        return err
    con = _db()
    ensure(con)
    items = _floor_items(con, u, check_items(con))
    ok = request.args.get("ok", "")
    if not request.args.get("list"):                     # S757 (D875): the photo and lab-report screens; ?list=1 is the old list
        try:
            import check_screens                         # noqa: PLC0415
            return check_screens.staff_page(con, u, [i for i in items if i["kind"] != "xray_file"], ok)
        except Exception:                                # noqa: BLE001 -- the old list stands in
            pass
    body = ['<div class="ckb"><a class="view" href="%s/add">+ Kagaz jodein (MRI / CT / discharge)</a></div>' % CP]
    if ok:
        body.append('<div class="okb">%s</div>' % _esc(ok))
    if not items:
        body.append('<div class="okb">Sab theek hai — kuch dekhna baaki nahi.</div>')
    for i in items:
        body.append(_old_item_html(i))
    return _shell("Check karein", "".join(body), lang="hi")


def _old_item_html(i):
    """One open item as the S340 list draws it (a form posting to /finance/checks/answer). S757: one function, so that
    check_screens draws the items it does not own exactly as before."""
    btn = "".join('<button name="a" value="%s">%s</button>' % (c, _esc(l)) for c, l in ANS[i["kind"]])
    extra = ""
    if i["kind"] in ("lab_id", "xray_file"):
        extra = ('<input name="new_id" inputmode="numeric" placeholder="Sahi clinic ID" maxlength="8" value="%s">'
                 '<button name="a" value="id_fixed">Sahi ID lagayein</button>') % _esc(i.get("suggest") or "")   # S752
    if i["kind"] == "wa":
        return ('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
                '<div class="ckh"><span class="age">%d din</span></div><div>%s (%s)</div>%s</form>' % (
                    CP, _esc(i["key"]), _age(i["day"]), _esc(i["hi"]), _dmy(i["day"])[:6], _wa_form(i)))
    return ('<form class="ck" method="post" action="%s/answer"><input type="hidden" name="key" value="%s">'
            '<div class="ckh"><b>%s</b> · %s · <span class="age">%d din</span></div>'
            '<div>%s (%s)</div>%s<div class="ckb">%s%s</div></form>' % (
                CP, _esc(i["key"]), _esc(i["clinic_id"]), _esc(i["name"] or "—"), _age(i["day"]),
                _esc(i["hi"]), _dmy(i["day"])[:6], ('<div class="sm">%s</div>' % _esc(i["why"])) if i["why"] else "",
                extra, btn))   # S752: the ID box first -- Enter in it is 'Sahi ID lagayein', never 'Yeh X-ray nahi'


@bp.route(CP + "/answer", methods=["POST"])
def checks_answer():
    u, err = _check_gate()
    if err:
        return err
    con = _db()
    ensure(con)
    key = (request.form.get("key") or "")[:80]
    a = (request.form.get("a") or "")[:20]
    item = next((i for i in check_items(con) if i["key"] == key), None)
    if not item:
        return redirect(CP + "?ok=" + quote("Yeh pehle hi ho chuka hai."), code=303)
    if item["kind"] == "wa":
        msg = wa_answer(con, u, item, a, request.form)
        if msg:
            return redirect(CP + "?ok=" + quote(msg), code=303)
        con.execute("INSERT INTO record_check(key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?) "
                    "ON CONFLICT(key) DO UPDATE SET answer=excluded.answer, answered_by=excluded.answered_by, "
                    "answered_at=excluded.answered_at", (key, "wa", _clean_id(request.form.get("new_id")) or _clean_id(request.form.get("cid")),
                                                         a, "", _who(u), _stamp()))
        con.commit()
        return redirect(CP + "?ok=" + quote("Ho gaya."), code=303)
    allowed = {c for c, _ in ANS[item["kind"]]} | ({"id_fixed"} if item["kind"] in ("lab_id", "xray_file") else set())
    if a not in allowed:
        return redirect(CP + "?ok=" + quote("Jawab samajh nahi aaya, dobara dabayein."), code=303)
    note = ""
    if a == "id_fixed":
        nid = _clean_id(request.form.get("new_id"))
        if not (nid and re.fullmatch(r"\d{1,8}", nid) and _known_id(con, nid)):
            return redirect(CP + "?ok=" + quote("Yeh ID bhi list mein nahi hai — dobara dekhein."), code=303)
        if item["kind"] == "xray_file":                     # S373: the next mailbox run files it under this ID
            note = nid
        else:
            con.execute("UPDATE record_file SET clinic_id=?, note=? WHERE id=?",
                        (nid, "ID corrected from %s by %s at %s" % (item["clinic_id"], _who(u), _stamp()), item["file_id"]))
            note = "%s -> %s" % (item["clinic_id"], nid)
    con.execute("INSERT INTO record_check(key, kind, clinic_id, answer, note, answered_by, answered_at) VALUES (?,?,?,?,?,?,?) "
                "ON CONFLICT(key) DO UPDATE SET answer=excluded.answer, note=excluded.note, answered_by=excluded.answered_by, "
                "answered_at=excluded.answered_at", (key, item["kind"], item["clinic_id"], a, note, _who(u), _stamp()))
    con.commit()
    return redirect(CP + "?ok=" + quote("Ho gaya."), code=303)


def _check_line_html(con):
    text, n, old = check_line(con)
    items = check_items(con) if n else []
    rows = "".join('<li><a href="%s/p/%s">%s</a> %s · %s · %s — %s</li>' % (
        P, quote(i["clinic_id"]), _esc(i["clinic_id"]), _esc(i["name"]), _dmy(i["day"]), _esc(i["en"]),
        "%d day%s" % (_age(i["day"]), "" if _age(i["day"]) == 1 else "s")) for i in items) or "<li>Nothing open.</li>"
    since = (dt.date.fromisoformat(_today()) - dt.timedelta(days=7)).isoformat()
    done = _rows(con, "SELECT * FROM record_check WHERE answered_at>=? ORDER BY answered_at DESC LIMIT 30", (since,))
    trail = "".join('<li>%s · %s · %s by %s, %s</li>' % (
        _esc(d["clinic_id"]), _esc(d["kind"].replace("_", " ")),
        _esc(ANS_EN.get(d["answer"], d["answer"]) + (" " + d["note"] if d["note"] else "")),
        _esc(d["answered_by"]), _esc(d["answered_at"][:16])) for d in done)
    return ('<details class="sec line %s"><summary><span>%s</span></summary><div class="body"><ul>%s</ul>%s</div></details>' % (
        "clear" if not n else "open", _esc(text), rows,
        ("<h3>Answered in the last 7 days</h3><ul>%s</ul>" % trail) if trail else ""))


# ---------------------------------------------------------------- the mailbox's doors (cron token)
@bp.route(P + "/api/reader", methods=["GET"])
def api_reader():
    """Which account the Apps Script shares 'Clinic Records' with: this box's read-only service account."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    e = sa_email()
    return jsonify(ok=bool(e), email=e)


@bp.route(P + "/api/folders", methods=["POST"])
def api_folders():
    """VPS_Lab_Files.gs (S333) tells the server the Drive ids of the folders it made."""
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    con = _db()
    ensure(con)
    n = 0
    for k in ("root_id", "blood_id", "xray_test_id", "xray_inbox_id", "xray_check_id"):
        v = str(j.get(k) or "")
        if re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", v):
            con.execute("INSERT INTO record_setting(key, value, set_at) VALUES (?,?,?) ON CONFLICT(key) DO UPDATE SET "
                        "value=excluded.value, set_at=excluded.set_at", (k, v, _stamp()))
            n += 1
    con.commit()
    return jsonify(ok=True, stored=n)


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


# ---------------------------------------------------------------- S373: the X-ray LIVE filing (S273_BUILD_BRIEF §2)
# THE OWNER, 23-Sep-2026: "The X-ray upload test period is over. Now incorporate it into the system."
# The server DECIDES with the same xray_plan() the test page proved (22 of 38 matched, 4 numbered, 12 to the check
# folder over 19-22 Sep; the X-ray PC clock agrees); the mailbox script EXECUTES (D574: it is the only Drive writer):
# every picture in "X-ray inbox" and "X-ray test" (the folder the staff already use) is COPIED under its new name into
# Clinic Records / X-ray / Mon YYYY / DD-Mon and the original is moved to X-ray inbox / _filed -- nothing is deleted.
# A picture the plan cannot place goes to "X-ray check" and becomes a Check karein item: the staff type the right
# clinic ID and the next run files it. A patient whose slip (or Docterz line) shows an X-ray and who has no file by the
# next day is a Check karein item too, from the go-live day onward (XRAY_LIVE_FROM; record_setting xray_live_from overrides).
XRAY_BATCH = 25
XRAY_LIVE_FROM = os.environ.get("XRAY_LIVE_FROM", "2026-09-23")    # the go-live day (the owner's word, 23-Sep-2026)
XRAY_SCHEMA = """
CREATE TABLE IF NOT EXISTS xray_filing (
  src_id      TEXT PRIMARY KEY,
  orig_name   TEXT NOT NULL DEFAULT '',
  file_time   TEXT NOT NULL DEFAULT '',
  action      TEXT NOT NULL DEFAULT '',
  clinic_id   TEXT NOT NULL DEFAULT '',
  day         TEXT NOT NULL DEFAULT '',
  new_name    TEXT NOT NULL DEFAULT '',
  dest_id     TEXT NOT NULL DEFAULT '',
  file_id     INTEGER,
  state       TEXT NOT NULL DEFAULT 'planned',
  verdict     TEXT NOT NULL DEFAULT '',
  planned_at  TEXT NOT NULL DEFAULT '',
  done_at     TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS xray_filing_state ON xray_filing(state);
"""
_xray_schema_done = False


def xray_ensure(con):
    global _xray_schema_done
    ensure(con)
    if not _xray_schema_done:
        con.executescript(XRAY_SCHEMA)
        con.commit()
        _xray_schema_done = True


def _xray_path(day):
    d = dt.date.fromisoformat(day)
    return ["X-ray", d.strftime("%b %Y"), d.strftime("%d-%b")]


def _xray_ext(name):
    m = IMG.search(name or "")
    return m.group(0).lower() if m else ".jpg"


_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".bmp": "image/bmp", ".tif": "image/tiff",
         ".tiff": "image/tiff", ".dcm": "application/dicom"}


def xray_actions(con):
    """What the next mailbox run must do, and the table updated to say so. Never raises past a folder that
    cannot be listed (that folder is skipped and reported)."""
    xray_ensure(con)
    stamp = _stamp()
    src, notes = [], []
    for key in ("xray_inbox_id", "xray_test_id"):
        fid = setting(con, key)
        if not fid:
            continue
        files, why = drive_list(fid)
        if files is None:
            notes.append("%s: %s" % (key, why))
            continue
        src.extend(files)
    ids = {f.get("id") for f in src}
    items = []
    for r in xray_plan(con, src):
        sid = r.get("id") or ""
        if not sid:
            continue
        if r["kind"] in ("ok", "differ") and r.get("proposed") and r.get("time"):
            day = r["time"].date().isoformat()
            it = {"id": sid, "action": "file", "name": r["proposed"], "path": _xray_path(day)}
            row = (sid, r["orig"], r["time"].isoformat(sep=" "), "file", r["cid"], day, r["proposed"], "planned", r["verdict"], stamp)
        elif r["kind"] == "check":
            it = {"id": sid, "action": "check"}
            row = (sid, r["orig"], r["time"].isoformat(sep=" ") if r.get("time") else "", "check", r.get("cid") or "",
                   r["time"].date().isoformat() if r.get("time") else "", "", "planned", r["verdict"], stamp)
        elif r["kind"] == "dup":
            it = {"id": sid, "action": "dup"}
            row = (sid, r["orig"], "", "dup", "", "", "", "planned", r["verdict"], stamp)
        else:
            continue                                   # not a picture: left where it is, as the test run said
        con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, new_name, state, verdict, planned_at) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(src_id) DO UPDATE SET action=excluded.action, clinic_id=excluded.clinic_id, "
                    "day=excluded.day, new_name=excluded.new_name, verdict=excluded.verdict, planned_at=excluded.planned_at "
                    "WHERE xray_filing.state IN ('planned','check')", row)
        items.append(it)
    # the check folder: what the staff have answered is filed; what is still there stays an item; what vanished is 'gone'
    cfid = setting(con, "xray_check_id")
    in_check, s752_retry, s752_listed = set(), [], False   # S752: the unanswered pictures, re-tried below
    if cfid:
        cf, why = drive_list(cfid)
        if cf is None:
            notes.append("xray_check_id: %s" % why)
        else:
            s752_listed = True                           # S752: the check folder was read
            answers = _answers(con)
            for f in cf:
                sid = f.get("id") or ""
                if not sid or sid in ids:
                    continue
                in_check.add(sid)
                t, _src = file_time(f)
                day = t.date().isoformat() if t else _today()
                con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, day, state, verdict, planned_at) "
                            "VALUES (?,?,?,?,?,?,?,?) ON CONFLICT(src_id) DO UPDATE SET state=CASE WHEN xray_filing.state IN "
                            "('done','gone','not_xray') THEN 'check' ELSE xray_filing.state END",
                            (sid, f.get("name", ""), t.isoformat(sep=" ") if t else "", "check", day, "check", "in the check folder", stamp))
                a = answers.get("xf:" + sid)
                if a and a["answer"] == "id_fixed" and re.fullmatch(r"\d{1,8}", a["note"] or ""):
                    cid = a["note"]
                    nm = _safe((person(con, cid) or {}).get("name") or "")
                    n = _rows(con, "SELECT COUNT(*) n FROM record_file WHERE kind='xray' AND clinic_id=? AND day=?", (cid, day))[0]["n"]
                    name = " · ".join(x for x in (day, cid, nm, "X-ray %d" % (n + 1)) if x) + _xray_ext(f.get("name"))
                    con.execute("UPDATE xray_filing SET action='file', clinic_id=?, new_name=?, state='planned', verdict=? WHERE src_id=?",
                                (cid, name, "ID %s given by %s" % (cid, a["answered_by"]), sid))
                    items.append({"id": sid, "action": "file", "name": name, "path": _xray_path(day)})
                elif not a:                                  # S752: nobody has answered it -- planned again below
                    s752_retry.append(f)
    items.extend(_s752_retry_safe(con, s752_retry, stamp, notes, s752_listed))
    for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='check'"):
        if cfid and s752_listed and r["src_id"] not in in_check and r["src_id"] not in ids:   # S752: never when the folder was not read
            con.execute("UPDATE xray_filing SET state='gone' WHERE src_id=?", (r["src_id"],))
    con.commit()
    return items[:XRAY_BATCH], notes


def xray_done(con, files):
    """The mailbox script did it. 'file' -> one record_file (kind xray, source xray_inbox, source_ref = the picture's
    own Drive id) on the patient; 'check' / 'dup' -> the table says where it went. Idempotent."""
    xray_ensure(con)
    n = 0
    for x in files[:60]:
        sid = str(x.get("id") or "")
        act = str(x.get("action") or "")
        if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", sid):
            continue
        row = con.execute("SELECT * FROM xray_filing WHERE src_id=?", (sid,)).fetchone()
        if not row:
            continue
        if act == "file":
            did = str(x.get("dest_id") or "")
            if not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", did) or not row["clinic_id"] or not row["day"]:
                continue
            name = str(x.get("name") or row["new_name"])[:200]
            con.execute("INSERT OR IGNORE INTO record_file(clinic_id, kind, day, drive_id, file_name, mime, bytes, source, source_ref, "
                        "note, added_by, added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (row["clinic_id"], "xray", row["day"], did, name, _MIME.get(_xray_ext(name), "image/jpeg"), 0,
                         "xray_inbox", sid, (row["verdict"] or "")[:200], "mailbox", _stamp()))
            fr = con.execute("SELECT id FROM record_file WHERE source='xray_inbox' AND source_ref=?", (sid,)).fetchone()
            con.execute("UPDATE xray_filing SET state='done', dest_id=?, file_id=?, done_at=? WHERE src_id=?",
                        (did, fr["id"] if fr else None, _stamp(), sid))
            n += 1
        elif act in ("check", "dup"):
            con.execute("UPDATE xray_filing SET state=?, done_at=? WHERE src_id=?", ("check" if act == "check" else "dup", _stamp(), sid))
            n += 1
    con.commit()
    return n


def xray_items(con):
    """Check karein: (1) a picture in the check folder, (2) an X-ray on the slip / Docterz with no file by the next day."""
    xray_ensure(con)
    answers = _answers(con)
    out = []
    for r in _rows(con, "SELECT * FROM xray_filing WHERE state='check' ORDER BY day, orig_name"):
        key = "xf:" + r["src_id"]
        a = answers.get(key)
        if a and a["answer"] in ("not_xray", "id_fixed"):
            continue
        out.append({"key": key, "kind": "xray_file", "clinic_id": r["clinic_id"] or "", "day": r["day"] or _today(),
                    "name": r["orig_name"], "hi": "X-ray file ka clinic ID nahi mila: %s" % r["orig_name"],
                    "en": "X-ray picture with no clinic ID (%s)" % r["orig_name"], "why": r["verdict"] or ""})
    live = setting(con, "xray_live_from") or XRAY_LIVE_FROM
    if live:
        last = (dt.date.fromisoformat(_today()) - dt.timedelta(days=1)).isoformat()
        want = {}
        for s in _rows(con, "SELECT DISTINCT s.day, s.clinic_id FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                            "WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' AND s.clinic_id<>'' AND s.day>=? AND s.day<=?",
                       (live, last)):
            want[(s["day"], s["clinic_id"])] = "slip"
        for d in _rows(con, "SELECT DISTINCT business_date day, clinic_id FROM clinic_day_line WHERE section='xray' AND clinic_id<>'' "
                            "AND business_date>=? AND business_date<=?", (live, last)):
            want.setdefault((d["day"], d["clinic_id"]), "Docterz")
        for (day, cid), how in sorted(want.items()):
            if _rows(con, "SELECT 1 FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=? LIMIT 1", (cid, day)):
                continue
            if _rows(con, "SELECT 1 FROM xray_filing WHERE clinic_id=? AND day=? AND state IN ('planned','check') LIMIT 1", (cid, day)):
                continue
            key = "xm:%s:%s" % (day, cid)
            op, why = _open_by_answer(key, answers)
            if op:
                out.append({"key": key, "kind": "xray_missing", "clinic_id": cid, "day": day,
                            "name": (person(con, cid) or {}).get("name", ""),
                            "hi": "X-ray hua tha (%s), file nahi aayi" % how, "en": "X-ray taken (%s), no file" % how, "why": why})
    return out


@bp.route(P + "/api/xray-plan", methods=["GET"])
def api_xray_plan():
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    con = _db()
    items, notes = xray_actions(con)
    return jsonify(ok=True, items=items, notes=notes)


@bp.route(P + "/api/xray-done", methods=["POST"])
def api_xray_done():
    if not _cron_ok():
        return jsonify(ok=False, error="bad_token"), 401
    j = request.get_json(silent=True) or {}
    con = _db()
    files = j.get("files") if isinstance(j.get("files"), list) else []
    return jsonify(ok=True, stored=xray_done(con, files))


def xray_gallery(con, cid):
    """The patient's X-ray pictures, newest first, side by side (S273 brief §2 step 2)."""
    fl = _rows(con, "SELECT id, day, file_name FROM record_file WHERE clinic_id=? AND kind='xray' AND state='ok' AND drive_id<>'' "
                    "ORDER BY day DESC, id DESC LIMIT 12", (cid,))
    if not fl:
        return '<p class="sm">No X-ray picture filed yet for this ID.</p>'
    cells = "".join('<a class="xg" href="%s/file/%d" target="_blank" rel="noopener"><img loading="lazy" src="%s/file/%d" alt="">'
                    '<span>%s</span></a>' % (P, f["id"], P, f["id"], _esc(_dmy(f["day"]) + " · " + (f["file_name"].split(" · ")[-1] if f["file_name"] else "")))
                    for f in fl)
    return ('<div style="display:flex;flex-wrap:wrap;gap:10px">%s</div>'
            '<style>a.xg{display:flex;flex-direction:column;width:170px;text-decoration:none;color:inherit;font-size:12px}'
            'a.xg img{width:170px;height:170px;object-fit:contain;background:#111;border-radius:6px}</style>' % cells)


# ---------------------------------------------------------------- the frame
def _shell(title, body, back="/portal", back_label="← Portal", lang="en"):
    return """<!doctype html><html lang="%s"><head><meta charset="utf-8">
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
.v-ok{color:var(--ok);font-weight:600}.v-check{color:var(--bad);font-weight:600}.v-differ,.v-dup{color:var(--warn);font-weight:600}
.okb{background:var(--okbg);border-left:6px solid var(--ok);padding:10px 12px;margin:0 0 10px;border-radius:6px}
form.ck{background:var(--paper);border:2px solid var(--line);border-radius:10px;padding:10px 12px;margin:0 0 10px}
.ckh{font-size:15px}.age{color:var(--bad);font-weight:700}.ckb{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px}
.ckb button{min-height:48px;padding:0 14px;border:2px solid var(--accent);background:#fff;color:var(--accent);border-radius:9px;font-size:16px;font-weight:600;cursor:pointer}
.ckb input{min-height:48px;font-size:17px;padding:0 10px;border:2px solid #6b7b86;border-radius:9px;width:150px}
.pks{display:flex;flex-direction:column;gap:6px;margin-top:8px}.pk{font-size:16px;display:flex;gap:8px;align-items:center;min-height:40px}
.pk input{width:22px;height:22px}.pks input[name=new_id]{min-height:44px;font-size:17px;padding:0 10px;border:2px solid #6b7b86;border-radius:9px;width:180px}
a.view{display:inline-flex;align-items:center;min-height:44px;padding:0 14px;border-radius:9px;background:var(--accent);color:#fff;text-decoration:none;font-weight:600}
.ckb button.nr{border-color:var(--bad);color:var(--bad)}
details.add{margin:10px 0}details.add>summary{cursor:pointer;color:var(--accent);font-weight:700}
details.add form{display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;align-items:center}
details.add input,details.add select{font:inherit;min-height:44px;padding:4px 8px;border:2px solid #6b7b86;border-radius:8px}
.pks input[type=date],.pks input[type=file]{min-height:44px;font-size:16px}
details.line.clear>summary{color:var(--ok)}details.line.open>summary{color:var(--bad)}
.rem{background:var(--warnbg);border-left:6px solid var(--warn);padding:8px 12px;margin:6px 0;border-radius:6px;font-size:15px}
</style></head><body><header class="top"><a class="back" href="%s">%s</a><h1>%s</h1><span class="d">%s</span></header>
<main>%s</main><script>
[].forEach.call(document.querySelectorAll('details.sec'),function(d){d.addEventListener('toggle',function(){
 if(d.open){[].forEach.call(document.querySelectorAll('details.sec'),function(o){if(o!==d)o.open=false;});}});});
</script></body></html>""" % (lang, _esc(title), _esc(back), _esc(back_label), _esc(title), _dmy(_today())[:6], body)


# ---------------------------------------------------------------- S752: the X-ray check folder RE-TRIED (S404, 08-Nov-2026)
# THE OWNER, 08-Nov-2026 14:46 IST ("build it"), after Alisha found 41 October X-rays 'photo baaki': the pictures had come --
# 33 of last night's 38 sat in Drive's "X-ray check" folder, parked once and never looked at again (100 parked since 20-Sep;
# no Check karein answer ever given). Three ways they got there: (1) the right ID on the picture, but the filing run (~17:40)
# came before the evening's X-ray slip (~19:30) -- "ID not in the day's X-ray list"; (2) the picture saved with the
# patient's name and no clinic ID; (3) the ID typed one digit wrong on the X-ray PC.
# NOW, on every run, each picture in the check folder that nobody has answered is planned again:
#   (1) its ID is now on that day's X-ray list (slip or Docterz)                -> filed, as the inbox files it;
#   (2) no number in its name, the day is OVER (its slips are all in), and its name is, word for word, the name of exactly
#       one X-ray patient of that day while NO other patient of that day shares even one word of it -> filed;
#       a 'baby of / master' picture is never filed by name;
#   (3) anything weaker -- an ID one keystroke off an unfiled patient of the day, a looser name match -> NEVER filed by
#       itself. Check karein shows "Shayad ID ..."; for an ID one keystroke off or a strict name match the ID is already in
#       the box (one tap on 'Sahi ID lagayein'); for a looser match it is shown as words only.
# A picture a person has answered is never touched. A re-try that no longer places goes back to the check list; a re-try
# whose picture has left the check folder by another road for a day is swept to 'gone'. The cold review's findings (S404):
# the run's own inbox rows are committed BEFORE the re-try, so a failing re-try can never take them back; numbering counts
# the rows still on their way; the day is the stored one; one read per day per page.
# The Drive side is unchanged: the mailbox script already files any picture id the plan names (VPS_Lab_Files.gs _fileXray).
S752_STOP = {"mr", "mrs", "smt", "shri", "sri", "ms", "miss", "dr", "km", "kumari", "md", "mohd",
             "mohammad", "mohammed", "devi", "kumar", "singh", "bee", "begum", "khan", "lal", "ram", "prasad", "chand", "kr",
             "jpg", "jpeg", "png", "img", "image", "xray", "ray", "scan", "copy", "new", "old", "film",
             "knee", "knees", "ankle", "wrist", "hip", "hips", "spine", "lat", "lateral", "both", "left", "right", "view",
             "views", "chest", "foot", "feet", "hand", "hands", "shoulder", "elbow", "pelvis", "lumbar", "cervical",
             "dorsal", "skull", "leg", "legs", "thigh", "arm", "standing", "side", "back", "neck", "oblique", "joint",
             "forearm", "femur", "tibia", "fibula", "humerus", "heel", "toe", "toes", "finger", "fingers", "thumb",
             "clavicle", "scapula", "sacrum", "coccyx", "lspine", "cspine", "dspine", "pbh", "lsp", "csp", "dsp", "lss",
             "ext", "flex", "flexion", "extension", "stress", "weight", "bearing", "axial", "skyline", "mortise"}
S752_CHILD = {"baby", "master", "bby", "child", "of", "putra", "putri", "son", "daughter", "putr", "beti", "beta", "wo", "do", "so"}
S752_SWEEP_HOURS = 24


def _s752_words(s):
    return re.findall(r"[a-z]+", str(s or "").lower())


def _s752_tokens(s):
    return [w for w in _s752_words(s) if len(w) >= 3 and w not in S752_STOP and w not in S752_CHILD]


S752_TITLES = {"mr", "mrs", "smt", "shri", "sri", "ms", "miss", "dr", "km", "kumari", "md", "mohd", "mohammad", "mohammed"}


def _s752_strict_tokens(s):
    """For a decision to FILE (and a pre-filled box): only titles, file and body-part words are dropped -- the name-part
    words (kumar, devi, begum, ram, lal, khan, singh, prasad ...) count, and so do two-letter words ('Om'). The cold
    review R2: 'KAMLESH KUMAR' must never become Kamlesh Devi, nor 'SITA RAM' Sita Devi, nor 'RAM PRAKASH' Om Prakash."""
    return [w for w in _s752_words(s) if len(w) >= 2 and w not in S752_TITLES and w not in S752_CHILD
            and (w not in S752_STOP or w in S752_NAMEPART)]


S752_NAMEPART = {"devi", "kumar", "singh", "bee", "begum", "khan", "lal", "ram", "prasad", "chand", "kr"}


def _s752_child(s):
    """'BABY OF REKHA', 'MASTER ...', 'S/O', 'D/O': never filed by a name match."""
    w = set(_s752_words(s))
    return bool(w & {"baby", "master", "bby", "child", "putra", "putri", "son", "daughter", "beti", "beta"}) or \
        bool(re.search(r"\b[sdwb]\s*/\s*o\b", str(s or "").lower())) or (" of " in " %s " % " ".join(_s752_words(s)))


def _s752_name_match(a, b):
    """STRICT -- a wrong match files a picture on the wrong patient. Whole words only (no prefixes): every word of the
    shorter name is a word of the other; a one-word name matches only a one-word name; or the two written together are
    the same."""
    if not a or not b:
        return False
    if "".join(a) == "".join(b):
        return True
    short, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if not all(x in long_ for x in short):
        return False
    return len(short) >= 2 or len(long_) == 1


def _s752_name_loose(a, b):
    """For a SUGGESTION only (a person confirms), and as the guard on (2): one word in common, or the same first four letters."""
    return any(x == y or (len(x) >= 4 and len(y) >= 4 and x[:4] == y[:4]) for x in a for y in b)


def _s752_one_off(a, b):
    """Two IDs one keystroke apart: one digit changed, two neighbours swapped, one digit added or left out."""
    a, b = str(a or ""), str(b or "")
    if a == b or not a or not b or abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        d = [i for i in range(len(a)) if a[i] != b[i]]
        if len(d) == 1:
            return True
        return len(d) == 2 and d[1] == d[0] + 1 and a[d[0]] == b[d[1]] and a[d[1]] == b[d[0]]
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s for i in range(len(l)))


def _s752_day(con, day, cache):
    """({clinic ID: [names]} of every X-ray patient of the day, {clinic ID: pictures filed that day}) -- read once per day."""
    if day in cache:
        return cache[day]
    pats = {}
    for s in _rows(con, "SELECT DISTINCT s.clinic_id, s.name_seen FROM slip s JOIN slip_item i ON i.slip_id=s.id "
                        "WHERE s.series='xp' AND s.state='ok' AND i.kind='xray' AND s.day=? AND s.clinic_id<>''", (day,)):
        pats.setdefault(s["clinic_id"], [])
        if s.get("name_seen"):
            pats[s["clinic_id"]].append(s["name_seen"])
    for d in _rows(con, "SELECT DISTINCT clinic_id, patient FROM clinic_day_line WHERE section='xray' AND business_date=? "
                        "AND clinic_id<>''", (day,)):
        pats.setdefault(d["clinic_id"], [])
        if d.get("patient"):
            pats[d["clinic_id"]].append(d["patient"])
    for cid, names in pats.items():
        r = _rows(con, "SELECT name FROM patient_ref WHERE clinic_id=? AND name<>'' LIMIT 1", (cid,))
        if r:
            names.append(r[0]["name"])
    filed = {r["clinic_id"]: r["n"] for r in _rows(con, "SELECT clinic_id, COUNT(*) n FROM record_file WHERE kind='xray' "
                                                        "AND state='ok' AND day=? GROUP BY clinic_id", (day,))}
    cache[day] = (pats, filed)
    return cache[day]


def _s752_by_name(con, day, orig, cache):
    """The ONE X-ray patient of the day whose name is the picture's name (strict), when no OTHER patient of that day shares
    even one word of it (loose) -- else ''. Never for a child's picture."""
    if _s752_child(xray_stem(orig)):
        return ""
    ft, fs = _s752_tokens(xray_stem(orig)), _s752_strict_tokens(xray_stem(orig))
    if not ft or not fs:
        return ""
    pats = _s752_day(con, day, cache)[0]
    strict = [c for c, names in pats.items() if any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in names)]
    loose = [c for c, names in pats.items() if any(_s752_name_loose(ft, _s752_tokens(n)) for n in names)]
    return strict[0] if len(strict) == 1 and loose == strict else ""


def _s752_utc(t):
    try:
        u = dt.datetime.fromisoformat(str(t or "")[:19]) - dt.timedelta(hours=5, minutes=30)
        return u.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    except ValueError:
        return ""


def _s752_retry(con, files, stamp, listed=True):
    """Plan again every unanswered picture in the check folder. Returns the mailbox items (action 'file')."""
    out = []
    rows = {}
    if files:
        rows = {r["src_id"]: r for r in _rows(con, "SELECT * FROM xray_filing WHERE src_id IN (%s)" % ",".join("?" * len(files)),
                                             tuple(f.get("id") or "" for f in files))}
    feed = []
    c772, s772_why, s772_day = {}, {}, {}                # S772: the planned day and its reason, per picture
    o782 = {f.get("id"): f.get("name") or "" for f in files}
    files, s782_why = _s782_files(con, files, rows, c772)   # S782 (a): photo numbers out of the names, for every rule below
    s782_dup = {}                                        # S782 (b): second uploads of a photo already filed -- never filed again
    for f in files:
        dd = _s782_second(con, f.get("id") or "", f.get("name") or "", c772, o782.get(f.get("id")) or "")
        if dd[0]:                                        # never planned to file; a row planned before goes back to the list below,
            r0 = rows.get(f.get("id")) or {}               # and is sent to duplicates on the next run; one already sent there is
            if r0.get("state") == "check" or (r0.get("state") == "planned" and r0.get("action") == "dup"   # asked again until done
                                              and str(r0.get("verdict") or "").startswith(S782_MARK)):
                s782_dup[f.get("id")] = dd
            continue
        f2 = dict(f)
        u = _s752_utc((rows.get(f.get("id")) or {}).get("file_time"))
        d772, w772 = _s772_day(con, f, rows.get(f.get("id")) or {}, c772)   # S772: the film's date / the ID's one open day
        if d772:
            u = _s752_utc(d772 + " 12:00:00")
            s772_why[f.get("id")] = w772
            s772_day[f.get("id")] = d772
        if u:                                              # the day first seen, not a time Drive may have moved
            f2.pop("imageMediaMetadata", None)
            f2["modifiedTime"] = u
        feed.append(f2)
    feed, s772_held = _s772_hold(con, feed, files, rows, s772_day, c772)   # S772: older copies held for the clean-up
    cache, placed = {}, {}
    today = _today()
    plan = [r for r in (xray_plan(con, feed) if feed else []) if r.get("id") and r.get("time")]
    plan.sort(key=lambda r: (r["time"], r["orig"]))
    for r in plan:
        sid = r["id"]
        row = rows.get(sid) or {}
        if row and row.get("state") not in ("check", "planned"):
            continue
        if row.get("state") == "planned" and not str(row.get("verdict") or "").startswith("S752"):
            continue                                       # planned by another road (a person's answer)
        day = r["time"].date().isoformat()
        cid, how, use_proposed = "", "", False
        if r["kind"] in ("ok", "differ") and r.get("cid") and r.get("proposed"):
            cid, how, use_proposed = r["cid"], "ID %s is now on %s's X-ray list" % (r["cid"], _dmy(day)), True
        elif r["kind"] == "check" and day < today and _s772_film_id(con, sid, r["orig"], day, cache):   # S772
            cid = _s772_film_id(con, sid, r["orig"], day, cache)
            how = "the clinic ID printed on the film, %s, is one of %s's X-ray patients" % (cid, _dmy(day))
        elif r["kind"] == "check" and xray_id(r["orig"])[1] == "none" and day < today:
            cid = _s752_by_name(con, day, r["orig"], cache)
            how = ("no ID on the picture; its name is that of %s's one X-ray patient %s" % (_dmy(day), cid)) if cid else ""
        if not cid and r["kind"] == "check" and day < today:   # S776: what nothing else placed
            cid, how = _s776_more(con, sid, r["orig"], day, cache)
        if not cid and r["kind"] == "check" and day < today:   # S782 (d): ONE X-ray patient's name but for the spelling
            cid, how, d782 = _s782_spell(con, sid, r["orig"], day, cache)
            if cid and d782:
                day = d782
        if not cid:
            continue
        if _s782_film_other(con, sid, cid, day, cache):   # S782 (c): the film prints another patient of that day -- a person decides
            continue
        if sid in s772_why:                              # S772: say why this day
            how = s772_why[sid] + " -- " + how
        if sid in s782_why:                              # S782 (a): say the number was a photo number
            how = s782_why[sid] + " -- " + how
        filed = _s752_day(con, day, cache)[1].get(cid, 0)
        onway = _rows(con, "SELECT COUNT(*) n FROM xray_filing WHERE state='planned' AND action='file' AND clinic_id=? AND day=? "
                           "AND src_id<>? AND NOT (verdict LIKE 'S752%%' AND src_id IN (%s))" % ",".join("?" * len(files)),
                      (cid, day, sid) + tuple(f.get("id") or "" for f in files))
        onway = onway[0]["n"] if onway else 0
        k = placed.get((day, cid), 0)
        placed[(day, cid)] = k + 1
        if use_proposed and not filed and not onway:
            name = r["proposed"]                           # the inbox's own name: the study, or 'X-ray k' of the group
        else:
            nm = _safe((person(con, cid) or {}).get("name") or "")
            name = " · ".join(x for x in (day, cid, nm, "X-ray %d" % (filed + onway + k + 1)) if x) + _xray_ext(r["orig"])
        cur = con.execute("UPDATE xray_filing SET action='file', clinic_id=?, day=?, new_name=?, state='planned', verdict=?, planned_at=? "
                          "WHERE src_id=? AND state IN ('check','planned')", (cid, day, name, "S752 re-try: " + how, stamp, sid))
        if cur.rowcount == 1:
            out.append({"id": sid, "action": "file", "name": name, "path": _xray_path(day)})
    for sid, (dcid, dday) in sorted(s782_dup.items()):   # S782 (b): to "X-ray inbox / _filed / duplicates", never deleted
        cur = con.execute("UPDATE xray_filing SET action='dup', state='planned', verdict=?, planned_at=? WHERE src_id=? AND (state='check' "
                          "OR (state='planned' AND action='dup' AND verdict LIKE 'S782%'))",
                          (S782_MARK + "a second upload of the photo already filed for ID %s on %s -- the same name, and the same "
                           "date and ID printed on the film" % (dcid, _dmy(dday)), stamp, sid))
        if cur.rowcount == 1:
            out.append({"id": sid, "action": "dup"})
    now_ids = {i["id"] for i in out}
    in_folder = {f.get("id") for f in files}
    for f in files:                                        # planned before, does not place now -> back to the check list
        sid = f.get("id") or ""
        row = rows.get(sid) or {}
        if sid and sid not in now_ids and row.get("state") == "planned" and (str(row.get("verdict") or "").startswith("S752") or (
                row.get("action") == "dup" and str(row.get("verdict") or "").startswith(S782_MARK))):   # S782: a duplicate no longer one
            con.execute("UPDATE xray_filing SET action='check', clinic_id=?, new_name='', state='check', "
                        "verdict='S752: no longer placed -- back in the check list' WHERE src_id=? AND state='planned'",
                        (xray_id(row.get("orig_name") or "")[0], sid))
    if listed:                                             # planned here, left the folder by another road a day ago -> gone
        cut = (_now() - dt.timedelta(hours=S752_SWEEP_HOURS)).strftime("%Y-%m-%d %H:%M:%S")
        for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND verdict LIKE 'S752%' AND planned_at<?", (cut,)):
            if r["src_id"] not in in_folder:
                con.execute("UPDATE xray_filing SET state='gone', verdict='S752: left the check folder by another road' "
                            "WHERE src_id=? AND state='planned'", (r["src_id"],))
        for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND action='dup' AND verdict LIKE 'S782%' "
                            "AND planned_at<?", (cut,)):   # S782 (b): sent to duplicates and gone from the folder a day ago
            if r["src_id"] not in in_folder:
                con.execute("UPDATE xray_filing SET state='dup', done_at=? WHERE src_id=? AND state='planned'", (stamp, r["src_id"]))
    out.extend(_s772_tidy(con, files, rows, stamp, c772))   # S772: the clean-up
    con.commit()
    return out


def _s752_retry_safe(con, files, stamp, notes, listed=True):
    """The re-try never stops, and never undoes, the filing it rides on: this run's inbox rows and a person's answers are
    COMMITTED first; then any error in the re-try is a note, its own half-work rolled back, and the run goes on as before."""
    con.commit()
    try:
        return _s752_retry(con, files, stamp, listed)
    except Exception as ex:                              # noqa: BLE001
        try:
            con.rollback()
        except Exception:                                # noqa: BLE001
            pass
        notes.append("S752 re-try skipped: %s" % type(ex).__name__)
        return []


def _s752_suggest(con, row, cache):
    """(clinic ID, words, prefill) for a parked picture a person must look at, or ('', '', False). prefill only for an ID
    one keystroke off, or a strict name match."""
    day = str(row.get("day") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        return "", "", False
    pats, filed = _s752_day(con, day, cache)
    if not pats:
        return "", "", False
    unfiled = [c for c in pats if not filed.get(c)]
    orig = row.get("orig_name") or ""

    def nm(c):
        return (pats.get(c) or [""])[-1] or "—"
    cid, how = xray_id(orig)
    if how == "one" and cid and cid not in pats:
        near = [c for c in unfiled if _s752_one_off(cid, c)]
        if len(near) == 1:
            return near[0], "Shayad ID %s (%s) — photo par %s likha hai, ek ank alag" % (near[0], nm(near[0]), cid), True
    ft = _s752_tokens(xray_stem(orig))
    if ft:
        fs = _s752_strict_tokens(xray_stem(orig))
        strict = [c for c in pats if fs and any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in pats[c])]
        loose = [c for c in pats if any(_s752_name_loose(ft, _s752_tokens(n)) for n in pats[c])]
        if len(loose) == 1 and loose[0] in unfiled:
            strong = strict == loose and not _s752_child(xray_stem(orig))
            return loose[0], ("Shayad ID %s (%s) — naam milta hai" % (loose[0], nm(loose[0])) if strong else
                              "Shayad ID %s (%s)? Naam thoda milta hai — dekh kar ID likhein" % (loose[0], nm(loose[0]))), strong
    return "", "", False


_s752_xray_items_before = xray_items


def xray_items(con):
    """S752: the S373 items, and on a parked picture the likely ID (in its box when it is a strong one)."""
    out = _s752_xray_items_before(con)
    try:
        rows = {"xf:" + r["src_id"]: r for r in _rows(con, "SELECT * FROM xray_filing WHERE state='check'")}
        cache = {}
        for i in out:
            if i.get("kind") != "xray_file":
                continue
            r = rows.get(i.get("key"))
            if not r:
                continue
            sug, words, prefill = _s752_suggest(con, r, cache)
            if sug:
                if prefill:
                    i["suggest"] = sug
                i["why"] = ((i.get("why") or "") + " · " if i.get("why") else "") + words
    except Exception:                                    # noqa: BLE001 -- a suggestion never breaks the page
        pass
    return out


# ---------------------------------------------------------------- S757 (S413, 09-Nov-2026, D875): check_screens' doors
# The photo and lab-report screens live in check_screens.py beside this file; their doors go on THIS blueprint here, at import,
# before finance_app registers it. Without that file (or on any fault in it) nothing is added and Check karein is the old list.
try:
    import sys as _s757_sys
    import check_screens as _s757                         # noqa: E402
    _s757.attach(_s757_sys.modules[__name__])
except Exception:                                        # noqa: BLE001
    _s757 = None


# ---------------------------------------------------------------- S772: the film's own date and ID, the ID's one open day, the clean-up
# S772_XRAY_FILM_DATE (the parent, S422, 10-Nov-2026; the owner 10:56-11:13 IST, "do all thats possible"). A picture prepared
# afresh on the X-ray PC carries no picture time, so its day was its file time -- the day it was re-added -- and its ID was
# never on that day's X-ray list: parked for ever (18 on 09-Nov). The S752 re-try now plans such a picture on another day ONLY
# after xray_filmdate.py has read its film, and only when the patient is confirmed -- the ID printed on the film is the file's
# ID, or the picture's name matches the ID's patient STRICTLY (the S752 rule for filing; a loose match never files):
#   (1) the date printed on the film, when it is one of that ID's X-ray days (or its one open day within 2 days of it);
#   (2) the ID printed on the film when the file's name has none or another: that ID's X-ray day, its patient's name strict;
#   (3) with no date on the film: the ID's ONE X-ray day with no photo in the S772_BACK_DAYS before it was first seen.
# Anything else stays for a person. The clean-up runs only AFTER the mailbox has filed the corrected copy (state 'done'), and
# moves to "X-ray inbox / _filed / duplicates" (never deletes):
#   (a) the older parked copies of the same name -- ID none or not on that day's list, never the same ID, first seen within 3
#       days, their own film read agreeing (a date within 2 days, no other ID printed) -- only when the corrected copies
#       already cover the study's films and there are no more old copies than corrected ones (held out of the plan meanwhile,
#       so they are not filed beside it as its 'sisters');
#   (b) a copy filed to ANOTHER patient that day under a mistyped ID, when that patient shares no word of the name and has
#       more photos that day than films (so it is not his own X-ray), while the corrected copy's own film printed its ID (or its
#       patient's name is the picture's, strictly) -- its record made 'void' with the reason.
S772_BACK_DAYS = 60
S772_FILM_WINDOW = 120
S772_MARK = "S772 · "
S772_TIDY_DAYS = 14


def _s772_film(con, sid):
    """([iso dates], [clinic IDs]) read from the film by xray_filmdate.py; None when the film has not been read yet."""
    try:
        r = con.execute("SELECT * FROM xray_filmdate WHERE src_id=?", (sid,)).fetchone()
    except Exception:                                    # noqa: BLE001 -- no table yet (xray_filmdate.py not run)
        return None
    if not r:
        return None
    try:
        ds = [d for d in json.loads(r["dates"] or "[]") if re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)) and _s782_real_day(d)]   # S782
    except ValueError:
        ds = []
    try:
        ids = [str(x) for x in json.loads(r["ids"] or "[]") if re.fullmatch(r"\d{4,6}", str(x))] if "ids" in r.keys() else []
    except ValueError:
        ids = []
    return ds, ids


def _s772_xray_days(con, cid):
    s = {r["day"] for r in _rows(con, "SELECT DISTINCT s.day FROM slip s JOIN slip_item i ON i.slip_id=s.id WHERE s.clinic_id=? "
                                      "AND s.series='xp' AND s.state='ok' AND i.kind='xray'", (cid,))}
    s |= {r["d"] for r in _rows(con, "SELECT DISTINCT business_date d FROM clinic_day_line WHERE clinic_id=? AND section='xray'", (cid,))}
    return s


def _s772_open_days(con, cid):
    filed = {r["day"] for r in _rows(con, "SELECT DISTINCT day FROM record_file WHERE clinic_id=? AND kind='xray' AND state='ok'", (cid,))}
    return {d for d in _s772_xray_days(con, cid) if d not in filed}


def _s772_shift(iso, days):
    return (dt.date.fromisoformat(iso) + dt.timedelta(days=days)).isoformat()


def _s772_near(d, dates, k=2):
    return any(_s772_shift(x, -k) <= d <= _s772_shift(x, k) for x in dates)


def _s772_names(con, cid):
    out = [(person(con, cid) or {}).get("name") or ""]
    out += [r["n"] for r in _rows(con, "SELECT DISTINCT name_seen n FROM slip WHERE clinic_id=? AND name_seen<>''", (cid,))]
    out += [r["n"] for r in _rows(con, "SELECT DISTINCT patient n FROM clinic_day_line WHERE clinic_id=? AND patient<>''", (cid,))]
    return [n for n in out if n]


def _s772_strict(con, cid, orig):
    """The picture's name is, word for word, the ID's patient (the S752 filing rule). False when the picture has no name or is a
    child's picture."""
    st = xray_stem(orig)
    fs = _s752_strict_tokens(st)
    if not fs or _s752_child(st):
        return False
    return any(_s752_name_match(fs, _s752_strict_tokens(n)) for n in _s772_names(con, cid))


def _s772_match(con, cid, film):
    """The ONE X-ray day of this ID the film's dates point to: a film date that is one of its X-ray days; else its one day with
    no photo within 2 days of a film date (the slip is sometimes written the next day). '' when none or more than one."""
    xd = _s772_xray_days(con, cid)
    hit = sorted({d for d in film if d in xd})
    if len(hit) == 1:
        return hit[0]
    if hit:
        return ""
    near = sorted(d for d in _s772_open_days(con, cid) if _s772_near(d, film))
    return near[0] if len(near) == 1 else ""


def _s772_day(con, f, row, cache):
    """(day, why) -- the day a parked picture is planned on instead of its first-seen day -- or ('', '')."""
    sid, orig = f.get("id") or "", f.get("name") or ""
    first = str(row.get("file_time") or row.get("day") or "")[:10]
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", first):
        return "", ""
    fr = _s772_film(con, sid)
    if fr is None:
        return "", ""                                    # the film not read yet: wait for xray_filmdate.py
    fd, fids = fr
    film = sorted({d for d in fd if _s772_shift(first, -S772_FILM_WINDOW) <= d <= first})
    cid, how = xray_id(orig)
    if how == "many":
        return "", ""
    for x in fids:                                       # (2) the film prints another ID than the file's name
        if x != cid and film:
            d = _s772_match(con, x, film)
            if d and d != first and _s776_ok(con, x, orig, d, cache):   # S776: strict, or a whole word and no neighbour ID
                if how == "one" and cid in _s752_day(con, d, cache)[0]:
                    return "", ""                        # the file's own (other) ID is an X-ray patient that day too: a person decides
                return d, S772_MARK + "the date and the ID %s printed on the film give its X-ray day %s" % (x, _dmy(d))
    if how == "one":
        if (fids and cid not in fids) or (cid not in fids and not _s772_strict(con, cid, orig)):
            return _s776_day_only(con, cid, film, first, cache)   # S776: the film's day only; the file's ID never files
        if film:                                         # (1)
            d = _s772_match(con, cid, film)
            return ((d, S772_MARK + "the date printed on the film (%s) gives ID %s's X-ray day %s"
                     % (", ".join(_dmy(x) for x in film), cid, _dmy(d))) if d and d != first else ("", ""))
        if cid in _s752_day(con, first, cache)[0]:
            return "", ""                                # on the first-seen day's list: the S752 path as before
        open_ = sorted(d for d in _s772_open_days(con, cid) if _s772_shift(first, -S772_BACK_DAYS) <= d <= first)   # (3)
        if len(open_) == 1:
            return open_[0], S772_MARK + "ID %s's only X-ray day with no photo in the %d days before (%s)" % (cid, S772_BACK_DAYS, _dmy(open_[0]))
        return "", ""
    if len(film) == 1 and film[0] != first:              # no ID: the day only; the S752 strict name rule (or the film's ID) decides
        return film[0], S772_MARK + "the date printed on the film, %s" % _dmy(film[0])
    return "", ""


def _s772_film_id(con, sid, orig, day, cache):
    """The clinic ID printed on the film when the film's date is this day (within 2) and the ID is ONE X-ray patient of the day
    whose name is the picture's, strictly -- for a parked picture whose name gives no ID or one not on that day's list."""
    fr = _s772_film(con, sid)
    if not fr or not fr[0] or not _s772_near(day, fr[0]):
        return ""
    pats = _s752_day(con, day, cache)[0]
    got = sorted({x for x in fr[1] if x in pats and _s776_ok(con, x, orig, day, cache)})   # S776
    return got[0] if len(got) == 1 else ""


def _s772_old(con, day, cid, st, n_new, files, rows, skip):
    """The older parked copies of a corrected picture (see the head of this section, (a)); [] unless every rule holds."""
    if not cid or not st or n_new < 1:
        return []
    studies = _day_studies(con, day, cid)[0]
    if n_new < max(1, len(studies)):
        return []                                        # the corrected copies do not cover the study's films: an old one may be a view
    pats = _s752_day(con, day, {})[0]
    old = []
    for f in files:
        sid = f.get("id") or ""
        r = rows.get(sid) or {}
        if not sid or sid in skip or r.get("state") != "check" or xray_stem(f.get("name")) != st:
            continue
        oc, how = xray_id(f.get("name") or "")
        if how == "many" or oc == cid or (oc and oc in pats):
            continue
        od = str(r.get("file_time") or r.get("day") or "")[:10]
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", od) or not _s772_near(od, [day], 3):
            continue
        fr = _s772_film(con, sid)
        if not fr or not fr[0] or not _s772_near(day, fr[0]) or (fr[1] and cid not in fr[1]):
            continue                                     # its own film must agree: the day, and no other ID
        old.append(sid)
    return old if len(old) <= n_new else []


def _s772_done_groups(con):
    """{(day, ID, name): [picture ids]} of the corrected copies the mailbox has FILED on an S772 day in the last S772_TIDY_DAYS."""
    since = (_now() - dt.timedelta(days=S772_TIDY_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    groups = {}
    for r in _rows(con, "SELECT src_id, clinic_id, day, orig_name FROM xray_filing WHERE state='done' AND action='file' AND verdict LIKE ? "
                        "AND done_at>=?", ("S752 re-try: " + S772_MARK + "%", since)):
        st = xray_stem(r["orig_name"])
        if st and r["clinic_id"] and r["day"]:
            groups.setdefault((r["day"], r["clinic_id"], st), []).append(r["src_id"])
    return groups


def _s772_hold(con, feed, files, rows, days, cache):
    """(feed without the older copies of pictures planned on an S772 day this run, the held ids) -- so they are not filed beside
    the corrected copy as its 'sisters'. They stay parked (Check karein) until the corrected copy is filed, then go to duplicates."""
    groups = {}
    for f in files:
        sid = f.get("id") or ""
        cid, how = xray_id(f.get("name") or "")
        if sid in days and how == "one":
            groups.setdefault((days[sid], cid, xray_stem(f.get("name"))), []).append(sid)
    held = set()
    for (day, cid, st), new in groups.items():
        held |= set(_s772_old(con, day, cid, st, len(new), files, rows, set(days)))
    for (day, cid, st), done in _s772_done_groups(con).items():     # filed already: its old copies wait for the clean-up below
        held |= set(_s772_old(con, day, cid, st, len(done), files, rows, set(days)))
    return [x for x in feed if x.get("id") not in held], held


def _s772_tidy(con, files, rows, stamp, cache):
    """The mailbox items of the clean-up (action 'dup'): every S772 one still waiting, and new ones for the corrected copies the
    mailbox has FILED (state 'done') in the last S772_TIDY_DAYS days."""
    res = [{"id": r["src_id"], "action": "dup"} for r in
           _rows(con, "SELECT src_id FROM xray_filing WHERE state='planned' AND action='dup' AND verdict LIKE 'S772%'")]
    planned = {i["id"] for i in res}
    for (day, cid, st), srcs in sorted(_s772_done_groups(con).items()):
        n = len(srcs)
        for sid in _s772_old(con, day, cid, st, n, files, rows, planned):
            cur = con.execute("UPDATE xray_filing SET action='dup', state='planned', verdict=?, planned_at=? WHERE src_id=? AND state='check'",
                              ("S772: replaced by the corrected copy filed for ID %s on %s" % (cid, _dmy(day)), stamp, sid))
            if cur.rowcount == 1:
                res.append({"id": sid, "action": "dup"})
                planned.add(sid)
        film_says = any(cid in ((_s772_film(con, s) or ([], []))[1]) for s in srcs)
        if not film_says and not any(_s752_name_match(_s752_strict_tokens(st), _s752_strict_tokens(nm)) for nm in _s772_names(con, cid)):
            continue                                     # the corrected copy's patient not confirmed (film ID or strict name): no judgement
        wrong = []
        for fr in _rows(con, "SELECT f.id, f.clinic_id, f.drive_id, x.orig_name FROM record_file f JOIN xray_filing x ON x.file_id=f.id "
                             "WHERE f.kind='xray' AND f.state='ok' AND f.day=? AND f.clinic_id<>? AND f.source='xray_inbox' "
                             "AND x.state='done'", (day, cid)):
            if xray_stem(fr["orig_name"]) != st or not re.fullmatch(r"[A-Za-z0-9_\-]{10,200}", fr["drive_id"] or ""):
                continue
            theirs = [_s752_tokens(nm) for nm in _s772_names(con, fr["clinic_id"])]
            if not theirs or any(_s752_name_loose(_s752_tokens(st), t) for t in theirs):
                continue                                 # that patient could be the picture's: never moved by itself
            photos = _rows(con, "SELECT COUNT(*) n FROM record_file WHERE kind='xray' AND state='ok' AND clinic_id=? AND day=?",
                           (fr["clinic_id"], day))[0]["n"]
            if photos <= max(1, len(_day_studies(con, day, fr["clinic_id"])[0])):
                continue                                 # no more photos than films: it may be his own X-ray, a person decides
            wrong.append(fr)
        if wrong and len(wrong) <= n:
            for fr in wrong:
                con.execute("UPDATE record_file SET state='void', note=? WHERE id=? AND state='ok'",
                            ("S772: filed under a mistyped ID; the corrected copy is filed for ID %s" % cid, fr["id"]))
                con.execute("INSERT INTO xray_filing(src_id, orig_name, file_time, action, clinic_id, day, new_name, state, verdict, planned_at) "
                            "VALUES (?,?,?,?,?,?,?,?,?,?) ON CONFLICT(src_id) DO NOTHING",
                            (fr["drive_id"], fr["orig_name"], "", "dup", fr["clinic_id"], day, "", "planned",
                             "S772: filed to ID %s by a mistyped ID -- the corrected copy is filed for ID %s" % (fr["clinic_id"], cid), stamp))
                if fr["drive_id"] not in planned:
                    res.append({"id": fr["drive_id"], "action": "dup"})
                    planned.add(fr["drive_id"])
    return res


# ---------------------------------------------------------------- S776: fewer pictures left for a person
# S776_XRAY_FEWER_LEFT (the parent, S422, 10-Nov-2026). The owner, 13:01 IST: "I do not want to leave any work for staff in Check
# karein as much as possible." S774 (read-only, on the live database after S772) found 41 of 70 still parked. S776 adds, for a
# picture nothing else placed (the film read; never a child's picture; names compared by WHOLE words, never by first letters):
#   R1 the ID printed on the film, on its X-ray day by the film's date, when the picture's name is that patient's strictly, OR
#      close (the same first word, or two words shared -- a surname alone never) and no patient of that day, X-rayed or only
#      seen, has an ID one keystroke off; a picture with no name is never placed on a read ID alone;
#   R2 the film's date within a day; the file has no ID (or one a keystroke off) and the film prints none (or his): the name
#      close to ONE X-ray patient of that day -- nobody else X-rayed that day close -- whose X-ray of that day has no photo;
#   R3 the ID printed on the film is a patient who CAME that day (a slip or a Docterz line) with no X-ray billed -- name as R1 --
#      or, with no ID on the film, the name is word for word ONE such patient: the picture is filed on him and appears on the
#      owner's "X-ray taken, no X-ray slip" list (S757), where it goes to Shavez to bill.


def _s776_words(a, b):
    return any(x == y for x in a for y in b)


def _s776_close(toks, names):
    """The picture's name and one of the patient's: the same FIRST word, or two whole words shared (a surname alone never)."""
    for n in names:
        t = _s752_tokens(n)
        if toks and t and (toks[0] == t[0] or len(set(toks) & set(t)) >= 2):
            return True
    return False


def _s776_neighbour(con, x, day, cache):
    """Another patient of that day -- X-rayed or only seen -- whose ID is one keystroke off x (an OCR misread could be him)."""
    others = set(_s752_day(con, day, cache)[0]) | _s776_visitors(con, day)
    return any(_s752_one_off(x, o) for o in others if o != x)


def _s776_ok(con, x, orig, day, cache):
    """The ID x may take this picture: its patient's name is the picture's strictly, or close (the same first word, or two words)
    while no patient of that day has an ID one keystroke off x. A picture with no name is never placed on a read ID alone."""
    st = xray_stem(orig)
    if _s752_child(st):
        return False
    if _s772_strict(con, x, orig):
        return True
    toks = _s752_tokens(st)
    return bool(toks) and _s776_close(toks, _s772_names(con, x)) and not _s776_neighbour(con, x, day, cache)


def _s776_day_only(con, cid, film, first, cache):
    """A picture whose own ID is not confirmed: its film's ONE date as the day -- only when its own ID is not an X-ray patient of
    that day (the S776 name and film-ID rules then decide, never the file's ID)."""
    if len(film) == 1 and film[0] != first and cid not in _s752_day(con, film[0], cache)[0]:
        return film[0], S772_MARK + "the date printed on the film, %s (the file's ID %s is not that day's)" % (_dmy(film[0]), cid)
    return "", ""


def _s776_visitors(con, day):
    s = {r["c"] for r in _rows(con, "SELECT DISTINCT clinic_id c FROM slip WHERE day=? AND state='ok' AND clinic_id<>''", (day,))}
    s |= {r["c"] for r in _rows(con, "SELECT DISTINCT clinic_id c FROM clinic_day_line WHERE business_date=? AND clinic_id<>''", (day,))}
    return s


def _s776_more(con, sid, orig, day, cache):
    """(clinic ID, why) for a parked picture nothing else placed -- R2 then R3 (see the head of this section) -- or ('', '')."""
    st = xray_stem(orig)
    if _s752_child(st):
        return "", ""
    fr = _s772_film(con, sid)
    if fr is None:
        return "", ""                                    # the film not read yet
    toks = _s752_tokens(st)
    pats, filed = _s752_day(con, day, cache)
    fid_ok = [x for x in fr[1] if re.fullmatch(r"\d{4,6}", x)]
    fcid, fhow = xray_id(orig)
    if toks and fr[0] and _s772_near(day, fr[0], 1) and not [x for x in fid_ok if x in pats]:   # R2
        hits = [c for c, names in pats.items() if _s776_close(toks, list(names) + _s772_names(con, c))]
        if len(hits) == 1 and not filed.get(hits[0]) \
                and (fhow == "none" or (fhow == "one" and _s752_one_off(fcid, hits[0]))) \
                and (not fid_ok or fid_ok == [hits[0]]):
            return hits[0], "S776 \u00b7 its name is close to %s's one matching X-ray patient %s, whose photo was missing" % (_dmy(day), hits[0])
        if hits:
            return "", ""                                # several, his photo there, or the file / film names another: a person decides
    if not fr[0] or not _s772_near(day, fr[0], 1):
        return "", ""
    vis = _s776_visitors(con, day) - set(pats)
    ids = sorted({x for x in fid_ok if x in vis and _s776_ok(con, x, orig, day, cache)})
    if len(ids) == 1:                                    # R3
        return ids[0], "S776 · the ID printed on the film, %s, came on %s with no X-ray billed" % (ids[0], _dmy(day))
    if not fid_ok and toks:                              # R3, no ID on the film: the name word for word
        vm = [c for c in vis if _s772_strict(con, c, orig)]
        if len(vm) == 1:
            return vm[0], "S776 · its name is, word for word, that of %s who came on %s with no X-ray billed" % (vm[0], _dmy(day))
    return "", ""


# ---------------------------------------------------------------- S782: the photo number and the second upload (F-1236)
# S782_XRAY_LEFTOVERS (the parent, S427, 11-Nov-2026). The owner, 13:01 IST 10-Nov: "I do not want to leave any work for staff in
# Check karein as much as possible." The re-try above (S752 / S772 / S776) now also knows two things:
#   (a) a 1-3-digit number in a picture's name ("NAME 2.jpg", "NAME 1234 2.jpg") is the photo's own sequence number, not a clinic
#       ID, when nobody who came on the picture's first-seen day, or on a date printed on its film (a day either side), has that
#       ID, and the picture's name is not that ID's patient -- the re-try reads the name without it; every rule above then decides
#       exactly as before (a number that IS such a patient is kept: an old patient's short ID still files);
#   (b) a parked picture whose film prints the same date(s) and the same clinic ID as a copy of the SAME NAME already filed on that
#       very ID under the very same file name -- whose X-rays of that day all have their photos -- is a second upload: it goes to "X-ray inbox / _filed /
#       duplicates" (never deleted) and is never filed a second time. A picture with no film read, no ID printed, two IDs in its
#       name, or its own ID another patient's, is never touched by (b);
#   (c) a picture is never filed by itself on one patient while its film prints the clinic ID of ANOTHER patient who came that
#       day (X-rayed or only seen) -- the staff's typing and the machine's print disagree on two real people: a person decides.
#       (Before S782 a name-only picture could be filed on its name's patient whatever the film printed.)
#   (d) the owner, 05:15 IST 11-Nov: "for the name, exact spelling might not be there" -- a picture nothing else placed, its film's
#       date read (within a day), is filed on the ONE X-ray patient of that day (or the day either side) whose photo is still
#       missing and whose name is the picture's but for the usual spelling variants (_s782_alike: SUNEETA = SUNITA, KAVITHA =
#       KAVITA; the first words must agree -- ANIL is never SUNIL, a surname alone never), while nobody else who came those days
#       -- X-rayed or only seen -- has a name like it; an ID printed on the film must be his (or one keystroke off); never a
#       child's picture, never a name of under six letters.
#   The owner's Check karein (check_screens.py) lists such names first ("Similar name"), the rest by letter likeness (_s782_sp).
S782_MARK = "S782 \u00b7 "


def _s782_real_day(d):
    """A calendar date (xray_filmdate.py checks this when it reads a film; a row written another way could carry 2026-02-30,
    which would stop every re-try)."""
    try:
        dt.date.fromisoformat(str(d))
        return True
    except ValueError:
        return False


def _s782_days(con, sid, first):
    """The first-seen day and every date printed on the film within S772_FILM_WINDOW before it, each with the day either side --
    None while the film has not been read (nothing is stripped before it is). A date that is no calendar date is skipped."""
    fr = _s772_film(con, sid)
    if fr is None:
        return None
    days = set()
    for d in [first] + list(fr[0]):
        try:
            if d != first and not (_s772_shift(first, -S772_FILM_WINDOW) <= d <= first):
                continue
            days |= {d, _s772_shift(d, -1), _s772_shift(d, 1)}
        except ValueError:                               # an OCR misread such as 2026-02-30 -- never stops the re-try
            continue
    return days or None


def _s782_strip(con, sid, name, first, cache):
    """(the name without its photo numbers, why) -- or ('', '') when no number is dropped (a)."""
    stem = IMG.sub("", name or "")
    short = [n for n in _NUM.findall(stem) if len(n) <= 3]
    if not short or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", first or ""):
        return "", ""
    days = _s782_days(con, sid, first)
    if not days:
        return "", ""
    who = set()
    for d in days:
        who |= set(_s752_day(con, d, cache)[0]) | _s776_visitors(con, d)
    drop = [n for n in short if n not in who and not _s772_strict(con, n, name)
            and not any(_s782_alike(_s752_tokens(xray_stem(name)), _s752_tokens(x)) for x in _s772_names(con, n))]   # (d)'s spelling too
    if not drop:
        return "", ""
    for n in drop:
        stem = re.sub(r"(?<!\d)%s(?!\d)" % n, " ", stem, count=1)
    ext = name[len(IMG.sub("", name)):]
    return stem + ext, S782_MARK + "%s in the name is the photo's number (no patient of that day has the ID)" % " and ".join(drop)


def _s782_files(con, files, rows, cache):
    """(files with the photo numbers taken out of their names, {picture id: why}) -- (a). The originals are not changed."""
    out, why = [], {}
    for f in files:
        row = rows.get(f.get("id")) or {}
        first = str(row.get("file_time") or row.get("day") or "")[:10]
        nm, w = _s782_strip(con, f.get("id") or "", f.get("name") or "", first, cache)
        if nm:
            f = dict(f, name=nm)
            why[f.get("id")] = w
        out.append(f)
    return out, why


def _s782_film_other(con, sid, cid, day, cache):
    """True when the film prints a clinic ID other than cid that is a patient who came that day (X-rayed or only seen): the
    staff's name and the machine's ID disagree on two real patients -- never filed by itself (c)."""
    fr = _s772_film(con, sid)
    if not fr or not fr[1]:
        return False
    who = set(_s752_day(con, day, cache)[0]) | _s776_visitors(con, day)
    return any(x != cid and x in who for x in fr[1])


def _s782_second(con, sid, name, cache, orig=""):
    """(clinic ID, day) of the one copy of this picture already filed -- (b) -- or ('', ''). The filed copy must carry the very
    same file name (a second view is always named apart: "NAME 1234 2"), and the picture's own name must be unchanged by (a)."""
    if orig and orig != name:
        return "", ""
    st = xray_stem(name)
    if not sid or not st or not _s752_tokens(st):
        return "", ""
    fr = _s772_film(con, sid)
    if not fr or not fr[0] or not fr[1]:
        return "", ""
    own, how = xray_id(name)
    if how == "many":
        return "", ""
    key = (sorted(set(fr[0])), sorted(set(fr[1])))
    hits = set()
    for x in _rows(con, "SELECT x.src_id, x.orig_name, x.clinic_id, x.day FROM xray_filing x JOIN record_file f ON f.id=x.file_id "
                        "WHERE x.state='done' AND x.action='file' AND f.state='ok' AND f.kind='xray' AND x.src_id<>? "
                        "AND x.clinic_id IN (%s)" % ",".join("?" * len(key[1])), (sid,) + tuple(key[1])):
        if (x["orig_name"] or "").strip().upper() != (name or "").strip().upper() or (own and own != x["clinic_id"]) or not x["day"]:
            continue
        fx = _s772_film(con, x["src_id"])
        if not fx or (sorted(set(fx[0])), sorted(set(fx[1]))) != key:
            continue
        n_st = len(_day_studies(con, x["day"], x["clinic_id"])[0])
        if not n_st or _s752_day(con, x["day"], cache)[1].get(x["clinic_id"], 0) < n_st:
            continue                                     # a film of that day still has no photo: this could be it -- a person decides
        hits.add((x["clinic_id"], x["day"]))
    return sorted(hits)[0] if len(hits) == 1 else ("", "")


S782_SPELL_SHOW = 0.70                                   # Check karein: the order of the rest (letter likeness), never a tag
_S782_PH = (("ee", "i"), ("ii", "i"), ("oo", "u"), ("aa", "a"), ("w", "v"), ("ph", "f"), ("sh", "s"), ("th", "t"), ("dh", "d"),
            ("bh", "b"), ("kh", "k"), ("gh", "g"), ("jh", "j"), ("ch", "c"), ("q", "k"), ("y", "i"))   # no z->j: RAZA is not RAJA


def _s782_ph(w):
    """A name word as it SOUNDS in the usual Hindi spellings: SUNEETA = SUNITA, KAVITHA = KAVITA, RAMESHWAR = RAMESVAR."""
    w = str(w or "").lower()
    for a, b in _S782_PH:
        w = w.replace(a, b)
    return re.sub(r"(.)\1+", r"\1", w)


def _s782_lev1(a, b):
    """True when a and b differ by ONE vowel inside the word in a way Hindi names are usually spelt both ways: E/I (or I/E),
    O/U, A/E, or an A put in or left out -- never the first or the last letter (RAMESHWAR / RAMESHWER yes; VANITA / VINITA and
    MANISHA / MONISHA no -- A/I and A/O are different names; SARITA / SARIKA no -- a consonant; RAJKUMAR / RAJKUMARI no -- the end)."""
    ok = ({"e", "i"}, {"o", "u"}, {"a", "e"})
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) == len(b):
        d = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
        return len(d) == 1 and 0 < d[0] < len(a) - 1 and {a[d[0]], b[d[0]]} in ok
    s, l = (a, b) if len(a) < len(b) else (b, a)
    return any(l[:i] + l[i + 1:] == s and 0 < i < len(l) - 1 and l[i] == "a" for i in range(len(l)))


def _s782_word(a, b):
    """Two name words the same person's: the same sound, or -- both six letters or more, the same first letter -- one vowel
    apart inside the word (RAMESHWAR / RAMESHWER). ANIL is never SUNIL; SUNITA is never SUNIL; SARITA is never SARIKA."""
    pa, pb = _s782_ph(a), _s782_ph(b)
    return pa == pb or (len(pa) >= 6 and len(pb) >= 6 and pa[0] == pb[0] and _s782_lev1(pa, pb))


def _s782_alike(pic, pat):
    """The picture's name is the patient's, allowing the usual spelling variants: every word of the picture pairs with its own
    word of the patient's name, the FIRST words with each other (a surname alone never); a one-word name only a one-word name."""
    if not pic or not pat or not _s782_word(pic[0], pat[0]):
        return False
    if len(pic) < 2 and len(pat) > 1:
        return False
    rest = list(pat[1:])
    for w in pic[1:]:
        k = next((i for i, x in enumerate(rest) if _s782_word(w, x)), None)
        if k is None:
            return False
        rest.pop(k)
    return True


def _s782_sp(toks, names):
    """0..1, letter likeness of the picture's name to the nearest of these names -- ONLY the order of a list a person reads."""
    import difflib                                       # noqa: PLC0415
    if not toks:
        return 0.0
    a, a2 = " ".join(toks), " ".join(sorted(toks))
    best = 0.0
    for n in names or []:
        t = _s752_tokens(n)
        if t:
            best = max(best, difflib.SequenceMatcher(None, a, " ".join(t)).ratio(),
                       difflib.SequenceMatcher(None, a2, " ".join(sorted(t))).ratio())
    return best


def _s782_names(con, cid, cache):
    k = ("s782n", cid)
    if k not in cache:
        cache[k] = _s772_names(con, cid)
    return cache[k]


def _s782_spell(con, sid, orig, day, cache):
    """(clinic ID, why, his X-ray day) by the name's spelling variants -- (d) -- or ('', '', '')."""
    st = xray_stem(orig)
    toks = _s752_tokens(st)
    if not toks or len("".join(toks)) < 6 or _s752_child(st):
        return "", "", ""
    fr = _s772_film(con, sid)
    if not fr or not fr[0] or not _s772_near(day, fr[0], 1):
        return "", "", ""
    own, how = xray_id(orig)
    if how == "many":
        return "", "", ""
    everyone, open_ = set(), {}
    for d in (day, _s772_shift(day, -1), _s772_shift(day, 1)):   # the film's day first
        pats, filed = _s752_day(con, d, cache)
        everyone |= set(pats) | _s776_visitors(con, d)
        for c in pats:
            if c not in open_ and filed.get(c, 0) < max(1, len(_day_studies(con, d, c)[0])):
                open_[c] = d
    def alike(c):
        return any(_s782_alike(toks, _s752_tokens(n)) for n in _s782_names(con, c, cache))
    hits = [c for c in sorted(open_) if alike(c)]
    if len(hits) != 1:
        return "", "", ""
    best = hits[0]
    if any(c != best and (alike(c) or _s776_close(toks, _s782_names(con, c, cache))) for c in everyone):
        return "", "", ""                                # anyone else who came those days could be the picture's: a person decides
    if open_[best] >= _today():
        return "", "", ""                                # his day is not over: everyone who came is not known yet
    for x in list(fr[1]) + ([own] if own else []):       # every ID the film prints or the name carries: his, or a slip of the
        if x != best and not (_s752_one_off(x, best) and not _known_id(con, x)):   # keys that is NOBODY's ID
            return "", "", ""
    return best, (S782_MARK + "its name is %s's X-ray patient %s's but for the spelling, and his photo was missing; nobody "
                  "else who came those days has a name like it" % (_dmy(open_[best]), best)), open_[best]
