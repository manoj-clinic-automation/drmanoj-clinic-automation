#!/usr/bin/env python3
"""
make_s698.py -- S698_CALLS_R1 (the parent, S379, 02-Nov-2026): the counted edits on three live files, from their
FROM bytes to their TO bytes. The installer re-runs this on the box's live files and refuses anything that does not
match the kit's TO pins byte for byte.

  /root/portal/portal.py              4ff31351 -> TO   3 edits: the old console moves to /portal/console/old; the digest's
                                                        "last build" filled (F-1084); the new module registered.
  /root/wa/portal_console.py          552135b5 -> TO   4 edits: the fold of the doubled rows (F-1083) in load_calls, its
                                                        stats in the meta, the selftest's checks.
  /root/wa/call-hook/call_hook_capture.py b8a1a293 -> TO  6 edits: v3.2 -- the real row from the append answer, the key
                                                        columns re-read on a miss, the cell verified before an update, the
                                                        ref_id as a second key, the selftest's fake sheet.

usage: make_s698.py <which> <from-file> <to-file>      which = portal | builder | hook
Every edit's anchor must occur EXACTLY ONCE in the input, or nothing is written (exit 2).
"""
import sys

EDITS = {}

# ----------------------------------------------------------------------------------------------------- portal.py
EDITS["portal"] = [
    # 1. the old page moves to /portal/console/old (the fallback); the new module takes /portal/console
    ('@app.route("/portal/console")\n@doctor_required\ndef console_page():\n',
     '@app.route("/portal/console/old")      # S698: the old page is the fallback; calls_console.py serves /portal/console\n'
     '@doctor_required\ndef console_page():\n'),
    # 2. F-1084: the digest's "last build" was empty -- the template reads m.built, the meta carries built_at
    ('    m = _console_meta()\n    d = {"day": day, "oneline": "", "calls": {}, "buckets": {}, "flagged": 0,\n',
     '    m = _console_meta()\n    m["built"] = m.get("built_at") or "unknown"          # S698 (F-1084): the template reads m.built\n'
     '    d = {"day": day, "oneline": "", "calls": {}, "buckets": {}, "flagged": 0,\n'),
    # 3. the new page registered (S698); a failure to load costs this one page, never the portal
    ('def _rotate_seed_in_config(new_seed: str) -> bool:\n',
     '# S698_CALLS_R1 (the parent, S379, 02-Nov-2026): the Call Console in the month page\'s look -- its own module beside this\n'
     '# file (calls_console.py), behind the doctor gate, reading console.db through this file\'s own readers. The old page stays\n'
     '# at /portal/console/old. A failure to load costs this one page, never the portal.\n'
     'try:\n'
     '    import calls_console\n'
     '    calls_console.register(\n'
     '        app, doctor_required,\n'
     '        lambda: ((_sso_user(request) or {}).get("user") or "manoj"),\n'
     '        _cfg_get,\n'
     '        {"console_conn": _console_conn, "console_meta": _console_meta, "reviews_maps": _reviews_maps,\n'
     '         "spam_phones": _spam_phones})\n'
     '    CALLS_IMPORT_ERR = ""\n'
     'except Exception as _cc_e:\n'
     '    CALLS_IMPORT_ERR = str(_cc_e)\n'
     '\n'
     '    @app.route("/portal/console")\n'
     '    @login_required\n'
     '    def _calls_broken():\n'
     '        return make_response("The Call Console failed to load: " + CALLS_IMPORT_ERR +\n'
     '                             " -- the older page is at /portal/console/old", 500)\n'
     '\n'
     '\n'
     'def _rotate_seed_in_config(new_seed: str) -> bool:\n'),
]

# ----------------------------------------------------------------------------------------------- portal_console.py
EDITS["builder"] = [
    # 1. the fold (pure helpers) before load_calls
    ('def load_calls(conn, rows, rec_index):\n    kept = skipped_probe = unknown_status = matched_jk = 0\n    for d in rows:\n',
     '# --- S698 (F-1083): the doubled rows ---------------------------------------------------------------------\n'
     '# Since 29-Oct midday the Call_Durations tab held two rows for one call (the receiver\'s row arithmetic drifted\n'
     '# after a gap in the tab, so every later call.summary landed on another call\'s row). The receiver is mended\n'
     '# (v3.2); this fold protects every reader of console.db whatever the tab holds: rows that describe ONE call\n'
     '# collapse to one, the fuller row winning, blanks filled from the other.\n'
     'def fold_keys(d):\n'
     '    """The keys that say \'the same call\': MyOperator\'s own uuid (ref_id), the recording file, the session id, and\n'
     '    the exact end-second of the same number in the same direction. Two webhook events of one call share at\n'
     '    least one; two different calls share none (two calls cannot end in the same second)."""\n'
     '    keys = []\n'
     '    for name, val in (("ref", d.get("ref_id")), ("rec", d.get("recording_filename")), ("ses", d.get("session_id"))):\n'
     '        v = (val or "").strip()\n'
     '        if v:\n'
     '            keys.append((name, v))\n'
     '    ph = norm_phone10(d.get("phone10", "")) or (d.get("client_ref_id") or "").strip()\n'
     '    end = (d.get("ended_at_ist") or "").strip()\n'
     '    if ph and end:\n'
     '        keys.append(("end", "%s|%s|%s" % (ph, (d.get("category") or "").strip().lower(), end)))\n'
     '    return keys\n'
     '\n'
     '\n'
     'def fold_score(d):\n'
     '    """The fuller of two rows of one call: the summary event, then a recording, then the longer duration."""\n'
     '    se = (d.get("source_event") or "").lower()\n'
     '    try:\n'
     '        dur = int(float(d.get("total_duration") or 0))\n'
     '    except (ValueError, TypeError):\n'
     '        dur = 0\n'
     '    return (1 if "summary" in se else 0, 1 if (d.get("recording_filename") or "").strip() else 0, dur,\n'
     '            1 if (d.get("status") or "").strip() else 0)\n'
     '\n'
     '\n'
     'def _blank(v):\n'
     '    return v is None or (isinstance(v, str) and not v.strip())\n'
     '\n'
     '\n'
     'def fold_calls(rows):\n'
     '    """Collapse the rows that describe one call. Returns (rows, stats). Pure; selftested."""\n'
     '    kept, owner = [], {}\n'
     '    stats = {"rows_in": len(rows), "folded": 0, "by": {"ref": 0, "rec": 0, "ses": 0, "end": 0},\n'
     '             "same_key_pairs": 0, "diff_key_pairs": 0}\n'
     '    for d in rows:\n'
     '        keys = fold_keys(d)\n'
     '        hit = how = None\n'
     '        for k in keys:\n'
     '            if k in owner:\n'
     '                hit, how = owner[k], k[0]\n'
     '                break\n'
     '        if hit is None:\n'
     '            idx = len(kept)\n'
     '            kept.append(dict(d))\n'
     '            for k in keys:\n'
     '                owner.setdefault(k, idx)\n'
     '            continue\n'
     '        base = kept[hit]\n'
     '        stats["folded"] += 1\n'
     '        stats["by"][how] += 1\n'
     '        if (base.get("client_ref_id") or "").strip() == (d.get("client_ref_id") or "").strip():\n'
     '            stats["same_key_pairs"] += 1\n'
     '        else:\n'
     '            stats["diff_key_pairs"] += 1\n'
     '        win, other = (d, base) if fold_score(d) > fold_score(base) else (base, d)\n'
     '        merged = dict(win)\n'
     '        for f, v in other.items():\n'
     '            if _blank(merged.get(f)) and not _blank(v):\n'
     '                merged[f] = v\n'
     '        kept[hit] = merged\n'
     '        for k in fold_keys(merged):\n'
     '            owner.setdefault(k, hit)\n'
     '    stats["rows_out"] = len(kept)\n'
     '    return kept, stats\n'
     '\n'
     '\n'
     'def load_calls(conn, rows, rec_index):\n'
     '    rows, fold = fold_calls(rows)                        # S698 (F-1083): one call, one row\n'
     '    kept = skipped_probe = unknown_status = matched_jk = 0\n'
     '    for d in rows:\n'),
    # 2. the fold's stats ride with the call stats into meta.row_counts
    ('    return {"kept": kept, "skipped_probe": skipped_probe,\n            "unknown_status": unknown_status, "matched_jk": matched_jk}\n',
     '    return {"kept": kept, "skipped_probe": skipped_probe,\n            "unknown_status": unknown_status, "matched_jk": matched_jk,\n'
     '            "fold": fold}                                   # S698: how many doubled rows were folded, by which key\n'),
    # 3. the builder's name
    ('    setk("builder", "portal_console.py A1 (D297 Stage A, rev5-i3)")\n',
     '    setk("builder", "portal_console.py A1 (D297 Stage A, rev5-i3; S698 fold)")\n'),
    # 4. the selftest: the fold on made-up rows
    ('    check("header discovery ignored junk column",\n          "junk" not in headers["Call_Durations"]["resolved"])\n',
     '    check("header discovery ignored junk column",\n          "junk" not in headers["Call_Durations"]["resolved"])\n'
     '    # --- S698 (F-1083): the fold of the doubled rows, pure ---\n'
     '    E = k["D0"] + "T10:00:00+05:30"\n'
     '    f_rows = [\n'
     '        # the drift pair: the same IN- key twice (call.end row left, call.summary written on another row)\n'
     '        {"client_ref_id": "IN-1.1", "ref_id": "u1", "session_id": "1.1", "category": "incoming", "status": "bridged",\n'
     '         "total_duration": "40", "recording_filename": "", "ended_at_ist": E, "source_event": "call.end", "phone10": "5000000031"},\n'
     '        {"client_ref_id": "IN-1.1", "ref_id": "u1", "session_id": "1.1", "category": "incoming", "status": "bridged",\n'
     '         "total_duration": "42", "recording_filename": "R9", "ended_at_ist": E, "source_event": "call.summary", "phone10": "5000000031"},\n'
     '        # a pair whose session ids differ but MyOperator\'s uuid agrees\n'
     '        {"client_ref_id": "IN-2.1", "ref_id": "u2", "session_id": "2.1", "category": "incoming", "status": "missed",\n'
     '         "total_duration": "0", "recording_filename": "", "ended_at_ist": k["D0"] + "T11:00:00+05:30", "source_event": "call.end", "phone10": "5000000032"},\n'
     '        {"client_ref_id": "IN-2.2", "ref_id": "u2", "session_id": "2.2", "category": "incoming", "status": "missed",\n'
     '         "total_duration": "0", "recording_filename": "", "ended_at_ist": k["D0"] + "T11:00:00+05:30", "source_event": "call.summary", "phone10": "5000000032"},\n'
     '        # two DIFFERENT calls of one number in one minute (31 s apart): never folded\n'
     '        {"client_ref_id": "IN-3.1", "ref_id": "u3", "session_id": "3.1", "category": "incoming", "status": "missed",\n'
     '         "total_duration": "0", "recording_filename": "", "ended_at_ist": k["D0"] + "T12:00:05+05:30", "source_event": "call.summary", "phone10": "5000000033"},\n'
     '        {"client_ref_id": "IN-3.2", "ref_id": "u4", "session_id": "3.2", "category": "incoming", "status": "missed",\n'
     '         "total_duration": "0", "recording_filename": "", "ended_at_ist": k["D0"] + "T12:00:36+05:30", "source_event": "call.summary", "phone10": "5000000033"},\n'
     '        # an OBD pair, keyed on our own reference, no phone10\n'
     '        {"client_ref_id": "5000000034-17000000aa", "ref_id": "u5", "session_id": "5.1", "category": "obd", "status": "bridged",\n'
     '         "total_duration": "30", "recording_filename": "", "ended_at_ist": k["D0"] + "T13:00:00+05:30", "source_event": "call.end", "phone10": ""},\n'
     '        {"client_ref_id": "5000000034-17000000aa", "ref_id": "", "session_id": "", "category": "obd", "status": "bridged",\n'
     '         "total_duration": "30", "recording_filename": "R10", "ended_at_ist": k["D0"] + "T13:00:00+05:30", "source_event": "call.summary", "phone10": ""},\n'
     '    ]\n'
     '    f_out, f_st = fold_calls(f_rows)\n'
     '    check("S698 fold: 8 rows -> 5 calls (three pairs folded, the two 31-s-apart calls kept)",\n'
     '          f_st["rows_out"] == 5 and f_st["folded"] == 3 and len(f_out) == 5)\n'
     '    check("S698 fold: the summary row wins and keeps the recording; blanks filled from the other",\n'
     '          next(r for r in f_out if r["client_ref_id"] == "IN-1.1")["recording_filename"] == "R9"\n'
     '          and next(r for r in f_out if r["client_ref_id"] == "IN-1.1")["total_duration"] == "42"\n'
     '          and next(r for r in f_out if r["client_ref_id"].startswith("5000000034"))["recording_filename"] == "R10"\n'
     '          and next(r for r in f_out if r["client_ref_id"].startswith("5000000034"))["ref_id"] == "u5")\n'
     '    check("S698 fold: the drift pair is a same-key pair, the uuid pair a different-key pair (the trace\'s two causes)",\n'
     '          f_st["same_key_pairs"] == 2 and f_st["diff_key_pairs"] == 1 and f_st["by"]["ref"] >= 1)\n'
     '    check("S698 fold: two calls 31 s apart of one number stay two",\n'
     '          sum(1 for r in f_out if r["phone10"] == "5000000033") == 2)\n'
     '    check("S698 fold: the real fixtures are untouched by the fold (11 kept of 12)", counts["calls"] == 11\n'
     '          and counts["_call_stats"]["fold"]["folded"] == 0)\n'),
]

# ------------------------------------------------------------------------------------------ call_hook_capture.py
EDITS["hook"] = [
    # 1. the version note
    ('v3.1   --  Session 140  --  PIPELINE KICK (D200 at-hangup chain)\n',
     'v3.2   --  Session 379 (S698, 02-Nov-2026)  --  THE ROW THAT IS REALLY WRITTEN (F-1083)\n'
     '\n'
     '  Changed from v3.1 in exactly ONE function (upsert) and its helpers; the gate, the raw log, the\n'
     '  extraction, the kick and the OBD/incoming paths are byte-identical.\n'
     '    . After append_row, the row number comes from the API\'s own answer (updates.updatedRange),\n'
     '      never from len(index)+2. Since 29-Oct the tab held a gap, so that arithmetic pointed one row\n'
     '      above the real one: every call.summary overwrote the PREVIOUS call\'s row, leaving the new call\n'
     '      twice and the older call gone. Two rows per call on the console; day counts doubled.\n'
     '    . A key not in the index re-reads the two key columns once before appending (a restart, a sort,\n'
     '      a second writer).\n'
     '    . Before an UPDATE the row\'s key cells are read: the row must still hold this call (or its\n'
     '      MyOperator uuid); otherwise the index is rebuilt and, failing that, the record is appended.\n'
     '    . ref_id (MyOperator\'s own uuid, column B) is a second key: the two events of one call share it\n'
     '      even if a session id ever differs between them.\n'
     '  Cost: a new call costs two column reads on its call.end (the index miss) and one small read on its\n'
     '  call.summary (~40 calls a day; well inside the Sheets quota). Repair of the rows already doubled: the companion\n'
     '  repair_call_durations_s698.py (from the raw log, the truth), run once by the S698 installer.\n'
     '\n'
     'v3.1   --  Session 140  --  PIPELINE KICK (D200 at-hangup chain)\n'),
    # 2. the store carries the second index
    ('_store = {"ws": None, "index": {}}     # index: client_ref_id -> row number\n',
     '_store = {"ws": None, "index": {}, "refs": {}}     # index: client_ref_id -> row number; refs: ref_id -> row number (v3.2)\n'
     '_RANGE_ROW = re.compile(r"![A-Z]+(\\d+)(?::[A-Z]+\\d+)?$")       # \'Call_Durations\'!A123:N123 -> 123\n'),
    # 3. the index preload reads both key columns
    ('    # build the client_ref_id -> row-number index (col A, skip header)\n'
     '    index = {}\n'
     '    try:\n'
     '        col = ws.col_values(1)[1:]\n'
     '        for i, v in enumerate(col, start=2):\n'
     '            if v:\n'
     '                index[v] = i\n'
     '    except Exception as e:              # noqa: BLE001\n'
     '        log("index preload failed:", e)\n'
     '    _store.update({"ws": ws, "index": index})\n'
     '    log("connected to \'%s\' (key=%s) - %d rows known" % (TAB, os.path.basename(key), len(index)))\n'
     '    return ws\n',
     '    # build the key indexes (col A = client_ref_id, col B = ref_id; the header skipped) -- v3.2\n'
     '    _store["ws"] = ws\n'
     '    try:\n'
     '        n = _reload_index(ws)\n'
     '    except Exception as e:              # noqa: BLE001\n'
     '        n = 0\n'
     '        _store.update({"index": {}, "refs": {}})\n'
     '        log("index preload failed:", e)\n'
     '    log("connected to \'%s\' (key=%s) - %d rows known" % (TAB, os.path.basename(key), n))\n'
     '    return ws\n'),
    # 4. upsert v3.2
    ('def upsert(rec):\n'
     '    """Insert or update one Call_Durations row keyed on client_ref_id."""\n'
     '    key = rec["client_ref_id"]\n'
     '    row = record_to_row(rec)\n'
     '    ws = store_handle()\n'
     '    r = _store["index"].get(key)\n'
     '    if r:\n'
     '        ws.batch_update([{"range": "A%d" % r, "values": [row]}], value_input_option="RAW")\n'
     '        return "updated", r\n'
     '    ws.append_row(row, value_input_option="RAW")\n'
     '    r = len(_store["index"]) + 2        # header + existing + this\n'
     '    _store["index"][key] = r\n'
     '    return "inserted", r\n',
     'def _index_from_cols(col_a, col_b):\n'
     '    """client_ref_id -> row, ref_id -> row. The header is skipped; a blank cell is no key; a key seen twice keeps\n'
     '    its LAST row (the one the receiver wrote last). Pure; selftested."""\n'
     '    index, refs = {}, {}\n'
     '    for i, v in enumerate(col_a[1:], start=2):\n'
     '        if v:\n'
     '            index[str(v).strip()] = i\n'
     '    for i, v in enumerate(col_b[1:], start=2):\n'
     '        if v:\n'
     '            refs[str(v).strip()] = i\n'
     '    return index, refs\n'
     '\n'
     '\n'
     'def _reload_index(ws):\n'
     '    index, refs = _index_from_cols(ws.col_values(1), ws.col_values(2))\n'
     '    _store.update({"index": index, "refs": refs})\n'
     '    return len(index)\n'
     '\n'
     '\n'
     'def _row_from_append(resp):\n'
     '    """The row the API really wrote: updates.updatedRange -> its row number; 0 when the answer has no range."""\n'
     '    try:\n'
     '        rng = str(((resp or {}).get("updates") or {}).get("updatedRange") or "")\n'
     '        m = _RANGE_ROW.search(rng)\n'
     '        return int(m.group(1)) if m else 0\n'
     '    except Exception:                   # noqa: BLE001\n'
     '        return 0\n'
     '\n'
     '\n'
     'def _find_row(key, ref):\n'
     '    r = _store["index"].get(key)\n'
     '    if r is None and ref:\n'
     '        r = _store["refs"].get(ref)\n'
     '    return r\n'
     '\n'
     '\n'
     'def _row_holds(ws, r, key, ref):\n'
     '    """True when row r still carries this call (its key in column A, or its uuid in column B). One small read; a read\n'
     '    error RAISES (the caller\'s reconnect retry handles it) -- a transient 429/5xx must never read as a mismatch."""\n'
     '    cells = ws.get("A%d:B%d" % (r, r)) or [[]]\n'
     '    a = str((list(cells[0]) + ["", ""])[0] or "").strip()\n'
     '    b = str((list(cells[0]) + ["", ""])[1] or "").strip()\n'
     '    return a == key or (bool(ref) and b == ref)\n'
     '\n'
     '\n'
     'def upsert(rec):\n'
     '    """Insert or update one Call_Durations row keyed on client_ref_id (v3.2: the row is verified before an\n'
     '    update, the key columns re-read on a miss, the appended row\'s number taken from the API\'s answer)."""\n'
     '    key = str(rec["client_ref_id"]).strip()\n'
     '    ref = str(rec.get("ref_id") or "").strip()\n'
     '    row = record_to_row(rec)\n'
     '    ws = store_handle()\n'
     '    r = _find_row(key, ref)\n'
     '    if r is None:\n'
     '        _reload_index(ws)\n'
     '        r = _find_row(key, ref)\n'
     '    if r is not None and not _row_holds(ws, r, key, ref):\n'
     '        _reload_index(ws)\n'
     '        r = _find_row(key, ref)\n'
     '        if r is not None and not _row_holds(ws, r, key, ref):\n'
     '            log("row %d no longer holds the call (key %s...%s) - appending instead of overwriting" % (r, key[:3], key[-4:]))\n'
     '            r = None\n'
     '    if r is not None:\n'
     '        ws.batch_update([{"range": "A%d" % r, "values": [row]}], value_input_option="RAW")\n'
     '        _store["index"][key] = r\n'
     '        if ref:\n'
     '            _store["refs"][ref] = r\n'
     '        return "updated", r\n'
     '    resp = ws.append_row(row, value_input_option="RAW")\n'
     '    r = _row_from_append(resp) or (len(_store["index"]) + 2)\n'
     '    _store["index"][key] = r\n'
     '    if ref:\n'
     '        _store["refs"][ref] = r\n'
     '    return "inserted", r\n'),
    # 5. the startup line names v3.2
    ('    log("Phase B receiver v3 (dual-key + incoming capture). raw logs: %s" % RAW_DIR)\n',
     '    log("Phase B receiver v3.2 (dual-key + incoming capture; the verified row, S698). raw logs: %s" % RAW_DIR)\n'),
    # 6. the selftest: upsert against a fake sheet (offline)
    ('    print("selftest: %d/%d passed" % (passed, passed + failed))\n    return 0 if failed == 0 else 1\n',
     '    # -- v3.2 (S698, F-1083): the upsert against a fake sheet ---------------------------------\n'
     '    class _FakeWS:\n'
     '        """A sheet as a list of rows (row 1 = the header). append_row answers like the API; a gap row is possible."""\n'
     '        def __init__(self, rows):\n'
     '            self.rows = rows\n'
     '            self.updated = []\n'
     '        def col_values(self, c):\n'
     '            out = [(r[c - 1] if len(r) >= c else "") for r in self.rows]\n'
     '            while out and out[-1] == "":\n'
     '                out.pop()\n'
     '            return out\n'
     '        def get(self, rng):\n'
     '            r = int(re.sub(r"\\D", "", rng.split(":")[0]))\n'
     '            return [self.rows[r - 1][:2]] if r <= len(self.rows) else [[]]\n'
     '        def batch_update(self, body, value_input_option=None):\n'
     '            r = int(body[0]["range"][1:])\n'
     '            while len(self.rows) < r:\n'
     '                self.rows.append([""] * len(HEADER))\n'
     '            self.rows[r - 1] = list(body[0]["values"][0])\n'
     '            self.updated.append(r)\n'
     '        def append_row(self, row, value_input_option=None):\n'
     '            self.rows.append(list(row))\n'
     '            n = len(self.rows)\n'
     '            return {"updates": {"updatedRange": "\'%s\'!A%d:N%d" % (TAB, n, n)}}\n'
     '    def _rec(key, ref, ses, ev):\n'
     '        return {"client_ref_id": key, "ref_id": ref, "session_id": ses, "category": "incoming", "status": "bridged",\n'
     '                "total_duration": 5, "customer_result": "", "customer_talk_duration": 5, "customer_ring_duration": 3,\n'
     '                "recording_filename": "", "ended_at_ist": "", "captured_at_ist": "", "source_event": ev, "phone10": "5000000001"}\n'
     '    _ws_save = dict(_store)\n'
     '    try:\n'
     '        # the tab: header, two calls, a GAP row, a third call -> len(index)+2 would say 5 while the real next row is 6\n'
     '        rows = [list(HEADER), record_to_row(_rec("IN-a", "ua", "a", "call.summary")),\n'
     '                record_to_row(_rec("IN-b", "ub", "b", "call.summary")), [""] * len(HEADER),\n'
     '                record_to_row(_rec("IN-c", "uc", "c", "call.end"))]\n'
     '        fws = _FakeWS(rows)\n'
     '        _store.update({"ws": fws, "index": {}, "refs": {}})\n'
     '        _reload_index(fws)\n'
     '        check("v3.2 index: three keys known, the gap row no key", len(_store["index"]) == 3 and _store["index"]["IN-c"] == 5)\n'
     '        check("v3.2 refs: the uuid column indexed", _store["refs"].get("uc") == 5)\n'
     '        a1, r1 = upsert(_rec("IN-d", "ud", "d", "call.end"))\n'
     '        check("v3.2 append: the REAL row from the API answer (6), not len+2 (5)", a1 == "inserted" and r1 == 6 and _store["index"]["IN-d"] == 6)\n'
     '        a2, r2 = upsert(_rec("IN-d", "ud", "d", "call.summary"))\n'
     '        check("v3.2 the pair collapses: the summary updates row 6, no new row", a2 == "updated" and r2 == 6 and len(fws.rows) == 6)\n'
     '        # the drift: the index says IN-c sits at row 4 (it is at 5): the cell check must refuse the overwrite\n'
     '        _store["index"]["IN-c"] = 4\n'
     '        a3, r3 = upsert(_rec("IN-c", "uc", "c", "call.summary"))\n'
     '        check("v3.2 drift refused: the verified row (5) is written, row 4 untouched", a3 == "updated" and r3 == 5 and fws.rows[3][0] == "")\n'
     '        # a session id that differs between the two events: the uuid still finds the row\n'
     '        a4, r4 = upsert(_rec("IN-e1", "ue", "e1", "call.end"))\n'
     '        a5, r5 = upsert(_rec("IN-e2", "ue", "e2", "call.summary"))\n'
     '        check("v3.2 second key: a changed session id still lands on the same row", a4 == "inserted" and a5 == "updated" and r4 == r5)\n'
     '        # a row that no longer holds the call (sorted away) and cannot be found: appended, never overwritten\n'
     '        fws.rows[r5 - 1] = record_to_row(_rec("IN-zz", "uzz", "zz", "call.summary"))\n'
     '        a6, r6 = upsert(_rec("IN-e2", "ue", "e2", "call.summary"))\n'
     '        check("v3.2 a vanished row is appended, never overwritten", a6 == "inserted" and r6 == len(fws.rows) and fws.rows[r5 - 1][0] == "IN-zz")\n'
     '        check("v3.2 the row-number parser", _row_from_append({"updates": {"updatedRange": "\'Call_Durations\'!A1234:N1234"}}) == 1234\n'
     '              and _row_from_append({"updates": {"updatedRange": "Sheet1!A7"}}) == 7 and _row_from_append({}) == 0)\n'
     '    finally:\n'
     '        _store.clear(); _store.update(_ws_save)\n'
     '\n'
     '    print("selftest: %d/%d passed" % (passed, passed + failed))\n    return 0 if failed == 0 else 1\n'),
]


def apply(which, src, dst):
    text = open(src, "r", encoding="utf-8", newline="").read()
    for i, (old, new) in enumerate(EDITS[which], 1):
        n = text.count(old)
        if n != 1:
            sys.stderr.write("edit %d of %s: anchor found %d times (must be 1); nothing written\n" % (i, which, n))
            return 2
        text = text.replace(old, new, 1)
    with open(dst, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in EDITS:
        sys.stderr.write(__doc__)
        sys.exit(2)
    sys.exit(apply(sys.argv[1], sys.argv[2], sys.argv[3]))
