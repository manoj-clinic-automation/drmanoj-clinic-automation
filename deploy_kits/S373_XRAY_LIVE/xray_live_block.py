

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
    in_check = set()
    if cfid:
        cf, why = drive_list(cfid)
        if cf is None:
            notes.append("xray_check_id: %s" % why)
        else:
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
    for r in _rows(con, "SELECT src_id FROM xray_filing WHERE state='check'"):
        if cfid and r["src_id"] not in in_check and r["src_id"] not in ids:
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
