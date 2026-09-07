#!/usr/bin/env python3
# =============================================================================
#  WALK_clinic_state.py · S230 · the LIVE-SHAPE walk for clinic_state_backup v1
#
#  A fixture estate in a temp dir — real sqlite databases, real csvs, real
#  "secret" files that must be skipped, a fake /etc/systemd/system, a fake
#  vhost tree, a fake crontab — and a fake Drive that stores the bytes it
#  actually receives, md5s them itself, and keeps a revision list per file.
#  The REAL gather/preflight/run/list functions are then driven through:
#
#   1  gather: every included file present, every excluded one absent
#   2  secrets skipped by pattern, counted, never named\n#  2b  v2 discovery: .jsonl/.json/.html and one level down are DATA,\n#      and widening that did NOT widen what counts as a secret
#   3  databases copied by the sqlite ONLINE BACKUP api (row counts survive)
#   4  the shape: crontab, clinic units only, clinic vhosts only, schemas,
#      and both shape directories overridable from the conf
#   5  INVENTORY.txt: one line per file, with size and mtime
#   6  encryption: round trip, salt header, wrong key refused, ciphertext opaque
#   7  run happy path: ship -> read back -> monthly PINNED -> state file
#   8  the shipped bytes really are the bundle (decrypt -> untar -> query db)
#   9  second run same month: nightly revises, monthly does not
#  10  read-back mismatch -> exit 30, monthly untouched, state NOT advanced
#  11  integrity failure -> exit 40 before any network call
#  12  a source that vanished since the last success -> exit 41
#  13  key file missing / world-readable -> exit 15
#  14  openssl absent -> exit 14
#  15  slot files missing -> exit 13
#  16  preflight end to end, content untouched
#
#  NO NETWORK. NO REAL PATH. Every module knob is pointed at the fixture tree
#  and the only Drive is the fake one; make_session is never called.
#
#  Run:  python -B WALK_clinic_state.py   (exits 0 with ALL WALK CHECKS PASS)
# =============================================================================
import gzip, hashlib, json, os, shutil, sqlite3, sys, tarfile, tempfile, time

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clinic_state_backup as M

CHECKS = []


def check(name, cond):
    CHECKS.append((name, bool(cond)))
    print("  [%s] %s" % ("ok " if cond else "FAIL", name))


# --------------------------------------------------------------- the drive --
class FakeDrive(object):
    """Owner-owned slot files with content, revisions and descriptions."""

    def __init__(self, session=None):
        self.files = {}
        self.calls = 0
        self.mangle_next = False

    def _f(self, i):
        return self.files[i]

    def seed(self, i, name):
        self.files[i] = {"name": name, "bytes": b"placeholder", "description": "",
                         "revisions": [{"id": "r0", "keepForever": False}]}

    def about(self):
        self.calls += 1
        return {"user": {"emailAddress": "sa@walk"}}

    def folder(self, fid):
        self.calls += 1
        return {"id": fid, "name": "ClinicState_Backups",
                "mimeType": "application/vnd.google-apps.folder"}

    def list(self, fid):
        self.calls += 1
        return [{"id": k, "name": v["name"], "size": str(len(v["bytes"])),
                 "md5Checksum": hashlib.md5(v["bytes"]).hexdigest(),
                 "description": v["description"]} for k, v in self.files.items()]

    def update_content(self, i, path):
        self.calls += 1
        data = open(path, "rb").read()
        if self.mangle_next:
            data = data[:-1] + b"X"
            self.mangle_next = False
        f = self._f(i)
        f["bytes"] = data
        f["revisions"].append({"id": "r%d" % len(f["revisions"]), "keepForever": False})
        return {"id": i}

    def patch_meta(self, i, body):
        self.calls += 1
        self._f(i)["description"] = body.get("description", self._f(i)["description"])
        return {"id": i}

    def get(self, i):
        self.calls += 1
        v = self._f(i)
        return {"id": i, "name": v["name"], "size": str(len(v["bytes"])),
                "md5Checksum": hashlib.md5(v["bytes"]).hexdigest(),
                "description": v["description"]}

    def revisions(self, i):
        self.calls += 1
        return list(self._f(i)["revisions"])

    def pin_revision(self, i, rid):
        self.calls += 1
        for r in self._f(i)["revisions"]:
            if r["id"] == rid:
                r["keepForever"] = True
                return
        raise RuntimeError("no such revision")


SESSIONS_MADE = []


def mk(sa):
    SESSIONS_MADE.append(sa)
    return None


# ------------------------------------------------------------- the fixture --
ROOT = tempfile.mkdtemp(prefix="walk_state_")


def p(*a):
    return os.path.join(ROOT, *a)


def mkdirs(*ds):
    for d in ds:
        os.makedirs(d, exist_ok=True)


def make_db(path, table, rows):
    c = sqlite3.connect(path)
    c.execute("CREATE TABLE %s (id INTEGER PRIMARY KEY, v TEXT)" % table)
    c.executemany("INSERT INTO %s (v) VALUES (?)" % table,
                  [("row-%d" % i,) for i in range(rows)])
    c.execute("CREATE INDEX idx_%s_v ON %s (v)" % (table, table))
    c.commit()
    c.close()


def write(path, text):
    mkdirs(os.path.dirname(path))
    with open(path, "w") as fh:
        fh.write(text)


mkdirs(p("wa"), p("assetapp", "uploads"), p("staff_register"), p("staff_ledger"),
       p("systemd"), p("vhosts"), p("state_backup", "work"))

make_db(p("wa", "console.db"), "calls", 40)
make_db(p("assetapp", "assets.db"), "assets", 12)
make_db(p("staff_register", "register.db"), "register", 7)
make_db(p("staff_ledger", "ledger.db"), "ledger", 5)
write(p("punches.csv"), "emp,ts\n1,2026-09-01T09:00\n")
write(p("punches_raw.log"), "raw punch line\nraw punch line 2\n")
write(p("staff_master.csv"), "emp,name\n1,A\n")
write(p("staff_register", "notes.csv"), "d,note\n2026-09-01,x\n")
write(p("staff_register", "app.py"), "# code, not data — GitHub is its backup\n")
write(p("staff_register", ".env"), "SECRET=never-in-a-backup\n")
write(p("staff_ledger", "credentials.json"), "{}\n")
write(p("staff_ledger", "token.json"), "{}\n")

# --- the live-box shapes v1 missed (S230 v2). These are the whole reason the
# --- extension list was widened, so the fixture now carries every one.
write(p("staff_ledger", "ledger.jsonl"),
      '{"staff":"A","owes":100}\n{"staff":"B","owes":250}\n')     # THE LEDGER
write(p("staff_ledger", "advance_pct.json"), '{"pct":30}\n')
write(p("staff_ledger", "waivers_2026-07.json"), '{"waived":[]}\n')
write(p("staff_ledger", "users.json"), '{"users":["maker","checker"]}\n')
write(p("staff_ledger", "approved_adjustments_2026-07.csv"), "who,amt\nA,10\n")
write(p("staff_ledger", "applications", "app_001.json"), '{"id":1}\n')
write(p("staff_ledger", "applications", "deeper", "too_deep.json"), '{"id":2}\n')
write(p("staff_ledger", "secret_key"), "x" * 64)          # MUST stay skipped
write(p("staff_ledger", "sa_key.json"), '{"type":"x"}\n')  # MUST stay skipped
write(p("staff_register", "hold_ledger.jsonl"), '{"hold":1}\n')
write(p("staff_register", "manual_advances_2026-07.json"), '{"adv":[]}\n')
write(p("staff_register", "register_salary_2026-07.html"),
      "<html><body>salary register</body></html>\n")
write(p("staff_register", "salary_engine.py"), "# code\n")
write(p("staff_register", "salary_engine.py.bak"), "# older code\n")
write(p("staff_register", "salary_engine.py.bak2"), "# older code still\n")
write(p("staff_register", "__pycache__", "salary_engine.cpython-39.pyc"), "junk\n")
write(p("wa", "api_key.json"), "{}\n")
write(p("assetapp", "uploads", "scan001.jpg"), "x" * 2048)

for unit in ("clinic-portal.service", "assetapp.service", "wa-send-api.service",
             "staff-ledger.service", "attlistener.service",
             "clinic-watchdog.timer", "clinic-followup-push.timer"):
    write(p("systemd", unit), "[Unit]\nDescription=%s\n" % unit)
for unit in ("sshd.service", "fitlog.service", "gutlog.service",
             "rxguard.service", "dnf-makecache.timer"):
    write(p("systemd", unit), "[Unit]\nDescription=%s\n" % unit)

for dom in ("followup.dr-manoj.in", "assets.dr-manoj.in",
            "attendance.dr-manoj.in", "example.com", "rx.dr-manoj.in"):
    write(p("vhosts", dom, "vhost.conf"), "docRoot $VH_ROOT/%s\n" % dom)

KEYFILE = p("state_backup", "state_backup.key")
write(KEYFILE, "walk-fixture-passphrase-not-a-real-key-do-not-use-anywhere\n")
os.chmod(KEYFILE, 0o600)
OTHERKEY = p("state_backup", "other.key")
write(OTHERKEY, "a-completely-different-passphrase-for-the-wrong-key-test\n")
os.chmod(OTHERKEY, 0o600)

SA = p("state_backup", "sa.json")
json.dump({"type": "service_account", "client_email": "walk-sa@example.iam"},
          open(SA, "w"))

M.CONF_PATH = p("state_backup", "clinic_state_backup.conf")
CONF_LINES = [
    "SA_JSON=%s" % SA,
    "FOLDER_ID=FOLDER1",
    "ENC_KEY_FILE=%s" % KEYFILE,
    "WORK_DIR=%s" % p("state_backup", "work"),
    "STATE_FILE=%s" % p("state_backup", "state.json"),
    "SUMMARY_FILE=%s" % p("state_backup", "summary.log"),
]
write(M.CONF_PATH, "\n".join(CONF_LINES) + "\n")

M.SRC_FILES = [p("wa", "console.db"), p("assetapp", "assets.db"),
               p("punches.csv"), p("punches_raw.log"), p("staff_master.csv"),
               p("wa", "api_key.json")]      # the last one MUST be skipped
M.SRC_DIRS = [p("staff_register"), p("staff_ledger")]
M.SYSTEMD_DIR = p("systemd")
M.VHOST_DIR = p("vhosts")
M.CRONTAB_CMD = ["printf", "50 1 * * * clinic_state_backup.py run\\n"]

CONF = M.load_conf()

# ============================================================================
print("- 1 . gather: what is in, what is out")
STAGE = p("state_backup", "stage1")
G = M.gather(CONF, STAGE, integrity_fatal=True)
inbundle = set()
for base, _d, files in os.walk(STAGE):
    for n in files:
        inbundle.add(os.path.relpath(os.path.join(base, n), STAGE).replace("\\", "/"))

check("console.db is in the bundle", "data/console.db" in inbundle)
check("assets.db is in the bundle", "data/assets.db" in inbundle)
check("punches.csv is in the bundle", "data/punches.csv" in inbundle)
check("punches_raw.log is in the bundle", "data/punches_raw.log" in inbundle)
check("staff_master.csv is in the bundle", "data/staff_master.csv" in inbundle)
check("staff_register store discovered (register.db)",
      "data/staff_register/register.db" in inbundle)
check("staff_register store discovered (notes.csv)",
      "data/staff_register/notes.csv" in inbundle)
check("staff_ledger store discovered (ledger.db)",
      "data/staff_ledger/ledger.db" in inbundle)
check("assetapp uploads/ excluded entirely",
      not any("uploads" in x or "scan001" in x for x in inbundle))
check("application code (.py) not gathered as data",
      not any(x.endswith("app.py") for x in inbundle))

print("- 2 . secrets are skipped by pattern and counted, never named")
check(".env not in the bundle", not any(x.endswith(".env") for x in inbundle))
check("credentials.json not in the bundle",
      not any("credentials" in x for x in inbundle))
check("token.json not in the bundle", not any("token" in x for x in inbundle))
check("api_key.json not in the bundle", not any("api_key" in x for x in inbundle))
check("exactly 6 secrets skipped and counted", G.secrets_skipped == 6)
check("is_secret catches every named pattern",
      all(M.is_secret(n) for n in (".env", "prod.env", "sa_key.json", "token.txt",
                                   "credentials.json", "server.pem", "id_rsa",
                                   "my.key", "app_secret.txt")))
check("is_secret does not eat ordinary data names",
      not any(M.is_secret(n) for n in ("console.db", "punches.csv",
                                       "staff_master.csv", "notes.csv")))

print("- 2b . v2 discovery: the live-box shapes v1 missed, and the secrets it must not")
LEDGER = set(x[len("data/staff_ledger/"):] for x in inbundle
             if x.startswith("data/staff_ledger/"))
REGISTER = set(x[len("data/staff_register/"):] for x in inbundle
               if x.startswith("data/staff_register/"))
check("THE STAFF LEDGER ITSELF is included (top-level .jsonl)",
      "ledger.jsonl" in LEDGER)
check("a top-level .json is included", "advance_pct.json" in LEDGER)
check("the dated .json files are included",
      "waivers_2026-07.json" in LEDGER and "users.json" in LEDGER)
check("a file one level down is included, with its subpath preserved",
      "applications/app_001.json" in LEDGER)
check("two levels down is NOT included (depth cap)",
      not any("deeper" in x for x in LEDGER))
check("the register .jsonl is included", "hold_ledger.jsonl" in REGISTER)
check("the register .json is included", "manual_advances_2026-07.json" in REGISTER)
check("a generated .html record is included",
      "register_salary_2026-07.html" in REGISTER)
check("secret_key is STILL skipped though .jsonl and .json are now data",
      not any("secret_key" in x for x in inbundle))
check("sa_key.json is STILL skipped", not any("sa_key" in x for x in inbundle))
check("both new secrets are matched by pattern",
      M.is_secret("secret_key") and M.is_secret("sa_key.json"))
check("the ledger sits beside those two secrets and still travels",
      "ledger.jsonl" in LEDGER and "sa_key.json" not in LEDGER
      and "secret_key" not in LEDGER)
check("code is still excluded", not any(x.endswith("salary_engine.py")
                                        for x in inbundle))
check("backups of code are still excluded",
      not any(".bak" in x for x in inbundle))
check("__pycache__ is still excluded",
      not any("pycache" in x or x.endswith(".pyc") for x in inbundle))
check("the ledger store yields exactly the seven data files it has",
      LEDGER == {"ledger.db", "ledger.jsonl", "advance_pct.json",
                 "waivers_2026-07.json", "users.json",
                 "approved_adjustments_2026-07.csv",
                 "applications/app_001.json"})
check("the register store yields exactly the five data files it has",
      REGISTER == {"register.db", "notes.csv", "hold_ledger.jsonl",
                   "manual_advances_2026-07.json",
                   "register_salary_2026-07.html"})
check("the included-file count rose by the nine v1 would have missed",
      len(G.entries) == 34)

print("- 3 . databases travel through the sqlite online-backup api")


def rows(path, table):
    c = sqlite3.connect(path)
    try:
        return c.execute("SELECT COUNT(*) FROM %s" % table).fetchone()[0]
    finally:
        c.close()


check("console.db copy opens and holds all 40 rows",
      rows(os.path.join(STAGE, "data", "console.db"), "calls") == 40)
check("register.db copy opens and holds all 7 rows",
      rows(os.path.join(STAGE, "data", "staff_register", "register.db"),
           "register") == 7)
check("copy is a real database, not a byte copy of a live file",
      M.sqlite_integrity(os.path.join(STAGE, "data", "console.db")) == "ok")
check("all four databases were integrity-checked", len(G.databases) == 4)
check("all four answered ok", all(a == "ok" for _s, a in G.databases))

print("- 4 . the shape of the machine")
crontab = open(os.path.join(STAGE, "shape", "crontab.txt")).read()
check("crontab captured", "clinic_state_backup.py run" in crontab)
units = os.listdir(os.path.join(STAGE, "shape", "systemd"))
check("clinic-portal.service collected", "clinic-portal.service" in units)
check("assetapp.service collected", "assetapp.service" in units)
check("staff-ledger.service collected", "staff-ledger.service" in units)
check("clinic-watchdog.timer collected", "clinic-watchdog.timer" in units)
check("sshd.service NOT collected", "sshd.service" not in units)
check("personal-cluster units NOT collected",
      not any(u.startswith(("fitlog", "gutlog", "rxguard")) for u in units))
check("OS timers NOT collected", "dnf-makecache.timer" not in units)
vhosts = os.listdir(os.path.join(STAGE, "shape", "vhosts"))
check("clinic vhost configs collected",
      "followup.dr-manoj.in.vhost.conf" in vhosts and
      "assets.dr-manoj.in.vhost.conf" in vhosts)
check("non-clinic vhost NOT collected",
      not any(v.startswith("example.com") for v in vhosts))
schemas = os.listdir(os.path.join(STAGE, "shape", "schema"))
check("a .schema dump exists for every database", len(schemas) == 4)
sch = open(os.path.join(STAGE, "shape", "schema", "console.db.schema.sql")).read()
check("schema dump carries CREATE TABLE and CREATE INDEX",
      "CREATE TABLE calls" in sch and "CREATE INDEX" in sch)

print("- 4b . the shape directories are conf-overridable")
mkdirs(p("altsystemd"), p("altvhosts"))
write(p("altsystemd", "clinic-alt.service"), "[Unit]\nDescription=alt\n")
write(p("altvhosts", "alt.dr-manoj.in", "vhost.conf"), "docRoot alt\n")
CONF_ALT = dict(CONF)
CONF_ALT["SYSTEMD_DIR"] = p("altsystemd")
CONF_ALT["VHOST_DIR"] = p("altvhosts")
STAGE_ALT = p("state_backup", "stage_alt")
M.gather(CONF_ALT, STAGE_ALT, integrity_fatal=True)
alt_units = os.listdir(os.path.join(STAGE_ALT, "shape", "systemd"))
alt_vh = os.listdir(os.path.join(STAGE_ALT, "shape", "vhosts"))
check("SYSTEMD_DIR override honoured",
      alt_units == ["clinic-alt.service"])
check("VHOST_DIR override honoured",
      alt_vh == ["alt.dr-manoj.in.vhost.conf"])

print("- 5 . the inventory")
inv = open(os.path.join(STAGE, "INVENTORY.txt")).read()
inv_rows = [l for l in inv.splitlines() if l and not l.startswith("#")]
check("inventory has a line per included file", len(inv_rows) == len(G.entries) - 1)
check("inventory lines carry path, size and mtime",
      all(len(l.split("\t")) == 4 and l.split("\t")[1].isdigit() for l in inv_rows))
check("inventory states the secrets-skipped count",
      "secrets skipped by pattern: 6" in inv)
check("inventory states what is excluded by design", "EXCLUDED by design" in inv)

print("- 6 . encryption")
WORK = p("state_backup", "work")
check("round trip proves itself", M.crypto_roundtrip(KEYFILE, WORK) is True)
plain = p("state_backup", "plain.txt")
write(plain, "PATIENTNAMEMARKER-and-staff-salary-marker\n" * 20)
enc = M.encrypt_file(plain, p("state_backup", "plain.enc"), KEYFILE)
blob = open(enc, "rb").read()
check("ciphertext carries the openssl salt header", blob[:8] == b"Salted__")
check("ciphertext does not contain the plaintext",
      b"PATIENTNAMEMARKER" not in blob)
dec = M.decrypt_file(enc, p("state_backup", "plain.out"), KEYFILE)
check("decrypt with the right key restores the bytes",
      M.md5_file(dec) == M.md5_file(plain))
wrong = False
try:
    M.decrypt_file(enc, p("state_backup", "plain.bad"), OTHERKEY)
except RuntimeError:
    wrong = True
check("decrypt with the wrong key refuses", wrong)

print("- 7 . run: happy path, first run of the month")
fake = FakeDrive()
fake.seed("N1", M.NIGHTLY)
fake.seed("M1", M.MONTHLY)
drv = lambda session: fake
M.run(drive_cls=drv, session_maker=mk)
shipped = fake.files["N1"]["bytes"]
check("nightly slot received the encrypted bundle", shipped[:8] == b"Salted__")
check("monthly slot holds the same bytes", fake.files["M1"]["bytes"] == shipped)
check("monthly head revision PINNED",
      fake.files["M1"]["revisions"][-1]["keepForever"] is True)
check("monthly description carries the month tag",
      "month=%s" % time.strftime("%Y-%m") in fake.files["M1"]["description"])
check("nightly description stamped",
      "encrypted clinic state" in fake.files["N1"]["description"])
check("no real Drive session was ever made (fake drive only)",
      len(SESSIONS_MADE) > 0 and all(x == SA for x in SESSIONS_MADE) and
      M.Drive not in (type(fake),))

print("- 8 . the shipped bytes really are the bundle")
shipped_path = p("state_backup", "shipped.enc")
open(shipped_path, "wb").write(shipped)
outtar = M.decrypt_file(shipped_path, p("state_backup", "shipped.tar.gz"), KEYFILE)
check("shipped bytes decrypt to a gzip", open(outtar, "rb").read(2) == b"\x1f\x8b")
ex = p("state_backup", "extract")
with tarfile.open(outtar, "r:gz") as tf:
    names = tf.getnames()
    tf.extractall(ex)
top = sorted(set(n.split("/")[0] for n in names))
check("archive has one dated top-level directory",
      len(top) == 1 and top[0].startswith("clinic_state_"))
check("archive carries INVENTORY.txt",
      any(n.endswith("/INVENTORY.txt") for n in names))
check("archive carries the console database",
      any(n.endswith("/data/console.db") for n in names))
check("archive carries the shape",
      any(n.endswith("/shape/crontab.txt") for n in names) and
      any("/shape/systemd/" in n for n in names))
check("the restored console database still answers 40 rows",
      rows(os.path.join(ex, top[0], "data", "console.db"), "calls") == 40)

print("- 9 . the state file - a backup that cannot state its own age has not been taken")
st = json.load(open(p("state_backup", "state.json")))
for key in ("last_success_iso", "bytes", "md5", "files_included", "secrets_skipped"):
    check("state records %s" % key, key in st and st[key] != "")
check("state md5 matches the shipped bytes",
      st["md5"] == hashlib.md5(shipped).hexdigest())
check("state bytes matches the shipped length", st["bytes"] == len(shipped))
check("state secrets_skipped is 6", st["secrets_skipped"] == 6)
check("state lists the sources it took", len(st["sources"]) >= 8)
summary = open(p("state_backup", "summary.log")).read()
check("a one-line summary was written", summary.count("\n") == 1 and " OK " in summary)

print("- 10 . second run in the same month")
n_rev = len(fake.files["N1"]["revisions"])
m_rev = len(fake.files["M1"]["revisions"])
M.run(drive_cls=drv, session_maker=mk)
check("nightly gained a revision", len(fake.files["N1"]["revisions"]) == n_rev + 1)
check("monthly did NOT", len(fake.files["M1"]["revisions"]) == m_rev)
check("summary log now has two lines",
      open(p("state_backup", "summary.log")).read().count("\n") == 2)

print("- 11 . read-back mismatch is FATAL and the monthly is not touched")
fake2 = FakeDrive()
fake2.seed("N1", M.NIGHTLY)
fake2.seed("M1", M.MONTHLY)
fake2.mangle_next = True
m_before = fake2.files["M1"]["bytes"]
state_before = open(p("state_backup", "state.json")).read()
rc = 0
try:
    M.run(drive_cls=(lambda s: fake2), session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 30 on read-back mismatch", rc == 30)
check("monthly untouched", fake2.files["M1"]["bytes"] == m_before)
check("nightly description NOT stamped", fake2.files["N1"]["description"] == "")
check("state file NOT advanced by a failed run",
      open(p("state_backup", "state.json")).read() == state_before)

print("- 12 . a database that fails integrity stops everything, before the network")
good = open(p("wa", "console.db"), "rb").read()
with open(p("wa", "console.db"), "wb") as fh:
    fh.write(b"SQLite format 3\x00" + b"\x00" * 200 + b"junk" * 400)
calls_before = fake.calls
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 40 on integrity failure", rc == 40)
check("zero Drive calls were made", fake.calls == calls_before)
with open(p("wa", "console.db"), "wb") as fh:
    fh.write(good)
check("integrity answer for a good db is ok",
      M.sqlite_integrity(p("wa", "console.db")) == "ok")

print("- 13 . a source present last time and missing now is FATAL")
os.rename(p("punches.csv"), p("punches.csv.moved"))
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 41 when a known source vanished", rc == 41)
os.rename(p("punches.csv.moved"), p("punches.csv"))

print("- 14 . the key file is guarded")
os.chmod(KEYFILE, 0o644)
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 15 on a world-readable key file", rc == 15)
os.chmod(KEYFILE, 0o600)
os.rename(KEYFILE, KEYFILE + ".hidden")
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 15 when the key file is absent", rc == 15)
os.rename(KEYFILE + ".hidden", KEYFILE)

print("- 15 . openssl absent, and slot files absent")
real_openssl = M.OPENSSL
M.OPENSSL = os.path.join(ROOT, "no-such-openssl")
rc = 0
try:
    M.run(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 14 when openssl is unavailable", rc == 14)
M.OPENSSL = real_openssl
fake3 = FakeDrive()          # an empty folder
rc = 0
try:
    M.run(drive_cls=(lambda s: fake3), session_maker=mk)
except SystemExit as e:
    rc = e.code
check("exit 13 when a slot file is missing", rc == 13)

print("- 16 . preflight proves everything and changes nothing")
n_bytes = fake.files["N1"]["bytes"]
n_revs = len(fake.files["N1"]["revisions"])
rc = 0
try:
    M.preflight(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("preflight OK end to end", rc == 0)
check("preflight touched no content and made no revision",
      fake.files["N1"]["bytes"] == n_bytes and
      len(fake.files["N1"]["revisions"]) == n_revs)
check("write access proven via description",
      "preflight write-test" in fake.files["N1"]["description"])
rc = 0
try:
    M.list_mode(drive_cls=drv, session_maker=mk)
except SystemExit as e:
    rc = e.code
check("list mode reports without shipping", rc == 0 and
      fake.files["N1"]["bytes"] == n_bytes)

shutil.rmtree(ROOT, ignore_errors=True)
fails = [n for n, ok in CHECKS if not ok]
print()
print("%d checks, %d failures" % (len(CHECKS), len(fails)))
if fails:
    print("WALK FAILED:", ", ".join(fails))
    sys.exit(1)
print("ALL WALK CHECKS PASS (%d)" % len(CHECKS))
sys.exit(0)
