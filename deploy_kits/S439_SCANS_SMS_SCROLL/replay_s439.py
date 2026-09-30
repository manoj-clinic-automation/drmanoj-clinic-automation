#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""replay_s439.py -- kit S439_SCANS_SMS_SCROLL (F-660). The phone's earlier posts, read again through the mended door.

The macro on the owner's phone sends each bank SMS as the bare query string of the door's address. The door read only a
field called 'text', so every post was refused with an empty text (and before S405 dropped without a trace) -- but the web
server's own access log still holds the address of every post. This reads those log lines (READ ONLY) and gives each post
the door answered 200 (the key was right) to bank_sms.take() -- the door's own code -- with the time the phone posted it.
The refused note of the same second, kept with no text, is replaced by what the door now makes of the post.

It prints outcomes only: never an SMS text, an amount, an account or the key. It runs ONCE per database (setting
bank_sms.s439_replay) and says so when asked again.

  --app DIR    the finance folder whose bank_sms.py is used
  --db PATH    finance.db (the live one at install; a scratch copy in the walk and the dry run)
  --log PATH   the web server's access log (repeat for more; a .gz is read too; a missing file is skipped)
"""
import argparse
import datetime as dt
import gzip
import io
import os
import re
import sqlite3
import sys

LINE_RE = re.compile(r'\[(\d{2})/([A-Za-z]{3})/(\d{4}):(\d{2}):(\d{2}):(\d{2}) [+-]\d{4}\] "POST /finance/api/bank-sms\?(\S*) HTTP/[\d.]+" (\d{3}) ')
MONTHS = {m: i + 1 for i, m in enumerate(("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"))}
PLACEHOLDER_RE = re.compile(r"^[\[{]\s*sms[_ ]?(message|number|text)\s*[\]}]$", re.I)      # the macro's own unfilled magic text
MARK = "bank_sms.s439_replay"


class _Post(object):
    """What read_post() needs of a request, built from a log line: only the query string."""
    form = {}
    mimetype = ""

    def __init__(self, qs):
        self.query_string = qs.encode("utf-8")

    def get_data(self, cache=True, as_text=False):
        return "" if as_text else b""

    def get_json(self, force=False, silent=False):
        return None


def say(line):
    try:
        print(line)
    except UnicodeEncodeError:                         # a shell with no UTF-8 locale
        print(line.encode("ascii", "replace").decode("ascii"))


def posts(paths):
    out = []
    for p in paths:
        if not os.path.isfile(p):
            continue
        fh = gzip.open(p, "rt", encoding="utf-8", errors="replace") if p.endswith(".gz") else io.open(p, "r", encoding="utf-8", errors="replace")
        with fh:
            for line in fh:
                if "api/bank-sms?" not in line:
                    continue
                m = LINE_RE.search(line)
                if not m or m.group(8) != "200" or m.group(2) not in MONTHS:
                    continue
                stamp = dt.datetime(int(m.group(3)), MONTHS[m.group(2)], int(m.group(1)), int(m.group(4)), int(m.group(5)), int(m.group(6)))
                out.append((stamp, m.group(7)))
    return sorted(set(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", required=True)
    ap.add_argument("--db", required=True)
    ap.add_argument("--log", action="append", default=[])
    a = ap.parse_args()
    sys.path.insert(0, a.app)
    import bank_sms as bs                              # noqa: E402
    if not hasattr(bs, "take") or not hasattr(bs, "read_post"):
        print("replay_s439: %s/bank_sms.py is not the S439 door -- nothing replayed" % a.app)
        return 1
    con = sqlite3.connect(a.db, timeout=60)
    con.row_factory = sqlite3.Row
    bs._ensure(con)
    done = con.execute("SELECT value FROM setting WHERE key=?", (MARK,)).fetchone()
    if done:
        print("replay_s439: already replayed on this database (%s) -- nothing done" % done[0])
        return 0
    found = posts(a.log)
    tally, lines, replaced = {}, [], 0
    for stamp, qs in found:
        text, sender, fields = bs.read_post(_Post(qs))
        if not text.strip() or PLACEHOLDER_RE.match(text.strip()):
            tally["a test post of the macro (no SMS in it)"] = tally.get("a test post of the macro (no SMS in it)", 0) + 1
            continue
        at = stamp.strftime("%Y-%m-%d %H:%M:%S")
        lo, hi = (stamp - dt.timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S"), (stamp + dt.timedelta(seconds=2)).strftime("%Y-%m-%d %H:%M:%S")
        cur = con.execute("DELETE FROM bank_sms_ignored WHERE masked_text='' AND phone_sender='' AND received_at BETWEEN ? AND ?", (lo, hi))
        replaced += cur.rowcount
        out, _code = bs.take(con, text, sender, at, (fields + " -- replayed from the web log by S439")[:160])
        if out.get("stored") and out.get("bank") == "YESBANK":
            what = "Yes Bank %s stored" % bs.KIND_WORDS.get(out.get("kind"), out.get("kind"))
            line = "%s  %s · SMS date %s%s" % (at, what, out.get("sms_date"), (" · matched to pay month %s" % out["matched_month"]) if out.get("matched_month") else "")
        elif out.get("stored"):
            what = "ICICI settlement stored (%s)" % out.get("unit")
            line = "%s  %s · business day %s · read %s" % (at, what, out.get("business_date"), out.get("parse_grade"))
        else:
            r = con.execute("SELECT bank_guess, reason FROM bank_sms_ignored WHERE received_at=? ORDER BY id DESC LIMIT 1", (at,)).fetchone()
            what = "ignored with its reason (%s)" % (r[0] if r else "?")
            line = "%s  ignored · %s · %s" % (at, r[0] if r else "?", r[1] if r else "?")
        tally[what] = tally.get(what, 0) + 1
        lines.append(line)
    note = "%s: %d post(s) in the log, %d replayed, %d empty refused note(s) replaced" % (
        dt.datetime.now().replace(microsecond=0).isoformat(), len(found), len(lines), replaced)
    con.execute("INSERT INTO setting (key, value, note) VALUES (?,?,?)", (MARK, note, "S439: the web log's earlier phone posts were replayed through the door once"))
    con.commit()
    say("replay_s439: %s" % note)
    for ln in lines:
        say("  " + ln)
    for k in sorted(tally):
        say("  = %d × %s" % (tally[k], k))
    return 0


if __name__ == "__main__":
    sys.exit(main())
