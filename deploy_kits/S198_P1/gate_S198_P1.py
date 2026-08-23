#!/usr/bin/env python3
"""S198_P1 gate — served-HTML assertions on the candidate portal.py (F-98
harness pattern: identity monkeypatched, real render path, candidate vs live
baseline for URL preservation). Run: python3 gate_S198_P1.py <candidate.py>
[--baseline <live.py>]. Exit 0 only on all-green."""
import importlib.util
import sys

PASS = FAIL = 0


def check(label, ok):
    global PASS, FAIL
    if ok:
        PASS += 1
    else:
        FAIL += 1
        print("FAIL: " + label)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def has_tile(h, name):
    """True when NAME renders as a tile (nm div), not merely appears in JS."""
    import html as _h
    return ('nm">%s</div>' % _h.escape(name, quote=False)) in h


def serve(mod, user, role, pc=False):
    """Render /portal as (user, role) with auth+SSO stubbed; returns HTML."""
    mod._usable = lambda: True
    mod._authed = lambda req: True
    mod._sso_ready = lambda: True
    mod._sso_user = lambda req: {"user": user, "role": role}
    mod._is_clinic_pc = lambda req: pc
    with mod.app.test_client() as c:
        r = c.get("/portal")
        assert r.status_code == 200, "HTTP %d for %s" % (r.status_code, user)
        return r.get_data(as_text=True)


def main():
    cand_path = sys.argv[1]
    base_path = sys.argv[sys.argv.index("--baseline") + 1] if "--baseline" in sys.argv else None
    cand = load(cand_path, "cand_portal")

    # ---- structural: every tile grouped, groups known (import already asserts;
    # re-assert here so the gate owns the claim) --------------------------------
    names = [t["name"] for t in cand.TILES]
    check("every tile grouped", all(n in cand._TILE_GROUP for n in names))
    # exact duplicate check (the only honest form -- F-106: never assert a
    # shape you have not printed):
    check("no exact duplicate names", len(set(names)) == len(names))

    # ---- URL preservation vs the LIVE baseline --------------------------------
    if base_path:
        base = load(base_path, "base_portal")
        burl = {t["name"]: t["url"] for t in base.TILES}
        curl = {t["name"]: t["url"] for t in cand.TILES}
        renamed = {"UPI Reconciliation": "UPI Sheet"}
        removed = {"Ayushman Finder", "WABA Send", "Surgical Estimate", "Nutrition / Physio"}
        added = {"Payment Register", "Forms & Downloads"}
        for n, u in burl.items():
            tgt = renamed.get(n, n)
            if n in removed:
                check("removed tile absent: " + n, tgt not in curl or n in renamed)
                continue
            check("url preserved: " + n, curl.get(tgt) == u)
        check("only the declared additions", set(curl) - {renamed.get(n, n) for n in burl} == added)

    # ---- doctor (manoj), PC not marked ---------------------------------------
    h = serve(cand, "manoj", "doctor", pc=False)
    for n in ["Clinic Gist", "Call Console", "Call Tracker", "Surgical Case Pack",
              "Send WhatsApp", "Follow-up WhatsApps", "WhatsApp Approvals",
              "GMB Review Assist", "Forms &amp; Downloads", "Attendance",
              "Staff Register", "Salary — approve &amp; lock", "Staff Ledger",
              "UPI Sheet", "Monthly Accounting", "Vehicle Tracking",
              "Sanjeevni Medicos", "Clinic", "CC Statement Saver", "Inbox Janitor",
              "Payment Register", "RxGuard", "GutLog", "FitLog", "Manage Users"]:
        check("manoj sees: " + n,
              has_tile(h, n.replace("&amp;", "&")) or n in ("Clinic",) and has_tile(h, "Clinic"))
    for n in ["Ayushman Finder", "WABA Send", "Surgical Estimate",
              "Nutrition / Physio", "UPI Reconciliation"]:
        check("manoj must NOT see: " + n, n not in h)
    check("manoj sees: Revenue Reconciler (as a migration-queue chip)",
          "Revenue Reconciler" in h and 'class="mchip held"' in h)
    check("hero present for doctor", 'id="healthHero"' in h and "/finance/health" in h)
    check("strip chips present", 'id="chipSanj"' in h and 'id="chipReg"' in h and 'id="chipRev"' in h)
    check("Staff section present", ">Staff</div>" in h)
    check("dark scheme kept on home (owner ruling)", "--bg:#0f2233" in h and "--surface-page" not in h)
    check("back-to-top present", 'id="toTop"' in h)
    # tile ORDER (owner, 23-Aug): calls together, GMB up, Case Pack down
    _i = h.index
    check("order: Console > Tracker > GMB adjacent block",
          _i('nm">Call Console<') < _i('nm">Call Tracker<') < _i('nm">GMB Review Assist<'))
    check("order: Case Pack sits after the WhatsApp cluster",
          _i('nm">WhatsApp Approvals<') < _i('nm">Surgical Case Pack<'))
    check("order: GMB before Send WhatsApp",
          _i('nm">GMB Review Assist<') < _i('nm">Send WhatsApp<'))
    check("logo embedded", "data:image/png;base64," in h)
    check("PC tools hidden off the clinic PC", "localhost:5000" not in h and "localhost:5057" not in h)
    check("Payment Register renders MANUAL when unconfigured",
          (not cand.PAYMENT_REGISTER_URL) and ("Payment Register" in h and "MANUAL" in h))
    check("count hooks intact",
          "data-sanjeevni-counts" in h and "data-review-counts" in h and "data-gist-summary" in h)
    check("forget-all + signout survive", "/portal/forget" in h and "/portal/signout-all" in h)
    check("mark-pc link survives", "/portal/mark-pc" in h)
    for u in ["https://attendance.dr-manoj.in/register/review",
              "https://attendance.dr-manoj.in/register/salary",
              "https://attendance.dr-manoj.in/ledger", "/finance/approvals",
              "/portal/console", "/portal/casepack", "/portal/gist"]:
        check("live url present: " + u, u in h)

    # ---- doctor (manoj), PC marked -------------------------------------------
    h = serve(cand, "manoj", "doctor", pc=True)
    check("PC chips appear on the marked PC",
          "localhost:5000" in h and "localhost:5057" in h and "localhost:5059" in h)
    check("PC row renders as chips", h.count('class="mchip') >= 4)
    check("saved-cases note on the fallback chip", "Keeps saved cases" in h)

    # ---- doctor (bhawna): masks intact ---------------------------------------
    h = serve(cand, "bhawna", "doctor", pc=True)
    for n in ["Sanjeevni Medicos", "GMB Review Assist", "Surgical Case Pack",
              "Send WhatsApp", "Follow-up WhatsApps", "Vitals &amp; Plan",
              "Follow-up Tracker", "CC Statements → Tally"]:
        check("bhawna masked from: " + n, n not in h)
    check("bhawna keeps Clinic (extra)", ">Clinic</div>" in h)
    check("bhawna keeps Staff Register", has_tile(h, "Staff Register"))

    # ---- staff (darpan): only Daily Sale of the family ------------------------
    h = serve(cand, "darpan", "staff")
    check("darpan sees Daily Sale", has_tile(h, "Daily Sale"))
    for n in ["Attendance", "Staff Register", "Scan Purchase", "Staff Ledger",
              "Sanjeevni Medicos", "Payment Register", "Manage Users"]:
        check("darpan must NOT see: " + n, not has_tile(h, n))
    check("no hero for staff", 'id="healthHero"' not in h)

    # ---- staff (alisha): family + clinic grant --------------------------------
    h = serve(cand, "alisha", "staff")
    for n in ["Attendance", "Staff Register", "Scan Purchase", "Daily Sale",
              "Daily Collection"]:
        check("alisha sees: " + n, has_tile(h, n))
    check("no hero for alisha", 'id="healthHero"' not in h)

    # ---- manager (shavez) -----------------------------------------------------
    h = serve(cand, "shavez", "manager")
    for n in ["Daily Collection", ">Clinic</div>", "Asset Register",
              "Staff Ledger — Entry", "Scan Purchase"]:
        check("shavez sees: " + n.replace(">Clinic</div>", "Clinic tile"),
              (n in h))
    check("no hero for manager", 'id="healthHero"' not in h)
    check("shavez not shown doctor personals", "Payment Register" not in h and "RxGuard" not in h)

    print("GATE %d/%d %s" % (PASS, PASS + FAIL, "GREEN" if FAIL == 0 else "RED"))
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
