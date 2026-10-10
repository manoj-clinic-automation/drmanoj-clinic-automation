#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s502.py -- kit S502_STOCK_MILAAN_TODAY: the walk (the brief's section 4), on the server, on scratch copies only.

    python3 -B walk_s502.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            --duty-map DUTY_MAP.json(v9)

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the three built files, OLD is the box as it is.
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  db / adb / spine    backup-API copies; every probe works on its OWN further copy (rule 3); the walk's rows carry W502 in their item or
                      note and are found by key, never by counting.

Sections 1-4 and 7 run by function and by route (header auth) in one process per side ("fn"); section 5 signs in through the portal as
darpan and manoj ("eye") and, on the NEW side, writes the darpan /api/state JSON of the fixed copy for the PC's rendered check (section 6,
render_stub_s502.py). Every control is the same probe on the OLD files and must go red there. ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR
and REPORTS_NTFY_STUB are set for every python: nothing reaches a phone. Nothing is imported from inside deploy_kits (rule 11): the data
fixes run from a copy of fix_s502.py placed beside the walk's work folder. No person, phone or account number is in this file.
"""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import shutil
import sqlite3
import subprocess
import sys

TAG = "W502JSON "
MAP9_MD5 = "2016244829b4c70c00f1c59b0250ee35"
HROLE = {"darpan": "staff", "manoj": "doctor", "w502other": "staff"}
USERS = {"darpan": "staff", "manoj": "doctor"}
N, FAILS, NOTES = [0], [], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def ins(con, table, row):
    row = dict(row)
    for _cid, name, typ, notnull, dflt, pk in con.execute("PRAGMA table_info(%s)" % table).fetchall():
        if notnull and dflt is None and not pk and name not in row:
            row[name] = 0 if "INT" in (typ or "").upper() else ""
    cols = list(row)
    cur = con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))), [row[c] for c in cols])
    return cur.lastrowid


def digest(con):
    """The rows the data fixes touch, as one hash -- a second run must leave it unchanged."""
    rows = []
    for q in ("SELECT id, qty_units, status, expected_units, gap_units, note, roster_id FROM stock_point WHERE item='TRUECEPROL OD' ORDER BY id",
              "SELECT id, qty_units, point_id FROM stock_spot_roster WHERE day='2026-10-10' AND item='TRUECEPROL OD'",
              "SELECT id, count_id, note FROM stock_shelf_fix WHERE item='TRUECEPROL OD' AND source='recount'",
              "SELECT id, void_why, void_at IS NOT NULL FROM stock_watch_loss_line WHERE item='TYRO BR'",
              "SELECT id, status, seen_by FROM stock_trace WHERE item='TYRO BR'",
              "SELECT item, by, done_at FROM stock_watch_ask WHERE item='TYRO BR' ORDER BY id"):
        try:
            rows.append([list(r) for r in con.execute(q).fetchall()])
        except sqlite3.Error as e:
            rows.append(str(e))
    return md5b(json.dumps(rows, default=str).encode()), rows


def run_fix(fixpy, db, fin, spine):
    env = dict(os.environ)
    p = subprocess.run([sys.executable, "-B", fixpy, "--db", db, "--finance", fin, "--spine", spine], env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=600)
    js = [l for l in p.stdout.splitlines() if l.startswith("FIX_S502_JSON ")]
    return (json.loads(js[-1][len("FIX_S502_JSON "):]) if js else None), p.returncode, p.stdout[-1500:]


# ============================================================================================================== the "fn" probe
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W502_DB0"))
    NEW = SIDE == "new"
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE)
    import finance_app as fa                                            # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import stockmatch as SM                                             # noqa: E402
    import loss_piles as LP                                             # noqa: E402
    for m in (SW, SM, LP):
        assert m.__file__.startswith(FIN), m.__file__
    cl = fa.app.test_client()
    today = dt.date.today()
    T = today.isoformat()
    Y = (today - dt.timedelta(days=1)).isoformat()
    A = os.environ["FINANCE_DB"]
    ca = sqlite3.connect(A, timeout=60)
    ca.row_factory = sqlite3.Row
    SW.ensure(ca)
    ca.commit()
    out["cols"] = [r[1] for r in ca.execute("PRAGMA table_info(stock_watch_loss_line)").fetchall()]

    def H(u):
        return {"X-Clinic-User": u, "X-Clinic-Role": HROLE[u], "Content-Type": "application/json"}

    def post(path, body, who):
        r = cl.post(path, data=json.dumps(body), headers=H(who))
        return r.status_code, (r.get_json(silent=True) or {})

    def point(item, qty, by, at, expected=50.0, status="settled", roster_id=None):
        return ins(ca, "stock_point", dict(item_norm=SW.norm_name(item), item=item, at=at, qty_units=float(qty), source="spot", by=by, expected_units=expected,
                                            gap_units=(float(qty) - expected), status=status, settled_at=at, note="W502 walk", roster_id=roster_id, provisional_units=0))

    def roster(item, day, qty, pid, at):
        return ins(ca, "stock_spot_roster", dict(day=day, item_norm=SW.norm_name(item), item=item, reason="W502", reason_hi="W502", rank=95, asked_at=day + "T06:30:00",
                                                  answered_at=at, qty_units=float(qty), point_id=pid, pack=1, packing="", carried=0))

    def trace(item, pid, status="open"):
        return ins(ca, "stock_trace", dict(item_norm=SW.norm_name(item), item=item, opened_at=T + "T10:00:05", trigger="point", anchor_at=T + "T09:00:00", window_from=T,
                                            window_to=T, gap_units=-10.0, verdict="unexplained", findings_json=json.dumps({"point_id": pid, "findings": [], "anchor": "W502"}),
                                            fix_json="{}", status=status, count_id=None, pack=1, packing=""))

    def pt(pid):
        r = ca.execute("SELECT id, qty_units, status, note, expected_units, gap_units, source, roster_id, by FROM stock_point WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    # ---------------------------------------------------------------- 1  the correction
    s1 = {}
    I1 = "W502 FIX ITEM"
    p1 = point(I1, 50, "darpan", T + "T10:00:00")
    r1 = roster(I1, T, 50, p1, T + "T10:00:00")
    t1 = trace(I1, p1)
    t_other = trace("W502 OTHER ITEM", 9502999)
    ca.commit()
    s1["code"], s1["json"] = post("/finance/stockmatch/api/spot/fix", dict(roster_id=r1, pcs=40), "darpan")
    s1["json"] = {k: s1["json"].get(k) for k in ("ok", "error", "message", "saved")}
    s1["old"] = pt(p1)
    rr = ca.execute("SELECT qty_units, point_id FROM stock_spot_roster WHERE id=?", (r1,)).fetchone()
    s1["roster"] = list(rr) if rr else None
    s1["new"] = pt(rr[1]) if rr and rr[1] != p1 else None
    s1["trace_old"] = list(ca.execute("SELECT status, seen_by FROM stock_trace WHERE id=?", (t1,)).fetchone())
    s1["trace_other"] = list(ca.execute("SELECT status, seen_by FROM stock_trace WHERE id=?", (t_other,)).fetchone())
    s1["new_trace_open"] = [list(x) for x in ca.execute("SELECT id, status FROM stock_trace WHERE item=? AND json_extract(findings_json,'$.point_id')=?", (I1, (rr[1] if rr else -1)))]
    vcol = "void_at" if "void_at" in out["cols"] else "NULL"                 # OLD has no void column
    s1["new_loss_line"] = [list(x) for x in ca.execute("SELECT id, point_id, gap_units, %s FROM stock_watch_loss_line WHERE item=?" % vcol, (I1,))]
    s1["audit"] = [list(x) for x in ca.execute("SELECT action, by_whom FROM audit_log WHERE table_name='stock_watch' AND action='spot_fix' AND after_json LIKE '%W502 FIX ITEM%'")]
    s1["same_qty"] = post("/finance/stockmatch/api/spot/fix", dict(roster_id=r1, pcs=40), "darpan")
    s1["same_qty"] = [s1["same_qty"][0], (s1["same_qty"][1].get("saved") or {}).get("message"), s1["same_qty"][1].get("message")]
    out["s1"] = s1

    # ---------------------------------------------------------------- 2  not yesterday / not someone else / the owner
    s2 = {}
    p2 = point("W502 YDAY ITEM", 50, "darpan", Y + "T10:00:00")
    r2 = roster("W502 YDAY ITEM", Y, 50, p2, Y + "T10:00:00")
    p3 = point("W502 OTHERS ITEM", 50, "w502other", T + "T10:05:00")
    r3 = roster("W502 OTHERS ITEM", T, 50, p3, T + "T10:05:00")
    ca.commit()
    c, j = post("/finance/stockmatch/api/spot/fix", dict(roster_id=r2, pcs=45), "darpan")
    s2["yday"] = [c, j.get("ok"), j.get("message")]
    c, j = post("/finance/stockmatch/api/spot/fix", dict(roster_id=r3, pcs=45), "darpan")
    s2["other"] = [c, j.get("ok"), j.get("message")]
    c, j = post("/finance/stockmatch/api/spot/fix", dict(roster_id=r3, pcs=45), "manoj")
    s2["owner"] = [c, j.get("ok"), (j.get("saved") or {}).get("message")]
    s2["owner_old"] = (pt(p3) or {}).get("status")
    c, j = post("/finance/stockmatch/api/spot/fix", dict(roster_id=9502998, pcs=45), "darpan")
    s2["nosuch"] = [c, j.get("ok")]
    out["s2"] = s2

    # ---------------------------------------------------------------- 3  superseded is skipped
    s3 = {}
    I3 = "W502 LP ITEM"
    pa = point(I3, 5, "darpan", T + "T11:00:00")
    pb = point(I3, 9, "darpan", T + "T12:00:00", status="superseded")
    ca.commit()
    lp = SW.last_point(ca, SW.norm_name(I3))
    s3["last_point"] = dict(id=lp["id"], qty=lp["qty"], picked="11:00" if lp["id"] == pa else ("12:00" if lp["id"] == pb else "?")) if lp else None
    sp = SW.Spine()
    real = None
    for it in sp.items():
        if sp.mrp_p(it["name"]):
            real = it["name"]
            break
    s3["real_item"] = real
    ym = today.strftime("%Y-%m")
    if real:
        before = SW.month_leak(ca, ym)
        ins(ca, "stock_point", dict(item_norm=SW.norm_name(real), item=real, at=T + "T12:30:00", qty_units=0.0, source="spot", by="darpan", expected_units=30.0, gap_units=-30.0,
                                    status="superseded", settled_at=T + "T12:30:00", note="W502 walk: superseded", provisional_units=0))
        ca.commit()
        after = SW.month_leak(ca, ym)
        s3["leak_before"] = (before or {}).get("loss_p")
        s3["leak_after"] = (after or {}).get("loss_p")
        s3["leak_points_before"] = (before or {}).get("points_p")
        s3["leak_points_after"] = (after or {}).get("points_p")
    out["s3"] = s3

    # ---------------------------------------------------------------- 4  the recount door is closed to staff
    s4 = {}
    items = LP.round_items(ca, 1)
    first = sorted(items)[0] if items else None
    s4["item"] = first
    if first:
        s4["darpan"] = post("/finance/stockmatch/api/recount", dict(item=first, pcs=5), "darpan")
        s4["darpan"] = [s4["darpan"][0], s4["darpan"][1].get("error"), s4["darpan"][1].get("message")]
        s4["owner"] = post("/finance/stockmatch/api/recount", dict(item=first, pcs=5), "manoj")[0]
    out["s4"] = s4

    # ---------------------------------------------------------------- 7  the data fixes, twice, on their own copy (NEW only -- the fixer needs the NEW file)
    s7 = {}
    if NEW:
        p7 = os.path.join(WORK, "w502_fix.db")
        copydb(DB0, p7)
        fixpy = os.environ["W502_FIXPY"]
        j1, rc1, tail1 = run_fix(fixpy, p7, FIN, os.environ["SPINE_DB"])
        c7 = sqlite3.connect(p7, timeout=60)
        c7.row_factory = sqlite3.Row
        d1, rows1 = digest(c7)
        s7["run1"] = dict(rc=rc1, json=j1, tail=(tail1 if j1 is None else ""))
        s7["cols"] = [r[1] for r in c7.execute("PRAGMA table_info(stock_watch_loss_line)").fetchall()]
        s7["roster"] = list(c7.execute("SELECT id, qty_units, point_id, answered_at FROM stock_spot_roster WHERE day='2026-10-10' AND item='TRUECEPROL OD'").fetchone() or [])
        s7["points"] = [list(r) for r in c7.execute("SELECT id, qty_units, status, expected_units, gap_units, source, by, substr(at,1,16), roster_id FROM stock_point WHERE item='TRUECEPROL OD' ORDER BY id")]
        np_ = c7.execute("SELECT id, qty_units, gap_units FROM stock_point WHERE item='TRUECEPROL OD' AND status<>'superseded' ORDER BY at DESC, id DESC LIMIT 1").fetchone()
        s7["newest"] = list(np_) if np_ else None
        s7["shelf_fix"] = [list(r) for r in c7.execute("SELECT id, count_id, qty, substr(note, -60) FROM stock_shelf_fix WHERE item='TRUECEPROL OD' AND source='recount'")]
        cl7 = c7.execute("SELECT bucket, pile, grp, line_json FROM stock_pile_cache WHERE count_id=1 AND item='TRUECEPROL OD'").fetchone()
        s7["cache_line"] = dict(bucket=cl7[0], pile=cl7[1], grp=cl7[2], counted=json.loads(cl7[3]).get("counted"), diff=json.loads(cl7[3]).get("diff")) if cl7 else None
        s7["recounts_by"] = [x["item"] for x in LP.recounts_by(c7, 1)]
        s7["tyro_line"] = [list(r) for r in c7.execute("SELECT id, gap_units, void_why, void_at IS NOT NULL FROM stock_watch_loss_line WHERE item='TYRO BR'")]
        s7["tyro_trace"] = [list(r) for r in c7.execute("SELECT id, status, seen_by FROM stock_trace WHERE item='TYRO BR' AND opened_at LIKE '2026-10-08T11:50%'")]
        s7["tyro_ask"] = [list(r) for r in c7.execute("SELECT item, by, done_at FROM stock_watch_ask WHERE item='TYRO BR'")]
        dv = SW.darpan_view(c7)
        s7["darpan_losses"] = [l["text_hi"] for l in (dv.get("losses") or [])] if dv.get("ok") else "RAISED %s" % dv.get("note")
        s7["darpan_roster_truece"] = [dict(qty=x.get("qty"), qty_hi=x.get("qty_hi"), can_fix=x.get("can_fix"), by=x.get("by")) for x in (dv.get("roster") or {}).get("items", []) if x["item"] == "TRUECEPROL OD"] if dv.get("ok") else None
        j2, rc2, tail2 = run_fix(fixpy, p7, FIN, os.environ["SPINE_DB"])
        d2, rows2 = digest(c7)
        s7["run2"] = dict(rc=rc2, json=j2, tail=(tail2 if j2 is None else ""))
        s7["same"] = d1 == d2
        s7["rows2"] = rows2
        c7.close()
    out["s7"] = s7
    ca.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "eye" probe (5)
def probe_eye():
    FIN, POR, DB, SIDE, WORK = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE", "WORKDIR"))
    NEW = SIDE == "new"
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    out = dict(side=SIDE)
    if NEW:                                                             # the copy as the install leaves it: the fixes applied first
        j, rc, _t = run_fix(os.environ["W502_FIXPY"], DB, FIN, os.environ["SPINE_DB"])
        out["fix"] = dict(rc=rc, A=(j or {}).get("A", {}).get("status"), B=(j or {}).get("B", {}).get("line"))
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import aaj_kaam as AK                                               # noqa: E402
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W502J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    sc, info = AK.connect(DB, mode="staff")
    out["floor"] = info.get("floor")
    eye = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        tok = m.group(1) if m else ""
        ck = {"Cookie": "clinic_sso=" + tok}
        home = pc.get("/portal?all=1", base_url=BASE, headers=ck).get_data(as_text=True)
        seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
        pg = fc.get("/finance/stockmatch", base_url=BASE, headers=ck)
        body = pg.get_data(as_text=True)
        st = fc.get("/finance/stockmatch/api/state", base_url=BASE, headers=ck)
        js = st.get_json(silent=True) or {}
        W = js.get("watch") or {}
        duties = []
        for du in dm.get("duties") or []:
            if du.get("person") != who or du.get("door") != "/finance/stockmatch":
                continue
            q = str(du.get("due_sql") or "").strip().rstrip(";")
            try:
                rr = sc.execute(q).fetchone()
                n = int((rr[0] if rr else 0) or 0)
            except Exception as e:                                      # noqa: BLE001
                n = "ERR " + str(e)[:80]
            duties.append(dict(id=du["id"], marker=du.get("door_marker"), due_n=n, marker_on_page=(du.get("door_marker") in body), tile_seen=(du.get("tile") in seen)))
        eye[who] = dict(login=r.status_code, tiles=len(seen), tile_stock=("Stock milaan" in seen), page=pg.status_code, marker=("Aaj ki ginti" in body),
                        state=st.status_code, watch_ok=W.get("ok"), roster=[dict(item=x.get("item"), qty=x.get("qty"), can_fix=x.get("can_fix"), has_can_fix=("can_fix" in x), by=x.get("by"))
                                                                                  for x in (W.get("roster") or {}).get("items", [])],
                        losses=[dict(at=l.get("at"), text=l.get("text_hi")) for l in (W.get("losses") or [])], traces_n=len(W.get("traces") or []),
                        duties=duties, me=js.get("me"))
        if who == "darpan" and NEW:
            with open(os.path.join(WORK, "state_darpan.json"), "w", encoding="utf-8") as fh:
                json.dump(js, fh, ensure_ascii=False, indent=1)
            out["state_file"] = os.path.join(WORK, "state_darpan.json")
    sc.close()
    out["eye"] = eye
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-eye"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_eye()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    m9raw = open(a.duty_map, "rb").read()
    check("the duty map beside the kit is v9 (md5 %s); this kit changes no duty" % md5b(m9raw)[:8], md5b(m9raw) == MAP9_MD5)
    fixpy = os.path.join(Wd, "fix_s502_copy.py")                        # a copy out of the kit folder: nothing runs from inside deploy_kits
    shutil.copy(os.path.join(a.kit, "fix_s502.py"), fixpy)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W502 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    for role in ("staff", "doctor"):
        try:
            clinic_users.add_role(store, role)
        except ValueError:
            pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, fin):
        wd = os.path.join(Wd, "%s_%s" % (mode, side))
        for sub in ("nosso", "noring", "nomarg"):
            os.makedirs(os.path.join(wd, sub))
        dbp, adbp, spp = [os.path.join(wd, "w502_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W502_DB0=a.db, W502_FIXPY=fixpy,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "eye" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, W502J=json.dumps(dict(pw=pw)), MARG_INGEST_DIR=os.path.join(wd, "nomarg"),
                   RING_PORTAL_DIR=os.path.join(wd, "noring"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"),
                   ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "ORDER_PUSH_NONE", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-40:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    NW, OL = run("fn", "new", a.fin_new), run("fn", "old", a.fin_old)
    if not check("both function probes ran to the end (NEW = the box + S502, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()
    check("after the NEW ensure, stock_watch_loss_line lists void_at and void_why (%s); OLD does not" % NW["cols"][-2:],
          "void_at" in NW["cols"] and "void_why" in NW["cols"] and "void_at" not in OL["cols"])

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  the correction: 'Galat likha? Badlo'")
    n1, o1 = NW["s1"], OL["s1"]
    sv = (n1["json"].get("saved") or {})
    P = sv.get("point") or {}
    check("/api/spot/fix as darpan, 50 -> 40: 200, a new point of 40 judged on the OLD expected 50 (gap -10, not against the old 50 as shelf) (%s)"
          % {k: P.get(k) for k in ("id", "qty", "expected", "gap", "status")},
          n1["code"] == 200 and n1["json"].get("ok") is True and P.get("expected") == 50 and P.get("gap") == -10 and P.get("qty") == 40 and sv.get("kind") == "spot_fix")
    check("the old point is superseded and its note names the replacement (%s)" % ({k: (n1["old"] or {}).get(k) for k in ("status", "note")},),
          (n1["old"] or {}).get("status") == "superseded" and "S502: badla, ab point %s" % P.get("id") in str((n1["old"] or {}).get("note")))
    check("the roster reads 40 and points at the new point; the new point is source spot with the roster id (%s / %s)" % (n1["roster"], {k: (n1["new"] or {}).get(k) for k in ("source", "roster_id", "expected_units", "by")}),
          n1["roster"] == [40.0, P.get("id")] and (n1["new"] or {}).get("source") == "spot" and (n1["new"] or {}).get("expected_units") == 50 and (n1["new"] or {}).get("by") == "darpan")
    check("the old point's open trace is closed by its own id (%s) and no other trace is closed (%s); the new point, still short beyond the allowance, has its own loss line and open trace (%s / %s)"
          % (n1["trace_old"], n1["trace_other"], n1["new_loss_line"], n1["new_trace_open"]),
          n1["trace_old"] == ["seen", "S502"] and n1["trace_other"] == ["open", None] and len(n1["new_loss_line"]) == 1 and n1["new_loss_line"][0][1] == P.get("id")
          and any(x[1] == "open" for x in n1["new_trace_open"]))
    check("one audit row 'spot_fix' by darpan (%s); the same quantity again -> 200 'Wahi ginti pehle se likhi hai.' (%s)" % (n1["audit"], n1["same_qty"]),
          n1["audit"] == [["spot_fix", "darpan"]] and n1["same_qty"][0] == 200 and n1["same_qty"][1] == "Wahi ginti pehle se likhi hai.")
    check("control OLD: no route -> 404 (%s)" % o1["code"], o1["code"] == 404)

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  not yesterday / not someone else's / the owner may")
    n2 = NW["s2"]
    check("a roster row dated yesterday -> 409 ok:false (%s)" % n2["yday"], n2["yday"][0] == 409 and n2["yday"][1] is False and n2["yday"][2] == "Sirf aaj ki ginti badal sakte hain.")
    check("a row answered by another user, fixed by darpan -> 403 ok:false (%s)" % n2["other"], n2["other"][0] == 403 and n2["other"][1] is False and "kisi aur ne" in n2["other"][2])
    check("the same row fixed as the owner -> 200, the old point superseded (%s / %s)" % (n2["owner"], n2["owner_old"]), n2["owner"][0] == 200 and n2["owner"][1] is True and n2["owner_old"] == "superseded")
    check("a roster id that does not exist -> 404 ok:false (%s)" % n2["nosuch"], n2["nosuch"] == [404, False])

    # ------------------------------------------------------------------------------------------------------------------------------- 3
    print("-- 3  superseded points are skipped where points are picked or summed")
    n3, o3 = NW["s3"], OL["s3"]
    check("last_point with the LATER point superseded (12:00) returns the 11:00 settled one (%s)" % n3["last_point"], (n3["last_point"] or {}).get("picked") == "11:00")
    check("control OLD returns the 12:00 superseded one (%s)" % o3["last_point"], (o3["last_point"] or {}).get("picked") == "12:00")
    check("month_leak for this month (a real item with an MRP: %s): a W502 superseded point of -30 leaves the total unchanged (%s -> %s)" % (n3["real_item"], n3.get("leak_before"), n3.get("leak_after")),
          n3.get("real_item") and n3.get("leak_before") is not None and n3.get("leak_before") == n3.get("leak_after"))
    check("control OLD: the total rises (%s -> %s)" % (o3.get("leak_before"), o3.get("leak_after")), o3.get("leak_before") is not None and o3.get("leak_after") > o3.get("leak_before"))

    # ------------------------------------------------------------------------------------------------------------------------------- 4
    print("-- 4  the recount door is closed to staff (the 06-Sep count is sealed)")
    n4, o4 = NW["s4"], OL["s4"]
    check("/api/recount as darpan for an item of the 06-Sep round (%s) -> 403 moved, 'Aaj ki ginti Stock batao mein likhiye.' (%s); as the owner not 403 (%s)" % (n4["item"], n4.get("darpan"), n4.get("owner")),
          n4.get("item") and n4["darpan"][0] == 403 and n4["darpan"][1] == "moved" and "Stock batao" in n4["darpan"][2] and n4["owner"] != 403)
    check("control OLD answers 200 to darpan (%s)" % (o4.get("darpan"),), o4.get("darpan", [0])[0] == 200)

    # ------------------------------------------------------------------------------------------------------------------------------- 7
    print("-- 7  the data fixes on a scratch copy, twice")
    n7 = NW["s7"]
    j1 = n7["run1"]["json"] or {}
    A1, B1 = j1.get("A") or {}, j1.get("B") or {}
    check("fix_s502 run 1: exit 0, A applied (old point 377 %s -> new point %s, gap %s), B line voided, trace set seen 1, TYRO BR asked (%s)"
          % (A1.get("old_status"), A1.get("new_point"), A1.get("gap"), B1.get("ask", {}).get("msg")),
          n7["run1"]["rc"] == 0 and A1.get("status") == "applied" and A1.get("gap") == 0 and B1.get("line") == "voided" and B1.get("trace_set_seen") == 1 and B1.get("ask", {}).get("ok") is True
          and "TYRO BR" in str(B1.get("ask", {}).get("msg")), n7["run1"]["tail"])
    if A1.get("note"):
        NOTES.append("fix A: " + A1["note"])
    check("after run 1: the roster reads 137 (%s); the newest non-superseded TRUECEPROL OD point is 137 with gap 0 (%s); point 377 superseded (%s)" % (n7["roster"], n7["newest"], [p for p in n7["points"] if p[0] == 377]),
          n7["roster"][1:3] == [137.0, A1.get("new_point")] and n7["newest"] and n7["newest"][1] == 137.0 and n7["newest"][2] == 0.0
          and any(p[0] == 377 and p[2] == "superseded" for p in n7["points"]))
    check("the shelf-fix row is off the 06-Sep count (count_id -1, the note says why) and Darpan's 'Aapne gina' list no longer carries it (%s / %s)" % (n7["shelf_fix"], n7["recounts_by"]),
          len(n7["shelf_fix"]) == 1 and n7["shelf_fix"][0][1] == -1 and "count se hata di" in str(n7["shelf_fix"][0][3]) and "TRUECEPROL OD" not in n7["recounts_by"])
    cache = A1.get("cache") or {}
    check("the 06-Sep cached line of TRUECEPROL OD reads counted 97 with its pile (bucket %s, grp %s, pile %s) before and after; the cache %s"
          % ((n7["cache_line"] or {}).get("bucket"), (n7["cache_line"] or {}).get("grp"), (n7["cache_line"] or {}).get("pile"),
             ("was recomputed" if cache.get("refreshed") else "was left to the desk's next full rebuild: " + str(cache.get("why"))[:120])),
          (n7["cache_line"] or {}).get("counted") == 97 and (cache.get("before") or {}).get("counted") == 97 and (cache.get("after") or {}).get("counted") == 97
          and (cache.get("before") or {}).get("bucket") == (cache.get("after") or {}).get("bucket") and (cache.get("before") or {}).get("grp") == (cache.get("after") or {}).get("grp"), cache)
    if not cache.get("refreshed"):
        NOTES.append("the Loss desk's pile cache of the 06-Sep count was NOT recomputed by the kit: " + str(cache.get("why")) + "; stamp parts differing: %s" % cache.get("stamp_parts_differing"))
    check("TYRO BR: the 70:7 line is voided with the brief's words (%s); trace 30 is seen by S502 (%s); TYRO BR is open in stock_watch_ask (%s)" % (n7["tyro_line"], n7["tyro_trace"], n7["tyro_ask"]),
          any(l[1] == 707.0 and l[3] == 1 and str(l[2]).startswith("S502: is din ka hisaab galat tha") for l in n7["tyro_line"]) and n7["tyro_trace"] and all(t[1] == "seen" and t[2] == "S502" for t in n7["tyro_trace"])
          and any(x[0] == "TYRO BR" and x[2] is None for x in n7["tyro_ask"]))
    check("Darpan's loss lines never show TYRO BR's 70:7 (%s); his roster row for TRUECEPROL OD reads 13 patte + 7 goli, can_fix (%s)" % (n7["darpan_losses"], n7["darpan_roster_truece"]),
          isinstance(n7["darpan_losses"], list) and not any("TYRO BR" in x and "70 patte" in x for x in n7["darpan_losses"]) and all("Doctor sahab dekh rahe hain" in x for x in n7["darpan_losses"])
          and n7["darpan_roster_truece"] and n7["darpan_roster_truece"][0]["qty"] == 137.0 and n7["darpan_roster_truece"][0]["can_fix"] is True)
    j2 = n7["run2"]["json"] or {}
    check("run 2 changes nothing: A %s, B %s / ask '%s'; the touched rows' digest is unchanged (%s)" % ((j2.get("A") or {}).get("status"), (j2.get("B") or {}).get("line"), (j2.get("B") or {}).get("ask", {}).get("msg"), n7["same"]),
          n7["run2"]["rc"] == 0 and (j2.get("A") or {}).get("status") == "already" and str((j2.get("B") or {}).get("line")).startswith("already") and (j2.get("B") or {}).get("trace_set_seen") == 0
          and "already" in str((j2.get("B") or {}).get("ask", {}).get("msg")) and n7["same"] is True)

    # ------------------------------------------------------------------------------------------------------------------------------- 5
    print("-- 5  the page, server side: darpan and the owner signed in through the portal (a walk-only store and secret)")
    EN, EO = run("eye", "new", a.fin_new), run("eye", "old", a.fin_old)
    if not check("both staff-eye probes ran to the end (NEW: the fixes applied on its copy first: %s)" % (EN or {}).get("fix"), EN is not None and EO is not None):
        return finish()
    en, eo = EN["eye"], EO["eye"]
    d = en["darpan"]
    check("darpan signs in (%s), holds the 'Stock milaan' tile (%s); /finance/stockmatch is 200 with 'Aaj ki ginti' on it; /api/state is 200, watch.ok, me=staff (%s)"
          % (d["login"], d["tile_stock"], d["me"]), d["login"] in (200, 302) and d["tile_stock"] and d["page"] == 200 and d["marker"] and d["state"] == 200 and d["watch_ok"] is True and d["me"] == "staff")
    check("every answered roster row carries can_fix; TRUECEPROL OD reads 137 by darpan (%s)" % d["roster"],
          all(x["has_can_fix"] for x in d["roster"]) and any(x["item"] == "TRUECEPROL OD" and x["qty"] == 137.0 and x["can_fix"] is True for x in d["roster"]))
    lim = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    check("watch.losses holds no voided line and none older than 7 days (%s)" % d["losses"],
          all(str(l["at"])[:10] >= lim for l in d["losses"]) and not any("TYRO BR" in l["text"] and "70 patte" in l["text"] for l in d["losses"]))
    check("control OLD: no can_fix on the rows, and TYRO BR's 70:7 line on the page (%s)" % [l["text"] for l in eo["darpan"]["losses"]],
          not any(x["has_can_fix"] for x in eo["darpan"]["roster"]) and any("TYRO BR" in l["text"] and "70 patte" in l["text"] for l in eo["darpan"]["losses"]))
    check("the duty darpan.spot_count keeps its door and marker ('Aaj ki ginti' on the page source) on the floored connection (%s)" % d["duties"],
          any(x["id"] == "darpan.spot_count" and x["marker_on_page"] for x in d["duties"]) and all(x["marker_on_page"] for x in d["duties"]))
    m = en["manoj"]
    check("manoj (checker) opens the page (%s) and the state (%s, me=%s)" % (m["page"], m["state"], m["me"]), m["page"] == 200 and m["state"] == 200 and m["me"] == "owner")
    print("   the darpan state JSON of the fixed copy for the PC's rendered check: %s" % EN.get("state_file"))
    # the source-level part of section 6 (the rendered check itself runs on the PC with render_stub_s502.py)
    new_h = open(os.path.join(a.fin_new, "stockmatch.html"), encoding="utf-8").read().split("<script>", 1)[1]
    old_h = open(os.path.join(a.fin_old, "stockmatch.html"), encoding="utf-8").read().split("<script>", 1)[1]
    check("NEW page script: 'Pichhle 7 din mein kam nikla', 'Galat likha? Badlo', 'Badal do', 'Aaj: ' and the fix route; none of blockCard / Dobara ginna hai / System ne dekha / the prog bar",
          all(w in new_h for w in ("Pichhle 7 din mein kam nikla", "Galat likha? Badlo", "Badal do", "/finance/stockmatch/api/spot/fix", "Sirf jaankari ke liye"))
          and not any(w in new_h for w in ("blockCard(", "Dobara ginna hai</h2>", "System ne dekha", 'class="prog"', "Ginti mein kam nikla")))
    check("control OLD page script carries blockCard, Dobara ginna hai, System ne dekha and the prog bar", all(w in old_h for w in ("blockCard(", "Dobara ginna hai</h2>", "System ne dekha", 'class="prog"')))
    for x in NOTES:
        print("   NOTE: " + mask(x))
    return finish()


def finish():
    if FAILS:
        print("WALK_S502 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:220])
        return 1
    print("WALK_S502 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
