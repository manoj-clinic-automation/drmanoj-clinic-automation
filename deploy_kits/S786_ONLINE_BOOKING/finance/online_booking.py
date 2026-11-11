#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""online_booking.py -- kit S786_ONLINE_BOOKING (session S428, 11-Nov-2026, the parent). NEW.

THE OWNER, 11-Nov-2026 07:15 IST: "One patient has booked a consultation through the doctor's system online, and she has paid
online, and I have received a mail in my Google account. So I need this to be pulled and displayed when this happens, so that
staff can see this." -- 07:59 IST: "Full mobile number required. Display required -- patient name, clinic id (for existing
ones), full mobile number, paid 600/- online, appointment time booked (if it's out of these timings -- 11 am to 1.30 pm, and
7 pm to 8.30 pm (Monday to Saturday) -- then they call patient and inform them to come in these timings)."

WHAT COMES IN. Docterz mails "<name> appointment at <11 Nov 2026 10:00 AM> payment completed." from support@docterz.in to the
owner's personal Gmail; the body carries Order Id, Patient Name, Patient Mobile, Payment Amount and the Razorpay Payment ID.
A filter in his personal Gmail forwards these mails (and only these) to the clinic Gmail, which this server already reads
(the query agent's IMAP login, /root/deploy/email_agent.json -- read here, never written).

WHAT THIS DOES, every 3 minutes (cron, flock):
  1. opens the clinic Gmail READ-ONLY (EXAMINE: no mail is marked read, labelled, moved or deleted) and asks Gmail for the
     Docterz 'payment completed' mails of the last LOOK_DAYS days;
  2. reads each one -- name, FULL mobile (the owner's ruling for this screen), amount, the booked time, the Razorpay ids;
  3. finds the clinic ID(s) on that mobile in patient_ref (the ring pop-up's own read-only lookup, ring_common.lookup_caller);
  4. keeps it ONCE in finance.db table online_booking (UNIQUE on the Razorpay payment id; insert-only -- a row is never
     rewritten by this job, so a staff tap 'Phone kar diya' is never lost);
  5. for a NEW row whose booked day is today or later: a push notification to the phones of PUSH_TO (the portal's own push,
     ring_common.push_user -- only phones that allowed notifications get it);
  6. writes its state (last run, last good run, what it found) to STATE, which the page shows as "Last checked".
A mail it cannot read (no payment id) is counted in the state and never stored half.

TIMINGS (the owner's words): Monday to Saturday, 11:00-13:30 and 19:00-20:30. A booked time outside them -- or a Sunday, or a
time that could not be read -- is out_of_hours=1: staff call the patient and tell them to come in those timings.

CLI:  online_booking.py            one pass (what cron runs)
      online_booking.py --selftest  the parser on built-in made-up mails; no network, no database
      online_booking.py --dry       one pass that reads the mailbox and prints COUNTS ONLY; writes and pushes nothing
Stdlib only (+ ring_common from /root/portal for the lookup and the push, both optional: absent = no ID, no push).
"""
import datetime as dt
import email
import html
import imaplib
import json
import os
import re
import sqlite3
import sys
import time
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

VERSION = "S786 1.0"
DB = os.environ.get("FINANCE_DB", "/root/finance/finance.db")
CFG = os.environ.get("EMAIL_AGENT_CONFIG", "/root/deploy/email_agent.json")
STATE = os.environ.get("OB_STATE", "/root/finance/online_booking_state.json")
PORTAL_DIR = os.environ.get("RING_PORTAL_DIR", "/root/portal")
LOOK_DAYS = int(os.environ.get("OB_LOOK_DAYS", "7"))
PUSH_TO = ("reception", "shivani", "alisha", "shavez", "manoj")
GMQ = "subject:(appointment payment completed) docterz newer_than:%dd"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
HOURS = ((11 * 60, 13 * 60 + 30), (19 * 60, 20 * 60 + 30))          # minutes of the day, both ends inclusive; Mon-Sat
MON = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}

SCHEMA = """CREATE TABLE IF NOT EXISTS online_booking (
    id            INTEGER PRIMARY KEY,
    payment_id    TEXT NOT NULL UNIQUE,      -- Razorpay pay_...
    order_id      TEXT,
    name          TEXT,
    mobile        TEXT,                      -- 10 digits, FULL (the owner's ruling for this screen, 11-Nov-2026)
    amount_p      INTEGER,                   -- paise
    appt_at       TEXT,                      -- 'YYYY-MM-DD HH:MM' IST; '' when the mail's time could not be read
    appt_raw      TEXT,                      -- the time as the mail wrote it
    out_of_hours  INTEGER,                   -- 1 = outside Mon-Sat 11:00-13:30 / 19:00-20:30 (or unread): staff call the patient
    clinic_ids    TEXT,                      -- JSON [{"id","name"}] on this mobile in patient_ref at the time it was read
    mail_at       TEXT,                      -- when Docterz sent it, IST
    seen_at       TEXT,                      -- when this server first read it, IST
    pushed        INTEGER DEFAULT 0,
    push_note     TEXT,
    called_by     TEXT,                      -- the staff tap 'Phone kar diya' (online_booking_portal.py)
    called_at     TEXT
)"""


def now_ist():
    return dt.datetime.now(IST)


def log(msg):
    print("%s %s" % (now_ist().strftime("%Y-%m-%d %H:%M:%S IST"), msg), flush=True)


# ------------------------------------------------------------------------------------------------ the parser
def _hdr(v):
    try:
        return str(make_header(decode_header(v or ""))).strip()
    except Exception:                                                  # noqa: BLE001
        return (v or "").strip()


def mail_text(msg):
    """The mail's words: text/plain if there is one, else the HTML with its tags taken out."""
    plain, htm = [], []
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        ct = part.get_content_type()
        if part.get("Content-Disposition", "").lower().startswith("attachment"):
            continue
        if ct not in ("text/plain", "text/html"):
            continue
        try:
            raw = part.get_payload(decode=True) or b""
            txt = raw.decode(part.get_content_charset() or "utf-8", "replace")
        except Exception:                                              # noqa: BLE001
            continue
        (plain if ct == "text/plain" else htm).append(txt)
    if plain and any(t.strip() for t in plain):
        return "\n".join(plain)
    t = "\n".join(htm)
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    t = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</tr>|</td>|</li>|</h\d>", "\n", t)
    t = re.sub(r"<[^>]+>", " ", t)
    return html.unescape(t)


def mobile10(raw):
    d = re.sub(r"\D+", "", str(raw or ""))
    if len(d) == 12 and d.startswith("91"):
        d = d[2:]
    elif len(d) == 11 and d.startswith("0"):
        d = d[1:]
    return d if len(d) == 10 else ""


def _field(text, label):
    m = re.search(r"(?im)^\s*" + label + r"\s*:\s*(.*?)\s*$", text)
    return m.group(1).strip() if m else ""


_APPT = re.compile(r"(?i)appointment\s+at\s+(\d{1,2})\s+([A-Za-z]{3})[A-Za-z]*\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*([AP]\.?M\.?)?")


def parse_appt(s):
    """'11 Nov 2026 10:00 AM' (and Docterz's own '06 Oct 2026 18:35 PM') -> ('2026-11-11 10:00', raw). ('', raw) if unread."""
    m = _APPT.search(s or "")
    if not m:
        return "", ""
    d, mon, y, h, mi, ap = m.groups()
    raw = m.group(0)[len("appointment at "):].strip() if m.group(0).lower().startswith("appointment at ") else m.group(0)
    try:
        h, mi = int(h), int(mi)
        ap = (ap or "").upper().replace(".", "")
        if ap == "PM" and h < 12:
            h += 12
        elif ap == "AM" and h == 12:
            h = 0
        when = dt.datetime(int(y), MON[mon.lower()[:3]], int(d), h, mi)
    except Exception:                                                  # noqa: BLE001
        return "", raw
    return when.strftime("%Y-%m-%d %H:%M"), raw


def out_of_hours(appt_at):
    """1 when the booked time is outside the clinic's timings (or a Sunday, or unread); 0 inside them."""
    if not appt_at:
        return 1
    try:
        t = dt.datetime.strptime(appt_at, "%Y-%m-%d %H:%M")
    except ValueError:
        return 1
    if t.weekday() == 6:
        return 1
    m = t.hour * 60 + t.minute
    return 0 if any(a <= m <= b for a, b in HOURS) else 1


def parse_mail(subject, text):
    """dict of the booking, or None when the mail is not a Docterz payment (no payment id)."""
    pay = _field(text, r"Payment\s*ID")
    if not re.match(r"^pay_[A-Za-z0-9]+$", pay or ""):
        m = re.search(r"\bpay_[A-Za-z0-9]{6,}\b", text or "")
        pay = m.group(0) if m else ""
    if not pay:
        return None
    name = _field(text, r"Patient\s*Name")
    if not name:
        m = re.match(r"^(?:Fwd?:\s*)?(.*?)\s+appointment\s+at\b", subject or "", re.I)
        name = m.group(1).strip() if m else ""
    amt = re.sub(r"[^\d.]", "", _field(text, r"Payment\s*Amount"))
    try:
        amount_p = int(round(float(amt) * 100)) if amt else None
    except ValueError:
        amount_p = None
    appt_at, raw = parse_appt(subject)
    if not appt_at:
        appt_at, raw2 = parse_appt(text)
        raw = raw or raw2
    return {"payment_id": pay, "order_id": _field(text, r"Order\s*Id"), "name": name,
            "mobile": mobile10(_field(text, r"Patient\s*Mobile")), "amount_p": amount_p,
            "appt_at": appt_at, "appt_raw": raw, "out_of_hours": out_of_hours(appt_at)}


# ------------------------------------------------------------------------------------------------ the clinic ID, the push
def _rc():
    if PORTAL_DIR not in sys.path:
        sys.path.insert(0, PORTAL_DIR)
    import ring_common as rc                                           # noqa: PLC0415
    return rc


def clinic_ids(mobile, name):
    """The patients on this mobile in patient_ref, the one whose name matches the booking first. [] on any failure."""
    if not mobile:
        return []
    try:
        info = _rc().lookup_caller(mobile)
    except Exception:                                                  # noqa: BLE001
        return []
    out = [{"id": p.get("clinic_id") or "", "name": p.get("name") or ""} for p in info.get("patients") or [] if p.get("clinic_id")]
    first = (name or "").strip().lower().split(" ")[0] if name else ""
    out.sort(key=lambda p: 0 if first and p["name"].strip().lower().startswith(first) else 1)
    return out


def hm12(appt_at):
    try:
        return dt.datetime.strptime(appt_at, "%Y-%m-%d %H:%M").strftime("%d %b, %I:%M %p").lstrip("0")
    except ValueError:
        return ""


def push_card(b):
    """(title, body) in Hindi for the staff phones."""
    ids = json.loads(b.get("clinic_ids") or "[]") if isinstance(b.get("clinic_ids"), str) else (b.get("clinic_ids") or [])
    idt = ("ID " + ids[0]["id"]) if ids else "नया मरीज़"
    amt = "₹%d" % (b["amount_p"] // 100) if b.get("amount_p") else "₹?"
    title = "\U0001F4B3 Online booking · %s online paid" % amt
    body = "%s · %s · %s · %s" % (b.get("name") or "?", idt, b.get("mobile") or "?", hm12(b.get("appt_at") or "") or (b.get("appt_raw") or "समय?"))
    if b.get("out_of_hours"):
        body += " · समय clinic का नहीं — patient को phone करें"
    return title, body


def push(b):
    try:
        rc = _rc()
    except Exception as e:                                             # noqa: BLE001
        return 0, "no push: %s" % type(e).__name__
    title, body = push_card(b)
    sent = failed = 0
    for who in PUSH_TO:
        try:
            s, f = rc.push_user(who, {"title": title, "body": body, "url": "/portal/booking", "tag": "ob-" + b["payment_id"],
                                      "ttl": 3600})
            sent, failed = sent + s, failed + f
        except Exception:                                              # noqa: BLE001
            failed += 1
    return sent, "sent %d, failed %d" % (sent, failed)


# ------------------------------------------------------------------------------------------------ the mailbox
def _all_mail(M):
    """The Gmail 'All Mail' folder (any language), else INBOX."""
    try:
        typ, data = M.list()
        for line in data or []:
            s = line.decode("utf-8", "replace") if isinstance(line, bytes) else str(line)
            if "\\All" in s:
                m = re.search(r'"([^"]+)"\s*$', s) or re.search(r"(\S+)\s*$", s)
                if m:
                    return '"%s"' % m.group(1)
    except Exception:                                                  # noqa: BLE001
        pass
    return "INBOX"


def fetch(cfg, days):
    """[(subject, text, mail_at_ist)] -- read-only."""
    out = []
    M = imaplib.IMAP4_SSL(cfg.get("imap_host") or "imap.gmail.com", timeout=40)
    try:
        M.login(cfg["user"], cfg["app_password"])
        typ, _ = M.select(_all_mail(M), readonly=True)
        if typ != "OK":
            M.select("INBOX", readonly=True)
        typ, data = M.uid("SEARCH", "X-GM-RAW", '"%s"' % (GMQ % days))
        uids = data[0].split() if typ == "OK" and data and data[0] else []
        for u in uids[-60:]:
            typ, md = M.uid("FETCH", u, "(BODY.PEEK[])")
            if typ != "OK" or not md or not isinstance(md[0], tuple):
                continue
            msg = email.message_from_bytes(md[0][1])
            try:
                when = parsedate_to_datetime(msg.get("Date")).astimezone(IST).strftime("%Y-%m-%d %H:%M")
            except Exception:                                          # noqa: BLE001
                when = ""
            out.append((_hdr(msg.get("Subject")), mail_text(msg), when))
    finally:
        try:
            M.logout()
        except Exception:                                              # noqa: BLE001
            pass
    return out


# ------------------------------------------------------------------------------------------------ one pass
def ensure(con):
    con.execute(SCHEMA)
    con.execute("CREATE INDEX IF NOT EXISTS online_booking_appt ON online_booking(appt_at)")


def write_state(st):
    try:
        tmp = STATE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False)
        os.replace(tmp, STATE)
    except Exception:                                                  # noqa: BLE001
        pass


def read_state():
    try:
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                  # noqa: BLE001
        return {}


def run(dry=False, mails=None, pusher=None):
    """One pass. mails= (for the walk) replaces the mailbox; pusher= replaces push(). Returns the state dict."""
    st = read_state()
    st.update({"version": VERSION, "last_run": now_ist().strftime("%Y-%m-%d %H:%M:%S")})
    try:
        if mails is None:
            with open(CFG, encoding="utf-8") as fh:
                cfg = json.load(fh)
            mails = fetch(cfg, LOOK_DAYS)
        found, unread, new, pushed = len(mails), 0, 0, 0
        rows = []
        for subj, text, when in mails:
            b = parse_mail(subj, text)
            if b is None:
                unread += 1
                continue
            b["mail_at"] = when
            rows.append(b)
        if dry:
            for b in rows:                                             # what was read -- yes/no only, never a value
                print("  mail %s: name %s . mobile %s . amount %s . time %s . %s" % (
                    (b["mail_at"] or "?")[:16], "yes" if b["name"] else "NO", "yes" if b["mobile"] else "NO",
                    "yes" if b["amount_p"] else "NO", "yes" if b["appt_at"] else "NO",
                    "outside timings" if b["out_of_hours"] else "inside timings"))
            print("DRY: %d mail(s) found, %d read as bookings, %d not readable; nothing written, nothing pushed" % (found, len(rows), unread))
            return {"found": found, "read": len(rows), "unreadable": unread}
        con = sqlite3.connect(DB, timeout=20)
        try:
            ensure(con)
            today = now_ist().strftime("%Y-%m-%d")
            for b in rows:
                if con.execute("SELECT 1 FROM online_booking WHERE payment_id=?", (b["payment_id"],)).fetchone():
                    continue
                b["clinic_ids"] = json.dumps(clinic_ids(b["mobile"], b["name"]), ensure_ascii=False)
                b["seen_at"] = now_ist().strftime("%Y-%m-%d %H:%M")
                con.execute("INSERT OR IGNORE INTO online_booking (payment_id, order_id, name, mobile, amount_p, appt_at, appt_raw, "
                            "out_of_hours, clinic_ids, mail_at, seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                            (b["payment_id"], b["order_id"], b["name"], b["mobile"], b["amount_p"], b["appt_at"], b["appt_raw"],
                             b["out_of_hours"], b["clinic_ids"], b["mail_at"], b["seen_at"]))
                con.commit()
                new += 1
                if (b["appt_at"] or today)[:10] >= today:
                    n, note = (pusher or push)(b)
                    pushed += 1 if n else 0
                    con.execute("UPDATE online_booking SET pushed=?, push_note=? WHERE payment_id=?", (1 if n else 0, note[:200], b["payment_id"]))
                    con.commit()
        finally:
            con.close()
        st.update({"last_ok": st["last_run"], "found": found, "read": len(rows), "unreadable": unread, "new": new,
                   "pushed": pushed, "error": ""})
        if new:
            log("%d mail(s), %d new booking(s), %d pushed, %d unreadable" % (found, new, pushed, unread))
    except Exception as e:                                             # noqa: BLE001 -- the page says so; the next pass tries again
        st["error"] = "%s: %s" % (type(e).__name__, str(e)[:160])
        log("ERROR %s" % st["error"])
    if not dry:
        write_state(st)
    return st


# ------------------------------------------------------------------------------------------------ the selftest
def _m(n):
    """A made-up mobile built at run time (the repository holds no number at all, F-185)."""
    return "9" + "%09d" % n


_FIX = [
    ("Pooja Test appointment at 11 Nov 2026 10:00 AM payment completed.",
     "Hi,\n\nInvoice No. :\n\nOrder Id : order_TestA1\n\nPatient Name : Pooja Test\n\nPatient Mobile : " + _m(1) + "\n\n"
     "Doctor Name : Manoj Agarwal\n\nPayment Amount : 600\n\nPayment ID : pay_TestA1\n",
     ("2026-11-11 10:00", 1, _m(1), 60000)),
    ("Ram appointment at 06 Oct 2026 18:35 PM payment completed.",
     "Order Id : order_B\nPatient Name : Ram\nPatient Mobile : +91 " + _m(2)[:5] + " " + _m(2)[5:] + "\nPayment Amount : 600.00\nPayment ID : pay_B2\n",
     ("2026-10-06 18:35", 1, _m(2), 60000)),
    ("Fwd: Sita appointment at 12 Oct 2026 07:15 PM payment completed.",
     "<p>Order Id : order_C</p><p>Patient Name : Sita</p><p>Patient Mobile : " + _m(3) + "</p><p>Payment Amount : 600</p>"
     "<p>Payment ID : pay_C3</p>", ("2026-10-12 19:15", 0, _m(3), 60000)),
    ("Gita appointment at 15 Nov 2026 11:00 AM payment completed.",
     "Patient Name : Gita\nPatient Mobile : " + _m(4) + "\nPayment Amount : 600\nPayment ID : pay_D4\n", ("2026-11-15 11:00", 1, _m(4), 60000)),
    ("Hari appointment at 14 Nov 2026 01:30 PM payment completed.",
     "Patient Name : Hari\nPatient Mobile : " + _m(5) + "\nPayment Amount : 600\nPayment ID : pay_E5\n", ("2026-11-14 13:30", 0, _m(5), 60000)),
    ("Docterz newsletter", "Hello doctor, nothing to pay here.", None),
]


def selftest():
    bad = 0
    for subj, body, want in _FIX:
        got = parse_mail(subj, mail_text(email.message_from_string(
            "Subject: x\nContent-Type: text/%s; charset=utf-8\n\n%s" % ("html" if body.startswith("<") else "plain", body))))
        g = None if got is None else (got["appt_at"], got["out_of_hours"], got["mobile"], got["amount_p"])
        ok = g == want
        bad += 0 if ok else 1
        print("%s %s -> %s" % ("ok " if ok else "BAD", subj[:40], g))
    print("SELFTEST %s" % ("OK" if not bad else "FAILED (%d)" % bad))
    return bad == 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a:
        sys.exit(0 if selftest() else 1)
    r = run(dry="--dry" in a)
    sys.exit(0 if not r.get("error") else 1)
