#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s575.py -- the S575_BATTERY_SETUP walk. The app with the given files on a COPY of a database (SQLite's backup API), in its own
scratch folder; made-up rows only: places 'WALK575 ..' (added through the page's own form), papers of 'B.L. Computers WALK575 ..' /
'Jasoria WALK575 ..' / 'Other Supplier WALK575 ..' with stamps the walk picks from numbers no paper of the copy has (B-9nnn), dated
around a made-up today of 15-Jun-2031, injected; made-up logins (walk_own_2031 / walk_mgr_2031, made here); no reader thread, no
paid call, nothing sent anywhere (a made-up key and URL). Flask's test client; no port. Every place, fitting and paper the walk uses
is found by its key (the place's name, the paper's stamp or id), never by counting rows; a total is compared before / after.

    python3 -B walk_s575.py <dir with asset_register.py, clinic_papers.py, claude_reader.py, claude_reread.py, sorting_desk.py,
                             asset_machine.py, scanner_widget.js, stationery.py, batteries.py> <assets.db to copy>
                            [--work DIR] [--shared DIR] [--expect-red] [--keep] [--save-pages DIR]

One named check per brief item 1-4 (I1..I4), I5 (D664: a linked paper's lane, section and status -- the whole row -- unchanged),
W1, W2 and Z1 (structural: the mount adds nothing to the database -- no data step). GREEN / RED; exit 1 on any RED. --expect-red (the
control, on the live FROM files -- batteries.py at S571's 9a0054ac): exit 0 only if every check named in MUST_RED is RED (W1 and Z1
are structural: green on both). Counts are printed (never a live row's content). --save-pages DIR writes the owner's Batteries page
with First setup open, the manager's page and three New battery fitted forms (made-up rows) for the PC's browser walk at 1366 x 768."""
import datetime, importlib.util, json, os, re, shutil, sqlite3, sys, tempfile

ARGS = [a for a in sys.argv[1:]]
R, FAILED, NAMES = [], [], []
MUST_RED = ("W2", "I1", "I2", "I3", "I4", "I5")
TODAY = datetime.date(2031, 6, 15)
MODS = ("asset_register.py", "clinic_papers.py", "claude_reader.py", "claude_reread.py", "sorting_desk.py", "asset_machine.py",
        "scanner_widget.js", "stationery.py", "batteries.py")
S571_OBJS = {("table", "battery_place"), ("table", "battery_fit"), ("table", "battery_upkeep"), ("index", "battery_place_asset"),
             ("index", "battery_fit_place")}
REFUSE = "No paper %s that you may link here. Nothing was linked."


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
    print(("GREEN " if ok else "RED   ") + name + ((" -- " + str(d)[:1200]) if (d and not ok) else ""))
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


def shape(path):
    c = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
    try:
        objs = {(r[0], r[1]) for r in c.execute("SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        counts = {t: c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0] for k, t in objs if k == "table"}
        sets = {r[0]: r[1] for r in c.execute("SELECT key, value FROM settings")}
    finally:
        c.close()
    return objs, counts, sets


def main():
    D = os.path.abspath(ARGS[0])
    SRC = os.path.abspath(ARGS[1])
    shared_src = opt("--shared", os.environ.get("S575_SHARED_DIR", "/root/shared"))
    work = opt("--work") or tempfile.mkdtemp(prefix="s575walk_", dir="/tmp" if os.path.isdir("/tmp") else None)
    work = os.path.abspath(work)
    try:
        run(D, SRC, shared_src, work)
    finally:
        if "--keep" not in ARGS:
            shutil.rmtree(work, ignore_errors=True)


def run(D, SRC, shared_src, work):
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
        fh.write("sk-ant-walk-made-up-" + "0" * 12 + "\n")
    dbp = os.path.join(work, "assets.db")
    s = sqlite3.connect("file:%s?mode=ro" % SRC, uri=True); d = sqlite3.connect(dbp); s.backup(d); s.close(); d.close()
    shape0 = shape(dbp)
    env = setup_env(work)
    os.environ.update(env)
    for k in ("SARVAM_API_KEY", "ANTHROPIC_API_KEY"):
        os.environ.pop(k, None)

    # ------------------------------------------------------------------ W: the import, isolated
    appdir = os.path.join(work, "app")
    if appdir not in sys.path:
        sys.path.insert(0, appdir)
    try:
        m = import_file("asset_register", os.path.join(appdir, "asset_register.py"))
    except Exception as e:                                                 # noqa: BLE001
        ck("W1 the app imports with these files", lambda: False, lambda: repr(e)); return
    cp = sys.modules.get("clinic_papers")
    sd = sys.modules.get("sorting_desk")
    am = sys.modules.get("asset_machine")
    st = sys.modules.get("stationery")
    bt = sys.modules.get("batteries")
    shape1 = shape(dbp)
    ck("W1 the app imports; asset_register, clinic_papers, sorting_desk, asset_machine, stationery and batteries come from the scratch "
       "folder; the database is the copy",
       lambda: under(m.__file__, appdir) and under(cp.__file__, appdir) and sd is not None and under(sd.__file__, appdir)
       and am is not None and under(am.__file__, appdir) and st is not None and under(st.__file__, appdir)
       and bt is not None and under(bt.__file__, appdir) and bt.MOUNTED and m.DB_PATH == dbp)
    ck("W2 the S575 mark: batteries.SETUP = S575, mounted from the scratch folder; the S571 marks kept (batteries VERSION S571, "
       "sorting_desk BATTERY, asset_register BATTERY_S571) and the S568 / S566 / S563 / S560 / S559 / S557 / S555 / S551 marks kept",
       lambda: getattr(bt, "SETUP", None) == "S575" and bt.VERSION == "S571" and getattr(sd, "BATTERY", None) == "S571"
       and getattr(m, "BATTERY_S571", None) == "S571" and sd.STOCK == "S568" and sd.STOCK_FIX == "S568_FIX1" and m.STOCK_S568 == "S568"
       and st.MOUNTED and st.VERSION == "S568" and sd.LAST == "S566" and m.LAST_S566 == "S566" and sd.TIDY == "S563"
       and sd.RECEIPTS == "S560" and sd.ROAD == "S559" and sd.MACHINE == "S557" and sd.CORRECTIONS == "S555" and sd.VERSION == "S551.2")
    # Z1 (structural): no data step -- the mount adds nothing when S571's tables are there (on a database before S571 it adds S571's own)
    had571 = ("table", "battery_place") in shape0[0]
    new_objs = shape1[0] - shape0[0]
    differ = sorted(t for t, n in shape0[1].items() if shape1[1].get(t) != n and t != "settings")
    set_new = {k: v for k, v in shape1[2].items() if k not in shape0[2]}
    set_same = all(shape1[2].get(k) == v for k, v in shape0[2].items())
    print("Z1 counts: S571's tables there before %s; new objects %s; every old table's row count kept %s%s; settings added %s; every old "
          "setting kept %s" % (had571, sorted(n for _t, n in new_objs), not differ, (" (differ: %s)" % ", ".join(differ)) if differ else "",
                               sorted(set_new), set_same))
    ck("Z1 (structural) no data step: with S571's tables in place the mount adds no table, index, row or setting and changes none",
       lambda: not differ and set_same and not (shape0[0] - shape1[0])
       and ((not new_objs and not set_new) if had571 else (new_objs <= S571_OBJS and set(set_new) <= {"batteries.since"})))

    sd.TODAY = TODAY
    am.TODAY = TODAY
    st.TODAY = TODAY
    bt.TODAY = TODAY
    db = sqlite3.connect(dbp, timeout=20); db.row_factory = sqlite3.Row
    if m.CLAUDE is not None:
        m.CLAUDE.ensure(db); db.commit()
    for k in ("desk.on", "machine.on", "desk.floor", "stationery.issue_on", "batteries.on"):
        db.execute("DELETE FROM settings WHERE key=?", (k,))
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('read.claude','off')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.floor','2031-06-01')")
    db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES('desk.on','on')")
    for un, dn, role in (("walk_own_2031", "Walk Owner", "owner"), ("walk_mgr_2031", "Walk Manager", "manager")):
        if not db.execute("SELECT 1 FROM users WHERE username=?", (un,)).fetchone():
            db.execute("INSERT INTO users(username, display_name, role, password_hash, active) VALUES(?,?,?,'x',1)", (un, dn, role))
    db.commit()
    epoch = db.execute("SELECT value FROM settings WHERE key='auth_epoch'").fetchone()[0]
    own_u = db.execute("SELECT * FROM users WHERE username='walk_own_2031'").fetchone()
    mgr_u = db.execute("SELECT * FROM users WHERE username='walk_mgr_2031'").fetchone()

    def client(u):
        cl = m.app.test_client()
        with cl.session_transaction() as ss:
            ss["uid"] = u["id"]; ss["epoch"] = epoch
        return cl
    own, mgr = client(own_u), client(mgr_u)

    def html(cl, url):
        return cl.get(url).get_data(as_text=True)

    def row(bid):
        r_ = db.execute("SELECT * FROM bills WHERE id=?", (bid,)).fetchone()
        return dict(r_) if r_ else {}

    used = set()

    def free_stamp():
        """A B-nnnn stamp no paper of this copy has (from B-9999 down), never one used before in this walk."""
        for n in range(9999, 999, -1):
            s_ = "B-%04d" % n
            if s_ not in used and not db.execute("SELECT 1 FROM bills WHERE upper(stamp_no)=?", (s_,)).fetchone():
                used.add(s_)
                return s_
        raise RuntimeError("no free stamp")

    def mk(vendor, lane="clinic", status=None, created="2031-06-10 05:00:00", kind=None, **cols_):
        kd = kind or {"clinic": "Consumable", "owner_expense": "Expense", "lab_purchase": "Lab", "pharmacy": "Pharmacy"}[lane]
        st_ = status or ("draft" if lane == "clinic" else "captured")
        vals = dict(kind=kd, vendor=vendor, stamp_no=free_stamp(), status=st_, lane=lane, created_at=created,
                    submitted_at=created[:16], submitted_by="Walk", bill_date=created[:10])
        vals.update(cols_)
        bid = db.execute("INSERT INTO bills(%s) VALUES(%s)" % (",".join(vals), ",".join("?" * len(vals))), tuple(vals.values())).lastrowid
        db.commit()
        return bid, vals["stamp_no"]

    def digits(stamp):
        return stamp.split("-", 1)[1].lstrip("0")

    def post(cl, url, j):
        r_ = cl.post(url, json=j)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def form(cl, url, data):
        return cl.post(url, data=data)

    def flashes(cl):
        with cl.session_transaction() as ss:
            f_ = list(ss.get("_flashes") or [])
            ss.pop("_flashes", None)
        return " | ".join(x[1] for x in f_)

    def paper(cl, bid):
        r_ = cl.get("/desk/api/paper/%d" % bid)
        return r_.status_code, (r_.get_json(silent=True) or {})

    def setting(k, v):
        if v is None:
            db.execute("DELETE FROM settings WHERE key=?", (k,))
        else:
            db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
        db.commit()

    P = {}

    def add_place(name, grp, payer="clinic", owner_only=False):
        d_ = {"do": "add", "name": name, "grp": grp, "payer": payer, "sub": "Walk"}
        if owner_only:
            d_["owner_only"] = "1"                                          # a vehicle is yours only, as the seeded ones
        r_ = form(own, "/batteries/place", d_)
        x = db.execute("SELECT id FROM battery_place WHERE name=? ORDER BY id DESC LIMIT 1", (name,)).fetchone()
        P[name] = x[0] if x else None
        return r_.status_code

    def place(name):
        return dict(db.execute("SELECT * FROM battery_place WHERE id=?", (P[name],)).fetchone())

    def cur_fit(name):
        r_ = db.execute("SELECT * FROM battery_fit WHERE place_id=? AND voided_at='' AND removed_on IS NULL ORDER BY fitted_on DESC, id DESC LIMIT 1",
                        (P.get(name),)).fetchone()
        return dict(r_) if r_ else {}

    def n_fits(name):
        return db.execute("SELECT COUNT(*) FROM battery_fit WHERE place_id=?", (P.get(name),)).fetchone()[0]

    def view(name):
        db2 = sqlite3.connect(dbp); db2.row_factory = sqlite3.Row
        try:
            return bt.place_view(db2, bt.place(db2, P[name]), TODAY)
        except Exception as e:                                             # noqa: BLE001
            print("  (view %s failed: %s)" % (name, repr(e)[:160]))
            return {"badge": ("", ""), "await": "-", "rem": [], "till": None, "life": None}
        finally:
            db2.close()

    def fitr(cl, name, **f_):
        return form(cl, "/batteries/fit/%s" % P[name], f_)

    def tr_of(page, name):
        i_ = page.find('<tr data-place="%s">' % P[name])
        return page[i_:page.find("</tr>", i_)] if i_ >= 0 else ""

    def fold(page):
        i_ = page.find("id=s571first")
        return page[i_:page.find("</details>", i_)] if i_ >= 0 else ""

    def hist(page):
        i_ = page.find("id=s571hist")
        return page[i_:page.find("</table>", i_)] if i_ >= 0 else ""

    def awaited_total():
        try:
            return bt.overview(db, True, TODAY)[0]["awaited"]
        except Exception:                                                  # noqa: BLE001
            return None

    OA, OB, OC = "WALK575 Online UPS A", "WALK575 Online UPS B", "WALK575 Online UPS C"
    SU, JI, VC = "WALK575 Small UPS", "WALK575 Inverter", "WALK575 Old Car"
    F1, F2, F3 = "WALK575 First small UPS", "WALK575 First inverter", "WALK575 First online UPS"
    adds = [add_place(OA, "online_ups"), add_place(OB, "online_ups"), add_place(OC, "online_ups"), add_place(SU, "small_ups"),
            add_place(JI, "gen_inv"), add_place(VC, "vehicles", "owner", True), add_place(F1, "small_ups"), add_place(F2, "gen_inv"),
            add_place(F3, "online_ups")]
    print("places: %d made through '+ Add a battery place' (%s)" % (sum(1 for x in P.values() if x), "/".join(str(a_) for a_ in adds)))

    # made-up papers (stamps B-9nnn that no paper of the copy has)
    p_old1, s_old1 = mk("B.L. Computers WALK575 old one", created="2030-01-10 10:00:00", total_amount=14200.0)     # B.L., older than 90 days
    p_old2, s_old2 = mk("Other Supplier WALK575 two", created="2029-03-03 10:00:00", total_amount=6100.0)          # another supplier, old
    p_pers, s_pers = mk("Jasoria WALK575 personal", lane="owner_expense", subgroup="personal", created="2030-11-11 10:00:00")
    p_phar, s_phar = mk("B.L. Computers WALK575 pharmacy", lane="pharmacy", created="2030-05-05 10:00:00")
    p_asid, s_asid = mk("B.L. Computers WALK575 aside", status="rejected", created="2030-05-06 10:00:00")
    p_dup, s_dup = mk("B.L. Computers WALK575 second scan", created="2030-05-07 10:00:00", dup_of=p_old2)
    p_page, s_page = mk("B.L. Computers WALK575 a page", created="2030-05-08 10:00:00", page_of=p_old2)
    p_new, s_new = mk("B.L. Computers WALK575 new", created="2031-06-14 09:00:00", total_amount=9900.0)          # on the desk now
    p_f3, s_f3 = mk("B.L. Computers WALK575 first three", created="2030-02-02 10:00:00", total_amount=31000.0)
    s_none = free_stamp()                                                                                      # a stamp no paper has
    watched = (p_old1, p_old2, p_pers, p_f3)
    before = {b_: row(b_) for b_ in watched}

    # ================================================================== I1 (item 1): an old battery, with only a date
    flashes(own)
    fp_bl = html(own, "/batteries/fit/%s" % P[OA])
    fp_j = html(own, "/batteries/fit/%s" % P[JI])
    aw0 = awaited_total()
    a_oc = fitr(own, OC, fitted_on="01-06-2031", supplier="B.L. Computers", warranty_months="12", bill="awaited").status_code   # awaited: the desk's offer
    a_oa = fitr(own, OA, fitted_on="15-06-2024", supplier="B.L. Computers", warranty_months="12", brand="WalkOld", bill="none").status_code
    f_oa1 = cur_fit(OA)
    v_oa = view(OA)
    aw1 = awaited_total()
    h_oa = html(own, "/batteries/place/%s" % P[OA])
    a_ji = fitr(own, JI, fitted_on="01-03-2025", supplier="Jasoria", price="9000", old_amount="1000", bill="none", card="none").status_code
    f_ji1 = cur_fit(JI)
    h_ji = html(own, "/batteries/place/%s" % P[JI])
    n_vc0 = n_fits(VC)
    a_16 = fitr(own, VC, fitted_on="14-06-2015", bill="none").status_code
    fl_16 = flashes(own)
    n_vc1 = n_fits(VC)
    a_14 = fitr(own, VC, fitted_on="01-07-2016", bill="none").status_code
    fl_14 = flashes(own)
    n_vc2 = n_fits(VC)
    aud = []
    try:
        for r_ in db.execute("SELECT detail FROM desk_audit WHERE action='battery_fitted' ORDER BY id DESC LIMIT 50"):
            j_ = json.loads(r_[0] or "{}")
            if j_.get("fit") == f_oa1.get("id"):
                aud.append(j_)
    except Exception:                                                      # noqa: BLE001
        pass
    s_dn, j_dn = paper(own, p_new)
    offs = [o.get("text", "") for o in ((j_dn.get("bat") or {}).get("offers") or [])]
    rem_oa = {k_ for (k_, _w, _d, _dd, _s) in (v_oa.get("rem") or [])}
    print("I1 counts: forms -- B.L. 'Old battery — no bill' %s, card select %s; Jasoria 'no bill' %s, 'no card' %s; the 2024 UPS battery %s: "
          "bill_id %s, marker %s, await %s, badge '%s', till %s, life %s, reminders %s; B.L. bill awaited total %s -> %s (the awaited one "
          "of 01-06-2031 counted once); history 'no bill (old battery)' %s, 'Bill awaited' %s; audit no_bill %s; Jasoria no bill / no card: "
          "%s, marker card %s, history %s / %s; 16 years back %s (refused %s, fittings %s -> %s); 14 years 11 months %s (fittings -> %s); "
          "the desk's offers for a new B.L. paper %d -- to the awaited UPS %s, to the old battery %s"
          % ("Old battery — no bill" in fp_bl, "name=card" in fp_bl, "Old battery — no bill" in fp_j, "Old battery — no card" in fp_j, a_oa,
             f_oa1.get("bill_id"), f_oa1.get("bill_created_at") == "none:old-battery", v_oa.get("await"), (v_oa.get("badge") or ("",))[0],
             v_oa.get("till"), v_oa.get("life"), sorted(rem_oa), aw0, aw1, "no bill (old battery)" in hist(h_oa),
             "Bill awaited" in hist(h_oa), [x.get("no_bill") for x in aud], a_ji, f_ji1.get("card_created_at") == "none:old-battery",
             "no bill (old battery)" in hist(h_ji), "no card (old battery)" in hist(h_ji), a_16, "more than 15 years back" in fl_16,
             n_vc0, n_vc1, a_14, n_vc2, len(offs), any(OC in t for t in offs), any(OA in t for t in offs)))
    ck("I1 (item 1) an old battery with only a date: 'Fitted on' takes a past date (2024; 14 years 11 months back saves, 16 years back is "
       "refused); 'Old battery — no bill' on both forms and 'Old battery — no card' on the Jasoria form only (the B.L. form has no card "
       "select); stored as the id NULL and 'none:old-battery'; no 'bill awaited' badge, reminder or total; warranty till fitted + 12 "
       "months and usual life fitted + 30 months (passed: 'Due for replacement'); the history reads 'no bill (old battery)' / 'no card "
       "(old battery)'; the audit says no_bill; the desk offers a new B.L. paper to the awaited battery but not to the old one",
       lambda: "Old battery — no bill" in fp_bl and "name=card" not in fp_bl and "Old battery — no bill" in fp_j and "Old battery — no card" in fp_j
       and "Old battery — no card" not in fp_bl
       and a_oc == 302 and a_oa == 302 and f_oa1.get("fitted_on") == "2024-06-15" and f_oa1.get("bill_id") is None
       and f_oa1.get("bill_created_at") == "none:old-battery" and v_oa.get("await") is None and "bill" not in rem_oa and "warranty" not in rem_oa
       and "life" in rem_oa and v_oa["badge"][0] == "Due for replacement" and v_oa.get("till") == datetime.date(2025, 6, 15)
       and v_oa.get("life") == datetime.date(2026, 12, 15) and aw0 is not None and aw1 == aw0 + 1
       and "no bill (old battery)" in hist(h_oa) and "Bill awaited" not in hist(h_oa) and "WalkOld" in hist(h_oa)
       and aud and aud[0].get("no_bill") is True
       and a_ji == 302 and f_ji1.get("bill_created_at") == "none:old-battery" and f_ji1.get("card_created_at") == "none:old-battery"
       and f_ji1.get("card_id") is None and "no bill (old battery)" in hist(h_ji) and "no card (old battery)" in hist(h_ji)
       and a_16 == 302 and "more than 15 years back" in fl_16 and n_vc1 == n_vc0 and a_14 == 302 and "Saved" in fl_14 and n_vc2 == n_vc0 + 1
       and s_dn == 200 and any(("Battery fitted at %s on 01-06-2031" % OC) in t for t in offs) and not any(OA in t for t in offs),
       lambda: (a_oa, f_oa1, v_oa.get("await"), v_oa.get("badge"), v_oa.get("till"), v_oa.get("life"), sorted(rem_oa), aw0, aw1,
                hist(h_oa)[-600:], aud, a_ji, f_ji1, fl_16, fl_14, n_vc0, n_vc1, n_vc2, offs))

    # ================================================================== I2 (item 2): link existing papers, old ones too
    p_oa = place(OA)
    c_oa = quiet(lambda: [c["id"] for c in bt.candidates(db, p_oa, True, TODAY)], [])
    w_own = quiet(lambda: [c["id"] for c in bt.wide_candidates(db, True)], [])
    w_mgr = quiet(lambda: [c["id"] for c in bt.wide_candidates(db, False)], [])
    w_txt = quiet(lambda: [c["text"] for c in bt.wide_candidates(db, True) if c["id"] == p_old2], [])
    fp_su = html(own, "/batteries/fit/%s" % P[SU])
    a_su = fitr(own, SU, fitted_on="10-05-2031", supplier="B.L. Computers", warranty_months="12", bill="awaited", bill_any=str(p_old2)).status_code
    fl_su = flashes(own)
    f_su = cur_fit(SU)
    links_box = html(own, "/batteries/place/%s" % P[OA])
    l_oa = form(own, "/batteries/link", {"fit": str(f_oa1.get("id")), "paper": "", "paper_stamp": "B" + digits(s_old1), "as": "bill"}).status_code
    fl_oa = flashes(own)
    f_oa2 = cur_fit(OA)
    v_oa2 = view(OA)
    h_oa2 = html(own, "/batteries/place/%s" % P[OA])
    f_oc = cur_fit(OC)
    setting("batteries.on", "on")
    l_m1 = form(mgr, "/batteries/link", {"fit": str(f_oc.get("id")), "paper": "", "paper_stamp": "b-0" + digits(s_pers), "as": "card"}).status_code
    fl_m1 = flashes(mgr)
    l_m2 = form(mgr, "/batteries/link", {"fit": str(f_oc.get("id")), "paper": "", "paper_stamp": "B" + digits(s_none), "as": "card"}).status_code
    fl_m2 = flashes(mgr)
    j_m3s, j_m3 = post(mgr, "/batteries/link", {"fit": f_oc.get("id"), "paper_stamp": s_pers, "as": "card"})
    links_mgr = html(mgr, "/batteries/place/%s" % P[OC])
    setting("batteries.on", None)
    ref_own = {}
    for nm_, s_ in (("pharmacy", s_phar), ("set aside", s_asid), ("second scan", s_dup), ("a page", s_page), ("not found", s_none)):
        rr_ = form(own, "/batteries/link", {"fit": str(f_oc.get("id")), "paper": "", "paper_stamp": s_, "as": "card"}).status_code
        ref_own[nm_] = (rr_, flashes(own) == REFUSE % s_)
    l_ji = form(own, "/batteries/link", {"fit": str(f_ji1.get("id")), "paper": "", "paper_stamp": "b" + digits(s_pers), "as": "card"}).status_code
    fl_ji = flashes(own)
    f_ji2 = cur_fit(JI)
    cf1 = form(own, "/batteries/link", {"fit": str(f_oc.get("id")), "paper": "", "paper_stamp": s_new, "paper_any": str(p_f3), "as": "bill"}).status_code
    fl_cf1 = flashes(own)
    n_vc3 = n_fits(VC)
    cf2 = fitr(own, VC, fitted_on="01-01-2031", bill_stamp=s_new, bill_any=str(p_f3)).status_code
    fl_cf2 = flashes(own)
    n_vc4 = n_fits(VC)
    f_oc2 = cur_fit(OC)
    print("I2 counts: the usual picker of a B.L. place has the old B.L. paper %s (unchanged: 90 days); 'Show older / other papers' -- owner %d "
          "papers (old B.L. %s, other supplier %s, Personal %s, pharmacy %s, set aside %s, second scan %s, a page %s), manager %d (Personal %s); "
          "its line '%s'; the fitted form has the fold %s, bill_any %s, bill_stamp %s; picked from it %s -> the bill %s; the links box has "
          "the fold %s; linked later by stamp typed 'B%s' %s ('%s'): bill %s, marker gone %s, awaited %s, history shows the stamp %s; manager "
          "by stamp: Personal %s '%s', not found %s '%s' -- the same line %s; JSON %s; the manager's links box lists Personal %s; the owner's "
          "refusals by stamp %s; the owner links the Personal paper as the card by 'b%s' %s -> card %s, marker gone %s; two pickers: link %s "
          "'%s', fitted form %s '%s' (fittings %s -> %s); the awaited UPS still awaited %s"
          % (p_old1 in c_oa, len(w_own), p_old1 in w_own, p_old2 in w_own, p_pers in w_own, p_phar in w_own, p_asid in w_own, p_dup in w_own,
             p_page in w_own, len(w_mgr), p_pers in w_mgr, (w_txt or [""])[0].replace(s_old2, "B-n"), "Show older / other papers" in fp_su,
             "name=bill_any" in fp_su, "name=bill_stamp" in fp_su, a_su, f_su.get("bill_id") == p_old2, "name=paper_stamp" in links_box,
             digits(s_old1), l_oa, fl_oa.replace(s_old1, "B-n"), f_oa2.get("bill_id") == p_old1, f_oa2.get("bill_created_at") != "none:old-battery",
             v_oa2.get("await"), s_old1 in hist(h_oa2), l_m1, fl_m1.replace(s_pers, "B-n"), l_m2, fl_m2.replace(s_none, "B-n"),
             fl_m1 == REFUSE % s_pers and fl_m2 == REFUSE % s_none, (j_m3s, (j_m3.get("error") or "").replace(s_pers, "B-n")),
             s_pers in links_mgr, ref_own, digits(s_pers), l_ji, f_ji2.get("card_id") == p_pers, f_ji2.get("card_created_at") != "none:old-battery",
             cf1, fl_cf1, cf2, fl_cf2, n_vc3, n_vc4, f_oc2.get("bill_id") is None))
    ck("I2 (item 2) link existing papers, old ones too: the usual picker unchanged (the supplier's last 90 days); 'Show older / other "
       "papers' lists every paper the person may see -- any supplier, any date, newest first, 'stamp · supplier · date · amount', never "
       "pharmacy, set aside, a second scan or a page, Personal to the owner only -- on the fitted form (bill_any) and in the battery's "
       "papers box (paper_any); 'Find by stamp' takes B-0162 / B162 / b-162; an old battery's bill linked later by stamp clears 'no bill'; "
       "a manager typing a Personal paper's stamp gets the same one line as a stamp nobody has (never that it exists); two pickers with "
       "different papers are refused",
       lambda: p_old1 not in c_oa and p_old1 in w_own and p_old2 in w_own and p_pers in w_own and p_new in w_own
       and not any(x in w_own for x in (p_phar, p_asid, p_dup, p_page)) and p_pers not in w_mgr and p_old1 in w_mgr
       and w_own.index(p_new) < w_own.index(p_old1) < w_own.index(p_old2)
       and w_txt and w_txt[0] == "%s · Other Supplier WALK575 two · 03-03-2029 · ₹6,100" % s_old2
       and "Show older / other papers" in fp_su and "name=bill_any" in fp_su and "name=bill_stamp" in fp_su and s_old2 in fp_su
       and a_su == 302 and "Saved" in fl_su and f_su.get("bill_id") == p_old2
       and "Show older / other papers" in links_box and "name=paper_any" in links_box and "name=paper_stamp" in links_box and s_old1 in links_box
       and l_oa == 302 and fl_oa.startswith("Linked: %s is the bill" % s_old1) and f_oa2.get("bill_id") == p_old1
       and f_oa2.get("bill_created_at") == before[p_old1]["created_at"] and v_oa2.get("await") is None and s_old1 in hist(h_oa2)
       and "no bill (old battery)" not in hist(h_oa2)
       and l_m1 == 302 and fl_m1 == REFUSE % s_pers and l_m2 == 302 and fl_m2 == REFUSE % s_none
       and j_m3s == 400 and j_m3.get("error") == REFUSE % s_pers and s_pers not in links_mgr
       and all(v_ == (302, True) for v_ in ref_own.values())
       and l_ji == 302 and fl_ji.startswith("Linked: %s is the warranty card" % s_pers) and f_ji2.get("card_id") == p_pers
       and f_ji2.get("bill_created_at") == "none:old-battery"
       and cf1 == 302 and fl_cf1 == "Pick the paper in one place only. Nothing was linked."
       and cf2 == 302 and fl_cf2 == "Pick the bill in one place only. Nothing was saved." and n_vc4 == n_vc3 and f_oc2.get("bill_id") is None,
       lambda: (c_oa, len(w_own), w_txt, a_su, fl_su, f_su.get("bill_id"), l_oa, fl_oa, f_oa2, v_oa2.get("await"), l_m1, fl_m1, l_m2, fl_m2,
                j_m3s, j_m3, ref_own, l_ji, fl_ji, f_ji2, cf1, fl_cf1, cf2, fl_cf2))

    # ================================================================== I5 (D664): a linked paper's lane, section and status unchanged
    after_ = {b_: row(b_) for b_ in watched}
    linked_ = (f_oa2.get("bill_id") == p_old1 and f_su.get("bill_id") == p_old2 and f_ji2.get("card_id") == p_pers)
    print("I5 counts: linked -- by stamp (old B.L.) %s, from the wider list (other supplier) %s, the Personal card by stamp %s; lane / section "
          "/ status: %s; whole rows unchanged %s"
          % (f_oa2.get("bill_id") == p_old1, f_su.get("bill_id") == p_old2, f_ji2.get("card_id") == p_pers,
             "; ".join("%s -> %s" % ((before[b_].get("lane"), before[b_].get("subgroup"), before[b_].get("status")),
                                     (after_[b_].get("lane"), after_[b_].get("subgroup"), after_[b_].get("status"))) for b_ in watched[:3]),
             all(before[b_] == after_[b_] for b_ in watched)))
    ck("I5 (D664) linking never changes the paper: the papers linked by stamp, from 'Show older / other papers' and as a card keep their lane, "
       "section and status -- the whole row unchanged",
       lambda: linked_ and all(before[b_] == after_[b_] for b_ in watched) and before[p_pers]["subgroup"] == "personal",
       lambda: (linked_, [(before[b_].get("lane"), after_[b_].get("lane"), before[b_].get("status"), after_[b_].get("status")) for b_ in watched]))

    # ================================================================== I3 (item 3): batteries in each online UPS
    pg3 = html(own, "/batteries")
    tr_ob, tr_su, tr_oa = tr_of(pg3, OB), tr_of(pg3, SU), tr_of(pg3, OA)
    ask_href = "/batteries/place/%s?edit=1#s571edit" % P[OB]
    setting("batteries.on", "on")
    pg3m = html(mgr, "/batteries")
    setting("batteries.on", None)
    e0 = html(own, "/batteries/place/%s" % P[OB])
    e1 = html(own, "/batteries/place/%s?edit=1" % P[OB])
    pob = place(OB)
    ed = form(own, "/batteries/place", {"do": "edit", "id": str(P[OB]), "name": pob["name"], "sub": pob["sub"], "payer": pob["payer"],
                                         "supplier": pob["supplier"], "warranty_months": str(pob["warranty_months"] or ""),
                                         "life_months": str(pob["life_months"] or ""), "btype": pob["btype"], "ah": pob["ah"],
                                         "volts": pob["volts"], "set_n": "4"}).status_code
    pob2 = place(OB)
    pg3b = html(own, "/batteries")
    tr_ob2 = tr_of(pg3b, OB)
    fo_ob = html(own, "/batteries/fit/%s" % P[OB])
    fo_su = fp_su
    i_set, i_date = fo_ob.find("name=set_n"), fo_ob.find("name=fitted_on")
    j_set, j_date = fo_su.find("name=set_n"), fo_su.find("name=fitted_on")
    print("I3 counts: the owner's list -- '%s' row asks %s (href %s), small UPS asks %s, the recorded online UPS with no count asks %s; the "
          "manager's list asks %s; the place page edit form open with ?edit=1 %s, without %s; set 4 %s -> set_n %s; the row then '%s' "
          "(asks %s); New battery fitted -- online UPS: 'Batteries in the set' before 'Fitted on' %s (%d < %d), small UPS %s"
          % (OB, "How many batteries? — set" in tr_ob, ask_href.replace(str(P[OB]), "<id>") in tr_ob.replace(str(P[OB]), "<id>"),
             "How many batteries?" in tr_su, "How many batteries?" in tr_oa, "How many batteries?" in pg3m,
             "<details class=card id=s571edit open>" in e1, "<details class=card id=s571edit open>" in e0, ed, pob2.get("set_n"),
             re.sub(r"<[^>]+>", " ", tr_ob2.split("</td>")[1] if "</td>" in tr_ob2 else "").strip(), "How many batteries?" in tr_ob2,
             0 <= i_set < i_date, i_set, i_date, 0 <= j_date < j_set))
    ck("I3 (item 3) batteries in each online UPS: an online UPS with no count shows the owner 'How many batteries? — set', linking to the "
       "place's 'Change this place' (opened by ?edit=1); a small UPS and the manager never see it; after setting 4 the row reads 'set of 4' "
       "(before any battery is recorded) and asks no more; on New battery fitted an online UPS has 'Batteries in the set' first",
       lambda: "How many batteries? — set" in tr_ob and ('href="%s"' % ask_href) in tr_ob and "How many batteries?" not in tr_su
       and "How many batteries?" in tr_oa and "How many batteries?" not in pg3m and "WALK575 Online UPS B" in pg3m
       and "<details class=card id=s571edit open>" in e1 and "<details class=card id=s571edit open>" not in e0 and "id=s571edit" in e0
       and ed == 302 and pob2.get("set_n") == 4 and pob2.get("warranty_months") == pob.get("warranty_months") and "set of 4" in tr_ob2
       and "How many batteries?" not in tr_ob2 and 0 <= i_set < i_date and 0 <= j_date < j_set,
       lambda: (tr_ob[:700], tr_su[:200], ed, pob2, tr_ob2[:500], i_set, i_date, j_set, j_date))

    # ================================================================== I4 (item 4): First setup in one sitting
    pg4 = html(own, "/batteries")
    fd = fold(pg4)
    v_f1 = view(F1)
    lines_ = {n_: ('data-place="%s"' % P[n_]) in fd for n_ in (F1, F2, F3, OA, SU)}
    i_f1 = fd.find('data-place="%s"' % P[F1])
    f1_line = fd[i_f1:fd.find("</form>", i_f1)] if i_f1 >= 0 else ""
    setting("batteries.on", "on")
    pg4m = html(mgr, "/batteries")
    setting("batteries.on", None)
    hid = {"back": "first", "supplier": "B.L. Computers", "warranty_months": "12"}
    e_r = fitr(own, F1, fitted_on="", bill="none", **hid)
    fl_e = flashes(own)
    n_f1e = n_fits(F1)
    r1_ = fitr(own, F1, fitted_on="01-03-2023", bill="none", **hid)
    fl1 = flashes(own)
    r2_ = fitr(own, F2, fitted_on="15-08-2022", bill="none", back="first", supplier="Jasoria", warranty_months="")
    fl2 = flashes(own)
    r3_ = fitr(own, F3, fitted_on="20-02-2030", set_n="6", bill="none", bill_stamp="b" + digits(s_f3), **hid)
    fl3 = flashes(own)
    locs = [x.headers.get("Location", "") for x in (e_r, r1_, r2_, r3_)]
    pg4b = html(own, "/batteries?first=1")
    fd2 = fold(pg4b)
    gf1, gf2, gf3 = cur_fit(F1), cur_fit(F2), cur_fit(F3)
    v_f1b = view(F1)
    r4_ = fitr(own, F1, fitted_on="01-06-2031", supplier="B.L. Computers", warranty_months="12", bill="awaited")   # the full form, a battery before it
    fl4 = flashes(own)
    print("I4 flash: a first battery says 'The one before' %s; a second one %s" % ("The one before" in fl1, "The one before is in the history." in fl4))
    print("I4 counts: the owner's fold %s, its lines -- %s; the first small UPS's badge '%s' (listed by current_fit, not the badge); its line "
          "carries back=first %s, supplier %s, warranty 12 %s, the date required %s; the manager's page has the fold %s; an empty date %s -> "
          "'%s', fittings %s; three in a row %s / %s / %s ('%s' | '%s' | '%s'); each back to the fold %s; the fold then open %s, the three "
          "gone %s; saved -- small UPS warranty %s (till %s), inverter %s, online UPS set %s bill by stamp %s"
          % ("id=s571first" in pg4, lines_, v_f1["badge"][0], 'name=back value=first' in f1_line, 'name=supplier value="B.L. Computers"' in f1_line,
             'name=warranty_months value="12"' in f1_line, "name=fitted_on required" in f1_line, "id=s571first" in pg4m, e_r.status_code, fl_e,
             n_f1e, r1_.status_code, r2_.status_code, r3_.status_code, fl1, fl2, fl3.replace(s_f3, "B-n"),
             all(x.endswith("/batteries?first=1#s571first") for x in locs), "<details class=card id=s571first open>" in pg4b,
             not any(('data-place="%s"' % P[n_]) in fd2 for n_ in (F1, F2, F3)), gf1.get("warranty_months"), v_f1b.get("till"),
             gf2.get("fitted_on"), gf3.get("set_n"), gf3.get("bill_id") == p_f3))
    ck("I4 (item 4) First setup: an owner-only fold on the Batteries page lists every place with no battery recorded (decided by "
       "current_fit -- a UPS showing 'Backup check due' is listed), one line each: the date (required), the set for an online UPS, the bill "
       "(Old battery — no bill / pick / find by stamp), Save, carrying the place's supplier and warranty; an empty date is refused; three "
       "places saved in a row, each back at the open fold with its flash; the places then leave the list; the manager has no fold; the saved "
       "line speaks of 'the one before' only when there was one",
       lambda: "id=s571first" in pg4 and "First setup" in fd and lines_[F1] and lines_[F2] and lines_[F3] and not lines_[OA] and not lines_[SU]
       and v_f1["badge"][0] == "Backup check due"
       and "name=back value=first" in f1_line and 'name=supplier value="B.L. Computers"' in f1_line and 'name=warranty_months value="12"' in f1_line
       and "name=fitted_on required" in f1_line and "Old battery — no bill" in f1_line and "name=bill_stamp" in f1_line
       and ('data-place="%s"' % P[F2]) in fd and "name=set_n" not in f1_line and "id=s571first" not in pg4m
       and e_r.status_code == 302 and "Type the date" in fl_e and fl_e.startswith(F1) and n_f1e == 0
       and r1_.status_code == r2_.status_code == r3_.status_code == 302 and all(x.startswith("Saved") for x in (fl1, fl2, fl3))
       and all(x.endswith("/batteries?first=1#s571first") for x in locs) and "<details class=card id=s571first open>" in pg4b
       and not any(('data-place="%s"' % P[n_]) in fd2 for n_ in (F1, F2, F3))
       and gf1.get("fitted_on") == "2023-03-01" and gf1.get("warranty_months") == 12 and gf1.get("bill_created_at") == "none:old-battery"
       and v_f1b.get("till") == datetime.date(2024, 3, 1) and gf2.get("fitted_on") == "2022-08-15" and gf2.get("warranty_months") is None
       and gf3.get("set_n") == 6 and gf3.get("bill_id") == p_f3
       and "The one before" not in fl1 and r4_.status_code == 302 and "The one before is in the history." in fl4,
       lambda: (lines_, v_f1.get("badge"), f1_line[:900], e_r.status_code, fl_e, n_f1e, r1_.status_code, r2_.status_code, r3_.status_code,
                fl1, fl2, fl3, locs, gf1, gf2, gf3))

    # ------------------------------------------------------------------ pages for the PC's browser walk (made-up rows)
    sp = opt("--save-pages")
    if sp:
        os.makedirs(sp, exist_ok=True)
        for nm, url in (("s575_owner_first.html", "/batteries?first=1"), ("s575_fit_online.html", "/batteries/fit/%s" % P[OB]),
                        ("s575_fit_small.html", "/batteries/fit/%s" % P[SU]), ("s575_fit_jasoria.html", "/batteries/fit/%s" % P[JI]),
                        ("s575_place_links.html", "/batteries/place/%s" % P[OC]),
                        ("batteries_owner.html", "/batteries"), ("batteries_place.html", "/batteries/place/%s" % P[JI]),
                        ("batteries_fit_bl.html", "/batteries/fit/%s" % P[OC]), ("batteries_fit_jasoria.html", "/batteries/fit/%s" % P[JI])):
            with open(os.path.join(sp, nm), "w", encoding="utf-8") as fh:
                fh.write(html(own, url))
        setting("batteries.on", "on")
        with open(os.path.join(sp, "batteries_manager.html"), "w", encoding="utf-8") as fh:
            fh.write(html(mgr, "/batteries"))
        setting("batteries.on", None)
        print("pages saved: 10")
    db.close()


if __name__ == "__main__":
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
        print("CONTROL structural (green on both, named): %s" % ", ".join("%s %s" % (k, "GREEN" if seen_.get(k) else "RED") for k in ("W1", "Z1")))
        sys.exit(0 if (reds and not not_red) else 1)
    sys.exit(1 if reds or not R else 0)
