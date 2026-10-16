#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s570.py -- kit S570_PROOF_MORNING_WINDOW: the walk (the brief's section 3), on the server, on scratch copies only.

    python3 -B walk_s570.py --run DIR --work /tmp/... --db finance.db --spine spine.db

  run    the installer's scratch layout: <run>/new/finance (the built stock_app.py) and <run>/old/finance (the box as it is).
  db     a backup-API copy of finance.db; every probe works on its OWN further copy.
  spine  a backup-API copy of the LIVE spine.db; every variant below is a further copy of it.

Every probe is a fresh process per side (NEW / OLD), FINANCE_DB and SPINE_DB on its own copies, ORDER_PUSH_STUB / RING_PORTAL_DIR /
REPORTS_NTFY_STUB pointed into the scratch folder: nothing reaches a phone. The walk's own rows are found by their keys (md5 'W570...',
the made-up day 2027-03-10, the made-up feed day 21-03-2027), never by counting. Every control is the same check on the OLD file and
must go red there. No person, phone or account number is printed; the walk's own output is checked for a run of ten digits (W6)."""
import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys

TAG = "W570JSON "
D, D1 = "2027-03-10", "2027-03-11"                              # the made-up day D (W1/W2) and the morning after
EARLIER = ("2026-10-10", "2026-10-12", "2026-10-13")             # the brief's earlier closings on the live copy (W3)
LIVE_CLOSE = "2026-10-15"                                        # the live case's closing (W4/W5)
OUT = []


def say(s=""):
    OUT.append(str(s))


def mask(s):
    return re.sub(r"\d{10,}", "##########", str(s))


def copydb(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    s = sqlite3.connect("file:%s?mode=ro" % src, uri=True, timeout=60)
    d = sqlite3.connect(dst)
    s.backup(d)
    d.close()
    s.close()


# ===================================================================================================================== the spine variants
def add_export(c, md5, family, stamp, dfrom, dto):
    c.execute("INSERT INTO sp_export (md5, name, family, stamp, date_from, date_to, as_on, ok, failed, role, note) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
              (md5, "W570 walk %s" % family, family, stamp, dfrom, dto, None, 1, 0, None, "S570 walk row"))


def make_variants(spine, work):
    v = {}
    v["live"] = os.path.join(work, "sp_live.db")
    copydb(spine, v["live"])
    # W1 -- the morning order on the made-up day D: sale D captured D+1 05:10, closing D captured D+1 05:17, purchases to D captured D+1 06:00
    v["d1"] = os.path.join(work, "sp_d1.db")
    copydb(spine, v["d1"])
    c = sqlite3.connect(v["d1"])
    add_export(c, "W570D1SALE", "SALE_BILLWISE", "20270311-051000", D, D)
    add_export(c, "W570D1CLOSE", "STOCK_CLOSING", "20270311-051700", D, D)
    add_export(c, "W570D1PB", "PURCHASE_BILLWISE", "20270311-060000", "2027-03-01", D)
    add_export(c, "W570D1PI", "PURCHASE_ITEMWISE", "20270311-060000", "2027-03-01", D)
    c.execute("INSERT INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,?)", (D, "W570 WALK ITEM", 1, "W570D1CLOSE"))
    c.commit()
    c.close()
    # W2 -- a true "not yet": the sale D captured D+1 05:20 (after the closing: both files pass the sale side), purchases to D captured D 09:10
    v["d2"] = os.path.join(work, "sp_d2.db")
    copydb(spine, v["d2"])
    c = sqlite3.connect(v["d2"])
    add_export(c, "W570D2SALE", "SALE_BILLWISE", "20270311-052000", D, D)
    add_export(c, "W570D2CLOSE", "STOCK_CLOSING", "20270311-051700", D, D)
    add_export(c, "W570D2PB", "PURCHASE_BILLWISE", "20270310-091000", "2027-03-01", D)
    add_export(c, "W570D2PI", "PURCHASE_ITEMWISE", "20270310-091000", "2027-03-01", D)
    c.execute("INSERT INTO sp_close (as_on, k20, units, source_md5) VALUES (?,?,?,?)", (D, "W570 WALK ITEM", 1, "W570D2CLOSE"))
    c.commit()
    c.close()
    # W4b -- the live copy plus a made-up purchase export captured 16-10 11:00 covering 1-16 Oct (both purchase families)
    v["pur"] = os.path.join(work, "sp_pur.db")
    copydb(spine, v["pur"])
    c = sqlite3.connect(v["pur"])
    add_export(c, "W570PURB", "PURCHASE_BILLWISE", "20261016-110000", "2026-10-01", "2026-10-16")
    add_export(c, "W570PURI", "PURCHASE_ITEMWISE", "20261016-110000", "2026-10-01", "2026-10-16")
    c.commit()
    c.close()
    # W5 -- the morning state: the live copy with any purchase export captured on 16-10 or later set aside (ok=0) -- the reach as it stood
    # at 11:00 IST 16-Oct whatever has landed since; a no-op when nothing has
    v["morning"] = os.path.join(work, "sp_morning.db")
    copydb(spine, v["morning"])
    c = sqlite3.connect(v["morning"])
    n = c.execute("UPDATE sp_export SET ok=0 WHERE family LIKE 'PURCHASE%' AND stamp >= '20261016-000000'").rowcount
    c.commit()
    c.close()
    v["_morning_set_aside"] = n
    return v


# ============================================================================================================================ the probe
def probe():
    side_dir, mode = os.environ["W570_FIN"], os.environ["W570_MODE"]
    sys.path.insert(0, side_dir)
    os.chdir(side_dir)
    import finance_app as fa                                    # noqa: E402
    import stock_watch as SW                                    # noqa: E402
    SW.SPINE_DB = os.environ["SPINE_DB"]
    import stock_app as SA                                      # noqa: E402
    assert os.path.abspath(SA.__file__).startswith(os.path.abspath(side_dir)), "stock_app from the wrong folder: %s" % SA.__file__
    assert os.path.abspath(fa.DB_PATH) == os.path.abspath(os.environ["FINANCE_DB"]) and fa.DB_PATH.startswith("/tmp/"), "a scratch copy only"
    out = dict(mode=mode, sa=SA.__file__)
    sp = SA._s524_spine()
    assert sp is not None, "the spine copy is not readable"
    reach = SA._s524_reach(sp)
    out["reach"] = reach
    closings = SA._s524_closings(sp)
    out["tryable"] = {c["as_on"] + "@" + c["stamp"]: list(SA._s524_tryable(c, reach)) for c in closings}
    con = sqlite3.connect(fa.DB_PATH, timeout=60)
    if mode in ("d1", "d2"):
        mine = [c for c in closings if c["as_on"] == D]
        out["mine"] = [dict(c, tryable=list(SA._s524_tryable(c, reach))) for c in mine]
    if mode == "live":
        # W1/W2 at the function, on made-up dicts (no spine) -- the chat's three cases of the brief's 2.1 too
        cD = dict(as_on=D, stamp="20270311-051700", stamp_iso="2027-03-11T05:17:00", end_day=D)
        F = {}
        F["morning"] = SA._s524_tryable(cD, dict(last_sale=D, sale_stamp="20270311-051000", last_pur=D, pur_stamp="20270311-060000"))
        F["pur_same_day"] = SA._s524_tryable(cD, dict(last_sale=D, sale_stamp="20270311-052000", last_pur=D, pur_stamp="20270310-091000"))
        F["pur_next_day_mid"] = SA._s524_tryable(cD, dict(last_sale=D, sale_stamp="20270311-051000", last_pur=D1, pur_stamp="20270311-111000"))
        F["sale_same_day_mid"] = SA._s524_tryable(cD, dict(last_sale=D, sale_stamp="20270310-150000", last_pur=D, pur_stamp="20270311-060000"))
        F["sale_short_day"] = SA._s524_tryable(cD, dict(last_sale="2027-03-09", sale_stamp="20270311-051000", last_pur=D, pur_stamp="20270311-060000"))
        out["fn"] = {k: list(v) for k, v in F.items()}
        # W3 -- the proof tables: the real lots' windows and a window just before each earlier closing
        root = SA._s446_root(con)
        out["root"] = root
        ent, batches = SA._s446_entered(con, root), SA._s446_batches(con, root)
        win = SA._s446_window(con, root)
        at_of = {k: str(win.get(k) or v[1] or "") for k, v in ent.items()}
        st = SA.amir_stage(con, root)
        wins = []
        for lot in ((st or {}).get("C") or {}).get("waiting_export") or []:
            ks = [tuple(k) for k in lot.get("keys") or [] if tuple(k) in at_of]
            if ks:
                wins.append(("lot@" + str(lot.get("at"))[:16], min(at_of[k] for k in ks)[:19], max(at_of[k] for k in ks)[:19]))
        for c in closings:
            if c["as_on"] in EARLIER and c["end_day"]:
                t0 = c["stamp_iso"][:17] + "00"                  # a window a few seconds before the closing's capture
                wins.append(("before " + c["as_on"], t0, t0))
        tabs = {}
        for name, fa_, la_ in wins:
            T = SA._s524_table(con, sp, root, ent, batches, fa_, la_, at_of)
            tabs[name] = dict(R=(T["R"] or {}).get("as_on"), after=[c["as_on"] for c in T["after"]], tries=[c["as_on"] for c in T["tries"]],
                              N=(T.get("N") or {}).get("as_on"), N_short=T.get("N_short"),
                              keys={k: dict(proven=e.get("proven"), wrong=e.get("wrong"), pending=e.get("pending_reach"),
                                            tries=[[t["X"]["as_on"], t.get("ok"), t.get("why"), round(float(t.get("res") or 0), 2)] for t in e["tries"]])
                                    for k, e in sorted(T["keys"].items())})
        out["tables"] = tabs
    if mode in ("live", "pur", "morning"):
        fc = fa.app.test_client(use_cookies=False)
        r = fc.get("/finance/stock/api/pad/hub/1", headers={"X-Clinic-User": "manoj", "X-Clinic-Role": "owner"})
        j = r.get_json(silent=True) or {}
        pr = j.get("proof") or {}
        C = pr.get("C") or {}
        out["hub"] = dict(code=r.status_code, state=pr.get("state"), stage=pr.get("stage"), text=pr.get("text"), lines=pr.get("lines"),
                          rows=pr.get("rows"),
                          counts={k: C.get(k) for k in ("total", "entered", "released", "lots", "verified")},
                          waiting=[dict(at=w.get("at"), n=len(w.get("keys") or []), **{k: (w.get("proof") or {}).get(k) for k in
                                   ("state", "why", "closing_day", "closing_at", "since")}) for w in C.get("waiting_export") or []],
                          wrong=[{k: x.get(k) for k in ("item", "need", "need_key", "need_hi", "moved", "moved_hi", "marg", "marg_hi", "closing_day", "keys")}
                                 for x in (C.get("wrong") or [])])
        st = SA.amir_stage(con)
        sw = SA._s521_stage_words(con, st) if st else {}
        out["card_hi"] = (sw or {}).get("card_hi")
        out["owner_en"] = (sw or {}).get("owner_en")
    if mode == "live":                                          # after the hub: the made-up feed rows never reach the hub's read
        # W7 (E3/E4) -- the feed branch: no clean spine closing after the vouchers; a made-up Marg push of 21-03-2027 captured mid-day
        # (21-03 10:11) and then one captured 22-03 05:17 (the end of 21-03). R is any closing; after = [].
        cols = [r[1] for r in con.execute("PRAGMA table_info(stock_feed)")]
        tmpl = con.execute("SELECT * FROM stock_feed WHERE source LIKE 'push_snapshot%' ORDER BY received_at DESC LIMIT 1").fetchone()
        pk = [r[1] for r in con.execute("PRAGMA table_info(stock_feed)") if r[5]]
        row = dict(zip(cols, tmpl))
        for k in pk:
            row.pop(k, None)
        R0 = next(c for c in closings if c["end_day"])

        def feed(at):
            r = dict(row, as_on="21-03-2027", source="push_snapshot", received_at=at)
            if "item" in r:
                r["item"] = "W570 WALK ITEM"
            con.execute("INSERT INTO stock_feed (%s) VALUES (%s)" % (",".join(r), ",".join("?" * len(r))), list(r.values()))
            con.commit()
        feed("2027-03-21T10:11:00")
        out["feed_mid"] = SA._s488_why(con, sp, closings, R0, [], "2027-03-20T10:00:00")
        feed("2027-03-22T05:17:00")
        out["feed_clean"] = SA._s488_why(con, sp, closings, R0, [], "2027-03-20T10:00:00")
    try:
        sp.con.close()
    except Exception:                                            # noqa: BLE001
        pass
    print(TAG + json.dumps(out, default=str))
    return 0


def run_probe(run, side, mode, spine, db0, work):
    fin = os.path.join(run, side, "finance")
    d = os.path.join(work, "p_%s_%s" % (side, mode))
    os.makedirs(os.path.join(d, "nosso"), exist_ok=True)
    os.makedirs(os.path.join(d, "noring"), exist_ok=True)
    db = os.path.join(d, "finance.db")
    copydb(db0, db)
    sp = os.path.join(d, "spine.db")
    copydb(spine, sp)
    env = dict(os.environ, W570_FIN=fin, W570_MODE=mode, FINANCE_DB=db, SPINE_DB=sp, FINANCE_ALLOW_HEADER_AUTH="1", FINANCE_SSO_DIR=os.path.join(d, "nosso"),
               ORDER_PUSH_STUB=os.path.join(d, "pushes.jsonl"), RING_PORTAL_DIR=os.path.join(d, "noring"), REPORTS_NTFY_STUB=os.path.join(d, "ntfy.jsonl"))
    for k in ("SARVAM_API_KEY", "ORDER_PUSH_NONE", "ORDER_TODAY", "ORDER_TICK", "ORDER_CLOCK"):
        env.pop(k, None)
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--probe"], env=env, cwd=fin, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                       universal_newlines=True, timeout=1800)
    js = [l for l in p.stdout.splitlines() if l.startswith(TAG)]
    if not js:
        say("   the %s/%s probe did not finish (exit %s); its last lines:" % (side, mode, p.returncode))
        for l in p.stdout.splitlines()[-15:]:
            say("     " + l[:300])
        return None
    return json.loads(js[-1][len(TAG):])


# ============================================================================================================================ the checks
FAILS, NCHK = [], [0]


def check(name, ok, detail=None):
    NCHK[0] += 1
    say(("GREEN " if ok else "RED   ") + name + ("" if ok or detail is None else "  -- " + str(detail)[:400]))
    if not ok:
        FAILS.append(name)
    return bool(ok)


def control(name, red_on_old, detail=None):
    """A control: the same check on the OLD file must be RED."""
    NCHK[0] += 1
    say(("CONTROL RED (as it must) " if red_on_old else "CONTROL NOT RED ") + name + ("" if red_on_old or detail is None else "  -- " + str(detail)[:400]))
    if not red_on_old:
        FAILS.append("control: " + name)
    return bool(red_on_old)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--probe":
        return probe()
    ap = argparse.ArgumentParser()
    for k in ("--run", "--work", "--db", "--spine"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    work = os.path.abspath(a.work)
    assert work.startswith("/tmp/") and os.path.abspath(a.db).startswith("/tmp/") and os.path.abspath(a.spine).startswith("/tmp/"), "scratch paths only"
    os.makedirs(work, exist_ok=True)
    V = make_variants(a.spine, work)
    P = {}
    for side in ("new", "old"):
        for mode, spv in (("live", "live"), ("d1", "d1"), ("d2", "d2"), ("pur", "pur"), ("morning", "morning")):
            P[(side, mode)] = run_probe(a.run, side, mode, V[spv], a.db, work)
    missing = [k for k, v in P.items() if v is None]
    if missing:
        say("WALK_S570 RED -- probes did not finish: %s" % missing)
        return finish(1)
    N, O = (lambda m: P[("new", m)]), (lambda m: P[("old", m)])

    # ---- W1 the morning order ------------------------------------------------------------------------------------------------------
    say("W1 the morning order (made-up day %s: sale captured %s 05:10, closing %s 05:17, purchases %s 06:00)" % (D, D1, D1, D1))
    check("W1a function: _s524_tryable -> (True, '') on the NEW file", N("live")["fn"]["morning"] == [True, ""], N("live")["fn"]["morning"])
    control("W1a on the OLD file -> %s" % O("live")["fn"]["morning"], O("live")["fn"]["morning"] != [True, ""], O("live")["fn"]["morning"])
    n1, o1 = N("d1").get("mine") or [], O("d1").get("mine") or []
    check("W1b the spine copy: the made-up closing read by _s524_closings (end_day %s), the reach by _s524_reach (sale %s, pur %s) -> tryable %s"
          % ((n1[0]["end_day"] if n1 else "?"), N("d1")["reach"]["last_sale"], N("d1")["reach"]["last_pur"], (n1[0]["tryable"] if n1 else "?")),
          len(n1) == 1 and n1[0]["end_day"] == D and N("d1")["reach"]["sale_stamp"] == "20270311-051000" and n1[0]["tryable"] == [True, ""], n1)
    control("W1b on the OLD file -> %s" % (o1[0]["tryable"] if o1 else "?"), bool(o1) and o1[0]["tryable"] == [False, "sale"], o1)

    # ---- W2 a true "not yet" ----------------------------------------------------------------------------------------------------------
    say("W2 a true 'not yet' (purchases to %s captured %s 09:10, inside that day's shop hours)" % (D, D))
    n2, o2 = N("d2").get("mine") or [], O("d2").get("mine") or []
    check("W2a function: NEW (False, 'pur'), OLD (False, 'pur')", N("live")["fn"]["pur_same_day"] == [False, "pur"] and O("live")["fn"]["pur_same_day"] == [False, "pur"],
          (N("live")["fn"]["pur_same_day"], O("live")["fn"]["pur_same_day"]))
    check("W2b the spine copy: NEW %s, OLD %s (both (False, 'pur'))" % ((n2[0]["tryable"] if n2 else "?"), (o2[0]["tryable"] if o2 else "?")),
          len(n2) == 1 and len(o2) == 1 and n2[0]["tryable"] == [False, "pur"] and o2[0]["tryable"] == [False, "pur"], (n2, o2))
    fN, fO = N("live")["fn"], O("live")["fn"]
    check("W2c the brief's other cases: purchase to D+1 captured D+1 11:10 (after the closing) %s; a sale captured D 15:00 %s; a sale report short of D %s"
          % (fN["pur_next_day_mid"], fN["sale_same_day_mid"], fN["sale_short_day"]),
          fN["pur_next_day_mid"] == [True, ""] and fN["sale_same_day_mid"] == [False, "sale"] and fN["sale_short_day"] == [False, "sale"], fN)

    # ---- W3 nothing else moves -----------------------------------------------------------------------------------------------------
    say("W3 nothing else moves (the live copy)")
    tN, tO = N("live")["tryable"], O("live")["tryable"]
    diff = {k: (tO.get(k), tN.get(k)) for k in set(tN) | set(tO) if tN.get(k) != tO.get(k)}
    for k in sorted(tN):
        say("   closing %s  OLD %s  NEW %s" % (k, tO.get(k), tN.get(k)))
    ear = {e: [k for k in tN if k.startswith(e + "@")] for e in EARLIER}
    check("W3a the earlier closings %s are on the copy and give the same answer on both files ((True, ''))" % ", ".join(EARLIER),
          all(ear[e] for e in EARLIER) and all(tN[k] == tO[k] == [True, ""] for e in EARLIER for k in ear[e]), ear)
    check("W3b the only closing whose answer moves is %s (%s)" % (LIVE_CLOSE, diff), all(k.startswith(LIVE_CLOSE + "@") for k in diff), diff)
    TN, TO = N("live")["tables"], O("live")["tables"]
    for name in sorted(TN):
        x = TN[name]
        say("   table %-26s R %s · after %s · tries %s · N %s (short: OLD %r, NEW %r) · keys %d · proven %d · wrong %d · pending %d"
            % (name, x["R"], ",".join(a[5:] for a in x["after"]), ",".join(a[5:] for a in x["tries"]) or "-", x["N"], (TO.get(name) or {}).get("N_short"),
               x["N_short"], len(x["keys"]), sum(1 for e in x["keys"].values() if e["proven"]), sum(1 for e in x["keys"].values() if e["wrong"]),
               sum(1 for e in x["keys"].values() if e["pending"])))
    same = {n: ({k: v for k, v in TN[n].items() if k != "N_short"} == {k: v for k, v in (TO.get(n) or {}).items() if k != "N_short"}) for n in TN}
    check("W3c the proof table (R, after, tries, N, every key's tries and verdict) is the same on both files for %d windows (the lots' and one before each earlier closing)" % len(TN),
          len(TN) >= 4 and set(TN) == set(TO) and all(same.values()) and any(n.startswith("before") for n in TN), same)

    # ---- W4 the live case ------------------------------------------------------------------------------------------------------------
    say("W4 the live case, count #1, on the copy")
    for lab, side, m in (("as on the copy", "new", "live"), ("as on the copy", "old", "live"), ("with a made-up purchase export captured 16-10 11:00 covering 1-16 Oct", "new", "pur")):
        h = P[(side, m)]["hub"]
        say("   %s (%s): reach pur to %s @ %s; hub %s state %s stage %s; %s" % (lab, side.upper(), P[(side, m)]["reach"]["last_pur"], P[(side, m)]["reach"]["pur_stamp"],
                                                                         h["code"], h["state"], h["stage"], h["counts"]))
        for w in h["waiting"]:
            say("     lot released %s (%d vouchers): %s · why %s · closing_day %s · closing_at %s · since %s" % (str(w["at"])[:16], w["n"], w["state"], w["why"], w["closing_day"], w["closing_at"], w["since"]))
        say("     text: %s" % h["text"])
        for r in h["wrong"]:
            say("     WRONG ROW: %s · voucher(s) %s · need %s (%s) · Marg moved %s (%s) · Marg at %s %s" % (r["item"], ",".join(r.get("keys") or []), r.get("need_key"), r.get("need_hi"),
                                                                                      r.get("moved"), r.get("moved_hi"), r.get("closing_day"), r.get("marg_hi") or r.get("marg")))
        for l in h["lines"] or []:
            say("     owner line: %s" % (l.get("text") if isinstance(l, dict) else l))
    hp = N("pur")["hub"]
    check("W4a with the made-up purchase export the NEW file gives a verdict (state %s; lots waiting %d; wrong rows %d)" % (hp["state"], len(hp["waiting"]), len(hp["wrong"])),
          hp["code"] == 200 and hp["stage"] == "C" and (hp["state"] in ("now", "done") or len(hp["waiting"]) < len(N("live")["hub"]["waiting"]) or any(w["why"] not in ("no_figure", "pur_behind") for w in hp["waiting"])), hp)
    hpo = O("pur")["hub"]
    control("W4a on the OLD file with the same made-up purchase export: state %s, lots waiting %d, wrong rows %d (the sale side still refuses the 05:17 closing)"
            % (hpo["state"], len(hpo["waiting"]), len(hpo["wrong"])), hpo["state"] == "wait" and len(hpo["wrong"]) == 0, hpo)
    names = sorted({r["item"] for r in hp["wrong"]})
    say("   the wrong rows name: %s (REPORT_S569's trial expected KT ROS DT and VINBACTUM DS among them -- shown, not asserted)" % (", ".join(names) or "none"))

    # ---- W5 the sentence -------------------------------------------------------------------------------------------------------------
    hm, hmo = N("morning")["hub"], O("morning")["hub"]
    say("W5 the sentence, the morning state (purchase exports captured on 16-10 set aside on this copy: %d)" % V["_morning_set_aside"])
    say("   NEW: %s" % hm["text"])
    say("   OLD: %s" % hmo["text"])
    sale_in = N("morning")["reach"]["last_sale"] >= LIVE_CLOSE
    t = hm["text"] or ""
    check("W5a the 15-10 sale report is in (reach last_sale %s); the NEW sentence has no '10:11' and no 'made when its sale report lands'" % N("morning")["reach"]["last_sale"],
          sale_in and "10:11" not in t and "made when its sale report lands" not in t, t)
    check("W5b the purchase side short -> the purchase words ('waiting for a purchase export that reaches that day (Amir)') and the closing the proof uses ('arrived 16-10 05:17')",
          all(w["why"] == "pur_behind" for w in hm["waiting"]) and "waiting for a purchase export that reaches that day (Amir)" in t and "arrived 16-10 05:17" in t, hm["waiting"])
    to = hmo["text"] or ""
    control("W5 on the OLD file the sentence carries both '10:11' and 'made when its sale report lands'", "10:11" in to and "made when its sale report lands" in to, to)
    for side in ("new", "old"):
        say("   Amir's card (%s): %s" % (side.upper(), P[(side, "morning")]["card_hi"]))
    cN, cO = N("morning")["card_hi"] or "", O("morning")["card_hi"] or ""
    check("W5c Amir's card: no verdict word; the same words as on the OLD file, or those words with S528's own do-this tail ' · Purchase report nikaaliye' (charter 1b: the wait is his purchase export)",
          cO and (cN == cO or cN == cO + " · Purchase report nikaaliye") and not re.search(r"(?i)galat|sahi nahi|wrong|verdict", cN), (cO, cN))

    # ---- W7 the feed branch (E3 / E4) --------------------------------------------------------------------------------------------------
    say("W7 the feed branch: no clean spine closing after the vouchers; a made-up Marg push of 21-03-2027")
    fmN, fmO, fcN, fcO = N("live")["feed_mid"], O("live")["feed_mid"], N("live")["feed_clean"], O("live")["feed_clean"]
    say("   mid-day push only (21-03 10:11): NEW %s | OLD %s" % (fmN, fmO))
    say("   + a push captured 22-03 05:17:  NEW %s | OLD %s" % (fcN, fcO))
    check("W7a a mid-day push is never named (NEW: why no_closing, no closing_at)", fmN.get("why") == "no_closing" and not fmN.get("closing_at"), fmN)
    control("W7a on the OLD file the mid-day push is named", fmO.get("closing_at") == "2027-03-21T10:11:00", fmO)
    check("W7b the clean push (22-03 05:17) is the one named (NEW)", fcN.get("closing_at") == "2027-03-22T05:17:00" and fcN.get("closing_day") == "21-03-2027", fcN)
    control("W7b on the OLD file the day's earliest push (the mid-day 10:11) is named", fcO.get("closing_at") == "2027-03-21T10:11:00", fcO)
    return finish(0)


def finish(rc):
    body = "\n".join(OUT)
    ten = re.findall(r"\d{10,}", body)
    if FAILS or rc:
        verdict = "WALK_S570 RED -- %d of %d checks failed: %s" % (len(FAILS), NCHK[0], "; ".join(FAILS)[:900])
    else:
        verdict = "WALK_S570 GREEN (%d checks, every control red on the old file)" % NCHK[0]
    print(mask(body))
    print(("GREEN W6 no run of ten digits in the walk's own output" if not ten else "RED   W6 a run of ten digits in the walk's own output (%d) -- masked above" % len(ten)))
    if ten:
        verdict = "WALK_S570 RED -- W6: a run of ten digits in the output"
    print(verdict)
    return 0 if verdict.startswith("WALK_S570 GREEN") else 1


if __name__ == "__main__":
    sys.exit(main())
