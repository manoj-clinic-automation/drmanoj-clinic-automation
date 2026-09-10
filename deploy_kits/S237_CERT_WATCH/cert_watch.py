#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cert_watch.py  —  the certificate night-watchman
Dr. Manoj Agarwal Clinic · Bareilly · Session 237 (F-387)

WHY THIS EXISTS
  On 08-Sep-2026 the public website drmanojagarwal.com served an EXPIRED
  certificate to patients for a full day. Nothing in the estate noticed. The
  first signal was the owner opening the site by chance on his phone.

  Three failures stacked (S236):
    a) acme.sh was renewing two domains against Let's Encrypt STAGING, whose
       certificates every browser rejects;
    b) having "renewed", acme.sh advanced its own clock to 01-Nov and then
       SKIPPED the domain every night, printing a clean successful run;
    c) when a real certificate finally arrived, the web server was not
       reloaded, so the correct file sat unused on disk for an hour.

  Every one of those reported success. So this watchman does NOT ask acme.sh
  anything, and does not read any file acme.sh writes.

  RULE (F-386, and the reason for every design choice below):
      A renewal job that reports success is not evidence.
      Assert the thing the world can see -- what the server actually SERVES.

WHAT IT DOES
  Opens a TLS connection to each clinic hostname, exactly as a patient's
  browser would, and reads the certificate that comes back. Then it says, for
  each one: how many days are left, who issued it, whether the name matches,
  and whether it is a STAGING certificate pretending to be real.

  Silent when everything is fine. One phone-push + one email when something
  needs attention, ONCE per problem, and one note when it recovers.

  It NEVER renews, installs, restarts or changes anything. Read-only.

HOW IT LOOKS -- TWO PASSES, AND THE FIRST ONE IS THE REAL TEST
  Pass 1 connects EXACTLY as a browser does, with full verification and
  hostname checking. If that succeeds, a browser accepts the site: that is the
  strongest statement available, and it is the one the owner cares about.

  Pass 2 runs only when pass 1 refused. It reconnects with verification off,
  purely to LOOK at the certificate being served, so the watchman can say what
  is actually wrong -- expired, wrong name, staging CA -- instead of "failed".

  (Design note, paid for by a live-shape walk at S237: ssl.getpeercert() returns
  an EMPTY dict on an unverified connection, so a one-pass "verification off"
  design silently reports every site as unreachable. It passed 50 unit checks
  and was wrong about all seven live sites. Pass 2 therefore reads the raw DER
  and decodes it itself.)

RUN
  On the VPS, by hand, safe, prints a table and sends nothing:
    /root/wa/venv/bin/python3 /root/wa/cert_watch.py --dry-run

  Prove it without touching the network:
    /root/wa/venv/bin/python3 /root/wa/cert_watch.py --selftest

  Live, as its own systemd timer installs it (daily 06:40 IST):
    /root/wa/venv/bin/python3 /root/wa/cert_watch.py

  Runs on plain python3 too -- standard library only, no gspread, no requests.
"""

import argparse
import datetime as dt
import json
import os
import smtplib
import socket
import ssl
import sys
import urllib.request
from email.mime.text import MIMEText

IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# CONFIG -- the nine vhosts on the server, taken from the server's own vhost
# list at S236, not from memory.
#
#   watch=True   a real public certificate is expected; report on it
#   watch=False  known and deliberately not certificated; counted, never alerted
#
# Adding a site here is the whole job of adding it to the watch.
# ---------------------------------------------------------------------------
SITES = [
    ("drmanojagarwal.com",      True,  "the public clinic website"),
    ("followup.dr-manoj.in",    True,  "the clinic hub"),
    ("attendance.dr-manoj.in",  True,  "attendance dashboard"),
    ("assets.dr-manoj.in",      True,  "asset register"),
    ("fit.dr-manoj.in",         True,  "fit"),
    ("health.dr-manoj.in",      True,  "health"),
    ("rx.dr-manoj.in",          True,  "rx"),
    ("srv1746119.hstgr.cloud",  True,  "the server's own hostname"),
    ("drmanojagarwal.in",       False, "RETIRED by the owner -- not renewed on purpose (D-, S236)"),
]

# THE THRESHOLDS ARE TUNED TO THIS SERVER, and the numbers are not arbitrary.
# Measured 10-Sep-2026: CyberPanel's own renew.py renews a certificate when it has
# 15 DAYS OR FEWER left -- not the 30 days acme.sh uses. So a warning at 21 days
# would fire while CyberPanel was behaving exactly as designed, which is a
# watchman crying wolf. These numbers sit INSIDE CyberPanel's window, so a
# warning means the renewal is genuinely LATE, not merely approaching.
WARN_DAYS = 10          # CyberPanel has already had 5 days to renew this and has not
URGENT_DAYS = 4         # it is about to break in front of patients
PORT = 443
TIMEOUT = 15

STATE_FILE = os.environ.get("CERTWATCH_STATE_FILE", "/root/wa/cert_watch_state.json")
LOG_FILE = os.environ.get("CERTWATCH_LOG_FILE", "/root/wa/cert_watch.log")
ALERT_EMAIL_TO = os.environ.get("WATCHDOG_EMAIL_TO", "drmka.ortho@gmail.com")
SMTP_HOST = os.environ.get("WATCHDOG_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("WATCHDOG_SMTP_PORT", "587"))
SMTP_USER = os.environ.get("WATCHDOG_SMTP_USER", "")
SMTP_PASS = os.environ.get("WATCHDOG_SMTP_PASS", "")
SMTP_FROM = os.environ.get("WATCHDOG_SMTP_FROM", SMTP_USER or ALERT_EMAIL_TO)

# Verdicts, worst first. The order matters: it decides the alert priority.
V_ERROR = "ERROR"        # could not be reached at all
V_EXPIRED = "EXPIRED"    # serving an expired certificate right now
V_STAGING = "STAGING"    # serving a test certificate -- browsers reject it
V_MISMATCH = "MISMATCH"  # the certificate is not for this hostname
V_URGENT = "URGENT"      # <= URGENT_DAYS left
V_WARN = "WARN"          # <= WARN_DAYS left
V_UNTRUSTED = "UNTRUSTED"  # a browser refuses it, for a reason not covered above
V_OK = "OK"
V_SKIP = "SKIP"          # watch=False
BAD = (V_ERROR, V_EXPIRED, V_STAGING, V_MISMATCH, V_UNTRUSTED, V_URGENT, V_WARN)


def now_ist():
    return dt.datetime.now(IST)


def stamp(when=None):
    return (when or now_ist()).strftime("%Y-%m-%d %H:%M:%S")


def log(line):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("[%s IST] %s\n" % (stamp(), line))
    except Exception:
        pass


# ---------------------------------------------------------------------------
# The pure half -- no network, no files. Everything here is selftested.
# ---------------------------------------------------------------------------
def _rdn_values(seq):
    """ssl.getpeercert() gives issuer/subject as a tuple of tuples of pairs.
    Flatten it to a plain dict, last value wins."""
    out = {}
    for rdn in (seq or ()):
        for pair in rdn:
            if isinstance(pair, (tuple, list)) and len(pair) == 2:
                out[str(pair[0])] = str(pair[1])
    return out


def cert_names(cert):
    """Every name the certificate claims: the SAN dNSNames, plus the subject CN."""
    names = [v for (k, v) in (cert.get("subjectAltName") or ()) if k.lower() == "dns"]
    cn = _rdn_values(cert.get("subject")).get("commonName")
    if cn and cn not in names:
        names.append(cn)
    return names


def name_matches(host, names):
    """Does this certificate cover this hostname? Wildcards match ONE label only,
    which is what browsers do -- *.dr-manoj.in covers followup.dr-manoj.in but
    never a.b.dr-manoj.in."""
    host = (host or "").lower().rstrip(".")
    for n in names:
        n = (n or "").lower().rstrip(".")
        if not n:
            continue
        if n == host:
            return True
        if n.startswith("*."):
            tail = n[2:]
            if not tail:
                continue
            if host.endswith("." + tail) and host[: -(len(tail) + 1)].count(".") == 0:
                return True
    return False


def is_staging_issuer(issuer_text):
    """Let's Encrypt's staging CA names itself loudly. This is the exact trap
    that hid the S236 outage: a staging certificate looks issued and valid to
    acme.sh, and is rejected by every browser."""
    t = (issuer_text or "").upper()
    return ("STAGING" in t) or ("FAKE LE" in t) or ("HAPPY HACKER" in t)


def days_left(not_after_epoch, now_epoch):
    """Whole days remaining. Negative once expired. Truncates toward zero from
    below on purpose: 0.9 days left is reported as 0, never as 1."""
    return int((not_after_epoch - now_epoch) // 86400)


def evaluate(host, watch, cert, now_epoch, error=None, browser_ok=None):
    """The whole judgement, as one pure function. Returns a plain dict.

    cert        the certificate's fields, in the shape ssl.getpeercert() uses,
                or None when nothing could be read -- then `error` says why.
    browser_ok  True  = pass 1 succeeded, a real browser accepts this site.
                False = a browser refuses it; `error` carries the reason.
                None  = not established (used by the offline selftests)."""
    r = {"host": host, "verdict": V_SKIP, "days": None, "issuer": "",
         "not_after": "", "names": [], "note": "", "browser_ok": browser_ok}
    if not watch:
        r["note"] = "not watched on purpose"
        return r
    if cert is None:
        r["verdict"] = V_ERROR
        r["note"] = str(error or "could not connect")
        return r

    issuer = _rdn_values(cert.get("issuer"))
    r["issuer"] = issuer.get("commonName") or issuer.get("organizationName") or ""
    issuer_all = " ".join(issuer.values())
    r["names"] = cert_names(cert)
    na = cert.get("notAfter") or ""
    r["not_after"] = na
    try:
        na_epoch = ssl.cert_time_to_seconds(na)
    except Exception:
        r["verdict"] = V_ERROR
        r["note"] = "unreadable expiry date %r" % na
        return r
    d = days_left(na_epoch, now_epoch)
    r["days"] = d
    r["expires_ist"] = dt.datetime.fromtimestamp(na_epoch, IST).strftime("%d-%b-%Y %H:%M")

    # Worst thing first. Each of these is a different repair, so they are not merged.
    if d < 0:
        r["verdict"] = V_EXPIRED
        r["note"] = "EXPIRED %d days ago -- browsers are refusing this site now" % abs(d)
    elif is_staging_issuer(issuer_all):
        r["verdict"] = V_STAGING
        r["note"] = "issued by the Let's Encrypt STAGING CA -- every browser rejects it"
    elif not name_matches(host, r["names"]):
        r["verdict"] = V_MISMATCH
        r["note"] = "certificate does not cover this name (it covers %s)" % (", ".join(r["names"][:4]) or "nothing")
    elif browser_ok is False:
        # A browser refuses it and none of the three named causes explains why.
        # Never let this fall through to OK: the site is broken for patients.
        r["verdict"] = V_UNTRUSTED
        r["note"] = "a browser refuses this site -- %s" % (error or "reason not reported")
    elif d <= URGENT_DAYS:
        r["verdict"] = V_URGENT
        r["note"] = "%d days left" % d
    elif d <= WARN_DAYS:
        r["verdict"] = V_WARN
        r["note"] = "%d days left -- CyberPanel renews at 15, so this one is already LATE" % d
    else:
        r["verdict"] = V_OK
        r["note"] = "%d days left" % d
    # A staging certificate that is ALSO expired is still worth saying twice.
    if r["verdict"] == V_EXPIRED and is_staging_issuer(issuer_all):
        r["note"] += " (and it is a STAGING certificate)"
    return r


def problem_key(r):
    """What we remember, so one problem alerts once. Includes the verdict, so a
    site sliding from WARN to EXPIRED alerts again -- that is a new fact."""
    return "%s:%s" % (r["host"], r["verdict"])


def build_message(results, when=None):
    """The words the owner actually reads. Kept short and in plain language."""
    bad = [r for r in results if r["verdict"] in BAD]
    lines = ["CLINIC CERTIFICATES -- %d site(s) need attention.\n" % len(bad)]
    for r in sorted(bad, key=lambda x: (BAD.index(x["verdict"]), x["host"])):
        lines.append("* %s -- %s" % (r["host"], r["verdict"]))
        lines.append("   %s" % r["note"])
        if r.get("expires_ist"):
            lines.append("   expires %s IST, issued by %s" % (r["expires_ist"], r["issuer"] or "unknown"))
        lines.append("")
    lines.append("Checked by opening each site the way a browser does.")
    lines.append("Nothing was changed. Time: %s IST" % stamp(when))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The I/O half.
# ---------------------------------------------------------------------------
def _fmt_time(d):
    """The exact spelling ssl.cert_time_to_seconds() expects, e.g. 'Sep  8 10:07:00 2026 GMT'."""
    return "%s %2d %02d:%02d:%02d %d GMT" % (
        ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")[d.month - 1],
        d.day, d.hour, d.minute, d.second, d.year)


def _parse_openssl_text(text):
    """Turn `openssl x509 -noout -subject -issuer -dates -ext subjectAltName`
    output into the same shape ssl.getpeercert() returns. Pure; selftested."""
    out = {"subject": (), "issuer": (), "notAfter": "", "subjectAltName": ()}

    def rdn(line):
        # 'subject=O = Lets Encrypt, CN = example.com'  ->  ((('organizationName','Lets Encrypt'),), ...)
        body = line.split("=", 1)[1].strip() if "=" in line else ""
        long = {"CN": "commonName", "O": "organizationName", "OU": "organizationalUnitName",
                "C": "countryName", "ST": "stateOrProvinceName", "L": "localityName"}
        items = []
        for part in body.split(","):
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            k, v = k.strip(), v.strip()
            items.append(((long.get(k, k), v),))
        return tuple(items)

    san = []
    for line in (text or "").splitlines():
        s = line.strip()
        if s.startswith("subject="):
            out["subject"] = rdn(s)
        elif s.startswith("issuer="):
            out["issuer"] = rdn(s)
        elif s.startswith("notAfter="):
            out["notAfter"] = s.split("=", 1)[1].strip()
        elif "DNS:" in s:
            for tok in s.split(","):
                tok = tok.strip()
                if tok.startswith("DNS:"):
                    san.append(("DNS", tok[4:].strip()))
    out["subjectAltName"] = tuple(san)
    return out


def _decode_der(der):
    """Read a raw certificate into getpeercert()-shaped fields.
    Tries the cryptography library, then the openssl command. Returns None if
    neither is available -- the caller then reports the handshake reason, which
    is still a true statement and never a silence."""
    try:
        from cryptography import x509 as _x509                      # optional
        from cryptography.hazmat.primitives.serialization import Encoding  # noqa: F401
        c = _x509.load_der_x509_certificate(der)

        def name(n):
            return tuple(((a.oid._name, a.value),) for a in n)
        san = ()
        try:
            ext = c.extensions.get_extension_for_class(_x509.SubjectAlternativeName)
            san = tuple(("DNS", v) for v in ext.value.get_values_for_type(_x509.DNSName))
        except Exception:
            pass
        na = getattr(c, "not_valid_after_utc", None) or c.not_valid_after
        return {"subject": name(c.subject), "issuer": name(c.issuer),
                "notAfter": _fmt_time(na), "subjectAltName": san}
    except Exception:
        pass
    try:
        import subprocess, tempfile
        with tempfile.NamedTemporaryFile(suffix=".der", delete=False) as f:
            f.write(der)
            path = f.name
        try:
            p = subprocess.run(["openssl", "x509", "-inform", "DER", "-in", path, "-noout",
                                "-subject", "-issuer", "-dates", "-ext", "subjectAltName"],
                               capture_output=True, text=True, timeout=20)
            if p.returncode == 0 and p.stdout:
                return _parse_openssl_text(p.stdout)
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass
    except Exception:
        pass
    return None


def fetch_cert(host, port=PORT, timeout=TIMEOUT):
    """Return (fields, error, browser_ok).

    Pass 1 is a full browser-style verified handshake. If it succeeds, the site
    is genuinely fine and we already have every field.
    Pass 2 runs only on refusal, with verification off, to LOOK at what is being
    served -- because that is the only way to say WHY a browser refused."""
    ctx = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                return ss.getpeercert(), None, True
    except ssl.SSLCertVerificationError as e:
        why = getattr(e, "verify_message", None) or str(e)
    except Exception as e:
        # Could not even reach it -- no second pass is possible or useful.
        return None, "%s: %s" % (type(e).__name__, e), False

    ctx2 = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx2.check_hostname = False
    ctx2.verify_mode = ssl.CERT_NONE
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx2.wrap_socket(sock, server_hostname=host) as ss:
                der = ss.getpeercert(binary_form=True)
        fields = _decode_der(der) if der else None
        return fields, why, False
    except Exception as e:
        return None, "%s (and could not re-read it: %s)" % (why, e), False


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f).get("alerted", []))
    except Exception:
        return set()


def save_state(keys):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({"alerted": sorted(keys), "updated": stamp()}, f, indent=2)
    except Exception as e:
        log("WARN could not write state: %s" % e)


def _ntfy_url():
    u = os.environ.get("WATCHDOG_NTFY_URL", "")
    if u:
        return u
    try:
        with open("/root/wa/.env", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("WATCHDOG_NTFY_URL="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except Exception:
        pass
    return ""


def _ascii_header(text):
    try:
        return text.encode("ascii", "ignore").decode("ascii").strip() or "Clinic certificates"
    except Exception:
        return "Clinic certificates"


def send_ntfy(title, body, priority="urgent"):
    url = _ntfy_url()
    if not url:
        log("WARN no ntfy topic configured -- push NOT sent")
        return False
    try:
        req = urllib.request.Request(
            url, data=body.encode("utf-8"),
            headers={"Title": _ascii_header(title), "Priority": priority, "Tags": "lock"},
            method="POST")
        urllib.request.urlopen(req, timeout=TIMEOUT)
        return True
    except Exception as e:
        log("WARN ntfy failed: %s" % e)
        return False


def send_email(subject, body):
    if not (SMTP_HOST and SMTP_USER and SMTP_PASS):
        log("INFO email skipped (SMTP not configured); ntfy is primary")
        return False
    try:
        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = ALERT_EMAIL_TO
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_FROM, [ALERT_EMAIL_TO], msg.as_string())
        return True
    except Exception as e:
        log("WARN email failed: %s" % e)
        return False


def check_all(sites=None, now_epoch=None):
    sites = sites or SITES
    now_epoch = now_epoch if now_epoch is not None else dt.datetime.now(dt.timezone.utc).timestamp()
    out = []
    for host, watch, _label in sites:
        if not watch:
            out.append(evaluate(host, watch, None, now_epoch))
            continue
        cert, err, browser_ok = fetch_cert(host)
        out.append(evaluate(host, watch, cert, now_epoch, error=err, browser_ok=browser_ok))
    return out


def print_table(results):
    print("=== Clinic certificates -- %s IST ===" % stamp())
    for r in results:
        mark = {V_OK: "ok  ", V_SKIP: "--  "}.get(r["verdict"], "!!  ")
        d = "" if r["days"] is None else "%4d d" % r["days"]
        print("  %s%-26s %-9s %6s  %s" % (mark, r["host"], r["verdict"], d, r["note"]))
    print("---")


def run(dry_run=False):
    results = check_all()
    print_table(results)

    bad = [r for r in results if r["verdict"] in BAD]
    keys = {problem_key(r) for r in bad}
    already = load_state()
    new = keys - already
    gone = already - keys

    if dry_run:
        print("  -> dry run: %d problem(s), %d new, %d cleared. Nothing sent, nothing saved."
              % (len(bad), len(new), len(gone)))
        return 0

    if new:
        body = build_message(results)
        worst = min((BAD.index(r["verdict"]) for r in bad), default=len(BAD))
        pri = "urgent" if worst <= BAD.index(V_MISMATCH) else "high"
        ok_n = send_ntfy("Clinic certificates: attention needed", body, priority=pri)
        ok_m = send_email("Clinic certificates: attention needed", body)
        log("ALERT %d new | ntfy=%s email=%s | %s" % (len(new), ok_n, ok_m, ", ".join(sorted(new))))
    if gone:
        body = ("CLINIC CERTIFICATES -- resolved:\n\n" +
                "\n".join("* %s" % k for k in sorted(gone)) +
                "\n\nTime: %s IST" % stamp())
        send_ntfy("Clinic certificates: resolved", body, priority="default")
        send_email("Clinic certificates: resolved", body)
        log("RECOVERED %s" % ", ".join(sorted(gone)))

    save_state(keys)
    if not bad:
        log("CHECK all %d watched sites healthy" % sum(1 for s in SITES if s[1]))
    else:
        log("CHECK %d problem(s): %s" % (len(bad), ", ".join(sorted(k for k in keys))))
    if not new and not gone:
        print("  -> no change since last check; nothing sent")
    return 0


# ---------------------------------------------------------------------------
# selftest -- no network, no files, no sending. Fixtures only.
# ---------------------------------------------------------------------------
def _cert(not_after, names=("example.com",), issuer_cn="R11", issuer_o="Let's Encrypt", cn=None):
    c = {"notAfter": not_after,
         "subjectAltName": tuple(("DNS", n) for n in names),
         "issuer": ((("countryName", "US"),), (("organizationName", issuer_o),), (("commonName", issuer_cn),))}
    if cn:
        c["subject"] = ((("commonName", cn),),)
    return c


def selftest():
    checks = []

    def ck(name, got, want):
        ok = got == want
        checks.append((ok, name, got, want))
        return ok

    NOW = ssl.cert_time_to_seconds("Sep 10 00:00:00 2026 GMT")

    # --- name matching ------------------------------------------------------
    ck("exact name matches", name_matches("a.dr-manoj.in", ["a.dr-manoj.in"]), True)
    ck("case is ignored", name_matches("A.DR-MANOJ.IN", ["a.dr-manoj.in"]), True)
    ck("trailing dot ignored", name_matches("a.dr-manoj.in.", ["a.dr-manoj.in"]), True)
    ck("wildcard covers one label", name_matches("followup.dr-manoj.in", ["*.dr-manoj.in"]), True)
    ck("wildcard does NOT cross a dot", name_matches("a.b.dr-manoj.in", ["*.dr-manoj.in"]), False)
    ck("wildcard does not cover the bare domain", name_matches("dr-manoj.in", ["*.dr-manoj.in"]), False)
    ck("wrong name is refused", name_matches("evil.com", ["*.dr-manoj.in", "dr-manoj.in"]), False)
    ck("empty list is refused", name_matches("a.dr-manoj.in", []), False)
    ck("bare * is refused", name_matches("a.dr-manoj.in", ["*."]), False)
    ck("CN is used when SAN is absent",
       cert_names({"subject": ((("commonName", "x.in"),),)}), ["x.in"])
    ck("CN not duplicated when already in SAN",
       cert_names({"subjectAltName": (("DNS", "x.in"),), "subject": ((("commonName", "x.in"),),)}), ["x.in"])

    # --- staging detection --------------------------------------------------
    ck("staging CA is caught", is_staging_issuer("(STAGING) Pretend Pear X1"), True)
    ck("Fake LE is caught", is_staging_issuer("Fake LE Intermediate X1"), True)
    ck("happy hacker is caught", is_staging_issuer("happy hacker fake CA"), True)
    ck("real LE is not flagged", is_staging_issuer("Let's Encrypt R11"), False)
    ck("empty issuer is not flagged", is_staging_issuer(""), False)

    # --- days left ----------------------------------------------------------
    ck("exactly 30 days", days_left(NOW + 30 * 86400, NOW), 30)
    ck("part days round DOWN", days_left(NOW + int(1.9 * 86400), NOW), 1)
    ck("expiring within the hour is 0 days", days_left(NOW + 3600, NOW), 0)
    ck("already expired is negative", days_left(NOW - 86400, NOW), -1)

    # --- the whole judgement ------------------------------------------------
    ok = evaluate("a.dr-manoj.in", True, _cert("Dec  8 00:00:00 2026 GMT", ["a.dr-manoj.in"]), NOW)
    ck("healthy site is OK", ok["verdict"], V_OK)
    ck("healthy site counts the days", ok["days"], 89)

    warn = evaluate("attendance.dr-manoj.in", True,
                    _cert("Sep 20 00:00:00 2026 GMT", ["attendance.dr-manoj.in"]), NOW)
    ck("10 days out warns", warn["verdict"], V_WARN)
    ck("and it says CyberPanel is late", "already LATE" in warn["note"], True)
    ck("22 days out is still quiet -- CyberPanel has not been asked yet",
       evaluate("attendance.dr-manoj.in", True, _cert("Oct  2 00:00:00 2026 GMT", ["attendance.dr-manoj.in"]), NOW)["verdict"], V_OK)
    ck("16 days out is still quiet -- one day outside CyberPanel's window",
       evaluate("a", True, _cert("Sep 26 00:00:00 2026 GMT", ["a"]), NOW)["verdict"], V_OK)

    urg = evaluate("a.dr-manoj.in", True, _cert("Sep 13 00:00:00 2026 GMT", ["a.dr-manoj.in"]), NOW)
    ck("3 days out is urgent", urg["verdict"], V_URGENT)

    exp = evaluate("drmanojagarwal.com", True,
                   _cert("Sep  8 10:07:00 2026 GMT", ["drmanojagarwal.com"]), NOW)
    ck("the real 08-Sep outage is caught", exp["verdict"], V_EXPIRED)
    ck("and it says how long it has been broken", exp["days"], -2)

    stg = evaluate("drmanojagarwal.com", True,
                   _cert("Dec  8 00:00:00 2026 GMT", ["drmanojagarwal.com"],
                         issuer_cn="(STAGING) Pretend Pear X1", issuer_o="(STAGING) Internet Security Research Group"), NOW)
    ck("a valid-looking STAGING cert is caught", stg["verdict"], V_STAGING)

    mis = evaluate("rx.dr-manoj.in", True,
                   _cert("Dec  8 00:00:00 2026 GMT", ["followup.dr-manoj.in"]), NOW)
    ck("the wrong certificate is caught", mis["verdict"], V_MISMATCH)

    err = evaluate("gone.dr-manoj.in", True, None, NOW, error="TimeoutError: timed out")
    ck("an unreachable site is an ERROR, not a silence", err["verdict"], V_ERROR)
    ck("and it keeps the reason", "Timeout" in err["note"], True)

    skip = evaluate("drmanojagarwal.in", False, None, NOW)
    ck("a retired domain is skipped, not alerted", skip["verdict"], V_SKIP)

    bad_date = evaluate("a.dr-manoj.in", True, _cert("not a date", ["a.dr-manoj.in"]), NOW)
    ck("an unreadable date is an ERROR, never an OK", bad_date["verdict"], V_ERROR)

    # expired AND staging: expiry is named first, staging still mentioned
    both = evaluate("drmanojagarwal.com", True,
                    _cert("Sep  1 00:00:00 2026 GMT", ["drmanojagarwal.com"],
                          issuer_cn="(STAGING) Pretend Pear X1"), NOW)
    ck("expired+staging reports EXPIRED", both["verdict"], V_EXPIRED)
    ck("expired+staging still says staging", "STAGING" in both["note"], True)

    # --- pass 2: reading a certificate the browser refused ------------------
    OPENSSL_FIXTURE = (
        "subject=O = Lets Encrypt, CN = drmanojagarwal.com\n"
        "issuer=C = US, O = (STAGING) Internet Security Research Group, CN = (STAGING) Pretend Pear X1\n"
        "notBefore=Jun 12 00:00:00 2026 GMT\n"
        "notAfter=Sep  8 10:07:00 2026 GMT\n"
        "X509v3 Subject Alternative Name: \n"
        "    DNS:drmanojagarwal.com, DNS:www.drmanojagarwal.com\n")
    f = _parse_openssl_text(OPENSSL_FIXTURE)
    ck("openssl text -> expiry", f["notAfter"], "Sep  8 10:07:00 2026 GMT")
    ck("openssl text -> both SAN names", cert_names(f), ["drmanojagarwal.com", "www.drmanojagarwal.com"])
    ck("openssl text -> issuer flattened", _rdn_values(f["issuer"]).get("commonName"), "(STAGING) Pretend Pear X1")
    fr = evaluate("drmanojagarwal.com", True, f, NOW, error="certificate has expired", browser_ok=False)
    ck("a pass-2 read still judges correctly", fr["verdict"], V_EXPIRED)
    ck("empty openssl text does not crash", _parse_openssl_text("")["notAfter"], "")

    ck("space-padded date parses", ssl.cert_time_to_seconds("Sep  8 10:07:00 2026 GMT") > 0, True)
    ck("zero-padded date parses", ssl.cert_time_to_seconds("Sep 08 10:07:00 2026 GMT") > 0, True)
    ck("both spellings are the same instant",
       ssl.cert_time_to_seconds("Sep  8 10:07:00 2026 GMT") == ssl.cert_time_to_seconds("Sep 08 10:07:00 2026 GMT"), True)
    ck("_fmt_time writes the space-padded spelling",
       _fmt_time(dt.datetime(2026, 9, 8, 10, 7, 0)), "Sep  8 10:07:00 2026 GMT")
    ck("_fmt_time round-trips through the parser",
       ssl.cert_time_to_seconds(_fmt_time(dt.datetime(2026, 12, 8, 0, 0, 0))),
       ssl.cert_time_to_seconds("Dec  8 00:00:00 2026 GMT"))

    # --- browser_ok drives the catch-all ------------------------------------
    unt = evaluate("a.dr-manoj.in", True, _cert("Dec  8 00:00:00 2026 GMT", ["a.dr-manoj.in"]), NOW,
                   error="unable to get local issuer certificate", browser_ok=False)
    ck("a browser refusal is never reported as OK", unt["verdict"], V_UNTRUSTED)
    ck("and the refusal reason is kept", "local issuer" in unt["note"], True)
    acc = evaluate("a.dr-manoj.in", True, _cert("Dec  8 00:00:00 2026 GMT", ["a.dr-manoj.in"]), NOW,
                   browser_ok=True)
    ck("a browser-accepted healthy cert is OK", acc["verdict"], V_OK)
    ck("browser_ok is carried into the result", acc["browser_ok"], True)
    ck("an expired cert outranks the catch-all",
       evaluate("a", True, _cert("Sep  1 00:00:00 2026 GMT", ["a"]), NOW, error="expired", browser_ok=False)["verdict"],
       V_EXPIRED)
    ck("UNTRUSTED is a problem", V_UNTRUSTED in BAD, True)
    ck("UNTRUSTED ranks below MISMATCH", BAD.index(V_UNTRUSTED) > BAD.index(V_MISMATCH), True)
    ck("UNTRUSTED ranks above WARN", BAD.index(V_UNTRUSTED) < BAD.index(V_WARN), True)
    ck("a present refusal outranks a future expiry",
       evaluate("a", True, _cert("Sep 14 00:00:00 2026 GMT", ["a"]), NOW,
                error="self-signed certificate", browser_ok=False)["verdict"], V_UNTRUSTED)
    ck("but an expiry inside a trusted site still reports URGENT",
       evaluate("a", True, _cert("Sep 13 00:00:00 2026 GMT", ["a"]), NOW, browser_ok=True)["verdict"], V_URGENT)

    # --- anti-spam key ------------------------------------------------------
    ck("the key holds host and verdict", problem_key(exp), "drmanojagarwal.com:EXPIRED")
    ck("a worsening site is a NEW problem", problem_key(warn) == problem_key(exp), False)

    # --- BAD ordering drives priority --------------------------------------
    ck("EXPIRED outranks WARN", BAD.index(V_EXPIRED) < BAD.index(V_WARN), True)
    ck("OK is not a problem", V_OK in BAD, False)
    ck("SKIP is not a problem", V_SKIP in BAD, False)

    # --- the message ---------------------------------------------------------
    msg = build_message([exp, warn, ok, skip])
    ck("message counts only the problems", msg.splitlines()[0].startswith("CLINIC CERTIFICATES -- 2 site(s)"), True)
    ck("message names the expired site first", msg.splitlines()[2].startswith("* drmanojagarwal.com"), True)
    ck("message never names a healthy site", "a.dr-manoj.in" in msg, False)
    ck("message is plain ASCII-safe title", _ascii_header("Clinic certificates: attention needed"),
       "Clinic certificates: attention needed")

    # --- the site list itself ------------------------------------------------
    hosts = [s[0] for s in SITES]
    ck("nine vhosts are listed", len(SITES), 9)
    ck("no duplicate host in the list", len(hosts), len(set(hosts)))
    ck("the site that broke is watched", ("drmanojagarwal.com", True) in [(h, w) for h, w, _ in SITES], True)
    ck("the retired domain is not watched", ("drmanojagarwal.in", False) in [(h, w) for h, w, _ in SITES], True)
    ck("attendance is watched", ("attendance.dr-manoj.in", True) in [(h, w) for h, w, _ in SITES], True)
    ck("warn fires INSIDE CyberPanel's 15-day renewal window", WARN_DAYS < 15, True)
    ck("and leaves CyberPanel at least 4 days to do its job first", 15 - WARN_DAYS >= 4, True)
    ck("urgent is tighter than warn", URGENT_DAYS < WARN_DAYS, True)

    fails = [c for c in checks if not c[0]]
    for ok_, name, got, want in checks:
        if not ok_:
            print("  FAIL  %-52s got %r want %r" % (name, got, want))
    print("selftest: %d checks, %d failures" % (len(checks), len(fails)))
    return 1 if fails else 0


def main():
    p = argparse.ArgumentParser(description="Watch the clinic's certificates the way a browser sees them.")
    p.add_argument("--selftest", action="store_true", help="prove the logic offline; no network, no files, no sending")
    p.add_argument("--dry-run", action="store_true", help="check and print, but send nothing and save nothing")
    a = p.parse_args()
    if a.selftest:
        return selftest()
    try:
        return run(dry_run=a.dry_run)
    except Exception as e:
        try:
            send_ntfy("Clinic certificate watch could NOT run",
                      "The certificate watchman hit an error.\nError: %s\nTime: %s IST" % (e, stamp()),
                      priority="high")
        except Exception:
            pass
        log("FATAL %s" % e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
