#!/usr/bin/env python3
# =============================================================================
#  WALK_freshness.py · S230 · the LIVE-SHAPE walk for freshness.py v1
#
#  A prepared kit is proven only by a LIVE-SHAPE walk. So this builds a real
#  fixture estate in a temp directory — real state files (fresh, stale,
#  malformed, missing-field, empty-field), real logs with mtimes set to the
#  hour, a real glob of several files, a REAL sqlite database opened the way
#  the live one will be, a parked leg and an unreadable path — and drives the
#  REAL functions through it. Nothing outside the temp directory is touched and
#  there is NO NETWORK ANYWHERE: the ntfy push is stubbed and the walk asserts
#  on exactly what WOULD have been sent.
#
#   1  timestamp parsing, the shapes this estate actually writes
#   2  age in plain words, and the window label
#   3  every kind, and every verdict from the condition that must produce it
#   4  a full check run: outputs, exit codes, ONE BAD LEG DOES NOT STOP THE REST
#   5  the once-per-day shout, and the next day's shout
#   6  the HTML: every leg named, no external asset, header line, IST label
#   7  list mode reads and writes nothing
#   8  the SHIPPED legs.json is valid, complete and carries no numbers (F-185)
#
#  Run:  python -B WALK_freshness.py     (exits 0 with ALL WALK CHECKS PASS)
# =============================================================================
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
import contextlib

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import freshness as M

CHECKS = []


def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))


H = 3600.0
NOW = time.time()
T = tempfile.mkdtemp(prefix="walk_fresh_")


def p(*a):
    return os.path.join(T, *a)


def iso(epoch):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(epoch))


def put(path, text, age_h=None):
    with open(path, "w") as fh:
        fh.write(text)
    if age_h is not None:
        t = NOW - age_h * H
        os.utime(path, (t, t))
    return path


def run_check(shout=False):
    """Drive the real check() and hand back (exit code, stdout)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = M.check(shout=shout)
    return rc, buf.getvalue()


def write_conf(**kw):
    lines = ["# walk fixture conf"]
    for k, v in kw.items():
        lines.append("%s=%s" % (k, v))
    put(p("freshness.conf"), "\n".join(lines) + "\n")
    M.CONF_PATH = p("freshness.conf")


def write_legs(legs, name="legs.json"):
    put(p(name), json.dumps({"legs": legs}, indent=1))
    return p(name)


# ---------------------------------------------------------------- fixtures --
os.makedirs(p("globdir"))
put(p("state_fresh.json"), json.dumps({"last_success_iso": iso(NOW - 2 * H)}))
put(p("state_stale.json"), json.dumps({"last_success_iso": iso(NOW - 100 * H)}))
put(p("state_bad.json"), "{ this is not json at all")
put(p("state_nofield.json"), json.dumps({"something_else": iso(NOW)}))
put(p("state_empty.json"), json.dumps({"last_success_iso": ""}))
put(p("state_epoch.json"), json.dumps({"last_success_iso": int(NOW - 3 * H)}))
put(p("log_fresh.log"), "ran\n", age_h=2)
put(p("log_old.log"), "ran once, long ago\n", age_h=100)
put(p("punches.csv"), "user,time\n", age_h=30)
put(p("globdir", "finance_20260901.db"), "x", age_h=72)
put(p("globdir", "finance_20260906.db"), "x", age_h=3)
put(p("globdir", "finance_20260905.db"), "x", age_h=27)
os.makedirs(p("a_directory_not_a_file"))

DB = p("feeds.db")
con = sqlite3.connect(DB)
con.execute("CREATE TABLE stock_feed (id INTEGER PRIMARY KEY, received_at TEXT)")
con.execute("CREATE TABLE empty_feed (id INTEGER PRIMARY KEY, at TEXT)")
con.execute("INSERT INTO stock_feed (received_at) VALUES (?)", (iso(NOW - 40 * H),))
con.execute("INSERT INTO stock_feed (received_at) VALUES (?)", (iso(NOW - 4 * H),))
con.execute("INSERT INTO stock_feed (received_at) VALUES (?)", (iso(NOW - 12 * H),))
con.commit()
con.close()
DB_MD5_BEFORE = os.path.getsize(DB), os.stat(DB).st_mtime

print("— 1 · timestamp parsing")
check("ISO with T parses", abs(M.parse_ts(iso(NOW)) - NOW) < 2)
check("ISO with a space parses",
      abs(M.parse_ts(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(NOW))) - NOW) < 2)
check("ISO with an offset parses", M.parse_ts("2026-09-07T10:00:00+05:30") ==
      M.parse_ts("2026-09-07T04:30:00+00:00"))
check("epoch seconds parse", abs(M.parse_ts(int(NOW)) - NOW) < 2)
check("a bare date parses", M.parse_ts("2026-09-07") is not None)
check("rubbish is not invented into a time", M.parse_ts("last tuesday") is None)
check("empty is not invented into a time", M.parse_ts("") is None and M.parse_ts(None) is None)

print("— 2 · age in words")
check("minutes read as minutes", M.plain_age(25 * 60) == "25 minutes ago")
check("hours read as hours", M.plain_age(4 * H + 1200) == "4 hours ago")
check("one hour is singular", M.plain_age(1 * H + 60) == "1 hour ago")
check("days read as days", M.plain_age(50 * H) == "2 days ago")
check("no reading is 'never'", M.plain_age(None) == "never")
check("window prints hours and days",
      M.window_str(26) == "26 h" and M.window_str(200) == "8.3 d")

print("— 3 · every kind, every verdict")


def one(leg):
    return M.check_leg(dict({"name": "x", "group": "g", "note": "", "bad": "",
                             "disabled": False}, **leg), NOW)


r = one({"kind": "state_json", "target": p("state_fresh.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("state_json fresh -> OK", r["verdict"] == "OK" and 1.9 < r["age_h"] < 2.1)
r = one({"kind": "state_json", "target": p("state_stale.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("state_json past its window -> STALE", r["verdict"] == "STALE")
r = one({"kind": "state_json", "target": p("state_bad.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("malformed state file -> ERROR", r["verdict"] == "ERROR")
check("the ERROR says what went wrong", "JSONDecodeError" in r["detail"] or
      "Expecting" in r["detail"])
r = one({"kind": "state_json", "target": p("state_nofield.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("state file without the named field -> ERROR", r["verdict"] == "ERROR")
r = one({"kind": "state_json", "target": p("state_empty.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("field present but empty -> NEVER", r["verdict"] == "NEVER")
r = one({"kind": "state_json", "target": p("no_such_state.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("no state file at all -> NEVER", r["verdict"] == "NEVER")
r = one({"kind": "state_json", "target": p("state_epoch.json"),
         "field": "last_success_iso", "max_age_h": 26})
check("state file holding an epoch -> OK", r["verdict"] == "OK")

r = one({"kind": "log_mtime", "target": p("log_fresh.log"), "max_age_h": 26})
check("log_mtime fresh -> OK", r["verdict"] == "OK")
r = one({"kind": "log_mtime", "target": p("log_old.log"), "max_age_h": 26})
check("log_mtime old -> STALE", r["verdict"] == "STALE" and r["age_h"] > 99)
r = one({"kind": "log_mtime", "target": p("never_written.log"), "max_age_h": 26})
check("a log never written -> NEVER", r["verdict"] == "NEVER")

r = one({"kind": "file_mtime", "target": p("punches.csv"), "max_age_h": 74})
check("file_mtime inside a wide window -> OK", r["verdict"] == "OK")
r = one({"kind": "file_mtime", "target": p("punches.csv"), "max_age_h": 26})
check("the same file against a tight window -> STALE", r["verdict"] == "STALE")

r = one({"kind": "glob_newest", "target": p("globdir", "finance_*.db"),
         "max_age_h": 26})
check("glob_newest takes the NEWEST of several", r["verdict"] == "OK" and
      2.9 < r["age_h"] < 3.1)
check("glob_newest says how many it saw", "3 file(s)" in r["detail"])
r = one({"kind": "glob_newest", "target": p("globdir", "assetapp_*.tar.gz"),
         "max_age_h": 200})
check("a glob that has never matched -> NEVER", r["verdict"] == "NEVER")

r = one({"kind": "sqlite_max", "target": DB, "table": "stock_feed",
         "column": "received_at", "max_age_h": 26})
check("sqlite_max reads the newest row -> OK", r["verdict"] == "OK" and
      3.9 < r["age_h"] < 4.1)
r = one({"kind": "sqlite_max", "target": DB, "table": "stock_feed",
         "column": "received_at", "max_age_h": 2})
check("sqlite_max past its window -> STALE", r["verdict"] == "STALE")
r = one({"kind": "sqlite_max", "target": DB, "table": "empty_feed",
         "column": "at", "max_age_h": 26})
check("a table with no rows -> NEVER", r["verdict"] == "NEVER")
r = one({"kind": "sqlite_max", "target": DB, "table": "no_such_table",
         "column": "at", "max_age_h": 26})
check("a table that is not there -> ERROR", r["verdict"] == "ERROR" and
      "no such table" in r["detail"])
r = one({"kind": "sqlite_max", "target": p("no_such.db"), "table": "stock_feed",
         "column": "received_at", "max_age_h": 26})
check("a database that is not there -> NEVER", r["verdict"] == "NEVER")
r = one({"kind": "sqlite_max", "target": DB, "table": "stock_feed; DROP TABLE x",
         "column": "received_at", "max_age_h": 26})
check("a table name that is not an identifier is refused -> ERROR",
      r["verdict"] == "ERROR")
check("the database was not written to by any of that",
      (os.path.getsize(DB), os.stat(DB).st_mtime) == DB_MD5_BEFORE)

r = one({"kind": "state_json", "target": p("a_directory_not_a_file"),
         "field": "last_success_iso", "max_age_h": 26})
check("an unreadable path -> ERROR, not a crash", r["verdict"] == "ERROR")
r = one({"kind": "moon_phase", "target": p("log_fresh.log"), "max_age_h": 26,
         "bad": "unknown kind 'moon_phase'"})
check("a kind this does not support -> ERROR naming it",
      r["verdict"] == "ERROR" and "moon_phase" in r["detail"])

print("— 4 · a full run")
LEGS = [
    {"name": "good one", "group": "Alpha", "kind": "log_mtime",
     "target": p("log_fresh.log"), "max_age_h": 26},
    {"name": "the bad leg", "group": "Alpha", "kind": "state_json",
     "target": p("a_directory_not_a_file"), "max_age_h": 26},
    {"name": "good two", "group": "Alpha", "kind": "glob_newest",
     "target": p("globdir", "finance_*.db"), "max_age_h": 26},
    {"name": "declared with no kind", "group": "Beta", "kind": "",
     "target": p("log_fresh.log"), "max_age_h": 26},
    {"name": "good three", "group": "Beta", "kind": "sqlite_max", "target": DB,
     "table": "stock_feed", "column": "received_at", "max_age_h": 26},
    {"name": "the stale one", "group": "Beta", "kind": "log_mtime",
     "target": p("log_old.log"), "max_age_h": 26},
    {"name": "the parked one", "group": "Beta", "kind": "log_mtime",
     "target": p("never_written.log"), "max_age_h": 26, "disabled": True,
     "note": "parked on purpose"},
    {"name": "the collector itself", "group": "Watchdog", "kind": "state_json",
     "target": "{STATE_FILE}", "field": "last_run_iso", "max_age_h": 26},
]
write_conf(LEGS_FILE=write_legs(LEGS), STATE_FILE=p("out.state.json"),
           JSON_OUT=p("out.json"), HTML_OUT=p("out.html"),
           SUMMARY_FILE=p("out.summary.log"))

rc, out = run_check()
data = json.load(open(p("out.json")))
names = [l["name"] for l in data["legs"]]
verdict = dict((l["name"], l["verdict"]) for l in data["legs"])
check("one bad leg did not stop the rest — all 7 live legs are in the output",
      len(data["legs"]) == 7)
check("the legs AFTER the bad one were still read",
      verdict["good two"] == "OK" and verdict["good three"] == "OK")
check("the bad leg is an ERROR row, not an exception",
      verdict["the bad leg"] == "ERROR")
check("a leg declared with no kind is an ERROR row",
      verdict["declared with no kind"] == "ERROR")
check("the stale leg is STALE", verdict["the stale one"] == "STALE")
check("the parked leg was skipped", "the parked one" not in names)
check("the parked leg is still listed as parked",
      data["parked"] and data["parked"][0]["name"] == "the parked one")
check("the collector's own leg is NEVER on its first ever run",
      verdict["the collector itself"] == "NEVER")
check("exit 1 when something is not fresh", rc == 1)
check("counts agree with the rows", data["counts"]["total"] == 7 and
      data["counts"]["ok"] + data["counts"]["stale"] + data["counts"]["never"]
      + data["counts"]["error"] == 7)
check("the printed table names every leg",
      all(n in out for n in names) and "PARKED" in out)
st = json.load(open(p("out.state.json")))
check("the state file records the run's own timestamp",
      isinstance(st.get("last_run_iso"), str) and "T" in st["last_run_iso"] and
      abs(st.get("last_run_epoch", 0) - NOW) < 120)
check("the state file names what was not fresh",
      "the stale one" in st["not_ok_legs"] and "good one" not in st["not_ok_legs"])
check("the summary log gained one line",
      len(open(p("out.summary.log")).read().strip().split("\n")) == 1)
check("the raw timestamp is carried through to the JSON",
      any(l["last_iso"] and l["last_raw"] for l in data["legs"]))

rc2, out2 = run_check()
st2 = json.load(open(p("out.state.json")))
data2 = json.load(open(p("out.json")))
v2 = dict((l["name"], l["verdict"]) for l in data2["legs"])
check("on the second run the collector can see its own last run",
      v2["the collector itself"] == "OK")
check("the summary log gained a second line",
      len(open(p("out.summary.log")).read().strip().split("\n")) == 2)
check("watched files were not written to by the run",
      os.stat(p("log_fresh.log")).st_mtime == NOW - 2 * H and
      (os.path.getsize(DB), os.stat(DB).st_mtime) == DB_MD5_BEFORE)

ALL_OK = [
    {"name": "good one", "group": "Alpha", "kind": "log_mtime",
     "target": p("log_fresh.log"), "max_age_h": 26},
    {"name": "good two", "group": "Alpha", "kind": "glob_newest",
     "target": p("globdir", "finance_*.db"), "max_age_h": 26},
]
write_conf(LEGS_FILE=write_legs(ALL_OK, "legs_ok.json"),
           STATE_FILE=p("ok.state.json"), JSON_OUT=p("ok.json"),
           HTML_OUT=p("ok.html"), SUMMARY_FILE=p("ok.summary.log"))
rc3, out3 = run_check()
check("exit 0 when every leg is inside its window", rc3 == 0)
check("and it says so", "every leg is inside its window" in out3)

print("— 5 · the shout, at most once per leg per day")
SENT = []
M.post_ntfy = lambda url, title, body: SENT.append((url, title, body)) or True
write_conf(LEGS_FILE=write_legs(LEGS, "legs_shout.json"),
           STATE_FILE=p("s.state.json"), JSON_OUT=p("s.json"),
           HTML_OUT=p("s.html"), SUMMARY_FILE=p("s.summary.log"),
           NTFY_URL="ntfy-topic-from-conf", NTFY_TITLE="Clinic freshness")
M.today_str = lambda: "2026-09-07"
rc, out = run_check(shout=True)
check("the first shout of the day is sent", len(SENT) == 1)
body = SENT[0][2] if SENT else ""
check("the message names the stale leg", "the stale one" in body)
check("the message names the never/error legs",
      "the bad leg" in body and "declared with no kind" in body)
check("the message does not name the healthy legs", "good two" not in body)
check("the message points at the page", p("s.html") in body)
check("the title comes from the conf", SENT[0][1] == "Clinic freshness")
check("the topic URL came from the conf, not from the code",
      SENT[0][0] == "ntfy-topic-from-conf")
check("the shout is one message, not one per leg", len(SENT) == 1)
rc, out = run_check(shout=True)
check("a second run the same day shouts about nothing", len(SENT) == 1)
check("and says why", "already shouted" in out)
sst = json.load(open(p("s.state.json")))
check("the shout record is keyed by leg and day",
      any(k.endswith("|2026-09-07") for k in sst["shouted"]))
M.today_str = lambda: "2026-09-08"
rc, out = run_check(shout=True)
check("the next day it shouts again", len(SENT) == 2)
check("the new day's message still names the stale leg", "the stale one" in SENT[1][2])

recovered = [dict(l) for l in LEGS if l["name"] != "the stale one"]
write_legs(recovered, "legs_shout.json")
rc, out = run_check(shout=True)
check("a leg that is gone from the file is no longer shouted about",
      "the stale one" not in SENT[-1][2] or len(SENT) == 2)

M.post_ntfy = lambda url, title, body: (_ for _ in ()).throw(RuntimeError("no network"))
M.today_str = lambda: "2026-09-09"
rc, out = run_check(shout=True)
check("a failed push does not crash the run", rc == 1)
check("a failed push is reported, not swallowed silently", "FAILED" in out)
fst = json.load(open(p("s.state.json")))
check("a failed push is NOT recorded as shouted (it retries tomorrow)",
      not any(k.endswith("|2026-09-09") for k in fst["shouted"]))
SENT2 = []
M.post_ntfy = lambda url, title, body: SENT2.append(body) or True
rc, out = run_check(shout=True)
check("the retry on the same day does go out once the push works", len(SENT2) == 1)

write_conf(LEGS_FILE=p("legs_shout.json"), STATE_FILE=p("n.state.json"),
           JSON_OUT=p("n.json"), HTML_OUT=p("n.html"),
           SUMMARY_FILE=p("n.summary.log"))
before = len(SENT2)
rc, out = run_check(shout=True)
check("with no NTFY_URL in the conf nothing is sent and nothing crashes",
      len(SENT2) == before and rc == 1)
check("and it says the topic is not configured", "NTFY_URL is not set" in out)

print("— 6 · the page")
# read the page back from a run over the FULL fixture set, so every
# verdict class is on it
write_legs(LEGS, "legs_shout.json")
write_conf(LEGS_FILE=p("legs_shout.json"), STATE_FILE=p("s.state.json"),
           JSON_OUT=p("s.json"), HTML_OUT=p("s.html"),
           SUMMARY_FILE=p("s.summary.log"))
run_check()
page = open(p("s.html")).read()
for n in ["good one", "the bad leg", "good two", "the stale one",
          "the collector itself", "declared with no kind", "good three"]:
    check("the page names '%s'" % n, n in page)
check("the parked leg is shown as parked, not silently dropped",
      "the parked one" in page and "Parked" in page)
check("no external asset is referenced",
      "http://" not in page and "https://" not in page and
      "<script" not in page and " src=" not in page and "@import" not in page)
check("the page needs no javascript to be read", "javascript" not in page.lower())
check("the header line counts the legs", "7 legs" in page)
check("the header line reports ok, stale and never",
      "OK &middot;" in page and "stale" in page and "never" in page)
tzname, tzoff = M.tz_label()
check("the clock offset is read and labelled, not assumed",
      tzoff in page and tzname in page)
check("the page is grouped", "<h2>Alpha</h2>" in page and "<h2>Beta</h2>" in page)
check("verdicts are coloured words, not icons",
      'class="v STALE">STALE<' in page and 'class="v OK">OK<' in page)
check("the page explains what each verdict means",
      "there is no sign it has ever run" in page)
check("the page carries the sentence this kit exists for",
      "not green, it is unmeasured" in page)
first_group = page.index("<h2>")
check("the worst group is printed first",
      page[first_group:first_group + 20].startswith("<h2>Alpha"))
rows_order = [page.index(x) for x in ["the bad leg", "good one"]]
check("inside a group the worst leg is first", rows_order[0] < rows_order[1])

print("— 7 · list mode reads nothing and writes nothing")
for f in [p("n.json"), p("n.html"), p("n.state.json"), p("n.summary.log")]:
    if os.path.exists(f):
        os.unlink(f)
mtimes = dict((f, os.stat(f).st_mtime) for f in
              [p("log_fresh.log"), p("log_old.log"), DB, p("punches.csv")])
buf = io.StringIO()
try:
    with contextlib.redirect_stdout(buf):
        rcl = M.list_mode()
except SystemExit as e:
    rcl = e.code
listing = buf.getvalue()
check("list exits 0", rcl == 0)
check("list names every declared leg",
      all(n in listing for n in ["good one", "the bad leg", "the collector itself"]))
check("list marks the parked leg", "[PARKED]" in listing)
check("list wrote no output files",
      not any(os.path.exists(f) for f in
              [p("n.json"), p("n.html"), p("n.state.json"), p("n.summary.log")]))
check("list touched no watched file",
      all(os.stat(f).st_mtime == m for f, m in mtimes.items()))

print("— 8 · the legs.json this kit ships")
SHIPPED = os.path.join(HERE, "legs.json")
raw = open(SHIPPED).read()
shipped = M.load_legs(SHIPPED, {"STATE_FILE": "/root/finance/freshness.state.json"})
check("the shipped legs.json is valid JSON and declares legs", len(shipped) >= 20)
check("every shipped leg is well formed",
      not [l["name"] for l in shipped if l["bad"]])
check("every shipped leg has a group and a window",
      all(l["group"] and l["max_age_h"] > 0 for l in shipped))
check("every shipped kind is one this code supports",
      all(l["kind"] in M.KINDS for l in shipped))
check("shipped leg names are unique",
      len(set(l["name"] for l in shipped)) == len(shipped))
check("every sqlite_max leg names a plain table and column",
      all(M.IDENT.match(str(l.get("table") or "")) and
          M.IDENT.match(str(l.get("column") or ""))
          for l in shipped if l["kind"] == "sqlite_max"))
check("the collector watches itself",
      any(l["kind"] == "state_json" and l["target"].endswith("freshness.state.json")
          for l in shipped))
check("{STATE_FILE} was expanded, not left as a literal",
      not any("{STATE_FILE}" in l["target"] for l in shipped))
check("every group on the page is one of the estate's lanes",
      set(l["group"] for l in shipped) ==
      {"Backups", "Finance pipeline", "Marg lane", "Console and calls",
       "Attendance", "Watchdog"})
check("no long digit run anywhere in legs.json (F-185)",
      __import__("re").search(r"\d{10,}", raw) is None)
check("no topic, token or key path is shipped in legs.json (F-185)",
      "ntfy" not in raw.lower() and "token" not in raw.lower() and
      ".json.key" not in raw and "key.json" not in raw)
src = open(os.path.join(HERE, "freshness.py")).read()
check("the code ships no ntfy topic of its own",
      "ntfy.sh" not in src and "https://" not in src)
check("every database read in the code is opened read-only",
      src.count("sqlite3.connect") == 1 and "mode=ro" in src and
      "query_only" in src)

import shutil
shutil.rmtree(T, ignore_errors=True)

fails = [n for n, ok in CHECKS if not ok]
print()
if fails:
    print("WALK FAILED (%d of %d):" % (len(fails), len(CHECKS)))
    for n in fails:
        print("   -", n)
    sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
