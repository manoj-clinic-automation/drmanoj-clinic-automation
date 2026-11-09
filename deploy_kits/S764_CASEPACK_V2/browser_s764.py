#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
browser_s764.py — the page walked in Chromium (Playwright) at 1366 and 390 px against a live harness of the kit's files:
the owner's road through the Enquiry stage v2 — the server's list, a package tapped, every fold, the worked example,
Give estimate, Save as a new package, the DTH rates, Build an estimate, a template, Next: Consent → (prefilled), the
stepper 1-4, Estimates given, Ayushman / TPA / the consent generator intact, the seeding page, the phone width.
Cloud-side evidence (the box has no Chromium); the installer runs walk_s764.py.

  python browser_s764.py <dir_with_kit_files>
"""
import os, sys, json, threading, time, tempfile, shutil, socket

def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p

def main():
    d = os.path.abspath(sys.argv[1])
    tmp = tempfile.mkdtemp(prefix="s764br.")
    os.environ["PORTAL_CASEPACK_DIR"] = tmp
    for nm in ("casepack_page.html", "casepack_seed.html"): shutil.copy(os.path.join(d, nm), os.path.join(tmp, nm))
    sys.path.insert(0, d)
    from flask import Flask, jsonify, request
    app = Flask("br764")
    @app.route("/portal/casepack/search")
    def _mock_search():
        q = request.args.get("q", "")
        return jsonify({"ok": True, "matches": [{"Patient_UID": "U1", "Clinic_Specific_Id": "T-0007", "Patient_Name": "Walk Patient", "Mobile_Clean": "", "Age": "52", "Sex": "M", "Source": "master"}] if "wal" in q.lower() else [], "sources": {}})
    @app.route("/finance/surgery/new")
    def _mock_ipd(): return "IPD " + json.dumps(request.args.to_dict())
    import casepack_portal
    casepack_portal.register(app, lambda f: f, lambda: "manoj")
    port = free_port()
    th = threading.Thread(target=lambda: app.run(host="127.0.0.1", port=port, threaded=True, use_reloader=False), daemon=True); th.start()
    time.sleep(1.2)
    base = "http://127.0.0.1:%d" % port
    from playwright.sync_api import sync_playwright
    n = [0]; fails = []
    def ck(label, cond, detail=""):
        n[0] += 1
        print("  %2d %s %s %s" % (n[0], "ok " if cond else "RED", label, "" if cond else detail)); (None if cond else fails.append(n[0]))
    errors = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 1366, "height": 900})
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: " + str(e)))
        pg.on("console", lambda m: errors.append("console.error: " + m.text) if (m.type == "error" and "Failed to load resource" not in m.text) else None)   # the consent's online transliteration (inputtools.google.com) is unreachable from the harness and falls back offline, as designed (S216)
        pg.on("dialog", lambda dlg: dlg.accept("Walk Name") if dlg.type == "prompt" else dlg.accept())
        pg.goto(base + "/portal/casepack"); pg.wait_for_selector(".s764pkg", timeout=8000)
        pkgs = pg.locator("#s764list .s764pkg").count()
        ck("the page loads with the server's packages (%d rows: his 15 as cards, the other fixations as dashed template rows)" % pkgs, pkgs >= 57 and pg.locator("#s764list .s764pkg:not(.tpl)").count() == 15 and not errors, "; ".join(errors[:3]))
        ck("the stepper reads 1 Estimate · 2 Consent · 3 OT & orders · 4 IPD case", pg.locator("#cpStepper").inner_text().replace("\n", " ").count("Estimate") == 1 and "IPD case" in pg.locator("#cpStepper").inner_text() and "parked" not in pg.locator("#cpStepper").inner_text())
        ck("the search box leads: it is wider than the patient line's box and has the blue border", pg.eval_on_selector("#q", "e=>parseFloat(getComputedStyle(e).borderTopWidth)") >= 2 and pg.eval_on_selector("#estPbQ", "e=>parseFloat(getComputedStyle(e).borderTopWidth)") <= 1)
        ck("region headings are there (Hip · thigh, Knee · leg · ankle, Other packages)", all(s in pg.locator("#s764list").inner_text() for s in ("HIP · THIGH", "KNEE · LEG · ANKLE", "OTHER PACKAGES")) or all(s in pg.locator("#s764list").inner_text().upper() for s in ("HIP", "KNEE", "OTHER PACKAGES")))
        # search + tap PFN
        pg.fill("#q", "pfn"); pg.wait_for_timeout(200)
        cards = pg.locator("#s764list .s764pkg").count()
        ck("searching 'pfn' narrows the list (%d rows)" % cards, 1 <= cards <= 6)
        pg.click("#s764list .s764pkg:not(.tpl) >> text=PFN"); pg.wait_for_selector(".s764sheet")
        tot = pg.locator(".s764sheet .s764total b").inner_text()
        ck("PFN opens as a sheet in place at general ward, 1 day: " + tot + " (his heads 4,000/2,000/1,600, other 1,150)", tot == "₹49,450")
        # the worked example: 2 days, medium heads
        pg.click(".s764sheet details[data-f=room] summary"); pg.click(".s764sheet .s764step[data-d='1']"); pg.wait_for_timeout(100)
        pg.click(".s764sheet details[data-f=heads] summary")
        pg.fill("#e_an", "5000"); pg.fill("#e_otm", "3000"); pg.fill("#e_wm", "2500"); pg.fill("#e_oth", "0"); pg.wait_for_timeout(150)
        tot2 = pg.locator(".s764sheet .s764total b").inner_text(); priv = pg.locator(".s764sheet .s764priv").inner_text()
        ck("the worked example on the screen: ₹54,700 to the patient; only-you net ₹17,500 (shareable ₹35,000 × 50%)", tot2 == "₹54,700" and "₹17,500" in priv and "₹35,000" in priv, tot2 + " | " + priv)
        ck("the heads fold stayed open while typing and the focus stayed in the box", pg.eval_on_selector(".s764sheet details[data-f=heads]", "e=>e.open") and pg.evaluate("document.activeElement && document.activeElement.id") == "e_oth")
        pg.click(".s764sheet details[data-f=impl] summary"); pg.select_option("#e_grade", "prem"); pg.wait_for_timeout(120)
        ck("Premium (Ti) ×1.6: implant line ₹9,600, total ₹58,300", "₹9,600" in pg.locator(".s764sheet details[data-f=impl] summary .v").inner_text() and pg.locator(".s764sheet .s764total b").inner_text() == "₹58,300")
        pg.select_option("#e_grade", "eco"); pg.wait_for_timeout(100)
        pg.click(".s764sheet details[data-f=disc] summary"); pg.fill("#e_disc", "700"); pg.wait_for_timeout(120)
        ck("a ₹700 discount: estimate ₹54,000, only-you net ₹17,150 (the discount comes off the shareable amount)", pg.locator(".s764sheet .s764total b").inner_text() == "₹54,000" and "₹17,150" in pg.locator(".s764sheet .s764priv").inner_text(), pg.locator(".s764sheet .s764priv").inner_text())
        # give estimate without a patient -> prompt (accepted as 'Walk Name')
        pg.click(".s764sheet [data-act=give]"); pg.wait_for_timeout(600)
        import urllib.request
        est = json.loads(urllib.request.urlopen(base + "/portal/casepack/estimates").read())["estimates"]
        ck("Give estimate with no patient linked asks a name and saves on the server (1, 'Walk Name', ₹54,000)", len(est) == 1 and est[0]["patient"]["name"] == "Walk Name" and est[0]["net_to_patient"] == 54000, json.dumps(est)[:200])
        # link a patient on the quiet line, give again -> no prompt, cid carried
        pg.fill("#estPbQ", "wal"); pg.wait_for_selector("#estPbRes [data-i]", timeout=4000); pg.click("#estPbRes [data-i]"); pg.wait_for_timeout(200)
        ck("the patient line links a patient (Walk Patient · T-0007)", "Walk Patient" in pg.locator("#estPbSel").inner_text() and "T-0007" in pg.locator("#estPbSel").inner_text())
        pg.click(".s764sheet [data-act=give]"); pg.wait_for_timeout(600)
        est = json.loads(urllib.request.urlopen(base + "/portal/casepack/estimates").read())["estimates"]
        ck("Give estimate with a patient linked: saved under T-0007 without asking", len(est) == 2 and est[0]["patient"]["cid"] == "T-0007")
        ck("the estimate is the latest for the case bundle (Est: PFN ₹54,000)", "PFN" in pg.evaluate("(function(){try{var e=chooseEstimate();return (e&&e.title)+' '+(e&&e.total);}catch(x){return 'x '+x;}})()"))
        # save as a new package (prompt -> 'Walk Name')
        before = len(json.loads(urllib.request.urlopen(base + "/portal/casepack/packages").read())["packages"])
        pg.click(".s764sheet [data-act=saveas]"); pg.wait_for_timeout(900)
        pk = json.loads(urllib.request.urlopen(base + "/portal/casepack/packages").read())
        new = [p for p in pk["packages"] if p["name"] == "Walk Name"]
        ck("Save as a new package: 'Walk Name' joins the server's list with the sheet's figures (stay 2, heads 5,000/3,000/2,500 = medium)", len(pk["packages"]) == before + 1 and new and new[0]["stay"] == 2 and new[0]["size"] == "medium" and new[0]["group"] == "g_hipfix" and new[0]["own"] is True, json.dumps(new)[:300])
        # save changes to the PFN package
        pg.fill("#q", "pfn"); pg.wait_for_timeout(200); pg.click("#s764list .s764pkg:not(.tpl) >> text=/^PFN/"); pg.wait_for_selector(".s764sheet")
        pg.click(".s764sheet details[data-f=surg] summary"); pg.fill("#e_op", "21000"); pg.wait_for_timeout(100); pg.click(".s764sheet [data-act=savepkg]"); pg.wait_for_timeout(900)
        pk = json.loads(urllib.request.urlopen(base + "/portal/casepack/packages").read()); pfn = [p for p in pk["packages"] if p["name"] == "PFN"][0]
        ck("Save changes to this package: PFN's surgery is 21,000 on the server (v%s)" % pk["version"], pfn["surgery"] == 21000 and pk["version"] >= 3)
        # the rates fold
        pg.fill("#q", ""); pg.wait_for_timeout(150)
        pg.click("#s764ratesbox summary"); pg.wait_for_timeout(150)
        gen = pg.locator("#s764rates input.rt").first; gen.fill("2500"); pg.wait_for_timeout(100)
        ck("the DTH rates fold: the first ward's rate edits in place and the summary line follows", "2,500" in pg.locator("#s764ratesum").inner_text())
        pg.click("#s764saverates"); pg.wait_for_timeout(700)
        rt = json.loads(urllib.request.urlopen(base + "/portal/casepack/rates").read())
        ck("Save rates: the server's list is v2 with General Ward 2,500; the old list is in the history", rt["version"] == 2 and [r for r in rt["rates"] if r["k"] == "gen"][0]["r"] == 2500 and any(h.startswith("cp_rates.json.") for h in os.listdir(os.path.join(tmp, "cp_history"))))
        # an unsaved rate edit blocks Give / Save (the figure recorded must be the figure quoted)
        gen.fill("2600"); pg.wait_for_timeout(100)
        ck("the rates summary says UNSAVED while a rate edit is not saved", "UNSAVED" in pg.locator("#s764ratesum").inner_text())
        pg.fill("#q", "pfn"); pg.wait_for_timeout(200)
        if pg.locator(".s764sheet").count() == 0: pg.click("#s764list .s764pkg:not(.tpl) >> text=/^PFN/")
        pg.wait_for_selector(".s764sheet")
        n_before = len(json.loads(urllib.request.urlopen(base + "/portal/casepack/estimates").read())["estimates"])
        pg.click(".s764sheet [data-act=give]"); pg.wait_for_timeout(400)
        n_after = len(json.loads(urllib.request.urlopen(base + "/portal/casepack/estimates").read())["estimates"])
        ck("Give estimate is refused while the DTH rates are unsaved (toast; nothing recorded)", n_after == n_before and "unsaved" in pg.locator("#toast").inner_text().lower())
        gen.fill("2500"); pg.click("#s764saverates"); pg.wait_for_timeout(700)
        ck("after Save rates the flag clears and the summary no longer says UNSAVED", "UNSAVED" not in pg.locator("#s764ratesum").inner_text())
        pg.click(".s764sheet [data-act=close]"); pg.fill("#q", ""); pg.wait_for_timeout(150)
        pg.click("#s764ratesbox summary")
        # build an estimate
        pg.click("#s764buildbox summary"); pg.wait_for_selector("#s764buildarea .s764sheet")
        ck("Build an estimate opens blank: medium size, general ward, 2 days, surgery and implant empty", pg.locator("#s764buildarea .s764size button.on").inner_text().startswith("Medium") and pg.input_value("#s764buildarea #e_op") == "" and "General Ward" in pg.locator("#s764buildarea .s764priv").inner_text())
        pg.fill("#s764buildarea #e_op", "10000"); pg.fill("#s764buildarea #e_impl", "2000"); pg.wait_for_timeout(150)
        ck("typing surgery 10,000 and implant 2,000: total ₹39,700 (OT 2,000 · medium heads 10,500 · admission/C-arm/inv 7,200 · ward 2,500×2 + visit 1,000×2 + nursing 500×2 = 8,000 · implant 2,000)", pg.locator("#s764buildarea .s764total b").inner_text() == "₹39,700", pg.locator("#s764buildarea .s764total b").inner_text())
        pg.click("#s764buildarea [data-act=close]"); pg.wait_for_timeout(150)
        ck("✕ closes the build and folds the box", pg.locator("#s764buildarea .s764sheet").count() == 0 and not pg.eval_on_selector("#s764buildbox", "e=>e.open"))
        # a template without a package
        pg.fill("#q", "dhs"); pg.wait_for_timeout(200)
        ck("a fixation with no package of his shows as a dashed template row (DHS — its suggested figures stay on Manage packages)", pg.locator("#s764list .s764pkg.tpl").count() >= 1 and "suggested figures are on Manage packages" in pg.locator("#s764list .s764pkg.tpl").first.inner_text())
        pg.click("#s764list .s764pkg.tpl"); pg.wait_for_selector("#s764buildarea .s764sheet")
        ck("tapping it opens Build prefilled with the fracture, the SB row and the stay (surgery blank)", "DHS" in pg.locator("#s764buildarea .s764sheet h2").inner_text() and "SB019B" in pg.locator("#s764buildarea .s764ay").inner_text() and pg.input_value("#s764buildarea #e_op") == "")
        # Next: Consent -> (the template feeds the consent)
        pg.click("#caseBtn"); pg.wait_for_timeout(500)
        ck("Next: Consent → opens the Case Pack on the CONSENT pane, stage 2 on the stepper", pg.eval_on_selector("#caseModal", "e=>e.classList.contains('open')") and pg.eval_on_selector("#pane_consent", "e=>e.classList.contains('on')") and pg.eval_on_selector("#cpStepper .cpstep[data-st='2']", "e=>e.classList.contains('on')"))
        ck("the template fed the consent (intertrochanteric → PFN opening 'itfix', part कूल्हे) and the OT list (lower limb)", pg.input_value("#cs_proc") == "itfix" and pg.input_value("#c_part") == "कूल्हे" and pg.input_value("#ot_proc") == "lowerlimb", pg.input_value("#cs_proc") + " " + pg.input_value("#c_part") + " " + pg.input_value("#ot_proc"))
        ck("the patient's name came along (Walk Patient, 52)", pg.input_value("#c_name") == "Walk Patient" and pg.input_value("#c_age") == "52")
        pg.click("#cpStepper .cpstep[data-st='3']"); pg.wait_for_timeout(300)
        ck("stepper 3 → the OT list pane, stage 3 on", pg.eval_on_selector("#pane_ot", "e=>e.classList.contains('on')") and pg.eval_on_selector("#cpStepper .cpstep[data-st='3']", "e=>e.classList.contains('on')") and pg.locator("#otRows .otrow").count() > 10)
        pg.click("#caseSub button[data-s=consent]"); pg.wait_for_timeout(200)
        ck("choosing the consent tab puts the stepper back on 2", pg.eval_on_selector("#cpStepper .cpstep[data-st='2']", "e=>e.classList.contains('on')"))
        # the consent generator itself still works
        pg.select_option("#c_side", "सीधे"); pg.fill("#cs_relname", "Ram Prasad"); pg.click("#cs_gen"); pg.wait_for_timeout(2500)
        out = pg.locator("#cs_out").inner_text()
        ck("Generate consent still works (S216/S684/S685 code intact): %d chars, names the hip, nail (PFN)" % len(out), len(out) > 800 and "कूल्हे" in out and "रॉड" in out)
        with pg.expect_popup() as pop:
            pg.click("#cpStepper .cpstep[data-st='4']")
        p4 = pop.value; p4.wait_for_load_state(); u = p4.url
        ck("stepper 4 → Continue to IPD case opens /finance/surgery/new with the patient (cid T-0007)", "/finance/surgery/new" in u and "cid=T-0007" in u and "name=Walk" in u, u)
        p4.close()
        pg.click("#cpStepper .cpstep[data-st='1']"); pg.wait_for_timeout(200)
        ck("stepper 1 closes the Case Pack and reads stage 1", not pg.eval_on_selector("#caseModal", "e=>e.classList.contains('open')") and pg.eval_on_selector("#cpStepper .cpstep[data-st='1']", "e=>e.classList.contains('on')"))
        # Estimates given
        pg.click("#recBtn"); pg.wait_for_selector("#s764given tbody tr td b", timeout=4000)
        ck("Estimates given lists the two from the server, newest first, with the patient", pg.locator("#s764given tbody tr").count() == 2 and "Walk Patient" in pg.locator("#s764given tbody tr").first.inner_text())
        pg.click("#s764given tbody tr >> nth=0 >> button[data-mk='1']"); pg.wait_for_timeout(600)
        ck("'Taken up' marks it on the server", "taken up" in pg.locator("#s764given tbody tr").first.inner_text())
        pg.click("#s764gclose")
        # Ayushman and TPA panes
        pg.fill("#q", ""); pg.wait_for_timeout(150)
        pg.click("#seg button[data-p=ayush]"); pg.wait_for_timeout(300)
        ck("the Ayushman pane renders as before (%d cards) and the cash pane hides" % pg.locator("#results .card").count(), pg.locator("#results .card").count() >= 50 and not pg.is_visible("#s764cash"))
        pg.click("#seg button[data-p=tpa]"); pg.wait_for_timeout(300)
        ck("the TPA pane renders with the insurer select (%d cards)" % pg.locator("#results .card").count(), pg.locator("#results .card").count() >= 10 and pg.is_visible("#tpaCtl"))
        pg.click("#seg button[data-p=cash]"); pg.wait_for_timeout(300)
        ck("back to Cash: the pane shows again", pg.is_visible("#s764cash"))
        # Manage packages -> the seeding page
        pg.click("#mgr"); pg.wait_for_selector(".gr", timeout=8000)
        rows = pg.locator(".gr").count()
        ck("Manage packages opens the seeding page with every package (%d rows), the groups and the defaults strip" % rows, "/portal/casepack/seed" in pg.url and rows >= 58 and pg.locator(".g").count() == 8 and pg.input_value("#d_share") == "50")
        sugg = pg.locator(".gr input.s").count()
        ck("suggested figures show dashed amber (%d boxes)" % sugg, sugg >= 60)
        dhs_row = pg.locator(".gr", has_text="DHS").first
        gsurg = pg.locator('.g:has(input[value="Hip fixation"])').locator("input[data-gf=surgery]")
        gsurg.fill("23000"); pg.wait_for_timeout(150)
        ck("editing the Hip fixation group's surgery flows to its linked member DHS (23,000)", dhs_row.locator("input[data-f=surgery]").input_value() == "23000")
        pg.click("#saveall"); pg.wait_for_timeout(1200)
        pk = json.loads(urllib.request.urlopen(base + "/portal/casepack/packages").read())
        ck("Save all: the server has it (DHS 23,000; v%s); his share setting saved" % pk["version"], [p for p in pk["packages"] if p.get("fix") == "DHS"][0]["surgery"] == 23000 and pk["settings"]["share_pct"] == 50)
        ck("no page error and no console error anywhere so far", not errors, "; ".join(errors[:4]))
        ctx.close()
        # the phone
        ctx2 = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
        p2 = ctx2.new_page(); e2 = []
        p2.on("pageerror", lambda e: e2.append(str(e)))
        p2.goto(base + "/portal/casepack"); p2.wait_for_selector(".s764pkg", timeout=8000)
        sw = p2.evaluate("document.documentElement.scrollWidth")
        ck("390 px: the page loads, no horizontal scroll (scrollWidth %d)" % sw, sw <= 392 and not e2)
        ck("390 px: the foot bar shows Next: Consent →, Estimates given, Manage packages", p2.is_visible("#caseBtn") and p2.is_visible("#recBtn") and p2.is_visible("#mgr") and p2.locator("#caseBtn").bounding_box()["width"] > 300)
        p2.fill("#q", "tibia"); p2.wait_for_timeout(200); p2.click("#s764list .s764pkg:not(.tpl) >> text=/TIBIA ILN/"); p2.wait_for_selector(".s764sheet")
        bb = p2.locator(".s764sheet").bounding_box()
        ck("390 px: a package opens as a sheet that fits the width (%d px)" % bb["width"], bb["width"] <= 390 and bb["width"] > 300)
        p2.click(".s764sheet details[data-f=room] summary"); p2.wait_for_timeout(100)
        ck("390 px: the room fold opens with the ward select and the days stepper", p2.is_visible("#e_room") and p2.locator(".s764sheet .s764step").count() == 2)
        p2.goto(base + "/portal/casepack/seed"); p2.wait_for_selector(".gr", timeout=8000)
        ck("390 px: the seeding page stacks its rows (no horizontal scroll: %d)" % p2.evaluate("document.documentElement.scrollWidth"), p2.evaluate("document.documentElement.scrollWidth") <= 392)
        ctx2.close(); b.close()
    shutil.rmtree(tmp, ignore_errors=True)
    if fails: print("BROWSER WALK FAILED at %s" % fails); sys.exit(1)
    print("BROWSER WALK OK %d/%d" % (n[0], n[0]))

if __name__ == "__main__":
    main()
