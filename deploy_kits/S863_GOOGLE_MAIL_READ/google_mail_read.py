#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""google_mail_read.py -- kit S863_GOOGLE_MAIL_READ (the parent, S480, 18-Nov-2026). PARENT. NEW.

THE OWNER, 18-Nov-2026 07:59 IST ("go"): Google's monthly figures on his Patients page read by the server by itself, from
Google's own monthly mail ("..., your performance report for <Month YYYY>", businessprofile-noreply@google.com, to
drmka.ortho@gmail.com) -- until now a session read the mail and typed a month into patients_google.json.

WHAT IT DOES (run): asks Gmail (read-only) for those mails of the last 400 days, reads from each its month and seven counts
(searches, profile views, calls, chat clicks, direction requests, website visits, interactions) and its top search terms,
and writes them to /root/finance/patients_google_mail.json (months by YYYY-MM; a month read again is replaced by its mail;
nothing else). patients_part2.py (S862) lays these months over patients_google.json: the mail's counts win; Google's
year-on-year (from the profile's Performance page) stays from the session file. COUNTS ONLY -- no reviewer, no customer.
It writes its state to /root/finance/google_mail_read.state.json (last_ok_iso / last_failure_iso / why; no secret) for the
health page's freshness leg "Google monthly mail".

THE ONE-TIME ALLOW (connect): the server's Google client is the one drive_token.json already uses (its client_id /
client_secret, read from that file; the owner's own Google Cloud project). 'connect' prints Google's Allow link for the
read-only Gmail scope; the owner opens it, signs in as drmka.ortho@gmail.com, presses Allow (Google warns the app is not
verified -- it is his own), and pastes back the address the browser lands on (http://localhost/?code=... -- the page itself
does not load, that is expected). The refresh token is kept at /root/wa/recordings-archive/gmail_token.json (mode 600,
beside drive_token.json; the code bundle takes only *.py from that folder and the state backup does not list it). Nothing
here prints a token or a code; the pasted address is read hidden.

    /root/wa/venv/bin/python3 -B /root/finance/google_mail_read.py run|connect|status
Exit: 0 ok (or nothing new) . 2 not connected yet . 3 Google refused (the state says why) . 4 read, but nothing current or
nothing readable (the state says why) . 1 anything else.
Standard library only.
"""
import base64
import datetime as dt
import getpass
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

KIT = "S863"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
FIN = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("GMR_OUT", os.path.join(FIN, "patients_google_mail.json"))
STATE = os.environ.get("GMR_STATE", os.path.join(FIN, "google_mail_read.state.json"))
TOKEN = os.environ.get("GMR_TOKEN", "/root/wa/recordings-archive/gmail_token.json")
ENV_CANDIDATES = ["/root/wa/recordings-archive/.env", "/root/wa/.env"]
DEFAULT_DRIVE_TOKEN = "/root/wa/recordings-archive/drive_token.json"
SCOPE = "https://www.googleapis.com/auth/gmail.readonly"
REDIRECT = "http://localhost"
TOKEN_URI = os.environ.get("GMR_TOKEN_URI", "https://oauth2.googleapis.com/token")
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
API = os.environ.get("GMR_API", "https://gmail.googleapis.com/gmail/v1/users/me")
QUERY = 'from:businessprofile-noreply@google.com subject:"performance report for" newer_than:400d'
ACCOUNT = "drmka.ortho@gmail.com"
MONTHS = {m: i + 1 for i, m in enumerate(("january", "february", "march", "april", "may", "june", "july", "august",
                                           "september", "october", "november", "december"))}
FIG = (("calls", r"([\d,]+)\s+calls?\b"), ("chats", r"([\d,]+)\s+chat clicks?\b"),          # review 2: "1 call", "1 chat click" ...
       ("directions", r"([\d,]+)\s+(?:people|person) asked for directions\b"),
       ("website", r"([\d,]+)\s+website visits? from profile\b"),
       ("views", r"([\d,]+)\s+profile views?\b"), ("searches", r"([\d,]+)\s+search(?:es)?\b(?! terms)"))
BUSINESS = os.environ.get("GMR_BUSINESS", r"dr\.?\s*manoj\s+agarwal")   # review 3 / second look 1: the clinic's own listing
STALE_DAYS = 55                                                     # review 4: Google's mail has come up to ~25 days after a month


class Refused(Exception):
    pass


def now_iso():
    return dt.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def _atomic(path, obj, mode=0o644):
    tmp = "%s.tmp%d" % (path, os.getpid())
    fd = os.open(tmp, os.O_CREAT | os.O_TRUNC | os.O_WRONLY, mode)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                  # noqa: BLE001
        return default


def state(ok, why="", **kw):
    s = _read(STATE, {}) if isinstance(_read(STATE, {}), dict) else {}
    s.update(kit=KIT, last_run_iso=now_iso(), ok=bool(ok), why=str(why)[:300], **kw)
    s.setdefault("last_ok_iso", "")                                    # the freshness leg reads it: empty = never yet
    if ok:
        s["last_ok_iso"] = s["last_run_iso"]
    else:
        s["last_failure_iso"] = s["last_run_iso"]
    _atomic(STATE, s)
    return s


# ------------------------------------------------------------------------------------------------ the client and the token
def drive_token_path():
    p = os.environ.get("DRIVE_TOKEN_FILE", "").strip()
    if p:
        return p
    for f in ENV_CANDIDATES:
        try:
            with open(f) as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("DRIVE_TOKEN_FILE="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return DEFAULT_DRIVE_TOKEN


def client():
    d = _read(drive_token_path(), {})
    cid, sec = str(d.get("client_id") or ""), str(d.get("client_secret") or "")
    if not cid or not sec:
        raise Refused("the server's Google client (client_id / client_secret in drive_token.json) could not be read")
    return cid, sec, str(d.get("token_uri") or TOKEN_URI)


def _post(url, fields):
    data = urllib.parse.urlencode(fields).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            j = json.loads(e.read().decode())
        except Exception:                                              # noqa: BLE001
            j = {}
        raise Refused("Google answered %s (%s)" % (e.code, str(j.get("error_description") or j.get("error") or "")[:160]))


def access_token():
    t = _read(TOKEN, None)
    if not isinstance(t, dict) or not t.get("refresh_token"):
        return None
    cid, sec, uri = client()
    j = _post(t.get("token_uri") or uri, dict(client_id=cid, client_secret=sec, refresh_token=t["refresh_token"], grant_type="refresh_token"))
    a = j.get("access_token")
    if not a:
        raise Refused("Google gave no access")
    return a


def _get(url, at):
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + at})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            j = json.loads(e.read().decode())
        except Exception:                                              # noqa: BLE001
            j = {}
        msg = str(((j.get("error") or {}).get("message")) if isinstance(j.get("error"), dict) else j.get("error") or "")
        m = re.search(r"https://console\.developers\.google\.com/apis/api/gmail\.googleapis\.com/overview\?project=\d+", msg)
        if m:
            raise Refused("the Gmail API is switched off in the clinic's Google project -- switch it on once: %s" % m.group(0))
        raise Refused("Gmail answered %s (%s)" % (e.code, msg[:160]))


# ------------------------------------------------------------------------------------------------ reading one mail
def _text(payload):
    """The text/plain part (or the html part, as text) of a Gmail message payload."""
    parts, plain, htm = [payload], [], []
    while parts:
        p = parts.pop(0)
        parts.extend(p.get("parts") or [])
        data = (p.get("body") or {}).get("data")
        if not data:
            continue
        raw = base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", "replace")
        if p.get("mimeType") == "text/plain":
            plain.append(raw)
        elif p.get("mimeType") == "text/html":
            htm.append(html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?is)<(style|script).*?</\1>", " ", raw))))
    return "\n".join(plain) if plain else "\n".join(htm)


def parse(subject, text):
    """{ym, searches, views, calls, directions, chats, website, interactions, top} or None. Every count must be found."""
    m = re.search(r"performance report for ([A-Za-z]+) (\d{4})", subject or "")
    if not m or m.group(1).lower() not in MONTHS:
        return None
    ym = "%s-%02d" % (m.group(2), MONTHS[m.group(1).lower()])
    t = " ".join(str(text or "").split())
    out = dict(ym=ym)
    for k, pat in FIG:
        f = re.search(pat, t, re.I)
        if not f:
            return None
        out[k] = int(f.group(1).replace(",", ""))
    f = re.search(r"performance for [A-Za-z]+ \d{4}:\s*([\d,]+)\s+interactions", t, re.I)
    out["interactions"] = int(f.group(1).replace(",", "")) if f else out["calls"] + out["chats"] + out["directions"] + out["website"]
    top = []
    seg = re.search(r"Top search terms(.*?)(Take the next step|Are your hours|See more recommendations|Need help|$)", t, re.I)
    if seg:
        for _rank, term, n in re.findall(r"\b([1-9])\s+(.+?)\s+([\d,]+)(?=\s+[1-9]\s|\s*$)", seg.group(1).strip()):
            top.append([term.strip()[:80], int(n.replace(",", ""))])
    out["top"] = top[:5]
    return out


# ------------------------------------------------------------------------------------------------ the commands
def run():
    try:
        at = access_token()
    except Refused as e:
        state(False, str(e))
        print("google_mail_read: REFUSED -- %s" % e)
        return 3
    if at is None:
        state(False, "not connected yet: run 'google_mail_read.py connect' once")
        print("google_mail_read: not connected yet -- the one-time Allow is owed (connect)")
        return 2
    try:
        lst = _get("%s/messages?%s" % (API, urllib.parse.urlencode(dict(q=QUERY, maxResults=50))), at)
        got = {}
        last_day = ""
        listed = other = unread = 0
        newest_listed, unread_months = "", set()
        for m in lst.get("messages") or []:
            msg = _get("%s/messages/%s?format=full" % (API, urllib.parse.quote(m["id"])), at)
            hdr = {h.get("name", "").lower(): h.get("value", "") for h in (msg.get("payload") or {}).get("headers") or []}
            if "businessprofile-noreply@google.com" not in hdr.get("from", "").lower():
                continue
            listed += 1
            if not re.search(BUSINESS, hdr.get("subject", ""), re.I):
                other += 1                                             # review 3: another listing's report -- never the clinic's
                continue
            sm = re.search(r"performance report for ([A-Za-z]+) (\d{4})", hdr.get("subject", ""))
            sym = ("%s-%02d" % (sm.group(2), MONTHS[sm.group(1).lower()])) if sm and sm.group(1).lower() in MONTHS else ""
            newest_listed = max(newest_listed, sym)
            r = parse(hdr.get("subject", ""), _text(msg.get("payload") or {}))
            if not r:
                unread += 1
                unread_months.add(sym)
                continue
            day = dt.datetime.fromtimestamp(int(msg.get("internalDate", "0")) / 1000, IST).strftime("%Y-%m-%d")
            ym = r.pop("ym")
            if ym not in got or day > got[ym]["mail_day"]:
                got[ym] = dict(r, mail_day=day)
            last_day = max(last_day, day)
    except Refused as e:
        state(False, str(e))
        print("google_mail_read: REFUSED -- %s" % e)
        return 3
    except Exception as e:                                             # noqa: BLE001 -- review 6: the state always says why
        state(False, "the run stopped: %s" % type(e).__name__)
        print("google_mail_read: STOPPED -- %s" % type(e).__name__)
        return 1
    old = _read(OUT, {})
    months = dict(old.get("months") or {}) if isinstance(old, dict) else {}
    changed = [ym for ym in sorted(got) if months.get(ym) != got[ym]]
    months.update(got)
    doc = dict(about=("Google Business Profile, the clinic's listing: each month's counts as Google's own monthly performance mail "
                      "gives them, read by the server (google_mail_read.py, %s). Counts and search terms only." % KIT),
               version="%s mail 1" % KIT, months=months,
               mail_day=max([v.get("mail_day", "") for v in months.values()] + [old.get("mail_day", "") if isinstance(old, dict) else ""]),
               checked=now_iso())
    _atomic(OUT, doc)
    newest = max(months) if months else ""
    age = (dt.datetime.now(IST).date() - month_end(newest)).days if newest else None
    why = ""
    if listed and not got and unread:
        why = "Google's monthly mails were found but none could be read (%d) -- the mail's wording may have changed" % unread
    elif listed and not got and other:
        why = "%d monthly reports found, none for the clinic's listing (its name not in the subject)" % other
    elif newest_listed and newest_listed in unread_months and newest_listed not in got:
        why = "the newest report (%s) could not be read -- the mail's wording may have changed" % newest_listed
    elif age is None or age > STALE_DAYS:
        why = "no monthly report newer than %s has come (%s days)" % (newest or "none", age if age is not None else "-")
    state(not why, why, months_read=len(got), months_kept=len(months), changed=changed, last_mail=last_day,
          other_listings=other, unread=unread, newest_month=newest)
    print("google_mail_read: %s -- %d monthly mails read, %d months kept, changed: %s%s" % (
        "OK" if not why else "ATTENTION", len(got), len(months), ", ".join(changed) or "none", (" -- " + why) if why else ""))
    return 0 if not why else 4


def month_end(ym):
    a = dt.date(int(ym[:4]), int(ym[5:7]), 1)
    return (a.replace(day=28) + dt.timedelta(days=4)).replace(day=1) - dt.timedelta(days=1)


def connect(inp=None, out=print):
    inp = inp or getpass.getpass
    cid, _sec, uri = client()
    q = dict(client_id=cid, redirect_uri=REDIRECT, response_type="code", scope=SCOPE, access_type="offline", prompt="consent",
             login_hint=ACCOUNT)
    out("")
    out("1. Open this link in your browser (one line):")
    out("")
    out("%s?%s" % (AUTH_URI, urllib.parse.urlencode(q)))
    out("")
    out("2. Sign in as %s. Google says the app is not verified -- it is yours: Advanced -> Go to ... -> Allow." % ACCOUNT)
    out("3. The browser lands on a page that does not load (localhost). Copy the WHOLE address from the address bar")
    out("   and paste it here (it stays hidden as you paste), then press Enter.")
    out("")
    got = inp("Paste the address here: ").strip()
    code = (urllib.parse.parse_qs(urllib.parse.urlparse(got).query).get("code") or [""])[0] if "code=" in got else ""
    if not code:
        out("!! no code in what was pasted -- nothing saved. Run the same line again.")
        return 1
    _c, sec, _u = client()
    try:
        j = _post(uri, dict(code=code, client_id=cid, client_secret=sec, redirect_uri=REDIRECT, grant_type="authorization_code"))
    except Refused as e:
        out("!! %s -- nothing saved. Run the same line again (a code works once, for a few minutes)." % e)
        return 3
    if not j.get("refresh_token"):
        out("!! Google gave no lasting permission -- nothing saved. Run the same line again.")
        return 3
    if SCOPE not in str(j.get("scope", SCOPE)):
        out("!! the Gmail read permission was not ticked on Google's page -- nothing saved. Run the same line again and tick it.")
        return 3
    try:                                                               # review 5: the right mailbox, or nothing is kept
        who = str(_get("%s/profile" % API, j.get("access_token", "")).get("emailAddress") or "").lower()
    except Refused as e:
        out("!! %s -- nothing saved." % e)
        return 3
    if who != ACCOUNT:
        out("!! that was another Google account (%s), not %s -- nothing saved. Run the same line again and choose %s."
            % (who or "unknown", ACCOUNT, ACCOUNT))
        return 3
    os.makedirs(os.path.dirname(TOKEN), exist_ok=True)
    _atomic(TOKEN, dict(refresh_token=j["refresh_token"], token_uri=uri, scopes=[SCOPE], account=ACCOUNT, saved=now_iso(), kit=KIT), mode=0o600)
    out("Saved the read-only Gmail permission (%s, mode 600). Reading Google's monthly mails now..." % TOKEN)
    rc = run()
    if rc == 0:
        out("CONNECTED: the server reads Google's monthly mail by itself from now on.")
    return rc


def status():
    s = _read(STATE, {})
    print(json.dumps({k: s.get(k) for k in ("ok", "why", "last_run_iso", "last_ok_iso", "last_failure_iso", "months_read", "months_kept", "last_mail",
                                             "newest_month", "other_listings", "unread")},
                     ensure_ascii=False))
    print("connected: %s" % ("yes" if isinstance(_read(TOKEN, None), dict) else "no"))
    return 0


if __name__ == "__main__":
    fn = {"run": run, "connect": connect, "status": status}.get(sys.argv[1] if len(sys.argv) > 1 else "")
    if fn is None:                                                     # review 6: the command looked up first
        print(__doc__)
        sys.exit(1)
    try:
        sys.exit(fn())
    except Refused as e:
        state(False, str(e))
        print("google_mail_read: REFUSED -- %s" % e)
        sys.exit(3)
    except Exception as e:                                             # noqa: BLE001
        state(False, "the run stopped: %s" % type(e).__name__)
        print("google_mail_read: STOPPED -- %s" % type(e).__name__)
        sys.exit(1)
