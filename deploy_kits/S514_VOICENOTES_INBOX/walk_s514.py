#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s514.py -- S514_VOICENOTES_INBOX: Voicenotes' to-do lists reach the owner's task box -- walked.

  usage: walk_s514.py --kit <kit folder> --finance <folder holding finance_app.py (at S513's pin) and its sibling files>
         [--negative]   walk the OLD files as if they were the new ones: must go RED

The finance app's CODE is copied to a scratch folder twice ('old' as it is, 'new' with make_s514.py's edits and
voicenotes_inbox.py beside it), each with an EMPTY database made from the app's own schema, a made-up owner and a
made-up staff login, and a made-up key file. Each is asked the same things through the Flask test client: Voicenotes'
door with no key, a wrong key and the right one; a to-do list in the shapes Voicenotes may send (Markdown, HTML, a list
of objects, a list of strings); the same list again; a summary; the owner's inbox, a staff login's refusal, and the
two marks. Every other row of the health page must be the old file's. Nothing live is opened.  Last: WALK_S514 GREEN|RED.
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

FROM = {"finance_app.py": "ec5b3ab170ff37c63ac98f6f1f11ad09", "aaj_panel.html": "898c42e14b142e06f2800d83aaaf01ca"}
TO = {"finance_app.py": "0d713b14570384e0de07ac93a3b113db", "aaj_panel.html": "36bd57bcda586f18183aec54c537e2e6"}
MARK = "@@S514JSON@@ "
OK, FAIL = [], []


def check(name, cond, note=""):
    (OK if cond else FAIL).append(name)
    if not cond:
        print("  FAIL: %s%s" % (name, ("  [%s]" % str(note)[:700]) if note else ""))


def md5(path):
    with open(path, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def child():
    sys.path.insert(0, os.getcwd())
    import finance_app as fa
    root = os.environ["S514_ROOT"]
    if not os.path.realpath(fa.DB_PATH).startswith(os.path.realpath(root) + os.sep):
        print(MARK + json.dumps({"abort": "the finance database is not the scratch one"}))
        return
    con = sqlite3.connect(fa.DB_PATH)
    con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES ('packs','wowner','checker',1)")
    con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES ('medical','wowner','checker',1)")
    con.execute("INSERT INTO unit_role (unit, username, role, active) VALUES ('medical','wstaff','maker',1)")
    con.commit()
    con.close()
    c = fa.app.test_client()
    OWN, STAFF = {"X-Clinic-User": "wowner"}, {"X-Clinic-User": "wstaff"}
    kf = os.environ["VOICENOTES_KEY_FILE"]
    key = "walkvn" + os.urandom(10).hex()
    door = "/finance/api/voicenotes-push"
    O = {}

    def post(q, body, raw=None):
        if raw is not None:
            r = c.post(door + q, data=raw, content_type="application/json")
        else:
            r = c.post(door + q, json=body)
        return [r.status_code, r.get_json(silent=True)]

    def rows():
        k = sqlite3.connect(fa.DB_PATH)
        try:
            return [list(x) for x in k.execute("SELECT text, state, title FROM vn_inbox ORDER BY id")]
        except sqlite3.OperationalError:
            return None
        finally:
            k.close()

    todo = {"event": "creation.todo", "timestamp": "2026-10-10T17:40:00+00:00",
            "data": {"id": "n1", "type": "todo", "title": "Clinic morning",
                     "content": "- [ ] Waiting room ka AC service karwaiye\n- [ ] Call the X-ray engineer at 10.30 baje\n"
                                "1. Order 2.5 kg plaster\n\n* [x] Waiting room ka AC service karwaiye\n# To-do list"}}
    O["no_key_file"] = post("?key=anything", todo)
    with open(kf, "w") as fh:
        fh.write(key + "\n")
    O["no_key"] = post("", todo)
    O["wrong_key"] = post("?key=" + key[:-1] + "x", todo)
    O["rows_after_refusals"] = rows()
    O["good"] = post("?key=" + key, todo)
    O["again"] = post("?key=" + key, todo)
    O["html"] = post("?key=" + key, {"event": "creation.todo", "data": {"id": "n2", "type": "todo", "title": "",
                                     "content": "<ul><li>Buy <b>printer</b> paper</li><li>Pay the &amp; electricity bill</li></ul>"}})
    O["objects"] = post("?key=" + key, {"event": "todo.created", "data": {"id": "n3", "todos": [{"text": "Renew fire extinguisher"}, {"text": ""}, {"title": "Ask Bhati for the challan"}]}})
    O["strings"] = post("?key=" + key, {"event": "creation.todo_list", "data": {"id": "n4", "content": ["Line one", "  - Line two  ", "Line\x07 three"]}})
    O["summary"] = post("?key=" + key, {"event": "creation.summary", "data": {"id": "n5", "type": "summary", "content": "- not a task"}})
    O["note"] = post("?key=" + key, {"event": "recording.created", "data": {"id": "n6", "title": "x", "transcript": "- not a task"}})
    O["not_json"] = post("?key=" + key, None, raw="this is not json")
    O["many"] = post("?key=" + key, {"event": "creation.todo", "data": {"id": "n7", "content": "\n".join("- item %d" % i for i in range(60))}})
    O["rows"] = rows()
    # the key never stored
    k = sqlite3.connect(fa.DB_PATH)
    try:
        dump = "\n".join(str(x) for t in ("vn_inbox", "vn_seen") for x in k.execute("SELECT * FROM %s" % t))
    except sqlite3.OperationalError:
        dump = ""
    k.close()
    O["key_stored"] = key in dump
    # the owner's inbox
    r = c.get("/finance/aaj/api/vn")
    O["vn_no_login"] = r.status_code
    r = c.get("/finance/aaj/api/vn", headers=STAFF)
    O["vn_staff"] = r.status_code
    r = c.get("/finance/aaj/api/vn", headers=OWN)
    j = r.get_json(silent=True) or {}
    O["vn_owner"] = [r.status_code, len(j.get("items") or []), (j.get("url") or "").endswith("?key=" + key),
                     (j.get("url") or "").startswith("https://followup.dr-manoj.in/finance/api/voicenotes-push"),
                     [s.get("event") for s in (j.get("seen") or [])], r.headers.get("Cache-Control")]
    ids = [it["id"] for it in (j.get("items") or [])]
    r = c.post("/finance/aaj/api/vn", headers=OWN, json={"op": "used", "ids": ids[:2]})
    j2 = r.get_json(silent=True) or {}
    O["used"] = [r.status_code, len(j2.get("items") or [])]
    r = c.post("/finance/aaj/api/vn", headers=OWN, json={"op": "drop", "ids": ids[2:3] + ["x", True, 99999]})
    j3 = r.get_json(silent=True) or {}
    O["drop"] = [r.status_code, len(j3.get("items") or [])]
    O["bad_op"] = c.post("/finance/aaj/api/vn", headers=OWN, json={"op": "delete", "ids": ids}).status_code
    O["staff_post"] = c.post("/finance/aaj/api/vn", headers=STAFF, json={"op": "drop", "ids": ids}).status_code
    O["states"] = [x[1] for x in (rows() or [])][:4]
    # no task was made by any of this
    k = sqlite3.connect(fa.DB_PATH)
    try:
        O["tasks"] = k.execute("SELECT COUNT(*) FROM aaj_task").fetchone()[0]
    except sqlite3.OperationalError:
        O["tasks"] = 0
    k.close()
    # the panel, as the owner
    r = c.get("/finance/aaj", headers=OWN)
    page = r.get_data(as_text=True)
    O["panel"] = [r.status_code, 'id="vnbox"' in page, 'id="vnurl"' in page, "To-Do List Creation" in page, key in page]
    # the health page: every row
    r = c.get("/finance/api/health", headers=OWN)
    hj = r.get_json(silent=True) or {}
    O["health"] = sorted((x["key"], x["state"], x["detail"]) for x in (hj.get("checks") or []) if x.get("key") not in ("nevfired", "renewals"))
    print(MARK + json.dumps(O))


def make_app(src, dst):
    os.makedirs(dst)
    for pat in ("*.py", "*.sql", "*.html", "*.json"):
        for f in glob.glob(os.path.join(src, pat)):
            if os.path.isfile(f) and os.path.getsize(f) < 4 * 1024 * 1024 and not f.endswith("renewals_state.json"):
                shutil.copy2(f, dst)
    if os.path.isdir(os.path.join(src, "finance_ui")):
        shutil.copytree(os.path.join(src, "finance_ui"), os.path.join(dst, "finance_ui"))
    con = sqlite3.connect(os.path.join(dst, "finance.db"))
    for f in ("finance_schema.sql", "finance_migration_S182_clinic.sql"):
        with open(os.path.join(dst, f), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    con.close()


def run(root, tag, appdir):
    base = os.path.join(root, "run_" + tag)
    tmp = os.path.join(base, "tmp")
    os.makedirs(tmp)
    e = dict(os.environ)
    # every token and key here is made up afresh at every run -- never the box's, and none is written in this file
    e.update({"S514_ROOT": base, "FINANCE_DB": os.path.join(base, "finance.db"), "FINANCE_SCAN_DIR": os.path.join(base, "scans"),
              "TMPDIR": tmp, "TEMP": tmp, "TMP": tmp, "FINANCE_ALLOW_HEADER_AUTH": "1",
              "FINANCE_DEV_USER": "", "FINANCE_DEV_ROLE": "", "FINANCE_CRON_TOKEN": "walk-" + os.urandom(12).hex(),
              "LEDGER_DIR": os.path.join(base, "ledger"), "FINANCE_LEDGER_JSONL": os.path.join(base, "ledger", "ledger.jsonl"),
              "FINANCE_RENEWALS_STATE": os.path.join(base, "renewals.json"), "FINANCE_BACKUP_DIR": os.path.join(root, "backups_shared"),
              "ASSETS_DB": os.path.join(base, "no_such_assets.db"), "VOICENOTES_KEY_FILE": os.path.join(base, "voicenotes.key"),
              "FINANCE_AUTOAPPLY_OFF": os.path.join(base, "AUTOAPPLY_OFF_absent"), "PYTHONDONTWRITEBYTECODE": "1"})
    shutil.move(os.path.join(appdir, "finance.db"), os.path.join(base, "finance.db"))
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child"], cwd=appdir, env=e,
                       capture_output=True, text=True, timeout=400)
    got = None
    for line in p.stdout.splitlines():
        if line.startswith(MARK):
            got = json.loads(line[len(MARK):])
    return p, got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--finance", required=True)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--negative", action="store_true")
    a = ap.parse_args()
    root = tempfile.mkdtemp(prefix="s514_walk_")
    try:
        walk(a, root)
    except Exception as ex:                                        # a walk that breaks is a RED walk, never a traceback
        check("the walk itself ran to its end", False, "%s: %s" % (type(ex).__name__, ex))
    finally:
        if not a.keep:
            shutil.rmtree(root, ignore_errors=True)
        else:
            print("  kept: %s" % root)
    print("  %d checks, %d failed" % (len(OK) + len(FAIL), len(FAIL)))
    print("WALK_S514 %s" % ("GREEN  %d checks" % len(OK) if not FAIL else "RED"))
    return 0 if not FAIL else 1


def walk(a, root):
    fin, kit = os.path.abspath(a.finance), os.path.abspath(a.kit)
    old, new = os.path.join(root, "old"), os.path.join(root, "new")
    make_app(fin, old)
    for f in FROM:
        check("0.1 the unpatched %s is the file this kit was built from (%s)" % (f, FROM[f][:8]), md5(os.path.join(old, f)) == FROM[f], md5(os.path.join(old, f)))
    if FAIL:
        return
    check("0.2 voicenotes_inbox.py is not on the box yet", not os.path.exists(os.path.join(fin, "voicenotes_inbox.py")))
    shutil.copytree(old, new)
    if not a.negative:
        p = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s514.py"), new], capture_output=True, text=True)
        shutil.copy2(os.path.join(kit, "voicenotes_inbox.py"), new)
        check("0.3 the edits apply and give the predicted bytes",
              p.returncode == 0 and all(md5(os.path.join(new, f)) == TO[f] for f in TO), p.stdout + p.stderr[-300:])
        p2 = subprocess.run([sys.executable, "-B", os.path.join(kit, "make_s514.py"), new], capture_output=True, text=True)
        check("0.4 applied twice: refused, both files left byte for byte", p2.returncode != 0 and all(md5(os.path.join(new, f)) == TO[f] for f in TO))
    R = {}
    for tag, d in (("old", old), ("new", new)):
        p, R[tag] = run(root, tag, d)
        check("0.5 the %s app answered every question" % tag, bool(R[tag]) and "abort" not in R[tag], (R[tag] or {}).get("abort") or p.stderr[-700:])
    if not (R.get("old") and R.get("new")):
        return
    o, n = R["old"], R["new"]

    # ---- 1 · the door
    check("1.1 SHOWN on the old file: there is no door -- a post is refused by the front gate (no table is made)",
          o["good"][0] in (401, 403, 404) and o["rows"] is None, (o["good"], o["rows"]))
    check("1.2 no key file on the box: refused 401, nothing stored", n["no_key_file"][0] == 401)
    check("1.3 no key, or a key one character wrong: refused 401, nothing stored",
          n["no_key"][0] == 401 and n["wrong_key"][0] == 401 and not n["rows_after_refusals"], (n["no_key"], n["wrong_key"], n["rows_after_refusals"]))
    rws = n["rows"] or []
    first = [r[0] for r in rws[:3]]
    check("1.4 a Markdown to-do list: three lines kept, tick-boxes and list marks taken off, '10.30 baje' and '2.5 kg' as written, "
          "the repeated line and the heading dropped",
          n["good"] == [200, {"ok": True, "kept": 3, "lines": 3}]
          and first == ["Waiting room ka AC service karwaiye", "Call the X-ray engineer at 10.30 baje", "Order 2.5 kg plaster"]
          and rws[0][2] == "Clinic morning", (n["good"], first))
    check("1.5 the same list sent again (Voicenotes retrying): answered 200, stored once", n["again"][0] == 200 and n["again"][1]["kept"] == 0, n["again"])
    texts = [r[0] for r in rws]
    check("1.6 an HTML list: two lines, the markup gone, '&' read as '&'",
          n["html"][1].get("kept") == 2 and "Buy printer paper" in texts and "Pay the & electricity bill" in texts, (n["html"], texts[3:6]))
    check("1.7 a list of objects: the two with words kept, the empty one dropped",
          n["objects"][1].get("kept") == 2 and "Renew fire extinguisher" in texts and "Ask Bhati for the challan" in texts, n["objects"])
    check("1.8 a list of strings: three lines, a control character made a space",
          n["strings"][1].get("kept") == 3 and "Line two" in texts and "Line  three".replace("  ", " ") in texts, (n["strings"], texts))
    check("1.9 a summary and a recorded note: answered 200 (no retry), nothing stored",
          n["summary"] == [200, {"ok": True, "kept": 0, "ignored": "not a to-do list"}] and n["note"][0] == 200 and n["note"][1]["kept"] == 0,
          (n["summary"], n["note"]))
    check("1.10 a post that is not JSON: 400, nothing stored", n["not_json"][0] == 400)
    check("1.11 a list of 60 lines: 40 kept (the cap)", n["many"][1].get("kept") == 40 and n["many"][1].get("lines") == 40, n["many"])
    check("1.12 the key is stored nowhere in the two tables", n["key_stored"] is False)

    # ---- 2 · the owner's inbox
    v = n["vn_owner"]
    check("2.1 the owner's inbox: 50 lines waiting, the address to paste ends in the key, the last posts named, not cached",
          v[0] == 200 and v[1] == 50 and v[2] is True and v[3] is True and v[4][:2] == ["creation.todo", ""] and v[5] == "no-store", v)
    check("2.2 not signed in: 401 · a staff login: 403 (asked and posting)",
          n["vn_no_login"] in (401, 302) and n["vn_staff"] == 403 and n["staff_post"] == 403, (n["vn_no_login"], n["vn_staff"], n["staff_post"]))
    check("2.3 two put in the box, then one removed (ids that are not numbers ignored): 48, then 47 waiting; an unknown op is 400",
          n["used"] == [200, 48] and n["drop"] == [200, 47] and n["bad_op"] == 400 and n["states"] == ["used", "used", "drop", "new"],
          (n["used"], n["drop"], n["bad_op"], n["states"]))
    check("2.4 no task was made by any of it -- a line becomes a task only through Give", n["tasks"] == 0, n["tasks"])
    check("2.5 the owner's panel carries the Voicenotes box and the one-time set-up; the key is not in the page itself (it is fetched)",
          n["panel"] == [200, True, True, True, False] and o["panel"][1] is False, (n["panel"], o["panel"]))

    # ---- 3 · nothing else moved
    hn = [x for x in n["health"] if x[0] != "mounts"]
    ho = [x for x in o["health"] if x[0] != "mounts"]
    check("3.1 every other row of the health page is the old file's", hn == ho, [x for x in hn if x not in ho][:3])
    mn = [x for x in n["health"] if x[0] == "mounts"]
    check("3.2 the parts-loaded row counts the new part: 'all 30 parts loaded'", mn and mn[0][1] == "ok" and mn[0][2] == "all 30 parts loaded", mn)
    for f in FROM:
        check("3.3 nothing in the box's finance folder was written by this walk: %s" % f, md5(os.path.join(fin, f)) == FROM[f])


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--child":
        child()
    else:
        sys.exit(main())
