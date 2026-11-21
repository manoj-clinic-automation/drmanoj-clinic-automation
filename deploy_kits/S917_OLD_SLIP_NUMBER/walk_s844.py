#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s844.py -- the walk for kit S844_SLIP_NAME_AS_ID (session 469). Runs on a COPY of finance.db with made-up slips added;
prints counts and check names only -- never a name, an ID or a number from the copy.
  python3 walk_s844.py <kit dir> <live finance dir> <db copy>              -> last line 'WALK OK n/n'
  python3 walk_s844.py <kit dir> <live finance dir> <db copy> --control    -> last line 'CONTROL: red n/n'
"""
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile

KDIR, FIN, DB = (os.path.abspath(a) for a in sys.argv[1:4])
CAND = os.path.join(KDIR, "parchi_desk.py")


def walk(cand):
    ok, bad = [], []

    def t(name, cond):
        (ok if cond else bad).append(name)
    work = tempfile.mkdtemp(prefix="s844w_")
    try:
        mods = os.path.join(work, "mods")
        os.mkdir(mods)
        for f in os.listdir(FIN):
            if f.endswith(".py"):
                shutil.copy(os.path.join(FIN, f), mods)
        shutil.copy(cand, os.path.join(mods, "parchi_desk.py"))
        db = os.path.join(work, "f.db")
        shutil.copy(DB, db)
        sys.path.insert(0, mods)
        os.environ["FINANCE_DB"] = db
        from flask import Flask                         # noqa: PLC0415
        import slip_log                                 # noqa: PLC0415
        con = sqlite3.connect(db, timeout=10, check_same_thread=False)
        con.row_factory = sqlite3.Row
        slip_log.ensure(con)
        U = {"u": {"user": "shavez", "roles": ["maker"]}}
        audits = []

        def require(*roles, unit=None):
            r = set(U["u"]["roles"])
            return (U["u"], None) if r & set(roles) else (None, ("denied", 403))

        def audit(c, table, rid, action, before=None, after=None, who=""):
            audits.append(action)
        app = Flask("s844walk")
        app.secret_key = "x"
        slip_log.init(app, lambda: con, require, audit, unit="slips")
        import parchi_desk as PD                        # noqa: PLC0415
        cl = app.test_client()
        today = slip_log._today()
        real = con.execute("SELECT COUNT(*) FROM slip s WHERE s.state='ok' AND s.clinic_id<>'' AND s.clinic_id GLOB '*[A-Za-z]*' "
                           "AND NOT EXISTS (SELECT 1 FROM patient_ref p WHERE p.clinic_id=s.clinic_id AND (p.merged_into IS NULL OR p.merged_into='')) "
                           "AND NOT EXISTS (SELECT 1 FROM clinic_day_line l WHERE l.clinic_id=s.clinic_id AND l.patient<>'')").fetchone()[0]
        known_letter = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id GLOB '*[A-Za-z]*' AND (merged_into IS NULL OR merged_into='') LIMIT 1").fetchone()
        pid = con.execute("SELECT clinic_id FROM patient_ref WHERE clinic_id<>'' AND clinic_id NOT GLOB '*[^0-9]*' AND (merged_into IS NULL OR merged_into='') "
                          "ORDER BY id LIMIT 1").fetchone()[0]
        normal = con.execute("SELECT id FROM slip WHERE state='ok' AND clinic_id<>'' AND clinic_id NOT GLOB '*[^0-9]*' LIMIT 1").fetchone()[0]

        def mk(cid, state="ok", series="xp", no=0):
            c = con.execute("INSERT INTO slip(series, slip_no, day, clinic_id, state, logged_by, logged_at, updated_by, updated_at) "
                            "VALUES (?,?,?,?,?,'walk',?, 'walk', ?)", (series, no, today, cid, state, today + " 10:00:00", today + " 10:00:00"))
            con.commit()
            return c.lastrowid
        a = mk("Zqxwalkname", no=990001)
        b = mk("Zqxwalkcancel", state="cancelled", no=990002)
        kl = mk(known_letter[0], no=990003) if known_letter else None
        items = PD._s844_items(con)
        sids = [i["sid"] for i in items]
        t("w1 the real copy's slips with a name as the ID are listed, no more no fewer", len(items) == real + 1)
        t("w2 a made-up live slip with a name is listed", a in sids)
        t("w3 a cancelled slip with a name is not listed", b not in sids)
        t("w4 a letter ID the master knows is not listed", kl is None or kl not in sids)
        t("w5 a normal slip is not listed", normal not in sids)
        t("w6 every suggested patient's ID is digits only", all(p["id"].isdigit() for i in items for p in i["pats"]))
        t("w7 at most 4 suggestions, the 'came' ones first", all(len(i["pats"]) <= 4 and [p["came"] for p in i["pats"]] == sorted([p["came"] for p in i["pats"]], reverse=True) for i in items))
        h = PD._s844_box(items, False)
        t("w8 the box: title with the count, one row per slip", ("clinic ID nahi &mdash; %d" % len(items)) in h and h.count('class="s844r"') == len(items))
        t("w9 the box is English for the owner", "instead of a clinic ID" in PD._s844_box(items, True))
        t("w10 no box when nothing is wrong", PD._s844_box([], False) == "")
        r = cl.get("/finance/slips/desk")
        body = r.get_data(as_text=True)
        t("w11 the desk page carries the box", r.status_code == 200 and 'id="s844x"' in body and 'id="missing"' in body)

        def setid(sid, cid):
            return cl.post("/finance/slips/desk/api/set_id", json={"sid": sid, "clinic_id": cid}).get_json()
        t("s1 letters refused", setid(a, "Abc").get("ok") is False)
        if known_letter:
            t("s1b a letter ID refused even when the master knows it", setid(a, known_letter[0]).get("ok") is False)
        t("s2 an ID the clinic does not know refused", setid(a, "99999999999").get("ok") is False)
        t("s3 a normal slip cannot be re-IDed", setid(normal, pid).get("ok") is False)
        t("s4 a cancelled slip cannot be re-IDed", setid(b, pid).get("ok") is False)
        before = con.execute("SELECT clinic_id FROM slip WHERE id=?", (a,)).fetchone()[0]
        n0 = len(audits)
        r1 = setid(a, pid)
        row = con.execute("SELECT clinic_id, name_seen, updated_by FROM slip WHERE id=?", (a,)).fetchone()
        t("s5 a known ID is set on the slip", r1.get("ok") is True and row["clinic_id"] == pid and row["updated_by"] == "shavez" and before != pid)
        t("s6 the name is filled from the master", bool(row["name_seen"]))
        t("s7 audited once", audits[n0:] == ["slip_set_id_s844"])
        t("s8 the same slip cannot be set twice", setid(a, pid).get("ok") is False)
        t("s9 it leaves the list", a not in [i["sid"] for i in PD._s844_items(con)])
        U["u"] = {"user": "x", "roles": ["viewer"]}
        r = cl.post("/finance/slips/desk/api/set_id", json={"sid": a, "clinic_id": pid})
        t("s10 a login without the desk's roles is refused", r.status_code == 403)
        U["u"] = {"user": "shavez", "roles": ["maker"]}

        # the guard on the old pages' doors
        def post(path, **form):
            return cl.post(path, data=form)
        r = post("/finance/slips/save", series="opd", slip_no="1", clinic_id="Zqxwalkname")
        t("g1 save: a name refused", r.status_code == 303 and "Naam%20clinic%20ID" in (r.headers.get("Location") or ""))
        r = post("/finance/slips/save", series="opd", slip_no="1", clinic_id="Zqxwalkname", noid="1", no_id_name="Zqx")
        t("g2 save: 'ID nahi hai' passes to the door", "Naam%20clinic%20ID" not in (r.headers.get("Location") or ""))
        r = post("/finance/slips/save", series="opd", slip_no="1", clinic_id=pid)
        t("g3 save: a digit ID passes to the door", "Naam%20clinic%20ID" not in (r.headers.get("Location") or ""))
        if known_letter:
            r = post("/finance/slips/save", series="opd", slip_no="1", clinic_id=known_letter[0])
            t("g4 save: a letter ID the master knows passes", "Naam%20clinic%20ID" not in (r.headers.get("Location") or ""))
        n_bo = con.execute("SELECT COUNT(*) FROM blood_order").fetchone()[0]
        r = post("/finance/slips/blood", clinic_id="Zqxwalkname")
        t("g5 blood: a name refused, nothing written", "Naam clinic ID nahi hai" in r.get_data(as_text=True)
          and con.execute("SELECT COUNT(*) FROM blood_order").fetchone()[0] == n_bo)
        r = post("/finance/slips/pending/new", clinic_id="Zqxwalkname", name="Zqx")
        t("g6 walk-in blood: a name refused", "Naam%20clinic%20ID" in (r.headers.get("Location") or "")
          and con.execute("SELECT COUNT(*) FROM blood_order").fetchone()[0] == n_bo)
        r = post("/finance/slips/pending/act", key="nx:1", act="noid_pick", cid="Zqxwalkname")
        t("g7 lab report pick: a name refused", "Naam%20clinic%20ID" in (r.headers.get("Location") or ""))
        r = post("/finance/slips/pending/act", key="nx:1", act="mailed", cid="Zqxwalkname")
        t("g8 another act passes to the door", "Naam%20clinic%20ID" not in (r.headers.get("Location") or ""))
        r = cl.get("/finance/slips/blood")
        t("g9 a GET is never stopped", r.status_code == 200)
        sys.path.remove(mods)
        for m in ("slip_log", "parchi_desk", "check_screens", "records", "slip_adjust"):
            sys.modules.pop(m, None)
        con.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return ok, bad


MUT = [("the master's knowledge ignored", 'and not _SL().patient(con, cid)', ''),
       ("the guard switched off", '        if request.method != "POST":\n            return None\n        p = request.path',
        '        return None\n        p = request.path'),
       ("the desk's roles not checked on the fix", '    u, err = _gate()\n    if err:\n        return err\n    SL = _SL()\n    con = _db()\n    SL.ensure(con)\n    eng = _eng(u)\n    f = _body()\n    sid',
        '    u = {"user": "x", "roles": []}\n    SL = _SL()\n    con = _db()\n    SL.ensure(con)\n    eng = _eng(u)\n    f = _body()\n    sid'),
       ("letters accepted on the fix", 'if not sid or not cid or not re.fullmatch(r"\\d{1,12}", cid):', 'if not sid or not cid:'),
       ("cancelled slips listed", "FROM slip WHERE state='ok' AND clinic_id<>'' \"", "FROM slip WHERE clinic_id<>'' \"")]


if __name__ == "__main__":
    if "--control" in sys.argv:
        src = open(CAND, encoding="utf-8").read()
        reds = 0
        for name, a_, b_ in MUT:
            assert src.count(a_) == 1, "anchor: " + name
            d = tempfile.mkdtemp(prefix="s844c_")
            p = os.path.join(d, "parchi_desk.py")
            open(p, "w", encoding="utf-8").write(src.replace(a_, b_))
            out = subprocess.run([sys.executable, "-s", "-B", os.path.abspath(__file__), KDIR, FIN, DB, "--one", p],
                                 capture_output=True, text=True).stdout.strip().splitlines()
            last = out[-1] if out else "?"
            red = not last.startswith("WALK OK")
            reds += red
            print("  %-34s %s" % (name, "RED (%s)" % last if red else "GREEN -- the walk did not see it"))
            shutil.rmtree(d, ignore_errors=True)
        print("CONTROL: red %d/%d" % (reds, len(MUT)) if reds == len(MUT) else "CONTROL: NOT RED %d/%d" % (reds, len(MUT)))
    else:
        cand = sys.argv[sys.argv.index("--one") + 1] if "--one" in sys.argv else CAND
        ok, bad = walk(cand)
        for x in bad:
            print("BAD", x)
        n = len(ok) + len(bad)
        print("WALK OK %d/%d" % (n, n) if not bad else "WALK NOT OK %d/%d" % (len(ok), n))
