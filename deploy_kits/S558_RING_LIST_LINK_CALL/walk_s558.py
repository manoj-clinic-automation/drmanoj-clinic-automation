#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s558.py -- the walk of S558_RING_LIST_LINK_CALL (D726, F-896): link a different number, remember it, the IVR call.
It writes ONLY under its own scratch folder: never to --kit, --portal, --db or --finance-db.

    python3 -B walk_s558.py --kit <kit folder> --portal <the portal's code folder as it is live>
            [--control]              the SAME walk on the LIVE files -- the negative control; it must end RED
            [--s497 DIR]             S497's kit folder: its own walk is run again on this kit's programs (part H)
            [--db ring_outcomes.db --finance-db finance.db]   a COPY of the real stores, counts only (part R)

THE REAL portal.py (live) with the kit's ring_outcome.py and ring_common.py is loaded from a scratch copy and driven through
Flask's test client. Sign-in runs on the walk's OWN user store and its OWN random signing secret (the live secret, the live
password store and portal_config.py are never read); finance.db is a made-up one; the fingerprint module is a walk-only
stand-in with a random salt; the call key is the walk's own random one in its own .env; the HTTP post to call_api.py is
answered by a stand-in (nothing leaves the machine). EVERY mobile number is made at run time from random digits (F-185).
The made-up day is in March 2027, far from any real row.

PART S  the files: which functions changed against the live bytes; THE RULE and the tap byte for byte.
PART G  installed OFF: nothing new renders for anyone, the acts are refused, only the owner sees his two toggles (OFF).
PART A  (a) the suggestions on a new number's line: who is in, who is not, newest first.
PART E  (e) the search: a clinic ID exact, a part of a name.
PART B  (b) the link: the line is Aa gaye 'doosre number se'; appt_link and appt_event written; a second link refused.
PART D  (d) lookup_caller: the linked patient, 'linked'; the next call offers the known list; no fingerprint still reads it.
PART C  (c) the undo: staff the same day; refused the next day; the owner any day.
PART F  (f) the IVR call: accepted, refused (its reason), no agent (greyed, refused), the key and the stored number reach
        the stand-in, never the page; one call per line per 60 seconds.
PART O  (g) both switches turned OFF again: nothing renders, the acts are refused, lookup_caller reads no link.
PART H  (h) THE RULE's own walk (S497's walk_s497.py) on this kit's programs: only its two file-identity checks may be red.
PART R  (with --db) copies of the real stores: the table is made, nothing lost, the list reads -- counts only.
Last line:  WALK_S558 GREEN <n> checks   or   WALK_S558 RED <n> failed of <m>
"""
import argparse
import ast
import contextlib
import hashlib
import html as htmllib
import importlib.util
import io
import json
import os
import re
import secrets
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import traceback
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))
BASE = "https://followup.dr-manoj.in"
CHECKS = []
RNG = secrets.SystemRandom()
TILE = "Call ke baad"
HELPERS = ("portal_push.py", "clinic_sso.py", "clinic_users.py")
HELPERS_IF_THERE = ("tracker_pass.py", "portal_sw.js")
USERS = {"alisha": "staff", "shivani": "staff", "shavez": "manager", "reception": "staff", "manoj": "doctor", "darpan": "staff"}
FOUR = ("alisha", "shivani", "shavez", "reception")
AGENT_NAMES = {"alisha": "Alisha Walk", "shivani": "Shivani Walk", "shavez": "Shavez Walk", "manoj": "Dr Walk"}   # reception: none
MON = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
T_FOLD = "Shayad yeh aaye?"
T_YES = "Haan, yahi hai"
T_CAME = "doosre number se aaye"
T_UNLINK = "Galat link — hatao"
T_CALL = "IVR se call karein"
T_CALL_OK = "Aapka phone baj raha hai — uthaiye, patient se jod diya jayega"
T_NOAGENT = "Aapka phone IVR mein nahi juda — owner se kahein"
NEW_MARKS = (T_FOLD, T_YES, T_CAME, T_UNLINK, T_CALL, "s558link(this)", "s558call(this)", "data-s558")
RULE_FUNCS = ("appt_state", "can_judge", "first_visit", "visits_since", "file_outcome", "choices_for", "mirror_one",
              "outcome_rows", "mirror_pending", "sweep_once", "recall_appt", "close_appt", "set_appt_day", "_noshow_now",
              "where_now", "floor_day", "list_access")


def _mask(s):
    return re.sub(r"\d{10,}", lambda m: "…" + m.group(0)[-4:], str(s))


def ok(cond, what, detail=""):
    CHECKS.append(bool(cond))
    print("  %s %s%s" % ("pass" if cond else "FAIL", what, ("" if cond else ("  <-- " + _mask(detail)[:400]))))
    return bool(cond)


def note(t):
    print("  note %s" % _mask(t))


def md5f(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def asks(mod, name):
    """A question the kit's program answers; the live program has no such question -> a red check, and the walk goes on."""
    return getattr(mod, name, None) or (lambda *a, **k: "absent")


def dm(d):
    return "%02d-%s" % (d.day, MON[d.month])


def number(taken):
    while True:
        n = RNG.choice("789") + "".join(RNG.choice("0123456789") for _ in range(9))
        if n not in taken and len(set(n)) > 3:
            taken.add(n)
            return n


def text_of(h):
    h = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", h or "")
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def tables(h):
    out = []
    for t in re.findall(r"(?s)<table>(.*?)</table>", h or ""):
        body = (re.findall(r"(?s)<tbody>(.*?)</tbody>", t) or [""])[0]
        out.append(re.findall(r"(?s)<tr>(.*?)</tr>", body))
    return out


def row_of(h, mobile):
    """(part 0 Nahi aaye / 1 Aane baaki / 2 Aa gaye, the row's html) of the line whose mobile cell is this number."""
    for i, rows in enumerate(tables(h)):
        for r in rows:
            if ("tel:+91" + mobile + '"') in r:
                return i, r
    return None, ""


def drawn(h):
    """What the page DRAWS on its lines: the three tables' rows (the page's script and the owner's box left out)."""
    return "".join("".join(rows) for rows in tables(h))


def load_as(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class W(object):
    pass


def part(title, fn, *a):
    print(title)
    try:
        fn(*a)
    except Exception as ex:                                  # noqa: BLE001 -- a part that cannot run is a red check, not a crash
        tb = traceback.extract_tb(sys.exc_info()[2])[-1]
        ok(False, "this part ran to its end", "%s: %s (line %s)" % (type(ex).__name__, ex, tb.lineno))


def funcs_of(path):
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef)}


# ============================================================================================ the scratch world
def build_world(args):
    w = W()
    w.args = args
    w.scratch = tempfile.mkdtemp(prefix="walk_s558_")
    w.pdir, w.fdir, w.wadir = (os.path.join(w.scratch, x) for x in ("portal", "finance", "wa"))
    for d in (w.pdir, w.fdir, w.wadir, os.path.join(w.scratch, "forms")):
        os.makedirs(d)
    w.under = args.portal if args.control else args.kit
    for f in ("ring_outcome.py", "ring_common.py"):
        shutil.copyfile(os.path.join(w.under, f), os.path.join(w.pdir, f))
    shutil.copyfile(os.path.join(args.portal, "portal.py"), os.path.join(w.pdir, "portal.py"))
    for f in HELPERS:
        shutil.copyfile(os.path.join(args.portal, f), os.path.join(w.pdir, f))
    for f in HELPERS_IF_THERE:
        if os.path.isfile(os.path.join(args.portal, f)):
            shutil.copyfile(os.path.join(args.portal, f), os.path.join(w.pdir, f))
    shutil.copyfile(os.path.join(args.portal, "tile_grants.json"), os.path.join(w.pdir, "tile_grants.json"))
    with open(os.path.join(w.fdir, "finance_patient_match.py"), "w", encoding="utf-8") as fh:      # walk-only stand-in
        fh.write('"""walk_s558 stand-in: the shape of the clinic\'s fingerprint, a salt made for this run only."""\n'
                 "import hashlib\nimport os\n\n\ndef salt(env=None):\n    return os.environ.get(\"W558_SALT\", \"\")\n\n\n"
                 "def fingerprint(mobile10, s):\n    if not mobile10 or not s:\n        return \"\"\n"
                 "    return hashlib.sha256((\"%s|%s\" % (s, mobile10)).encode(\"utf-8\")).hexdigest()[:32]\n")
    w.fin = os.path.join(w.fdir, "finance.db")
    con = sqlite3.connect(w.fin)
    con.executescript("""
    CREATE TABLE patient_ref (id INTEGER PRIMARY KEY, clinic_id TEXT NOT NULL UNIQUE, name TEXT, phone_last4 TEXT, first_seen TEXT,
      merged_into INTEGER, note TEXT, mobile_fp TEXT, patient_uid TEXT, mobile TEXT, last_seen TEXT, mobile_dup_count INTEGER);
    CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT);
    CREATE INDEX ix_visit_date ON patient_visit(visit_date);
    CREATE INDEX ix_visit_clinic ON patient_visit(clinic_id);
    CREATE INDEX ix_visit_fp ON patient_visit(mobile_fp);
    """)
    con.commit()
    con.close()
    w.key = secrets.token_hex(24)                            # the walk's own call key, in the walk's own .env
    with open(os.path.join(w.wadir, ".env"), "w", encoding="utf-8") as fh:
        fh.write("CALL_API_SECRET=%s\n" % w.key)
    env = {"RING_PORTAL_DIR": w.pdir, "RING_OUTCOME_DB": os.path.join(w.pdir, "ring_outcomes.db"),
           "TILE_GRANTS_FILE": os.path.join(w.pdir, "tile_grants.json"), "RING_AGENTS_FILE": os.path.join(w.pdir, "ring_agents.json"),
           "RING_HOOK_ENV": os.path.join(w.pdir, "ring_hook.env"), "PUSH_SUBS_FILE": os.path.join(w.pdir, "push_subs.json"),
           "PUSH_DIAG_FILE": os.path.join(w.pdir, "push_diag.json"), "FINANCE_DB": w.fin, "FINANCE_DIR": w.fdir,
           "RING_WA_DIR": w.wadir, "RING_WA_ENV": os.path.join(w.wadir, ".env"), "FU_KEY_DIR": w.wadir, "FU_SHEET_ID": "",
           "CLINIC_USERS_FILE": os.path.join(w.scratch, "walk_users.json"), "PORTAL_FORMS_DIR": os.path.join(w.scratch, "forms"),
           "RING_NO_SWEEPER": "1", "RING_CALL_URL": "http://127.0.0.1:8097/call"}
    os.environ.update(env)
    os.environ["CLINIC_SSO_SECRET"] = secrets.token_hex(32)
    os.environ["W558_SALT"] = secrets.token_hex(16)
    for k in ("PORTAL_PIN_HASH", "PORTAL_PIN_SALT", "PORTAL_TOKEN_SEED", "PATIENT_FP_SALT"):
        os.environ.pop(k, None)
    return w


def load_programs(w):
    here = {os.path.realpath(HERE), os.path.realpath(w.args.kit), os.path.realpath(w.args.portal), os.path.realpath(os.getcwd())}
    sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) not in here]
    sys.path.insert(0, w.pdir)
    for name in ("portal_config", "casepack_portal", "vitals_portal", "portal_wa", "portal_followups"):
        sys.modules[name] = None
    import warnings                                          # noqa: PLC0415
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        import ring_common as rc                             # noqa: PLC0415
        import ring_outcome as ro                            # noqa: PLC0415
        import portal as po                                  # noqa: PLC0415
        import clinic_users as cu                            # noqa: PLC0415
    w.rc, w.ro, w.po, w.cu = rc, ro, po, cu
    root = os.path.realpath(w.pdir) + os.sep
    ok(all(os.path.realpath(m.__file__).startswith(root) for m in (rc, ro, po, cu))
       and md5f(ro.__file__) == md5f(os.path.join(w.under, "ring_outcome.py")) and md5f(rc.__file__) == md5f(os.path.join(w.under, "ring_common.py")),
       "the programs under test are the %s ring_outcome.py and ring_common.py (with the live portal.py), loaded from the walk's scratch folder"
       % ("LIVE (this is the control)" if w.args.control else "kit's"))
    ok(po._SSO_LIBS and po.SSO_SECRET == os.environ["CLINIC_SSO_SECRET"] and "portal_config" not in [k for k, v in sys.modules.items() if v is not None],
       "sign-in runs on the walk's own user store and its own random secret; the live portal_config.py was not loaded")
    w.clock = [datetime(2027, 3, 15, 12, 0, tzinfo=IST)]
    ro.now_ist = lambda: w.clock[0]
    w.net = []

    def no_connect(self, addr, *a, **k):
        w.net.append(("socket", repr(addr)[:60]))
        raise OSError("walk_s558: no network")
    socket.socket.connect = no_connect
    # the stand-in for call_api.py: every request to it is kept; it answers what the part asks it to
    w.calls, w.answer = [], [("json", 200, {"ok": True, "accepted": True})]

    def fake_open(req, *a, **k):
        url = str(getattr(req, "full_url", req))
        if url != os.environ["RING_CALL_URL"]:
            w.net.append(("urlopen", url[:60]))
            raise OSError("walk_s558: no network")
        w.calls.append({"url": url, "method": req.get_method(), "key": req.get_header("X-call-key"),
                        "ctype": req.get_header("Content-type"), "body": json.loads(req.data.decode("utf-8")),
                        "timeout": k.get("timeout", a[0] if a else None)})
        kind, code, body = w.answer[0]
        if kind == "down":
            raise urllib.error.URLError("refused")
        raw = json.dumps(body).encode("utf-8")
        if code != 200:
            raise urllib.error.HTTPError(url, code, "x", {}, io.BytesIO(raw))

        class R(object):
            status = 200

            def read(self):
                return raw

            def __enter__(self):
                return self

            def __exit__(self, *x):
                return False
        return R()
    urllib.request.urlopen = fake_open


def sign_in(w):
    cu, po = w.cu, w.po
    store = os.environ["CLINIC_USERS_FILE"]
    cu.add_role(store, "staff")
    w.pc = po.app.test_client(use_cookies=False)
    w.tok = {}
    for u, role in USERS.items():
        pw = secrets.token_urlsafe(12)
        cu.add_user(store, u, role, pw)
        r = w.pc.post("/portal/login", base_url=BASE, data={"user": u, "password": pw})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        w.tok[u] = m.group(1) if m else ""
    ok(all(w.tok.values()), "six logins sign in through the real /portal/login (alisha, shivani, shavez, reception, manoj, darpan)",
       {u: bool(t) for u, t in w.tok.items()})


def GET(w, user, path):
    r = w.pc.get(path, base_url=BASE, headers={"Cookie": "clinic_sso=" + w.tok[user]})
    if path == "/portal" and r.status_code in (301, 308):
        r = w.pc.get("/portal/", base_url=BASE, headers={"Cookie": "clinic_sso=" + w.tok[user]})
    return r.status_code, r.get_data(as_text=True)


def POST(w, user, path, js=None, form=None):
    h = {"Cookie": "clinic_sso=" + w.tok[user]}
    r = w.pc.post(path, base_url=BASE, headers=h, json=js) if js is not None else w.pc.post(path, base_url=BASE, headers=h, data=form or {})
    return r.status_code, (r.get_json(silent=True) or {}), r.headers.get("Location", "")


def act(w, user, oid, a, **extra):
    b = {"id": oid, "act": a}
    b.update(extra)
    code, j, _l = POST(w, user, "/portal/ring/list/act", js=b)
    return code, j


def at(w, days_ago, clock="11:00"):
    hh, mm = clock.split(":")
    d = w.today - timedelta(days=days_ago)
    return datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=IST)


def fp(m):
    return hashlib.sha256(("%s|%s" % (os.environ["W558_SALT"], m)).encode("utf-8")).hexdigest()[:32]


def vrow(w, cid, d, f=""):
    con = sqlite3.connect(w.fin)
    w.vn += 1
    con.execute("INSERT INTO patient_visit (visit_id, visit_date, clinic_id, patient_uid, mobile_fp, had_procedure) VALUES (?,?,?,?,?,?)",
                ("W558V%04d" % w.vn, d.isoformat(), cid, "W558U" + cid, f, ""))
    con.commit()
    con.close()


def prow(w, cid, name, mobile_fp, first_seen):
    con = sqlite3.connect(w.fin)
    con.execute("INSERT INTO patient_ref (clinic_id, name, mobile_fp, patient_uid, first_seen, last_seen) VALUES (?,?,?,?,?,?)",
                (cid, name, mobile_fp, "W558U" + cid, first_seen.isoformat(), first_seen.isoformat()))
    con.commit()
    con.close()


def ring(w, sid, mobile, login, when, appt=None):
    """One call as ring_hook records it, the tap 'Appointment book ho gaya', and (if given) the promised day."""
    ro, rc = w.ro, w.rc
    who = {login: AGENT_NAMES.get(login, login)}
    ro.record_call(sid, mobile, rc.lookup_caller(mobile), who)
    ro.record_answered(sid, login)
    ro.record_end(sid, "answered", who, [login])
    good, msg, row = ro.file_outcome(sid, "appointment_booked", login, AGENT_NAMES.get(login, login), "", now=when)
    if not good:
        raise RuntimeError("the tap was refused for %s: %s" % (sid, msg))
    if appt is not None:
        good, msg = ro.set_appt_day(sid, appt.isoformat(), login, login, now=when)
        if not good:
            raise RuntimeError("the day was refused for %s: %s" % (sid, msg))
    return row["id"]


def make_day(w):
    """The made-up day: today is 15-Mar-2027 (India time).
    N1  a NEW number A, booked 20 days ago, promised 18 days ago -> its window is [booked, promised + 3] = [T-20, T-15]
    N2  a NEW number C, booked 19 days ago; came, found by its own mobile -- that patient (M) is 'matched by another line'
    N3  a KNOWN caller (an ID on the card), booked 12 days ago, promised 10 days ago -> Nahi aaye, no fold
    N4  a NEW number G, booked yesterday, promised in 2 days -> Aane baaki, its fold with nothing to suggest
    Docterz:  X W5801 first visit T-18 (two days after the booking, another mobile)      -> suggested
              Y W5806 first visit T-16 (another mobile)                                    -> suggested, first (newest)
              L W5802 first visit T-5, 10 days after the window                            -> NOT suggested
              M W5803 first visit T-17 under N2's mobile (N2 came by it)                   -> NOT suggested (matched by another line)
              F W5804 first visit T-16, registered under A's own fingerprint               -> NOT suggested (the caller's own)
              O W5805 an old patient (first visit T-100), seen again T-17 and today        -> NOT suggested (not new)"""
    ro = w.ro
    w.today = w.clock[0].date()
    T = w.today
    w.taken, w.vn = set(), 0
    json.dump({"agents": {number(w.taken): {"user": u, "name": n} for u, n in AGENT_NAMES.items()}},
              open(os.environ["RING_AGENTS_FILE"], "w"))
    w.m = {k: number(w.taken) for k in ("A", "B", "C", "D", "E", "G", "H")}
    # the known caller of N3
    prow(w, "W5810", "Kailash Walk", fp(w.m["E"]), T - timedelta(days=200))
    vrow(w, "W5810", T - timedelta(days=60), fp(w.m["E"]))
    # the list is ON for staff, and follows bookings from 40 days back
    ro.set_list_on(True, "manoj", now=at(w, 41))
    ro._kv_set("follow_from", (T - timedelta(days=40)).isoformat(), "manoj")
    w.id = {}
    w.id["N1"] = ring(w, "w558-n1", w.m["A"], "alisha", at(w, 20), T - timedelta(days=18))
    w.id["N2"] = ring(w, "w558-n2", w.m["C"], "shivani", at(w, 19, "12:30"))
    w.id["N3"] = ring(w, "w558-n3", w.m["E"], "shavez", at(w, 12), T - timedelta(days=10))
    w.id["N4"] = ring(w, "w558-n4", w.m["G"], "alisha", at(w, 1), T + timedelta(days=2))
    # what Docterz shows afterwards
    for cid, name, first, mob, ownfp in (("W5801", "Sunita Walk", 18, "B", False), ("W5806", "Yamini Walk", 16, "D", False),
                                         ("W5802", "Lalit Walk", 5, "H", False), ("W5803", "Meera Walk", 17, "C", False)):
        prow(w, cid, name, fp(w.m[mob]), T - timedelta(days=first))
        vrow(w, cid, T - timedelta(days=first), fp(w.m[mob]))
    prow(w, "W5804", "Farida Walk", fp(w.m["A"]), T - timedelta(days=16))          # registered under the caller's own number
    vrow(w, "W5804", T - timedelta(days=16), "")                                     # ... the visit row carries no fingerprint
    prow(w, "W5805", "Om Walk", fp(number(w.taken)), T - timedelta(days=100))
    vrow(w, "W5805", T - timedelta(days=100))
    vrow(w, "W5805", T - timedelta(days=17))
    vrow(w, "W5805", T)                                                             # the visits on the server reach today
    w.fin_md5 = md5f(w.fin)


def where(w, oid):
    d = w.ro.list_data(None, None, None, None, everything=True)
    for i, p in enumerate(("noshow", "due", "came")):
        for r in d[p]:
            if r["id"] == oid:
                return p
    return ""


def rows(table):
    con = sqlite3.connect("file:%s?mode=ro" % os.environ["RING_OUTCOME_DB"], uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute("SELECT * FROM %s ORDER BY id" % table)]
    except sqlite3.Error:
        return None
    finally:
        con.close()


def switch(w, user, feat, on):
    code, _j, loc = POST(w, user, "/portal/ring/list/switch", form={"feature": feat, "on": "1" if on else "0"})
    return code, loc


# ============================================================================================ PART S
def part_s(w):
    for f, want in (("ring_outcome.py", ["_ids_on_call", "_owner_box", "_row_came", "_row_due", "_row_noshow", "init_db",
                                         "install", "list_data", "render_list"]),
                    ("ring_common.py", ["lookup_caller"])):
        nf, of = funcs_of(os.path.join(w.under, f)), funcs_of(os.path.join(w.args.portal, f))
        changed = sorted(k for k in of if nf.get(k) != of[k])
        ok(changed == want, "%s: of the live file's %d functions only %s differ" % (f, len(of), ", ".join(want)), changed)
        if f == "ring_outcome.py":
            same = [k for k in RULE_FUNCS if nf.get(k) == of.get(k) and of.get(k)]
            ok(len(same) == len(RULE_FUNCS), "THE RULE and the rest are the live bytes: " + ", ".join(RULE_FUNCS),
               sorted(set(RULE_FUNCS) - set(same)))
            ok({"link_appt", "unlink_appt", "ivr_call", "find_people", "feature_on", "_s558_list"} <= set(nf),
               "ring_outcome.py: the link, the undo, the call, the search and the switches are there")
            src = open(os.path.join(w.under, f), encoding="utf-8").read()
            ok("mirror" not in "".join(v for k, v in nf.items() if k in ("link_appt", "unlink_appt", "ivr_call")),
               "a link, an undo and a call are never mirrored to the Google tracker (no mirror call in them)")
            ok("print(" not in "".join(v for k, v in nf.items() if k.startswith(("_s558", "ivr", "_ivr", "link_", "unlink_", "find_"))),
               "nothing of S558 prints or logs (no number, no key, can reach a log line from it)")
            ok("CALL_API_SECRET" in src and src.count('add_header("X-Call-Key"') == 1, "the key is read in one place and goes only into the X-Call-Key header")
        else:
            ok("_linked_ids" in nf, "ring_common.py: the links are read by _linked_ids (read-only, its own path constant)")
    if not w.args.control:
        m = subprocess.run([sys.executable, "-B", os.path.join(w.args.kit, "make_s558.py"), "--check", w.args.portal, w.args.kit],
                           capture_output=True, text=True)
        ok(m.returncode == 0 and m.stdout.count("= the file in the kit") == 2,
           "make_s558.py builds the kit's two programs again from the live bytes, in memory: the same bytes", (m.stdout + m.stderr)[-300:])


# ============================================================================================ PART G -- installed OFF
def part_g(w):
    ro = w.ro
    ok(not asks(ro, "feature_on")("link") and not asks(ro, "feature_on")("call") and asks(ro, "feature_on")("link") != "absent",
       "installed OFF: link_on and call_on read OFF when the owner has not turned them on")
    for u in ("alisha", "shivani", "shavez", "reception", "manoj"):            # the staff-eye walk: each login's own home
        c, h = GET(w, u, "/portal")
        names = [htmllib.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', h)]
        ok(c == 200 and TILE in names, "%s: the portal home renders with the tile 'Call ke baad' (the door to the list)" % u, (c, names[:12]))
    c, _h = GET(w, "darpan", "/portal/ring/list")
    ok(c == 403, "darpan, who does not hold the tile, is refused the list (403)", c)
    for u in ("alisha", "shivani", "shavez", "reception", "manoj"):
        c, h = GET(w, u, "/portal/ring/list?d=30")
        hits = [x for x in NEW_MARKS if x in drawn(h)]
        ok(c == 200 and not hits, "%s: the list renders, and nothing of S558 is on it while both switches are off" % u, (c, hits))
    c, h = GET(w, "manoj", "/portal/ring/list?d=30")
    ok("Doosre number se link: <b>OFF</b>" in h and "IVR call button: <b>OFF</b>" in h,
       "the owner's box carries his two toggles, both OFF", text_of(h)[:200])
    c, h = GET(w, "alisha", "/portal/ring/list?d=30")
    ok("Doosre number se link" not in h and "IVR call button" not in h, "a staff page carries no toggle")
    p, _r = row_of(h, w.m["A"])
    ok(p == 0, "N1 (a new number, its day gone, Docterz reaching today) stands in Nahi aaye", p)
    for a in ("link", "find", "unlink", "call"):
        code, j = act(w, "alisha", w.id["N1"], a, clinic_id="W5801", q="W5801")
        ok(code == 403 and not j.get("ok"), "the act '%s' is refused while its switch is off (403)" % a, (code, j))
    ok(rows("appt_link") == [] and not [e for e in rows("appt_event") if e["kind"] in ("link", "unlink", "ivr_call")],
       "…and nothing was written; no call was attempted", rows("appt_link"))
    ok(not w.calls, "…the stand-in call_api.py was never reached", len(w.calls))
    code, loc = switch(w, "alisha", "link", True)
    ok(code == 403 and not asks(ro, "feature_on")("link"), "a staff login cannot turn a switch on (403)", code)


# ============================================================================================ PART A -- the suggestions
def part_a(w):
    ro = w.ro
    code, loc = switch(w, "manoj", "link", True)
    ok(code == 302 and loc.endswith("m=link_on") and asks(ro, "feature_on")("link") is True and ro.list_on(),
       "the owner turns 'Doosre number se link' ON from his box (302 back to the list); the list itself stays on", (code, loc))
    c, h = GET(w, "manoj", "/portal/ring/list?m=link_on")
    ok("Doosre number se link: turned on." in h and "Doosre number se link: <b>ON</b>" in h, "his box says so")
    c, h = GET(w, "alisha", "/portal/ring/list?d=30")
    p, r1 = row_of(h, w.m["A"])
    cids = re.findall(r'data-cid="([^"]+)"', r1)
    ok(p == 0 and T_FOLD in r1, "N1 (Nahi aaye, a new number) carries the fold 'Shayad yeh aaye?'", p)
    ok(cids == ["W5806", "W5801"], "the suggestions are Yamini (first visit T-16) then Sunita (T-18, two days after the booking): "
       "newest first", cids)
    ok("W5802" not in cids, "Lalit, registered 10 days after the window, is not suggested")
    ok("W5803" not in cids, "Meera, already matched by another ring line (N2 came by her mobile), is not suggested")
    ok("W5804" not in cids, "Farida, registered under the caller's own fingerprint, is not suggested")
    ok("W5805" not in cids, "Om, an old patient seen again in the window, is not suggested")
    T = w.today
    ok(("Sunita Walk · ID W5801 · pehli visit %s" % dm(T - timedelta(days=18))) in htmllib.unescape(r1) and r1.count(T_YES) == 2,
       "each is shown as name · clinic ID · 'pehli visit dd-mm', with one button 'Haan, yahi hai'", text_of(r1)[:300])
    ok(T_CALL not in h, "the IVR button is not drawn while its own switch is off")
    p3, r3 = row_of(h, w.m["E"])
    ok(p3 == 0 and T_FOLD not in r3, "N3 (a known caller, an ID on the card) stands in Nahi aaye with no fold", p3)
    p4, r4 = row_of(h, w.m["G"])
    ok(p4 == 1 and T_FOLD in r4 and "data-cid" not in r4 and "koi naya mareez nahi mila" in r4,
       "N4 (Aane baaki, a new number) carries the fold, saying nobody new is in its window yet", (p4, text_of(r4)[:200]))
    p2, _r2 = row_of(h, w.m["C"])
    ok(p2 == 2, "N2 stands in Aa gaye, found by its own mobile (unchanged)", p2)
    for u in ("shivani", "shavez", "reception", "manoj"):
        c, hh = GET(w, u, "/portal/ring/list?d=30")
        ok(c == 200 and re.findall(r'data-cid="([^"]+)"', row_of(hh, w.m["A"])[1]) == ["W5806", "W5801"],
           "%s sees the same fold and the same two suggestions" % u)


# ============================================================================================ PART E -- the search
def part_e(w):
    oid = w.id["N1"]
    code, j = act(w, "shivani", oid, "find", q="W5803")
    ok(code == 200 and [x["clinic_id"] for x in j.get("hits", [])] == ["W5803"], "search by a clinic ID (exact) finds that patient", (code, j))
    code, j = act(w, "shivani", oid, "find", q="sUnItA")
    ok(code == 200 and [x["clinic_id"] for x in j.get("hits", [])] == ["W5801"] and "Sunita Walk · ID W5801" in j["hits"][0]["words"],
       "search by part of a name, case-blind, finds Sunita", (code, j))
    code, j = act(w, "shivani", oid, "find", q="walk")
    got = [x["clinic_id"] for x in j.get("hits", [])]
    ok(code == 200 and "W5810" not in got and set(got) == {"W5801", "W5802", "W5803", "W5804", "W5805", "W5806"} and len(got) <= 8,
       "search covers only patients with a visit from the booking day to today (Kailash, seen before, is not in it)", got)
    code, j = act(w, "shivani", oid, "find", q="W580")
    ok(code == 200 and j.get("hits") == [], "a part of a clinic ID is not a match (an ID is exact)", j)
    code, j = act(w, "shivani", w.id["N2"], "find", q="W5801")
    ok(code == 409 and not j.get("ok"), "search on a line already in Aa gaye is refused (409)", (code, j))


# ============================================================================================ PART B -- the link
def part_b(w):
    ro = w.ro
    oid = w.id["N1"]
    outc = rows("outcome")
    code, j = act(w, "alisha", oid, "link", clinic_id="W5801")
    ok(code == 200 and j.get("ok"), "alisha presses 'Haan, yahi hai' on Sunita: taken", (code, j))
    ok(where(w, oid) == "came", "N1 now stands in Aa gaye", where(w, oid))
    c, h = GET(w, "shivani", "/portal/ring/list?d=30")
    p, r1 = row_of(h, w.m["A"])
    words = "doosre number se aaye · Sunita Walk · ID W5801 · linked by Alisha Walk"
    ok(p == 2 and words in htmllib.unescape(r1) and ("Aaye · " + dm(w.today - timedelta(days=18))) in htmllib.unescape(r1),
       "the line reads Aaye · %s and '%s'" % (dm(w.today - timedelta(days=18)), words), text_of(r1)[:300])
    ok("Sunita Walk" in text_of(r1.split("</td>")[1]), "the Mareez cell carries the name Docterz gave (Sunita Walk)")
    L = rows("appt_link")
    ok(len(L) == 1 and L[0]["outcome_id"] == oid and L[0]["clinic_id"] == "W5801" and L[0]["mobile"] == w.m["A"]
       and L[0]["linked_by"] == "alisha" and L[0]["linked_at"].startswith(w.today.isoformat()) and not L[0]["undone_at"],
       "appt_link: one row -- this line, W5801, the call's own number, by alisha, today, not undone",
       [{k: v for k, v in x.items() if k != "mobile"} for x in (L or [])])
    E = [e for e in rows("appt_event") if e["kind"] == "link"]
    ok(len(E) == 1 and E[0]["outcome_id"] == oid and E[0]["new_value"] == "W5801" and E[0]["by_login"] == "alisha",
       "appt_event: one 'link' row (W5801, by alisha)", E)
    code, j = act(w, "shivani", oid, "link", clinic_id="W5806")
    ok(code == 409 and not j.get("ok") and len(rows("appt_link")) == 1 and rows("appt_link")[0]["clinic_id"] == "W5801",
       "a second link on the same line is refused (409); the first stands", (code, j))
    code, j = act(w, "alisha", w.id["N4"], "link", clinic_id="W5802")
    ok(code == 400 and not j.get("ok") and where(w, w.id["N4"]) == "due",
       "a link to a clinic ID with no visit on or after the booking day is refused (400); the line stays in Aane baaki", (code, j))
    code, j = act(w, "alisha", w.id["N2"], "link", clinic_id="W5806")
    ok(code == 409, "a link on a line already in Aa gaye is refused (409)", (code, j))
    code, j = act(w, "darpan", oid, "link", clinic_id="W5806")
    ok(code == 403, "darpan, who does not hold the list, is refused (403)", code)
    after = rows("outcome")
    ok([{k: v for k, v in x.items()} for x in after] == outc, "the outcome table is not touched by a link (nothing to mirror)")
    p, rr = row_of(GET(w, "alisha", "/portal/ring/list?d=30")[1], w.m["A"])
    ok(T_UNLINK in rr, "on that line, the same day, staff see 'Galat link — hatao'")


# ============================================================================================ PART D -- remembered
def part_d(w):
    rc, ro = w.rc, w.ro
    info = rc.lookup_caller(w.m["A"])
    lk = [p for p in info.get("patients", []) if p.get("clinic_id") == "W5801"]
    ok(len(lk) == 1 and lk[0].get("linked") is True and lk[0].get("name") == "Sunita Walk" and lk[0].get("visits") == 1
       and lk[0].get("last_visit") == (w.today - timedelta(days=18)).isoformat(),
       "lookup_caller for the caller's number: Sunita is there, 'linked', with her last visit and visit count", info.get("patients"))
    ok([p.get("clinic_id") for p in info["patients"]].count("W5801") == 1, "…once")
    ro.record_call("w558-next", w.m["A"], info, {"alisha": "Alisha Walk"})
    kind, _opts = ro.choices_for(ro.get_call("w558-next"))
    ok(kind == "known", "the next call from that number is a KNOWN caller: the pop-up offers the known list", kind)
    keep = os.environ["W558_SALT"]
    os.environ["W558_SALT"] = ""
    try:
        info2 = rc.lookup_caller(w.m["A"])
    finally:
        os.environ["W558_SALT"] = keep
    ok(not info2.get("fp_ok") and [p.get("clinic_id") for p in info2.get("patients", []) if p.get("linked")] == ["W5801"],
       "a number whose fingerprint cannot be made still reads its link (by the 10 digits)", info2)
    info3 = rc.lookup_caller(w.m["C"])
    ok(not [p for p in info3.get("patients", []) if p.get("linked")], "another number reads no link")


# ============================================================================================ PART C -- the undo
def part_c(w):
    rc, ro = w.rc, w.ro
    oid = w.id["N1"]
    code, j = act(w, "shivani", oid, "unlink")
    ok(code == 200 and j.get("ok") and where(w, oid) == "noshow", "shivani (staff) undoes it the same day: back to Nahi aaye", (code, j))
    L = rows("appt_link")
    ok(len(L) == 1 and L[0]["undone_by"] == "shivani" and L[0]["undone_at"], "the row is kept, marked undone by shivani (never deleted)")
    ok([e["kind"] for e in rows("appt_event") if e["kind"] in ("link", "unlink")] == ["link", "unlink"], "appt_event: 'unlink' written")
    ok(not [p for p in rc.lookup_caller(w.m["A"]).get("patients", []) if p.get("linked")],
       "lookup_caller after the undo: the linked patient is absent")
    code, j = act(w, "shivani", oid, "unlink")
    ok(code == 404, "undo of a line with no live link: refused (404)", code)
    code, j = act(w, "alisha", oid, "link", clinic_id="W5801")
    L = rows("appt_link")
    ok(code == 200 and len(L) == 1 and not L[0]["undone_at"] and where(w, oid) == "came",
       "linked again: the same row is used again (one row per line), Aa gaye again", (code, len(L or [])))
    w.clock[0] = w.clock[0] + timedelta(days=1)                # the NEXT India day
    code, j = act(w, "alisha", oid, "unlink")
    ok(code == 403 and not j.get("ok") and where(w, oid) == "came", "the next day, staff (alisha, who linked it) cannot undo it (403)", (code, j))
    p, rr = row_of(GET(w, "alisha", "/portal/ring/list?d=30")[1], w.m["A"])
    ok(p == 2 and T_UNLINK not in rr, "…and her page no longer offers the undo")
    p, rr = row_of(GET(w, "manoj", "/portal/ring/list?d=30")[1], w.m["A"])
    ok(p == 2 and T_UNLINK in rr, "the owner's page still offers it")
    code, j = act(w, "manoj", oid, "unlink")
    ok(code == 200 and where(w, oid) == "noshow", "the owner (manoj) undoes it the next day: allowed; back to Nahi aaye", (code, j))
    code, j = act(w, "alisha", oid, "link", clinic_id="W5801")
    ok(code == 200 and where(w, oid) == "came", "linked once more (for the parts that follow)", (code, j))


# ============================================================================================ PART F -- the IVR call
def part_f(w):
    ro = w.ro
    n3 = w.id["N3"]
    code, j = act(w, "alisha", n3, "call")
    ok(code == 403 and not w.calls, "with the call switch still off, the call act is refused (403)", code)
    code, loc = switch(w, "manoj", "call", True)
    ok(code == 302 and asks(ro, "feature_on")("call") is True, "the owner turns the IVR call button ON", (code, loc))
    c, h = GET(w, "alisha", "/portal/ring/list?d=30")
    p, r3 = row_of(h, w.m["E"])
    ok(p == 0 and 'onclick="s558call(this)"' in r3 and T_CALL in r3 and T_NOAGENT not in r3,
       "alisha's page: N3 (Nahi aaye) carries 'IVR se call karein'", text_of(r3)[-200:])
    ok(("tel:+91" + w.m["E"]) in r3, "…and the tel: link stays as it was")
    ok(T_CALL not in row_of(h, w.m["G"])[1] and T_CALL not in row_of(h, w.m["A"])[1], "Aane baaki and Aa gaye lines carry no call button")
    c, hr = GET(w, "reception", "/portal/ring/list?d=30")
    p, rr = row_of(hr, w.m["E"])
    ok(p == 0 and T_NOAGENT in rr and "disabled" in rr and 's558call(this)' not in rr,
       "reception (no MyOperator entry): the button is greyed with 'Aapka phone IVR mein nahi juda — owner se kahein'", text_of(rr)[-200:])
    code, j = act(w, "reception", n3, "call")
    ok(code == 400 and j.get("msg") == T_NOAGENT and not w.calls, "…and the press is refused at the server (400); call_api is not reached", (code, j))
    other = number(w.taken)
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code, j = act(w, "alisha", n3, "call", mobile=other, patient_number=other)
    ok(code == 200 and j.get("ok") is True and j.get("msg") == T_CALL_OK, "accepted: '%s'" % T_CALL_OK, (code, j))
    c1 = w.calls[-1] if w.calls else {}
    ok(c1.get("method") == "POST" and c1.get("url") == "http://127.0.0.1:8097/call" and c1.get("key") == w.key
       and c1.get("ctype") == "application/json" and c1.get("timeout") == 30,
       "the stand-in call_api.py got a POST with X-Call-Key = the key from .env, JSON, a 30 s timeout",
       {k: v for k, v in c1.items() if k not in ("key", "body")})
    ok(c1.get("body") == {"agent": "Alisha Walk", "patient_number": w.m["E"], "reference_id": "RL%d" % n3},
       "…its body: alisha's MyOperator name, the line's STORED number (not the one the page sent), reference RL<id>",
       c1.get("body"))
    ok(w.m["E"] not in out.getvalue() + err.getvalue() and w.key not in out.getvalue() + err.getvalue(),
       "nothing printed or logged carries the number or the key")
    for u in ("alisha", "manoj", "reception", "shivani"):
        ok(w.key not in GET(w, u, "/portal/ring/list?d=30")[1], "%s's page never contains the key" % u)
    ev = [e for e in rows("appt_event") if e["kind"] == "ivr_call"]
    ok(len(ev) == 1 and ev[0]["by_login"] == "alisha" and ev[0]["new_value"] == "accepted" and ev[0]["at_ist"]
       and w.m["E"] not in json.dumps(ev), "appt_event 'ivr_call': who (alisha), when, accepted -- no number in it", ev)
    n = len(w.calls)
    code, j = act(w, "shivani", n3, "call")
    ok(code == 429 and len(w.calls) == n, "a second press on the same line within 60 seconds is refused (429); call_api not reached", code)

    def age():
        con = sqlite3.connect(os.environ["RING_OUTCOME_DB"])
        con.execute("UPDATE appt_event SET created_at=created_at-61 WHERE kind='ivr_call'")
        con.commit()
        con.close()
    age()
    digits = number(w.taken)
    w.answer[0] = ("json", 200, {"ok": False, "accepted": False, "reason": "Agent busy hai %s" % digits})
    code, j = act(w, "shivani", n3, "call")
    ok(code == 502 and j.get("msg", "").startswith("Call nahi lagi: Agent busy hai") and digits not in j.get("msg", "")
       and ("…" + digits[-4:]) in j.get("msg", ""), "refused: 'Call nahi lagi: <call_api's reason, short>' (a long number in it cut to its last 4)", j)
    ok(w.calls[-1]["body"]["agent"] == "Shivani Walk", "…shivani's own MyOperator name was sent for her press")
    age()
    w.answer[0] = ("json", 400, {"ok": False, "reason": "Unknown agent. Send the agent's extension (10-16), exact name, or a valid user_id."})
    code, j = act(w, "shivani", n3, "call")
    ok(code == 400 and j.get("msg") == T_NOAGENT, "call_api refusing the agent (its 400) is said as 'Aapka phone IVR mein nahi juda'", (code, j))
    age()
    w.answer[0] = ("down", 0, {})
    code, j = act(w, "shivani", n3, "call")
    ok(code == 502 and "IVR server se jawab nahi" in j.get("msg", ""), "call_api not answering: 'Call nahi lagi: IVR server se jawab nahi aaya'", j)
    w.answer[0] = ("json", 200, {"ok": True, "accepted": True})
    ev = [e["new_value"] for e in rows("appt_event") if e["kind"] == "ivr_call"]
    ok(ev == ["accepted", "refused", "refused", "error"], "each press is kept: accepted, refused, refused, error", ev)
    code, j = act(w, "alisha", w.id["N4"], "call")
    ok(code == 409, "a call on an Aane baaki line is refused (409)", code)
    code, j = act(w, "alisha", w.id["N1"], "call")
    ok(code == 409, "a call on an Aa gaye line is refused (409)", code)
    os.rename(os.environ["RING_WA_ENV"], os.environ["RING_WA_ENV"] + ".away")
    try:
        age()
        n = len(w.calls)
        code, j = act(w, "alisha", n3, "call")
        ok(code == 502 and len(w.calls) == n and "set nahi" in j.get("msg", ""), "no key in .env: refused, call_api not reached", (code, j))
    finally:
        os.rename(os.environ["RING_WA_ENV"] + ".away", os.environ["RING_WA_ENV"])


# ============================================================================================ PART O -- switches off again
def part_o(w):
    ro, rc = w.ro, w.rc
    c1, _l = switch(w, "manoj", "link", False)
    c2, _l = switch(w, "manoj", "call", False)
    ok(c1 == 302 and c2 == 302 and asks(ro, "feature_on")("link") is False and asks(ro, "feature_on")("call") is False and ro.list_on(),
       "the owner turns both OFF again; the list itself stays on", (c1, c2))
    for u in ("alisha", "shivani", "shavez", "reception", "manoj"):
        c, h = GET(w, u, "/portal/ring/list?d=30")
        hits = [x for x in NEW_MARKS if x in drawn(h)]
        ok(c == 200 and not hits, "%s: nothing of S558 renders (no fold, no button, no linked words)" % u, hits)
    ok(where(w, w.id["N1"]) == "noshow", "with the link switch off a stored link supplies nothing: N1 is back in Nahi aaye")
    for a in ("link", "find", "unlink", "call"):
        code, j = act(w, "manoj", w.id["N1"] if a != "call" else w.id["N3"], a, clinic_id="W5806", q="W5806")
        ok(code == 403, "the act '%s' is refused again (403), even for the owner" % a, code)
    ok(not [p for p in rc.lookup_caller(w.m["A"]).get("patients", []) if p.get("linked")],
       "lookup_caller with link_on=0: the linked patient is absent")
    ok(len(rows("appt_link") or []) == 1 and not rows("appt_link")[0]["undone_at"], "the stored link itself is kept as it was")
    ok(md5f(w.fin) == w.fin_md5, "finance.db: not one byte changed by the whole walk (opened read-only)")
    ok(not w.net, "nothing tried to leave this machine", w.net)


# ============================================================================================ PART H -- S497's own walk
def part_h(w):
    k = w.args.s497
    pd = w.args.portal
    froms = {"ring_outcome.py": "ring_outcome.py.bak_S497_495b0ada", "portal.py": "portal.py.bak_S497_63df9d49",
             "tile_grants.json": "tile_grants.json.bak_S497_f9441311"}
    if not (k and os.path.isfile(os.path.join(k, "walk_s497.py")) and all(os.path.isfile(os.path.join(pd, b)) for b in froms.values())):
        ok(False, "S497's kit folder (--s497) and its three FROM backups beside the live files are there", k)
        return
    base = tempfile.mkdtemp(prefix="walk_s558_h_")
    kk, pp = os.path.join(base, "kit"), os.path.join(base, "portal")
    os.makedirs(kk)
    os.makedirs(pp)
    for f in os.listdir(k):
        if os.path.isfile(os.path.join(k, f)):
            shutil.copyfile(os.path.join(k, f), os.path.join(kk, f))
    shutil.copyfile(os.path.join(w.args.kit, "ring_outcome.py"), os.path.join(kk, "ring_outcome.py"))     # S497's TO -> this kit's
    shutil.copyfile(os.path.join(pd, "portal.py"), os.path.join(kk, "portal.py"))                         # S497's TO = live
    for f, b in froms.items():
        shutil.copyfile(os.path.join(pd, b), os.path.join(pp, f))                                         # S497's FROM files
    for f in ("portal_push.py", "clinic_sso.py", "clinic_users.py", "tracker_pass.py", "portal_sw.js"):
        if os.path.isfile(os.path.join(pd, f)):
            shutil.copyfile(os.path.join(pd, f), os.path.join(pp, f))
    shutil.copyfile(os.path.join(w.args.kit, "ring_common.py"), os.path.join(pp, "ring_common.py"))       # this kit's ring_common
    env = dict(os.environ)
    for x in list(env):
        if x.startswith(("RING_", "FU_", "W558", "CLINIC_", "FINANCE_", "PUSH_", "PORTAL_", "TILE_")):
            env.pop(x)
    env["TMPDIR"] = base
    p = subprocess.run([sys.executable, "-W", "ignore", "-B", os.path.join(kk, "walk_s497.py"), "--kit", kk, "--portal", pp],
                       capture_output=True, text=True, env=env, cwd=base, timeout=900)
    lines = p.stdout.splitlines()
    fails = [x for x in lines if x.startswith("  FAIL")]
    last = lines[-1] if lines else (p.stderr[-200:] or "no output")
    known = ("ring_outcome.py: of the live file's", "make_s497.py builds the kit's two programs again")
    other = [x for x in fails if not x.startswith(tuple("  FAIL " + s for s in known))]
    n = re.match(r"WALK_S497 (GREEN|RED) (\d+)", last)
    ok(n is not None and not other and any(known[1] in x for x in fails),
       "S497's own walk, re-run on this kit's programs: %s -- the only red line is its file-identity check (make_s497 rebuilds S497's bytes, and the "
       "program is now S558's); every check of THE RULE, the tap, the card, the clock and Docterz is green" % _mask(last),
       [x[:160] for x in other][:6])
    for x in fails:
        note("S497 walk, expected red (file identity): " + x.strip()[:150])
    shutil.rmtree(base, ignore_errors=True)


# ============================================================================================ PART R -- copies of the real stores
def part_r(w):
    src = w.args.db
    cp = os.path.join(w.scratch, "real_copy.db")
    a = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=30)
    b = sqlite3.connect(cp)
    a.backup(b)
    b.close()
    a.close()

    def shape(p):
        c = sqlite3.connect("file:%s?mode=ro" % p, uri=True)
        out = {}
        for t in ("call", "outcome", "kv", "appt_event"):
            r = c.execute("SELECT * FROM %s ORDER BY 1" % t).fetchall()
            out[t] = (len(r), hashlib.md5(repr(r).encode("utf-8")).hexdigest())
        c.close()
        return out
    before = shape(cp)
    w.ro.init_db(cp)
    after = shape(cp)
    c = sqlite3.connect("file:%s?mode=ro" % cp, uri=True)
    have = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    c.close()
    ok("appt_link" in have and before == after, "a copy of the real ring store: appt_link is made; call, outcome, kv, appt_event not changed")
    ro = w.ro
    keep_now = ro.now_ist
    ro.now_ist = lambda: datetime.now(IST)
    try:
        d0 = ro.list_data("30", cp, None, w.args.finance_db)
        ok(d0["store_ok"] and not d0.get("link_on") and not d0.get("call_on"),
           "the real list reads on the copy with both switches OFF (as installed): %d Nahi aaye . %d Aane baaki . %d Aa gaye"
           % (len(d0["noshow"]), len(d0["due"]), len(d0["came"])))
        ro.set_feature("link", True, "walk", cp)
        d1 = ro.list_data("30", cp, None, w.args.finance_db)
        folds = [r for r in d1["noshow"] + d1["due"] if r.get("s558_new")]
        ok(d1["store_ok"] and [len(d1[x]) for x in ("noshow", "due", "came")] == [len(d0[x]) for x in ("noshow", "due", "came")],
           "with the link switch on (on the COPY only): the same lines in the same parts; %d line(s) of a new number get the fold, "
           "%d suggestion(s) in all (counts only)" % (len(folds), sum(len(r.get("s558_sugg") or []) for r in folds)))
        html_ = ro.render_list(d1, True, True, [], "", viewer="manoj")
        ok(html_.count("data-s558-fold") == len(folds), "…the owner's page on the copy draws exactly those folds")
    finally:
        ro.now_ist = keep_now


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", required=True)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--s497", default="")
    ap.add_argument("--db", default="")
    ap.add_argument("--finance-db", dest="finance_db", default="")
    args = ap.parse_args()
    w = build_world(args)
    print("WALK S558 -- %s" % ("CONTROL: the LIVE files" if args.control else "the kit's files"))
    part("PART S  the files", part_s, w)
    part("LOAD    the programs, the sign-in", lambda: (load_programs(w), sign_in(w), make_day(w)))
    part("PART G  installed OFF", part_g, w)
    part("PART A  (a) the suggestions", part_a, w)
    part("PART E  (e) the search", part_e, w)
    part("PART B  (b) the link", part_b, w)
    part("PART D  (d) the second number remembered", part_d, w)
    part("PART C  (c) the undo", part_c, w)
    part("PART F  (f) the IVR call", part_f, w)
    part("PART O  (g) the switches off again", part_o, w)
    if not args.control:
        part("PART H  (h) S497's own walk on this kit's programs", part_h, w)
        if args.db and args.finance_db:
            part("PART R  copies of the real stores (counts only)", part_r, w)
    shutil.rmtree(w.scratch, ignore_errors=True)
    bad = CHECKS.count(False)
    print("WALK_S558 %s %s" % ("GREEN" if not bad else "RED", ("%d checks" % len(CHECKS)) if not bad else ("%d failed of %d" % (bad, len(CHECKS)))))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
