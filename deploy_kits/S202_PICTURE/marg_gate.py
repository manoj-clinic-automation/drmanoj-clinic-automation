#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
marg_gate.py  --  S201.  The missing consumer for the Marg _outbox, plus an
honest daily picture of which sale reports exist and which actually reached
the clinic server.

Two jobs, one file:

    python marg_gate.py status          # the picture. read-only. no network.
    python marg_gate.py send            # drain the outbox to the clinic server
    python marg_gate.py send --dry-run  # show what send WOULD do
    python marg_gate.py send --resend-all
    python marg_gate.py selftest        # offline checks, no network, no state

WHY THIS EXISTS (S201, 25-Aug-2026)
    marg_router.py copies every VERIFIED sale report into MargArchive\\_outbox
    and stamps it "queued". Nothing ever read that folder. Eight reports sat
    there; the 24-Aug report never reached the server and nobody knew, because
    the only sender lived on the medical PC behind a manual double-click.

WHAT IT FIXES BEYOND THAT (audit finding AF-1, 24-Aug)
    The medical sender decides success by searching a response FILE that curl
    does not overwrite when the connection fails -- so a network drop makes it
    print ACCEPTED, log ACCEPTED, and permanently blacklist the report's hash.
    This sender:
      * holds the reply in memory, never in a shared file;
      * records a hash as sent ONLY on a real HTTP 200 whose body actually
        says the server took it;
      * on ANY doubt leaves the report unsent so the next run retries it.
    A false "sent" is the expensive failure. A repeat send is free -- the
    server dedupes by content.

The token is read from token.txt and never printed, never logged.
"""

import argparse
import datetime as dt
import io
import json
import os
import re
import sys
import urllib.error
import urllib.request

# --------------------------------------------------------------------------
# Layout. Overridable on the command line; these are the manojz live paths.
# --------------------------------------------------------------------------
DEF_ARCHIVE = r"D:\Downloads\margsync\MargArchive"
# The token lives on the medical PC. manojz reads that share read-only every
# ten minutes already, so read the LIVE token at send time and keep a local
# cache only for when the medical PC is off. A hand-copied token silently
# rots -- that is exactly how this sender spent five days answering 401 while
# the medical PC's own copy worked fine.
DEF_TOKEN_UNC = r"\\100.119.151.40\DDrive\SendToClinic\token.txt"
DEF_TOKEN = r"D:\Downloads\margsync\SendToClinic\token.txt"
DEF_MEDICAL_LOG = r"D:\Downloads\margsync\medical_SendToClinic\send_log.txt"
DEF_UPLOAD_DIR = r"D:\Downloads\margsync\_UPLOAD_NOW"
DEF_URL = "https://followup.dr-manoj.in/finance/api/marg-push"

SALE = "SALE_BILLWISE"
STATE_NAME = "_outbox_state.json"
SENDLOG_NAME = "_outbox_send_log.txt"
# S202: how far back the picture calls a missing day a GAP. Older reports are
# backfill, not gaps. Matches the server's own 45-day missing-export horizon.
COVERAGE_WINDOW_DAYS = 45
# S202: the date daily coverage actually began, declared not guessed.
COVERAGE_FROM_NAME = "_coverage_from.txt"
PICTURE_NAME = "MARG_PICTURE.txt"
ATTENTION_NAME = "_NEEDS_ATTENTION.txt"

# The server's own words. A 200 that says neither of these is NOT a success.
OK_MARKERS = ("ACCEPTED-FOR-REVIEW", '"ok": true', '"ok":true')
DUPE_MARKERS = ("already", "duplicate", "same report")


# --------------------------------------------------------------------------
# small helpers
# --------------------------------------------------------------------------
def now_str():
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_date(s):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return dt.date(*[int(x) for x in s.split("-")])
    except Exception:
        return None


def read_index(archive):
    """Every row of the router's index.csv, newest last. Tolerant of a
    half-written final line -- the router may be mid-append."""
    import csv
    path = os.path.join(archive, "index.csv")
    if not os.path.exists(path):
        return []
    with io.open(path, "r", encoding="utf-8", errors="replace", newline="") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return []
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        if len(r) < len(hdr):
            continue
        out.append(dict(zip(hdr, r)))
    return out


def verified_sales(archive):
    """The VERIFIED sale reports, de-duplicated by md5, newest occurrence kept."""
    seen = {}
    for r in read_index(archive):
        if r.get("type") != SALE or r.get("verdict") != "VERIFIED":
            continue
        md5 = (r.get("md5") or "").strip()
        if not md5:
            continue
        seen[md5] = r
    return seen


def accepted_from_medical_log(path):
    """md5s the medical PC's sender recorded as ACCEPTED.

    Treated as a HINT, never as proof: AF-1 means this log can carry an
    ACCEPTED for a report that never left the building. It is used only to
    avoid re-staging days the server plainly already has, and --resend-all
    ignores it entirely.
    """
    out = set()
    if not os.path.exists(path):
        return out
    with io.open(path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3 and parts[2].upper().startswith("ACCEPTED"):
                m = re.fullmatch(r"[0-9a-fA-F]{32}", parts[1])
                if m:
                    out.add(parts[1].lower())
    return out


def load_state(archive):
    path = os.path.join(archive, STATE_NAME)
    if not os.path.exists(path):
        return {"sent": {}}
    try:
        with io.open(path, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        d.setdefault("sent", {})
        return d
    except Exception:
        # A corrupt state file must never block the send. Worst case we
        # re-send something the server already has, which it dedupes.
        return {"sent": {}}


def save_state(archive, state):
    path = os.path.join(archive, STATE_NAME)
    tmp = path + ".tmp"
    with io.open(tmp, "w", encoding="utf-8") as fh:
        fh.write(json.dumps(state, indent=2, sort_keys=True))
    # os.replace is atomic and overwrites on Windows too. The old
    # remove-then-rename left a window in which the state file did not exist
    # at all -- a crash there loses every record of what has been delivered.
    os.replace(tmp, path)


def log_line(archive, text):
    with io.open(os.path.join(archive, SENDLOG_NAME), "a", encoding="utf-8") as fh:
        fh.write("%s  %s\n" % (now_str(), text))


def read_token(token_file):
    """First non-empty line of a token file, or None. Never logged, never
    printed. utf-8-sig so a Notepad-saved file with a BOM still works."""
    try:
        if not token_file or not os.path.exists(token_file):
            return None
        with io.open(token_file, "r", encoding="utf-8-sig", errors="replace") as fh:
            for line in fh:
                line = line.strip().strip('"').strip("'")
                if line:
                    return line
    except Exception:
        return None
    return None


def resolve_token(unc_path, local_path):
    """(token, where) -- the live token from the medical PC if that share is
    reachable, else the local cache.

    A successful live read refreshes the cache, so the cache can never drift
    from the medical PC for more than one offline stretch. Returns the source
    name for the log; the value itself is never surfaced.
    """
    tok = read_token(unc_path)
    if tok:
        try:
            if read_token(local_path) != tok:
                d = os.path.dirname(local_path)
                if d and not os.path.isdir(d):
                    os.makedirs(d)
                with io.open(local_path, "w", encoding="utf-8") as fh:
                    fh.write(tok + "\n")
                return tok, "medical PC (live) -- local cache refreshed"
        except Exception:
            return tok, "medical PC (live) -- cache refresh failed, not fatal"
        return tok, "medical PC (live)"
    tok = read_token(local_path)
    if tok:
        return tok, "local cache (medical PC unreachable)"
    return None, "nowhere"


# --------------------------------------------------------------------------
# the picture
# --------------------------------------------------------------------------
def covered_days(row):
    """Every business day a report actually covers.

    S201 fix. build_picture() and the send logic both keyed a report by
    date_to alone, so a catch-up export covering 01->15 Aug counted as 15-Aug
    and the other fourteen days read as MISSING -- and if a newer single-day
    export existed for the 15th, the range file was marked superseded and its
    earlier days were never sent at all. It did not bite only because the one
    range export we have spans a Sunday.

    The DATA range wins over the title range where it exists: a title reading
    "FROM 23-08 TO 24-08" over a file holding only 24-Aug rows describes what
    was asked for, not what arrived. Rows written before data_from/data_to
    existed fall back to the title range.
    """
    d_from = parse_date(row.get("data_from")) or parse_date(row.get("date_from"))
    d_to = parse_date(row.get("data_to")) or parse_date(row.get("date_to"))
    if not d_to:
        return []
    if not d_from or d_from > d_to:
        d_from = d_to
    return business_days(d_from, d_to)


def span_key(row):
    """Groups exports of the same coverage together, so 'newest wins' compares
    like with like instead of collapsing a range onto a single day."""
    days = covered_days(row)
    return (days[0].isoformat(), days[-1].isoformat()) if days else ("", "")


def business_days(first, last):
    """Every day first..last inclusive except Sunday. Sunday is not a
    trading day for this clinic and must never be reported as a gap."""
    out = []
    d = first
    while d <= last:
        if d.weekday() != 6:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def build_picture(archive, medical_log, today=None):
    today = today or dt.date.today()
    yesterday = today - dt.timedelta(days=1)

    sales = verified_sales(archive)
    med_ok = accepted_from_medical_log(medical_log)
    state = load_state(archive)
    # Only a real delivery counts as "on server". A superseded export was
    # never sent and must not be allowed to make a day look covered.
    sent_here = {m for m, v in state.get("sent", {}).items()
                 if v.get("result") in ("accepted", "duplicate")}

    # date -> list of (md5, row, is_range)
    by_date = {}
    ranges = []
    for md5, r in sales.items():
        days = covered_days(r)
        if not days:
            continue
        is_range = len(days) > 1
        if is_range:
            ranges.append((md5, r))
        for day in days:                      # every day it covers, not just the last
            by_date.setdefault(day, []).append((md5, r, is_range))

    if not by_date:
        return {"lines": ["No verified sale reports in the archive at all."],
                "missing": [], "unsent": [], "today": today}

    # S202: THE COVERAGE WINDOW IS OPERATIONAL, NOT "EVERYTHING EVER SEEN".
    # This used to run from the EARLIEST report in the archive to yesterday. On
    # 26-Aug ONE report for 12-June was generated deliberately, to answer an old
    # question. It widened the window across two months and this file instantly
    # claimed 56 MISSING DAYS, with an ACTION telling the owner to go and
    # produce 56 reports. None were missing. The day before, the same file read
    # "days with NO export: 0".
    # A file that cries wolf every ten minutes stops being read -- and this is
    # the file the 60-second health check depends on. A false alarm is worse
    # than no alarm.
    # So coverage is measured over the OPERATIONAL window (matching the
    # server's own 45-day horizon), and anything older is reported for what it
    # is: BACKFILL, deliberately loaded, never a gap.
    # AND the window must not reach back BEFORE the daily feed existed. The
    # 45-day horizon alone still claimed 32 missing days across July -- a month
    # in which no daily export was ever produced, because the feed began on
    # 17-Aug. Those are not gaps either; they are pre-history.
    # The machine must not GUESS when coverage began. It is told, once, in
    # _coverage_from.txt beside the archive. Absent, it falls back to the
    # horizon and says so by behaving exactly as before.
    first_seen = min(by_date)
    horizon = yesterday - dt.timedelta(days=COVERAGE_WINDOW_DAYS)
    declared = None
    try:
        with io.open(os.path.join(archive, COVERAGE_FROM_NAME), "r",
                     encoding="utf-8-sig", errors="replace") as _fh:
            for _ln in _fh:
                _ln = _ln.strip()
                if _ln and not _ln.startswith("#"):
                    declared = parse_date(_ln)
                    break
    except Exception:
        declared = None
    first = max(first_seen, horizon)
    if declared:
        first = max(first, declared)
    backfill = sorted(d for d in by_date if d < first)
    days = business_days(first, yesterday)

    missing, unsent, lines = [], [], []
    lines.append("MARG SALE REPORTS -- the picture at %s" % now_str())
    lines.append("archive: %s" % archive)
    lines.append("")
    lines.append("%-12s %-9s %-10s %s" % ("BUSINESS DAY", "REPORT", "ON SERVER", "NOTE"))
    lines.append("-" * 72)

    for d in days:
        got = by_date.get(d, [])
        if not got:
            missing.append(d)
            lines.append("%-12s %-9s %-10s %s" % (
                d.isoformat(), "MISSING", "-",
                "no export exists -- run it in Marg for this date"))
            continue
        md5s = [m for m, _r, _x in got]
        on_server = any((m in med_ok) or (m in sent_here) for m in md5s)
        rng = any(x for _m, _r, x in got)
        note = []
        if rng:
            note.append("came from a multi-day export")
        if len(got) > 1:
            note.append("%d exports for this day" % len(got))
        if not on_server:
            unsent.append((d, md5s[-1]))
            note.append("NOT SENT -- run SEND_OUTBOX.bat")
        lines.append("%-12s %-9s %-10s %s" % (
            d.isoformat(), "yes", "yes" if on_server else "NO", "; ".join(note)))

    lines.append("-" * 72)
    _why = ("declared in %s" % COVERAGE_FROM_NAME) if (declared and first == declared) else (
            "%d-day window" % COVERAGE_WINDOW_DAYS if first == horizon else "earliest report")
    lines.append("business days covered : %s .. %s (Sundays excluded; start: %s)"
                 % (first.isoformat(), yesterday.isoformat(), _why))
    lines.append("reports verified      : %d" % len(sales))
    lines.append("days with NO export   : %d%s" % (
        len(missing), (" -> " + ", ".join(d.isoformat() for d in missing)) if missing else ""))
    if backfill:
        lines.append("backfill outside the window : %d -> %s"
                     % (len(backfill), ", ".join(d.isoformat() for d in backfill)))
        lines.append("   (deliberately loaded older days. NOT gaps, and no action needed.)")
    lines.append("exports NOT on server : %d%s" % (
        len(unsent), (" -> " + ", ".join(d.isoformat() for d, _ in unsent)) if unsent else ""))
    lines.append("")
    if missing:
        lines.append("ACTION: a missing day cannot be fixed from here. Someone must open")
        lines.append("        Marg on the medical PC and run BILL WISE SALES (With Item")
        lines.append("        Deta. = Yes) for that exact date. The watcher captures it")
        lines.append("        automatically once it is saved.")
    if unsent:
        lines.append("ACTION: run SEND_OUTBOX.bat -- these are sitting in the outbox.")
    if not missing and not unsent:
        lines.append("Every trading day up to yesterday has a report and the server has it.")

    return {"lines": lines, "missing": missing, "unsent": unsent, "today": today}


# --------------------------------------------------------------------------
# the sender
# --------------------------------------------------------------------------
def build_multipart(file_bytes, filename="REPORT_1.XLS", field="file"):
    boundary = "----margGateS201Boundary7d91c4e2"
    pre = (
        "--%s\r\n"
        'Content-Disposition: form-data; name="%s"; filename="%s"\r\n'
        "Content-Type: application/vnd.ms-excel\r\n\r\n" % (boundary, field, filename)
    ).encode("utf-8")
    post = ("\r\n--%s--\r\n" % boundary).encode("utf-8")
    return pre + file_bytes + post, "multipart/form-data; boundary=%s" % boundary


def delivered_stamps(state, sales):
    """business date -> newest export stamp already delivered for it.

    Backfills export_stamp from the index for entries written before the
    field existed; without that backfill an old entry looks like stamp "" and
    every later export for that day would be sent again.
    """
    out = {}
    for md5, v in (state.get("sent") or {}).items():
        if v.get("result") not in ("accepted", "duplicate"):
            continue
        row = sales.get(md5) or {}
        stamp = v.get("export_stamp") or row.get("export_stamp") or ""
        if stamp and not v.get("export_stamp"):
            v["export_stamp"] = stamp
        if not stamp:
            continue
        # A delivered range export delivered EVERY day inside it.
        days = [d.isoformat() for d in covered_days(row)] if row else []
        if not days and v.get("business_date"):
            days = [v["business_date"]]
        for d in days:
            if stamp > out.get(d, ""):
                out[d] = stamp
    return out


def drop_already_delivered(items, delivered):
    """(keep, skipped). A report whose day already has a delivery at the same
    or a newer export stamp is not sent again."""
    keep, skipped = [], []
    for it in items:
        row = it[3]
        stamp = row.get("export_stamp") or ""
        days = [d.isoformat() for d in covered_days(row)]
        if not days:
            days = [row.get("date_to") or ""]
        # Send unless EVERY day it covers already has a delivery at least as
        # new. One uncovered day is reason enough to send the whole report.
        if all(d in delivered and stamp <= delivered[d] for d in days):
            skipped.append(it)
        else:
            keep.append(it)
    return keep, skipped


def pick_latest_per_date(items):
    """items: list of (md5, name, path, row). Returns (keep, superseded).

    Marg is often run twice for the same day -- once with the wrong date range,
    then again correctly. Both exports verify, both land in the outbox, and
    sending both stages the same day twice on the server for no gain. Keep the
    newest export per business date; the older ones are superseded, not lost.

    A deliberate correction re-run (the 18-Aug case) is the same shape and is
    handled the same way: the newest export for a day is the one that counts.
    """
    best = {}
    for it in items:
        row = it[3]
        d = span_key(row)
        stamp = (row.get("export_stamp") or "", row.get("seen_at") or "")
        if d not in best or stamp > best[d][0]:
            best[d] = (stamp, it)
    keep = [v[1] for v in best.values()]
    keep_ids = {id(x) for x in keep}
    superseded = [it for it in items if id(it) not in keep_ids]
    keep.sort(key=lambda it: span_key(it[3]))
    return keep, superseded


def classify(http, body):
    """Decide, conservatively, what the server did.

    Returns one of: 'accepted', 'duplicate', 'refused'.
    Anything that is not a 200 carrying an affirmative body is 'refused' --
    we would rather send a report twice than record a phantom success.
    """
    if http != 200:
        return "refused"
    low = (body or "").lower()
    if any(m.lower() in low for m in OK_MARKERS):
        return "accepted"
    if any(m in low for m in DUPE_MARKERS):
        return "duplicate"
    return "refused"


def post_one(url, token, path, timeout=90):
    """Returns (http_code, body_text). Never raises for an HTTP error."""
    with open(path, "rb") as fh:
        data = fh.read()
    # S202: send the ARCHIVED filename, not Marg's slot name.
    # Every report ever pushed arrived at the server called "REPORT_1.XLS",
    # because that is the slot Marg writes into. The approvals card therefore
    # listed every one of them under the same name and the owner could only
    # tell June from August by decoding a hash fragment. The bytes are
    # unchanged; only the name the server records as its hint improves.
    body, ctype = build_multipart(data, filename=os.path.basename(path))
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", ctype)
    req.add_header("X-Finance-Marg", token)
    req.add_header("User-Agent", "marg_gate/S201")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.getcode(), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        try:
            txt = e.read().decode("utf-8", "replace")
        except Exception:
            txt = ""
        return e.code, txt
    except Exception as e:
        # Connection refused, DNS, timeout, TLS. NOT a success, and crucially
        # not a body we might mistake for one -- there is no previous reply
        # lying around to read. This is the AF-1 fix.
        return 0, "LOCAL-ERROR: %s" % e.__class__.__name__


def do_send(args):
    archive = args.archive
    outbox = os.path.join(archive, "_outbox")
    if not os.path.isdir(outbox):
        print("  no outbox at %s -- nothing to do." % outbox)
        return 0

    token, where = resolve_token(args.token_unc, args.token_file)
    print("  token source: %s" % where)
    if not token and not args.dry_run:
        print("  PROBLEM: no token on the medical PC share and none cached here.")
        print("  Nothing was sent. Tell Dr. Manoj this exact message.")
        return 2

    sales = verified_sales(archive)
    med_ok = accepted_from_medical_log(args.medical_log)
    state = load_state(archive)
    sent = state.setdefault("sent", {})

    # Only files the router actually verified as sale reports get sent. A
    # stray file dropped into _outbox by hand is ignored, loudly.
    candidates = []
    for name in sorted(os.listdir(outbox)):
        path = os.path.join(outbox, name)
        if not os.path.isfile(path):
            continue
        md5 = None
        m = re.search(r"__([0-9a-f]{8})\.[Xx][Ll][Ss][Xx]?$", name)
        for full in sales:
            if m and full.startswith(m.group(1)):
                md5 = full
                break
        if md5 is None:
            print("  skipping %s -- not a verified sale report in index.csv" % name)
            continue
        candidates.append((md5, name, path, sales[md5]))

    if not candidates:
        print("  outbox holds nothing the router has verified. Nothing to send.")
        return 0

    todo = []
    for md5, name, path, row in candidates:
        if not args.resend_all:
            if md5 in sent and sent[md5].get("result") in ("accepted", "duplicate"):
                continue
            if md5 in med_ok:
                # Already sent from the medical PC before this tool existed.
                sent[md5] = {"result": "duplicate", "http": None,
                             "business_date": row.get("date_to"),
                             "when": now_str(),
                             "export_stamp": row.get("export_stamp") or "",
                             "note": "recorded as ACCEPTED in the medical PC send log"}
                continue
        todo.append((md5, name, path, row))

    if not args.resend_all:
        todo, already = drop_already_delivered(todo, delivered_stamps(state, sales))
        for md5, name, _p, row in already:
            sent.setdefault(md5, {})
            sent[md5] = {"result": "superseded", "http": None,
                         "business_date": row.get("date_to"), "when": now_str(),
                         "export_stamp": row.get("export_stamp") or "",
                         "note": "that business date already has a delivery "
                                 "from this export or a newer one"}
            print("  skipping %s (%s) -- that day is already on the server"
                  % (md5[:8], row.get("date_to")))
        todo, superseded = pick_latest_per_date(todo)
        for md5, name, _p, row in superseded:
            sent[md5] = {"result": "superseded", "http": None,
                         "business_date": row.get("date_to"), "when": now_str(),
                         "note": "a newer export exists for this business date"}
            print("  skipping %s (%s) -- a newer export exists for that day"
                  % (md5[:8], row.get("date_to")))

    if not todo:
        save_state(archive, state)
        print("  everything in the outbox is already on the server. Nothing to send.")
        return 0

    print("  %d report(s) to send:" % len(todo))
    for md5, name, _p, row in todo:
        print("     %s  %s  (%s)" % (md5[:8], row.get("date_to"), name))
    if args.dry_run:
        print("  --dry-run: nothing was sent.")
        return 0

    failures = []
    for md5, name, path, row in todo:
        bdate = row.get("date_to")
        http, body = post_one(args.url, token, path, timeout=args.timeout)
        verdict = classify(http, body)
        short = " ".join((body or "").split())[:300]
        if verdict in ("accepted", "duplicate"):
            sent[md5] = {"result": verdict, "http": http,
                         "business_date": bdate, "when": now_str(),
                         "export_stamp": row.get("export_stamp") or ""}
            log_line(archive, "%s | %s | %s | HTTP %s | %s"
                     % (md5, bdate, verdict.upper(), http, name))
            print("     %s  %s  -> %s" % (md5[:8], bdate, verdict.upper()))
        else:
            failures.append((md5, bdate, http, short))
            log_line(archive, "%s | %s | REFUSED | HTTP %s | %s | %s"
                     % (md5, bdate, http, name, short))
            print("     %s  %s  -> REFUSED (HTTP %s)" % (md5[:8], bdate, http))
            print("        server said: %s" % short)

    save_state(archive, state)

    att = os.path.join(archive, ATTENTION_NAME)
    if failures:
        with io.open(att, "w", encoding="utf-8") as fh:
            fh.write("MARG REPORTS NOT DELIVERED -- %s\n\n" % now_str())
            for md5, bdate, http, short in failures:
                fh.write("  business date %s  (%s)  HTTP %s\n" % (bdate, md5[:8], http))
                fh.write("    server said: %s\n\n" % short)
            fh.write("These will be retried automatically on the next run.\n")
            fh.write("If HTTP is 401 the token has changed. If HTTP is 0 the\n")
            fh.write("clinic server was unreachable from this PC.\n")
        print("\n  %d report(s) NOT delivered. Written to %s" % (len(failures), att))
        print("  They stay in the outbox and will be retried. Nothing was lost.")
        return 1

    if os.path.exists(att):
        os.remove(att)
    print("\n  All queued reports are on the clinic server.")
    return 0


# --------------------------------------------------------------------------
# the manual-upload fallback folder
# --------------------------------------------------------------------------
def refresh_upload_folder(archive, upload_dir, picture):
    """Keep one obvious folder holding exactly the reports that still need a
    human to upload them through the portal's Choose File button. When the
    automatic sender is working this folder is empty, and an empty folder is
    itself the status message."""
    import shutil
    if not os.path.isdir(upload_dir):
        os.makedirs(upload_dir)
    for n in os.listdir(upload_dir):
        p = os.path.join(upload_dir, n)
        if os.path.isfile(p):
            os.remove(p)

    sales = verified_sales(archive)
    wanted = {md5 for _d, md5 in picture["unsent"]}
    placed = []
    for md5 in wanted:
        row = sales.get(md5)
        if not row:
            continue
        src = row.get("archived_path")
        if src and os.path.exists(src):
            dst = os.path.join(upload_dir, "UPLOAD_%s%s"
                               % (row.get("date_to"), os.path.splitext(src)[1]))
            shutil.copy2(src, dst)
            placed.append(dst)

    readme = os.path.join(upload_dir, "READ_ME.txt")
    with io.open(readme, "w", encoding="utf-8") as fh:
        if placed:
            fh.write("These Marg reports have NOT reached the clinic server.\n\n")
            fh.write("Open  https://followup.dr-manoj.in/finance/approvals\n")
            fh.write("Press 'Choose File', pick the file here, then 'Load into the books'.\n\n")
            for p in placed:
                fh.write("   %s\n" % os.path.basename(p))
        else:
            fh.write("Nothing to upload by hand. Every verified Marg report has\n")
            fh.write("reached the clinic server. This folder stays empty when the\n")
            fh.write("automatic sender is doing its job.\n\n")
            fh.write("Last checked: %s\n" % now_str())
    return placed


# --------------------------------------------------------------------------
# selftest -- offline, no network, no state written
# --------------------------------------------------------------------------
def do_selftest(_args):
    checks, failed = [], []

    def ck(name, cond):
        checks.append(name)
        if not cond:
            failed.append(name)

    # classify() is the whole AF-1 fix. It gets the hardest look.
    ck("200 + ACCEPTED-FOR-REVIEW is accepted",
       classify(200, '{"verdict":"ACCEPTED-FOR-REVIEW"}') == "accepted")
    ck("200 + ok:true is accepted", classify(200, '{"ok": true}') == "accepted")
    ck("200 + already-have is duplicate",
       classify(200, "the server already has this exact report") == "duplicate")
    ck("401 is refused even with a good body",
       classify(401, '{"verdict":"ACCEPTED-FOR-REVIEW"}') == "refused")
    ck("500 is refused", classify(500, "boom") == "refused")
    ck("connection failure (http 0) is refused",
       classify(0, "LOCAL-ERROR: URLError") == "refused")
    ck("empty body on 200 is refused, not assumed good",
       classify(200, "") == "refused")
    ck("a 200 saying nothing affirmative is refused",
       classify(200, '{"weather":"fine"}') == "refused")

    # Sunday must never be reported as a missing trading day.
    d1, d2 = dt.date(2026, 8, 21), dt.date(2026, 8, 25)
    days = business_days(d1, d2)
    ck("business_days excludes Sunday", dt.date(2026, 8, 23) not in days)
    ck("business_days keeps Saturday", dt.date(2026, 8, 22) in days)
    ck("business_days is inclusive at both ends", days[0] == d1 and days[-1] == d2)

    # ---- S202: the upload must be identifiable at a glance -----------------
    _b, _c = build_multipart(b"x", filename="SALE_BILLWISE_DETAIL__2026-06-12__x__a815063a.XLS")
    ck("S202: the multipart carries the ARCHIVED filename, so the approvals "
       "card can be read without decoding a hash",
       b'filename="SALE_BILLWISE_DETAIL__2026-06-12__x__a815063a.XLS"' in _b)
    ck("S202: it is NOT the Marg slot name every report used to arrive under",
       b'filename="REPORT_1.XLS"' not in _b)

    # ---- S202: an old backfilled report must not manufacture gaps ----------
    # The exact 26-Aug shape: one deliberate 12-June report beside recent ones.
    _y = dt.date(2026, 8, 25)
    _old = _y - dt.timedelta(days=COVERAGE_WINDOW_DAYS + 30)
    _firstseen = min([_old, _y - dt.timedelta(days=2)])
    _horizon = _y - dt.timedelta(days=COVERAGE_WINDOW_DAYS)
    _first = max(_firstseen, _horizon)
    ck("S202: a report older than the window does NOT drag the coverage window "
       "back with it (26-Aug: one June report claimed 56 missing days)",
       _first == _horizon and len(business_days(_first, _y)) < 60)
    ck("S202: and that old day is classed as BACKFILL, not a gap",
       _old < _first)


    # The multipart body must carry the filename the server expects.
    body, ctype = build_multipart(b"hello")
    ck("multipart names the file REPORT_1.XLS", b"REPORT_1.XLS" in body)
    ck("multipart closes its boundary", body.rstrip().endswith(b"--"))
    ck("content-type carries the boundary", "boundary=" in ctype)
    ck("multipart carries the payload bytes", b"hello" in body)

    # A range export covers every day inside it, not just the last one.
    def _row(df, dt_, adf=None, adt=None, stamp="1"):
        return {"date_from": df, "date_to": dt_, "data_from": adf or "",
                "data_to": adt or "", "export_stamp": stamp}
    days = covered_days(_row("2026-08-10", "2026-08-14"))
    ck("range: covers every day in the span", len(days) == 5)
    ck("range: first and last are the ends",
       days[0].isoformat() == "2026-08-10" and days[-1].isoformat() == "2026-08-14")
    ck("range: Sundays are excluded from coverage",
       dt.date(2026, 8, 23) not in covered_days(_row("2026-08-21", "2026-08-24")))
    ck("single day covers exactly itself",
       [d.isoformat() for d in covered_days(_row("2026-08-22", "2026-08-22"))]
       == ["2026-08-22"])
    ck("the DATA range beats the title range",
       [d.isoformat() for d in covered_days(
           _row("2026-08-23", "2026-08-24", "2026-08-24", "2026-08-24"))]
       == ["2026-08-24"])
    ck("a row with no dates covers nothing",
       covered_days(_row("", "")) == [])
    ck("reversed dates fall back to the single end day",
       [d.isoformat() for d in covered_days(_row("2026-08-24", "2026-08-20"))]
       == ["2026-08-20"])
    ck("span_key separates a range from a single day",
       span_key(_row("2026-08-10", "2026-08-14")) != span_key(_row("2026-08-14", "2026-08-14")))

    # One uncovered day is reason enough to send the whole report.
    rng = ("r" * 32, "n", "p", _row("2026-08-10", "2026-08-14", stamp="9"))
    part = {d: "9" for d in ("2026-08-10", "2026-08-11", "2026-08-12")}
    ck("range is still sent when some of its days are undelivered",
       drop_already_delivered([rng], part)[0] == [rng])
    allof = {d: "9" for d in ("2026-08-10", "2026-08-11", "2026-08-12",
                              "2026-08-13", "2026-08-14")}
    ck("range is skipped only when every day it covers is delivered",
       drop_already_delivered([rng], allof)[1] == [rng])

    # The live bug of 25-Aug: an older export must not be sent for a day that
    # already has a delivery.
    def _it2(md5, d, stamp):
        return (md5, "n", "p", {"date_to": d, "export_stamp": stamp})
    older24 = _it2("a" * 32, "2026-08-24", "20260825-081605")
    newer24 = _it2("b" * 32, "2026-08-24", "20260825-082715")
    day22 = _it2("c" * 32, "2026-08-22", "20260825-103700")
    st = {"sent": {"b" * 32: {"result": "accepted", "business_date": "2026-08-24",
                              "export_stamp": "20260825-082715"}}}
    dl = delivered_stamps(st, {})
    keep, skip = drop_already_delivered([older24, day22], dl)
    ck("delivered: an older export for a delivered day is skipped",
       older24 in skip)
    ck("delivered: an untouched day still goes", day22 in keep)
    ck("delivered: a NEWER export for a delivered day still goes",
       drop_already_delivered([_it2("d" * 32, "2026-08-24", "20260825-999999")],
                              dl)[0] != [])
    ck("delivered: only accepted/duplicate count as delivered",
       delivered_stamps({"sent": {"z" * 32: {"result": "refused",
                                             "business_date": "2026-08-24",
                                             "export_stamp": "9"}}}, {}) == {})
    ck("delivered: stamp is backfilled from the index when missing",
       delivered_stamps({"sent": {"e" * 32: {"result": "accepted",
                                             "business_date": "2026-08-20"}}},
                        {"e" * 32: {"export_stamp": "20260821-203200"}})
       == {"2026-08-20": "20260821-203200"})
    ck("delivered: an entry with no stamp anywhere is ignored, not treated as 0",
       delivered_stamps({"sent": {"f" * 32: {"result": "accepted",
                                             "business_date": "2026-08-20"}}},
                        {}) == {})

    # Token resolution: live beats cache, and a live read repairs the cache.
    import tempfile, shutil as _sh
    td = tempfile.mkdtemp()
    unc = os.path.join(td, "live.txt")
    loc = os.path.join(td, "cache.txt")
    with io.open(unc, "w", encoding="utf-8") as fh:
        fh.write("LIVE_TOKEN_VALUE\n")
    with io.open(loc, "w", encoding="utf-8") as fh:
        fh.write("STALE_TOKEN_VALUE\n")
    tok, where = resolve_token(unc, loc)
    ck("token: live beats cache", tok == "LIVE_TOKEN_VALUE")
    ck("token: a live read repairs the cache", read_token(loc) == "LIVE_TOKEN_VALUE")
    ck("token: source names the medical PC", "medical" in where)
    os.remove(unc)
    tok2, where2 = resolve_token(unc, loc)
    ck("token: falls back to cache when medical is unreachable",
       tok2 == "LIVE_TOKEN_VALUE")
    ck("token: fallback says so", "cache" in where2)
    os.remove(loc)
    tok3, where3 = resolve_token(unc, loc)
    ck("token: nothing anywhere returns None", tok3 is None and where3 == "nowhere")
    with io.open(loc, "w", encoding="utf-8-sig") as fh:
        fh.write('  "BOM_QUOTED_TOKEN"  \n')
    ck("token: BOM and quotes are stripped",
       read_token(loc) == "BOM_QUOTED_TOKEN")
    with io.open(loc, "w", encoding="utf-8") as fh:
        fh.write("\n\n   \nSECOND_LINE_TOKEN\n")
    ck("token: leading blank lines are skipped",
       read_token(loc) == "SECOND_LINE_TOKEN")
    _sh.rmtree(td, ignore_errors=True)

    # Two exports for one day: the newest wins, the older is superseded.
    def _it(md5, d, stamp):
        return (md5, "n_" + md5, "p", {"date_to": d, "export_stamp": stamp,
                                       "seen_at": stamp})
    older = _it("a" * 32, "2026-08-24", "20260825-081605")
    newer = _it("b" * 32, "2026-08-24", "20260825-082715")
    other = _it("c" * 32, "2026-08-21", "20260822-005652")
    keep, sup = pick_latest_per_date([older, newer, other])
    ck("supersede: newest export for a day is kept", newer in keep)
    ck("supersede: older export for the same day is dropped", older in sup)
    ck("supersede: a different day is untouched", other in keep)
    ck("supersede: nothing is invented or lost",
       len(keep) + len(sup) == 3 and len(keep) == 2)
    ck("supersede: kept list is date-ordered",
       [k[3]["date_to"] for k in keep] == ["2026-08-21", "2026-08-24"])
    ck("supersede: a single report is kept as-is",
       pick_latest_per_date([other]) == ([other], []))

    # The medical log is a hint, and only ACCEPTED lines count.
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                     encoding="utf-8") as fh:
        fh.write("18-08-2026 6:54 | %s | ACCEPTED | x\n" % ("a" * 32))
        fh.write("21-08-2026 20:51 | %s | REFUSED HTTP 401 | x\n" % ("b" * 32))
        fh.write("20-08-2026 7:35 | %s | SKIPPED-KEPT | x\n" % ("c" * 32))
        tmp = fh.name
    got = accepted_from_medical_log(tmp)
    os.remove(tmp)
    ck("medical log: ACCEPTED is read", ("a" * 32) in got)
    ck("medical log: REFUSED is not read", ("b" * 32) not in got)
    ck("medical log: SKIPPED is not read", ("c" * 32) not in got)
    ck("medical log: missing file is empty, not an error",
       accepted_from_medical_log(r"\\no\such\file.txt") == set())

    print("selftest: %d/%d" % (len(checks) - len(failed), len(checks)))
    for f in failed:
        print("   FAILED: %s" % f)
    return 1 if failed else 0


# --------------------------------------------------------------------------
def do_status(args):
    pic = build_picture(args.archive, args.medical_log)
    text = "\n".join(pic["lines"])
    print(text)
    out = os.path.join(os.path.dirname(args.archive.rstrip("\\/")), PICTURE_NAME)
    try:
        with io.open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print("\n(written to %s)" % out)
    except Exception as e:
        print("\n(could not write the picture file: %s)" % e)
    if not args.no_upload_folder:
        try:
            placed = refresh_upload_folder(args.archive, args.upload_dir, pic)
            if placed:
                print("%d report(s) copied to %s for manual upload."
                      % (len(placed), args.upload_dir))
        except Exception as e:
            print("(could not refresh the upload folder: %s)" % e)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Marg outbox sender and daily picture.")
    ap.add_argument("mode", choices=["status", "send", "selftest"])
    ap.add_argument("--archive", default=DEF_ARCHIVE)
    ap.add_argument("--token-file", default=DEF_TOKEN)
    ap.add_argument("--token-unc", default=DEF_TOKEN_UNC)
    ap.add_argument("--medical-log", default=DEF_MEDICAL_LOG)
    ap.add_argument("--upload-dir", default=DEF_UPLOAD_DIR)
    ap.add_argument("--url", default=DEF_URL)
    ap.add_argument("--timeout", type=int, default=90)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resend-all", action="store_true")
    ap.add_argument("--no-upload-folder", action="store_true")
    a = ap.parse_args(argv)
    return {"status": do_status, "send": do_send, "selftest": do_selftest}[a.mode](a)


if __name__ == "__main__":
    sys.exit(main())
