#!/usr/bin/env python3
"""
callhook_write_probe.py -- G-6 / F-38: prove the call-hook's WRITE PATH daily.
Dr. Manoj Agarwal Clinic, Bareilly. Session 140.

WHY THIS EXISTS (the F-38 lesson)
  The receiver answers 200 even when the Sheet write fails ("sheet":
  "deferred") -- by design, so MyOperator never retries into a storm. That
  means a green service status is NOT proof that rows are landing. On
  01-Jul the followups watcher sat green while doing nothing (see
  INCIDENT_2026-07-01). A check must traverse the path the fault would
  traverse: this probe sends one real, signed, synthetic webhook through
  the PUBLIC url (DNS -> OpenLiteSpeed -> proxy -> gunicorn -> Flask ->
  gate -> extract -> gspread -> Sheet) and then reads the Sheet back to
  verify the row moved. Anything less is a light on the wrong circuit.

WHAT IT SENDS
  A call.end payload with category=obd and client_ref_id=PROBE-WRITEPATH.
  extract_record() keys the row on that constant, so the probe UPSERTS THE
  SAME SINGLE ROW every day -- no growth, no PHI (no phone number at all).
  Dashboard bundles never query that key; the row is invisible to staff.

VERDICT
  PASS  -> HTTP 200, response says sheet=inserted/updated, AND the row's
           captured_at_ist read back from Call_Durations is fresher than
           FRESH_SECONDS. Exit 0, one PASS line.
  FAIL  -> anything else, including the F-38 case (200 + sheet=deferred).
           Exit 1, one FAIL line with the reason. The cron redirects both
           to write_probe.log; the Diagnostics watchman lane for the
           CALLHOOK_* family covers escalation (Register v2.1 s2.5).

SECRETS (D176)
  CALLHOOK_SECRET is read from /root/wa/.env and sent only inside the
  request. It is never printed, never logged, never part of any error
  message. The URL is logged with the key masked.

OPERATIONS
  Selftest (offline):  /root/wa/venv/bin/python3 callhook_write_probe.py --selftest
  Manual run:          /root/wa/venv/bin/python3 callhook_write_probe.py
  Cron (daily 08:45):  45 8 * * * /root/wa/venv/bin/python3 \
      /root/wa/call-hook/callhook_write_probe.py >> /root/wa/call-hook/write_probe.log 2>&1
"""

import datetime
import glob
import json
import os
import re
import sys
import time

ENV_PATH = os.environ.get("PROBE_ENV_PATH", "/root/wa/.env")
PROBE_URL = os.environ.get("CALLHOOK_PROBE_URL", "").strip() \
    or "https://followup.dr-manoj.in/mo-callhook"
PROBE_KEY = "PROBE-WRITEPATH"
FRESH_SECONDS = 180
SHEET_ID_DEFAULT = "1USjArkqIdrE9hIqerghms76STatM5XTbSW_a9I3klo0"
TAB = "Call_Durations"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


def log(*a):
    print("[write-probe %s]"
          % datetime.datetime.now(IST).strftime("%d-%b %H:%M:%S"),
          *a, flush=True)


def load_env(path=None):
    """Tiny .env reader: KEY=VALUE lines, quotes stripped, no export kw."""
    out = {}
    try:
        with open(path or ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    except Exception:                   # noqa: BLE001
        pass
    return out


def mask_url(url, key):
    return url + "?key=" + ("*" * 4 + key[-2:] if len(key) >= 6 else "***")


def probe_payload():
    return {
        "event_type": "call.end",
        "payload": {
            "category": "obd",
            "client_ref_id": PROBE_KEY,
            "status": "probe",
            "duration": 0,
            "recording_filename": "",
        },
    }


def parse_captured_at(value):
    """'2026-07-12T18:05:33+05:30' -> aware datetime, or None."""
    v = str(value or "").strip()
    m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\+05:30$", v)
    if not m:
        return None
    try:
        return datetime.datetime.strptime(
            m.group(1), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=IST)
    except ValueError:
        return None


def _find_sa_key():
    explicit = (os.environ.get("CALLHOOK_SA_KEY", "").strip()
                or os.environ.get("WA_SA_KEY", "").strip())
    if explicit and os.path.exists(explicit):
        return explicit
    here = os.path.dirname(os.path.abspath(__file__))
    for d in ("/root/wa", "/root/wa/keys", here, "/root"):
        for path in glob.glob(os.path.join(d, "*.json")):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if obj.get("type") == "service_account" and obj.get("client_email"):
                    return path
            except Exception:           # noqa: BLE001
                continue
    return ""


def verify_row_fresh():
    """Read the PROBE row back from the Sheet; return (ok, detail)."""
    import gspread
    sa = _find_sa_key()
    if not sa:
        return False, "no service-account key found"
    gc = gspread.service_account(filename=sa, scopes=SCOPES)
    env = load_env()
    sheet_id = (os.environ.get("CALLHOOK_SHEET_ID", "").strip()
                or env.get("CALLHOOK_SHEET_ID", "").strip()
                or env.get("WA_SHEET_ID", "").strip()
                or SHEET_ID_DEFAULT)
    ws = gc.open_by_key(sheet_id).worksheet(TAB)
    cell = ws.find(PROBE_KEY, in_column=1)
    if cell is None:
        return False, "probe row not found in %s col A" % TAB
    header = ws.row_values(1)
    row = ws.row_values(cell.row)
    try:
        idx = header.index("captured_at_ist")
    except ValueError:
        return False, "captured_at_ist column missing"
    captured = row[idx] if idx < len(row) else ""
    dt = parse_captured_at(captured)
    if dt is None:
        return False, "unparseable captured_at_ist: %r" % captured
    age = (datetime.datetime.now(IST) - dt).total_seconds()
    if age > FRESH_SECONDS:
        return False, "row is stale: captured %ds ago (>%ds)" % (age, FRESH_SECONDS)
    return True, "row %d fresh (%ds old)" % (cell.row, int(age))


def main():
    import requests
    env = load_env()
    secret = env.get("CALLHOOK_SECRET", "") or env.get("CALLHOOK_SECRET_PREV", "")
    if not secret:
        log("FAIL: CALLHOOK_SECRET not found in", ENV_PATH)
        return 1

    log("POST", mask_url(PROBE_URL, secret))
    try:
        r = requests.post(PROBE_URL, params={"key": secret},
                          json=probe_payload(), timeout=25)
    except Exception as e:              # noqa: BLE001
        log("FAIL: request error:", type(e).__name__, e)
        return 1

    if r.status_code != 200:
        log("FAIL: HTTP", r.status_code, "-- gate or proxy problem")
        return 1
    try:
        body = r.json()
    except ValueError:
        log("FAIL: non-JSON reply")
        return 1
    sheet = str(body.get("sheet", ""))
    if sheet not in ("inserted", "updated"):
        # THE F-38 CASE: green reply, dead write path.
        log("FAIL: HTTP 200 but sheet=%r -- write path is NOT working" % sheet)
        return 1

    time.sleep(3)                       # let the write settle before read-back
    try:
        ok, detail = verify_row_fresh()
    except Exception as e:              # noqa: BLE001
        log("FAIL: read-back error:", type(e).__name__, e)
        return 1
    if not ok:
        log("FAIL:", detail)
        return 1
    log("PASS: hook reply sheet=%s; %s" % (sheet, detail))
    return 0


# ---------------------------------------------------------------------------
def _selftest():
    import tempfile
    passed = failed = 0

    def check(name, cond):
        nonlocal passed, failed
        if cond:
            passed += 1
        else:
            failed += 1
            print("  FAIL:", name)

    with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
        f.write("# comment\nCALLHOOK_SECRET='abc123'\nWA_SHEET_ID=xyz\nBAD LINE\n")
        p = f.name
    env = load_env(p)
    os.unlink(p)
    check("env parses quoted secret", env.get("CALLHOOK_SECRET") == "abc123")
    check("env parses plain value", env.get("WA_SHEET_ID") == "xyz")
    check("env skips junk", "BAD LINE" not in env)

    check("mask never shows the key",
          "abc123" not in mask_url("https://x/h", "abc123secret"))
    check("mask keeps last-2", mask_url("https://x/h", "abc123").endswith("23"))

    pl = probe_payload()
    check("payload keys the probe row",
          pl["payload"]["client_ref_id"] == PROBE_KEY
          and pl["payload"]["category"] == "obd"
          and pl["event_type"] == "call.end")
    check("payload carries no PHI",
          "phone" not in json.dumps(pl).lower()
          and "customer_number" not in json.dumps(pl))

    now = datetime.datetime.now(IST).strftime("%Y-%m-%dT%H:%M:%S") + "+05:30"
    dt = parse_captured_at(now)
    check("captured_at parses",
          dt is not None
          and abs((datetime.datetime.now(IST) - dt).total_seconds()) < 5)
    check("garbage captured_at rejected", parse_captured_at("12 Jul") is None)
    check("blank captured_at rejected", parse_captured_at("") is None)

    print("SELFTEST: %d/%d PASS" % (passed, passed + failed))
    return failed == 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    sys.exit(main())
