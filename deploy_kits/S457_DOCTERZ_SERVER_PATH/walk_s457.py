#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s457.py -- kit S457_DOCTERZ_SERVER_PATH. The two export doors of the kit's reception_door.py and the owner's
PC's docterz_fetch.py, end to end over real HTTP, on made-up exports in a scratch folder with a throwaway key.
Nothing live is read or written; no real export is opened. Last line:  WALK_S457 GREEN <n> checks  or  WALK_S457 RED.

    python3 -B walk_s457.py --door built/reception_door.py --fetch pc/docterz_fetch.py --finance /root/finance
"""
import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request

PASS, FAIL = [], []


def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print("%s  %s%s" % ("  ok  " if cond else "  FAIL", name, ("  -- " + str(detail)[:300]) if (detail and not cond) else ""))


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def consult(day, n, extra=""):
    rows = ["Consultation Date,Patient UID,Mode Of Payment,Bill Amount,Amount collected"]
    rows += ["%s,WALK%04d%s,Cash,500,500" % (day, i, extra) for i in range(n)]
    return ("\r\n".join(rows) + "\r\n").encode("utf-8")


def follow(day, n):
    rows = ["Appointment ID,Followup Date,Mobile No,Status"]
    rows += ["A%05d,%s,NOMOBILE,due" % (i, day) for i in range(n)]
    return ("\r\n".join(rows) + "\r\n").encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--door", required=True)
    ap.add_argument("--fetch", required=True)
    ap.add_argument("--finance", required=True, help="the folder that holds the server's docterz_pickup.py")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="s457_walk_")
    try:
        return walk(a, tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def walk(a, tmp):
    os.environ["DOCTERZ_EXPORT_STORE"] = os.path.join(tmp, "store")
    os.environ["RECEPTION_JOB_KEYS"] = os.path.join(tmp, "job_keys.txt")
    os.environ["RECEPTION_JOB_DIR"] = os.path.join(tmp, "jobs")
    os.environ["RECEPTION_BEAT"] = os.path.join(tmp, "beat.json")
    os.environ["RECEPTION_KEYS"] = os.path.join(tmp, "keys.txt")
    sys.path.insert(0, os.path.abspath(a.finance))
    import docterz_pickup as DP                                  # the server's reader, read-only use of its code
    check("the reader keeps its bytes in the scratch store, not the live one", os.path.realpath(DP.STORE).startswith(os.path.realpath(tmp)))
    if FAIL:
        print("WALK_S457 RED")
        return 1
    rd = load(a.door, "reception_door_s457")
    F = load(a.fetch, "docterz_fetch_s457")
    from flask import Flask
    from werkzeug.serving import make_server
    dbf = os.path.join(tmp, "scratch.db")

    def db():
        con = sqlite3.connect(dbf, timeout=10)
        con.row_factory = sqlite3.Row
        return con
    app = Flask("walk_s457")
    rd.init(app, db)

    secret, other = hashlib.sha256(b"walk-s457-key").digest(), hashlib.sha256(b"someone-else").digest()
    with open(os.environ["RECEPTION_JOB_KEYS"], "w") as fh:
        fh.write("%s walk-manojz\n" % F.ed_public(secret).hex())

    # ---- made-up exports, taken through the reader's own take() ----
    con = db()
    DP.ensure(con)
    c_old, c_new = consult("01-10-2026", 3), consult("01-10-2026", 5)
    c_few = consult("01-10-2026", 2, "x")
    f_cur = follow("02-10-2026", 4)
    c_anc = consult("20-09-2026", 6)
    def take(tag, raw, mt):
        return DP.take(con, {"id": "walk:" + tag, "name": tag + ".csv", "modifiedTime": mt}, raw)
    take("c_old", c_old, "2026-10-01T15:00:00.000Z")
    take("c_new", c_new, "2026-10-01T15:30:00.000Z")
    take("c_few", c_few, "2026-10-01T15:40:00.000Z")
    take("f_cur", f_cur, "2026-10-01T15:31:00.000Z")
    take("c_anc", c_anc, "2026-09-20T15:00:00.000Z")
    m_old, m_new, m_few, m_fol, m_anc = (hashlib.md5(x).hexdigest() for x in (c_old, c_new, c_few, f_cur, c_anc))
    con.execute("UPDATE docterz_export SET taken_at=? WHERE md5=?", ((DP.now() - __import__("datetime").timedelta(days=10)).isoformat(sep=" "), m_anc))
    con.commit()
    st = {r["md5"]: r["status"] for r in con.execute("SELECT md5, status FROM docterz_export")}
    check("the made-up exports stand as the reader files them: one current per kind and day, the older superseded, the smaller quarantined",
          st.get(m_new) == "current" and st.get(m_fol) == "current" and st.get(m_old) == "superseded" and st.get(m_few) == "quarantined" and st.get(m_anc) == "current", st)

    srv = make_server("127.0.0.1", 0, app, threaded=True)
    base = "http://127.0.0.1:%d" % srv.server_port
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    def post(path, obj, raw=None):
        data = raw if raw is not None else json.dumps(obj).encode()
        req = urllib.request.Request(base + path, data=data, method="POST", headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, r.read(), dict(r.headers.items())
        except urllib.error.HTTPError as ex:
            return ex.code, ex.read(), {}

    def status(body):
        try:
            return json.loads(body.decode()).get("status")
        except Exception:                                      # noqa: BLE001
            return None

    LCTX = getattr(rd, "EXPORT_LIST_CONTEXT", b"clinic-docterz-export-list-v1\n")
    GCTX = getattr(rd, "EXPORT_GET_CONTEXT", b"clinic-docterz-export-get-v1\n")
    check("the door and the fetcher sign the same words", LCTX == F.LIST_CONTEXT and GCTX == F.GET_CONTEXT and hasattr(rd, "EXPORT_LIST_CONTEXT"))

    def lsig(key=secret, ts=None, ctx=None):
        ts = ts or str(int(time.time()))
        return {"ts": ts, "sig": F.ed_sign(key, (ctx or LCTX) + ts.encode()).hex()}

    def gsig(md5, key=secret, ts=None, ctx=None, signed_md5=None):
        ts = ts or str(int(time.time()))
        return {"md5": md5, "ts": ts, "sig": F.ed_sign(key, (ctx or GCTX) + (signed_md5 or md5).encode() + b"\n" + ts.encode()).hex()}
    LIST, GET = "/finance/api/reception/exports/list", "/finance/api/reception/exports/get"

    # ---- 1. the list door ----
    c, b, _ = post(LIST, {})
    check("list: no signature -> 401 NOT_YOU", c == 401 and status(b) == "NOT_YOU", (c, b[:120]))
    c, b, _ = post(LIST, None, raw=b"not json")
    check("list: not JSON -> 400", c == 400, (c, b[:120]))
    c, b, _ = post(LIST, lsig(key=other))
    check("list: a signature by a key this server does not hold -> 401", c == 401 and status(b) == "NOT_YOU", (c, b[:120]))
    c, b, _ = post(LIST, lsig(ctx=rd.JOB_READ_CONTEXT + b"20261003T100000_x.py\n"))
    check("list: a job's read token does not open it", c == 401, (c, b[:120]))
    c, b, _ = post(LIST, lsig(ctx=GCTX))
    check("list: a signature made for the other door does not open it", c == 401, (c, b[:120]))
    c, b, _ = post(LIST, lsig(ts=str(int(time.time()) - 1200)))
    check("list: a signature 20 minutes old -> 401 CLOCK", c == 401 and status(b) == "CLOCK", (c, b[:120]))
    c, b, _ = post(LIST, lsig())
    j = json.loads(b.decode()) if c == 200 else {}
    got = {e["md5"]: e for e in j.get("exports", [])}
    check("list: a good signature -> the CURRENT exports of the last 3 days, and only those", c == 200 and set(got) == {m_new, m_fol}, (c, sorted(got)))
    check("list: counts and dates only -- seven plain fields, no name, no row", all(sorted(e) == ["bytes", "day", "kind", "md5", "mtime", "rows", "taken_at"] for e in got.values())
          and b"WALK0" not in b and b"NOMOBILE" not in b, b[:300])
    check("list: kind, day, rows and size are the reader's own", got.get(m_new, {}).get("kind") == "consultation" and got[m_new]["day"] == "2026-10-01" and got[m_new]["rows"] == 5
          and got[m_new]["bytes"] == len(c_new) and got.get(m_fol, {}).get("kind") == "followup", got)
    c, b, _ = post(LIST, dict(lsig(), days=45))
    check("list: days=45 reaches the older one; days is capped", c == 200 and m_anc in {e["md5"] for e in json.loads(b.decode())["exports"]}
          and json.loads(post(LIST, dict(lsig(), days=9999))[1].decode())["days"] == 45, b[:200])

    # ---- 2. the get door ----
    c, b, h = post(GET, gsig(m_new))
    check("get: a good signature -> the export's bytes exactly", c == 200 and b == c_new and h.get("X-Export-Kind") == "consultation" and h.get("X-Export-Day") == "2026-10-01", (c, len(b)))
    c, b, _ = post(GET, {"md5": m_new})
    check("get: no signature -> 401", c == 401, (c, b[:120]))
    c, b, _ = post(GET, gsig(m_new, signed_md5=m_fol))
    check("get: a signature made for another export does not open this one", c == 401, (c, b[:120]))
    c, b, _ = post(GET, gsig(m_new, ctx=LCTX))
    check("get: the list door's signature does not open it", c == 401, (c, b[:120]))
    c, b, _ = post(GET, gsig(m_new, key=other))
    check("get: another key -> 401", c == 401, (c, b[:120]))
    c, b, _ = post(GET, gsig(m_new, ts=str(int(time.time()) + 1200)))
    check("get: a signature dated 20 minutes ahead -> 401 CLOCK", c == 401 and status(b) == "CLOCK", (c, b[:120]))
    c, b, _ = post(GET, gsig("0" * 32))
    check("get: an md5 this server does not hold -> 404, nothing sent", c == 404 and status(b) == "NOT_HERE", (c, b[:120]))
    c1, b1, _ = post(GET, gsig(m_old))
    c2, b2, _ = post(GET, gsig(m_few))
    check("get: a superseded export and a quarantined one are not handed out", c1 == 404 and c2 == 404, (c1, c2))
    c, b, _ = post(GET, gsig("../../etc/passwd"))
    check("get: something that is not an md5 -> refused", c == 401, (c, b[:120]))
    log = open(os.path.join(os.environ["RECEPTION_JOB_DIR"], "log.txt")).read()
    check("the log says kind, day and size of what was sent -- never a row", "EXPORT SENT (consultation for 2026-10-01, %d bytes)" % len(c_new) in log and "WALK0" not in log, log[-200:])
    stored = con.execute("SELECT stored FROM docterz_export WHERE md5=?", (m_fol,)).fetchone()["stored"]
    keep = open(stored, "rb").read()
    open(stored, "wb").write(keep + b"tampered\r\n")
    c, b, _ = post(GET, gsig(m_fol))
    check("get: a kept copy that is no longer the bytes taken -> 500, nothing sent", c == 500 and status(b) == "NOT_WHOLE" and b"A0000" not in b, (c, b[:120]))
    open(stored, "wb").write(keep)
    outside = os.path.join(tmp, "outside.csv")
    open(outside, "wb").write(f_cur)
    con.execute("UPDATE docterz_export SET stored=? WHERE md5=?", (outside, m_fol)); con.commit()
    c, b, _ = post(GET, gsig(m_fol))
    c3, b3, _ = post(LIST, lsig())
    check("a row that points outside the reader's store is neither listed nor sent", c == 404 and m_fol not in b3.decode(), (c, b3[:200]))
    con.execute("UPDATE docterz_export SET stored=? WHERE md5=?", (stored, m_fol)); con.commit()
    try:
        urllib.request.urlopen(base + GET, timeout=10)
        code = 200
    except urllib.error.HTTPError as ex:
        code = ex.code
    check("a plain GET is not a way in", code == 405, code)
    os.rename(os.environ["RECEPTION_JOB_KEYS"], os.environ["RECEPTION_JOB_KEYS"] + ".away")
    c, b, _ = post(LIST, lsig())
    check("no key on the server -> the doors are shut (503)", c == 503 and status(b) == "NO_KEY", (c, b[:120]))
    os.rename(os.environ["RECEPTION_JOB_KEYS"] + ".away", os.environ["RECEPTION_JOB_KEYS"])
    c, b, _ = post("/finance/api/reception/heartbeat", {})
    check("the heartbeat door still refuses an unsigned heartbeat in its own words", status(b) in ("NOT_YOU", "NO_KEY"), (c, b[:120]))

    # ---- 3. the owner's PC's fetcher, against these doors ----
    dl, arc = os.path.join(tmp, "Downloads"), os.path.join(tmp, "Downloads", "DocterzArchive")
    os.makedirs(arc)
    keyf = os.path.join(tmp, "key.txt")
    open(keyf, "w").write(secret.hex() + "\n")
    F.SERVER, F.KEY_FILE, F.DOWNLOADS, F.ARCHIVE, F.ALL_OFF = base, keyf, dl, arc, os.path.join(tmp, "ALL_OFF.txt")
    asked = []
    real_post = F.http_post

    def counting(path, obj, timeout=20):
        asked.append(path)
        return real_post(path, obj, timeout)
    open(os.path.join(dl, "consultation_report (3).csv"), "wb").write(c_new)      # reception's file, already copied by hand
    open(os.path.join(dl, "notes.csv"), "wb").write(f_cur)                         # same bytes, but not a Docterz name
    line = F.one_pass(dry=True, now=True, post=counting)
    check("dry run: asks, compares, fetches and writes nothing", "DRY RUN" in open(F.last_file()).read() and "1 already here, 1 would be fetched" in open(F.last_file()).read()
          and sorted(os.listdir(dl)) == ["DocterzArchive", "consultation_report (3).csv", "notes.csv"] and not os.path.exists(F.state_file()) and asked == [LIST], (asked, os.listdir(dl)))
    del asked[:]
    line = F.one_pass(now=True, post=counting)
    name = "followup_logs_2026-10-01_reception_%s.csv" % m_fol[:6]
    got_p = os.path.join(dl, name)
    check("a real pass: the follow-up log is fetched into Downloads, byte for byte; the report already there is not fetched again",
          os.path.isfile(got_p) and open(got_p, "rb").read() == f_cur and asked == [LIST, GET] and "1 already here, 1 fetched now" in line, (asked, line, os.listdir(dl)))
    check("...with the time reception downloaded it as the file's own time", abs(os.path.getmtime(got_p) - F.mtime_of("2026-10-01T15:31:00.000Z")) < 2, os.path.getmtime(got_p))
    check("...no half-written file is left behind", not [n for n in os.listdir(dl) if n.endswith(".part")], os.listdir(dl))
    stt = json.load(open(F.state_file()))
    check("...and both are remembered", set(stt["have"]) == {m_new, m_fol} and stt["have"][m_new]["how"] == "already in Downloads" and stt["have"][m_fol]["how"] == "fetched", stt)
    del asked[:]
    line = F.one_pass(post=counting)
    check("five minutes later: not due, the server is not asked", line == "not due" and asked == [], (line, asked))
    line = F.one_pass(now=True, post=counting)
    check("the next question: nothing new, nothing fetched twice", asked == [LIST] and "2 already here, 0 fetched now" in line and len(os.listdir(dl)) == 4, (asked, line))
    nlog = len(open(F.log_file()).read().splitlines())
    F.one_pass(now=True, post=counting); F.one_pass(now=True, post=counting)
    check("an idle evening is one line in the log, not one per pass", len(open(F.log_file()).read().splitlines()) == nlog)
    logt = open(F.log_file()).read() + open(F.last_file()).read()
    check("the fetcher's log carries kinds, days, sizes and md5s -- never a row", "WALK0" not in logt and "NOMOBILE" not in logt and "A0000" not in logt, logt[-300:])
    # a new export arrives on the server
    f_new = follow("03-10-2026", 6)
    take("f_new", f_new, "2026-10-02T15:33:00.000Z")
    del asked[:]
    line = F.one_pass(now=True, post=counting)
    check("a new export on the server is fetched at the next question", "1 fetched now" in line and
          open(os.path.join(dl, "followup_logs_2026-10-02_reception_%s.csv" % hashlib.md5(f_new).hexdigest()[:6]), "rb").read() == f_new, (line, os.listdir(dl)))
    # the switch
    open(os.path.join(arc, "_server_fetch_OFF.txt"), "w").write("off for the walk")
    del asked[:]
    line = F.one_pass(now=True, post=counting)
    check("the switch file: nothing asked, and it says OFF", asked == [] and "switched off" in line, (asked, line))
    open(os.path.join(arc, "_server_fetch_OFF.txt"), "w").write("ON")
    F.one_pass(now=True, post=counting)
    check("a switch file that says ON counts as absent", asked == [LIST], asked)
    os.remove(os.path.join(arc, "_server_fetch_OFF.txt"))
    # bad bytes
    f_bad = follow("04-10-2026", 7)
    take("f_bad", f_bad, "2026-10-03T15:33:00.000Z")

    def lying(path, obj, timeout=20):
        if path == GET:
            return 200, b"not the export", {}
        return real_post(path, obj, timeout)
    before = sorted(os.listdir(dl))
    line = F.one_pass(now=True, post=lying)
    check("bytes that are not the export are refused: no file written, said in the log", sorted(os.listdir(dl)) == before and "NOT FETCHED" in open(F.log_file()).read()
          and hashlib.md5(f_bad).hexdigest() not in json.load(open(F.state_file()))["have"], (line, os.listdir(dl)))
    line = F.one_pass(now=True)
    check("...and fetched properly at the next pass", "1 fetched now" in line, line)
    # wrong key, then no server
    open(keyf, "w").write(other.hex() + "\n")
    line = F.one_pass(now=True)
    check("a key the server does not know: said, nothing raised", "NOT ANSWERED" in line or "did not answer" in line, line)
    open(keyf, "w").write("not a key\n")
    line = F.one_pass(now=True)
    check("no readable key: nothing asked, said", "signing key was not read" in line, line)
    open(keyf, "w").write(secret.hex() + "\n")
    srv.shutdown()
    line = F.one_pass(now=True)
    check("the server gone altogether: nothing raised, one line", "did not answer" in line and "no connection" in line, line)
    rc = F.main(["--now"])
    check("the command itself always ends 0, so the pickup after it always runs", rc == 0, rc)

    print("%d passed, %d failed" % (len(PASS), len(FAIL)))
    for f in FAIL:
        print("   FAILED: " + f)
    print("WALK_S457 GREEN %d checks" % len(PASS) if not FAIL else "WALK_S457 RED")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
