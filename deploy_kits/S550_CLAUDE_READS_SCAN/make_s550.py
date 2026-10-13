#!/usr/bin/env python3
"""make_s550.py -- S550_CLAUDE_READS_SCAN (D723): asset_register.py learns to ask Claude first when it reads a scan.

    python3 make_s550.py <dir with the live asset_register.py> <out dir>

Exact counted edits on the pinned live bytes (BUILD_NORM_v1). Refuses when the input is not the pin or an anchor is not found
exactly the counted number of times. claude_reader.py and claude_reread.py are new files, copied as they are."""
import hashlib, os, shutil, sys

FROM = "99652ff0ca4f8f52377b0c6f210eb4c9"
HERE = os.path.dirname(os.path.abspath(__file__))

EDITS = [
    # E1 -- the import, fail-soft (the app runs exactly as before when the module is absent)
    ("""try:                # S441 (D643): the after-the-fact checks and the shared login's name -- fail-soft, the scan never waits on them
    import scan_checks_s441 as S441
except Exception:
    S441 = None
""",
     """try:                # S441 (D643): the after-the-fact checks and the shared login's name -- fail-soft, the scan never waits on them
    import scan_checks_s441 as S441
except Exception:
    S441 = None
try:                # S550 (D723): Claude reads the scan first; Sarvam reads when Claude answers nothing -- fail-soft
    _S550_DIR = os.path.dirname(os.path.abspath(__file__))
    if _S550_DIR not in _sys.path:
        _sys.path.append(_S550_DIR)
    import claude_reader as CLAUDE
except Exception:
    CLAUDE = None
""", 1),
    # E2 -- one more reader: Sarvam OR Claude
    ("""def _sarvam_on():
    return bool(SARVAM is not None and getattr(SARVAM, "available", lambda: False)())
""",
     """def _sarvam_on():
    return bool(SARVAM is not None and getattr(SARVAM, "available", lambda: False)())

def _claude_on():                                                                    # S550 (D723)
    try:
        return bool(CLAUDE is not None and CLAUDE.available(DB_PATH))
    except Exception:
        return False

def _reader_on():                                                                    # S550: a scan can be read by Sarvam OR Claude
    return _sarvam_on() or _claude_on()
""", 1),
    # E3 -- the bill page offers the re-read when either reader is there
    ("""        b=b, items=items, sarvam_on=_sarvam_on(), blank=blank,""",
     """        b=b, items=items, sarvam_on=_reader_on(), blank=blank,""", 1),
    # E4 -- the background reading: Claude first, then Sarvam exactly as before
    ("""    try:
        data, st = SARVAM.extract(path, schema=ASSET_BILL_SCHEMA)
        if st != "done" or data is None:
            _set_ocr_status(bid, "failed"); return "failed"
        hdr, items = _map_bill(data)
        db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row""",
     """    try:
        _cr = _reading if _reading is not None else _s550_claude(bid, path)    # S550 (D723): Claude reads first
        if _cr is not None:
            hdr, items = _cr
        else:                                                # Sarvam, exactly as before
            if not _sarvam_on():
                _set_ocr_status(bid, "failed"); return "failed"
            data, st = SARVAM.extract(path, schema=ASSET_BILL_SCHEMA)
            if st != "done" or data is None:
                _set_ocr_status(bid, "failed"); return "failed"
            hdr, items = _map_bill(data)
        db = sqlite3.connect(DB_PATH); db.row_factory = sqlite3.Row""", 1),
    # E5 -- the helper, placed just before _bg_extract; _bg_extract takes a reading already made (the older scans' pass)
    ("""def _bg_extract(bid, path):
""",
     """def _s550_claude(bid, path):
    \"\"\"S550 (D723): Claude reads the scan. Returns (hdr, items) to fill, or None -- then Sarvam reads exactly as before.
    Not sent to Claude: the Other-document lane and the Personal and Resumes sections (a person's papers; Sarvam as before).
    A pharmacy paper: Claude reads it BESIDE Sarvam (its own thread) and the reading is kept aside -- Sarvam fills it as
    before and never waits (the Sanjeevni side unchanged).\"\"\"
    if CLAUDE is None:
        return None
    try:
        if not CLAUDE.available(DB_PATH):
            return None
        _d = sqlite3.connect(DB_PATH); _d.row_factory = sqlite3.Row
        try:
            _r = _d.execute("SELECT lane, kind, subgroup FROM bills WHERE id=?", (bid,)).fetchone()
        finally:
            _d.close()
        if not _r:
            return None
        _lane = _r["lane"] or KIND_LANE.get(_r["kind"], "clinic")
        if _lane == "other_doc" or (_r["subgroup"] or "") in ("personal", "resume"):
            return None
        if _lane == "pharmacy":
            import threading
            threading.Thread(target=CLAUDE.read, args=(path,), kwargs={"bid": bid, "db_path": DB_PATH}, daemon=True).start()
            return None
        return CLAUDE.read_bill(path, bid=bid, db_path=DB_PATH)
    except Exception:
        return None

def _bg_extract(bid, path, _reading=None):
""", 1),
    # E6 -- the intake starts the reading when either reader is there
    ("""    if _sarvam_on():
        db.execute("UPDATE bills SET ocr_status='reading' WHERE id=?", (bid,)); db.commit()""",
     """    if _reader_on():                                                                 # S550: Sarvam OR Claude
        db.execute("UPDATE bills SET ocr_status='reading' WHERE id=?", (bid,)); db.commit()""", 1),
    # E7 -- the re-read door
    ("""    if not _sarvam_on():
        flash("Sarvam OCR isn't configured, so the bill can't be auto-read""",
     """    if not _reader_on():                                                             # S550: Sarvam OR Claude
        flash("Sarvam OCR isn't configured, so the bill can't be auto-read""", 1),
    ("""    flash("Re-reading the bill with Sarvam — refresh this page in a few seconds.")""",
     """    flash("Re-reading the bill — refresh this page in a few seconds.")""", 1),
    ("""<button class="btn small">🔄 Re-read with Sarvam</button>""",
     """<button class="btn small">🔄 Re-read</button>""", 1),
    # E8 -- the owner's switch
    ("""            flash("Reception's lane buttons on the bill intake are now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
""",
     """            flash("Reception's lane buttons on the bill intake are now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
        elif act == "set_read_claude":                                                 # S550 (D723)
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude',?)",
                       ("on" if request.form.get("on") == "1" else "off",))
            flash("Claude reading the scans is now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
""", 1),
    # E9 -- the card on /admin, under the lane buttons' card
    ("""<form method=post><input type=hidden name=action value=set_scan_lanes5><input type=hidden name=on value="{{'0' if lanes5 else '1'}}">
<button class="btn small">{{'Switch OFF' if lanes5 else 'Switch ON'}}</button></form></div>
""",
     """<form method=post><input type=hidden name=action value=set_scan_lanes5><input type=hidden name=on value="{{'0' if lanes5 else '1'}}">
<button class="btn small">{{'Switch OFF' if lanes5 else 'Switch ON'}}</button></form></div>
{% if claude %}<div class=card id=claude-reads><h4>Reading the scans \\u2014 Claude</h4>
<p class=muted>When ON, Claude reads every new scan first (handwriting and estimate slips too) and fills only what is empty; when it cannot, Sarvam reads as before. Pharmacy papers are read and kept aside; Sarvam still fills them. The key is kept on the server only. It stops by itself if the key is refused or the credit runs out, and Sarvam carries on.</p>
<p>Now: <b>{{claude.words}}</b> \\u00b7 read today {{claude.today}} (limit {{claude.cap}}) \\u00b7 read so far {{claude.ok}}{% if claude.failed %} \\u00b7 could not read {{claude.failed}}{% endif %}{% if claude.model %} \\u00b7 {{claude.model}}{% endif %}</p>
{% if claude.progress %}<p class=muted>The older scans: {{claude.progress}}</p>{% endif %}
{% if claude.key %}<form method=post><input type=hidden name=action value=set_read_claude><input type=hidden name=on value="{{'0' if claude.on else '1'}}">
<button class="btn small">{{'Switch OFF' if claude.on else 'Switch ON'}}</button></form>{% endif %}</div>{% endif %}
""", 1),
    ("""        scan_cv=_scan_cv_on(), opencv_present=os.path.exists(OPENCV_JS_PATH), lanes5=_lanes5_on(),          # S544                     # S523
""",
     """        scan_cv=_scan_cv_on(), opencv_present=os.path.exists(OPENCV_JS_PATH), lanes5=_lanes5_on(),          # S544                     # S523
        claude=_s550_admin(),                                                                                 # S550 (D723)
""", 1),
    # E10 -- what the card shows
    ("""@app.route("/admin", methods=["GET", "POST"])
""",
     """def _s550_admin():
    \"\"\"S550 (D723): the Claude card's figures. None when the module is absent (the card is then not shown).\"\"\"
    if CLAUDE is None:
        return None
    try:
        db = get_db()
        CLAUDE.ensure(db)
        st = CLAUDE.state(db)
        words = {"on": "ON", "off": "OFF", "no key": "no key on the server yet"}.get(st) or ("STOPPED \\u2014 " + st.split(":", 1)[-1])
        ok = db.execute("SELECT COUNT(*) FROM claude_reading WHERE ok=1").fetchone()[0]
        bad = db.execute("SELECT COUNT(*) FROM claude_reading WHERE ok=0").fetchone()[0]
        return {"on": st == "on", "key": CLAUDE.key_present(), "words": words, "today": CLAUDE.readings_today(db),
                "cap": CLAUDE.setting(db, "read.claude_daily_cap", CLAUDE.DAILY_CAP), "ok": ok, "failed": bad,
                "model": CLAUDE.setting(db, "read.claude_model", ""), "progress": CLAUDE.setting(db, "read.reread_progress", "")}
    except Exception:
        return None

@app.route("/admin", methods=["GET", "POST"])
""", 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    src, out = sys.argv[1], sys.argv[2]
    raw = open(os.path.join(src, "asset_register.py"), "rb").read()
    if md5(raw) != FROM:
        sys.exit("REFUSED: asset_register.py is %s, not the pinned %s" % (md5(raw)[:8], FROM[:8]))
    s = raw.decode("utf-8")
    for i, (old, new, n) in enumerate(EDITS, 1):
        c = s.count(old)
        if c != n:
            sys.exit("REFUSED: edit %d anchor found %d times, expected %d" % (i, c, n))
        s = s.replace(old, new)
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, "asset_register.py"), "wb").write(s.encode("utf-8"))
    for f in ("claude_reader.py", "claude_reread.py"):
        shutil.copy(os.path.join(HERE, f), os.path.join(out, f))
    print("asset_register.py %s -> %s (%d edits)" % (FROM[:8], md5(s.encode("utf-8")), len(EDITS)))


if __name__ == "__main__":
    main()
