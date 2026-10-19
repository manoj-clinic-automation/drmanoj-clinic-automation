#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s601.py -- S601_PHARMACY_BILLS_READ_BY_CLAUDE (D747): asset_register.py and claude_reread.py rebuilt from the pinned live bytes
(asset_register.py c39c084e, 4,920 lines; claude_reread.py d9b75e78) with anchored edits, each anchor found exactly once. These are the
ONLY two files changed. claude_reader.py, sorting_desk.py, clinic_papers.py, batteries.py, stationery.py, xray_costs.py, asset_machine.py,
scanner_widget.js, /root/shared/sarvam_ocr.py, the parent's packs.py and every Sanjeevni file are never touched.

    python3 -B make_s601.py <dir with the live asset_register.py and claude_reread.py> <out dir>

What the edits do (the brief claude_code_briefs/S601_PHARMACY_BILLS_READ_BY_CLAUDE.md v2, with R1 folded in):
  asset_register.py
  E1  _sarvam_on(): today's test AND _sarvam_setting() -- Sarvam reads nothing while the owner's setting is off
  E2  _s550_claude(): the pharmacy "beside" branch deleted (a second paid reading nothing used); the exclusions become the one test
      _s601_asked(bid); a pharmacy paper (a bill or a challan) is filled by Claude like the clinic lanes
  E3  _bg_extract(): the retry -- after _set_ocr_status(bid, "failed") exactly as today, _s601_retry(bid, path) (R1-B1: failed first,
      then the timer; R1-B2: only when Claude was asked and has no good reading of the paper)
  E4  _bg_extract(): the audit row `filled {by, items}` inside the open transaction, right after the header/items write (F-949's remedy)
  E5  bill_extract() (the checker's upload form): Claude first (bid=None -- nothing recorded in claude_reading, the call counted), then
      Sarvam exactly as today, else the manual flash
  E6  BILLFORM_TPL: the reader-neutral text
  E7  _bill_form_page(): sarvam_on=_reader_on() (as the bill page already does)
  E8  bill_reread(): the no-reader flash
  E9  admin(): the set_read_sarvam action beside set_read_claude (the ONLY writer of the setting)
  E10 admin page: the Claude card's words rewritten; the new Sarvam card (Now: ON / OFF / no key; the switch only when the key is on the
      server); the separate "Sarvam key configured" line retired into it (one fact, one place)
  E11 admin(): sarvam=_s601_sarvam_card() beside claude= (its own variable -- _s550_admin() is None without Claude); ocr_key= retired
  E12 the tail block S601: _S601_TRIES, _S601_DELAYS, _s601_asked, _sarvam_setting, _s601_retry, _s601_sarvam_card
  claude_reread.py
  E13 to_fill(): the pharmacy lane no longer excluded from filling (only other_doc)
  E14 the docstring's line: an approved paper's reading is kept aside (the pharmacy words dropped)
Every byte of the built files comes from the live files plus these edits (BUILD_NORM_v1)."""
import hashlib, os, sys

FROM = {"asset_register.py": "c39c084eabf52daa0da9cc6720fc7aa7", "claude_reread.py": "d9b75e784c4a806e941f3d1a243990e1"}

AR = []

# E1 -- _sarvam_on(): the owner's setting
AR.append(('''def _sarvam_on():
    return bool(SARVAM is not None and getattr(SARVAM, "available", lambda: False)())
''', '''def _sarvam_on():
    return bool(SARVAM is not None and getattr(SARVAM, "available", lambda: False)() and _sarvam_setting())   # S601 (D747): the owner's setting
''', 1))

# E2 -- _s550_claude(): the pharmacy branch deleted; the exclusions are _s601_asked()
AR.append(('''def _s550_claude(bid, path):
    """S550 (D723): Claude reads the scan. Returns (hdr, items) to fill, or None -- then Sarvam reads exactly as before.
    Not sent to Claude: the Other-document lane and the Personal and Resumes sections (a person's papers; Sarvam as before),
    and a patient's paper (S555: belt and braces -- it sits on Other document already).
    A pharmacy paper: Claude reads it BESIDE Sarvam (its own thread) and the reading is kept aside -- Sarvam fills it as
    before and never waits (the Sanjeevni side unchanged)."""
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
        if _lane == "other_doc" or (_r["subgroup"] or "") in ("personal", "resume", "patient_paper"):     # S555 item 8
            return None
        if _lane == "pharmacy":
            import threading
            threading.Thread(target=CLAUDE.read, args=(path,), kwargs={"bid": bid, "db_path": DB_PATH}, daemon=True).start()
            return None
        return CLAUDE.read_bill(path, bid=bid, db_path=DB_PATH)
    except Exception:
        return None
''', '''def _s550_claude(bid, path):
    """S550 (D723): Claude reads the scan. Returns (hdr, items) to fill, or None -- then Sarvam reads exactly as before.
    Not sent to Claude: the Other-document lane and the Personal and Resumes sections (a person's papers; Sarvam as before),
    and a patient's paper (S555: belt and braces -- it sits on Other document already) -- the one test, see _s601_asked below.
    S601 (D747): a pharmacy paper -- a bill or a challan -- is filled by Claude like the clinic lanes: the one reading fills
    the paper (header and items, only what is empty); Sarvam is the fall-back, and reads nothing while its setting is off."""
    if CLAUDE is None:
        return None
    try:
        if not CLAUDE.available(DB_PATH):
            return None
        if not _s601_asked(bid):                                                                         # S555 item 8; S601
            return None
        return CLAUDE.read_bill(path, bid=bid, db_path=DB_PATH)
    except Exception:
        return None
''', 1))

# E3 -- _bg_extract(): the retry, after `failed` is written exactly as today (R1-B1, R1-B2)
AR.append(('''        else:                                                # Sarvam, exactly as before
            if not _sarvam_on():
                _set_ocr_status(bid, "failed"); return "failed"
            data, st = SARVAM.extract(path, schema=ASSET_BILL_SCHEMA)
''', '''        else:                                                # Sarvam, exactly as before
            if not _sarvam_on():
                _set_ocr_status(bid, "failed")
                _s601_retry(bid, path)                       # S601 (D747 item 4): Claude could not read it -- the app tries again by itself
                return "failed"
            data, st = SARVAM.extract(path, schema=ASSET_BILL_SCHEMA)
''', 1))

# E4 -- _bg_extract(): the `filled` audit row (which reader filled this paper), inside the open transaction
AR.append(('''                         _norm_date(it.get("expiry")), it.get("hsn") or None))
            # terminal status reflects the RESULTING bill state, so a re-read of an
''', '''                         _norm_date(it.get("expiry")), it.get("hsn") or None))
            _audit_bill(db, bid, "filled", {"by": "claude" if _cr is not None else "sarvam", "items": len(items or [])})   # S601 (F-949)
            # terminal status reflects the RESULTING bill state, so a re-read of an
''', 1))

# E5 -- bill_extract(): Claude first, then Sarvam exactly as today, else the manual flash
AR.append(('''    hdr, items = {}, []
    if _sarvam_on():
        data, st = SARVAM.extract(os.path.join(UPLOAD_DIR, stored), schema=ASSET_BILL_SCHEMA)
        if st == "done" and data is not None:
            hdr, items = _map_bill(data)
            flash("Auto-filled from the scan — please review and correct before saving.")
        else:
            flash("Couldn't read the bill automatically — enter it manually. The scan is attached.")
    else:
        flash("Sarvam OCR isn't configured — enter the bill manually. The scan is attached.")
    return _bill_form_page(hdr, items, src)
''', '''    hdr, items = {}, []
    _r = None
    if _claude_on():                                         # S601 (D747): Claude first, as _bg_extract -- bid=None: nothing is recorded
        try:                                                 # in claude_reading, the call is counted (claude_reader.read)
            _r = CLAUDE.read_bill(os.path.join(UPLOAD_DIR, stored), bid=None, db_path=DB_PATH)
        except Exception:
            _r = None
    if _r is not None:
        hdr, items = _r
        flash("Auto-filled from the scan — please review and correct before saving.")
    elif _sarvam_on():                                       # Sarvam, exactly as before
        data, st = SARVAM.extract(os.path.join(UPLOAD_DIR, stored), schema=ASSET_BILL_SCHEMA)
        if st == "done" and data is not None:
            hdr, items = _map_bill(data)
            flash("Auto-filled from the scan — please review and correct before saving.")
        else:
            flash("Couldn't read the bill automatically — enter it manually. The scan is attached.")
    else:
        flash("No reader is on — enter the bill manually. The scan is attached.")       # S601
    return _bill_form_page(hdr, items, src)
''', 1))

# E6 -- BILLFORM_TPL: reader-neutral words
AR.append(('''<p class=muted>{% if sarvam_on %}Upload a bill image/PDF — Sarvam reads it and pre-fills the form below for you to check.{% else %}Sarvam OCR isn't configured yet, so this attaches the scan and you fill the form. (Set SARVAM_API_KEY + install sarvamai to enable auto-read.){% endif %}</p>
''', '''<p class=muted>{% if sarvam_on %}Upload a bill image/PDF — the scan is read and the form pre-filled for you to check.{% else %}No reader is on, so this attaches the scan and you fill the form.{% endif %}</p>
''', 1))

# E7 -- _bill_form_page(): a reader, Sarvam OR Claude
AR.append(('''                vendors=vendors, today=today().isoformat(), sarvam_on=_sarvam_on(), editing=editing)
''', '''                vendors=vendors, today=today().isoformat(), sarvam_on=_reader_on(), editing=editing)      # S601: Sarvam OR Claude
''', 1))

# E8 -- bill_reread(): the no-reader flash
AR.append(('''        flash("Sarvam OCR isn't configured, so the bill can't be auto-read — type it in.")
''', '''        flash("No reader is on — enter the bill manually. The scan is attached.")       # S601
''', 1))

# E9 -- admin(): set_read_sarvam -- the ONLY writer of the setting
AR.append(('''            flash("Claude reading the scans is now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
''', '''            flash("Claude reading the scans is now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
        elif act == "set_read_sarvam":                                                 # S601 (D747): the owner's word on Sarvam
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.sarvam',?)",
                       ("on" if request.form.get("on") == "1" else "off",))
            flash("Sarvam reading the scans is now %s." % ("ON" if request.form.get("on") == "1" else "OFF"))
''', 1))

# E10 -- the admin page: the Claude card's words; the Sarvam card
AR.append(('''<p class=muted>When ON, Claude reads every new scan first (handwriting and estimate slips too) and fills only what is empty; when it cannot, Sarvam reads as before. Pharmacy papers are read and kept aside; Sarvam still fills them. The key is kept on the server only. It stops by itself if the key is refused or the credit runs out, and Sarvam carries on.</p>
''', '''<p class=muted>When ON, Claude reads every new scan first — printed bills, handwriting, estimate slips and challans, the pharmacy's papers too — and fills only what is empty. A paper it cannot read is tried again three times over two hours; one still unread is counted here. The key is kept on the server only. It stops by itself if the key is refused or the credit runs out.</p>
''', 1))
AR.append(('''<button class="btn small">{{'Switch OFF' if claude.on else 'Switch ON'}}</button></form>{% endif %}</div>{% endif %}
<div class=card><h4>Locations</h4>
''', '''<button class="btn small">{{'Switch OFF' if claude.on else 'Switch ON'}}</button></form>{% endif %}</div>{% endif %}
{% if sarvam %}<div class=card id=sarvam-reads><h4>Reading the scans — Sarvam</h4>
<p class=muted>Kept as the fall-back reader, switched by you. When OFF, only Claude reads.</p>
<p>Now: <b>{{sarvam.words}}</b></p>
{% if sarvam.key %}<form method=post><input type=hidden name=action value=set_read_sarvam><input type=hidden name=on value="{{'0' if sarvam.on else '1'}}">
<button class="btn small">{{'Switch OFF' if sarvam.on else 'Switch ON'}}</button></form>{% endif %}</div>{% endif %}
<div class=card><h4>Locations</h4>
''', 1))
AR.append(('''<div class=card><h4>Document text (OCR)</h4>
<p>Sarvam key configured: <b>{{'yes' if ocr_key else 'no'}}</b></p>
<table><tr><th>Status</th><th>Documents</th></tr>
''', '''<div class=card><h4>Document text (OCR)</h4>
<table><tr><th>Status</th><th>Documents</th></tr>
''', 1))

# E11 -- admin(): the Sarvam card's own variable; ocr_key retired
AR.append(('''        claude=_s550_admin(),                                                                                 # S550 (D723)
        ocr_key=bool(SARVAM_API_KEY))
''', '''        claude=_s550_admin(),                                                                                 # S550 (D723)
        sarvam=_s601_sarvam_card())                                                                           # S601 (D747)
''', 1))

# E12 -- the tail block, before main
AR.append(('''# --- S571_BATTERIES end ---


# ---------------------------------------------------------------- main
''', '''# --- S571_BATTERIES end ---


# --- S601_PHARMACY_BILLS_READ_BY_CLAUDE begin -- D747 (19-Oct-2026): Claude fills the pharmacy bills; Sarvam behind the owner's setting ---
# The owner (15:41 IST 19-Oct): "Start Claude to read the pharmacy bills. Keep Sarvam switched off in settings so that the code is made
# once." Nothing of Sarvam's code is deleted: _sarvam_on() now also asks _sarvam_setting(); the admin page's Sarvam card switches it.
# The pharmacy "beside" read (a second paid reading nothing used) is retired: _s550_claude fills a pharmacy paper like the clinic lanes.
# A paper Claude could not read is tried again by the app itself, three times over two hours (_s601_retry); a paper read as empty, an
# excluded paper, a stopped reader: never. Which reader filled a paper: the `filled` audit row in _bg_extract (one fact, one place).
import threading

_S601_TRIES = {}                 # {bill id: retries timed} -- per gunicorn worker (-w 2); lost on a restart (the paper stays `failed`, counted
#                                  on the owner's card). Incremented only when a retry is timed, never on the first call or the re-read path.
_S601_DELAYS = (10, 30, 90)      # minutes: the three tries over two hours (D747 item 4)


def _s601_asked(bid):
    """S601 (D747): True when this paper is one Claude is asked to read -- every lane but Other document, and never a person's paper
    (the Personal and Resumes sections, a patient's paper: S555 item 8). The ONE test: _s550_claude and the retry both ask it."""
    try:
        _d = sqlite3.connect(DB_PATH); _d.row_factory = sqlite3.Row
        try:
            _r = _d.execute("SELECT lane, kind, subgroup FROM bills WHERE id=?", (bid,)).fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return False
    if not _r:
        return False
    _lane = _r["lane"] or KIND_LANE.get(_r["kind"], "clinic")
    return not (_lane == "other_doc" or (_r["subgroup"] or "") in ("personal", "resume", "patient_paper"))


def _sarvam_setting():
    """S601 (D747): the owner's word on Sarvam, from the settings row the admin page's set_read_sarvam writes: 'off' -> False; absent
    or 'on' -> True (today's behaviour); a database error -> True. Its own short connection (called from threads), the _set_ocr_status
    shape. The ONLY reader of that row."""
    try:
        _d = sqlite3.connect(DB_PATH)
        try:
            _r = _d.execute("SELECT value FROM settings WHERE key='read.sarvam'").fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return True
    return not (_r and (_r[0] or "").strip().lower() == "off")


def _s601_retry(bid, path):
    """S601 (D747 item 4; R1-B1, R1-B2): called by _bg_extract AFTER _set_ocr_status(bid, 'failed'). When Claude is on, the paper is one
    Claude is asked to read, and no good reading of it exists (a paper read as empty is not tried again), one more _bg_extract is timed
    for 10, then 30, then 90 minutes later -- three in all, never more; each is audited as read_retry {try, in_min} through its own short
    connection with a commit (no db is open at the call site). A reader stopped or off, an excluded paper, a fourth time: nothing.
    Returns True when a retry was timed. The retry's own result overwrites `failed` (ocr_status keeps its existing values)."""
    try:
        if not (_claude_on() and _s601_asked(bid)):
            return False
        n = _S601_TRIES.get(bid, 0)
        if n >= len(_S601_DELAYS):
            return False
        _d = sqlite3.connect(DB_PATH)
        try:
            if _d.execute("SELECT 1 FROM claude_reading WHERE bill_id=? AND ok=1", (bid,)).fetchone():
                return False
            _S601_TRIES[bid] = n + 1
            _audit_bill(_d, bid, "read_retry", {"try": n + 1, "in_min": _S601_DELAYS[n]})
            _d.commit()
        finally:
            _d.close()
        t = threading.Timer(_S601_DELAYS[n] * 60, _bg_extract, args=(bid, path))
        t.daemon = True
        t.start()
        return True
    except Exception:
        return False


def _s601_sarvam_card():
    """S601 (D747): the admin page's Sarvam card -- its own template variable (not inside _s550_admin, which is None without Claude).
    The one place that says whether the Sarvam key is on the server (the admin page's old separate key line is retired into it)."""
    _key = bool(SARVAM_API_KEY)
    _on = _sarvam_on()
    return {"on": _on, "key": _key, "words": ("ON" if _on else "OFF") if _key else "no key on the server"}
# --- S601 end ---


# ---------------------------------------------------------------- main
''', 1))

RR = []

# E13 -- to_fill(): the pharmacy lane is filled like the others
RR.append(('''    return (r is not None and r["status"] not in ("approved", "rejected") and r["lane"] not in ("pharmacy", "other_doc")
''', '''    return (r is not None and r["status"] not in ("approved", "rejected") and r["lane"] != "other_doc"          # S601 (D747)
''', 1))

# E14 -- the docstring
RR.append(('''- An approved paper and a pharmacy paper: the reading is kept aside and nothing on the paper is written.
''', '''- An approved paper: the reading is kept aside and nothing on the paper is written.
''', 1))


def md5(b):
    return hashlib.md5(b).hexdigest()


def apply(name, text, edits):
    n = 0
    for old, new, cnt in edits:
        k = text.count(old)
        if k != cnt:
            raise SystemExit("REFUSED: an anchor in %s was found %d times, not %d: %r" % (name, k, cnt, old[:70]))
        text = text.replace(old, new)
        n += 1
    return text, n


def build(src, out, f, edits):
    with open(os.path.join(src, f), "rb") as fh:
        raw = fh.read()
    if md5(raw) != FROM[f]:
        raise SystemExit("REFUSED: %s is %s, not the pinned FROM %s" % (f, md5(raw)[:8], FROM[f][:8]))
    text, n = apply(f, raw.decode("utf-8"), edits)
    b = text.encode("utf-8")
    with open(os.path.join(out, f), "wb") as fh:
        fh.write(b)
    print("%-18s %s -> %s  (%d anchored edits, each anchor exactly once)" % (f, FROM[f][:8], md5(b)[:8], n))
    return md5(b)


def main():
    a = [x for x in sys.argv[1:] if not x.startswith("--")]
    if len(a) != 2:
        raise SystemExit(__doc__)
    src, out = a
    os.makedirs(out, exist_ok=True)
    build(src, out, "asset_register.py", AR)
    build(src, out, "claude_reread.py", RR)


if __name__ == "__main__":
    main()
