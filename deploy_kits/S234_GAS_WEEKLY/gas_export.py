#!/root/wa/venv/bin/python3
# =============================================================================
#  gas_export.py  ·  Session 234  ·  S234_GAS_WEEKLY  ·  v1
#
#  THE SCRIPTS IN GOOGLE ARE THE ORIGINAL. EVERY COPY OF THEM GOES STALE THE
#  FIRST TIME SOMEONE EDITS IN THE BROWSER, AND NOTHING SAYS SO.
#
#  WHY THIS EXISTS
#  ---------------
#  S230 found 2,122 lines of live clinic automation that existed in no
#  repository at all, and exported three projects by hand into
#  `deploy_kits/S230_GAS_EXPORT/`. That export is a PHOTOGRAPH taken on
#  07-Sep-2026. Nothing refreshes it. The same census measured the cost of
#  that: `VPS_Push_UPI.gs` in the repository was already a whole generation
#  behind the live project, and `Bank_Statement_Relay.gs` held a pre-survey
#  copy — both silently, both discovered only because somebody went and looked.
#
#  So this is not a backup job with a diff bolted on. **It is a drift
#  detector that happens to leave a backup behind.** The weekly question it
#  answers is: has anyone edited these projects in the browser since the copy
#  we are all reading was taken?
#
#  IT EXPORTS. IT NEVER WRITES TO GOOGLE.
#  No project is edited, no trigger is created, changed or read, no Script
#  Property is touched. The only Google call this file can make is a read:
#  `files.get` for metadata and `files.export` for content. The selftest
#  asserts that no other Drive endpoint appears in the source.
#
#  🛑 THE CALLBACK TRACKER IS DENYLISTED IN CODE, NOT MERELY LEFT OUT.
#  HOLD 2 (owner, 07-Sep-2026) is absolute: the Clinic Callback Tracker is not
#  to be touched at all — "no edit, no trigger change, NO RE-EXPORT, no tidy" —
#  and its abandoned v1 ancestor is under the same rule because it carries an
#  unscoped `removeTriggers()`. A hold that lives only in a document is one
#  config edit away from being broken by a future session that never read it.
#  So the ids sit in DENY below, and a conf naming one is refused with EXIT 44
#  before a single network call is made. Removing them from DENY takes a
#  deliberate code change and the owner's word, which is exactly the bar a
#  standing hold should have.
#
#  WHAT IT COMPARES, AND WHY TWO COMPARISONS AND NOT ONE
#  ----------------------------------------------------
#    1. against LAST WEEK'S export  -> "what changed in Google this week"
#    2. against the REPOSITORY copy -> "how stale is the copy people read"
#  They answer different questions and either can be clean while the other is
#  not. A project edited twice since S230 and not at all this week is quiet on
#  (1) and seven days stale on (2); that is the exact shape that hid
#  `VPS_Push_UPI.gs` for a generation.
#
#  Comparison is by CONTENT, file by file, md5 of the exact bytes — never by
#  Drive's modifiedTime, which moves when nothing meaningful changed and can
#  sit still through a same-second edit.
#
#  ⚠ MASKED FILES. The repository copy of DailyClinicReports has four
#  MyOperator values masked (S230 §4), so it can NEVER match live byte for
#  byte and would shout drift every week for ever. Files listed in MASKED are
#  compared on LINE COUNT AND FUNCTION NAMES instead, and the report says so
#  rather than pretending. When those four values move into Script Properties
#  the entry comes out of MASKED and full byte comparison resumes.
#
#  REFUSAL STANCES — a bad week must never overwrite a good export
#    EXIT 10  no conf, no service-account key, or no GAS list   -> nothing written
#    EXIT 11  the google libraries are not importable           -> nothing written
#    EXIT 41  a project that exported last run is now refused   -> its PREVIOUS
#             export is left exactly where it is
#    EXIT 42  a project lost more than SHRINK_GUARD_PCT of its  -> that project is
#             lines, or lost files entirely                        not swapped in
#    EXIT 43  Google rate-limited us after retries              -> nothing swapped
#    EXIT 44  a denylisted project id appears in the conf       -> nothing at all
#
#  41 and 43 wear DIFFERENT WORDS on purpose. S233 sent the owner to Google to
#  re-share five sheets that were already shared correctly, because a quota
#  refusal printed the permission message. One message for every failure is a
#  message that lies.
#
#  Modes:
#    preflight  open every configured project WITHOUT writing anything.
#    run        the export, the two diffs, and the report.
#    diff       re-run both comparisons against what is already on disk.
#               Read-only, no network.
#    list       what is on disk and how old it is. No network.
#    selftest   every rule above against fixtures. No network, no live path.
# =============================================================================

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time

CONF_PATH = os.environ.get("GAS_CONF",
                           "/root/state_backup/clinic_state_backup.conf")
GAS_DIR_DEFAULT = "/root/state_backup/gas"
REPO_COPY_DEFAULT = ("/root/deploy/repo/deploy_kits/S230_GAS_EXPORT")
SHRINK_GUARD_PCT_DEFAULT = 20.0
API_MIN_INTERVAL_S = 1.2
API_MAX_RETRIES = 5
RETRY_STATUS = (429, 500, 502, 503, 504)

PROJECT_META = "_PROJECT.json"
DRIFT_FILE = "_DRIFT.json"
TAKEN_AT = "_TAKEN_AT.json"
STAGING = ".staging"

EXIT_OK = 0
EXIT_CONF = 10
EXIT_DEPS = 11
EXIT_UNREACHABLE = 41
EXIT_SHRANK = 42
EXIT_RATELIMIT = 43
EXIT_DENIED = 44

IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

# 🛑 HOLD 2, owner, 07-Sep-2026 — enforced here and not only written down.
# Prefix match, because an id may be recorded truncated in some documents.
DENY = {
    "148sj-FT2t": "the Clinic Callback Tracker — the live call console. The "
                  "owner's standing hold is 'not to be touched at all', and "
                  "it names re-export explicitly.",
}

# Files whose repository copy is deliberately masked (S230 §4) and therefore
# can never match live byte for byte. Compared on shape instead.
MASKED = {
    ("DailyClinicReports", "Code.gs"):
        "four MyOperator values are masked in the repository copy (S230 §4). "
        "Byte comparison is meaningless until they move to Script Properties.",
}

DRIVE_META = "https://www.googleapis.com/drive/v3/files/%s?fields=id,name,modifiedTime,mimeType"
DRIVE_EXPORT = ("https://www.googleapis.com/drive/v3/files/%s/export"
                "?mimeType=application/vnd.google-apps.script%%2Bjson")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def stamp():
    return datetime.datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")


def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def die(code, msg):
    sys.stderr.write("REFUSED (%d): %s\n" % (code, msg))
    sys.stderr.flush()
    sys.exit(code)


# ------------------------------------------------------------------- conf ----
def read_conf(path=None):
    p = path or CONF_PATH
    if not os.path.exists(p):
        die(EXIT_CONF, "no conf at %s . This job reads the SAME conf the S230 "
                       "bundle and the S233 pull already use." % p)
    conf = {}
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            conf[k.strip()] = v.strip().strip('"').strip("'")
    return conf


def parse_projects(conf):
    """GAS=<fileId>:<label>,<fileId>:<label>  — the same shape as SHEETS=."""
    raw = conf.get("GAS", "")
    if not raw:
        die(EXIT_CONF,
            "the conf has no GAS= line, so there is nothing to export. Add one "
            "in the same shape as SHEETS=, e.g. GAS=<fileId>:<label>. Nothing "
            "was written.")
    out, seen = [], set()
    for part in [x.strip() for x in raw.split(",") if x.strip()]:
        fid, _, label = part.partition(":")
        fid, label = fid.strip(), label.strip()
        if not fid or not label:
            die(EXIT_CONF, "GAS entry %r is not <fileId>:<label>." % part)
        for bad, why in DENY.items():
            if fid.startswith(bad):
                die(EXIT_DENIED,
                    "the conf names a project this system is forbidden to "
                    "touch: %s\nNothing was exported and no network call was "
                    "made. If this hold has genuinely been lifted, it is "
                    "lifted in code and by the owner, not in a conf file."
                    % why)
        if label in seen:
            die(EXIT_CONF, "two GAS entries share the label %r." % label)
        seen.add(label)
        out.append((fid, label))
    return out


def gas_dir(conf):
    return conf.get("GAS_DIR", GAS_DIR_DEFAULT)


def repo_copy(conf):
    return conf.get("GAS_REPO_COPY", REPO_COPY_DEFAULT)


def guard_pct(conf):
    try:
        return float(conf.get("SHRINK_GUARD_PCT", SHRINK_GUARD_PCT_DEFAULT))
    except ValueError:
        return SHRINK_GUARD_PCT_DEFAULT


# -------------------------------------------------------------------- api ----
_last_call = [0.0]


def _pace():
    gap = time.time() - _last_call[0]
    if gap < API_MIN_INTERVAL_S:
        time.sleep(API_MIN_INTERVAL_S - gap)
    _last_call[0] = time.time()


def make_session(conf):
    sa = conf.get("SA_JSON", "")
    if not sa or not os.path.exists(sa):
        die(EXIT_CONF, "SA_JSON in the conf does not point at a readable "
                       "service-account key (%r)." % sa)
    try:
        from google.oauth2 import service_account
        import google.auth.transport.requests as gart
    except ImportError as ex:
        die(EXIT_DEPS,
            "the google auth libraries are not importable by this python "
            "(%s). Use /root/wa/venv/bin/python3 — the system python does not "
            "have them." % ex)
    creds = service_account.Credentials.from_service_account_file(
        sa, scopes=SCOPES)
    return gart.AuthorizedSession(creds)


def api_get(sess, url, label):
    """One paced, retried GET. Tells a permission refusal from a rate refusal,
    because sending the owner to Google to re-share something already shared
    is a worse outcome than the failure itself."""
    last = None
    for attempt in range(API_MAX_RETRIES):
        _pace()
        r = sess.get(url)
        if r.status_code == 200:
            return r
        last = r
        if r.status_code in RETRY_STATUS:
            time.sleep(min(2 ** attempt, 20))
            continue
        break
    code = last.status_code if last is not None else 0
    if code in (401, 403, 404):
        die(EXIT_UNREACHABLE,
            "PERMISSION — %s could not be opened (HTTP %d). THIS one does mean "
            "go to Google: open the script project, Share, and give the "
            "backup's service account Viewer access. The other projects are "
            "untouched and their previous exports still stand."
            % (label, code))
    if code == 429:
        die(EXIT_RATELIMIT,
            "RATE LIMIT — Google refused %s after %d tries (HTTP 429). THE "
            "SHARING IS FINE. Do not re-share anything. Let next week's run "
            "take it, or raise the pacing." % (label, API_MAX_RETRIES))
    die(EXIT_UNREACHABLE,
        "%s could not be fetched (HTTP %s)." % (label, code))


# ----------------------------------------------------------------- export ----
def safe_name(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("_") or "unnamed"


def md5_bytes(b):
    return hashlib.md5(b).hexdigest()


def fn_names(src):
    """Top-level function names, in file order. The shape used to compare a
    masked file, where bytes cannot be compared honestly."""
    return re.findall(r"^\s*function\s+([A-Za-z0-9_$]+)\s*\(", src, re.M)


def write_project(dest, meta, files):
    os.makedirs(dest, exist_ok=True)
    out = {"title": meta.get("name", ""),
           "file_id": meta.get("id", ""),
           "modified_time": meta.get("modifiedTime", ""),
           "pulled_at_ist": stamp(), "files": []}
    for f in files:
        name = f["name"] + ("." + {"server_js": "gs",
                                   "html": "html",
                                   "json": "json"}.get(f.get("type"), "txt"))
        if f["name"] == "appsscript":
            name = "appsscript.json"
        body = (f.get("source") or "")
        path = os.path.join(dest, safe_name(name))
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(body)
        out["files"].append({
            "name": safe_name(name), "type": f.get("type", ""),
            "lines": body.count("\n") + (1 if body and not
                                         body.endswith("\n") else 0),
            "bytes": len(body.encode("utf-8")),
            "md5": md5_bytes(body.encode("utf-8")),
            "md5_trimmed": md5_bytes(body.rstrip().encode("utf-8")),
            "functions": fn_names(body),
        })
    out["line_total"] = sum(x["lines"] for x in out["files"])
    with open(os.path.join(dest, PROJECT_META), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    return out


def read_meta(d):
    """The metadata for a folder of exported script files.

    ⚠ THE FALLBACK IS THE POINT, NOT A CONVENIENCE. The repository copy this
    job compares against is `deploy_kits/S230_GAS_EXPORT/`, which was written
    BY HAND at S230 and has no `_PROJECT.json` in it. v1 of this file returned
    None for it and the run reported "there is no repository copy to compare
    against" for all three projects — which reads like a note and is in fact
    the entire second comparison silently doing nothing. Found on the first
    live install, behind 24 green selftests and a 26-check walk (F-378).

    So: read the meta file when there is one, and otherwise BUILD the same
    shape by reading the files that are actually on disk."""
    p = os.path.join(d, PROJECT_META)
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as fh:
                return json.load(fh)
        except (ValueError, OSError):
            return None
    return scan_dir_meta(d)


# Files that live beside an export without being part of it.
NOT_SOURCE = {"README.md", "READ_ME_FIRST.md", "SUMS.md5", "MD5SUMS.txt",
              "KIT_ID.txt"}
SOURCE_EXT = (".gs", ".json", ".html")


def scan_dir_meta(d):
    """Build export metadata from a plain folder of script files. Counts lines
    and hashes exactly as write_project does, so the two are comparable."""
    if not os.path.isdir(d):
        return None
    files = []
    for name in sorted(os.listdir(d)):
        p = os.path.join(d, name)
        if not os.path.isfile(p) or name in NOT_SOURCE:
            continue
        if name.startswith("_") or not name.lower().endswith(SOURCE_EXT):
            continue
        try:
            with open(p, encoding="utf-8") as fh:
                body = fh.read()
        except (OSError, UnicodeDecodeError):
            continue
        files.append({
            "name": name, "type": "",
            "lines": body.count("\n") + (1 if body and not
                                          body.endswith("\n") else 0),
            "bytes": len(body.encode("utf-8")),
            "md5": md5_bytes(body.encode("utf-8")),
            "md5_trimmed": md5_bytes(body.rstrip().encode("utf-8")),
            "functions": fn_names(body),
        })
    if not files:
        return None
    return {"title": os.path.basename(d), "file_id": "", "modified_time": "",
            "pulled_at_ist": "", "scanned": True, "files": files,
            "line_total": sum(f["lines"] for f in files)}


def judge_shrink(label, new, old, pct):
    """A bad week must never overwrite a good export."""
    if not old:
        return []
    bad = []
    gone = {f["name"] for f in old["files"]} - {f["name"] for f in new["files"]}
    if gone:
        bad.append("%s: %d file(s) present last run and missing now: %s"
                   % (label, len(gone), ", ".join(sorted(gone))))
    o, n = old.get("line_total", 0), new.get("line_total", 0)
    if o and n < o * (1 - pct / 100.0):
        bad.append("%s: %d lines last run, %d now — a fall of %.0f%%, beyond "
                   "the %.0f%% guard" % (label, o, n, 100.0 * (o - n) / o, pct))
    return bad


# ------------------------------------------------------------------ diffs ----
def compare(label, new_meta, other_meta, other_what):
    """One comparison, file by file, by content. Returns a list of findings."""
    if not other_meta:
        return [{"label": label, "against": other_what, "kind": "no_copy",
                 "file": "", "detail": "there is no %s to compare against"
                                       % other_what}]
    out = []
    nf = {f["name"]: f for f in new_meta["files"]}
    of = {f["name"]: f for f in other_meta["files"]}
    for name in sorted(set(nf) - set(of)):
        out.append({"label": label, "against": other_what, "kind": "added",
                    "file": name,
                    "detail": "in Google, absent from the %s" % other_what})
    for name in sorted(set(of) - set(nf)):
        out.append({"label": label, "against": other_what, "kind": "removed",
                    "file": name,
                    "detail": "in the %s, absent from Google" % other_what})
    for name in sorted(set(nf) & set(of)):
        a, b = nf[name], of[name]
        if (label, name) in MASKED:
            if a["lines"] != b["lines"] or a["functions"] != b["functions"]:
                out.append({"label": label, "against": other_what,
                            "kind": "changed_shape", "file": name,
                            "detail": "%d lines / %d functions in Google vs "
                                      "%d / %d in the %s — compared on SHAPE "
                                      "because %s"
                                      % (a["lines"], len(a["functions"]),
                                         b["lines"], len(b["functions"]),
                                         other_what, MASKED[(label, name)])})
            continue
        if a["md5"] != b["md5"]:
            ta, tb = a.get("md5_trimmed"), b.get("md5_trimmed")
            if ta and tb and ta == tb:
                out.append({"label": label, "against": other_what,
                            "kind": "changed_whitespace", "file": name,
                            "detail": "differs ONLY in trailing whitespace "
                                      "from the %s — not an edit" % other_what})
                continue
            out.append({"label": label, "against": other_what,
                        "kind": "changed", "file": name,
                        "detail": "%d lines in Google vs %d in the %s"
                                  % (a["lines"], b["lines"], other_what)})
    return out


def run_diffs(conf, labels=None):
    root = gas_dir(conf)
    repo = repo_copy(conf)
    found = []
    if not os.path.isdir(root):
        return found
    for label in sorted(labels or os.listdir(root)):
        d = os.path.join(root, label)
        if not os.path.isdir(d) or label.startswith("."):
            continue
        new = read_meta(d)
        if not new:
            continue
        found += compare(label, new, read_meta(os.path.join(repo, label)),
                         "repository copy")
    return found


# -------------------------------------------------------------------- run ----
def do_run(conf, dry=False):
    projects = parse_projects(conf)
    root = gas_dir(conf)
    repo = repo_copy(conf)
    staging = os.path.join(root, STAGING)
    os.makedirs(staging, exist_ok=True)
    sess = make_session(conf)
    pct = guard_pct(conf)

    results, complaints, week_findings, repo_findings = {}, [], [], []
    for fid, label in projects:
        meta = api_get(sess, DRIVE_META % fid, label).json()
        body = api_get(sess, DRIVE_EXPORT % fid, label).json()
        files = body.get("files", [])
        if not files:
            complaints.append("%s: the export came back with no files at all"
                              % label)
            continue
        staged = os.path.join(staging, label)
        if os.path.isdir(staged):
            shutil.rmtree(staged)
        new = write_project(staged, meta, files)
        old = read_meta(os.path.join(root, label))
        bad = judge_shrink(label, new, old, pct)
        if bad:
            complaints += bad
            continue
        week_findings += compare(label, new, old, "copy from last run")
        repo_findings += compare(label, new, read_meta(
            os.path.join(repo, label)), "repository copy")
        results[label] = (staged, new)

    if complaints:
        for c in complaints:
            log("  REFUSING to swap in — " + c)
        die(EXIT_SHRANK,
            "%d project(s) came back smaller or emptier than last run. NOTHING "
            "was swapped in; every previous export is exactly where it was. "
            "Look at the project in Google — the project is what changed, not "
            "the backup." % len(complaints))

    if dry:
        return {"projects": len(results), "week": week_findings,
                "repo": repo_findings, "dry": True}

    for label, (staged, _new) in results.items():
        final = os.path.join(root, label)
        if os.path.isdir(final):
            shutil.rmtree(final)
        shutil.move(staged, final)

    taken = {"taken_at_ist": stamp(),
             "projects": {l: {"lines": m["line_total"],
                              "files": len(m["files"]),
                              "modified_time": m.get("modified_time", "")}
                          for l, (_s, m) in results.items()}}
    with open(os.path.join(root, TAKEN_AT), "w", encoding="utf-8") as fh:
        json.dump(taken, fh, indent=2, sort_keys=True)
    with open(os.path.join(root, DRIFT_FILE), "w", encoding="utf-8") as fh:
        json.dump({"checked_at_ist": stamp(),
                   "since_last_run": week_findings,
                   "against_repository": repo_findings}, fh, indent=2,
                  sort_keys=True)
    return {"projects": len(results), "week": week_findings,
            "repo": repo_findings, "dry": False}


def report(res):
    log("gas_export  ·  %s" % stamp())
    log("  projects exported   %d" % res["projects"])
    for title, key in (("CHANGED IN GOOGLE SINCE LAST RUN", "week"),
                       ("THE REPOSITORY COPY IS BEHIND", "repo")):
        f = [x for x in res[key] if x["kind"] != "no_copy"]
        none = [x for x in res[key] if x["kind"] == "no_copy"]
        log("")
        if not f:
            log("  %s: nothing" % title.lower())
        else:
            log("  %s — %d finding(s):" % (title, len(f)))
            for x in f:
                log("    %-24s %-22s %s" % (x["label"], x["file"],
                                            x["detail"]))
        for x in none:
            log("    %-24s (%s)" % (x["label"], x["detail"]))
    return EXIT_OK


def do_list(conf):
    root = gas_dir(conf)
    p = os.path.join(root, TAKEN_AT)
    if not os.path.exists(p):
        log("nothing exported yet under %s" % root)
        return EXIT_CONF
    with open(p, encoding="utf-8") as fh:
        t = json.load(fh)
    log("last export  %s" % t.get("taken_at_ist", "?"))
    for label, m in sorted(t.get("projects", {}).items()):
        log("  %-26s %4d lines · %d file(s) · modified %s"
            % (label, m["lines"], m["files"], m.get("modified_time", "?")))
    return EXIT_OK


# --------------------------------------------------------------- selftest ----
def _fake_project(name, files):
    return {"name": name, "id": "x", "modifiedTime": "2026-09-08T00:00:00Z"}, \
        [{"name": n, "type": "server_js", "source": s} for n, s in files]


def selftest():
    fails, n = [], [0]

    def check(name, cond):
        n[0] += 1
        if not cond:
            fails.append(name)
            log("  FAIL  %s" % name)

    tmp = tempfile.mkdtemp(prefix="gassel_")

    # ---- the denylist, before anything else ------------------------------
    code = None
    try:
        parse_projects({"GAS": "148sj-FT2tSOMETHINGSOMETHING:callback"})
    except SystemExit as ex:
        code = ex.code
    check("HOLD 2: a denylisted project id in the conf REFUSES with exit 44",
          code == EXIT_DENIED)
    code = None
    try:
        parse_projects({"GAS": "1WFQrMh:daily,148sj-FT2tXX:sneaky"})
    except SystemExit as ex:
        code = ex.code
    check("HOLD 2: it is caught even when hidden among valid entries",
          code == EXIT_DENIED)
    check("HOLD 2: an ordinary conf still parses",
          [l for _f, l in parse_projects({"GAS": "1abc:daily,1def:upi"})]
          == ["daily", "upi"])
    code = None
    try:
        parse_projects({"GAS": "1abc:daily,1def:daily"})
    except SystemExit as ex:
        code = ex.code
    check("conf: two entries with the same label are refused", code == EXIT_CONF)
    code = None
    try:
        parse_projects({})
    except SystemExit as ex:
        code = ex.code
    check("conf: no GAS= line at all is refused, not silently skipped",
          code == EXIT_CONF)

    # ---- shape helpers ----------------------------------------------------
    check("functions: top-level names are found in order",
          fn_names("function a(){}\n  function b_2(x){}\n// function c(){}")
          == ["a", "b_2"])

    # ---- writing and comparing -------------------------------------------
    meta, files = _fake_project("Daily", [("Code", "function a(){}\n"),
                                          ("appsscript", "{}\n")])
    d1 = os.path.join(tmp, "run1", "daily")
    m1 = write_project(d1, meta, files)
    check("export: one file per script file plus a meta file",
          sorted(os.listdir(d1)) == ["Code.gs", PROJECT_META,
                                     "appsscript.json"])
    check("export: appsscript keeps its .json name",
          os.path.exists(os.path.join(d1, "appsscript.json")))
    check("export: line totals are counted", m1["line_total"] == 2)

    d2 = os.path.join(tmp, "run2", "daily")
    m2 = write_project(d2, *_fake_project(
        "Daily", [("Code", "function a(){}\n"), ("appsscript", "{}\n")]))
    check("diff: an identical export reports nothing",
          compare("daily", m2, m1, "copy from last run") == [])

    m3 = write_project(os.path.join(tmp, "run3", "daily"), *_fake_project(
        "Daily", [("Code", "function a(){}\nfunction b(){}\n"),
                  ("appsscript", "{}\n")]))
    f = compare("daily", m3, m1, "copy from last run")
    check("diff: an edited file is reported once, by content",
          len(f) == 1 and f[0]["kind"] == "changed" and f[0]["file"]
          == "Code.gs")

    m4 = write_project(os.path.join(tmp, "run4", "daily"), *_fake_project(
        "Daily", [("Code", "function a(){}\n"), ("appsscript", "{}\n"),
                  ("New", "function z(){}\n")]))
    f = compare("daily", m4, m1, "copy from last run")
    check("diff: a NEW file in Google is reported as added",
          len(f) == 1 and f[0]["kind"] == "added" and f[0]["file"] == "New.gs")
    f = compare("daily", m1, m4, "repository copy")
    check("diff: a file only in the copy is reported as removed",
          len(f) == 1 and f[0]["kind"] == "removed")
    check("diff: no copy at all is a finding, not silence",
          compare("daily", m1, None, "repository copy")[0]["kind"] == "no_copy")

    # ---- the masked file --------------------------------------------------
    live = write_project(os.path.join(tmp, "mlive", "DailyClinicReports"),
                         *_fake_project("D", [("Code", "var K='REAL';\n"
                                                       "function a(){}\n")]))
    repo = write_project(os.path.join(tmp, "mrepo", "DailyClinicReports"),
                         *_fake_project("D", [("Code", "var K='****';\n"
                                                       "function a(){}\n")]))
    f = compare("DailyClinicReports", live, repo, "repository copy")
    check("masked: a masked file with the SAME shape does NOT shout drift "
          "every week", f == [])
    repo2 = write_project(os.path.join(tmp, "mrepo2", "DailyClinicReports"),
                          *_fake_project("D", [("Code", "var K='****';\n")]))
    f = compare("DailyClinicReports", live, repo2, "repository copy")
    check("masked: but a real change of shape IS reported",
          len(f) == 1 and f[0]["kind"] == "changed_shape")
    check("masked: and the report says why it compared on shape",
          "masked" in f[0]["detail"])

    # ---- F-378: A FOLDER WITH NO _PROJECT.json IS STILL A COPY ------------
    # This is the check whose absence let the entire second comparison do
    # nothing while reporting a benign-looking note. It is written first here
    # so it is never quietly dropped again.
    handmade = os.path.join(tmp, "handmade", "daily")
    os.makedirs(handmade)
    with open(os.path.join(handmade, "Code.gs"), "w") as fh:
        fh.write("function a(){}\n")
    with open(os.path.join(handmade, "appsscript.json"), "w") as fh:
        fh.write("{}\n")
    with open(os.path.join(handmade, "READ_ME_FIRST.md"), "w") as fh:
        fh.write("not source\n")
    scanned = read_meta(handmade)
    check("F-378: a hand-made export folder with NO _PROJECT.json is still "
          "read as a copy", scanned is not None)
    check("F-378: and prose beside it is not counted as source",
          sorted(f["name"] for f in scanned["files"])
          == ["Code.gs", "appsscript.json"])
    check("F-378: its line count matches the exporter's own counting",
          scanned["line_total"] == 2)
    check("F-378: AND COMPARING AGAINST IT REPORTS NOTHING WHEN IT MATCHES "
          "— not 'no copy'", compare("daily", m1, scanned,
                                     "repository copy") == [])
    with open(os.path.join(handmade, "Code.gs"), "w") as fh:
        fh.write("function a(){}\nfunction b(){}\n")
    f = compare("daily", m1, read_meta(handmade), "repository copy")
    check("F-378: and it reports a real difference when there is one",
          len(f) == 1 and f[0]["kind"] == "changed")

    # ---- a trailing newline is not an edit --------------------------------
    nonl = os.path.join(tmp, "nonl", "daily")
    os.makedirs(nonl)
    with open(os.path.join(nonl, "Code.gs"), "w") as fh:
        fh.write("function a(){}")
    with open(os.path.join(nonl, "appsscript.json"), "w") as fh:
        fh.write("{}\n")
    f = compare("daily", m1, read_meta(nonl), "repository copy")
    check("whitespace: a missing trailing newline is reported as whitespace, "
          "NOT as an edit",
          len(f) == 1 and f[0]["kind"] == "changed_whitespace")
    check("whitespace: and the report says it is not an edit",
          "not an edit" in f[0]["detail"])

    # ---- the shrink guard -------------------------------------------------
    big = write_project(os.path.join(tmp, "big", "p"), *_fake_project(
        "P", [("Code", "x\n" * 100)]))
    small = write_project(os.path.join(tmp, "small", "p"), *_fake_project(
        "P", [("Code", "x\n" * 50)]))
    check("shrink: half the lines trips the guard",
          judge_shrink("p", small, big, 20.0) != [])
    ok = write_project(os.path.join(tmp, "ok", "p"), *_fake_project(
        "P", [("Code", "x\n" * 95)]))
    check("shrink: a 5% fall does not", judge_shrink("p", ok, big, 20.0) == [])
    lost = write_project(os.path.join(tmp, "lost", "p"), *_fake_project(
        "P", [("Code", "x\n" * 100)]))
    two = write_project(os.path.join(tmp, "two", "p"), *_fake_project(
        "P", [("Code", "x\n" * 100), ("Other", "y\n" * 100)]))
    check("shrink: a file that vanished entirely trips the guard even when "
          "the lines look fine", judge_shrink("p", lost, two, 20.0) != [])

    # ---- the promise: this file cannot write to Google --------------------
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    head = src.split("def selftest")[0]
    check("read-only: no Drive endpoint but files.get and files.export appears",
          not re.search(r"googleapis\.com/drive/v3/files/[^\"']*"
                        r"(permissions|copy|update|trash|watch)", head))
    check("read-only: the scope requested is drive.readonly",
          SCOPES == ["https://www.googleapis.com/auth/drive.readonly"])
    check("read-only: no POST, PATCH, PUT or DELETE anywhere in the file",
          not re.search(r"\.(post|patch|put|delete)\s*\(", head))
    check("HOLD 2: the callback tracker id is present in DENY",
          any(k.startswith("148sj") for k in DENY))

    shutil.rmtree(tmp)
    log("")
    log("selftest: %d checks, %d failures" % (n[0], len(fails)))
    for f in fails:
        log("  FAILED: %s" % f)
    return EXIT_OK if not fails else 1


# ------------------------------------------------------------------- main ----
def do_preflight(conf):
    projects = parse_projects(conf)
    sess = make_session(conf)
    ok = 0
    for fid, label in projects:
        meta = api_get(sess, DRIVE_META % fid, label).json()
        log("  %-26s reachable · %s · modified %s"
            % (label, meta.get("name", "?"), meta.get("modifiedTime", "?")))
        ok += 1
    log("%d of %d project(s) reachable" % (ok, len(projects)))
    log("PREFLIGHT OK")
    return EXIT_OK


def main():
    ap = argparse.ArgumentParser(
        description="Weekly Apps Script export and drift check. Reads Google, "
                    "never writes to it.")
    ap.add_argument("mode", choices=("preflight", "run", "diff", "list",
                                     "selftest"))
    ap.add_argument("--conf", default=None)
    a = ap.parse_args()
    if a.mode == "selftest":
        sys.exit(selftest())
    conf = read_conf(a.conf)
    if a.mode == "preflight":
        sys.exit(do_preflight(conf))
    if a.mode == "list":
        sys.exit(do_list(conf))
    if a.mode == "diff":
        findings = run_diffs(conf)
        sys.exit(report({"projects": 0, "week": [], "repo": findings}))
    sys.exit(report(do_run(conf)))


if __name__ == "__main__":
    main()
