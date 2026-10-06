#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s488.py -- kit S488_DATES_AND_WAITS: the walk (the brief's section 7), on the server, on scratch copies only.

    python3 -B walk_s488.py --kit DIR --work /tmp/... --fin-new DIR --fin-old DIR --por DIR --db finance.db --adb assets.db --spine spine.db
                            --duty-map DUTY_MAP.json(v8)

  fin-new / fin-old   scratch copies of /root/finance: NEW carries the nine built files, OLD is the box as it is.
  por                 a scratch copy of /root/portal's *.py and tile_grants.json; the walk writes its OWN secret and user store there.
  db / adb / spine    backup-API copies; every probe works on its OWN further copies of them (rule 3); the walk's rows are keyed W488.

Each side runs in its own process ("fn": sections 1-6 by function and by route, header auth; "eye": section 7, signed in through the
portal as each login). Every section's negative control is the same probe on the OLD side. Nothing is imported from inside deploy_kits
(rule 11): rejudge_s488.py is run as a script from a copy in the work folder. No person, phone or real export line is in this file.
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

TAG = "W488JSON "
USERS = {"amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff", "manoj": "doctor"}
HROLE = {"manoj": "doctor", "amir": "staff", "darpan": "staff", "shavez": "manager", "reception": "staff"}
STAFF = ("amir", "darpan", "shavez", "alisha", "shivani", "reception", "bhati", "sukhveer")
NEW_IDS = ("manoj.salt_list", "manoj.item_lists")
N, FAILS = [0], []
PRE = {}


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + mask(str(got))[:900] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def md5b(b):
    return hashlib.md5(b).hexdigest()


def steady(h):
    h = re.sub(r"\b\d{1,2}:\d\d(:\d\d)?\b", "HH:MM", h or "")
    return re.sub(r"\b[0-9a-f]{16,}\b", "HEX", h)


def copydb(src, dst):
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


def spans(h):
    """The visible words of a card, span by span (tags dropped, entities read)."""
    return [_html.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<span[^>]*>(.*?)</span>", h or "", re.S)]


# ============================================================================================================== the "fn" probe (1-6)
def probe_fn():
    FIN, WORK, SIDE, DB0 = (os.environ[k] for k in ("FINDIR", "WORKDIR", "SIDE", "W488_DB0"))
    NEW = SIDE == "new"
    sys.path.insert(0, FIN)
    os.chdir(FIN)
    out = dict(side=SIDE)

    def mk(name):
        p = os.path.join(WORK, "w488_%s.db" % name)
        copydb(DB0, p)
        c = sqlite3.connect(p, timeout=60)
        c.row_factory = sqlite3.Row
        return p, c

    # ---------------------------------------------------------------- copy A: the app's own database for the route checks
    A = os.environ["FINANCE_DB"]
    ca = sqlite3.connect(A, timeout=60)
    ca.row_factory = sqlite3.Row
    D1, D2 = "30-09-2026", "25-10-2026"
    for day, rec, m, e in ((D1, "2026-10-07T01:00:00", 10, 12), (D2, "2026-10-26T09:00:00", 10, 13)):
        ca.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (day, "push_snapshot", "W488 ITEM", m, rec))
        ca.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)",
                   (day, "push_expected base=03-09-2026 pur_to=%s" % D2, "W488 ITEM", e, rec))
    for day, pk, size in ((D1, "1*10", 10), (D2, "1*15", 15)):
        ca.execute("INSERT INTO stock_snapshot (as_on, item, qty, packing, pack_size, loaded_at, source) VALUES (?,?,?,?,?,?,?)",
                   (day, "W488 SNAP", 5, pk, size, "2026-10-26T09:00:00", "W488"))
    for item, fo, diff in (("W488 LOSS IN", "15-10-2030", -3), ("W488 LOSS OUT", "15-12-2030", -4)):
        ca.execute("INSERT INTO stock_diff (count_id, item, found_on, marg_qty, counted_qty, diff, cause) VALUES (?,?,?,?,?,?,?)",
                   (948801, item, fo, 10, 10 + diff, diff, "UNEXPLAINED"))
    ca.commit()
    import finance_app as fa                                            # noqa: E402
    import stock_app as SA                                              # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import shelf_figure as SF                                           # noqa: E402
    import stock_watch as SW                                            # noqa: E402
    import owner_sheets as OSH                                          # noqa: E402
    import reports_tile as RT                                           # noqa: E402
    import item_check as IC                                             # noqa: E402
    import aaj_kaam as AK                                               # noqa: E402
    import owner_console as OC                                          # noqa: E402
    for m in (SA, AD, SF, SW, OSH, RT, IC, AK, OC):
        assert m.__file__.startswith(FIN), m.__file__
    cl = fa.app.test_client()

    def H(u):
        return {"X-Clinic-User": u, "X-Clinic-Role": HROLE[u]}

    def jget(path, u="manoj"):
        r = cl.get(path, headers=H(u))
        return r.status_code, (r.get_json(silent=True) or {})

    # ---------------------------------------------------------------- 1  dates
    s1 = {}
    c, j = jget("/finance/stock/api/now")
    s1["now"] = [c, j.get("as_on")]
    c, j = jget("/finance/stock/api/drift")
    w = [x for x in (j.get("items") or []) if x.get("item") == "W488 ITEM"]
    s1["drift"] = [c, (w[0]["days"] if w else None), [f.get("as_on") for f in (j.get("feeds") or [])[:2]]]
    s1["r_stock"] = (SA._r_stock(ca).get("marg") or {}).get("as_on")
    c, j = jget("/finance/stock/api/losses?from=2030-10-01&to=2030-10-31")
    s1["losses"] = [c, sorted(x.get("item") for x in (j.get("by_item") or []) if str(x.get("item")).startswith("W488")),
                    sorted(x.get("item") for x in (j.get("repeat_offenders") or []) if str(x.get("item")).startswith("W488"))]
    c, j = jget("/finance/darpan/api/pipeline")
    s1["pipeline"] = [c, ((j.get("stock") or {}).get("latest_snapshot") if isinstance(j.get("stock"), dict) else
                          json.dumps(j)[:0] or None), (j.get("stock") or {}).get("snapshots") if isinstance(j.get("stock"), dict) else None]
    if s1["pipeline"][1] is None:                                      # the leg may be wrapped: find it wherever it sits
        blob = json.dumps(j)
        m = re.search(r'"latest_snapshot":\s*"([^"]*)"', blob)
        s1["pipeline"][1] = m.group(1) if m else None

    class NoSpine(object):
        ok = False
    s1["item_info"] = SW.item_info(ca, NoSpine(), "W488 SNAP")
    ca.execute("DELETE FROM stock_item_section")
    ca.commit()
    ci = OSH.consumable_items(ca, limit=5000)
    s1["consumable"] = [len(ci), sorted(x["item"] for x in ci if x["item"].startswith("W488"))]
    # readiness: one copy, its stock_feed emptied; one W488 closing of the day under test; the purchase exports reach it or not
    _p, cr = mk("ready")
    cr.execute("DELETE FROM stock_feed")
    rd = {}
    for day in ("05-11-2030", "25-11-2030"):
        for cover in (False, True):
            cr.execute("DELETE FROM stock_feed")
            cr.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w488%'")
            cr.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (day, "push_snapshot", "W488 ITEM", 3, "2030-11-26T09:00:00"))
            if cover:
                iso = "%s-%s-%s" % (day[6:10], day[3:5], day[0:2])
                cr.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at) VALUES (?,?,?,?,?,?,?)",
                           ("w488%s" % day.replace("-", ""), "ITEMWISE", "W488.XLS", iso[:8] + "01", iso, iso.replace("-", "") + "-090000", iso + "T09:00:00"))
            cr.commit()
            r = SA.readiness(cr)
            rd["%s|%s" % (day[:2], "covered" if cover else "short")] = [x for x in r["warnings"] if x.startswith("The stock figure is for")]
    s1["readiness"] = rd
    cr.close()
    out["s1"] = s1

    # ---------------------------------------------------------------- 2  the filed vouchers
    s2 = {}
    _p, cv = mk("vouch")
    CID = 948802

    def vline(rno, kind, bno, item, ch):
        cv.execute("INSERT INTO stock_voucher_line (count_id, round_no, kind, batch_no, batches_n, line_no, section, item, packing, pack, marg_from, change, "
                   "marg_to, reason, made_by, made_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                   (CID, rno, kind, bno, 1, 1, "Orthotics", item, "1", 1, 0, ch, ch, "W488", "w488", "2031-01-01T09:00:00"))

    def vent(rno, kind, bno, vno, on, at):
        cv.execute("INSERT INTO stock_voucher_entered (count_id, round_no, kind, batch_no, marg_voucher_no, entered_on, by_user, at) VALUES (?,?,?,?,?,?,?,?)",
                   (CID, rno, kind, bno, vno, on, "w488", at))
    vline(1, "RECEIVE", 1, "W488 VITEM", 6)
    vent(1, "RECEIVE", 1, "W488-1", "04-10-2026", "2026-10-04T10:00:00")
    vline(1, "RECEIVE", 2, "W488 VITEM2", 3)
    vent(1, "RECEIVE", 2, "W488-2", "kal", "2026-10-04T11:00:00")
    vline(1, "RECEIVE", 3, "W488 VITEM3", 5)
    vent(1, "RECEIVE", 3, "W488-3", "06-10-2026", "2026-10-06T11:00:00")
    vline(1, "RECEIVE", 4, "W488 VITEM4", 7)
    vent(1, "RECEIVE", 4, "W488-4", "04-10-2026", "2026-10-04T10:10:00")
    vent(1, "RECEIVE", 4, "", "04-10-2026", "2026-10-04T10:20:00")        # its newest row: the number cleared
    vline(1, "RECEIVE", 5, "W488 VITEM5", 2)
    vent(1, "RECEIVE", 5, "W488-5", "2026-10-03", "2026-10-03T12:00:00")
    vent(1, "RECEIVE", 5, "W488-5", "2026-10-03", "2026-10-03T12:05:00")  # entered twice
    cv.commit()
    fv = lambda it: SF.filed_vouchers(cv, it, "2026-10-02", "2026-10-04")
    s2["filed"] = {it: fv(it) for it in ("W488 VITEM", "W488 VITEM2", "W488 VITEM3", "W488 VITEM4", "W488 VITEM5")}

    class FakeSpine(object):
        ok = True

        def __init__(self):
            self.c = sqlite3.connect(":memory:")
            self.c.row_factory = sqlite3.Row
            self.c.execute("CREATE TABLE sp_move (k20 TEXT, kind TEXT, units REAL, date TEXT)")
            self.c.execute("INSERT INTO sp_move VALUES ('W488 VITEM', 'PURCHASE', 6, '2026-10-01')")

        def key(self, n):
            return str(n)[:20]

        def q(self, s, *a):
            return [dict(r) for r in self.c.execute(s, a).fetchall()]
    s2["boundary"] = SF.boundary_purchases(cv, FakeSpine(), "W488 VITEM", "2026-10-03", 10, 16, "2026-10-04", 1)
    # the re-judge's own W488 rows: three closings far ahead, a voucher filed between the first two
    C1, C2, C3 = "2031-03-01", "2031-03-03", "2031-03-05"
    vline(2, "RECEIVE", 1, "W488 G1", 5)
    vline(2, "RECEIVE", 1, "W488 G2", 5)
    vent(2, "RECEIVE", 1, "W488-G", "02-03-2031", "2031-03-02T10:00:00")
    SF_GAP = SF.GAP_DDL
    cv.execute(SF_GAP)

    def gap(as_on, item, flagged, why, move, pack=1):
        cv.execute("INSERT INTO s454_shelf_gap (as_on, item, shelf, marg, gap, marg_move, voucher, base_day, pack, approx, flagged, why, at) "
                   "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", (as_on, item, 0, 0, 0, move, 0, "2026-09-03", pack, 0, flagged, why, as_on + "T10:00:00"))
    why = lambda mv, d: "Marg moved %+g beyond its own sales and purchases on %s with no voucher filed" % (mv, d)
    gap(C1, "W488 G1", 0, None, 0)
    gap(C1, "W488 G2", 0, None, 0)
    gap(C1, "W488 G3", 1, why(1, C1), 1)                                    # flagged at the first closing, no voucher of its own
    gap(C2, "W488 G1", 1, why(5, C2), 5)
    gap(C2, "W488 G2", 1, why(9, C2), 9)
    gap(C2, "W488 G3", 1, why(1, C1), 0.5)                                  # a carried flag of an earlier closing, with a small move
    gap(C3, "W488 G1", 1, why(5, C2), 0)                                    # carries of C2's rows
    gap(C3, "W488 G2", 1, why(9, C2), 0)
    cv.commit()
    s2["old_fv_G1"] = SF.filed_vouchers(cv, "W488 G1", C1, C2)
    cv.close()
    if NEW:
        rj = os.path.join(WORK, "rejudge_s488.py")
        runs = []
        for _i in range(2):
            p = subprocess.run([sys.executable, "-B", rj, "rejudge", "--db", os.path.join(WORK, "w488_vouch.db"), "--fin", FIN],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=600)
            js = [l for l in p.stdout.splitlines() if l.startswith("S488JSON ")]
            runs.append(json.loads(js[-1][9:]) if js else dict(err=p.stdout[-600:]))
        cz = sqlite3.connect(os.path.join(WORK, "w488_vouch.db"))
        s2["rows_after"] = {"%s|%s" % (r[0], r[1]): [r[2], r[3]] for r in cz.execute(
            "SELECT as_on, item, flagged, why FROM s454_shelf_gap WHERE item LIKE 'W488%' ORDER BY as_on, item")}
        cz.close()
        s2["rejudge"] = runs
    out["s2"] = s2

    # ---------------------------------------------------------------- 3  the card
    s3 = {}
    _p, ck = mk("card")
    LAST = "2031-03-10T10:00:00"
    key = (1, "ISSUE", 1)
    ent = {key: ("W488-1", LAST)}
    batches = {key: {"lines": [("W488 P1", -2, 0)]}}

    def feed(day, kind, rec, base="01-01-2031", pur=None, qty=None):
        src = "push_snapshot" if kind == "m" else "push_expected base=%s pur_to=%s" % (base, pur or day)
        ck.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES (?,?,?,?,?)", (day, src, "W488 P1", qty if qty is not None else 10, rec))

    def scen(name, rows, reach=None):
        ck.execute("DELETE FROM stock_feed")
        ck.execute("DELETE FROM purchase_export WHERE md5 LIKE 'w488%'")
        if reach:
            ck.execute("INSERT INTO purchase_export (md5, type, file, period_from, period_to, export_stamp, received_at) VALUES (?,?,?,?,?,?,?)",
                       ("w488reach", "ITEMWISE", "W488.XLS", reach[:8] + "01", reach, reach.replace("-", "") + "-090000", reach + "T09:00:00"))
        for r in rows:
            feed(*r)
        ck.commit()
        SA._S446_PROOF_CACHE.clear()
        res = SA._s446_proof(ck, 948803, [key], ent, batches)
        s3.setdefault("proofs", {})[name] = {k: res.get(k) for k in ("state", "why", "since", "closing_day", "closing_at", "text", "as_before", "as_after")}
        s3.setdefault("keys", {})[name] = sorted(res.keys())
        return res
    BEF = [("08-03-2031", "m", "2031-03-08T22:00:00"), ("08-03-2031", "e", "2031-03-08T22:00:00")]
    P = {}
    P["no_closing"] = scen("no_closing", BEF)
    P["no_figure"] = scen("no_figure", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00"), ("11-03-2031", "m", "2031-03-12T22:30:00")])
    P["pur_behind"] = scen("pur_behind", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00"), ("11-03-2031", "m", "2031-03-12T22:30:00"),
                                                ("11-03-2031", "e", "2031-03-11T11:00:00", "01-01-2031", "10-03-2031")])
    scen("reach_covers", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00"), ("11-03-2031", "e", "2031-03-11T11:00:00", "01-01-2031", "10-03-2031")],
         reach="2031-03-11")
    P["no_before"] = scen("no_before", [("11-03-2031", "m", "2031-03-11T10:31:00"), ("11-03-2031", "e", "2031-03-11T11:00:00")])
    P["rebased"] = scen("rebased", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00"), ("11-03-2031", "e", "2031-03-11T11:00:00", "05-03-2031")])
    scen("later_pairs_no_before", [("11-03-2031", "m", "2031-03-11T10:31:00"), ("12-03-2031", "m", "2031-03-12T10:40:00"),
                                   ("12-03-2031", "e", "2031-03-12T11:00:00")])
    scen("later_pairs_rebased", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00"), ("12-03-2031", "m", "2031-03-12T10:40:00"),
                                       ("12-03-2031", "e", "2031-03-12T11:00:00", "05-03-2031")])
    scen("done", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00", "01-01-2031", None, 8), ("11-03-2031", "e", "2031-03-11T11:00:00")])
    scen("wrong", BEF + [("11-03-2031", "m", "2031-03-11T10:31:00", "01-01-2031", None, 9), ("11-03-2031", "e", "2031-03-11T11:00:00")])
    ck.close()

    def stA(pr):
        return dict(stage="A", count_id=948803, A=dict(total=3, entered=3, open=0, proof=pr, verified_at=None), B={}, C={}, numbers={}, visible=[])

    def stC(pr, today=None):
        return dict(stage="C", count_id=948803, A={}, B=dict(verified_at="2031-01-01T09:00:00"),
                    C=dict(open=0, today=today or [], waiting_export=[dict(at="2031-03-09T09:00:00", keys=[key], proof=pr, verified=False)],
                           wrong=[], unreleased=0, total=3, entered=3, released=3, verified=0, lot_at="2031-03-09T09:00:00"), numbers={}, visible=[])
    WRONG = dict(state="wrong", rows=[dict(item="W488 P1", need=-2, moved=-1, marg=9, should=8, ok=False, keys=["1|ISSUE|1"])], as_before="08-03-2031",
                 as_after="11-03-2031", last_at=LAST, items=1)
    DONE = dict(state="done", rows=[], as_before="08-03-2031", as_after="11-03-2031", last_at=LAST, items=1)
    NOKEY = dict(state="export", rows=[], last_at=LAST, text="")
    cards = {}
    for name, pr in list(P.items()) + [("nokey", NOKEY), ("done", DONE), ("wrong", WRONG)]:
        wA = {"s446": {"stage": stA(pr)}}
        wC = {"s446": {"stage": stC(pr)}}
        cards[name] = dict(A=AD._s446_card(wA), C=AD._s446_card(wC), A_hi=AD._s452_extra_hi(wA), C_hi=AD._s452_extra_hi(wC),
                           A_left=AD._s446_left(wA), C_left=AD._s446_left(wC), C_left_open=AD._s446_left({"s446": {"stage": stC(pr, today=[key])}}))
        # the board's line: _s436_board_extra with the stage given and the S304 proof standing at "now"
        real_stage, real_proof = SA.amir_stage, SA._proof_state
        try:
            for nm2, st in (("A_board", stA(pr)), ("C_board", stC(pr))):
                SA.amir_stage = (lambda con, cid=None, _st=st: _st)
                SA._proof_state = (lambda con, d: dict(state="now", rows=[], agree=0, items=0))
                cx = sqlite3.connect(os.path.join(WORK, "w488_card.db"))
                try:
                    cards[name][nm2] = SA._s436_board_extra(cx, dict(count_id=948803, differences=[], as_on="11-03-2031")).get("proof_hi")
                finally:
                    cx.close()
            # the owner's lines
            for nm2, st in (("A_owner", stA(pr)), ("C_owner", stC(pr))):
                SA.amir_stage = (lambda con, cid=None, _st=st: _st)
                cx = sqlite3.connect(os.path.join(WORK, "w488_card.db"))
                try:
                    cards[name][nm2] = [x["text"] for x in AD._s446_owner_lines(cx) if x.get("target") == "stock"]
                finally:
                    cx.close()
        finally:
            SA.amir_stage, SA._proof_state = real_stage, real_proof
    s3["cards"] = cards
    # the 48-hour line: since 47 h / 48 h ago, stage A and a stage-C lot; the setting moves it
    hrs = {}
    _p, cw = mk("wait")
    real_stage = SA.amir_stage
    try:
        for hh in (47, 48):
            since = (AD._now() - dt.timedelta(hours=hh, minutes=1 if hh == 48 else 0)).strftime("%Y-%m-%dT%H:%M:%S")
            pr = dict(P["no_closing"], since=since)
            for nm2, st in (("A", stA(pr)), ("C", stC(pr))):
                SA.amir_stage = (lambda con, cid=None, _st=st: _st)
                hrs["%s|%d" % (nm2, hh)] = [x["text"] for x in AD._s446_owner_lines(cw) if x.get("cls") == "warn" and "voucher proof has waited" in x["text"]]
        cw.execute("INSERT OR REPLACE INTO setting (key, value, note) VALUES ('amir.proof_wait_hours', '72', 'W488')")
        cw.commit()
        SA.amir_stage = (lambda con, cid=None, _st=stA(pr): _st)
        hrs["A|48|setting72"] = [x["text"] for x in AD._s446_owner_lines(cw) if "voucher proof has waited" in x.get("text", "")]
    finally:
        SA.amir_stage = real_stage
    cw.close()
    s3["hours"] = hrs
    out["s3"] = s3

    # ---------------------------------------------------------------- 4  refusals
    s4 = {}
    _p, cf = mk("refused")
    IST = AD.IST
    cf.execute("CREATE TEMP TABLE mi_file AS SELECT * FROM main.mi_file")    # a TEMP twin: the main table forbids a NULL type; this one does not
    cf.execute("DELETE FROM temp.mi_file")

    def mi(md5, typ, verdict, at, reason="W488 test reason", pcv="REFUSED"):
        cf.execute("INSERT INTO temp.mi_file (md5, type, verdict, pc_verdict, reason, received_at) VALUES (?,?,?,?,?,?)", (md5, typ, verdict, pcv, reason, at))
    mi("w488r1", "W488_REPORT", "REFUSED", "2031-03-10T23:30:00+05:30")
    for i, t in enumerate([None, "", "_UNKNOWN"] * 5):
        mi("w488u%02d" % i, t, "REFUSED", "2031-03-10T%02d:%02d:00+05:30" % (20 + i // 6, (i * 7) % 60), reason="")
    cf.commit()
    real_now = AD._now

    def at(y, mo, d, h, mi_):
        AD._now = (lambda: dt.datetime(y, mo, d, h, mi_, tzinfo=IST))
        try:
            return [x["text"] for x in AD._s444_refused_lines(cf)]
        finally:
            AD._now = real_now
    s4["morning"] = at(2031, 3, 11, 9, 0)
    s4["h35"] = at(2031, 3, 12, 10, 30)
    s4["h37"] = at(2031, 3, 12, 12, 30)
    s4["evening_before"] = at(2031, 3, 10, 23, 45)
    cf.execute("INSERT INTO main.setting (key, value, note) VALUES ('amir.refused_keep_hours', '40', 'W488') ON CONFLICT(key) DO UPDATE SET value='40'")
    cf.commit()
    s4["h37_setting40"] = at(2031, 3, 12, 12, 30)
    mi("w488v1", "W488_REPORT", "VERIFIED", "2031-03-11T08:00:00+05:30", reason="", pcv="")
    cf.commit()
    s4["after_verified"] = at(2031, 3, 11, 9, 0)
    cf.close()
    out["s4"] = s4

    # ---------------------------------------------------------------- 5  the lists
    s5 = {}
    m8 = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    sql = {d["id"]: d["due_sql"] for d in m8["duties"] if d["id"] in NEW_IDS}
    pl, cl5 = mk("lists")
    s5["due0"] = {k: tuple(cl5.execute(v).fetchone()) if v else None for k, v in sql.items()}
    today = dt.date.today()

    def move(typ, days):
        cl5.execute("UPDATE mi_file SET date_from=?, received_at=? WHERE type=? AND verdict='VERIFIED'",
                    ((today - dt.timedelta(days=days)).isoformat(), (today - dt.timedelta(days=days)).isoformat() + "T09:00:00+05:30", typ))
    move("SALT_WISE_ITEM_LIST", 9)
    move("ITEM_MASTER", 36)
    cl5.execute("DELETE FROM mi_file WHERE type='CATEGORY_WISE_ITEM_LIST' AND verdict='VERIFIED'")
    cl5.commit()
    s5["due1"] = {k: tuple(cl5.execute(v).fetchone()) for k, v in sql.items()}
    os.environ["DUTY_MAP_JSON"] = os.environ["DUTY_MAP"]
    s5["lines8"] = [x["text"] for x in AD._s444_duty_lines(cl5) if x.get("duty") in NEW_IDS]
    os.environ["DUTY_MAP_JSON"] = os.environ["MAP7"]
    s5["lines7"] = [x["text"] for x in AD._s444_duty_lines(cl5) if x.get("duty") in NEW_IDS]
    cl5.execute("DELETE FROM mi_file WHERE type='SALT_WISE_ITEM_LIST' AND verdict='VERIFIED'")
    cl5.commit()
    os.environ["DUTY_MAP_JSON"] = os.environ["DUTY_MAP"]
    s5["salt_never"] = [tuple(cl5.execute(sql["manoj.salt_list"]).fetchone()), [x["text"] for x in AD._s444_duty_lines(cl5) if x.get("duty") == "manoj.salt_list"]]
    cl5.close()
    _p, co = mk("owner_lists")
    s5["ol_default"] = RT.owner_lists(co, today)
    co.execute("INSERT INTO setting (key, value, note) VALUES ('owner.salt_list_days', '3', 'W488') ON CONFLICT(key) DO UPDATE SET value='3'")
    co.execute("INSERT INTO setting (key, value, note) VALUES ('owner.item_lists_days', '9x', 'W488') ON CONFLICT(key) DO UPDATE SET value='9x'")
    co.commit()
    s5["ol_set"] = [(x["key"], x["limit"]) for x in RT.owner_lists(co, today)]
    co.close()
    mem = sqlite3.connect(":memory:")
    mem.row_factory = sqlite3.Row
    mem.execute(sqlite3.connect("file:%s?mode=ro" % DB0, uri=True).execute("SELECT sql FROM sqlite_master WHERE name='mi_file'").fetchone()[0])
    try:
        s5["ol_nosetting"] = [(x["key"], x["limit"]) for x in RT.owner_lists(mem, today)]
    except Exception as e:                                              # noqa: BLE001
        s5["ol_nosetting"] = "RAISED %s" % type(e).__name__
    # the map in its two readers, and every staff login's list cut with v7 and with v8
    AK.DUTY_MAP = os.environ["DUTY_MAP"]
    m, x = AK.load_defs()
    s5["load_defs"] = [m.get("_err"), m.get("version"), x.get("_err")]
    OC.DUTY_MAP = os.environ["DUTY_MAP"]
    try:
        rdu = OC.read_duties(DB0)                                       # the copy as it is (the lists' copy above was moved on purpose)
        s5["console"] = [rdu.get("version"), {d["id"]: [d["n"], d["err"]] for d in rdu["duties"] if d["id"] in NEW_IDS}, sum(1 for d in rdu["duties"] if d["err"])]
    except Exception as e:                                              # noqa: BLE001
        s5["console"] = "RAISED %s: %s" % (type(e).__name__, e)
    now = dt.datetime.now().replace(microsecond=0)
    cuts = {}
    for tag, path in (("v7", os.environ["MAP7"]), ("v8", os.environ["DUTY_MAP"])):
        AK.DUTY_MAP = path
        allp = AK.build_all(DB0, now=now)
        cuts[tag] = {lg: json.dumps(AK.list_for(allp, lg), sort_keys=True, default=str) for lg in STAFF + ("manoj",)}
        cuts[tag + "_manoj_ids"] = sorted(i["id"] for k, v in AK.list_for(allp, "manoj")["sections"].items() for i in v)
    s5["cuts_equal"] = {lg: cuts["v7"][lg] == cuts["v8"][lg] for lg in STAFF}
    s5["manoj_gains"] = sorted(set(cuts["v8_manoj_ids"]) - set(cuts["v7_manoj_ids"]))
    out["s5"] = s5

    # ---------------------------------------------------------------- 6  the strike
    s6 = {}
    _p, cs = mk("strike")
    cs.execute("INSERT INTO purchase_bill (id, supplier_norm, supplier, bill_no, bill_date, month, amount_p) VALUES (948806,'W488 SUPPLIER','W488 SUPPLIER',"
               "'W488-1','2031-03-01','2031-03',5000)")
    cs.commit()
    marg = {"item": "W488 ALPHA TABLET"}
    asset = sqlite3.connect(":memory:")
    asset.execute("CREATE TABLE bill_items (id INTEGER PRIMARY KEY, bill_id INTEGER, item_name TEXT, quantity REAL, rate REAL)")
    asset.execute("INSERT INTO bill_items (bill_id, item_name, quantity, rate) VALUES (948807, 'W488 ALPHA TAB', 10, 5.0)")

    class KeepOpen(object):                                             # learn() closes the asset connection: hand it a wrapper
        def __init__(self, c):
            self.c = c

        def execute(self, *a):
            return self.c.execute(*a)

        def cursor(self):
            return self.c.cursor()

        def close(self):
            pass

    class FakePA(object):
        EFF_LINE = "1=1"

        @staticmethod
        def _assets_con():
            return KeepOpen(asset)

    class FakeSR(object):
        @staticmethod
        def asset_scans(con):
            return {948807: dict(id=948807)}

        @staticmethod
        def Ctx(con):
            return None

        @staticmethod
        def links(con):
            return {948806: dict(scan=948807)}

        @staticmethod
        def agree(cx, s, b):
            return True

        @staticmethod
        def verified(x):
            return True
    real = (IC._pa, IC._sr, IC.marg_lines)
    IC._pa, IC._sr = (lambda: FakePA), (lambda: FakeSR)
    IC.marg_lines = lambda con, b: [dict(item=marg["item"], qty=10, rate_p=500, line_type="BILLITEMWISE", source_md5="w488")]
    bill = dict(supplier_norm="W488 SUPPLIER")
    SN, NM = "W488 SUPPLIER", "W488 ALPHA TAB"
    ll = lambda: (IC.learnt_line(cs, bill, NM, [dict(item="W488 ALPHA TABLET"), dict(item="W488 ALPHA FORTE")])[0] or {}).get("item")
    try:
        s6["learn1"] = [x["marg_item"] for x in IC.learn(cs)]
        s6["line1"] = ll()
        if NEW:
            s6["strike1"] = IC.strike(cs, SN, NM, "manoj")
            s6["line_after_strike"] = ll()
            s6["learn_again"] = [x["marg_item"] for x in IC.learn(cs)]
            s6["line_after_learn"] = ll()
            marg["item"] = "W488 ALPHA FORTE"
            s6["learn_other"] = [x["marg_item"] for x in IC.learn(cs)]
            s6["line_other"] = ll()
            s6["strike2"] = IC.strike(cs, SN, NM, "manoj")
            marg["item"] = "W488 ALPHA TABLET"
            s6["learn_t"] = [x["marg_item"] for x in IC.learn(cs)]
            marg["item"] = "W488 ALPHA FORTE"
            s6["learn_f"] = [x["marg_item"] for x in IC.learn(cs)]
            s6["struck"] = [x["marg_item"] for x in IC.struck(cs)]
            s6["back_t"] = IC.unstrike(cs, SN, NM, "W488 ALPHA TABLET")
            s6["line_back"] = ll()
            s6["back_f"] = IC.unstrike(cs, SN, NM, "W488 ALPHA FORTE")
            s6["learnt_has_scan_norm"] = all("scan_norm" in x for x in IC.learnt(cs))
        else:                                                           # the OLD design: the only way back is a delete -- and learn brings it back
            cs.execute("DELETE FROM s454_item_name WHERE supplier_norm=? AND scan_norm=?", (SN, NM))
            cs.commit()
            s6["line_after_delete"] = ll()
            s6["learn_again"] = [x["marg_item"] for x in IC.learn(cs)]
            s6["line_after_learn"] = ll()
    finally:
        IC._pa, IC._sr, IC.marg_lines = real
    cs.close()
    # the route and the page, on the app's own copy (A): a W488 learnt name
    IC.ensure(ca)
    ca.execute("INSERT OR REPLACE INTO s454_item_name (supplier_norm, scan_norm, scan_name, marg_item, bill_id, asset_bill_id, learnt_at) VALUES "
               "('W488 SUPPLIER','W488 BETA CAP','W488 BETA CAP','W488 BETA CAPSULE',NULL,NULL,'2031-03-01T09:00:00')")
    ca.commit()
    body = dict(supplier_norm="W488 SUPPLIER", scan_norm="W488 BETA CAP", marg_item="W488 BETA CAPSULE", do="strike")
    r = cl.post("/finance/purchase/api/items/strike", json=body, headers=H("amir"))
    s6["route_amir"] = r.status_code
    r = cl.post("/finance/purchase/api/items/strike", json=body, headers=H("manoj"))
    s6["route_manoj"] = [r.status_code, (r.get_json(silent=True) or {}).get("ok")]
    pg = cl.get("/finance/purchase/page/items", headers=H("manoj")).get_data(as_text=True)
    s6["page"] = dict(wrong=pg.count(">Wrong</button>"), struck=bool(re.search(r"<summary>Struck: \d+</summary>", pg)),
                      put_back=pg.count(">Put back</button>"), sentence="Tap Wrong on a name that is not the same item" in pg, js="s488strike" in pg,
                      learnt_n=len(IC.learnt(ca)) if NEW else None)
    r = cl.post("/finance/purchase/api/items/strike", json=dict(body, do="back"), headers=H("manoj"))
    s6["route_back"] = [r.status_code, (r.get_json(silent=True) or {}).get("ok")]
    ca.close()
    out["s6"] = s6
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the "eye" probe (7)
def probe_eye():
    FIN, POR, DB, SIDE = (os.environ[k] for k in ("FINDIR", "PORDIR", "FINANCE_DB", "SIDE"))
    for p in (POR, FIN):
        sys.path.insert(0, p)
    os.chdir(FIN)
    import finance_app as fa                                            # noqa: E402
    import portal as po                                                 # noqa: E402
    import amir_day as AD                                               # noqa: E402
    import stock_app as SA                                              # noqa: E402
    assert AD.__file__.startswith(FIN) and SA.__file__.startswith(FIN)
    BASE = "https://followup.dr-manoj.in"
    fc = fa.app.test_client(use_cookies=False)
    pc = po.app.test_client(use_cookies=False)
    pw = json.loads(os.environ["W488J"])["pw"]
    dm = json.load(open(os.environ["DUTY_MAP"], encoding="utf-8"))
    out = dict(side=SIDE)

    def page(path, ck):
        body, code = "", 0
        for _hop in range(4):
            rr2 = fc.get(path, base_url=BASE, headers={"Cookie": ck})
            code = rr2.status_code
            if code in (301, 302, 303) and rr2.headers.get("Location", "").replace(BASE, "").startswith("/finance/"):
                path = rr2.headers["Location"].replace(BASE, "")
                continue
            body = rr2.get_data(as_text=True)
            break
        return code, body
    EXTRA = {"amir": ["/finance/amir", "/finance/amir/step/6", "/finance/amir/step/7", "/finance/stock/api/pad/amir/1"],
             "manoj": ["/finance/stock/api/now", "/finance/stock/api/readiness", "/finance/stock/api/drift", "/finance/darpan/api/pipeline",
                       "/finance/purchase/page/items", "/finance/amir/day"],
             "darpan": [], "shavez": [], "reception": []}
    cookies = {}

    def sweep(tag):
        ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
        eye = {}
        for who in USERS:
            if who not in cookies:
                r = pc.post("/portal/login", base_url=BASE, data={"user": who, "password": pw[who]})
                m = re.search(r"clinic_sso=([^;]+)", " ".join(r.headers.getlist("Set-Cookie")))
                cookies[who] = (m.group(1) if m else "")
            tok = cookies[who]
            ck = "clinic_sso=" + tok
            r = pc.get("/portal?all=1", base_url=BASE, headers={"Cookie": ck})
            home = r.get_data(as_text=True)
            seen = [_html.unescape(t) for t in re.findall(r'<div class="nm">([^<]+)</div>', home)]
            pages = {"home": md5b(steady(home.replace(tok, "TOKEN")).encode())}
            texts = {}
            rows, doors = [], set(EXTRA[who])
            mine = {who, (dm.get("shared") or {}).get(who)}
            for du in dm.get("duties") or []:
                if du.get("person") not in mine:
                    continue
                row = {"id": du.get("id"), "tile": du.get("tile"), "tile_seen": (du.get("tile") in seen) if du.get("tile") else None, "door": du.get("door")}
                q = str(du.get("due_sql") or "").strip().rstrip(";")
                n = None
                if q:
                    try:
                        rr = ro.execute(q).fetchone()
                        n = int((rr[0] if rr else 0) or 0)
                        row["since"] = rr[1] if rr is not None and len(rr) > 1 else None
                    except Exception as e:                              # noqa: BLE001
                        n = "ERR " + str(e)[:80]
                row["due_n"] = n
                door, mark = du.get("door"), du.get("door_marker")
                if door and str(door).startswith("/finance/"):
                    doors.add(str(door))
                    if mark and isinstance(n, int) and n > 0:
                        body = page(str(door), ck)[1]
                        row["door_seen"] = (mark in body) or (mark in _html.unescape(body))
                rows.append(row)
            for d in sorted(doors):
                code, body = page(d, ck)
                pages[d] = "%s %s" % (code, md5b(steady(body.replace(tok, "TOKEN")).encode()))
                if d in ("/finance/amir", "/finance/amir/step/6", "/finance/amir/step/7", "/finance/amir/day"):
                    texts[d] = [x for x in spans(body) if x][:80]
                if d == "/finance/stock/api/pad/amir/1":
                    try:
                        texts[d] = [(json.loads(body) or {}).get("proof_hi")]
                    except ValueError:
                        texts[d] = None
                if d == "/finance/stock/api/now":
                    try:
                        texts[d] = [code, (json.loads(body) or {}).get("as_on")]
                    except ValueError:
                        texts[d] = [code, None]
            eye[who] = dict(status=r.status_code, n_tiles=len(seen), duties=rows, pages=pages, texts=texts)
        try:
            cx = sqlite3.connect(DB, timeout=60)
            eye["_needs_you"] = [x.get("text") for x in AD.needs_you_lines(cx)]
            cx.close()
        except Exception as e:                                          # noqa: BLE001
            eye["_needs_you"] = "RAISED %s" % e
        ro.close()
        out[tag] = eye
    # the live copy, as it is (NEW: re-judged on its own copy first, by the installer's own script)
    sweep("as_is")
    ro = sqlite3.connect("file:%s?mode=ro" % DB, uri=True)
    days = sorted({r[0] for r in ro.execute("SELECT DISTINCT as_on FROM stock_feed")}, key=lambda s: s[6:10] + s[3:5] + s[0:2])
    out["newest_by_date"] = days[-1] if days else None
    ro.close()
    # a W488 state where the orthotic proof waits: the closings after the vouchers are set aside on this copy, and one W488 Marg push of a
    # later day arrives with no figure of ours for it
    cx = sqlite3.connect(DB, timeout=60)
    last = cx.execute("SELECT MAX(at) FROM stock_voucher_entered").fetchone()[0] or ""
    lk = last[:10].replace("-", "")
    gone = [r[0] for r in cx.execute("SELECT DISTINCT as_on FROM stock_feed") if (r[0][6:10] + r[0][3:5] + r[0][0:2]) >= lk]
    for d in gone:
        cx.execute("DELETE FROM stock_feed WHERE as_on=?", (d,))
    cx.execute("INSERT INTO stock_feed (as_on, source, item, qty, received_at) VALUES ('06-10-2026', 'push_snapshot', 'W488 ITEM', 1, '2026-10-06T23:59:00')")
    cx.commit()
    cx.close()
    out["set_aside"] = gone
    SA._S446_PROOF_CACHE.clear()
    sweep("waiting")
    print(TAG + json.dumps(out, default=str))


# ============================================================================================================== the walk
def main():
    if len(sys.argv) >= 2 and sys.argv[1] in ("--probe-fn", "--probe-eye"):
        return probe_fn() if sys.argv[1] == "--probe-fn" else probe_eye()
    ap = argparse.ArgumentParser()
    for k in ("--kit", "--work", "--fin-new", "--fin-old", "--por", "--db", "--adb", "--spine", "--duty-map"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/") and os.path.abspath(a.por).startswith("/tmp/"), "refusing a non-scratch path: %s" % W
    os.makedirs(W)
    # the v7 map, made back from v8 by taking out exactly what S488 added -- it must read back as the pinned v7 bytes
    m8raw = open(a.duty_map, "rb").read()
    m8 = json.loads(m8raw.decode("utf-8"))
    m7 = dict(m8, version=7, kit="S485_DARPAN_ORDER_TAB", duties=[d for d in m8["duties"] if d["id"] not in NEW_IDS],
              _note=m8["_note"].split(" S488 (06-Oct-2026", 1)[0])
    m7raw = (json.dumps(m7, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
    map7 = os.path.join(W, "DUTY_MAP_v7.json")
    open(map7, "wb").write(m7raw)
    if not check("the v8 map less S488's two duties reads back as the v7 map byte for byte (md5 %s = the brief's pin 1595520d)" % md5b(m7raw)[:8],
                 md5b(m7raw) == "1595520d9c287efc6ecdcd16310041ae" and m8["version"] == 8 and len(m8["duties"]) == len(m7["duties"]) + 2):
        return finish()
    shutil.copy(os.path.join(a.kit, "rejudge_s488.py"), os.path.join(W, "rejudge_s488.py"))
    # the walk's own sign-in: a random secret and its own user store, in the scratch portal folder
    secret = secrets.token_hex(32)
    pw = {u: secrets.token_urlsafe(12) for u in USERS}
    with open(os.path.join(a.por, "portal_config.py"), "w") as fh:
        fh.write("# W488 walk only\nCLINIC_SSO_SECRET = %r\nPORTAL_PIN_HASH = ''\nPORTAL_PIN_SALT = ''\nPORTAL_TOKEN_SEED = %r\n" % (secret, secrets.token_hex(16)))
    sys.path.insert(0, a.por)
    import clinic_users                                                 # noqa: E402
    store = os.path.join(a.por, "clinic_users.json")
    if os.path.exists(store):
        os.remove(store)
    try:
        clinic_users.add_role(store, "staff")
    except ValueError:
        pass
    for u, role in USERS.items():
        clinic_users.add_user(store, u, role, pw[u])

    def run(mode, side, fin):
        wd = os.path.join(W, "%s_%s" % (mode, side))
        os.makedirs(os.path.join(wd, "nosso"))
        os.makedirs(os.path.join(wd, "nomarg"))
        dbp, adbp, spp = [os.path.join(wd, "w488_%s.db" % x) for x in ("app", "assets", "spine")]
        copydb(a.db, dbp)
        copydb(a.adb, adbp)
        copydb(a.spine, spp)
        if mode == "fn":
            shutil.copy(os.path.join(W, "rejudge_s488.py"), os.path.join(wd, "rejudge_s488.py"))
        if mode == "eye" and side == "new":                             # NEW: the re-judge the installer makes, on this copy
            p = subprocess.run([sys.executable, "-B", os.path.join(W, "rejudge_s488.py"), "rejudge", "--db", dbp, "--fin", fin],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=600, env=dict(os.environ, SPINE_DB=spp))
            print("   (eye, NEW copy) " + " | ".join(l for l in p.stdout.splitlines() if l.startswith("closing")))
        env = dict(os.environ, SIDE=side, FINDIR=fin, PORDIR=a.por, WORKDIR=wd, FINANCE_DB=dbp, ASSETS_DB=adbp, SPINE_DB=spp, W488_DB0=a.db,
                   FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=(a.por if mode == "eye" else os.path.join(wd, "nosso")), CLINIC_PORTAL_DIR=a.por,
                   CLINIC_USERS_FILE=store, TILE_GRANTS_FILE=os.path.join(a.por, "tile_grants.json"), CLINIC_SSO_SECRET=secret,
                   DUTY_MAP=a.duty_map, DUTY_MAP_JSON=a.duty_map, MAP7=map7, W488J=json.dumps(dict(pw=pw)), MARG_INGEST_DIR=os.path.join(wd, "nomarg"),
                   RING_PORTAL_DIR=os.path.join(wd, "nosso"), ORDER_PUSH_STUB=os.path.join(wd, "pushes.jsonl"),
                   ATT_PUNCH_CSV=os.path.join(wd, "no_punches.csv"), SR_DB_PATH=os.path.join(wd, "no_staff_register.db"),
                   CONSOLE_SNAPSHOT=os.path.join(wd, "console_reading.dat"), CONSOLE_BUILD_LOG=os.path.join(wd, "console_build.log"))
        for k in ("SARVAM_API_KEY", "ORDER_TICK", "ORDER_TODAY", "ORDER_CLOCK", "FINANCE_MARG_TOKEN", "FINANCE_DEV_USER", "FINANCE_DEV_ROLE", "FINANCE_CRON_TOKEN"):
            env.pop(k, None)
        p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe-" + mode], env=env, cwd=fin, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, universal_newlines=True, timeout=2400)
        js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
        if not js:
            print("-- the %s %s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
            for l in p.stdout.splitlines()[-30:]:
                print("   " + mask(l)[:300])
            return None
        return json.loads(js[-1][len(TAG):])
    NW, OL = run("fn", "new", a.fin_new), run("fn", "old", a.fin_old)
    if not check("both function probes ran to the end (NEW = the box + S488, OLD = the box as it is), each on its own copies", NW is not None and OL is not None):
        return finish()

    # ------------------------------------------------------------------------------------------------------------------------------- 1
    print("-- 1  dates as dates (F-753)")
    n1, o1 = NW["s1"], OL["s1"]
    check("api_now with W488 closings of 30-09-2026 and 25-10-2026: NEW answers %s; control OLD answers %s" % (n1["now"][1], o1["now"][1]),
          n1["now"] == [200, "25-10-2026"] and o1["now"] == [200, "30-09-2026"])
    check("_r_stock (the readiness line 'Marg's closing stock: as on ...'): NEW %s; control OLD %s" % (n1["r_stock"], o1["r_stock"]),
          n1["r_stock"] == "25-10-2026" and o1["r_stock"] == "30-09-2026")
    check("api_drift: the W488 item's days end on the October day (NEW %s), its feeds list begins with it (NEW %s); control OLD %s / %s"
          % (n1["drift"][1], n1["drift"][2], o1["drift"][1], o1["drift"][2]),
          n1["drift"][1] == ["30-09-2026", "25-10-2026"] and n1["drift"][2][0] == "25-10-2026"
          and o1["drift"][1] == ["25-10-2026", "30-09-2026"] and o1["drift"][2][0] == "30-09-2026")
    nr, orr = n1["readiness"], o1["readiness"]
    check("readiness, NEW: warns when the stock day is past the purchase exports' reach and is silent when the reach covers it, on the 5th "
          "and on the 25th: %s" % {k: bool(v) for k, v in sorted(nr.items())},
          bool(nr["05|short"]) and not nr["05|covered"] and bool(nr["25|short"]) and not nr["25|covered"] and "05-11-2030" in nr["05|short"][0], nr)
    check("control OLD: silent on the 5th whatever the reach, warning on the 25th whatever the reach: %s" % {k: bool(v) for k, v in sorted(orr.items())},
          not orr["05|short"] and not orr["05|covered"] and bool(orr["25|short"]) and bool(orr["25|covered"]))
    check("api_losses with ISO from/to (October 2030): NEW returns the W488 loss inside the range and not the one outside (%s); control OLD %s"
          % (n1["losses"][1], o1["losses"][1]), n1["losses"][0] == 200 and n1["losses"][1] == ["W488 LOSS IN"] and o1["losses"][1] == [])
    check("darpan_app's pipeline leg: the newest snapshot NEW %s; control OLD %s" % (n1["pipeline"][1], o1["pipeline"][1]),
          n1["pipeline"][0] == 200 and n1["pipeline"][1] == "25-10-2026" and o1["pipeline"][1] == "30-09-2026", (n1["pipeline"], o1["pipeline"]))
    check("stock_watch.item_info (no spine): the October snapshot row, packing %s (NEW); control OLD %s" % (n1["item_info"].get("packing"), o1["item_info"].get("packing")),
          n1["item_info"].get("packing") == "1*15" and n1["item_info"].get("pack") == 15 and o1["item_info"].get("packing") == "1*10")
    check("owner_sheets.consumable_items with stock_item_section emptied: NEW reads the October snapshot (%d item(s): %s); control OLD the "
          "September one (%d items)" % (n1["consumable"][0], n1["consumable"][1], o1["consumable"][0]),
          n1["consumable"] == [1, ["W488 SNAP"]] and o1["consumable"][0] > 1)
    # the text check: each OLD statement is absent from the NEW file (and present in the OLD one)
    OLDS = {"stock_app.py": ["for (as_on, item) in sorted(byday):", "ORDER BY as_on DESC, source", "if cur is None or (as_on, v[\"received_at\"]) > (cur[\"as_on\"],",
                             "stk[\"marg\"][\"as_on\"] > pur[\"bill_date\"]", "days = sorted({d for (d, k) in latest})\n", "AND found_on BETWEEN ? AND ?",
                             "WHERE found_on BETWEEN ? AND ?"],
            "darpan_app.py": ["SELECT MAX(as_on) d, COUNT(DISTINCT as_on) n FROM"],
            "owner_sheets.py": ["SELECT MAX(as_on) AS a FROM stock_snapshot"],
            "stock_watch.py": ["FROM stock_snapshot WHERE item=? ORDER BY as_on DESC LIMIT 1"],
            "shelf_figure.py": ["e.entered_on>? AND e.entered_on<=?"]}
    bad = []
    for f, sts in OLDS.items():
        tn, to = open(os.path.join(a.fin_new, f), encoding="utf-8").read(), open(os.path.join(a.fin_old, f), encoding="utf-8").read()
        bad += ["%s: %s" % (f, s[:50]) for s in sts if s in tn or s not in to]
    check("text check: each OLD statement of A.1-A.10 (%d) is in the OLD file and absent from the NEW one" % sum(len(v) for v in OLDS.values()), not bad, bad)

    # ------------------------------------------------------------------------------------------------------------------------------- 2
    print("-- 2  the filed vouchers (F-754)")
    n2, o2 = NW["s2"], OL["s2"]
    f = n2["filed"]
    check("filed_vouchers(item, 2026-10-02, 2026-10-04): a batch entered 04-10-2026 -> %g (control OLD %g); free-text entered_on falls back to "
          "the day of `at` -> %g; a day outside the window -> %g; a batch whose newest row has an empty number -> %g; entered twice -> counted once %g"
          % (f["W488 VITEM"], o2["filed"]["W488 VITEM"], f["W488 VITEM2"], f["W488 VITEM3"], f["W488 VITEM4"], f["W488 VITEM5"]),
          f == {"W488 VITEM": 6, "W488 VITEM2": 3, "W488 VITEM3": 0, "W488 VITEM4": 0, "W488 VITEM5": 2} and o2["filed"]["W488 VITEM"] == 0
          and o2["filed"]["W488 VITEM2"] == 0, (f, o2["filed"]))
    check("boundary_purchases for a W488 item with a filed RECEIVE voucher and a purchase two days before the base day: NEW %g; control OLD %g "
          "(the voucher's gain mistaken for a late-dated purchase)" % (n2["boundary"], o2["boundary"]), n2["boundary"] == 0 and o2["boundary"] == 6)
    rj = n2.get("rejudge") or [{}, {}]
    r1, r2 = rj[0], rj[1]
    print("   re-judge on the copy (first run): flagged before %s -> after %s; items with a filed voucher in the window %s; cleared by pass 1 / 2 %s"
          % (r1.get("flagged_before"), r1.get("flagged_after"), r1.get("items_with_voucher"), r1.get("by_pass")))
    ra = n2.get("rows_after") or {}
    g = lambda d, it: (ra.get("%s|%s" % (d, it)) or [None, None])
    check("W488 rows: a first-flagged row its voucher explains is cleared (G1 at 03-03: %s); one it does not explain stays (G2: %s); a carried "
          "flag of an earlier closing with a small move is NOT cleared by pass 1 (G3: %s); the carry of a cleared row is cleared by pass 2 "
          "(G1 at 05-03: %s) and the carry of an uncleared one stays (G2 at 05-03: %s)"
          % (g("2031-03-03", "W488 G1")[0], g("2031-03-03", "W488 G2")[0], g("2031-03-03", "W488 G3")[0], g("2031-03-05", "W488 G1")[0], g("2031-03-05", "W488 G2")[0]),
          g("2031-03-03", "W488 G1") == [0, "explained by the vouchers filed (re-judged S488)"] and g("2031-03-03", "W488 G2")[0] == 1
          and g("2031-03-03", "W488 G3")[0] == 1 and g("2031-03-05", "W488 G1") == [0, "explained by the vouchers filed (re-judged S488)"]
          and g("2031-03-05", "W488 G2")[0] == 1 and g("2031-03-01", "W488 G3")[0] == 1, ra)
    check("a second run writes nothing (written %s; flagged per closing the same: %s)" % (r2.get("written"), r2.get("flagged_after")),
          r2.get("written") == 0 and r2.get("flagged_after") == r1.get("flagged_after") and r1.get("written", 0) > 0)
    check("control OLD: its filed_vouchers over (01-03, 03-03] for G1 is %g -- |5 - %g| >= 1, so the OLD rule would clear nothing" % (o2["old_fv_G1"], o2["old_fv_G1"]),
          o2["old_fv_G1"] == 0 and n2["old_fv_G1"] == 5)

    # ------------------------------------------------------------------------------------------------------------------------------- 3
    print("-- 3  the card (B)")
    pn, po_ = NW["s3"]["proofs"], OL["s3"]["proofs"]
    want = {"no_closing": ("no_closing", None, None), "no_figure": ("no_figure", "11-03-2031", "2031-03-11T10:31:00"),
            "pur_behind": ("pur_behind", "11-03-2031", "2031-03-11T10:31:00"), "reach_covers": ("no_figure", "11-03-2031", "2031-03-11T10:31:00"),
            "no_before": ("no_before", "11-03-2031", "2031-03-11T10:31:00"), "rebased": ("rebased", "11-03-2031", "2031-03-11T10:31:00"),
            "later_pairs_no_before": ("no_before", "12-03-2031", "2031-03-12T10:40:00"), "later_pairs_rebased": ("rebased", "12-03-2031", "2031-03-12T10:40:00")}
    got = {k: (pn[k]["why"], pn[k]["closing_day"], pn[k]["closing_at"]) for k in want}
    check("_s446_proof on W488 feeds: why / closing_day / closing_at per state %s (the earliest push, with a 22:30 re-push present)" % got,
          got == {k: tuple(v) for k, v in want.items()} and all(pn[k]["since"] == "2031-03-10T10:00:00" for k in want))
    check("the same state as the OLD function in every case (export; done; wrong), and OLD carries no reason (control)",
          all(pn[k]["state"] == po_[k]["state"] for k in pn) and all(pn[k]["state"] == "export" for k in want) and pn["done"]["state"] == "done"
          and pn["wrong"]["state"] == "wrong" and all(po_[k]["why"] is None for k in po_) and pn["done"]["why"] is None and pn["wrong"]["why"] is None,
          {k: (pn[k]["state"], po_[k]["state"]) for k in pn})
    check("a later day pairs while the first Marg day after the vouchers has no figure: no_before / rebased, never no_figure",
          got["later_pairs_no_before"][0] == "no_before" and got["later_pairs_rebased"][0] == "rebased")
    cn, co = NW["s3"]["cards"], OL["s3"]["cards"]
    H1A, H1C = "Orthotic ke 3 voucher Marg mein daal diye ✓", "Dawa ke voucher Marg mein daal diye ✓"
    GOT = "Closing stock aa gaya ✓ (11-03 10:31)"
    rows = {"no_closing": ["Ab closing stock export kijiye", "Voucher 10-03 10:00 par daale gaye. Uske baad ka closing stock abhi nahi aaya."],
            "no_figure": [GOT, "Server ka 11-03 ka apna hisaab abhi nahi bana — yeh bikri report ke baad banta hai. Aapko abhi kuch nahi karna."],
            "pur_behind": [GOT, "Ab purchase report nikaliye — 11-03 tak ki", "Purchase report aate hi server khud mila lega."],
            "no_before": [GOT, "Jaanch system ki taraf se ruki hai — Doctor sahab ko dikh raha hai. Aapko kuch nahi karna."],
            "rebased": [GOT, "Jaanch system ki taraf se ruki hai — Doctor sahab ko dikh raha hai. Aapko kuch nahi karna."]}
    bad = {}
    for k, r in rows.items():
        if spans(cn[k]["A"]) != [H1A] + r or spans(cn[k]["C"]) != [H1C] + r:
            bad[k] = (spans(cn[k]["A"]), spans(cn[k]["C"]))
    check("Amir's card, stage A and stage C, each row of B.2 letter for letter (closing_day printed dd-mm)", not bad, bad)
    old_A = ["Orthotic ke 3 voucher Marg mein daal diye ✓", "Ab closing stock export kijiye", "Server khud milayega ki Marg ab shelf ke barabar hai."]
    check("control OLD: every reason renders today's words ('Ab closing stock export kijiye' even when the closing has come)",
          all(spans(co[k]["A"]) == old_A for k in rows) and all(spans(co[k]["C"]) == [H1C, "Ab closing stock export kijiye"] for k in rows))
    check("a result without the key renders today's words; a done and a wrong proof render byte-equal OLD and NEW",
          cn["nokey"]["A"] == co["nokey"]["A"] and cn["nokey"]["C"] == co["nokey"]["C"] and spans(cn["nokey"]["A"]) == old_A
          and all(cn[k][s] == co[k][s] for k in ("done", "wrong") for s in ("A", "C", "A_hi", "C_hi", "A_left", "C_left", "A_board", "C_board", "A_owner", "C_owner")))
    TAIL = {"no_figure": "closing stock aa gaya — server ka hisaab banna baaki (bikri report ke baad)",
            "pur_behind": "closing stock aa gaya — purchase report nikalni baaki",
            "no_before": "closing stock aa gaya — jaanch system ki taraf se ruki hai", "rebased": "closing stock aa gaya — jaanch system ki taraf se ruki hai"}
    bad = {}
    for k in rows:
        hiA = ("Ginti #948803: " + TAIL[k]) if k in TAIL else "Ginti #948803: orthotic voucher ki jaanch ke liye closing stock export baaki"
        hiC = ("Ginti #948803: " + TAIL[k]) if k in TAIL else "Ginti #948803: dawa voucher ki jaanch ke liye closing stock export baaki"
        bd = ("Abhi baaki — " + TAIL[k]) if k in TAIL else "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye"
        if cn[k]["A_hi"][:1] != [hiA] or cn[k]["C_hi"][:1] != [hiC] or cn[k]["A_board"] != bd or cn[k]["C_board"] != bd:
            bad[k] = (cn[k]["A_hi"], cn[k]["C_hi"], cn[k]["A_board"], cn[k]["C_board"])
    check("B.2b: his day's two lines (stage A, stage C) and the voucher board's proof line say the same reason; no_closing keeps today's words", not bad, bad)
    check("control OLD: the three places say an export is awaited in every state",
          all(co[k]["A_hi"][:1] == ["Ginti #948803: orthotic voucher ki jaanch ke liye closing stock export baaki"]
              and co[k]["A_board"] == "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye" for k in rows))
    MA = "Marg's closing of 11-03 arrived 11-03 10:31; "
    END = {"no_closing": "waiting for a closing-stock export since 10-03 10:00 (Amir / Shavez)",
           "no_figure": MA + "waiting for our own figure for that day (made when its sale report lands — Shavez; on a no-sale day, the empty report)",
           "pur_behind": MA + "waiting for a purchase export that reaches that day (Amir)",
           "no_before": MA + "held on the system's side (no comparable export before the vouchers / figures re-based) — for the chat",
           "rebased": MA + "held on the system's side (no comparable export before the vouchers / figures re-based) — for the chat"}
    bad = {}
    for k, e in END.items():
        if (cn[k]["A_owner"][:1] != ["Count #948803: Stage A: all 3 orthotic vouchers entered -- " + e]
                or cn[k]["A_left"] != ["count #948803 stage A: " + e] or cn[k]["C_left"] != ["count #948803 stage C: this lot's vouchers entered -- " + e]
                or cn[k]["C_left_open"] != ["count #948803 stage C: 1 medicine vouchers of this lot not entered"]):
            bad[k] = (cn[k]["A_owner"], cn[k]["A_left"], cn[k]["C_left"], cn[k]["C_left_open"])
    check("the owner's lines: each ending (stage A's line and sentence; stage C's sentence once the lot is entered -- unchanged while some of it is left)", not bad, bad)
    check("control OLD: the owner's stage A line ends 'waiting for the closing-stock export'; the left sentence names the export",
          all(co[k]["A_owner"][:1] == ["Count #948803: Stage A: all 3 orthotic vouchers entered -- waiting for the closing-stock export"] for k in END))
    hn, ho = NW["s3"]["hours"], OL["s3"]["hours"]
    check("the warn line: absent at 47 hours, present at 48 -- stage A %s; a stage-C lot %s; amir.proof_wait_hours 72 moves it (%s)"
          % (hn["A|48"], hn["C|48"], hn["A|48|setting72"]),
          hn["A|47"] == [] and hn["C|47"] == [] and len(hn["A|48"]) == 1 and len(hn["C|48"]) == 1 and hn["A|48|setting72"] == []
          and re.match(r"^Count #948803: the voucher proof has waited 48 hours — waiting for a closing-stock export since ", hn["A|48"][0]))
    check("control OLD: no warn line at 48 hours", ho["A|48"] == [] and ho["C|48"] == [])

    # ------------------------------------------------------------------------------------------------------------------------------- 4
    print("-- 4  refusals (B.4)")
    n4, o4 = NW["s4"], OL["s4"]
    R1 = "Report refused 10-03 23:30: W488_REPORT -- W488 test reason (Shavez / Amir to export it again)"
    U15 = [x for x in n4["morning"] if "unrecognised" in x]
    check("a W488 refusal at 23:30 yesterday is shown this morning (09:00): %s; control OLD shows none of it: %s"
          % ([x for x in n4["morning"] if "W488" in x], [x for x in o4["morning"] if "W488" in x]),
          R1 in n4["morning"] and not any("W488" in x for x in o4["morning"]))
    check("fifteen unrecognised refusals (NULL, '' and _UNKNOWN mixed) make ONE line: %s; control OLD on their own evening: %d lines"
          % (U15, sum(1 for x in o4["evening_before"] if "unknown file" in x)),
          len(U15) == 1 and U15[0].startswith("15 unrecognised file(s) refused since 10-03 20:00 (newest ") and sum(1 for x in o4["evening_before"] if "unknown file" in x) > 1)
    check("still there at 35 hours; gone at 37 (the window 36); amir.refused_keep_hours 40 brings it back at 37",
          R1 in n4["h35"] and not any("W488_REPORT" in x for x in n4["h37"]) and R1 in n4["h37_setting40"])
    check("it goes when a VERIFIED file of its type arrives later", not any("W488_REPORT" in x for x in n4["after_verified"]) and len(n4["after_verified"]) == 1)

    # ------------------------------------------------------------------------------------------------------------------------------- 5
    print("-- 5  the owner's lists (C)")
    n5, o5 = NW["s5"], OL["s5"]
    td = dt.date.today()
    since = td.strftime("%d-%m")
    check("both due_sql on the copy: %s; with the newest verified list moved 9 / 36 days back (no category list): %s" % (n5["due0"], n5["due1"]),
          all(list(v) == [0, None] for v in n5["due0"].values()) and list(n5["due1"]["manoj.salt_list"]) == [1, td.isoformat()]
          and list(n5["due1"]["manoj.item_lists"]) == [2, td.isoformat()])
    check("_s444_duty_lines raises each owner_line exactly as worded: %s" % n5["lines8"],
          n5["lines8"] == ["Your salt list from Marg is overdue -- due since %s" % since,
                           "Your monthly Marg lists are overdue: 2 of 2 (category list / item list) -- due since %s" % since])
    check("... also when since is NULL (no salt list ever): %s %s" % (n5["salt_never"][0], n5["salt_never"][1]),
          list(n5["salt_never"][0]) == [1, None] and n5["salt_never"][1] == ["Your salt list from Marg is overdue -- due since -"])
    check("control: with the v7 map no such line", n5["lines7"] == [])
    check("owner_lists at the default settings returns what the OLD function returns", n5["ol_default"] == o5["ol_default"], (n5["ol_default"], o5["ol_default"]))
    check("it follows a changed setting (salt 3 -> limit 3; '9x' -> the constant 35): %s; control OLD %s" % (n5["ol_set"], o5["ol_set"]),
          n5["ol_set"] == [["SALT_WISE_ITEM_LIST", 3], ["CATEGORY_WISE_ITEM_LIST", 35], ["ITEM_MASTER", 35]]
          and o5["ol_set"] == [["SALT_WISE_ITEM_LIST", 8], ["CATEGORY_WISE_ITEM_LIST", 35], ["ITEM_MASTER", 35]])
    check("and survives a database with no setting table: %s" % (n5["ol_nosetting"],),
          n5["ol_nosetting"] == [["SALT_WISE_ITEM_LIST", 8], ["CATEGORY_WISE_ITEM_LIST", 35], ["ITEM_MASTER", 35]])
    check("the v8 map loads in aaj_kaam.load_defs (%s) and in owner_console's reader (%s) without an error" % (n5["load_defs"], n5["console"]),
          n5["load_defs"][0] is None and n5["load_defs"][1] == 8 and isinstance(n5["console"], list) and n5["console"][0] == 8
          and all(v == [0, None] for v in n5["console"][1].values()) and len(n5["console"][1]) == 2)
    check("for every staff login %s the list cut with the v7 map and with the v8 map is identical; only manoj gains the two (%s)"
          % (", ".join(STAFF), n5["manoj_gains"]), all(n5["cuts_equal"].values()) and n5["manoj_gains"] == sorted(NEW_IDS), n5["cuts_equal"])

    # ------------------------------------------------------------------------------------------------------------------------------- 6
    print("-- 6  the strike (D)")
    n6, o6 = NW["s6"], OL["s6"]
    check("learn pairs the W488 printed name with Marg's item (%s); learnt_line returns it (%s)" % (n6["learn1"], n6["line1"]),
          n6["learn1"] == ["W488 ALPHA TABLET"] and n6["line1"] == "W488 ALPHA TABLET")
    check("Wrong (strike): ok; learnt_line no longer returns it (%s) and learn over the same pairing does not bring it back (%s, %s)"
          % (n6["line_after_strike"], n6["learn_again"], n6["line_after_learn"]),
          n6["strike1"][0] is True and n6["line_after_strike"] is None and n6["learn_again"] == [] and n6["line_after_learn"] is None)
    check("control, the OLD design (a delete is the only way back): learn brings the same pair back at once (%s, %s)" % (o6["learn_again"], o6["line_after_learn"]),
          o6["line_after_delete"] is None and o6["learn_again"] == ["W488 ALPHA TABLET"] and o6["line_after_learn"] == "W488 ALPHA TABLET")
    check("a different item for the same printed name is learnt (%s); strike that too, and neither returns (%s / %s); both listed struck %s"
          % (n6["learn_other"], n6["learn_t"], n6["learn_f"], n6["struck"]),
          n6["learn_other"] == ["W488 ALPHA FORTE"] and n6["line_other"] == "W488 ALPHA FORTE" and n6["strike2"][0] is True
          and n6["learn_t"] == [] and n6["learn_f"] == [] and sorted(n6["struck"]) == ["W488 ALPHA FORTE", "W488 ALPHA TABLET"])
    check("Put back restores one at once without a learn (%s -> %s); the other is refused while it holds the name: '%s'" % (n6["back_t"], n6["line_back"], n6["back_f"][1]),
          n6["back_t"][0] is True and n6["line_back"] == "W488 ALPHA TABLET" and n6["back_f"][0] is False
          and n6["back_f"][1] == "Another item is learnt for this name — tap Wrong on that one first.")
    check("the route: a staff login is refused (amir: %s); the doctor strikes (%s) and puts back (%s); control OLD: no route (%s)"
          % (n6["route_amir"], n6["route_manoj"], n6["route_back"], o6["route_manoj"]),
          n6["route_amir"] in (302, 401, 403) and n6["route_manoj"] == [200, True] and n6["route_back"] == [200, True] and o6["route_manoj"][0] in (404, 405))
    pg = n6["page"]
    check("the Items check page: every learnt name has a Wrong button (%d), a collapsed 'Struck: N' with Put back (%d), the sentence, the script"
          % (pg["wrong"], pg["put_back"]), pg["wrong"] == pg["learnt_n"] and pg["wrong"] > 0 and pg["struck"] and pg["put_back"] >= 1 and pg["sentence"] and pg["js"])
    check("control OLD page: no button", o6["page"]["wrong"] == 0 and not o6["page"]["struck"])

    # ------------------------------------------------------------------------------------------------------------------------------- 7
    print("-- 7  staff-eye (D648): amir, darpan, shavez, reception and the owner, signed in on scratch copies (a walk-only store and secret)")
    EN, EO = run("eye", "new", a.fin_new), run("eye", "old", a.fin_old)
    if not check("both staff-eye probes ran to the end (NEW: re-judged on its own copy; OLD: the copy as it is)", EN is not None and EO is not None):
        return finish()
    an = (EN["as_is"]["manoj"]["texts"].get("/finance/stock/api/now") or [None, None])
    ao = (EO["as_is"]["manoj"]["texts"].get("/finance/stock/api/now") or [None, None])
    check("on the live copy with no W488 row: api_now's day %s equals the newest day by date in stock_feed itself (%s); control OLD %s"
          % (an[1], EN["newest_by_date"], ao[1]), an == [200, EN["newest_by_date"]] and ao[1] != EN["newest_by_date"] and ao[1] == "30-09-2026")
    ALLOW = {"/finance/stock/api/now": "A.5 the newest day", "/finance/stock/api/readiness": "A.3 / A.4 the stock lines",
             "/finance/stock/api/drift": "A.1-A.3 the days and the readiness block", "/finance/darpan/api/pipeline": "A.7 the newest snapshot",
             "/finance/purchase/page/items": "D the Wrong / Struck buttons"}
    ALLOW_WHO = {("darpan", "/finance/stockmatch"): "the shelf-gap re-judge: Darpan's spot-count roster",
                 ("manoj", "/finance/approvals"): "the Needs-you list: B.4 refusals, the shelf-gap count, B.3",
                 ("manoj", "/finance/amir/day"): "B.3 the owner's view of Amir's day"}
    ALLOW_WAIT = {"/finance/amir": "B.2 Amir's card", "/finance/amir/step/6": "B.2 his card", "/finance/amir/step/7": "B.2 / B.2b his card and his day's line",
                  "/finance/amir/step/5": "B.2 his card on the step", "/finance/amir/step/3": "B.2 his card on the step",
                  "/finance/stock/api/pad/amir/1": "B.2b the board's line"}
    for tag in ("as_is", "waiting"):
        en, eo = EN[tag], EO[tag]
        print("   [%s]" % tag)
        for who in USERS:
            n, o = en[who], eo[who]
            diff = sorted(k for k in set(n["pages"]) | set(o["pages"]) if n["pages"].get(k) != o["pages"].get(k))
            allowed = dict(ALLOW, **(ALLOW_WAIT if tag == "waiting" else {}))
            allowed.update({p: why for (w_, p), why in ALLOW_WHO.items() if w_ == who})
            unexplained = [d for d in diff if d not in allowed]
            check("%s (%s): signs in (%s), %d tiles; %d pages compared NEW vs OLD; differences: %s"
                  % (who, tag, n["status"], n["n_tiles"], len(n["pages"]), ["%s (%s)" % (d, allowed.get(d, "NOT EXPLAINED")) for d in diff] or "none"),
                  n["status"] == 200 and n["n_tiles"] == o["n_tiles"] and not unexplained and n["pages"].get("home") == o["pages"].get("home"), unexplained)
            def misses(side):
                due_ = [r for r in side["duties"] if isinstance(r.get("due_n"), int) and r["due_n"] > 0 and r["id"] not in NEW_IDS]
                return due_, sorted(r["id"] for r in due_ if (r.get("tile") and r.get("tile_seen") is False) or r.get("door_seen") is False)
            due, miss = misses(n)
            _due_o, miss_o = misses(o)
            errs = [r["id"] for r in n["duties"] if isinstance(r.get("due_n"), str)]
            before = [m for m in miss if m in miss_o]
            if before:
                PRE.update({m: [r.get("door") for r in n["duties"] if r["id"] == m] + [r.get("since") for r in n["duties"] if r["id"] == m] for m in before})
            check("   %s: %d duties in the map, %d due now -- each due one visible (its tile on the home, its marker on its door) as on the OLD side; "
                  "the two door-less duties of S488 exempt by id%s" % (who, len(n["duties"]), len(due),
                                                                     ("; NOT visible on either side, before this kit too: %s (a finding, below)" % before) if before else ""),
                  not [m for m in miss if m not in miss_o] and not errs, (miss, miss_o, errs))
        ny_n, ny_o = en["_needs_you"], eo["_needs_you"]
        print("   the owner's Needs-you, NEW only: %s" % [x for x in ny_n if x not in ny_o])
        print("   the owner's Needs-you, OLD only: %s" % [x for x in ny_o if x not in ny_n])
    w_n, w_o = EN["waiting"]["amir"]["texts"], EO["waiting"]["amir"]["texts"]
    a_n = w_n.get("/finance/amir") or []
    a_o = w_o.get("/finance/amir") or []
    check("the W488 waiting state (the closings after the vouchers set aside; a Marg push of 06-10 with no figure of ours): Amir's home card "
          "says 'Closing stock aa gaya' and nothing is asked of him (NEW %s); control OLD tells him to export (%s)"
          % ([x for x in a_n if "losing stock" in x or "hisaab" in x][:3], [x for x in a_o if "export" in x][:2]),
          any(x.startswith("Closing stock aa gaya ✓ (06-10 23:59)") for x in a_n) and not any(x == "Ab closing stock export kijiye" for x in a_n)
          and any(x == "Ab closing stock export kijiye" for x in a_o), EN["set_aside"])
    pb_n, pb_o = (w_n.get("/finance/stock/api/pad/amir/1") or [None])[0], (w_o.get("/finance/stock/api/pad/amir/1") or [None])[0]
    check("... and the voucher board's line (as amir): NEW '%s'; control OLD '%s'" % (pb_n, pb_o),
          str(pb_n) == "Abhi baaki — closing stock aa gaya — server ka hisaab banna baaki (bikri report ke baad)"
          and pb_o == "Abhi baaki — voucher daal diye, Marg ka agla closing stock export aane dijiye", (pb_n, pb_o))
    ny = [x for x in EN["waiting"]["_needs_you"] if "Count #" in x and "Stage A" in x]
    check("the owner's stage-A line in that state names the arrival: %s" % ny, any("Marg's closing of 06-10 arrived 06-10 23:59" in x for x in ny))
    if PRE:
        print("   FINDING (not this kit's; the same on the box as it is): a due duty whose marker is not on its door page -- %s" % PRE)
    return finish()


def finish():
    if FAILS:
        print("WALK_S488 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + f[:200])
        return 1
    print("WALK_S488 GREEN -- %d checks" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
