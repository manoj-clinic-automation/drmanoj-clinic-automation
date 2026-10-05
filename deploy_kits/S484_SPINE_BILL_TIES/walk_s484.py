#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s484.py -- kit S484_SPINE_BILL_TIES: the walk (the brief's section 2), on the server, on scratch copies only.

    python -B walk_s484.py --work /tmp/... --spine-new DIR --spine-old DIR --readings DIR --archive DIR --ingest DIR --fin DIR
                           --db scratch_finance.db --live-db /root/finance/spine/spine.db

  spine-new / spine-old   scratch copies of the spine folder (the *.py and *.json; spine_read.py beside them): NEW carries the built
                          spine_build.py and marg_read.py, OLD is the box as it is. No OFF file may sit in either.
  readings, archive, live-db, fin   the live ones -- READ ONLY here (the readings are copied; the 08:00 spine.db is opened mode=ro).

Sections: 1 the reader (S483's, re-run)  2 the order of same-second exports  3 the tie of a shared bill number  4 the gate
5 F-737 measured, not mended  6 the new spine.db against the 08:00 one. Every control named in the brief is run on the OLD file.
Nothing is imported from inside deploy_kits (CLAUDE.md rule 11): every module is loaded from the copies the caller names.
"""
import argparse
import ast
import collections
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time

DE = "de92f5d5185646d4de563e30d5464f6e"          # BILL/ITEM WISE, 208 lines, text-made (F-734)
F6 = "f62cc9e3d93c692f1795229be9e7cfe1"          # the whole-shop category list (F-735)
SUP_WHOLE, SUP_ONE = "957b473f", "15b48bc5"      # the two SUPPLIER/ITEM WISE sheets of the same second (the whole one; one supplier's)
P0, P1 = "2026-09-01", "2026-10-03"              # the period all three sheets print
G_PUR = "every purchase line of an export that is the authority for its whole period belongs to exactly one bill"
G_SALE = "every sale export passes its own witness"
G_CAT = "every CATEGORY_WISE_ITEM_LIST export passes its own witness"
G_ADD = "every purchase bill: its lines re-add to the bill (net, within Rs 1)"
PLF = ("PURCHASE_ITEMWISE", "PURCHASE_BILLITEMWISE")
N, FAILS = [0], []


def check(label, cond, got=None):
    N[0] += 1
    print(("  ok   " if cond else "  FAIL ") + label + (("   [" + re.sub(r"\d{10,}", "##########", str(got))[:600] + "]") if got is not None else ""))
    if not cond:
        FAILS.append(label)
    return bool(cond)


def md5f(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def core(rec):
    return json.loads(json.dumps(dict(family=rec.get("family"), ok=rec.get("ok"), data=rec.get("data") or {})))


def statements(path):
    src = open(path, encoding="utf-8").read()
    out = {}
    for node in ast.parse(src).body:
        seg = ast.get_source_segment(src, node)
        out[getattr(node, "name", None) or ("stmt:" + seg[:60])] = seg
    return out


def ubill(b):
    return (b or "").upper().lstrip("0") or "0"


def tol(b):
    return 100 + 0.002 * abs(b["amount_p"])       # the build's own expression, the same one the gate uses


def run_build(spine_dir, readings, out_db, fin_db):
    """spine_build.py's own main(), as the crontab runs it -- on a scratch store, to a scratch --out."""
    os.makedirs(os.path.dirname(out_db), exist_ok=True)
    p = subprocess.run([sys.executable, "-B", os.path.join(spine_dir, "spine_build.py"), "--readings", readings, "--out", out_db, "--finance-db", fin_db],
                       cwd=spine_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=1500)
    rows, detail = {}, {}
    for l in p.stdout.splitlines():
        m = re.match(r"^  (ok|FAIL|note)\s+(.*?)(  -- .*)?$", l)
        if m:
            rows[m.group(2).strip()] = m.group(1)
            detail[m.group(2).strip()] = (m.group(3) or "")[5:]
    state = {}
    try:
        state = json.load(open(os.path.join(os.path.dirname(out_db), "spine_state.json")))
    except (OSError, ValueError):
        pass
    return dict(rc=p.returncode, rows=rows, detail=detail, fails=sorted(k for k, v in rows.items() if v == "FAIL"),
                swapped="SPINE BUILT AND SWAPPED" in p.stdout, off="switched off" in p.stdout, state=state,
                tail=p.stdout.splitlines()[-1] if p.stdout else "", db=out_db if os.path.exists(out_db) else out_db + ".failed")


def passed(b):
    return b["rc"] == 0 and b["swapped"] and not b["off"] and not b["fails"] and b["state"].get("passed") is True and os.path.exists(b["db"]) \
        and not b["db"].endswith(".failed")


def authority(exports, key, fams, accepted_only, dates):
    """{day: md5} -- 'the latest covering a day is that day's authority', in the order `key` gives (a stable sort of the store's order)."""
    rs = [r for r in exports if r.get("family") in fams and (r.get("_accepted") or not accepted_only)]
    auth = {}
    for r in sorted(rs, key=key):
        for d in dates(r["data"]["date_from"], r["data"]["date_to"]):
            auth[d] = r["md5"]
    return auth


def table(con, t):
    return sorted(repr(tuple(r)) for r in con.execute("SELECT * FROM %s" % t))


def main():
    ap = argparse.ArgumentParser()
    for k in ("--work", "--spine-new", "--spine-old", "--readings", "--archive", "--ingest", "--fin", "--db", "--live-db"):
        ap.add_argument(k, required=True)
    a = ap.parse_args()
    W = os.path.abspath(a.work)
    assert W.startswith("/tmp/"), "refusing a non-scratch path: %s" % W
    os.makedirs(W)
    sys.path.insert(0, a.ingest)                                        # the vendored xlrd beside the collector
    off = [p for p in ("/root/finance/_off/ALL_OFF", os.path.join(a.spine_new, "OFF"), os.path.join(a.spine_old, "OFF")) if os.path.exists(p)]
    if not check("no OFF switch is set (spine_build.py would exit 0 as 'switched off' and read like a pass): /root/finance/_off/ALL_OFF absent, "
                 "no OFF file beside either scratch copy; spine_read.py sits beside both", not off
                 and all(os.path.exists(os.path.join(d, "spine_read.py")) for d in (a.spine_new, a.spine_old)), off):
        return finish()
    RN, RO = load("marg_read_new", os.path.join(a.spine_new, "marg_read.py")), load("marg_read_old", os.path.join(a.spine_old, "marg_read.py"))
    NEW, OLD = load("spine_build_new", os.path.join(a.spine_new, "spine_build.py")), load("spine_build_old", os.path.join(a.spine_old, "spine_build.py"))
    rules = json.load(open(os.path.join(a.spine_new, "spine_rules.json")))
    live0 = {fn: md5f(os.path.join(a.readings, fn)) for fn in sorted(os.listdir(a.readings)) if fn.endswith(".json")}
    db0 = (md5f(a.live_db), os.path.getmtime(a.live_db))
    stored = {fn[:-5]: json.load(open(os.path.join(a.readings, fn))) for fn in live0}
    kept = {}
    for dp, _dn, fn in os.walk(a.archive):
        for f in fn:
            if f.lower().endswith((".xls", ".xlsx")):
                kept.setdefault(md5f(os.path.join(dp, f)), os.path.join(dp, f))
    full = {p: [m for m in stored if m.startswith(p)] for p in (SUP_WHOLE, SUP_ONE)}
    if not check("the store holds the two readings and the two SUPPLIER-grouped sheets of the same second; the server keeps both mended sheets",
                 DE in stored and F6 in stored and DE in kept and F6 in kept and all(len(v) == 1 for v in full.values()),
                 {k: len(v) for k, v in full.items()}):
        return finish()
    M_WHOLE, M_ONE = full[SUP_WHOLE][0], full[SUP_ONE][0]
    stamps = {m[:8]: (stored[m]["stamp"], stored[m]["data"].get("grouping"), len(stored[m]["data"]["lines"])) for m in (M_WHOLE, M_ONE, DE)}

    def store(name, skip=(), swap=None):
        s = os.path.join(W, name)
        os.makedirs(s)
        for fn in live0:
            if fn[:-5] not in skip:
                shutil.copy(os.path.join(a.readings, fn), os.path.join(s, fn))
        for m, rec in (swap or {}).items():
            with open(os.path.join(s, m + ".json"), "w") as fh:         # REPLACES the reading's file -- never a second file beside it
                json.dump(rec, fh)
        return s

    # ------------------------------------------------------------------------------------------------------------------ 1  the reader
    print("-- 1  the reader (S483's two edits, built by make_s484_reader.py): the two readings rewritten on a scratch copy")
    rew = {}
    for m in (DE, F6):
        rec = RN.reading_record(kept[m], stored[m]["name"])              # as spine_evidence.py writes a reading
        rec["folder"], rec["read_at"] = stored[m].get("folder", ""), dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        rew[m] = json.loads(json.dumps(rec))
    s_old, s_new = store("store_old"), store("store_new", swap=rew)
    ln = rew[DE]["data"]["lines"]
    check("%s: %d of %d lines dated, every one inside %s .. %s; ok %s (the stored reading: %d of %d)" % (
        DE[:8], sum(1 for l in ln if l["date"]), len(ln), P0, P1, rew[DE]["ok"], sum(1 for l in stored[DE]["data"]["lines"] if l["date"]),
        len(stored[DE]["data"]["lines"])), len(ln) == 208 and all(l["date"] and P0 <= l["date"] <= P1 for l in ln) and rew[DE]["ok"] is True
        and not any(l["date"] for l in stored[DE]["data"]["lines"]))
    check("%s: ok %s -> %s; %d items; data['code'] == %s" % (F6[:8], stored[F6]["ok"], rew[F6]["ok"], len(rew[F6]["data"]["items"]), rew[F6]["data"].get("code")),
          stored[F6]["ok"] is False and rew[F6]["ok"] is True and rew[F6]["failed"] == [] and len(rew[F6]["data"]["items"]) == 341
          and rew[F6]["data"].get("code") == {"OTHERS": "D98"})
    changed, same, nofam, away = [], 0, 0, collections.Counter()
    for m, st in sorted(stored.items()):
        if not st.get("family"):
            nofam += 1
        elif m not in kept:
            away[st["family"]] += 1
        elif core(RN.reading_record(kept[m], st["name"])) == core(st):
            same += 1
        else:
            changed.append(m)
    check("%d kept readings re-read by the NEW reader: %d the same family, ok and data as stored; the only two that differ are these two "
          "(not re-read here: %s; %d the spine does not use)" % (same + len(changed), same, dict(away), nofam),
          sorted(changed) == sorted([DE, F6]) and same > 100, [c[:8] for c in changed])
    so, sn = statements(os.path.join(a.spine_old, "marg_read.py")), statements(os.path.join(a.spine_new, "marg_read.py"))
    bo_, bn_ = statements(os.path.join(a.spine_old, "spine_build.py")), statements(os.path.join(a.spine_new, "spine_build.py"))
    check("the two files' source, statement by statement: marg_read.py differs in read_purchase_lines and read_grouped_list only; "
          "spine_build.py in build, the new cut_shared_bill and BUILD_VERSION only",
          sorted(k for k in set(so) | set(sn) if so.get(k) != sn.get(k)) == ["read_grouped_list", "read_purchase_lines"]
          and sorted(k for k in set(bo_) | set(bn_) if bo_.get(k) != bn_.get(k)) == sorted(
              ["build", "cut_shared_bill", 'stmt:BUILD_VERSION = "S331.1"', 'stmt:BUILD_VERSION = "S484.1"']),
          sorted(k for k in set(bo_) | set(bn_) if bo_.get(k) != bn_.get(k)))
    st_ = {}
    for side, d in (("new", a.spine_new), ("old", a.spine_old)):
        p = subprocess.run([sys.executable, "-B", "selftest_spine.py"], cwd=d, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, timeout=900)
        st_[side] = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
    check("selftest_spine.py beside the built reader AND the built spine_build.py: %s -- every check passes (the box as it is: %s)"
          % (st_["new"], st_["old"]), st_["new"].startswith("SELFTEST OK") and st_["new"] == st_["old"])

    # ------------------------------------------------------------------------------------------------------------------ 2  the order
    print("-- 2  the order of same-second exports (the three sheets stamped %s: %s)" % (stamps[DE[:8]][0], stamps))
    calls = []
    real_cut = NEW.cut_shared_bill

    def counted(lines, bills, tol_):
        r = real_cut(lines, bills, tol_)
        calls.append(dict(n=len(lines), k=len(bills), supplier=any(l.get("supplier") for l in lines), fit=r is not None,
                          key=(ubill(lines[0]["bill"]), lines[0]["date"]) if lines else None))
        return r
    NEW.cut_shared_bill = counted
    BN = NEW.build(NEW.load_readings(s_new), rules, finance_db=a.db)
    NEW.cut_shared_bill = real_cut
    calls_real = list(calls)
    BO = OLD.build(OLD.load_readings(s_new), rules, finance_db=a.db)
    exn = list(BN["exports"].values())                                  # the store's own order (file name = md5), with _accepted
    k_new_pl = lambda r: (r["stamp"], r["data"].get("grouping") == "SUPPLIER", len(r["data"]["lines"]), r["md5"])
    k_new_bw = lambda r: (r["stamp"], len(r["data"]["bills"]), r["md5"])
    k_old = lambda r: r["stamp"]
    days = list(NEW.dates(P0, P1))
    apn, apo = authority(exn, k_new_pl, PLF, False, NEW.dates), authority(exn, k_old, PLF, False, NEW.dates)
    cn, co = collections.Counter(apn[d][:8] for d in days), collections.Counter(apo[d][:8] for d in days)
    src_n = collections.Counter(l["source"][:8] for l in BN["plines"] if P0 <= l["date"] <= P1)
    src_o = collections.Counter(l["source"][:8] for l in BO["plines"] if P0 <= l["date"] <= P1)
    check("NEW order (stamp, SUPPLIER-grouped, number of lines, md5): the authority of every day %s .. %s for purchase lines -- %d days -> %s, "
          "%d -> %s, %d -> %s; and the NEW build's own purchase lines of that period all come from %s (%s)"
          % (P0, P1, cn.get(SUP_WHOLE, 0), SUP_WHOLE, cn.get(DE[:8], 0), DE[:8], cn.get(SUP_ONE, 0), SUP_ONE, SUP_WHOLE, dict(src_n)),
          len(days) == 33 and cn == {SUP_WHOLE: 33} and set(src_n) == {SUP_WHOLE}, (dict(cn), dict(src_n)))
    check("negative control, OLD spine_build.py (ce99bedf, stamp alone -> the store's md5 order) on the same store: %s for the same %d days; "
          "its build takes that period's lines from %s (%s)" % (dict(co), len(days), DE[:8], dict(src_o)),
          co == {DE[:8]: 33} and set(src_o) == {DE[:8]}, (dict(co), dict(src_o)))
    moved_pl = sorted(d for d in apn if apn[d] != apo.get(d))
    abn, abo = authority(exn, k_new_bw, ("PURCHASE_BILLWISE",), True, NEW.dates), authority(exn, k_old, ("PURCHASE_BILLWISE",), True, NEW.dates)
    moved_bw = sorted(d for d in abn if abn[d] != abo.get(d))
    eq_bw = [s for s, c in collections.Counter(r["stamp"] for r in exn if r.get("family") == "PURCHASE_BILLWISE" and r.get("_accepted")).items() if c > 1]
    check("days whose authority moved under the new keys: purchase lines %d (exactly the %d days above, nothing outside them); bill-wise "
          "exports %d (expected 0 -- %d bill-wise stamps are shared by two exports)" % (len(moved_pl), len(days), len(moved_bw), len(eq_bw)),
          moved_pl == days and moved_bw == [] and BN["pbills"].keys() == BO["pbills"].keys(), (moved_pl[:2], moved_bw[:5]))

    # ------------------------------------------------------------------------------------------------------------------ 3  the tie
    print("-- 3  the tie of a shared bill number (bill 160 of 01-Sep in %s)" % DE[:8])
    g = [l for l in rew[DE]["data"]["lines"] if ubill(l["bill"]) == "160" and l["date"] == P0]
    cb = [b for (sk, bill, d), b in BN["pbills"].items() if ubill(bill) == "160" and d == P0]
    fit = NEW.cut_shared_bill(g, cb, tol) if hasattr(NEW, "cut_shared_bill") else None
    runs = collections.OrderedDict()
    for i in sorted(fit or {}):
        runs.setdefault(id(fit[i]), [fit[i], []])[1].append(g[i])
    for b, ls in runs.values():
        print("         run: %d line(s), net %s = Rs %.2f  ->  the bill of Rs %.2f (supplier %s..., %s)   %s"
              % (len(ls), " + ".join("%.2f" % (l["net_amount_p"] / 100.0) for l in ls), sum(l["net_amount_p"] for l in ls) / 100.0,
                 abs(b["amount_p"]) / 100.0, NEW.supnorm(b["supplier"])[:4], b["direction"], [l["name"][:14] for l in ls]))
    rr = [(len(ls), sum(l["net_amount_p"] for l in ls), abs(b["amount_p"])) for b, ls in runs.values()]
    check("cut_shared_bill on the five lines and the two bills numbered 160 of 01-Sep: exactly one cutting fits -- run 1 = 5,376.68 -> the "
          "Rs 5,377.00 bill; run 2 = 2,400.00 + 880.00 + 3,200.00 + 5,920.00 = 12,400.00 -> the Rs 12,400.00 bill (the whole sum, Rs %.2f, "
          "is no bill's)" % (sum(l["net_amount_p"] for l in g) / 100.0),
          len(g) == 5 and len(cb) == 2 and rr == [(1, 537668, 537700), (4, 1240000, 1240000)], rr)
    hard_o = BO["G"].rows[[r[0] for r in BO["G"].rows].index(G_PUR)]
    check("negative control, OLD: no cut_shared_bill; its build leaves those five lines tied to no bill and its gate line fails (%s)"
          % hard_o[3][:9], not hasattr(OLD, "cut_shared_bill") and hard_o[2] == 0 and hard_o[3].startswith("5 lines") and "'160'" in hard_o[3])
    # end to end, where the BILL-grouped sheet IS the only export of its period: the same store without the two SUPPLIER sheets of that second
    s_bill = store("store_bill_only", skip=(M_WHOLE, M_ONE), swap=rew)
    BB = NEW.build(NEW.load_readings(s_bill), rules, finance_db=a.db)
    BBo = OLD.build(OLD.load_readings(s_bill), rules, finance_db=a.db)
    five = [l for l in BB["plines"] if ubill(l["bill"]) == "160" and l["date"] == P0]
    by_sup = sorted(collections.Counter(l["supkey"][:4] for l in five).items(), key=lambda x: x[1])
    pur_b = BB["G"].rows[[r[0] for r in BB["G"].rows].index(G_PUR)]
    pur_bo = BBo["G"].rows[[r[0] for r in BBo["G"].rows].index(G_PUR)]
    check("end to end, a scratch store WITHOUT the two SUPPLIER sheets (so %s is the authority of the period, as a BILL-grouped sheet may "
          "be): the NEW build ties all its lines -- the gate line passes, the whole gate passes, and the five lines are purchase lines "
          "under their two suppliers %s; the OLD build on that store fails the line on 5 lines" % (DE[:8], by_sup),
          pur_b[2] == 1 and BB["G"].passed and len(five) == 5 and [c for _s, c in by_sup] == [1, 4] and {l["source"] for l in five} == {DE}
          and pur_bo[2] == 0 and pur_bo[3].startswith("5 lines"), (pur_b[3][:60], pur_bo[3][:40]))
    # who reaches the helper, on the real store
    one_cand = sup_lines = two_cand = 0
    for r in exn:
        if r.get("family") not in PLF:
            continue
        if r["data"].get("grouping") == "SUPPLIER":
            sup_lines += len(r["data"]["lines"])
            continue
        seen = set()
        for l in r["data"]["lines"]:
            k = (ubill(l["bill"]), l["date"])
            if k in seen:
                continue
            seen.add(k)
            nb = len([1 for (sk, bill, d) in BN["pbills"] if ubill(bill) == k[0] and d == k[1]])
            one_cand += nb == 1
            two_cand += nb >= 2
    check("(c) a group with ONE candidate bill never reaches the helper: %d such groups in the BILL-grouped sheets of the store, %d groups "
          "with two or more bills, %d calls in the whole build -- every one with two or more bills (%s)"
          % (one_cand, two_cand, len(calls_real), sorted({(c["key"], c["k"], c["fit"]) for c in calls_real})),
          one_cand > 0 and len(calls_real) >= 1 and all(c["k"] >= 2 for c in calls_real) and len(calls_real) <= two_cand, len(calls_real))
    check("(d) a SUPPLIER-grouped line never reaches it: %d lines in the SUPPLIER-grouped sheets, 0 calls carried a line with a supplier"
          % sup_lines, sup_lines > 1000 and not any(c["supplier"] for c in calls_real))
    check("    the cap: no group of the store has more than 24 lines or more than 4 bills (largest call: %d lines, %d bills)"
          % (max([c["n"] for c in calls_real] or [0]), max([c["k"] for c in calls_real] or [0])), all(c["n"] <= 24 and c["k"] <= 4 for c in calls_real))
    L = lambda *nets: [dict(net_amount_p=x, bill="W484", date="2030-01-01", name="W484 ITEM %d" % i, supplier="") for i, x in enumerate(nets)]
    Bl = lambda *amts: [dict(amount_p=x, supplier="W484 SUPPLIER %s" % chr(65 + i), bill="W484", date="2030-01-01", direction="PURCHASE") for i, x in enumerate(amts)]
    b2 = Bl(537700, 1240000)
    f1 = NEW.cut_shared_bill(L(537668, 240000, 88000, 320000, 592000), b2, tol)
    f2 = NEW.cut_shared_bill(L(537668, 240000, 88000, 320000, 592000), b2[::-1], tol)
    f3 = NEW.cut_shared_bill(L(240000, 88000, 320000, 592000, 537668), b2, tol)
    check("invented rows through cut_shared_bill itself: the shape of today's five lines ties 1 + 4; the bills given in the other order tie "
          "the same way; the bigger bill's lines printed first tie 4 + 1",
          f1 is not None and [f1[i] is b2[0] for i in range(5)] == [True, False, False, False, False]
          and f2 is not None and [f2[i] is b2[0] for i in range(5)] == [True, False, False, False, False]
          and f3 is not None and [f3[i] is b2[1] for i in range(5)] == [True, True, True, True, False])
    check("(a) two candidate bills of EQUAL amount, lines that fit either way -> two fits -> None: every line stays untied",
          NEW.cut_shared_bill(L(100000, 100000), Bl(100000, 100000), tol) is None)
    check("(b) lines whose runs fit no cutting -> None: untied", NEW.cut_shared_bill(L(30000, 30000, 30000), Bl(50000, 70000), tol) is None
          and NEW.cut_shared_bill(L(120000), Bl(50000, 70000), tol) is None)
    t0 = time.time()
    cap25 = NEW.cut_shared_bill(L(*([50000] + [1000] * 24)), Bl(50000, 24000), tol)        # it WOULD fit one way: the cap answers first
    cap5 = NEW.cut_shared_bill(L(10000, 20000, 30000, 40000, 50000), Bl(10000, 20000, 30000, 40000, 50000), tol)
    took = time.time() - t0
    in24 = NEW.cut_shared_bill(L(*([50000] + [1000] * 23)), Bl(50000, 23000), tol)
    in4 = NEW.cut_shared_bill(L(10000, 20000, 30000, 40000), Bl(40000, 30000, 20000, 10000), tol)
    check("(e) the cap: 25 lines, or 5 bills -> None at once (%.4f s; both groups WOULD fit exactly one way, so it is the cap that answers, "
          "not the search); 24 lines and 4 bills are still cut" % took, cap25 is None and cap5 is None and took < 0.05 and in24 is not None
          and len(in24) == 24 and in4 is not None and [abs(in4[i]["amount_p"]) for i in range(4)] == [10000, 20000, 30000, 40000])

    # ------------------------------------------------------------------------------------------------------------------ 4  the gate
    print("-- 4  the gate: spine_build.py's own main() on scratch stores, to scratch --out files")
    NN = run_build(a.spine_new, s_new, os.path.join(W, "b_new_new", "spine.db"), a.db)
    ON = run_build(a.spine_old, s_new, os.path.join(W, "b_old_new", "spine.db"), a.db)
    NO = run_build(a.spine_new, s_old, os.path.join(W, "b_new_old", "spine.db"), a.db)
    OO = run_build(a.spine_old, s_old, os.path.join(W, "b_old_old", "spine.db"), a.db)
    check("NEW spine_build.py + NEW readings: %s of the blocking lines, '%s' (exit %s) -- on the scratch copy"
          % (NN["state"].get("gate"), NN["tail"][:23], NN["rc"]), passed(NN) and NN["state"].get("gate") == "13/13"
          and [NN["rows"].get(x) for x in (G_PUR, G_SALE, G_CAT)] == ["ok", "ok", "ok"], (NN["rc"], NN["fails"], NN["tail"][:50]))
    print("         the non-blocking line '%s': %s" % (G_ADD, NN["detail"].get(G_ADD, "")[:160]))
    check("negative control, OLD build + NEW readings: GATE FAILED (exit 3) on the purchase-lines line alone -- %s, bill number %s "
          "(REPORT_S483's finding, reproduced)" % (ON["detail"].get(G_PUR, "")[:7], sorted(set(re.findall(r"\.XLS', '([^']*)', '", ON["detail"].get(G_PUR, "").split(" | ")[0])))),
          ON["rc"] == 3 and ON["fails"] == [G_PUR] and ON["detail"].get(G_PUR, "").startswith("5 lines") and not ON["swapped"], (ON["rc"], ON["fails"]))
    check("negative control, NEW build + OLD readings: GATE FAILED (exit 3) on the category-list line alone -- E.2 is still needed",
          NO["rc"] == 3 and NO["fails"] == [G_CAT] and not NO["swapped"], (NO["rc"], NO["fails"]))
    check("the box as it is, OLD build + OLD readings: GATE FAILED on both lines (%s on the purchase line), as spine.log says today"
          % OO["detail"].get(G_PUR, "")[:9], OO["rc"] == 3 and OO["fails"] == sorted([G_CAT, G_PUR]), (OO["rc"], OO["fails"]))
    others = [k for k in NN["rows"] if k not in (G_PUR, G_CAT)]
    check("every other gate line reads the same in all four builds (%d lines); none was 'switched off'" % len(others),
          all(set(b["rows"]) == set(NN["rows"]) and all(b["rows"][k] == NN["rows"][k] for k in others) and not b["off"] for b in (ON, NO, OO)),
          [(k, [b["rows"].get(k) for b in (NN, ON, NO, OO)]) for k in others if len({b["rows"].get(k) for b in (NN, ON, NO, OO)}) > 1])

    # ------------------------------------------------------------------------------------------------------------------ 5  F-737
    print("-- 5  F-737 measured, not mended: a one-supplier print exported AFTER the whole one")
    late = dict(stored[M_ONE])
    s9 = stored[M_WHOLE]["stamp"]
    late["stamp"] = (dt.datetime.strptime(s9, "%Y%m%d-%H%M%S") + dt.timedelta(seconds=1)).strftime("%Y%m%d-%H%M%S")
    s_f = store("store_f737", swap=dict(rew, **{M_ONE: late}))
    BF = NEW.build(NEW.load_readings(s_f), rules, finance_db=a.db)
    af = authority(list(BF["exports"].values()), k_new_pl, PLF, False, NEW.dates)
    cf = collections.Counter(af[d][:8] for d in days)
    n_before = sum(1 for l in BN["plines"] if P0 <= l["date"] <= P1)
    n_after = sum(1 for l in BF["plines"] if P0 <= l["date"] <= P1)
    FF = run_build(a.spine_new, s_f, os.path.join(W, "b_f737", "spine.db"), a.db)
    check("with %s's stamp moved one second after %s's (%s -> %s; a copy of the store, the reading's file replaced): the NEW order makes "
          "the one-supplier print the authority for all %d days, the build's purchase lines of %s .. %s fall from %d to %d -- and the gate "
          "STILL PASSES (%s, swapped on the scratch copy). F-737 is real and is not mended by this kit"
          % (SUP_ONE, SUP_WHOLE, s9, late["stamp"], cf.get(SUP_ONE, 0), P0, P1, n_before, n_after, FF["state"].get("gate")),
          cf == {SUP_ONE: 33} and n_before > 100 and n_after == len(stored[M_ONE]["data"]["lines"]) == 5 and passed(FF), (dict(cf), n_before, n_after, FF["rc"]))
    print("         the non-blocking re-add line in that build: %s   (in the true build: %s)"
          % (FF["detail"].get(G_ADD, "")[:60], NN["detail"].get(G_ADD, "")[:60]))
    check("the stores of the other sections were never changed by this one (the F-737 store is its own copy; %s's reading in the walk's "
          "main store is the live one, byte for byte)" % SUP_ONE, md5f(os.path.join(s_new, M_ONE + ".json")) == live0[M_ONE + ".json"])

    # ------------------------------------------------------------------------------------------------------------------ 6  the two spines
    print("-- 6  the new spine.db (scratch) against the last good one (%s, opened read only)"
          % dt.datetime.fromtimestamp(db0[1]).strftime("%Y-%m-%d %H:%M:%S"))
    old = sqlite3.connect("file:%s?mode=ro" % a.live_db, uri=True)
    new = sqlite3.connect("file:%s?mode=ro" % NN["db"], uri=True)
    tabs = [r[0] for r in old.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    had = {r[0] for r in old.execute("SELECT md5 FROM sp_export")}
    # 6a: the NEW build on the evidence the last good build had -> the same spine, row for row
    s_then = store("store_then", skip=[m for m in stored if m not in had])
    TH = run_build(a.spine_new, s_then, os.path.join(W, "b_then_new", "spine.db"), a.db)
    THo = run_build(a.spine_old, s_then, os.path.join(W, "b_then_old", "spine.db"), a.db)
    then, then_o = sqlite3.connect("file:%s?mode=ro" % TH["db"], uri=True), sqlite3.connect("file:%s?mode=ro" % THo["db"], uri=True)

    def differ(c1, c2):
        """The tables in which two spines are not the same rows (sp_meta but for built / build_version / readings; sp_gate by its verdicts:
        some gate lines word their detail in an order that changes from one run to the next, under the old file too)."""
        out = []
        for t in tabs:
            if t == "sp_meta":
                x, y = [dict((k, v) for k, v in c.execute("SELECT key, value FROM sp_meta") if k not in ("built", "build_version", "readings")) for c in (c1, c2)]
                same_ = x == y
            elif t == "sp_gate":
                same_ = [r for r in c1.execute("SELECT n, name, blocking, ok FROM sp_gate ORDER BY n")] == [r for r in c2.execute("SELECT n, name, blocking, ok FROM sp_gate ORDER BY n")]
            else:
                same_ = table(c1, t) == table(c2, t)
            if not same_:
                out.append(t)
        return out
    info = lambda c: int(re.search(r"\(information\): (\d+)", dict(c.execute("SELECT name, detail FROM sp_gate"))[G_PUR]).group(1))
    d_live, d_code = differ(old, then_o), differ(then, then_o)
    check("6a  the evidence the last good build had (%d readings of the store's %d), built again on scratch by the OLD file: that spine, row "
          "for row, in every table -- %s -- so the scratch store IS that evidence" % (len(had & set(stored)), len(stored),
          ", ".join("%s %d" % (t, old.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]) for t in tabs)), passed(THo) and not d_live, (THo["rc"], d_live))
    check("    the NEW spine_build.py on the same evidence: it builds 13/13 and every table is the same rows as the OLD file's -- on what the "
          "spine held at 08:00 the new rules move no row. One gate detail differs, as it should: lines of superseded exports tied to no "
          "bill (information) %d -> %d -- the five lines of bill 160 in Marg's own BILL-grouped sheet of 06-Sep now find their two bills"
          % (info(then_o), info(then)), passed(TH) and not d_code and info(then_o) - info(then) == 5, (TH["rc"], TH["fails"], d_code))
    then.close()
    then_o.close()
    # 6b: what the readings since then bring
    since = {r[0]: r[1] for r in new.execute("SELECT md5, family FROM sp_export") if r[0] not in had}
    fam_since = collections.Counter(v or "(not used)" for v in since.values())
    gone = [r[0] for r in old.execute("SELECT md5 FROM sp_export") if r[0] not in {x[0] for x in new.execute("SELECT md5 FROM sp_export")}]
    okmoved = [m for m, ok in old.execute("SELECT md5, ok FROM sp_export") if dict(new.execute("SELECT md5, ok FROM sp_export")).get(m) != ok]
    check("6b  sp_export: %d rows then, %d now -- %d readings arrived since that build (%s); no export left; the `ok` of every export "
          "both hold is the same" % (len(had), len(had) + len(since), len(since), dict(fam_since)), not gone and not okmoved and len(since) > 0,
          (gone[:3], okmoved[:3]))
    per = {}
    for m in since:
        r = stored.get(m) or {}
        if r.get("family") in PLF or r.get("family") == "PURCHASE_BILLWISE":
            k = "L" if r["family"] in PLF else "B"
            per.setdefault(k, []).append((r["data"]["date_from"], r["data"]["date_to"]))
    inside = lambda d, k: any(x <= d <= y for x, y in per.get(k, []))
    unexplained, counts = [], {}
    for t, dcol, k, pk in (("sp_purchase_line", "date", "L", None), ("sp_purchase_bill", "date", "B", ("supkey", "bill", "date")),
                           ("sp_sale_bill", "date", None, ("date", "bill")), ("sp_close", "as_on", None, ("as_on", "k20"))):
        o_rows = {repr(tuple(r)): r for r in old.execute("SELECT * FROM %s" % t)}
        n_rows = {repr(tuple(r)): r for r in new.execute("SELECT * FROM %s" % t)}
        ci = [c[1] for c in old.execute("PRAGMA table_info(%s)" % t)]
        added = [n_rows[x] for x in set(n_rows) - set(o_rows)]
        removed = [o_rows[x] for x in set(o_rows) - set(n_rows)]
        key = (lambda r: tuple(r[ci.index(c)] for c in pk)) if pk else (lambda r: None)
        again = {key(r) for r in added} if pk else set()
        bad_add = [r for r in added if r[ci.index("source_md5")] not in since]
        bad_rem = [r for r in removed if not ((k and inside(r[ci.index(dcol)], k)) or (pk and key(r) in again))]
        counts[t] = (old.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0], new.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0], len(added), len(removed))
        if bad_add or bad_rem:
            unexplained.append((t, len(bad_add), len(bad_rem)))
    check("    the tables that carry their source (rows then -> now, +added, -removed): %s -- every added row comes from a reading that "
          "arrived since; every removed row is a purchase line or bill of a period a newer export of its kind now covers, or the same "
          "bill / closing figure printed again by a newer export"
          % ", ".join("%s %d -> %d (+%d, -%d)" % ((t,) + counts[t]) for t in counts), not unexplained, unexplained)
    mo = lambda c: collections.OrderedDict(c.execute("SELECT substr(date,1,7), COUNT(*) FROM sp_purchase_line GROUP BY 1 ORDER BY 1"))
    mo_o, mo_n = mo(old), mo(new)
    src_p = collections.Counter(r[0][:8] for r in new.execute("SELECT source_md5 FROM sp_purchase_line WHERE date BETWEEN ? AND ?", (P0, P1)))
    src_po = collections.Counter(r[0][:8] for r in old.execute("SELECT source_md5 FROM sp_purchase_line WHERE date BETWEEN ? AND ?", (P0, P1)))
    print("         sp_purchase_line by month, then: %s" % dict(mo_o))
    print("         sp_purchase_line by month, now : %s" % dict(mo_n))
    check("    the purchase lines of %s .. %s: then %d, from %s; now %d, every one from %s (the SUPPLIER-grouped sheet's %d lines) -- none "
          "from %s; the months before September are the same, month for month"
          % (P0, P1, sum(src_po.values()), dict(src_po), sum(src_p.values()), SUP_WHOLE, len(stored[M_WHOLE]["data"]["lines"]), DE[:8]),
          set(src_p) == {SUP_WHOLE} and sum(src_p.values()) == len(stored[M_WHOLE]["data"]["lines"]) == 208
          and all(mo_o[m] == mo_n.get(m) for m in mo_o if m < "2026-09"), (dict(src_p), dict(src_po)))
    b160 = [r for r in new.execute("SELECT supkey, COUNT(*), SUM(net_amount_p) FROM sp_purchase_line WHERE date=? AND ltrim(bill,'0')='160' GROUP BY supkey ORDER BY 2", (P0,))]
    pb160 = sorted(abs(r[0]) for r in new.execute("SELECT amount_p FROM sp_purchase_bill WHERE date=? AND ltrim(bill,'0')='160'", (P0,)))
    check("    the five lines of bill 160 of 01-Sep are in sp_purchase_line under their two bills: %s against the bills %s"
          % ([(s[:4], c, "%.2f" % (v / 100.0)) for s, c, v in b160], ["%.2f" % (x / 100.0) for x in pb160]),
          [(c, v) for _s, c, v in b160] == [(1, 537668), (4, 1240000)] and pb160 == [537700, 1240000])
    same_tabs = [t for t in ("sp_alias", "sp_recon") if table(old, t) == table(new, t)]
    derived = {t: (old.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0], new.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0])
               for t in tabs if t not in counts and t not in ("sp_alias", "sp_recon", "sp_export")}
    check("    sp_alias and sp_recon (the rules' own tables) are the same; the items: sp_item %d -> %d. The tables worked out from the above "
          "(rows then -> now): %s" % (derived["sp_item"][0], derived["sp_item"][1], ", ".join("%s %d -> %d" % (t, v[0], v[1]) for t, v in derived.items() if t != "sp_item")),
          same_tabs == ["sp_alias", "sp_recon"] and derived["sp_item"][1] >= derived["sp_item"][0])
    meta = dict(new.execute("SELECT key, value FROM sp_meta"))
    check("    sp_meta records the build: build_version %s (then: %s)" % (meta.get("build_version"), dict(old.execute("SELECT key, value FROM sp_meta")).get("build_version")),
          meta.get("build_version") == "S484.1")
    old.close()
    new.close()
    live1 = {fn: md5f(os.path.join(a.readings, fn)) for fn in sorted(os.listdir(a.readings)) if fn.endswith(".json")}
    check("the walk wrote nothing live: every reading it read at its start is byte for byte as it was; spine.db is the same file (md5 %s)"
          % db0[0][:8], all(live1.get(k) == v for k, v in live0.items()) and md5f(a.live_db) == db0[0])
    return finish()


def finish():
    if FAILS:
        print("WALK_S484 RED -- %d of %d checks failed:" % (len(FAILS), N[0]))
        for f in FAILS:
            print("   - " + f[:200])
        return 1
    print("WALK_S484 GREEN -- %d checks" % N[0])
    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
