#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s685.py -- kit S685_CONSENT_SPELLING_FIX (the parent, session S371, 31-Oct-2026).

THE OWNER, 09:28 IST 31-Oct: in the consent's Hindi-spelling box (S385) he corrected the address and pressed
"Apply everywhere"; the address in the consent did not change.
THE CAUSE (reproduced with made-up addresses): the consent prints a name or an address TIDIED -- a space before a comma
or a double space is removed (csFill, csGloss) -- while the box searched for the untidied spelling. It found 0 places,
still said "✔ Address: 0 places", and changed only the page header.
THE FIX: the box looks for the spelling as printed; a correction that finds no place changes nothing (the header
included) and says so in words.

Builds /root/wa/casepack/casepack_page.html from its LIVE bytes (ff713e36, S684's TO) by four anchored edits, each
anchor required exactly once.    python3 make_s685.py FROM.html TO.html
"""
import hashlib
import sys

FROM_MD5 = "ff713e36a1ecd082a43ee1824b654df1"

EDITS = [
    ("F1 the printed form of a spelling",
     "function csFixBuild(){\n",
     "/* S685 (31-Oct-2026): the spelling as the consent PRINTS it -- csFill and csGloss tidy spaces before a comma, double\n"
     "   spaces and (in Hindi print) English in brackets; the box must look for that form, or it finds nothing. */\n"
     "function csFixNorm(s){ s=String(s||'').replace(/  +/g,' ').replace(/ ,/g,',').replace(/ ।/g,'।').replace(/\\s{2,}/g,' ');   /* csFill, then the paragraph's collapse */\n"
     " if(window.csLang==='hi') s=s.replace(/\\s*\\([^()]*[A-Za-z][^()]*\\)/g,'').replace(/\\s{2,}/g,' ').replace(/\\s+([,.;।])/g,'$1');   /* csGloss: Hindi print only */\n"
     " return s.trim(); }\n"
     "function csFixBuild(){\n"),
    ("F2 the box starts from the printed spelling",
     "   var cur=(m[r[0]]||'').trim(); if(!cur||cur==='[___]'||cur==='[नाम]') return;\n",
     "   var cur=(m[r[0]]||'').trim(); if(!cur||cur==='[___]'||cur==='[नाम]') return;\n"
     "   if(!csFixCount(txt,cur)){ var c2=csFixNorm(cur); if(c2 && c2!==cur && csFixCount(txt,c2)) cur=c2; }   /* S685: as printed */\n"),
    ("F3 a correction that finds no place changes nothing",
     " var pairs={}, done=[];\n"
     " CS_FIX.forEach(function(f,i){\n"
     "   var nv=((document.getElementById('csfix_'+i)||{}).value||'').trim();\n"
     "   if(!nv||nv===f.cur) return;\n"
     "   var n=csFixReplace(out,f.cur,nv);\n",
     " var pairs={}, done=[], miss=[];\n"
     " CS_FIX.forEach(function(f,i){\n"
     "   var nv=((document.getElementById('csfix_'+i)||{}).value||'').trim();\n"
     "   if(!nv||nv===f.cur) return;\n"
     "   var n=csFixReplace(out,f.cur,nv);\n"
     "   if(!n){ miss.push(f.label); return; }   /* S685: nothing found -- the header and the memory are left alone too */\n"),
    ("F4 the message says what happened",
     " if(!done.length){ if(msg) msg.textContent='Nothing changed.'; return; }\n"
     " if(msg) msg.textContent='✔ '+done.join(' · ')+' + the header on every page.';\n",
     " var warn=miss.length?(' ⚠ '+miss.join(', ')+': not found in the consent text, so nothing was changed for it — correct it by hand in the consent below.'):'';\n"
     " if(!done.length){ if(msg) msg.textContent=warn?warn.trim():'Nothing changed.'; return; }\n"
     " if(msg) msg.textContent='✔ '+done.join(' · ')+' + the header on every page.'+warn;\n"),
]


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: make_s685.py FROM.html TO.html")
    raw = open(sys.argv[1], "rb").read()
    if hashlib.md5(raw).hexdigest() != FROM_MD5:
        sys.exit("!! the FROM file is %s, not the pinned %s -- nothing written" % (hashlib.md5(raw).hexdigest(), FROM_MD5))
    s = raw.decode("utf-8")
    for label, old, new in EDITS:
        n = s.count(old)
        if n != 1:
            sys.exit("!! %s: the anchor occurs %d times (exactly 1 needed) -- nothing written" % (label, n))
        s = s.replace(old, new, 1)
    out = s.encode("utf-8")
    open(sys.argv[2], "wb").write(out)
    print("S685 TO %s (%d bytes, %d counted edits)" % (hashlib.md5(out).hexdigest(), len(out), len(EDITS)))


if __name__ == "__main__":
    main()
