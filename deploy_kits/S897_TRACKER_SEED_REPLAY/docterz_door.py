#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""docterz_door.py -- kit S897 (the parent, S493, 20-Nov-2026). NEW. THE DOCTERZ REPORTS -- ONE DOOR ON THE SERVER.

THE OWNER, 20-Nov-2026 15:18 IST (plan S492 FINAL s10): four kinds of Docterz CSV reach the clinic by four roads today
(reception's agent, his PC's Downloads pickup, the PC browser page's upload box, a by-hand run of the diagnosis seeder).
On the server there is ONE door, and every road leads to it. This is the owner's page of that door:

  /finance/console/docterz-reports   (his login, the console's gate)
    * one upload box: ANY Docterz CSV -- consultation report, follow-up log, clinical data report, patient list -- of any
      period (one evening or six months), any file name. It is recognised by its COLUMNS (docterz_pickup.identify, the
      box's own reader; a patient list by its 'Patient Medical History' + 'Parent Name' columns), never by its name;
    * a consultation report that spans days is CUT into business days (the PC orchestrator's own cut: header, the clinic's
      banner row, the day's UID-shaped rows) and each day goes through the same RUN / skip / 'newest wins' / QUARANTINE
      rules as reception's evening file (docterz_pickup.take): a known day with the same bytes is a duplicate, an older
      export is superseded, FEWER rows than held is quarantined and said, more rows replace the day (newest wins);
    * a follow-up log goes through whole, dated by its own first due date (S509: the day it was exported -- an old log
      uploaded today never becomes today's log); a clinical data report whole, by its bytes;
    * a patient list is KEPT by its bytes (STORE/patientlist/, mode 600) and listed -- the diagnosis seeder absorbs it in
      a later session (plan s8 item 5); nothing is run from it yet;
    * the answer is COUNTS: days new and taken, already known (skipped), superseded, quarantined -- never a patient;
    * the list below the box shows every export the box holds from every road (reception / Drive / this page / the
      not-sitting mark), newest first, and the four 'reaches' lines: last consultation report, last follow-up log (the
      due dates it reaches), last clinical data report, last patient list -- each with the date it reaches, so he knows
      what period to ask Docterz for.
A file taken here is read by the tracker's server runner within minutes (S895; from the switch evening -- OFF until then)
exactly as reception's files are: this door writes nothing but the export store and its table. No dialogs (F-1464).
NEVER prints a name or a number. The archive's bytes carry patients and stay mode 600 on the box (F-185, D656).

Mounted by owner_console.init beside the off-days page (the same gate); touches no database at mount (F-303).
"""
import csv
import datetime as dt
import hashlib
import io
import os
import re
import sys

VERSION = "S897 1"
PAGE_URL = "/finance/console/docterz-reports"
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES = 40 * 1024 * 1024
UID_RE = re.compile(r"[A-Z0-9]{8,14}")
LIST_ROWS = 60
KIND_WORDS = {"consultation": "consultation report", "followup": "follow-up log", "clinical": "clinical data report",
              "patientlist": "patient list", "unknown": "not a Docterz report"}


def _dp():
    if HERE not in sys.path:
        sys.path.insert(0, HERE)
    import docterz_pickup as DP                                   # noqa: PLC0415 -- the box's own reader (S443)
    return DP


def now():
    return dt.datetime.now()


# ── reading the file ───────────────────────────────────────────────────────────────────────────────
def _decode(raw):
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


def is_patient_list(raw):
    text = _decode(raw)
    if text is None:
        return False, 0
    try:
        rows = list(csv.reader(io.StringIO(text)))
    except csv.Error:
        return False, 0
    if not rows:
        return False, 0
    head = {h.strip() for h in rows[0]}
    if {"Patient Medical History", "Parent Name"} <= head:
        return True, sum(1 for r in rows[1:] if any(c.strip() for c in r))
    return False, 0


def cut_days(raw, parse_date):
    """a consultation report -> {iso day: (bytes of that day's file, the day's (UID set, rows))}, the PC orchestrator's cut
    (header, banner, the day's dated rows -- identify's own count, so the cut never reads fewer than the held day).
    {} when the file has no dated row (the empty not-sitting report goes through whole)."""
    text = _decode(raw)
    if text is None:
        return {}
    rows = list(csv.reader(io.StringIO(text)))
    if not rows:
        return {}
    head = [h.strip() for h in rows[0]]
    idx = {h: i for i, h in enumerate(head)}
    if "Consultation Date" not in idx or "Patient UID" not in idx:
        return {}
    di, ui = idx["Consultation Date"], idx["Patient UID"]
    banner = rows[1] if len(rows) > 1 and len(rows[1]) > ui and not rows[1][ui].strip() and not parse_date(rows[1][di] if len(rows[1]) > di else "") else None
    days = {}
    for r in rows[1:]:
        if len(r) <= di or not any(c.strip() for c in r):
            continue
        d = parse_date(r[di])                                     # identify's own rule: a row with a date is a row (the held count)
        if d:
            days.setdefault(d.isoformat(), []).append(r)
    out = {}
    for d, rs in days.items():
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\r\n")
        w.writerow(rows[0])
        if banner is not None:
            w.writerow(banner)
        for r in rs:
            w.writerow(r)
        out[d] = (("\ufeff" + buf.getvalue()).encode("utf-8"), ({r[ui].strip() for r in rs if len(r) > ui}, len(rs)))
    return out


def held_same(con, DP, day, uids, n):
    """the day's CURRENT consultation export holds the very same patients (count and UID set) -> nothing to take"""
    try:
        cur = con.execute("SELECT rows, stored FROM docterz_export WHERE kind='consultation' AND business_date=? AND status='current' "
                          "ORDER BY id DESC LIMIT 1", (day,)).fetchone()
        if cur is None or int(cur["rows"] or 0) != n or not cur["stored"] or not os.path.exists(cur["stored"]):
            return False
        with open(cur["stored"], "rb") as fh:
            parts = cut_days(fh.read(), DP.parse_date)
        got = parts.get(day)
        return bool(got) and got[1][0] == uids and got[1][1] == n
    except Exception:                                               # noqa: BLE001 -- unreadable: let take() decide
        return False


# ── taking ─────────────────────────────────────────────────────────────────────────────────────────
def take_upload(con, raw, name, who, dry=False):
    """one uploaded file -> (summary dict, [per-day lines]); counts only"""
    DP = _dp()
    DP.ensure(con)
    md5 = hashlib.md5(raw).hexdigest()
    kind, day, nrows, note = DP.identify(raw)
    mt = dt.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(name or "upload.csv"))[:80]
    res = {"kind": kind, "word": KIND_WORDS.get(kind, kind), "rows": nrows, "days": 0, "taken": 0, "already": 0,
           "superseded": 0, "quarantined": 0, "kept": 0, "refused": "", "stopped": "", "lines": [], "version": VERSION}
    if kind == "unknown":
        is_pl, n = is_patient_list(raw)
        if not is_pl:
            res["refused"] = "not one of the four Docterz reports -- nothing kept (%s)" % (note or "columns not recognised")
            return res
        res.update(kind="patientlist", word=KIND_WORDS["patientlist"], rows=n)
        seen = con.execute("SELECT id FROM docterz_export WHERE kind='patientlist' AND md5=?", (md5,)).fetchone()
        if seen is not None:
            res["already"] = 1
            res["lines"].append("patient list: already here (export #%d) -- nothing kept twice" % seen["id"])
            return res
        if not dry:
            d = os.path.join(DP.STORE, "patientlist")
            os.makedirs(d, mode=0o700, exist_ok=True)
            stored = os.path.join(d, "%s__%s.csv" % (now().strftime("%Y-%m-%d"), md5[:10]))
            with open(stored, "wb") as fh:
                fh.write(raw)
            os.chmod(stored, 0o600)
            con.execute("INSERT OR IGNORE INTO docterz_export (drive_id, drive_name, drive_mtime, md5, kind, business_date, rows, stored, "
                        "status, note, taken_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        ("owner:" + md5, base, mt, md5, "patientlist", now().date().isoformat(), n, stored, "kept",
                         "kept by this page (%s); the diagnosis seeder absorbs it in a later session" % who, now().isoformat(sep=" ")))
            con.commit()
        res["kept"] = 1
        res["lines"].append("patient list: kept (%d rows) -- absorbed by the diagnosis seeder in a later session" % n)
        return res
    if kind == "consultation":
        parts = cut_days(raw, DP.parse_date)
        if len(parts) > 1:
            res["days"] = len(parts)
            for d in sorted(parts):
                day_bytes, (uids, n) = parts[d]
                if held_same(con, DP, d, uids, n):                  # the same patients already held: nothing re-stored, nothing superseded
                    res["already"] += 1
                    res["lines"].append("%s: already here (the same %d patient%s) -- nothing changed" % (d, n, "" if n == 1 else "s"))
                    continue
                f = {"id": "owner:%s:%s" % (md5, d), "name": "%s__%s" % (base, d), "modifiedTime": mt}
                try:
                    k2, d2, n2, st, nt = DP.take(con, f, day_bytes, dry=dry)
                except Exception as ex:                             # noqa: BLE001 -- the days before it stand; said, counted
                    res["stopped"] = "the reader stopped at %s (%s); the days before it were taken" % (d, type(ex).__name__)
                    res["lines"].append("%s: the reader stopped (%s)" % (d, type(ex).__name__))
                    break
                _count(res, st)
                res["lines"].append("%s: %s (%d rows)%s" % (d2 or d, _word(st), n2, (" -- " + nt) if nt else ""))
            return res
        if not parts:
            res["lines"].append("no patient rows in it: the not-sitting rule decides the day (S868)")
    elif kind == "followup":
        # S509: a follow-up log's day is the day it was EXPORTED; Docterz's default range starts that day, so the log's own
        # first due date dates it -- never the upload's clock (an old log uploaded today must not become today's log)
        dfrom, _dto = DP.followup_span(raw)
        if dfrom:
            mt = "%sT10:00:00.000Z" % dfrom                         # 15:30 IST of that day: after 13:00, so export_day = that day
    f = {"id": "owner:" + md5, "name": base, "modifiedTime": mt}
    k2, d2, n2, st, nt = DP.take(con, f, raw, dry=dry)
    _count(res, st)
    res["days"] = 1 if d2 else 0
    res["lines"].append("%s %s: %s (%d rows)%s" % (KIND_WORDS.get(k2, k2), d2 or "(no date)", _word(st), n2, (" -- " + nt) if nt else ""))
    return res


def _word(st):
    return {"current": "taken", "duplicate": "already here", "superseded": "superseded (an older export)",
            "quarantined": "QUARANTINED -- not taken", "unknown": "not recognised"}.get(st, st)


def _count(res, st):
    key = {"current": "taken", "duplicate": "already", "superseded": "superseded", "quarantined": "quarantined"}.get(st)
    if key:
        res[key] += 1


# ── the page's reading ─────────────────────────────────────────────────────────────────────────────
def reaches(con):
    """the four 'reaches' lines: (kind word, date it reaches, how many current exports)"""
    out = []
    q = [("consultation report", "SELECT MAX(business_date), COUNT(*) FROM docterz_export WHERE kind='consultation' AND status='current' AND business_date<>''"),
         ("follow-up log (due dates reach)", "SELECT MAX(COALESCE(NULLIF(due_to,''), business_date)), COUNT(*) FROM docterz_export WHERE kind='followup' AND status='current'"),
         ("clinical data report", "SELECT MAX(business_date), COUNT(*) FROM docterz_export WHERE kind='clinical' AND status='current' AND business_date<>''"),
         ("patient list", "SELECT MAX(business_date), COUNT(*) FROM docterz_export WHERE kind='patientlist' AND status='kept'")]
    for word, sql in q:
        try:
            r = con.execute(sql).fetchone()
            out.append((word, (r[0] or "") if r else "", int(r[1] or 0) if r else 0))
        except Exception as ex:                                     # noqa: BLE001 -- a missing column (due_to before S507)
            out.append((word, "", 0))
    return out


def recent(con, n=LIST_ROWS):
    try:
        rows = con.execute("SELECT taken_at, kind, business_date, rows, status, note, drive_id, drive_name FROM docterz_export "
                           "ORDER BY id DESC LIMIT ?", (n,)).fetchall()
    except Exception:                                               # noqa: BLE001
        return []
    out = []
    for r in rows:
        src = str(r["drive_id"] or "")
        road = "this page" if src.startswith("owner:") else "reception's PC" if src.startswith("reception:") else \
               "not-sitting mark" if src.startswith("offday:") else "Drive folder"
        out.append({"at": str(r["taken_at"] or "")[:16], "kind": KIND_WORDS.get(r["kind"], r["kind"]), "day": r["business_date"] or "",
                    "rows": int(r["rows"] or 0), "status": r["status"], "note": _safe_note(str(r["note"] or "")), "road": road})
    return out


def _safe_note(s):
    """the table's notes are the reader's own words (counts, export numbers, dates); a file name is dropped all the same"""
    s = re.sub(r"\S+\.csv", "(file)", s)
    return s[:160]


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_CSS = ("body{font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;background:#f6f7f9;color:#1d2433}"
        ".w{max-width:860px;margin:0 auto;padding:16px}h1{font-size:20px;margin:6px 0 4px}.sub{color:#5b6475;margin:0 0 14px}"
        ".box{background:#fff;border:1px solid #dfe3ea;border-radius:10px;padding:14px;margin:0 0 12px}"
        "button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid #2b5cd6;background:#2b5cd6;color:#fff;cursor:pointer}"
        "button:disabled{opacity:.5}input[type=file]{font:inherit}"
        "table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:6px 6px;border-bottom:1px solid #eef0f4;vertical-align:top}"
        ".mut{color:#6b7385;font-size:13px}.ok{color:#137333}.bad{color:#b3261e}.warn{color:#9a6700}a{color:#2b5cd6}"
        "#ans{white-space:pre-wrap;font-size:14px;margin-top:10px}.reach td:first-child{width:45%}")


def page_html(con, who):
    rl = reaches(con)
    reach_rows = "".join("<tr><td>%s</td><td><b>%s</b> <span class=mut>(%d export%s held)</span></td></tr>"
                         % (_esc(w), _esc(d) if d else "<span class=bad>none yet</span>", n, "" if n == 1 else "s") for w, d, n in rl)
    lis = []
    for r in recent(con):
        cls = {"current": "ok", "kept": "ok", "quarantined": "bad", "superseded": "mut", "duplicate": "mut", "unknown": "warn"}.get(r["status"], "")
        lis.append("<tr><td class=mut>%s</td><td>%s</td><td>%s</td><td>%d</td><td class=%s>%s</td><td class=mut>%s</td><td class=mut>%s</td></tr>"
                   % (_esc(r["at"]), _esc(r["kind"]), _esc(r["day"]), r["rows"], cls, _esc(r["status"]), _esc(r["road"]), _esc(r["note"])))
    return ("<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>Docterz reports</title><style>%s</style></head><body><div class=w>"
            "<h1>Docterz reports -- one door</h1><p class=sub>Any Docterz CSV, any period, any file name: it is recognised by its "
            "columns, cut into days, and taken by the same rules as reception's evening files. Counts only.</p>"
            "<div class=box><form id=f><input type=file id=file accept='.csv,text/csv'> <button id=go type=submit>Upload and take</button>"
            "<div id=ans class=mut>Choose a consultation report, a follow-up log, a clinical data report or a patient list.</div></form></div>"
            "<div class=box><b>How far the box's reports reach</b><table class=reach>%s</table>"
            "<p class=mut>The clinical data report is never waited for: export it when you can, for any period, and it makes every list better "
            "from the day it arrives.</p></div>"
            "<div class=box><b>Exports the box holds</b> <span class=mut>(every road, newest first, last %d)</span>"
            "<table><tr><th>when</th><th>kind</th><th>day</th><th>rows</th><th>status</th><th>road</th><th>note</th></tr>%s</table></div>"
            "<p class=mut>Signed in as %s · %s</p></div>"
            "<script>const f=document.getElementById('f'),a=document.getElementById('ans'),g=document.getElementById('go');"
            "f.addEventListener('submit',async e=>{e.preventDefault();const i=document.getElementById('file');if(!i.files.length){a.textContent='Pick a file first.';return}"
            "g.disabled=true;a.className='mut';a.textContent='Reading ...';const fd=new FormData();fd.append('file',i.files[0]);"
            "try{const r=await fetch('%s',{method:'POST',body:fd});const j=await r.json();"
            "if(!j.ok){a.className='bad';a.textContent=j.why||('HTTP '+r.status)}else{const s=j.result;"
            "a.className=s.refused?'bad':(s.quarantined?'warn':'ok');"
            "a.textContent=s.refused?s.refused:(s.word+' -- '+s.rows+' rows, '+s.days+' day(s): '+s.taken+' taken, '+s.already+' already here, '"
            "+s.superseded+' superseded, '+s.quarantined+' quarantined'+(s.kept?', kept':'')+(s.stopped?' -- '+s.stopped:'')+'\\n'+(s.lines||[]).join('\\n'));"
            "if(!s.refused)setTimeout(()=>location.reload(),2500)}}catch(x){a.className='bad';a.textContent='Could not reach the box: '+x}"
            "g.disabled=false});</script></body></html>") % (_CSS, reach_rows, LIST_ROWS, "".join(lis), _esc(who), _esc(VERSION), PAGE_URL)


# ── the mount ──────────────────────────────────────────────────────────────────────────────────────
def init(app, db_getter, require_fn, unit="packs"):
    """Mount only; touches no database at mount (F-303). Called by owner_console.init, beside the off-days page."""
    from flask import Blueprint, Response, jsonify, request        # noqa: PLC0415
    bp = Blueprint("docterz_door", __name__)

    def _gate():
        return require_fn("checker", unit=unit)

    def _who(u):
        return str((u or {}).get("user") or (u or {}).get("username") or "owner")[:40]

    @bp.route(PAGE_URL, methods=["GET"])
    def docterz_door_page():
        u, err = _gate()
        if err:
            return Response("This page is for Dr Manoj's login.", status=403, mimetype="text/plain")
        con = db_getter()
        _dp().ensure(con)
        r = Response(page_html(con, _who(u)), mimetype="text/html")
        r.headers["Cache-Control"] = "no-store"
        return r

    @bp.route(PAGE_URL, methods=["POST"])
    def docterz_door_post():
        u, err = _gate()
        if err:
            return err
        f = request.files.get("file")
        if f is None or not f.filename:
            return jsonify(ok=False, why="no file in the request"), 400
        raw = f.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return jsonify(ok=False, why="the file is larger than %d MB" % (MAX_BYTES // (1024 * 1024))), 413
        if not raw.strip():
            return jsonify(ok=False, why="the file is empty"), 400
        con = db_getter()
        try:
            res = take_upload(con, raw, f.filename, _who(u))
        except Exception as ex:                                    # noqa: BLE001 -- said, never a trace with a row in it
            return jsonify(ok=False, why="the reader stopped: %s" % type(ex).__name__), 500
        return jsonify(ok=True, result=res, version=VERSION)

    @bp.route(PAGE_URL + "/healthz", methods=["GET"])
    def docterz_door_healthz():
        return Response("ok %s" % VERSION, mimetype="text/plain")

    app.register_blueprint(bp)
