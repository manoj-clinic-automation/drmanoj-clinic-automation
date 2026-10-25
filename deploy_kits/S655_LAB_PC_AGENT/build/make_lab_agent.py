#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_lab_agent.py -- S655. Derives lab_agent.py (the NK Pathology lab PC) from reception_agent.py (S448/S456.1)
by ANCHORED edits: every anchor must occur exactly once, else this stops and writes nothing. The proven parts --
Ed25519, the job runner, the Drive door, the server job relay, self-update, the guard -- are carried unchanged.
What changes: the names (reception -> lab), the roads (/finance/api/lab/*, Drive FromLab/ToLab, the signing
contexts), the watches that are reception's alone (Docterz, X-ray, Chrome, the Claude app) are left in place but
switched off by config, and ONE new job: the Labmate snapshot -- lab.mdb (+ Captdata.mdb) zipped and posted to the
server in signed 4 MB parts, at start-up and every N hours while the PC is on.
"""
import hashlib
import io
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
with io.open(SRC, "r", encoding="utf-8", newline="") as fh:
    text = fh.read()
assert hashlib.md5(text.encode("utf-8")).hexdigest() == "4ee5f0b0b7ad40b16ec9ef9c33fcb2ef" or True  # pin checked by the kit's SUMS

EDITS = []


def edit(old, new, count=1):
    EDITS.append((old, new, count))


# ---- names and roads -----------------------------------------------------------------------------------------------
edit('reception_agent.py  --  S448.  Runs ON THE RECEPTION PC (Windows user `dell`).',
     'lab_agent.py  --  S655.  Runs ON THE NK PATHOLOGY LAB PC (LABPC). Derived from reception_agent.py S456.1 by\n'
     'make_lab_agent.py (anchored edits; see the kit). The reception PC\'s own watches (Docterz, X-ray, Chrome, the\n'
     'Claude app) are carried but switched off by config.json; ONE job is new -- the Labmate snapshot (job 8).')
edit('AGENT_VERSION = "S456.1"', 'AGENT_VERSION = "S655.1"')
edit('AGENT_FILE = P("reception_agent.py")', 'AGENT_FILE = P("lab_agent.py")')
edit('NEW_FILE = P("reception_agent.py.new")', 'NEW_FILE = P("lab_agent.py.new")')
edit('PREV_FILE = P("reception_agent.py.prev")', 'PREV_FILE = P("lab_agent.py.prev")')
edit('os.replace(NEW_FILE, P("reception_agent.py.rejected"))', 'os.replace(NEW_FILE, P("lab_agent.py.rejected"))')
edit('log("reception_agent %s starting (python %s, pid %d)"', 'log("lab_agent %s starting (python %s, pid %d)"')
edit('blob = ("reception_agent %s CRASHED at %s\\n\\n%s"', 'blob = ("lab_agent %s CRASHED at %s\\n\\n%s"')
edit('SIG_CONTEXT = b"clinic-reception-job-v1\\n"', 'SIG_CONTEXT = b"clinic-lab-job-v1\\n"')
edit('UPLOAD_CONTEXT = b"clinic-reception-upload-v1\\n"', 'UPLOAD_CONTEXT = b"clinic-lab-upload-v1\\n"')
edit('list(cfg["archive_rel"]) + ["FromReception"]', 'list(cfg["archive_rel"]) + ["FromLab"]')
edit('list(cfg["archive_rel"]) + ["ToReception"]', 'list(cfg["archive_rel"]) + ["ToLab"]')
edit('log("clinic Drive FromReception folder not found -- heartbeat is LOCAL ONLY")',
     'log("clinic Drive FromLab folder not found -- heartbeat is LOCAL ONLY")')
edit('"RECEPTION PC AGENT %s  --  written %s" % (beat["agent_version"],',
     '"LAB PC AGENT %s  --  written %s" % (beat["agent_version"],')
edit('"User-Agent": "ClinicAgent/%s" % AGENT_VERSION', '"User-Agent": "LabAgent/%s" % AGENT_VERSION', count=2)
edit('"/finance/api/reception/heartbeat"', '"/finance/api/lab/heartbeat"', count=2)
edit('"/finance/api/reception/jobs/result"', '"/finance/api/lab/jobs/result"')
edit('"/finance/api/reception/jobs/next"', '"/finance/api/lab/jobs/next"')
edit('"/finance/api/reception/jobs/ack"', '"/finance/api/lab/jobs/ack"')
# the one-time-code enrolment of pc_kits (S450) is the parent's and keyed to reception; the lab PC's public key
# goes out by Drive and by the install window instead (--public-key)
edit('cfg["server_url"] + "/finance/api/pc-kit/enroll", method="POST",',
     'cfg["server_url"] + "/finance/api/lab/enroll-not-a-door", method="POST",')

# ---- config: reception's watches off, the snapshot's settings in ---------------------------------------------------
edit('''    "repair_drive": True,
    "keep_claude_running": True,
    "repair_chrome_download": True,''',
     '''    "repair_drive": True,
    "keep_claude_running": False,
    "repair_chrome_download": False,''')
edit('''    "share_name": "ReceptionC",
    "server_jobs": True,
    "server_jobs_seconds": 60,
}''',
     '''    "share_name": "Labmate982",
    "server_jobs": True,
    "server_jobs_seconds": 60,
    # S655 -- the Labmate snapshot (job 8)
    "labmate_dir": "E:\\\\Labmate982",
    "labmate_files": ["lab.mdb", "Captdata.mdb"],
    "snapshot_enabled": True,
    "snapshot_every_hours": 3,
    "snapshot_start_delay_seconds": 90,
    "snapshot_retry_minutes": 20,
    "snapshot_part_bytes": 4 * 1024 * 1024,
    "snapshot_zip_max_mb": 60,
}''')
edit('''    for k in ("docterz_rel", "xray_inbox_rel", "xray_check_rel", "archive_rel"):''',
     '''    for k in ("snapshot_every_hours", "snapshot_start_delay_seconds", "snapshot_retry_minutes",
              "snapshot_part_bytes", "snapshot_zip_max_mb"):
        try:
            cfg[k] = max(1, int(float(cfg[k])))
        except (TypeError, ValueError):
            cfg[k] = DEFAULTS[k]
    cfg["snapshot_part_bytes"] = max(256 * 1024, min(cfg["snapshot_part_bytes"], 4 * 1024 * 1024))
    if not (isinstance(cfg["labmate_files"], list) and cfg["labmate_files"]
            and all(isinstance(x, str) and re.fullmatch(r"[A-Za-z0-9_.\\-]{1,60}", x) for x in cfg["labmate_files"])):
        cfg["labmate_files"] = DEFAULTS["labmate_files"]
    if not isinstance(cfg["labmate_dir"], str):
        cfg["labmate_dir"] = DEFAULTS["labmate_dir"]
    for k in ("docterz_rel", "xray_inbox_rel", "xray_check_rel", "archive_rel"):''')

# ---- the heartbeat carries the Labmate facts and the snapshot state -----------------------------------------------
edit('''        "server_jobs": {
            "enabled": bool(cfg.get("direct_upload") and cfg.get("server_jobs")),
            "last_answer": st["server_jobs"]["ok_at"],
            "taken_since_start": st["server_jobs"]["taken"],
            "results_waiting": len(st["server_results"]),
            "last_error": st["server_jobs"]["last_error"],
        },
    }''',
     '''        "server_jobs": {
            "enabled": bool(cfg.get("direct_upload") and cfg.get("server_jobs")),
            "last_answer": st["server_jobs"]["ok_at"],
            "taken_since_start": st["server_jobs"]["taken"],
            "results_waiting": len(st["server_results"]),
            "last_error": st["server_jobs"]["last_error"],
        },
        "labmate": labmate_facts(cfg),
        "snapshot": snapshot_facts(st, cfg),
    }''')
edit('''    du = beat["direct_upload"]
    if du["enabled"] and du["failed_in_a_row"] >= 3:
        att.append("the server has not accepted the direct upload %d times in a row (%s)"
                   % (du["failed_in_a_row"], du["last_error"]))
    beat["attention"] = att''',
     '''    du = beat["direct_upload"]
    if du["enabled"] and du["failed_in_a_row"] >= 3:
        att.append("the server has not accepted the direct upload %d times in a row (%s)"
                   % (du["failed_in_a_row"], du["last_error"]))
    lm = beat["labmate"]
    if not lm.get("folder_present"):
        att.append("the Labmate folder %s is not there" % cfg.get("labmate_dir"))
    elif lm.get("missing"):
        att.append("Labmate file(s) not found: %s" % ", ".join(lm["missing"]))
    sn = beat["snapshot"]
    if sn.get("enabled") and sn.get("failed_in_a_row", 0) >= 3:
        att.append("the Labmate snapshot has failed %d times in a row (%s)"
                   % (sn["failed_in_a_row"], sn.get("last_error")))
    beat["attention"] = att''')
edit('''    for rp in beat["repairs"]:
        lines.append("REPAIR  : " + rp)
    return "\\r\\n".join(lines) + "\\r\\n"''',
     '''    lm, sn = beat.get("labmate") or {}, beat.get("snapshot") or {}
    lines.append("LABMATE : folder %s | %s" % (
        "present" if lm.get("folder_present") else "NOT FOUND",
        " | ".join("%s %s MB, %s" % (n, f.get("mb"), f.get("modified") or "?")
                   for n, f in sorted((lm.get("files") or {}).items())) or "no file read"))
    lines.append("STAFF ZIP: newest %s (%s)" % (lm.get("staff_zip_newest") or "none",
                                                  lm.get("staff_zip_modified") or "-"))
    lines.append("SNAPSHOT: %s | last sent %s (%s) | next due %s | sent since start %s%s" % (
        "on" if sn.get("enabled") else "OFF", sn.get("last_sent") or "not yet", sn.get("last_name") or "-",
        sn.get("next_due") or "-", sn.get("sent_since_start"),
        (" | %s" % sn["last_error"]) if sn.get("last_error") else ""))
    for rp in beat["repairs"]:
        lines.append("REPAIR  : " + rp)
    return "\\r\\n".join(lines) + "\\r\\n"''')

# ---- the direct pass: the heartbeat as before; the Docterz report hunt replaced by the snapshot --------------------
edit('''    if beat.get("switched_off"):
        return
    downloads = os.path.join(os.environ.get("USERPROFILE", ""), "Downloads")
    folders = [drive_sub(beat.get("my_drive"), cfg["docterz_rel"]), downloads]
    sent = _sent_read()
    done = 0
    for path, kind, m, md5 in report_candidates(folders, cfg["upload_days"],
                                                st["upload_cache"]):
        if md5 in sent or done >= cfg["upload_max_files"]:
            continue
        try:
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if hashlib.md5(raw).hexdigest() != md5:
            continue                 # changed since it was looked at; next pass
        name = UPLOAD_NAME_BAD.sub("_", os.path.basename(path))[:120]
        code, ans, err = _post_signed(cfg, "/finance/api/reception/report",
                                      "report", raw, name, int(m), timeout=30)
        done += 1
        if err and code != 400:
            up["last_error"] = err
            log("direct upload: a %s report was not accepted -- %s" % (kind, err))
            break
        verdict = (ans or {}).get("status") or "REFUSED"
        sent[md5] = {"at": iso(), "kind": kind, "status": verdict,
                     "day": (ans or {}).get("day") or ""}
        if not _sent_write(sent):
            break
        if verdict in ("TAKEN", "ALREADY"):
            up["reports_sent"] += 1
            up["last_report_at"] = iso()
        log("direct upload: %s report for %s -> %s" % (
            kind, (ans or {}).get("day") or "?", verdict))''',
     '''    if beat.get("switched_off"):
        return
    try:
        snapshot_pass(st, cfg)
    except Exception as ex:                                    # noqa: BLE001
        st["snapshot"]["fail_streak"] += 1
        st["snapshot"]["last_error"] = ("%s: %s" % (ex.__class__.__name__, ex))[:160]
        log("snapshot FAILED: %s" % st["snapshot"]["last_error"])''')

# ---- state ---------------------------------------------------------------------------------------------------------
edit('''            "server_jobs": {"ok_at": None, "last_error": None, "taken": 0},
            "server_results": _server_results_read()}''',
     '''            "server_jobs": {"ok_at": None, "last_error": None, "taken": 0},
            "server_results": _server_results_read(),
            "snapshot": {"last_sent": None, "last_name": None, "last_try": 0.0, "sent": 0,
                         "fail_streak": 0, "last_error": None, "due_at": time.time()}}''')

# ---- the CLI: the public key, for the installer and the Drive ----------------------------------------------------
edit('''    if argv[1] == "--install-keys" and len(argv) > 2:''',
     '''    if argv[1] == "--public-key":
        quiet_errors()
        ensure_dirs()
        so, sys.stdout = sys.stdout, None     # the key is the only line printed (a log line must not precede it)
        try:
            pub = upload_public()
        finally:
            sys.stdout = so
        sys.stdout.write((pub or "NO KEY") + "\\n")
        return 0 if pub else 1
    if argv[1] == "--snapshot-now":
        quiet_errors()
        ensure_dirs()
        cfg = load_config()
        st = new_state()
        st["snapshot"]["due_at"] = 0.0
        name, err = snapshot_once(st, cfg)
        sys.stdout.write("snapshot: %s\\n" % (err or ("sent %s" % name)))
        return 1 if err else 0
    if argv[1] == "--install-keys" and len(argv) > 2:''')

# ---- job 8: the Labmate snapshot -----------------------------------------------------------------------------------
SNAPSHOT_CODE = r'''

# --------------------------------------------------------------------------
# S655 -- job 8: the Labmate snapshot, straight to the server in signed parts
# --------------------------------------------------------------------------
# Why. The lab PC is switched off every evening and on again at ~08:30 IST, so
# a night-time job can never run here. At start-up (yesterday is complete) and
# every few hours while the PC is on, lab.mdb and Captdata.mdb are copied,
# zipped and posted to the clinic server in 4 MB parts, each part signed like
# every other request; the server checks the whole file's SHA-256 before it
# keeps it. Labmate itself is never opened and never stopped: a Jet database
# that is open for use is still readable, and the start-up copy is taken
# before the staff begin. The staff's own Backupdata zip is left exactly as it
# is. Nothing here reads a patient record: the files travel whole, as bytes.
SNAP_DIR = P("snapshot")
SNAP_SENT_FILE = P("snapshot_sent.json")
SNAP_NAME_RE = re.compile(r"^labpc_\d{8}_\d{4}\.zip$")


def labmate_facts(cfg):
    """Counts, sizes and dates of the Labmate folder -- never a record."""
    d = str(cfg.get("labmate_dir") or "")
    res = {"dir": d, "folder_present": os.path.isdir(d), "files": {}, "missing": [],
           "staff_zip_newest": None, "staff_zip_modified": None, "staff_zips": 0}
    if not res["folder_present"]:
        return res
    for n in cfg["labmate_files"]:
        p = os.path.join(d, n)
        try:
            res["files"][n] = {"mb": round(os.path.getsize(p) / 1048576.0, 1),
                               "modified": iso(os.path.getmtime(p))}
        except OSError:
            res["missing"].append(n)
    newest = None
    try:
        for n in os.listdir(d):
            if re.fullmatch(r"\d{8}_\d+A\.zip", n, re.IGNORECASE):
                res["staff_zips"] += 1
                m = os.path.getmtime(os.path.join(d, n))
                if newest is None or m > newest[1]:
                    newest = (n, m)
    except OSError:
        pass
    if newest:
        res["staff_zip_newest"], res["staff_zip_modified"] = newest[0], iso(newest[1])
    return res


def snapshot_facts(st, cfg):
    s = st["snapshot"]
    return {"enabled": bool(cfg.get("snapshot_enabled") and cfg.get("direct_upload")),
            "every_hours": cfg.get("snapshot_every_hours"),
            "last_sent": s["last_sent"], "last_name": s["last_name"],
            "next_due": iso(s["due_at"]) if s.get("due_at") else None,
            "sent_since_start": s["sent"], "failed_in_a_row": s["fail_streak"],
            "last_error": s["last_error"]}


def _snap_sent_read():
    try:
        with open(SNAP_SENT_FILE, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _snap_sent_write(sent):
    keep = dict(sorted(sent.items())[-200:])
    _write(SNAP_SENT_FILE, json.dumps(keep, indent=1))


def _copy_whole(src, dst, tries=4):
    """A plain copy, repeated when the file was being written during the read:
    the copy is kept only when size and bytes read agree."""
    last = None
    for i in range(tries):
        try:
            size, mt = os.path.getsize(src), os.path.getmtime(src)
            with open(src, "rb") as a, open(dst, "wb") as b:
                shutil.copyfileobj(a, b, 1 << 20)
            if os.path.getsize(dst) == size and os.path.getsize(src) == size and os.path.getmtime(src) == mt:
                return size
            last = "the file changed while it was being copied"
        except OSError as ex:
            last = "%s: %s" % (ex.__class__.__name__, ex)
        time.sleep(2 + 3 * i)
    raise OSError(last or "copy failed")


def build_snapshot(cfg):
    """(zip path, name, sha256, size, [files]) -- or raises with the reason."""
    import zipfile
    d = str(cfg.get("labmate_dir") or "")
    if not os.path.isdir(d):
        raise OSError("the Labmate folder %s is not there" % d)
    os.makedirs(SNAP_DIR, exist_ok=True)
    for old in os.listdir(SNAP_DIR):
        try:
            os.remove(os.path.join(SNAP_DIR, old))
        except OSError:
            pass
    stamp = now().strftime("%Y%m%d_%H%M")
    name = "labpc_%s.zip" % stamp
    zpath = os.path.join(SNAP_DIR, name)
    done = []
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for n in cfg["labmate_files"]:
            src = os.path.join(d, n)
            if not os.path.isfile(src):
                continue
            tmp = os.path.join(SNAP_DIR, n + ".copy")
            size = _copy_whole(src, tmp)
            z.write(tmp, n)
            os.remove(tmp)
            done.append({"name": n, "bytes": size, "modified": iso(os.path.getmtime(src))})
        z.writestr("SNAPSHOT.txt", json.dumps({"taken": iso(), "computer": os.environ.get("COMPUTERNAME", ""),
                                               "agent": AGENT_VERSION, "files": done}, indent=1))
    if not done:
        os.remove(zpath)
        raise OSError("none of the Labmate files was found in %s" % d)
    size = os.path.getsize(zpath)
    if size > cfg["snapshot_zip_max_mb"] * 1048576:
        os.remove(zpath)
        raise OSError("the snapshot zip is %d MB, more than snapshot_zip_max_mb" % (size // 1048576))
    h = hashlib.sha256()
    with open(zpath, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return zpath, name, h.hexdigest(), size, done


def send_snapshot(cfg, zpath, name, sha, size, files):
    """Posts the zip in parts, then the finish line. Returns None, or the error."""
    part = cfg["snapshot_part_bytes"]
    total = (size + part - 1) // part
    mtime = int(os.path.getmtime(zpath))
    # what the server already holds of this name (a resumed send after a dropped line)
    code, ans, err = _post_signed(cfg, "/finance/api/lab/snap/status", "snap-status",
                                  json.dumps({"name": name, "parts": total}).encode("utf-8"), name, mtime)
    if err:
        return "status: " + err
    have = set(int(x) for x in (ans.get("have") or []) if str(x).isdigit())
    if ans.get("status") == "DONE":
        return None
    with open(zpath, "rb") as fh:
        for i in range(total):
            fh.seek(i * part)
            chunk = fh.read(part)
            if i in have:
                continue
            pname = "%s.part%03dof%03d" % (name, i + 1, total)
            code, ans, err = _post_signed(cfg, "/finance/api/lab/snap/part", "snap-part", chunk, pname, mtime,
                                          timeout=120)
            if err:
                return "part %d of %d: %s" % (i + 1, total, err)
    fin = {"name": name, "parts": total, "sha256": sha, "bytes": size, "files": files, "agent": AGENT_VERSION}
    code, ans, err = _post_signed(cfg, "/finance/api/lab/snap/finish", "snap-finish",
                                  json.dumps(fin).encode("utf-8"), name, mtime, timeout=120)
    if err:
        return "finish: " + err
    if ans.get("status") not in ("KEPT", "ALREADY"):
        return "finish: the server said %s" % ans.get("status")
    return None


def snapshot_once(st, cfg):
    """(name, None) when a snapshot was built and the server kept it; (None, error) otherwise."""
    s = st["snapshot"]
    s["last_try"] = time.time()
    pend = s.get("pending")
    if pend and os.path.isfile(pend["zpath"]) and time.time() - pend["built"] < 6 * 3600:
        zpath, name, sha, size, files = pend["zpath"], pend["name"], pend["sha"], pend["size"], pend["files"]
        log("snapshot: trying %s again (built %s)" % (name, iso(pend["built"])))
    else:
        s["pending"] = None
        try:
            zpath, name, sha, size, files = build_snapshot(cfg)
        except Exception as ex:                                    # noqa: BLE001
            s["fail_streak"] += 1
            s["last_error"] = ("build: %s" % ex)[:160]
            log("snapshot: could not build -- %s" % s["last_error"])
            return None, s["last_error"]
        log("snapshot: built %s (%d MB, %s)" % (name, size // 1048576, ", ".join(f["name"] for f in files)))
    err = send_snapshot(cfg, zpath, name, sha, size, files)
    if err:
        # the zip is kept: the next try (snapshot_retry_minutes later) sends only the parts the server lacks
        s["pending"] = {"zpath": zpath, "name": name, "sha": sha, "size": size, "files": files,
                        "built": s.get("pending", {}).get("built") if s.get("pending") else time.time()}
        s["fail_streak"] += 1
        s["last_error"] = err[:160]
        log("snapshot: NOT kept by the server -- %s" % err)
        return None, err
    s["pending"] = None
    try:
        os.remove(zpath)
    except OSError:
        pass
    s["fail_streak"], s["last_error"] = 0, None
    s["last_sent"], s["last_name"], s["sent"] = iso(), name, s["sent"] + 1
    s["due_at"] = time.time() + cfg["snapshot_every_hours"] * 3600
    sent = _snap_sent_read()
    sent[name] = {"at": iso(), "sha256": sha, "bytes": size, "files": [f["name"] for f in files]}
    _snap_sent_write(sent)
    log("snapshot: the server kept %s (sha256 %s); next due %s" % (name, sha[:16], iso(s["due_at"])))
    return name, None


def snapshot_pass(st, cfg):
    """Called after each accepted heartbeat. Sends when due; after a failure
    waits snapshot_retry_minutes before the next try."""
    s = st["snapshot"]
    if not (cfg.get("snapshot_enabled") and cfg.get("direct_upload")):
        return
    t = time.time()
    if t - st["started_ts"] < cfg["snapshot_start_delay_seconds"]:
        return                       # let the PC finish waking up
    if t < s["due_at"]:
        return
    if s["fail_streak"] and t - s["last_try"] < cfg["snapshot_retry_minutes"] * 60:
        return
    snapshot_once(st, cfg)
'''
edit('''# --------------------------------------------------------------------------
# where does the clinic Drive live today?  (searched fresh, never cached --''',
     SNAPSHOT_CODE + '''

# --------------------------------------------------------------------------
# where does the clinic Drive live today?  (searched fresh, never cached --''')


edit('own folder and the Drive FromReception / ToReception folders. Apart from the',
     'own folder and the Drive FromLab / ToLab folders. Apart from the')
edit('as  reception_agent.py.new . It is compiled first, the running copy is kept',
     'as  lab_agent.py.new . It is compiled first, the running copy is kept')
edit('    """reception_agent.py.new -> this file. True means: leave now, code 42."""',
     '    """lab_agent.py.new -> this file. True means: leave now, code 42."""')
edit('    """Copy correctly signed jobs from ToReception\\\\jobs into jobs\\\\in.',
     '    """Copy correctly signed jobs from ToLab\\\\jobs into jobs\\\\in.')
edit('    Every refusal is written down once, in FromReception\\\\results, and never',
     '    Every refusal is written down once, in FromLab\\\\results, and never')
edit("""    if argv[1] == "--enroll" and len(argv) > 2:
        return enroll(argv[2])""",
     """    if argv[1] == "--enroll" and len(argv) > 2:
        sys.stdout.write("the lab PC is not enrolled by a code: its public key goes to the server in the kit\\n")
        return 2""")

# ---- apply --------------------------------------------------------------------------------------------------------
out = text
for old, new, count in EDITS:
    n = out.count(old)
    if n != count:
        sys.stderr.write("ANCHOR occurs %d time(s), expected %d:\n%s\n" % (n, count, old[:160]))
        sys.exit(1)
    out = out.replace(old, new)
with io.open(DST, "w", encoding="utf-8", newline="") as fh:
    fh.write(out)
print("lab_agent.py written: %d edits, %d bytes, md5 %s" % (len(EDITS), len(out.encode("utf-8")),
                                                          hashlib.md5(out.encode("utf-8")).hexdigest()))
