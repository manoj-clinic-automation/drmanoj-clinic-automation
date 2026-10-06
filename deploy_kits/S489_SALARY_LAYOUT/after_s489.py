#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
after_s489.py -- kit S489_SALARY_LAYOUT: read the engine AS PLACED, once, read-only. Run by the installer
after the service has restarted (red -> the installer puts the old engine back), and safe to run by hand
at any time:   /root/wa/venv/bin/python3 -B after_s489.py        (it need not be run; it changes nothing)

It loads /root/staff_register/salary_policy.py itself -- not a copy -- and holds, for each month asked:
  * the engine is 1.17-S489 and reads the kit's loan record (loan_pages.json) beside it, whole
  * the staff ledger holds the restatement row exactly once
  * the private-loan person's shown salary, advance and net are what the ledger's own lines give when
    worked out HERE (walk_s489.want_private -- not taken from the engine):
        salary = full salary - the instalment kept aside · net = full net - what the private page pays
  * his loan page, row by row and as printed, is what the ledger's RAW rows and the history record give
    (walk_s489.loan_page_checks), carries no 'Check' note, and ends on the ledger's own balance
  * Sheet 2 has its three advance tables; the common pages do not show the private loan
NO RUPEE FIGURE IS PRINTED (F-31).   env ROOT (default /root) · MONTHS (default 2026-09,<this month>)
"""
import os, sys, sqlite3, shutil, tempfile, datetime, importlib.util

sys.dont_write_bytecode = True


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def main():
    ROOT = os.path.abspath(os.environ.get("ROOT", "/root"))
    kit = os.path.dirname(os.path.abspath(__file__))
    live = os.path.join(ROOT, "staff_register")
    os.environ["ATT_DIR"] = ROOT
    os.environ.setdefault("LEDGER_DIR", os.path.join(ROOT, "staff_ledger"))
    os.environ.setdefault("STAFF_CSV", os.path.join(ROOT, "staff_master.csv"))
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    W = load(os.path.join(kit, "walk_s489.py"), "walk_s489")       # its helpers only; the walk itself is not run
    check = W.check
    scratch = tempfile.mkdtemp(prefix="s489_after_", dir="/tmp")
    try:
        dbp = os.path.join(scratch, "sr_after.db")
        live_db = os.path.join(live, "staff_register.db")
        if os.path.isfile(live_db):
            s = sqlite3.connect("file:%s?mode=ro" % live_db, uri=True)
            d = sqlite3.connect(dbp)
            s.backup(d); d.close(); s.close()
        os.environ["SR_DB_PATH"] = dbp
        os.environ["ATT_REGISTER_DB"] = dbp
        P = load(os.path.join(live, "salary_policy.py"), "sp_placed_s489")
        check("the placed engine is 1.17-S489", getattr(P, "VERSION", "") == "1.17-S489")
        D = load(os.path.join(kit, "data_s489.py"), "data_s489")
        check("loan_pages.json beside the engine holds the kit's record",
              D.main(["data", "--check", P.LOAN_PAGES_PATH]) == 0)
        lp = P.loan_pages()
        check("the engine reads the record whole: every group and every private loan history",
              len(lp["groups"]) == len(D.RECORD["groups"]) and len(lp["history"]) == len(D.RECORD["history"]))
        RS = load(os.path.join(kit, "restate_s489.py"), "restate_s489")
        import staff_ledger as L
        raw = L.load_ledger()
        mine = [r for r in raw if r.get("restate") == RS.TAG]
        check("the staff ledger holds the restatement row exactly once",
              len(mine) == 1 and mine[0]["amount"] == RS.AMOUNT and mine[0]["contra_of"] == RS.LOAN_ID
              and mine[0]["category"] == "LOAN_CAPITALISE" and mine[0]["status"] == "APPROVED")
        today = datetime.date.today().strftime("%Y-%m")
        months = sorted(set(m for m in os.environ.get("MONTHS", "2026-09,%s" % today).split(",") if m))
        privn = P.private_loan_names(P.load_settings())
        seen = 0
        for ym in months:
            res = P.compute(ym)
            closed = bool(res["ledger_closed"])
            s2 = P.sheet2_html(res, doors=True, prefix="/register")
            s34 = P.sheets34_html(res, approved=True, prefix="/register")
            check("%s: Sheet 2 has its three advance tables and no warning note of its own" % ym,
                  "1 · This month's advances" in s2 and "2 · Instalment loans" in s2
                  and "3 · What each salary bears" in s2 and "Does not add up" not in s2
                  and "could not be laid out" not in s2)
            check("%s: no SHEET 5 is written" % ym, "SHEET 5" not in s34)
            for st in res["staff"]:
                if str(st["name"]).strip().lower() not in privn or not st.get("priv"):
                    continue
                priv = st["priv"]
                lines = [dict(t, inst_raw=W.raw_instalment(raw, t["id"])) for t in (st["ledger_money"] or {}).get("lines", [])]
                want = W.want_private(lines, closed)
                check("%s: the long-term loan, worked out here from the ledger's lines, is the one on his private page" % ym,
                      want is not None and want["kept"] > 0 and sorted(t["id"] for t in priv["lines"]) == want["ids"])
                check("%s: he is on the common sheet at salary less the instalment kept aside" % ym,
                      abs(st["base"] - (st["base_full"] - want["kept"])) < 0.005 and st["base"] < st["base_full"])
                check("%s: common advance = the ledger's figure less the long-term instalment it took" % ym,
                      abs(st["adv_ded"] - (st["adv_ded_full"] - want["cut_shown"])) < 0.005)
                check("%s: common net = the full net less what the private page pays" % ym,
                      abs(st["net"] - (st["net_full"] - want["reserve"])) < 0.005)
                seen += W.loan_page_checks(ym, st, res, P, raw, RS.LOAN_ID)
                secret = set()
                for t in priv["lines"]:
                    for x in (t["end"], t["start"], t["amount"]):
                        if x >= 50000:
                            secret.add(P.inr(x)); secret.add(P.money(x))
                check("%s: the common pages do not show the private loan" % ym,
                      not any(W.shows(s2, x) or W.shows(s34, x) for x in secret))
        check("the private loan page was read against the raw ledger", seen >= 1)
        print("AFTER OK — %d checks; %d month(s); engine 1.17-S489 as placed; the restatement row is in the ledger once"
              % (W.N[0], len(months)))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    main()
