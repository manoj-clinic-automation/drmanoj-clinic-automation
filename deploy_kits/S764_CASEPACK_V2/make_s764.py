#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_s764.py — remakes the kit's two changed files from the LIVE bytes, by counted edits (F-472: no patcher from an
inferred anchor — every anchor below is text read from the live file whole; each must occur exactly once).

  python make_s764.py <from_dir> <to_dir>
    <from_dir>/casepack_page.html   (f95d186d, S685's TO)   ->  <to_dir>/casepack_page.html
    <from_dir>/casepack_portal.py   (cbbd392d, S385's TO)   ->  <to_dir>/casepack_portal.py
  The S764 page block (s764_page_block.html) is read from the kit folder beside this script and appended before </body>.

What the page edits do (D880, the Enquiry stage v2):
  E1  the header's line: packages, rates and estimates on the server
  E2  the stepper: 1 Estimate → 2 Consent → 3 OT & orders → 4 IPD case (nothing 'parked')
  E3  the top of the page: the patient link a quiet line, the procedure search the lead control, the payer segment
      with its small labels, the cash pane (DTH rates fold · Build an estimate fold · My packages) — #q #chips #seg
      #estPb* #tpaCtl #ins #tray #results keep their ids; #cashCtl (#room #stay #hr) goes
  E4  the foot: Next: Consent → · Estimates given · Manage packages (#caseBtn #recBtn #mgr keep their ids)
  R1  the 'Cash package builder' modal (localStorage, "Saves on this device only") and its script go
  R2  the 'Saved estimate records' modal (on-device log) goes — Estimates given is the server's list
  R3  the old cash renderer (room/stay/high-risk controls, present/itemised views, the 50%-of-surgery share) goes;
      renderCash() hands the cash pane to the S764 block
  E7  render(): the cash pane paints itself; Ayushman and TPA render as before
  E8  cpSetStage(): delegates to the S764 block — stages 3 and 4 are live
  E8b the modal observer keeps the stage the owner is on (2 consent / 3 OT & orders) instead of forcing 2
  E14 the payer click shows/hides the cash pane (the old #cashCtl is gone)
  E15 the cash chips
  E16 general ward is the default
  E19 the Build modal's note no longer says 'On this device only' (Save case has written to the ledger since S172)
  R7  the S216 blue-box styling of the patient strip goes (the strip is the quiet line now)
  E18 the S764 block appended before </body>
"""
import os, sys, hashlib, re

HERE = os.path.dirname(os.path.abspath(__file__))

def md5(b): return hashlib.md5(b).hexdigest()

def rep(text, old, new, n=1, tag=""):
    c = text.count(old)
    if c != n:
        raise SystemExit("anchor %s occurs %d time(s), expected %d: %r" % (tag, c, n, old[:90]))
    return text.replace(old, new)

def cut(text, start, end, tag="", keep_end=False):
    """remove from `start` (inclusive) up to `end` (inclusive unless keep_end) — both occur exactly once"""
    if text.count(start) != 1: raise SystemExit("cut-start %s occurs %d time(s): %r" % (tag, text.count(start), start[:90]))
    if text.count(end) != 1: raise SystemExit("cut-end %s occurs %d time(s): %r" % (tag, text.count(end), end[:90]))
    a = text.index(start); b = text.index(end)
    if b < a: raise SystemExit("cut %s: end before start" % tag)
    return text[:a] + (text[b:] if keep_end else text[b + len(end):])

# ------------------------------------------------------------------------------------------------- the page
def make_page(src):
    t = src
    # E1
    t = rep(t, '<div class="sub">Dr. Manoj Agarwal Clinic · Bareilly — tap a result to open every charge head. Offline. No patient data.</div>',
               '<div class="sub">Dr. Manoj Agarwal Clinic · Bareilly — your packages, the DTH rates and every estimate given are on the server: the same list on every device.</div>', tag="E1")
    # E2
    t = rep(t, '''  <button class="cpstep on" data-st="1"><b>1 · Enquiry</b><span>payer · package · patient</span></button>
  <button class="cpstep" data-st="2"><b>2 · Build</b><span>consent first · OT · orders</span></button>
  <button class="cpstep parked" data-st="3"><b>3 · Surgery done</b><span>parked — CP-3</span></button>
  <button class="cpstep parked" data-st="4"><b>4 · Money</b><span>parked — CP-3/CP-4</span></button>''',
               '''  <button class="cpstep on" data-st="1"><b>1 · Estimate</b><span>payer · package · patient</span></button>
  <button class="cpstep" data-st="2"><b>2 · Consent</b><span>Hindi consent · print</span></button>
  <button class="cpstep" data-st="3"><b>3 · OT &amp; orders</b><span>OT list · pre/post-op · notes</span></button>
  <button class="cpstep" data-st="4"><b>4 · IPD case</b><span>admission · papers · money</span></button>''', tag="E2")
    # E3 — the top of the page
    old_top = '''<div class="seg" id="seg">
  <button data-p="cash" class="on">Cash</button>
  <button data-p="ayush">Ayushman</button>
  <button data-p="tpa">TPA</button>
</div>

<div id="estPb" style="display:flex;gap:8px;align-items:center;margin:8px 0;padding:8px 10px;border:1px solid var(--line);border-radius:10px;font-size:13px;flex-wrap:wrap">
  <span id="estPbSel" style="font-weight:600;color:var(--muted)">No patient linked</span>
  <span style="position:relative;flex:1;min-width:160px">
    <input id="estPbQ" placeholder="Link patient — name / ID" autocomplete="off" style="width:100%;padding:6px 10px;border:1px solid var(--line);border-radius:8px;background:inherit;color:inherit">
    <div id="estPbRes" style="position:absolute;left:0;right:0;top:34px;background:var(--card,#fff);border:1px solid var(--line);border-radius:8px;display:none;z-index:40;max-height:220px;overflow:auto"></div>
  </span>
  <span id="estPbDate" style="white-space:nowrap;color:var(--muted)"></span>
</div>
<input class="search" id="q" placeholder="Search procedure, bone, or code…" autocomplete="off">

<div class="controls" id="cashCtl">
  <label>Room <select id="room"></select></label>
  <label>Stay <input id="stay" type="number" min="1" style="width:52px;border:none;font-weight:600;font-size:14px"></label>
  <label><input type="checkbox" id="hr"> High-risk (+₹1300/day)</label>
</div>
<div class="controls" id="tpaCtl" style="display:none">
  <label>Insurer <select id="ins"></select></label>
</div>

<div id="tray"></div>
<div class="chips" id="chips"></div>
<div id="results"></div>
</div>
'''
    new_top = '''<!-- S764 (D880): the patient link a quiet line; the procedure search the lead control; the payer segment; the cash pane from the server -->
<div class="s764pline" id="estPb">
  <span id="estPbSel">No patient linked</span>
  <span class="s764pq">
    <input id="estPbQ" placeholder="Link patient (optional)" autocomplete="off">
    <div id="estPbRes"></div>
  </span>
  <span id="estPbDate" style="white-space:nowrap"></span>
</div>
<div class="s764search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg><input class="search" id="q" placeholder="Procedure, bone or code — e.g. tibia, PFN, SB019" autocomplete="off"></div>
<div class="chips" id="chips"></div>

<div class="seg" id="seg">
  <button data-p="cash" class="on">Cash<small>my packages</small></button>
  <button data-p="ayush">Ayushman<small>HBP 2022 · Tier 2</small></button>
  <button data-p="tpa">TPA<small>10 insurers</small></button>
</div>

<div id="s764cash">
  <details class="s764box" id="s764ratesbox"><summary><span class="k">DTH rates</span><span class="sub" id="s764ratesum"></span></summary>
    <div class="s764rates" id="s764rates"></div>
    <div class="s764acts"><button type="button" class="s764btn" id="s764addrate">+ Add a rate</button><button type="button" class="s764btn pri" id="s764saverates">Save rates</button></div>
    <div class="sub">Per-day rates DTH charges. Edit a figure, add a new ward or head, or delete one; Save keeps them on the server with the date (the old list stays in the history). Every estimate and package reads this list.</div>
  </details>
  <details class="s764box" id="s764buildbox"><summary><span class="k">Build an estimate</span><span class="sub">blank · surgery ₹ · implant ₹ · stay</span></summary>
    <div id="s764buildarea" style="margin-top:8px"></div>
  </details>
  <div class="s764h"><h2>My packages <span class="sub" id="s764count"></span></h2><button type="button" class="s764btn ghost" id="s764refresh" title="Reload from the server">↻</button></div>
  <div class="sub" id="s764note">Saved on the server — the same list on your phone, the clinic PC and Shavez's PC.</div>
  <div id="s764list"></div>
</div>
<div class="controls" id="tpaCtl" style="display:none">
  <label>Insurer <select id="ins"></select></label>
</div>

<div id="tray"></div>
<div id="results"></div>
</div>
'''
    t = rep(t, old_top, new_top, tag="E3")
    # E4 — the foot
    t = rep(t, '''<div class="foot">
  <span id="count" class="sub"></span>
  <span><button id="caseBtn" class="casebtn">Case pack</button> <button id="recBtn">Records</button> <button id="mgr">Build / manage</button></span>
</div>''',
               '''<div class="foot">
  <button id="caseBtn" class="casebtn">Next: Consent →</button>
  <button id="recBtn">Estimates given</button>
  <button id="mgr">Manage packages</button>
  <span id="count" class="sub"></span>
</div>''', tag="E4")
    # R1 — the builder modal (HTML)
    t = cut(t, '<div class="modal" id="modal"><div class="mbox">\n  <h2>Cash package builder</h2>',
               '    <input type="file" id="impFile" accept="application/json" style="display:none">\n  </div>\n</div></div>\n\n', tag="R1")
    # R2 — the records modal (HTML)
    t = cut(t, '<div class="modal" id="recModal"><div class="mbox">\n  <h2>Saved estimate records</h2>',
               '    <button class="cbtn" id="closeR" style="float:right">Close</button>\n  </div>\n</div></div>\n\n', tag="R2")
    # R3e — the on-device package list and its two helpers (the list is the server's now; LOGLS stays as the device's copy)
    t = rep(t, "const LS = 'dma_cash_v1';\nconst LOGLS = 'dma_estlog_v1';   // on-device estimates record (own log)\n",
               "const LOGLS = 'dma_estlog_v1';   // the device's copy of the estimates given; the record is the server's (S764)\n", tag="R3e")
    t = rep(t, "function cashData(){ try{const s=localStorage.getItem(LS); if(s) return JSON.parse(s);}catch(e){} return BUNDLE.cash.map(x=>Object.assign({},x)); }\nfunction saveCash(d){ try{localStorage.setItem(LS, JSON.stringify(d));}catch(e){} }\n",
               "function cashData(){ return (typeof window.s764CashData==='function')? window.s764CashData() : []; }   /* S764: the server's list */\n", tag="R3f")
    # E16 — general ward the default everywhere
    t = rep(t, "let state = {payer:'cash', q:'', room:'pvt', stay:null,", "let state = {payer:'cash', q:'', room:'gen', stay:null,", tag="E16")
    # R3a — the room/stay/high-risk controls' wiring (the controls are gone)
    t = rep(t, '''const roomSel=document.getElementById('room');
BUNDLE.rooms.forEach(r=>{const o=document.createElement('option');o.value=r.key;o.textContent=r.name+' ('+rupee(r.rate)+'/day)';roomSel.appendChild(o);});
roomSel.value='pvt';
''', '', tag="R3a")
    t = rep(t, '''roomSel.addEventListener('change',e=>{state.room=e.target.value;render();});
document.getElementById('stay').addEventListener('input',e=>{state.stay=e.target.value?parseInt(e.target.value):null;render();});
document.getElementById('hr').addEventListener('change',e=>{state.hr=e.target.checked;render();});
''', '', tag="R3b")
    # R3g — the per-day constants and the private share rate: the DTH rates list and the share setting replace them
    t = rep(t, "const HR = BUNDLE.highRiskPerDay;\nconst VISIT_PER_DAY = 1000;      // day-driven, moves with stay like room\nconst NURSING_PER_DAY = 500;     // day-driven, moves with stay like room\nconst SHARE_RATE = 0.5;          // my cut of surgery/OT/image/room/visit (private)\n",
               "/* S764: the per-day figures are the DTH rates list on the server; his share is the share_pct setting (his eyes only) */\n", tag="R3g")
    # E14 — the payer click
    t = rep(t, "  document.getElementById('cashCtl').style.display = state.payer==='cash'?'flex':'none';",
               "  document.getElementById('s764cash').style.display = state.payer==='cash'?'block':'none';   /* S764: the cash pane */", tag="E14")
    # E15 — the cash chips
    t = rep(t, "const CASH_CHIPS=['knee','hip','tibia','clavicle','radius','pfn','bipolar','thr'];",
               "const CASH_CHIPS=['knee','hip','tibia','femur','clavicle','radius','ankle','PFN','bipolar','THR','spine'];", tag="E15")
    # E7 — render(): the cash pane paints itself
    t = rep(t, '''  let cards=[];
  if(state.payer==='cash') cards=renderCash(q);
  else if(state.payer==='ayush') cards=renderAyush(q);''',
               '''  let cards=[];
  if(state.payer==='cash'){ renderCash(q); document.getElementById('count').textContent=''; return; }   /* S764: the cash pane paints itself (#s764cash) from the server's list */
  else if(state.payer==='ayush') cards=renderAyush(q);''', tag="E7")
    # R3c — the old cash renderer and its helpers
    t = cut(t, "/* ---------- CASH: every head separate; Surgery & Implant editable; visit/nursing day-driven ---------- */",
               "/* ---------- AYUSHMAN: implant amount + per-result full-detail copy + cascade ---------- */", tag="R3c", keep_end=True)
    t = rep(t, "/* ---------- AYUSHMAN: implant amount + per-result full-detail copy + cascade ---------- */",
               '''/* ---------- CASH (S764, D880): the packages, the DTH rates and the estimates live on the server; the pane is drawn by the S764 block
   at the foot of the page (window.s764RenderCash) — every estimate line a fold, general ward and the basic implant the defaults. ---------- */
function renderCash(q){ if(typeof window.s764RenderCash==='function') window.s764RenderCash(q); return []; }

/* ---------- AYUSHMAN: implant amount + per-result full-detail copy + cascade ---------- */''', tag="R3d")
    # R6 — the builder / records modal script
    t = cut(t, "/* ---------- builder / records ---------- */", "/* ================= CASE PACK (Phase 1e) ================= */", tag="R6", keep_end=True)
    # E19 — the Build modal's note
    t = rep(t, '<div class="note">On this device only. Print for pharmacy/patient, or WhatsApp/Copy to your assistant. Nothing is synced to any cloud.</div>',
               '<div class="note">Print for pharmacy / patient, or WhatsApp / Copy to your assistant. Save case keeps the case on the server (the ledger, versioned).</div>', tag="E19")
    # R7 — the S216 blue-box styling of the patient strip
    t = rep(t, '''#estPb{border:2px solid var(--blue) !important;background:rgba(59,130,246,.07) !important;font-size:14px}
#estPbQ{border:2px solid var(--blue) !important;font-weight:600;font-size:14px !important;background:rgba(59,130,246,.04) !important}
#estPbSel{font-size:14.5px}
''', '', tag="R7")
    # E8 — cpSetStage delegates; E8b — the observer keeps the stage
    t = rep(t, '''function cpSetStage(n){
 var cm=document.getElementById('caseModal');
 if(n===1){ window.cpStage=1; if(cm) cm.classList.remove('open'); cpPaint(); return; }
 if(n===2){ window.cpStage=2;
   if(cm && !cm.classList.contains('open')){ var b=document.getElementById('caseBtn'); if(b&&b.onclick) b.onclick(); }
   cpFeedForward(); cpPaint(); return; }
 /* 3 & 4 are parked by the owner's word (CP-3 / CP-4) */
 try{ toast('Parked — arrives with CP-'+(n===3?'3':'3/CP-4')); }catch(_e){ alert('Parked — arrives with CP-3/CP-4'); }
}''',
               '''function cpSetStage(n){
 /* S764 (D880): the four stages are live — 1 Estimate · 2 Consent · 3 OT & orders · 4 IPD case (the existing
    'Continue to IPD case'); the body is window.s764SetStage in the S764 block at the foot of the page. */
 if(typeof window.s764SetStage==='function') return window.s764SetStage(n);
 var cm=document.getElementById('caseModal');
 if(n===1){ window.cpStage=1; if(cm) cm.classList.remove('open'); cpPaint(); return; }
 window.cpStage=2; if(cm && !cm.classList.contains('open')){ var b=document.getElementById('caseBtn'); if(b&&b.onclick) b.onclick(); }
 cpFeedForward(); cpPaint();
}''', tag="E8")
    t = rep(t, "   window.cpStage = _open ? 2 : 1;", "   window.cpStage = _open ? (window.cpStage>1?window.cpStage:2) : 1;   /* S764: keep 2 (consent) or 3 (OT & orders) */", tag="E8b")
    # E18 — the S764 block
    with open(os.path.join(HERE, "s764_page_block.html"), "r", encoding="utf-8") as f:
        block = f.read()
    if not block.strip().startswith('<style id="s764css">'): raise SystemExit("s764_page_block.html is not the block")
    t = rep(t, "</script>\n</body>\n</html>", "</script>\n" + block.rstrip("\n") + "\n</body>\n</html>", tag="E18")
    # nothing of the removed builder may survive by name
    for bad in ("renderPkgList", "buildPreview", "applyProfile", "packageFromBuild", "cashMarginData", "mineHtml", "presentQuoteText",
                "getElementById('closeM')", "getElementById('recCsv')", "id=\"cashCtl\"", "id=\"recModal\"", "id=\"modal\"", "parked —", "dma_cash_v1'"):
        if bad in t: raise SystemExit("the removed builder survives by name: %r" % bad)
    for need in ("renderAyush(", "renderTray(", "renderTpa(", "function csGenerate", "s684AnkleOpening", "csFixApply", "function caseBundle", "window.s764Render",
                 "id=\"q\"", "id=\"seg\"", "id=\"estPbQ\"", "id=\"caseBtn\"", "id=\"recBtn\"", "id=\"mgr\"", "id=\"tray\"", "id=\"results\"", "id=\"ins\""):
        if need not in t: raise SystemExit("something the page needs is gone: %r" % need)
    return t

# ------------------------------------------------------------------------------------------------- the server
def make_portal(src):
    t = src
    t = rep(t, "casepack_portal.py — Surgical Case Pack, VPS edition · v2 (S215, CP-1 · D359) · S385: /portal/casepack/trdict",
               "casepack_portal.py — Surgical Case Pack, VPS edition · v2 (S215, CP-1 · D359) · S385: /portal/casepack/trdict · S764: casepack_v2 (packages · rates · estimates · templates · seed)", tag="P1")
    t = rep(t, "            return jsonify({\"ok\": False, \"error\": str(e)}), 500\n\n    return True\n",
               '''            return jsonify({"ok": False, "error": str(e)}), 500

    # --- S764 (09-Nov-2026, D880): the enquiry v2 — cash packages, the DTH rates, the estimates given, the fracture
    # templates and the seeding page live in casepack_v2.py beside this file, behind the SAME owner-only guard. A failure
    # there must never take the Case Pack down: the routes above still serve, and the page says what is missing. ---
    try:
        import casepack_v2
        casepack_v2.register(app, guard, get_user)
        CASEPACK_V2_IMPORT_ERR = ""
    except Exception as _v2e:                    # fail loud where the page looks AND in the journal, never brick the portal
        CASEPACK_V2_IMPORT_ERR = str(_v2e)
        import sys as _sys
        print("casepack_v2 failed to load: " + CASEPACK_V2_IMPORT_ERR, file=_sys.stderr)

        @app.route("/portal/casepack/packages")
        @guard
        def casepack_v2_broken():
            return jsonify({"ok": False, "error": "casepack_v2 failed to load: " + CASEPACK_V2_IMPORT_ERR}), 500

    return True
''', tag="P2")
    return t

def main():
    if len(sys.argv) != 3: raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    os.makedirs(dst, exist_ok=True)
    with open(os.path.join(src, "casepack_page.html"), "rb") as f: pb = f.read()
    with open(os.path.join(src, "casepack_portal.py"), "rb") as f: sb = f.read()
    print("FROM casepack_page.html %s  casepack_portal.py %s" % (md5(pb)[:8], md5(sb)[:8]))
    page = make_page(pb.decode("utf-8"))
    portal = make_portal(sb.decode("utf-8"))
    for name, text in (("casepack_page.html", page), ("casepack_portal.py", portal)):
        b = text.encode("utf-8")
        if b"\r\n" in b: raise SystemExit("CRLF in " + name)
        with open(os.path.join(dst, name), "wb") as f: f.write(b)
        print("TO   %s %s  %d bytes" % (name, md5(b), len(b)))

if __name__ == "__main__":
    main()
