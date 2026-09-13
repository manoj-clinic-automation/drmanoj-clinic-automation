#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
selftest_salts_refresh_s243.py -- the S243_SALTS_REFRESH kit against a mock, end to end.

Builds under a temp root: a fake server archive with TWO SALT_WISE_ITEM_LIST files (older / newer, the older
given the NEWER mtime so the name stamp must win) plus a decoy of another type; a fake finance door (local
HTTP server on a free port) that records the POST; a fake systemd drop-in with a dummy token. Then runs
salts_refresh.main() and asserts: newest chosen; payload equals push_salts.read_marg_salt_list for the same
file; header carries the token; state written; second --once is a no-op; --force re-sends; --dry-run sends
nothing; a wrong token is refused. If the live purchase_app.py (S240_SANJEEVNI_123) and flask are at hand,
the recorded payload is also fed to the REAL /api/salts handler on a temp db: purchase_salt_marg is replaced
whole, MAX(as_on) is the new date, and an existing DONE tick survives.

Fixtures are raw BIFF8 streams written here (no xlwt needed) and read with the vendored xlrd of
S240_MARG_INGEST -- the same reader the server uses.

Run:  python3 -B selftest_salts_refresh_s243.py           (from inside the kit folder or anywhere)
"""
import glob
import hashlib
import io
import json
import os
import sqlite3
import struct
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

HERE = os.path.dirname(os.path.abspath(__file__))
KITS = os.path.dirname(HERE)
CANDIDATE_KITS = [KITS, "/tmp/kbv/deploy_kits", "/root/deploy/repo/deploy_kits"]


def kit(name):
    for k in CANDIDATE_KITS:
        p = os.path.join(k, name)
        if os.path.isdir(p):
            return p
    return None


INGEST = kit("S240_MARG_INGEST")
S225 = kit("S225_SALTS")
LIVE = kit("S240_SANJEEVNI_123")
if not INGEST:
    print("FAILED: S240_MARG_INGEST kit (vendored marg_report + xlrd) not found beside this kit")
    sys.exit(1)
sys.path.insert(0, HERE)
sys.path.insert(0, INGEST)
import salts_refresh as SR                                    # noqa: E402

PASS = FAIL = 0


def ck(label, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ok   %s" % label)
    else:
        FAIL += 1
        print("  FAIL %s  %s" % (label, detail))


# ------------------------------------------------------------------ minimal BIFF8 writer (fixtures)
def _rec(code, data):
    return struct.pack("<HH", code, len(data)) + data


def _ustr8(s):
    return struct.pack("<BB", len(s), 1) + s.encode("utf-16-le")


def _ustr16(s):
    return struct.pack("<HB", len(s), 1) + s.encode("utf-16-le")


def write_xls(path, rows):
    """rows: list of lists; str -> LABEL, number -> NUMBER, None/'' skipped. Raw BIFF8, no OLE wrapper."""
    bof_g = _rec(0x0809, struct.pack("<HHHHII", 0x0600, 0x0005, 0x0DBB, 0x07CC, 0, 0))
    bof_s = _rec(0x0809, struct.pack("<HHHHII", 0x0600, 0x0010, 0x0DBB, 0x07CC, 0, 0))
    cp = _rec(0x0042, struct.pack("<H", 1200))
    eof = _rec(0x000A, b"")
    sheet = bof_s
    for r, row in enumerate(rows):
        for c, v in enumerate(row):
            if v is None or v == "":
                continue
            if isinstance(v, (int, float)):
                sheet += _rec(0x0203, struct.pack("<HHHd", r, c, 0, float(v)))
            else:
                sheet += _rec(0x0204, struct.pack("<HHH", r, c, 0) + _ustr16(str(v)))
    sheet += eof
    bs_len = 4 + 1 + 1 + 2 + len("Sheet1") * 2
    glen = len(bof_g) + len(cp) + 4 + bs_len + len(eof)
    bs = _rec(0x0085, struct.pack("<IBB", glen, 0, 0) + _ustr8("Sheet1"))
    with open(path, "wb") as fh:
        fh.write(bof_g + cp + bs + eof + sheet)


def salt_list_rows(n_salts, per_salt, tag):
    """The shape of Marg's SALT WISE ITEM LIST: title, blank, header, then a salt line (col A only) and its
    items as 'N     NAME' with packing and three rates. A page-number '1.0' and a note line are sprinkled
    in, as the real export has them."""
    rows = [["SALT WISE ITEM LIST"], [""], ["S.No. DESCRIPTION", "PACKING", "P.RATE", "S.RATE", "M.R.P."]]
    n = 0
    for s in range(n_salts):
        rows.append(["ZZ SALT %s %02d" % (tag, s)])
        for i in range(per_salt):
            n += 1
            rows.append(["%d     ZZ ITEM %s %03d" % (n, tag, n), "10X10", 10.5 + i, 12.0 + i, 15.0 + i])
        if s == 1:
            rows.append([1.0])                                # page number cell, skipped by the reader
    rows.append(["Total Items : %d" % n, "", "", "", ""])
    return rows


# ------------------------------------------------------------------ fake finance door
class _Door(BaseHTTPRequestHandler):
    calls = []
    token = "DUMMY-TOKEN-PUT-HERE"

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n)
        try:
            body = json.loads(raw.decode("utf-8"))
        except ValueError:
            body = None
        rec = dict(path=self.path, token=self.headers.get("X-Finance-Marg"), body=body)
        _Door.calls.append(rec)
        if rec["token"] != _Door.token:
            out, code = dict(ok=False, error="bad_token"), 401
        elif not isinstance(body, dict) or not body.get("marg_items"):
            out, code = dict(ok=False, error="malformed"), 400
        else:
            out, code = dict(ok=True, stored=0, kept=0, marg_items=len(body["marg_items"])), 200
        data = json.dumps(out).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):                                # quiet
        pass


srv = HTTPServer(("127.0.0.1", 0), _Door)
PORT = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = "http://127.0.0.1:%d/finance/purchase/api/salts" % PORT

# ------------------------------------------------------------------ the mock root
TMP = tempfile.mkdtemp(prefix="s243_salts_")
ARCH = os.path.join(TMP, "root", "marg_ingest", "archive")
DROPIN = os.path.join(TMP, "etc", "systemd", "system", "clinic-finance.service.d", "marg_token.conf")
STATE = os.path.join(TMP, "root", "finance", "salts_refresh.state.json")
os.makedirs(os.path.join(ARCH, "SALT_WISE_ITEM_LIST", "2026-08"))
os.makedirs(os.path.join(ARCH, "SALT_WISE_ITEM_LIST", "2026-09"))
os.makedirs(os.path.join(ARCH, "STOCK_CLOSING", "2026-09"))
os.makedirs(os.path.dirname(DROPIN))
with io.open(DROPIN, "w", encoding="utf-8") as fh:
    fh.write("[Service]\nEnvironment=FINANCE_MARG_TOKEN=%s\n" % _Door.token)


def stamped(folder, as_on, stamp, rows):
    tmp = os.path.join(TMP, "tmp.xls")
    write_xls(tmp, rows)
    d = hashlib.md5(open(tmp, "rb").read()).hexdigest()[:8]
    dest = os.path.join(ARCH, "SALT_WISE_ITEM_LIST", folder, "SALT_WISE_ITEM_LIST_DEFAULT__%s__%s__%s.XLS" % (as_on, stamp, d))
    os.replace(tmp, dest)
    return dest


OLDER = stamped("2026-08", "2026-08-28", "20260828-190512", salt_list_rows(5, 22, "OLD"))    # 110 items
NEWER = stamped("2026-09", "2026-09-12", "20260912-224900", salt_list_rows(6, 20, "NEW"))    # 120 items
write_xls(os.path.join(ARCH, "STOCK_CLOSING", "2026-09", "STOCK_CLOSING_DEFAULT__2026-09-13__20260913-080000__deadbeef.XLS"),
          salt_list_rows(9, 30, "DECOY"))
now = time.time()
os.utime(OLDER, (now, now))                       # the OLDER file gets the newer mtime: the name stamp must decide
os.utime(NEWER, (now - 86400, now - 86400))

ARGS = ["--archive=" + ARCH, "--ingest=" + INGEST, "--dropin=" + DROPIN, "--state=" + STATE, "--url=" + URL]

print("S243_SALTS_REFRESH selftest  (mock root %s, door on port %d)" % (TMP, PORT))

# ------------------------------------------------------------------ 1. choosing and reading
print("1. the newest file, by the stamp in its name")
ck("find_newest picks the 12-Sep file although the 28-Aug file has the newer mtime", SR.find_newest(ARCH) == NEWER, str(SR.find_newest(ARCH)))
ck("the STOCK_CLOSING decoy is never a candidate", "DECOY" not in (SR.find_newest(ARCH) or ""))
ck("as_on comes from the capture stamp: 2026-09-12", SR.as_on_of(NEWER) == "2026-09-12", SR.as_on_of(NEWER))
items, as_on = SR.read_marg_salt_list(NEWER, INGEST)
ck("reads 120 items under 6 salts (page-number and total lines skipped)", len(items) == 120 and len({i["salt"] for i in items}) == 6, "%d items" % len(items))
ck("an item row is {item, salt} with the salt upper-cased and the leading number stripped",
   items[0] == dict(item="ZZ ITEM NEW 001", salt="ZZ SALT NEW 00"), str(items[0]))
ck("the token is read from the drop-in and equals the dummy", SR.read_token(DROPIN) == _Door.token)
ck("a missing drop-in gives None, not an exception", SR.read_token(DROPIN + ".absent") is None)

# ------------------------------------------------------------------ 2. same payload as push_salts.py
print("2. the payload is push_salts.py's, key for key")
if S225:
    sys.path.insert(0, S225)
    import push_salts as PS                                   # noqa: E402
    ref_items, ref_as_on = PS.read_marg_salt_list(NEWER)
    body = SR.build_payload(NEWER, INGEST)
    ck("marg_items == push_salts.read_marg_salt_list(same file)", body["marg_items"] == ref_items, "%d vs %d" % (len(body["marg_items"]), len(ref_items)))
    ck("marg_as_on == push_salts' as_on (stamp date)", body["marg_as_on"] == ref_as_on == "2026-09-12", "%s vs %s" % (body["marg_as_on"], ref_as_on))
    ck("marg_md5 is the file's full md5, as push_salts sends it", body["marg_md5"] == hashlib.md5(open(NEWER, "rb").read()).hexdigest())
    ck("no 'tasks' / 'salt_tasks' key: Amir's ticks are never in this payload", "tasks" not in body and "salt_tasks" not in body)
    ck("the older file reads the same way through both readers", SR.read_marg_salt_list(OLDER, INGEST)[0] == PS.read_marg_salt_list(OLDER)[0])
else:
    ck("(S225_SALTS kit not beside this one -- push_salts comparison skipped)", True)

# ------------------------------------------------------------------ 3. dry run, once, once again, force
print("3. --dry-run / --once / --once / --force")
_Door.calls[:] = []
rc = SR.main(ARGS + ["--dry-run"])
ck("--dry-run exits 0 and sends nothing", rc == 0 and _Door.calls == [], "rc=%s calls=%d" % (rc, len(_Door.calls)))
ck("--dry-run writes no state", not os.path.exists(STATE))

rc = SR.main(ARGS + ["--once"])
ck("first --once exits 0 and POSTs once", rc == 0 and len(_Door.calls) == 1, "rc=%s calls=%d" % (rc, len(_Door.calls)))
c = _Door.calls[0]
ck("POST went to /finance/purchase/api/salts", c["path"] == "/finance/purchase/api/salts", c["path"])
ck("header X-Finance-Marg carries the drop-in token", c["token"] == _Door.token)
ck("body carries 120 marg_items, marg_as_on 2026-09-12, marg_md5 of the NEWER file",
   c["body"] and len(c["body"]["marg_items"]) == 120 and c["body"]["marg_as_on"] == "2026-09-12"
   and c["body"]["marg_md5"] == hashlib.md5(open(NEWER, "rb").read()).hexdigest())
st = json.load(open(STATE))
ck("state written: file, md5, as_on, rows, ok, applied_at, reply", st.get("file") == os.path.basename(NEWER) and st.get("md5") == c["body"]["marg_md5"]
   and st.get("as_on") == "2026-09-12" and st.get("rows") == 120 and st.get("ok") is True and st.get("applied_at") and st.get("reply", {}).get("marg_items") == 120, json.dumps(st)[:200])
ck("the state file holds no token", _Door.token not in open(STATE).read())

rc = SR.main(ARGS + ["--once"])
ck("second --once is a no-op: exit 0, no POST", rc == 0 and len(_Door.calls) == 1, "rc=%s calls=%d" % (rc, len(_Door.calls)))
st2 = json.load(open(STATE))
ck("...but it records checked_at (proof of life) and keeps the applied record", st2.get("checked_at") and st2.get("md5") == st.get("md5") and st2.get("applied_at") == st.get("applied_at"))

rc = SR.main(ARGS + ["--force"])
ck("--force re-sends the same file: exit 0, second POST", rc == 0 and len(_Door.calls) == 2, "rc=%s calls=%d" % (rc, len(_Door.calls)))
ck("the forced payload is identical to the first", _Door.calls[1]["body"] == _Door.calls[0]["body"])

# ------------------------------------------------------------------ 4. a fresh export arrives
print("4. a newer export lands in the archive")
NEWEST = stamped("2026-09", "2026-09-13", "20260913-081500", salt_list_rows(6, 21, "NEWEST"))   # 126 items
os.utime(NEWEST, (now - 2 * 86400, now - 2 * 86400))
rc = SR.main(ARGS + ["--once"])
ck("--once sees the 13-Sep file and POSTs it (126 rows, as_on 2026-09-13)", rc == 0 and len(_Door.calls) == 3
   and len(_Door.calls[2]["body"]["marg_items"]) == 126 and _Door.calls[2]["body"]["marg_as_on"] == "2026-09-13", "rc=%s calls=%d" % (rc, len(_Door.calls)))
rc = SR.main(ARGS + ["--once"])
ck("and the next --once is again a no-op", rc == 0 and len(_Door.calls) == 3)

# ------------------------------------------------------------------ 5. refusals
print("5. what is refused")
SHORT = stamped("2026-09", "2026-09-13", "20260913-090000", salt_list_rows(2, 5, "SHORT"))        # 10 items
rc = SR.main(ARGS + ["--once"])
ck("a 10-row list (truncated export) is NOT sent: exit 2, no POST -- the table is not wiped", rc == 2 and len(_Door.calls) == 3, "rc=%s calls=%d" % (rc, len(_Door.calls)))
rc = SR.main(ARGS + ["--once", "--min-rows=1"])
ck("--min-rows=1 lets it through (the override exists and works)", rc == 0 and len(_Door.calls) == 4)
os.remove(SHORT)
rc = SR.main(ARGS + ["--force", "--dropin=" + DROPIN + ".absent"])
ck("no drop-in -> exit 2, nothing sent", rc == 2 and len(_Door.calls) == 4, "rc=%s" % rc)
with io.open(DROPIN + ".wrong", "w", encoding="utf-8") as fh:
    fh.write("[Service]\nEnvironment=FINANCE_MARG_TOKEN=ZZWRONG\n")
rc = SR.main(ARGS + ["--force", "--dropin=" + DROPIN + ".wrong"])
ck("a wrong token -> the door's 401 -> exit 1, state.ok false", rc == 1 and json.load(open(STATE)).get("ok") is False, "rc=%s" % rc)
rc = SR.main(ARGS + ["--force", "--url=http://127.0.0.1:9/nothing"])
ck("an unreachable door -> exit 1, no crash", rc == 1, "rc=%s" % rc)
EMPTY = os.path.join(TMP, "empty_archive")
os.makedirs(os.path.join(EMPTY, "SALT_WISE_ITEM_LIST"))
before = len(_Door.calls)
rc = SR.main(["--archive=" + EMPTY, "--once", "--state=" + STATE + ".e", "--dropin=" + DROPIN, "--url=" + URL])
ck("an empty archive -> exit 2, nothing sent", rc == 2 and len(_Door.calls) == before, "rc=%s calls=%d" % (rc, len(_Door.calls)))
rc = SR.main(ARGS + ["--force"])
ck("after the refusals a good --force goes through again", rc == 0 and json.load(open(STATE)).get("ok") is True and json.load(open(STATE)).get("as_on") == "2026-09-13")

# ------------------------------------------------------------------ 6. the REAL handler, if at hand
print("6. the live purchase_app's /api/salts on a temp db")
try:
    from flask import Flask, g, has_app_context, jsonify     # noqa: E402
    sys.path.insert(0, LIVE)
    import purchase_app as PA                                 # noqa: E402
    have_live = LIVE is not None
except Exception as e:                                        # noqa: BLE001
    have_live = False
    ck("(flask or the live purchase_app not importable here: %s -- handler leg skipped)" % e.__class__.__name__, True)
if have_live:
    DB = os.path.join(TMP, "finance.db")

    def _db():
        if not has_app_context():
            raise RuntimeError("outside app context")
        if "db" not in g:
            g.db = sqlite3.connect(DB)
            g.db.row_factory = sqlite3.Row
        return g.db

    def _require(*roles, unit="medical"):
        return None, (jsonify(ok=False, error="not_signed_in"), 401)

    for k in ("S225_SALTS", "S224_MARG_PURCHASES", "S225_STAFF_ORDER"):
        if kit(k) and os.path.exists(os.path.join(kit(k), "purchase_schema.sql")):
            PA.SCHEMA = os.path.join(kit(k), "purchase_schema.sql")      # the live kit relies on the installed copy
            break
    app = Flask("s243")
    PA.init(app, _db, _require, unit="medical", marg_token=_Door.token, assets_db=os.path.join(TMP, "absent.db"), assets_url="https://assets.example")
    cl = app.test_client()
    H = {"X-Finance-Marg": _Door.token}
    # yesterday's list (04-Sep, 3 rows) and one DONE tick already on the server
    old = dict(marg_items=[dict(item="ZZ OLD A", salt="OLD"), dict(item="ZZ OLD B", salt="OLD"), dict(item="ZZ ITEM NEWEST 001", salt="WRONG")], marg_as_on="2026-09-04", marg_md5="a" * 32)
    r = cl.post("/finance/purchase/api/salts", json=old, headers=H)
    ck("seed: the handler takes a 3-row list dated 04-Sep", r.status_code == 200 and r.get_json().get("marg_items") == 3, r.get_data(as_text=True)[:120])
    con = sqlite3.connect(DB)
    con.execute("INSERT INTO purchase_salt_task (section,seq,a,b,c,done,done_by,done_at) VALUES ('change',1,'ZZ ITEM NEWEST 001','WRONG','ZZ SALT NEWEST 00',1,'amir','2026-09-10T10:00:00')")
    con.commit(); con.close()
    body = _Door.calls[-1]["body"]                            # exactly what salts_refresh sent on the last --force
    r = cl.post("/finance/purchase/api/salts", json=body, headers=H)
    j = r.get_json() or {}
    ck("the REAL handler accepts salts_refresh's payload: ok, marg_items=126, stored=0 (no tasks touched)", r.status_code == 200 and j.get("ok") is True and j.get("marg_items") == 126 and j.get("stored") == 0, r.get_data(as_text=True)[:160])
    con = sqlite3.connect(DB)
    n = con.execute("SELECT COUNT(*) FROM purchase_salt_marg").fetchone()[0]
    mx = con.execute("SELECT MAX(as_on), MIN(as_on) FROM purchase_salt_marg").fetchone()
    gone = con.execute("SELECT COUNT(*) FROM purchase_salt_marg WHERE item LIKE 'ZZ OLD%'").fetchone()[0]
    tick = con.execute("SELECT done, done_by FROM purchase_salt_task WHERE a='ZZ ITEM NEWEST 001'").fetchone()
    src = con.execute("SELECT DISTINCT source_md5 FROM purchase_salt_marg").fetchall()
    con.close()
    ck("purchase_salt_marg is REPLACED whole: 126 rows, the 04-Sep rows gone", n == 126 and gone == 0, "n=%d gone=%d" % (n, gone))
    ck("every row carries as_on 2026-09-13 -> the page's 'list of 13-Sep-2026' (MAX(as_on))", mx == ("2026-09-13", "2026-09-13"), str(mx))
    ck("Amir's DONE tick on purchase_salt_task survives untouched", tick is not None and tick[0] == 1 and tick[1] == "amir", str(tick))
    ck("source_md5 on the rows is the export's md5 (first 32)", len(src) == 1 and src[0][0] == body["marg_md5"][:32])
    with app.test_request_context():
        c2 = _db()
        marg = {r_[0]: r_[1] for r_ in c2.execute("SELECT item_norm, salt FROM purchase_salt_marg")}
        say = PA._marg_says(c2, dict(section="change", a="ZZ ITEM NEWEST 001", b="WRONG", c="ZZ SALT NEWEST 00"), marg, {s for s in marg.values()})
    ck("_marg_says now reads 'done' for the ticked item from the fresh list", say[0] == "done", str(say))
    r = cl.post("/finance/purchase/api/salts", json=body, headers={"X-Finance-Marg": "ZZWRONG"})
    ck("the real door refuses a wrong token with 401", r.status_code == 401)

# ------------------------------------------------------------------ 7. compile + hygiene
print("7. hygiene")
import py_compile                                             # noqa: E402
try:
    py_compile.compile(os.path.join(HERE, "salts_refresh.py"), doraise=True)
    ck("salts_refresh.py py_compiles", True)
except py_compile.PyCompileError as e:
    ck("salts_refresh.py py_compiles", False, str(e))
src_txt = open(os.path.join(HERE, "salts_refresh.py"), encoding="utf-8").read()
ck("salts_refresh.py never prints the token (no print of tok / token variable)", "print(" not in "".join(l for l in src_txt.splitlines() if "tok" in l and "print" in l and "no FINANCE_MARG_TOKEN" not in l))
ck("no leftover state.tmp", not glob.glob(os.path.join(os.path.dirname(STATE), "*.tmp")))

srv.shutdown()
print("\n%d passed, %d failed" % (PASS, FAIL))
print("RESULT: %s" % ("PASS" if FAIL == 0 else "FAILED"))
sys.exit(0 if FAIL == 0 else 1)
