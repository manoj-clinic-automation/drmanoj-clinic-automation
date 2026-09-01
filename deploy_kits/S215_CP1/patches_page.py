#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_page.py — builds the CP-1 casepack_page.html (S215 · D359 CP-1)
========================================================================
Reads the S172/S204-era portal page (the live page's repo twin, verified
against the live pin lineage) and applies ANCHORED patches. Every anchor
must match EXACTLY ONCE or the build aborts — nothing is ever patched by
guesswork (the F-109/F-141 family).

The Post-Polio consent paragraphs are EXTRACTED VERBATIM from the signed
contract paper (S214_CASEPACK_V2_IDEATION.md) — never retyped (owner rule:
consent text comes only from the casepack template store; the polio draft
is the owner's own, lifted byte-true from his paper).

Usage:  python3 patches_page.py <base_page> <contract_paper> <out_page>
"""
import sys, re, hashlib

def main():
    base_fp, paper_fp, out_fp = sys.argv[1], sys.argv[2], sys.argv[3]
    src = open(base_fp, encoding="utf-8").read()
    paper = open(paper_fp, encoding="utf-8").read()

    # ---- extract the owner's polio paragraphs from the contract paper ----
    m = re.search(r"Draft content \(owner\s*\n?\s*edits\):(.*?)- Anything the owner tweaks",
                  paper, re.S)
    assert m, "polio draft block not found in the contract paper"
    block = m.group(1)
    bullets, cur = [], None
    for ln in block.splitlines():
        if re.match(r"^\s+- ", ln):
            if cur: bullets.append(cur)
            cur = ln.strip()[2:].strip()
        elif ln.strip() and cur is not None:
            cur += " " + ln.strip()
    if cur: bullets.append(cur)
    assert len(bullets) == 5, "expected the 5 owner-drafted polio paragraphs, got %d" % len(bullets)
    polio_js = ",\n   ".join("'" + b.replace("\\", "\\\\").replace("'", "\\'") + "'" for b in bullets)

    n_applied = [0]
    def patch(old, new, count=1, label=""):
        c = src_ref[0].count(old)
        assert c == count, "ANCHOR FAIL (%s): found %d of expected %d: %r" % (label, c, count, old[:70])
        src_ref[0] = src_ref[0].replace(old, new)
        n_applied[0] += 1
    src_ref = [src]

    # P1 — identity: this is the Case Pack now (stage 1 = enquiry & estimate)
    patch("<title>Surgical Estimate Finder — Dr. Manoj Agarwal</title>",
          "<title>Surgical Case Pack — Dr. Manoj Agarwal</title>", 1, "title")
    patch("<h1>Surgical Estimate Finder</h1>",
          "<h1>Surgical Case Pack</h1>", 1, "h1")

    # P2 — the stepper (D359: the Vaapsi-Desk stepper pattern replaces the
    # three unintuitive bottom buttons as primary navigation)
    stepper = """</header>

<style>
#cpStepper{display:flex;gap:6px;margin:10px 0 12px;flex-wrap:wrap}
#cpStepper .cpstep{flex:1;min-width:130px;border:1px solid var(--line);border-radius:12px;padding:8px 10px;cursor:pointer;background:transparent;text-align:left;font:inherit;color:inherit}
#cpStepper .cpstep b{display:block;font-size:13px}
#cpStepper .cpstep span{font-size:11px;color:var(--muted)}
#cpStepper .cpstep.on{border-color:var(--blue);box-shadow:0 0 0 2px rgba(59,130,246,.25)}
#cpStepper .cpstep.parked{opacity:.55;cursor:default}
h3.cs-mod{margin:14px 0 4px;font-size:16px}
</style>
<div id="cpStepper">
  <button class="cpstep on" data-st="1"><b>1 · Enquiry</b><span>payer · package · patient</span></button>
  <button class="cpstep" data-st="2"><b>2 · Build</b><span>consent first · OT · orders</span></button>
  <button class="cpstep parked" data-st="3"><b>3 · Surgery done</b><span>parked — CP-3</span></button>
  <button class="cpstep parked" data-st="4"><b>4 · Money</b><span>parked — CP-3/CP-4</span></button>
</div>"""
    patch("</header>", stepper, 1, "stepper")

    # P3 — the polio module in the ONE template store (edit once, every
    # future consent gains it; extensible: add entries to POLIO_MODULES)
    polio_store = """var POLIO_MODULES=[
 {k:'thr_fnf',en:'Total Hip Replacement (fracture neck of femur)',
  h:'पोलियो + गर्दन फ्रैक्चर — विशेष स्थिति (Post-Polio)',
  ps:[POLIO_PS_1]}
];
var csLastMeta=null;"""
    polio_store = polio_store.replace("POLIO_PS_1", polio_js)
    patch("var csLastMeta=null;", polio_store, 1, "polio-store")

    # P4 — polio toggle UI (before the comorbidities hint)
    polio_ui = """<div id="polioWrap" style="border:2px solid #7c3aed;border-radius:12px;padding:10px 14px;margin:8px 0;background:rgba(124,58,237,.05)">
      <label style="display:flex;gap:8px;align-items:center;cursor:pointer"><input type="checkbox" id="cs_polio" onchange="polioSync()"> <b>Post-Polio (विशेष स्थिति)</b>&nbsp;— include polio-specific consent</label>
      <div id="polioSub" style="display:none;margin-top:6px;font-size:13px">Procedure: <select id="cs_polio_proc" style="max-width:100%"></select></div>
    </div>
    <div class="casehint"><b>Patient condition (comorbidities)</b>"""
    patch('<div class="casehint"><b>Patient condition (comorbidities)</b>', polio_ui, 1, "polio-ui")

    # P5 — csGenerate: push the polio block (own heading) after the
    # procedure/implant paragraph, before the generic risk block
    anch = "if(proc.d && !(_implantTick && _isArthro)) paras.push(csFill(proc.d,v));"
    patch(anch, anch + "\n try{ var _pcb=document.getElementById('cs_polio'); if(_pcb&&_pcb.checked){ var _pm=POLIO_MODULES.find(function(x){return x.k===((document.getElementById('cs_polio_proc')||{}).value||'');})||POLIO_MODULES[0]; paras.push({h:_pm.h,ps:_pm.ps}); } }catch(_e){}",
          1, "polio-generate")

    # P6 — the html assembler learns headed blocks
    old_loop = "paras.forEach(function(p){ html+='<p>'+p.replace(/\\s{2,}/g,' ').trim()+'</p>'; });"
    new_loop = ("paras.forEach(function(p){ if(p&&p.h){ html+='<h3 class=\"cs-mod\">'+p.h+'</h3>'; "
                "(p.ps||[]).forEach(function(q){ html+='<p>'+String(q).replace(/\\s{2,}/g,' ').trim()+'</p>'; }); return; } "
                "html+='<p>'+String(p).replace(/\\s{2,}/g,' ').trim()+'</p>'; });")
    patch(old_loop, new_loop, 1, "html-loop")

    # P7 — save row: change-note input + consent history button
    patch('<span id="caseSaveMsg" style="font-size:12px;color:var(--muted)"></span>',
          '<input id="cs_change_note" placeholder="Consent change note (only if content changed)" style="flex:1;min-width:140px;padding:6px 8px;border:1px solid var(--line);border-radius:8px;background:inherit;color:inherit;font-size:12px">\n'
          '    <button class="cbtn ghost" id="cs_hist" type="button">Consent history</button>\n'
          '    <span id="caseSaveMsg" style="font-size:12px;color:var(--muted)"></span>', 1, "save-row")
    patch('<button class="cbtn" id="closeCase" style="margin-left:auto">Close</button>\n  </div>',
          '<button class="cbtn" id="closeCase" style="margin-left:auto">Close</button>\n  </div>\n'
          '  <div id="cs_hist_panel" style="display:none;margin-top:8px;border:1px solid var(--line);border-radius:10px;padding:8px 10px;font-size:13px"></div>', 1, "hist-panel")

    # P8 — save response narrates the consent verdict (new / re-issue / revision)
    old_msg = "msg.textContent='✓ Saved: '+j.case_id+(j.version&&j.version>1?(' (v'+j.version+')'):'')"
    new_msg = (old_msg + "+(j.consent?(' · Consent: '+(j.consent.kind==='reissue'?('re-issued c'+j.consent.no+' ('+j.consent.issue_date+')'):(j.consent.kind==='revision'?('REVISED → c'+j.consent.no):'c1 issued'))):'')")
    patch(old_msg, new_msg, 1, "save-msg")

    # P9 — English chrome (owner ruling 1; consent output stays Hindi)
    patch('placeholder="Patient khoje — Clinic ID / naam / mobile / UID"',
          'placeholder="Find patient — Clinic ID / name / mobile / UID"', 1, "pb-placeholder")
    patch("'<div style=\"padding:6px;font-size:13px;color:var(--muted)\">Koi match nahin</div>'",
          "'<div style=\"padding:6px;font-size:13px;color:var(--muted)\">No match</div>'", 1, "no-match")
    patch("if(!b.patient.uid && !confirm('Koi patient link nahin hua (UID blank). Phir bhi save karein?')) return;",
          "if(!b.patient.uid && !b.patient.clinic_id && !confirm('No patient linked. Save anyway?')) return;", 1, "confirm-en")
    patch("msg.textContent='Downloaded (offline mode) — clinic PC par cases\\\\inbox\\\\ me daal dijiye.'; return;",
          "msg.textContent='Downloaded (offline mode) — drop the file into cases\\\\inbox\\\\ on the clinic PC.'; return;", 1, "offline-en")
    patch('<h2>Case pack — after estimate is finalised</h2>',
          '<h2>Case Pack — Build (तैयारी)</h2>', 1, "h2-build")

    # P10 — search rows show the source register (Docterz master vs console)
    old_row = "(m.Age?(' · '+escapeHtml(String(m.Age))+'y'):'');\n         d.onclick=function(){ pbPick(m); };"
    new_row = ("(m.Age?(' · '+escapeHtml(String(m.Age))+'y'):'')"
               "+(m.Source?(' <span style=\"font-size:10px;border:1px solid var(--line);border-radius:8px;padding:0 5px;color:var(--muted)\">'+(m.Source==='master'?'Docterz':'console')+'</span>'):'');\n"
               "         d.onclick=function(){ pbPick(m); };")
    patch(old_row, new_row, 1, "source-tag")

    # P10b — publish-gate hygiene: a rupee RANGE in the TPA data reads as one
    # 10+-digit run to NO_PHONE_NUMBERS.py (the dash joins the digits). Reword,
    # value unchanged. (Base page carries the same bytes, unstaged; recorded.)
    patch("[UNREADABLE - approx 62000" + "-" + "62500]",
          "[UNREADABLE - approx 62000 to 62500]", 1, "tariff-range")  # split so this file itself carries no joined run

    # P11 — the CP-1 wiring block (stepper logic · feed-forward · polio ·
    # snapshot wrappers · consent history) — added at the very end so every
    # base function it wraps already exists
    wiring = open(__file__.replace("patches_page.py", "cp1_wiring.js"), encoding="utf-8").read()
    patch("</body>", "<script>\n" + wiring + "\n</script>\n</body>", 1, "wiring")

    out = src_ref[0]
    assert "POLIO_MODULES" in out and "cpStepper" in out
    with open(out_fp, "w", encoding="utf-8") as f:
        f.write(out)
    print("patches applied:", n_applied[0])
    print("out md5:", hashlib.md5(out.encode("utf-8")).hexdigest())
    print("out bytes:", len(out.encode("utf-8")))

if __name__ == "__main__":
    main()
