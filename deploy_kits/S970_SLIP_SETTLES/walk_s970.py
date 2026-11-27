#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s970.py -- the walk of kit S970_SLIP_SETTLES (the parent, S531, 27-Nov-2026).

    python3 walk_s970.py walk <dir>                 part A: register_push.py from <dir> with made-up day checks. ALL PASS, exit 0.
    python3 walk_s970.py live <dir> <appdir> <db>   part B: the real modules (<appdir>, with <dir>'s two files over them) on a
                                                    COPY of <db> in a temp folder; a made-up slip and Rs 100 added. COUNTS ONLY.
On the FROM files both parts go red -- the control. Made-up IDs and amounts only; no name, no number; never the network.
"""
import datetime as dt
import os
import shutil
import sqlite3
import sys
import tempfile
import types

PASS, FAIL = [], []
AT = dt.datetime(2026, 11, 27, 12, 50)


def ok(cond, name):
    (PASS if cond else FAIL).append(name)
    print(("  PASS  " if cond else "  FAIL  ") + name)


def _stub_flask():
    try:
        import flask  # noqa: F401
        return
    except Exception:                                                   # noqa: BLE001
        pass
    f = types.ModuleType("flask")

    class _BP(object):
        def __init__(self, *a, **k):
            pass

        def route(self, *a, **k):
            return lambda fn: fn

        def before_app_request(self, fn):
            return fn
    f.Blueprint = _BP
    f.request = types.SimpleNamespace(args={}, form={}, method="GET", headers={})
    for n in ("redirect", "jsonify", "Response", "abort", "make_response", "send_file"):
        setattr(f, n, lambda *a, **k: (a, k))
    sys.modules["flask"] = f


class FakeDC(object):
    def __init__(self):
        self.chk, self.reads = {}, 0

    def check_day(self, con, day):
        self.reads += 1
        return dict(self.chk.get(day) or {"state": "no_register", "day": day})

    @staticmethod
    def is_clean(chk):
        return chk.get("state") == "checked" and not chk.get("cards") and not chk.get("backdate") \
            and not (chk.get("top") or {}).get("left")

    @staticmethod
    def summary_hi(chk):
        return "%s: kuch" % chk.get("day")


class FakeNID(object):
    """mark() writes a row the way not_in_docterz.mark does (live), and takes the row off the fake day's back-date list."""
    def __init__(self, fake, day):
        self.fake, self.day, self.boom = fake, day, False

    def mark(self, con, who, slip_id, kind, act):
        if self.boom:
            raise RuntimeError("refused")
        con.execute("CREATE TABLE IF NOT EXISTS nid_mark (id INTEGER PRIMARY KEY AUTOINCREMENT, slip_id INTEGER, kind TEXT, act TEXT, "
                    "who TEXT, state TEXT DEFAULT 'live')")
        con.execute("INSERT INTO nid_mark (slip_id, kind, act, who) VALUES (?,?,?,?)", (slip_id, kind, act, who))
        con.commit()
        c = self.fake.chk[self.day]
        c["backdate"] = [b for b in c["backdate"] if (b["slip_id"], b["kind"]) != (slip_id, kind)]
        return 1


def walk_a(d):
    sys.path.insert(0, d)
    _stub_flask()
    import register_push as rp                                          # noqa: E402
    if os.path.dirname(os.path.abspath(rp.__file__)) != os.path.abspath(d):
        raise SystemExit("REFUSED: register_push did not load from %s" % d)
    tmp = tempfile.mkdtemp(prefix="s970a_")
    try:
        db = os.path.join(tmp, "a.db")
        con = sqlite3.connect(db)
        con.row_factory = sqlite3.Row
        con.execute("CREATE TABLE clinic_register_day (business_date TEXT PRIMARY KEY)")
        D = "2026-11-26"
        con.execute("INSERT INTO clinic_register_day VALUES (?)", (D,))
        con.commit()
        fake = FakeDC()
        nid = FakeNID(fake, D)
        rp.DC_MOD, rp.LIVE_DB = fake, db
        if hasattr(rp, "NID_MOD"):
            rp.NID_MOD = nid
        sent = []
        rp._send = lambda who, title, body, tag: (sent.append(title) or ((len(who), 0, 0), ""))
        os.environ.pop("REGPUSH_AUTO_OUTSIDE", None)
        os.environ.pop("REGPUSH_ON", None)

        def bd(sid, kind="proc", placed=True):
            return {"key": "k%d" % sid, "slip_id": sid, "kind": kind, "cid": "c", "name": "", "amount": 10000, "placed": placed,
                    "allp": placed}

        def marks():
            try:
                return con.execute("SELECT slip_id, kind, act, who, state FROM nid_mark ORDER BY id").fetchall()
            except sqlite3.Error:
                return []
        fake.chk[D] = {"state": "no_register", "day": D}
        rp.one_day(con, D, at=AT, from_save=True)
        ok(not marks(), "A1 a day not yet checked: nothing answered")
        fake.chk[D] = {"state": "checked", "day": D, "cards": [], "backdate": [bd(11), bd(12, placed=False), bd(13, "opd")]}
        r0 = fake.reads
        w = rp.one_day(con, D, at=AT, from_save=True)
        m = marks()
        ok([(x[0], x[1]) for x in m] == [(11, "proc"), (13, "opd")], "A2 the slips whose money the register holds: answered by themselves")
        ok(all(x[2] == "outside" and x[3] == "auto" for x in m), "A3 the answer is 'Not entering in Docterz', given by 'auto'")
        ok(not any(x[0] == 12 for x in m), "A4 a slip whose money the register does NOT hold: left for him")
        ok(fake.reads - r0 == 2, "A5 the day read afresh after answering (the pushed words follow the new answer)")
        ok(" clean " not in w, "A6 the day still has his row 12: not 'sab mile'")
        rp.sweep(con, at=AT)
        ok(len(marks()) == 2, "A7 the next sweep: nothing answered twice")
        con.execute("UPDATE nid_mark SET state='undone' WHERE slip_id=11")
        con.commit()
        fake.chk[D]["backdate"].append(bd(11))
        rp.sweep(con, at=AT)
        ok(len(marks()) == 2, "A8 a row he undid comes back: never answered again (an Undo is final)")
        fake.chk[D]["backdate"] = [b for b in fake.chk[D]["backdate"] if b["slip_id"] != 11] + [bd(21)]
        os.environ["REGPUSH_AUTO_OUTSIDE"] = "0"
        rp.sweep(con, at=AT)
        ok(len(marks()) == 2, "A9 REGPUSH_AUTO_OUTSIDE=0: nothing answered")
        os.environ.pop("REGPUSH_AUTO_OUTSIDE", None)
        nid.boom = True
        try:
            w = rp.one_day(con, D, at=AT, from_save=True)
            fine = True
        except Exception:                                               # noqa: BLE001
            fine = False
        ok(fine and len(marks()) == 2, "A10 an answer refused: the day is still judged, nothing raised")
        nid.boom = False
        fake.chk[D]["backdate"] = [dict(bd(31), slip_id=None), dict(bd(32), kind="xx"), dict(bd(33), slip_id="x")]
        rp.sweep(con, at=AT)
        ok(len(marks()) == 2, "A11 a row with no slip, an unknown kind or a bad slip id: skipped")
        fake.chk[D]["backdate"] = [bd(41)]
        rp.sweep(con, at=AT)
        ok(len(marks()) == 3 and marks()[-1][0] == 41, "A12 the sweep (every 5 minutes) answers a slip made later in the morning")
        fake.chk[D]["backdate"] = [dict(bd(51), allp=False)]
        rp.sweep(con, at=AT)
        ok(len(marks()) == 3, "A14 a row only partly held by the register (one of its lines): left for him")
        T = AT.date().isoformat()
        con.execute("INSERT INTO clinic_register_day VALUES (?)", (T,))
        con.commit()
        fake.chk[T] = {"state": "checked", "day": T, "cards": [], "backdate": [bd(61)]}
        nid.day = T
        rp.one_day(con, T, at=AT, from_save=True)
        ok(len(marks()) == 3, "A15 today's day (a register saved early): never answered -- the evening list is the staff's")
        nid.day = D
        fake.chk[D] = {"state": "checked", "day": D, "cards": [], "backdate": [], "top": {"left": 0}}
        n0 = len(sent)
        rp.sweep(con, at=AT)
        ok(len(sent) == n0, "A13 the push's own rules unchanged (a day already told stays quiet)")
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def walk_b(d, appdir, db):
    tmp = tempfile.mkdtemp(prefix="s970b_")
    try:
        os.chmod(tmp, 0o700)
        app = os.path.join(tmp, "app")
        shutil.copytree(appdir, app)
        for n in ("register_push.py", "day_check.py"):
            shutil.copy(os.path.join(d, n), os.path.join(app, n))
        sys.path.insert(0, app)
        _stub_flask()
        for n in ("register_push", "day_check", "not_in_docterz"):
            sys.modules.pop(n, None)
        import register_push as rp                                      # noqa: E402
        import day_check as dc                                          # noqa: E402
        import not_in_docterz as nid                                    # noqa: E402
        for m in (rp, dc, nid):
            if os.path.dirname(os.path.abspath(m.__file__)) != app:
                raise SystemExit("REFUSED: %s did not load from the walk's copy" % m.__name__)
        rp.DC_MOD = rp.NID_MOD = None
        os.environ.pop("REGPUSH_AUTO_OUTSIDE", None)
        cp = os.path.join(tmp, "copy.db")
        src = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        dst = sqlite3.connect(cp)
        src.backup(dst)
        src.close()
        dst.close()
        rp.LIVE_DB = os.path.join(tmp, "never.db")
        # B0: what the install would answer on the real days (counts only)
        con = sqlite3.connect(cp)
        con.row_factory = sqlite3.Row
        res = rp.sweep(con, push=False, at=AT)
        errs = sum(1 for w in res if " error " in w)
        try:
            n_auto = con.execute("SELECT COUNT(*) FROM nid_mark WHERE who='auto'").fetchone()[0]
        except sqlite3.Error:
            n_auto = 0
        print("LIVE install sweep: days told %d, errors %d, rows answered by themselves %d" % (len(res), errs, n_auto))
        ok(errs == 0, "B0 the real last week swept with no error")
        con.close()
        # B1..: the 26-Nov case made up on a fresh copy of the newest day with a register and an export
        nid._done = False                                               # its table flag belongs to the first copy
        src = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
        cp2 = os.path.join(tmp, "copy2.db")
        dst = sqlite3.connect(cp2)
        src.backup(dst)
        src.close()
        dst.close()
        con = sqlite3.connect(cp2)
        con.row_factory = sqlite3.Row
        D = con.execute("SELECT MAX(r.business_date) FROM clinic_register_day r JOIN clinic_day_revenue v ON v.business_date=r.business_date").fetchone()[0]
        CID = "987654321"                                               # made up; on no patient
        ok(con.execute("SELECT COUNT(*) FROM clinic_day_line WHERE clinic_id=?", (CID,)).fetchone()[0] == 0, "B1 the made-up ID is nobody's")
        base = dc.check_day(con, D)
        con.execute("UPDATE clinic_register_day SET dress_cash_p=COALESCE(dress_cash_p,0)+10000 WHERE business_date=?", (D,))
        no = (con.execute("SELECT MAX(slip_no) FROM slip WHERE series='xp'").fetchone()[0] or 0) + 1
        cur = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, paid_mode, name_seen, logged_by, logged_at) "
                          "VALUES ('xp',?,?,?,'ok','cash','','walk',?)", (no, D, CID, D + " 20:10:00"))
        sid = cur.lastrowid
        con.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, sort, discount_p) VALUES (?,'proc','Dressing','',10000,1,0)", (sid,))
        con.commit()
        c0 = dc.check_day(con, D)
        mine = [b for b in (c0.get("backdate") or []) if b.get("slip_id") == sid]
        ok(len(mine) == 1 and mine[0]["placed"], "B2 the day check (TO): the slip on his back-date list, its money in the register")
        left0 = (c0.get("top") or {}).get("left")
        ok(left0 == (base.get("top") or {}).get("left"), "B3 the register's extra Rs 100 is placed on the slip (the day's 'left' unchanged)")
        rp.judge(con, D, push=False, at=AT, from_save=True)
        m = con.execute("SELECT id, act, who, state, amount_p FROM nid_mark WHERE slip_id=? AND kind='proc'", (sid,)).fetchall()
        ok(len(m) == 1 and tuple(m[0][1:]) == ("outside", "auto", "live", 10000), "B4 judged: answered 'Not entering in Docterz' by 'auto', Rs 100")
        c1 = dc.check_day(con, D)
        ok(not [b for b in (c1.get("backdate") or []) if b.get("slip_id") == sid], "B5 the slip has left his back-date list")
        ok((c1.get("top") or {}).get("left") == left0, "B6 the day's 'left' unchanged (no money counted twice)")
        ok(any("kept outside Docterz automatically" in n[0] for n in c1.get("notes") or []), "B7 the day's notes say why, in words")
        ok(10000 in nid.outside_for_day(con, D), "B8 his money page reads it as 'Slips outside Docterz'")
        ok(not any(c.get("who") in ("docterz", "parchi") and "987654321" in str(c.get("cid")) for c in c1.get("cards") or []),
           "B9 no staff card for the slip")
        nid.undo(con, "manoj", m[0][0])
        rp.judge(con, D, push=False, at=AT, from_save=True)
        live = con.execute("SELECT COUNT(*) FROM nid_mark WHERE slip_id=? AND state='live'", (sid,)).fetchone()[0]
        c2 = dc.check_day(con, D)
        ok(live == 0 and [b for b in (c2.get("backdate") or []) if b.get("slip_id") == sid], "B10 he undoes it: back on his list, never re-answered")
        nid.mark(con, "manoj", sid, "proc", "outside")
        o_before = sum(nid.outside_for_day(con, D))           # the day may hold real slips of the same amount: compare sums
        con.execute("INSERT INTO clinic_day_line (business_date, section, sn, patient, clinic_id, amount_p, mode) VALUES (?,'proc',990,'x',?,10000,'Cash')", (D, CID))
        con.commit()
        c3 = dc.check_day(con, D)
        ok(sum(nid.outside_for_day(con, D)) == o_before - 10000 and not any(r["slip_id"] == sid for r in nid.rows(con, D, D))
           and (c3.get("top") or {}).get("left") == left0,
           "B11 Docterz carries it later: the answer leaves with the row, nothing counted twice")
        con.close()
        # B12: a slip of two lines, the register holding only one -- left for him (cold review MUST)
        def fresh(name):
            s = sqlite3.connect("file:%s?mode=ro" % db, uri=True)
            p = os.path.join(tmp, name)
            t2 = sqlite3.connect(p)
            s.backup(t2)
            s.close()
            t2.close()
            nid._done = False
            c = sqlite3.connect(p)
            c.row_factory = sqlite3.Row
            return c

        def slip(c, cid, prices, room):
            c.execute("UPDATE clinic_register_day SET dress_cash_p=COALESCE(dress_cash_p,0)+? WHERE business_date=?", (room, D))
            n2 = (c.execute("SELECT MAX(slip_no) FROM slip WHERE series='xp'").fetchone()[0] or 0) + 1
            s2 = c.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, paid_mode, name_seen, logged_by, logged_at) "
                           "VALUES ('xp',?,?,?,'ok','cash','','walk',?)", (n2, D, cid, D + " 20:10:00")).lastrowid
            for i, pr in enumerate(prices):
                c.execute("INSERT INTO slip_item (slip_id, kind, name, side, price_p, sort, discount_p) VALUES (?,'proc','Dressing','',?,?,0)",
                          (s2, pr, i + 1))
            c.commit()
            return s2
        con = fresh("copy3.db")
        spare = max(0, (dc.check_day(con, D).get("top") or {}).get("left") or 0)   # the day's own unexplained money, if any
        sid3 = slip(con, CID, [50000, 50000 + spare + 100000], 50000)            # the bigger line can never fit the room
        c4 = dc.check_day(con, D)
        r4 = [b for b in (c4.get("backdate") or []) if b.get("slip_id") == sid3]
        rp.judge(con, D, push=False, at=AT, from_save=True)
        n4 = con.execute("SELECT COUNT(*) FROM nid_mark WHERE slip_id=?", (sid3,)).fetchone()[0] if con.execute(
            "SELECT 1 FROM sqlite_master WHERE name='nid_mark'").fetchone() else 0
        ok(len(r4) == 1 and r4[0]["placed"] and not r4[0].get("allp") and n4 == 0,
           "B12 a slip of two lines, the register holding one: not answered (the row stays his)")
        con.close()
        # B13: an auto answer, then Docterz's clinical report knows the visit -- the old answer hides no staff card
        con = fresh("copy4.db")
        fee = int(nid._SL().usual_fee(con, D) or 0)
        con.execute("UPDATE clinic_register_day SET cons_cash_p=COALESCE(cons_cash_p,0)+? WHERE business_date=?", (fee, D))
        n6 = (con.execute("SELECT MAX(slip_no) FROM slip WHERE series='opd'").fetchone()[0] or 0) + 1
        sid5 = con.execute("INSERT INTO slip (series, slip_no, day, clinic_id, state, paid_mode, name_seen, logged_by, logged_at) "
                           "VALUES ('opd',?,?,?,'ok','cash','','walk',?)", (n6, D, CID, D + " 20:10:00")).lastrowid
        con.commit()
        rp.judge(con, D, push=False, at=AT, from_save=True)
        n5 = con.execute("SELECT COUNT(*) FROM nid_mark WHERE slip_id=? AND kind='opd' AND who='auto' AND state='live'", (sid5,)).fetchone()[0]
        con.execute("INSERT INTO dx_visit (patient_uid, visit_date, clinic_id, diagnosis_raw, std_dx, category, priority, dx_status, "
                    "follow_up_date, export_id, updated_at) VALUES ('w',?,?,'','','','','','','w','')", (D + " 10:00", CID))
        con.commit()
        c5 = dc.check_day(con, D)
        ok(n5 == 1 and any(c.get("who") == "docterz" and str(c.get("cid")) == CID for c in c5.get("cards") or [])
           and ((c5.get("top") or {}).get("missing") or 0) >= fee > 0,
           "B13 an OPD slip answered by itself, then Docterz's clinical report knows the visit: the staff card comes back, the old answer is not used")
        con.close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(a):
    try:
        if a[:1] == ["walk"] and len(a) == 2:
            walk_a(a[1])
        elif a[:1] == ["live"] and len(a) == 4:
            walk_b(a[1], a[2], a[3])
        else:
            print(__doc__)
            return 2
    except SystemExit:
        raise
    except Exception as ex:                                             # noqa: BLE001 -- a crash is a FAIL, never a pass
        FAIL.append("crash")
        print("  FAIL  crash: %s" % type(ex).__name__)
    print("%s %d/%d" % ("ALL PASS" if not FAIL else "RED", len(PASS), len(PASS) + len(FAIL)))
    return 0 if not FAIL else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

