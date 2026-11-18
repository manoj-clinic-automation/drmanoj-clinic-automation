#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s890_app.py -- S890_RENEWALS_ONE_LIST on the REAL scan app: asset_register.py and every part it mounts, copied into a scratch
folder with the kit's asset_register.py + renewals_one.py (TO -- or the live files alone for the CONTROL, --expect-red), on a fresh
database the app makes itself. Made-up users, a made-up token, made-up renewal rows with made-up long numbers; nothing leaves the
process; the scratch folder is removed at the end. The walk never imports from its own folder (F-1415).

    python3 -B walk_s890_app.py --live <the app folder> --shared <the shared folder> --files <folder holding the kit files> [--expect-red] [--box]
"""
import datetime
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile

ARGS = sys.argv[1:]


def opt(n, d=None):
    return ARGS[ARGS.index(n) + 1] if n in ARGS else d


LIVE, FILES = opt("--live", "/root/assetapp"), opt("--files")
EXPECT_RED = "--expect-red" in ARGS
KIT_FILES = ("asset_register.py", "renewals_one.py")
GREEN_BOTH = ("A0", "Z1", "C1", "B24")                         # the app loads; an ordinary page; the old sections; two absence checks
TOKEN = "PUT-THE-TOKEN-HERE"                                          # a fixture: the walk sets this same string in the environment it makes
N = lambda *p: "".join(p)                                             # noqa: E731 -- made-up numbers built at run time, never written whole (F-1485)

if "--inner" not in ARGS:
    work = tempfile.mkdtemp(prefix="s890app_")
    try:
        app = os.path.join(work, "app")
        os.makedirs(app)
        for f in os.listdir(LIVE):
            p = os.path.join(LIVE, f)
            if os.path.isfile(p) and re.fullmatch(r"[A-Za-z0-9_]+\.(py|js|json)", f):
                shutil.copy(p, os.path.join(app, f))
        if FILES:
            for f in KIT_FILES:
                p = os.path.join(FILES, f)
                if os.path.isfile(p):
                    shutil.copy(p, os.path.join(app, f))
        SHARED = opt("--shared")
        if SHARED:
            shutil.copytree(SHARED, os.path.join(work, "shared"), ignore=shutil.ignore_patterns("*.pyc", "__pycache__"))
        os.makedirs(os.path.join(work, "uploads"))
        os.makedirs(os.path.join(work, "key"))
        os.makedirs(os.path.join(work, "fin"))
        open(os.path.join(work, "key", "anthropic.key"), "w").write("made-up-walk-key\n")
        fin, spn = os.path.join(work, "finance.db"), os.path.join(work, "spine.db")
        f = sqlite3.connect(fin)
        f.executescript("""
CREATE TABLE purchase_scan_link(bill_id INTEGER, asset_bill_id INTEGER, grade TEXT, matched_on TEXT, linked_at TEXT);
CREATE TABLE purchase_bill(id INTEGER PRIMARY KEY, supplier_norm TEXT, supplier TEXT, bill_no TEXT, bill_date TEXT, month TEXT, amount_p INTEGER, first_seen_day TEXT);
CREATE TABLE purchase_line(id INTEGER PRIMARY KEY, supplier_norm TEXT, bill_no TEXT, bill_date TEXT, month TEXT, item TEXT, packing TEXT, batch TEXT,
  expiry TEXT, tax REAL, qty REAL, free REAL, rate_p INTEGER, discount_pct REAL, amount_p INTEGER, net_rate_p INTEGER, net_amount_p INTEGER,
  loose_qty REAL, purchase_rate_p INTEGER, direction TEXT, source_md5 TEXT, line_type TEXT);
CREATE TABLE purchase_export(md5 TEXT PRIMARY KEY, type TEXT, received_at TEXT, superseded_by TEXT);
""")
        f.commit()
        f.close()
        s = sqlite3.connect(spn)
        s.execute("CREATE TABLE sp_purchase_bill (supplier TEXT, supkey TEXT, bill TEXT, date TEXT, amount_p INTEGER, direction TEXT, source_md5 TEXT)")
        s.commit()
        s.close()
        env = dict(os.environ, ASSETS_DB=os.path.join(work, "assets.db"), ASSETS_UPLOADS=os.path.join(work, "uploads"),
                   SHARED_LIB_DIR=os.path.join(work, "shared" if SHARED else "noshared"), SCANAPP_ANTHROPIC_KEY_FILE=os.path.join(work, "key", "anthropic.key"),
                   SCANAPP_ANTHROPIC_URL="https://made-up.invalid/v1", CLINIC_PORTAL_DIR=os.path.join(work, "noportal"),
                   FINANCE_LOCAL_URL="http://127.0.0.1:9", FINANCE_DB_FOR_SCANS=fin, SPINE_DB_FOR_SCANS=spn,
                   READER_WATCH_STATE=os.path.join(work, "rw_state.json"), READER_WATCH_STUB=os.path.join(work, "rw_sent.jsonl"),
                   READER_WATCH_ALL_OFF=os.path.join(work, "_off", "ALL_OFF"),
                   FINANCE_RENEWALS_TOKEN=TOKEN, FINANCE_RENEWALS_STATE=os.path.join(work, "fin", "renewals_state.json"))
        for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
            env.pop(k, None)
        r = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--inner", app, work] + ARGS, env=env, cwd=work,
                           capture_output=True, text=True, timeout=600)
        sys.stdout.write(r.stdout)
        for l in r.stderr.splitlines():
            if "NOT mounted" in l or "S890" in l or "renewals_one" in l:
                print("  stderr: " + l[:200])
        if r.returncode not in (0, 1) or os.environ.get("S890_WALK_DEBUG"):
            print(r.stderr[-3000:])
        sys.exit(r.returncode)
    finally:
        shutil.rmtree(work, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ inside the scratch process
APPD = ARGS[ARGS.index("--inner") + 1]
WORK = ARGS[ARGS.index("--inner") + 2]
_me = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") not in (_me, os.path.abspath("."))]   # never the kit's own copies (F-1415)
sys.path.insert(0, APPD)
RES = {}


def ck(name, fn, detail=None):
    try:
        ok = bool(fn())
        d = "" if ok or detail is None else detail()
    except Exception as e:                                           # noqa: BLE001
        ok, d = False, repr(e)
    RES[name.split(" ")[0]] = ok
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:500]) if (d and not ok) else ""))


import asset_register as ar                                          # noqa: E402

ro = sys.modules.get("renewals_one")
ck("A0 the real app loads", lambda: ar.app is not None)
dbp = os.environ["ASSETS_DB"]
db = sqlite3.connect(dbp, timeout=20)
db.row_factory = sqlite3.Row
for u_, r_ in (("walk_own_s890", "owner"), ("walk_mgr_s890", "manager")):
    db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (u_, u_, r_))
db.commit()
epoch = (db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone() or [""])[0]
TODAY = (datetime.datetime.utcnow() + datetime.timedelta(hours=5, minutes=30)).date()   # IST, as the module counts
D = lambda n: (TODAY + datetime.timedelta(days=n)).isoformat()      # noqa: E731


def client(name):
    c = ar.app.test_client()
    if name:
        with c.session_transaction() as ss:
            ss["uid"] = db.execute("SELECT id FROM users WHERE username=?", (name,)).fetchone()[0]
            ss["epoch"] = epoch
    return c


own, mgr, anon = client("walk_own_s890"), client("walk_mgr_s890"), client(None)
H = {"X-Finance-Renewals": TOKEN}


def page(c, path):
    r = c.get(path)
    return r.status_code, r.get_data(as_text=True)


def rows(q, *a):
    """[dict] -- [] when the table is not there (the CONTROL runs on the live files, which have no renewal_* tables)."""
    try:
        return [dict(r) for r in db.execute(q, a).fetchall()]
    except sqlite3.OperationalError:
        return []


def one(q, *a):
    r = rows(q, *a)
    return r[0] if r else {}


NONE = {"id": 0, "what": "", "grp": "", "expires_on": "", "remind_days": 0, "note": "", "last4": "", "closed": None}


def G(k):
    return items.get(k) or NONE


# ---- the seed door (made-up rows in the Janitor's own shape; the long numbers are made up) ------------------------------------
SEED = [
    {"vendor": "WALK Arms licence renewal - Owner (%s)" % N("99887", "7665544"), "dateISO": D(-50), "cycleMonths": 60, "note": "Expiry %s (walk). 90-day lead." % datetime.date.fromisoformat(D(38)).strftime("%d-%m-%Y")},
    {"vendor": "WALK Vento insurance", "dateISO": D(35), "cycleMonths": 12, "note": "ICICI ...%s" % N("12345", "6789")},
    {"vendor": "WALK passport renewal (%s)" % N("11223", "3445"), "dateISO": D(300 - 365), "cycleMonths": 120, "note": "Expires %s. 12-month lead." % datetime.date.fromisoformat(D(300)).strftime("%d-%b-%Y")},
    {"vendor": "WALK Marg ERP licence %s" % N("909", "090"), "dateISO": D(380), "cycleMonths": 12, "note": "walk"},
    {"vendor": "WALK Clinic trade licence", "dateISO": D(-12), "cycleMonths": 12, "note": "walk overdue"},
    {"vendor": "WALK Nagar Nigam renewal - Clinic", "firstISO": D(40), "title": "ANNUAL: WALK Nagar Nigam renewal - Clinic", "note": "Renew every January."},
    {"vendor": "WALK quiet subscription", "dateISO": D(200), "cycleMonths": 12, "note": "far away"},
    {"vendor": "WALK undated row", "dateISO": "TODO", "cycleMonths": 12, "note": "no date -> skipped, not stored"},
]
for s in SEED:
    if "title" in s:
        s.pop("vendor")
r0 = anon.post("/renewals/one/api/seed", json={"rows": SEED})
r1 = anon.post("/renewals/one/api/seed", json={"rows": SEED}, headers={"X-Finance-Renewals": "wrong"})
r2 = anon.post("/renewals/one/api/seed", json={"rows": SEED}, headers=H)
r3 = anon.post("/renewals/one/api/seed", json={"rows": SEED}, headers=H)
ck("B1 the seed door: no token 401, wrong token 401, the right token seeds 7 of 8 rows (the undated one skipped), a second seed is refused 409",
   lambda: r0.status_code == 401 and r1.status_code == 401 and r2.status_code == 200 and r2.get_json()["added"] == 7 and r3.status_code == 409,
   lambda: (r0.status_code, r1.status_code, r2.status_code, r2.get_json() if r2.status_code == 200 else r2.get_data(as_text=True)[:200], r3.status_code))
items = {r["what"]: r for r in rows("SELECT * FROM renewal_item WHERE closed=0")}
longnum = [r["what"] + "|" + r["note"] + "|" + r["last4"] for r in rows("SELECT * FROM renewal_item") if re.search(r"\d{5,}", r["what"] + r["note"] + r["last4"])]
ck("B2 no run of 5+ digits is stored anywhere: the bracketed number becomes last4 '5544', the licence number in the name reads '…9090', the note's '…6789'",
   lambda: not longnum and items.get("WALK Arms licence renewal - Owner", {"last4": ""})["last4"] == "5544"
   and "WALK Marg ERP licence …9090" in items and "…6789" in items["WALK Vento insurance"]["note"], lambda: (longnum, sorted(items)))
arms = G("WALK Arms licence renewal - Owner")
ck("B3 the real expiry is read as the Janitor read it: from the note when it is later than the alert day (arms %s), expiryISO/dateISO otherwise; "
   "groups guessed (arms Personal, Vento Vehicle, Nagar Nigam Civic, Marg NK Pathology); lead times by rule (passport 365, Vento insurance 30, arms 45)" % D(38),
   lambda: arms["expires_on"] == D(38) and arms["grp"] == "Personal" and arms["remind_days"] == 45
   and items["WALK Vento insurance"]["grp"] == "Vehicle" and items["WALK Vento insurance"]["remind_days"] == 30 and items["WALK Vento insurance"]["expires_on"] == D(35)
   and items["WALK passport renewal"]["remind_days"] == 365 and items["WALK passport renewal"]["expires_on"] == D(300)
   and items["WALK Nagar Nigam renewal - Clinic"]["grp"] == "Civic" and items["WALK Nagar Nigam renewal - Clinic"]["expires_on"] == D(40)
   and items["WALK Marg ERP licence …9090"]["grp"] == "NK Pathology",
   lambda: {k: (v["grp"], v["expires_on"], v["remind_days"]) for k, v in items.items()})

# ---- the page -----------------------------------------------------------------------------------------------------------------
c1, d1 = page(own, "/renewals")
ck("B4 the owner's Renewals page: 'Licences, documents and subscriptions', the due rows with days badges, the overdue one red, the far one hidden "
   "behind 'more beyond 60 days', + Add renewal and Mark renewed present",
   lambda: c1 == 200 and "Licences, documents and subscriptions" in d1 and "WALK Arms licence renewal - Owner" in d1 and "overdue 12 d" in d1
   and "WALK quiet subscription" not in d1 and "2 more beyond 60 days" in d1 and "+ Add renewal" in d1 and "Mark renewed" in d1, lambda: c1)
c1a, d1a = page(own, "/renewals?all=1")
ck("B4b show all: the far row appears too", lambda: c1a == 200 and "WALK quiet subscription" in d1a, lambda: c1a)
c2, d2 = page(mgr, "/renewals")
ck("B5 a manager sees the list without the Personal and Vehicle rows (arms, Vento, passport) but with the Clinic / Civic / NK rows",
   lambda: c2 == 200 and "WALK Arms licence" not in d2 and "WALK Vento" not in d2 and "WALK passport" not in d2
   and "WALK Clinic trade licence" in d2 and "WALK Nagar Nigam" in d2, lambda: c2)
ck("C1 the old sections of the page are still drawn (the heading 'Renewals &amp; warranties' and its due-soon line)",
   lambda: c1 == 200 and "Renewals &amp; warranties" in d1 and ("due soon only" in d1 or "show all upcoming" in d1), lambda: c1)

# ---- staff documents (F-1493: never on the page before) -----------------------------------------------------------------------
db.execute("INSERT INTO staff(name, role_title, status) VALUES('WALK Staff S890','walk','Active')")
sid = db.execute("SELECT id FROM staff WHERE name='WALK Staff S890'").fetchone()[0]
db.execute("INSERT INTO expiries(entity,entity_id,label,due_date,threshold_days) VALUES('staff',?,?,?,45)", (sid, "WALK police verification", D(20)))
db.commit()
c3, d3 = page(own, "/renewals")
ck("B6 a staff document's expiry reaches the Renewals page ('Staff documents', the person, the label, 20 days)",
   lambda: c3 == 200 and "Staff documents" in d3 and "WALK Staff S890" in d3 and "WALK police verification" in d3, lambda: c3)
ck("B7 the default lead time is 45 days (THRESHOLD_DEFAULT), not 60", lambda: ar.THRESHOLD_DEFAULT == 45, lambda: ar.THRESHOLD_DEFAULT)

# ---- the due list and the cadence --------------------------------------------------------------------------------------------
rd = anon.get("/renewals/one/api/due", headers=H)
due = rd.get_json() if rd.status_code == 200 else {}
whats = [x["what"] for x in due.get("items", [])]
ck("B8 the due list (token): the overdue licence, the arms licence (38 d, lead 45), the Nagar Nigam row (40 d), the passport (300 d, lead 365) are on it; "
   "Vento insurance (35 d, lead 30), Marg (380 d) and the quiet row are NOT; sorted worst first; subject + text composed; every item nag_today",
   lambda: rd.status_code == 200 and whats[0] == "WALK Clinic trade licence" and "WALK Arms licence renewal - Owner" in whats
   and "WALK Nagar Nigam renewal - Clinic" in whats and "WALK passport renewal" in whats and "WALK Vento insurance" not in whats
   and "WALK Marg ERP licence …9090" not in whats and "WALK quiet subscription" not in whats and due["nag_now"] is True
   and due["subject"].startswith("OVERDUE RENEWAL: WALK Clinic trade licence") and "expires in 38 day(s)" in due["text"]
   and all(x["nag_today"] for x in due["items"]), lambda: (rd.status_code, whats, due.get("subject")))
rs = anon.post("/renewals/one/api/due/sent", json={"ids": due.get("ids_to_mark", [])}, headers=H)
due2 = anon.get("/renewals/one/api/due", headers=H).get_json()
ck("B9 after 'sent', the same day's list carries the same items but none needs a nag (nag_now false) -- the cadence remembers",
   lambda: rs.status_code == 200 and rs.get_json()["marked"] == len(due["items"]) and len(due2["items"]) == len(due["items"]) and due2["nag_now"] is False,
   lambda: (rs.status_code, due2.get("nag_now")))
ck("B10 the token doors refuse without the token (due 401, sent 401, mail 401)",
   lambda: anon.get("/renewals/one/api/due").status_code == 401 and anon.post("/renewals/one/api/due/sent", json={}).status_code == 401
   and anon.post("/renewals/one/api/mail", json={}).status_code == 401)

# ---- Mark renewed -------------------------------------------------------------------------------------------------------------
aid = arms["id"]
rr = own.post("/renewals/one/renewed/%d" % aid, data={"new_expiry": D(38 + 1826), "number": "WALK %s" % N("0000", "11112222")})
old = one("SELECT * FROM renewal_item WHERE id=?", aid)
new = rows("SELECT * FROM renewal_item WHERE what=? AND closed=0", "WALK Arms licence renewal - Owner")
due3 = anon.get("/renewals/one/api/due", headers=H).get_json()
ck("B11 Mark renewed: the old row is closed with renewed_on and replaced_by (history kept), ONE new open row carries the new date and the new last 4 '2222', "
   "and the renewed item leaves the due list",
   lambda: rr.status_code in (302, 303) and old["closed"] == 1 and old["renewed_on"] == TODAY.isoformat() and len(new) == 1 and new[0]["expires_on"] == D(38 + 1826)
   and new[0]["last4"] == "2222" and old["replaced_by"] == new[0]["id"] and "WALK Arms licence renewal - Owner" not in [x["what"] for x in due3["items"]],
   lambda: (rr.status_code, dict(old) if old else None, [dict(x) for x in new]))
rp = own.post("/renewals/one/renewed/%d" % (new[0]["id"] if new else 0), data={"new_expiry": D(-3)})
ck("B12 a renewal to a past date is refused (400), nothing changes", lambda: rp.status_code == 400 and one("SELECT COUNT(*) c FROM renewal_item WHERE what=? AND closed=0", "WALK Arms licence renewal - Owner").get("c") == 1)
rm1 = mgr.post("/renewals/one/add", data={"what": "WALK manager personal", "grp": "Personal", "expires_on": D(100)})
rm2 = mgr.post("/renewals/one/add", data={"what": "WALK manager clinic %s" % N("55555", "66666"), "grp": "Clinic", "expires_on": D(100), "number": N("98765", "43210")})
ck("B13 a manager cannot add a Personal row (403) but can add a Clinic row; its long number is cut (…66666 -> '…6666'), last4 '3210', lead 45 by rule",
   lambda: rm1.status_code == 403 and rm2.status_code in (302, 303)
   and one("SELECT * FROM renewal_item WHERE what LIKE 'WALK manager clinic%'")["what"] == "WALK manager clinic …6666"
   and one("SELECT * FROM renewal_item WHERE what LIKE 'WALK manager clinic%'")["last4"] == "3210"
   and one("SELECT * FROM renewal_item WHERE what LIKE 'WALK manager clinic%'")["remind_days"] == 45,
   lambda: (rm1.status_code, rm2.status_code, [dict(x) for x in rows("SELECT * FROM renewal_item WHERE what LIKE 'WALK manager%'")]))
rm3 = mgr.post("/renewals/one/renewed/%d" % G("WALK Vento insurance")["id"], data={"new_expiry": D(400)})
ck("B14 a manager cannot mark a Vehicle row renewed (403)", lambda: rm3.status_code == 403 and one("SELECT closed FROM renewal_item WHERE id=?", G("WALK Vento insurance")["id"])["closed"] == 0)

# ---- mail intake and the one tap -----------------------------------------------------------------------------------------------
vento = G("WALK Vento insurance")
MAIL = {"mail_key": "walk-msg-0001", "received_at": TODAY.isoformat() + " 10:14", "sender": "care@made-up-insurer.invalid",
        "subject": "Policy schedule - WALK Vento insurance renewed",
        "excerpt": "Dear Customer, your WALK Vento policy %s is renewed. Period of insurance %s to %s (valid till midnight). Premium Rs 12,345."
                   % (N("44556", "6778899"), datetime.date.fromisoformat(D(35)).strftime("%d/%m/%Y"), datetime.date.fromisoformat(D(400)).strftime("%d/%m/%Y")),
        "attachments": ["policy_schedule.pdf"], "link": "https://mail.google.com/mail/u/0/#all/walkmsg0001"}
before = one("SELECT expires_on FROM renewal_item WHERE id=?", vento["id"]).get("expires_on")
rmx = anon.post("/renewals/one/api/mail", json=MAIL, headers=H)
rmy = anon.post("/renewals/one/api/mail", json=MAIL, headers=H)
m = rows("SELECT * FROM renewal_mail WHERE mail_key='walk-msg-0001'")
mid = m[0]["id"] if m else 0
after = one("SELECT expires_on FROM renewal_item WHERE id=?", vento["id"]).get("expires_on")
ck("B15 a renewal mail is stored ONCE (second post 'already'), matched to the Vento row, the later date read (%s), its numbers cut (…8899), the Gmail link kept -- "
   "and NOTHING on the row changed (no silent apply)" % D(400),
   lambda: rmx.status_code == 200 and rmx.get_json()["stored"] == 1 and rmy.get_json()["already"] == 1 and len(m) == 1 and m[0]["item_id"] == vento["id"]
   and m[0]["date_found"] == D(400) and N("44556", "6778899") not in m[0]["excerpt"] and "…8899" in m[0]["excerpt"] and m[0]["link"].startswith("https://mail.google.com/")
   and before == after == D(35), lambda: (rmx.status_code, rmx.get_json() if rmx.status_code == 200 else "", [dict(x) for x in m], before, after))
c4, d4 = page(own, "/renewals")
ck("B16 the page shows 'Found in your mail' with the subject, 'looks like' the Vento row, the mail's text, the attachment name, 'Open in Gmail', and the three taps",
   lambda: c4 == 200 and "Found in your mail" in d4 and "Policy schedule - WALK Vento insurance renewed" in d4 and "looks like <b>WALK Vento insurance</b>" in d4
   and "Period of insurance" in d4 and "policy_schedule.pdf" in d4 and "Open in Gmail" in d4 and ">Apply<" in d4 and ">Add as new<" in d4 and ">Not a renewal<" in d4,
   lambda: c4)
MAIL0 = dict(MAIL, mail_key="walk-msg-0000", subject="WALK unmatched personal mail about a passport", excerpt="nothing matches a row here %s" % N("12345", "6789"), attachments=[])
anon.post("/renewals/one/api/mail", json=MAIL0, headers=H)
c5, d5 = page(mgr, "/renewals")
c5o, d5o = page(own, "/renewals")
ign = mgr.post("/renewals/one/mail/%d/ignore" % mid)
ck("B17 a manager sees neither the mail matched to a Vehicle row nor an unmatched mail (his personal Gmail stays his), and cannot dismiss the Vehicle one (403); the owner sees both",
   lambda: c5 == 200 and "WALK Vento insurance renewed" not in d5 and "WALK unmatched personal mail" not in d5 and ign.status_code == 403
   and one("SELECT status FROM renewal_mail WHERE id=?", mid).get("status") == "open" and "WALK unmatched personal mail" in d5o and "WALK Vento insurance renewed" in d5o,
   lambda: (c5, ign.status_code, "WALK unmatched personal mail" in d5, "WALK Vento insurance renewed" in d5))
ra = own.post("/renewals/one/mail/%d/apply" % mid, data={"new_expiry": D(400)})
vnew = rows("SELECT * FROM renewal_item WHERE what='WALK Vento insurance' AND closed=0")
vold = one("SELECT * FROM renewal_item WHERE id=?", vento["id"])
ms = one("SELECT status, decided_by FROM renewal_mail WHERE id=?", mid)
c6, d6 = page(own, "/renewals")
ck("B18 Apply (the one tap): the Vento row is renewed to the mail's date (old closed, new open, source 'mail'), the mail is 'applied' with who, and leaves the page (the unmatched one stays)",
   lambda: ra.status_code in (302, 303) and vold["closed"] == 1 and len(vnew) == 1 and vnew[0]["expires_on"] == D(400) and vnew[0]["source"] == "mail"
   and ms["status"] == "applied" and ms["decided_by"] == "walk_own_s890" and c6 == 200 and "WALK Vento insurance renewed" not in d6 and "WALK unmatched personal mail" in d6,
   lambda: (ra.status_code, dict(vold), [dict(x) for x in vnew], dict(ms)))
ck("B19 a second tap on the same mail is 404", lambda: m and own.post("/renewals/one/mail/%d/apply" % mid).status_code == 404)
MAIL2 = dict(MAIL, mail_key="walk-msg-0002", subject="Your WALK domain something.invalid has been renewed", excerpt="Renewed for 1 year. Order 99887766.", attachments=[])
anon.post("/renewals/one/api/mail", json={"mails": [MAIL2]}, headers=H)
m2 = one("SELECT * FROM renewal_mail WHERE mail_key='walk-msg-0002'") or dict(NONE, item_id=1)
rad = own.post("/renewals/one/mail/%d/add" % m2["id"], data={"what": "WALK something.invalid domain", "grp": "Clinic", "new_expiry": D(365)})
added = rows("SELECT * FROM renewal_item WHERE what='WALK something.invalid domain' AND closed=0")
ck("B20 a mail with no matched row: 'Add as new' makes the row with the typed name, group and date (source 'mail'); the mail is 'added'",
   lambda: m2["item_id"] is None and rad.status_code in (302, 303) and len(added) == 1 and added[0]["expires_on"] == D(365) and added[0]["grp"] == "Clinic"
   and one("SELECT status FROM renewal_mail WHERE id=?", m2["id"]).get("status") == "added", lambda: (dict(m2), rad.status_code))
MAIL3 = dict(MAIL, mail_key="walk-msg-0003", subject="WALK newsletter about insurance", excerpt="nothing here", attachments=[])
anon.post("/renewals/one/api/mail", json=MAIL3, headers=H)
m3 = one("SELECT * FROM renewal_mail WHERE mail_key='walk-msg-0003'") or NONE
rig = own.post("/renewals/one/mail/%d/ignore" % m3["id"])
ck("B21 'Not a renewal' closes the mail as ignored; nothing added", lambda: rig.status_code in (302, 303) and one("SELECT status FROM renewal_mail WHERE id=?", m3["id"]).get("status") == "ignored"
   and one("SELECT COUNT(*) c FROM renewal_item WHERE what LIKE '%newsletter%'").get("c") == 0)

# ---- the health file and the count --------------------------------------------------------------------------------------------
try:
    st = json.load(open(os.environ["FINANCE_RENEWALS_STATE"], encoding="utf-8"))
except (OSError, ValueError):
    st = {}
ck("B22 the health page's file is written from the list in the shape the finance app reads (items with vendor / dateISO / expiryISO; the overdue licence and the "
   "Nagar Nigam row in, the passport (300 d) out), with received_at",
   lambda: isinstance(st.get("items"), list) and st.get("received_at") and {"WALK Clinic trade licence", "WALK Nagar Nigam renewal - Clinic"} <= {x["vendor"] for x in st["items"]}
   and "WALK passport renewal" not in {x["vendor"] for x in st["items"]} and all({"vendor", "dateISO", "expiryISO"} <= set(x) for x in st["items"]),
   lambda: st)
rc = own.get("/renewals/one/api/count").get_json() or {}
rcm = mgr.get("/renewals/one/api/count").get_json() or {}
rca = anon.get("/renewals/one/api/count").get_json() or {"n": 0}
ck("B23 the count door: the owner counts every due-or-overdue row (licence, Nagar Nigam, passport = 3), a manager only his groups (2), not signed in -> n null",
   lambda: rc.get("n") == 3 and rcm.get("n") == 2 and rca.get("n") is None, lambda: (rc, rcm, rca))
STRIP = lambda h: re.sub(r"#[0-9a-fA-F]{6}\b", "", re.sub(r"\d{4}-\d{2}-\d{2}", "", h))   # noqa: E731 -- dates and CSS colours are not numbers
ck("B24 the owner's page carries no run of 5+ digits anywhere (numbers cut; dates, years and CSS colours stand)",
   lambda: not re.search(r"\d{5,}", STRIP(d6)), lambda: re.findall(r".{0,60}\d{5,}.{0,20}", STRIP(d6))[:5])
cz, dz = page(own, "/assets")
ck("Z1 an ordinary page of the app still answers (Machines)", lambda: cz == 200, lambda: cz)
db.close()
red = [k for k, v in RES.items() if not v]
if EXPECT_RED:
    bad_ = [k for k in GREEN_BOTH if not RES.get(k)] + [k for k, v in RES.items() if v and k not in GREEN_BOTH]
    print("WALK S890 APP CONTROL: %d red; %s" % (len(red), "AS IT MUST BE (every new check red; the app, the old sections and an ordinary page green)" if not bad_
                                                   else "NOT AS IT MUST BE: " + ", ".join(bad_)))
    sys.exit(0 if not bad_ else 1)
print("WALK S890 APP: %d green, %d red" % (len(RES) - len(red), len(red)))
sys.exit(0 if not red else 1)
