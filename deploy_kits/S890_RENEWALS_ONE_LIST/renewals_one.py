#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""renewals_one.py -- S890_RENEWALS_ONE_LIST (D1017, 18-Nov-2026): every renewal on ONE list on the server.

Lives in /root/assetapp beside asset_register.py and is mounted from its foot by a guarded block (the S571 pattern): absent or
broken, the scan app runs exactly as before. Tables in the scan app's own assets.db (renewal_item, renewal_mail, renewal_nag).

What it gives the /renewals page (jinja globals, each wrapped so an error draws nothing, never a broken page):
  s890_top(show_all)    -- "Found in your mail" (only when there is something) + "Licences, documents and subscriptions"
  s890_staff(show_all)  -- "Staff documents" (the expiries rows of entity 'staff', which never reached the page before: F-1493)
Doors (all under the scan app, so /scanapp/renewals/one/... on the box):
  POST /renewals/one/add            the owner (any group) or a manager (Clinic / NK Pathology / Civic only)
  POST /renewals/one/renewed/<id>   Mark renewed: the old row closed (history kept), a new row opened with the new date
  POST /renewals/one/mail/<id>/<a>  a = apply | add | ignore -- the one tap that changes a date from a mail
  GET  /renewals/one/api/count      {"ok":true,"n":due-or-overdue}  for the home tile's red count (soft: not signed in -> n null)
  GET  /renewals/one/api/due        TOKEN: today's due list + the mail's subject and text (the Janitor sends it at 08:42)
  POST /renewals/one/api/due/sent   TOKEN: the Janitor says it sent -> the cadence remembers today
  POST /renewals/one/api/mail       TOKEN: the Janitor's feeder posts a renewal-type mail (sender, subject, date, excerpt ...)
  POST /renewals/one/api/seed       TOKEN: the one-time seed from the Janitor's typed lists; refused once seeded rows exist
The token: the environment's FINANCE_RENEWALS_TOKEN, else the file beside this module named by TOKEN_FILE (0600, written by the
installer from the finance service's own setting). No token anywhere -> every token door answers 503 (fail closed, F-84).
Numbers: any run of 5+ digits (and a vehicle registration) is cut to its last 4 BEFORE storing -- in names, notes, mail excerpts.
The health page's Renewals row keeps reading /root/finance/renewals_state.json: this module now writes that file from the one
list (at every change, at every due-list read, and by the installer's cron) -- finance_app.py is not touched.
Lead times (his rulings, D689 / D713 / S487): passport 365 days; vehicle insurance 30; PUC 7; RC 45; arms licence 45; else 45.
Cadence of the mail (as Renewal_Nag v4): inside 7 days daily; inside 21 every 3 days; inside the lead time weekly; a passport
between 365 and 45 days once a month; overdue kept 45 days past the expiry.

CLI (the installer and the walk):  --ensure <assets.db> | --state <assets.db> [<state.json>] | --selfcheck
"""
import datetime
import hmac
import json
import os
import re
import sqlite3
import sys

VERSION = "S890"
AR = None                       # the asset app's module, handed in by init()
MOUNTED = False
TODAY = None                    # the walk sets a made-up day here (an ISO string)
TOKEN_FILE = "renewals_one.token"
STATE_FILE = os.environ.get("FINANCE_RENEWALS_STATE", "/root/finance/renewals_state.json")
GROUPS = ("Clinic", "NK Pathology", "Personal", "Vehicle", "Civic")
OWNER_ONLY = {"Personal", "Vehicle"}
EVERY = ((12, "1 year"), (6, "6 months"), (24, "2 years"), (60, "5 years"), (120, "10 years"), (180, "15 years"), (240, "20 years"), (0, "Once"))
DEFAULT_REMIND, PASSPORT_REMIND, VEH_INS_REMIND, PUC_REMIND, RC_REMIND = 45, 365, 30, 7, 45
URGENT_DAYS, CLOSE_DAYS, EVERY_DAYS, WEEKLY_DAYS, PASSPORT_EARLY_EVERY, OVERDUE_KEEP = 7, 21, 3, 7, 30, 45
STATE_WINDOW, STATE_KEEP = 50, 45             # what the health row's file carries (as the Janitor's push did)
PAGE_QUIET_DAYS = 60                          # the page without "show all": items inside their lead time or 60 days
EXCERPT_MAX, ATTACH_MAX, SUBJECT_MAX, WHAT_MAX, NOTE_MAX = 1500, 400, 200, 120, 300
MAIL_WORDS = ("renew", "policy", "licence", "license", "subscription", "domain", "valid till", "valid upto", "valid up to",
              "expiry", "expires", "expiring", "due date", "registration", "insurance", "premium", "membership")

DDL = (
    """CREATE TABLE IF NOT EXISTS renewal_item(
         id INTEGER PRIMARY KEY, what TEXT NOT NULL, grp TEXT NOT NULL, expires_on TEXT NOT NULL,
         remind_days INTEGER NOT NULL DEFAULT 45, every_months INTEGER NOT NULL DEFAULT 12,
         note TEXT NOT NULL DEFAULT '', last4 TEXT NOT NULL DEFAULT '', source TEXT NOT NULL DEFAULT 'typed',
         closed INTEGER NOT NULL DEFAULT 0, closed_at TEXT, renewed_on TEXT, replaced_by INTEGER,
         created_at TEXT NOT NULL DEFAULT (datetime('now')), created_by TEXT NOT NULL DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS renewal_mail(
         id INTEGER PRIMARY KEY, mail_key TEXT NOT NULL UNIQUE, received_at TEXT NOT NULL DEFAULT '', sender TEXT NOT NULL DEFAULT '',
         subject TEXT NOT NULL DEFAULT '', excerpt TEXT NOT NULL DEFAULT '', attachments TEXT NOT NULL DEFAULT '',
         link TEXT NOT NULL DEFAULT '', date_found TEXT, words TEXT NOT NULL DEFAULT '', item_id INTEGER, score INTEGER NOT NULL DEFAULT 0,
         status TEXT NOT NULL DEFAULT 'open', decided_at TEXT, decided_by TEXT NOT NULL DEFAULT '',
         posted_at TEXT NOT NULL DEFAULT (datetime('now')))""",
    """CREATE TABLE IF NOT EXISTS renewal_nag(item_id INTEGER PRIMARY KEY, last_nag_on TEXT NOT NULL)""",
    "CREATE INDEX IF NOT EXISTS renewal_item_open ON renewal_item(closed, expires_on)",
)
TABLES = ("renewal_item", "renewal_mail", "renewal_nag")

_DIGITS = re.compile(r"\d{5,}")
_GROUPED = re.compile(r"\b\d{4}(?:[ -]\d{4}){2,}\b")                         # a number printed in blocks of four (Aadhaar, a card); never a date
_REG = re.compile(r"\b([A-Z]{2})[ -]?(\d{1,2})[ -]?([A-Z]{1,3})[ -]?(\d{4})\b")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_MONTHS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}
_DATE_WORDS = re.compile(r"(\d{1,2})[-/. ]([A-Za-z]{3,9}|\d{1,2})[-/. ](\d{4})")
_DATE_ISO = re.compile(r"(\d{4})-(\d{2})-(\d{2})")


# ------------------------------------------------------------------------------------------------------------- small helpers
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))        # his time zone; the service runs in UTC


def now_ist():
    return datetime.datetime.now(IST).replace(tzinfo=None)


def today():
    if TODAY:
        return datetime.date.fromisoformat(TODAY)
    return now_ist().date()


def now_s():
    return now_ist().strftime("%Y-%m-%d %H:%M:%S")


def mask(s):
    """Any run of 5+ digits -> '…' + its last 4; a vehicle registration (UP25AB1234) -> '…1234'. Idempotent."""
    s = str(s or "")
    s = _REG.sub(lambda m: "…" + m.group(4), s)
    s = _GROUPED.sub(lambda m: "…" + re.sub(r"\D", "", m.group(0))[-4:], s)
    return _DIGITS.sub(lambda m: "…" + m.group(0)[-4:], s)


def last4(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d[-4:] if d else ""


def iso_ok(s):
    try:
        return bool(_ISO.match(str(s or ""))) and datetime.date.fromisoformat(s) is not None
    except ValueError:
        return False


def add_months(d, months):
    m = d.month - 1 + months
    y, m = d.year + m // 12, m % 12 + 1
    last = [31, 29 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]
    return datetime.date(y, m, min(d.day, last))


def dates_in(text):
    """Every date written in a text, as ISO, in order of appearance (dd-Mon-yyyy, dd/mm/yyyy, yyyy-mm-dd)."""
    out = []
    for m in _DATE_ISO.finditer(text or ""):
        try:
            out.append(datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3))).isoformat())
        except ValueError:
            pass
    for m in _DATE_WORDS.finditer(text or ""):
        mon = int(m.group(2)) if m.group(2).isdigit() else _MONTHS.get(m.group(2)[:3].lower())
        if not mon:
            continue
        try:
            out.append(datetime.date(int(m.group(3)), mon, int(m.group(1))).isoformat())
        except ValueError:
            pass
    seen, res = set(), []
    for d in out:
        if d not in seen:
            seen.add(d)
            res.append(d)
    return res


def remind_for(what, grp, note=""):
    """His lead times: a passport 365; vehicle insurance 30; PUC 7; RC 45; everything else (the arms licence too) 45."""
    t = ("%s %s" % (what, note)).lower()
    if "passport" in t:
        return PASSPORT_REMIND
    if grp == "Vehicle" or re.search(r"\b(vento|carnival|kia|tvs|honda|aviator|car|scooter|bike|vehicle)\b", t):
        if re.search(r"\bpuc\b|pollution", t):
            return PUC_REMIND
        if re.search(r"\brc\b|registration", t):
            return RC_REMIND
        if "insurance" in t or "policy" in t:
            return VEH_INS_REMIND
    return DEFAULT_REMIND


def every_word(months):
    return dict(EVERY).get(int(months or 0), "%d months" % int(months or 0))


def dmy(iso):
    try:
        if AR is not None and hasattr(AR, "_s559_dmy"):
            return AR._s559_dmy(iso)
        return datetime.date.fromisoformat(str(iso)[:10]).strftime("%d-%m-%Y")
    except Exception:                                                # noqa: BLE001
        return str(iso or "")


def esc(s):
    return (str(s if s is not None else "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


# ------------------------------------------------------------------------------------------------------------- the data
def ensure(db):
    for ddl in DDL:
        db.execute(ddl)
    db.commit()
    return TABLES


def ensure_path(path):
    db = sqlite3.connect(path, timeout=20)
    try:
        ensure(db)
        n = db.execute("SELECT COUNT(*) FROM renewal_item WHERE closed=0").fetchone()[0]
    finally:
        db.close()
    return TABLES, n


def ensure_at_mount(path):
    try:
        ensure_path(path)
    except sqlite3.Error as ex:
        print("renewals_one: tables not ensured: %s" % ex, file=sys.stderr)


def _role():
    try:
        from flask import g
        return g.user["role"] or ""
    except Exception:                                                # noqa: BLE001
        return ""


def _who():
    try:
        from flask import g
        return str(g.user["display_name"] or g.user["username"] or "")[:60]
    except Exception:                                                # noqa: BLE001
        return ""


def groups_for(role):
    return list(GROUPS) if role == "owner" else [g for g in GROUPS if g not in OWNER_ONLY]


def may_edit(role, grp):
    return role == "owner" or (role == "manager" and grp not in OWNER_ONLY)


def days_left(iso, on=None):
    return (datetime.date.fromisoformat(iso) - (on or today())).days


def state_of(days, remind):
    if days < 0:
        return "red"
    if days <= remind:
        return "amber"
    return ""


def open_items(db, role="owner"):
    gs = groups_for(role)
    q = "SELECT * FROM renewal_item WHERE closed=0 AND grp IN (%s) ORDER BY expires_on, what" % ",".join("?" * len(gs))
    return db.execute(q, gs).fetchall()


def add_item(db, what, grp, expires_on, remind_days=None, every_months=12, note="", number="", source="typed", who=""):
    what = mask(str(what or "").strip())[:WHAT_MAX]
    note = mask(str(note or "").strip())[:NOTE_MAX]
    if not what:
        raise ValueError("what is empty")
    if grp not in GROUPS:
        raise ValueError("unknown group")
    if not iso_ok(expires_on):
        raise ValueError("expires_on is not a date")
    try:
        every_months = int(every_months or 0)
    except (TypeError, ValueError):
        every_months = 12
    rd = int(remind_days) if remind_days not in (None, "", 0, "0") else remind_for(what, grp, note)
    l4 = last4(number)
    cur = db.execute("INSERT INTO renewal_item(what,grp,expires_on,remind_days,every_months,note,last4,source,created_by) "
                     "VALUES(?,?,?,?,?,?,?,?,?)", (what, grp, expires_on, rd, every_months, note, l4, source, who))
    return cur.lastrowid


def renew_item(db, item_id, new_expiry, who="", new_last4=None, source="typed", renewed_on=None):
    """Mark renewed: the old row is CLOSED (history), a new row opens with the new date. Returns the new id."""
    r = db.execute("SELECT * FROM renewal_item WHERE id=? AND closed=0", (item_id,)).fetchone()
    if r is None:
        raise ValueError("no such open item")
    if not iso_ok(new_expiry):
        raise ValueError("new expiry is not a date")
    if new_expiry < today().isoformat():
        raise ValueError("the new date is in the past")
    l4 = last4(new_last4) if new_last4 else r["last4"]
    cur = db.execute("UPDATE renewal_item SET closed=1, closed_at=?, renewed_on=? WHERE id=? AND closed=0",
                     (now_s(), renewed_on or today().isoformat(), item_id))
    if cur.rowcount != 1:
        raise ValueError("already renewed")                          # a second tap in flight: the first one won
    cur = db.execute("INSERT INTO renewal_item(what,grp,expires_on,remind_days,every_months,note,last4,source,created_by) "
                     "VALUES(?,?,?,?,?,?,?,?,?)",
                     (r["what"], r["grp"], new_expiry, r["remind_days"], r["every_months"], r["note"], l4, source, who))
    nid = cur.lastrowid
    db.execute("UPDATE renewal_item SET replaced_by=? WHERE id=?", (nid, item_id))
    db.execute("DELETE FROM renewal_nag WHERE item_id=?", (item_id,))
    return nid


def next_expiry(r, date_found=None):
    """The date Apply pre-fills: the date read in the mail when it is later than today's expiry, else one cycle on."""
    if date_found and iso_ok(date_found) and date_found > r["expires_on"]:
        return date_found
    if not int(r["every_months"] or 0):
        return r["expires_on"]                                       # 'Once': nothing to pre-fill
    d = datetime.date.fromisoformat(r["expires_on"])
    return add_months(d, int(r["every_months"])).isoformat()


# ------------------------------------------------------------------------------------------------------------- the due list
def due_rows(db, on=None):
    """[(row, days)] of every open item inside its lead time or up to OVERDUE_KEEP days past -- the 08:42 mail's list."""
    on = on or today()
    out = []
    for r in db.execute("SELECT * FROM renewal_item WHERE closed=0 ORDER BY expires_on, what"):
        d = days_left(r["expires_on"], on)
        if d <= int(r["remind_days"]) and d >= -OVERDUE_KEEP:
            out.append((r, d))
    out.sort(key=lambda x: (x[1], x[0]["what"]))
    return out


def gap_for(days, remind):
    if days <= URGENT_DAYS:
        return 1
    if days <= CLOSE_DAYS:
        return EVERY_DAYS
    if days <= DEFAULT_REMIND:
        return WEEKLY_DAYS
    return PASSPORT_EARLY_EVERY if remind > DEFAULT_REMIND else WEEKLY_DAYS


def due_list(db, on=None):
    """The due list with the cadence applied: each item says whether the mail should carry it TODAY."""
    on = on or today()
    nags = {r["item_id"]: r["last_nag_on"] for r in db.execute("SELECT * FROM renewal_nag")}
    items, nag_now = [], False
    for r, d in due_rows(db, on):
        gap = gap_for(d, int(r["remind_days"]))
        last = nags.get(r["id"])
        since = (on - datetime.date.fromisoformat(last)).days if last else 999
        nag = since >= gap
        nag_now = nag_now or nag
        items.append({"id": r["id"], "what": r["what"], "group": r["grp"], "expires_on": r["expires_on"], "days": d,
                      "remind_days": int(r["remind_days"]), "last4": r["last4"], "note": r["note"], "nag_today": nag})
    return items, nag_now


def mail_text(items, on=None):
    on = on or today()
    if not items:
        return "", ""
    lines = []
    for x in items:
        d = x["days"]
        when = ("OVERDUE — expired %d day(s) ago (%s)" % (-d, dmy(x["expires_on"])) if d < 0
                else "EXPIRES TODAY (%s)" % dmy(x["expires_on"]) if d == 0
                else "expires in %d day(s) (%s)" % (d, dmy(x["expires_on"])))
        lines.append("• %s — %s%s%s" % (when, x["what"], (" · …%s" % x["last4"]) if x["last4"] else "",
                                                  ("\n    " + x["note"]) if x["note"] else ""))
    worst = items[0]
    subject = ("OVERDUE RENEWAL: " if worst["days"] < 0 else "RENEWAL DUE: ") + worst["what"][:60] + \
              (" (+%d more)" % (len(items) - 1) if len(items) > 1 else "")
    text = ("Today's renewals, from the clinic server's one list (%s):\n\n%s\n\n"
            "Renewed? Open the Renewals page and tap Mark renewed on the row -- that is what silences this.\n"
            "https://followup.dr-manoj.in/scanapp/renewals\n— Renewal nag (Inbox Janitor, S890)" % (dmy(on.isoformat()), "\n".join(lines)))
    return subject, text


def mark_sent(db, ids, on=None):
    on = (on or today()).isoformat()
    n = 0
    for i in ids:
        try:
            i = int(i)
        except (TypeError, ValueError):
            continue
        db.execute("INSERT OR REPLACE INTO renewal_nag(item_id,last_nag_on) VALUES(?,?)", (i, on))
        n += 1
    db.commit()
    return n


def count_due(db, role="owner", on=None):
    on = on or today()
    n = 0
    for r in open_items(db, role):
        if days_left(r["expires_on"], on) <= int(r["remind_days"]):
            n += 1
    return n


# ------------------------------------------------------------------------------------------------------------- the health file
def state_items(db, on=None):
    on = on or today()
    out = []
    for r in db.execute("SELECT * FROM renewal_item WHERE closed=0 ORDER BY expires_on, what"):
        d = days_left(r["expires_on"], on)
        if d <= STATE_WINDOW and d >= -STATE_KEEP:
            alert = (datetime.date.fromisoformat(r["expires_on"]) - datetime.timedelta(days=int(r["remind_days"]))).isoformat()
            out.append({"vendor": r["what"][:120], "dateISO": alert, "expiryISO": r["expires_on"], "note": ""})
    return out


def write_state(db, path=None, on=None):
    """The file the finance health page reads (its push door wrote it until now). Written atomically; a missing folder = nothing."""
    path = path or STATE_FILE
    if not os.path.isdir(os.path.dirname(path) or "."):
        return False
    if not db.execute("SELECT 1 FROM renewal_item WHERE closed=0 LIMIT 1").fetchone():
        return False                                                 # before the seed the Janitor's own push file stands
    state = {"received_at": now_ist().isoformat(timespec="seconds"), "window_days": DEFAULT_REMIND,
             "items": state_items(db, on), "source": "renewals_one %s" % VERSION}
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)
    os.replace(tmp, path)
    return True


def _state_quiet(db):
    try:
        write_state(db)
    except Exception as ex:                                          # noqa: BLE001
        print("renewals_one: state file not written: %s" % ex, file=sys.stderr)


# ------------------------------------------------------------------------------------------------------------- mail intake
def match_item(db, subject, excerpt, sender=""):
    """The open item a mail seems to speak of: its last 4 in the text (strong), its name's words (weak). (item_id, score) or (None, 0)."""
    text = ("%s %s %s" % (subject, excerpt, sender)).lower()
    digits = set(re.findall(r"\d{4}", text))
    best, best_s = None, 0
    for r in db.execute("SELECT * FROM renewal_item WHERE closed=0"):
        s = 0
        if r["last4"] and r["last4"] in digits:
            s += 5
        for w in re.findall(r"[a-z][a-z0-9.\-]{2,}", r["what"].lower()):
            if w in ("renewal", "insurance", "licence", "license", "the", "and", "for", "annual", "membership", "x2"):
                continue
            if w in text:
                s += 2 if len(w) > 5 else 1
        if s > best_s:
            best, best_s = r["id"], s
    return (best, best_s) if best_s >= 2 else (None, best_s)


def intake_mail(db, p):
    """One renewal-type mail from the feeder. Stored once (mail_key); numbers cut; a match proposed, never applied. Returns the row id or None."""
    key = str(p.get("mail_key") or p.get("id") or "").strip()[:120]
    if not key:
        raise ValueError("mail_key missing")
    if db.execute("SELECT 1 FROM renewal_mail WHERE mail_key=?", (key,)).fetchone():
        return None
    subject = mask(str(p.get("subject") or ""))[:SUBJECT_MAX]
    excerpt = mask(str(p.get("excerpt") or p.get("body") or ""))[:EXCERPT_MAX]
    sender = mask(str(p.get("sender") or p.get("from") or ""))[:160]
    att = p.get("attachments") or []
    if isinstance(att, str):
        att = [att]
    att = json.dumps([mask(str(a))[:80] for a in att][:10], ensure_ascii=False)[:ATTACH_MAX]
    link = str(p.get("link") or "")[:300]
    if link and not link.startswith("https://mail.google.com/"):
        link = ""
    received = str(p.get("received_at") or p.get("date") or "")[:25]
    found = [d for d in dates_in("%s %s" % (subject, excerpt)) if d >= today().isoformat()]
    date_found = p.get("date_found") if iso_ok(p.get("date_found") or "") else (max(found) if found else None)   # the latest: 'valid till'

    words = ", ".join(w for w in MAIL_WORDS if w in ("%s %s" % (subject, excerpt)).lower())[:200]
    item_id, score = match_item(db, subject, excerpt, sender)
    cur = db.execute("INSERT OR IGNORE INTO renewal_mail(mail_key,received_at,sender,subject,excerpt,attachments,link,date_found,words,item_id,score) "
                     "VALUES(?,?,?,?,?,?,?,?,?,?,?)", (key, received, sender, subject, excerpt, att, link, date_found, words, item_id, score))
    return cur.lastrowid if cur.rowcount == 1 else None


def decide_mail(db, mail_id, action, who="", new_expiry=None, grp=None, what=None):
    m = db.execute("SELECT * FROM renewal_mail WHERE id=? AND status='open'", (mail_id,)).fetchone()
    if m is None:
        raise ValueError("no such open mail")
    if action == "ignore":
        st = "ignored"
    elif action == "apply":
        if not m["item_id"]:
            raise ValueError("no matched item to apply to")
        r = db.execute("SELECT * FROM renewal_item WHERE id=? AND closed=0", (m["item_id"],)).fetchone()
        if r is None:
            raise ValueError("the matched item is no longer open")
        renew_item(db, r["id"], new_expiry if iso_ok(new_expiry or "") else next_expiry(r, m["date_found"]), who=who, source="mail")
        st = "applied"
    elif action == "add":
        exp = new_expiry if iso_ok(new_expiry or "") else (m["date_found"] or add_months(today(), 12).isoformat())
        add_item(db, what or m["subject"][:WHAT_MAX], grp if grp in GROUPS else "Clinic", exp, note="from a mail of %s" % m["received_at"][:10],
                 source="mail", who=who)
        st = "added"
    else:
        raise ValueError("unknown action")
    db.execute("UPDATE renewal_mail SET status=?, decided_at=?, decided_by=? WHERE id=?", (st, now_s(), who, mail_id))
    return st


# ------------------------------------------------------------------------------------------------------------- the seed
def seed_rows(db, rows, who="seed"):
    """The Janitor's typed lists, once. Each row: what, group, expires_on (or dateISO/expiryISO/note as the script had them),
    every_months, note, number. Refused when seeded rows already exist. Returns the number added."""
    if db.execute("SELECT COUNT(*) FROM renewal_item WHERE source='seeded'").fetchone()[0]:
        raise ValueError("already seeded")
    n = 0
    for p in rows:
        if not isinstance(p, dict):
            continue
        what = str(p.get("what") or p.get("vendor") or p.get("title") or "").strip()
        what = re.sub(r"^ANNUAL:\s*", "", what)
        what = re.sub(r"\s*\(\s*[^)]*\d[^)]*\)", "", what).strip()
        if not what:
            continue
        exp = p.get("expires_on") or p.get("expiryISO") or ""
        if not iso_ok(exp):
            found = [d for d in dates_in(str(p.get("note") or "")) if d >= str(p.get("dateISO") or "")]
            exp = found[0] if found else (p.get("dateISO") or p.get("firstISO") or "")
        if not iso_ok(exp):
            continue
        grp = p.get("group") if p.get("group") in GROUPS else guess_group(what, str(p.get("note") or ""))
        every = p.get("every_months", p.get("cycleMonths", 12))
        try:
            every = int(every or 12)
        except (TypeError, ValueError):
            every = 12
        number = p.get("number") or p.get("last4") or ""
        if not number:
            m = re.search(r"\((?:[^)]*?)(\d{4,})\)", str(p.get("vendor") or p.get("title") or ""))
            number = m.group(1) if m else ""
        add_item(db, what, grp, exp, every_months=every, note=p.get("note") or "", number=number, source="seeded", who=who)
        n += 1
    db.commit()
    return n


def guess_group(what, note=""):
    t = ("%s %s" % (what, note)).lower()
    if re.search(r"\b(vento|carnival|kia|tvs|honda|aviator|\brc\b|puc|registration \(rc\))", t):
        return "Vehicle"
    if re.search(r"passport|\bdl\b|driving|arms licence|arms license|health insurance|mediclaim|club membership", t):
        return "Personal"
    if re.search(r"nagar nigam|municipal|civic", t):
        return "Civic"
    if re.search(r"marg|nk pathology|pathology|agilus", t):
        return "NK Pathology"
    return "Clinic"


# ------------------------------------------------------------------------------------------------------------- the pages
def _badge(days, remind):
    st = state_of(days, remind)
    if days < 0:
        return '<span class="badge red">overdue %d d</span>' % -days
    if st == "amber":
        return '<span class="badge amber">%d days</span>' % days
    return '<span class=muted>%d days</span>' % days


def _row_class(days, remind):
    return state_of(days, remind)


def _renew_form(r, action_url, extra=""):
    nxt = next_expiry(r)
    return ('<details class="s890d"><summary class="btn small">Mark renewed</summary>'
            '<form method=post action="%s" class="s890f">%s<label>Renewed — new expiry <input type=date name=new_expiry value="%s" required></label> '
            '<label>New number, last 4 (if changed) <input name=number maxlength=12 placeholder="%s" style="width:7em"></label> '
            '<button class="btn small" type=submit>Save</button></form></details>' % (esc(action_url), extra, esc(nxt), esc(r["last4"])))


def section_top(show_all=False):
    db = AR.get_db()
    role = _role()
    on = today()
    gs = groups_for(role)
    base = AR.url_for("renewals")
    parts = []
    # --- Found in your mail (only when there is something) ---
    mails = db.execute("SELECT * FROM renewal_mail WHERE status='open' ORDER BY received_at DESC, id DESC LIMIT 20").fetchall()
    items = {r["id"]: r for r in db.execute("SELECT * FROM renewal_item WHERE closed=0")}
    if role != "owner":                                              # a manager: only a mail matched to a row of his groups (his personal Gmail stays his)
        mails = [m for m in mails if m["item_id"] in items and items[m["item_id"]]["grp"] in gs]
    if mails:
        h = ['<div class=card id=s890mail><h3 style="color:#1f3864">Found in your mail <span class=muted>(%d to look at)</span></h3>'
             '<p class=muted>Nothing changes until you tap. A mail once answered is never shown again.</p>' % len(mails)]
        for m in mails:
            it = items.get(m["item_id"]) if m["item_id"] else None
            looks = (" · looks like <b>%s</b> (expires %s)" % (esc(it["what"]), esc(dmy(it["expires_on"])))) if it else " · no row matched"
            found = (" · a date read in the mail: <b>%s</b>" % esc(dmy(m["date_found"]))) if m["date_found"] else " · no full date read"
            try:
                att = json.loads(m["attachments"] or "[]")
            except ValueError:
                att = []
            pre = esc(next_expiry(it, m["date_found"])) if it else esc(m["date_found"] or add_months(on, 12).isoformat())
            h.append('<div class="s890m" id="s890m%d"><div><b>%s</b>%s<br><span class=muted>%s · %s%s</span></div>'
                     % (m["id"], esc(m["subject"] or "(no subject)"), looks, esc(m["sender"] or "unknown sender"), esc(m["received_at"][:16] or "date unknown"), found))
            h.append('<details><summary class="btn small">Show mail · why this?</summary><div class="s890why">'
                     '<div class=muted>Why it was picked up: %s%s</div>'
                     '<pre class="s890pre">%s</pre>%s%s</div></details>'
                     % (esc("words found: " + (m["words"] or "none")),
                        (" · the row's last 4 (…%s) is in the mail" % esc(it["last4"])) if (it and it["last4"] and it["last4"] in re.sub(r"\D", " ", m["subject"] + " " + m["excerpt"])) else "",
                        esc(m["excerpt"] or "(no text)"),
                        ("<div class=muted>Attachments: %s</div>" % esc(", ".join(att))) if att else "",
                        ('<div><a href="%s" target=_blank rel=noopener>Open in Gmail ↗</a></div>' % esc(m["link"])) if m["link"] else
                        "<div class=muted>No Gmail link came with this mail.</div>"))
            h.append('<form method=post action="%s/one/mail/%d/apply" class="s890f">%s<button class="btn small" type=submit%s>Apply</button> '
                     '<label>new expiry <input type=date name=new_expiry value="%s"></label></form>'
                     % (esc(base), m["id"], "", "" if (it and may_edit(role, it["grp"])) else " disabled title=\"no matched row\"", pre))
            h.append('<form method=post action="%s/one/mail/%d/add" class="s890f"><button class="btn small" type=submit>Add as new</button> '
                     '<select name=grp>%s</select> <label>expires <input type=date name=new_expiry value="%s"></label> '
                     '<input name=what placeholder="what (as it should read)" maxlength=120 style="width:16em"></form>'
                     % (esc(base), m["id"], "".join('<option>%s</option>' % g for g in gs), esc(m["date_found"] or add_months(on, 12).isoformat())))
            h.append('<form method=post action="%s/one/mail/%d/ignore" class="s890f"><button class="btn small" type=submit>Not a renewal</button></form></div>'
                     % (esc(base), m["id"]))
        h.append("</div>")
        parts.append("".join(h))
    # --- Licences, documents and subscriptions ---
    rows = open_items(db, role)
    shown, hidden = [], 0
    for r in rows:
        d = days_left(r["expires_on"], on)
        if show_all or d <= max(int(r["remind_days"]), PAGE_QUIET_DAYS):
            shown.append((r, d))
        else:
            hidden += 1
    shown.sort(key=lambda x: (x[1], x[0]["what"]))
    h = ['<div class=card id=s890list><h3 style="color:#1f3864">Licences, documents and subscriptions <span class=muted>(%d%s)</span></h3>'
         % (len(rows), "" if show_all else ", by days left")]
    h.append('<details class="s890d" id=s890add><summary class="btn small">+ Add renewal</summary>'
             '<form method=post action="%s/one/add" class="s890f s890add">'
             '<label>What <input name=what maxlength=120 required style="width:18em"></label> '
             '<label>Group <select name=grp>%s</select></label> '
             '<label>Expires on <input type=date name=expires_on required></label> '
             '<label>Repeats every <select name=every_months>%s</select></label> '
             '<label>Remind before <select name=remind_days><option value="">by rule (45 d; passport 365; vehicle insurance 30; PUC 7)</option>'
             '<option value=45>45 days</option><option value=30>30 days</option><option value=7>7 days</option><option value=365>365 days</option></select></label> '
             '<label>Number — last 4 only <input name=number maxlength=12 style="width:7em"></label> '
             '<label>Note <input name=note maxlength=300 style="width:22em"></label> '
             '<button class="btn small" type=submit>Save</button></form></details>'
             % (esc(base), "".join('<option>%s</option>' % g for g in gs),
                "".join('<option value=%d%s>%s</option>' % (m, " selected" if m == 12 else "", w) for m, w in EVERY)))
    if shown:
        h.append("<table><tr><th>Days left</th><th>What</th><th>Group</th><th>Expires on</th><th>Every</th><th></th></tr>")
        for r, d in shown:
            h.append('<tr class="%s"><td>%s</td><td>%s%s</td><td class=muted>%s</td><td>%s</td><td class=muted>%s</td><td>%s</td></tr>'
                     % (_row_class(d, int(r["remind_days"])), _badge(d, int(r["remind_days"])), esc(r["what"]),
                        (' <span class=muted>· …%s</span>' % esc(r["last4"])) if r["last4"] else "",
                        esc(r["grp"]), esc(dmy(r["expires_on"])), esc(every_word(r["every_months"])),
                        _renew_form(r, "%s/one/renewed/%d" % (base, r["id"])) if may_edit(role, r["grp"]) else ""))
        h.append("</table>")
    else:
        h.append("<p class=muted>%s</p>" % ("No renewal on the list yet — the seed has not run." if not rows else "Nothing inside 60 days."))
    if hidden and not show_all:
        h.append('<p class=muted>… %d more beyond 60 days · <a href="%s">show all upcoming</a></p>' % (hidden, esc(AR.url_for("renewals", all=1))))
    h.append("</div>")
    parts.append("".join(h))
    return CSS + "".join(parts)


def section_staff(show_all=False):
    db = AR.get_db()
    on = today()
    rows = db.execute("SELECT e.id eid, e.label, e.due_date, e.threshold_days, s.id sid, s.name sname FROM expiries e "
                      "JOIN staff s ON e.entity='staff' AND s.id=e.entity_id WHERE e.resolved=0 AND s.hidden=0 ORDER BY e.due_date").fetchall()
    out = []
    for r in rows:
        try:
            d = days_left(str(r["due_date"])[:10], on)
        except ValueError:
            continue
        if show_all or d <= max(int(r["threshold_days"] or 45), PAGE_QUIET_DAYS):
            out.append((r, d))
    if not out:
        return ""
    h = ['<div class=card id=s890staff><h3 style="color:#1f3864">Staff documents <span class=muted>(%d)</span></h3>'
         '<table><tr><th>Days left</th><th>Who · what</th><th>Expires on</th><th></th></tr>' % len(out)]
    for r, d in out:
        try:
            href = AR.url_for("staff_view", sid=r["sid"])
        except Exception:                                            # noqa: BLE001
            href = "#"
        h.append('<tr class="%s"><td>%s</td><td><a href="%s">%s</a> — %s</td><td>%s</td><td><a class="btn small" href="%s">Open</a></td></tr>'
                 % (_row_class(d, int(r["threshold_days"] or 45)), _badge(d, int(r["threshold_days"] or 45)), esc(href), esc(r["sname"]),
                    esc(r["label"]), esc(dmy(r["due_date"])), esc(href)))
    h.append("</table></div>")
    return "".join(h)


CSS = """<style>
.s890f{display:inline-flex;flex-wrap:wrap;gap:8px;align-items:center;margin:6px 8px 2px 0;font-size:13px}
.s890f label{font-size:12px;color:#5b6b7b}.s890f input,.s890f select{font:inherit;padding:3px 6px;border:1px solid #cfd8e3;border-radius:6px}
.s890d summary{display:inline-block;list-style:none;cursor:pointer}.s890d summary::-webkit-details-marker{display:none}
.s890m{border-top:1px solid #e4e9ef;padding:10px 0}.s890m:first-of-type{border-top:0}
.s890why{background:#f6f8fb;border:1px solid #e4e9ef;border-radius:8px;padding:8px 10px;margin:6px 0;font-size:13px}
.s890pre{white-space:pre-wrap;font:12.5px/1.5 ui-monospace,Consolas,monospace;background:#fff;border-radius:6px;padding:8px;max-height:16em;overflow:auto}
</style>"""


def _wrap(fn):
    def w(*a, **k):
        try:
            from markupsafe import Markup
            return Markup(fn(*a, **k))
        except Exception as ex:                                      # noqa: BLE001
            print("renewals_one %s: %s" % (fn.__name__, ex), file=sys.stderr)
            return ""
    return w


# ------------------------------------------------------------------------------------------------------------- the doors
def _token():
    t = os.environ.get("FINANCE_RENEWALS_TOKEN", "").strip()
    if t:
        return t
    try:
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), TOKEN_FILE), encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return ""


def _tok_ok(given):
    t = _token()
    return bool(t) and bool(given) and hmac.compare_digest(str(given), t)


def _gate_token():
    from flask import jsonify, request
    if not _token():
        return jsonify(ok=False, error="not_enabled", message="no renewals token on this server"), 503
    if not _tok_ok(request.headers.get("X-Finance-Renewals") or request.headers.get("X-Renewals-Token")):
        return jsonify(ok=False, error="bad_token"), 401
    return None


def _back():
    from flask import redirect, request
    return redirect(request.form.get("back") or AR.url_for("renewals"))


def post_add():
    from flask import abort, request
    db = AR.get_db()
    f = request.form
    if not may_edit(_role(), f.get("grp", "")):
        abort(403)
    try:
        add_item(db, f.get("what"), f.get("grp"), f.get("expires_on"), f.get("remind_days") or None, f.get("every_months") or 12,
                 f.get("note"), f.get("number"), source="typed", who=_who())
        db.commit()
    except ValueError as ex:
        return "Not saved: %s" % esc(ex), 400
    _state_quiet(db)
    return _back()


def post_renewed(item_id):
    from flask import abort, request
    db = AR.get_db()
    r = db.execute("SELECT grp FROM renewal_item WHERE id=? AND closed=0", (item_id,)).fetchone()
    if r is None:
        abort(404)
    if not may_edit(_role(), r["grp"]):
        abort(403)
    try:
        renew_item(db, item_id, request.form.get("new_expiry"), who=_who(), new_last4=request.form.get("number") or None)
        db.commit()
    except ValueError as ex:
        return "Not saved: %s" % esc(ex), 400
    _state_quiet(db)
    return _back()


def post_mail(mail_id, action):
    from flask import abort, request
    db = AR.get_db()
    m = db.execute("SELECT * FROM renewal_mail WHERE id=? AND status='open'", (mail_id,)).fetchone()
    if m is None:
        abort(404)
    role = _role()
    if action == "apply":
        it = db.execute("SELECT grp FROM renewal_item WHERE id=?", (m["item_id"] or 0,)).fetchone()
        if it is None or not may_edit(role, it["grp"]):
            abort(403)
    elif action == "add":
        if not may_edit(role, request.form.get("grp") or "Clinic"):
            abort(403)
    elif action == "ignore":
        if role != "owner":                                          # a manager may dismiss only a mail matched to a row he may edit
            it = db.execute("SELECT grp FROM renewal_item WHERE id=?", (m["item_id"] or 0,)).fetchone()
            if it is None or not may_edit(role, it["grp"]):
                abort(403)
    else:
        abort(404)
    try:
        decide_mail(db, mail_id, action, who=_who(), new_expiry=request.form.get("new_expiry"), grp=request.form.get("grp"),
                    what=(request.form.get("what") or "").strip() or None)
        db.commit()
    except ValueError as ex:
        return "Not saved: %s" % esc(ex), 400
    _state_quiet(db)
    return _back()


def api_count():
    from flask import jsonify
    try:
        u = AR.current_user()
    except Exception:                                                # noqa: BLE001
        u = None
    if not u or u["role"] not in ("owner", "manager"):
        return jsonify(ok=True, n=None)
    db = AR.get_db()
    gs = groups_for(u["role"])
    mq = ("SELECT COUNT(*) FROM renewal_mail WHERE status='open'" if u["role"] == "owner" else
          "SELECT COUNT(*) FROM renewal_mail m JOIN renewal_item i ON i.id=m.item_id WHERE m.status='open' AND i.closed=0 AND i.grp IN (%s)"
          % ",".join("?" * len(gs)))
    return jsonify(ok=True, n=count_due(db, u["role"]), mails=db.execute(mq, () if u["role"] == "owner" else gs).fetchone()[0])


def api_due():
    from flask import jsonify
    g_ = _gate_token()
    if g_:
        return g_
    db = AR.get_db()
    items, nag_now = due_list(db)
    subject, text = mail_text(items)
    _state_quiet(db)
    return jsonify(ok=True, today=today().isoformat(), items=items, nag_now=nag_now, subject=subject, text=text,
                   ids_to_mark=[x["id"] for x in items if x["nag_today"]])


def api_due_sent():
    from flask import jsonify, request
    g_ = _gate_token()
    if g_:
        return g_
    p = request.get_json(silent=True) or {}
    n = mark_sent(AR.get_db(), p.get("ids") or [])
    return jsonify(ok=True, marked=n)


def api_mail():
    from flask import jsonify, request
    g_ = _gate_token()
    if g_:
        return g_
    p = request.get_json(silent=True)
    if not isinstance(p, dict):
        return jsonify(ok=False, error="bad_payload"), 400
    db = AR.get_db()
    mails = p.get("mails") if isinstance(p.get("mails"), list) else [p]
    stored, dup = 0, 0
    for m in mails[:50]:
        if not isinstance(m, dict):
            continue
        try:
            r = intake_mail(db, m)
        except ValueError:
            continue
        if r is None:
            dup += 1
        else:
            stored += 1
    db.commit()
    return jsonify(ok=True, stored=stored, already=dup, open=db.execute("SELECT COUNT(*) FROM renewal_mail WHERE status='open'").fetchone()[0])


def api_seed():
    from flask import jsonify, request
    g_ = _gate_token()
    if g_:
        return g_
    p = request.get_json(silent=True)
    rows = (p or {}).get("rows") if isinstance(p, dict) else None
    if not isinstance(rows, list):
        return jsonify(ok=False, error="bad_payload", message="expected {rows:[...]}"), 400
    db = AR.get_db()
    try:
        n = seed_rows(db, rows, who="Janitor seed")
    except ValueError as ex:
        return jsonify(ok=False, error=str(ex)), 409
    _state_quiet(db)
    return jsonify(ok=True, added=n, open=db.execute("SELECT COUNT(*) FROM renewal_item WHERE closed=0").fetchone()[0])


def init(ar):
    """Called once, at the foot of asset_register.py."""
    global AR, MOUNTED
    AR = ar
    ensure_at_mount(ar.DB_PATH)
    app, lr = ar.app, ar.login_required
    app.add_url_rule("/renewals/one/add", "s890_add", lr(post_add), methods=["POST"])
    app.add_url_rule("/renewals/one/renewed/<int:item_id>", "s890_renewed", lr(post_renewed), methods=["POST"])
    app.add_url_rule("/renewals/one/mail/<int:mail_id>/<action>", "s890_mail", lr(post_mail), methods=["POST"])
    app.add_url_rule("/renewals/one/api/count", "s890_count", api_count)
    app.add_url_rule("/renewals/one/api/due", "s890_due", api_due)
    app.add_url_rule("/renewals/one/api/due/sent", "s890_due_sent", api_due_sent, methods=["POST"])
    app.add_url_rule("/renewals/one/api/mail", "s890_mail_in", api_mail, methods=["POST"])
    app.add_url_rule("/renewals/one/api/seed", "s890_seed", api_seed, methods=["POST"])
    app.jinja_env.globals.update(s890_top=_wrap(section_top), s890_staff=_wrap(section_staff))
    MOUNTED = True
    return VERSION


# ------------------------------------------------------------------------------------------------------------- CLI
def _selfcheck():
    ok = True

    def c(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("ok   " if cond else "FAIL ") + name)
    c("mask cuts a long number to its last 4", mask("licence 141167 x") == "licence …1167 x")
    c("mask cuts a registration", mask("UP25 AB 0997 insurance") == "…0997 insurance")
    c("mask leaves a date and a 4-digit year", mask("valid till 04-12-2027 and 2026-12-05") == "valid till 04-12-2027 and 2026-12-05")
    c("mask leaves a date followed by a digit", mask("Expires 04-12-2027 1 year 2027 1234") == "Expires 04-12-2027 1 year 2027 1234")
    c("mask cuts a number printed in groups (Aadhaar-style, a card with dashes)", mask("no 1234 5678 9012 card 4111-1111-1111-1234") == "no …9012 card …1234")
    c("today is IST", today() == (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date())
    c("dates_in reads dd-Mon-yyyy and dd/mm/yyyy", dates_in("valid till 04/12/2027 and Expires 13-Aug-2029") == ["2027-12-04", "2029-08-13"])
    c("remind: passport 365", remind_for("Manoj passport renewal", "Personal") == 365)
    c("remind: vehicle insurance 30", remind_for("TVS Star City insurance renewal", "Vehicle") == 30)
    c("remind: PUC 7", remind_for("Vento PUC", "Vehicle") == 7)
    c("remind: RC 45", remind_for("VW Vento registration (RC) renewal", "Vehicle") == 45)
    c("remind: arms licence 45", remind_for("Arms licence renewal - Manoj", "Personal") == 45)
    c("add_months end of month", add_months(datetime.date(2027, 1, 31), 1) == datetime.date(2027, 2, 28))
    c("gap: 7 -> 1, 21 -> 3, 45 -> 7, passport far -> 30", (gap_for(5, 45), gap_for(20, 45), gap_for(40, 45), gap_for(200, 365)) == (1, 3, 7, 30))
    c("guess_group vehicle / personal / civic / nk", (guess_group("VW Vento insurance"), guess_group("Bhawna passport renewal"),
                                                     guess_group("Nagar Nigam renewal - Clinic"), guess_group("Marg ERP licence")) ==
      ("Vehicle", "Personal", "Civic", "NK Pathology"))
    print("renewals_one %s selfcheck: %s" % (VERSION, "OK" if ok else "FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 2 and a[0] == "--ensure":
        t, n = ensure_path(a[1])
        print("renewals_one %s: tables ready (%s); open items %d" % (VERSION, ", ".join(t), n))
    elif len(a) >= 2 and a[0] == "--state":
        db = sqlite3.connect(a[1], timeout=20)
        db.row_factory = sqlite3.Row
        ensure(db)
        wrote = write_state(db, a[2] if len(a) > 2 else None)
        print("renewals_one %s: state file %s (%d items)" % (VERSION, "written" if wrote else "NOT written (folder absent)", len(state_items(db))))
        db.close()
    elif a[:1] == ["--selfcheck"]:
        sys.exit(_selfcheck())
    else:
        print(__doc__)
