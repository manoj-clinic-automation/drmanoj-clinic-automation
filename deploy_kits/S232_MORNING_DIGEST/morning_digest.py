#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
morning_digest.py  --  S232  --  ONE push a morning, and it is the owner's idea.

    "we can think of NTFY of doing more things ... This could be a place where the
     notification occurs so that the notification layer is this NTFY and not a
     buried portal page or a small tile out there."

THE RULE THIS OBEYS (S232_NOTIFICATION_LAYER_PLAN §1)
    The push carries what is TIME-BOUND or NEEDS HIS WORD. The page carries state.
    Every push names the page it came from.

    A push cannot show what is still outstanding, cannot be ticked, and is gone
    once swiped. The moment it carries routine state it becomes wallpaper -- and
    the one that mattered goes invisible with it. This project has recorded that
    failure twice in its own words: a file that cries wolf every ten minutes stops
    being read (S202), and alarming all night about a PC meant to be off is how a
    light stops being read (v5.52).

IT IS AN ASSEMBLER, NOT A SENSOR
    It creates no new instrumentation and measures nothing itself. Every figure
    below is READ from something that already runs:

      block 1  NEEDS YOUR WORD ....... the staff ledger's PENDING rows (jsonl)
                                       + whatever digest.conf declares
      block 2  STOPPED OR STALE ...... freshness.json, the 08:05 job's own output
      block 3  WAITING ON SOMEONE .... digest_waiting.txt, owner-editable
      block 4  ALL FRESH - n tick .... freshness.json again

    If a source is missing or unreadable the block SAYS SO and the digest still
    goes out. A morning with no push is indistinguishable from a morning with
    nothing to say -- which is the exact fault (F-369, "silence was load-bearing")
    that the daily-green line was built to end. This must never re-create it.

TIMING -- 08:15, NOT 08:05, AND THE REASON IS NOT COSMETIC
    freshness runs at `5 8 * * *`. A digest at 08:05 would race it and report
    yesterday's freshness.json about half the time, silently. Ten minutes later it
    reports the run that just happened. The title still says the time it ran.

THE TITLE IS THE PRODUCT
    Collapsed on a phone the title is ALL he sees, so it carries the two numbers
    that decide whether to open it. ASCII ONLY: ntfy sends Title as an HTTP header
    and a non-ASCII header breaks the push (recorded in clinic_health_report.py,
    and the reason the tick marks live in the body).

EVERY ACTIONABLE LINE CARRIES A COMPLETE URL
    Never "check the portal", never a bare /finance/... . His standing rule,
    applied to the push. Plain text throughout, because his stated fallback is
    "I copy the message if needed and share it with you in a chat" -- that has to
    work with nothing built, and it does.

CONFIGURATION, NOT CODE (D417/D423)
    /root/finance/digest.conf. The ntfy topic is NOT stored here: it is read from
    freshness.conf, so the topic lives in exactly ONE file on the box (F-358, and
    the reason the S231 rotation was possible at all).

RUN
    /root/wa/venv/bin/python3 /root/finance/morning_digest.py --dry-run
    /root/wa/venv/bin/python3 /root/finance/morning_digest.py --selftest
    /root/wa/venv/bin/python3 /root/finance/morning_digest.py          # sends
"""

import json
import os
import sys
import time
import urllib.request

CONF_PATH      = os.environ.get("DIGEST_CONF", "/root/finance/digest.conf")
FRESHNESS_CONF = os.environ.get("FRESHNESS_CONF", "/root/finance/freshness.conf")

DEFAULTS = {
    "FRESHNESS_JSON": "/root/finance/freshness.json",
    "LEDGER_DIR":     "/root/staff_ledger",
    "WAITING_FILE":   "/root/finance/digest_waiting.txt",
    "STATE_FILE":     "/root/finance/digest.state.json",
    "FRESHNESS_PAGE": "",
    "LEDGER_URL":     "",
    "ONCE_PER_DAY":   "1",
    "MAX_LINES":      "12",
}


# ----------------------------------------------------------------- plumbing --
def read_conf(path):
    conf = {}
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    conf[k.strip()] = v.strip()
    except OSError:
        pass
    return conf


def setting(conf, key):
    v = conf.get(key)
    return v if v not in (None, "") else DEFAULTS.get(key, "")


def truthy(v):
    return str(v).strip().lower() not in ("0", "off", "no", "false", "")


def ist_now(epoch=None):
    """The owner's zone, always. The box runs IST but never assume it: fix the
    offset so a rebuilt or relocated box cannot silently retime his morning."""
    return time.gmtime((epoch if epoch is not None else time.time()) + 5.5 * 3600)


def hhmm(epoch=None):
    return time.strftime("%H:%M", ist_now(epoch))


def today_ist(epoch=None):
    return time.strftime("%Y-%m-%d", ist_now(epoch))


def ascii_only(s):
    """A non-ASCII byte in an HTTP header breaks the push outright."""
    return "".join(ch if 32 <= ord(ch) < 127 else "-" for ch in s)


# ------------------------------------------------------------------ sources --
class Source(object):
    """A block's worth of lines, plus an honest reason when there are none.

    `broken` is the distinction that matters: an EMPTY source (nothing pending)
    and an UNREADABLE source (the file is gone) look identical in a list of
    lines, and treating them the same is how a dead feed reads as a quiet one.
    """
    def __init__(self, name):
        self.name = name
        self.lines = []
        self.broken = None

    def fail(self, why):
        self.broken = why
        return self


def freshness_source(conf):
    """READ, never recompute -- the 08:05 job already did the work."""
    s = Source("freshness")
    path = setting(conf, "FRESHNESS_JSON")
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError) as e:
        return s.fail("freshness.json unreadable (%s)" % e.__class__.__name__)
    counts = data.get("counts") or {}
    legs = data.get("legs") or []
    s.total = int(counts.get("total") or len(legs))
    s.ok = int(counts.get("ok") or 0)
    s.generated = data.get("generated_iso") or "?"
    s.bad = [l for l in legs if (l.get("verdict") or "OK") != "OK"]
    s.ok_names = [l.get("name", "?") for l in legs if (l.get("verdict") or "OK") == "OK"]
    return s


def ledger_pending_source(conf):
    """PENDING rows in the staff ledger -- the clearest 'needs your word' the
    estate has: a maker entered money and it is waiting on a doctor's tap."""
    s = Source("ledger")
    path = os.path.join(setting(conf, "LEDGER_DIR"), "ledger.jsonl")
    if not os.path.exists(path):
        return s.fail("ledger.jsonl not found")
    try:
        pend = []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue          # one bad line never kills the digest
                if r.get("status") == "PENDING":
                    pend.append(r)
    except OSError as e:
        return s.fail("ledger unreadable (%s)" % e.__class__.__name__)
    for r in pend:
        who = r.get("staff") or "?"
        amt = abs(int(r.get("amount") or 0))
        cat = (r.get("category") or "").replace("_", " ").lower()
        flag = " [SPECIAL]" if r.get("special") else ""
        s.lines.append("%s - %s Rs %d%s" % (who, cat, amt, flag))
    return s


def waiting_source(conf):
    """Owner-editable, one line per thing he is NOT chasing. A file, not code:
    the list changes weekly and must never need a deploy."""
    s = Source("waiting")
    path = setting(conf, "WAITING_FILE")
    if not os.path.exists(path):
        return s          # absent is legitimately empty here, not broken
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"):
                    s.lines.append(line)
    except OSError as e:
        return s.fail("waiting file unreadable (%s)" % e.__class__.__name__)
    return s


# ------------------------------------------------------------------ render --
def build(conf, epoch=None):
    fresh = freshness_source(conf)
    ledger = ledger_pending_source(conf)
    waiting = waiting_source(conf)

    fresh_page = setting(conf, "FRESHNESS_PAGE")
    ledger_url = setting(conf, "LEDGER_URL")
    max_lines = int(setting(conf, "MAX_LINES") or 12)

    need = list(ledger.lines)
    stale = list(getattr(fresh, "bad", []))

    # ---- title: the two numbers that decide whether he opens it -------------
    if fresh.broken:
        fresh_bit = "freshness unknown"
    else:
        fresh_bit = "%d of %d fresh" % (fresh.ok, fresh.total)
    if need:
        need_bit = "%d need%s you" % (len(need), "s" if len(need) == 1 else "")
    else:
        need_bit = "nothing needs you"
    title = ascii_only("Clinic %s - %s, %s" % (hhmm(epoch), need_bit, fresh_bit))

    out = []

    # ---- block 1 -----------------------------------------------------------
    out.append("NEEDS YOUR WORD")
    if ledger.broken:
        out.append("  ? could not read the ledger - %s" % ledger.broken)
    elif not need:
        out.append("  nothing waiting on your approval")
    else:
        for line in need[:max_lines]:
            out.append("  - " + line)
        if len(need) > max_lines:
            out.append("  ... and %d more" % (len(need) - max_lines))
        if ledger_url:
            out.append("  " + ledger_url)

    # ---- block 2 -----------------------------------------------------------
    out.append("")
    out.append("STOPPED OR STALE")
    if fresh.broken:
        out.append("  ? %s" % fresh.broken)
        out.append("  (the 08:05 freshness run did not leave a result - that is")
        out.append("   itself the finding, not a quiet morning)")
    elif not stale:
        out.append("  nothing")
    else:
        for l in stale[:max_lines]:
            out.append("  - %s: %s, %s" % (l.get("name", "?"),
                                           (l.get("verdict") or "?").lower(),
                                           l.get("age_words") or "age unknown"))
        if fresh_page:
            out.append("  " + fresh_page)

    # ---- block 3 -----------------------------------------------------------
    out.append("")
    out.append("WAITING ON SOMEONE ELSE")
    if waiting.broken:
        out.append("  ? %s" % waiting.broken)
    elif not waiting.lines:
        out.append("  nothing recorded")
    else:
        for line in waiting.lines[:max_lines]:
            out.append("  - " + line)

    # ---- block 4 -- last, where routine state belongs ----------------------
    out.append("")
    if fresh.broken:
        out.append("ALL FRESH - not known this morning")
    else:
        # "ALL FRESH" only when it IS all of them. Saying "ALL FRESH - 24 of
        # 26" is the small kind of wrong that teaches a reader to stop trusting
        # the heading, and then the heading is worth nothing on the day it says
        # something true.
        if fresh.ok == fresh.total:
            out.append("ALL FRESH - %d of %d" % (fresh.ok, fresh.total))
        else:
            out.append("FRESH - %d of %d (the other %d are above)"
                       % (fresh.ok, fresh.total, fresh.total - fresh.ok))
        for name in getattr(fresh, "ok_names", []):
            out.append("  [x] %s" % name)
        out.append("  as of %s" % fresh.generated)

    return title, "\n".join(out)


# ------------------------------------------------------------------- send ---
def topic_url():
    """ONE place on the box holds the topic (F-358). Read it; never carry it."""
    return read_conf(FRESHNESS_CONF).get("NTFY_URL", "").strip()


def post(url, title, body):
    req = urllib.request.Request(
        url, data=body.encode("utf-8"),
        headers={"Title": title, "Priority": "default", "Tags": "sunrise"})
    urllib.request.urlopen(req, timeout=15).read()


def already_sent_today(conf, epoch=None):
    if not truthy(setting(conf, "ONCE_PER_DAY")):
        return False
    try:
        with open(setting(conf, "STATE_FILE"), encoding="utf-8") as fh:
            return json.load(fh).get("last_sent") == today_ist(epoch)
    except (OSError, ValueError):
        return False


def mark_sent(conf, epoch=None):
    path = setting(conf, "STATE_FILE")
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"last_sent": today_ist(epoch)}, fh)
        os.replace(tmp, path)
    except OSError:
        pass


# --------------------------------------------------------------- selftest ---
def selftest():
    import tempfile
    bad = [0]

    def ok(label, cond):
        if not cond:
            bad[0] += 1
            print("  FAIL %s" % label)

    d = tempfile.mkdtemp()
    fj = os.path.join(d, "freshness.json")
    lj = os.path.join(d, "ledger.jsonl")
    wf = os.path.join(d, "waiting.txt")
    conf = {"FRESHNESS_JSON": fj, "LEDGER_DIR": d, "WAITING_FILE": wf,
            "STATE_FILE": os.path.join(d, "s.json"),
            "FRESHNESS_PAGE": "https://followup.dr-manoj.in/finance/freshness",
            "LEDGER_URL": "https://followup.dr-manoj.in/ledger/"}

    # 1. everything missing -- must still produce a digest, and say so
    t, b = build(conf)
    ok("title is ASCII with nothing present", t == ascii_only(t))
    ok("missing freshness is NAMED, not silent", "freshness.json unreadable" in b)
    ok("missing ledger is NAMED, not silent", "could not read the ledger" in b)
    ok("the four blocks are all present",
       all(x in b for x in ("NEEDS YOUR WORD", "STOPPED OR STALE",
                            "WAITING ON SOMEONE ELSE", "ALL FRESH")))

    # 2. a healthy morning
    json.dump({"generated_iso": "2026-09-09T08:05:01",
               "counts": {"total": 3, "ok": 3},
               "legs": [{"name": "marg pull", "verdict": "OK"},
                        {"name": "bank ingest", "verdict": "OK"},
                        {"name": "docterz", "verdict": "OK"}]},
              open(fj, "w"))
    open(lj, "w").close()
    t, b = build(conf)
    ok("quiet title says nothing needs him", "nothing needs you" in t)
    ok("quiet title carries the count", "3 of 3 fresh" in t)
    ok("quiet body says nothing pending", "nothing waiting on your approval" in b)
    ok("tick list present", b.count("[x]") == 3)
    ok("ALL FRESH heading only when all are fresh", "ALL FRESH - 3 of 3" in b)
    ok("no stale block content", "nothing" in b.split("STOPPED OR STALE")[1][:40])

    # 3. a morning that needs him
    with open(lj, "w") as fh:
        fh.write(json.dumps({"status": "PENDING", "staff": "Darpan",
                             "category": "ADVANCE_ISSUE", "amount": 12000,
                             "special": True}) + "\n")
        fh.write(json.dumps({"status": "APPROVED", "staff": "Amir",
                             "category": "NIGHT_DUTY", "amount": 200}) + "\n")
        fh.write("not json at all\n")
    json.dump({"generated_iso": "2026-09-09T08:05:01",
               "counts": {"total": 3, "ok": 2},
               "legs": [{"name": "marg pull", "verdict": "STALE",
                         "age_words": "2 days"},
                        {"name": "bank ingest", "verdict": "OK"},
                        {"name": "docterz", "verdict": "OK"}]},
              open(fj, "w"))
    open(wf, "w").write("# a comment\nAmir - the 24 renames\nMyOperator - token overlap\n")
    t, b = build(conf)
    ok("busy title counts only PENDING, and says NEEDS for one", "1 needs you" in t)
    ok("the heading is not ALL FRESH when it is not all of them",
       "ALL FRESH" not in b and "FRESH - 2 of 3" in b)
    ok("busy title counts fresh", "2 of 3 fresh" in t)
    ok("the pending row names the staff", "Darpan" in b)
    ok("a SPECIAL advance is flagged", "[SPECIAL]" in b)
    ok("an APPROVED row is NOT listed", "Amir - night duty" not in b)
    ok("a malformed line does not kill the run", "12000" in b)
    ok("the stale leg is named with its age", "marg pull" in b and "2 days" in b)
    ok("block 1 carries a FULL url", "https://followup.dr-manoj.in/ledger/" in b)
    ok("block 2 carries a FULL url", "https://followup.dr-manoj.in/finance/freshness" in b)
    ok("no bare path anywhere", "\n  /finance" not in b and "\n  /ledger" not in b)
    ok("waiting block reads the file", "the 24 renames" in b)
    ok("waiting block drops comments", "a comment" not in b)
    ok("body is plain text, no markup", "<" not in b and "*" not in b)

    # 4. the once-a-day guard
    ok("not sent yet", not already_sent_today(conf))
    mark_sent(conf)
    ok("guard holds after sending", already_sent_today(conf))
    conf2 = dict(conf); conf2["ONCE_PER_DAY"] = "0"
    ok("guard can be switched off in conf", not already_sent_today(conf2))

    # 5. IST is fixed, never the box's idea of local time.
    # These are CONSTANTS, not the function compared with itself: the first
    # version of this check read `hhmm(x) == hhmm(x)`, which is true on any
    # machine in any zone and could never have failed. A selftest that cannot
    # fail is not a test.
    ok("02:35 UTC reads 08:05 IST", hhmm(1789439700) == "08:05")
    ok("20:35 UTC reads 02:05 IST the NEXT day", hhmm(1789504500) == "02:05")
    ok("the day rolls at IST midnight, not UTC",
       today_ist(1789439700) == "2026-09-15" and today_ist(1789504500) == "2026-09-16")

    n = 29
    print("morning_digest selftest: %d/%d passed" % (n - bad[0], n))
    return 0 if bad[0] == 0 else 1


# ------------------------------------------------------------------- main ---
def main():
    args = sys.argv[1:]
    if "--selftest" in args:
        return selftest()
    conf = read_conf(CONF_PATH)
    title, body = build(conf)
    if "--dry-run" in args:
        print("TITLE: %s" % title)
        print("-" * 60)
        print(body)
        return 0
    if already_sent_today(conf):
        print("already sent today -- nothing to do")
        return 0
    url = topic_url()
    if not url:
        print("REFUSING -- no NTFY_URL in %s. The topic lives in exactly one "
              "file on this box and this is not it (F-358)." % FRESHNESS_CONF)
        return 2
    post(url, title, body)
    mark_sent(conf)
    print("sent: %s" % title)
    return 0


if __name__ == "__main__":
    sys.exit(main())
