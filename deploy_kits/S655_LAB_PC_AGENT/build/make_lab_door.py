#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_lab_door.py -- S655. Derives /root/finance/lab_door.py (this project's file) from the parent's
reception_door.py (S449/S453/S457, md5 417ae384) by anchored edits: the Ed25519 verify, the signed-request gate,
the heartbeat and the whole job relay are carried as they are, under new names, keys, folders and contexts; the
Docterz report door and the two Docterz export-read doors are REMOVED (lines 288-321 and the S457 block) and the
Labmate SNAPSHOT doors put in their place; health_row is rewritten for the lab PC (not wired by this kit).
Every anchor must occur exactly once, else nothing is written.
"""
import hashlib
import io
import re
import sys

SRC, DST = sys.argv[1], sys.argv[2]
text = io.open(SRC, "r", encoding="utf-8", newline="").read()
if hashlib.md5(text.encode("utf-8")).hexdigest() != "417ae38496a505a866033be29167decf":
    sys.exit("reception_door.py is not the S457 file this patcher was written against")

# ---- 1. the docstring --------------------------------------------------------------------------------------------
head_end = text.index('"""\nimport base64')
NEW_HEAD = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lab_door.py -- kit S655_LAB_PC_AGENT (session 351, the NK Pathology chat, 25-Oct-2026, D784). THIS PROJECT'S FILE.

THE OWNER, 25-Oct-2026: "Go ahead with the lab PC agent ... plan a direct upload to the server from this PC also."

The NK Pathology lab PC (LABPC) runs Labmate; its data is one Access file, lab.mdb in E:/Labmate982, with Captdata.mdb
beside it. Until today nothing of it left that PC except the staff's own backup zip, kept on the same drive. The lab
agent (lab_agent.py, derived from reception_agent.py S456.1) now posts straight to this server over HTTPS, the same
road the reception PC uses (reception_door.py, S449/S453), and this file is that road's lab end -- derived from
reception_door.py by make_lab_door.py in the kit, so what is proven there is proven here:

  POST /finance/api/lab/heartbeat         the agent's heartbeat (COUNTS AND DATES ONLY -- the agent's own rule)
  POST /finance/api/lab/snap/status       what this server already holds of a snapshot (so a dropped send resumes)
  POST /finance/api/lab/snap/part         one part (<= 4 MB) of a snapshot zip: lab.mdb + Captdata.mdb, zipped on the PC
  POST /finance/api/lab/snap/finish       the whole: parts count, bytes and SHA-256; the server joins, checks, keeps
  POST /finance/api/lab/jobs/submit|next|ack|result|read   the job relay, exactly the reception relay (S453)
  POST /finance/api/lab/snap/list         the owner's PC reads what snapshots are here (signed by a job key)

NO SHARED SECRET TRAVELS. Each request is signed with an Ed25519 key made ON the lab PC that never leaves it; this
server holds only the PUBLIC key (lab_keys.txt). What is signed: a fixed context (clinic-lab-upload-v1), the kind, the
sender's clock, the part's name and time, and the SHA-256 of the body; a request more than 15 minutes from this
server's clock is refused. A snapshot is kept only when the joined parts' SHA-256 equals the one the PC signed in the
finish line, and only under /root/labdata/incoming/ (mode 700), where it is pruned after KEEP_DAYS. The bytes are
patient data: they are never logged and never served back by this door; the day page (a later kit) reads them here.

The paths are in finance_app's PUBLIC_PATHS (like the reception doors): the gate lets them reach this handler and
THIS HANDLER authenticates. With no key file the door answers 503 and takes nothing (fail closed).

Stdlib + Flask. Creates no table. Sends nothing anywhere. Queue: /root/labdata/lab_jobs (mode 700), pruned after 14 days.
"""
'''
text = NEW_HEAD + text[head_end + 4:]

EDITS = []


def edit(old, new, count=1):
    EDITS.append((old, new, count))


# ---- 2. constants ------------------------------------------------------------------------------------------------
edit('''HERE = os.path.dirname(os.path.abspath(__file__))
KEYS_FILE = os.environ.get("RECEPTION_KEYS", os.path.join(HERE, "reception_keys.txt"))
BEAT_FILE = os.environ.get("RECEPTION_BEAT", os.path.join(HERE, "reception_heartbeat.json"))
SIG_CONTEXT = b"clinic-reception-upload-v1\\n"
MAX_BEAT = 64 * 1024
MAX_REPORT = 5 * 1024 * 1024
MAX_SKEW = 900                  # seconds either side of this server's clock
RATE_PER_MIN = 60               # one PC: a heartbeat every 5 minutes and a few files a day
NAME_RE = re.compile(r"^[A-Za-z0-9 ._()\\-]{0,120}$")
# S453 -- the job relay
JOB_KEYS_FILE = os.environ.get("RECEPTION_JOB_KEYS", os.path.join(HERE, "reception_job_keys.txt"))
JOB_DIR = os.environ.get("RECEPTION_JOB_DIR", os.path.join(HERE, "reception_jobs"))
JOB_CONTEXT = b"clinic-reception-job-v1\\n"            # exactly what reception_sign.py signs: context, name, bytes
JOB_READ_CONTEXT = b"clinic-reception-job-read-v1\\n"''',
     '''HERE = os.path.dirname(os.path.abspath(__file__))
LAB_HOME = os.environ.get("LAB_HOME", "/root/labdata")
KEYS_FILE = os.environ.get("LAB_KEYS", os.path.join(LAB_HOME, "lab_keys.txt"))
BEAT_FILE = os.environ.get("LAB_BEAT", os.path.join(LAB_HOME, "lab_heartbeat.json"))
SNAP_DIR = os.environ.get("LAB_SNAP_DIR", os.path.join(LAB_HOME, "incoming"))
SNAP_INDEX = os.path.join(SNAP_DIR, "snapshots.json")
SIG_CONTEXT = b"clinic-lab-upload-v1\\n"
MAX_BEAT = 64 * 1024
MAX_PART = 4 * 1024 * 1024      # one part of a snapshot zip (the agent's snapshot_part_bytes is capped at this)
MAX_PARTS = 200                 # 800 MB -- lab.mdb is 73 MB today and zips to ~12 MB
MAX_FINISH = 64 * 1024
KEEP_DAYS = 30                  # snapshots kept on this box
PART_KEEP_HOURS = 48            # unfinished parts
MAX_SKEW = 900                  # seconds either side of this server's clock
RATE_PER_MIN = 120              # one PC: a heartbeat every 5 minutes, and up to ~20 parts in a minute when it sends
NAME_RE = re.compile(r"^[A-Za-z0-9 ._()\\-]{0,120}$")
SNAP_NAME_RE = re.compile(r"^labpc_\\d{8}_\\d{4}\\.zip$")
PART_NAME_RE = re.compile(r"^(labpc_\\d{8}_\\d{4}\\.zip)\\.part(\\d{3})of(\\d{3})$")
# S453 -- the job relay, this PC's own queue
JOB_KEYS_FILE = os.environ.get("LAB_JOB_KEYS", os.path.join(LAB_HOME, "lab_job_keys.txt"))
JOB_DIR = os.environ.get("LAB_JOB_DIR", os.path.join(LAB_HOME, "lab_jobs"))
JOB_CONTEXT = b"clinic-lab-job-v1\\n"                  # exactly what lab_sign.py signs: context, name, bytes
JOB_READ_CONTEXT = b"clinic-lab-job-read-v1\\n"''')
edit('bp = Blueprint("reception_door", __name__)', 'bp = Blueprint("lab_door", __name__)')
edit('return None, None, None, None, _no("NO_KEY", "no reception key is enrolled on this server -- nothing taken", 503)',
     'return None, None, None, None, _no("NO_KEY", "no lab PC key is enrolled on this server -- nothing taken", 503)')
edit('label = next((lab or "reception" for k, lab in keys if ed_verify(k, msg, sig)), None)',
     'label = next((lab or "labpc" for k, lab in keys if ed_verify(k, msg, sig)), None)')
edit('@bp.route("/finance/api/reception/heartbeat", methods=["POST"])\ndef api_reception_heartbeat():',
     '@bp.route("/finance/api/lab/heartbeat", methods=["POST"])\ndef api_lab_heartbeat():')
edit('''    tmp = "%s.%d.tmp" % (BEAT_FILE, os.getpid())
    try:
        with open(tmp, "w", encoding="utf-8") as fh:''',
     '''    tmp = "%s.%d.tmp" % (BEAT_FILE, os.getpid())
    try:
        os.makedirs(os.path.dirname(BEAT_FILE), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as fh:''')
for r in ("jobs/submit", "jobs/next", "jobs/ack", "jobs/result", "jobs/read"):
    edit('@bp.route("/finance/api/reception/%s", methods=["POST"])\ndef api_reception_job_%s():'
         % (r, r.split("/")[1]),
         '@bp.route("/finance/api/lab/%s", methods=["POST"])\ndef api_lab_job_%s():' % (r, r.split("/")[1]))

edit('"""Exactly what the reception agent signs (its own function of the same name builds the same bytes)."""',
     '"""Exactly what the lab agent signs (its own function of the same name builds the same bytes)."""')
edit('"""[(32 raw bytes, label)] from reception_keys.txt; [] shuts the door."""',
     '"""[(32 raw bytes, label)] from lab_keys.txt; [] shuts the door."""')

# ---- 3. the Docterz report door out, the snapshot doors in --------------------------------------------------------
REPORT_START = '@bp.route("/finance/api/reception/report", methods=["POST"])'
REPORT_END = '# ---------------------------------------------------------------------------------------------------------------------\n# S453 -- the job relay'
SNAPSHOT_DOORS = r'''# ---------------------------------------------------------------------------------------------------------------------
# S655 -- the Labmate snapshot, in signed parts
# ---------------------------------------------------------------------------------------------------------------------
def _snap_dirs():
    for d in (LAB_HOME, SNAP_DIR, os.path.join(SNAP_DIR, "_parts")):
        os.makedirs(d, exist_ok=True)
        try:
            os.chmod(d, 0o700)
        except OSError:
            pass


def _parts_dir(name):
    return os.path.join(SNAP_DIR, "_parts", name)


def _index_read():
    try:
        with open(SNAP_INDEX, "r", encoding="utf-8") as fh:
            got = json.load(fh)
        return got if isinstance(got, dict) else {}
    except (OSError, ValueError):
        return {}


def _index_write(idx):
    tmp = "%s.%d.tmp" % (SNAP_INDEX, os.getpid())
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(idx, fh, indent=1, sort_keys=True)
    os.chmod(tmp, 0o600)
    os.replace(tmp, SNAP_INDEX)


def _snap_log(event, name=""):
    try:
        with open(os.path.join(SNAP_DIR, "log.txt"), "a", encoding="utf-8") as fh:
            fh.write("%s | %s | %s\n" % (_ist_now().strftime("%Y-%m-%d %H:%M:%S"), event, name))
    except OSError:
        pass


def _prune_snapshots():
    """Finished snapshots older than KEEP_DAYS, part folders older than PART_KEEP_HOURS."""
    now = time.time()
    idx = _index_read()
    changed = False
    for name in list(idx):
        p = os.path.join(SNAP_DIR, name)
        try:
            if os.path.isfile(p) and now - os.path.getmtime(p) > KEEP_DAYS * 86400:
                os.remove(p)
                idx.pop(name, None)
                changed = True
                _snap_log("PRUNED after %d days" % KEEP_DAYS, name)
        except OSError:
            pass
    if changed:
        _index_write(idx)
    base = os.path.join(SNAP_DIR, "_parts")
    try:
        for n in os.listdir(base):
            d = os.path.join(base, n)
            if os.path.isdir(d) and now - os.path.getmtime(d) > PART_KEEP_HOURS * 3600:
                for f in os.listdir(d):
                    os.remove(os.path.join(d, f))
                os.rmdir(d)
                _snap_log("unfinished parts dropped after %d h" % PART_KEEP_HOURS, n)
    except OSError:
        pass


def _have_parts(name, total):
    d = _parts_dir(name)
    have = []
    try:
        for n in os.listdir(d):
            m = re.fullmatch(r"(\d{3})\.part", n)
            if m and 1 <= int(m.group(1)) <= total:
                have.append(int(m.group(1)) - 1)
    except OSError:
        pass
    return sorted(have)


@bp.route("/finance/api/lab/snap/status", methods=["POST"])
def api_lab_snap_status():
    label, body, name, _mtime, err = _signed("snap-status", 4096)
    if err:
        return err
    if not SNAP_NAME_RE.match(name):
        return _no("REFUSED", "not a snapshot name (labpc_YYYYMMDD_HHMM.zip)", 400)
    try:
        j = json.loads(body.decode("utf-8"))
        total = int(j.get("parts"))
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
        return _no("REFUSED", "the status line needs the parts count", 400)
    if not 1 <= total <= MAX_PARTS:
        return _no("REFUSED", "parts must be 1..%d" % MAX_PARTS, 400)
    _snap_dirs()
    _prune_snapshots()           # old parts folders go here too, not only after a successful finish
    if name in _index_read() and os.path.isfile(os.path.join(SNAP_DIR, name)):
        return jsonify(ok=True, status="DONE", name=name, have=[], message="this snapshot is already kept"), 200
    return jsonify(ok=True, status="PARTIAL", name=name, have=_have_parts(name, total)), 200


@bp.route("/finance/api/lab/snap/part", methods=["POST"])
def api_lab_snap_part():
    label, body, pname, _mtime, err = _signed("snap-part", MAX_PART)
    if err:
        return err
    m = PART_NAME_RE.match(pname)
    if not m:
        return _no("REFUSED", "not a part name (labpc_YYYYMMDD_HHMM.zip.partNNNofMMM)", 400)
    name, idx, total = m.group(1), int(m.group(2)), int(m.group(3))
    if not (1 <= total <= MAX_PARTS and 1 <= idx <= total):
        return _no("REFUSED", "part number out of range", 400)
    if not body:
        return _no("REFUSED", "an empty part", 400)
    _snap_dirs()
    if name in _index_read() and os.path.isfile(os.path.join(SNAP_DIR, name)):
        return jsonify(ok=True, status="ALREADY", name=name, part=idx, message="this snapshot is already kept"), 200
    d = _parts_dir(name)
    os.makedirs(d, exist_ok=True)
    try:
        os.chmod(d, 0o700)
    except OSError:
        pass
    try:
        _jwrite(os.path.join(d, "%03d.part" % idx), body)
        _jwrite(os.path.join(d, "total.txt"), str(total).encode("ascii"))
    except OSError as ex:
        return _no("NOT_KEPT", "could not write the part: %s" % str(ex)[:120], 500)
    return jsonify(ok=True, status="KEPT", name=name, part=idx, of=total, bytes=len(body)), 200


@bp.route("/finance/api/lab/snap/finish", methods=["POST"])
def api_lab_snap_finish():
    label, body, name, _mtime, err = _signed("snap-finish", MAX_FINISH)
    if err:
        return err
    if not SNAP_NAME_RE.match(name):
        return _no("REFUSED", "not a snapshot name", 400)
    try:
        j = json.loads(body.decode("utf-8"))
        total, size, sha = int(j.get("parts")), int(j.get("bytes")), str(j.get("sha256") or "").lower()
        if str(j.get("name")) != name or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise ValueError("name or sha")
    except (ValueError, TypeError, AttributeError, UnicodeDecodeError):
        return _no("REFUSED", "the finish line needs name, parts, bytes and sha256", 400)
    if not (1 <= total <= MAX_PARTS and 0 < size <= total * MAX_PART):
        return _no("REFUSED", "parts or bytes out of range", 400)
    _snap_dirs()
    idx = _index_read()
    final = os.path.join(SNAP_DIR, name)
    if name in idx and os.path.isfile(final):
        return jsonify(ok=True, status="ALREADY", name=name, sha256=idx[name].get("sha256"),
                       message="this snapshot is already kept"), 200
    have = _have_parts(name, total)
    if have != list(range(total)):
        missing = [i + 1 for i in range(total) if i not in have]
        return _no("INCOMPLETE", "parts missing: %s" % ", ".join(str(x) for x in missing[:20]), 409, missing=missing)
    d = _parts_dir(name)
    tmp = final + ".%d.tmp" % os.getpid()
    h = hashlib.sha256()
    n = 0
    try:
        with open(tmp, "wb") as out:
            for i in range(1, total + 1):
                with open(os.path.join(d, "%03d.part" % i), "rb") as fh:
                    chunk = fh.read(MAX_PART + 1)
                h.update(chunk)
                out.write(chunk)
                n += len(chunk)
        os.chmod(tmp, 0o600)
    except OSError as ex:
        try:
            os.remove(tmp)
        except OSError:
            pass
        return _no("NOT_KEPT", "could not join the parts: %s" % str(ex)[:120], 500)
    if n != size or h.hexdigest() != sha:
        try:
            os.remove(tmp)
        except OSError:
            pass
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)
        _snap_log("REFUSED: joined %d bytes sha %s, the PC said %d bytes sha %s -- parts dropped"
                  % (n, h.hexdigest()[:16], size, sha[:16]), name)
        return _no("NOT_WHOLE", "the joined parts are not the bytes the PC signed (%d bytes, sha %s); send again"
                   % (n, h.hexdigest()[:16]), 409)
    os.replace(tmp, final)
    for f in os.listdir(d):
        os.remove(os.path.join(d, f))
    os.rmdir(d)
    files = j.get("files") if isinstance(j.get("files"), list) else []
    idx[name] = {"sha256": sha, "bytes": size, "parts": total, "from": label,
                 "received_ts": int(time.time()), "received_ist": _ist_now().isoformat(timespec="seconds"),
                 "agent": str(j.get("agent") or "")[:20],
                 "files": [{"name": str(f.get("name"))[:60], "bytes": int(f.get("bytes") or 0),
                            "modified": str(f.get("modified") or "")[:25]} for f in files if isinstance(f, dict)][:10]}
    _index_write(idx)
    _snap_log("KEPT %d bytes in %d parts, sha256 %s, from %s" % (size, total, sha[:16], label), name)
    _prune_snapshots()
    return jsonify(ok=True, status="KEPT", name=name, bytes=size, sha256=sha, server_time=int(time.time())), 200


SNAP_LIST_CONTEXT = b"clinic-lab-snap-list-v1\n"


@bp.route("/finance/api/lab/snap/list", methods=["POST"])
def api_lab_snap_list():
    """The owner's PC reads what is here: names, sizes, dates -- never the bytes. Signed by a job key like S457's list."""
    if not _rate_ok():
        return _no("SLOW_DOWN", "more than %d requests in a minute" % RATE_PER_MIN, 429)
    j = _json_body(4096)
    if j is None:
        return _no("REFUSED", "not a JSON object", 400)
    keys = job_keys()
    if not keys:
        return _no("NO_KEY", "no key is on this server -- the door is shut", 503)
    ts, sig_hex = str(j.get("ts") or ""), str(j.get("sig") or "").strip()
    if not re.fullmatch(r"\d{9,11}", ts) or not re.fullmatch(r"[0-9a-fA-F]{128}", sig_hex):
        return _no("NOT_YOU", "this door needs the time and a signature", 401)
    if not any(ed_verify(k, SNAP_LIST_CONTEXT + ts.encode("ascii"), bytes.fromhex(sig_hex)) for k, _ in keys):
        return _no("NOT_YOU", "the signature does not match a key on this server", 401)
    if abs(int(time.time()) - int(ts)) > MAX_SKEW:
        return _no("CLOCK", "signed more than 15 minutes from this server's clock", 401, server_time=int(time.time()))
    _snap_dirs()
    idx = _index_read()
    out = []
    for name in sorted(idx):
        p = os.path.join(SNAP_DIR, name)
        row = dict(idx[name])
        row["name"] = name
        row["present"] = os.path.isfile(p)
        out.append(row)
    return jsonify(ok=True, status="LIST", snapshots=out, keep_days=KEEP_DAYS, server_time=int(time.time())), 200


'''
a, b = text.index(REPORT_START), text.index(REPORT_END)
text = text[:a] + SNAPSHOT_DOORS + text[b:]

# ---- 4. the S457 export doors out; health_row rewritten -----------------------------------------------------------
EXPORT_START = '# ---------------------------------------------------------------------------------------------------------------------\n# S457 -- the exports, read back by the owner\'s PC'
READ_BEAT = '# ---------------------------------------------------------------------------------------------------------------------\ndef read_beat():'
a, b = text.index(EXPORT_START), text.index(READ_BEAT)
text = text[:a] + text[b:]
REPORTS_START = '# ---- S456: BOTH Docterz reports, by name'
a = text.index(REPORTS_START)
HEALTH = r'''# ---------------------------------------------------------------------------------------------------------------------
def health_row(add, setting, con, now_ts=None, now_ist=None):
    """One row for /finance/health, "Lab PC" -- NOT wired by kit S655 (finance_app.py is the parent's; one line there
    later). The age is measured on THIS server's clock from when the heartbeat ARRIVED. Red after 3 h while the lab is
    open (08:00-20:30 Mon-Sat, 08:00-14:00 Sun, IST); amber when the last snapshot is older than a day."""
    now_ts = now_ts or time.time()
    now_ist = now_ist or _ist_now()
    rec = read_beat()
    if rec is None:
        add("labpc", "Lab PC", "red", "no heartbeat has ever arrived from the lab PC", None)
        return
    age_h = (now_ts - int(rec.get("received_ts") or 0)) / 3600.0
    beat = rec["beat"]
    sn = beat.get("snapshot") or {}
    att = beat.get("attention") or []
    open_now = (8 <= now_ist.hour < (14 if now_ist.weekday() == 6 else 21))
    state = "green"
    words = ["heartbeat %.1f h ago" % age_h]
    if age_h > 3 and open_now:
        state = "red"
        words.append("the lab is open and the PC has been silent")
    elif age_h > 16:
        words.append("the PC is off (switched off evenings; that is the routine)")
    idx = _index_read()
    newest = max((v.get("received_ts") or 0 for v in idx.values()), default=0)
    if newest:
        snap_age = (now_ts - newest) / 3600.0
        words.append("last snapshot %.1f h ago (%d kept)" % (snap_age, len(idx)))
        if snap_age > 26 and state == "green":
            state = "amber"
    else:
        words.append("no snapshot kept yet")
        if state == "green":
            state = "amber"
    if att:
        words.append("; ".join(str(x) for x in att[:3]))
        if state == "green":
            state = "amber"
    add("labpc", "Lab PC", state, " | ".join(words), rec.get("received_ist"))
'''
text = text[:a] + HEALTH

for old, new, count in EDITS:
    n = text.count(old)
    if n != count:
        sys.stderr.write("ANCHOR occurs %d time(s), expected %d:\n%s\n" % (n, count, old[:200]))
        sys.exit(1)
    text = text.replace(old, new)
for word in ("reception", "docterz", "Docterz", "RECEPTION"):
    hits = [ln for ln in text.splitlines() if word in ln and not ln.lstrip().startswith("#")]
    hits = [h for h in hits if "reception_door.py" not in h and "reception_agent.py" not in h and "reception PC" not in h
            and "reception doors" not in h and "reception relay" not in h]
    if hits:
        sys.stderr.write("LEFT-OVER %r in a code line:\n  %s\n" % (word, "\n  ".join(hits[:10])))
        sys.exit(1)
io.open(DST, "w", encoding="utf-8", newline="").write(text)
print("lab_door.py written: %d bytes, md5 %s" % (len(text.encode("utf-8")), hashlib.md5(text.encode("utf-8")).hexdigest()))
