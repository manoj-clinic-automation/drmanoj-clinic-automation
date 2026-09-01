#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patches_ayush_names.py - S216: readable Ayushman package names
==============================================================
Base = the S216 step-2 page (contrast live, pin 3cac3904...).
Six ANCHORED patches, each must match EXACTLY ONCE. Display only.

WHY:
  The card headline was `a.name || a.proc` - the SUB-OPTION ALONE, with the
  parent package name never shown. Measured over BUNDLE.ayush (138 rows,
  73 parent procedures): 28 headlines are a bare body part or qualifier that
  means nothing on its own, and 59 of 138 are twelve characters or fewer.
  Cards read "Upper Limbs", "Spikas", "Long bone", "Without plaster".

  The parent name was in the data the whole time. It is now shown as a kicker
  line above the variant. A kicker + variant was chosen over joining them into
  one headline because "Spikas" and "Jackets" share the parent
  "Application of P.O.P. Spikas & Jackets" and a join collapsed two rows with
  DIFFERENT RATES to the same text.

WHAT IS NOT TOUCHED - the money path:
  ayushBlock() already prints the government's own hpkg/hproc, and it still
  does, byte for byte. Those are the strings the CLAIM is filed under, typos
  included ("Duputryen's", "radiofreque ncy"). Copy details, WhatsApp and the
  record detail are unchanged. ayushKey() is unchanged so existing tray
  selections keep their identity.

Usage:  python3 patches_ayush_names.py <base_page> <out_page>
"""
import sys, hashlib

BASE_MD5 = "3cac3904db706a399f44ddab91d971e7"

A_FN = "function ayushBlock(a){"

N_FN = r'''/* ---- S216: readable package naming (display only) --------------------
   ayLabel  - what the owner READS: parent package, then the variant.
   ayOfficial - what the CLAIM says: the government's own strings, verbatim.
   Never let the second follow the first.                                  */
function ayEsc(s){ return String(s==null?'':s)
 .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function ayTidy(s){ return String(s||'').replace(/\s*\bw\/\s*/g,' with ')
 .replace(/\s{2,}/g,' ').trim(); }
var _aySibs=null;
function aySibs(code){
 if(!_aySibs){ _aySibs={}; try{ BUNDLE.ayush.forEach(function(r){
   _aySibs[r.code]=(_aySibs[r.code]||0)+1; }); }catch(_e){ _aySibs={}; } }
 return _aySibs[code]||1;
}
/* When the parent already ENDS with the variant and the package has no
   siblings, the variant adds nothing - print the parent alone rather than
   "DUPUYTREN'S CONTRACTURE RELEASE + REHABILITATION / Release + rehabilitation".
   The sibling guard is what keeps Spikas and Jackets apart. */
function ayFolds(a){
 var p=ayTidy(a.proc).toLowerCase(), n=ayTidy(a.name).toLowerCase();
 if(!p || !n) return true;
 if(p===n) return true;
 return (p.slice(-n.length)===n) && aySibs(a.code)<2;
}
function ayKicker(a){
 if(ayFolds(a)) return '';
 return ayTidy(a.proc);
}
function ayHead(a){
 var p=ayTidy(a.proc), n=ayTidy(a.name);
 if(ayFolds(a)) return p || n || '';
 return n || p || '';
}
function ayLabel(a){
 var k=ayKicker(a), h=ayHead(a);
 return k? (k+' — '+h) : h;
}
function ayOfficial(a){
 var p=String(a.hpkg||a.proc||'').trim(), n=String(a.hproc||a.name||'').trim();
 if(!n || n.toLowerCase()===p.toLowerCase()) return p;
 return p+' / '+n;
}
/* The official line earns its row ONLY when it differs from what he is
   already reading. On most packages the two are the same sentence, and
   printing it twice six pixels apart is clutter, not provenance. */
function ayNorm(s){ return String(s||'').toLowerCase()
 .replace(/[\/\-\u2013\u2014,.']/g,' ').replace(/\s+/g,' ').trim(); }
function ayOfficialDiffers(a){ return ayNorm(ayOfficial(a))!==ayNorm(ayLabel(a)); }
function ayOfficialHTML(a){
 if(!ayOfficialDiffers(a)) return '';
 return '<div class="inc ayoff">Filed as: '+ayEsc(ayOfficial(a))+'</div>';
}
function ayushBlock(a){'''

A_HEAD = ("'<div class=\"chead\"><h3>'+(a.name||a.proc||'')+'</h3>"
          "<div class=\"big\">'+(a.rate?rupee(a.rate):'—')+'</div></div>'+")

N_HEAD = ("'<div class=\"chead\"><div style=\"flex:1;min-width:0\">'"
          "+(ayKicker(a)?('<div class=\"aykick\">'+ayEsc(ayKicker(a))+'</div>'):'')"
          "+'<h3>'+ayEsc(ayHead(a))+'</h3></div>"
          "<div class=\"big\">'+(a.rate?rupee(a.rate):'—')+'</div></div>'+")

A_ID = ("'<div class=\"inc\"><small class=\"k\">ID '+(a.code||'—')+(a.sub?(' · '+a.sub):'')"
        "+'</small></div>'+ayushFlags(a)+")

N_ID = ("'<div class=\"inc\"><small class=\"k\">ID '+(a.code||'—')+(a.sub?(' · '+a.sub):'')"
        "+'</small></div>'+ayOfficialHTML(a)+ayushFlags(a)+")

A_TRAY = "name:(a.name||a.proc), code:a.code"
N_TRAY = "name:ayLabel(a), off:ayOfficial(a), code:a.code"

A_REC = "recordEstimate('Ayushman',(a.name||a.proc),(a.rate||0),ayushDetail(a))"
N_REC = "recordEstimate('Ayushman',ayLabel(a),(a.rate||0),ayushDetail(a))"

A_TROW = ("rows+='<div class=\"trow\"><span style=\"flex:1\">'+(x.flg?'⚠ ':'')+x.name"
          "+' <small class=\"k\">[ID '+(x.code||'—')+']</small><br>")

N_TROW = ("rows+='<div class=\"trow\"><span style=\"flex:1\">'+(x.flg?'⚠ ':'')+x.name"
          "+' <small class=\"k\">[ID '+(x.code||'—')+']</small>'"
          "+(x.off?('<br><small class=\"k ayoff\">Official: '+x.off+'</small>'):'')+'<br>")

A_CSS = ".chead h3{margin:0;font-size:16px}"
N_CSS = (".chead h3{margin:0;font-size:16px}\n"
         ".aykick{font-size:11.5px;font-weight:700;letter-spacing:.2px;color:var(--muted);"
         "text-transform:uppercase;margin-bottom:2px;line-height:1.25}\n"
         ".ayoff{font-size:11px;color:var(--muted);opacity:.85;margin:0 0 6px;line-height:1.35}\n"
         ".aycard .chead{align-items:flex-start}\n"
         ".aycard .chead .big{margin-top:0}")


def main():
    base_fp, out_fp = sys.argv[1], sys.argv[2]
    src = open(base_fp, encoding="utf-8").read()
    got = hashlib.md5(open(base_fp, "rb").read()).hexdigest()
    assert got == BASE_MD5, "BASE MISMATCH: expected %s got %s" % (BASE_MD5, got)

    n = [0]; ref = [src]
    def patch(old, new, label):
        c = ref[0].count(old)
        assert c == 1, "ANCHOR FAIL (%s): found %d, expected 1" % (label, c)
        ref[0] = ref[0].replace(old, new); n[0] += 1

    patch(A_CSS,  N_CSS,  "N0 kicker + official CSS")
    patch(A_FN,   N_FN,   "N1 naming helpers")
    patch(A_HEAD, N_HEAD, "N2 card kicker + headline")
    patch(A_ID,   N_ID,   "N3 official line on the card")
    patch(A_TRAY, N_TRAY, "N4 tray carries label + official")
    patch(A_REC,  N_REC,  "N5 recorded estimate title")
    patch(A_TROW, N_TROW, "N6 tray row shows official")
    patch("const el=document.createElement('div'); el.className='card open';\n"
          "    const sel=inSel(a); const scnt=selCount(a);",
          "const el=document.createElement('div'); el.className='card open aycard';\n"
          "    const sel=inSel(a); const scnt=selCount(a);",
          "N7 ayushman card class, for a steady price column")

    out = ref[0]
    open(out_fp, "w", encoding="utf-8", newline="").write(out)
    print("patches applied: %d" % n[0])
    print("base md5: %s" % got)
    print("out  md5: %s" % hashlib.md5(out.encode("utf-8")).hexdigest())

if __name__ == "__main__":
    main()
