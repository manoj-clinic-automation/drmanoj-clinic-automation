# -*- coding: utf-8 -*-
"""edits_s731.py -- S731_CHALLAN_READ (F-1136, the Scan App chat, session 392, 06-Nov-2026): the counted edits, file by file.

The cause (read on the box, 16:5x IST 06-Nov): B-0250, a Variety Stationers challan, was scanned on 05-Nov 15:10 IST with the Challan
button on the Other-document lane ("bill nahi"); that lane is never put to Claude (_s601_asked), Sarvam is off, so it was marked
'read failed' with no reading and no retry. The desk moved it to the clinic lane at 08:51 06-Nov but did not read it; it was read only
when 'Read it again' (S715) was pressed at 11:11.

The fix:
  (a) a CHALLAN is put to Claude on any lane -- goods received are never a person's paper; the Personal and Resumes sections and a
      patient's paper stay unread, and any other paper on Other document stays unread as before;
  (b) after the desk's Save or the lane button, a paper Claude is asked to read that holds a scan, is marked 'failed' and was NEVER put
      to Claude (no claude_reading row at all -- B-0250's case, and B-0234's) is read then, once, in the background through the app's own
      filling step (only what is empty). A paper Claude already tried -- read, or failed (a photo too large) -- is never re-read by it.
"""

AR_ANCHOR = "# ---------------------------------------------------------------- main\n"

AR_BLOCK = '''# --- S731_CHALLAN_READ begin -- F-1136 (06-Nov-2026): a challan is read on any lane; a paper moved into a read lane is read then ---
# B-0250 (a challan scanned with the Challan button on Other document) was never put to Claude: that lane is not read, Sarvam is off.
# Guarded: every function here never raises; if this block failed to load, the app behaves exactly as before.
CHALLAN_READ_S731 = "S731"
_s601_asked_before_s731 = _s601_asked


def _s601_asked(bid):                                                                   # noqa: F811 -- S731
    """S601's one test, widened by S731 (F-1136): also a CHALLAN on the Other-document lane (reception's 'bill nahi' button takes
    challans too) -- goods received are never a person's paper. The Personal and Resumes sections and a patient's paper stay unread;
    every other paper on Other document stays unread as before. _s550_claude, _s601_retry and _s618_lie read this name when called."""
    if _s601_asked_before_s731(bid):
        return True
    try:
        _d = sqlite3.connect(DB_PATH); _d.row_factory = sqlite3.Row
        try:
            _r = _d.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        finally:
            _d.close()
    except sqlite3.Error:
        return False
    if not _r or "doc_kind" not in _r.keys():
        return False
    _lane = _r["lane"] or KIND_LANE.get(_r["kind"], "clinic")
    return (_lane == "other_doc" and (_r["doc_kind"] or "") == "challan"
            and (_r["subgroup"] or "") not in ("personal", "resume", "patient_paper"))


def _s731_read_if_never_asked(bid):
    """S731 (F-1136): called AFTER the desk's Save or the lane button has committed. A paper Claude is asked to read (now), with its scan
    on disk, marked 'failed', that was NEVER put to Claude (no claude_reading row, good or failed): read now, once, in the background,
    through the app's own _bg_extract (only what is empty, then the after-checks) -- as a new scan. Audited 'read_after_move'. A paper
    Claude already tried is never re-read here (its row exists). Returns True when the read was started. Never raises."""
    try:
        if not _claude_on() or not _s601_asked(bid):
            return False
        _d = sqlite3.connect(DB_PATH); _d.row_factory = sqlite3.Row
        try:
            _b = _d.execute("SELECT source_stored, ocr_status FROM bills WHERE id=?", (bid,)).fetchone()
            if not _b or not _b["source_stored"] or (_b["ocr_status"] or "") != "failed":
                return False
            if _d.execute("SELECT 1 FROM claude_reading WHERE bill_id=?", (bid,)).fetchone():
                return False
            _path = os.path.join(UPLOAD_DIR, _b["source_stored"])
            if not os.path.exists(_path):
                return False
            _d.execute("UPDATE bills SET ocr_status='reading' WHERE id=?", (bid,))
            _audit_bill(_d, bid, "read_after_move", {"by": "S731"})
            _d.commit()
        finally:
            _d.close()
        import threading as _s731_th
        _s731_th.Thread(target=_bg_extract, args=(bid, _path), daemon=True).start()
        return True
    except Exception:                                                                   # noqa: BLE001
        return False


def _s731_wrap_lane():
    """The lane button (/bills/<id>/lane, bill_lane): after its own commit, a paper never put to Claude is read (above)."""
    _v = app.view_functions.get("bill_lane")
    if _v is None or getattr(_v, "_s731", False):
        return

    @functools.wraps(_v)
    def _s731_bill_lane(bid, *a, **kw):
        _rv = _v(bid, *a, **kw)
        _s731_read_if_never_asked(bid)
        return _rv
    _s731_bill_lane._s731 = True
    app.view_functions["bill_lane"] = _s731_bill_lane


try:
    _s731_wrap_lane()
except Exception as _ex_s731:                                                           # noqa: BLE001
    print("S731 lane button NOT wrapped: %s" % _ex_s731, file=_sys.stderr)
# --- S731_CHALLAN_READ end ---


'''

SD_MARK_OLD = 'ITEMS = "S715"                # S715_DESK_ITEM_LINES: the supplier list, the calendar, the stationery lines, Read it again\n'
SD_MARK_NEW = SD_MARK_OLD + 'CHALLAN_READ = "S731"         # S731_CHALLAN_READ (F-1136): a paper never put to Claude is read after its Save\n'

SD_NEXT_OLD = '''    nxt = [x["id"] for x in list_json(db, _owner())["papers"] if x["id"] != bid]
'''
SD_NEXT_NEW = '''    try:                                                             # S731 (F-1136): a paper never put to Claude is read now
        AR._s731_read_if_never_asked(bid)
    except Exception:                                                # noqa: BLE001
        pass
    nxt = [x["id"] for x in list_json(db, _owner())["papers"] if x["id"] != bid]
'''

# file -> [(name, old, new)], each old must occur exactly once in the FROM bytes
EDITS = {
    "asset_register.py": [("AR1 the S731 block before main", AR_ANCHOR, AR_BLOCK + AR_ANCHOR)],
    "sorting_desk.py": [("SD1 the S731 mark", SD_MARK_OLD, SD_MARK_NEW),
                        ("SD2 read after the Save's commit", SD_NEXT_OLD, SD_NEXT_NEW)],
}
FROM = {"asset_register.py": "63a8b15b", "sorting_desk.py": "4990350b"}     # short; make_s731.py holds the full pins
