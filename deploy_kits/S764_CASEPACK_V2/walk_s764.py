#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
walk_s764.py — the walk of kit S764 on a MADE-UP store (no patient row, no live file written).

  python walk_s764.py <dir>            green = "WALK OK ..." on the kit's files
  python walk_s764.py <dir> --control  red   = "CONTROL: red at check N" on the LIVE files (the v2 routes are not there)

<dir> holds casepack_portal.py, casepack_v2.py (the kit's; for the control the kit's casepack_v2.py is still beside the
live casepack_portal.py — the live portal does not register it, so check 1 goes red), casepack_page.html and
casepack_seed.html. The portal's guard is stood in by a pass-through decorator: the gate itself is portal.py's
(casepack_required) and is not this kit's to test; the routes are proved behind whatever guard they are given.
"""
import os, sys, json, tempfile, shutil, importlib, re

def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    d = os.path.abspath(sys.argv[1]); control = "--control" in sys.argv
    tmp = tempfile.mkdtemp(prefix="s764walk.")
    os.environ["PORTAL_CASEPACK_DIR"] = tmp
    for nm in ("casepack_page.html", "casepack_seed.html"):
        if os.path.exists(os.path.join(d, nm)): shutil.copy(os.path.join(d, nm), os.path.join(tmp, nm))
    sys.path.insert(0, d)
    for m in ("casepack_portal", "casepack_v2"):
        if m in sys.modules: del sys.modules[m]
    from flask import Flask
    app = Flask("walk764"); app.config["TESTING"] = True
    def guard(f): return f
    import casepack_portal
    casepack_portal.register(app, guard, lambda: "manoj")   # the owner's login; a second app below is registered as another login
    c = app.test_client()
    n = [0]; fails = []
    def ck(label, cond, detail=""):
        n[0] += 1
        if cond: print("  %2d ok  %s" % (n[0], label))
        else:
            print("  %2d RED %s %s" % (n[0], label, detail)); fails.append(n[0])
            if control:
                print("CONTROL: red at check %d (%s)" % (n[0], label)); sys.exit(0)
    def J(r):
        try: return r.get_json() or {}
        except Exception: return {}

    # 0 — a POST before any GET (a fresh store, a second tab, a lost file) must answer, never hang (the cold review's deadlock)
    import signal
    def _alarm(*a): raise TimeoutError("hung")
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(20)
    try:
        r0 = c.post("/portal/casepack/rates", json={"base_version": 1, "rates": [{"k": "gen", "n": "General Ward", "r": 2100, "t": "ward"}]})
        r0b = c.post("/portal/casepack/packages", json={"base_version": 1, "packages": [{"id": "px", "name": "X"}], "groups": []})
        hung = False
    except TimeoutError:
        hung = True
    finally:
        signal.alarm(0)
    ck("a POST before the first GET answers (no lock waiting on itself): rates %s · packages %s" % (getattr(r0, "status_code", "hung"), getattr(r0b, "status_code", "hung")), not hung and r0.status_code == 200 and r0b.status_code == 200)
    # the store is re-seeded for the checks below (that first POST was on a seeded file: v1 -> v2)
    for nm in ("cp_rates.json", "cp_packages.json"):
        try: os.remove(os.path.join(tmp, nm))
        except FileNotFoundError: pass
    # 1 — the v2 routes are registered
    r = c.get("/portal/casepack/packages"); j = J(r)
    ck("GET /portal/casepack/packages answers ok", r.status_code == 200 and j.get("ok") is True, "status %s %s" % (r.status_code, j.get("error")))
    pk = j.get("packages") or []; groups = j.get("groups") or []
    # 2 — the seed: his 15 live packages + a suggested one per uncovered template; 8 groups
    have = [p for p in pk if not p.get("suggested")]; sug = [p for p in pk if p.get("suggested")]
    ck("the seed: 15 of his packages, 42 suggested, 8 charge groups", len(have) == 15 and len(sug) == 42 and len(groups) == 8, "%d/%d/%d" % (len(have), len(sug), len(groups)))
    names = set(p["name"] for p in have)
    ck("his 12 template-mapped packages carry their templates", sum(1 for p in have if p.get("template")) == 12, str([p["name"] for p in have if p.get("template")]))
    ck("THR, THR REVISION, POTTS SPINE stand on their own (no group)", all(p.get("group") is None for p in pk if p["name"] in ("THR", "THR REVISION", "POTTS SPINE")))
    pfn = [p for p in have if p["name"] == "PFN"][0]
    ck("PFN keeps its live figures (surgery 20,000 · implant 6,000 · stay 1 · heads 4,000/2,000/1,600)", (pfn["surgery"], pfn["implant"], pfn["stay"], pfn["anaesthesia"], pfn["otMeds"], pfn["wardMeds"]) == (20000, 6000, 1, 4000, 2000, 1600))
    ck("PFN is in Hip fixation with its own figures, marked where it differs", pfn.get("group") == "g_hipfix" and pfn.get("own") is True and pfn.get("differs") is True)
    ck("general ward and the basic implant are the defaults", (j.get("defaults") or {}).get("room") == "gen" and (j.get("defaults") or {}).get("grade") == "eco")
    ck("his share is a private setting at 50", (j.get("settings") or {}).get("share_pct") == 50)
    # 3 — the DTH rates list
    r = c.get("/portal/casepack/rates"); jr = J(r); rates = jr.get("rates") or []
    ck("GET rates: 5 wards, 2 daily, 1 optional; General Ward 2,000", len([x for x in rates if x["t"] == "ward"]) == 5 and len([x for x in rates if x["t"] == "day"]) == 2 and len([x for x in rates if x["t"] == "opt"]) == 1 and [x for x in rates if x["k"] == "gen"][0]["r"] == 2000)
    # 4 — the worked example he approved: PFN, general ward, 2 days, medium size → 54,700 → 35,000 → 17,500
    fig = {"surgery": 20000, "implant": 6000, "grade": "eco", "stay": 2, "room": "gen", "anaesthesia": 5000, "otMeds": 3000, "wardMeds": 2500, "admission": 1200, "carm": 4000, "investigations": 2000, "other": 0, "discount": 0}
    r = c.post("/portal/casepack/v2/calc", json={"figures": fig}); cc = (J(r).get("calc") or {})
    ck("the worked example: total 54,700 · shareable 35,000 · his net 17,500", (cc.get("total"), cc.get("shareable"), cc.get("my_net")) == (54700, 35000, 17500), str((cc.get("total"), cc.get("shareable"), cc.get("my_net"))))
    r = c.post("/portal/casepack/v2/calc", json={"figures": dict(fig, grade="prem", discount=1000, opts={"hr": True})}); c2 = (J(r).get("calc") or {})
    ck("premium ×1.6, high-risk 1,300 × 2, a 1,000 discount: 60,900 → 59,900 → 36,600 → 18,300", (c2.get("total"), c2.get("net_to_patient"), c2.get("shareable"), c2.get("my_net"), c2.get("implant")) == (60900, 59900, 36600, 18300, 9600), str(c2))
    r = c.post("/portal/casepack/v2/calc", json={"figures": dict(fig, surgery=-5, stay=0, implant="abc")}); c3 = (J(r).get("calc") or {})
    ck("bad figures are clamped, never a crash (surgery -5 → 0, stay 0 → 1, implant 'abc' → 0)", c3.get("surgery") == 0 and c3.get("stay") == 1 and c3.get("implant") == 0)
    # 5 — saving packages: pinned by version; empty refused; two ids refused
    v = j.get("version")
    r = c.post("/portal/casepack/packages", json={"base_version": v, "packages": pk, "groups": groups, "defaults": j.get("defaults")}); js = J(r)
    ck("POST packages with the right version saves (v%s → v%s)" % (v, js.get("version")), r.status_code == 200 and js.get("ok") and js.get("version") == v + 1)
    r = c.post("/portal/casepack/packages", json={"base_version": v, "packages": pk, "groups": groups}); js2 = J(r)
    ck("a stale save (another device saved first) is refused with 409 and the current list", r.status_code == 409 and js2.get("stale") and (js2.get("current") or {}).get("version") == v + 1)
    r = c.post("/portal/casepack/packages", json={"base_version": v + 1, "packages": [], "groups": groups})
    ck("an empty list is refused", r.status_code == 400)
    r = c.post("/portal/casepack/packages", json={"packages": pk, "groups": groups})
    ck("a save with NO version pinned (an empty cache) is refused — never a silent overwrite", r.status_code == 400 and "no version pinned" in (J(r).get("error") or ""))
    r = c.post("/portal/casepack/rates", json={"rates": rates})
    ck("rates with no version pinned are refused too", r.status_code == 400)
    dup = [dict(pk[0]), dict(pk[0])]
    r = c.post("/portal/casepack/packages", json={"base_version": v + 1, "packages": dup, "groups": groups})
    ck("two packages with one id are refused", r.status_code == 400)
    # a group change flows to its linked members; an own member keeps its figures
    g = [dict(x) for x in groups]; gh = [x for x in g if x["id"] == "g_hipfix"][0]; gh["surgery"] = 22222; gh["stay"] = 3
    r = c.post("/portal/casepack/packages", json={"base_version": v + 1, "packages": pk, "groups": g}); js3 = J(r)
    j4 = J(c.get("/portal/casepack/packages")); pk4 = j4["packages"]
    dhs = [p for p in pk4 if p.get("fix") == "DHS"][0]; pfn4 = [p for p in pk4 if p["name"] == "PFN"][0]
    ck("a group's surgery/stay flows to its linked member (DHS 22,222 · 3 d); PFN with own figures keeps 20,000 · 1 d, marked differs", dhs["surgery"] == 22222 and dhs["stay"] == 3 and pfn4["surgery"] == 20000 and pfn4["stay"] == 1 and pfn4["differs"] is True)
    hist = os.listdir(os.path.join(tmp, "cp_history")) if os.path.isdir(os.path.join(tmp, "cp_history")) else []
    ck("every save keeps the previous file in cp_history (%d there)" % len(hist), len([h for h in hist if h.startswith("cp_packages.json.")]) >= 2)
    # 6 — the rates: pinned; at least one ward; a bad row refused
    rv = jr.get("version")
    r = c.post("/portal/casepack/rates", json={"base_version": rv, "rates": [x for x in rates if x["t"] != "ward"]})
    ck("rates without a ward are refused", r.status_code == 400)
    newr = [dict(x) for x in rates] + [{"k": "", "n": "Physiotherapy", "r": 300, "t": "opt"}]
    r = c.post("/portal/casepack/rates", json={"base_version": rv, "rates": newr}); jj = J(r)
    ck("a new optional per-day head saves; the list is v%s" % jj.get("version"), r.status_code == 200 and jj.get("count") == 9)
    r = c.post("/portal/casepack/rates", json={"base_version": rv, "rates": newr})
    ck("a stale rates save is refused (409)", r.status_code == 409)
    r = c.get("/portal/casepack/rates"); j5 = J(r)
    ck("the new head has a key of its own and reads back", any(x["n"] == "Physiotherapy" and x["k"] for x in j5["rates"]))
    # 7 — estimates given: append-only, under the patient, newest first, marked
    r = c.post("/portal/casepack/estimates", json={"patient": {"uid": "", "cid": "T-0001", "name": "Test Patient"}, "payer": "Cash", "title": "PFN", "package_id": pfn["id"], "figures": fig, "text": "x"}); e1 = J(r)
    ck("POST estimates saves a cash estimate with the server's arithmetic (54,700; his net 17,500)", r.status_code == 200 and (e1.get("estimate") or {}).get("net_to_patient") == 54700 and e1["estimate"].get("my_net") == 17500)
    r = c.post("/portal/casepack/estimates", json={"patient": {"cid": "T-0001", "name": "Test Patient"}, "payer": "Ayushman", "title": "SB019C", "total": 26900, "figures": None, "text": "y"}); e2 = J(r)
    ck("an Ayushman record keeps the scheme's figure (26,900) and works out no net of his", r.status_code == 200 and e2["estimate"]["total"] == 26900 and e2["estimate"]["my_net"] is None)
    r = c.get("/portal/casepack/estimates?cid=T-0001"); el = J(r).get("estimates") or []
    ck("GET estimates?cid lists both, newest first, taken_up unknown", len(el) == 2 and el[0]["title"] == "SB019C" and el[0]["taken_up"] is None)
    r = c.post("/portal/casepack/estimates/mark", json={"id": e1["estimate"]["id"], "taken_up": True})
    el2 = J(c.get("/portal/casepack/estimates?cid=T-0001")).get("estimates") or []
    ck("a mark (taken up) is a new line; the estimate reads taken_up true", r.status_code == 200 and [e for e in el2 if e["id"] == e1["estimate"]["id"]][0]["taken_up"] is True)
    r = c.post("/portal/casepack/estimates/mark", json={"id": "E-20200101-010203000", "taken_up": True})
    ck("a mark on no such estimate is refused", r.status_code == 404)
    with open(os.path.join(tmp, "cp_estimates.jsonl"), "r", encoding="utf-8") as f: nl = len([x for x in f.read().split("\n") if x.strip()])
    ck("the estimates file is append-only: 3 lines (2 estimates + 1 mark)", nl == 3)
    ck("the estimates file is the owner's alone (mode 600)", (os.stat(os.path.join(tmp, "cp_estimates.jsonl")).st_mode & 0o777) == 0o600)
    # 8 — a device's old list merges by name
    items = [{"name": "PFN", "operation": 21000, "implant": 6500, "stay": 2, "anaesthesia": 4000, "otMeds": 2000, "wardMeds": 1600, "admission": 1200, "carm": 4000, "investigations": 2000, "other": 1150},
             {"name": "SHOULDER HEMI", "operation": 30000, "implant": 20000, "stay": 3, "anaesthesia": 5000, "otMeds": 3000, "wardMeds": 2500, "admission": 1200, "carm": 0, "investigations": 2000, "other": 0}]
    r = c.post("/portal/casepack/packages/import", json={"items": items}); ck("an import with no version pinned is refused", r.status_code == 400)
    r = c.post("/portal/casepack/packages/import", json={"items": items, "base_version": 1}); ck("an import pinned to an old version is refused (409)", r.status_code == 409)
    vcur = J(c.get("/portal/casepack/packages"))["version"]
    r = c.post("/portal/casepack/packages/import", json={"items": items, "base_version": vcur}); ji = J(r)
    j6 = J(c.get("/portal/casepack/packages")); pfn6 = [p for p in j6["packages"] if p["name"] == "PFN"][0]
    ck("import: PFN takes the device's figures (21,000 · 6,500 · 2 d), SHOULDER HEMI is added; nothing removed", ji.get("updated") == 1 and ji.get("imported") == 1 and pfn6["surgery"] == 21000 and pfn6["stay"] == 2 and len(j6["packages"]) == len(pk) + 1)
    # 9 — the templates and the seeding page
    r = c.get("/portal/casepack/templates"); jt = J(r)
    ck("GET templates: 54 options in 6 regions; every option has an SB code and a charge group or none", jt.get("ok") and len(jt.get("options") or []) == 54 and len(jt.get("regions") or []) == 6 and all(re.match(r"^SB\d{3}[A-Z]$", o["sb"]) for o in jt["options"]))
    r = c.get("/portal/casepack/seed")
    ck("GET /portal/casepack/seed serves the seeding page", r.status_code == 200 and b"Package seeding" in r.data and b"Save all packages" in r.data)
    # 10 — the page itself
    r = c.get("/portal/casepack"); page = r.data.decode("utf-8") if r.status_code == 200 else ""
    ck("the page serves and carries the S764 block, the four live stages and the foot bar", r.status_code == 200 and 's764css' in page and '1 · Estimate' in page and '2 · Consent' in page and '3 · OT &amp; orders' in page and '4 · IPD case' in page and 'Estimates given' in page and 'Manage packages' in page and 'class="cpstep parked"' not in page and 'Parked — arrives' not in page)
    ck("the on-device builder, its 'Saves on this device only' and the room/stay/high-risk controls are gone", 'Saves on this device only' not in page and 'id="cashCtl"' not in page and 'Cash package builder' not in page and "dma_cash_v1'" not in page)
    ck("the consent, OT list and orders code is intact (S216 · S684 · S685 · the ankle box)", all(s in page for s in ("function csGenerate", "s684AnkleOpening", "csFixApply", "function caseBundle", "id=\"s684_ank\"", "function buildPostop")))
    ck("the page's data is untouched: BUNDLE with 138 Ayushman rows and the TPA set", page.count('"sub":"SB') == 138 and '"tpas": [' in page)
    ck("the page says the server holds the lists, not the device", 'the same list on every device' in page)
    # 11 — his net is his: a login not named as the owner gets no share, no net, no setting
    import casepack_v2 as _v2
    app2 = Flask("walk764b"); app2.config["TESTING"] = True
    _v2.register(app2, guard, lambda: "shavez")
    c2 = app2.test_client()
    j2 = J(c2.get("/portal/casepack/packages")); e2l = J(c2.get("/portal/casepack/estimates")).get("estimates") or []
    cc2 = J(c2.post("/portal/casepack/v2/calc", json={"figures": fig})).get("calc") or {}
    ck("another login sees the packages but no share setting, no my_net on the estimates, no net in a calc; the setting routes refuse (403)",
       j2.get("ok") and j2.get("settings") is None and e2l and all("my_net" not in e for e in e2l) and "my_net" not in cc2 and c2.get("/portal/casepack/settings").status_code == 403 and c2.post("/portal/casepack/settings", json={"share_pct": 10}).status_code == 403)
    ck("rounding is half-up like the page (shareable 35,001 at 50% → 17,501)", _v2.calc(dict(fig, other=1), rates, 50)["my_net"] == 17501)
    # 12 — the unused routes refuse cleanly
    r = c.post("/portal/casepack/packages", data="not json", content_type="application/json")
    ck("a non-JSON body is refused, not a crash", r.status_code in (400, 415) or (r.status_code == 200 and J(r).get("ok") is False) or r.status_code == 500 and "refused" in (J(r).get("error") or ""))
    shutil.rmtree(tmp, ignore_errors=True)
    if control:
        print("CONTROL: did NOT go red (%d checks green)" % n[0]); sys.exit(2)
    if fails:
        print("WALK FAILED at checks %s" % fails); sys.exit(1)
    print("WALK OK %d/%d checks green (made-up store, deleted)" % (n[0], n[0]))

if __name__ == "__main__":
    main()
