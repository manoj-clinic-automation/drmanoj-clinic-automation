#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""make_s750.py -- S750_MONTH_END: the appended sections and the anchored changes of the six live files (four of this project; the Scan App's
two, PLANNED on board/_numbers v1066).
    python3 -B make_s750.py <finance dir> <assetapp dir> <out dir> [<dir holding the S750 sections>]
Each FROM file must carry its pinned md5 (the live bytes of 08-Nov: the 08-Nov bundle + kit S749); every anchor must stand EXACTLY the number
of times named; the TO md5s are printed. The sections are read from sec_sr750.txt, sec_pa750.txt, sec_amir750.txt, sec_p454_750.txt,
sec_ar750.txt and sec_reader750.txt beside this script."""
import hashlib
import os
import sys

FROM = {"finance/scan_register.py": "5b0662498992439075e6adfb2d834daa",     # S749's TO (live 08-Nov 08:20 IST)
        "finance/purchase_app.py": "0d49c2490d8ca05e6043192987f71c03",      # S749's TO
        "finance/amir_day.py": "98c40f51d5b9ed1500baef26d2941d5c",          # S749's TO
        "finance/porders_s454.py": "37c4f3bf7589fde41617d4c103cd01ee",      # S740's TO (the 08-Nov bundle; S749 did not touch it)
        "assetapp/asset_register.py": "16a2abea4d716444bd3a9bd9540a1269",   # the Scan App's, the 08-Nov bundle (PLANNED, D646)
        "assetapp/claude_reader.py": "1277e80de5c141cf3f5f7c97b9434cb9"}    # the Scan App's, the 08-Nov bundle (PLANNED, D646)
APPEND = {"finance/scan_register.py": "sec_sr750.txt", "finance/purchase_app.py": "sec_pa750.txt", "finance/amir_day.py": "sec_amir750.txt",
          "finance/porders_s454.py": "sec_p454_750.txt", "assetapp/asset_register.py": "sec_ar750.txt", "assetapp/claude_reader.py": "sec_reader750.txt"}

# asset_register.py -- the anchored changes: (old, new, how many times the anchor stands)
AR_EDITS = [
    # the capture function takes the tick
    ('''def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False, kind_over=None):      # S568: kind_over''',
     '''def _create_intake_bill(fobj, note, lane=None, prefill=None, challan=False, kind_over=None, summary=False):      # S568: kind_over; S750: summary''', 1),
    # the two call sites (the basic form and the widget) pass it
    ('''                              request.form.get("lane"), _form_prefill(), challan=(request.form.get("challan") == "1"))     # S403; S531''',
     '''                              request.form.get("lane"), _form_prefill(), challan=(request.form.get("challan") == "1"),
                              summary=(request.form.get("summary") == "1"))     # S403; S531; S750''', 2),
    # after the challan block: the summary lands as kind 'Summary' on the pharmacy lane (the challan's own road)
    ('''        _audit_bill(db, bid, "challan", {"lane": _lane})
''',
     '''        _audit_bill(db, bid, "challan", {"lane": _lane})
    if summary and not challan and _lane == "pharmacy":      # S750: a dealer's month summary -- never a bill scan for the Sanjeevni register
        db.execute("UPDATE bills SET doc_kind='summary', kind='Summary' WHERE id=?", (bid,))
        _audit_bill(db, bid, "summary", {"lane": _lane})
''', 1),
    # the intake page: the second button beside the challan button
    ('''<p class=muted id=challan_hint style="margin:6px 0 0;font-size:13px">Sirf tab dabao jab kaagaz challan ho (maal aaya, bill baad mein). Bill ho to kuch mat dabao.</p></div>''',
     '''<p class=muted id=challan_hint style="margin:6px 0 0;font-size:13px">Sirf tab dabao jab kaagaz challan ho (maal aaya, bill baad mein). Bill ho to kuch mat dabao.</p>
<button type=button id=summary_btn style="display:block;width:100%;margin-top:10px;min-height:52px;font-size:17px;font-weight:700;border-radius:10px;border:2px solid #b7c2d4;background:#fff;color:#2d3742">📋 DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?</button>
<p class=muted id=summary_hint style="margin:6px 0 0;font-size:13px">Sirf tab dabao jab kaagaz dealer ka mahine ka hisaab (summary / statement) ho &mdash; bill nahi. Pharmacy lane par hi.</p></div>''', 1),
    # the JS: the summary flag rides uploadFields like the challan's; the lane line says SUMMARY
    ('''<script>window.SCANNER_CONFIG = {{ scan_cfg|tojson }};</script>''',
     '''<script>function _summarySet(on){var b=document.getElementById('summary_btn'),h=document.getElementById('summary_basic');if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields){if(on){window.SCANNER_CONFIG.uploadFields.summary='1';}else{delete window.SCANNER_CONFIG.uploadFields.summary;}}
if(h){h.value=on?'1':'';}if(b){b.textContent=on?'✔ SUMMARY — dealer ka mahine ka hisaab':'📋 DEALER KA MAHINE KA HISAAB (SUMMARY) HAI?';b.style.background=on?'#dfe9f7':'#fff';b.style.borderColor=on?'#1f3864':'#b7c2d4';}
var hh=document.getElementById('summary_hint');if(hh){hh.textContent=on?'Yeh scan dealer ka hisaab (summary) ban kar jaayega — doctor sahab ki list par. Galti se dabaya? Dobara dabao.':'Sirf tab dabao jab kaagaz dealer ka mahine ka hisaab (summary / statement) ho — bill nahi. Pharmacy lane par hi.';}
if(on&&typeof _challanSet==='function'&&window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1'){_challanSet(false);}if(typeof _laneLine==='function'){_laneLine();}}</script>
<script>window.SCANNER_CONFIG = {{ scan_cfg|tojson }};</script>''', 1),
    ('''(ch?' · CHALLAN':'');}''',
     '''(ch?' · CHALLAN':'')+((((window.SCANNER_CONFIG||{}).uploadFields||{}).summary==='1')?' · SUMMARY':'');}''', 1),
    # the basic form's hidden field
    ('''<input type=hidden name=challan id=challan_basic value="">''',
     '''<input type=hidden name=challan id=challan_basic value=""><input type=hidden name=summary id=summary_basic value="">''', 1),
    # the click, and the reset after Save (the widget keeps its own copy of the fields, as S531's challan)
    ('''var cb=document.getElementById('challan_btn');if(cb){cb.addEventListener('click',function(){_challanSet(!(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1'));});}''',
     '''var cb=document.getElementById('challan_btn');if(cb){cb.addEventListener('click',function(){_challanSet(!(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1'));if(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.challan==='1'){_summarySet(false);}});}
var sb=document.getElementById('summary_btn');if(sb){sb.addEventListener('click',function(){_summarySet(!(window.SCANNER_CONFIG&&window.SCANNER_CONFIG.uploadFields&&window.SCANNER_CONFIG.uploadFields.summary==='1'));});}''', 1),
    ('''setTimeout(function(){_challanSet(false);''',
     '''setTimeout(function(){_challanSet(false);_summarySet(false);''', 1),
    # the slip
    ('''{% if b['doc_kind']=='challan' %}<p style="font-size:18px;font-weight:700;color:#5b3a06;background:#fff4e0;border-radius:8px;padding:8px 10px;margin:6px 0">CHALLAN — bill baad mein aayega. Kaagaz par yeh number likho; bill aaye to yahi number batao.</p>{% endif %}''',
     '''{% if b['doc_kind']=='challan' %}<p style="font-size:18px;font-weight:700;color:#5b3a06;background:#fff4e0;border-radius:8px;padding:8px 10px;margin:6px 0">CHALLAN — bill baad mein aayega. Kaagaz par yeh number likho; bill aaye to yahi number batao.</p>{% endif %}
{% if b['doc_kind']=='summary' %}<p style="font-size:18px;font-weight:700;color:#1f3864;background:#dfe9f7;border-radius:8px;padding:8px 10px;margin:6px 0">SUMMARY — dealer ka mahine ka hisaab liya. Doctor sahab ki list par chala gaya.</p>{% endif %}''', 1),
    # the edit form keeps the kind (as it keeps 'Challan')
    ('''        kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense") else (f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document") else "Consumable")''',
     '''        kind = b["kind"] if b["kind"] in ("Lab", "Expense", "Document", "Pharmacy", "Challan", "Pharmacy expense", "Summary") else (f.get("kind") if f.get("kind") in ("Asset", "Consumable", "Pharmacy", "Lab", "Expense", "Document") else "Consumable")''', 1),
    ('''{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense') %}''',
     '''{% if editing and hdr.get('kind') in ('Lab','Expense','Document','Pharmacy','Challan','Pharmacy expense','Summary') %}''', 1),
]


def md5(b):
    return hashlib.md5(b).hexdigest()


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    fin, aapp, out = sys.argv[1], sys.argv[2], sys.argv[3]
    here = sys.argv[4] if len(sys.argv) > 4 else os.path.dirname(os.path.abspath(__file__))
    bad = 0
    for rel, pin in FROM.items():
        src = os.path.join(fin if rel.startswith("finance/") else aapp, os.path.basename(rel))
        raw = open(src, "rb").read()
        if md5(raw) != pin:
            print("!! %s is %s, not the pinned %s -- refused" % (rel, md5(raw)[:8], pin[:8]))
            bad += 1
            continue
        text = raw.decode("utf-8")
        if rel == "assetapp/asset_register.py":
            for old, new, n in AR_EDITS:
                c = text.count(old)
                if c != n:
                    print("!! %s: anchor stands %d time(s), expected %d: %r" % (rel, c, n, old[:70]))
                    bad += 1
                    continue
                text = text.replace(old, new)
        sec = open(os.path.join(here, APPEND[rel]), "rb").read().decode("utf-8")
        text = text.rstrip("\n") + "\n\n\n" + sec.lstrip("\n")          # two blank lines, then the section; one newline at the end
        if not text.endswith("\n"):
            text += "\n"
        dst = os.path.join(out, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, "wb").write(text.encode("utf-8"))
        print("%s  %s -> %s" % (rel, pin[:8], md5(text.encode("utf-8"))))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
