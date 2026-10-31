#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""walk_s684.py -- kit S684_CONSENT_ANKLE_STAGED: the consent generator driven in a real browser (Chromium, Playwright)
with a MADE-UP patient (no patient's name or number anywhere). Proves every new choice prints what the owner approved,
that the old procedures print exactly as before (regression against the FROM page), and that a saved case comes back.

  python3 walk_s684.py NEW.html [--old OLD.html] [--control] [--shots DIR]

--control runs the S684 checks against OLD.html (the live page): they must go RED there and the regression checks GREEN.
The last line is the verdict: 'walk_s684: N of N green' (or, with --control, 'control: R S684 red · 0 older red · G green').
"""
import argparse
import os
import sys

from playwright.sync_api import sync_playwright

NAME = "Ramesh Kumar Test"      # made up; transliterated by the page's own offline rules
AGE = "45"

checks = []          # (id, kind, ok, note)   kind: 'S684' new behaviour, 'OLD' must hold before and after


def ok(cid, kind, cond, note=""):
    checks.append((cid, kind, bool(cond), note))


def open_page(browser, path):
    pg = browser.new_page(viewport={"width": 1366, "height": 900})
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route("**/*", lambda r: r.abort() if not r.request.url.startswith("file:") else r.continue_())
    pg.goto("file://" + os.path.abspath(path))
    pg.wait_for_timeout(400)
    pg.click("#caseBtn")
    pg.click('#caseSub button[data-s="consent"]')
    return pg, errs


def reset(pg, proc, side="बाएँ", part="गट्टे (टखने)", bone=""):
    pg.evaluate("""([proc,side,part,bone,name,age])=>{
      document.getElementById('c_name').value=name; document.getElementById('c_age').value=age;
      var s=document.getElementById('c_side'); s.value=side; s.dispatchEvent(new Event('change'));
      var p=document.getElementById('c_part'); p.value=part; p.dispatchEvent(new Event('change'));
      try{ boneFill(); }catch(e){}
      var b=document.getElementById('c_bone'); b.value=bone; b.dispatchEvent(new Event('change'));
      document.getElementById('cs_dur').value='कल';
      document.getElementById('cs_relmark').value='पुत्र श्री'; document.getElementById('cs_relname').value='Suresh Test';
      [].forEach.call(document.querySelectorAll('#pane_consent input[type=checkbox]'),function(e){e.checked=false;});
      var op=document.getElementById('fm_opnow'); if(op) op.checked=true;
      [].forEach.call(document.querySelectorAll('input[name=fm_stage][value=""],input[name=ank_jt][value=""],input[name=fm_mob][value=normal],input[name=fm_comm][value=""],input[name=fm_art][value=""],input[name=fm_grade][value=""]'),function(e){e.checked=true;});
      var pc=document.querySelector('input[name=fm_path]:checked'); if(pc) pc.checked=false;
      try{ fxRestore([]); }catch(e){}
      var ps=document.getElementById('cs_proc'); ps.value=proc; ps.dispatchEvent(new Event('change'));
      try{ fmSync(); }catch(e){}
      window.cp11Ok=null;
    }""", [proc, side, part, bone, NAME, AGE])


def tick(pg, *ids):
    for i in ids:
        pg.evaluate("(i)=>{var e=document.getElementById(i); if(e){e.checked=true; e.dispatchEvent(new Event('change'));}}", i)


def radio(pg, name, val):
    pg.evaluate("([n,v])=>{var e=document.querySelector('input[name='+n+'][value=\"'+v+'\"]'); if(e){e.checked=true; e.dispatchEvent(new Event('change'));}}", [name, val])


def gen(pg):
    pg.evaluate("async()=>{ await csGenerate(); }")
    pg.wait_for_timeout(150)
    return pg.evaluate("()=>document.getElementById('cs_out').innerText")


def shot(pg, d, name):
    if d:
        os.makedirs(d, exist_ok=True)
        pg.screenshot(path=os.path.join(d, name), full_page=False)


def run(path, old, control, shots):
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg, errs = open_page(br, path)
        has_box = pg.evaluate("()=>!!document.getElementById('s684_ank')")

        # ---- A: the owner's patient -- medial + posterior, subluxation, ex-fix now, fixed-with blank; shoulder plan later
        reset(pg, "ankle")
        vis = pg.evaluate("()=>{var b=document.getElementById('s684_ank'); return !!b && b.style.display!=='none';}")
        ok("A1 the ankle box shows for the ankle procedure", "S684", vis)
        tick(pg, "ank_med", "ank_post"); radio(pg, "ank_jt", "sub"); radio(pg, "fm_stage", "exfix")
        inslot = pg.evaluate("()=>{var s=document.getElementById('s684_stagebox'); return !!s && s.parentNode && s.parentNode.id==='s684_stage_slot';}")
        ok("A2 the plan-now choice sits inside the ankle box", "S684", inslot)
        summ = pg.evaluate("()=>(document.getElementById('s684_sum')||{}).textContent||''")
        ok("A3 the box reads 'Bimalleolar (medial + posterior), subluxation -- external fixator now'", "S684",
           "Bimalleolar (medial + posterior), subluxation" in summ and "external fixator now" in summ, summ)
        t = gen(pg)
        shot(pg, shots, "A_owner_case.png")
        ok("A4 the opening names the inner and back bones, plural", "S684",
           "अंदर की ओर की हड्डी और पीछे की ओर की हड्डी कल टूट गई हैं।" in t, t[:300])
        ok("A5 the opening says the joint is partly out of place", "S684", "आंशिक रूप से खिसक गया है" in t)
        ok("A6 nothing promises plate-screws", "S684", "प्लेट-पेंच से जोड़ा" not in t and "प्लेट-पेंच द्वारा" not in t)
        ok("A7 the two-stage plan: external fixator now, then screws, wires or plate", "S684",
           "अभी पहले चरण में टखने के जोड़ और हड्डियों को अपनी जगह बैठाकर बाहरी फिक्सेटर" in t and
           "शिकंजा निकालकर हड्डियों को पेंच, तार या प्लेट (जो ऑपरेशन के समय उचित हो) द्वारा जोड़ा जाएगा।" in t)
        ok("A8 the scope: this consent is for the first stage only", "S684",
           "यह सहमति अभी किए जा रहे पहले चरण — टखने में बाहरी फिक्सेटर (शिकंजा) लगाने — के लिए दी जा रही है।" in t)
        ok("A9 the ex-fix risks and the joint risks print", "S684", "शिकंजे (बाहरी फिक्सेटर) से जुड़े जोखिम" in t and
           "जोड़ तक पहुँची चोट से जुड़े जोखिम" in t and "जोड़ खिसका होने पर" in t)
        ok("A10 Hindi print drops the English brackets", "S684", "(medial malleolus)" not in t and "external fixator" not in t)
        en = pg.evaluate("()=>{var q=CONSENT_LIB.find(function(x){return x.k==='ankle';}); return (typeof s684ProcEn==='function')?s684ProcEn(q):q.en;}")
        ok("A11 the OT notes' procedure name follows the ticks", "S684", en.startswith("Ankle fracture — Bimalleolar"), en)
        tmpl = pg.evaluate("()=>{ if(!document.getElementById('ank_med')) return CONSENT_LIB.find(function(x){return x.k==='ankle';}).o; ['ank_med','ank_lat','ank_post'].forEach(function(i){document.getElementById(i).checked=false;}); var z=document.querySelector('input[name=ank_jt][value=\"\"]'); z.checked=true; var o=CONSENT_LIB.find(function(x){return x.k==='ankle';}).o; document.getElementById('ank_med').checked=true; document.getElementById('ank_post').checked=true; document.querySelector('input[name=ank_jt][value=sub]').checked=true; return o; }")
        ok("A12 the ankle template keeps no state: with nothing ticked it reads plain", "S684", "की हड्डियाँ {DUR} टूट गई हैं। " in tmpl and "अंदर की ओर" not in tmpl and "प्लेट" not in tmpl, tmpl[:120])
        # the same patient with the shoulder as an extra fracture, plan later
        pg.evaluate("()=>{ fxAdd({s:'बाएँ',p:'कंधे',b:'बाजू की हड्डी का ऊपरी सिरा',pl:1}); fmSync(); }")
        t2 = gen(pg)
        shot(pg, shots, "A_owner_case_with_shoulder.png")
        ok("A13 the shoulder is named in the opening", "S684", "साथ ही बाएँ बाजू की हड्डी का ऊपरी सिरा भी टूटी है।" in t2, t2[:500])
        ok("A14 'plan later': with or without an operation, decided later", "S684",
           "शेष हड्डियों की योजना:" in t2 and "बाएँ बाजू की हड्डी का ऊपरी सिरा का इलाज ऑपरेशन द्वारा होगा या बिना ऑपरेशन" in t2)
        ok("A15 one scope only, naming the rest for later", "S684",
           t2.count("इस सहमति का दायरा:") == 1 and "दूसरे चरण के ऑपरेशन तथा शेष हड्डियों के इलाज के लिए अलग से सहमति ली जाएगी।" in t2)
        # save and come back
        snap = pg.evaluate("()=>JSON.stringify(csFieldsSnap())")
        reset(pg, "generic", part="जांघ")
        pg.evaluate("(s)=>{ var f=JSON.parse(s); csFieldsRestore(f); }", snap)
        back = pg.evaluate("()=>[!!document.getElementById('ank_med').checked, !!document.getElementById('ank_post').checked, !!document.getElementById('ank_lat').checked, (document.querySelector('input[name=ank_jt]:checked')||{}).value, (document.querySelector('input[name=fm_stage]:checked')||{}).value, document.getElementById('cs_proc').value]") if has_box else []
        ok("A16 a saved case comes back with its ticks", "S684", back == [True, True, False, "sub", "exfix", "ankle"], str(back))

        # ---- B: one bone, fix now, screws only
        reset(pg, "ankle"); tick(pg, "ank_lat", "ank_fw_screw")
        t = gen(pg)
        ok("B1 one bone: singular, 'इसे ... पेंच द्वारा जोड़ा जाएगा'", "S684",
           "बाहर की ओर की हड्डी कल टूट गई है।" in t and "इसे ऑपरेशन करके पेंच द्वारा जोड़ा जाएगा।" in t, t[:300])
        ok("B2 fix now prints no two-stage plan and no stage scope", "S684", "इलाज की योजना:" not in t and "पहले चरण" not in t)
        ok("B3 lateral only, in place: no joint-risk paragraph", "S684", "जोड़ तक पहुँची चोट से जुड़े जोखिम" not in t)

        # ---- C: three bones, dislocation, fix now, plate + wire
        reset(pg, "ankle"); tick(pg, "ank_med", "ank_lat", "ank_post", "ank_fw_plate", "ank_fw_wire"); radio(pg, "ank_jt", "dis")
        summ = pg.evaluate("()=>(document.getElementById('s684_sum')||{}).textContent||''")
        t = gen(pg)
        ok("C1 three bones listed with commas and 'और'", "S684",
           "अंदर की ओर की हड्डी, बाहर की ओर की हड्डी और पीछे की ओर की हड्डी कल टूट गई हैं।" in t, t[:300])
        ok("C2 dislocation: fully out of place", "S684", "पूरी तरह खिसक गया है" in t)
        ok("C3 plate + wires: 'प्लेट या तार द्वारा'", "S684", "इन्हें ऑपरेशन करके प्लेट या तार द्वारा जोड़ा जाएगा।" in t)
        ok("C4 the box reads Trimalleolar, dislocation", "S684", "Trimalleolar, dislocation" in summ, summ)

        # ---- D: nothing ticked, fix now -- the neutral line
        reset(pg, "ankle")
        t = gen(pg)
        ok("D1 nothing ticked: the bones generically, fixed with 'screws, wires or plate -- as suitable'", "S684",
           "गट्टे (टखने) की हड्डियाँ कल टूट गई हैं।" in t and
           "इन्हें ऑपरेशन करके पेंच, तार या प्लेट (जो ऑपरेशन के समय उचित हो) द्वारा जोड़ा जाएगा।" in t, t[:300])

        # ---- E: the cold review's findings (round 1), each a check
        nslab = pg.evaluate("()=>document.querySelectorAll('input[name=fm_stage][value=slab]').length")
        ok("E1 no 'plaster / slab now' option in this kit (the rest of the consent speaks of an operation)", "S684", has_box and nslab == 0)
        reset(pg, "ankle", bone="टखने की दोनों हड्डियाँ"); tick(pg, "ank_med")
        t = gen(pg)
        ok("E2 one bone ticked with a plural bone field: still singular", "S684", "अंदर की ओर की हड्डी कल टूट गई है।" in t, t[:200])
        reset(pg, "ankle"); tick(pg, "ank_med", "ank_post"); radio(pg, "fm_stage", "exfix")
        reset(pg, "ankle"); tick(pg, "ank_med"); radio(pg, "ank_jt", "dis")
        t = pg.evaluate("""async()=>{ var orig=csHindi, n=0;
            csHindi=function(s){ n++; var d=(n<=2)?400:10; return new Promise(function(r){ setTimeout(function(){ r(orig(s)); }, d); }); };
            var a=csGenerate(); await new Promise(function(r){setTimeout(r,30);}); var b=csGenerate(); await a; await b;
            csHindi=orig; return document.getElementById('cs_out').innerText; }""")
        ok("E3 two overlapping generations (the first slower): the print still follows the ticks", "S684",
           "अंदर की ओर की हड्डी कल टूट गई है।" in t and "पूरी तरह खिसक गया है" in t and "इसे ऑपरेशन करके" in t, t[:220])
        pg.evaluate("()=>{ fxAdd({s:'बाएँ',p:'कंधे',b:'बाजू की हड्डी का ऊपरी सिरा',n:1}); }")
        pg.evaluate("()=>{ var r=document.querySelector('#fx_list .fxrow'); var e=r&&r.querySelector('.fx_pl'); if(!e) return; e.checked=true; e.dispatchEvent(new Event('change',{bubbles:true})); }")
        both = pg.evaluate("()=>{ var r=document.querySelector('#fx_list .fxrow'); if(!r||!r.querySelector('.fx_pl')) return []; return [r.querySelector('.fx_n').checked, r.querySelector('.fx_pl').checked]; }")
        ok("E4 'op now' and 'plan later' exclude each other", "S684", both == [False, True], str(both))
        radio(pg, "fm_stage", "exfix")
        st0 = pg.evaluate("()=>(document.querySelector('input[name=fm_stage]:checked')||{}).value")
        pg.evaluate("()=>{ var e=document.getElementById('fm_opnow'); e.checked=false; e.dispatchEvent(new Event('change',{bubbles:true})); }")
        st = pg.evaluate("()=>(document.querySelector('input[name=fm_stage]:checked')||{}).value")
        ok("E5 un-ticking 'operated now' takes the plan back to fix now", "S684", st0 == "exfix" and st == "", repr((st0, st)))
        reset(pg, "ankle"); tick(pg, "ank_med", "ank_lat", "fm_compound"); radio(pg, "fm_path", "C")
        t = gen(pg)
        ok("E6 open ankle with the fixator pathway: no 'joined now' sentence", "S684", "ऑपरेशन करके" not in t and "तीसरा तरीका" in t)
        reset(pg, "tkr", part="घुटने")
        hid = pg.evaluate("()=>{ var s=document.getElementById('s684_stagebox'); return !!s && s.style.display==='none'; }")
        ok("E7 a planned operation (TKR) shows no 'plan now'", "S684", hid)

        # ---- F: the staged plan on another CLOSED fracture (distal tibia)
        reset(pg, "dtibia", part="टांग", bone="पैर की मोटी हड्डी")
        hidden = pg.evaluate("()=>{var b=document.getElementById('s684_ank'); return !b || b.style.display==='none';}")
        ingrid = pg.evaluate("()=>{var s=document.getElementById('s684_stagebox'); return !!s && s.parentNode && s.parentNode.id==='fmGrid';}")
        ok("F1 another procedure: no ankle box; the plan-now choice is back in the fracture panel", "S684", hidden and ingrid)
        radio(pg, "fm_stage", "exfix")
        t = gen(pg)
        ok("F2 distal tibia, closed, ex-fix now: the generic plan and scope", "S684",
           "अभी पहले चरण में हड्डी को अपनी जगह बैठाकर बाहरी फिक्सेटर" in t and
           "शिकंजा निकालकर हड्डी जोड़ने का पक्का ऑपरेशन किया जाएगा।" in t and
           "पहले चरण — बाएँ पैर की मोटी हड्डी में बाहरी फिक्सेटर (शिकंजा) लगाने" in t, t[:200])
        ok("F3 a closed fracture never prints the open-fracture wording", "S684", "खुला फ्रैक्चर" not in t and "खुले फ्रैक्चर" not in t)

        # ---- G: an OPEN fracture keeps its own pathway; the plan-now box stands aside
        reset(pg, "dtibia", part="टांग", bone="पैर की मोटी हड्डी")
        radio(pg, "fm_stage", "exfix"); tick(pg, "fm_compound"); radio(pg, "fm_path", "C")
        dis = pg.evaluate("()=>[].every.call(document.querySelectorAll('input[name=fm_stage]'),function(r){return r.disabled;})")
        t = gen(pg)
        ok("G1 open fracture: the plan-now choice is greyed out", "S684", dis)
        ok("G2 open fracture: the pathway prints, chosen = the third (external fixator)", "S684",
           "तीसरा तरीका — बाहरी फिक्सेटर" in t and "चुना गया तरीका" in t)
        ok("G3 ... and no S684 two-stage paragraph", "S684", "इलाज की योजना:" not in t)

        # ---- H: the bone list
        opts = pg.evaluate("()=>boneOpts('गट्टे (टखने)')")
        ok("H1 the ankle's bone list carries the posterior malleolus", "S684",
           "टखने की पीछे की हड्डी (posterior malleolus)" in opts and "टखने की तीनों हड्डियाँ" in opts, str(opts))
        # the plural guard: an opening already plural with a plural bone is not doubled
        reset(pg, "dtibia", part="टांग", bone="पैर की दोनों हड्डियाँ")
        t = gen(pg)
        ok("H2 no doubled ending ('हैंं') when the bone is plural", "S684", "हैंं" not in t, t[:200])

        ok("Z1 no script error on the page", "S684", not errs, "; ".join(errs[:3]))
        br.close()


def regression(new, old):
    """The procedures S684 does not touch print the same consent before and after."""
    cases = [("generic", "जांघ", "जांघ की हड्डी", []), ("shoulder", "कंधे", "बाजू की हड्डी का ऊपरी सिरा", []),
             ("itfix", "कूल्हे", "जांघ की हड्डी का ऊपरी भाग", ["fm_geri", "fm_osteo"]),
             ("dtibia", "टांग", "पैर की मोटी हड्डी", ["fm_compound"]), ("tkr", "घुटने", "", [])]
    with sync_playwright() as p:
        br = p.chromium.launch()
        outs = {}
        for tag, path in (("new", new), ("old", old)):
            pg, errs = open_page(br, path)
            for proc, part, bone, ticks in cases:
                reset(pg, proc, part=part, bone=bone)
                tick(pg, *ticks)
                if "fm_compound" in ticks:
                    radio(pg, "fm_path", "C")
                if proc == "tkr":
                    pg.evaluate("()=>{window.cp11Ok='tkr';}")
                outs[(tag, proc)] = gen(pg)
            outs[(tag, "errs")] = errs
            pg.close()
        br.close()
    for proc, _p, _b, _t in cases:
        same = outs[("new", proc)] == outs[("old", proc)]
        ok("R-%s prints exactly as before" % proc, "OLD", same and len(outs[("new", proc)]) > 200,
           "" if same else "differs")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--old")
    ap.add_argument("--control", action="store_true")
    ap.add_argument("--shots")
    a = ap.parse_args()
    target = a.old if a.control else a.page
    run(target, a.old, a.control, a.shots)
    if a.old:
        regression(a.page, a.old)
    for cid, kind, good, note in checks:
        print("%s %s%s" % ("GREEN" if good else "RED  ", cid, (" -- " + note[:160]) if (note and not good) else ""))
    g = sum(1 for c in checks if c[2])
    if a.control:
        r684 = sum(1 for c in checks if c[1] == "S684" and not c[2])
        rold = sum(1 for c in checks if c[1] == "OLD" and not c[2])
        print("control: %d S684 red · %d older red · %d green" % (r684, rold, g))
    else:
        print("walk_s684: %d of %d green" % (g, len(checks)))


if __name__ == "__main__":
    main()
