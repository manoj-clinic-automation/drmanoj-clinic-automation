#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s601.py -- the S601_PHARMACY_BILLS_READ_BY_CLAUDE walk (D747). The app with the given files on a COPY of a database (SQLite's
backup API) in its own scratch folder; made-up rows only (papers stamped W601-… with a made-up supplier, submitted 15-Jun-2031); made-up
logins (walk_own_2031 / walk_mgr_2031, made here; a scanning login stood in for by the walk); Flask's test client, no port. NEVER a real
API call, never the key: asset_register.CLAUDE is a stub (read_bill answers per control; read is OLD's thread target; everything else goes
to the real claude_reader on the copy), SARVAM is None or a counting stub, threading.Timer is a stub that QUEUES (delay, fn, args) and runs
nothing -- the walk drains the queue AFTER _bg_extract has returned (R1-B1). Every row the walk checks is found by its key, never by
counting a table. S585's walk is the shape.

    python3 -B walk_s601.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js, stationery.py, batteries.py, xray_costs.py> <assets.db to copy>
                            [--work DIR] [--shared DIR] [--dump FILE | --old-dump FILE] [--expect-red] [--keep]
    python3 -B walk_s601.py --state <dir> <assets.db to copy> [--work DIR] [--shared DIR] [--label before|after]

Checks: W1 (structural) the app imports from the scratch folder; W2 the S601 marks; G1 the grep proof on the files' text; C1-C11 one per
item of the brief's walk list (s4): C1 a pharmacy paper filled by Claude · C2 a pharmacy challan too · C3 Sarvam OFF by the setting ·
C4 the retry (R1-B1, R1-B2) · C5 the clinic lanes unchanged (the one difference the `filled` row) · C6 the exclusions unchanged (green on
both) · C7 the non-clobber rule · C8 the reread's to_fill and _run's SELECT · C9 bill_extract, the form's words, the re-read flash ·
C10 the admin page · C11 nothing else moved: the Sanjeevni listing, the staff pages byte-equal OLD vs NEW (--dump on OLD, --old-dump on
NEW; green on both), the link table never opened. (Item 12 -- the control -- is this walk with --expect-red on the OLD files.)
--expect-red: exit 0 only if every check in MUST_RED is RED (W1, C6, C11 structural: green on both)."""
import datetime, importlib.util, io, json, os, re, shutil, sqlite3, sys, tempfile, threading, time

try:
    import fcntl                                                           # noqa: F401 -- claude_reread's lock file (the box has it)
except ImportError:                                                        # the walk on a Windows PC: a stand-in that locks nothing
    import types
    sys.modules["fcntl"] = types.SimpleNamespace(flock=lambda *a, **k: None, LOCK_EX=2, LOCK_NB=4, LOCK_UN=8)

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) != HERE]   # never import from the kit's own folder
ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "G1", "C1", "C2", "C3", "C4", "C5", "C7", "C8", "C9", "C10")
GREEN_BOTH = ("W1", "C6", "C11")
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py", "batteries.py", "xray_costs.py")
VENDOR = "Made-Up Pharma Walk 2031"
CREATED = "2026-10-19 00:00:00"
HINDI = ("karo", "nahi", "chuno", "dikhao", "diya", "kitna", "kisko")


def opt(name, default=None):
    return ARGS[ARGS.index(name) + 1] if name in ARGS else default


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = ""
        if not ok and detail:
            try:
                d = detail()
            except Exception as e:                                         # noqa: BLE001
                d = repr(e)
    except Exception as e:                                                 # noqa: BLE001
        ok, d = False, repr(e)
    R.append(ok)
    NAMES.append(name.split(" ")[0])
    if not ok:
        FAILED.append(name.split(" ")[0])
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:1500]) if (d and not ok) else ""))
    return ok


def quiet(fn, default=None):
    try:
        return fn()
    except Exception as e:                                                 # noqa: BLE001
        print("  (step failed: %s)" % repr(e)[:240])
        return default


def setup_env(work):
    app = os.path.join(work, "app")
    return {"ASSETS_DB": os.path.join(work, "assets.db"), "ASSETS_UPLOADS": os.path.join(work, "uploads"),
            "SCANAPP_ANTHROPIC_KEY_FILE": os.path.join(work, "key", "anthropic.key"),
            "SCANAPP_ANTHROPIC_URL": "https://made-up.invalid/v1/messages",
            "CLINIC_PORTAL_DIR": os.path.join(work, "no_portal"), "FINANCE_LOCAL_URL": "http://127.0.0.1:9",
            "SHARED_LIB_DIR": os.path.join(work, "shared"), "FINANCE_DB_FOR_SCANS": os.path.join(work, "no_finance.db"),
            "SCANNER_OPENCV_JS": os.path.join(app, "static", "opencv.js")}


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def under(p, d):
    return bool(p) and os.path.realpath(p).startswith(os.path.realpath(d) + os.sep)


def copy_db(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True); d = sqlite3.connect(dst); s.backup(d); s.close(); d.close()


def tiny_pdf(tag):
    body = ("%PDF-1.1\n%% " + tag + "\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 300]>>endobj\ntrailer<</Size 4/Root 1 0 R>>\n%%EOF\n")
    return body.encode()


def prepare(D, SRC, shared_src, work):
    for sub in ("app", "uploads", "key", "no_portal", "shared"):
        os.makedirs(os.path.join(work, sub), exist_ok=True)
    for f in MODS:
        if os.path.exists(os.path.join(D, f)):
            shutil.copy(os.path.join(D, f), os.path.join(work, "app", f))
    if shared_src and os.path.isdir(shared_src):
        for f in os.listdir(shared_src):
            if f.endswith(".py"):
                shutil.copy(os.path.join(shared_src, f), os.path.join(work, "shared", f))
    with open(os.path.join(work, "key", "anthropic.key"), "w") as fh:
        fh.write("sk-ant-walk-made-up-" + "0" * 12 + "\n")                     # a made-up key file: key_present() answers True
    dbp = os.path.join(work, "assets.db")
    copy_db(SRC, dbp)
    os.environ.update(setup_env(work))
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)
    appdir = os.path.join(work, "app")
    if appdir not in sys.path:
        sys.path.insert(0, appdir)
    return dbp, appdir


def users_and_settings(db):
    for k in ("desk.on", "machine.on", "desk.floor", "read.sarvam", "read.claude_daily_cap"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','on')")        # S601's walk: Claude ON (S585's sets off)
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()


def freeze(*mods):
    for x in mods:
        if x is not None:
            x.TODAY = TODAY


def client_for(m, db, un):
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    u = db.execute("SELECT * FROM users WHERE username=?", (un,)).fetchone()
    cl = m.app.test_client()
    with cl.session_transaction() as ss:
        ss["uid"] = u["id"]; ss["epoch"] = epoch
    return cl


# ---------------------------------------------------------------------------------------------- the stubs
class ClaudeStub:
    """Stands in for asset_register.CLAUDE. read_bill answers per the control from a queue: ("fill", hdr, items) records an ok=1 reading
    and returns (hdr, items); ("none",) records a failure (no ok=1 row) and returns None; ("empty",) records an ok=1 reading of nothing and
    returns None (a paper read as empty). read (OLD's beside-thread target) records a canned ok=1 reading and consumes no answer.
    available / state / ensure / key_present / readings_today / calls_today / cap / setting / to_bill / DAILY_CAP / MODELS go to the real
    claude_reader on the copy. Never a call, never the key."""
    def __init__(self, real, dbp):
        self.real, self.dbp, self.answers, self.calls = real, dbp, [], []
        self.VERSION, self.DAILY_CAP, self.MODELS, self.PROMPT = real.VERSION, real.DAILY_CAP, real.MODELS, real.PROMPT
        self.default = ("fill", dict(HDR), [dict(x) for x in ITEMS])

    def available(self, db_path=None):
        return self.real.available(db_path or self.dbp)

    def state(self, con):
        return self.real.state(con)

    def ensure(self, con):
        return self.real.ensure(con)

    def key_present(self):
        return self.real.key_present()

    def readings_today(self, con):
        return self.real.readings_today(con)

    def calls_today(self, con):
        return self.real.calls_today(con)

    def cap(self, con):
        return self.real.cap(con)

    def setting(self, con, key, default=None):
        return self.real.setting(con, key, default)

    def set_setting(self, con, key, value):
        return self.real.set_setting(con, key, value)

    def to_bill(self, data):
        return self.real.to_bill(data)

    def set(self, *answers):
        self.answers = list(answers); self.calls = []

    def _record(self, bid, ok, data, err):
        con = self.real._db(self.dbp)
        try:
            self.real.ensure(con)
            self.real._record(con, bid, "walk-model" if ok else None, ok, (data or {}).get("doc_kind"), data, err)
        finally:
            con.close()

    def read(self, path, bid=None, db_path=None):
        self.calls.append((bid, "read"))
        data = dict(READING)
        self._record(bid, True, data, None)
        return data

    def read_bill(self, path, bid=None, db_path=None):
        self.calls.append((bid, "read_bill"))
        if not self.real.available(db_path or self.dbp):
            return None
        a = self.answers.pop(0) if self.answers else self.default
        if a[0] == "fill":
            self._record(bid, True, dict(READING, vendor=a[1].get("vendor"), bill_no=a[1].get("bill_no")), None)
            return a[1], a[2]
        if a[0] == "empty":
            self._record(bid, True, {"doc_kind": "other", "vendor": None, "bill_no": None, "bill_date": None, "total_amount": None, "items": []}, None)
            return None
        self._record(bid, False, None, "walk: could not read")
        return None


class SarvamStub:
    def __init__(self):
        self.calls = 0

    def available(self):
        return True

    def extract(self, path, schema=None):
        self.calls += 1
        return {"vendor": "Made-Up Sarvam Vendor 2031", "bill_no": "SV-2031-%d" % self.calls, "total_amount": "77", "items": []}, "done"


class FakeTimer:
    def __init__(self, delay, fn, args=(), kwargs=None):
        self.delay, self.fn, self.args, self.kwargs, self.daemon, self.started = delay, fn, tuple(args), dict(kwargs or {}), False, False

    def start(self):
        self.started = True

    def cancel(self):
        pass


class TimerQueue:
    """threading.Timer's stand-in: queues, runs nothing. drain() runs the first queued callback AFTER the caller has returned."""
    def __init__(self):
        self.q = []

    def __call__(self, delay, fn, args=(), kwargs=None):
        t = FakeTimer(delay, fn, args, kwargs)
        self.q.append(t)
        return t

    def take(self):
        return self.q.pop(0) if self.q else None

    def drain_one(self):
        t = self.take()
        if t is None:
            return None
        return t.fn(*t.args, **t.kwargs), t


HDR = {"vendor": VENDOR, "vendor_phone": None, "vendor_email": None, "bill_no": "W601-1", "bill_date": "12-10-2026", "total_amount": 1250.0}
ITEMS = [{"name": "Walk Tab 2031", "qty": 10, "pack": "strip", "rate": 100, "amount": 1000, "make": None, "model": None, "serial": None,
          "batch": "WB-1", "expiry": "2031-12-31", "hsn": None},
         {"name": "Walk Syrup 2031", "qty": 5, "pack": "bottle", "rate": 50, "amount": 250, "make": None, "model": None, "serial": None,
          "batch": None, "expiry": None, "hsn": None}]
READING = {"doc_kind": "tax_invoice", "vendor": VENDOR, "vendor_phone": None, "vendor_email": None, "bill_no": "W601-1", "bill_date": "2026-10-12",
           "date_as_read": "12/10/26", "total_amount": 1250.0, "made_out_to": "clinic", "handwritten": False,
           "items": [{"name": "Walk Tab 2031", "qty": 10.0, "unit": "strip", "rate": 100.0, "amount": 1000.0, "make": None, "model": None,
                      "serial": None, "batch": "WB-1", "expiry": "2031-12-31", "hsn": None}]}


def fill(no, total=1250.0, items=None):
    return ("fill", dict(HDR, bill_no=no, total_amount=total), [dict(x) for x in (ITEMS if items is None else items)])


# ---------------------------------------------------------------------------------------------- --state
def state_mode():
    """--state <dir> <db>: the install-day state as these files read a fresh copy -- the settings read.*, the pharmacy papers by
    ocr_status, the admin page's two cards as the owner (the test client, a walk-only login), the last 5 bill_audit rows (action only)."""
    i = ARGS.index("--state")
    D, SRC = os.path.abspath(ARGS[i + 1]), os.path.abspath(ARGS[i + 2])
    label = opt("--label", "state")
    work = os.path.abspath(opt("--work") or tempfile.mkdtemp(prefix="s601state_", dir="/tmp" if os.path.isdir("/tmp") else None))
    try:
        dbp, appdir = prepare(D, SRC, opt("--shared", "/root/shared"), work)
        db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
        print("STATE %s: settings read.*: %s" % (label, ", ".join("%s=%s" % (r[0], r[1]) for r in db.execute(
            "SELECT key, value FROM settings WHERE key LIKE 'read.%' AND key NOT LIKE 'read.calls.%' ORDER BY key"))))
        print("STATE %s: pharmacy papers by ocr_status: %s" % (label, ", ".join("%s=%d" % (r[0] or "<none>", r[1]) for r in db.execute(
            "SELECT ocr_status, COUNT(*) FROM bills WHERE COALESCE(lane,'')='pharmacy' OR kind='Pharmacy' GROUP BY 1 ORDER BY 1"))))
        print("STATE %s: pharmacy papers with a good Claude reading: %d" % (label, db.execute(
            "SELECT COUNT(*) FROM bills b JOIN claude_reading r ON r.bill_id=b.id AND r.ok=1 WHERE COALESCE(b.lane,'')='pharmacy' OR b.kind='Pharmacy'").fetchone()[0]))
        print("STATE %s: last 5 bill_audit rows (id, paper, action): %s" % (label, ", ".join("%d/%d/%s" % (r[0], r[1], r[2]) for r in db.execute(
            "SELECT id, bill_id, action FROM bill_audit ORDER BY id DESC LIMIT 5"))))
        print("STATE %s: bill_audit rows by action filled / read_retry: %s" % (label, ", ".join("%s=%d" % (r[0], r[1]) for r in db.execute(
            "SELECT action, COUNT(*) FROM bill_audit WHERE action IN ('filled','read_retry') GROUP BY 1"))))
        if not db.execute("SELECT 1 FROM users WHERE username='walk_own_2031'").fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES('walk_own_2031','Walk Owner','owner','x',1)")
        db.commit()
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
        m.SARVAM_API_KEY = "walk-made-up"                        # the card's key line, as the live service has one (never the value)
        own = client_for(m, db, "walk_own_2031")
        t = own.get("/admin").get_data(as_text=True)
        cards = []
        for cid, nm in (("claude-reads", "Claude"), ("sarvam-reads", "Sarvam")):
            sec = t.split("id=%s" % cid, 1)[1].split("</div>", 1)[0] if ("id=%s" % cid) in t else ""
            now = re.findall(r"Now: <b>([^<]*)</b>", sec)
            fig = re.findall(r"read today (\d+) \(limit (\d+)\) · read so far (\d+)(?: · could not read (\d+))?", sec)
            cards.append("%s: %s%s" % (nm, (now[0] if now else "no card"), (" · today %s limit %s · read so far %s · could not read %s" % fig[0]) if fig else ""))
        print("STATE %s: the admin page as the owner -- %s; 'Sarvam key configured' line %s" % (label, "; ".join(cards), "present" if "Sarvam key configured" in t else "absent"))
        print("STATE OK S601 %s" % label)
        db.close()
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


# ---------------------------------------------------------------------------------------------- the walk
def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S601_SHARED_DIR", "/root/shared"))
    work = os.path.abspath(opt("--work") or tempfile.mkdtemp(prefix="s601walk_", dir="/tmp" if os.path.isdir("/tmp") else None))
    try:
        run(D, SRC, shared_src, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, work):
    dbp, appdir = prepare(D, SRC, shared_src, work)
    up = os.path.join(work, "uploads")
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    users_and_settings(db)
    db.close()
    try:
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    cp, sd, am = sys.modules.get("clinic_papers"), sys.modules.get("sorting_desk"), sys.modules.get("asset_machine")
    st, bt, xc = sys.modules.get("stationery"), sys.modules.get("batteries"), sys.modules.get("xray_costs")
    CR = m.CLAUDE
    ck("W1 (structural) the app imports; asset_register, clinic_papers, sorting_desk, asset_machine, stationery, batteries and the Claude "
       "reader come from the scratch folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and st is not None and under(st.__file__, appdir) and bt is not None
       and under(bt.__file__, appdir) and CR is not None and under(CR.__file__, appdir) and m.DB_PATH == dbp)
    try:
        RR = import_file("claude_reread", os.path.join(appdir, "claude_reread.py"))
    except Exception as e:                                                 # noqa: BLE001
        RR = None
        print("  (claude_reread could not be imported: %s)" % repr(e)[:200])
    ck("W2 the S601 marks: _S601_TRIES (a dict), _S601_DELAYS (10, 30, 90), _s601_asked, _sarvam_setting, _s601_retry and "
       "_s601_sarvam_card defined in asset_register; claude_reread.to_fill no longer names the pharmacy lane; the earlier marks kept "
       "(APP_VERSION 1.14.0, STOCK_S568, BATTERY_S571)",
       lambda: isinstance(getattr(m, "_S601_TRIES", None), dict) and getattr(m, "_S601_DELAYS", None) == (10, 30, 90)
       and all(callable(getattr(m, f, None)) for f in ("_s601_asked", "_sarvam_setting", "_s601_retry", "_s601_sarvam_card"))
       and RR is not None and '"pharmacy", "other_doc"' not in open(os.path.join(appdir, "claude_reread.py"), encoding="utf-8").read()
       and m.APP_VERSION == "1.14.0" and getattr(m, "STOCK_S568", None) == "S568" and getattr(m, "BATTERY_S571", None) == "S571",
       lambda: dict(tries=getattr(m, "_S601_TRIES", None), delays=getattr(m, "_S601_DELAYS", None), rr=RR is not None))
    freeze(sd, am, st, bt, xc)

    # ================================================================== G1 the grep proof (the brief s3.3), on the files' text
    ar_t = open(os.path.join(appdir, "asset_register.py"), encoding="utf-8").read()
    rr_t = open(os.path.join(appdir, "claude_reread.py"), encoding="utf-8").read()
    counts = {"beside thread": ar_t.count("threading.Thread(target=CLAUDE.read"), "def _sarvam_setting": ar_t.count("def _sarvam_setting"),
              "read.sarvam": ar_t.count("read.sarvam"), '"filled"': ar_t.count('"filled"'), '"read_retry"': ar_t.count('"read_retry"'),
              "_S601_TRIES =": ar_t.count("_S601_TRIES = "), "def _s601_asked": ar_t.count("def _s601_asked"),
              "_s601_asked( uses": ar_t.count("_s601_asked(") - ar_t.count("def _s601_asked("),
              "Sarvam key configured": ar_t.count("Sarvam key configured"), "ocr_key": ar_t.count("ocr_key"),
              "reread pharmacy exclusion": rr_t.count('"pharmacy", "other_doc"'), "ten-digit run": len(re.findall(r"(?<![0-9])[6-9][0-9]{9}(?![0-9])", ar_t + rr_t))}
    want = {"beside thread": 0, "def _sarvam_setting": 1, "read.sarvam": 2, '"filled"': 1, '"read_retry"': 1, "_S601_TRIES =": 1, "def _s601_asked": 1,
            "_s601_asked( uses": 2, "Sarvam key configured": 0, "ocr_key": 0, "reread pharmacy exclusion": 0, "ten-digit run": 0}
    print("G1 counts: %s" % counts)
    ck("G1 the grep proof: no beside-thread read; _sarvam_setting defined once; the setting named twice in asset_register (one read in "
       "_sarvam_setting, one write in set_read_sarvam); the `filled` and `read_retry` audit actions once each; _S601_TRIES defined once; "
       "_s601_asked defined once and used twice (_s550_claude's lane test, the retry); 'Sarvam key configured' and ocr_key gone; "
       "claude_reread's pharmacy exclusion gone; no ten-digit run",
       lambda: counts == want, lambda: {k: (counts[k], want[k]) for k in want if counts[k] != want[k]})

    # ================================================================== the stubs, the logins, the made-up rows
    stub = ClaudeStub(CR, dbp)
    m.CLAUDE = stub
    sarvam = SarvamStub()
    m.SARVAM = None
    m.SARVAM_API_KEY = "walk-made-up"
    tq = TimerQueue()
    real_timer = threading.Timer
    threading.Timer = tq
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    CR.ensure(db); db.commit()
    own, mgr = client_for(m, db, "walk_own_2031"), client_for(m, db, "walk_mgr_2031")
    rcp_u = {"id": None, "username": "walk_rcp_2031", "display_name": "Walk Reception", "role": "reception", "active": 1}
    orig_cu = m.current_user
    seq = {"n": 0}

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    def as_reception(fn):
        m.current_user = lambda: rcp_u
        try:
            return fn(m.app.test_client())
        finally:
            m.current_user = orig_cu

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    def scan(tag):
        fn = "w601_%s.pdf" % tag
        with open(os.path.join(up, fn), "wb") as fh:
            fh.write(tiny_pdf(tag))
        return fn

    def paper(tag, lane="pharmacy", kind="Pharmacy", status="captured", vendor=None, bill_no=None, total=None, sg=None, doc_kind=None,
              challan_state=None, by="Walk Reception"):
        seq["n"] += 1
        at = "2031-06-%02d 10:00" % seq["n"]                              # a day apart: S441's page-join never pairs two walk papers
        cur = db.execute("INSERT INTO bills(kind, vendor, bill_no, total_amount, stamp_no, status, lane, submitted_by, submitted_at, created_at, "
                         "source_stored, source_orig, subgroup, doc_kind, challan_state, ocr_status) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,'reading')",
                         (kind, vendor, bill_no, total, "W601-%02d" % seq["n"], status, lane, by, at, CREATED, scan(tag), "w601_%s.pdf" % tag,
                          sg, doc_kind, challan_state))
        db.commit()
        return cur.lastrowid, os.path.join(up, "w601_%s.pdf" % tag)

    def row(bid):
        r = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        return dict(r) if r else None

    def items_n(bid):
        return db.execute("SELECT COUNT(*) FROM bill_items WHERE bill_id=?", (bid,)).fetchone()[0]

    def audits(bid, action=None):
        q = "SELECT action, detail FROM bill_audit WHERE bill_id=?" + (" AND action=?" if action else "") + " ORDER BY id"
        return [(r[0], quiet(lambda: json.loads(r[1] or "{}"), r[1])) for r in db.execute(q, (bid, action) if action else (bid,))]

    def ok_rows(bid):
        return db.execute("SELECT ok FROM claude_reading WHERE bill_id=?", (bid,)).fetchall()

    def tries():
        return dict(getattr(m, "_S601_TRIES", {}) or {})

    def reset_tries():
        t = getattr(m, "_S601_TRIES", None)
        if isinstance(t, dict):
            t.clear()
        tq.q[:] = []

    def section(page, start, end):
        i_ = page.find(start)
        if i_ < 0:
            return ""
        j_ = page.find(end, i_ + len(start))
        return page[i_:j_ if j_ > 0 else len(page)]

    def sanj_listing():
        """The Sanjeevni register's own query on the copy (scan_register.asset_scans: kind='Pharmacy' AND status='captured'), read only."""
        return sorted(r[0] for r in db.execute("SELECT id FROM bills WHERE kind='Pharmacy' AND status='captured' ORDER BY id"))

    sanj_before = sanj_listing()
    # the dump papers: a pharmacy paper already typed (the staff pages are rendered on it, OLD and NEW -- byte-equal)
    PD, _ = paper("pd", vendor="Made-Up Typed Pharma 2031", bill_no="W601-PD", total=990.0)
    db.execute("UPDATE bills SET ocr_status='read' WHERE id=?", (PD,)); db.commit()
    dump = {}
    for who, cl in (("owner", own), ("manager", mgr)):
        for nm, url in (("desk", "/desk"), ("bills", "/bills"), ("paper", "/bills/%d" % PD)):
            r_ = cl.get(url)
            dump["%s %s" % (who, nm)] = [r_.status_code, r_.get_data(as_text=True)]
    for nm, url in (("desk", "/desk"), ("bills", "/bills"), ("paper", "/bills/%d" % PD)):
        r_ = as_reception(lambda c, u=url: c.get(u))
        dump["reception %s" % nm] = [r_.status_code, r_.get_data(as_text=True)]
    dump_path = opt("--dump")
    old_dump = opt("--old-dump")

    try:
        # ================================================================== C1 a pharmacy paper is filled by Claude
        P1, p1 = paper("p1")
        stub.set(fill("W601-C1")); reset_tries()
        st1 = m._bg_extract(P1, p1)
        for _ in range(50):                                                # OLD: the beside thread may still be recording
            if stub.calls and stub.calls[-1][1] == "read" and ok_rows(P1):
                break
            time.sleep(0.1)
        r1 = row(P1)
        its1 = [dict(x) for x in db.execute("SELECT item_name, quantity, pack_size, rate, amount, batch, expiry FROM bill_items WHERE bill_id=? ORDER BY id", (P1,))]
        f1 = audits(P1, "filled")
        print("C1 counts: _bg_extract -> %r; the stub's calls %s; vendor %r bill_no %r date %r total %r; items %d; ocr_status %r; `filled` rows %s; "
              "audit actions %s; dup_flag %r; queued %d" % (st1, stub.calls, r1["vendor"], r1["bill_no"], r1["bill_date"], r1["total_amount"],
                                                              len(its1), r1["ocr_status"], f1, [a for a, _d in audits(P1)], r1["dup_flag"], len(tq.q)))
        ck("C1 a pharmacy paper (lane pharmacy, kind Pharmacy, empty header) through _bg_extract with the Claude stub answering a header "
           "(date 12-10-2026 -> stored 2026-10-12 through _norm_date) and two items: vendor, bill_no, bill_date, total and 2 bill_items "
           "written, ocr_status 'read', ONE bill_audit row filled {by: claude, items: 2}; _dup_after_ocr and S441's pass ran on the filled "
           "data (no exception, no dup mark on a fresh paper); the stub asked through read_bill, not a beside thread",
           lambda: st1 == "read" and r1["vendor"] == VENDOR and r1["bill_no"] == "W601-C1" and r1["bill_date"] == "2026-10-12"
           and r1["total_amount"] == 1250.0 and len(its1) == 2 and its1[0]["item_name"] == "Walk Tab 2031" and its1[0]["quantity"] == 10
           and its1[0]["pack_size"] == "strip" and its1[0]["expiry"] == "2031-12-31" and r1["ocr_status"] == "read"
           and f1 == [("filled", {"by": "claude", "items": 2})] and not r1["dup_flag"] and r1["status"] == "captured"
           and stub.calls == [(P1, "read_bill")] and ok_rows(P1) and ok_rows(P1)[0][0] == 1 and not tq.q,
           lambda: dict(st=st1, row={k: r1[k] for k in ("vendor", "bill_no", "bill_date", "total_amount", "ocr_status", "dup_flag", "status")},
                        items=its1, filled=f1, calls=stub.calls, ok=[tuple(x) for x in ok_rows(P1)], queued=len(tq.q)))

        # ================================================================== C2 a pharmacy challan too
        P2, p2 = paper("p2", kind="Challan", doc_kind="challan", challan_state="awaiting")
        in_before = P2 in sanj_listing()
        stub.set(fill("W601-C2", total=None)); reset_tries()
        st2 = m._bg_extract(P2, p2)
        for _ in range(50):
            if stub.calls and stub.calls[-1][1] == "read" and ok_rows(P2):
                break
            time.sleep(0.1)
        r2 = row(P2)
        in_after = P2 in sanj_listing()
        f2 = audits(P2, "filled")
        print("C2 counts: -> %r; vendor %r; kind %r doc_kind %r challan_state %r; items %d; `filled` %s; in the Sanjeevni listing before %s after %s"
              % (st2, r2["vendor"], r2["kind"], r2["doc_kind"], r2["challan_state"], items_n(P2), f2, in_before, in_after))
        ck("C2 a pharmacy challan (kind Challan, doc_kind challan, lane pharmacy) is filled the same way on NEW: vendor, number, date and "
           "the items written, the `filled` row; challan_state 'awaiting' before and after; kind stays Challan; the Sanjeevni register's "
           "asset_scans query (kind='Pharmacy' AND status='captured') does not list it before or after",
           lambda: st2 == "read" and r2["vendor"] == VENDOR and r2["bill_no"] == "W601-C2" and r2["bill_date"] == "2026-10-12"
           and items_n(P2) == 2 and r2["challan_state"] == "awaiting" and r2["kind"] == "Challan" and r2["doc_kind"] == "challan"
           and f2 == [("filled", {"by": "claude", "items": 2})] and not in_before and not in_after and stub.calls == [(P2, "read_bill")],
           lambda: dict(st=st2, row={k: r2[k] for k in ("vendor", "bill_no", "kind", "doc_kind", "challan_state")}, filled=f2, calls=stub.calls, sanj=(in_before, in_after)))

        # ================================================================== C3 Sarvam OFF by the setting
        m.SARVAM = sarvam
        setting("read.sarvam", "off")
        P3, p3 = paper("p3")
        stub.set(("none",)); sarvam.calls = 0; reset_tries()
        st3 = m._bg_extract(P3, p3)
        r3 = row(P3)
        c3a = (sarvam.calls, st3, r3["ocr_status"], r3["vendor"])
        setting("read.sarvam", None); setting("read.claude", "off")
        P3b, p3b = paper("p3b")
        stub.set(("none",)); sarvam.calls = 0; reset_tries()
        st3b = m._bg_extract(P3b, p3b)
        r3b = row(P3b)
        c3b = (sarvam.calls, st3b, r3b["ocr_status"], r3b["vendor"], audits(P3b, "filled"))
        setting("read.claude", "on")
        print("C3 counts: setting off + Claude cannot read: Sarvam calls %d, -> %r, ocr_status %r, vendor %r; setting absent + Claude off: Sarvam "
              "calls %d, -> %r, ocr_status %r, vendor %r, `filled` %s" % (c3a + c3b))
        ck("C3 Sarvam OFF by the setting: with read.sarvam = off and the Claude stub answering nothing (no claude_reading row with ok=1), "
           "the counting Sarvam stub is NEVER called (0) and the paper reads `failed`; with the setting absent and read.claude = off the "
           "Sarvam stub IS called (absent = today) and fills the paper (filled {by: sarvam})",
           lambda: c3a[0] == 0 and c3a[1] == "failed" and c3a[2] == "failed" and c3a[3] is None
           and c3b[0] == 1 and c3b[1] == "read" and c3b[3] == "Made-Up Sarvam Vendor 2031" and c3b[4] == [("filled", {"by": "sarvam", "items": 0})],
           lambda: dict(off=c3a, absent=c3b))
        setting("read.sarvam", "off")
        reset_tries()

        # ================================================================== C4 the retry (R1-B1, R1-B2)
        P4, p4 = paper("p4")
        stub.set(("none",), ("none",), fill("W601-C4")); reset_tries()
        s_a = m._bg_extract(P4, p4)
        st_a = row(P4)["ocr_status"]; q_a = [(t.delay, t.daemon, t.started, t.args) for t in tq.q]; aud_a = audits(P4, "read_retry")
        d1 = tq.drain_one()
        st_b = row(P4)["ocr_status"]; q_b = [(t.delay, t.daemon, t.started, t.args) for t in tq.q]; aud_b = audits(P4, "read_retry")
        d2 = tq.drain_one()
        r4 = row(P4)
        q_c = [t.delay for t in tq.q]; aud_c = audits(P4, "read_retry"); f4 = audits(P4, "filled")
        tr4 = tries().get(P4)
        print("C4 counts: first call -> %r, ocr_status %r, queued %s, read_retry %s; after the first drain -> %r, ocr_status %r, queued %s, read_retry %s; "
              "after the second drain -> %r, ocr_status %r, vendor %r, queued %s, `filled` %s, _S601_TRIES[bid] %s"
              % (s_a, st_a, q_a, aud_a, d1 and d1[0], st_b, q_b, aud_b, d2 and d2[0], r4["ocr_status"], r4["vendor"], q_c, f4, tr4))
        # always unreadable: exactly three retries (10, 30, 90), then failed and nothing queued on the fourth call
        P4b, p4b = paper("p4b")
        stub.set(("none",), ("none",), ("none",), ("none",), ("none",)); reset_tries()
        m._bg_extract(P4b, p4b)
        delays = []
        for _ in range(5):
            if not tq.q:
                break
            t = tq.take(); delays.append(t.delay)
            t.fn(*t.args, **t.kwargs)
        r4b = row(P4b); aud_4b = audits(P4b, "read_retry"); q_4b = len(tq.q); tr4b = tries().get(P4b); calls_4b = len(stub.calls)
        print("C4b counts: delays run %s, calls %d, read_retry %s, ocr_status %r, queued after the fourth call %d, _S601_TRIES[bid] %s"
              % (delays, calls_4b, aud_4b, r4b["ocr_status"], q_4b, tr4b))
        # read as empty: failed, NO retry
        P4c, p4c = paper("p4c")
        stub.set(("empty",)); reset_tries()
        s_c = m._bg_extract(P4c, p4c)
        c4c = (s_c, row(P4c)["ocr_status"], len(tq.q), audits(P4c, "read_retry"), [tuple(x) for x in ok_rows(P4c)], tries().get(P4c))
        # the reader stopped: failed at once, no retry, the stub not asked
        setting("read.claude", "stopped:the key was refused")
        P4d, p4d = paper("p4d")
        stub.set(("none",)); reset_tries()
        s_d = m._bg_extract(P4d, p4d)
        c4d = (s_d, row(P4d)["ocr_status"], len(tq.q), audits(P4d, "read_retry"), stub.calls, tries().get(P4d))
        setting("read.claude", "on")
        print("C4c counts (read as empty): %s; C4d counts (stopped): %s" % (c4c, c4d))
        ck("C4 the retry: the Claude stub answers nothing twice and a reading the third time -> after the first call ocr_status 'failed', ONE "
           "queued daemon Timer of 10 min (600 s) on _bg_extract(bid, path), one read_retry {try: 1, in_min: 10} row; the queue drained AFTER "
           "the call returned -> 'failed', a 30-min Timer, read_retry {try: 2}; drained again -> filled, 'read', the `filled` row, "
           "_S601_TRIES[bid] == 2. A stub that always answers nothing -> exactly 3 retries (10, 30, 90 min), then 'failed' and nothing "
           "queued on the fourth call. A paper read as EMPTY (an ok=1 reading of nothing) -> 'failed', NO retry, no read_retry row. "
           "read.claude = stopped:… -> 'failed' at once, no retry, the stub not asked",
           lambda: s_a == "failed" and st_a == "failed" and q_a == [(600, True, True, (P4, p4))] and aud_a == [("read_retry", {"try": 1, "in_min": 10})]
           and d1 and d1[0] == "failed" and st_b == "failed" and q_b == [(1800, True, True, (P4, p4))]
           and aud_b == [("read_retry", {"try": 1, "in_min": 10}), ("read_retry", {"try": 2, "in_min": 30})]
           and d2 and d2[0] == "read" and r4["ocr_status"] == "read" and r4["vendor"] == VENDOR and r4["bill_no"] == "W601-C4" and q_c == []
           and f4 == [("filled", {"by": "claude", "items": 2})] and tr4 == 2
           and delays == [600, 1800, 5400] and calls_4b == 4 and [a[1]["try"] for a in aud_4b] == [1, 2, 3] and r4b["ocr_status"] == "failed"
           and q_4b == 0 and tr4b == 3
           and c4c[0] == "failed" and c4c[1] == "failed" and c4c[2] == 0 and c4c[3] == [] and c4c[4] == [(1,)] and c4c[5] is None
           and c4d[0] == "failed" and c4d[1] == "failed" and c4d[2] == 0 and c4d[3] == [] and c4d[4] == [] and c4d[5] is None,
           lambda: dict(first=(s_a, st_a, q_a, aud_a), second=(d1 and d1[0], st_b, q_b, aud_b), third=(d2 and d2[0], r4["ocr_status"], r4["vendor"], q_c, f4, tr4),
                        always=(delays, calls_4b, aud_4b, r4b["ocr_status"], q_4b, tr4b), empty=c4c, stopped=c4d))
        reset_tries()

        # ================================================================== C5 the clinic lanes unchanged (OLD vs NEW through the dump)
        c5 = {}
        for tag, lane, kind, status, total in (("c5a", "clinic", "Consumable", "draft", 333.0), ("c5b", "owner_expense", "Expense", "captured", 444.0)):
            P5, p5 = paper(tag, lane=lane, kind=kind, status=status, by="Walk Owner")
            stub.set(fill("W601-" + tag.upper(), total=total)); reset_tries()
            s5 = m._bg_extract(P5, p5)
            r5 = row(P5)
            its5 = [dict(x) for x in db.execute("SELECT item_name, quantity, pack_size, rate, amount FROM bill_items WHERE bill_id=? ORDER BY id", (P5,))]
            c5[tag] = {"st": s5, "hdr": [r5["vendor"], r5["bill_no"], r5["bill_date"], r5["total_amount"], r5["ocr_status"], r5["lane"], r5["kind"], r5["status"]],
                       "items": its5, "audit": [[a, d] for a, d in audits(P5) if a != "filled"], "filled": [[a, d] for a, d in audits(P5, "filled")],
                       "calls": [c[1] for c in stub.calls]}
        dump["C5"] = c5
        old5 = (json.load(open(old_dump, encoding="utf-8")).get("C5") if old_dump and os.path.exists(old_dump) else None)
        same5 = (old5 is not None and all(c5[t]["hdr"] == old5[t]["hdr"] and c5[t]["items"] == old5[t]["items"] and c5[t]["audit"] == old5[t]["audit"]
                                          and c5[t]["st"] == old5[t]["st"] for t in c5))
        print("C5 counts: %s; OLD's results given %s, equal on header / items / audit (filled apart) %s"
              % ({t: (c5[t]["st"], c5[t]["hdr"][:4], len(c5[t]["items"]), [a for a, _d in c5[t]["audit"]], c5[t]["filled"]) for t in c5}, old5 is not None, same5))
        ck("C5 the clinic lanes unchanged: a clinic-lane paper (draft) and an owner-expense paper through _bg_extract -> filled from the "
           "stub (header, 2 items, 'read'), the audit rows compared by (action, detail) equal to the OLD files' (--old-dump; on the OLD "
           "run the results are written with --dump), the ONE difference the new `filled {by: claude, items: 2}` row -- exactly one per paper",
           lambda: all(c5[t]["st"] == "read" and c5[t]["hdr"][:4] == [VENDOR, "W601-" + t.upper(), "2026-10-12", 333.0 if t == "c5a" else 444.0] and len(c5[t]["items"]) == 2
                       and c5[t]["filled"] == [["filled", {"by": "claude", "items": 2}]] and c5[t]["calls"] == ["read_bill"] for t in c5)
           and (same5 if old_dump else True),
           lambda: dict(c5=c5, old5=old5, same5=same5))

        # ================================================================== C6 the exclusions unchanged (green on both)
        m.SARVAM = None                                                    # no Sarvam at all: the same on OLD and NEW (the setting is NEW's)
        c6 = {}
        for tag, lane, kind, sg in (("c6a", "other_doc", "Document", None), ("c6b", "clinic", "Consumable", "personal"),
                                    ("c6c", "clinic", "Consumable", "resume"), ("c6d", "clinic", "Consumable", "patient_paper")):
            P6, p6 = paper(tag, lane=lane, kind=kind, status="captured", sg=sg, by="Walk Owner")
            stub.set(fill("W601-" + tag.upper())); reset_tries()
            s6 = m._bg_extract(P6, p6)
            c6[tag] = (s6, stub.calls, row(P6)["vendor"], len(tq.q), audits(P6, "read_retry"), tries().get(P6))
        print("C6 counts: %s" % c6)
        ck("C6 the exclusions unchanged: other_doc, personal, resume and patient_paper papers (no Sarvam module) -> the Claude stub never "
           "called (as OLD), nothing written, `failed`, and (R1-B2) zero read_retry rows and nothing queued",
           lambda: all(v[0] == "failed" and v[1] == [] and v[2] is None and v[3] == 0 and v[4] == [] and v[5] is None for v in c6.values()),
           lambda: c6)

        # ================================================================== C7 the non-clobber rule
        P7, p7 = paper("p7", vendor="Typed By Reception 2031", bill_no="W601-TYPED", total=500.0)
        db.execute("INSERT INTO bill_items(bill_id, item_name, quantity) VALUES(?, 'Typed Item 2031', 1)", (P7,)); db.commit()
        stub.set(fill("W601-C7")); reset_tries()
        s7 = m._bg_extract(P7, p7)
        r7 = row(P7)
        f7 = audits(P7, "filled")
        print("C7 counts: -> %r; vendor %r bill_no %r total %r date %r; items %d; `filled` %s" % (s7, r7["vendor"], r7["bill_no"], r7["total_amount"], r7["bill_date"], items_n(P7), f7))
        ck("C7 the non-clobber rule: a pharmacy paper whose vendor, number and total are typed and one item present -> nothing overwritten "
           "(the empty date is filled), bill_items count unchanged (1), ocr_status 'read'; the `filled` row still written with items = what "
           "the reader gave (2) -- it records the fill attempt's reader",
           lambda: s7 == "read" and r7["vendor"] == "Typed By Reception 2031" and r7["bill_no"] == "W601-TYPED" and r7["total_amount"] == 500.0
           and r7["bill_date"] == "2026-10-12" and items_n(P7) == 1 and f7 == [("filled", {"by": "claude", "items": 2})] and r7["ocr_status"] == "read",
           lambda: dict(st=s7, row={k: r7[k] for k in ("vendor", "bill_no", "total_amount", "bill_date", "ocr_status")}, items=items_n(P7), filled=f7))

        # ================================================================== C8 the reread run
        P8a, _ = paper("p8a")
        P8b, _ = paper("p8b", status="approved")
        P8c, _ = paper("p8c", lane="other_doc", kind="Document")
        P8d, _ = paper("p8d", lane="clinic", kind="Consumable", status="draft")
        tf = {k: (RR.to_fill(RR.row(db, bid)) if RR else None) for k, bid in (("pharmacy captured empty", P8a), ("pharmacy approved", P8b), ("other_doc", P8c), ("clinic draft", P8d))}
        src8 = rr_t[rr_t.index('rows = con.execute(') + len('rows = con.execute('):]
        sql8 = "\n".join(l_.strip() for l_ in re.search(r'^(.*?)\)\.fetchall\(\)', src8, re.S).group(1).splitlines())
        sel = sorted(r[0] for r in db.execute(eval("(" + sql8 + ")", {"KIND_LANE_SQL": RR.KIND_LANE_SQL if RR else ""})))  # noqa: S307 -- the file's own SELECT text
        ok_pharm = sorted(r[0] for r in db.execute("SELECT b.id FROM bills b JOIN claude_reading r ON r.bill_id=b.id AND r.ok=1 WHERE COALESCE(b.lane,'')='pharmacy' OR b.kind='Pharmacy'"))
        overlap = sorted(set(sel) & set(ok_pharm))
        print("C8 counts: to_fill %s; _run's SELECT on the copy: %d papers, pharmacy papers with a good reading %d, selected among them %d"
              % (tf, len(sel), len(ok_pharm), len(overlap)))
        ck("C8 the reread: claude_reread.to_fill on a captured, empty pharmacy row -> True (OLD: False); on an approved pharmacy row -> False "
           "(the SELECT still reads it: the reading is kept aside); on other_doc -> False (never selected); a clinic draft -> True; _run's own "
           "SELECT (the file's text, run on the copy) selects NONE of the pharmacy papers that already have a good reading -- the 140 stored "
           "readings are applied by nothing (by design)",
           lambda: tf == {"pharmacy captured empty": True, "pharmacy approved": False, "other_doc": False, "clinic draft": True} and len(ok_pharm) >= 140
           and overlap == [] and P8a in sel and P8b in sel and P8c not in sel,
           lambda: dict(tf=tf, n=len(sel), ok=len(ok_pharm), overlap=overlap[:5], p8=(P8a in sel, P8b in sel, P8c in sel)))

        # ================================================================== C9 bill_extract (the checker's upload form), the words, the re-read flash
        def extract(cl, tag):
            return cl.post("/bills/extract", data={"bill": (io.BytesIO(tiny_pdf(tag)), "w601_%s.pdf" % tag)}, content_type="multipart/form-data")
        m.SARVAM = sarvam; setting("read.sarvam", None); setting("read.claude", "on")
        stub.set(fill("W601-C9")); sarvam.calls = 0
        r9a = extract(mgr, "x9a"); t9a = r9a.get_data(as_text=True)
        c9a = (r9a.status_code, 'value="%s"' % VENDOR in t9a, "Auto-filled from the scan" in t9a, sarvam.calls, [c[1] for c in stub.calls], [c[0] for c in stub.calls])
        setting("read.claude", "off"); stub.set(fill("W601-C9b")); sarvam.calls = 0
        r9b = extract(mgr, "x9b"); t9b = r9b.get_data(as_text=True)
        c9b = (r9b.status_code, 'value="Made-Up Sarvam Vendor 2031"' in t9b, "Auto-filled from the scan" in t9b, sarvam.calls, stub.calls)
        m.SARVAM = None; stub.set(fill("W601-C9c"))
        r9c = extract(mgr, "x9c"); t9c = r9c.get_data(as_text=True)
        c9c = (r9c.status_code, "No reader is on — enter the bill manually. The scan is attached." in t9c, "Scan attached:" in t9c, 'value="%s"' % VENDOR in t9c, stub.calls)
        new_off = html(mgr, "/bills/new")
        setting("read.claude", "on"); new_on = html(mgr, "/bills/new")
        c9d = ("No reader is on, so this attaches the scan and you fill the form." in new_off, "the scan is read and the form pre-filled for you to check" in new_on,
               "Sarvam reads it" in new_on, "Set SARVAM_API_KEY" in new_off)
        setting("read.claude", "off")
        r9e = mgr.post("/bills/%d/reread" % P7)
        with mgr.session_transaction() as ss:
            fl9 = [x[1] for x in (ss.get("_flashes") or [])]; ss.pop("_flashes", None)
        setting("read.claude", "on")
        print("C9 counts: Claude on %s; Claude off + Sarvam %s; both off %s; the form's words (off, on, old words) %s; the re-read with no reader: %s %s"
              % (c9a, c9b, c9c, c9d, r9e.status_code, fl9))
        ck("C9 bill_extract as a checker (the manager login, the walk-only session): with the Claude stub -> the form pre-filled from it "
           "('Auto-filled from the scan'), Sarvam not asked, nothing recorded (bid None); Claude off + the Sarvam stub -> Sarvam's; both "
           "off -> 'No reader is on -- enter the bill manually. The scan is attached.' and the scan attached; the form's words are "
           "reader-neutral; the Re-read button with no reader flashes the same line",
           lambda: c9a[0] == 200 and c9a[1] and c9a[2] and c9a[3] == 0 and c9a[4] == ["read_bill"] and c9a[5] == [None]
           and c9b[0] == 200 and c9b[1] and c9b[2] and c9b[3] == 1 and c9b[4] == []
           and c9c[0] == 200 and c9c[1] and c9c[2] and not c9c[3] and c9c[4] == []
           and c9d == (True, True, False, False) and r9e.status_code == 302 and fl9 == ["No reader is on — enter the bill manually. The scan is attached."],
           lambda: dict(a=c9a, b=c9b, c=c9c, d=c9d, e=(r9e.status_code, fl9)))

        # ================================================================== C10 the admin page
        m.SARVAM = sarvam; setting("read.sarvam", None); setting("read.claude", "on")
        with own.session_transaction() as ss:
            ss.pop("_flashes", None)
        t10 = html(own, "/admin")
        cc = section(t10, "id=claude-reads", "</div>"); sc = section(t10, "id=sarvam-reads", "</div>")
        before = (re.findall(r"Now: <b>([^<]*)</b>", sc), "Switch OFF" in sc, "set_read_sarvam" in sc, "Reading the scans — Sarvam" in sc,
                  "Kept as the fall-back reader, switched by you. When OFF, only Claude reads." in sc)
        ctext = ("tried again three times over two hours" in cc, "the pharmacy's papers too" in cc, "Pharmacy papers are read and kept aside" in cc,
                 "Sarvam carries on" in cc, re.findall(r"Now: <b>([^<]*)</b>", cc))
        p10 = own.post("/admin", data={"action": "set_read_sarvam", "on": "0"})
        with own.session_transaction() as ss:
            fl10 = [x[1] for x in (ss.get("_flashes") or [])]; ss.pop("_flashes", None)
        v10 = db.execute("SELECT value FROM settings WHERE key='read.sarvam'").fetchone()
        t10b = html(own, "/admin"); sc2 = section(t10b, "id=sarvam-reads", "</div>")
        after = (re.findall(r"Now: <b>([^<]*)</b>", sc2), "Switch ON" in sc2)
        own.post("/admin", data={"action": "set_read_claude", "on": "0"})
        v10c = db.execute("SELECT value FROM settings WHERE key='read.claude'").fetchone()
        cc2 = section(html(own, "/admin"), "id=claude-reads", "</div>")
        own.post("/admin", data={"action": "set_read_claude", "on": "1"})
        with own.session_transaction() as ss:
            ss.pop("_flashes", None)
        hindi = [w for w in HINDI if w in (cc + sc + sc2).lower()]
        keyline = "Sarvam key configured" in t10 or "ocr_key" in t10
        saved_claude = m.CLAUDE; m.CLAUDE = None
        t10n = html(own, "/admin"); m.CLAUDE = saved_claude
        no_claude = ("id=sarvam-reads" in t10n, "id=claude-reads" in t10n)
        m.SARVAM_API_KEY = ""
        sc3 = section(html(own, "/admin"), "id=sarvam-reads", "</div>")
        m.SARVAM_API_KEY = "walk-made-up"
        nokey = (re.findall(r"Now: <b>([^<]*)</b>", sc3), "set_read_sarvam" in sc3)
        print("C10 counts: Sarvam card before %s; the Claude card's words %s; the switch POST %s %s -> setting %s; after %s; set_read_claude -> %s, "
              "the Claude card %s; Hindi words %s; the old key line %s; CLAUDE=None -> (Sarvam card, Claude card) %s; no key -> %s"
              % (before, ctext, p10.status_code, fl10, v10 and v10[0], after, v10c and v10c[0], re.findall(r"Now: <b>([^<]*)</b>", cc2), hindi, keyline, no_claude, nokey))
        ck("C10 the admin page as the owner: the Claude card's new words (the retry, the pharmacy's papers; the old 'kept aside' and "
           "'Sarvam carries on' gone); the Sarvam card 'Reading the scans -- Sarvam' with Now: ON and Switch OFF before the setting; "
           "set_read_sarvam writes read.sarvam = off, flashes, and the card reads Now: OFF with Switch ON; set_read_claude unchanged; "
           "'Sarvam key configured' absent from the page; no Hindi on the two cards; with CLAUDE = None the Sarvam card still renders "
           "(its own variable); with no Sarvam key the card says 'no key on the server' and offers no switch",
           lambda: before == (["ON"], True, True, True, True) and ctext[:4] == (True, True, False, False) and ctext[4] == ["ON"]
           and p10.status_code == 302 and fl10 == ["Sarvam reading the scans is now OFF."] and v10 and v10[0] == "off"
           and after == (["OFF"], True) and v10c and v10c[0] == "off" and re.findall(r"Now: <b>([^<]*)</b>", cc2) == ["OFF"]
           and hindi == [] and not keyline and no_claude == (True, False) and nokey == (["no key on the server"], False),
           lambda: dict(before=before, ctext=ctext, post=(p10.status_code, fl10, v10 and v10[0]), after=after, claude=(v10c and v10c[0]), hindi=hindi,
                        keyline=keyline, no_claude=no_claude, nokey=nokey))
        setting("read.sarvam", None)

        # ================================================================== C11 nothing else moved
        sanj_after = sanj_listing()
        mine = sorted(r[0] for r in db.execute("SELECT id FROM bills WHERE stamp_no LIKE 'W601-%' AND kind='Pharmacy' AND status='captured'"))
        sanj_ok = (sanj_after == sorted(set(sanj_before) | set(mine)) and P2 not in sanj_after)
        link_words = [w for w in ("purchase_scan_link", "finance.db", "FINANCE_DB") if w in ar_t[ar_t.find("S601_PHARMACY_BILLS_READ_BY_CLAUDE begin"):]]
        pages_same, diffs = None, []
        if old_dump and os.path.exists(old_dump):
            od = json.load(open(old_dump, encoding="utf-8"))
            pages_same = True
            for k, v in dump.items():
                if k == "C5":
                    continue
                o = od.get(k)
                if not o or o[0] != v[0] or o[1] != v[1]:
                    pages_same = False
                    if o:
                        i_ = next((j for j in range(min(len(o[1]), len(v[1]))) if o[1][j] != v[1][j]), min(len(o[1]), len(v[1])))
                        diffs.append((k, o[0], v[0], o[1][max(0, i_ - 80):i_ + 80], v[1][max(0, i_ - 80):i_ + 80]))
                    else:
                        diffs.append((k, None, v[0]))
        codes = {k: v[0] for k, v in dump.items() if k != "C5"}
        print("C11 counts: the Sanjeevni listing before %d after %d (the walk's own pharmacy bills %d; the challan listed %s); link words in the S601 "
              "block %s; staff pages dumped %d (codes %s); OLD's dump given %s, byte-equal %s"
              % (len(sanj_before), len(sanj_after), len(mine), P2 in sanj_after, link_words, len(codes), codes, bool(old_dump), pages_same))
        ck("C11 nothing else moved: the Sanjeevni register's asset_scans query on the copy lists, after the walk, exactly what it listed "
           "before plus the walk's own pharmacy bills (never the challan); the S601 block opens no finance table (the link table is not "
           "touched); the sorting desk, the bills list and the typed pharmacy paper's page for the owner, a manager and a scanning login "
           "(the desk refuses that login) rendered BEFORE the controls -- byte-equal to the OLD files' (--old-dump; --dump on the OLD run)",
           lambda: sanj_ok and link_words == [] and codes["owner desk"] == 200 and codes["manager desk"] == 200 and codes["reception desk"] == 403
           and codes["owner paper"] == 200 and codes["reception paper"] == 200 and codes["reception bills"] == 200 and (pages_same if old_dump else True),
           lambda: dict(sanj=(len(sanj_before), len(sanj_after), len(mine), P2 in sanj_after), link=link_words, codes=codes, diffs=diffs[:3]))
    finally:
        threading.Timer = real_timer
        m.current_user = orig_cu
    if dump_path:
        with open(dump_path, "w", encoding="utf-8") as fh:
            json.dump(dump, fh)
        print("dump written: %s (%d pages, C5)" % (dump_path, len(dump) - 1))
    db.close()


if __name__ == "__main__":
    if "--state" in ARGS:
        try:
            state_mode(); sys.exit(0)
        except Exception as e:                                             # noqa: BLE001
            import traceback
            traceback.print_exc()
            print("STATE RED S601: %r" % (e,)); sys.exit(1)
    if len(ARGS) < 2:
        print(__doc__); sys.exit(2)
    try:
        main()
    except Exception as e:                                                 # noqa: BLE001
        import traceback
        traceback.print_exc()
        ck("the walk ran to its end", lambda: False, lambda: repr(e))
    reds = R.count(False)
    print("%d checks: %d GREEN, %d RED%s" % (len(R), R.count(True), reds, (" (" + ", ".join(FAILED) + ")") if FAILED else ""))
    if "--expect-red" in ARGS:
        seen_ = {}
        for ok_, nm_ in zip(R, NAMES):
            seen_[nm_] = ok_
        not_red = [k for k in MUST_RED if seen_.get(k) is not False]
        print("CONTROL must-be-red: %s -- %s" % (", ".join(MUST_RED), ("all RED" if not not_red else "NOT red: " + ", ".join(
            k + ("(green)" if seen_.get(k) else "(not reached)") for k in not_red))))
        print("CONTROL structural (green on both, named): %s" % ", ".join("%s %s" % (k, "GREEN" if seen_.get(k) else "RED") for k in GREEN_BOTH))
        sys.exit(0 if (reds and not not_red and all(seen_.get(k) for k in GREEN_BOTH)) else 1)
    sys.exit(1 if reds or not R else 0)
