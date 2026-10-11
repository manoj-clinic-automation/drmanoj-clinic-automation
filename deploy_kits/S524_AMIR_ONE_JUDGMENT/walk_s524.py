#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s524.py -- kit S524_AMIR_ONE_JUDGMENT: the walk (the brief's section 3), on the server, on scratch copies only.

    python3 -B walk_s524.py --kit DIR --work /tmp/... --run DIR --por DIR --db finance.db --adb assets.db --spine spine.db --p0 DIR --duty-map FILE

  run       the scratch layout the installer made: <run>/new/{finance,marg_ingest}, <run>/old/{finance,marg_ingest}; NEW carries the built
            files (stock_app.py, stockmatch.py, shelf_figure.py, amir_day.py in finance; marg_take.py in marg_ingest; spine/marg_read.py and
            spine/spine_build.py), OLD is the box as it is.  <run>/new/finance/spine is also the selftest's folder.
  por       a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there (never the live ones).
  db / adb  backup-API copies of finance.db and assets.db; every probe works on its OWN further copy.
  spine     the NEW spine built in Part 0 on the real evidence (scratch); every probe copies it and points SPINE_DB at its copy.
  p0        Part 0's artefacts: old_old/ new_new/ old_new/ new_old/ (each spine_state.json and spine.db or spine.db.failed), live_spine.db.
  duty-map  the v10 DUTY_MAP.json (the repository clone's); the v9 due_sql is embedded here as the control.

Probes run as fresh processes per side ("api": the live case through the routes, signed in through a walk-only portal as amir and as the
owner; "fn": the functions on their own copies), every one with ORDER_PUSH_STUB, a scratch RING_PORTAL_DIR and REPORTS_NTFY_STUB: nothing
reaches a phone.  Every control is the same probe on the OLD files and must go red there.  Rows are found by key, never by counting.
No person, phone or account number is in this file; item names only."""
import argparse
import datetime as dt
import hashlib
import html as _html
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time

TAG = "W524JSON "
USERS = {"amir": "staff", "manoj": "doctor"}
LS_ITEM_L = "L S BELT CONT GRAY UNISON L"
PENDING_ITEM = "ANKLE BINDER BAMBOO L"
NEW_CARD = "naya voucher Doctor sahab banayenge"
V9_SQL = ("SELECT COUNT(*) AS n, MIN(made_at) AS since FROM (SELECT l.count_id, l.round_no, l.kind, l.batch_no, MIN(l.made_at) AS made_at FROM stock_voucher_line l "
          "GROUP BY l.count_id, l.round_no, l.kind, l.batch_no) b WHERE NOT EXISTS (SELECT 1 FROM stock_voucher_entered e WHERE e.count_id = b.count_id "
          "AND e.round_no = b.round_no AND e.kind = b.kind AND e.batch_no = b.batch_no AND TRIM(COALESCE(e.marg_voucher_no,'')) <> '' AND e.id = "
          "(SELECT MAX(e2.id) FROM stock_voucher_entered e2 WHERE e2.count_id = b.count_id AND e2.round_no = b.round_no AND e2.kind = b.kind AND e2.batch_no = b.batch_no))")
TIED_BILLS = ("GPPL2678591", "GPPPL3679039", "A000207_", "YS0706202627")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + mask(label) + (("   [" + mask(str(got))[:1200] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


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
    return con.execute("INSERT INTO %s (%s) VALUES (%s)" % (table, ", ".join(cols), ", ".join("?" * len(cols))), [row[c] for c in cols]).lastrowid


def texts(h):
    return [_html.unescape(x).strip() for x in re.findall(r">([^<]{3,300})<", h or "")]


def dmy(iso):
    s = str(iso or "")
    return "%s-%s-%s" % (s[8:10], s[5:7], s[0:4])


def now_iso():
    return dt.datetime.now().isoformat(timespec="seconds")


def keyset(ks):
    return sorted("%d|%s|%d" % (int(k[0]), k[1], int(k[2])) for k in ks or [])


def events(c, root):
    return [list(r) for r in c.execute("SELECT stage, event, ref, detail FROM stock_stage_event WHERE count_id=? ORDER BY id", (root,))]


def add_ortho_batch(c, root, rno=9):
    """One un-entered orthotic batch of the root, by key (round rno, ISSUE, batch 1) -- the walk's own row."""
    ins(c, "stock_voucher_line", dict(count_id=root, round_no=rno, kind="ISSUE", batch_no=1, batches_n=1, line_no=1, section="Orthotics", family="w524",
                                      item="W524 ORTHO ITEM", packing="1*1", pack=1, marg_from=1, change=-1, marg_to=0, counted=0, reason="W524 walk",
                                      made_by="W524", made_at=now_iso()))
    c.commit()
    return (rno, "ISSUE", 1)


# ============================================================================================================== the "api" probe
def probe_api():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import stock_app as SA                                              # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    W = json.loads(os.environ["W524J"])
    pw = W["pw"]
    c = sqlite3.connect(DB, timeout=60)
    root = SA._s446_root(c)
    out = dict(side=SIDE, root=root)
    ck = {}
    for who in USERS:
        r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
        m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
        ck[who] = {"Cookie": "clinic_sso=" + (m.group(1) if m else "")}

    def board(who):
        t0 = time.perf_counter()
        rr = fc.get("/finance/stock/api/pad/amir/%d" % root, base_url=BASE, headers=ck[who])
        j = rr.get_json(silent=True) or {}
        flat = ((j.get("made") or {}).get("vouchers_flat") or [])
        return dict(code=rr.status_code, proof_state=j.get("proof_state"), proof_hi=j.get("proof_hi"), renames_ready=j.get("renames_ready"),
                    renames_wait_hi=j.get("renames_wait_hi"), renames_n=len((j.get("renames") or {}).get("rows") or []),
                    flat=sorted("%d|%s|%d" % (v["round_no"], v["kind"], v["batch_no"]) for v in flat),
                    stage=(j.get("stage") or {}).get("stage") if isinstance(j.get("stage"), dict) else None,
                    hona=("hona chahiye" in json.dumps(j, ensure_ascii=False)), ms=int((time.perf_counter() - t0) * 1000))

    def step6(who):
        rr = fc.get("/finance/amir/step/6", base_url=BASE, headers=ck[who])
        h = rr.get_data(as_text=True)
        tx = texts(h)
        return dict(code=rr.status_code, marker=("Marg sudhar" in h), baaki=[x for x in tx if x.startswith("Orthotic voucher baaki")][:2],
                    sahi=[x for x in tx if "Orthotic ke" in x or "Orthotic:" in x][:3], newcard=(NEW_CARD in h), naam=[x for x in tx if x.startswith("Naam badlo")][:2],
                    hona=("hona chahiye" in h), wrong=("Marg mein yeh abhi sahi nahi hain" in h))

    def stage_direct():
        SA._S446_PROOF_CACHE.clear()
        st = SA.amir_stage(c, root)
        A = (st or {}).get("A") or {}
        return dict(stage=(st or {}).get("stage"), A_open=A.get("open"), A_pending=A.get("pending"), A_proof=((A.get("proof") or {}).get("state")),
                    as_after=((A.get("proof") or {}).get("as_after")), visible=keyset((st or {}).get("visible")), renames_visible=(st or {}).get("renames_visible"),
                    wrong_items=[r["item"] for r in ((A.get("proof") or {}).get("rows") or [])])
    # ---- 1. the board as it stands: two reads as amir (the once-only recheck event), one as the owner
    out["events0"] = events(c, root)
    out["board_amir_1"] = board("amir")
    out["events1"] = events(c, root)
    out["board_amir_2"] = board("amir")
    out["events2"] = events(c, root)
    out["board_owner"] = board("manoj")
    out["step6_before"] = step6("amir")
    out["stage_before"] = stage_direct()
    # ---- 2. one un-entered orthotic batch (the walk's own) -> the duty is due; stage A lists it; the door shows it
    kb = add_ortho_batch(c, root)
    out["new_key"] = "%d|%s|%d" % kb
    out["board_amir_3"] = board("amir")
    out["events3"] = events(c, root)
    out["board_amir_4"] = board("amir")
    out["events4"] = events(c, root)
    out["board_owner_2"] = board("manoj")
    out["stage_after"] = stage_direct()
    out["step6_after"] = step6("amir")
    # the duty map, as the staff-eye walk reads it: amir's duties, their due counts on this copy, the tile on his home, the door's marker
    dm = json.load(open(os.environ["W524_DUTY_MAP"], encoding="utf-8"))
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    r1 = pc.get("/portal", base_url=BASE, headers=ck["amir"])
    r3 = pc.get("/portal?all=1", base_url=BASE, headers=ck["amir"])
    tiles = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', r3.get_data(as_text=True) or "")]
    rows = []
    for du in dm.get("duties") or []:
        if du.get("person") != "amir":
            continue
        row = dict(id=du["id"], tile=du.get("tile"), tile_seen=(du.get("tile") in tiles) if du.get("tile") else None, due_n=None, door_seen=None)
        try:
            rr = ro.execute(str(du.get("due_sql") or "").rstrip(";")).fetchone()
            row["due_n"] = int((rr[0] if rr else 0) or 0)
            row["since"] = rr[1] if rr else None
        except Exception as e:                                          # noqa: BLE001
            row["due_n"] = "ERR " + str(e)[:80]
        door, mark = du.get("door"), du.get("door_marker")
        if door and mark and isinstance(row["due_n"], int) and row["due_n"] > 0 and str(door).startswith("/finance/"):
            path, body = str(door), ""
            for _hop in range(4):
                r = fc.get(path, base_url=BASE, headers=ck["amir"])
                if r.status_code in (301, 302, 303) and r.headers.get("Location", "").startswith(("/finance/", BASE + "/finance/")):
                    path = r.headers["Location"].replace(BASE, "")
                    continue
                body = r.get_data(as_text=True)
                break
            row["door_seen"] = mark in body
        rows.append(row)
    ro.close()
    out["eye"] = dict(first=[r1.status_code, r1.headers.get("Location", "")], tiles=tiles, duties=rows, version=dm.get("version"))
    # the owner's hub (step 7 = the proof) and the orthotic section (stockmatch) as the owner
    rr = fc.get("/finance/stock/api/pad/hub/%d" % root, base_url=BASE, headers=ck["manoj"])
    j = rr.get_json(silent=True) or {}
    P = j.get("proof") or {}
    O = j.get("ortho") or {}
    out["hub"] = dict(code=rr.status_code, state=P.get("state"), text=P.get("text"), rows=[(r.get("item"), r.get("why")) for r in (P.get("rows") or [])][:6],
                      stage=P.get("stage"), moved_without=P.get("moved_without"), hona=("hona chahiye" in json.dumps(j, ensure_ascii=False)),
                      ortho_conds={x.get("key"): (x.get("ok"), x.get("en")) for x in (O.get("conds") or [])}, ortho_ok=O.get("ok"))
    rr = fc.get("/finance/stock/page/hub?count=%d" % root, base_url=BASE, headers=ck["manoj"])
    out["hub_page"] = rr.status_code
    rr = fc.get("/finance/stockmatch", base_url=BASE, headers=ck["manoj"])
    out["sm_page"] = rr.status_code
    rr = fc.get("/finance/stockmatch/api/state", base_url=BASE, headers=ck["manoj"])
    j = rr.get_json(silent=True) or {}
    sec = j if isinstance(j.get("conds"), list) else next((v for v in j.values() if isinstance(v, dict) and isinstance(v.get("conds"), list)), {})
    out["sm_api"] = dict(code=rr.status_code, conds={x.get("key"): (x.get("ok"), x.get("en")) for x in (sec.get("conds") or [])},
                         hona=("hona chahiye" in json.dumps(j, ensure_ascii=False)))
    # every step 1-7 as amir: no 'hona chahiye' anywhere
    out["steps_hona"] = []
    for n in range(1, 8):
        rr = fc.get("/finance/amir/step/%d" % n, base_url=BASE, headers=ck["amir"])
        if "hona chahiye" in rr.get_data(as_text=True):
            out["steps_hona"].append(n)
    # ---- 3. the door (F-845): amir on a medicine batch (not released) / on the orthotic batch (released) / clear; the owner on the medicine batch
    def post(who, rno, kind, bno, clear=False):
        body = dict(round=rno, kind=kind, batch=bno)
        body.update(dict(clear=True) if clear else dict(marg_voucher_no="W524V%d" % rno, entered_on="11-10-2026"))
        rr = fc.post("/finance/stock/api/pad/vouchers/%d/entered" % root, base_url=BASE, headers=ck[who], json=body)
        j = rr.get_json(silent=True) or {}
        return [rr.status_code, j.get("error")]
    med = c.execute("SELECT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=? AND section='Medicines' ORDER BY round_no, kind, batch_no LIMIT 1", (root,)).fetchone()
    out["med_key"] = "%d|%s|%d" % tuple(med)
    out["post"] = dict(amir_med=post("amir", *med), amir_ortho=post("amir", *kb), amir_ortho_clear=post("amir", *kb, clear=True),
                       owner_med=post("manoj", *med), owner_med_clear=post("manoj", *med, clear=True))
    out["roles"] = [list(r) for r in c.execute("SELECT unit, role, username FROM unit_role WHERE lower(username) IN ('amir','manoj') AND active=1 AND unit='medical'")]
    # ---- 4. timing (reported, not gated)
    SA.amir_stage(c, root)
    t0 = time.perf_counter()
    SA.amir_stage(c, root)
    out["ms_stage_warm"] = int((time.perf_counter() - t0) * 1000)
    out["ms_board"] = board("amir")["ms"]
    out["events_end"] = events(c, root)
    c.close()
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "fn" probe
def probe_fn():
    FIN, WORK, SIDE, DB0, SP0, ING = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W524_DB0", "W524_SPINE0", "INGDIR"))
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402,F401 -- the app, so stock_app is the side's own file
    import stock_app as SA                                              # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stockmatch as SM                                             # noqa: E402
    import shelf_figure as SF                                           # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    assert SA.__file__.startswith(FIN), SA.__file__
    NEW = hasattr(SA, "_s524_table")
    out = dict(side=SIDE, new=NEW, spine_db=SW.SPINE_DB)

    def mk(name, spine=True):
        p = os.path.join(WORK, "w524_%s.db" % name)
        copydb(DB0, p)
        if spine:
            sp = os.path.join(WORK, "w524_%s_spine.db" % name)
            copydb(SP0, sp)
            SW.SPINE_DB = sp                                            # the proof opens _sw.Spine() -> this copy
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        SA._voucher_ensure(c)
        SA._feed_ensure(c)
        SA._s446_ensure(c)
        SA._S446_PROOF_CACHE.clear()
        if hasattr(SA, "_S524_REPORT_CACHE"):
            SA._S524_REPORT_CACHE.clear()
        if hasattr(SF, "_S524_CAPTURES"):
            SF._S524_CAPTURES.clear()
        return c, (sp if spine else None)

    def proof(c, root):
        SA._S446_PROOF_CACHE.clear()
        b = SA._s446_batches(c, root)
        e = SA._s446_entered(c, root)
        ortho = SA._s446_order([k for k, bb in b.items() if "Orthotics" in bb["secs"]])
        return SA._s446_proof(c, root, ortho, e, b), b, e, ortho

    def view(pr):
        return dict(state=pr.get("state"), why=pr.get("why"), as_before=pr.get("as_before"), as_after=pr.get("as_after"), items=pr.get("items"),
                    rows=[(r["item"], r.get("ok"), r.get("should"), r.get("closing_day"), r.get("moved_hi"), r.get("need_hi"), r.get("key"), r.get("family"))
                          for r in pr.get("rows") or []],
                    unseen=[(r["item"], r.get("why")) for r in pr.get("unseen") or []], proven_on=pr.get("proven_on"))

    # ---- 1. the regression: count #1's orthotic batches on the rebuilt spine, the per-key table (NEW); the OLD proof on the same copy (information)
    c, sp = mk("reg")
    root = SA._s446_root(c)
    pr, b, e, ortho = proof(c, root)
    out["root"] = root
    out["reg"] = view(pr)
    spc = sqlite3.connect("file:%s?mode=ro" % sp, uri=True)
    out["built"] = spc.execute("SELECT value FROM sp_meta WHERE key='built'").fetchone()[0]
    out["newest_close"] = spc.execute("SELECT MAX(as_on) FROM sp_close").fetchone()[0]
    out["first_at"] = min(e[k][1] for k in ortho)
    out["last_at"] = max(e[k][1] for k in ortho)
    T = None
    if NEW:
        spx = SA._s524_spine()
        T = SA._s524_table(c, spx, root, e, b, out["first_at"][:19], out["last_at"][:19])
        out["R"] = {k: T["R"][k] for k in ("as_on", "stamp", "end_day")} if T["R"] else None
        out["after"] = [(x["as_on"], x["stamp"], x["end_day"]) for x in T["after"]]
        out["tries"] = [(x["as_on"], x["stamp"], x["end_day"]) for x in T["tries"]]
        out["reach"] = T["reach"]
        out["mixed"] = sorted(T["mixed"])
        out["table"] = []
        for k, ent_ in sorted(T["keys"].items()):
            for t in ent_["tries"]:
                out["table"].append(dict(key=k, X=t["X"]["as_on"], need=t.get("need"), marg_move=t.get("marg_move"), spine_move=t.get("spine_move"),
                                         late=t.get("late"), ok=t.get("ok"), why=t.get("why"), items=sorted(ent_["items"])))
        out["closings"] = [(x["as_on"], x["stamp"], x["end_day"]) for x in T["closings"][-8:]]
        if T["R"]:
            out["moves"] = {}
            for kk in (T["kof"].get(LS_ITEM_L), T["kof"].get("TYNOR WRIST SPLINT RT M ELAST"), T["kof"].get("ANKLE BINDER BAMBOO M")):
                out["moves"][kk] = dict(moves=spc.execute("SELECT date, kind, units, ref FROM sp_move WHERE k20=? AND date > ? AND date <= '2026-12-31' ORDER BY date", (kk, T["R"]["end_day"])).fetchall(),
                                        close=spc.execute("SELECT as_on, units FROM sp_close WHERE k20=? AND as_on >= ? ORDER BY as_on", (kk, T["R"]["as_on"])).fetchall())
        spx.con.close()
    spc.close()
    c.close()
    # ---- 2. F-843: one sale of the LS BELT key after R (both sides -1): NEW the key's verdict unchanged / OLD size L wrong with a should
    ls_key = None
    if NEW and T and T["tries"]:
        ls_key = T["kof"].get(LS_ITEM_L)
        R_end, X0 = T["R"]["end_day"], T["after"][0]
        d = (dt.date.fromisoformat(R_end) + dt.timedelta(days=1)).isoformat()          # the day after R: inside (end_day(R), end_day(after[0])]
        d = d if d <= X0["end_day"] else None
        # the inverse case must not be explained away by the spine's late-purchase reading: a delta no one or two purchases of the key in the
        # 21 days up to R's day add up to
        spx = sqlite3.connect("file:%s?mode=ro" % sp, uri=True)
        late = [float(r[0] or 0) for r in spx.execute("SELECT units FROM sp_move WHERE k20=? AND kind IN ('PURCHASE','PURCHASE_RETURN') AND date >= ? AND date <= ?",
                                                      (ls_key, (dt.date.fromisoformat(R_end) - dt.timedelta(days=21)).isoformat(), R_end))]
        spx.close()
        expl = set(late) | {late[i] + late[j] for i in range(len(late)) for j in range(i + 1, len(late))}
        res0 = [t.get("res") or 0.0 for t in (T["keys"].get(ls_key) or {}).get("tries") or [] if t.get("ok") is not None]   # the key's own residue at each try
        delta = next(k for k in range(1, 40) if all(abs(k + r0) >= 0.5 and not any(abs(k + r0 - u) < 0.5 for u in expl) for r0 in res0))
        out["f843_setup"] = dict(key=ls_key, d=d, R_end=R_end, tries=[x["as_on"] for x in T["tries"]], late=late, res0=res0, delta=delta)
    else:
        out["f843_setup"] = dict(key=None)
    sale_d = (out["f843_setup"] or {}).get("d")
    if (NEW and ls_key and sale_d) or (not NEW and os.environ.get("W524_LS")):
        W = json.loads(os.environ.get("W524_LS") or "{}") if not NEW else dict(key=ls_key, d=sale_d, tries=[x["as_on"] for x in T["tries"]], delta=out["f843_setup"]["delta"])
        c, sp = mk("f843")
        spw = sqlite3.connect(sp)
        spw.execute("INSERT INTO sp_move (k20, date, kind, units, ref) VALUES (?,?,?,?,?)", (W["key"], W["d"], "SALE", -1.0, "W524"))
        spw.execute("UPDATE sp_close SET units = units - 1 WHERE k20=? AND as_on >= ?", (W["key"], W["d"]))
        spw.commit()
        spw.close()
        c.execute("UPDATE stock_feed SET qty = qty - 1 WHERE item=? AND LOWER(source) LIKE 'push_snapshot%' AND "
                  "substr(as_on,7,4)||'-'||substr(as_on,4,2)||'-'||substr(as_on,1,2) >= ?", (LS_ITEM_L, W["d"]))
        c.commit()
        pr2, _b, _e, _o = proof(c, root)
        out["f843"] = view(pr2)
        c.close()
        if NEW:
            c, sp = mk("f843inv")
            spw = sqlite3.connect(sp)
            for x in W["tries"]:
                spw.execute("UPDATE sp_close SET units = units + ? WHERE k20=? AND as_on=?", (W["delta"], W["key"], x))
            spw.commit()
            spw.close()
            pr3, _b, _e, _o = proof(c, root)
            out["f843_inv"] = view(pr3)
            # F-840 (b): the orthotic section on the inverse copy
            try:
                d_ = SA._pad_report_data(c, root)
                SA._S446_PROOF_CACHE.clear()
                st = SM.section_state(c, d_)
                out["f840_inv"] = dict(c3=[x for x in st["conds"] if x["key"] == "proof"][0]["ok"], text=[x for x in st["conds"] if x["key"] == "proof"][0]["en"],
                                       proof=st.get("proof"))
            except Exception as ex:                                     # noqa: BLE001
                out["f840_inv"] = dict(error="%s: %s" % (type(ex).__name__, str(ex)[:200]))
            c.close()
        out["f843_W"] = W
    # ---- 3. F-844: the stage on the plain copy, the recheck event once per ref, the new batch listed, the pending line cleared
    c, sp = mk("f844")
    res = {}
    try:
        res["ev0"] = events(c, root)
        st = SA.amir_stage(c, root)
        A = st["A"]
        res["s1"] = dict(stage=st["stage"], open=A.get("open"), pending=A.get("pending"), proof=(A.get("proof") or {}).get("state"), as_after=(A.get("proof") or {}).get("as_after"),
                         visible=keyset(st["visible"]), ortho=keyset(ortho), renames_visible=st.get("renames_visible"))
        res["ev1"] = events(c, root)
        SA.amir_stage(c, root)
        res["ev2"] = events(c, root)
        bb = SA._s521_stage_proof(c, dict(count_id=root, proof_state="x", proof_hi="x", renames_ready=None, renames_wait_hi="x", made=dict(vouchers_flat=[])))
        res["s521"] = dict(proof_state=bb.get("proof_state"), proof_hi=bb.get("proof_hi"), renames_ready=bb.get("renames_ready"))
        res["card"] = AD._s446_card(dict(s446=dict(stage=st)))
        kb = add_ortho_batch(c, root)
        st2 = SA.amir_stage(c, root)
        res["s2"] = dict(stage=st2["stage"], open=st2["A"].get("open"), pending=st2["A"].get("pending"), visible=keyset(st2["visible"]), new_key="%d|%s|%d" % kb,
                         listed=("%d|%s|%d" % kb) in keyset(st2["visible"]))
        res["ev3"] = events(c, root)
        SA.amir_stage(c, root)
        res["ev4"] = events(c, root)
        # the pending line cleared: a correcting shelf figure of the keyed shape loss_piles.apply_fixes reads (counted = marg - 2 -> the line nets to its vouchers)
        d_ = SA._pad_report_data(c, root)
        x = [y for y in d_["differences"] if y["item"] == PENDING_ITEM]
        res["pending_line"] = [(y["item"], y.get("marg"), y.get("counted"), y.get("diff"), (y.get("word") or {}).get("action")) for y in x]
        res["pend_before"] = [(p["item"], p["change"]) for p in SA._voucher_pending(c, d_, section="Orthotics")]
        c.execute("DELETE FROM stock_voucher_line WHERE count_id=? AND round_no=? AND kind=? AND batch_no=? AND made_by='W524'", (root, kb[0], kb[1], kb[2]))
        if x:
            ins(c, "stock_shelf_fix", dict(count_id=root, item=PENDING_ITEM, qty=int(x[0]["marg"]) - 2, source="accept_back", note="W524 walk", by_user="W524", at=now_iso()))
        c.commit()
        d2 = SA._pad_report_data(c, root)
        res["pend_after"] = [(p["item"], p["change"]) for p in SA._voucher_pending(c, d2, section="Orthotics")]
        st3 = SA.amir_stage(c, root)
        res["s3"] = dict(stage=st3["stage"], pending=st3["A"].get("pending"), proof=(st3["A"].get("proof") or {}).get("state"))
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f844"] = res
    c.close()
    # ---- 6. F-847: a short closing never verifies a rename (marg_take._rename_verify on this side's ingest dir); proof side: an absent key
    res = {}
    try:
        sys.path.insert(0, ING)
        if "marg_take" in sys.modules:
            del sys.modules["marg_take"]
        import marg_take as MT                                          # noqa: E402
        assert MT.__file__.startswith(ING), MT.__file__
        import item_alias as IA                                         # noqa: E402
        import openpyxl                                                 # noqa: E402
        c, _sp = mk("f847", spine=False)
        day = c.execute("SELECT as_on FROM stock_snapshot GROUP BY as_on ORDER BY substr(as_on,7,4)||substr(as_on,4,2)||substr(as_on,1,2) DESC LIMIT 1").fetchone()[0]
        names = [r[0] for r in c.execute("SELECT item FROM stock_snapshot WHERE as_on=? ORDER BY item", (day,))]
        planned = [r for r in IA.rows(c) if r["state"] == "planned"]
        old_name = planned[0]["old_name"]
        ok_t, msg_t, _row = IA.tick(c, old_name, "W524", ts="2026-10-11T00:00:01")
        c.commit()
        as_on_txt = "11-10-2026"

        def closing_xlsx(path, items):
            wb = openpyxl.Workbook()
            ws = wb.active
            for row in (["SANJEEVNI MEDICOS"], ["35G/15B , RAMPUR BAGH BAREILLY"], ["WHOLE STORES CLOSING STOCK AS ON " + as_on_txt],
                        ["S.No.", "Description", "Total Stock", "Unit"]):
                ws.append(row)
            for n, nm in enumerate(items, 1):
                ws.append([n, "%-30s%s" % (nm[:29], "1*1"), 1, "PCS"])
            ws.append(["TOTAL", "", len(items), ""])
            wb.save(path)
            return hashlib.md5(open(path, "rb").read()).hexdigest()
        ps = os.path.join(WORK, "W524_short.xlsx")
        pw_ = os.path.join(WORK, "W524_whole.xlsx")
        short_names = [n for n in names if n != old_name][:249] + [old_name]
        m_s = closing_xlsx(ps, short_names)
        m_w = closing_xlsx(pw_, names)
        seen = lambda: c.execute("SELECT seen_n, verified_at FROM marg_item_rename WHERE old_name=?", (old_name,)).fetchone()   # noqa: E731
        res["ticked"] = [ok_t, msg_t]
        res["ref"] = dict(day=day, n_names=len(names), short=len(short_names), old_in_names=(old_name in names))
        try:
            import reports_watch as RW                                  # noqa: E402
            res["closing_short"] = RW.closing_short(c, "2026-10-11", len(short_names))
        except Exception as ex:                                         # noqa: BLE001
            res["closing_short"] = "ERR " + str(ex)[:120]
        res["seen0"] = list(seen())
        MT._rename_verify(c, ps, m_s, "20261011-120000")
        c.commit()
        res["seen_short"] = list(seen())
        MT._rename_verify(c, pw_, m_w, "20261011-120100")
        c.commit()
        res["seen_whole"] = list(seen())
        c.close()
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f847"] = res
    if NEW and ls_key and T and T["after"]:
        c, sp = mk("f847p")
        spw = sqlite3.connect(sp)
        for x in T["after"]:
            spw.execute("DELETE FROM sp_close WHERE k20=? AND as_on=?", (ls_key, x["as_on"]))
        spw.commit()
        spw.close()
        pr4, _b, _e, _o = proof(c, root)
        out["f847_proof"] = view(pr4)
        c.close()
    # ---- 7. F-848: the shelf gap judges a voucher by its moment
    c, _sp = mk("f848", spine=False)
    res = {}
    try:
        D = "2031-04-01"
        D1, D2, D3, D4, D5 = "2031-04-02", "2031-04-03", "2031-04-04", "2031-04-05", "2031-04-06"
        it1, it2 = "W524 GAP ITEM", "W524 GAP ITEM TWO"
        for day, rcv in ((D, D1 + "T06:00:00"), (D1, D1 + "T09:30:00"), (D2, D2 + "T22:30:00")):
            ins(c, "stock_feed", dict(as_on=dmy(day), source="push_snapshot W524", item=it1, qty=5, received_at=rcv))
        ins(c, "stock_feed", dict(as_on=dmy(D5), source="push_snapshot W524", item=it2, qty=5, received_at=D5 + "T23:00:00"))
        for it, rno, at, eon in ((it1, 1, D1 + "T09:50:00", dmy(D1)), (it2, 2, D5 + "T12:00:00", dmy(D5))):
            ins(c, "stock_voucher_line", dict(count_id=9524001, round_no=rno, kind="ISSUE", batch_no=1, batches_n=1, line_no=1, section="Medicines", item=it,
                                              packing="1*10", pack=10, marg_from=5, change=-1, marg_to=4, reason="W524", made_by="W524", made_at=D))
            ins(c, "stock_voucher_entered", dict(count_id=9524001, round_no=rno, kind="ISSUE", batch_no=1, marg_voucher_no="W524V", entered_on=eon, by_user="W524", at=at))
        c.commit()
        if hasattr(SF, "_S524_CAPTURES"):
            SF._S524_CAPTURES.clear()
        res["w_D_D1"] = SF.filed_vouchers(c, it1, D, D1)
        res["w_D1_D2"] = SF.filed_vouchers(c, it1, D1, D2)
        res["w_D2_D3"] = SF.filed_vouchers(c, it1, D2, D3)
        res["w_missing_day_rule"] = SF.filed_vouchers(c, it2, D4, D5)
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f848"] = res
    c.close()
    # ---- 8. F-840: the orthotic section's c3 on the plain copy, and on a copy whose voucher lines are moved aside
    res = {}
    try:
        c, sp = mk("f840")
        d_ = SA._pad_report_data(c, root)
        st = SM.section_state(c, d_)
        pc_ = [x for x in st["conds"] if x["key"] == "proof"][0]
        res["plain"] = dict(c3=pc_["ok"], text=pc_["en"], proof=st.get("proof"), closed=st.get("closed"))
        c.close()
        c, sp = mk("f840none")
        c.execute("UPDATE stock_voucher_line SET count_id = count_id + 9000000 WHERE count_id=?", (root,))
        c.commit()
        d_ = SA._pad_report_data(c, root)
        st = SM.section_state(c, d_)
        pc_ = [x for x in st["conds"] if x["key"] == "proof"][0]
        res["none"] = dict(c3=pc_["ok"], text=(st.get("proof") or {}).get("text"), cond=pc_["en"])
        c.close()
    except Exception as ex:                                             # noqa: BLE001
        res["error"] = "%s: %s" % (type(ex).__name__, str(ex)[:300])
    out["f840"] = res
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def run_probe(a, mode, side, Wd, store, secret, pw, extra=None):
    fin = os.path.join(a.run, side, "finance")
    ing = os.path.join(a.run, side, "marg_ingest")
    wd = os.path.join(Wd, "%s_%s" % (mode, side))
    for sub in ("nosso", "noring", "nomarg"):
        os.makedirs(os.path.join(wd, sub))
    dbp, adbp, spp = [os.path.join(wd, "w524_%s.db" % x) for x in ("app", "assets", "spine")]
    copydb(a.db, dbp)
    copydb(a.adb, adbp)
    copydb(a.spine, spp)
    env = dict(os.environ, SIDE=side, FINDIR=fin, INGDIR=ing, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W524_DB0=a.db, W524_SPINE0=a.spine,
               FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "api" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
               CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret, W524J=json.dumps(dict(pw=pw)),
               W524_DUTY_MAP=os.path.abspath(a.duty_map), MARG_INGEST_DIR=os.path.join(wd, "nomarg"), RING_PORTAL_DIR=os.path.join(wd, "noring"),
               ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"), REPORTS_NTFY_STUB=os.path.join(wd, "ntfy_stub.jsonl"), ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"),
               SR_DB_PATH=os.path.join(wd, "no_staff_register.db"), CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
    env.update(extra or {})
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


def gate_of(path):
    """(passed, gate, failed names, FAIL lines) of a Part-0 build folder: spine_state.json beside spine.db / spine.db.failed."""
    st = json.load(open(os.path.join(path, "spine_state.json")))
    dbp = os.path.join(path, "spine.db") if os.path.exists(os.path.join(path, "spine.db")) else os.path.join(path, "spine.db.failed")
    c = sqlite3.connect("file:%s?mode=ro" % dbp, uri=True)
    rows = c.execute("SELECT n, name, blocking, ok, substr(detail,1,400) FROM sp_gate ORDER BY n").fetchall()
    c.close()
    return st.get("passed"), st.get("gate"), st.get("failed"), [(r[0], r[1], r[4]) for r in rows if r[2] and not r[3]], dbp


def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-api"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_api()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--run", "--por", "--db", "--adb", "--spine", "--p0", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    Wd = os.path.abspath(a.work)
    assert Wd.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % Wd
    os.makedirs(Wd)
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W524 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
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

    # ------------------------------------------------------------------------------------------------------------------------------- 0
    print("-- 0  Part 0 on the real evidence (scratch builds the installer made): the gate before and after, the bills of 01-Sep, the four tied bills")
    oo = gate_of(os.path.join(a.p0, "old_old"))
    nn = gate_of(os.path.join(a.p0, "new_new"))
    on = gate_of(os.path.join(a.p0, "old_new"))
    no = gate_of(os.path.join(a.p0, "new_old"))
    print("   OLD builder on the OLD readings (the box as it was): gate %s passed %s" % (oo[1], oo[0]))
    for n_, name, det in oo[3]:
        print("      FAIL %d %s -- %s" % (n_, name, mask(det)[:260]))
    print("   OLD builder on the re-read readings: gate %s; NEW builder on the OLD readings: gate %s (each repairs one gate line)" % (on[1], no[1]))
    print("   NEW builder on the re-read readings: gate %s passed %s" % (nn[1], nn[0]))
    for n_, name, det in nn[3]:
        print("      FAIL %d %s -- %s" % (n_, name, mask(det)[:260]))
    check("control: the OLD spine_build on the OLD readings fails its gate 11/13 on the two purchase-line checks", oo[0] is False and oo[1] == "11/13" and len(oo[2] or []) == 2
          and all("purchase line" in x for x in oo[2]), oo[2])
    check("the NEW spine_build on the re-read readings passes 13/13 and would swap", nn[0] is True and nn[1] == "13/13" and not nn[3], nn[1])
    check("each repair alone leaves the gate red (old builder / new readings %s; new builder / old readings %s): both are needed" % (on[1], no[1]),
          on[0] is False and no[0] is False)
    live = sqlite3.connect("file:%s?mode=ro" % os.path.join(a.p0, "live_spine.db"), uri=True)
    new = sqlite3.connect("file:%s?mode=ro" % nn[4], uri=True)
    q = "SELECT supkey, bill, date, seq, name27, qty, free, units, net_amount_p, direction FROM sp_purchase_line WHERE date <= '2026-09-30' ORDER BY date, supkey, bill, seq"
    l_rows, n_rows = live.execute(q).fetchall(), new.execute(q).fetchall()
    sep = [r for r in n_rows if r[2] == "2026-09-01"]
    check("every purchase line dated to 30-Sep is byte-for-byte the same in the new build as in the live spine (%d lines; 01-Sep: %d lines, S484's shared numbers among them)"
          % (len(n_rows), len(sep)), l_rows == n_rows and len(sep) > 0, (len(l_rows), len(n_rows)))
    print("   01-Sep lines in the new build: %s" % mask([(r[0], r[1], r[4], r[8]) for r in sep]))
    tied = new.execute("SELECT bill, date, COUNT(*) FROM sp_purchase_line WHERE bill IN (%s) GROUP BY bill, date ORDER BY date" % ",".join("?" * len(TIED_BILLS)), TIED_BILLS).fetchall()
    print("   the four bills of 05/06/07-Oct the piece ties to: %s" % tied)
    check("the four bills Marg printed in part (GPPL2678591 1 line, GPPPL3679039 2, A000207_ 1, YS0706202627 4) carry their lines in the new build",
          {(r[0], r[2]) for r in tied} == {("GPPL2678591", 1), ("GPPPL3679039", 2), ("A000207_", 1), ("YS0706202627", 4)}, tied)
    untied_live = live.execute("SELECT COUNT(*) FROM sp_purchase_line WHERE date >= '2026-10-05'").fetchone()[0]
    print("   purchase lines dated 05-Oct or later: live spine %d, new build %d" % (untied_live, new.execute("SELECT COUNT(*) FROM sp_purchase_line WHERE date >= '2026-10-05'").fetchone()[0]))
    mixed = new.execute("SELECT detail FROM sp_gate WHERE name LIKE 'no item is printed both%'").fetchone()
    print("   the gate's mixed list (keys skipped by the proof): %s" % (mixed[0] if mixed else "?"))
    print("   sp_meta of the new build: %s" % dict(new.execute("SELECT key, value FROM sp_meta WHERE key IN ('built','build_version','checkable','pending')").fetchall()))
    live.close()
    new.close()
    # selftest on the NEW spine folder
    sp_new = os.path.join(a.run, "new", "finance", "spine")
    p = subprocess.run([sys.executable, "-B", os.path.join(sp_new, "selftest_spine.py")], cwd=sp_new, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=900)
    check("selftest_spine.py (the F-536 made-to-fail suite) is green with the new reader and builder", p.returncode == 0 and "SELFTEST OK" in p.stdout, p.stdout.strip().splitlines()[-1:])
    # the greps
    fin_new = os.path.join(a.run, "new", "finance")
    hits = []
    for fn in os.listdir(fin_new):
        if fn.endswith(".py"):
            t = open(os.path.join(fin_new, fn), encoding="utf-8", errors="replace").read()
            for bad in ("_proof_state(", "def _proof_state"):
                if bad in t:
                    hits.append((fn, bad))
    check("grep -n '_proof_state(' and 'def _proof_state' over the NEW finance folder return nothing", not hits, hits)

    # ------------------------------------------------------------------------------------------------------------------------------- 1-3, 6-8
    print("-- 1  the functions on their own copies (NEW), the same on the OLD files (controls)")
    FN = run_probe(a, "fn", "new", Wd, store, secret, pw)
    if not check("the NEW function probe ran to the end and the file carries the S524 proof", FN is not None and FN.get("new")):
        return finish()
    FO = run_probe(a, "fn", "old", Wd, store, secret, pw, extra=dict(W524_LS=json.dumps(FN.get("f843_W") or {})) if FN.get("f843_W") else None)
    if not check("the OLD function probe ran to the end", FO is not None):
        return finish()
    reg = FN["reg"]
    print("   spine built %s; newest sp_close %s; first_at %s; last_at %s" % (FN.get("built"), FN.get("newest_close"), FN.get("first_at"), FN.get("last_at")))
    print("   R %s; after %s; tries %s; reach %s" % (FN.get("R"), FN.get("after"), FN.get("tries"), FN.get("reach")))
    print("   per-key table (key, X, need, marg_move, spine_move, late, ok, why):")
    for t in FN.get("table") or []:
        print("      %-21s %s need %s marg %s spine %s late %s ok %s %s  %s" % (t["key"], t["X"], t["need"], t["marg_move"], t["spine_move"], t["late"], t["ok"], t.get("why") or "", mask(t["items"])))
    for kk, v in (FN.get("moves") or {}).items():
        print("   %-21s moves after R: %s | closings: %s" % (kk, mask(v["moves"]), v["close"]))
    print("   NEW proof of count #%s's orthotic batches: %s" % (FN.get("root"), mask(reg)))
    print("   OLD proof on the same copy (information): %s" % mask(FO.get("reg")))
    tries = FN.get("tries") or []
    if tries:
        check("regression: a clean closing captured after the last entry is in the spine's reach (%s) -> the proof judges (state %s), never 'export'" % ([x[0] for x in tries], reg["state"]),
              reg["state"] in ("done", "wrong") and reg.get("as_after") and reg.get("as_before"), reg)
        check("regression: every wrong row carries ok False, no should, a closing day and words; every proven item a proven_on day; no row both",
              all(r[1] is False and r[2] is None and r[3] and r[4] and r[5] for r in reg["rows"]) and not (set(r[0] for r in reg["rows"]) & set(reg["proven_on"] or {})), reg["rows"])
    else:
        check("regression: no clean after-closing in the spine's reach -> state export with the reason (%s)" % reg.get("why"), reg["state"] == "export" and reg.get("why") in ("no_figure", "pur_behind", "no_closing", "no_before"), reg)
    # F-843
    S = FN.get("f843_setup") or {}
    if FN.get("f843"):
        base_ok = LS_ITEM_L in (reg.get("proven_on") or {})
        base_wrong = LS_ITEM_L in [r[0] for r in reg["rows"]]
        f = FN["f843"]
        check("F-843: one SALE of the LS BELT key (%s) on %s moves Marg AND the spine by -1: the key's verdict is unchanged (proven before %s / after %s; wrong before %s / after %s)"
              % (S.get("key"), S.get("d"), base_ok, LS_ITEM_L in (f.get("proven_on") or {}), base_wrong, LS_ITEM_L in [r[0] for r in f["rows"]]),
              (LS_ITEM_L in (f.get("proven_on") or {})) == base_ok and (LS_ITEM_L in [r[0] for r in f["rows"]]) == base_wrong and f["state"] == reg["state"], f)
        fo = (FO or {}).get("f843") or {}
        orow = [r for r in fo.get("rows") or [] if r[0] == LS_ITEM_L]
        check("control OLD F-843: the same copies -> size L named wrong with a `should` figure (%s)" % mask(orow), bool(orow) and orow[0][1] is False and orow[0][2] is not None, fo)
        fi = FN.get("f843_inv") or {}
        irows = [r for r in fi.get("rows") or [] if r[6] == S.get("key")]
        check("F-843 inverse: +%s on the key's closing at every try (%s; the key's own residue there %s; a figure no late purchase of the key %s explains at any try) -> the key WRONG (%d rows of the key), should absent, closing_day set, moved_hi / need_hi words present, state wrong"
              % (S.get("delta"), S.get("tries"), S.get("res0"), S.get("late"), len(irows)), fi.get("state") == "wrong" and irows and all(r[1] is False and r[2] is None and r[3] and r[4] and r[5] for r in irows) and all(r[7] for r in irows), fi)
    else:
        check("F-843 could not be set up (no try in reach: %s)" % mask(S), False, FN.get("f843_setup"))
    # F-844
    f = FN["f844"]
    fo = FO["f844"]
    print("   NEW F-844: %s" % mask({k: v for k, v in f.items() if k != "card"}))
    print("   OLD F-844: %s" % mask({k: v for k, v in fo.items() if k != "card"}))
    s1 = f.get("s1") or {}
    check("F-844: the copy reads stage A, A.pending == 1 (%s), visible == every orthotic batch, renames_visible True (the 'A verified' event stands)" % s1.get("pending"),
          s1.get("stage") == "A" and s1.get("pending") == 1 and s1.get("visible") == s1.get("ortho") and s1.get("renames_visible") is True, s1)
    ev_new = [e for e in (f.get("ev1") or []) if e not in (f.get("ev0") or [])]
    check("F-844: the first read wrote ONE (A, recheck, 'pending:1') event; the second read wrote none", ev_new == [["A", "recheck", "pending:1", s1.get("proof")]] and f.get("ev2") == f.get("ev1"), (ev_new, f.get("ev2")))
    exp_state = "done" if s1.get("proof") == "done" else s1.get("proof")
    check("F-844: _s521_stage_proof -> %s (%s); the card says the S524 sentence when the proof is done" % (exp_state, (f.get("s521") or {}).get("proof_hi")),
          (f.get("s521") or {}).get("proof_state") == exp_state and ((s1.get("proof") != "done") or ((f.get("s521") or {}).get("proof_hi") == "Orthotic: sab sahi ✓" and NEW_CARD in (f.get("card") or ""))),
          f.get("s521"))
    s2 = f.get("s2") or {}
    ev3 = [e for e in (f.get("ev3") or []) if e not in (f.get("ev1") or [])]
    check("F-844: an un-entered orthotic batch made after the event -> still A, the batch in visible, one recheck event with its key, none on re-read",
          s2.get("stage") == "A" and s2.get("listed") and ev3 == [["A", "recheck", s2.get("new_key"), s2.get("proof") or s1.get("proof")]] or (s2.get("stage") == "A" and s2.get("listed") and len(ev3) == 1 and ev3[0][2] == s2.get("new_key") and f.get("ev4") == f.get("ev3")), (s2, ev3))
    check("F-844: the pending line (%s) cleared by a correcting shelf figure -> pending 0 (%s -> %s)" % (mask(f.get("pending_line")), mask(f.get("pend_before")), mask(f.get("pend_after"))),
          f.get("pend_before") and not f.get("pend_after") and (f.get("s3") or {}).get("pending") == 0, f.get("s3"))
    so1 = fo.get("s1") or {}
    check("control OLD F-844: stage B, no pending key, the new batch not listed, no event written, the card without the S524 sentence",
          so1.get("stage") == "B" and so1.get("pending") is None and not (fo.get("s2") or {}).get("listed") and fo.get("ev4") == fo.get("ev0") and NEW_CARD not in (fo.get("card") or ""), (so1, fo.get("s2")))
    # F-846
    print("-- 5  F-846: the duty's v10 SQL against v9 on a copy")
    p846 = os.path.join(Wd, "w524_f846.db")
    copydb(a.db, p846)
    c = sqlite3.connect(p846)
    dm = json.load(open(a.duty_map, encoding="utf-8"))
    du = [d for d in dm["duties"] if d["id"] == "amir.count_vouchers"][0]
    v10 = du["due_sql"]
    root = c.execute("SELECT MAX(count_id) FROM stock_voucher_line").fetchone()[0]
    q10 = lambda: c.execute(v10).fetchone()                             # noqa: E731
    q9 = lambda: c.execute(V9_SQL).fetchone()                           # noqa: E731
    n0, o0 = q10(), q9()
    add_ortho_batch(c, root)
    n1, o1 = q10(), q9()
    meds = c.execute("SELECT DISTINCT round_no, kind, batch_no FROM stock_voucher_line WHERE count_id=? AND section='Medicines' AND NOT EXISTS "
                     "(SELECT 1 FROM stock_voucher_entered e WHERE e.count_id=stock_voucher_line.count_id AND e.round_no=stock_voucher_line.round_no AND e.kind=stock_voucher_line.kind "
                     "AND e.batch_no=stock_voucher_line.batch_no AND TRIM(COALESCE(e.marg_voucher_no,''))<>'') ORDER BY round_no, kind, batch_no LIMIT 12", (root,)).fetchall()
    rel_at = "2026-10-11T05:00:00"
    ins(c, "stock_stage_event", dict(count_id=root, stage="C", event="release", ref=",".join("%d|%s|%d" % tuple(m) for m in meds), at=rel_at, detail="W524"))
    c.commit()
    n2, o2 = q10(), q9()
    c.close()
    print("   v10: %s -> %s -> %s ; v9: %s -> %s -> %s" % (tuple(n0), tuple(n1), tuple(n2), tuple(o0), tuple(o1), tuple(o2)))
    check("F-846: v10 answers n0=%d on the copy; +1 un-entered orthotic batch -> %d; +a release of %d medicine keys -> %d with since = the release's at" % (n0[0], n1[0], len(meds), n2[0]),
          dm.get("version") == 10 and n1[0] == n0[0] + 1 and n2[0] == n0[0] + 1 + len(meds) and n2[1] == rel_at and len(meds) == 12, (n0, n1, n2))
    check("control F-846: the v9 SQL answers at least v10 at every step and MORE at the first (it counts the unreleased batches: %d vs %d)" % (o1[0], n1[0]),
          o0[0] >= n0[0] and o1[0] >= n1[0] and o2[0] >= n2[0] and o1[0] > n1[0], (o0, o1, o2))
    # F-847
    f = FN["f847"]
    fo = FO["f847"]
    print("   NEW F-847: %s" % mask(f))
    print("   OLD F-847: %s" % mask(fo))
    check("F-847: a closing text of 250 names (built here from the copy's own names) is SHORT by reports_watch (%s) -> skipped, seen_n unchanged; the whole one (%s names) -> counted"
          % (mask(f.get("closing_short")), (f.get("ref") or {}).get("n_names")),
          f.get("closing_short") not in (None, "") and not str(f.get("closing_short")).startswith("ERR") and f.get("seen_short") == f.get("seen0") and (f.get("seen_whole") or [0])[0] == (f.get("seen0") or [0])[0] + 1, f)
    check("control OLD F-847: the short closing is counted as a sighting (seen_n +1)", (fo.get("seen_short") or [0])[0] == (fo.get("seen0") or [0])[0] + 1, fo)
    if FN.get("f847_proof"):
        fp = FN["f847_proof"]
        check("F-847 proof side: the LS BELT key absent from every after-closing -> its items in `unseen` (%d), never in rows; state never 'wrong' for them" % len([u for u in fp["unseen"] if u[0].startswith("L S BELT")]),
              any(u[0] == LS_ITEM_L for u in fp["unseen"]) and not any(r[0] == LS_ITEM_L for r in fp["rows"]) and (fp["state"] == "export" or (fp["state"] == "wrong" and fp["rows"])), fp)
    # F-848
    f = FN["f848"]
    fo = FO["f848"]
    print("   NEW F-848: %s ; OLD: %s" % (f, fo))
    check("F-848: a batch filed at D+1 09:50, Marg's closing of D+1 captured at D+1 09:30 -> counted in (D+1, D+2] (%s), not in (D, D+1] (%s); (D+2, D+3] with no D+3 capture -> the day rule, 0; a window with its first capture missing -> the day rule counts it (%s)"
          % (f.get("w_D1_D2"), f.get("w_D_D1"), f.get("w_missing_day_rule")),
          f.get("w_D_D1") == 0.0 and f.get("w_D1_D2") == -1.0 and f.get("w_D2_D3") == 0.0 and f.get("w_missing_day_rule") == -1.0, f)
    check("control OLD F-848: the day rule puts it in (D, D+1] (%s)" % fo.get("w_D_D1"), fo.get("w_D_D1") == -1.0 and fo.get("w_D1_D2") == 0.0, fo)
    # F-840
    f = FN["f840"]
    fo = FO["f840"]
    print("   NEW F-840: %s" % mask(f))
    print("   OLD F-840: %s" % mask(fo))
    pl = f.get("plain") or {}
    done = reg["state"] == "done"
    check("F-840: section_state's c3 follows the stage proof on the plain copy (proof %s -> c3 %s) and its text names the closing %s" % (reg["state"], pl.get("c3"), reg.get("as_after")),
          pl.get("c3") == done and ((not done) or (str(reg.get("as_after")) in str(pl.get("text")))) and (pl.get("proof") or {}).get("as_after") == (reg.get("as_after") or ""), pl)
    fi = FN.get("f840_inv") or {}
    check("F-840 with the inverse case: c3 False and the text names the key count (%s)" % fi.get("text"), fi.get("c3") is False and "key" in str(fi.get("text")), fi)
    check("F-840 with the voucher lines moved aside: c3 True, 'nothing to prove yet'", (f.get("none") or {}).get("c3") is True and "nothing to prove yet" in str((f.get("none") or {}).get("text")), f.get("none"))
    po_ = fo.get("plain") or {}
    check("control OLD F-840: the old proof judges by the stock_feed figures and does not name the closing the stage proves (%s)" % mask(po_.get("text")),
          po_.get("c3") is not None and str(po_.get("text")) != str(pl.get("text")), po_)

    # ------------------------------------------------------------------------------------------------------------------------------- 4, 10, 11, 12
    print("-- 4  the routes on a copy, signed in through a walk-only portal as amir and as the owner (the door, the board, the home, the hub)")
    AN = run_probe(a, "api", "new", Wd, store, secret, pw)
    AO = run_probe(a, "api", "old", Wd, store, secret, pw)
    if not check("both route probes ran to the end", AN is not None and AO is not None):
        return finish()
    for k in ("board_amir_1", "board_amir_2", "board_owner", "stage_before", "step6_before", "board_amir_3", "stage_after", "step6_after", "post", "hub", "sm_api", "eye"):
        print("   NEW %-13s %s" % (k, mask(AN.get(k))))
    for k in ("board_amir_1", "stage_after", "board_amir_3", "step6_after", "post", "hub"):
        print("   OLD %-13s %s" % (k, mask(AO.get(k))))
    print("   events NEW: %s -> %s -> %s -> %s (end %s)" % (mask(AN["events0"]), mask(AN["events1"]), mask(AN["events2"]), mask(AN["events3"]), mask(AN["events_end"])))
    roles = AN.get("roles") or []
    check("the roles on the copy: 'checker' is not among amir's and is among the owner's (the F-845 check is void otherwise) %s" % roles,
          not any(r[1] == "checker" and r[2] == "amir" for r in roles) and any(r[1] == "checker" and r[2] == "manoj" for r in roles), roles)
    P = AN["post"]
    check("F-845: as amir, a medicine batch (%s, not released) -> 403 not_released; the released orthotic batch -> 200; clear on it -> 200; the owner -> 200 on the medicine batch (and its clear)" % AN.get("med_key"),
          P["amir_med"] == [403, "not_released"] and P["amir_ortho"][0] == 200 and P["amir_ortho_clear"][0] == 200 and P["owner_med"][0] == 200 and P["owner_med_clear"][0] == 200, P)
    check("control OLD F-845: amir -> 200 on the medicine batch", AO["post"]["amir_med"][0] == 200, AO["post"])
    b1, b2 = AN["board_amir_1"], AN["board_amir_2"]
    st0 = AN["stage_before"]
    exp_ps = {"done": "done", "wrong": "wrong", "export": "export"}.get(st0.get("A_proof"))
    check("the board as amir: 200, proof_state %s = the stage proof (%s), renames_ready True (released once, kept), and the owner's board says the same line" % (b1["proof_state"], st0.get("A_proof")),
          b1["code"] == 200 and b1["proof_state"] == exp_ps and b1["renames_ready"] is True and AN["board_owner"]["proof_hi"] == b1["proof_hi"] and AN["board_owner"]["renames_ready"] is True, (b1, AN["board_owner"]))
    check("the first board read wrote one once-only (A, recheck, 'pending:1') event; the second none; the owner's read none",
          len(AN["events1"]) == len(AN["events0"]) + 1 and AN["events1"][-1][:3] == ["A", "recheck", "pending:1"] and AN["events2"] == AN["events1"], (AN["events0"], AN["events1"]))
    s6 = AN["step6_after"]
    sa_ = AN["stage_after"]
    check("staff-eye: with the un-entered orthotic batch the duty is due; Amir's home tile 'Amir ka kaam' shows; his step 6 carries 'Marg sudhar' and 'Orthotic voucher baaki: 1'; his board lists exactly visible (%d)" % len(sa_.get("visible") or []),
          AN["eye"]["first"][0] == 302 and "Amir ka kaam" in AN["eye"]["tiles"] and s6["code"] == 200 and s6["marker"] and any(x.startswith("Orthotic voucher baaki: 1") for x in s6["baaki"])
          and AN["board_amir_3"]["flat"] == sa_.get("visible") and AN["new_key"] in (sa_.get("visible") or []), (AN["eye"]["first"], s6, AN["board_amir_3"]["flat"]))
    eye = AN["eye"]["duties"]
    bad_eye = [d for d in eye if d["tile"] and not d["tile_seen"]] + [d for d in eye if d.get("door_seen") is False] + [d for d in eye if isinstance(d["due_n"], str)]
    cv = [d for d in eye if d["id"] == "amir.count_vouchers"]
    check("staff-eye: every duty of amir on the v10 map (%d): tile on his home, door shows its marker while due (%s); amir.count_vouchers due %s" % (len(eye), ", ".join("%s %s" % (d["id"], d["due_n"]) for d in eye if isinstance(d["due_n"], int) and d["due_n"] > 0), cv[0]["due_n"] if cv else "?"),
          eye and not bad_eye and cv and cv[0]["due_n"] == 1 and cv[0].get("door_seen") is True and AN["eye"]["version"] == 10, bad_eye)
    check("control OLD staff-eye: the new orthotic batch is NOT on his board (stage B hides it) and his step 6 shows no 'Orthotic voucher baaki'",
          AN["new_key"] not in AO["board_amir_3"]["flat"] and not AO["step6_after"]["baaki"], (AO["board_amir_3"]["flat"], AO["step6_after"]))
    H = AN["hub"]
    # the hub was read AFTER the walk's un-entered batch was made: stage A with a voucher open -> 'wait', "Stage A: 7 of 8 entered"
    exp_hub = "wait" if (sa_.get("A_open") or 0) > 0 else {"done": "done", "wrong": "now", "export": "wait"}.get(sa_.get("A_proof"), "wait")
    check("the owner's hub step 7 renders the stage proof: state %s (expected %s: a voucher open %s, proof %s), text %r, rows with why; the page answers 200" % (H["state"], exp_hub, sa_.get("A_open"), sa_.get("A_proof"), H.get("text")),
          H["code"] == 200 and H["state"] == exp_hub and H.get("text") and AN["hub_page"] == 200 and all(r[1] for r in H["rows"])
          and ((sa_.get("A_open") or 0) == 0 or str(H.get("text")).startswith("Stage A:")), H)
    check("the orthotic section (the hub's ortho block and /finance/stockmatch as the owner) renders; its proof condition follows the stage (%s)" % mask(H["ortho_conds"].get("proof")),
          H.get("ortho_ok") is True and AN["sm_page"] == 200 and AN["sm_api"]["code"] == 200 and "proof" in H["ortho_conds"], (AN["sm_page"], AN["sm_api"]))
    check("nothing on any page reads 'hona chahiye': steps 1-7, the board, the hub, the section",
          not AN["steps_hona"] and not b1["hona"] and not AN["board_amir_3"]["hona"] and not H["hona"] and not AN["sm_api"]["hona"] and not s6["hona"], AN["steps_hona"])
    print("   timing (reported, not gated): amir_stage warm %d ms; the board API %d ms (NEW); OLD board %d ms" % (AN["ms_stage_warm"], AN["ms_board"], AO["ms_board"]))
    return finish()


def finish():
    if FAILS:
        print("WALK_S524 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + mask(f)[:240])
        return 1
    print("WALK_S524 GREEN (%d checks)" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
