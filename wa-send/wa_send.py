#!/usr/bin/env python3
# =============================================================================
# wa_send.py  —  Dr Manoj Agarwal Clinic
# Window-guarded WhatsApp FREE-TEXT sender.
#
# STATUS: BUILD + TEST. Not wired into any live app yet. Safe to run by hand.
#
# WHY THIS EXISTS
#   A free-text (non-template) WhatsApp only DELIVERS if the patient messaged the
#   clinic within the last 24 hours (a WhatsApp/Meta rule). This module checks
#   the WA_Inbox tab for that number's most recent INCOMING message and only
#   sends if the 24h window is open. If it is closed (or the patient never wrote
#   in), it REFUSES and tells you to use an approved template instead.
#
# TWO WAYS TO USE
#   1) Command line (testing):
#        python3 wa_send.py <10-digit-number> "your message"     # guarded send
#        python3 wa_send.py --check <10-digit-number>            # window status only
#        python3 wa_send.py --dry-run <number> "msg"             # guard + preview, no send
#   2) Imported by another app (e.g. the dashboard) later:
#        from wa_send import load_config, send_with_guard
#        cfg = load_config()
#        result = send_with_guard(cfg, number, message)   # returns a dict
#
# CONFIG (no secrets in this file)
#   Sheet settings are reused from the receiver's /root/wa/.env :
#     WA_SHEET_ID, WA_SA_KEY (service-account json path), WA_TAB (default WA_Inbox)
#   The WhatsApp send token is read (first found wins) from:
#     - env var  WA_SEND_TOKEN   or   WA_TOKEN
#     - a file given by  --token-env PATH   (KEY=VALUE lines)
#     - /root/wa/wa_send.env  if present
#   The token is NEVER printed (masked) and NEVER committed to git.
#
# Company id / phone-number id are public identifiers (safe defaults below).
# =============================================================================

import argparse
import datetime
import http.client
import json
import os
import re
import sys

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
WINDOW_HOURS = 24

DEFAULT_COMPANY_ID      = "68384350414b9847"
DEFAULT_PHONE_NUMBER_ID = "1090067637530949"
DEFAULT_COUNTRY_CODE    = "91"
API_HOST                = "publicapi.myoperator.co"
API_PATH                = "/chat/messages"
RECEIVER_ENV            = "/root/wa/.env"
SEND_ENV                = "/root/wa/wa_send.env"


# ----------------------------- small helpers --------------------------------
def read_env_file(path):
    vals = {}
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals


def last10(raw):
    d = re.sub(r"\D", "", raw or "")
    return d[-10:] if len(d) >= 10 else d


def mask(tok):
    return (tok[:4] + "…") if tok and len(tok) > 4 else "(missing)"


def load_config(token_env_path=None):
    recv = read_env_file(RECEIVER_ENV)

    token = (os.environ.get("WA_SEND_TOKEN")
             or os.environ.get("WA_TOKEN"))
    if not token and token_env_path:
        f = read_env_file(token_env_path)
        token = f.get("WA_SEND_TOKEN") or f.get("WA_TOKEN")
    if not token and os.path.exists(SEND_ENV):
        f = read_env_file(SEND_ENV)
        token = f.get("WA_SEND_TOKEN") or f.get("WA_TOKEN")
    if not token:
        token = recv.get("WA_SEND_TOKEN") or recv.get("WA_TOKEN")

    return {
        "token":           token,
        "company_id":      recv.get("WA_COMPANY_ID", DEFAULT_COMPANY_ID),
        "phone_number_id": recv.get("WA_PHONE_NUMBER_ID", DEFAULT_PHONE_NUMBER_ID),
        "country_code":    DEFAULT_COUNTRY_CODE,
        "sheet_id":        recv.get("WA_SHEET_ID"),
        "sa_key":          recv.get("WA_SA_KEY"),
        "tab":             recv.get("WA_TAB", "WA_Inbox"),
    }


def parse_ist(s):
    """Parse a WA_Inbox timestamp into an aware IST datetime, or None."""
    if not s:
        return None
    s = str(s).strip()
    try:
        t = s.replace("Z", "+00:00")
        # trim 7-9 digit fractional seconds that Py3.9 can't parse
        m = re.search(r"\.(\d{7,9})", t)
        if m:
            t = t.replace("." + m.group(1), "." + m.group(1)[:6])
        d = datetime.datetime.fromisoformat(t)
        if d.tzinfo is None:
            d = d.replace(tzinfo=IST)
        return d.astimezone(IST)
    except Exception:
        return None


# --------------------- WA_Inbox read (isolated for tests) -------------------
def fetch_inbox_rows(cfg):
    """Return WA_Inbox as a list of header-keyed dicts. Imports google libs lazily."""
    import gspread
    from google.oauth2.service_account import Credentials
    scopes = ["https://www.googleapis.com/auth/spreadsheets",
              "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(cfg["sa_key"], scopes=scopes)
    gc = gspread.authorize(creds)
    ws = gc.open_by_key(cfg["sheet_id"]).worksheet(cfg["tab"])
    values = ws.get_all_values()
    if not values:
        return []
    header = [h.strip() for h in values[0]]
    rows = []
    for r in values[1:]:
        row = {header[i]: (r[i] if i < len(r) else "") for i in range(len(header))}
        rows.append(row)
    return rows


def _col(row, *names):
    """Case-insensitive column getter with fallbacks."""
    low = {k.lower(): v for k, v in row.items()}
    for n in names:
        if n.lower() in low:
            return low[n.lower()]
    return ""


def latest_inbound(cfg, number, _rows=None):
    """Most recent INCOMING timestamp (IST datetime) for this number, or None."""
    rows = _rows if _rows is not None else fetch_inbox_rows(cfg)
    want = last10(number)
    best = None
    for row in rows:
        direction = str(_col(row, "Direction")).strip().lower()
        if direction.startswith("out"):           # skip outgoing; keep incoming/blank
            continue
        if last10(_col(row, "Phone", "Number", "Customer")) != want:
            continue
        dt = parse_ist(_col(row, "Timestamp", "Time", "Received"))
        if dt and (best is None or dt > best):
            best = dt
    return best


def window_state(cfg, number, _rows=None, now=None):
    """Return (is_open: bool, last_inbound: dt|None, age: timedelta|None)."""
    dt = latest_inbound(cfg, number, _rows=_rows)
    if dt is None:
        return (False, None, None)
    now = now or datetime.datetime.now(IST)
    age = now - dt
    return (age <= datetime.timedelta(hours=WINDOW_HOURS), dt, age)


# ------------------------------- sending ------------------------------------
def build_payload(cfg, number, message, reply_to=None, preview_url=False):
    return {
        "phone_number_id": cfg["phone_number_id"],
        "customer_country_code": cfg["country_code"],
        "customer_number": last10(number),
        "data": {
            "type": "text",
            "context": {"body": message, "preview_url": bool(preview_url)},
        },
        "reply_to": reply_to,
        "myop_ref_id": None,
    }


def send_text(cfg, number, message, reply_to=None, preview_url=False):
    """POST the free-text message. Returns (http_status, parsed_or_raw)."""
    payload = build_payload(cfg, number, message, reply_to, preview_url)
    headers = {
        "Authorization": "Bearer " + (cfg["token"] or ""),  # capital B required
        "X-MYOP-COMPANY-ID": cfg["company_id"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    conn = http.client.HTTPSConnection(API_HOST, timeout=30)
    try:
        conn.request("POST", API_PATH, json.dumps(payload), headers)
        res = conn.getresponse()
        status = res.status
        text = res.read().decode("utf-8", errors="replace")
    finally:
        try:
            conn.close()
        except Exception:
            pass
    try:
        return status, json.loads(text)
    except Exception:
        return status, text


def send_with_guard(cfg, number, message, reply_to=None, _rows=None):
    """Safe entry point. Checks the 24h window, sends only if open.
    Returns a dict the caller (e.g. dashboard) can render."""
    is_open, last_dt, age = window_state(cfg, number, _rows=_rows)
    out = {
        "number": last10(number),
        "window_open": is_open,
        "last_inbound": last_dt.isoformat() if last_dt else None,
        "hours_since": round(age.total_seconds() / 3600, 1) if age else None,
        "sent": False,
        "ok": False,
        "reason": None,
        "message_id": None,
        "http_status": None,
    }
    if not cfg.get("token"):
        out["reason"] = "No WhatsApp token configured (set WA_SEND_TOKEN)."
        return out
    if not is_open:
        if last_dt is None:
            out["reason"] = ("No incoming WhatsApp on record from this number — "
                             "free text not allowed; use an approved template.")
        else:
            out["reason"] = (f"24h window closed (last message {out['hours_since']}h ago) — "
                             "use an approved template instead.")
        return out

    status, body = send_text(cfg, number, message, reply_to=reply_to)
    out["http_status"] = status
    if status == 200 and isinstance(body, dict) and str(body.get("status", "")).lower() == "success":
        out["sent"] = True
        out["ok"] = True
        out["message_id"] = (body.get("data") or {}).get("message_id")
        out["reason"] = "Accepted."
    else:
        out["reason"] = "Send failed."
        out["raw"] = body
    return out


# --------------------------------- CLI --------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Window-guarded WhatsApp free-text sender")
    ap.add_argument("number", help="10-digit destination")
    ap.add_argument("message", nargs="?", default=None, help="message text (quote it)")
    ap.add_argument("--check", action="store_true", help="only report window status; do not send")
    ap.add_argument("--dry-run", action="store_true", help="check window + preview, but do not send")
    ap.add_argument("--token-env", default=None, help="path to a KEY=VALUE file holding WA_SEND_TOKEN")
    ap.add_argument("--reply-to", default=None, help="optional message_id to quote/thread")
    args = ap.parse_args()

    cfg = load_config(token_env_path=args.token_env)

    if not cfg["sheet_id"] or not cfg["sa_key"]:
        print("✗ Could not read WA_SHEET_ID / WA_SA_KEY from", RECEIVER_ENV)
        sys.exit(2)

    num = last10(args.number)
    if len(num) != 10:
        print(f"✗ '{args.number}' is not a 10-digit number (got '{num}').")
        sys.exit(2)

    # status-only mode
    if args.check:
        is_open, last_dt, age = window_state(cfg, num)
        print(f"Number 91-{num[:2]}xxxxx{num[-3:]} (masked)")
        if last_dt is None:
            print("  Window: CLOSED — no incoming message on record. Template required.")
        else:
            hrs = round(age.total_seconds() / 3600, 1)
            print(f"  Last incoming: {last_dt.isoformat()}  ({hrs}h ago)")
            print(f"  Window: {'OPEN — free text allowed.' if is_open else 'CLOSED — template required.'}")
        return

    if args.message is None:
        print("✗ A message is required unless using --check.")
        sys.exit(2)

    if args.dry_run:
        is_open, last_dt, age = window_state(cfg, num)
        print(f"DRY RUN — to 91-{num[:2]}xxxxx{num[-3:]} (masked)")
        print(f"  token        : {mask(cfg['token'])}")
        print(f"  window_open  : {is_open}")
        print(f"  last_inbound : {last_dt.isoformat() if last_dt else None}")
        print(f"  message      : {args.message!r}")
        print("  -> would SEND." if is_open else "  -> would REFUSE (use a template).")
        return

    result = send_with_guard(cfg, num, args.message, reply_to=args.reply_to)
    print(json.dumps({k: v for k, v in result.items() if k != "raw"}, indent=2, ensure_ascii=False))
    if result.get("ok"):
        print("✅ Sent (window was open).")
    elif not result["window_open"]:
        print("⛔ Not sent —", result["reason"])
    else:
        print("⚠ Not sent —", result["reason"])
        if result.get("raw"):
            print(json.dumps(result["raw"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
