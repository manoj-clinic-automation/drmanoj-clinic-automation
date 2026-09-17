#!/usr/bin/env python3
"""test_s303.py -- S303 (F-519) offline proof, with the REAL salary_policy.sheets34_html writing the frozen
report exactly as a lock does. Throwaway database under /tmp; nothing live is read or written.
Usage: python3 test_s303.py <dir holding the kit staff_register.py> <dir holding salary_policy.py>"""
import copy
import os
import sqlite3
import sys
import tempfile
import types

N = [0]


def check(name, cond):
    N[0] += 1
    if not cond:
        print("FAIL %d: %s" % (N[0], name))
        sys.exit(1)


def person(name, base, net, prior=0.0, adv=0.0):
    return {"uid": 1, "name": name, "base": base, "exempt": False, "offs": 2, "shift_min": 600, "rate": 0.05,
            "present": 25, "absent": 1, "absent_excl": 1, "leave_in_absent": 0, "night_rs": 0.0, "extra_rs": 0.0,
            "extra_days": 0, "outst_rs": 0.0, "outst_days": 0, "ot_min": 0, "ot_rs": 0.0, "ot_paid": 0.0,
            "duty_credits": 0.0, "genuine": 1, "disc": 0, "fest": 0, "leaves_total": 1, "leave_amt": -150.5,
            "marks": 1, "grace_days": 0, "late_min": 40, "late_charge": 100.0, "collect": 25.0, "held": 75.0,
            "prev_min": 50, "release": 0.0, "release_note": "", "prior_collect": prior, "leaves_weighted": 1,
            "fine_uninf": 0, "fine_exc": 0, "dress_days": 0, "icard_days": 0, "dress_rs": 0.0, "icard_rs": 0.0,
            "incentive": 120.33, "inc_tier": "FULL", "advances_month": [], "loans": [], "open_bal": 0.0,
            "adv_ded": adv, "manual_adv": 0.0, "ledger_money": {"start": 0, "taken": 0, "recovered": 0,
                                                                  "interest": 0, "end": 0, "lines": [],
                                                                  "deducted": adv},
            "grid": {}, "absent_dates": [], "leave_dates": set(), "net": net, "net_exact": net + 3.2,
            "net_round_off": 3.2}


def main():
    kit, pol = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    sys.path.insert(0, pol)
    import salary_policy as P
    s = P.load_settings()
    staff = [person("Alisha", 9000, 4170 - 530, prior=526.25), person("Amir Sohail", 2500, 2500),
             person("Darpan", 15000, -1940, adv=20000), person("Pravesh", 3000, 2820),
             person("Vikki", 6000, 4700)]
    res = {"ym": "2026-08", "settings": s, "staff": staff, "enforced": True, "ledger_closed": True, "notes": []}
    total = int(round(sum(x["net"] for x in staff)))
    report = P.sheets34_html(res, approved=True, prefix="/register")
    tmp = tempfile.mkdtemp(prefix="s303_")
    os.environ["SR_DB_PATH"] = os.path.join(tmp, "sr.db")
    sys.path.insert(0, kit)
    os.chdir(tmp)
    import staff_register as sr
    check("kit copy imported", os.path.dirname(os.path.abspath(sr.__file__)) == kit)
    # ---- the reader ------------------------------------------------------------------------
    snap, why = sr.locked_snapshot(report, total)
    check("the frozen report reads back: " + why, snap is not None)
    check("all five people, Darpan from his own sheet", sorted(r["name"] for r in snap) ==
          ["Alisha", "Amir Sohail", "Darpan", "Pravesh", "Vikki"] and [r for r in snap if r["own"]][0]["name"].lower() == "darpan")
    check("every NET exact", {r["name"]: r["vals"]["net"] for r in snap} ==
          {"Alisha": 3640.0, "Amir Sohail": 2500.0, "Darpan": -1940.0, "Pravesh": 2820.0, "Vikki": 4700.0})
    al = [r for r in snap if r["name"] == "Alisha"][0]["vals"]
    check("Sheet 3 columns land on their fields", al["prior_collect"] == 526.25 and al["leave_amt"] == -150.5
          and al["incentive"] == 120.33 and al["held"] == 75.0)
    check("a wrong locked total is refused", sr.locked_snapshot(report, total + 10)[0] is None)
    check("a report with no Sheet 3 is refused", sr.locked_snapshot("<html>nothing</html>", total)[0] is None)
    check("a damaged figure is refused", sr.locked_snapshot(report.replace("<td class='n'>3640</td>", "<td class='n'>x</td>", 1), total)[0] is None)
    # ---- the differences -------------------------------------------------------------------
    now = copy.deepcopy(staff)
    now = [x for x in now if x["name"] != "Pravesh"]                       # made inactive
    for x in now:
        if x["name"] == "Alisha":
            x["prior_collect"], x["net"] = 0.0, 4170                        # the lock closed her hold
        if x["name"] == "Darpan":
            x["net"], x["adv_ded"] = -1120, 19180                          # ledger corrected
    d = {x["name"]: x for x in sr.locked_differences(snap, now, P.money)}
    check("three differ, Amir and Vikki do not", sorted(d) == ["Alisha", "Darpan", "Pravesh"])
    check("Alisha: the hold is named", "Prev hold deducted 526.25 → 0" in d["Alisha"]["moved"] and d["Alisha"]["diff"] == "530")
    check("Pravesh: no longer computed", d["Pravesh"]["today"] == "not in today's recompute")
    check("Darpan: own sheet, only NET frozen", d["Darpan"]["diff"] == "820" and "own sheet" in d["Darpan"]["moved"])
    # ---- the desk --------------------------------------------------------------------------
    sr.init_db()
    con = sqlite3.connect(os.environ["SR_DB_PATH"])
    con.execute("INSERT INTO locked_run(ym,total_payout,report_html,locked_by,locked_ts,status) VALUES (?,?,?,?,?,'locked')",
                ("2026-08", total, report, "manoj", "2026-09-13 12:44:38"))
    con.commit()
    fake = types.SimpleNamespace(compute=lambda ym: {"ym": ym, "staff": copy.deepcopy(now), "enforced": True},
                                 money=P.money, load_settings=P.load_settings)
    sr._policy_module = lambda: (fake, "")
    c = sr.app.test_client()
    with c.session_transaction() as ss:
        ss["sr_user"], ss["sr_role"] = "manoj", "override"
    t = c.get("/register/salary?ym=2026-08").get_data(as_text=True)
    now_total = "{:,}".format(int(round(sum(x["net"] for x in now))))
    card = "{:,}".format(total)
    check("desk 200 with the card", "TOTAL PAYOUT &#8377;%s" % card in t)
    check("the table is the locked one and its TOTAL is the card's", "The locked table" in t and "<td><b>%s</b></td></tr>" % card in t)
    check("today's recompute total is NOT shown", "<b>%s</b>" % now_total not in t)
    check("the differences are listed", "Today's recompute differs for 3 staff" in t and "Prev hold deducted 526.25 → 0" in t)
    check("Pravesh is in the locked table", "<b>Pravesh</b>" in t)
    r = c.get("/register/salary/locked?ym=2026-08")
    check("the frozen sheets open as saved", r.status_code == 200 and r.get_data(as_text=True) == report)
    check("an unlocked month has no frozen sheets", c.get("/register/salary/locked?ym=2026-07").status_code == 404)
    sr._policy_module = lambda: (types.SimpleNamespace(compute=lambda ym: {"ym": ym, "staff": copy.deepcopy(staff), "enforced": True},
                                                       money=P.money, load_settings=P.load_settings), "")
    t = c.get("/register/salary?ym=2026-08").get_data(as_text=True)
    check("a matching recompute says so", "matches the locked table" in t and "differs for" not in t)
    t = c.get("/register/salary?ym=2026-07").get_data(as_text=True)
    check("an unlocked month keeps today's table and total", "Computed by the NEW policy engine" in t and "The locked table" not in t)
    con.execute("UPDATE locked_run SET report_html='<html>damaged</html>' WHERE ym='2026-08'")
    con.commit()
    t = c.get("/register/salary?ym=2026-08").get_data(as_text=True)
    check("an unreadable frozen table: card stays, no second total", "could not be read back" in t and "TOTAL PAYOUT &#8377;%s" % card in t
          and "Computed by the NEW policy engine" not in t)
    with c.session_transaction() as ss:
        ss["sr_user"], ss["sr_role"] = "sukhveer", "self"
    check("a staff login cannot open the frozen sheets", c.get("/register/salary/locked?ym=2026-08").status_code in (302, 403))
    print("TEST OK — %d checks (S303 locked table, over the real sheets34_html)" % N[0])


if __name__ == "__main__":
    main()
