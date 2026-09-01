#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_cp11_tone.py - CP-1.1 step 4: flow, tone, and the language switch
==========================================================================
Base = the S216 smart page (LIVE, pin 62d472fd...).
Six ANCHORED patches. THIS KIT CHANGES CONSENT WORDING, on the owner's
written instructions in D:\\Downloads\\CONSENT_TONE_S216_FOR_YOUR_PEN.txt
(md5 21cf41e9...), and on nothing else.

WHAT THE OWNER RULED
  Part B - "none needed": every bracketed English gloss may disappear in
           Hindi-only mode. Nothing is kept always.
  Part C - 1: "एक्सरे और एमआरआई जांच"   (his wording)
           2: "नई लिगामेंट बनाकर"       (already bracketed - the switch does it)
           3: "घुटने की लिगामेंट (ACL)"  (unchanged - the switch does it)
  Part D - the switch starts on हिंदी every time; it does NOT remember.

THE GLOSS SWITCH
  In Hindi-only mode, a bracketed group containing Latin letters is dropped
  from the printed paragraphs. It is applied ONLY inside the paragraph loop,
  so the attestation line - which carries the owner's (M.S. Ortho) - is
  untouched by construction rather than by a list that could rot.
  The STORE is never edited by the switch, so no word can be lost.

Usage:  python3 patches_cp11_tone.py <base_page> <out_page>
"""
import sys, hashlib

BASE_MD5 = "62d472fd8e08f54403858c5fb88de9bf"

# ---- 1 · the polio module: flowing prose, no heading, no English ----------
# The whole block is replaced, located by its own boundaries and verified by
# what it must contain - never by re-typing the old Hindi.
POLIO_OLD_MUST_CONTAIN = "पोलियो + गर्दन फ्रैक्चर"
POLIO_NEW = (
 "var POLIO_MODULES=[\n"
 " {k:'thr_fnf',en:'Total Hip Replacement (fracture neck of femur)',\n"
 "  h:'',\n"
 "  ps:['मरीज को बचपन में "
 "पोलियो हुआ था — "
 "इसलिए यह एक विशेष "
 "स्थिति है।',\n"
 "   'हमें बता दिया गया है कि जिस पैर की हड्डी टूटी है, उसी पैर में पोलियो का असर है — हड्डी पतली है और मांसपेशियाँ बहुत कमजोर और अधूरी बनी हुई हैं। पतली हड्डी होने के कारण ऑपरेशन के दौरान या उसके बाद हड्डी चटकने का, या जोड़ में लगने वाले सामान के आसपास हड्डी टूट जाने का खतरा आम मरीजों से ज्यादा रहता है, और कभी कभी छोटे या खास तरह के सामान की जरूरत पड़ सकती है। मांसपेशियाँ कमजोर होने के कारण नया जोड़ अपनी जगह से खिसकने का खतरा भी ज्यादा रहता है, और आगे चलकर सहारे या कैलिपर की जरूरत बनी रह सकती है।',\n"
 "   'डॉक्टर साहब ने हमें साफ साफ समझा दिया है कि पोलियो वाले पैर में ताकत पहले से ही कम है, इसलिए ऑपरेशन पूरी तरह सफल होने पर भी चलने फिरने में उतना सुधार नहीं आ सकता जितना आम मरीज में आता है, और पैर की लंबाई में कुछ अंतर रह सकता है। यह स्थिति आम कूल्हा बदलने या हड्डी जोड़ने वाले ऑपरेशन से अलग है और इसमें खतरे ज्यादा हैं। बिना ऑपरेशन के इलाज का विकल्प और उसकी सीमाएँ भी हमें समझा दी गई हैं। सब कुछ अच्छी तरह समझकर हम अपनी मर्जी से यह ऑपरेशन करवा रहे हैं।']}\n"
 "];")

# ---- 2 · the generator must not stringify a module when h is empty -------
A_FOREACH = (" paras.forEach(function(p){ if(p&&p.h){ html+='<h3 class=\"cs-mod\">'"
             "+p.h+'</h3>';")
N_FOREACH = (" paras.forEach(function(p){ if(p&&p.ps){ if(p.h) html+='<h3 class=\"cs-mod\">'"
             "+p.h+'</h3>';")

# ---- 3 · the three loose words the owner ruled + the two he was not shown -
A_MRI = "एक्सरे/MRI जांच में दिखाया है"
N_MRI = "एक्सरे और एमआरआई जांच में दिखाया है"

A_IMPL = "हमें बताया गया है कि जो implant (cemented / uncemented / hybrid) मरीज के लिए उचित होगा"
N_IMPL = "हमें बताया गया है कि जो इम्प्लांट (cemented / uncemented / hybrid) मरीज के लिए उचित होगा"

A_GRAFT = "दोबारा चोट लगने पर graft को नुकसान पहुँच सकता है"
N_GRAFT = "दोबारा चोट लगने पर नई लिगामेंट (graft) को नुकसान पहुँच सकता है"

# ---- 4 · the switch -------------------------------------------------------
A_SLOT = '<div id="cp11_trwarn"></div>'

N_SLOT = r'''<div id="cp11_trwarn"></div>
<div id="cs_langbar" style="display:flex;gap:6px;align-items:center;margin:8px 0;font-size:13px">
  <span style="color:var(--muted)">छपाई की भाषा</span>
  <button type="button" class="cbtn cslang on" data-lang="hi">हिंदी</button>
  <button type="button" class="cbtn cslang ghost" data-lang="hien">हिंदी + English</button>
</div>
<style>
.cslang{padding:5px 12px;font-size:13px}
.cslang.on{background:var(--blue);border-color:var(--blue);color:#fff}
</style>
<script>
/* S216 CP-1.1 step 4 - the printed language. Owner ruling: starts on हिंदी
   EVERY time; it deliberately does not remember. */
window.csLang='hi';
(function(){
 var bar=document.getElementById('cs_langbar'); if(!bar) return;
 bar.addEventListener('click',function(e){
  var b=e.target.closest('.cslang'); if(!b) return;
  window.csLang=b.getAttribute('data-lang');
  [].forEach.call(bar.querySelectorAll('.cslang'),function(x){
    var on=(x===b);
    x.classList.toggle('on',on); x.classList.toggle('ghost',!on);
  });
  try{ if(document.getElementById('cs_out').style.display!=='none') csGenerate(); }catch(_e){}
 });
})();
/* Drop a bracketed group that contains Latin letters. Applied ONLY to the
   consent paragraphs - the attestation line, which carries (M.S. Ortho), is
   built separately and never passes through here. */
function csGloss(txt){
 if(window.csLang!=='hi') return txt;
 return String(txt)
   .replace(/\s*\([^()]*[A-Za-z][^()]*\)/g,'')
   .replace(/\s{2,}/g,' ')
   .replace(/\s+([,.;।])/g,'$1')
   .trim();
}
</script>'''

# ---- 5 · apply the switch to every printed paragraph ----------------------
A_P1 = "(p.ps||[]).forEach(function(q){ html+='<p>'+String(q).replace(/\\s{2,}/g,' ').trim()+'</p>'; }); return; }"
N_P1 = "(p.ps||[]).forEach(function(q){ html+='<p>'+csGloss(String(q).replace(/\\s{2,}/g,' ').trim())+'</p>'; }); return; }"

A_P2 = "html+='<p>'+String(p).replace(/\\s{2,}/g,' ').trim()+'</p>'; });"
N_P2 = "html+='<p>'+csGloss(String(p).replace(/\\s{2,}/g,' ').trim())+'</p>'; });"


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)
    n = [0]; ref = [src]
    def patch(old, new, label, count=1):
        c = ref[0].count(old)
        assert c == count, "ANCHOR FAIL (%s): found %d, expected %d" % (label, c, count)
        ref[0] = ref[0].replace(old, new); n[0] += 1
    # locate the polio block by its own boundaries, verify, replace whole
    i = ref[0].index("var POLIO_MODULES=[")
    j = ref[0].index("var csLastMeta=null")
    old_block = ref[0][i:j].rstrip()
    assert POLIO_OLD_MUST_CONTAIN in old_block, "polio block not the expected one"
    assert old_block.count("var POLIO_MODULES=[") == 1
    ref[0] = ref[0][:i] + POLIO_NEW + "\n" + ref[0][j:]
    n[0] += 1
    print("  T1 polio module replaced: %d chars -> %d" % (len(old_block), len(POLIO_NEW)))
    patch(A_FOREACH,    N_FOREACH,    "T2 module printed as prose, not a heading")
    patch(A_P1,         N_P1,         "T3 gloss applied to module paragraphs")
    patch(A_P2,         N_P2,         "T4 gloss applied to every paragraph")
    patch(A_MRI,        N_MRI,        "T5 MRI - owner's wording")
    patch(A_IMPL,       N_IMPL,       "T6 implant -> इम्प्लांट (both hip templates)", 2)
    patch(A_GRAFT,      N_GRAFT,      "T7 graft bracketed in the ACL risk line")
    patch(A_SLOT,       N_SLOT,       "T8 the language switch")
    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
