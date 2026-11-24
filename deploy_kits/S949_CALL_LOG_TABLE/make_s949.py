#!/usr/bin/env python3
"""make_s949.py -- S949 (S516): call_hook_capture.py 70c3d257 -> TO by exact anchors (each must occur exactly once).
usage: python make_s949.py FROM.py TO.py"""
import sys, hashlib

FROM_MD5 = "70c3d257cf9b576bda54acbdf83b99ee"
EDITS = []

EDITS.append(("""PHASE B (the "duration gate", D77): passive capture PLUS a PHI-clean Call_Durations feed.
""", """PHASE B (the "duration gate", D77): passive capture PLUS a PHI-clean Call_Durations feed.

v3.4   --  Session 516 (S949, 24-Nov-2026)  --  THE CALL LOG ON THE SERVER, FIRST (roadmap S510 F1a)

  Every record that goes to the Call_Durations Sheet is written FIRST to the server table call_log_raw
  (/root/wa/calls.db, through the sibling call_log_db.py; this script is its one writer), then to the Sheet
  exactly as before. The table write is best-effort in its own try: a failure is logged in one line and the
  Sheet write, the raw log, the kick and the reply are untouched; the reply carries db=inserted|updated|
  deferred|off beside sheet=. CALLHOOK_DB=off (or 0/no/false) in /root/wa/.env turns the table off, no code change.
  The nightly call_log_compare.py (23:40) proves table = Sheet; the console builder and the probe move to the
  table only after that (F1b). Gate, raw log, extraction, kick, Sheet upsert: byte-identical to v3.3.
"""))

EDITS.append(("""IST         = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
""", """IST         = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# v3.4 (S949, F1a): the call log table, written before the Sheet. A missing or broken module leaves the hook as v3.3.
_cldb = None
_CLDB_STATE = "off"
if os.environ.get("CALLHOOK_DB", "").strip().lower() not in ("off", "0", "no", "false", "none", "disabled"):
    try:
        if _HERE not in sys.path:
            sys.path.insert(0, _HERE)
        import call_log_db as _cldb
        _CLDB_STATE = "on"
    except Exception as _e:            # noqa: BLE001
        _cldb = None
        _CLDB_STATE = "import failed (%s)" % type(_e).__name__
_db_lock = threading.Lock()
"""))

EDITS.append(("""def record_to_row(rec):
    return [rec.get(h, "") for h in HEADER]
""", """def record_to_row(rec):
    return [rec.get(h, "") for h in HEADER]


def db_write(rec):
    \"\"\"v3.4 (S949): the call log table FIRST. Never raises; returns inserted|updated|deferred|off.\"\"\"
    if _cldb is None:
        return "off"
    try:
        with _db_lock:
            try:
                return _cldb.upsert(rec)
            except Exception as e1:     # a database error (e.g. the table missing after a failed startup init): make it once, retry once
                if type(e1).__name__ != "OperationalError":
                    raise
                _cldb.init()
                return _cldb.upsert(rec)
    except Exception as e:              # noqa: BLE001
        try:
            log("call log table write failed (the Sheet is still written; the raw log kept): %s %s"
                % (type(e).__name__, str(e)[:80]))
        except Exception:               # noqa: BLE001
            pass
        return "deferred"
"""))

EDITS.append(("""    # best-effort PHI-clean upsert; never let a failure break the webhook
    try:
        rec = extract_record(payload, event_type)
        if not rec:
            return jsonify(ok=True, captured=True, event=event_type, sheet="skipped"), 200
        with _lock:
""", """    # best-effort PHI-clean upsert; never let a failure break the webhook
    db_action = "skipped"
    try:
        rec = extract_record(payload, event_type)
        if not rec:
            return jsonify(ok=True, captured=True, event=event_type, sheet="skipped"), 200
        db_action = db_write(rec)       # v3.4 (S949): the table first; never raises
        with _lock:
"""))

EDITS.append(("""        return jsonify(ok=True, captured=True, event=event_type, sheet=action, row=r), 200
    except Exception as e:              # noqa: BLE001
        log("sheet write failed (kept in raw log):", e)
        return jsonify(ok=True, captured=True, event=event_type, sheet="deferred"), 200
""", """        return jsonify(ok=True, captured=True, event=event_type, sheet=action, row=r, db=db_action), 200
    except Exception as e:              # noqa: BLE001
        log("sheet write failed (kept in raw log):", e)
        return jsonify(ok=True, captured=True, event=event_type, sheet="deferred", db=db_action), 200
"""))

EDITS.append(("""    log("Phase B receiver v3.3 (dual-key + incoming + app-dialled outgoing capture, S935; the verified row, S698). raw logs: %s" % RAW_DIR)
    log("reject logs: %s" % REJECT_DIR)
""", """    log("Phase B receiver v3.4 (dual-key + incoming + app-dialled outgoing capture, S935; the verified row, S698; the call log table first, S949). raw logs: %s" % RAW_DIR)
    log("reject logs: %s" % REJECT_DIR)
    if _cldb is None:
        log("call log table: %s -- the Sheet path unchanged" % _CLDB_STATE)
    else:
        try:
            n, since = _cldb.init()
            log("call log table: %s -- %d rows since %s" % (_cldb.DB_PATH, n, since))
        except Exception as e:          # noqa: BLE001
            log("call log table: NOT ready (%s) -- each call will retry; the Sheet path unchanged" % type(e).__name__)
"""))

EDITS.append(("""    finally:
        _store.clear(); _store.update(_ws_save)

    print("selftest: %d/%d passed" % (passed, passed + failed))
""", """    finally:
        _store.clear(); _store.update(_ws_save)

    # -- v3.4 (S949): the table first, the Sheet unchanged, a table failure harmless ------------------------
    global _cldb
    _cldb_save = _cldb
    _ws_save2 = dict(_store)
    try:
        import call_log_db as _m
        _dbp_save = _m.DB_PATH
        with tempfile.TemporaryDirectory() as td:
            _m.DB_PATH = os.path.join(td, "calls.db")
            _m.init()
            _cldb = _m
            _raw_q_save = (globals()["RAW_DIR"], globals()["QUEUE_DIR"])
            globals()["RAW_DIR"] = os.path.join(td, "raw")         # never the live raw log or the live pipeline queue
            globals()["QUEUE_DIR"] = os.path.join(td, "queue")
            fws2 = _FakeWS([list(HEADER)])
            _store.update({"ws": fws2, "index": {}, "refs": {}})
            SECRET, SECRET_PREV = "NewKey@12345", ""
            num = "5" + "0" * 8 + "2"
            body = {"event_type": "call.end", "payload": {"id": "s9", "category": "incoming", "status": "bridged",
                                                          "customer_number": "+91" + num, "duration": 12}}
            r = c.post("/mo-callhook?key=NewKey@12345", json=body)
            j = r.get_json() or {}
            check("v3.4 end: table inserted AND sheet inserted", j.get("db") == "inserted" and j.get("sheet") == "inserted")
            body["event_type"] = "call.summary"
            j = (c.post("/mo-callhook?key=NewKey@12345", json=body).get_json() or {})
            check("v3.4 summary: both updated, one row each", j.get("db") == "updated" and j.get("sheet") == "updated"
                  and len(_m.rows()) == 1 and len(fws2.rows) == 2)
            check("v3.4 the table row equals the sheet row",
                  [str(_m.rows()[0][h]) for h in HEADER] == [str(v) for v in fws2.rows[1]])
            _m.DB_PATH = os.path.join(td, "no_such_dir", "calls.db")       # the table cannot be written
            body2 = {"event_type": "call.end", "payload": {"id": "s10", "category": "incoming", "status": "missed",
                                                           "customer_number": "+91" + num}}
            j = (c.post("/mo-callhook?key=NewKey@12345", json=body2).get_json() or {})
            check("v3.4 a table failure: db=deferred, the sheet still inserted", j.get("db") == "deferred"
                  and j.get("sheet") == "inserted" and len(fws2.rows) == 3)
            _cldb = None
            j = (c.post("/mo-callhook?key=NewKey@12345", json=dict(body2, event_type="call.summary")).get_json() or {})
            check("v3.4 the table off: db=off, the sheet still updated", j.get("db") == "off" and j.get("sheet") == "updated")
            j = (c.post("/mo-callhook?key=NewKey@12345", json={"payload": {"category": "webcall"}}).get_json() or {})
            check("v3.4 a skipped event writes neither", j.get("sheet") == "skipped" and "db" not in j)
    except Exception as e:              # noqa: BLE001
        check("v3.4 table tests ran (%s)" % type(e).__name__, False)
    finally:
        _cldb = _cldb_save
        try:
            globals()["RAW_DIR"], globals()["QUEUE_DIR"] = _raw_q_save
        except NameError:
            pass
        try:
            _m.DB_PATH = _dbp_save
        except NameError:
            pass
        _store.clear(); _store.update(_ws_save2)

    print("selftest: %d/%d passed" % (passed, passed + failed))
"""))


def main():
    src, dst = sys.argv[1], sys.argv[2]
    b = open(src, "rb").read()
    if hashlib.md5(b).hexdigest() != FROM_MD5:
        sys.exit("FROM is not 70c3d257 -- refused")
    t = b.decode("utf-8")
    for i, (a, n) in enumerate(EDITS, 1):
        k = t.count(a)
        if k != 1:
            sys.exit("anchor %d occurs %d times -- refused" % (i, k))
        t = t.replace(a, n)
    open(dst, "wb").write(t.encode("utf-8"))
    print("TO written: %s %s" % (dst, hashlib.md5(t.encode("utf-8")).hexdigest()))


if __name__ == "__main__":
    main()
