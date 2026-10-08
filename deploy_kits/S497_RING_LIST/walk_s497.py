#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s497.py -- the walk of S497_RING_LIST ("the after-call list", tile 'Call ke baad'). It writes ONLY under its own
scratch folder: never to --kit, --portal, --db or --finance-db.

    python3 -B walk_s497.py --kit <kit folder> --portal <the portal's code folder as it is live>
            [--control]                 the SAME walk on the LIVE files -- the negative control; it must end RED
            [--now "YYYY-MM-DD HH:MM"]  the India-time moment the made-up day is built around (default: the clock)
            [--screens DIR]             also write the four real screens there, as served (made-up names and numbers)
            [--db ring_outcomes.db] [--finance-db finance.db]   a COPY of the real store, counts only (part R)

THE REAL portal.py and ring_outcome.py are loaded from a scratch copy and driven through Flask's test client. Sign-in
runs on the walk's OWN user store and its OWN random signing secret (the live secret, the live password store and
portal_config.py are never read); the finance database is a made-up one; the fingerprint module is a walk-only
stand-in with a random salt. EVERY mobile number is made at run time from random digits -- none is written here (F-676).

PART S  the files: what changed against the live bytes, and nothing else.
PART 1  the made-up day, exactly the owner's mock-up -- each login's home and page while the list is OFF, the tap, his
        switch (and: NO OLD LINE meets the staff on the first morning), then ON: the tile, the three parts and their
        order, the columns, every cell, the card after the tap.
PART 2  the two buttons, the optional day, the note -- and what each does to the store; a press is taken only where
        the button stands.
PART 3  the rule: no-show on both branches, the setting changed, a late arrival, the family mobile, the spans, the
        floor -- and that nobody is called a no-show before Docterz can speak for that day.
PART 4  the clock: India-time midnight from both sides, moments given in UTC, five process time zones.
PART 5  Docterz: read-only, patient_visit only, bytes unchanged; absent; locked.  WhatsApp: the place, and nothing sent.
PART 6  a store made by the LIVE file is taken over by the kit's: columns added, nothing lost.
PART 7  the rest of what the review of 08-Oct found: a masked tile, odd numbers, names for logins, the date box,
        the phone's sticky column, the counts page.
PART R  (with --db) a copy of the real store: counts only -- no name, no number is printed.
A check that begins [B1 s1.py] (and so on) is one the review's own script showed failing on the build before this one.
Last line:  WALK_S497 GREEN <n> checks   or   WALK_S497 RED <n> failed of <m>
"""
import argparse
import ast
import difflib
import hashlib
import html as htmllib
import importlib.util
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
import threading
import time
import traceback
from datetime import date, datetime, timedelta, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
IST = timezone(timedelta(hours=5, minutes=30))
UTC = timezone.utc
BASE = "https://followup.dr-manoj.in"
CHECKS = []
RNG = secrets.SystemRandom()
TILE = "Call ke baad"
HELPERS = ("ring_common.py", "portal_push.py", "clinic_sso.py", "clinic_users.py")
HELPERS_IF_THERE = ("tracker_pass.py", "portal_sw.js")
USERS = {"alisha": "staff", "shivani": "staff", "shavez": "manager", "reception": "staff", "manoj": "doctor", "darpan": "staff"}
FOUR = ("alisha", "shivani", "shavez", "reception")
PEOPLE = {"shivani": "Shivani", "alisha": "Alisha", "shavez": "Shavez", "reception": "Reception"}
# the mock-up's people: key -> (name, clinic ID, last visit this many days before the mock-up's day)
PATIENTS = {"rajesh": ("Rajesh Kumar", "4521", 35), "meena": ("Meena Devi", "3310", 57), "suresh": ("Suresh Pal", "2207", 80),
            "imran": ("Imran Khan", "5108", 9), "ramesh": ("Ramesh Gangwar", "4890", 20), "arif": ("Mohd. Arif", "3077", 30),
            "kamla": ("Kamla Rani", "1456", 40)}
# the mock-up's ten lines: key, booked (days ago, clock), who filed, patient (None = a new number), promised day
# (days from today; None = no day given), note
MOCK = [("r1", 4, "11:20", "shivani", "rajesh", -2, "ghutne ka dard"),
        ("r2", 5, "17:45", "alisha", None, -4, "kandhe ki chot, surgery puchh rahe the"),
        ("r3", 6, "10:05", "shavez", "meena", None, ""),
        ("r4", 0, "10:15", "alisha", "suresh", 1, "kal 11 baje"),
        ("r5", 0, "09:40", "shivani", None, 0, "shaam ko aayenge"),
        ("r6", 1, "18:30", "reception", "imran", 2, ""),
        ("r7", 2, "12:02", "shavez", "ramesh", -1, ""),
        ("r8", 2, "10:48", "shivani", None, -2, ""),
        ("r9", 4, "16:10", "alisha", "arif", -2, ""),
        ("r10", 5, "11:30", "reception", "kamla", None, "")]
MOCK_VISIT = {"r7": 1, "r8": 2, "r9": 1, "r10": 4}          # Docterz shows a visit this many days ago
MOCK_NEW = {"r8": ("Sunita Devi", "9917")}                 # the name and ID Docterz gave a number that was new
MON = ("", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
DOW_FROM_WED = ("Wed", "Thu", "Fri", "Sat", "Sun", "Mon", "Tue")
ANCHOR_WED = date(2026, 10, 7)                             # the mock-up says so itself: "07-Oct (Wed)"
HARD = date(2026, 10, 1)                                   # the list never follows an appointment booked before this day
T_UNSURE = "Docterz se abhi pakka nahi hua"
T_NO_MATCH = "Is number se Docterz ki visit nahi mil sakti"
T_NOT_NOSHOW = "Yeh line ab “Nahi aaye” mein nahi hai. List dobara dekhein."


def hard_words():
    return "%s-%d" % (dm(HARD), HARD.year)


def ok(cond, what, detail=""):
    CHECKS.append(bool(cond))
    print("  %s %s%s" % ("pass" if cond else "FAIL", what, ("" if cond else ("  <-- " + str(detail)[:500]))))
    return bool(cond)


def note(t):
    print("  note %s" % t)


def md5f(p):
    with open(p, "rb") as fh:
        return hashlib.md5(fh.read()).hexdigest()


def asks(ro, name):
    """A question the kit's program answers. A build that has no such question answers 'absent' -- a red check, and the
    walk goes on (so the walk can be run on the build before this one, and each finding seen red there)."""
    return getattr(ro, name, None) or (lambda *a, **k: "absent")


def dm(d):
    return "%02d-%s" % (d.day, MON[d.month])


def dow(d):
    """The weekday in English, worked from the mock-up's own Wednesday -- not from the code under test."""
    return DOW_FROM_WED[(d.toordinal() - ANCHOR_WED.toordinal()) % 7]


def dmw(d):
    return "%s (%s)" % (dm(d), dow(d))


def number(taken):
    """A ten-digit number that is nobody's: made here from random digits, never written in this file."""
    while True:
        n = RNG.choice("789") + "".join(RNG.choice("0123456789") for _ in range(9))
        if n not in taken and len(set(n)) > 3:
            taken.add(n)
            return n


def spaced(m):
    return m[:5] + " " + m[5:]


def text_of(h):
    h = re.sub(r"(?s)<(script|style)\b.*?</\1>", " ", h or "")
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", h))).strip()


def seen(cell):
    """What a person sees in a table cell: the day-chooser of a 'Nahi aaye' line is closed until its button is pressed."""
    return text_of(cell.split("<div data-s497-pick")[0])


def tables(h):
    """[(column heads, [[cell html ...] per line])] for each table of the page, in order."""
    out = []
    for t in re.findall(r"(?s)<table>(.*?)</table>", h or ""):
        heads = [text_of(x) for x in re.findall(r"(?s)<th>(.*?)</th>", t)]
        body = (re.findall(r"(?s)<tbody>(.*?)</tbody>", t) or [""])[0]
        rows = [re.findall(r"(?s)<td[^>]*>(.*?)</td>", r) for r in re.findall(r"(?s)<tr>(.*?)</tr>", body)]
        out.append((heads, rows))
    return out


def tiles(h):
    return [htmllib.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', h or "")]


def table_print(path, names=("call", "outcome", "appt_event", "kv")):
    con = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    out = {}
    for t in names:
        try:
            rows = con.execute("SELECT * FROM %s ORDER BY 1" % t).fetchall()
            out[t] = (len(rows), hashlib.md5(repr(rows).encode("utf-8")).hexdigest())
        except sqlite3.Error:
            out[t] = None
    con.close()
    return out


def load_as(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def quiet():
    """Wait for the tap's own mirror thread (it finds no key in the scratch folder and stops) before a store is fingerprinted."""
    end = time.time() + 20
    while time.time() < end and [t for t in threading.enumerate() if t is not threading.current_thread() and t.daemon]:
        time.sleep(0.05)


class W(object):
    """The walk's own world: the scratch folders, the loaded programs, the signed-in logins, the made-up day."""


def part(title, fn, *a):
    print(title)
    try:
        fn(*a)
    except Exception as ex:                                  # noqa: BLE001  -- a part that cannot run is a red check, not a crash
        tb = traceback.extract_tb(sys.exc_info()[2])[-1]
        ok(False, "this part ran to its end", "%s: %s (line %s)" % (type(ex).__name__, ex, tb.lineno))


# ============================================================================================ PART S -- the files
def _lit(node):
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.List):
        return [_lit(x) for x in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_lit(x) for x in node.elts)
    if isinstance(node, ast.Dict):
        return {_lit(k): _lit(v) for k, v in zip(node.keys, node.values)}
    return "<computed: %s>" % ast.dump(node)


def tree_of(path):
    import warnings                                          # noqa: PLC0415
    src = open(path, encoding="utf-8").read()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return src, ast.parse(src)


def tables_of_portal(path):
    _src, tree = tree_of(path)
    got = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ("TILES", "_TILE_GROUP", "GROUP_ORDER"):
            got[node.targets[0].id] = _lit(node.value)
    return got


def funcs_of(path):
    src, tree = tree_of(path)
    return {n.name: ast.get_source_segment(src, n) for n in tree.body if isinstance(n, ast.FunctionDef)}


def part_s(w):
    new_p, old_p = os.path.join(w.under, "portal.py"), os.path.join(w.args.portal, "portal.py")
    new, old = tables_of_portal(new_p), tables_of_portal(old_p)
    mine = [t for t in new["TILES"] if t["name"] == TILE]
    ok(len(mine) == 1 and mine[0]["url"] == "/portal/ring/list" and mine[0]["roles"] == ["doctor"] and mine[0]["live"] is True,
       "portal.py: one new tile, 'Call ke baad', to /portal/ring/list, the doctor's by role", mine)
    names = [t["name"] for t in new["TILES"]]
    ok(TILE in names and names[names.index(TILE) - 1] == "Call Tracker", "…it sits right after Call Tracker", names[:8])
    ok([t for t in new["TILES"] if t["name"] != TILE] == old["TILES"], "…every other tile is exactly the live tile, in the same order")
    g = dict(new["_TILE_GROUP"])
    sect = g.pop(TILE, None)
    ok(sect == "Clinic" and g == old["_TILE_GROUP"] and new["GROUP_ORDER"] == old["GROUP_ORDER"],
       "…its section is Clinic, as Call Tracker's; the sections are otherwise the live sections", sect)
    a = open(old_p, encoding="utf-8").read().splitlines()
    b = open(new_p, encoding="utf-8").read().splitlines()
    gone = [a[i] for tag, i1, i2, _j1, _j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes() if tag != "equal" for i in range(i1, i2)]
    ok(len(gone) == 2 and '"Call Tracker": "Clinic",' in gone[0] and 'not t.get("pc_only") or pc)]' in gone[1],
       "…against the live file: two lines changed (the section line, the end of the tile filter), %d added, nothing else" % (len(b) - len(a)),
       (len(gone), gone[:3]))
    nf, of = funcs_of(os.path.join(w.under, "ring_outcome.py")), funcs_of(os.path.join(w.args.portal, "ring_outcome.py"))
    changed = sorted(k for k in of if nf.get(k) != of[k])
    ok(changed == ["init_db", "install", "render_page"],
       "ring_outcome.py: of the live file's %d functions only init_db, install and render_page differ -- the tap (file_outcome), "
       "the mirror into the tracker, the sweeper and the counts are byte for byte the live ones" % len(of), changed)
    ok(len(set(nf) - set(of)) >= 20 and {"list_data", "appt_state", "visits_since", "render_list", "render_appt_card", "_page"} <= set(nf),
       "…and the list's own functions are there (%d new)" % len(set(nf) - set(of)))
    src = open(os.path.join(w.under, "ring_outcome.py"), encoding="utf-8").read()
    ok(src.count('.replace("SID"') == 1 and "def _page(" in src,
       "F-797: the page's id is put in at ONE place, the template's -- no longer through the whole page", src.count('.replace("SID"'))
    # the grants
    live_g = os.path.join(w.args.portal, "tile_grants.json")
    cp = os.path.join(w.scratch, "grants_copy.json")
    shutil.copyfile(live_g, cp)
    ap = os.path.join(w.args.kit, "apply_s497.py")
    p = subprocess.run([sys.executable, "-B", ap, cp], capture_output=True, text=True)
    pins = subprocess.run([sys.executable, "-B", ap, "--pins"], capture_output=True, text=True).stdout.split()
    ok(p.returncode == 0 and "v32 -> v33" in p.stdout and len(pins) == 2 and md5f(live_g) == pins[0] and md5f(cp) == pins[1],
       "tile_grants.json: apply_s497.py takes the live v32 to v33 at the md5 it names (its own checks: nothing else moved)", (p.stdout + p.stderr)[-300:])
    g2 = json.load(open(cp, encoding="utf-8"))
    who = sorted(u for u, d in g2["users"].items() if TILE in (d.get("extra") or []))
    ok(who == sorted(FOUR) and all(g2["users"][u]["extra"][g2["users"][u]["extra"].index(TILE) - 1] == "Call Tracker" for u in FOUR),
       "…the tile by name to the four who hold Call Tracker -- alisha, reception, shavez, shivani -- right after it; to nobody else", who)
    before = md5f(cp)
    p2 = subprocess.run([sys.executable, "-B", ap, cp], capture_output=True, text=True)
    ok(p2.returncode == 0 and "already v33" in p2.stdout and md5f(cp) == before, "…run again on its own result: 'already v33', not a byte changed", p2.stdout[-200:])
    bad = os.path.join(w.scratch, "grants_changed.json")
    with open(bad, "wb") as fh:
        fh.write(open(live_g, "rb").read() + b"\n")
    p3 = subprocess.run([sys.executable, "-B", ap, bad], capture_output=True, text=True)
    ok(p3.returncode == 1 and "nothing written" in p3.stdout and open(bad, "rb").read() == open(live_g, "rb").read() + b"\n",
       "…a tile_grants.json that is not v32 is refused and left untouched", p3.stdout[-200:])
    if not w.args.control:
        m = subprocess.run([sys.executable, "-B", os.path.join(w.args.kit, "make_s497.py"), "--check", w.args.portal, w.args.kit], capture_output=True, text=True)
        ok(m.returncode == 0 and m.stdout.count("= the file in") == 2,
           "make_s497.py builds the kit's two programs again from the live bytes, in memory: the same bytes", (m.stdout + m.stderr)[-300:])


# ============================================================================================ the scratch world
def build_world(args):
    w = W()
    w.args = args
    w.scratch = tempfile.mkdtemp(prefix="walk_s497_")
    w.pdir, w.fdir = os.path.join(w.scratch, "portal"), os.path.join(w.scratch, "finance")
    for d in (w.pdir, w.fdir, os.path.join(w.scratch, "wa"), os.path.join(w.scratch, "forms")):
        os.makedirs(d)
    w.under = args.portal if args.control else args.kit      # where the two programs under test come from
    for f in ("ring_outcome.py", "portal.py"):
        shutil.copyfile(os.path.join(w.under, f), os.path.join(w.pdir, f))
    for f in HELPERS:
        shutil.copyfile(os.path.join(args.portal, f), os.path.join(w.pdir, f))
    for f in HELPERS_IF_THERE:
        if os.path.isfile(os.path.join(args.portal, f)):
            shutil.copyfile(os.path.join(args.portal, f), os.path.join(w.pdir, f))
    shutil.copyfile(os.path.join(args.portal, "tile_grants.json"), os.path.join(w.pdir, "tile_grants.json"))
    if not args.control:
        subprocess.run([sys.executable, "-B", os.path.join(args.kit, "apply_s497.py"), os.path.join(w.pdir, "tile_grants.json")],
                       capture_output=True, text=True, check=True)
    with open(os.path.join(w.fdir, "finance_patient_match.py"), "w", encoding="utf-8") as fh:      # walk-only stand-in
        fh.write('"""walk_s497 stand-in: the same shape as the clinic\'s fingerprint, a salt made for this run only."""\n'
                 "import hashlib\nimport os\n\n\ndef salt(env=None):\n    return os.environ.get(\"W497_SALT\", \"\")\n\n\n"
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
    CREATE TABLE day_entry (id INTEGER PRIMARY KEY, unit TEXT, business_date TEXT, amount_p INTEGER);
    INSERT INTO day_entry (unit, business_date, amount_p) VALUES ('walk', '2026-01-01', 12345);
    """)
    con.commit()
    con.close()
    env = {"RING_PORTAL_DIR": w.pdir, "RING_OUTCOME_DB": os.path.join(w.pdir, "ring_outcomes.db"),
           "TILE_GRANTS_FILE": os.path.join(w.pdir, "tile_grants.json"), "RING_AGENTS_FILE": os.path.join(w.pdir, "ring_agents.json"),
           "RING_HOOK_ENV": os.path.join(w.pdir, "ring_hook.env"), "PUSH_SUBS_FILE": os.path.join(w.pdir, "push_subs.json"),
           "PUSH_DIAG_FILE": os.path.join(w.pdir, "push_diag.json"), "FINANCE_DB": w.fin, "FINANCE_DIR": w.fdir,
           "RING_WA_DIR": os.path.join(w.scratch, "wa"), "RING_WA_ENV": os.path.join(w.scratch, "wa", ".env"),
           "FU_KEY_DIR": os.path.join(w.scratch, "wa"), "FU_SHEET_ID": "", "CLINIC_USERS_FILE": os.path.join(w.scratch, "walk_users.json"),
           "PORTAL_FORMS_DIR": os.path.join(w.scratch, "forms"), "RING_NO_SWEEPER": "1"}
    os.environ.update(env)
    os.environ["CLINIC_SSO_SECRET"] = secrets.token_hex(32)   # the walk's own, made now, never the live one
    os.environ["W497_SALT"] = secrets.token_hex(16)
    for k in ("PORTAL_PIN_HASH", "PORTAL_PIN_SALT", "PORTAL_TOKEN_SEED", "PATIENT_FP_SALT"):
        os.environ.pop(k, None)
    return w


def load_programs(w):
    """Take the kit's own folder (and the working folder) off the import path, by REAL path (F-776), put the scratch
    portal first, and shut out every module of the live box the walk must not read."""
    here = {os.path.realpath(HERE), os.path.realpath(w.args.kit), os.path.realpath(w.args.portal), os.path.realpath(os.getcwd())}
    sys.path[:] = [p for p in sys.path if os.path.realpath(p or os.getcwd()) not in here]
    sys.path.insert(0, w.pdir)
    for name in ("portal_config", "casepack_portal", "vitals_portal", "portal_wa", "portal_followups"):
        sys.modules[name] = None                             # 'import portal_config' now fails: the live secrets cannot be read
    import warnings                                          # noqa: PLC0415
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")                      # the live portal.py carries an old '\/' inside a page's script
        import ring_common as rc                             # noqa: PLC0415
        import ring_outcome as ro                            # noqa: PLC0415
        import portal as po                                  # noqa: PLC0415
        import clinic_users as cu                            # noqa: PLC0415
    w.rc, w.ro, w.po, w.cu = rc, ro, po, cu
    root = os.path.realpath(w.pdir) + os.sep
    here_ok = all(os.path.realpath(m.__file__).startswith(root) for m in (rc, ro, po, cu, sys.modules["portal_push"], sys.modules["clinic_sso"]))
    ok(here_ok and md5f(ro.__file__) == md5f(os.path.join(w.under, "ring_outcome.py")) and md5f(po.__file__) == md5f(os.path.join(w.under, "portal.py")),
       "the programs under test are the %s ring_outcome.py and portal.py, loaded from the walk's scratch folder and nowhere else"
       % ("LIVE (this is the control)" if w.args.control else "kit's"), (ro.__file__, po.__file__))
    ok(po._SSO_LIBS and po.SSO_SECRET == os.environ["CLINIC_SSO_SECRET"] and po.STORE == os.environ["CLINIC_USERS_FILE"]
       and getattr(po, "_PORTAL_PUSH", False) and "portal_config" not in [k for k, v in sys.modules.items() if v is not None],
       "sign-in runs on the walk's own user store and its own random secret; the live portal_config.py was not loaded")
    w.live = load_as("ring_outcome_live", os.path.join(w.args.portal, "ring_outcome.py"))
    # the clock the walk gives the programs (India time). Everything in ring_outcome asks now_ist().
    w.real_now = ro.now_ist
    w.clock = [w.base]
    ro.now_ist = lambda: w.clock[0]
    # nothing may leave this machine: any attempt is counted, and refused
    w.net = []
    real_connect = socket.socket.connect

    def no_connect(self, addr, *a, **k):
        w.net.append(("socket", repr(addr)[:60]))
        raise OSError("walk_s497: no network")
    socket.socket.connect = no_connect
    w._real_connect = real_connect
    import urllib.request                                    # noqa: PLC0415
    real_open = urllib.request.urlopen

    def no_open(req, *a, **k):
        w.net.append(("urlopen", str(getattr(req, "full_url", req))[:60]))
        raise OSError("walk_s497: no network")
    urllib.request.urlopen = no_open
    w._real_open = real_open
    # every door ring_outcome opens on a database is watched: how it was opened, and which tables it read
    w.doors = []
    real_sql = ro.sqlite3

    class Watch(object):
        def __getattr__(self, k):
            return getattr(real_sql, k)

        def connect(self, target, *a, **k):
            con = real_sql.connect(target, *a, **k)
            if os.path.basename(str(target).split("?")[0]) == "finance.db":
                rec = {"target": str(target), "uri": bool(k.get("uri")), "tables": set(), "writes": 0}
                w.doors.append(rec)

                def auth(action, a1, a2, dbn, src, rec=rec):
                    if action == real_sql.SQLITE_READ:
                        rec["tables"].add(a1)
                    elif action in (real_sql.SQLITE_INSERT, real_sql.SQLITE_UPDATE, real_sql.SQLITE_DELETE, real_sql.SQLITE_CREATE_TABLE,
                                    real_sql.SQLITE_DROP_TABLE, real_sql.SQLITE_ALTER_TABLE, real_sql.SQLITE_CREATE_INDEX):
                        rec["writes"] += 1
                    return real_sql.SQLITE_OK
                con.set_authorizer(auth)
            return con
    ro.sqlite3 = Watch()


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
    ok(all(w.tok.values()) and len(w.tok) == 6,
       "six logins sign in through the real /portal/login: alisha, shivani, shavez, reception, the doctor (manoj), and darpan who must not see the tile",
       {u: bool(t) for u, t in w.tok.items()})
    r = w.pc.get("/portal/ring/list", base_url=BASE)
    ok(r.status_code == 302 and "/portal/login" in r.headers.get("Location", ""), "with no sign-in the list's address sends a stranger to the login (302)", r.status_code)


def GET(w, user, path):
    r = w.pc.get(path, base_url=BASE, headers={"Cookie": "clinic_sso=" + w.tok[user]})
    if path == "/portal" and r.status_code in (301, 308) and r.headers.get("Location", "").rstrip("/").endswith("/portal"):
        r = w.pc.get("/portal/", base_url=BASE, headers={"Cookie": "clinic_sso=" + w.tok[user]})    # an older Flask sends /portal on to /portal/
    return r.status_code, r.get_data(as_text=True)


def POST(w, user, path, js=None, form=None):
    h = {"Cookie": "clinic_sso=" + w.tok[user]}
    r = w.pc.post(path, base_url=BASE, headers=h, json=js) if js is not None else w.pc.post(path, base_url=BASE, headers=h, data=form or {})
    j = r.get_json(silent=True) or {}
    return r.status_code, j, r.headers.get("Location", "")


def at(w, days_ago, clock="12:00"):
    hh, mm = clock.split(":")
    d = w.today - timedelta(days=days_ago)
    return datetime(d.year, d.month, d.day, int(hh), int(mm), tzinfo=IST)


def vrow(w, cid, d, fp=""):
    """One made-up visit in the made-up Docterz table."""
    con = sqlite3.connect(w.fin)
    w.vn += 1
    con.execute("INSERT INTO patient_visit (visit_id, visit_date, clinic_id, patient_uid, mobile_fp, had_procedure) VALUES (?,?,?,?,?,?)",
                ("W497V%04d" % w.vn, d.isoformat(), cid, "W497U" + cid, fp, ""))
    con.commit()
    con.close()


def prow(w, cid, name, mobile, last_seen=None):
    con = sqlite3.connect(w.fin)
    con.execute("INSERT INTO patient_ref (clinic_id, name, mobile_fp, patient_uid, last_seen) VALUES (?,?,?,?,?)",
                (cid, name, w.fp(mobile), "W497U" + cid, last_seen.isoformat() if last_seen else ""))
    con.commit()
    con.close()


def ring(w, sid, mobile, login, when, code="appointment_booked", note_="", file_it=True):
    """One call as ring_hook records it -- dial, answer, end -- then, unless told not to, the tap."""
    ro, rc = w.ro, w.rc
    who = {login: PEOPLE[login]}
    ro.record_call(sid, mobile, rc.lookup_caller(mobile), who)
    ro.record_answered(sid, login)
    ro.record_end(sid, "answered", who, [login])
    if file_it:
        good, msg, row = ro.file_outcome(sid, code, login, PEOPLE[login], note_, now=when)
        if not good:
            raise RuntimeError("the tap was refused for %s: %s" % (sid, msg))
        return row


def make_mockup_day(w):
    """The owner's mock-up, line for line, built around the walk's day: seven known patients, three new numbers."""
    ro, rc = w.ro, w.rc
    w.taken, w.vn = set(), 0
    w.fp = lambda m: sys.modules["finance_patient_match"].fingerprint(m, os.environ["W497_SALT"]) if "finance_patient_match" in sys.modules \
        else hashlib.sha256(("%s|%s" % (os.environ["W497_SALT"], m)).encode("utf-8")).hexdigest()[:32]
    agents = {number(w.taken): {"user": u, "name": n} for u, n in PEOPLE.items()}
    json.dump({"agents": agents}, open(os.environ["RING_AGENTS_FILE"], "w"))
    w.mob, w.sid = {}, {}
    for key, (name, cid, last) in PATIENTS.items():
        w.mob[key] = number(w.taken)
        prow(w, cid, name, w.mob[key])
        vrow(w, cid, w.today - timedelta(days=last), w.fp(w.mob[key]))      # the visit BEFORE the call: 'pichhli visit', never 'aaye'
    for key, ago, clock, login, pat, promised, note_ in MOCK:
        m = w.mob[pat] if pat else number(w.taken)
        w.mob[key], w.sid[key] = m, "w497-" + key
        if key == "r4":
            ring(w, w.sid[key], m, login, None, file_it=False)                # r4's tap is made through the real page, below
            continue
        ring(w, w.sid[key], m, login, at(w, ago, clock), note_=note_)
        if promised is not None and not w.args.control:
            good, msg = ro.set_appt_day(w.sid[key], (w.today + timedelta(days=promised)).isoformat(), login, PEOPLE[login], now=at(w, ago, clock))
            if not good:
                raise RuntimeError("the day was refused for %s: %s" % (key, msg))
    # two calls that are NOT appointments, and one name with the letters S-I-D (F-797)
    w.mob["sid"] = number(w.taken)
    prow(w, "7001", "SIDDIQUI AHMED", w.mob["sid"])
    ring(w, "w497-x1", w.mob["sid"], "shavez", at(w, 0, "09:05"), code="K_CALL_AGAIN", note_="<script>x</script>")
    ring(w, "w497-x2", w.mob["sid"], "shivani", None, file_it=False)
    # what Docterz shows afterwards
    for key, ago in MOCK_VISIT.items():
        pat = [r[4] for r in MOCK if r[0] == key][0]
        if pat:
            vrow(w, PATIENTS[pat][1], w.today - timedelta(days=ago), w.fp(w.mob[key]))
        else:
            name, cid = MOCK_NEW[key]
            prow(w, cid, name, w.mob[key])
            vrow(w, cid, w.today - timedelta(days=ago), w.fp(w.mob[key]))


# ============================================================================================ PART 1 -- the mock-up's day
EXPECT_HEADS = [["Kab book hua", "Mareez", "Mobile", "Kis din aana tha", "Kisne book kiya", "Note", "WhatsApp", "Ab kya karna hai"],
                ["Kab book hua", "Mareez", "Mobile", "Kis din aana hai", "Kisne book kiya", "Note", "WhatsApp"],
                ["Kab book hua", "Mareez", "Mobile", "Kis din aana tha", "Aaye (Docterz)", "Kisne book kiya"]]
WA_CELL = "WhatsApp message jald — abhi band"
BUTTONS = "Phir call kiya — naya din Ab nahi aayenge"


def expect_rows(w):
    """The thirty-odd cells of the mock-up, with this walk's dates and this run's numbers."""
    T, d = w.today, lambda n: w.today - timedelta(days=n)
    return [
        [[dm(d(4)) + " · 11:20", "Rajesh Kumar ID 4521 · pichhli visit " + dm(d(35)), spaced(w.mob["r1"]), dmw(d(2)) + " 2 din ho gaye", "Shivani", "ghutne ka dard", WA_CELL, BUTTONS],
         [dm(d(5)) + " · 17:45", "Naya number Docterz mein abhi koi record nahi", spaced(w.mob["r2"]), dmw(d(4)) + " 4 din ho gaye", "Alisha", "kandhe ki chot, surgery puchh rahe the", WA_CELL, BUTTONS],
         [dm(d(6)) + " · 10:05", "Meena Devi ID 3310 · pichhli visit " + dm(d(57)), spaced(w.mob["r3"]), "din nahi likha 6 din ho gaye", "Shavez", "—", WA_CELL, BUTTONS]],
        [[dm(T) + " · 10:15", "Suresh Pal ID 2207 · pichhli visit " + dm(d(80)), spaced(w.mob["r4"]), dmw(d(-1)) + " · kal", "Alisha", "kal 11 baje", WA_CELL],
         [dm(T) + " · 09:40", "Naya number Docterz mein abhi koi record nahi", spaced(w.mob["r5"]), dmw(T) + " · aaj", "Shivani", "shaam ko aayenge", WA_CELL],
         [dm(d(1)) + " · 18:30", "Imran Khan ID 5108 · pichhli visit " + dm(d(9)), spaced(w.mob["r6"]), dmw(d(-2)), "Reception", "—", WA_CELL]],
        [[dm(d(2)) + " · 12:02", "Ramesh Gangwar ID 4890", spaced(w.mob["r7"]), dmw(d(1)), "Aaye · " + dm(d(1)), "Shavez"],
         [dm(d(2)) + " · 10:48", "Sunita Devi call ke samay naya number tha · ab ID 9917", spaced(w.mob["r8"]), dmw(d(2)), "Aaye · " + dm(d(2)), "Shivani"],
         [dm(d(4)) + " · 16:10", "Mohd. Arif ID 3077", spaced(w.mob["r9"]), dmw(d(2)), "Aaye · " + dm(d(1)) + " 1 din baad", "Alisha"],
         [dm(d(5)) + " · 11:30", "Kamla Rani ID 1456", spaced(w.mob["r10"]), "din nahi likha", "Aaye · " + dm(d(4)), "Reception"]]]


def part_1(w):
    ro, live = w.ro, w.live
    db = os.environ["RING_OUTCOME_DB"]
    # ---- the list is OFF: what each login is shown
    ok(ro.list_on() is False, "INSTALLED OFF FOR STAFF: with nothing pressed, the switch reads off")
    homes = {u: GET(w, u, "/portal") for u in USERS}
    ok(all(c == 200 for c, _h in homes.values()), "every login's portal home answers 200", {u: c for u, (c, _h) in homes.items()})
    ok(all(TILE not in tiles(homes[u][1]) and "Call Tracker" in tiles(homes[u][1]) for u in FOUR),
       "while it is off: alisha, shivani, shavez and reception are NOT drawn the tile (their Call Tracker tile is there as before)",
       {u: TILE in tiles(homes[u][1]) for u in FOUR})
    td = tiles(homes["manoj"][1])
    ok(TILE in td and td[td.index(TILE) - 1] == "Call Tracker" and 'href="/portal/ring/list"' in homes["manoj"][1],
       "the doctor's home has the tile 'Call ke baad', right after Call Tracker, opening /portal/ring/list", td[:8])
    ok(TILE not in tiles(homes["darpan"][1]), "darpan, who does not hold Call Tracker, is not drawn it")
    bad = []
    for u in FOUR:
        c, h = GET(w, u, "/portal/ring/list")
        if not (c == 200 and "Yeh list abhi band hai. Dr sahab chalu karenge." in h and "<table>" not in h and "switch" not in h):
            bad.append((u, c))
    ok(not bad, "while it is off, each of the four (typing the address) reads 'Yeh list abhi band hai. Dr sahab chalu karenge.' and no list", bad)
    c, h = GET(w, "darpan", "/portal/ring/list")
    ok(c == 403 and "aapke login ke liye nahi" in h and "<table>" not in h, "darpan is refused the page (403)", c)
    # ---- the tap's own page while off: byte for byte the live page, but for the S-I-D name
    same, mended = 0, 0
    sids = [w.sid[k] for k in ("r1", "r2", "r4", "r7")] + ["w497-x1", "w497-x2", "w497-nope"]
    for sid in sids:
        cl = ro.get_call(sid)
        o = ro.get_outcome(sid) if cl else None
        a, b = live.render_page(cl, o, sid), ro.render_page(cl, o, sid)
        if a == b:
            same += 1
        elif sid in ("w497-x1", "w497-x2") and "SIDDIQUI AHMED" in b and "SIDDIQUI AHMED" not in a:
            mended += 1
    ok(same == 5 and mended == 2, "the tap's page (render_page): 5 of 7 calls byte for byte the live page; the other two are the ones the live page "
       "BREAKS -- a name written with the letters S-I-D -- and the kit shows the name whole (F-797)", (same, mended))
    c, h = GET(w, "shivani", "/portal/ring/outcome?s=w497-x2")
    ok(c == 200 and "SIDDIQUI AHMED" in h and '{s:"w497-x2",code:' in h and "go('appointment_booked')" in h,
       "…served to shivani: the name whole, the call's id in the page's script, the buttons as before")
    c, h = GET(w, "shivani", "/portal/ring/outcome?s=%3C/script%3E%3Cb%3Ex")
    ok(c == 200 and "</script><b>x" not in h, "…and an address that carries '</script>' cannot close the page's script early")
    # ---- r4: the tap, through the real page, while the list is off
    w.clock[0] = at(w, 0, "10:15")
    before_tap = live.render_page(ro.get_call(w.sid["r4"]), None, w.sid["r4"])
    c, h = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    ok(c == 200 and h == before_tap, "r4 before the tap: alisha's page is byte for byte the live page (the six buttons, the note box)")
    c, j, _l = POST(w, "alisha", "/portal/ring/outcome", js={"s": w.sid["r4"], "code": "appointment_booked", "note": "kal 11 baje"})
    quiet()
    w.clock[0] = w.base
    o4 = ro.get_outcome(w.sid["r4"])
    ok(c == 200 and j.get("ok") is True and o4 and o4["code"] == "appointment_booked" and o4["handler"] == "Alisha" and o4["detail"] == "kal 11 baje",
       "alisha taps 'Appointment book ho gaya' on the real page: filed once, by Alisha, with her note", (c, j))
    c, h = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    ok(c == 200 and h == live.render_page(ro.get_call(w.sid["r4"]), ro.get_outcome(w.sid["r4"]), w.sid["r4"]) and "Kis din aayenge" not in h,
       "while the list is off her card after the tap is byte for byte the OLD card -- no day question, no link")
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": (w.today + timedelta(days=1)).isoformat()})
    ok(c == 403 and not (ro.get_outcome(w.sid["r4"]).get("appt_day") or ""), "…and while it is off a staff login cannot set a day (403)", (c, j))
    # ---- the doctor, while off
    c, hd = GET(w, "manoj", "/portal/ring/list")
    ok(c == 200 and "Shown to staff: <b>OFF</b>" in hd and 'action="/portal/ring/list/switch"' in hd and "Turn it on for staff" in hd,
       "THE OWNER'S SWITCH: the doctor opens the page while it is off -- his box reads OFF and carries the switch", (c, hd[:200]))
    ok("The tile is hidden from staff until you turn this on." in text_of(hd) and "For nobody" not in hd and "alisha, reception" not in hd,
       "[M3] …and says 'The tile is hidden from staff until you turn this on.' -- no small-letter login is printed", text_of(hd)[:200])
    ok("Nahi aaye — appointment liya tha" in hd and len(tables(hd)) == 3, "…and under his box he sees the staff's page itself, three parts")
    unset = not sqlite3.connect(db).execute("SELECT COUNT(*) FROM kv WHERE k='wait_days'").fetchone()[0]
    ok(unset and ro.wait_days() == 3 and 'name="wait_days" min="1" max="30" value="3"' in hd and "Din na likha ho to 3 din baad." in text_of(hd),
       "with NOTHING ever set, a booking with no day waits 3 days: his box shows 3 and the page's foot says 3")
    lines = lambda page: [len(t[1]) if (t[1] and len(t[1][0]) > 1) else 0 for t in tables(page)]      # noqa: E731
    old_ones = [spaced(w.mob[k]) for k in ("r1", "r2", "r3", "r6", "r7", "r8", "r9", "r10")]
    ok(lines(hd) == [0, 2, 0] and not [m for m in old_ones if m in hd] and asks(ro, "switch_on_day")() is None and asks(ro, "floor_day")() == w.today,
       "[B1 s1.py] BEFORE IT HAS EVER BEEN ON he is shown what the staff WOULD be shown if he turned it on now: only the two "
       "appointments filed today -- not one of the eight filed on earlier days", lines(hd))
    # ---- his box opened just before India midnight, Saved just after it, the date field untouched
    y = w.today - timedelta(days=1)
    w.clock[0] = datetime(y.year, y.month, y.day, 23, 59, 30, tzinfo=IST)
    c, hy = GET(w, "manoj", "/portal/ring/list")
    shown = re.findall(r'<input type="date" name="follow_from" min="[^"]*" value="([^"]*)"', hy)
    form = {"wait_days": "3", "follow_from": shown[0] if shown else ""}
    form.update(dict(re.findall(r'<input type="hidden" name="(follow_shown)" value="([^"]*)"', hy)))
    w.clock[0] = datetime(w.today.year, w.today.month, w.today.day, 0, 0, 30, tzinfo=IST)
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form=form)
    w.clock[0] = w.base
    ok(shown == [y.isoformat()] and loc.endswith("?m=saved") and ro.follow_from() == "" and asks(ro, "floor_day")() == w.today,
       "[D4 delta] his box opened at 23:59 India time showed %s; Saved at 00:00 with the date untouched, it does NOT make yesterday his own "
       "date -- his setting stays empty and the day in force is today" % dm(y), (shown, loc, ro.follow_from()))
    c, j, _l = POST(w, "shivani", "/portal/ring/list/switch", form={"on": "1"})
    ok(c == 403 and ro.list_on() is False, "a staff login cannot turn it on (403)", c)
    c, j, loc = POST(w, "manoj", "/portal/ring/list/switch", form={"on": "1"})
    ok(c == 302 and loc.endswith("/portal/ring/list?m=on") and ro.list_on() is True, "the doctor turns it on", (c, loc))
    # ---- B1: the first morning. Eight appointments were filed on earlier days and nobody ever pressed anything on them.
    kv = dict((k, v) for k, v, _b in sqlite3.connect(db).execute("SELECT k, v, by_whom FROM kv").fetchall())
    ok(kv.get("switch_on_day") == w.today.isoformat() and asks(ro, "switch_on_day")() == w.today and ro.follow_from() == "" and asks(ro, "floor_day")() == w.today,
       "[B1 s1.py] the FIRST time it is turned on, that India day is written once under its own key (switch_on_day); with his own "
       "setting empty, that day is the first booking day the list follows", kv)
    stale = {}
    for span in ("aaj", "7", "30"):
        c, hs = GET(w, "shivani", "/portal/ring/list?d=" + span)
        stale[span] = (c, lines(hs), [m for m in old_ones if m in hs], hs.count(">Ab nahi aayenge</button>"))
    ok(all(v == (200, [0, 2, 0], [], 0) for v in stale.values()),
       "[B1 s1.py] NO OLD LINE MEETS THE STAFF: on the first morning, under Aaj, 7 din and 30 din alike, shivani's page holds the two "
       "appointments filed today and nothing else -- Nahi aaye (0), no button, none of the eight earlier numbers", stale)
    oid1 = sqlite3.connect(db).execute("SELECT id FROM outcome WHERE sid=?", (w.sid["r1"],)).fetchone()[0]
    kal_ = (w.today + timedelta(days=1)).isoformat()
    got = [POST(w, "shivani", "/portal/ring/list/act", js={"id": oid1, "act": "closed"})[:2],
           POST(w, "shivani", "/portal/ring/list/act", js={"id": oid1, "act": "recall", "day": kal_})[:2],
           POST(w, "shivani", "/portal/ring/appt", js={"s": w.sid["r1"], "day": kal_})[:2]]
    o1 = ro.get_outcome(w.sid["r1"])
    c, hc1 = GET(w, "shivani", "/portal/ring/outcome?s=" + w.sid["r1"])
    ok(all(c_ == 404 and j_.get("ok") is False for c_, j_ in got) and (o1.get("appt_state") or "") == "" and o1["appt_day"] == (w.today - timedelta(days=2)).isoformat()
       and not (o1.get("recalls") or 0) and "Kis din aayenge" not in hc1
       and hc1 == live.render_page(ro.get_call(w.sid["r1"]), ro.get_outcome(w.sid["r1"]), w.sid["r1"]),
       "[B1 s1.py] …and an appointment booked before that day cannot be pressed either: 'Ab nahi aayenge', 'Phir call kiya' and the "
       "card's day are each refused (404), nothing is written, and its card is byte for byte the old card", (got, o1.get("appt_state")))
    c, hd = GET(w, "manoj", "/portal/ring/list?m=on")
    fld = re.findall(r'<input type="date" name="follow_from" min="([^"]*)" value="([^"]*)"', hd)
    ok(fld == [(HARD.isoformat(), w.today.isoformat())] and "(empty = all)" not in hd
       and ("You may move it earlier, back to %s and no further. Emptied, it returns to the day the list was first turned on (%s)." % (hard_words(), dmw(w.today))) in text_of(hd),
       "[B1 s1.py] HIS BOX shows the day in force (today), no longer says '(empty = all)', and says in plain English that he may move it "
       "earlier, back to %s and no further, and where it returns when emptied" % hard_words(), fld)
    six = (w.today - timedelta(days=6)).isoformat()
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": (HARD - timedelta(days=1)).isoformat()})
    ok(loc.endswith("?m=bad") and ro.follow_from() == "" and asks(ro, "floor_day")() == w.today
       and ("the date not before %s." % hard_words()) in text_of(GET(w, "manoj", "/portal/ring/list?m=bad")[1]),
       "[B1 s1.py] a day before %s is refused, and his box says why" % hard_words(), loc)
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": six})
    ok(loc.endswith("?m=saved") and ro.follow_from() == six and asks(ro, "floor_day")() == w.today - timedelta(days=6) and asks(ro, "switch_on_day")() == w.today,
       "[B1 s1.py] HE moves it earlier than the switch-on day, to six days ago (his choice, in his box): from here on the made-up "
       "day is the mock-up's -- the ten appointments are followed", (loc, ro.follow_from()))
    # ---- ON: the homes
    homes = {u: GET(w, u, "/portal") for u in USERS}
    bad = []
    for u in FOUR:
        t = tiles(homes[u][1])
        if not (homes[u][0] == 200 and t.count(TILE) == 1 and t[t.index(TILE) - 1] == "Call Tracker"
                and re.search(r'<a class="tile" href="/portal/ring/list"[^>]*>\s*<div class="ic">[^<]+</div>\s*<div class="tx"><div class="nm">Call ke baad</div>', homes[u][1])):
            bad.append((u, t[:6]))
    ok(not bad, "once on, the home of each of alisha, shivani, shavez and reception has the tile 'Call ke baad' once, right after Call Tracker, opening /portal/ring/list", bad)
    ok(TILE not in tiles(homes["darpan"][1]) and TILE in tiles(homes["manoj"][1]), "…darpan's home still has none; the doctor's still has it")
    w.screen1 = homes["alisha"][1]
    # ---- ON: the card after the tap
    c, h = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    tx = text_of(h)
    ok(c == 200 and "Likh gaya — Appointment book ho gaya" in tx and "Suresh Pal · ID 2207" in tx
       and "%s · %s 10:15 · Alisha" % (spaced(w.mob["r4"]), dm(w.today)) in tx,
       "THE CARD AFTER THE TAP (alisha, r4): 'Likh gaya — Appointment book ho gaya' · the name and ID · the FULL number, when, who", tx[:200])
    days = re.findall(r'<button type="button" data-day="([^"]*)" onclick="s497day\(this\)" style="([^"]*)">([^<]+)</button>', h)
    ok([d[2] for d in days] == ["Aaj", "Kal", "Parso"] and [d[0] for d in days] == [(w.today + timedelta(days=i)).isoformat() for i in range(3)]
       and "Kis din aayenge?" in tx and re.search(r'onclick="s497other\(\)"[^>]*>Aur din chuniye</button>', h) and all("#2563eb" not in d[1] for d in days),
       "…the ONE optional tap 'Kis din aayenge?': Aaj · Kal · Parso · Aur din chuniye, each carrying its India-time date; none chosen yet", days)
    ok("Zaroori nahi hai. Din na batayein to 3 din tak intezaar hoga, phir mareez “Nahi aaye” mein dikhega." in tx
       and "Note (chahein to)" in tx and re.search(r'<input id="note" type="text" value="kal 11 baje"', h),
       "…'Zaroori nahi hai …' in the mock-up's words; the note stays, in its box")
    ok("Mareez ko WhatsApp par appointment ka message" in tx and "Jald — abhi band. Chalu hone par din chunte hi clinic ke WhatsApp number se jayega." in tx
       and re.search(r'<a href="/portal/ring/list\?d=aaj"[^>]*>Aaj ki list dekho</a>', h),
       "…the WhatsApp place, switched off, in the mock-up's words; the link 'Aaj ki list dekho'")
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": (w.today + timedelta(days=1)).isoformat(), "note": "kal 11 baje"})
    o4 = ro.get_outcome(w.sid["r4"])
    ok(c == 200 and j.get("ok") is True and o4["appt_day"] == (w.today + timedelta(days=1)).isoformat() and o4["appt_day_by"] == "alisha",
       "she taps Kal: the day is written on the appointment, with who and when", (c, j, o4.get("appt_day")))
    c, h = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    days = re.findall(r'<button type="button" data-day="([^"]*)" onclick="s497day\(this\)" style="([^"]*)">([^<]+)</button>', h)
    ok(len(days) == 3 and "#2563eb" in days[1][1] and "#2563eb" not in days[0][1] and "#2563eb" not in days[2][1],
       "…and the card now shows Kal chosen, as the mock-up draws it", [(d[2], "#2563eb" in d[1]) for d in days])
    w.screen3 = h
    ok(not re.search(u"[\u0900-\u097f]", h), "…the card is in Roman letters throughout (no Devanagari)")
    c, h = GET(w, "darpan", "/portal/ring/outcome?s=" + w.sid["r4"])
    ok(c == 200 and "Kis din aayenge" not in h, "…a login that does not hold the tile still gets the old card")
    c, h = GET(w, "shavez", "/portal/ring/outcome?s=w497-x1")
    ok(c == 200 and h == live.render_page(ro.get_call("w497-x1"), ro.get_outcome("w497-x1"), "w497-x1").replace(
        "SIDDIQUI AHMED".replace("SID", '"w497-x1"'), "SIDDIQUI AHMED") and "Kis din aayenge" not in h,
       "…and an outcome that is not an appointment keeps its old card (the live page, with the name whole)")
    # ---- he turns it off again, and on
    c, j, loc = POST(w, "manoj", "/portal/ring/list/switch", form={"on": "0"})
    c2, hoff = GET(w, "manoj", "/portal/ring/list")
    seen_off = (GET(w, "shivani", "/portal/ring/list")[1], GET(w, "shivani", "/portal")[1], GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])[1])
    kv = sqlite3.connect(db).execute("SELECT k, v, by_whom FROM kv ORDER BY k").fetchall()
    ok(c == 302 and loc.endswith("?m=off") and ro.list_on() is False and "Shown to staff: <b>OFF</b>" in hoff and "Turned off." in GET(w, "manoj", "/portal/ring/list?m=off")[1]
       and "abhi band hai" in seen_off[0] and TILE not in tiles(seen_off[1]) and "Kis din aayenge" not in seen_off[2]
       and kv == [("follow_from", six, "manoj"), ("list_on", "0", "manoj"), ("switch_on_day", w.today.isoformat(), "manoj"), ("wait_days", "3", "manoj")]
       and ro.get_outcome(w.sid["r4"])["appt_day"] == (w.today + timedelta(days=1)).isoformat(),
       "he turns it OFF again: at once the staff lose the tile, the page and the card's new part; what was written stays; the switch row says who", (c, loc, kv))
    w.screen4 = hoff
    c, j, loc = POST(w, "manoj", "/portal/ring/list/switch", form={"on": "1"})
    ok(c == 302 and ro.list_on() is True, "…and ON again", c)
    # ---- ON: the staff's table, line for line
    before = table_print(db)
    fin_before = md5f(w.fin)
    c, h = GET(w, "shivani", "/portal/ring/list")
    w.screen2 = h
    tx = text_of(h)
    ok(c == 200 and "<h1" in h and "Call ke baad — appointment list" in text_of(re.findall(r"(?s)<h1[^>]*>(.*?)</h1>", h)[0]) and "For you only" not in h
       and "switch" not in h, "THE STAFF'S PAGE (shivani): 'Call ke baad — appointment list'; no owner's box, no switch", (c, tx[:120]))
    pills = re.findall(r'<a href="/portal/ring/list\?d=([^"]+)" style="([^"]*)">([^<]+)</a>', h)
    ok([p[2] for p in pills] == ["Aaj", "7 din", "30 din"] and ["#2563eb" in p[1] for p in pills] == [False, True, False],
       "the spans Aaj · 7 din · 30 din; opened from the tile it is on 7 din", pills and [(p[2], "#2563eb" in p[1]) for p in pills])
    i1, i2, i3 = (tx.find(x) for x in ("Nahi aaye — appointment liya tha, Docterz mein visit nahi mili (3)", "Aane baaki — din abhi aaya nahi ya aaj hai (3)",
                                         "Aa gaye — Docterz ke export se pakka (4)"))
    ok(0 < i1 < i2 < i3, "THREE PARTS IN THE MOCK-UP'S ORDER, with its headings and counts: Nahi aaye (3) on top, Aane baaki (3), Aa gaye (4)", (i1, i2, i3))
    ok("border: 2px solid #b45309" in h and h.find("border: 2px solid #b45309") < h.find("border: 1px solid #2563eb; border-radius: 14px; padding: 14px 16px 6px"),
       "…Nahi aaye is set apart: the heavy amber frame, above the others")
    ok("3 Nahi aaye 3 Aane baaki 4 Aa gaye" in tx, "the three counts on top: 3 Nahi aaye · 3 Aane baaki · 4 Aa gaye", tx[:200])
    ok("Yeh line tab tak yahin rahegi jab tak mareez aa na jaye ya aap neeche ka ek button na dabayein" in tx
       and "Yahan kisi ko kuch tick nahi karna — yeh apne aap bharta hai" in tx, "the two side lines, in the mock-up's words")
    tb = tables(h)
    ok([t[0] for t in tb] == EXPECT_HEADS, "THE COLUMNS, and their order, in each of the three parts, as drawn", [t[0] for t in tb])
    want = expect_rows(w)
    got = [[[seen(cell) for cell in row] for row in t[1]] for t in tb]
    for pi, pname in enumerate(("Nahi aaye", "Aane baaki", "Aa gaye")):
        if len(got) > pi and got[pi] == want[pi]:
            ok(True, "%s: %d lines, newest booking first, every cell as the mock-up draws it" % (pname, len(want[pi])))
        else:
            bad = [(g, x) for g, x in zip(sum(got[pi] if len(got) > pi else [], []), sum(want[pi], [])) if g != x][:2]
            ok(False, "%s: every cell as the mock-up draws it" % pname, bad or (len(got[pi]) if len(got) > pi else "no table"))
    ok(all(re.search(r'<a href="tel:\+91%s">%s</a>' % (w.mob[k], spaced(w.mob[k])), h) for k in ("r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10")),
       "FULL NUMBERS: all ten mobiles are shown whole (5+5), each a link that dials it -- none masked")
    wd = re.findall(r"(\d\d)-([A-Z][a-z]{2}) \((\w+)\)", tx)
    ok(len(wd) >= 7 and all(x[2] in DOW_FROM_WED for x in wd) and dmw(w.today - timedelta(days=2)) in tx,
       "WEEKDAYS IN ENGLISH (Mon … Sun), each the right one for its date", wd[:4])
    ok(not re.search(u"[\u0900-\u097f]", h), "the page is in Roman letters throughout (no Devanagari)")
    n_btn = (h.count(">Phir call kiya — naya din</button>"), h.count(">Ab nahi aayenge</button>"))
    ok(n_btn == (3, 3) and all(len(r) == 8 for r in tb[0][1]) and all(BUTTONS not in seen(c) for t in tb[1:] for r in t[1] for c in r),
       "THE TWO BUTTONS on each Nahi aaye line, and on no other line", n_btn)
    wa = re.findall(r'<button type="button" disabled style="[^"]*">WhatsApp message</button>', h)
    ok(len(wa) == 6 and "WhatsApp" not in tb[2][0] and "onclick" not in "".join(wa),
       "THE WHATSAPP PLACE: a column in Nahi aaye and Aane baaki; its button is there, disabled, wired to nothing ('jald — abhi band')", len(wa))
    how = ["Yeh list kaise bharti hai", "Call ke baad notification par “Appointment book ho gaya” dabate hi mareez “Aane baaki” mein aa jata hai.",
           "Docterz ka roz ka export aate hi jis mareez ki visit mil jati hai, woh apne aap “Aa gaye” mein chala jata hai.",
           "WhatsApp: mareez ko appointment ka message clinic ke WhatsApp number se bhejne ki jagah rakhi gayi hai. Abhi band hai; chalu hone par yahin se jayega aur “bheja gaya” yahin dikhega.",
           "Jis din aana tha uske agle din tak visit na mile to mareez “Nahi aaye” mein aa jata hai. Din na likha ho to 3 din baad."]
    ok(all(x in tx for x in how) and tx.find(how[0]) > i3, "'Yeh list kaise bharti hai' and its four lines, word for word, at the foot")
    ok("K_CALL_AGAIN" not in h and "SIDDIQUI" not in h and "&lt;script&gt;" not in h, "an outcome that is not an appointment is not on this page")
    bad = [u for u in ("alisha", "shavez", "reception") if GET(w, u, "/portal/ring/list") != (200, h)]
    ok(not bad, "alisha, shavez and reception read the same page, byte for byte", bad)
    c2, hd = GET(w, "manoj", "/portal/ring/list")
    ok(c2 == 200 and "Shown to staff: <b>ON</b>" in hd and "Turn it off for staff" in hd and hd.replace(hd[hd.find('  <div style="background: #1e293b; border: 1px dashed'):hd.find('  <div style="background: #1e293b; border: 1px solid #334155; border-radius: 14px; padding: 16px 18px;')], "") == h,
       "the doctor's page is the staff's page, byte for byte, with his own box on top (now reading ON)")
    c2, h2 = GET(w, "darpan", "/portal/ring/list")
    ok(c2 == 403, "darpan is still refused (403)", c2)
    c, ha = GET(w, "shivani", "/portal/ring/list?d=aaj")
    ta = tables(ha)
    ok(c == 200 and len(ta[0][1]) == 3 and [seen(r[1]).split(" ID")[0] for r in ta[1][1]] == ["Suresh Pal", "Naya number Docterz mein abhi koi record nahi"]
       and seen(ta[2][1][0][0]) == "—" and "(0)" in text_of(ha),
       "Aaj: Nahi aaye keeps all its three lines WHATEVER THE SPAN; Aane baaki shows only the two booked today; Aa gaye is empty", [len(t[1]) for t in ta])
    c, hm = GET(w, "shivani", "/portal/ring/list?d=30")
    c2, hz = GET(w, "shivani", "/portal/ring/list?d=zzz")
    ok(c == 200 and [len(t[1]) for t in tables(hm)] == [3, 3, 4] and c2 == 200 and hz == h, "30 din holds the same ten; an address typed wrong falls back to 7 din")
    c, hk = GET(w, "manoj", "/portal/ring/counts")
    ok(c == 200 and "Calls" in hk and "<td>shivani</td>" in hk, "the doctor's counts page answers as before")
    quiet()
    ok(table_print(db) == before and md5f(w.fin) == fin_before,
       "READING WROTE NOTHING: after all these pages the calls, the outcomes, the history and the settings are what they were, and the Docterz file's bytes are unchanged")


# ============================================================================================ PART 2 -- what a person presses
def part_2(w):
    ro = w.ro
    db = os.environ["RING_OUTCOME_DB"]
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    oid = {k: con.execute("SELECT id FROM outcome WHERE sid=?", (w.sid[k],)).fetchone()[0] for k in ("r1", "r2", "r3", "r6", "r7")}
    q = lambda s, *a: [dict(r) for r in con.execute(s, a).fetchall()]          # noqa: E731
    kal = (w.today + timedelta(days=1)).isoformat()
    # ---- Phir call kiya — naya din
    c, h = GET(w, "shivani", "/portal/ring/list")
    row2 = [r for r in re.findall(r"(?s)<tr>(.*?)</tr>", h) if spaced(w.mob["r2"]) in r][0]
    pick = re.findall(r'<button type="button" data-id="(\d+)" data-day="([^"]+)" onclick="s497day\(this\)"[^>]*>([^<]+)</button>', row2)
    ok([p[2] for p in pick] == ["Aaj", "Kal", "Parso"] and [p[1] for p in pick] == [(w.today + timedelta(days=i)).isoformat() for i in range(3)]
       and all(int(p[0]) == oid["r2"] for p in pick) and "Aur din chuniye" in row2 and 'data-s497-pick style="display: none' in row2
       and re.search(r'<input type="date" data-id="%d" min="%s" max="%s"' % (oid["r2"], w.today.isoformat(), (w.today + timedelta(days=366)).isoformat()), row2),
       "'Phir call kiya — naya din' opens the same four choices as the card -- Aaj · Kal · Parso · Aur din chuniye -- closed until pressed", pick)
    c, j, _l = POST(w, "darpan", "/portal/ring/list/act", js={"id": oid["r2"], "act": "recall", "day": kal})
    ok(c == 403 and not q("SELECT 1 FROM appt_event WHERE outcome_id=? AND kind='recall'", oid["r2"]), "darpan cannot press it (403)", c)
    c, j, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r2"], "act": "recall", "day": (w.today - timedelta(days=1)).isoformat()})
    ok(c == 400 and j.get("ok") is False and "aaj ya aage ka din" in j.get("msg", "") and q("SELECT appt_day FROM outcome WHERE id=?", oid["r2"])[0]["appt_day"] == (w.today - timedelta(days=4)).isoformat(),
       "a day already gone is refused (400) in plain words and nothing is written", (c, j))
    c, j, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r2"], "act": "recall", "day": kal})
    o = q("SELECT * FROM outcome WHERE id=?", oid["r2"])[0]
    ev = q("SELECT * FROM appt_event WHERE outcome_id=? ORDER BY id", oid["r2"])
    ok(c == 200 and j.get("ok") is True and o["appt_day"] == kal and o["recalls"] == 1 and o["appt_day_by"] == "shivani" and (o["recall_at"] or "")[:10] == w.today.isoformat(),
       "shivani presses 'Phir call kiya' → Kal on r2: the store holds the NEW promised day, one recall, who and when", (j, o.get("appt_day"), o.get("recalls")))
    ok([(e["kind"], e["old_value"], e["new_value"], e["by_login"], e["by_name"]) for e in ev]
       == [("day", "", (w.today - timedelta(days=4)).isoformat(), "alisha", "Alisha"), ("recall", (w.today - timedelta(days=4)).isoformat(), kal, "shivani", "Shivani")],
       "…THE EARLIER DAY IS KEPT AS HISTORY: appt_event holds the first day (by Alisha) and the recall from it to the new one (by Shivani)", ev)
    c, h = GET(w, "shivani", "/portal/ring/list")
    tb = tables(h)
    ok([len(t[1]) for t in tb] == [2, 4, 4] and spaced(w.mob["r2"]) not in "".join(sum(tb[0][1], []))
       and [seen(r[3]) for r in tb[1][1] if len(r) > 2 and spaced(w.mob["r2"]) in r[2]] == [dmw(w.today + timedelta(days=1)) + " · kal"],
       "…on the page the line has left Nahi aaye and stands in Aane baaki with the new day '· kal' (2 · 4 · 4)", [len(t[1]) for t in tb])
    # ---- S4: the same press sent again (a second tap, a page left open on another phone)
    c, j, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r2"], "act": "recall", "day": kal})
    c2, j2, _l = POST(w, "alisha", "/portal/ring/list/act", js={"id": oid["r2"], "act": "recall", "day": (w.today + timedelta(days=2)).isoformat()})
    o = q("SELECT * FROM outcome WHERE id=?", oid["r2"])[0]
    ok(c == 409 and c2 == 409 and j.get("ok") is False and j.get("msg") == T_NOT_NOSHOW and o["recalls"] == 1 and o["appt_day"] == kal
       and len(q("SELECT 1 FROM appt_event WHERE outcome_id=? AND kind='recall'", oid["r2"])) == 1,
       "[S4 s9.py] THE SAME PRESS SENT TWICE IS WRITTEN ONCE: the line is no longer in Nahi aaye, so the second 'Phir call kiya' is "
       "refused (409, in plain words) -- still one recall, still the first new day", (c, c2, j, o.get("recalls")))
    n_ev = len(q("SELECT 1 FROM appt_event"))
    got = [POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r6"], "act": "closed"})[0],
           POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r6"], "act": "recall", "day": kal})[0],
           POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r7"], "act": "closed"})[0],
           POST(w, "manoj", "/portal/ring/list/act", js={"id": oid["r7"], "act": "recall", "day": kal})[0]]
    st = q("SELECT COALESCE(appt_state,'') s, COALESCE(recalls,0) n, appt_day d FROM outcome WHERE id IN (?,?) ORDER BY id", oid["r6"], oid["r7"])
    ok(got == [409, 409, 409, 409] and len(q("SELECT 1 FROM appt_event")) == n_ev and all(x["s"] == "" and x["n"] == 0 for x in st),
       "[S4 s9.py] THE TWO BUTTONS ARE TAKEN ONLY WHERE THEY STAND: sent for a line in Aane baaki (r6) or in Aa gaye (r7) -- by staff or by "
       "the doctor -- each is refused (409) and nothing is written", (got, st))
    # ---- Ab nahi aayenge
    before_ev = len(q("SELECT 1 FROM appt_event"))
    c, j, _l = POST(w, "shavez", "/portal/ring/list/act", js={"id": oid["r3"], "act": "closed"})
    o = q("SELECT * FROM outcome WHERE id=?", oid["r3"])[0]
    ev = q("SELECT * FROM appt_event WHERE outcome_id=?", oid["r3"])
    ok(c == 200 and j.get("ok") is True and o["appt_state"] == "closed" and o["appt_state_by"] == "shavez" and (o["appt_state_at"] or "")[:10] == w.today.isoformat()
       and [(e["kind"], e["new_value"], e["by_name"]) for e in ev] == [("closed", "closed", "Shavez")],
       "shavez presses 'Ab nahi aayenge' on r3: the store marks it closed, with who and when; the row itself is kept", (j, o.get("appt_state")))
    c, h = GET(w, "shivani", "/portal/ring/list?d=30")
    ok([len(t[1]) for t in tables(h)] == [1, 4, 4] and "Meena Devi" not in h, "…and the line is gone from all three parts (1 · 4 · 4)", [len(t[1]) for t in tables(h)])
    c, j, _l = POST(w, "shavez", "/portal/ring/list/act", js={"id": oid["r3"], "act": "closed"})
    c2, j2, _l = POST(w, "shavez", "/portal/ring/list/act", js={"id": oid["r3"], "act": "recall", "day": kal})
    ok(c == 409 and j.get("ok") is False and len(q("SELECT 1 FROM appt_event")) == before_ev + 1 and c2 == 409 and j2.get("ok") is False,
       "[S4 s9.py] pressed twice it is written once (the second is refused, 409); a closed line cannot be given a new day (409)", (c, j, c2, j2))
    c, j, _l = POST(w, "shavez", "/portal/ring/appt", js={"s": w.sid["r3"], "note": "baad mein badla"})
    ok(c == 404 and j.get("ok") is False and (q("SELECT detail FROM outcome WHERE id=?", oid["r3"])[0]["detail"] or "") == ""
       and not q("SELECT 1 FROM appt_event WHERE outcome_id=? AND kind='note'", oid["r3"]),
       "[D2 delta] …and its note cannot be changed after 'Ab nahi aayenge' either (404), like its day", (c, j))
    c, j, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": 987654, "act": "closed"})
    c2, j2, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": "x", "act": "closed"})
    c3, j3, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": oid["r1"], "act": "delete"})
    ok(c == 404 and j.get("ok") is False and c2 == 400 and c3 == 400 and j3.get("ok") is False and q("SELECT COALESCE(appt_state,'') s FROM outcome WHERE id=?", oid["r1"])[0]["s"] == "",
       "a line that does not exist (404), a wrong id (400) and an unknown press (400) are each refused; r1 is untouched", (c, c2, c3))
    n_ev = len(q("SELECT 1 FROM appt_event"))
    odd_ids = [10 ** 30, 2 ** 63, 0, -1, True, 1.5, "abc", [oid["r1"]], None]
    got = [POST(w, "shivani", "/portal/ring/list/act", js={"id": v, "act": a, "day": kal})[0] for v in odd_ids for a in ("closed", "recall")]
    ok(set(got) == {400} and len(q("SELECT 1 FROM appt_event")) == n_ev,
       "[D1 delta] an id that is no whole number between 0 and 2**63 -- 10**30, 2**63, 0, -1, true, 1.5, text, a list, none -- is refused (400) "
       "by both buttons, never an error (500); nothing is written", got)
    # ---- the optional day on the card: Aur din, changing it, taking it back; the note
    far = (w.today + timedelta(days=9)).isoformat()
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": far})
    c2, h = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    ok(j.get("ok") is True and ro.get_outcome(w.sid["r4"])["appt_day"] == far
       and re.search(r'onclick="s497other\(\)" style="[^"]*#2563eb[^"]*">Aur din · %s</button>' % re.escape(dmw(w.today + timedelta(days=9))), h),
       "the card's 'Aur din chuniye': a day nine days on is written, and the card shows it chosen, with its date and English weekday", j)
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": ""})
    ok(j.get("ok") is True and (ro.get_outcome(w.sid["r4"])["appt_day"] or "") == "", "the tap is OPTIONAL: tapping the chosen day again takes it back -- no day", j)
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": "2026-13-45"})
    c2, j2, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": (w.today - timedelta(days=1)).isoformat()})
    c3, j3, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": "w497-x1", "day": kal})
    ok(c == 400 and c2 == 400 and c3 == 404 and j.get("ok") is False and j2.get("ok") is False and j3.get("ok") is False and (ro.get_outcome(w.sid["r4"])["appt_day"] or "") == "",
       "a day that is no date (400), a day gone by (400), and a call that is not an appointment (404) are each refused", (c, c2, c3))
    c, j, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": w.sid["r4"], "day": kal, "note": "kal 11 baje, wife ke saath"})
    o = ro.get_outcome(w.sid["r4"])
    ev = q("SELECT kind, old_value, new_value FROM appt_event WHERE outcome_id=? ORDER BY id", o["id"])
    ok(j.get("ok") is True and o["appt_day"] == kal and o["detail"] == "kal 11 baje, wife ke saath"
       and [e["kind"] for e in ev] == ["day", "day", "day", "note", "day"] and ev[3]["old_value"] == "kal 11 baje",
       "Kal again, with the note put right on the card: both written; every change of day and the old note are in the history", [e["kind"] for e in ev])
    tap = q("SELECT code, outcome_code, settle, identity, row_key, when_ist, login, handler FROM outcome WHERE sid=?", w.sid["r4"])[0]
    ok(tap == {"code": "appointment_booked", "outcome_code": "in_appointment_booked", "settle": "settle", "identity": "known",
               "row_key": "IN_%s_%s" % (w.mob["r4"], w.today.strftime("%Y%m%d")), "when_ist": w.today.isoformat() + " 10:15", "login": "alisha", "handler": "Alisha"},
       "…and what the tap itself filed for the tracker is exactly what it was (code, key, time, who)", tap)
    # ---- S6: a line standing in Nahi aaye is given a day FROM THE CARD (not by 'Phir call kiya')
    w.mob["s6"] = number(w.taken)
    prow(w, "6001", "Zoya Walk", w.mob["s6"])
    ring(w, "w497-s6", w.mob["s6"], "alisha", at(w, 5, "13:00"))
    ro.set_appt_day("w497-s6", (w.today - timedelta(days=3)).isoformat(), "alisha", "Alisha", now=at(w, 5, "13:00"))
    was = [p_ for p_ in ("noshow", "due", "came") if any(r["sid"] == "w497-s6" for r in ro.list_data("aaj")[p_])]
    c, j, _l = POST(w, "shivani", "/portal/ring/appt", js={"s": "w497-s6", "day": kal})
    o = ro.get_outcome("w497-s6")
    where = {sp: [p_ for p_ in ("noshow", "due", "came") if any(r["sid"] == "w497-s6" for r in ro.list_data(sp)[p_])] for sp in ("aaj", "7", "30")}
    ev = q("SELECT kind, old_value, new_value, by_name FROM appt_event WHERE outcome_id=? ORDER BY id", o["id"])
    ok(was == ["noshow"] and c == 200 and j.get("ok") is True and o["appt_day"] == kal and (o["recall_at"] or "")[:10] == w.today.isoformat() and o["recalls"] == 1
       and where == {"aaj": ["due"], "7": ["due"], "30": ["due"]} and [(e["kind"], e["new_value"], e["by_name"]) for e in ev][-1] == ("recall", kal, "Shivani"),
       "[S6 s9.py] A NO-SHOW GIVEN A DAY FROM THE CARD is written as what it is, a re-call (recall_at, one recall, kept in the history): "
       "under Aaj, 7 din and 30 din alike the line stands in Aane baaki -- it is not in NO part", (was, c, where, o.get("recall_at")))
    c, j, _l = POST(w, "shivani", "/portal/ring/appt", js={"s": "w497-s6", "day": kal})
    c2, j2, _l = POST(w, "shivani", "/portal/ring/appt", js={"s": "w497-s6", "day": (w.today + timedelta(days=2)).isoformat()})
    o = ro.get_outcome("w497-s6")
    ok(j.get("ok") is True and j2.get("ok") is True and o["recalls"] == 1 and o["appt_day"] == (w.today + timedelta(days=2)).isoformat(),
       "[S6 s9.py] …the same day sent again changes nothing; another day after that is an ordinary change of day -- still ONE recall", (j, j2, o.get("recalls")))
    con.close()


# ============================================================================================ PART 3 -- the rule
def find(data, sid):
    for part_ in ("noshow", "due", "came"):
        for r in data[part_]:
            if r["sid"] == sid:
                return part_, r
    return "", None


def part_3(w):
    ro = w.ro
    T = w.today
    D = lambda n: T - timedelta(days=n)                                         # noqa: E731
    noon = lambda n: datetime(D(-n).year, D(-n).month, D(-n).day, 12, 0, tzinfo=IST)   # noqa: E731  -- noon, n days AFTER today
    floor6 = D(6).isoformat()                                                   # the day his box holds since part 1
    # a known patient for the rule's lines; her last visit is long before any of these bookings
    def known(tag, cid, name):
        w.mob[tag] = number(w.taken)
        prow(w, cid, name, w.mob[tag])
        vrow(w, cid, D(200), w.fp(w.mob[tag]))

    def book(tag, who, ago, promised, clock="15:00"):
        sid = "w497-" + tag
        ring(w, sid, w.mob.get(who) or w.mob.setdefault(tag, number(w.taken)), "shivani", at(w, ago, clock))
        if promised is not None:
            good, msg = ro.set_appt_day(sid, (T + timedelta(days=promised)).isoformat(), "shivani", "Shivani", now=at(w, ago, clock))
            if not good:
                raise RuntimeError("the day was refused for %s: %s" % (tag, msg))
        return sid
    known("ka", "6101", "Asha Walk")
    known("kb", "6102", "Bina Walk")
    known("kc", "6103", "Chand Walk")
    known("kd", "6104", "Deep Walk")
    known("ke", "6105", "Esha Walk")
    s_y = book("p_yest", "ka", 3, -1)          # promised yesterday, no visit
    s_t = book("p_today", "kb", 3, 0)          # promised today
    s_w3 = book("n_wait3", "kc", 3, None)      # no day, booked 3 days ago
    s_w4 = book("n_wait4", "kd", 4, None)      # no day, booked 4 days ago
    s_w6 = book("n_wait6", "ke", 6, None)      # no day, booked 6 days ago
    d = ro.list_data("7")
    ok(d["visits_through"] == D(1), "the made-up Docterz export reaches yesterday (the newest visit on file is %s)" % dm(D(1)), d["visits_through"])
    ok(find(d, s_y)[0] == "noshow" and find(d, s_y)[1]["since"] == 1 and find(d, s_t)[0] == "due",
       "DAY GIVEN: promised yesterday and no visit → Nahi aaye, from the day AFTER the promised day; promised today → still Aane baaki",
       (find(d, s_y)[0], find(d, s_t)[0]))
    ok(find(d, s_w3)[0] == "due" and find(d, s_w4)[0] == "noshow" and find(d, s_w4)[1]["since"] == 4,
       "NO DAY GIVEN: three days are waited -- booked 3 days ago is still Aane baaki; booked 4 days ago is Nahi aaye ('4 din ho gaye')",
       (find(d, s_w3)[0], find(d, s_w4)[0]))
    c, h = GET(w, "shivani", "/portal/ring/list?d=aaj")
    row = [r for r in tables(h)[0][1] if len(r) > 2 and spaced(w.mob["ka"]) in r[2]]
    ok(len(row) == 1 and seen(row[0][3]) == dmw(D(1)) + " 1 din ho gaya", "…on the page: '%s 1 din ho gaya'" % dmw(D(1)), row and seen(row[0][3]))
    ok(len(row) == 1 and seen(row[0][1]) == "Asha Walk ID 6101 · pichhli visit %s-%d" % (dm(D(200)), D(200).year),
       "…and her last visit, 200 days back, carries its year (%s-%d) so it is not read as a recent one" % (dm(D(200)), D(200).year), row and seen(row[0][1]))
    # ---- S3: the spans
    due_in = {sp: [r["sid"] for r in ro.list_data(sp)["due"]] for sp in ("aaj", "7", "30")}
    ok(s_t in due_in["aaj"] and s_w3 not in due_in["aaj"] and s_w3 in due_in["7"],
       "[S3 s3.py] AAJ = booked or re-called today, OR DUE TODAY: a line booked three days ago for today is in Aane baaki under Aaj "
       "(the card's link 'Aaj ki list dekho' opens this); one booked three days ago with no day is not", (s_t in due_in["aaj"], s_w3 in due_in["aaj"]))
    s_far = book("far9", None, 0, 9)           # booked today, promised nine days on
    at8 = {sp: find(ro.list_data(sp, now=noon(8)), s_far)[0] for sp in ("aaj", "7", "30")}
    at9 = {sp: find(ro.list_data(sp, now=noon(9)), s_far)[0] for sp in ("aaj", "7", "30")}
    ok(at8 == {"aaj": "", "7": "due", "30": "due"} and at9 == {"aaj": "due", "7": "due", "30": "due"},
       "[S3 s3.py] A SPAN LOOKS AHEAD AS FAR AS IT LOOKS BACK: eight days after it was booked, a line due the NEXT day is under 7 din "
       "(not under Aaj); on its day it is under Aaj too", (at8, at9))
    # ---- B2: nobody is a no-show before Docterz can speak for that day
    t1 = noon(1)                                # tomorrow noon: s_t's day (today) has gone by; the export still reaches only yesterday
    got = {sp: find(ro.list_data(sp, now=t1), s_t) for sp in ("aaj", "7", "30")}
    ok(all(p == "due" and r.get("unsure") for p, r in got.values()) and not [r for r in ro.list_data("7", now=t1)["noshow"] if r["appt"] == T],
       "[B2 s2.py] NO FALSE NO-SHOW: the day after a promised day, while the Docterz visits on the server reach only the day BEFORE it, "
       "that line is NOT in Nahi aaye -- it stays in Aane baaki, under every span", {k: v[0] for k, v in got.items()})
    w.clock[0] = t1
    c, h = GET(w, "shivani", "/portal/ring/list?d=aaj")
    w.clock[0] = w.base
    tb = tables(h)
    row = [r for r in tb[1][1] if len(r) > 2 and spaced(w.mob["kb"]) in r[2]]
    ok(c == 200 and len(row) == 1 and len(row[0]) == 7 and seen(row[0][3]) == dmw(T) + " " + T_UNSURE and BUTTONS not in text_of("".join(row[0]))
       and spaced(w.mob["kb"]) not in "".join(sum(tb[0][1], [])) and "padha nahi ja saka" not in h,
       "[B2 s2.py] …on the page that line reads '%s %s', with NO button (and no banner: Docterz is readable, only not yet up to that day)" % (dmw(T), T_UNSURE),
       row and seen(row[0][3]))
    oid_t = ro.get_outcome(s_t)["id"]
    r1_ = ro.close_appt(oid_t, "shivani", "Shivani", now=t1)
    r2_ = ro.recall_appt(oid_t, D(-2).isoformat(), "shivani", "Shivani", now=t1)
    ok(r1_ == (False, T_NOT_NOSHOW) and r2_ == (False, T_NOT_NOSHOW) and (ro.get_outcome(s_t).get("appt_state") or "") == "",
       "[B2 s2.py] …and neither button can be sent for it: 'Ab nahi aayenge' on a patient Docterz has not yet spoken for is refused", (r1_, r2_))
    vrow(w, "9998", T, "")                      # the next export lands: somebody else's visit, dated today
    p, r = find(ro.list_data("7", now=t1), s_t)
    ok(p == "noshow" and r["since"] == 1 and ro.list_data("7")["visits_through"] == T,
       "[B2 s2.py] …once the visits on the server reach that day (the next export lands) and hers is not among them, the line IS Nahi aaye", p)
    J = asks(ro, "can_judge")
    ok([J(D(1), D(1)), J(D(1), T), J(D(1), D(2)), J(D(1), None)] == [True, True, False, False],
       "[B2 s2.py] the test itself (can_judge): the visits must reach the line's last day; a day short, or none readable → not yet")
    # ---- kept until dealt with
    vrow(w, "9999", D(-40), "")                 # forty days on, Docterz has been arriving all along
    w.clock[0] = noon(40)
    c, h = GET(w, "shivani", "/portal/ring/list?d=aaj")
    w.clock[0] = w.base
    p, r = find(ro.list_data("30", now=noon(40)), s_y)
    ok(p == "noshow" and r["since"] == 41 and spaced(w.mob["ka"]) in "".join(sum(tables(h)[0][1], [])) and dm(D(3)) + " · 15:00" in text_of(h),
       "KEPT UNTIL DEALT WITH: forty days on, a no-show booked 43 days before is outside every span and is still on the page, even under Aaj", (p, r and r.get("since")))
    # the setting changed
    c, j, loc = POST(w, "shivani", "/portal/ring/list/setting", form={"wait_days": "5", "follow_from": floor6})
    ok(c == 403 and ro.wait_days() == 3, "a staff login cannot change the setting (403)", c)
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "5", "follow_from": floor6})
    d5 = ro.list_data("7")
    ok(c == 302 and loc.endswith("?m=saved") and ro.wait_days() == 5 and find(d5, s_w4)[0] == "due" and find(d5, s_w6)[0] == "noshow" and find(d5, s_y)[0] == "noshow",
       "THE SETTING: the doctor makes it 5 days -- the line booked 4 days ago goes back to Aane baaki, the one booked 6 days ago stays Nahi aaye, "
       "a line with a day given is not moved by it", (c, loc, ro.wait_days(), find(d5, s_w4)[0]))
    c, h = GET(w, "shivani", "/portal/ring/list")
    c2, hc = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    hm = GET(w, "manoj", "/portal/ring/list?m=saved")[1]
    ok("<b>Saved.</b>" in hm and 'name="wait_days" min="1" max="30" value="5"' in hm and "Saved." not in GET(w, "shivani", "/portal/ring/list?m=saved")[1],
       "…his box says 'Saved.' and shows 5; a staff login sees no such line whatever the address says")
    ok("Din na likha ho to 5 din baad." in text_of(h) and "Din na batayein to 5 din tak intezaar hoga" in text_of(hc),
       "…and both sentences that say the number now say 5 (the page's foot, the card)")
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "0", "follow_from": floor6})
    ok(loc.endswith("?m=bad") and ro.wait_days() == 5, "a setting of 0 days is refused", loc)
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "0", "follow_from": D(2).isoformat()})
    ok(loc.endswith("?m=bad") and ro.wait_days() == 5 and ro.follow_from() == floor6,
       "[D3 delta] when the days box is wrong NOTHING is saved -- not the date either -- so the page's 'Not saved' is true", (loc, ro.follow_from()))
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": floor6})
    ok(ro.wait_days() == 3 and find(ro.list_data("7"), s_w4)[0] == "noshow", "back to 3: the line booked 4 days ago is Nahi aaye again")
    # a late arrival
    con = sqlite3.connect(os.environ["RING_OUTCOME_DB"])
    n_before = con.execute("SELECT COUNT(*) FROM appt_event").fetchone()[0]
    con.close()
    ok(find(ro.list_data("7"), w.sid["r1"])[0] == "noshow", "r1 (promised two days ago) is still Nahi aaye")
    vrow(w, PATIENTS["rajesh"][1], T, w.fp(w.mob["r1"]))
    p, r = find(ro.list_data("7"), w.sid["r1"])
    c, h = GET(w, "shivani", "/portal/ring/list")
    cell = [seen(x[4]) for x in tables(h)[2][1] if len(x) > 2 and spaced(w.mob["r1"]) in x[2]]
    con = sqlite3.connect(os.environ["RING_OUTCOME_DB"])
    n_after = con.execute("SELECT COUNT(*) FROM appt_event").fetchone()[0]
    con.close()
    ok(p == "came" and r["late"] == 2 and cell == ["Aaye · %s 2 din baad" % dm(T)] and spaced(w.mob["r1"]) not in "".join(sum(tables(h)[0][1], [])) and n_after == n_before,
       "A LATE ARRIVAL IS STILL COME: Docterz shows r1's visit today → the line moves BY ITSELF from Nahi aaye to Aa gaye, 'Aaye · %s 2 din baad' -- nobody pressed anything" % dm(T),
       (p, cell))
    # the visit must be on or after the booking day
    known("kf", "6106", "Farah Walk")
    s_pre = book("pre", "kf", 3, -1)
    vrow(w, "6106", D(5), w.fp(w.mob["kf"]))    # two days BEFORE she was booked (and inside the days the list reads)
    ok(find(ro.list_data("7"), s_pre)[0] == "noshow", "a visit dated BEFORE the booking day does not count: that line is Nahi aaye")
    vrow(w, "6106", D(3), w.fp(w.mob["kf"]))
    p, r = find(ro.list_data("7"), s_pre)
    ok(p == "came" and r["visit"] == D(3) and r["late"] == 0, "a visit ON the booking day counts (and one earlier than promised carries no 'din baad')", (p, r and r.get("visit")))
    # a family mobile: two patients on the card; the second one comes
    w.mob["fam"] = number(w.taken)
    prow(w, "6201", "Gita Walk", w.mob["fam"], last_seen=D(60))
    prow(w, "6202", "Hari Walk", w.mob["fam"], last_seen=D(90))
    s_fam = book("fam1", "fam", 2, -1)
    filed = ro.get_outcome(s_fam)["clinic_id"]
    other = "6202" if filed == "6201" else "6201"
    names = {"6201": "Gita Walk", "6202": "Hari Walk"}
    ok(find(ro.list_data("7"), s_fam)[0] == "noshow", "a family mobile (two patients on the card): no visit yet → Nahi aaye")
    vrow(w, other, D(1), "")
    p, r = find(ro.list_data("7"), s_fam)
    ok(p == "came" and r["visit_by"] == "id" and r["visit_id"] == other, "…the OTHER patient on that card comes → Aa gaye, found by the clinic ID the card showed", (p, r and r.get("visit_by")))
    c, h = GET(w, "shivani", "/portal/ring/list")
    row = [x for x in tables(h)[2][1] if len(x) > 2 and spaced(w.mob["fam"]) in x[2]]
    ok(len(row) == 1 and seen(row[0][1]) == "%s ID %s" % (names[filed], filed) and seen(row[0][4]) == "Aaye · %s %s · ID %s ki visit" % (dm(D(1)), names[other], other),
       "[S2 s2.py] WHOSE VISIT IT WAS: the line is filed under %s, the visit is %s's -- under 'Aaye · %s' the page says '%s · ID %s ki visit'"
       % (names[filed], names[other], dm(D(1)), names[other], other), row and seen(row[0][4]))
    # a known caller; the person who comes was registered at the visit (a new ID on the same mobile)
    known("kg", "6301", "Indu Walk")
    s_new_id = book("newid", "kg", 2, -1)
    vrow(w, "6399", D(1), w.fp(w.mob["kg"]))
    p, r = find(ro.list_data("7"), s_new_id)
    ok(p == "came" and r["visit_by"] == "mobile", "a known caller whose visit is under a NEW clinic ID on the same mobile → Aa gaye, found by the mobile's fingerprint", (p, r and r.get("visit_by")))
    c, h = GET(w, "shivani", "/portal/ring/list")
    row = [x for x in tables(h)[2][1] if len(x) > 2 and spaced(w.mob["kg"]) in x[2]]
    own = [x for x in tables(h)[2][1] if len(x) > 2 and spaced(w.mob["r7"]) in x[2]]
    ok(len(row) == 1 and seen(row[0][4]) == "Aaye · %s ID 6399 ki visit" % dm(D(1)) and len(own) == 1 and seen(own[0][4]) == "Aaye · " + dm(D(1)),
       "[S2 s2.py] …an ID with no name on file yet reads 'ID 6399 ki visit'; a visit under the line's OWN ID carries no such line (the mock-up's cell)",
       (row and seen(row[0][4]), own and seen(own[0][4])))
    # a new number that comes, not yet in the patient list: the ID from the visit, the name still 'Naya number'
    s_nn = book("nn", None, 2, -1)
    vrow(w, "6400", D(1), w.fp(w.mob["nn"]))
    c, h = GET(w, "shivani", "/portal/ring/list")
    cell = [seen(x[1]) for x in tables(h)[2][1] if len(x) > 2 and spaced(w.mob["nn"]) in x[2]]
    ok(cell == ["Naya number call ke samay naya number tha · ab ID 6400"], "a new number whose visit is in but whose name is not yet: 'Naya number · call ke samay naya number tha · ab ID 6400'", cell)
    # a closed line whose patient comes after all
    known("kh", "6501", "Jaya Walk")
    s_cl = book("closedcame", "kh", 3, -2)
    con = sqlite3.connect(os.environ["RING_OUTCOME_DB"])
    oid = con.execute("SELECT id FROM outcome WHERE sid=?", (s_cl,)).fetchone()[0]
    con.close()
    ok(ro.close_appt(oid, "shivani", "Shivani") == (True, "ok") and find(ro.list_data("7"), s_cl)[0] == "", "'Ab nahi aayenge' pressed: the line is in no part")
    vrow(w, "6501", T, w.fp(w.mob["kh"]))
    ok(find(ro.list_data("7"), s_cl)[0] == "came", "…but if Docterz then shows the visit, it is in Aa gaye: the export is the truth, not the button")
    # ---- B1: the floor -- his setting, the switch-on day, and the day nothing goes behind
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": ""})
    df = ro.list_data("30")
    c2, hd = GET(w, "manoj", "/portal/ring/list")
    fld = re.findall(r'<input type="date" name="follow_from" min="([^"]*)" value="([^"]*)"', hd)
    ok(loc.endswith("?m=saved") and ro.follow_from() == "" and asks(ro, "floor_day")() == T and df["follow_from"] == T and find(df, s_y)[0] == "" and find(df, s_far)[0] == "due"
       and fld == [(HARD.isoformat(), T.isoformat())] and not [r for k in ("noshow", "due", "came") for r in df[k] if r["booked"] < T],
       "[B1 s1.py] EMPTIED, HIS SETTING RETURNS TO THE SWITCH-ON DAY -- never to 'all of them': only appointments booked on or after the "
       "day the list was first turned on are followed, and his box shows that day", (loc, ro.follow_from(), str(df["follow_from"])))
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": T.isoformat()})
    ok(loc.endswith("?m=saved") and ro.follow_from() == "",
       "[B1 s1.py] …and the day his box was already showing, sent back untouched with a Save, pins nothing (his setting stays empty)", ro.follow_from())
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": D(2).isoformat()})
    df = ro.list_data("30")
    ok(loc.endswith("?m=saved") and asks(ro, "floor_day")() == D(2) and find(df, s_y)[0] == "" and find(df, s_fam)[0] == "came" and find(df, s_new_id)[0] == "came",
       "[B1 s1.py] he moves it to two days ago: an appointment booked three days ago is not followed; those booked two days ago are", loc)
    bad = []
    for v in ("not-a-date", "2026-13-45", (HARD - timedelta(days=1)).isoformat(), "2025-01-01"):
        c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": v})
        if not (loc.endswith("?m=bad") and ro.follow_from() == D(2).isoformat()):
            bad.append((v, loc))
    ok(not bad, "[B1 s1.py] a floor that is no date, or a day before %s, is refused and the setting is left as it was" % hard_words(), bad)
    w.clock[0] = noon(1)                        # the next day he turns it off, and on again
    POST(w, "manoj", "/portal/ring/list/switch", form={"on": "0"})
    POST(w, "manoj", "/portal/ring/list/switch", form={"on": "1"})
    w.clock[0] = w.base
    ok(ro.list_on() is True and asks(ro, "switch_on_day")() == T, "[B1 s1.py] turned off and on again the NEXT day: the switch-on day is still the first one -- a later turn never moves it", asks(ro, "switch_on_day")())
    c, j, loc = POST(w, "manoj", "/portal/ring/list/setting", form={"wait_days": "3", "follow_from": floor6})
    ok(asks(ro, "floor_day")() == D(6) and find(ro.list_data("7"), s_y)[0] == "noshow", "back to six days ago for the rest of the walk")
    # the same, on a store nobody has touched: before it is ever on, the floor is 'today'; a Save pins nothing
    fresh = os.path.join(w.scratch, "fresh_store.db")
    ro.init_db(fresh)
    fl, sw = asks(ro, "floor_day"), asks(ro, "switch_on_day")
    a1 = fl(fresh, now=at(w, 0))
    a2 = ro.set_follow_from(T.isoformat(), "manoj", fresh, now=at(w, 0)), ro.follow_from(fresh)
    ro.set_list_on(True, "manoj", fresh, now=noon(3))
    a3 = sw(fresh), fl(fresh, now=noon(5))
    ro.set_list_on(False, "manoj", fresh, now=noon(6))
    ro.set_list_on(True, "manoj", fresh, now=noon(9))
    a4 = sw(fresh), fl(fresh, now=noon(12))
    a5 = ro.set_follow_from(HARD.isoformat(), "manoj", fresh), fl(fresh, now=noon(12))
    ok(a1 == T and a2 == (True, "") and a3 == (D(-3), D(-3)) and a4 == (D(-3), D(-3)) and a5 == (True, HARD),
       "[B1 s1.py] on an untouched store: never yet on → the floor is today, and a Save of the day shown pins nothing; first turned on three "
       "days later → THAT is the floor (not the earlier day); off and on again later → unchanged; he may take it back to %s" % hard_words(), (a1, a2, a3, a4, a5))
    # the rule itself, as a table of cases
    S = ro.appt_state
    cases = [(S(D(5), D(2), False, None, T, 3), "noshow"), (S(D(5), T, False, None, T, 3), "due"), (S(D(5), D(-1), False, None, T, 3), "due"),
             (S(D(3), None, False, None, T, 3), "due"), (S(D(4), None, False, None, T, 3), "noshow"), (S(D(4), None, False, None, T, 4), "due"),
             (S(D(9), D(8), False, D(1), T, 3), "came"), (S(D(9), D(8), True, None, T, 3), "closed"), (S(D(9), D(8), True, D(1), T, 3), "came")]
    ok(all(a_ == b_ for a_, b_ in cases), "the rule by the calendar (appt_state) on nine cases: both branches, both sides of each edge, come beats closed", [a_ for a_, b_ in cases])


# ============================================================================================ PART 4 -- the clock
def part_4(w):
    ro = w.ro
    T = w.today
    w.mob["mid"] = number(w.taken)
    prow(w, "6601", "Kiran Walk", w.mob["mid"])
    sid = "w497-mid"
    ring(w, sid, w.mob["mid"], "shivani", at(w, 1, "15:00"))
    ro.set_appt_day(sid, T.isoformat(), "shivani", "Shivani", now=at(w, 1, "15:00"))
    vrow(w, "9997", T, "")                                   # the Docterz export reaches the promised day (somebody else's visit)
    nxt = T + timedelta(days=1)
    moments = [("India 23:59:59 on the promised day", datetime(T.year, T.month, T.day, 23, 59, 59, tzinfo=IST), "due"),
               ("India 00:00:00 the next day", datetime(nxt.year, nxt.month, nxt.day, 0, 0, 0, tzinfo=IST), "noshow"),
               ("18:29:59 UTC (India 23:59:59)", datetime(T.year, T.month, T.day, 18, 29, 59, tzinfo=UTC), "due"),
               ("18:30:00 UTC (India midnight)", datetime(T.year, T.month, T.day, 18, 30, 0, tzinfo=UTC), "noshow"),
               ("23:30 UTC, still the promised DATE in UTC (India 05:00 next day)", datetime(T.year, T.month, T.day, 23, 30, tzinfo=UTC), "noshow"),
               ("20:00 UTC the day before (India 01:30 on the promised day)", datetime(T.year, T.month, T.day, 20, 0, tzinfo=UTC) - timedelta(days=1), "due"),
               ("a moment with no zone is read as India time", datetime(nxt.year, nxt.month, nxt.day, 0, 0, 1), "noshow")]
    got = [(name, find(ro.list_data("7", now=m), sid)[0], want) for name, m, want in moments]
    ok(all(g == x for _n, g, x in got),
       "INDIA-TIME MIDNIGHT is the day's edge, whatever zone the moment is given in: Aane baaki up to 23:59:59 IST, Nahi aaye from 00:00:00 IST "
       "(18:30 UTC) -- a UTC-day reader would be wrong for five and a half hours", [(n, g) for n, g, x in got if g != x])
    w.clock[0] = datetime(nxt.year, nxt.month, nxt.day, 0, 0, 30, tzinfo=IST)
    c, h = GET(w, "shivani", "/portal/ring/list")
    row = [r for r in tables(h)[0][1] if len(r) > 2 and spaced(w.mob["mid"]) in r[2]]
    cc, hc = GET(w, "shivani", "/portal/ring/outcome?s=" + sid)
    days = re.findall(r'data-day="([^"]*)" onclick="s497day', hc)
    ok(len(row) == 1 and seen(row[0][3]) == dmw(T) + " 1 din ho gaya" and days == [nxt.isoformat(), (nxt + timedelta(days=1)).isoformat(), (nxt + timedelta(days=2)).isoformat()],
       "…served thirty seconds after India midnight: the page says '%s 1 din ho gaya', and the card's Aaj · Kal · Parso are the new day's" % dmw(T), (row and seen(row[0][3]), days))
    late = datetime(T.year, T.month, T.day, 23, 58, tzinfo=IST)
    w.clock[0] = late
    w.mob["mid2"] = number(w.taken)
    ring(w, "w497-mid2", w.mob["mid2"], "alisha", None, file_it=False)
    c, j, _l = POST(w, "alisha", "/portal/ring/outcome", js={"s": "w497-mid2", "code": "appointment_booked", "note": ""})
    quiet()
    c2, j2, _l = POST(w, "alisha", "/portal/ring/appt", js={"s": "w497-mid2", "day": T.isoformat()})
    o = ro.get_outcome("w497-mid2")
    ok(j.get("ok") and j2.get("ok") and o["when_ist"] == T.isoformat() + " 23:58" and o["day_key"] == T.strftime("%Y%m%d") and o["appt_day"] == T.isoformat(),
       "a tap at 23:58 India time (18:28 UTC) is booked on THAT India day, and 'Aaj' is that day", (o["when_ist"], o["day_key"], o["appt_day"]))
    w.clock[0] = w.base
    # five process time zones: the clock itself, and the page's bytes
    keep = os.environ.get("TZ")
    c, ref = GET(w, "shivani", "/portal/ring/list")
    bad = []
    for tz in ("UTC", "Asia/Kolkata", "Pacific/Kiritimati", "Etc/GMT+12", "America/New_York"):
        os.environ["TZ"] = tz
        time.tzset()
        a = (datetime(1970, 1, 1) + timedelta(seconds=time.time() + 19800)).date()
        b = w.real_now()
        a2 = (datetime(1970, 1, 1) + timedelta(seconds=time.time() + 19800)).date()
        if not (b.utcoffset() == timedelta(hours=5, minutes=30) and b.date() in (a, a2) and ro._ist(None) == w.clock[0]):
            bad.append((tz, "clock"))
        ro.now_ist = w.real_now
        if ro.list_data("7")["today"] not in (a, a2):
            bad.append((tz, "today"))
        ro.now_ist = lambda: w.clock[0]
        if GET(w, "shivani", "/portal/ring/list")[1] != ref:
            bad.append((tz, "page"))
    if keep is None:
        os.environ.pop("TZ", None)
    else:
        os.environ["TZ"] = keep
    time.tzset()
    ok(not bad, "FIVE PROCESS TIME ZONES (UTC, Asia/Kolkata, UTC+14, UTC-12, New York): the program's clock is India time in each, "
       "'today' is India's date in each, and the page is byte for byte the same", bad)


# ============================================================================================ PART 5 -- Docterz, WhatsApp
def part_5(w):
    ro = w.ro
    db = os.environ["RING_OUTCOME_DB"]
    del w.doors[:]
    fin_md5, fin_dir = md5f(w.fin), sorted(os.listdir(w.fdir))
    store = table_print(db)
    for u in ("shivani", "manoj"):
        for span in ("aaj", "7", "30"):
            GET(w, u, "/portal/ring/list?d=" + span)
    ok(len(w.doors) >= 6 and all(d["uri"] and d["target"].startswith("file:") and d["target"].endswith("?mode=ro") for d in w.doors),
       "DOCTERZ, READ-ONLY: every door ring_outcome opened on finance.db (%d of them) was opened 'file:…?mode=ro'" % len(w.doors),
       [d["target"][-30:] for d in w.doors][:3])
    read = set().union(*[d["tables"] for d in w.doors]) if w.doors else set()
    ok(read == {"patient_visit"} and sum(d["writes"] for d in w.doors) == 0,
       "…and through those doors the ONLY table read was patient_visit; nothing was written, made or changed", sorted(read))
    ok(md5f(w.fin) == fin_md5 and sorted(os.listdir(w.fdir)) == fin_dir and table_print(db) == store,
       "…the finance database's BYTES are unchanged, no journal file appeared beside it, and the ring store is unchanged too")
    con = sqlite3.connect("file:%s?mode=ro" % w.fin, uri=True)
    money = con.execute("SELECT COUNT(*), SUM(amount_p) FROM day_entry").fetchone()
    con.close()
    ok(money == (1, 12345), "…the money table beside it holds what it held")
    # absent
    n_before = [len(t[1]) for t in tables(GET(w, "shivani", "/portal/ring/list?d=30")[1])]
    ns_before = [r["id"] for r in ro.list_data("aaj")["noshow"]]
    ev_before = sqlite3.connect(db).execute("SELECT COUNT(*) FROM appt_event").fetchone()[0]
    away = w.fin + ".away"
    os.rename(w.fin, away)
    try:
        da = ro.list_data("aaj")
        c, h = GET(w, "shivani", "/portal/ring/list?d=aaj")
        unsure = {r["id"] for r in da["due"] if r.get("unsure")}
        ok(len(ns_before) >= 3 and da["noshow"] == [] and set(ns_before) <= unsure and c == 200 and h.count(">Ab nahi aayenge</button>") == 0
           and h.count(">Phir call kiya — naya din</button>") == 0 and text_of(h).count(T_UNSURE) == len(unsure),
           "[B2 s2.py] FINANCE DATABASE ABSENT: NOBODY is Nahi aaye -- each of the %d lines that stood there is in Aane baaki, whatever the "
           "span, marked '%s', and the page has NO button at all" % (len(ns_before), T_UNSURE), (len(ns_before), len(da["noshow"]), len(unsure), h.count(">Ab nahi aayenge</button>")))
        c, j, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": ns_before[0], "act": "closed"})
        c2, j2, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": ns_before[0], "act": "recall", "day": (w.today + timedelta(days=1)).isoformat()})
        ok(c == 409 and c2 == 409 and j.get("ok") is False and sqlite3.connect(db).execute("SELECT COUNT(*) FROM appt_event").fetchone()[0] == ev_before,
           "[B2 s2.py] …and a button sent anyway is refused (409): 'Ab nahi aayenge' cannot be pressed on someone who may have come", (c, c2, j))
        c, h = GET(w, "shivani", "/portal/ring/list?d=30")
        c2, hd = GET(w, "manoj", "/portal/ring/list?d=30")
        c3, hh = GET(w, "shivani", "/portal")
        tb = tables(h)
        ok(c == 200 and c2 == 200 and c3 == 200 and len(tb) == 3 and seen(tb[2][1][0][0]) == "—" and "Aa gaye — Docterz ke export se pakka (0)" in text_of(h),
           "FINANCE DATABASE ABSENT: the page still answers 200 for staff and for the doctor, the home too -- Aa gaye simply cannot confirm (0)", (c, c2, c3))
        ok("Docterz ka record abhi padha nahi ja saka" in text_of(h) and "could not be read just now" in text_of(hd),
           "…and the page SAYS so, to staff in their words and to the doctor in his -- it is not silently short (F-748)")
        ok(not os.path.exists(w.fin), "…and the missing file was not created by the reading")
    finally:
        os.rename(away, w.fin)
    # locked
    lock = sqlite3.connect(w.fin, timeout=1, isolation_level=None)
    lock.execute("BEGIN EXCLUSIVE")
    try:
        t0 = time.time()
        c, h = GET(w, "shivani", "/portal/ring/list")
        ok(c == 200 and "Docterz ka record abhi padha nahi ja saka" in text_of(h) and time.time() - t0 < 30,
           "FINANCE DATABASE LOCKED by another program: the page answers 200 with the same line (%.1f s), never an error" % (time.time() - t0), c)
        ok(h.count(">Ab nahi aayenge</button>") == 0 and [len(t[1]) if (t[1] and len(t[1][0]) > 1) else 0 for t in tables(h)][0] == 0,
           "[B2 s2.py] …and while it is locked nobody is Nahi aaye and there is no button")
    finally:
        lock.execute("ROLLBACK")
        lock.close()
    c, h = GET(w, "shivani", "/portal/ring/list?d=30")
    ok(c == 200 and [len(t[1]) for t in tables(h)] == n_before and "padha nahi ja saka" not in h, "…put back and unlocked, the page is whole again", [len(t[1]) for t in tables(h)])
    # dates Docterz did not write as YYYY-MM-DD cannot confirm anything, and the page says so
    odd = os.path.join(w.scratch, "odd.db")
    con = sqlite3.connect(odd)
    con.execute("CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT)")
    con.execute("INSERT INTO patient_visit VALUES ('x','07/10/2026','4521','u','','')")
    con.commit()
    con.close()
    ok(ro.list_data("7", finance_db=odd)["visits_ok"] is False and ro.visits_since(w.today.isoformat(), w.today, odd)["ok"] is False,
       "a visit table whose dates are not written YYYY-MM-DD is treated as unreadable, not as 'nobody came'")
    # a switch that cannot read its own state is off (fail closed) -- and the doctor is never locked out
    away = db + ".away"
    os.rename(db, away)
    try:
        c, h = GET(w, "shivani", "/portal")
        c2, h2 = GET(w, "shivani", "/portal/ring/list")
        c3, h3 = GET(w, "manoj", "/portal")
        ok(c == 200 and TILE not in tiles(h) and c2 == 200 and "Yeh list abhi band hai" in h2 and c3 == 200 and TILE in tiles(h3) and not os.path.exists(db),
           "THE RING STORE ABSENT: the switch cannot be read, so it is OFF -- shivani's home answers 200 without the tile, her page says band; "
           "the doctor's home keeps the tile; no store was made by the looking", (c, c2, c3, os.path.exists(db)))
    finally:
        os.rename(away, db)
    mod = sys.modules["ring_outcome"]
    sys.modules["ring_outcome"] = None
    try:
        c, h = GET(w, "shivani", "/portal")
        c3, h3 = GET(w, "manoj", "/portal")
        ok(c == 200 and TILE not in tiles(h) and "Call Tracker" in tiles(h) and c3 == 200 and TILE in tiles(h3),
           "ring_outcome NOT LOADABLE by the portal: the home still answers 200 for everyone; the tile is simply not drawn for staff", (c, c3))
    finally:
        sys.modules["ring_outcome"] = mod
    ok(TILE in tiles(GET(w, "shivani", "/portal")[1]), "…both put back: shivani's tile is there again")
    # WhatsApp: room only
    con = sqlite3.connect(db)
    cols = [r[1] for r in con.execute("PRAGMA table_info(outcome)")]
    used = con.execute("SELECT COUNT(*) FROM outcome WHERE COALESCE(wa_state,'')<>'' OR COALESCE(wa_at,'')<>'' OR COALESCE(wa_ref,'')<>''").fetchone()[0]
    con.close()
    src = open(ro.__file__, encoding="utf-8").read()
    ok({"wa_state", "wa_at", "wa_ref"} <= set(cols) and used == 0 and ro.WA_ENABLED is False,
       "WHATSAPP, ROOM ONLY: the store has the three fields for a message's state, and after every press in this walk all of them are empty", used)
    named = [ln.strip() for ln in src.splitlines() if re.search(r"wa_state|wa_at\b|wa_ref", ln)]
    ok(len(named) >= 1 and all(ln.startswith("#") or ln.startswith('("wa_state", "TEXT")') for ln in named),
       "…the program names those fields only where it makes them (and in its notes): no line of it writes one, so no line of it can send", named)
    quiet()
    mirrored = sqlite3.connect(db).execute("SELECT COUNT(*) FROM outcome WHERE mirrored_at IS NOT NULL").fetchone()[0]
    ok(w.net == [] and mirrored == 0, "NOTHING WAS SENT ANYWHERE: through the whole walk no program tried to open a connection (every attempt is counted)", w.net[:3])


# ============================================================================================ PART 6 -- the old store
def part_6(w):
    ro, live = w.ro, w.live
    old_db = os.path.join(w.scratch, "old_store.db")
    m = number(w.taken)
    live.now_ist = lambda: at(w, 1, "11:00")
    live.init_db(old_db)
    live.record_call("w497-old1", m, {"mobile": m, "patients": [{"name": "Lata Walk", "clinic_id": "6701", "last_visit": "", "visits": 1, "procedure": False}]}, {"shivani": "Shivani"}, path=old_db)
    live.record_answered("w497-old1", "shivani", path=old_db)
    live.record_end("w497-old1", "answered", {"shivani": "Shivani"}, ["shivani"], path=old_db)
    live.file_outcome("w497-old1", "appointment_booked", "shivani", "Shivani", "purana", path=old_db, now=at(w, 1, "11:00"))
    con = sqlite3.connect(old_db)
    cols_before = [r[1] for r in con.execute("PRAGMA table_info(outcome)")]
    rows_before = con.execute("SELECT * FROM outcome").fetchall(), con.execute("SELECT * FROM call").fetchall()
    con.close()
    md5_before = md5f(old_db)
    ok("appt_day" not in cols_before and len(cols_before) == 21, "a store made by the LIVE file: 21 columns on outcome, none of the list's", len(cols_before))
    d = ro.list_data("7", path=old_db)
    ok(d["store_ok"] is False and ro.list_on(old_db) is False and md5f(old_db) == md5_before and "List abhi padhi nahi ja saki" in text_of(ro.render_list(d)),
       "the kit's READS on that old store -- list_data, list_on -- change not a byte of it; the list SAYS it could not be read rather than showing nothing (F-793)")
    ro.init_db(old_db)
    ro.init_db(old_db)
    con = sqlite3.connect(old_db)
    cols = [r[1] for r in con.execute("PRAGMA table_info(outcome)")]
    kept = con.execute("SELECT %s FROM outcome" % ", ".join(cols_before)).fetchall(), con.execute("SELECT * FROM call").fetchall()
    tabs = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    con.close()
    ok(cols[:21] == cols_before and cols[21:] == [c[0] for c in ro.S497_COLS] and kept == rows_before and {"kv", "appt_event"} <= tabs,
       "the kit's init_db (run twice) ADDS its eleven columns and two tables; every column and every row that was there is as it was", cols[21:])
    d = ro.list_data("7", path=old_db)
    ok(d["store_ok"] and d["noshow"] + d["due"] + d["came"] == [] and d["follow_from"] == w.today,
       "[B1 s1.py] …the appointment filed YESTERDAY, before the kit, is NOT on the list: nothing booked before the first switch-on day is followed", d["follow_from"])
    good = ro.set_follow_from((w.today - timedelta(days=1)).isoformat(), "manoj", old_db)
    d = ro.list_data("7", path=old_db)
    ok(good and d["store_ok"] and [r["sid"] for r in d["due"]] == ["w497-old1"],
       "…until HE moves 'follow from' back a day: then it is on the list (no day written → Aane baaki)")
    ok(live.get_outcome("w497-old1", path=old_db)["detail"] == "purana" and live.counts(at(w, 1).strftime("%Y%m%d"), path=old_db)["per_person"]["shivani"]["appointments"] == 1,
       "…and the LIVE file still reads the store after the kit has touched it (an undo finds its data whole)")


# ============================================================================================ PART 7 -- the review's other findings
def part_7(w):
    ro, rc = w.ro, w.rc
    db = os.environ["RING_OUTCOME_DB"]
    T = w.today
    noon = lambda n: datetime.combine(T + timedelta(days=n), datetime.min.time()).replace(hour=12, tzinfo=IST)   # noqa: E731
    # ---- S1: the tile MASKED for one login (Manage Users can do this to any one person)
    g = os.environ["TILE_GRANTS_FILE"]
    raw = open(g, "rb").read()
    d = json.loads(raw.decode("utf-8"))
    d["users"]["shivani"]["mask"] = list(d["users"]["shivani"].get("mask") or []) + [TILE]
    with open(g, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)
    os.utime(g, (time.time() + 5, time.time() + 5))
    try:
        ns = ro.list_data("aaj")["noshow"]
        n_ev = sqlite3.connect(db).execute("SELECT COUNT(*) FROM appt_event").fetchone()[0]
        c1, hp = GET(w, "shivani", "/portal")
        c2, hl = GET(w, "shivani", "/portal/ring/list")
        c3, j3, _l = POST(w, "shivani", "/portal/ring/list/act", js={"id": ns[0]["id"], "act": "closed"})
        c4, j4, _l = POST(w, "shivani", "/portal/ring/appt", js={"s": w.sid["r4"], "day": (T + timedelta(days=3)).isoformat()})
        c5, hc = GET(w, "shivani", "/portal/ring/outcome?s=" + w.sid["r4"])
        c6, hd = GET(w, "manoj", "/portal/ring/list")
        c7, ha = GET(w, "alisha", "/portal/ring/list")
        ok(c1 == 200 and TILE not in tiles(hp) and c2 == 403 and "<table>" not in hl and "aapke login ke liye nahi" in hl and c3 == 403 and c4 == 403
           and c5 == 200 and "Kis din aayenge" not in hc and sqlite3.connect(db).execute("SELECT COUNT(*) FROM appt_event").fetchone()[0] == n_ev
           and "shivani" not in ro.list_holders() and "Alisha, Reception, Shavez see the tile" in hd and c7 == 200 and len(tables(ha)) == 3,
           "[S1 s7.py] THE TILE MASKED FOR ONE LOGIN: shivani's home has no tile -- and typing the address she is refused the page (403), both "
           "presses (403) and the card's new part; the doctor's box names the other three; alisha is as before", (c1, c2, c3, c4, c5, sorted(ro.list_holders())))
    finally:
        with open(g, "wb") as fh:
            fh.write(raw)
        os.utime(g, (time.time() + 10, time.time() + 10))
    ok(GET(w, "shivani", "/portal/ring/list")[0] == 200 and TILE in tiles(GET(w, "shivani", "/portal")[1]) and "shivani" in ro.list_holders(), "…the mask taken away: she has it all again")
    # ---- S5: a new caller whose number is not a mobile -- a landline, none at all, withheld
    odd = ["0" + "".join(RNG.choice("0123456789") for _ in range(6)), "", "anonymous"]
    for i, num in enumerate(odd):
        sid = "w497-odd%d" % i
        ro.record_call(sid, num, rc.lookup_caller(num), {"alisha": "Alisha"})
        ro.record_answered(sid, "alisha")
        ro.record_end(sid, "answered", {"alisha": "Alisha"}, ["alisha"])
        good, msg, _row = ro.file_outcome(sid, "appointment_booked", "alisha", "Alisha", "", now=at(w, 0, "16:0%d" % i))
        if not good:
            raise RuntimeError("the tap was refused for an odd number: %s" % msg)
    dd = ro.list_data("7")
    c, h = GET(w, "shivani", "/portal/ring/list")
    marked = [r for r in tables(h)[1][1] if len(r) > 2 and T_NO_MATCH in text_of(r[2])]
    ok(dd["visits_ok"] is True and "padha nahi ja saka" not in h and len(marked) == 3 and text_of(h).count(T_NO_MATCH) == 3
       and all((find(dd, "w497-odd%d" % i)[1] or {}).get("unmatchable") for i in range(3)) and find(dd, w.sid["r1"])[0] == "came",
       "[S5 s3.py] ODD NUMBERS DO NOT BLIND THE PAGE: three new callers with a landline, no number, a withheld one -- no banner, everyone else "
       "is confirmed as before; only those three lines say '%s'" % T_NO_MATCH, (dd["visits_ok"], len(marked)))
    p40, r40 = find(ro.list_data("aaj", now=noon(40)), "w497-odd2")
    shut = ro.close_appt(r40["id"], "shivani", "Shivani", now=noon(40)) if r40 else None
    ok(p40 == "noshow" and shut == (True, "ok"),
       "…and such a line does not sit there for ever: once its days are gone and Docterz reaches them it is in Nahi aaye like any "
       "other, where a person can press 'Ab nahi aayenge'", (p40, shut))
    keep = os.environ.pop("W497_SALT")
    try:
        d40 = ro.list_data("30", now=noon(40))
    finally:
        os.environ["W497_SALT"] = keep
    blind = [r for r in d40["due"] if r.get("unsure") and not r["known"] and not r.get("unmatchable")]
    ok(d40["visits_ok"] is False and len(blind) >= 2 and not [r for r in d40["noshow"] if not r["known"] and not r.get("unmatchable")]
       and find(d40, "w497-p_yest")[0] == "noshow" and "padha nahi ja saka" in text_of(ro.render_list(d40)),
       "[S5 s3.py] if the clinic's fingerprint cannot be made at all, the page SAYS so and no new MOBILE number is called a no-show (%d stay in "
       "Aane baaki); callers known by clinic ID are judged as before" % len(blind), (d40["visits_ok"], len(blind)))
    # ---- M3: a login is shown as a name
    m3 = {"darpan": number(w.taken), "reception": number(w.taken)}
    for sid, login in (("w497-m3a", "darpan"), ("w497-m3b", "reception")):
        ro.record_call(sid, m3[login], rc.lookup_caller(m3[login]), {login: login})
        ro.record_answered(sid, login)
        ro.record_end(sid, "answered", {login: login}, [login])
        ro.file_outcome(sid, "appointment_booked", login, login, "", now=at(w, 0, "16:1%d" % (0 if login == "darpan" else 1)))
    c, h = GET(w, "shivani", "/portal/ring/list")
    who = [seen(r[4]) for r in tables(h)[1][1] if len(r) > 4 and (spaced(m3["darpan"]) in r[2] or spaced(m3["reception"]) in r[2])]
    c2, hd = GET(w, "manoj", "/portal/ring/list")
    c3, hc = GET(w, "manoj", "/portal/ring/outcome?s=w497-m3a")
    ok(sorted(who) == ["Darpan", "Reception"] and "Shown to staff: <b>ON</b>. Alisha, Reception, Shavez, Shivani see the tile" in hd
       and text_of(hc).count("· Darpan") == 1 and not re.search(r">\s*(darpan|reception|alisha|shivani|shavez)\s*<", h + hd),
       "[M3] A LOGIN IS SHOWN AS A NAME: two appointments filed with only the bare login read 'Darpan' and 'Reception' under 'Kisne book kiya' "
       "(and on the card); his box names 'Alisha, Reception, Shavez, Shivani'", (who, text_of(hc)[:120]))
    # ---- M1: the 'Aur din' date boxes
    c, hl = GET(w, "shivani", "/portal/ring/list")
    c2, hc = GET(w, "alisha", "/portal/ring/outcome?s=" + w.sid["r4"])
    boxes = re.findall(r'<input (?:id="aurdin" )?type="date"[^>]*>', hl) + re.findall(r'<input (?:id="aurdin" )?type="date"[^>]*>', hc)
    lim = 'min="%s" max="%s"' % (T.isoformat(), (T + timedelta(days=366)).isoformat())
    ok(len(boxes) >= 2 and all(lim in b and 'onchange="s497date(this)"' in b and 'onkeydown="s497key(this,event)"' in b for b in boxes)
       and all("function s497good(i)" in p_ and "/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/" in p_ and "var v=s497good(i); if(!v){return;}" in p_ for p_ in (hl, hc)),
       "[M1] 'AUR DIN': every date box (%d on these two pages) carries today as its first day and a last day, and the page's script sends "
       "ONLY a whole date within them -- a part-typed one is not sent, so it cannot raise the bad-day alert" % len(boxes), boxes[:1])
    # ---- S7: on a phone the Mareez column stays in place while the table slides
    rule = "@media (max-width: 820px){th:nth-child(2),td:nth-child(2){position:sticky;left:0;z-index:1;background:#1e293b}}"
    style = (re.findall(r"(?s)<style>(.*?)</style>", hl) or [""])[0]
    ok(style.count(rule) == 1 and style.count("@media") == 1 and all(t[0][1] == "Mareez" for t in tables(hl)) and "position:sticky" not in hc,
       "[S7] ON A PHONE (820 px and under) the second column of each part -- Mareez -- stays at the left edge on the part's own background "
       "while the table slides; the rule is inside that one @media, so a wider screen is drawn exactly as before", style.count(rule))
    # ---- M2: the doctor's counts page
    c, hk = GET(w, "manoj", "/portal/ring/counts?day=%3Cscript%3E")
    ok(c == 200 and "Calls · &lt;script&gt;" in hk and "Calls · <script>" not in hk,
       "[M2 s4.py] the counts page writes the day from its address as text ('&lt;script&gt;'), not as markup", c)
    # ---- one served page that holds the lines added on 08-Oct, kept as the fifth screen
    w.clock[0] = noon(2)
    c, h5 = GET(w, "shivani", "/portal/ring/list?d=30")
    w.clock[0] = w.base
    t5 = text_of(h5)
    ok(c == 200 and T_UNSURE in t5 and T_NO_MATCH in t5 and " ki visit" in t5 and not re.search(u"[ऀ-ॿ]", h5),
       "two days on, one served page holds every line added on 08-Oct -- '%s', '%s', '… ki visit' -- in Roman letters (the fifth screen)" % (T_UNSURE, T_NO_MATCH))
    w.screen5 = h5
    quiet()
    ok(w.net == [], "…and still nothing tried to leave this machine", w.net[:3])


# ============================================================================================ PART R -- a copy of the real store
def part_r(w):
    ro = w.ro
    work = os.path.join(w.scratch, "real_copy.db")
    a = sqlite3.connect("file:%s?mode=ro" % w.args.db, uri=True, timeout=30)
    b = sqlite3.connect(work)
    a.backup(b)
    a.close()
    b.close()
    fin = None
    if w.args.finance_db and os.path.isfile(w.args.finance_db):
        try:                                                 # the visits only, copied out through a read-only door
            fin = os.path.join(w.scratch, "real_visits.db")
            src = sqlite3.connect("file:%s?mode=ro" % w.args.finance_db, uri=True, timeout=30)
            dst = sqlite3.connect(fin)
            dst.execute("CREATE TABLE patient_visit (visit_id TEXT PRIMARY KEY, visit_date TEXT NOT NULL, clinic_id TEXT, patient_uid TEXT, mobile_fp TEXT, had_procedure TEXT)")
            dst.executemany("INSERT OR IGNORE INTO patient_visit VALUES (?,?,?,?,?,?)",
                            src.execute("SELECT visit_id, visit_date, clinic_id, patient_uid, mobile_fp, had_procedure FROM patient_visit"))
            dst.commit()
            dst.close()
            src.close()
        except sqlite3.Error as ex:                          # busy just now: the part runs without the visits, and says so
            fin = None
            note("the visits could not be copied from %s just now (%s) -- part R runs without them" % (w.args.finance_db, type(ex).__name__))
    ro.now_ist = w.real_now
    try:
        con = sqlite3.connect(work)
        n_out = con.execute("SELECT COUNT(*) FROM outcome").fetchone()[0]
        n_appt = con.execute("SELECT COUNT(*) FROM outcome WHERE code='appointment_booked'").fetchone()[0]
        before = con.execute("SELECT * FROM outcome ORDER BY id").fetchall(), con.execute("SELECT * FROM call ORDER BY sid").fetchall()
        n_cols = len(con.execute("PRAGMA table_info(outcome)").fetchall())
        con.close()
        ro.init_db(work)
        con = sqlite3.connect(work)
        cols = [r[1] for r in con.execute("PRAGMA table_info(outcome)")]
        after = con.execute("SELECT %s FROM outcome ORDER BY id" % ", ".join(cols[:n_cols])).fetchall(), con.execute("SELECT * FROM call ORDER BY sid").fetchall()
        con.close()
        ok(after == before, "the real store's copy: the kit's init_db adds its columns; the %d outcomes and every call are as they were" % n_out)
        printed = table_print(work)
        for span in ("aaj", "7", "30"):
            d = ro.list_data(span, path=work, finance_db=fin or os.path.join(w.scratch, "none.db"), floor=HARD)
            n = (len(d["noshow"]), len(d["due"]), len(d["came"]))
            pages = [ro.render_list(d, doc, True, FOUR) for doc in (False, True)]
            good = d["store_ok"] and sum(n) <= n_appt and all([len(t[1]) if (t[1] and len(t[1][0]) > 1) else 0 for t in tables(p)] == list(n) for p in pages)
            ok(good, "%s: of %d appointments on file, IF he took 'follow from' back to %s -- %d Nahi aaye · %d Aane baaki · %d Aa gaye; each page draws one line per record%s"
               % (span, n_appt, hard_words(), n[0], n[1], n[2], "" if d["visits_ok"] else " (Docterz not confirmable in this walk)"), n)
        ok(table_print(work) == printed, "reading the real copy changed nothing in it")
        d0 = ro.list_data("30", path=work, finance_db=fin or os.path.join(w.scratch, "none.db"))
        note("as installed (never yet on, so only today's bookings are followed): %d Nahi aaye · %d Aane baaki · %d Aa gaye; Docterz visits in the copy reach %s"
             % (len(d0["noshow"]), len(d0["due"]), len(d0["came"]), d0["visits_through"] or "(not read)"))
        note("new numbers are not matched to visits in this part: the walk never reads the real fingerprint salt")
    finally:
        ro.now_ist = lambda: w.clock[0]


# ============================================================================================ the screens
def write_screens(w):
    out = w.args.screens
    os.makedirs(out, exist_ok=True)
    for name, attr in (("01_home_tile.html", "screen1"), ("02_table_staff.html", "screen2"), ("03_card_after_tap.html", "screen3"), ("04_owner_switch.html", "screen4"),
                       ("05_lines_added_08oct.html", "screen5")):
        h = getattr(w, attr, None)
        if h is None:
            note("screen %s was not reached" % name)
            continue
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(h)
    note("the four screens, and a fifth holding the lines added on 08-Oct, as served, are in %s (made-up names; numbers made for this run)" % out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kit", default=HERE)
    ap.add_argument("--portal", required=True)
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--now")
    ap.add_argument("--screens")
    ap.add_argument("--db")
    ap.add_argument("--finance-db", dest="finance_db")
    args = ap.parse_args()
    args.kit, args.portal = os.path.abspath(args.kit), os.path.abspath(args.portal)
    w = None
    try:
        w = build_world(args)
        w.base = datetime.strptime(args.now, "%Y-%m-%d %H:%M").replace(tzinfo=IST) if args.now else datetime.now(IST).replace(second=0, microsecond=0)
        w.today = w.base.date()
        if w.today - timedelta(days=6) < HARD:
            print("walk_s497: the made-up day must be %s or later -- the mock-up's day books six days back, and the list never follows an "
                  "appointment booked before %s." % ((HARD + timedelta(days=6)).isoformat(), hard_words()))
            shutil.rmtree(w.scratch, ignore_errors=True)
            return 2
        print("walk_s497: the made-up day is %s India time; process TZ=%s; the files under test: %s"
              % (w.base.strftime("%Y-%m-%d %H:%M"), os.environ.get("TZ", "(unset)"), "the LIVE files -- NEGATIVE CONTROL" if args.control else args.kit))
        part("PART S -- the files", part_s, w)
        print("PART 1 -- the mock-up's day")
        try:
            load_programs(w)
            sign_in(w)
            make_mockup_day(w)
        except Exception as ex:                              # noqa: BLE001
            traceback.print_exc()
            ok(False, "the scratch portal was built, signed in to and filled", repr(ex))
        else:
            part("", part_1, w)
            part("PART 2 -- what a person presses", part_2, w)
            part("PART 3 -- the rule", part_3, w)
            part("PART 4 -- the clock", part_4, w)
            part("PART 5 -- Docterz read-only; WhatsApp room only", part_5, w)
            part("PART 6 -- a store made by the live file", part_6, w)
            part("PART 7 -- the rest of what the review found", part_7, w)
            if args.screens:
                write_screens(w)
            if args.db:
                if os.path.isfile(args.db):
                    part("PART R -- a copy of the real store (counts only)", part_r, w)
                else:
                    note("no ring_outcomes.db at %s -- part R not run" % args.db)
    except Exception as ex:                                  # noqa: BLE001
        traceback.print_exc()
        ok(False, "the walk ran to its end", repr(ex))
    finally:
        if w is not None:
            shutil.rmtree(w.scratch, ignore_errors=True)
    bad = CHECKS.count(False)
    print("WALK_S497 %s" % (("GREEN %d checks" % len(CHECKS)) if not bad else ("RED %d failed of %d" % (bad, len(CHECKS)))))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    sys.exit(main())
