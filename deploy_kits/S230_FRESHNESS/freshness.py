#!/root/wa/venv/bin/python3
# =============================================================================
#  freshness.py  ·  Session 230  ·  S230_FRESHNESS  ·  v1
#
#  A GREEN PIPELINE THAT CANNOT STATE ITS AGE IS NOT GREEN, IT IS UNMEASURED.
#
#  WHAT THIS EXISTS FOR. The defining failure of this estate is not that jobs
#  break — jobs always break — it is that NOTHING REPORTS ITS OWN AGE. Two
#  measured examples, both silent for as long as nobody happened to look:
#
#    * a pipeline step failed on 69 consecutive ten-minute cycles across
#      eleven hours, printing one word into a log nobody reads, while the
#      pipeline around it went on reporting "ok";
#    * a "weekly backup" has sat in cron for months and has never in its life
#      produced a single file. The cron line still looks perfectly healthy.
#
#  So this is not a dashboard. It is one sentence, once a day: ANYTHING THAT
#  HAS STOPPED SAYS SO, THE SAME DAY, IN ONE PLACE.
#
#  THE DESIGN PROPERTY THAT MATTERS MOST — legs are DECLARED, not coded.
#  Every watched leg lives in legs.json beside this file. Adding a leg, moving
#  a path, widening a window or parking a leg is an edit to that file and NEVER
#  a change to this code. A collector that needs a programmer to learn about a
#  new job will fall behind the estate within a month.
#
#  REFUSAL STANCES, ABSOLUTE:
#    * STRICTLY READ-ONLY against everything it watches. Databases are opened
#      file:...?mode=ro (uri=True). Logs and files are stat'ed and read. It
#      never writes to, moves, truncates, restarts or signals ANY other
#      service, ever, in any mode. The only things it writes are its own
#      state file, its own summary log, and its own JSON/HTML output.
#    * one unreadable leg NEVER stops the rest. A bad leg becomes an ERROR row
#      and the other forty are still checked.
#    * it never invents a timestamp. A target that cannot be read is ERROR; a
#      target that has never existed is NEVER; the two are different facts and
#      are never merged.
#    * it shouts at most ONCE PER LEG PER CALENDAR DAY. Alert fatigue is a
#      real failure mode: an alarm that cries every ten minutes is an alarm
#      nobody reads, which is where we started.
#
#  IT WATCHES ITSELF. The collector appears in its own output as a leg reading
#  its own state file. A freshness checker that has itself stopped is the worst
#  possible failure of this design, and it must be visible on its own page.
#  (That row shows the PREVIOUS run: state is written after the reading is
#  done, which is the only order in which the row can ever be honest.)
#
#  Modes:
#    check      (default) read every leg, print the table, write the JSON, the
#               HTML, the summary line and the state file. Exit 0 if every leg
#               is OK, exit 1 if anything is STALE, NEVER or ERROR.
#    --shout    as check, and if anything is not OK push ONE consolidated
#               message to the ntfy topic named in the conf — once per leg per
#               calendar day, no matter how often the job runs.
#    list       print the declared legs from legs.json and read nothing else.
#               Instant, and touches no watched path at all.
#
#  Config:  /root/finance/freshness.conf   (KEY=VALUE, chmod 600)
#    LEGS_FILE     path to legs.json          (default: beside this script)
#    STATE_FILE    default /root/finance/freshness.state.json
#    JSON_OUT      default /root/finance/freshness.json
#    HTML_OUT      default /root/finance/freshness.html
#    SUMMARY_FILE  default /root/finance/freshness.summary.log
#    NTFY_URL      the private ntfy topic URL — A SECRET. It lives in the conf
#                  on the box and NEVER in this file, in legs.json, or in git.
#    NTFY_TITLE    default "Clinic freshness"
#    SHOUT_MAX_LINES  default 12
#
#  Cron (08:05, five minutes after the 08:00 health report, so one morning
#  message covers the whole estate):
#    5 8 * * *  /root/wa/venv/bin/python3 /root/finance/freshness.py --shout >> /root/finance/freshness.log 2>&1
#
#  No patient data, no numbers, no ids, no tokens, no key paths in this file
#  or in legs.json (F-185). The topic URL comes from the conf at runtime.
# =============================================================================
import glob as globmod
import html
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

# --- module-level knobs: the WALK points the whole job at a fixture tree and
# --- so touches no real path and no network.
CONF_PATH = "/root/finance/freshness.conf"
HERE = os.path.dirname(os.path.abspath(__file__))

KINDS = ("state_json", "file_mtime", "glob_newest", "log_mtime", "sqlite_max")

OK, STALE, NEVER, ERROR = "OK", "STALE", "NEVER", "ERROR"
RANK = {ERROR: 0, NEVER: 1, STALE: 2, OK: 3}

EXIT_OK = 0
EXIT_STALE = 1
EXIT_USAGE = 2
EXIT_CONF = 10
EXIT_LEGS = 11

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def log(*a):
    print("[%s]" % time.strftime("%Y-%m-%d %H:%M:%S"), *a, flush=True)


def die(code, *a):
    log("FATAL:", *a)
    sys.exit(code)


def today_str():
    """The calendar day, for the once-a-day shout record. Its own function so
    the WALK can walk the clock over midnight without waiting for midnight."""
    return time.strftime("%Y-%m-%d")


# ---------------------------------------------------------------- config ----
def load_conf():
    conf = {}
    if os.path.exists(CONF_PATH):
        for line in open(CONF_PATH):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                conf[k.strip()] = v.strip()
    return conf


def _beside_conf(name):
    return os.path.join(os.path.dirname(CONF_PATH) or "/tmp", name)


def paths_of(conf):
    """Every path this job writes, and the legs file it reads. Resolved once so
    the leg declarations can refer to them by name."""
    return {
        "LEGS_FILE": conf.get("LEGS_FILE") or os.path.join(HERE, "legs.json"),
        "STATE_FILE": conf.get("STATE_FILE") or _beside_conf("freshness.state.json"),
        "JSON_OUT": conf.get("JSON_OUT") or _beside_conf("freshness.json"),
        "HTML_OUT": conf.get("HTML_OUT") or _beside_conf("freshness.html"),
        "SUMMARY_FILE": conf.get("SUMMARY_FILE") or _beside_conf("freshness.summary.log"),
    }


def int_conf(conf, key, default):
    try:
        return int(str(conf.get(key, "")).strip())
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------ legs ----
def expand(value, subs):
    """{STATE_FILE} in a declared target becomes the resolved path. This is how
    the collector watches itself without knowing where it was installed."""
    if not isinstance(value, str):
        return value
    for k, v in subs.items():
        value = value.replace("{%s}" % k, v)
    return value


def load_legs(legs_file, subs):
    """Read the declarations. A leg that is malformed is not fatal — it comes
    back as a leg whose verdict will be ERROR, because a mis-declared leg is
    exactly the kind of silence this job exists to break."""
    with open(legs_file) as fh:
        data = json.load(fh)
    raw = data.get("legs") if isinstance(data, dict) else data
    if not isinstance(raw, list):
        raise ValueError("legs file has no 'legs' list")
    legs, seen = [], set()
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            legs.append({"name": "leg #%d" % (i + 1), "group": "(undeclared)",
                         "kind": "", "target": "", "max_age_h": 0,
                         "note": "", "disabled": False,
                         "bad": "declaration is not an object"})
            continue
        leg = dict(item)
        leg["name"] = str(leg.get("name") or "leg #%d" % (i + 1))
        leg["group"] = str(leg.get("group") or "Ungrouped")
        leg["kind"] = str(leg.get("kind") or "")
        leg["target"] = expand(str(leg.get("target") or ""), subs)
        leg["note"] = str(leg.get("note") or "")
        leg["disabled"] = bool(leg.get("disabled"))
        leg["bad"] = ""
        try:
            leg["max_age_h"] = float(leg.get("max_age_h"))
        except (TypeError, ValueError):
            leg["max_age_h"] = 0.0
            leg["bad"] = "max_age_h is missing or not a number"
        if leg["name"] in seen:
            leg["bad"] = leg["bad"] or "duplicate leg name"
        seen.add(leg["name"])
        if not leg["bad"] and leg["kind"] not in KINDS:
            leg["bad"] = "unknown kind %r" % leg["kind"]
        if not leg["bad"] and not leg["target"]:
            leg["bad"] = "no target declared"
        if not leg["bad"] and leg["max_age_h"] <= 0:
            leg["bad"] = "max_age_h must be greater than zero"
        legs.append(leg)
    return legs


# ------------------------------------------------------------ timestamps ----
def parse_ts(value):
    """A stored timestamp -> epoch seconds, or None if it cannot be read.
    Accepts epoch numbers and the ISO shapes this estate actually writes.
    A naive timestamp is read as box-local time, which is what every writer
    on this box means by it. It NEVER guesses: unparseable is None."""
    import datetime as dt
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if value > 0 else None
    s = str(value).strip()
    if not s:
        return None
    if re.match(r"^\d{9,13}(\.\d+)?$", s):          # epoch seconds or millis
        n = float(s)
        return n / 1000.0 if n > 1e11 else n
    s = s.replace("Z", "+00:00").replace("z", "+00:00")
    if len(s) > 10 and s[10] == " ":
        s = s[:10] + "T" + s[11:]
    try:
        return dt.datetime.fromisoformat(s).timestamp()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"):
        try:
            return time.mktime(time.strptime(s[:len(fmt) + 8].strip(), fmt))
        except ValueError:
            continue
    return None


def tz_label():
    """The box's clock is already IST — but do not assume it. Read the offset
    and label what is actually there, so a page printed on a UTC box says so."""
    import datetime as dt
    off = dt.datetime.now().astimezone().utcoffset()
    secs = int(off.total_seconds()) if off else 0
    sign = "+" if secs >= 0 else "-"
    a = abs(secs)
    stamp = "%s%02d:%02d" % (sign, a // 3600, (a % 3600) // 60)
    return ("IST" if stamp == "+05:30" else "UTC" + stamp), stamp


def when_str(epoch):
    if not epoch:
        return "never"
    return time.strftime("%d-%b-%Y %H:%M", time.localtime(epoch))


def plain_age(seconds):
    """Age in the words the owner would use. Deliberately blunt: floors, never
    rounds up, so a row never claims to be fresher than it is."""
    if seconds is None:
        return "never"
    if seconds < 0:
        return "dated in the future"
    m = int(seconds // 60)
    if m < 1:
        return "just now"
    if m < 60:
        return "%d minute%s ago" % (m, "" if m == 1 else "s")
    h = int(seconds // 3600)
    if h < 48:
        return "%d hour%s ago" % (h, "" if h == 1 else "s")
    d = int(seconds // 86400)
    return "%d days ago" % d


def window_str(hours):
    if hours >= 48:
        return "%g d" % round(hours / 24.0, 1)
    return "%g h" % round(hours, 1)


# --------------------------------------------------------------- readers ----
def read_state_json(leg):
    """A state file's own field. Missing file = the job has never succeeded;
    a file that exists but does not carry the named field is a MIS-DECLARED
    leg, which is an error in this config and is reported as one."""
    path = leg["target"]
    field = str(leg.get("field") or "last_success_iso")
    if not os.path.exists(path):
        return None, NEVER, "no state file — no successful run recorded"
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("state file is not a JSON object")
    if field not in data:
        raise KeyError("state file has no field %r" % field)
    raw = data[field]
    if raw in (None, "", 0):
        return None, NEVER, "field %s is empty — nothing recorded yet" % field
    ts = parse_ts(raw)
    if ts is None:
        raise ValueError("field %s is not a timestamp this can read" % field)
    return ts, None, str(raw)


def read_file_mtime(leg):
    path = leg["target"]
    if not os.path.exists(path):
        return None, NEVER, "file has never been created"
    st = os.stat(path)
    detail = "%d bytes" % st.st_size
    if st.st_size == 0:
        detail += " (empty file — mtime only)"
    return st.st_mtime, None, detail


def read_glob_newest(leg):
    pattern = leg["target"]
    hits = [p for p in globmod.glob(pattern) if os.path.isfile(p)]
    if not hits:
        return None, NEVER, "nothing has ever matched this pattern"
    newest = max(hits, key=lambda p: os.stat(p).st_mtime)
    return (os.stat(newest).st_mtime, None,
            "%d file(s), newest %s" % (len(hits), os.path.basename(newest)))


def read_sqlite_max(leg):
    """max(column) from a table, opened READ-ONLY. Never writes, never creates,
    never migrates: mode=ro means sqlite refuses to make the file if it is
    absent, and we check for it first so the answer is NEVER, not ERROR."""
    path = leg["target"]
    table = str(leg.get("table") or "")
    column = str(leg.get("column") or "")
    if not IDENT.match(table) or not IDENT.match(column):
        raise ValueError("table/column must be plain identifiers")
    if not os.path.exists(path):
        return None, NEVER, "database file does not exist"
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True, timeout=5.0)
    try:
        con.execute("PRAGMA query_only = ON")
        row = con.execute("SELECT max(%s) FROM %s" % (column, table)).fetchone()
    finally:
        con.close()
    raw = row[0] if row else None
    if raw in (None, ""):
        return None, NEVER, "%s.%s has no rows yet" % (table, column)
    ts = parse_ts(raw)
    if ts is None:
        raise ValueError("%s.%s is not a timestamp this can read (%r)"
                         % (table, column, str(raw)[:40]))
    return ts, None, str(raw)


READERS = {
    "state_json": read_state_json,
    "file_mtime": read_file_mtime,
    "log_mtime": read_file_mtime,        # a log written every run IS a heartbeat
    "glob_newest": read_glob_newest,
    "sqlite_max": read_sqlite_max,
}


def check_leg(leg, now):
    """One leg -> one row. This function NEVER raises: a leg that blows up in
    any way whatsoever becomes an ERROR row so the other forty still run."""
    row = {
        "name": leg["name"], "group": leg["group"], "kind": leg["kind"],
        "target": leg["target"], "max_age_h": leg["max_age_h"],
        "note": leg.get("note", ""), "verdict": ERROR,
        "last_epoch": None, "last_iso": "", "last_raw": "",
        "age_h": None, "age_words": "never", "detail": "",
    }
    if leg.get("bad"):
        row["detail"] = "declaration: " + leg["bad"]
        return row
    try:
        ts, verdict, detail = READERS[leg["kind"]](leg)
        row["detail"] = detail
        if verdict is not None:
            row["verdict"] = verdict
            return row
        row["last_epoch"] = ts
        row["last_iso"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(ts))
        row["last_raw"] = detail
        age = now - ts
        row["age_h"] = round(age / 3600.0, 2)
        row["age_words"] = plain_age(age)
        row["verdict"] = OK if age <= leg["max_age_h"] * 3600.0 else STALE
    except Exception as ex:                      # deliberately everything
        row["verdict"] = ERROR
        row["detail"] = "%s: %s" % (type(ex).__name__, str(ex)[:160])
    return row


def collect(legs, now):
    rows, skipped = [], []
    for leg in legs:
        if leg.get("disabled"):
            skipped.append({"name": leg["name"], "group": leg["group"],
                            "note": leg.get("note", "")})
            continue
        rows.append(check_leg(leg, now))
    return rows, skipped


def counts_of(rows):
    c = {OK: 0, STALE: 0, NEVER: 0, ERROR: 0}
    for r in rows:
        c[r["verdict"]] = c.get(r["verdict"], 0) + 1
    return c


def sort_rows(rows):
    """Worst first, and oldest first inside a verdict."""
    return sorted(rows, key=lambda r: (RANK.get(r["verdict"], 0),
                                       -(r["age_h"] or 0), r["name"].lower()))


# --------------------------------------------------------------- outputs ----
def write_atomic(path, text):
    d = os.path.dirname(path) or "."
    if not os.path.isdir(d):
        os.makedirs(d, 0o755)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(text)
    os.replace(tmp, path)


def print_table(rows, skipped):
    wn = max([len(r["name"]) for r in rows] + [4])
    wg = max([len(r["group"]) for r in rows] + [5])
    print("%-*s  %-*s  %-18s  %-8s  %s"
          % (wn, "LEG", wg, "GROUP", "AGE", "WINDOW", "VERDICT"))
    for r in sort_rows(rows):
        print("%-*s  %-*s  %-18s  %-8s  %s%s"
              % (wn, r["name"], wg, r["group"], r["age_words"],
                 window_str(r["max_age_h"]), r["verdict"],
                 ("  — " + r["detail"]) if r["verdict"] in (NEVER, ERROR) else ""))
    for s in skipped:
        print("%-*s  %-*s  %-18s  %-8s  %s"
              % (wn, s["name"], wg, s["group"], "-", "-", "PARKED"))


def json_payload(rows, skipped, now, tzname, tzoff):
    c = counts_of(rows)
    return {
        "generated_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "generated_epoch": int(now),
        "timezone": tzname, "utc_offset": tzoff,
        "counts": {"total": len(rows), "ok": c[OK], "stale": c[STALE],
                   "never": c[NEVER], "error": c[ERROR], "parked": len(skipped)},
        "legs": [
            {"name": r["name"], "group": r["group"], "kind": r["kind"],
             "target": r["target"], "max_age_h": r["max_age_h"],
             "verdict": r["verdict"], "age_h": r["age_h"],
             "age_words": r["age_words"], "last_iso": r["last_iso"],
             "last_raw": r["last_raw"], "detail": r["detail"],
             "note": r["note"]}
            for r in sort_rows(rows)],
        "parked": skipped,
        "kit": "S230_FRESHNESS",
    }


HTML_HEAD = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Clinic freshness</title>
<style>
body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
 margin:0;padding:18px;background:#f6f7f9;color:#16202b;}
h1{font-size:20px;margin:0 0 4px 0;}
.sub{color:#5b6672;font-size:13px;margin-bottom:16px;}
h2{font-size:15px;margin:22px 0 6px 0;color:#33414f;
 border-bottom:1px solid #d8dee5;padding-bottom:4px;}
table{border-collapse:collapse;width:100%;background:#fff;
 box-shadow:0 1px 2px rgba(0,0,0,.08);}
th,td{padding:7px 10px;text-align:left;font-size:13px;
 border-bottom:1px solid #eceff2;vertical-align:top;}
th{background:#eef1f4;font-weight:600;color:#3d4a57;}
td.v{font-weight:700;white-space:nowrap;}
.OK{color:#1a7f37;} .STALE{color:#b25000;} .NEVER{color:#b3261e;}
.ERROR{color:#6b21a8;}
.banner{padding:10px 12px;border-radius:6px;margin-bottom:14px;font-size:14px;}
.good{background:#e7f5ec;color:#1a7f37;}
.bad{background:#fdeceb;color:#b3261e;}
.note{color:#6b7581;font-size:12px;}
.foot{margin-top:26px;color:#6b7581;font-size:12px;line-height:1.5;}
</style></head><body>
"""


def render_html(rows, skipped, now, tzname, tzoff):
    e = html.escape
    c = counts_of(rows)
    gen = time.strftime("%d-%b-%Y %H:%M", time.localtime(now))
    head = ("%d legs &middot; %d OK &middot; %d stale &middot; %d never"
            % (len(rows), c[OK], c[STALE], c[NEVER]))
    if c[ERROR]:
        head += " &middot; %d error" % c[ERROR]
    head += " &middot; generated %s %s" % (e(gen), e(tzname))
    bad = c[STALE] + c[NEVER] + c[ERROR]
    out = [HTML_HEAD, "<h1>Clinic freshness</h1>\n",
           '<div class="sub">Every automated leg of the estate, and how long '
           'ago it last succeeded. Times are %s (clock offset %s).</div>\n'
           % (e(tzname), e(tzoff))]
    out.append('<div class="banner %s">%s</div>\n'
               % ("bad" if bad else "good", head))
    groups = []
    for r in rows:
        if r["group"] not in groups:
            groups.append(r["group"])
    for g in sorted(groups, key=lambda x: (min(RANK.get(r["verdict"], 3)
                                               for r in rows if r["group"] == x), x)):
        out.append("<h2>%s</h2>\n<table>\n" % e(g))
        out.append("<tr><th>Leg</th><th>Last success</th><th>Age</th>"
                   "<th>Window</th><th>Verdict</th></tr>\n")
        for r in sort_rows([r for r in rows if r["group"] == g]):
            bits = [r["note"]] if r["note"] else []
            if r["verdict"] in (NEVER, ERROR) and r["detail"]:
                bits.insert(0, r["detail"])
            note = " · ".join(bits)
            out.append("<tr><td>%s%s</td><td>%s</td><td>%s</td><td>%s</td>"
                       '<td class="v %s">%s</td></tr>\n'
                       % (e(r["name"]),
                          ('<div class="note">%s</div>' % e(note)) if note else "",
                          e(when_str(r["last_epoch"])), e(r["age_words"]),
                          e(window_str(r["max_age_h"])),
                          r["verdict"], r["verdict"]))
        out.append("</table>\n")
    if skipped:
        out.append("<h2>Parked (not checked)</h2>\n<table>\n"
                   "<tr><th>Leg</th><th>Why it is parked</th></tr>\n")
        for s in skipped:
            out.append("<tr><td>%s</td><td>%s</td></tr>\n"
                       % (e(s["name"]), e(s["note"] or "disabled in legs.json")))
        out.append("</table>\n")
    out.append('<div class="foot">'
               "<b>OK</b> — succeeded inside its window. "
               "<b>STALE</b> — it ran once, but not recently enough. "
               "<b>NEVER</b> — there is no sign it has ever run. "
               "<b>ERROR</b> — the collector could not read it; the leg or its "
               "declaration needs a look.<br>"
               "A green pipeline that cannot state its age is not green, it is "
               "unmeasured.</div>\n</body></html>\n")
    return "".join(out)


# ----------------------------------------------------------------- state ----
def load_state(path):
    if os.path.exists(path):
        try:
            with open(path) as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                return data
        except Exception as ex:
            log("WARNING: state file unreadable (%s) — starting a fresh one" % ex)
    return {}


def prune_shouted(shouted, today):
    """Keep only the last few days: the record exists to stop repeats today,
    not to be an archive."""
    keep = {}
    for k, v in shouted.items():
        day = k.rsplit("|", 1)[-1]
        if day >= _days_ago(today, 3):
            keep[k] = v
    return keep


def _days_ago(today, n):
    return time.strftime("%Y-%m-%d", time.localtime(
        time.mktime(time.strptime(today, "%Y-%m-%d")) - n * 86400))


# ----------------------------------------------------------------- shout ----
def post_ntfy(url, title, body):
    """Best-effort push. Its own function so the WALK can stub it and assert on
    exactly what WOULD have been sent, with no network anywhere in the test."""
    req = urllib.request.Request(url, data=body.encode("utf-8"),
                                 headers={"Title": title, "Priority": "default"})
    urllib.request.urlopen(req, timeout=10).read()
    return True


def shout_body(rows, total, html_out):
    lines = ["%d of %d legs are not fresh:" % (len(rows), total)]
    for r in sort_rows(rows):
        lines.append("%-5s %s — %s (window %s)"
                     % (r["verdict"], r["name"], r["age_words"],
                        window_str(r["max_age_h"])))
    lines.append("page: " + html_out)
    return "\n".join(lines)


def do_shout(conf, rows, state, today, html_out, total):
    """One consolidated message, and at most once per leg per calendar day."""
    url = conf.get("NTFY_URL")
    bad = [r for r in rows if r["verdict"] != OK]
    if not bad:
        return "nothing to shout about"
    shouted = state.get("shouted") or {}
    fresh = [r for r in bad if ("%s|%s" % (r["name"], today)) not in shouted]
    if not fresh:
        return "already shouted about every stale leg today — staying quiet"
    if not url:
        return ("NTFY_URL is not set in the conf — %d leg(s) would have been"
                " shouted about" % len(fresh))
    cap = int_conf(conf, "SHOUT_MAX_LINES", 12)
    shown = sort_rows(fresh)[:cap]
    body = shout_body(shown, total, html_out)
    if len(fresh) > len(shown):
        body += "\n...and %d more on the page" % (len(fresh) - len(shown))
    title = conf.get("NTFY_TITLE") or "Clinic freshness"
    try:
        post_ntfy(url, title, body)
    except Exception as ex:
        return ("ntfy push FAILED (%s) — not recorded, it will be retried on the"
                " next run" % str(ex)[:120])
    for r in fresh:
        shouted["%s|%s" % (r["name"], today)] = r["verdict"]
    state["shouted"] = prune_shouted(shouted, today)
    return "shouted about %d leg(s)" % len(fresh)


# ----------------------------------------------------------------- modes ----
def _setup():
    conf = load_conf()
    p = paths_of(conf)
    if not os.path.exists(p["LEGS_FILE"]):
        die(EXIT_LEGS, "no legs file at", p["LEGS_FILE"],
            "— this job watches what it is told to watch and never guesses.")
    try:
        legs = load_legs(p["LEGS_FILE"], p)
    except Exception as ex:
        die(EXIT_LEGS, "legs file %s is not readable JSON: %s" % (p["LEGS_FILE"], ex))
    if not legs:
        die(EXIT_LEGS, "legs file %s declares no legs." % p["LEGS_FILE"])
    return conf, p, legs


def check(shout=False):
    conf, p, legs = _setup()
    now = time.time()
    tzname, tzoff = tz_label()
    rows, skipped = collect(legs, now)
    c = counts_of(rows)

    print_table(rows, skipped)
    write_atomic(p["JSON_OUT"], json.dumps(
        json_payload(rows, skipped, now, tzname, tzoff), indent=1) + "\n")
    write_atomic(p["HTML_OUT"], render_html(rows, skipped, now, tzname, tzoff))

    state = load_state(p["STATE_FILE"])
    said = ""
    if shout:
        said = do_shout(conf, rows, state, today_str(), p["HTML_OUT"], len(rows))
        log("shout:", said)

    state.update({
        "last_run_iso": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)),
        "last_run_epoch": int(now),
        "legs_checked": len(rows), "parked": len(skipped),
        "ok": c[OK], "stale": c[STALE], "never": c[NEVER], "error": c[ERROR],
        "not_ok_legs": sorted(r["name"] for r in rows if r["verdict"] != OK),
        "timezone": tzname, "utc_offset": tzoff,
        "kit": "S230_FRESHNESS",
    })
    state.setdefault("shouted", {})
    write_atomic(p["STATE_FILE"], json.dumps(state, indent=1) + "\n")

    line = ("%s legs=%d ok=%d stale=%d never=%d error=%d parked=%d%s"
            % (state["last_run_iso"], len(rows), c[OK], c[STALE], c[NEVER],
               c[ERROR], len(skipped), (" shout=" + said) if shout else ""))
    with open(p["SUMMARY_FILE"], "a") as fh:
        fh.write(line + "\n")
    log("SUMMARY:", line)
    log("wrote:", p["JSON_OUT"], "·", p["HTML_OUT"], "·", p["STATE_FILE"])
    bad = c[STALE] + c[NEVER] + c[ERROR]
    if bad:
        log("%d leg(s) are not fresh — the page names them." % bad)
        return EXIT_STALE
    log("every leg is inside its window.")
    return EXIT_OK


def list_mode():
    """What is declared, and nothing else: no target is opened, no output is
    written. Safe to run at any moment on a busy box."""
    conf, p, legs = _setup()
    wn = max([len(l["name"]) for l in legs] + [4])
    wg = max([len(l["group"]) for l in legs] + [5])
    print("%-*s  %-*s  %-12s  %-8s  %s"
          % (wn, "LEG", wg, "GROUP", "KIND", "WINDOW", "TARGET"))
    for l in legs:
        print("%-*s  %-*s  %-12s  %-8s  %s%s"
              % (wn, l["name"], wg, l["group"], l["kind"],
                 window_str(l["max_age_h"]) if l["max_age_h"] else "-",
                 l["target"], "   [PARKED]" if l.get("disabled") else ""))
    log("%d leg(s) declared in %s · %d parked"
        % (len(legs), p["LEGS_FILE"], len([l for l in legs if l.get("disabled")])))
    return EXIT_OK


def main(argv):
    args = argv[1:]
    shout = "--shout" in args
    words = [a for a in args if not a.startswith("-")]
    mode = words[0] if words else "check"
    if mode == "check":
        sys.exit(check(shout=shout))
    elif mode == "list":
        sys.exit(list_mode())
    else:
        print("usage: freshness.py [check] [--shout] | list")
        sys.exit(EXIT_USAGE)


if __name__ == "__main__":
    main(sys.argv)
