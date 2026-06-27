#!/usr/bin/env python3
"""
notifier_wa.py - new-WhatsApp -> ntfy push for Dr. Manoj Agarwal Clinic.

A long-running, READ-ONLY watcher. It does NOT touch the receiver or the relay.
Every POLL_SECONDS it checks the WA_Inbox tab for NEW inbound patient messages,
resolves the patient's NAME from Patient_Master (last-10-digit phone match - the
same key the dashboard uses), and sends a NAME-ONLY push to ntfy:

      Title:  New WhatsApp
      Body :  <Patient Name>          (or "<Name> (3 messages)")
              "new contact"           (when the number isn't in Patient_Master)

PRIVACY: pushes carry the NAME only - never the phone number, the message text,
or any diagnosis.

SOURCES (all read-only, same spreadsheet):
  - WA_Inbox       tab : inbound rows the receiver already writes
  - Patient_Master tab : phone -> name

It reuses the receiver's own /root/wa/.env for the sheet id + service-account key,
so there is nothing new to configure there.

CONFIG (via systemd Environment=, with safe defaults):
  NTFY_SERVER     default https://ntfy.sh
  NTFY_TOPIC      REQUIRED - the private topic
  POLL_SECONDS    default 30
  PAT_REFRESH_MIN default 30   (re-read Patient_Master this often, for new patients)
  WA_TAB          default WA_Inbox
  PATIENT_TAB     default Patient_Master
  STATE_FILE      default /root/wa/notifier_state.json
From /root/wa/.env (read-only): WA_SHEET_ID, WA_SA_KEY, PATIENT_SHEET_ID (optional)

DEDUPE: state stores the WA_Inbox row count seen last time; only rows beyond that
are considered. First-ever run (no state) just records the current count as a
baseline and alerts nothing historical - so it never floods on start/restart.
"""

import os
import re
import sys
import json
import time
import urllib.request
import urllib.error

import gspread
from google.oauth2.service_account import Credentials

HERE = os.path.dirname(os.path.abspath(__file__))


def _load_env_file(path):
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except OSError:
        pass


# reuse the receiver's .env for the sheet id + key path (read-only)
_load_env_file(os.path.join(HERE, ".env"))

SHEET_ID    = os.environ.get("WA_SHEET_ID", "").strip()
SA_KEY      = os.environ.get("WA_SA_KEY", "").strip()
PAT_SHEET   = os.environ.get("PATIENT_SHEET_ID", "").strip() or SHEET_ID
WA_TAB      = os.environ.get("WA_TAB", "WA_Inbox").strip() or "WA_Inbox"
PAT_TAB     = os.environ.get("PATIENT_TAB", "Patient_Master").strip() or "Patient_Master"
NTFY_SERVER = (os.environ.get("NTFY_SERVER", "https://ntfy.sh").strip() or "https://ntfy.sh").rstrip("/")
NTFY_TOPIC  = os.environ.get("NTFY_TOPIC", "").strip()
POLL        = int(os.environ.get("POLL_SECONDS", "30"))
PAT_REFRESH = int(os.environ.get("PAT_REFRESH_MIN", "30")) * 60
STATE_FILE  = os.environ.get("STATE_FILE", os.path.join(HERE, "notifier_state.json")).strip()
SCOPES      = ["https://www.googleapis.com/auth/spreadsheets.readonly"]


def log(*a):
    print("[notifier_wa]", *a, flush=True)


def last10(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-10:] if len(d) >= 10 else d


def findcol(header_lower, candidates):
    """Mirror the dashboard's tolerant header match: exact first, then 'contains',
    always respecting candidate priority order."""
    for c in candidates:
        if c in header_lower:
            return header_lower.index(c)
    for c in candidates:
        for i, h in enumerate(header_lower):
            if c in h:
                return i
    return -1


def connect():
    creds = Credentials.from_service_account_file(SA_KEY, scopes=SCOPES)
    return gspread.authorize(creds)


def load_patient_map(gc):
    m = {}
    try:
        ws = gc.open_by_key(PAT_SHEET).worksheet(PAT_TAB)
        vals = ws.get_all_values()
        if len(vals) < 2:
            return m
        H = [str(x).strip().lower() for x in vals[0]]
        iPhone = findcol(H, ['phone number', 'mobile number', 'mobile no', 'mobile', 'phone', 'number', 'phone10'])
        iName  = findcol(H, ['patient name', 'name', 'first name'])
        if iPhone < 0:
            return m
        for r in vals[1:]:
            if iPhone >= len(r):
                continue
            ph = last10(r[iPhone])
            if not ph:
                continue
            nm = (r[iName].strip() if (0 <= iName < len(r)) else "")
            if ph not in m and nm:
                m[ph] = nm
    except Exception as e:  # noqa: BLE001
        log("patient map load failed:", e)
    return m


def ntfy_push(title, body, tags="speech_balloon", priority="high"):
    if not NTFY_TOPIC:
        log("NTFY_TOPIC not set - cannot push")
        return False
    url = "%s/%s" % (NTFY_SERVER, NTFY_TOPIC)
    req = urllib.request.Request(url, data=body.encode("utf-8"), method="POST")
    req.add_header("Title", title)      # ASCII only
    req.add_header("Priority", priority)
    req.add_header("Tags", tags)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except Exception as e:  # noqa: BLE001
        log("ntfy push failed:", e)
        return False


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(st):
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(st, f)
        os.replace(tmp, STATE_FILE)
    except Exception as e:  # noqa: BLE001
        log("save_state failed:", e)


def wa_dir_phone_idx(ws):
    H = [str(x).strip().lower() for x in ws.row_values(1)]
    return (
        findcol(H, ['phone', 'number', 'customer_number', 'from', 'mobile']),
        findcol(H, ['direction', 'dir']),
    )


def main():
    miss = [k for k, v in {"WA_SHEET_ID": SHEET_ID, "WA_SA_KEY": SA_KEY,
                           "NTFY_TOPIC": NTFY_TOPIC}.items() if not v]
    if miss:
        log("MISSING config:", ", ".join(miss))
        sys.exit(2)

    gc = connect()
    ws = gc.open_by_key(SHEET_ID).worksheet(WA_TAB)
    iPhone, iDir = wa_dir_phone_idx(ws)
    if iPhone < 0:
        log("WA_Inbox has no phone column - aborting")
        sys.exit(2)

    pat = load_patient_map(gc)
    last_pat = time.time()
    log("patient map loaded: %d names" % len(pat))

    st = load_state()
    vals = ws.get_all_values()
    if "wa_rows" in st:
        last_count = int(st["wa_rows"])
        if last_count > len(vals):      # sheet shrank/reset -> rebaseline
            last_count = len(vals)
    else:
        last_count = len(vals)          # first run: baseline, alert nothing historical
        st["wa_rows"] = last_count
        save_state(st)
    log("baseline rows=%d (alert only on rows after this); poll=%ds" % (last_count, POLL))

    while True:
        time.sleep(POLL)
        try:
            if time.time() - last_pat > PAT_REFRESH:
                newpat = load_patient_map(gc)
                if newpat:
                    pat = newpat
                last_pat = time.time()

            vals = ws.get_all_values()
            n = len(vals)
            if n < last_count:
                last_count = n
                st["wa_rows"] = n
                save_state(st)
                continue
            if n == last_count:
                continue

            new_rows = vals[last_count:n]
            known = {}     # name -> count
            unknown = 0
            for r in new_rows:
                direction = str(r[iDir]).lower() if (0 <= iDir < len(r)) else ""
                if "out" in direction:
                    continue            # our own outbound reply -> skip
                phone = r[iPhone] if iPhone < len(r) else ""
                name = pat.get(last10(phone), "")
                if name:
                    known[name] = known.get(name, 0) + 1
                else:
                    unknown += 1

            for name, cnt in known.items():
                body = name if cnt == 1 else "%s (%d messages)" % (name, cnt)
                ntfy_push("New WhatsApp", body)
            if unknown:
                body = "new contact" if unknown == 1 else "%d new contacts" % unknown
                ntfy_push("New WhatsApp", body)

            last_count = n
            st["wa_rows"] = n
            save_state(st)

        except Exception as e:  # noqa: BLE001
            log("cycle error (will retry):", e)
            try:
                gc = connect()
                ws = gc.open_by_key(SHEET_ID).worksheet(WA_TAB)
            except Exception as e2:  # noqa: BLE001
                log("reconnect failed:", e2)


if __name__ == "__main__":
    main()
